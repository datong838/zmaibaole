"""Synthetic dispatch artifacts only; no coordinator, business or UI execution."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import daily_dispatch_order as d
import execution_timing as t

class DispatchOrderTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.archive=self.root/'archive'
        self.config=self.write('companies.json',{'companies':{'company-a':{'groupid':'123'},'company-b':{'groupid':'456'}}})
        self.ledger={'version':1,'companies':{'company-a':{'next_start':'2026-10-16','covered_through':'2026-10-15','last_completed_on':'2026-10-16','planned_runs':{}},'company-b':{'next_start':'2026-10-20','covered_through':'2026-10-19','last_completed_on':'2026-10-20','planned_runs':{}}}}
        self.offer_value={'workflow':d.WORKFLOW,'role':d.ROLE,'action':'dispatch','tool':'collaboration.followup_task','dispatch_id':'2026-10-21:daily-comment-stats:0','message':'synthetic offer'};self.refresh()
    def write(self,name,value):
        path=self.root/name;path.write_text(json.dumps(value));return t.ref(path)
    def refresh(self):
        self.sequence=getattr(self,'sequence',0)+1;snapshot=self.write('ledger-snapshot-'+str(self.sequence)+'.json',self.ledger);progress={}
        for company,value in self.ledger['companies'].items():
            progress[company]={k:value.get(k) for k in ('next_start','covered_through','last_completed_on')}
            progress[company].update(original_plan_ids=list(value.get('planned_runs',{})),original_batch_ids=list(value.get('batches',{})),original_task_ids=list(value.get('tasks',{})))
        self.offer_value['ledger_snapshots']=[{'workflow':d.WORKFLOW,'company':None,'original_path':str(self.root/'untouched-live-ledger.json'),'snapshot':snapshot,'progress':progress}];self.offer=self.write('offer-'+str(self.sequence)+'.json',self.offer_value)
    def prepare(self,**kwargs):return d.archive(self.archive,self.offer,self.config,origin=kwargs.pop('origin','fresh'),**kwargs)
    def test_two_ranges_immutable_repeat_validates_and_does_not_start_or_write_ledger(self):
        ref=self.prepare();raw=Path(ref['path']).read_bytes();order=d.validate(ref,self.archive);self.assertEqual([x['start'] for x in order['scope']['company_ranges']],['2026-10-16','2026-10-20']);self.assertEqual(order['scope_sha256'],t.digest(order['scope']));self.assertEqual(self.prepare(),ref);self.assertEqual(Path(ref['path']).read_bytes(),raw);self.assertFalse(order['dispatch_authorization_granted']);self.assertFalse(order['timing_started']);self.assertFalse((self.root/'untouched-live-ledger.json').exists())
    def test_one_completed_company_skipped_without_reacquisition_other_company_continues(self):
        self.ledger['companies']['company-a']['next_start']='2026-10-21';self.refresh();order=d.validate(self.prepare(),self.archive)
        self.assertEqual([x['company'] for x in order['scope']['company_ranges']],['company-b']);self.assertEqual(order['skipped_companies'][0]['company'],'company-a');self.assertEqual(order['skipped_companies'][0]['ledger_snapshot'],order['ledger_snapshot']);self.assertEqual(order['skipped_companies'][0]['reason'],'already-covered-through-dispatch-day-exclusive')
    def test_all_completed_ranges_cannot_be_fresh_new_run(self):
        for value in self.ledger['companies'].values():value['next_start']='2026-10-21'
        self.refresh()
        with self.assertRaisesRegex(ValueError,'no-pending-range'):self.prepare()
        self.assertFalse(self.archive.exists())
    def test_overlapping_existing_plan_requires_verified_original_dispatch_resume(self):
        prior=self.prepare();self.offer_value['dispatch_id']='2026-10-21:daily-comment-stats:1'
        self.ledger['companies']['company-a']['planned_runs'][str(self.root/'original-run')]={'start':'2026-10-16','end':'2026-10-20','planned_on':'2026-10-21'};self.refresh()
        with self.assertRaisesRegex(ValueError,'use-resume'):self.prepare()
        with self.assertRaisesRegex(ValueError,'origin-invalid'):self.prepare(origin='resume')
        with self.assertRaisesRegex(ValueError,'order-invalid'):self.prepare(origin='resume',resumed_from=self.write('random.json',{'synthetic_original_stop':True}))
        order=d.validate(self.prepare(origin='resume',resumed_from=prior),self.archive);self.assertEqual(order['resumed_from'],prior);self.assertEqual(order['resume_identity']['work_order'],prior);self.assertEqual(order['resume_identity']['dispatch_id'],'2026-10-21:daily-comment-stats:0');self.assertEqual(order['overlapping_original_plans'][0]['run_dir'],str(self.root/'original-run'))
    def test_resume_prior_scope_subset_allows_completed_company_but_wrong_range_rejected(self):
        prior=self.prepare();self.offer_value['dispatch_id']='2026-10-21:daily-comment-stats:1';self.ledger['companies']['company-a']['next_start']='2026-10-21';self.refresh();order=d.validate(self.prepare(origin='resume',resumed_from=prior),self.archive);self.assertEqual(len(order['scope']['company_ranges']),1)
        self.offer_value['dispatch_id']='2026-10-21:daily-comment-stats:2';self.ledger['companies']['company-b']['next_start']='2026-10-19';self.refresh()
        with self.assertRaisesRegex(ValueError,'company-range-mismatch'):self.prepare(origin='resume',resumed_from=prior)
    def test_resume_same_dispatch_wrong_day_tampered_order_or_copied_ref_rejected(self):
        prior=self.prepare()
        with self.assertRaisesRegex(ValueError,'original-dispatch-required'):self.prepare(origin='resume',resumed_from=prior)
        self.offer_value['dispatch_id']='2026-10-22:daily-comment-stats:1';self.refresh()
        with self.assertRaisesRegex(ValueError,'workflow-day-mismatch'):self.prepare(origin='resume',resumed_from=prior)
        copied=self.write('copied.json',json.loads(Path(prior['path']).read_bytes()))
        with self.assertRaisesRegex(ValueError,'canonical-path-required'):self.prepare(origin='resume',resumed_from=copied)
        raw=json.loads(Path(prior['path']).read_bytes());raw['workflow']='violation-notifier';Path(prior['path']).write_text(json.dumps(raw))
        with self.assertRaisesRegex(ValueError,'evidence-changed'):self.prepare(origin='resume',resumed_from=prior)
    def test_nonoverlapping_completed_history_does_not_prevent_new_fresh_range(self):
        self.ledger['companies']['company-a']['planned_runs'][str(self.root/'old-completed-run')]={'start':'2026-10-10','end':'2026-10-15','planned_on':'2026-10-16'};self.refresh();order=d.validate(self.prepare(),self.archive);self.assertEqual(order['overlapping_original_plans'],[])
    def test_same_dispatch_cannot_change_scope_or_origin_and_copied_path_rejected(self):
        ref=self.prepare();raw=Path(ref['path']).read_bytes();self.ledger['companies']['company-a']['next_start']='2026-10-17';self.refresh()
        with self.assertRaisesRegex(ValueError,'immutable-conflict'):self.prepare()
        self.assertEqual(Path(ref['path']).read_bytes(),raw);copyref=self.write('copied-order.json',json.loads(raw))
        with self.assertRaisesRegex(ValueError,'canonical-path-required'):d.validate(copyref,self.archive)
    def test_offer_wrong_role_inspect_action_and_false_summary_rejected(self):
        original=copy.deepcopy(self.offer_value)
        for field,value in [('role','violation_operator'),('action','inspect-original-run'),('dispatch_id','2026-10-21:violation-notifier:0')]:
            offer=copy.deepcopy(original);offer[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):d.build(self.write('bad-offer.json',offer),self.config,origin='fresh')
        offer=copy.deepcopy(original);offer['ledger_snapshots'][0]['progress']['company-a']['next_start']='2026-10-17'
        with self.assertRaisesRegex(ValueError,'summary-not-derived'):d.build(self.write('false-summary.json',offer),self.config,origin='fresh')
    def test_ref_change_and_duplicate_gid_rejected(self):
        ref=self.prepare();Path(self.offer['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'evidence-changed'):d.validate(ref,self.archive)
        self.refresh();config=self.write('duplicate-companies.json',{'companies':{'company-a':{'groupid':'123'},'company-b':{'groupid':'123'}}})
        with self.assertRaisesRegex(ValueError,'company-duplicate'):d.build(self.offer,config,origin='fresh')
    def test_archive_order_directly_usable_by_timing_before_role_planning(self):
        from datetime import datetime, timezone
        class Clock:
            def monotonic(self):return 100.
            def wall(self):return datetime(2026,10,21,tzinfo=timezone.utc)
            def boot(self):return 'synthetic-system-boot'
        ref=self.prepare();order=d.validate(ref,self.archive);run=self.root/'timing.json'
        r=t.start(run,'daily-dispatch-test',ref,order['scope'],mode='acceptance',clock=Clock());self.assertFalse(r['delivery_sealed']);self.assertFalse(r['acceptance_pass']);s=json.loads(run.read_text());self.assertEqual(s['work_order'],ref);self.assertEqual(s['scope_sha256'],order['scope_sha256']);self.assertEqual(s['events'],[])
    def test_cli_prepare_verify_does_not_import_or_run_business_workflows(self):
        cli=Path(d.__file__);args=[sys.executable,'-I','-B',str(cli)];p=subprocess.run(args+['prepare','--root',str(self.archive),'--offer',self.offer['path'],'--companies',self.config['path'],'--origin','fresh'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr);result=json.loads(p.stdout);self.assertFalse(result['timing_started']);self.assertFalse(result['business_actions_performed']);p=subprocess.run(args+['verify','--root',str(self.archive),'--order',result['order']['path']],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);self.assertTrue(json.loads(p.stdout)['valid'])

if __name__=='__main__':unittest.main()
