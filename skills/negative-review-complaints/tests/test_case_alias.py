"""Portable SYNTHETIC cases, including all NEW drawer/product evidence.
No test is evidence that the current ve drawer was actually opened or linked.
"""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/'skills/negative-review-complaints/scripts')]
import case_alias as c
import unbound_case_runner as u

def node(name='',cl='',children=None,tag='div',selector=None):
    return {'name':name,'tag':tag,'attributes':{'class':cl},'children':children or [],'selector':selector or '#synthetic-'+str(id(children))+name}
def page(customer='ve'):
    fields=[node(children=[node(k,'label-bygbVJ'),node(v,'text-Fp_RCZ',selector='#value'+str(i))]) for i,(k,v) in enumerate([('投诉类型','其他'),('投诉理由','完整原投诉理由'),('投诉时间','2026-10-20 14:08:45')])]
    d=node(cl='byted-drawer-dialog-show',selector='#drawer',children=[node('投诉评价'),node('投诉审核中','status-head-DNErJ9'),node('店','poiName-W9HDFV'),node(customer,'nickName-wB7fZf'),node('正文','text-Hl9jZe'),node(children=fields,tag='form'),node('','byted-drawer-close-icon',selector='#close')])
    return {'tab':{'tabId':7,'windowId':8,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'},'observed_at':'2026-10-22T05:00:00+00:00','tree':{'kind':'DOM-derived semantic tree (not native AX)','truncated':False,'url':'https://life.douyin.com/p/life_comment/management','root':node(children=[d])}}
def card():return node(cl='commentItem-jrXo5p',selector='#card',children=[node('店','poiName-W9HDFV'),node('ve','nickName-wB7fZf'),node('正文','text-Hl9jZe'),node('已消费完整商品','spuName-j3ysmF'),node('非常差','text-J4lpcH'),node('投诉审核中','button-vhqEd7 isHighlight-DoxxP4',selector='#action')])
class PureTests(unittest.TestCase):
    def setUp(self):
        self.job={'groupid':'123','company':'公司','identity':{'provider':'P','account_id':'A','manager':'M'}};self.old_review={'store':'店','customer':'M.','text':'正文','product':'完整商品','stars':1,'review_key':'123:old'};self.current=c.candidate_fields(card());self.old=c.parse_case(self.job,page('M.'));self.new=c.parse_case(self.job,page());self.pending=[{'review_key':'123:old','review':self.old_review,'case':self.old['case']}]
    def link(self):return c.link(self.old,self.new,self.old_review,self.current,self.pending)
    def test_case_link_is_not_person_identity_or_screenshot_grant(self):
        p=self.link();self.assertFalse(p['person_identity_verified']);self.assertFalse(p['screenshot_authorized']);self.assertEqual(p['original_review_key'],'123:old');self.assertEqual(self.old_review['customer'],'M.')
    def test_case_each_exact_field_and_second_time_required(self):
        for k in self.new['case']:
            with self.subTest(k=k):
                bad=copy.deepcopy(self.new);bad['case'][k]+='x'
                with self.assertRaisesRegex(ValueError,'case-mismatch'):c.link(self.old,bad,self.old_review,self.current,self.pending)
        p=page();p['tree']['root']['children'][0]['children'][5]['children'][2]['children'][1]['name']='2026-10-20 14:08'
        with self.assertRaisesRegex(ValueError,'exact-seconds'):c.parse_case(self.job,p)
    def test_ambiguous_old_pending_or_wrong_group_rejected(self):
        self.pending.append(copy.deepcopy(self.pending[0]))
        with self.assertRaisesRegex(ValueError,'one-to-one'):self.link()
        self.pending.pop();self.new['groupid']='124'
        with self.assertRaisesRegex(ValueError,'identity-mismatch'):self.link()
    def test_product_rating_body_and_customer_binding_not_dropped(self):
        for k,val in [('product','另一商品'),('stars',2),('text','省略')]:
            v={**self.current,k:val}
            with self.subTest(k=k),self.assertRaises(ValueError):c.link(self.old,self.new,self.old_review,v,self.pending)
        self.new['review']['customer']='第三人'
        with self.assertRaisesRegex(ValueError,'drawer-review'):self.link()
    def test_missing_or_duplicate_case_field_or_editable_control_rejected(self):
        for mode in ('missing','duplicate','input'):
            p=page();d=p['tree']['root']['children'][0];rows=d['children'][5]['children']
            if mode=='missing':rows.pop()
            if mode=='duplicate':rows.append(copy.deepcopy(rows[0]))
            if mode=='input':d['children'].append(node(tag='input'))
            with self.subTest(mode=mode),self.assertRaises(ValueError):c.parse_case(self.job,p)
    def test_unknown_product_rating_or_aggregate_not_promoted(self):
        for pos,val in [(3,'完整商品'),(4,'差')]:
            d=card();d['children'][pos]['name']=val
            with self.assertRaises(ValueError):c.candidate_fields(d)
        d=card();d['children'][3]['children']=[node('尾部')]
        with self.assertRaises(ValueError):c.candidate_fields(d)
    def test_whole_normal_scope_and_exact_unique_current_candidate_required(self):
        d=card();p=page();p['tree']['root']=node(children=[d]);env={'pages':[p]};profile={}
        obs={'rows':[{'store':'店','text':'正文','page_index':1,'dom_selector':'#card'}]}
        with patch.object(c.n,'observation',return_value=obs) as check:
            self.assertEqual(c.candidates(self.job,env,profile,self.old_review)[0]['customer'],'ve');check.assert_called_once_with(self.job,env,profile)
            obs['rows']*=2
            with self.assertRaisesRegex(ValueError,'one-to-one'):c.candidates(self.job,env,profile,self.old_review)
    def test_real_task_business_shape_vs_source_dom_metadata_is_exact(self):
        review={'customer':'M.','customer_id':'','date':'2026-10-19','product':'完整商品','review_id':'old','stars':1,'store':'店','text':'正文','time':'2026-10-19T14:12:14+08:00'};source={k:v for k,v in review.items() if k!='customer_id'};source.update(action='投诉审核中',dom_selector='#old',authority={'method':'synthetic'})
        u.task_source_review(review,source)
        for field,value in [('customer','ve'),('time','2026-10-19T14:12:15+08:00'),('stars',2),('product','不完整')]:
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'source-facts'):u.task_source_review({**review,field:value},source)
    def test_original_existing_order_exact_source_key_selector_and_nickname(self):
        r={'review_id':'old','store':'店','customer':'M.','text':'正文','stars':1,'date':'2026-10-19','dom_selector':'#old','action':'投诉审核中'};refs={x:{'path':'/synthetic/'+x,'sha256':x} for x in ('job','source','envelope','profile')};m={'review_key':'123:old','inputs':{'old_'+k:v for k,v in refs.items()}};src={'company':'公司','groupid':'123','start':'2026-10-19','end_exclusive':'2026-10-20'};o={'review_key':'123:old','snapshot_sha256':'source','card_selector':'#old','source_tuple':{k:r[k] for k in ('review_id','store','customer','text','stars','date')},'original_action':'投诉审核中','click_kind':'complaint-read','allowed_actions':['查看投诉结果','投诉审核中'],'never_click':['投诉','再次投诉','提交']};orders={'kind':'existing-complaint-result-orders-v1','submission_enabled':False,'send_enabled':False,'inputs':refs,'company':'公司','groupid':'123','range':{'start':src['start'],'end_exclusive':src['end_exclusive']},'orders':[o]};v={'old_orders':orders,'old_source':src,'old_job':{'company':'公司','groupid':'123'}};u.verify_old_order(v,m,r)
        for field,value in [('card_selector','#wrong'),('snapshot_sha256','wrong'),('click_kind','complaint')]:
            bad=copy.deepcopy(v);bad['old_orders']['orders'][0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'tuple-or-action'):u.verify_old_order(bad,m,r)
        bad=copy.deepcopy(v);bad['old_orders']['orders'][0]['source_tuple']['customer']='ve'
        with self.assertRaisesRegex(ValueError,'tuple-or-action'):u.verify_old_order(bad,m,r)
    def test_document_hash_symlink_and_mutation(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'p';p.write_text('{}');q=c.ref(p);p.write_text('{"x":1}')
            with self.assertRaisesRegex(ValueError,'changed'):c.document(q)
            link=Path(t)/'link';link.symlink_to(p)
            with self.assertRaisesRegex(ValueError,'nonsymlink'):c.ref(link)
class DurableTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.m={'root':str(self.root),'review_key':'123:old','kind':'synthetic-test-manifest'};self.normal=page();self.normal['tree']['root']=node(children=[card()]);self.v={'normal_before':{'pages':[self.normal]},'fresh_job':{'groupid':'123'},'fresh_profile':{},'current':c.candidate_fields(card())};self.calls=[]
        self.patches=[patch.object(u,'now',return_value='2026-10-22T05:00:00+00:00'),patch.object(u,'inputs',return_value=self.v),patch.object(u,'barriers'),patch.object(u,'page_scope',side_effect=lambda p,v,**kw:p),patch.object(u,'verify_complete',return_value={'kind':c.KIND})]
        for p in self.patches:p.start();self.addCleanup(p.stop)
    def statepath(self):return self.root/'existing-result-operations'/u.hashlib.sha256(b'123:old').hexdigest()/'unbound-case/operation.json'
    def request(self,cmd):
        self.calls.append(cmd);return {'kind':'complaint-read','clicked':{'selector':cmd['locator']['value'],'name':'投诉审核中','attributes':{'class':'button-vhqEd7 isHighlight-DoxxP4'}}}
    def tick(self,request=None):return u.tick(self.m,read_page=lambda:self.normal,request=request or self.request)
    def test_intent_persisted_before_input_and_raw_before_guard(self):
        def call(cmd):
            self.assertEqual(json.loads(self.statepath().read_bytes())['state'],'unknown-open');return {'wrong':'raw reply'}
        with self.assertRaises(ValueError):self.tick(call)
        s=json.loads(self.statepath().read_bytes());self.assertEqual(c.document(s['open_reply_raw']),{'wrong':'raw reply'});self.assertEqual(s['state'],'unknown-open')
    def test_unknown_never_replays_even_after_restart(self):
        def fail(cmd):self.calls.append(cmd);raise TimeoutError('synthetic transport outcome unknown')
        with self.assertRaises(TimeoutError):self.tick(fail)
        self.assertEqual(self.tick()['state'],'unknown-open');self.assertEqual(len(self.calls),1)
    def test_changed_manifest_cannot_wash_unknown(self):
        def fail(cmd):raise TimeoutError()
        with self.assertRaises(TimeoutError):self.tick(fail)
        self.m={**self.m,'new_source':'cannot wash'}
        with self.assertRaisesRegex(ValueError,'original-manifest'):self.tick()
    def test_inputs_or_barrier_failure_occurs_before_any_read_or_request(self):
        with patch.object(u,'inputs',side_effect=ValueError('source changed')):
            with self.assertRaisesRegex(ValueError,'source changed'):self.tick()
        self.assertFalse(self.calls)
    def test_full_durable_cycle_replays_real_parser_and_alias_verifier(self):
        # Only original authority/scope are mocked here; saved case parser, replies,
        # commands, immutable refs and receipt verification execute unchanged.
        # Load a second module to exercise the real pure verification API.
        spec=importlib.util.spec_from_file_location('synthetic_alias_replay',ROOT/'skills/negative-review-complaints/scripts/unbound_case_runner.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        job={'groupid':'123','company':'公司','identity':{'provider':'P','account_id':'A','manager':'M'}}
        review={'review_key':'123:old','store':'店','customer':'M.','text':'正文','product':'完整商品','stars':1}
        old=c.parse_case(job,page('M.'));self.v.update(fresh_job=job,review=review,old_case=old,pending=[{'review_key':'123:old','review':review,'case':old['case']}])
        self.m.update(inputs={},old_result={'synthetic':True},old_drawer={'synthetic':True})
        u.verify_complete.side_effect=lambda s:module.verify_complete(s)
        with patch.object(module,'inputs',return_value=self.v),patch.object(module,'page_scope',side_effect=lambda p,v,**kw:p):
            self.tick();self.normal=page()
            def close(cmd):
                self.calls.append(cmd);return {'kind':'complaint-read','clicked':{'selector':'#close','name':'','attributes':{'class':'byted-drawer-close-icon'}}}
            self.tick(close);self.normal=page();self.normal['tree']['root']=node(children=[card()]);out=self.tick();self.assertEqual(out['state'],'complete');self.assertEqual(len(self.calls),2)
            receipt=module.record_reconciled(c.ref(self.statepath()),self.statepath().parent/'alias-receipt.json');proof=module.validate_alias(receipt);self.assertFalse(proof['person_identity_verified']);self.assertEqual(proof['original_review_key'],'123:old')
            # Altering a saved raw reply cannot reuse a complete boolean.
            raw=Path(out['close_reply_raw']['path']);raw.write_text('{}')
            with self.assertRaisesRegex(ValueError,'ref-changed'):module.verify_complete(out)
    def test_unknown_reconciliation_is_explicit_readonly_and_sha_bound(self):
        self.v['fresh_job']={'groupid':'123','company':'公司','identity':{}}
        def fail(cmd):self.calls.append(cmd);raise TimeoutError()
        with self.assertRaises(TimeoutError):self.tick(fail)
        old=c.ref(self.statepath())
        with self.assertRaisesRegex(ValueError,'state-sha'):u.reconcile(self.m,expected_state_sha256='0'*64,read_page=lambda:page())
        out=u.reconcile(self.m,expected_state_sha256=old['sha256'],read_page=lambda:page());self.assertEqual(out['state'],'opened');self.assertFalse(out['open_reconciliation']['ui_used']);self.assertNotIn('open_reply',out);self.assertEqual(len(self.calls),1)
    def test_completed_operation_replays_verifier_without_new_request(self):
        self.tick();s=json.loads(self.statepath().read_bytes());s['state']='complete';u.save(self.statepath(),s);self.calls.clear();self.tick();self.assertFalse(self.calls);u.verify_complete.assert_called_once()
if __name__=='__main__':unittest.main()
