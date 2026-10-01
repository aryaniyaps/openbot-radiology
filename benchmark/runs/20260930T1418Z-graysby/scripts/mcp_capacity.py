"""Reclaim only owned completed-case specialist registrations; retain the platform cap."""
import pathlib,json,fcntl,time,re
R=pathlib.Path(__file__).resolve().parents[1]
MODELS=['gpt-6-luna','gpt-6.1-sol','gpt-6-astra']
def reclaim(api):
 with (R/'private/mcp-registration-capacity.lock').open('a') as guard:
  fcntl.flock(guard,fcntl.LOCK_EX)
  servers=api('mcp/servers')['servers']
  if len(servers)<18:return
  bots=api('bots')['bots']
  for server in servers:
   args=server.get('args',[])
   if server.get('command')!='/usr/bin/python3' or len(args)!=4 or args[0]!=str(R/'scripts/medgemma_read_mcp.py'):continue
   case,stage=args[1:3]
   if stage!='evaluation' or not re.fullmatch(r'(CXR|CT|MR)-EVALUATION-\d{3}',case) or server['name']!='med_'+case.lower().replace('-','_'):continue
   if any(b.get('busy') and (case in b.get('name','') or server['name'] in (b.get('mcpServers') or [])) for b in bots):continue
   lock=(R/'private'/('delegation-'+case+'.lock')).open('a')
   try:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:continue
    records=[]
    for model in MODELS:
     folder=R/'evidence'/stage/'B-delegated'/model/case
     if not (folder/'assignment.json').exists() or not (folder/'result.json').exists():break
     result=json.loads((folder/'result.json').read_text())
     if result.get('status') not in ['succeeded','failed','timeout','quarantined'] or not result.get('finished_unix'):break
     records.append({'path':str((folder/'result.json').relative_to(R)),'finished_unix':result['finished_unix'],'bot_id':result['bot_id']})
    if len(records)!=3 or any(b.get('busy') and b['id'] in [x['bot_id'] for x in records] for b in bots):continue
    api('mcp/servers/'+server['name'],'DELETE')
    with (R/'evidence/mcp-capacity-recovery.jsonl').open('a') as out:out.write(json.dumps({'time_unix':time.time(),'deleted_registration':server,'completed_case_results':records,'no_clinical_turn_repeated':True})+'\n')
   finally:lock.close()
