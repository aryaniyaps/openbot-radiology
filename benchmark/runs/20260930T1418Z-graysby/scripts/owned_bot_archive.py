import pathlib,json,urllib.request,time,fcntl
R=pathlib.Path(__file__).resolve().parents[1]
def api(path,method='GET'):
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18899/api/'+path,method=method),timeout=20) as f:return json.load(f)
def recover_capacity(force=False):
 with (R/'private/bot-archive.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);bots=api('bots')['bots']
  if len(bots)<80 and not force:return
  proven={}
  for p in (R/'evidence').glob('*/*/*/*/result.json'):
   try:r=json.loads(p.read_text())
   except Exception:continue
   if r.get('bot_id') and r.get('arm')=='B' and r.get('finished_unix') and r.get('status')!='pending':proven[r['bot_id']]=(p,r)
  for receipt in (R/'private/bot-create-receipts').glob('*.json'):
   r=json.loads(receipt.read_text());b=next((b for b in bots if b['id']==r['bot_id']),None)
   if b and not any(m.get('role')=='user' for m in b.get('messages',[])) and time.time()-r['created_unix']>120:proven[r['bot_id']]=(receipt,{'thread_id':r['thread_id']})
  archived=0
  for b in bots:
   if b['id'] not in proven or b.get('busy') or b['id']=='94515d5f-026d-495b-80cd-883b05f59052':continue
   p,r=proven[b['id']];assert b['threadId']==r['thread_id'];d=R/'private/archived-bots';d.mkdir(exist_ok=True);f=d/(b['id']+'.json');f.write_text(json.dumps(b,indent=2));f.chmod(0o600);receipt=api('bots/'+b['id'],'DELETE')
   with (R/'evidence/owned-bot-archive.jsonl').open('a') as out:out.write(json.dumps({'time_unix':time.time(),'bot_id':b['id'],'thread_id':b['threadId'],'archived_full_state':str(f.relative_to(R)),'case_result':str(p.relative_to(R)),'receipt':receipt})+'\n')
   archived+=1
   if archived>=30:break
  print('Archived completed owned bots',archived,flush=True)
if __name__=='__main__':recover_capacity(True)
