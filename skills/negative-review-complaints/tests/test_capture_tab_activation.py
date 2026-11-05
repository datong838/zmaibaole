"""Portable pure/TEMP regression. Imports installed project sources; no business/UI calls."""
import sys,ast,copy,importlib.util,unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_capture.py').is_file() and (p/'packages/workshop-director/workshop_director/timing_worker.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'packages/workshop-director')]
import review_capture_tab as m
o=m.o
import capture_review_region as wrapper
class Activation(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.d = Path(self.tmp.name).resolve()
        source = o.immutable(self.d / 'source.json', {})
        self.manifest = o.immutable(self.d / 'frames/manifest.json', {'source': source, 'review_keys': ['key']})
        self.binding = {'manifest': self.manifest, 'source': source, 'scope': {'tabId': 10, 'windowId': 20, 'groupid': '30'}, 'url': 'https://life.douyin.com/p/life_comment/management?groupid=30', 'original_record_tab': {'tabId': 11, 'windowId': 20, 'url': 'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=30'}}
        patch.object(m, 'derive', return_value=self.binding).start()
        self.addCleanup(patch.stopall)
        self.commands = []

    def tabs(self, active=False):
        return [{'windowId': 20, 'focused': True, 'tabs': [{'tabId': 10, 'windowId': 20, 'url': self.binding['url'], 'allowed': True, 'active': active}, {**self.binding['original_record_tab'], 'allowed': True, 'active': not active}]}]

    def state(self):
        return o.doc(o.ref(next((self.d / '.review-tab-activation').glob('*.json'))))

    def request(self, command):
        self.commands.append(command)
        if command['op'] == 'activate':
            return {'ok': True, 'result': {'tabId': 10, 'windowId': 20, 'url': self.binding['url']}}
        return {'ok': True, 'result': self.tabs(any((c['op'] == 'activate' for c in self.commands)))}

    def test_active_no_activate(self):
        r = m.ensure(self.manifest, request=lambda c: {'ok': True, 'result': self.tabs(True)})
        self.assertFalse(r['activation_dispatched_this_call'])
        self.assertFalse(self.state()['calls'])

    def test_inactive_once_then_fresh_active(self):
        r = m.ensure(self.manifest, request=self.request)
        self.assertTrue(r['activation_dispatched_this_call'])
        self.assertEqual([c['op'] for c in self.commands], ['tabs', 'activate', 'tabs'])
        self.assertEqual(self.state()['calls'][0]['state'], 'confirmed')
        self.assertEqual(self.state()['state'], 'complete')

    def test_repeat_complete_no_reactivate(self):
        m.ensure(self.manifest, request=self.request)
        r = m.ensure(self.manifest, request=self.request)
        self.assertFalse(r['activation_dispatched_this_call'])
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)

    def test_intent_persisted_before_dispatch(self):
        original = self.request

        def request(c):
            if c['op'] == 'activate':
                self.assertEqual(self.state()['calls'][0]['state'], 'unknown')
                self.assertEqual(self.state()['calls'][0]['command'], c)
            return original(c)
        m.ensure(self.manifest, request=request)

    def test_transport_unknown_never_replays_input(self):

        def request(c):
            self.commands.append(c)
            if c['op'] == 'activate':
                raise TimeoutError('synthetic')
            return {'ok': True, 'result': self.tabs(False)}
        with self.assertRaises(TimeoutError):
            m.ensure(self.manifest, request=request)
        with self.assertRaisesRegex(ValueError, 'unknown-no-replay'):
            m.ensure(self.manifest, request=request)
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)
        self.assertEqual(self.state()['calls'][0]['state'], 'unknown')

    def test_unknown_effect_readonly_reconciled_no_activate(self):

        def request(c):
            self.commands.append(c)
            if c['op'] == 'activate':
                raise TimeoutError('lost reply')
            return {'ok': True, 'result': self.tabs(False)}
        with self.assertRaises(TimeoutError):
            m.ensure(self.manifest, request=request)
        reads = []
        r = m.ensure(self.manifest, readonly=True, request=lambda c: reads.append(c) or {'ok': True, 'result': self.tabs(True)})
        self.assertFalse(r['activation_dispatched_this_call'])
        self.assertEqual(reads, [{'op': 'tabs'}])
        self.assertTrue(self.state()['calls'][0]['result']['observed'])

    def test_readonly_inactive_never_activates(self):
        with self.assertRaisesRegex(ValueError, 'effect-not-observed'):
            m.ensure(self.manifest, readonly=True, request=lambda c: {'ok': True, 'result': self.tabs(False)})
        self.assertFalse(self.state()['calls'])

    def test_target_zero_or_two_rejected(self):
        for count in (0, 2):
            tabs = self.tabs()
            target = tabs[0]['tabs'][0]
            tabs[0]['tabs'] = [tabs[0]['tabs'][1]] + [copy.deepcopy(target) for _ in range(count)]
            with self.assertRaisesRegex(ValueError, 'target-not-unique'):
                m.classify(tabs, self.binding)

    def test_wrong_sibling_or_cross_window_or_url_rejected(self):
        for change in ('sibling', 'window', 'url', 'allowed'):
            tabs = self.tabs()
            if change == 'sibling':
                tabs[0]['tabs'][1]['tabId'] = 99
            if change == 'window':
                tabs[0]['windowId'] = 99
            if change == 'url':
                tabs[0]['tabs'][0]['url'] += '&unreviewed=1'
            if change == 'allowed':
                tabs[0]['tabs'][0]['allowed'] = False
            with self.assertRaises(ValueError):
                m.classify(tabs, self.binding)

    def test_zero_two_active_or_other_focused_window_rejected(self):
        for change in ('zero', 'two', 'focus'):
            tabs = self.tabs()
            if change == 'zero':
                tabs[0]['tabs'][1]['active'] = False
            if change == 'two':
                tabs[0]['tabs'][0]['active'] = True
            if change == 'focus':
                tabs.append({'windowId': 99, 'focused': True, 'tabs': []})
            with self.assertRaises(ValueError):
                m.classify(tabs, self.binding)

    def test_after_effect_unverified_stops_no_second_activate(self):

        def request(c):
            self.commands.append(c)
            return {'ok': True, 'result': {'tabId': 10, 'windowId': 20, 'url': self.binding['url']} if c['op'] == 'activate' else self.tabs(False)}
        with self.assertRaisesRegex(ValueError, 'effect-unverified'):
            m.ensure(self.manifest, request=request)
        with self.assertRaisesRegex(ValueError, 'unknown-no-replay'):
            m.ensure(self.manifest, request=request)
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)

    def test_original_binding_change_rejected_before_request(self):
        m.ensure(self.manifest, request=lambda c: {'ok': True, 'result': self.tabs(True)})
        changed = copy.deepcopy(self.binding)
        changed['url'] += '&x=1'
        with patch.object(m, 'derive', return_value=changed), self.assertRaisesRegex(ValueError, 'original-binding'):
            m.ensure(self.manifest, request=lambda c: self.fail('must not request'))

    def test_source_key_cannot_bypass_unknown_with_other_review(self):

        def request(c):
            if c['op'] == 'activate':
                raise TimeoutError('lost')
            return {'ok': True, 'result': self.tabs(False)}
        with self.assertRaises(TimeoutError):
            m.ensure(self.manifest, request=request)
        other = o.immutable(self.d / 'frames/other.json', {'source': o.doc(self.manifest)['source'], 'review_keys': ['other']})
        with self.assertRaisesRegex(ValueError, 'other-unknown'):
            m.ensure(other, request=lambda c: self.fail('must not request'))

    def test_unfocused_original_record_window_one_activate_then_fresh(self):

        def request(c):
            self.commands.append(c)
            if c['op'] == 'activate':
                return {'ok': True, 'result': {'tabId': 10, 'windowId': 20, 'url': self.binding['url']}}
            did = any((x['op'] == 'activate' for x in self.commands))
            tabs = self.tabs(did)
            tabs[0]['focused'] = did
            return {'ok': True, 'result': tabs}
        result = m.ensure(self.manifest, request=request)
        self.assertTrue(result['activation_dispatched_this_call'])
        self.assertEqual([c['op'] for c in self.commands], ['tabs', 'activate', 'tabs'])

    def test_unfocused_target_already_active_still_one_activate_to_focus(self):

        def request(c):
            self.commands.append(c)
            if c['op'] == 'activate':
                return {'ok': True, 'result': {'tabId': 10, 'windowId': 20, 'url': self.binding['url']}}
            tabs = self.tabs(True)
            tabs[0]['focused'] = any((x['op'] == 'activate' for x in self.commands))
            if not tabs[0]['focused']:
                tabs.append({'windowId': 99, 'focused': True, 'tabs': [{'tabId': 88, 'active': True}]})
            return {'ok': True, 'result': tabs}
        m.ensure(self.manifest, request=request)
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)

    def test_unknown_unfocused_target_or_record_never_reactivates(self):

        def fail(c):
            self.commands.append(c)
            if c['op'] == 'activate':
                raise TimeoutError('lost')
            return {'ok': True, 'result': self.tabs(False)}
        with self.assertRaises(TimeoutError):
            m.ensure(self.manifest, request=fail)
        for active in (False, True):
            tabs = self.tabs(active)
            tabs[0]['focused'] = False
            with self.assertRaisesRegex(ValueError, 'unknown-no-replay'):
                m.ensure(self.manifest, request=lambda c: {'ok': True, 'result': tabs})
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)

    def test_focus_metadata_missing_and_other_window_active_ambiguity_rejected(self):
        tabs = self.tabs(True)
        tabs[0].pop('focused')
        with self.assertRaisesRegex(ValueError, 'focus-unknown'):
            m.classify(tabs, self.binding)
        tabs = self.tabs(True)
        tabs.append({'windowId': 99, 'focused': False, 'tabs': [{'active': True}, {'active': True}]})
        with self.assertRaisesRegex(ValueError, 'active-not-unique'):
            m.classify(tabs, self.binding)

    def test_unknown_missing_original_intent_does_not_issue_input(self):
        m.ensure(self.manifest, request=lambda c: {'ok': True, 'result': self.tabs(True)})
        path = next((self.d / '.review-tab-activation').glob('*.json'))
        state = self.state()
        state['state'] = 'unknown'
        m.overlay.rc.atomic(path, state)
        with self.assertRaisesRegex(ValueError, 'unknown-without-original-intent'):
            m.ensure(self.manifest, request=lambda c: {'ok': True, 'result': self.tabs(False)} if c['op'] == 'tabs' else self.fail('must not activate'))

    def test_interruption_before_once_leaves_preflight_and_can_dispatch_once(self):
        with patch.object(m.Activation, 'once', side_effect=RuntimeError('interrupted before once')):
            with self.assertRaisesRegex(RuntimeError, 'before once'):
                m.ensure(self.manifest, request=self.request)
        self.assertEqual(self.state()['state'], 'preflight')
        self.assertEqual(self.state()['calls'], [])
        self.assertFalse(any((c['op'] == 'activate' for c in self.commands)))
        result = m.ensure(self.manifest, request=self.request)
        self.assertTrue(result['activation_dispatched_this_call'])
        self.assertEqual(sum((c['op'] == 'activate' for c in self.commands)), 1)

    def test_once_intent_persisted_then_exception_never_replays(self):
        with patch.object(m.Activation, 'call', side_effect=RuntimeError('interrupted after intent')):
            with self.assertRaisesRegex(RuntimeError, 'after intent'):
                m.ensure(self.manifest, request=self.request)
        self.assertEqual(len(self.state()['calls']), 1)
        self.assertEqual(self.state()['calls'][0]['state'], 'unknown')
        with self.assertRaisesRegex(ValueError, 'unknown-no-replay'):
            m.ensure(self.manifest, request=self.request)
        self.assertFalse(any((c['op'] == 'activate' for c in self.commands)))
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
        patch.object(m, 'ensure', side_effect=lambda *a, **k: self.events.append('activate-guard')).start()
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
