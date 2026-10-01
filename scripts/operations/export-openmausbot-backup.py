#!/usr/bin/env python3
"""Export a native team backup and redact credentials known to this installation."""
import base64
import argparse
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
SECRET_FIELD = re.compile(r'password|passwd|token|secret|api.?key|private.?key', re.I)


def known_secrets():
    values = set()

    def collect(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if SECRET_FIELD.search(key) and isinstance(item, str) and len(item) >= 8:
                    values.add(item)
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    candidates = list((ROOT / '.private').glob('*.json'))
    candidates += list((ROOT / '.private/server').glob('*.json'))
    candidates += [pathlib.Path('/home/kauvery-demo/.codex/auth.json')]
    for path in candidates:
        if path.exists():
            collect(json.loads(path.read_text()))
    for path in list((ROOT / '.private').glob('*.env')) + list((ROOT / '.private/server').glob('*.env')):
        for line in path.read_text().splitlines():
            key, sep, value = line.partition('=')
            value = value.strip().strip('\"\'')
            if sep and SECRET_FIELD.search(key) and len(value) >= 8:
                values.add(value)
    values -= {'password', 'REDACTED', '[REDACTED]', 'changeme', 'change-me'}
    return values | {urllib.parse.quote(v, safe='') for v in values} | {base64.b64encode(v.encode()).decode() for v in values}


def sanitize(value, secrets):
    if isinstance(value, str):
        for secret in sorted(secrets, key=len, reverse=True):
            value = value.replace(secret, '[REDACTED]')
        value = re.sub(r'\bBearer\s+[A-Za-z0-9._~+/=-]{16,}', 'Bearer [REDACTED]', value)
        value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED]', value)
        value = re.sub(r'([?&](?:password|token|api_key)=)[^\s&\"<>]+', r'\1[REDACTED]', value, flags=re.I)
        return value
    if isinstance(value, dict):
        return {k: sanitize(v, secrets) for k, v in value.items() if k != 'connectorTools'}
    if isinstance(value, list):
        return [sanitize(v, secrets) for v in value]
    return value


def validate(backup):
    assert backup['format'] == 'openmaus.backup' and backup['version'] == 1
    bot_keys = [bot['key'] for bot in backup['bots']]
    assert len(bot_keys) == len(set(bot_keys))
    for bot in backup['bots']:
        tasks = bot['tasks']
        task_keys = [task['key'] for task in tasks]
        assert len(task_keys) == len(set(task_keys))
        assert not bot.get('activeTask') or bot['activeTask'] in task_keys
        for task in tasks:
            ids = [m['id'] for m in task['messages']]
            assert len(ids) == len(set(ids))
            assert not task.get('activeLeafId') or task['activeLeafId'] in ids
            assert all(not m.get('parentId') or m['parentId'] in ids for m in task['messages'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=pathlib.Path, default=ROOT / '.private/server/operator-session.json')
    parser.add_argument('--profiles-only', action='store_true', help='Export current profiles and operating memory with empty tasks, excluding historical case facts')
    args = parser.parse_args()
    session = json.loads(args.session.read_text())
    request = urllib.request.Request('http://127.0.0.1:8799/api/teams/export',
        data=json.dumps({'format': 'backup', 'name': 'Radiology clinical assistant team'}).encode(),
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + session['token']})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = json.load(response)
    backup = sanitize(raw, known_secrets())
    if args.profiles_only:
        for bot in backup['bots']:
            bot['tasks'] = bot['tasks'][:1]
            bot['activeTask'] = bot['tasks'][0]['key'] if bot['tasks'] else None
            for task in bot['tasks']:
                task['messages'] = []
                task['activeLeafId'] = None
                task['title'] = 'New radiology case'
            bot['memory']['topics'] = []
            bot['memory']['logs'] = []
        backup['routines'] = []
    validate(backup)
    destination = ROOT / 'backups/openmausbot.backup.json'
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(backup, indent=2, ensure_ascii=False) + '\n')
    print(f'Exported {len(backup["bots"])} profiles to {destination.relative_to(ROOT)}')
