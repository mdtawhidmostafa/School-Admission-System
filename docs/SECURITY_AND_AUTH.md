# Authentication, authorization and security boundary

## Important: original assignment contract
The recruitment PDF explicitly requires **no login**, a 17-digit birth registration number entered on the page, and `X-Student-Id` in student requests. The default `AUTH_MODE=assignment` preserves that requirement and **does not provide real student identity verification**. Anyone knowing a birth registration number could impersonate that student. Do not use assignment mode for real admissions.

## Optional administrator-protected mode
Set `AUTH_MODE=protected` and `ADMIN_API_KEY` to a cryptographically random secret containing **at least 32 UTF-8 bytes**. All three ASP.NET API containers inherit those environment values. The `POST /classes` endpoint requires `X-Admin-Key`; missing/incorrect keys return `401`. `GET /admin/auth-check` allows operational verification. Class list and student operations continue to follow the PDF's unauthenticated contract. The frontend's Admin form has a password-type API key input kept in component memory only; it is never written to localStorage or sessionStorage. Close or reload the page to clear it.

Example (PowerShell): `[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))`.

Example (macOS/Linux): `openssl rand -hex 32`.

Set environment variables in untracked `.env`, never in Git. Do not use a real production secret in shared QA transcripts. Run `docker compose up --build -d` and verify the mode with `python tests/auth_mode_test.py` after exporting `ADMIN_API_KEY` and setting `API_URL` to your backend endpoint.

## Authorization matrix

| Action | Assignment mode | Protected mode |
|---|---|---|
| `POST /classes` | Public, as PDF specifies | Requires `X-Admin-Key` |
| `GET /classes`, `GET /classes/{id}` | Public | Public |
| Student hold / confirm / cancel / history | Valid `X-Student-Id`; NOT authentication | Same; NOT production-safe |
| `/healthz`, `/readyz` | Operational endpoints | Operational endpoints |

## What this *does not* solve
This is an administrator API-key gate, **not** full user authentication, RBAC, MFA, or verified student identity. It is appropriate as an optional assignment demonstration, not as a secure real-world identity model. For production: integrate an identity provider (e.g. Supabase Auth or OIDC), server-verified session/JWT, role-based policies for administrators, verified student-to-identity binding, TLS, audit log, brute-force protections, secret rotation, access control for operational endpoints and data-retention controls. Never claim that `X-Student-Id` alone authorizes student access securely.

## Failure actions
- `AUTH_MODE` invalid: correct to `assignment` or `protected` and restart.
- Protected startup fails: set 32+ byte `ADMIN_API_KEY` consistently across all instances.
- HTTP 401 on admin create: enter correct key; check server environment and avoid pasting key in logs.
- HTTP 400 on invalid student ID: supply exactly 17 digits (the assignment accepts an unverified identifier).
- HTTP 403 on someone else's hold: access denied by the existing ownership comparison, but the supplied identity is not verified.
- Suspected key leakage: rotate secret, redeploy all API instances and invalidate old values.
- Test in assignment mode: `tests/auth_mode_test.py` is **not applicable** (auth-check intentionally returns 200 with no key).
