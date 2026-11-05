"""A durable file paste is in flight, never completed progress or retry authority."""
import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(D));spec=importlib.util.spec_from_file_location('sender_pending_semantic',D/'semantic_progress.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PendingFileTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);p=Path(self.tmp.name)/'report.xlsx';p.write_bytes(b'synthetic');job={'key':'same-original-key','kind':'group','scope':'test','target':'测试群请忽略','type':'file','file':str(p),'file_name':p.name,'file_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};self.source=p
  self.s={'job':job,'fingerprint':hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'unknown','phase':'file-confirm','pid':123,'baseline':0,'paste_empty_composer_verified':True,'send_intent_at':'2026-10-22T21:03:38+08:00','last_read':{'read_scope':'application-windows-complete','truncated':False,'truncation_reason':None},'events':[{'stage':'recipient-verified','name':'测试群请忽略','kind':'group'},{'stage':'send-intent','at':'2026-10-22T21:03:38+08:00','file':p.name,'sha256':job['file_sha256']}]}
 def extract(self,s=None):return m.extract(s or self.s,'daily_stats_operator')
 def test_inflight_paste_adds_no_completed_token(self):
  running=copy.deepcopy(self.s);running.update(phase='stage',status='running');running['events'].pop();before=self.extract(running);after=self.extract();self.assertEqual(before['tokens'],after['tokens']);self.assertEqual(set(after['tokens']),{'recipient-verified'})
 def test_malformed_or_unowned_paste_rejected(self):
  for mode in ('pid','baseline','empty','missing','twice','hash','phase','read','naive'):
   s=copy.deepcopy(self.s)
   if mode=='pid':s['pid']=None
   if mode=='baseline':s.pop('baseline')
   if mode=='empty':s['paste_empty_composer_verified']=False
   if mode=='missing':s['events'].pop()
   if mode=='twice':s['events'].append(copy.deepcopy(s['events'][-1]))
   if mode=='hash':s['events'][-1]['sha256']='0'*64
   if mode=='phase':s['phase']='unexpected-phase'
   if mode=='read':s['last_read']['truncated']=True
   if mode=='naive':s['send_intent_at']='2026-10-22T21:03:38'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.extract(s)
 def test_original_source_changed_rejected(self):
  self.source.write_bytes(b'changed')
  with self.assertRaises(ValueError):self.extract()
 def test_errors_and_terminal_outcomes_still_stop(self):
  for change in ({'error':'send-outcome-unknown'},{'last_error':'x'},{'status':'abandoned'},{'status':'failed'},{'hold':True}):
   with self.subTest(change=change),self.assertRaises(ValueError):self.extract({**self.s,**change})
 def test_existing_verify_phase_is_unchanged(self):
  s=copy.deepcopy(self.s);s.update(phase='verify-sent',checks=0);self.extract(s);s['checks']=5
  with self.assertRaises(ValueError):self.extract(s)
if __name__=='__main__':unittest.main()
