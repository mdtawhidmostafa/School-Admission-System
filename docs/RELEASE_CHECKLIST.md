# Release Checklist — v9 (all unchecked until verified on a real host)

- [ ] Generate and commit authentic `frontend/package-lock.json` and `tests/package-lock.json` on an internet-connected host.
- [ ] Clean checkout: `npm ci` + frontend build pass; dotnet restore/publish pass.
- [ ] `docker compose config --quiet` passes and `docker compose up --build -d` starts all five containers.
- [ ] All three API replicas respond `200` on `/readyz`; gateway responds on `/api/classes`.
- [ ] All 8 required API routes and exact JSON contracts pass.
- [ ] Negative test coverage: invalid input 4xx, duplicate application 409, wrong owner 403.
- [ ] Concurrency and parallel-confirm tests pass without overselling or double counting.
- [ ] Controlled hold expiry test passes; seat becomes available.
- [ ] Browser tests pass: invalid class form, admin draft recovery, Student ID recovery, submitted application refresh.
- [ ] `docker compose down` then `docker compose up -d` preserves class and hold records.
- [ ] One API replica stopped: gateway continues via remaining replicas; restart successful.
- [ ] Load-smoke results saved; no unverified 10,000-user capacity claims.
- [ ] Document network, dependency, startup and database failure behavior and recovery instructions.
- [ ] No credentials or confidential source PDF in public repo; AI_USAGE updated and accurate.
- [ ] Final GitHub Actions green with actual logs; link to verified commit and release evidence.

## v12 additions (unchecked until executed)
- [ ] `python tests/run_isolated_qa.py` passes all eight API tests, cross-replica consistency and isolated backup/restore drill.
- [ ] `python tests/run_isolated_qa.py --race` passes expiry-boundary competition in dedicated 4-second test stack.
- [ ] Migration checksum mismatch is rejected in a disposable database (do not edit applied migration files in real deployments).
- [ ] Shared API error schema (`error/code/requestId`) and frontend independent-failure handling verified in runtime/browser tests.
- [ ] `QA_EVIDENCE_v12.json` checked for actual exit codes and unresolved blockers; do not use static checks as runtime proof.
