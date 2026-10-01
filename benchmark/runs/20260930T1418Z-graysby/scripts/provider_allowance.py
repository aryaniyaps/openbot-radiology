#!/usr/bin/env python3
"""Read own cloned Codex account allowance without inference or credential refresh."""
import pathlib,json,os,subprocess,select,time
R=pathlib.Path(__file__).resolve().parents[1];cli=R/'private/cli/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex';env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','LC_ALL','TZ','USER','LOGNAME','NO_PROXY','HTTP_PROXY','HTTPS_PROXY']};env['CODEX_HOME']=str(R/'private/provider')
p=subprocess.Popen([str(cli),'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(R/'private/provider-allowance-stderr.log').open('a'),text=True,bufsize=1,env=env,cwd=R/'private/provider')
def rpc(i,m,params):
 p.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':m,'params':params})+'\n');p.stdin.flush();end=time.monotonic()+20
 while time.monotonic()<end:
  if not select.select([p.stdout],[],[],.5)[0]:continue
  s=p.stdout.readline()
  if not s:raise RuntimeError('Owned allowance process closed')
  d=json.loads(s)
  if d.get('id')==i:
   if 'error' in d:raise RuntimeError(str(d['error']))
   return d['result']
 raise TimeoutError('Allowance RPC')
try:
 rpc(1,'initialize',{'clientInfo':{'name':'benchmark-allowance-check','version':'1'}})
 p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'initialized','params':{}})+'\n');p.stdin.flush()
 d=rpc(2,'account/rateLimits/read',{})
 (R/'evidence/provider-allowance-current.json').write_text(json.dumps({'time_unix':time.time(),'no_inference':True,'limits':d},indent=2)+'\n');print(json.dumps(d))
finally:
 p.stdin.close()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=3)
