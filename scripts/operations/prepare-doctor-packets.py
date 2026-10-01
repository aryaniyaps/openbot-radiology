#!/usr/bin/env python3
"""Prepare clinician-visible packets from native read-only HMS/DICOMweb sources."""
import hashlib, importlib.util, io, json, pathlib, email, urllib.request
import numpy as np
import pydicom
from PIL import Image,ImageDraw
from pydicom.pixels import apply_modality_lut,apply_voi_lut

ROOT=pathlib.Path(__file__).resolve().parents[2]
ORIGINAL=pathlib.Path('/home/aryan/ai-projects/openbot-radiology')
PRIVATE=ROOT/'.private/doctor-packets'
spec=importlib.util.spec_from_file_location('hospital',ORIGINAL/'scripts/server/configure-hospital.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

def get(path,accept='application/dicom+json'):
    q=urllib.request.Request('https://radiology.demo/dicomweb/'+path,headers={'Accept':accept})
    with urllib.request.urlopen(q,timeout=60) as r:return r.headers.get('Content-Type',''),r.read()
def tag(ds,key,default=None):return ds.get(key,{}).get('Value',[default])[0]
def raster(ds,frame=None,window=None):
    pixels=ds.pixel_array
    if frame is not None:pixels=pixels[frame]
    if pixels.ndim==3 and pixels.shape[-1] in [3,4]:return Image.fromarray(pixels.astype(np.uint8)).convert('RGB')
    transformed=apply_modality_lut(pixels,ds)
    values=transformed.astype(np.float32)
    if window:
        center,width=window;low,high=center-width/2,center+width/2
    else:
        try:values=apply_voi_lut(transformed,ds).astype(np.float32)
        except (ValueError,NotImplementedError):pass
        low,high=np.percentile(values,[.5,99.5])
    normalized=np.clip((values-low)/max(float(high-low),1e-6),0,1)
    if ds.get('PhotometricInterpretation')=='MONOCHROME1':normalized=1-normalized
    return Image.fromarray((normalized*255).astype(np.uint8)).convert('RGB')
def fetch_dicom(study,series,instance,destination):
    content,body=get(f'studies/{study}/series/{series}/instances/{instance}', 'multipart/related; type="application/dicom"; transfer-syntax=*')
    if content.startswith('multipart/'):
        message=email.message_from_bytes(b'Content-Type: '+content.encode()+b'\r\nMIME-Version: 1.0\r\n\r\n'+body)
        parts=[p.get_payload(decode=True) for p in message.walk() if p.get_content_type()=='application/dicom'];assert len(parts)==1
        body=parts[0]
    destination.write_bytes(body);ds=pydicom.dcmread(io.BytesIO(body));assert str(ds.SOPInstanceUID)==instance;return ds,hashlib.sha256(body).hexdigest()
def montage(images,labels,title):
    cell=310;tile=Image.new('RGB',(4*cell,52+4*(cell+28)),(17,24,31));draw=ImageDraw.Draw(tile);draw.text((12,16),title,fill='white')
    for i,(image,label) in enumerate(zip(images,labels)):
        x=(i%4)*cell;y=52+(i//4)*(cell+28);scale=min((cell-6)/image.width,(cell-6)/image.height);image=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.LANCZOS);tile.paste(image,(x+(cell-image.width)//2,y+(cell-image.height)//2));draw.text((x+8,y+cell+4),label,fill='white')
    return tile
def main():
    PRIVATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    cases=json.loads((ROOT/'config/doctor/cases.json').read_text());audit=[]
    for c in cases:
        patient=h.request('patient/'+c['patient']+'?v=full',account=h.state['accounts']['pacs_service'])
        assert any(i['identifier']==c['patient_id'] for i in patient['identifiers'])
        orders=h.request('order?patient='+c['patient']+'&v=full',account=h.state['accounts']['pacs_service'])['results']
        assert sum(o['orderNumber']==c['accession'] and o['orderType']['display']=='Radiology Order' for o in orders)==1
        _,body=get('studies?PatientID='+c['patient_id']+'&AccessionNumber='+c['accession']);studies=json.loads(body);assert len(studies)==1 and tag(studies[0],'0020000D')==c['study_uid']
        assert int(tag(studies[0],'00201208'))==c['instances']
        output=ROOT/'config/doctor/packets'/c['patient_id'];output.mkdir(parents=True,exist_ok=True);private=PRIVATE/c['patient_id'];private.mkdir(exist_ok=True)
        _,body=get('studies/'+c['study_uid']+'/series');series=json.loads(body);views=[];sources=[];coverage=[]
        for si,s in enumerate(sorted(series,key=lambda x:str(tag(x,'0020000E')))):
            uid=tag(s,'0020000E');desc=str(tag(s,'0008103E','Source series'))
            _,body=get('studies/'+c['study_uid']+'/series/'+uid+'/instances?includefield=00200013');instances=json.loads(body);instances.sort(key=lambda x:int(tag(x,'00200013',0)))
            chosen=np.linspace(0,len(instances)-1,min(16,len(instances)),dtype=int).tolist() if c['modality'] in ['CT','MR'] else list(range(len(instances)))
            datasets=[];labels=[]
            for index in chosen:
                sop=tag(instances[index],'00080018');ds,sha=fetch_dicom(c['study_uid'],uid,sop,private/(sop+'.dcm'))
                assert str(ds.PatientID)==c['patient_id'] and str(ds.AccessionNumber)==c['accession'] and str(ds.StudyInstanceUID)==c['study_uid']
                datasets.append(ds);labels.append('Instance '+str(ds.get('InstanceNumber',index+1)))
                sources.append({'sop':sop,'series':uid,'native_dicom_sha256':sha,'pixel_sha256':hashlib.sha256(ds.PixelData).hexdigest(),'number_of_frames':int(ds.get('NumberOfFrames',1))})
            if c['modality']=='CT':
                for label,window in [('lung',(-600,1500)),('mediastinal',(40,400))]:
                    filename=f'series-{si+1}-{label}.png';montage([raster(d,window=window) for d in datasets],labels,desc+' | '+label+' window | sampled axial positions').save(output/filename);views.append(filename)
                coverage.append(f'{len(chosen)} of {len(instances)} axial positions, lung and mediastinal windows')
            elif c['modality']=='MR':
                filename=f'series-{si+1}.png';montage([raster(d) for d in datasets],labels,desc+' | sampled source instances').save(output/filename);views.append(filename);coverage.append(desc+f': {len(chosen)} of {len(instances)} instances')
            elif c['modality']=='US':
                assert len(datasets)==1;ds=datasets[0];count=int(ds.get('NumberOfFrames',1));frames=np.linspace(0,count-1,min(16,count),dtype=int).tolist();filename=f'series-{si+1}.png';montage([raster(ds,frame=i) for i in frames],['Spatial frame '+str(i+1) for i in frames],'Spatial ultrasound sweep | sampled frames | not temporal cine').save(output/filename);views.append(filename);coverage.append(f'{len(frames)} of {count} spatial frames; not temporal cine')
            else:
                for index,d in enumerate(datasets):
                    filename=f'view-{len(views)+1:02}.png';im=raster(d);im.thumbnail((1800,1800))
                    if c['modality']=='MG':
                        labelled=Image.new('RGB',(im.width,im.height+40),(17,24,31));labelled.paste(im,(0,40));ImageDraw.Draw(labelled).text((10,12),c['patient_id']+' | '+str(d.get('ImageLaterality','Side unavailable'))+' '+str(d.get('ViewPosition','View unavailable')),fill='white');im=labelled
                    im.save(output/filename);views.append(filename)
                coverage.append(f'{len(datasets)} supplied source views, rendered for display')
        assert 1<=len(views)<=4,'Packet requires grouped native admission; do not silently drop images'
        c['packet_views']=[{'url':'/worklist/packets/'+c['patient_id']+'/'+f,'filename':f,'sha256':hashlib.sha256((output/f).read_bytes()).hexdigest()} for f in views]
        c['assistant_coverage']='; '.join(coverage)
        c['clinical_context']=f"Native patient {c['patient_id']}, {patient['person']['display']}, {patient['person']['gender']}, approximately {patient['person']['age']} years. Synthetic administrative demographics. Radiology order {c['accession']}. No clinical indication or symptom history was added to this practice encounter. Do not infer a diagnosis from the public collection. Source study dates are deidentification-shifted and do not establish the current order date."
        c['assistant_limits']='Rendered images may hide small findings. CT/MRI/ultrasound are sampled presentations, not complete examination review. Full original supplied series remain available in the native viewer. Mammography display resizing limits fine calcification assessment. No prior report or diagnostic reference is supplied.'
        audit.append({'patient_id':c['patient_id'],'accession':c['accession'],'modality':c['modality'],'hms_and_pacs_identifiers_matched':True,'read_only_hms_account':'pacs_service','views':c['packet_views'],'coverage':c['assistant_coverage'],'native_sources':sources})
        print(c['modality'],c['patient_id'],len(views),'native-sourced assigned views prepared')
    (ROOT/'config/doctor/cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    (ROOT/'docs/evidence/hospital-deployment/packet-provenance.json').write_text(json.dumps(audit,indent=2)+'\n')

if __name__=='__main__':main()
