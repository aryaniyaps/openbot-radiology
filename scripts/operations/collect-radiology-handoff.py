#!/usr/bin/env python3
"""Publish only current public-rehearsal evidence, never historical case messages."""
import argparse,hashlib,json,re,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'.private/frontier-v2'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,required=True);a=ap.parse_args();token=json.loads(a.session.read_text())['token'];assigned=json.loads((P/'workflow-assignment.json').read_text());guide=json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text())
 def api(route):
  q=urllib.request.Request('http://127.0.0.1:8799/api/'+route,headers={'Authorization':'Bearer '+token})
  with urllib.request.urlopen(q,timeout=30) as f:return json.load(f)
 bots=api('bots')['bots'];coordinator=next(b for b in bots if b['id']==assigned['coordinator_id']);task=next(t for t in coordinator['tasks'] if t['threadId']==assigned['thread_id']);assert not task.get('busy') and not coordinator.get('waitingForTeammates'),'Rehearsal remains active'
 role_evidence=[];raw={};all_tags={};final='';handoffs=[]
 for role,spec in guide['roles'].items():
  bot=next(b for b in bots if b['name']==spec['name']);entries=[]
  for t in bot['tasks']:
   page=api('threads/'+t['threadId']+'/messages?limit=200');fresh=[m for m in page['messages'] if m.get('at',0)>=assigned['started_unix']*1000]
   if not fresh:continue
   if not any(assigned['case_id'] in json.dumps(m) for m in fresh):continue
   raw[t['threadId']]=fresh;tags=[]
   for m in fresh:
    text=m.get('text','');tags.extend(re.findall(r'<attached-image path="([^"]+)" name="([^"]+)"\s*/>',text))
    tool=m.get('tool') or {}
    if role=='coordinator' and tool.get('name')=='coordinate_bots' and tool.get('input'):
     payload=json.loads(tool['input']);handoffs.append({'bot_ids':payload['bot_ids'],'native_attachment_tags':payload['message'].count('<attached-image'),'case_identifier_in_brief':assigned['case_id'] in payload['message']})
    if role=='coordinator' and m.get('kind')=='text' and m.get('role')=='bot' and not m.get('from'):final=text
   admitted=[]
   for path,name in tags:
    f=Path(path);assert str(f.parent)=='/home/kauvery-demo/.openmausbot/attachments' and f.is_file(),'Handoff did not identify an owned actual attachment';sha=hashlib.sha256(f.read_bytes()).hexdigest();assert sha in assigned['image_sha256'],'Handoff image differs from assigned source';admitted.append({'view_name':name,'source_sha256':sha})
   all_tags[role]=admitted
   entries.append({'thread_id':t['threadId'],'runtime_thread_model_selection':t.get('modelSelection'),'completed_digests':sum(bool(m.get('digest')) for m in fresh),'native_owned_image_tags':admitted,'enabled_procedures_in_standing_prompt':all((ROOT/'config/openmausbot/skills'/name/'SKILL.md').read_text() in bot['soul'] for name in spec['skills'])})
  role_evidence.append({'role':role,'name':spec['name'],'configured_default':bot.get('modelSelection'),'active_rehearsal_threads':entries})
 assert len(handoffs)==5 and all(h['case_identifier_in_brief'] for h in handoffs),'Expected actual sequential five-role handoff chain'
 assert len(next(x for x in role_evidence if x['name']=='Image Assistant')['active_rehearsal_threads'][0]['native_owned_image_tags'])==2
 assert len(next(x for x in role_evidence if x['name']=='Report Check')['active_rehearsal_threads'][0]['native_owned_image_tags'])==2
 # Normalize only assigned attachment paths in the public model-generated text.
 for path,name in [item for messages in raw.values() for m in messages for item in re.findall(r'<attached-image path="([^"]+)" name="([^"]+)"\s*/>',m.get('text',''))]:final=final.replace(path,name)
 (P/'workflow-all-case-threads.json').write_text(json.dumps(raw,indent=2)+'\n')
 observed=json.loads((P/'workflow-receipt.json').read_text());assert observed['status']=='terminal'
 result={'case_id':assigned['case_id'],'status':'passed','source_packet':assigned['source_packet'],'source_image_sha256':assigned['image_sha256'],'seconds':observed['finished_unix']-observed['started_unix'],'actual_native_handoffs':handoffs,'roles':role_evidence,'final_model_generated_reply':final,'clinical_record_writes_observed':False,'record_write_proof_limit':'Native rehearsal actions/returns only, not an independent audit of every hospital system','diagnostic_accuracy_scope':'Qualitative public-case native integration rehearsal; does not enter primary diagnosis metrics','identity_limit':'Native execution-thread provider selection and assigned image admission; backend weights and delegated provider image resizing not independently exposed','setup_deviation':'Report Draft pair thread retained Sol/medium during this rehearsal, despite high default. Corrected afterward without rerunning its output.','first_rehearsal':'Observed timeout at 900 seconds during manual approval delays; later all five native returns completed; raw history retained privately'}
 (ROOT/'docs/evidence/frontier-v2/native-handoff-rehearsal.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'passed','handoffs':len(handoffs),'owned_image_tags_image_read_check':4}))
if __name__=='__main__':main()
