"""Saved actual 0032 replay + synthetic mutations/temp journals. No UI."""
import copy,fcntl,importlib.util,json,sys,tempfile,time,unittest
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
SCRIPTS=HERE if (HERE/'dom_evidence.py').is_file() else ROOT/'skills/douyin-laike-operator/scripts'
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'));sys.path.insert(0,str(SCRIPTS))
import dom_evidence as d
import export_record_page_recovery as recovery
spec=importlib.util.spec_from_file_location('export_page_workflow',SCRIPTS/'bridge-workflow.py');workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
FIXTURES=HERE/'fixtures/export-first-page'
def read(p):return json.loads(Path(p).read_text())
def cls(n):return set(n.get('attributes',{}).get('class','').split())
class Page(unittest.TestCase):
 def setUp(self):
  self.original=read(FIXTURES/'original-journal.json');self.job=read(FIXTURES/'original-job.json');self.tree=read(FIXTURES/'0032-record-page.json');self.basepath=FIXTURES/'0021-baseline.json';self.baseline=read(self.basepath);self.original['last_tree']['path']=str((FIXTURES/'0032-record-page.json').resolve())
 def prove(self,t=None,baseline=None,start=None):return d.submitted_export_record(t or self.tree,self.original['date_range'],self.original['baseline_records'] if baseline is None else baseline,start or self.original['submitted_at'])
 def test_actual_unique_first_page_target_not_complete_list(self):
  result=self.prove();self.assertEqual(result['row']['generated_at'],'2026-10-22 19:50:42');self.assertEqual(result['page']['total'],11);self.assertEqual(result['page']['visible_rows'],10);self.assertFalse(result['page']['all_pages_read'])
  self.assertEqual(d.complete_record_list(self.baseline),self.original['baseline_records'])
  with self.assertRaisesRegex(ValueError,'pagination-incomplete'):d.complete_record_list(self.tree)
 def test_wrong_page_count_size_order_scope_or_exact_tag_rejected(self):
  for mode in ('page','total','size','order','table','foreignrow','tag','predate'):
   t=copy.deepcopy(self.tree);ns=list(d.nodes(t));body=next(n for n in ns if 'byted-table-body' in cls(n));start=None
   if mode=='page':
    selected=next(n for n in ns if 'byted-pager-item-checked' in cls(n));selected['attributes']['class']=selected['attributes']['class'].replace(' byted-pager-item-checked','');next(n for n in ns if n.get('tag')=='li' and n.get('name')=='2')['attributes']['class']+=' byted-pager-item-checked'
   if mode=='total':next(n for n in ns if 'byted-pager-record' in cls(n))['name']='共12条记录'
   if mode=='size':body['children'].pop()
   if mode=='order':body['children'][1],body['children'][2]=body['children'][2],body['children'][1]
   if mode=='table':t['root']['children'].append(copy.deepcopy(next(n for n in ns if 'byted-table-container-row' in cls(n))))
   if mode=='foreignrow':t['root']['children'].append(copy.deepcopy(body['children'][0]))
   if mode=='tag':next(n for n in d.nodes({'truncated':False,'root':body['children'][0]}) if 'byted-table-cell-first' in cls(n))['name']='prefix-'+d.export_tag(self.original['date_range'])
   if mode=='predate':start='2026-10-22T12:00:00+00:00'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.prove(t,start=start)
 def test_multiple_new_same_tag_and_changed_baseline_rejected(self):
  t=copy.deepcopy(self.tree);body=next(n for n in d.nodes(t) if 'byted-table-body' in cls(n));row=body['children'][1];old_name=self.original['baseline_records'][0]['text'].split(' ',1)[0];old_time=self.original['baseline_records'][0]['generated_at']
  for n in d.nodes({'truncated':False,'root':row}):n['name']=n.get('name','').replace(old_name,d.export_tag(self.original['date_range'])).replace(old_time,'2026-10-22 19:50:41')
  next(n for n in d.nodes(t) if 'byted-pager-record' in cls(n))['name']='共12条记录'
  with self.assertRaises(ValueError):self.prove(t)
  old=copy.deepcopy(self.original['baseline_records']);old.pop()
  with self.assertRaises(ValueError):self.prove(baseline=old)
 def test_new_exact_tag_timestamp_also_must_be_absent_from_all_baseline(self):
  t=copy.deepcopy(self.tree);body=next(n for n in d.nodes(t) if 'byted-table-body' in cls(n));old=copy.deepcopy(self.original['baseline_records']);previous=old[0]['generated_at'];stamp=self.prove()['row']['generated_at']
  for n in d.nodes({'truncated':False,'root':body['children'][1]}):n['name']=n.get('name','').replace(previous,stamp)
  old[0]['generated_at']=stamp;old[0]['text']=old[0]['text'].replace(previous,stamp)
  with self.assertRaisesRegex(ValueError,'timestamp-already-in-baseline'):self.prove(t,baseline=old)
 def fake_workflow(self,phase,tree):
  w=object.__new__(workflow.Workflow);w.job=copy.deepcopy(self.job);w.s=copy.deepcopy(self.original);w.s.update(phase=phase,generated_record=self.prove()['row']);w.invoke=None;w.file=Path('/not-written');events=[]
  current={'tabId':w.s['tab_id'],'windowId':995698278,'url':'https://life.douyin.com/p/life_comment/management?groupid='+str(w.job['groupid']),'allowed':True,'groupid':str(w.job['groupid'])};record={'tabId':w.s['record_tab_id'],'windowId':995698278,'url':w.s['record_url'],'allowed':True}
  tabs=[{'tabs':[current,record]}]
  def call(cmd):
   events.append(cmd);self.assertIn(cmd['op'],('tabs','ping'))
   return tabs if cmd['op']=='tabs' else {'version':d.VERSION,'safety':'DOM-only'}
  w.call=call;w.source_context=lambda tabs:current;w.ensure_source_active=lambda tabs,current:(tabs,current);w.tree=lambda tab=None:tree if tab else {'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'children':[]}};w.save=lambda:None;w.go=lambda phase:w.s.update(phase=phase);w.checkpoint=lambda *a,**kw:None;w.current_call=lambda:None
  def once(cmd):events.append(cmd);return {'ticket':'synthetic','since':'2026-10-22T10:00:00Z','expires':time.time()*1000+60000}
  w.once=once;return w,events
 def test_all_download_boundaries_use_same_fresh_proof(self):
  for phase,next_phase in (('pollRecords','armDownload'),('armDownload','prepareDownload'),('prepareDownload','clickDownload'),('clickDownload','downloadResult')):
   w,events=self.fake_workflow(phase,copy.deepcopy(self.tree));w.s['download_ticket']={'ticket':'synthetic','expires':time.time()*1000+60000};w.s['download_command']={'op':'click','tabId':w.s['record_tab_id'],'locator':{'by':'selector','value':d.exact({'truncated':False,'root':next(n for n in d.nodes(self.tree) if n.get('selector')==self.prove()['row']['selector'])},'下载')['selector']},'kind':'download'}
   with self.subTest(phase=phase):w.tick();self.assertEqual(w.s['phase'],next_phase);self.assertFalse(w.s['postsubmit_record_page']['all_pages_read'])
 def test_absent_target_holds_in_poll_without_reload_or_export(self):
  w,events=self.fake_workflow('pollRecords',copy.deepcopy(self.baseline));w.s['submitted_at']=workflow.now();w.tick();self.assertEqual(w.s['phase'],'pollRecords');self.assertIn('not-visible-or-ready',w.s['waiting_for']);self.assertFalse(any(x['op'] not in ('tabs','ping') for x in events))
 def temp_original(self,folder):
  folder=Path(folder).resolve();job=copy.deepcopy(self.job);s=copy.deepcopy(self.original);job['workflow_path']=str(folder/'workflow.json');job['work_order_path']=str(folder/'work-order.json');(folder/'bridge-evidence').mkdir();baseline=folder/'bridge-evidence/0021-recordsProfileRequired-tab-995698376.json';baseline.write_bytes(self.basepath.read_bytes());record=folder/'bridge-evidence/0032-pollRecords-tab-995698376.json';record.write_bytes(Path(s['last_tree']['path']).read_bytes());s['last_tree']=recovery.ref(record);jobpath=folder/'work-order.json';jobpath.write_text(json.dumps(job,ensure_ascii=False));path=folder/'workflow.json';path.write_text(json.dumps(s,ensure_ascii=False));return jobpath,path,baseline
 def test_pure_recovery_keeps_calls_phase_and_clears_only_typed_error(self):
  with tempfile.TemporaryDirectory() as tmp:
   jobpath,path,baseline=self.temp_original(tmp);old=read(path);oldsha=recovery.ref(path)['sha256'];result=recovery.reconcile(jobpath,oldsha,recovery.ref(baseline));current=read(path);self.assertEqual(current['phase'],'pollRecords');self.assertEqual(current['calls'],old['calls']);self.assertNotIn('last_error',current);self.assertEqual(recovery.verify_recovered(current,result['proof'])['original_error'],old['last_error']);self.assertEqual(recovery.reconcile(jobpath,oldsha,recovery.ref(baseline))['proof'],result['proof'])
   current['calls'][-1]['state']='unknown'
   with self.assertRaises(ValueError):recovery.verify_recovered(current,result['proof'])
 def test_recovery_refuses_other_error_unknown_and_download_intent(self):
  for kind in ('error','unknown','download','baseline'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as tmp:
    jobpath,path,baseline=self.temp_original(tmp);s=read(path)
    if kind=='error':s['last_error']['code']='arbitrary'
    if kind=='unknown':s['calls'][-1]['state']='unknown'
    if kind=='download':s['downloadPending']=True
    path.write_text(json.dumps(s,ensure_ascii=False));checksum=recovery.ref(path)['sha256'];r=recovery.ref(baseline)
    if kind=='baseline':r['sha256']='0'*64
    with self.assertRaises(ValueError):recovery.reconcile(jobpath,checksum,r)
    self.assertEqual(recovery.ref(path)['sha256'],checksum)
 def test_execution_lock_and_job_path_binding_refused_before_repair(self):
  with tempfile.TemporaryDirectory() as tmp:
   jobpath,path,baseline=self.temp_original(tmp);checksum=recovery.ref(path)['sha256']
   with (path.parent/'.bridge-execution.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaises(BlockingIOError):recovery.reconcile(jobpath,checksum,recovery.ref(baseline))
   self.assertEqual(recovery.ref(path)['sha256'],checksum)
   job=read(jobpath);job['work_order_path']=str(jobpath.parent/'other.json');jobpath.write_text(json.dumps(job))
   with self.assertRaisesRegex(ValueError,'canonical-work-order'):recovery.reconcile(jobpath,checksum,recovery.ref(baseline))
   self.assertEqual(recovery.ref(path)['sha256'],checksum)
 def test_reference_symlink_proof_contract_and_midread_job_change_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   jobpath,path,baseline=self.temp_original(tmp);checksum=recovery.ref(path)['sha256'];alias=path.parent/'alias.json';alias.symlink_to(baseline)
   with self.assertRaisesRegex(ValueError,'nonsymlink'):recovery.read({'path':str(alias),'sha256':recovery.ref(baseline)['sha256']})
   result=recovery.reconcile(jobpath,checksum,recovery.ref(baseline));current=read(path);proof=read(result['proof']['path']);proof['ui_used']=True;proofpath=Path(result['proof']['path']);proofpath.write_text(json.dumps(proof))
   with self.assertRaisesRegex(ValueError,'proof-kind'):recovery.verify_recovered(current,recovery.ref(proofpath))
  with tempfile.TemporaryDirectory() as tmp:
   jobpath,path,baseline=self.temp_original(tmp);checksum=recovery.ref(path)['sha256'];original_parser=recovery.d.submitted_export_record
   def change(*args,**kwargs):
    result=original_parser(*args,**kwargs);job=read(jobpath);job['synthetic_changed_midread']=True;jobpath.write_text(json.dumps(job));return result
   with patch.object(recovery.d,'submitted_export_record',side_effect=change),self.assertRaises(ValueError):recovery.reconcile(jobpath,checksum,recovery.ref(baseline))
   self.assertEqual(recovery.ref(path)['sha256'],checksum)
if __name__=='__main__':unittest.main()
