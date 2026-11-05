"""Strict pure held-filter observation proof. Never invokes bridge or inputs.
Normal pending reads stay in Workflow's original bounded3 loop.
"""
import copy,hashlib,importlib.util,json,sys,os
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[3]
KIND='verified-held-filter-readonly-ready-v1';FIELD='confirmed_bounded_filter_readonly_recovery';ERROR='review-filter-loading-exhausted'
PROVIDER_SHA='bd11b03234dc4c16970e09f8e4d8ba847c23cb6f2e4876df5b1957c2c635f893'
OBSERVER_SHA='72bbd8f0f8c63243df662534b2bd0a250825f9c3102a2eac19933980fe08882c'
def need(ok,reason):
 if not ok:raise ValueError(reason)
def ref(path):return {'path':str(path),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
def raw(r):
 p=Path(r['path']);need(p.is_absolute()and p.resolve()==p and not any(q.is_symlink()for q in(p,*p.parents))and p.is_file(),'held-filter-canonical-material');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'held-filter-material-drift');return b
def doc(r):return json.loads(raw(r))
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def provider():
 path=ROOT/'packages/workshop-director/workshop_director/filter_readiness_recovery.py';need(ref(path)['sha256']==PROVIDER_SHA,'held-filter-provider-generation');spec=importlib.util.spec_from_file_location('_held_filter_provider',path);module=importlib.util.module_from_spec(spec);exec(compile(raw(ref(path)),str(path),'exec'),module.__dict__);module.modules();return module

def qualify(inputs,read=doc,read_bytes=raw):
 seen=[];original_read=read;original_bytes=read_bytes
 def read(r):
  value=original_read(r);seen.append(r);return value
 def read_bytes(r):
  value=original_bytes(r);seen.append(r);return value
 need(type(inputs)is dict and set(inputs)=={'job','original','ready_observation'},'held-filter-inputs');job=read(inputs['job']);state=read(inputs['original']);p=provider()
 need(job['action']=='acquire'and job['work_order_path']==inputs['job']['path']and job['workflow_path']==inputs['original']['path'],'held-filter-original-paths')
 dates={k:job['date_range'][k]for k in('start','end')}
 need(state['state']=='running'and state['phase']=='verifyFilter'and state['work_order_id']==job['work_order_id']and state['company']==job['company']and str(state['groupid'])==str(job['groupid'])and state['date_range']==dates and state['identity']==job['identity_baseline'],'held-filter-job-scope')
 import switch_read_recovery as switch
 need(state['fingerprint']==switch.fingerprint(job),'held-filter-job-fingerprint')
 error=state.get('last_error');need(type(error)is dict and set(error)=={'at','code','message'}and(error['code'],error['message'])==(ERROR,ERROR)and FIELD not in state,'held-filter-exact-error')
 calls=state['calls'];need(len(calls)in(5,10)and all(c.get('state')=='confirmed'for c in calls)and len({c['key']for c in calls})==len(calls),'held-filter-confirmed-prefix')
 materials=[inputs['job'],inputs['original'],inputs['ready_observation'],ref(Path(p.__file__)),ref(Path(switch.__file__))]
 if len(calls)==10:
  need(job.get('company_configuration_registry')=='configured-source-index-v2','held-filter-configured-prefix');checked,switch_ref,tree=p._configured_switch_prefix(job,state,read);materials.extend([switch_ref,tree])
 tail=calls[-5:];phases=['openReviews','openReviews','openPageCalendar','pageStart','pageEnd']
 need([c['phase']for c in tail]==phases and state['revision']==int(tail[-1]['key'].split(':')[0])+1,'held-filter-confirmed-tail')
 for call,phase in zip(tail,phases):
  cmd=call['command'];clicked=call.get('result',{}).get('clicked',{});need(call['key'].split(':')[1]==phase and cmd.get('op')=='click'and cmd.get('tabId')==state['tab_id']and cmd.get('kind')==('navigation'if phase=='openReviews'else'filter')and cmd.get('locator')=={'by':'selector','value':clicked.get('selector')}and call['result'].get('kind')==cmd['kind'],'held-filter-action-binding')
 need(tail[-2]['result']['clicked']['name']==str(int(dates['start'][-2:]))and tail[-1]['result']['clicked']['name']==str(int(dates['end'][-2:])),'held-filter-date-days')
 need(not any(state.get(k)for k in('exportPending','downloadPending','export_pending','download_pending','submittedAt','result','record_tab_id','record_url')),'held-filter-no-export-input')
 reads=state.get('review_filter_loading_reads');need(type(reads)is list and len(reads)==3 and [r['attempt']for r in reads]==[0,1,2],'held-filter-three-spent');previous=None;pending=None
 for row in reads:
  reply=read(row['reply']);need(reply.get('ok')is True and reply.get('error')is None,'held-filter-original-read-reply');scope=p.scope(job,state,reply['result'],read,pending=True)
  need(row['command']=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':scope['window_id']}and read(row['tree'])==reply['result']['tree'],'held-filter-original-read-source')
  if previous is None:
   initial=read(row['before_tree']);dom,_,loading=p.modules();dom.identity(initial,job['identity_baseline']);loading.validate_filter_values(initial,dates);loading.validate_pending_store_scope(initial);need(loading.is_loading(initial),'held-filter-initial-pending')
  else:need(row['before_tree']==previous,'held-filter-original-read-chain')
  dom,_,_=p.modules();need(not any(n.get('name')=='系统错误，请稍后再试'for n in dom.nodes(reply['result']['tree'])),'held-filter-system-error')
  need(pending is None or pending==scope,'held-filter-original-read-identity');pending=scope;previous=row['tree'];materials.extend([row['before_tree'],row['reply'],row['tree']])
 need(state['last_tree']==previous,'held-filter-last-tree')
 index=read(inputs['ready_observation']);need(index.get('kind')=='original-CF5-once-current-filter-readonly-evidence-index-v1'and index.get('new_inputs')==0 and index.get('no_metadata_retry')is True and index.get('stdout_is_classification_not_raw_response')is True,'held-filter-observer-protocol')
 refs={Path(r['path']).relative_to(Path(inputs['ready_observation']['path']).parent).as_posix():r for r in index['refs']}
 names={'read_once.py','binding.json','read-baseline.json','root-readonly-authorization.json','authority-record.json','command.json','intent.json','request-started.json','request-returned.json','response.json','tree.json','result.json','exec/started.json','exec/process.json','exec/stdout.log','exec/stderr.log','exec/natural-exit.json'}
 need(len(refs)==len(index['refs'])==17 and set(refs)==names and refs['read_once.py']['sha256']==OBSERVER_SHA,'held-filter-observer-files')
 for r in refs.values():read_bytes(r)
 binding=read(refs['binding.json']);authority=read(refs['authority-record.json']);auth=read(refs['root-readonly-authorization.json']);intent=read(refs['intent.json']);command=read(refs['command.json']);start=read(refs['request-started.json']);returned=read(refs['request-returned.json']);outer=read(refs['exec/started.json']);process=read(refs['exec/process.json']);exit=read(refs['exec/natural-exit.json']);response=read(refs['response.json']);result=read(refs['result.json'])
 need(binding['max_requests']==1 and binding['refs']=={'job':inputs['job'],'workflow':inputs['original']}and authority['original_WF']==inputs['original']and authority['task']==binding['task']['id']and authority['maximum_requests']==1 and authority['business_inputs_allowed']==0,'held-filter-observer-binding')
 need(auth.get('execution_authorized')is True and auth['binding']==refs['binding.json']and auth['actor']==refs['read_once.py']and auth['baseline']==refs['read-baseline.json']and authority['authority']==refs['root-readonly-authorization.json'],'held-filter-observer-authority')
 need(command=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':pending['window_id']}and authority['command']==command and intent['command']==refs['command.json']and intent['original_job']==inputs['job']and intent['original_workflow']==inputs['original']and intent['business_inputs_allowed']==0,'held-filter-observer-intent')
 argv=[str(ROOT/'skills/daily-comment-stats/.venv/bin/python'),'-I','-B',refs['read_once.py']['path'],'--authorization-sha',refs['root-readonly-authorization.json']['sha256'],'--execute']
 need(outer['argv']==process['argv']==argv and process['pid']==start['pid']and type(start['pid'])is int and start['pid']>0 and process.get('process')is None,'held-filter-observer-natural-process')
 need(exit.get('returncode')==0 and type(exit.get('seconds'))in(int,float)and 0<=exit['seconds']<60 and read_bytes(refs['exec/stderr.log'])==b'','held-filter-observer-natural-exit')
 times=[error['at'],outer['at'],intent['at'],start['at'],returned['returned_at'],exit['at']];need(all(p.stamp(a)<=p.stamp(b)for a,b in zip(times,times[1:]))and p.stamp(auth['issued_at'])<=p.stamp(outer['at'])<=p.stamp(exit['at'])<=p.stamp(auth['expires_at']),'held-filter-observer-clock')
 need(returned['response']==refs['response.json']==index['protocol_response_source']and response.get('ok')is True and response.get('error')is None and read(refs['tree.json'])==response['result']['tree'],'held-filter-observer-response')
 dom,_,_=p.modules();need(not any(n.get('name')=='系统错误，请稍后再试'for n in dom.nodes(response['result']['tree'])),'held-filter-system-error');ready=p.scope(job,state,response['result'],read,pending=False);need(all(ready[k]==v for k,v in pending.items()if k!='page_filtered'),'held-filter-ready-same-source')
 stdout=json.loads(read_bytes(refs['exec/stdout.log']));need(stdout.get('result')==refs['result.json']and stdout.get('classification')=='ready'and result.get('classification')=='ready'and result['response']==refs['response.json']and result['fields']['provider_scope_ready']==ready and result.get('business_inputs')==0,'held-filter-observer-result')
 materials.extend(refs.values());materials.append(binding['failure_summary']);read(binding['failure_summary']);materials.extend(seen)
 return {'kind':KIND,'inputs':copy.deepcopy(inputs),'original_error':copy.deepcopy(error),'original_calls':copy.deepcopy(calls),'phase':state['phase'],'revision':state['revision'],'ready':ready,'task_id':binding['task']['id'],'attempt':authority['failed_attempt'],'materials':list({(r['path'],r['sha256']):r for r in materials}.values()),'new_inputs':0}
def transform(original,proof_ref):
 need(original.get('last_error',{}).get('code')==original['last_error'].get('message')==ERROR and FIELD not in original,'held-filter-transform-original');after=copy.deepcopy(original);after.pop('last_error');after[FIELD]=proof_ref;return after
def location(original):return Path(original['path']).parent/'bounded-filter-readiness'/original['sha256']
def verify(proof_ref):
 proof=doc(proof_ref);need(set(proof)=={'kind','module','facts','archives'}and proof['kind']==KIND and proof['module']==ref(Path(__file__).absolute()),'held-filter-proof-source');facts=proof['facts'];base=location(facts['inputs']['original']);need(proof_ref['path']==str(base/'proof.json'),'held-filter-proof-path');mapped={}
 for pair in proof['archives']:
  r,a=pair['original'],pair['archive'];need(a['sha256']==r['sha256']and a['path']==str(base/'materials'/(r['sha256']+'.data')),'held-filter-archive');raw(a);mapped[(r['path'],r['sha256'])]=a
 def read(r):need((r['path'],r['sha256'])in mapped,'held-filter-unarchived');return doc(mapped[(r['path'],r['sha256'])])
 need(qualify(facts['inputs'],read,lambda r:raw(mapped[(r['path'],r['sha256'])]))==facts,'held-filter-proof-derived');original=read(facts['inputs']['original']);return {'facts':facts,'original':original,'after':transform(original,proof_ref)}
