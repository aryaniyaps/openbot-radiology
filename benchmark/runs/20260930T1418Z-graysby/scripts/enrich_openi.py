#!/usr/bin/env python3
"""Before held-out inference: prespecified report-stratified enrichment, not image oracle selection."""
import pathlib,json,tarfile,xml.etree.ElementTree as ET,hashlib,collections,time,shutil
from code_report_references import assertions,CLASSES
R=pathlib.Path(__file__).resolve().parents[1];P=R/'private';old=json.loads((P/'openi-selection-with-references.json').read_text());dev={x['source_report_id'] for x in old['development']};seed='graysby-report-enrichment-v1';order=lambda x:hashlib.sha256((seed+x['source_report_id']).encode()).hexdigest()
eligible=[]
with tarfile.open(P/'openi-reports.tgz') as t:
 for m in t.getmembers():
  if not m.isfile() or not m.name.endswith('.xml'):continue
  root=ET.fromstring(t.extractfile(m).read());id=root.find('uId').get('id');imgs=[x.get('id') for x in root.findall('parentImage')];ref={x.get('Label'):''.join(x.itertext()) for x in root.findall('.//AbstractText')}
  if not 1<=len(imgs)<=2 or not ref.get('FINDINGS','').strip() or not ref.get('IMPRESSION','').strip() or id in dev:continue
  text=ref['FINDINGS']+'\n'+ref['IMPRESSION'];labels={c:assertions(text,c) for c in CLASSES['CXR']};eligible.append({'source_report_id':id,'images':imgs,'reference':ref,'reference_xml':m.name,'license':root.findtext('licenseURL'),'labels':labels})
# Source PNG membership established from the already acquired archive's published manifest.
with tarfile.open(P/'openi-images.tgz') as t:names={pathlib.Path(x.name).stem for x in t.getmembers() if x.isfile() and x.name.endswith('.png')}
eligible=[x for x in eligible if all(i in names for i in x['images'])];positive=sorted([x for x in eligible if any(v['state']=='present' for v in x['labels'].values())],key=order);negative=sorted([x for x in eligible if all(v['state']=='absent' for v in x['labels'].values())],key=order)
assert len(positive)>=45 and len(negative)>=25,(len(positive),len(negative))
# Allocate ten to each disease where possible, then fill remaining positives by hash.
selected=[];used=set();strata=collections.Counter()
for c in CLASSES['CXR']:
 group=[x for x in positive if x['source_report_id'] not in used and x['labels'][c]['state']=='present']
 for x in group[:10]:selected.append(x);used.add(x['source_report_id']);strata[c]+=1
for x in positive:
 if len(selected)>=40:break
 if x['source_report_id'] not in used:selected.append(x);used.add(x['source_report_id']);strata['positive_fill']+=1
selected+=negative[:20];fresh=[x for x in positive if x['source_report_id'] not in used][:5]+negative[20:25];new=dict(old,evaluation=[],fresh_validation=[])
for key,items in [('evaluation',selected),('fresh_validation',fresh)]:
 for i,x in enumerate(items):
  x=dict(x);x.pop('labels');x['benchmark_id']='CXR-'+('EVALUATION' if key=='evaluation' else 'FRESH')+f'-{i+1:03}';new[key].append(x)
backup=P/'openi-natural-selection-pre-freeze.json';backup=backup if not backup.exists() else P/('openi-selection-prefreeze-'+str(int(time.time()))+'.json');backup.write_text(json.dumps(old,indent=2));(P/'openi-selection-with-references.json').write_text(json.dumps(new,indent=2));
(R/'evidence/openi-enrichment-decision.json').write_text(json.dumps({'time_unix':time.time(),'before_any_heldout_model_output':not (R/'evidence/evaluation').exists(),'reason':'Natural initial sample had too few explicit positive report assertions to estimate omission rates. Prespecified prospective report-based enrichment before inference; no lesion-selected images','seed':seed,'eligible_pool':len(eligible),'report_positive_pool':len(positive),'explicit_all_target_negative_pool':len(negative),'positive_evaluation_studies':40,'negative_evaluation_studies':20,'allocation_strata':dict(strata),'fresh_studies':10,'population_weighting':'No population prevalence/PPV or pooled representative accuracy claim; report each task and source enrichment separately'},indent=2))
# Quarantine all old neutral inputs before replacing; no model outputs exist for them.
for stage in ['evaluation','fresh-validation']:
 folder=R/'agent-visible'/stage;q=P/'quarantine-prefreeze-inputs'/str(int(time.time()))/stage;q.mkdir(parents=True,exist_ok=True)
 for f in folder.glob('CXR-*'):shutil.move(str(f),str(q/f.name))
targets={};manifest=[]
for key,stage in [('evaluation','evaluation'),('fresh_validation','fresh-validation')]:
 for row in new[key]:
  folder=R/'agent-visible'/stage/row['benchmark_id'];folder.mkdir(parents=True)
  for i,id in enumerate(row['images']):targets[id+'.png']=folder/f'view-{i+1:02}.png'
  manifest.append({'case_id':row['benchmark_id'],'modality':'CXR','stage':stage,'source_report_id':row['source_report_id'],'source_image_ids':row['images'],'published_views':len(row['images'])})
count=0
with tarfile.open(P/'openi-images.tgz',mode='r|gz') as t:
 for m in t:
  name=pathlib.Path(m.name).name
  if name in targets:targets[name].write_bytes(t.extractfile(m).read());count+=1
assert count==len(targets)
(R/'evidence/openi-selected-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'eligible':len(eligible),'positive':len(positive),'negative':len(negative),'allocation':dict(strata),'images':count}))
