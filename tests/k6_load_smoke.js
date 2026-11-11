// Execute only against a disposable QA deployment. This is NOT a capacity certification.
import http from 'k6/http';
import { check, sleep } from 'k6';
export const options = { scenarios: { browse: { executor: 'constant-vus', vus: Number(__ENV.VUS || 20), duration: __ENV.DURATION || '20s' } }, thresholds: { http_req_failed: ['rate<0.02'], http_req_duration: ['p(95)<1500'] } };
const base=__ENV.GATEWAY_URL || 'http://127.0.0.1:13080';
export default function () {
  const response=http.get(base+'/api/classes');
  check(response, {'class listing succeeded': r=>r.status===200});
  sleep(1);
}
