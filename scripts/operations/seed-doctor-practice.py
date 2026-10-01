#!/usr/bin/env python3
"""Operator-only fresh HMS orders and real pixel-preserving scanner replay."""
import base64, datetime, importlib.util, json, os, pathlib, subprocess, urllib.request
ROOT=pathlib.Path(__file__).resolve().parents[2]
ORIGINAL=pathlib.Path('/home/aryan/ai-projects/openbot-radiology')
P=ROOT/'.private/hospital-it'
spec=importlib.util.spec_from_file_location('hospital',ORIGINAL/'scripts/server/configure-hospital.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)

def main():
    assert os.geteuid()==0
    file=P/'practice-state.json';state=json.loads(file.read_text()) if file.exists() else {}
    def save():file.write_text(json.dumps(state,indent=2)+'\n');file.chmod(0o600)
    outputs=[]
    case_file=ROOT/'config/doctor/cases.json'
    previous={c['patient_id']:c for c in json.loads(case_file.read_text())} if case_file.exists() else {}
    source_metadata={x['case']:x for x in json.loads((ROOT/'config/data/public-manifest.json').read_text())}
    cases=[('DX','xray-01','Dev','Shah','M'),('CT','ct-02','Arun','Kumar','M'),
        ('MR','mr-01','Vikram','Rao','M'),('US','us-01','Rahul','Mehta','M'),('MG','mg-01','Asha','Iyer','F')]
    role=h.request('encounterrole')['results'][0]['uuid']
    for index,(mod,source,given,family,gender) in enumerate(cases,1):
        key='practice-'+mod.lower();identifier=f'PRACTICE{index:03}'
        row=state.setdefault(key,{'patient_id':identifier,'modality':mod,'source_case':source,'name':given+' '+family});save()
        now=datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S.000%z')
        if 'patient' not in row:
            existing=h.request('patient?q='+identifier)['results'];assert not existing,'Unmanaged matching patient requires operator review'
            patient=h.request('patient',{'person':{'names':[{'givenName':given,'familyName':family}],'gender':gender,'age':50},'identifiers':[{'identifier':identifier,'identifierType':h.state['identifier_type'],'location':h.state['location'],'preferred':True}]})
            row['patient']=patient['uuid'];save()
        if 'visit' not in row:
            row['visit']=h.request('visit',{'patient':row['patient'],'visitType':h.state['visit_type'],'location':h.state['location'],'startDatetime':now})['uuid'];save()
        if 'encounter' not in row:
            row['encounter']=h.request('encounter',{'patient':row['patient'],'visit':row['visit'],'encounterType':h.state['consultation_type'],'encounterDatetime':now,'location':h.state['location'],'encounterProviders':[{'provider':h.state['accounts']['radiologist']['provider'],'encounterRole':role}]})['uuid'];save()
        if 'order' in row and not row.get('imaging_received'):
            old=h.request('order/'+row['order']+'?v=full')
            if old['type']=='testorder':
                # Preserve the setup mistake as a voided owned practice order.
                # Bahmni radiology uses org.openmrs.Order, not TestOrder; its
                # encounter adapter excludes the latter from the PACS feed.
                assert old['patient']['uuid']==row['patient'] and old['orderNumber']==row['accession']
                auth=base64.b64encode((h.admin['username']+':'+h.admin['password']).encode()).decode()
                q=urllib.request.Request('https://radiology.demo/openmrs/ws/rest/v1/order/'+row['order']+'?reason=Practice%20setup%20incorrect%20order%20class',method='DELETE',headers={'Authorization':'Basic '+auth})
                urllib.request.urlopen(q).close();row['voided_setup_order']={'uuid':row.pop('order'),'accession':row.pop('accession'),'reason':'Incorrect TestOrder class; no images or report created'};save()
        if 'order' not in row:
            order=h.request('order',{'type':'order','action':'NEW','patient':row['patient'],'concept':h.state['concepts'][mod],'careSetting':h.state['care_setting'],'orderer':h.state['accounts']['radiologist']['provider'],'encounter':row['encounter'],'orderType':h.state['radiology_order_type'],'urgency':'ROUTINE'})
            row.update(order=order['uuid'],accession=order['orderNumber']);save()
        if not row.get('imaging_received'):
            # Generic REST order creation alone does not emit the Bahmni
            # encounter event consumed by the native PACS integration. Save
            # that same encounter through the native application service.
            # Empty orders means no order mutation or duplicate creation.
            payload={'bahmniDiagnoses':[],'observations':[],'accessionNotes':[],
                'encounterType':'Consultation','encounterTypeUuid':h.state['consultation_type'],
                'encounterUuid':row['encounter'],'patientUuid':row['patient'],
                'patientId':identifier,'visitUuid':row['visit'],
                'visitTypeUuid':h.state['visit_type'],'locationUuid':h.state['location'],
                'orders':[],'drugOrders':[],'providers':[{'uuid':h.state['accounts']['radiologist']['provider'],
                    'encounterRoleUuid':role}],'context':{},'extensions':{}}
            h.request('bahmnicore/bahmniencounter',payload)
            data=subprocess.check_output([str(ORIGINAL/'.venv/bin/python'),str(ROOT/'scripts/server/acquire-demo.py'),row['patient'],source,key],cwd=ROOT,text=True,env={**os.environ,'HOSPITAL_PROJECT':str(ORIGINAL)})
            result=json.loads(data);assert result['patient_id']==identifier and result['accession']==row['accession'];row.update(study_uid=result['study_uid'],instances=result['instances'],imaging_received=True);save()
        output={k:row[k] for k in ['patient','patient_id','name','accession','modality','source_case','study_uid','instances']}
        output['frames']=source_metadata[source]['frames']
        output['coverage_note']='Spatial ultrasound sweep; not a temporal cine' if mod=='US' else 'Released source series; confirm coverage in the viewer'
        prior=previous.get(identifier,{})
        if all(prior.get(k)==output[k] for k in ['patient','accession','study_uid','instances']):
            for field in ['packet_views','assistant_coverage','clinical_context','assistant_limits']:
                if field in prior:output[field]=prior[field]
        outputs.append(output)
        print(mod,identifier,row['accession'],'native order and archived imaging ready')
    (ROOT/'config/doctor/cases.json').write_text(json.dumps(outputs,indent=2)+'\n')
    (ROOT/'docs/evidence/hospital-deployment/practice-cases.json').write_text(json.dumps(outputs,indent=2)+'\n')

if __name__=='__main__':main()
