#!/usr/bin/env python3
"""Losslessly wrap published OpenI grayscale PNG pixels for the existing DICOM viewer."""
import pathlib,json,hashlib,sys
import numpy as np,pydicom
from pydicom.dataset import FileDataset,FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian,SecondaryCaptureImageStorage,generate_uid
from PIL import Image
R=pathlib.Path(__file__).resolve().parents[1];folder=pathlib.Path(sys.argv[1]).resolve();assert folder.is_relative_to(R/'agent-visible');images=sorted(folder.glob('*.png'));assert images
study=generate_uid();series=generate_uid();rows=[]
for i,p in enumerate(images):
 im=Image.open(p);a=np.asarray(im)
 if a.ndim==3:
  assert np.all(a[:,:,0]==a[:,:,1]) and np.all(a[:,:,1]==a[:,:,2]),'Color content requires a separate faithful conversion';a=a[:,:,0]
 assert a.dtype==np.uint8 and a.ndim==2
 fm=FileMetaDataset();fm.MediaStorageSOPClassUID=SecondaryCaptureImageStorage;fm.MediaStorageSOPInstanceUID=generate_uid();fm.TransferSyntaxUID=ExplicitVRLittleEndian;fm.ImplementationClassUID=generate_uid()
 out=folder/(p.stem+'.dcm');ds=FileDataset(str(out),{},file_meta=fm,preamble=b'\0'*128);ds.SOPClassUID=fm.MediaStorageSOPClassUID;ds.SOPInstanceUID=fm.MediaStorageSOPInstanceUID;ds.StudyInstanceUID=study;ds.SeriesInstanceUID=series;ds.PatientName='Research^Study';ds.PatientID=folder.name;ds.StudyDate='20000101';ds.StudyTime='120000';ds.Modality='DX';ds.SeriesDescription='Published source radiograph views';ds.StudyDescription='Research chest radiography';ds.AccessionNumber=hashlib.sha256(folder.name.encode()).hexdigest()[:16];ds.SeriesNumber=1;ds.InstanceNumber=i+1;ds.ConversionType='WSD';ds.Manufacturer='Benchmark research conversion';ds.Rows=a.shape[0];ds.Columns=a.shape[1];ds.SamplesPerPixel=1;ds.PhotometricInterpretation='MONOCHROME2';ds.BitsAllocated=8;ds.BitsStored=8;ds.HighBit=7;ds.PixelRepresentation=0;ds.WindowCenter=127.5;ds.WindowWidth=256;ds.PixelData=a.tobytes();ds.save_as(out,enforce_file_format=True)
 assert np.array_equal(pydicom.dcmread(out).pixel_array,a)
 rows.append({'view':p.name,'dicom':out.name,'png_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pixel_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'rows':a.shape[0],'columns':a.shape[1]})
# No invented physical spacing or orientation. Original public raster, not native source DICOM.
(R/'evidence'/('wrap-'+folder.name+'.json')).write_text(json.dumps({'case':folder.name,'source':'Published OpenI PNG, derived secondary capture','patient_spacing':'unknown; measurements not supported','side_orientation':'only original visible radiographic markers; no invented geometry','lossless_pixels_verified':True,'views':rows},indent=2)+'\n');print('Lossless viewer wrapper',folder.name,len(rows),'views')
