"""Portable HomeV3 structure; synthetic identities/switch/card, never real UI."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
spec=importlib.util.spec_from_file_location('formal_home_switch_tests',ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class HomeContext(unittest.TestCase):
 def setUp(self):
  # Portable reduced HomeV3 shape from the observed queryless-home case.
  # All identities, original switch calls, later trigger/card and transport are
  # SYNTHETIC. This fixture never asserts that a real account was verified.
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  old={'provider':'服务商123456789','account_id':'111111111','manager':'测试甲'}
  target={'provider':'服务商123456789','account_id':'222222222','manager':'测试乙'}
  self.job={'action':'return-company','backend':'local-dom-bridge','navigation_only':True,'work_order_id':'synthetic-home-switch-order','company':'合成目标公司','groupid':'222','workflow_path':str(self.root/'workflow.json'),'identity_contract':'merchant-v2','provider_baseline':target['provider'],'identity_baseline':target,'known_company_identities':{'111':old,'222':target}}
  trigger={'attributes':{'class':'src-components-HeaderV3-components-Profile-index-module__title--fixture'},'role':'generic','tag':'div','name':old['provider'],'selector':'#synthetic-provider-trigger','children':[]}
  def click(phase,kind,name,selector):
   return {'phase':phase,'key':'synthetic-'+phase,'state':'confirmed','command':{'op':'click','tabId':5,'kind':kind,'locator':{'by':'selector','value':selector}},'result':{'clicked':{'name':name,'selector':selector}}}
  self.state={'version':1,'backend':'local-dom-bridge','work_order_id':self.job['work_order_id'],'fingerprint':b.fingerprint(self.job),'company':self.job['company'],'groupid':'222','date_range':{},'tab_id':5,'state':'running','phase':'verifySwitch','initial_groupid':'111','entry_groupid':'111','entry_identity':old,'identity_contract':'merchant-v2','provider_baseline':target['provider'],'checkpoints':[],'revision':6,'calls':[{'phase':'account','key':'synthetic-focus','state':'confirmed','command':{'op':'activate','tabId':5},'result':{}},{'phase':'account','key':'synthetic-hover','state':'confirmed','command':{'op':'hover','tabId':5,'kind':'navigation'},'result':{'hovered':trigger}},click('chooseCompany','company',self.job['company'],'#synthetic-company'),click('confirmSwitch','company-confirm','确认','#synthetic-confirm')]}
  company={'attributes':{'class':'src-pages-HomeV3-components-DataOverviewAndAccountInfo-AccountInfo-AccountInfo-module__companyName--fixture'},'role':'generic','name':self.job['company'],'tag':'span','selector':'#core-account-info > div > span','children':[]}
  self.tree={'url':'https://life.douyin.com/p/home','truncated':False,'root':{'tag':'body','selector':'body','name':'合成首页','attributes':{},'children':[company]}}
  self.original_tree=copy.deepcopy(self.tree);self.url=self.tree['url'];self.window=3;self.requests=[];self.tabs_count=0;self.race=False;self.card=False
 def invoke(self,c):
  self.requests.append(copy.deepcopy(c))
  if c['op']=='tabs':
   self.tabs_count+=1;url=self.url
   if self.race and self.tabs_count==1:url='https://life.douyin.com/p/governance/violation_list?groupid='+self.state['initial_groupid']
   return {'ok':True,'result':[{'windowId':self.window,'focused':True,'tabs':[{'tabId':self.state['tab_id'],'windowId':self.window,'active':True,'allowed':True,'url':url}]}]}
  if c['op']=='ping':return {'ok':True,'result':{'version':b.VERSION,'safety':'DOM-only'}}
  if c['op']=='tree':return {'ok':True,'result':copy.deepcopy(self.tree)}
  if c['op']=='hover':self.add_card();return {'ok':True,'result':{'hovered':True}}
  raise AssertionError('No confirm/click/input is allowed: '+str(c))
 def add_card(self,identity=None):
  i=identity or self.job['identity_baseline'];self.tree['root']['children'].append({'attributes':{'class':'src-components-HeaderV3-components-UserCard-index-module__outer--fixture'},'role':'generic','tag':'div','selector':'#verified-fixture-card','name':i['provider']+' 账户ID '+i['account_id']+' 我的客户经理 '+i['manager']+' 退出登录','children':[]})
 def workflow(self):
  Path(self.job['workflow_path']).write_text(json.dumps(self.state));return b.Workflow(self.job,self.state['tab_id'],self.invoke)
 def test_reduced_home_shape_requires_synthetic_full_card_without_reconfirm_or_fake_url_gid(self):
  w=self.workflow();w.tick();self.assertEqual(w.s['phase'],'accountAfterSwitch');self.assertIsNone(w.s.get('identity'));w.tick();self.assertEqual(w.s['waiting_for'],'post-switch-home-account-trigger');self.assertFalse(any(c['op']=='hover' for c in self.requests));self.tree['root']['children'].append(copy.deepcopy(self.state['calls'][1]['result']['hovered']));w.tick();self.assertEqual(w.s['phase'],'identityAfterSwitch');w.tick();self.assertEqual(w.s['state'],'complete');self.assertEqual(w.s['result']['groupid'],self.job['groupid']);self.assertFalse(w.s['post_switch_scope_evidence']['url_groupid_observed']);self.assertTrue(w.s['post_switch_scope_evidence']['full_identity_rechecked']);self.assertFalse(any(c['op']=='click' for c in self.requests))
 def test_old_tabs_to_home_race_is_bounded_to_original_window_switch_phase(self):
  self.race=True;w=self.workflow();w.tick();self.assertEqual(w.s['phase'],'accountAfterSwitch');self.assertIsNone(w.s.get('identity'))
 def test_wrong_host_path_query_fragment_and_other_phase_are_rejected(self):
  for url in ('https://evil.example/p/home','https://life.douyin.com/p/other','http://life.douyin.com/p/home','https://life.douyin.com/p/home?unknown=1','https://life.douyin.com/p/home#x'):
   with self.subTest(url=url):
    self.url=url;w=self.workflow()
    with self.assertRaises(ValueError):w.tick()
  self.url='https://life.douyin.com/p/home';self.state['phase']='openReviews';w=self.workflow()
  with self.assertRaisesRegex(ValueError,'home-phase'):w.tick()
 def test_unconfirmed_or_unknown_switch_and_changed_company_are_rejected(self):
  original=copy.deepcopy(self.state)
  for kind in ('missing','unknown','wrong-target','duplicate-company'):
   self.state=copy.deepcopy(original);self.tree=copy.deepcopy(self.original_tree)
   if kind=='missing':self.state['calls']=[c for c in self.state['calls'] if c['phase']!='confirmSwitch']
   elif kind=='unknown':self.state['calls'][-1]['state']='unknown'
   elif kind=='wrong-target':self.state['calls'][-2]['result']['clicked']['name']='another company'
   else:
    label=next(n for n in b.nodes(self.tree) if 'AccountInfo-module__companyName--' in n.get('attributes',{}).get('class',''));self.tree['root']['children'].append(copy.deepcopy(label))
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.workflow().tick()
 def test_old_identity_provider_or_duplicate_registry_mapping_cannot_complete(self):
  original=copy.deepcopy(self.state);job=copy.deepcopy(self.job)
  for kind in ('old','provider','old-manager','duplicate-registry'):
   self.state=copy.deepcopy(original);self.job=copy.deepcopy(job);self.tree=copy.deepcopy(self.original_tree);self.state['phase']='identityAfterSwitch'
   if kind=='old':self.add_card(self.state['entry_identity'])
   elif kind=='provider':self.add_card({**self.job['identity_baseline'],'provider':'服务商000000001'})
   elif kind=='old-manager':self.add_card({**self.job['identity_baseline'],'manager':self.state['entry_identity']['manager']})
   else:self.job['known_company_identities']['999999999']=self.job['identity_baseline'];self.add_card()
   with self.subTest(kind=kind),self.assertRaises(ValueError):self.workflow().tick()
 def test_existing_groupid_route_still_uses_original_behavior(self):
  self.url='https://life.douyin.com/p/home?groupid='+self.job['groupid'];w=self.workflow();w.tick();self.assertEqual(w.s['phase'],'accountAfterSwitch');self.assertNotIn('post_switch_scope_evidence',w.s)
if __name__=='__main__':unittest.main()
