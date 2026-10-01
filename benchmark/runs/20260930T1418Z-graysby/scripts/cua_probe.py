#!/usr/bin/env python3
"""Development-only native Cua calls, pinned to the positively owned container."""
import sys,json,pathlib,subprocess,select,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
owned=json.loads((ROOT/'ownership.json').read_text())['owned_containers']
assert len(owned)==1
container=owned[0]
assert container['runtime']=='docker'
actual=json.loads(subprocess.check_output(['docker','inspect',container['name']]))[0]
assert actual['Name']=='/'+container['name'] and actual['State']['Running']
assert [m['Source'] for m in actual['Mounts'] if m['Destination']=='/home/cua/workspace']==[container['mount']]
method=sys.argv[1]; arguments=json.loads(sys.argv[2]) if len(sys.argv)>2 else {}
assert method in ['list_apps','list_windows','get_window_state','get_desktop_state','click','drag','scroll','hotkey','type_text','press_key','start_recording','stop_recording','get_recording_state']
p=subprocess.Popen(['docker','exec','--user','cua','-i',container['name'],'/usr/local/libexec/openmausbot/cua-driver','mcp','--embedded','--socket','/run/user/1000/openmausbot-cua.sock'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
def send(d):p.stdin.write(json.dumps(d)+'\n');p.stdin.flush()
send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'benchmark-development','version':'1'}}})
result=None;deadline=time.monotonic()+30
while time.monotonic()<deadline:
    if not select.select([p.stdout],[],[],1)[0]:continue
    line=p.stdout.readline()
    if not line:break
    d=json.loads(line)
    if d.get('id')==1:
        send({'jsonrpc':'2.0','method':'notifications/initialized'})
        send({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':method,'arguments':arguments}})
    if d.get('id')==2:result=d;break
p.stdin.close()
try:p.wait(timeout=3)
except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=3)
assert result is not None,'Observation expired; inspect target before retrying an action'
record={'timestamp':time.time(),'container':container['name'],'method':method,'arguments':arguments,'response':result}
log=ROOT/'private/cua-development.jsonl'
with log.open('a') as f:f.write(json.dumps(record)+'\n')
for content in result.get('result',{}).get('content',[]):
    if content.get('type')=='text':print(content['text'][:15000])
if result.get('error'):print(json.dumps(result['error']));sys.exit(1)

if result.get('result',{}).get('isError'):sys.exit(1)
