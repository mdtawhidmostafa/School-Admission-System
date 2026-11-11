"""Source-based cleanup regressions; not a substitute for dotnet build or browser tests."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def source(path):
    return (ROOT / path).read_text(encoding='utf-8')

class CleanupRegressions(unittest.TestCase):
    def test_single_transition_implementation(self):
        service = source('backend/SchoolAdmission.Api/Services/HoldTransitionService.cs')
        program = source('backend/SchoolAdmission.Api/Program.cs')
        self.assertEqual(service.count('internal static async Task<IResult> ExecuteAsync'), 1)
        self.assertEqual(service.count("status='CONFIRMED'"), 1)  # exactly one SQL transition
        self.assertNotIn('static async Task<IResult> ChangeHoldAsync', program)
        self.assertIn('HoldTransitionService.ExecuteAsync', program)

    def test_admin_key_in_dedicated_helper(self):
        program = source('backend/SchoolAdmission.Api/Program.cs')
        helper = source('backend/SchoolAdmission.Api/Security/AdminKeyAuthorization.cs')
        self.assertIn('FixedTimeEquals', helper)
        self.assertNotIn('FixedTimeEquals', program)

    def test_frontend_single_persistence_hook(self):
        main = source('frontend/src/main.tsx')
        saved = source('frontend/src/hooks/useSavedField.ts')
        self.assertIn('useSavedField(', main)
        self.assertNotIn('localStorage.setItem', main)
        self.assertIn('localStorage.setItem', saved)

    def test_history_and_classes_independent(self):
        hook = source('frontend/src/hooks/useAdmissionData.ts')
        self.assertIn('Promise.allSettled', hook)
        self.assertIn('setClassError', hook)
        self.assertIn('setHistoryError', hook)
        self.assertIn('setHolds([])', hook)

if __name__ == '__main__':
    unittest.main()
