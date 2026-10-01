#!/usr/bin/env python3
"""Local native OMB entry point that always requires a paired session.

No UI or authorization replacement: forwarding headers make the upstream
apply its native remote-session checks instead of desktop owner trust.
The separate IT gateway provides TLS and forwards its client-scoped session
to this loopback boundary. Native application authorization remains upstream.
"""
import http.client
import os
import posixpath
import json
import re
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOP = {'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
       'te', 'trailer', 'transfer-encoding', 'upgrade'}
STYLE = Path(__file__).resolve().parents[2] / 'config/openmausbot/doctor-workspace.css'
TASK_ROUTE = re.compile(r'^/api/(?:bots|groups)/[\w-]+/tasks(?:/[\w-]+)?$')
TASK_FIELDS = {'title', 'projectId', 'pinnedMessageId', 'archivedAt', 'pinned', 'snoozedUntil'}


class Proxy(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def forward(self):
        host = self.headers.get('Host', '')
        if host not in ('localhost:8798', '127.0.0.1:8798'):
            self.send_error(403, 'Local doctor entry point only')
            return
        origin = self.headers.get('Origin')
        allowed_origins = {'http://localhost:8798', 'http://127.0.0.1:8798',
                           os.environ.get('DOCTOR_PUBLIC_ORIGIN', 'https://doctor.radiology.demo')}
        if origin and origin not in allowed_origins:
            self.send_error(403, 'Unrecognized doctor origin')
            return
        length = int(self.headers.get('Content-Length', '0'))
        if length > 40 * 1024 * 1024 or self.headers.get('Transfer-Encoding'):
            self.send_error(413)
            return
        body = self.rfile.read(length) if length else None
        # OMB 0.1.91 exposes thread model/approval updates to client scope.
        # The doctor entry point permits organization fields only, and never
        # forwards execution-setting overrides. Owner routes remain upstream.
        path = posixpath.normpath(urllib.parse.unquote(self.path.split('?', 1)[0]))
        if path.endswith('/always-allow'):
            self.send_error(403, 'Persistent permissions are managed by IT')
            return
        if self.command == 'POST' and path.endswith('/respond') and body:
            try:
                reply = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                self.send_error(400, 'Invalid JSON')
                return
            if not isinstance(reply, dict) or reply.get('always'):
                self.send_error(403, 'Only one-time review is permitted in the doctor workspace')
                return
        if self.command in {'POST', 'PATCH'} and TASK_ROUTE.fullmatch(path) and body:
            try:
                payload = json.loads(body)
            except (ValueError, UnicodeDecodeError):
                self.send_error(400, 'Invalid JSON')
                return
            if not isinstance(payload, dict) or set(payload) - TASK_FIELDS:
                reply = json.dumps({'error': 'Doctor workspace: execution settings are managed by your administrator'}).encode()
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(reply)))
                self.end_headers()
                self.wfile.write(reply)
                return
        headers = {k: v for k, v in self.headers.items()
                   if k.lower() not in HOP
                   and not k.lower().startswith(('x-forwarded-', 'x-openmausbot-'))
                   and k.lower() != 'forwarded'}
        headers.update({'X-Forwarded-For': self.client_address[0],
                        'X-Forwarded-Proto': 'http', 'Accept-Encoding': 'identity'})
        if origin:
            # Upstream sees the loopback tunnel's Host and protocol. Validate
            # the actual public origin above before translating it for native
            # same-origin validation; never forward an arbitrary origin.
            headers['Origin'] = 'http://' + host
        connection = http.client.HTTPConnection('127.0.0.1', 8799, timeout=3600)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            html = None
            if 'text/html' in response.getheader('Content-Type', '') and self.command == 'GET':
                html = response.read().replace(b'</head>',
                    b'<style id="doctor-workspace">' + STYLE.read_bytes() + b'</style></head>')
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in HOP and not (html is not None and key.lower() in {'content-length', 'etag'}):
                    self.send_header(key, value)
            if html is not None:
                self.send_header('Content-Length', str(len(html)))
                self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            if self.command != 'HEAD':
                if html is not None:
                    self.wfile.write(html)
                else:
                    while chunk := response.read1(65536):
                        self.wfile.write(chunk)
                        self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            connection.close()
            self.close_connection = True

    do_GET = do_POST = do_PATCH = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = forward

    def log_message(self, fmt, *args):
        # Pairing codes can appear in query strings; never log request URLs.
        pass


if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8798), Proxy).serve_forever()
