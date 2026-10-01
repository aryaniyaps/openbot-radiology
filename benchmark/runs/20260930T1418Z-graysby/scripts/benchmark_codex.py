#!/usr/bin/env python3
"""Benchmark-local Codex entrypoint. Enforces input-arm tool restrictions."""
import os,sys,pathlib,json
R=pathlib.Path(__file__).resolve().parents[1];cli=R/'private/cli/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex'
args=sys.argv[1:]
allowed={'PATH','HOME','LANG','LC_ALL','TZ','USER','LOGNAME','TMPDIR','CODEX_HOME','NO_PROXY','HTTP_PROXY','HTTPS_PROXY','NPM_CONFIG_LOGLEVEL'}
for s in args:
 if s.startswith('mcp_servers.') and '.env_vars=' in s:
  allowed.update(json.loads(s.split('=',1)[1]))
env={k:v for k,v in os.environ.items() if k in allowed}
# Preserve only the isolated credential home; fail closed if misrouted.
assert pathlib.Path(env.get('CODEX_HOME','')).resolve()==(R/'private/provider').resolve(),'Unexpected provider home'
if args and args[0]=='app-server':
 restrictions={'web_search':'disabled','sandbox_mode':'read-only','approval_policy':'never','project_doc_max_bytes':0,'agents.enabled':False}
 for f in ['shell_tool','unified_exec','view_image','apps','plugins','hooks','skill_search','browser_use','browser_use_external','computer_use','image_generation','memories','multi_agent','goals']:
  restrictions['features.'+f]=False
 restrictions['features.skip_host_skill_discovery']=True
 if any(s.startswith('mcp_servers.computer.command=') for s in args):
  restrictions['mcp_servers.computer.enabled_tools']=['get_desktop_state','get_window_state','click','drag','scroll','hotkey','press_key']
 if any(s.startswith('mcp_servers.agents.') for s in args):restrictions['mcp_servers.agents.enabled']=False
 for k,v in restrictions.items():args+=['-c',k+'='+json.dumps(v)]
 # Record names and policies, never environment values or command arguments.
 with (R/'private/benchmark-provider-launches.jsonl').open('a') as f:f.write(json.dumps({'pid':os.getpid(),'command':args[0],'restrictions':restrictions,'environment_names':sorted(env)})+'\n')
os.execve(str(cli),[str(cli),*args],env)
