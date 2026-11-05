"""Pure fakes only. Formal sender and archived baseline; no UI/framework actions."""
import sys,copy,json,tempfile,unittest,importlib.util
from pathlib import Path
from unittest.mock import patch
CAND=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CAND/'scripts'))
import messenger as m,files
from test_sender import MockNative
sp=importlib.util.spec_from_file_location('baseline_sender',Path(__file__).parent/'fixtures/messenger-before-initial-merge.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old);old.POLICY=m.POLICY
class Tracked(MockNative):
 def __init__(self):super().__init__();self.pid=123;self.input_generation=0;self.by_path={};self.reads=0;self.inputs=[]
 def tree(self):self.reads+=1;self.by_path={};s=super().tree();s['read_scope']='application-windows-complete';return s
 def set_text(self,n,text):self.inputs.append('set_text');self.input_generation+=1;super().set_text(n,text)
 def flag(self,*a):self.inputs.append('flag');self.input_generation+=1;self.target='测试群请忽略'
 def focus(self,n):self.inputs.append('focus');self.input_generation+=1;raise RuntimeError('stop-before-fake-input')
 def key(self,*a,**kw):self.inputs.append('key');self.input_generation+=1;super().key(*a,**kw)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def job(self,key='j',file=False):
  if file:
   p=self.root/'f.png';p.write_bytes(b'not real image, stop before first input');return m.prepare(key,'group','测试群请忽略',file=p,directory=self.root/'jobs')
  return m.prepare(key,'group','测试群请忽略',text='candidate text',directory=self.root/'jobs')
 def test_initial_text_reduces_three_full_reads_to_one_and_same_phase_state_events(self):
  p,_=self.job('new');q,_=self.job('old');a,b=Tracked(),Tracked()
  with patch.object(m,'now',return_value='fixed'),patch.object(old,'now',return_value='fixed'):
   result=m.advance(p,lambda:a)
   for _ in range(3):baseline=old.advance(q,lambda:b)
  self.assertEqual((a.reads,b.reads),(1,3));self.assertEqual((result['phase'],baseline['phase']),('ready','ready'));self.assertEqual(a.draft,b.draft);self.assertEqual(result['events'],baseline['events']);self.assertEqual(result['baseline'],baseline['baseline']);self.assertEqual(a.inputs,['set_text']);self.assertFalse(a.keys);self.assertNotIn('send_intent_at',result)
 def test_png_initial_segment_reduces_two_reads_but_keeps_first_focus_boundary(self):
  p,_=self.job('newfile',True);q,_=self.job('oldfile',True);a,b=Tracked(),Tracked();r=m.advance(p,lambda:a)
  for _ in range(3):s=old.advance(q,lambda:b)
  self.assertEqual((a.reads,b.reads),(1,3));self.assertEqual((r['phase'],s['phase']),('stage','stage'));self.assertEqual(r['error'],s['error']);self.assertEqual(a.inputs,['focus']);self.assertFalse(a.keys);self.assertNotIn('send_intent_at',r)
 def test_changes_during_local_checkpoint_block_before_any_input(self):
  for mode in ('generation','pid','target','mapping','snapshot'):
   p,_=self.job('mutation-'+mode);n=Tracked();atomic=m.atomic;changed=False
   def intercept(path,state):
    nonlocal changed
    atomic(path,state)
    if not changed and state['phase']=='verify':
     changed=True
     if mode=='generation':n.input_generation+=1
     elif mode=='pid':n.pid=999
     elif mode=='target':state['job']['target']='foreign'
     elif mode=='mapping':n.by_path={}
     else:
      # Locate the same local snapshot retained by the created ticket.
      ticket.snapshot['tree']['children'][0]['AXTitle']='mutated'
   original=files.stage_read;ticket=None
   def capture(*args):
    nonlocal ticket
    ticket=original(*args);return ticket
   with self.subTest(mode=mode),patch.object(m,'atomic',side_effect=intercept),patch.object(files,'stage_read',side_effect=capture):r=m.advance(p,lambda:n)
   self.assertEqual(r['status'],'failed');self.assertFalse(n.inputs);self.assertNotIn('send_intent_at',r)
 def test_selection_is_input_boundary_not_merged_and_next_call_reads_fresh(self):
  p,_=self.job('selection');n=Tracked();n.target='other';r=m.advance(p,lambda:n);self.assertEqual(r['phase'],'verify');self.assertEqual(n.inputs,['flag']);self.assertEqual(n.reads,1);r=m.advance(p,lambda:n);self.assertEqual(n.reads,2);self.assertEqual(r['phase'],'ready')
 def test_unknown_return_never_restages_or_sends(self):
  p,s=self.job('unknown',True);s.update(status='unknown',phase='image-verify-sent',pid=123,send_intent_at=m.now(),image_return_intent_at=m.now());m.atomic(p,s);n=Tracked()
  with patch.object(files,'stage_file',side_effect=AssertionError('no-restage')):r=m.advance(p,lambda:n)
  self.assertEqual(r['status'],'unknown');self.assertFalse(n.inputs);self.assertEqual(n.reads,1)
 def test_single_use_ticket_cannot_cross_native_or_call(self):
  n=Tracked();job={'kind':'group','target':'测试群请忽略'};t=files.stage_read(n,n.tree(),job)
  with self.assertRaises(files.FileError):t.take(Tracked(),job)
  t.take(n,job)
  with self.assertRaises(files.FileError):t.take(n,job)
 def test_failed_terminal_and_error_or_unknown_entry_never_use_merge_ticket(self):
  for mode in ('failed','error','unknown'):
   p,s=self.job('entry-'+mode);s['status']='failed' if mode=='failed' else 'unknown' if mode=='unknown' else 'running'
   if mode=='error':s['error']='original-error'
   m.atomic(p,s);n=Tracked()
   with patch.object(files,'stage_read',side_effect=AssertionError('no-initial-merge')):r=m.advance(p,lambda:n)
   self.assertFalse(n.inputs);self.assertEqual(r['phase'],'locate' if mode=='failed' else 'verify');self.assertEqual(n.reads,0 if mode=='failed' else 1)
 def test_incomplete_initial_tree_is_not_a_reusable_guard(self):
  p,_=self.job('incomplete');n=Tracked();tree=n.tree
  def incomplete():
   s=tree();s['truncated']=True;return s
  n.tree=incomplete;r=m.advance(p,lambda:n);self.assertEqual(r['status'],'failed');self.assertFalse(n.inputs)
 def test_no_ticket_capability_preserves_legacy_one_phase_per_call(self):
  p,_=self.job('legacy');n=MockNative();r=m.advance(p,lambda:n);self.assertEqual(r['phase'],'verify');self.assertEqual(n.draft,'')
if __name__=='__main__':unittest.main()
