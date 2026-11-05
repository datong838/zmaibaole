import importlib.util,json,sys,unittest,copy,types
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/tests'))
import switch_read_fixture as fixture
spec=importlib.util.spec_from_file_location('return_recovery',ROOT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);fixture.m=m
class ReturnReadTests(fixture.RecoveryFixture):
 def navigation(self):
  self.job.update(action='return-company',navigation_only=True,progress_updates_enabled=False,export_enabled=False,send_enabled=False);self.job.pop('date_range');self.job.pop('source_dir');self.s.update(date_range={},fingerprint=m.fingerprint(self.job));self.file.write_bytes(m.encoded(self.s));self.jobpath.write_bytes(m.encoded(self.job));self.original=self.file.read_bytes();self.original_sha=m.sha(self.original)
 def queryless(self,c):
  if c['op']=='tabs':
   t=self.tabs();t[0]['tabs'][0]['url']='https://life.douyin.com/p/home';return t
  return self.invoke(c)
 def test_return_queryless_home_is_transition_not_observed_gid(self):
  self.navigation();r=self.runrepair(self.queryless);self.assertEqual(r['state'],'reconciled');proof=m.verify_recovered(json.loads(self.file.read_bytes()),r['proof']);f=proof['facts'];self.assertIsNone(f['groupid']);self.assertFalse(f['url_groupid_observed']);self.assertEqual(f['target_groupid'],'222');self.assertFalse(f['full_identity_observed']);self.assertEqual(proof['original_calls'],self.s['calls'])
 def test_acquire_queryless_remains_rejected(self):
  self.assertEqual(self.runrepair(self.queryless)['state'],'hold');self.assertEqual(self.file.read_bytes(),self.original)
 def test_return_query_gid_supported_without_extra_claim_fields(self):
  self.navigation();r=self.runrepair();self.assertEqual(r['state'],'reconciled');self.assertNotIn('url_groupid_observed',m.document(r['proof'])['facts'])
 def test_navigation_flags_and_dates_required(self):
  self.navigation()
  for key,value in [('navigation_only',False),('send_enabled',True),('export_enabled',True),('progress_updates_enabled',True),('date_range',{'start':'2026-10-21','end':'2026-10-21'})]:
   j=copy.deepcopy(self.job);j[key]=value;s=copy.deepcopy(self.s);s['fingerprint']=m.fingerprint(j)
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'navigation-only-contract'):m.contract(j,s)
 def test_wrong_company_window_provider_refused(self):
  self.navigation()
  for wrong in ('company','provider','window'):
   def bad(c):
    v=self.queryless(c)
    if c['op']=='tree':v['root']['children'][0 if wrong=='company' else 1]['name']='wrong'
    if c['op']=='tabs' and wrong=='window':v[0]['windowId']=7
    return v
   r=self.runrepair(bad);self.assertEqual(r['state'],'hold');self.assertEqual(self.file.read_bytes(),self.original)
 def test_return_runtime_tick_uses_same_readonly_branch(self):
  self.navigation();self.s.pop('last_error');self.file.write_bytes(m.encoded(self.s))
  runtime=types.ModuleType('return_switch_runtime');runtime.__file__=str(ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')
  exec(compile((ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py').read_text(),runtime.__file__,'exec'),runtime.__dict__)
  w=runtime.Workflow.__new__(runtime.Workflow);w.job=self.job;w.file=self.file;w.s=copy.deepcopy(self.s);w.invoke=self.queryless
  with patch.dict(sys.modules,{'switch_read_recovery':m}):result=w.tick()
  self.assertEqual(result['phase'],'accountAfterSwitch');self.assertEqual(result['calls'],self.s['calls']);self.assertTrue(all(c['op'] in ('tabs','tree','ping') for c in self.seen))
 def test_original_actual_stopped_return_job_contract_pure(self):
  p=Path(__file__).parent/'fixtures/return-switch-read-original-a00f921';manifest=json.loads((p/'provenance.json').read_bytes())
  for name,record in manifest.items():self.assertEqual(m.sha((p/name).read_bytes()),record['sha256'])
  self.assertEqual(manifest['original-journal.json']['sha256'],'a00f921cc6225aaa3f48e9d0ae2b68da93f8c7256ce3c6e583c6d47cd052cace')
  job=json.loads((p/'original-job.json').read_bytes());s=json.loads((p/'original-journal.json').read_bytes());scope=m.contract(job,s);self.assertTrue(scope['allow_queryless_home']);self.assertEqual(scope['groupid'],'1764303851132943')
if __name__=='__main__':unittest.main()
