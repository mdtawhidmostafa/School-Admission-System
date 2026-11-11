"""Execute source-level QA and record commands/exit codes; NEVER marks live tests as passed."""
from __future__ import annotations
import json, pathlib, subprocess, sys, datetime, shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
checks=[
 ('v12 repository unit checks',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_v12_source.py','-v']),
 ('legacy repository unit checks',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_quality_unit.py','-v']),
 ('API source contract',[sys.executable,'tests/static_contract_check.py']),
 ('source quality gate',[sys.executable,'tests/quality_gate.py']),
 ('Python syntax',[sys.executable,'-m','compileall','-q','tests','ops']),
 ('JS browser syntax',['node','--check','tests/browser_e2e.spec.cjs']),
 ('JS load scenario syntax',['node','--check','tests/k6_load_smoke.js']),
 ('JS Playwright config syntax',['node','--check','tests/playwright.config.cjs']),
]
reports=[]
for label,command in checks:
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    status='PASS' if p.returncode==0 else 'FAIL'
    out=(p.stdout+'\n'+p.stderr).strip()
    reports.append({'check':label,'status':status,'exit_code':p.returncode,'command':command,'output':out[-5000:]})
    print(status,label)
# Real system test entries remain explicitly blocked or not run.
for label,reason in [
 ('frontend/test npm lockfile generation','npm registry DNS EAI_AGAIN; no authentic locks created'),
 ('actual .NET 10 compilation','dotnet SDK not installed in current container'),
 ('Docker startup and 8-API integration','Docker CLI/daemon not installed in current container'),
 ('PostgreSQL concurrency / expiry / cross replica','Docker runtime unavailable'),
 ('PostgreSQL backup/restore drill','Docker runtime unavailable'),
 ('Playwright browser E2E / k6 load benchmark','runtime/dependencies unavailable'),
 ('Windows/macOS/Linux runtime matrix','external OS runners unavailable'),
]: reports.append({'check':label,'status':'BLOCKED','reason':reason})
for lock in ('frontend/package-lock.json','tests/package-lock.json'):
    reports.append({'check':lock,'status':'PASS' if (ROOT/lock).exists() else 'BLOCKED','reason':'authentic dependency lock required' if not (ROOT/lock).exists() else ''})
result={'project':'School Admission System v12','timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'platform':sys.platform,'tools':{x:shutil.which(x) for x in ('python','node','npm','dotnet','docker','nginx')},'checks':reports}
path=ROOT/'QA_EVIDENCE_v12.json'
path.write_text(json.dumps(result,indent=2)+'\n')
print('WROTE',path)
sys.exit(1 if any(x['status']=='FAIL' for x in reports) else 0)
