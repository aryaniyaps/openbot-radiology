from index_native_trace import index
from response_schema import validate
from runtime_slots import acquire,settle,throttle
#!/usr/bin/env python3
"""One owned Weasis study, one fresh native platform thread, graphical-only model."""
import argparse,pathlib,json,time,urllib.request,uuid,re,hashlib,subprocess,shutil
R=pathlib.Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--case',required=True);p.add_argument('--model',required=True,choices=['gpt-6-luna','gpt-6.1-sol','gpt-6-astra']);p.add_argument('--modality',required=True,choices=['CXR','CT','MR']);p.add_argument('--stage',default='development');p.add_argument('--wall-seconds',type=int,default=180);p.add_argument('--step-limit',type=int,default=24);a=p.parse_args()
def api(path,method='GET',body=None):
 data=json.dumps(body).encode() if body is not None else None
 with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18899/api/'+path,data=data,method=method,headers={'Content-Type':'application/json'}),timeout=20) as f:return json.load(f)
runtime_slot=acquire(a.model)
bid='94515d5f-026d-495b-80cd-883b05f59052';bot=next(x for x in api('bots')['bots'] if x['id']==bid);assert not bot['busy'],'Own viewer occupied'
owned=json.loads((R/'ownership.json').read_text())['owned_containers'][0];actual=json.loads(subprocess.check_output(['docker','inspect',owned['name']]))[0];assert [m['Source'] for m in actual['Mounts'] if m['Destination']=='/home/cua/workspace']==[owned['mount']]
case=R/'agent-visible'/a.case;assert case.is_dir();dcms=sorted(case.rglob('*.dcm'));assert dcms
out=R/'evidence'/a.stage/'A'/a.model/case.name;out.mkdir(parents=True,exist_ok=False)
active=pathlib.Path(owned['mount'])/'active-research-case';active.mkdir(exist_ok=True)
for old in active.iterdir():
 assert old.is_file() and old.suffix=='.dcm';old.unlink()
for f in dcms:shutil.copyfile(f,active/f.name)
cmd=['docker','exec','--user','cua','-e','DISPLAY=:1','-e','LIBGL_ALWAYS_SOFTWARE=1','-e','GALLIUM_DRIVER=llvmpipe','-e','MESA_GL_VERSION_OVERRIDE=4.5',owned['name'],'/home/cua/workspace/weasis/bin/Weasis','$dicom:close --all','$dicom:get -l /home/cua/workspace/active-research-case']
load=subprocess.run(cmd,capture_output=True,text=True,timeout=45);assert load.returncode==0;time.sleep(5)
# Deterministic operator reset, before the timed diagnostic conversation.
probe=R/'scripts/cua_probe.py';python=str(R/'private/venv/bin/python')
subprocess.run([python,str(probe),'get_desktop_state',json.dumps({'screenshot_out_file':'/home/cua/workspace/preflight-before-reset.png'})],check=True,stdout=subprocess.DEVNULL)
subprocess.run([python,str(probe),'click',json.dumps({'target':{'kind':'desktop','display_id':'primary'},'x':900,'y':450})],check=True,stdout=subprocess.DEVNULL)
subprocess.run([python,str(probe),'press_key',json.dumps({'scope':'desktop','key':'Escape'})],check=True,stdout=subprocess.DEVNULL)
subprocess.run([python,str(probe),'hotkey',json.dumps({'scope':'desktop','keys':['ctrl','Enter']})],check=True,stdout=subprocess.DEVNULL)
subprocess.run([python,str(probe),'get_desktop_state',json.dumps({'screenshot_out_file':'/home/cua/workspace/preflight-initial.png'})],check=True,stdout=subprocess.DEVNULL)
initial=pathlib.Path(owned['mount'])/'preflight-initial.png';shutil.copyfile(initial,out/'initial-viewer-state.png')
task=api('bots/'+bid+'/tasks','POST',{'title':a.stage+' '+case.name+' '+a.model,'approvalMode':'ask'})['task'];tid=task['threadId'];taskid=task['threadId'];selection={'instanceId':'codex','model':a.model,'effort':'medium'};api('bots/'+bid+'/tasks/'+taskid,'PATCH',{'modelSelection':selection,'requireAvailableModel':True,'approvalMode':'ask'})
classes={'CXR':['pleural_effusion','pneumothorax','cardiomegaly','focal_consolidation'],'CT':['pleural_effusion','pulmonary_nodule','consolidation','emphysema'],'MR':['white_matter_signal_abnormality','atrophy','chronic_infarction','mass_lesion']}[a.modality]
prompt=f'Independently interpret the {a.modality} research study already open in Weasis on your dedicated container desktop. Expected patient ID: {case.name}. First obtain a desktop screenshot and confirm the case ID. Use ONLY the computer MCP graphical tools get_desktop_state, get_window_state, click, drag, scroll, hotkey, press_key. Do not read files, APIs, source pixels, reports, memory, other agents, or the internet. No shell or external application. Clinical context: modality only, no history or priors. The source is a deidentified published research image study converted to DICOM. Inspect available images and series using the viewer; screenshots are your only visual evidence. Begin at standardized default fit and window. Click within the displayed viewer. Avoid typing paths, opening files or terminals. You have '+str(a.wall_seconds)+' seconds and at most '+str(a.step_limit)+' graphical tool calls. Prioritize useful examination within that limit, then return your final answer. For radiographs inspect both provided views; for volumes inspect multiple levels and available technical sequences, state omissions. Use the displayed image frame counter to confirm scrolling changes images. Never repeat more than three identical scroll requests; use press_key for single up/down keys and Home/End, or hotkey with Shift+up/down (10 frames), or vary the scroll amount to inspect different levels. Return ONLY one JSON object with keys observed_case_id (copy the displayed patient ID), primary_diagnosis (string), findings_status (exact keys '+', '.join(classes)+' with present, absent, uncertain, or unassessable values), key_findings (array of short strings), image_references (array describing actually viewed series/frame positions), urgent_findings (array), confidence (0–1 subjective probability your primary conclusion is correct), abstention (boolean), limitations (array). Use uncertain for equivocal findings and unassessable when coverage cannot support a read. Maximum 250 words. At most six key findings, eight image references and six limitations. No JSON comments.'
request={'threadId':tid,'sendId':str(uuid.uuid4()),'text':prompt};rec={'case_id':case.name,'modality':a.modality,'stage':a.stage,'arm':'A','requested_model':a.model,'model_selection':selection,'bot_id':bid,'thread_id':tid,'task_id':taskid,'container':owned['name'],'dicom_instances_available':len(dcms),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'wall_limit_seconds':a.wall_seconds,'step_limit':a.step_limit,'started_unix':time.time(),'status':'pending'};(out/'assignment.json').write_text(json.dumps(rec,indent=2));(out/'request.json').write_text(json.dumps(request,indent=2));rec['provider_start_wait_seconds']=throttle(a.model);api('bots/'+bid+'/messages','POST',request);end=time.monotonic()+a.wall_seconds;approved=set();seen=set();calls=[]
allowed={'get_desktop_state','get_window_state','click','drag','scroll','hotkey','press_key'}
while time.monotonic()<end:
 b=next(x for x in api('bots')['bots'] if x['id']==bid);assert b['threadId']==tid
 for m in b['messages']:
  tool=m.get('tool');card=m.get('card')
  if tool and tool.get('itemId') and m['id'] not in seen:
   seen.add(m['id']);calls.append({'id':m['id'],'at':m.get('at'),'tool':tool})
   if tool['name'] not in allowed:rec['forbidden_tool']=tool['name'];end=0;break
  if card and not card.get('answered') and card.get('requestId') not in approved:
   try:
    name=card.get('tool');assert name in allowed,'Reject unapproved tool surface'
    preview=next((x['tool'] for x in reversed(b['messages']) if x.get('tool',{}).get('name')==name and x.get('tool',{}).get('input')),None);assert preview,'No arguments available for viewer approval';args=json.loads(preview['input'])
    if name in ['hotkey','press_key'] and '«redacted' in json.dumps(args,ensure_ascii=False):
     raw=[]
     for trace in (R/'private/provider/sessions').rglob('*.jsonl'):
      if trace.stat().st_mtime<rec['started_unix']:continue
      with trace.open() as f:meta=json.loads(f.readline())
      if tid not in meta.get('payload',{}).get('cwd',''):continue
      for line in trace.open():
       item=json.loads(line).get('payload',{})
       if item.get('type')=='custom_tool_call' and ('__'+name+'(') in item.get('input',''):raw.append(item['input'])
     assert raw,'Raw owned shortcut trace unavailable'
     match=re.search(r'keys\s*:\s*(\[[^\]]+\])',raw[-1]) if name=='hotkey' else re.search(r'key\s*:\s*("[^"\n]+")',raw[-1]);assert match,'Nonliteral shortcut arguments cannot be approved'
     args['keys' if name=='hotkey' else 'key']=json.loads(match.group(1))
    if 'x' in args:assert 0<=args['x']<1280 and 50<=args.get('y',-1)<900,'Outside viewer coordinates'
    target=args.get('target',{});assert not target or target.get('kind') in ['desktop','window']
    if target.get('kind')=='desktop':assert target.get('display_id')=='primary'
    if target.get('kind')=='window':assert target.get('pid')==282
    if name=='hotkey':
     keys=[x.lower().replace('arrow','').replace('control','ctrl') for x in args['keys']]
     assert all(x in ['ctrl','shift','alt','up','down','left','right','home','end','pageup','pagedown','enter','tab','m','+','-','add','subtract','numpadadd','numpadsubtract'] for x in keys) and not ('ctrl' in keys and 'alt' in keys),'Unsupported viewer shortcut'
    if name=='press_key':assert args['key'].lower().replace('_','').replace(' ','') in ['up','down','left','right','arrowup','arrowdown','arrowleft','arrowright','home','end','pageup','pagedown','escape','esc','enter','tab','space','spacebar','f11','w','s','z','t','m','d','a','h','c','r','n','q','0','1','2','3','4','5','6','7','8','9'],'Unsupported key '+str(args.get('key'))
    if len(calls)>=a.step_limit:api('bots/'+bid+'/respond','POST',{'threadId':tid,'requestId':card['requestId'],'behavior':'deny'});rec['step_limit_exceeded']=True;end=0;break
   except Exception as error:
    api('bots/'+bid+'/respond','POST',{'threadId':tid,'requestId':card['requestId'],'behavior':'deny'});rec['policy_rejection']=type(error).__name__+': '+str(error);end=0;break
   api('bots/'+bid+'/respond','POST',{'threadId':tid,'requestId':card['requestId'],'behavior':'allow'});approved.add(card['requestId'])
   with (out/'graphical-approvals.jsonl').open('a') as f:f.write(json.dumps({'at':time.time(),'thread_id':tid,'request_id':card['requestId'],'tool':name,'authorization':'User authorized benchmark computer use; bound to owned container','scope':'graphical viewer-only tools'})+'\n')
 if len(calls)>a.step_limit:rec['step_limit_exceeded']=True;break
 if not b.get('busy') and any(m.get('digest') or m.get('turnTerminal') for m in b['messages']):break
 time.sleep(.5)
else:rec['status']='timeout'
if b.get('busy'):
 api('bots/'+bid+'/interrupt','POST',{'threadId':tid});rec['status']='timeout' if not rec.get('forbidden_tool') else 'quarantined';b=settle(bid,tid)
(out/'observation.json').write_text(json.dumps(b,indent=2));(out/'actions.json').write_text(json.dumps(calls,indent=2));ds=[m for m in b['messages'] if m.get('digest')];term=[m for m in b['messages'] if m.get('turnTerminal')]
if ds:
 m=ds[-1];rec.update(turn_id=m.get('turnId') or m['digest'].get('turnId'),usage=m['digest'].get('usage'),duration_ms=m['digest'].get('durationMs'),tool_calls=m['digest'].get('toolCalls'))
 if rec['status']=='pending':rec['status']='succeeded' if m.get('turnSucceeded') else 'failed'
text=next((m['text'] for m in reversed(term) if m.get('turnSucceeded')),ds[-1]['digest'].get('reply','') if ds else '');rec['raw_answer']=text
try:
 clean=re.sub(r'^```(?:json)?\s*|\s*```$','',text.strip());v=json.loads(clean);assert set(v['findings_status'])==set(classes);assert all(x in ['present','absent','uncertain','unassessable'] for x in v['findings_status'].values());rec['structured_answer']=validate(v,classes);assert v.get('observed_case_id')==case.name,'Case ID mismatch'
except Exception as e:rec['structured_answer']=None;rec['parse_error']=type(e).__name__
rec['finished_unix']=time.time();rec['native_identity']=index(R,rec,out);
(out/'result.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({k:rec.get(k) for k in ['case_id','requested_model','status','duration_ms','tool_calls','parse_error']}))
