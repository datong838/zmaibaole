"""Tiny immutable fixtures only; no UI or production evidence writes."""
import copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import verification_session as v
class SessionTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
 def file(self,name,value):p=self.base/name;p.write_text(json.dumps(value));return p,hashlib.sha256(p.read_bytes()).hexdigest()
 def test_single_parse_hashes_each_read_and_mutation_is_rejected(self):
  p,h=self.file('doc.json',{'items':[{'x':1}]})
  with v.validation_scope() as s:
   a=s.read_pinned(p,h);b=s.read_pinned(p,h);self.assertIs(a,b);self.assertIsInstance(a,dict);self.assertIsInstance(a['items'],list);self.assertEqual(a,{'items':[{'x':1}]});self.assertEqual(json.loads(json.dumps(a)),a)
   for action in (lambda:a.update(x=2),lambda:a['items'].append(2),lambda:a['items'][0].__setitem__('x',3)):
    with self.assertRaises(TypeError):action()
   changed=copy.deepcopy(a);changed['items'][0]['x']=9;self.assertEqual(a['items'][0]['x'],1)
   self.assertEqual(s.stats['JSON_decodes'],1);self.assertEqual(s.stats['hash_checks'],2)
 def test_same_path_changed_bytes_with_preserved_stat_is_not_trusted(self):
  p,h=self.file('doc.json',{'x':1})
  with v.validation_scope() as s:
   s.read_pinned(p,h);st=p.stat();p.write_text('{"x": 2}');import os;os.utime(p,ns=(st.st_atime_ns,st.st_mtime_ns))
   with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):s.read_pinned(p,h)
   new=hashlib.sha256(p.read_bytes()).hexdigest();self.assertEqual(s.read_pinned(p,new)['x'],2);self.assertEqual(s.stats['JSON_decodes'],2)
 def test_failed_JSON_and_failed_verification_not_cached(self):
  p=self.base/'bad.json';p.write_text('{');h=hashlib.sha256(p.read_bytes()).hexdigest();calls=[]
  with v.validation_scope() as s:
   for _ in range(2):
    with self.assertRaises(ValueError):s.read_pinned(p,h)
   def fail():calls.append(1);raise ValueError('bad evidence')
   for _ in range(2):
    with self.assertRaises(ValueError):s.memo('test',fail,(),{})
   self.assertEqual(s.stats['JSON_decodes'],2);self.assertEqual(len(calls),2);self.assertFalse(s.memos)
 def test_memo_tracks_transitive_dependencies_on_every_hit(self):
  p,h=self.file('root.json',{'x':1});child,ch=self.file('child.json',{'x':2});calls=[]
  with v.validation_scope() as s:
   root=s.read_pinned(p,h)
   def compute(arg):calls.append(1);return {'x':s.read_pinned(child,ch)['x']+arg['x']}
   self.assertEqual(s.memo('test',compute,(root,),{}),{'x':3});self.assertEqual(s.memo('test',compute,(root,),{}),{'x':3});self.assertEqual(len(calls),1)
   child.write_text('{"x":9}')
   with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):s.memo('test',compute,(root,),{})
   self.assertEqual(len(calls),1)
 def test_parameters_loaded_code_constants_and_revision_invalidate(self):
  p,h=self.file('root.json',{'x':1});calls=[];module=types.ModuleType('fake_validator');module.LABELS={'x':['a']}
  with v.validation_scope() as s:
   root=s.read_pinned(p,h)
   def compute(arg,flag=True):calls.append(1);return [arg['x'],flag]
   s.memo('test',compute,(root,),{'flag':True},code_token=v.code_signature([module]));s.memo('test',compute,(root,),{'flag':True},code_token=v.code_signature([module]));self.assertEqual(len(calls),1)
   s.memo('test',compute,(root,),{'flag':False},code_token=v.code_signature([module]));module.LABELS['x'].append('b');s.memo('test',compute,(root,),{'flag':True},code_token=v.code_signature([module]));s.revision='new';s.memo('test',compute,(root,),{'flag':True},code_token=v.code_signature([module]));self.assertEqual(len(calls),4)
 def test_preorder_intervals_and_classes_preserve_order_without_subtree_lists(self):
  p,h=self.file('tree.json',{'root':{'tag':'div','children':[{'tag':'span','attributes':{'class':'a'},'children':[{'tag':'b','attributes':{'class':'a'},'children':[]}]},{'tag':'i','attributes':{'class':'a'},'children':[]}]}})
  with v.validation_scope() as s:
   root=s.read_pinned(p,h)['root'];self.assertEqual([n['tag'] for n in s.walk_view(root)],['div','span','b','i']);sub=root['children'][0];self.assertEqual([n['tag'] for n in s.walk_view(sub)],['span','b']);self.assertEqual([n['tag'] for n in s.matching(root,'classes','a')],['span','b','i']);self.assertEqual(len(s.indexes),1);self.assertIsInstance(s.all_nodes(root),list)
   first=s.bytes
   for _ in range(20):list(s.walk_view(sub))
   self.assertEqual(s.bytes,first)
 def test_cap_and_plain_live_nodes_bypass_without_changing_result(self):
  p,h=self.file('doc.json',{'x':[1,2]})
  with v.validation_scope(max_bytes=0) as s:
   self.assertEqual(s.read_pinned(p,h),{'x':[1,2]});self.assertFalse(s.docs);self.assertIsNone(s.document_ref(s.read_pinned(p,h)));self.assertEqual(s.bytes,0);self.assertIsNone(s.walk_view({'tag':'div','children':[]}))
 def test_nested_hit_propagates_dependency_to_later_outer_hit(self):
  p,h=self.file('root.json',{'x':1});child,ch=self.file('child.json',{'x':2})
  with v.validation_scope() as s:
   root=s.read_pinned(p,h)
   def inner(a):return s.read_pinned(child,ch)['x']
   def outer(a):return s.memo('inner',inner,(a,),{})+1
   s.memo('inner',inner,(root,),{});self.assertEqual(s.memo('outer',outer,(root,),{}),3)
   child.write_text('{"x":3}')
   with self.assertRaisesRegex(ValueError,'pinned-evidence-changed'):s.memo('outer',outer,(root,),{})
 def test_require_complete_is_part_of_key(self):
  p,h=self.file('state.json',{'phase':'partial'});calls=[]
  with v.validation_scope() as s:
   state=s.read_pinned(p,h)
   def verify(state,*,require_complete=True):
    calls.append(require_complete)
    if require_complete:raise ValueError('not complete')
    return []
   self.assertEqual(s.memo('completed',verify,(state,),{'require_complete':False}),[])
   with self.assertRaisesRegex(ValueError,'not complete'):s.memo('completed',verify,(state,),{'require_complete':True})
   self.assertEqual(calls,[False,True])
 def test_iframe_tree_is_independent_and_order_is_exact(self):
  leaf=lambda tag:{'tag':tag,'attributes':{'class':'a'},'children':[]}
  inner={'tag':'main','children':[leaf('b')]}
  p,h=self.file('frame.json',{'root':{'tag':'div','children':[{'tag':'iframe','children':[],'public_frame_dom':{'root':inner}},leaf('i')]}})
  with v.validation_scope() as s:
   root=s.read_pinned(p,h)['root'];frame=root['children'][0]['public_frame_dom']['root']
   self.assertEqual([n['tag'] for n in s.walk_view(root)],['div','iframe','i'])
   self.assertEqual([n['tag'] for n in s.walk_view(frame)],['main','b']);self.assertEqual(len(s.indexes),2)
   self.assertEqual([n['tag'] for n in s.matching(frame,'classes','a')],['b'])
 def test_code_defaults_and_module_aliases_are_signed_dynamic_closure_rejected(self):
  module=types.ModuleType('fixed');exec('def verify(x=True):return x',module.__dict__)
  first=v.code_signature([module]);module.verify.__defaults__=(False,);self.assertNotEqual(first,v.code_signature([module]))
  module.child=types.ModuleType('one');first=v.code_signature([module]);module.child=types.ModuleType('two');self.assertNotEqual(first,v.code_signature([module]))
  captured=[]
  def dynamic():return captured
  module.dynamic=dynamic
  with self.assertRaisesRegex(TypeError,'dynamic-closure'):v.code_signature([module])
 def test_nested_scope_and_cross_session_cache_isolation(self):
  p,h=self.file('doc.json',{'x':1})
  with v.validation_scope() as outer:
   value=outer.read_pinned(p,h)
   with v.validation_scope() as inner:self.assertIs(outer,inner)
  self.assertIsNone(v.current())
  with v.validation_scope() as other:self.assertIsNone(other.document_ref(value));self.assertFalse(other.docs)
if __name__=='__main__':unittest.main()
