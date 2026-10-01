#!/usr/bin/env python3
"""Native Codex entrypoint with no reference/file/web/tool access for reads."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
PRIVATE = ROOT / '.private/frontier-v2'
cli = json.loads((PRIVATE / 'runtime-config.json').read_text())['codex_cli']
args = sys.argv[1:]
allowed = {'PATH','LANG','LC_ALL','TZ','USER','LOGNAME','TMPDIR','CODEX_HOME','NO_PROXY','HTTP_PROXY','HTTPS_PROXY'}
env = {k:v for k,v in os.environ.items() if k in allowed}
assert Path(env.get('CODEX_HOME','')).resolve() == (PRIVATE / 'provider').resolve()
if args and args[0] == 'app-server':
    restrictions = {'web_search':'disabled','sandbox_mode':'read-only','approval_policy':'never',
                    'project_doc_max_bytes':0,'agents.enabled':False}
    if any(s.startswith('mcp_servers.agents.command=') or s.startswith('mcp_servers.agents.url=') for s in args):
        restrictions['mcp_servers.agents.enabled'] = False
    for name in ['shell_tool','unified_exec','view_image','apps','plugins','hooks','skill_search',
                 'browser_use','browser_use_external','computer_use','image_generation','memories','multi_agent','goals']:
        restrictions['features.'+name] = False
    restrictions['features.skip_host_skill_discovery'] = True
    for key,value in restrictions.items():
        args += ['-c',key+'='+json.dumps(value)]
    with (PRIVATE / 'provider-launches.jsonl').open('a') as f:
        f.write(json.dumps({'pid':os.getpid(),'restrictions':restrictions,'environment_names':sorted(env)})+'\n')
os.execve(str(cli),[str(cli),*args],env)
