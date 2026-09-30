#!/usr/bin/env python3
"""Open one verified demonstration study using native Weasis DICOMweb."""
import json,pathlib,subprocess,sys,urllib.parse
root=pathlib.Path(__file__).resolve().parents[2];s=json.loads((root/'.private/server/hospital-state.json').read_text());c=s['cases'][sys.argv[1]]
command='$dicom:close --all $dicom:rs --url "https://radiology.demo/dicomweb" -r "studyUID='+c['study_uid']+'"'
uri='weasis://?'+command
p=['sudo','-n','-u','kauvery-demo','env','XDG_RUNTIME_DIR=/run/user/1001','podman','exec','--user','cua', 'openmausbot-computer-daff52065908e226','/home/cua/workspace/apps/weasis/bin/Weasis',uri]
subprocess.run(p,check=True,cwd='/tmp')
