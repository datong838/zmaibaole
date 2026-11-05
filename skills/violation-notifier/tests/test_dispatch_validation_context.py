"""Synthetic formal dispatcher regressions; no native, messages or actual evidence."""
import copy,hashlib,importlib.util,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/daily-comment-stats/scripts')]
import dispatch_validation_context as c
import registration_validation as rv
spec=importlib.util.spec_from_file_location('formal_dispatch_context_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py');w=importlib.util.module_from_spec(spec);sys.modules[spec.name]=w;spec.loader.exec_module(w)
class ContextTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.dep=self.root/'dependency';self.dep.write_text('original')
  self.s={'mode':'development','company':'mock','groupid':'1','events':[],'batches':{'b':{'total':2,'send_jobs':{},'status':'built','records':[{'notice_id':'1'}]}}}
  self.orders=[{'part':str(n),'key':'mock-'+str(n),'target':w.TEST_GROUP,'kind':'group','scope':'test','type':'text','text_file':str(self.dep),'text_sha256':hashlib.sha256(b'original').hexdigest()} for n in range(2)]
 def fixture(self):
  m=types.ModuleType('fixed_dispatch_fixture');m.__file__=str(Path(__file__).resolve());m.__dict__.update(Path=Path,dependency=self.dep,ORDER=self.orders)
  exec('def send_orders(s,batch):\n dependency.read_bytes()\n return ORDER\n',m.__dict__);return m
 def derive(self):return c.derive(self.fixture(),self.s,'b')
 def test_real_pure_derivation_rechecks_transitive_bytes_after_sideeffects(self):
  context=self.derive();self.assertTrue(context.session.all_deps);context.check(self.s,'b');self.dep.write_text('changed')
  with self.assertRaisesRegex(ValueError,'dependency-changed'):context.check(self.s,'b')
 def test_order_source_scope_and_code_changes_reject(self):
  for kind in ('order','state','code'):
   context=self.derive();state=copy.deepcopy(self.s)
   try:
    if kind=='order':
     bad=context.orders()[0];bad['key']='different';context.check(self.s,'b',bad)
    elif kind=='state':self.s['company']='wrong';context.check(self.s,'b')
    else:
     exec('def send_orders(s,batch): return []',context.workflow.__dict__);context.check(self.s,'b')
   except ValueError:pass
   else:self.fail('mutation must reject')
   finally:self.s=state
 def test_context_owner_and_returned_orders_are_not_mutable_authority(self):
  context=self.derive();out=context.orders();out[0]['key']='mutated';self.assertNotEqual(out,context.orders())
  with self.assertRaisesRegex(ValueError,'owner-conflict'):context.check(copy.deepcopy(self.s),'b')
 def test_fresh_prefix_guard_not_cached_across_receipts(self):
  context=self.derive();calls=[]
  def guard():calls.append(1);raise ValueError('prefix-now-unknown')
  context.session.all_guards={'unknown':(guard,())}
  with self.assertRaisesRegex(ValueError,'prefix-now-unknown'):context.check(self.s,'b')
  self.assertEqual(calls,[1])
 def test_dispatch_derives_once_receipts_use_context_and_independent_receipt_still_derives(self):
  module=self.fixture();module.send_orders=self.fixture().send_orders
  # Real collector, then only substitute workflow association so receipt can consume it.
  context=c.derive(module,self.s,'b');context.workflow=w;context.graph=[w,sys.modules[c.__name__]];context.code=rv.reviewed_graph_token(context.graph,c.vs.code_signature,[])
  receipts={}
  def run(argv,**kw):
   self.assertIsNone(rv._ACTIVE.get());verb=argv[2]
   if verb=='prepare':
    key=argv[argv.index('--key')+1];order=next(o for o in self.orders if o['key']==key);path=self.root/(key+'.json');job={'key':key,'target':w.TEST_GROUP,'kind':'group','scope':'test','type':'text','text':'original'};path.write_text(json.dumps({'job':job,'fingerprint':w.fingerprint(job),'status':'complete','phase':'done','ui_confirmed':True}));receipts[key]=path;return types.SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(path)}))
   return types.SimpleNamespace(returncode=0)
  with patch.object(c,'derive',return_value=context) as derive,patch.object(w,'subprocess',types.SimpleNamespace(run=run)),patch.object(w,'send_orders',side_effect=AssertionError('must not derive receipt again')):
   # Code guard sees these test-only substitutes; capture their exact current identity.
   context.code=rv.reviewed_graph_token(context.graph,c.vs.code_signature,[])
   # Only this synthetic fixture installs fake sender/derive after collection.
   # Sign that exact test-double graph before dispatch; production is unmodified.
   context.session.token=context.session.code_token()
   w.dispatch(self.root,self.s,'b');self.assertEqual(derive.call_count,1);self.assertEqual(len(self.s['batches']['b']['send_jobs']),2)
  with patch.object(w,'send_orders',return_value=self.orders) as full:w.accept_receipt(self.root,self.s,'b','0',receipts['mock-0']);self.assertEqual(full.call_count,1)
 def test_unknown_receipt_stops_without_second_run_or_new_key(self):
  class Stub:
   def orders(_):return copy.deepcopy(self.orders)
   def check(*a):pass
   def checked_orders(*a):return {o['part']:o for o in self.orders}
  # Isolate dispatch scheduling only; unknown receipt validation remains original.
  def unknown(root,s,batch,part,path,**kw):raise ValueError('send-unknown-stop-no-resend')
  calls=[]
  def run(argv,**kw):calls.append(argv);return types.SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(self.root/'same.json')}))
  with patch.object(c,'derive',return_value=Stub()),patch.object(w,'subprocess',types.SimpleNamespace(run=run)),patch.object(w,'accept_receipt',side_effect=unknown),self.assertRaisesRegex(ValueError,'unknown'):w.dispatch(self.root,self.s,'b')
  self.assertEqual([a[2] for a in calls],['prepare','run']);self.assertEqual(len(self.s['batches']['b']['send_jobs']),1)
 def timeout_case(self,complete):
  if complete:self.orders=self.orders[:1]
  context=c.derive(self.fixture(),self.s,'b');context.workflow=w;context.graph=[w,sys.modules[c.__name__]]
  calls=[]
  def run(argv,**kw):
   self.assertIsNone(rv._ACTIVE.get());calls.append(argv);verb=argv[2]
   if verb=='prepare':
    key=argv[argv.index('--key')+1];path=self.root/(key+'.json');job={'key':key,'target':w.TEST_GROUP,'kind':'group','scope':'test','type':'text','text':'original'}
    path.write_text(json.dumps({'job':job,'fingerprint':w.fingerprint(job),'status':'complete' if complete else 'unknown','phase':'done' if complete else 'image-verify-sent','ui_confirmed':complete}))
    return types.SimpleNamespace(returncode=0,stdout=json.dumps({'job_path':str(path)}))
   raise subprocess.TimeoutExpired(argv,180)
  fake=types.SimpleNamespace(run=run,TimeoutExpired=subprocess.TimeoutExpired)
  with patch.object(c,'derive',return_value=context),patch.object(w,'subprocess',fake),patch.object(w,'send_orders',side_effect=AssertionError('receipt must not rederive')):
   context.code=rv.reviewed_graph_token(context.graph,c.vs.code_signature,[])
   # Only this synthetic fixture installs fake sender/derive after collection.
   # Sign that exact test-double graph before dispatch; production is unmodified.
   context.session.token=context.session.code_token()
   if complete:w.dispatch(self.root,self.s,'b')
   else:
    with self.assertRaisesRegex(ValueError,'send-unknown-stop-no-resend'):w.dispatch(self.root,self.s,'b')
  self.assertEqual([a[2] for a in calls],['prepare','run'])
  entry=self.s['batches']['b']['send_jobs']['0'];self.assertEqual(entry['order']['key'],'mock-0');self.assertEqual(entry['confirmed'],complete)
  self.assertEqual(set(self.s['batches']['b']['send_jobs']),{'0'})
  events=[e for e in self.s['events'] if e['type']=='send-job-run-timeout'];self.assertEqual(len(events),1);self.assertEqual(events[0]['key'],'mock-0');self.assertEqual(events[0]['job_path'],str(self.root/'mock-0.json'))
  durable=json.loads((self.root/'state.json').read_text());self.assertEqual(len([e for e in durable['events'] if e['type']=='send-job-run-timeout']),1)
 def test_timeout_same_job_complete_receipt_is_registered(self):self.timeout_case(True)
 def test_timeout_same_job_unknown_stops_without_next_order_or_rerun(self):self.timeout_case(False)
if __name__=='__main__':unittest.main()
