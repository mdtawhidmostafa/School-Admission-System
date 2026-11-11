# School Admission System

A containerized school admission management application built with
**ASP.NET Core (.NET 10), PostgreSQL 16, React, TypeScript, Nginx, and
Docker Compose**.

The application manages admission classes and student seat reservations.
It supports temporary holds, admission confirmation, cancellation,
automatic hold expiry, and concurrent seat-allocation protection.

> **Project status:** This README documents the repository configuration
> and the local checks that can be run. A successful build or test must
> be verified on the machine where the project is executed;
> configuration alone is not proof of production readiness.

## Contents

-   [Features](#features)
-   [Technology stack](#technology-stack)
-   [Architecture](#architecture)
-   [Prerequisites](#prerequisites)
-   [Local setup](#local-setup)
-   [Accessing the application](#accessing-the-application)
-   [Database access](#database-access)
-   [API reference](#api-reference)
-   [Admission workflow](#admission-workflow)
-   [Rate limiting and load
    balancing](#rate-limiting-and-load-balancing)
-   [Testing and verification](#testing-and-verification)
-   [Docker commands](#docker-commands)
-   [Configuration](#configuration)
-   [Security notes](#security-notes)
-   [Troubleshooting](#troubleshooting)
-   [Project structure](#project-structure)

## Features

-   Create and list admission classes.
-   View class capacity, held seats, confirmed seats, and available
    seats.
-   Temporarily hold a seat for a student.
-   Confirm or cancel a hold.
-   Automatically expire temporary holds.
-   Prevent seat overselling with PostgreSQL transactions and row-level
    locking.
-   Run three stateless API replicas behind an Nginx reverse proxy/load
    balancer.
-   Apply request rate limits to admission mutations.
-   Return structured API errors and request IDs.
-   Persist PostgreSQL data in a named Docker volume.
-   Optionally protect class creation with an administrator API key.

## Technology stack

  Area                            Technology
  ------------------------------- ------------------------
  Backend API                     ASP.NET Core / .NET 10
  Frontend                        React 18, TypeScript
  Frontend build                  Vite
  Database                        PostgreSQL 16
  Data access                     Npgsql
  Reverse proxy / load balancer   Nginx
  Containers                      Docker, Docker Compose
  API and QA tests                Python 3
  Browser tests                   Playwright

## Architecture

``` text
                    Browser / Client
                           |
                           v
                  Nginx Gateway :3000
                  /api routing + limits
                           |
                 least_conn load balancing
                    /      |      \
                   v       v       v
              backend  backend2  backend3
               .NET      .NET      .NET
                   \       |       /
                    \      |      /
                           v
                    PostgreSQL 16
                    Docker volume
```

-   The frontend is served by Nginx on the host's configured frontend
    port (default `3000`).
-   Requests beginning with `/api/` are proxied to the backend replicas.
    Nginx removes the `/api` prefix before forwarding the request.
-   The API replicas share one PostgreSQL database.
-   The database is the source of truth for seat allocation and hold
    state.
-   The database port is **not published to the host by default**. This
    keeps PostgreSQL accessible to the Compose services without exposing
    it on the host network.

The three API replicas and the single Nginx gateway do not make the
whole system highly available: PostgreSQL and the gateway remain single
points of failure.

## Prerequisites

Install:

-   Docker Desktop (macOS/Windows) or Docker Engine with Docker Compose
    v2 (Linux).
-   Node.js 22 or a compatible Node.js release, with npm.
-   Python 3.10+ (Python 3.12 is used by the optional Compose QA
    service).
-   Git.

Check the tools:

``` bash
docker --version
docker compose version
node --version
npm --version
python3 --version
```

The first Docker build needs network access to download the .NET and
Node dependencies/base images.

## Local setup

Run all commands from the repository root (`School-Admission-System/`).

### 1. Create the environment file

The repository includes `.env.example`. Copy it to `.env`:

``` bash
cp .env.example .env
```

On Windows PowerShell:

``` powershell
Copy-Item .env.example .env
```

Open `.env` and set a unique local database password in
`POSTGRES_PASSWORD`. Do not commit `.env`.

### 2. Generate npm lockfiles if they are missing

The Docker frontend build uses `npm ci`, which requires
`frontend/package-lock.json`. The Playwright test setup also needs
`tests/package-lock.json`.

If either lockfile is missing, generate it:

``` bash
cd frontend
npm install --package-lock-only --ignore-scripts
cd ../tests
npm install --package-lock-only --ignore-scripts
cd ..
```

Commit the generated lockfiles to Git after reviewing them. Do not
replace `npm ci` with an unpinned install in the Dockerfile.

### 3. Install dependencies and build the frontend locally (optional)

``` bash
cd frontend
npm ci
npm run build
cd ..
```

Install the Playwright test dependencies when you intend to run browser
tests:

``` bash
cd tests
npm ci
cd ..
```

### 4. Validate and start Docker Compose

``` bash
docker compose config --quiet
docker compose up --build -d
```

Check the containers:

``` bash
docker compose ps
```

Expected services:

-   `db`
-   `backend`
-   `backend2`
-   `backend3`
-   `frontend`

Wait until PostgreSQL reports healthy and the API replicas have started.

### 5. View logs

``` bash
docker compose logs --tail=100
```

Follow logs continuously:

``` bash
docker compose logs -f
```

Only the database:

``` bash
docker compose logs -f db
```

Only API replicas:

``` bash
docker compose logs -f backend backend2 backend3
```

## Accessing the application

Default local URLs:

  ------------------------------------------------------------------------------------
  Service                 URL                                  Purpose
  ----------------------- ------------------------------------ -----------------------
  Frontend                <http://localhost:3000>              React application

  Nginx API gateway       <http://localhost:3000/api>          API through the gateway

  Direct API replica      <http://localhost:8080>              Direct access to
                                                               `backend`

  Gateway readiness       <http://localhost:3000/api/readyz>   API readiness through
                                                               Nginx

  Direct API readiness    <http://localhost:8080/readyz>       API readiness without
                                                               Nginx
  ------------------------------------------------------------------------------------

Quick checks:

``` bash
curl -i http://localhost:3000/api/readyz
curl -i http://localhost:8080/readyz
curl -i http://localhost:3000/api/classes
```

A successful readiness response is HTTP `200` with:

``` json
{"status":"ready"}
```

## Database access

### Access PostgreSQL from the Docker container

PostgreSQL is available to the Compose network as service `db`. Use:

``` bash
docker compose exec db pg_isready -U admissions -d admissions
docker compose exec db psql -U admissions -d admissions
```

Inside `psql`:

``` sql
\l
\c admissions
\dt
SELECT * FROM classes;
SELECT * FROM holds;
\q
```

The default database name and user are `admissions`. If you changed the
`.env` values, use those values instead.

### Optional: connect with DBeaver or pgAdmin

The database port is not exposed to the host by default. To use a
desktop database client locally, add this under the `db:` service in
`docker-compose.yml`:

``` yaml
    ports:
      - "127.0.0.1:5432:5432"
```

Then recreate only the database container:

``` bash
docker compose up -d --force-recreate db
```

Use these connection settings in DBeaver/pgAdmin:

  Setting    Value
  ---------- -------------------------------------------------
  Host       `localhost`
  Port       `5432`
  Database   Value of `POSTGRES_DB` (default `admissions`)
  Username   Value of `POSTGRES_USER` (default `admissions`)
  Password   Value of `POSTGRES_PASSWORD` in `.env`

Binding to `127.0.0.1` keeps the database port local to your computer.
Do not publish PostgreSQL to a public interface for convenience.

## API reference

All paths below are shown relative to the Nginx gateway prefix
`http://localhost:3000/api`. The backend itself receives the path
without `/api`.

  --------------------------------------------------------------------------------
  Method                  Gateway endpoint                 Description
  ----------------------- -------------------------------- -----------------------
  `GET`                   `/api/healthz`                   Liveness check

  `GET`                   `/api/readyz`                    Readiness check;
                                                           verifies database
                                                           connectivity

  `GET`                   `/api/classes`                   List classes and seat
                                                           counts

  `POST`                  `/api/classes`                   Create a class

  `GET`                   `/api/classes/{classId}`         Get class details

  `POST`                  `/api/classes/{classId}/holds`   Temporarily hold a seat

  `GET`                   `/api/holds/{holdId}`            Get hold details

  `POST`                  `/api/holds/{holdId}/confirm`    Confirm admission

  `DELETE`                `/api/holds/{holdId}`            Cancel a hold

  `GET`                   `/api/me/holds`                  List holds for the
                                                           supplied student ID

  `GET`                   `/api/admin/auth-check`          Check administrator
                                                           authorization mode/key
  --------------------------------------------------------------------------------

### Create a class

``` bash
curl -i -X POST http://localhost:3000/api/classes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Class 6 - Morning Shift",
    "totalSeats": 10
  }'
```

When `AUTH_MODE=protected`, include the administrator key:

``` bash
-H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

### List classes

``` bash
curl -i http://localhost:3000/api/classes
```

### Hold a seat

Replace `{classId}` with an ID returned by the classes endpoint. The
assignment workflow expects `X-Student-Id` to contain exactly 17 digits.

``` bash
curl -i -X POST \
  http://localhost:3000/api/classes/{classId}/holds \
  -H "X-Student-Id: 20152691234567890"
```

### Get a hold

``` bash
curl -i http://localhost:3000/api/holds/{holdId}
```

### Confirm admission

``` bash
curl -i -X POST \
  http://localhost:3000/api/holds/{holdId}/confirm \
  -H "X-Student-Id: 20152691234567890"
```

### Cancel a hold

``` bash
curl -i -X DELETE \
  http://localhost:3000/api/holds/{holdId} \
  -H "X-Student-Id: 20152691234567890"
```

### List a student's holds

``` bash
curl -i http://localhost:3000/api/me/holds \
  -H "X-Student-Id: 20152691234567890"
```

Replace `{classId}` and `{holdId}` with actual IDs returned by the API.
Do not use the example student ID for real student records.

## Admission workflow

A hold moves through these states:

  State         Meaning
  ------------- -----------------------------------
  `HELD`        A seat is temporarily reserved
  `CONFIRMED`   Admission has been confirmed
  `EXPIRED`     The hold's expiry time has passed
  `CANCELLED`   The hold was cancelled

The default hold duration is `600` seconds (10 minutes), controlled by
`HOLD_DURATION_SECONDS`.

The backend uses database transactions and row-level locking when
reserving a seat. The goal is to ensure that concurrent requests cannot
reserve more seats than the class capacity. A student may not create
another active hold for the same class.

## Rate limiting and load balancing

### Nginx gateway

The current Nginx configuration:

-   Uses the `least_conn` upstream balancing method across `backend`,
    `backend2`, and `backend3`.
-   Applies a per-observed-client-IP limit of `10` requests per second
    to configured mutation routes.
-   Allows a burst of `20` requests with `nodelay`.
-   Returns HTTP `429` when the gateway rate limit is exceeded.
-   Sends `Retry-After: 1` for gateway-generated rate-limit responses.

The mutation routes covered by the gateway limit are class creation,
hold creation, hold confirmation, and hold cancellation. GET requests
are not included in this Nginx mutation limit.

### Backend concurrency limiter

Each ASP.NET API process also has a process-local concurrency limiter
configured for 128 active permits and a queue of 128 requests. This is a
resource-protection setting, not a throughput guarantee. Each replica
has its own limiter.

Because gateway rate limiting is based on the observed client IP,
legitimate users sharing a public/NAT IP may share the same limit.

## Testing and verification

Run tests only against a development or disposable QA database. Do not
run destructive or load tests against real student data.

### Static source checks

``` bash
python3 tests/quality_gate.py
```

This checks source/configuration expectations. It does **not** compile
the .NET application or prove runtime behavior.

### API integration and concurrency tests

The Compose QA profile runs the API integration test against the
internal backend service:

``` bash
docker compose --profile qa run --rm qa
```

Alternatively, with the stack already running and in the default
assignment mode:

``` bash
API_URL=http://localhost:8080 python3 tests/integration_test.py
```

The integration suite covers API contracts, concurrent seat holds, hold
lifecycle, ownership checks, validation, structured errors, and optional
expiry testing.

For an expiry test, use a separate disposable stack and configure
matching values for `HOLD_DURATION_SECONDS` and `TEST_HOLD_SECONDS` (the
test script accepts values from 1 to 90 seconds). Do not change the hold
duration on a live admissions database just to run this test.

### Load smoke test

Direct backend test:

``` bash
API_URL=http://localhost:8080 USERS=100 WORKERS=25 python3 tests/load_smoke.py
```

Through the Nginx gateway:

``` bash
API_URL=http://localhost:3000/api USERS=100 WORKERS=25 python3 tests/load_smoke.py
```

The script reports request throughput, p95 latency, and HTTP status
counts, and checks that held plus confirmed seats do not exceed
capacity. It is a bounded smoke benchmark, **not** a production capacity
certificate. Results depend on the machine and test conditions.

### Load-balancer failover test

``` bash
python3 tests/failover_test.py
```

This test stops `backend2`, probes `GET /api/classes` through Nginx, and
starts `backend2` again in a `finally` block. It tests availability
during one API replica outage; it does not prove full high availability.

### Other QA utilities

The repository also includes additional scripts for gateway policy,
persistence, backup/restore drills, race-boundary checks, and browser
E2E testing. Read each script and its prerequisites before running it.
Prefer `tests/run_isolated_qa.py` for the isolated QA workflow described
in the project QA documentation.

## Docker commands

Run from the project root.

  Task                                 Command
  ------------------------------------ ----------------------------------------
  Start services                       `docker compose up -d`
  Build and start                      `docker compose up --build -d`
  Stop services, keep containers       `docker compose stop`
  Start stopped services               `docker compose start`
  Stop and remove containers/network   `docker compose down`
  Show status                          `docker compose ps`
  Follow all logs                      `docker compose logs -f`
  Follow database logs                 `docker compose logs -f db`
  Rebuild one service                  `docker compose up -d --build backend`

**Database warning:** `docker compose down -v` deletes the Compose named
volume and can permanently remove local PostgreSQL data. Do not use it
unless you intentionally want to delete the database volume.

## Configuration

The root `.env.example` documents the supported Compose settings:

  -------------------------------------------------------------------------
  Variable                  Default                 Purpose
  ------------------------- ----------------------- -----------------------
  `POSTGRES_DB`             `admissions`            PostgreSQL database
                                                    name

  `POSTGRES_USER`           `admissions`            PostgreSQL username

  `POSTGRES_PASSWORD`       Set by you              Required database
                                                    password

  `AUTH_MODE`               `assignment`            `assignment` or
                                                    `protected`

  `ADMIN_API_KEY`           Empty                   Required in protected
                                                    mode; at least 32 UTF-8
                                                    bytes

  `HOLD_DURATION_SECONDS`   `600`                   Hold duration, 1--86400
                                                    seconds

  `TEST_HOLD_SECONDS`       `0`                     Optional expiry-test
                                                    duration; use a
                                                    separate QA stack

  `FRONTEND_PORT`           `3000`                  Host port for
                                                    frontend/Nginx

  `BACKEND_PORT`            `8080`                  Loopback host port for
                                                    the first API replica
  -------------------------------------------------------------------------

`DATABASE_URL` is assembled for the API containers by Docker Compose
from the PostgreSQL settings. Do not put production credentials in
source files.

## Security notes

-   `AUTH_MODE=assignment` preserves the assignment workflow and does
    not provide real student identity verification.
-   `X-Student-Id` is an identifier supplied by the client; by itself it
    is **not authentication**. Do not use this mode for real public
    admissions.
-   `AUTH_MODE=protected` optionally requires `X-Admin-Key` for class
    creation. The key must contain at least 32 UTF-8 bytes.
-   The optional admin API key is not a replacement for user
    authentication, verified student identity, RBAC, or MFA.
-   Keep `.env`, backups, database dumps, and real student data out of
    Git.
-   Use HTTPS, managed secrets, restricted database access, monitoring,
    backups, and a verified identity provider before any real production
    deployment.
-   A single PostgreSQL primary and a single Nginx gateway remain single
    points of failure.

## Troubleshooting

  ----------------------------------------------------------------------------------------------
  Symptom                             Checks
  ----------------------------------- ----------------------------------------------------------
  Compose says `POSTGRES_PASSWORD` is Create `.env` from `.env.example` and set a non-empty
  required                            password

  Frontend Docker build fails at      Generate and commit `frontend/package-lock.json`
  `npm ci`                            

  Playwright install/test fails       Generate `tests/package-lock.json`, run `npm ci` in
                                      `tests`, and install the required Playwright browser

  API returns `503` on `/readyz`      Check `docker compose ps`, `docker compose logs db`,
                                      credentials, and database health

  Gateway returns `502`               Check all three backend containers and
                                      `docker compose logs frontend backend backend2 backend3`

  API returns `429`                   Respect `Retry-After`; reduce request rate and check
                                      whether users share a NAT/public IP

  Hold returns `409`                  Check class capacity, existing active holds, and the hold
                                      state

  Confirm/cancel returns `403`        The supplied `X-Student-Id` does not match the hold owner

  Port is already in use              Change `FRONTEND_PORT` or `BACKEND_PORT` in `.env`

  Data appears missing after restart  Confirm the `admissions_data` volume is present; do not
                                      run `down -v`
  ----------------------------------------------------------------------------------------------

## Project structure

``` text
School-Admission-System/
├── backend/
│   ├── Dockerfile
│   └── SchoolAdmission.Api/
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── tests/
│   ├── integration_test.py
│   ├── load_smoke.py
│   ├── failover_test.py
│   └── ...
├── deploy/
├── docs/
├── ops/
├── scripts/
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Contributing

1.  Create a feature branch.
2.  Keep changes focused and document configuration changes.
3.  Run relevant static, integration, concurrency, and browser tests.
4.  Review generated lockfile changes.
5.  Never commit secrets, local environment files, database dumps, or
    real student data.

## License

No license is specified in this repository. Add an appropriate `LICENSE`
file before publishing or redistributing the project.
