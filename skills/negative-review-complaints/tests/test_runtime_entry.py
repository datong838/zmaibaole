import importlib.util,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('runtime_entry',Path(__file__).resolve().parents[1]/'scripts/runtime_entry.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Stop(Exception):pass
class RuntimeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.env=self.root/'skills/daily-comment-stats/.venv';self.exe=self.env/'bin/python';self.exe.parent.mkdir(parents=True);self.exe.write_text('#!/bin/sh\n');self.exe.chmod(0o755)
 def test_current_runtime_has_no_exec_or_ui(self):
  with patch.object(m.sys,'prefix',str(self.env)),patch.object(m.os,'execv') as call:m.ensure_runtime(self.root);call.assert_not_called()
 def test_wrong_runtime_execs_same_script_args_once(self):
  with patch.object(m.sys,'prefix','/other'),patch.object(m.sys,'argv',['/tmp/tool.py','--state','/tmp/a b.json']),patch.object(m.os,'execv',side_effect=Stop) as call:
   with self.assertRaises(Stop):m.ensure_runtime(self.root)
   call.assert_called_once_with(str(self.exe),[str(self.exe),str(Path('/tmp/tool.py').resolve()),'--state','/tmp/a b.json'])
 def test_missing_runtime_stops_without_fallback(self):
  self.exe.unlink()
  with patch.object(m.sys,'prefix','/other'),patch.object(m.os,'execv') as call:
   with self.assertRaisesRegex(RuntimeError,'runtime-missing'):m.ensure_runtime(self.root)
   call.assert_not_called()
if __name__=='__main__':unittest.main()
