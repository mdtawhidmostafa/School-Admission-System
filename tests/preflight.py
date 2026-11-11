"""Cross-platform host preflight; requires Python 3.10+ and Docker Compose v2."""
from pathlib import Path
import subprocess,sys,socket
root=Path(__file__).resolve().parents[1]
checks=[('docker',['docker','version','--format','{{.Server.Version}}']),
        ('compose',['docker','compose','version']),
        ('compose_config',['docker','compose','config','--quiet'])]
failed=[]
for name,command in checks:
    try:
        result=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=25)
        print(('PASS' if result.returncode==0 else 'FAIL'),name)
        if result.returncode: failed.append(name);print(result.stderr[-900:])
    except (OSError,subprocess.TimeoutExpired) as exc:
        failed.append(name);print('FAIL',name,str(exc))
for name in ('frontend/package-lock.json','tests/package-lock.json'):
    if (root/name).is_file():print('PASS',name)
    else:failed.append(name);print('BLOCKED missing',name)
for port in (3000,8080):
    with socket.socket() as s:
        try: s.bind(('127.0.0.1',port));print('PASS available host port',port)
        except OSError:print('WARN occupied host port',port,'(change FRONTEND_PORT / BACKEND_PORT if needed)')
sys.exit(1 if failed else 0)
