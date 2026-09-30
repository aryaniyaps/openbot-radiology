#!/usr/bin/env python3
"""Operator-only scanner emulator: native MWL C-FIND, pixel-preserving DICOM C-STORE."""
import importlib.util,json,pathlib,sys,subprocess,urllib.request,time,shlex
import pydicom
from pydicom.uid import generate_uid
ROOT=pathlib.Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('h',pathlib.Path(__file__).with_name('configure-hospital.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
from guest import SSH
patient,source,key=sys.argv[1:4];c=h.state['cases'][source]
p=h.request('patient/'+patient+'?v=full');ident=next(i['identifier'] for i in p['identifiers'] if i['preferred']);orders=h.request('order?patient='+patient+'&v=full')['results'];orders=[o for o in orders if o['concept']['uuid']==h.state['concepts'][c['modality']]]
assert len(orders)==1,'Expected exactly one modality order';order=orders[0];acc=order['orderNumber']
for _ in range(60):
 cmd='python3 -c '+shlex.quote('import urllib.request;print(urllib.request.urlopen("http://127.0.0.1:8080/dcm4chee-arc/aets/WORKLIST/rs/mwlitems?PatientID='+ident+'&AccessionNumber='+acc+'").read().decode())')
 raw=subprocess.check_output(SSH+[cmd],text=True);m=json.loads(raw) if raw.strip() else []
 if len(m)==1:break
 time.sleep(1)
else:raise RuntimeError('Native MWL was not populated')
uid=m[0]['0020000D']['Value'][0];mod=m[0]['00400100']['Value'][0]['00080060']['Value'][0];assert mod==c['modality'],(mod,c['modality'])
trace=subprocess.run(SSH+['findscu -W -aec WORKLIST -aet SCHEDULEDSTATION -k '+shlex.quote('PatientID='+ident)+' -k AccessionNumber -k StudyInstanceUID -k ScheduledProcedureStepSequence 192.168.178.10 11112'],capture_output=True,text=True,check=True)
assert acc in trace.stderr and uid in trace.stderr
(ROOT/'docs/evidence/local-hospital'/f'{key}-mwl.txt').write_text(trace.stderr)
out=ROOT/'.private/dicom/scanner'/(key+'-'+acc);out.mkdir(parents=True,exist_ok=True);uids={c['study_uid']:uid}
def remap(dataset):
 for e in dataset:
  if e.VR=='SQ':
   for item in e.value:remap(item)
  elif e.VR=='UI' and e.keyword not in ['SOPClassUID','ReferencedSOPClassUID','TransferSyntaxUID','MediaStorageSOPClassUID','ImplementationClassUID']:
   if isinstance(e.value,str):
    if e.value not in uids:uids[e.value]=generate_uid(entropy_srcs=[str(e.value),uid])
    e.value=uids[e.value]
for i,file in enumerate(sorted((ROOT/'.private/dicom/replay'/source).glob('*.dcm'))):
 target=out/f'{i:04}.dcm'
 if target.exists():continue
 d=pydicom.dcmread(file);pixels=d.PixelData;sop=d.SOPClassUID;remap(d);d.file_meta.MediaStorageSOPInstanceUID=d.SOPInstanceUID;d.PatientID=ident;d.PatientName=p['person']['display'].replace(' ','^');d.AccessionNumber=acc;d.StudyInstanceUID=uid;d.DeidentificationMethod=['Public deidentified source; synthetic demo identity','UID remapping; original geometry and pixels preserved'];assert d.PixelData==pixels and d.SOPClassUID==sop;d.save_as(out/f'{i:04}.dcm',enforce_file_format=True)
remote='/opt/kauvery-hospital/scanner/new/'+key
subprocess.run(SSH+['mkdir -p '+shlex.quote(remote)],check=True);subprocess.run(['scp','-q','-i',str(ROOT/'.private/server/operator-key'),*map(str,out.glob('*.dcm')),'operator@192.168.178.10:'+remote+'/'],check=True)
subprocess.run(SSH+['storescu -q -aet SCHEDULEDSTATION -aec DCM4CHEE --scan-directories --recurse 192.168.178.10 11112 '+shlex.quote(remote)],check=True)
for _ in range(30):
 response=urllib.request.urlopen('https://radiology.demo/dicomweb/studies?PatientID='+ident+'&AccessionNumber='+acc)
 raw=response.read();studies=json.loads(raw) if raw.strip() else []
 if len(studies)==1 and int(studies[0]['00201208']['Value'][0])==len(list(out.glob('*.dcm'))):break
 time.sleep(1)
else:raise RuntimeError('Archive instance count did not match scanner transmission')
result={'patient':patient,'patient_id':ident,'accession':acc,'study_uid':uid,'source_case':source,'modality':c['modality'],'instances':len(list(out.glob('*.dcm'))),'order':order['uuid'],'mwl_modality':mod,'scanner':'public-source acquisition emulator'}
h.state['cases'][key]=result;h.save();print(json.dumps(result))
