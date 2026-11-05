"""Bounded fresh single-page DOM acquisition. Only bounded identity-display hover; no business input/export/download/sender."""
import argparse,importlib.util,fcntl,hashlib,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
PRODUCER=Path(__file__).absolute().with_name('dom_daily_acquisition.py')
PRODUCER_SHA='0b5479e2271aa3d4118a84e9374daa1f899c4fbd8784ca080568785367a8d22d'
def _producer_module():
 if not PRODUCER.is_file()or PRODUCER.resolve()!=PRODUCER or any(p.is_symlink()for p in(PRODUCER,*PRODUCER.parents)):
  raise ValueError('collector-producer-source-origin')
 raw=PRODUCER.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=PRODUCER_SHA:raise ValueError('collector-producer-source-changed')
 name='_daily_verified_dom_producer_'+PRODUCER_SHA
 if name not in sys.modules:
  spec=importlib.util.spec_from_file_location(name,PRODUCER);module=importlib.util.module_from_spec(spec);exec(compile(raw,str(PRODUCER),'exec'),module.__dict__);sys.modules[name]=module
 module=sys.modules[name]
 if Path(module.__file__)!=PRODUCER:raise ValueError('collector-producer-loaded-origin')
 return module
dom=_producer_module()
sys.path.insert(0,str(ROOT/'packages/workshop-director'))
from workshop_director.common import boot,identity
PYTHON=ROOT/'skills/daily-comment-stats/.venv/bin/python'
BRIDGE=ROOT/'skills/chrome-dom-export/scripts/bridge.py'
SCHEDULER=ROOT/'runtime/standalone-workshop-director'
COORDINATOR=ROOT/'runtime/workshop-director'
KIND='daily-fresh-dom-single-page-capture-v1'
QUALIFIER=ROOT/'skills/douyin-laike-operator/scripts/popup-recover-download.py'
PREPARATION=Path(__file__).absolute().with_name('dom_identity_preparation.py')
PREPARATION_SHA='8d75a06e8cc1ad4c9de3cf312f5a4c904f771ef7a1859698dd8cb38dd1e41eef'
def preparation_module():
 need(PREPARATION.is_file()and PREPARATION.resolve()==PREPARATION and not any(p.is_symlink()for p in(PREPARATION,*PREPARATION.parents))and hashlib.sha256(PREPARATION.read_bytes()).hexdigest()==PREPARATION_SHA,'collector-preparation-source-origin')
 name='_daily_dom_identity_preparation_'+PREPARATION_SHA
 if name not in sys.modules:
  spec=importlib.util.spec_from_file_location(name,PREPARATION);module=importlib.util.module_from_spec(spec);exec(compile(PREPARATION.read_bytes(),str(PREPARATION),'exec'),module.__dict__);sys.modules[name]=module
 module=sys.modules[name];need(Path(module.__file__)==PREPARATION,'collector-preparation-loaded-origin');return module
def need(v,e):
 if not v:raise ValueError(e)
def ref(p):return dom.ref(dom.canonical(p))
def doc(r):return dom.pinned(r)
def stamp():return {'wall_at':datetime.now(timezone.utc).isoformat(),'monotonic_ns':time.monotonic_ns()}
def syncdir(path):
 fd=os.open(path,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def immutable(path,value):
 b=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 with Path(path).open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 syncdir(Path(path).parent);return ref(path)
def archive(path,reference):
 dom.pinned(reference)
 with Path(path).open('xb')as f:f.write(Path(reference['path']).read_bytes());f.flush();os.fsync(f.fileno())
 result=ref(path);need(result['sha256']==reference['sha256'],'capture-archive-race');syncdir(Path(path).parent);return result
def sources():
 need(Path(dom.__file__).absolute()==PRODUCER and ref(PRODUCER)['sha256']==PRODUCER_SHA,'collector-producer-generation')
 return [ref(__file__),ref(PRODUCER),ref(PREPARATION),dom.RATING_EVIDENCE,ref(BRIDGE),ref(ROOT/'skills/douyin-laike-operator/scripts/dom_evidence.py'),ref(ROOT/'skills/douyin-laike-operator/scripts/readonly_tick_snapshot.py'),ref(ROOT/'packages/workshop-director/workshop_director/common.py'),ref(QUALIFIER),ref(QUALIFIER.with_name('chrome-popup-navigation.py')),ref(QUALIFIER.with_name('bridge-workflow.py')),ref(QUALIFIER.with_name('switch_read_recovery.py'))]
def task_snapshot(task_id):
 with sqlite3.connect('file:'+str(SCHEDULER/'queue.sqlite3')+'?mode=ro',uri=True)as db:
  db.row_factory=sqlite3.Row;r=db.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone();need(r is not None,'collector-original-task-missing');task=dict(r)
  for key in ('context','outer','payload'):task[key]=json.loads(task[key])if task[key]else None
  v=db.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();owner=json.loads(v[0])if v else None
 return {'task':task,'resource_owner':owner}
def guard(spec):
 job=spec['job'];need(boot()==job['original_outer']['boot'],'collector-boot-changed');request=doc(job['original_request']);wf=doc(spec['workflow']);order=doc(job['original_order']);lease=doc(spec['lease']);snapshot=task_snapshot(job['original_task']);t=snapshot['task']
 need(snapshot['resource_owner']==job['original_task']and t['id']==job['original_task']and t['flow']=='daily-comment-stats'and t['state']=='failed','collector-legal-original-daily-owner-required')
 need(t['outer']==job['original_outer']and t['context']['order']==job['original_order']and t['context']['scope']=={'pid':job['pid'],'tab_id':job['tab_id']},'collector-current-task-scope')
 need(request['task']['id']==t['id']and request['task']['outer']==t['outer']and request['context']['scope']==t['context']['scope']and request['context']['browser_binding']['process']==t['context']['browser_binding']['process'],'collector-original-request')
 need(lease['dispatch_id']==order['dispatch_id']and lease['day']==order['day']and lease['production_enabled']is False and lease['complaint_submission_enabled']is False and lease['test_target']=='测试群请忽略','collector-original-daily-lease')
 need(wf['company']==job['company']and str(wf['groupid'])==str(job['groupid'])and wf['tab_id']==job['tab_id']and wf['identity']==job['identity']and {k:wf['date_range'][k]for k in ('start','end')}==job['date_range'],'collector-workflow-binding')
 need(wf['phase']=='downloadResult','collector-original-phase')
 binding=t['context']['browser_binding'];need(binding['process']==identity(job['pid'])and binding['scope']['pid']==job['pid']and binding['comm']=='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','collector-live-public-Chrome-process')
 exit_path=Path(t['active_attempt'])/'exit.json';need(exit_path.is_file(),'collector-original-worker-not-terminal');exit_ref=ref(exit_path);ex=doc(exit_ref);need(ex.get('request')==job['original_request'],'collector-current-attempt-request')
 need(spec['lease']['path']==str(COORDINATOR/'state.json')and spec['workflow']['path']==str(Path(job['original_job']['path']).with_name('workflow.json')),'collector-canonical-guards')
 return {'snapshot':snapshot,'lease':spec['lease'],'workflow':spec['workflow'],'original_exit':exit_ref}
def qualify_workflow(spec):
 path=dom.canonical(QUALIFIER);loader=importlib.util.spec_from_file_location('_collector_download_qualifier',path);module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module);wf=doc(spec['workflow']);state,p=module.verified_order(doc(spec['job']['original_job']),wf['record_tab_id']);need(str(p)==spec['workflow']['path']and state==wf and ref(p)==spec['workflow'],'collector-public-qualifier-drift');return {'source':ref(path),'workflow':spec['workflow'],'qualified':True}
def capture_location(spec):
 key=hashlib.sha256(json.dumps([KIND,spec['job']['original_job'],spec['job']['original_request']],sort_keys=True,separators=(',',':')).encode()).hexdigest()[:24]
 return Path(spec['job']['original_job']['path']).parent/'dom-fresh-capture'/key
def run_bridge(command,prefix,folder,intent):
 """One real normal CLI child; even failed/unknown transport has an immutable exit."""
 argv=[str(PYTHON),'-I','-B',str(BRIDGE),'request',json.dumps(command,separators=(',',':')),'--timeout','90']
 request=immutable(folder/(prefix+'-request.json'),{'command':command,'argv':argv,'intent':intent,'started':stamp()})
 with (folder/(prefix+'-stdout.json')).open('xb')as stdout,(folder/(prefix+'-stderr.log')).open('xb')as stderr:
  child=subprocess.Popen(argv,stdout=stdout,stderr=stderr)
  started=immutable(folder/(prefix+'-started.json'),{'pid':child.pid,'ppid':os.getpid(),'argv':argv,'request':request,'started':stamp()})
  rc=child.wait();stdout.flush();os.fsync(stdout.fileno());stderr.flush();os.fsync(stderr.fileno())
 exited=immutable(folder/(prefix+'-natural-exit.json'),{'started':started,'returncode':rc,'ended':stamp(),'stdout':ref(folder/(prefix+'-stdout.json')),'stderr':ref(folder/(prefix+'-stderr.log'))})
 transport=immutable(folder/(prefix+'-transport.json'),{'command':command,'request':request,'started':started,'natural_exit':exited})
 return transport

def bridge_reply(transport):
 record=doc(transport);ex=doc(record['natural_exit'])
 try:reply=doc(ex['stdout'])
 except (ValueError,TypeError):reply=None
 return ex['returncode'],reply

def checked_environment_pending(reference,spec,intent,before):
 value=doc(reference);folder=Path(reference['path']).parent;epoch=doc(value['epoch'])
 need(set(value)=={'kind','epoch','intent','preparation_folder','transport_calls','completed','reason'} and value['kind']=='daily-capture-environment-pending-v1' and value['intent']==intent and epoch['intent']==intent and epoch['before']==before,'collector-pending-contract')
 need(reference['path']==str(folder/'pending.json') and value['epoch']['path']==str(folder/'intent.json') and folder.parent==capture_location(spec)/'environment-epochs','collector-pending-path')
 prep_folder=Path(value['preparation_folder']) if value['preparation_folder'] else None
 calls=value['transport_calls'];dependencies=[reference,value['epoch']];requests=[]
 if prep_folder is not None:
  need(prep_folder.parent==Path(spec['job']['original_job']['path']).parent/'dom-identity-preparation' and len(prep_folder.name)==4 and prep_folder.name.isdigit(),'collector-pending-preparation-path')
  for transport in calls:
   record=doc(transport);command=record['command'];prefix=Path(transport['path']).name.removesuffix('-transport.json')
   if command.get('op')=='readonly-scope':
    expected={'op':'readonly-scope','tabId':spec['job']['tab_id'],'windowId':spec['job']['window_id']};need(command==expected,'collector-pending-read-command');command=expected
   else:
    index=prefix.split('-')[0];sample=doc(ref(prep_folder/(index+'-scope.json')));facts=preparation_module().checked_scope(spec['job'],ref(prep_folder/(index+'-scope.json')),None)
    need(not facts['ready'] and command==facts['command'] and command.get('op')=='hover','collector-pending-environment-only');command=facts['command'];dependencies.append(ref(prep_folder/(index+'-scope.json')))
   record,ex,refs=verify_transport(transport,command,intent,prep_folder,prefix);dependencies.extend(refs);requests.append(record['request']['path'])
  need(sorted(requests)==sorted(str(x)for x in prep_folder.glob('*-request.json')),'collector-pending-unresolved-child')
 else:need(not calls,'collector-pending-unbound-child')
 need(len(calls)<=5 and len([x for x in calls if doc(x)['command']['op']=='readonly-scope'])<=3 and len([x for x in calls if doc(x)['command']['op']=='hover'])<=2,'collector-pending-budget')
 return dependencies

def capture(spec,outdir):
 need(set(spec)=={'kind','job','workflow','lease'}and spec['kind']==KIND,'collector-spec-schema');need(Path(sys.executable)==PYTHON,'collector-fixed-python');code=sources();out=Path(outdir);need(out==capture_location(spec),'collector-original-stable-output');need(out.is_absolute()and out.parent.resolve()==out.parent and not out.is_symlink(),'collector-output-not-canonical')
 resource=COORDINATOR/'browser-wecom.resource.lock';need(resource.is_file()and resource.resolve()==resource and not resource.is_symlink(),'collector-existing-resource-lock-required')
 with resource.open('r+')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);before=guard(spec);qualification=qualify_workflow(spec)
  prior=[]
  if out.exists():
   intent=ref(out/'intent.json');original=doc(intent)
   need(original['spec']==spec and original['sources']==code and original['before']==before and original['qualification']==qualification,'collector-existing-capture-drift')
   if (out/'complete.json').exists():
    complete=ref(out/'complete.json');value=doc(complete);need(value['intent']==intent and value['sources']==code,'collector-complete-reentry-drift');return complete
   need(not(out/'page-0001.json').exists() and not(out/'dom-source').exists(),'collector-producer-outcome-observe-only')
   epochs=sorted((out/'environment-epochs').iterdir())
   need(epochs and all(x.is_dir()and not x.is_symlink()and x.name==f'{i:04d}'for i,x in enumerate(epochs)),'collector-environment-prefix')
   for epoch_folder in epochs:
    need(not(epoch_folder/'observe-only.json').exists(),'collector-unresolved-prefix-observe-only');pending=ref(epoch_folder/'pending.json');checked_environment_pending(pending,spec,intent,before);prior.append(pending)
  else:
   out.parent.mkdir(parents=True,exist_ok=True);out.mkdir();syncdir(out.parent)
   archives=[{'original':spec[k],'archive':archive(out/(k+'-before.json'),spec[k])}for k in ('workflow','lease')]
   intent=immutable(out/'intent.json',{'kind':KIND,'spec':spec,'sources':code,'before':before,'guard_archives':archives,'qualification':qualification,'started':stamp()})
  epochroot=out/'environment-epochs';epochroot.mkdir(exist_ok=True);epochfolder=epochroot/f'{len(prior):04d}';epochfolder.mkdir();syncdir(epochroot)
  epoch=immutable(epochfolder/'intent.json',{'kind':'daily-capture-environment-epoch-v1','intent':intent,'before':before,'prior_pending':prior,'started':stamp(),'budget':{'readonly':3,'environment_hover':2,'business_inputs':0}})
  prep=preparation_module();calls=[];prepfolder=[None]
  def checked_guard():
   current=guard(spec);need(current==before and sources()==code,'collector-protected-state-changed');return current
  def observe(index,folder):
   prepfolder[0]=str(folder);checked_guard();command={'op':'readonly-scope','tabId':spec['job']['tab_id'],'windowId':spec['job']['window_id']}
   transport=run_bridge(command,f'{index:02d}-scope',folder,intent);calls.append(transport);rc,reply=bridge_reply(transport)
   need(rc==0 and type(reply)is dict and reply.get('ok')is True and not reply.get('error')and reply.get('outcome')not in('unknown','not-delivered'),'collector-read-failed-or-unknown-no-replay')
   raw=reply['result'];dom.decode(raw,command['tabId'],command['windowId']);scope=immutable(folder/f'{index:02d}-scope.json',raw)
   return {'scope':scope,'transport':transport}
  def hover(command,index,folder):
   prepfolder[0]=str(folder);checked_guard();transport=run_bridge(command,f'{index:02d}-hover',folder,intent);calls.append(transport)
   # Display is idempotent environment preparation. A failure/UNKNOWN remains
   # recorded; only the subsequent strictly verified scope can establish ready.
   return {'transport':transport}
  def consume(scope,preparation):
   checked_guard();page=archive(out/'page-0001.json',scope)
   producer_receipt=dom.create(spec['job'],[page],dom.POLICY,out/'dom-source')
   prepdoc=doc(preparation);last=doc(prepdoc['samples'][-1]['observed']['transport']);after=checked_guard()
   return immutable(out/'complete.json',{'kind':KIND,'intent':intent,'identity_preparation':preparation,'environment_epoch':epoch,'prior_pending':prior,'transport_calls':calls,'request':last['request'],'started':last['started'],'natural_exit':last['natural_exit'],'pages':[page],'producer_receipt':producer_receipt,'before':before,'after':after,'sources':code,'completed':stamp()})
  try:
   result=prep.prepare_and_consume(spec['job'],Path(spec['job']['original_job']['path']).parent/'dom-identity-preparation',observe=observe,hover=hover,guard=checked_guard,resource_fd=lock.fileno(),consume=consume)
   if result['state']!='ready':raise ValueError('collector-identity-preparation-pending')
   return result['consumed']
  except Exception:
   # Only a closed environment-only prefix is resumable. Any partial child or
   # producer prefix remains observe-only; it cannot receive another epoch.
   if not(out/'page-0001.json').exists() and not(out/'dom-source').exists():
    value={'kind':'daily-capture-environment-pending-v1','epoch':epoch,'intent':intent,'preparation_folder':prepfolder[0],'transport_calls':calls,'completed':stamp(),'reason':'environment-not-ready'}
    candidate=epochfolder/'pending.json'
    # Verify the same pure closure before publishing a resumable terminal.
    provisional=immutable(epochfolder/'pending-proposal.json',value)
    # The proposal is immutable audit, but only pending.json admits reentry.
    value_ref={'path':str(candidate),'sha256':provisional['sha256']}
    try:
     # Use the identical bytes under the canonical terminal name, then verify;
     # invalid closure has a permanent rejected marker and no resumable pending.
     archive(candidate,provisional);checked_environment_pending(value_ref,spec,intent,before)
    except Exception as error:
     immutable(epochfolder/'observe-only.json',{'kind':'capture-unresolved-prefix-v1','epoch':epoch,'validation_error':str(error)})
   raise

def verify_transport(reference,command,intent,folder,prefix):
 record=doc(reference);need(set(record)=={'command','request','started','natural_exit'}and record['command']==command,'capture-transport-command')
 need(reference['path']==str(folder/(prefix+'-transport.json'))and record['request']['path']==str(folder/(prefix+'-request.json'))and record['started']['path']==str(folder/(prefix+'-started.json'))and record['natural_exit']['path']==str(folder/(prefix+'-natural-exit.json')),'capture-transport-paths')
 request=doc(record['request']);started=doc(record['started']);ex=doc(record['natural_exit']);argv=[str(PYTHON),'-I','-B',str(BRIDGE),'request',json.dumps(command,separators=(',',':')),'--timeout','90']
 
 for key,valid in [('request-command',request['command']==command),('request-argv',request['argv']==argv),('request-intent',request['intent']==intent),('started-argv',started['argv']==argv),('started-request',started['request']==record['request']),('pid',type(started['pid'])is int and started['pid']>0),('ppid',type(started['ppid'])is int),('exit-started',ex['started']==record['started']),('exit-code',type(ex['returncode'])is int)]:need(valid,'capture-natural-child-chain-'+key)
 need(ex['stdout']['path']==str(folder/(prefix+'-stdout.json'))and ex['stderr']['path']==str(folder/(prefix+'-stderr.log')),'capture-original-child-stream-paths');need(ref(ex['stderr']['path'])==ex['stderr']and ref(ex['stdout']['path'])==ex['stdout'],'capture-child-stream-drift')
 ticks=[request['started'],started['started'],ex['ended']];need(all(type(t['monotonic_ns'])is int for t in ticks)and [t['monotonic_ns']for t in ticks]==sorted(t['monotonic_ns']for t in ticks)and [datetime.fromisoformat(t['wall_at'])for t in ticks]==sorted(datetime.fromisoformat(t['wall_at'])for t in ticks),'capture-child-clock-order')
 dependencies=[reference,record['request'],record['started'],record['natural_exit'],ex['stdout'],ex['stderr']]
 return record,ex,dependencies

def verify_preparation(reference,spec,intent,before):
 prep=preparation_module();value=doc(reference);folder=Path(reference['path']).parent;root=Path(spec['job']['original_job']['path']).parent/'dom-identity-preparation'
 need(folder.parent==root and len(folder.name)==4 and folder.name.isdigit()and Path(reference['path']).name=='complete.json','capture-identity-preparation-path')
 need(value['kind']==prep.KIND and value['capture_authority']is False and value['business_inputs']==0 and value['code_refs']==prep.code_refs()and value['full_identity']==spec['job']['identity']and value['guard_after']==before,'capture-identity-preparation-contract')
 initial=doc(value['intent']);need(value['intent']['path']==str(folder/'intent.json')and initial['job']==spec['job']and initial['guard']==before and initial['code_refs']==value['code_refs']and initial['environment_only']is True and initial['business_inputs']==0,'capture-identity-preparation-intent')
 samples=value['samples'];hovers=value['hovers'];need(1<=len(samples)<=3 and len(hovers)==len(samples)-1<=2 and value['environment_hover_attempts']==len(hovers),'capture-identity-preparation-budget')
 dependencies=[reference,value['intent'],*value['code_refs']];transports=[];url=None
 for index,sample in enumerate(samples):
  need(sample['intent']['path']==str(folder/f'{index:02d}-read-intent.json')and doc(sample['intent'])['command']=={'op':'readonly-scope','tabId':spec['job']['tab_id'],'windowId':spec['job']['window_id']},'capture-identity-read-intent')
  resultref=ref(folder/f'{index:02d}-read-result.json');need(doc(resultref)==sample,'capture-identity-read-result')
  facts=prep.checked_scope(spec['job'],sample['observed']['scope'],url);url=facts['url'];need(sample['checked']==facts and facts['ready']==(index==len(samples)-1),'capture-identity-scope-sequence')
  command={'op':'readonly-scope','tabId':spec['job']['tab_id'],'windowId':spec['job']['window_id']};record,ex,refs=verify_transport(sample['observed']['transport'],command,intent,folder,f'{index:02d}-scope');reply=doc(ex['stdout'])
  need(ex['returncode']==0 and reply.get('ok')is True and not reply.get('error')and reply.get('outcome')not in('unknown','not-delivered')and doc(sample['observed']['scope'])==reply['result'],'capture-identity-read-reply')
  need(sample['observed']['scope']['path']==str(folder/f'{index:02d}-scope.json'),'capture-identity-scope-path');dependencies.extend([sample['intent'],resultref,sample['observed']['scope'],*refs]);transports.append(sample['observed']['transport'])
  if index<len(hovers):
   hover=hovers[index];expected=facts['command'];need(hover['intent']['path']==str(folder/f'{index:02d}-hover-intent.json'),'capture-identity-hover-intent-path');hi=doc(hover['intent']);need(hi['kind']=='idempotent-provider-display-only-v1'and hi['command']==expected and hi['scope']==sample['observed']['scope']and hi['business_inputs']==0,'capture-identity-hover-command');hr=ref(folder/f'{index:02d}-hover-result.json');need(doc(hr)==hover,'capture-identity-hover-result')
   _,_,refs=verify_transport(hover['reply']['transport'],expected,intent,folder,f'{index:02d}-hover');dependencies.extend([hover['intent'],hr,*refs]);transports.append(hover['reply']['transport'])
 need(value['final_scope']==samples[-1]['observed']['scope'],'capture-identity-final-scope');last=doc(samples[-1]['observed']['transport'])
 return value,transports,last,dependencies

def historical_bridge_material(prior,live):
 # Exact already-published W53 bridge succession. This reads before/payload
 # bytes as evidence; never executes archived code or grants capture authority.
 release_ref={'path':str(ROOT/'work/2026-10-29/round009-issue53-bridge-generation-maintenance/source/full5/supervisor-release.json'),'sha256':'df82acf13729b15e956ad5b7dc9e9c8b591c5ba709cc61afb553fb4cbadba184'}
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director','capture-bridge-reviewed-release')
 rows=[r for r in release['targets']if r['target']==str(BRIDGE)];need(len(rows)==1,'capture-bridge-one-reviewed-slot');row=rows[0]
 need(prior['path']==live['path']==str(BRIDGE)and row['old_sha256']==row['before']['sha256']==prior['sha256']and row['after']['sha256']==live['sha256']and row['mode']==420,'capture-bridge-exact-generation')
 for r in(row['before'],row['after']):need(ref(r['path'])==r,'capture-bridge-source-material-drift')
 need(ref(BRIDGE)==live,'capture-bridge-live-generation');return [release_ref,row['before'],row['after'],live]

def capture_source_materials(original):
 """Only finite reviewed self/navigation or the exact W53 bridge successor
 may move; archives are data, and current producer guards remain separate.
 Every other source remains physical, and actual current sources/dependencies
 are returned for command-hit hashing. This grants no new capture authority.
 """
 current=sources();need(type(original)is list and len(original)==len(current)and [r.get('path')for r in original]==[r['path']for r in current],'capture-code-source-vector')
 allowed={str(Path(__file__).absolute()),str(QUALIFIER.with_name('bridge-workflow.py')),str(QUALIFIER.with_name('switch_read_recovery.py'))};dependencies=[]
 for prior,live in zip(original,current):
  if prior==live:dom.pinned(prior)if Path(prior['path']).suffix=='.json'else need(ref(prior['path'])==prior,'capture-code-source-drift');dependencies.append(live);continue
  if prior['path']==str(BRIDGE):
   dependencies.extend(historical_bridge_material(prior,live));continue
  need(prior['path']in allowed,'capture-code-generation')
  sys.path.insert(0,str(ROOT/'skills/workshop-director/scripts'))
  import execution_timing as timing
  path=ROOT/'skills/workshop-director/scripts/execution_timing.py';need(Path(timing.__file__).absolute()==path and timing._CONFIGURATION_MODULE_SOURCE==ref(path),'capture-source-resolver-origin')
  admitted=timing.configuration_source_material(prior);need(admitted['historical']==prior and admitted['current']==live,'capture-reviewed-source-transition')
  dependencies.extend([admitted['material'],admitted['current'],*admitted['dependencies'],ref(path)])
 return list({(r['path'],r['sha256']):r for r in dependencies}.values())

def verify_capture(capture_ref,payload,state=None,row=None):
 c=doc(capture_ref);need(c['kind']==KIND,'capture-kind');source_dependencies=capture_source_materials(c['sources']);intent=doc(c['intent']);spec=intent['spec'];need(intent['kind']==KIND and spec['kind']==KIND and intent['sources']==c['sources']and intent['before']==c['before']==c['after'],'capture-original-guard-drift');job=spec['job'];folder=capture_location(spec);need(capture_ref['path']==str(folder/'complete.json')and c['intent']['path']==str(folder/'intent.json')and c['pages'][0]['path']==str(folder/'page-0001.json')and c['producer_receipt']['path']==str(folder/'dom-source/receipt.json'),'capture-stable-original-location');before=c['before'];need(before['lease']==spec['lease']and before['workflow']==spec['workflow'],'capture-original-guard-refs');task=before['snapshot']['task'];need(before['original_exit']['path']==str(Path(task['active_attempt'])/'exit.json')and doc(before['original_exit']).get('request')==job['original_request'],'capture-original-natural-exit');request=doc(job['original_request']);archives=intent['guard_archives'];need(len(archives)==2 and {x['original']['path']for x in archives}=={spec['lease']['path'],spec['workflow']['path']},'capture-original-archives');mapped={}
 for pair in archives:
  need(pair['archive']['sha256']==pair['original']['sha256'],'capture-archive-bytes');mapped[pair['original']['path']]=doc(pair['archive'])
 lease=mapped[spec['lease']['path']];wf=mapped[spec['workflow']['path']];order=doc(job['original_order'])
 need(before['snapshot']['resource_owner']==task['id']==job['original_task']and task['flow']=='daily-comment-stats'and task['state']=='failed'and task['outer']==job['original_outer']==request['task']['outer']and task['context']['order']==job['original_order']and task['context']['scope']==request['context']['scope']=={'pid':job['pid'],'tab_id':job['tab_id']}and task['context']['browser_binding']['process']==request['context']['browser_binding']['process'],'capture-original-owner')
 need(lease['dispatch_id']==order['dispatch_id']and lease['day']==order['day']and lease['test_target']=='测试群请忽略'and lease['production_enabled']is False and lease['complaint_submission_enabled']is False,'capture-original-lease')
 need(intent['qualification']=={'source':ref(QUALIFIER),'workflow':spec['workflow'],'qualified':True},'capture-original-qualified-workflow');need(wf['company']==job['company']and str(wf['groupid'])==str(job['groupid'])and wf['tab_id']==job['tab_id']and wf['identity']==job['identity']and wf['phase']=='downloadResult','capture-original-workflow')
 preparation,transports,last,preparation_dependencies=verify_preparation(c['identity_preparation'],spec,c['intent'],before)
 need(c['transport_calls']==transports and all(c[k]==last[k]for k in('request','started','natural_exit')),'capture-final-transport-binding')
 need(doc(c['pages'][0])==doc(preparation['final_scope']),'capture-final-scope-page-binding')
 epoch=doc(c['environment_epoch']);need(epoch['intent']==c['intent']and epoch['before']==before and epoch['prior_pending']==c['prior_pending'],'capture-environment-epoch');pending_dependencies=[]
 for pending in c['prior_pending']:pending_dependencies.extend(checked_environment_pending(pending,spec,c['intent'],before))
 started=doc(c['started']);ex=doc(c['natural_exit']);ticks=[epoch['started'],started['started'],ex['ended'],c['completed']]
 need(datetime.fromisoformat(intent['started']['wall_at'])<=datetime.fromisoformat(epoch['started']['wall_at']),'capture-original-wall-order')
 need([t['monotonic_ns']for t in ticks]==sorted(t['monotonic_ns']for t in ticks)and [datetime.fromisoformat(t['wall_at'])for t in ticks]==sorted(datetime.fromisoformat(t['wall_at'])for t in ticks),'capture-real-time-order')
 data=dom.verify(c['producer_receipt']);need(payload==dom._source_evidence_from_verified(c['producer_receipt'],data)and payload['receipt']==c['producer_receipt'],'capture-producer-wrapper');need(data['job']==job and data['pages']==c['pages'],'capture-fresh-producer-pages')
 if state is not None:
  need(state['dispatch_scope']['work_order']==job['original_order']and Path(state['run_dir'])==Path(doc(job['original_job'])['workflow_path']).parents[3],'capture-batch-dispatch')
 if row is not None:
  need(row['company']==job['company']and str(row['groupid'])==str(job['groupid'])and {k:row['date_range'][k]for k in('start','end')}==job['date_range'],'capture-row-binding')
 producer_receipt=doc(c['producer_receipt']);dependencies=[c['environment_epoch'],*pending_dependencies,*preparation_dependencies,capture_ref,c['intent'],job['original_job'],job['original_order'],job['original_request'],before['original_exit'],c['request'],c['started'],c['natural_exit'],ex['stdout'],ex['stderr'],c['producer_receipt'],producer_receipt['manifest'],producer_receipt['xlsx'],dom.RATING_EVIDENCE,*source_dependencies,*producer_receipt['reader_code_refs'],*c['pages'],*[pair['archive']for pair in archives]];dependencies=list({(r['path'],r['sha256']):r for r in dependencies}.values())
 return {'kind':KIND,'capture':capture_ref,'job':job,'workflow':spec['workflow'],'pages':c['pages'],'producer_receipt':c['producer_receipt'],'snapshot_freshness':'fresh-program-readonly-scope-with-natural-child-exit','no_business_input':True,'verification_refs':dependencies,'producer_data':data}
def main():
 p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--out',required=True);a=p.parse_args();print(json.dumps(capture(doc(json.loads(a.spec)),a.out)))
if __name__=='__main__':main()
