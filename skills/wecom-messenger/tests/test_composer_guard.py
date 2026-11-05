"""Actual saved WeCom shape replay; menu/focus metadata is explicitly synthetic.
No saved full-tree snapshot proves current menu absence. No UI/input APIs run.
"""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import composer_guard as g,guard_context as ctx
from native import Native
import ui
BASE=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/live-profile'
class FakeNative:
 def __init__(self,file='lumos-region-draft-unknown.ax.json'):
  snap=json.loads((BASE/file).read_text());self.pid=snap['pid'];self.by_path={};self.data={};self.children={};self.reads=[];self.inputs=[];self.next=1;self.front=True;self.windows_reads=0;self.change_windows=False;self.missing_attributes=False
  def store(node):
   e=self.next;self.next+=1;self.data[e]=copy.deepcopy({k:v for k,v in node.items() if k!='children'});self.children[e]=[store(c) for c in node.get('children',[])];return e
  self.root=store(snap['tree']);self.windows=[e for e,v in self.data.items() if v.get('role')=='AXWindow'];self.window=next(e for e in self.windows if self.data[e].get('AXSubrole')=='AXStandardWindow');self.editor=next(e for e,v in self.data.items() if v.get('role')=='AXTextArea' and 'AXValue' in v.get('settable',[]));self.focus=self.editor;self.tables=[e for e,v in self.data.items() if v.get('role')=='AXTable']
 def get(self,e,key):self.reads.append((e,key));return self.front if e==self.root and key=='AXFrontmost' else self.data[e].get('role') if key=='AXRole' else self.data[e].get(key)
 def value(self,e,key):self.reads.append((e,key));return self.window if key=='AXMainWindow' else self.focus if key=='AXFocusedUIElement' else None
 def same_element(self,a,b):return a==b
 def scoped_array(self,e,key,required=False):
  self.reads.append((e,key))
  if key=='AXWindows':
   self.windows_reads+=1
   return list(self.windows)+([9999] if self.change_windows and self.windows_reads>1 else [])
  if key=='AXChildren':return list(self.children[e])
  return None
 def scoped_settable(self,e,key):return key in self.data[e].get('settable',[])
 def node_attributes(self,e,keys):
  self.reads.append((e,'node_attributes'));r={k:self.get(e,k) for k in keys}
  if self.missing_attributes and e==self.editor:r.pop('AXValue')
  return r
 def activate(self,*a):raise AssertionError('must not activate')
 focus_input=activate;key=activate;press=activate;set_text=activate
class GuardTests(unittest.TestCase):
 def capture(self,n=None,menu=(-25212,False),**kwargs):
  self.n=n or FakeNative()
  with patch.object(g,'public_attribute',return_value=menu):return g.capture(self.n,**kwargs)
 def test_actual_saved_attachment_shape_with_synthetic_positive_menu_proof_no_history(self):
  s=self.capture(require_focused=True);self.assertTrue(s['guard_complete'],s['truncation_reason']);c=ctx.context(s,require_focused=True);ctx.verify(c,{'target':'测试群请忽略','kind':'group'});self.assertEqual(ui.value(c['composer']),'\ufffc');self.assertFalse(s['history_read']);self.assertFalse(s['transcript_complete']);self.assertNotIn('tree',s);self.assertNotIn('transcript',c)
  for table in self.n.tables:self.assertNotIn((table,'AXChildren'),self.n.reads)
  self.assertLess(s['node_count'],30);self.assertEqual(s['menu_evidence']['AX_error'],-25212)
 def test_old_saved_ax_does_not_prove_no_menu_unknown_unsupported_present_rejected(self):
  for reply in [(-25205,False),(-25204,False),(0,False),(0,True),(-25212,True)]:
   with self.subTest(reply=reply):
    s=self.capture(menu=reply);self.assertFalse(s['guard_complete']);self.assertEqual(s['menu_state'],'unknown');self.assertEqual(s['menu_evidence']['AX_error'],reply[0]);self.assertEqual(s['menu_evidence']['present'],reply[1]);self.assertEqual(s['menu_evidence']['owner'],'AXApplication');self.assertEqual(s['menu_evidence']['attribute'],'AXShownMenuUIElement')
    with self.assertRaises(ui.UIError):ctx.context(s)
 def test_unavailable_menu_diagnostics_distinguish_unsupported_busy_and_nil_success(self):
  for code,name in [(-25205,'kAXErrorAttributeUnsupported'),(-25204,'kAXErrorCannotComplete'),(0,'kAXErrorSuccess')]:
   s=self.capture(menu=(code,False))
   with self.subTest(code=code):
    self.assertFalse(s['guard_complete']);self.assertEqual(s['truncation_reason'],'composer-guard-menu-state-unavailable');self.assertEqual(s['menu_evidence'],{'attribute':'AXShownMenuUIElement','owner':'AXApplication','AX_error':code,'present':False,'result':name});self.assertNotEqual(s['menu_state'],'positively-no-shown-menu')
 def test_actual_observed_ime_indicator_is_narrow_exception_other_dialog_rejected(self):
  n=FakeNative('lumos-region-recovery-dialog.ax.json');s=self.capture(n);self.assertTrue(s['guard_complete'],s['truncation_reason']);self.assertEqual(len(s['extra_windows']),1)
  extra=next(e for e in n.windows if e!=n.window);button=n.children[extra][0];n.data[button]['AXDescription']='unreviewed';s=self.capture(n);self.assertFalse(s['guard_complete']);self.assertIn('extra-window',s['truncation_reason'])
 def test_nested_sheet_menu_and_unknown_control_rejected(self):
  for role in ['AXSheet','AXDialog','AXMenu','AXMenuItem','AXUnknown']:
   n=FakeNative();e=n.next;n.next+=1;n.data[e]={'role':role};n.children[e]=[];n.children[n.window].append(e);s=self.capture(n)
   with self.subTest(role=role):self.assertFalse(s['guard_complete'])
 def test_duplicate_recipient_action_and_editor_refuse(self):
  for mode in ['header','editor']:
   n=FakeNative();orig=next(e for e,d in n.data.items() if d.get('AXHelp')=='添加群成员') if mode=='header' else n.editor;e=n.next;n.data[e]=copy.deepcopy(n.data[orig]);n.children[e]=[];parent=next(parent for parent,children in n.children.items() if orig in children);n.children[parent].append(e);s=self.capture(n)
   with self.subTest(mode=mode):self.assertFalse(s['guard_complete']);self.assertIn('ambiguous',s['truncation_reason'])
 def test_fresh_focus_and_frontmost_are_read_not_changed(self):
  n=FakeNative();n.front=False;s=self.capture(n);self.assertTrue(s['guard_complete']);self.assertFalse(s['input_ready'])
  with self.assertRaises(ui.UIError):ctx.context(s,require_focused=True)
  s=self.capture(n,require_focused=True);self.assertFalse(s['guard_complete']);n.front=True;n.focus=n.window;s=self.capture(n,require_focused=True);self.assertFalse(s['guard_complete']);self.assertEqual(n.inputs,[])
 def test_window_set_changes_and_missing_critical_attributes_refuse(self):
  n=FakeNative();n.change_windows=True;s=self.capture(n);self.assertFalse(s['guard_complete']);self.assertIn('window-set-changed',s['truncation_reason'])
  n=FakeNative();n.missing_attributes=True;s=self.capture(n);self.assertFalse(s['guard_complete']);self.assertIn('attributes-incomplete',s['truncation_reason'])
 def test_mid_read_structural_sheet_or_editor_insertion_refuses_without_history(self):
  for inserted_role in ('AXSheet','AXTextArea'):
   n=FakeNative();original=n.node_attributes;changed=[False]
   parent=next(parent for parent,children in n.children.items() if n.editor in children)
   def during(e,keys):
    result=original(e,keys)
    if e==n.editor and not changed[0]:
     added=n.next;n.next+=1;n.data[added]={'role':inserted_role,'settable':['AXValue']};n.children[added]=[];n.children[parent].append(added);changed[0]=True
    return result
   n.node_attributes=during;s=self.capture(n)
   with self.subTest(role=inserted_role):
    self.assertFalse(s['guard_complete']);self.assertEqual(s['truncation_reason'],'composer-guard-structure-changed-during-read')
    for table in n.tables:self.assertNotIn((table,'AXChildren'),n.reads)
 def test_budget_failure_is_not_a_successful_partial_scope(self):
  s=self.capture(max_nodes=5);self.assertTrue(s['truncated']);self.assertFalse(s['guard_complete']);self.assertIn('node-limit',s['truncation_reason'])
 def test_native_entry_only_delegates_and_sets_honest_read_metadata(self):
  n=FakeNative()
  with patch.object(g,'public_attribute',return_value=(-25212,False)):s=Native.composer_guard(n)
  self.assertTrue(s['guard_complete']);self.assertEqual(n.last_snapshot_metadata['read_scope'],g.SCOPE);self.assertFalse(n.last_snapshot_metadata['history_read'])
 def test_public_menu_reader_preserves_no_value_vs_unsupported_and_releases_refs(self):
  import ctypes as C
  from types import SimpleNamespace
  released=[]
  for code,present in [(-25212,False),(-25205,False),(0,True)]:
   def read(element,key,out):
    if present:C.cast(out,C.POINTER(C.c_void_p))[0]=123
    return code
   native=SimpleNamespace(string=lambda s:77,ax=SimpleNamespace(AXUIElementCopyAttributeValue=read),cf=SimpleNamespace(CFRelease=released.append))
   self.assertEqual(g.public_attribute(native,1,'AXShownMenuUIElement'),(code,present))
  self.assertEqual(released,[77,77,77,123])
 def test_guard_context_is_separate_and_wrong_target_or_scope_refused(self):
  s=self.capture();c=ctx.context(s)
  with self.assertRaises(ui.UIError):ctx.verify(c,{'target':'wrong','kind':'group'})
  s['read_scope']='application-windows-complete'
  with self.assertRaises(ui.UIError):ctx.context(s)
if __name__=='__main__':unittest.main()
