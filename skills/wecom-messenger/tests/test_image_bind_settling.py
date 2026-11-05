"""Fake Native, clipboard and monotonic clock. No real UI/clipboard/network."""
import copy,hashlib,json,sys,tempfile,types,unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=R/'skills/wecom-messenger/scripts';sys.path[:0]=[str(S),str(R/'skills/wecom-messenger/tests')]
import files as f
import images,messenger as m,ui,test_images as fixtures
class Clock:
 def __init__(self):self.now=0
 def monotonic(self):return self.now
 def sleep(self,seconds):self.now+=seconds
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.source=self.root/'mock.png';self.source.write_bytes(b'synthetic-png');self.path,self.s=m.prepare('settling-test','group','测试群请忽略',file=self.source,directory=self.root/'jobs');self.s['pid']=123;self.s['baseline']=0;self.clock=Clock();self.keys=[];self.focus=[];self.pasted=False;self.post_reads=0;self.total_reads=0;self.clip_calls=0;self.snapshots=[fixtures.image_snapshot('\ufffc')];self.durations=[];self.hook=None;self.clip_hook=None
  def tree():
   self.total_reads+=1
   if not self.pasted:return fixtures.image_snapshot('')
   self.post_reads+=1
   if self.durations:self.clock.now+=self.durations[min(self.post_reads-1,len(self.durations)-1)]
   if self.hook:self.hook(self.post_reads)
   return copy.deepcopy(self.snapshots[min(self.post_reads-1,len(self.snapshots)-1)])
  def key(code,*args,**kw):
   self.keys.append(code)
   if code==9:
    saved=json.loads(self.path.read_text());self.seed=copy.deepcopy(saved['image_paste_seed']);self.pasted=True
   if code==36:raise AssertionError('stage must never Return')
  self.native=types.SimpleNamespace(tree=tree,focus=lambda n:self.focus.append(n['path']),key=key,close=lambda:None)
  @contextmanager
  def clipboard(path):
   def owned():
    self.clip_calls+=1;v={'change_count':7,'types':['public.file-url'],'file_url_verified':True}
    if self.clip_hook:self.clip_hook(v,self.clip_calls)
    return v
   yield {'assert_owned':owned,'restored':True,'concurrent_change':False}
  self.addCleanup(patch.stopall);patch.object(f,'file_url',clipboard).start();patch.object(f,'time',self.clock).start()
 def run_stage(self):return f.stage_file(self.native,self.s,self.path,m.atomic,m.event)
 def assert_one_paste(self):self.assertEqual(self.keys,[53,9]);self.assertEqual(len(self.focus),3);self.assertEqual(self.s['image_paste_seed'],self.seed)
 def test_only_transcript_transient_restores_then_original_bind(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True),fixtures.image_snapshot('\ufffc')];self.run_stage();self.assert_one_paste();self.assertEqual(self.post_reads,2);self.assertEqual(self.s['owned_image_paste']['transcript'],self.seed['transcript']);self.assertNotIn('image_paste_binding_failure',self.s);self.assertTrue(any(e['stage']=='file-pasted' for e in self.s['events']))
 def test_persistent_transcript_diff_eight_reads_no_rebase_diagnostic_durable(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True)]
  with self.assertRaisesRegex(ui.UIError,'seed-or-transcript'):self.run_stage()
  self.assert_one_paste();self.assertEqual(self.post_reads,8);saved=json.loads(self.path.read_text());d=saved['image_paste_binding_failure'];self.assertEqual(saved['status'],'unknown');self.assertEqual(d['original_transcript'],self.seed['transcript']);self.assertEqual(d['diff_indices'],[1]);self.assertIsNotNone(d['snapshot_sha256']);self.assertFalse(d['message_text_recorded']);self.assertNotIn('owned_image_paste',saved);self.assertFalse(any(e['stage']=='file-pasted' for e in saved['events']))
 def test_clipboard_change_immediate_not_settling(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True)];self.clip_hook=lambda v,n:v.update(change_count=8) if n>1 else None
  with self.assertRaisesRegex(ui.UIError,'clipboard-binding-changed'):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assert_one_paste()
 def test_session_change_is_not_a_transcript_only_difference(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True)]
  with patch.object(images,'OWNERSHIP_SESSION',images.OWNERSHIP_SESSION):
   self.hook=lambda n:setattr(images,'OWNERSHIP_SESSION','different-session')
   with self.assertRaisesRegex(ui.UIError,'seed-or-transcript'):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assertIn('ownership_session',self.s['image_paste_binding_failure']['seed_diff_fields']);self.assert_one_paste()
 def test_source_change_immediate(self):
  self.hook=lambda n:self.source.write_bytes(b'changed')
  with self.assertRaisesRegex(ui.UIError,'source-changed'):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assert_one_paste()
 def test_pid_target_truncated_and_multiple_attachments_refuse(self):
  for kind in ('pid','target','truncated','multiple'):
   # Each subcase gets a fresh independent original key/TEMP state.
   case=Tests();case.setUp()
   try:
    snap=fixtures.image_snapshot('\ufffc')
    if kind=='pid':snap['pid']=999
    elif kind=='target':ui.context(snap)['header']['AXValue']='other'
    elif kind=='truncated':snap['truncated']=True
    else:ui.context(snap)['composer']['children'].append(copy.deepcopy(ui.context(snap)['composer']['children'][0]))
    case.snapshots=[snap]
    with self.assertRaises(ui.UIError):case.run_stage()
    self.assertEqual(case.post_reads,1);case.assert_one_paste();self.assertNotIn('owned_image_paste',case.s)
   finally:case.doCleanups()
 def test_late_second_read_cannot_bind_or_start_third(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True),fixtures.image_snapshot('\ufffc')];self.durations=[13,13]
  with self.assertRaises(ui.UIError):self.run_stage()
  self.assertEqual(self.post_reads,2);self.assertTrue(self.s['image_paste_binding_failure']['deadline_exhausted']);self.assertGreater(self.clock.now,20);self.assertNotIn('owned_image_paste',self.s);self.assert_one_paste()
 def test_first_read_overruns_deadline_no_late_bind(self):
  self.durations=[21]
  with self.assertRaises(ui.UIError):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assertNotIn('owned_image_paste',self.s);self.assert_one_paste()
 def test_late_pure_bind_cannot_publish_owned_proof_or_bound_event(self):
  original=images.bind_owned_paste
  def late(*a,**kw):original(*a,**kw);self.clock.now+=21
  with patch.object(images,'bind_owned_paste',side_effect=late),self.assertRaises(ui.UIError):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assertNotIn('owned_image_paste',self.s);self.assertFalse(any(e['stage']=='owned-image-paste-bound' for e in self.s['events']));self.assert_one_paste()
 def test_followup_unknown_ticks_never_restage_or_return(self):
  self.snapshots=[fixtures.image_snapshot('\ufffc',with_image=True)]
  with self.assertRaises(ui.UIError):self.run_stage()
  for _ in range(2):result=m.advance(self.path,lambda:self.native)
  self.assertEqual(result['status'],'unknown');self.assertEqual(self.keys,[53,9]);self.assertEqual(result['image_paste_seed'],self.seed);self.assertIn('image_paste_binding_failure',result);self.assertNotIn('owned_image_paste',result)
 def test_unknown_seed_mutation_is_not_baseline_recovery(self):
  self.hook=lambda n:self.s['image_paste_seed'].update(pid=999)
  with self.assertRaisesRegex(ui.UIError,'seed-or-transcript'):self.run_stage()
  self.assertEqual(self.post_reads,1);self.assertNotIn('owned_image_paste',self.s)
if __name__=='__main__':unittest.main()
