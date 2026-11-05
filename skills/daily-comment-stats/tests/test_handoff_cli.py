"""Two physical skills over JSON/CLI, fixtures only; never touches browser/user exports."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import openpyxl

SKILL=Path(__file__).resolve().parents[1]
FLOW=SKILL/'scripts/flow.py'
OP=SKILL.parent/'douyin-laike-operator/scripts/role_cli.py'
IDENTITY={'provider':'服务商测试','account_id':'123456789','manager':'测试经理'}

class HandoffCLI(unittest.TestCase):
    def test_two_company_full_handoff_zero_resume_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);run=root/'run';notification_work=root/'work';notification_work.mkdir()
            def command(script,*args):
                if script==FLOW and args and args[0]=='init':args=(*args,'--notification-work-root',notification_work)
                r=subprocess.run([sys.executable,str(script),*map(str,args)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
                return json.loads(r.stdout)
            def datafile(name,value):
                p=root/name;p.write_text(json.dumps(value,ensure_ascii=False));return p
            state=command(FLOW,'init','--today','2026-10-19','--outdir',run,'--export-dir',root/'exports','--progress-file',root/'progress.json')
            self.assertEqual(state['date_range']['end'],'2026-10-18');self.assertEqual(state['backend'],'local-dom-bridge')
            for index,count in enumerate([2,0]):
                task=command(FLOW,'advance','--run-dir',run)
                self.assertEqual(task['action'],'acquire')
                company=task['company']
                taskfile=datafile('task%d.json'%index,task)
                prepared=command(OP,'prepare','--work-order',taskfile,'--tab-id','17')
                self.assertEqual(prepared['backend'],'local-dom-bridge');self.assertEqual(task['backend'],'local-dom-bridge');self.assertTrue(task['explicit_tab_id_required'])
                source=root/('download%d.xlsx'%index);wb=openpyxl.Workbook();sheet=wb.active
                sheet.append(['门店名称','用户昵称','评价时间','推荐等级','文本内容','图片内容','视频内容']+['门店ID', '门店备注名', '门店所在省份', '门店所在城市', '门店所在区域', '用户等级', '是否为消费后评价', '评价来源', '商品ID', '消费商品', '商家是否回复', '商家回复内容', '商家回复时间'])
                for n in range(count):sheet.append(['公司%d测试门店'%index,'测试用户','2026-10-17 12:00:00',5 if n==0 else 2,'文',None,None])
                wb.save(source);wb.close()
                candidate={'company':company,'groupid':task['groupid'],'source':str(source),'date_range':{'start':'2026-10-16','end':'2026-10-18'},'identity':IDENTITY,'identity_before':IDENTITY,'account_verified':True,'page_filtered':count,'record_url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid='+task['groupid']}
                stages=[{'stage':'identity','identity':IDENTITY},
                        {'stage':'switch','groupid':task['groupid'],'identity':IDENTITY},
                        {'stage':'navigation'},
                        {'stage':'filter','date_range':task['date_range'],'page_filtered':count},
                        {'stage':'export-intent'},{'stage':'export-submitted'},
                        {'stage':'export-generated','generated_at':'2026-10-20 18:00:00'},
                        {'stage':'download-intent'},{'stage':'download-complete'}]
                stages[3]['date_range']={k:task['date_range'][k] for k in ('start','end')}
                for n,event in enumerate(stages):event['event_id']='fixture-%d-%d'%(index,n)
                journal={'state':'complete','phase':'done','work_order_id':task['work_order_id'],
                         'company':company,'groupid':task['groupid'],'date_range':candidate['date_range'],
                         'checkpoints':stages,'result':candidate}
                datafile_path=Path(task['workflow_path']);datafile_path.write_text(json.dumps(journal,ensure_ascii=False))
                # One command imports checkpoints, verifies the real fixture XLSX and processes it.
                command(FLOW,'advance','--run-dir',run)
                result=json.loads((Path(task['output_dir'])/'receipt.json').read_text())
                self.assertEqual(result['status'],'complete' if count else 'zero_rows');self.assertTrue(result['send_blocked'])
                if count:self.assertEqual(result['summary']['bad'],1)
                else:self.assertEqual(list(Path(task['output_dir']).glob('*.xlsx')),[])
            task=command(FLOW,'next','--run-dir',run)
            self.assertEqual(task['action'],'return-company')
            Path(task['workflow_path']).write_text(json.dumps({'state':'complete','phase':'done',
                'work_order_id':task['work_order_id'],'company':task['company'],'groupid':task['groupid'],
                'checkpoints':[{'stage':'identity','identity':IDENTITY,'event_id':'return-identity'},{'stage':'switch','identity':IDENTITY,'groupid':task['groupid'],'event_id':'return-switch'}],'result':{'verified':True,'company':task['company'],'groupid':task['groupid'],'identity':IDENTITY}}))
            done=command(FLOW,'advance','--run-dir',run);self.assertEqual(done['action'],'done');self.assertEqual(done['summary']['succeeded'],1);self.assertEqual(done['summary']['skipped'],1)
            command(FLOW,'init','--today','2026-10-19','--outdir',run,'--progress-file',root/'progress.json')
            self.assertEqual(command(FLOW,'next','--run-dir',run)['action'],'done')
            stats=next(run.glob('01_*/*评价统计*.xlsx'));stats.write_bytes(b'corrupted')
            repair=command(FLOW,'next','--run-dir',run);self.assertEqual(repair['action'],'repair')
            command(FLOW,'repair','--run-dir',run,'--company',repair['company'])
            regenerated=command(FLOW,'process','--run-dir',run,'--company',repair['company'])
            self.assertEqual(regenerated['status'],'complete')

if __name__=='__main__':unittest.main()
