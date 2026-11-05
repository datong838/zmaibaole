"""Portable synthetic zero DOM/query replay. No live evidence or browser."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import governance_dom as g
from zero_source_fixtures import Evidence,q
def read(p):return json.loads(p.read_text())
class Zero(unittest.TestCase):
 def setUp(self):
  self.fixture_temp=tempfile.TemporaryDirectory();self.addCleanup(self.fixture_temp.cleanup);self.e=Evidence(self,Path(self.fixture_temp.name));self.original,self.raw=self.e.original_records();self.last=read(self.original)['last_observation'];self.job=self.e.job
 def page(self,t=None):return g.records_page(t or self.raw['tree'],start='2026-10-16',end_exclusive='2026-10-21')
 def test_synthetic_explicit_empty_and_logical_not_observed_pager(self):
  p=self.page();self.assertEqual(g.complete_pages([p]),[]);self.assertFalse(p['empty_result']['pagination_observed']);self.assertEqual(p['total'],0)
 def test_scope_structure_positive_mixed_and_loading_negatives(self):
  for kind in ('date','all','unread','header','empty','row','multi','pager','busy','management'):
   t=copy.deepcopy(self.raw['tree']);ns=g.nodes(t)
   if kind=='date':g.date_input(t)['attributes']['value']='2026/10/16 ～ 2026/10/21'
   if kind=='all':next(n for n in ns if n.get('tag')=='div' and n.get('name')=='全部')['attributes']['class']='governance_merchant-tab-bar-item'
   if kind=='unread':next(n for n in ns if 'governance_merchant-checkbox-icon-uncheck' in g.cls(n))['attributes']['class']='governance_merchant-checkbox-icon-check'
   if kind=='header':next(n for n in ns if n.get('tag')=='th')['name']='错误'
   if kind=='empty':next(n for n in ns if n.get('tag')=='p' and g.text(n)=='暂无数据')['name']='加载中'
   if kind=='row':next(n for n in ns if n.get('tag')=='tbody')['children']=[{'tag':'tr','children':[{'tag':'td','children':[]}]}]
   if kind=='multi':g.root(t)['children'].append(copy.deepcopy(next(n for n in ns if n.get('tag')=='table')))
   if kind=='pager':g.root(t)['children'].append({'tag':'div','attributes':{'class':'governance_merchant-pager'},'children':[]})
   if kind=='busy':g.root(t)['attributes']['aria-busy']='true'
   if kind=='management':next(n for n in ns if n.get('tag')=='div' and n.get('name')=='违规记录管理')['attributes']['class']='governance_merchant-tab-bar-item'
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.page(t)
 def runner(self,folder,mutate=None):
  state=read(self.original)
  if mutate:mutate(state)
  path=folder/'state.json';path.write_text(json.dumps(state,ensure_ascii=False));events=[]
  def invoke(cmd):
   events.append(cmd);self.assertIn(cmd['op'],('tabs','ping','tree'))
   if cmd['op']=='tabs':result=[{'tabs':[self.raw['tab']]}]
   elif cmd['op']=='tree':result=self.raw['tree']
   else:result={'version':q.nav.VERSION,'safety':'DOM-only'}
   return {'ok':True,'result':result}
  return q.Runner(self.job,state['tab_id'],path,q.nav.VERSION,invoke),events
 def test_original_confirmed_query_readonly_reconcile_no_reclick_calls_unchanged(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,events=self.runner(Path(tmp));before=copy.deepcopy(r.s['calls']);digest=q.nav.digest(r.file);r.reconcile_records_zero(digest,self.last['sha256']);self.assertEqual(r.s['phase'],'capture-complete');self.assertEqual(r.s['calls'],before);self.assertEqual(r.s['rows'],[]);self.assertFalse(r.s['zero_verified']);self.assertTrue(r.s['records_zero_verified']);self.assertEqual(q.nav.digest(Path(r.s['records_zero_reconciliation']['original_journal']['path'])),digest);self.assertNotIn('click',[c['op'] for c in events])
   count=len(events);r.reconcile_records_zero(digest,self.last['sha256']);self.assertEqual(len(events),count)
 def test_interrupted_first_fresh_read_resumes_original_parameters_without_input(self):
  with tempfile.TemporaryDirectory() as tmp:
   r,events=self.runner(Path(tmp));digest=q.nav.digest(r.file);original=copy.deepcopy(r.s['calls']);normal=r.invoke
   def fail(cmd):
    self.assertEqual(cmd['op'],'tabs');events.append(cmd);raise TimeoutError('synthetic readonly timeout')
   r.invoke=fail
   with self.assertRaises(TimeoutError):r.reconcile_records_zero(digest,self.last['sha256'])
   pending=read(r.file);self.assertEqual(pending['records_zero_reconciliation']['state'],'pending-readonly');self.assertNotEqual(q.nav.digest(r.file),digest)
   resumed=q.Runner(self.job,r.tab,r.file,q.nav.VERSION,normal);resumed.reconcile_records_zero(digest,self.last['sha256']);self.assertEqual(resumed.s['phase'],'capture-complete');self.assertEqual(resumed.s['calls'],original);self.assertNotIn('click',[c['op'] for c in events])
   calls=len(events);resumed.reconcile_records_zero(digest,self.last['sha256']);self.assertEqual(len(events),calls)
 def test_wrong_sha_unknown_and_wrong_saved_reply_zero_requests(self):
  for mode in ('sha','unknown','reply'):
   with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
    def mutate(s):
     if mode=='unknown':s['calls'][-1]['state']='unknown'
     if mode=='reply':s['calls'][-1]['result']['clicked']['name']='重置'
    r,events=self.runner(Path(tmp),mutate)
    with self.assertRaises(ValueError):r.reconcile_records_zero('0'*64 if mode=='sha' else q.nav.digest(r.file),self.last['sha256'])
    self.assertEqual(events,[])
if __name__=='__main__':unittest.main()
