"""Synthetic callbacks/ctypes doubles only. No native OS APIs or live jobs."""
import copy,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
S=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(S))
import performance_trace as p,messenger as m
from native import Native,AXError
from test_sender import MockNative
import test_window_snapshot as window_fixture
import test_batch_attributes as bulk_fixture
spec=importlib.util.spec_from_file_location('sender_trace_baseline',Path(__file__).parent/'fixtures/before-stage-timing-messenger.py');baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline);baseline.POLICY=m.POLICY
class TraceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.out=self.root/'timing';self.state={'job':{'key':'sensitive-key','type':'file','text':'SECRET_MESSAGE'},'fingerprint':'a'*64,'phase':'stage','status':'running'}
 def enabled(self):return patch.dict(os.environ,{'WECOM_PERFORMANCE_DIR':str(self.out)})
 def logs(self):return [json.loads(x.read_bytes()) for x in self.out.glob('wecom-*.json')]
 def test_original_call_order_return_identity_and_phase_buckets(self):
  events=[];value=object()
  def fn(x):events.append(x);return value
  with self.enabled(),p.sender_scope(self.state):
   self.assertIs(p.call('ax.full',fn,1),value);self.state['phase']='file-confirm';self.assertIs(p.call('ax.chat',fn,2),value)
  self.assertEqual(events,[1,2]);rows=self.logs()[0]['operations'];self.assertEqual([(r['phase'],r['operation'],r['calls']) for r in rows],[('file-confirm','ax.chat',1),('stage','ax.full',1)]);self.assertTrue(all(r['elapsed_monotonic_ns']>=0 for r in rows))
 def test_original_exception_instance_not_swallowed_and_no_message_leak(self):
  error=RuntimeError('SECRET_MESSAGE account123');events=[]
  def fail():events.append('only-call');raise error
  with self.enabled(),p.sender_scope(self.state):
   with self.assertRaises(RuntimeError) as caught:p.call('ax.full',fail)
  self.assertIs(caught.exception,error);self.assertEqual(events,['only-call']);raw=next(self.out.glob('*.json')).read_text();self.assertNotIn('SECRET_MESSAGE',raw);self.assertNotIn('account123',raw);self.assertNotIn('sensitive-key',raw);self.assertEqual(self.logs()[0]['operations'][0]['exceptions'],1)
 def test_timer_and_recording_failure_do_not_change_call_or_exception(self):
  error=AXError('business error');seen=[]
  with self.enabled(),p.sender_scope(self.state):
   with patch.object(p.time,'perf_counter_ns',side_effect=RuntimeError('clock broken')):self.assertEqual(p.call('ax.full',lambda:seen.append('once') or 7),7)
   with patch.object(p.Recorder,'record',side_effect=RuntimeError('telemetry broken')):
    with self.assertRaises(AXError) as got:p.call('ax.chat',lambda:(_ for _ in ()).throw(error))
  self.assertIs(got.exception,error);self.assertEqual(seen,['once'])
 def test_trace_output_failure_cannot_replace_business_return(self):
  with self.enabled(),patch.object(p.Recorder,'flush',side_effect=OSError('disk failure')):
   with p.sender_scope(self.state):self.assertEqual(p.call('ax.full',lambda:42),42)
  self.assertIsNone(p.ACTIVE.get())
 def test_disabled_trace_does_not_sample_clock_or_write(self):
  with patch.dict(os.environ,{'WECOM_PERFORMANCE_DIR':''}),patch.object(p.time,'perf_counter_ns',side_effect=AssertionError('disabled clock')):
   with p.sender_scope(self.state):self.assertEqual(p.call('ax.full',lambda:9),9)
  self.assertFalse(self.out.exists())
 def test_actual_full_and_chat_methods_keep_snapshot_and_public_call_counts(self):
  fixture=window_fixture.WindowSnapshotTests();n,_,_,reads=fixture.fake();original=n.tree();count=len(reads);reads.clear()
  chat={'truncated':False,'tree':{'name':'SECRET_MESSAGE'},'read_scope':'current-chat-readonly'}
  with self.enabled(),p.sender_scope(self.state),patch('chat_snapshot.capture',return_value=chat) as capture:
   self.assertEqual(n.tree(),original);self.assertIs(n.chat_tree(),chat)
  self.assertEqual(len(reads),count);capture.assert_called_once_with(n);ops={r['operation']:r for r in self.logs()[0]['operations']};self.assertEqual(ops['ax.full']['calls'],1);self.assertEqual(ops['ax.chat']['calls'],1);self.assertEqual(ops['ax.rpc.copy_action_names']['calls'],6);self.assertEqual(ops['ax.full_attempt']['calls'],1)
 def test_real_batch_public_call_once_and_numeric_error_code_only(self):
  fixture=bulk_fixture.BulkTests();n=fixture.setup_native({100:'AXTextArea',101:'SECRET_MESSAGE'})
  with self.enabled(),p.sender_scope(self.state):self.assertEqual(n.node_attributes(1,['AXRole','AXValue'])['AXValue'],'SECRET_MESSAGE')
  self.assertEqual(fixture.calls,1);ops={r['operation']:r for r in self.logs()[0]['operations']};self.assertEqual(ops['ax.rpc.copy_multiple_attributes']['calls'],1);self.assertEqual(ops['ax.rpc.copy_multiple_attributes']['return_code_counts'],{'0':1});self.assertNotIn('SECRET_MESSAGE',next(self.out.glob('*.json')).read_text())
 def test_numeric_AX_failure_is_counted_without_hiding_original_error(self):
  fixture=bulk_fixture.BulkTests();n=fixture.setup_native({},error=-25204)
  with self.enabled(),p.sender_scope(self.state):
   with self.assertRaisesRegex(AXError,'batch-attribute-read-failed:-25204'):n.node_attributes(1,['AXRole','AXValue'])
  self.assertEqual(fixture.calls,1);ops={r['operation']:r for r in self.logs()[0]['operations']};self.assertEqual(ops['ax.rpc.copy_multiple_attributes']['return_code_counts'],{'-25204':1});self.assertEqual(ops['ax.node_attributes']['exceptions'],1)
 def test_real_serial_fallback_and_attribute_children_and_settable_counts(self):
  n=Native.__new__(Native);n.refs=[];order=[];n.string=lambda key:key;n.cf=SimpleNamespace(CFRelease=lambda name:None)
  def attr(e,key,out):order.append(key);out._obj.value=101;return 0
  def flag(e,key,out):order.append('settable:'+key);out._obj.value=True;return 0
  n.ax=SimpleNamespace(AXUIElementCopyAttributeValue=attr,AXUIElementIsAttributeSettable=flag);n.decode=lambda v:'AXTextArea'
  with self.enabled(),p.sender_scope(self.state):
   self.assertEqual(n.value(1,'AXChildren'),101);self.assertEqual(n.single_node_attributes(1,['AXRole','AXValue']),{'AXRole':'AXTextArea','AXValue':'AXTextArea'});self.assertTrue(n.scoped_settable(1,'AXValue'))
  self.assertEqual(order,['AXChildren','AXRole','AXValue','settable:AXValue']);ops={r['operation']:r for r in self.logs()[0]['operations']};self.assertEqual(ops['ax.rpc.attribute.AXChildren']['calls'],1);self.assertEqual(ops['ax.rpc.attribute.AXValue']['calls'],1);self.assertEqual(ops['ax.rpc.is_attribute_settable']['calls'],1)
 def test_advance_behavior_state_events_and_inputs_match_baseline(self):
  class Tracked(MockNative):
   def __init__(self):super().__init__();self.calls=[]
   @p.stage('ax.full')
   def tree(self):self.calls.append('tree');return super().tree()
   def set_text(self,*args):self.calls.append('set_text');return super().set_text(*args)
   def close(self):self.calls.append('close')
  newdir=self.root/'new';olddir=self.root/'old';a,_=m.prepare('same','group','测试群请忽略',text='SECRET_MESSAGE',directory=newdir);b,_=baseline.prepare('same','group','测试群请忽略',text='SECRET_MESSAGE',directory=olddir);n,o=Tracked(),Tracked()
  with self.enabled(),patch.object(m,'now',return_value='fixed'),patch.object(baseline,'now',return_value='fixed'):
   result=m.advance(a,lambda:n)
  with patch.object(baseline,'now',return_value='fixed'):old=baseline.advance(b,lambda:o)
  # Prepare's wall timestamp is not the timing instrumentation contract.
  result.pop('created_at');old.pop('created_at');self.assertEqual(result,old);self.assertEqual(n.calls,o.calls);self.assertEqual(n.keys,o.keys);self.assertEqual(result['phase'],'verify');self.assertEqual(len(self.logs()),1)
 def test_aggregate_multiple_advances_without_mixing_jobs(self):
  with self.enabled():
   for _ in range(2):
    with p.sender_scope(self.state):p.call('ax.full',lambda:None)
   self.state['fingerprint']='b'*64
   with p.sender_scope(self.state):p.call('ax.chat',lambda:None)
  out=p.summarize(self.out);self.assertEqual(sorted(j['advance_calls'] for j in out['jobs']),[1,2]);self.assertIn('excludes prepare',out['scope']);self.assertTrue(out['operation_durations_inclusive'])
 def test_unknown_return_does_not_replay_or_change_original_receipt(self):
  n,o=MockNative(),MockNative();n.fail_key=o.fail_key=True
  a,state=m.prepare('return-once','group','测试群请忽略',text='SECRET_MESSAGE',directory=self.root/'new-unknown');b,old=baseline.prepare('return-once','group','测试群请忽略',text='SECRET_MESSAGE',directory=self.root/'old-unknown')
  for path,doc in ((a,state),(b,old)):doc.update(phase='ready',pid=123);m.atomic(path,doc)
  n.draft=o.draft='SECRET_MESSAGE'
  with self.enabled(),patch.object(m,'now',return_value='fixed'):result=m.advance(a,lambda:n)
  with patch.object(baseline,'now',return_value='fixed'):original=baseline.advance(b,lambda:o)
  result.pop('created_at');original.pop('created_at');self.assertEqual(result,original);self.assertEqual(n.keys,o.keys);self.assertEqual(len(n.keys),1);self.assertEqual(result['status'],'unknown');self.assertEqual(result['phase'],'verify-sent')
 def test_rebased_exact_AXChildren_retry_keeps_baseline_result_and_budget(self):
  sp=importlib.util.spec_from_file_location('trace_current_native_baseline',Path(__file__).parent/'fixtures/before-stage-timing-native.py');old=importlib.util.module_from_spec(sp);sp.loader.exec_module(old)
  def subject(cls):
   n=cls.__new__(cls);calls=[];results=[{'truncated':True,'truncation_reason':'scoped-required-array-unavailable:AXChildren','node_count':230},{'truncated':False,'node_count':401}]
   def once(**kw):calls.append(kw);return results.pop(0)
   n._tree_once=once;return n,calls
  new,ncalls=subject(Native);prior,ocalls=subject(old.Native)
  with self.enabled(),p.sender_scope(self.state),patch('native.time.monotonic',return_value=10),patch('native.time.sleep'):
   actual=new.tree()
  with patch.object(old.time,'monotonic',return_value=10),patch.object(old.time,'sleep'):
   expected=prior.tree()
  self.assertEqual(actual,expected);self.assertEqual(ncalls,ocalls);self.assertEqual(len(ncalls),2);self.assertEqual(ncalls[1]['timeout'],55)
 def test_historical_timing_business_AST_is_identical_after_removing_timing(self):
  import ast
  class Strip(ast.NodeTransformer):
   def visit_Import(self,node):
    return None if any(a.name=='performance_trace' for a in node.names) else node
   def visit_FunctionDef(self,node):
    node=self.generic_visit(node);node.decorator_list=[d for d in node.decorator_list if not (isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and isinstance(d.func.value,ast.Name) and d.func.value.id=='performance')];return node
   def visit_With(self,node):
    node=self.generic_visit(node)
    if len(node.items)==1:
     c=node.items[0].context_expr
     if isinstance(c,ast.Call) and isinstance(c.func,ast.Attribute) and isinstance(c.func.value,ast.Name) and c.func.value.id=='performance' and c.func.attr=='sender_scope':return node.body
    return node
   def visit_Call(self,node):
    node=self.generic_visit(node)
    if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='performance' and node.func.attr in ('call','attribute_call'):return ast.copy_location(ast.Call(func=node.args[1],args=node.args[2:],keywords=node.keywords),node)
    return node
  archived=Path(__file__).parent/'fixtures'
  for name in ('native.py','messenger.py'):
   source=(archived/('before-stage-timing-'+name)).read_text();candidate=(archived/'structure-migrations'/('timing-'+name)).read_text();self.assertEqual(ast.dump(Strip().visit(ast.parse(candidate))),ast.dump(ast.parse(source)),name)
if __name__=='__main__':unittest.main()
