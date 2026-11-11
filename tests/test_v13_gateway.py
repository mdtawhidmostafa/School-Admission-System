"""Offline assertions; runtime Nginx verification is separate."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GatewayPolicy(unittest.TestCase):
    def test_mutation_coverage(self):
        s=(ROOT/'frontend/nginx.conf').read_text()
        for pattern in ('POST:/api/classes$', 'POST:/api/classes/[^/]+/holds$', 'POST:/api/holds/[^/]+/confirm$', 'DELETE:/api/holds/[^/]+$'):
            self.assertIn(pattern,s)
    def test_retry_safety(self):
        s=(ROOT/'frontend/nginx.conf').read_text()
        self.assertNotIn('proxy_next_upstream non_idempotent',s)
        self.assertIn('proxy_next_upstream_tries 3',s)
    def test_gateway_errors_are_json(self):
        s=(ROOT/'frontend/nginx.conf').read_text()
        self.assertIn('"RATE_LIMITED"',s)
        self.assertIn('Retry-After 1',s)
    def test_no_lockfile_fabrication(self):
        # This is a blocking release prerequisite, not something source tests can waive.
        self.assertTrue((ROOT/'scripts/generate-lockfiles.sh').exists())
if __name__=='__main__':unittest.main()
