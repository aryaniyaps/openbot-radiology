#!/usr/bin/env python3
"""Operator bootstrap via native OpenMRS REST; never used by clinical agents."""
import base64
import datetime
import json
import pathlib
import secrets
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
STATE = ROOT / '.private/server/hospital-state.json'
state = json.loads(STATE.read_text()) if STATE.exists() else {'accounts': {}, 'cases': {}, 'concepts': {}}
admin = state['accounts'].get('admin', {'username': 'admin', 'password': 'Admin123'})

def save():
    STATE.write_text(json.dumps(state, indent=2))
    STATE.chmod(0o600)

def request(path, payload=None, account=None):
    account = account or admin
    authorization = base64.b64encode((account['username'] + ':' + account['password']).encode()).decode()
    req = urllib.request.Request('https://radiology.demo/openmrs/ws/rest/v1/' + path,
                                data=json.dumps(payload).encode() if payload is not None else None,
                                headers={'Authorization': 'Basic ' + authorization, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as error:
        # Do not print request payloads, passwords or full patient responses.
        detail = json.loads(error.read()).get('error', {})
        raise RuntimeError(f'{path}: HTTP {error.code}: {detail.get("message", "request failed")}') from None

def values(resource):
    return request(resource + '?limit=1000')['results']

def named(resource, name):
    return next(v for v in values(resource) if v['display'] == name)['uuid']

def make_account(username, given, roles):
    if username in state['accounts']:
        return state['accounts'][username]
    existing = request('user?username=' + username)['results']
    if existing:
        raise RuntimeError('Existing unmanaged account: ' + username)
    person = request('person', {'names': [{'givenName': given, 'familyName': 'Demo'}], 'gender': 'M'})
    password = secrets.token_urlsafe(24) + '9aA!'
    user = request('user', {'username': username, 'password': password, 'person': person['uuid'], 'roles': roles})
    provider = request('provider', {'person': person['uuid'], 'identifier': username})
    account = {'username': username, 'password': password, 'user': user['uuid'], 'person': person['uuid'], 'provider': provider['uuid']}
    state['accounts'][username] = account
    save()
    return account

if __name__ == '__main__':
    # Bahmni requires a provider identity even for read-only application users.
    if not request('provider?user=82f18b44-6814-11e8-923f-e9a88dcb533f')['results']:
        request('provider', {'person': '5f87c042-6814-11e8-923f-e9a88dcb533f', 'identifier': 'demo-operator'})
    roles = {v['display']: v['uuid'] for v in values('role')}
    readonly = [roles['Clinical-App-Read-Only'], roles['Registration-App-Read-Only']]
    doctor = make_account('radiologist', 'Radiologist', [roles['Clinical-App'], roles['Registration-App'], roles['OrderFulfillment-App']])
    for name in ['clinical', 'workflow', 'reportcheck', 'reportdraft', 'image', 'caseprep']:
        make_account('assistant_' + name, name.title(), readonly)
    make_account('pacs_service', 'PACS Integration', readonly)
    sources = values('conceptsource')
    source = next((s['uuid'] for s in sources if s['display'] == 'PACS Procedure Code'), None)
    if not source:
        source = request('conceptsource', {'name': 'PACS Procedure Code', 'description': 'Local demonstration procedure codes'})['uuid']
    for modality, label in [('DX', 'Demo chest X-ray'), ('CT', 'Demo chest CT'), ('MR', 'Demo prostate MRI'), ('US', 'Demo prostate ultrasound'), ('MG', 'Demo bilateral mammography')]:
        if modality in state['concepts']:
            continue
        term = request('conceptreferenceterm', {'code': modality, 'name': label, 'conceptSource': source})
        concept = request('concept', {'names': [{'name': label, 'locale': 'en', 'localePreferred': True, 'conceptNameType': 'FULLY_SPECIFIED'}],
                                     'datatype': named('conceptdatatype', 'N/A'), 'conceptClass': named('conceptclass', 'Radiology'),
                                     'set': False, 'mappings': [{'conceptReferenceTerm': term['uuid'], 'conceptMapType': named('conceptmaptype', 'SAME-AS')}]})
        state['concepts'][modality] = concept['uuid']
        save()
    # Only five procedures are shown in this scoped demo configuration.
    request('concept/05d53977-443c-4883-a1f8-ea265fdaaf39', {'setMembers': list(state['concepts'].values())})
    location = named('location', 'Bahmni Hospital')
    state['location'] = location
    state['radiology_order_type'] = named('ordertype', 'Radiology Order')
    state['consultation_type'] = named('encountertype', 'Consultation')
    state['visit_type'] = named('visittype', 'OPD')
    state['identifier_type'] = named('patientidentifiertype', 'Patient Identifier')
    state['care_setting'] = named('caresetting', 'Outpatient')
    cases = json.loads((ROOT / '.private/dicom/source-manifest.json').read_text())
    for index, case in enumerate(cases, 1):
        key = case['case']
        if key in state['cases']:
            continue
        existing = request('patient?q=' + f'DEMO-{index:03}')['results']
        patient = existing[0] if existing else request('patient', {'person': {'names': [{'givenName': key.upper().replace('-', ''), 'familyName': 'PublicCase'}], 'gender': 'F' if case['modality'] == 'MG' else 'M', 'age': 50},
                                      'identifiers': [{'identifier': f'DEMO-{index:03}', 'identifierType': state['identifier_type'], 'location': location, 'preferred': True}]})
        visit = request('visit', {'patient': patient['uuid'], 'visitType': state['visit_type'], 'location': location, 'startDatetime': datetime.datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S.000%z')})
        state['cases'][key] = {'patient': patient['uuid'], 'patient_id': f'DEMO-{index:03}', 'patient_name': key.upper().replace('-', '') + '^PublicCase', 'visit': visit['uuid'], 'modality': case['modality']}
        save()
    save()
    print('Configured six read-only assistants, physician, service account, five procedures and ten synthetic administrative cases.')
