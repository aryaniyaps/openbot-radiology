#!/usr/bin/env python3
"""Scoped operator access to the named hospital guest; no LAN fallback."""
import pathlib
import shlex
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SSH = ['ssh', '-i', str(ROOT / '.private/server/operator-key'), '-o', 'UserKnownHostsFile='+str(ROOT / '.private/server/known_hosts'), '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'operator@192.168.178.10']

if __name__ == '__main__':
    if sys.argv[1] == 'sql':
        command = 'docker exec -i kauvery-hospital-openmrsdb-1 sh -c ' + shlex.quote('exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" openmrs')
    else:
        command = 'cd /opt/kauvery-hospital && ' + sys.argv[1]
    raise SystemExit(subprocess.run(SSH + [command], input=sys.stdin.buffer.read()).returncode)
