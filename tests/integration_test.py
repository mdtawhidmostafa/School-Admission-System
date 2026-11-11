"""Black-box API QA; run against an isolated, running Docker stack.
Optional expiry exercise: set TEST_HOLD_SECONDS to backend HOLD_DURATION_SECONDS.
"""
import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = os.getenv('API_URL', 'http://localhost:8080').rstrip('/')

def call(method, path, student=None, body=None):
    headers = {'Content-Type': 'application/json'}
    if student is not None:
        headers['X-Student-Id'] = student
    payload = json.dumps(body).encode() if body is not None else None
    request = Request(BASE + path, data=payload, method=method, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            content = response.read()
            return response.status, json.loads(content) if content else None
    except HTTPError as exc:
        content = exc.read()
        return exc.code, json.loads(content) if content else None

def wait_ready(timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            status, _ = call('GET', '/readyz')
            if status == 200:
                return
        except (URLError, TimeoutError, OSError):
            pass
        time.sleep(1)
    raise RuntimeError(f'API did not become ready within {timeout}s at {BASE}')

def expect(code, method, path, student=None, body=None):
    actual, result = call(method, path, student, body)
    assert actual == code, (method, path, 'expected', code, 'actual', actual, result)
    return result

def create(seats=1):
    return expect(201, 'POST', '/classes', body={
        'name': 'QA-' + uuid.uuid4().hex,
        'totalSeats': seats
    })['id']

def hold(class_id, student):
    return expect(201, 'POST', f'/classes/{class_id}/holds', student)['holdId']

def class_counts(class_id):
    return expect(200, 'GET', f'/classes/{class_id}')

def test_api_contract():
    cid = create(3)
    classes = expect(200, 'GET', '/classes')
    assert any(item['id'] == cid for item in classes)
    detail = class_counts(cid)
    assert all(key in detail for key in ('id','name','totalSeats','heldSeats','confirmedSeats','availableSeats'))
    assert (detail['totalSeats'], detail['availableSeats']) == (3,3)
    student = '20152691234567890'
    hid = hold(cid, student)
    h = expect(200, 'GET', f'/holds/{hid}')
    assert h['status'] == 'HELD' and h['holdId'] == hid and h['classId'] == cid
    mine = expect(200, 'GET', '/me/holds', student)
    assert any(item['holdId'] == hid and item['className'] == detail['name'] for item in mine)
    print('PASS contract: 8 endpoints, required response fields and student history')

def test_concurrency():
    cid = create(1)
    def attempt(i):
        return call('POST', f'/classes/{cid}/holds', f'{i:017d}')[0]
    with ThreadPoolExecutor(max_workers=int(os.getenv("CONCURRENCY_WORKERS","100"))) as pool:
        codes = list(pool.map(attempt, range(100)))
    assert codes.count(201) == 1 and codes.count(409) == 99, codes
    detail = class_counts(cid)
    assert (detail['heldSeats'], detail['availableSeats']) == (1,0), detail
    print('PASS concurrency: 100 requests using configurable concurrent workers / 1 seat / no oversell')

def test_lifecycle_and_isolation():
    first, second = create(2), create(1)
    user, other = '11111111111111111', '22222222222222222'
    hid = hold(first,user)
    expect(409,'POST',f'/classes/{first}/holds',user)
    expect(403,'POST',f'/holds/{hid}/confirm',other)
    expect(403,'DELETE',f'/holds/{hid}',other)
    for _ in range(5):
        confirmed = expect(200,'POST',f'/holds/{hid}/confirm',user)
        assert confirmed['status'] == 'CONFIRMED'
    expect(409,'DELETE',f'/holds/{hid}',user)
    counts = class_counts(first)
    assert counts['confirmedSeats'] == 1 and counts['heldSeats'] == 0, counts
    assert class_counts(second)['availableSeats'] == 1
    cancelled = hold(second,user)
    expect(204,'DELETE',f'/holds/{cancelled}',user)
    expect(204,'DELETE',f'/holds/{cancelled}',user)
    expect(409,'POST',f'/holds/{cancelled}/confirm',user)
    hold(second,other)
    assert class_counts(second)['availableSeats'] == 0
    print('PASS lifecycle: ownership, duplicate, confirm idempotency, cancellation, class isolation')


def test_parallel_confirm():
    cid=create(1)
    student='33333333333333333'
    hid=hold(cid,student)
    with ThreadPoolExecutor(max_workers=10) as pool:
        results=list(pool.map(lambda _ : call('POST',f'/holds/{hid}/confirm',student)[0],range(10)))
    assert results==[200]*10,results
    counts=class_counts(cid)
    assert counts['confirmedSeats']==1 and counts['heldSeats']==0,counts
    print('PASS parallel confirm: repeated requests counted once')

def test_structured_errors():
    cid=create()
    status,body=call('GET','/classes/invalid')
    assert status==400 and isinstance(body,dict) and all(k in body for k in ('error','code','requestId')),(status,body)
    status,body=call('POST',f'/classes/{cid}/holds','invalid')
    assert status==400 and all(k in body for k in ('error','code','requestId')),(status,body)
    print('PASS structured errors include error/code/requestId')

def test_validation():
    cid=create()
    expect(400,'POST','/classes',body={'name':'','totalSeats':0})
    expect(400,'POST','/classes',body={'name':'Bad','totalSeats':-1})
    expect(400,'POST','/classes',body={'name':'Bad','totalSeats':1000001})
    expect(400,'POST','/classes',body={'name':'Bad','totalSeats':1_000_001})
    expect(400,'POST','/classes',body={'name':'x'*151,'totalSeats':1})
    expect(400,'POST','/classes',body={'name':'Valid','totalSeats':0})
    expect(400,'POST',f'/classes/{cid}/holds','abc')
    expect(400,'POST',f'/classes/{cid}/holds','')
    expect(400,'POST',f'/classes/{cid}/holds','1234567890123456')
    expect(400,'GET','/classes/invalid')
    expect(400,'GET','/holds/invalid')
    expect(404,'GET','/holds/h_' + uuid.uuid4().hex)
    expect(404,'GET','/classes/c_' + uuid.uuid4().hex)
    print('PASS validation: malformed identifiers, bad seats, missing resources')

def test_expiry():
    seconds=int(os.getenv('TEST_HOLD_SECONDS','0'))
    if not seconds:
        print('SKIP expiry: set TEST_HOLD_SECONDS matching HOLD_DURATION_SECONDS in a dedicated test stack')
        return
    if seconds < 1 or seconds > 90:
        raise ValueError('TEST_HOLD_SECONDS must be between 1 and 90')
    cid=create()
    student='77777777777777777'
    hid=hold(cid,student)
    time.sleep(seconds+2)
    assert expect(200,'GET',f'/holds/{hid}')['status']=='EXPIRED'
    expect(409,'POST',f'/holds/{hid}/confirm',student)
    assert class_counts(cid)['availableSeats']==1
    hold(cid,'88888888888888888')
    print('PASS expiry: status change, blocked late confirmation, released seat')

if __name__=='__main__':
    wait_ready()
    for test in (test_api_contract,test_concurrency,test_lifecycle_and_isolation,test_parallel_confirm,test_structured_errors,test_validation,test_expiry):
        test()
    print('ALL EXECUTED API TESTS PASSED')
