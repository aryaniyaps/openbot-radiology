#!/usr/bin/env python3
"""Development-only DICOM preparation; no labels or lesion annotations read."""
import pathlib,json,hashlib
import pydicom,numpy as np
from pydicom.pixels import apply_modality_lut,apply_voi_lut
from pydicom.uid import generate_uid
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[1]
SOURCE=ROOT/'private/development-cmmd/dicom'
DEST=ROOT/'agent-visible/development-mg'
DEST.mkdir(exist_ok=True)
uids={};rows=[]
for index,p in enumerate(sorted(SOURCE.glob('*.dcm'))):
    d=pydicom.dcmread(p);before=hashlib.sha256(d.PixelData).hexdigest()
    # Render source VOI where supplied, and disclose a deterministic full-range fallback.
    pixels=apply_modality_lut(d.pixel_array,d)
    has_voi='VOILUTSequence' in d or ('WindowCenter' in d and 'WindowWidth' in d)
    shown=np.asarray(apply_voi_lut(pixels,d) if has_voi else pixels,dtype=np.float64)
    # Use the VOI output domain, not observed min/max: preserve displayed contrast.
    if 'VOILUTSequence' in d:
        low=0.0;high=float(2**int(d.VOILUTSequence[0].LUTDescriptor[2])-1)
    else:
        bits=int(d.BitsStored)
        low=float(-(2**(bits-1)) if d.PixelRepresentation else 0)
        high=float(2**(bits-1)-1 if d.PixelRepresentation else 2**bits-1)
        slope=float(d.get('RescaleSlope',1));intercept=float(d.get('RescaleIntercept',0))
        low=low*slope+intercept;high=high*slope+intercept
    normalized=np.clip((shown-low)/(high-low if high>low else 1),0,1)
    if d.PhotometricInterpretation=='MONOCHROME1':normalized=1-normalized
    png=DEST/f'view-{index+1:02}.png'
    Image.fromarray((normalized*255).round().astype(np.uint8)).save(png)
    # Preserve technical interpretation geometry; remove identifiers, private and answer fields.
    d.remove_private_tags()
    for tag in list(d.keys()):
        element=d[tag]
        if element.VR=='SQ' and element.keyword not in ['ViewCodeSequence','ViewModifierCodeSequence','PatientOrientationCodeSequence','VOILUTSequence','ModalityLUTSequence','PresentationLUTSequence']:
            del d[tag]
        elif element.keyword.startswith(('Patient','ClinicalTrial','Referring','Performing','Operators','Institution','StudyComments','ImageComments','Request','Scheduled','Admitting','AdditionalPatient','Medical','Diagnosis')) and element.keyword not in ['PatientOrientation']:
            del d[tag]
        elif element.VR=='UI' and element.keyword not in ['SOPClassUID','TransferSyntaxUID','ImplementationClassUID']:
            old=str(element.value)
            if old not in uids:uids[old]=generate_uid(entropy_srcs=['benchmark-development-20260930',old])
            element.value=uids[old]
    d.PatientID='BENCHMARK-DEV-MG-001';d.PatientName='Development^Mammography';d.AccessionNumber='DEV-MG-001'
    d.StudyDescription='Benchmark development mammography';d.SeriesDescription='Mammography'
    d.file_meta.MediaStorageSOPInstanceUID=d.SOPInstanceUID
    assert hashlib.sha256(d.PixelData).hexdigest()==before
    target=DEST/f'view-{index+1:02}.dcm';d.save_as(target,enforce_file_format=True)
    rows.append({'pipeline_revision':'development-v2-voi-domain','source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixel_sha256':before,'dicom_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'png_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'png':str(png.relative_to(ROOT)),'png_bytes':png.stat().st_size,'source_dimensions':[d.Columns,d.Rows],'rendered_dimensions':[d.Columns,d.Rows],'bits_delivered':8,'voi':'source VOI LUT/window' if has_voi else 'full dynamic range fallback','display_low':low,'display_high':high,'resized':False,'compression':'lossless PNG','reference_annotations_used':False,'laterality':str(d.get('ImageLaterality',''))})
(ROOT/'evidence/development-rendering.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Prepared',len(rows),'full-resolution development views; no reference data read')
