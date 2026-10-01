#!/usr/bin/env python3
import pathlib,json,time,subprocess,threading,fcntl,hashlib,traceback,shutil,sys,urllib.request
R=pathlib.Path(__file__).resolve().parents[1];P=json.loads((R/'PROTOCOL.json').read_text());PY=str(R/'private/venv/bin/python');models=P['models'];stop=threading.Event();guard=threading.Lock();counts=0
log=R/'evidence/batch-events.jsonl'
def event(d):
 with guard:
  with log.open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**d))+'\n')
def path(a):return R/'evidence'/a['stage']/('A' if a['arm']=='A' else 'B' if a['configuration']=='primary' else 'B-'+a['configuration'])/a['model'].replace('/','--')/(a['case_id']+('-'+a['attempt'] if a['attempt'] else ''))/'result.json'
def reserve(a):
 global counts
 if stop.is_set():return False
 if shutil.disk_usage(R).free<35*1024**3:stop.set();event({'failure':'disk-floor'});return False
 with (R/'private/batch-budget.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  results=[]
  for p in (R/'evidence').glob('*/*/*/*/result.json'):
   try:results.append(json.loads(p.read_text()))
   except Exception:pass
  inp=sum((r.get('usage') or {}).get('input',0) or 0 for r in results);out=sum((r.get('usage') or {}).get('output',0) or 0 for r in results)
  from native_only_usage import totals
  supplement=totals(R);inp+=supplement['input_tokens'];out+=supplement['output_tokens']
  if counts>=1002 or inp>=100000000 or out>=1000000:stop.set();event({'failure':'budget-ceiling','input_tokens':inp,'output_tokens':out,'assigned_started':counts});return False
  if not a['model'].startswith('google/'):
   statep=R/'private/provider-throttle.json';state=json.loads(statep.read_text()) if statep.exists() else {'last_started':0,'calls':0}
   delay=10-(time.time()-state['last_started'])
   if delay>0:time.sleep(delay)
   if True: # Check allowance before every start; preserve quota headroom
    b=subprocess.run([PY,str(R/'scripts/provider_budget.py')],capture_output=True,text=True,timeout=70)
    event({'allowance_check':b.returncode,'output':b.stdout[-600:],'error':b.stderr[-600:]})
    if b.returncode:stop.set();return False
   state.update(last_started=time.time(),calls=state['calls']+1);statep.write_text(json.dumps(state))
  counts+=1
 return True
worker_failures=[]
def settle(a):
 assignment=path(a).parent/'assignment.json'
 if not assignment.exists():return
 r=json.loads(assignment.read_text());bid=r['bot_id'];tid=r['thread_id']
 try:
  req=urllib.request.Request('http://127.0.0.1:18899/api/bots/'+bid+'/interrupt',data=json.dumps({'threadId':tid}).encode(),headers={'Content-Type':'application/json'});urllib.request.urlopen(req,timeout=15).close()
  end=time.monotonic()+20
  while time.monotonic()<end:
   with urllib.request.urlopen('http://127.0.0.1:18899/api/bots',timeout=15) as f:b=next(x for x in json.load(f)['bots'] if x['id']==bid)
   if not b['busy']:return
   time.sleep(.5)
  raise RuntimeError('Owned inference did not settle')
 except Exception as e:stop.set();event({'settle_failed':a,'error':str(e)})
def run(a):
 recovery=None
 prior_queue=json.loads((R/'evidence/transport-retry-queue.json').read_text()) if (R/'evidence/transport-retry-queue.json').exists() else []
 prior=next((x for x in prior_queue if all(x.get(k,'')==a.get(k,'') for k in ['stage','case_id','arm','configuration','model','attempt'])),None)
 if prior:recovery={'no_clinical_action_before_retry':True,'original_request_started_unix':prior['original_started_unix'],'original_failure_path':prior['original_failure_path']}
 existing=path(a)
 if existing.exists():
  old=json.loads(existing.read_text())
  setup_failure=old.get('status')=='controller_failure' and any(x in old.get('exception','') for x in ['this workspace is limited to 100 bots','attachments storage is full','You can add at most 20 MCP servers.',"Permission denied: '"+str(R/'private/mcp-registration-capacity.lock')+"'"])
  if not setup_failure:return
  assert a['arm']=='B' and not (existing.parent/'assignment.json').exists() and not (existing.parent/'request.json').exists() and not old.get('native_identity') and not old.get('structured_answer')
  recovery=old.get('transport_retry') or {'no_clinical_action_before_retry':True,'original_request_started_unix':old['started_unix']}
  archive=R/'private/transport-failures-v2'/str(time.time_ns())/existing.parent.name;archive.parent.mkdir(parents=True);existing.parent.rename(archive)
  recovery['original_failure_path']=str((archive/'result.json').relative_to(R))
  event({'no_clinical_action_setup_recovery':a,'archive':str(archive.relative_to(R))})
 elif (existing.parent/'assignment.json').exists():
  event({'unresolved_prior_dispatch_not_retried':a});return
 if not reserve(a):return
 cmd=[PY,str(R/'scripts'/('run_viewer_case.py' if a['arm']=='A' else 'run_direct_case.py')),'--case',a['stage']+'/'+a['case_id'],'--model',a['model'],'--modality',a['modality'],'--stage',a['stage'],'--wall-seconds',str(120 if a['arm']=='A' and a['modality']=='CXR' else 180)]
 if a['arm']=='A':cmd+=['--step-limit',str(16 if a['modality']=='CXR' else 24)]
 else:cmd+=['--configuration',a['configuration'],'--attempt',a['attempt']]
 event({'start':a});start=time.time()
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=600)
  event({'finish':a,'returncode':p.returncode,'elapsed_seconds':time.time()-start,'stdout':p.stdout[-1200:],'stderr':p.stderr[-1800:]})
  if p.returncode:settle(a)
  if p.returncode and not path(a).exists():
   out=path(a);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps({'case_id':a['case_id'],'stage':a['stage'],'arm':a['arm'],'configuration':a['configuration'],'requested_model':a['model'],'modality':a['modality'],'status':'controller_failure','structured_answer':None,'exception':p.stderr[-1800:],'started_unix':start,'finished_unix':time.time()},indent=2))
 except Exception as e:
  event({'exception':a,'error':str(e)});worker_failures.append(str(e));settle(a)
 if recovery and path(a).exists():
  r=json.loads(path(a).read_text());recovery.update(retry_started_unix=start,total_first_request_to_closure_seconds=time.time()-recovery['original_request_started_unix']);r['transport_retry']=recovery;path(a).write_text(json.dumps(r,indent=2)+'\n')
def worker(items):
 try:
  for a in items:
   if stop.is_set():break
   run(a)
 except Exception:event({'worker_exception':traceback.format_exc()});stop.set()
def viewer():
 try:
  pairs=[a for a in P['assignments'] if a['arm']=='A'];last=None
  for a in pairs:
   if stop.is_set():break
   if path(a).exists():continue # Never reconstruct or rerun terminal viewer reads on controller resume.
   cid=a['case_id'];folder=R/'agent-visible/evaluation'/cid
   if cid!=last and a['modality']!='CXR':
    p=subprocess.run([PY,str(R/'scripts/prepare_volume.py'),cid,'--dicom'],capture_output=True,text=True,timeout=300);event({'preparation':cid,'returncode':p.returncode,'stdout':p.stdout[-600:],'stderr':p.stderr[-600:]});assert p.returncode==0
   run(a)
   last=cid
   nxt=pairs[pairs.index(a)+1]['case_id'] if pairs.index(a)+1<len(pairs) else None
   if nxt!=cid and a['modality']!='CXR':shutil.rmtree(folder/'dicom')
 except Exception:event({'viewer_exception':traceback.format_exc()});stop.set()
primary_gpt=[a for a in P['assignments'] if a['arm']=='B' and a['configuration']=='primary' and not a['model'].startswith('google/')]
mg=[a for a in P['assignments'] if a['model'].startswith('google/')]
v=threading.Thread(target=viewer);m=threading.Thread(target=worker,args=(mg,));v.start();m.start()
# One direct GPT lane until dedicated graphical lane finishes; then two lanes.
idx=0
while idx<len(primary_gpt) and v.is_alive() and not stop.is_set():run(primary_gpt[idx]);idx+=1
remaining=primary_gpt[idx:];w=threading.Thread(target=worker,args=(remaining[::2],));w.start();worker(remaining[1::2]);w.join();m.join()
roles=[a for a in P['assignments'] if a['arm']=='B' and a['configuration']!='primary']
# Role reads depend on saved direct baselines/specialist reads, not graphical reads.
# Preserve one B lane while A is active; the shared runtime locks still cap GPT at2.
idx=0
while idx<len(roles) and v.is_alive() and not stop.is_set():run(roles[idx]);idx+=1
remaining_roles=roles[idx:]
# Assign whole case groups to each lane: no case MCP lock collision and no
# dedicated slow-consultation lane after the other conditions have finished.
case_groups={}
for assignment in remaining_roles:case_groups.setdefault(assignment['case_id'],[]).append(assignment)
groups=list(case_groups.values())
lanes=[sum(groups[offset::2],[]) for offset in [0,1]]
w=threading.Thread(target=worker,args=(lanes[0],));w.start();worker(lanes[1]);w.join();v.join()
event({'batch_complete':True,'stopped_by_budget_or_safety':stop.is_set(),'started_calls':counts,'worker_failures':worker_failures})
print('Batch finished',counts,'started; stopped',stop.is_set())
