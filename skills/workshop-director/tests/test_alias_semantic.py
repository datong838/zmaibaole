"""Pure semantic adapter tests; deep CLI verifier runs in its own suite."""
import types,json,tempfile,unittest,copy,importlib.util
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
spec=importlib.util.spec_from_file_location('alias_semantic_production',ROOT/'skills/workshop-director/scripts/semantic_progress.py');s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
class AliasSemanticTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.path=Path(self.t.name)/'input.json';self.path.write_text('{}');ref={'path':str(self.path),'sha256':s.checksum(self.path)};self.value={'kind':'unbound-case-operation-v1','state':'complete','submission_enabled':False,'send_enabled':False,'manifest':{'kind':'unbound-case-inspection-manifest-v1','inputs':{'source':ref},'review_key':'gid:case'},'normal_before':ref,'drawer':ref,'normal_after':ref}
 def extract(self,*,failure=False,role='complaint_operator'):
  def verify(*args):
   if failure:raise ValueError('public-case-did-not-match')
   return {'original_review_key':'gid:case','case_signature_sha256':'fixed'}, {}, []
  loader=types.SimpleNamespace(exec_module=lambda _:None);module=types.SimpleNamespace(alias_verified=verify)
  with patch.object(s.importlib.util,'spec_from_file_location',return_value=types.SimpleNamespace(loader=loader)),patch.object(s.importlib.util,'module_from_spec',return_value=module):return s.extract(self.value,role,journal_path=self.path)
 def test_new_complete_schema_is_separate_deep_verified_token(self):
  out=self.extract();self.assertEqual(out['schema'],'complaint-case-alias-inspection-v1');self.assertEqual(list(out['tokens']),['closed-case-alias'])
 def test_incomplete_ready_is_baseline_not_progress(self):
  self.value['state']='ready';self.assertEqual(self.extract()['tokens'],{})
 def test_wrong_role_or_unknown_state_is_attention(self):
  with self.assertRaises(ValueError):self.extract(role='daily_stats_operator')
  self.value['state']='unknown-open'
  with self.assertRaisesRegex(ValueError,'unknown-alias'):self.extract()
 def test_mismatching_case_cannot_make_progress(self):
  with self.assertRaisesRegex(ValueError,'public-case'):self.extract(failure=True)
 def test_edited_input_or_policy_is_rejected(self):
  self.value['send_enabled']=True
  with self.assertRaisesRegex(ValueError,'policy'):self.extract()
  self.value['send_enabled']=False;self.path.write_text('changed')
  with self.assertRaisesRegex(ValueError,'evidence-changed'):self.extract()
if __name__=='__main__':unittest.main()
