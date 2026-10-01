#!/usr/bin/env python3
"""Install the hospital CA for the native execution account's Chromium trust."""
import hashlib,pathlib,subprocess
CA=pathlib.Path('/var/lib/kauvery-hospital/workstation-assets/ca.crt')
DATABASE=pathlib.Path('/home/kauvery-demo/.pki/nssdb')
def main():
 subprocess.run(['install','-d','-o','kauvery-demo','-g','kauvery-demo','-m','700',str(DATABASE)],check=True)
 prefix=['runuser','-u','kauvery-demo','--','certutil']
 if not (DATABASE/'cert9.db').exists():subprocess.run(prefix+['-N','--empty-password','-d','sql:'+str(DATABASE)],cwd='/tmp',check=True)
 subprocess.run(prefix+['-A','-d','sql:'+str(DATABASE),'-n','Kauvery Hospital CA','-t','C,,','-i',str(CA)],cwd='/tmp',check=True)
 result=subprocess.run(prefix+['-L','-d','sql:'+str(DATABASE),'-n','Kauvery Hospital CA','-a'],cwd='/tmp',check=True,capture_output=True,text=True)
 assert 'BEGIN CERTIFICATE' in result.stdout
 ROOT=pathlib.Path(__file__).resolve().parents[2]
 (ROOT/'docs/evidence/hospital-deployment/native-browser-trust.json').write_text(__import__('json').dumps({'hospital_ca_sha256':hashlib.sha256(CA.read_bytes()).hexdigest(),'native_account_nss_import_passed':True,'certificate_verification_not_bypassed':True,'runtime_navigation_verification':'pending'},indent=2)+'\n')
 print('Hospital CA imported into native execution account NSS; runtime navigation still needs verification')
if __name__=='__main__':main()
