"""Coverage tests use temporary files and synthetic authenticated receipts only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import openpyxl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from ds_calendar import compute
from ds_common import FlowError,sha256,atomic_json
from ds_workbooks import REQUIRED
from ds_processor import process
from ds_progress import read,record,plan,initialize
from flow import init_run,next_task,save,update_progress

A='烟台一成教育文化咨询有限公司'
B='上海老芗汇餐饮管理有限公司'
IDENTITY={'provider':'测试服务商','account_id':'123456789','manager':'测试经理'}

class ProgressTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.progress=self.root/'progress/progress.json'
        self.mapping=self.root/'map.csv';self.mapping.write_text('公司名称,企业微信群\n'+A+',测试群1\n')
    def tearDown(self):self.tmp.cleanup()
    def run_on(self,today,name=None,start=None,end=None):
        dates=compute(today,start,end)
        return init_run(dates,self.root/(name or today),self.mapping,progress_file=self.progress)
    def complete(self,state,index=0,count=1,verified=True,commit=True):
        row=state['companies'][index];dates=row['date_range'];src=Path(row['outdir'])/'source.xlsx';src.parent.mkdir(parents=True,exist_ok=True)
        w=openpyxl.Workbook();sheet=w.active;sheet.append(REQUIRED+['extra'+str(i) for i in range(13)])
        for _ in range(count):sheet.append(['门店','测试用户',dates['start']+' 12:00:00',5,'好评',None,None])
        w.save(src);w.close()
        evidence={'company':row['company'],'groupid':row['groupid'],'date_range':{k:dates[k] for k in ('start','end')},
                  'src_sha256':sha256(src),'download_verified':True,'account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,
                  'operator_skill':'douyin-laike-operator','backend':'codex-existing-extension'} if verified else None
        with patch('ds_processor.now',return_value=dates['today']+'T18:00:00+08:00'):
            result=process(src,row,dates,row['outdir'],self.mapping,count,evidence)
        row.update(status=result['status'],receipt=result['receipt']);save(state)
        if commit:update_progress(state,row)
        return result
    def entry(self,company=A):return read(self.progress)['companies'][company]
    def test_first_monday_then_tuesday_and_completion_date(self):
        monday=self.run_on('2026-10-19');self.assertEqual(next_task(monday)['date_range']['start'],'2026-10-16')
        self.complete(monday)
        entry=self.entry();self.assertEqual(entry['covered_through'],'2026-10-18');self.assertEqual(entry['last_completed_on'],'2026-10-19')
        self.assertEqual(entry['last_run_date'],'2026-10-19')
        task=next_task(self.run_on('2026-10-20'));self.assertEqual((task['date_range']['start'],task['date_range']['end']),('2026-10-19','2026-10-19'))
    def test_forgot_monday_and_tuesday_catches_up_from_friday(self):
        friday=self.run_on('2026-10-16');self.complete(friday)
        task=next_task(self.run_on('2026-10-21'))
        self.assertEqual((task['date_range']['start'],task['date_range']['end'],task['date_range']['end_exclusive']),('2026-10-16','2026-10-20','2026-10-21'))
        self.assertEqual(task['date_range']['days'],5)
    def test_company_failures_do_not_skip_each_others_backlog(self):
        self.mapping.write_text('公司名称,企业微信群\n'+A+',测试群1\n'+B+',测试群2\n')
        friday=self.run_on('2026-10-16');self.complete(friday,0);self.complete(friday,1)
        monday=self.run_on('2026-10-19');self.complete(monday,0)
        monday['companies'][1]['status']='failed';save(monday)
        wed=self.run_on('2026-10-21')
        self.assertEqual(wed['companies'][0]['date_range']['start'],'2026-10-19')
        self.assertEqual(wed['companies'][1]['date_range']['start'],'2026-10-16')
        self.assertEqual(wed['date_range']['start'],'2026-10-16')
    def test_first_failed_or_needs_review_run_keeps_its_anchor(self):
        monday=self.run_on('2026-10-19');result=self.complete(monday,verified=False)
        self.assertEqual(result['status'],'needs_review');self.assertIsNone(self.entry()['covered_through'])
        self.assertEqual(next_task(self.run_on('2026-10-21'))['date_range']['start'],'2026-10-16')
    def test_verified_zero_advances_but_unverified_zero_does_not(self):
        monday=self.run_on('2026-10-19');result=self.complete(monday,count=0)
        self.assertEqual(result['status'],'zero_rows');self.assertEqual(self.entry()['covered_through'],'2026-10-18')
        tuesday=self.run_on('2026-10-20');self.complete(tuesday,count=0,verified=False)
        self.assertEqual(self.entry()['covered_through'],'2026-10-18')
        self.assertEqual(next_task(self.run_on('2026-10-21'))['date_range']['start'],'2026-10-19')
    def test_manual_range_cannot_jump_gap_and_filling_gap_merges(self):
        self.run_on('2026-10-19')
        later=self.run_on('2026-10-20','manual-later','2026-10-19','2026-10-19');self.complete(later)
        self.assertIsNone(self.entry()['covered_through']);self.assertEqual(self.entry()['next_start'],'2026-10-16')
        fill=self.run_on('2026-10-21','manual-fill','2026-10-16','2026-10-18');self.complete(fill)
        self.assertEqual(self.entry()['covered_through'],'2026-10-19');self.assertEqual(self.entry()['next_start'],'2026-10-20')
        size=len(self.entry()['completions']);update_progress(fill,fill['companies'][0]);self.assertEqual(len(self.entry()['completions']),size)
    def test_same_day_repeated_init_keeps_frozen_batch_then_new_plan_skips(self):
        monday=self.run_on('2026-10-19');self.complete(monday)
        same=self.run_on('2026-10-19');self.assertEqual(same['run_token'],monday['run_token'])
        self.assertEqual(next_task(same)['action'],'done')
        another=self.run_on('2026-10-19','another');self.assertEqual(next_task(another)['action'],'done')
        self.assertEqual(another['companies'][0]['skip_reason'],'already_covered')
    def test_unsynced_export_intent_blocks_new_batch(self):
        monday=self.run_on('2026-10-19');row=monday['companies'][0]
        atomic_json(Path(row['outdir'])/'operator/test/workflow.json',{'exportPending':True,'state':'running'})
        with self.assertRaisesRegex(FlowError,'Resume previous run'):self.run_on('2026-10-21')
        self.assertIsNone(self.entry()['covered_through'])
    def test_invalid_artifacts_never_advance(self):
        monday=self.run_on('2026-10-19');result=self.complete(monday,commit=False)
        Path(result['outputs'][1]).write_bytes(b'broken')
        with self.assertRaisesRegex(FlowError,'progress-receipt-invalid'):update_progress(monday,monday['companies'][0])
        self.assertIsNone(self.entry()['covered_through'])
    def test_crash_between_receipt_and_cursor_is_recovered_by_next(self):
        monday=self.run_on('2026-10-19');self.complete(monday,commit=False)
        self.assertIsNone(self.entry()['covered_through']);self.assertEqual(next_task(monday)['action'],'done')
        self.assertEqual(self.entry()['covered_through'],'2026-10-18')
    def test_today_is_excluded_even_for_manual_live_range(self):
        with self.assertRaisesRegex(FlowError,'today-excluded'):self.run_on('2026-10-20','future','2026-10-19','2026-10-20')
    def test_explicit_initial_backlog_is_not_a_completion(self):
        initialize(self.progress,A,'2026-10-16')
        self.assertIsNone(self.entry()['covered_through'])
        self.assertEqual(self.entry()['completions'],[])
        self.assertEqual(next_task(self.run_on('2026-10-21'))['date_range']['start'],'2026-10-16')
        with self.assertRaises(FlowError):initialize(self.progress,A,'2026-10-19')
    def test_corrupt_ledger_fails_closed(self):
        self.progress.parent.mkdir(parents=True);self.progress.write_text('{broken')
        with self.assertRaises(ValueError):self.run_on('2026-10-19')

if __name__=='__main__':unittest.main()
