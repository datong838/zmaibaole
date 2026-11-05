"""Portable synthetic public AX fixture. No live evidence/UI invocation."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/wecom-messenger/scripts'),str(ROOT/'skills/wecom-messenger/tests')]
from test_sender import fixture
spec=importlib.util.spec_from_file_location('preinput_candidate',(Path(__file__).with_name('sender_preinput_recovery.py') if Path(__file__).with_name('sender_preinput_recovery.py').exists() else ROOT/'skills/wecom-messenger/scripts/sender_preinput_recovery.py'));h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
m=h.m
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.addCleanup(patch.stopall)
  patch.object(m,'RUNTIME',self.root/'jobs').start();self.source=self.root/'source.xlsx';self.source.write_bytes(b'synthetic-file')
  self.path,s=m.prepare('original-key','group','测试群请忽略',file=self.source,directory=m.RUNTIME)
  s.update(status='failed',phase='stage',pid=123,error='ui-tree-incomplete',last_read={'read_scope':'application-windows-complete','truncated':True,'truncation_reason':'scoped-required-array-unavailable:AXChildren','node_count':230})
  s['events']=[{'stage':'recipient-verified','at':'synthetic','name':'测试群请忽略','kind':'group'},{'stage':'stopped','at':'synthetic','error':'ui-tree-incomplete'}];m.atomic(self.path,s);self.original=self.path.read_bytes();self.digest=h.sha(self.original);self.reads=0;self.closed=0;self.snap=fixture();self.snap.update(read_scope='application-windows-complete',node_count=25)
  owner=self
  class Native:
   def __init__(self,pid):owner.assertEqual(pid,123)
   def tree(self):owner.reads+=1;return copy.deepcopy(owner.snap)
   def close(self):owner.closed+=1
  self.factory=Native
 def run_repair(self):return h.reconcile(self.path,self.digest,self.factory)
 def test_exact_readonly_recovery_and_idempotent_no_second_read(self):
  result=self.run_repair();now=json.loads(self.path.read_text());v=h.verify_recovered(now,result['proof']);self.assertEqual(v['original_error'],{'code':'ui-tree-incomplete','message':'ui-tree-incomplete'});self.assertEqual(h.document(result['proof'])['original_sha256'],self.digest)
  self.assertEqual(Path(v['original_journal']['path']).read_bytes(),self.original);self.assertEqual(now['job'],json.loads(self.original)['job']);self.assertEqual(self.reads,1);self.run_repair();self.assertEqual(self.reads,1)
 def test_wrong_pid_recipient_draft_truncated_modal_rejected(self):
  for kind in ['pid','target','draft','truncated','modal']:
   with self.subTest(kind=kind):
    self.snap=fixture(name='wrong' if kind=='target' else '测试群请忽略',draft='draft' if kind=='draft' else '');self.snap.update(read_scope='application-windows-complete',node_count=25)
    if kind=='pid':self.snap['pid']=999
    if kind=='truncated':self.snap['truncated']=True
    if kind=='modal':self.snap['tree']['children'].append({'role':'AXSheet','path':[1],'children':[]})
    with self.assertRaises(Exception):self.run_repair()
    self.assertEqual(self.path.read_bytes(),self.original)
 def test_intent_unknown_or_different_error_zero_reads(self):
  for change in [{'paste_intent':{'x':1}},{'status':'unknown'},{'error':'other-error'},{'sent':True}]:
   s=json.loads(self.original);s.update(change);m.atomic(self.path,s)
   with self.assertRaises(Exception):h.reconcile(self.path,h.sha(self.path.read_bytes()),self.factory)
  self.assertEqual(self.reads,0)
 def test_concurrent_bytes_change_rejected(self):
  owner=self
  class Native(self.factory):
   def tree(n):owner.path.write_bytes(owner.original+b' ');return super().tree()
  with self.assertRaisesRegex(ValueError,'concurrent'):h.reconcile(self.path,self.digest,Native)
 def test_savedproof_delta_tamper_and_sourcefile_change_rejected(self):
  result=self.run_repair();s=json.loads(self.path.read_text());s['sent']=True
  with self.assertRaisesRegex(ValueError,'delta'):h.verify_recovered(s,result['proof'])
  s=json.loads(self.path.read_text());self.source.write_bytes(b'changed')
  with self.assertRaises(Exception):h.verify_recovered(s,result['proof'])
 def test_resume_commit_crash_recovers_without_another_tree(self):
  atomic=m.atomic
  def fail(path,val):
   if Path(path).name=='recovery-proof.json':raise OSError('synthetic-crash')
   return atomic(path,val)
  with patch.object(m,'atomic',fail):
   with self.assertRaises(OSError):self.run_repair()
  self.assertEqual(json.loads(self.path.read_text())['status'],'running');self.run_repair();self.assertEqual(self.reads,1)
 def test_failed_truncated_read_then_same_original_sha_success_preserves_both(self):
  self.snap['truncated']=True;self.snap['truncation_reason']='scoped-required-array-unavailable:AXChildren'
  with self.assertRaises(Exception):self.run_repair()
  base=self.path.parent/'preinput-read-recovery'/self.digest
  failed=list((base/'attempts').glob('*/fresh-snapshot.json'));self.assertEqual(len(failed),1);old=failed[0].read_bytes();self.assertEqual(self.path.read_bytes(),self.original)
  self.snap['truncated']=False;self.snap.pop('truncation_reason');result=self.run_repair();self.assertEqual(self.reads,2);self.assertEqual(failed[0].read_bytes(),old);self.assertEqual(len(list((base/'attempts').glob('*/fresh-snapshot.json'))),2)
  proof=h.document(result['proof']);self.assertNotEqual(proof['fresh_snapshot']['path'],str(failed[0]))
 def test_at_is_aware_utc_and_naive_proof_rejected(self):
  from datetime import datetime,timedelta
  result=self.run_repair();proof=h.document(result['proof']);at=datetime.fromisoformat(proof['at']);self.assertEqual(at.utcoffset(),timedelta(0))
  proof['at']='2026-10-22T12:00:00';pp=Path(result['proof']['path']);m.atomic(pp,proof);s=json.loads(self.path.read_text());s[h.FIELD]=h.ref(pp)
  with self.assertRaisesRegex(ValueError,'utc'):h.verify_recovered(s,s[h.FIELD])
 def test_crash_after_proof_before_job_field_finalizes_without_ui(self):
  atomic=m.atomic
  def fail(path,val):
   if Path(path)==self.path and h.FIELD in val:raise OSError('synthetic-final-commit-crash')
   return atomic(path,val)
  with patch.object(m,'atomic',fail):
   with self.assertRaises(OSError):self.run_repair()
  result=self.run_repair();self.assertEqual(self.reads,1);self.assertEqual(h.document(result['proof'])['kind'],h.KIND)
 def test_ambiguous_crash_snapshot_holds_without_second_ui(self):
  atomic=m.atomic
  def fail(path,val):
   if Path(path).name=='recovery-proof.json':raise OSError('synthetic-crash')
   return atomic(path,val)
  with patch.object(m,'atomic',fail):
   with self.assertRaises(OSError):self.run_repair()
  base=self.path.parent/'preinput-read-recovery'/self.digest;existing=next((base/'attempts').glob('*/fresh-snapshot.json'));extra=base/'attempts'/('f'*32)/'fresh-snapshot.json';m.atomic(extra,json.loads(existing.read_text()))
  with self.assertRaisesRegex(ValueError,'not-unique'):self.run_repair()
  self.assertEqual(self.reads,1)
 def test_existing_sender_lock_rejects_before_read(self):
  with m.lock(self.path.parent):
   with self.assertRaises(m.SendError):self.run_repair()
  self.assertEqual(self.reads,0)
 def test_noncanonical_path_or_wrong_sha_rejected(self):
  copy_path=self.root/'fake.json';copy_path.write_bytes(self.original)
  with self.assertRaises(Exception):h.reconcile(copy_path,self.digest,self.factory)
  with self.assertRaises(Exception):h.reconcile(self.path,'0'*64,self.factory)
  self.assertEqual(self.reads,0)
if __name__=='__main__':unittest.main()
