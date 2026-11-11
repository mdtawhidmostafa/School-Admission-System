"""Static regression gates; NOT a substitute for .NET compilation or live QA."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
backend=(root/'backend/SchoolAdmission.Api/Program.cs').read_text()
frontend=(root/'frontend/src/main.tsx').read_text()
nginx=(root/'frontend/nginx.conf').read_text()
compose=(root/'docker-compose.yml').read_text()
assert len(re.findall(r'app.Map(Post|Get|Delete)\(', backend)) >= 10
routes=[('Post','/classes'),('Get','/classes'),('Get','/classes/{classId}'),
        ('Post','/classes/{classId}/holds'),('Get','/holds/{holdId}'),
        ('Post','/holds/{holdId}/confirm'),('Delete','/holds/{holdId}'),('Get','/me/holds')]
for method,route in routes:
    assert f'app.Map{method}("{route}"' in backend, (method,route)
for fragment in ('FOR UPDATE','ExpireClassAsync','ExecuteAsync','try { await next(); }'):
    assert fragment in (backend+(root/'backend/SchoolAdmission.Api/Data/Db.cs').read_text()+(root/'backend/SchoolAdmission.Api/Services/HoldTransitionService.cs').read_text()),fragment
frontend_sources=frontend+''.join(p.read_text() for p in (root/'frontend/src/hooks').glob('*.ts'))
for fragment in ('validStudent','localStorage','setClassError','setHistoryError','Promise.allSettled','1_000_000'):
    assert fragment in frontend_sources,fragment
for fragment in ('backend:8080','backend2:8080','backend3:8080','limit_req_status 429'):
    assert fragment in nginx,fragment
for fragment in ('admissions_data','condition: service_healthy','restart: unless-stopped'):
    assert fragment in compose,fragment
assert 'npm ci --no-audit --no-fund' in (root/'frontend/Dockerfile').read_text()
print('PASS source-structure checks (runtime is NOT validated)')
