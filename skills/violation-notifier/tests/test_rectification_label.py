"""Portable actual old/fresh public table trees, no current UI or live refs.
Remaining duration is retained evidence, not stable record identity/deadline.
"""
import copy,hashlib,json,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRIPTS=ROOT/'skills/violation-notifier/scripts';sys.path.insert(0,str(SCRIPTS))
import governance_detail as d
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
class RectificationLabelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.q=json.loads((HERE/'fixtures/rectification-label/query.json').read_bytes());cls.job=json.loads((HERE/'fixtures/rectification-label/job.json').read_bytes());cls.old=json.loads((HERE/'fixtures/rectification-label/original.json').read_bytes());cls.fresh=json.loads((HERE/'fixtures/rectification-label/fresh.json').read_bytes())
 def expected(self):return {k:v for k,v in self.q['pages'][0].items() if k!='observation'}
 def test_actual_110_second_display_change_preserves_source_membership_and_raws(self):
  before=copy.deepcopy((self.q,self.old,self.fresh));self.assertEqual(self.q['rows'][0]['rectification_status'],'待整改 5天18:51:26')
  with patch.object(d,'document',side_effect=AssertionError('no extra clock/receipt/evidence reads')):parsed=d.normal_page(self.fresh['tree'],self.job,self.q)
  self.assertEqual(parsed,self.expected());self.assertIn(self.q['rows'][0],parsed['rows']);self.assertEqual((self.q,self.old,self.fresh),before);self.assertEqual(d.g.records_page(self.fresh['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive'])['rows'][0]['rectification_status'],'待整改 5天18:49:36')
 def test_known_format_splits_label_and_retains_complete_dynamic_display(self):
  for text in ('待整改 5天18:49:36','待整改 0天00:00:00','待整改 100天23:59:59'):
   value=d.pending_rectification_display(text);self.assertEqual(value,{'label':'待整改','remaining_display':text[len('待整改 '):],'original_display':text});self.assertNotIn('deadline',value)
 def test_unknown_format_and_nonstring_have_no_countdown_exception(self):
  for value in (None,True,123,{},'待整改','整改完成','待整改5天18:49:36','待整改 05天18:49:36','待整改 5天24:00:00','待整改 5天18:60:00','待整改 5天18:49:60','待整改 ５天18:49:36','待整改 5天18:49:36\n','待整改 5天18:49:36 extra'):
   with self.subTest(value=value):self.assertIsNone(d.pending_rectification_display(value))
 def test_changed_state_or_unknown_remaining_format_refuses(self):
  raw=d.g.records_page(self.fresh['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive'])
  for value in ('整改完成','已整改','待整改','逾期未整改','待整改 5天24:49:36','待整改 5天18:49','unreviewed'):
   current=copy.deepcopy(raw);current['rows'][0]['rectification_status']=value
   with self.subTest(value=value),patch.object(d.g,'records_page',return_value=current),self.assertRaisesRegex(ValueError,'row-facts-changed'):d.normal_page(self.fresh['tree'],self.job,self.q)
 def test_unknown_old_format_cannot_be_promoted_to_known_pending(self):
  source=copy.deepcopy(self.q);source['pages'][0]['rows'][0]['rectification_status']='待处理 5天18:51:26'
  with self.assertRaisesRegex(ValueError,'row-facts-changed'):d.normal_page(self.fresh['tree'],self.job,source)
 def test_remaining_duration_does_not_assert_identical_deadline_or_need_clocks(self):
  current=d.g.records_page(self.fresh['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);current['rows'][0]['rectification_status']='待整改 6天00:00:00'
  with patch.object(d.g,'records_page',return_value=current):self.assertEqual(d.normal_page(self.fresh['tree'],self.job,self.q),self.expected())
 def test_every_other_stable_business_field_stays_exact(self):
  original=d.g.records_page(self.fresh['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive'])
  for key in ('notice_id','store_name','reason','severity','object','effective_status','disposal','violation_date'):
   current=copy.deepcopy(original);current['rows'][0][key]+=' CHANGED'
   with self.subTest(key=key),patch.object(d.g,'records_page',return_value=current),self.assertRaises(ValueError):d.normal_page(self.fresh['tree'],self.job,self.q)
 def test_total_row_order_and_missing_rows_still_refuse(self):
  original=d.g.records_page(self.fresh['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive'])
  for mode in ('total','order','missing'):
   current=copy.deepcopy(original)
   if mode=='total':current['total']+=1
   elif mode=='order':current['rows'].reverse()
   else:current['rows'].pop()
   with self.subTest(mode=mode),patch.object(d.g,'records_page',return_value=current),self.assertRaisesRegex(ValueError,'coverage-changed'):d.normal_page(self.fresh['tree'],self.job,self.q)
 def test_legacy_unchanged_projection_is_exact(self):self.assertEqual(d.normal_page(self.old['tree'],self.job,self.q),self.expected())
 def test_frozen_source_stays_immutable_and_normalized_rows_equal_original(self):
  import verification_session as verification
  with tempfile.TemporaryDirectory() as t:
   file=Path(t)/'q.json';file.write_text(json.dumps(self.q));before=file.read_bytes()
   with verification.validation_scope():
    source=d.document(d.ref(file));self.assertIsInstance(source,verification.FrozenDict);parsed=d.normal_page(self.fresh['tree'],self.job,source);self.assertIn(source['rows'][0],parsed['rows'])
   self.assertEqual(file.read_bytes(),before)
 def test_public_report_helper_matches_python_exact_format_without_reading_source_files(self):
  source=(SCRIPTS/'build-report.mjs').read_text();helper=next(line for line in source.splitlines() if line.startswith('function rectificationLabel('));values=['待整改 5天18:51:26','待整改 0天00:00:00','整改完成','待整改','-','待整改 05天18:51:26','待整改 5天24:00:00','待整改 5天18:60:00','待整改 5天18:51:60','待整改 5天18:51:26\n','待整改 ５天18:51:26']
  code=helper+"\nconst fs=require('node:fs');const values=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(values.map(rectificationLabel)));";result=subprocess.run([str(NODE),'-e',code],input=json.dumps(values),text=True,capture_output=True,check=True);expected=['待整改' if d.pending_rectification_display(v) else v for v in values];self.assertEqual(json.loads(result.stdout),expected);self.assertIn('rectificationLabel(r.rectification_status),r.notice_id',source)
 def test_real_temp_xlsx_uses_label_while_input_keeps_original_duration(self):
  from openpyxl import load_workbook
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);row={'notice_id':'synthetic-notice','date':'2026-10-21','subject':'模拟门店','reason':'模拟原因','object_type':'门店','object_name':'模拟对象','actions':['警告'],'effectiveness_status':'已生效','rectification_status':'待整改 5天18:51:26'};data={'company':'明确模拟状态回归','mode':'fixture','start':'2026-10-21','end_exclusive':'2026-10-22','total':1,'analysis':[{'violation_type':'模拟原因','object_types':['门店'],'count':1}],'records':[row],'source':{'sha256':'a'*64}};file=root/'input.json';file.write_text(json.dumps(data,ensure_ascii=False));before=file.read_bytes();out=root/'out';script=root/'build-report.mjs';script.write_bytes((SCRIPTS/'build-report.mjs').read_bytes());(root/'node_modules').symlink_to(NODE.parent.parent/'node_modules',target_is_directory=True);result=subprocess.run([str(NODE),str(script),str(file),str(out)],text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stderr);artifacts=json.loads((out/'artifacts.json').read_text());xlsx=next(x['path'] for x in artifacts['files'] if x['kind']=='workbook');book=load_workbook(xlsx);self.assertEqual(book['违规记录表']['G4'].value,'待整改');book.close();self.assertEqual(file.read_bytes(),before);self.assertEqual(json.loads(file.read_text())['records'][0]['rectification_status'],row['rectification_status']);self.assertTrue(any(x['kind']=='records_image' for x in artifacts['files']))
if __name__=='__main__':unittest.main()
