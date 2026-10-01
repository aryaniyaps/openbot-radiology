"""Auxiliary exact-screen transport audit; one original study, no new primary N."""
import pathlib,json,hashlib,base64,collections
R=pathlib.Path(__file__).resolve().parents[1]
registration=R/'evidence/matched-screenshot-registration.json'
if not registration.exists():raise SystemExit(0)
reg=json.loads(registration.read_text());case=reg['underlying_case_id'];model=reg['model']
paths={'A viewer':R/'evidence/evaluation/A'/model/case/'result.json',
       'B original images':R/'evidence/evaluation/B'/model/case/'result.json',
       'B exact screenshots':R/'evidence/evaluation/B'/model/reg['auxiliary_case_id']/'result.json'}
if not all(p.exists() for p in paths.values()):raise SystemExit(0)
results={name:json.loads(p.read_text()) for name,p in paths.items()}
matched=results['B exact screenshots'];assert reg['registered_before_matched_dispatch_unix']<=matched['started_unix']
expected=collections.Counter(x['sha256'] for x in reg['screenshots'])
assert collections.Counter(x['sha256'] for x in matched['input_manifest'])==expected
native_hashes=[]
for line in (R/matched['native_identity']['native_trace']).read_text().splitlines():
    d=json.loads(line);p=d.get('payload',{})
    if d.get('type')!='response_item' or p.get('type')!='message' or p.get('role')!='user':continue
    for part in p.get('content',[]):
        url=part.get('image_url','')
        if part.get('type')=='input_image' and url.startswith('data:image/'):
            native_hashes.append(hashlib.sha256(base64.b64decode(url.split(',',1)[1])).hexdigest())
assert collections.Counter(native_hashes)==expected,'Actual native image bytes differ from saved A screenshots'
tasks=json.loads((R/'report/task-results.json').read_text());reference={x['task']:x['label'] for x in tasks if x['stage']=='evaluation' and x['case_id']==case and x['model']==model and x['arm']=='B' and x['configuration']=='primary' and not x['attempt']}
comparisons=[]
for task,label in reference.items():
    conditions={}
    for name,r in results.items():
        valid=r.get('status')=='succeeded' and r.get('structured_answer') and r.get('native_identity',{}).get('status')=='verified' and not r.get('native_identity',{}).get('prior_conversation_context_detected')
        answer=r.get('structured_answer') if valid else None
        state=answer['findings_status'][task] if answer else None
        scorable=bool(answer and not answer['abstention'] and state in ['present','absent'])
        conditions[name]={'state':state,'correct_explicit_report_assertion':bool(int(state=='present')==label) if scorable else None,'status':r['status'],'duration_ms':r.get('duration_ms'),'result_path':str(paths[name].relative_to(R))}
    comparisons.append({'task':task,'explicit_reference':'present' if label else 'absent','conditions':conditions})
data={'underlying_case_id':case,'auxiliary_case_id':reg['auxiliary_case_id'],'model':model,'actual_native_image_bytes_equal_A_screenshots':True,'native_image_sha256':native_hashes,'independent_patient_count':1,'primary_sample_increment':0,'native_identity_status':matched['native_identity']['status'],'unexpected_prior_context':matched['native_identity'].get('prior_conversation_context_detected'),
      'interpretation':'Single technical sensitivity comparison; different instructions/tool affordances and budgets remain. No general superiority or equivalence inference.', 'comparisons':comparisons}
(R/'report/matched-screenshot-comparison.json').write_text(json.dumps(data,indent=2)+'\n')
