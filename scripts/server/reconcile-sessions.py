#!/usr/bin/env python3
"""Renew native read-only browser sessions after a server reboot, while assistants are idle."""
import json,pathlib,subprocess,time,urllib.request,http.cookies
from workstation import run
from guest import SSH
ROOT=pathlib.Path(__file__).resolve().parents[2];statefile=ROOT/'.private/server/session-state.json'
try:
 bots=json.load(urllib.request.urlopen('http://127.0.0.1:8799/api/bots',timeout=5))['bots']
except OSError:
 bots=[] # The app can be closed overnight; dedicated browser sessions still need renewal.
if any(b['busy'] or b.get('waitingForTeammates') for b in bots):
 print('Session reconciliation deferred while an assistant is active');raise SystemExit(0)
try:
 if urllib.request.urlopen('https://radiology.demo/openmrs/ws/rest/v1/session',timeout=5).status!=200:raise OSError('Hospital not ready')
except OSError:
 print('Hospital not ready; timer will retry');raise SystemExit(0)
boot=subprocess.check_output(SSH+['cat /proc/sys/kernel/random/boot_id'],text=True).strip()
containers=json.loads(run('ps','--format','json',capture_output=True,text=True).stdout)
identities={c['Names'][0]:c['Id'] for c in containers if c['Names'][0].startswith('openmausbot-computer-')}
if statefile.exists():
 previous=json.loads(statefile.read_text())
 if previous.get('boot_id')==boot and previous.get('container_ids')==identities:raise SystemExit(0)
s=json.loads((ROOT/'.private/server/hospital-state.json').read_text());mapping={'b5d05486b0d0102b':'clinical','b220bf79ca0808d4':'workflow','76775bc343c61e6a':'reportcheck','911a0acc4783b93b':'reportdraft','daff52065908e226':'image','57dd7131d2c87b34':'caseprep'}
evidence=[]
for suffix,name in mapping.items():
 c='openmausbot-computer-'+suffix
 # Dedicated native browser profile: close cleanly, clear only this demo site's expired cookies.
 script='''import pathlib,sqlite3,subprocess,time
subprocess.run(['pkill','-TERM','-x','firefox-esr']);time.sleep(2)
for p in pathlib.Path('/home/cua/.mozilla').rglob('cookies.sqlite'):
 con=sqlite3.connect(p);con.execute("delete from moz_cookies where host in ('radiology.demo','.radiology.demo')");con.commit();con.close()
'''
 run('exec','--user','cua','-i',c,'/home/cua/workspace/operator-venv/bin/python','-',input=script,text=True)
 run('exec','--user','cua',c,'sh','-c','firefox https://radiology.demo/bahmni/home/#/login >/home/cua/workspace/browser-operator.log 2>&1 &')
 time.sleep(4);a=s['accounts']['assistant_'+name]
 script='import sys,types,time;sys.modules["mouseinfo"]=types.ModuleType("mouseinfo");import pyautogui;pyautogui.click(650,459);pyautogui.hotkey("ctrl","a");pyautogui.write('+repr(a['username'])+',interval=0.03); pyautogui.press("tab");pyautogui.hotkey("ctrl","a");pyautogui.write('+repr(a['password'])+',interval=0.05); pyautogui.press("tab");pyautogui.press("enter");time.sleep(5);pyautogui.click(672,328);pyautogui.click(685,464);pyautogui.press("o");pyautogui.press("enter");pyautogui.click(676,515);time.sleep(2)'
 run('exec','--user','cua','-i',c,'/home/cua/workspace/operator-venv/bin/python','-',input=script,text=True)
 # Verify the browser's actual native session, without reading or exporting cookies.
 expression='fetch("/openmrs/ws/rest/v1/session").then(r=>r.json()).then(s=>{document.title=s.authenticated?"Authenticated "+s.user.username:"Session unavailable"})'
 script='import sys,types,time;sys.modules["mouseinfo"]=types.ModuleType("mouseinfo");import pyautogui;pyautogui.hotkey("ctrl","shift","k");time.sleep(1);pyautogui.write('+repr(expression)+',interval=0.003);pyautogui.press("enter");time.sleep(2);pyautogui.hotkey("ctrl","shift","i")'
 run('exec','--user','cua','-i',c,'/home/cua/workspace/operator-venv/bin/python','-',input=script,text=True)
 windows=json.loads(run('exec','--user','cua',c,'/usr/local/libexec/openmausbot/cua-driver','--socket','/run/user/1000/openmausbot-cua.sock','call','list_windows','{}',capture_output=True,text=True).stdout)['windows']
 assert any(('Authenticated '+a['username']) in w.get('title','') for w in windows),name+' native browser session was not established'
 script='import sys,types,time;sys.modules["mouseinfo"]=types.ModuleType("mouseinfo");import pyautogui;pyautogui.hotkey("ctrl","l");pyautogui.write("https://radiology.demo/");pyautogui.press("enter");time.sleep(1)'
 run('exec','--user','cua','-i',c,'/home/cua/workspace/operator-venv/bin/python','-',input=script,text=True)
 evidence.append({'role':name,'username':a['username'],'authenticated_native_browser_session':True});print(name,'native session verified',flush=True)
statefile.write_text(json.dumps({'boot_id':boot,'container_ids':identities,'accounts':evidence}));statefile.chmod(0o600)
(ROOT/'docs/evidence/local-hospital/desktop-sessions.json').write_text(json.dumps(evidence,indent=2))
