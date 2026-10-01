import pathlib,json,os,time,subprocess,hashlib,shutil
R=pathlib.Path(__file__).resolve().parents[1];sessions=[]
for p in (R/'evidence').glob('*/*/*/*/assignment.json'):
 d=json.loads(p.read_text());sessions.append({k:d.get(k) for k in ['bot_id','thread_id','case_id','requested_model','arm','stage']})
(R/'evidence/owned-diagnostic-sessions.json').write_text(json.dumps(sessions,indent=2))
protected_pid=3135347
try:os.kill(protected_pid,0);alive=True
except ProcessLookupError:alive=False
except PermissionError:alive=pathlib.Path("/proc",str(protected_pid)).exists()
s={'time_unix':time.time(),'free_disk_bytes':shutil.disk_usage(R).free,'protected_server_pid':protected_pid,'protected_server_pid_alive':alive,'installed_bundle_sha256':hashlib.sha256(pathlib.Path('/opt/OpenMausBot/resources/server/index.js').read_bytes()).hexdigest(),'owned_sessions_registered':len(sessions),'shared_resource_caveat':'Physical host GPU/CPU and account quota shared; no foreign task content read'}
current=[]
controller=json.loads((R/'evidence/control-processes.json').read_text()) if (R/'evidence/control-processes.json').exists() else {'batch_pid':1081476,'watch_pid':883936}
for pid,role,expected in [(1103456,'isolated benchmark server',str(R/'private/benchmark-server.mjs')),(controller['batch_pid'],'resumed frozen batch controller',str(R/'scripts/run_batch.py')),(controller['watch_pid'],'report watcher',str(R/'scripts/report_watch.py'))]:
 try:
  cmd=pathlib.Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()
  current.append({'pid':pid,'role':role,'alive':True,'ownership_command_matches':expected in cmd})
 except FileNotFoundError:current.append({'pid':pid,'role':role,'alive':False,'ownership_command_matches':False})
s['known_owned_process_checks']=current
s['foreign_gpu_process_92991_alive']=pathlib.Path('/proc/92991').exists()
(R/'evidence/ownership-current.json').write_text(json.dumps({'updated_unix':time.time(),'startup_manifest':'ownership.json','process_restarts':'evidence/own-server-restarts.jsonl','current_processes':current,'owned_diagnostic_sessions':'evidence/owned-diagnostic-sessions.json','medgemma_phase_stop':'evidence/medgemma-phase-complete.json','interpretation':'Startup PIDs are historical; current processes require positive command match, never kill based on stale PID. Containers/displays retain separately verified dedicated ownership.'},indent=2)+'\n')
for name,cmd in [('gpu',['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu,temperature.gpu','--format=csv,noheader,nounits']),('gpu_processes',['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader,nounits']),('own_medgemma',(['sudo','-n','-u','aryan','env','XDG_RUNTIME_DIR=/run/user/1000','DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus'] if os.geteuid()==0 else [])+['systemctl','--user','show','graysby-medgemma.service','-p','MainPID','-p','MemoryCurrent','-p','CPUUsageNSec'])]:
 try:s[name]=subprocess.check_output(cmd,timeout=10,text=True).strip()
 except Exception as e:s[name+'_error']=str(e)
with (R/'evidence/resource-telemetry.jsonl').open('a') as f:f.write(json.dumps(s)+'\n')
print(json.dumps(s))
