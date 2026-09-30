#!/usr/bin/env python3
"""Operator migration of demo MWL metadata through native PACS REST, preserving studies."""
import json,pathlib,subprocess,sys
from guest import SSH
ROOT=pathlib.Path(__file__).resolve().parents[2]
script=r'''
import json,urllib.request,urllib.parse,sys
base='http://127.0.0.1:8080/dcm4chee-arc/aets/WORKLIST/rs/mwlitems'
items=json.load(urllib.request.urlopen(base));changes=[]
for item in items:
 acc=item['00080050']['Value'][0]
 if not acc.startswith('ORD-') or len(acc)>16:continue
 sps=item['00400100']['Value'][0];old=sps['00400009']['Value'][0];requested=item.get('00401001',{}).get('Value',[''])[0]
 if len(old)<=16 and len(requested)<=16:continue
 uid=item['0020000D']['Value'][0]
 sps['00400009']={'vr':'SH','Value':[acc]};item['00401001']={'vr':'SH','Value':[acc]}
 req=urllib.request.Request(base,data=json.dumps(item).encode(),headers={'Content-Type':'application/dicom+json'})
 assert urllib.request.urlopen(req).status==200
 updated=json.load(urllib.request.urlopen(base+'?AccessionNumber='+urllib.parse.quote(acc)))
 assert any(x['00400100']['Value'][0]['00400009']['Value']==[acc] for x in updated)
 if old!=acc:
  req=urllib.request.Request(base+'/'+urllib.parse.quote(uid,safe='')+'/'+urllib.parse.quote(old,safe=''),method='DELETE');assert urllib.request.urlopen(req).status in [200,204]
 changes.append({'accession':acc,'scheduled_procedure_step_id':acc,'requested_procedure_id':acc})
final=json.load(urllib.request.urlopen(base));assert len(final)==len(items)
assert all(len(x['00400100']['Value'][0]['00400009']['Value'][0])<=16 for x in final)
print(json.dumps({'changes':changes,'worklist_entries':len(final),'short_string_ids_valid':True}))
'''
r=subprocess.run(SSH+['python3 -'],input=script,text=True,capture_output=True,check=True)
(ROOT/'docs/evidence/local-hospital/worklist-conformance.json').write_text(json.dumps(json.loads(r.stdout),indent=2));print('Native worklist IDs migrated and verified')
