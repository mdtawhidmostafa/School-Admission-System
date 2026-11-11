"""Runs API QA against an isolated Compose project/database. Never removes default volumes."""
import os, subprocess, sys, pathlib, secrets
ROOT=pathlib.Path(__file__).resolve().parents[1]
PROJECT='admission-qa-'+secrets.token_hex(3)
RACE='--race' in sys.argv
POLICY='--gateway-policy' in sys.argv
ENV=os.environ.copy()
ENV.update(POSTGRES_PASSWORD=secrets.token_hex(20), POSTGRES_DB='admissions_qa',
  FRONTEND_PORT='13080', BACKEND_PORT='18080', HOLD_DURATION_SECONDS='4' if RACE else '20', TEST_HOLD_SECONDS='4' if RACE else '20')
ENV['API_URL']='http://127.0.0.1:18080'
ENV['GATEWAY_URL']='http://127.0.0.1:13080'
COMPOSE=['docker','compose','-p',PROJECT]
def execute(*args,check=True):
    return subprocess.run([*COMPOSE,*args],cwd=ROOT,env=ENV,check=check)
def main():
    if not (ROOT/'frontend/package-lock.json').exists():
        print('BLOCKED: frontend/package-lock.json absent. Run npm install --package-lock-only with registry access.',file=sys.stderr)
        return 2
    try:
        execute('up','--build','-d')
        script='race_boundary_test.py' if RACE else ('gateway_policy_test.py' if POLICY else 'integration_test.py')
        run=subprocess.run([sys.executable,str(ROOT/'tests'/script)],env=ENV,cwd=ROOT,check=False)
        if run.returncode: return run.returncode
        if not RACE and not POLICY:
            # Executed in the same isolated stack, from a Python QA container.
            cross=execute('--profile','qa','run','--rm','qa','python','cross_replica_test.py',check=False)
            if cross.returncode: return cross.returncode
            drill_env=ENV.copy()
            drill_env.update(QA_DB_DRILL='YES',COMPOSE_PROJECT_NAME=PROJECT)
            restore=subprocess.run([sys.executable,str(ROOT/'tests/backup_restore_drill.py')],env=drill_env,cwd=ROOT,check=False)
            if restore.returncode: return restore.returncode
        return 0
    finally:
        # Only isolated project resources, never the user's normal database.
        execute('down','--volumes','--remove-orphans',check=False)
if __name__=='__main__': sys.exit(main())
