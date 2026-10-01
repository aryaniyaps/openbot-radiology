#!/usr/bin/env python3
"""Apply radiology profiles and skills through the paired native operator API."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--session', type=Path, required=True)
    p.add_argument('--url', default='http://127.0.0.1:8799')
    p.add_argument('--apply', action='store_true')
    p.add_argument('--resume', action='store_true', help='Resume after inspecting a preserved native backup')
    a = p.parse_args()
    session = json.loads(a.session.read_text())

    def api(route, method='GET', body=None):
        req = urllib.request.Request(a.url + '/api/' + route, method=method,
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + session['token']},
            data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Native API {method} {route}: {e.code}: {e.read().decode()[:300]}') from None

    guidance = json.loads((ROOT / 'config/openmausbot/role-guidance.json').read_text())
    permissions = json.loads((ROOT / 'config/openmausbot/routine-permissions.json').read_text())
    state = api('bots')
    bots = state['bots']
    roles = guidance['roles']
    selected = []
    for role, spec in roles.items():
        matches = [b for b in bots if b['name'] == spec['name']]
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one native role: ' + spec['name'])
        bot = matches[0]
        if bot.get('busy') or bot.get('waitingForTeammates') or any(t.get('busy') for t in bot.get('tasks', [])):
            raise RuntimeError('Role must be idle before update: ' + spec['name'])
        # Preserve the operator's current addresses and source-of-truth mapping,
        # while replacing the obsolete clinical prohibition in the old persona.
        installation = next((line[line.index('Hospital:'):] for line in bot.get('soul', '').splitlines()
            if 'Hospital:' in line), '')
        soul = spec['instructions'] + '\n\n' + guidance['shared']
        soul += '\n\nRoutine permission policy:\n' + permissions['instructions']
        if installation:
            soul += '\n\nOperator-configured application locations: ' + installation
        soul += '\n\nLoad the enabled role procedures: ' + ', '.join(spec['skills']) + '.'
        soul += ' Their complete text is supplied below; use it directly without a filesystem read. Do not block case work by trying to load another copy.'
        # Read-only desktop roles may have no host file-read capability. Keep
        # the installed skills canonical and include their exact procedures in
        # the native standing prompt, without granting shell/file access.
        for name in spec['skills']:
            procedure = (ROOT / 'config/openmausbot/skills' / name / 'SKILL.md').read_text()
            soul += '\n\nEnabled procedure, supplied in full: ' + name + '\n' + procedure
        patch = {k: spec[k] for k in ['name', 'title', 'description']}
        patch.update(soul=soul, modelSelection=spec['model'])
        assert len(soul.encode()) <= 24000
        selected.append((role, spec, bot, patch))
    if not a.apply:
        print(json.dumps({'mode': 'plan', 'roles': [{'role': r, 'id': b['id'], 'model': s['model'],
            'skills': s['skills'], 'soul_bytes': len(patch['soul'].encode())} for r,s,b,patch in selected]}, indent=2))
        return
    private = ROOT / '.private/frontier-v2'
    private.mkdir(parents=True, exist_ok=True)
    backup = private / 'native-before.json'
    if backup.exists():
        if not a.resume:
            raise RuntimeError('Preserved native backup already exists; inspect before reapplying')
        before = json.loads(backup.read_text())
        original = {b['id']: b for b in before['bots']}
        prior_receipt = ROOT / 'docs/evidence/frontier-v2/native-profile-update.json'
        previously_applied = {r['bot_id']: r['after_soul_sha256'] for r in
            json.loads(prior_receipt.read_text())['roles']} if prior_receipt.exists() else {}
        for _,_,bot,patch in selected:
            assert bot['soul'] in [original[bot['id']]['soul'], patch['soul']] or hashlib.sha256(bot['soul'].encode()).hexdigest() == previously_applied.get(bot['id']), 'Unrelated profile changes since backup'
    else:
        with backup.open('x') as f:
            json.dump(state, f, indent=2)
        os.chmod(backup, 0o600)
        original = {b['id']: b for b in state['bots']}
    receipts = []
    role_ids = {b['id'] for _,_,b,_ in selected}
    for role,spec,bot,patch in selected:
        # Model changes are thread-scoped in paired API v0.1.91. Update the
        # selected thread and default explicitly; preserve other history.
        api('bots/' + bot['id'], 'PATCH', {k:v for k,v in patch.items() if k != 'modelSelection'})
        api(f'bots/{bot["id"]}/tasks/{bot["threadId"]}', 'PATCH', {
            'modelSelection': patch['modelSelection'], 'updateBotDefault': True, 'requireAvailableModel': True})
        handoffs = []
        for task in bot.get('tasks', []):
            source_bot = (task.get('openedBy') or {}).get('botId')
            if source_bot not in role_ids or task.get('archivedAt') or task['threadId'] == bot['threadId']:
                continue
            # Native pair conversations retain a thread-level selection. A
            # new bot default alone does not move existing handoffs to it.
            api(f'bots/{bot["id"]}/tasks/{task["threadId"]}', 'PATCH', {
                'modelSelection': patch['modelSelection'], 'updateBotDefault': False, 'requireAvailableModel': True})
            handoffs.append({'thread_id': task['threadId'], 'source_bot': source_bot,
                'before_model_selection': task.get('modelSelection'), 'after_model_selection': patch['modelSelection']})
        current = next(b for b in api('bots')['bots'] if b['id'] == bot['id'])
        assert all(current[k] == v for k,v in patch.items()), 'Profile readback mismatch'
        assert all(next(t for t in current['tasks'] if t['threadId'] == h['thread_id'])['modelSelection'] == patch['modelSelection'] for h in handoffs), 'Handoff selection readback mismatch'
        assert current.get('peers') == bot.get('peers') and current.get('autoApprove', False) == bot.get('autoApprove', False)
        existing = {x['name']: x for x in api('bots/' + bot['id'] + '/skills')['skills']}
        hashes = {}
        for name in spec['skills']:
            text = (ROOT / 'config/openmausbot/skills' / name / 'SKILL.md').read_text()
            sha = hashlib.sha256(text.encode()).hexdigest()
            if name in existing:
                assert existing[name]['sha256'] == sha, 'Existing skill differs; explicit revision required'
                api(f'bots/{bot["id"]}/skills/{name}', 'PATCH', {'enabled': True})
            else:
                api('bots/' + bot['id'] + '/skill-template', 'POST', {'name': name,
                    'source': 'project:openbot-radiology/config/openmausbot/skills/' + name,
                    'description': re.search(r'^description: (.+)$', text, re.M).group(1),
                    'text': text, 'enabled': True})
            fetched = api(f'bots/{bot["id"]}/skills/{name}')
            assert fetched['text'] == text, 'Skill readback mismatch'
            listing = api('bots/' + bot['id'] + '/skills')['skills']
            assert next(x for x in listing if x['name'] == name)['enabled']
            hashes[name] = sha
        prompt = api('bots/' + bot['id'] + '/system-prompt')
        receipts.append({'role': role, 'bot_id': bot['id'], 'model': patch['modelSelection'],
            'before_soul_sha256': hashlib.sha256(original[bot['id']].get('soul', '').encode()).hexdigest(),
            'after_soul_sha256': hashlib.sha256(patch['soul'].encode()).hexdigest(),
            'skills': hashes, 'native_profile_readback': True, 'native_skills_readback': True,
            'full_procedures_in_native_standing_prompt': True, 'soul_bytes': len(patch['soul'].encode()),
            'native_pair_thread_model_updates': handoffs,
            'prompt_response_keys': list(prompt), 'peer_and_approval_settings_preserved': True})
    out = ROOT / 'docs/evidence/frontier-v2/native-profile-update.json'
    out.write_text(json.dumps({'version': guidance['version'], 'roles': receipts}, indent=2) + '\n')
    print(json.dumps({'updated_roles': len(receipts), 'receipt': str(out)}, indent=2))


if __name__ == '__main__':
    main()
