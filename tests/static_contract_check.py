from pathlib import Path
root=Path(__file__).resolve().parents[1]
api=(root/'backend/SchoolAdmission.Api/Program.cs').read_text()
required=['/classes','/classes/{classId}','/classes/{classId}/holds','/holds/{holdId}','/holds/{holdId}/confirm','/me/holds']
for route in required: assert route in api, route
project=(root/'backend/SchoolAdmission.Api/SchoolAdmission.Api.csproj').read_text()
assert 'net10.0' in project
image=(root/'backend/Dockerfile').read_text()
assert 'dotnet/sdk:10.0' in image and 'dotnet/aspnet:10.0' in image
compose=(root/'docker-compose.yml').read_text()
for service in ('backend:', 'backend2:', 'backend3:', 'frontend:', 'db:'): assert service in compose
assert 'admissions_data' in compose
assert 'pg_advisory_lock' in (root/'backend/SchoolAdmission.Api/Data/Db.cs').read_text()
print('PASS static .NET10/API/compose checks (does not prove runtime behavior)')
