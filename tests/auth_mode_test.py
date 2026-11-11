"""Optional live authorization smoke test; use against protected-mode API only."""
import json
import os
import urllib.error
import urllib.request

base = os.environ.get("API_URL", "http://localhost:8080").rstrip("/")
secret = os.environ.get("ADMIN_API_KEY", "")
if len(secret.encode()) < 32:
    raise SystemExit("Set ADMIN_API_KEY to the same 32+ byte secret as the protected backend")

def call(key=None):
    req = urllib.request.Request(base + "/admin/auth-check", headers=({"X-Admin-Key": key} if key else {}))
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)

assert call()[0] == 401, "Missing key must be rejected"
assert call("not-the-right-admin-key")[0] == 401, "Wrong key must be rejected"
assert call(secret)[0] == 200, "Valid admin key must be accepted"
# Verify authorization on the real protected operation without creating a class.
def attempt_create(key=None):
    headers = {"Content-Type": "application/json"}
    if key: headers["X-Admin-Key"] = key
    req = urllib.request.Request(base + "/classes", data=b'{"name":"","totalSeats":0}', headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            return response.status
    except urllib.error.HTTPError as err:
        return err.code

assert attempt_create() == 401, "Unauthorized POST /classes must be rejected"
assert attempt_create("invalid-key") == 401, "Wrong key must be rejected at the mutation endpoint"
assert attempt_create(secret) == 400, "Authorized invalid body should receive validation error"
print("PASS protected admin authentication, mutation authorization and validation checks")
