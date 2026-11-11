# Operations Runbook — School Admission System v9

> Audience: reviewers, maintainers and on-call engineers. Applies to the five-service local Docker Compose stack. **The assignment-specific identity header is not production authentication.**

## 1. Components and ownership

| Service | Responsibility | Failure symptom | Immediate action |
|---|---|---|---|
| `frontend` | Nginx UI, routing, admission rate limit | Website unavailable / 502 | `docker compose logs --tail=100 frontend`; check 3 API readiness, then `docker compose restart frontend` if needed |
| `backend`, `backend2`, `backend3` | Stateless .NET 10 admission API, background expiry | 502/503, failed `/readyz` | `docker compose logs --tail=100 backend2`; check database health; restart affected replica only |
| `db` | Durable source of truth, transactions, row locks | 503 / SQL errors / hold delays | Check `docker compose ps db`, logs, storage and connection count; **never delete volume** |
| `qa` (profile) | Optional integration verification | Test failure | Inspect test output, separate code error from test-environment failures |

## 2. One-time prerequisite checks

- Docker Desktop (Windows/macOS, Linux containers) or Docker Engine + Compose v2 (Linux).
- Allocate CPU/RAM/disk suitable for 3 API services + PostgreSQL; no capacity promise without benchmarks.
- Network required for FIRST image build, .NET NuGet restore and `npm ci`.
- **Release blocker**: `frontend/package-lock.json` and `tests/package-lock.json` must be generated with trusted npm on an online machine, reviewed, and committed. They are intentionally not fabricated.
- Do not publish `.env` secrets or student data.

## 3. Prepare, build, start

```sh
# From project root
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
# Set a unique local POSTGRES_PASSWORD in .env
# First time only, with Node/npm available to create lockfiles:
cd frontend && npm install --package-lock-only && npm ci && npm run build && cd ..
cd tests && npm install --package-lock-only && npm ci && cd ..
# Then:
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Expected: `db`, `backend`, `backend2`, `backend3`, `frontend` running. `/api/classes` returns JSON array, `/readyz` from direct API returns `{ "status":"ready" }`. Browser UI at http://localhost:3000. Test secrets MUST NOT be committed.

### Why startup may fail

| Symptom / code | Likely cause | Action / verification |
|---|---|---|
| `npm ci` says lockfile missing | Dependency lockfile not committed | Generate using commands above on online host, review `npm ci`, commit; do not weaken Dockerfile with `npm install` fallback |
| `npm EAI_AGAIN` / DNS | Registry not resolvable | Verify internet, DNS, proxy and npm registry; retry when accessible; do NOT invent dependency hashes |
| `dotnet restore` fails | NuGet unavailable or package mismatch | Inspect full `docker compose build backend --progress=plain`; network/NuGet version first |
| Docker port 3000 or 8080 busy | Other process listening | Set `FRONTEND_PORT`/`BACKEND_PORT` in `.env` before start |
| API startup SQL error | DB unhealthy, credentials, migration conflict | Inspect `db` logs and API logs; verify DB via `pg_isready`, schema migrations; do not blindly recreate DB |
| API `/readyz` 503 | DB connectivity failure | Inspect db logs/health, credentials, pool saturation and network |
| Browser `/api` 502 | No healthy API upstream or stale gateway upstream | Inspect 3 backend statuses; check `frontend` logs; restart gateway after re-created API containers |
| 429 on Hold/Confirm | Gateway or API overload protection | Wait, respect backoff; verify duplicate request logic; reduce abusive retry volume |
| 409 on Hold | Seat exhausted / already active | Display user-facing message; verify `/classes/{id}` and `/me/holds` |
| 409 on Confirm | Expired/cancelled hold | Re-apply for an available seat; never force the database to CONFIRMED |
| 400 on request | Invalid student ID, class name, seat count, IDs, JSON | Validate 17-digit numeric ID, 1–1,000,000 seats, max 150-char name |
| 403 on Confirm/Cancel | Student header differs from hold owner | Use correct student identifier; do not circumvent ownership check |
| 404 | Hold/class does not exist | Re-fetch lists, check IDs |
| 503 from API | DB unavailable, contention or connection exhaustion | Inspect correlation ID, resource use and DB; retry with backoff |

## 4. Check each API safely

- `POST /classes`: expect 201 and `{id,name,totalSeats}`. 400 validation, 409 duplicate class name.
- `GET /classes`, `GET /classes/{id}`: expect 200 and counts; 400 bad ID, 404 missing class.
- `POST /classes/{id}/holds`: require `X-Student-Id` (17 ASCII digits); 201 `HELD`, 409 no capacity / duplicate active admission, 404 nonexistent class.
- `GET /holds/{id}`: 200 status `HELD|CONFIRMED|EXPIRED|CANCELLED`; 400 malformed, 404 missing.
- `POST /holds/{id}/confirm`: header required; 200 `CONFIRMED` (repeat returns 200), 403 wrong owner, 409 expired/cancelled.
- `DELETE /holds/{id}`: header required; 204 (repeat cancel returns 204), 403 wrong owner, 409 confirmed/expired.
- `GET /me/holds`: header required; 200 collection filtered by student ID.

API functions are implemented in `backend/SchoolAdmission.Api/Program.cs`; common transaction/migration methods are in `Data/Db.cs`; background expiry is in `Services/ExpiryWorker.cs`. Source inspection is not proof of live success.

## 5. Data persistence and backup policy

```sh
docker compose stop
docker compose start
# or
docker compose down
docker compose up -d
```

A Docker named volume `admissions_data` persists across those commands. **NEVER** use `docker compose down -v` during ordinary operations; it removes project-owned volumes. Snapshot/backup and restore need a separate tested procedure before any real deployment. `pg_dump` example (development only):

```sh
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > admissions.backup
```

Keep backup files secure; they may include student identifiers. An actual restore test must be performed in an isolated database. Do not attempt to restore over an active admissions database.

Expired holds after downtime correctly remain historical rows while their *effective* status becomes EXPIRED; losing an active hold after its deadline is expected behavior, **not data loss**.

## 6. QA commands and interpretation

```sh
python3 tests/quality_gate.py               # source checks, not runtime
python3 tests/preflight.py                  # optional host preflight; needs Python
# after successful Docker build:
docker compose --profile qa run --rm qa     # API and concurrency tests
docker compose --profile qa run --rm qa python gateway_smoke.py
python3 tests/failover_test.py              # host Docker CLI required
python3 tests/evidence_runner.py            # saves QA_EVIDENCE.json
```

For expiry test use a **separate test deployment** with matching `HOLD_DURATION_SECONDS=3`, `TEST_HOLD_SECONDS=3`; do not modify a live environment's duration mid-test. For Playwright, generate `tests/package-lock.json`, run `npm ci` and install the browser. CI in `.github/workflows/verify.yml` executes build, API, persistence, failover and E2E checks on Ubuntu when dependencies are available.

Any failed mandatory test is a release blocker. Save actual logs and exit codes. Never mark a test PASS based on its existence in source.

## 7. Load and failure management

`tests/load_smoke.py` is bounded smoke testing (throughput, p95, statuses), not a claim that a host supports 10,000 users. Three stateless APIs cannot eliminate the single Postgres and gateway points of failure. `least_conn` balances backend connections, not FIFO application ordering; row locks protect capacity. Tune limits based on measured bottlenecks. Do not increase DB pool sizes indiscriminately: total active connections scale with replica count.

## 8. Operational security limits

- `X-Student-Id` is a take-home contract, **not secure identity verification**.
- No admin authentication by assignment requirement: cannot expose this public API to real students.
- Use TLS, secrets manager, separate database roles, authenticated student/admin sessions, backups, metrics and incident response before real production use.
- `localStorage` stores a student identifier in a browser; avoid shared/public devices and never place secrets in browser storage.


## v10 security update
Optional administrator API-key authorization is documented in `SECURITY_AND_AUTH.md`. Default `AUTH_MODE=assignment` preserves the PDF no-login behaviour; **student identity is not verified**. The new authorization script has not been run against a live stack in this environment.
