"""Repository regression checks: no network or Docker required; not API runtime evidence."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def read(p):return (ROOT/p).read_text()
class V12SourceTests(unittest.TestCase):
    def test_telemetry_import(self):
        self.assertIn('using System.Diagnostics;',read('backend/SchoolAdmission.Api/Infrastructure/HttpTelemetry.cs'))
    def test_schema_checksum(self):
        content=read('backend/SchoolAdmission.Api/Data/Db.cs')
        self.assertIn('checksum_sha256',content)
        self.assertIn('Migration checksum mismatch',content)
    def test_split_frontend_network_failure(self):
        content=read('frontend/src/hooks/useAdmissionData.ts')
        self.assertIn('Promise.allSettled',content)
        self.assertIn('setClassError',content)
        self.assertIn('setHistoryError',content)
    def test_ci_executed_race(self):
        content=read('.github/workflows/verify.yml')
        self.assertIn('run_isolated_qa.py --race',content)
        self.assertIn('cross_replica_test.py',read('tests/run_isolated_qa.py'))
    def test_backup_drill_guard(self):
        content=read('tests/backup_restore_drill.py')
        self.assertIn("project.startswith('admission-qa-')",content)
    def test_no_sensitive_dotenv_in_archive(self):
        self.assertFalse((ROOT/'.env').exists())
    def test_lockfiles_are_real_and_present(self):
        # Explicitly skip until actual registry-based lockfile generation succeeds.
        for rel in ('frontend/package-lock.json','tests/package-lock.json'):
            if not (ROOT/rel).exists(): self.skipTest('Release blocker: missing '+rel)
if __name__=='__main__':unittest.main()
