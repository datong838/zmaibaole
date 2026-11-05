import copy, importlib.util, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('policy_rejection_workflow',SCRIPTS/'bridge-workflow.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class RejectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        button={'name':'切换','role':'button','selector':'#merchant-switch','attributes':{'class':'SwitchCard-index-module__switch-card-button--known'}}
        switch={'name':'商户 服务商123456789 切换','attributes':{'class':'SwitchCard-index-module__switch-card--known'},'children':[button]}
        self.tree={'truncated':False,'root':{'name':'服务商123456789 账户ID987654321 我的客户经理陈方圆 退出登录','attributes':{'class':'UserCard-index-module__outer--known'},'children':[switch]}}
        path=self.root/'observed.json';m.write_json(path,self.tree)
        self.w=m.Workflow.__new__(m.Workflow);self.w.file=self.root/'workflow.json'
        self.w.s={'state':'running','phase':'context','revision':1,'tab_id':1,'initial_groupid':'123','calls':[{'key':'1:context','state':'unknown','phase':'context','command':{'op':'click','tabId':1,'kind':'navigation','locator':{'by':'selector','value':'#merchant-switch'}}}], 'checkpoints':[], 'last_tree':{'path':str(path),'sha256':m.digest(path)},'last_error':{'message':'bridge-command-failed: not in offline reviewed click allowlist'}}
        self.commands=[]
        def invoke(c):
            self.commands.append(c)
            if c['op']=='ping':return {'ok':True,'result':{'version':'dom-only-20261021-7'}}
            if c['op']=='tabs':return {'ok':True,'result':[{'tabs':[{'tabId':1,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]}
            if c['op']=='tree':return {'ok':True,'result':copy.deepcopy(self.tree)}
            raise AssertionError('No mutations allowed')
        self.w.invoke=invoke;self.w.save()
        self.version=patch.object(m,'VERSION','dom-only-20261021-7');self.version.start();self.addCleanup(self.version.stop)
    def test_explicit_pre_action_denial_is_archived_without_click(self):
        original=self.w.file.read_bytes();self.w.reconcile_rejected_company_switch()
        c=self.w.s['calls'][0];self.assertEqual(c['state'],'rejected');self.assertEqual(self.w.s['revision'],2)
        self.assertEqual(Path(c['rejection']['archive']).read_bytes(),original)
        self.assertEqual([c['op'] for c in self.commands],['ping','tabs','tree'])
        with self.assertRaisesRegex(ValueError,'explicit-pre-action'):self.w.reconcile_rejected_company_switch()
    def test_transport_or_other_errors_are_never_reconciled(self):
        for message in ('bridge-command-failed: timeout','ui-outcome-unknown-do-not-replay','bridge-command-failed: action kind does not match reviewed policy'):
            self.w.s['last_error']['message']=message
            with self.assertRaisesRegex(ValueError,'explicit-pre-action'):self.w.reconcile_rejected_company_switch()
        self.assertEqual(self.commands,[])
    def test_changed_source_or_other_unknown_blocks_recovery(self):
        self.w.s['calls'].append({'key':'other','state':'unknown','command':{'op':'activate'}})
        with self.assertRaisesRegex(ValueError,'other-unknown'):self.w.reconcile_rejected_company_switch()
        self.w.s['calls'].pop();self.w.s['last_tree']['sha256']='changed'
        with self.assertRaisesRegex(ValueError,'original-rejected'):self.w.reconcile_rejected_company_switch()
    def test_upgrade_and_current_identity_are_required(self):
        with patch.object(m,'VERSION','dom-only-20261021-6'):
            with self.assertRaisesRegex(ValueError,'policy-upgrade'):self.w.reconcile_rejected_company_switch()
        self.tree['root']['name']=self.tree['root']['name'].replace('987654321','987654322')
        with self.assertRaisesRegex(ValueError,'page-changed'):self.w.reconcile_rejected_company_switch()
        self.assertEqual(self.w.s['calls'][0]['state'],'unknown')
if __name__=='__main__':unittest.main()
