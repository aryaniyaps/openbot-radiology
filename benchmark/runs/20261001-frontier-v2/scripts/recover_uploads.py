#!/usr/bin/env python3
"""Recover only explicitly preserved pre-inference upload failures, once."""
import concurrent.futures,json
from pathlib import Path
from run_batch import one,event,P
if __name__=='__main__':
 jobs=[]
 for file in sorted((P/'results/evaluation/direct').glob('*/*/result.json')):
  r=json.loads(file.read_text())
  if r['status']!='controller-failure':continue
  assert r.get('exception')=='HTTPError: HTTP Error 507: Insufficient Storage'
  assert not list(file.parent.glob('request-*.json')) and not r.get('turns'),'Clinical retry forbidden'
  if file.parent.name.endswith('-transport-recovery'):raise RuntimeError('Recovery itself failed; diagnose before another tactic')
  jobs.append((r['case_id'],r['requested_model'],'direct','-transport-recovery'))
 event({'event':'pre-inference-upload-recovery-start','assignments':len(jobs),'reason':'Native cached attachment accounting refreshed at isolated-server restart; original upload failures preserved; no diagnostic request previously issued'})
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(one,jobs))
 event({'event':'pre-inference-upload-recovery-complete','assignments':len(jobs)})
