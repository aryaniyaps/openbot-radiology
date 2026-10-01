#!/usr/bin/env python3
"""Executive report from actual local deployment receipts, not inferred readiness."""
import json,pathlib
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
ROOT=pathlib.Path(__file__).resolve().parents[2];E=ROOT/'docs/evidence/hospital-deployment'
def data(name):return json.loads((E/name).read_text())
def main():
    save=data('doctor-save-reopen.json');recovery=data('it-recovery.json');backup=data('it-backup-restore.json');trial=data('doctor-packet-rehearsal.json');access=data('access-checks.json')
    assert all(x['status']=='passed' for x in [save,recovery,access])
    pdfmetrics.registerFont(TTFont('Lato','/usr/share/fonts/truetype/lato/Lato-Regular.ttf'));pdfmetrics.registerFont(TTFont('LatoB','/usr/share/fonts/truetype/lato/Lato-Bold.ttf'))
    navy=colors.HexColor('#142f44');teal=colors.HexColor('#07828a');muted=colors.HexColor('#5e7180');pale=colors.HexColor('#edf5f6')
    styles=getSampleStyleSheet();styles.add(ParagraphStyle('bodyx',fontName='Lato',fontSize=10,leading=15,textColor=navy,spaceAfter=10));styles.add(ParagraphStyle('titlex',fontName='LatoB',fontSize=29,leading=34,textColor=navy,spaceAfter=14));styles.add(ParagraphStyle('hx',fontName='LatoB',fontSize=15,leading=20,textColor=teal,spaceBefore=12,spaceAfter=8));styles.add(ParagraphStyle('smallx',fontName='Lato',fontSize=8,leading=11,textColor=muted,spaceAfter=8))
    story=[]
    def p(text,style='bodyx'):story.append(Paragraph(text,styles[style]))
    def title(kicker,text):p(kicker.upper(),'smallx');p(text,'titlex')
    def table(rows,widths):
        cells=[[Paragraph(str(v),styles['smallx']) for v in row] for row in rows];t=Table(cells,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),pale),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#dce6e9')),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t)
    title('Executive deployment brief | 1 October 2026','A working doctor workflow\nwith separate IT ownership')
    p('The local practice deployment is operational: a separate IT server manages access and native configuration; the doctor client opens matching records and full supplied images, starts a real Sol/Astra case handoff, and leaves report saving to the physician-role interface.')
    table([['Outcome','Observed evidence'],['Separate IT guest','kauvery-it: 2 vCPU, 2 GiB RAM, 10 GiB virtual disk; persistent and autostart enabled'],['Hospital archive',str(recovery['study_count'])+' studies / '+str(recovery['instance_count'])+' instances after five new practice cases'],['Native models','gpt-6.1-sol: coordination, preparation and drafting. gpt-6-astra: image interpretation and independent checking.'],['Doctor boundary',str(len(access['checks']))+' live HTTPS access checks passed; configuration and permanent approvals remain IT controlled.'],['Persistence','Native physician-role note save/reload passed. IT guest reboot, telemetry persistence and encrypted backup restore passed.']],[150,357])
    p('Decision: suitable for supervised local workflow practice','hx')
    p('Keep clinician review mandatory. This evidence does not qualify the system for live patient deployment, autonomous diagnosis, electronic signing/release, individual SSO or patient-isolated history.')
    p('Doctor: https://doctor.radiology.demo/worklist/<br/>IT: https://it.radiology.demo/operations/<br/>Private logins: .private/HOSPITAL-DEMO-ACCESS.txt','smallx')
    story.append(PageBreak());title('Doctor experience and image coverage','Five modalities, explicit limits')
    table([['Case / accession','Native supplied study','Assistant display packet'],['PRACTICE001 / ORD-22 | DX','1 AP chest image','1 rendered frontal view'],['PRACTICE002 / ORD-23 | CT','241 source instances','16 axial positions, lung and mediastinal windows'],['PRACTICE003 / ORD-24 | MRI','95 source instances, 3 series','16/19 T2, 16/19 ADC, 16/57 DWI instances'],['PRACTICE004 / ORD-25 | US','1 object, 227 spatial frames','16 spatial frames; not temporal cine'],['PRACTICE005 / ORD-26 | MG','4 supplied source views','4 resized views; fine-detail limits disclosed']],[151,154,202])
    p('Actual native handoff rehearsal','hx')
    p('The attached-image chest case completed through Sol Clinical Assistant, Astra Image Assistant and Astra Report Check. Identifiers, context and coverage were supplied from read-only native integrations; both Astra roles inspected the assigned pixels. The assistant returned a provisional report and did not write the hospital record.')
    table([['Interaction measurement','GUI navigation rehearsal','Attached-image rehearsal'],['Observer one-shot reviews',str(trial['gui_comparator_review_count'])+'; early manual reviews excluded',str(trial['one_shot_review_count'])+' teammate handoffs; no navigation reviews'],['Observed elapsed interval',f"{trial['gui_elapsed_observed_seconds']/60:.1f} minutes",f"{trial['elapsed_observed_seconds']/60:.1f} minutes"]],[171,168,168])
    p('Single-case engineering comparison, with different access paths and initial GUI trust/navigation friction. These are observation intervals and approval counts, not a controlled physician-efficiency study or a diagnostic accuracy comparison. Neither workflow was professionally clinically adjudicated.','smallx')
    p('All five full supplied studies rendered visible pixels in OHIF. All 11 packet assets matched SHA256 manifests. Missing packets were refused before native submission. Sampling, source-date shifts, missing history and display limitations remain visible to the doctor.','smallx')
    story.append(PageBreak());title('Controls, recovery and first use','Verified operation; bounded claims')
    p('What passed','hx')
    p('Authenticated doctor and IT origins; doctor configuration/SOUL/execution/permanent-permission denial; native IT management; actual gateway session renewal; tunnel-loss alert and recovery; IT guest reboot with preserved native state and telemetry; encrypted IT configuration backup and exact-bundle/SQLite restore; physician-role provisional note save and matching displayed content after reload.')
    p('The hospital stayed available during the IT transport failure. TLS checks used the trusted hospital CA without certificate bypass. The IT backup restored '+str(backup['restored_samples'])+' telemetry samples with SQLite integrity verified. The on-machine backup has no external replica.','smallx')
    p('Try the deployment','hx')
    p('1. Open Radiology Assistant or the doctor worklist and use the private login handout.<br/>2. Choose PRACTICE002 / ORD-23 for a fresh CT case; verify the chart and full supplied images.<br/>3. Inspect packet coverage and choose Prepare this case. Allow the two teammate handoffs once.<br/>4. Review and edit the proposal. Expand the Bahmni order, enter Radiology Notes, Save and reload.')
    p('PRACTICE001 / ORD-22 contains the clearly labelled practice note used for save/reload verification. Four other practice cases remain unsaved. No professional clinical sign-off is implied.','smallx')
    p('Clinical evidence remains separate','hx')
    p('The existing Sol/Astra evaluation PDF reports the 106-study primary comparison, physician-report assertion measures, published-case diagnosis recognition and supplementary challenges. Workflow availability does not improve or replace those diagnostic findings. Consult Radiology-Frontier-Model-Evaluation.pdf before choosing any clinical use.')
    p('Source evidence','hx')
    p('docs/evidence/hospital-deployment/: access-checks.json; doctor-packet-rehearsal.json; doctor-modalities-ui.json; doctor-save-reopen.json; it-recovery.json; it-backup-restore.json; packet-provenance.json. Operational guide: docs/HOSPITAL-DEPLOYMENT.md. Public TCIA image attribution: config/doctor/packets/README.md. Failed attempts are retained in IMPLEMENTATION-LOG.md.','smallx')
    out=ROOT/'output/pdf/Hospital-Radiology-Deployment.pdf'
    def footer(c,doc):
        c.setStrokeColor(teal);c.line(44,36,551,36);c.setFont('Lato',8);c.setFillColor(muted);c.drawString(44,23,'SYNTHETIC PRACTICE ENVIRONMENT | Mandatory clinician review');c.drawRightString(551,23,str(doc.page))
    SimpleDocTemplate(str(out),pagesize=(595,842),rightMargin=44,leftMargin=44,topMargin=44,bottomMargin=52,title='Hospital Radiology Deployment - Executive Brief',author='Openbot Radiology').build(story,onFirstPage=footer,onLaterPages=footer)
    print(out)
if __name__=='__main__':main()
