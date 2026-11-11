#!/usr/bin/env sh
set -eu
# Run where npm registry is reachable; commit generated lockfiles.
(cd frontend && npm install --package-lock-only --ignore-scripts --no-audit --no-fund && npm ci --no-audit --no-fund && npm run build)
(cd tests && npm install --package-lock-only --ignore-scripts --no-audit --no-fund && npm ci --no-audit --no-fund)
