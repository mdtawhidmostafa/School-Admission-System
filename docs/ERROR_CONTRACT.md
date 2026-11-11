# Error contract and failure handling

The PDF only fixes several statuses and existing `error` fields. Preserve the response `error` string to retain frontend compatibility.

Global handled exceptions additionally return `{"error":"...","code":"...","requestId":"..."}`. Some endpoint-level business-validation errors retain only `error` and may include `status`; this is a documented transitional inconsistency rather than a claim of full standardization.

| Status | Meaning | Client action | Operator action |
|---|---|---|---|
| 400 | Invalid JSON, 17-digit ID, seats, or malformed resource ID | Correct input | Inspect validation logs if recurring |
| 401 | Wrong/missing admin API key in protected mode | Use valid key | Check AUTH_MODE and secret injection |
| 403 | Attempt to update another student hold | Stop and verify ownership | Investigate abuse without logging raw IDs |
| 404 | Class or hold does not exist | Refresh list | Verify migration/fixtures |
| 409 | No seats, duplicate active admission, expired hold | Refresh status and do not auto-retry hold | Monitor contention and capacity |
| 429 | Rate/concurrency limit | Respect retry/backoff; do not spam | Adjust capacity after metrics review |
| 503 | Database unavailable or contention | Retry with backoff; confirmation may already have succeeded, so refresh first | Check DB, pool and lock waits |
| 500 | Unexpected error | Show safe error; retain request ID | Search correlated logs |

Never automatically retry mutation requests without preserving idempotency. Nginx proxies may route requests to different API instances.


## v12 contract
For API-level errors handled by endpoints or global exception middleware, responses contain `{ "error": "human readable message", "code": "STABLE_CODE", "requestId": "..." }`. HTTP status is authoritative. Nginx-generated 502/429 and framework-generated exceptions may bypass this contract; ensure the frontend treats non-JSON responses defensively. 204 cancellation has an empty response body.
