"""Pure fake connector; verifies durable intent and no blind retries."""
import importlib.util,json,unittest
from pathlib import Path
import test_governance_dom as fixtures
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('query_runner',here.parent/'scripts/bridge-governance-query.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('nav_fixtures',here/'test_bridge_navigation.py');nf=importlib.util.module_from_spec(spec);spec.loader.exec_module(nf)
class RunnerTests(unittest.TestCase):
 def setUp(self):
  nf.NavigationTests.setUp(self);self.path=m.g.RECORDS;self.marker=False;self.fail=False;self.state=self.root/'query.json';self.t=fixtures.tree();self.t['root']['children'] += [nf.leaf('服务商123456789','#provider'),nf.leaf('账户ID987654321','#account'),nf.leaf('我的客户经理测试经理 切换公司','#manager')]
 def request(self,c):
  self.calls.append(c)
  if c['op']=='tabs':v=[{'tabs':[{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+self.path+'?groupid=123'}]}]
  elif c['op']=='ping':v={'version':m.nav.VERSION,'safety':'DOM-only',**({'governance_query_policy':'observed-dom-20261021-v1','governance_calendar_policy':'date-item-div-v3-single'} if self.marker else {})}
  elif c['op']=='tree':v=self.t
  elif c['op']=='click':
   self.assertEqual(json.loads(self.state.read_text())['calls'][-1]['state'],'unknown')
   if self.fail:raise TimeoutError('unknown')
   v={'clicked':True}
  else:raise AssertionError(c)
  return {'ok':True,'result':v}
 def step(self):
  r=m.Runner(self.job,5,self.state,m.nav.VERSION,self.request)
  try:r.step()
  finally:r.save()
  return r
 def test_current_policy_without_query_marker_does_not_act(self):
  with self.assertRaisesRegex(ValueError,'not-yet-loaded'):self.step()
  self.assertEqual(json.loads(self.state.read_text())['calls'],[]);self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_unknown_click_intent_never_replays(self):
  self.marker=True;self.fail=True
  with self.assertRaises(TimeoutError):self.step()
  before=len(self.calls);r=self.step();self.assertEqual(len(self.calls),before);self.assertEqual(r.s['waiting_for'],'original-unknown-intent-no-replay')
 def test_confirmed_no_effect_only_reads_until_bounded_supervisor_hold(self):
  self.marker=True;self.step()
  for _ in range(5):r=self.step()
  self.assertEqual(sum(c['op']=='click' for c in self.calls),1);self.assertEqual(r.s['read_only_settling']['checks'],5);self.assertTrue(r.s['settling_exhausted']);before=len(self.calls);self.step();self.assertEqual(len(self.calls),before)
 def test_delayed_calendar_mount_uses_original_click_then_continues(self):
  self.marker=True;self.step();r=self.step();self.assertEqual(r.s['waiting_for'],'confirmed-action-pending-readonly-recheck');self.t=fixtures.with_calendar(self.t);r=self.step();self.assertEqual(r.s['phase'],'select-end');self.assertEqual(len(r.s['calls']),2);self.assertNotEqual(r.s['calls'][0]['command']['locator'],r.s['calls'][1]['command']['locator']);self.assertEqual(r.s['settled_actions'][0]['checks'],2)
 def test_transient_month_waits_for_exact_delta_without_reclick(self):
  self.marker=True;self.t=fixtures.with_calendar(self.t);r=m.Runner(self.job,5,self.state,m.nav.VERSION,self.request);r.observe();r.query_policy_ready=True;r.act({'op':'click','locator':{'by':'selector','value':'#mock-month'},'kind':'filter'},'select-start',{'month_delta':-1});r=self.step();self.assertEqual(r.s['waiting_for'],'confirmed-action-pending-readonly-recheck');self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
  for node in m.g.nodes(self.t):
   if 'governance_merchant-date-title' in m.g.cls(node):node['name']='2026年'+str(int(node['name'].split('年')[1][:-1])-1)+'月'
  # The exact month delta settles; a subsequent legitimate plan action may run.
  r=self.step();self.assertEqual(r.s['settled_actions'][0]['reason'],'governance-month-did-not-advance-exactly-once');self.assertFalse(r.s.get('settling_exhausted',False));self.assertEqual(len(r.s['calls']),2)
 def test_pending_next_page_reads_only_then_records_actual_page_two(self):
  self.marker=True;ns=m.g.nodes(self.t);next(n for n in ns if 'governance_merchant-tab-bar-item-active' in m.g.cls(n))['name']='全部2';next(n for n in ns if n['tag']=='li' and 'governance_merchant-pager-item-disabled' in m.g.cls(n))['attributes']['class']='governance_merchant-pager-item'
  r=m.Runner(self.job,5,self.state,m.nav.VERSION,self.request);r.observe();r.query_policy_ready=True;page=m.g.records_page(self.t,start=self.job['start'],end_exclusive=self.job['end_exclusive']);r.s['pages']=[page];r.act(page['next']['command'],'next-page');r=self.step();self.assertEqual(r.s['waiting_for'],'confirmed-action-pending-readonly-recheck');self.assertEqual(len(r.s['calls']),1)
  ns=m.g.nodes(self.t)
  for node in ns:
   if node.get('name')=='一般 模拟原因 ID: TEST123':node['name']='一般 模拟原因 ID: TEST124'
   if node.get('tag')=='li' and 'governance_merchant-pager-item-checked' in m.g.cls(node):node['name']='2'
   if node.get('tag')=='li' and any('governance_merchant-icon-right' in m.g.cls(c) for c in node.get('children',[])):node['attributes']['class']='governance_merchant-pager-item governance_merchant-pager-item-disabled'
  r=self.step();self.assertEqual(r.s['phase'],'capture-complete');self.assertEqual([x['notice_id'] for x in r.s['rows']],['TEST123','TEST124']);self.assertEqual(len(r.s['calls']),1)
 def test_changed_pinned_plan_stops_before_observation(self):
  self.pp.write_text('{}')
  with self.assertRaises(ValueError):self.step()
  self.assertEqual(self.calls,[])
 def test_detail_exact_current_notice_once_then_raw_tree_hold(self):
  self.marker=True;r=m.DetailProbe(self.job,5,self.state,m.nav.VERSION,'TEST123',self.request);r.step();r.save();self.assertEqual(r.s['phase'],'observe-detail')
  r=m.DetailProbe(self.job,5,self.state,m.nav.VERSION,'TEST123',self.request);r.step();r.save();self.assertEqual(r.s['phase'],'profile-required');self.assertFalse(r.s['advice_extracted']);before=len(self.calls);r.step();self.assertEqual(len(self.calls),before);self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
  with self.assertRaisesRegex(ValueError,'notice-binding'):m.DetailProbe(self.job,5,self.state,m.nav.VERSION,'OTHER',self.request)
 def test_unlisted_detail_cannot_click(self):
  self.marker=True;r=m.DetailProbe(self.job,5,self.state,m.nav.VERSION,'OTHER',self.request)
  with self.assertRaisesRegex(ValueError,'not-on-current-page'):r.step()
  self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_first_detail_returns_to_bound_original_page_once_after_all_pages(self):
  import copy
  self.marker=True
  for node in m.g.nodes(self.t):
   if 'governance_merchant-tab-bar-item-active' in m.g.cls(node):node['name']='全部2'
   if node.get('tag')=='li' and 'governance_merchant-pager-item-disabled' in m.g.cls(node):node['attributes']['class']='governance_merchant-pager-item'
  p1=m.g.records_page(self.t,start=self.job['start'],end_exclusive=self.job['end_exclusive']);first=copy.deepcopy(self.t)
  for node in m.g.nodes(self.t):
   if node.get('name')=='一般 模拟原因 ID: TEST123':node['name']='一般 模拟原因 ID: TEST124'
   if node.get('tag')=='li' and 'governance_merchant-pager-item-checked' in m.g.cls(node):node['name']='2'
   if node.get('tag')=='li' and any('governance_merchant-icon-right' in m.g.cls(c) for c in node.get('children',[])):node['attributes']['class']='governance_merchant-pager-item governance_merchant-pager-item-disabled'
  pager=m.g.classnodes(self.t['root'],'governance_merchant-pager')[0];pager['children'].append(fixtures.n('1','li','governance_merchant-pager-item'));p2=m.g.records_page(self.t,start=self.job['start'],end_exclusive=self.job['end_exclusive'])
  query={'phase':'capture-complete','fingerprint':m.nav.tag(self.job),'tab_id':5,'approved_version':m.nav.VERSION,'pages':[p1,p2],'rows':m.g.complete_pages([p1,p2])};q=self.root/'captured-query.json';m.nav.write_json(q,query);ref={'path':str(q),'sha256':m.nav.digest(q)}
  def run():
   r=m.DetailProbe(self.job,5,self.state,m.nav.VERSION,'TEST123',self.request,query_ref=ref);r.step();r.save();return r
  r=run();self.assertEqual(r.s['phase'],'goto-detail-page');self.assertEqual(len(r.s['calls']),1);r=run();self.assertEqual(r.s['waiting_for'],'confirmed-action-pending-readonly-recheck');self.assertEqual(len(r.s['calls']),1);self.t=first;r=run();self.assertEqual(r.s['phase'],'observe-detail');self.assertEqual(len(r.s['calls']),2);self.assertEqual(r.s['calls'][0]['postcondition'],{'expected_page':1})
if __name__=='__main__':unittest.main()
