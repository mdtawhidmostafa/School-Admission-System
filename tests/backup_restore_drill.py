"""Execute against a disposable QA Compose project only. Verifies pg_dump -> pg_restore.
Requires QA_DB_DRILL=YES and project name admission-qa-*, never the default stack.
"""
import os,subprocess,sys,uuid
project=os.getenv('COMPOSE_PROJECT_NAME','')
if os.getenv('QA_DB_DRILL')!='YES' or not project.startswith('admission-qa-'):
    sys.exit('REFUSED: QA_DB_DRILL=YES and COMPOSE_PROJECT_NAME=admission-qa-* required')

def compose(*args,input=None):
    p=subprocess.run(['docker','compose','-p',project,*args],input=input,capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.decode(errors='replace')[-1500:])
    return p.stdout

def db_script(script,input=None):
    return compose('exec','-T','db','sh','-ec',script,input=input)

name='qa_restore_'+uuid.uuid4().hex[:12]
backup=db_script('exec pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"')
assert len(backup)>100,'Invalid backup data'
db_script('exec createdb -U "$POSTGRES_USER" '+name)
try:
    db_script('exec pg_restore -U "$POSTGRES_USER" --no-owner --no-privileges -d '+name,input=backup)
    source=db_script('exec psql -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM classes"').strip()
    restored=db_script('exec psql -At -U "$POSTGRES_USER" -d '+name+' -c "SELECT count(*) FROM classes"').strip()
    assert source==restored,(source,restored)
    print('PASS QA backup/restore; class rows:',restored.decode(),'archive bytes:',len(backup))
finally:
    db_script('exec dropdb -U "$POSTGRES_USER" '+name)
