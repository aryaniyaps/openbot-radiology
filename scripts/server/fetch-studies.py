#!/usr/bin/env python3
"""Operator-only curated TCIA download. Originals remain separate from replay data."""
import concurrent.futures
import hashlib
import json
import pathlib
import re
import shutil
import time
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.private'
DEST = PRIVATE / 'dicom' / 'originals'
API = 'https://services.cancerimagingarchive.net/nbia-api/services/v1/'

def catalogue(name):
    return json.loads((PRIVATE / 'server' / f'{name}-series.json').read_text())

def select():
    cases = []
    for name, predicate in [('xray', lambda s: s['ImageCount'] == 1),
                            ('ct', lambda s: 'LUNG HR' in s.get('SeriesDescription', '') and 100 <= s['ImageCount'] <= 500),
                            ('us', lambda s: s['ImageCount'] == 1 and s['FileSize'] > 20_000_000)]:
        seen = set()
        for s in sorted(catalogue(name), key=lambda s: (s['PatientID'], s['StudyInstanceUID'], s['SeriesInstanceUID'])):
            if predicate(s) and s['PatientID'] not in seen:
                seen.add(s['PatientID'])
                cases.append({'case': f'{name}-{len(seen):02}', 'modality': s['Modality'], 'series': [s]})
                if len(seen) == 2:
                    break
        assert len(seen) == 2, name
    grouped = {}
    for s in catalogue('mr'):
        grouped.setdefault((s['PatientID'], s['StudyInstanceUID']), []).append(s)
    for key, series in sorted(grouped.items()):
        chosen = []
        for predicate in [lambda s: s.get('SeriesDescription') == 't2_tse_tra',
                          lambda s: s.get('SeriesDescription', '').endswith('_ADC'),
                          lambda s: s.get('SeriesDescription') in ('ep2d_diff_tra_DYNDIST', 'ep2d_diff_tra')]:
            candidates = [s for s in series if predicate(s)]
            if candidates:
                chosen.append(sorted(candidates, key=lambda s: s['SeriesInstanceUID'])[0])
        if len(chosen) == 3:
            number = len([c for c in cases if c['modality'] == 'MR']) + 1
            cases.append({'case': f'mr-{number:02}', 'modality': 'MR', 'series': chosen})
            if number == 2:
                break
    seen = set()
    for series in sorted(catalogue('cmmd'), key=lambda s: s['PatientID']):
        if series['ImageCount'] == 4 and series['PatientID'] not in seen:
            seen.add(series['PatientID'])
            cases.append({'case': f'mg-{len(seen):02}', 'modality': 'MG', 'series': [series]})
            if len(seen) == 2:
                break
    assert len(cases) == 10
    assert sum(s['FileSize'] for c in cases for s in c['series']) < 3_000_000_000
    return cases

def fetch(item):
    case, series = item
    target = DEST / case / (series['SeriesInstanceUID'] + '.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(3):
        try:
            if not target.exists():
                if shutil.disk_usage(DEST).free < 30 * 1024**3:
                    raise RuntimeError('30 GiB host free-space reserve reached')
                url = API + 'getImage?SeriesInstanceUID=' + series['SeriesInstanceUID']
                with urllib.request.urlopen(url, timeout=120) as response, target.with_suffix('.partial').open('wb') as output:
                    shutil.copyfileobj(response, output)
                target.with_suffix('.partial').replace(target)
            with zipfile.ZipFile(target) as archive:
                assert archive.testzip() is None
                assert len(archive.namelist()) >= series['ImageCount']
            series['archive_sha256'] = hashlib.file_digest(target.open('rb'), 'sha256').hexdigest()
            series['local_archive'] = str(target.relative_to(ROOT))
            print(case, series['SeriesDescription'] if 'SeriesDescription' in series else 'US', 'verified', flush=True)
            return
        except Exception:
            if target.exists():
                target.unlink()
            if attempt == 2:
                raise
            time.sleep(2**attempt)

if __name__ == '__main__':
    DEST.mkdir(parents=True, exist_ok=True)
    cases = select()
    manifest = PRIVATE / 'dicom' / 'source-manifest.json'
    manifest.write_text(json.dumps(cases, indent=2))
    print('Selected', len(cases), 'cases;', sum(s['FileSize'] for c in cases for s in c['series']), 'uncompressed bytes', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, [(c['case'], s) for c in cases for s in c['series']]))
    manifest.write_text(json.dumps(cases, indent=2))
