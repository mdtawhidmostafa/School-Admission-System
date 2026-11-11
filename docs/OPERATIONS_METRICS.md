# Operational observability

The HTTP middleware emits structured logs with `RequestId`, HTTP method, path, response status and duration (ms). It does not log the student ID or admin API key. `X-Request-Id` echoes the request correlation ID. `/healthz` checks process liveness; `/readyz` checks DB connectivity.

**Instrumentation:** `HttpTelemetry` publishes request counters and duration histograms through .NET `Meter` (`SchoolAdmission.Http`). **Limitation:** No Prometheus/OpenTelemetry exporter, dashboard, alerting or central log store is installed. These require a collector and measured operational environment; logs alone do not make production observability complete.

For failures, record UTC timestamp + request ID, inspect `docker compose logs --tail=200 backend backend2 backend3 frontend db`, verify `/readyz`, and inspect active DB transactions. See `OPERATIONS_RUNBOOK.md`.
