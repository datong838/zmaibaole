"""Recovery orchestration uses actual public trees and explicitly simulated page two/filter results."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_dom as g,governance_rates_recovery as rr
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name).resolve();self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);snapshot=DIR/'rates-recovery/source-parent-317bcff8387a23310b77302ec82d507471da3adc7380c5344b741a350faef0de.json';self.parent=json.loads((snapshot if snapshot.exists() else DIR/'state.json').read_text());self.manifest={'kind':'rates-notice-list-recovery-v1','detail_manifest':d.ref(BASE/'detail-inspection-manifest.json'),'parent_state':d.ref(snapshot if snapshot.exists() else DIR/'state.json')};self.live_parent=self.folder/'parent.json';self.live_parent.write_bytes((snapshot if snapshot.exists() else DIR/'state.json').read_bytes());self.source=(self.m,self.v,self.parent,self.v['query']['rows'][12]);self.center_default=d.document(d.ref(DIR/'state-evidence/0065.json'));self.center_one=d.document(d.ref(BASE/'center-analysis-query-v9-evidence/0016.json'));self.center_two=copy.deepcopy(self.center_one)
  root=g.root(self.center_two['tree'],g.CENTER);panel=g.one(g.classnodes(root,'topList-DDjs8Y'),'test');items=g.classnodes(panel,'listItem-CaUVh0');legend=rr.center.center_page(self.center_one['tree'],start=self.v['job']['start'],end_exclusive=self.v['job']['end_exclusive'])['legend']
  # This is synthetic page-two data, not a claim the platform page was observed.
  for i,item in enumerate(items):
   g.one(g.classnodes(item,'name-vjRMI5'),'test')['name']=legend[i+5];g.one(g.classnodes(item,'rank-mj9wvJ'),'test')['name']=str(i+6);g.one(g.classnodes(item,'count-PUTPse'),'test')['name']='1'
  for li in g.classnodes(panel,'governance_merchant-pager-item'):
   cls=li['attributes']['class'].split();cls=[c for c in cls if c!='governance_merchant-pager-item-checked']
   if g.text(li)=='2':cls.append('governance_merchant-pager-item-checked')
   li['attributes']['class']=' '.join(cls)
  self.record_one=d.document(self.v['query']['pages'][0]['observation']);self.record_two=d.document(self.v['query']['pages'][1]['observation']);self.current=self.center_default;self.calls=[];self.filter_calls=[];self.lose=None;self.mismatch_records=False
 def invoke(self,c):
  if c['op']=='tabs':value=[{'tabs':[self.current['tab']]}]
  elif c['op']=='ping':value={'version':d.nav.VERSION,'safety':'DOM-only','governance_query_policy':'observed-dom-20261021-v1','governance_calendar_policy':'date-item-div-v3-single'}
  elif c['op']=='tree':value=copy.deepcopy(self.current['tree'])
  elif c['op']=='click':
   node=next(n for n in g.nodes(self.current['tree']) if n['selector']==c['locator']['value']);self.calls.append(copy.deepcopy(c));name=g.text(node);value={'version':d.nav.VERSION,'kind':c['kind'],'clicked':copy.deepcopy(node)}
   if urlpath(self.current)==g.CENTER and name=='2':self.current=self.center_two
   elif name=='违规记录':
    self.current=copy.deepcopy(self.record_one)
    if self.mismatch_records:g.date_input(self.current['tree'])['attributes']['value']='2026-09-21 ~ 2026-10-21'
   elif urlpath(self.current)==g.RECORDS and name=='2':self.current=self.record_two
   else:raise AssertionError(('unexpected click',name))
   if self.lose==name:raise RuntimeError('lost reply')
  else:raise AssertionError(c)
  return {'ok':True,'result':value}
 def runner(self):
  with patch.object(rr,'source_inputs',return_value=self.source),patch.object(rr,'locations',return_value=(self.live_parent,self.folder)):r=rr.Runner(self.manifest,self.folder/'state.json',self.invoke)
  def child(route):
   owner=self
   class FakeFilter:
    file=owner.folder/('center-range.json' if route==g.CENTER else 'records-range.json')
    s={'phase':'open-date','calls':[]}
    def step(childself):
     owner.filter_calls.append(route);owner.current=owner.center_one if route==g.CENTER else owner.record_one;path=owner.folder/('fake-center-after.json' if route==g.CENTER else 'fake-records-after.json')
     if not path.exists():d.exclusive(path,owner.current)
     childself.s={'phase':'profile-required' if route==g.CENTER else 'range-restored','calls':[],'last_observation':d.ref(path)}
    def save(childself):d.nav.write_json(childself.file,childself.s)
   return FakeFilter()
  r.child=child;return r
 def finish(self,r):
  for _ in range(15):
   r.step();r.save()
   if r.s['phase']=='normal-restored-ready':return r
  self.fail(r.s['phase'])
 def test_actual_parent_chain_is_readonly_validated(self):
  m,v,parent,row=rr.source_inputs(self.manifest);self.assertEqual(parent['cursor'],12);self.assertEqual(row['notice_id'],'ZS202610174748574044');self.assertEqual(v['job']['end_exclusive'],'2026-10-21')
 def test_complete_simulated_recovery_restores_original_page_and_no_detail_open(self):
  r=self.finish(self.runner());self.assertEqual(r.s['restored_page'],{k:v for k,v in self.v['query']['pages'][1].items() if k!='observation'});self.assertEqual([c['kind'] for c in self.calls],['navigation']*3);self.assertEqual(self.filter_calls,[g.CENTER]);self.assertEqual(len(r.s['center_pages']),2);snapshot=r.s['filter_final_snapshots']['center-range'];frozen=d.document(snapshot);d.nav.write_json(self.folder/'center-range.json',{'later_read':True});self.assertEqual(d.document(snapshot),frozen);self.assertFalse(r.s['detail_cursor_advanced']);self.assertEqual(self.parent['cursor'],12);before=len(self.calls);r.step();self.assertEqual(len(self.calls),before)
 def test_records_range_mismatch_uses_separate_filter_and_no_automatic_all_pages(self):
  self.mismatch_records=True;r=self.finish(self.runner());self.assertEqual(self.filter_calls,[g.CENTER,g.RECORDS]);self.assertEqual(len([c for c in self.calls if url_selector(c).endswith('li:nth-of-type(3)')]),2);self.assertEqual(r.s['restored_page']['page'],2)
 def test_lost_center_pager_reply_only_reads_never_reclicks(self):
  r=self.runner();r.step();self.lose='2'
  with self.assertRaisesRegex(RuntimeError,'lost reply'):r.step()
  self.assertEqual(len(self.calls),1);r.step();r.step();self.assertEqual(len(self.calls),1);self.assertTrue(r.s['hold']);self.assertIn('unknown-intent',r.s['waiting_for'])
 def test_unknown_child_prevents_new_actions_and_new_manifest_cannot_bypass(self):
  r=self.runner();d.nav.write_json(self.folder/'records-range.json',{'calls':[{'state':'unknown'}]});r.step();self.assertTrue(r.s['hold']);self.assertEqual(self.calls,[])
  changed=copy.deepcopy(self.manifest);changed['parent_state']['sha256']='0'*64
  with patch.object(rr,'source_inputs',return_value=self.source),patch.object(rr,'locations',return_value=(self.live_parent,self.folder)),self.assertRaisesRegex(ValueError,'original-manifest-required|live-parent-changed'):rr.Runner(changed,r.file,self.invoke)
 def test_live_parent_new_unknown_stops_before_any_ui(self):
  r=self.runner();changed=copy.deepcopy(self.parent);changed['calls'].append({'state':'unknown'});d.nav.write_json(self.live_parent,changed);requests=[];original=r.invoke
  def invoke(command):requests.append(command);return original(command)
  r.invoke=invoke
  with self.assertRaisesRegex(ValueError,'live-parent-changed'):r.step()
  self.assertEqual(requests,[]);self.assertEqual(self.calls,[])
 def test_copied_state_cannot_bypass_original_unknown(self):
  r=self.runner();r.s['calls'].append({'state':'unknown'});r.save();original=r.file.read_bytes();copied=self.folder/'elsewhere/rates-recovery';copied.mkdir(parents=True)
  with patch.object(rr,'source_inputs',return_value=self.source),patch.object(rr,'locations',return_value=(self.live_parent,self.folder)),self.assertRaisesRegex(ValueError,'canonical-state-required'):rr.Runner(self.manifest,copied/'state.json',self.invoke)
  self.assertEqual(r.file.read_bytes(),original);self.assertFalse((copied/'state.json').exists());self.assertEqual(self.calls,[])
 def test_copied_manifest_cli_refuses_before_runner_or_ui(self):
  import contextlib,io
  copied=self.folder/'copy/rates-recovery';copied.mkdir(parents=True);mp=copied/'manifest.json';d.exclusive(mp,self.manifest);output=io.StringIO()
  with patch.object(rr,'locations',return_value=(self.live_parent,self.folder)),patch.object(sys,'argv',['governance_rates_recovery.py','run','--manifest',str(mp)]),contextlib.redirect_stdout(output):code=rr.main()
  self.assertEqual(code,2);self.assertIn('canonical-manifest-required',output.getvalue());self.assertFalse((copied/'state.json').exists());self.assertEqual(self.calls,[])
 def test_window_change_stops_before_navigation(self):
  r=self.runner();self.current=copy.deepcopy(self.current);self.current['tab']['windowId']=123
  with self.assertRaisesRegex(ValueError,'window-changed'):r.step()
  self.assertEqual(self.calls,[])
 def test_records_collect_page_is_intercepted_without_click_next(self):
  self.current=self.record_one;r=rr.RangeRestore(self.v['job'],self.m['tab_id'],self.folder/'child.json',self.m['approved_version'],g.RECORDS,self.invoke,self.record_one['tab']['windowId']);r.s['phase']='collect-page';r.step();self.assertEqual(r.s['phase'],'range-restored');self.assertFalse(r.s['all_pages_read']);self.assertEqual(self.calls,[]);self.assertEqual(r.s['range_page']['page'],1)
 def test_unknown_records_filter_never_act(self):
  self.current=self.record_one;r=rr.RangeRestore(self.v['job'],self.m['tab_id'],self.folder/'child.json',self.m['approved_version'],g.RECORDS,self.invoke);r.s.update(phase='collect-page',calls=[{'state':'unknown'}]);r.step();self.assertEqual(self.calls,[]);self.assertEqual(r.s['waiting_for'],'original-unknown-intent-no-replay')

def urlpath(raw):return rr.urlsplit(raw['tab']['url']).path
def url_selector(c):return c['locator']['value']
if __name__=='__main__':unittest.main()
