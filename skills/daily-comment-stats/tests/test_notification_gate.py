"""CLI gate tests use only independent temporary work/progress/outbox roots."""
import io,json,sys,tempfile,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import flow,notification_backlog as backlog
from ds_calendar import compute
import test_notification_backlog as fixtures

class NotificationInitGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.work=self.root/'work';self.work.mkdir();self.run=self.work/'new'/'daily';self.progress=self.root/'progress.json'
    def cli(self,*extra):
        args=['flow.py','init','--today','2026-10-21','--outdir',str(self.run),'--progress-file',str(self.progress),'--notification-work-root',str(self.work),*extra]
        with patch.object(sys,'argv',args),redirect_stdout(io.StringIO()) as output:code=flow.main()
        return code,json.loads(output.getvalue())
    def test_pending_actual_batch_refuses_new_run_before_creation(self):
        fixture=fixtures.BacklogTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        self.work=fixture.root/'work';self.run=self.work/'new'/'daily'
        code,result=self.cli();self.assertEqual(code,3);self.assertEqual(result['action'],'resolve-notification-backlog');self.assertEqual(result['next_action'],'prepare');self.assertTrue(Path(result['outbox']).is_file());self.assertFalse((self.run/'batch_receipt.json').exists());self.assertFalse(self.progress.exists())
    def test_empty_test_work_root_allows_new_run_without_real_scan(self):
        code,result=self.cli();self.assertEqual(code,0);self.assertEqual(result['run_dir'],str(self.run.resolve()));self.assertEqual(result['backend'],'local-dom-bridge')
    def test_existing_identical_run_recovers_without_its_pending_notice_gate(self):
        dates=compute('2026-10-21');original=flow.init_run(dates,self.run,progress_file=self.progress);before=(self.run/'batch_receipt.json').read_bytes()
        with patch.object(backlog,'plan',side_effect=AssertionError('existing recovery must not gate')):
            code,result=self.cli()
        self.assertEqual(code,0);self.assertEqual(result['run_token'],original['run_token']);self.assertEqual((self.run/'batch_receipt.json').read_bytes(),before)
    def test_existing_different_configuration_conflict_not_recovery_bypass(self):
        flow.init_run(compute('2026-10-20'),self.run,progress_file=self.progress)
        with patch.object(backlog,'plan',side_effect=AssertionError('config rejects before gate')):code,result=self.cli()
        self.assertEqual(code,2);self.assertEqual(result['error']['code'],'run-conflict')
    def test_fixture_init_run_function_never_scans_notification_tree(self):
        with patch.object(backlog,'plan',side_effect=AssertionError('pure fixture function must not scan')):
            state=flow.init_run(compute('2026-10-21'),self.run,progress_file=self.progress)
        self.assertEqual(state['status'],'running')
    def test_rerun_does_not_bypass_pending_gate(self):
        flow.init_run(compute('2026-10-21'),self.run,progress_file=self.progress);before=(self.run/'batch_receipt.json').read_bytes()
        pending={'can_acquire_new_dates':False,'next':{'outbox':'fixture-outbox','next':{'action':'hold-unknown','job_path':'fixture-original-job'}}}
        with patch.object(backlog,'plan',return_value=pending):code,result=self.cli('--rerun')
        self.assertEqual(code,3);self.assertEqual(result['job_path'],'fixture-original-job');self.assertEqual((self.run/'batch_receipt.json').read_bytes(),before)
    def test_missing_work_root_is_configuration_failure_not_empty_backlog(self):
        self.work=self.root/'missing-work'
        code,result=self.cli();self.assertEqual(code,2);self.assertIn('notification-work-root-missing',result['error']['message']);self.assertFalse((self.run/'batch_receipt.json').exists())
if __name__=='__main__':unittest.main()
