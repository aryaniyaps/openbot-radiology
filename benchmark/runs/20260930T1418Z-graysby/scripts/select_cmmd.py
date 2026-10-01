#!/usr/bin/env python3
"""Curator-only patient sampling; never reads lesion masks or model outputs."""
import collections,hashlib,json,os,pathlib,random
import openpyxl
ROOT=pathlib.Path(__file__).resolve().parents[1]
if os.getuid()!=0:raise SystemExit('Run as authorized curator; references must remain unreadable to diagnostic uid')
REF=ROOT/'scoring/references'
wb=openpyxl.load_workbook(REF/'cmmd-clinical.xlsx',read_only=True,data_only=True)
iterator=iter(wb.active.values);header=next(iterator);patients=collections.defaultdict(list)
for values in iterator:
    record=dict(zip(header,values))
    patients[str(record['ID1'])].append({k:record[k] for k in ['LeftRight','Age','number','classification']})
series=json.loads((ROOT/'private/cmmd-series.json').read_text())
by_patient=collections.defaultdict(list)
for s in series:by_patient[s['PatientID']].append(s)
eligible={};exclusions=[]
known_duplicate_patients={'D1-0202','D2-0284','D1-0808','D1-1292'}
for pid,breasts in sorted(patients.items()):
    reasons=[]; ss=by_patient.get(pid,[])
    if pid in known_duplicate_patients:reasons.append('TCIA-documented cross-patient identical pixel payload; exclude complete duplicate group')
    if len(ss)!=1:reasons.append('requires exactly one catalogued study/series in this candidate design')
    sides=[b['LeftRight'] for b in breasts]
    if len(set(sides))!=len(sides) or not set(sides)<=set(['L','R']):reasons.append('duplicate or unsupported breast side')
    if not set(b['classification'] for b in breasts)<=set(['Benign','Malignant']):reasons.append('missing or unsupported class')
    try:
        expected=sum(int(b['number']) for b in breasts)
        if ss and int(ss[0]['ImageCount'])<expected:reasons.append('catalogue image count is less than the recorded labeled-breast view count')
    except (TypeError,ValueError):reasons.append('invalid view count')
    if reasons:exclusions.append({'patient_id':pid,'reasons':reasons});continue
    eligible[pid]={'patient_id':pid,'label':int(any(b['classification']=='Malignant' for b in breasts)), 'reference_breasts':breasts,'series':ss[0]}
# TCIA documents bilateral D2 imaging with only the malignant side labeled.
# Reference 'number' counts the labeled breast's views, not all study views.
# Preserve all catalogue images, including contralateral images.
# Patient-level binary malignancy label; negatives have biopsy-labeled benign disease, not normal screening.
seed=int(hashlib.sha256((ROOT/'REQUEST.md').read_bytes()+b'CMMD-cohort-v3-matched-count').hexdigest(),16)
rng=random.Random(seed)
strata={(label,count):sorted(pid for pid,v in eligible.items() if v['label']==label and int(v['series']['ImageCount'])==count) for label in [0,1] for count in [2,4]}
for ids in strata.values():rng.shuffle(ids)
selected={};already_exposed=['D1-0001', 'D1-0021', 'D1-0322', 'D1-0870', 'D1-0932', 'D1-0939', 'D1-1341', 'D1-1402', 'D2-0051', 'D2-0661']
for pid in already_exposed:
    assert pid in eligible;selected[pid]='development';strata[eligible[pid]['label'],int(eligible[pid]['series']['ImageCount'])].remove(pid)
for split,per_class in [('development',{2:3,4:2}),('evaluation',{2:20,4:20}),('fresh_followup',{2:5,4:5})]:
    for label in [0,1]:
        for count,target in per_class.items():
            existing=sum(eligible[pid]['label']==label and int(eligible[pid]['series']['ImageCount'])==count and role==split for pid,role in selected.items())
            need=target-existing;assert need>=0 and len(strata[label,count])>=need
            for pid in strata[label,count][:need]:selected[pid]=split
            strata[label,count]=strata[label,count][need:]
refs=[];manifest=[]
for number,(pid,split) in enumerate(sorted(selected.items(),key=lambda x:(x[1],x[0])),start=1):
    v=eligible[pid];case=f'CMMD-{number:04}'
    refs.append({'case_id':case,'split':split,'patient_id':pid,'label':v['label'],'reference_breasts':v['reference_breasts']})
    manifest.append({'case_id':case,'split':split,'source_patient_id':pid,'modality':'MG','task':'patient-level any biopsy-labeled malignant breast versus all labeled breasts benign','series':v['series'],'dicom_eligibility':'pending image laterality, technical completeness and leakage validation'})
assert len(selected)==110 and len(selected)==len(set(selected))
for split,count in [('development',10),('evaluation',80),('fresh_followup',20)]:assert sum(x['split']==split for x in manifest)==count
for filename,content in [('cmmd-selected-labels.json',refs),('cmmd-exclusions.json',exclusions)]:
    p=REF/filename;p.write_text(json.dumps(content,indent=2)+'\n');p.chmod(0o600)
# Candidate manifests are operator-only; do not expose source IDs to a diagnostic model.
p=ROOT/'private/cmmd-candidate-cohort.json';p.write_text(json.dumps(manifest,indent=2)+'\n');p.chmod(0o600);os.chown(p,1000,1000)
summary={'status':'candidate sample; protocol not frozen and image eligibility not yet verified','seed_sha256':hashlib.sha256(str(seed).encode()).hexdigest(),'sampling':'seeded random within patient class and study image count; 20 two-view and 20 four-view patients in each evaluation class; no model outputs, lesion locations or abnormality categories used','reference_patients':len(patients),'catalogue_patients':len(by_patient),'eligible_patients':len(eligible),'excluded_patients':len(exclusions),'eligible_class_counts':dict(collections.Counter(v['label'] for v in eligible.values())),'split_counts':dict(collections.Counter(selected.values())),'development_eval_overlap':0,'fresh_eval_overlap':0,'exposed_development_patient_count':len(already_exposed),'sampling_revision':'v4 documented duplicate groups excluded; v3 development patients retained','known_duplicate_exclusion_source':'https://www.cancerimagingarchive.net/collection/cmmd/','selected_evaluation_class_counts':dict(collections.Counter(eligible[pid]['label'] for pid,role in selected.items() if role=='evaluation')),'evaluation_class_and_image_count_cells':[{ 'label':label,'image_count':count,'patients':sum(eligible[pid]['label']==label and int(eligible[pid]['series']['ImageCount'])==count and role=='evaluation' for pid,role in selected.items())} for label in [0,1] for count in [2,4]],'total_evaluation_images':sum(int(x['series']['ImageCount']) for x in manifest if x['split']=='evaluation'),'estimated_source_uncompressed_bytes':sum(int(x['series']['FileSize']) for x in manifest),'candidate_manifest_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reference_standard_caveats':['disease-enriched biopsy dataset; no healthy normal class','patient endpoint aggregates breast labels and requires all referenced breasts to be visually supplied','catalogue counts do not yet prove actual DICOM coverage or correctness of view labels','negative means recorded target breasts benign, not independently verified cancer-free entire study','image-count and D1/D2 enrollment confounding require prespecified shortcut and subgroup analyses']}
p=ROOT/'evidence/cmmd-sampling.json';p.write_text(json.dumps(summary,indent=2)+'\n');os.chown(p,1000,1000)
print(json.dumps(summary,indent=2))
