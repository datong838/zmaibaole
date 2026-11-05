"""Offline DOM/XLSX fixtures: no real history workspace, browser, messages or memory."""
import copy
import contextlib
import io
import json
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import history_workspace as h
import case_memory
import test_normal_observation as fixtures


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.NormalObservationTests(); self.f.setUp(); self.addCleanup(self.f.doCleanups)
        # This synthetic generic-tree fixture exercises workspace ownership;
        # actual DOM single-page rejection is independently replayed below.
        probe=patch.object(h.normal,'navigation_probe',return_value={'pagination':'1/1','normal_count':1});self.probe=probe.start();self.addCleanup(probe.stop)
        self.base = self.f.f.root; self.root = self.base/'history'; self.memory = self.base/'memory'
        self.f.f.receipt['transport_proof']['safety_version'] = 'dom-only-20261021-11'; self.f.f.write_receipt()
        self.f.job.update(source_receipt=str(self.f.f.receipt_path),source_receipt_sha256=self.f.f.receipt_hash)
        seed = copy.deepcopy(self.f.f.receipt); folder=self.base/'seed'; folder.mkdir()
        journal={'state':'complete','phase':'done','work_order_id':seed['work_order_id'],'company':seed['company'],'groupid':seed['groupid'],'date_range':seed['date_range'],'result':copy.deepcopy(seed),'checkpoints':[{'stage':x} for x in ('identity','switch','navigation','filter','export-intent','export-generated','download-intent','download-complete')]}
        h.workflow.atomic(folder/'workflow.json',journal); seed['workflow_sha256']=h.authority.digest(folder/'workflow.json');h.workflow.atomic(folder/'acquisition.json',seed);self.seed=h.ref(folder/'acquisition.json')
        self.source=self.f.joined();self.key=self.source['groupid']+':'+self.source['rows'][0]['review_id'];self.refs={}
        for k,value in [('job',self.f.job),('source',self.source),('profile',self.f.profile),('envelope',self.f.envelope)]:
            p=self.base/(k+'-input.json');h.workflow.atomic(p,value);self.refs[k]=h.ref(p)

    def init(self, **kw):
        return h.initialize(self.root,self.f.job['company'],self.f.job['groupid'],'2026-10-19','2026-10-21',self.seed,today='2026-10-21',**kw)

    def ingest(self):
        self.init();return h.ingest(self.root,self.refs)

    def result(self):
        return {'review_key':self.key,'snapshot_sha256':self.refs['source']['sha256'],'url':self.source['url'],'source':'local-dom-bridge','status':'rejected','platform_status':'投诉失败','visible_text':'投诉失败\n只请求平台核对真实材料','observed_at':'2026-10-21T10:00:00+08:00','original_complaint':{'投诉类型':'其他','投诉理由':'只请求平台核对真实材料','投诉时间':'2026-10-20 10:30:00'},'submitted_by_this_workflow':False}

    def test_separate_init_pins_identity_without_daily_progress_and_is_idempotent(self):
        state=self.init();self.assertEqual(state['workspace_kind'],h.KIND);self.assertFalse(any(k in state for k in h.FORBIDDEN));raw=(self.root/'state.json').read_bytes();self.init();self.assertEqual((self.root/'state.json').read_bytes(),raw)
        self.assertFalse(h.CAPABILITIES['send']);self.assertFalse(h.CAPABILITIES['analyze'])

    def test_copied_daily_ledger_or_wrong_identity_cannot_initialize(self):
        self.root.mkdir();h.workflow.atomic(self.root/'state.json',{'version':1,'mode':'draft-only'})
        with self.assertRaisesRegex(ValueError,'history-only-workspace'):self.init()
        other=self.base/'other-history'
        with self.assertRaisesRegex(ValueError,'identity-receipt-scope'):h.initialize(other,'别家公司',self.f.job['groupid'],'2026-10-19','2026-10-21',self.seed,today='2026-10-21')

    def test_actual_join_ingests_existing_only_without_fake_media(self):
        state=self.ingest();self.assertEqual(list(state['tasks']),[self.key]);self.assertIsNone(state['tasks'][self.key]['screenshot']);self.assertFalse(any(k in state for k in h.FORBIDDEN));self.probe.assert_called_once()
        before=(self.root/'state.json').read_bytes();h.ingest(self.root,self.refs);self.assertEqual((self.root/'state.json').read_bytes(),before)

    def test_plain_complaint_is_skipped_cannot_get_runner_order(self):
        self.f.find('a')['name']='投诉';self.source=self.f.joined()
        for k,v in [('source',self.source),('envelope',self.f.envelope)]:h.workflow.atomic(self.refs[k]['path'],v);self.refs[k]=h.ref(self.refs[k]['path'])
        state=self.ingest();self.assertEqual(state['tasks'],{});self.assertEqual(len(state['sources'][self.refs['source']['sha256']]['skipped_uncomplained_ids']),1)
        with self.assertRaisesRegex(ValueError,'existing-result-only'):h.prepare(self.root,self.key)
        complete=h.verify_coverage(self.root,memory=self.memory);self.assertEqual(complete['existing_results_read'],0);self.assertEqual(complete['uncomplained_skipped'],1)

    def test_history_count_complete_requires_current_single_page_proof(self):
        self.init()
        for proof in [{'pagination':'1/2','normal_count':1},{'pagination':'1/1','normal_count':2}]:
            self.probe.return_value=proof
            with self.assertRaisesRegex(ValueError,'current-single-page-proof'):h.ingest(self.root,self.refs)
        self.assertEqual(h.load(self.root)['sources'],{})

    def test_unknown_profile_changed_source_or_wrong_scope_refuses(self):
        self.init()
        for name,change in [('profile',lambda x:x.update(status='awaiting-live-validation')),('source',lambda x:x['rows'][0].update(text='伪造正文')),('job',lambda x:x.update(identity={'provider':'其他','account_id':'x','manager':'x'})),('job',lambda x:x.update(start='2026-09-01'))]:
            values=json.loads(Path(self.refs[name]['path']).read_text());change(values);p=self.base/('changed-'+name+'.json');h.workflow.atomic(p,values);refs={**self.refs,name:h.ref(p)}
            with self.assertRaises(ValueError):h.ingest(self.root,refs)
        self.assertFalse(h.load(self.root)['sources'])

    def test_prepare_reuses_existing_runner_no_screenshot_and_pins_real_source_page(self):
        self.ingest();out=h.prepare(self.root,self.key);manifest=h.workflow.read(out['manifest']['path']);self.assertEqual(set(manifest['inputs']),{'job','source','profile','envelope','page','orders'});self.assertEqual(manifest['root'],str(self.root.resolve()));self.assertFalse(out['ui_used']);self.assertEqual(h.prepare(self.root,self.key),out)

    def test_generic_reader_also_enforces_history_identity_range_and_capabilities(self):
        self.ingest();prepared=h.prepare(self.root,self.key);manifest=h.workflow.read(prepared['manifest']['path']);before=h.load(self.root)
        for mutate in [lambda s:s['capabilities'].update(send=True),lambda s:s.update(next_start='2026-10-19'),lambda s:s['tasks'][self.key]['review'].update(text='不同原文')]:
            state=copy.deepcopy(before);mutate(state);h.workflow.atomic(self.root/'state.json',state)
            with self.assertRaises(ValueError):h.runner.tick(manifest,request=lambda c:self.fail('invalid history must fail before UI'))
        h.workflow.atomic(self.root/'state.json',before)

    def test_record_result_automatically_stores_original_in_isolated_case_memory_no_cursor(self):
        self.ingest();p=self.base/'result.json';h.workflow.atomic(p,self.result());out=h.record_result(self.root,self.key,p,memory=self.memory);self.assertTrue(out['appended']);self.assertFalse(h.record_result(self.root,self.key,p,memory=self.memory)['appended']);self.assertEqual(len(case_memory.read_records(self.memory)),1);self.assertFalse(any(k in h.load(self.root) for k in h.FORBIDDEN))
        self.assertFalse((self.root/'投诉处理结果汇总.xlsx').exists())

    def test_unclosed_result_or_uncovered_dates_cannot_claim_full_month(self):
        self.ingest()
        with self.assertRaisesRegex(ValueError,'history-incomplete'):h.verify_coverage(self.root,memory=self.memory)
        state=h.load(self.root);state['history_range']['start']='2026-09-21';state['binding']['history_range']['start']='2026-09-21';state['binding_sha256']=h.authority.data_hash(state['binding']);h.workflow.atomic(self.root/'state.json',state)
        with self.assertRaisesRegex(ValueError,'coverage-gap'):h.verify_coverage(self.root,memory=self.memory)

    def test_formal_workflow_cli_cannot_analyze_send_close_or_init_history_root(self):
        self.init()
        for args in [['plan'],['send-test','--id',self.key],['close','--batch','x'],['init','--company','x','--groupid','123']]:
            with patch.object(sys,'argv',['workflow.py','--root',str(self.root),*args]),self.assertRaisesRegex(ValueError,'history-only-workspace-use'),contextlib.redirect_stdout(io.StringIO()):h.workflow.main()

    def test_runner_default_record_callback_dispatches_to_history_guard(self):
        self.ingest();p=self.base/'result.json';h.workflow.atomic(p,self.result())
        original=h.record_result
        with patch.object(h,'record_result',side_effect=lambda root,key,path:original(root,key,path,memory=self.memory)) as called:
            h.runner.ledger_record(self.root,self.key,p)
        called.assert_called_once();self.assertFalse((self.root/'投诉处理结果汇总.xlsx').exists())

    def test_history_run_uses_original_once_reader_and_proves_coverage_without_media(self):
        import test_result_observation as resultfixtures
        classes={'store':'poiName-W9HDFV','customer':'nickName-wB7fZf','text':'text-Hl9jZe','action':'button-vhqEd7 isHighlight-DoxxP4'}
        for field,selector in [('store','s'),('customer','c'),('text','t'),('action','a')]:
            self.f.find(selector)['attributes']['class']=classes[field];self.f.profile[field]={'attributes':{'class':classes[field]}}
        self.source=self.f.joined()
        for k,v in [('source',self.source),('profile',self.f.profile),('envelope',self.f.envelope)]:h.workflow.atomic(self.refs[k]['path'],v);self.refs[k]=h.ref(self.refs[k]['path'])
        self.ingest();prepared=h.prepare(self.root,self.key);fx=resultfixtures.ResultObservationTests();fx.setUp();drawer=copy.deepcopy(fx.drawer);row=self.source['rows'][0]
        for position,field in [(3,'store'),(4,'customer'),(5,'text')]:drawer['children'][position]['name']=row[field]
        close=resultfixtures.n(cl='byted-drawer-close-icon',tag='span');close.update(selector='#close',disabled=False);drawer['children'].append(close)
        tab=self.f.envelope['pages'][0]['tab'];normal_tree=self.f.envelope['pages'][0]['tree'];opened=False;commands=[]
        def request(cmd):
            nonlocal opened
            commands.append(cmd)
            if cmd['op']=='activate':value={}
            elif cmd['op']=='tabs':value=[{'tabs':[tab]}]
            elif cmd['op']=='tree':value={**normal_tree,'root':resultfixtures.n(children=[drawer])} if opened else normal_tree
            elif cmd['op']=='click':
                closed=cmd['locator']['value']=='#close';opened=not closed;node=close if closed else self.f.find('a');value={'kind':'complaint-read','clicked':node}
            else:raise AssertionError(cmd)
            return {'ok':True,'result':value}
        with patch.object(h.runner.normal,'navigation_probe',return_value={'pagination':'1/1','normal_count':1}),patch.object(h.runner,'runtime_identity',return_value={'runtime_full_identity_rechecked':False}),patch.object(h.runner,'LEGACY',self.base/'no-legacy'),patch.object(h.runner,'datetime') as clock:
            clock.now.return_value=datetime(2026,10,21,3,tzinfo=timezone.utc)
            result=h.run(prepared['manifest']['path'],steps=10,request=request,memory=self.memory)
            self.assertEqual(result['state'],'complete');count=len(commands)
            h.run(prepared['manifest']['path'],steps=10,request=request,memory=self.memory);self.assertEqual(len(commands),count)
            coverage=h.verify_coverage(self.root,memory=self.memory);self.assertTrue(coverage['scope_complete']);self.assertFalse(coverage['company_all_history_complete']);self.assertIn('already removed or otherwise not displayed records',coverage['scope_exclusions']);self.assertEqual(coverage['existing_results_read'],1)
        self.assertEqual([x['locator']['value'] for x in commands if x['op']=='click'],['a','#close']);self.assertEqual(len(case_memory.read_records(self.memory)),1);self.assertFalse(opened)

    def other_identity(self):
        seed=h.document(self.seed);seed.update(company='另一公司',groupid='987654321',identity={**seed['identity'],'account_id':'987654321','manager':'另一经理'},work_order_id='other-fixture');seed['identity_before']=seed['identity'];seed['record_url']='https://life.douyin.com/p/export_records/20101?groupid=987654321'
        folder=self.base/'other-seed';folder.mkdir();old=h.workflow.read(Path(self.seed['path']).with_name('workflow.json'));old.update(company=seed['company'],groupid=seed['groupid'],work_order_id=seed['work_order_id'],result=copy.deepcopy(seed));h.workflow.atomic(folder/'workflow.json',old);seed['workflow_sha256']=h.authority.digest(folder/'workflow.json');h.workflow.atomic(folder/'acquisition.json',seed);return h.ref(folder/'acquisition.json')

    def test_acquisition_order_is_independent_stable_and_does_not_run_or_reset_unknown(self):
        self.init();other=self.other_identity();prepared=h.prepare_acquisition(self.root,[self.seed,other]);job=h.document(prepared['work_order']);self.assertEqual(job['action'],'acquire');self.assertEqual(job['date_range']['start'],'2026-10-19');self.assertEqual(job['date_range']['end'],'2026-10-20');self.assertFalse(job['progress_updates_enabled']);self.assertFalse(job['send_enabled']);self.assertEqual(len(job['known_company_identities']),2)
        self.assertFalse(Path(job['workflow_path']).exists());h.workflow.atomic(job['workflow_path'],{'phase':'unknown-export-intent'});raw=Path(job['workflow_path']).read_bytes();self.assertEqual(h.prepare_acquisition(self.root,[other,self.seed]),prepared);self.assertEqual(Path(job['workflow_path']).read_bytes(),raw)
        changed=h.document(other);changed['recorded_at']='2026-10-21T09:01:00+08:00';h.workflow.atomic(other['path'],changed);other=h.ref(other['path'])
        with self.assertRaisesRegex(ValueError,'original-order-required'):h.prepare_acquisition(self.root,[self.seed,other])
        self.assertFalse(any(k in h.load(self.root) for k in h.FORBIDDEN))

    def test_incomplete_identity_set_or_unowned_receipt_cannot_prepare_normal_job(self):
        self.init()
        with self.assertRaisesRegex(ValueError,'two-identities'):h.prepare_acquisition(self.root,[self.seed])
        with self.assertRaisesRegex(ValueError,'owned-acquisition'):h.prepare_normal_job(self.root,self.seed,self.root/'normal-job.json')


class ActualSinglePageProofTests(unittest.TestCase):
    def test_history_checks_visible_pager_without_changing_legacy_reconstruction(self):
        import tempfile
        base=h.runner.PROJECT/'work/live-acceptance/complaints/frozen-20261016-20261020/01-yantai'
        if not (base/'normal-envelope.json').exists():self.skipTest('immutable source fixture absent')
        job=h.workflow.read(base/'navigation-job.json');profile=h.workflow.read(base/'normal-profile.json');envelope=h.workflow.read(base/'normal-envelope.json')
        source=h.workflow.read(base/'authoritative-normal-capture.json')
        state={'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'history_range':{'start':'2026-09-21','end_exclusive':'2026-10-21'}}
        original=h.normal.joined(job,envelope,profile,job['source_receipt'],job['source_receipt_sha256'])
        self.assertEqual(original,source)
        with tempfile.TemporaryDirectory() as temp:
            def refs():
                values={'job':job,'profile':profile,'envelope':envelope,'source':source};out={}
                for key,value in values.items():
                    path=Path(temp)/(key+'.json');h.workflow.atomic(path,value);out[key]=h.ref(path)
                return out
            self.assertEqual(h._inputs(state,refs())['source'],source)
            labels=[x for x in h.normal.flatten(envelope['pages'][0]['tree']['root']) if x.get('name')=='1/1' and not x.get('children')]
            self.assertEqual(len(labels),1);labels[0]['name']='1/2'
            # Synthetic altered tree is NOT live evidence. Legacy source replay
            # remains unchanged; only NEW history intake adds a current UI gate.
            source=h.normal.joined(job,envelope,profile,job['source_receipt'],job['source_receipt_sha256'])
            self.assertTrue(source['all_pages_read'])
            with self.assertRaisesRegex(ValueError,'normal-probe-pagination-needs-profile'):h._inputs(state,refs())


class PriorProofTests(unittest.TestCase):
    def test_real_pinned_closed_chains_allow_only_history_cross_source_audit(self):
        index=h.runner.PROJECT/'work/live-acceptance/complaints/runner-adoption/history-prior-complete-proofs.json'
        if not index.exists():self.skipTest('immutable actual closed proofs unavailable')
        for item in h.workflow.read(index)['proofs']:
            operation=h.document(item['operation']);m=operation['manifest'];v,o,row=h.runner.manifest_inputs(m,historical_complete=True)
            proof={'kind':'history-prior-verified-complete-v1','review_key':m['review_key'],'operation':item['operation'],'legacy':item['legacy']}
            state={'workspace_kind':h.KIND,'company':v['job']['company'],'groupid':str(v['job']['groupid']),'identity':v['job']['identity'],'history_range':{'start':'2026-09-21','end_exclusive':'2026-10-21'},'prior_operations':[proof]}
            result=h.verify_prior_for_legacy(state,m['review_key'],item['legacy'],row);self.assertIn('never substitutes',result['use'])
            # The new monthly snapshot is deliberately not the old source hash;
            # only the closed prior permits navigation, not a current result.
            audit=h.runner.legacy_guard(m['review_key'],{},None,history=(state,row));self.assertEqual(len(audit),1)
            with self.assertRaisesRegex(ValueError,'explicit-complete-adoption'):h.runner.legacy_guard(m['review_key'],{},None)
            changed={**row,'text':'另一个评价'}
            with self.assertRaisesRegex(ValueError,'tuple-changed'):h.verify_prior_for_legacy(state,m['review_key'],item['legacy'],changed)
            state['prior_operations']=[]
            with self.assertRaisesRegex(ValueError,'proof-required'):h.runner.legacy_guard(m['review_key'],{},None,history=(state,row))

    def test_unknown_old_operation_and_hash_changes_never_get_history_exception(self):
        import tempfile
        index=h.runner.PROJECT/'work/live-acceptance/complaints/runner-adoption/history-prior-complete-proofs.json'
        if not index.exists():self.skipTest('immutable actual closed proofs unavailable')
        item=h.workflow.read(index)['proofs'][0];operation=h.document(item['operation']);m=operation['manifest'];v,o,row=h.runner.manifest_inputs(m,historical_complete=True)
        state={'workspace_kind':h.KIND,'company':v['job']['company'],'groupid':str(v['job']['groupid']),'identity':v['job']['identity'],'history_range':{'start':'2026-09-21','end_exclusive':'2026-10-21'}}
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'operation.json';operation['state']='open-unknown';h.workflow.atomic(p,operation)
            proof={'kind':'history-prior-verified-complete-v1','review_key':m['review_key'],'operation':h.ref(p),'legacy':item['legacy']}
            with self.assertRaisesRegex(ValueError,'complete-manifest'):h._prior(proof,state,row=row)
            proof['operation']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'input-changed'):h._prior(proof,state,row=row)


if __name__=='__main__':unittest.main()
