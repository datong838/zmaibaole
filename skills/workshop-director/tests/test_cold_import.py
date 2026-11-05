"""Exercise the real director import without sibling paths from other tests."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


class ColdImportTests(unittest.TestCase):
    def run_isolated(self, body):
        prefix = 'import sys,types,json;sys.path.insert(0,' + repr(str(SCRIPTS)) + ');'
        return subprocess.run(
            [sys.executable, '-I', '-B', '-c', prefix + body],
            cwd='/', capture_output=True, text=True, timeout=15,
        )

    def test_director_imports_without_violation_path_and_restores_path(self):
        result = self.run_isolated(
            'before=list(sys.path);import director;'
            'assert sys.path==before;'
            'assert director.progress.records.verification.current() is None;'
            'print(json.dumps({"imported":True}))'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'imported': True})

    def test_wrong_preloaded_helper_origin_is_rejected(self):
        result = self.run_isolated(
            'fake=types.ModuleType("verification_session");'
            'fake.__file__="/wrong/verification_session.py";'
            'sys.modules["verification_session"]=fake;import director'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('workshop-verification-module-origin-conflict', result.stderr)


if __name__ == '__main__':
    unittest.main()
