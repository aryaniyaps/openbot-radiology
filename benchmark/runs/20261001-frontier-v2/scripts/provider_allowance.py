#!/usr/bin/env python3
"""Read current authenticated account allowance; no purchase, reset or inference."""
import json,os,select,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parents[2]/'.private/frontier-v2'
env={k:v for k,v in os.environ.items() if k in ['PATH','LANG','LC_ALL','TZ','USER','LOGNAME','NO_PROXY','HTTP_PROXY','HTTPS_PROXY']};env['CODEX_HOME']=str(P/'provider')
p=subprocess.Popen(['/home/aryan/.local/bin/codex','app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(P/'allowance-stderr.log').open('a'),text=True,bufsize=1,env=env,cwd=P/'provider')
def rpc(i,method,params):
 p.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':method,'params':params})+'\n');p.stdin.flush();deadline=time.monotonic()+20
 while time.monotonic()<deadline:
  if not select.select([p.stdout],[],[],.5)[0]:continue
  row=json.loads(p.stdout.readline())
  if row.get('id')==i:
   if row.get('error'):raise RuntimeError(row['error'])
   return row['result']
 raise TimeoutError(method)
try:
 rpc(1,'initialize',{'clientInfo':{'name':'frontier-radiology-allowance','version':'1'}});p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'initialized','params':{}})+'\n');p.stdin.flush();result=rpc(2,'account/rateLimits/read',{});(P/'account-rateLimits-current.json').write_text(json.dumps({'time_unix':time.time(),'no_inference':True,'result':result},indent=2)+'\n');print(json.dumps(result))
finally:
 p.stdin.close()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=3)
