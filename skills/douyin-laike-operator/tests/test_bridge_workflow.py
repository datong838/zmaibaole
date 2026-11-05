"""Pure mocks only; never opens Chrome or calls the local bridge."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import timedelta
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('bridge_workflow_tests',SCRIPTS/'bridge-workflow.py')
bw=importlib.util.module_from_spec(spec);spec.loader.exec_module(bw)
IDENTITY={'provider':'服务商123456789','account_id':'987654321','manager':'李先生'}
def leaf(name,**kw):return {'name':name,'selector':'#'+name,'children':[],**kw}
def tree(*extra):return {'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'children':[leaf('服务商123456789'),leaf('账户ID'),leaf('987654321'),leaf('我的客户经理'),leaf('李先生'),*extra]}}
class Mock:
    def __init__(self,group='123'):
        self.group=group;self.calls=[];self.t=tree(leaf('切换公司',role='button'));self.fail_mutation=False;self.changed_after_read=False
    def __call__(self,c):
        self.calls.append(copy.deepcopy(c));op=c['op']
        if op=='tabs':return {'ok':True,'result':[{'tabs':[{'tabId':5,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid='+self.group}]}]}
        if op=='ping':return {'ok':True,'result':{'version':bw.VERSION,'safety':'DOM-only'}}
        if op=='tree':
            if self.changed_after_read:self.group='999'
            return {'ok':True,'result':self.t}
        if self.fail_mutation:raise TimeoutError('injected unknown click outcome')
        return {'ok':True,'result':{'clicked':True}}
    def mutations(self):return [x for x in self.calls if x['op'] not in ('tabs','ping','tree')]
class BridgeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job={'action':'acquire','work_order_id':'fixture-order','company':'fixture','groupid':'123','date_range':{'start':'2026-10-17','end':'2026-10-19'},'source_dir':str(self.root/'sources'),'workflow_path':str(self.root/'workflow.json')}
        self.mock=Mock()
    def workflow(self):return bw.Workflow(self.job,5,self.mock)
    def test_async_company_search_waits_readonly_then_selects_unique_result(self):
        w=self.workflow();w.s.update(phase='chooseCompany',initial_groupid='123');w.save()
        field=leaf('',role='textbox',placeholder='搜索商户',attributes={'value':self.job['company']})
        self.mock.t=tree(field);w.tick()
        self.assertEqual(w.s['waiting_for'],'company-search-results');self.assertFalse(self.mock.mutations())
        self.mock.t=tree(field,leaf(self.job['company']));w.tick()
        self.assertEqual(w.s['phase'],'confirmSwitch');self.assertNotIn('waiting_for',w.s)
        self.assertEqual(len(self.mock.mutations()),1)
    def test_async_switch_only_waits_for_original_or_target_company(self):
        w=self.workflow();w.s.update(phase='verifySwitch',initial_groupid='old');w.save()
        self.mock.group='old';w.tick()
        self.assertEqual(w.s['waiting_for'],'company-switch-result');self.assertFalse(self.mock.mutations())
        self.mock.group='other'
        with self.assertRaisesRegex(ValueError,'source-company-mismatch'):w.tick()
        self.mock.group='123';w.tick()
        self.assertEqual(w.s['phase'],'accountAfterSwitch');self.assertNotIn('waiting_for',w.s)
        self.assertFalse(self.mock.mutations())
    def test_company_home_routes_through_review_menu_once(self):
        w=self.workflow();w.s.update(phase='openReviews',initial_groupid='123');w.save()
        self.mock.t=tree(leaf('评价管理'));w.tick()
        self.assertEqual(w.s['phase'],'waitReviewManagement');self.assertEqual(len(self.mock.mutations()),1)
        w.tick();self.assertEqual(w.s['waiting_for'],'review-management-load');self.assertEqual(len(self.mock.mutations()),1)
        self.mock.t=tree(leaf('评价管理'),leaf('全部评价 12'));w.tick()
        self.assertEqual(w.s['phase'],'openReviews');w.tick()
        self.assertEqual(w.s['phase'],'readReviewFilters');self.assertEqual(len(self.mock.mutations()),2)
    def test_background_source_is_activated_before_read_or_navigation(self):
        active=False;commands=[];original=self.mock
        def invoke(c):
            nonlocal active
            commands.append(c)
            if c['op']=='tabs':return {'ok':True,'result':[{'windowId':3,'focused':active,'tabs':[{'tabId':5,'windowId':3,'active':active,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]}
            if c['op']=='activate':active=True;return {'ok':True,'result':{'tabId':5,'active':True,'windowFocused':True}}
            return original(c)
        w=bw.Workflow(self.job,5,invoke);w.s.update(phase='openReviews',initial_groupid='123');w.save();self.mock.t=tree(leaf('全部评价 12'))
        w.tick();self.assertTrue(active);self.assertEqual(w.s['phase'],'readReviewFilters')
        self.assertLess(next(i for i,c in enumerate(commands) if c['op']=='activate'),next(i for i,c in enumerate(commands) if c['op']=='tree'))
    def test_unknown_source_focus_reconciles_public_state_without_reactivation(self):
        active=False;activations=0
        def invoke(c):
            nonlocal active,activations
            if c['op']=='tabs':return {'ok':True,'result':[{'windowId':3,'focused':active,'tabs':[{'tabId':5,'windowId':3,'active':active,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]}
            if c['op']=='activate':active=True;activations+=1;raise TimeoutError('focus reply lost')
            return self.mock(c)
        w=bw.Workflow(self.job,5,invoke);w.s.update(phase='openReviews',initial_groupid='123');w.save();self.mock.t=tree(leaf('全部评价 12'))
        with self.assertRaises(TimeoutError):w.tick()
        w.tick();self.assertEqual(activations,1);self.assertEqual(w.s['phase'],'readReviewFilters')
        self.assertTrue(next(c for c in w.s['calls'] if c['command']['op']=='activate')['result']['observed'])
    def test_onboarding_closes_once_then_resumes_original_phase(self):
        guide={'name':'新来客 新生意 抖音来客全新升级! 导航升级 首页升级 立即体验','selector':'#guide','attributes':{'class':'src-pages-HomeV3-components-Guide-index-module__guide-modal--observed'},'children':[leaf('立即体验',role='button')]}
        w=self.workflow();w.s.update(phase='openReviews',initial_groupid='123');w.save();self.mock.t=tree(guide)
        w.tick();self.assertEqual(w.s['phase'],'dismissOnboarding');self.assertFalse(self.mock.mutations())
        w.tick();self.assertEqual(w.s['phase'],'waitOnboardingClosed');self.assertEqual(len(self.mock.mutations()),1)
        w.tick();self.assertEqual(w.s['waiting_for'],'onboarding-close');self.assertEqual(len(self.mock.mutations()),1)
        self.mock.t=tree(leaf('全部评价 12'));w.tick();self.assertEqual(w.s['phase'],'openReviews')
    def test_ambiguous_company_search_or_changed_input_never_selects(self):
        for changed in (True,False):
            w=self.workflow();w.s.update(phase='chooseCompany',initial_groupid='123');w.save()
            field=leaf('',role='textbox',placeholder='搜索商户',attributes={'value':'other' if changed else self.job['company']})
            self.mock.t=tree(field,*([] if changed else [leaf(self.job['company']),leaf(self.job['company'],role='button')]))
            with self.assertRaises(ValueError):w.tick()
            self.assertFalse(self.mock.mutations())
    def old(self,**kw):
        value={'version':1,'work_order_id':self.job['work_order_id'],'company':self.job['company'],'groupid':self.job['groupid'],'date_range':self.job['date_range'],'fingerprint':bw.legacy_fingerprint(self.job),'state':'failed','error_code':'connection-unavailable','phase':'account','attempts':0,'checkpoints':[]}
        value.update(kw);Path(self.job['workflow_path']).write_text(json.dumps(value));return value
    def recover(self):self.job['recovery_request']={'kind':'connection-recovery','id':'fixture-recovery'}
    def test_unknown_click_not_replayed_after_restart(self):
        w=self.workflow();self.mock.fail_mutation=True
        with self.assertRaises(TimeoutError):w.mutate('click',leaf('fixture'),'navigation')
        self.assertEqual(len(self.mock.mutations()),1)
        w=self.workflow()
        with self.assertRaisesRegex(ValueError,'outcome-unknown'):w.mutate('click',leaf('fixture'),'navigation')
        self.assertEqual(len(self.mock.mutations()),1)
    def test_confirmed_click_result_reused_without_second_request(self):
        w=self.workflow();first=w.mutate('click',leaf('fixture'),'navigation');w=self.workflow()
        self.assertEqual(w.mutate('click',leaf('fixture'),'navigation'),first)
        self.assertEqual(len(self.mock.mutations()),1)
    def test_confirmed_intent_cannot_be_reused_for_different_command(self):
        w=self.workflow();w.mutate('click',leaf('first'),'navigation')
        with self.assertRaisesRegex(ValueError,'command-conflict'):w.mutate('click',leaf('second'),'navigation')
        self.assertEqual(len(self.mock.mutations()),1)
    def test_journal_range_cannot_disagree_with_its_fingerprint(self):
        self.old(date_range={'start':'2026-10-01','end':'2026-10-19'});self.recover()
        with self.assertRaisesRegex(ValueError,'work-order-conflict'):self.workflow()
    def test_allowed_failed_connection_migration_is_archived(self):
        original=self.old();self.recover();w=self.workflow()
        self.assertEqual(w.s['backend'],'local-dom-bridge');self.assertEqual(json.loads(Path(w.s['migration']['archive']).read_text()),original)
        self.assertFalse(self.mock.calls)
    def test_migration_preserves_previously_verified_identity(self):
        self.old(identity={**IDENTITY,'manager':'原经理'});self.recover();w=self.workflow()
        with self.assertRaisesRegex(ValueError,'account-changed'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_migration_needs_explicit_failed_connection(self):
        for changes in ({'state':'running'},{'error_code':'captcha'}):
            self.old(**changes);self.recover()
            with self.assertRaisesRegex(ValueError,'explicit-connection'):self.workflow()
        self.old();self.job.pop('recovery_request',None)
        with self.assertRaisesRegex(ValueError,'explicit-connection'):self.workflow()
    def test_any_old_export_or_download_intent_blocks_migration(self):
        for changes in ({'exportPending':True},{'downloadPending':True},{'attempts':1},{'submittedAt':123},{'result':{'source':'fixture.xlsx'}},{'checkpoints':[{'stage':'export-intent'}]},{'checkpoints':[{'stage':'download-intent'}]},{'phase':'clickDownload'}):
            self.old(**changes);self.recover()
            with self.subTest(changes=changes),self.assertRaisesRegex(ValueError,'side-effect'):self.workflow()
    def test_existing_same_backend_can_reconcile_its_own_export_intent(self):
        w=self.workflow();w.s['exportPending']=True;w.s['phase']='pollRecords';w.save()
        self.job['resume']={'export_pending':True,'checkpoints':[{'stage':'export-intent'}]}
        resumed=self.workflow()
        self.assertTrue(resumed.s['exportPending']);self.assertFalse(self.mock.mutations())
    def test_return_company_finishes_without_review_or_export(self):
        self.job.update(action='return-company',identity_baseline=IDENTITY)
        self.job.pop('date_range');self.job.pop('source_dir')
        w=self.workflow();w.tick();w.tick()
        self.assertEqual(w.s['state'],'complete');self.assertTrue(w.s['result']['verified'])
        self.assertFalse(self.mock.mutations())
    def test_job_resume_unknown_intent_also_blocks_new_state(self):
        self.job['resume']={'export_pending':True}
        with self.assertRaisesRegex(ValueError,'side-effect'):self.workflow()
    def test_migration_fingerprint_covers_dates_directory_and_action(self):
        for key,value in [('date_range',{'start':'2026-10-18','end':'2026-10-19'}),('source_dir',str(self.root/'other')),('action','return-company')]:
            original=copy.deepcopy(self.job);self.old();self.recover();self.job[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'work-order-conflict'):self.workflow()
            self.job=original
    def test_account_baseline_mismatch_never_clicks(self):
        self.job['identity_baseline']={**IDENTITY,'manager':'其他人'};w=self.workflow()
        with self.assertRaisesRegex(ValueError,'account-changed'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_initial_group_fixed_and_third_company_refused(self):
        self.mock.group='111';w=self.workflow();w.tick();self.assertEqual(w.s['initial_groupid'],'111')
        self.mock.group='999'
        with self.assertRaisesRegex(ValueError,'source-company'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_target_must_not_replace_initial_before_confirmation(self):
        w=self.workflow();w.s.update(phase='chooseCompany',initial_groupid='111',identity=IDENTITY);w.save()
        with self.assertRaisesRegex(ValueError,'before-confirm'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_verify_after_confirmation_requires_target(self):
        self.mock.group='111';w=self.workflow();w.s.update(phase='verifySwitch',initial_groupid='111',identity=IDENTITY);w.save()
        w.tick();self.assertEqual(w.s['phase'],'verifySwitch');self.assertEqual(w.s['waiting_for'],'company-switch-result')
        w.s['company_switch_wait_started']=(bw.datetime.now(bw.timezone.utc)-timedelta(seconds=61)).isoformat()
        with self.assertRaisesRegex(ValueError,'switch-result-timeout'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_group_changed_during_tree_read_blocks_action(self):
        w=self.workflow();self.mock.changed_after_read=True
        with self.assertRaisesRegex(ValueError,'changed-during-read'):w.tick()
        self.assertFalse(self.mock.mutations())
    def test_tree_path_must_bind_enumerated_tab(self):
        w=self.workflow();self.mock.t['url']='https://life.douyin.com/p/other'
        with self.assertRaisesRegex(ValueError,'tree-context-path'):w.tick()
    def test_second_identity_cannot_replace_first(self):
        w=self.workflow();w.set_identity(IDENTITY)
        with self.assertRaisesRegex(ValueError,'account-changed'):w.set_identity({**IDENTITY,'account_id':'11111111'})
if __name__=='__main__':unittest.main()
