"""Offline fixtures only; no browser connector or business progress."""
import importlib.util,json,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('navigation_fixture',HERE/'test_bridge_navigation.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
spec=importlib.util.spec_from_file_location('profile_discovery',HERE.parent/'scripts/bridge-profile-discovery.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def n(name='',tag='div',cls='',children=None,**kw):return dict(name=name,tag=tag,role='generic',selector='#'+(name or 'input'),attributes={'class':cls},children=children or [],**kw)
class DiscoveryTests(fixture.NavigationTests):
    # Reuse setup, not the Navigator test cases.
    def setUp(self):
        super().setUp();self.path=m.nav.CENTER;self.version='dom-only-20261021-7';self.state=self.root/'probe.json'
    def tree(self):
        t=super().tree();picker=n('', 'input','governance_merchant-input',placeholder=m.PLACEHOLDER);picker['role']='textbox';picker['selector']='#date'
        t['root']['children'].append(dict(n(children=[n(cls='governance_merchant-date-picker governance_merchant-date-picker-range',children=[picker]),n('常用工具 违规记录 新增21',cls='todoSummary-xpJGcr',children=[n('违规记录 新增21',cls='todoItem-SQ0SNc',children=[n('违规记录','p','todoLabel-I3rSqB')])]),n(cls='topList-DDjs8Y',children=[n('违规原因 Top10',cls='title-KYD1nB'),n('全部','span','viewAllText-W89JWE')])]),attributes={'id':'governanceRoot'}))
        return t
    def bridge(self,c):
        if c['op']=='ping':self.calls.append(c);return {'ok':True,'result':{'version':self.version,'safety':'DOM-only'}}
        if c['op']=='click':
            self.calls.append(c);self.assertEqual(json.loads(self.state.read_text())['calls'][-1]['state'],'unknown')
            if self.fail:raise TimeoutError('unknown')
            return {'ok':True,'result':{'clicked':True}}
        return super().bridge(c)
    def step(self,mode='picker'):
        p=m.Probe(self.job,5,self.state,mode,self.bridge);p.step();return p
    def test_v7_observes_without_click_or_intent(self):
        p=self.step();self.assertEqual(p.s['waiting_for'],'reviewed-governance-current-policy-required');self.assertEqual(p.s['calls'],[]);self.assertEqual(p.s['observed_target']['selector'],'#date');self.assertFalse(p.s['profile_accepted'])
    def test_one_v8_click_then_saved_tree_hold(self):
        self.version=m.POLICY_VERSION;p=self.step();self.assertEqual(p.s['phase'],'observe-result');p=self.step();self.assertEqual(p.s['phase'],'profile-required');self.assertFalse(p.s['picker_open_verified']);before=len(self.calls);self.step();self.assertEqual(len(self.calls),before);self.assertEqual(sum(c['op']=='click' for c in self.calls),1)
    def test_unknown_stops_without_any_replay_or_observation(self):
        self.version=m.POLICY_VERSION;self.fail=True
        with self.assertRaises(TimeoutError):self.step()
        before=len(self.calls);p=self.step();self.assertEqual(len(self.calls),before);self.assertIn('unknown-no-replay',p.s['waiting_for'])
    def test_actual_structure_required(self):
        t=self.tree();targets=m.center_targets(t,fixture.IDENTITY);self.assertTrue(all('gap' not in x for x in targets.values()))
        def change(node):
            if node.get('attributes',{}).get('class')=='todoItem-SQ0SNc':node['name']='整改 新增21'
            for child in node.get('children',[]):change(child)
        change(t['root']);self.assertIn('gap',m.center_targets(t,fixture.IDENTITY)['records'])
    def test_wrong_company_before_tree_no_action(self):
        self.group='999'
        with self.assertRaisesRegex(ValueError,'source-company'):self.step()
        self.assertEqual([c['op'] for c in self.calls],['tabs'])
    def test_scope_and_missing_or_ambiguous_picker(self):
        t=self.tree();t['url']='https://life.douyin.com/p/unknown'
        with self.assertRaisesRegex(ValueError,'center-tree'):m.center_targets(t,fixture.IDENTITY)
        t=self.tree();root=t['root']['children'][-1];root['children'][0]['children'].append(dict(root['children'][0]['children'][0]));self.assertIn('gap',m.center_targets(t,fixture.IDENTITY)['picker'])
# Inherited Navigator tests belong to their own suite, not this Probe suite.
for name in list(vars(fixture.NavigationTests)):
    if name.startswith('test_') and name not in vars(DiscoveryTests):setattr(DiscoveryTests,name,None)
if __name__=='__main__':unittest.main()
