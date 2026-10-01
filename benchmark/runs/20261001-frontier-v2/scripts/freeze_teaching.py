#!/usr/bin/env python3
"""Curator-only frozen published diagnosis terms and visible imaging targets."""
import hashlib,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];P=ROOT/'.private/frontier-v2';R=Path(__file__).resolve().parents[1]
# Diagnosis names and morphology come from the existing published report,
# never model outputs. Regexes define terminology recognition, not adjudication.
TARGETS={
 'PMC12689878':('Post-traumatic dysphagia',r'dysphagia',r'residue|retention|aspiration|impaired.{0,30}swallow'),
 'PMC12338180':('Gastric diverticulum',r'gastric diverticul|diverticul.{0,30}(?:gastric|stomach)',r'diverticul|outpouch'),
 'PMC12324042':('Gastrojejunocolic fistula',r'gastro(?:jejuno)?colic fistula|gastrojejunocolic|(?:gastr|stomach).{0,60}(?:fistul|colon)|fistul.{0,60}(?:colon|colonic)',r'fistul|abnormal.{0,30}communication'),
 'PMC12494590':('Esophageal duplication cyst',r'(?:esophageal|oesophageal|foregut).{0,30}duplication cyst|duplication cyst',r'achalasia|pseudoachalasia|bird.beak|distal.{0,30}taper|esophag.{0,30}dilat'),
 'PMC12808875':('Primary aortic angiosarcoma',r'angiosarcoma|aortic sarcoma',r'aortic.{0,50}(?:uptake|avid|activity|inflamm)|(?:uptake|avid|activity).{0,50}aort'),
 'PMC12813286':('Cardiac sarcoidosis',r'cardiac sarcoid|sarcoid.{0,30}(?:heart|cardiac|myocard)',r'myocard.{0,50}(?:uptake|avid|activity)|(?:uptake|avid|activity).{0,50}myocard'),
 'PMC12771140':('Thymoma with splenic metastasis',r'thymoma|thymic malignan',r'(?:splenic|spleen).{0,45}(?:lesion|mass|uptake|avid)|(?:lesion|mass|uptake|avid).{0,45}(?:splenic|spleen)'),
 'PMC12723220':('Recurrent lymphoma involving pulmonary vein',r'lymphoma',r'pulmonary vein|left atrial.{0,30}(?:lesion|mass|involv)'),
 'PMC12625026':('Large-cell neuroendocrine prostate carcinoma',r'neuroendocrine.{0,40}(?:carcinoma|cancer)|large.cell.{0,40}(?:carcinoma|cancer)',r'(?:prostat|pelvi).{0,45}(?:mass|tumou?r|lesion|uptake)|(?:mass|tumou?r|lesion|uptake).{0,45}(?:prostat|pelvi)'),
 'PMC12830000':('Ductal carcinoma in situ',r'ductal carcinoma in situ|\bDCIS\b',r'microcalcific|calcific'),
 'PMC12623610':('Metaplastic breast carcinoma',r'metaplastic.{0,30}(?:carcinoma|cancer)',r'mass|lesion|nodule'),
 'PMC12837338':('Male breast carcinoma',r'breast.{0,30}(?:carcinoma|cancer)|(?:ductal|mammary).{0,30}carcinoma',r'mass|lesion|nodule'),
 'PMC12699083':('Invasive breast carcinoma in fibrous disease',r'breast.{0,30}(?:carcinoma|cancer)|(?:ductal|mammary).{0,30}carcinoma|invasive carcinoma',r'asymmetr|density|architectural distort'),
 'PMC12812165':('Brown tumors from hyperparathyroidism',r'brown tumou?r|hyperparathyroid',r'(?:rib|chest wall).{0,50}(?:mass|lesion)|(?:mass|lesion).{0,50}(?:rib|chest wall)'),
 'PMC12805601':('Anterior urethral valve',r'anterior urethral valve|\bAUV\b',r'hydronephro|urethra.{0,30}dilat|dilat.{0,30}urethra|megacyst'),
 'PMC12602904':('Sternocleidomastoid rupture and hematoma',r'(?:sternocleidomastoid|\bSCM\b).{0,60}(?:rupture|tear)|(?:rupture|tear).{0,60}(?:sternocleidomastoid|\bSCM\b)',r'hematoma|haematoma|muscle.{0,40}(?:tear|rupture)'),
 'PMC12849064':('Bilateral uveal/choroidal effusion',r'(?:uveal|choroid).{0,30}(?:effusion|detach)',r'(?:choroid|uveal).{0,30}(?:effusion|detach)'),
 'PMC12854931':('Shoulder synovial chondromatosis',r'synovial (?:osteo)?chondromatosis',r'calcif.{0,35}(?:bodies|body)|loose bod|intra.articular.{0,30}(?:calcif|bodies)'),
 'PMC12767946':('Williams-Campbell syndrome',r'williams.campbell',r'bronchiecta|cystic.{0,30}(?:lung|lesion)'),
 'PMC12727386':('Rapidly destructive hip disease',r'rapidly (?:destructive|progressive).{0,30}(?:hip|osteoarth)|rapid.{0,30}(?:hip destruction|hip arthropathy)',r'femoral head.{0,40}(?:destruct|resorp|dissolu|collapse)|(?:destruct|resorp|dissolu|collapse).{0,40}femoral head'),
 'PMC12778971':('Proximal humeral peri-implant fracture',r'(?:humer|proximal humer|surgical neck).{0,50}fracture|fracture.{0,50}(?:humer|surgical neck)',r'fracture'),
 'PMC12578567':('Monteggia fracture-dislocation',r'monteggia',r'(?:ulna.{0,40}fracture|fracture.{0,40}ulna)|radial head.{0,30}disloc'),
 'PMC12707725':('Pituitary macroadenoma',r'pituitary (?:macro)?adenoma|macroadenoma',r'(?:sellar|pituitary).{0,40}(?:mass|lesion|adenoma)|macroadenoma'),
 'PMC12998254':('Mid-ventricular Takotsubo cardiomyopathy',r'takotsubo|stress.induced cardiomyopath',r'mid.ventricul.{0,45}(?:dysfunction|akine|hypokine|balloon|wall.motion)|(?:akine|hypokine|balloon).{0,45}mid.ventricul'),
 'PMC12715121':('Epidural cavernous hemangioma',r'cavernous h[ae]+mangioma|cavernous malformation|epidural h[ae]+mangioma',r'(?:epidural|dumbbell|paraspinal).{0,50}(?:mass|lesion|tumou?r)|(?:mass|lesion|tumou?r).{0,50}(?:epidural|dumbbell|paraspinal)'),
 'PMC12550707':('Pelizaeus-Merzbacher disease',r'pelizaeus.merzbacher|\bPMD\b',r'hypomyelin|leukodystroph|white matter.{0,50}(?:hyperintens|signal)'),
 'PMC12718484':('Nasal solitary fibrous tumor',r'solitary fibrous tumou?r|\bSFT\b',r'(?:nasal|sinonasal).{0,45}(?:mass|lesion|tumou?r)|(?:mass|lesion|tumou?r).{0,45}(?:nasal|sinonasal)'),
 'PMC12765126':('Giant hydronephrosis',r'hydronephro',r'hydronephro|dilat.{0,40}(?:collecting|pelvi)|(?:collecting|pelvi).{0,40}dilat'),
 'PMC12712397':('Primary Sjogren syndrome',r'sj[oö]gren',r'sialadenitis|parotid.{0,35}(?:enlarg|calcif)|(?:enlarg|calcif).{0,35}parotid'),
 'PMC12860284':('Interhemispheric acute subdural hematoma',r'subdural (?:h[ae]+matoma|hemorrhage|haemorrhage)',r'subdural|interhemispheric.{0,30}(?:hemorr|haemorr|blood|hematoma)'),
 'PMC12763897':('Endobronchial glomus tumor',r'glomus',r'(?:endobronchial|bronch|tracheal).{0,50}(?:mass|lesion|tumou?r)|(?:mass|lesion|tumou?r).{0,50}(?:endobronchial|bronch|tracheal)'),
 'PMC12718670':('Mandibular first-molar periapical lesion/infection',r'periapical|apical periodontitis|odontogenic.{0,30}(?:infect|cyst)|dental.{0,30}(?:infect|abscess)',r'periapical|radiolucen|odontogenic|bone loss'),
 'PMC12647393':('External replacement root resorption',r'(?:replacement|external).{0,25}(?:root )?resorption|ankylosis|root resorption',r'resorption|ankylosis'),
 'PMC12451084':('Mandibular canine transmigration',r'canine.{0,30}(?:transmigr|impac|transpos)|(?:transmigr|impac|transpos).{0,30}canine',r'transmigr|impacted.{0,30}canine|canine.{0,30}impac'),
 'PMC12625601':('Complex odontoma',r'odontoma',r'odontoma|radiopaque.{0,30}(?:mass|lesion)|calcif.{0,30}(?:mass|lesion)'),
 'PMC12767806':('Aneurysmal bone cyst with dentigerous cyst',r'aneurysmal bone cyst|\bABC\b',r'multilocul|expansile.{0,30}(?:cyst|lesion)|cystic.{0,30}(?:lesion|mass)'),
}
EXCLUSIONS={
 'PMC12705489':'Visual QA: purported mammography figure is an ultrasound raster; modality mismatch.',
 'PMC12889389':'Visual QA: diagnostic answer is printed beneath the development image.',
 'PMC12738374':'Source ultrasound caption says gallstones, but final case establishes gallbladder agenesis; incompatible reference for this supplied image.',
 'PMC12661876':'Only serial post-treatment images; initial presenting diagnostic imaging absent.',
}

def main():
    assert not any((P/'results/evaluation').glob('*/gpt-6-*/PUB-*')), 'Teaching evaluation already started'
    manifest=json.loads((P/'pmc-manifest.json').read_text());gold=[];cases=[];excluded=[]
    for row in manifest['cases']:
        id=row['source_id']
        if id in EXCLUSIONS:excluded.append(dict(row,reason=EXCLUSIONS[id]));continue
        packet_path=P/'agent-visible'/row['case_id']/'input.json';packet=json.loads(packet_path.read_text())
        ref_path=P/'references'/(row['case_id']+'.json');ref=json.loads(ref_path.read_text())
        # Neutral chronology, copied from source figure descriptors, with no
        # findings, source title, disease name or interpretation in the packet.
        chronology=[]
        for f in ref['figures']:
            c=f['caption'].lower()
            label='follow-up/post-treatment' if any(t in c for t in ['follow-up','follow up','postoperative','post-operative','after treatment','after closed reduction','one-month','one‐month','four-month','four‐month','12-month review']) else 'baseline/pre-treatment' if any(t in c for t in ['preoperative','pre-operative','pre-treatment','at presentation','initial','baseline']) else 'time point not reliably specified'
            chronology.append({'file':f['file'],'time_point':label})
        packet['view_chronology']=chronology
        packet['coverage']='Selected published clinical case figures; some composite figures contain supplementary modalities or follow-up time points. Chronology supplied where reliable. Not a complete original examination.'
        packet_path.write_text(json.dumps(packet,indent=2)+'\n')
        if row['stage']=='evaluation':
            assert id in TARGETS,'No pre-output scoring target: '+id
            name,diagnosis,morphology=TARGETS[id]
            gold.append({'case_id':row['case_id'],'modality':row['modality'],'source_id':id,'source_url':row['source_url'],'published_diagnosis':name,'diagnosis_regex':diagnosis,'visible_imaging_target_regex':morphology,'reference_type':ref['reference_type'],'reference_sha256':hashlib.sha256(ref_path.read_bytes()).hexdigest(),'basis':'Existing physician case narrative and imaging figure interpretation; not new clinical adjudication'})
        cases.append({'case_id':row['case_id'],'stage':row['stage'],'modality':row['modality'],'images':row['images'],'input_sha256':hashlib.sha256(packet_path.read_bytes()).hexdigest(),'images_sha256':[hashlib.sha256((packet_path.parent/f).read_bytes()).hexdigest() for f in packet['image_files']],'reference_sha256':hashlib.sha256(ref_path.read_bytes()).hexdigest()})
    gold_path=P/'teaching-gold.json';gold_path.write_text(json.dumps({'cases':gold,'scoring':'Prespecified lexical recognition of the published diagnosis in the primary field and up to three differential entries; separate morphological term recognition anywhere in findings/report. Not semantic clinical adjudication. Failure/abstention counted as nonrecognition.'},indent=2)+'\n');gold_path.chmod(0o600)
    protocol={'frozen_unix':time.time(),'models':['gpt-6.1-sol','gpt-6-astra'],'effort':'high','cases':cases,'gold_sha256':hashlib.sha256(gold_path.read_bytes()).hexdigest(),'cohort':'Published clinician-authored case presentations with source imaging interpretations; distinct from routine signed reports','primary_metric':'Published diagnosis terminology recognized in primary field; not diagnosis adjudication or hospital diagnostic accuracy','secondary_metrics':['Diagnosis terminology in primary plus three-entry differential','Published morphological target terminology anywhere in findings/report','Completion, latency, token counts, abstentions and input limitations'], 'clinical_limits':['Physician-selected annotated images','Some composites include supplementary modalities and longitudinal treatment images','Pathologic/genetic/causal diagnoses may require evidence outside the supplied modality','Rare disease enriched, no negatives or specificity estimate','Public pretraining/memorization exposure unknown'], 'controls_case_ids':[next(x['case_id'] for x in cases if x['stage']=='evaluation' and x['modality']==m) for m in ['CBCT','FL','NM','MG','US','DX','MR','CT']],'repeat_case_ids':[],'routine_protocol_sha256':hashlib.sha256((R/'PROTOCOL-ROUTINE.json').read_bytes()).hexdigest()}
    (R/'PROTOCOL-TEACHING.json').write_text(json.dumps(protocol,indent=2)+'\n')
    (P/'teaching-exclusions.json').write_text(json.dumps({'pre_inference_exclusions':excluded,'acquisition_exclusions':manifest['exclusions']},indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'evaluation':len(gold),'development':len(cases)-len(gold),'gold_sha256':protocol['gold_sha256']}))

if __name__=='__main__':main()
