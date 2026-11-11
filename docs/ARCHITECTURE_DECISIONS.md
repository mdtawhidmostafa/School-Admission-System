# Architecture Decision Records (ADRs)

## ADR-001 — PostgreSQL is the source of truth
**Decision:** Lock the admission class row within a database transaction and reconcile expired holds before inserting another hold. All API replicas share one database.
**Why:** Application-process locks would not coordinate three API replicas; a cache alone cannot guarantee admission consistency.
**Trade-off:** Popular classes can serialize and slow down. Adding APIs does not remove this database contention. **Evidence required:** real concurrent hold tests against PostgreSQL.

## ADR-002 — Three .NET 10 API replicas + Nginx
**Decision:** Stateless identical replicas behind Nginx `least_conn`; the gateway handles browser routes and `/api` proxying.
**Why:** Demonstrates horizontal application scaling within one Compose project, as requested.
**Trade-off:** Nginx and PostgreSQL remain single points of failure. Passive failover can produce transient 502s. **Evidence required:** `tests/failover_test.py`.

## ADR-003 — Expiry uses database time
**Decision:** A hold is active only while `expires_at > clock_timestamp()`. Transactional lazy expiry makes seats reusable even if the worker stops.
**Trade-off:** UI timers are approximate; server/database status governs confirmation.

## ADR-004 — Idempotent confirmation
**Decision:** Repeated successful confirmation of the same hold returns success without creating another seat allocation.
**Why:** HTTP retries, lost responses, and double-clicks should not allocate another seat.

## ADR-005 — Focused modular monolith
**Decision:** Do not introduce Redis, Kafka, RabbitMQ or a distributed queue for this take-home assignment.
**Why:** They increase operating complexity without fixing correctness; PostgreSQL transactions already address the key consistency requirement.

## ADR-006 — Identity and fair ordering are documented limitations
**Decision:** Keep the PDF-required `X-Student-Id` 17-digit header; do not pretend it authenticates the user. First-come-first-served is based on successful serialized DB seat allocation, not strict network arrival FIFO.
**Production alternative:** Verified authentication and an explicit admission ordering/queue policy. Do not deploy with real student data as-is.

## ADR-007 — Supabase scope
**Decision:** Default stack uses a PostgreSQL container that is compatible with typical Supabase PostgreSQL connections, not Supabase services. An external Supabase database override exists. Do not label the default stack "full Supabase".

## ADR-008 — Reproducible frontend builds and honest release gates (v9)
**Decision:** Dockerfile uses `npm ci` only. A genuine reviewed lockfile is mandatory; do not fall back to a floating dependency resolution at build time.
**Reason:** The same commit should resolve the same transitive dependencies. No lockfile is included until npm registry access permits generation and verification.
**Trade-off:** A first-time build deliberately fails instead of silently installing varying versions. This remains a P0 task before submission.

## ADR-009 — Operational evidence and troubleshooting
**Decision:** Document which component handles each failure, distinguish HTTP 400/403/404/409/429/503, and capture actual CI/build logs.
**Reason:** Reliability depends on recoverability and diagnosis, not only feature implementation.
**Trade-off:** Adds a concise operations runbook and tests; does not imply real-world production authorization or HA.
