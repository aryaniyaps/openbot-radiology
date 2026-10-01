#!/usr/bin/env python3
"""Build the source-linked frontier radiology executive brief; no inference."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/Radiology-Frontier-Research-Executive-Report.pdf'
for name, font in [('Lato','Lato-Regular.ttf'),('LatoB','Lato-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, '/usr/share/fonts/truetype/lato/'+font))
pdfmetrics.registerFontFamily('Lato', normal='Lato', bold='LatoB', italic='Lato', boldItalic='LatoB')
navy, teal, ink = [colors.HexColor(c) for c in ['#152C42','#007F82','#263C4D']]
styles = {
    'title': ParagraphStyle('title',fontName='LatoB',fontSize=25,leading=29,textColor=navy,spaceAfter=16),
    'h': ParagraphStyle('h',fontName='LatoB',fontSize=13,leading=17,textColor=teal,spaceBefore=15,spaceAfter=8),
    'body': ParagraphStyle('body',fontName='Lato',fontSize=10.5,leading=15,textColor=ink,spaceAfter=10),
    'small': ParagraphStyle('small',fontName='Lato',fontSize=9,leading=12.5,textColor=ink,spaceAfter=8),
    'cell': ParagraphStyle('cell',fontName='Lato',fontSize=9,leading=12,textColor=ink),
}
story=[]
def p(s,kind='body'): story.append(Paragraph(s,styles[kind]))
def title(kicker,heading):
    p(kicker.upper(),'h');p(heading,'title')
def page(): story.append(PageBreak())
def table(rows,widths):
    t=Table([[Paragraph(c,styles['cell']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDEBED')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#DAE3E8'))]))
    story.append(t);story.append(Spacer(1,12))
def link(label,url):return '<link href="'+url+'" color="#007F82">'+label+'</link>'

title('Executive decision / 01 October 2026','Direct frontier models<br/>in radiology')
p('<b>Yes, credible successes exist.</b> Direct GPT and Gemini have solved bounded radiology tasks. The most encouraging results use carefully selected images or established findings; the evidence is much weaker for searching a full examination and safely reporting everything.')
table([['<b>Evidence</b>','<b>What it actually establishes</b>'],['GPT-4o: 37/45 abdominal CT diagnoses correct (82.2%) [1]','Representative slices plus clinical context; not independent whole-scan discovery.'],['Gemini 3 Pro Preview: 90.0% external CBCT accuracy [2]','One selected image, one narrow abnormality; 70 balanced external cases.'],['GPT-5: top-five diagnosis 24.7% to 59.1% [3]','Replacing images with radiologist descriptions improves reasoning; not improved pixel detection.']],[220,287])
p('Recommended decision','h')
p('<b>Keep direct frontier inference as the primary research arm.</b> Test a current GPT and Gemini on one report-supported task, using native image APIs and explicit scan coverage. Include Claude if the comparison can meaningfully test a different operating point. Choose by held-out task performance, rather than a universal model ranking.')
p('Evidence boundary','h')
p('This is an exhaustive targeted synthesis, not a registered systematic review or a new clinical benchmark. The supporting package indexes 95 distinct source URLs; multiple URLs can refer to one study. No new patient-care inference, training or clinician recruitment was performed. Earlier benchmark results remain unchanged.','small')
page()
title('Direct interpretation','Successes and failures coexist')
p('Good input can make a large difference','h')
p('The 45-case abdominal CT study supplied four to seven expert-selected, windowed JPEGs plus clinical information. GPT-4o matched the numerical range of six residents. Its separate image-only findings task had 75% unsupported listed findings. Correct diagnoses and unreliable supporting observations can coexist. [1]')
p('In the CBCT study, radiologists selected the affected side or most conspicuous lesion. Gemini achieved external sensitivity 85.71% and specificity 94.29%. Excluding artifacts and selecting relevant anatomy limits transfer to routine whole examinations. [2]')
p('Large visual evaluations expose serious misses','h')
table([['<b>Study</b>','<b>Measured result</b>'],['10,675 pneumothorax radiographs [4]','Sensitivity: GPT-4o 17%, Claude 4 Sonnet 23%, Gemini 2 Pro 22%; specificity 92-95%.'],['4,500 CheXpert cohort entries [5]','GPT-5.4 edema sensitivity 4.3%, specificity 99.7%, despite AUROC 0.836. A good ranking metric does not guarantee a useful binary decision.'],['ABRA real DICOM viewer [6]','Real annotation tasks: 0-25% outcome accuracy versus 69-100% with oracle annotations. Tool execution often succeeded while localization failed.']],[210,297])
p('Implication','h')
p('Measure finding discovery, localization and final diagnosis separately. A model can navigate a viewer, generate a plausible explanation or answer a teaching case without reliably finding a small lesion. Positive selected-image studies justify experiments; they do not erase the negative evidence.')
page()
title('Techniques','What is worth testing directly')
table([['<b>Technique</b>','<b>Evidence and decision</b>'],['Native image resolution','Official APIs support explicit resolution controls. Preserve small details and document resizing. No collected study establishes that the latest settings solve radiology. [9-11]'],['Complete slice/frame coverage','Use labeled series, windows and slice positions. Gemini video defaults to 1 FPS; video can omit clinically important slices unless sampling is controlled. Video superiority over still images remains unproven. [10]'],['Structured anatomical checklist','Promising in narrow CBCT classification, but not separately randomized against a simpler prompt. Test it as an explicit arm. [2]'],['More sequences or annotations','Not automatically beneficial. Gemini 3.1 MRI T1+T2 increased sensitivity 0.58 to 0.77, but specificity fell 0.74 to 0.51 and accuracy 0.70 to 0.58. [7]'],['Longer reasoning / role prompts','No consistent evidence that longer thinking repairs missed visual findings. Role-play in one prompt is not an independently validated multi-agent system.'],['Findings-first reasoning','Strongest recurring frontier strength. GPT-5 top-five thoracic diagnosis improved with human descriptions. Keep this separate from autonomous image interpretation. [3]']],[155,352])
p('Practical model shortlist','h')
p('<b>GPT:</b> first direct still-image arm with native resolution. <b>Gemini:</b> paired still-image and controlled video/volume arm. <b>Claude:</b> comparator with explicit resolution and crop handling. These are proposed experimental roles, not a clinically validated ranking. Exact snapshots and input settings must be recorded. Existing Codex access does not establish direct API access or billing.')
page()
title('Report-grounded design','A decisive next study without new doctors')
p('1. Freeze one task and the reference set','h')
p('Use existing doctors\' reports with explicit positive or negative assertions. Split by patient. Exclude or flag internal report conflicts before viewing model answers. Do not infer absence from silence, relabel cases post hoc or treat a report as exhaustive image truth.')
p('2. Keep privileged inputs separate','h')
p('Arm A: direct interpretation with controlled full coverage and clinically available context. Arm B: selected-image interpretation, labeled as such. Arm C: reasoning from existing findings, without the impression or diagnosis. Expert-selected slices and findings are different inputs and should have different claims.')
p('3. Compare inputs, not just prompts','h')
p('Freeze model snapshots, image detail, windows, slice/frame count, anatomical checklist and decision threshold after development. Compare input variants on the same held-out patients. Verify actual delivered resolution and coverage. Repeat a subset to estimate stability.')
p('4. Report misses and false alarms','h')
p('Primary results: sensitivity and specificity with confidence intervals, localization when an existing spatial reference is available, abstentions and technical failures. Report unsupported findings, latency and actual cost. Keep unresolvable cases visible. Predefine pass criteria for the intended role; do not adopt a cutoff merely because it looks good afterward.')
p('5. Test whether images matter','h')
p('Use context-only controls and valid opposite-label image swaps. Hide the gold report from the visual arm. Check whether predictions depend on the pixels rather than a diagnostic clue in context. Answer-revealing feedback belongs to development, never the held-out test.')
p('Hospital distinction','h')
p('A positive retrospective result supports a bounded next evaluation. Actual clinical deployment still requires a defined workflow, applicable authorization, institutional governance and role-specific validation. Existing-report testing cannot certify autonomous care.')
page()
title('Clinical comparators / sources','What has worked in hospitals')
p('The strongest workflow evidence comes from specialized systems','h')
p('MASAI mammography screening increased cancer detection from 5.0 to 6.4 per 1,000 and reduced screen-reading workload 44.2%, while retaining human readers. Its later interval-cancer result met noninferiority, not superiority. This proves that a carefully bounded AI workflow can work; it does not validate consumer GPT/Gemini/Claude as autonomous radiologists. [8]')
p('The full report also covers AI-assisted CXR nodule detection, stroke triage, domain-trained report drafting and negative clinical trials. Narrow FDA device records describe specific triage indications; U.S. clearance does not establish authorization in India. Avoid extrapolating device performance to another model or task.','small')
p('Selected primary and official references','h')
sources=[('1. GPT-4o emergency abdominal CT','https://www.mdpi.com/2379-139X/11/10/108'),('2. Gemini CBCT classification','https://pmc.ncbi.nlm.nih.gov/articles/PMC13499149/'),('3. Thoracic perception versus reasoning','https://snu.elsevierpure.com/en/publications/decoupling-visual-parsing-and-diagnostic-reasoning-for-vision-lan/'),('4. Large pneumothorax evaluation','https://pmc.ncbi.nlm.nih.gov/articles/PMC13530647/'),('5. CheXpert operating-point evaluation','https://pmc.ncbi.nlm.nih.gov/articles/PMC13361219/'),('6. ABRA DICOM viewer benchmark (preprint)','https://arxiv.org/abs/2605.11224'),('7. Gemini lumbar MRI sequence comparison','https://doi.org/10.1007/s00586-026-10285-9'),('8. MASAI screening analysis','https://www.sciencedirect.com/science/article/pii/S258975002400267X'),('9. OpenAI image detail documentation','https://developers.openai.com/api/docs/guides/images-vision'),('10. Gemini video documentation','https://ai.google.dev/gemini-api/docs/video-understanding'),('11. Claude vision documentation','https://platform.claude.com/docs/en/build-with-claude/vision')]
for label,url in sources:p(link(label,url),'small')
p('Full evidence package','h')
p('docs/research/RADIOLOGY-FRONTIER-DEEP-RESEARCH.md contains the detailed synthesis, study-level caveats, citations and proposed protocol. Its linked evidence matrix and source index retain the broader collection. Published benchmark artifacts are unchanged.','small')

def footer(canvas,doc):
    canvas.setFillColor(teal);canvas.rect(0,835,596,7,stroke=0,fill=1)
    canvas.setFillColor(navy);canvas.setFont('LatoB',7.5)
    canvas.drawString(44,26,'RADIOLOGY / FRONTIER RESEARCH  |  01 OCT 2026')
    canvas.drawRightString(551,26,f'{doc.page:02d} / 05')
OUT.parent.mkdir(parents=True,exist_ok=True)
SimpleDocTemplate(str(OUT),pagesize=(595.276,841.89),rightMargin=44,leftMargin=44,topMargin=45,bottomMargin=48,title='Direct Frontier Models in Radiology - Executive Research',author='Radiology research workspace').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
