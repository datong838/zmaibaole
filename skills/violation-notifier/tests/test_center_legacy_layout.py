"""Synthetic UI/navigation transport; no real prepare, click, or browser."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
m=load('formal_center_legacy_layout',ROOT/'skills/violation-notifier/scripts/center_legacy_layout.py');fixtures=load('layout_fixtures',ROOT/'skills/violation-notifier/tests/test_bridge_profile_discovery.py')
class Layout(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.DiscoveryTests('test_actual_structure_required');self.f.setUp();self.addCleanup(self.f.doCleanups);self.jobpath=self.f.root/'job.json';m.nav.write_json(self.jobpath,self.f.job);self.legacy=self.f.tree();self.t=copy.deepcopy(self.legacy);root=next(n for n in m.nav.nodes(self.t) if n.get('attributes',{}).get('id')=='governanceRoot')
  def node(tag,name,cls,selector,children=()):return {'tag':tag,'role':'button' if tag=='button' else 'generic','name':name,'selector':selector,'attributes':{'class':cls},'children':list(children),'disabled':False}
  self.button=node('button','回到旧版','governance_merchant-btn governance_merchant-btn-size-md governance_merchant-btn-type-text governance_merchant-btn-shape-angle governance_merchant-can-input-grouped backButton-cbYsPY','#back')
  root['children']=[node('div','新版中心','container-a3IjFk','#container',[node('div','违规中心 回到旧版','header-EaBIRz','#header',[node('p','违规中心','title-N66Jpb','#title'),node('div','回到旧版','actions-lq_eBp','#actions',[self.button])])])]
  self.current=copy.deepcopy(self.t);self.calls=[];self.version=True;self.error=False
  self.obs={'source':'local-dom-bridge','tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+m.nav.CENTER+'?groupid=123'},'tree':self.t};self.op=self.f.root/'before.json';m.nav.write_json(self.op,self.obs)
 def prepare(self):return m.prepare(m.ref(self.jobpath),m.ref(self.op),'fixture-display-key')
 def invoke(self,c):
  self.calls.append(c)
  if c['op']=='tabs':return {'ok':True,'result':[{'tabs':[self.obs['tab']]}]}
  if c['op']=='tree':return {'ok':True,'result':copy.deepcopy(self.current)}
  if c['op']=='ping':return {'ok':True,'result':{'version':m.nav.VERSION,'safety':'DOM-only','content_build':m.BUILD if self.version else 'old-build','governance_center_layout_policy':m.MARKER}}
  if c['op']=='click':
   path=Path(self.prepare()['path']).with_name('state.json');state=json.loads(path.read_text());self.assertEqual(state['intent']['state'],'unknown')
   if self.error:raise TimeoutError('original click unknown')
   self.current=copy.deepcopy(self.legacy);return {'ok':True,'result':{'clicked':{'name':'回到旧版','selector':'#back'}}}
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
   elif mode=='duplicate':self.current['root']['children'].append(copy.deepcopy(self.button))
   else:self.current['root']['children'].append({'tag':'dialog','role':'dialog','name':'配置确认','children':[]})
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.run(self.prepare(),self.invoke)
  self.assertFalse(any(c['op']=='click' for c in self.calls))
if __name__=='__main__':unittest.main()
