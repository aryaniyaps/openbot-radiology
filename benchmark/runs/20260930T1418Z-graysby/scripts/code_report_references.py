#!/usr/bin/env python3
"""Conservative auditable report assertions; omission != negative. No clinical adjudication."""
import pathlib,csv,json,re,hashlib,time,collections
R=pathlib.Path(__file__).resolve().parents[1];P=R/'private'
CLASSES={'CXR':['pleural_effusion','pneumothorax','cardiomegaly','focal_consolidation'],'CT':['pleural_effusion','pulmonary_nodule','consolidation','emphysema'],'MR':['white_matter_signal_abnormality','atrophy','chronic_infarction','mass_lesion']}
PATTERNS={'pleural_effusion':r'pleural\s+(?:fluid|effusion)|pleural.{0,50}effusion','pneumothorax':r'pneumothora(?:x|ces)','cardiomegaly':r'cardiomegaly|(?:heart|cardiac|cardiomediastinal).{0,35}(?:enlarg|\bnormal\b|within normal)|enlarg.{0,25}(?:heart|cardiac|cardiomediastinal)','focal_consolidation':r'consolidat\w*','consolidation':r'consolidat\w*','pulmonary_nodule':r'(?:(?:pulmonary|lung|parenchyma|upper lobe|lower lobe|middle lobe|subpleural).{0,130}(?:nodule(?:s)?|nodular lesion)|(?:nodule(?:s)?|nodular lesion).{0,130}(?:lung|parenchyma|pulmonary|upper lobe|lower lobe|middle lobe|subpleural))','emphysema':r'emphysema\w*|emphysematous','white_matter_signal_abnormality':r'(?:white matter|periventricular|centrum semiovale|corona radiata).{0,100}(?:hyperintens|signal|foci|small vessel|ischemi)|(?:hyperintens|signal|small vessel|ischemi|foci).{0,100}(?:white matter|periventricular|centrum semiovale|corona radiata)','atrophy':r'atroph\w*','chronic_infarction':r'chronic.{0,40}infarct|infarct.{0,40}(?:chronic|sequelae)|sequelae.{0,40}infarct','mass_lesion':r'(?:intracranial|cerebral|brain).{0,50}(?:mass|space.occupying)|(?:mass|space.occupying).{0,50}(?:intracranial|cerebral|brain)|space.occupying lesion|mass lesion'}
NEG=re.compile(r'\bno\b|\bwithout\b|\bnot\b|\babsent\b|\bnegative\b|\bneither\b|free of|clear of',re.I)
UNC=re.compile(r'\b(?:possible|possibly|suspicious|suspected|cannot exclude|could represent|questionable|may represent|equivocal|borderline|probable|likely|potentially|possible|limited|resolution|resolved|have cleared)\b',re.I)
def assertions(text,cls):
 hits=[]
 for raw in re.split(r'(?<=[.;\n])\s+|\n|\bbut\b|\bhowever\b',text):
  clause=raw.strip();low=clause.lower()
  if not re.search(PATTERNS[cls],low):continue
  if cls=='mass_lesion' and 'massa intermedia' in low:continue
  if cls=='mass_lesion' and any(x in low for x in ['liver','adrenal','orbit','sinus']):continue
  if cls=='white_matter_signal_abnormality' and re.search(r'signal.{0,30}(?:normal|natural)',low) and not re.search(r'hyperintens|abnormal|ischemi|small vessel',low):state='absent'
  elif cls=='cardiomegaly' and re.search(r'\bnormal\b|within normal',low) and not re.search(r'enlarg|cardiomegaly',low):state='absent'
  elif UNC.search(low) or re.search(r'(?:no|not).{0,25}(?:large|significant|gross|definite|sizable)',low):state='ambiguous'
  elif NEG.search(low):
   match=re.search(PATTERNS[cls],low);before=low[max(0,match.start()-85):match.start()];after=low[match.end():match.end()+45]
   local_prefix=before.rsplit(',',1)[-1]
   explicit=bool(re.search(r'\b(?:no|without|neither|absent)\b|clear of|free of',local_prefix) or re.search(r'\bnot\s+(?:seen|observed|detected|identified|noted|present|visualized)',after))
   if re.search(r'\b(?:with|although|except|apart from)\b',low) or not explicit:state='ambiguous'
   else:state='absent'
  elif re.search(r'\bor\b',low) and not re.search(r'present|observed|seen|identified|noted|detected|mild|moderate|severe|small|large|trace|multiple|millimet',low):state='ambiguous'
  else:state='present'
  hits.append({'state':state,'quote':clause})
 states={x['state'] for x in hits};state=next(iter(states)) if len(states)==1 else 'ambiguous' if states else 'unscorable'
 return {'state':state,'evidence':hits,'reason':'No explicit report assertion' if not hits else 'Conflicting or uncertain report assertions' if state=='ambiguous' else 'Explicit report assertion, mechanically coded; not independent clinical adjudication'}
if __name__=='__main__':
 op=json.loads((P/'openi-selection-with-references.json').read_text());sel=json.loads((P/'report-cohort-selection.json').read_text());ct={x['VolumeName']:x for x in csv.DictReader((P/'ct-valid-reports.csv').open())};mr={x['study_uid']:x for x in csv.DictReader((P/'mr-batch00-reports.csv').open())};refs=[]
 for key,n in [('development',10),('evaluation',60),('fresh_validation',10)]:
  for x in op[key][:n]:
   f=x['reference'];text=f.get('FINDINGS','')+'\n'+f.get('IMPRESSION','');refs.append({'case_id':x['benchmark_id'],'modality':'CXR','stage':key.replace('_','-'),'patient_id':'OpenI:'+x['source_report_id'],'reference_source':x['reference_xml'],'reference_text':text,'labels':{c:assertions(text,c) for c in CLASSES['CXR']},'reference_processing':'Published deidentified physician report; source XXXX redactions preserved','reference_sha256':hashlib.sha256(text.encode()).hexdigest()})
 for x in sel['ct']+sel['mr']:
  if x['modality']=='CT':f=ct[x['volume']];text=f['Findings_EN']+'\n'+f['Impressions_EN'];pid='CT-RATE:'+x['patient_id'];source=x['volume'];processing='Author-released English radiology report, translated from Turkish; not newly adjudicated'
  else:f=mr[x['study_uid']];text=f['findings']+'\n'+f['impression'];pid='MR-RATE:'+x['patient_uid'];source=x['study_uid'];processing='Author translation/restructuring of existing Turkish radiology report with Qwen3.5-35B-A3B-FP8; potentially inconsistent or incomplete'
  refs.append({'case_id':x['case_id'],'modality':x['modality'],'stage':x['stage'],'patient_id':pid,'reference_source':source,'reference_text':text,'labels':{c:assertions(text,c) for c in CLASSES[x['modality']]},'reference_processing':processing,'reference_sha256':hashlib.sha256(text.encode()).hexdigest()})
 for row in refs:
  if row['case_id']=='CXR-EVALUATION-036':
   row['labels']['focal_consolidation']['state']='ambiguous'
   row['labels']['focal_consolidation']['reason']='Prospective audit: XXXX redaction may conceal diagnostic qualifier; excluded before any evaluation output'
 assert len({r['case_id'] for r in refs})==len(refs)
 out=R/'scoring/references/report-references.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'coded_unix':time.time(),'policy':'Explicit sentence/clause assertions only; omitted labels unscorable; uncertain/conflicting assertions ambiguous; physician reports are not exhaustive truth; no LLM correctness judge','cases':refs},indent=2));out.chmod(0o600)
 print(json.dumps({'cases':len(refs),'evaluation_by_modality':dict(collections.Counter(x['modality'] for x in refs if x['stage']=='evaluation')),'label_states':{m:dict(collections.Counter(y['state'] for x in refs if x['stage']=='evaluation' and x['modality']==m for y in x['labels'].values())) for m in CLASSES}},indent=2))
