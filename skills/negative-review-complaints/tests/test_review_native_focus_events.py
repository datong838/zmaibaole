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
class Focus(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name).resolve()
        self.source = o.immutable(self.d / 'source.json', {})
        self.manifest = {'source': self.source, 'review_keys': ['k']}
        self.ref = o.immutable(self.d / 'manifest.json', self.manifest)
        self.act = o.immutable(self.d / 'activation.json', {'state': 'complete'})
        self.binding = {'manifest': self.ref, 'activation': self.act, 'pid': 123, 'source': self.source, 'scope': {'tabId': 2, 'windowId': 3, 'groupid': '4'}, 'url': 'https://life.douyin.com/p/review?groupid=4', 'identity': {}}
        self.front = 999
        self.focused = False
        self.active = True
        self.count = []
        self.fail = False
        self.derive = patch.object(m, 'derive', return_value=self.binding).start()
        patch.object(tab.overlay, 'no_capture_unknown').start()
        self.addCleanup(patch.stopall)

    def tabs(self):
        return [{'windowId': 3, 'focused': self.focused, 'tabs': [{'tabId': 2, 'windowId': 3, 'active': self.active, 'url': self.binding['url'], 'allowed': True}]}]

    def request(self, c):
        self.count.append(c)
        if c['op'] == 'activate':
            if self.fail:
                raise TimeoutError('reply lost')
            self.front = 123
            self.focused = True
            return {'ok': True, 'result': {**self.binding['scope'], 'url': self.binding['url'], 'active': True, 'windowFocused': True}}
        return {'ok': True, 'result': self.tabs(), 'error': None}

    def reader(self, pid):
        return {'application': {'pid': 123, 'bundle': 'com.google.Chrome', 'terminated': False}, 'frontmost_pid': self.front}

    def runensure(self, **kw):
        return m.ensure(self.ref, activation_ref=self.act, pid=123, request=self.request, reader=self.reader, **kw)

    def path(self):
        return self.d / '.review-capture-focus' / (tab.overlay.rc.digest({'source': self.source['sha256'], 'review_keys': ['k']}) + '.json')

    def presses(self):
        return sum((c['op'] == 'activate' for c in self.count))

    def test_ready_no_input_original_activation_unchanged(self):
        old = o.raw(self.act)
        self.front = 123
        self.focused = True
        self.assertTrue(self.runensure()['ready'])
        self.assertEqual(self.presses(), 0)
        self.assertEqual(o.raw(self.act), old)

    def test_external_focus_once_then_later_loss_new_ordinal(self):
        old = o.raw(self.act)
        self.assertTrue(self.runensure()['input_dispatched'])
        self.runensure()
        self.assertEqual(self.presses(), 1)
        self.front = 999
        self.focused = False
        self.assertEqual(self.runensure()['focus_event'], 2)
        self.assertEqual(self.presses(), 2)
        s = o.doc(o.ref(self.path()))
        self.assertEqual([e['number'] for e in s['events']], [1, 2])
        self.assertEqual(o.raw(self.act), old)

    def test_unknown_cannot_reissue_even_new_call(self):
        self.fail = True
        with self.assertRaises(TimeoutError):
            self.runensure()
        self.fail = False
        with self.assertRaisesRegex(ValueError, 'unknown-readonly-no-replay'):
            self.runensure()
        self.assertEqual(self.presses(), 1)
        self.front = 123
        self.focused = True
        self.assertFalse(self.runensure()['input_dispatched'])
        self.assertEqual(self.presses(), 1)
        self.assertEqual(o.doc(o.ref(self.path()))['events'][0]['calls'][0]['state'], 'confirmed')

    def test_interruption_before_once_leaves_preflight_reusable(self):
        with patch.object(m.Focus, 'once', side_effect=RuntimeError('before-once')), self.assertRaisesRegex(RuntimeError, 'before-once'):
            self.runensure()
        s = o.doc(o.ref(self.path()))
        self.assertEqual(s['events'][0]['state'], 'preflight')
        self.assertEqual(s['events'][0]['calls'], [])
        self.runensure()
        self.assertEqual(self.presses(), 1)

    def test_crash_after_confirmed_call_before_postread_reconciles_only(self):
        original = self.reader

        def read(pid):
            if self.presses():
                raise RuntimeError('post-read interrupted')
            return original(pid)
        with patch.object(self, 'reader', side_effect=read), self.assertRaisesRegex(RuntimeError, 'post-read interrupted'):
            self.runensure()
        self.assertEqual(self.presses(), 1)
        self.runensure()
        self.assertEqual(self.presses(), 1)

    def test_wrong_pid_bundle_route_window_or_tab_not_active_zero_input(self):
        for kind in ('bundle', 'pid', 'url', 'window', 'inactive'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as t:
                self.front = 999
                self.focused = False
                self.active = True
                if kind == 'bundle':
                    p = patch.object(self, 'reader', return_value={'application': {'pid': 123, 'bundle': 'other', 'terminated': False}, 'frontmost_pid': 999})
                elif kind == 'pid':
                    p = patch.object(self, 'reader', return_value={'application': {'pid': 124, 'bundle': 'com.google.Chrome', 'terminated': False}, 'frontmost_pid': 999})
                else:
                    tabs = self.tabs()
                    if kind == 'url':
                        tabs[0]['tabs'][0]['url'] += '&other=1'
                    elif kind == 'window':
                        tabs[0]['windowId'] = 4
                    else:
                        tabs[0]['tabs'][0]['active'] = False
                    p = patch.object(self, 'tabs', return_value=tabs)
                with p, self.assertRaises(ValueError):
                    self.runensure()
        self.assertEqual(self.presses(), 0)

    def test_native_chrome_frontmost_but_window_unfocused_is_ambiguous(self):
        self.front = 123
        with self.assertRaisesRegex(ValueError, 'not-proven-external-change'):
            self.runensure()
        self.assertEqual(self.presses(), 0)

    def test_readonly_cannot_start_event(self):
        with self.assertRaisesRegex(ValueError, 'readonly-effect-not-observed'):
            self.runensure(readonly=True)
        self.assertEqual(self.presses(), 0)

    def test_unknown_without_call_and_tampered_before_ref_rejected(self):
        with patch.object(m.Focus, 'once', side_effect=RuntimeError('before-once')), self.assertRaises(RuntimeError):
            self.runensure()
        s = o.doc(o.ref(self.path()))
        s['events'][0]['state'] = 'unknown'
        tab.overlay.rc.atomic(self.path(), s)
        with self.assertRaisesRegex(ValueError, 'unknown-without-original-intent'):
            self.runensure()
        self.assertEqual(self.presses(), 0)
class ZeroActivation(unittest.TestCase):

    def test_existing_complete_zero_call_activation_is_valid_and_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t).resolve()
            source = o.immutable(d / 'source.json', {})
            manifest = {'source': source, 'review_keys': ['k']}
            ref = o.immutable(d / 'manifest.json', manifest)
            base = {'manifest': ref, 'source': source, 'scope': {'tabId': 2, 'windowId': 3, 'groupid': '4'}, 'url': 'https://life.douyin.com/p/review?groupid=4', 'identity': {}, 'original_record_tab': {}}
            directory = d / '.review-tab-activation'
            directory.mkdir()
            key = tab.overlay.rc.digest({'source': source['sha256'], 'review_keys': ['k']})
            path = directory / (key + '.json')
            tabs = [{'windowId': 3, 'focused': True, 'tabs': [{'tabId': 2, 'windowId': 3, 'active': True, 'url': base['url'], 'allowed': True}]}]
            raw = o.immutable(d / 'tabs.json', {'command': {'op': 'tabs'}, 'response': {'ok': True, 'result': tabs}})
            act = o.immutable(path, {'kind': 'review-capture-tab-activation-v1', 'state': 'complete', 'phase': 'frames', 'revision': 0, 'binding': base, 'calls': [], 'reads': [raw]})
            old = o.raw(act)
            with patch.object(tab, 'derive', return_value=base), patch.object(tab.overlay, 'no_capture_unknown'):
                binding = m.derive(ref, act, 123)
                self.assertEqual(binding['activation'], act)
                with patch.object(m, 'ensure', return_value={'ready': True}) as ensure:
                    self.assertTrue(tab.ensure(ref, pid=123, request=lambda c: self.fail('must not re-read original activation'))['ready'])
                    ensure.assert_called_once()
            self.assertEqual(o.raw(act), old)
if __name__=="__main__":unittest.main()
