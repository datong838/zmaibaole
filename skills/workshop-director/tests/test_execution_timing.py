"""Synthetic telemetry fixtures only. Never execute platform or messenger APIs."""
import copy,hashlib,json,sys,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import execution_timing as t
class Clock:
 def __init__(self):self.n=100.;self.base=datetime(2026,10,22,0,0,tzinfo=timezone.utc);self.b='public-boot-1'
 def monotonic(self):return self.n
 def wall(self):return self.base+timedelta(seconds=self.n-100)
 def boot(self):return self.b
class TimingTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.clock=Clock();self.order=self.write('order.json',{'kind':'synthetic-order'});self.run=self.root/'run.json';self.sender_dir=self.root/'sender-jobs';self.sender_dir.mkdir();self.sender_patch=patch.object(t,'SENDER_DIRECTORY',self.sender_dir);self.sender_patch.start();self.addCleanup(self.sender_patch.stop);self.scope={'workflow':'daily-comment-stats','companies':[{'company':'synthetic','groupid':'123'}],'start':'2026-10-20','end_exclusive':'2026-10-21','test_target':t.TARGET,'expected_send_keys':['one','two']}
 def write(self,name,value):p=self.root/name;p.write_text(json.dumps(value));return t.ref(p)
 def start(self,**kw):return t.start(self.run,'test-run',self.order,self.scope,clock=self.clock,**kw)
 def receipt(self,keys=('one','two'),created=None):
  jobs=[]
  for key in keys:
   payload={'key':key,'target':t.TARGET,'kind':'group','scope':'test','type':'file'};j={'job':payload,'fingerprint':hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'complete','sent':True,'ui_confirmed':True,'created_at':created or json.loads(self.run.read_text())['wall_started_at'],'completed_at':self.clock.wall().isoformat(),'events':[{'stage':'ui-confirmed'}]};p=t.sender_path(key);p.write_text(json.dumps(j));jobs.append(t.ref(p))
  return self.write('completion.json',{'kind':'workflow-client-confirmation-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'client_jobs':jobs})
 def finish(self,**kw):return t.finish(self.run,'client-confirmed',self.receipt(),clock=self.clock,**kw)
 def test_fresh_all_expected_clients_within_30_pass_and_overlapping_stages_not_summed(self):
  self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock);t.stage(self.run,'a','webpage-acquisition',clock=self.clock);self.clock.n=105;t.stage(self.run,'b','artifact-generation',clock=self.clock);self.clock.n=120;t.stage(self.run,'a','webpage-acquisition',end=True,clock=self.clock);self.clock.n=125;t.stage(self.run,'b','artifact-generation',end=True,clock=self.clock);r=self.finish();self.assertTrue(r['acceptance_pass']);self.assertEqual(r['elapsed_seconds'],25);self.assertFalse(r['stage_durations_are_additive']);self.assertEqual(sum(x['elapsed_seconds'] for x in json.loads(self.run.read_text())['stages']),40)
 def test_overdeadline_does_not_cancel_or_replay_and_development_never_passes(self):
  self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock);self.clock.n=131;r=self.finish();self.assertTrue(r['deadline_exceeded']);self.assertFalse(r['acceptance_pass']);self.assertEqual(r['outcome'],'client-confirmed');self.assertTrue(r['measurement_only_no_cancel_or_replay'])
  self.run=self.root/'development.json';self.clock.n=200
  for p in self.sender_dir.glob('*.json'):p.unlink()
  self.start();t.mark_web_action(self.run,clock=self.clock);self.clock.n=201;r=self.finish();self.assertFalse(r['acceptance_pass'])
 def test_no_end_or_no_first_web_boundary_cannot_pass(self):
  r=self.start(mode='acceptance');self.assertFalse(r['acceptance_pass']);self.clock.n=105
  with self.assertRaisesRegex(t.TimingError,'boundary-not-measured'):self.finish()
  r=t.finish(self.run,'incomplete',reason='source acquisition stopped',clock=self.clock);self.assertFalse(r['acceptance_pass']);self.assertFalse(r['full_workflow_measured'])
 def test_duplicate_start_keeps_clock_and_scope_cannot_change(self):
  self.start(mode='acceptance');self.clock.n=120;self.assertEqual(self.start(mode='acceptance')['elapsed_seconds'],20)
  self.scope['end_exclusive']='2026-10-22'
  with self.assertRaises(t.TimingError):self.start(mode='acceptance')
 def test_boot_change_and_monotonic_rollback_fail_closed(self):
  self.start();self.clock.b='new-boot'
  with self.assertRaisesRegex(t.TimingError,'boot-changed'):t.mark_web_action(self.run,clock=self.clock)
  self.clock.b='public-boot-1';self.clock.n=90
  with self.assertRaisesRegex(t.TimingError,'monotonic-invalid'):t.mark_web_action(self.run,clock=self.clock)
 def test_subset_duplicates_payload_tamper_and_old_send_rejected(self):
  self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock);self.clock.n=105
  with self.assertRaisesRegex(t.TimingError,'job-set-mismatch'):t.finish(self.run,'client-confirmed',self.receipt(keys=('one',)),clock=self.clock)
  with self.assertRaisesRegex(t.TimingError,'old-send'):t.finish(self.run,'client-confirmed',self.receipt(created=(self.clock.base-timedelta(days=1)).isoformat()),clock=self.clock)
  r=self.receipt();s=json.loads(Path(r['path']).read_text());s['client_jobs'].append(s['client_jobs'][0]);r=self.write('duplicate.json',s)
  with self.assertRaises(t.TimingError):t.finish(self.run,'client-confirmed',r,clock=self.clock)
  r=self.receipt();p=t.sender_path('one');job=json.loads(p.read_text());job['job']['target']='wrong';p.write_text(json.dumps(job))
  with self.assertRaisesRegex(t.TimingError,'evidence-changed'):t.finish(self.run,'client-confirmed',r,clock=self.clock)
 def test_resume_can_confirm_original_job_but_cannot_claim_fresh_acceptance(self):
  prior=self.write('prior.json',{'kind':'original-order-stop'});self.start(mode='acceptance',origin='resume',resumed_from=prior);self.clock.n=105;r=t.finish(self.run,'client-confirmed',self.receipt(created=(self.clock.base-timedelta(days=1)).isoformat()),clock=self.clock);self.assertEqual(r['origin'],'resume');self.assertFalse(r['acceptance_pass']);self.assertFalse(r['full_workflow_measured'])
 def test_zero_data_separate_real_acquisition_refs_no_send_success(self):
  self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock);self.clock.n=104;raw=self.write('raw.json',{'synthetic':True,'observed_count':0});a={'workflow':self.scope['workflow'],'run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[raw],'groupid':'123','observed_at':self.clock.wall().isoformat()};ar=self.write('acquisition.json',a);receipt={'kind':'workflow-no-data-completion-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'fixture':False,'live':True,'row_count':0,'acquisitions':[ar]};r=t.finish(self.run,'no-data-complete',self.write('zero.json',receipt),clock=self.clock);self.assertEqual(r['outcome'],'no-data-complete');self.assertTrue(r['full_workflow_measured']);self.assertFalse(r['acceptance_pass']);self.assertFalse(json.loads(self.run.read_text())['completion_detail']['client_send_success'])
 def test_zero_boolean_without_pinned_collection_or_expected_company_is_rejected(self):
  self.start();t.mark_web_action(self.run,clock=self.clock);receipt={'kind':'workflow-no-data-completion-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'fixture':False,'live':True,'row_count':0}
  with self.assertRaisesRegex(t.TimingError,'acquisition-evidence-required'):t.finish(self.run,'no-data-complete',self.write('zero.json',receipt),clock=self.clock)
 def test_cli_cross_process_same_boot_start_and_finish_incomplete(self):
  import subprocess
  scope=self.root/'scope.json';cli_scope=copy.deepcopy(self.scope);cli_scope['expected_send_keys']=['timing-cli-synthetic-'+self.root.name];scope.write_text(json.dumps(cli_scope));cli=Path(t.__file__)
  args=[sys.executable,'-I','-B',str(cli)]
  parent_before=t.Clock().monotonic()
  first=subprocess.run(args+['start','--run',str(self.run),'--run-id','cli-run','--work-order',self.order['path'],'--scope',str(scope),'--mode','acceptance','--before-first-webpage-action'],capture_output=True,text=True)
  self.assertEqual(first.returncode,0,first.stdout+first.stderr);self.assertFalse(json.loads(first.stdout)['acceptance_pass']);parent_after=t.Clock().monotonic();self.assertTrue(parent_before<=json.loads(self.run.read_text())['start_monotonic']<=parent_after)
  import time;time.sleep(.15)
  status=subprocess.run(args+['status','--run',str(self.run)],capture_output=True,text=True);self.assertEqual(status.returncode,0,status.stdout);self.assertGreaterEqual(json.loads(status.stdout)['elapsed_seconds'],.15)
  second=subprocess.run(args+['finish','--run',str(self.run),'--outcome','incomplete','--reason','synthetic collection stopped'],capture_output=True,text=True)
  self.assertEqual(second.returncode,0,second.stdout+second.stderr);self.assertEqual(json.loads(second.stdout)['outcome'],'incomplete');self.assertFalse(json.loads(second.stdout)['acceptance_pass'])
 def test_same_second_preexisting_sender_job_blocks_fresh_start(self):
  t.sender_path('one').write_text(json.dumps({'created_at':self.clock.wall().isoformat(),'status':'complete'}))
  with self.assertRaisesRegex(t.TimingError,'preexists-use-resume'):self.start(mode='acceptance')
  self.assertFalse(self.run.exists())
 def test_original_run_repeated_start_does_not_rescan_newly_created_jobs(self):
  self.start(mode='acceptance');original=json.loads(self.run.read_text());t.sender_path('one').write_text('{}');self.clock.n=102
  r=self.start(mode='acceptance');self.assertEqual(r['elapsed_seconds'],2);self.assertEqual(json.loads(self.run.read_text()),original)
 def test_noncanonical_client_job_ref_is_rejected_even_if_all_fields_match(self):
  self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock);self.clock.n=104;r=self.receipt();receipt=json.loads(Path(r['path']).read_text());copied=self.root/'copied-job.json';copied.write_bytes(t.sender_path('one').read_bytes());receipt['client_jobs'][0]=t.ref(copied)
  with self.assertRaisesRegex(t.TimingError,'canonical-client-job'):t.finish(self.run,'client-confirmed',self.write('copied.json',receipt),clock=self.clock)
 def test_start_prechecks_are_included_not_moved_before_timer(self):
  original=t.pinned
  def delayed(ref):self.clock.n+=7;return original(ref)
  with patch.object(t,'pinned',side_effect=delayed):r=self.start(mode='acceptance')
  state=json.loads(self.run.read_text());self.assertEqual(state['start_monotonic'],100);self.assertEqual(r['elapsed_seconds'],7);self.assertTrue(r['startup_prechecks_included']);self.assertFalse(r['final_timing_ledger_write_in_elapsed'])
 def dynamic_start(self,workflow='violation-notifier',**kw):
  self.scope.pop('expected_send_keys');self.scope['delivery_contract']=t.DYNAMIC_DELIVERY;self.scope['workflow']=workflow;self.start(mode='acceptance',**kw);t.mark_web_action(self.run,clock=self.clock)
 def manifest(self,keys=('one','two'),workflow=None):
  workflow=workflow or self.scope['workflow'];orders=[]
  for i,key in enumerate(keys):
   f=self.root/(key+'.xlsx');f.write_bytes(('synthetic-'+key).encode());sha=hashlib.sha256(f.read_bytes()).hexdigest()
   if workflow=='daily-comment-stats':
    orders.append({'part':str(i),'payload':str(f),'sha256':sha,'prepare_argv':[sys.executable,'/unused/messenger.py','prepare','--key',key,'--kind','group','--target',t.TARGET,'--scope','test','--file',str(f)]})
   else:orders.append({'key':key,'kind':'group','target':t.TARGET,'scope':'test','type':'file','file':str(f),'file_sha256':sha})
  plan={'workflow':workflow,'company':'synthetic','date_range':{'start':self.scope['start'],'end':'2026-10-20'},'test_target':t.TARGET,'orders':orders} if workflow=='daily-comment-stats' else orders
  planref=self.write('native-plan.json',plan);source=self.write('plan-source.json',{'synthetic-source':True});return self.write('delivery.json',{'kind':'workflow-delivery-manifest-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source_refs':[source],'source_plans':[planref],'expected_send_keys':list(keys)})
 def dynamic_receipt(self,*,old=False):
  state=json.loads(self.run.read_text());refs=[]
  for o in state['delivery']['orders']:
   payload={**o['sender_payload'],'version':'1.0.0'};j={'job':payload,'fingerprint':hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'complete','sent':True,'ui_confirmed':True,'created_at':(self.clock.base-timedelta(days=1)).isoformat() if old else self.clock.wall().isoformat(),'completed_at':self.clock.wall().isoformat(),'events':[{'stage':'ui-confirmed'}]};p=t.sender_path(payload['key']);p.write_text(json.dumps(j));refs.append(t.ref(p))
  return self.write('dynamic-completion.json',{'kind':'workflow-client-confirmation-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'delivery_manifest_sha256':state['delivery']['manifest_sha256'],'client_jobs':refs})
 def test_dynamic_seal_keeps_original_start_and_business_scope_hash(self):
  self.dynamic_start();original=json.loads(self.run.read_text());self.clock.n=118;manifest=self.manifest();r=t.seal_delivery(self.run,manifest,clock=self.clock);sealed=json.loads(self.run.read_text());self.assertEqual(sealed['scope'],original['scope']);self.assertEqual(sealed['scope_sha256'],original['scope_sha256']);self.assertEqual(sealed['start_monotonic'],100);self.assertEqual(r['elapsed_seconds'],18);self.assertTrue(r['delivery_sealed']);self.clock.n=125;r=t.finish(self.run,'client-confirmed',self.dynamic_receipt(),clock=self.clock);self.assertTrue(r['acceptance_pass']);self.assertEqual(r['elapsed_seconds'],25)
 def test_dynamic_unsealed_cannot_finish_and_empty_plan_does_not_mean_unknown_complete(self):
  self.dynamic_start();receipt=self.receipt()
  with self.assertRaisesRegex(t.TimingError,'manifest-unsealed'):t.finish(self.run,'client-confirmed',receipt,clock=self.clock)
  for p in self.sender_dir.glob('*.json'):p.unlink()
  with self.assertRaisesRegex(t.TimingError,'complete-native-plan-required'):t.seal_delivery(self.run,self.manifest(keys=()),clock=self.clock)
  self.assertEqual(json.loads(self.run.read_text())['delivery']['status'],'unsealed')
 def test_dynamic_prepared_unsent_and_preexisting_sent_jobs_both_rejected(self):
  self.dynamic_start();manifest=self.manifest()
  for status in ('running','complete','unknown'):
   t.sender_path('one').write_text(json.dumps({'status':status,'created_at':self.clock.wall().isoformat()}))
   with self.subTest(status=status),self.assertRaisesRegex(t.TimingError,'job-preexists-use-resume'):t.seal_delivery(self.run,manifest,clock=self.clock)
  self.assertEqual(json.loads(self.run.read_text())['delivery']['status'],'unsealed')
 def test_dynamic_seal_once_idempotent_after_sender_prepare_and_no_reseal(self):
  self.dynamic_start();manifest=self.manifest();t.seal_delivery(self.run,manifest,clock=self.clock);original=json.loads(self.run.read_text());self.dynamic_receipt();self.clock.n=110;self.assertTrue(t.seal_delivery(self.run,manifest,clock=self.clock)['delivery_sealed']);self.assertEqual(json.loads(self.run.read_text()),original)
  other=self.write('other-manifest.json',json.loads(Path(manifest['path']).read_text()))
  with self.assertRaisesRegex(t.TimingError,'already-sealed-conflict'):t.seal_delivery(self.run,other,clock=self.clock)
 def test_dynamic_all_three_native_order_formats_and_complete_key_matching(self):
  for workflow in t.FLOWS:
   with self.subTest(workflow=workflow):
    self.run=self.root/(workflow+'.json');self.scope.pop('delivery_contract',None);self.scope['expected_send_keys']=[];self.dynamic_start(workflow);manifest=self.manifest();t.seal_delivery(self.run,manifest,clock=self.clock);state=json.loads(self.run.read_text());self.assertEqual(state['delivery']['keys'],['one','two'])
    for p in self.sender_dir.glob('*.json'):p.unlink()
 def test_dynamic_manifest_source_payload_or_subset_tamper_rejected(self):
  self.dynamic_start();manifest=self.manifest();m=json.loads(Path(manifest['path']).read_text());m['expected_send_keys']=['one']
  with self.assertRaisesRegex(t.TimingError,'complete-key-set-mismatch'):t.seal_delivery(self.run,self.write('subset.json',m),clock=self.clock)
  t.seal_delivery(self.run,manifest,clock=self.clock);(self.root/'plan-source.json').write_text('{}')
  with self.assertRaisesRegex(t.TimingError,'source-changed'):t.stage(self.run,'later','test-group-send',clock=self.clock)
 def test_dynamic_finish_requires_manifest_hash_and_original_payload(self):
  self.dynamic_start();manifest=self.manifest();t.seal_delivery(self.run,manifest,clock=self.clock);receipt=self.dynamic_receipt();r=json.loads(Path(receipt['path']).read_text());r['delivery_manifest_sha256']='0'*64
  with self.assertRaisesRegex(t.TimingError,'delivery-hash-mismatch'):t.finish(self.run,'client-confirmed',self.write('bad-hash.json',r),clock=self.clock)
  r=json.loads(Path(receipt['path']).read_text());p=t.sender_path('one');job=json.loads(p.read_text());job['job']['file_sha256']='0'*64;job['fingerprint']=hashlib.sha256(json.dumps(job['job'],ensure_ascii=False,sort_keys=True).encode()).hexdigest();p.write_text(json.dumps(job));r['client_jobs'][0]=t.ref(p)
  with self.assertRaisesRegex(t.TimingError,'delivery-payload-mismatch'):t.finish(self.run,'client-confirmed',self.write('bad-payload.json',r),clock=self.clock)
 def test_dynamic_resume_may_reference_existing_keys_never_fresh_pass(self):
  prior=self.write('prior.json',{'synthetic':True});self.dynamic_start(origin='resume',resumed_from=prior);manifest=self.manifest();t.sender_path('one').write_text('{}');t.seal_delivery(self.run,manifest,clock=self.clock);r=t.finish(self.run,'client-confirmed',self.dynamic_receipt(old=True),clock=self.clock);self.assertFalse(r['acceptance_pass']);self.assertFalse(r['full_workflow_measured'])
 def test_sealed_state_cannot_shrink_keys_or_downgrade_contract(self):
  self.dynamic_start();manifest=self.manifest();t.seal_delivery(self.run,manifest,clock=self.clock);original=json.loads(self.run.read_text())
  for mode in ('keys','contract'):
   s=copy.deepcopy(original)
   if mode=='keys':s['delivery']['keys']=['one']
   else:s['delivery']['contract']='legacy-fixed-keys-v1'
   self.run.write_text(json.dumps(s))
   with self.subTest(mode=mode),self.assertRaises(t.TimingError):t.stage(self.run,'read','webpage-acquisition',clock=self.clock)
 def test_dynamic_zero_acquisition_ends_separately_without_sealing_a_send_plan(self):
  self.dynamic_start();self.clock.n=105;raw=self.write('raw.json',{'synthetic':True});a={'workflow':self.scope['workflow'],'run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[raw],'groupid':'123','observed_at':self.clock.wall().isoformat()};receipt={'kind':'workflow-no-data-completion-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'fixture':False,'live':True,'row_count':0,'acquisitions':[self.write('zero-acquisition.json',a)]};r=t.finish(self.run,'no-data-complete',self.write('dynamic-zero.json',receipt),clock=self.clock);self.assertEqual(r['outcome'],'no-data-complete');self.assertFalse(r['delivery_sealed']);self.assertFalse(r['acceptance_pass']);self.assertTrue(r['full_workflow_measured'])
 def test_unversioned_old_clock_record_cannot_be_treated_as_current_timing(self):
  self.start();s=json.loads(self.run.read_text());s.pop('monotonic_clock');self.run.write_text(json.dumps(s))
  with self.assertRaisesRegex(t.TimingError,'clock-contract-missing'):t.mark_web_action(self.run,clock=self.clock)
 def test_actual_saved_daily_outbox_native_format_normalizes_all_three_parts(self):
  root=Path(__file__).resolve().parents[3];plan=root/'work/2026-10-21/daily/01_烟台一成教育文化咨询有限公司/test-notifications/orders.json';raw=json.loads(plan.read_text());orders=[t.normalized_order(o,'daily-comment-stats') for o in raw['orders']];self.assertEqual(len(orders),3);self.assertEqual([o['sender_payload']['type'] for o in orders],['file','file','text']);self.assertEqual(len({o['key'] for o in orders}),3)
 def ranged_start(self,workflow='daily-comment-stats'):
  self.scope={'workflow':workflow,'company_ranges':[{'company':'synthetic','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-21'},{'company':'second','groupid':'456','start':'2026-10-20','end_exclusive':'2026-10-21'}],'test_target':t.TARGET,'delivery_contract':t.DYNAMIC_DELIVERY};self.start(mode='acceptance');t.mark_web_action(self.run,clock=self.clock)
 def ranged_manifest(self):
  plans=[]
  for i,c in enumerate(self.scope['company_ranges']):
   f=self.root/('ranged-'+str(i)+'.xlsx');f.write_bytes(b'synthetic');key='ranged-'+str(i);plan={'workflow':'daily-comment-stats','company':c['company'],'date_range':{'start':c['start'],'end':'2026-10-20'},'test_target':t.TARGET,'orders':[{'payload':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'prepare_argv':[sys.executable,'/unused/messenger.py','prepare','--key',key,'--kind','group','--target',t.TARGET,'--scope','test','--file',str(f)]}]};plans.append(self.write('ranged-plan-'+str(i)+'.json',plan))
  return self.write('ranged-delivery.json',{'kind':'workflow-delivery-manifest-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'company_ranges':copy.deepcopy(self.scope['company_ranges']),'source_refs':[self.order],'source_plans':plans,'expected_send_keys':['ranged-0','ranged-1']})
 def test_two_company_ranges_seal_and_finish_one_original_clock(self):
  self.ranged_start();original=json.loads(self.run.read_text());self.clock.n=117;t.seal_delivery(self.run,self.ranged_manifest(),clock=self.clock);self.clock.n=126;r=t.finish(self.run,'client-confirmed',self.dynamic_receipt(),clock=self.clock);self.assertTrue(r['acceptance_pass']);self.assertEqual(r['elapsed_seconds'],26);state=json.loads(self.run.read_text());self.assertEqual(state['scope'],original['scope']);self.assertEqual(state['scope_sha256'],original['scope_sha256']);self.assertNotIn('start',state['scope']);self.assertEqual(state['start_monotonic'],100)
 def test_company_range_daily_date_or_manifest_range_mismatch_rejected(self):
  self.ranged_start();manifest=self.ranged_manifest();m=json.loads(Path(manifest['path']).read_text());plan=json.loads(Path(m['source_plans'][1]['path']).read_text());plan['date_range']['start']='2026-10-16';m['source_plans'][1]=self.write('wrong-range-plan.json',plan)
  with self.assertRaisesRegex(t.TimingError,'daily-range-conflict'):t.seal_delivery(self.run,self.write('wrong-range.json',m),clock=self.clock)
  m=json.loads(Path(manifest['path']).read_text());m['company_ranges'][1]['start']='2026-10-16'
  with self.assertRaisesRegex(t.TimingError,'company-ranges-conflict'):t.seal_delivery(self.run,self.write('wrong-company-ranges.json',m),clock=self.clock)
 def test_ranged_scope_duplicate_company_gid_mixed_global_and_fixed_keys_reject(self):
  self.ranged_start()
  for kind in ('company','groupid','global','keys'):
   scope=copy.deepcopy(self.scope)
   if kind in ('company','groupid'):scope['company_ranges'][1][kind]=scope['company_ranges'][0][kind]
   elif kind=='global':scope.update(start='2026-10-16',end_exclusive='2026-10-21')
   else:scope.pop('delivery_contract');scope['expected_send_keys']=[]
   with self.subTest(kind=kind),self.assertRaises(t.TimingError):t.scope_check(scope)
 def test_ranged_zero_requires_each_company_exact_range_not_min_max(self):
  self.ranged_start('violation-notifier');self.clock.n=106;acquisitions=[]
  for i,c in enumerate(self.scope['company_ranges']):
   a={**c,'workflow':self.scope['workflow'],'run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[self.order],'observed_at':self.clock.wall().isoformat()};acquisitions.append(self.write('ranged-zero-'+str(i)+'.json',a))
  receipt={'kind':'workflow-no-data-completion-v1','run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'fixture':False,'live':True,'row_count':0,'acquisitions':acquisitions};wrong=copy.deepcopy(receipt);a=json.loads(Path(acquisitions[1]['path']).read_text());a['start']='2026-10-16';wrong['acquisitions'][1]=self.write('wrong-zero-range.json',a)
  with self.assertRaisesRegex(t.TimingError,'zero-company-range-invalid'):t.finish(self.run,'no-data-complete',self.write('wrong-ranged-zero.json',wrong),clock=self.clock)
  r=t.finish(self.run,'no-data-complete',self.write('ranged-zero.json',receipt),clock=self.clock);self.assertTrue(r['full_workflow_measured']);self.assertFalse(r['acceptance_pass']);self.assertFalse(r['delivery_sealed'])
 def test_legacy_scope_serialization_and_delivery_manifest_shape_unchanged(self):
  for dynamic in (False,True):
   self.run=self.root/('legacy-'+str(dynamic)+'.json');self.scope={'workflow':'daily-comment-stats','companies':[{'company':'synthetic','groupid':'123'}],'start':'2026-10-20','end_exclusive':'2026-10-21','test_target':t.TARGET,'expected_send_keys':['one','two']};before=json.dumps(self.scope,ensure_ascii=False,separators=(',',':')).encode()
   if dynamic:self.dynamic_start('daily-comment-stats');t.seal_delivery(self.run,self.manifest(),clock=self.clock)
   else:self.start()
   saved=json.loads(self.run.read_text());expected=json.loads(before)
   if dynamic:expected.pop('expected_send_keys');expected['delivery_contract']=t.DYNAMIC_DELIVERY
   self.assertEqual(saved['scope'],expected);self.assertEqual(saved['scope_sha256'],t.digest(expected));self.assertNotIn('company_ranges',saved['scope']);self.assertEqual(json.dumps(t.scope_check(expected),ensure_ascii=False,separators=(',',':')).encode(),json.dumps(expected,ensure_ascii=False,separators=(',',':')).encode())
 def test_start_from_order_counts_validation_and_path_derivation_prechecks(self):
  def destination():self.clock.n+=2;return self.run
  def loader(ref):self.clock.n+=7;self.assertEqual(ref,self.order);return {'scope':self.scope,'origin':'fresh','resumed_from':None}
  r=t.start_from_order(destination,'test-run',self.order,loader,mode='acceptance',clock=self.clock);self.assertEqual(json.loads(self.run.read_text())['start_monotonic'],100);self.assertEqual(r['elapsed_seconds'],9);self.clock.n=120;r=t.start_from_order(destination,'test-run',self.order,loader,mode='acceptance',clock=self.clock);self.assertEqual(json.loads(self.run.read_text())['start_monotonic'],100);self.assertEqual(r['elapsed_seconds'],29)
 def test_mixed_zero_exact_company_and_scope_cover_without_fabricated_empty_orders(self):
  self.ranged_start();manifest=self.ranged_manifest();m=json.loads(Path(manifest['path']).read_text());m['source_plans']=m['source_plans'][1:];m['expected_send_keys']=['ranged-1'];c=self.scope['company_ranges'][0];a={'workflow':self.scope['workflow'],'run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[self.order],'observed_at':self.clock.wall().isoformat(),**c};m['zero_acquisitions']=[self.write('mixed-zero.json',a)];t.seal_delivery(self.run,self.write('mixed-manifest.json',m),clock=self.clock);r=t.finish(self.run,'client-confirmed',self.dynamic_receipt(),clock=self.clock);self.assertTrue(r['acceptance_pass']);self.assertEqual(json.loads(self.run.read_text())['delivery']['keys'],['ranged-1'])
 def test_mixed_zero_cannot_duplicate_nonzero_company_or_omit_source_raw(self):
  self.ranged_start();manifest=self.ranged_manifest();m=json.loads(Path(manifest['path']).read_text());c=self.scope['company_ranges'][0];a={'workflow':self.scope['workflow'],'run_id':'test-run','work_order':self.order,'scope_sha256':t.digest(self.scope),'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[self.order],'observed_at':self.clock.wall().isoformat(),**c};m['zero_acquisitions']=[self.write('duplicate-zero.json',a)]
  with self.assertRaisesRegex(t.TimingError,'company-coverage-conflict'):t.seal_delivery(self.run,self.write('duplicate-zero-manifest.json',m),clock=self.clock)
  a['raw_evidence']=[];m['zero_acquisitions']=[self.write('empty-zero.json',a)]
  with self.assertRaisesRegex(t.TimingError,'zero-raw-evidence-required'):t.seal_delivery(self.run,self.write('empty-zero-manifest.json',m),clock=self.clock)
 def test_order_replacement_is_rejected(self):
  self.start();Path(self.order['path']).write_text('{}')
  with self.assertRaisesRegex(t.TimingError,'evidence-changed'):t.mark_web_action(self.run,clock=self.clock)
if __name__=='__main__':unittest.main()
