import base64,copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
import messenger as m, image_paste_repair as repair,ui
from native import Native,AXError
from test_sender import MockNative,fixture
PNG='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAX+XDSwAAAABJRU5ErkJggg=='
class ImageRepairTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);source=self.root/'source.png';source.write_bytes(base64.b64decode(PNG))
  self.path,self.s=m.prepare('same-image-key','group','测试群请忽略',file=source,directory=self.root/'jobs');self.native=MockNative();self.snap=self.native.tree();pid=self.snap['pid'];self.s.update(pid=pid,phase='file-confirm',status='unknown',error='file-confirm-button-ambiguous:0',send_intent_at=m.now(),paste_empty_composer_verified=True)
  m.event(self.s,'send-intent',file=self.s['job']['file_name'],sha256=self.s['job']['file_sha256']);m.event(self.s,'file-pasted',clipboard_restored=True,clipboard_changed_by_other_app=False);m.atomic(self.path,self.s)
  self.failed=self.root/'failed.json';m.atomic(self.failed,self.snap);image=self.root/'window.png';image.write_bytes(base64.b64decode(PNG));meta=self.root/'window.json';m.atomic(meta,{'pid':pid,'window_id':8,'window':{'kCGWindowOwnerPID':pid,'kCGWindowName':'企业微信','kCGWindowNumber':8},'executable':'/Applications/企业微信.app/Contents/MacOS/企业微信','whole_window':True,'pixel_actions_used':False,'permission_request_used':False,'capture_method':'macos-public-screencapture-window-id','png':{'path':str(image),'sha256':repair.sha(image),'width':1,'height':1}})
  self.report=self.root/'report.json';self.r={'kind':'wecom-image-paste-repair-v1','root_authorization':'retry-same-job-image-paste-once','job':{'path':str(self.path),'sha256':repair.sha(self.path)},'failed_snapshot':{'path':str(self.failed),'sha256':repair.sha(self.failed)},'visual_empty':{'image':{'path':str(image),'sha256':repair.sha(image)},'capture_metadata':{'path':str(meta),'sha256':repair.sha(meta)},'reviewed_by':'root-supervisor','composer_empty':True,'no_attachment_or_preview':True,'target':'测试群请忽略','pid':pid}};m.atomic(self.report,self.r)
 def run_repair(self):return repair.repair(self.path,{'path':str(self.report),'sha256':repair.sha(self.report)},native_factory=lambda:self.native)
 def test_same_job_repair_only_prepares_stage_and_archives_original(self):
  raw=self.path.read_bytes();s=self.run_repair();self.assertEqual(s['phase'],'stage');self.assertEqual(s['status'],'running');self.assertFalse(s['sent']);self.assertFalse(self.native.keys);self.assertEqual(s['job']['key'],'same-image-key')
  root=self.path.parent/'image-paste-repairs'/self.path.stem;self.assertEqual((root/'original-job.json').read_bytes(),raw)
  with self.assertRaises(ui.UIError):self.run_repair()
 def test_any_return_intent_or_confirmation_rejects(self):
  for marker in ('image_return_intent_at','original_file_choice_intent_at','owned_image_paste','image_proof','sent'):
   s=copy.deepcopy(self.s);s[marker]=True;m.atomic(self.path,s)
   with self.subTest(marker=marker),self.assertRaisesRegex(ui.UIError,'intent-present'):self.run_repair()
  self.assertFalse(self.native.keys)
 def test_changed_transcript_pid_or_nonempty_draft_rejects(self):
  for snap in (fixture(messages=['new message']),fixture(draft='existing draft')):
   self.native.tree=lambda:copy.deepcopy(snap)
   with self.assertRaises(ui.UIError):self.run_repair()
  snap=copy.deepcopy(self.snap);snap['pid']+=1;self.native.tree=lambda:snap
  with self.assertRaisesRegex(ui.UIError,'pid-changed'):self.run_repair()
 def test_visual_bool_without_real_image_not_accepted(self):
  self.r['visual_empty']['image']['sha256']='0'*64;m.atomic(self.report,self.r)
  with self.assertRaisesRegex(ui.UIError,'evidence-changed'):self.run_repair()
 def test_report_pinned_original_job_cannot_change_key(self):
  s=copy.deepcopy(self.s);s['error']='different';m.atomic(self.path,s)
  with self.assertRaises(ui.UIError):self.run_repair()
class StablePasteTests(unittest.TestCase):
 def test_empty_real_ax_shape_waits_without_file_modal_or_return_and_seed_precedes_paste(self):
  from contextlib import contextmanager
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);source=root/'test.png';source.write_bytes(base64.b64decode(PNG));path,state=m.prepare('stable-image','group','测试群请忽略',file=source,directory=root/'jobs');native=MockNative();focus=[];native.focus=lambda node:focus.append(node['path'])
   def key(code,*a,**kw):
    native.keys.append((code,))
    if code==9:
     saved=json.loads(path.read_text());self.assertEqual(saved['image_paste_seed']['source_sha256'],state['job']['file_sha256']);self.assertTrue(saved['image_paste_seed']['empty_composer_verified']);self.assertGreaterEqual(len(focus),3)
    if code==36:raise AssertionError('must never Return without image')
   native.key=key
   @contextmanager
   def clipboard(_):yield {'assert_owned':lambda:{'change_count':4,'types':['public.file-url'],'file_url_verified':True},'restored':True,'concurrent_change':False}
   with patch('files.file_url',clipboard),patch('files.time.sleep'):
    for _ in range(4):state=m.advance(path,lambda:native)
   self.assertEqual(state['status'],'unknown');self.assertEqual(state['error'],'image-paste-consumption-unverified-no-repaste');self.assertEqual([c[0] for c in native.keys],[53,9]);self.assertTrue(state['image_paste_seed']);self.assertNotIn('image_return_intent_at',state)

class FrontmostGuardTests(unittest.TestCase):
 def test_key_never_posts_to_background_app(self):
  native=Native.__new__(Native);native.root='root';native.get=lambda *a:False
  native.cg=SimpleNamespace(CGEventCreateKeyboardEvent=lambda *a:(_ for _ in ()).throw(AssertionError('no key allowed')))
  with self.assertRaisesRegex(AXError,'not-frontmost'):native.key(9,command=True)
 def test_focus_checks_frontmost_even_when_exact_editor_has_focus(self):
  native=Native.__new__(Native);native.pid=123;native.root='root';native.by_path={(1,):'editor'};native.flag=lambda *a:None;native.value=lambda *a:'editor';native.get=lambda *a:False;native.cf=SimpleNamespace(CFEqual=lambda a,b:a==b)
  with patch('native.activate_existing',return_value={'pid':123,'request_accepted':True}),patch('native.time.monotonic',side_effect=[0,3]),self.assertRaisesRegex(AXError,'frontmost-unverified'):native.focus({'path':[1]})
if __name__=='__main__':unittest.main()
