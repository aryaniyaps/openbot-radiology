#!/usr/bin/env python3
"""Diagnosis-blind prospective IDs, pinned corrected volumes, bounded own downloads."""
import pathlib,json,csv,hashlib,time,shutil,tarfile,concurrent.futures,os
from huggingface_hub import HfApi,hf_hub_download
R=pathlib.Path(__file__).resolve().parents[1];P=R/'private';token=(P/'hf-token').read_text().strip();os.environ['HF_HOME']=str(P/'hf-cache');os.environ['HF_HUB_DOWNLOAD_TIMEOUT']='120'
seed='graysby-report-cohort-v1'
def order(x):return hashlib.sha256((seed+x).encode()).hexdigest()
def download(repo,rev,path,limit=512*1024**2):
 assert shutil.disk_usage(R).free>35*1024**3,'Benchmark disk floor reached'
 info=HfApi(token=token).get_paths_info(repo,[path],repo_type='dataset',revision=rev)[0];assert info.size<limit,'Source exceeds prespecified per-file acquisition limit'
 target=P/'report-cohort-sources'/repo.replace('/','--')/path;target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():
  cached=hf_hub_download(repo,path,repo_type='dataset',revision=rev,token=token,cache_dir=str(P/'hf-cache'));shutil.copyfile(cached,target)
 assert target.stat().st_size==info.size
 return target
ctrev=json.loads((R/'evidence/dataset-revision-ibrahimhamamci-CT-RATE.json').read_text())['revision'];mrrev=json.loads((R/'evidence/dataset-revision-Forithmus-MR-RATE.json').read_text())['revision']
excluded=download('ibrahimhamamci/CT-RATE',ctrev,'dataset/metadata/no_chest_valid.txt',1024**2).read_text().splitlines();excluded={x.strip().replace('.nii.gz','') for x in excluded if x.strip()}
ctreports={x['VolumeName']:x for x in csv.DictReader((P/'ct-valid-reports.csv').open())};ctmeta={x['VolumeName']:x for x in csv.DictReader((P/'ct-valid-metadata.csv').open())};groups={}
for v in ctreports:
 if v not in ctmeta or v.replace('.nii.gz','') in excluded:continue
 pid='_'.join(v.split('_')[:2]);groups.setdefault(pid,[]).append(v)
devct=json.loads((P/'ct-development-selection.json').read_text());devp={x['patient_id'] for x in devct};ids=sorted(set(groups)-devp,key=order)
ct=[dict(case_id=f'CT-EVALUATION-{i+1:03}',patient_id=pid,volume=sorted(groups[pid])[0],stage='evaluation',modality='CT') for i,pid in enumerate(ids[:40])]
ct+=[dict(case_id=f'CT-FRESH-{i+1:03}',patient_id=pid,volume=sorted(groups[pid])[0],stage='fresh-validation',modality='CT') for i,pid in enumerate(ids[40:50])]
for i,x in enumerate(devct):ct.append(dict(x,case_id=f'CT-DEVELOPMENT-{i+1:03}',stage='development',modality='CT'))
mrsource=json.loads((P/'mr-selection-identities.json').read_text());mr=[]
for stage,key,n in [('development','development',5),('evaluation','evaluation',20),('fresh-validation','fresh_validation',10)]:
 items=mrsource.get(key,mrsource.get('fresh',[]) if stage=='fresh-validation' else [])
 for i,x in enumerate(items[:n]):mr.append(dict(x,case_id=f'MR-'+{'development':'DEVELOPMENT','evaluation':'EVALUATION','fresh-validation':'FRESH'}[stage]+f'-{i+1:03}',stage=stage,modality='MR'))
op=json.loads((P/'openi-selection-with-references.json').read_text());print('OpenI selection keys',list(op),flush=True)
selection={'seed':seed,'created_unix':time.time(),'ct':ct,'mr':mr,'ct_exclusion_count':len(excluded),'sampling':'Hash-ranked patient identifiers, one lexicographically first eligible reconstruction/study; no findings or labels used','frozen':False};(P/'report-cohort-selection.json').write_text(json.dumps(selection,indent=2))
def work(x):
 try:
  if x['modality']=='CT':
   v=x['volume'];stem=v.removesuffix('.nii.gz');pid='_'.join(stem.split('_')[:2]);study='_'.join(stem.split('_')[:3]);path=f'dataset/valid_fixed/{pid}/{study}/{v}';repo='ibrahimhamamci/CT-RATE';rev=ctrev
  else:path=f"mri/{x['batch_id']}/{x['study_uid']}.zip";repo='Forithmus/MR-RATE';rev=mrrev
  started=time.time();f=download(repo,rev,path);record=dict(x,source_repo=repo,revision=rev,source_path=path,local_path=str(f.relative_to(R)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),acquisition_seconds=time.time()-started,status='acquired')
 except Exception as e:record=dict(x,status='acquisition-failed',error=type(e).__name__+': '+str(e)[:250])
 target=R/'evidence/acquisition'/x['case_id'];target.parent.mkdir(parents=True,exist_ok=True);target.with_suffix('.json').write_text(json.dumps(record,indent=2));print(json.dumps({k:record.get(k) for k in ['case_id','status','bytes','acquisition_seconds','error']}),flush=True);return record
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(work,ct+mr))
