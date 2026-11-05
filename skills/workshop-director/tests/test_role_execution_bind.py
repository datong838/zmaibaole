"""Real candidate bind/order gates over synthetic canonical completed ledgers.
The reportkind has real production shape, but sources/clients are NOT claimed
real: the execution ProductionPorts guard performs that independent deep replay.
No run/Native/bridge/sender is invoked by this test.
"""
import copy,json,tempfile,unittest
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from unittest.mock import patch
import coordinator as c
import director as d
import role_execution_order as o
import role_execution_orchestration as role
import test_coordinator as scheduling
class BindTests(unittest.TestCase):
 def setUp(self):
  scheduling.CoordinatorTests.setUp(self);self.root=self.root.resolve();self.dispatch=self.dispatch.resolve();self.project=self.project.resolve();self.old_project=o.PROJECT;o.PROJECT=self.project;self.addCleanup(setattr,o,'PROJECT',self.old_project)
  c.morning(self.dispatch,self.acceptance_file,datetime.fromisoformat('2026-10-21T08:30:00+08:00'),self.project)
  state=d.read(self.dispatch/'state.json');state.update(phase='ready',index=2,attempt=0)
  self.report={'kind':'daily-director-completion-report-v1','workflow':'daily-comment-stats','day':state['day'],'complete':True,'live':True,'fixture':False,'test_target':'测试群请忽略','production_sent':False,'complaint_submitted':False,'note':'synthetic source/client payload intentionally absent; bind only, never executable proof'}
  self.rpath=self.root/'daily-completion-shape.json';d.atomic(self.rpath,self.report);state['events'].append({'type':'completed','dispatch_id':state['day']+':daily-comment-stats:0','report':o.ref(self.rpath),'at':d.stamp()});d.atomic(self.dispatch/'state.json',state)
  for i,name in enumerate(c.COMPANIES):
   root=self.project/'runtime/violation-notifier'/name
   ledger={'version':1,'company':name,'groupid':str(123+i),'mode':'development','browser_backend':'local-dom-bridge','next_start':'2026-10-20','covered_through':'2026-10-19','batches':{'2026-10-16_2026-10-20':{'start':'2026-10-16','end_exclusive':'2026-10-20','status':'zero_no_notification','total':0,'records':[],'analysis':[],'completed_at':'2026-10-20T10:00:00+08:00','send_jobs':{}}},'tasks':{},'identity':None}
   d.atomic(root/'state.json',ledger)
  self.ledger_bytes={str(self.project/'runtime/violation-notifier'/name/'state.json'):(self.project/'runtime/violation-notifier'/name/'state.json').read_bytes() for name in c.COMPANIES}
 def plan(self):return c.command(self.dispatch,'plan',project=self.project)
 def test_real_coordinator_bind_archives_canonical_two_company_order(self):
  result=self.plan();self.assertEqual(result['workflow'],o.FLOW);self.assertIn('role_execution',result);reference=result['role_execution']['order'];order=o.validate(reference);self.assertEqual(order['daily_completion'],o.ref(self.rpath));self.assertEqual([x['company'] for x in order['companies']],list(c.COMPANIES));self.assertEqual(len(order['scope']['company_ranges']),2);self.assertTrue(all(x['start']=='2026-10-20' and x['end_exclusive']=='2026-10-21' for x in order['companies']));self.assertTrue(all(x['root']==str(self.project/'runtime/violation-notifier'/x['company']) for x in order['companies']));self.assertTrue(all(x['batches']['2026-10-16_2026-10-20']['completed_at'] for x in [o.doc(y['ledger']) for y in order['companies']]))
  self.assertIn('role_execution_launcher.py',result['role_execution']['commands']['start'][1]);self.assertTrue(result['role_execution']['start_requires_explicit_tab_id_and_pid']);self.assertEqual(d.read(self.dispatch/'state.json')['phase'],'dispatch-intent')
  for path,raw in self.ledger_bytes.items():self.assertEqual(Path(path).read_bytes(),raw)
  # A second plan returns the original offer to inspect, not a fresh order.
  self.assertEqual(self.plan()['action'],'inspect-original-run');self.assertEqual(o.ref(reference['path']),reference)
 def test_actual_bind_rejects_nonformal_or_wrong_day_daily_report(self):
  # No mock of role.bind/o.build: source admission and order construction fail.
  for label,change in [('kind',{'kind':'old-functional-acceptance'}),('day',{'day':'2026-10-20'})]:
   with self.subTest(label=label):
    state=d.read(self.dispatch/'state.json');state.update(phase='ready',index=2);state['events']=[x for x in state['events'] if x.get('type') not in ('dispatch-intent','role-order-preparation-stopped','role-execution-bound')];r=self.root/('bad-'+label+'.json');d.atomic(r,{**self.report,**change});state['events']=[x for x in state['events'] if x.get('type')!='completed']+[{'type':'completed','dispatch_id':state['dispatch_id'],'report':o.ref(r),'at':d.stamp()}];d.atomic(self.dispatch/'state.json',state)
    with self.assertRaises(ValueError):self.plan()
    stopped=d.read(self.dispatch/'state.json');self.assertEqual(stopped['phase'],'attention');self.assertEqual(stopped['attention_reason'],'role-order-preparation-failed-before-dispatch');self.assertEqual(stopped['events'][-1]['dispatch_outcome'],'not-dispatched');self.assertFalse(any(x.get('type')=='dispatched' and x.get('id')==stopped['dispatch_id'] for x in stopped['events']))
 def test_changed_ledger_snapshot_or_wrong_canonical_origin_rejected(self):
  result=self.plan();order=o.doc(result['role_execution']['order']);offer=o.doc(order['offer']);changed=copy.deepcopy(offer);changed['ledger_snapshots'][0]['original_path']=str(self.root/'copied-ledger.json');bad=o.immutable(self.root/'copied-offer.json',changed)
  with self.assertRaisesRegex(ValueError,'canonical-company-ledger'):o.build(bad,order['daily_completion'])
  ref=offer['ledger_snapshots'][0]['snapshot'];Path(ref['path']).write_text('{}')
  with self.assertRaisesRegex(ValueError,'reference-changed'):o.validate(result['role_execution']['order'])
 def test_bind_failure_stops_before_dispatch_and_records_attention(self):
  with patch.object(role,'bind',side_effect=ValueError('synthetic-before-dispatch')) as called,self.assertRaisesRegex(ValueError,'synthetic-before-dispatch'):self.plan()
  self.assertEqual(called.call_count,1);s=d.read(self.dispatch/'state.json');self.assertEqual(s['phase'],'attention');event=s['events'][-1];self.assertEqual(event['type'],'role-order-preparation-stopped');self.assertEqual(event['dispatch_outcome'],'not-dispatched');self.assertFalse(any(x.get('type')=='dispatched' and x.get('id')==s['dispatch_id'] for x in s['events']))
 def test_coordinator_finish_refuses_wrong_kind_without_mocking_role_verifier(self):
  result=self.plan();key=result['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='synthetic followup receipt',project=self.project);s=d.read(self.dispatch/'state.json');p=self.root/'legacy-violation-complete.json';data=d.read(self.acceptance[o.FLOW]);data.update(dispatch_id=key,day=s['day'],role=o.ROLE,completed_at=d.stamp());d.atomic(p,data)
  before=(self.dispatch/'state.json').read_bytes()
  with self.assertRaisesRegex(ValueError,'current-role-parent-required'):c.command(self.dispatch,'finish',dispatch_id=key,report=p,project=self.project)
  self.assertEqual((self.dispatch/'state.json').read_bytes(),before)
if __name__=='__main__':unittest.main()
