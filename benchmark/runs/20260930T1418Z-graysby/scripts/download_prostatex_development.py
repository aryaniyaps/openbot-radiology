#!/usr/bin/env python3
"""Acquire ONE complete diagnosis-blind development patient, all MR series.

No clinical CSV, lesion coordinates, image-reference table or masks are read.
No inference. Serial downloads with bounded storage and resumable receipts.
"""
import hashlib, json, pathlib, shutil, urllib.parse, urllib.request, zipfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
catalogue = json.loads((ROOT/'private/prostatex-series.json').read_text())
patient = sorted({x['PatientID'] for x in catalogue})[0]
series = sorted([x for x in catalogue if x['PatientID']==patient], key=lambda x: (int(x['SeriesNumber']), x['SeriesInstanceUID']))
assert all(x['Modality']=='MR' for x in series)
assert sum(int(x['FileSize']) for x in series) < 256*1024**2
DEST = ROOT/'private/prostatex-development-complete'
DEST.mkdir(mode=0o700,exist_ok=True)
selection = {'split':'development permanently','selection':'first lexicographic catalogue PatientID, no references read; all catalogue studies and MR series retained',
             'source_patient_id':patient,'series':series,'source_catalogue_sha256':hashlib.sha256((ROOT/'private/prostatex-series.json').read_bytes()).hexdigest()}
p=DEST/'selection.json'
if p.exists():assert json.loads(p.read_text())==selection
else:p.write_text(json.dumps(selection,indent=2)+'\n')
receipts=[]
for index,s in enumerate(series,1):
    if shutil.disk_usage(ROOT).free < 35*1024**3:raise SystemExit('Own benchmark free disk floor reached')
    directory=DEST/f'series-{index:03}';directory.mkdir(mode=0o700,exist_ok=True)
    url='https://services.cancerimagingarchive.net/nbia-api/services/v1/getImage?'+urllib.parse.urlencode({'SeriesInstanceUID':s['SeriesInstanceUID']})
    archive=directory/'source.zip';part=directory/'source.partial'
    if not archive.exists():
        if part.exists():raise SystemExit('Inspect previous incomplete acquisition before retrying')
        with urllib.request.urlopen(url,timeout=60) as response,part.open('xb') as output:
            assert response.status==200
            total=0
            while chunk:=response.read(1024*1024):
                total+=len(chunk)
                if total>64*1024**2:raise SystemExit('Own single-series archive limit exceeded')
                output.write(chunk)
        part.rename(archive)
    images=[]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members=[m for m in z.infolist() if not m.is_dir()]
        assert sum(m.file_size for m in members)<128*1024**2
        for member in members:
            name=pathlib.PurePosixPath(member.filename)
            assert not name.is_absolute() and '..' not in name.parts
            if name.suffix.lower()!='.dcm':continue
            target=directory/'dicom'/name.name;target.parent.mkdir(mode=0o700,exist_ok=True)
            payload=z.read(member)
            assert not target.exists() or target.read_bytes()==payload
            target.write_bytes(payload)
            images.append({'filename':name.name,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)})
    assert len(images)==int(s['ImageCount'])
    receipt={'series_index':index,'source_url':url,'series_description':s.get('SeriesDescription'),
             'source_series_uid':s['SeriesInstanceUID'],'archive_bytes':archive.stat().st_size,
             'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'images':images}
    (directory/'acquisition.json').write_text(json.dumps(receipt,indent=2)+'\n')
    receipts.append(receipt)
    (DEST/'acquisition.json').write_text(json.dumps(receipts,indent=2)+'\n')
    summary={'split':'development only','selection':'first catalogue patient; all series, no reference/lesion table read',
             'expected_patients':1,'expected_studies':len({x['StudyInstanceUID'] for x in series}),
             'expected_series':len(series),'expected_images':sum(int(x['ImageCount']) for x in series),
             'downloaded_series':len(receipts),'downloaded_images':sum(len(x['images']) for x in receipts),
             'downloaded_archive_bytes':sum(x['archive_bytes'] for x in receipts),
             'complete':len(receipts)==len(series),'pixel_decode_and_geometry_validation':'pending',
             'receipt_sha256':hashlib.sha256((DEST/'acquisition.json').read_bytes()).hexdigest()}
    (ROOT/'evidence/prostatex-development-acquisition.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({'series':index,'of':len(series),'images':len(images),'compressed_bytes':archive.stat().st_size}),flush=True)
