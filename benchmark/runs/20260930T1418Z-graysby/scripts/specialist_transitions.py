"""Reference-supported three-way observations, without causal or severity claims."""
import pathlib,json,collections,time
R=pathlib.Path(__file__).resolve().parents[1]
tasks=json.loads((R/'report/task-results.json').read_text())
baseline={(x['case_id'],x['model'],x['task']):x for x in tasks if x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and not x['attempt']}
records=[]
for final in tasks:
    if final['stage']!='evaluation' or final['configuration'] not in ['delegated','second-reader']:continue
    b=baseline[(final['case_id'],final['model'],final['task'])]
    s=baseline[(final['case_id'],'google/medgemma-1.5-4b-it',final['task'])]
    assert b['label']==s['label']==final['label']
    x={k:final[k] for k in ['case_id','modality','model','configuration','task','label']}
    x['states']={name:{'status':v['status'],'scorable':v['scorable'],'correct':v['correct'],'prediction':v['prediction']} for name,v in [('baseline',b),('specialist',s),('final',final)]}
    pending=any(v['status']=='not_run' for v in [b,s,final]);x['pending']=pending
    c=[]
    if not pending:
        if s['correct'] and final['scorable'] and not final['correct']:c.append('correct_specialist_finding_not_retained_in_final_completed_label')
        if s['correct'] and not final['scorable']:c.append('correct_specialist_finding_followed_by_unresolved_final_label')
        if b['correct'] and s['correct'] and final['scorable'] and not final['correct']:c.append('both_initial_readers_correct_final_completed_label_wrong')
        if b['scorable'] and s['scorable'] and final['scorable'] and not b['correct'] and not s['correct'] and not final['correct']:c.append('shared_wrong_label_persisted')
        if b['scorable'] and not b['correct'] and s['correct'] and final['correct']:c.append('wrong_baseline_correct_specialist_correct_final')
        if b['correct'] and s['scorable'] and not s['correct'] and final['scorable'] and not final['correct']:c.append('correct_baseline_wrong_specialist_wrong_final')
        if b['scorable'] and s['scorable'] and not b['correct'] and not s['correct'] and final['correct']:c.append('both_initial_readers_wrong_final_correct')
    x['descriptive_transitions']=c;records.append(x)
groups=[]
for key in sorted({(x['modality'],x['model'],x['configuration'],x['task']) for x in records}):
    z=[x for x in records if (x['modality'],x['model'],x['configuration'],x['task'])==key]
    groups.append(dict(zip(['modality','model','configuration','task'],key),explicit_reference_studies=len(z),pending_studies=sum(x['pending'] for x in z),transition_counts=dict(collections.Counter(c for x in z for c in x['descriptive_transitions']))))
(R/'report/specialist-transitions.json').write_text(json.dumps({'updated_unix':time.time(),'interpretation':'Each row is an explicit report-supported finding on one study. Categories overlap and are not summed as independent patients. Correct means concordance with the report assertion, not independent clinical adjudication. Three-way patterns cannot prove that the specialist caused a correction or error, or that the primary deliberately ignored evidence. Unresolved labels remain distinct from wrong diagnostic labels.','groups':groups,'records':records},indent=2)+'\n')
