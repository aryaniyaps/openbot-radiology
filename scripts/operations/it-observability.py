#!/usr/bin/env python3
"""IT-only operational telemetry. Never persist prompts, images or case text."""
import datetime, json, os, shutil, sqlite3, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATE = Path(os.environ.get('RADIOLOGY_IT_STATE', '/var/lib/radiology-it'))
CONFIG = Path(os.environ.get('RADIOLOGY_IT_CONFIG', '/etc/radiology-it/runtime.json'))
LATEST = {}; LOCK = threading.Lock()

def request(path):
    config = json.loads(CONFIG.read_text())
    q = urllib.request.Request('http://127.0.0.1:18799/api/'+path,
        headers={'Authorization':'Bearer '+config['admin_token']})
    with urllib.request.urlopen(q,timeout=8) as f: return json.load(f)

def collect():
    state={'at':time.time(),'native_up':False,'hospital_up':False,'pacs_up':False,
        'studies':0,'instances':0,'busy':0,'waiting':0,'roles':[],
        'disk_free_gib':round(shutil.disk_usage(STATE).free/1024**3,2),'alerts':[]}
    config=json.loads(CONFIG.read_text())
    state['native_session_days_remaining']=round((config['native_session_expiry_unix']-time.time())/86400,1)
    if state['native_session_days_remaining']<7:state['alerts'].append('Native gateway sessions expire within seven days; check host session renewal')
    if config.get('tls_cert_expiry_unix'):
        state['tls_cert_days_remaining']=round((config['tls_cert_expiry_unix']-time.time())/86400,1)
        if state['tls_cert_days_remaining']<21:state['alerts'].append('Gateway TLS expires within 21 days; check host gateway maintenance')
    try:
        bots=request('bots')['bots']; state['native_up']=True
        for b in bots:
            # Store status and configured provider only, never messages/titles.
            state['roles'].append({'name':b['name'],'model':b.get('modelSelection'),
                'busy':bool(b.get('busy')),'waiting':bool(b.get('waitingForTeammates')),
                'auto_approve':bool(b.get('autoApprove')),'computer':b.get('computer')})
        state['busy']=sum(x['busy'] for x in state['roles'])
        state['waiting']=sum(x['waiting'] for x in state['roles'])
    except Exception: state['alerts'].append('OpenMausBot unavailable; check the execution host and tunnel')
    try:
        state['hospital_up']=urllib.request.urlopen('https://radiology.demo/openmrs/ws/rest/v1/session',timeout=8).status==200
    except Exception: state['alerts'].append('Hospital records unavailable')
    try:
        studies=json.load(urllib.request.urlopen('https://radiology.demo/dicomweb/studies',timeout=8))
        state['studies']=len(studies);state['instances']=sum(int(x['00201208']['Value'][0]) for x in studies);state['pacs_up']=True
    except Exception: state['alerts'].append('Imaging archive unavailable')
    if state['disk_free_gib']<2:state['alerts'].append('IT guest disk reserve below 2 GiB')
    state['healthy']=all(state[k] for k in ['native_up','hospital_up','pacs_up']) and not state['alerts']
    return state

def monitor():
    STATE.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(STATE/'telemetry.sqlite') as db:
        db.execute('CREATE TABLE IF NOT EXISTS samples (at REAL PRIMARY KEY, data TEXT NOT NULL)')
    while True:
        state=collect()
        with LOCK: LATEST.clear(); LATEST.update(state)
        with sqlite3.connect(STATE/'telemetry.sqlite') as db:
            db.execute('INSERT OR REPLACE INTO samples VALUES (?,?)',(state['at'],json.dumps(state)))
            db.execute('DELETE FROM samples WHERE at < ?',(time.time()-30*86400,))
        time.sleep(20)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]
        with LOCK: state=dict(LATEST)
        if path in ['/operations/api/status','/operations/health']:
            self.reply(json.dumps(state).encode(),'application/json',200 if path.endswith('status') or state.get('healthy') else 503)
        elif path=='/operations/api/history':
            with sqlite3.connect(STATE/'telemetry.sqlite') as db:
                samples=[json.loads(x[0]) for x in db.execute('SELECT data FROM samples ORDER BY at DESC LIMIT 180')][::-1]
            self.reply(json.dumps(samples).encode(),'application/json')
        elif path=='/operations/metrics':
            values={k:int(state.get(k,0)) for k in ['native_up','hospital_up','pacs_up','studies','instances','busy','waiting']}
            self.reply(''.join(f'radiology_{k} {v}\n' for k,v in values.items()).encode(),'text/plain')
        elif path in ['/operations/','/operations/index.html']:
            self.reply(Path('/opt/radiology-it/operations.html').read_bytes(),'text/html')
        else: self.reply(b'Not found','text/plain',404)
    def reply(self,body,mime,status=200):
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args): pass

if __name__=='__main__':
    threading.Thread(target=monitor,daemon=True).start()
    ThreadingHTTPServer(('127.0.0.1',9050),Handler).serve_forever()
