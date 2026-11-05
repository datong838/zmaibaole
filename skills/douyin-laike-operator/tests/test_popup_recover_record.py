"""Pure fake bridge/AX recovery chain; no Chrome or OS APIs."""
import copy,importlib.util,json,sys,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_chrome_popup_navigation import snapshot,popup_snapshot
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
spec=importlib.util.spec_from_file_location('popup_recover_record_tests',SCRIPTS/'popup-recover-record.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
NOW=datetime(2026,10,21,2,0,0,tzinfo=timezone.utc)
class Native:
    def __init__(self,world):self.world=world;self.pid=55
    def tree(self):return popup_snapshot() if self.world['bubble'] else snapshot()
    def press(self,path,window_path):
        self.world['presses']+=1
        if self.world.get('fail_press'):raise RuntimeError('injected unknown press')
        if not self.world['bubble']:self.world['bubble']=True
        else:self.world['record']=True
    def close(self):pass
class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job={'action':'acquire','work_order_id':'fixture','company':'fixture','groupid':'123','date_range':{'start':'2026-10-17','end':'2026-10-19'},'source_dir':str(self.root/'sources'),'workflow_path':str(self.root/'formal.json')}
        self.s={'backend':'local-dom-bridge','state':'running','phase':'recordTabAfterOpen','work_order_id':'fixture','fingerprint':r.workflow.fingerprint(self.job),'tab_id':9,'company':'fixture','groupid':'123','date_range':self.job['date_range'],'identity':{'provider':'p','account_id':'a','manager':'m'},'calls':[],'checkpoints':[]}
        self.save();self.world={'bubble':False,'presses':0,'record':False};self.commands=[];self.factories=0
    def save(self):Path(self.job['workflow_path']).write_text(json.dumps(self.s))
    def tabs(self):
        tabs=[{'tabId':9,'windowId':3,'active':True,'allowed':True,'title':'抖音来客','url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]
        if self.world['record']:tabs.append({'tabId':77,'windowId':3,'allowed':True,'url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123'})
        return [{'windowId':3,'focused':True,'tabs':tabs}]
    def invoke(self,c):
        self.commands.append(c)
        if c['op']=='activate':return {'ok':True,'result':{'tabId':9,'windowId':3,'url':self.tabs()[0]['tabs'][0]['url'],'title':'抖音来客','active':True,'windowFocused':True,'observedAt':NOW.isoformat(),'safety_version':'dom-only-20261021-11'}}
        self.assertEqual(c['op'],'tabs');return {'ok':True,'result':self.tabs()}
    def factory(self,expected_pid):self.assertEqual(expected_pid,55);self.factories+=1;return Native(self.world)
    def recover(self,**kw):return r.recover(self.job,9,55,self.root/'recovery',self.invoke,self.factory,at=NOW,**kw)
    def test_closed_observed_then_list_and_link_in_one_process_no_second_activate(self):
        result=self.recover();self.assertEqual(result['state'],'complete');self.assertEqual(result['record_tab']['tabId'],77)
        self.assertEqual(self.world['presses'],2);self.assertEqual([c['op'] for c in self.commands],['activate','tabs','tabs'])
        folder=self.root/'recovery';self.assertEqual(json.loads((folder/'confirmed-closed.json').read_text())['bubble_count'],0)
        self.assertEqual(json.loads((folder/'list-intent.json').read_text())['state'],'complete');self.assertEqual(json.loads((folder/'link-intent.json').read_text())['state'],'complete')
    def test_repeat_only_reads_tabs_never_constructs_ax_or_activates(self):
        self.recover();self.commands=[];factories=self.factories
        result=self.recover();self.assertEqual(result['state'],'complete');self.assertEqual(self.commands,[{'op':'tabs'}]);self.assertEqual(self.factories,factories);self.assertEqual(self.world['presses'],2)
    def test_unknown_list_press_is_not_treated_as_closed_on_repeat(self):
        self.world['fail_press']=True
        with self.assertRaises(RuntimeError):self.recover()
        presses=self.world['presses'];self.commands=[];self.world['fail_press']=False
        result=self.recover();self.assertEqual(result['state'],'unknown');self.assertEqual(self.world['presses'],presses);self.assertEqual(self.commands,[{'op':'tabs'}])
    def test_wrong_formal_phase_or_export_intent_stops_before_bridge(self):
        for changes in ({'phase':'submit'},{'exportPending':True},{'attempts':1},{'calls':[{'state':'unknown'}]}):
            original=copy.deepcopy(self.s);self.s.update(changes);self.save()
            with self.subTest(changes=changes),self.assertRaises(RuntimeError):self.recover()
            self.s=original
        self.assertFalse(self.commands)
    def test_group_date_identity_scope_proof_required(self):
        for changes in ({'groupid':'999'},{'date_range':{'start':'2026-10-18','end':'2026-10-19'}},{'identity':None}):
            original=copy.deepcopy(self.s);self.s.update(changes);self.save()
            with self.subTest(changes=changes),self.assertRaises(RuntimeError):self.recover()
            self.s=original
        self.assertFalse(self.commands)
    def test_already_open_bubble_without_prior_complete_chain_refuses(self):
        self.world['bubble']=True
        with self.assertRaisesRegex(RuntimeError,'complete-list-chain'):self.recover()
        self.assertEqual(self.world['presses'],0)
    def test_multiple_popup_windows_are_refused_without_press(self):
        self.world['bubble']=True
        def factory(expected_pid):
            native=Native(self.world)
            def tree():
                result=popup_snapshot();result['tree']['children'].append(copy.deepcopy(result['tree']['children'][1]));return result
            native.tree=tree;return native
        self.factory=factory
        with self.assertRaisesRegex(RuntimeError,'count-ambiguous'):self.recover()
        self.assertEqual(self.world['presses'],0)
    def test_existing_bubble_reuses_only_matching_complete_list_chain(self):
        self.world['bubble']=True;old=self.root/'old-list.json'
        old.write_text(json.dumps({'mode':'open-list','state':'complete','expected_pid':55,'bridge_focus':{'tabId':9,'windowId':3,'groupid':'123','url':self.tabs()[0]['tabs'][0]['url']},'after':popup_snapshot()}))
        result=self.recover(list_intent=old);self.assertEqual(result['state'],'complete');self.assertEqual(self.world['presses'],1)
        self.assertFalse((self.root/'recovery'/'confirmed-closed.json').exists())
    def test_orphan_link_intent_does_not_trigger_any_ui(self):
        folder=self.root/'recovery';folder.mkdir();(folder/'link-intent.json').write_text('{"state":"unknown"}')
        with self.assertRaisesRegex(RuntimeError,'orphan'):self.recover()
        self.assertFalse(self.commands);self.assertEqual(self.world['presses'],0)
if __name__=='__main__':unittest.main()
