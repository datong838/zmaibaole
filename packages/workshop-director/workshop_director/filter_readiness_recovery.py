"""Outer package metadata recovery. No bridge/worker/scheduler verbs or CLI.
Installer target: packages/workshop-director/workshop_director/filter_readiness_recovery.py
Caller must own original runtime locks and recheck natural exits/lease via guard.
"""
import copy,hashlib,json,os,sys,tempfile
from datetime import datetime
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
KIND='verified-readonly-review-filter-readiness-metadata-v1'
FIELD='confirmed_filter_readonly_recovery'
ERROR='review-filter-loading-exhausted'
def need(v,m):
 if not v:raise ValueError(m)
def raw(reference):
 need(type(reference)is dict and set(reference)=={'path','sha256'},'readiness-exact-ref');p=Path(reference['path']);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),'readiness-canonical-ref');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==reference['sha256'],'readiness-ref-changed');return b
def ref(path):
 p=Path(path);need(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink(),'readiness-canonical-path');return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def doc(reference):return json.loads(raw(reference))
def encoded(value):return (json.dumps(value,ensure_ascii=True,indent=2)+'\n').encode()
def modules():
 directory=PROJECT/'skills/douyin-laike-operator/scripts';sys.path.insert(0,str(directory))
 import dom_evidence as d,readonly_tick_snapshot as s,review_filter_loading as l
 for m in (d,s,l):need(Path(m.__file__).resolve()==directory/(m.__name__+'.py'),'readiness-module-origin')
 return d,s,l
def stamp(value):
 t=datetime.fromisoformat(value.replace('Z','+00:00'));need(t.utcoffset()is not None,'readiness-aware-time');return t
def scope(job,state,value,read,*,pending):
 d,s,l=modules();window=value['scope']['windowId'];s.decode(value,state['tab_id'],window)
 before=d.context(value['before'],state['tab_id'],job['groupid']);after=d.context(value['after'],state['tab_id'],job['groupid'])
 need(before['url']==after['url']and before['windowId']==after['windowId']==window and before['url'].split('?')[0]=='https://life.douyin.com/p/life_comment/management'and value['tree'].get('url')=='https://life.douyin.com/p/life_comment/management'and value['ping'].get('version')==d.VERSION and value['ping'].get('safety')=='DOM-only','readiness-scope-route')
 list(d.nodes(value['tree']));d.identity(value['tree'],job['identity_baseline']);l.validate_filter_values(value['tree'],state['date_range'])
 need(not any(any(w in n.get('name','')for w in ('扫码登录','安全验证','风险验证','账号异常'))for n in d.nodes(value['tree'])),'readiness-risk')
 if pending:
  need(l.is_loading(value['tree']),'readiness-original-pending-required');l.validate_pending_store_scope(value['tree']);count=None
 else:
  need(not l.is_loading(value['tree']),'readiness-current-still-pending');d.all_store_scope(value['tree']);count=d.verified_review_filter(value['tree'],state['date_range'])['page_filtered']
 return {'tab_id':state['tab_id'],'window_id':window,'url':before['url'],'groupid':str(job['groupid']),'identity':copy.deepcopy(job['identity_baseline']),'date_range':copy.deepcopy(state['date_range']),'page_filtered':count}
def _qualify_exhausted(inputs,read=doc,read_bytes=raw):
 need(type(inputs)is dict and set(inputs)in ({'job','original','original_scope','ready_raw','ready_exit'},{'job','original','original_scope','ready_raw','ready_observation'}),'readiness-input-schema')
 job=read(inputs['job']);state=read(inputs['original']);need(job.get('action')=='acquire'and job.get('workflow_path')==inputs['original']['path']and job.get('work_order_path')==inputs['job']['path'],'readiness-job-path')
 dates={k:job['date_range'][k]for k in ('start','end')};need(state.get('state')=='running'and state.get('phase')=='verifyFilter'and state.get('work_order_id')==job['work_order_id']and state.get('company')==job['company']and str(state.get('groupid'))==str(job['groupid'])and state.get('date_range')==dates and state.get('identity')==job['identity_baseline'],'readiness-original-job')
 if 'ready_observation'in inputs:
  modules();from switch_read_recovery import fingerprint
  expected_fingerprint=fingerprint(job)
 else:expected_fingerprint=hashlib.sha256(json.dumps({k:job.get(k)for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 need(state['fingerprint']==expected_fingerprint,'readiness-original-fingerprint')
 error=state.get('last_error');need(type(error)is dict and error.get('code')==error.get('message')==ERROR and FIELD not in state,'readiness-exact-known-failure')
 calls=state['calls'];phases=['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'];need(len(calls)==5 and [c.get('phase')for c in calls]==phases and all(c.get('state')=='confirmed'for c in calls)and state['revision']==int(calls[-1]['key'].split(':')[0])+1,'readiness-original-five-confirmed')
 for c,p in zip(calls,phases):
  command=c['command'];clicked=c.get('result',{}).get('clicked',{});need(c['key'].split(':')[1]==p and command.get('op')=='click'and command.get('tabId')==state['tab_id']and command.get('kind')==('navigation'if p=='openReviews'else'filter')and command.get('locator')=={'by':'selector','value':clicked.get('selector')}and c['result'].get('kind')==command['kind'],'readiness-confirmed-action-binding')
 need(not any(state.get(k)for k in ('exportPending','downloadPending','export_pending','download_pending','submittedAt','result','record_tab_id','record_url')),'readiness-no-postfilter-side-effects')
 initial=read(inputs['original_scope'])
 if 'ready_observation'in inputs:
  need(inputs['original_scope']==state['review_filter_loading_reads'][0]['reply']and initial.get('ok')is True,'readiness-observation-original-envelope');initial=initial['result']
 facts=scope(job,state,initial,read,pending=True);reads=state.get('review_filter_loading_reads');need(type(reads)is list and len(reads)==3 and [x['attempt']for x in reads]==[0,1,2],'readiness-original-three-waits')
 materials=[inputs['job'],inputs['original'],inputs['original_scope'],inputs['ready_raw'],inputs.get('ready_exit',inputs.get('ready_observation'))];previous=None
 for row in reads:
  need(row['command']=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':facts['window_id']},'readiness-original-wait-scope');reply=read(row['reply']);need(reply.get('ok')is True,'readiness-original-wait-transport');found=scope(job,state,reply['result'],read,pending=True);need(found==facts and read(row['tree'])==reply['result']['tree'],'readiness-original-wait-tree')
  if previous is None:need(read(row['before_tree'])==initial['tree'],'readiness-original-first-tree')
  else:need(row['before_tree']==previous,'readiness-original-wait-prefix')
  previous=row['tree'];materials.extend([row['before_tree'],row['reply'],row['tree']])
 need(state['last_tree']==previous,'readiness-original-final-tree')
 if 'ready_observation'in inputs:
  ready,provenance=_readonly_observation(inputs,state,read,read_bytes);materials.extend(provenance)
 else:
  ready=read(inputs['ready_raw']);exit=read(inputs['ready_exit']);need(ready.get('ok')is True and exit.get('returncode')==0 and exit.get('stdout')==inputs['ready_raw']and stamp(exit['at'])>stamp(error['at']),'readiness-new-natural-read-binding');need(read_bytes(exit['stderr'])==b'','readiness-new-read-stderr');materials.append(exit['stderr'])
 current=scope(job,state,ready['result'],read,pending=False);need(all(current[k]==facts[k]for k in facts if k!='page_filtered'),'readiness-original-current-scope')
 return {**({'provider':READONLY_PROVIDER}if 'ready_observation'in inputs else{}),'kind':KIND,'inputs':copy.deepcopy(inputs),'original_error':copy.deepcopy(error),'original_calls':copy.deepcopy(calls),'phase':state['phase'],'revision':state['revision'],'ready':current,'materials':list({(r['path'],r['sha256']):r for r in materials}.values()),'ui_used':False,'new_inputs':0,'does_not_certify_export_or_completion':True}
def _previous_shared_transform(original,proof_ref):
 need(original.get('last_error',{}).get('code')in (ERROR,INITIAL_ERROR) and FIELD not in original,'readiness-transform-original');result=copy.deepcopy(original);result.pop('last_error');result[FIELD]=copy.deepcopy(proof_ref);return result
def location(original_ref):return Path(original_ref['path']).parent/'filter-readiness-recoveries'/original_ref['sha256']
def verify(proof_ref,current=None):
 proof=doc(proof_ref);need(set(proof)=={'kind','facts','archives','module'}and proof['kind']==KIND , 'readiness-proof-schema-source');_verify_module(proof);facts=proof['facts'];base=location(facts['inputs']['original']);need(proof_ref['path']==str(base/'proof.json'),'readiness-proof-location')
 mapped={}
 for pair in proof['archives']:
  a,r=pair['archive'],pair['original'];need(set(pair)=={'original','archive'}and a['sha256']==r['sha256']and a['path']==str(base/'materials'/(r['sha256']+'.data')),'readiness-proof-archive');raw(a);key=(r['path'],r['sha256']);need(key not in mapped,'readiness-proof-duplicate');mapped[key]=a
 def archived(r):
  key=(r['path'],r['sha256']);need(key in mapped,'readiness-proof-unarchived-material');return doc(mapped[key])
 need(qualify(facts['inputs'],archived,lambda r:raw(mapped[(r['path'],r['sha256'])]))==facts,'readiness-proof-derived-facts')
 original=archived(facts['inputs']['original']);expected=shared_transform(original,proof_ref)
 if current is not None:need(current==expected,'readiness-exact-metadata-delta')
 return {'original':original,'after':expected,'proof':proof_ref,'facts':facts}
def immutable(path,b):
 path=Path(path);need(path.resolve()==path and not path.is_symlink(),'readiness-output-canonical');path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(path.read_bytes()==b,'readiness-immutable-conflict');return ref(path)
 with path.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(path)
def recover(inputs,*,guard=None,checkpoint=lambda stage:None):
 """One WF CAS only. No default execution authority or lock acquisition."""
 need(callable(guard),'readiness-caller-locked-guard-required');guard('preflight');need(type(inputs)is dict and set(inputs)in ({'job','original','original_scope','ready_raw','ready_exit'},{'job','original','original_scope','ready_raw','ready_exit','request'},{'job','original','original_scope','ready_raw','ready_observation'}),'readiness-input-schema')
 for name,reference in inputs.items():
  if name!='original':raw(reference) # Immutable current inputs stay pinned on reentry.
 base=location(inputs['original']);proof_path=base/'proof.json';intent_path=base/'intent.json';path=Path(inputs['original']['path'])
 expected_intent={'kind':KIND,'inputs':inputs,'proof_path':str(proof_path),'module':ref(Path(__file__).resolve())}
 if intent_path.exists()or intent_path.is_symlink():need(doc(ref(intent_path))==expected_intent,'readiness-foreign-intent-preflight')
 if proof_path.exists():
  pr=ref(proof_path);found=verify(pr);need(found['facts']['inputs']==inputs,'readiness-reentry-inputs');need(intent_path.is_file()and doc(ref(intent_path))=={'kind':KIND,'inputs':inputs,'proof_path':str(proof_path),'module':ref(Path(__file__).resolve())},'readiness-reentry-intent');before,after=found['original'],found['after'];need(doc(ref(path))in (before,after),'readiness-reentry-conflict')
 else:
  facts=qualify(inputs);before=doc(inputs['original']);need(ref(path)==inputs['original'],'readiness-original-CAS');pr={'path':str(proof_path),'sha256':'not-yet-published'}
  archives=[]
  for r in facts['materials']:archives.append({'original':r,'archive':immutable(base/'materials'/(r['sha256']+'.data'),raw(r))})
  checkpoint('archives');guard('intent');intent={'kind':KIND,'inputs':inputs,'proof_path':str(proof_path),'module':ref(Path(__file__).resolve())};immutable(intent_path,encoded(intent));checkpoint('intent');pr=immutable(proof_path,encoded({'kind':KIND,'facts':facts,'archives':archives,'module':ref(Path(__file__).resolve())}));checkpoint('proof');found=verify(pr);after=found['after']
 guard('before-CAS');current=doc(ref(path));need(current in (before,after),'readiness-third-state-CAS')
 if current==before:
  need(ref(path)==inputs['original'],'readiness-before-raw-CAS');fd,tmp=tempfile.mkstemp(prefix='.filter-readiness-',dir=path.parent)
  try:
   os.fchmod(fd,path.stat().st_mode&0o777)
   with os.fdopen(fd,'wb')as f:f.write(encoded(after));f.flush();os.fsync(f.fileno())
   os.replace(tmp,path);directory_fd=os.open(path.parent,os.O_RDONLY)
   try:os.fsync(directory_fd)
   finally:os.close(directory_fd)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
  checkpoint('after-CAS')
 verify(pr,doc(ref(path)));guard('readback');return {'state':'reconciled','journal':ref(path),'proof':pr,'phase':after['phase'],'revision':after['revision'],'original_inputs_unchanged':True,'new_inputs':0}

INITIAL_ERROR='page-count-unverified'
INITIAL_PROVIDER='initial-established-store-header-count-missing-v1'
_PREVIOUS_MODULE={'path': '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/workshop_director/filter_readiness_recovery.py', 'sha256': 'f2d66048b9582a26b3aab587d06d010db9213915227a036d453e56e895d063dd'}
_PREVIOUS_MODULE_ARCHIVE={'path': '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/references/filter-readiness-module-archives/f2d66048b9582a26b3aab587d06d010db9213915227a036d453e56e895d063dd.py.data', 'sha256': 'f2d66048b9582a26b3aab587d06d010db9213915227a036d453e56e895d063dd'}
def _verify_module(proof):
 current=ref(Path(__file__).resolve())
 if proof['module']==current:return
 if proof['module']==_READONLY_PREVIOUS_MODULE and proof['facts'].get('provider')!=READONLY_PROVIDER:
  raw(_READONLY_PREVIOUS_ARCHIVE);return
 if proof['module']==_CONFIGURED_PREVIOUS_MODULE and proof['facts'].get('provider')!=CONFIGURED_PROVIDER:
  raw(_CONFIGURED_PREVIOUS_ARCHIVE);return
 if proof['module']==_INITIAL_PREVIOUS_MODULE and proof['facts'].get('provider')==INITIAL_PROVIDER and set(proof['facts']['inputs'])=={'job','original','original_scope','ready_raw','ready_exit','request'}:
  raw(_INITIAL_PREVIOUS_MODULE_ARCHIVE);return
 need(set(proof['facts']['inputs'])=={'job','original','original_scope','ready_raw','ready_exit'}and proof['module']==_PREVIOUS_MODULE,'readiness-proof-unknown-module')
 raw(_PREVIOUS_MODULE_ARCHIVE)

def qualify(inputs,read=doc,read_bytes=raw):
 if type(inputs)is dict and 'request'in inputs:
  if read(inputs['original']).get('last_error',{}).get('code')==ERROR:return _qualify_configured_exhausted(inputs,read,read_bytes)
  if read(inputs['original']).get('last_error',{}).get('code')==EXPORT_ERROR:return _qualify_export(inputs,read,read_bytes)
  return _qualify_initial(inputs,read,read_bytes)
 return _qualify_exhausted(inputs,read,read_bytes)

def _qualify_initial(inputs,read=doc,read_bytes=raw):
 need(type(inputs)is dict and set(inputs)=={'job','original','original_scope','ready_raw','ready_exit','request'},'readiness-input-schema')
 job=read(inputs['job']);state=read(inputs['original']);need(job.get('action')=='acquire'and job.get('workflow_path')==inputs['original']['path']and job.get('work_order_path')==inputs['job']['path'],'readiness-job-path')
 dates={k:job['date_range'][k]for k in ('start','end')};need(state.get('state')=='running'and state.get('phase')=='verifyFilter'and state.get('work_order_id')==job['work_order_id']and state.get('company')==job['company']and str(state.get('groupid'))==str(job['groupid'])and state.get('date_range')==dates and state.get('identity')==job['identity_baseline'],'readiness-original-job')
 fingerprint=hashlib.sha256(json.dumps({k:job.get(k)for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode()).hexdigest();need(state['fingerprint']==fingerprint,'readiness-original-fingerprint')
 error=state.get('last_error');need(type(error)is dict and error.get('code')==error.get('message')==INITIAL_ERROR and FIELD not in state,'readiness-exact-known-failure')
 calls=state['calls'];phases=['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'];need(len(calls)==5 and [c.get('phase')for c in calls]==phases and all(c.get('state')=='confirmed'for c in calls)and state['revision']==int(calls[-1]['key'].split(':')[0])+1,'readiness-original-five-confirmed')
 for c,p in zip(calls,phases):
  command=c['command'];clicked=c.get('result',{}).get('clicked',{});need(c['key'].split(':')[1]==p and command.get('op')=='click'and command.get('tabId')==state['tab_id']and command.get('kind')==('navigation'if p=='openReviews'else'filter')and command.get('locator')=={'by':'selector','value':clicked.get('selector')}and c['result'].get('kind')==command['kind'],'readiness-confirmed-action-binding')
 need(not any(state.get(k)for k in ('exportPending','downloadPending','export_pending','download_pending','submittedAt','result','record_tab_id','record_url')),'readiness-no-postfilter-side-effects')

 request=read(inputs['request']);context=request['context'];task=request['task'];binding=context.get('browser_binding',{});bound=context.get('scope')
 need(request.get('kind')=='workshop-worker-request-v1'and request.get('attempt_id')==Path(inputs['request']['path']).parent.name and task.get('id')and request['attempt_id']==task['id']+'-'+str(task['attempt']+1)and task.get('context')==context,'readiness-initial-original-request')
 need(type(bound)is dict and set(bound)=={'pid','tab_id'}and binding.get('kind')=='task-browser-process-binding-v1'and binding.get('scope')==bound and bound['pid']==binding.get('process',{}).get('pid')and bound['tab_id']==state['tab_id']and not context.get('scope_pending'),'readiness-initial-browser-binding')
 need(context.get('operator',{}).get('work_order')==inputs['job']and context['operator'].get('action')=='acquire','readiness-initial-original-operator')
 order=read(context['order']);need(order.get('kind')=='daily-dispatch-order-v1'and order.get('workflow')=='daily-comment-stats'and order.get('role')=='daily_stats_operator','readiness-initial-original-order')
 matching=[c for c in order['scope']['company_ranges']if c['company']==job['company']and str(c['groupid'])==str(job['groupid'])]
 need(len(matching)==1 and matching[0]['start']==dates['start']and matching[0]['end_exclusive']==job['date_range']['end_exclusive']and binding['tab_bootstrap']['order']==context['order'],'readiness-initial-order-date-company')
 selection=binding['tab_bootstrap']['selection'];need(selection['tab_id']==state['tab_id']and str(selection['groupid'])==str(job['groupid'])and type(selection.get('window_id'))is int,'readiness-initial-request-window')
 initial=read(inputs['original_scope']);facts=scope(job,state,initial,read,pending=True)
 need(facts['window_id']==selection['window_id']and read(state['last_tree'])==initial['tree']and state.get('review_filter_loading_reads',[])==[],'readiness-initial-zero-waits-tree')
 d,s,l=modules();need(l.is_header_pending(initial['tree']),'readiness-initial-header-only');d.all_store_scope(initial['tree'])
 need(any(__import__('re').fullmatch(r'全部门店 [1-9]\d*',n.get('name',''))and n.get('attributes',{}).get('class')=='byted-tab-bar-item-label'for n in d.nodes(initial['tree'])),'readiness-initial-established-stores')
 ready=read(inputs['ready_raw']);exit=read(inputs['ready_exit']);need(ready.get('ok')is True and exit.get('returncode')==0 and exit.get('stdout')==inputs['ready_raw']and stamp(exit['at'])>stamp(error['at']),'readiness-new-natural-read-binding');need(read_bytes(exit['stderr'])==b'','readiness-new-read-stderr')
 current=scope(job,state,ready['result'],read,pending=False);need(all(current[k]==facts[k]for k in facts if k!='page_filtered'),'readiness-original-current-scope')
 materials=[*inputs.values(),context['order'],state['last_tree'],exit['stderr']]
 return {'kind':KIND,'provider':INITIAL_PROVIDER,'inputs':copy.deepcopy(inputs),'original_error':copy.deepcopy(error),'original_calls':copy.deepcopy(calls),'phase':state['phase'],'revision':state['revision'],'ready':current,'task_id':task['id'],'attempt_id':request['attempt_id'],'outer':copy.deepcopy(task['outer']),'binding':copy.deepcopy(bound),'materials':list({(r['path'],r['sha256']):r for r in materials}.values()),'ui_used':False,'new_inputs':0,'does_not_certify_export_or_completion':True}

EXPORT_ERROR='export-store-scope-unverified'
EXPORT_PROVIDER='initial-empty-export-dialog-store-ready-v1'
EXPORT_FIELD='confirmed_export_dialog_readonly_recovery'
_INITIAL_PREVIOUS_MODULE={'path': '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/workshop_director/filter_readiness_recovery.py', 'sha256': 'fb3591ae01f360d338a561e4021800f3b8caec9fadb74beba435e733cb67277f'}
_INITIAL_PREVIOUS_MODULE_ARCHIVE={'path': '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/references/filter-readiness-module-archives/fb3591ae01f360d338a561e4021800f3b8caec9fadb74beba435e733cb67277f.py.data', 'sha256': 'fb3591ae01f360d338a561e4021800f3b8caec9fadb74beba435e733cb67277f'}
def shared_transform(original,proof_ref):
 if original.get('last_error',{}).get('code')!=EXPORT_ERROR:return _previous_shared_transform(original,proof_ref)
 need(original['last_error'].get('message')==EXPORT_ERROR and EXPORT_FIELD not in original,'export-readiness-transform-original');result=copy.deepcopy(original);result.pop('last_error');result[EXPORT_FIELD]=copy.deepcopy(proof_ref);return result

def export_module():
 import importlib.util
 path=PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py';spec=importlib.util.spec_from_file_location('reviewed_export_dialog_workflow',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def _export_scope(job,state,value,*,pending):
 d,s,l=modules();window=value['scope']['windowId'];s.decode(value,state['tab_id'],window);before=d.context(value['before'],state['tab_id'],job['groupid']);after=d.context(value['after'],state['tab_id'],job['groupid'])
 need(before['url']==after['url']and before['windowId']==after['windowId']==window and before['url'].split('?')[0]=='https://life.douyin.com/p/life_comment/management'and value['tree'].get('url')=='https://life.douyin.com/p/life_comment/management'and value['ping'].get('version')==d.VERSION and value['ping'].get('safety')=='DOM-only','export-readiness-scope')
 tree=value['tree'];list(d.nodes(tree));d.identity(tree,job['identity_baseline']);d.all_store_scope(tree);count=d.verified_review_filter(tree,state['date_range'])['page_filtered'];need(count==state['page_filtered'],'export-readiness-page-count-changed')
 need(not any(any(w in n.get('name','')for w in ('扫码登录','安全验证','风险验证','账号异常'))for n in d.nodes(tree)),'export-readiness-risk')
 if pending:need(export_module().export_dialog_scope_pending(tree,state['date_range']),'export-readiness-original-modal-empty')
 else:d.verified_export_dialog(tree,state['date_range'],require_dates=False)
 return {'tab_id':state['tab_id'],'window_id':window,'url':before['url'],'groupid':str(job['groupid']),'identity':copy.deepcopy(job['identity_baseline']),'date_range':copy.deepcopy(state['date_range']),'page_filtered':count}

def _qualify_export(inputs,read=doc,read_bytes=raw):
 need(type(inputs)is dict and set(inputs)=={'job','original','original_scope','ready_raw','ready_exit','request'},'export-readiness-input-schema');job=read(inputs['job']);state=read(inputs['original']);request=read(inputs['request']);error=state.get('last_error',{})
 need(job.get('action')=='acquire'and job.get('workflow_path')==inputs['original']['path']and job.get('work_order_path')==inputs['job']['path']and state.get('phase')=='exportDialogProfileRequired'and state.get('state')=='running'and error.get('code')==error.get('message')==EXPORT_ERROR and EXPORT_FIELD not in state,'export-readiness-original-phase-error')
 dates={k:job['date_range'][k]for k in ('start','end')};need(state['work_order_id']==job['work_order_id']and state['company']==job['company']and str(state['groupid'])==str(job['groupid'])and state['date_range']==dates and state['identity']==job['identity_baseline'],'export-readiness-original-job');fingerprint=hashlib.sha256(json.dumps({k:job.get(k)for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode()).hexdigest();need(state['fingerprint']==fingerprint,'export-readiness-original-fingerprint')
 calls=state['calls'];phases=['openReviews','openReviews','openPageCalendar','pageStart','pageEnd','openExportMenu','recordsProfileRequired','recordsProfileRequired','openExportMenuAgain','openExportDialog'];need(len(calls)==10 and [c.get('phase')for c in calls]==phases and all(c.get('state')=='confirmed'for c in calls)and state['revision']==int(calls[-1]['key'].split(':')[0])+1,'export-readiness-original-ten-confirmed')
 for c in calls:
  cmd=c['command'];need(type(cmd.get('tabId'))is int and cmd['tabId']>0 and cmd['tabId']in (state['tab_id'],state.get('record_tab_id'))and cmd.get('op')in ('click','hover')and cmd.get('kind')in ('navigation','filter','export')and c.get('result',{}).get('kind')==cmd['kind'],'export-readiness-confirmed-input')
 last=calls[-1];need(last['command'].get('op')=='click'and last['command'].get('kind')=='export'and last['command'].get('tabId')==state['tab_id']and last['command'].get('locator')=={'by':'selector','value':last['result'].get('clicked',{}).get('selector')}and last['result']['clicked'].get('name')=='导出评价','export-readiness-original-open-confirmed')
 need(not any(state.get(k)for k in ('exportPending','downloadPending','submittedAt','result'))and not any(c.get('stage')in ('export-intent','export-generated','download-intent','download-complete')for c in state['checkpoints'])and state.get('export_dialog_loading_reads',[])==[],'export-readiness-preexport-only')
 filters=[c for c in state['checkpoints']if c.get('stage')=='filter'];need(len(filters)==1 and filters[0]['date_range']==dates and filters[0]['page_filtered']==state['page_filtered']and str(filters[0]['groupid'])==str(job['groupid'])and stamp(filters[0]['at'])<stamp(last['at']),'export-readiness-original-filter-checkpoint')
 ctx=request['context'];task=request['task'];binding=ctx.get('browser_binding',{});bound=ctx.get('scope');need(request.get('kind')=='workshop-worker-request-v1'and request.get('attempt_id')==Path(inputs['request']['path']).parent.name and request['attempt_id']==task['id']+'-'+str(task['attempt']+1)and task['context']==ctx,'export-readiness-original-request')
 need(type(bound)is dict and set(bound)=={'pid','tab_id'}and binding.get('kind')=='task-browser-process-binding-v1'and binding.get('scope')==bound and bound['pid']==binding.get('process',{}).get('pid')and bound['tab_id']==state['tab_id']and not ctx.get('scope_pending')and ctx.get('operator',{}).get('work_order')==inputs['job'],'export-readiness-original-binding')
 order=read(ctx['order']);matching=[c for c in order['scope']['company_ranges']if c['company']==job['company']and str(c['groupid'])==str(job['groupid'])];need(order.get('kind')=='daily-dispatch-order-v1'and order.get('workflow')=='daily-comment-stats'and order.get('role')=='daily_stats_operator'and len(matching)==1 and matching[0]['start']==dates['start']and matching[0]['end_exclusive']==job['date_range']['end_exclusive']and binding['tab_bootstrap']['order']==ctx['order'],'export-readiness-order-company-date')
 selection=binding['tab_bootstrap']['selection'];need(selection['tab_id']==state['tab_id']and str(selection['groupid'])==str(job['groupid']),'export-readiness-selected-tab');original=read(inputs['original_scope']);facts=_export_scope(job,state,original,pending=True);need(facts['window_id']==selection['window_id']and read(state['last_tree'])==original['tree'],'export-readiness-original-window-tree')
 ready=read(inputs['ready_raw']);exit=read(inputs['ready_exit']);need(ready.get('ok')is True and exit.get('returncode')==0 and exit.get('stdout')==inputs['ready_raw']and stamp(exit['at'])>stamp(error['at'])and read_bytes(exit['stderr'])==b'','export-readiness-new-natural-read');current=_export_scope(job,state,ready['result'],pending=False);need(current==facts,'export-readiness-current-same-scope')
 materials=[*inputs.values(),ctx['order'],state['last_tree'],exit['stderr']]
 return {'kind':KIND,'provider':EXPORT_PROVIDER,'inputs':copy.deepcopy(inputs),'original_error':copy.deepcopy(error),'original_calls':copy.deepcopy(calls),'phase':state['phase'],'revision':state['revision'],'ready':current,'task_id':task['id'],'attempt_id':request['attempt_id'],'outer':copy.deepcopy(task['outer']),'binding':copy.deepcopy(bound),'materials':list({(r['path'],r['sha256']):r for r in materials}.values()),'ui_used':False,'new_inputs':0,'does_not_certify_export_or_completion':True}


CONFIGURED_PROVIDER='configured-switch-exhausted-filter-ready-v1'
_CONFIGURED_PREVIOUS_MODULE={'path':str(PROJECT/'packages/workshop-director/workshop_director/filter_readiness_recovery.py'),'sha256':'ccbc90af8286310c79df2f71e1d122bbf59d763f592fe7fe519717f4014ed3e5'}
_CONFIGURED_PREVIOUS_ARCHIVE={'path':str(PROJECT/'packages/workshop-director/references/filter-readiness-module-archives/ccbc90af8286310c79df2f71e1d122bbf59d763f592fe7fe519717f4014ed3e5.py.data'),'sha256':'ccbc90af8286310c79df2f71e1d122bbf59d763f592fe7fe519717f4014ed3e5'}

def _configured_switch_prefix(job,state,read):
    """Reuse the original public switch verifier; never accept a caller boolean.
    All prior calls remain byte-for-byte facts; no previous input is repeated.
    """
    import switch_read_recovery as recovery
    need(Path(recovery.__file__)==PROJECT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py','readiness-switch-verifier-origin')
    proof_ref=state['switch_read_recovery'];proof=read(proof_ref);old=read(proof['original_journal'])
    need(read(proof['job'])==job and len(old['calls'])==4 and state['calls'][:4]==old['calls'],'readiness-switch-exact-original-prefix')
    # Reconstruct only the public verifier's completed switch journal. It checks
    # this complete dictionary against the original proof/operation/sample itself.
    verified=copy.deepcopy(old)
    if verified.get('last_error'):verified.setdefault('resolved_errors',[]).append({**verified.pop('last_error'),'resolved_at':proof['at'],'next_phase':'accountAfterSwitch','recovery_proof':proof_ref})
    sample_path=Path(proof['sample']['path']);tree_ref=ref(sample_path.with_name(sample_path.name.replace('-sample.json','-tree.json')))
    verified.update(phase='accountAfterSwitch',revision=old['revision']+1,last_tree=tree_ref,switch_read_recovery=proof_ref,updated_at=proof['at']);verified.pop('waiting_for',None);verified.pop('company_switch_wait_started',None)
    checked=recovery.verify_recovered(verified,proof_ref)
    need(checked['original_calls']==state['calls'][:4]and checked['facts']['groupid']==str(job['groupid'])and checked['facts']['tab_id']==state['tab_id'],'readiness-switch-proof-binding')
    hover=state['calls'][4];cmd=hover['command'];target=hover.get('result',{}).get('hovered',{})
    need(hover['phase']=='accountAfterSwitch'and hover['key']==str(verified['revision'])+':accountAfterSwitch'and hover['state']=='confirmed'and cmd.get('op')=='hover'and cmd.get('kind')=='navigation'and cmd.get('tabId')==state['tab_id']and cmd.get('locator')=={'by':'selector','value':target.get('selector')}and target.get('name')==job['provider_baseline']and 'Profile-index-module__title--'in target.get('attributes',{}).get('class',''),'readiness-switch-confirmed-profile-hover')
    need(any(c.get('stage')=='switch'and c.get('identity')==job['identity_baseline']and str(c.get('groupid'))==str(job['groupid'])for c in state.get('checkpoints',[])),'readiness-switch-target-checkpoint')
    return checked,proof_ref,tree_ref

def _qualify_configured_exhausted(inputs,read=doc,read_bytes=raw):
    need(type(inputs)is dict and set(inputs)=={'job','original','original_scope','ready_raw','ready_exit','request'},'readiness-configured-input-schema')
    job=read(inputs['job']);state=read(inputs['original']);need(job.get('company_configuration_registry')=='configured-source-index-v2'and job.get('action')=='acquire'and job.get('workflow_path')==inputs['original']['path']and job.get('work_order_path')==inputs['job']['path'],'readiness-configured-job')
    dates={k:job['date_range'][k]for k in ('start','end')};need(state.get('state')=='running'and state.get('phase')=='verifyFilter'and state.get('work_order_id')==job['work_order_id']and state.get('company')==job['company']and str(state.get('groupid'))==str(job['groupid'])and state.get('date_range')==dates and state.get('identity')==job['identity_baseline'],'readiness-original-job')
    import switch_read_recovery as recovery
    need(state['fingerprint']==recovery.fingerprint(job),'readiness-original-fingerprint')
    error=state.get('last_error');need(type(error)is dict and set(error)=={'at','code','message'}and(error.get('code'),error.get('message'))==(ERROR,ERROR)and FIELD not in state,'readiness-exact-known-failure')
    calls=state['calls'];phases=['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'];need(len(calls)==10 and all(c.get('state')=='confirmed'for c in calls)and[c.get('phase')for c in calls[5:]]==phases and state['revision']==int(calls[-1]['key'].split(':')[0])+1 and len({c['key']for c in calls})==len(calls),'readiness-configured-confirmed-tail')
    checked,switch_ref,switch_tree=_configured_switch_prefix(job,state,read);configuration=recovery.configured_source_module(job)
    for call,phase in zip(calls[5:],phases):
        command=call['command'];clicked=call.get('result',{}).get('clicked',{});need(call['key'].split(':')[1]==phase and command.get('op')=='click'and type(command.get('tabId'))is int and command['tabId']>0 and command['tabId']==state['tab_id']and command.get('kind')==('navigation'if phase=='openReviews'else'filter')and command.get('locator')=={'by':'selector','value':clicked.get('selector')},'readiness-confirmed-action-binding')
    need(calls[-2]['result']['clicked']['name']==str(int(dates['start'][-2:]))and calls[-1]['result']['clicked']['name']==str(int(dates['end'][-2:])),'readiness-confirmed-date-days')
    need(not any(state.get(k)for k in('exportPending','downloadPending','export_pending','download_pending','submittedAt','result','record_tab_id','record_url')),'readiness-no-postfilter-side-effects')
    request=read(inputs['request']);context=request['context'];task=request['task'];binding=context['browser_binding'];bound=context['scope']
    need(request.get('kind')=='workshop-worker-request-v1'and task.get('context')==context and request['attempt_id']==Path(inputs['request']['path']).parent.name==task['id']+'-'+str(task['attempt']+1),'readiness-original-request')
    need(binding.get('kind')=='task-browser-process-binding-v1'and binding.get('scope')==bound and bound['pid']==binding['process']['pid']and bound['tab_id']==state['tab_id']and context.get('operator',{}).get('work_order')==inputs['job']and not context.get('scope_pending'),'readiness-original-browser-operator')
    order=read(context['order']);matching=[c for c in order['scope']['company_ranges']if c['company']==job['company']and str(c['groupid'])==str(job['groupid'])]
    need(order.get('kind')=='daily-dispatch-order-v1'and order.get('workflow')=='daily-comment-stats'and len(matching)==1 and matching[0]['start']==dates['start']and matching[0]['end_exclusive']==job['date_range']['end_exclusive'],'readiness-original-order-scope')
    initial_raw=read(inputs['original_scope']);need(initial_raw.get('ok')is True and initial_raw.get('error')is None,'readiness-original-scope-envelope');initial=initial_raw['result'];configuration.require_no_visible_system_error(initial['tree']);facts=scope(job,state,initial,read,pending=True);need(facts['window_id']==checked['facts']['window_id'],'readiness-switch-original-window')
    reads=state.get('review_filter_loading_reads');need(type(reads)is list and len(reads)==3 and [r['attempt']for r in reads]==[0,1,2],'readiness-original-three-waits');materials=[*inputs.values(),context['order'],switch_ref,switch_tree,ref(Path(recovery.__file__))];previous=None
    for row in reads:
        need(row['command']=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':facts['window_id']},'readiness-original-wait-scope');reply=read(row['reply']);need(reply.get('ok')is True,'readiness-original-wait-transport');found=scope(job,state,reply['result'],read,pending=True);need(found==facts and read(row['tree'])==reply['result']['tree'],'readiness-original-wait-tree');need(read(row['before_tree'])==initial['tree']if previous is None else row['before_tree']==previous,'readiness-original-wait-prefix');previous=row['tree'];materials.extend([row['before_tree'],row['reply'],row['tree']])
    need(state['last_tree']==previous,'readiness-original-final-tree')
    index=read(inputs['ready_exit']);exit=read(index['natural_exit']);returned=read(index['request_returned']);started=read(index['request_started']);ready=read(inputs['ready_raw']);command=read(index['command'])
    need(index.get('kind')=='same-original-readonly-classification-provenance-v1'and index.get('WF_after')==inputs['original']and index.get('response')==inputs['ready_raw']and index.get('one_request_only')is True and exit.get('returncode')==0 and returned['response']==inputs['ready_raw']and stamp(exit['at'])>stamp(error['at'])and stamp(returned['returned_at'])>=stamp(started['at'])and command=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':facts['window_id']},'readiness-natural-ready-provenance')
    need(ready.get('ok')is True and ready.get('error')is None,'readiness-new-read-transport');configuration.require_no_visible_system_error(ready['result']['tree']);current=scope(job,state,ready['result'],read,pending=False);need(all(current[k]==facts[k]for k in facts if k!='page_filtered'),'readiness-original-current-scope')
    # Pin the exact original producer proof, its original journal/sample/tree and
    # original operation observations. No directory walk or unrelated history.
    switch=read(switch_ref);old=read(switch['original_journal'])
    for key in ('job','original_journal','original_tree','original_tree_ref','sample','window_anchor_ref'):
        if key in switch:materials.append(switch[key]);read(switch[key])
    if old.get('company_configuration_operation'):materials.append(old['company_configuration_operation']);read(old['company_configuration_operation'])
    for observation in old.get('company_configuration_observations',[]):
        materials.extend([observation['scope'],observation['operation']]);read(observation['scope']);read(observation['operation'])
    materials.extend([index[k]for k in('natural_exit','request_returned','request_started','command')])
    return {'kind':KIND,'provider':CONFIGURED_PROVIDER,'inputs':copy.deepcopy(inputs),'original_error':copy.deepcopy(error),'original_calls':copy.deepcopy(calls),'phase':state['phase'],'revision':state['revision'],'ready':current,'task_id':task['id'],'attempt_id':request['attempt_id'],'outer':copy.deepcopy(task['outer']),'materials':list({(r['path'],r['sha256']):r for r in materials}.values()),'ui_used':False,'new_inputs':0,'does_not_certify_export_or_completion':True}


# A separate real observer protocol. Its stdout is classification JSON, not the
# bridge response. Never manufacture the legacy ready_exit.stdout binding.
READONLY_PROVIDER='verified-original-single-readonly-observation-v1'
_READONLY_OBSERVER_SHA='15a929f8c3ef23dfb448ee83bd9fb3dd7e701a64f99538fe881152ba409a7bca'
_READONLY_PREVIOUS_MODULE={'path':str(PROJECT/'packages/workshop-director/workshop_director/filter_readiness_recovery.py'),'sha256':'7c66a662d80a24aa0b2272d6f479ebd1db7ef58ac417fd8866cc2abd67bbf8dc'}
_READONLY_PREVIOUS_ARCHIVE={'path':str(PROJECT/'packages/workshop-director/references/filter-readiness-module-archives/7c66a662d80a24aa0b2272d6f479ebd1db7ef58ac417fd8866cc2abd67bbf8dc.py.data'),'sha256':'7c66a662d80a24aa0b2272d6f479ebd1db7ef58ac417fd8866cc2abd67bbf8dc'}
def _readonly_observation(inputs,state,read,read_bytes):
 index=read(inputs['ready_observation']);need(index.get('kind')=='CF4-single-current-readonly-evidence-index-v1','readiness-observer-index-kind');refs=index['refs'];names={'authority-record.json','command.json','intent.json','natural-exit.json','outer-started.json','process.json','read-baseline.json','read_once.py','request-returned.json','request-started.json','response.json','result.json','stderr.log','stdout.log','tree.json'}
 need(set(refs)==names and inputs['ready_raw']==refs['response.json'],'readiness-observer-index-refs');base=Path(inputs['ready_observation']['path']).parent
 for name,reference in refs.items():need(reference['path']==str(base/name),'readiness-observer-canonical-files');read_bytes(reference)
 need(refs['read_once.py']['sha256']==_READONLY_OBSERVER_SHA,'readiness-observer-source');authority=read(refs['authority-record.json']);intent=read(refs['intent.json']);command=read(refs['command.json']);start=read(refs['request-started.json']);returned=read(refs['request-returned.json']);exit=read(refs['natural-exit.json']);outer=read(refs['outer-started.json']);process=read(refs['process.json']);result=read(refs['result.json']);response=read(refs['response.json'])
 need(authority.get('kind')=='root-direct-one-fresh-classification-authorization-v1'and authority.get('maximum_requests')==1 and authority.get('original_WF')==inputs['original']and authority.get('command')==command,'readiness-observer-authority')
 need(intent.get('kind')=='original-CF4-current-scope-classification-once-v1'and intent['command']==refs['command.json']and intent['original_workflow']==inputs['original']and intent['original_job']==inputs['job']and intent['business_inputs_allowed']==0,'readiness-observer-intent')
 need(command=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':response['result']['scope']['windowId']}and returned['response']==inputs['ready_raw']and response.get('ok')is True,'readiness-observer-command-response')
 expected=[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),'-I','-B',refs['read_once.py']['path']]
 need(outer['argv']==process['argv']==expected and process['pid']==start['pid']and type(start['pid'])is int and start['pid']>0,'readiness-observer-natural-process')
 need(set(exit)=={'at','returncode','seconds'}and exit['returncode']==0 and type(exit['seconds'])in(int,float)and 0<=exit['seconds']<60,'readiness-observer-natural-exit')
 times=[state['last_error']['at'],outer['at'],process['at'],intent['at'],start['at'],returned['returned_at'],exit['at']]
 need(all(stamp(a)<=stamp(b)for a,b in zip(times,times[1:])),'readiness-observer-time-order')
 need(read_bytes(refs['stderr.log'])==b'','readiness-observer-stderr');stdout=json.loads(read_bytes(refs['stdout.log']));need(stdout.get('result')==refs['result.json']and stdout.get('classification')=='ready','readiness-observer-classification-stdout')
 current=scope(read(inputs['job']),state,response['result'],read,pending=False)
 need(result.get('kind')=='original-CF4-current-readonly-classification-v1'and result.get('classification')=='ready'and result['response']==inputs['ready_raw']and result['fields']['provider_scope_ready']==current and result['business_inputs']==0,'readiness-observer-result-derived')
 need(read(refs['tree.json'])==response['result']['tree'],'readiness-observer-tree')
 need(index['original_saved_summary']and index['classification']=='ready'and index['page_filtered']==current['page_filtered']and index['new_inputs']==0 and index['retry']==0,'readiness-observer-index-derived')
 return response,[inputs['ready_observation'],index['original_saved_summary'],*refs.values()]
