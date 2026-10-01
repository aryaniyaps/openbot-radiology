#!/usr/bin/env python3
"""Single assigned study, cached independent image interpretation, no source/report access."""
import json,sys,pathlib,time,hashlib,os
R=pathlib.Path(__file__).resolve().parents[1];case=sys.argv[1];stage=sys.argv[2];nonce=sys.argv[3];assert case.replace('-','').isalnum() and stage in ['development','evaluation','fresh-validation']
path=(R/'private/specialist-development-results'/(case+'.json')) if stage=='development' else R/'evidence'/stage/'B/google--medgemma-1.5-4b-it'/case/'result.json';calls=0
tool={'name':'get_medgemma_read','description':'Return the independently acquired MedGemma interpretation of the exact assigned supplied study images. This is a cached blinded image read, not a clinical reference. It may be wrong or incomplete. Maximum one request; no other study accessible.','inputSchema':{'type':'object','properties':{'study_id':{'type':'string','enum':[case]},'task':{'type':'string','enum':['independent imaging findings']},'clinical_context':{'type':'string','enum':['modality only']}},'required':['study_id','task','clinical_context'],'additionalProperties':False}}
for line in sys.stdin:
 try:
  d=json.loads(line);id=d.get('id');method=d.get('method');params=d.get('params',{});result=None
  if method=='initialize':result={'protocolVersion':params.get('protocolVersion','2024-11-05'),'capabilities':{'tools':{}},'serverInfo':{'name':'benchmark-medgemma-single-study','version':'1'}}
  elif method=='tools/list':result={'tools':[tool]}
  elif method=='tools/call':
   args=params['arguments'];assert params['name']=='get_medgemma_read' and args=={'study_id':case,'task':'independent imaging findings','clinical_context':'modality only'};assert calls==0,'Single specialist-call budget exhausted';calls+=1;read=json.loads(path.read_text());payload={'study_id':case,'visual_evidence':read['input_manifest'],'model':read['requested_model'],'execution_status':read['status'],'independent_of_primary':True,'clinical_context':'modality only','read':read.get('structured_answer'),'unstructured_read_if_invalid':read.get('raw_answer') if not read.get('structured_answer') else None,'limitations':'Cached independent MedGemma image interpretation; no original doctor report or ground truth; may be incorrect. No additional follow-up permitted.'};result={'content':[{'type':'text','text':json.dumps(payload)}]}
   log=R/'private/specialist-calls.jsonl'
   with log.open('a') as f:f.write(json.dumps({'time':time.time(),'consultation_nonce':nonce,'case_id':case,'arguments':args,'read_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'status':read['status']})+'\n')
  elif method in ['resources/list','resources/templates/list']:result={'resources':[]} if method=='resources/list' else {'resourceTemplates':[]}
  elif method=='ping':result={}
  elif id is not None:raise ValueError('Unsupported method')
  if id is not None:print(json.dumps({'jsonrpc':'2.0','id':id,'result':result}),flush=True)
 except Exception as e:
  if d.get('id') is not None:print(json.dumps({'jsonrpc':'2.0','id':d['id'],'error':{'code':-32602,'message':str(e)[:300]}}),flush=True)
