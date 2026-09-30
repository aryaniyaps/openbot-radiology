#!/usr/bin/env python3
import importlib.util,pathlib,secrets,json,subprocess
sp=importlib.util.spec_from_file_location('hospital',pathlib.Path(__file__).with_name('configure-hospital.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
# Native service account receives only read privileges needed for order feed.
roles=h.values('role'); common=next(r for r in roles if r['display']=='Clinical-App-Read-Only')['uuid']; role=h.request('role/'+common+'?v=full')
privs=[p['uuid'] for p in role['privileges']]
allp=h.values('privilege'); names={'Get Providers','Get Users','Get Encounter Types','Get Encounter Roles','Get Concepts','Get Orders','Get Patients','Get Encounters','Get Visits'}
selected=[p['uuid'] for p in allp if p['display'] in names]
existing=next((r for r in roles if r['display']=='Demo-PACS-Read-Only'),None)
r=h.request('role/'+existing['uuid'],{'privileges':selected}) if existing else h.request('role',{'name':'Demo-PACS-Read-Only','description':'Native imaging order integration read access','privileges':selected})
h.request('user/'+h.state['accounts']['pacs_service']['user'],{'roles':[r['uuid']]})
if 'admin' not in h.state['accounts']:
 a={'username':'admin','password':secrets.token_urlsafe(24)+'9Aa!','user':'82f18b44-6814-11e8-923f-e9a88dcb533f'}
 h.request('password',{'oldPassword':'Admin123','newPassword':a['password']})
 assert h.request('session',account=a).get('authenticated');h.state['accounts']['admin']=a;h.save()
print('Operator password rotated; native read-only integration role configured')
