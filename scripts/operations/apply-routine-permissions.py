#!/usr/bin/env python3
"""Install native automatic review for the existing, bounded radiology team."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    secrets = json.loads((ROOT / '.private/hospital-it/gateway-secrets.json').read_text())
    headers = {'Authorization': 'Bearer ' + secrets['it_native']['token'],
               'Content-Type': 'application/json'}

    def api(route, method='GET', body=None):
        request = urllib.request.Request('http://127.0.0.1:8799/api/' + route,
            method=method, headers=headers,
            data=json.dumps(body).encode() if body is not None else None)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    policy = json.loads((ROOT / 'config/openmausbot/routine-permissions.json').read_text())
    names = {r['name'] for r in json.loads((ROOT / 'config/openmausbot/role-guidance.json').read_text())['roles'].values()}
    state = api('bots')
    bots = [b for b in state['bots'] if b['name'] in names]
    assert len(bots) == len(names) == 6 and len({b['name'] for b in bots}) == 6
    ids = {b['id'] for b in bots}
    for bot in bots:
        assert not bot.get('busy') and not bot.get('waitingForTeammates') and not any(t.get('busy') for t in bot['tasks']), 'Preserve active work'
        assert bot['computer'] != 'local', 'No host desktop grant'
        assert set(bot['peers']) <= ids - {bot['id']}, 'Explicit existing team only'
    if not args.apply:
        print(json.dumps({'roles': sorted(names), 'mode': policy['approvalMode'], 'host_desktop': False}))
        return
    private = ROOT / '.private/routine-permissions'
    private.mkdir(mode=0o700, exist_ok=True)
    backup = private / 'before.json'
    if not backup.exists():
        backup.write_text(json.dumps(state, indent=2) + '\n')
        os.chmod(backup, 0o600)
    receipts = []
    for bot in bots:
        soul = bot['soul']
        if policy['instructions'] not in soul:
            soul += '\n\nRoutine permission policy:\n' + policy['instructions']
        api('bots/' + bot['id'], 'PATCH', {'approvalMode': policy['approvalMode'],
            'approvePeerComms': policy['approvePeerComms'], 'soul': soul})
        threads = []
        for task in bot['tasks']:
            if task['threadId'] != bot['threadId'] and ((task.get('openedBy') or {}).get('botId') not in ids or task.get('archivedAt')):
                continue
            api(f"bots/{bot['id']}/tasks/{task['threadId']}", 'PATCH', {'approvalMode': policy['approvalMode']})
            threads.append(task['threadId'])
        current = next(b for b in api('bots')['bots'] if b['id'] == bot['id'])
        assert current['autoApprove'] is True and current['approvePeerComms'] is False
        assert current['soul'] == soul
        for key in ['peers', 'modelSelection', 'computer', 'composio', 'browser']:
            assert current.get(key) == bot.get(key), 'Unrelated configuration changed: ' + key
        assert {t['threadId'] for t in current['tasks']} == {t['threadId'] for t in bot['tasks']}, 'History preserved'
        assert all(next(t for t in current['tasks'] if t['threadId'] == tid)['approvalMode'] == policy['approvalMode'] for tid in threads)
        receipts.append({'name': bot['name'], 'bot_id': bot['id'],
            'approval_mode': policy['approvalMode'], 'updated_threads': threads,
            'soul_sha256': hashlib.sha256(soul.encode()).hexdigest(),
            'models_peers_computers_and_history_preserved': True})
    out = ROOT / 'docs/evidence/hospital-deployment/routine-permissions.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'status': 'installed', 'native_version': '0.1.91',
        'native_auto_review': True, 'full_access': False, 'roles': receipts}, indent=2) + '\n')
    print('Installed native automatic review for six bounded roles; history preserved')


if __name__ == '__main__':
    main()
