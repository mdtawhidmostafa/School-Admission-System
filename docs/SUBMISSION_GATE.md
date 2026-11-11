# submission gate — evidence required

**Do not label v13 certified until all mandatory gates pass.** The assignment uses no verified student login; keep `AUTH_MODE=assignment` for PDF parity, use only throwaway students in testing.

## Known blocker

`frontend/package-lock.json` and `tests/package-lock.json` are **not included**: npm registry DNS returned `EAI_AGAIN` in the build workspace. Do **not** invent lockfile metadata. Generate both on an internet-connected machine, commit both, then use `npm ci`. A clean checkout must build before submission.

## Required commands (repo root)

```sh
(cd frontend && npm install --package-lock-only --ignore-scripts && npm ci && npm run build)
(cd tests && npm install --package-lock-only --ignore-scripts && npm ci)
docker compose config --quiet
docker compose up --build -d
python3 tests/integration_test.py
python3 tests/run_isolated_qa.py
python3 tests/run_isolated_qa.py --race
python3 tests/run_isolated_qa.py --gateway-policy
python3 tests/failover_test.py
python3 tests/persistence_test.py before
docker compose down
docker compose up -d
python3 tests/persistence_test.py after
```

On Windows, run `powershell -ExecutionPolicy Bypass -File scripts/generate-lockfiles.ps1` to generate and verify both npm lockfiles.

Run `k6 run tests/k6_admission_workflow.js` **only with** `GATEWAY_URL=http://127.0.0.1:13080` and the disposable QA stack. Record environment, VUs, RPS, p95, HTTP 429/503, database CPU and pool wait, and no-oversell invariant. Record results and exit codes; do not claim a throughput figure without an actual execution.

## Rate limit semantics

Gateway limits all state-changing `/api/` routes (`POST /classes`, `POST /classes/{id}/holds`, `POST /holds/{id}/confirm`, `DELETE /holds/{id}`) by observed source IP, 10 req/s, burst 20. NAT means unrelated students may share a limit. `GET` requests are exempt. The backend has a separate process-local concurrent-work limiter (not a distributed per-user rate limit). Database locks, not Nginx, enforce seat safety. Gateway rejects overload with JSON `429 RATE_LIMITED` and `Retry-After: 1`.

## Replay and timeout semantics

Nginx does not enable `non_idempotent` upstream replay. An upstream failure can still give a client an **ambiguous outcome**: the request may have committed even if its response was lost. Before retrying `POST /classes/{id}/holds`, refresh `/me/holds` for that student; before retrying confirm/cancel inspect `/holds/{id}`. For strict exactly-once request semantics a future idempotency-key ledger is needed; current project does not provide one.

## Bottleneck and HA limitations

`SELECT ... FOR UPDATE` serializes writes to a popular class; performance bottleneck possible, not measured. Three API instances use one PostgreSQL and one Nginx: neither DB HA nor gateway HA is implemented. Database pool and gateway rate settings must be tuned based on actual p95/p99 and error counts, not the number of API replicas. Expiry workers are repeated per process; database row locks preserve correctness but add load.
