"""Current-source native-stage tests with synthetic TEMP frontier; no UI/RPC."""
import sys,unittest,tempfile,copy,importlib.util,types
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts/review_capture_focus.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'skills/wecom-messenger/scripts')]
import review_capture_focus as m
o=m.o;tab=m.previous;nw=m.nw
spec=importlib.util.spec_from_file_location('native_stage_portable_fixture',R/'skills/negative-review-complaints/tests/test_review_native_focus_events.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
def forbidden_real_port(*args,**kwargs):raise AssertionError('real-AppKit-CG-or-bridge-forbidden-in-pure-test')
# Direct process-local sentinels survive the inherited fixture's patch.stopall cleanup.
m.PublicRunningApplication=forbidden_real_port
nw.PublicCGWindow=forbidden_real_port
tab.overlay.bridge.request=forbidden_real_port
legacy=types.SimpleNamespace(derive=m.derive)
def seed_extension_only_frontier(manifest_ref,*,activation_ref,pid,request,reader):
    """Pure fake pre-native fixture, using current durable Focus.once and validator.
    Does not execute archived source; creates no actual business operation.
    """
    binding=legacy.derive(manifest_ref,activation_ref,pid);manifest=o.doc(manifest_ref)
    directory=Path(manifest['source']['path']).parent/'.review-capture-focus';directory.mkdir(exist_ok=True)
    key=tab.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});path=directory/(key+'.json');rawdir=directory/key;rawdir.mkdir()
    state={'kind':'review-capture-focus-events-v1','binding':binding,'events':[],'reads':[],'created_at':m.stamp()}
    def raw(command,label):
        reply=request(command);r=o.immutable(rawdir/(label+'-'+str(len(state['reads']))+'.json'),{'command':command,'response':reply,'observed_at':m.stamp()});state['reads'].append(r);tab.overlay.rc.atomic(path,state);return reply
    reply=raw({'op':'tabs'},'before-tabs');before={**reader(pid),'tabs':reply['result'],'tabs_reply':state['reads'][-1],'observed_at':m.stamp()};before_ref=o.immutable(rawdir/'before-observation.json',before)
    if m.qualify(before,binding)!='external-focus-loss':raise AssertionError('fixture-requires-external-focus-loss')
    event={'number':1,'binding':binding,'before':before_ref,'state':'preflight','phase':'capture-focus','revision':0,'calls':[],'created_at':m.stamp()};state['events'].append(event);tab.overlay.rc.atomic(path,state)
    focus=m.Focus(path,state,event,binding,request,raw);focus.once({'op':'activate','tabId':binding['scope']['tabId']});event['state']='unknown';focus.save();m.validate_events(state,binding)
    raise ValueError('capture-focus-effect-unverified-no-replay')
legacy.ensure=seed_extension_only_frontier
class Stage(unittest.TestCase):
    setUp = base.Focus.setUp
    tabs = base.Focus.tabs
    reader = base.Focus.reader
    path = base.Focus.path
    presses = base.Focus.presses

    def request(self, c):
        self.count.append(c)
        if c['op'] == 'activate':
            self.focused = True
            return {'ok': True, 'result': {**self.binding['scope'], 'url': self.binding['url'], 'active': True, 'windowFocused': True}}
        return {'ok': True, 'result': self.tabs()}

    def create_original_browser_confirmed(self):
        with patch.object(legacy, 'derive', return_value=self.binding), self.assertRaisesRegex(ValueError, 'effect-unverified-no-replay'):
            legacy.ensure(self.ref, activation_ref=self.act, pid=123, request=self.request, reader=self.reader)
        self.assertEqual(self.presses(), 1)
        s = o.doc(o.ref(self.path()))
        self.assertEqual(s['events'][0]['state'], 'unknown')
        self.assertNotIn('native_focus', s['events'][0])

    def ensure(self, activate, **kw):
        return m.ensure(self.ref, activation_ref=self.act, pid=123, request=self.request, reader=self.reader, native_activator=activate, **kw)

    def native(self, pid):
        s = o.doc(o.ref(self.path()))
        self.assertEqual(s['events'][-1]['native_focus']['state'], 'unknown')
        self.assertEqual(pid, 123)
        self.native_calls += 1
        self.front = 123
        return {'pid': 123, 'bundle': 'com.google.Chrome', 'process': {'executable': nw.EXE}, 'request_accepted': True, 'frontmost_verified': False, 'launch_used': False}

    def test_native_original_attempt8_shape_no_extension_replay_true_input_flag(self):
        self.create_original_browser_confirmed()
        self.native_calls = 0
        r = self.ensure(self.native)
        self.assertTrue(r['input_dispatched'])
        self.assertTrue(r['native_input_dispatched'])
        self.assertEqual(self.presses(), 1)
        self.assertEqual(self.native_calls, 1)
        self.assertEqual(o.doc(o.ref(self.path()))['events'][0]['native_focus']['state'], 'complete')

    def test_native_unknown_lost_reply_cannot_repeat_then_readonly_reconcile(self):
        self.create_original_browser_confirmed()
        with self.assertRaisesRegex(RuntimeError, 'lost'):
            self.ensure(lambda p: (_ for _ in ()).throw(RuntimeError('lost')))
        with self.assertRaisesRegex(ValueError, 'native-unknown-readonly-no-replay'):
            self.ensure(lambda p: self.fail('must not activate again'))
        self.front = 123
        self.focused = True
        r = self.ensure(lambda p: self.fail('must not activate again'))
        self.assertFalse(r['input_dispatched'])
        self.assertEqual(self.presses(), 1)

    def test_native_acceptance_without_frontmost_not_success(self):
        self.create_original_browser_confirmed()
        self.native_calls = 0

        def accepted(pid):
            self.native_calls += 1
            return {'pid': pid, 'bundle': 'com.google.Chrome', 'request_accepted': True, 'frontmost_verified': False, 'launch_used': False}
        with self.assertRaisesRegex(ValueError, 'native-effect-unverified'):
            self.ensure(accepted)
        with self.assertRaisesRegex(ValueError, 'native-unknown-readonly-no-replay'):
            self.ensure(accepted)
        self.assertEqual(self.native_calls, 1)
        self.assertEqual(self.presses(), 1)

    def test_native_browser_unknown_never_enters_new_stage(self):

        def request(c):
            if c['op'] == 'activate':
                raise TimeoutError('browser reply lost')
            return {'ok': True, 'result': self.tabs()}
        with self.assertRaises(TimeoutError):
            m.ensure(self.ref, activation_ref=self.act, pid=123, request=request, reader=self.reader, native_activator=lambda p: self.fail('no native'))
        self.focused = True
        with self.assertRaisesRegex(ValueError, 'unknown-readonly-no-replay'):
            self.ensure(lambda p: self.fail('no native'))

    def test_native_readonly_mode_does_not_dispatch_missing_native_stage(self):
        self.create_original_browser_confirmed()
        with self.assertRaisesRegex(ValueError, 'native-stage-not-qualified'):
            self.ensure(lambda p: self.fail('readonly'), readonly=True)
        self.assertNotIn('native_focus', o.doc(o.ref(self.path()))['events'][0])

    def test_native_next_external_change_gets_distinct_event_after_complete(self):
        self.create_original_browser_confirmed()
        self.native_calls = 0
        self.ensure(self.native)
        self.front = 999
        self.focused = False
        r = self.ensure(self.native)
        self.assertEqual(r['focus_event'], 2)
        self.assertEqual(self.native_calls, 2)
        self.assertEqual(self.presses(), 2)

    def test_native_completed_then_outer_save_crash_can_seal_and_next_loss(self):
        self.native_calls = 0
        save = m.Focus.save

        def crash(port):
            if port.s['state'] == 'complete':
                raise RuntimeError('outer save crashed')
            return save(port)
        with patch.object(m.Focus, 'save', crash), self.assertRaisesRegex(RuntimeError, 'outer save crashed'):
            self.ensure(self.native)
        old = o.doc(o.ref(self.path()))
        self.assertEqual(old['events'][0]['state'], 'unknown')
        self.assertEqual(old['events'][0]['native_focus']['state'], 'complete')
        self.front = 999
        self.focused = False
        r = self.ensure(self.native)
        self.assertEqual(r['focus_event'], 2)
        self.assertEqual(self.presses(), 2)
        self.assertEqual(self.native_calls, 2)

    def test_native_target_scope_change_or_capture_unknown_stops_before_activation(self):
        self.create_original_browser_confirmed()
        self.binding['url'] += '&changed=1'
        with self.assertRaises(ValueError):
            self.ensure(lambda p: self.fail('no native'))

    def test_native_app_port_exact_Chrome_identity_process_and_no_launch(self):

        class Port:

            def __init__(self, identity):
                self.value = identity
                self.activated = 0
                self.closed = False

            def identity(self, p):
                return self.value

            def activate(self):
                self.activated += 1
                return True

            def close(self):
                self.closed = True
        process = type('P', (), {'process_path': lambda _, p: nw.EXE})()
        identity = {'pid': 123, 'bundle': 'com.google.Chrome', 'terminated': False}
        p = Port(identity)
        r = m.activate_original_chrome(123, p, process)
        self.assertEqual(p.activated, 1)
        self.assertTrue(p.closed)
        self.assertFalse(r['frontmost_verified'])
        self.assertFalse(r['launch_used'])
        for wrong in ({**identity, 'pid': 124}, {**identity, 'bundle': 'com.tencent.WeWorkMac'}, {**identity, 'terminated': True}):
            p = Port(wrong)
            with self.assertRaisesRegex(ValueError, 'native-app-identity-mismatch'):
                m.activate_original_chrome(123, p, process)
            self.assertEqual(p.activated, 0)
            self.assertTrue(p.closed)
    def test_unfocused_target_active_all_Chrome_unfocused_native_once_extension_zero(self):
        self.create_original_browser_confirmed(); self.count=[]; self.focused=False; self.native_calls=0
        def activate(pid):
            self.focused=True
            return self.native(pid)
        r=self.ensure(activate)
        self.assertTrue(r['native_input_dispatched']); self.assertEqual(self.native_calls,1); self.assertEqual(self.presses(),0)

    def test_unfocused_other_Chrome_focused_or_unknown_rejects_native_zero(self):
        self.create_original_browser_confirmed(); self.count=[]; self.focused=False; self.native_calls=0; original=self.tabs
        for focused in (True,None):
            def tabs():
                return original()+[{'windowId':9,'focused':focused,'tabs':[{'tabId':8,'windowId':9,'active':True,'allowed':False,'url':'chrome://newtab/'}]}]
            with patch.object(self,'tabs',side_effect=tabs), self.assertRaisesRegex(ValueError,'native-stage-not-qualified'):
                self.ensure(lambda p: (_ for _ in ()).throw(AssertionError('must not native')))
        self.assertEqual(self.presses(),0); self.assertNotIn('native_focus',o.doc(o.ref(self.path()))['events'][0])
if __name__=="__main__":unittest.main()
