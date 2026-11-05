"""Synthetic same-dispatch repair/watchdog tests. No business or UI invocation."""
import copy,importlib.util,json,sys,unittest
from pathlib import Path
DIR=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location('formal_switch_read_director',DIR/'director.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
fixture_path=Path(__file__).resolve().parents[2]/'douyin-laike-operator/tests/switch_read_fixture.py'
spec=importlib.util.spec_from_file_location('formal_switch_read_fixture',fixture_path)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
m=f.m
class KnownSwitchReadReconciliationTests(f.RecoveryFixture):
 def director(self,repaired):
  path=str(self.file);doc=json.loads(self.file.read_bytes());old=copy.deepcopy(self.s);old.pop('last_error');prior=d.progress.extract(old,'daily_stats_operator',path)
  state={'test_target':'测试群请忽略','production_enabled':False,'complaint_submission_enabled':False,'index':0,'phase':'attention','day':'2026-10-22','dispatch_id':'dispatch0','dispatch_intent_at':'2026-10-22T09:00:00+00:00','dispatched_at':'2026-10-22T09:00:01+00:00','tool_receipt':{'ack':True},'queue':[{'role':'daily_stats_operator','workflow':'daily-comment-stats'}],'cursor':0,'events':[{'type':'dispatched','id':'dispatch0'},{'type':'semantic-progress-attention','dispatch_id':'dispatch0','at':'2026-10-22T10:00:02+00:00','error':'semantic-terminal-error'}],'attention_reason':'semantic-progress-unverified','semantic_progress_error':'semantic-terminal-error','journal':path,'semantic_progress':{'dispatch0':{path:prior}},'last_progress_at':'2026-10-22T09:00:01+00:00','attempt':0,'order':'unchanged','parent_clock':12}
  report={'kind':'supervisor-known-switch-read-reconciliation-v1','dispatch_id':'dispatch0','day':'2026-10-22','role':'daily_stats_operator','journal':m.ref(self.file),'original_binding':prior['binding'],'original_journal':m.document(repaired['proof'])['original_journal'],'worker_recovery':repaired['proof'],**{k:True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')}}
  reportpath=self.p/'repair.json';reportpath.write_bytes(m.encoded(report));return state,report,reportpath

 def test_same_dispatch_reconciliation_no_clock_or_progress_change(self):
  r=self.runrepair();s,report,p=self.director(r);old=copy.deepcopy(s);d.reconcile_running_intent(s,'dispatch0',p);self.assertEqual(s['phase'],'running')
  for k in ('dispatch_id','dispatch_intent_at','dispatched_at','tool_receipt','attempt','order','parent_clock','last_progress_at'):self.assertEqual(s[k],old[k])
  self.assertEqual(s['semantic_progress_error'],'semantic-terminal-error');self.assertFalse(s['events'][-1]['automatic_followup'])
  with self.assertRaises(ValueError):d.reconcile_running_intent(s,'dispatch0',p)

 def test_supervised_pause_is_not_business_progress_and_stall_resumes(self):
  from datetime import datetime,timedelta,timezone
  r=self.runrepair();s,report,p=self.director(r);end=datetime.now(timezone.utc);start=end-timedelta(seconds=1000);prior=start-timedelta(seconds=120)
  s['last_progress_at']=prior.isoformat();s['events'][-1]['at']=start.isoformat();s['dispatch_intent_at']=(prior-timedelta(seconds=20)).isoformat()
  # Fresh proof must also postdate original dispatch; wall clock is never changed.
  d.reconcile_running_intent(s,'dispatch0',p,now=end)
  self.assertEqual(s['last_progress_at'],prior.isoformat());self.assertEqual(s['parent_clock'],12)
  self.assertAlmostEqual(d.inspect(s,now=end)['journal_idle_seconds'],120,places=3)
  # Keep liveness fresh so the assertion isolates the progress watchdog.
  s['last_heartbeat']=(end+timedelta(seconds=181)).isoformat();out=d.inspect(s,now=end+timedelta(seconds=181));self.assertEqual(out['reason'],'journal-no-progress');self.assertAlmostEqual(out['journal_idle_seconds'],301,places=3)

 def test_pause_merge_and_invalid_interval_rejected(self):
  from datetime import datetime,timedelta,timezone
  r=self.runrepair();s,report,p=self.director(r);end=datetime.now(timezone.utc);d.reconcile_running_intent(s,'dispatch0',p,now=end)
  age=d.active_age(s,s['last_progress_at'],end);s['events'].append(copy.deepcopy(s['events'][-1]));self.assertEqual(d.active_age(s,s['last_progress_at'],end),age)
  s['events'][-1]['supervised_pause']['end']=(end+timedelta(seconds=1)).isoformat();s['events'][-1]['at']=s['events'][-1]['supervised_pause']['end']
  with self.assertRaisesRegex(ValueError,'pause-time'):d.active_age(s,s['last_progress_at'],end)

 def test_director_scope_ack_prefix_and_new_action_rejected(self):
  r=self.runrepair();s,report,p=self.director(r)
  for mode in ('scope','ack','prefix','quiescent','newaction'):
   with self.subTest(mode=mode):
    state=copy.deepcopy(s);rp=copy.deepcopy(report);original=self.file.read_bytes()
    if mode=='scope':rp['dispatch_id']='wrong'
    if mode=='ack':state['dispatched_at']=None
    if mode=='prefix':state['semantic_progress']['dispatch0'][str(self.file)]['confirmed_call_prefix']=['wrong']
    if mode=='quiescent':rp['browser_quiescent']=False
    if mode=='newaction':
     v=json.loads(original);v['calls'].append({'state':'confirmed','command':{'op':'hover'}});self.file.write_bytes(m.encoded(v));rp['journal']=m.ref(self.file)
    p.write_bytes(m.encoded(rp))
    with self.assertRaises(ValueError):d.reconcile_running_intent(state,'dispatch0',p)
    self.file.write_bytes(original)

if __name__=='__main__':unittest.main()
