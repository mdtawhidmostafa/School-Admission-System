# Production authentication design (NOT implemented)

The PDF explicitly specifies a login-free candidate exercise with `X-Student-Id`. The default `AUTH_MODE=assignment` preserves this contract. **Do not deploy with real student records.** A header that a browser controls is not proof of identity.

## Recommended real-world path
- OIDC authorization-code + PKCE with an identity provider; HTTPS and secure, HttpOnly, SameSite session cookies; CSRF protection for cookie-based mutations.
- RBAC roles `SchoolAdmin`, `AdmissionsOfficer`, `Guardian`; apply authorization to *every* endpoint that returns or changes sensitive records.
- Verify student's birth registration number using an authorized identity-proofing workflow; maintain guardian/student relationship and audit events.
- Rotate secrets, use a dedicated secret store, scope database credentials per service, set bounded session lifetimes and throttled sign-in.
- Threat model: identity spoofing, enumeration, reservation abuse, CSRF, replay, privilege escalation, data leakage and credentials in logs.

Protected admin API key mode is a limited deployment option, **not** OIDC/RBAC or secure student authentication. The only production-safe state of this repository is a demonstration system with synthetic identities.


## v12 clarification
A shared administrator API key in protected mode is a limited demo safeguard, not RBAC or a full auth service. No verified student identity is implemented. Production proposal: OIDC login for admin, role claims verified server-side, verified student identity with a server-issued principal (never trusting a raw birth-registration header), audit log for every mutating action, rate limiting keyed by verified identity, HTTPS, key rotation, and threat-modelled account recovery. **Do not activate production auth on the PDF assignment mode, which explicitly requires login-free student flows.**
