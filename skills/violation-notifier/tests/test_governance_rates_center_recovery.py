"""Actual rate notice no-effect return, one sidebar recovery, fake connector only."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_rates_stop_loss as rates
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);original=DIR/'rates-stop-loss-original-0a49399b2db7906fbbc1179f5207099be6ee2b40b0dbe5ea41dcb854f473986f.json';self.s=json.loads(original.read_text());row=self.v['query']['rows'][12];opening=self.s['calls'][-1]
  def ref(n):return d.ref(DIR/'state-evidence'/n)
  facts,command=rates.parse(d.document(ref('0060.json')),row,opening,self.v['job']);self.s['rates_stop_loss_stage']={'schema':'rates-stop-loss-readonly-stage-v1','original_state':d.ref(original),'expected_state_sha256':d.nav.digest(original),'original_observation':ref('0059.json'),'expected_observation_sha256':ref('0059.json')['sha256']};self.s['current'].update(detail_observation=ref('0060.json'),facts=facts,return_command=command,before_return=ref('0061.json'),return_observation=ref('0063.json'),return_route={'origin':'https://life.douyin.com','path':rates.PATH},return_enabled=False);target=next(n for n in d.g.nodes(d.document(ref('0061.json'))['tree']) if n['selector']==command['locator']['value']);self.s['calls'].append({'state':'confirmed','command':command,'before':ref('0061.json'),'result':{'kind':'navigation','version':d.nav.VERSION,'clicked':target}});self.s.update(phase='rates-stop-loss-return-route-hold',hold=True,last_observation=ref('0063.json'));self.raw=d.document(ref('0063.json'));self.center=json.loads((BASE/'profile-discovery-evidence/000-all-reasons.json').read_text());self.original_details=copy.deepcopy(self.s['details']);self.requests=[];self.lost=False;self.changed=False
 def runner(self):
  r=object.__new__(rates.Runner);r.manifest=self.m;r.v=self.v;r.job=self.v['job'];r.tab=995698279;r.file=self.folder/'state.json';r.s=copy.deepcopy(self.s);r.save()
  def observe():
   raw=self.center if self.changed else self.raw;p=self.folder/('fresh-'+str(len(r.s['observations']))+'.json');d.exclusive(p,raw);r.s['last_observation']=d.ref(p);r.s['observations'].append(d.ref(p));r.save();return raw['tree']
  def request(command):
   self.requests.append(command);self.changed=True
   if self.lost:raise RuntimeError('lost-sidebar-reply')
   target=next(n for n in d.g.nodes(self.raw['tree']) if n['selector']==command['locator']['value']);return {'kind':'navigation','version':d.nav.VERSION,'clicked':target}
  r.observe=observe;r.request=request;return r
 def test_single_sidebar_archives_original_and_stops_at_center_without_query(self):
  r=self.runner();original=r.file.read_bytes();sha=d.nav.digest(r.file);r.recover_center_once(sha);self.assertEqual(len(self.requests),1);self.assertEqual(r.s['phase'],'rates-center-recovery-route-hold');self.assertEqual(r.s['cursor'],12);self.assertEqual(r.s['details'],self.original_details);recovery=r.s['rates_center_recovery'];self.assertEqual(Path(recovery['original_state']['path']).read_bytes(),original);self.assertTrue(recovery['center_structure_verified']);self.assertEqual(recovery['original_arrow_effect'],'not-observed-same-route-and-facts');self.assertFalse(recovery['automatic_records_query'])
  with self.assertRaises(ValueError):r.recover_center_once(sha)
  r.inspect_center_recovery();self.assertEqual(len(self.requests),1)
 def test_unknown_sidebar_only_reconciles_read_no_second_click(self):
  r=self.runner();sha=d.nav.digest(r.file);self.lost=True
  with self.assertRaisesRegex(RuntimeError,'lost-sidebar'):r.recover_center_once(sha)
  self.assertEqual(r.s['phase'],'rates-center-recovery-navigated-unknown')
  with self.assertRaises(ValueError):r.recover_center_once(sha)
  r.inspect_center_recovery();self.assertEqual(len(self.requests),1);self.assertTrue(r.s['rates_center_recovery']['center_structure_verified'])
 def test_changed_hash_or_sidebar_structure_cannot_navigate(self):
  r=self.runner()
  with self.assertRaises(ValueError):r.recover_center_once('0'*64)
  next(n for n in d.g.nodes(self.raw['tree']) if n.get('attributes',{}).get('class')=='navi_violation_center src-components-AsideMenu-index-module__label--Pcplo--212e2')['attributes']['class']='different'
  with self.assertRaisesRegex(ValueError,'sidebar-not-unique'):r.recover_center_once(d.nav.digest(r.file))
  self.assertEqual(self.requests,[])
 def test_fresh_notice_change_rejected_before_sidebar_input(self):
  r=self.runner();node=next(n for n in d.g.nodes(self.raw['tree']) if n.get('attributes',{}).get('class')=='my-[8px] is__content-TWHNZz' and n.get('name','').startswith('建议您查看'));node['name']='fresh changed advice'
  with self.assertRaises(ValueError):r.recover_center_once(d.nav.digest(r.file))
  self.assertEqual(self.requests,[]);self.assertEqual(r.s['details'],self.original_details);self.assertEqual(r.s['cursor'],12)
 def test_unconfirmed_original_arrow_cannot_start_sidebar_recovery(self):
  r=self.runner();r.s['calls'][-1]['state']='unknown';r.save()
  with self.assertRaisesRegex(ValueError,'arrow-unconfirmed'):r.recover_center_once(d.nav.digest(r.file))
  self.assertEqual(self.requests,[])
if __name__=='__main__':unittest.main()
