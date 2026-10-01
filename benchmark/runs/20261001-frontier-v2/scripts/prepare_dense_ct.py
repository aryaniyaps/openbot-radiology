#!/usr/bin/env python3
"""Curator-only paired input experiment; original voxel geometry and HU windows."""
import hashlib,json,os,time
from pathlib import Path
import nibabel as nib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];OLD=ROOT/'benchmark/runs/20260930T1418Z-graysby';P=ROOT/'.private/frontier-v2';R=Path(__file__).resolve().parents[1]

def render(data,z,spacing,window):
    c,w=window;gray=np.clip((data[::-1,::-1,z].T-(c-w/2))/w*255,0,255).astype(np.uint8)
    physical=(gray.shape[1]*spacing[0],gray.shape[0]*spacing[1]);scale=min(512/physical[0],512/physical[1]);size=(max(1,round(physical[0]*scale)),max(1,round(physical[1]*scale)))
    tile=Image.new('RGB',(512,512));tile.paste(Image.fromarray(gray).resize(size,Image.Resampling.BILINEAR),((512-size[0])//2,(512-size[1])//2));return tile

def main():
    routine=json.loads((R/'PROTOCOL-ROUTINE.json').read_text())['cases'];selected=[]
    for row in sorted(routine,key=lambda x:x['case_id']):
        if row['modality']!='CT':continue
        ref=json.loads((P/'references'/(row['case_id']+'.json')).read_text())
        if ref['labels']['pulmonary_nodule']['state']=='present':selected.append((row,ref))
        if len(selected)==2:break
    assert len(selected)==2;cases=[];receipts=[]
    for i,(row,ref) in enumerate(selected,1):
        source_record=json.loads((OLD/'evidence/acquisition'/(row['original_case_id']+'.json')).read_text());source=OLD/source_record['local_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==source_record['sha256']
        im=nib.as_closest_canonical(nib.load(source));data=np.asanyarray(im.dataobj);assert len(data.shape)==3 and np.isfinite(data).all();spacing=np.linalg.norm(im.affine[:3,:3],axis=0);dirs=im.affine[:3,:3]/spacing;assert np.max(np.abs(dirs.T@dirs-np.eye(3)))<.01
        indices=np.unique(np.rint(np.linspace(.05,.95,64)*(data.shape[2]-1)).astype(int));windows=[(-600,1500),(40,400)]
        id=f'DENSE-CT-{i:03}';out=P/'agent-visible'/id;out.mkdir(parents=True,exist_ok=True);views=[]
        for start in range(0,len(indices),2):
            group=indices[start:start+2];sheet=Image.new('RGB',(1024,1080));draw=ImageDraw.Draw(sheet)
            for j,z in enumerate(group):
                for k,window in enumerate(windows):
                    x=k*512;y=j*540;sheet.paste(render(data,int(z),spacing,window),(x,y+28));draw.text((x+8,y+6),f'CT axial slice {z+1}/{data.shape[2]} R | L; W/L {window[1]}/{window[0]}',fill='white')
            name=f'view-{len(views)+1:03}.png';sheet.save(out/name);views.append({'file':name,'indices_zero_based':list(map(int,group)),'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),'pixels':list(sheet.size)})
        packet={'case_id':id,'stage':'evaluation','modality':'CT','clinical_context':'Modality only; clinical history and prior images not supplied','image_files':[x['file'] for x in views],'coverage':f'{len(indices)} uniformly sampled axial slice positions from 5-95% of one released chest CT volume, with lung and mediastinal windows. Still not a complete examination.','input_limitations':['Fixed sampling can still omit small lesions','Source-derived uncalibrated raster montages','No contrast status inferred','No original full examination or priors'],'target_findings':['pleural_effusion','pulmonary_nodule','consolidation','emphysema'],'source_type':'Existing translated physician radiology report'}
        (out/'input.json').write_text(json.dumps(packet,indent=2)+'\n');rp=P/'references'/(id+'.json');rp.write_text(json.dumps(dict(ref,case_id=id,baseline_case_id=row['case_id']),indent=2)+'\n');rp.chmod(0o600)
        cases.append({'case_id':id,'stage':'evaluation','modality':'CT','cohort':'adaptive denser CT presentation experiment','baseline_case_id':row['case_id'],'images':len(views),'input_sha256':hashlib.sha256((out/'input.json').read_bytes()).hexdigest(),'images_sha256':[x['sha256'] for x in views],'reference_sha256':hashlib.sha256(rp.read_bytes()).hexdigest()})
        receipts.append({'case_id':id,'baseline_case_id':row['case_id'],'source_sha256':source_record['sha256'],'source_shape':list(data.shape),'canonical_affine':im.affine.tolist(),'spacing_mm':spacing.tolist(),'source_orientation':'Canonical RAS voxel reindexing, x/y reversal for radiological axial display; identical geometry recipe to prior run, no volumetric interpolation','source_intensity_range':[float(data.min()),float(data.max())],'windows':windows,'views':views})
        os.chown(out,1000,1000)
        for f in out.iterdir():os.chown(f,1000,1000)
    protocol={'frozen_unix':time.time(),'models':['gpt-6.1-sol','gpt-6-astra'],'effort':'high','cases':cases,'motivation':'Primary 16-slice montages leave most report-positive small nodules unresolved. Test denser coverage and larger per-tile delivery as a mechanism experiment; do not replace primary failures or claim hospital accuracy.','selection':'First two primary CT case IDs with an explicit existing positive pulmonary-nodule report assertion, regardless of either model result; no selection by per-case errors','recipe':'64 uniformly spaced axial positions, both HU windows, two slice positions per 1024x1080 montage, successive native four-image turns','changes_bundled':['Fourfold slice sampling','Smaller montage canvas preserving per-tile delivery','More native conversational turns'],'causality':'Bundled input presentation experiment, not isolated proof for one factor','metric':'Same-patient report-assertion detection versus original primary, with latency/token overhead; n=2 exploratory only','primary_scope':'Same patients as primary; never inflate unique-patient N or overwrite primary results'}
    for filename,value in [('PROTOCOL-DENSE-CT.json',protocol),('evidence/dense-ct-preprocessing.json',receipts)]:
        path=R/filename;path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(value,indent=2)+'\n');os.chown(path,1000,1000)
    print(json.dumps({'patients':len(cases),'native_images_each':[x['images'] for x in cases],'baseline_cases':[x['baseline_case_id'] for x in cases]}))

if __name__=='__main__':main()
