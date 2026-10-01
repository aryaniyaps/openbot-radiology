#!/usr/bin/env python3
"""Live authorization probes against deployed TLS origins; never print secrets."""
import base64,json,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
a=json.loads((ROOT/'.private/doctor-client-auth.json').read_text())
def api(role,path,method='GET',body=None,origin=None):
 host='https://doctor.radiology.demo' if role in ['doctor','anonymous'] else 'https://it.radiology.demo'
 headers={'Content-Type':'application/json'}
 if role!='anonymous':headers['Authorization']='Basic '+base64.b64encode((a[role]['username']+':'+a[role]['password']).encode()).decode()
 if origin:headers['Origin']=origin
 q=urllib.request.Request(host+path,method=method,headers=headers,data=json.dumps(body).encode() if body is not None else None)
 try:
  with urllib.request.urlopen(q,timeout=30) as r:return r.status,json.loads(r.read()) if r.headers.get('Content-Type','').startswith('application/json') else None
 except urllib.error.HTTPError as e:return e.code,None

def main():
 results=[]
 def probe(label,role,path,method,body,expected,origin=None):
  status,data=api(role,path,method,body,origin);assert status==expected,(label,status,expected)
  results.append({'check':label,'status':status,'expected':expected});return data
 probe('anonymous doctor denied','anonymous','/api/bots','GET',None,401)
 state=probe('authenticated doctor can read native workspace','doctor','/api/bots','GET',None,200)
 bot=next(x for x in state['bots'] if x['name']=='Clinical Assistant')
 assert not any(b.get('busy') or b.get('waitingForTeammates') for b in state['bots']),'Preserve active clinical work'
 probe('doctor IT operations denied','doctor','/operations/api/status','GET',None,403)
 probe('doctor native sessions denied','doctor','/api/auth/sessions','GET',None,403)
 probe('doctor configuration mutation denied','doctor','/api/config','PATCH',{'features':{'autoRecall':True}},403)
 probe('doctor SOUL mutation denied','doctor','/api/bots/'+bot['id'],'PATCH',{'soul':'Authorization probe must not be saved'},403)
 task=probe('doctor may create a case thread','doctor','/api/bots/'+bot['id']+'/tasks','POST',{'title':'Owned authorization verification'},201)
 tid=task['task']['threadId'];route='/api/bots/'+bot['id']+'/tasks/'+tid
 try:
  override={'modelSelection':{'instanceId':'codex','model':'gpt-6.1-sol','effort':'low'}}
  probe('doctor thread execution override denied','doctor',route,'PATCH',override,403)
  probe('doctor Full access override denied','doctor',route,'PATCH',{'approvalMode':'full'},403)
  probe('doctor bot approval policy override denied','doctor','/api/bots/'+bot['id'],'PATCH',{'approvalMode':'full'},403)
  probe('doctor external peer grant denied','doctor','/api/bots/'+bot['id'],'PATCH',{'peers':['unapproved-recipient']},403)
  probe('normalized dot path execution override denied','doctor','/api/bots/'+bot['id']+'/tasks/../tasks/'+tid,'PATCH',override,403)
  probe('doctor permanent approval denied','doctor','/api/bots/'+bot['id']+'/always-allow','POST',{'tool':'test'},403)
  probe('doctor always-approve response denied','doctor','/api/bots/'+bot['id']+'/respond','POST',{'threadId':tid,'requestId':'not-issued','behavior':'allow','always':True},403)
  probe('cross-origin mutation denied','doctor',route,'PATCH',{'title':'Should not be applied'},403,'https://untrusted.example')
 finally:probe('owned verification thread deleted','doctor',route,'DELETE',None,200)
 config=probe('IT can read native configuration','it','/api/config','GET',None,200)
 assert config['features']['autoRecall'] is False
 probe('IT can manage a role through native API','it','/api/bots/'+bot['id'],'PATCH',{'title':bot['title']},200,'https://it.radiology.demo')
 probe('IT can manage native SOUL without changing its value','it','/api/bots/'+bot['id'],'PATCH',{'soul':bot['soul']},200,'https://it.radiology.demo')
 health=probe('IT operational monitoring healthy','it','/operations/api/status','GET',None,200)
 assert health['healthy'] and len(health['roles'])==6
 after=api('it','/api/bots')[1]['bots'];current=next(x for x in after if x['id']==bot['id']);assert current['soul']==bot['soul'] and current['modelSelection']==bot['modelSelection']
 out={'status':'passed','transport':'Trusted HTTPS without certificate bypass','checks':results,'native_soul_and_model_unchanged':True,'telemetry_has_no_patient_text':all('messages' not in x for x in health['roles'])}
 (ROOT/'docs/evidence/hospital-deployment/access-checks.json').write_text(json.dumps(out,indent=2)+'\n');print('Passed',len(results),'live TLS authorization and monitoring checks')

if __name__=='__main__':main()
