"""Synthetic artifacts and mocked complaint deep-verifier adapters; no live/UI."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
from unittest.mock import patch
from datetime import datetime,timezone
sp=importlib.util.spec_from_file_location('fresh_candidate_tests',Path(__file__).resolve().parents[1]/'scripts/fresh_completed_evidence.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
sys.path.insert(0,str(h.PROJECT/'skills/workshop-director/scripts'));import execution_timing as timing
class FreshTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.started='2026-10-22T10:00:00+00:00';self.now=datetime(2026,10,22,11,tzinfo=timezone.utc);self.calls=[]
 def write(self,p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x));return h.reference(p)
 def inspection(self):
  source=self.write(self.root/'source.json',{'company':'synthetic'});key='123:review-synthetic'
  ledger=self.root/'ledger';self.write(ledger/'state.json',{'company':'synthetic','tasks':{}})
  m={'kind':'existing-result-inspection-manifest-v1','root':str(ledger),'review_key':key,'inputs':{'source':source}}
  path=ledger/'existing-result-operations'/hashlib.sha256(key.encode()).hexdigest()/source['sha256']/'operation.json'
  s={'state':'complete','manifest':m,'submission_enabled':False,'send_enabled':False,'created_at':'2026-10-22T10:01:00+00:00','completed_at':'2026-10-22T10:02:01+00:00'}
  for k,t in [('normal_before','10:01:10'),('drawer','10:01:20'),('normal_after','10:02:00.900000')]:s[k]=self.write(path.parent/(k+'.json'),{'observed_at':'2026-10-22T'+t+'+00:00'})
  self.write(path,s);return path,s
 @contextmanager
 def complaint_backend(self,bad=False):
  job={'company':'synthetic','groupid':'123','identity':{'account_id':'synthetic'},'start':'2026-10-21','end_exclusive':'2026-10-22'}
  def inputs(m,**kw):self.calls.append(('inputs',kw));h.read(m['inputs']['source']);return {'job':job},{},{}
  def verify(*args,**kwargs):
   self.calls.append(('verify',))
   if bad:raise ValueError('synthetic-source-invalid')
  runner=SimpleNamespace(manifest_inputs=inputs,verify_complete=verify,workflow=SimpleNamespace(__file__=str(h.PROJECT/'skills/negative-review-complaints/scripts/workflow.py')))
  draft=SimpleNamespace(validate=verify,inputs=lambda *a,**kw:inputs(*a,**kw))
  real=h.modules
  @contextmanager
  def load(skill,names):
   if skill=='negative-review-complaints':yield runner,draft
   else:
    with real(skill,names) as loaded:yield loaded
  with patch.object(h,'modules',load):yield
 def check(self,path,schema='complaint-inspection-v1',role='complaint_operator'):return h.fresh_completed_evidence(path,schema,role=role,dispatch_started_at=self.started,now=self.now)
 def test_inspection_deep_replay_and_source_refs(self):
  path,s=self.inspection()
  with self.complaint_backend():out=self.check(path)
  self.assertEqual(self.calls,[('inputs',{'historical_complete':True}),('verify',)]);self.assertEqual(out['business_identity']['review_key'],s['manifest']['review_key']);self.assertEqual(out['completed_at'],'2026-10-22T10:02:00.900000+00:00');self.assertGreaterEqual(len(out['artifact_refs']),5)
 def test_same_business_dedup_independent_completion_dates(self):
  path,s=self.inspection()
  with self.complaint_backend():a=self.check(path);s['completed_at']='2026-10-22T10:30:00+00:00';self.write(path,s);b=self.check(path)
  self.assertEqual(a['dedup_key'],b['dedup_key']);self.assertEqual(a['business_binding'],b['business_binding']);self.assertEqual(a['completed_at'],b['completed_at'])
 def test_copy_is_not_canonical_operation(self):
  path,s=self.inspection();copy_path=self.root/'copy.json';self.write(copy_path,s)
  with self.complaint_backend(),self.assertRaisesRegex(ValueError,'canonical-operation'):self.check(copy_path)
 def test_unsupported_unfinished_and_legacy_missing_time_none(self):
  path,s=self.inspection();self.assertIsNone(self.check(path,'unsupported'))
  s['state']='opened';self.write(path,s);self.assertIsNone(self.check(path))
  s['state']='complete';s.pop('created_at');self.write(path,s);self.assertIsNone(self.check(path))
 def test_valid_old_complete_no_new_progress(self):
  path,s=self.inspection();s['created_at']='2026-10-21T10:00:00+00:00';self.write(path,s);self.assertIsNone(self.check(path))
 def test_current_malformed_reverse_or_future_time_rejected(self):
  path,s=self.inspection()
  for change in [{'created_at':'invalid'},{'completed_at':'2026-10-22T10:00:00+00:00'},{'completed_at':'2026-10-22T12:00:00+00:00'}]:
   self.write(path,{**s,**change})
   with self.assertRaises(ValueError):self.check(path)
 def test_retimed_old_raw_wrong_order_or_after_completion_rejected(self):
  path,s=self.inspection()
  for t in ['2026-10-21T10:01:10+00:00','2026-10-22T10:03:00+00:00']:
   s['normal_before']=self.write(path.parent/'normal_before.json',{'observed_at':t});self.write(path,s)
   with self.complaint_backend(),self.assertRaises(ValueError):self.check(path)
 def test_changed_ref_deep_error_and_unknown_rejected(self):
  path,s=self.inspection()
  with self.complaint_backend(bad=True),self.assertRaisesRegex(ValueError,'source-invalid'):self.check(path)
  Path(s['manifest']['inputs']['source']['path']).write_text('changed')
  with self.complaint_backend(),self.assertRaises(ValueError):self.check(path)
  s['calls']=[{'state':'unknown'}];self.write(path,s)
  with self.assertRaises(ValueError):self.check(path)
 def test_draft_calls_canonical_validator_and_no_submission(self):
  path,s=self.inspection();m=s['manifest'];m['kind']='complaint-draft-inspection-manifest-v1';s['form']=s.pop('drawer');new=Path(m['root'])/'draft-inspection'/hashlib.sha256(m['review_key'].encode()).hexdigest()/m['inputs']['source']['sha256']/'operation.json';self.write(new,s)
  with self.complaint_backend():out=self.check(new)
  self.assertEqual(out['business_binding']['inspection_kind'],m['kind']);s['submitted']=True;self.write(new,s)
  with self.complaint_backend(),self.assertRaises(ValueError):self.check(new)
 def sender(self):
  key='synthetic-original-sender';payload={'version':'1.0.0','key':key,'kind':'group','target':'测试群请忽略','scope':'test','type':'file','file':str(self.root/'artifact.xlsx'),'file_sha256':hashlib.sha256(b'synthetic').hexdigest(),'file_name':'artifact.xlsx'};Path(payload['file']).write_bytes(b'synthetic')
  s={'job':payload,'fingerprint':hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'complete','phase':'done','sent':True,'ui_confirmed':True,'created_at':'2026-10-22T10:01:00+00:00','completed_at':'2026-10-22T10:02:00+00:00','events':[{'stage':'send-intent','at':'2026-10-22T10:01:05+00:00','sha256':payload['file_sha256'],'file':payload['file_name']},{'stage':'ui-confirmed','at':'2026-10-22T10:02:00+00:00','recipient':payload['target'],'recipient_kind':'group'}]}
  path=self.root/'senders'/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json');self.write(path,s);return path,s
 def test_sender_existing_receipt_replay_canonical_file_and_dedup(self):
  path,s=self.sender()
  with patch.object(timing,'SENDER_DIRECTORY',path.parent):a=self.check(path,'wecom-v1');b=self.check(path,'wecom-v1')
  self.assertEqual(a['dedup_key'],b['dedup_key']);self.assertEqual(len(a['artifact_refs']),2)
 def test_sender_copy_file_tamper_bad_target_or_time_reject(self):
  path,s=self.sender();copied=self.root/'fake.json';self.write(copied,s)
  with patch.object(timing,'SENDER_DIRECTORY',path.parent):
   with self.assertRaises(ValueError):self.check(copied,'wecom-v1')
   Path(s['job']['file']).write_bytes(b'changed')
   with self.assertRaises(ValueError):self.check(path,'wecom-v1')
   s['completed_at']='2026-10-22T10:00:00+00:00';self.write(path,s)
   with self.assertRaises(ValueError):self.check(path,'wecom-v1')
if __name__=='__main__':unittest.main()
