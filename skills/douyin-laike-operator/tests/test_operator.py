import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

spec=importlib.util.spec_from_file_location('operator_role',Path(__file__).resolve().parents[1]/'scripts/role_cli.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class OperatorTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.source=self.root/'browser-download.xlsx'
        with ZipFile(self.source,'w') as z:z.writestr('[Content_Types].xml','fixture');z.writestr('xl/workbook.xml','fixture')
        self.identity={'provider':'服务商测试','account_id':'123456789','manager':'测试经理'}
        self.job={'action':'acquire','company':'测试公司','groupid':'1234','date_range':{'start':'2026-10-16','end':'2026-10-18'},'source_dir':str(self.root/'exports'),'identity_baseline':self.identity}
        self.candidate={'company':'测试公司','groupid':'1234','date_range':self.job['date_range'],'identity':self.identity,'identity_before':self.identity,'account_verified':True,'record_url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=1234','page_filtered':1,'source':str(self.source)}
    def tearDown(self):self.tmp.cleanup()
    def test_finalize_local_file_and_idempotence(self):
        result=m.finalize(self.job,self.candidate,self.root/'receipt.json')
        self.assertTrue(result['download_verified']);self.assertTrue(Path(result['source']).is_file())
        self.assertEqual(m.digest(self.source),result['src_sha256'])
        again=m.finalize(self.job,self.candidate,self.root/'receipt.json');self.assertEqual(result['source'],again['source'])
        self.assertEqual(len(list((self.root/'exports').glob('*.xlsx'))),1)
    def test_wrong_company_group_date_rejected(self):
        for field,value in [('company','另一公司'),('groupid','5678'),('date_range',{'start':'2026-10-19','end':'2026-10-19'})]:
            with self.assertRaises(ValueError):m.finalize(self.job,{**self.candidate,field:value},self.root/'r.json')
    def test_identity_unverified_or_changed_rejected(self):
        for patch in [{'account_verified':False},{'identity':{}},{'identity_before':{**self.identity,'account_id':'different'}}]:
            with self.assertRaises(ValueError):m.finalize(self.job,{**self.candidate,**patch},self.root/'r.json')
    def test_merchant_v2_finalizer_checks_global_provider_and_target_identity(self):
        self.job.update(identity_contract='merchant-v2',provider_baseline=self.identity['provider'],identity_baseline=None,
                        known_company_identities={})
        actual={**self.identity,'account_id':'different-merchant','manager':'merchant-manager'}
        candidate={**self.candidate,'identity':actual,'identity_before':actual}
        self.assertEqual(m.finalize(self.job,candidate,self.root/'r.json')['identity'],actual)
        self.job['known_company_identities']={'1234':actual}
        bad={**actual,'manager':'changed'}
        with self.assertRaisesRegex(ValueError,'account-changed'):
            m.finalize(self.job,{**candidate,'identity':bad,'identity_before':bad},self.root/'other.json')
        self.job['provider_baseline']='another-provider'
        with self.assertRaisesRegex(ValueError,'provider-changed'):
            m.finalize(self.job,candidate,self.root/'other.json')
    def test_download_not_ready(self):
        self.source.write_bytes(b'not a completed XLSX')
        with self.assertRaises(ValueError):m.finalize(self.job,self.candidate,self.root/'r.json')
    def test_verified_download_cannot_change_before_handoff(self):
        candidate={**self.candidate,'src_sha256':m.digest(self.source)}
        with ZipFile(self.source,'a') as z:z.writestr('changed.xml','changed')
        with self.assertRaisesRegex(ValueError,'download-changed-after-verification'):
            m.finalize(self.job,candidate,self.root/'r.json')
        self.assertFalse((self.root/'exports').exists())
    def test_bridge_backend_requires_reviewed_handshake(self):
        bridge={**self.candidate,'backend':'local-dom-bridge'}
        with self.assertRaisesRegex(ValueError,'bridge-transport-unverified'):
            m.finalize(self.job,bridge,self.root/'r.json')
        bridge['transport_proof']={'safety_version':'dom-only-20261021-3','safety':'DOM-only','reviewed_extension_ready':True}
        result=m.finalize(self.job,bridge,self.root/'r.json')
        self.assertEqual(result['backend'],'local-dom-bridge')
        with self.assertRaisesRegex(ValueError,'acquisition-backend-mismatch'):
            m.finalize(self.job,{**bridge,'backend':'unreviewed'},self.root/'r.json')
    def test_wrong_record_origin(self):
        with self.assertRaises(ValueError):m.finalize(self.job,{**self.candidate,'record_url':'https://evil.test/?groupid=1234'},self.root/'r.json')
    def test_different_export_not_overwritten(self):
        first=m.finalize(self.job,self.candidate,self.root/'r.json')
        with ZipFile(self.source,'a') as z:z.writestr('other.xml','changed')
        second=m.finalize(self.job,self.candidate,self.root/'r.json')
        self.assertNotEqual(first['source'],second['source']);self.assertTrue(Path(first['source']).exists())
    def test_backend_is_physical_dependency(self):
        root=Path(__file__).resolve().parents[1]
        cfg=json.loads((root/'backend.json').read_text());self.assertEqual(cfg['backend'],'local-dom-bridge')
        self.assertEqual(cfg['runtime'],'scripts/bridge-workflow.py');self.assertTrue(cfg['explicit_tab_id_required']);self.assertTrue(cfg['legacy']['receipt_reading_supported'])
        code=(root/'scripts/acquire.mjs').read_text()
        for forbidden in ['chrome.debugger','document.cookie','__reactFiber','connectOverCDP','remote-debugging-port','127.0.0.1:17341']:
            self.assertNotIn(forbidden,code)



class JournalTest(unittest.TestCase):
    setUp=OperatorTest.setUp
    tearDown=OperatorTest.tearDown
    def make_journal(self):
        path=self.root/'workflow.json';self.job.update(work_order_id='fixture',workflow_path=str(path))
        stages=['identity','switch','navigation','filter','export-intent','export-generated','download-intent','download-complete']
        data={'state':'complete','phase':'done','work_order_id':'fixture','company':self.job['company'],
              'groupid':self.job['groupid'],'date_range':self.job['date_range'],'result':self.candidate,
              'checkpoints':[{'stage':s,'event_id':str(n)} for n,s in enumerate(stages)]}
        path.write_text(json.dumps(data));return path,data
    def test_complete_journal_finalizes(self):
        path,data=self.make_journal();result=m.finalize_journal(self.job,path,self.root/'receipt.json')
        self.assertEqual(result['work_order_id'],'fixture');self.assertEqual(result['workflow_sha256'],m.digest(path))
    def test_incomplete_or_mismatched_journal_rejected(self):
        path,data=self.make_journal()
        for patch in [{'state':'running'},{'work_order_id':'other'},{'checkpoints':[]},{'date_range':{'start':'bad'}}]:
            with self.subTest(patch=patch):
                path.write_text(json.dumps({**data,**patch}))
                with self.assertRaises(ValueError):m.finalize_journal(self.job,path,self.root/'receipt.json')

if __name__=='__main__':unittest.main()
