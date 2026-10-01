"""Observed component attribution; serial-duration sums are not measured workflow wall time."""
import pathlib,json,collections,statistics,time
R=pathlib.Path(__file__).resolve().parents[1]
rows=json.loads((R/'report/assignment-results.json').read_text())
key=lambda x:(x['case_id'],x['model'],x['configuration'])
lookup={key(x):x for x in rows if x['stage']=='evaluation' and x['arm']=='B' and not x['attempt']}
logs=[json.loads(l) for l in (R/'private/medgemma-inferences.jsonl').read_text().splitlines()]
records=[]
for row in rows:
    if row['configuration'] not in ['delegated','second-reader','self-review'] or row['execution_status']=='not_run':continue
    p=R/row['result_path'];v=json.loads(p.read_text());base=lookup[(row['case_id'],row['model'],'primary')]
    parts=[row]+([base] if row['configuration'] in ['second-reader','self-review'] else [])
    mg=lookup[(row['case_id'],'google/medgemma-1.5-4b-it','primary')] if row['configuration']!='self-review' else None
    physical=[]
    if mg:
        m=json.loads((R/mg['result_path']).read_text())
        physical=[d for d in logs if d.get('inference_seconds') is not None and m['started_unix']<=d['started_unix']<=m['finished_unix'] and sorted(i['sha256'] for i in d.get('images',[]))==sorted(i['sha256'] for i in m['input_manifest'])]
    record={k:row[k] for k in ['case_id','modality','model','configuration','execution_status']}
    record['gpt_components']=len(parts)
    for field in ['input_tokens','cached_input_tokens','output_tokens','latency_ms']:
        known=[x[field] for x in parts if x[field] is not None]
        record[field+'_component_observed_subtotal']=sum(known) if known else None
        record[field+'_missing_components']=len(parts)-len(known)
    record['specialist_component_required']=bool(mg)
    record['specialist_physical_inference_matches']=len(physical)
    record['specialist_observed_inference_seconds']=physical[0]['inference_seconds'] if len(physical)==1 else None
    record['serial_diagnostic_component_seconds']=sum(x['latency_ms']/1000 for x in parts)+(record['specialist_observed_inference_seconds'] if mg else 0) if all(x['latency_ms'] is not None for x in parts) and (not mg or len(physical)==1) else None
    record['result_paths']=[x['result_path'] for x in parts]+([mg['result_path']] if mg else [])
    records.append(record)
groups=[]
for group in sorted({(x['modality'],x['model'],x['configuration']) for x in records}):
    z=[x for x in records if (x['modality'],x['model'],x['configuration'])==group]
    elapsed=[x['serial_diagnostic_component_seconds'] for x in z if x['serial_diagnostic_component_seconds'] is not None]
    inputs=[x['input_tokens_component_observed_subtotal'] for x in z if x['input_tokens_component_observed_subtotal'] is not None]
    specialist=[x['specialist_observed_inference_seconds'] for x in z if x['specialist_observed_inference_seconds'] is not None]
    groups.append(dict(zip(['modality','model','configuration'],group),recorded_cases=len(z),median_serial_diagnostic_component_seconds=statistics.median(elapsed) if elapsed else None,serial_duration_measured_count=len(elapsed),gpt_input_observed_subtotal=sum(inputs) if inputs else None,gpt_input_missing_components=sum(x['input_tokens_missing_components'] for x in z),specialist_component_seconds_observed_subtotal=sum(specialist) if specialist else None,specialist_component_duration_missing=sum(x['specialist_component_required'] and x['specialist_observed_inference_seconds'] is None for x in z)))
controls=[]
for modality,model in sorted({(x['modality'],x['model']) for x in rows if x['stage']=='evaluation' and x['configuration']=='self-review'}):
    cases=sorted({x['case_id'] for x in rows if x['stage']=='evaluation' and x['configuration']=='self-review' and x['modality']==modality and x['model']==model})
    for configuration in ['delegated','second-reader','self-review']:
        z=[x for x in records if x['modality']==modality and x['model']==model and x['configuration']==configuration and x['case_id'] in cases]
        elapsed=[x['serial_diagnostic_component_seconds'] for x in z if x['serial_diagnostic_component_seconds'] is not None]
        complete=len(z)==len(cases)
        controls.append({'modality':modality,'model':model,'configuration':configuration,'case_ids':cases,'planned_cases':len(cases),'recorded_cases':len(z),'pending_cases':len(cases)-len(z),'serial_duration_measured_count':len(elapsed),'median_serial_diagnostic_component_seconds':statistics.median(elapsed) if complete and len(elapsed)==len(cases) else None,'gpt_input_component_observed_subtotal':sum(x['input_tokens_component_observed_subtotal'] for x in z) if complete and all(x['input_tokens_component_observed_subtotal'] is not None and not x['input_tokens_missing_components'] for x in z) else None})
out={'updated_unix':time.time(),'attribution':'Delegated: fresh GPT with specialist + independent specialist. Second reader: original GPT + independent specialist + fresh synthesis GPT. Self review: original GPT + fresh self-review GPT. Same specialist read is physically cached/reused across experiments; attribution represents a separately deployed role workflow, not additional measured GPU execution.','limitations':'Component serial-duration sums are not observed end-to-end wall time and omit setup/preprocessing. GPT and specialist tokens are separate tokenizers and are not combined into currency. No purchase, electricity, hardware or subscription allocation prices. Cached input is a subset.','groups':groups,'same_case_control_groups':controls,'records':records}
(R/'report/role-cost-attribution.json').write_text(json.dumps(out,indent=2)+'\n')
