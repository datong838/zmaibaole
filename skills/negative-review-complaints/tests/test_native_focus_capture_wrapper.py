"""Current-source pure/TEMP native focus regression; no UI, RPC or real capture."""
import sys,unittest,tempfile,copy,json
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts/review_capture_focus.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'skills/wecom-messenger/scripts')]
import review_capture_focus as m
import review_capture_tab as tab
import native_window_capture as nw
o=m.o
import capture_review_region as wrapper
class Wrapper(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name).resolve()
        self.source = o.immutable(self.d / 'source.json', {})
        self.manifest = {'job': {}, 'source': self.source, 'envelope': {}, 'profile': {}, 'page': {}, 'review_keys': ['k'], 'capture_key': 'capture-key-123'}
        self.ref = o.immutable(self.d / 'manifest.json', self.manifest)
        self.events = []
        patch.object(wrapper.overlay, 'derive', return_value=({}, {}, {}, '')).start()
        patch.object(wrapper.region, 'legacy_gate', side_effect=lambda *a: self.events.append('legacy')).start()
        patch.object(wrapper.overlay, 'no_capture_unknown', side_effect=lambda *a: self.events.append('unknown-guard')).start()
        patch.object(tab, 'ensure', side_effect=lambda *a, **k: self.events.append('activate-guard')).start()
        patch.object(wrapper.overlay, 'ensure', side_effect=lambda *a, **k: self.events.append('overlay-fresh')).start()
        patch.object(wrapper.region, 'capture', side_effect=lambda *a, **k: self.events.append('capture-fresh') or {'state': 'complete'}).start()
        self.addCleanup(patch.stopall)

    def call(self):
        return wrapper.capture(self.ref, self.d / 'out', pid=123, revision='complaint-region-v1', request=lambda c: self.fail('unexpected real request'))

    def test_new_capture_activation_then_original_overlay_then_fresh_capture(self):
        self.call()
        self.assertEqual(self.events, ['legacy', 'unknown-guard', 'activate-guard', 'overlay-fresh', 'capture-fresh'])
        self.assertEqual(o.doc(self.ref), self.manifest)

    def oldstate(self, state):
        directory = self.d / '.review-region-state'
        directory.mkdir()
        key = wrapper.rc.digest({'source': self.source['sha256'], 'review_keys': ['k']})
        operation = {'kind': 'normal-review-region-capture-v1', 'manifest': self.manifest, 'outdir': str(self.d / 'out'), 'pid': 123, 'revision': 'complaint-region-v1', 'replaces': None}
        wrapper.rc.atomic(directory / (key + '.json'), {'state': state, 'operation': operation})

    def test_completed_uses_original_capture_no_activation_or_overlay(self):
        self.oldstate('complete')
        self.call()
        self.assertEqual(self.events, ['capture-fresh'])

    def test_unknown_remains_original_capture_guard_no_activation(self):
        self.oldstate('unknown')
        with patch.object(wrapper.region, 'capture', side_effect=ValueError('original-unknown-no-replay')), self.assertRaisesRegex(ValueError, 'original-unknown'):
            self.call()
        self.assertFalse(self.events)
if __name__=="__main__":unittest.main()
