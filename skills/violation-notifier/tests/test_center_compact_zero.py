"""Synthetic public DOM/query state; no real UI or business acquisition."""
import copy,importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fixture=load('compact_zero_fixtures',ROOT/'skills/violation-notifier/tests/test_center_analysis_tab.py');d=load('formal_compact_discovery',ROOT/'skills/violation-notifier/scripts/bridge-profile-discovery.py');c=load('formal_analysis_zero',ROOT/'skills/violation-notifier/scripts/center_reconciliation.py');a=load('formal_compact_analysis_build',ROOT/'skills/violation-notifier/scripts/center_analysis_tab.py')
def n(tag,name,cls,selector,children=()):return {'tag':tag,'role':'generic','name':name,'selector':selector,'attributes':{'class':cls},'children':list(children),'disabled':False}
class CompactZero(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Layout('test_once_and_real_legacy_date_input_before_layout_completion');self.f.setUp();self.addCleanup(self.f.doCleanups);self.tree=copy.deepcopy(self.f.legacy);self.root=next(x for x in c.g.nodes(self.tree) if x.get('attributes',{}).get('id')=='governanceRoot')
  self.root['children']=[x for x in self.root['children'] if x.get('attributes',{}).get('class') not in ('topList-DDjs8Y','todoSummary-xpJGcr')]
  date=c.g.date_input(self.tree);date['attributes']['value']='2026/10/16 ～2026/10/20'
  self.label=n('p','违规记录','compactLabel-aFEjMF','#compact-records');self.item=n('div','违规记录 新增1','compactItem-TpyZAq','#compact-item',[self.label,n('span','新增1','governance_merchant-tooltip','#badge')]);self.tools=n('div','违规记录 新增1 预警记录 8','todoSummary-xpJGcr compact-Gcf1ET boardSuccess-tXR2Eq','#tools',[n('div','违规记录 新增1','compactList-kThnsC','#list',[self.item])]);self.root['children'].append(self.tools)
  self.root['children'].append(n('div','全部','governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active governance_merchant-tab-bar-item-type-capsule','#all'))
  literal='2026/10/16～2026/10/20期间 您暂无违规记录，可选择其他时间范围查询相关违规信息～'
  self.summary=n('p',literal,'summaryText-zSe9bU','#zero-summary');self.chart=n('div','暂无图表数据','governance_merchant-empty-inner-text','#chart-empty');self.top=n('div','暂无数据','governance_merchant-empty-inner-text','#top-empty')
  self.distribution=n('div','总结 '+literal+' 暂无图表数据 违规原因 Top10 暂无数据','distributionView-C7cPRe','#distribution',[n('div','总结 '+literal,'summary-RY8k0Q','#summary',[n('span','总结','summaryLabel-jKfWQQ','#summary-label'),self.summary]),n('div','暂无图表数据','sectionEmpty-PdpC3y','#chart',[self.chart]),n('div','违规原因 Top10 暂无数据','topList-DDjs8Y','#top',[n('div','违规原因 Top10','title-KYD1nB','#top-title'),self.top])]);self.root['children'].append(self.distribution)
 def zero(self):return c.center_page(self.tree,start='2026-10-16',end_exclusive='2026-10-21')
 def test_compact_records_target_is_unique_and_not_a_count_fact(self):
  result=d.center_targets(self.tree,self.f.f.job['identity'])['records'];self.assertEqual(result['selector'],'#compact-records');self.assertEqual(result['name'],'违规记录')
  self.item['name']='违规记录 新增999';self.assertEqual(d.center_targets(self.tree,self.f.f.job['identity'])['records']['selector'],'#compact-records')
 def test_bad_compact_shape_or_duplicate_fails(self):
  for mode in ('class','parent','label','duplicate'):
   tree=copy.deepcopy(self.tree);root=next(x for x in c.g.nodes(tree) if x.get('attributes',{}).get('id')=='governanceRoot');label=next(x for x in c.g.nodes(tree) if x.get('selector')=='#compact-records')
   if mode=='class':label['attributes']['class']='unreviewed'
   elif mode=='parent':next(x for x in c.g.nodes(tree) if x.get('selector')=='#compact-item')['attributes']['class']='unreviewed'
   elif mode=='label':label['name']='处理整改'
   else:root['children'].append(copy.deepcopy(self.tools))
   self.assertIn('gap',d.center_targets(tree,self.f.f.job['identity'])['records'])
 def test_explicit_zero_analysis_never_claims_records_or_batch_zero(self):
  result=self.zero();self.assertEqual(result['analysis_total'],0);self.assertFalse(result['records_queried']);self.assertFalse(result['records_zero_verified']);self.assertFalse(result['business_zero_verified']);self.assertEqual(result['end_exclusive'],'2026-10-21')
  with self.assertRaisesRegex(ValueError,'positive-evidence-required'):c.reconcile([result],[])
 def test_zero_range_empty_or_positive_contradictions_rejected(self):
  for mode in ('range','all','chart','top','positive'):
   saved=copy.deepcopy(self.tree)
   if mode=='range':self.summary['name']=self.summary['name'].replace('10/20','10/21')
   elif mode=='all':next(x for x in c.g.nodes(self.tree) if x.get('selector')=='#all')['attributes']['class']='governance_merchant-tab-bar-item'
   elif mode=='chart':self.chart['name']='加载中'
   elif mode=='top':self.top['name']='存在记录'
   else:self.distribution['children'].append(n('div','真实正数bucket','listItem-CaUVh0','#positive'))
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.zero()
   self.tree=saved;self.root=next(x for x in c.g.nodes(self.tree) if x.get('attributes',{}).get('id')=='governanceRoot');self.summary=next(x for x in c.g.nodes(self.tree) if x.get('selector')=='#zero-summary');self.chart=next(x for x in c.g.nodes(self.tree) if x.get('selector')=='#chart-empty');self.top=next(x for x in c.g.nodes(self.tree) if x.get('selector')=='#top-empty');self.distribution=next(x for x in c.g.nodes(self.tree) if x.get('selector')=='#distribution')
 def test_compact_probe_requires_hot_policy_before_any_intent(self):
  job=self.f.f.job;state=self.f.f.root/'compact-probe.json';calls=[];ready=False
  def invoke(cmd):
   calls.append(cmd)
   if cmd['op']=='tabs':return {'ok':True,'result':[{'tabs':[{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+d.nav.CENTER+'?groupid=123'}]}]}
   if cmd['op']=='tree':return {'ok':True,'result':self.tree}
   if cmd['op']=='ping':return {'ok':True,'result':{'version':d.POLICY_VERSION,'safety':'DOM-only',**({'content_build':'governance-center-compact-records-v1','governance_compact_records_policy':'observed-compact-record-entry-v1'} if ready else {})}}
   if cmd['op']=='click':return {'ok':True,'result':{'clicked':True}}
   raise AssertionError(cmd)
  p=d.Probe(job,5,state,'records',invoke);p.step();self.assertEqual(p.s['calls'],[]);self.assertIn('compact-record',p.s['waiting_for']);ready=True;p.step();self.assertEqual(len(p.s['calls']),1);self.assertEqual(p.s['calls'][0]['command']['locator']['value'],'#compact-records');p.step();self.assertEqual(p.s['phase'],'profile-required');self.assertEqual(sum(x['op']=='click' for x in calls),1)
 def test_analysis_adapter_accepts_exact_new_build_but_not_future(self):
  f=fixture.Layout('test_once_and_real_legacy_date_input_before_layout_completion');f.setUp();self.addCleanup(f.doCleanups);base=f.invoke
  def invoke(cmd):
   result=base(cmd)
   if cmd['op']=='ping':result['result']['content_build']='governance-center-compact-records-v1'
   return result
  manifest=a.prepare(a.ref(f.jobpath),a.ref(f.op),'fixture-display-key');self.assertEqual(a.run(manifest,invoke)['phase'],'complete')
  self.assertEqual(set(a.ACCEPTED_BUILDS),{'governance-center-analysis-tab-v1','governance-center-compact-records-v1','governance-center-analysis-preflight-spacer-v2','normal-review-adjacent-pager-v1'})
 def test_analysis_future_build_rejected_before_any_click(self):
  f=fixture.Layout('test_once_and_real_legacy_date_input_before_layout_completion');f.setUp();self.addCleanup(f.doCleanups);base=f.invoke
  def invoke(cmd):
   result=base(cmd)
   if cmd['op']=='ping':result['result']['content_build']='governance-center-compact-records-future'
   return result
  manifest=a.prepare(a.ref(f.jobpath),a.ref(f.op),'fixture-display-key')
  with self.assertRaisesRegex(ValueError,'layout-reviewed-hotbuild-required'):a.run(manifest,invoke)
  self.assertFalse(any(c['op']=='click' for c in f.calls))
if __name__=='__main__':unittest.main()
