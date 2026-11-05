import base64,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import native_window_capture as n
import chrome_process_identity as ci
REAL_CLONE_VERIFY=ci.verify
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg=='
class FakeNative:
 def __init__(self):
  self.permission=True;self.pid=55;self.count=0;self.exe=n.EXE;self.items=[{'kCGWindowNumber':77,'kCGWindowOwnerPID':55,'kCGWindowOwnerName':'Google Chrome','kCGWindowName':'来客','kCGWindowLayer':0,'kCGWindowIsOnscreen':True,'kCGWindowSharingState':1},{'kCGWindowNumber':78,'kCGWindowOwnerPID':55,'kCGWindowOwnerName':'Google Chrome','kCGWindowName':'来客','kCGWindowLayer':0,'kCGWindowIsOnscreen':True,'kCGWindowSharingState':1}]
 def preflight(self):return self.permission
 def process_path(self,pid):return self.exe
 def windows(self):return copy.deepcopy(self.items)
 def set_capture_scope(self,pid,title):self.bound=(pid,title)
 def capture(self,cgwindow,path):
  assert cgwindow==77;assert self.bound==(55,'来客');self.count+=1;Path(path).write_bytes(base64.b64decode(PNG));return {'width':1,'height':1}
class NativeTransportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'image.png';self.native=FakeNative();self.command={'backend':'screen-capture-kit','pid':55,'tabId':7,'windowId':1,'groupid':'123','url':'https://life.douyin.com/p/life_comment/management?groupid=123','captureKey':'test-sck-001'};self.changed=False
 def request(self,c):return {'ok':True,'result':[{'windowId':1,'focused':True,'tabs':[{'tabId':8 if self.changed else 7,'windowId':1,'active':True,'allowed':True,'url':self.command['url'],'title':'来客'}]}]}
 def test_permission_preflight_separate_and_duplicate_titles_allowed(self):
  result=n.preflight(self.command,self.request,self.native);self.assertFalse(result['capture_attempted']);self.assertEqual(self.native.count,0)
  r=n.write_capture(self.command,self.path,self.request,self.native);m=json.loads(self.path.with_suffix('.json').read_text());self.assertTrue(m['whole_window']);self.assertFalse(m['viewport_only']);self.assertEqual(m['before']['window']['kCGWindowNumber'],77);self.assertEqual(n.validate(m,self.command,self.path)['sha256'],r['result']['sha256'])
  n.write_capture(self.command,self.path,self.request,self.native);self.assertEqual(self.native.count,1)
 def test_unavailable_permission_does_not_create_capture_intent(self):
  self.native.permission=False
  with self.assertRaisesRegex(ValueError,'no-permission-requested'):n.write_capture(self.command,self.path,self.request,self.native)
  self.assertFalse(self.path.with_suffix('.json').exists());self.assertEqual(self.native.count,0)
 def test_wrong_frontmost_app_or_pid_refused(self):
  self.native.items[0]['kCGWindowOwnerPID']=99
  with self.assertRaisesRegex(ValueError,'frontmost-pid'):n.preflight(self.command,self.request,self.native)
  self.assertEqual(self.native.count,0)
 def test_changed_active_tab_after_capture_becomes_unknown_no_replay(self):
  original=self.native.capture
  def capture(*a):r=original(*a);self.changed=True;return r
  self.native.capture=capture
  with self.assertRaisesRegex(ValueError,'active-tab-scope'):n.write_capture(self.command,self.path,self.request,self.native)
  with self.assertRaisesRegex(ValueError,'unknown-no-replay'):n.write_capture(self.command,self.path,self.request,self.native)
  self.assertEqual(self.native.count,1)
 def test_changed_cgwindow_after_capture_refused(self):
  original=self.native.capture
  def capture(*a):r=original(*a);self.native.items.reverse();return r
  self.native.capture=capture
  with self.assertRaisesRegex(ValueError,'changed-during'):n.write_capture(self.command,self.path,self.request,self.native)
 def clone_identity(self,path):
  import chrome_process_identity as c
  import test_chrome_process_identity as f
  fixture=f.IdentityTests();fixture.setUp();return REAL_CLONE_VERIFY(path,display_fn=fixture.display,bundle_fn=fixture.bundle,validity_fn=fixture.validity,resolve_fn=lambda p:p)
 def test_signed_clone_actual_path_is_bound_before_after_and_in_history(self):
  import test_chrome_process_identity as f
  self.native.exe=f.CLONE
  with patch('chrome_process_identity.verify',side_effect=self.clone_identity):result=n.write_capture(self.command,self.path,self.request,self.native)
  metadata=json.loads(self.path.with_suffix('.json').read_text());self.assertEqual(metadata['before']['executable'],f.CLONE);self.assertEqual(metadata['after']['executable'],f.CLONE);self.assertFalse(metadata['before']['executable_identity']['bundle_resources_verified']);self.assertEqual(n.validate(metadata,self.command,self.path)['sha256'],result['result']['sha256']);self.assertEqual(self.native.count,1)
 def test_clone_identity_change_after_capture_rejected_without_output(self):
  import test_chrome_process_identity as f
  self.native.exe=f.CLONE;original=self.native.capture
  def capture(*args):r=original(*args);self.native.exe=f.CLONE.replace('.Abc123/','.Different/');return r
  self.native.capture=capture
  with patch('chrome_process_identity.verify',side_effect=self.clone_identity),self.assertRaisesRegex(ValueError,'process-changed'):n.write_capture(self.command,self.path,self.request,self.native)
  self.assertFalse(self.path.exists());self.assertEqual(self.native.count,1)
 def test_wrong_process_and_changed_png_rejected(self):
  self.native.exe='/other/Chrome'
  with self.assertRaisesRegex(ValueError,'main-chrome-path'):n.preflight(self.command,self.request,self.native)
  self.native.exe=n.EXE;n.write_capture(self.command,self.path,self.request,self.native);self.path.write_bytes(b'broken')
  with self.assertRaisesRegex(ValueError,'png-hash'):n.validate(json.loads(self.path.with_suffix('.json').read_text()),self.command,self.path)
if __name__=='__main__':unittest.main()
