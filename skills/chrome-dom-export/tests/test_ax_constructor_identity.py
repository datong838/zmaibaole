import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import ax_capture_grant as a
import chrome_process_identity as c
from test_chrome_process_identity import CLONE
class ConstructorIdentityTests(unittest.TestCase):
 def test_original_main_executable_remains_exact_without_new_signature_path(self):
  with patch.object(c,'verify',side_effect=AssertionError('old branch must stay original')):
   self.assertEqual(a.checked_executable_identity(c.EXE),{'executable':c.EXE})
 def test_only_reviewed_clone_delegates_same_public_signature_checker(self):
  proof={'kind':'validated-google-main-code'}
  with patch.object(c,'verify',return_value=proof) as verify:
   value=a.checked_executable_identity(CLONE);verify.assert_called_once_with(CLONE)
  self.assertEqual(value,{'executable':CLONE,'executable_identity':proof})
 def test_arbitrary_path_rejects_before_signature_and_failed_signature_rejects(self):
  with patch.object(c,'verify',side_effect=AssertionError('no arbitrary pathname')):
   with self.assertRaisesRegex(a.GrantError,'path-mismatch'):a.checked_executable_identity('/tmp/Google Chrome.app/Contents/MacOS/Google Chrome')
  with patch.object(c,'verify',side_effect=ValueError('chrome-signed-main-code-invalid')):
   with self.assertRaisesRegex(ValueError,'code-invalid'):a.checked_executable_identity(CLONE)
if __name__=='__main__':unittest.main()
