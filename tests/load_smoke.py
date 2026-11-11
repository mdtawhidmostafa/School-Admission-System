"""Bounded smoke benchmark; not a capacity certificate. Usage: API_URL=http://... USERS=100 python tests/load_smoke.py"""
import os,time,uuid,statistics
from concurrent.futures import ThreadPoolExecutor,as_completed
from integration_test import call,expect,wait_ready
users=int(os.getenv('USERS','100'))
workers=int(os.getenv('WORKERS','25'))
assert 1<=users<=10000 and 1<=workers<=200
wait_ready()
class_id=expect(201,'POST','/classes',body={'name':'LoadSmoke-'+uuid.uuid4().hex,'totalSeats':min(20,users)})['id']
def run(i):
    start=time.perf_counter()
    try: status,_=call('POST',f'/classes/{class_id}/holds',f'{i:017d}')
    except Exception: status=0
    return status,(time.perf_counter()-start)*1000
start=time.perf_counter()
with ThreadPoolExecutor(max_workers=workers) as pool:
    res=list(pool.map(run,range(users)))
duration=time.perf_counter()-start
from collections import Counter
statuses=Counter(s for s,_ in res)
counts=expect(200,'GET',f'/classes/{class_id}')
assert counts['heldSeats']+counts['confirmedSeats']<=counts['totalSeats'],counts
samples=sorted(d for _,d in res)
p95=samples[max(0,int(.95*len(samples))-1)]
print(f'users={users} workers={workers} duration_s={duration:.2f} rps={users/duration:.2f} p95_ms={p95:.1f} status_counts={dict(statuses)}')
print('PASS capacity invariant; throughput figures are from this run only')
