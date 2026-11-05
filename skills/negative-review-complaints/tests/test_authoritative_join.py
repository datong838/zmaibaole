"""Offline fixtures only; never uses historical Excel as a current acquisition."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import re
from zipfile import ZipFile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import authoritative_join as j

@unittest.skipUnless(importlib.util.find_spec('openpyxl'),'run with daily-comment-stats/.venv/bin/python')
class AuthoritativeJoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.source=self.root/'current.xlsx';self.receipt_path=self.root/'current-receipt.json'
        self.headers=list(j.REQUIRED)+['门店ID','门店备注名','门店所在省份','门店所在城市','门店所在区域','用户等级','是否为消费后评价','评价来源','商品ID','消费商品','商家是否回复','商家回复内容','商家回复时间']
        self.identity={'provider':'测试服务商','account_id':'test-account','manager':'测试经理'}
        self.job={'company':'测试公司','groupid':'123456789','start':'2026-10-19','end_exclusive':'2026-10-21','source_work_order_id':'current-work-order','account_verified':True,'identity':self.identity}
        self.rows=[['测试门店','顾客甲','2026-10-20 10:11:12','2星','完整原文\n仍是原文',None,None]+[None]*13]
        self.rows[0][self.headers.index('消费商品')]='测试水果'
        self.observation={'company':'测试公司','groupid':'123456789','start':'2026-10-19','end_exclusive':'2026-10-21','account_verified':True,'identity':self.identity,'source':'codex-existing-extension',
            'url':'https://life.douyin.com/p/life_comment/management?groupid=123456789','observed_at':'2026-10-21T09:05:00+08:00',
            'negative_filter':'中差评（1-3心）','filter_active':True,'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'},
            'fold_boundary_verified':True,'all_pages_read':True,'filtered_count':1,
            'rows':[{'section':'filtered','store':'测试门店','customer':'顾客甲','text':'完整原文\n仍是原文','text_complete':True,'action':'投诉','date_label':'1天前'}]}
        self.write_source()
    def write_source(self):
        import openpyxl
        wb=openpyxl.Workbook();ws=wb.active;ws.append(self.headers)
        for row in self.rows:ws.append(row)
        wb.save(self.source);wb.close()
        self.receipt={'company':self.job['company'],'groupid':self.job['groupid'],'work_order_id':self.job['source_work_order_id'],
            'date_range':{'start':'2026-10-19','end':'2026-10-20'},'source':str(self.source.resolve()),'src_sha256':j.digest(self.source),'bytes':self.source.stat().st_size,
            'download_verified':True,'source_is_authoritative_export':True,'operator_skill':'douyin-laike-operator','account_verified':True,
            'identity':self.identity,'identity_before':self.identity,'backend':'codex-existing-extension','page_filtered':1,
            'record_url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123456789','recorded_at':'2026-10-21T09:00:00+08:00'}
        self.write_receipt()
    def write_receipt(self):
        self.receipt_path.write_text(json.dumps(self.receipt,ensure_ascii=False),encoding='utf-8');self.receipt_hash=j.digest(self.receipt_path)
    def run_join(self):return j.join(self.job,self.observation,self.receipt_path,self.receipt_hash)
    def test_exact_unique_join_fills_absolute_fields_not_relative_guess(self):
        out=self.run_join();row=out['rows'][0]
        self.assertEqual(row['time'],'2026-10-20T10:11:12+08:00');self.assertEqual(row['date'],'2026-10-20');self.assertEqual(row['stars'],2)
        self.assertTrue(row['review_id'].startswith('verified-tuple-sha256:'))
        self.assertEqual(row['authority']['receipt_sha256'],self.receipt_hash);self.assertEqual(out['authority_binding']['work_order_id'],'current-work-order')
    def test_platform_export_id_preferred(self):
        self.headers+=['评价ID'];self.rows[0]+=['1234567890123456789'];self.write_source()
        row=self.run_join()['rows'][0];self.assertEqual(row['review_id'],'1234567890123456789');self.assertEqual(row['authority']['id_source'],'platform-export')
    def test_folded_reviews_never_join_or_inflate_filtered_total(self):
        self.observation['rows'].append({'section':'folded','store':'不属于本轮','text':'不检查、不匹配','customer':'折叠用户'})
        out=self.run_join();self.assertEqual(len(out['rows']),1);self.assertEqual(out['excluded_folded_count'],1)
    def test_duplicate_export_match_across_dates_is_not_unique(self):
        duplicate=copy.deepcopy(self.rows[0]);duplicate[2]='2026-10-19 12:00:00';self.rows.append(duplicate);self.write_source()
        with self.assertRaisesRegex(j.JoinError,'match-not-unique:2'):self.run_join()
    def test_identical_canonical_tuple_rejected_even_with_distinct_platform_ids(self):
        self.headers+=['评价ID'];self.rows[0]+=['id-1'];duplicate=copy.deepcopy(self.rows[0]);duplicate[-1]='id-2';self.rows.append(duplicate);self.write_source()
        with self.assertRaisesRegex(j.JoinError,'duplicate-export-canonical'):self.run_join()
    def test_repeated_visible_normal_row_rejected(self):
        self.observation['rows']*=2;self.observation['filtered_count']=2
        with self.assertRaisesRegex(j.JoinError,'duplicate-normal-review'):self.run_join()
    def test_partial_body_or_nickname_or_store_never_fuzzy_matches(self):
        for key,value in [('text','完整原文'),('customer','顾客'),('store','测试门')]:
            with self.subTest(key=key):
                original=self.observation['rows'][0][key];self.observation['rows'][0][key]=value
                with self.assertRaisesRegex(j.JoinError,'match-not-unique:0'):self.run_join()
                self.observation['rows'][0][key]=original
    def test_whitespace_normalization_does_not_collapse_interior_text(self):
        self.observation['rows'][0]['text']=' 完整原文\r\n仍是原文 '
        self.assertEqual(len(self.run_join()['rows']),1)
        self.observation['rows'][0]['text']='完整原文 仍是原文'
        with self.assertRaises(j.JoinError):self.run_join()
    def test_positive_rating_cannot_be_complaint(self):
        self.rows[0][3]='4星';self.write_source()
        with self.assertRaisesRegex(j.JoinError,'positive-export'):self.run_join()
    def test_missing_full_body_attestation_stops(self):
        self.observation['rows'][0]['text_complete']=False
        with self.assertRaisesRegex(j.JoinError,'full-text-unverified'):self.run_join()
    def test_old_receipt_or_missing_current_work_order_stops(self):
        self.receipt['work_order_id']='last-week-job';self.write_receipt()
        with self.assertRaisesRegex(j.JoinError,'not-current'):self.run_join()
        self.job.pop('source_work_order_id')
        with self.assertRaisesRegex(j.JoinError,'current-source-work-order-id-required'):self.run_join()
    def test_receipt_hash_and_source_hash_are_both_required(self):
        self.receipt_path.write_text(self.receipt_path.read_text()+' ')
        with self.assertRaisesRegex(j.JoinError,'receipt-hash-mismatch'):self.run_join()
        self.write_receipt();self.source.write_bytes(self.source.read_bytes()+b'changed')
        with self.assertRaisesRegex(j.JoinError,'source-hash-mismatch'):self.run_join()
    def test_company_group_dates_and_identity_are_pinned(self):
        for field,value in [('company','另一公司'),('groupid','999'),('date_range',{'start':'2026-10-18','end':'2026-10-20'}),('identity_before',{'different':True})]:
            with self.subTest(field=field):
                original=copy.deepcopy(self.receipt[field]);self.receipt[field]=value;self.write_receipt()
                with self.assertRaises(j.JoinError):self.run_join()
                self.receipt[field]=original;self.write_receipt()
    def test_non_authoritative_historical_stats_receipt_rejected(self):
        self.receipt.pop('source_is_authoritative_export');self.write_receipt()
        with self.assertRaisesRegex(j.JoinError,'not-authoritative'):self.run_join()
    def test_outside_export_dates_and_date_only_timestamp_rejected(self):
        for timestamp,reason in [('2026-10-18 12:00:00','outside-range'),('2026-10-20','absolute-time-missing')]:
            with self.subTest(timestamp=timestamp):
                self.rows[0][2]=timestamp;self.write_source()
                with self.assertRaisesRegex(j.JoinError,reason):self.run_join()
    def test_literal_fields_only_no_formula_execution(self):
        self.rows[0][4]='=SUM(1,2)';self.write_source()
        with self.assertRaisesRegex(j.JoinError,'formula-not-literal'):self.run_join()
    def test_existing_absolute_fields_must_agree(self):
        self.observation['rows'][0]['stars']=1
        with self.assertRaisesRegex(j.JoinError,'field-conflict:stars'):self.run_join()
    def test_unknown_section_missing_fold_boundary_or_pagination_stops(self):
        for key in ('fold_boundary_verified','all_pages_read'):
            self.observation[key]=False
            with self.assertRaises(j.JoinError):self.run_join()
            self.observation[key]=True
        self.observation['rows'][0]['section']='unknown'
        with self.assertRaisesRegex(j.JoinError,'section-unknown'):self.run_join()
    def test_export_count_is_not_assumed_equal_to_normal_ui_count(self):
        extra=copy.deepcopy(self.rows[0]);extra[1]='另一人';extra[3]=5;self.rows.append(extra);self.write_source()
        self.assertEqual(self.run_join()['authority_binding']['export_rows'],2)
    def test_source_time_timezone_is_canonicalized(self):
        self.rows[0][2]='2026-10-20T02:11:12+00:00';self.write_source()
        self.assertEqual(self.run_join()['rows'][0]['time'],'2026-10-20T10:11:12+08:00')
    def test_numeric_long_platform_id_precision_is_not_trusted(self):
        self.headers+=['评价ID'];self.rows[0]+=[1234567890123456789];self.write_source()
        with self.assertRaisesRegex(j.JoinError,'precision-unsafe'):self.run_join()
    def test_zero_normal_scope_retains_authority_without_inventing_tasks(self):
        self.observation.update(rows=[],filtered_count=0)
        out=self.run_join();self.assertEqual(out['rows'],[]);self.assertEqual(out['authority_binding']['export_rows'],1)

    def test_false_A1_dimension_does_not_truncate_actual_twenty_columns_and_rows(self):
        other=copy.deepcopy(self.rows[0]);other[1]='顾客乙';other[2]='2026-10-20 13:14:15';self.rows.append(other);self.write_source()
        with ZipFile(self.source) as archive:
            entries=[(info,archive.read(info.filename)) for info in archive.infolist()]
        with ZipFile(self.source,'w') as archive:
            for info,data in entries:
                if info.filename=='xl/worksheets/sheet1.xml':data=re.sub(rb'<dimension ref="[^"]+"',b'<dimension ref="A1"',data)
                archive.writestr(info,data)
        self.receipt.update(src_sha256=j.digest(self.source),bytes=self.source.stat().st_size);self.write_receipt()
        exported,headers=j.load_export(self.source,self.job,self.receipt)
        self.assertEqual(len(headers),20);self.assertEqual(len(exported),2);self.assertEqual([r['source_row'] for r in exported],[2,3])
        out=self.run_join();self.assertEqual(out['authority_binding']['export_rows'],2);self.assertEqual(len(out['rows']),1)
    def test_short_data_rows_missing_optional_columns_are_safe(self):
        self.rows[0]=self.rows[0][:7];self.write_source()
        exported,_=j.load_export(self.source,self.job,self.receipt)
        self.assertEqual(exported[0]['product'],'');self.assertEqual(exported[0]['source_row'],2)
    def test_short_missing_required_value_returns_join_error_not_index_error(self):
        self.rows[0]=self.rows[0][:2];self.write_source()
        with self.assertRaisesRegex(j.JoinError,'absolute-time-missing'):j.load_export(self.source,self.job,self.receipt)
    def test_nonempty_unheaded_extra_data_column_is_rejected(self):
        self.rows[0]+=['unexpected-unheaded-data'];self.write_source()
        with self.assertRaisesRegex(j.JoinError,'outside-header'):j.load_export(self.source,self.job,self.receipt)
if __name__=='__main__':unittest.main()
