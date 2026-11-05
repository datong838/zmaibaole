"""Synthetic artifact regression only; never initializes or sends a live workflow."""
import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

SKILL=Path(__file__).resolve().parents[1]
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'


class ReportStageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name)
        cls.stage='已生效：警告\n待生效（待扣，尚未扣除）：信用分-6分\n已结束：推荐流量限制\n待生效：商品展示调整'
        cls.row={'notice_id':'202610204776378817','date':'2026-10-20','subject':'模拟门店','reason':'模拟原因','object_type':'模拟对象','object_name':'模拟对象名称','actions':['警告','信用分扣分'],'table_disposal':'原列表：警告与信用分扣分','table_effectiveness_status':'原列表状态','effectiveness_status':'详情状态不能覆盖列表','rectification_status':'-','disposal_stage_text':cls.stage,'public_recommendation':'模拟建议'}
        cls.data={'company':'明确模拟排版回归','mode':'fixture','start':'2026-10-20','end_exclusive':'2026-10-21','total':1,'analysis':[{'violation_type':'模拟原因','object_types':['模拟对象'],'count':1}],'records':[cls.row],'source':{'sha256':'a'*64}}
        cls.input=cls.root/'build-input.json';cls.input.write_text(json.dumps(cls.data,ensure_ascii=False));cls.out=cls.root/'artifacts'
        result=subprocess.run([str(NODE),str(SKILL/'scripts/build-report.mjs'),str(cls.input),str(cls.out)],capture_output=True,text=True,timeout=120)
        if result.returncode:raise AssertionError(result.stderr)
        cls.book=load_workbook(cls.out/'违规汇总.xlsx',read_only=False,data_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.book.close();cls.tmp.cleanup()

    def test_table_literals_are_preserved_and_pending_stage_is_separate(self):
        sheet=self.book['违规记录表']
        self.assertEqual([c.value for c in sheet[3]],['违规日期','处置主体（门店/公司原名）','违规原因','违规对象','处置方式','生效状态','整改状态','通知书ID','处置分项状态'])
        self.assertEqual(sheet['E4'].value,self.row['table_disposal']);self.assertEqual(sheet['F4'].value,self.row['table_effectiveness_status']);self.assertEqual(sheet['I4'].value,self.stage)
        self.assertIn('待扣，尚未扣除',sheet['I4'].value)

    def test_notice_id_xlsx_text_format_and_dash_placeholder_are_exact(self):
        sheet=self.book['违规记录表'];self.assertEqual(sheet['H4'].value,self.row['notice_id']);self.assertIsInstance(sheet['H4'].value,str)
        self.assertEqual(sheet['H4'].number_format,'@','native workbook IDs are text; PNG appearance additionally requires visual review')
        self.assertEqual(sheet['G4'].value,'-','platform placeholder must not acquire an apostrophe')

    def test_newline_height_and_full_image_row_coverage(self):
        sheet=self.book['违规记录表'];required_lines=sum(max(1,math.ceil(len(line)/30)) for line in self.stage.split('\n'))
        self.assertGreaterEqual(sheet.row_dimensions[4].height,required_lines*16+16,'all explicit lines must fit, not just the longest line')
        images=json.loads((self.out/'artifacts.json').read_text())['files'];records=[r for r in images if r['kind']=='records_image'];self.assertEqual([(r['first_row'],r['last_row'],r['total_rows']) for r in records],[(1,1,1)]);self.assertTrue(records[0]['headers_repeated'])
        self.assertEqual(self.book['违规类型汇总']['E5'].value,1)

    def test_copy_does_not_apply_summary_status_to_pending_score(self):
        spec=importlib.util.spec_from_file_location('violation_report_stage_workflow',SKILL/'scripts/workflow.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
        root=self.root/'copy-only';root.mkdir(exist_ok=True);batch='fixture-only'
        state={'mode':'fixture','events':[],'batches':{batch:{'total':1,'send_jobs':{},'source':{'sha256':'a'*64},'records':[self.row]}}}
        p=root/'copy-input.json';p.write_text(json.dumps({'source_sha256':'a'*64,'agent_reviewed':True,'facts_preserved':True,'no_internal_rules':True,'items':[{'notice_id':self.row['notice_id'],'gentle_reason':'模拟反馈，仅用于代码验证。','recommendation':'模拟建议，仅核表达结构。'}]},ensure_ascii=False))
        w.set_copy(root,state,batch,p);text=Path(state['batches'][batch]['copy']['path']).read_text()
        self.assertIn('处置方式：警告；信用分扣分\n    处置状态：',text);self.assertIn('待扣，尚未扣除',text);self.assertNotIn('信用分扣分（详情状态不能覆盖列表）',text)


if __name__=='__main__':unittest.main()
