"""Live gateway tests: mutations limited; GET remains usable. Use disposable QA stack.
Requires GATEWAY_URL (default http://127.0.0.1:13080) and assignment auth mode.
"""
import json, os, uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
BASE=os.getenv('GATEWAY_URL','http://127.0.0.1:13080').rstrip('/')
def call(method,path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=Request(BASE+path,method=method,data=data,headers={'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=8) as r:return r.status, r.read()
    except HTTPError as e:return e.code,e.read()

def main():
    code,raw=call('GET','/api/classes')
    assert code==200, ('GET',code,raw)
    codes=[]
    for n in range(65):
        status, raw=call('POST','/api/classes',{'name':'policy-'+uuid.uuid4().hex,'totalSeats':1})
        assert status in (201,429,503), (status,raw)
        if status==429:
            body=json.loads(raw)
            assert body['code']=='RATE_LIMITED' and 'error' in body,body
        codes.append(status)
    assert 429 in codes, ('Expected gateway throttling at 10r/s burst 20; got',codes)
    status,_=call('GET','/api/classes')
    assert status==200,('GET must not be rate-limited',status)
    print('PASS gateway throttles mutations with JSON 429, not class GET', {c:codes.count(c) for c in set(codes)})
if __name__=='__main__':main()
