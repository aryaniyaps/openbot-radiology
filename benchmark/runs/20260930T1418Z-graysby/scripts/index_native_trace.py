"""Case-bound native identity, sandbox and actual model-visible screenshot index."""
import pathlib,json,hashlib,base64,time
def index(R,rec,out):
 candidates=[]
 for p in (R/'private/provider/sessions').rglob('*.jsonl'):
  if p.stat().st_mtime<rec['started_unix']-5:continue
  with p.open() as f:first=json.loads(f.readline())
  cwd=first.get('payload',{}).get('cwd','')
  if rec['thread_id'] in cwd or (rec.get('provider_cwd') and cwd==rec['provider_cwd']) or (rec['arm']=='B' and not rec.get('provider_cwd') and cwd.endswith('/'+rec['case_id'])):candidates.append(p)
 matches=[]
 for p in candidates:
  data=[json.loads(l) for l in p.open()];texts=json.dumps([x['payload'] for x in data if x.get('type')=='response_item' and x.get('payload',{}).get('type')=='message'])
  if rec['case_id'] in texts:matches.append((p,data))
 # A task cwd is unique. B case cwd reused across configurations, so match request send/time and model.
 matches=[(p,d) for p,d in matches if any(x.get('type')=='turn_context' and x['payload'].get('model')==rec['requested_model'] for x in d)]
 if len(matches)!=1:return {'status':'unresolved','candidate_count':len(matches),'reason':'Audit exact native thread mapping before claiming identity'}
 p,data=matches[0];contexts=[x['payload'] for x in data if x.get('type')=='turn_context'];assert contexts and all(x['model']==rec['requested_model'] for x in contexts),'Model mismatch'
 assert all(x.get('sandbox_policy',{}).get('type')=='read-only' for x in contexts),'Sandbox mismatch'
 screens=[]
 for row in data:
  payload=row.get('payload',{})
  if payload.get('type')!='custom_tool_call_output':continue
  content=payload.get('output',[])
  if not isinstance(content,list):continue
  for part in content:
   if part.get('type')=='input_image' and part.get('image_url','').startswith('data:image/'):
    url=part['image_url'];mime=url.split(';',1)[0];b=base64.b64decode(url.split(',',1)[1]);folder=out/'screenshots';folder.mkdir(exist_ok=True);name=f'viewed-{len(screens)+1:03}.'+('png' if 'png' in mime else 'jpg');(folder/name).write_bytes(b);screens.append({'file':str((folder/name).relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'timestamp':row.get('timestamp'),'call_id':payload.get('call_id')})
 context_text=json.dumps([x.get('payload',{}) for x in data if x.get('type')=='response_item' and x.get('payload',{}).get('type')=='message'])
 prior_context=any(marker in context_text for marker in ['Your recent work','Recalled for this message','Recalled from your other conversations','Relevant memories from','<recalled_context>'])
 receipt={'status':'verified','prior_conversation_context_detected':prior_context,'native_trace':str(p.relative_to(R)),'native_trace_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reported_model':contexts[-1]['model'],'effort':contexts[-1].get('effort'),'sandbox':contexts[-1].get('sandbox_policy'),'screenshots_actually_delivered':screens,'snapshot_identity_limit':'Native provider identifier verified; backend weights/revision are not independently exposed'}
 (out/'native-trace-index.json').write_text(json.dumps(receipt,indent=2));return receipt
