"""Formal pure-validator wiring and synthetic CLI/cold regressions. No live evidence/UI."""
import ast,contextlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;SCRIPTS=ROOT/'skills/violation-notifier/scripts'
sys.path[:0]=[str(SCRIPTS),str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import region_frame_capture as r
import registration_validation as validation
import verification_session

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
legacy=load('formal_region_legacy_fixture',ROOT/'skills/violation-notifier/tests/test_region_frame_capture.py')
class RegistrationWiringTests(unittest.TestCase):
 def test_each_public_pure_function_is_wrapped_and_business_entrypoints_are_not(self):
  tree=ast.parse((SCRIPTS/'region_frame_capture.py').read_text());functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
  for name in ('selection_ids','validate_frame','validate_attestation','validate_chain','inspect_registration'):
   n=functions[name];self.assertIsInstance(n.body[0],ast.With);self.assertEqual(n.body[0].items[0].context_expr.func.attr,'pure_scope');self.assertIn('_'+name+'_uncached',functions)
  for name in ('capture','approve_preview','assemble','main'):
   self.assertFalse(any(isinstance(n,ast.With) and any(isinstance(i.context_expr,ast.Call) and getattr(i.context_expr.func,'attr',None)=='pure_scope' for i in n.items) for n in ast.walk(functions[name])))
 def test_inspect_and_chain_route_through_pure_scope(self):
  entered=[]
  @contextlib.contextmanager
  def scope(module):entered.append(module);yield
  with patch.object(validation,'pure_scope',scope),patch.object(r,'_inspect_registration_uncached',return_value={'same':'output'}),patch.object(r,'_validate_chain_uncached',return_value={'chain':'same'}):
   self.assertEqual(r.inspect_registration('unused'),{'same':'output'});self.assertEqual(r.validate_chain({},source={},company='a',groupid='1',start='s',end_exclusive='e',notice_ids=[]),{'chain':'same'})
  self.assertEqual(entered,[r,r])
 def test_complete_helper_graph_contextmanager_methods_and_aliases_are_signed(self):
  # Run normal imports first, then sign helper itself including class contexts.
  import chrome_process_identity,screenshot_identity,prepare_records_profile,governance_capture,governance_detail
  graph=validation.loaded_graph(r);self.assertIn(validation,graph);self.assertIn(governance_detail.nav,graph)
  def token():return validation.reviewed_graph_token(graph,verification_session.code_signature,[])
  before=token();fn=validation.Session.pause.__wrapped__;old=fn.__code__
  try:
   fn.__code__=(lambda self:None).__code__;self.assertNotEqual(before,token())
  finally:fn.__code__=old
  alias=governance_detail.nav;self.assertIn(alias,graph)
  original=alias.scope.__code__
  try:
   alias.scope.__code__=(lambda job:None).__code__;self.assertNotEqual(before,token())
  finally:alias.scope.__code__=original
 def test_live_capture_and_all_writes_outside_scope(self):
  case=legacy.RegionFrames('test_exact_original_pixel_regions_cover_all_pages_and_never_select_raw_for_send');case.setUp();self.addCleanup(case.doCleanups)
  old_request=case.request;old_capture=case.native.capture;seen=[]
  def request(command):
   self.assertIsNone(validation._ACTIVE.get());seen.append(command['op']);return old_request(command)
  def capture(*args):self.assertIsNone(validation._ACTIVE.get());return old_capture(*args)
  case.request=request;case.native.capture=capture;value=case.frame(1,'anchor');self.assertEqual(value['state'],'complete');self.assertIn('viewport-proof',seen);self.assertIn('dom-region-proof',seen)
 def test_adapter_other_context_never_uses_active_session(self):
  import contextvars
  module=types.SimpleNamespace(sr=types.SimpleNamespace());module.sr.document=lambda ref:dict(ref);module._selection_prefix=lambda *args:None
  calls=[]
  def validate(image,m,*,source,allow_preview=False):calls.append(True);return {'uncached':True}
  module.validate_frame=validate;session=validation.Session(lambda:('fixed',))
  with validation.installed(module,session),session.transaction():
   other=contextvars.Context();out=other.run(lambda:module.validate_frame('unused',{},source={}))
   self.assertEqual(out,{'uncached':True});self.assertEqual(session.stats['misses'],0)
  self.assertEqual(len(calls),1)
 def test_public_and_private_signatures_match(self):
  import inspect
  for name in ('selection_ids','validate_frame','validate_attestation','validate_chain','inspect_registration'):
   self.assertEqual(inspect.signature(getattr(r,name)),inspect.signature(getattr(r,'_'+name+'_uncached')))
 def test_synthetic_chain_and_delivery_order_semantics(self):
  case=legacy.RegionFrames('test_exact_original_pixel_regions_cover_all_pages_and_never_select_raw_for_send');case.setUp();self.addCleanup(case.doCleanups)
  case.test_exact_original_pixel_regions_cover_all_pages_and_never_select_raw_for_send()
 def test_canonical_import_and_normal_script_main_produce_same_inspect(self):
  case=legacy.RegionFrames('test_exact_original_pixel_regions_cover_all_pages_and_never_select_raw_for_send');case.setUp();self.addCleanup(case.doCleanups)
  value=case.frame(1,'anchor');expected=r.inspect_registration(value['metadata'])
  self.assertIs(sys.modules[r.__name__],r)
  result=subprocess.run([sys.executable,str(SCRIPTS/'region_frame_capture.py'),'inspect','--metadata',value['metadata']],capture_output=True,text=True,timeout=60)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout),expected)
 def test_auth_identity_collision_cannot_authenticate_another_dict(self):
  import hashlib
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);refs=[]
   for number in (1,2):
    path=folder/('m'+str(number)+'.json');path.write_text(json.dumps({'capture_backend':'test','pinned_inputs':{},'number':number}));refs.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
   module=types.SimpleNamespace(sr=types.SimpleNamespace());module.sr.document=lambda ref:json.loads(Path(ref['path']).read_text());module._selection_prefix=lambda *args:None
   module.validate_frame=lambda image,m,**kw:{'number':m['number']}
   session=validation.Session(lambda:('fixed',))
   with patch.object(validation,'id',lambda obj:7,create=True),validation.installed(module,session),session.transaction():
    first=module.sr.document(refs[0]);second=module.sr.document(refs[1])
    self.assertEqual(module.validate_frame('unused',first,source={}),{'number':1})
    self.assertEqual(module.validate_frame('unused',second,source={}),{'number':2})
    self.assertEqual(session.stats['unpublished_computations'],1)
 def test_unconsumed_auth_registry_is_bounded_and_bypasses_safely(self):
  import hashlib
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'large.json';path.write_text(json.dumps({'capture_backend':'test','pinned_inputs':{},'text':'x'*5000}));ref={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
   module=types.SimpleNamespace(sr=types.SimpleNamespace());module.sr.document=lambda ref:json.loads(Path(ref['path']).read_text());module._selection_prefix=lambda *args:None;module.validate_frame=lambda *a,**kw:{'verified':True}
   session=validation.Session(lambda:('fixed',),max_bytes=1024)
   with validation.installed(module,session),session.transaction():
    for _ in range(5):doc=module.sr.document(ref)
    out=module.validate_frame('unused',doc,source={});self.assertEqual(out,{'verified':True});self.assertLessEqual(session.retained,1024);self.assertFalse(session.entries);self.assertEqual(session.stats['unpublished_computations'],1)
 def test_cold_normal_python_clean_pycache_png_validation(self):
  with tempfile.TemporaryDirectory() as temp:
   result=subprocess.run([sys.executable,'-I','-X','pycache_prefix='+temp,str(HERE/'fixtures/registration_validation_cold.py')],capture_output=True,text=True,timeout=60)
   self.assertEqual(result.returncode,0,result.stderr);data=json.loads(result.stdout);self.assertTrue(data['validated']);self.assertGreater(data['pyc_files'],0);self.assertFalse(data['writes_in_pure_scope']);self.assertFalse(data['input_or_live_actions'])
if __name__=='__main__':unittest.main()
