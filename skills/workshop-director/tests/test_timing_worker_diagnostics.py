"""Portable pure/TEMP regression. Imports installed project sources; no business/UI calls."""
import sys,ast,copy,importlib.util,unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_capture.py').is_file() and (p/'packages/workshop-director/workshop_director/timing_worker.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'packages/workshop-director')]
import workshop_director.timing_worker as m
class TimingDiagnostics(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name).resolve()
        self.f = self.p / 'runtime/standalone-workshop-director/attempts/task-test-1'
        self.f.mkdir(parents=True)
        self.py = self.p / 'skills/daily-comment-stats/.venv/bin/python'
        self.config = {'project': str(self.p), 'python': str(self.py), 'worker_argv': [str(self.py), '-m', 'workshop_director.timing_worker']}
        cfg = m.immutable(self.f.parent.parent / 'config.json', self.config)
        source = self.p / 'skills/wecom-messenger/scripts/performance_trace.py'
        source.parent.mkdir(parents=True)
        source.write_text('# fixture not executed\n')
        bridge = self.p / 'skills/chrome-dom-export/scripts/bridge.py'
        bridge.parent.mkdir(parents=True)
        bridge.write_text('# fixture emitter not executed\n')
        self.r = {'kind': 'workshop-worker-request-v1', 'root': str(self.f.parent.parent), 'attempt_id': self.f.name, 'config': self.config, 'config_ref': cfg, 'task': {'id': 'task-test', 'flow': 'daily-comment-stats', 'payload': {}}}
        self.q = self.f / 'request.json'
        m.immutable(self.q, self.r)
        self.out = self.f / 'response.json'
        self.sp = patch.object(m.sys, 'executable', str(self.py))
        self.sp.start()
        self.addCleanup(self.sp.stop)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_original_step_once_same_request_response_and_env_restored(self):
        calls = []

        def step(r, f):
            calls.append((r, f, os.environ['WECOM_PERFORMANCE_DIR']))
            return {'fixture': 'original response unchanged'}
        out = m.run(self.q, self.out, step)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:2], (self.r, self.f))
        self.assertEqual(calls[0][2], str(self.f / 'wecom-performance'))
        self.assertEqual(m.read(self.out), out)
        self.assertNotIn('WECOM_PERFORMANCE_DIR', os.environ)
        self.assertFalse((self.f / 'wecom-performance').exists())

    def test_old_default_worker_not_silently_opted_in(self):
        self.config['worker_argv'] = [str(self.py), '-m', 'workshop_director.local_worker']
        m.atomic(self.f.parent.parent / 'config.json', self.config)
        self.r['config'] = self.config
        self.r['config_ref'] = m.ref(self.f.parent.parent / 'config.json')
        m.atomic(self.q, self.r)
        with self.assertRaisesRegex(ValueError, 'explicit-opt-in'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_wrong_python_rejected(self):
        with patch.object(m.sys, 'executable', '/other/python'), self.assertRaisesRegex(ValueError, 'fixed-python'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_wrong_response_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'original-attempt'):
            m.run(self.q, self.f / 'alias.json', lambda *_: self.fail('no business'))

    def test_existing_diagnostic_env_not_redirected(self):
        os.environ['WECOM_PERFORMANCE_DIR'] = '/existing'
        with self.assertRaisesRegex(ValueError, 'existing-diagnostic'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_original_exception_preserved_no_second_step(self):
        calls = []

        def step(*_):
            calls.append(1)
            raise ValueError('original stop')
        with self.assertRaisesRegex(ValueError, 'original stop'):
            m.run(self.q, self.out, step)
        self.assertEqual(calls, [1])
        self.assertFalse(self.out.exists())
        self.assertTrue(m.read(self.f / 'timing-worker-scope.json')['business_exception'])
        self.assertNotIn('WECOM_PERFORMANCE_DIR', os.environ)

    def test_config_changed_refused_before_business(self):
        m.atomic(self.f.parent.parent / 'config.json', {})
        with self.assertRaisesRegex(ValueError, 'pinned-file-changed'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_benchmark_requires_separate_review_not_silent_weakened_gate(self):
        self.r['task']['payload']['benchmark'] = {'fixture': 'round'}
        m.atomic(self.q, self.r)
        with self.assertRaisesRegex(ValueError, 'not-benchmark'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_other_original_flow_delegates_unchanged_not_new_router(self):
        self.r['task']['flow'] = 'negative-review-complaints'
        m.atomic(self.q, self.r)
        calls = []
        out = m.run(self.q, self.out, lambda r, f: calls.append(r) or {'fixture': 'same original complaint step'})
        self.assertEqual(calls, [self.r])
        self.assertEqual(out, {'fixture': 'same original complaint step'})

    def test_unknown_flow_cannot_use_entry(self):
        self.r['task']['flow'] = 'unknown-flow'
        m.atomic(self.q, self.r)
        with self.assertRaisesRegex(ValueError, 'known-flow-only'):
            m.run(self.q, self.out, lambda *_: self.fail('no business'))

    def test_both_env_once_original_response_and_inherited_environment(self):
        os.environ['UNCHANGED_FIXTURE'] = 'keep'
        calls = []

        def step(r, f):
            calls.append((r, f))
            self.assertEqual(os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR'], str(self.f / 'bridge-performance'))
            self.assertEqual(os.environ['WECOM_PERFORMANCE_DIR'], str(self.f / 'wecom-performance'))
            self.assertEqual(os.environ['UNCHANGED_FIXTURE'], 'keep')
            return {'original': 'response'}
        result = m.run(self.q, self.out, step)
        self.assertEqual(calls, [(self.r, self.f)])
        self.assertEqual(m.read(self.out), result)
        self.assertNotIn('BRIDGE_REQUEST_PERFORMANCE_DIR', os.environ)
        self.assertNotIn('WECOM_PERFORMANCE_DIR', os.environ)
        self.assertEqual(os.environ['UNCHANGED_FIXTURE'], 'keep')
        self.assertFalse((self.f / 'bridge-performance').exists())

    def test_existing_exact_dual_values_restored(self):
        values = {'WECOM_PERFORMANCE_DIR': str(self.f / 'wecom-performance'), 'BRIDGE_REQUEST_PERFORMANCE_DIR': str(self.f / 'bridge-performance')}
        os.environ.update(values)
        m.run(self.q, self.out, lambda *_: {'ok': 'original'})
        self.assertTrue(all((os.environ[k] == v for (k, v) in values.items())))

    def test_bridge_conflict_refuses_before_business_or_binding_and_keeps_env(self):
        os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR'] = '/different/attempt'
        os.environ['WECOM_PERFORMANCE_DIR'] = str(self.f / 'wecom-performance')
        with self.assertRaisesRegex(ValueError, 'existing-bridge-diagnostic'):
            m.run(self.q, self.out, lambda *_: self.fail('must not invoke'))
        self.assertEqual(os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR'], '/different/attempt')
        self.assertEqual(os.environ['WECOM_PERFORMANCE_DIR'], str(self.f / 'wecom-performance'))
        self.assertFalse((self.f / 'timing-worker-binding.json').exists())

    def test_bridge_symlink_refuses_without_creating_other_log_directory(self):
        other = self.p / 'foreign'
        other.mkdir()
        (self.f / 'bridge-performance').symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'directory-alias'):
            m.run(self.q, self.out, lambda *_: self.fail('must not invoke'))
        self.assertEqual(list(other.iterdir()), [])
        self.assertNotIn('BRIDGE_REQUEST_PERFORMANCE_DIR', os.environ)

    def test_original_exception_restores_both_even_when_step_changes_env(self):
        calls = []

        def step(*_):
            calls.append(1)
            os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR'] = 'changed-inside'
            os.environ['WECOM_PERFORMANCE_DIR'] = 'changed-inside'
            raise RuntimeError('original failure')
        with self.assertRaisesRegex(RuntimeError, 'original failure'):
            m.run(self.q, self.out, step)
        self.assertEqual(calls, [1])
        self.assertNotIn('BRIDGE_REQUEST_PERFORMANCE_DIR', os.environ)
        self.assertNotIn('WECOM_PERFORMANCE_DIR', os.environ)
        self.assertFalse(self.out.exists())
        self.assertTrue(m.read(self.f / 'timing-worker-scope.json')['business_exception'])

    def test_response_write_failure_restores_both(self):
        original = m.immutable

        def write(path, value):
            if Path(path) == self.out:
                raise OSError('original response write failure')
            return original(path, value)
        with patch.object(m, 'immutable', side_effect=write), self.assertRaisesRegex(OSError, 'response write failure'):
            m.run(self.q, self.out, lambda *_: {'value': 1})
        self.assertNotIn('WECOM_PERFORMANCE_DIR', os.environ)
        self.assertNotIn('BRIDGE_REQUEST_PERFORMANCE_DIR', os.environ)

    def test_diagnostic_binding_has_exact_attempt_and_no_business_content(self):
        m.run(self.q, self.out, lambda *_: {'secret_test_payload': 'not logged to binding'})
        binding = m.read(self.f / 'timing-worker-binding.json')
        self.assertEqual(binding['bridge_directory'], str(self.f / 'bridge-performance'))
        self.assertTrue(binding['diagnostic_only'])
        self.assertFalse(binding['command_payload_logged'])
        self.assertEqual(binding['extra_ui_reads'], 0)
        self.assertEqual(binding['request'], m.ref(self.q))
        self.assertEqual(binding['code_refs'][-1], m.ref(self.p / 'skills/chrome-dom-export/scripts/bridge.py'))
        self.assertNotIn('secret_test_payload', json.dumps(binding))

    def test_bridge_emitter_schema_excludes_payload_token_dom_and_does_not_call_network(self):
        import ast, time, uuid
        src = R / 'skills/chrome-dom-export/scripts/bridge.py'
        tree = ast.parse(src.read_bytes())
        nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('_request_timing_start', '_request_timing_finish')]
        env = {'os': os, 'Path': Path, 'time': time, 'uuid': uuid, 'json': json, 'OPS': {'tree'}}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(src), 'exec'), env)
        os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR'] = str(self.f / 'bridge-performance')
        start = env['_request_timing_start']()
        env['_request_timing_finish'](start, {'op': 'tree', 'secret': 'no', 'locator': {'text': 'business'}}, {'ok': True, 'DOM': 'private'}, False)
        paths = list((self.f / 'bridge-performance').glob('*.json'))
        self.assertEqual(len(paths), 1)
        v = m.read(paths[0])
        self.assertEqual(set(v), {'schema', 'op', 'elapsed_monotonic_ns', 'ok', 'outcome', 'exception'})
        self.assertEqual(v['op'], 'tree')
        self.assertEqual(v['outcome'], 'success')
        self.assertNotIn('private', json.dumps(v))
        self.assertNotIn('business', json.dumps(v))

    def test_plain_child_inherits_both_diagnostic_directories_without_custom_env(self):
        import subprocess
        real_python = R / 'skills/daily-comment-stats/.venv/bin/python'

        def step(*_):
            code = "import os,json; print(json.dumps({k:os.environ.get(k) for k in ('WECOM_PERFORMANCE_DIR','BRIDGE_REQUEST_PERFORMANCE_DIR')}))"
            p = subprocess.run([str(real_python), '-I', '-B', '-c', code], capture_output=True, text=True, check=True)
            v = json.loads(p.stdout)
            self.assertEqual(v['WECOM_PERFORMANCE_DIR'], str(self.f / 'wecom-performance'))
            self.assertEqual(v['BRIDGE_REQUEST_PERFORMANCE_DIR'], str(self.f / 'bridge-performance'))
            return {'original': 'unchanged'}
        self.assertEqual(m.run(self.q, self.out, step), {'original': 'unchanged'})
if __name__=="__main__":unittest.main()
