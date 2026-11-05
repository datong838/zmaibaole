"""Synthetic recovery regression. Public reads are fakes; files are temporary."""
import copy,importlib.util,json,unittest
from pathlib import Path
from switch_read_fixture import RecoveryFixture,m,OP
class SwitchReadRecoveryTests(RecoveryFixture):
 def test_success_preserves_bytes_calls_error_and_tree(self):
  original_tree=Path(self.s['last_tree']['path']).read_bytes();r=self.runrepair();self.assertEqual(r['state'],'reconciled');s=json.loads(self.file.read_bytes());proof=m.verify_recovered(s,r['proof']);self.assertEqual(s['phase'],'accountAfterSwitch');self.assertEqual(s['calls'],self.s['calls']);self.assertEqual(Path(proof['original_journal']['path']).read_bytes(),self.original);self.assertEqual(Path(self.s['last_tree']['path']).read_bytes(),original_tree);self.assertEqual(s['resolved_errors'][0]['code'],self.s['last_error']['code']);self.assertFalse(proof['facts']['full_identity_observed']);self.assertEqual(len(self.seen),4)

 def test_absent_provider_is_transition_not_identity_verification(self):
  def invoke(c):
   if c['op']=='tree':
    t=self.tree();t['root']['children'].pop();return t
   return self.invoke(c)
  result=self.runrepair(invoke);self.assertEqual(result['state'],'reconciled');facts=m.document(result['proof'])['facts']
  self.assertFalse(facts['provider_observed']);self.assertIsNone(facts['provider']);self.assertFalse(facts['full_identity_observed']);self.assertEqual(facts['provider_baseline'],self.ident['provider'])
 def test_background_unfocused_read_does_not_activate(self):
  def invoke(c):
   if c['op']=='tabs':
    t=self.tabs();t[0]['focused']=False;t[0]['tabs'][0]['active']=False;return t
   return self.invoke(c)
  result=self.runrepair(invoke);self.assertEqual(result['state'],'reconciled');self.assertTrue(all(c['op'] in ('tabs','tree','ping') for c in self.seen))

 def test_route_race_bounded_then_success(self):
  n=0
  def invoke(c):
   nonlocal n
   if c['op']=='tabs':n+=1;return self.tabs('111' if n==1 else '222')
   return self.invoke(c)
  r=self.runrepair(invoke);self.assertEqual(r['state'],'reconciled');self.assertEqual(n,4);self.assertEqual(len(list((self.p/'switch-read-recovery').rglob('*sample.json'))),2)

 def test_bounded_three_old_samples_then_same_sha_resume(self):
  def old(c):return self.tabs('111') if c['op']=='tabs' else self.invoke(c)
  r=self.runrepair(old);self.assertEqual(r['state'],'hold');self.assertEqual(self.file.read_bytes(),self.original);self.assertEqual(len(list((self.p/'switch-read-recovery').rglob('*sample.json'))),3);self.assertEqual(self.runrepair()['state'],'reconciled')

 def test_host_or_window_risk_no_retry(self):
  for mode in ('host','window'):
   with self.subTest(mode=mode):
    calls=[]
    def bad(c):
     calls.append(c);t=self.tabs(host='evil.invalid' if mode=='host' else 'life.douyin.com')
     if mode=='window':t[0]['windowId']=7
     return t
    r=self.runrepair(bad);self.assertEqual(r['state'],'hold');self.assertEqual(len(calls),1);self.assertEqual(self.file.read_bytes(),self.original)

 def test_no_query_home_holds_not_navigation_exception(self):
  def noquery(c):
   t=self.tabs();t[0]['tabs'][0]['url']='https://life.douyin.com/p/home';return t
  self.assertEqual(self.runrepair(noquery)['error'],'read-recovery-group-risk');self.assertEqual(self.file.read_bytes(),self.original)

 def test_conflicting_provider_or_wrong_company_does_not_advance(self):
  for bad in ('provider','company'):
   def invoke(c):
    if c['op']=='tree':
     t=self.tree();t['root']['children'][1 if bad=='provider' else 0]['name']='wrong';return t
    return self.invoke(c)
   self.assertEqual(self.runrepair(invoke)['state'],'hold');self.assertEqual(self.file.read_bytes(),self.original)

 def test_visible_wrong_card_and_unknown_and_wrong_sha_refused(self):
  def invoke(c):
   if c['op']=='tree':
    t=self.tree();t['root']['children'].append({'attributes':{'class':'UserCard-index-module__outer--xxx'},'name':'服务商123456789 账户ID 99999999999 我的客户经理 错误 退出登录'});return t
   return self.invoke(c)
  self.assertEqual(self.runrepair(invoke)['error'],'read-recovery-card-identity-risk');self.assertEqual(self.file.read_bytes(),self.original)
  with self.assertRaisesRegex(ValueError,'original-sha'):m.reconcile(self.jobpath,'0'*64,self.invoke)
  self.s['calls'][-1]['state']='unknown';self.file.write_bytes(m.encoded(self.s))
  with self.assertRaisesRegex(ValueError,'unknown'):m.reconcile(self.jobpath,m.sha(self.file.read_bytes()),self.invoke)

 def test_failed_transport_preserved_and_repeat_read_only(self):
  def failure(c):return {'ok':False,'error':'Frame removed'}
  r=self.runrepair(failure);self.assertEqual(r['state'],'hold');self.assertTrue(list((self.p/'switch-read-recovery').rglob('*transport.json')));self.assertEqual(self.runrepair()['state'],'reconciled')

 def test_regular_verify_switch_is_bounded_and_read_only(self):
  spec=importlib.util.spec_from_file_location('candidate_switch_workflow',OP/'bridge-workflow.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
  self.s.pop('last_error');self.file.write_bytes(m.encoded(self.s));w=runtime.Workflow.__new__(runtime.Workflow);w.job=self.job;w.file=self.file;w.s=copy.deepcopy(self.s);w.invoke=self.invoke
  result=w.tick();self.assertEqual(result['phase'],'accountAfterSwitch');self.assertEqual(result['calls'],self.s['calls']);self.assertTrue(all(c['op'] in ('tabs','ping','tree') for c in self.seen))

 def test_recovered_evidence_tampering_and_second_attempt_refused(self):
  r=self.runrepair();original_reads=len(self.seen)
  with self.assertRaisesRegex(ValueError,'current-original-changed'):self.runrepair()
  self.assertEqual(len(self.seen),original_reads)
  s=json.loads(self.file.read_bytes());proof=m.document(r['proof']);sample=Path(proof['sample']['path']);sample.write_bytes(sample.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'evidence-changed'):m.verify_recovered(s,r['proof'])

if __name__=='__main__':unittest.main()
