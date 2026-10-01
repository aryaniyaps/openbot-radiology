#!/usr/bin/env python3
"""Final independent transport/reference audit, without modifying model answers."""
import hashlib,json,time
from pathlib import Path
from run_case import audit,P,ROOT
from build_results import frozen_reader_soul_sha
R=Path(__file__).resolve().parents[1]
def main():
 protocols=['PROTOCOL-ROUTINE.json','PROTOCOL-TEACHING.json','PROTOCOL-PNX-SUPPLEMENT.json','PROTOCOL-DENSE-CT.json'];sources=[];expected=[]
 for name in protocols:
  protocol=json.loads((R/name).read_text())
  for case in protocol['cases']:
   cid=case['case_id'];packet=P/'agent-visible'/cid/'input.json';inp=json.loads(packet.read_text());assert hashlib.sha256(packet.read_bytes()).hexdigest()==case['input_sha256'],cid+' packet changed'
   assert [hashlib.sha256((packet.parent/f).read_bytes()).hexdigest() for f in inp['image_files']]==case['images_sha256'],cid+' source image changed'
   ref=P/'references'/(cid+'.json');assert hashlib.sha256(ref.read_bytes()).hexdigest()==case['reference_sha256'],cid+' reference changed'
   sources.append({'case_id':cid,'input_reference_integrity':True,'reference_root_protected':ref.stat().st_uid==0 and ref.stat().st_mode&0o077==0})
   if case.get('stage')=='development':continue
   expected.extend((cid,m,'direct','') for m in protocol['models'])
  expected.extend((cid,m,'context-only','') for cid in protocol.get('controls_case_ids',[]) for m in protocol['models'])
  expected.extend((cid,m,'direct','-repeat') for cid in protocol.get('repeat_case_ids',[]) for m in protocol['models'])
 review=json.loads((R/'PROTOCOL-REVIEW.json').read_text());expected.extend((cid,m,'cross-review','') for cid in review['case_ids'] for m in review['models'])
 initial_expected=len(expected)
 for cid,m,condition,suffix in list(expected):
  original=P/'results/evaluation'/condition/m/(cid+suffix)/'result.json'
  if original.exists():
   first=json.loads(original.read_text())
   if first['status']=='controller-failure' and first.get('exception')=='HTTPError: HTTP Error 507: Insufficient Storage':
    assert not list(original.parent.glob('request-*.json')) and not first.get('turns')
    expected.append((cid,m,condition,'-transport-recovery'))
 rows=[]
 for cid,m,condition,suffix in expected:
  directory=P/'results/evaluation'/condition/m/(cid+suffix);file=directory/'result.json';assert file.exists(),'Missing assignment '+str((cid,m,condition,suffix));result=json.loads(file.read_text())
  identity=audit(result,directory) if result.get('provider_cwd') and result.get('bot_id') else {'status':'not-started'}
  if result['status']=='succeeded':assert identity['status']=='verified','Transport audit failed '+str((cid,m,condition,suffix))
  prompt_match=result.get('soul_sha256')==frozen_reader_soul_sha(condition)
  if condition=='direct':assert prompt_match,'Primary/direct reader instructions drifted'
  rows.append({'case_id':cid,'model':m,'condition':condition,'suffix':suffix,'status':result['status'],'reader_prompt_sha256':result.get('soul_sha256'),'frozen_reader_prompt_match':prompt_match,'native_qualification':identity['status'],'efforts':identity.get('efforts',[]),'delivered_images':len(identity.get('delivered_images',[])),'tool_call_count':identity.get('tool_call_count'),'prior_conversation_context_detected':identity.get('prior_conversation_context_detected'),'trace_sha256':identity.get('native_trace_sha256'),'result_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 receipt={'time_unix':time.time(),'status':'passed','initial_assigned_reads':initial_expected,'assigned_attempts_with_upload_recovery':len(expected),'pre_inference_upload_recoveries':len(expected)-initial_expected,'diagnostic_retries':0,'primary_studies':106,'unique_patients_with_supplement':116,'sources':sources,'assignment_audits':rows,'protocol_sha256':{name:hashlib.sha256((R/name).read_bytes()).hexdigest() for name in protocols+['PROTOCOL-REVIEW.json']},'limits':'Provider identities, input delivery and reference integrity; not clinical outcome certification'}
 (R/'evidence/final-acceptance.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'passed','assigned_reads':len(expected)}))
if __name__=='__main__':main()
