"""Director boundary tests with a mocked typed verifier; no browser or live state."""
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
DIR=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location('record_repair_director',DIR/'director.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class SenderPreinputDirectorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.at=datetime.now(timezone.utc);start=self.at-timedelta(seconds=1000);self.job={'version':'1.0.0','key':'original-test-file','kind':'group','target':'测试群请忽略','scope':'test','type':'file','file':'/not-opened.xlsx','file_sha256':'a'*64,'file_name':'test.xlsx'};fingerprint=hashlib.sha256(json.dumps(self.job,ensure_ascii=False,sort_keys=True).encode()).hexdigest();self.original={'job':self.job,'fingerprint':fingerprint,'phase':'stage','status':'failed','sent':False,'ui_confirmed':False,'pid':123,'events':[{'stage':'recipient-verified','name':'测试群请忽略','kind':'group'},{'stage':'stopped','error':'ui-tree-incomplete'}],'error':'ui-tree-incomplete','last_read':{'truncated':True,'truncation_reason':'scoped-required-array-unavailable:AXChildren'}}
  self.originalref=self.save('original.json',self.original);self.proof=self.save('proof.json',{'at':self.at.isoformat()});self.current=copy.deepcopy(self.original);self.current.pop('error');self.current.update(phase='locate',status='running');self.current['sender_preinput_recovery']=self.proof;self.journal=self.save('workflow.json',self.current);prior=d.progress.extract(self.current,'daily_stats_operator',self.journal['path'])
  self.state={'test_target':'测试群请忽略','production_enabled':False,'complaint_submission_enabled':False,'index':0,'phase':'attention','day':'2026-10-22','dispatch_id':'dispatch0','dispatch_intent_at':(start-timedelta(seconds=140)).isoformat(),'dispatched_at':(start-timedelta(seconds=139)).isoformat(),'tool_receipt':{'ack':True},'queue':[{'role':'daily_stats_operator','workflow':'daily-comment-stats'}],'cursor':0,'events':[{'type':'dispatched','id':'dispatch0'},{'type':'semantic-progress-attention','dispatch_id':'dispatch0','at':start.isoformat(),'error':'semantic-terminal-error'}],'attention_reason':'semantic-progress-unverified','semantic_progress_error':'semantic-terminal-error','journal':self.journal['path'],'semantic_progress':{'dispatch0':{self.journal['path']:prior}},'last_progress_at':(start-timedelta(seconds=120)).isoformat(),'attempt':0,'parent_clock':367008.987475}
  self.report={'kind':'supervisor-known-sender-preinput-reconciliation-v1','dispatch_id':'dispatch0','day':'2026-10-22','role':'daily_stats_operator','journal':self.journal,'original_binding':prior['binding'],'original_journal':self.originalref,'worker_recovery':self.proof,**{k:True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')}};self.reportpath=Path(self.save('repair.json',self.report)['path'])
  self.verifier=types.SimpleNamespace(__file__=str(DIR.parents[1]/'wecom-messenger/scripts/sender_preinput_recovery.py'),verify_recovered=self.verify)
 def save(self,name,doc):
  p=self.root/name;p.write_text(json.dumps(doc,ensure_ascii=False));return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 def verify(self,document,proof):
  self.assertEqual(document,self.current);self.assertEqual(proof,self.proof);return {'kind':'verified-wecom-preinput-read-recovery-v1','original_journal':self.originalref,'proof':self.proof,'original_error':{'code':self.original['error'],'message':self.original['error']}}
 def runrepair(self):
  original_import=__import__('importlib').import_module
  def lookup(name,*args):return self.verifier if name=='sender_preinput_recovery' else original_import(name,*args)
  with patch('importlib.import_module',side_effect=lookup):return d.reconcile_running_intent(self.state,'dispatch0',self.reportpath,now=self.at)
 def test_same_dispatch_clock_and_progress_preserved(self):
  old=copy.deepcopy(self.state);self.runrepair();self.assertEqual(self.state['phase'],'running')
  for k in ('dispatch_id','dispatch_intent_at','dispatched_at','tool_receipt','attempt','parent_clock','last_progress_at'):self.assertEqual(self.state[k],old[k])
  self.assertEqual(self.state['events'][-1]['type'],'supervisor-known-sender-preinput-reconciled');self.assertAlmostEqual(d.inspect(self.state,now=self.at)['journal_idle_seconds'],120,places=3)
  with self.assertRaises(ValueError):self.runrepair()
 def test_future_or_changed_report_pause_rejected(self):
  self.runrepair();self.reportpath.write_bytes(self.reportpath.read_bytes()+b' ')
  with self.assertRaises(ValueError):d.inspect(self.state,now=self.at)
 def test_scope_quiescence_prefix_and_wrong_kind_rejected(self):
  initial=copy.deepcopy(self.state)
  for mode in ('scope','quiescence','prefix','kind'):
   self.state=copy.deepcopy(initial);r=copy.deepcopy(self.report)
   if mode=='scope':r['dispatch_id']='other'
   if mode=='quiescence':r['browser_quiescent']=False
   if mode=='prefix':self.state['semantic_progress']['dispatch0'][self.journal['path']]['tokens']['recipient-verified']='changed'
   if mode=='kind':r['kind']='generic-clear-error'
   self.reportpath.write_text(json.dumps(r))
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.runrepair()
 def test_switch_error_cannot_use_record_verifier(self):
  self.original['error']='tab-context-changed-during-read'
  with self.assertRaisesRegex(ValueError,'worker-proof'):self.runrepair()
 def test_first_sender_baseline_does_not_renew_progress(self):
  self.state['semantic_progress']['dispatch0'].pop(self.journal['path']);self.state['events'][-1]['journal']=self.journal['path'];old=self.state['last_progress_at'];self.runrepair();self.assertEqual(self.state['last_progress_at'],old);self.assertTrue(self.state['events'][-1]['initial_sender_baseline_without_progress_renewal']);self.assertIn(self.journal['path'],self.state['semantic_progress']['dispatch0'])
 def test_first_sender_baseline_needs_exact_attention_and_binding(self):
  self.state['semantic_progress']['dispatch0'].pop(self.journal['path'])
  with self.assertRaisesRegex(ValueError,'original-sender-attention'):self.runrepair()
  self.state['events'][-1]['journal']=self.journal['path'];self.report['original_binding']={'wrong':True};self.reportpath.write_text(json.dumps(self.report))
  with self.assertRaisesRegex(ValueError,'original-sender-attention'):self.runrepair()
if __name__=='__main__':unittest.main()
