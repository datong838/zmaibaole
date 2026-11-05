"""Offline fixtures only; navigation order generation does not invoke runtime/UI."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS))
import prepare_company_navigation as n
IDENTITY={'provider':'服务商123456789','account_id':'111222333','manager':'测试甲'}
OTHER={**IDENTITY,'account_id':'444555666','manager':'测试乙'}
class CompanyNavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.primary=self.receipt('A','123',IDENTITY);self.other=self.receipt('B','456',OTHER)
        self.registry=self.root/'registry'/'identity.json';self.registry.parent.mkdir();self.registry.write_text(json.dumps({'version':2,'provider_baseline':IDENTITY['provider'],'company_identities':{'123':IDENTITY,'456':OTHER},'updated_at':'fixture'}))
        self.out=self.root/'navigation';self.kw={'target_company':'A','target_groupid':'123','outdir':str(self.out),'purpose':'complaint-brand-navigation','stable_key':'frozen-16-19-A','registry_ref':n.ref(str(self.registry),n.digest(self.registry))}
    def receipt(self,company,gid,identity):
        folder=self.root/'inputs'/company;folder.mkdir(parents=True)
        source=self.root/'exports'/company/'export.xlsx';source.parent.mkdir(parents=True)
        with ZipFile(source,'w') as z:z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml','<workbook/>')
        fields={'source':str(source),'src_sha256':n.digest(source),'bytes':source.stat().st_size,'download_verified':True,'source_is_authoritative_export':True,'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge','transport_proof':{'safety_version':'dom-only-20261021-6','safety':'DOM-only','reviewed_extension_ready':True},'identity':identity,'identity_before':identity,'account_verified':True,'work_order_id':'fixture-'+company,'company':company,'groupid':gid,'date_range':{'start':'2026-10-16','end':'2026-10-19'},'record_url':'https://life.douyin.com/p/export_records/20101?groupid='+gid}
        journal={'state':'complete','phase':'done','work_order_id':fields['work_order_id'],'company':company,'groupid':gid,'date_range':fields['date_range'],'result':copy.deepcopy(fields),'checkpoints':[{'stage':s} for s in ('identity','switch','navigation','filter','export-intent','export-generated','download-intent','download-complete')]}
        (folder/'workflow.json').write_text(json.dumps(journal));fields['workflow_sha256']=n.digest(folder/'workflow.json');path=folder/'acquisition.json';path.write_text(json.dumps(fields));return n.ref(str(path),n.digest(path))
    def prepare(self,**changes):return n.prepare(self.primary,**{**self.kw,**changes})
    def test_legal_order_fixed_company_only_and_snapshot_bytes(self):
        original={p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()};result=self.prepare();job=json.loads(Path(result['work_order_path']).read_text())
        self.assertEqual(job['action'],'return-company');self.assertEqual(job['identity_contract'],'merchant-v2');self.assertEqual(job['identity_baseline'],IDENTITY);self.assertEqual(job['known_company_identities'],{'123':IDENTITY,'456':OTHER})
        self.assertFalse(job['export_enabled']);self.assertFalse(job['send_enabled']);self.assertFalse(job['progress_updates_enabled']);self.assertNotIn('date_range',job);self.assertNotIn('source_dir',job);self.assertFalse(Path(result['workflow_path']).exists())
        for p,raw in original.items():self.assertEqual(p.read_bytes(),raw)
        for ref in result['snapshots']:self.assertEqual(n.digest(ref['path']),ref['sha256'])
        self.assertTrue(result['explicit_tab_id_required']);self.assertEqual(result['required_extra_argv'],['--tab-id','FRESHLY_VERIFIED_EXISTING_TAB_ID'])
    def test_generated_order_runs_existing_return_company_state_machine_with_fake_bridge(self):
        spec=importlib.util.spec_from_file_location('company_nav_existing_runtime',SCRIPTS/'bridge-workflow.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
        result=self.prepare();job=json.loads(Path(result['work_order_path']).read_text());commands=[]
        def invoke(command):
            commands.append(command);op=command['op']
            if op=='tabs':value=[{'tabs':[{'tabId':7,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]
            elif op=='ping':value={'version':runtime.VERSION,'safety':'DOM-only'}
            elif op=='tree':value={'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'children':[{'name':IDENTITY['provider']+' 账户ID '+IDENTITY['account_id']+' 我的客户经理 '+IDENTITY['manager']+' 退出登录','attributes':{'class':'UserCard-index-module__outer--fixture'},'children':[]}]}}
            else:raise AssertionError('No export/send/UI action expected on already-selected target')
            return {'ok':True,'result':value}
        workflow=runtime.Workflow(job,7,invoke);workflow.tick();workflow.tick()
        self.assertEqual(workflow.s['state'],'complete');self.assertEqual(workflow.s['phase'],'done');self.assertTrue(workflow.s['result']['verified']);self.assertEqual(workflow.s['date_range'],{})
        self.assertTrue(all(c['op'] in ('tabs','ping','tree') for c in commands))
    def test_same_binding_reuses_even_live_registry_updated_and_workflow_untouched(self):
        first=self.prepare();path=Path(first['workflow_path']);path.write_text('{"phase":"unknown-native-action"}')
        self.registry.write_text(self.registry.read_text()+' ')
        again=self.prepare();self.assertTrue(again['reused']);self.assertEqual(first['work_order_sha256'],again['work_order_sha256']);self.assertEqual(path.read_text(),'{"phase":"unknown-native-action"}')
        with self.assertRaisesRegex(ValueError,'stable-key-input-conflict'):self.prepare(registry_ref=n.ref(str(self.registry),n.digest(self.registry)))
    def test_two_receipt_identity_mode(self):
        result=self.prepare(registry_ref=None,identity_refs=[self.primary,self.other]);job=json.loads(Path(result['work_order_path']).read_text());self.assertEqual(job['known_company_identities']['456'],OTHER)
    def test_hash_changes_unknown_target_and_identity_conflicts_rejected(self):
        for changes in [{'target_company':'other'},{'target_groupid':'456'},{'registry_ref':n.ref(str(self.registry),'f'*64)}]:
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.prepare(**changes)
        registry=json.loads(self.registry.read_text());registry['company_identities']['123']={**IDENTITY,'manager':'changed'};self.registry.write_text(json.dumps(registry))
        with self.assertRaisesRegex(ValueError,'target-identity'):self.prepare(registry_ref=n.ref(str(self.registry),n.digest(self.registry)))
    def test_provider_conflict_and_single_known_identity_reject(self):
        for known in [{'123':IDENTITY},{'123':IDENTITY,'456':{**OTHER,'provider':'服务商999999999'}}]:
            self.registry.write_text(json.dumps({'version':2,'provider_baseline':IDENTITY['provider'],'company_identities':known}))
            with self.subTest(known=known),self.assertRaisesRegex(ValueError,'two-known'):self.prepare(registry_ref=n.ref(str(self.registry),n.digest(self.registry)))
    def test_statistics_receipt_incomplete_journal_and_changed_export_reject(self):
        path=Path(self.primary['path']);raw=path.read_bytes();original=json.loads(raw)
        for changes in [{'operator_skill':None},{'workflow_sha256':'f'*64},{'download_verified':False},{'identity_before':OTHER}]:
            path.write_text(json.dumps({**original,**changes}));r=n.ref(str(path),n.digest(path))
            with self.subTest(changes=changes),self.assertRaises(ValueError):n.prepare(r,**self.kw)
        path.write_bytes(raw);source=Path(original['source']);source.write_bytes(source.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'source-changed'):self.prepare()
    def test_fixed_paths_no_daily_folder_or_symlink_or_partial_reset(self):
        with self.assertRaisesRegex(ValueError,'independent'):self.prepare(outdir=str(Path(self.primary['path']).parent/'new-order'))
        with self.assertRaisesRegex(ValueError,'absolute'):self.prepare(outdir='relative-navigation')
        self.out.mkdir();(self.out/'workflow.json').write_text('do not reset')
        with self.assertRaisesRegex(ValueError,'without-manifest'):self.prepare()
        self.assertEqual((self.out/'workflow.json').read_text(),'do not reset')
    def test_export_overlap_and_output_symlink_fail_before_original_directory_write(self):
        source=Path(json.loads(Path(self.primary['path']).read_text())['source']);before=set(source.parent.iterdir())
        with self.assertRaisesRegex(ValueError,'export-directory'):self.prepare(outdir=str(source.parent/'new-nav'))
        self.assertEqual(set(source.parent.iterdir()),before)
        self.out.mkdir();(self.out/'inputs').symlink_to(source.parent,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.prepare()
        self.assertEqual(set(source.parent.iterdir()),before)
    def test_frozen_snapshot_or_job_tampering_refuses_reuse(self):
        result=self.prepare();p=Path(result['snapshots'][0]['path']);p.write_text('{}')
        with self.assertRaisesRegex(ValueError,'snapshot-changed'):self.prepare()
    def test_same_stablekey_company_or_purpose_change_does_not_overwrite(self):
        result=self.prepare();old=Path(result['work_order_path']).read_bytes()
        for changes in [{'stable_key':'different'},{'purpose':'other-purpose'},{'target_company':'B'}]:
            with self.assertRaisesRegex(ValueError,'stable-key-input-conflict'):self.prepare(**changes)
        self.assertEqual(Path(result['work_order_path']).read_bytes(),old)
if __name__=='__main__':unittest.main()
