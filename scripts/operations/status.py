#!/usr/bin/env python3
"""One operator status surface for the actual VM, assistants and backups."""
import datetime,json,pathlib,shutil,subprocess,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
def command(*args):return subprocess.run(list(args),capture_output=True,text=True).stdout.strip()
status={'vm':command('sudo','-n','virsh','domstate','kauvery-hospital'),'disk_free_gib':round(shutil.disk_usage('/').free/1024**3,1),'backup_timer':command('systemctl','is-active','kauvery-backup.timer')}
p=subprocess.run(['sudo','-n','cat','/var/lib/kauvery-hospital/backup/status.json'],capture_output=True,text=True)
if p.returncode==0:
 b=json.loads(p.stdout);status['last_backup']=b['last_success'];status['external_copy']=b['external_copy'];age=datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(b['last_success']);status['backup_overdue']=age.total_seconds()>36*3600
else:status['backup_overdue']=True
try:
 status['hospital_http']=urllib.request.urlopen('https://radiology.demo/openmrs/ws/rest/v1/session',timeout=5).status
 studies=json.load(urllib.request.urlopen('https://radiology.demo/dicomweb/studies',timeout=5));status['studies']=len(studies);status['instances']=sum(int(x['00201208']['Value'][0])for x in studies)
except Exception:status['hospital_http']='unavailable'
try:status['assistants']=[{'name':b['name'],'busy':b['busy'],'computer':b['computer']}for b in json.load(urllib.request.urlopen('http://127.0.0.1:8799/api/bots',timeout=5))['bots']]
except Exception:status['assistants']='app unavailable'
status['workstation_timer']=command('systemctl','is-active','kauvery-workstations.timer')
status['workstation_recovery_result']=command('systemctl','show','kauvery-workstations.service','-p','Result','--value')
status['maintenance_needed']=status['backup_overdue'] or status['disk_free_gib']<30 or status['hospital_http']!=200 or status['workstation_timer']!='active' or status['workstation_recovery_result'] not in ['success',''] or status['vm']!='running' or status['backup_timer']!='active'
print(json.dumps(status,indent=2))
