import pathlib,fcntl,time,os,json,shutil,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def guard(existing_assignment=False):
 while (R/'private/scheduling-pause').exists():time.sleep(.5)
 flag=R/'private/scheduling-stop.json'
 if flag.exists():raise RuntimeError('Owned benchmark safety stop: '+flag.read_text()[:200])
 if shutil.disk_usage(R).free<35*1024**3:raise RuntimeError('Free-disk floor')
 values=[]
 for p in (R/'evidence').glob('*/*/*/*/result.json'):
  try:values.append(json.loads(p.read_text()))
  except Exception:pass
 inp=sum((r.get('usage') or {}).get('input',0) or 0 for r in values);out=sum((r.get('usage') or {}).get('output',0) or 0 for r in values)
 from native_only_usage import totals
 supplement=totals(R);inp+=supplement['input_tokens'];out+=supplement['output_tokens']
 calls=sum(1 for _ in (R/'evidence').rglob('assignment.json'))
 if inp>=98000000 or out>=980000 or (calls>1002 if existing_assignment else calls>=1002):
  flag.write_text(json.dumps({'time_unix':time.time(),'reason':'Shared resource guard with pending-request headroom','input':inp,'output':out,'diagnostic_conversations_created':calls}));raise RuntimeError('Shared token/request ceiling')
def acquire(model):
 family='medgemma' if model.startswith('google/') else 'codex'
 while True:
  guard()
  for n in range(1 if family=='medgemma' else 2):
   f=(R/'private'/(family+'-runtime-slot-'+str(n)+'.lock')).open('a')
   try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);guard();return f
   except BlockingIOError:f.close()
  time.sleep(.2)
def settle(bid,tid):
 end=time.monotonic()+25
 while time.monotonic()<end:
  with urllib.request.urlopen('http://127.0.0.1:18899/api/bots',timeout=20) as f:b=next(x for x in json.load(f)['bots'] if x['id']==bid)
  if not b.get('busy'):return b
  time.sleep(.5)
 (R/'private/scheduling-stop.json').write_text(json.dumps({'time_unix':time.time(),'reason':'Own interrupted native turn not confirmed idle','bot_id':bid,'thread_id':tid}));raise RuntimeError('Own native turn did not settle; stop scheduling')
def throttle(model):
 if model.startswith('google/'):return 0.
 import subprocess,sys
 start=time.monotonic()
 with (R/'private/diagnostic-provider-start.lock').open('a+') as f:
  fcntl.flock(f,fcntl.LOCK_EX);p=R/'private/diagnostic-provider-start.json';last=json.loads(p.read_text())['started_unix'] if p.exists() else 0.;delay=10-(time.time()-last)
  if delay>0:time.sleep(delay)
  guard(existing_assignment=True);check=subprocess.run([sys.executable,str(R/'scripts/provider_budget.py')],capture_output=True,text=True,timeout=70)
  if check.returncode:
   (R/'private/scheduling-stop.json').write_text(json.dumps({'time_unix':time.time(),'reason':'Provider allowance guard','error':check.stderr[-600:]}));raise RuntimeError('Provider allowance stop before clinical request')
  p.write_text(json.dumps({'started_unix':time.time()}))
 return time.monotonic()-start
