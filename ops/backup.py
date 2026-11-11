"""Safe logical backup. Password supplied by Docker container environment, never CLI."""
import datetime,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
BACKUPS=ROOT/'backups'
BACKUPS.mkdir(exist_ok=True)
name='admissions-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.dump'
target=BACKUPS/name
cmd=['docker','compose','exec','-T','db','sh','-ec','exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc']
with target.open('wb') as f:
    p=subprocess.run(cmd,cwd=ROOT,stdout=f,stderr=subprocess.PIPE)
if p.returncode or target.stat().st_size<100:
    target.unlink(missing_ok=True)
    print(p.stderr.decode(errors='replace'),file=sys.stderr)
    sys.exit(1)
print('BACKUP_WRITTEN',target,'bytes',target.stat().st_size)
