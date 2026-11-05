"""Synthetic public CF/AX RPCs only; no OS framework load or UI inputs."""
import ast,copy,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).resolve().parents[3];S=R/'skills/wecom-messenger/scripts';sys.path[:0]=[str(S),str(Path(__file__).resolve().parent)]
FIXTURES=Path(__file__).resolve().parent/'fixtures/sender-capabilities'
import native as nmod,messenger as m
import ui
from test_sender import fixture,MockNative
old=types.ModuleType('native_before');exec(compile((FIXTURES/'native.py.before').read_text(),'native.py.before','exec'),old.__dict__)
FIELDS=['AXRole','AXTitle','AXDescription','AXValue','AXIdentifier','AXRoleDescription','AXSubrole','AXPlaceholderValue','AXHelp','AXEnabled','AXSelected','AXURL','AXFilename']
class Tests(unittest.TestCase):
 def fake(self,module=nmod,scope=None):
  n=object.__new__(module.Native);n.root=1;n.pid=123;n.refs=[]
  if scope is not None:n.capability_scope=scope
  root=fixture()['tree'];root['children'].append({'role':'AXDialog','AXTitle':'modal','children':[{'role':'AXComboBox','AXValue':'choice','children':[]}]})
  data={1:root};children={};idx=1
  def assign(node,e):
   nonlocal idx
   children[e]=[]
   for child in node['children']:
    idx+=1;ce=idx;data[ce]=child;children[e].append(ce);assign(child,ce)
  assign(root,1);windows=children[1];counts={'actions':0,'settable':[],'attributes':[],'arrays':[]};fail={}
  def attrs(e,keys):
   counts['attributes'].append((e,list(keys)))
   if e==fail.get('attribute'):raise module.AXError('batch-input-value-unreadable')
   return {k:(data[e]['role'] if k=='AXRole' else data[e].get(k)) for k in keys}
  def action(e,out):counts['actions']+=1;out._obj.value=900;return 0
  def settable(e,key,out):
   counts['settable'].append((e,key))
   if key==fail.get('settable'):return -25204
   out._obj.value=True;return 0
  def array(e,key,required=False):
   counts['arrays'].append((e,key,required))
   if e==fail.get('children') and key=='AXChildren':raise module.AXError('scoped-required-array-unavailable:AXChildren')
   if key=='AXWindows':return windows
   return children[e]
  n.node_attributes=attrs;n.get=lambda e,k:data[e]['role'] if k=='AXRole' else data[e].get(k);n.scoped_array=array;n.same_element=lambda a,b:a==b;n.string=lambda key:key;n.decode=lambda x:'AXPress';n.ax=types.SimpleNamespace(AXUIElementCopyActionNames=action,AXUIElementIsAttributeSettable=settable);n.cf=types.SimpleNamespace(CFArrayGetCount=lambda p:1,CFArrayGetValueAtIndex=lambda p,i:901,CFRelease=lambda p:None)
  return n,data,counts,fail
 def cleaned(self,s):
  s=copy.deepcopy(s);s.pop('capability_scope',None)
  for row in ui.nodes(s['tree']):
   row.pop('actions',None)
   keys=['AXValue'] if row['role'] in ('AXTextArea','AXTextField') else ['AXSelected'] if row['role']=='AXRow' else []
   values=[k for k in row.get('settable',[]) if k in keys];row.pop('settable',None)
   if values:row['settable']=values
  return s
 def test_default_full_exact_baseline_and_explicit_full(self):
  a,_,ac,_=self.fake(old);b,_,bc,_=self.fake();c,_,cc,_=self.fake(scope='full');expected=a.tree();self.assertEqual(expected,b.tree());self.assertEqual(expected,c.tree());self.assertEqual(ac,bc);self.assertEqual(ac,cc);self.assertNotIn('capability_scope',expected)
 def test_sender_all_fields_paths_windows_and_required_rpc_only(self):
  a,data,ac,_=self.fake(old);b,_,bc,_=self.fake(scope='sender-required');prior=a.tree();new=b.tree();self.assertEqual(self.cleaned(prior),self.cleaned(new));self.assertEqual(new['capability_scope'],'sender-required');self.assertEqual(new['node_count'],prior['node_count']);self.assertEqual(a.by_path,b.by_path);self.assertEqual(ac['arrays'],bc['arrays']);self.assertEqual(ac['attributes'],bc['attributes']);self.assertTrue(all(keys==FIELDS for _,keys in bc['attributes']));self.assertEqual(bc['actions'],0);self.assertEqual(ac['actions'],new['node_count']);self.assertEqual([x['role'] for x in new['tree']['children']],['AXWindow','AXDialog'])
  expected=[(e,k) for e,d in data.items() for k in (['AXValue'] if d['role'] in ('AXTextArea','AXTextField') else ['AXSelected'] if d['role']=='AXRow' else [])];self.assertCountEqual(bc['settable'],expected);self.assertFalse(any('actions' in x for x in ui.nodes(new['tree'])))
 def test_ui_header_search_composer_and_recent_row_guards_still_work(self):
  n,_,_,_=self.fake(scope='sender-required');ctx=ui.context(n.tree());ui.verify(ctx,{'target':'测试群请忽略','kind':'group'});self.assertIn('AXValue',ctx['composer']['settable']);self.assertIn('AXValue',ui.search_field(ctx)['settable']);self.assertIn('AXSelected',ui.recent_row(ctx,'测试群请忽略')['settable'])
 def test_required_settable_failure_is_not_assumed_true(self):
  n,_,_,fault=self.fake(scope='sender-required');fault['settable']='AXValue';s=n.tree()
  with self.assertRaisesRegex(ui.UIError,'composer-ambiguous'):ui.context(s)
 def test_attribute_failure_and_children_failures_remain_truncated(self):
  for key in ('attribute','children'):
   a,_,_,af=self.fake(old);b,_,_,bf=self.fake(scope='sender-required');af[key]=bf[key]=3
   with patch.object(nmod.time,'sleep'),patch.object(old.time,'sleep'):left=a.tree();right=b.tree()
   self.assertTrue(right['truncated']);self.assertEqual(self.cleaned(left),self.cleaned(right))
 def test_node_depth_deadline_and_unexpected_scope(self):
  for args in ({'max_nodes':2},{'max_depth':1},{'timeout':-1}):
   a,_,_,_=self.fake(old);b,_,_,_=self.fake(scope='sender-required');self.assertEqual(self.cleaned(a.tree(**args)),self.cleaned(b.tree(**args)))
  n,_,_,_=self.fake(scope='unknown')
  with self.assertRaisesRegex(nmod.AXError,'capability-scope-invalid'):n.tree()
  with self.assertRaisesRegex(nmod.AXError,'capability-scope-invalid'):nmod.Native(capability_scope='unknown')
 def test_production_advance_opts_in_but_mock_factory_unchanged(self):
  calls=[]
  class NativeFake(MockNative):
   def __init__(self,pid=None,**kw):super().__init__();calls.append((pid,kw))
  with tempfile.TemporaryDirectory() as t:
   p,_=m.prepare('native-select','group','测试群请忽略',text='synthetic',directory=Path(t))
   with patch.object(m,'Native',NativeFake):m.advance(p,native_factory=NativeFake)
   self.assertEqual(calls,[(None,{'capability_scope':'sender-required'})]);p,_=m.prepare('mock-unchanged','group','测试群请忽略',text='synthetic',directory=Path(t));mock=MockNative();m.advance(p,lambda:mock);self.assertEqual(len(calls),1)
 def test_only_reviewed_functions_changed_and_recovery_constructor_full(self):
  def functions(text):
   tree=ast.parse(text);return {x.name:ast.dump(x) for x in ast.walk(tree) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
  for name,allowed in [('native.py',{'__init__','tree','_tree_once','walk'}),('messenger.py',{'advance'})]:
   a=functions((FIXTURES/(name+'.before')).read_text());b=functions((FIXTURES.parent/'structure-migrations'/('capabilities-'+name)).read_text());self.assertEqual(set(a),set(b));self.assertLessEqual({k for k in a if a[k]!=b[k]},allowed)
  src=ast.parse((S/'messenger.py').read_text());fn=next(x for x in src.body if isinstance(x,ast.FunctionDef) and x.name=='resume_before_send');calls=[x for x in ast.walk(fn) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='Native'];self.assertEqual(len(calls),1);self.assertEqual(calls[0].keywords,[])
if __name__=='__main__':unittest.main()
