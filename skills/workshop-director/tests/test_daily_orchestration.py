"""Isolated candidate. Synthetic source/client schemas, fake UI ports only."""
import sys,json,copy,importlib.util,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];SCRIPTS=ROOT/'skills/workshop-director/scripts'
sys.path.insert(0,str(SCRIPTS))
import daily_orchestration as w,coordinator as c,director as d
w.parent.FORMAL_CLI=ROOT/'skills/daily-comment-stats/scripts/daily_timed_run.py'
sys.path.insert(0,str(ROOT/'skills/workshop-director/tests'));sys.path.insert(0,str(ROOT/'skills/daily-comment-stats/tests'));sys.path.insert(0,str(ROOT/'skills/daily-comment-stats/scripts'))
import test_coordinator as coord_fixture
import test_daily_execution_launcher as parent_fixture
class DispatchTests(unittest.TestCase):
 def setUp(self):self.h=coord_fixture.CoordinatorTests();self.h.setUp();self.addCleanup(self.h.doCleanups)
 def test_formal_morning_binds_offer_order_and_only_parent_commands_before_dispatch(self):
  v=self.h.morning();x=v['daily_execution'];self.assertEqual(x['origin'],'fresh');self.assertEqual(x['business_journal_candidates'],[]);self.assertIn('unsupported',x['business_journal_source']);order=w.dispatch.validate(x['order'],self.h.dispatch);self.assertEqual(order['dispatch_id'],v['dispatch_id']);self.assertIn('daily_execution_launcher.py',x['commands']['start'][1]);self.assertEqual(x['commands']['start'][2],'start');self.assertTrue(x['advance_requires_explicit_tab_id']);self.assertIn('禁止直接flow',v['message']);self.assertEqual(d.read(self.h.dispatch/'state.json')['phase'],'dispatch-intent')
  for p,raw in self.h.original.items():self.assertEqual(Path(p).read_bytes(),raw)
  before=list((self.h.dispatch/'dispatch-orders').glob('*.json'));again=self.h.morning();self.assertEqual(again['action'],'inspect-original-run');self.assertEqual(list((self.h.dispatch/'dispatch-orders').glob('*.json')),before);self.assertNotIn('daily_execution',again)
 def test_resume_uses_pinned_original_order_and_unknown_cannot_issue_another(self):
  first=self.h.morning();s=d.read(self.h.dispatch/'state.json');s.update(phase='ready',attempt=1);d.atomic(self.h.dispatch/'state.json',s);next_offer=c.command(self.h.dispatch,'plan',project=self.h.project);new=w.dispatch.validate(next_offer['daily_execution']['order'],self.h.dispatch);self.assertEqual(new['origin'],'resume');self.assertEqual(new['resumed_from'],first['daily_execution']['order']);self.assertNotEqual(new['dispatch_id'],first['dispatch_id']);again=self.h.morning();self.assertEqual(again['action'],'inspect-original-run')
 def test_unowned_overlapping_legacy_plan_holds_before_any_followup(self):
  _,_,p=c.fixed_ledgers(self.h.project)[0];s=d.read(p)
  for val in s['companies'].values():val['planned_runs']={str(self.h.root/'legacy'):{'start':'2026-10-16','end':'2026-10-20'}}
  d.atomic(p,s)
  with self.assertRaisesRegex(ValueError,'existing-plan-use-resume'):self.h.morning()
  self.assertEqual(d.read(self.h.dispatch/'state.json')['phase'],'attention');self.assertEqual(self.h.morning()['action'],'inspect-original-run')
class CompletionTests(unittest.TestCase):
 def setUp(self):
  self.h=parent_fixture.ParentTests();self.h.setUp();self.addCleanup(self.h.doCleanups);self.h.h.clock.base=datetime.now(timezone.utc)-timedelta(hours=1);self.h.finish();self.f=self.h.h;self.order=w.dispatch.validate(self.f.order_ref,self.f.archive);self.parentpath=w.parent.location(self.f.order_ref)/'state.json';start=self.f.clock.base-timedelta(seconds=1)
  self.ds={'version':2,'phase':'running','day':self.order['day'],'dispatch_id':self.order['dispatch_id'],'index':0,'attempt':0,'test_target':d.TARGET,'production_enabled':False,'complaint_submission_enabled':False,'dispatch_intent_at':start.isoformat(),'dispatched_at':start.isoformat(),'events':[{'type':'dispatched','id':self.order['dispatch_id']}]};self.dp=self.f.archive/'state.json';d.atomic(self.dp,self.ds);self.out=self.f.root/'adapter/report.json'
 def adapt(self):return w.completion_report(w.t.ref(self.parentpath),w.t.ref(self.dp),self.out,clock=self.f.clock)
 def test_complete_actual_schema_replay_creates_immutable_current_dispatch_report_and_finish(self):
  report=self.adapt();value=w.t.pinned(report);self.assertEqual(value['dispatch_id'],self.order['dispatch_id']);self.assertTrue(value['source_client_replay_verified']);self.assertTrue(value['performance']['acceptance_pass']);self.assertTrue(value['evidence']);self.assertEqual(self.adapt(),report);w.verify_completion(report['path'],self.ds,clock=self.f.clock);d.finish(self.ds,self.order['dispatch_id'],report['path']);self.assertEqual(self.ds['index'],1)
 def test_coordinator_finish_mechanically_requires_and_replays_adapter(self):
  report=self.adapt();d.atomic(self.f.archive/'state.json',self.ds)
  with patch.object(c,'bind_config',return_value={'active_day':self.ds['day']}),patch.object(w.t,'Clock',return_value=self.f.clock):result=c.command(self.f.archive,'finish',dispatch_id=self.ds['dispatch_id'],report=report['path'])
  self.assertEqual(result['index'],1)
 def test_actual_resumed_parent_completion_is_functional_but_not_fresh_performance_pass(self):
  h=parent_fixture.ParentTests();h.setUp();self.addCleanup(h.doCleanups);f=h.h;f.clock.base=datetime.now(timezone.utc)-timedelta(hours=1);h.call('start');prior=f.order_ref;oldstate=json.loads((f.execution/'state.json').read_text());original=w.dispatch.validate(prior,f.archive);offer=w.t.pinned(original['offer']);offer['dispatch_id']=original['day']+':daily-comment-stats:1';offerref=f.pin(f.root/'new-offer.json',offer);f.order_ref=w.dispatch.archive(f.archive,offerref,original['company_config'],origin='resume',resumed_from=prior);f.execution=parent_fixture.role.location(f.order_ref['path']);f.clock.n=110;intent=f.clock.wall()-timedelta(seconds=1)
  with patch.object(f.ports,'init',return_value=json.loads((Path(oldstate['run_dir'])/'batch_receipt.json').read_text())):h.call('start')
  h.call('advance');h.call('advance');h.call('notify');order=w.dispatch.validate(f.order_ref,f.archive);ds=copy.deepcopy(self.ds);ds.update(dispatch_id=order['dispatch_id'],day=order['day'],dispatch_intent_at=intent.isoformat(),dispatched_at=intent.isoformat(),events=[{'type':'dispatched','id':order['dispatch_id']}]);dp=f.archive/'state.json';d.atomic(dp,ds);out=f.root/'adapter/report.json';report=w.completion_report(w.t.ref(w.parent.location(f.order_ref)/'state.json'),w.t.ref(dp),out,clock=f.clock);value=w.t.pinned(report);self.assertTrue(value['complete']);self.assertEqual(value['performance']['origin'],'resume');self.assertFalse(value['performance']['acceptance_pass']);self.assertFalse(value['performance']['full_workflow_measured']);w.verify_completion(report['path'],ds,clock=f.clock)
 def test_client_or_completion_tampering_prevents_adapter_or_finish(self):
  report=self.adapt();p=next(self.f.jobs.glob('*.json'));p.write_text('{}')
  with self.assertRaises(ValueError):w.verify_completion(report['path'],self.ds,clock=self.f.clock)
 def test_actual_source_workbook_tamper_blocks_report_without_ui(self):
  state=json.loads(self.parentpath.read_text());batch=w.t.pinned(state['completion_proof']['batch']);receipt=json.loads(Path(batch['companies'][0]['receipt']).read_text());Path(receipt['src_file']).write_bytes(b'tampered source')
  with self.assertRaises(ValueError):self.adapt()
  self.assertFalse(self.out.exists())
 def test_unknown_not_complete_wrong_dispatch_unacked_or_older_completion_rejected(self):
  original=self.dp.read_bytes()
  for mode in ('dispatch','unacked','time'):
   ds=copy.deepcopy(self.ds)
   if mode=='dispatch':ds['dispatch_id']+='-wrong'
   elif mode=='unacked':ds['events']=[]
   else:ds['dispatch_intent_at']=(self.f.clock.wall()+timedelta(seconds=1)).isoformat()
   d.atomic(self.dp,ds)
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.adapt()
   self.assertFalse(self.out.exists())
  self.dp.write_bytes(original);state=json.loads(self.parentpath.read_text());state['status']='attention';self.parentpath.write_text(json.dumps(state))
  with self.assertRaisesRegex(ValueError,'parent-not-complete'):self.adapt()
 def test_old_functional_report_cannot_replace_parent_adapter(self):
  p=self.f.root/'fake-old-functional.json';p.write_text(json.dumps({'live':True,'complete':True,'workflow':d.FLOWS[0]}))
  with self.assertRaisesRegex(ValueError,'adapter-report-required'):w.verify_completion(p,self.ds,clock=self.f.clock)
 def test_resume_completion_never_claims_fresh_30_second_acceptance(self):
  # The formal parent enforces origin semantics; even a complete resumed run
  # cannot override immutable original entry fields by relabeling it fresh.
  state=json.loads(self.parentpath.read_text());state['origin']='resume';self.parentpath.write_text(json.dumps(state))
  with self.assertRaisesRegex(ValueError,'original-entry-changed'):self.adapt()
if __name__=='__main__':unittest.main()
