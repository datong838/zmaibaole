"""Exact reviewed proposal transition. This is not a supervisor release record."""
import ast,copy,hashlib,json,unittest
from pathlib import Path
F=Path(__file__).parent/'fixtures/structure-migrations/postpaste';S=Path(__file__).parents[1]/'scripts'
FREEZE='81845384ae5c90da6d8d6bae5a771a42538d93d7074a921991a2f6b4530260dd'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def qualified(tree):
 result={}
 def visit(node,prefix=''):
  for child in ast.iter_child_nodes(node):
   if isinstance(child,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
    name=prefix+child.name
    if not isinstance(child,ast.ClassDef):result[name]=ast.dump(child)
    visit(child,name+'.')
   else:visit(child,prefix)
 visit(tree);return result
def parsed(name,phase):return ast.parse((F/(phase+'-'+name)).read_text())
class MigrationTests(unittest.TestCase):
 def test_reviewed_proposal_provenance_exact_before_after_bytes(self):
  manifest=json.loads((F/'reviewed-proposal.json').read_text());self.assertEqual(manifest['status'],'reviewed-proposal-not-released');self.assertEqual(manifest['proposal_freeze_sha256'],FREEZE);self.assertEqual(sha(F/'proposal-freeze.json'),FREEZE)
  self.assertEqual(sha(F/'proposal-report.json'),manifest['proposal_report_sha256']);frozen=json.loads((F/'proposal-freeze.json').read_text())['files'];report=json.loads((F/'proposal-report.json').read_text())
  self.assertEqual(manifest['review_evidence']['independent_contract_tests_passed'],5)
  for name,record in manifest['modules'].items():
   self.assertEqual(sha(F/('before-'+name)),record['before_sha256']);self.assertEqual(sha(F/('after-'+name)),record['after_sha256'])
   self.assertEqual(record['before_sha256'],report['production_baselines']['skills/wecom-messenger/scripts/'+name]);self.assertEqual(record['after_sha256'],frozen['project/skills/wecom-messenger/scripts/'+name])
   if name=='messenger.py':
    # The historical endpoint remains exact; only the current-tip link advances.
    transition=F.parent/'initial-locate';tip=json.loads((transition/'reviewed-proposal.json').read_text())
    self.assertEqual(sha(transition/'before-messenger.py'),record['after_sha256']);self.assertEqual(record['after_sha256'],tip['before_sha256']);self.assertEqual(sha(S/name),tip['after_sha256'])
   else:self.assertEqual(sha(S/name),record['after_sha256'])
  # Existing capability-release endpoint is retained and binds this exact before.
  self.assertEqual(sha(F/'before-messenger.py'),sha(F.parent/'capabilities-messenger.py'))
 def test_precise_qualified_function_delta(self):
  expected={'files.py':({'_StageRead.take','_wait_image_binding','stage_file'},{'_StageRead.take_snapshot','_BoundImageRead.__init__','_BoundImageRead.signature','_BoundImageRead.take_snapshot'}),'messenger.py':({'advance'},set()),'images.py':({'confirm_image'},set())}
  for name,(changed,added) in expected.items():
   a=qualified(parsed(name,'before'));b=qualified(parsed(name,'after'))
   self.assertEqual(set(a)-set(b),set(),name);self.assertEqual(set(b)-set(a),added,name);self.assertEqual({k for k in a if a[k]!=b[k]},changed,name)
 def test_no_unreviewed_import_global_or_signature_changes(self):
  class Skeleton(ast.NodeTransformer):
   def visit_ClassDef(self,node):
    if node.name=='_BoundImageRead':return None
    return self.generic_visit(node)
   def visit_FunctionDef(self,node):
    if node.name=='take_snapshot':return None
    node.body=[ast.Pass()];return node
  for name in ('files.py','messenger.py','images.py'):
   self.assertEqual(ast.dump(Skeleton().visit(parsed(name,'before'))),ast.dump(Skeleton().visit(parsed(name,'after'))),name)
 def test_final_focus_pid_guard_is_only_image_confirmation_delta(self):
  a=next(n for n in parsed('images.py','before').body if isinstance(n,ast.FunctionDef) and n.name=='confirm_image');b=next(n for n in parsed('images.py','after').body if isinstance(n,ast.FunctionDef) and n.name=='confirm_image')
  guard=ast.parse("if snapshot.get('pid')!=s.get('pid'):raise ui.UIError('image-confirm-process-changed')").body[0]
  hits=[i for i,node in enumerate(b.body) if ast.dump(node)==ast.dump(guard)];self.assertEqual(len(hits),1);idx=hits[0]
  self.assertEqual(ast.dump(b.body[idx-1]),ast.dump(ast.parse('snapshot=native.tree()').body[0]));self.assertEqual(ast.dump(b.body[idx+1]),ast.dump(ast.parse('fresh=ui.context(snapshot)').body[0]))
  del b.body[idx];self.assertEqual(ast.dump(a),ast.dump(b))
 def test_snapshot_adapter_context_semantics_and_confirm_client_checks_unchanged(self):
  before=parsed('files.py','before');after=parsed('files.py','after');a=next(n for n in before.body if isinstance(n,ast.ClassDef) and n.name=='_StageRead');b=next(n for n in after.body if isinstance(n,ast.ClassDef) and n.name=='_StageRead');old=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='take');snapshot=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='take_snapshot');wrapper=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='take')
  # All invalidation checks remain exact before replacing the final return value.
  self.assertEqual([ast.dump(n) for n in old.body[:-1]],[ast.dump(n) for n in snapshot.body[:-1]])
  self.assertEqual(ast.dump(snapshot.body[-1]),ast.dump(ast.parse('return self.snapshot').body[0]));self.assertEqual(ast.dump(wrapper.body[0]),ast.dump(ast.parse('return ui.context(self.take_snapshot(native,job))').body[0]))
  a=qualified(parsed('images.py','before'));b=qualified(parsed('images.py','after'))
  for name in ('owned_proof','settled_owned_proof','verify_image'):self.assertEqual(a[name],b[name])
if __name__=='__main__':unittest.main()
