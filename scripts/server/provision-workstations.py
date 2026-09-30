#!/usr/bin/env python3
"""Idempotent operator provisioning of the six app-managed desktops."""
import json
import pathlib
import subprocess

BASE = pathlib.Path('/var/lib/kauvery-hospital/workstation-assets')
PREFIX = ['sudo', '-n', '-u', 'kauvery-demo', 'env', 'XDG_RUNTIME_DIR=/run/user/1001', 'podman']

def podman(*args, **kw):
    return subprocess.run(PREFIX + list(args), check=True, cwd='/tmp', **kw)

containers = json.loads(podman('ps', '--format', 'json', capture_output=True, text=True).stdout)
for container in containers:
    name = container['Names'][0]
    if not name.startswith('openmausbot-computer-'):
        continue
    mesa_probe = subprocess.run(PREFIX + ['exec', name, 'test', '-f', '/etc/kauvery-mesa-v1'], cwd='/tmp')
    if mesa_probe.returncode != 0:
        podman('cp', str(BASE / 'mesa-debs'), name + ':/tmp/kauvery-mesa-debs')
        podman('exec', name, 'sh', '-c', 'for f in /tmp/kauvery-mesa-debs/*.deb; do dpkg-deb -x "$f" /; done; ldconfig; touch /etc/kauvery-mesa-v1')
    probe = subprocess.run(PREFIX + ['exec', name, 'test', '-f', '/etc/kauvery-provision-v3'], cwd='/tmp')
    if probe.returncode == 0:
        continue
    podman('exec', '--user', 'cua', name, 'mkdir', '-p', '/home/cua/workspace/apps')
    archive = subprocess.check_output(['tar', '-C', str(BASE), '-cf', '-', 'weasis'])
    podman('exec', '--user', 'cua', '-i', name, 'tar', '-xf', '-', '-C', '/home/cua/workspace/apps', input=archive)
    podman('exec', name, 'mkdir', '-p', '/usr/local/share/ca-certificates', '/etc/firefox/policies')
    podman('exec', name, 'mkdir', '-p', '/etc/ssl/certs/java')
    podman('cp', str(BASE / 'java-cacerts'), name + ':/etc/ssl/certs/java/cacerts')
    podman('cp', str(BASE / 'ca.crt'), name + ':/usr/local/share/ca-certificates/kauvery-demo.crt')
    script = r'''
set -eu
grep -q '192.168.178.10 radiology.demo' /etc/hosts || echo '192.168.178.10 radiology.demo' >> /etc/hosts
update-ca-certificates >/dev/null
cat > /etc/firefox/policies/policies.json <<'EOF'
{"policies":{"Certificates":{"Install":["/usr/local/share/ca-certificates/kauvery-demo.crt"]},"Homepage":{"URL":"https://radiology.demo/","StartPage":"homepage"}}}
EOF
'''
    podman('exec', '-i', name, '/bin/sh', input=script, text=True)
    script = r'''
set -eu
mkdir -p /home/cua/workspace/preferences/weasis /home/cua/Desktop /home/cua/.local/share/applications
if [ ! -e /home/cua/.weasis ]; then ln -s /home/cua/workspace/preferences/weasis /home/cua/.weasis; fi
cat > /home/cua/Desktop/Radiology.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Radiology workspace
Exec=firefox https://radiology.demo/
Icon=applications-science
Terminal=false
EOF
cat > /home/cua/Desktop/Weasis.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=Weasis imaging viewer
Exec=/home/cua/workspace/apps/weasis/bin/Weasis %U
Icon=/home/cua/workspace/apps/weasis/lib/Weasis.png
Terminal=false
MimeType=x-scheme-handler/weasis;application/dicom;
EOF
cp /home/cua/Desktop/Weasis.desktop /home/cua/.local/share/applications/weasis.desktop
chmod +x /home/cua/Desktop/*.desktop
xdg-mime default weasis.desktop x-scheme-handler/weasis
'''
    podman('exec', '--user', 'cua', '-i', name, '/bin/sh', input=script, text=True)
    # Persist browser sessions in the app-owned workspace, after a clean browser exit.
    script = r"""
set -eu
pkill -TERM -x firefox-esr || true
sleep 2
mkdir -p /home/cua/workspace/preferences
if [ ! -L /home/cua/.mozilla ]; then
  if [ -d /home/cua/workspace/preferences/firefox ]; then
    if [ -d /home/cua/.mozilla ]; then mv /home/cua/.mozilla /home/cua/.mozilla.initial; fi
  elif [ -d /home/cua/.mozilla ]; then mv /home/cua/.mozilla /home/cua/workspace/preferences/firefox; else mkdir -p /home/cua/workspace/preferences/firefox; fi
  ln -s /home/cua/workspace/preferences/firefox /home/cua/.mozilla
fi
"""
    podman('exec', '--user', 'cua', '-i', name, '/bin/sh', input=script, text=True)
    podman('exec', name, 'touch', '/etc/kauvery-provision-v3')
    print(name, 'provisioned', flush=True)
