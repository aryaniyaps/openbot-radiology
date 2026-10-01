#!/usr/bin/env python3
"""Curator-only, report-backed routine cohorts. Never modifies the previous run."""
import hashlib,json,os,shutil,sys,tarfile,time,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OLD=ROOT/'benchmark/runs/20260930T1418Z-graysby';P=ROOT/'.private/frontier-v2'
sys.path.insert(0,str(OLD/'scripts'))
from code_report_references import assertions,CLASSES

def main():
    prior=json.loads((OLD/'private/openi-selection-with-references.json').read_text())
    used={x['source_report_id'] for key in ['development','evaluation','fresh_validation'] for x in prior[key]}
    eligible=[]
    with tarfile.open(OLD/'private/openi-reports.tgz') as t:
        for m in t.getmembers():
            if not m.isfile() or not m.name.endswith('.xml'):continue
            r=ET.fromstring(t.extractfile(m).read());id=r.find('uId').get('id');imgs=[x.get('id') for x in r.findall('parentImage')];ref={x.get('Label'):''.join(x.itertext()) for x in r.findall('.//AbstractText')}
            if id in used or not 1<=len(imgs)<=2 or not ref.get('FINDINGS') or not ref.get('IMPRESSION'):continue
            text=ref['FINDINGS']+'\n'+ref['IMPRESSION'];labels={c:assertions(text,c) for c in CLASSES['CXR']}
            eligible.append({'source_id':id,'images':imgs,'reference':ref,'labels':labels,'source_xml':m.name,'license':r.findtext('licenseURL')})
    with tarfile.open(OLD/'private/openi-images.tgz') as t:names={Path(x.name).stem for x in t.getmembers() if x.isfile() and x.name.endswith('.png')}
    eligible=[x for x in eligible if all(i in names for i in x['images'])]
    order=lambda x:hashlib.sha256(('frontier-v2-routine-cohort'+x['source_id']).encode()).hexdigest()
    positive=sorted([x for x in eligible if any(y['state']=='present' for y in x['labels'].values())],key=order)
    negative=sorted([x for x in eligible if all(y['state']=='absent' for y in x['labels'].values())],key=order)
    selected=[];chosen=set()
    for cls in CLASSES['CXR']:
        group=[x for x in positive if x['source_id'] not in chosen and x['labels'][cls]['state']=='present']
        for x in group[:5]:selected.append(x);chosen.add(x['source_id'])
    for x in positive:
        if len(selected)>=20:break
        if x['source_id'] not in chosen:selected.append(x);chosen.add(x['source_id'])
    selected+=negative[:20];targets={};manifest=[]
    for i,x in enumerate(selected,1):
        id='ROUTINE-CXR-'+f'{i:03}';out=P/'agent-visible'/id;out.mkdir(parents=True,exist_ok=True)
        packet={'case_id':id,'stage':'evaluation','modality':'CXR','clinical_context':x['reference'].get('INDICATION','Not supplied'),
                'image_files':[f'view-{j:03}.png' for j in range(1,len(x['images'])+1)],
                'coverage':'All released views for this OpenI patient study. No prior images.',
                'input_limitations':['Deidentified public study; pretraining exposure unknown','Released PNG images, no calibrated DICOM'],
                'target_findings':CLASSES['CXR'],'source_type':'Existing deidentified physician radiology report'}
        (out/'input.json').write_text(json.dumps(packet,indent=2)+'\n')
        for j,img in enumerate(x['images'],1):targets[img+'.png']=out/f'view-{j:03}.png'
        (P/'references'/(id+'.json')).write_text(json.dumps(dict(x,case_id=id,modality='CXR',stage='evaluation',reference_processing='Existing physician report; explicit assertions mechanically coded before model output; no new adjudication'),indent=2)+'\n')
        manifest.append({'case_id':id,'stage':'evaluation','modality':'CXR','source_id':x['source_id'],'images':len(x['images']),'cohort':'fresh-v2-report-enriched OpenI'})
    with tarfile.open(OLD/'private/openi-images.tgz',mode='r|gz') as t:
        for m in t:
            name=Path(m.name).name
            if name in targets:targets[name].write_bytes(t.extractfile(m).read())
    assert all(x.exists() for x in targets.values())
    # Re-evaluate previous held-out CT/MR packets for a paired model comparison.
    # Explicitly disclose reuse and the original sampled-montage coverage.
    refs=json.loads((OLD/'scoring/references/report-references.json').read_text())['cases']
    for modality,limit in [('CT',20),('MR',10)]:
        rows=sorted([x for x in refs if x['stage']=='evaluation' and x['modality']==modality],key=lambda x:hashlib.sha256(('frontier-v2-reused-'+x['case_id']).encode()).hexdigest())[:limit]
        for i,x in enumerate(rows,1):
            id='ROUTINE-'+modality+f'-{i:03}';out=P/'agent-visible'/id;out.mkdir(parents=True,exist_ok=True)
            src=OLD/'agent-visible/evaluation'/x['case_id'];images=sorted(src.glob('*.png'));assert images
            for j,image in enumerate(images,1):shutil.copyfile(image,out/f'view-{j:03}.png')
            packet={'case_id':id,'stage':'evaluation','modality':modality,'clinical_context':'Modality only; clinical history and prior images not supplied',
                    'image_files':[f'view-{j:03}.png' for j in range(1,len(images)+1)],'coverage':'Previous benchmark fixed sampled montages; not a complete original examination.',
                    'input_limitations':['Selected slices and sequence representatives','Public dataset, previous-run cohort reuse','Translated/restructured existing report'],'target_findings':CLASSES[modality],
                    'source_type':'Existing translated physician radiology report'}
            (out/'input.json').write_text(json.dumps(packet,indent=2)+'\n')
            (P/'references'/(id+'.json')).write_text(json.dumps(dict(x,case_id=id,original_case_id=x['case_id']),indent=2)+'\n')
            manifest.append({'case_id':id,'stage':'evaluation','modality':modality,'source_id':x['reference_source'],'original_case_id':x['case_id'],'images':len(images),'cohort':'reused prior report-backed '+modality})
    uid=ROOT.stat().st_uid;gid=ROOT.stat().st_gid
    for row in manifest:
        folder=P/'agent-visible'/row['case_id'];os.chown(folder,uid,gid)
        for f in folder.iterdir():os.chown(f,uid,gid)
    (P/'routine-manifest.json').write_text(json.dumps({'cases':manifest,'seed':'frontier-v2-routine-cohort','eligible_fresh_cxr':len(eligible),'positive_pool':len(positive),'negative_pool':len(negative),'prepared_unix':time.time()},indent=2)+'\n')
    print(json.dumps({'cases':len(manifest),'fresh_cxr':len(selected),'CT':20,'MR':10}))

if __name__=='__main__':main()
