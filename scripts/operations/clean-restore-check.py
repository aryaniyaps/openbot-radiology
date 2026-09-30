#!/usr/bin/env python3
"""Remove only the project's shut-off verification clone after a passing receipt."""
import json,pathlib,subprocess,xml.etree.ElementTree as E,shutil
ROOT=pathlib.Path('/home/aryan/ai-projects/openbot-radiology');TARGET=pathlib.Path('/var/lib/kauvery-hospital/restore-check');NAME='kauvery-restore-check'
e=json.loads((ROOT/'docs/evidence/local-hospital/restore.json').read_text());assert e['status']=='passed'
state=subprocess.check_output(['virsh','domstate',NAME],text=True).strip();assert state=='shut off',state
xml=E.fromstring(subprocess.check_output(['virsh','dumpxml',NAME],text=True));assert xml.find('name').text==NAME
for source in xml.findall('./devices/disk/source'):
 assert pathlib.Path(source.attrib['file']).is_relative_to(TARGET)
assert (TARGET/'restore-domain.xml').is_file()
subprocess.run(['virsh','undefine',NAME],check=True);shutil.rmtree(TARGET);print('Removed only the verified, shut-off restore clone')
