#!/usr/bin/env python3
"""Local synthetic MCP fixture. Never controls a desktop or reads any file."""
import json,sys
TOOLS=[{'name':name,'description':'Synthetic transport fixture; no actual operation',
        'inputSchema':{'type':'object','properties':{},'additionalProperties':False}}
       for name in ['get_desktop_state','vm_exec','read_file','search_web']]
for line in sys.stdin:
    request=json.loads(line)
    if 'id' not in request:continue
    method=request['method']
    if method=='initialize':result={'protocolVersion':'2025-06-18','capabilities':{'tools':{}},'serverInfo':{'name':'benchmark-no-operation-fixture','version':'1'}}
    elif method=='tools/list':result={'tools':TOOLS}
    elif method=='tools/call':result={'isError':True,'content':[{'type':'text','text':'Synthetic fixture refuses every operation; no desktop/files/network accessed'}]}
    elif method=='ping':result={}
    else:
        print(json.dumps({'jsonrpc':'2.0','id':request['id'],'error':{'code':-32601,'message':'Unsupported fixture method'}}),flush=True);continue
    print(json.dumps({'jsonrpc':'2.0','id':request['id'],'result':result}),flush=True)
