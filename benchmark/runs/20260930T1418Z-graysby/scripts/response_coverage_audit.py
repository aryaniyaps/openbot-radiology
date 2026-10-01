"""Descriptive curator audit; does not change frozen diagnostic scoring."""
import pathlib,json,collections,time,re
R=pathlib.Path(__file__).resolve().parents[1]
rows=json.loads((R/'report/assignment-results.json').read_text())
records=[]
allowed={'get_desktop_state','get_window_state','click','drag','scroll','hotkey','press_key'}
def leaves(v):
    if isinstance(v,str):return [v]
    if isinstance(v,dict):return sum((leaves(x) for x in v.values()),[])
    if isinstance(v,list):return sum((leaves(x) for x in v),[])
    return []
for row in rows:
    if not row['result_path']:continue
    p=R/row['result_path']
    if not p.exists():continue
    v=json.loads(p.read_text());a=v.get('structured_answer');issues=[]
    record={k:row[k] for k in ['case_id','stage','model','arm','configuration','attempt','execution_status','result_path']}
    if a:
        # Word count is explicitly descriptive: scalar text/status values, excluding JSON keys.
        n=len(re.findall(r'\S+',' '.join(leaves(a))))
        record['response_scalar_word_count']=n
        if n>250:issues.append('scalar_text_over_250_words')
        for field,limit in [('key_findings',6),('image_references',8 if row['arm']=='A' else 4),('limitations',6)]:
            if len(a.get(field,[]))>limit:issues.append(field+'_over_prompt_limit')
        if row['arm']=='B':
            supplied={x['view'] for x in v.get('input_manifest',[])}
            invented=[x for x in a.get('image_references',[]) if x not in supplied]
            record['image_references_not_exact_supplied_filenames']=invented
            if invented:issues.append('nonmatching_image_reference')
    if row['arm']=='A':
        native=v.get('native_identity',{})
        record['native_screenshots_delivered']=len(native.get('screenshots_actually_delivered',[]))
        record['dicom_instances_available']=v.get('dicom_instances_available')
        record['graphical_call_budget']=v.get('step_limit')
        record['native_digest_tool_calls']=v.get('tool_calls')
        record['controller_step_limit_exceeded']=v.get('step_limit_exceeded',False)
        if v.get('tool_calls') is not None and v.get('step_limit') is not None and v['tool_calls']>v['step_limit']:issues.append('native_digest_tool_calls_over_configured_budget')
        ap=p.parent/'actions.json'
        actions=json.loads(ap.read_text()) if ap.exists() else []
        names=collections.Counter(x.get('tool',{}).get('name','unknown') for x in actions)
        record['graphical_requests_by_tool']=dict(names)
        record['graphical_requests_with_recorded_success']=sum(x.get('tool',{}).get('ok') is True for x in actions)
        record['graphical_requests_with_recorded_failure']=sum(x.get('tool',{}).get('ok') is False for x in actions)
        record['graphical_requests_without_recorded_completion']=sum('ok' not in x.get('tool',{}) for x in actions)
        record['unauthorized_recorded_tool_names']=sorted(set(names)-allowed)
        if record['unauthorized_recorded_tool_names']:issues.append('unauthorized_recorded_tool_name')
    record['descriptive_prompt_conformance_issues']=issues
    records.append(record)
groups=[]
for key in sorted({(x['stage'],x['arm'],x['configuration'],x['model']) for x in records}):
    z=[x for x in records if (x['stage'],x['arm'],x['configuration'],x['model'])==key]
    groups.append(dict(zip(['stage','arm','configuration','model'],key),recorded_cases=len(z),issue_counts=dict(collections.Counter(i for x in z for i in x['descriptive_prompt_conformance_issues'])),screenshots_delivered=sum(x.get('native_screenshots_delivered',0) for x in z)))
out={'updated_unix':time.time(),'scope':'970 frozen assignments only; auxiliary exact-screen case is reported separately','interpretation':'Descriptive prompt conformance, not an extra retrospective accuracy gate. Actual screenshots are delivered image counts, not proof of unique slices, anatomical coverage, or navigation success. Unrecorded action completion is unknown, not a failed action. Word counts use scalar values rather than JSON syntax.','groups':groups,'records':records}
(R/'report/response-coverage-audit.json').write_text(json.dumps(out,indent=2)+'\n')
feasibility=[]
for modality in ['CXR','CT','MR']:
    for model in ['gpt-6-luna','gpt-6.1-sol','gpt-6-astra']:
        candidates=sorted((x for x in rows if x['modality']==modality and x['model']==model and x['arm']=='A'),key=lambda x:x['case_id'])
        if not candidates:continue
        x=candidates[0];p=R/x['result_path'];v=json.loads(p.read_text()) if p.exists() else None
        n=len(v.get('native_identity',{}).get('screenshots_actually_delivered',[])) if v else None
        reason='pending source read' if not v else 'source context contaminated' if x['prior_conversation_context_detected'] else 'source read lacks qualified response' if not x['valid_structured'] else 'more than four model-delivered screenshots' if n>4 else 'no model-delivered screenshot' if not n else 'technically eligible'
        auxiliary=R/'evidence/evaluation/B'/model/'CXR-MATCHED-001'/'assignment.json'
        executed=modality=='CXR' and auxiliary.exists()
        feasibility.append({'modality':modality,'model':model,'first_frozen_case':x['case_id'],'actual_delivered_screenshots':n,'source_status':x['execution_status'],'feasibility':reason,'auxiliary_dispatched':executed,'unexecuted_reason':None if executed else 'no remaining extra assignment allowance: 31 development + 970 frozen + 1 auxiliary = 1002 (prospective correction of self-imposed conversation cap; original frozen cap1000)' if reason=='technically eligible' else reason})
(R/'report/matched-screen-feasibility.json').write_text(json.dumps({'candidate_rule':'First frozen paired study per modality/model; full screenshot byte sequence only; no outcome-driven screen selection; at most four attachments','candidates':feasibility},indent=2)+'\n')
