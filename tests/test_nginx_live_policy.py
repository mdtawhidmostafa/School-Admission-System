"""Optional local Nginx smoke against a fake backend; no Docker/DB requirements.
Runs actual Nginx binary, verifies GET exemption, all mutation paths and 429 JSON.
Use: python tests/test_nginx_live_policy.py
"""
import contextlib
import http.server
import json
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Stub(http.server.BaseHTTPRequestHandler):
    def respond(self):
        payload=b'{"ok":true}'
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    def do_GET(self): self.respond()
    def do_POST(self): self.respond()
    def do_DELETE(self): self.respond()
    def log_message(self,*_): pass

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

class GatewayRuntime(unittest.TestCase):
    @unittest.skipUnless(shutil.which('nginx'), 'nginx binary is not installed')
    def test_live_gateway_limit(self):
        port=free_port()
        apiport=free_port()
        fake=http.server.ThreadingHTTPServer(('127.0.0.1',apiport),Stub)
        thread=threading.Thread(target=fake.serve_forever,daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)
                site=(ROOT/'frontend/nginx.conf').read_text()
                for host in ('backend','backend2','backend3'):
                    site=site.replace(host+':8080',f'127.0.0.1:{apiport}')
                site=site.replace('listen 80;',f'listen 127.0.0.1:{port};')
                (path/'site.conf').write_text(site)
                (path/'main.conf').write_text(f'pid {path}/nginx.pid;\nevents {{ worker_connections 512; }}\nhttp {{ access_log off; error_log {path}/error.log warn; include {path}/site.conf; }}\n')
                cfg=str(path/'main.conf')
                check=subprocess.run(['nginx','-t','-c',cfg],capture_output=True,text=True)
                self.assertEqual(0,check.returncode,check.stderr)
                run=subprocess.run(['nginx','-c',cfg],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
                self.assertEqual(0,run.returncode,'Nginx failed to start')
                try:
                    def request(method,uri):
                        req=urllib.request.Request(f'http://127.0.0.1:{port}{uri}',method=method)
                        try:
                            with urllib.request.urlopen(req,timeout=5) as r:return r.status,r.read()
                        except urllib.error.HTTPError as e:return e.code,e.read()
                    for _ in range(20):
                        code,_=request('GET','/api/classes')
                        self.assertEqual(200,code)
                    # One IP, four protected mutation paths.
                    paths=[('POST','/api/classes'),('POST','/api/classes/c_123/holds'),('POST','/api/holds/h_123/confirm'),('DELETE','/api/holds/h_123')]
                    seen=[]
                    for n in range(75):
                        method,uri=paths[n%len(paths)]
                        code,body=request(method,uri)
                        seen.append(code)
                        self.assertIn(code,(200,429),body)
                        if code==429:
                            self.assertEqual('RATE_LIMITED',json.loads(body)['code'])
                    self.assertIn(429,seen,'Mutation throttle did not activate')
                    self.assertEqual(200,request('GET','/api/classes')[0])
                finally:
                    subprocess.run(['nginx','-s','stop','-c',cfg],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        finally:
            fake.shutdown()
            fake.server_close()

if __name__=='__main__': unittest.main(verbosity=2)
