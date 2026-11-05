"""Actual stop-loss DOM fixture, immutable inputs and fake read-only connector."""
import copy,json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_stop_loss as sl
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class StopLossTests(unittest.TestCase):
 def test_direct_cli_source_encoding_and_help(self):
  result=subprocess.run([sys.executable,str(HERE.parents[1]/"scripts/governance_stop_loss.py"),"--help"],capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stderr);self.assertIn("return-once",result.stdout)
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);self.raw=json.loads((DIR/'state-evidence/0042.json').read_text());self.before=json.loads((DIR/'state-evidence/0041.json').read_text());self.row=self.v['query']['rows'][9]
  # Saved original call is derived from the observed reply, not a new browser action.
  target=next(n for n in d.g.nodes(self.before['tree']) if n['selector']==self.row['detail']['locator']['value']);self.call={'state':'confirmed','before':d.ref(DIR/'state-evidence/0041.json'),'command':{**self.row['detail'],'tabId':995698279},'result':{'kind':'navigation','version':d.nav.VERSION,'clicked':target}}
 def test_actual_notice_exact_source_fields_and_only_public_improvement(self):
  facts,cmd=sl.parse(self.raw,self.row,self.call,self.v['job']);self.assertEqual(facts['notice_id'],'ZS202610174754837331');self.assertEqual(facts['notification_time'],'2026-10-17 20:59');self.assertEqual(facts['object_id'],'1878370263889955');self.assertEqual(facts['effective_statuses'],[]);self.assertFalse(facts['detail_effectiveness_status_observed']);self.assertEqual(facts['table_effectiveness_status'],'已结束');self.assertEqual(len(facts['public_recommendation_paragraphs']),2);self.assertNotIn('平台管控',facts['public_recommendation']);self.assertEqual(cmd['kind'],'navigation');self.assertTrue(cmd['locator']['value'].endswith('button:nth-of-type(2)'))
 def test_changed_source_identity_route_or_open_refuses(self):
  for mode in ('notice','store','product','date','route','query','opening','reply'):
   raw=copy.deepcopy(self.raw);row=copy.deepcopy(self.row);call=copy.deepcopy(self.call)
   if mode=='route':raw['tab']['url']=raw['tab']['url'].replace(sl.PATH,'/unreviewed')
   elif mode=='query':raw['tab']['url']+='&token=not-allowed'
   elif mode=='opening':call['state']='unknown'
   elif mode=='reply':call['result']['clicked']['attributes']['class']='different'
   elif mode=='notice':row['notice_id']='different'
   elif mode=='store':row['store_name']='different'
   elif mode=='product':row['object']='different'
   else:row['violation_date']='2026-10-18'
   with self.subTest(mode=mode),self.assertRaises(ValueError):sl.parse(raw,row,call,self.v['job'])
 def runner(self):
  r=object.__new__(sl.Runner);r.manifest=self.m;r.v=self.v;r.job=self.v['job'];r.tab=995698279;r.file=self.folder/'state.json';r.version=d.nav.VERSION;r.detail_policy_ready=False;r.frame_detail_policy_ready=False
  r.s={'manifest':self.m,'fingerprint':d.nav.tag(r.job),'cursor':0,'details':[],'phase':'read-detail','current':{'notice_id':self.row['notice_id'],'normal_before':self.call['before']},'calls':[self.call],'last_observation':d.ref(DIR/'state-evidence/0042.json'),'observations':[]};r.v=copy.deepcopy(self.v);r.v['query']['rows']=[self.row];r.save();self.requests=[];self.fail_return=False
  def observe():
   p=self.folder/('fresh-'+str(len(r.s['observations']))+'.json');d.exclusive(p,self.raw);ref=d.ref(p);r.s['observations'].append(ref);r.s['last_observation']=ref;r.stop_loss_policy_ready=True;r.save();return self.raw['tree']
  def request(c):
   self.requests.append(c)
   if self.fail_return:raise RuntimeError('lost-return-reply')
   target=next(n for n in d.g.nodes(self.raw['tree']) if n['selector']==c['locator']['value']);return {'kind':c['kind'],'version':d.nav.VERSION,'clicked':target}
  r.observe=observe;r.request=request;return r
 def stage(self,r):
  sha=d.nav.digest(r.file);r.stage(sha,r.s['last_observation']['sha256']);return sha
 def test_stage_only_archives_exact_original_and_no_click_or_cursor_advance(self):
  r=self.runner();original=r.file.read_bytes();sha=self.stage(r);self.assertEqual(d.document(r.s['stop_loss_stage']['original_state'])['phase'],'read-detail');self.assertEqual(Path(r.s['stop_loss_stage']['original_state']['path']).read_bytes(),original);self.assertEqual(r.s['phase'],'stop-loss-return-ready');self.assertEqual(r.s['cursor'],0);self.assertEqual(self.requests,[]);r.stage(sha,r.s['stop_loss_stage']['expected_observation_sha256']);self.assertEqual(self.requests,[])
 def test_wrong_original_hash_and_fresh_changed_page_never_action(self):
  r=self.runner()
  with self.assertRaises(ValueError):r.stage('0'*64,r.s['last_observation']['sha256'])
  old=r.observe
  def changed():
   old();self.raw['tab']['url']=self.raw['tab']['url'].replace(sl.PATH,'/changed');old()
  r.observe=changed
  with self.assertRaises(ValueError):self.stage(r)
  self.assertEqual(self.requests,[]);self.assertEqual(r.s['phase'],'stop-loss-staging')
 def test_single_return_then_only_observe_route_and_hold(self):
  r=self.runner();self.stage(r);r.return_once();self.assertEqual(len(self.requests),1);self.assertEqual(r.s['phase'],'stop-loss-return-route-hold');self.assertEqual(r.s['cursor'],0);self.assertEqual(len(r.s['details']),0)
  with self.assertRaises(ValueError):r.return_once()
  r.inspect_return();self.assertEqual(len(self.requests),1)
 def test_unknown_return_may_only_inspect_original_no_repeat(self):
  r=self.runner();self.stage(r);self.fail_return=True
  with self.assertRaisesRegex(RuntimeError,'lost-return'):r.return_once()
  self.assertEqual(r.s['phase'],'stop-loss-returned-unknown');self.assertEqual(r.s['calls'][-1]['state'],'unknown')
  with self.assertRaises(ValueError):r.return_once()
  r.inspect_return();self.assertEqual(len(self.requests),1);self.assertEqual(r.s['phase'],'stop-loss-return-route-hold')
if __name__=='__main__':unittest.main()
