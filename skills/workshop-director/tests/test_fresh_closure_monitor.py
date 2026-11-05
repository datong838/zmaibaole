"""Pure monitor state transitions; deep artifact replay tested separately."""
import copy,importlib.util,json,tempfile,unittest,types
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('closure_director',Path(__file__).resolve().parents[1]/'scripts/director.py')
d=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(d)
class ClosureMonitorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.t=datetime(2026,10,22,10,tzinfo=timezone.utc)
  self.state={'test_target':d.TARGET,'production_enabled':False,'complaint_submission_enabled':False,'phase':'running','index':1,'day':'2026-10-22','attempt':1,'dispatch_id':'original','dispatch_intent_at':self.t.isoformat(),'last_heartbeat':self.t.isoformat(),'last_progress_at':self.t.isoformat(),'events':[]}
  self.path=self.root/'operation.json';self.path.write_text('{}')
  self.extracted={'schema':'complaint-inspection-v1','binding':{'source':'fixed'},'tokens':{'closed':'fixed'}}
  self.closure={'schema':'complaint-inspection-v1','dedup_key':'business-unique','business_binding':{'company':'one','source':'fixed'},'created_at':(self.t+timedelta(seconds=10)).isoformat(),'completed_at':(self.t+timedelta(seconds=30)).isoformat()}
 def beat(self,minute=2,closure=None,path=None):
  with patch.object(d.progress,'extract',return_value=copy.deepcopy(self.extracted)),patch.object(d.progress,'fresh_completed_evidence',return_value=copy.deepcopy(self.closure if closure is None else closure)):
   d.heartbeat(self.state,'original',path or self.path,now=self.t+timedelta(minutes=minute))
 def test_first_closed_observation_counts_actual_completion_not_read_time(self):
  self.beat();self.assertEqual(self.state['last_progress_at'],self.closure['completed_at']);self.assertEqual(self.state['phase'],'running')
 def test_duplicate_path_or_copy_never_renews(self):
  self.beat();first=self.state['last_progress_at'];other=self.root/'copy.json';other.write_text('{}');self.beat(4,path=other);self.assertEqual(self.state['last_progress_at'],first)
  self.extracted['tokens']['another']='new';self.beat(5,path=other);self.assertEqual(self.state['last_progress_at'],first)
 def test_changed_business_binding_is_rejected_before_history_write(self):
  self.beat();history=copy.deepcopy(self.state['semantic_progress']);changed={**self.closure,'business_binding':{'company':'two'}};self.beat(3,changed)
  self.assertEqual(self.state['phase'],'attention');self.assertEqual(self.state['semantic_progress'],history)
 def test_old_or_unsupported_completion_pins_baseline_without_refresh(self):
  with patch.object(d.progress,'extract',return_value=self.extracted),patch.object(d.progress,'fresh_completed_evidence',return_value=None):d.heartbeat(self.state,'original',self.path,now=self.t+timedelta(minutes=4))
  self.assertEqual(self.state['last_progress_at'],self.t.isoformat())
 def test_future_completion_rejected_before_history_write(self):
  self.closure['completed_at']=(self.t+timedelta(hours=2)).isoformat();self.beat();self.assertEqual(self.state['phase'],'attention');self.assertNotIn('semantic_progress',self.state)
 def test_deep_proof_failure_attention_without_progress(self):
  with patch.object(d.progress,'extract',return_value=self.extracted),patch.object(d.progress,'fresh_completed_evidence',side_effect=ValueError('source-changed')):d.heartbeat(self.state,'original',self.path,now=self.t+timedelta(minutes=4))
  self.assertEqual(self.state['phase'],'attention');self.assertEqual(self.state['last_progress_at'],self.t.isoformat())
 def test_later_distinct_business_closure_can_advance(self):
  self.beat();second={**self.closure,'dedup_key':'second','completed_at':(self.t+timedelta(minutes=3)).isoformat()};self.beat(4,second)
  self.assertEqual(self.state['last_progress_at'],second['completed_at']);self.assertEqual(len(self.state['verified_business_closures']['original']),2)
 def test_missing_progress_falls_back_to_dispatch_not_new_heartbeat(self):
  self.state.pop('last_progress_at');self.beat();self.assertEqual(self.state['last_progress_at'],self.closure['completed_at'])
if __name__=='__main__':unittest.main()
