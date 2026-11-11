# Cross-platform Setup and Failure Recovery — v9

**Target hosts:** Windows 10/11 with Docker Desktop (WSL2/Linux containers), macOS Intel/Apple Silicon with Docker Desktop, and Linux with Docker Engine/Compose v2. These are **intended** targets, not a completed three-OS certification.

## Before the first build

1. Have Docker Compose v2, enough disk/RAM, and internet access for the image registry, NuGet, and npm dependencies.
2. **Generate and commit genuine npm lockfiles** (`frontend/package-lock.json`, `tests/package-lock.json`) from an internet-connected environment, as described in README. The application will intentionally not build until the frontend lockfile exists.
3. Copy `.env.example` to `.env`, set a unique PostgreSQL password and optional host ports. Never commit `.env`.
4. Run the same commands in Windows PowerShell, macOS Terminal, or Linux shell from project root:

```sh
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose --profile qa run --rm qa
```

URL defaults: `http://localhost:3000` (frontend) and `http://localhost:8080/readyz` (direct development API). Change ports in `.env` if occupied. API requests through Nginx use `/api` under the frontend host.

### Windows

- Choose Docker Desktop WSL2/Linux container mode, check the Docker Engine is running.
- Extract project to a local folder, not a protected system folder.
- Copy `.env.example` to `.env` with `Copy-Item .env.example .env`.
- Use PowerShell unchanged for all `docker compose` commands.

### macOS

- Use the Docker Desktop build matching Apple Silicon or Intel CPU; grant access to the project path if prompted.
- Check available memory/disk. Docker image architecture support must be verified during pull/build.

### Linux

- Install Docker Engine and official Docker Compose plugin. Ensure daemon running and user has safe Docker access; avoid broad insecure socket permissions.
- Run Compose as the authorized Docker user; preserve LF shell script line endings (repository `.gitattributes`).

## Failure-to-action table

| Error | Action |
|---|---|
| `docker: command not found` | Install Docker/Compose; verify `docker compose version` |
| `Cannot connect to the Docker daemon` | Start Docker Desktop/Engine; verify permissions |
| `npm ERR! EAI_AGAIN` | Check npm registry DNS/network, proxy/firewall; do not fabricate lockfile |
| `npm ci` missing lockfile | Generate/commit lockfile online, repeat build |
| NuGet restore fails | Check SDK image, connectivity, package version; capture full build logs |
| `port already allocated` | Change `FRONTEND_PORT` or `BACKEND_PORT` in `.env` |
| Database unhealthy | Inspect `docker compose logs db`, credentials and volume disk space |
| Nginx 502 | Verify backend 1/2/3 readiness, then gateway logs/restart |
| API 503 | Check DB connectivity, connection pool, lock contention and logs; bounded retry |
| Data appears missing | Check Compose project name and named volume; NEVER run `down -v` for a normal restart |
| TypeScript build error | Run `cd frontend && npm ci && npm run build`, fix errors before deployment |

More details: `OPERATIONS_RUNBOOK.md` including API error meanings, health checks, backup and test commands.

## Limitations

The source can target three operating systems, but **only execution on each target OS can establish compatibility**. Docker build depends on external downloads for first use; no all-machine 0% failure guarantee is possible. PostgreSQL is persistent through named volume, but production disaster recovery requires tested backup/restore procedures.
