#!/usr/bin/env python3
"""Exercise owned IT transport failure/recovery and guest reboot, preserving native work."""
import base64,json,os,pathlib,subprocess,time,urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2];P=ROOT/'.private/hospital-it'
def main():
 assert os.geteuid()==0
 accounts=json.loads((ROOT/'.private/doctor-client-auth.json').read_text());s=json.loads((P/'gateway-secrets.json').read_text());token=s['it_native']['token']
 ssh=['ssh','-i',str(P/'operator-key'),'-o','UserKnownHostsFile='+str(P/'known_hosts'),'-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','-o','ConnectTimeout=3','operator@192.168.178.11']
 def guest(command):return subprocess.run(ssh+[command],capture_output=True,text=True,timeout=15)
 def native():return json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8799/api/bots',headers={'Authorization':'Bearer '+token}),timeout=10))['bots']
 def status(history=False):
  a=accounts['it'];h={'Authorization':'Basic '+base64.b64encode((a['username']+':'+a['password']).encode()).decode()}
  return json.load(urllib.request.urlopen(urllib.request.Request('https://it.radiology.demo/operations/api/'+('history' if history else 'status'),headers=h),timeout=5))
 before=native();assert all(not b.get('busy') and not b.get('waitingForTeammates') for b in before),'Preserve active case work'
 baseline={(b['id'],b['threadId']):b['modelSelection'] for b in before};history=status(True);old_boot=guest('cat /proc/sys/kernel/random/boot_id');assert old_boot.returncode==0
 assert guest('sudo -n systemctl stop radiology-tunnel').returncode==0
 degraded=None
 try:
  for _ in range(45):
   current=status()
   if not current['native_up']:
    assert current['hospital_up'] and current['pacs_up'];degraded=current;break
   time.sleep(1)
  assert degraded,'Monitor did not detect IT transport loss'
 finally:assert guest('sudo -n systemctl start radiology-tunnel').returncode==0
 for _ in range(45):
  try:
   if status()['healthy']:break
  except OSError:pass
  time.sleep(1)
 else:raise RuntimeError('Transport health did not recover')
 subprocess.run(['virsh','reboot','kauvery-it'],check=True,capture_output=True)
 changed=False
 for _ in range(120):
  try:
   current=guest('cat /proc/sys/kernel/random/boot_id')
   if current.returncode==0 and current.stdout.strip()!=old_boot.stdout.strip():changed=True;break
  except subprocess.TimeoutExpired:pass
  time.sleep(1)
 assert changed,'IT guest reboot was not observed'
 for _ in range(90):
  try:
   health=status()
   if health['healthy']:break
  except OSError:pass
  time.sleep(1)
 else:raise RuntimeError('IT gateway did not recover after reboot')
 after=native();assert {(b['id'],b['threadId']):b['modelSelection'] for b in after}==baseline
 new_history=status(True);old_times={x['at'] for x in history};assert any(x['at'] in old_times for x in new_history)
 services=guest('systemctl is-active nginx radiology-tunnel radiology-observability');assert services.returncode==0 and services.stdout.split()==['active']*3
 hospital=subprocess.check_output(['virsh','domstate','kauvery-hospital'],text=True).strip();assert hospital=='running'
 result={'status':'passed','transport_failure_detected':True,'hospital_and_pacs_remained_up_during_it_transport_failure':True,'transport_recovery_passed':True,'it_guest_new_boot_observed':True,'services_active_after_reboot':services.stdout.split(),'tls_origins_healthy_after_reboot':True,'telemetry_history_survived':True,'native_role_thread_and_model_state_preserved':True,'hospital_vm_remained_running':True,'study_count':health['studies'],'instance_count':health['instances'],'session_days_remaining':health['native_session_days_remaining'],'tls_days_remaining':health.get('tls_cert_days_remaining')}
 (ROOT/'docs/evidence/hospital-deployment/it-recovery.json').write_text(json.dumps(result,indent=2)+'\n');print('IT transport alert/recovery, guest reboot, telemetry persistence and native state preservation passed')
if __name__=='__main__':main()
