"""Executed inside QA Docker service: verifies all three API processes share one database.
Use only on disposable QA stack because it creates admissions.
"""
import json, uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError
BASES=['http://backend:8080','http://backend2:8080','http://backend3:8080']

def request(base,method,path,student=None,body=None):
    headers={'Content-Type':'application/json'}
    if student: headers['X-Student-Id']=student
    req=Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
    try:
        with urlopen(req,timeout=20) as response:
            payload=response.read()
            return response.status,json.loads(payload) if payload else None
    except HTTPError as exc:
        payload=exc.read()
        return exc.code,json.loads(payload) if payload else None

name='Replica-QA-'+uuid.uuid4().hex
code,created=request(BASES[0],'POST','/classes',body={'name':name,'totalSeats':1})
assert code==201,(code,created)
cid=created['id']
for base in BASES:
    code,detail=request(base,'GET','/classes/'+cid)
    assert code==200 and detail['availableSeats']==1,(base,detail)
sid='5'+str(uuid.uuid4().int).zfill(16)[-16:]
code,h=request(BASES[1],'POST',f'/classes/{cid}/holds',sid)
assert code==201,(code,h)
code,detail=request(BASES[2],'GET',f'/classes/{cid}')
assert code==200 and detail['heldSeats']==1,(code,detail)
code,res=request(BASES[2],'POST',f'/holds/{h["holdId"]}/confirm',sid)
assert code==200 and res['status']=='CONFIRMED',(code,res)
code,detail=request(BASES[0],'GET',f'/classes/{cid}')
assert detail['confirmedSeats']==1 and detail['availableSeats']==0,detail
code,history=request(BASES[1],'GET','/me/holds',sid)
assert any(x['holdId']==h['holdId'] and x['status']=='CONFIRMED' for x in history)
print('PASS cross-replica: create API1, reserve API2, confirm API3, read API1/2')
