"""Only temporary ledgers/files and synthetic operator receipts. No UI/process."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import director as d,coordinator as c
import test_director as base
class PendingTests(unittest.TestCase):
 def setUp(self):
  self.h=base.DirectorTest();self.h.setUp();self.addCleanup(self.h.doCleanups);self.root=self.h.root;self.j=self.h.journal;self.s=self.h.state();self.key=self.h.dispatch(self.s);self.at=datetime.fromisoformat(self.s['dispatched_at']);self.originalclock=self.root/'parent.json';self.originalclock.write_text('{"start_monotonic":101,"order":"original"}');self.clockbytes=self.originalclock.read_bytes()
  self.doc={'version':1,'backend':'local-dom-bridge','work_order_id':'original-job','fingerprint':'f'*64,'company':'Test','groupid':'123','date_range':{'start':'2026-10-21','end':'2026-10-21'},'state':'running','phase':'reloadRecords','revision':8,'tab_id':7,'record_tab_id':8,'calls':[{'key':'7:submitExport','phase':'submitExport','at':self.at.isoformat(),'state':'confirmed','command':{'op':'click','tabId':7,'kind':'export','locator':{'by':'selector','value':'#export'}},'result':{'ok':True}}],'checkpoints':[{'stage':'navigation','groupid':'123'}]};self.write();d.heartbeat(self.s,self.key,self.j,now=self.at)
 def write(self):d.atomic(self.j,self.doc)
 def pending(self):
  self.doc['calls'].append({'key':'8:reloadRecords','phase':'reloadRecords','at':self.at.isoformat(),'state':'unknown','command':{'op':'reload-records','tabId':8,'groupid':'123','reloadKey':'original-job-records-8'}});self.write()
 def heartbeat(self,seconds):d.heartbeat(self.s,self.key,self.j,now=self.at+timedelta(seconds=seconds))
 def stopped(self):
  self.pending();self.s.update(phase='attention',attention_reason='semantic-progress-unverified',semantic_progress_error='semantic-unknown-intent',journal=str(self.j.resolve()),journal_sha256=hashlib.sha256(self.j.read_bytes()).hexdigest());self.s['events'].append({'type':'semantic-progress-attention','error':'semantic-unknown-intent','dispatch_id':self.key})
 def terminal(self):
  self.doc['calls'][-1]['state']='confirmed';self.doc['calls'][-1]['result']={'reloaded':True};file=self.root/'actual-shaped.xlsx';file.write_bytes(b'explicit synthetic xlsx bytes');sha=hashlib.sha256(file.read_bytes()).hexdigest();ticket={'ticket':'original-ticket'};receipt={'state':'complete','downloadId':25,'path':str(file),'exists':True,'bytesReceived':file.stat().st_size,'totalBytes':file.stat().st_size};self.doc.update(state='complete',phase='done',exportPending=False,downloadPending=False,download_ticket=ticket,download_receipt=receipt,result={'source':str(file),'src_sha256':sha,'download_verified':True,'download_receipt':receipt,'download_ticket':ticket,**{k:self.doc[k] for k in ('company','groupid','work_order_id','date_range')}});self.doc['checkpoints'].append({'stage':'download-complete','at':(self.at+timedelta(seconds=20)).isoformat(),'path':str(file),'sha256':sha,'ticket':'original-ticket'});self.write()
 def report(self,**changes):
  previous=self.s['semantic_progress'][self.key][str(self.j.resolve())];r={'kind':'supervisor-original-running-intent-reconciliation-v1','dispatch_id':self.key,'day':self.s['day'],'role':d.current(self.s)['role'],'operator_quiescent':True,'browser_quiescent':True,'wecom_quiescent':True,'original_work_orders_only':True,'journal':{'path':str(self.j.resolve()),'sha256':hashlib.sha256(self.j.read_bytes()).hexdigest()},'original_binding':copy.deepcopy(previous['binding']),**changes};p=self.root/'repair.json';d.atomic(p,r);return p
 def test_pending_tail_is_not_progress_and_300_seconds_still_stalls(self):
  self.pending();old=self.s['last_progress_at']
  for sec in (20,100,250):self.doc['calls'][-1]['at']=(self.at+timedelta(seconds=sec)).isoformat();self.write();self.heartbeat(sec);self.assertEqual(self.s['phase'],'running');self.assertEqual(self.s['last_progress_at'],old)
  result=d.inspect(self.s,now=self.at+timedelta(seconds=301));self.assertEqual(result['reason'],'journal-no-progress');self.assertEqual(self.s['attempt'],0)
 def test_pending_new_checkpoint_does_not_refresh_but_removal_rejected(self):
  self.pending();old=self.s['last_progress_at'];self.doc['checkpoints'].append({'stage':'filter','date_range':self.doc['date_range'],'page_filtered':21});self.write();self.heartbeat(20);self.assertEqual(self.s['last_progress_at'],old);self.doc['checkpoints'].pop();self.write();self.heartbeat(30);self.assertEqual(self.s['phase'],'attention')
 def test_non_tail_multi_terminal_unknown_error_hold_and_bad_metadata_rejected(self):
  self.pending();original=copy.deepcopy(self.doc)
  for mode in ('non-tail','multi','terminal','error','hold','naive','phase','key','command','sender','inspection'):
   value=copy.deepcopy(original)
   if mode=='non-tail':value['calls'].append(copy.deepcopy(value['calls'][0]))
   elif mode=='multi':value['calls'][0]['state']='unknown'
   elif mode=='terminal':value['state']='complete';value['phase']='done'
   elif mode=='error':value['last_error']='terminal error'
   elif mode=='hold':value['hold']=True
   elif mode=='naive':value['calls'][-1]['at']='2026-10-22T10:51:41'
   elif mode=='phase':value['phase']='other'
   elif mode=='key':value['calls'][-1]['key']='other'
   elif mode=='sender':value['job']={'key':'mixed-sender'}
   elif mode=='inspection':value['manifest']={'kind':'complaint-draft-inspection-manifest-v1'}
   else:value['calls'][-1]['command']['groupid']='999'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.progress.extract(value,d.ROLES[0])
 def test_confirmed_prefix_or_binding_change_still_attention(self):
  for mode in ('prefix','binding'):
   state=copy.deepcopy(self.s);self.pending() if len(self.doc['calls'])==1 else None
   if mode=='prefix':self.doc['calls'][0]['result']={'changed':True}
   else:self.doc['work_order_id']='changed'
   self.write();d.heartbeat(state,self.key,self.j,now=self.at+timedelta(seconds=20));self.assertEqual(state['phase'],'attention');self.doc['calls'][0]['result']={'ok':True};self.doc['work_order_id']='original-job';self.doc['calls'][-1]['command']['reloadKey']='original-job-records-8'
 def test_completed_original_same_dispatch_restored_no_input_or_clock_reset(self):
  self.stopped();self.terminal();report=self.report();before={k:copy.deepcopy(self.s.get(k)) for k in ('dispatch_id','day','attempt','index','dispatched_at','dispatch_intent_at','tool_receipt')};journal=self.j.read_bytes()
  with patch.object(d,'plan',side_effect=AssertionError('no followup/redispatch')):d.reconcile_running_intent(self.s,self.key,report,now=self.at+timedelta(seconds=40))
  self.assertEqual(self.s['phase'],'running');self.assertEqual({k:self.s.get(k) for k in before},before);self.assertEqual(self.j.read_bytes(),journal);self.assertEqual(self.originalclock.read_bytes(),self.clockbytes);self.assertEqual(self.s['semantic_progress_error'],'semantic-unknown-intent');self.assertTrue(self.s['events'][-1]['diagnostics_preserved']);self.assertFalse(self.s['events'][-1]['business_replayed'])
  with self.assertRaises(ValueError):d.reconcile_running_intent(self.s,self.key,report,now=self.at+timedelta(seconds=41))
 def test_wrong_scope_unacked_nonquiescent_and_stale_sha_rejected(self):
  self.stopped();self.terminal();original=copy.deepcopy(self.s)
  for change in ({'dispatch_id':'other'},{'day':'other'},{'role':'violation_operator'},{'browser_quiescent':False},{'journal':{'path':str(self.j.resolve()),'sha256':'0'*64}},{'original_binding':{}}):
   report=self.report(**change)
   with self.subTest(change=change),self.assertRaises(ValueError):d.reconcile_running_intent(self.s,self.key,report,now=self.at+timedelta(seconds=40))
   self.assertEqual(self.s,original)
  self.s['tool_receipt']=None
  with self.assertRaisesRegex(ValueError,'original-ack'):d.reconcile_running_intent(self.s,self.key,self.report(),now=self.at+timedelta(seconds=40))
 def test_terminal_error_or_unknown_or_bad_download_or_prefix_regression_refused(self):
  self.stopped();self.terminal();original=copy.deepcopy(self.doc)
  for mode in ('error','unknown','file','tokens','calls'):
   self.doc=copy.deepcopy(original)
   if mode=='error':self.doc['error']='failure'
   elif mode=='unknown':self.doc['calls'][-1]['state']='unknown'
   elif mode=='file':self.doc['result']['src_sha256']='0'*64
   elif mode=='tokens':self.doc['checkpoints']=self.doc['checkpoints'][1:]
   else:self.doc['calls'][0]['result']={'changed':True}
   self.write()
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.reconcile_running_intent(self.s,self.key,self.report(),now=self.at+timedelta(seconds=40))
   self.assertEqual(self.s['phase'],'attention')
 def test_coordinator_command_only_archives_report_and_restores_same_lease(self):
  self.stopped();self.terminal();self.doc['checkpoints'][-1]['at']=self.at.isoformat();self.write();report=self.report();dispatch=self.root/'coordinator';dispatch.mkdir();d.atomic(dispatch/'state.json',self.s)
  with patch.object(c,'bind_config',return_value={'active_day':self.s['day']}),patch.object(d,'plan',side_effect=AssertionError('no dispatch')):value=c.command(dispatch,'reconcile-running-intent',dispatch_id=self.key,repair_report=report)
  self.assertEqual(value['phase'],'running');self.assertEqual(value['dispatch_id'],self.key);self.assertEqual(value['attempt'],0);refs=list((dispatch/'operation-receipts').glob('running-reconciliation-*.json'));self.assertEqual(len(refs),1);self.assertEqual(refs[0].read_bytes(),report.read_bytes())
if __name__=='__main__':unittest.main()
