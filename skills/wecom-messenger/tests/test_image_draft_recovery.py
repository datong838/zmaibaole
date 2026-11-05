import json,sys,copy,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import images,messenger as m,image_draft_recovery as recovery
import test_images as fixtures
image_snapshot=fixtures.image_snapshot
class DraftRecoveryTests(unittest.TestCase):
 def setUp(self):
  fixtures.ImageSenderTests.setUp(self);p=self.state['owned_image_paste'];self.state['image_paste_seed']={k:p[k] for k in ('source_sha256','pid','target','kind','clipboard','transcript')};self.state['image_paste_seed']['empty_composer_verified']=True;self.state['error']='image-owned-paste-draft-or-transcript-changed';m.atomic(self.path,self.state)
 def copy(self,job,action):
  action();return {'method':'public-selected-image-copy-exact-decoded-RGBA','source_sha256':job['file_sha256'],'width':2,'height':1,'rgba_sha256':'a'*64,'clipboard_before_change_count':10,'clipboard_copy_change_count':11}
 def recover(self,verifier=None):
  with patch.object(images,'OWNERSHIP_SESSION','new-recovery-process'):return recovery.recover(self.path,lambda:self.native,verifier or self.copy)
 def test_copy_recovers_same_job_once_without_paste_and_persists_return_before_key(self):
  def key(code,*a,**kw):
   s=json.loads(self.path.read_text())
   if code in (0,8):self.assertIn('draft_copy_recovery',s)
   if code==36:self.assertEqual(s['phase'],'image-verify-sent');self.assertEqual(s['image_proof']['copy_proof']['clipboard_copy_change_count'],11)
   self.native.keys.append(code)
  self.native.key=key;s=self.recover();self.assertEqual(self.native.keys,[0,8,36]);self.assertEqual(s['phase'],'image-verify-sent');self.assertEqual(s['job'],self.state['job']);self.assertTrue(self.path.with_name(self.path.stem+'.before-draft-copy-recovery.json').exists())
  with self.assertRaisesRegex(m.SendError,'scope-invalid'):self.recover()
  self.assertEqual(self.native.keys,[0,8,36])
 def test_copy_failure_is_locked_and_does_not_send_or_recopy(self):
  def fail(job,action):action();raise RuntimeError('image-copy-decoded-pixels-not-source')
  with self.assertRaisesRegex(RuntimeError,'pixels-not-source'):self.recover(fail)
  self.assertEqual([k[0] for k in self.native.keys],[0,8])
  with self.assertRaisesRegex(m.SendError,'intent-exists|scope-invalid'):self.recover()
  self.assertEqual([k[0] for k in self.native.keys],[0,8])
 def test_unchanged_clipboard_refuses_stale_data(self):
  def stale(job,action):v=self.copy(job,action);v['clipboard_copy_change_count']=10;return v
  with self.assertRaisesRegex(m.SendError,'copy-proof-invalid'):self.recover(stale)
  self.assertNotIn(36,self.native.keys)
 def test_changed_transcript_or_wrong_pid_refuses_before_any_key(self):
  self.native.tree=lambda:image_snapshot('\ufffc',with_image=True)
  with self.assertRaisesRegex(m.SendError,'transcript-changed'):self.recover()
  self.assertEqual(self.native.keys,[])
 def test_changed_process_refuses_before_copy_or_any_key(self):
  snap=image_snapshot('\ufffc');snap['pid']=999;self.native.tree=lambda:snap
  with self.assertRaisesRegex(m.SendError,'process-changed'):self.recover()
  self.assertEqual(self.native.keys,[])
 def test_exact_observed_system_input_source_indicator_does_not_block_real_draft(self):
  snap=image_snapshot('\ufffc');snap['tree']['children'].append({'role':'AXWindow','AXSubrole':'AXDialog','path':[99],'children':[{'role':'AXButton','AXIdentifier':'InputSource','AXDescription':'com.apple.inputmethod.SCIM.ITABC','AXEnabled':True,'path':[99,0],'children':[]}]});self.native.tree=lambda:snap
  s=self.recover();self.assertEqual(s['phase'],'image-verify-sent');self.assertEqual([k[0] for k in self.native.keys],[0,8,36])
 def test_real_or_unknown_dialog_never_copies_or_returns(self):
  for child in ({'role':'AXButton','AXTitle':'发送','AXEnabled':True,'path':[99,0],'children':[]},{'role':'AXButton','AXIdentifier':'InputSource','AXDescription':'different-input-source','AXEnabled':True,'path':[99,0],'children':[]}):
   snap=image_snapshot('\ufffc');snap['tree']['children'].append({'role':'AXWindow','AXSubrole':'AXDialog','path':[99],'children':[child]});self.native.tree=lambda:snap
   with self.assertRaisesRegex(m.SendError,'dialog-present'):self.recover()
   self.assertEqual(self.native.keys,[])
 def test_old_return_intent_refuses_copy(self):
  self.state['image_return_intent_at']=m.now();m.atomic(self.path,self.state)
  with self.assertRaisesRegex(m.SendError,'intent-exists|scope-invalid'):self.recover()
  self.assertEqual(self.native.keys,[])
 def test_recovery_cli_dispatches_original_job_only(self):
  import io,contextlib
  with patch.object(sys,'argv',['messenger.py','recover-image-draft','--job',str(self.path)]),patch.object(recovery,'recover',return_value=self.state) as run,contextlib.redirect_stdout(io.StringIO()):m.main()
  run.assert_called_once_with(str(self.path))
 def test_non_test_target_refuses_copy(self):
  self.state['job']['scope']='production';self.state['fingerprint']=__import__('hashlib').sha256(json.dumps(self.state['job'],ensure_ascii=False,sort_keys=True).encode()).hexdigest();m.atomic(self.path,self.state)
  with self.assertRaisesRegex(m.SendError,'scope-invalid|not-authorized'):self.recover()
  self.assertEqual(self.native.keys,[])
if __name__=='__main__':__import__('unittest').main()
