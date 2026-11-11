# Backup and restore

From project root after the database is healthy:

```sh
python3 ops/backup.py
```

Produces timestamped `backups/*.dump` (ignored by Git). Validate on an *explicitly created* disposable database (example `admissions_restore_test`):

```sh
docker compose exec db sh -c 'createdb -U "$POSTGRES_USER" admissions_restore_test'
python3 ops/restore.py backups/<filename>.dump admissions_restore_test
```

**Never** restore into the live `admissions` database. A backup is only proven recoverable after a tested restore and record/count verification. Passwords are read from the running DB container. Store backups off host with encryption, retention and access controls for real deployments.


## v12 isolated restoration certification
The test runner `python tests/run_isolated_qa.py` creates a disposable Compose project and invokes `tests/backup_restore_drill.py`. The latter refuses execution without `QA_DB_DRILL=YES` and `COMPOSE_PROJECT_NAME=admission-qa-*`; it backs up the disposable database, creates a separate test database, restores into it, compares class counts, then removes only that test database. **This is not a production DR certification**; also schedule off-host backups, encrypt them and exercise recovery against an independent host.
