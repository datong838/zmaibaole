"""Synthetic TEMP date/body/receipt fixtures. No real business or UI invocation."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preselected_range_production_loader as loader
m,q,d,z,sem=loader.recovery,loader.query,loader.detail,loader.zero,loader.semantic;g=m.g
import test_bridge_navigation as nf
import test_governance_dom as dom
import zero_source_fixtures as zf
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.statepath=self.root/'records-query.json';self.jp=self.root/'navigation-job.json';self.reads=[]
  f=nf.NavigationTests();f.setUp();self.addCleanup(f.doCleanups);self.job=copy.deepcopy(f.job);self.job.update(start='2026-10-21',end_exclusive='2026-10-22');plan=copy.deepcopy(f.plan);plan.update(start='2026-10-21',end_exclusive='2026-10-22');pp=self.put(self.root/'plan.json',plan);self.job.update(plan_path=pp['path'],plan_sha256=pp['sha256']);self.jr=self.put(self.jp,self.job)
  self.closed=zf.records_tree();g.date_input(self.closed)['attributes']['value']='2026/10/21 ～ 2026/10/21';self.open=dom.with_calendar(copy.deepcopy(self.closed));views=g.calendar(self.open);october=g.one([v for v in views if v['month']==10],'synthetic-october');item=october['cells']['2026-10-20'];parent=g.one([n for n in g.nodes(self.open) if n.get('tag')=='span' and n.get('children')==[item]],'synthetic-parent');item['name']=parent['name']='21';item['attributes']['class']+=' governance_merchant-date-selected governance_merchant-date-state-single';parent['attributes']['class']+=' governance_merchant-date-selected governance_merchant-date-state-single'
  self.refs=[];self.raws=[]
  for i in range(7):
   raw=self.raw(self.closed if i==0 else self.open,at=f'2026-10-22T10:00:{i:02d}+00:00');self.raws.append(raw);self.refs.append(self.put(self.root/'records-query-evidence'/f'{i:04d}.json',raw))
  calls=[];plan=g.QueryPlan(self.job['start'],self.job['end_exclusive'])
  for i,phase in enumerate(('open-date','select-start')):
   command={**plan.next(self.raws[i]['tree'],{'phase':phase})['command'],'tabId':5};target=g.one([n for n in g.nodes(self.raws[i]['tree']) if n.get('selector')==command['locator']['value']],'synthetic-command-target');calls.append({'state':'confirmed','command':command,'before':self.refs[i],'intent_at':f'2026-10-22T10:00:0{i}.500000+00:00','postcondition':None,'result':{'kind':'filter','version':m.nav.VERSION,'clicked':copy.deepcopy(target)}})
  pending={'checks':5,'max_checks':5,'original_call_index':1,'last_observation':self.refs[-1],'reason':'governance-start-date-selection-not-observed'}
  self.s={'fingerprint':m.nav.tag(self.job),'tab_id':5,'approved_version':m.nav.VERSION,'phase':'select-end','calls':calls,'pages':[],'observations':self.refs,'last_observation':self.refs[-1],'business_progress_changed':False,'profile_accepted':False,'query_job_binding':{'kind':'governance-query-job-binding-v1','job':self.jr,'fingerprint':m.nav.tag(self.job),'tab_id':5,'query_state_path':str(self.statepath),'window_id':3},'settled_actions':[{'checks':1,'max_checks':5,'original_call_index':0,'last_observation':self.refs[1],'reason':'governance-calendar-not-mounted','settled_at':'2026-10-22T10:00:01.100000+00:00'}],'needs_changed_tree':self.refs[1],'read_only_settling':pending,'waiting_for':'confirmed-action-settling-exhausted-supervisor-reconcile-original-journal','settling_exhausted':True};self.save();self.fresh=self.raw(self.open,at='2026-10-22T10:01:00+00:00')
 def put(self,path,v):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(m.encoded(v));return {'path':str(path),'sha256':m.sha(path.read_bytes())}
 def save(self):self.statepath.write_bytes(m.encoded(self.s));self.original=self.statepath.read_bytes();self.digest=m.sha(self.original)
 def raw(self,tree,at):return {'source':'local-dom-bridge','observed_at':at,'tab_id':5,'tab':{'tabId':5,'windowId':3,'allowed':True,'url':'https://life.douyin.com'+g.RECORDS+'?groupid=123'},'tree':copy.deepcopy(tree),'not_business_capture':True}
 def invoke(self,command):
  self.reads.append(command);self.assertIn(command['op'],('tabs','ping','tree'))
  result=[{'tabs':[self.fresh['tab']]}] if command['op']=='tabs' else self.fresh['tree'] if command['op']=='tree' else {'version':m.nav.VERSION,'safety':'DOM-only','governance_query_policy':'observed-dom-20261021-v1','governance_calendar_policy':'date-item-div-v3-single'}
  return {'ok':True,'result':copy.deepcopy(result)}
 def reconcile(self,checkpoint=None):
  with patch.object(m,'now',return_value='2026-10-22T10:01:00+00:00'):return m.reconcile(self.jp,self.statepath,self.digest,self.s['last_observation']['sha256'],self.invoke,checkpoint)
 def completed(self,positive=False):
  result=self.reconcile();state=json.loads(self.statepath.read_bytes());before=self.put(self.root/'records-query-evidence/0008.json',self.fresh);state['observations'].append(before);plan=g.QueryPlan(self.job['start'],self.job['end_exclusive']);command={**plan.next(self.fresh['tree'],{'phase':'verify-date'})['command'],'tabId':5};target=g.one([n for n in g.nodes(self.fresh['tree']) if n.get('selector')==command['locator']['value']],'query-button');state['calls'].append({'state':'confirmed','command':command,'before':before,'intent_at':'2026-10-22T10:01:00+00:00','postcondition':None,'result':{'kind':'filter','version':m.nav.VERSION,'clicked':copy.deepcopy(target)}})
  tree=copy.deepcopy(self.closed)
  if positive:
   tree=dom.tree();g.date_input(tree)['attributes']['value']='2026/10/21 ～ 2026/10/21';next(n for n in g.nodes(tree) if n.get('tag')=='td' and n.get('name')=='2026/10/20')['name']='2026/10/21';tree['root']['children']+=copy.deepcopy(self.closed['root']['children'][-3:])
  raw=self.raw(tree,at='2026-10-22T10:02:00+00:00');after=self.put(self.root/'records-query-evidence/0009.json',raw);page=g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);state['observations'].append(after);state.update(phase='capture-complete',last_observation=after,pages=[{**page,'observation':after}],rows=g.complete_pages([page]),zero_verified=False,waiting_for='readonly-detail-profile-and-analysis-full-distribution-required');self.put(self.statepath,state);return state,result
 def test_exact_restore_has_only_four_reads_archive_and_no_input_claim(self):
  result=self.reconcile();current=json.loads(self.statepath.read_bytes());m.verify_recovered(current,result['proof']);self.assertEqual(current['phase'],'verify-date');self.assertEqual(current['calls'],self.s['calls']);proof=m.document(result['proof']);manifest=m.document(proof['manifest']);self.assertEqual(Path(manifest['original_journal']['path']).read_bytes(),self.original);self.assertEqual(proof['original_stop']['read_only_settling'],self.s['read_only_settling']);self.assertFalse(proof['start_selection_effect_observed']);self.assertFalse(proof['records_query_effect_claimed']);self.assertEqual([c['op'] for c in self.reads],['tabs','ping','tree','tabs']);self.assertNotIn('settling_exhausted',current);self.assertEqual(m.verify_continuation(current,self.job,self.statepath)['original_call_count'],2)
 def test_fresh_different_range_calendar_identity_window_and_busy_preserves_original(self):
  for mode in ('date','calendar','identity','window','busy'):
   f=Tests();f.setUp();self.addCleanup(f.doCleanups)
   if mode=='date':g.date_input(f.fresh['tree'])['attributes']['value']='2026/10/20 ～ 2026/10/20'
   elif mode=='calendar':g.one([n for n in g.nodes(f.fresh['tree']) if 'governance_merchant-date-title' in g.cls(n) and n['name']=='2026年10月'],'title')['name']='2026年11月'
   elif mode=='identity':g.one([n for n in g.nodes(f.fresh['tree']) if n.get('selector')=='#manager'],'manager')['name']='我的客户经理错误 切换公司'
   elif mode=='window':f.fresh['tab']['windowId']=9
   else:f.fresh['tree']['root']['attributes']['aria-busy']='true'
   with self.subTest(mode=mode),self.assertRaises(ValueError):f.reconcile()
   self.assertEqual(f.statepath.read_bytes(),f.original);self.assertTrue(all(c['op'] in ('tabs','ping','tree') for c in f.reads));self.assertLessEqual(len(f.reads),3)
 def test_incomplete_read_intent_never_replays_and_original_unchanged(self):
  def fail(c):self.reads.append(c);raise TimeoutError('synthetic read interruption')
  with self.assertRaises(TimeoutError):m.reconcile(self.jp,self.statepath,self.digest,self.refs[-1]['sha256'],fail)
  with self.assertRaisesRegex(ValueError,'incomplete-read-intent-hold-no-replay'):self.reconcile()
  self.assertEqual(len(self.reads),1);self.assertEqual(self.statepath.read_bytes(),self.original)
 def test_proof_published_crash_resumes_offline_no_second_reads(self):
  def stop(stage):self.assertEqual(stage,'proof-published');raise RuntimeError('crash before commit')
  with self.assertRaises(RuntimeError):self.reconcile(stop)
  self.assertEqual(self.statepath.read_bytes(),self.original);count=len(self.reads);result=self.reconcile();self.assertEqual(len(self.reads),count);m.verify_recovered(json.loads(self.statepath.read_bytes()),result['proof'])
 def test_repeated_success_refuses_without_new_read(self):
  self.reconcile();count=len(self.reads)
  with self.assertRaisesRegex(ValueError,'already-reconciled-no-read'):self.reconcile()
  self.assertEqual(len(self.reads),count)
 def test_invalid_original_phase_unknown_query_extra_call_or_non_desired_rejects_before_read(self):
  old=copy.deepcopy(self.s)
  for mode in ('unknown','end-intent','phase','date','calendar'):
   self.s=copy.deepcopy(old)
   if mode=='unknown':self.s['calls'][-1]['state']='unknown'
   elif mode=='end-intent':self.s['calls'].append(copy.deepcopy(self.s['calls'][-1]))
   elif mode=='phase':self.s['phase']='collect-page'
   elif mode=='date':
    raw=copy.deepcopy(self.raws[0]);g.date_input(raw['tree'])['attributes']['value']='2026/10/20 ～ 2026/10/20';self.s['observations'][0]=self.put(self.root/'bad-original.json',raw);self.s['calls'][0]['before']=self.s['observations'][0]
   else:
    raw=copy.deepcopy(self.raws[-1]);g.one([n for n in g.nodes(raw['tree']) if 'governance_merchant-date-title' in g.cls(n) and n['name']=='2026年10月'],'title')['name']='2026年11月';self.s['observations'][-1]=self.put(self.root/'bad-calendar.json',raw);self.s['last_observation']=self.s['observations'][-1];self.s['read_only_settling']['last_observation']=self.s['last_observation']
   self.save()
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.reconcile()
   self.assertFalse(self.reads)
 def test_zero_replay_and_positive_detail_inputs_and_monitor_accept_complete_proof(self):
  state,result=self.completed();r=m.reference(self.statepath);actual,zero,refs=z.query(r,self.job,5,3,g.RECORDS);self.assertEqual(zero['total'],0);self.assertEqual(actual['calls'],state['calls']);out=sem.extract(state,'violation_operator',self.statepath);self.assertEqual(len(out['tokens']),1)
 def test_missing_forged_skip_or_changed_original_proof_does_not_pass_zero(self):
  state,_=self.completed();state[m.FIELD]={'path':str(self.root/'fake.json'),'sha256':'0'*64};self.put(self.statepath,state)
  with self.assertRaises(ValueError):z.query(m.reference(self.statepath),self.job,5,3,g.RECORDS)
 def test_positive_detail_query_inputs_deep_validate_reconciliation(self):
  state,result=self.completed(positive=True);manifest={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':self.jr,'query':m.reference(self.statepath)},'tab_id':5,'approved_version':m.nav.VERSION};self.assertEqual(d.inputs(manifest)['query'],state);state['calls'][1]['result']['clicked']['name']='20';self.put(self.statepath,state);manifest['inputs']['query']=m.reference(self.statepath)
  with self.assertRaises(ValueError):d.inputs(manifest)
 def test_double_zero_prepare_build_validate_full_route_replays_typed_skip(self):
  state,_=self.completed()
  import test_center_compact_zero as cf
  f=cf.CompactZero();f.setUp();self.addCleanup(f.doCleanups);final=copy.deepcopy(f.tree)
  for n in g.nodes(final):
   if 'name' in n:n['name']=n['name'].replace('2026/10/16','2026/10/21').replace('2026/10/20','2026/10/21')
  g.date_input(final)['attributes']['value']='2026/10/21 ～ 2026/10/21'
  old=copy.deepcopy(final);g.date_input(old)['attributes']['value']='2026/10/20 ～ 2026/10/20';cal=copy.deepcopy(old);cal['root']['children'].extend(copy.deepcopy([n for n in g.nodes(self.open) if 'governance_merchant-date-picker-popper' in g.cls(n)]));refs=[];calls=[];phase='open-date';plan=g.QueryPlan(self.job['start'],self.job['end_exclusive'])
  for i,tree in enumerate((old,cal,copy.deepcopy(cal),final)):
   tree['url']='https://life.douyin.com'+g.CENTER;raw=self.raw(tree,at=f'2026-10-22T10:03:0{i}+00:00');raw['tab']['url']='https://life.douyin.com'+g.CENTER+'?groupid=123';r=self.put(self.root/'center-query-evidence'/f'{i:04d}.json',raw);refs.append(r)
   if i<3:
    step=plan.next(tree,{'phase':phase});command={**step['command'],'tabId':5};target=g.one([n for n in g.nodes(tree) if n.get('selector')==command['locator']['value']],'synthetic-center-target');calls.append({'state':'confirmed','command':command,'before':r,'intent_at':f'2026-10-22T10:03:0{i}.500000+00:00','postcondition':None,'result':{'kind':'filter','version':m.nav.VERSION,'clicked':copy.deepcopy(target)}});phase=step['next_phase']
  center={'fingerprint':m.nav.tag(self.job),'tab_id':5,'approved_version':m.nav.VERSION,'phase':'profile-required','calls':calls,'pages':[],'observations':refs,'last_observation':refs[-1],'business_progress_changed':False,'profile_accepted':False,'waiting_for':'analysis-all-reasons-actual-view-profile-required'};cp=self.put(self.root/'center-query.json',center)
  manifest=z.prepare(self.jp,cp['path'],self.statepath,self.root/'zero-profile.json',self.root/'zero-manifest.json');capture=self.root/'zero-capture.json';payload=z.build(manifest['path'],capture);self.assertEqual(payload['records']['total'],0);self.assertEqual(z.validate(capture),payload);self.assertEqual(z.common.validate(capture),payload);self.assertEqual(payload['start'],'2026-10-21');self.assertEqual(len(self.reads),4)
 def test_same_lock_and_tampered_proof_reject_without_requests(self):
  import fcntl
  with self.statepath.with_name(self.statepath.name+'.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):self.reconcile()
  self.assertFalse(self.reads);result=self.reconcile();proof=m.document(result['proof']);manifest=m.document(proof['manifest']);Path(manifest['original_journal']['path']).write_text('{}');count=len(self.reads)
  with self.assertRaises(ValueError):q.Runner(self.job,5,self.statepath,m.nav.VERSION,self.invoke,job_ref=self.jr)
  self.assertEqual(len(self.reads),count)
 def test_formal_runner_uses_exact_query_once_then_real_table_capture(self):
  self.reconcile();query_inputs=[];closed=copy.deepcopy(self.closed)
  def fake(command):
   if command['op']=='click':
    saved=json.loads(self.statepath.read_bytes());self.assertEqual(saved['calls'][-1]['state'],'unknown');target=g.one([n for n in g.nodes(self.fresh['tree']) if n.get('selector')==command['locator']['value']],'formal-query-button');self.assertEqual(target['name'],'查询');query_inputs.append(command);self.fresh['tree']=closed;return {'ok':True,'result':{'kind':'filter','version':m.nav.VERSION,'clicked':copy.deepcopy(target)}}
   return self.invoke(command)
  runner=q.Runner(self.job,5,self.statepath,m.nav.VERSION,fake,job_ref=self.jr);runner.step();self.assertEqual(runner.s['phase'],'collect-page');runner=q.Runner(self.job,5,self.statepath,m.nav.VERSION,fake,job_ref=self.jr);runner.step();self.assertEqual(runner.s['phase'],'capture-complete');self.assertEqual(runner.s['rows'],[]);self.assertEqual(len(query_inputs),1);self.assertEqual(len(runner.s['calls']),3);self.assertEqual(runner.s['calls'][:2],self.s['calls']);m.verify_continuation(runner.s,self.job,self.statepath)
 def test_old_no_field_zero_full_output_is_byte_equal(self):
  import types
  import test_governance_zero_capture as old_fixture
  f=old_fixture.DoubleZero();f.setUp();self.addCleanup(f.doCleanups);old=types.ModuleType('baseline_zero');old.__file__=str(loader.D/'governance_zero_capture.py');exec(compile((loader.FIXTURES/'governance_zero_capture.py.before').read_text(),old.__file__,'exec'),old.__dict__)
  ref=z.prepare(f.refs['job']['path'],f.refs['center_query']['path'],f.refs['records_query']['path'],f.root/'comparison-profile.json',f.root/'comparison-manifest.json');manifest=d.document(ref);a=old.assemble(manifest,ref);b=z.assemble(manifest,ref);self.assertEqual(m.encoded(a),m.encoded(b));self.assertNotIn(m.FIELD,a)
 def test_pure_codegraph_signs_new_helper_and_its_navigation_dependencies(self):
  import verification_session as verification
  modules=[m,m.nav,q,d];token=verification.code_signature(modules);function=m.verify_continuation;original=function.__code__
  def changed(*args,**kw):raise ValueError('synthetic code replacement')
  try:
   function.__code__=changed.__code__;self.assertNotEqual(token,verification.code_signature(modules))
  finally:function.__code__=original
  self.assertEqual(token,verification.code_signature(modules))
 def loading_history(self,state,*,index=None,busy=True):
  raw=copy.deepcopy(self.fresh);raw['observed_at']='2026-10-22T10:01:30+00:00'
  if busy:raw['tree']['root']['attributes']['aria-busy']='true'
  # Explicit loading can replace the table; it never proves a zero result.
  raw['tree']['root']['children']=[n for n in raw['tree']['root']['children'] if not any(x.get('tag')=='table' for x in g.walk(n))]
  ref=self.put(self.root/'records-query-evidence/loading.json',raw);state['observations'].insert(len(state['observations'])-1 if index is None else index,ref);self.put(self.statepath,state);return ref
 def test_confirmed_query_busy_history_then_stable_zero_and_positive_replays(self):
  state,_=self.completed();self.loading_history(state);m.verify_continuation(state,self.job,self.statepath);self.assertEqual(z.query(m.reference(self.statepath),self.job,5,3,g.RECORDS)[1]['total'],0)
  f=Tests();f.setUp();self.addCleanup(f.doCleanups);state,_=f.completed(positive=True);f.loading_history(state);manifest={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':f.jr,'query':m.reference(f.statepath)},'tab_id':5,'approved_version':m.nav.VERSION};self.assertEqual(d.inputs(manifest)['query'],state)
 def test_original_pre_recovery_busy_remains_strict_no_reads(self):
  raw=copy.deepcopy(self.raws[0]);raw['tree']['root']['attributes']['aria-busy']='true';ref=self.put(self.root/'original-busy.json',raw);self.s['observations'][0]=ref;self.s['calls'][0]['before']=ref;self.save()
  with self.assertRaisesRegex(ValueError,'busy-or-risk'):self.reconcile()
  self.assertFalse(self.reads);self.assertEqual(self.statepath.read_bytes(),self.original)
 def test_busy_before_query_or_without_confirmed_query_refused(self):
  self.reconcile();state=json.loads(self.statepath.read_bytes());r=self.loading_history(state,index=len(state['observations']));state['last_observation']=r
  with self.assertRaises(ValueError):m.verify_continuation(state,self.job,self.statepath)
  f=Tests();f.setUp();self.addCleanup(f.doCleanups);state,_=f.completed();r=f.loading_history(state,index=state['observations'].index(state['calls'][2]['before']));state['calls'][2]['before']=r
  with self.assertRaises(ValueError):m.verify_continuation(state,f.job,f.statepath)
 def test_missing_busy_bad_table_final_busy_and_risk_never_become_result(self):
  for mode in ('no-busy','final','risk','date','window'):
   f=Tests();f.setUp();self.addCleanup(f.doCleanups);state,_=f.completed();r=f.loading_history(state,busy=mode!='no-busy')
   if mode=='final':state['last_observation']=r;state['observations'].remove(r);state['observations'].append(r);state['pages'][0]['observation']=r
   elif mode in ('risk','date','window'):
    raw=m.document(r)
    if mode=='risk':raw['tree']['root']['children'].append({'tag':'div','role':'alertdialog','name':'风险验证','selector':'#risk','attributes':{},'children':[]})
    elif mode=='date':g.date_input(raw['tree'])['attributes']['value']='2026/10/20 ～ 2026/10/20'
    else:raw['tab']['windowId']=99
    new=f.put(f.root/'bad-loading.json',raw);state['observations'][state['observations'].index(r)]=new
   with self.subTest(mode=mode),self.assertRaises(ValueError):m.verify_continuation(state,f.job,f.statepath)

if __name__=='__main__':unittest.main()
