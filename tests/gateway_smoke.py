"""Run from QA container: python gateway_smoke.py. Check all three backends and Nginx ingress."""
from urllib.request import urlopen
from urllib.error import URLError
import json,time

for address in ('http://backend:8080/readyz','http://backend2:8080/readyz','http://backend3:8080/readyz','http://frontend/api/classes'):
    for attempt in range(60):
        try:
            with urlopen(address, timeout=5) as response:
                assert response.status == 200, (address,response.status)
            print('PASS',address)
            break
        except (URLError, TimeoutError, OSError):
            if attempt==59:raise
            time.sleep(1)
print('PASS gateway smoke + readiness for all three API services')
