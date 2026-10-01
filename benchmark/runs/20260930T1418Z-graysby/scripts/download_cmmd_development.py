#!/usr/bin/env python3
"""Operator-only, bounded acquisition of candidate DEVELOPMENT series.

No reference labels read; never downloads evaluation or follow-up patients.
Reuses a verified archive, checks count, and rejects archive path traversal.
"""
import hashlib, json, pathlib, shutil, urllib.parse, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / 'private/cmmd-development-cohort'
DEST.mkdir(mode=0o700, exist_ok=True)
records = []
manifest = json.loads((ROOT / 'private/cmmd-candidate-cohort.json').read_text())
cases = [x for x in manifest if x['split'] == 'development']
assert len(cases) == 10
for case in cases:
    if shutil.disk_usage(ROOT).free < 35 * 1024**3:
        raise SystemExit('Benchmark free disk floor reached; stop own acquisition')
    directory = DEST / case['case_id']
    directory.mkdir(mode=0o700, exist_ok=True)
    archive = directory / 'source.zip'
    url = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/getImage?' + urllib.parse.urlencode({'SeriesInstanceUID': case['series']['SeriesInstanceUID']})
    if not archive.exists():
        part = archive.with_suffix('.partial')
        # No repeated failed fetch: partial remains evidence; resume requires inspection.
        if part.exists():
            raise SystemExit(f'Inspect previous partial before retrying {case["case_id"]}')
        with urllib.request.urlopen(url, timeout=60) as response, part.open('xb') as output:
            assert response.status == 200
            total = 0
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > 128 * 1024**2:
                    raise SystemExit('Development series compressed size exceeds cap')
                output.write(chunk)
        part.rename(archive)
    images = []
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members = [x for x in z.infolist() if not x.is_dir()]
        assert sum(x.file_size for x in members) < 256 * 1024**2
        for member in members:
            path = pathlib.PurePosixPath(member.filename)
            assert not path.is_absolute() and '..' not in path.parts
            if path.suffix.lower() != '.dcm':
                continue
            payload = z.read(member)
            target = directory / 'dicom' / path.name
            target.parent.mkdir(mode=0o700, exist_ok=True)
            assert not target.exists() or target.read_bytes() == payload
            target.write_bytes(payload)
            images.append({'filename': path.name, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
    assert len(images) == int(case['series']['ImageCount'])
    record = {'case_id': case['case_id'], 'split': 'development', 'source_url': url,
              'archive_bytes': archive.stat().st_size, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'images': images}
    (directory / 'acquisition.json').write_text(json.dumps(record, indent=2) + '\n')
    records.append(record)
    print(json.dumps({'case_id': case['case_id'], 'images': len(images), 'compressed_bytes': archive.stat().st_size}), flush=True)
    # Incremental receipt persists successes if a later download fails.
    (ROOT / 'evidence/cmmd-development-acquisition.json').write_text(json.dumps(records, indent=2) + '\n')
