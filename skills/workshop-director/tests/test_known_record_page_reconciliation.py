"""Director boundary tests with a mocked typed verifier; no browser or live state."""
import copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
DIR=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(DIR))
spec=importlib.util.spec_from_file_location('record_repair_director',DIR/'director.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class RecordRepairDirectorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.at=datetime.now(timezone.utc);start=self.at-timedelta(seconds=1000);self.original={'version':1,'backend':'local-dom-bridge','work_order_id':'w','fingerprint':'f','company':'公司','groupid':'1','date_range':{'start':'2026-10-21','end':'2026-10-21'},'state':'running','phase':'pollRecords','checkpoints':[],'calls':[{'key':'30:submitExport','phase':'submitExport','state':'confirmed','command':{'op':'click'}}],'last_error':{'code':'record-pagination-incomplete','message':'record-pagination-incomplete'}}
  self.originalref=self.save('original.json',self.original);self.proof=self.save('proof.json',{'at':self.at.isoformat()});self.current=copy.deepcopy(self.original);self.current.pop('last_error');self.current['record_page_recovery']=self.proof;self.journal=self.save('workflow.json',self.current);prior=d.progress.extract(self.current,'daily_stats_operator',self.journal['path'])
  self.state={'test_target':'测试群请忽略','production_enabled':False,'complaint_submission_enabled':False,'index':0,'phase':'attention','day':'2026-10-22','dispatch_id':'dispatch0','dispatch_intent_at':(start-timedelta(seconds=140)).isoformat(),'dispatched_at':(start-timedelta(seconds=139)).isoformat(),'tool_receipt':{'ack':True},'queue':[{'role':'daily_stats_operator','workflow':'daily-comment-stats'}],'cursor':0,'events':[{'type':'dispatched','id':'dispatch0'},{'type':'semantic-progress-attention','dispatch_id':'dispatch0','at':start.isoformat(),'error':'semantic-terminal-error'}],'attention_reason':'semantic-progress-unverified','semantic_progress_error':'semantic-terminal-error','journal':self.journal['path'],'semantic_progress':{'dispatch0':{self.journal['path']:prior}},'last_progress_at':(start-timedelta(seconds=120)).isoformat(),'attempt':0,'parent_clock':367008.987475}
  self.report={'kind':'supervisor-known-record-page-reconciliation-v1','dispatch_id':'dispatch0','day':'2026-10-22','role':'daily_stats_operator','journal':self.journal,'original_binding':prior['binding'],'original_journal':self.originalref,'worker_recovery':self.proof,**{k:True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')}};self.reportpath=Path(self.save('repair.json',self.report)['path'])
  self.verifier=types.SimpleNamespace(__file__=str(DIR.parents[1]/'douyin-laike-operator/scripts/export_record_page_recovery.py'),verify_recovered=self.verify)
 def save(self,name,doc):
  p=self.root/name;p.write_text(json.dumps(doc,ensure_ascii=False));return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 def verify(self,document,proof):
  self.assertEqual(document,self.current);self.assertEqual(proof,self.proof);return {'kind':'verified-export-record-page-recovery-v1','original_journal':self.originalref,'proof':self.proof,'original_error':self.original['last_error']}
 def runrepair(self):
  original_import=__import__('importlib').import_module
  def lookup(name,*args):return self.verifier if name=='export_record_page_recovery' else original_import(name,*args)
  with patch('importlib.import_module',side_effect=lookup):return d.reconcile_running_intent(self.state,'dispatch0',self.reportpath,now=self.at)
 def test_same_dispatch_clock_and_progress_preserved(self):
  old=copy.deepcopy(self.state);self.runrepair();self.assertEqual(self.state['phase'],'running')
  for k in ('dispatch_id','dispatch_intent_at','dispatched_at','tool_receipt','attempt','parent_clock','last_progress_at'):self.assertEqual(self.state[k],old[k])
  self.assertEqual(self.state['events'][-1]['type'],'supervisor-known-record-page-reconciled');self.assertAlmostEqual(d.inspect(self.state,now=self.at)['journal_idle_seconds'],120,places=3)
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
   if mode=='prefix':self.state['semantic_progress']['dispatch0'][self.journal['path']]['confirmed_call_prefix']=['changed']
   if mode=='kind':r['kind']='generic-clear-error'
   self.reportpath.write_text(json.dumps(r))
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.runrepair()
 def test_switch_error_cannot_use_record_verifier(self):
  self.original['last_error']['code']=self.original['last_error']['message']='tab-context-changed-during-read'
  with self.assertRaisesRegex(ValueError,'worker-proof'):self.runrepair()
if __name__=='__main__':unittest.main()
