#!/usr/bin/env python3
"""Render the executive brief from the retained, audited benchmark artifacts.

Requires reportlab. No model calls or protected reference access are performed.
"""
import hashlib
import json
import math
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'benchmark/runs/20260930T1418Z-graysby'
OUT = ROOT / 'output/pdf/Imaging-Benchmark-Executive-Report.pdf'
OPS = json.loads((RUN / 'report/operational-metrics.json').read_text())
TASKS = json.loads((RUN / 'report/task-metrics.json').read_text())
FINAL = json.loads((RUN / 'report/final-acceptance.json').read_text())
CONTROLS = json.loads((RUN / 'report/self-review-controlled-comparisons.json').read_text())
assert FINAL['passed']
assert len(CONTROLS['records']) == 72
assert FINAL['assignment_status_counts']['completed'] + FINAL['assignment_status_counts']['abstained'] == 919
estimable = [r for r in CONTROLS['records'] if r['paired_patients'] > 0]
assert len(estimable) == 66
assert sum(r['b_minus_a'] != 0 for r in estimable) == 1
for line in (RUN / 'delivery-checksums.sha256').read_text().splitlines():
    sha, file = line.split('  ', 1)
    assert hashlib.sha256((RUN / file).read_bytes()).hexdigest() == sha, file

FONT = Path('/usr/share/fonts/truetype/lato')
for name, file in [('Lato','Lato-Regular.ttf'),('LatoB','Lato-Bold.ttf'),('LatoI','Lato-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT / file)))
pdfmetrics.registerFontFamily('Lato', normal='Lato', bold='LatoB', italic='LatoI', boldItalic='LatoB')
NAVY = colors.HexColor('#152C42')
TEAL = colors.HexColor('#007F82')
GOLD = colors.HexColor('#BC8430')
RED = colors.HexColor('#A64441')
INK = colors.HexColor('#263C4D')
MUTED = colors.HexColor('#607281')
PALE = colors.HexColor('#EEF4F5')
LINE = colors.HexColor('#DAE3E8')
WHITE = colors.white
W, H = 595.276, 841.89
M, CW = 44, W-88
OUT.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUT), pagesize=(W,H), pageCompression=1)
c.setTitle('Imaging Benchmark | Executive Decision Report')
c.setAuthor('Radiology research workspace')
c.setSubject('Audited imaging workflow evidence and research decisions, 1 October 2026')
page_number = 0

def para(text, x, y, width=CW, size=11, color=INK, font='Lato', leading=None):
    """Draw using top coordinates and reject overflow into the footer."""
    p = Paragraph(text, ParagraphStyle('body',fontName=font,fontSize=size,
        leading=leading or size*1.42,textColor=color,alignment=TA_LEFT))
    _, height = p.wrap(width,H)
    assert y+height < H-57, (page_number,text[:80],y,height)
    p.drawOn(c,x,H-y-height)
    return y+height

def text(s,x,y,size=11,font='Lato',color=INK):
    c.setFillColor(color);c.setFont(font,size);c.drawString(x,H-y,s)

def rect(x,y,w,h,fill,radius=0):
    c.setFillColor(fill);c.setStrokeColor(fill)
    c.roundRect(x,H-y-h,w,h,radius,stroke=0,fill=1)

def page(kicker,title,sub):
    global page_number
    if page_number:c.showPage()
    page_number+=1
    rect(0,0,W,7,TEAL)
    text('RADIOLOGY / RESEARCH INTELLIGENCE',M,34,8,'LatoB',TEAL)
    text('01 OCT 2026',W-M-69,34,8,'LatoB',MUTED)
    text(kicker.upper(),M,80,9,'LatoB',TEAL)
    para(title.replace('\n','<br/>'),M,94,size=27,font='LatoB',color=NAVY,leading=30)
    para(sub,M,164,size=10.5,color=MUTED)
    c.setStrokeColor(LINE);c.line(M,46,W-M,46)
    text('IMAGING BENCHMARK  |  EXECUTIVE REPORT',M,H-31,7.5,'LatoB',MUTED)
    text(f'{page_number:02d} / 07',W-M-33,H-31,8,'LatoB',TEAL)

def section(label,y):
    text(label.upper(),M,y,9,'LatoB',TEAL)

def box(title,body,y,height=100,color=TEAL):
    rect(M,y,CW,height,PALE,8);rect(M,y,4,height,color)
    end=para(title,M+17,y+13,CW-34,size=12 if height<100 else 13,font='LatoB',color=NAVY)
    end=para(body,M+17,end+8,CW-34,size=9.4 if height<100 else 10.5)
    assert end <= y+height-9,(title,end,y+height)

def table(headers,rows,y,widths,font=9.2):
    sty=ParagraphStyle('cell',fontName='Lato',fontSize=font,leading=font*1.3,textColor=INK)
    hs=ParagraphStyle('head',parent=sty,fontName='LatoB',textColor=WHITE)
    data=[[Paragraph(escape(str(x)),hs) for x in headers]]
    data += [[Paragraph(str(x).replace('\n','<br/>'),sty) for x in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,PALE]),
        ('LINEBELOW',(0,-1),(-1,-1),.5,LINE)]))
    _,h=t.wrap(CW,H);assert y+h<H-60,(page_number,y,h)
    t.drawOn(c,M,H-y-h);print(f'Page {page_number} table: {y:.1f}-{y+h:.1f}');return y+h

def source(s):para(s,M,748,size=8,color=MUTED,leading=10)

MODELS=['gpt-6-astra','gpt-6-luna','gpt-6.1-sol','google/medgemma-1.5-4b-it']
SHORT=['Astra','Luna','Sol','MedGemma 4B']
COLS=[TEAL,colors.HexColor('#608FAD'),NAVY,GOLD]
def op(model,mod,stage='evaluation',arm='B'):
    return next(x for x in OPS if x['model']==model and x['modality']==mod and x['stage']==stage and x['arm']==arm and x['configuration']=='primary' and not x['attempt'])
def task(model,mod,finding):
    return next(x for x in TASKS if x['model']==model and x['modality']==mod and x['stage']=='evaluation' and x['arm']=='B' and x['configuration']=='primary' and x['task']==finding and not x['attempt'])
def wilson(k,n):
    z=1.95996398454;p=k/n;d=1+z*z/n;a=(p+z*z/(2*n))/d;b=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return max(0,a-b),min(1,a+b)

# 1 - decision first.
page('01 / Executive decision','Image access works.\nClinical trust is unproven.',
     'A completed comparison of GPT imaging workflows and pinned MedGemma, using existing doctors\' reports as the reference. Research evidence; no live clinician adjudication.')
for i,(value,label) in enumerate([('970','Frozen assignments closed'),('919','Qualified outcomes'),('120','Main imaging studies')]):
    x=M+i*(CW+12)/3;w=(CW-24)/3
    rect(x,225,w,87,PALE,7);text(value,x+13,266,31,'LatoB',NAVY);para(label,x+13,279,w-26,size=9,color=MUTED)
box('Recommendation: retain research engineering; hold clinical deployment',
    'Successful image delivery and structured answers establish technical feasibility. Poor report-positive finding resolution, input limitations and small reference counts do not support autonomous patient-care use or radiologist equivalence.',333,113,color=RED)
section('Decisions supported by the evidence',476)
table(['Decision','Basis'],[
    ['<b>Continue a bounded research workflow</b>','All three GPTs captured qualified direct responses on 120/120 main studies. Identity and input audits remain essential.'],
    ['<b>Hold the tested diagnostic workflows</b>','Pneumothorax resolution: 0-1 of 10 positives. CT nodule resolution: 0-3 of 19 positives.'],
    ['<b>Do not add a specialist by default</b>','MedGemma consultation has no established general benefit versus self-review, with additional diagnostic components.'],
    ['<b>Investigate a narrow MRI endpoint</b>','White-matter assertion concordance is promising in a tiny, source-conflicted sample; fresh validation is absent.'],
],491,[205,CW-205],9.5)
source('[E1-E4] Qualified outcomes measure execution, not diagnostic accuracy. Results concern these tested inputs and budgets.')

# 2 - scope and operational results.
page('02 / Study coverage','A completed study,\nwith distinct evidence tiers.',
     'Repeated runs and multiple workflow assignments are not additional independent patients. Main, development and fresh cohorts remain separate.')
table(['Evidence tier','Study count','What it supports'],[
    ['Main cohort','120','60 chest radiographs (CXR), 40 chest CT volumes, 20 MRI studies.'],
    ['Fresh cohort','30','10 per modality; Sol and MedGemma only. Not all models or role workflows.'],
    ['Development','20','Feasibility and setup checks; excluded from primary performance.'],
],219,[110,77,CW-187])
section('Qualified direct-input responses',376)
rows=[]
for model,label in zip(MODELS,SHORT):
    cells=[]
    for mod in ['CXR','CT','MR']:
        q=op(model,mod);v=q['valid_structured'];cells.append(f"{v['numerator']}/{v['denominator']}")
    rows.append([model if model.startswith('gpt-') else 'MedGemma 1.5 4B NF4']+cells)
table(['Model','CXR / 60','CT / 40','MRI / 20'],rows,391,[167,113,113,CW-393],10)
box('Completion is a prerequisite, not a diagnostic verdict',
    'The frozen engineering gate requires at least 95% qualified responses, a Wilson 95% lower bound of at least 80%, and clean identity/isolation. GPT direct workflows pass this gate in each main modality. MedGemma passes for CXR; its CT and MRI completion falls below the gate.',572,113)
para('970 assignments: 480 main direct, 120 viewer, 270 role, 40 repeat and 60 fresh. There are no pending frozen assignments. Recovery-assisted results include 198 assignments with documented pre-dispatch setup failures.',M,702,size=9.5)
source('[E1, E2] Qualified outcomes include properly structured abstentions. Setup and preprocessing are separate from inference latency.')

# 3 - vector chart from machine-readable task results.
page('03 / Finding resolution','Key report-positive findings\nwere often unresolved.',
     'Correctly resolved report-positive assertions / all explicit assigned positives. Failures and abstentions stay in the denominator. Whiskers: Wilson 95% intervals.')
for i,(label,col) in enumerate(zip(SHORT,COLS)):
    x=M+i*128;rect(x,211,7,7,col);text(label,x+12,218,9,'LatoB',INK)
for j,(mod,key,title) in enumerate([('CXR','pneumothorax','Pneumothorax / 10 positives'),('CT','pulmonary_nodule','Pulmonary nodules / 19 positives'),('MR','white_matter_signal_abnormality','White-matter signal assertions / 5 coded positives')]):
    y=253+j*136;text(title,M,y,12,'LatoB',NAVY)
    bx=M+120;bw=275
    for i,(model,label,col) in enumerate(zip(MODELS,SHORT,COLS)):
        q=task(model,mod,key);k=q['diagnostic_confusion_counts']['TP'];n=q['reference_positive'];lo,hi=wilson(k,n)
        yy=y+14+i*21
        text(label,M,yy+9,9,color=MUTED);rect(bx,yy,bw,10,PALE,3)
        if k:rect(bx,yy,bw*k/n,10,col,3)
        c.setStrokeColor(col);c.setLineWidth(1);cy=H-yy-5
        c.line(bx+bw*lo,cy,bx+bw*hi,cy)
        for xx in [lo,hi]:c.line(bx+bw*xx,cy-3,bx+bw*xx,cy+3)
        text(f'{k}/{n}',bx+bw+14,yy+9,10,'LatoB',col)
    if j==2:
        for v in [0,50,100]:text(f'{v}%',bx+bw*v/100-6,y+110,8,color=MUTED)
box('MRI is a candidate for narrower validation, not a validated ranking',
    'Two of the five coded MRI positives have normal-impression conflicts. A post hoc source-scope restriction leaves GPT concordance at 3/3 and MedGemma at 0/3. The original 5-case scores remain unchanged. No explicit target negatives support MRI specificity.',644,94,color=GOLD)
source('[E1, E3] All 10 pneumothorax and 19 nodule-positive source mappings were independently audited. Report support does not prove visibility in supplied frames.')

# 4 - role value and cost.
page('04 / Specialist value','More inference did not establish\na general specialist advantage.',
     '270 role assignments cover delegated reads, independent second-reading and self-review. The same saved MedGemma study read is reused; it is not a new physical GPU read each time.')
box('Same-case controls: 65 of 66 estimable cells show zero difference',
    'The sole nonzero cell is Luna/CXR cardiomegaly, second-reader versus self-review: +1 resolved assertion in 4 supported pairs (+25 percentage points; exploratory interval 0 to 75; exact McNemar p=1.0). Six additional cells have no reference support.',222,110)
section('Observed transitions across supported assertions',365)
table(['Condition','Comparison count','Gained / lost resolution'],[
    ['CXR / delegated','195','1 / 2'],['CXR / second-reader','195','1 / 1'],
    ['CT / delegated','42','0 / 1'],['CT / second-reader','42','0 / 0'],
    ['MRI / delegated','12','0 / 2'],['MRI / second-reader','12','0 / 1'],
],380,[166,139,CW-305],9.3)
para('These are repeated finding/model comparisons, not independent patient counts. Resolution changes include movement into or out of unresolved states. The sole completed-label reversal occurs in a source-conflicted MRI case and is not adjudicated clinical harm.',M,601,size=9.5)
box('Incremental complexity requires demonstrated value',
    'On identical Sol controls, median component sums are CT: 54.0s delegated / 82.0s second-reader / 45.0s self-review; MRI: 106.2s / 125.7s / 50.3s. These omit setup/preprocessing and are not serial wall time or dollar costs.',650,88,color=GOLD)
source('[E1, E4, E5] Exploratory controls were added during audit. Sparse zero differences establish neither benefit nor equivalence.')

# 5 - integrity / limitations.
page('05 / Evidence boundaries','Input fidelity and reference quality\nlimit what the results mean.',
     'Observed failures belong to the tested workflow. They cannot be attributed to model weights alone, or generalized to full clinical examinations.')
table(['Material limitation','Decision impact'],[
    ['<b>MedGemma montage distortion</b>','CT montages: 2048 x 1080 to 896 x 896, about 1.90x aspect change. MRI: about 1.26x. Revisit evidence delivery before judging intrinsic volumetric ability.'],
    ['<b>GPT native image transformation</b>','Audited MRI inputs: 2048 x 1620 to 1779 x 1408, approximately aspect-preserving. Delivered pixels differ from source attachment bytes.'],
    ['<b>Viewer contamination and sparse coverage</b>','18 viewer reads had prior conversation context. Both sides of these pairs are excluded. A clean CT trace inspected 9 distinct slices out of 247 frames.'],
    ['<b>Existing reports, no new clinical review</b>','Assertion concordance is measured. Translation, narrow coding, conflicts and unknown public training exposure limit interpretation. Error severity is unadjudicated.'],
    ['<b>Missing comparative evidence</b>','Historical GPT controls, MedGemma 27B, broad modality coverage and limited differential diagnosis were not tested. No validated overall model ranking.'],
],219,[160,CW-160],10)
section('Repeatability is separate from correctness',553)
para('Identical finding-status objects: Astra 7/10 repeat pairs, Luna 7/10, Sol 6/10. MedGemma is identical in 8/8 pairs with two qualified responses; 2/10 pairs lack two qualified responses. Repeated agreement does not turn an incorrect finding into a correct one.',M,567,size=10)
box('Fresh studies do not rescue the main diagnostic claim',
    'Fresh CXR cardiomegaly: Sol 1/5, MedGemma 3/5. The sole CT nodule positive is unresolved by both. The narrow primary MRI white-matter endpoint has no coded fresh positives; known omitted clauses remain unscored. No retrospective relabeling was used.',640,94,color=GOLD)
source('[E1, E3, E6] Fresh completion: Sol 10/10 in each modality; MedGemma CXR 10/10, CT 6/10, MRI 7/10. These are execution measures.')

# 6 - recommended action plan.
page('06 / Action agenda','Make the next study narrower,\ncleaner and decision-specific.',
     'Recommended sequence for future authorized research. These steps have not been executed as additional benchmark conditions.')
table(['Priority','Action','Acceptance evidence'],[
    ['<b>1 / Retain</b>','Keep isolated attachment and viewer engineering with explicit response and identity checks.','Trace audit passes; setup reliability is reported separately from response capture.'],
    ['<b>2 / Repair evidence delivery</b>','Preserve montage geometry; inspect native delivered pixels and anatomical coverage.','Known source-to-model transformations; representative lesions fall within delivered evidence.'],
    ['<b>3 / Tighten existing-report references</b>','Reconcile original-language clauses, translation and normal-impression conflicts. Use explicit positive and negative assertions.','Versioned reference rules; conflicts excluded prospectively; no live-doctor dependency introduced.'],
    ['<b>4 / Preregister one narrow endpoint</b>','Choose a finding and input method; use institution-separated cases and a paired self-review control.','Prespecified denominators, missing-outcome handling, intervals and precision target.'],
    ['<b>5 / Decide specialist value</b>','Add consultation only if matched controls demonstrate useful benefit with measured incremental resources.','Benefit supported beyond sparse observations; full workflow components accounted for.'],
],220,[85,207,CW-292],9.7)
box('Planning guidance, not a clinical safety guarantee',
    'Approximately 385 independent positives and 385 negatives per task give a worst-case normal-approximation 95% margin near +/-5 percentage points. Zero misses in 59 independent positives gives a one-sided exact 95% upper miss-rate bound below 5%. Reference quality and independence still matter.',632,99)
source('[E1, E7] Patient-care deployment remains on hold under the current evidence. Hardware, subscription-dollar allocation and whole-lifecycle ROI are unmeasured.')

# 7 - economics, definitions, evidence index.
page('07 / Accountability & sources','Traceable results.\nExplicit accounting boundaries.',
     'Evidence completed 1 October 2026. Original diagnostic outputs and frozen scores were preserved; no new inference was used to create this report.')
table(['Measured resource','Observed amount','Boundary'],[
    ['GPT diagnostic usage','66,584,015 input tokens\n405,317 output tokens','Includes development and native-only receipts; excludes curation/orchestration. Cached input is a subset.'],
    ['Local MedGemma','172 timed serving records\n6,226.7 inference seconds','Includes development; 160 frozen physical study reads. Plus 19 pre-inference guards and 3 records without duration.'],
    ['Account actions','One authorized free reset\nNo purchases or upgrades','Shared compute and quota; no dollar/energy estimate or equivalence claim.'],
    ['Conversation accounting','1,002 observed\n970 frozen assignments','31 development + 970 frozen + 1 auxiliary. Original 1,000 cap corrected prospectively; no new study condition.'],
],218,[130,145,CW-275],9.2)
section('How to interpret the numbers',478)
para('<b>Qualified outcome:</b> a terminal response meeting engineering validity checks, including structured abstention. <b>Finding resolution:</b> a correct explicit report-supported label under the assigned workflow; unresolved cases remain in the denominator. <b>Intervals:</b> Wilson 95% for fractions; paired comparisons are exploratory and not multiplicity-adjusted. Global patient independence is not fully certified.',M,492,size=9.6)
section('Evidence index',573)
base='https://github.com/aryaniyaps/openbot-radiology/blob/a6b126bc4c032bcc3dcd38f154010b69537b2ebb/benchmark/runs/20260930T1418Z-graysby/'
refs=[('E1','Decision report and complete technical appendix','DECISION-REPORT.md'),
      ('E2','Execution metrics and final acceptance','report/operational-metrics.json'),
      ('E3','Task-specific counts, intervals and missing-outcome bounds','report/task-metrics.json'),
      ('E4','Identical-control comparisons and specialist transitions','report/self-review-controlled-comparisons.json'),
      ('E5','Role timing and component cost attribution','report/role-cost-attribution.json'),
      ('E6','Independent source, arithmetic and native-boundary audit','report/audit-delivery-summary.json'),
      ('E7','Statistical methods, provenance and requirements audit','research/statistical-methods.md')]
y=587
for code,label,path in refs:
    y=para(f'<b>{code}</b>  <link href="{base+path}" color="#007F82">{label}</link>',M,y,size=9,leading=12)+4
para('Source version: a6b126b. Full requirements and gaps: REQUIREMENT-AUDIT.md. The 90-artifact delivery-checksums.sha256 manifest verifies the retained package; this PDF is an executive synthesis. Protected reports and raw traces remain local.',M,714,size=8.2,leading=10)
source('CXR = chest radiograph. CT = computed tomography. MRI = magnetic resonance imaging. MedGemma here = pinned 1.5 4B NF4 workflow; Sol = gpt-6.1-sol.')
c.save()
print(f'Created {OUT} ({OUT.stat().st_size:,} bytes; {page_number} pages)')
