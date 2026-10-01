import pathlib,json,time,subprocess,threading,fcntl,urllib.request
from runtime_slots import guard,settle
R=pathlib.Path(__file__).resolve().parents[1];P=json.loads((R/'PROTOCOL.json').read_text());PY=str(R/'private/venv/bin/python')
def path(a):return R/'evidence'/a['stage']/('A' if a['arm']=='A' else 'B' if a['configuration']=='primary' else 'B-'+a['configuration'])/a['model'].replace('/','--')/(a['case_id']+('-'+a['attempt'] if a['attempt'] else ''))/'result.json'
queue=json.loads((R/"evidence/transport-retry-queue.json").read_text()) if (R/"evidence/transport-retry-queue.json").exists() else []
for a in P['assignments']:
 p=path(a)
 if not p.exists():continue
 d=json.loads(p.read_text())
 if d.get('status')!='controller_failure' or 'this workspace is limited to 100 bots' not in d.get('exception',''):continue
 assert a['arm']=='B' and a['configuration']=='primary';assert not (p.parent/'assignment.json').exists() and not (p.parent/'request.json').exists() and not d.get('structured_answer') and not d.get('native_identity')
 dest=R/'private/transport-failures'/a['stage']/a['model'].replace('/','--')/p.parent.name;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();p.parent.rename(dest);queue.append(dict(a,original_failure_path=str((dest/'result.json').relative_to(R)),original_started_unix=d['started_unix']))
(R/'evidence/transport-retry-queue.json').write_text(json.dumps(queue,indent=2));print('Eligible no-clinical-action transport retries',len(queue),flush=True)
# Let pre-semaphore children finish within the pre-existing controller wall cap.
enabled=json.loads((R/'private/runtime-slots-enabled-at.json').read_text())['enabled_unix']
while time.time()<enabled+320:time.sleep(5)
def event(d):
 with (R/'evidence/transport-retries.jsonl').open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**d))+'\n')
def run(items):
 for a in items:
  guard()
  if not a['model'].startswith('google/'):
   with (R/'private/batch-budget.lock').open('a+') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX);statep=R/'private/provider-throttle.json';state=json.loads(statep.read_text());delay=10-(time.time()-state['last_started'])
    if delay>0:time.sleep(delay)
    check=subprocess.run([PY,str(R/'scripts/provider_budget.py')],capture_output=True,text=True,timeout=70)
    if check.returncode:event({'retry_not_started':a,'budget_error':check.stderr[-600:]});break
    state.update(last_started=time.time(),calls=state['calls']+1);statep.write_text(json.dumps(state))
  cmd=[PY,str(R/'scripts/run_direct_case.py'),'--case',a['stage']+'/'+a['case_id'],'--model',a['model'],'--modality',a['modality'],'--stage',a['stage'],'--attempt',a['attempt']]
  event({'retry_started':a});start=time.time()
  try:
   v=subprocess.run(cmd,capture_output=True,text=True,timeout=600);event({'retry_finished':a,'returncode':v.returncode,'stdout':v.stdout[-1000:],'stderr':v.stderr[-1200:]})
   if v.returncode and (path(a).parent/'assignment.json').exists():
    owned=json.loads((path(a).parent/'assignment.json').read_text());req=urllib.request.Request('http://127.0.0.1:18899/api/bots/'+owned['bot_id']+'/interrupt',data=json.dumps({'threadId':owned['thread_id']}).encode(),headers={'Content-Type':'application/json'});urllib.request.urlopen(req,timeout=20).close();settle(owned['bot_id'],owned['thread_id'])
   if not path(a).exists():
    path(a).parent.mkdir(parents=True,exist_ok=True);path(a).write_text(json.dumps({'case_id':a['case_id'],'stage':a['stage'],'arm':a['arm'],'configuration':a['configuration'],'requested_model':a['model'],'modality':a['modality'],'status':'controller_failure','structured_answer':None,'exception':v.stderr[-1800:],'started_unix':start,'finished_unix':time.time()},indent=2))
   if path(a).exists():
    r=json.loads(path(a).read_text());r['transport_retry']={'no_clinical_action_before_retry':True,'original_failure_path':a['original_failure_path'],'original_request_started_unix':a['original_started_unix'],'retry_started_unix':start,'total_first_request_to_closure_seconds':time.time()-a['original_started_unix']};path(a).write_text(json.dumps(r,indent=2)+'\n')
  except Exception as e:
   assignment=path(a).parent/'assignment.json'
   if assignment.exists():
    r=json.loads(assignment.read_text());req=urllib.request.Request('http://127.0.0.1:18899/api/bots/'+r['bot_id']+'/interrupt',data=json.dumps({'threadId':r['thread_id']}).encode(),headers={'Content-Type':'application/json'});urllib.request.urlopen(req,timeout=20).close();settle(r['bot_id'],r['thread_id'])
   event({'retry_controller_exception':a,'error':str(e)});break
mg=[a for a in queue if a['model'].startswith('google/')];gpt=[a for a in queue if not a['model'].startswith('google/')];t=threading.Thread(target=run,args=(mg,));t.start();run(gpt);t.join();event({'retry_queue_finished':True,'assigned_retries':len(queue)})
