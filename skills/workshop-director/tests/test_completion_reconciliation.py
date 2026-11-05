"""Original-lease completion reconciliation is local evidence only, never replay."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import director as d
import coordinator as c
import test_director as base
import test_coordinator as coordinator_base

class CompletionReconciliationTests(base.DirectorTest):
    def stopped(self):
        s=self.state();key=self.dispatch(s);d.heartbeat(s,key,self.journal)
        d.inspect(s,now=datetime.fromisoformat(s['last_heartbeat'])+timedelta(minutes=6))
        return s,key
    def completion_bundle(self,s,key):
        journal=d.read(self.journal);journal.update(state='complete',phase='done');d.atomic(self.journal,journal)
        src={'path':str(self.journal.resolve()),'sha256':hashlib.sha256(self.journal.read_bytes()).hexdigest()}
        p=Path(self.completion(s,key,d.current(s)['workflow']));value=d.read(p);value['evidence'].append(src);d.atomic(p,value)
        r={'kind':'supervisor-original-dispatch-completion-reconciliation-v1','dispatch_id':key,'day':s['day'],'role':d.current(s)['role'],'source_completion_verified':True,'operator_quiescent':True,'browser_quiescent':True,'wecom_quiescent':True,'original_work_orders_only':True,'completion_report':{'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'original_work_order':{'journal':src,'identity':d.original_work_order_identity(journal)}}
        rp=self.root/'supervisor.json';d.atomic(rp,r);return p,rp
    def test_original_attention_completion_is_consumed_once_without_new_dispatch(self):
        s,key=self.stopped();p,rp=self.completion_bundle(s,key);before=sum(e['type']=='dispatch-intent' for e in s['events'])
        with self.assertRaisesRegex(ValueError,'lease-conflict'):d.finish(s,key,p)
        d.reconcile_finish(s,key,p,rp)
        self.assertEqual(s['index'],1);self.assertEqual(s['phase'],'ready');self.assertEqual(s['dispatch_id'],key);self.assertEqual(s['attempt'],0)
        self.assertEqual(sum(e['type']=='dispatch-intent' for e in s['events']),before)
        self.assertEqual(sum(e['type']=='completed' for e in s['events']),1)
        event=next(e for e in s['events'] if e['type']=='supervisor-original-completion-reconciled');self.assertFalse(event['business_replayed']);self.assertFalse(event['new_dispatch_created'])
        with self.assertRaises(ValueError):d.reconcile_finish(s,key,p,rp)
    def test_missing_supervisor_report_or_mismatched_scope_and_quiescence_is_rejected(self):
        s,key=self.stopped();p,rp=self.completion_bundle(s,key);original=d.read(rp)
        with self.assertRaisesRegex(ValueError,'supervisor-completion-reconciliation-required'):d.reconcile_finish(s,key,p,None)
        for changes in ({'dispatch_id':'other'},{'day':'2026-10-20'},{'role':d.ROLES[-1]},{'source_completion_verified':False},{'wecom_quiescent':False},{'original_work_orders_only':False},{'completion_report':{'path':str(p.resolve()),'sha256':'0'*64}}):
            d.atomic(rp,{**original,**changes})
            with self.subTest(changes=changes),self.assertRaises(ValueError):d.reconcile_finish(s,key,p,rp)
            self.assertEqual(s['index'],0);self.assertEqual(s['phase'],'attention')
    def test_unacked_dispatch_cannot_use_reconciliation_even_with_report(self):
        s=self.state();key=d.plan(s)['dispatch_id'];s.update(phase='attention',attention_reason='dispatch-ack-unknown');p,rp=self.completion_bundle(s,key)
        with self.assertRaisesRegex(ValueError,'original-ack-required'):d.reconcile_finish(s,key,p,rp)
        # Removing the explicit ack-unknown reason cannot synthesize an ack.
        s['attention_reason']='semantic-progress-unverified'
        with self.assertRaisesRegex(ValueError,'original-ack-required'):d.reconcile_finish(s,key,p,rp)
        self.assertEqual(s['index'],0)
    def test_original_lease_time_remains_strict_and_stale_completed_proof_is_rejected(self):
        s,key=self.stopped();p,rp=self.completion_bundle(s,key);value=d.read(p);value['completed_at']='2000-01-01T00:00:00Z';d.atomic(p,value)
        with self.assertRaisesRegex(ValueError,'time-outside-dispatch'):d.reconcile_finish(s,key,p,rp)
        self.assertEqual(s['phase'],'attention')
    def test_original_work_order_change_or_missing_source_from_evidence_rejected(self):
        for change in ('identity','source-not-in-evidence','source-other-path'):
            s,key=self.stopped();p,rp=self.completion_bundle(s,key);r=d.read(rp)
            if change=='identity':r['original_work_order']['identity']['work_order_id']='different'
            elif change=='source-other-path':
                target=self.root/'other-job.json';d.atomic(target,d.read(self.journal));ref={'path':str(target.resolve()),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()};r['original_work_order']['journal']=ref;v=d.read(p);v['evidence'].append(ref);d.atomic(p,v);r['completion_report']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            else:
                v=d.read(p);v['evidence']=v['evidence'][:1];d.atomic(p,v);r['completion_report']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            d.atomic(rp,r)
            with self.subTest(change=change),self.assertRaises(ValueError):d.reconcile_finish(s,key,p,rp)
            self.assertEqual(s['index'],0)
    def test_frozen_same_bytes_copy_covers_canonical_original(self):
        s,key=self.stopped();p,rp=self.completion_bundle(s,key);r=d.read(rp);source=r['original_work_order']['journal'];snapshot=self.root/'frozen-source.json';snapshot.write_bytes(self.journal.read_bytes());ref={'path':str(snapshot.resolve()),'sha256':source['sha256']};v=d.read(p);v['evidence']=[ref if x==source else x for x in v['evidence']];d.atomic(p,v);r['completion_report']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();d.atomic(rp,r);d.reconcile_finish(s,key,p,rp);self.assertEqual(s['phase'],'ready');self.assertEqual(s['index'],1)
    def test_frozen_copy_changed_content_cannot_cover_original(self):
        s,key=self.stopped();p,rp=self.completion_bundle(s,key);r=d.read(rp);source=r['original_work_order']['journal'];snapshot=self.root/'changed-source.json';v=d.read(self.journal);v['work_order_id']='changed';d.atomic(snapshot,v);ref={'path':str(snapshot.resolve()),'sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest()};v=d.read(p);v['evidence']=[ref if x==source else x for x in v['evidence']];d.atomic(p,v);r['completion_report']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest();d.atomic(rp,r)
        with self.assertRaises(ValueError):d.reconcile_finish(s,key,p,rp)
        self.assertEqual(s['phase'],'attention')

    def test_coordinator_transfers_explicit_reconciliation_without_plan_or_business_execution(self):
        fixture=coordinator_base.CoordinatorTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        offer=fixture.morning();key=offer['dispatch_id'];c.command(fixture.dispatch,'ack',dispatch_id=key,tool_receipt='original tool receipt')
        state=d.read(fixture.dispatch/'state.json');state.update(phase='attention',attention_reason='journal-no-progress');d.atomic(fixture.dispatch/'state.json',state)
        # The source is a fixed original operator journal and is explicitly
        # referenced in the independently verified completion report.
        source={'path':str(fixture.journal.resolve()),'sha256':hashlib.sha256(fixture.journal.read_bytes()).hexdigest()};report=Path(base.DirectorTest.completion(fixture,state,key,d.FLOWS[0]));data=d.read(report);data['evidence'].append(source);d.atomic(report,data)
        r={'kind':'supervisor-original-dispatch-completion-reconciliation-v1','dispatch_id':key,'day':state['day'],'role':d.ROLES[0],'source_completion_verified':True,'operator_quiescent':True,'browser_quiescent':True,'wecom_quiescent':True,'original_work_orders_only':True,'completion_report':{'path':str(report.resolve()),'sha256':hashlib.sha256(report.read_bytes()).hexdigest()},'original_work_order':{'journal':source,'identity':d.original_work_order_identity(d.read(fixture.journal))}}
        rp=fixture.root/'reconcile.json';d.atomic(rp,r)
        # This is a coordinator forwarding unit test; real parent replay has its own tests.
        with patch.object(d,'plan',side_effect=AssertionError('must not dispatch')),patch('daily_orchestration.verify_completion',return_value=data) as parent_gate:
            result=c.command(fixture.dispatch,'reconcile-finish',dispatch_id=key,report=report,supervisor_report=rp)
        self.assertEqual(result['index'],1);self.assertEqual(result['dispatch_id'],key);self.assertEqual(parent_gate.call_args.args[0],report)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(CompletionReconciliationTests(n) for n in CompletionReconciliationTests.__dict__ if n.startswith('test_'))
if __name__=='__main__':unittest.main()
