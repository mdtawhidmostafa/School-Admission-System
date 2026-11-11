# PDF requirements traceability — .NET 10 v9

Source: `Asst_Software_Engineer_Project_Assignment.pdf`, pages 1–5. All entries in *Implemented* column refer to source code, not successful execution.

| PDF requirement | Source location | Implemented | Execution verified here |
|---|---|---|---|
| C# .NET 8+ (upgraded to .NET 10) | `backend/SchoolAdmission.Api/*.csproj`, `backend/Dockerfile` | Yes | No (.NET unavailable) |
| PostgreSQL persistence | `docker-compose.yml`, `Data/Db.cs` | Yes | No |
| React 18+ UI | `frontend/src/main.tsx` | Yes | No (npm unavailable) |
| Docker Compose one-command launch | `docker-compose.yml` | Configured | No |
| Admin creates separate class/shift with capacity | `POST /classes` and UI | Yes | No |
| Class list/detail with total/held/confirmed/available | `GET /classes`, `GET /classes/{classId}` | Yes | No |
| Birth ID header (17 digits), no login | `Db.Student()`, UI | Yes | No |
| Hold seat | `POST /classes/{classId}/holds` | Yes | No |
| Hold state, time remaining | `GET /holds/{holdId}`, UI | Yes | No |
| Confirm simulated payment | `POST /holds/{holdId}/confirm` | Yes | No |
| Cancel hold | `DELETE /holds/{holdId}` | Yes | No |
| Student history | `GET /me/holds` | Yes | No |
| Never overbook, concurrent users | Class `FOR UPDATE` + transaction | Designed | Concurrency test unrun |
| Timeout `HOLD_DURATION_SECONDS`, default 600, auto-release | `Db.ExpireClassAsync`, `ExpiryWorker` | Yes | Expiry test unrun |
| One active or confirmed admission per student/class | Partial unique index + checks | Yes | No |
| Only owner may confirm; cannot confirm expired hold | `ChangeHoldAsync` | Yes | No |
| Idempotent confirmation | `ChangeHoldAsync` | Yes | No |
| Persistence across stop/start and down/up | Named volume | Configured | Restart test unrun |
| 4xx for malformed inputs | API handlers and validation | Designed | No |
| Everything usable from UI | `frontend/src/main.tsx` | Yes | Browser test unrun |
| Expired shown without reload; actions disabled | UI polling/countdown | Yes | Browser test unrun |
| Class seats refresh automatically | 3-second polling | Yes | Browser test unrun |
| Refresh/reopen student sees current applications | LocalStorage ID + `/me/holds` | Yes | Browser test unrun |
| At least 3 automated tests including concurrency | `tests/integration_test.py` | Yes | Not executed |
| Git history, public GitHub repository | User must push | No (requires user account) | No |
| README, ASSUMPTIONS, AI_USAGE | Repository root | Yes | Files present |
| Optional bonus: shared 17-digit student header | `Db.Student`, APIs | Yes | No |

**Not in PDF:** 3 API replicas, Nginx LB, Supabase brand stack, draft autosave, high load guarantees. These are project enhancements/constraints requested afterward. The embedded `postgres:16-alpine` is **not full Supabase**. Use the separate external Supabase override to connect an existing Supabase PostgreSQL instance.

**Unresolved requirements risks:** strict FIFO arrival order across concurrent requests (row locks provide correctness but not timestamp ordering); `frontend/package-lock.json` and `tests/package-lock.json` missing because npm registry is inaccessible in the authoring runtime; and OS-specific deployment execution remains untested.

**v9 additions:** `tests/browser_e2e.spec.cjs` includes admin validation and submitted-hold recovery on reload; `tests/integration_test.py` includes upper-bound validation checks; CI adds down/up persistence, failure log artifacts and the static quality gate. The tests are NOT runtime verified until a real Docker/CI run succeeds. For endpoint-specific incident action see `OPERATIONS_RUNBOOK.md`.


## v10 security update
Optional administrator API-key authorization is documented in `SECURITY_AND_AUTH.md`. Default `AUTH_MODE=assignment` preserves the PDF no-login behaviour; **student identity is not verified**. The new authorization script has not been run against a live stack in this environment.

## v12 verified status reminder
The eight required endpoints exist in source and the API integration suite is implemented; **live acceptance results are not yet available**. `QA_REPORT_v12.md` and `QA_EVIDENCE_v12.json` are authoritative for executed-vs-unexecuted checks. Migration checksum, independent frontend partial-error handling, three-replica QA and guarded restore test were added in v12. The deadline-ready definition remains successful clean Docker build plus actual PDF acceptance tests, not feature count.
