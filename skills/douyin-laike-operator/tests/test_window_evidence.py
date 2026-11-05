"""Public CGWindow evidence tests use a fake native adapter; no macOS API calls."""
from datetime import datetime,timezone,timedelta
import copy, importlib.util, json
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('window_evidence',Path(__file__).resolve().parents[1]/'scripts/window-evidence.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
NOW=datetime(2026,10,21,1,0,0,tzinfo=timezone.utc)
def leaf(selector,name):return {'selector':selector,'name':name,'children':[]}
def proof():return {'source':'local-dom-bridge','observed_at':NOW.isoformat(),'tab_id':9,'groupid':'123','date_range':{'start':'2026-10-19','end':'2026-10-20'},'tabs':[{'windowId':3,'focused':True,'tabs':[{'tabId':9,'windowId':3,'active':True,'title':'抖音来客','allowed':True,'url':'https://life.douyin.com/p/governance?groupid=123'}]}],'tree':{'kind':'DOM-derived semantic tree (not native AX)','url':'https://life.douyin.com/p/governance','truncated':False,'root':{'selector':'body','children':[leaf('#date','2026/10/19 ~ 2026/10/20'),leaf('#header','处置主体')]}},'bindings':{'date':{'selector':'#date','text':'2026/10/19 ~ 2026/10/20'},'headers':[{'selector':'#header','text':'处置主体'}]}}
def window():return {'kCGWindowNumber':7,'kCGWindowOwnerPID':55,'kCGWindowOwnerName':'Google Chrome','kCGWindowName':'抖音来客','kCGWindowLayer':0,'kCGWindowIsOnscreen':True,'kCGWindowSharingState':1}
class MockNative:
    def __init__(self):self.items=[window()];self.allowed=True;self.path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';self.captures=0;self.callback=None
    def preflight(self):return self.allowed
    def process_path(self,pid):return self.path
    def windows(self):return copy.deepcopy(self.items)
    def capture(self,window_id,path):
        self.captures+=1;Path(path).write_bytes(b'\x89PNG\r\n\x1a\nMOCK_ONLY')
        if self.callback:self.callback()
        return {'width':100,'height':50}
class WindowEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.dom=self.root/'dom.json';self.native=MockNative();self.p=proof();self.write()
    def write(self):self.dom.write_text(json.dumps(self.p,ensure_ascii=False))
    def capture(self):return w.capture_evidence(55,7,self.dom,self.root/'screen.png',self.native,NOW)
    def test_capture_binds_hash_without_claiming_content_coverage(self):
        result=self.capture();metadata=json.loads(Path(result['metadata']).read_text())
        self.assertEqual(metadata['source'],'macos-public-cgwindow');self.assertEqual(metadata['dom_evidence']['sha256'],w.sha(self.dom))
        self.assertFalse(metadata['coverage_verified']);self.assertFalse(metadata['live_accepted']);self.assertFalse(metadata['pixel_actions_used']);self.assertTrue(metadata['content_review_required'])
        self.assertEqual(self.native.captures,1)
    def test_permission_unavailable_does_not_request_or_capture(self):
        self.native.allowed=False
        with self.assertRaisesRegex(ValueError,'access-unavailable'):self.capture()
        self.assertEqual(self.native.captures,0)
    def test_pid_must_be_real_chrome_main_executable(self):
        self.native.path='/Applications/Other.app/Contents/MacOS/Google Chrome'
        with self.assertRaisesRegex(ValueError,'not-chrome-main'):self.capture()
    def test_window_metadata_mismatch_stops_before_capture(self):
        for key,value in [('kCGWindowOwnerPID',99),('kCGWindowName','别的标签'),('kCGWindowLayer',1),('kCGWindowSharingState',0),('kCGWindowIsOnscreen',False)]:
            self.native.items=[{**window(),key:value}]
            with self.subTest(key=key),self.assertRaises(ValueError):self.capture()
        self.assertEqual(self.native.captures,0)
    def test_ambiguous_matching_chrome_windows_refused(self):
        self.native.items.append({**window(),'kCGWindowNumber':8})
        with self.assertRaisesRegex(ValueError,'title-ambiguous'):self.capture()
    def test_window_must_be_foreground_not_another_application(self):
        self.native.items.insert(0,{**window(),'kCGWindowNumber':8,'kCGWindowOwnerPID':99})
        with self.assertRaisesRegex(ValueError,'not-frontmost'):self.capture()
    def test_stale_dom_or_future_evidence_refused(self):
        for seconds in (-61,1):
            self.p['observed_at']=(NOW+timedelta(seconds=seconds)).isoformat();self.write()
            with self.subTest(seconds=seconds),self.assertRaisesRegex(ValueError,'stale-or-future'):self.capture()
    def test_inactive_or_mismatched_tab_refused(self):
        for field,value in [('active',False),('tabId',8),('windowId',99),('allowed',False),('url','https://life.douyin.com/?groupid=999')]:
            self.p=proof();self.p['tabs'][0]['tabs'][0][field]=value;self.write()
            with self.subTest(field=field),self.assertRaises(ValueError):self.capture()
    def test_dom_group_date_and_header_are_actual_leaf_evidence(self):
        for change in ('date','header','truncated','aggregate'):
            self.p=proof()
            if change=='date':self.p['date_range']['start']='2026-10-18'
            if change=='header':self.p['bindings']['headers'][0]['text']='伪造表头'
            if change=='truncated':self.p['tree']['truncated']=True
            if change=='aggregate':self.p['tree']['root']['children'][1]['children']=[leaf('#nested','隐藏信息')]
            self.write()
            with self.subTest(change=change),self.assertRaises(ValueError):self.capture()
        self.assertEqual(self.native.captures,0)
    def test_window_change_during_capture_leaves_no_published_evidence(self):
        self.native.callback=lambda:self.native.items[0].update(kCGWindowName='其他标签')
        with self.assertRaises(ValueError):self.capture()
        self.assertFalse((self.root/'screen.png').exists());self.assertFalse((self.root/'screen.json').exists())
    def test_dom_file_changed_during_capture_refused(self):
        self.native.callback=lambda:self.dom.write_text('{}')
        with self.assertRaisesRegex(ValueError,'evidence-changed'):self.capture()
        self.assertFalse((self.root/'screen.png').exists())
    def test_existing_evidence_never_overwritten(self):
        self.capture()
        with self.assertRaisesRegex(ValueError,'new-png-output'):self.capture()
        self.assertEqual(self.native.captures,1)

class ScreenCaptureKitAdapterTests(unittest.TestCase):
    def native(self,allowed=True):
        native=w.PublicCGWindow.__new__(w.PublicCGWindow);native.preflight=lambda:allowed
        native.capture_scope=(55,'抖音来客');return native
    def reply(self,**change):
        return {**{'ok':True,'backend':'ScreenCaptureKit/SCScreenshotManager','pid':55,'window_id':7,'title':'抖音来客',
            'whole_window':True,'width':800,'height':600,'window_activation_used':False,'permission_request_used':False,'pixel_actions_used':False},**change}
    def test_denied_permission_never_compiles_or_invokes_capture(self):
        with patch.object(w,'build_helper') as build,patch.object(w.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'access-unavailable'):self.native(False).capture(7,'/tmp/no-capture.png')
        build.assert_not_called();run.assert_not_called()
    def test_helper_has_explicit_window_pid_title_and_safe_scoped_result(self):
        with patch.object(w,'build_helper',return_value=Path('/tmp/helper')),patch.object(w.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(self.reply()),stderr='')) as run:
            result=self.native().capture(7,'/tmp/test.png')
        self.assertEqual(result,{'width':800,'height':600});args=run.call_args.args[0]
        self.assertEqual(args,['/tmp/helper','--pid','55','--window-id','7','--title','抖音来客','--out',str(Path('/tmp/test.png').resolve())])
    def test_helper_wrong_scope_or_safety_refused(self):
        for change in ({'pid':66},{'window_id':8},{'whole_window':False},{'permission_request_used':True}):
            with self.subTest(change=change),patch.object(w,'build_helper',return_value=Path('/tmp/helper')),patch.object(w.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(self.reply(**change)),stderr='')):
                with self.assertRaises(ValueError):self.native().capture(7,'/tmp/test.png')
    def test_compilation_only_is_cached_and_never_invokes_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            calls=[]
            def compiler(args,**kwargs):
                calls.append(args);Path(args[args.index('-o')+1]).write_bytes(b'MOCK_BINARY');return SimpleNamespace(returncode=0,stderr='')
            first=w.build_helper(directory,compiler);second=w.build_helper(directory,compiler)
            self.assertEqual(first,second);self.assertEqual(len(calls),1)
            self.assertEqual(calls[0][:2],['/usr/bin/xcrun','swiftc']);self.assertIn('-parse-as-library',calls[0])
    def test_swift_source_has_no_permission_request_or_legacy_capture_call(self):
        text=(Path(__file__).resolve().parents[1]/'scripts/window-capture.swift').read_text()
        self.assertNotIn('CGRequestScreenCaptureAccess(',text);self.assertNotIn('CGWindowListCreateImage(',text)
        self.assertIn('CGPreflightScreenCaptureAccess()',text);self.assertIn('SCContentFilter(desktopIndependentWindow:',text)
    def test_cli_initializes_appkit_without_activating_a_window(self):
        text=(Path(__file__).resolve().parents[1]/'scripts/window-capture.swift').read_text()
        self.assertIn('@MainActor',text)
        self.assertIn('application.setActivationPolicy(.prohibited)',text)
        self.assertLess(text.index('NSApplication.shared'),text.index('try need(CGPreflightScreenCaptureAccess()'))
        self.assertNotIn('.activate(',text)
if __name__=='__main__':unittest.main()
