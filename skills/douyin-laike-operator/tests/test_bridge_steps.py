"""CLI-only scheduling mocks: never initialize a bridge or native UI."""
import contextlib,importlib.util,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('bridge_steps_runtime',SCRIPTS/'bridge-workflow.py')
bw=importlib.util.module_from_spec(spec);spec.loader.exec_module(bw)
class FakeWorkflow:
    def __init__(self,transitions=()):
        self.s={'state':'running','phase':'account'};self.transitions=list(transitions);self.calls=0;self.saves=0
    def tick(self):
        self.calls+=1
        if self.transitions:
            value=self.transitions.pop(0)
            if isinstance(value,Exception):raise value
            self.s.update(value)
    def save(self):self.saves+=1
class StepTests(unittest.TestCase):
    def run_steps(self,w,steps=25,status=False):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):bw.run_steps(w,Path('/mock-only/journal.json'),steps,status)
        return [json.loads(line) for line in out.getvalue().splitlines()]
    def test_default_executes_one_tick_and_keeps_json_fields(self):
        w=FakeWorkflow();rows=self.run_steps(w,1)
        self.assertEqual(w.calls,1);self.assertEqual(rows[0]['step'],1)
        self.assertTrue({'state','phase','waiting_for','journal'}<=rows[0].keys())
    def test_continuous_same_instance_bounded_steps_all_outputs_flushed(self):
        w=FakeWorkflow()
        with patch('builtins.print') as output:bw.run_steps(w,Path('/mock-only/journal.json'),25)
        self.assertEqual(w.calls,25);self.assertEqual(output.call_count,25)
        self.assertTrue(all(call.kwargs.get('flush') is True for call in output.call_args_list))
        self.assertEqual([json.loads(call.args[0])['step'] for call in output.call_args_list],list(range(1,26)))
    def test_wait_stops_without_retry_then_single_step_explicitly_resumes(self):
        w=FakeWorkflow([{'waiting_for':'generated-export-record'}, {'waiting_for':None}])
        rows=self.run_steps(w);self.assertEqual(w.calls,1);self.assertEqual(len(rows),1)
        rows=self.run_steps(w);self.assertEqual(w.calls,1);self.assertEqual(rows[0]['step'],0)
        self.run_steps(w,1);self.assertEqual(w.calls,2);self.assertIsNone(w.s['waiting_for'])
    def test_reviewed_profile_validation_runs_in_code_without_manual_name_gate(self):
        for phase in ('reviewProfileRequired','calendarProfileRequired','exportProfileRequired','recordsProfileRequired','exportDialogProfileRequired'):
            with self.subTest(phase=phase):
                w=FakeWorkflow([{'phase':phase},{'phase':'next'},{'state':'complete'}]);self.run_steps(w)
                self.assertEqual(w.calls,3);self.assertEqual(w.s['phase'],'next')
                held=FakeWorkflow([{'phase':phase,'waiting_for':'unreviewed-profile'}])
                self.run_steps(held);self.run_steps(held);self.assertEqual(held.calls,1)
    def test_completion_or_failed_state_stop_immediately(self):
        for state in ('complete','failed'):
            w=FakeWorkflow([{'state':state,'phase':'done'}]);rows=self.run_steps(w)
            self.assertEqual(w.calls,1);self.assertEqual(len(rows),1)
            self.run_steps(w,1);self.assertEqual(w.calls,1)
    def test_error_persists_once_and_no_unknown_retry(self):
        w=FakeWorkflow([{'phase':'submitExport'},ValueError('unknown-do-not-replay'),{'phase':'done'}]);out=io.StringIO()
        with contextlib.redirect_stdout(out),self.assertRaisesRegex(ValueError,'unknown-do-not-replay'):
            bw.run_steps(w,Path('/mock-only/journal.json'),25)
        self.assertEqual(w.calls,2);self.assertEqual(w.saves,1)
        self.assertEqual(w.s['last_error']['code'],'unknown-do-not-replay')
        self.assertEqual(len(out.getvalue().splitlines()),1)
    def test_status_never_tick_even_with_steps(self):
        w=FakeWorkflow([AssertionError('must not execute')]);rows=self.run_steps(w,25,True)
        self.assertEqual(w.calls,0);self.assertEqual(w.saves,0);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['step'],0)
    def test_cli_parser_bounds_and_main_preserves_single_locked_workflow(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);order=root/'job.json';order.write_text(json.dumps({'workflow_path':str(root/'journal.json')}))
            args=['--work-order',str(order),'--tab-id','9']
            w=FakeWorkflow([{'phase':'next'},{'state':'complete'}])
            with patch.object(bw,'Workflow',return_value=w) as factory,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(bw.main(args+['--steps','25']),0)
            factory.assert_called_once();self.assertEqual(w.calls,2)
            for invalid in ('0','26','-1','one','1.5'):
                with self.subTest(invalid=invalid),contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:
                    bw.main(args+['--steps',invalid])
                self.assertEqual(error.exception.code,2)
    def test_main_error_json_and_status_does_not_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);order=root/'job.json';order.write_text(json.dumps({'workflow_path':str(root/'journal.json')}));args=['--work-order',str(order),'--tab-id','9','--steps','25']
            w=FakeWorkflow([TimeoutError('unknown outcome')]);out=io.StringIO()
            with patch.object(bw,'Workflow',return_value=w),contextlib.redirect_stdout(out):self.assertEqual(bw.main(args),1)
            self.assertEqual(w.calls,1);self.assertEqual(json.loads(out.getvalue())['error'],'unknown outcome')
            with patch.object(bw,'Workflow',return_value=w),contextlib.redirect_stdout(io.StringIO()):self.assertEqual(bw.main(args+['--status']),0)
            self.assertEqual(w.calls,1)
if __name__=='__main__':unittest.main()
