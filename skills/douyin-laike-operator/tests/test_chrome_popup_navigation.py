"""Only fake AX shell and stored focus proof; no accessibility or browser calls."""
from datetime import datetime,timezone,timedelta
import copy,importlib.util,json
from pathlib import Path
import tempfile,unittest
spec=importlib.util.spec_from_file_location('chrome_popup_navigation_tests',Path(__file__).resolve().parents[1]/'scripts/chrome-popup-navigation.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
NOW=datetime(2026,10,21,2,0,0,tzinfo=timezone.utc)
def focus():return {'source':'local-dom-bridge','expected_pid':55,'observed_at':NOW.isoformat(),'groupid':'123','tabId':9,'windowId':3,'activation':{'tabId':9,'windowId':3,'active':True,'windowFocused':True,'observedAt':NOW.isoformat(),'safety_version':'dom-only-20261021-11','url':'https://life.douyin.com/p/life_comment/management?groupid=123'},'tabs':[{'windowId':3,'focused':True,'tabs':[{'tabId':9,'windowId':3,'active':True,'allowed':True,'title':'抖音来客','url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]}
def snapshot():return {'ok':True,'bundle_id':'com.google.Chrome','pid':55,'truncated':False,'all_web_areas_omitted':True,'tree':{'role':'AXApplication','path':[],'children':[{'role':'AXWindow','AXSubrole':'AXStandardWindow','AXMain':True,'AXTitle':'抖音来客','path':[0],'children':[{'role':'AXButton','AXDescription':p.LABEL,'AXEnabled':True,'actions':['AXPress'],'path':[0,0],'children':[]},{'role':'AXWebArea','web_content_omitted':True,'path':[0,1],'children':[]}]}]}}
class MockNative:
    def __init__(self):self.pid=55;self.s=snapshot();self.presses=0;self.tree_reads=0;self.closed=0;self.fail=False;self.after_fail=False;self.out=None
    def tree(self):
        self.tree_reads+=1
        if self.after_fail and self.tree_reads>1:raise RuntimeError('after tree unavailable')
        return copy.deepcopy(self.s)
    def press(self,path,window_path):
        if self.out is not None:
            saved=json.loads(self.out.read_text());assert saved['state']=='unknown';assert saved['target']['path']==path
        self.presses+=1
        if self.fail:raise RuntimeError('unknown AX result')
    def close(self):self.closed+=1
class PopupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.out=self.root/'intent.json';self.proof=self.root/'focus.json';self.f=focus();self.write();self.native=MockNative();self.native.out=self.out;self.constructed=0
    def write(self):self.proof.write_text(json.dumps(self.f))
    def factory(self,expected_pid):self.assertEqual(expected_pid,55);self.constructed+=1;return self.native
    def run_once(self):return p.run_open_list(self.out,55,self.proof,self.factory,NOW)
    def test_write_ahead_press_once_then_repeat_does_not_touch_ax(self):
        result=self.run_once();self.assertEqual(result['state'],'complete');self.assertEqual(self.native.presses,1)
        result=self.run_once();self.assertTrue(result['already_recorded']);self.assertFalse(result['replayed']);self.assertEqual(self.native.presses,1);self.assertEqual(self.constructed,1)
    def test_unknown_press_after_restart_never_replayed(self):
        self.native.fail=True
        with self.assertRaisesRegex(RuntimeError,'unknown AX'):self.run_once()
        self.assertEqual(json.loads(self.out.read_text())['state'],'unknown')
        self.assertEqual(self.run_once()['state'],'unknown');self.assertEqual(self.native.presses,1);self.assertEqual(self.constructed,1)
    def test_after_snapshot_failure_does_not_repress(self):
        self.native.after_fail=True
        with self.assertRaises(RuntimeError):self.run_once()
        self.assertTrue(self.run_once()['press_returned_success']);self.assertEqual(self.native.presses,1)
    def test_changed_focus_proof_cannot_reuse_output_intent(self):
        self.run_once();self.f['groupid']='999';self.write()
        with self.assertRaisesRegex(RuntimeError,'intent-conflict'):self.run_once()
        self.assertEqual(self.native.presses,1)
    def test_main_window_pid_title_and_enabled_button_required(self):
        for field,value in [('AXMain',False),('AXTitle','别的标签')]:
            self.native.s=snapshot();self.native.s['tree']['children'][0][field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):self.run_once()
        self.native.s=snapshot();self.native.s['tree']['children'][0]['children'][0]['AXEnabled']=False
        with self.assertRaisesRegex(RuntimeError,'not-unique'):self.run_once()
        self.assertEqual(self.native.presses,0)
    def test_duplicate_buttons_or_main_windows_refuse(self):
        win=self.native.s['tree']['children'][0];win['children'].insert(0,copy.deepcopy(win['children'][0]))
        with self.assertRaisesRegex(RuntimeError,'button-not-unique'):self.run_once()
        self.native.s=snapshot();self.native.s['tree']['children'].append(copy.deepcopy(self.native.s['tree']['children'][0]))
        with self.assertRaisesRegex(RuntimeError,'window-not-unique'):self.run_once()
    def test_webarea_descendants_never_used_as_popup_target(self):
        win=self.native.s['tree']['children'][0];button=win['children'].pop(0);win['children'][0]['children']=[button]
        with self.assertRaisesRegex(RuntimeError,'button-not-unique'):self.run_once()
        self.assertEqual(self.native.presses,0)
    def test_settings_buttons_never_qualify(self):
        for text in ('始终允许来自此网站的弹出式窗口','设置','弹出式窗口已拦截'):
            self.native.s['tree']['children'][0]['children'][0]['AXDescription']=text
            with self.subTest(text=text),self.assertRaisesRegex(RuntimeError,'button-not-unique'):self.run_once()
        self.assertEqual(self.native.presses,0)
    def test_focus_proof_group_and_activation_must_match(self):
        for change in ('group','active','focused','tab','window','pid'):
            self.f=focus()
            if change=='group':self.f['groupid']='999'
            if change=='active':self.f['activation']['active']=False
            if change=='focused':self.f['tabs'][0]['focused']=False
            if change=='tab':self.f['tabId']=8
            if change=='window':self.f['windowId']=8
            if change=='pid':self.f['expected_pid']=99
            self.write()
            with self.subTest(change=change),self.assertRaises(RuntimeError):self.run_once()
        self.assertEqual(self.constructed,0)
    def test_actual_traversal_omits_every_webarea_without_reading_attributes(self):
        from types import SimpleNamespace
        inspector=p.PopupShellInspector.__new__(p.PopupShellInspector);inspector.root='app';inspector.pid=55;inspector.refs=[]
        reads=[]
        def get(element,key):
            reads.append((element,key))
            if element=='web':
                self.assertEqual(key,'AXRole');return 'AXWebArea'
            return 'AXApplication' if key=='AXRole' else None
        def array(element,key):
            self.assertNotEqual(element,'web');return ['web'] if element=='app' else []
        inspector.get=get;inspector.array=array
        inspector.ax=SimpleNamespace(AXUIElementCopyActionNames=lambda *args:1)
        result=inspector.tree()
        self.assertTrue(result['all_web_areas_omitted']);self.assertEqual(reads.count(('web','AXRole')),1)
        self.assertEqual(result['tree']['children'][0]['children'],[])
    def test_same_title_nonmain_windows_do_not_block_unique_main(self):
        for i in range(8):
            window=copy.deepcopy(self.native.s['tree']['children'][0]);window.update(AXMain=False,path=[i+1]);self.native.s['tree']['children'].append(window)
        self.assertEqual(self.run_once()['state'],'complete');self.assertEqual(self.native.presses,1)
    def test_javascript_z_timestamps_are_accepted(self):
        self.f['observed_at']='2026-10-21T02:00:00.000Z';self.f['activation']['observedAt']='2026-10-21T02:00:00.000Z';self.write()
        self.assertEqual(self.run_once()['state'],'complete')
    def test_public_link_url_never_retains_auth_queries(self):
        self.assertEqual(p.public_navigation_url('https://life.douyin.com/p/export_records/comments?groupid=123'),'https://life.douyin.com/p/export_records/comments?groupid=123')
        for url in ('https://life.douyin.com/?token=secret&groupid=123','https://life.douyin.com/?%74oken=secret','https://example.com/?groupid=123','chrome://settings/','https://life.douyin.com/?groupid=123&groupid=456'):
            self.assertIsNone(p.public_navigation_url(url))
    def test_private_queries_in_link_labels_or_static_values_are_omitted(self):
        value=p.public_shell_text('打开 https://life.douyin.com/p/?token=private-secret')
        self.assertNotIn('private-secret',value);self.assertIn('omitted',value)
    def test_only_public_link_url_and_noneditable_static_value_are_read(self):
        from types import SimpleNamespace
        inspector=p.PopupShellInspector.__new__(p.PopupShellInspector);inspector.root='app';inspector.pid=55;inspector.refs=[];reads=[]
        roles={'app':'AXApplication','link':'AXLink','text':'AXStaticText','input':'AXTextField','web':'AXWebArea'}
        def get(element,key):
            reads.append((element,key))
            if key=='AXRole':return roles[element]
            if key=='AXURL':self.assertEqual(element,'link');return 'https://life.douyin.com/p/export_records/comments?groupid=123'
            if key=='AXValue':self.assertEqual(element,'text');return '公开记录页'
            return None
        inspector.get=get;inspector.array=lambda element,key:['link','text','input','web'] if element=='app' else []
        inspector.string=lambda key:key;inspector.cf=SimpleNamespace(CFRelease=lambda key:None)
        inspector.ax=SimpleNamespace(AXUIElementCopyActionNames=lambda *args:1,AXUIElementIsAttributeSettable=lambda *args:0)
        result=inspector.tree();children=result['tree']['children'];self.assertEqual(children[0]['AXURL'],'https://life.douyin.com/p/export_records/comments?groupid=123');self.assertEqual(children[1]['AXValue'],'公开记录页')
        self.assertNotIn(('input','AXValue'),reads);self.assertEqual([key for e,key in reads if e=='web'],['AXRole'])
    def test_stale_focus_does_not_construct_native(self):
        self.f['observed_at']=(NOW-timedelta(seconds=61)).isoformat();self.write()
        with self.assertRaisesRegex(RuntimeError,'stale-or-future'):self.run_once()
        self.assertEqual(self.constructed,0)

def popup_snapshot():
    s=snapshot();s['tree']['children'].append({'role':'AXWindow','AXSubrole':'AXUnknown','AXTitle':p.POPUP_TITLE,'AXMain':False,'path':[1],'children':[{'role':'AXLink','AXTitle':p.RECORD_LABEL,'AXDescription':p.RECORD_LABEL,'AXEnabled':True,'actions':['AXPress','AXShowMenu'],'path':[1,0],'children':[]},{'role':'AXRadioButton','AXTitle':'始终允许','AXEnabled':True,'path':[1,1],'children':[]}]})
    return s
class RecordLinkTests(unittest.TestCase):
    setUp=PopupTests.setUp
    write=PopupTests.write
    factory=PopupTests.factory
    def prepare(self):
        self.native.s=popup_snapshot();self.list=self.root/'list.json'
        proof=p.focused_bridge_proof(self.proof,55,NOW)
        self.list.write_text(json.dumps({'mode':'open-list','state':'complete','expected_pid':55,'bridge_focus':proof,'after':popup_snapshot()}));self.list_sha=p.sha(self.list);self.reads=0
    def tabs(self):
        self.reads+=1
        return [{'windowId':3,'tabs':[{'tabId':77,'windowId':3,'allowed':True,'url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123'}]}]
    def run_link(self):return p.run_record_link(self.out,55,self.proof,self.list,self.list_sha,self.factory,self.tabs,NOW)
    def test_exact_observed_native_link_pressed_once_without_url_guess(self):
        self.prepare();result=self.run_link();self.assertEqual(result['state'],'complete');self.assertEqual(result['record_tab']['tabId'],77);self.assertEqual(self.native.presses,1);self.assertEqual(self.reads,1)
        result=self.run_link();self.assertTrue(result['already_recorded']);self.assertEqual(self.native.presses,1);self.assertEqual(self.reads,1)
    def test_missing_popup_after_activate_stops_without_reopening_list(self):
        self.prepare();self.native.s=snapshot()
        with self.assertRaisesRegex(RuntimeError,'popup-window'):self.run_link()
        self.assertEqual(self.native.presses,0);self.assertFalse(self.out.exists())
    def test_observed_link_label_cannot_change(self):
        self.prepare();self.native.s['tree']['children'][1]['children'][0]['AXTitle']='另一个链接'
        with self.assertRaisesRegex(RuntimeError,'record-link-changed'):self.run_link()
        self.assertEqual(self.native.presses,0)
    def test_original_complete_list_hash_is_mandatory(self):
        self.prepare();self.list.write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'hash-mismatch'):self.run_link()
        self.assertEqual(self.native.presses,0)
    def test_full_url_when_present_must_be_public_record_group(self):
        self.prepare();self.native.s['tree']['children'][1]['children'][0]['AXURL']='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=999'
        with self.assertRaisesRegex(RuntimeError,'public-url-mismatch'):self.run_link()
        self.assertEqual(self.native.presses,0)
    def test_unknown_click_never_replayed(self):
        self.prepare();self.native.fail=True
        with self.assertRaises(RuntimeError):self.run_link()
        self.assertEqual(self.run_link()['state'],'unknown');self.assertEqual(self.native.presses,1);self.assertEqual(self.reads,0)
    def test_observed_business_routing_values_only(self):
        base='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123'
        good=base+'&life_biz_view_id=22&life_account_biz_ids='
        self.assertTrue(p.record_url(good,'123'))
        self.assertEqual(p.public_navigation_url(good),good)
        for suffix in ('&token=x','&life_biz_view_id=23','&life_biz_view_id=22&life_biz_view_id=22','&life_account_biz_ids=123','&groupid=123'):
            with self.subTest(suffix=suffix):
                self.assertFalse(p.record_url(base+suffix,'123'))
                self.assertIsNone(p.public_navigation_url(base+suffix))
    def test_post_tab_requires_new_actual_export_url_and_group(self):
        for url in ('https://example.com/p/fulfillsettle/export_records/20101?groupid=123','https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=999','https://life.douyin.com/p/fulfillsettle/something/20101?groupid=123'):
            self.prepare();self.out.unlink(missing_ok=True)
            self.tabs=lambda:[{'tabs':[{'tabId':77,'allowed':True,'url':url}]}]
            with self.subTest(url=url),self.assertRaisesRegex(RuntimeError,'new-record-tab'):self.run_link()
            self.assertEqual(json.loads(self.out.read_text())['state'],'unknown')
    def test_duplicate_popup_or_link_refuses(self):
        self.prepare();popup=self.native.s['tree']['children'][1];popup['children'].append(copy.deepcopy(popup['children'][0]))
        with self.assertRaisesRegex(RuntimeError,'link-not-unique'):self.run_link()
        self.assertEqual(self.native.presses,0)
if __name__=='__main__':unittest.main()
