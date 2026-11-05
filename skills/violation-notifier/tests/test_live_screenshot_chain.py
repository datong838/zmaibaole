"""Integration uses the actual v6 local producer with a fake public bridge only."""
import importlib.util,json
from pathlib import Path
from unittest.mock import patch
import unittest
ROOT=Path(__file__).resolve().parents[3]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
helper=load('violation_registration_fixture',ROOT/'skills/chrome-dom-export/tests/test_screenshot_registration.py')
w=load('violation_live_registration_workflow',ROOT/'skills/violation-notifier/scripts/workflow.py')
class LiveRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=helper.RegistrationTests('test_real_local_producer_output_validates_without_browser');self.fixture.setUp();self.addCleanup(self.fixture.doCleanups);f=self.fixture
        self.batch='2026-10-16_2026-10-20';self.root=f.root
        self.b={'start':'2026-10-16','end_exclusive':'2026-10-20','source':w.evidence(self.root,f.src),'records':[{'notice_id':'notice-1'}],'total':1,'send_jobs':{},'screenshots':[]}
        self.s={'version':1,'mode':'development','browser_backend':'local-dom-bridge','company':'fixture','groupid':'123','batches':{self.batch:self.b},'events':[]}
    def register(self):return w.add_screenshot(self.root,self.s,self.batch,self.fixture.out,self.fixture.registration)
    def test_matching_v6_output_registered_with_immutable_nested_evidence(self):
        self.register();entry=self.b['screenshots'][0];self.assertEqual(entry['public_dom_chain']['version'],'dom-only-20261021-11');self.assertEqual(len(entry['public_dom_chain']['references']),4)
        for ref in entry['public_dom_chain']['references']:w.verify(ref);self.assertEqual(Path(ref['path']).parent,self.root/'evidence')
        before=len(self.b['screenshots']);self.register();self.assertEqual(len(self.b['screenshots']),before)
    def test_handwritten_flags_never_create_screenshot_entry(self):
        f=self.fixture;meta={k:f.meta[k] for k in ('source','source_sha256','sha256','filters_visible','list_headers_visible','notice_ids')};path=self.root/'fake.json';w.atomic(path,meta)
        with self.assertRaisesRegex(ValueError,'pinned-source-required'):w.add_screenshot(self.root,self.s,self.batch,f.out,path)
        self.assertFalse(self.b['screenshots'])
    def test_proof_reference_changed_between_validation_and_snapshot_rejected(self):
        original=w.evidence;observation=self.fixture.obs
        def race(root,path,image=False):
            if Path(path).resolve()==observation.resolve():observation.write_text('{}')
            return original(root,path,image)
        with patch.object(w,'evidence',race),self.assertRaisesRegex(ValueError,'proof-changed-before-snapshot'):self.register()
        self.assertFalse(self.b['screenshots'])
    def test_registration_changed_between_validation_and_snapshot_rejected(self):
        original=w.evidence;metadata=self.fixture.registration
        def race(root,path,image=False):
            if Path(path).resolve()==metadata.resolve():metadata.write_text('{}')
            return original(root,path,image)
        with patch.object(w,'evidence',race),self.assertRaisesRegex(ValueError,'screenshot-changed-before-snapshot'):self.register()
        self.assertFalse(self.b['screenshots'])
    def test_send_validation_checks_nested_evidence_after_registration(self):
        self.register();entry=self.b['screenshots'][0];observation=Path(entry['public_dom_chain']['references'][1]['path']);observation.write_text('{}')
        text=self.root/'copy.txt';text.write_text('fixture only');self.b.update(copy=w.evidence(self.root,text),copy_evidence=w.evidence(self.root,text),artifacts={'source_sha256':self.b['source']['sha256'],'files':[]})
        with patch.object(w,'validate_artifact_coverage',lambda *_:None),self.assertRaisesRegex(ValueError,'evidence-changed'):w.send_orders(self.s,self.batch)
if __name__=='__main__':unittest.main()
