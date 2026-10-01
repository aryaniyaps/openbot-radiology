#!/usr/bin/env python3
"""Install the IT control gateway on the named guest; secrets stay private."""
import argparse, base64, hashlib, io, json, os, pathlib, secrets, shlex, ssl, subprocess, tarfile, time, urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
P=ROOT/'.private/hospital-it'
H=pathlib.Path('/home/aryan/ai-projects/openbot-radiology/.private/server')

def run(*args,**kw): return subprocess.run(list(args),check=True,**kw)
def management_token():
    # Renew from the gateway's current admin session, rather than an operator
    # session that would itself eventually expire outside this renewal loop.
    if (P/'gateway-secrets.json').exists():
        return json.loads((P/'gateway-secrets.json').read_text())['it_native']['token']
    return json.loads((H/'operator-session.json').read_text())['token']
def api(path,body):
    token=management_token()
    q=urllib.request.Request('http://127.0.0.1:8799/api/'+path,
        data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    with urllib.request.urlopen(q,timeout=30) as f:return json.load(f)
def pair(label,scope):
    code=api('auth/pairing',{'label':label,'scopes':['admin','client'] if scope=='admin' else ['client']})
    return api('auth/pair',{'code':code['code'],'label':label})

def main():
    assert os.geteuid()==0
    assert (P/'guest.json').exists()
    parser=argparse.ArgumentParser();parser.add_argument('--rotate-if-due',action='store_true');parser.add_argument('--renew-now',action='store_true');args=parser.parse_args()
    old_sessions=[]
    if args.rotate_if_due or args.renew_now:
        state=json.loads((P/'gateway-secrets.json').read_text())
        remaining=min(state[k]['session']['expiresAt']/1000-time.time() for k in ['doctor_native','it_native'])
        if remaining>14*86400 and not args.renew_now and not state.get('pending_rotation'):
            print('Native gateway sessions have more than 14 days remaining');return
        token=management_token()
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8799/api/bots',headers={'Authorization':'Bearer '+token})) as response:bots=json.load(response)['bots']
        if any(b.get('busy') or b.get('waitingForTeammates') or any(t.get('busy') for t in b.get('tasks',[])) for b in bots):
            print('Session rotation deferred: preserve active case work');return
        old_sessions=state.get('pending_rotation',[])
        if not old_sessions:
            for key,label,scope in [('doctor_native','Hospital gateway: doctor practice','client'),('it_native','Hospital IT management server','admin')]:
                old_sessions.append(state[key]['session']['id']);state[key]=pair(label,scope)
            state['pending_rotation']=old_sessions
        (P/'gateway-secrets.json').write_text(json.dumps(state,indent=2))
    # The doctor boundary is root-managed and runs without native data access.
    # Keep its path independent of a developer checkout.
    if subprocess.run(['id','radiology-gateway'],capture_output=True).returncode:
        run('useradd','--system','--no-create-home','--shell','/usr/sbin/nologin','radiology-gateway')
    for relative in ['scripts/operations/doctor-workspace-proxy.py','config/openmausbot/doctor-workspace.css']:
        target=pathlib.Path('/opt/radiology-client')/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/relative).read_bytes());target.chmod(0o644)
    userunit=pathlib.Path('/home/aryan/.config/systemd/user/openmausbot-doctor-workspace.service')
    if userunit.exists() and not (P/'doctor-user-service-before').exists():
        (P/'doctor-user-service-before').write_bytes(userunit.read_bytes())
    run('runuser','-u','aryan','--','env','XDG_RUNTIME_DIR=/run/user/1000',
        'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus','systemctl','--user','disable','--now','openmausbot-doctor-workspace.service')
    pathlib.Path('/etc/systemd/system/openmausbot-doctor-workspace.service').write_bytes((ROOT/'config/operations/openmausbot-doctor-workspace.service').read_bytes())
    run('systemctl','daemon-reload');run('systemctl','enable','--now','openmausbot-doctor-workspace.service')
    run('systemctl','restart','openmausbot-doctor-workspace.service')
    if not (P/'gateway-secrets.json').exists():
        state={'doctor':{'username':'doctor','password':secrets.token_urlsafe(20)},
               'it':{'username':'itadmin','password':secrets.token_urlsafe(24)},
               'doctor_native':pair('Hospital gateway: doctor practice','client'),
               'it_native':pair('Hospital IT management server','admin')}
        (P/'gateway-secrets.json').write_text(json.dumps(state,indent=2));(P/'gateway-secrets.json').chmod(0o600)
    state=json.loads((P/'gateway-secrets.json').read_text())
    if not (P/'tunnel-key').exists():run('ssh-keygen','-q','-t','ed25519','-N','','-f',str(P/'tunnel-key'))
    if subprocess.run(['id','radiology-it-tunnel'],capture_output=True).returncode:
        run('useradd','--system','--create-home','--shell','/bin/sh','radiology-it-tunnel')
    hostssh=pathlib.Path('/home/radiology-it-tunnel/.ssh');hostssh.mkdir(mode=0o700,exist_ok=True)
    key=(P/'tunnel-key.pub').read_text().strip()
    (hostssh/'authorized_keys').write_text('restrict,port-forwarding,command="/bin/false",permitopen="127.0.0.1:8798",permitopen="127.0.0.1:8799" '+key+'\n')
    run('chown','-R','radiology-it-tunnel:radiology-it-tunnel',str(hostssh));(hostssh/'authorized_keys').chmod(0o600)
    certificate_due=not (P/'server.crt').exists() or ssl.cert_time_to_seconds(ssl._ssl._test_decode_cert(str(P/'server.crt'))['notAfter'])-time.time()<30*86400
    if certificate_due:
        run('openssl','req','-new','-newkey','rsa:2048','-nodes','-keyout',str(P/'server.key'),'-out',str(P/'server.csr'),'-subj','/CN=doctor.radiology.demo',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        (P/'server.ext').write_text('subjectAltName=DNS:doctor.radiology.demo,DNS:it.radiology.demo,IP:192.168.178.11\nextendedKeyUsage=serverAuth\n')
        run('openssl','x509','-req','-in',str(P/'server.csr'),'-CA',str(H/'tls/ca.crt'),'-CAkey',str(H/'tls/ca.key'),'-CAserial',str(P/'ca.srl'),'-CAcreateserial','-out',str(P/'server.crt'),'-days','180','-sha256','-extfile',str(P/'server.ext'),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        (P/'server.key').chmod(0o600)
    admin=state['it_native']['token'];doctor=state['doctor_native']['token']
    common='''ssl_certificate /etc/radiology-it/server.crt;
ssl_certificate_key /etc/radiology-it/server.key;
ssl_protocols TLSv1.2 TLSv1.3;
client_max_body_size 40m;
add_header X-Content-Type-Options nosniff always;
add_header Referrer-Policy same-origin always;
'''
    nginx='''server { listen 192.168.178.11:80 default_server; server_name doctor.radiology.demo it.radiology.demo; return 301 https://$host$request_uri; }
server { listen 192.168.178.11:443 ssl default_server; server_name _; '''+common+'''return 444; }
server { listen 192.168.178.11:443 ssl; server_name doctor.radiology.demo;
'''+common+'''auth_basic "Radiology doctor workstation";
auth_basic_user_file /etc/radiology-it/doctor.htpasswd;
access_log /var/log/nginx/radiology-doctor.log radiology;
location ^~ /operations/ { return 403; }
location ^~ /worklist/ { alias /opt/radiology-it/doctor/; index index.html; }
location = /api/auth/logout { return 403; }
location = /api/auth/pair { return 403; }
location = /api/pair { return 403; }
location / { proxy_pass http://127.0.0.1:18798;
proxy_set_header Host localhost:8798;
proxy_set_header Authorization "Bearer '''+doctor+'''";
proxy_set_header Cookie "";
proxy_set_header Accept-Encoding "";
proxy_buffering off; proxy_read_timeout 3600s;
}
}
server { listen 192.168.178.11:443 ssl; server_name it.radiology.demo;
'''+common+'''auth_basic "Radiology IT management";
auth_basic_user_file /etc/radiology-it/it.htpasswd;
access_log /var/log/nginx/radiology-it.log radiology;
location ^~ /operations/ { proxy_pass http://127.0.0.1:9050; }
location / { proxy_pass http://127.0.0.1:18799;
proxy_set_header Host it.radiology.demo;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header Authorization "Bearer '''+admin+'''";
proxy_set_header Cookie "";
proxy_buffering off; proxy_read_timeout 3600s;
}
}
'''
    tunnel='''[Unit]
Description=Restricted SSH transport to native radiology execution host
After=network-online.target
Wants=network-online.target
[Service]
User=radiology-it
ExecStart=/usr/bin/ssh -N -i /etc/radiology-it/tunnel-key -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/etc/radiology-it/known_hosts -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -L 127.0.0.1:18798:127.0.0.1:8798 -L 127.0.0.1:18799:127.0.0.1:8799 radiology-it-tunnel@192.168.178.1
Restart=always
RestartSec=5
NoNewPrivileges=yes
[Install]
WantedBy=multi-user.target
'''
    monitor='''[Unit]
Description=Radiology IT operational monitoring
After=network-online.target radiology-tunnel.service
[Service]
User=radiology-it
ExecStart=/usr/bin/python3 /opt/radiology-it/it-observability.py
Restart=always
RestartSec=5
StateDirectory=radiology-it
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
NoNewPrivileges=yes
[Install]
WantedBy=multi-user.target
'''
    files={'etc/nginx/sites-available/radiology-it':nginx,
        'etc/nginx/conf.d/radiology-log.conf':'log_format radiology \'$time_iso8601 user=$remote_user method=$request_method status=$status bytes=$body_bytes_sent duration=$request_time\';\n',
        'etc/systemd/system/radiology-tunnel.service':tunnel,
        'etc/systemd/system/radiology-observability.service':monitor,
        'etc/radiology-it/runtime.json':json.dumps({'admin_token':admin,
            'native_session_expiry_unix':min(state[k]['session']['expiresAt']/1000 for k in ['doctor_native','it_native']),
            'tls_cert_expiry_unix':ssl.cert_time_to_seconds(ssl._ssl._test_decode_cert(str(P/'server.crt'))['notAfter'])}),
        'etc/radiology-it/known_hosts':'192.168.178.1 '+pathlib.Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text(),
        'etc/radiology-it/tunnel-key':(P/'tunnel-key').read_text(),
        'etc/radiology-it/server.key':(P/'server.key').read_text(),
        'etc/radiology-it/server.crt':(P/'server.crt').read_text(),
        'usr/local/share/ca-certificates/radiology-hospital.crt':(H/'tls/ca.crt').read_text(),
        'opt/radiology-it/it-observability.py':(ROOT/'scripts/operations/it-observability.py').read_text(),
        'opt/radiology-it/operations.html':(ROOT/'config/it/operations.html').read_text()}
    for role in ['doctor','it']:
        account=state[role];hashed=run('openssl','passwd','-6','-stdin',input=account['password']+'\n',text=True,capture_output=True).stdout.strip()
        files[f'etc/radiology-it/{role}.htpasswd']=account['username']+':'+hashed+'\n'
    for path in (ROOT/'config/doctor').rglob('*'):
        if path.is_file():files['opt/radiology-it/doctor/'+str(path.relative_to(ROOT/'config/doctor'))]=path.read_bytes()
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as tar:
        for name,text in files.items():
            data=text if isinstance(text,bytes) else text.encode();entry=tarfile.TarInfo(name);entry.size=len(data);entry.mode=0o600 if name.startswith('etc/radiology-it/') or name.endswith('sites-available/radiology-it') else 0o644;tar.addfile(entry,io.BytesIO(data))
    ssh=['ssh','-i',str(P/'operator-key'),'-o','UserKnownHostsFile='+str(P/'known_hosts'),'-o','StrictHostKeyChecking=yes','-o','BatchMode=yes','operator@192.168.178.11']
    run(*ssh,'sudo -n tar -xzf - -C /',input=stream.getvalue())
    install='''set -eu
id radiology-it >/dev/null 2>&1 || useradd --system --home /var/lib/radiology-it --shell /usr/sbin/nologin radiology-it
chown root:radiology-it /etc/radiology-it/tunnel-key /etc/radiology-it/known_hosts /etc/radiology-it/runtime.json
chmod 640 /etc/radiology-it/tunnel-key /etc/radiology-it/known_hosts /etc/radiology-it/runtime.json
chown root:www-data /etc/radiology-it/*.htpasswd
chmod 640 /etc/radiology-it/*.htpasswd
grep -q '^192.168.178.10 radiology.demo' /etc/hosts || echo '192.168.178.10 radiology.demo' >> /etc/hosts
grep -q '^192.168.178.10 radiology.demo' /etc/cloud/templates/hosts.debian.tmpl || echo '192.168.178.10 radiology.demo' >> /etc/cloud/templates/hosts.debian.tmpl
update-ca-certificates >/dev/null
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/radiology-it /etc/nginx/sites-enabled/radiology-it
nginx -t
systemctl daemon-reload
systemctl enable --now radiology-tunnel.service radiology-observability.service nginx
systemctl restart nginx radiology-observability.service
systemctl is-active radiology-tunnel.service radiology-observability.service nginx
'''
    run(*ssh,'sudo -n bash -s',input=install.encode())
    hosts=pathlib.Path('/etc/hosts');entry='192.168.178.11 doctor.radiology.demo it.radiology.demo'
    if entry not in hosts.read_text():hosts.write_text(hosts.read_text()+'\n'+entry+'\n')
    hospital=json.loads((H/'hospital-state.json').read_text())['accounts']['radiologist']
    handout=ROOT/'.private/HOSPITAL-DEMO-ACCESS.txt'
    handout.write_text('Doctor workstation: https://doctor.radiology.demo/worklist/\nDoctor gateway login: '+state['doctor']['username']+'\nDoctor gateway password: '+state['doctor']['password']+'\n\nHospital records login: '+hospital['username']+'\nHospital records password: '+hospital['password']+'\n\nIT console: https://it.radiology.demo/operations/\nIT login: '+state['it']['username']+'\nIT password: '+state['it']['password']+'\n\nDemo access only. Browser HTTP authentication lasts until the browser session is closed. Native case history is shared inside this dedicated practice workspace.\n')
    handout.chmod(0o600);os.chown(handout,1000,1000)
    out=ROOT/'docs/evidence/hospital-deployment';out.mkdir(parents=True,exist_ok=True)
    (out/'deployment.json').write_text(json.dumps({'it_vm':'kauvery-it','ip':'192.168.178.11','doctor_origin':'https://doctor.radiology.demo','it_origin':'https://it.radiology.demo','native_execution':'existing restricted kauvery-demo host workstations','transport':'SSH key restricted to two loopback native endpoints','doctor_native_scopes':state['doctor_native']['session']['scopes'],'it_native_scopes':state['it_native']['session']['scopes'],'telemetry_excludes_patient_text':True,'private_handout':'.private/HOSPITAL-DEMO-ACCESS.txt'},indent=2)+'\n')
    if old_sessions:
        token=management_token()
        for session_id in old_sessions:
            req=urllib.request.Request('http://127.0.0.1:8799/api/auth/sessions/'+session_id,method='DELETE',headers={'Authorization':'Bearer '+token})
            urllib.request.urlopen(req).close()
        state.pop('pending_rotation',None)
        (P/'gateway-secrets.json').write_text(json.dumps(state,indent=2))
    print('Installed HTTPS gateway, role-separated native sessions, SSH transport and operational monitoring; credentials saved privately.')

if __name__=='__main__': main()
