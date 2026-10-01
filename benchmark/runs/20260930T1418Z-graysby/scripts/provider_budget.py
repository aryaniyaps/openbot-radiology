#!/usr/bin/env python3
"""Existing account allowance and user-authorized single free reset; no purchases."""
import pathlib,json,time,subprocess,select,os,uuid,sys
R=pathlib.Path(__file__).resolve().parents[1]
for attempt in range(2):
 check=subprocess.run([sys.executable,str(R/'scripts/provider_allowance.py')],capture_output=True,text=True,timeout=65)
 if check.returncode==0:break
 transient=any(x in check.stderr for x in ['TimeoutError','request timed out','temporarily unavailable','ConnectionError','failed to fetch codex rate limits: error sending request for url'])
 with (R/'private/allowance-read-recovery.jsonl').open('a') as f:f.write(json.dumps({'at_unix':time.time(),'attempt':attempt+1,'read_only':True,'no_clinical_dispatch':True,'returncode':check.returncode,'transient_detected':transient,'error':check.stderr[-3000:]})+'\n')
 if not transient or attempt:raise RuntimeError('Read-only provider allowance check failed; guard remains closed')
 time.sleep(1)
d=json.loads((R/'evidence/provider-allowance-current.json').read_text())['limits'];used=d['rateLimits']['primary']['usedPercent'];balance=d['rateLimits'].get('credits',{}).get('balance');assert balance in [None,'62500'],'Usage-credit draw detected; stop benchmark rather than incur unbounded paid usage'
if used<95 and d['ordinaryUsageAllowed']:print('Existing subscription allowance available',used);sys.exit(0)
receipt=R/'evidence/free-banked-reset-receipt.json';assert not receipt.exists(),'Already used one authorized free reset; no additional paid usage authorized'
credits=d.get('rateLimitResetCredits',{}).get('credits',[]);credit=next((x for x in credits if x['status']=='available' and 'free' in x.get('description','').lower()),None);assert credit,'No existing free banked reset available'
attempt=R/'private/free-banked-reset-attempt.json'
if attempt.exists():params=json.loads(attempt.read_text())
else:params={'creditId':credit['id'],'idempotencyKey':str(uuid.uuid4())};attempt.write_text(json.dumps(params));attempt.chmod(0o600)
env={k:v for k,v in os.environ.items() if k in ['PATH','HOME','LANG','LC_ALL','TZ','USER','LOGNAME','NO_PROXY','HTTP_PROXY','HTTPS_PROXY']};env['CODEX_HOME']=str(R/'private/provider');cli=R/'private/cli/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex';p=subprocess.Popen([str(cli),'app-server'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(R/'private/reset-rpc-stderr.log').open('a'),text=True,env=env,cwd=R/'private/provider')
def rpc(i,m,v):
 p.stdin.write(json.dumps({'jsonrpc':'2.0','id':i,'method':m,'params':v})+'\n');p.stdin.flush();end=time.monotonic()+30
 while time.monotonic()<end:
  if not select.select([p.stdout],[],[],.5)[0]:continue
  d=json.loads(p.stdout.readline())
  if d.get('id')==i:
   assert 'error' not in d,d.get('error');return d['result']
 raise TimeoutError('Owned reset request; preserve idempotency key')
try:
 rpc(1,'initialize',{'clientInfo':{'name':'benchmark-authorized-free-reset','version':'1'}});p.stdin.write(json.dumps({'jsonrpc':'2.0','method':'initialized','params':{}})+'\n');p.stdin.flush();result=rpc(2,'account/rateLimitResetCredit/consume',params);receipt.write_text(json.dumps({'time_unix':time.time(),'authorization':'User: I have a banked reset I can use; use this Codex account itself','free_credit_verified':True,'before_used_percent':used,'result':result},indent=2));after=rpc(3,'account/rateLimits/read',{});assert after['rateLimits']['primary']['usedPercent']<95 and after['ordinaryUsageAllowed'],'Reset did not restore ordinary usage';print('Consumed existing user-authorized free banked reset; allowance restored',after['rateLimits']['primary']['usedPercent'])
finally:
 p.stdin.close()
 try:p.wait(timeout=3)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=3)
