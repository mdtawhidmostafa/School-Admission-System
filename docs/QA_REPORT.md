# Focused Cleanup — QA Evidence

**Date:** 2026-11-10. **Baseline:** v13. **Scope:** Maintainability and safe refactoring; not a production release certification.

## Code changes
- `Program.cs`: extracted confirm/cancel transaction handler to `Services/HoldTransitionService.cs`; extracted admin API-key authorization to `Security/AdminKeyAuthorization.cs`. Routes and required request/response shapes unchanged by intent.
- React: extracted `useAdmissionData` (independent polling, stale response protection), `useSavedField` (deduplicated local drafts), and formatted `AdminClassForm` and `ClassCard`. On student ID change, clear previous identity's displayed holds.
- Removed unused React default imports from presentational components.
- Updated source tests which depended on implementation being embedded in `main.tsx`.

## What was executed
- Python unittest discovery: captured in `QA_EVIDENCE.json`; includes actual isolated Nginx/stub gateway test.
- Static API/Compose contract and static quality gate.
- Python compilation.
- TypeScript `transpileModule` syntax diagnostics for modified frontend files (not full TS typechecking).
- Archive CRC integrity checks and file enumeration.

## Outstanding blockers
- No valid `frontend/package-lock.json` or `tests/package-lock.json`: `npm ci` cannot be certified until lockfiles generated using registry and committed. Do not fabricate resolved versions/hashes.
- `dotnet` and Docker unavailable: .NET build, PostgreSQL-backed tests, browser E2E, restart/persistence, and load/failover benchmarks were **not executed**.
- Nginx gateway-stub success does not prove backend failover or business correctness.
- Production identity verification and full HA remain outside the assignment implementation.

## Release decision
**Not certified.** The cleanup is statically validated; finish lockfile + clean build + isolated DB integration before submission.
