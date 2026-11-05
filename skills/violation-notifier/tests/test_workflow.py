import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import workflow as w
COMPANY='烟台一成教育文化咨询有限公司'
class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.s=w.initialize(self.root,COMPANY,'2026-10-20','2026-10-16',mode='fixture')
        self.batch='2026-10-16_2026-10-20'
    def json(self,name,value):
        p=self.root/name;w.atomic(p,value);return p
    def payload(self):
        return {'company':COMPANY,'groupid':self.s['groupid'],'source':'fixture',
            'url':'https://life.douyin.com/p/governance/violation_list?groupid='+self.s['groupid'],
            'observed_at':'2026-10-20T09:00:00+08:00','account_verified':True,
            'identity':{'provider':'测试服务商','account_id':'123456789','manager':'测试经理'},
            'start':'2026-10-16','end_exclusive':'2026-10-20',
            'analysis':{'start':'2026-10-16','end_exclusive':'2026-10-20','scope':'全部','total':2,
                'all_pages_read':True,'filters_verified':True,'all_reasons_read':True,
                'rows':[{'violation_type':'商品信息需完善','object_types':['商品'],'count':2}]},
            'records':{'start':'2026-10-16','end_exclusive':'2026-10-20','scope':'全部','total':2,'unread_only':False,
                'all_pages_read':True,'filters_verified':True,'rows':[
                {'notice_id':'test-1','date':'2026-10-19','subject':'测试水果一店','reason':'商品信息需完善','object_type':'商品','object_name':'测试榴莲',
                 'actions':['下架商品','扣分2分'],'effectiveness_status':'已生效','rectification_status':'待整改',
                 'detail_read':True,'public_recommendation':'核对并补充商品信息后再按页面要求申请复核。','internal_rule_basis':'内部规则R123','internal_judgment_detail':'测试内部判定明细'},
                {'notice_id':'test-2','date':'2026-10-18','subject':COMPANY,'reason':'商品信息需完善','object_type':'商品','object_name':'测试水果',
                 'actions':['商品不展示'],'effectiveness_status':'已结束','rectification_status':'平台未显示',
                 'detail_read':True,'public_recommendation':'核对商品信息，保持描述完整。'}]}}
    def capture(self,p=None):return w.ingest(self.root,self.s,self.json('capture.json',p or self.payload()),'2026-10-20')
    def copy(self):
        b=self.s['batches'][self.batch]
        return {'source_sha256':b['source']['sha256'],'agent_reviewed':True,'facts_preserved':True,'no_internal_rules':True,
                'items':[{'notice_id':r['notice_id'],'gentle_reason':'相关商品信息需要进一步完善。','recommendation':r['public_recommendation']} for r in b['records']]}
    def artifacts(self):
        b=self.s['batches'][self.batch];files=[]
        for kind,body in [('workbook',b'fake-xlsx'),('analysis_image',b'\x89PNG\r\n\x1a\nsummary'),('records_image',b'\x89PNG\r\n\x1a\nrecords')]:
            p=self.root/(kind+'.dat');p.write_bytes(body)
            f={'kind':kind,'path':str(p),'sha256':w.sha(p)}
            if kind!='workbook':f.update(first_row=1,last_row=1 if kind=='analysis_image' else 2,row_count=1 if kind=='analysis_image' else 2,total_rows=1 if kind=='analysis_image' else 2,headers_repeated=True)
            files.append(f)
        b['artifacts']={'source_sha256':b['source']['sha256'],'files':files}
    def screenshot(self,ids=None):
        b=self.s['batches'][self.batch];image=self.root/'list.png';image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
        m={'source_sha256':b['source']['sha256'],'sha256':w.sha(image),'source':'fixture',
           'filters_visible':True,'list_headers_visible':True,'notice_ids':ids or ['test-1','test-2']}
        w.add_screenshot(self.root,self.s,self.batch,image,self.json('screenshot.json',m))
    def ready(self):
        self.capture();self.artifacts();w.set_copy(self.root,self.s,self.batch,self.json('copy.json',self.copy()));self.screenshot()
    def test_date_mismatch_rejected(self):
        p=self.payload();p['analysis']['start']='2026-09-20'
        with self.assertRaisesRegex(ValueError,'date-mismatch'):self.capture(p)
    def test_client_reply_identifies_object_without_repeating_hostile_original(self):
        p=self.payload();r=p['records']['rows'][0]
        r.update(object_type='评价',object_subtype='商家回复',object_name='真是什么人都有',actions=['平台对该回复下线'],effectiveness_status='生效中',
                 detail_object_type_basis={'object_id':'7697150429360080930','normalized_type_basis':{'method':'exact-comment-field-source-object-and-reply-disposal-v1','subtype':'商家回复','source_disposal':'平台对该回复下线'}})
        self.capture(p);w.set_copy(self.root,self.s,self.batch,self.json('copy.json',self.copy()))
        b=self.s['batches'][self.batch];text=Path(b['copy']['path']).read_text()
        self.assertNotIn('真是什么人都有',text);self.assertIn('评价商家回复（评价ID：7697150429360080930）',text)
        self.assertIn('平台对该回复下线（生效中）',text);self.assertEqual(b['records'][0]['object_name'],'真是什么人都有')
    def test_client_reply_missing_proof_refuses_instead_of_repeating_original(self):
        r={'object_type':'评价','object_subtype':'商家回复','object_name':'不友善原文'}
        with self.assertRaisesRegex(ValueError,'client-reply-object-proof-required'):w.client_object_label(r)
    def test_top10_and_partial_page_rejected(self):
        for section,field in [('analysis','all_reasons_read'),('analysis','all_pages_read'),('records','all_pages_read')]:
            p=self.payload();p[section][field]=False
            with self.subTest(section=section,field=field),self.assertRaises(ValueError):self.capture(p)
    def test_unread_only_or_waiting_scope_rejected(self):
        p=self.payload();p['records']['unread_only']=True
        with self.assertRaises(ValueError):self.capture(p)
        p=self.payload();p['records']['scope']='待整改'
        with self.assertRaises(ValueError):self.capture(p)
    def test_analysis_and_records_totals_must_reconcile(self):
        p=self.payload();p['analysis']['total']=3;p['analysis']['rows'][0]['count']=3
        with self.assertRaisesRegex(ValueError,'reconciliation'):self.capture(p)
    def test_duplicate_or_outside_date_rejected(self):
        for field,value in [('notice_id','test-1'),('date','2026-10-20')]:
            p=self.payload();p['records']['rows'][1][field]=value
            with self.assertRaises(ValueError):self.capture(p)
    def test_detail_missing_or_truncated_rejected(self):
        p=self.payload();p['records']['rows'][0]['detail_read']=False
        with self.assertRaises(ValueError):self.capture(p)
        p=self.payload();p['records']['rows'][0]['subject']='店铺…'
        with self.assertRaises(ValueError):self.capture(p)
    def test_account_change_rejected(self):
        self.capture();p=self.payload();p['identity']['account_id']='different'
        with self.assertRaisesRegex(ValueError,'account-changed'):self.capture(p)
    def test_zero_no_table_no_notification(self):
        p=self.payload()
        for section in ('analysis','records'):p[section]['total']=0;p[section]['rows']=[]
        self.capture(p);w.complete(self.root,self.s,self.batch)
        self.assertEqual(self.s['next_start'],'2026-10-20');self.assertEqual(self.s['batches'][self.batch]['status'],'zero_no_notification')
        self.assertFalse((self.root/'batches').exists())
    def test_unknown_zero_cannot_finish(self):
        p=self.payload();p['analysis']['total']=0;p['analysis']['rows']=[]
        with self.assertRaises(ValueError):self.capture(p)
    def test_exact_actions_status_preserved_in_gentle_copy(self):
        self.ready();text=Path(self.s['batches'][self.batch]['copy']['path']).read_text()
        self.assertIn('下架商品；扣分2分（已生效）',text);self.assertIn('商品不展示（已结束）',text)
    def test_pending_deduction_keeps_per_action_stages_instead_of_aggregate_status(self):
        p=self.payload();r=p['records']['rows'][0]
        r.update(actions=['直播间警告','创作者信用分扣分'],effectiveness_status='已生效',
                 action_details=[{'action':'直播间警告','status':'已生效'},{'action':'创作者信用分扣分','status':'待生效'}],
                 disposal_stage_text='直播间警告（已生效）；创作者信用分扣分（待生效，直播分-6分）')
        self.capture(p);w.set_copy(self.root,self.s,self.batch,self.json('copy.json',self.copy()))
        text=Path(self.s['batches'][self.batch]['copy']['path']).read_text()
        self.assertIn('处置方式：直播间警告；创作者信用分扣分\n',text)
        self.assertIn('处置状态：'+r['disposal_stage_text'],text)
        self.assertNotIn('创作者信用分扣分（已生效）',text)
        order=w.copy_order(self.s,self.batch)['items'][0]
        self.assertEqual(order['action_details'],r['action_details']);self.assertEqual(order['disposal_stage_text'],r['disposal_stage_text'])
        self.assertIn(COMPANY,text);self.assertNotIn('内部规则R123',text)
    def test_internal_rules_or_accusations_rejected(self):
        self.capture();p=self.copy();p['items'][0]['recommendation']='依据内部规则R123执行'
        with self.assertRaises(ValueError):w.set_copy(self.root,self.s,self.batch,self.json('copy.json',p))
    def test_copy_missing_id_rejected(self):
        self.capture();p=self.copy();p['items'][1]['notice_id']='test-1'
        with self.assertRaises(ValueError):w.set_copy(self.root,self.s,self.batch,self.json('copy.json',p))
    def test_whole_table_and_source_screenshot_required(self):
        self.capture();self.artifacts();w.set_copy(self.root,self.s,self.batch,self.json('copy.json',self.copy()))
        self.screenshot(['test-1'])
        with self.assertRaisesRegex(ValueError,'coverage-incomplete'):w.send_orders(self.s,self.batch)
    def test_missing_image_page_rejected(self):
        self.ready();b=self.s['batches'][self.batch];b['artifacts']['files'][2]['last_row']=1;b['artifacts']['files'][2]['row_count']=1
        with self.assertRaisesRegex(ValueError,'not-complete'):w.send_orders(self.s,self.batch)
    def test_orders_fixed_test_target_and_sequence(self):
        self.ready();a=w.send_orders(self.s,self.batch);b=w.send_orders(self.s,self.batch)
        self.assertEqual(a,b);self.assertEqual(a[-2]['part'],'public_text');self.assertTrue(a[-1]['part'].startswith('source_list'))
        self.assertTrue(all(o['target']=='测试群请忽略' and o['scope']=='test' for o in a))
    def test_fixture_never_sends(self):
        with self.assertRaisesRegex(ValueError,'fixture-external'):w.dispatch(self.root,self.s,self.batch)
    def test_nonzero_cannot_complete_without_receipts(self):
        self.ready()
        with self.assertRaisesRegex(ValueError,'not-complete'):w.complete(self.root,self.s,self.batch)
        self.assertEqual(self.s['next_start'],'2026-10-16')
    def test_message_unknown_stops_and_wrong_group_fails(self):
        self.ready();o=w.send_orders(self.s,self.batch)[0]
        job={'key':o['key'],'target':'测试群请忽略','kind':'group','scope':'test','type':'file','file_sha256':o['file_sha256']}
        p={'job':job,'fingerprint':w.fingerprint(job),'status':'unknown','phase':'verify-sent','ui_confirmed':False}
        with self.assertRaisesRegex(ValueError,'no-resend'):w.accept_receipt(self.root,self.s,self.batch,o['part'],self.json('receipt.json',p))
        job['target']='生产群';p.update(status='complete',phase='done',ui_confirmed=True,fingerprint=w.fingerprint(job))
        with self.assertRaises(ValueError):w.accept_receipt(self.root,self.s,self.batch,o['part'],self.json('receipt.json',p))
    def test_all_ui_confirmed_then_complete_idempotent(self):
        self.ready()
        for n,o in enumerate(w.send_orders(self.s,self.batch)):
            job={'key':o['key'],'target':'测试群请忽略','kind':'group','scope':'test','type':o['type']}
            if o['type']=='file':job['file_sha256']=o['file_sha256']
            else:job['text']=Path(o['text_file']).read_text()
            p={'job':job,'fingerprint':w.fingerprint(job),'status':'complete','phase':'done','ui_confirmed':True}
            w.accept_receipt(self.root,self.s,self.batch,o['part'],self.json('receipt'+str(n)+'.json',p))
        w.complete(self.root,self.s,self.batch);n=len(self.s['events']);w.complete(self.root,self.s,self.batch)
        self.assertEqual(len(self.s['events']),n);self.assertEqual(self.s['next_start'],'2026-10-20')
    def test_complete_cannot_skip_older_gap(self):
        p=self.payload();p['start']='2026-10-19'
        for section in ('analysis','records'):p[section].update(start='2026-10-19',total=0,rows=[])
        self.capture(p);w.complete(self.root,self.s,'2026-10-19_2026-10-20');self.assertEqual(self.s['next_start'],'2026-10-16')
    def test_catchup_preserves_missed_dates(self):
        p=w.plan(self.s,'2026-10-22');self.assertEqual(p['start'],'2026-10-16');self.assertEqual(p['end'],'2026-10-21')
    def test_rename_ended_state_not_allowed_via_copy(self):
        self.ready();text=Path(self.s['batches'][self.batch]['copy']['path']).read_text()
        self.assertEqual(text.count('（已生效）'),1);self.assertEqual(text.count('（已结束）'),1)
    def test_immutable_after_sender_job_prepared(self):
        self.ready();self.s['batches'][self.batch]['send_jobs']['x']={'confirmed':False}
        with self.assertRaises(ValueError):w.set_copy(self.root,self.s,self.batch,self.json('new-copy.json',self.copy()))
    def test_routing_two_brand_groups(self):
        self.assertEqual(w.route(COMPANY)[1],'榴哆哆全案运营沟通群')
        self.assertEqual(w.route('上海老芗汇餐饮管理有限公司')[1],'地锅岁月抖音运营群')
    def test_long_copy_splits_only_between_notices(self):
        p=self.payload();base=copy.deepcopy(p['records']['rows'][0])
        p['records']['rows']=[{**copy.deepcopy(base),'notice_id':f'long-{i}'} for i in range(24)]
        p['records']['total']=24;p['analysis']['total']=24;p['analysis']['rows'][0]['count']=24
        self.capture(p);c=self.copy()
        for item in c['items']:item['gentle_reason']='商品资料需补充。'*60;item['recommendation']='请核对页面资料并补充。'*30
        w.set_copy(self.root,self.s,self.batch,self.json('long-copy.json',c))
        b=self.s['batches'][self.batch];self.assertGreater(len(b['copy_parts']),1)
        for part in b['copy_parts']:
            text=Path(part['path']).read_text();self.assertLessEqual(len(text),10000)
            self.assertTrue(text.startswith('违规汇总 24 条（第'))
        all_text=''.join(Path(p['path']).read_text() for p in b['copy_parts'])
        for i in range(1,25):self.assertEqual(all_text.splitlines().count(f'{i}. 测试水果一店'),1)

    def test_bridge_screenshot_source_matches_pinned_backend(self):
        self.capture();self.s['mode']='development';self.s['browser_backend']='local-dom-bridge'
        image=self.root/'bridge-mock.png';image.write_bytes(b'\x89PNG\r\n\x1a\nmock')
        m={'source_sha256':self.s['batches'][self.batch]['source']['sha256'],'sha256':w.sha(image),'source':'codex-existing-extension','filters_visible':True,'list_headers_visible':True,'notice_ids':['test-1']}
        with self.assertRaisesRegex(ValueError,'screenshot-source-invalid'):
            w.add_screenshot(self.root,self.s,self.batch,image,self.json('wrong-source.json',m))
        m['source']='local-dom-bridge'
        with self.assertRaisesRegex(ValueError,'screenshot-chain-pinned-source-required'):
            w.add_screenshot(self.root,self.s,self.batch,image,self.json('bridge-source.json',m))
        self.assertEqual(len(self.s['batches'][self.batch]['screenshots']),0)
        # The historical Codex route retains its existing metadata contract.
        self.s['browser_backend']='codex-existing-extension';m['source']='codex-existing-extension'
        w.add_screenshot(self.root,self.s,self.batch,image,self.json('legacy-source.json',m))
        self.assertEqual(len(self.s['batches'][self.batch]['screenshots']),1)

class BackendTests(unittest.TestCase):
    def test_source_backend_pinned_and_defaults_compatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            s=w.initialize(root,COMPANY,'2026-10-20','2026-10-16',backend='local-dom-bridge')
            self.assertEqual(w.plan(s,'2026-10-20')['browser_backend'],'local-dom-bridge')
            self.assertEqual(w.initialize(root,COMPANY,backend='local-dom-bridge')['browser_backend'],'local-dom-bridge')
            with self.assertRaisesRegex(ValueError,'backend-conflict'):w.initialize(root,COMPANY)
        with tempfile.TemporaryDirectory() as tmp:
            s=w.initialize(Path(tmp),COMPANY,'2026-10-20','2026-10-16')
            self.assertEqual(s['browser_backend'],'codex-existing-extension')

    def test_bridge_source_not_codex_and_fixture_stays_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=w.initialize(Path(tmp),COMPANY,'2026-10-20','2026-10-16',backend='local-dom-bridge')
            p={'company':COMPANY,'groupid':s['groupid'],'url':'https://life.douyin.com/?groupid='+s['groupid'],'source':'codex-existing-extension'}
            with self.assertRaisesRegex(ValueError,'source-invalid'):w.check_source(p,s,'2026-10-20')
            from unittest.mock import patch
            from datetime import date
            p.update(source='local-dom-bridge',observed_at='2026-10-20T10:00:00+08:00',account_verified=True,identity={'provider':'p','account_id':'a','manager':'m'},start='2026-10-16',end_exclusive='2026-10-20')
            with patch.object(w,'shanghai_today',return_value=date(2026,10,20)):
                self.assertEqual(w.check_source(p,s,'2026-10-20'),p['identity'])
            s['mode']='fixture';p['source']='local-dom-bridge'
            with self.assertRaisesRegex(ValueError,'source-invalid'):w.check_source(p,s,'2026-10-20')

    def test_unknown_backend_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'backend-invalid'):
                w.initialize(Path(tmp),COMPANY,backend='debug-service')

if __name__=='__main__':unittest.main()
