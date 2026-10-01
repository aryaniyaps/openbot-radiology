from index_native_trace import index
from response_schema import validate
from runtime_slots import acquire,settle,throttle
from owned_bot_archive import recover_capacity
from attachment_capacity import reclaim
#!/usr/bin/env python3
"""One fresh OpenMausbot diagnostic conversation, supplied images only, bounded wall time."""
import argparse,pathlib,json,urllib.request,urllib.error,time,uuid,hashlib,re
p=argparse.ArgumentParser();p.add_argument('--model',required=True,choices=['gpt-6-luna','gpt-6.1-sol','gpt-6-astra','google/medgemma-1.5-4b-it']);p.add_argument('--case',required=True);p.add_argument('--modality',required=True,choices=['CXR','CT','MR']);p.add_argument('--stage',default='development',choices=['development','evaluation','fresh-validation']);p.add_argument('--wall-seconds',type=int,default=180);p.add_argument('--attempt',default='');p.add_argument('--configuration',choices=['primary','delegated','second-reader','self-review'],default='primary');a=p.parse_args();R=pathlib.Path(__file__).resolve().parents[1];case=(R/'agent-visible'/a.case).resolve();assert case.is_relative_to(R/'agent-visible') and case.is_dir();images=sorted(case.glob('*.png'));assert 1<=len(images)<=4
runtime_slot=acquire(a.model)
classes={'CXR':['pleural_effusion','pneumothorax','cardiomegaly','focal_consolidation'],'CT':['pleural_effusion','pulmonary_nodule','consolidation','emphysema'],'MR':['white_matter_signal_abnormality','atrophy','chronic_infarction','mass_lesion']}[a.modality]
prompt='Interpret the supplied '+a.modality+' research-study images independently. All attached views belong to one patient study. Clinical context: imaging modality only; no history or prior study is supplied. The images are all the visual evidence available in this direct-input condition. Describe observed findings, identify a primary imaging conclusion or normal conclusion, and state uncertainty and input limitations. Do not use tools, files, memory, other agents, internet, or known public-case answers. Do not assume that selected volumetric images cover the entire study. Return ONLY one JSON object with keys: primary_diagnosis (string), findings_status (object with exactly the following keys: '+', '.join(classes)+'; each value must be present, absent, uncertain, or unassessable), key_findings (array of short strings), image_references (array of view filenames), urgent_findings (array of short strings), confidence (decimal number from 0 to 1, for example 0.8, subjective probability your primary imaging conclusion is correct), abstention (boolean), limitations (array of short strings). Use uncertain for equivocal findings and unassessable when the provided coverage cannot support a read. Maximum 250 words. At most six key findings, four image references and six limitations. No JSON comments. Image references must use the supplied view filenames, not invented identifiers.'
prompt+=' Study ID: '+case.name+'. Attached views in order: '+', '.join(x.name for x in images)+'.'
def api(path,method='GET',body=None,mime='application/json'):
 data=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request('http://127.0.0.1:18899/api/'+path,method=method,headers={'Content-Type':mime},data=data)
 try:
  with urllib.request.urlopen(req,timeout=20) as f:return json.load(f)
 except urllib.error.HTTPError as e:raise RuntimeError('Own platform HTTP '+str(e.code)+': '+e.read().decode()[:300])
selection={'instanceId':'openaiCompat' if a.model.startswith('google/') else 'codex','model':a.model}
if not a.model.startswith('google/'):selection['effort']='medium'
work=R/'agent-visible/conversation-workspaces'/str(uuid.uuid4());work.mkdir(parents=True);
body={'name':a.stage+' '+case.name+' '+a.model,'useDefaults':False,'modelSelection':selection,'requireAvailableModel':True,'computer':'off','browser':False,'composio':False,'peers':[],'mcpServers':[],'approvalMode':'ask','cwd':str(work),'soul':'Independent blinded research-image interpreter. Use only images attached in this conversation. No clinical report or answer is available. No tools, memory, files, web, or other agents.'}
if a.configuration!='primary':
 baseline_path=R/'evidence'/a.stage/'B'/a.model.replace('/','--')/case.name/'result.json'
 baseline=json.loads(baseline_path.read_text())
 if a.configuration in ['second-reader','self-review']:
  prompt+=' Your original independent answer is already saved. Re-examine the supplied images and revise only if justified by the visual evidence. Original answer: '+json.dumps(baseline.get('structured_answer') or {'invalid_output':True,'raw':baseline.get('raw_answer','')})
 if a.configuration=='second-reader':
  mgpath=R/'evidence'/a.stage/'B/google--medgemma-1.5-4b-it'/case.name/'result.json';mg=json.loads(mgpath.read_text());prompt+=' Independent blinded MedGemma read of exactly these supplied images (may be wrong, not ground truth): '+json.dumps({'status':mg['status'],'read':mg.get('structured_answer'),'invalid_read':mg.get('raw_answer') if not mg.get('structured_answer') else None})
 if a.configuration=='delegated':
  import fcntl
  consultation_lock=(R/'private'/('delegation-'+case.name+'.lock')).open('a');fcntl.flock(consultation_lock,fcntl.LOCK_EX)
  from mcp_capacity import reclaim as reclaim_mcp
  reclaim_mcp(api)
  consultation_nonce=str(uuid.uuid4());name='med_'+case.name.lower().replace('-','_');existing=api('mcp/servers')['servers'];server=next((x for x in existing if x['name']==name),None);mcp_args=[str(R/'scripts/medgemma_read_mcp.py'),case.name,a.stage,consultation_nonce]
  if server:
   assert server['command']=='/usr/bin/python3' and server['args'][:3]==mcp_args[:3],'Unowned specialist config'
   api('mcp/servers/'+name,'PUT',{'command':'/usr/bin/python3','args':mcp_args,'env':{},'enabled':True})
   api('mcp/servers/'+name,'PATCH',{'enabled':True})
  else:
   api('mcp/servers','POST',{'name':name,'command':'/usr/bin/python3','args':mcp_args,'env':{},'enabled':True})
   api('mcp/servers/'+name,'PATCH',{'enabled':True})
  body['mcpServers']=[name];body['soul']='Independent research reader. Only supplied images and the single assigned-study MedGemma tool may be used; no references, files, web, other cases or agents.'
  prompt=prompt.replace('Do not use tools, files, memory, other agents, internet, or known public-case answers.','Use only supplied images plus the assigned-study MedGemma tool; no files, memory, other agents, web or public answers.')
  prompt+=' Before interpreting, call the single get_medgemma_read tool exactly once with study_id='+case.name+', task=independent imaging findings, clinical_context=modality only. Its cached independent image read may be wrong and is not ground truth. Interpret the images yourself and use specialist evidence only where justified. Do not call any other tool.'
reclaim();recover_capacity()
created=api('bots','POST',body);bot=created.get('bot',created);bid=bot['id'];tid=bot['threadId'];receipts=R/'private/bot-create-receipts';receipts.mkdir(exist_ok=True);(receipts/(bid+'.json')).write_text(json.dumps({'bot_id':bid,'thread_id':tid,'case_id':case.name,'stage':a.stage,'model':a.model,'provider_cwd':str(work),'created_unix':time.time()}));out=R/'evidence'/a.stage/('B' if a.configuration=='primary' else 'B-'+a.configuration)/a.model.replace('/','--')/(case.name+('-'+a.attempt if a.attempt else ''));out.mkdir(parents=True,exist_ok=False)
manifest=[];text=prompt
for image in images:
 b=image.read_bytes();assert len(b)<=10*1024**2;v=api('attachments','POST',b,'image/png');v=v.get('attachment',v);manifest.append({'view':image.name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});text+='\n<attached-image path="'+v['path']+'" name="'+image.name+'"/>'
request={'threadId':tid,'sendId':str(uuid.uuid4()),'text':text};record={'case_id':case.name,'stage':a.stage,'arm':'B','configuration':a.configuration,'requested_model':a.model,'modality':a.modality,'model_selection':selection,'bot_id':bid,'thread_id':tid,'provider_cwd':str(work),'input_manifest':manifest,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'wall_limit_seconds':a.wall_seconds,'started_unix':time.time(),'status':'pending'}
(out/'request.json').write_text(json.dumps(request,indent=2));(out/'assignment.json').write_text(json.dumps(record,indent=2));record['provider_start_wait_seconds']=throttle(a.model);api('bots/'+bid+'/messages','POST',request);end=time.monotonic()+a.wall_seconds;approved=set()
while time.monotonic()<end:
 state=api('bots');b=next(x for x in state['bots'] if x['id']==bid)
 if a.configuration=='delegated':
  for m in b['messages']:
   card=m.get('card')
   if card and not card.get('answered') and card.get('requestId') not in approved:
    assert card.get('tool','').endswith('get_medgemma_read'),'Unexpected delegated tool approval'
    api('bots/'+bid+'/respond','POST',{'threadId':tid,'requestId':card['requestId'],'behavior':'allow'});approved.add(card['requestId'])
 if not b.get('busy') and any(m.get('digest') or m.get('turnTerminal') for m in b['messages']):break
 time.sleep(1)
else:
 try:api('bots/'+bid+'/interrupt','POST',{'threadId':tid})
 except Exception as e:record['stop_error']=str(e)
 record['status']='timeout'
 b=settle(bid,tid)
(out/'observation.json').write_text(json.dumps(b,indent=2));digests=[m for m in b['messages'] if m.get('digest')];terminal=[m for m in b['messages'] if m.get('turnTerminal')]
if digests:
 m=digests[-1];record.update(turn_id=m.get('turnId') or m['digest'].get('turnId'),usage=m['digest'].get('usage'),duration_ms=m['digest'].get('durationMs'),tool_calls=m['digest'].get('toolCalls'))
 if not (record['tool_calls']==0 if a.configuration!='delegated' else 1<=record['tool_calls']<=2):record['status']='quarantined';record['policy_rejection']='Unexpected or missing required tool activity'
 if record['status'] not in ['timeout','quarantined']:record['status']='succeeded' if m.get('turnSucceeded') else 'failed'
texts=[m.get('text','') for m in b['messages'] if m.get('role')=='bot' and m.get('kind')=='text' and m.get('turnId')==record.get('turn_id')];answer=next((m['text'] for m in terminal if m.get('turnSucceeded')),texts[-1] if texts else '')
if not answer and digests:answer=digests[-1]['digest'].get('reply','')
record['raw_answer']=answer
if a.configuration=='delegated':
 specialist_path=(R/'private/specialist-development-results'/(case.name+'.json')) if a.stage=='development' else R/'evidence'/a.stage/'B/google--medgemma-1.5-4b-it'/case.name/'result.json'
 specialist=json.loads(specialist_path.read_text());expected_hash=hashlib.sha256(specialist_path.read_bytes()).hexdigest();events=[json.loads(l) for l in (R/'private/specialist-calls.jsonl').read_text().splitlines()] if (R/'private/specialist-calls.jsonl').exists() else []
 consultations=[x for x in events if x.get('consultation_nonce')==consultation_nonce and x.get('case_id')==case.name and x.get('read_sha256')==expected_hash and x['time']>=record['started_unix']]
 record['specialist_consultation_events']=consultations
 observed_tools=[x['tool'] for x in b['messages'] if x.get('tool',{}).get('itemId')]
 if len(consultations)!=1 or specialist['input_manifest']!=manifest or any(not t.get('name','').endswith('get_medgemma_read') or t.get('ok') is False for t in observed_tools):record['status']='quarantined';record['policy_rejection']='Required single case-bound specialist consultation or identical image evidence not proven'

try:
 clean=re.sub(r'^```(?:json)?\s*|\s*```$','',answer.replace('<end_of_turn>','').strip());v=json.loads(clean);assert isinstance(v,dict) and set(v['findings_status'])==set(classes);assert all(x in ['present','absent','uncertain','unassessable'] for x in v['findings_status'].values());record['structured_answer']=validate(v,classes)
except Exception as e:record['parse_error']=type(e).__name__;record['structured_answer']=None
record['finished_unix']=time.time();
if a.configuration!='primary':
 record['original_primary_result']=str(baseline_path.relative_to(R));record['original_primary_sha256']=hashlib.sha256(baseline_path.read_bytes()).hexdigest()
 if a.configuration in ['second-reader','delegated']:
  specialist_path=(R/'private/specialist-development-results'/(case.name+'.json')) if a.stage=='development' else R/'evidence'/a.stage/'B/google--medgemma-1.5-4b-it'/case.name/'result.json'
  record['independent_specialist_result']=str(specialist_path.relative_to(R));record['independent_specialist_sha256']=hashlib.sha256(specialist_path.read_bytes()).hexdigest()

if not a.model.startswith('google/'):record['native_identity']=index(R,record,out)
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'case':record['case_id'],'model':a.model,'status':record['status'],'structured':bool(record['structured_answer']),'duration_ms':record.get('duration_ms'),'result':str(out/'result.json')}))
