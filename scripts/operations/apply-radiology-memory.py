#!/usr/bin/env python3
"""Update operational memory through native, journaled, hash-checked API writes."""
import argparse,hashlib,json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser();ap.add_argument('--session',type=Path,required=True);a=ap.parse_args()
s=json.loads(a.session.read_text());text=(ROOT/'config/openmausbot/operating-memory.md').read_text()
def api(path,method='GET',body=None):
    q=urllib.request.Request('http://127.0.0.1:8799/api/'+path,method=method,headers={'Authorization':'Bearer '+s['token'],'Content-Type':'application/json'},data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(q,timeout=30) as f:return json.load(f)
roles=json.loads((ROOT/'config/openmausbot/role-guidance.json').read_text())['roles'];names={x['name'] for x in roles.values()};bots=[b for b in api('bots')['bots'] if b['name'] in names];assert len(bots)==6
records=[]
for b in bots:
    assert not b.get('busy') and not any(t.get('busy') for t in b.get('tasks',[]))
    path='bots/'+b['id']+'/memory/file';before=api(path)
    result=api(path,'PUT',{'path':'MEMORY.md','text':text,'expectedHash':before['hash']})
    actual=api(path);assert actual['text']==text
    upkeep_before=api('bots/'+b['id']+'/memory/upkeep')['enabled']
    api('bots/'+b['id'],'PATCH',{'memoryUpkeep':False})
    assert api('bots/'+b['id']+'/memory/upkeep')['enabled'] is False
    records.append({'bot':b['name'],'before_sha256':before['hash'],'after_sha256':actual['hash'],'journal_entry_id':(result.get('entry') or {}).get('id'),'automatic_memory_before':upkeep_before,'automatic_memory_after':False})
recall_before=api('config')['features']['autoRecall']
api('config','PATCH',{'features':{'autoRecall':False}})
assert api('config')['features']['autoRecall'] is False
(ROOT/'docs/evidence/frontier-v2/native-memory-update.json').write_text(json.dumps({'policy_version':'frontier-v2','records':records,'automatic_cross_conversation_recall_before':recall_before,'automatic_cross_conversation_recall_after':False,'scope':'Dedicated six-role radiology workspace; history preserved, automatic case capture/recall disabled'},indent=2)+'\n')
print(json.dumps({'updated':len(records),'policy_sha256':hashlib.sha256(text.encode()).hexdigest()}))
