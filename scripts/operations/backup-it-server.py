#!/usr/bin/env python3
"""Encrypted IT configuration and consistent telemetry backup; no clinical restart."""
import datetime, json, os, pathlib, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/'.private/hospital-it'
REPO='/var/backups/kauvery-hospital/restic'
KEY='/var/lib/kauvery-hospital/backup/restic-password'
def run(*args,**kw):return subprocess.run(list(args),check=True,**kw)
def main():
    assert os.geteuid()==0
    ssh=['ssh','-i',str(P/'operator-key'),'-o','UserKnownHostsFile='+str(P/'known_hosts'),'-o','StrictHostKeyChecking=yes','operator@192.168.178.11']
    # Online SQLite backup avoids copying a live WAL/database pair.
    command="""sudo -n python3 - <<'PY'
import os, sqlite3, tarfile, tempfile, sys
with tempfile.TemporaryDirectory() as d:
 os.chmod(d,0o700)
 src=sqlite3.connect('file:/var/lib/radiology-it/telemetry.sqlite?mode=ro',uri=True)
 dst=sqlite3.connect(d+'/telemetry.sqlite');src.backup(dst);dst.close();src.close()
 with tarfile.open(fileobj=sys.stdout.buffer,mode='w:gz') as t:
  for p in ['/etc/radiology-it','/etc/nginx/sites-available/radiology-it','/etc/nginx/conf.d/radiology-log.conf','/etc/systemd/system/radiology-tunnel.service','/etc/systemd/system/radiology-observability.service','/opt/radiology-it']:
   t.add(p,arcname=p.lstrip('/'))
  t.add(d+'/telemetry.sqlite',arcname='var/lib/radiology-it/telemetry.sqlite')
PY"""
    env={**os.environ,'RESTIC_REPOSITORY':REPO,'RESTIC_PASSWORD_FILE':KEY,'RESTIC_CACHE_DIR':'/var/cache/kauvery-restic'}
    state=pathlib.Path('/var/lib/radiology-deployment/backup');state.mkdir(mode=0o700,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=state) as temp:
        bundle=pathlib.Path(temp)/'it-guest-config.tar.gz'
        with bundle.open('wb') as target:run(*ssh,command,stdout=target)
        bundle.chmod(0o600)
        (state/'domain.xml').write_text(run('virsh','dumpxml','kauvery-it',capture_output=True,text=True).stdout)
        result=run('restic','backup','--json','--tag','radiology-it',str(bundle),str(state/'domain.xml'),'/var/lib/radiology-deployment/operator','/opt/radiology-deployment','/etc/systemd/system/radiology-it-session-renewal.service','/etc/systemd/system/radiology-it-session-renewal.timer','/etc/systemd/system/kauvery-backup.service','/etc/systemd/system/kauvery-backup.service.d','/etc/systemd/system/kauvery-backup.timer',env=env,capture_output=True,text=True)
        summary=next(json.loads(line) for line in result.stdout.splitlines() if json.loads(line).get('message_type')=='summary')
        snapshot=summary['snapshot_id']
        # Restore the exact encrypted guest bundle and inspect it safely.
        restored=pathlib.Path(temp)/'restored.tar.gz'
        with restored.open('wb') as target:run('restic','dump',snapshot,str(bundle),env=env,stdout=target)
        import hashlib,tarfile,sqlite3
        assert hashlib.sha256(restored.read_bytes()).digest()==hashlib.sha256(bundle.read_bytes()).digest()
        with tarfile.open(restored) as archive:
            names=archive.getnames();assert 'etc/radiology-it/runtime.json' in names and 'opt/radiology-it/doctor/cases.json' in names
            db=pathlib.Path(temp)/'restored.sqlite';db.write_bytes(archive.extractfile('var/lib/radiology-it/telemetry.sqlite').read())
        with sqlite3.connect(db) as connection:
            assert connection.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            samples=connection.execute('SELECT count(*) FROM samples').fetchone()[0]
        receipt={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':snapshot,'tag':'radiology-it','encrypted_repository':REPO,'restored_bundle_sha256_matches':True,'restored_telemetry_integrity':'ok','restored_samples':samples,'external_copy':False,'coverage':'IT guest configuration, assets, telemetry, operator secrets, deployment kit and domain definition; hospital VM covered by separate hospital backup'}
        (state/'status.json').write_text(json.dumps(receipt,indent=2)+'\n')
        output=ROOT/'docs/evidence/hospital-deployment';output.mkdir(parents=True,exist_ok=True);(output/'it-backup-restore.json').write_text(json.dumps(receipt,indent=2)+'\n')
        print('Encrypted IT configuration backup and exact-bundle restore passed;',samples,'telemetry samples recovered')
if __name__=='__main__':main()
