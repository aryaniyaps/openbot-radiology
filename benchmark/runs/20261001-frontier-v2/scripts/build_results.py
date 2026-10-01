#!/usr/bin/env python3
"""Curator-only scoring from frozen references; publishes derived data, no raw reports."""
import argparse,collections,csv,hashlib,json,math,random,re,statistics,time,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];R=Path(__file__).resolve().parents[1];P=ROOT/'.private/frontier-v2'
MODELS=['gpt-6.1-sol','gpt-6-astra']

def frozen_reader_soul_sha(condition):
    guide=json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text())
    skill=(ROOT/'config/openmausbot/skills/radiology-study-read/SKILL.md').read_text()
    if condition=='cross-review':skill+='\n'+(ROOT/'config/openmausbot/skills/radiology-report-review/SKILL.md').read_text()
    soul='Independent blinded radiology research assistant. Use only the clinical context and images supplied in this thread. Never use tools, files, memory, public-case recall or other agents. No doctor report or correct answer is supplied. '+guide['shared']+'\n'+skill
    return hashlib.sha256(soul.encode()).hexdigest()

def wilson(k,n):
    if not n:return None
    z=1.959963984540054;d=1+z*z/n;c=(k/n+z*z/(2*n))/d;h=z*math.sqrt(k/n*(1-k/n)/n+z*z/(4*n*n))/d
    return [max(0,c-h),min(1,c+h)]

def recognized(text,pattern):
    text=unicodedata.normalize('NFKC',text)
    for match in re.finditer(pattern,text,re.I):
        prefix=re.split(r'[.;\n]',text[:match.start()])[-1][-65:]
        if re.search(r'\b(?:no|without|ruled out|not consistent with|not suggestive of|unlikely)\b',prefix,re.I):continue
        return True
    return False

def load_result(case,model,condition='direct',suffix=''):
    path=P/'results/evaluation'/condition/model/(case+suffix)/'result.json'
    first=json.loads(path.read_text()) if path.exists() else None
    if not suffix and first and first.get('status')=='controller-failure' and first.get('exception')=='HTTPError: HTTP Error 507: Insufficient Storage':
        # Only upload failures with zero model requests can be recovered. Keep
        # the initial result and expose it beside the first diagnostic output.
        assert not list(path.parent.glob('request-*.json')) and not first.get('turns'), 'Never retry a diagnostic answer'
        recovery=path.parent.parent/(case+'-transport-recovery')/'result.json'
        if recovery.exists():
            recovered=json.loads(recovery.read_text());recovered['first_attempt_status']=first['status'];recovered['first_attempt_exception']=first['exception'];recovered['transport_recovery']=True
            return recovered
        first['transport_recovery_pending']=True
    return first

def clean_answer(r):
    return r['structured_answer'] if r and r.get('status')=='succeeded' and r.get('native_identity',{}).get('status')=='verified' and r.get('structured_answer') else None

def score_teaching(gold,r):
    a=clean_answer(r)
    if not a or a['abstention']:return {'primary_recognition':False,'differential_recognition':False,'morphology_recognition':False}
    primary=a['primary_diagnosis'];diff=primary+'\n'+'\n'.join(a['differential'][:3]);body=json.dumps({k:a.get(k) for k in ['primary_diagnosis','key_findings','report_draft']})
    return {'primary_recognition':recognized(primary,gold['diagnosis_regex']),
            'differential_recognition':recognized(diff,gold['diagnosis_regex']),
            'morphology_recognition':recognized(body,gold['visible_imaging_target_regex'])}

def summarize_label(rows):
    c=collections.Counter();positive=negative=0
    for row in rows:
        g,p=row['reference'],row['prediction']
        if g=='present':
            positive+=1;c['TP' if p=='present' else 'FN' if p=='absent' else 'unresolved_positive']+=1
        elif g=='absent':
            negative+=1;c['TN' if p=='absent' else 'FP' if p=='present' else 'unresolved_negative']+=1
    for k in ['TP','FN','FP','TN','unresolved_positive','unresolved_negative']:c.setdefault(k,0)
    c.update(reference_positive=positive,reference_negative=negative)
    c['all_assigned_positive_detection']=c['TP']/positive if positive else None
    c['positive_detection_ci95']=wilson(c['TP'],positive)
    c['all_assigned_correct_negative']=c['TN']/negative if negative else None
    c['correct_negative_ci95']=wilson(c['TN'],negative)
    c['definite_only_sensitivity']=c['TP']/(c['TP']+c['FN']) if c['TP']+c['FN'] else None
    c['definite_only_specificity']=c['TN']/(c['TN']+c['FP']) if c['TN']+c['FP'] else None
    return dict(c)

def paired_difference(values,seed='frontier-v2-paired-bootstrap'):
    if not values:return None
    rng=random.Random(seed);n=len(values);d=[sum(rng.choice(values) for _ in range(n))/n for _ in range(5000)];d.sort()
    return {'n':n,'astra_minus_sol':sum(values)/n,'patient_bootstrap_ci95':[d[124],d[4874]],'bootstrap_samples':5000,'seed':seed}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--require-complete',action='store_true');a=ap.parse_args();report=R/'report';report.mkdir(exist_ok=True)
    routine=json.loads((R/'PROTOCOL-ROUTINE.json').read_text());teaching=json.loads((R/'PROTOCOL-TEACHING.json').read_text());gold=json.loads((P/'teaching-gold.json').read_text());golds={x['case_id']:x for x in gold['cases']};cases=routine['cases']+[x for x in teaching['cases'] if x['stage']=='evaluation'];assignment_rows=[];label_rows=[];teaching_rows=[];operational=[]
    for row in cases:
        case=row['case_id'];is_teaching=case in golds;ref=json.loads((P/'references'/(case+'.json')).read_text())
        for model in MODELS:
            r=load_result(case,model);v=clean_answer(r)
            result={'case_id':case,'modality':row['modality'],'cohort':'published case figures' if is_teaching else row['cohort'],'model':model,'status':r['status'] if r else 'pending','qualified':bool(v),'abstention':v.get('abstention') if v else None,'primary_diagnosis':v['primary_diagnosis'][:350] if v else None,'differential':v['differential'] if v else None,'confidence':v.get('confidence') if v else None,'seconds':r['finished_unix']-r['started_unix'] if r else None,'image_count':len(r['input_manifest']) if r else row.get('images'),'result_sha256':hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest() if r else None}
            if is_teaching:
                scored=score_teaching(golds[case],r);result.update(scored);result['published_diagnosis']=golds[case]['published_diagnosis'];result['source_url']=golds[case]['source_url'];teaching_rows.append(result.copy())
            else:
                scored=[]
                for cls,label in ref['labels'].items():
                    pred=v.get('findings_status',{}).get(cls,'unresolved') if v else 'failure'
                    scorable=label['state'] in ['present','absent'];match=pred==label['state'] if scorable else None
                    item={'case_id':case,'modality':row['modality'],'model':model,'target':cls,'reference':label['state'],'prediction':pred,'scorable':scorable,'matches':match};label_rows.append(item)
                    if scorable:scored.append(match)
                result['scorable_assertions']=len(scored);result['matched_assertions']=sum(scored);result['all_scorable_assertions_match']=all(scored) if scored else None
            assignment_rows.append(result)
            result['first_attempt_status']=r.get('first_attempt_status',r['status']) if r else 'pending'
            result['transport_recovery']=bool(r and r.get('transport_recovery'))
            result['transport_recovery_pending']=bool(r and r.get('transport_recovery_pending'))
            if r:
                turns=r.get('turns',[]);operational.append({'case_id':case,'model':model,'modality':row['modality'],'cohort':result['cohort'],'status':r['status'],'seconds':result['seconds'],'native_duration_ms':sum(t.get('duration_ms') or 0 for t in turns),'turns':len(turns),'input_tokens':sum((t.get('usage') or {}).get('input') or 0 for t in turns),'output_tokens':sum((t.get('usage') or {}).get('output') or 0 for t in turns),'cached_input_tokens':sum((t.get('usage') or {}).get('cachedInput') or 0 for t in turns),'tool_calls':sum(t.get('tool_calls') or 0 for t in turns),'delivered_images':len(r.get('native_identity',{}).get('delivered_images',[])),'delivered_pixels':[x['pixels'] for x in r.get('native_identity',{}).get('delivered_images',[])],'usd':None})
    pending=sum(x['status']=='pending' or x['transport_recovery_pending'] for x in assignment_rows)
    if a.require_complete:assert not pending,'Missing primary assignments: '+str(pending)
    routine_metrics=[]
    for model in MODELS:
        for modality in ['CXR','CT','MR']:
            targets=sorted({x['target'] for x in label_rows if x['modality']==modality})
            for target in targets:
                rows=[x for x in label_rows if x['model']==model and x['modality']==modality and x['target']==target]
                routine_metrics.append(dict(model=model,modality=modality,target=target,**summarize_label(rows)))
    teaching_metrics=[]
    for model in MODELS:
        for modality in ['CBCT','FL','NM','MG','US','DX','MR','CT']:
            rows=[x for x in teaching_rows if x['model']==model and x['modality']==modality];n=len(rows)
            d={'model':model,'modality':modality,'assigned':n,'qualified':sum(x['qualified'] for x in rows),'abstentions':sum(bool(x['abstention']) for x in rows)}
            for metric in ['primary_recognition','differential_recognition','morphology_recognition']:
                k=sum(x[metric] for x in rows);d[metric+'_count']=k;d[metric+'_rate']=k/n if n else None;d[metric+'_ci95']=wilson(k,n)
            teaching_metrics.append(d)
    paired=[]
    for modality in ['CXR','CT','MR']:
        vals=[]
        for row in routine['cases']:
            if row['modality']!=modality:continue
            pair=[next(x for x in assignment_rows if x['case_id']==row['case_id'] and x['model']==m) for m in MODELS]
            if pair[0]['scorable_assertions']:
                vals.append((pair[1]['matched_assertions']-pair[0]['matched_assertions'])/pair[0]['scorable_assertions'])
        paired.append({'modality':modality,'cohort':'routine assertion agreement',**(paired_difference(vals) or {})})
    for modality in ['CBCT','FL','NM','MG','US','DX','MR','CT']:
        vals=[]
        for g in gold['cases']:
            if g['modality']!=modality:continue
            vals.append(int(score_teaching(g,load_result(g['case_id'],MODELS[1]))['primary_recognition'])-int(score_teaching(g,load_result(g['case_id'],MODELS[0]))['primary_recognition']))
        paired.append({'modality':modality,'cohort':'published diagnosis term recognition',**(paired_difference(vals) or {})})
    for metric in ['primary_recognition','differential_recognition']:
        vals=[int(score_teaching(g,load_result(g['case_id'],MODELS[1]))[metric])-int(score_teaching(g,load_result(g['case_id'],MODELS[0]))[metric]) for g in gold['cases']]
        paired.append({'modality':'all published presentations','cohort':metric,**paired_difference(vals)})
    ops_summary=[]
    for model in MODELS:
        rows=[x for x in operational if x['model']==model];seconds=sorted(x['seconds'] for x in rows)
        ops_summary.append({'model':model,'primary_assigned':len(cases),'terminal':len(rows),'qualified':sum(x['qualified'] for x in assignment_rows if x['model']==model),'status':dict(collections.Counter(x['status'] for x in assignment_rows if x['model']==model)),'first_attempt_status':dict(collections.Counter(x['first_attempt_status'] for x in assignment_rows if x['model']==model)),'pre_inference_transport_recoveries':sum(x['transport_recovery'] for x in assignment_rows if x['model']==model),'median_seconds':statistics.median(seconds) if seconds else None,'p90_seconds':seconds[max(0,math.ceil(.9*len(seconds))-1)] if seconds else None,'input_tokens':sum(x['input_tokens'] for x in rows),'output_tokens':sum(x['output_tokens'] for x in rows),'cached_input_tokens':sum(x['cached_input_tokens'] for x in rows),'doctor_time_saved':None,'usd':None})
    sources=[{'case_id':g['case_id'],'modality':g['modality'],'source_id':g['source_id'],'source_url':g['source_url'],'published_diagnosis':g['published_diagnosis'],'reference_type':g['reference_type'],'reference_sha256':g['reference_sha256']} for g in gold['cases']]
    context_audit=json.loads((R/'evidence/context-term-audit.json').read_text());flagged=set(context_audit['flagged_case_ids']);context_subset=[]
    teaching_overall=[]
    for model in MODELS:
        all_rows=[x for x in teaching_rows if x['model']==model]
        overall={'model':model,'assigned':len(all_rows),'qualified':sum(x['qualified'] for x in all_rows),'abstentions':sum(bool(x['abstention']) for x in all_rows)}
        for metric in ['primary_recognition','differential_recognition','morphology_recognition']:
            k=sum(x[metric] for x in all_rows);overall.update({metric+'_count':k,metric+'_rate':k/len(all_rows),metric+'_ci95':wilson(k,len(all_rows))})
        teaching_overall.append(overall)
        rows=[x for x in teaching_rows if x['model']==model and x['case_id'] not in flagged]
        context_subset.append({'model':model,'assigned':len(rows),'primary_recognition_count':sum(x['primary_recognition'] for x in rows),'differential_recognition_count':sum(x['differential_recognition'] for x in rows),'morphology_recognition_count':sum(x['morphology_recognition'] for x in rows),'selection':'No exact frozen target terminology in supplied pre-imaging context; source-audit sensitivity subset, original primary unchanged'})
    data={'generated_unix':time.time(),'status':'complete' if pending==0 else 'interim','primary_studies':len(cases),'primary_assignments':len(assignment_rows),'pending':pending,'routine_metrics':routine_metrics,'teaching_metrics':teaching_metrics,'teaching_overall':teaching_overall,'teaching_no_explicit_target_context_subset':context_subset,'paired_differences':paired,'operational_summary':ops_summary,'metric_limit':'Report assertion concordance and lexical published-term recognition; no independent clinical adjudication, complete-exam accuracy, doctor time-savings or dollar-cost estimate'}
    model_reads=[]
    for row in cases:
        for model in MODELS:
            r=load_result(row['case_id'],model);answer=clean_answer(r)
            if answer:
                text=json.dumps(answer)
                for image in r.get('input_manifest',[]):
                    text=text.replace(str(P/'platform/attachments'/image['attachment_name']),image['file'])
                    text=text.replace(image['attachment_name'],image['file'])
                answer=json.loads(text)
            model_reads.append({'case_id':row['case_id'],'model':model,'status':r['status'] if r else 'pending','structured_answer':answer,'normalization':'Only application-owned image filenames/paths mapped to supplied logical view names; no clinical answer repair'})
    outputs={'summary.json':data,'assignment-results.json':assignment_rows,'routine-assertions.json':label_rows,'teaching-case-results.json':teaching_rows,'operational-metrics.json':operational,'source-provenance.json':sources,'structured-model-reads.json':model_reads}
    for filename,value in outputs.items():(report/filename).write_text(json.dumps(value,indent=2)+'\n')
    for filename,rows in [('assignment-results.csv',assignment_rows),('routine-metrics.csv',routine_metrics),('teaching-metrics.csv',teaching_metrics),('operational-metrics.csv',operational)]:
        with (report/filename).open('w') as f:
            fields=list(dict.fromkeys(k for row in rows for k in row))
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({'primary_studies':len(cases),'pending':pending,'terminal':len(operational),'status':data['status']}))

if __name__=='__main__':main()
