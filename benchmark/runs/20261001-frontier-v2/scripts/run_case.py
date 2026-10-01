#!/usr/bin/env python3
"""Fresh native OpenMausBot conversation, exact requested model, supplied images only."""
import argparse, base64, fcntl, hashlib, io, json, re, time, urllib.request, uuid
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
P = ROOT / '.private/frontier-v2'

def api(path, method='GET', body=None, mime='application/json'):
    data = body if isinstance(body, bytes) else json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request('http://127.0.0.1:18899/api/'+path, data=data, method=method, headers={'Content-Type':mime})
    with urllib.request.urlopen(req, timeout=30) as f:
        return json.load(f)

def audit(record, out):
    matches=[]
    for path in (P/'provider/sessions').rglob('*.jsonl'):
        if path.stat().st_mtime < record['started_unix']-5: continue
        with path.open() as f:
            first=json.loads(f.readline())
        cwd=first.get('payload',{}).get('cwd','')
        if cwd == record['provider_cwd'] or (record['bot_id'] in cwd and record['thread_id'] in cwd):
            matches.append(path)
    if len(matches)!=1:
        return {'status':'unresolved','candidate_count':len(matches)}
    path=matches[0]; rows=[json.loads(s) for s in path.read_text().splitlines()]
    contexts=[x['payload'] for x in rows if x.get('type')=='turn_context']
    messages=[x.get('payload',{}) for x in rows if x.get('type')=='response_item' and x.get('payload',{}).get('type')=='message']
    message_text=json.dumps(messages)
    markers=['Your recent work','Recalled for this message','Recalled from your other conversations','Relevant memories from','<recalled_context>']
    delivered=[]
    for m in messages:
        if m.get('role')!='user': continue
        for part in m.get('content',[]):
            url=part.get('image_url','')
            if part.get('type')=='input_image' and url.startswith('data:image/'):
                b=base64.b64decode(url.split(',',1)[1]); im=Image.open(io.BytesIO(b))
                delivered.append({'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'pixels':list(im.size)})
    calls=[x for x in rows if x.get('type')=='response_item' and x.get('payload',{}).get('type') in ['function_call','custom_tool_call']]
    # Official Ask mode uses workspace-write. File/web/tool capabilities are
    # disabled by the isolated provider wrapper; protected gold is root-only.
    # Record the native sandbox honestly instead of claiming a stricter mode.
    valid=bool(contexts) and all(x.get('model')==record['requested_model'] and x.get('effort')=='high' and x.get('sandbox_policy',{}).get('type')=='workspace-write' and not x.get('sandbox_policy',{}).get('network_access',False) for x in contexts)
    prior=any(s in message_text for s in markers)
    complete_images=len(delivered)==len(record['input_manifest'])
    result={'status':'verified' if valid and not prior and not calls and complete_images else 'quarantined',
            'reported_models':sorted(set(x.get('model','') for x in contexts)),
            'efforts':sorted(set(x.get('effort','') for x in contexts)),
            'sandbox_policies':[x.get('sandbox_policy') for x in contexts],
            'prior_conversation_context_detected':prior,'tool_call_count':len(calls),
            'complete_image_delivery':complete_images,
            'delivered_images':delivered,'native_trace_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'native_trace':str(path.relative_to(ROOT)),
            'identity_limit':'Provider identifier only; backend weights/revision not independently exposed'}
    (out/'native-trace-index.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

def run(case_id, model, condition='direct', suffix='', wall_seconds=300):
    while True:
        for i in range(2):
            lock=(P/f'runtime-slot-{i}.lock').open('a')
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:lock.close();continue
            try:return _run(case_id,model,condition,suffix,wall_seconds)
            finally:lock.close()
        time.sleep(.25)

def _run(case_id, model, condition='direct', suffix='', wall_seconds=300):
    case=P/'agent-visible'/case_id
    packet=json.loads((case/'input.json').read_text())
    out=P/'results'/packet['stage']/condition/model/(case_id+suffix)
    out.mkdir(parents=True,exist_ok=False)
    work=P/'conversation-workspaces'/str(uuid.uuid4()); work.mkdir(parents=True)
    selection={'instanceId':'codex','model':model,'effort':'high'}
    guide=json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text())
    shared=guide['shared']
    # The wrapper disables file/skill discovery, so inject the exact native skill
    # text rather than inviting the reader to open its file or a gold reference.
    skill=(ROOT/'config/openmausbot/skills/radiology-study-read/SKILL.md').read_text()
    if condition=='cross-review':skill+='\n'+(ROOT/'config/openmausbot/skills/radiology-report-review/SKILL.md').read_text()
    soul='Independent blinded radiology research assistant. Use only the clinical context and images supplied in this thread. Never use tools, files, memory, public-case recall or other agents. No doctor report or correct answer is supplied. '+shared+'\n'+skill
    body={'name':'v2 '+case_id+' '+model+' '+condition,'useDefaults':False,
          'modelSelection':selection,'requireAvailableModel':True,'computer':'off',
          'browser':False,'composio':False,'peers':[],'mcpServers':[],
          'memoryUpkeep':False,'approvalMode':'ask','cwd':str(work),'soul':soul}
    record={'case_id':case_id,'modality':packet['modality'],'stage':packet['stage'],
            'condition':condition,'requested_model':model,'model_selection':selection,
            'provider_cwd':str(work),'started_unix':time.time(),'wall_limit_seconds_per_turn':wall_seconds,
            'input_manifest':[],'turns':[],'status':'pending',
            'soul_sha256':hashlib.sha256(soul.encode()).hexdigest()}
    (out/'assignment.json').write_text(json.dumps(record,indent=2)+'\n')
    baseline=None
    if condition=='cross-review':
        other='gpt-6-astra' if model=='gpt-6.1-sol' else 'gpt-6.1-sol'
        source=P/'results'/packet['stage']/'direct'/other/case_id/'result.json'
        baseline=json.loads(source.read_text())
        assert baseline['status']=='succeeded' and baseline['structured_answer']
        record['baseline_model']=other;record['baseline_result_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    bot=api('bots','POST',body);bot=bot.get('bot',bot);bid=bot['id'];tid=bot['threadId']
    # Native creation accepts only a subset of profile fields. Apply the
    # supported settings PATCH before admission, and verify the actual soul.
    patched=api('bots/'+bid,'PATCH',{k:v for k,v in body.items() if k not in ['useDefaults','requireAvailableModel','modelSelection']})
    assert patched.get('bot',patched).get('soul')==soul, 'Native profile did not retain supplied instructions'
    assert api('bots/'+bid+'/memory/upkeep')['enabled'] is False, 'Automatic case memory capture must be disabled'
    record.update(bot_id=bid,thread_id=tid)
    (out/'assignment.json').write_text(json.dumps(record,indent=2)+'\n')
    image_names=packet['image_files'] if condition!='context-only' else []
    assert condition=='context-only' or image_names, 'No image evidence: reject diagnostic admission'
    images=[]
    for name in image_names:
        path=case/name; b=path.read_bytes();assert len(b)<=10*1024**2
        v=api('attachments','POST',b,'image/png');v=v.get('attachment',v)
        images.append((name,v['path']))
        record['input_manifest'].append({'file':name,'attachment_name':Path(v['path']).name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'pixels':list(Image.open(path).size)})
    groups=[images[i:i+4] for i in range(0,len(images),4)] or [[]]
    if baseline is not None:
        assert [(x['file'],x['sha256']) for x in baseline['input_manifest']]==[(x['file'],x['sha256']) for x in record['input_manifest']], 'Reviewer images differ from primary'
        aliases=baseline.get('image_reference_aliases',{})
        baseline_text=json.dumps(baseline['structured_answer'])
        for original,logical in aliases.items():baseline_text=baseline_text.replace(original,logical)
        baseline['structured_answer']=json.loads(baseline_text)
        record['baseline_view_alias_normalization']=aliases
    classes=packet.get('target_findings',[])
    schema='Return ONLY one JSON object with primary_diagnosis (string), differential (array of at most 3 strings), key_findings (array of short strings with supplied image filenames), urgent_findings (array), image_references (array of supplied filenames), report_draft (object with findings and impression strings), confidence (number 0 to 1), abstention (boolean), limitations (array). Maximum 450 words. No JSON comments.'
    if classes:
        schema+=' Include findings_status with exactly these keys: '+', '.join(classes)+'. Values must be present, absent, uncertain, or unassessable. Absence requires adequate coverage; do not force certainty.'
    for i,group in enumerate(groups):
        final=i==len(groups)-1
        prompt=('Study '+case_id+'. Modality: '+packet['modality']+'. Clinical context from the pre-imaging history only: '+packet.get('clinical_context','None supplied')+'. Coverage: '+packet['coverage']+'. Limitations: '+json.dumps(packet['input_limitations'])+'. ') if i==0 else 'Continue the same study '+case_id+'. '
        if i==0 and packet.get('view_chronology'):prompt+=' Neutral source chronology: '+json.dumps(packet['view_chronology'])+'. Compare baseline and follow-up where supplied; do not merge different time points into one current examination. '
        if condition=='context-only': prompt+='No images are supplied in this control. Do not invent visual findings. State a provisional differential from context, explicitly mark lack of image evidence, and abstain from image-based diagnosis. '
        if final and baseline is not None:prompt+=' Independently check this other model\'s proposed read against the actual supplied images. It is not ground truth. Correct errors only when justified; preserve uncertainty. Return your final checked diagnosis and draft in the same required schema. Other model proposal: '+json.dumps(baseline['structured_answer'])
        prompt+=('This is the final image group. Consolidate your own observations from ALL '+str(len(images))+' supplied images in this thread. Interpret independently; suggest a primary imaging diagnosis or normal conclusion, differential, urgent findings and a provisional report for doctor review. '+schema) if final else ('Image group '+str(i+1)+' of '+str(len(groups))+'. Record concise provisional visible findings with view references and uncertainty. Do not give the final report yet; more images follow.')
        for name,path in group: prompt+='\n<attached-image path="'+path+'" name="'+name+'"/>'
        request={'threadId':tid,'sendId':str(uuid.uuid4()),'text':prompt}
        (out/f'request-{i+1:02}.json').write_text(json.dumps(request,indent=2)+'\n')
        turn={'number':i+1,'started_unix':time.time(),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'images':[x[0] for x in group]}
        with (P/'provider-start.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            stamp=P/'provider-start-time.json';last=json.loads(stamp.read_text()) if stamp.exists() else 0
            pause=max(0,10-(time.time()-last));time.sleep(pause)
            stamp.write_text(json.dumps(time.time()))
            turn['start_throttle_seconds']=pause
        api('bots/'+bid+'/messages','POST',request)
        deadline=time.monotonic()+wall_seconds
        while time.monotonic()<deadline:
            b=next(x for x in api('bots')['bots'] if x['id']==bid)
            digest=[m for m in b['messages'] if m.get('digest')]
            if not b.get('busy') and len(digest)>i: break
            time.sleep(1)
        else:
            api('bots/'+bid+'/interrupt','POST',{'threadId':tid})
            record['status']='timeout';record['turns'].append(turn);break
        d=digest[-1];turn.update(duration_ms=d['digest'].get('durationMs'),usage=d['digest'].get('usage'),tool_calls=d['digest'].get('toolCalls'),turn_id=d.get('turnId') or d['digest'].get('turnId'),succeeded=bool(d.get('turnSucceeded')))
        texts=[m.get('text','') for m in b['messages'] if m.get('role')=='bot' and m.get('kind')=='text' and m.get('turnId')==turn['turn_id']]
        answer=d['digest'].get('reply') or (texts[-1] if texts else '')
        terminal=[m for m in b['messages'] if m.get('turnTerminal') and m.get('turnId')==turn['turn_id']]
        if terminal and terminal[-1].get('text'):answer=terminal[-1]['text']
        turn['raw_answer']=answer;record['turns'].append(turn)
        (out/f'observation-{i+1:02}.json').write_text(json.dumps(b,indent=2)+'\n')
        if not turn['succeeded'] or turn.get('tool_calls')!=0:
            record['status']='failed';break
        record['status']='succeeded' if final else 'pending'
    record['raw_answer']=record['turns'][-1].get('raw_answer','') if record['turns'] else ''
    try:
        clean=re.sub(r'^```(?:json)?\s*|\s*```$','',record['raw_answer'].replace('<end_of_turn>','').strip())
        v=json.loads(clean)
        assert isinstance(v.get('primary_diagnosis'),str) and isinstance(v.get('abstention'),bool)
        assert isinstance(v.get('report_draft'),dict) and isinstance(v.get('limitations'),list)
        assert 0<=v['confidence']<=1
        aliases={x['attachment_name']:x['file'] for x in record['input_manifest']}
        assert set(v['image_references']).issubset(set(image_names)|set(aliases))
        record['image_reference_aliases']=aliases
        if classes: assert set(v['findings_status'])==set(classes) and all(x in ['present','absent','uncertain','unassessable'] for x in v['findings_status'].values())
        record['structured_answer']=v
    except Exception as e:
        record['structured_answer']=None;record['parse_error']=type(e).__name__
    record['finished_unix']=time.time()
    record['native_identity']=audit(record,out)
    if record['native_identity']['status']!='verified':record['status']='quarantined'
    if record['status']=='succeeded' and record['structured_answer'] is None:record['status']='invalid-output'
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    # Preserve observation/trace evidence first; then archive only this run's
    # terminal idle bot, preventing the native 100-bot workspace limit.
    if record['status']!='timeout':
        api('bots/'+bid,'DELETE')
        for item in record['input_manifest']:
            attachment=P/'platform/attachments'/item['attachment_name']
            if attachment.is_file():attachment.unlink()
    print(json.dumps({'case':case_id,'model':model,'condition':condition,'status':record['status'],'seconds':round(record['finished_unix']-record['started_unix'],1),'images':len(images),'result':str(out/'result.json')}),flush=True)
    return record

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--model',choices=['gpt-6.1-sol','gpt-6-astra'],required=True);ap.add_argument('--condition',choices=['direct','context-only','cross-review'],default='direct');ap.add_argument('--suffix',default='');ap.add_argument('--wall-seconds',type=int,default=300);a=ap.parse_args()
    run(a.case,a.model,a.condition,a.suffix,a.wall_seconds)
