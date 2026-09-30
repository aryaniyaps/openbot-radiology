#!/usr/bin/env python3
"""Operator access to a named project desktop, never a hospital write path."""
import json,subprocess,sys,io,tarfile,pathlib
P=['sudo','-n','-u','kauvery-demo','env','XDG_RUNTIME_DIR=/run/user/1001','podman']
def run(*a,**kw):return subprocess.run(P+list(a),cwd='/tmp',check=True,**kw)
if __name__=='__main__':
 c='openmausbot-computer-daff52065908e226'
 if sys.argv[1]=='screen':
  run('exec','--user','cua',c,'/usr/local/libexec/openmausbot/cua-driver','--socket','/run/user/1000/openmausbot-cua.sock','call','get_desktop_state',json.dumps({'screenshot_out_file':'/home/cua/workspace/operator-screen.png'}),stdout=subprocess.DEVNULL)
  archive=run('cp',c+':/home/cua/workspace/operator-screen.png','-',capture_output=True).stdout
  with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
   member=next(m for m in tar.getmembers() if m.isfile())
   pathlib.Path(sys.argv[2]).write_bytes(tar.extractfile(member).read())
 elif sys.argv[1]=='input':
  script='import sys,types;sys.modules["mouseinfo"]=types.ModuleType("mouseinfo");import pyautogui;'+sys.argv[2]
  run('exec','--user','cua',c,'/home/cua/workspace/operator-venv/bin/python','-c',script)
