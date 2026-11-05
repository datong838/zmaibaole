"""Synthetic time/dispatch integration; alias deep replay has separate CLI tests."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('alias_fresh_candidate',Path(__file__).resolve().parents[1]/'scripts/fresh_completed_evidence.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
class AliasFreshTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.path=self.root/'operation.json';self.start='2026-10-22T10:00:00+00:00';self.now=datetime(2026,10,22,11,tzinfo=timezone.utc)
  self.s={'kind':'unbound-case-operation-v1','state':'complete','created_at':'2026-10-22T10:00:01+00:00','completed_at':'2026-10-22T10:01:30+00:00','submission_enabled':False,'send_enabled':False}
  for name,t in [('normal_before','10:00:10'),('drawer','10:00:30'),('normal_after','10:01:00')]:
   p=self.root/(name+'.json');p.write_text(json.dumps({'observed_at':'2026-10-22T'+t+'+00:00'}));self.s[name]=h.reference(p)
  self.path.write_text(json.dumps(self.s));self.proof={'original_review_key':'gid:original','case_signature_sha256':'stable'};self.binding={'review_key':'gid:original','old_source_sha256':'old-source'}
 def check(self,**kwargs):
  with patch.object(h,'alias_verified',return_value=(self.proof,self.binding,[h.reference(self.path)])):
   return h.fresh_completed_evidence(self.path,'complaint-case-alias-inspection-v1',role=kwargs.get('role','complaint_operator'),dispatch_started_at=self.start,now=self.now)
 def test_first_closed_progress_time_comes_from_raw_after_not_later_completed_or_read(self):
  out=self.check();self.assertEqual(out['completed_at'],'2026-10-22T10:01:00+00:00');self.assertEqual(out['schema'],'complaint-case-alias-inspection-v1')
 def test_same_case_business_dedup_ignores_state_timestamp(self):
  one=self.check();self.s['completed_at']='2026-10-22T10:30:00+00:00';self.path.write_text(json.dumps(self.s));two=self.check();self.assertEqual(one['dedup_key'],two['dedup_key']);self.assertEqual(one['completed_at'],two['completed_at'])
 def test_old_closure_none_without_recredit(self):
  self.start='2026-10-22T10:10:00+00:00';self.assertIsNone(self.check())
 def test_retimed_old_normal_page_cannot_refresh(self):
  self.s['created_at']='2026-10-22T10:00:20+00:00';self.path.write_text(json.dumps(self.s))
  with self.assertRaisesRegex(ValueError,'page-time-invalid'):self.check()
 def test_deep_verification_failure_rejected(self):
  with patch.object(h,'alias_verified',side_effect=ValueError('wrong-public-case')):
   with self.assertRaisesRegex(ValueError,'wrong-public-case'):h.fresh_completed_evidence(self.path,'complaint-case-alias-inspection-v1',role='complaint_operator',dispatch_started_at=self.start,now=self.now)
 def test_wrong_role_and_future_completion_rejected(self):
  with self.assertRaisesRegex(ValueError,'role-schema'):self.check(role='violation_operator')
  self.s['completed_at']='2026-10-22T12:00:00+00:00';self.path.write_text(json.dumps(self.s))
  with self.assertRaisesRegex(ValueError,'closure-time-invalid'):self.check()
 def test_unknown_not_progress(self):
  self.s['state']='unknown-open';self.path.write_text(json.dumps(self.s));self.assertIsNone(self.check())
if __name__=='__main__':unittest.main()
