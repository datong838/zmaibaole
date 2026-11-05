"""Offline parent timing tests. UI ports are fake; real children are synthetic."""
import copy,json,subprocess,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
SCRIPT=Path(__file__).resolve().parents[1]/'scripts'
PROJECT=SCRIPT.parents[2]
sys.path.insert(0,str(SCRIPT));sys.path.insert(0,str(PROJECT/'skills/daily-comment-stats/tests'));sys.path.insert(0,str(PROJECT/'skills/daily-comment-stats/scripts'))
import daily_execution_launcher as outer
import execution_timing as t
import daily_timed_run as role
import test_daily_timed_run as fixtures

class ParentTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.TimedRunTests();self.h.setUp();self.addCleanup(self.h.doCleanups);self.h.order();self.calls=[];self.first_delay=1
    def runner(self,argv):
        self.calls.append(argv);verb=argv[2];h=self.h;h.clock.n+=self.first_delay if verb=='start' else 1
        if verb=='start':value=role.start(h.order_ref,h.archive,mode='acceptance',clock=h.clock,ports=h.ports)
        elif verb=='advance':value=role.advance(h.order_ref,h.archive,995698279,clock=h.clock,ports=h.ports)
        else:value=role.notify(h.order_ref,h.archive,steps=100,clock=h.clock,ports=h.ports)
        h.clock.n+=1 # Child teardown/stdout/exit after its inner measurement.
        return subprocess.CompletedProcess(argv,0,json.dumps(value),'')
    def call(self,verb,**kw):return outer.execute(self.h.order_ref,self.h.archive,verb,mode='acceptance',tab_id=995698279,steps=100,clock=self.h.clock,runner=kw.pop('runner',self.runner),**kw)
    def finish(self):
        self.call('start');self.h.clock.n+=3;self.call('advance');self.h.clock.n+=4;self.call('advance');return self.call('notify')
    def test_whole_parent_interval_includes_launch_gap_handoff_wait_and_child_exit(self):
        value=self.finish();self.assertTrue(value['acceptance_pass']);self.assertTrue(value['inner_timing_is_diagnostic_only']);s=json.loads((outer.location(self.h.order_ref)/'state.json').read_text());inner=json.loads((self.h.execution/'timing.json').read_text());self.assertEqual(s['start_monotonic'],100);self.assertGreater(inner['start_monotonic'],100);self.assertGreater(s['end_monotonic'],inner['end_monotonic']);self.assertEqual([x['verb'] for x in s['calls']],['start','advance','advance','notify']);self.assertTrue(all(x['state']=='returned' for x in s['calls']));self.assertEqual(value['elapsed_seconds'],self.h.clock.n-100)
        before=len(self.calls);self.assertTrue(outer.status(self.h.order_ref,self.h.archive,clock=self.h.clock)['acceptance_pass']);self.call('notify');self.assertEqual(len(self.calls),before)
    def test_inner_pass_does_not_override_outer_overdeadline_and_no_cancel(self):
        self.first_delay=31;r=self.finish();inner=json.loads((self.h.execution/'timing.json').read_text());self.assertTrue(inner['acceptance_pass']);self.assertFalse(r['acceptance_pass']);self.assertTrue(r['deadline_exceeded']);self.assertEqual(r['status'],'complete');self.assertEqual(self.h.ports.actual_sends,6)
    def test_duplicate_start_keeps_original_clock_and_does_not_launch(self):
        self.call('start');raw=(outer.location(self.h.order_ref)/'state.json').read_bytes();self.h.clock.n+=6;r=self.call('start');self.assertEqual(len(self.calls),1);self.assertEqual((outer.location(self.h.order_ref)/'state.json').read_bytes(),raw);self.assertEqual(r['elapsed_seconds'],self.h.clock.n-100)
    def test_unknown_launch_has_no_replay_no_new_verb_and_no_false_pass(self):
        def lost(argv):self.calls.append(argv);raise OSError('synthetic parent lost wait result')
        with self.assertRaises(OSError):self.call('start',runner=lost)
        r=self.call('start');self.assertEqual(r['status'],'attention');self.call('advance');self.assertEqual(len(self.calls),1);self.assertTrue(outer.status(self.h.order_ref,self.h.archive,clock=self.h.clock)['unresolved_child']);self.assertFalse(r['acceptance_pass'])
    def test_preexisting_inner_run_cannot_be_adopted_as_new_parent_measurement(self):
        role.start(self.h.order_ref,self.h.archive,mode='acceptance',clock=self.h.clock,ports=self.h.ports)
        with self.assertRaisesRegex(ValueError,'inner-preexists'):self.call('start')
        self.assertEqual(self.calls,[])
    def test_boot_change_scope_tamper_and_client_mutation_rejected(self):
        self.finish();p=next(self.h.jobs.glob('*.json'));p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'evidence-changed'):outer.status(self.h.order_ref,self.h.archive,clock=self.h.clock)
    def test_clock_rollback_and_boot_change_rejected_before_child(self):
        self.call('start');count=len(self.calls);self.h.clock.n=90
        with self.assertRaisesRegex(ValueError,'monotonic-invalid'):self.call('advance')
        self.h.clock.n=110
        with patch.object(self.h.clock,'boot',return_value='different-boot'),self.assertRaisesRegex(ValueError,'boot-changed'):self.call('advance')
        self.assertEqual(len(self.calls),count)
    def test_zero_data_keeps_separate_result_no_send_success(self):
        # Rebuild original synthetic artifacts in a fresh test fixture.
        self.h.zero={r['company'] for r in self.h.rows};r=self.finish();self.assertEqual(r['outcome'],'no-data-complete');self.assertFalse(r['acceptance_pass']);self.assertEqual(self.h.ports.actual_sends,0)
    def test_known_exit_receipt_crash_gap_recovered_readonly_without_second_notify(self):
        self.finish();root=outer.location(self.h.order_ref);p=root/'state.json';s=json.loads(p.read_text());s['status']='attention';s.pop('end_monotonic');s.pop('completion_proof');s.pop('outcome');s['acceptance_pass']=False;s['calls'][-1].pop('result');s['calls'][-1]['state']='unknown';p.write_text(json.dumps(s));count=len(self.calls);r=self.call('notify');self.assertEqual(r['status'],'complete');self.assertEqual(len(self.calls),count)

    def test_original_start_and_final_elapsed_cannot_be_changed_in_mutable_state(self):
        self.call('start');p=outer.location(self.h.order_ref)/'state.json';original=p.read_bytes();state=json.loads(original);state['start_monotonic']+=.01;p.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'original-entry-changed'):self.call('advance')
        p.write_bytes(original);self.call('advance');self.call('advance');self.call('notify');state=json.loads(p.read_text());state['end_monotonic']-=.01;p.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'completion-record-changed'):outer.status(self.h.order_ref,self.h.archive,clock=self.h.clock)

    def test_completed_source_cannot_hide_an_unresolved_earlier_launch(self):
        self.finish();p=outer.location(self.h.order_ref)/'state.json';state=json.loads(p.read_text());first=state['calls'][0];Path(first.pop('result')['path']).unlink();first['state']='unknown';p.write_text(json.dumps(state))
        with self.assertRaisesRegex(ValueError,'unresolved-child'):outer.status(self.h.order_ref,self.h.archive,clock=self.h.clock)

class RealChildBoundaryTests(unittest.TestCase):
    def test_real_system_clock_spans_two_synthetic_children_and_controlled_startup_delay(self):
        h=fixtures.TimedRunTests();h.setUp();self.addCleanup(h.doCleanups);h.order();clock=t.Clock();calls=[]
        # This child only creates synthetic timing/role metadata in TemporaryDirectory.
        # It never imports the daily business flow, accesses a browser or sends.
        source='''import sys,time,json\nfrom pathlib import Path\ntime.sleep(.12)\nsys.path.insert(0,sys.argv[1])\nimport execution_timing as t,daily_dispatch_order as d\nr=json.loads(sys.argv[2]);root=Path(r['path']).parent.parent/'daily-executions'/Path(r['path']).stem\nif sys.argv[4]=='start':\n t.start_from_order(root/'timing.json','daily-'+Path(r['path']).stem,r,lambda x:d.validate(x,sys.argv[3]),mode='acceptance')\n t.save(root/'state.json',{'order':r,'scope_sha256':d.validate(r,sys.argv[3])['scope_sha256'],'phase':'acquisition','run_dir':str(root/'synthetic-only')})\nc=t.Clock();print(json.dumps({'phase':'acquisition','timing':t.view(t.load(root/'timing.json',c),c)}))'''
        def runner(argv):
            calls.append(argv);return subprocess.run([sys.executable,'-I','-B','-c',source,str(SCRIPT),json.dumps(h.order_ref),str(h.archive),argv[2]],capture_output=True,text=True)
        outer.execute(h.order_ref,h.archive,'start',mode='acceptance',clock=clock,runner=runner);time.sleep(.08);r=outer.execute(h.order_ref,h.archive,'advance',mode='acceptance',tab_id=995698279,clock=clock,runner=runner);self.assertEqual(len(calls),2);self.assertGreaterEqual(r['elapsed_seconds'],.32);self.assertFalse(r['acceptance_pass']);s=json.loads((outer.location(h.order_ref)/'state.json').read_text());inner=json.loads((h.execution/'timing.json').read_text());self.assertGreaterEqual(inner['start_monotonic']-s['start_monotonic'],.12);self.assertGreaterEqual(s['calls'][1]['launch_monotonic']-s['calls'][0]['launch_monotonic'],.20)
        self.metrics={'evidence_kind':'synthetic subprocesses only; no business CLI/UI/network','clock_contract':r['clock_contract'],'child_count':len(calls),'controlled_child_delay_seconds_each':.12,'controlled_between_cli_delay_seconds':.08,'parent_elapsed_seconds':r['elapsed_seconds'],'first_child_pre_inner_seconds':inner['start_monotonic']-s['start_monotonic'],'between_child_launches_seconds':s['calls'][1]['launch_monotonic']-s['calls'][0]['launch_monotonic'],'acceptance_pass':r['acceptance_pass'],'complete_business_measured':False}
        subprocess_help=subprocess.run([sys.executable,'-I','-B',outer.__file__,'--help'],capture_output=True,text=True);self.assertEqual(subprocess_help.returncode,0,subprocess_help.stderr)

if __name__=='__main__':unittest.main()
