#!/usr/bin/env python3
"""Reference-blind NIfTI presentation; source geometry, intensity and coverage receipt."""
import pathlib,json,sys,zipfile,hashlib,time,argparse,shutil
import numpy as np,nibabel as nib,pydicom
from pydicom.dataset import FileDataset,FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian,CTImageStorage,MRImageStorage,generate_uid
from PIL import Image,ImageDraw
R=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('case');ap.add_argument('--dicom',action='store_true');a=ap.parse_args();record=json.loads((R/'evidence/acquisition'/a.case).with_suffix('.json').read_text());assert record['status']=='acquired';mod=record['modality'];start=time.time()
out=R/'agent-visible'/record['stage']/a.case;out.mkdir(parents=True,exist_ok=True);work=R/'private/volume-work'/a.case;work.mkdir(parents=True,exist_ok=True)
source=R/record['local_path'];files=[]
if mod=='CT':files=[('CT',source)]
else:
 with zipfile.ZipFile(source) as z:
  for name in sorted(z.namelist()):
   if '/img/' not in name or not name.endswith('.nii.gz'):continue
   # Do not copy segmentations, brain masks, defacing masks or any annotation.
   fname=pathlib.Path(name).name;family=fname.split('_',1)[-1].split('-raw')[0]
   f=work/fname;f.write_bytes(z.read(name));files.append((family,f))
assert files,'No eligible source image volumes'
prepared=[]
for idx,(family,f) in enumerate(files):
 im=nib.as_closest_canonical(nib.load(f));assert len(im.shape)==3,'4D inputs need a separately frozen temporal condition';data=np.asanyarray(im.dataobj);assert np.isfinite(data).all();assert data.shape[2]>=8
 # Canonical reindexing preserves source voxels, affine and obliquity; no interpolation.
 affine=im.affine;spacing=np.linalg.norm(affine[:3,:3],axis=0);dirs=affine[:3,:3]/spacing
 assert np.max(np.abs(dirs.T@dirs-np.eye(3)))<.01,'Nonorthogonal source geometry requires separate resampling protocol'
 if mod=='CT':
  assert np.min(data)>=-32768 and np.max(data)<=32767 and np.allclose(data,np.rint(data));stored=data.astype(np.int16);slope=1.;intercept=0.;windows=[(-600,1500),(40,400)]
 else:
  lo=float(data.min());hi=float(data.max());assert hi>lo
  if np.issubdtype(data.dtype,np.integer) and lo>=0 and hi<=65535:stored=data.astype(np.uint16);slope=1.;intercept=0.
  else:slope=(hi-lo)/65535;intercept=lo;stored=np.rint((data-lo)/slope).astype(np.uint16)
  nz=data[data>np.min(data)];low,high=np.percentile(nz,[1,99.5]);windows=[(float((low+high)/2),float(max(high-low,1)))]
 prepared.append({'family':family,'data':data,'stored':stored,'affine':affine,'spacing':spacing,'slope':slope,'intercept':intercept,'windows':windows,'source':f,'index':idx+1})
chosen=[]
if mod=='CT':chosen=prepared
else:
 for family in ['flair','t2w','t1w','swi','mra','other']:
  options=[p for p in prepared if p['family']==family]
  if options:chosen.append(options[0])
 for p in prepared:
  if all(p is not q for q in chosen) and len(chosen)<4:chosen.append(p)
 chosen=chosen[:4]
views=[]
def render(p,z,window):
 c,w=window;arr=p['data'][::-1,::-1,z].T;gray=np.clip((arr-(c-w/2))/w*255,0,255).astype(np.uint8)
 # Maintain physical aspect ratio, letterbox at source resolution up to 512.
 sx,sy=p['spacing'][:2];physical=(gray.shape[1]*sx,gray.shape[0]*sy);scale=min(512/physical[0],512/physical[1]);size=(max(1,round(physical[0]*scale)),max(1,round(physical[1]*scale)));tile=Image.new('RGB',(512,512));tile.paste(Image.fromarray(gray).resize(size,Image.Resampling.BILINEAR),((512-size[0])//2,(512-size[1])//2));return tile
for p in chosen:
 indices=np.unique(np.rint(np.linspace(.05,.95,16 if mod=='CT' else 12)*(p['data'].shape[2]-1)).astype(int))
 for wi,window in enumerate(p['windows']):
  groups=[indices[:8],indices[8:]] if mod=='CT' else [indices]
  for group in groups:
   if len(views)>=4:break
   sheet=Image.new('RGB',(2048,3*540 if mod=='MR' else 1080));draw=ImageDraw.Draw(sheet)
   for j,z in enumerate(group):
    x=(j%4)*512;y=(j//4)*540;sheet.paste(render(p,int(z),window),(x,y+28));draw.text((x+8,y+6),f"{p['family']} axial slice {int(z)+1}/{p['data'].shape[2]} R | L; W/L {window[1]:.0f}/{window[0]:.0f}",fill='white')
   name=f'view-{len(views)+1:02}.png';sheet.save(out/name);views.append({'file':name,'series':p['index'],'family':p['family'],'indices_zero_based':list(map(int,group)),'window_level':window,'canvas_pixels':sheet.size,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()})
series_manifest=[dict(series=p['index'],family=p['family'],source_sha256=hashlib.sha256(p['source'].read_bytes()).hexdigest(),shape=list(p['data'].shape),affine=p['affine'].tolist(),spacing_mm=p['spacing'].tolist(),source_dtype=str(p['data'].dtype),stored_dtype=str(p['stored'].dtype),rescale_slope=p['slope'],rescale_intercept=p['intercept'],window_levels=p['windows']) for p in prepared]
if a.dicom:
 assert shutil.disk_usage(R).free>35*1024**3
 dest=out/'dicom';dest.mkdir(exist_ok=True);study=generate_uid();frame=generate_uid();LPS=np.diag([-1,-1,1])
 for p in prepared:
  arr=p['stored'];aff=p['affine'];sp=p['spacing'];series=generate_uid();col=LPS@(-aff[:3,0]/sp[0]);row=LPS@(-aff[:3,1]/sp[1]);c,w=p['windows'][0]
  for k in range(arr.shape[2]):
   pixels=np.ascontiguousarray(arr[::-1,::-1,k].T);pos=LPS@(aff@np.array([arr.shape[0]-1,arr.shape[1]-1,k,1]))[:3];file=dest/f'series-{p["index"]:02}-slice-{k+1:05}.dcm';fm=FileMetaDataset();fm.MediaStorageSOPClassUID=CTImageStorage if mod=='CT' else MRImageStorage;fm.MediaStorageSOPInstanceUID=generate_uid();fm.TransferSyntaxUID=ExplicitVRLittleEndian;fm.ImplementationClassUID=generate_uid();ds=FileDataset(str(file),{},file_meta=fm,preamble=b'\0'*128)
   ds.SOPClassUID=fm.MediaStorageSOPClassUID;ds.SOPInstanceUID=fm.MediaStorageSOPInstanceUID;ds.StudyInstanceUID=study;ds.SeriesInstanceUID=series;ds.FrameOfReferenceUID=frame;ds.PatientName='Research^Study';ds.PatientID=a.case;ds.StudyDate='20000101';ds.StudyTime='120000';ds.Modality=mod;ds.StudyDescription='Research '+mod;ds.SeriesDescription=f'Source {p["family"]} series {p["index"]}';ds.AccessionNumber=hashlib.sha256(a.case.encode()).hexdigest()[:16];ds.SeriesNumber=p['index'];ds.InstanceNumber=k+1;ds.ImageType=['DERIVED','SECONDARY','AXIAL'];ds.Rows=pixels.shape[0];ds.Columns=pixels.shape[1];ds.SamplesPerPixel=1;ds.PhotometricInterpretation='MONOCHROME2';ds.BitsAllocated=16;ds.BitsStored=16;ds.HighBit=15;ds.PixelRepresentation=1 if pixels.dtype==np.int16 else 0;ds.PixelSpacing=[format(float(sp[1]),".10g"),format(float(sp[0]),".10g")];ds.SliceThickness=format(float(sp[2]),".10g");ds.SpacingBetweenSlices=format(float(sp[2]),".10g");ds.ImageOrientationPatient=[format(float(x),".10g") for x in np.r_[col,row]];ds.ImagePositionPatient=[format(float(x),".10g") for x in pos];ds.RescaleSlope=str(p['slope']);ds.RescaleIntercept=str(p['intercept']);ds.WindowCenter=str(c);ds.WindowWidth=str(w);ds.PixelData=pixels.tobytes();ds.save_as(file,enforce_file_format=True)
   if k in [0,arr.shape[2]//2,arr.shape[2]-1]:assert np.array_equal(pydicom.dcmread(file).pixel_array,pixels)
receipt={'case_id':a.case,'modality':mod,'stage':record['stage'],'source_sha256':record['sha256'],'direct_images':views,'total_series':len(prepared),'total_axial_slices':sum(p['data'].shape[2] for p in prepared),'direct_selected_series':len(chosen),'source_conversion':'Derived research DICOM from NIfTI, not native source DICOM','orientation':'RAS canonical index permutation then x/y reversal; physical affine converted to LPS; no interpolation','technical_series':series_manifest,'dicom_prepared':a.dicom,'preprocessing_seconds':time.time()-start,'limitations':['Fixed uniform axial sampling can omit pathology','Up to four MRI series selected by sequence family and lexical order','No contrast status inferred','Defaced MRI may lose facial information','Volumetric input is montage images, not native volumetric model input']}
(R/'evidence'/('preprocess-'+a.case+'.json')).write_text(json.dumps(receipt,indent=2));shutil.rmtree(work);print(json.dumps({'case':a.case,'views':len(views),'series':len(prepared),'slices':receipt['total_axial_slices'],'dicom':a.dicom,'seconds':receipt['preprocessing_seconds']}))
