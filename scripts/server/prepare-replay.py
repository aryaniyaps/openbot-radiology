#!/usr/bin/env python3
"""Create disclosed identity-remapped replay copies; never modify source archives."""
import hashlib
import io
import json
import pathlib
import zipfile

import pydicom
from pydicom.uid import generate_uid

ROOT = pathlib.Path(__file__).resolve().parents[2]
state = json.loads((ROOT / '.private/server/hospital-state.json').read_text())
sources = json.loads((ROOT / '.private/dicom/source-manifest.json').read_text())
mwl = json.loads((ROOT / '.private/server/mwl.json').read_text())
manifest = []

def uid(case, original):
    return generate_uid(entropy_srcs=['kauvery-public-demo-v1', case, str(original)])

for source in sources:
    key = source['case']
    case = state['cases'][key]
    matches = [x for x in mwl if x['00080050']['Value'][0] == case['accession']]
    assert len(matches) == 1, key
    item = matches[0]
    assert item['00100020']['Value'][0] == case['patient_id']
    study_uid = item['0020000D']['Value'][0]
    destination = ROOT / '.private/dicom/replay' / key
    destination.mkdir(parents=True, exist_ok=True)
    files = []
    for series in source['series']:
        with zipfile.ZipFile(ROOT / series['local_archive']) as archive:
            for name in archive.namelist():
                if not name.lower().endswith('.dcm'):
                    continue
                data = pydicom.dcmread(io.BytesIO(archive.read(name)))
                pixels = hashlib.sha256(data.PixelData).hexdigest()
                source_sop = str(data.SOPInstanceUID)
                original_sop_class = str(data.SOPClassUID)
                original_study = str(data.StudyInstanceUID)
                # Remap instance/reference UIDs recursively, keeping SOP classes and transfer syntax intact.
                for element in data.iterall():
                    if element.VR == 'UI' and any(x in element.keyword for x in ('InstanceUID', 'FrameOfReferenceUID')) and 'Class' not in element.keyword:
                        if element.VM > 1:
                            element.value = [uid(key, x) for x in element.value]
                        else:
                            element.value = uid(key, element.value)
                data.StudyInstanceUID = study_uid
                data.PatientID = case['patient_id']
                data.PatientName = 'PublicCase^' + key.upper().replace('-', '')
                data.PatientBirthDate = '19760101'
                data.PatientSex = 'F' if source['modality'] == 'MG' else 'M'
                if 'PatientAge' in data:
                    del data.PatientAge
                data.AccessionNumber = case['accession']
                data.IssuerOfPatientID = 'Bahmni EMR'
                data.PatientIdentityRemoved = 'YES'
                data.DeidentificationMethod = ['Public source; demo identity and accession; pixels unchanged', 'Instance UIDs remapped; source manifest retains provenance']
                data.StudyDescription = 'PUBLIC DEMO ' + key.upper() + ' - ' + str(data.get('StudyDescription', ''))[:35]
                data.file_meta.MediaStorageSOPInstanceUID = data.SOPInstanceUID
                output = destination / (str(data.SOPInstanceUID) + '.dcm')
                data.save_as(output, enforce_file_format=True)
                check = pydicom.dcmread(output)
                assert hashlib.sha256(check.PixelData).hexdigest() == pixels
                assert str(check.SOPClassUID) == original_sop_class
                files.append({'file': str(output.relative_to(ROOT)), 'sha256': hashlib.file_digest(output.open('rb'), 'sha256').hexdigest(),
                              'pixel_sha256': pixels, 'source_sop': source_sop, 'source_study': original_study,
                              'sop': str(check.SOPInstanceUID), 'sop_class': original_sop_class,
                              'frames': int(check.get('NumberOfFrames', 1)), 'rows': int(check.Rows), 'columns': int(check.Columns)})
    case['study_uid'] = study_uid
    case['instance_count'] = len(files)
    manifest.append({'case': key, 'modality': source['modality'], 'patient_id': case['patient_id'], 'accession': case['accession'],
                     'study_uid': study_uid, 'files': files, 'source_collections': sorted({s['Collection'] for s in source['series']})})
    print(key, len(files), 'pixel-preserving objects prepared')
(ROOT / '.private/dicom/replay-manifest.json').write_text(json.dumps(manifest, indent=2))
(ROOT / '.private/server/hospital-state.json').write_text(json.dumps(state, indent=2))
