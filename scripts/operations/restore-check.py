#!/usr/bin/env python3
"""Restore encrypted checkpoint and boot a clone with NO network interface."""
import json,os,pathlib,subprocess,time,uuid,xml.etree.ElementTree as E,base64
ROOT=pathlib.Path('/home/aryan/ai-projects/openbot-radiology');TARGET=pathlib.Path('/var/lib/kauvery-hospital/restore-check');STATE=pathlib.Path('/var/lib/kauvery-hospital/backup')
env=dict(os.environ,RESTIC_REPOSITORY='/var/backups/kauvery-hospital/restic',RESTIC_PASSWORD_FILE=str(STATE/'restic-password'),RESTIC_CACHE_DIR='/var/cache/kauvery-restic')
def run(*a,**kw):return subprocess.run(list(a),check=True,**kw)
if TARGET.exists():raise SystemExit('Existing restore evidence retained; choose a new restore target before rerunning')
started=time.time();run('restic','restore','latest','--tag','kauvery-hospital','--target',str(TARGET),'--sparse','--include','/var/lib/libvirt/images/kauvery-hospital','--include','/var/lib/kauvery-hospital/backup','--include',str(ROOT/'config'),'--include',str(ROOT/'.private/server/hospital-state.json'),'--include','/home/kauvery-demo/.openmausbot','--include','/home/kauvery-demo/.codex','--include','/home/kauvery-demo/.config/openmausbot',env=env)
import hashlib
profile=TARGET/'home/kauvery-demo/.openmausbot'
import shutil,sqlite3
shutil.copyfile(TARGET/'var/lib/kauvery-hospital/backup/messages.db',profile/'messages.db')
for suffix in ['-wal','-shm']:
 (profile/('messages.db'+suffix)).unlink(missing_ok=True)
connection=sqlite3.connect('file:'+str(profile/'messages.db')+'?mode=ro',uri=True)
assert connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok';connection.close()
profiles=json.loads((profile/'bots.json').read_text());assert len(profiles)==6
assert all(b.get('computer')=='vm' for b in profiles)
assert (profile/'config.json').is_file() and (profile/'messages.db').is_file()
assert (TARGET/'home/kauvery-demo/.codex/auth.json').is_file()
restored_preferences=list((profile/'vm-homes').glob('*/preferences/firefox/firefox/profiles.ini'))
assert len(restored_preferences)==6, len(restored_preferences)
profile_receipt={'native_profiles_restored':6,'restored_profile_models':{b['name']:b['modelSelection']['model'] for b in profiles},'browser_preferences_restored':len(restored_preferences),'native_message_database_restored':True,'codex_auth_file_restored':True,'config_sha256':hashlib.sha256((profile/'config.json').read_bytes()).hexdigest()}
domain=E.fromstring((TARGET/'var/lib/kauvery-hospital/backup/domain.xml').read_text());domain.find('name').text='kauvery-restore-check';domain.find('uuid').text=str(uuid.uuid4());domain.find('memory').text=str(8*1024*1024);domain.find('currentMemory').text=str(8*1024*1024);domain.find('vcpu').text='4'
dev=domain.find('devices')
for i in list(dev):
 if i.tag in ['interface','graphics','video']:dev.remove(i)
for disk in dev.findall('disk'):
 source=disk.find('source')
 if source is not None and 'file' in source.attrib:source.set('file',str(TARGET/source.attrib['file'].lstrip('/')))
for c in dev.findall('channel'):
 source=c.find('source')
 if source is not None: c.remove(source)
# No original network, MAC or IP can become an active writer on the live VM network.
xml=TARGET/'restore-domain.xml';xml.write_text(E.tostring(domain,encoding='unicode'))
run('chown','-R','libvirt-qemu:kvm',str(TARGET/'var/lib/libvirt/images'));run('chmod','755',str(TARGET),str(TARGET/'var'),str(TARGET/'var/lib'),str(TARGET/'var/lib/libvirt'),str(TARGET/'var/lib/libvirt/images'))
run('virsh','define',str(xml));run('virsh','start','kauvery-restore-check')
def agent(payload):return json.loads(run('virsh','qemu-agent-command','kauvery-restore-check',json.dumps(payload),capture_output=True,text=True).stdout)['return']
def execute(command):
 p=agent({'execute':'guest-exec','arguments':{'path':'/bin/sh','arg':['-c',command],'capture-output':True}})['pid']
 for _ in range(60):
  r=agent({'execute':'guest-exec-status','arguments':{'pid':p}})
  if r.get('exited'):
   if r.get('exitcode')!=0:raise RuntimeError('Isolated restore command failed: '+base64.b64decode(r.get('err-data','')).decode()[:200])
   return base64.b64decode(r.get('out-data','')).decode()
  time.sleep(1)
 raise RuntimeError('Restore probe timed out')
try:
 for _ in range(240):
  try:agent({'execute':'guest-ping'});break
  except Exception:time.sleep(1)
 else:raise RuntimeError('Restore guest agent unavailable')
 execute('ip address add 192.168.178.10/32 dev lo; cd /opt/kauvery-hospital; docker compose up -d >/dev/null 2>&1; systemctl restart nginx')
 for _ in range(300):
  try:
   data=execute("python3 -c 'import urllib.request,json;d=json.load(urllib.request.urlopen(\"http://127.0.0.1:8080/dcm4chee-arc/aets/DCM4CHEE/rs/studies\"));print(json.dumps({\"studies\":len(d),\"instances\":sum(int(x[\"00201208\"][\"Value\"][0]) for x in d)}))'")
   imaging=json.loads(data);break
  except Exception:time.sleep(1)
 else:raise RuntimeError('Restored archive did not become ready')
 reports=execute('docker exec kauvery-hospital-openmrsdb-1 sh -c '+__import__('shlex').quote('mysql -N -uroot -p"$MYSQL_ROOT_PASSWORD" openmrs -e "select count(*) from obs where concept_id=57370 and voided=0"')).strip()
 evidence={'restored_studies':imaging['studies'],'restored_instances':imaging['instances'],'restored_reports':int(reports),'external_network_interfaces':0,**profile_receipt,'duration_seconds':round(time.time()-started),'status':'passed'}
 assert imaging['studies']>=10 and imaging['instances']>=672 and int(reports)>=5
 (ROOT/'docs/evidence/local-hospital/restore.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
finally:run('virsh','shutdown','kauvery-restore-check')
