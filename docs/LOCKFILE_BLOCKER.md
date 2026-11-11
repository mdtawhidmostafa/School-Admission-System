# Lockfile release blocker

`frontend/package-lock.json` and `tests/package-lock.json` could not be generated in this tool environment: `npm install --package-lock-only` returned `EAI_AGAIN` for `registry.npmjs.org`. Never handcraft a lockfile or claim reproducible build is verified.

On any network-enabled machine run `sh scripts/generate-lockfiles.sh` (Windows PowerShell: run the two `npm install --package-lock-only` and `npm ci` commands in `frontend` and `tests` separately). Commit both lockfiles, run `docker compose up --build -d`, then run the isolated QA suite. A failing `npm ci` is a release blocker, not an invitation to fall back to unpinned `npm install` in CI.
