import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import date,datetime
from unittest.mock import patch
import csv

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ds_calendar import compute
from ds_common import (FlowError,load_map,match_name,sha256,company_dir,atomic_json,lock)
from ds_workbooks import REQUIRED,category,CATEGORIES,rating,load_reviews
from ds_processor import process
from batch_run import batch
from flow import init_run,next_task,checkpoint,record_source,fail_company
import openpyxl

A='烟台一成教育文化咨询有限公司'
B='上海老芗汇餐饮管理有限公司'
IDENTITY={'provider':'服务商测试','account_id':'123456789','manager':'测试经理'}

def workbook(path,rows):
    w=openpyxl.Workbook();s=w.active;s.append(REQUIRED+['门店ID', '门店备注名', '门店所在省份', '门店所在城市', '门店所在区域', '用户等级', '是否为消费后评价', '评价来源', '商品ID', '消费商品', '商家是否回复', '商家回复内容', '商家回复时间'])
    for row in rows:s.append(row)
    w.save(path);w.close()

def review(star=5,text='文字',image='图片',video=None,day='2026-10-17 12:00:00',store='测试门店'):
    return [store,'测试用户',day,star,text,image,video]

class CalendarTest(unittest.TestCase):
    def test_monday(self):
        r=compute('2026-10-19');self.assertEqual((r['start'],r['end'],r['end_exclusive']),('2026-10-16','2026-10-18','2026-10-19'))
    def test_tuesday(self):self.assertEqual(compute('2026-10-20')['end'],'2026-10-19')
    def test_makeup_saturday(self):
        self.assertEqual(compute('2026-10-10')['start'],'2026-10-09')
        self.assertEqual(compute('2026-10-12')['start'],'2026-10-10')
    def test_after_holiday(self):self.assertEqual(compute('2026-10-08')['start'],'2026-09-30')
    def test_non_workday_and_force(self):
        self.assertFalse(compute('2026-10-18')['ok'])
        self.assertEqual(compute('2026-10-18',force=True)['start'],'2026-10-16')
    def test_manual(self):
        self.assertEqual(compute('2026-10-18','2026-10-16','2026-10-18')['days'],3)
        for start,end in [('2026-10-17',None),('2026-10-19','2026-10-16')]:
            with self.assertRaises(ValueError):compute('2026-10-20',start,end)
    def test_uncovered_calendar_warns(self):
        self.assertTrue(compute('2027-02-02')['warnings'])

class MappingTest(unittest.TestCase):
    def test_matching(self):
        self.assertEqual(match_name('烟台 一成教育文化咨询（有限公司）',[A,B]),A)
        self.assertEqual(match_name('烟台一成',[A,B]),A)
    def test_ambiguous_or_missing(self):
        for value in ['上海','不存在']:
            with self.assertRaises(FlowError):match_name(value,[A,B,'上海另一家公司'])
    def test_duplicate_mapping_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'map.csv';p.write_text('公司名称,企业微信群\n甲有限公司,群1\n甲有限公司,群2\n')
            with self.assertRaises(FlowError):load_map(p)

class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        progress_patch=patch('flow.DEFAULT_PROGRESS',self.root/'progress.json');progress_patch.start();self.addCleanup(progress_patch.stop)
        self.src=self.root/'source.xlsx';self.out=self.root/'out';self.map=self.root/'map.csv'
        self.map.write_text('公司名称,企业微信群\n'+A+',群1\n'+B+',群2\n')
        self.company=load_map(self.map)[0];self.dates=compute('2026-10-19')
    def tearDown(self):self.tmp.cleanup()
    def run_stats(self,rows,**kwargs):
        workbook(self.src,rows)
        return process(self.src,self.company,self.dates,self.out,self.map,**kwargs)
    def evidence(self):
        return {'company':A,'groupid':'1767942028615694','date_range':{'start':'2026-10-16','end':'2026-10-18'},'src_sha256':sha256(self.src),'download_verified':True,'account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,'operator_skill':'douyin-laike-operator','backend':'codex-existing-extension'}
class FilesTest(Fixture):
    def test_all_categories_and_reconcile(self):
        rows=[review(s,t,i,v) for s in [5,2] for t,i,v in [('文','图',None),(None,None,None),('文',None,None),(None,'图',None),('文','图','视频')]]
        result=self.run_stats(rows,page_filtered=10)
        self.assertEqual(result['summary']['good'],5);self.assertEqual(result['summary']['bad'],5)
        self.assertTrue(result['send_blocked']);self.assertEqual(result['status'],'needs_review')
        stats=next(p for p in result['outputs'] if '评价统计_' in p)
        w=openpyxl.load_workbook(stats);s=w['按门店每日明细'];headers=[c.value for c in s[1]]
        self.assertEqual(s.cell(2,headers.index('差评反馈总数')+1).value,5)
        self.assertEqual(s.cell(2,headers.index('中间态合计')+1).value,6)
        self.assertEqual(s.freeze_panes,'C2');w.close()
        self.assertEqual(sha256(self.src),result['artifacts'][0]['sha256'])
    def test_video_priority_and_rating(self):
        self.assertEqual(category('文','图','视频',3),'有视频内容差评')
        for value in [0,6,'超赞',None,4.5]:
            with self.assertRaises(FlowError):rating(value)
        self.assertEqual(rating(4.0),4);self.assertEqual(rating('5星'),5)
    def test_complete_provenance(self):
        workbook(self.src,[review()]);ev=self.evidence()
        result=process(self.src,self.company,self.dates,self.out,self.map,1,ev)
        self.assertEqual(result['status'],'complete');self.assertTrue(result['send_blocked'])
    def test_zero_no_output_and_receipt(self):
        result=self.run_stats([],page_filtered=0)
        self.assertEqual(result['status'],'zero_rows');self.assertEqual(result['outputs'],[])
        self.assertTrue((self.out/'receipt.json').exists());self.assertEqual(list(self.out.glob('*.xlsx')),[])
    def test_page_mismatch(self):
        result=self.run_stats([review()],page_filtered=99)
        self.assertTrue(result['mismatch']);self.assertEqual(result['status'],'needs_review')
    def test_invalid_rating_and_date_fail(self):
        for row in [review(star=0),review(day='2026-10-19 00:00:00'),review(day='bad date')]:
            result=self.run_stats([row]);self.assertEqual(result['status'],'failed');self.assertFalse(result['outputs'])
    def test_missing_schema(self):
        w=openpyxl.Workbook();w.active.append(['门店名称']);w.save(self.src);w.close()
        r=process(self.src,self.company,self.dates,self.out,self.map)
        self.assertEqual(r['error']['code'],'source-schema')
    def test_source_formula_rejected(self):
        result=self.run_stats([review(text='=1+1')]);self.assertEqual(result['error']['code'],'source-formula')
    def test_idempotence_and_changed_input(self):
        first=self.run_stats([review()],page_filtered=1)
        paths={p:Path(p).stat().st_mtime_ns for p in first['outputs']}
        second=process(self.src,self.company,self.dates,self.out,self.map,1)
        self.assertEqual(second['action'],'skipped');self.assertEqual(paths,{p:Path(p).stat().st_mtime_ns for p in first['outputs']})
        third=self.run_stats([review(),review(star=1)],page_filtered=2)
        self.assertEqual(third['row_count'],2);self.assertTrue(list((self.out/'history').glob('*/receipt.json')))
    def test_tampered_output_regenerated(self):
        r=self.run_stats([review()],page_filtered=1);Path(r['outputs'][1]).write_bytes(b'bad')
        again=process(self.src,self.company,self.dates,self.out,self.map,1)
        self.assertNotEqual(again.get('action'),'skipped');self.assertEqual(again['row_count'],1)
    def test_zero_rerun_removes_prior_published_artifacts(self):
        self.run_stats([review()],page_filtered=1)
        result=self.run_stats([],page_filtered=0)
        self.assertEqual(result['status'],'zero_rows');self.assertEqual(list(self.out.glob('*.xlsx')),[])
    def test_corrupt_receipt_recovers_without_skipping(self):
        self.run_stats([review()],page_filtered=1)
        (self.out/'receipt.json').write_text('{broken')
        result=process(self.src,self.company,self.dates,self.out,self.map,1)
        self.assertEqual(result['row_count'],1);self.assertNotEqual(result.get('action'),'skipped')
        self.assertTrue(list((self.out/'history').glob('*/receipt.corrupt.json')))
    def test_source_column_drift_requires_review(self):
        w=openpyxl.Workbook();w.active.append(REQUIRED);w.active.append(review());w.save(self.src);w.close()
        result=process(self.src,self.company,self.dates,self.out,self.map,1,self.evidence())
        self.assertEqual(result['status'],'needs_review');self.assertTrue(any('column-count' in x for x in result['warnings']))
    def test_wrong_company_provenance_stops(self):
        workbook(self.src,[review()]);ev=self.evidence();ev['groupid']='1764303851132943'
        result=process(self.src,self.company,self.dates,self.out,self.map,1,ev)
        self.assertTrue(result['error']['fatal']);self.assertEqual(result['status'],'failed')
    def test_lock_rejects_second_writer(self):
        with lock(self.out):
            with self.assertRaises(FlowError):
                with lock(self.out):pass
    def test_offline_batch_isolation_and_zero(self):
        source=self.root/'sources';source.mkdir()
        workbook(source/(A+'.xlsx'),[review()]);workbook(source/(B+'.xlsx'),[])
        result=batch(source,self.dates,self.root/'batch',self.map)
        self.assertEqual(result['needs_review'],1);self.assertEqual(result['skipped'],1)
        self.assertEqual(result['failed'],0)
        second=batch(source,self.dates,self.root/'batch',self.map)
        self.assertEqual(second['results'][0]['action'],'skipped')
    def test_batch_ambiguous_source_never_picks_latest(self):
        source=self.root/'sources';source.mkdir()
        workbook(source/(A+'.xlsx'),[review()]);workbook(source/('评价明细_'+A+'_1016-1018.xlsx'),[review()])
        result=batch(source,self.dates,self.root/'batch',self.map)
        self.assertEqual(result['results'][0]['status'],'skipped')

class FlowTest(Fixture):
    def test_live_handoff_and_resume(self):
        state=init_run(self.dates,self.root/'live',self.map)
        row=state['companies'][0];self.assertEqual(next_task(state)['operator_skill'],'douyin-laike-operator')
        checkpoint(state,row,{'stage':'identity','identity':IDENTITY})
        checkpoint(state,row,{'stage':'switch','groupid':row['groupid'],'identity':IDENTITY})
        checkpoint(state,row,{'stage':'filter','date_range':{'start':'2026-10-16','end':'2026-10-18'},'page_filtered':1})
        checkpoint(state,row,{'stage':'export-intent'})
        checkpoint(state,row,{'stage':'navigation'})
        with self.assertRaises(FlowError):checkpoint(state,row,{'stage':'export-intent'})
        workbook(self.src,[review()])
        checkpoint(state,row,{'stage':'export-generated'})
        checkpoint(state,row,{'stage':'download-intent'})
        checkpoint(state,row,{'stage':'download-complete'})
        record_source(state,row,{'company':A,'groupid':row['groupid'],'source':str(self.src),'date_range':{'start':'2026-10-16','end':'2026-10-18'},'download_verified':True,'account_verified':True,'page_filtered':1,'identity':IDENTITY,'identity_before':IDENTITY,'operator_skill':'douyin-laike-operator','backend':'codex-existing-extension'})
        self.assertEqual(next_task(state)['action'],'process')
        rec=process(row['source'],row,state['date_range'],row['outdir'],self.map,1,row['evidence'])
        row['status']=rec['status'];self.assertEqual(next_task(state)['company'],B)
    def test_risk_halts_batch(self):
        for code in ['risk-prompt','connection-unavailable']:
            with self.subTest(code=code):
                state=init_run(self.dates,self.root/('live-'+code),self.map)
                fail_company(state,state['companies'][0],code)
                self.assertEqual(next_task(state)['action'],'halted')
                self.assertEqual(state['halt_reason']['code'],code)
    def test_one_company_failure_continues(self):
        state=init_run(self.dates,self.root/'live',self.map)
        fail_company(state,state['companies'][0],'download-timeout')
        self.assertEqual(next_task(state)['company'],B)
    def test_unconfigured_company_is_skipped_not_guessed(self):
        self.map.write_text('公司名称,企业微信群\n未配置公司,群0\n'+A+',群1\n'+B+',群2\n')
        state=init_run(self.dates,self.root/'live',self.map)
        self.assertEqual(state['companies'][0]['status'],'skipped')
        self.assertEqual(next_task(state)['company'],A)
        self.assertEqual(state['roundtrip']['target_company'],A)
    def test_mapping_change_requires_new_run(self):
        state=init_run(self.dates,self.root/'live',self.map)
        self.map.write_text('公司名称,企业微信群\n'+A+',新群\n')
        from flow import load_state
        with self.assertRaises(FlowError):load_state(state['run_dir'])



class DeterministicFlowTest(Fixture):
    def test_checkpoints_cannot_skip_dependencies(self):
        state=init_run(self.dates,self.root/'live',self.map);row=state['companies'][0]
        for stage in ['switch','filter','export-submitted','export-generated','download-intent','download-complete']:
            with self.subTest(stage=stage),self.assertRaises(FlowError):checkpoint(state,row,{'stage':stage})
        self.assertEqual(row['checkpoints'],[])

    def test_source_cannot_skip_download_checkpoint(self):
        state=init_run(self.dates,self.root/'live',self.map)
        with self.assertRaisesRegex(FlowError,'download-checkpoint-missing'):record_source(state,state['companies'][0],{})

    def test_work_order_is_stable_and_new_run_is_isolated(self):
        from flow import dispatch
        state=init_run(self.dates,self.root/'live',self.map)
        a=dispatch(state);b=dispatch(state)
        self.assertEqual(a['work_order_id'],b['work_order_id']);self.assertEqual(a['workflow_path'],b['workflow_path'])
        rerun=init_run(self.dates,self.root/'live',self.map,rerun=True)
        self.assertNotEqual(a['workflow_path'],dispatch(rerun)['workflow_path'])

    def test_rerun_checks_unsynced_browser_journal(self):
        from flow import dispatch
        state=init_run(self.dates,self.root/'live',self.map);task=dispatch(state)
        atomic_json(task['workflow_path'],{'state':'running','exportPending':True})
        with self.assertRaisesRegex(FlowError,'Unresolved operator journal'):init_run(self.dates,self.root/'live',self.map,rerun=True)

    def test_failed_journal_is_imported_and_connection_halts_correct_company(self):
        from flow import dispatch,advance
        state=init_run(self.dates,self.root/'live',self.map)
        fail_company(state,state['companies'][0],'company-not-found')
        task=dispatch(state)
        atomic_json(task['workflow_path'],{'work_order_id':task['work_order_id'],'company':B,'groupid':task['groupid'],
                    'state':'failed','error_code':'connection-unavailable','error':'Debugger unattached','checkpoints':[]})
        self.assertEqual(advance(state)['action'],'halted')
        self.assertEqual(state['companies'][0]['status'],'skipped');self.assertEqual(state['companies'][1]['status'],'failed')

    def test_connection_recovery_redispatches_same_workorder(self):
        from flow import dispatch,advance,request_connection_retry
        state=init_run(self.dates,self.root/'retry-live',self.map);job=dispatch(state)
        journal={'work_order_id':job['work_order_id'],'company':job['company'],'groupid':job['groupid'],
                 'state':'failed','error_code':'connection-unavailable','error':'Debugger unattached','checkpoints':[],
                 'exportPending':False,'downloadPending':False}
        atomic_json(job['workflow_path'],journal)
        self.assertEqual(advance(state)['action'],'halted')
        retried=request_connection_retry(state)
        self.assertEqual(retried['work_order_id'],job['work_order_id'])
        self.assertEqual(retried['workflow_path'],job['workflow_path'])
        self.assertEqual(retried['recovery_request']['kind'],'connection-recovery')
        self.assertEqual(advance(state)['action'],'acquire')
        self.assertEqual(json.loads(Path(job['workflow_path']).read_text())['state'],'failed')
    def test_connection_retry_refuses_unknown_download(self):
        from flow import dispatch,advance,request_connection_retry
        state=init_run(self.dates,self.root/'download-retry',self.map);job=dispatch(state)
        atomic_json(job['workflow_path'],{'work_order_id':job['work_order_id'],'company':job['company'],'groupid':job['groupid'],
                    'state':'failed','error_code':'connection-unavailable','checkpoints':[],'downloadPending':True})
        advance(state)
        with self.assertRaisesRegex(FlowError,'Reconcile existing download'):request_connection_retry(state)
        self.assertEqual(state['status'],'halted')
    def test_connection_retry_never_clears_risk_or_account_fault(self):
        from flow import request_connection_retry
        for code in ('risk-prompt','account-changed','captcha'):
            state=init_run(self.dates,self.root/('risk-'+code),self.map)
            fail_company(state,state['companies'][0],code)
            with self.assertRaises(FlowError):request_connection_retry(state)
            self.assertEqual(state['status'],'halted')

if __name__=='__main__':unittest.main()
