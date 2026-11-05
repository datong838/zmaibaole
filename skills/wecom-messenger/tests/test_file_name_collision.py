"""Synthetic same-name/different-content history. No runtime dependencies or UI."""
import sys,json,hashlib,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import messenger as m,files,ui
from test_sender import MockNative
class CollisionTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/'违规汇总.xlsx';self.source.write_bytes(b'new real scope fixture');self.path,self.state=m.prepare('original-real-scope-key','group','测试群请忽略',file=self.source,directory=self.root/'jobs')
 def test_same_display_name_different_content_is_baseline_not_duplicate_and_owned_file_sends_once(self):
  n=MockNative();n.messages=[self.source.name];n.attachment=None;n.pastes=0;tree=n.tree
  def snapshot():
   s=tree()
   if n.attachment:
    c=ui.context(s)['composer'];c['children']=[{'role':'AXUnknown','AXSubrole':'AXTextAttachment','AXURL':n.attachment,'path':c['path']+[0],'children':[]}]
   return s
  n.tree=snapshot
  def key(code,*a,**kw):
   if code==53:return
   saved=json.loads(self.path.read_text());self.assertTrue(saved.get('send_intent_at'))
   if code==9:n.pastes+=1;n.attachment=self.source.as_uri();n.draft='\ufffc'
   elif code==36:
    self.assertEqual(saved['phase'],'verify-sent');self.assertEqual(saved['baseline'],1);n.sends+=1;n.messages.append(self.source.name);n.draft='';n.attachment=None
  n.key=key
  @contextmanager
  def clipboard(_):yield {'restored':True,'concurrent_change':False}
  with patch.object(files,'file_url',clipboard),patch.object(files.time,'sleep'):
   for _ in range(9):result=m.advance(self.path,lambda:n)
  self.assertEqual(result['status'],'complete');self.assertEqual(result['baseline'],1);self.assertEqual((n.pastes,n.sends),(1,1));self.assertEqual(result['job'],self.state['job']);m.advance(self.path,lambda:n);self.assertEqual(n.sends,1)
 def test_same_tick_merge_file_baseline_one_is_not_text_duplicate(self):
  from test_initial_no_input_merge import Tracked
  n=Tracked();n.messages=[self.source.name];result=m.advance(self.path,lambda:n);self.assertEqual(result['baseline'],1);self.assertEqual(result['phase'],'stage');self.assertEqual(result['error'],'stop-before-fake-input');self.assertNotIn('send_intent_at',result);self.assertFalse(n.keys)
 def test_original_failed_no_input_job_can_resume_same_key_only_with_fresh_pid_target_empty_composer(self):
  self.state.update(status='failed',phase='verify',pid=123,baseline=1,error='same-content-already-visible');m.atomic(self.path,self.state);n=MockNative();n.messages=[self.source.name];result=m.resume_before_send(self.path,lambda:n);self.assertEqual(result['job'],self.state['job']);self.assertEqual(result['fingerprint'],self.state['fingerprint']);self.assertEqual(result['status'],'running');self.assertEqual(result['phase'],'locate');self.assertFalse(n.keys)
 def test_historical_row_without_new_record_never_confirms_current_return(self):
  self.state.update(status='unknown',phase='verify-sent',pid=123,baseline=1,send_intent_at=m.now(),events=[{'stage':'file-confirm-intent','attachment_url_verified':True}]);m.atomic(self.path,self.state);n=MockNative();n.messages=[self.source.name];result=m.advance(self.path,lambda:n);self.assertFalse(result['ui_confirmed']);self.assertEqual(result['status'],'unknown');self.assertFalse(n.keys)
  n.messages.append(self.source.name);result=m.advance(self.path,lambda:n);self.assertEqual(result['status'],'complete');self.assertFalse(n.keys)
 def test_text_duplicate_guard_remains(self):
  path,state=m.prepare('text','group','测试群请忽略',text='original text',directory=self.root/'jobs');n=MockNative();n.messages=['original text'];m.advance(path,lambda:n);result=m.advance(path,lambda:n);self.assertEqual(result['error'],'same-content-already-visible');self.assertFalse(n.keys)
 def test_unknown_paste_return_or_choice_cannot_resume_or_change_key(self):
  for mode in ('unknown','paste','return','choice'):
   state=json.loads(json.dumps(self.state));state.update(status='unknown' if mode=='unknown' else 'failed',phase='verify',pid=123)
   if mode=='paste':state['send_intent_at']=m.now()
   elif mode=='return':state['image_return_intent_at']=m.now()
   elif mode=='choice':state['original_file_choice_intent_at']=m.now()
   m.atomic(self.path,state)
   with self.subTest(mode=mode),self.assertRaisesRegex(m.SendError,'resume-not-safe'):m.resume_before_send(self.path,MockNative)
 def test_wrong_file_hash_recipient_or_existing_draft_cannot_resume(self):
  self.state.update(status='failed',phase='verify',pid=123);m.atomic(self.path,self.state)
  for mode in ('target','draft'):
   n=MockNative()
   if mode=='target':n.target='wrong group'
   else:n.draft='existing draft'
   with self.subTest(mode=mode),self.assertRaises((m.SendError,ui.UIError)):m.resume_before_send(self.path,lambda:n)
  self.source.write_bytes(b'modified')
  with self.assertRaisesRegex(m.SendError,'file-changed'):m.resume_before_send(self.path,MockNative)
if __name__=='__main__':unittest.main()
