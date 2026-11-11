import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RepositoryTests(unittest.TestCase):
 def test_exact_documented_routes(self):
  text=(ROOT/'backend/SchoolAdmission.Api/Program.cs').read_text()
  for method,path in [('Post','/classes'),('Get','/classes'),('Get','/classes/{classId}'),('Post','/classes/{classId}/holds'),('Get','/holds/{holdId}'),('Post','/holds/{holdId}/confirm'),('Delete','/holds/{holdId}'),('Get','/me/holds')]:
   self.assertIn(f'app.Map{method}("{path}"',text)
 def test_no_hardcoded_db_password(self):
  text=(ROOT/'backend/SchoolAdmission.Api/Program.cs').read_text()
  self.assertNotIn('Password=admissions123',text)
 def test_named_volume(self):
  self.assertIn('admissions_data:',(ROOT/'docker-compose.yml').read_text())
 def test_isolated_qa_name(self):
  self.assertIn("PROJECT='admission-qa-'",(ROOT/'tests/run_isolated_qa.py').read_text())
if __name__=='__main__':unittest.main()
