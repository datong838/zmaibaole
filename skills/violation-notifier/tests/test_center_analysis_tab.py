"""Synthetic UI/navigation transport; no real prepare, click, or browser."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('formal_center_analysis_tab',ROOT/'skills/violation-notifier/scripts/center_analysis_tab.py');fixtures=load('layout_fixtures',ROOT/'skills/violation-notifier/tests/test_bridge_profile_discovery.py')
class Layout(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.DiscoveryTests('test_actual_structure_required');self.f.setUp();self.addCleanup(self.f.doCleanups);self.jobpath=self.f.root/'job.json';m.nav.write_json(self.jobpath,self.f.job);self.legacy=self.f.tree();self.t=copy.deepcopy(self.legacy);root=next(n for n in m.nav.nodes(self.t) if n.get('attributes',{}).get('id')=='governanceRoot')
  def node(tag,name,cls,selector,children=()):return {'tag':tag,'role':'button' if tag=='button' else 'generic','name':name,'selector':selector,'attributes':{'class':cls},'children':list(children),'disabled':False}
  base='governance_merchant-tab-bar-item governance_merchant-tab-bar-item-type-basic'
  self.button=node('div','违规分析',base,'#analysis',[node('span','违规分析','governance_merchant-tab-bar-item-label','#analysis-label')])
  prevent=node('div','违规预防',base+' governance_merchant-tab-bar-item-active','#prevent',[node('span','违规预防','governance_merchant-tab-bar-item-label','#prevent-label')])
  container=node('div','违规分析 违规预防','governance_merchant-tab-bar-items-container','#tabs',[node('div','违规分析 违规预防','governance_merchant-tab-bar-items-inner','#inner',[self.button,prevent,node('div','','governance_merchant-tab-bar-items-inner-line','#line')])])
  root['children']=[container]
  after_container=copy.deepcopy(container);after_container['children'][0]['children'][0]['attributes']['class']+=' governance_merchant-tab-bar-item-active';after_container['children'][0]['children'][1]['attributes']['class']=base
  next(n for n in m.nav.nodes(self.legacy) if n.get('attributes',{}).get('id')=='governanceRoot')['children'].append(after_container)
  self.current=copy.deepcopy(self.t);self.calls=[];self.version=True;self.error=False
  self.obs={'source':'local-dom-bridge','tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+m.nav.CENTER+'?groupid=123'},'tree':self.t};self.op=self.f.root/'before.json';m.nav.write_json(self.op,self.obs)
 def prepare(self):return m.prepare(m.ref(self.jobpath),m.ref(self.op),'fixture-display-key')
 def invoke(self,c):
  self.calls.append(c)
  if c['op']=='tabs':return {'ok':True,'result':[{'tabs':[self.obs['tab']]}]}
  if c['op']=='tree':return {'ok':True,'result':copy.deepcopy(self.current)}
  if c['op']=='ping':return {'ok':True,'result':{'version':m.nav.VERSION,'safety':'DOM-only','content_build':m.BUILD if self.version else 'old-build','governance_analysis_tab_policy':m.MARKER}}
  if c['op']=='click':
   path=Path(self.prepare()['path']).with_name('state.json');state=json.loads(path.read_text());self.assertEqual(state['intent']['state'],'unknown')
   if self.error:raise TimeoutError('original click unknown')
   self.current=copy.deepcopy(self.legacy);return {'ok':True,'result':{'clicked':{'name':'违规分析','selector':'#analysis'}}}
  raise AssertionError(c)
 def test_once_and_real_legacy_date_input_before_layout_completion(self):
  manifest=self.prepare();s=m.run(manifest,self.invoke);self.assertEqual(s['phase'],'complete');self.assertFalse(s['dates_queried']);self.assertEqual(s['intent']['command']['kind'],'navigation');m.run(manifest,self.invoke);self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
 def test_manifest_target_cannot_differ_from_pinned_before(self):
  manifest=self.prepare();path=Path(manifest['path']);value=json.loads(path.read_text());value['tab_id']=99;m.nav.write_json(path,value)
  with self.assertRaisesRegex(ValueError,'original-context-conflict'):m.run(m.ref(path),self.invoke)
  self.assertFalse(self.calls)
 def test_old_build_cannot_issue_click(self):
  self.version=False
  with self.assertRaisesRegex(ValueError,'hotbuild-required'):m.run(self.prepare(),self.invoke)
  self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_unknown_original_intent_never_replayed_or_new_manifest(self):
  self.error=True;manifest=self.prepare()
  with self.assertRaises(TimeoutError):m.run(manifest,self.invoke)
  s=m.run(manifest,self.invoke);self.assertEqual(s['intent']['state'],'unknown');self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
  with self.assertRaisesRegex(ValueError,'original-manifest'):m.prepare(m.ref(self.jobpath),m.ref(self.op),'new-key')
 def test_source_identity_route_window_and_actual_shape_fail_closed(self):
  for mode in ('identity','route','window','duplicate','confirmation'):
   self.current=copy.deepcopy(self.t);self.obs['tab']['windowId']=3
   if mode=='identity':self.current['root']['children'][0]['name']='服务商000000000'
   elif mode=='route':self.current['url']='https://life.douyin.com/p/unreviewed'
   elif mode=='window':self.obs['tab']['windowId']=9
   elif mode=='duplicate':self.current['root']['children'].append(copy.deepcopy(self.current['root']['children'][-1]))
   else:self.current['root']['children'].append({'tag':'dialog','role':'dialog','name':'配置确认','children':[]})
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.run(self.prepare(),self.invoke)
  self.assertFalse(any(c['op']=='click' for c in self.calls))
 def test_already_analysis_ready_is_readonly_and_ambiguous_active_rejected(self):
  self.current=copy.deepcopy(self.legacy);self.obs['tree']=self.current;m.nav.write_json(self.op,self.obs)
  state=m.run(self.prepare(),self.invoke);self.assertEqual(state['phase'],'complete');self.assertEqual(state['layout_result'],'analysis-tab-already-ready-readonly');self.assertFalse(any(c['op']=='click' for c in self.calls))
  for active in (False,True):
   tree=copy.deepcopy(self.t);pair=next(n for n in m.nav.nodes(tree) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner')
   for tab in pair['children'][:2]:tab['attributes']['class']='governance_merchant-tab-bar-item governance_merchant-tab-bar-item-type-basic'+(' governance_merchant-tab-bar-item-active' if active else '')
   with self.assertRaisesRegex(ValueError,'single-active'):m.tabs(tree)
 def test_original_layout_unknown_stays_untouched_and_blocks_new_input(self):
  manifest=self.prepare();path=self.jobpath.parent/'.center-legacy-layout'/m.nav.tag(self.f.job)/'state.json';m.nav.write_json(path,{'intent':{'state':'unknown','key':'old-layout-key'}});before=path.read_bytes()
  with self.assertRaisesRegex(ValueError,'original-layout-intent-unknown'):m.run(manifest,self.invoke)
  self.assertFalse(self.calls);self.assertEqual(path.read_bytes(),before)
 def test_date_input_behind_prevention_does_not_claim_analysis_ready(self):
  tree=copy.deepcopy(self.legacy);pair=next(n for n in m.nav.nodes(tree) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner');pair['children'][0]['attributes']['class']='governance_merchant-tab-bar-item governance_merchant-tab-bar-item-type-basic';pair['children'][1]['attributes']['class']+=' governance_merchant-tab-bar-item-active'
  with self.assertRaisesRegex(ValueError,'analysis-tab-not-active'):m.ready(tree)
 def dual_layer(self):
  tree=copy.deepcopy(self.legacy);pair=next(n for n in m.nav.nodes(tree) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner');pair['children'].insert(2,{'tag':'span','role':'generic','name':'','selector':'#basic-spacer','attributes':{'class':'governance_merchant-tab-bar-item-span'},'children':[]})
  root=next(n for n in m.nav.nodes(tree) if n.get('attributes',{}).get('id')=='governanceRoot');capsule=copy.deepcopy(root['children'][-1]);inner=capsule['children'][0]
  inner['name']='全部 门店 商品 短视频 直播';inner['children']=[]
  for index,label in enumerate(('全部','门店','商品','短视频','直播')):
   inner['children'].append({'tag':'div','role':'generic','name':label,'selector':'#capsule-'+str(index),'attributes':{'class':'governance_merchant-tab-bar-item governance_merchant-tab-bar-item-type-capsule'+(' governance_merchant-tab-bar-item-active' if index==0 else '')},'children':[{'tag':'span','role':'generic','name':label,'selector':'#capsule-label-'+str(index),'attributes':{'class':'governance_merchant-tab-bar-item-label'},'children':[]}]})
  root['children'].append(capsule);return tree
 def test_existing_confirmed_intent_reads_dual_layer_after_without_second_click(self):
  previous=load('synthetic_former_single_pair_assumption',ROOT/'skills/violation-notifier/scripts/center_analysis_tab.py');original_tabs=previous.tabs
  # Reproduce the former all-inner cardinality assumption, without an old live
  # source snapshot or claiming that this synthetic module is the deployed past.
  def former_single_pair(tree):
   pairs=[n for n in previous.nav.nodes(tree) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner']
   if len(pairs)!=1:raise ValueError('analysis-tab-pair-not-unique')
   return original_tabs(tree)
  previous.tabs=former_single_pair;self.legacy=self.dual_layer();manifest=self.prepare()
  with self.assertRaisesRegex(ValueError,'pair-not-unique'):previous.run(manifest,self.invoke)
  path=Path(manifest['path']).with_name('state.json');state=json.loads(path.read_text());self.assertEqual(state['phase'],'observe-analysis');self.assertEqual(state['intent']['state'],'confirmed');original_intent=copy.deepcopy(state['intent'])
  state=m.run(manifest,self.invoke);self.assertEqual(state['phase'],'complete');self.assertEqual(state['intent'],original_intent);self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
 def test_duplicate_basic_pair_or_nonempty_spacer_rejected_capsule_not_substitute(self):
  tree=self.dual_layer();self.assertTrue(m.ready(tree));pair=next(n for n in m.nav.nodes(tree) if n.get('name')=='违规分析 违规预防' and n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner')
  for mode in ('duplicate-basic','text-spacer','unknown-spacer','capsule-only'):
   altered=copy.deepcopy(tree);root=next(n for n in m.nav.nodes(altered) if n.get('attributes',{}).get('id')=='governanceRoot');basic=next(n for n in m.nav.nodes(altered) if n.get('name')=='违规分析 违规预防' and n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner')
   if mode=='duplicate-basic':root['children'].append(copy.deepcopy(root['children'][-2]))
   elif mode=='text-spacer':basic['children'][2]['name']='unknown'
   elif mode=='unknown-spacer':basic['children'][2]['attributes']['class']='unknown'
   else:basic['children'][0]['name']='其他';basic['children'][1]['name']='其他2'
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.ready(altered)
if __name__=='__main__':unittest.main()
