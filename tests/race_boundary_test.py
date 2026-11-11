"""Runs against a dedicated stack with HOLD_DURATION_SECONDS=4; NOT a load benchmark."""
import os,time,uuid
from concurrent.futures import ThreadPoolExecutor
from integration_test import call,wait_ready,create,class_counts,hold

def check():
    wait_ready()
    cid=create(1)
    sid='1'+str(uuid.uuid4().int).zfill(16)[-16:]
    h=hold(cid,sid)
    # Confirm/expiry race: either CONFIRMED or EXPIRED, never both/oversold.
    time.sleep(3.8)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda fn:fn(), [lambda:call('POST',f'/holds/{h}/confirm',sid),lambda:call('POST',f'/classes/{cid}/holds','99999999999999999')]))
    detail=class_counts(cid)
    assert detail['confirmedSeats']+detail['heldSeats'] <= 1,(detail,results)
    assert detail['availableSeats'] >= 0,(detail,results)
    assert results[0][0] in (200,409),(detail,results)
    print('PASS expiry-boundary: invariant held+confirmed<=capacity; statuses:',[r[0] for r in results])
if __name__=='__main__':
    assert os.getenv('TEST_HOLD_SECONDS')=='4','Run with dedicated 4-second hold QA stack'
    check()
