"""Host-side failover integration test. Requires Docker CLI, running stack.
Run: python tests/failover_test.py
This tests GET availability via Nginx during one API replica outage; not full high availability.
"""
import subprocess, time, urllib.request, urllib.error, json, os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GATEWAY=os.environ.get('GATEWAY_URL','http://localhost:3000').rstrip('/')

def compose(*args):
    return subprocess.run(['docker','compose',*args],cwd=ROOT,check=True,capture_output=True,text=True)

def probe():
    with urllib.request.urlopen(GATEWAY+'/api/classes',timeout=4) as response:
        data=json.load(response)
        assert response.status == 200 and isinstance(data,list)

if __name__=='__main__':
    stopped=False
    try:
        probe()
        compose('stop','backend2')
        stopped=True
        failures=[]
        # Nginx may momentarily attempt the down node until passive failover detects it.
        for i in range(30):
            try: probe()
            except Exception as exc: failures.append(str(exc))
            time.sleep(.25)
        assert len(failures)<=3, f'Too many gateway errors during one replica outage: {failures}'
        print(f'PASS: Nginx continued serving GET /api/classes with backend2 stopped; transient_failures={len(failures)}')
    finally:
        if stopped: compose('start','backend2')
