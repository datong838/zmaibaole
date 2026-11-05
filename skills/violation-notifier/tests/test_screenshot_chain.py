"""Additional live-chain registration with synthetic public DOM and no UI."""
import copy,importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module);return module
fixture=load('violation_frame_fixture',ROOT/'skills/chrome-dom-export/tests/test_frame_capture.py')
w=load('violation_frame_chain_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py')
class ChainWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.FrameTests('test_anchor_and_row_frames_keep_visibility_false_and_cover_all_pages');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);f=self.fixture;self.root=f.root;self.manifest=f.all_frames();self.path=self.root/'manifest.json';self.batch='2026-10-16_2026-10-20'
        self.b={'start':'2026-10-16','end_exclusive':'2026-10-20','source':w.evidence(self.root,f.source_path),'records':[{'notice_id':'notice-'+str(i)} for i in range(1,4)],'total':3,'send_jobs':{},'screenshots':[]}
        self.s={'version':1,'mode':'development','browser_backend':'local-dom-bridge','company':'fixture','groupid':'123','batches':{self.batch:self.b},'events':[]}
    def register(self):return w.add_screenshot_chain(self.root,self.s,self.batch,self.path)
    def ready(self):
        text=self.root/'copy.txt';text.write_text('fixture only');self.b.update(copy=w.evidence(self.root,text),copy_evidence=w.evidence(self.root,text),artifacts={'source_sha256':self.b['source']['sha256'],'files':[]})
    def test_registers_page_anchors_and_offscreen_date_row_frames_without_faking_true(self):
        self.register();chain=self.b['screenshot_chains'][0];self.assertEqual(len(chain['frames']),4);self.assertEqual(chain['notice_ids'],['notice-1','notice-2','notice-3'])
        for frame in chain['frames']:
            self.assertEqual(len(frame['references']),5)
            for ref in frame['references']:w.verify(ref)
            m=json.loads(Path(frame['metadata']['path']).read_text())
            if frame['frame_mode']=='rows':self.assertFalse(m['filters_visible']);self.assertFalse(m['list_headers_visible'])
        count=len(self.s['events']);self.register();self.assertEqual(len(self.b['screenshot_chains']),1);self.assertEqual(len(self.s['events']),count)
    def test_historical_viewport_chain_stays_registered_but_is_not_final_region_evidence(self):
        self.register();self.ready()
        with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'region-only-final-evidence-required'):w.send_orders(self.s,self.batch)
        self.assertEqual(len(self.b['screenshot_chains'][0]['frames']),4)
    def test_missing_page_anchor_is_not_registered(self):
        self.manifest['frames'].pop(2);w.atomic(self.path,self.manifest)
        with self.assertRaises(ValueError):self.register()
        self.assertFalse(self.b.get('screenshot_chains'));self.assertFalse(self.b['screenshots'])
    def test_registered_chain_cannot_change_or_bypass_fixture_send_guard(self):
        self.register();self.manifest['frames'].reverse();w.atomic(self.path,self.manifest)
        with self.assertRaisesRegex(ValueError,'chain-id-conflict'):self.register()
        self.s['mode']='fixture'
        with self.assertRaisesRegex(ValueError,'live-bridge-only'):self.register()
    def test_sender_detects_changed_nested_profile_evidence(self):
        self.register();self.ready();ref=self.b['screenshot_chains'][0]['frames'][0]['references'][2];Path(ref['path']).write_text('{}')
        with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'evidence-changed'):w.send_orders(self.s,self.batch)
if __name__=='__main__':unittest.main()
