"""Exact immutable standard Path defaults; no business/UI/evidence access."""
import importlib.util,json,pathlib,subprocess,sys,tempfile,types,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import registration_validation as h,verification_session as v
class PathDefaults(unittest.TestCase):
 def module(self,path):
  module=types.ModuleType('standard_path_default_fixture');module.__file__=str(Path(__file__).resolve())
  module.path=path;exec('def f(value=path): return value',module.__dict__);return module
 def token(self,module):return h.reviewed_graph_token([module],v.code_signature,[])
 def test_exact_standard_path_classes_and_lexical_values(self):
  for value in (Path('/tmp/calendar.json'),pathlib.PurePosixPath('relative/../calendar.json'),pathlib.PureWindowsPath('C:/calendar.json')):
   module=self.module(value);before=self.token(module);self.assertEqual(before,self.token(module));module.f.__defaults__=(type(value)(str(value)+'-changed'),);self.assertNotEqual(before,self.token(module))
 def test_path_binding_replacement_same_value_rechecks(self):
  module=self.module(Path('/tmp/calendar.json'));before=self.token(module);module.f.__defaults__=(Path('/tmp/calendar.json'),);self.assertNotEqual(before,self.token(module))
 def test_subclass_arbitrary_pathlike_callable_and_mutable_rejected(self):
  class Custom(type(Path())):pass
  class Dangerous:
   def __fspath__(self):raise AssertionError('must not invoke arbitrary pathlike')
  class Callable:
   def __call__(self):return 1
  for value in (Custom('/tmp/calendar.json'),Dangerous(),Callable(),object(),{'unreviewed':object()}):
   with self.assertRaises((TypeError,ValueError)):self.token(self.module(value))
 def test_pathlib_export_binding_change_rejected(self):
  module=self.module(Path('/tmp/calendar.json'));old=pathlib.PosixPath
  try:
   pathlib.PosixPath=type('FakePath',(),{})
   with self.assertRaisesRegex(ValueError,'path-class-binding-changed'):self.token(module)
  finally:pathlib.PosixPath=old
 def test_complete_workflow_import_and_main_graph_smoke(self):
  outputs=[]
  for mode in ('imported','main'):
   result=subprocess.run([sys.executable,'-I','-B',str(HERE/'fixtures/registration_validation_workflow_graph.py'),mode],capture_output=True,text=True,timeout=30)
   self.assertEqual(result.returncode,0,result.stderr);value=json.loads(result.stdout);self.assertTrue(value['ok']);self.assertTrue(value['calendar_owner_in_graph']);self.assertFalse(value['business_called']);outputs.append(value)
  self.assertEqual(outputs[0]['source_sha_map'],outputs[1]['source_sha_map'])
if __name__=='__main__':unittest.main()
