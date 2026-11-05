"""Synthetic sender/native/copy-pixels only. Never invokes real UI/clipboard."""
import copy,hashlib,json,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=R/'skills/wecom-messenger/scripts';sys.path[:0]=[str(S),str(R/'skills/wecom-messenger/tests')]
import images,messenger as m,image_draft_recovery as recovery,ui,test_images as fixtures
class SeedTests(unittest.TestCase):
 def setUp(self):
  fixtures.ImageSenderTests.setUp(self);runtime=patch.object(m,'RUNTIME',self.path.parent);runtime.start();self.addCleanup(runtime.stop);proof=self.state.pop('owned_image_paste');self.state['image_paste_seed']={k:proof[k] for k in ('source_sha256','pid','target','kind','clipboard','transcript')};self.state['image_paste_seed'].update(empty_composer_verified=True,ownership_session='a'*32);self.state['error']='image-paste-seed-or-transcript-changed';at=m.now();self.state['send_intent_at']=at;self.state['events']=[{'stage':'recipient-verified','at':at,'name':self.state['job']['target'],'kind':'group'},{'stage':'send-intent','at':at,'file':self.state['job']['file_name'],'sha256':self.state['job']['file_sha256']},{'stage':'image-paste-seed-persisted','at':at,'source_sha256':self.state['job']['file_sha256']},{'stage':'stopped','at':at,'error':self.state['error']}];self.save();self.original=self.path.read_bytes();self.original_sha=hashlib.sha256(self.original).hexdigest()
 def save(self):m.atomic(self.path,self.state)
 def copy(self,job,action):
  action();return {'method':'public-selected-image-copy-exact-decoded-RGBA','source_sha256':job['file_sha256'],'width':2,'height':1,'rgba_sha256':'d'*64,'clipboard_before_change_count':10,'clipboard_copy_change_count':11,'clipboard_format':'public.png','clipboard_restore':'only-if-still-owned'}
 def recover(self,verify=None):return recovery.recover(self.path,lambda:self.native,verify or self.copy,original_sha256=self.original_sha)
 def keys(self):return [x[0] if isinstance(x,tuple) else x for x in self.native.keys]
 def staged(self):
  # Stop before Return solely to inspect durable typed staging for negative replay.
  with patch.object(images,'confirm_image',return_value=None):self.recover()
  return json.loads(self.path.read_text())
 def test_exact_seed_copy_once_return_intent_first_no_fake_file_pasted(self):
  def key(code,*args,**kw):
   saved=json.loads(self.path.read_text());self.assertIn('draft_copy_recovery',saved)
   if code==36:self.assertEqual(saved['phase'],'image-verify-sent');self.assertIn('seed_copy_staging',saved);self.assertIn('image_return_intent_at',saved)
   self.native.keys.append(code)
  self.native.key=key;s=self.recover();self.assertEqual(self.keys(),[0,8,36]);self.assertEqual(s['job'],self.state['job']);self.assertEqual(s['image_paste_seed'],self.state['image_paste_seed']);self.assertFalse(any(e['stage']=='file-pasted' for e in s['events']));self.assertEqual(Path(s['draft_copy_recovery']['original_job']['path']).read_bytes(),self.original)
  with self.assertRaises(m.SendError):self.recover()
  self.assertEqual(self.keys(),[0,8,36])
 def test_copy_failure_no_return_no_retry_cross_process(self):
  def bad(job,action):action();raise RuntimeError('exact-pixels-mismatch')
  with self.assertRaisesRegex(m.SendError,'pixels-mismatch'):self.recover(bad)
  with patch.object(images,'OWNERSHIP_SESSION','b'*32),self.assertRaises(m.SendError):self.recover()
  self.assertEqual(self.keys(),[0,8])
 def test_no_original_sha_or_bad_seed_refuses_without_input(self):
  with self.assertRaises(m.SendError):recovery.recover(self.path,lambda:self.native,self.copy,original_sha256='0'*64)
  self.assertEqual(self.keys(),[])
  self.state['image_paste_seed']['clipboard']['change_count']=True;self.save();self.original_sha=hashlib.sha256(self.path.read_bytes()).hexdigest()
  with self.assertRaises(m.SendError):self.recover()
  self.assertEqual(self.keys(),[])
 def test_changed_baseline_multiple_attachment_pid_or_dialog_no_input(self):
  for mode in ('baseline','attachments','pid','dialog'):
   snap=fixtures.image_snapshot('\ufffc',with_image=mode=='baseline')
   if mode=='attachments':ui.context(snap)['composer']['children'].append(copy.deepcopy(ui.context(snap)['composer']['children'][0]))
   if mode=='pid':snap['pid']=999
   if mode=='dialog':snap['tree']['children'].append({'role':'AXSheet','path':[8],'children':[]})
   self.native.tree=lambda:snap
   with self.assertRaises(m.SendError):self.recover()
   self.assertEqual(self.keys(),[])
 def test_source_file_change_or_prior_return_intent_no_input(self):
  self.state['image_return_intent_at']=m.now();self.save()
  with self.assertRaises(m.SendError):self.recover()
  self.state.pop('image_return_intent_at');self.save();Path(self.state['job']['file']).write_bytes(b'changed')
  with self.assertRaises(m.SendError):self.recover()
  self.assertEqual(self.keys(),[])
 def test_fake_event_or_missing_typed_proof_never_qualifies(self):
  s=copy.deepcopy(self.state);s['events'].append({'stage':'image-seed-copy-staging-verified','staging_sha256':'x'})
  with self.assertRaises(ui.UIError):images.confirm_image(self.native,s,ui.context(self.native.tree()),self.path,m.atomic,m.event)
  self.assertEqual(self.keys(),[])
 def test_staged_binding_corruption_job_baseline_session_archive(self):
  s=self.staged();ctx=ui.context(self.native.tree());recovery.verify_seed_staging(s,ctx)
  for mode in ('proof','job','baseline','session','archive'):
   bad=copy.deepcopy(s)
   if mode=='proof':bad.pop('owned_image_paste')
   elif mode=='job':bad['job']['key']='other-job'
   elif mode=='baseline':bad['owned_image_paste']['transcript']=[]
   elif mode=='session':bad['seed_copy_staging']['ownership_session']='other-session'
   else:Path(s['draft_copy_recovery']['original_job']['path']).write_bytes(b'{}')
   with self.assertRaises((ui.UIError,m.SendError,ValueError,KeyError)):recovery.verify_seed_staging(bad,ctx)
  self.assertNotIn(36,self.keys())
 def test_invalid_copy_counts_or_pixels_metadata_do_not_return(self):
  def bad(job,action):proof=self.copy(job,action);proof['rgba_sha256']='not-a-sha';return proof
  with self.assertRaises(m.SendError):self.recover(bad)
  self.assertNotIn(36,self.keys())
 def test_seed_path_never_settles_or_substitutes_another_snapshot(self):
  count=[]
  def tree():
   count.append(1)
   if len(count)==5:return fixtures.image_snapshot('\ufffc',with_image=True)
   snap=fixtures.image_snapshot('\ufffc')
   if len(count)>=6:snap['tree']['children'].append({'role':'AXSheet','path':[8],'children':[]})
   return snap
  self.native.tree=tree
  with patch.object(images,'settled_owned_proof',side_effect=AssertionError('seed must not settle')),self.assertRaises(m.SendError):self.recover()
  self.assertEqual(len(count),5);self.assertEqual(self.keys(),[0,8])
 def test_fake_copy_verifier_without_copy_action_or_double_action_refuses(self):
  def noaction(job,action):return self.copy(job,lambda:None)
  with self.assertRaises(m.SendError):self.recover(noaction)
  self.assertEqual(self.keys(),[])
 def test_copy_action_is_single_use_even_inside_verifier(self):
  def twice(job,action):self.copy(job,action);action()
  with self.assertRaisesRegex(m.SendError,'already-used'):self.recover(twice)
  self.assertEqual(self.keys(),[0,8])
 def test_copied_same_basename_cannot_escape_canonical_runtime(self):
  folder=self.root/'copy';folder.mkdir();target=folder/self.path.name;target.write_bytes(self.original)
  with self.assertRaisesRegex(m.SendError,'sha-or-path-required'):recovery.recover(target,lambda:self.native,self.copy,original_sha256=self.original_sha)
  self.assertEqual(self.keys(),[]);self.assertEqual(self.path.read_bytes(),self.original)
 def test_sender_lock_rejects_concurrent_recovery(self):
  with m.lock(self.path.parent),self.assertRaisesRegex(m.SendError,'sender-busy'):self.recover()
  self.assertEqual(self.keys(),[])
if __name__=='__main__':unittest.main()
