# Reviewer Guide — v9

## 1. Release status

Read `QA_REPORT.md` first. This is source-level implementation with unresolved dependency and runtime verification blockers. No test result is claimed without actual execution.

## 2. Prepare

Generate authentic `frontend/package-lock.json` and `tests/package-lock.json` on an online environment. See README. Copy `.env.example` to `.env` and change the development password.

## 3. Start

```sh
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Expect DB + 3 APIs + Nginx/React; use `http://localhost:3000` and `http://localhost:3000/api/classes`.

## 4. Demonstration and verification

1. Admin UI: create a class (use a unique name), check seat counts.
2. Enter 17-digit birth registration identifier; reserve one seat; check countdown.
3. Refresh browser and inspect My Applications; confirm, retry confirmation, verify only one confirmed seat.
4. Run `docker compose --profile qa run --rm qa` and `docker compose --profile qa run --rm qa python gateway_smoke.py`.
5. Run `python3 tests/failover_test.py` with host Docker and Python installed; verify Nginx can use remaining replicas during backend2 outage.
6. Run `python3 tests/persistence_test.py before`, `docker compose down`, `docker compose up -d`, then `python3 tests/persistence_test.py after`.
7. Record actual commands, timestamps, exit codes and observations. Do **not** use `down -v` for persistence verification.

## 5. Interview demo suggestions

Explain why DB row locks and shared PostgreSQL protect capacity across three APIs; why idempotent confirm handles retries; how expiry remains correct through downtime; why multiple API replicas do not remove PostgreSQL or gateway single points of failure; why strict FIFO is a separate problem; why this assignment's student header is not production authentication.

For failures and recovery actions, read `OPERATIONS_RUNBOOK.md`. For omitted/optional scope, read `ASSUMPTIONS.md` and `ARCHITECTURE_DECISIONS.md`. No confidential employer PDF belongs in the public repository.
