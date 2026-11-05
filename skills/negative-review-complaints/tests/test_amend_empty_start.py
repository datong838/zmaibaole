"""Temporary ledgers only. No real progress edits, browser or external send."""
import copy, hashlib, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import workflow as w
class EmptyStartTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.s=w.initialize(self.root,'测试公司','123','2026-10-21','2026-10-19',mode='fixture')
    def test_only_earlier_empty_anchor_changes_and_exact_backup_retained(self):
        original=(self.root/'state.json').read_bytes();original_state=copy.deepcopy(self.s)
        w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
        self.assertEqual((self.s['initial_start'],self.s['next_start']),('2026-10-16','2026-10-16'))
        event=self.s['events'][-1];self.assertEqual(event['type'],'empty-start-amended')
        self.assertEqual(event['backup']['sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual(Path(event['backup']['path']).read_bytes(),original)
        for key in original_state:
            if key not in ('initial_start','next_start','events','updated_at','xlsx_dirty'):self.assertEqual(self.s[key],original_state[key])
        self.assertIsNone(self.s['covered_through']);self.assertIsNone(self.s['last_completed_at'])
    def test_same_later_today_and_noncanonical_date_refused(self):
        for start in ('2026-10-19','2026-10-20','2026-10-21','20261016'):
            with self.subTest(start=start),self.assertRaises(ValueError):w.amend_empty_start(self.root,self.s,start,'2026-10-21')
        self.assertEqual(w.read(self.root/'state.json')['initial_start'],'2026-10-19')
    def test_any_processing_state_refuses_without_clearing_it(self):
        for key,value in [('tasks',{'id':{}}),('batches',{'date':{}}),('completions',[{}]),('send_jobs',{'id':{}}),('send_attempt',{'intent':True}),('receipts',[{}]),('covered_through','2026-10-18'),('last_completed_on','2026-10-20'),('last_completed_at','stamp'),('next_start','2026-10-20')]:
            state=copy.deepcopy(self.s);state[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'progress-not-empty'):w.amend_empty_start(self.root,state,'2026-10-16','2026-10-21')
            self.assertEqual(state[key],value)
    def test_prior_business_events_refuse_even_if_rows_were_removed(self):
        self.s['events'].append({'type':'captured','total':0})
        with self.assertRaisesRegex(ValueError,'processing-history'):w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
    def test_stale_in_memory_state_refused(self):
        disk=w.read(self.root/'state.json');disk['identity']={'provider':'other'};w.atomic(self.root/'state.json',disk)
        with self.assertRaisesRegex(ValueError,'stale-state'):w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
    def test_amend_retry_still_empty_and_old_audit_preserved(self):
        w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
        w.amend_empty_start(self.root,self.s,'2026-10-15','2026-10-21')
        self.assertEqual(sum(e['type']=='empty-start-amended' for e in self.s['events']),2)
        self.assertEqual(len(list((self.root/'state-backups').glob('*.json'))),2)
    def test_cli_dispatch_uses_guarded_amend_and_reports_backlog(self):
        from unittest.mock import patch
        from contextlib import redirect_stdout
        from datetime import date
        import io
        output=io.StringIO()
        argv=['workflow.py','--root',str(self.root),'amend-empty-start','--start','2026-10-16']
        with patch.object(sys,'argv',argv),patch.object(w,'shanghai_today',return_value=date(2026,10,21)),patch.object(w,'export_xlsx',return_value={'fixture_only':True},create=True),redirect_stdout(output):
            w.main()
        result=json.loads(output.getvalue());self.assertTrue(result['ok']);self.assertEqual(result['plan']['start'],'2026-10-16')
        self.assertEqual(w.read(self.root/'state.json')['events'][-1]['type'],'empty-start-amended')
    def test_corrupted_existing_backup_refuses_progress_change(self):
        old_hash=hashlib.sha256((self.root/'state.json').read_bytes()).hexdigest()
        folder=self.root/'state-backups';folder.mkdir();(folder/('before-empty-start-'+old_hash+'.json')).write_text('corrupt')
        with self.assertRaisesRegex(ValueError,'backup-hash'):w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
        self.assertEqual(self.s['initial_start'],'2026-10-19')
    def test_backend_can_migrate_legacy_empty_ledger_with_exact_backup(self):
        self.s.pop('browser_backend',None);w.atomic(self.root/'state.json',self.s)
        original=(self.root/'state.json').read_bytes()
        w.amend_empty_backend(self.root,self.s,'local-dom-bridge')
        event=self.s['events'][-1];self.assertEqual(event['type'],'empty-backend-amended');self.assertEqual(event['previous_backend'],'codex-existing-extension')
        self.assertEqual(Path(event['backup']['path']).read_bytes(),original)
        self.assertEqual(event['backup']['sha256'],hashlib.sha256(original).hexdigest())
        self.assertEqual(self.s['browser_backend'],'local-dom-bridge');self.assertEqual(self.s['initial_start'],'2026-10-19')
        self.assertIsNone(self.s['covered_through']);self.assertIsNone(self.s['last_completed_at'])
    def test_backend_refuses_any_identity_or_processing_fields(self):
        for key,value in [('identity',{}),('identity',{'provider':'old'}),('identity_before',{'id':'x'}),('account_verified',True),('tasks',{'x':{}}),('batches',{'x':{}}),('send_intent',{'unknown':True}),('covered_through','2026-10-18')]:
            state=copy.deepcopy(self.s);state[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):w.amend_empty_backend(self.root,state,'local-dom-bridge')
            self.assertEqual(state[key],value)
    def test_backend_and_start_audits_can_be_sequenced_without_processing(self):
        w.amend_empty_start(self.root,self.s,'2026-10-16','2026-10-21')
        w.amend_empty_backend(self.root,self.s,'local-dom-bridge')
        w.amend_empty_start(self.root,self.s,'2026-10-15','2026-10-21')
        self.assertEqual([e['type'] for e in self.s['events']],['initialized','empty-start-amended','empty-backend-amended','empty-start-amended'])
    def test_backend_cannot_use_unknown_route_and_repeat_is_noop(self):
        with self.assertRaisesRegex(ValueError,'backend-invalid'):w.amend_empty_backend(self.root,self.s,'debugger')
        w.amend_empty_backend(self.root,self.s,'local-dom-bridge');count=len(self.s['events'])
        w.amend_empty_backend(self.root,self.s,'local-dom-bridge');self.assertEqual(len(self.s['events']),count)
    def test_backend_cli_dispatch_uses_same_strict_gate(self):
        from unittest.mock import patch
        from contextlib import redirect_stdout
        import io
        output=io.StringIO();argv=['workflow.py','--root',str(self.root),'amend-empty-backend','--backend','local-dom-bridge']
        with patch.object(sys,'argv',argv),patch.object(w,'export_xlsx',return_value={'fixture_only':True},create=True),redirect_stdout(output):w.main()
        result=json.loads(output.getvalue());self.assertTrue(result['ok']);self.assertEqual(result['plan']['browser_backend'],'local-dom-bridge')
        self.assertEqual(w.read(self.root/'state.json')['events'][-1]['type'],'empty-backend-amended')
    def test_backend_rejects_cleared_business_history_and_stale_state(self):
        state=copy.deepcopy(self.s);state['events'].append({'type':'test-group-ui-confirmed'})
        with self.assertRaisesRegex(ValueError,'processing-history'):w.amend_empty_backend(self.root,state,'local-dom-bridge')
        self.s['uncommitted']='changed'
        with self.assertRaisesRegex(ValueError,'stale-state'):w.amend_empty_backend(self.root,self.s,'local-dom-bridge')
if __name__=='__main__':unittest.main()
