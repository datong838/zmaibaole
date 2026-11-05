import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile
import xml.etree.ElementTree as ET

CLI=Path(__file__).resolve().parents[1]/'scripts/workflow.py'
class CliTests(unittest.TestCase):
    def test_zero_batch_exports_and_rejected_input_is_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'state'
            def run(*args,ok=True):
                p=subprocess.run([sys.executable,str(CLI),'--root',str(root),*args],text=True,capture_output=True,timeout=120)
                self.assertEqual(p.returncode,0 if ok else 1,p.stdout+p.stderr)
                return json.loads(p.stdout)
            run('init','--company','测试公司','--groupid','123','--mode','fixture','--today','2026-10-20','--start','2026-10-16')
            self.assertTrue((root/'投诉处理结果汇总.xlsx').is_file())
            payload={'account_verified':True,'identity':{'provider':'服务商测试','account_id':'123456789','manager':'测试经理'},'company':'测试公司','groupid':'123','source':'fixture','url':'https://life.douyin.com/?groupid=123',
                     'start':'2026-10-16','end_exclusive':'2026-10-20','observed_at':'2026-10-20T09:00:00+08:00',
                     'negative_filter':'中差评（1-3心）','filter_active':False,
                     'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'},
                     'fold_boundary_verified':True,'all_pages_read':True,'filtered_count':0,'rows':[]}
            src=Path(tmp)/'capture.json';src.write_text(json.dumps(payload))
            run('capture','--input',str(src),'--today','2026-10-20',ok=False)
            state=json.loads((root/'state.json').read_text());self.assertFalse(state['batches'])
            self.assertEqual(state['events'][-1]['type'],'operation-stopped')
            payload['filter_active']=True;src.write_text(json.dumps(payload))
            run('capture','--input',str(src),'--today','2026-10-20')
            run('close','--batch','2026-10-16_2026-10-20')
            state=json.loads((root/'state.json').read_text())
            self.assertEqual(state['next_start'],'2026-10-20');self.assertFalse(state['xlsx_dirty'])
            with ZipFile(root/'投诉处理结果汇总.xlsx') as z:
                ns={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                book=ET.fromstring(z.read('xl/workbook.xml'))
                self.assertEqual([s.attrib['name'] for s in book.findall('x:sheets/x:sheet',ns)],['处理汇总','逐条处理结果','分类判断依据','日期进度','处理记录'])
                sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                count=sheet.find('.//x:c[@r="B9"]/x:v',ns)
                self.assertEqual(float(count.text),0)
                self.assertFalse(sheet.findall('.//x:f',ns))
if __name__=='__main__':unittest.main()
