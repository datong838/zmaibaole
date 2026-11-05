import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import workflow as w

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        from unittest.mock import patch
        import case_memory
        original_load=case_memory.load_for_workflow
        memory_patch=patch.object(case_memory,'load_for_workflow',side_effect=lambda state,key=None,**kw:original_load(state,key,memory=self.root/'isolated-memory',**kw))
        memory_patch.start();self.addCleanup(memory_patch.stop)
        import_patch=patch.object(case_memory,'auto_import',return_value={'appended':False,'test_isolated':True})
        import_patch.start();self.addCleanup(import_patch.stop)
        self.s=w.initialize(self.root,'测试公司','123','2026-10-20','2026-10-16',mode='fixture')
        self.key='123:review-1'
    def json(self,name,data):
        p=self.root/name;w.atomic(p,data);return p
    def payload(self):
        return {'account_verified':True,'identity':{'provider':'服务商测试','account_id':'123456789','manager':'测试经理'},'source':'fixture','company':'测试公司','groupid':'123','url':'https://life.douyin.com/p/life_comment/management?groupid=123',
            'start':'2026-10-16','end_exclusive':'2026-10-20','negative_filter':'中差评（1-3心）','filter_active':True,
            'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'},'fold_boundary_verified':True,'all_pages_read':True,
            'filtered_count':1,'observed_at':'2026-10-20T10:00:00+08:00','rows':[{'review_id':'review-1','section':'filtered',
            'store':'测试水果店','customer':'测试顾客','date':'2026-10-19','stars':1,'text':'味道一般','product':'水果','action':'投诉'},
            {'section':'folded','text':'不得导入这条'}]}
    def capture(self,p=None):
        w.ingest(self.root,self.s,self.json('capture.json',p or self.payload()),'2026-10-20')
    def screenshot_and_send(self):
        # Only fixture magic bytes; not presented as a real browser screenshot.
        image=self.root/'fixture.png';image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        meta={'review_key':self.key,'snapshot_sha256':self.s['tasks'][self.key]['latest_snapshot']['sha256'],
              'source':'fixture','filters_visible':True,'review_visible':True,'sha256':w.digest(image)}
        w.attach_screenshot(self.root,self.s,self.key,image,self.json('screenshot.json',meta))
        order=w.send_order(self.root,self.s,self.key)
        req={'key':order['key'],'kind':'group','target':'测试群请忽略','scope':'test','file_sha256':w.digest(image)}
        self.receipt={'job':req,'fingerprint':hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                      'status':'complete','phase':'done','ui_confirmed':True}
        w.attach_wecom(self.root,self.s,self.key,self.json('wecom.json',self.receipt))
    def history(self):
        return {'company':'测试公司','groupid':'123','url':'https://life.douyin.com/?groupid=123','source':'fixture',
                'start':'2026-10-13','end_exclusive':'2026-10-20','observed_at':'2026-10-20T10:01:00+08:00',
                'all_pages_read':True,'items':[]}
    def analysis(self):
        return {'review_key':self.key,'snapshot_sha256':self.s['tasks'][self.key]['latest_snapshot']['sha256'],
                'agent_assessed':True,'no_fabricated_facts':True,'category':'其他','reason':'只有口味主观评价，无恶意证据',
                'draft':'请核实该评价具体消费情况；现有内容不足以确认违规，不作恶意指控。','quotes':['味道一般'],
                'suspected_bulk':False,'history_sha256':(self.s['tasks'][self.key].get('history') or {}).get('evidence',{}).get('sha256')}
    def ready(self):
        self.capture();self.screenshot_and_send()
        w.attach_history(self.root,self.s,self.key,self.json('history.json',self.history()))
        w.analyze(self.root,self.s,self.key,self.json('analysis.json',self.analysis()))
    def test_platform_under_review_is_existing_pending_never_new_draft(self):
        p=self.payload();p['rows'][0]['action']='投诉审核中';self.capture(p);self.screenshot_and_send()
        self.assertEqual(self.s['tasks'][self.key]['status'],'existing_pending');self.assertEqual(w.next_action(self.s,self.key),'read-existing-result')
        with self.assertRaises(ValueError):w.close_batch(self.root,self.s,next(iter(self.s['batches'])))
    def test_resolved_result_before_media_still_schedules_required_screenshot(self):
        p=self.payload();p['rows'][0]['action']='查看投诉结果';self.capture(p)
        self.s['tasks'][self.key]['status']='resolved'
        planned=w.plan(self.s,'2026-10-20');self.assertEqual(planned['next_actions'][self.key],'capture-screenshot')
    def test_only_filtered_and_exclude_folded(self):
        self.capture();self.assertEqual(list(self.s['tasks']),[self.key]);self.assertEqual(next(iter(self.s['batches'].values()))['excluded_folded'],1)
    def test_scope_guards(self):
        for key,value in [('filter_active',False),('fold_boundary_verified',False),('all_pages_read',False),('filtered_count',2),('groupid','999')]:
            p=self.payload();p[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.capture(p)
    def test_today_and_good_review_rejected(self):
        for changes in ({'date':'2026-10-20'},{'stars':4},{'review_id':''}):
            p=self.payload();p['rows'][0].update(changes)
            with self.assertRaises(ValueError):self.capture(p)
    def test_duplicate_ids_rejected(self):
        p=self.payload();p['rows']=[p['rows'][0],copy.deepcopy(p['rows'][0])];p['filtered_count']=2
        with self.assertRaises(ValueError):self.capture(p)
    def test_draft_cannot_become_submitted(self):
        self.ready();t=self.s['tasks'][self.key]
        self.assertEqual(t['status'],'draft_ready');self.assertNotIn('submitted_at',t)
        w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
        self.assertEqual(self.s['next_start'],'2026-10-20')
        self.assertIn(self.key,w.plan(self.s,'2026-10-23')['recheck_ids'])
    def test_other_requires_week_history(self):
        self.capture();self.screenshot_and_send()
        with self.assertRaisesRegex(ValueError,'history-required'):w.analyze(self.root,self.s,self.key,self.json('analysis.json',self.analysis()))
    def test_history_partial_not_accepted(self):
        self.capture();h=self.history();h['start']='2026-10-14'
        with self.assertRaises(ValueError):w.attach_history(self.root,self.s,self.key,self.json('h.json',h))
    def test_fake_quote_rejected(self):
        self.ready();a=self.analysis();a.update(category='脏话辱骂',quotes=['不存在的脏话'])
        with self.assertRaises(ValueError):w.analyze(self.root,self.s,self.key,self.json('a2.json',a))
    def test_same_name_is_not_identity_proof(self):
        self.ready();a=self.analysis();a.update(suspected_bulk=True,related_ids=[self.key])
        with self.assertRaises(ValueError):w.analyze(self.root,self.s,self.key,self.json('a2.json',a))
    def test_unknown_send_does_not_confirm(self):
        self.capture();self.screenshot_and_send();r=copy.deepcopy(self.receipt);r['status']='unknown'
        with self.assertRaisesRegex(ValueError,'no-resend'):w.attach_wecom(self.root,self.s,self.key,self.json('unknown.json',r))
    def test_wrong_recipient_rejected(self):
        self.capture();self.screenshot_and_send();r=copy.deepcopy(self.receipt);r['job']['target']='生产群'
        with self.assertRaises(ValueError):w.attach_wecom(self.root,self.s,self.key,self.json('wrong.json',r))
    def test_existing_complaint_read_not_duplicate(self):
        p=self.payload();p['rows'][0]['action']='查看投诉结果';self.capture(p);self.screenshot_and_send()
        self.assertEqual(self.s['tasks'][self.key]['status'],'existing_pending')
        result={'review_key':self.key,'snapshot_sha256':self.s['tasks'][self.key]['latest_snapshot']['sha256'],
                'url':p['url'],'source':'fixture','status':'pending','visible_text':'处理中','observed_at':p['observed_at']}
        w.record_result(self.root,self.s,self.key,self.json('result.json',result))
        with self.assertRaises(ValueError):w.analyze(self.root,self.s,self.key,self.json('a.json',self.analysis()))
        w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
        self.assertIn(self.key,w.plan(self.s)['recheck_ids'])
        result.update(status='rejected',visible_text='投诉未通过')
        w.record_result(self.root,self.s,self.key,self.json('result2.json',result))
        self.assertNotIn(self.key,w.plan(self.s)['recheck_ids'])
    def test_incomplete_tasks_cannot_advance(self):
        self.capture()
        with self.assertRaises(ValueError):w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
        self.assertEqual(self.s['next_start'],'2026-10-16')
    def test_future_completed_range_cannot_skip_gap(self):
        p=self.payload();p['start']='2026-10-19';p['filtered_count']=0;p['rows']=[]
        self.capture(p);w.close_batch(self.root,self.s,'2026-10-19_2026-10-20')
        self.assertEqual(self.s['next_start'],'2026-10-16')
    def test_missed_monday_tuesday_catch_up(self):
        self.assertEqual(w.plan(self.s,'2026-10-21')['start'],'2026-10-16')
        self.assertEqual(w.plan(self.s,'2026-10-21')['end'],'2026-10-20')
    def test_first_run_previous_workday(self):
        with tempfile.TemporaryDirectory() as temp:
            s=w.initialize(Path(temp),'测试公司','123','2026-10-19',mode='fixture')
            self.assertEqual(s['initial_start'],'2026-10-16')
    def test_evidence_tamper_blocks_close(self):
        self.ready();Path(self.s['tasks'][self.key]['screenshot']['path']).write_text('changed')
        with self.assertRaises(ValueError):w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
    def test_same_id_changed_text_requires_reconciliation(self):
        self.capture();p=self.payload();p['rows'][0]['text']='改了内容'
        with self.assertRaises(ValueError):self.capture(p)
    def test_fixture_never_sends(self):
        self.capture()
        with self.assertRaisesRegex(ValueError,'fixture-external'):w.send_test(self.root,self.s,self.key)
    def test_never_reset_completion(self):
        with self.assertRaises(ValueError):w.initialize(self.root,'测试公司','123','2026-10-20','2026-10-19',mode='fixture')

    def test_zero_result_verified_completes_without_fabricated_tasks(self):
        p=self.payload();p['rows']=[];p['filtered_count']=0;self.capture(p)
        w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
        self.assertEqual(self.s['next_start'],'2026-10-20');self.assertFalse(self.s['tasks'])
    def test_close_is_idempotent_after_restart(self):
        self.ready();w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
        restored=w.load(self.root);n=len(restored['events'])
        w.close_batch(self.root,restored,'2026-10-16_2026-10-20')
        self.assertEqual(len(restored['events']),n)
    def test_existing_complaint_requires_reading_result_before_batch_close(self):
        p=self.payload();p['rows'][0]['action']='查看投诉结果';self.capture(p);self.screenshot_and_send()
        with self.assertRaisesRegex(ValueError,'result-read'):w.close_batch(self.root,self.s,'2026-10-16_2026-10-20')
    def test_specific_category_without_quotes_fails(self):
        self.ready();a=self.analysis();a.update(category='同行刷屏',quotes=[])
        with self.assertRaises(ValueError):w.analyze(self.root,self.s,self.key,self.json('bad.json',a))
    def test_wecom_payload_tamper_fails(self):
        self.capture();self.screenshot_and_send();r=copy.deepcopy(self.receipt);r['job']['key']='new-key'
        with self.assertRaisesRegex(ValueError,'job-changed'):w.attach_wecom(self.root,self.s,self.key,self.json('changed.json',r))
    def test_send_key_stable_on_resume(self):
        self.capture();self.screenshot_and_send();one=w.send_order(self.root,self.s,self.key)
        two=w.send_order(self.root,w.load(self.root),self.key)
        self.assertEqual(one,two)
    def test_every_changed_task_event_keeps_previous_result(self):
        self.ready();events=w.load(self.root)['events'];last=events[-1]
        self.assertEqual(last['record']['analysis']['category'],'其他')
        self.assertEqual(last['record']['status'],'draft_ready')
        self.assertTrue(last['record']['screenshot'])
    def test_future_date_range_rejected(self):
        p=self.payload();p['end_exclusive']='2026-10-21'
        with self.assertRaisesRegex(ValueError,'date-range'):self.capture(p)

    def test_account_change_blocks_collection(self):
        self.capture();p=self.payload();p['identity']['account_id']='different'
        with self.assertRaisesRegex(ValueError,'account-changed'):self.capture(p)
    def test_unknown_send_cannot_swap_image_to_get_new_key(self):
        self.capture();self.screenshot_and_send();t=self.s['tasks'][self.key]
        t['wecom']=None  # Simulate persisted sender intent without final confirmation.
        image=self.root/'new.png';image.write_bytes(b'\x89PNG\r\n\x1a\nnew-image')
        meta={'review_key':self.key,'snapshot_sha256':t['latest_snapshot']['sha256'],
              'source':'fixture','filters_visible':True,'review_visible':True,'sha256':w.digest(image)}
        with self.assertRaisesRegex(ValueError,'unknown-screenshot'):w.attach_screenshot(self.root,self.s,self.key,image,self.json('new-meta.json',meta))

    def test_local_bridge_backend_is_explicit_and_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=w.initialize(root,'测试公司','123','2026-10-20','2026-10-16',backend='local-dom-bridge')
            self.assertEqual(w.plan(s,'2026-10-20')['browser_backend'],'local-dom-bridge')
            self.assertEqual(w.initialize(root,'测试公司','123',backend='local-dom-bridge')['browser_backend'],'local-dom-bridge')
            with self.assertRaisesRegex(ValueError,'backend-conflict'):
                w.initialize(root,'测试公司','123',backend='codex-existing-extension')

    def test_bridge_capture_never_masquerades_existing_connection(self):
        self.s['mode']='draft-only';self.s['browser_backend']='local-dom-bridge'
        p=self.payload();p['source']='codex-existing-extension'
        with self.assertRaisesRegex(ValueError,'source-not-live'):self.capture(p)
        p['source']='local-dom-bridge';self.capture(p)
        self.assertEqual(len(self.s['tasks']),1)

    def test_fixture_cannot_claim_bridge_source(self):
        p=self.payload();p['source']='local-dom-bridge'
        with self.assertRaisesRegex(ValueError,'source-not-live'):self.capture(p)

    def test_unknown_backend_cannot_initialize(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'backend-invalid'):
                w.initialize(Path(tmp),'测试公司','123',backend='debug-service')

if __name__=='__main__':unittest.main()
