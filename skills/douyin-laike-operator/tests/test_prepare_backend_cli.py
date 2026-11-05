"""Prepare only emits commands; fixtures never contact a browser or the bridge."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
CLI=Path(__file__).resolve().parents[1]/'scripts/role_cli.py'
class PrepareDefaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.job=self.root/'job.json'
        self.job.write_text(json.dumps({'action':'acquire','work_order_id':'fixture','company':'fixture','groupid':'123','date_range':{'start':'2026-10-16','end':'2026-10-19'},'source_dir':str(self.root/'sources'),'workflow_path':str(self.root/'workflow.json')}))
    def prepare(self,*args):
        result=subprocess.run([sys.executable,str(CLI),'prepare','--work-order',str(self.job),*args],capture_output=True,text=True)
        return result.returncode,json.loads(result.stdout)
    def test_new_order_defaults_to_installed_local_bridge_and_explicit_tab(self):
        code,data=self.prepare('--tab-id','27');self.assertEqual(code,0);self.assertEqual(data['backend'],'local-dom-bridge')
        argv=data['tick_argv'];self.assertIn('bridge-workflow.py',argv[1]);self.assertEqual(argv[-2:],['--tab-id','27']);self.assertNotIn('bootstrap_code',data)
        self.assertFalse((self.root/'workflow.json').exists());self.assertFalse((self.root/'sources').exists())
    def test_default_missing_zero_or_negative_tab_fails_closed(self):
        for args in [(),('--tab-id','0'),('--tab-id','-1')]:
            with self.subTest(args=args):
                code,data=self.prepare(*args);self.assertEqual(code,2);self.assertEqual(data['error'],'explicit-tab-id-required')
        self.assertFalse((self.root/'workflow.json').exists())
    def test_legacy_prepare_requires_explicit_backend_and_stays_separate(self):
        code,data=self.prepare('--backend','codex-existing-extension');self.assertEqual(code,0);self.assertEqual(data['backend'],'codex-existing-extension');self.assertIn('bootstrap_code',data);self.assertNotIn('tick_argv',data)
if __name__=='__main__':unittest.main()
