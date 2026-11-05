"""Candidate fake connector only. No browser, URLs constructed only in fixtures."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;S=HERE.parent/'scripts';sys.path.insert(0,str(S))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
fixture=load('preflight_shape_fixture',HERE/'test_center_analysis_tab.py');q=load('preflight_query',S/'bridge-governance-query.py');import center_analysis_tab as a
class Preflight(unittest.TestCase):
 def setUp(self):
  self.f=fixture.Layout();self.f.setUp();self.addCleanup(self.f.doCleanups);self.current=copy.deepcopy(self.f.t);self.job=self.f.f.job;self.jobpath=self.f.jobpath;self.path=self.f.f.root/'query-preflight.json';self.calls=[];self.fail=False;self.after=self.f.dual_layer();self.before=a.ref(self.f.op)
 def invoke(self,c):
  self.calls.append(c)
  if c['op']=='tabs':out=[{'tabs':[self.f.obs['tab']]}]
  elif c['op']=='tree':out=copy.deepcopy(self.current)
  elif c['op']=='ping':out={'version':q.nav.VERSION,'safety':'DOM-only','content_build':'governance-center-analysis-preflight-spacer-v2','governance_analysis_tab_policy':a.MARKER,'governance_query_policy':'observed-dom-20261021-v1','governance_calendar_policy':'date-item-div-v3-single'}
  elif c['op']=='click':
   selector=c['locator']['value']
   if selector=='#analysis':
    state=json.loads((self.jobpath.parent/'.center-analysis-tab'/q.nav.tag(self.job)/'state.json').read_text());self.assertEqual(state['intent']['state'],'unknown')
    if self.fail:raise TimeoutError('unknown original analysis')
    self.current=copy.deepcopy(self.after);out={'clicked':{'selector':'#analysis','name':'违规分析'}}
   else:self.assertEqual(selector,'#date');self.assertEqual(json.loads(self.path.read_text())['calls'][-1]['state'],'unknown');out={'clicked':{'selector':'#date'}}
  else:raise AssertionError(c)
  return {'ok':True,'result':out}
 def runner(self,ref=True):return q.Runner(self.job,5,self.path,q.nav.VERSION,self.invoke,job_ref=a.ref(self.jobpath) if ref else None)
 def click_count(self,selector):return sum(c['op']=='click' and c['locator']['value']==selector for c in self.calls)
 def test_prevention_one_navigation_then_next_tick_fresh_date(self):
  r=self.runner();r.step();self.assertEqual(r.s['phase'],'open-date');self.assertEqual(self.click_count('#analysis'),1);self.assertEqual(self.click_count('#date'),0);self.assertEqual(r.s['analysis_preflight']['state'],'complete');r=self.runner();r.step();self.assertEqual(self.click_count('#analysis'),1);self.assertEqual(self.click_count('#date'),1);self.assertEqual(r.s['phase'],'select-start')
 def test_observed_four_child_prevention_and_dual_layer_after(self):
  basic=next(n for n in a.nav.nodes(self.current) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner');basic['children'].insert(2,{'tag':'span','role':'generic','name':'','selector':'#spacer','attributes':{'class':'governance_merchant-tab-bar-item-span'},'children':[]});self.runner().step();self.assertEqual(self.click_count('#analysis'),1);self.runner().step();self.assertEqual(self.click_count('#date'),1)
 def test_already_ready_no_adapter_or_analysis_input(self):
  self.current=copy.deepcopy(self.after);self.runner().step();self.assertEqual(self.click_count('#analysis'),0);self.assertEqual(self.click_count('#date'),1);self.assertFalse((self.jobpath.parent/'.center-analysis-tab').exists())
 def test_original_confirmed_manifest_only_reads_and_never_prepares_new_key(self):
  manifest=a.prepare(a.ref(self.jobpath),self.before,'original-stable-key');a.run(manifest,self.invoke);prior=json.loads(Path(manifest['path']).with_name('state.json').read_text())['intent'];self.calls=[]
  with patch.object(a,'prepare',side_effect=AssertionError('no replacement manifest')):self.runner().step()
  self.assertEqual(self.click_count('#analysis'),0);self.assertEqual(self.click_count('#date'),1);state=json.loads(Path(manifest['path']).with_name('state.json').read_text());self.assertEqual(prior,state['intent']);self.assertEqual(a.read(manifest)['key'],'original-stable-key')
 def test_unknown_analysis_or_layout_holds_date_without_new_key(self):
  for kind in ('analysis','legacy'):
   if kind=='analysis':
    manifest=a.prepare(a.ref(self.jobpath),self.before,'unknown-key');p=Path(manifest['path']).with_name('state.json');q.nav.write_json(p,{'manifest':manifest,'phase':'prepared','intent':{'state':'unknown','key':'unknown-key'}})
   else:
    p=self.jobpath.parent/'.center-legacy-layout'/q.nav.tag(self.job)/'state.json';q.nav.write_json(p,{'intent':{'state':'unknown','key':'original-layout'}})
   before=p.read_bytes();r=self.runner();r.step();self.assertIn('unknown',r.s['waiting_for']);self.assertEqual(p.read_bytes(),before);self.assertEqual(self.click_count('#date'),0);self.assertEqual(self.click_count('#analysis'),0)
 def test_canonical_conflict_and_wrong_job_ref_refuse_before_input(self):
  manifest=a.prepare(a.ref(self.jobpath),self.before,'fixed-key');path=Path(manifest['path']);m=a.read(manifest);m['window_id']=99;q.nav.write_json(path,m)
  with self.assertRaisesRegex(ValueError,'canonical-manifest-conflict'):self.runner().step()
  bad=self.f.f.root/'wrong-job.json';q.nav.write_json(bad,{**self.job,'company':'other'})
  with self.assertRaisesRegex(ValueError,'pinned-job-conflict'):q.Runner(self.job,5,self.path,q.nav.VERSION,self.invoke,job_ref=a.ref(bad))
  self.assertEqual(self.click_count('#date')+self.click_count('#analysis'),0)
 def test_basic_pair_without_ref_no_fallback_legacy_nonpair_unchanged(self):
  with self.assertRaisesRegex(ValueError,'original-job-ref-required'):self.runner(False).step()
  self.current=copy.deepcopy(self.f.legacy);root=next(n for n in a.nav.nodes(self.current) if n.get('attributes',{}).get('id')=='governanceRoot');root['children']=[n for n in root['children'] if n.get('attributes',{}).get('class')!='governance_merchant-tab-bar-items-container'];self.runner(False).step();self.assertEqual(self.click_count('#date'),1)
 def test_spacer_interactive_and_ambiguous_pair_never_date_fallback(self):
  for mode in ('tabindex','role','nonempty','duplicate'):
   self.current=copy.deepcopy(self.after);pair=next(n for n in a.nav.nodes(self.current) if n.get('attributes',{}).get('class')=='governance_merchant-tab-bar-items-inner' and any(c.get('name')=='违规分析' for c in n.get('children',[])))
   if mode=='tabindex':pair['children'][2]['attributes']['tabindex']='0'
   elif mode=='role':pair['children'][2]['role']='button'
   elif mode=='nonempty':pair['children'][2]['name']='unreviewed'
   else:next(n for n in a.nav.nodes(self.current) if n.get('attributes',{}).get('id')=='governanceRoot')['children'].append(copy.deepcopy(pair))
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.runner().step()
  self.assertEqual(self.click_count('#date')+self.click_count('#analysis'),0)
 def test_confirmed_original_navigation_before_read_failure_resumes_readonly(self):
  manifest=a.prepare(a.ref(self.jobpath),self.before,'confirmed-before-read-error')
  def cut(c):
   if c['op']=='tree' and self.click_count('#analysis'):raise ValueError('synthetic interrupted first after-read')
   return self.invoke(c)
  with self.assertRaisesRegex(ValueError,'interrupted'):a.run(manifest,cut)
  path=Path(manifest['path']).with_name('state.json');prior=json.loads(path.read_text());self.assertEqual(prior['phase'],'observe-analysis');self.assertEqual(prior['intent']['state'],'confirmed');self.calls=[]
  with patch.object(a,'prepare',side_effect=AssertionError('no new stable key')):self.runner().step()
  self.assertEqual(self.click_count('#analysis'),0);self.assertEqual(self.click_count('#date'),1);self.assertEqual(json.loads(path.read_text())['intent'],prior['intent'])
 def test_original_query_unknown_stops_before_even_readonly_observation(self):
  r=self.runner();r.s['calls']=[{'state':'unknown'}];r.save();before=len(self.calls);r.step();self.assertEqual(len(self.calls),before);self.assertIn('unknown',r.s['waiting_for'])
if __name__=='__main__':unittest.main()
