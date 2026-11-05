"""Offline dispatch fixtures. No operators, automation, UI or real ledgers."""
import copy,importlib.util,json,multiprocessing,sys,unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import coordinator as c
import director as d
import test_director as old

def fixture_finish(*args,**kwargs):
    # These tests isolate scheduling with synthetic completion booleans. The
    # real parent/source/client adapter is exercised in test_daily_orchestration.
    from unittest.mock import patch
    import daily_orchestration,role_execution_orchestration
    # Scheduling fixtures intentionally do not claim a real role source/client proof.
    with patch.object(daily_orchestration,'verify_completion'),patch.object(role_execution_orchestration,'verify_completion'):
        return c.command(*args,**kwargs)

def race(root,acceptance,project,queue,event):
    event.wait()
    try:queue.put(c.morning(root,acceptance,datetime.fromisoformat('2026-10-21T08:30:00+08:00'),project).get('action'))
    except BlockingIOError:queue.put('lock-busy')
class CoordinatorTests(unittest.TestCase):
 def setUp(self):
    old.DirectorTest.setUp(self);self.dispatch=self.root/'dispatch';self.project=self.root/'project';self.acceptance_file=self.root/'acceptance-index.json';d.atomic(self.acceptance_file,self.acceptance)
    for flow,company,path in c.fixed_ledgers(self.project):
        value={'next_start':'2026-10-16','covered_through':None,'batches':{'original-job':{'closed_at':None}},'tasks':{'original-task':{'status':'draft'}}}
        data={'version':1,'company':company,**value} if company else {'version':1,'companies':{name:copy.deepcopy(value) for name in c.COMPANIES}}
        d.atomic(path,data)
    self.original={str(p):p.read_bytes() for _,_,p in c.fixed_ledgers(self.project)}
 def morning(self,at='2026-10-21T08:30:00+08:00'):return c.morning(self.dispatch,self.acceptance_file,datetime.fromisoformat(at),self.project)
 def finish_day(self):
    # This helper tests day/lease transitions only. Real violation binding is
    # separately exercised with canonical ledgers in test_role_execution_bind.
    from unittest.mock import patch
    import role_execution_orchestration
    with patch.object(role_execution_orchestration,'bind',side_effect=lambda root,state,offer:offer):
        self.scheduling_fixture_finish_day()
 def scheduling_fixture_finish_day(self):
    while True:
        s=d.read(self.dispatch/'state.json')
        if d.current(s).get('action')=='done':return
        offer=c.command(self.dispatch,'plan',project=self.project);key=offer['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='mock receipt',project=self.project);s=d.read(self.dispatch/'state.json');flow=d.current(s)['workflow'];p=self.root/(s['day']+'-'+flow+'-complete.json');data=d.read(self.acceptance[flow]);data.update(dispatch_id=key,day=s['day'],role=d.current(s)['role'],completed_at=d.stamp());d.atomic(p,data);fixture_finish(self.dispatch,'finish',dispatch_id=key,report=p,project=self.project)
 def test_gate_requires_three_actual_acceptances_and_fixed_ledgers(self):
    p=Path(self.acceptance[d.FLOWS[2]]);data=d.read(p);data['fixture']=True;d.atomic(p,data)
    with self.assertRaisesRegex(ValueError,'real-completion'):self.morning()
    self.assertFalse((self.dispatch/'state.json').exists())
 def test_repeated_morning_persists_one_intent_and_hashes_fixed_progress(self):
    first=self.morning();second=self.morning();self.assertEqual(first['action'],'dispatch');self.assertEqual(second['action'],'inspect-original-run');self.assertEqual(first['dispatch_id'],second['dispatch_id']);state=d.read(self.dispatch/'state.json');self.assertEqual(len(state['ledger_snapshots']),5)
    for e in state['ledger_snapshots']:
        self.assertEqual(c.sha(Path(e['snapshot']['path']).read_bytes()),e['snapshot']['sha256']);self.assertTrue(all(v['next_start']=='2026-10-16' for v in e['progress'].values()))
    self.assertEqual(sum(e['type']=='dispatch-intent' for e in state['events']),1)
    for path,raw in self.original.items():self.assertEqual(Path(path).read_bytes(),raw)
 def test_cross_midnight_shanghai_old_unacked_day_keeps_original_dispatch(self):
    first=self.morning('2026-10-20T16:01:00+00:00');second=self.morning('2026-10-21T16:01:00+00:00');self.assertEqual(first['active_day'],'2026-10-21');self.assertEqual(second['requested_day'],'2026-10-22');self.assertEqual(second['active_day'],'2026-10-21');self.assertTrue(second['resuming_old_day']);self.assertEqual(second['dispatch_id'],first['dispatch_id']);self.assertFalse((self.dispatch/'days').exists())
 def test_old_running_and_attention_are_not_redispatched_on_new_day(self):
    first=self.morning();c.command(self.dispatch,'ack',dispatch_id=first['dispatch_id'],tool_receipt='mock receipt');second=self.morning('2026-10-22T08:30:00+08:00');self.assertEqual(second['phase'],'running');self.assertEqual(second['action'],'inspect-original-run');self.assertEqual(second['dispatch_id'],first['dispatch_id'])
 def test_completed_day_rollover_archives_exact_old_state_and_starts_current_day(self):
    self.morning();self.finish_day();oldraw=(self.dispatch/'state.json').read_bytes();offer=self.morning('2026-10-22T08:30:00+08:00');self.assertEqual(offer['active_day'],'2026-10-22');self.assertEqual(offer['action'],'dispatch');self.assertEqual((self.dispatch/'days/2026-10-21/state.json').read_bytes(),oldraw);self.assertEqual(len(d.read(self.dispatch/'coordinator.json')['archives']),1)
    again=self.morning('2026-10-22T08:31:00+08:00');self.assertEqual(again['action'],'inspect-original-run');self.assertEqual(len(d.read(self.dispatch/'coordinator.json')['archives']),1)
 def test_new_role_dispatch_reads_updated_independent_progress_without_mutating_it(self):
    self.morning();s=d.read(self.dispatch/'state.json');key=s['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='mock receipt');s=d.read(self.dispatch/'state.json');p=self.root/'finish-first.json';data=d.read(self.acceptance[d.FLOWS[0]]);data.update(dispatch_id=key,day=s['day'],role=d.ROLES[0],completed_at=d.stamp());d.atomic(p,data);fixture_finish(self.dispatch,'finish',dispatch_id=key,report=p)
    flow,company,path=c.fixed_ledgers(self.project)[1];doc=d.read(path);doc['next_start']='2026-10-20';d.atomic(path,doc);raw=path.read_bytes();offer=c.command(self.dispatch,'plan',project=self.project);entry=next(e for e in offer['ledger_snapshots'] if e['company']==company);self.assertEqual(entry['progress'][company]['next_start'],'2026-10-20');self.assertEqual(path.read_bytes(),raw)
 def test_concurrent_morning_can_offer_only_one_dispatch(self):
    ctx=multiprocessing.get_context('fork');q=ctx.Queue();event=ctx.Event();ps=[ctx.Process(target=race,args=(self.dispatch,self.acceptance_file,self.project,q,event)) for _ in range(2)]
    for p in ps:p.start()
    event.set()
    for p in ps:p.join(5);self.assertEqual(p.exitcode,0)
    outcomes=[q.get(timeout=2) for _ in ps];self.assertEqual(outcomes.count('dispatch'),1);self.assertTrue(all(x in ('dispatch','inspect-original-run','lock-busy') for x in outcomes));s=d.read(self.dispatch/'state.json');self.assertEqual(sum(e['type']=='dispatch-intent' for e in s['events']),1)
 def test_archive_cannot_be_used_as_independent_coordinator_root(self):
    self.morning();self.finish_day();self.morning('2026-10-22T08:30:00+08:00')
    with self.assertRaisesRegex(ValueError,'cannot-use-day-archive'):c.morning(self.dispatch/'days/2026-10-21',self.acceptance_file,datetime.fromisoformat('2026-10-22T08:30:00+08:00'),self.project)
 def test_rollover_crash_retains_old_archive_and_recovers_current_pointer(self):
    from unittest.mock import patch
    self.morning();self.finish_day();real=d.atomic
    def fail_pointer(path,value):
        if Path(path).name=='coordinator.json' and value.get('active_day')=='2026-10-22':raise OSError('synthetic crash before pointer')
        return real(path,value)
    with patch.object(d,'atomic',side_effect=fail_pointer),self.assertRaises(OSError):self.morning('2026-10-22T08:30:00+08:00')
    self.assertEqual(d.read(self.dispatch/'state.json')['day'],'2026-10-22');self.assertTrue((self.dispatch/'days/2026-10-21/state.json').exists());offer=self.morning('2026-10-22T08:31:00+08:00');self.assertEqual(offer['action'],'dispatch');config=d.read(self.dispatch/'coordinator.json');self.assertEqual(config['active_day'],'2026-10-22');self.assertEqual(len(config['archives']),1)
 def test_cli_disallows_alternate_roots_and_legacy_bypass_of_owned_root(self):
    import subprocess
    path=Path(c.__file__);result=subprocess.run([sys.executable,str(path),'--root',str(self.root/'alternate'),'morning','--acceptance',str(self.acceptance_file)],capture_output=True,text=True);self.assertNotEqual(result.returncode,0);self.assertIn('fixed-global-root',result.stdout);self.assertFalse((self.root/'alternate').exists())
    self.morning();result=subprocess.run([sys.executable,str(Path(d.__file__)),'--root',str(self.dispatch),'plan'],capture_output=True,text=True);self.assertNotEqual(result.returncode,0);self.assertIn('use-global-coordinator',result.stdout)
 def test_changed_acceptance_blocks_new_offer_before_any_ledger_snapshot(self):
    self.morning();s=d.read(self.dispatch/'state.json');key=s['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='mock receipt')
    c.command(self.dispatch,'retry',dispatch_id=key,quiescent=True,repair_report=old.DirectorTest.repair(self,s))
    before=(self.dispatch/'state.json').read_bytes();p=Path(self.acceptance[d.FLOWS[-1]]);data=d.read(p);data['extra']='new but valid';d.atomic(p,data)
    from unittest.mock import patch
    with patch.object(c,'ledger_snapshot',side_effect=AssertionError('must gate before reading business ledger')),self.assertRaisesRegex(ValueError,'pinned-acceptance-changed'):
        c.command(self.dispatch,'plan',project=self.project)
    self.assertEqual((self.dispatch/'state.json').read_bytes(),before)
 def test_invalid_acceptance_does_not_block_running_readonly_recovery(self):
    offer=self.morning();key=offer['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='mock receipt');p=Path(self.acceptance[d.FLOWS[-1]]);data=d.read(p);data['complete']=False;d.atomic(p,data)
    self.assertEqual(c.command(self.dispatch,'status')['phase'],'running')
    self.assertEqual(c.command(self.dispatch,'heartbeat',dispatch_id=key,journal=self.journal)['phase'],'running')
    self.assertEqual(c.command(self.dispatch,'plan')['action'],'inspect-original-run')
    self.assertIn(c.command(self.dispatch,'inspect')['action'],('wait','supervisor-repair'))
 def test_changed_acceptance_preserves_unknown_dispatch_reconciliation(self):
    offer=self.morning();key=offer['dispatch_id'];p=Path(self.acceptance[d.FLOWS[-1]]);data=d.read(p);data['complete']=False;d.atomic(p,data)
    self.assertEqual(c.command(self.dispatch,'plan')['action'],'inspect-original-run')
    self.assertEqual(c.command(self.dispatch,'status')['phase'],'dispatch-intent')
    # A late actual tool receipt records the SAME original dispatch, not a new
    # offer. Evidence damage cannot erase the existing lease or force replay.
    c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='late original receipt')
    state=d.read(self.dispatch/'state.json');self.assertEqual(state['dispatch_id'],key)
    c.command(self.dispatch,'retry',dispatch_id=key,quiescent=True,repair_report=old.DirectorTest.repair(self,state))
    with self.assertRaisesRegex(ValueError,'real-completion'):c.command(self.dispatch,'plan',project=self.project)
    self.assertEqual(d.read(self.dispatch/'state.json')['phase'],'ready')
 def test_original_acceptance_pins_survive_next_day_and_legacy_configuration(self):
    self.morning();self.finish_day();before=(self.dispatch/'state.json').read_bytes();config=d.read(self.dispatch/'coordinator.json');config.pop('acceptance_proofs');d.atomic(self.dispatch/'coordinator.json',config)
    p=Path(self.acceptance[d.FLOWS[-1]]);data=d.read(p);data['extra']='changed after original';d.atomic(p,data)
    with self.assertRaisesRegex(ValueError,'pinned-acceptance-changed'):self.morning('2026-10-22T08:30:00+08:00')
    self.assertEqual((self.dispatch/'state.json').read_bytes(),before);self.assertFalse((self.dispatch/'days').exists())
 def test_coordinator_config_and_state_cannot_repin_each_other(self):
    self.morning();s=d.read(self.dispatch/'state.json');key=s['dispatch_id'];c.command(self.dispatch,'ack',dispatch_id=key,tool_receipt='mock receipt');c.command(self.dispatch,'retry',dispatch_id=key,quiescent=True,repair_report=old.DirectorTest.repair(self,s))
    state=d.read(self.dispatch/'state.json');state['acceptance'][d.FLOWS[0]]['sha256']='0'*64;d.atomic(self.dispatch/'state.json',state)
    with self.assertRaisesRegex(ValueError,'pin-conflict'):c.command(self.dispatch,'plan',project=self.project)
 def test_failed_archive_publication_leaves_no_partial_destination(self):
    from unittest.mock import patch
    destination=self.root/'immutable.json'
    with patch.object(c.os,'link',side_effect=OSError('publication interrupted')),self.assertRaises(OSError):
        c.immutable(destination,b'{"complete":true}')
    self.assertFalse(destination.exists())
    c.immutable(destination,b'{"complete":true}')
    self.assertEqual(destination.read_bytes(),b'{"complete":true}')
    with self.assertRaisesRegex(ValueError,'immutable-conflict'):
        c.immutable(destination,b'changed')
    self.assertEqual(destination.read_bytes(),b'{"complete":true}')
if __name__=='__main__':unittest.main()
