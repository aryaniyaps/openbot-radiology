#!/usr/bin/env python3
"""Encrypted, quiesced backup of this project only. Run as root."""
import datetime,json,os,pathlib,shutil,subprocess,urllib.request
ROOT=pathlib.Path('/home/aryan/ai-projects/openbot-radiology')
STATE=pathlib.Path('/var/lib/kauvery-hospital/backup'); STATE.mkdir(parents=True,exist_ok=True);STATE.chmod(0o700)
REPO='/var/backups/kauvery-hospital/restic';KEY=STATE/'restic-password'
if not KEY.exists():
 import secrets
 KEY.write_text(secrets.token_urlsafe(48));KEY.chmod(0o600)
env=dict(os.environ,RESTIC_REPOSITORY=REPO,RESTIC_PASSWORD_FILE=str(KEY),RESTIC_CACHE_DIR='/var/cache/kauvery-restic')
def run(*args,**kw):return subprocess.run(list(args),check=True,**kw)
if shutil.disk_usage('/').free < 30*1024**3:raise SystemExit('30 GiB storage reserve reached')
try:
 bots=json.load(urllib.request.urlopen('http://127.0.0.1:8799/api/bots',timeout=5))['bots']
 if any(b.get('busy') or b.get('waitingForTeammates') for b in bots):
  print('Assistant active; backup deferred for scheduled retry');raise SystemExit(75)
except OSError: pass
if not pathlib.Path(REPO+'/config').exists():run('restic','init',env=env)
# Freeze desktop processes, preserving persistent files and live browser databases.
names=run('sudo','-n','-u','kauvery-demo','env','XDG_RUNTIME_DIR=/run/user/1001','podman','ps','--format','{{.Names}}',cwd='/tmp',capture_output=True,text=True).stdout.splitlines()
names=[n for n in names if n.startswith('openmausbot-computer-')]
paused=[];running=run('virsh','domstate','kauvery-hospital',capture_output=True,text=True).stdout.strip()=='running'
try:
 for name in names:
  run('sudo','-n','-u','kauvery-demo','env','XDG_RUNTIME_DIR=/run/user/1001','podman','pause',name,cwd='/tmp',stdout=subprocess.DEVNULL);paused.append(name)
 if running:
  run('virsh','shutdown','kauvery-hospital')
  import time
  for _ in range(120):
   if run('virsh','domstate','kauvery-hospital',capture_output=True,text=True).stdout.strip()=='shut off':break
   time.sleep(1)
  else:raise RuntimeError('Guest did not shut down gracefully; no backup made')
 (STATE/'domain.xml').write_text(run('virsh','dumpxml','kauvery-hospital',capture_output=True,text=True).stdout)
 # SQLite online backup removes WAL ambiguity without editing the original DB.
 import sqlite3
 src=sqlite3.connect('file:/home/kauvery-demo/.openmausbot/messages.db?mode=ro',uri=True)
 dst=sqlite3.connect(str(STATE/'messages.db'));src.backup(dst);dst.close();src.close()
 run('restic','backup','--tag','kauvery-hospital','--exclude','**/node_modules','--exclude','**/.cache','--exclude','**/restic-password','--exclude','**/originals','--exclude','**/replay',
     '/var/lib/libvirt/images/kauvery-hospital','/var/lib/kauvery-hospital/workstation-assets',str(STATE),
     '/home/kauvery-demo/.openmausbot','/home/kauvery-demo/.codex','/home/kauvery-demo/.config/openmausbot','/home/kauvery-demo/.local/share/containers/storage/volumes',str(ROOT),env=env)
 run('restic','forget','--tag','kauvery-hospital','--keep-daily','7','--keep-weekly','4',env=env)
 (STATE/'status.json').write_text(json.dumps({'last_success':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repository':REPO,'external_copy':False}))
finally:
 if running and run('virsh','domstate','kauvery-hospital',capture_output=True,text=True).stdout.strip()=='shut off':run('virsh','start','kauvery-hospital')
 for name in paused:run('sudo','-n','-u','kauvery-demo','env','XDG_RUNTIME_DIR=/run/user/1001','podman','unpause',name,cwd='/tmp',stdout=subprocess.DEVNULL)
