# Load test and availability plan (unverified)

## k6 / measured stages
Test `/classes` separately from `/classes/{id}/holds`; collect requests/s, throughput, p50/p95/p99 latency, HTTP 429/503, CPU, memory, DB locks and connection utilization. Configure arrival-rate rather than equating 10,000 *connected users* with 10,000 requests/second. Do not target public services or production databases.

## Invariants
- `heldSeats + confirmedSeats <= totalSeats` for each class under every load profile.
- Exactly at most `capacity` successful competing holds; expired holds excluded.
- Repeated confirmation increments confirmed count at most once.

## Availability
3 API replicas tolerate a single API process failure in principle but share Nginx and one Postgres primary as SPOFs. A real HA deployment requires redundant ingress, health-checking, failover for DB, backup PITR and restore drills. Load balancing is not strict arrival-order FIFO; document a fairness policy separately.

## Safe execution
Use `python tests/run_isolated_qa.py` for normal integration coverage, not against a live tenant database. Run further load tests against a separately provisioned staging stack only. Reconcile 429 rejects with admission fairness policy.

Example read-only k6 smoke: `GATEWAY_URL=http://127.0.0.1:13080 k6 run tests/k6_load_smoke.js`. This asserts an illustrative latency target, **not a measured result**. Do not run on public infrastructure without explicit authorization.


## v12 acceptance metrics
Measure separate read and write workloads: 100/1000/5000 simulated clients, RPS, p50/p95/p99 latency, HTTP 429 vs 5xx, DB active connections, lock waits, request queue and CPU/RAM. Do not promise capacity before tests. Retry-after must be honored; monitor retries and avoid stampedes.

Three API replicas share a single database, so Postgres is still an SPOF. Nginx is an SPOF as well. A real HA roadmap requires an external health-checked gateway pair/managed LB, primary/standby database with tested failover, durable backups, and defined RPO/RTO. Strict request-arrival FIFO is not guaranteed by row locking; document the fairness policy separately.
