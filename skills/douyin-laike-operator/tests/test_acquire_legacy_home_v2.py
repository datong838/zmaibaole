"""Pinned real readonly sample and original confirmed journal; TEMP writes only."""
import copy,hashlib,json,tempfile,types,unittest,importlib.util
from pathlib import Path
from switch_read_fixture import m,OP,RecoveryFixture
F=Path(__file__).parent/'fixtures/acquire-legacy-home-v2'
def doc(name):return json.loads((F/name).read_bytes())
def raw(name):return doc(name)['result']
class Tests(unittest.TestCase):
 def setUp(self):
  self.job=doc('job.json');self.s=doc('journal.json');self.sample={'before':raw('01-tabs-raw.json'),'ping':raw('02-ping-raw.json'),'tree':raw('03-tree-raw.json'),'after':raw('04-tabs-raw.json')}
 def test_pinned_actual_sample_is_only_provisional_not_identity(self):
  for name,ref in doc('provenance.json').items():self.assertEqual(m.sha((F/name).read_bytes()),ref['sha256'])
  self.assertEqual(m.sha((F/'journal.json').read_bytes()),'2d75d79c6f15100c2300f99b0033c15a3ff248d4bec0a5d3e1366dec77abe427');self.assertEqual(m.sha((F/'03-tree-raw.json').read_bytes()),'782f40c27ccd2f95cce0fedfa90dd957a55bdf962d920fab45a0a23f84bb6b68')
  facts=m.verify_sample(self.job,self.s,self.sample);self.assertEqual(self.job['action'],'acquire');self.assertTrue(facts['legacy_home_v2_provisional']);self.assertFalse(facts['full_identity_observed']);self.assertFalse(facts['company_label_observed']);self.assertEqual(facts['groupid'],self.job['groupid'])
 def test_wrong_provider_gid_window_and_queryless_reject(self):
  for mode in ('provider','gid','window','queryless'):
   sample=copy.deepcopy(self.sample)
   if mode=='provider':next(n for n in m.walk(sample['tree']) if 'Profile-index-module__title--' in n.get('attributes',{}).get('class',''))['name']='服务商000000000'
   else:
    for key in ('before','after'):
     scope=m.contract(self.job,self.s);tab=next(t for w in sample[key] for t in w['tabs'] if t['tabId']==scope['tab_id'])
     if mode=='gid':tab['url']=tab['url'].replace(scope['groupid'],'999999999')
     elif mode=='window':tab['windowId']=0
     else:tab['url']='https://life.douyin.com/p/home'
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.verify_sample(self.job,self.s,sample)
 def test_v3_card_accountinfo_ambiguous_roots_or_header_refuse(self):
  for mode in ('v3','card','accountinfo','root','header'):
   sample=copy.deepcopy(self.sample);tree=sample['tree'];nodes=list(m.walk(tree))
   if mode in ('root','header'):
    marker='HomeV2-index-module__container--' if mode=='root' else 'Profile-index-module__title--';tree['root']['children'].append(copy.deepcopy(next(n for n in nodes if marker in n.get('attributes',{}).get('class',''))))
   else:tree['root']['children'].append({'tag':'div','name':'x','children':[],'attributes':{'class':{'v3':'src-pages-HomeV3-index-module__container--x','card':'UserCard-index-module__outer--x','accountinfo':'AccountInfo-module__other--x'}[mode]}})
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.verify_sample(self.job,self.s,sample)
 def test_unknown_export_download_intent_or_wrong_confirm_chain_refuse(self):
  for mode in ('unknown','export','download','checkpoint','pending','choose'):
   s=copy.deepcopy(self.s)
   if mode=='unknown':s['calls'][-1]['state']='unknown'
   elif mode in ('export','download'):s['calls'][-1]['command']['kind']=mode
   elif mode=='checkpoint':s['checkpoints'].append({'stage':'export-intent'})
   elif mode=='pending':s['exportPending']={'x':1}
   else:next(c for c in s['calls'] if c['phase']=='chooseCompany')['result']['clicked']['name']='another'
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.verify_sample(self.job,s,self.sample)
 def test_old_gov_route_still_rejects_instead_of_broadening_route_allowlist(self):
  with self.assertRaisesRegex(ValueError,'read-recovery-route-risk'):m.verify_sample(self.job,self.s,doc('old-rejected-sample.json'))
 def test_explicit_temp_reconcile_four_readonly_calls_preserves_unknown_intent_chain(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);job=copy.deepcopy(self.job);s=copy.deepcopy(self.s);old=p/'old-tree.json';old.write_bytes((F/'original-tree.json').read_bytes());s['last_tree']=m.ref(old);journal=p/'workflow.json';jobfile=p/'job.json';job.update(workflow_path=str(journal),work_order_path=str(jobfile));journal.write_bytes(m.encoded(s));jobfile.write_bytes(m.encoded(job));original=journal.read_bytes();seen=[]
   def invoke(cmd):
    seen.append(cmd);self.assertIn(cmd['op'],('tabs','ping','tree'));return copy.deepcopy(self.sample['before' if cmd['op']=='tabs' else cmd['op']])
   result=m.reconcile(jobfile,m.sha(original),invoke);self.assertEqual(result['phase'],'accountAfterSwitch');self.assertEqual([c['op'] for c in seen],['tabs','ping','tree','tabs']);new=json.loads(journal.read_bytes());self.assertEqual(new['calls'],s['calls']);self.assertEqual(new['date_range'],s['date_range']);proof=m.verify_recovered(new,result['proof']);self.assertFalse(proof['facts']['full_identity_observed']);self.assertEqual(Path(proof['original_journal']['path']).read_bytes(),original);self.assertNotIn('result',new)
 def test_account_full_identity_required_before_openreviews(self):
  spec=importlib.util.spec_from_file_location('legacy_acquire_identity_runtime',OP/'bridge-workflow.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
  w=runtime.Workflow.__new__(runtime.Workflow);w.job=copy.deepcopy(self.job);w.s=copy.deepcopy(self.s);w.s['phase']='identityAfterSwitch';w.s.pop('last_error',None);w.save=lambda:None;w.tree=lambda:copy.deepcopy(self.sample['tree']);w.invoke=lambda c:None;w.call=lambda c:copy.deepcopy(self.sample['before' if c['op']=='tabs' else c['op']]);w.ensure_source_active=lambda tabs,current:(tabs,current)
  with self.assertRaises(ValueError):w.tick()
  self.assertEqual(w.s['phase'],'identityAfterSwitch');self.assertFalse(any(c.get('stage')=='switch' for c in w.s['checkpoints']))
class ByteCompatibility(RecoveryFixture):
 def test_old_supported_sample_facts_bytes_unchanged(self):
  before=types.ModuleType('old_recovery');exec(compile((F/'switch_read_recovery.py.before').read_bytes(),'before','exec'),before.__dict__)
  sample={'before':self.tabs(),'after':self.tabs(),'tree':self.tree(),'ping':{'version':'dom-only-20261021-11','safety':'DOM-only'}}
  self.assertEqual(before.encoded(before.verify_sample(self.job,self.s,sample)),m.encoded(m.verify_sample(self.job,self.s,sample)))

 def test_old_generated_readonly_proof_bytes_still_verify(self):
  before=types.ModuleType('old_recovery_proof');exec(compile((F/'switch_read_recovery.py.before').read_bytes(),'before','exec'),before.__dict__)
  result=before.reconcile(self.jobpath,self.original_sha,self.invoke);proof_path=Path(result['proof']['path']);raw=proof_path.read_bytes();current=json.loads(self.file.read_bytes());proof=m.verify_recovered(current,result['proof']);self.assertEqual(proof_path.read_bytes(),raw);self.assertEqual(proof['original_calls'],self.s['calls'])
