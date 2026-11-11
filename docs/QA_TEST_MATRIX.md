# v11 QA matrix and evidence status

| Suite | Scope | Required environment | Current evidence |
|---|---|---|---|
| Python unittest | Repo contract, configuration | Python | Runnable locally |
| Source static checks | Paths and code structure | Python | Runnable locally |
| API integration | All eight endpoints, ownership, validation, concurrency, repeated confirm | Running isolated Compose | NOT EXECUTED here |
| Expiry boundary | Concurrent confirm and new hold at expiry | Dedicated 4-second hold stack | NOT EXECUTED here; `python tests/run_isolated_qa.py --race` |
| Browser E2E | Draft restore, student ID, hold history | Node, Chromium, running stack | NOT EXECUTED here |
| Failover | API replica failure, Nginx routing | Docker Compose | NOT EXECUTED here |
| Backup/restore | pg_dump + pg_restore to disposable DB | Docker Compose | NOT EXECUTED here |
| Load/HA | Throughput, latency and failure behaviour | Isolated staging setup | NOT EXECUTED here |

Do not interpret source syntax checks as runtime correctness. Lockfiles are required for deterministic `npm ci`. Never put guessed PASS results in evidence reports.
