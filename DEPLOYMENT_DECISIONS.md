# Deployment choices

**Default:** three API instances + Nginx + persistent PostgreSQL in one Docker Compose stack. This is a deployable **container configuration**, not a high availability guarantee: single gateway, shared DB and single host remain failure points.

**Supabase:** existing official Supabase installation can be used as the database through `deploy/supabase-external.yml`. The default internal `postgres:16-alpine` is NOT branded Supabase or a complete Supabase deployment. Full self-hosted Supabase requires the official multi-service stack and resource capacity.

**Concurrency:** `SELECT ... FOR UPDATE` locks one class row while creating or transitioning Holds. This protects seat counts but serializes hot classes. Nginx distribution does not guarantee FIFO. Load-test queue wait time, p95, error rates, and PostgreSQL connections before announcing throughput figures.
