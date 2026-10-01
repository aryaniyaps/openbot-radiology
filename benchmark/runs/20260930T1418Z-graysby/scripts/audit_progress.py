#!/usr/bin/env python3
"""Reconcile nonmedical smoke evidence. Never interpret this as diagnostic accuracy."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
rows=[]
trace=[]
for p in (ROOT/'private/provider').rglob('*.jsonl'):
    for line in p.open():
        try: d=json.loads(line)
        except ValueError: continue
        if d.get('type')=='turn_context':
            v=d['payload']
            trace.append({'source':str(p.relative_to(ROOT)), 'timestamp':d.get('timestamp'), 'model':v.get('model'), 'effort':v.get('effort'), 'cwd':v.get('cwd')})
for model,file in [('gpt-6-luna','smoke-observation.json'),('gpt-6.1-sol','smoke-gpt-6.1-sol-result.json'),('gpt-6-astra','smoke-gpt-6-astra-result.json')]:
    p=ROOT/'evidence'/file
    if not p.exists(): rows.append({'requested_model':model,'status':'missing'}); continue
    b=json.loads(p.read_text()); terminal=[m for m in b['messages'] if m.get('turnTerminal')]; digests=[m['digest'] for m in b['messages'] if m.get('digest')]
    assert len(terminal)==1 and len(digests)==1, 'Do not pool retry/duplicate turns'
    t=terminal[0]; d=digests[0]
    answer=json.loads(t['text']) if t.get('turnSucceeded') else None
    colors={x.get('color'):x.get('shape') for x in answer.get('shapes',[])} if answer else {}
    rows.append({'requested_model':model,'configured_model':b['modelSelection']['model'],'status':'succeeded' if t.get('turnSucceeded') else 'failed','bot_id':b['id'],'thread_id':b['threadId'],'turn_id':t['turnId'],'answer':answer,'shape_color_agreement':colors=={'red':'square','blue':'circle'},'duration_ms':d['durationMs'],'tool_calls':d['toolCalls'],'usage':d.get('usage'),'source':str(p.relative_to(ROOT)), 'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'evidence/smoke-model-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
(ROOT/'evidence/visual-smoke-summary.json').write_text(json.dumps({'experiment':'nonmedical visual transport smoke; NOT diagnostic benchmark','diagnostic_cases_completed':0,'runs':rows},indent=2)+'\n')
for x in rows: print(x['requested_model'],x['status'],x.get('duration_ms'),'ms',x.get('shape_color_agreement'),'shape/color agreement')
print('Provider turn contexts:',[(x['model'],x['effort']) for x in trace]);print('Diagnostic studies completed: 0')
