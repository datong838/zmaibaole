"""Same-round, evidence-bound download deferral. No RPC, input or invented ready.
The daily scheduler row is never parked/rewritten: only ownership moves to the
original two collection tasks. Existing immutable/CAS coordinator exchange is used.
"""
import copy,fcntl,importlib.util,os
from .common import *
KIND='same-round-expired-download-defer-v1'
KEY='same_round_deferred_download'
CONTRACT='three-flow-collection-ready-v1'
def _checkpoint(stage):pass # TEMP fault injection only; production never supplies a callback

def material(reference):
 p=Path(reference['path']);need(p.is_absolute()and p.resolve()==p and not any(q.is_symlink()for q in(p,*p.parents))and p.is_file(),'defer-canonical-required');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'defer-material-changed');return raw
def raw_archive(path,raw):
 """Immutable byte copy: a CAS source is never JSON-decoded/re-encoded."""
 path=Path(path);need(type(raw)is bytes,'defer-archive-bytes');path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(not path.is_symlink()and path.read_bytes()==raw,'defer-raw-archive-conflict');return ref(path)
 fd,tmp=tempfile.mkstemp(dir=path.parent)
 try:
  with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
  try:os.link(tmp,path)
  except FileExistsError:need(not path.is_symlink()and path.read_bytes()==raw,'defer-raw-archive-conflict')
  syncdir(path.parent)
 finally:os.unlink(tmp)
 return ref(path)

def canonical(reference):return json.loads(material(reference))

def coordinator(e):
 from .adapters import modules
 return modules(e.config)[0]

@contextlib.contextmanager
def locks(e,operator=None):
 paths=[Path(e.config['resource_lock']),e.root/'scheduler.lock',Path(e.config['coordinator_root'])/'.lock']
 if operator:paths.append(operator)
 with contextlib.ExitStack()as stack:
  for path in paths:
   need(path.is_file()and not any(p.is_symlink()for p in(path,*path.parents)),'defer-existing-lock-required');fd=os.open(path,os.O_RDWR|os.O_NOFOLLOW);stack.callback(os.close,fd);fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);stat=os.fstat(fd)
   need((stat.st_dev,stat.st_ino)==(path.stat().st_dev,path.stat().st_ino),'defer-lock-inode')
  yield

def quiet(e):
 need(not any(t['state']in('running','dispatching','unknown')for t in e.s.tasks()),'defer-active-or-unknown-task')

def validate_proof(e,proof_ref):
 p=canonical(proof_ref);need(p.get('kind')==KIND,'defer-proof-kind');task=canonical(p['task']);need(task==e.s.task(task['id'])and task['state']=='failed'and task['flow']==FLOWS[0]and task['payload'].get('collection_contract')==CONTRACT and e.s.get('resource_owner')==task['id'],'defer-original-failed-daily-owner');quiet(e)
 original=Path(task['active_attempt']);ended=canonical(p['worker_exit']);need(p['worker_exit']['path']==str(original/'exit.json')and ended['returncode']!=0 and ended['attempt_id']==original.name,'defer-natural-failed-worker');request=canonical(ended['request']);need(request['task']['id']==task['id']and request['task']['outer']==task['outer']and request['context']==task['context'],'defer-original-request')
 required=[original/n for n in('started.json','spawn.json','child-process.json','parent-operator-process.json')];need([r['path']for r in p['dead_processes']]==list(map(str,required)),'defer-exact-process-records')
 for r in p['dead_processes']:need(not same_process(canonical(r)['process']),'defer-worker-live')
 job=canonical(p['job']);state=canonical(p['workflow']);need(job['workflow_path']==p['workflow']['path']and p['job']==task['context']['operator']['work_order'],'defer-original-job');parent=canonical(p['parent']);need(parent['order']==task['context']['order'],'defer-original-parent-order')
 project=Path(e.config['project']);source=project/'skills/douyin-laike-operator/scripts/popup-recover-download.py';need(ref(source)==p['qualifier_source'],'defer-qualifier-source');spec=importlib.util.spec_from_file_location('same_round_defer_popup_qualifier',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 validated,formal=m.verified_order(job,state['record_tab_id']);need(validated==state and str(formal)==p['workflow']['path'],'defer-canonical-download-history')
 # Existing qualifier validates the sole old typed UNKNOWN and every later call.
 # Independently reject any unowned tail UNKNOWN, including non-input operations.
 unknown=[x for x in state['calls']if x.get('state')=='unknown'];need(len(unknown)<=1 and all(x.get('stage')=='searchCompany' or str(x.get('key','')).endswith(':searchCompany') for x in unknown),'defer-new-unknown')
 ticket=state['download_ticket'];need(timestamp(now()).timestamp()*1000>=ticket['expires'],'defer-ticket-not-expired')
 x=canonical(p['readonly_exit']);need(x.get('returned_naturally')is True,'defer-readonly-natural-exit');intent=canonical(x['intent']);reply=canonical(x['response'])
 need(intent['WF_before']==p['workflow']and intent['task']['id']==task['id']and intent['task']['attempt']==task['attempt']and intent['owner']==task['id']and json.loads(intent['task']['outer'])==task['outer']and intent['command']=={'op':'download-reconcile','tabId':state['record_tab_id'],'groupid':str(job['groupid']),'ticket':ticket['ticket'],'since':ticket['since'],'filename':'门店评价_全部门店_'+job['date_range']['start'].replace('-','_')+'-'+job['date_range']['end'].replace('-','_')+'.xlsx'},'defer-exact-original-query')
 need(timestamp(x['at']).timestamp()*1000>=ticket['expires']and reply=={'ok':True,'result':{'state':'pending','ticket':ticket['ticket'],'readonly':True,'reconciled':True},'error':None},'defer-expired-readonly-pending')
 same=[t for t in e.s.tasks()if t['plan_id']==task['plan_id']and t['day']==task['day']];need(len(same)==3 and {t['flow']for t in same}==set(FLOWS),'defer-exact-original-trio')
 for t in same:
  need(t['payload'].get('collection_contract')==CONTRACT,'defer-contract')
  if t['id']!=task['id']:need(t['state']=='queued'and t['attempt']==0 and not t['active_attempt']and not t['context']and not t['outer'],'defer-successor-not-fresh')
 offer=canonical(task['context']['offer']);root=Path(e.config['coordinator_root']);s=read(root/'state.json');need(s['day']==task['day']and s['index']==0 and s['phase']=='running'and s['dispatch_id']==offer['dispatch_id']and not s.get('collection_ready_reports')and not s.get('deferred_download'),'defer-original-coordinator');return p,task,s,same

def session(e):
 r=e.s.get(KEY)
 if not r:return None
 value=canonical(r);need(value['kind']==KIND and value['root']==str(e.root),'defer-session-binding');return value

def phase(e,s):
 committed=e.s.get('defer-stage:'+s['folder'])
 if committed:return committed
 p=Path(s['folder'])/'phase.json';return read(p)['phase']if p.exists()else'pending'

def unchanged_daily(e,s):
 need(e.s.task(s['daily']['id'])==s['daily'],'defer-daily-task-changed')
 for r in s['preserved']:material(r)
 proof=canonical(s['proof'])
 for r in proof['dead_processes']:need(not same_process(canonical(r)['process']),'defer-original-caller-live')

def exchange(e,c,s,label,after,owner,expected_owner,*,extra_guard=None):
 """Durable intent before coordinator CAS then scheduler transaction, same ticket."""
 if extra_guard:extra_guard()
 folder=Path(s['folder'])/label;root=Path(e.config['coordinator_root']);ip=folder/'intent.json'
 if not ip.exists():
  need(e.s.get('resource_owner')==expected_owner,'defer-owner-raced');before=raw_archive(folder/'state-before.json',(root/'state.json').read_bytes());config=ref(root/'coordinator.json');snapshot=immutable(folder/'state-after.json',after)
  immutable(ip,{'kind':KIND+'-transition','session':e.s.get(KEY),'before':before,'config':config,'after':snapshot,'before_owner':expected_owner,'after_owner':owner,'daily':s['daily']})
 plan=canonical(ref(ip));need(plan['kind']==KIND+'-transition'and plan['session']==e.s.get(KEY)and plan['daily']==s['daily']and plan['after']==ref(folder/'state-after.json')and plan['after_owner']==owner and plan['before_owner']==expected_owner and canonical(plan['after'])==after and plan['before']['path']==str(folder/'state-before.json'),'defer-transition-intent');canonical(plan['before']);unchanged_daily(e,s)
 before=plan['before'];supplement=folder/'raw-before-supplement.json';live=(root/'state.json').read_bytes()
 need(ref(root/'coordinator.json')==plan['config'],'defer-coordinator-raced')
 if supplement.exists():
  correction=canonical(ref(supplement));need(set(correction)=={'kind','intent','old_before','raw_before'}and correction['kind']=='defer-original-intent-raw-before-v1'and correction['intent']==ref(ip)and correction['old_before']==plan['before']and correction['raw_before']['path']==str(folder/'state-before-raw.json'),'defer-raw-supplement-binding');before=correction['raw_before']
  need(label=='collecting'and material(plan['before'])==encode(canonical(before))and canonical(before)==canonical(s['original_coordinator']),'defer-raw-supplement-not-original')
 elif hashlib.sha256(live).hexdigest()not in(plan['before']['sha256'],plan['after']['sha256']):
  # Only the original pre-CAS collection intent created by the old JSON
  # encoder can be repaired. Preserve it and every old archive byte-for-byte.
  need(label=='collecting'and phase(e,s)=='pending'and expected_owner==s['daily']['id']==e.s.get('resource_owner')and all(e.s.task(t['id'])==t for t in s['trio'])and material(plan['before'])==encode(json.loads(live))and canonical(plan['before'])==canonical(s['original_coordinator']),'defer-coordinator-raced')
  before=raw_archive(folder/'state-before-raw.json',live);immutable(supplement,{'kind':'defer-original-intent-raw-before-v1','intent':ref(ip),'old_before':plan['before'],'raw_before':before});_checkpoint(label+'-raw-supplement-written')
 need(hashlib.sha256((root/'state.json').read_bytes()).hexdigest()in(before['sha256'],plan['after']['sha256']),'defer-coordinator-raced')
 if extra_guard:extra_guard()
 # Real primitive receives exact original/new bytes, including on reentry.
 c.exchange_quiescent_state(root,before,plan['config'],plan['after'],plan['config']);_checkpoint(label+'-coordinator-written')
 with e.s.transaction():
  unchanged_daily(e,s)
  if extra_guard:extra_guard()
  need(e.s.get('resource_owner')in(expected_owner,owner),'defer-owner-raced');e.s.set('resource_owner',owner)
  if e.s.get('defer-transition:'+str(ip))is None:e.s.event('deferred-download-'+label,s['daily']['id'],intent=ref(ip));e.s.set('defer-transition:'+str(ip),ref(ip))
 _checkpoint(label+'-owner-committed')
 immutable(folder/'result.json',{'intent':ref(ip),'coordinator_after':plan['after'],'owner':owner,'daily_unchanged':s['daily']});atomic(Path(s['folder'])/'phase.json',{'phase':label})

def start(e,proof_ref):
 p=canonical(proof_ref)
 with locks(e,Path(p['workflow']['path']).parent/'.bridge-execution.lock'):
  if e.s.get(KEY):
   s=session(e);need(s['proof']==proof_ref,'defer-another-session');return {'action':'inspect-original-defer','phase':phase(e,s),'session':e.s.get(KEY)}
  p,task,state,trio=validate_proof(e,proof_ref);c=coordinator(e);folder=e.root/'deferred-downloads'/proof_ref['sha256'];original=raw_archive(folder/'original-coordinator.json',(Path(e.config['coordinator_root'])/'state.json').read_bytes());need(canonical(original)==state,'defer-original-coordinator-raced')
  next_task=next(t for t in trio if t['flow']==FLOWS[1]);sref=immutable(folder/'session.json',{'kind':KIND,'root':str(e.root),'folder':str(folder),'proof':proof_ref,'daily':task,'trio':trio,'original_coordinator':original,'created_at':now(),'preserved':[p[k]for k in('job','workflow','parent','worker_exit','readonly_exit','qualifier_source')]+p['dead_processes']})
  with e.s.transaction():need(e.s.get(KEY)is None and e.s.get('resource_owner')==task['id'],'defer-session-raced');e.s.set(KEY,sref)
  _checkpoint('session-written');s=canonical(sref);after=copy.deepcopy(state);after.update(index=1,phase='ready',attempt=0,deferred_download={'kind':KIND,'session':sref,'status':'collecting-other-two'});after['events'].append({'type':'download-deferred','dispatch_id':state['dispatch_id'],'session':sref,'at':s['created_at']});exchange(e,c,s,'collecting',after,next_task['id'],task['id']);return {'action':'deferred-download-collect-other-two','session':sref,'owner':next_task['id'],'daily_unchanged':True}

def admission(e):
 s=session(e)
 if s and phase(e,s)=='collecting':
  unchanged_daily(e,s);need(e.s.get('resource_owner')in[t['id']for t in s['trio']if t['id']!=s['daily']['id']],'defer-owner-outside-original-peers');return s
 return None

def collection_transition(e,task):
 s=session(e)
 if not s:return None
 need(e.s.db.in_transaction,'defer-transfer-requires-store-transaction')
 stage=phase(e,s)
 if stage=='collecting':
  unchanged_daily(e,s);need(task['plan_id']==s['daily']['plan_id']and task['day']==s['daily']['day']and task['state']=='collection-ready','defer-other-round');ready_packet(task,s)
  if task['flow']==FLOWS[1]:
   original=next(t for t in s['trio']if t['flow']==FLOWS[2]);need(e.s.task(original['id'])==original and e.s.get('resource_owner')==task['id'],'defer-successor-changed');e.s.set('resource_owner',original['id']);e.s.event('deferred-collection-transferred',original['id'],session=e.s.get(KEY));return {'action':'deferred-collection-transferred','task':original['id']}
  need(task['flow']==FLOWS[2],'defer-unexpected-ready');return {'action':'deferred-await-original-daily-restoration','task':s['daily']['id']}
 if stage=='primary-first'and task['id']==s['daily']['id']:
  need(task==e.s.task(task['id'])and task['state']=='collection-ready'and all(task[k]==s['daily'][k]for k in('id','plan_id','day','flow','payload','outer')),'withdrawal-original-daily-real-ready');ready_packet(task,s);record=canonical(ref(Path(s['folder'])/'primary-first/withdrawal-proof.json'));proof=canonical(record['proof']);withdrawal_terminal(e,s,record['proof']);peer=canonical(proof['peer']);current=e.s.task(peer['id']);need(e.s.get('resource_owner')==task['id']and current==peer,'withdrawal-peer-not-original-failed');e.s.set('resource_owner',peer['id']);e.s.event('withdrawn-defer-daily-ready-owner-returned',peer['id'],withdrawal=ref(Path(s['folder'])/'primary-first/result.json'));e.s.set('defer-stage:'+s['folder'],'primary-first-peers');return {'action':'primary-first-original-peer-handoff','task':peer['id'],'state':current['state'],'official_repair_required':current['state']=='failed'}
 if stage=='restored'and task['id']==s['daily']['id']:
  from .staged_delivery import delivery_context
  final=next(t for t in e.s.tasks()if t['plan_id']==task['plan_id']and t['day']==task['day']and t['flow']==FLOWS[2]);context=delivery_context(final,e.s.tasks());e.s.update(final['id'],state='queued',context=context,error=None);e.s.set('resource_owner',final['id']);e.s.event('deferred-three-real-ready-delivery-staged',final['id'],session=e.s.get(KEY));e.s.set('defer-stage:'+s['folder'],'delivery-staged');return {'action':'delivery-staged','task':final['id'],'business_complete':False}
 return None

def ready_packet(task,s):
 # The worker's real rc0 collection-ready exit, already deep-verified at harvest,
 # must still bind the current scheduler context and original task/outer.
 folder=Path(task['active_attempt']);ended=read(folder/'exit.json');response=canonical(ended['response']);request=canonical(ended['request'])
 need(ended['returncode']==0 and ended['attempt_id']==folder.name==request['attempt_id']==response['attempt_id']and response['task_id']==task['id']and response['outcome']=='collection-ready','defer-natural-peer-ready-required')
 need(all(request['task'][k]==task[k]for k in('id','flow','day','plan_id','outer'))and task['context']=={**response['context'],'collection_ready_receipt':response['collection_ready'],'collection_ready_attempt':str(folder)},'defer-peer-context-binding')
 for name in('started.json','spawn.json','child-process.json','parent-operator-process.json'):
  p=folder/name
  if p.exists():need(not same_process(read(p)['process']),'defer-peer-caller-live')

def advance(e):
 s=session(e)
 if not s or phase(e,s)not in('pending','collecting'):return None
 # Recovery after an interrupted original intent never manufactures another one.
 try:
  with locks(e,Path(canonical(s['proof'])['workflow']['path']).parent/'.bridge-execution.lock'):
   plan=next((p for p in e.s.plans()if p['id']==s['daily']['plan_id']),None);need(plan is not None,'defer-original-plan-missing')
   if plan['state']!='active':return None # official lifecycle load must preserve business owner/state
   if any(t['state']in('running','dispatching','unknown')for t in e.s.tasks()):return None
   quiet(e);c=coordinator(e);unchanged_daily(e,s);stage=phase(e,s)
   if stage=='pending':
    state=copy.deepcopy(canonical(s['original_coordinator']));state.update(index=1,phase='ready',attempt=0,deferred_download={'kind':KIND,'session':e.s.get(KEY),'status':'collecting-other-two'});state['events'].append({'type':'download-deferred','dispatch_id':state['dispatch_id'],'session':e.s.get(KEY),'at':s['created_at']});target=next(t for t in s['trio']if t['flow']==FLOWS[1]);exchange(e,c,s,'collecting',state,target['id'],s['daily']['id']);return {'action':'deferred-original-intent-reconciled'}
   resume=Path(s['folder'])/'restored/intent.json'
   if resume.exists():
    plan=read(resume);exchange(e,c,s,'restored',canonical(plan['after']),plan['after_owner'],plan['before_owner']);return {'action':'deferred-original-restore-intent-reconciled'}
   peers=[e.s.task(t['id'])for t in s['trio']if t['id']!=s['daily']['id']]
   if not all(t['state']=='collection-ready'for t in peers):return None
   root=Path(e.config['coordinator_root']);current=read(root/'state.json');reports=current.get('collection_ready_reports',{});need(current['index']==3 and current['phase']=='ready'and set(reports)==set(FLOWS[1:])and current['deferred_download']=={'kind':KIND,'session':e.s.get(KEY),'status':'collecting-other-two'},'defer-real-peer-readiness')
   for t in peers:
    need(t['context']['collection_ready_receipt']['report']==reports[t['flow']],'defer-peer-report-binding');ready_packet(t,s);canonical(reports[t['flow']])
   after=copy.deepcopy(canonical(s['original_coordinator']));after['collection_ready_reports']=reports;after['events']=current['events']+[{'type':'deferred-daily-restored','session':e.s.get(KEY),'at':now()}];after['deferred_download']={'kind':KIND,'session':e.s.get(KEY),'status':'restored-await-original-download'};last=next(t for t in peers if t['flow']==FLOWS[2]);exchange(e,c,s,'restored',after,s['daily']['id'],last['id']);return {'action':'deferred-original-daily-restored','task':s['daily']['id'],'state':'failed','no_retry':True}
 except BlockingIOError:return None


WITHDRAW_KIND='same-round-bind-preinput-defer-withdrawal-v1'
def withdrawal_before(e,s,proof):
 path=Path(s['folder'])/'primary-first/state-before.json';root=Path(e.config['coordinator_root']);need(proof['coordinator']['path']==str(root/'state.json'),'withdrawal-original-coordinator-path')
 if path.exists():
  r=ref(path);need(r['sha256']==proof['coordinator']['sha256'],'withdrawal-original-before-bytes');return canonical(r)
 return canonical(proof['coordinator'])

def withdrawal_facts(e,s,proof_ref,*,resume=False):
 """Only failed first peer before any role order/UI, not business rollback."""
 proof=canonical(proof_ref);need(proof.get('kind')==WITHDRAW_KIND and proof['session']==e.s.get(KEY),'withdrawal-proof-session');quiet(e);unchanged_daily(e,s)
 peer=canonical(proof['peer']);expected=next(t for t in s['trio']if t['flow']==FLOWS[1]);need(peer==e.s.task(peer['id'])and all(peer[k]==expected[k]for k in('id','plan_id','day','flow','payload','due','rank'))and peer['state']=='failed'and peer['attempt']==1 and peer['error']=='worker-exit:1'and peer['context']=={} and peer['outer'],'withdrawal-exact-peer-preinput-failure')
 last=next(t for t in s['trio']if t['flow']==FLOWS[2]);need(e.s.task(last['id'])==last and last['state']=='queued'and last['attempt']==0 and not last['context']and not last['active_attempt'],'withdrawal-last-peer-not-fresh')
 A=Path(peer['active_attempt']);need(A==e.root/'attempts'/(peer['id']+'-1'),'withdrawal-original-attempt');ended=canonical(proof['worker_exit']);need(proof['worker_exit']['path']==str(A/'exit.json')and ended['returncode']==1 and ended['response']is None and ended['attempt_id']==A.name,'withdrawal-natural-preinput-failure');request=canonical(ended['request']);need(request['attempt_id']==A.name and request['context']=={} and all(request['task'][k]==peer[k]for k in('id','flow','day','plan_id','outer')),'withdrawal-original-worker-request')
 call=canonical(proof['coordinator_call']);need(proof['coordinator_call']['path']==str(A/'coordinator-call-intent.json')and call=={'kind':'local-coordinator-call-intent-v1','request':ended['request'],'day':peer['day'],'flow':peer['flow'],'at':call['at']},'withdrawal-only-coordinator-call')
 need(proof['stderr']==ended['stderr']and material(proof['stderr']).decode().rstrip().endswith('ValueError: execution-current-daily-finish-required'),'withdrawal-exact-bind-leaf')
 paths=[A/n for n in('started.json','spawn.json','child-process.json')];need([r['path']for r in proof['dead_processes']]==list(map(str,paths)),'withdrawal-exact-callers')
 for r in proof['dead_processes']:need(not same_process(canonical(r)['process']),'withdrawal-live-caller')
 for name in('offer.json','coordinator-dispatch-intent.json','browser-scope-resolution.json','parent-operator-process.json','parent-operator-intent.json'):
  need(not(A/name).exists()and not(A/name).is_symlink(),'withdrawal-business-stage-exists')
 before=withdrawal_before(e,s,proof);need(before['day']==s['daily']['day']and before['index']==1 and before['phase']=='attention'and before.get('attention_reason')=='role-order-preparation-failed-before-dispatch'and before.get('deferred_download')=={'kind':KIND,'session':e.s.get(KEY),'status':'collecting-other-two'}and not before.get('collection_ready_reports')and not before.get('delivery_complete')and not before.get('unified_delivery'),'withdrawal-only-uncollected-round')
 dispatch=before['dispatch_id'];need(dispatch==peer['day']+':'+FLOWS[1]+':0'and sum(event.get('type')=='role-order-preparation-stopped'and event.get('dispatch_id')==dispatch and event.get('dispatch_outcome')=='not-dispatched'and event.get('error')=='execution-current-daily-finish-required'for event in before['events'])==1,'withdrawal-preinput-dispatch-outcome')
 root=Path(e.config['coordinator_root']);stem=hashlib.sha256(dispatch.encode()).hexdigest()
 for path in(root/'role-execution-orders'/(stem+'.json'),root/'dispatch-offers'/(stem+'.json'),root/'role-executions'/stem):need(not path.exists()and not path.is_symlink(),'withdrawal-role-order-or-parent-exists')
 need(e.s.get('resource_owner')in((peer['id'],s['daily']['id'])if resume else(peer['id'],)),'withdrawal-original-owner')
 if not resume:need(phase(e,s)=='collecting'and ref(root/'state.json')==proof['coordinator'],'withdrawal-coordinator-changed')
 return proof,peer,before

def withdrawal_after(e,s,proof,bound):
 before=withdrawal_before(e,s,proof);after=copy.deepcopy(canonical(s['original_coordinator']));after['events']=before['events']+[{'type':'deferred-download-withdrawn-primary-first','session':e.s.get(KEY),'proof':bound,'at':proof['recorded_at']}];after['deferred_download']={'kind':KIND,'session':e.s.get(KEY),'status':'primary-first','withdrawal':bound};return after

def withdrawal_terminal(e,s,proof_ref):
 folder=Path(s['folder'])/'primary-first'
 plan=canonical(ref(folder/'intent.json'));result=canonical(ref(folder/'result.json'));bound=ref(folder/'withdrawal-proof.json');binding=canonical(bound);proof=canonical(proof_ref);peer=canonical(proof['peer'])
 need(binding=={'kind':WITHDRAW_KIND,'proof':proof_ref,'session':e.s.get(KEY)}and proof['kind']==WITHDRAW_KIND and proof['session']==e.s.get(KEY),'withdrawal-terminal-proof')
 need(plan=={'kind':KIND+'-transition','session':e.s.get(KEY),'before':ref(folder/'state-before.json'),'config':ref(Path(e.config['coordinator_root'])/'coordinator.json'),'after':ref(folder/'state-after.json'),'before_owner':peer['id'],'after_owner':s['daily']['id'],'daily':s['daily']}and plan['before']['sha256']==proof['coordinator']['sha256']and canonical(plan['before'])==withdrawal_before(e,s,proof)and canonical(plan['after'])==withdrawal_after(e,s,proof,bound),'withdrawal-terminal-plan');canonical(plan['config'])
 need(result=={'intent':ref(folder/'intent.json'),'coordinator_after':plan['after'],'owner':s['daily']['id'],'daily_unchanged':s['daily']},'withdrawal-terminal-result')
 return plan

def withdraw_primary_first(e,proof_ref):
 """No task mutation/input/retry: restore original daily coordinator/owner only.
 Original failed peer and every old intent remain available for official repair.
 A completed withdrawal is inspect-only even after later ordinary business.
 """
 s=session(e);need(s is not None,'withdrawal-no-session');folder=Path(s['folder'])/'primary-first'
 with locks(e,Path(canonical(s['proof'])['workflow']['path']).parent/'.bridge-execution.lock'):
  if(folder/'result.json').exists():
   plan=withdrawal_terminal(e,s,proof_ref)
   if phase(e,s)=='collecting':
    withdrawal_facts(e,s,proof_ref,resume=True);need(e.s.get('resource_owner')==s['daily']['id']and ref(Path(e.config['coordinator_root'])/'state.json')['sha256']==plan['after']['sha256'],'withdrawal-terminal-incomplete-phase');atomic(Path(s['folder'])/'phase.json',{'phase':'primary-first'})
   return {'action':'inspect-original-withdrawal','result':ref(folder/'result.json'),'replayed':False}
  proof,peer,before=withdrawal_facts(e,s,proof_ref,resume=(folder/'intent.json').exists());bound=immutable(folder/'withdrawal-proof.json',{'kind':WITHDRAW_KIND,'proof':proof_ref,'session':e.s.get(KEY)});after=withdrawal_after(e,s,proof,bound)
  exchange(e,coordinator(e),s,'primary-first',after,s['daily']['id'],peer['id'],extra_guard=lambda:withdrawal_facts(e,s,proof_ref,resume=True));return {'action':'defer-withdrawn-primary-first','result':ref(folder/'result.json'),'owner':s['daily']['id'],'peer_failed_unchanged':peer['id'],'business_inputs':0}
