"""Portable synthetic public DOM and original query journals. Never live evidence."""
import copy,importlib.util,json
from pathlib import Path
import governance_dom as g
import test_governance_dom as dom
import test_center_compact_zero as center_fixture
import test_bridge_navigation as navigation_fixture
spec=importlib.util.spec_from_file_location('zero_fixture_query',Path(__file__).resolve().parents[1]/'scripts/bridge-governance-query.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
def node(tag,name='',classes='',children=()):return dom.n(name,tag,classes,list(children))
def records_tree():
 t=dom.tree();root=t['root'];old=next(n for n in root['children'] if n.get('tag')=='table');heads=next(n for n in g.walk(old) if n.get('tag')=='tr')['children']
 table=node('table',classes='governance_merchant-Table-Implement',children=[node('colgroup',classes='governance_merchant-Table-ColGroup',children=[node('col',classes='governance_merchant-Table-Col') for _ in range(10)]),node('thead',classes='governance_merchant-Table-Head',children=[node('tr',classes='governance_merchant-Table-Row',children=heads)]),node('tbody',classes='governance_merchant-Table-Body')]);table['role']='table';table['children'][2]['role']='rowgroup'
 empty=node('div',classes='governance_merchant-Table-Empty',children=[node('div',classes='governance_merchant-empty',children=[node('div',classes='governance_merchant-empty-inner',children=[node('svg'),node('p','暂无数据')])])]);container=node('div',classes='governance_merchant-Table-Container governance_merchant-Table-Container_scrollable',children=[table,empty])
 root['children']=[n for n in root['children'] if n is not old and 'governance_merchant-pager' not in g.cls(n) and not ('governance_merchant-tab-bar-item' in g.cls(n))]
 root['children'] += [node('div','全部','governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active governance_merchant-tab-bar-item-type-text',[node('span','全部','governance_merchant-tab-bar-item-label')]),node('div','违规记录管理','governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active governance_merchant-tab-bar-item-type-line'),container]
 root['children'] += [navigation_fixture.leaf('服务商123456789','#provider'),navigation_fixture.leaf('账户ID987654321','#account'),navigation_fixture.leaf('我的客户经理测试经理 切换公司','#manager')]
 return t
class Evidence:
 def __init__(self,case,root):
  self.case=case;self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.events=[]
  f=navigation_fixture.NavigationTests('test_already_center_observes_only_no_actions');f.setUp();case.addCleanup(f.doCleanups);self.job=f.job;self.jobpath=self.root/'job.json';q.nav.write_json(self.jobpath,self.job);self.raw=self.obs(records_tree(),g.RECORDS)
 def obs(self,tree,path):
  tree=copy.deepcopy(tree);tree['url']='https://life.douyin.com'+path
  return {'source':'local-dom-bridge','observed_at':'2026-10-22T10:00:00+08:00','tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+path+'?groupid=123'},'tree':tree,'not_business_capture':True}
 def save(self,path,value):q.nav.write_json(path,value);return {'path':str(Path(path).resolve()),'sha256':q.nav.digest(path)}
 def query(self,name,path,final,exhausted=False):
  folder=self.root/(name+'-evidence');folder.mkdir();phase='open-date';plan=g.QueryPlan(self.job['start'],self.job['end_exclusive']);calls=[];refs=[]
  old=copy.deepcopy(final);g.date_input(old)['attributes']['value']='2026/10/15 ～ 2026/10/22';calendar=dom.with_calendar(copy.deepcopy(old));before_trees=[old,calendar,copy.deepcopy(calendar)]
  # Public selected-day shape only; no page event is executed.
  selected=g.calendar_action(before_trees[2],'2026-10-16')['action']['locator']['value'];next(n for n in g.nodes(before_trees[2]) if n.get('selector')==selected)['attributes']['class']+=' governance_merchant-date-selected governance_merchant-date-state-single'
  if path==g.RECORDS:before_trees.append(copy.deepcopy(final))
  for i,tree in enumerate(before_trees):
   raw=self.obs(tree,path);ref=self.save(folder/(str(i)+'.json'),raw);refs.append(ref);step=plan.next(raw['tree'],{'phase':phase});command={**step['command'],'tabId':5};target=g.one([n for n in g.nodes(raw['tree']) if n.get('selector')==command['locator']['value']],'synthetic-query-target');calls.append({'state':'confirmed','command':command,'before':ref,'intent_at':'2026-10-22T09:59:00+00:00','postcondition':None,'result':{'kind':'filter','version':q.nav.VERSION,'clicked':copy.deepcopy(target)}});phase=step['next_phase']
  raw=self.obs(final,path);last=self.save(folder/'final.json',raw);refs.append(last);state={'fingerprint':q.nav.tag(self.job),'tab_id':5,'approved_version':q.nav.VERSION,'phase':'profile-required' if path==g.CENTER else 'collect-page','calls':calls,'pages':[],'observations':refs,'last_observation':last,'business_progress_changed':False,'profile_accepted':False}
  if path==g.CENTER:state['waiting_for']='analysis-all-reasons-actual-view-profile-required'
  elif exhausted:state.update(settling_exhausted=True,needs_changed_tree=calls[-1]['before'],read_only_settling={'checks':5,'max_checks':5,'original_call_index':3,'last_observation':last,'reason':'governance-all-tab-not-unique'})
  p=self.root/(name+'.json');self.save(p,state);return p,raw
 def original_records(self):return self.query('records-query',g.RECORDS,self.raw['tree'],True)
 def center_query(self):
  f=center_fixture.CompactZero('test_explicit_zero_analysis_never_claims_records_or_batch_zero');f.setUp();self.case.addCleanup(f.doCleanups);return self.query('center-query',g.CENTER,f.tree)[0]
 def invoke(self,command):
  self.events.append(command);self.case.assertIn(command['op'],('tabs','ping','tree'))
  result=[{'tabs':[self.raw['tab']]}] if command['op']=='tabs' else self.raw['tree'] if command['op']=='tree' else {'version':q.nav.VERSION,'safety':'DOM-only'}
  return {'ok':True,'result':result}
