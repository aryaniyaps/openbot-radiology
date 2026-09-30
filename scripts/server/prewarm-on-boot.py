#!/usr/bin/env python3
"""Once per host boot, prepare the six native desktops through supported app APIs."""
import json,pathlib,urllib.request,urllib.error,time,os
ROOT=pathlib.Path(__file__).resolve().parents[2];marker=pathlib.Path('/var/lib/kauvery-hospital/desktop-boot-id');boot=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
try:
 session_path=ROOT/'.private/server/operator-session.json'
 credential=json.loads(session_path.read_text());token=credential['token']
 def request(path,payload=None,method=None):
  req=urllib.request.Request('http://127.0.0.1:8799/api/'+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'},method=method)
  return json.load(urllib.request.urlopen(req,timeout=120))
 if credential['session']['expiresAt']-int(time.time()*1000)<7*86400000:
  pairing=request('auth/pairing',{'label':'Local hospital workstation maintenance','scopes':['admin','client']})
  renewed=request('auth/pair',{'code':pairing['code'],'label':'Local hospital workstation maintenance'})
  old_id=credential['session']['id'];token=renewed['token']
  request('auth/sessions') # Confirm the replacement is live before persisting it.
  temporary=session_path.with_suffix('.renewing');temporary.write_text(json.dumps(renewed));temporary.chmod(0o600);os.replace(temporary,session_path)
  request('auth/sessions/'+old_id,method='DELETE')
  print('Native maintenance session renewed')
 if marker.exists() and marker.read_text().strip()==boot:raise SystemExit(0)
 bots=request('bots')['bots'];selected=[b for b in bots if b['computer']=='vm']
 if len(selected)!=6:raise RuntimeError('Expected six configured native VM roles')
 if any(b.get('busy') or b.get('waitingForTeammates') for b in bots):
  print('Boot preparation deferred while assistants work');raise SystemExit(0)
 for bot in selected:
  path='bots/'+bot['id']+'/local-computer';s=request(path)
  if s.get('container')=='running':continue
  if s.get('container')=='stopped':
   if not s.get('managed') or s.get('persistence')!='durable':raise RuntimeError('Unverified stopped desktop; operator review required')
   request(path+'/remove',{})
  elif s.get('container')!='missing':raise RuntimeError('Unexpected native desktop state')
  r=request(path+'/run',{});assert r['container']=='running' and r['persistence']=='durable'
  print(bot['name'],'native desktop prepared',flush=True)
 marker.write_text(boot+'\n');marker.chmod(0o600)
except OSError as e:
 print('Native app not ready for boot preparation; timer will retry',type(e).__name__);raise SystemExit(0)
