"""Pure mock navigation: no live Chrome, WeCom or complaint ledger."""
import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
spec=importlib.util.spec_from_file_location('negative_navigation_test',SCRIPTS/'bridge-navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
IDENTITY={'provider':'服务商123456789','account_id':'987654321','manager':'测试经理'}
def leaf(name,selector,**kw):return {'name':name,'selector':selector,'children':[],**kw}
def tree():return {'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'children':[
 leaf('服务商123456789','#provider'),leaf('账户ID987654321','#account'),leaf('我的客户经理测试经理 切换公司','#manager'),
 *[leaf(name,'#'+str(i),role='textbox',attributes={'value':value}) for i,(name,value) in enumerate([('评价时间','2026-10-16 ~ 2026-10-19'),('评价类型','全部'),('评价来源','全部'),('评价状态','全部')])],
 leaf('按省市 全部门店','#scope',attributes={'id':'CommentPoi_select'}),leaf('中差评（1-3心）','#negative',attributes={'class':'option-YmRyn3'})]}}
class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.state=self.root/'navigation.json'
        self.job={'company':'测试公司','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-20','account_verified':True,'identity':IDENTITY}
        self.t=tree();self.calls=[];self.group='123';self.fail=False
    def bridge(self,c):
        self.calls.append(c)
        if c['op']=='tabs':result=[{'tabs':[{'tabId':5,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid='+self.group}]}]
        elif c['op']=='ping':result={'version':m.VERSION,'safety':'DOM-only'}
        elif c['op']=='tree':result=self.t
        elif c['op']=='click':
            s=json.loads(self.state.read_text());assert s['calls'][-1]['state']=='unknown'
            if self.fail:raise TimeoutError('unknown click')
            self.t['root']['children'][-1]['attributes']['class']='unknown-active-class';result={'clicked':True}
        else:raise AssertionError(c)
        return {'ok':True,'result':result}
    def tick(self):
        n=m.Navigator(self.job,5,self.state,self.bridge);n.tick();n.save();return n
    def test_known_dates_and_unselected_negative_click_then_hold_for_real_profile(self):
        with patch.object(m,'navigation_probe',return_value={'normal_count':1,'rows':['fixture-only']}):
            for i in range(5):n=self.tick()
        self.assertEqual(n.s['phase'],'profileRequired');self.assertFalse(n.s['profile_accepted']);self.assertFalse(n.s['submission_enabled'])
        self.assertEqual(sum(c['op']=='click' for c in self.calls),1);before=len(self.calls);self.tick();self.assertEqual(len(self.calls),before)
        self.assertFalse((self.root/'state.json').exists())
    def test_reviewed_home_menu_navigation_is_once_and_identity_bound(self):
        self.t['url']='https://life.douyin.com/p/home'
        self.t['root']['children'].append(leaf('评价管理','#review-menu',attributes={'class':'navi_evaluation public-menu'}))
        original=self.bridge
        def dispatch(c):
            if c['op']=='tabs':
                return {'ok':True,'result':[{'tabs':[{'tabId':5,'allowed':True,'url':self.t['url']+'?groupid=123'}]}]}
            return original(c)
        n=m.Navigator(self.job,5,self.state,dispatch);n.tick();n.save()
        self.assertTrue(n.s['review_entry_dispatched'])
        n.tick();n.save()
        self.assertEqual(n.s['waiting_for'],'review-menu-navigation-settling')
        self.assertEqual(len([c for c in self.calls if c['op']=='click']),1)
        self.assertEqual(next(c for c in self.calls if c['op']=='click')['locator']['value'],'#review-menu')

    def test_readonly_parser_upgrade_preserves_job_calls_and_pins_old_bytes(self):
        self.tick();self.tick();n=self.tick();before=self.state.read_bytes();job=copy.deepcopy(self.job);calls=copy.deepcopy(n.s['calls'])
        n.set_text_schema('public-visible-text-v2',m.digest(self.state))
        self.assertEqual(self.job,job);self.assertEqual(n.s['calls'],calls)
        contract=n.s['parser_contract'];self.assertEqual(Path(contract['previous_state_path']).read_bytes(),before)
        self.assertEqual(contract['job_fingerprint'],m.tag(job))
        with patch.object(m,'navigation_probe',return_value={'normal_count':1}) as probe:
            n.tick();probe.assert_called_once_with(self.t,self.job,text_schema='public-visible-text-v2')
        with self.assertRaisesRegex(ValueError,'not-empty-observation'):n.set_text_schema('public-visible-text-v2',m.digest(self.state))
    def test_parser_upgrade_refuses_wrong_hash_and_before_observe(self):
        n=self.tick()
        with self.assertRaisesRegex(ValueError,'state-hash'):n.set_text_schema('public-visible-text-v2','0'*64)
        with self.assertRaisesRegex(ValueError,'not-empty-observation'):n.set_text_schema('public-visible-text-v2',m.digest(self.state))

    def test_unknown_click_is_never_replayed(self):
        self.tick();self.tick();self.fail=True
        with self.assertRaises(TimeoutError):self.tick()
        self.fail=False
        with self.assertRaisesRegex(ValueError,'unknown-no-replay'):self.tick()
        self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
    def test_wrong_company_stops_before_any_click(self):
        self.group='999'
        with self.assertRaisesRegex(ValueError,'source-company'):self.tick()
        self.assertFalse(any(c['op']=='click' for c in self.calls))
    def test_changed_date_before_negative_filter_is_not_clicked(self):
        self.tick();self.tick();self.t['root']['children'][3]['attributes']['value']='2026-10-18 ~ 2026-10-19'
        with self.assertRaisesRegex(ValueError,'date-changed'):self.tick()
        self.assertFalse(any(c['op']=='click' for c in self.calls))
    def test_observed_css_selected_negative_is_not_clicked_again(self):
        self.tick();self.tick();self.t['root']['children'][-1]['attributes']['class']='option-YmRyn3 isSelected-ov8pOi'
        n=self.tick();self.assertEqual(n.s['phase'],'observeNegative');self.assertFalse(any(c['op']=='click' for c in self.calls))

    def test_already_active_unknown_class_stops_instead_of_toggling(self):
        self.tick();self.tick();self.t['root']['children'][-1]['attributes']['class']='unobserved-active-class'
        with self.assertRaisesRegex(ValueError,'needs-live-profile'):self.tick()
        self.assertFalse(any(c['op']=='click' for c in self.calls))
    def test_identity_changed_or_other_filter_not_all_refused(self):
        self.t['root']['children'][2]['name']='我的客户经理其他 切换公司'
        with self.assertRaisesRegex(ValueError,'account-changed'):self.tick()
        self.t=tree();self.tick();self.t['root']['children'][4]['attributes']['value']='差评'
        with self.assertRaisesRegex(ValueError,'nondefault-filter'):self.tick()
    def test_job_must_not_change_between_ticks(self):
        self.tick();self.job['start']='2026-10-17'
        with self.assertRaisesRegex(ValueError,'state-scope-conflict'):self.tick()
    def test_navigation_job_is_derived_only_from_pinned_current_receipt(self):
        source=self.root/'fixture.xlsx';source.write_bytes(b'fixture only; no live data')
        receipt={'operator_skill':'douyin-laike-operator','work_order_id':'current-fixture','company':'测试公司','groupid':'123','date_range':{'start':'2026-10-16','end':'2026-10-19'},'backend':'local-dom-bridge','download_verified':True,'source_is_authoritative_export':True,'account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,'source':str(source),'src_sha256':m.digest(source),'bytes':source.stat().st_size}
        path=self.root/'receipt.json';m.write_json(path,receipt);checksum=m.digest(path)
        job=m.job_from_receipt(path,'current-fixture',checksum);self.assertEqual(job['end_exclusive'],'2026-10-20');self.assertEqual(job['source_work_order_id'],'current-fixture')
        with self.assertRaisesRegex(ValueError,'current-source'):m.job_from_receipt(path,'historical-fixture',checksum)
        with self.assertRaisesRegex(ValueError,'receipt-hash'):m.job_from_receipt(path,'current-fixture','0'*64)
        source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'file-changed'):m.job_from_receipt(path,'current-fixture',checksum)
    def test_observe_waits_for_two_identical_reads_without_reclick(self):
        self.tick();self.tick();self.tick()
        with patch.object(m,'navigation_probe',side_effect=[ValueError('loading'),{'normal_count':1},{'normal_count':2},{'normal_count':2}]):
            for expected in [0,1,1,2]:
                result=self.tick();self.assertEqual(result.s['stable_observations'],expected)
        self.assertEqual(result.s['phase'],'profileRequired');self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
        refs=result.s['stable_read_evidence'];self.assertEqual(len({x['path'] for x in refs}),len(refs))
    def test_loading_never_completes_and_observation_is_bounded(self):
        self.tick();self.tick();self.tick()
        with patch.object(m,'navigation_probe',side_effect=ValueError('loading')):
            for _ in range(8):self.assertEqual(self.tick().s['phase'],'observeNegative')
            with self.assertRaisesRegex(ValueError,'attempt-limit'):self.tick()
        self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
    def test_default_store_tab_selects_current_dynamic_all_reviews_once(self):
        normal=tree();self.t={'url':normal['url'],'truncated':False,'root':{'children':normal['root']['children'][:3]+[leaf('全部评价 4383','#current-all',attributes={})]}}
        original=self.bridge
        def dispatch(command):
            if command['op']=='click' and command['locator']['value']=='#current-all':
                self.calls.append(command);self.t=tree();return {'ok':True,'result':{'clicked':True}}
            return original(command)
        n=m.Navigator(self.job,5,self.state,dispatch)
        for _ in range(3):n.tick();n.save()
        clicks=[c for c in self.calls if c['op']=='click'];self.assertEqual(len(clicks),1);self.assertEqual(clicks[0]['kind'],'navigation');self.assertEqual(n.s['phase'],'negativeFilter')
if __name__=='__main__':unittest.main()
