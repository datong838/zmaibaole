"""Pure fake Native tests. No macOS UI or actual paste/send."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from test_sender import MockNative,fixture
import files,messenger as m,ui
from native import Native
class StopBeforeInput(RuntimeError):pass
class TrackedNative(MockNative):
 def __init__(self):super().__init__();self.pid=123;self.input_generation=0;self.by_path={};self.reads=0
 def tree(self):self.reads+=1;s=super().tree();s['read_scope']='application-windows-complete';return s
 def focus(self,node):raise StopBeforeInput('test-stop-before-first-input')
class HandoffTests(unittest.TestCase):
 def setUp(self):self.n=TrackedNative();self.job={'target':'测试群请忽略','kind':'group'}
 def ticket(self):return files.stage_read(self.n,self.n.tree(),self.job)
 def test_normal_same_tick_advance_first_tree_only_once(self):
  with tempfile.TemporaryDirectory() as folder:
   f=Path(folder)/'f.png';f.write_bytes(b'fake source only, no paste');p,s=m.prepare('same-tick','group','测试群请忽略',file=f,directory=Path(folder)/'jobs');s.update(phase='stage',pid=123);m.atomic(p,s)
   result=m.advance(p,lambda:self.n)
   self.assertEqual(self.n.reads,1);self.assertEqual(result['error'],'test-stop-before-first-input');self.assertFalse(self.n.keys);self.assertNotIn('send_intent_at',result)
 def test_different_native_target_pid_window_or_read_mapping_rejected(self):
  for mode in ('native','target','pid','window','mapping'):
   self.n=TrackedNative();ticket=self.ticket();native=self.n;job=self.job
   if mode=='native':native=TrackedNative()
   elif mode=='target':job={**job,'target':'另一群'}
   elif mode=='pid':self.n.pid=999
   elif mode=='window':ticket.snapshot['tree']['children'][0]['path']=[9]
   else:self.n.by_path={}
   with self.subTest(mode=mode),self.assertRaises(files.FileError):ticket.take(native,job)
 def test_intermediate_native_input_invalidates_handoff(self):
  for method,args in (('set_text',({'path':[1]},'x')),('press',({'path':[1]},)),('flag',({'path':[1]},'AXFocused')),('key',(9,))):
   ticket=self.ticket();probe=object.__new__(Native);probe.input_generation=ticket.generation;probe.by_path={}
   # Fail before any real framework call; generation still marks attempted input.
   try:getattr(probe,method)(*args)
   except (AttributeError,RuntimeError):pass
   self.n.input_generation=probe.input_generation
   with self.subTest(method=method),self.assertRaisesRegex(files.FileError,'handoff-changed'):ticket.take(self.n,self.job)
 def test_default_old_stage_call_still_reads_tree(self):
  with self.assertRaises(StopBeforeInput):files.stage_file(self.n,{'job':self.job},None,None,None)
  self.assertEqual(self.n.reads,1)
 def test_single_use_and_incomplete_snapshots(self):
  ticket=self.ticket();self.assertEqual(ticket.take(self.n,self.job)['name'],self.job['target'])
  with self.assertRaisesRegex(files.FileError,'handoff-changed'):ticket.take(self.n,self.job)
  s=self.n.tree();s['truncated']=True
  with self.assertRaises(ui.UIError):files.stage_read(self.n,s,self.job)
 def test_unknown_after_return_only_reads_no_stage_or_key(self):
  with tempfile.TemporaryDirectory() as folder:
   f=Path(folder)/'f.png';f.write_bytes(b'fake');p,s=m.prepare('unknown','group','测试群请忽略',file=f,directory=Path(folder)/'jobs');s.update(phase='image-verify-sent',status='unknown',pid=123,send_intent_at=m.now(),image_return_intent_at=m.now());m.atomic(p,s)
   with patch.object(files,'stage_file',side_effect=AssertionError('must-not-restage')):result=m.advance(p,lambda:self.n)
   self.assertEqual(result['status'],'unknown');self.assertFalse(self.n.keys)
if __name__=='__main__':unittest.main()
