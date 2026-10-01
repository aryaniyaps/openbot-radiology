#!/usr/bin/env python3
"""Two bounded native readers, no diagnostic retries or outcome selection."""
import argparse, concurrent.futures, hashlib, json, threading, time, traceback
from pathlib import Path
from run_case import run, P, ROOT
LOCK=threading.Lock()

def event(row):
    with LOCK:
        with (P/'batch-events.jsonl').open('a') as f:f.write(json.dumps(dict(time_unix=time.time(),**row))+'\n')
        print(json.dumps(row),flush=True)

def one(job):
    case,model,condition,suffix=job
    packet=json.loads((P/'agent-visible'/case/'input.json').read_text());out=P/'results'/packet['stage']/condition/model/(case+suffix)
    if (out/'result.json').exists():
        event({'event':'retained','case':case,'model':model,'condition':condition});return
    event({'event':'start','case':case,'model':model,'condition':condition,'suffix':suffix})
    try:
        result=run(case,model,condition,suffix)
    except Exception as e:
        out.mkdir(parents=True,exist_ok=True)
        result=json.loads((out/'assignment.json').read_text()) if (out/'assignment.json').exists() else {'case_id':case,'requested_model':model,'condition':condition,'stage':packet['stage'],'modality':packet['modality']}
        result.update(status='controller-failure',exception=type(e).__name__+': '+str(e)[:400],finished_unix=time.time(),structured_answer=None)
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    event({'event':'finish','case':case,'model':model,'condition':condition,'suffix':suffix,'status':result['status']})

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--protocol',required=True);ap.add_argument('--controls',action='store_true');ap.add_argument('--development',action='store_true');a=ap.parse_args();protocol=json.loads(Path(a.protocol).read_text());jobs=[]
    cases=protocol['cases']
    for row in cases:
        if (row.get('stage')=='development')!=a.development:continue
        models=list(protocol['models'])
        if int(hashlib.sha256(row['case_id'].encode()).hexdigest(),16)%2:models.reverse()
        for model in models:jobs.append((row['case_id'],model,'direct',''))
    if a.controls:
        for case in protocol.get('controls_case_ids',[]):
            for model in protocol['models']:jobs.append((case,model,'context-only',''))
        for case in protocol.get('repeat_case_ids',[]):
            for model in protocol['models']:jobs.append((case,model,'direct','-repeat'))
    event({'event':'batch-start','assignments':len(jobs),'protocol_sha256':hashlib.sha256(Path(a.protocol).read_bytes()).hexdigest(),'workers':2})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(one,jobs))
    event({'event':'batch-complete','assignments':len(jobs)})
