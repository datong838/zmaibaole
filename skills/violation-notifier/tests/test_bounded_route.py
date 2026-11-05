"""Candidate only: synthetic confirmed before/reply and read-only route races."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fixture=load('bounded_nav_fixture',ROOT/'skills/violation-notifier/tests/test_bridge_navigation.py');nav=load('bounded_nav_candidate',HERE.parent/'scripts/bridge-navigation.py')
discovery_fixture=load('bounded_probe_fixture',ROOT/'skills/violation-notifier/tests/test_bridge_profile_discovery.py');discovery=load('bounded_probe_candidate',HERE.parent/'scripts/bridge-profile-discovery.py')
class BoundedRoutes(unittest.TestCase):
 def setUp(self):
  self.f=fixture.NavigationTests('test_menu_then_center_then_hold_saves_full_raw_tree');self.f.setUp();self.addCleanup(self.f.doCleanups);self.f.path='/p/home';self.f.has_menu=True
  self.prior=self.f.root/'003-openCenter-before.json';obs={'source':'local-dom-bridge','tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com/p/home?groupid=123'},'tree':self.f.tree(),'navigation_fingerprint':nav.tag(self.f.job)};nav.write_json(self.prior,obs);r={'path':str(self.prior),'sha256':nav.digest(self.prior)}
  self.n=nav.Navigator(self.f.job,5,self.f.state,self.f.bridge);self.n.s.update(phase='observeCenter',revision=4,identity_verified_at='synthetic',last_tree=r,last_error='previous-race-retained',calls=[{'key':'3:openCenter','state':'confirmed','before':r,'command':{'op':'click','tabId':5,'kind':'navigation','locator':{'by':'selector','value':'#center'}},'result':{'clicked':{'name':'违规中心','selector':'#center'}}}]);self.n.save()
 def racing(self,failures=1,invalid=None):
  calls=[];trees=0
  def invoke(c):
   nonlocal trees
   calls.append(c)
   if c['op']=='tabs':
    old=trees<failures
    path='/p/home' if old else nav.CENTER;window=9 if invalid=='window' else 3;gid='999' if invalid=='group' else '123'
    return {'ok':True,'result':[{'tabs':[{'tabId':5,'windowId':window,'allowed':True,'url':'https://life.douyin.com'+path+'?groupid='+gid}]}]}
   if c['op']=='ping':return {'ok':True,'result':{'version':nav.VERSION,'safety':'DOM-only'}}
   if c['op']=='tree':
    trees+=1;self.f.path=nav.CENTER;t=self.f.tree()
    if invalid=='path':t['url']='https://life.douyin.com/p/other'
    if invalid=='identity':t['root']['children'][2]['name']='我的客户经理错误 切换公司'
    if invalid=='risk':t['root']['children'].append(fixture.leaf('风险验证','#risk'))
    return {'ok':True,'result':t}
   raise AssertionError('No UI input allowed')
  return invoke,calls
 def test_confirmed_center_race_retries_only_reads_and_keeps_audit_and_error(self):
  self.n.invoke,calls=self.racing();self.n.tick();self.assertEqual(self.n.s['phase'],'profileRequired');self.assertEqual(len(self.n.s['readonly_route_recovery']),1);self.assertEqual(self.n.s['last_error'],'previous-race-retained');self.assertEqual(sum(c['op']=='tree' for c in calls),2);self.assertTrue(all(c['op'] in ('tabs','ping','tree') for c in calls))
 def test_two_retry_limit_then_original_error_and_phase_preserved(self):
  self.n.invoke,calls=self.racing(failures=99)
  with self.assertRaisesRegex(ValueError,'navigation-tree-path-conflict'):self.n.tick()
  self.assertEqual(sum(c['op']=='tree' for c in calls),3);self.assertEqual(len(self.n.s['readonly_route_recovery']),3);self.assertEqual(self.n.s['phase'],'observeCenter')
  count=len(calls)
  with self.assertRaisesRegex(ValueError,'settling-exhausted'):self.n.tick()
  self.assertEqual(len(calls),count)
 def test_unknown_or_unconfirmed_or_changed_before_never_enters_retry(self):
  for kind in ('unknown','unconfirmed','bad-before'):
   original=copy.deepcopy(self.n.s);self.n.invoke,calls=self.racing()
   if kind=='unknown':self.n.s['calls'][0]['state']='unknown'
   elif kind=='unconfirmed':self.n.s['calls'][0]['state']='rejected'
   else:self.n.s['calls'][0]['before']['sha256']='0'*64
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.n.tick()
   self.assertLessEqual(sum(c['op']=='tree' for c in calls),1);self.n.s=original
 def test_scope_route_risk_or_identity_errors_not_retried(self):
  for kind in ('group','window','path','identity','risk'):
   self.n.invoke,calls=self.racing(invalid=kind)
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.n.tick()
   self.assertLessEqual(sum(c['op']=='tree' for c in calls),1)
 def test_interrupted_budget_reuses_original_prefix_and_window(self):
  invoke,calls=self.racing(failures=99);reads=0
  def interrupt(c):
   nonlocal reads
   if c['op']=='tabs':
    reads+=1
    if reads==3:raise RuntimeError('external interrupted next sample')
   return invoke(c)
  self.n.invoke=interrupt
  with self.assertRaisesRegex(RuntimeError,'interrupted'):self.n.tick()
  self.assertEqual(len(self.n.s['readonly_route_recovery']),1)
  resumed=nav.Navigator(self.f.job,5,self.f.state);resumed.invoke,calls=self.racing(failures=0,invalid='window')
  with self.assertRaisesRegex(ValueError,'scope-conflict'):resumed.tick()
  self.assertEqual(sum(c['op']=='tree' for c in calls),1)
 def test_confirmed_records_probe_retries_readonly_to_profile_hold(self):
  f=discovery_fixture.DiscoveryTests('test_actual_structure_required');f.setUp();self.addCleanup(f.doCleanups);f.version=discovery.POLICY_VERSION
  p=discovery.Probe(f.job,5,f.state,'records',f.bridge);p.step();self.assertEqual(p.s['phase'],'observe-result')
  # Upgrade only this synthetic old fake's bool reply into an explicit saved node.
  p.s['calls'][-1]['result']={'clicked':{'name':'违规记录','selector':p.s['calls'][-1]['command']['locator']['value']}};p.save();trees=0;calls=[]
  def invoke(c):
   nonlocal trees
   calls.append(c)
   if c['op']=='tree':trees+=1;t=f.tree();t['url']='https://life.douyin.com/p/governance/violation_list';return {'ok':True,'result':t}
   if c['op']=='tabs':
    path=discovery.nav.CENTER if trees==0 else '/p/governance/violation_list';return {'ok':True,'result':[{'tabs':[{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+path+'?groupid=123'}]}]}
   return f.bridge(c)
  p.invoke=invoke;p.step();self.assertEqual(p.s['phase'],'profile-required');self.assertEqual(trees,2);self.assertEqual(len(p.s['readonly_route_recovery']),1);self.assertFalse(any(c['op'] in ('click','hover') for c in calls))
 def test_compact_records_entry_retains_marker_and_bounded_route(self):
  f=discovery_fixture.DiscoveryTests('test_actual_structure_required');f.setUp();self.addCleanup(f.doCleanups);original=f.tree
  def compact():
   t=original();ns=list(nav.nodes(t));tools=next(n for n in ns if n.get('attributes',{}).get('class')=='todoSummary-xpJGcr');tools['attributes']['class']='todoSummary-xpJGcr compact-Gcf1ET boardSuccess-tXR2Eq';tools['name']='违规记录 新增21 预警记录 8'
   item=tools['children'][0];item['attributes']['class']='compactItem-TpyZAq';label=item['children'][0];label['attributes']['class']='compactLabel-aFEjMF';tools['children']=[discovery_fixture.n(cls='compactList-kThnsC',children=[item])];return t
  f.tree=compact
  def bridge(c):
   if c['op']=='ping':return {'ok':True,'result':{'version':discovery.POLICY_VERSION,'safety':'DOM-only','content_build':'governance-center-analysis-preflight-spacer-v2','governance_compact_records_policy':'observed-compact-record-entry-v1'}}
   return f.bridge(c)
  p=discovery.Probe(f.job,5,f.state,'records',bridge);p.step();self.assertEqual(p.s['phase'],'observe-result');entry=p.s['calls'][-1];entry['result']={'clicked':{'name':'违规记录','selector':entry['command']['locator']['value']}};p.save();trees=0;calls=[]
  def route(c):
   nonlocal trees
   calls.append(c)
   if c['op']=='tree':trees+=1;t=compact();t['url']='https://life.douyin.com/p/governance/violation_list';return {'ok':True,'result':t}
   if c['op']=='tabs':
    path=nav.CENTER if trees==0 else '/p/governance/violation_list';return {'ok':True,'result':[{'tabs':[{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+path+'?groupid=123'}]}]}
   return bridge(c)
  p.invoke=route;p.step();self.assertEqual(p.s['phase'],'profile-required');self.assertEqual(trees,2);self.assertFalse(any(c['op'] in ('click','hover') for c in calls))
if __name__=='__main__':unittest.main()
