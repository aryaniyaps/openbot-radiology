#!/usr/bin/env python3
"""Observe the owned rehearsal and exercise one-shot GUI review as the doctor."""
import base64,json,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 assignment=json.loads((ROOT/'.private/doctor-workflow-assignment.json').read_text())
 account=json.loads((ROOT/'.private/doctor-client-auth.json').read_text())['doctor']
 headers={'Authorization':'Basic '+base64.b64encode((account['username']+':'+account['password']).encode()).decode(),'Content-Type':'application/json','Origin':'https://doctor.radiology.demo'}
 def api(path,body=None):
  q=urllib.request.Request('https://doctor.radiology.demo/api/'+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
  with urllib.request.urlopen(q,timeout=30) as response:return json.load(response)
 bid=assignment['coordinator_id'];tid=assignment['thread_id'];progress=ROOT/'.private/doctor-workflow-progress.json';approved=json.loads(progress.read_text()).get('one_shot_reviews',[]) if progress.exists() else [];deadline=time.time()+1800
 allowed={'select_computer','press_key','hotkey','type_text','click','set_value','scroll','drag','coordinate_bots','browser_evaluate'}
 while time.time()<deadline:
  bots=api('bots')['bots'];bot=next(b for b in bots if b['id']==bid)
  assert bot['threadId']==tid,'Human changed the current thread; preserve their activity'
  for target in bots:
   if target['id']!=bid:
    if not target.get('busy') or target.get('computer')!='vm':continue
    active=next((t for t in target['tasks'] if t['threadId']==target['threadId']),{})
    if (active.get('openedBy') or {}).get('botId')!=bid:continue
    content=json.dumps(target['messages'])
    if assignment['case']['patient_id'] not in content or assignment['case']['accession'] not in content:continue
   for m in target['messages']:
    card=m.get('card') or {}
    if not card.get('requestId') or card.get('answered') or card.get('dismissed') or m.get('at',0)<(assignment['started_unix']-60)*1000:continue
    if card.get('tool') not in allowed:
     print('Unreviewed tool requires inspection:',card.get('tool'),flush=True);continue
    answer=api('bots/'+target['id']+'/respond',{'threadId':target['threadId'],'requestId':card['requestId'],'behavior':'allow','always':False})
    approved.append({'role':target['name'],'tool':card['tool'],'request_id':card['requestId'],'outcome':answer.get('outcome'),'persistent_permission':False})
    print('One-shot configured-workstation / teammate review:',target['name'],card['tool'],answer.get('outcome'),flush=True)
  state={'observed_unix':time.time(),'busy':bot.get('busy'),'waiting_for_teammates':bot.get('waitingForTeammates'),'one_shot_reviews':approved,'thread_id':tid}
  (ROOT/'.private/doctor-workflow-progress.json').write_text(json.dumps(state,indent=2)+'\n')
  terminal=[m for m in bot['messages'] if m.get('turnTerminal') and m.get('turnSucceeded')]
  if not bot.get('busy') and not bot.get('waitingForTeammates') and terminal:
   state.update(status='terminal',model_generated_reply=terminal[-1].get('text'),case=assignment['case']);(ROOT/'.private/doctor-workflow-terminal.json').write_text(json.dumps(state,indent=2)+'\n');print('Owned doctor rehearsal terminal',flush=True);return
  time.sleep(2)
 print('Observation window ended; inspect actual native activity before continuing',flush=True)

if __name__=='__main__':main()
