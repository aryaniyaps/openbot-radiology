#!/usr/bin/env python3
"""Operator technical audit. No diagnostic reference labels or model outputs."""
import collections, hashlib, json, pathlib
import pydicom

ROOT = pathlib.Path(__file__).resolve().parents[1]
records = []
for directory in sorted((ROOT / 'private/cmmd-development-cohort').glob('CMMD-*')):
    receipt = json.loads((directory / 'acquisition.json').read_text())
    instances = []
    for image in receipt['images']:
        path = directory / 'dicom' / image['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == image['sha256']
        ds = pydicom.dcmread(path)
        pixels = ds.pixel_array
        overlay_groups = sorted({f'{e.tag.group:04X}' for e in ds if 0x6000 <= e.tag.group <= 0x60FF})
        # Presence of these fields requires review; absence is not a complete leak audit.
        text_fields = [k for k in ['PatientName','PatientID','AccessionNumber','StudyDescription','SeriesDescription','ImageComments','PatientComments','StudyComments','InstitutionName'] if ds.get(k)]
        instances.append({'filename': image['filename'], 'sop_uid': str(ds.SOPInstanceUID),
                          'series_uid': str(ds.SeriesInstanceUID), 'study_uid': str(ds.StudyInstanceUID),
                          'modality': str(ds.Modality), 'dimensions': list(pixels.shape),
                          'photometric_interpretation': str(ds.PhotometricInterpretation),
                          'bits_stored': int(ds.BitsStored), 'pixel_representation': int(ds.PixelRepresentation),
                          'transfer_syntax': str(ds.file_meta.TransferSyntaxUID),
                          'pixel_data_sha256': hashlib.sha256(ds.PixelData).hexdigest(),
                          'image_laterality': str(ds.get('ImageLaterality','')),
                          'laterality': str(ds.get('Laterality','')), 'view_position': str(ds.get('ViewPosition','')),
                          'view_code_meanings': [str(x.get('CodeMeaning','')) for x in ds.get('ViewCodeSequence',[])],
                          'burned_in_annotation': str(ds.get('BurnedInAnnotation','UNSPECIFIED')),
                          'overlay_groups': overlay_groups, 'text_fields_requiring_scrub': text_fields,
                          'window_center': str(ds.get('WindowCenter','')), 'window_width': str(ds.get('WindowWidth',''))})
    assert len(instances) == len(receipt['images'])
    assert all(x['modality'] == 'MG' for x in instances)
    assert len({x['series_uid'] for x in instances}) == 1
    assert len({x['sop_uid'] for x in instances}) == len(instances)
    records.append({'case_id': directory.name, 'images': instances})
all_images = [x for case in records for x in case['images']]
assert len({x['sop_uid'] for x in all_images}) == len(all_images), 'Duplicate SOP instance across development patients'
assert len({x['pixel_data_sha256'] for x in all_images}) == len(all_images), 'Duplicate pixel payload across development patients'
(ROOT / 'private/cmmd-development-technical-details.json').write_text(json.dumps(records,indent=2)+'\n')
summary = {'split': 'development only', 'patients': len(records), 'images': len(all_images),
           'image_count_histogram': dict(collections.Counter(len(x['images']) for x in records)),
           'dimension_histogram': dict(collections.Counter('x'.join(map(str,x['dimensions'])) for x in all_images)),
           'laterality_histogram': dict(collections.Counter(x['image_laterality'] or x['laterality'] or 'MISSING' for x in all_images)),
           'view_position_histogram': dict(collections.Counter(x['view_position'] or 'MISSING' for x in all_images)),
           'view_code_meaning_histogram': dict(collections.Counter(v for x in all_images for v in x['view_code_meanings'])),
           'burned_in_annotation_histogram': dict(collections.Counter(x['burned_in_annotation'] for x in all_images)),
           'overlay_image_count': sum(bool(x['overlay_groups']) for x in all_images),
           'duplicate_sop_uid_count': 0, 'duplicate_pixel_payload_count': 0,
           'pixels_decoded': True, 'visual_review_complete': False,
           'eligibility_status': 'Technical development audit only; view/laterality correction, reference-breast coverage and visual leakage review remain pending',
           'details_sha256': hashlib.sha256((ROOT / 'private/cmmd-development-technical-details.json').read_bytes()).hexdigest()}
(ROOT / 'evidence/cmmd-development-technical-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
