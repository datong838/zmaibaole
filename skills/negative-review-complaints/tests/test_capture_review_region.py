"""Synthetic wrapper contracts. No bridge, native capture, or actual source use."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import capture_review_region as m
class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve();self.source=self.root/'source.json';self.source.write_text('{}');self.source_ref=m.overlay.ref(self.source);self.manifest={k:self.source_ref for k in ('job','source','envelope','profile','page')};self.manifest.update(review_keys=['gid:old'],capture_key='original-capture-key');self.mp=self.root/'manifest.json';self.mp.write_text(json.dumps(self.manifest));self.mr=m.overlay.ref(self.mp);self.events=[];self.pid=42;self.revision='region1';self.out=self.root/'out'
        self.state=self.root/'.review-region-state'/(m.rc.digest({'source':self.source_ref['sha256'],'review_keys':['gid:old']})+'.json')
        self.operation={'kind':'normal-review-region-capture-v1','manifest':copy.deepcopy(self.manifest),'outdir':str(self.out),'pid':42,'revision':'region1','replaces':None}
        self.patches=[patch.object(m.overlay,'derive'),patch.object(m.overlay,'ensure',side_effect=lambda *a,**k:self.events.append(('ensure',k))),patch.object(m.region,'legacy_gate'),patch.object(m.region,'capture',side_effect=self.original_capture)]
        for p in self.patches:p.start();self.addCleanup(p.stop)
    def original_capture(self,manifest,outdir,request,**kw):
        self.events.append(('fresh-capture',manifest));self.assertEqual(manifest,self.manifest)
        if self.state.exists():
            old=m.rc.load(self.state)
            if old['state'] not in ('complete','awaiting-visual-review'):raise ValueError('review-region-unknown-no-recapture')
        return {'state':'complete','image':{'sha256':'synthetic'},'image_scope':'derived-dom-review-region'}
    def run_capture(self,**kw):return m.capture(self.mr,self.out,pid=42,revision='region1',request=lambda command:self.fail('unexpected request'),**kw)
    def existing(self,state):self.state.parent.mkdir(exist_ok=True);self.state.write_text(json.dumps({'state':state,'operation':self.operation}))
    def test_new_capture_ensure_precedes_original_fresh_capture_and_manifest_unchanged(self):
        before=self.mp.read_bytes();self.run_capture();self.assertEqual([x[0] for x in self.events],['ensure','fresh-capture']);self.assertEqual(self.mp.read_bytes(),before);self.assertEqual(self.events[0][1]['adopt'],None)
    def test_complete_and_preview_reuse_without_ensure_or_new_request(self):
        for state in ('complete','awaiting-visual-review'):
            self.events.clear();self.existing(state);self.run_capture();self.assertEqual([x[0] for x in self.events],['fresh-capture'])
    def test_unknown_delegates_original_guard_without_ensure_or_input(self):
        self.existing('unknown')
        with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.run_capture()
        self.assertEqual([x[0] for x in self.events],['fresh-capture'])
    def test_existing_original_operation_cannot_be_changed(self):
        self.existing('complete');self.operation['revision']='changed';self.existing('complete')
        with self.assertRaisesRegex(ValueError,'original-operation'):self.run_capture()
        self.assertFalse(self.events)
    def test_other_unknown_capture_blocks_new_overlay_input(self):
        p=self.root/'.review-capture-state';p.mkdir();(p/'old.json').write_text('{"state":"unknown"}')
        with self.assertRaisesRegex(ValueError,'unresolved'):self.run_capture()
        self.assertFalse(self.events)
    def test_explicit_adopt_only_forwarded_for_new_capture(self):
        q={'path':'synthetic-adopt','sha256':'synthetic'};self.run_capture(adopt=q);self.assertEqual(self.events[0][1]['adopt'],q);self.events.clear();self.existing('complete')
        with self.assertRaisesRegex(ValueError,'only-new'):self.run_capture(adopt=q)
        self.assertFalse(self.events)
    def test_ensure_failure_never_enters_capture(self):
        m.overlay.ensure.side_effect=ValueError('overlay-original-events-unclosed-no-replay')
        with self.assertRaisesRegex(ValueError,'unclosed'):self.run_capture()
        m.region.capture.assert_not_called()
    def test_changed_manifest_during_ensure_stops_before_capture(self):
        m.overlay.ensure.side_effect=lambda *a,**k:self.mp.write_text('{}')
        with self.assertRaisesRegex(ValueError,'changed'):self.run_capture()
        m.region.capture.assert_not_called()
    def test_invalid_pid_or_revision_fails_before_ensure(self):
        for pid,revision in ((True,'r'),(0,'r'),(42,'../r')):
            with self.subTest(pid=pid,revision=revision),self.assertRaises(ValueError):m.capture(self.mr,self.out,pid=pid,revision=revision,request=lambda c:None)
        self.assertFalse(self.events)
if __name__=='__main__':unittest.main()
