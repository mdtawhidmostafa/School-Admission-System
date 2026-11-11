# Assumptions and rationale

1. **Class-shift model:** Each independently seat-limited class/shift is one `classes` row (`Class 6 - Morning Shift`, `Class 6 - Day Shift`). This matches the provided API rather than introducing a shift entity.
2. **Identity:** An `X-Student-Id` HTTP header containing exactly 17 ASCII digits identifies a student for the assignment. No login is required. In a real system, unverified birth registration numbers are not secure authentication.
3. **Time interval:** A hold is active only while `expires_at > clock_timestamp()` on the database. Exactly at expiry it cannot be confirmed. The default duration is 600 seconds, configured using `HOLD_DURATION_SECONDS`; all stored timestamps are UTC.
4. **Seat allocation order:** PostgreSQL acquisition order of a given class row lock defines effective first-come-first-served order. This guarantees no overselling, not strict arrival-order fairness across different network connections.
5. **Duplicate policy:** A student may have at most one `HELD` or `CONFIRMED` row per class; cancelled and expired attempts remain in history, allowing another attempt. A partial unique index enforces the rule on persisted statuses; expired holds are reconciled before a replacement is inserted.
6. **State transitions:** Only an active `HELD` row may transition to `CONFIRMED` or `CANCELLED`. `EXPIRED`, `CANCELLED`, and `CONFIRMED` are terminal. A second confirm of an already confirmed hold succeeds without adding capacity usage. Repeated cancel on an already cancelled hold returns 204.
7. **Cancel after confirmation:** Reject with 409; confirmed admission cannot be refunded or cancelled by the assignment's simplified endpoint.
8. **Payment:** POST confirm simulates successful fee collection as explicitly allowed; no financial transaction, receipt or gateway is implemented.
9. **Expired seats:** A background worker reconciles expired rows every ~3 seconds; mutations also reconcile expiry transactionally. Reads compute effective expiry and availability immediately, without requiring a cleanup tick.
10. **Admin authorization:** Not included because the brief says no login. Class creation is not protected in this demonstration; do not reuse this policy in a deployed system.
11. **Error responses:** Validation failures use 400, unknown resources use 404, capacity/duplicate/state conflicts use 409, wrong student owner uses 403 and successful delete uses 204. JSON error bodies use the `error` property.
12. **IDs and data migration:** Class IDs use `c_` followed by 32 hex GUID digits, hold IDs use `h_` similarly. Schema auto-initialization at launch enables Docker-only startup. Production deployment would use controlled migrations and secrets management.
13. **Polling:** UI polls every 3 seconds and shows a second-by-second countdown. The API/database determine real expiry; the browser countdown is only visual guidance.
14. **Persistence:** Docker named PostgreSQL volume survives ordinary `docker compose down`; `down -v` is explicitly excluded, because it deletes volumes by design.

15. **Overload behavior:** Nginx rate-limits reservation/confirmation routes by source IP in both deployment modes; this can affect multiple legitimate users behind one NAT. Backend process-local concurrency limits and PostgreSQL connection pool bounds prevent uncontrolled resource growth but do not imply a throughput guarantee.
16. **Optional scaling:** Option B routes to three API instances sharing one database. Each instance uses the same transactional lock protocol; the database and gateway are still single points of failure. No HA claim is made.
