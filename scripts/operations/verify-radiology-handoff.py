#!/usr/bin/env python3
"""Public-image rehearsal through configured native roles; no patient record writes."""
import argparse,fcntl,hashlib,json,time,urllib.request,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'.private/frontier-v2'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,required=True);ap.add_argument('--case-id',default='PUBLIC-WORKFLOW-CXR-02');args=ap.parse_args();token=json.loads(args.session.read_text())['token']
 def api(route,method='GET',body=None,mime='application/json'):
  data=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
  req=urllib.request.Request('http://127.0.0.1:8799/api/'+route,method=method,data=data,headers={'Authorization':'Bearer '+token,'Content-Type':mime})
  with urllib.request.urlopen(req,timeout=30) as f:return json.load(f)
 # Reserve one of the two evaluation account slots. Sequential native handoffs
 # use at most one role inference at a time while the coordinator is parked.
 slot=(P/'runtime-slot-0.lock').open('a')
 fcntl.flock(slot,fcntl.LOCK_EX)
 try:
  bots=api('bots')['bots'];guidance=json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text());roles={k:next(b for b in bots if b['name']==s['name']) for k,s in guidance['roles'].items()}
  assert all(not b.get('busy') and not b.get('waitingForTeammates') for b in roles.values()),'Live role busy; preserve user activity'
  before={k:len(b.get('messages',[])) for k,b in roles.items()};bid=roles['coordinator']['id']
  created=api('bots/'+bid+'/tasks','POST',{'title':args.case_id+': supervised radiology rehearsal','approvalMode':'ask'});tid=created['task']['threadId']
  source=P/'agent-visible/ROUTINE-CXR-001';packet=json.loads((source/'input.json').read_text());attachments=[]
  for name in packet['image_files']:
   image=(source/name).read_bytes();a=api('attachments','POST',image,'image/png');a=a.get('attachment',a);attachments.append({'path':a['path'],'name':name,'sha256':hashlib.sha256(image).hexdigest()})
  prompt='Public teaching workflow rehearsal, case PUBLIC-WORKFLOW-CXR-01, not a hospital patient or signed report. The attached public chest radiographs are the ONLY image evidence. No history, accession, prior report or correct answer is supplied. Do not open hospital applications, browser, shell, network or other case files; do not save, sign, release or write clinical records. Complete a useful provisional case preparation, independent image read, report draft and independent check, stating coverage and uncertainty for radiologist review. Use actual native teammates one at a time, with sequential handoffs; do not role-play their answers and do not dispatch parallel work. Brief Case Prep first with the supplied identifier/context. Then brief Image Assistant with the exact attached image paths (these are assigned attachments and may be inspected directly), then Report Draft with the image observations, then Report Check with the draft AND these same image paths, then Workflow Steward to verify completion/limitations and read-only status. Send self-contained case-specific briefs; do not reuse prior case facts. End your turn after each delegation so the native return can resume you. If permissions or tools prevent a step, state the exact gap and return the completed parts. Final answer should contain findings, impression, urgent concerns, missing evidence, actual roles used and doctor actions. '
  prompt=prompt.replace('PUBLIC-WORKFLOW-CXR-01',args.case_id)
  prompt+='Assigned image paths: '+json.dumps(attachments)+'. To deliver pixels to Image Assistant and Report Check, copy the following actual native attachment markup into their self-contained brief. A plain file path alone is not native image delivery. Use the complete enabled procedures supplied in each role\'s standing prompt; no skill file read is needed. '
  for a in attachments:prompt+='\n<attached-image path="'+a['path']+'" name="'+a['name']+'"/>'
  api('bots/'+bid+'/messages','POST',{'threadId':tid,'sendId':str(uuid.uuid4()),'text':prompt});started=time.time();receipt={'case_id':args.case_id,'started_unix':started,'coordinator_id':bid,'thread_id':tid,'source_packet':'ROUTINE-CXR-001','image_sha256':[a['sha256'] for a in attachments],'before_message_counts':before};approved=set();approval_events=[]
  (P/'workflow-assignment.json').write_text(json.dumps(receipt,indent=2)+'\n')
  while time.time()-started<900:
   current=api('bots')['bots'];b=next(x for x in current if x['id']==bid)
   for m in b.get('messages',[]):
    card=m.get('card') or {};rid=card.get('requestId')
    if not rid or rid in approved or m.get('at',0)<started*1000 or card.get('tool')!='coordinate_bots':continue
    answer=api('bots/'+bid+'/respond','POST',{'threadId':tid,'requestId':rid,'behavior':'allow','always':False});approved.add(rid);approval_events.append({'request_id':rid,'tool':'coordinate_bots','outcome':answer.get('outcome'),'persistent_grant':False})
   if not b.get('busy') and not b.get('waitingForTeammates') and any(m.get('digest') for m in b.get('messages',[])):break
   time.sleep(2)
  receipt['finished_unix']=time.time();receipt['status']='terminal' if not b.get('busy') and not b.get('waitingForTeammates') else 'timeout'
  receipt['one_shot_internal_coordination_approvals']=approval_events
  snapshots={k:next(x for x in current if x['id']==old['id']) for k,old in roles.items()}
  raw=P/'workflow-native.json';raw.write_text(json.dumps(snapshots,indent=2)+'\n');raw.chmod(0o600)
  receipt['roles']=[{'role':k,'bot_id':b['id'],'model_selection':b.get('modelSelection'),'active_thread_id':b.get('threadId'),'message_count':len(b.get('messages',[])),'digests':[m['digest'] for m in b.get('messages',[]) if m.get('digest')]} for k,b in snapshots.items()]
  # Digest replies can contain app paths; publish only summarized evidence after
  # a separate curator inspection, never blindly copy complete native state.
  (P/'workflow-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
  print(json.dumps({'status':receipt['status'],'seconds':receipt['finished_unix']-started,'case_id':receipt['case_id']}))
 finally:slot.close()
if __name__=='__main__':main()
