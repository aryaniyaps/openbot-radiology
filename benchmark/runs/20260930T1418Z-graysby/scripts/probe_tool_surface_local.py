#!/usr/bin/env python3
"""Capture actual Codex tool specifications at a LOCAL failing fixture endpoint.

No upstream inference, auth copy, provider quota or medical images involved.
The fixture deliberately responds HTTP400, so no mock answer is a model result.
"""
import argparse, hashlib, http.server, json, os, pathlib, select, subprocess, sys, threading, time
parser=argparse.ArgumentParser()
parser.add_argument('--model',default='tool-surface-fixture',choices=['tool-surface-fixture','gpt-6-luna','gpt-6.1-sol','gpt-6-astra'])
parser.add_argument('--mcp-fixture',action='store_true')
parser.add_argument('--inventory',action='store_true',help='Local synthetic tool-call response, metadata only')
parser.add_argument('--deny-write',action='store_true',help='Attempt only an owned fixture canary write under read-only policy')
options=parser.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1]
assert not (options.inventory and options.deny_write)
suffix=options.model+('-mcp' if options.mcp_fixture else '')+('-inventory' if options.inventory else '')+('-deny-write' if options.deny_write else '')
HOME=ROOT/'private'/('tool-surface-'+suffix);HOME.mkdir(mode=0o700,exist_ok=True)
captured=[]
class Endpoint(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get('Content-Length',0)))
        captured.append({'path':self.path,'body':json.loads(body)})
        if (options.inventory or options.deny_write) and len(captured)==1:
            # Replay a metadata-only custom call; it cannot read data or invoke tools.
            if options.deny_write:
                patch='*** Begin Patch\n*** Add File: '+str(HOME/'write-canary.txt')+'\n+synthetic canary, no patient data\n*** End Patch'
                code='text(await tools.apply_patch('+json.dumps(patch)+'));'
            else:code='text(ALL_TOOLS.map(x => ({name:x.name})));'
            item={'type':'custom_tool_call','id':'fixture-item','call_id':'fixture-local-operation','name':'exec','namespace':'functions','input':code}
            result={'id':'fixture-response','object':'response','status':'completed','output':[item]}
            events=[{'type':'response.created','response':dict(result,status='in_progress',output=[])},
                    {'type':'response.output_item.done','output_index':0,'item':item},
                    {'type':'response.completed','response':result}]
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.end_headers()
            for event in events:self.wfile.write(('event: '+event['type']+'\ndata: '+json.dumps(event)+'\n\n').encode())
            self.wfile.flush();return
        self.send_response(400);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(b'{"error":{"message":"Local tool-surface fixture; deliberate refusal, no inference","type":"invalid_request_error"}}')
server=http.server.HTTPServer(('127.0.0.1',0),Endpoint)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
port=server.server_address[1]
cli=ROOT/'private/cli/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex'
config=f'''model = "{options.model}"
model_provider = "benchmark_fixture"
web_search = "disabled"
sandbox_mode = "read-only"
approval_policy = "never"
project_doc_max_bytes = 0
[model_providers.benchmark_fixture]
name = "Local no-inference fixture"
base_url = "http://127.0.0.1:{port}/v1"
env_key = "BENCHMARK_FIXTURE_KEY"
wire_api = "responses"
request_max_retries = 0
stream_max_retries = 0
supports_websockets = false
[features]
shell_tool = false
unified_exec = false
view_image = false
apps = false
plugins = false
hooks = false
skill_search = false
skip_host_skill_discovery = true
browser_use = false
browser_use_external = false
computer_use = false
image_generation = false
memories = false
multi_agent = false
goals = false
[agents]
enabled = false
'''
if options.mcp_fixture:
    config+=f'''[mcp_servers.computer]
command = {json.dumps(sys.executable)}
args = [{json.dumps(str(ROOT/'scripts/mcp_surface_fixture.py'))}]
enabled_tools = ["get_desktop_state"]
startup_timeout_sec = 10
tool_timeout_sec = 10
'''
(HOME/'config.toml').write_text(config)
# Allow only ordinary runtime variables: never inherit current Orca/Codex session hooks.
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','LC_ALL','TZ','USER','LOGNAME','TMPDIR']}
env.update(CODEX_HOME=str(HOME),BENCHMARK_FIXTURE_KEY='synthetic-not-a-credential',NO_PROXY='127.0.0.1,localhost')
child=subprocess.Popen([str(cli),'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(HOME/'stderr.log').open('w'),text=True,bufsize=1,env=env,cwd=HOME)
events=[]
def send(obj):child.stdin.write(json.dumps(obj)+'\n');child.stdin.flush()
def response(request_id,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if not select.select([child.stdout],[],[],0.5)[0]:continue
        line=child.stdout.readline()
        if not line:raise RuntimeError('Owned fixture process closed')
        value=json.loads(line);events.append(value)
        if value.get('id')==request_id:
            if 'error' in value:raise RuntimeError(str(value['error']))
            return value['result']
    raise TimeoutError('Fixture RPC timed out')
try:
    send({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'clientInfo':{'name':'benchmark-local-fixture','version':'1'},'capabilities':{'experimentalApi':True}}});response(1)
    send({'jsonrpc':'2.0','method':'initialized','params':{}})
    send({'jsonrpc':'2.0','id':2,'method':'config/read','params':{'cwd':str(HOME),'includeLayers':False}});resolved=response(2)
    (HOME/'resolved-config.json').write_text(json.dumps(resolved,indent=2)+'\n')
    send({'jsonrpc':'2.0','id':3,'method':'thread/start','params':{'cwd':str(HOME),'model':options.model,'modelProvider':'benchmark_fixture','sandbox':'read-only','approvalPolicy':'never','ephemeral':True}});started=response(3)
    send({'jsonrpc':'2.0','id':4,'method':'turn/start','params':{'threadId':started['thread']['id'],'input':[{'type':'text','text':'Local tool transport fixture. No images. No inference should succeed.'}],'sandboxPolicy':{'type':'readOnly'},'approvalPolicy':'never'}});response(4)
    deadline=time.monotonic()+20
    while len(captured)<(2 if options.inventory or options.deny_write else 1) and time.monotonic()<deadline:
        if select.select([child.stdout],[],[],0.5)[0]:
            line=child.stdout.readline()
            if line:events.append(json.loads(line))
    assert captured,'No local inference request reached fixture; inspect evidence, do not claim surface verification'
finally:
    child.stdin.close()
    try:child.wait(timeout=3)
    except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=3)
    server.shutdown();server.server_close()
    (HOME/'events.json').write_text(json.dumps(events,indent=2)+'\n')
    (HOME/'captured-request.json').write_text(json.dumps(captured,indent=2)+'\n')
body=captured[0]['body'];tools=body.get('tools',[])+[t for item in body.get('input',[]) if item.get('type')=='additional_tools' for t in item.get('tools',[])]
def flattened(items,prefix=''):
    for tool in items:
        name=prefix+tool.get('name',tool.get('type','?'))
        if 'tools' in tool:yield from flattened(tool['tools'],name+'.')
        else:yield {'name':name,'type':tool.get('type')}
flat=list(flattened(tools))
summary={'kind':'local fixture transport inspection; no upstream inference','local_endpoint_port':port,'local_requests':len(captured),
         'requested_model':body.get('model'),'tool_specs':tools,'web_search_exposed':any(t.get('type') in ['web_search','web_search_preview'] for t in tools),
         'model_answer_generated':False,'configuration_sha256':hashlib.sha256(config.encode()).hexdigest(),
         'capture_sha256':hashlib.sha256((HOME/'captured-request.json').read_bytes()).hexdigest(),
         'mcp_fixture_enabled':options.mcp_fixture,'flattened_tool_specs':flat,'environment_policy':'ordinary runtime allowlist only; current Orca/Codex session variables excluded',
         'inventory_call_requested':options.inventory,
         'inventory_call_followup_received':len(captured)>1,
         'canary_write_attempt_requested':options.deny_write,
         'canary_created':(HOME/'write-canary.txt').exists(),
         'scope':'Copied CLI with a local synthetic provider and optional synthetic MCP server; not upstream identity or an integrated OpenMausbot turn'}
(ROOT/'evidence'/('tool-surface-local-'+suffix+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'local_requests':len(captured),'tools':flat,'web_search_exposed':summary['web_search_exposed'],'upstream_inference':False},indent=2))
