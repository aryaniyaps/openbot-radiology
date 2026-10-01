#!/usr/bin/env python3
"""Technical geometry/temporal inspection of one complete MRI development case."""
import collections, hashlib, json, pathlib
import numpy as np
import pydicom
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEST=ROOT/'private/prostatex-development-complete'
selection=json.loads((DEST/'selection.json').read_text())
receipts=json.loads((DEST/'acquisition.json').read_text())
assert len(receipts)==len(selection['series']), 'Do not audit incomplete acquisition as complete'
records=[]
for receipt in receipts:
    directory=DEST/f"series-{receipt['series_index']:03}"
    images=[]
    for item in receipt['images']:
        path=directory/'dicom'/item['filename']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        ds=pydicom.dcmread(path);pixels=ds.pixel_array
        orientation=[float(x) for x in ds.get('ImageOrientationPatient',[])]
        position=[float(x) for x in ds.get('ImagePositionPatient',[])]
        projection=float(np.dot(position,np.cross(orientation[:3],orientation[3:]))) if len(position)==3 and len(orientation)==6 else None
        images.append({'filename':item['filename'],'sop_uid':str(ds.SOPInstanceUID),
                       'series_uid':str(ds.SeriesInstanceUID),'study_uid':str(ds.StudyInstanceUID),
                       'dimensions':list(pixels.shape),'pixel_data_sha256':hashlib.sha256(ds.PixelData).hexdigest(),
                       'orientation':orientation,'position':position,'slice_projection_mm':projection,
                       'pixel_spacing_mm':[float(x) for x in ds.get('PixelSpacing',[])],
                       'instance_number':int(ds.get('InstanceNumber',0)),
                       'temporal_position':str(ds.get('TemporalPositionIdentifier','')),
                       'acquisition_time':str(ds.get('AcquisitionTime','')),
                       'diffusion_b_value':str(ds.get('DiffusionBValue','')),
                       'image_type':list(ds.get('ImageType',[])),
                       'window_center':str(ds.get('WindowCenter','')),'window_width':str(ds.get('WindowWidth','')),
                       'burned_in_annotation':str(ds.get('BurnedInAnnotation','UNSPECIFIED')),
                       'overlay_groups':sorted({f'{e.tag.group:04X}' for e in ds if 0x6000<=e.tag.group<=0x60FF}),
                       'transfer_syntax':str(ds.file_meta.TransferSyntaxUID)})
    assert len(images)==len(receipt['images'])
    assert {x['series_uid'] for x in images}=={receipt['source_series_uid']}
    projections=sorted({round(x['slice_projection_mm'],5) for x in images if x['slice_projection_mm'] is not None})
    gaps=[round(b-a,5) for a,b in zip(projections,projections[1:])]
    records.append({'series_index':receipt['series_index'],'description':receipt['series_description'],
                    'instances':len(images),'unique_slice_positions':len(projections),
                    'slice_spacing_histogram':dict(collections.Counter(gaps)),
                    'orientation_count':len({tuple(x['orientation']) for x in images}),
                    'pixel_spacing_count':len({tuple(x['pixel_spacing_mm']) for x in images}),
                    'acquisition_time_count':len({x['acquisition_time'] for x in images}),
                    'images':images})
all_images=[x for s in records for x in s['images']]
assert len(all_images)==sum(int(s['ImageCount']) for s in selection['series'])
assert len({x['sop_uid'] for x in all_images})==len(all_images)
p=DEST/'technical-audit.json';p.write_text(json.dumps(records,indent=2)+'\n')
summary={'split':'development only','patients':1,'studies':len({x['study_uid'] for x in all_images}),
         'series':len(records),'images':len(all_images),'pixels_decoded':True,
         'description_series_counts':dict(collections.Counter(s['description'] for s in records)),
         'dimension_histogram':dict(collections.Counter('x'.join(map(str,x['dimensions'])) for x in all_images)),
         'missing_position_count':sum(not x['position'] for x in all_images),
         'missing_orientation_count':sum(not x['orientation'] for x in all_images),
         'burned_in_annotation_histogram':dict(collections.Counter(x['burned_in_annotation'] for x in all_images)),
         'overlay_image_count':sum(bool(x['overlay_groups']) for x in all_images),
         'repeated_slice_positions_series_count':sum(s['instances']>s['unique_slice_positions'] for s in records),
         'source_pixel_payload_duplicate_count':len(all_images)-len({x['pixel_data_sha256'] for x in all_images}),
         'reference_or_lesion_coordinate_access':False,'rendering_or_viewer_validation_complete':False,
         'caveat':'Catalogue acquisition complete does not establish diagnostic completeness. Repeated positions may encode diffusion/temporal contrasts; do not sort/drop by position alone.',
         'private_details_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ROOT/'evidence/prostatex-development-technical-audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
