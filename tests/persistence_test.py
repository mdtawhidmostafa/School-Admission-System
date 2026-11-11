"""Run: python tests/persistence_test.py before; docker compose restart; python tests/persistence_test.py after"""
import json
import os
import sys
import uuid
from pathlib import Path
from integration_test import call, expect

STATE=Path(os.getenv('PERSISTENCE_STATE_FILE','/tmp/admission_qa_persistence.json'))
if len(sys.argv)!=2 or sys.argv[1] not in ('before','after'):
    raise SystemExit('Usage: python tests/persistence_test.py before|after')
if sys.argv[1]=='before':
    name='QA-persist-'+uuid.uuid4().hex
    created=expect(201,'POST','/classes',body={'name':name,'totalSeats':2})
    student='95555555555555555'
    held=expect(201,'POST',f'/classes/{created["id"]}/holds',student)
    STATE.write_text(json.dumps({'classId':created['id'],'holdId':held['holdId'],'student':student}))
    print('PASS persistence fixture saved:',STATE)
else:
    saved=json.loads(STATE.read_text())
    detail=expect(200,'GET',f'/classes/{saved["classId"]}')
    hold=expect(200,'GET',f'/holds/{saved["holdId"]}')
    assert detail['id']==saved['classId'] and hold['holdId']==saved['holdId']
    print('PASS persistence: class and hold survive container restart')
