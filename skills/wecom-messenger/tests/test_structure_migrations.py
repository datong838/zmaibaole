"""Release-bound source history; newer transitions append a version, not relax history."""
import ast,hashlib,json,unittest
from pathlib import Path
T=Path(__file__).parent;F=T/'fixtures/structure-migrations';S=T.parent/'scripts'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def functions(path):return {n.name:ast.dump(n) for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
class MigrationTests(unittest.TestCase):
 def test_fixture_bytes_and_supervisor_release_bindings(self):
  manifest=json.loads((F/'provenance.json').read_text())
  for name,record in manifest.items():self.assertEqual(digest(F/name),record['sha256'],name)
  for stage in ('timing','capabilities'):
   release=json.loads((F/(stage+'-release.json')).read_text());rows=release.get('files',release.get('published'))
   for name in ('native.py','messenger.py'):
    published=next(r for r in rows if r['path'].endswith('/scripts/'+name))
    self.assertEqual(digest(F/(stage+'-'+name)),published['sha256'])
  release=json.loads((F/'children-release.json').read_text())
  self.assertEqual(digest(F/'children-native.py'),release['published']['sha256'])
  self.assertEqual(digest(F/'capabilities-native.py'),release['published']['before_sha256'])
 def test_current_source_matches_latest_reviewed_transition(self):
  # New production changes require their own source-bound transition. Historical
  # AST tests above never compare their obsolete version directly to current.
  self.assertEqual(digest(S/'native.py'),digest(F/'main-window-restore-wait/after-native.py'))
  # Preserve the published capability endpoint as postpaste's fixed before.
  self.assertEqual(digest(F/'postpaste/before-messenger.py'),digest(F/'capabilities-messenger.py'))
  for name in ('files.py','messenger.py','images.py'):
   self.assertEqual(digest(S/name),digest(F/'initial-locate/after-messenger.py') if name=='messenger.py' else digest(F/'postpaste'/('after-'+name)))
 def test_initial_locate_transition_preserves_postpaste_history(self):
  directory=F/'initial-locate';release=json.loads((directory/'reviewed-proposal.json').read_text())
  self.assertEqual(digest(directory/'proposal-freeze.json'),release['proposal_freeze_sha256']);self.assertEqual(digest(directory/'proposal-review.json'),release['proposal_review_sha256'])
  self.assertEqual(digest(F/'postpaste/after-messenger.py'),release['before_sha256']);self.assertEqual(digest(directory/'before-messenger.py'),release['before_sha256']);self.assertEqual(digest(directory/'after-messenger.py'),release['after_sha256'])
  target=next(x for x in json.loads((directory/'proposal-freeze.json').read_text())['targets'] if x['target'].endswith('/scripts/messenger.py'))
  self.assertEqual(target['old_sha256'],release['before_sha256']);self.assertEqual(target['after']['sha256'],release['after_sha256'])
  a,b=functions(directory/'before-messenger.py'),functions(directory/'after-messenger.py')
  self.assertEqual(set(a)-set(b),set());self.assertEqual(set(b)-set(a),{'initial_locate_failure','initial_resume_archive'});self.assertEqual({n for n in a if a[n]!=b[n]},{'resume_before_send'})
 def test_optional_children_extends_frozen_dialog_helper(self):
  directory=F/'main-dialog-optional';record=json.loads((directory/'reviewed-proposal.json').read_text())
  self.assertEqual(digest(F/'dialog-main-window.py'),record['before_sha256']);self.assertEqual(digest(directory/'before-main_window.py'),record['before_sha256']);self.assertEqual(digest(directory/'after-main_window.py'),record['after_sha256'])
  a,b=functions(directory/'before-main_window.py'),functions(directory/'after-main_window.py')
  self.assertEqual(set(a),set(b));self.assertEqual({name for name in a if a[name]!=b[name]},{'native_main_window','read'})
 def test_restore_wait_extends_exact_main_window_release(self):
  directory=F/'main-window-restore-wait';record=json.loads((directory/'reviewed-proposal.json').read_text())
  self.assertEqual(digest(F/'main-window-focus/after-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'before-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'after-native.py'),record['after_sha256'])
  a,b=functions(directory/'before-native.py'),functions(directory/'after-native.py');self.assertEqual(set(a),set(b));self.assertEqual({name for name in a if a[name]!=b[name]},{'focus','_restore_main_window_for_focus'})
 def test_main_window_focus_extends_public_focus_history(self):
  directory=F/'main-window-focus';record=json.loads((directory/'reviewed-proposal.json').read_text())
  self.assertEqual(digest(F/'public-focus/after-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'before-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'after-native.py'),record['after_sha256'])
  a,b=functions(directory/'before-native.py'),functions(directory/'after-native.py');self.assertEqual(set(a)-set(b),set());self.assertEqual(set(b)-set(a),{'_restore_main_window_for_focus'});self.assertEqual({name for name in a if a[name]!=b[name]},{'focus'})
 def test_public_focus_transition_retains_previous_native_guard_history(self):
  directory=F/'public-focus';record=json.loads((directory/'reviewed-proposal.json').read_text())
  self.assertEqual(digest(F/'dialog-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'before-native.py'),record['before_sha256']);self.assertEqual(digest(directory/'after-native.py'),record['after_sha256']);self.assertEqual(digest(directory/'public_app_activation.py'),record['activation_sha256']);self.assertEqual(digest(S/'public_app_activation.py'),record['activation_sha256'])
  a,b=functions(directory/'before-native.py'),functions(directory/'after-native.py');self.assertEqual(set(a)-set(b),set());self.assertEqual(set(b)-set(a),{'fail'});self.assertEqual({name for name in a if a[name]!=b[name]},{'focus'})
 def test_dialog_transition_extends_unchanged_children_baseline(self):
  release=json.loads((F/'dialog-release.json').read_text())
  self.assertEqual(digest(F/'children-native.py'),release['before_sha256'])
  self.assertEqual(digest(F/'dialog-native.py'),release['after_sha256'])
  self.assertEqual(digest(F/'dialog-main-window.py'),release['helper_sha256'])
  self.assertEqual(digest(F/'main-dialog-optional/before-main_window.py'),release['helper_sha256'])
  self.assertEqual(digest(S/'main_window.py'),digest(F/'main-dialog-optional/after-main_window.py'))
  a,b=functions(F/'children-native.py'),functions(F/'dialog-native.py')
  self.assertEqual(set(a),set(b));self.assertEqual({name for name in a if a[name]!=b[name]},{'__init__'})
 def test_children_transition_exact_function_delta_and_constructor_scope(self):
  a=functions(F/'capabilities-native.py');b=functions(F/'children-native.py')
  self.assertEqual(set(a)-set(b),set());self.assertEqual(set(b)-set(a),{'node_attributes_and_children'})
  self.assertEqual({name for name in a if a[name]!=b[name]},{'node_attributes','_tree_once','walk'})
  self.assertEqual(a['__init__'],b['__init__']);self.assertEqual(a['tree'],b['tree'])
 def test_historical_before_sources_bound_to_published_chain(self):
  for name in ('native.py','messenger.py'):
   self.assertEqual(digest(T/'fixtures/sender-capabilities'/(name+'.before')),digest(F/('timing-'+name)))
  expected={'native.py':'bc1e16f5e20c066bad8c59e6497057fd5292b36046d2407821e032aab076b713','messenger.py':'02c701615a25d53c8be561fd1dd616270c8b411e84c7bc17827a780c8f6192b7'}
  for name,value in expected.items():self.assertEqual(digest(T/'fixtures'/('before-stage-timing-'+name)),value)
if __name__=='__main__':unittest.main()
