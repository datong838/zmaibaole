"""Pure fixture navigation; no Chrome or WeCom API calls."""
import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('violation_navigation_tests',Path(__file__).resolve().parents[1]/'scripts/bridge-navigation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
IDENTITY={'provider':'服务商123456789','account_id':'987654321','manager':'测试经理'}
def leaf(name,selector):return {'name':name,'selector':selector,'children':[]}
class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.state=self.root/'navigation.json';self.calls=[];self.fail=False;self.path='/p/life_comment/management';self.group='123';self.has_menu=False
        self.plan={'company':'测试公司','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-21','browser_backend':'local-dom-bridge','production_enabled':False,'platform_writes':False,'send_target':'测试群请忽略','has_new_dates':True}
        self.receipt={'operator_skill':'douyin-laike-operator','work_order_id':'fixture-current','backend':'local-dom-bridge','company':'测试公司','groupid':'123','account_verified':True,'identity':IDENTITY,'identity_before':IDENTITY,'date_range':{'start':'2000-01-01','end':'2000-01-02'}}
        self.pp=self.root/'plan.json';self.rp=self.root/'receipt.json';m.write_json(self.pp,self.plan);m.write_json(self.rp,self.receipt)
        self.job=m.prepare(self.pp,m.digest(self.pp),self.rp,m.digest(self.rp),'fixture-current')
    def tree(self):
        children=[leaf('服务商123456789','#provider'),leaf('账户ID987654321','#account'),leaf('我的客户经理测试经理 切换公司','#manager'),leaf('经营保障','#menu')]
        if self.has_menu:children.append(leaf('违规中心','#center'))
        if self.path==m.CENTER:children.extend([leaf('违规分析','#analysis'),leaf('全部 999','#unverified-total')])
        return {'url':'https://life.douyin.com'+self.path,'truncated':False,'root':{'children':children}}
    def bridge(self,c):
        self.calls.append(c)
        if c['op']=='tabs':result=[{'windowId':3,'tabs':[{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+self.path+'?groupid='+self.group}]}]
        elif c['op']=='ping':result={'version':m.VERSION,'safety':'DOM-only'}
        elif c['op']=='tree':result=self.tree()
        elif c['op'] in ('click','hover'):
            saved=json.loads(self.state.read_text());assert saved['calls'][-1]['state']=='unknown'
            if self.fail:raise TimeoutError('unknown test action')
            if c['locator']['value']=='#menu':self.has_menu=True
            elif c['locator']['value']=='#center':self.path=m.CENTER
            result={'clicked':True}
        else:raise AssertionError(c)
        return {'ok':True,'result':result}
    def tick(self):
        n=m.Navigator(self.job,5,self.state,self.bridge);n.tick();n.save();return n
    def test_menu_then_center_then_hold_saves_full_raw_tree(self):
        for _ in range(4):n=self.tick()
        self.assertEqual(n.s['phase'],'profileRequired');self.assertFalse(n.s['zero_verified']);self.assertFalse(n.s['profile_accepted']);self.assertFalse(n.s['business_progress_changed'])
        self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#menu','#center'])
        evidence=json.loads(Path(n.s['last_tree']['path']).read_text());self.assertEqual(evidence['tree'],self.tree());self.assertTrue(evidence['not_business_capture']);self.assertFalse(evidence['full_field_text_verified'])
        before=len(self.calls);self.tick();self.assertEqual(len(self.calls),before);self.assertFalse((self.root/'state.json').exists())
    def test_expanded_menu_skips_parent_toggle(self):
        self.has_menu=True
        for _ in range(4):self.tick()
        self.assertEqual([c['locator']['value'] for c in self.calls if c['op']=='click'],['#center'])
    def test_already_center_observes_only_no_actions(self):
        self.path=m.CENTER
        for _ in range(2):n=self.tick()
        self.assertEqual(n.s['phase'],'profileRequired');self.assertFalse(any(c['op'] in ('click','hover') for c in self.calls))
    def test_unknown_action_never_replayed(self):
        self.tick();self.fail=True
        with self.assertRaises(TimeoutError):self.tick()
        self.fail=False
        with self.assertRaisesRegex(ValueError,'unknown-no-replay'):self.tick()
        self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
    def test_wrong_company_stops_without_tree_or_action(self):
        self.group='999'
        with self.assertRaisesRegex(ValueError,'source-company'):self.tick()
        self.assertEqual([c['op'] for c in self.calls],['tabs'])
    def test_plan_dates_independent_of_identity_receipt_dates(self):
        self.assertEqual(self.job['start'],'2026-10-16');self.assertEqual(self.job['end_exclusive'],'2026-10-21');self.assertNotEqual(self.job['start'],self.receipt['date_range']['start'])
    def test_changed_pinned_plan_or_identity_stops_before_calls(self):
        self.pp.write_text('{}')
        with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):self.tick()
        self.assertFalse(self.calls)
    def test_mutated_job_or_tab_cannot_resume(self):
        self.tick()
        with self.assertRaisesRegex(ValueError,'state-scope-conflict'):m.Navigator(self.job,6,self.state,self.bridge)
    def test_truncated_tree_risk_and_changed_account_stop(self):
        original=self.tree
        for kind in ('truncated','risk','account'):
            def altered():
                t=original()
                if kind=='truncated':t['truncated']=True
                elif kind=='risk':t['root']['children'].append(leaf('风险验证','#risk'))
                else:t['root']['children'][2]['name']='我的客户经理其他 切换公司'
                return t
            self.tree=altered
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.tick()
        self.assertFalse(any(c['op'] in ('click','hover') for c in self.calls))
    def test_ambiguous_center_never_clicks_parent_or_guess(self):
        self.tick();original=self.tree
        def duplicates():
            t=original();t['root']['children'].extend([leaf('违规中心','#a'),leaf('违规中心','#b')]);return t
        self.tree=duplicates
        with self.assertRaises(ValueError):self.tick()
        self.assertFalse(any(c['op']=='click' for c in self.calls))
if __name__=='__main__':unittest.main()
