#!/usr/bin/env python3
"""After the initial routine batch, run held-out broader cases and fixed reviews."""
import concurrent.futures,json,subprocess,sys,time
from pathlib import Path
from run_batch import one,event,P,ROOT
R=Path(__file__).resolve().parents[1]

if __name__=='__main__':
    # The first batch imported its runner before the global slots were added.
    # Wait for its actual terminal event, so total native concurrency stays two.
    while True:
        log=P/'routine-batch.log'
        if log.exists() and any(json.loads(line).get('event')=='batch-complete' for line in log.read_text().splitlines() if line.startswith('{')):break
        time.sleep(5)
    event({'event':'continuation-start','reason':'routine batch terminal; no concurrent older runner'})
    subprocess.run([sys.executable,str(R/'scripts/run_batch.py'),'--protocol',str(R/'PROTOCOL-PNX-SUPPLEMENT.json')],check=True)
    subprocess.run([sys.executable,str(R/'scripts/run_batch.py'),'--protocol',str(R/'PROTOCOL-TEACHING.json'),'--development'],check=True)
    # A development failure does not justify tuning against held-out cases.
    # Keep the protocol fixed; all assigned outcomes remain visible.
    subprocess.run([sys.executable,str(R/'scripts/run_batch.py'),'--protocol',str(R/'PROTOCOL-TEACHING.json'),'--controls'],check=True)
    review=json.loads((R/'PROTOCOL-REVIEW.json').read_text());jobs=[(case,model,'cross-review','') for case in review['case_ids'] for model in review['models']]
    event({'event':'review-batch-start','assignments':len(jobs)})
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(one,jobs))
    event({'event':'all-evaluation-batches-complete','review_assignments':len(jobs)})
