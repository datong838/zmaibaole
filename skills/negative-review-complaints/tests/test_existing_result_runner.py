import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import existing_result_runner as r
import test_result_observation as fixtures
class RunnerTests(unittest.TestCase):
 def setUp(self):
  memory_patch=patch('case_memory.auto_import',return_value={'appended':False,'test_isolated':True});memory_patch.start();self.addCleanup(memory_patch.stop)
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.fx=fixtures.ResultObservationTests();self.fx.setUp();self.fx.job['identity']={'provider':'服务商123456789'};self.open=False;self.calls=[];self.records=[];self.fail_open=False;self.fail_close=False
  self.row={**self.fx.review,'dom_selector':'#card','stars':3,'date':'2026-10-19','action':'查看投诉结果'};self.key='123:'+self.row['review_id'];self.tab=self.fx.page['tab'];self.action=fixtures.n('查看投诉结果','button-vhqEd7 isHighlight-DoxxP4');self.action.update(selector='#action',disabled=False)
  self.normal=fixtures.n(children=[dict(fixtures.n(children=[dict(fixtures.n(self.row[k],cl),selector='#'+k) for k,cl in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf'),('text','text-Hl9jZe')]]+[self.action]),selector='#card')]);self.normal['children'].append(dict(fixtures.n('服务商123456789','src-components-HeaderV3-components-Profile-index-module__title--fixture'),selector='#provider'));self.drawer=copy.deepcopy(self.fx.drawer);self.close=fixtures.n('','byted-drawer-close-icon',tag='span');self.close.update(selector='#close',disabled=False);self.drawer['children'].append(self.close)
  self.v={'job':self.fx.job,'profile':{},'page':self.fx.page};self.order={'card_selector':'#card','original_action':'查看投诉结果'};self.source=self.root/'source.json';self.source.write_text('{}');self.m={'kind':'existing-result-inspection-manifest-v1','root':str(self.root/'ledger'),'review_key':self.key,'inputs':{'source':r.ref(self.source)}}
  self.patches=[patch.object(r,'manifest_inputs',side_effect=lambda m,**kw:(self.v,self.order,self.row)),patch.object(r.normal,'navigation_probe',return_value={}),patch.object(r.normal,'public_identity'),patch.object(r,'LEGACY',self.root/'legacy')]
  for p in self.patches:p.start();self.addCleanup(p.stop)
  (self.root/'legacy').mkdir()
 def request(self,c):
  self.calls.append(c)
  if c['op']=='activate':return {'ok':True,'result':{}}
  if c['op']=='tabs':return {'ok':True,'result':[{'tabs':[self.tab]}]}
  if c['op']=='tree':return {'ok':True,'result':dict(self.fx.page['tree'],root=fixtures.n(children=[copy.deepcopy(self.drawer)])) if self.open else dict(self.fx.page['tree'],root=copy.deepcopy(self.normal))}
  if c['op']=='click':
   close=c['locator']['value']=='#close';self.open=not close
   if (close and self.fail_close) or (not close and self.fail_open):raise RuntimeError('reply-lost')
   return {'ok':True,'result':{'kind':'complaint-read','clicked':copy.deepcopy(self.close if close else self.action)}}
  raise AssertionError(c)
 def tick(self,m=None):return r.tick(m or self.m,self.request,lambda root,key,path:self.records.append((key,str(path))))
 def done(self):
  for _ in range(10):
   out=self.tick()
   if out['state']=='complete':return out
  self.fail('not complete')
 def test_fixed_single_open_record_close_and_completed_repeat_is_offline(self):
  out=self.done();clicks=[c for c in self.calls if c['op']=='click'];self.assertEqual([c['locator']['value'] for c in clicks],['#action','#close']);self.assertEqual(len(self.records),1);before=len(self.calls);self.assertEqual(self.tick()['state'],'complete');self.assertEqual(len(self.calls),before);self.assertTrue(Path(out['operation']).exists())
 def test_unknown_open_only_reconciles_exact_drawer_no_reclick(self):
  self.tick();self.fail_open=True
  with self.assertRaisesRegex(RuntimeError,'reply-lost'):self.tick()
  out=self.done();self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#action','#close']);s=json.loads(Path(out['operation']).read_text());self.assertNotIn('open_reply',s);self.assertEqual(s['open_reconciliation']['method'],'exact-public-result-drawer')
 def test_unknown_close_only_reads_absent_drawer_and_never_reclicks(self):
  for _ in range(4):self.tick()
  self.fail_close=True
  with self.assertRaisesRegex(RuntimeError,'reply-lost'):self.tick()
  out=self.tick();self.assertEqual(out['state'],'complete');self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#action','#close'])
 def test_unfinished_prior_source_blocks_new_source_no_ui(self):
  self.tick();new=copy.deepcopy(self.m);new['inputs']['source']['sha256']='f'*64;before=len(self.calls)
  with self.assertRaisesRegex(ValueError,'prior-source-operation-unfinished'):self.tick(new)
  self.assertEqual(len(self.calls),before)
 def test_explicit_prior_complete_allows_new_source(self):
  self.done();new=copy.deepcopy(self.m);new['inputs']['source']['sha256']='f'*64;self.assertEqual(self.tick(new)['state'],'open-ready')
 def test_unreferenced_legacy_unknown_blocks_any_new_operation(self):
  legacy=self.root/'legacy/known-result-operation.json';legacy.write_text(json.dumps({'state':'opened','review_key':self.key}))
  with self.assertRaisesRegex(ValueError,'legacy-operation'):self.tick()
  self.assertEqual(self.calls,[])
 def test_wrong_current_review_refuses_before_open(self):
  self.normal['children'][0]['children'][0]['name']='wrong'
  with self.assertRaisesRegex(ValueError,'review-changed:store'):self.tick()
  self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_closed_hover_card_uses_exact_provider_and_honestly_marks_no_full_identity_recheck(self):
  out=self.tick();state=json.loads(Path(out['operation']).read_text());self.assertFalse(state['runtime_full_identity_rechecked']);self.assertEqual(state['runtime_identity_basis'],'visible-provider-trigger-and-pinned-source-full-identity');r.normal.public_identity.assert_not_called()
 def test_present_but_invalid_usercard_never_falls_back_to_provider_only(self):
  self.normal['children'].append(fixtures.n('wrong','src-components-HeaderV3-components-UserCard-index-module__outer--fixture'));r.normal.public_identity.side_effect=ValueError('identity-mismatch')
  with self.assertRaisesRegex(ValueError,'identity-mismatch'):self.tick()
  self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_crash_after_page_output_preserves_it_and_next_read_uses_unique_name(self):
  original=r.immutable_write;files=[]
  def crash(path,value):original(path,value);files.append(Path(path));raise KeyboardInterrupt('simulated power loss')
  with patch.object(r,'immutable_write',side_effect=crash),self.assertRaises(KeyboardInterrupt):self.tick()
  old=files[0].read_bytes();out=self.tick();self.assertEqual(files[0].read_bytes(),old);self.assertEqual(len(list(Path(out['operation']).parent.glob('*-normal-before.json'))),2)
 def test_crash_after_result_input_write_reuses_verified_original_drawer_without_reopen(self):
  self.tick();self.tick();original=r.workflow.atomic
  def crash(path,value):
   if Path(path).name=='operation.json' and value.get('state')=='record-ready':raise KeyboardInterrupt('simulated power loss')
   return original(path,value)
  with patch.object(r.workflow,'atomic',side_effect=crash),self.assertRaises(KeyboardInterrupt):self.tick()
  folder=next((Path(self.m['root'])/'existing-result-operations').glob('*'))/self.m['inputs']['source']['sha256'];old=(folder/'result-input.json').read_bytes();out=self.done();self.assertEqual((folder/'result-input.json').read_bytes(),old);self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#action','#close']);self.assertEqual(out['state'],'complete')
 def test_complete_file_before_active_index_commit_is_fully_revalidated_for_next_source(self):
  for _ in range(5):self.tick()
  original=r.workflow.atomic
  def crash(path,value):
   if Path(path).name=='active.json' and r.document(value['operation']).get('state')=='complete':raise KeyboardInterrupt('simulated power loss')
   return original(path,value)
  with patch.object(r.workflow,'atomic',side_effect=crash),self.assertRaises(KeyboardInterrupt):self.tick()
  new=copy.deepcopy(self.m);new['inputs']['source']['sha256']='f'*64;out=self.tick(new);index=json.loads((Path(out['operation']).parent.parent/'active.json').read_text());self.assertEqual(len(index['completed_pointer_recoveries']),1);self.assertEqual(out['state'],'open-ready');self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#action','#close'])
 def test_cli_run_uses_same_manifest_and_stops_on_complete(self):
  import contextlib,io
  p=self.root/'manifest.json';p.write_text(json.dumps(self.m))
  with patch.object(sys,'argv',['existing_result_runner.py','run','--manifest',str(p),'--steps','10']),patch.object(r,'tick',return_value={'state':'complete','ok':True}) as tick,contextlib.redirect_stdout(io.StringIO()):self.assertEqual(r.main(),0)
  tick.assert_called_once_with(self.m)
if __name__=='__main__':unittest.main()

class ActualCompletedOperationTests(unittest.TestCase):
 def test_original_completed_shanghai_operation_is_adopted_readonly_with_all_pinned_pages(self):
  b=r.PROJECT/'work/live-acceptance/complaints/frozen-20261016-20261020/02-shanghai';live=r.LEGACY;old=live/'shanghai-jiu-result-operation.json'
  if not old.exists():self.skipTest('local real completed evidence unavailable')
  job=json.loads((b/'navigation-job.json').read_text());op=json.loads(old.read_text());orders=b/'existing-result-orders.json'
  before=live/'shanghai-jiu-normal-before.json';drawer=live/'shanghai-jiu-drawer-read-1.json';after=live/'shanghai-jiu-normal-after-1.json'
  # The original v1 drawer read preceded v2 parser adoption. Find the exact
  # originally recorded drawer bytes through its result DOM hash, never guess.
  matched=[]
  for p in live.glob('shanghai-jiu*json'):
   value=json.loads(p.read_text())
   if isinstance(value,dict) and 'tree' in value and r.normal.authority.data_hash(value['tree'])==op['result']['result_dom_sha256']:matched.append(p)
  if len(matched)!=1:self.skipTest('exact original result drawer evidence unavailable')
  drawer=matched[0]
  if not before.exists() or not after.exists():self.skipTest('original complete before/after evidence unavailable')
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);source=json.loads((b/'authoritative-normal-capture.json').read_text());key=op['review_key'];r.workflow.atomic(root/'state.json',{'version':1,'mode':'draft-only','company':job['company'],'groupid':job['groupid'],'browser_backend':'local-dom-bridge','tasks':{key:{'latest_snapshot':{'sha256':r.workflow.digest(b/'authoritative-normal-capture.json')}}}})
   m=r.prepare(root,{k:p for k,p in [('job',b/'navigation-job.json'),('source',b/'authoritative-normal-capture.json'),('profile',b/'normal-profile.json'),('envelope',b/'normal-envelope.json'),('page',b/'normal-page.json'),('orders',orders)]},key,root/'manifest.json',old,{'normal_before':before,'drawer':drawer,'normal_after':after})
   original=old.read_bytes();out=r.tick(m,lambda c:self.fail('completed adoption must make no browser call'),lambda *a:self.fail('completed adoption must not rewrite result'));self.assertEqual(out['state'],'complete');self.assertEqual(old.read_bytes(),original)
   self.assertEqual(r.tick(m,lambda c:self.fail('complete repeat must remain offline'))['state'],'complete')
