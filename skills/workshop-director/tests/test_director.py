import importlib.util
import hashlib
import json
import tempfile
import subprocess
import sys
import copy
import unittest
from pathlib import Path
from datetime import datetime, timedelta, timezone

spec = importlib.util.spec_from_file_location('director', Path(__file__).parents[1] / 'scripts/director.py')
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)


class DirectorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.evidence = self.root / 'business.json'; self.evidence.write_text('{"real":true}')
        self.journal=self.root/'operator-workflow.json'
        d.atomic(self.journal,{'version':1,'backend':'local-dom-bridge','work_order_id':'fixed-fixture-job','fingerprint':'f'*64,'company':'测试公司','groupid':'123','date_range':{},'state':'running','phase':'downloadResult','calls':[],'checkpoints':[]})
        self.acceptance = {}
        for flow in d.FLOWS:
            p = self.root / (flow + '.json')
            p.write_text(json.dumps({'workflow': flow, 'live': True, 'complete': True,
                'test_target': d.TARGET, 'production_sent': False, 'complaint_submitted': False,
                'evidence': [{'path': str(self.evidence), 'sha256': hashlib.sha256(self.evidence.read_bytes()).hexdigest()}]}))
            self.acceptance[flow] = str(p)

    def state(self):
        return d.initialize('2026-10-21', self.acceptance)

    def completion(self,s,key,flow):
        p=self.root/(flow+'-completion.json');data=json.loads(Path(self.acceptance[flow]).read_text());data.update(dispatch_id=key,day=s['day'],role=d.current(s)['role'],completed_at=d.stamp());p.write_text(json.dumps(data));return str(p)

    def repair(self,s,**changes):
        p=self.root/'repair.json';data={'dispatch_id':s['dispatch_id'],'day':s['day'],'role':d.current(s)['role'],'operator_quiescent':True,'browser_quiescent':True,'wecom_quiescent':True,'original_work_orders_only':True,**changes};d.atomic(p,data);return p

    def dispatch(self, s):
        command = d.plan(s)
        self.assertEqual(command['tool'], 'collaboration.followup_task')
        d.ack(s, command['dispatch_id'], 'actual tool success')
        return command['dispatch_id']

    def test_no_start_before_all_three_actual_acceptances(self):
        self.acceptance.pop(d.FLOWS[-1])
        with self.assertRaisesRegex(ValueError, 'three-acceptances'):
            self.state()

    def test_fixture_or_missing_business_evidence_is_not_acceptance(self):
        p = Path(self.acceptance[d.FLOWS[0]]); data = json.loads(p.read_text())
        data['fixture'] = True; p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'real-completion'): self.state()
        data.pop('fixture'); data['evidence'] = []; p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'business-evidence'): self.state()

    def test_changed_evidence_is_rejected(self):
        self.evidence.write_text('changed')
        with self.assertRaisesRegex(ValueError, 'evidence-changed'): self.state()

    def test_running_operator_cannot_be_double_dispatched(self):
        s = self.state(); key = self.dispatch(s)
        self.assertEqual(d.plan(s)['action'], 'inspect-original-run')
        with self.assertRaisesRegex(ValueError, 'dispatch-conflict'): d.ack(s, key, 'second')
        self.assertEqual(s['index'], 0)

    def test_stall_goes_to_supervisor_without_replaying_or_handing_off(self):
        s = self.state(); key = self.dispatch(s)
        now = datetime.fromisoformat(s['last_heartbeat']) + timedelta(minutes=6)
        result = d.inspect(s, now=now)
        self.assertEqual(result['action'], 'supervisor-repair')
        self.assertFalse(result['business_execution_allowed'])
        self.assertFalse(result['automatic_replay_allowed'])
        self.assertEqual(s['index'], 0)
        with self.assertRaisesRegex(ValueError, 'quiescence'):
            d.retry(s, key, False, str(self.evidence))
        d.retry(s, key, True, self.repair(s))
        next_command=d.plan(s)
        self.assertEqual(next_command['role'], d.ROLES[0])
        self.assertNotEqual(next_command['dispatch_id'], key)
        self.assertIn('续原未完成工单', next_command['message'])

    def test_wrong_operator_heartbeat_cannot_keep_lease_alive(self):
        s = self.state(); self.dispatch(s)
        with self.assertRaisesRegex(ValueError, 'lease-conflict'):
            d.heartbeat(s, 'wrong', str(self.journal))

    def test_finished_roles_are_serial_and_final_done(self):
        s = self.state()
        for role, flow in zip(d.ROLES, d.FLOWS):
            self.assertEqual(d.current(s)['role'], role)
            key = self.dispatch(s)
            d.finish(s, key, self.completion(s,key,flow))
        self.assertEqual(d.plan(s)['action'], 'done')

    def test_wrong_workflow_report_does_not_advance(self):
        s = self.state(); key = self.dispatch(s)
        with self.assertRaisesRegex(ValueError, 'real-completion'):
            d.finish(s, key, self.acceptance[d.FLOWS[-1]])
        self.assertEqual(s['index'], 0)

    def test_policy_cannot_be_switched_to_production(self):
        s = self.state(); s['production_enabled'] = True
        with self.assertRaisesRegex(ValueError, 'dispatch-policy'): d.plan(s)

    def test_plan_result_is_write_ahead_and_crash_before_ack_cannot_redispatch(self):
        root=self.root/'cli';root.mkdir();state=self.state();d.atomic(root/'state.json',state)
        cmd=[sys.executable,str(Path(d.__file__).resolve()),'--root',str(root),'plan']
        first=json.loads(subprocess.check_output(cmd));self.assertEqual(first['action'],'dispatch')
        persisted=d.read(root/'state.json');self.assertEqual(persisted['phase'],'dispatch-intent');self.assertEqual(persisted['dispatch_id'],first['dispatch_id'])
        second=json.loads(subprocess.check_output(cmd));self.assertEqual(second['action'],'inspect-original-run');self.assertEqual(second['dispatch_id'],first['dispatch_id']);self.assertNotIn('tool',second)
        with self.assertRaisesRegex(ValueError,'quiescence'):d.retry(persisted,first['dispatch_id'],False,str(self.evidence))

    def test_inspect_ready_does_not_consume_dispatch_intent(self):
        s=self.state();self.assertEqual(d.inspect(s)['action'],'await-plan');self.assertEqual(s['phase'],'ready');self.assertEqual(d.plan(s)['action'],'dispatch')

    def test_unacked_intent_timeout_requires_reconcile_not_replay(self):
        s=self.state();command=d.plan(s);future=datetime.fromisoformat(s['dispatch_intent_at'])+timedelta(minutes=6)
        result=d.inspect(s,now=future);self.assertEqual(result['action'],'supervisor-reconcile-dispatch');self.assertFalse(result['automatic_replay_allowed']);self.assertEqual(s['index'],0)
        d.ack(s,command['dispatch_id'],'late observed original tool receipt');self.assertEqual(s['phase'],'running')

    def test_heartbeats_without_journal_changes_do_not_mask_stall(self):
        s=self.state();key=self.dispatch(s);start=datetime.fromisoformat(s['last_heartbeat']);d.heartbeat(s,key,self.journal,now=start)
        for minute in range(1,7):d.heartbeat(s,key,self.journal,now=start+timedelta(minutes=minute))
        result=d.inspect(s,now=start+timedelta(minutes=6));self.assertEqual(result['action'],'supervisor-repair');self.assertEqual(result['reason'],'journal-no-progress');self.assertEqual(result['idle_seconds'],0)

    def test_real_journal_change_resets_progress_only_for_same_lease(self):
        s=self.state();key=self.dispatch(s);start=datetime.fromisoformat(s['last_heartbeat']);d.heartbeat(s,key,self.journal,now=start)
        journal=d.read(self.journal);journal['checkpoints'].append({'stage':'navigation','groupid':'123'});d.atomic(self.journal,journal);d.heartbeat(s,key,self.journal,now=start+timedelta(minutes=4));self.assertEqual(d.inspect(s,now=start+timedelta(minutes=6))['action'],'wait')

    def test_finish_rejects_old_acceptance_report_cross_day_and_other_dispatch(self):
        s=self.state();key=self.dispatch(s)
        with self.assertRaisesRegex(ValueError,'completion-dispatch-scope'):d.finish(s,key,self.acceptance[d.FLOWS[0]])
        p=Path(self.completion(s,key,d.FLOWS[0]));original=json.loads(p.read_text())
        for change in ({'day':'2026-10-20'},{'dispatch_id':'another-run'},{'role':d.ROLES[-1]},{'completed_at':'2000-01-01T00:00:00Z'}):
            data={**original,**change};p.write_text(json.dumps(data))
            with self.subTest(change=change),self.assertRaises(ValueError):d.finish(s,key,p)
        self.assertEqual(s['index'],0)

    def test_legacy_ready_unknown_dispatch_is_quarantined_and_running_can_resume(self):
        s=self.state();s['version']=1;d.migrate(s);self.assertTrue(s['legacy_dispatch_unknown']);self.assertEqual(d.plan(s)['action'],'inspect-original-run');repair=self.root/'reconcile.json';repair.write_text(json.dumps({'dispatch_id':s['dispatch_id'],'day':s['day'],'role':d.current(s)['role'],'dispatch_outcome':'not-dispatched','operator_quiescent':True,'browser_quiescent':True,'wecom_quiescent':True,'original_work_orders_only':True}));d.retry(s,s['dispatch_id'],True,repair);self.assertEqual(d.plan(s)['action'],'dispatch')
        running=self.state();key=self.dispatch(running);running['version']=1;running.pop('last_progress_at');d.migrate(running);d.heartbeat(running,key,self.journal);self.assertEqual(running['phase'],'running')

    def test_unknown_dispatch_cannot_retry_with_only_quiescence_checkbox(self):
        s=self.state();key=d.plan(s)['dispatch_id']
        with self.assertRaisesRegex(ValueError,'scope-and-quiescence'):d.retry(s,key,True,self.evidence)
        self.assertEqual(s['phase'],'dispatch-intent');self.assertEqual(s['attempt'],0)

    def test_all_retry_paths_require_original_scope_and_all_quiescent_fields(self):
        for attention in (False,True):
            s=self.state();key=self.dispatch(s)
            if attention:s.update(phase='attention',attention_reason='journal-no-progress')
            for change in ({'dispatch_id':'other'},{'day':'2026-10-20'},{'role':d.ROLES[-1]},*({field:False} for field in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only'))):
                with self.subTest(attention=attention,change=change),self.assertRaisesRegex(ValueError,'scope-and-quiescence'):
                    d.retry(s,key,True,self.repair(s,**change))
                self.assertEqual(s['attempt'],0)
            d.retry(s,key,True,self.repair(s));self.assertEqual(s['phase'],'ready')

    def test_unknown_retry_additionally_needs_outcome_and_preserves_original_intent(self):
        s=self.state();key=d.plan(s)['dispatch_id']
        with self.assertRaisesRegex(ValueError,'unknown-dispatch-reconciliation'):d.retry(s,key,True,self.repair(s))
        self.assertEqual(s['phase'],'dispatch-intent')
        d.retry(s,key,True,self.repair(s,dispatch_outcome='not-dispatched'));self.assertEqual(s['phase'],'ready')

    def test_new_plan_rechecks_original_report_bytes_and_evidence(self):
        s=self.state();p=Path(self.acceptance[d.FLOWS[-1]]);raw=p.read_bytes();data=json.loads(raw);data['extra']='replacement valid report';p.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'pinned-acceptance-changed'):d.plan(s)
        self.assertEqual(s['phase'],'ready');self.assertFalse(s['events'])
        p.write_bytes(raw);self.evidence.write_text('changed')
        with self.assertRaisesRegex(ValueError,'evidence-changed'):d.plan(s)
        self.assertEqual(s['phase'],'ready')

    def test_plan_cutoff_is_dispatch_day_not_runtime_today(self):
        s=self.state();message=d.plan(s)['message'];self.assertIn('调度日2026-10-21不含',message);self.assertNotIn('补做到今天',message)


if __name__ == '__main__': unittest.main()
