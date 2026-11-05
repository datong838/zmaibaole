"""Outbox scheduling fixtures. All messenger execution is injected fake code."""
import copy,io,json,sys,tempfile,unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_workflow import workbook,review,IDENTITY
from ds_common import load_map,MAPPING,sha256,company_dir
from ds_processor import process
from ds_calendar import compute
import notification_backlog as b
class BacklogTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.out=self.root/'outbox';self.jobs=self.root/'sender';self.batch=self.make_batch('2026-10-19')
    def make_batch(self,today):
        base=self.root/'work'/today/'daily';base.mkdir(parents=True);dates=compute(today);companies=[]
        for company in load_map():
            dest=company_dir(base,company);source=base/('source-'+str(company['seq'])+'.xlsx');workbook(source,[review(star=2,day=dates['start']+' 12:00:00')])
            evidence={'company':company['company'],'groupid':{'烟台一成教育文化咨询有限公司':'1767942028615694','上海老芗汇餐饮管理有限公司':'1764303851132943'}[company['company']],'date_range':{k:dates[k] for k in ('start','end')},'src_sha256':sha256(source),'download_verified':True,'account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,'operator_skill':'douyin-laike-operator','backend':'codex-existing-extension'}
            result=process(source,company,dates,dest,MAPPING,page_filtered=1,evidence=evidence)
            self.assertEqual(result['status'],'complete',result);companies.append({**company,'status':'complete','outdir':str(dest),'receipt':result['receipt'],'date_range':dates})
        path=base/'batch_receipt.json';path.write_text(json.dumps({'flow':'daily-comment-stats','mode':'agent-live','status':'complete','mapping_sha256':sha256(MAPPING),'companies':companies,'date_range':dates,'roundtrip':{'required':True,'verified':True},'failed':0,'needs_review':0}));return path
    def prepare(self,path=None):return b.prepare_batch(path or self.batch,self.out,self.jobs)
    def state(self,queue,index=0,**fields):
        q=json.loads(Path(queue).read_text());item=q['items'][index];job,path=b.job_for(item,self.jobs);kwargs={'text':job['text']} if item['type']=='text' else {'file':job['file']}
        p,s=b.messenger.prepare(item['key'],'group',b.pn.TARGET,directory=self.jobs,**kwargs);s.update(fields);b.messenger.atomic(p,s);return p,s
    def complete(self,path):
        s=json.loads(Path(path).read_text());s.update(status='complete',phase='done',sent=True,ui_confirmed=True,pid=123,baseline=0,send_intent_at='2026-10-21T08:00:00+08:00',completed_at='2026-10-21T08:01:00+08:00');s['events']=[{'stage':'send-intent'},{'stage':'ui-confirmed','recipient':b.pn.TARGET,'recipient_kind':'group'}];b.messenger.atomic(path,s);return s
    def test_immutable_six_orders_compatible_keys_no_ui_job_created(self):
        queue=self.prepare();q=json.loads(queue.read_text());self.assertEqual(len(q['items']),6);self.assertFalse(self.jobs.exists());self.assertEqual(self.prepare(),queue)
        result=b.backlog(self.out);self.assertFalse(result['can_acquire_new_dates']);self.assertEqual(result['next']['next']['part'],'detail')
        for item in q['items']:self.assertEqual(item['key'],'daily-comments:'+item['company']+':'+item['dates']['start']+':'+item['dates']['end']+':'+item['part'])
    def test_pending_ignores_handwritten_sent_acceptance_and_complete_requires_real_job_evidence(self):
        queue=self.prepare();queue.with_name('acceptance.json').write_text('{"sent":true,"all_required_client_ui_confirmed":true}')
        self.assertFalse(b.inspect(queue)['complete']);path,s=self.state(queue,status='complete',phase='done',sent=True,ui_confirmed=True)
        with self.assertRaisesRegex(ValueError,'evidence-incomplete'):b.inspect(queue)
        self.complete(path);self.assertEqual(b.inspect(queue)['items'][0]['action'],'skip-complete')
    def test_complete_client_jobs_generate_mechanical_hash_acceptance_and_skip(self):
        queue=self.prepare()
        for index in range(6):path,_=self.state(queue,index);self.complete(path)
        result=b.inspect(queue,True);a=json.loads(Path(result['acceptance']['path']).read_text());self.assertTrue(a['all_required_client_ui_confirmed']);self.assertFalse(a['delivery_confirmed']);self.assertEqual(len(a['jobs']),6)
        for ref in a['jobs']:self.assertEqual(sha256(ref['path']),ref['sha256'])
        before=sha256(Path(result['acceptance']['path']));b.run(self.out,advance=lambda p:(_ for _ in ()).throw(AssertionError('complete must skip')));self.assertEqual(sha256(result['acceptance']['path']),before)
    def test_failed_without_intent_requires_supervisor_no_automatic_resume(self):
        queue=self.prepare();path,_=self.state(queue,status='failed',phase='stage',error='ui-tree-incomplete')
        result=b.run(self.out,advance=lambda p:(_ for _ in ()).throw(AssertionError('must not resume')))
        self.assertEqual(result['next']['next']['action'],'supervisor-safe-resume');self.assertEqual(json.loads(path.read_text())['status'],'failed')
    def test_unknown_only_original_verify_sent_read_once_and_no_new_key(self):
        queue=self.prepare();path,_=self.state(queue,status='unknown',phase='verify-sent',send_intent_at='fixture',events=[{'stage':'send-intent'}]);calls=[]
        result=b.run(self.out,advance=lambda p:calls.append(str(p)));self.assertEqual(calls,[str(path)]);self.assertFalse(result['complete']);self.assertEqual(len(list(self.jobs.glob('*.json'))),1)
        s=json.loads(path.read_text());s['phase']='file-confirm';b.messenger.atomic(path,s)
        result=b.run(self.out,advance=lambda p:(_ for _ in ()).throw(AssertionError('unknown file confirmation must hold')));self.assertEqual(result['next']['next']['action'],'hold-unknown')
    def test_oldest_batch_before_newer_and_company_sequence_serial(self):
        old=self.prepare();new=self.prepare(self.make_batch('2026-10-21'));calls=[]
        result=b.run(self.out,max_steps=2,advance=lambda p:calls.append(str(p)))
        self.assertEqual(result['next']['outbox'],str(old));self.assertEqual(calls,[result['next']['next']['job_path']]);self.assertFalse(any(self.jobs.glob('bad-new-key*.json')))
    def test_payload_target_fingerprint_and_source_mutations_fail_closed(self):
        queue=self.prepare();path,s=self.state(queue);s['job']['target']='生产群';b.messenger.atomic(path,s)
        with self.assertRaisesRegex(ValueError,'binding-conflict'):b.inspect(queue)
        self.state(queue);q=json.loads(queue.read_text());Path(q['items'][0]['payload']).write_bytes(b'changed')
        with self.assertRaises((ValueError,RuntimeError)):b.inspect(queue)
    def test_partial_batch_or_unreturned_company_not_accepted(self):
        original=self.batch.read_text();value=json.loads(original);value['companies'].pop();self.batch.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'company-sequence'):self.prepare()
        value=json.loads(original);value['roundtrip']['verified']=False;self.batch.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'return-unverified'):self.prepare()
    def test_scan_and_explicit_receipt_pin_do_not_need_manual_six_item_commands(self):
        result=b.plan(work_root=self.root/'work',outbox=self.out,messenger_dir=self.jobs);self.assertEqual(len(result['batches']),1)
        receipt=Path(json.loads(self.batch.read_text())['companies'][0]['receipt']);result=b.plan(receipt=receipt,receipt_sha=sha256(receipt),outbox=self.out,messenger_dir=self.jobs);self.assertEqual(len(result['next']['items']),6)
        with self.assertRaisesRegex(ValueError,'explicit-receipt-hash'):b.plan(receipt=receipt,receipt_sha='f'*64,outbox=self.out,messenger_dir=self.jobs)
    def test_gate_discovers_pending_and_blocks_new_date_without_advancing(self):
        argv=['notification_backlog.py','gate','--work-root',str(self.root/'work'),'--outbox',str(self.out)]
        with patch.object(sys,'argv',argv),patch.object(b.messenger,'RUNTIME',self.jobs),redirect_stdout(io.StringIO()) as output:
            self.assertEqual(b.main(),3)
        result=json.loads(output.getvalue());self.assertEqual(result['gate'],'blocked-notification-backlog');self.assertFalse(result['can_acquire_new_dates']);self.assertFalse(self.jobs.exists())
    def test_running_intent_never_advances_unknown_confirmation(self):
        queue=self.prepare();path,_=self.state(queue,status='running',phase='file-confirm',send_intent_at='fixture',events=[{'stage':'send-intent'}])
        result=b.run(self.out,advance=lambda p:(_ for _ in ()).throw(AssertionError('no confirmation replay')));self.assertEqual(result['next']['next']['action'],'hold-intent')
    def test_new_running_file_uses_one_complete_sender_run_normal_chain(self):
        queue=self.prepare();path,_=self.state(queue);calls=[]
        def normal(p):
            calls.append(str(p));self.complete(p)
        result=b.run(self.out,max_steps=1,run_job=normal,advance=lambda p:(_ for _ in ()).throw(AssertionError('not step-driven')))
        self.assertEqual(calls,[str(path)]);self.assertEqual(result['batches'][0]['items'][0]['action'],'skip-complete')
    def test_new_sender_run_unknown_result_stops_without_followup_verify(self):
        queue=self.prepare();path,_=self.state(queue);calls=[]
        def normal(p):
            calls.append(str(p));s=json.loads(p.read_text());s.update(status='unknown',phase='verify-sent',send_intent_at='fixture',events=[{'stage':'send-intent'}]);b.messenger.atomic(p,s)
        result=b.run(self.out,max_steps=10,run_job=normal,advance=lambda p:(_ for _ in ()).throw(AssertionError('must hold after new unknown')))
        self.assertEqual(calls,[str(path)]);self.assertEqual(result['next']['next']['action'],'verify-readonly')
    def test_already_covered_company_uses_original_receipt_not_new_messages(self):
        batch=json.loads(self.batch.read_text());row=batch['companies'][0];r=json.loads(Path(row['receipt']).read_text());progress={'version':1,'companies':{row['company']:{'initial_start':r['date_range']['start'],'next_start':batch['date_range']['today'],'completions':[{'start':r['date_range']['start'],'end':r['date_range']['end'],'receipt':row['receipt'],'receipt_sha256':sha256(row['receipt'])}]}}};pp=self.root/'progress.json';pp.write_text(json.dumps(progress));batch['progress_file']=str(pp);row.update(status='skipped',skip_reason='already_covered',date_range={**row['date_range'],'ok':False,'reason':'already_covered','covered_through':r['date_range']['end']});self.batch.write_text(json.dumps(batch));queue=self.prepare();q=json.loads(queue.read_text());self.assertEqual(len(q['items']),3);self.assertTrue(q['scopes'][0]['already_covered']);self.assertEqual({x['company'] for x in q['items']},{batch['companies'][1]['company']});pp.write_text('{}');self.assertEqual(self.prepare(),queue);b.validate_queue(queue)
        Path(row['receipt']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'input-changed'):b.validate_queue(queue)
    def test_skipped_risk_or_unproven_coverage_not_accepted(self):
        original=json.loads(self.batch.read_text());batch=copy.deepcopy(original);batch['companies'][0].update(status='skipped',skip_reason='company-not-found');self.batch.write_text(json.dumps(batch))
        with self.assertRaises(ValueError):self.prepare()
        batch=copy.deepcopy(original);row=batch['companies'][0];row.update(status='skipped',skip_reason='already_covered',date_range={**row['date_range'],'ok':False,'reason':'already_covered','covered_through':batch['date_range']['end']});pp=self.root/'progress.json';pp.write_text(json.dumps({'version':1,'companies':{row['company']:{'initial_start':row['date_range']['start'],'next_start':batch['date_range']['today'],'completions':[]}}}));batch['progress_file']=str(pp);self.batch.write_text(json.dumps(batch))
        with self.assertRaisesRegex(ValueError,'coverage-unverified'):self.prepare()
if __name__=='__main__':unittest.main()
