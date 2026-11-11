"""Record verifiable external QA evidence; never convert unrun tests to PASS.
From project root: python tests/evidence_runner.py
Requires Docker and built/running stack. Writes QA_EVIDENCE.json (ignored by git).
"""
import subprocess, json, datetime, sys, os, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
checks=[
 ('compose_config',['docker','compose','config','--quiet']),
 ('service_status',['docker','compose','ps']),
 ('api_contract_and_concurrency',['docker','compose','--profile','qa','run','--rm','qa']),
 ('gateway_smoke',['docker','compose','--profile','qa','run','--rm','qa','python','gateway_smoke.py']),
 ('single_replica_failover',[sys.executable,'tests/failover_test.py']),
]
evidence={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'environment': {'platform':sys.platform},'results':[]}
for name,command in checks:
    try:
        result=subprocess.run(command,cwd=root,text=True,capture_output=True,timeout=240)
        evidence['results'].append({'check':name,'status':'PASS' if result.returncode==0 else 'FAIL',
                                    'exit_code':result.returncode,'output_tail':(result.stdout+'\n'+result.stderr)[-5000:]})
    except Exception as exc:
        evidence['results'].append({'check':name,'status':'ERROR','reason':str(exc)})
output=root/'QA_EVIDENCE.json'
output.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print('Evidence saved:',output)
for item in evidence['results']: print(item['check'],item['status'])
sys.exit(0 if all(x['status']=='PASS' for x in evidence['results']) else 1)
