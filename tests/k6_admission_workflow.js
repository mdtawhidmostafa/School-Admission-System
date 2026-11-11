// Disposable QA stack ONLY. POST/DELETE are rate-limited per IP; 429 is a valid load-shedding outcome.
import http from 'k6/http';
import { check, sleep } from 'k6';
const base = (__ENV.GATEWAY_URL || 'http://127.0.0.1:13080').replace(/\/$/, '');
const vu = Number(__ENV.VUS || 12);
export const options = {
  scenarios: { admission: { executor: 'constant-vus', vus: vu, duration: __ENV.DURATION || '30s' } },
  thresholds: { http_req_failed: ['rate<0.80'], http_req_duration: ['p(95)<5000'] }
};
const json = {headers:{'Content-Type':'application/json'}};
export function setup() {
  const res = http.post(base+'/api/classes', JSON.stringify({name:'k6-'+Date.now(),totalSeats:20}), json);
  if(res.status!==201) throw new Error('QA class create failed: '+res.status+' '+res.body);
  return {classId:res.json('id')};
}
export default function(data) {
  const student = String(__VU).padStart(6,'0')+String(__ITER).padStart(11,'0');
  const headers = {'X-Student-Id':student};
  const h = http.post(base+'/api/classes/'+data.classId+'/holds', null, {headers});
  check(h, {'hold expected outcome':r=>[201,409,429].includes(r.status), 'no server error':r=>r.status<500});
  if(h.status===201) {
    const id = h.json('holdId');
    const r = __ITER%2===0
      ? http.post(base+'/api/holds/'+id+'/confirm',null,{headers})
      : http.del(base+'/api/holds/'+id,null,{headers});
    check(r, {'transition expected outcome':x=>[200,204,409,429].includes(x.status), 'transition no 5xx':x=>x.status<500});
  }
  const c=http.get(base+'/api/classes/'+data.classId);
  check(c, {'class reachable':r=>r.status===200});
  if(c.status===200) {
    const body=c.json();
    check(c, {'capacity invariant':()=>body.heldSeats+body.confirmedSeats<=body.totalSeats && body.availableSeats>=0});
  }
  sleep(0.25);
}
