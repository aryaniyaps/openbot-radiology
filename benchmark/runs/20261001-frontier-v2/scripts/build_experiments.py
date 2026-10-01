#!/usr/bin/env python3
"""Curator-only supplementary metrics; never pool them into primary accuracy."""
import argparse, collections, json, time
from build_results import R, P, MODELS, load_result, clean_answer, summarize_label, frozen_reader_soul_sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--require-complete',action='store_true');args=ap.parse_args()
    pending=[]; assignments=[]
    def get(case,model,condition='direct',suffix=''):
        r=load_result(case,model,condition,suffix)
        if r is None or r.get('transport_recovery_pending'):pending.append([case,model,condition,suffix])
        assignments.append({'case_id':case,'model':model,'condition':condition,'suffix':suffix,'status':r.get('status') if r else 'pending','first_attempt_status':r.get('first_attempt_status',r['status']) if r else 'pending','transport_recovery':bool(r and r.get('transport_recovery')),'qualified':bool(clean_answer(r)), 'seconds':r['finished_unix']-r['started_unix'] if r and r.get('started_unix') else None})
        return r
    def predictions(r):return (clean_answer(r) or {}).get('findings_status',{})
    pnx=json.loads((R/'PROTOCOL-PNX-SUPPLEMENT.json').read_text());pnx_metrics=[]
    for model in MODELS:
        rows=[]
        for case in pnx['cases']:
            r=get(case['case_id'],model);ref=json.loads((P/'references'/(case['case_id']+'.json')).read_text())
            rows.append({'reference':ref['labels']['pneumothorax']['state'],'prediction':predictions(r).get('pneumothorax','unresolved')})
        pnx_metrics.append(dict(model=model,**summarize_label(rows)))
    controls=[];repeats=[]
    for protocol_name in ['PROTOCOL-ROUTINE.json','PROTOCOL-TEACHING.json']:
        protocol=json.loads((R/protocol_name).read_text())
        for model in MODELS:
            for case in protocol.get('controls_case_ids',[]):
                r=get(case,model,'context-only');a=clean_answer(r)
                controls.append({'case_id':case,'model':model,'status':r.get('status') if r else 'pending','abstention':a.get('abstention') if a else None,'delivered_images':len(r.get('native_identity',{}).get('delivered_images',[])) if r else None})
            for case in protocol.get('repeat_case_ids',[]):
                base=load_result(case,model);repeat=get(case,model,'direct','-repeat');b=predictions(base);p=predictions(repeat)
                repeats.append({'case_id':case,'model':model,'baseline_qualified':bool(clean_answer(base)),'repeat_qualified':bool(clean_answer(repeat)),'targets':len(b),'same_states':sum(p.get(k)==v for k,v in b.items()),'exact_state_agreement':b==p if b and p else False})
    review=json.loads((R/'PROTOCOL-REVIEW.json').read_text());reviews=[]
    for case in review['case_ids']:
        ref=json.loads((P/'references'/(case+'.json')).read_text())
        for model in MODELS:
            other=next(m for m in MODELS if m!=model);baseline=load_result(case,other);checked=get(case,model,'cross-review');b=predictions(baseline);p=predictions(checked)
            for target,label in ref['labels'].items():
                if label['state'] not in ['present','absent']:continue
                before=b.get(target,'unresolved');after=p.get(target,'unresolved');gold=label['state']
                reviews.append({'case_id':case,'review_model':model,'baseline_model':other,'frozen_reader_prompt_match':bool(checked and checked.get('soul_sha256')==frozen_reader_soul_sha('cross-review')),'target':target,'reference':gold,'before':before,'after':after,'before_matches':before==gold,'after_matches':after==gold,'corrected_mismatch':before!=gold and after==gold,'introduced_mismatch':before==gold and after!=gold,'before_definite_error':before in ['present','absent'] and before!=gold,'after_definite_error':after in ['present','absent'] and after!=gold})
    review_summary=[]
    for model in MODELS:
        rows=[x for x in reviews if x['review_model']==model]
        exact=[x for x in rows if x['frozen_reader_prompt_match']]
        review_summary.append({'review_model':model,'scorable_assertions':len(rows),'prompt_deviation_cases':len({x['case_id'] for x in rows if not x['frozen_reader_prompt_match']}),'exact_prompt_subset':{'assertions':len(exact),'before_matches':sum(x['before_matches'] for x in exact),'after_matches':sum(x['after_matches'] for x in exact)},**{k:sum(x[k] for x in rows) for k in ['before_matches','after_matches','corrected_mismatch','introduced_mismatch','before_definite_error','after_definite_error']}})
    dense=json.loads((R/'PROTOCOL-DENSE-CT.json').read_text());dense_rows=[]
    def tokens(result,key):return sum((t.get('usage') or {}).get(key) or 0 for t in (result or {}).get('turns',[]))
    for case in dense['cases']:
        ref=json.loads((P/'references'/(case['case_id']+'.json')).read_text())
        for model in MODELS:
            baseline=load_result(case['baseline_case_id'],model);r=get(case['case_id'],model)
            dense_rows.append({'case_id':case['case_id'],'baseline_case_id':case['baseline_case_id'],'model':model,'reference_nodule':ref['labels']['pulmonary_nodule']['state'],'baseline_predictions':predictions(baseline),'dense_predictions':predictions(r),'status':r.get('status') if r else 'pending','baseline_seconds':baseline['finished_unix']-baseline['started_unix'] if baseline else None,'dense_seconds':r['finished_unix']-r['started_unix'] if r and r.get('started_unix') else None,'baseline_input_tokens':tokens(baseline,'input'),'dense_input_tokens':tokens(r,'input'),'dense_output_tokens':tokens(r,'output'),'dense_cached_input_tokens':tokens(r,'cachedInput'),'dense_turns':len(r.get('turns',[])) if r else None,'dense_delivered_images':len(r.get('native_identity',{}).get('delivered_images',[])) if r else None})
    if args.require_complete:assert not pending,'Missing supplementary assignments: '+str(pending)
    data={'generated_unix':time.time(),'status':'complete' if not pending else 'interim','pending':pending,'pnx_supplement':pnx_metrics,'context_controls':controls,'repeats':repeats,'cross_review_assertions':reviews,'cross_review_summary':review_summary,'dense_ct':dense_rows,'assignments':assignments,'limits':['Pneumothorax challenge uses ten previously evaluated report-positive patients, no specificity denominator','Context-only control explicitly requests abstention and cannot isolate causal benefit of images','Repeatability: four cases per model only','Review uses opponent proposals plus identical images; human clinical adjudication unavailable','Denser CT bundles sampling, tile resolution and conversational turns; two reused patients, mechanism experiment only','No supplementary observations enter primary metrics']}
    (R/'report/experiments.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'status':data['status'],'pending':len(pending),'assigned_experiments':len(assignments)}))

if __name__=='__main__':main()
