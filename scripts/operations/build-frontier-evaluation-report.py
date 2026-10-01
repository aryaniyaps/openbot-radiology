#!/usr/bin/env python3
"""Build only from complete frozen-cohort results; no inference or gold access."""
import json, html, collections
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.graphics.shapes import Drawing, Rect, String
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'benchmark/runs/20261001-frontier-v2';OUT=ROOT/'output/pdf/Radiology-Frontier-Model-Evaluation.pdf'
S=json.loads((R/'report/summary.json').read_text());E=json.loads((R/'report/experiments.json').read_text())
assert S['status']==E['status']=='complete','Refuse to publish incomplete results'
for name,file in [('Lato','Lato-Regular.ttf'),('LatoB','Lato-Bold.ttf')]:pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/lato/'+file))
pdfmetrics.registerFontFamily('Lato',normal='Lato',bold='LatoB',italic='Lato',boldItalic='LatoB')
navy,teal,ink=[colors.HexColor(c) for c in ['#152C42','#007F82','#263C4D']]
styles={k:ParagraphStyle(k,fontName='LatoB' if k in ['title','h'] else 'Lato',fontSize=size,leading=lead,textColor=teal if k=='h' else navy if k=='title' else ink,spaceAfter=9) for k,size,lead in [('title',25,29),('h',13,17),('body',10.3,14.5),('small',8.5,11.5),('cell',8.7,11.7)]}
story=[]
def p(s,k='body'):story.append(Paragraph(s,styles[k]))
def title(k,s):p(k.upper(),'h');p(s,'title')
def page():story.append(PageBreak())
def table(rows,widths):
 t=Table([[Paragraph(str(c),styles['cell']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDEBED')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#DAE3E8'))]));story.extend([t,Spacer(1,10)])
def esc(x):return html.escape(str(x))
def pct(x):return '-' if x is None else f'{100*x:.1f}%'
def short(m):return 'Sol' if m=='gpt-6.1-sol' else 'Astra'
def fraction(d,k,n):return f'{d[k]}/{d[n]} ({pct(d[k]/d[n])})' if d[n] else 'No denominator'
def ci(v):return '-' if not v else f'{100*v[0]:.1f}-{100*v[1]:.1f}%'
models=['gpt-6.1-sol','gpt-6-astra']
T={m:[x for x in S['teaching_metrics'] if x['model']==m] for m in models}
counts={m:{k:sum(x[k+'_count'] for x in T[m]) for k in ['primary_recognition','differential_recognition','morphology_recognition']} for m in models}
title('Measured evaluation / 01 October 2026','Frontier radiology<br/>with OpenMausBot')
p('<b>Decision: use the models as supervised assistants, with provisional interpretations and mandatory radiologist review.</b> Both models completed the paired routine-image test, but important findings were missed or left unresolved. These data do not support autonomous whole-examination reporting.')
table([['Measured scope','What was tested'],['106 primary studies / 212 paired reads','40 fresh chest radiographs, 20 reused chest CTs, 10 reused brain MRIs, 36 held-out published case presentations.'],['116 unique evaluation patients including supplement','Ten additional previously evaluated pneumothorax-positive radiographs; denser CT reuses two primary patients.'],['Nine imaging domain groups','CXR, general radiography, CT, MRI, ultrasound, mammography, fluoroscopy, PET/CT nuclear imaging and dental CBCT. Domain groups overlap DICOM modalities.'],['Actual requested models','gpt-6.1-sol and gpt-6-astra; native Codex provider, high effort, fresh independent case conversations.']],[180,327])
p('Published-case diagnosis term recognition','h')
table([['Model','Primary diagnosis','Primary + top-three differential'],*[ [m,f"{counts[m]['primary_recognition']}/36 ({100*counts[m]['primary_recognition']/36:.1f}%)",f"{counts[m]['differential_recognition']}/36 ({100*counts[m]['differential_recognition']/36:.1f}%)"] for m in models]],[155,155,197])
p('Those counts measure prespecified name matching against published clinician case diagnoses, not independently adjudicated clinical accuracy. Figure selection, rare-case enrichment, prior training exposure and diagnoses that require pathology constrain interpretation.','small')
p('A source audit found one case with the target disease name in legitimate prior clinical history. In the remaining 35 cases: '+ '; '.join(short(x['model'])+' primary '+str(x['primary_recognition_count'])+'/35, primary + differential '+str(x['differential_recognition_count'])+'/35' for x in S['teaching_no_explicit_target_context_subset'])+'. This sensitivity subset does not change the original primary cohort.','small')
page();title('Routine physician-report references','What the models detected')
p('All assigned positive detection = definite positive model assertions / all explicit positive source-report assertions. Uncertain, unassessable and failed reads stay in the denominator. Negative results use only explicit source-report negatives; silence is never normality.')
rows=[['Domain / report finding','Sol: detected / positive','Astra: detected / positive']]
for modality in ['CXR','CT','MR']:
 for x in [x for x in S['routine_metrics'] if x['model']==models[0] and x['modality']==modality and x['reference_positive']]:
  y=next(y for y in S['routine_metrics'] if y['model']==models[1] and y['modality']==modality and y['target']==x['target'])
  rows.append([modality+' / '+x['target'].replace('_',' '),fraction(x,'TP','reference_positive'),fraction(y,'TP','reference_positive')])
table(rows,[225,141,141])
p('Why this matters','h')
p('The initial sampled CT presentation detected only one of ten report-positive nodule assertions for each model. An unresolved result is safer than invented certainty, but it still fails to supply the doctor with the reported finding. A dense-input follow-up tests the presentation bottleneck separately.')
p('MRI has only three positive assertions across the scored targets. Matching those assertions cannot establish broad MRI diagnostic reliability. Reports may omit image findings; MR-RATE references include machine translation/restructuring. Chest radiographs use source rasters; CT and MRI use selected montages rather than full examinations.','small')
page();title('Error accounting','Misses, uncertainty and false alarms')
rows=[['Finding / model','TP / FN / unresolved+','TN / FP / unresolved-','Positive 95% CI']]
for modality,target in [('CXR','cardiomegaly'),('CXR','focal_consolidation'),('CXR','pleural_effusion'),('CT','pulmonary_nodule')]:
 for m in models:
  x=next(x for x in S['routine_metrics'] if x['model']==m and x['modality']==modality and x['target']==target)
  rows.append([modality+' '+target.replace('_',' ')+' / '+short(m),f"{x['TP']} / {x['FN']} / {x['unresolved_positive']}",f"{x['TN']} / {x['FP']} / {x['unresolved_negative']}",ci(x['positive_detection_ci95'])])
table(rows,[210,104,104,89])
p('TP: detected report-positive assertion. FN: definite negative against a report positive. TN: definite negative against a report negative. FP: definite positive against a report negative. Unresolved includes uncertainty, unassessable output and technical failure.','small')
p('The fresh chest-radiograph primary cohort has no explicit pneumothorax positives. Its negative reads do not establish sensitivity. The separate ten-positive challenge below closes that measurement gap without quietly changing the primary cohort.','small')
p('No universal winner','h')
p('Compare each intended task and input separately. Patient-level paired bootstrap intervals are published in summary.json; small denominators give wide uncertainty. A single pooled accuracy score would mix incompatible reference types and conceal missed findings.')
page();title('Selected published images','Diagnosis recognition across domains')
rows=[['Domain / n','Sol primary / +diff / morphology','Astra primary / +diff / morphology']]
for mod in ['CBCT','FL','NM','MG','US','DX','MR','CT']:
 a=next(x for x in T[models[0]] if x['modality']==mod);b=next(x for x in T[models[1]] if x['modality']==mod)
 vals=lambda x:' / '.join(str(x[k+'_count']) for k in ['primary_recognition','differential_recognition','morphology_recognition'])
 rows.append([mod+' / '+str(a['assigned']),vals(a),vals(b)])
table(rows,[115,196,196])
p('Primary diagnosis term recognition by domain','h')
d=Drawing(507,135)
for i,mod in enumerate(['CBCT','FL','NM','MG','US','DX','MR','CT']):
 y=119-i*14
 d.add(String(0,y,mod,fontName='Lato',fontSize=8.5,fillColor=ink))
 for j,m in enumerate(models):
  x=next(x for x in T[m] if x['modality']==mod)
  d.add(Rect(55,y+4-j*7,360*x['primary_recognition_rate'],5,fillColor=teal if j else navy,strokeColor=None))
d.add(String(55,0,'0%',fontName='Lato',fontSize=8,fillColor=ink));d.add(String(395,0,'100%',fontName='Lato',fontSize=8,fillColor=ink))
d.add(String(440,113,'Sol',fontName='LatoB',fontSize=8,fillColor=navy));d.add(String(440,97,'Astra',fontName='LatoB',fontSize=8,fillColor=teal))
story.append(d)
p('Three distinct measures','h')
p('<b>Primary:</b> the prespecified published diagnosis term appears in the primary answer. <b>+diff:</b> appears in the primary answer or first three differential entries. <b>Morphology:</b> a prespecified visible imaging term appears in findings/report text. Negated matches and abstentions score zero. These mechanical measures are reproducible; they are not semantic medical adjudication.')
p('Per-domain denominators are only four or five cases; Wilson 95% intervals are published with each rate. Model confidence values are uncalibrated and do not estimate clinical risk.','small')
p('What remains untested','h')
p('Published still figures do not validate ultrasound cine acquisition, screening mammography workflows, complete multiparametric MRI, diagnostic angiography, full PET quantitation, SPECT, interventional guidance or whole-study lesion search. CBCT is a CT subtype; PET/CT cases are grouped under NM. Mixed figures and baseline/follow-up composites are disclosed in source records.')
p('Seven separate development presentations qualified input transport before held-out inference. Printed-answer, mismatched-modality, incompatible-reference and follow-up-only candidates were excluded before the primary cohort ran. No gold feedback was used to tune the held-out prompt.','small')
page();title('Bounded additional experiments','Can input and checking improve the read?')
rows=[['Pneumothorax-positive challenge','Detected / 10','Definite miss / unresolved']]
for x in E['pnx_supplement']:rows.append([x['model'],fraction(x,'TP','reference_positive'),f"{x['FN']} / {x['unresolved_positive']}"])
table(rows,[235,130,142])
p('Ten previously evaluated positive patients, modality-only context, new profiles. This enriched challenge estimates detection on those supplied images, with Wilson intervals in experiments.json; it has no specificity denominator.','small')
rows=[['Denser CT / model','Nodule: baseline to dense','Seconds: baseline to dense']]
for x in E['dense_ct']:rows.append([x['case_id']+' / '+short(x['model']),x['baseline_predictions'].get('pulmonary_nodule','failure')+' to '+x['dense_predictions'].get('pulmonary_nodule','failure'),f"{x['baseline_seconds']:.0f} to {x['dense_seconds']:.0f}" if x['dense_seconds'] else 'Failed'])
table(rows,[190,190,127])
p('Two primary patients, 64 sampled axial positions in both windows, 32 smaller montages across eight native turns per model. Sampling, delivered tile size and conversational turns changed together; this is a mechanism experiment, not an isolated causal test or full CT examination.','small')
p('No nodule-status gain occurred on either patient. Native input usage increased from '+f"{sum(x['baseline_input_tokens'] for x in E['dense_ct']):,}"+' to '+f"{sum(x['dense_input_tokens'] for x in E['dense_ct']):,}"+' tokens across the four reads, including cumulative conversational context. More input alone did not repair the unresolved finding.','small')
rows=[['Independent review model','Corrected mismatches','Introduced mismatches','Before / after matching']]
for x in E['cross_review_summary']:rows.append([short(x['review_model']),x['corrected_mismatch'],x['introduced_mismatch'],f"{x['before_matches']} / {x['after_matches']} of {x['scorable_assertions']}"])
table(rows,[155,107,107,138])
p('Twelve fixed primary cases: the reviewer receives the other model\'s proposal and the same images. Compare against that opponent baseline. Mismatches include unresolved assertions. Structured report-assertion checking does not adjudicate all narrative errors.','small')
p('One Sol review received an additional image-handoff paragraph during live workflow configuration. Its observed result remains in this descriptive table without retry; exact-prompt subset totals and the deviation are published separately. All direct primary reader prompts retain identical frozen instructions.','small')
page();title('Operational evidence','Efficiency measured honestly')
rows=[['Model','Technically valid reads','Median / p90 completion','Input / output tokens']]
for x in S['operational_summary']:rows.append([short(x['model']),f"{x['qualified']}/{x['primary_assigned']}",f"{x['median_seconds']:.1f}s / {x['p90_seconds']:.1f}s",f"{x['input_tokens']:,} / {x['output_tokens']:,}"])
table(rows,[90,121,148,148])
p('Completion latency includes native orchestration, throttling, multiple image groups and final answer generation, excluding global reader-slot queueing and earlier upload failures. Token counts are native provider usage, including cumulative conversational input; cached input is separately recorded. No direct dollar price or measured doctor time saving is available.','small')
p('Infrastructure failures are separate from diagnostic misses: '+ '; '.join(short(x['model'])+': '+str(x['pre_inference_transport_recoveries'])+' primary upload recoveries' for x in S['operational_summary'])+'. Original HTTP 507 outcomes remain published. The native attachment accounting cache was refreshed by restarting only the idle isolated server. Only zero-request upload failures were recovered; no model diagnosis was rerun or replaced. Completion latencies describe the eventual read, not the earlier failed-upload overhead.','small')
controls=E['context_controls'];repeats=E['repeats']
table([['Integrity / stability check','Observed'],['Context-only controls',f"{sum(x['abstention'] is True for x in controls)}/{len(controls)} abstained; {sum((x['delivered_images'] or 0) for x in controls)} delivered images."],['Fresh conversation repeats',f"{sum(x['exact_state_agreement'] for x in repeats)}/{len(repeats)} exact structured finding-state repeats across four cases per model."],['Identity and evidence checks','Requested provider IDs, actual native trace IDs, image count/dimensions/hashes, no prior-conversation recall markers, zero image-reader tool calls.'],['Reference separation','Root-protected gold/source text; no source titles, diagnostic figure captions or published final diagnoses. Legitimate pre-imaging history is supplied; public cases may still be in pretraining.']],[190,317])
p('Controls explicitly ask for abstention without images. They verify no invented visual certainty under that policy; they cannot isolate causal image benefit. Weight versions are not independently exposed by the provider. Native Ask mode records workspace-write with network disabled; file/web/skill/tool discovery is disabled for the isolated readers, and actual traces are audited.','small')
p('Workflow efficiency remains a next measured outcome','h')
p('Case preparation, draft structuring and checking can shift work to the assistant, but this experiment did not time radiologists or compare final patient outcomes. No hours-saved, workload-reduction or clinical approval claim is made.')
page();title('Live assistant configuration','Native OpenMausBot, six focused roles')
rows=[['Role','Model / effort','Responsibility']]
for role,x in json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text())['roles'].items():rows.append([x['name'],x['model']['model']+' / '+x['model']['effort'],esc(x['description'])])
table(rows,[115,157,235])
p('Native settings updated and read back','h')
p('Standing instructions, identities, operating memory and three enabled native skills cover case workup, imaging reads and report review. Automatic case-memory upkeep and cross-conversation recall are disabled. Existing hospital addresses, permissions, peer relationships and historical conversations remain in place.')
p('Doctor workflow','h')
p('Provide or open the correct current case; request preparation, provisional interpretation and a draft. The assistant states image coverage, findings, urgent suspicions, uncertainty and missing evidence. The radiologist reviews images and proposed text, then saves, signs or releases in the authorized doctor session.')
p('Portable setup boundary','h')
p('The native v1 backup contains sanitized identities, standing guidance and operating memory with empty case threads. Models, enabled skills, approval settings and browser/desktop connections are not exported by that format; repository operator scripts and skills install them explicitly. Native workflow receipts distinguish settings verification from observed handoffs.','small')
workflow=json.loads((ROOT/'docs/evidence/frontier-v2/native-handoff-rehearsal.json').read_text())
assert workflow['status']=='passed'
p('Observed native handoff rehearsal','h')
p(f"Five actual specialist handoffs returned in {workflow['seconds']/60:.1f} minutes for a public two-view CXR case. Both Image Assistant and Report Check received the two owned image tags, with source hashes verified. All procedures were supplied inside standing prompts. This qualitative integration check is separate from diagnosis metrics and physician time savings. The first rehearsal exceeded its 900-second observer window; Report Draft's reused pair thread retained medium effort during the fresh rehearsal, then its setting was corrected without replacing the observed output.",'small')
page();title('Decision and reproducibility','What to use now and what to validate next')
table([['Decision','Reason'],['Use both as supervised assistants','Automate read-only case preparation, draft structure, evidence-linked provisional findings and independent checks. Human review remains the release gate.'],['Retain Sol for coordination/drafting; Astra for image read/check','A practical role split, not proof of superior diagnostic performance. Task-specific measured results take priority over model prestige.'],['Do not promise comprehensive autonomous diagnosis','Incomplete study inputs, misses, unresolved findings and sparse references leave important reliability gaps.'],['Expand only with the right evidence','Full series/frames, modality-specific reference assertions, held-out negatives, localization where available and actual clinician workflow timing.']],[180,327])
p('Reproducible data and methods','h')
p('benchmark/runs/20261001-frontier-v2 contains frozen protocols, preparation/runner/scoring scripts, derived per-case tables, operational measurements and source provenance. Gold reports, licensed source images, account files and raw native transcripts remain private. Earlier benchmark artifacts are preserved.')
p('Primary source families','h')
for label,url in [('OpenI physician-report chest radiographs','https://openi.nlm.nih.gov/'),('CT-RATE released chest CT/report dataset','https://huggingface.co/datasets/ibrahimhamamci/CT-RATE'),('MR-RATE released MRI/report dataset','https://huggingface.co/datasets/ibrahimhamamci/MR-RATE'),('PubMed Central clinician case reports / exact per-case links in source-provenance.json','https://pmc.ncbi.nlm.nih.gov/')]:p('<link href="'+url+'" color="#007F82">'+label+'</link>','small')
p('The companion frontier research report summarizes external hospital trials and published direct-model experiments. External results are not substituted for these measured model runs. Exploratory retrospective concordance cannot authorize a hospital deployment.','small')
def footer(canvas,doc):
 canvas.setFillColor(teal);canvas.rect(0,835,596,7,fill=1,stroke=0);canvas.setFillColor(navy);canvas.setFont('LatoB',7.5);canvas.drawString(44,26,'RADIOLOGY / MEASURED FRONTIER EVALUATION | 01 OCT 2026');canvas.drawRightString(551,26,f'{doc.page:02d}')
OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),rightMargin=44,leftMargin=44,topMargin=45,bottomMargin=48,title='Frontier Radiology Model Evaluation',author='Radiology research workspace').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
