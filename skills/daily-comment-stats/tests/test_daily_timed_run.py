"""Real daily file schemas with synthetic workbooks; every UI port is fake."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_workflow import workbook,review,IDENTITY
from ds_common import load_map,MAPPING,sha256,company_dir
from ds_processor import process
from ds_calendar import compute
import notification_backlog as b
import daily_timed_run as w
import execution_timing as t
import daily_dispatch_order as d

class Clock:
    def __init__(self):self.n=100.;self.base=datetime.now(timezone.utc).replace(microsecond=0)
    def monotonic(self):return self.n
    def wall(self):return self.base+timedelta(seconds=self.n-100)
    def boot(self):return 'synthetic-fixed-boot'

class Ports:
    def __init__(self,test):self.test=test;self.init_calls=0;self.send_calls=0;self.actual_sends=0;self.unknown=False
    def init(self,order,run_dir,progress):
        self.init_calls+=1;self.test.clock.n+=2;return self.test.batch(run_dir,progress)
    def advance(self,run_dir):
        path=run_dir/'batch_receipt.json';batch=json.loads(path.read_text());self.test.clock.n+=2
        if not self.test.did_web:
            self.test.did_web=True;job=run_dir/'operator/work-order.json';job.parent.mkdir();job.write_text(json.dumps({'work_order_id':'synthetic-original'}));return {'action':'acquire','backend':'local-dom-bridge','explicit_tab_id_required':True,'work_order_path':str(job)}
        batch['status']='complete';path.write_text(json.dumps(batch));return {'action':'done'}
    def prepare(self,batch_path,outbox):return b.prepare_batch(batch_path,outbox,self.test.jobs)
    def inspect(self,queue):return b.inspect(queue,True)
    def run(self,outbox,steps):
        self.send_calls+=1;state=json.loads((self.test.execution/'timing.json').read_text());self.test.assertEqual(state['delivery']['status'],'sealed');self.test.assertEqual(set(state['delivery']['keys']),{x['key'] for x in json.loads(next(Path(outbox).glob('*/outbox.json')).read_text())['items']})
        original=b.messenger.prepare
        def prepare(*a,**kw):
            self.test.assertEqual(json.loads((self.test.execution/'timing.json').read_text())['delivery']['status'],'sealed');return original(*a,**kw)
        def send(path):
            self.actual_sends+=1;job=json.loads(path.read_text());job.update(status='unknown' if self.unknown else 'complete',phase='verify-sent' if self.unknown else 'done',sent=not self.unknown,ui_confirmed=not self.unknown,pid=123,send_intent_at=self.test.clock.wall().isoformat(),completed_at=self.test.clock.wall().isoformat(),created_at=self.test.clock.wall().isoformat(),events=[{'stage':'send-intent'}]+([] if self.unknown else [{'stage':'ui-confirmed','recipient':t.TARGET,'recipient_kind':'group'}]));b.messenger.atomic(path,job)
        with patch.object(b.messenger,'prepare',side_effect=prepare):return b.run(outbox,steps,run_job=send,advance=lambda p:None)

class TimedRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.clock=Clock();self.jobs=self.root/'sender';self.archive=self.root/'archive';self.rows=load_map();self.zero=set();self.covered=set();self.did_web=False;self.ports=Ports(self)
        self.addCleanup(patch.stopall);patch.object(w,'PROJECT',self.root).start();patch.object(t,'SENDER_DIRECTORY',self.jobs).start()
    def pin(self,path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return t.ref(path)
    def make_row(self,base,company,dates,zero=False):
        base.mkdir(parents=True,exist_ok=True);dest=company_dir(base,company);source=base/('source-'+str(company['seq'])+'.xlsx');workbook(source,[] if zero else [review(star=2,day=dates['start']+' 12:00:00')]);gid={'烟台一成教育文化咨询有限公司':'1767942028615694','上海老芗汇餐饮管理有限公司':'1764303851132943'}[company['company']]
        evidence={'company':company['company'],'groupid':gid,'date_range':{k:dates[k] for k in ('start','end')},'src_sha256':sha256(source),'download_verified':True,'account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','transport_proof':{'safety_version':'dom-only-20261021-11','safety':'DOM-only','reviewed_extension_ready':True},'page_filtered':0 if zero else 1,'recorded_at':self.clock.wall().isoformat()};r=process(source,company,dates,dest,MAPPING,page_filtered=evidence['page_filtered'],evidence=evidence);self.assertIn(r['status'],('complete','zero_rows'));self.pin(dest/'acquisition.json',evidence)
        return {**company,'groupid':gid,'status':r['status'],'receipt':r['receipt'],'outdir':str(dest),'date_range':dates}
    def order(self):
        day='2026-10-19';dates=compute(day);progress={'version':1,'companies':{}}
        for company in self.rows:
            name=company['company'];entry={'initial_start':dates['start'],'next_start':dates['start'],'covered_through':None,'last_completed_on':None,'planned_runs':{},'completions':[]}
            if name in self.covered:
                row=self.make_row(self.root/'prior',company,dates);entry.update(next_start=day,covered_through=dates['end'],completions=[{'start':dates['start'],'end':dates['end'],'receipt':row['receipt'],'receipt_sha256':sha256(row['receipt'])}])
            progress['companies'][name]=entry
        pp=self.root/'progress.json';self.pin(pp,progress);snapshot=self.pin(self.root/'snapshot-progress.json',progress);progress_summary={}
        for name,v in progress['companies'].items():progress_summary[name]={**{k:v.get(k) for k in ('next_start','covered_through','last_completed_on')},'original_plan_ids':[],'original_batch_ids':[],'original_task_ids':[]}
        offer=self.pin(self.root/'offer.json',{'workflow':d.WORKFLOW,'role':d.ROLE,'action':'dispatch','tool':'collaboration.followup_task','dispatch_id':day+':daily-comment-stats:0','ledger_snapshots':[{'workflow':d.WORKFLOW,'company':None,'original_path':str(pp),'snapshot':snapshot,'progress':progress_summary}]});self.order_ref=d.archive(self.archive,offer,t.ref(d.DEFAULT_COMPANIES),origin='fresh');self.execution=w.location(self.order_ref['path']);return self.order_ref
    def batch(self,run_dir,progress):
        dates=compute('2026-10-19');rows=[]
        for company in self.rows:
            if company['company'] in self.covered:rows.append({**company,'status':'skipped','skip_reason':'already_covered','outdir':str(company_dir(run_dir,company)),'date_range':{**dates,'ok':False,'reason':'already_covered','covered_through':dates['end']}})
            else:rows.append(self.make_row(run_dir,company,dates,company['company'] in self.zero))
        batch={'flow':'daily-comment-stats','mode':'agent-live','status':'running','run_dir':str(run_dir),'run_token':'1'*32,'requested_date_range':dates,'date_range':dates,'progress_file':str(progress),'mapping_sha256':sha256(MAPPING),'companies':rows,'roundtrip':{'required':False,'verified':False},'failed':0,'needs_review':0};self.pin(run_dir/'batch_receipt.json',batch);return batch
    def acquire(self):
        w.start(self.order_ref,self.archive,mode='acceptance',clock=self.clock,ports=self.ports);r=w.advance(self.order_ref,self.archive,995698279,clock=self.clock,ports=self.ports);self.assertEqual(r['handoff']['action'],'acquire');self.assertIn('--tab-id',r['handoff']['argv']);self.assertTrue(any(e['kind']=='first-webpage-action-intent' for e in json.loads((self.execution/'timing.json').read_text())['events']));w.advance(self.order_ref,self.archive,995698279,clock=self.clock,ports=self.ports)
    def test_all_companies_seal_before_first_prepare_finish_only_all_confirmed(self):
        self.order();self.acquire();self.clock.n=125;r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertEqual(r['phase'],'complete');self.assertTrue(r['timing']['acceptance_pass']);self.assertEqual(r['timing']['elapsed_seconds'],25);self.assertEqual(len(list(self.jobs.glob('*.json'))),6);self.assertEqual(self.ports.send_calls,1)
        r=w.notify(self.order_ref,self.archive,clock=self.clock,ports=self.ports);self.assertEqual(self.ports.send_calls,1)
    def test_company_already_complete_only_pending_company_sent(self):
        self.covered={self.rows[0]['company']};self.order();self.acquire();r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertTrue(r['timing']['acceptance_pass']);self.assertEqual(len(list(self.jobs.glob('*.json'))),3);self.assertEqual(len(json.loads((self.execution/'delivery-manifest.json').read_text())['company_ranges']),1)
    def test_mixed_zero_sealed_with_actual_acquisition_only_nonzero_company_sent(self):
        self.zero={self.rows[0]['company']};self.order();self.acquire();r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertTrue(r['timing']['acceptance_pass']);manifest=json.loads((self.execution/'delivery-manifest.json').read_text());self.assertEqual(len(manifest['zero_acquisitions']),1);self.assertEqual(len(list(self.jobs.glob('*.json'))),3)
    def test_all_zero_real_sources_complete_no_send_success_no_sender(self):
        self.zero={r['company'] for r in self.rows};self.order();self.acquire();r=w.notify(self.order_ref,self.archive,clock=self.clock,ports=self.ports);self.assertEqual(r['timing']['outcome'],'no-data-complete');self.assertFalse(r['timing']['acceptance_pass']);self.assertEqual(self.ports.send_calls,0);self.assertFalse(self.jobs.exists())
    def test_repeated_start_keeps_clock_no_replan_and_unknown_never_resends(self):
        self.order();self.acquire();self.clock.n=111;r=w.start(self.order_ref,self.archive,mode='acceptance',clock=self.clock,ports=self.ports);self.assertEqual(r['timing']['elapsed_seconds'],11);self.assertEqual(self.ports.init_calls,1);self.ports.unknown=True;r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertFalse(r['timing']['acceptance_pass']);self.assertEqual(r['phase'],'notification-pending');original=self.ports.send_calls;r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertEqual(len(list(self.jobs.glob('*.json'))),1);self.assertEqual(json.loads(next(self.jobs.glob('*.json')).read_text())['status'],'unknown');self.assertEqual(self.ports.actual_sends,1)
    def test_order_validation_cost_counted_and_preexisting_complete_not_adopted_fresh(self):
        self.order();original=d.validate
        def slow(*a,**kw):self.clock.n+=3;return original(*a,**kw)
        with patch.object(d,'validate',side_effect=slow):r=w.start(self.order_ref,self.archive,clock=self.clock,ports=self.ports)
        ts=json.loads((self.execution/'timing.json').read_text());self.assertEqual(ts['start_monotonic'],100);self.assertGreaterEqual(r['timing']['elapsed_seconds'],6)
    def test_crash_after_timing_finish_recovers_without_second_send(self):
        self.order();self.acquire();r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);state=json.loads((self.execution/'state.json').read_text());state['phase']='notification-pending';self.pin(self.execution/'state.json',state);count=self.ports.send_calls;r=w.notify(self.order_ref,self.archive,clock=self.clock,ports=self.ports);self.assertEqual(r['phase'],'complete');self.assertEqual(self.ports.send_calls,count)

    def test_existing_completed_business_run_is_not_fresh_adopted(self):
        self.order();run_dir=w.PROJECT/'work'/'2026-10-19'/('daily-timed-'+Path(self.order_ref['path']).stem[:24]);self.pin(run_dir/'batch_receipt.json',{'status':'complete'})
        with self.assertRaisesRegex(ValueError,'business-run-preexists'):w.start(self.order_ref,self.archive,clock=self.clock,ports=self.ports)
        self.assertEqual(self.ports.init_calls,0);self.assertFalse(json.loads((self.execution/'timing.json').read_text())['acceptance_pass'])
    def test_formal_cli_delegates_fixed_original_init_and_advance_without_rerun(self):
        import subprocess
        self.order();order=d.validate(self.order_ref,self.archive);ports=w.FormalPorts();called=[]
        def run(args,**kw):called.append(args);return subprocess.CompletedProcess(args,0,json.dumps({'synthetic_formal_response':True}),'')
        with patch.object(w.subprocess,'run',side_effect=run):ports.init(order,self.root/'run',self.root/'progress.json');ports.advance(self.root/'run')
        self.assertEqual(called[0][2:4],['init','--today']);self.assertEqual(called[0][4],order['day']);self.assertIn('--notification-work-root',called[0]);self.assertNotIn('--rerun',called[0]);self.assertEqual(called[1][2:4],['advance','--run-dir'])
        p=subprocess.run([sys.executable,'-I','-B',w.__file__,'--help'],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertIn('--order-sha256',p.stdout)
    def test_live_progress_change_stops_before_business_init_but_does_not_reset_timer(self):
        self.order();(self.root/'progress.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'progress-changed'):w.start(self.order_ref,self.archive,clock=self.clock,ports=self.ports)
        self.assertEqual(self.ports.init_calls,0);self.assertEqual(json.loads((self.execution/'timing.json').read_text())['start_monotonic'],100)
    def test_explicit_resume_reuses_original_run_and_never_claims_fresh_pass(self):
        self.order();old_order=self.order_ref;w.start(old_order,self.archive,mode='acceptance',clock=self.clock,ports=self.ports);old_state=json.loads((self.execution/'state.json').read_text());original=d.validate(old_order,self.archive);offer=t.pinned(original['offer']);offer['dispatch_id']='2026-10-19:daily-comment-stats:1';offer_ref=self.pin(self.root/'resume-offer.json',offer);self.order_ref=d.archive(self.archive,offer_ref,original['company_config'],origin='resume',resumed_from=old_order);self.execution=w.location(self.order_ref['path']);self.clock.n=110
        with patch.object(self.ports,'init',return_value=json.loads((Path(old_state['run_dir'])/'batch_receipt.json').read_text())):r=w.start(self.order_ref,self.archive,mode='acceptance',clock=self.clock,ports=self.ports)
        self.assertEqual(r['run_dir'],old_state['run_dir']);self.assertEqual(r['timing']['origin'],'resume');w.advance(self.order_ref,self.archive,995698279,clock=self.clock,ports=self.ports);w.advance(self.order_ref,self.archive,995698279,clock=self.clock,ports=self.ports);r=w.notify(self.order_ref,self.archive,steps=100,clock=self.clock,ports=self.ports);self.assertEqual(r['phase'],'complete');self.assertFalse(r['timing']['acceptance_pass']);self.assertFalse(r['timing']['full_workflow_measured'])
if __name__=='__main__':unittest.main()
