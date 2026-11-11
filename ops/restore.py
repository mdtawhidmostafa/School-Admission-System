"""Restore ONLY into a separate already created test DB; never overwrite admissions."""
import pathlib,subprocess,sys,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
if len(sys.argv)!=3 or not re.fullmatch(r'[a-z][a-z0-9_]{2,50}',sys.argv[2]) or sys.argv[2]=='admissions':
    sys.exit('Usage: python ops/restore.py <backup.dump> <non-production-test-db-name>')
path=pathlib.Path(sys.argv[1]).resolve()
if not path.is_file() or path.suffix!='.dump': sys.exit('A valid .dump file is required')
name=sys.argv[2]
# Restrict restore to a database name explicitly provided; never delete or recreate a database.
cmd=['docker','compose','exec','-T','db','sh','-ec',f'exec pg_restore -U "$POSTGRES_USER" -d "{name}" --no-owner --no-privileges']
with path.open('rb') as inp:
    run=subprocess.run(cmd,stdin=inp,cwd=ROOT)
sys.exit(run.returncode)
