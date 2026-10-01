import pathlib,json,urllib.request,hashlib,re,time,fcntl
R=pathlib.Path(__file__).resolve().parents[1];D=R/'private/platform/attachments'
def reclaim():
 with (R/'private/attachment-capacity.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  total=sum(p.stat().st_size for p in D.iterdir() if p.is_file())
  if total<350*1024**2:return
  with urllib.request.urlopen('http://127.0.0.1:18899/api/bots',timeout=20) as f:bots=json.load(f)['bots']
  active=set()
  for b in bots:
   if b.get('busy') or any(t.get('busy') for t in b.get('tasks',[])):
    for m in b.get('messages',[]):active.update(re.findall(r'<attached-image path="([^"]+)"',m.get('text','')))
  completed=set()
  for result in (R/'evidence').glob('*/*/*/*/result.json'):
   try:
    value=json.loads(result.read_text());request=result.parent/'request.json'
    if value.get('arm')=='B' and value.get('finished_unix') and value.get('status') not in ['pending','controller_failure'] and request.exists():
     completed.update(re.findall(r'<attached-image path="([^\"]+)"',json.loads(request.read_text()).get('text','')))
   except (OSError,ValueError):continue
  # A retained terminal result positively proves this unique upload belongs to a completed own request.
  sources={}
  for p in (R/'agent-visible').glob('*/*/*.png'):sources[hashlib.sha256(p.read_bytes()).hexdigest()]=p
  freed=0
  for p in sorted(D.glob('*.png'),key=lambda p:p.stat().st_mtime):
   if str(p) not in completed or str(p) in active or time.time()-p.stat().st_mtime<120:continue
   h=hashlib.sha256(p.read_bytes()).hexdigest()
   if h not in sources:continue
   n=p.stat().st_size
   with (R/'evidence/attachment-reclamation.jsonl').open('a') as f:f.write(json.dumps({'time_unix':time.time(),'owned_attachment':str(p.relative_to(R)),'source_png':str(sources[h].relative_to(R)),'sha256':h,'bytes':n,'active_conversation':False,'terminal_own_request_proven':True,'minimum_age_seconds':120,'reason':'Exact own source retained and inactive upload reclaimed under native512MiB store cap'})+'\n')
   p.unlink();freed+=n
   if total-freed<200*1024**2:break
  print('Reclaimed exact inactive owned attachment copies',freed,flush=True)
if __name__=='__main__':reclaim()
