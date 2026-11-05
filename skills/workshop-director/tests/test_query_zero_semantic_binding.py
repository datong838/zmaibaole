"""Portable synthetic job/DOM replay; never connects to Chrome or writes real state."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SKILLS=Path(__file__).resolve().parents[2]
VIO=SKILLS/'violation-notifier';sys.path.insert(0,str(VIO/'scripts'));sys.path.insert(0,str(VIO/'tests'))
from zero_source_fixtures import Evidence,q
import governance_dom as g
import test_governance_dom as positive
spec=importlib.util.spec_from_file_location('zero_bound_semantic',SKILLS/'workshop-director/scripts/semantic_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class QueryZeroBindingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.e=Evidence(self,self.root);self.path=self.root/'new-query.json';self.jobref={'path':str(self.e.jobpath.resolve()),'sha256':q.nav.digest(self.e.jobpath)}
 def runner(self):return q.Runner(self.e.job,5,self.path,q.nav.VERSION,self.e.invoke,job_ref=self.jobref)
 def completed(self):
  runner=self.runner();self.assertTrue(self.path.is_file());self.assertEqual(json.loads(self.path.read_bytes())['query_job_binding']['job'],self.jobref);self.assertEqual(self.e.events,[])
  tree=runner.observe();page=g.records_page(tree,start=self.e.job['start'],end_exclusive=self.e.job['end_exclusive']);page['observation']=runner.s['last_observation'];runner.s.update(pages=[page],rows=[],phase='capture-complete');runner.save();return runner
 def extract(self,state):return m.extract(state,'violation_operator',journal_path=self.path)
 def rewrite_observation(self,runner,change):
  ref=runner.s['pages'][0]['observation'];path=Path(ref['path']);raw=json.loads(path.read_bytes());change(raw);q.nav.write_json(path,raw);runner.s['pages'][0]['observation']={'path':str(path),'sha256':q.nav.digest(path)}
 def test_zero_original_job_scope_gives_single_completed_token(self):
  runner=self.completed();out=self.extract(runner.s);self.assertEqual(list(out['tokens']),['records-page:1']);self.assertEqual(runner.s['query_job_binding']['window_id'],3);self.assertTrue(all(c['op'] in ('tabs','tree','ping') for c in self.e.events))
 def test_wrong_date_does_not_borrow_dom_or_zero_flag(self):
  runner=self.completed();self.rewrite_observation(runner,lambda raw:g.date_input(raw['tree'])['attributes'].update(value='2026/10/17 ～ 2026/10/20'))
  with self.assertRaisesRegex(ValueError,'date-filter-mismatch'):self.extract(runner.s)
 def test_original_job_tampering_or_changed_fingerprint_rejected(self):
  runner=self.completed();raw=self.e.jobpath.read_bytes();self.e.jobpath.write_bytes(raw+b' ')
  with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):self.extract(runner.s)
  self.e.jobpath.write_bytes(raw);runner.s['fingerprint']='wrong'
  with self.assertRaisesRegex(ValueError,'fingerprint-conflict'):self.extract(runner.s)
 def test_original_receipt_bytes_are_revalidated(self):
  runner=self.completed();receipt=Path(self.e.job['identity_receipt']);receipt.write_bytes(receipt.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):self.extract(runner.s)
 def test_unbound_legacy_zero_is_explicitly_unsupported(self):
  runner=self.completed();runner.s.pop('query_job_binding')
  with self.assertRaisesRegex(ValueError,'semantic-zero-query-job-binding-required'):self.extract(runner.s)
 def test_wrong_job_scope_receipt_and_window_rejected(self):
  runner=self.completed()
  for mode in ('window','tab','group','identity','journal'):
   with self.subTest(mode=mode):
    state=copy.deepcopy(runner.s)
    if mode=='window':state['query_job_binding']['window_id']=4
    if mode=='tab':state['query_job_binding']['tab_id']=6
    if mode=='journal':state['query_job_binding']['query_state_path']=str(self.root/'other.json')
    if mode in ('group','identity'):
     changed=copy.deepcopy(self.e.job);changed['groupid']='999' if mode=='group' else changed['groupid']
     if mode=='identity':changed['identity']['manager']='错'
     f=self.root/(mode+'-job.json');q.nav.write_json(f,changed);state['query_job_binding']['job']={'path':str(f),'sha256':q.nav.digest(f)}
    with self.assertRaises(ValueError):self.extract(state)
 def test_unknown_or_error_is_not_reconciled(self):
  runner=self.completed()
  for change in ({'calls':[{'state':'unknown'}]},{'last_error':'original failure'},{'hold':True}):
   state=copy.deepcopy(runner.s);state.update(change)
   with self.assertRaises(ValueError):self.extract(state)
 def test_saved_zero_page_must_equal_reparsed_dom(self):
  runner=self.completed();runner.s['pages'][0]['empty_result']['empty_selector']='#fake'
  with self.assertRaisesRegex(ValueError,'not-proved-by-dom'):self.extract(runner.s)
 def test_old_positive_unbound_behavior_is_unchanged(self):
  tree=positive.tree();page=g.records_page(tree,start=self.e.job['start'],end_exclusive=self.e.job['end_exclusive']);raw=self.e.obs(tree,g.RECORDS);ref=self.e.save(self.root/'positive.json',raw)
  state={'fingerprint':'legacy-fingerprint','tab_id':5,'calls':[],'phase':'capture-complete','pages':[{**page,'observation':ref}]}
  out=self.extract(state);self.assertEqual(list(out['tokens']),['records-page:1']);self.assertNotIn('query_job_binding',state)
 def test_constructor_never_retrofits_or_rewrites_existing_legacy(self):
  for phase in ('open-date','capture-complete'):
   state={'fingerprint':q.nav.tag(self.e.job),'tab_id':5,'approved_version':q.nav.VERSION,'phase':phase,'calls':[],'pages':[],'observations':[]}
   q.nav.write_json(self.path,state);raw=self.path.read_bytes();r=self.runner();self.assertNotIn('query_job_binding',r.s);self.assertEqual(self.path.read_bytes(),raw)
 def test_resume_original_binding_conflict_and_window_change_rejected(self):
  runner=self.completed();other=self.root/'same-job-other-ref.json';other.write_bytes(self.e.jobpath.read_bytes())
  with self.assertRaisesRegex(ValueError,'original-job-binding-conflict'):q.Runner(self.e.job,5,self.path,q.nav.VERSION,self.e.invoke,job_ref={'path':str(other),'sha256':q.nav.digest(other)})
  self.e.raw['tab']['windowId']=4
  with self.assertRaisesRegex(ValueError,'original-window-conflict'):runner.observe()
 def test_main_cli_pins_exact_single_read_job_before_step(self):
  seen={}
  class Fake:
   def __init__(inner,*args,**kwargs):seen.update(args=args,kwargs=kwargs);inner.file=self.path;inner.s={'phase':'open-date'}
   def step(inner):pass
   def save(inner):q.nav.write_json(inner.file,inner.s)
  with patch.object(sys,'argv',['query','--job',str(self.e.jobpath),'--tab-id','5','--state',str(self.path),'--approved-version',q.nav.VERSION]),patch.object(q,'Runner',Fake):q.main()
  self.assertEqual(seen['kwargs']['job_ref'],self.jobref);self.assertEqual(seen['args'][0],self.e.job)
if __name__=='__main__':unittest.main()
