"""Actual 0041..0045 stop-loss roundtrip, fake observer; no live state changes."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_stop_loss as sl,governance_capture as cap
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class RoundtripTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name);self.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());self.v=d.inputs(self.m);self.row=self.v['query']['rows'][9];self.original=DIR/'stop-loss-original-30d8686b9b10e2bfe54be6f0d3e5735aae4f1376b71de86ec826349f1aa683dc.json';self.s=json.loads(self.original.read_text());self.prefix=copy.deepcopy(self.s['details']);opening=self.s['calls'][-1]
  def raw(n):return d.ref(DIR/'state-evidence'/n)
  facts,command=sl.parse(d.document(raw('0043.json')),self.row,opening,self.v['job']);self.entry=copy.deepcopy(self.s['current']);self.entry.update(detail_observation=raw('0043.json'),facts=facts,return_command=command,before_return=raw('0044.json'),return_observation=raw('0045.json'),return_route={'origin':'https://life.douyin.com','path':d.g.RECORDS})
  stage={'schema':'stop-loss-readonly-stage-v1','original_state':d.ref(self.original),'original_observation':raw('0042.json'),'expected_state_sha256':d.nav.digest(self.original),'expected_observation_sha256':raw('0042.json')['sha256']};self.s.update(current=self.entry,stop_loss_stage=stage,phase='stop-loss-return-route-hold',last_observation=raw('0045.json'),hold=True,waiting_for='supervisor-review-observed-return-route')
  before=d.document(raw('0044.json'));clicked=next(n for n in d.g.nodes(before['tree']) if n['selector']==command['locator']['value']);self.s['calls'].append({'state':'confirmed','command':command,'before':raw('0044.json'),'result':{'kind':'navigation','version':d.nav.VERSION,'clicked':clicked}})
 def completed(self):
  entry=copy.deepcopy(self.entry);entry.update(state='complete',completion_kind='stop-loss-roundtrip-v1',stage_evidence=self.s['stop_loss_stage'],normal_after=self.entry['return_observation']);state=copy.deepcopy(self.s);state['details'].append(entry);state.update(cursor=10,current=None,phase='normal');return entry,state
 def test_actual_completed_verifier_preserves_first_nine_and_status_origin(self):
  entry,state=self.completed();facts=sl.verify_entry(entry,state,self.m,self.v,self.row);out=d.verify_completed(state,self.m,self.v,require_complete=False);self.assertEqual(len(out),10);self.assertEqual(state['details'][:9],self.prefix);self.assertEqual(facts['effective_statuses'],[])
 def test_capture_mapping_uses_table_status_without_fabricating_detail_state(self):
  entry,state=self.completed();mapped=cap.stop_loss_mapping(self.row,entry['facts'],entry,state=state,manifest=self.m,inputs=self.v);self.assertEqual(mapped['table_effectiveness_status'],'已结束');self.assertEqual(mapped['actions'],[self.row['disposal']]);self.assertEqual(mapped['action_details'][0]['status_basis'],'original-records-table');self.assertFalse(mapped['action_details'][0]['detail_status_observed']);self.assertEqual(mapped['disposal_literal_mapping']['method'],'exact-stop-loss-disposal-table-status-v1')
 def test_changed_facts_missing_return_normal_or_unconfirmed_return_refuses(self):
  for mode in ('detail_status','notice','before_return','normal_after','reply','unknown','duplicate','route'):
   entry,state=self.completed()
   if mode=='detail_status':entry['facts']['effective_statuses']=['已结束']
   elif mode=='notice':entry['facts']['object_id']='other'
   elif mode=='before_return':entry['before_return']=entry['normal_before']
   elif mode=='normal_after':entry['normal_after']=entry['detail_observation']
   elif mode=='reply':state['calls'][-1]['result']['clicked']['name']='其他'
   elif mode=='unknown':state['calls'][-1]['state']='unknown'
   elif mode=='duplicate':state['calls'].append(copy.deepcopy(state['calls'][-1]))
   else:entry['return_route']['path']='/unreviewed'
   with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):sl.verify_entry(entry,state,self.m,self.v,self.row)
 def runner(self):
  r=object.__new__(sl.Runner);r.manifest=self.m;r.v=self.v;r.job=self.v['job'];r.tab=995698279;r.file=self.folder/'state.json';r.s=copy.deepcopy(self.s);r.save();self.clicks=[]
  def observe():
   raw=d.document(self.entry['return_observation']);p=self.folder/'fresh.json';d.exclusive(p,raw);r.s['last_observation']=d.ref(p);r.s['observations'].append(d.ref(p));r.save();return raw['tree']
  r.observe=observe;r.request=lambda cmd:self.clicks.append(cmd);return r
 def test_finish_uses_only_fresh_observation_and_advances_exactly_one(self):
  r=self.runner();r.finish_roundtrip(d.nav.digest(r.file));self.assertEqual(r.s['cursor'],10);self.assertEqual(r.s['phase'],'normal');self.assertFalse(r.s.get('hold'));self.assertEqual(r.s['details'][:9],self.prefix);self.assertEqual(self.clicks,[]);self.assertNotIn('stop_loss_stage',r.s)
  with self.assertRaises(ValueError):r.finish_roundtrip(d.nav.digest(r.file))
 def test_finish_wrong_checkpoint_refuses_before_fresh_read(self):
  r=self.runner()
  with self.assertRaises(ValueError):r.finish_roundtrip('0'*64)
  self.assertFalse((self.folder/'fresh.json').exists());self.assertEqual(r.s['cursor'],9)
if __name__=='__main__':unittest.main()
