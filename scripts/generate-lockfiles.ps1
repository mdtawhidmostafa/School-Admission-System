# Run in PowerShell from any directory on an internet-connected machine.
# Do not replace package-lock.json with invented metadata: npm resolves the full tree.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
foreach ($rel in @('frontend','tests')) {
    $dir = Join-Path $root $rel
    Push-Location $dir
    try {
        & npm install --package-lock-only --ignore-scripts --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw "npm lockfile generation failed for $rel" }
        & npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed for $rel" }
        Write-Host "PASS: $rel lockfile and npm ci"
    } finally { Pop-Location }
}
Push-Location (Join-Path $root 'frontend')
try {
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally { Pop-Location }
Write-Host 'PASS: frontend build. Commit both package-lock.json files.'
