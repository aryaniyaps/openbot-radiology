#!/usr/bin/env python3
"""Run a fresh public practice packet through native models, without answering approvals."""
import base64
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    account = json.loads((ROOT / '.private/doctor-client-auth.json').read_text())['doctor']
    headers = {'Authorization': 'Basic ' + base64.b64encode((account['username'] + ':' + account['password']).encode()).decode(),
               'Content-Type': 'application/json', 'Origin': 'https://doctor.radiology.demo'}
    def api(route, body=None, raw=None):
        request_headers = dict(headers)
        if raw is not None:
            request_headers['Content-Type'] = 'image/png'
        request = urllib.request.Request('https://doctor.radiology.demo' + route,
            headers=request_headers, data=raw if raw is not None else json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    bots = api('/api/bots')['bots']
    if not args.resume:
        assert not any(b.get('busy') or b.get('waitingForTeammates') for b in bots), 'Preserve current work'
    bot = next(b for b in bots if b['name'] == 'Clinical Assistant')
    case = json.loads((ROOT / 'config/doctor/cases.json').read_text())[0]
    title = case['patient_id'] + ' / ' + case['accession'] + ' · routine permission verification'
    if args.resume:
        assert next(t for t in bot['tasks'] if t['threadId'] == bot['threadId'])['title'] == title, 'Only resume the owned verification'
        task = {'task': next(t for t in bot['tasks'] if t['threadId'] == bot['threadId'])}
    else:
        task = api('/api/bots/' + bot['id'] + '/tasks', {'title': title})
    tid = task['task']['threadId']
    assert task['task']['approvalMode'] == 'auto', 'Fresh case must inherit automatic review'
    text = ('Current practice patient ' + case['patient_id'] + ', accession ' + case['accession'] + '. '
        'The read-only hospital integration verified the current patient, radiology order and imaging study. '
        'Use ONLY this summary and attached image packet. No hospital browsing is needed. '
        'Discover the actual allowed teammate IDs with list_bots. First obtain an actual Image Assistant read, '
        'then draft a provisional report and obtain an actual independent Report Check against the same images. '
        'Preserve the native attached-image markup in both briefs and end your turn after each handoff. '
        'Return one consolidated provisional report with coverage limits, uncertainty and doctor review actions. '
        'Do not save, sign, release, order, change records, contact external recipients or configure bots. '
        + case['clinical_context'] + ' Coverage: ' + case['assistant_coverage'] + '. Limits: ' + case['assistant_limits'])
    for view in ([] if args.resume else case['packet_views']):
        image = ROOT / 'config/doctor/packets' / case['patient_id'] / view['filename']
        raw = image.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == view['sha256']
        attachment = api('/api/attachments', raw=raw)
        attachment = attachment.get('attachment', attachment)
        text += '\n<attached-image path="' + attachment['path'] + '" name="' + view['filename'] + '"/>'
    if args.resume:
        owned = [m for m in bot['messages'] if m.get('role') == 'user' and m.get('text', '').startswith('Current practice patient ' + case['patient_id'])]
        assert len(owned) == 1
        started = owned[0]['at'] / 1000
    else:
        started = time.time()
        api('/api/bots/' + bot['id'] + '/messages', {'threadId': tid, 'text': text, 'sendId': str(uuid.uuid4())})
    cards = {}
    tools = {}
    progress = ROOT / '.private/routine-permission-progress.json'
    while time.time() - started < 900:
        current = api('/api/bots')['bots']
        lead = next(b for b in current if b['id'] == bot['id'])
        for b in current:
            for message in b['messages']:
                if message.get('at', 0) < started * 1000:
                    continue
                card = message.get('card') or {}
                if card.get('requestId'):
                    cards[card['requestId']] = {'role': b['name'], 'tool': card.get('tool'), 'answered': bool(card.get('answered'))}
                tool = message.get('tool') or {}
                if tool.get('name'):
                    tools[message['id']] = {'role': b['name'], 'name': tool['name'], 'ok': tool.get('ok')}
        state = {'thread_id': tid, 'seconds': round(time.time()-started, 1), 'approval_cards': list(cards.values()),
                 'tools': list(tools.values()), 'busy': bool(lead.get('busy')), 'waiting': bool(lead.get('waitingForTeammates'))}
        progress.write_text(json.dumps(state, indent=2) + '\n')
        if cards:
            print(json.dumps(state), flush=True)
            raise RuntimeError('Routine workflow requested human approval; no approval was answered')
        terminal = [m for m in lead['messages'] if m.get('at', 0) >= started*1000 and m.get('turnTerminal') and m.get('turnSucceeded')]
        if terminal and not state['busy'] and not state['waiting']:
            assert any(t['name'] == 'coordinate_bots' for t in tools.values()), 'Actual team coordination required'
            assert all(any(m.get('at', 0) >= started*1000 and m.get('digest') and m.get('turnSucceeded') for m in next(b for b in current if b['name'] == name)['messages']) for name in ['Image Assistant', 'Report Check']), 'Both Astra roles must actually finish successfully'
            state['observation_seconds'] = state['seconds']
            state['seconds'] = round(max(m['at'] for m in terminal)/1000 - started, 1)
            state.update(status='passed', case_id=case['patient_id'], accession=case['accession'], human_tool_approvals=0,
                observer_approval_responses_sent=0, models={'coordinator': lead['modelSelection'],
                **{b['name']: b['modelSelection'] for b in current if b['name'] in ['Image Assistant', 'Report Check']}},
                clinical_record_writes_requested=False, scope='One public practice-case integration check; not clinical validation')
            (ROOT / 'docs/evidence/hospital-deployment/routine-permission-rehearsal.json').write_text(json.dumps(state, indent=2)+'\n')
            print(json.dumps({'status': 'passed', 'seconds': state['seconds'], 'human_tool_approvals': 0}), flush=True)
            return
        time.sleep(2)
    raise RuntimeError('Observation window exceeded; native work and evidence preserved')


if __name__ == '__main__':
    main()
