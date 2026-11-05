"""Config-driven context-only producer and bounded supervisor CLI.
No grant builder, acquisition, business resume or cursor/lease writes.
Runner ports are injected in tests; CLI uses the exact authorized lease executor.
"""
import copy,fcntl,hashlib,json,os,tempfile,sys
from pathlib import Path
from datetime import datetime,timezone
_CONFIG_SOURCE=Path(__file__).absolute().parents[3]/'skills/workshop-director/scripts/company_configuration.py'
if not _CONFIG_SOURCE.is_file()or _CONFIG_SOURCE!=_CONFIG_SOURCE.resolve()or any(p.is_symlink()for p in(_CONFIG_SOURCE,*_CONFIG_SOURCE.parents)):raise ValueError('configured-discovery-configuration-source-origin')
sys.path.insert(0,str(Path(__file__).absolute().parent))
sys.path.insert(0,str(_CONFIG_SOURCE.parent))
import company_configuration as c
import dom_evidence as dom
from readonly_tick_snapshot import decode
MODAL='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__'
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()}
def immutable(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);b=encode(value)
 if path.exists():c.need(not path.is_symlink()and path.read_bytes()==b,'configured-discovery-immutable-conflict');return ref(path)
 with path.open('xb')as f:f.write(b);f.flush();os.fsync(f.fileno())
 return ref(path)
def atomic(path,value):
 path=Path(path);fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.configured-company-')
 try:
  with os.fdopen(fd,'wb')as f:f.write(encode(value));f.flush();os.fsync(f.fileno())
  os.replace(tmp,path);fd=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def prepare(path,operation_ref):
 """Writes an independent operation state, never authorizes or extends order."""
 p=Path(path);c.need(p.is_absolute()and p==p.resolve()and not any(x.is_symlink()for x in(p,*p.parents))and not p.exists(),'configured-discovery-new-canonical-state');op=c.doc(operation_ref);config=c.Config(op['config']);c.operation(config,operation_ref);p.parent.mkdir(parents=True,exist_ok=True);value={'kind':'configured-company-discovery-state-v2','operation':operation_ref,'calls':[],'observations':[],'state':'running','proof':None};immutable(p,value);return value
def checked_prefix(state,op,row):
 order={'source-identity-hover':-2,'open-picker':-1,'search':0,'selection':1,'confirmation':2,'identity-hover':3};seen=[];observations=[x['raw_reply']for x in state['observations']]
 for call in state['calls']:
  stage=call['stage'];c.need(stage in order and stage not in seen and (not seen or order[seen[-1]]<order[stage])and call['key']==op['key']+':'+stage and call['state']in('unknown','confirmed'),'configured-discovery-prefix-stage');seen.append(stage);intent=c.doc(call['intent']);c.need(intent=={k:call[k]for k in('key','stage','command','before')}and call['before']in observations,'configured-discovery-prefix-conflict');raw=c.doc(call['before']);c.need(raw.get('ok')is True,'configured-discovery-prefix-before');command=call['command']
  if stage in('source-identity-hover','open-picker'):target=c.source_bootstrap_input(raw['result'],op,stage);expected={'op':'hover'if stage=='source-identity-hover'else'click','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
  elif stage=='identity-hover':target,gid=c.identity_hover_before(raw['result'],op,row);expected={'op':'hover','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
  else:
   if stage=='search':_,(_,_,target)=c.picker_source(raw['result'],op);expected={'op':'filter','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'value':row['company'],'companyRequest':state['operation']}
   else:
    kind='company'if stage=='selection'else'company-confirm';target=c.input_before(raw['result'],op,row,kind);expected={'op':'click','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':kind,'companyRequest':state['operation']}
  c.need(command==expected,'configured-discovery-prefix-command')
  if call['state']=='confirmed':
   reply=c.doc(call['reply']);result=reply.get('result',{});node=result.get('filtered'if stage=='search'else'hovered'if stage in('identity-hover','source-identity-hover')else'clicked',{});c.need(reply.get('ok')is True and node.get('selector')==target['selector'],'configured-discovery-prefix-effect')
   if stage=='search':c.need(node.get('attributes',{}).get('value')==row['company'],'configured-discovery-prefix-search-effect')
   else:
    c.need(node.get('name')==target['name'],'configured-discovery-prefix-effect-name');receipt=c.doc(call['receipt']);c.need(all(receipt.get(k)==v for k,v in {'operation':state['operation'],'key':call['key'],'command':command,'before':call['before'],'reply':call['reply'],'state':'confirmed'}.items()),'configured-discovery-prefix-receipt')
 c.need('source-identity-hover'not in seen or 'open-picker'in seen or seen==['source-identity-hover'],'configured-discovery-bootstrap-prefix');return seen
class Runner:
 def __init__(self,path,transport,guard,*,clock=None):
  c.need(callable(transport)and callable(guard),'configured-discovery-ports-required');self.path=Path(path);self.transport=transport;self.guard=guard;self.clock=clock or(lambda:datetime.now(timezone.utc))
 def save(self,state):atomic(self.path,state)
 def step(self):
  with (self.path.parent/'.lock').open('a')as held:
   fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads(self.path.read_bytes());c.need(state.get('kind')=='configured-company-discovery-state-v2','configured-discovery-state-kind');op=c.doc(state['operation']);config=c.Config(op['config']);complete=state.get('state')=='complete';op,row=c.operation(config,state['operation'],now=datetime.fromisoformat(op['issued_at'])if complete else self.clock())
   checked_prefix(state,op,row)
   if complete:
    proof=c.doc(state['proof']);c.need(proof['operation']==state['operation'],'configured-discovery-complete-operation');c.need(proof['selection']==next(x['receipt']for x in state['calls']if x['stage']=='selection')and proof['confirmation']==(next(x['receipt']for x in state['calls']if x['stage']=='confirmation')if 'source_entry'not in op else None),'configured-discovery-complete-prefix');c.need(all(x['state']=='confirmed'for x in state['calls'])and len(state['calls'])==len({x['stage']for x in state['calls']})and all(x['key']==op['key']+':'+x['stage']for x in state['calls']),'configured-discovery-complete-confirmed-prefix');c.need(proof.get('identity_hover')==(next((x['receipt']for x in state['calls']if x['stage']=='identity-hover'),None)),'configured-discovery-complete-hover-prefix');c.need(proof.get('source_bootstrap')==({'identity_hover':next((x['receipt']for x in state['calls']if x['stage']=='source-identity-hover'),None),'open_picker':next(x['receipt']for x in state['calls']if x['stage']=='open-picker')}if any(x['stage']=='open-picker'for x in state['calls'])else None),'configured-discovery-complete-bootstrap-prefix');c.need(proof['observations']==state['observations'][-2:],'configured-discovery-complete-observation-prefix');facts=c.verify_context_proof(state['proof']);c.need(state.get('stable',{}).get('facts')=={k:facts[k]for k in('company','groupid','identity')},'configured-discovery-complete-stable-facts');return state
   self.guard(op)
   c.need(not state.get('source_bootstrap_exhausted'),'configured-discovery-source-bootstrap-exhausted')
   c.need(len(state.get('identity_hover_reads',[]))<2,'configured-discovery-post-hover-read-budget')
   c.need(not any(x['state']=='unknown'for x in state['calls']),'configured-discovery-unknown-no-replay');c.need(len(state['observations'])<(12 if 'source_bootstrap'in op else 8),'configured-discovery-read-budget-exhausted');command={'op':'readonly-scope','tabId':op['tab_id'],'windowId':op['window_id']};self.guard(op);reply=self.transport(command);observation={'command':command,'raw_reply':immutable(self.path.parent/('read-%04d.json'%len(state['observations'])),reply),'observed_at':self.clock().isoformat()};state['observations'].append(observation);self.save(state);c.need(reply.get('ok')is True,'configured-discovery-read-error');value=decode(reply['result'],op['tab_id'],op['window_id']);login=value['tree'].get('url')=='https://life.douyin.com/p/login';before=c.entry_context(value['before'],op['tab_id'],op['window_id'],login=login);after=c.entry_context(value['after'],op['tab_id'],op['window_id'],login=login);c.need(before==after and before['windowId']==op['window_id']and value['tree'].get('truncated')is False,'configured-discovery-fresh-scope');tree=value['tree'];c.require_no_visible_system_error(tree);nodes=list(dom.nodes(tree));labels=c.company_labels(tree);stages={x['stage']:x for x in state['calls']}
   if len(labels)==1 and labels[0].get('name')==row['company']:
    c.need(all(x['state']=='confirmed'for x in state['calls'])and 'selection'in stages and ('source_entry'in op or 'confirmation'in stages),'configured-discovery-before-identity-prefix')
    if 'identity-hover'in stages:state.setdefault('identity_hover_reads',[]).append(observation);self.save(state)
    try:actual=dom.identity(tree)
    except ValueError as error:
     if 'identity-hover'in stages:
      c.identity_hover_before(value,op,row);c.need(len(state['identity_hover_reads'])<2,'configured-discovery-identity-hover-exhausted');return state
     target,gid=c.identity_hover_before(value,op,row);return self.issue(state,op,'identity-hover',{'op':'hover','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},observation)
    c.need(actual['provider']==row['provider']and all(x['state']=='confirmed'for x in state['calls'])and 'selection'in stages and ('source_entry'in op or 'confirmation'in stages),'configured-discovery-original-input-prefix');prior=state.get('stable')
    facts={'company':row['company'],'groupid':before['groupid'],'identity':actual}
    if prior is None:state['stable']={'facts':facts,'observation':observation};self.save(state);return state
    c.need(prior['facts']==facts,'configured-discovery-target-identity-changed');proof={'kind':'configured-login-company-context-proof-v2'if 'source_entry'in op else'configured-company-context-proof-v2','operation':state['operation'],'selection':stages['selection']['receipt'],'confirmation':None if 'source_entry'in op else stages['confirmation']['receipt'],'observations':[prior['observation'],observation]};
    if 'identity-hover'in stages:proof['identity_hover']=stages['identity-hover']['receipt']
    if 'open-picker'in stages:proof['source_bootstrap']={'identity_hover':stages['source-identity-hover']['receipt']if 'source-identity-hover'in stages else None,'open_picker':stages['open-picker']['receipt']}
    pr=immutable(self.path.parent/'context-proof.json',proof);c.verify_context_proof(pr);state.update(state='complete',proof=pr);self.save(state);return state
   if 'source_bootstrap'in op:
    # Only absence of the reviewed modal may wait. A malformed/foreign dialog
    # falls through to strict picker validation and cannot authorize an input.
    dialogs=[n for n in nodes if n.get('role')=='dialog']
    if not dialogs:return self.bootstrap(state,op,value,observation,stages)
   value,(root,children,field)=c.picker_source(value,op)
   if 'source_entry'in op and 'selection'in stages:return state # bounded read-only post-selection, no invented confirmation.
   if field.get('attributes',{}).get('value')!=row['company']:
    c.need('search'not in stages,'configured-discovery-search-effect-lost');return self.issue(state,op,'search',{'op':'filter','tabId':op['tab_id'],'locator':{'by':'selector','value':field['selector']},'value':row['company'],'companyRequest':state['operation']},observation)
   items=[n for n in children if not n.get('children')and n.get('name')==row['company']];c.need(len(items)<=1,'configured-discovery-target-duplicate')
   if not items:return state # bounded reads; never submit search again.
   stage='confirmation'if 'selection'in stages else'selection';kind='company-confirm'if stage=='confirmation'else'company'
   if kind=='company-confirm'and not c.picker_confirm_nodes(children):return state # footer renders after the row; bounded reads
   target=c.input_before(value,op,row,kind);return self.issue(state,op,stage,{'op':'click','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':kind,'companyRequest':state['operation']},observation)
 def bootstrap(self,state,op,value,observation,stages):
  c.source_bootstrap_scope(value,op)
  c.need(not any(x in stages for x in('search','selection','confirmation','identity-hover')),'configured-discovery-picker-lost-after-input')
  if 'open-picker'in stages:
   dom.identity(value['tree'],op['source_identity']);reads=state.setdefault('picker_open_reads',[]);reads.append(observation);state['source_bootstrap_exhausted']=len(reads)>=2;self.save(state);c.need(not state['source_bootstrap_exhausted'],'configured-discovery-picker-open-exhausted');return state
  if 'source-identity-hover'in stages:
   reads=state.setdefault('source_identity_reads',[]);reads.append(observation);self.save(state)
  try:dom.identity(value['tree'],op['source_identity'])
  except ValueError:
   target=c.source_bootstrap_input(value,op,'source-identity-hover')
   if 'source-identity-hover'in stages:
    if len(state['source_identity_reads'])>=2:state['source_bootstrap_exhausted']=True;self.save(state);raise ValueError('configured-discovery-source-identity-exhausted')
    return state
   return self.issue(state,op,'source-identity-hover',{'op':'hover','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},observation)
  target=c.source_bootstrap_input(value,op,'open-picker');return self.issue(state,op,'open-picker',{'op':'click','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},observation)
 def issue(self,state,op,stage,command,observation):
  prior=c.doc(observation['raw_reply']);c.need(prior.get('ok')is True,'configured-discovery-input-before');c.require_no_visible_system_error(prior['result']['tree'])
  c.need(not any(x['stage']==stage for x in state['calls']),'configured-discovery-stage-once');self.guard(op);key=op['key']+':'+stage;call={'key':key,'stage':stage,'command':command,'before':observation['raw_reply'],'state':'unknown'};call['intent']=immutable(self.path.parent/('intent-'+stage+'.json'),{k:call[k]for k in('key','stage','command','before')});state['calls'].append(call);self.save(state)
  try:
   reply=self.transport(command);reply_ref=immutable(self.path.parent/('reply-'+stage+'.json'),reply);c.need(reply.get('ok')is True,'configured-discovery-input-unknown');result=reply['result'];node=result.get('filtered'if stage=='search'else'hovered'if stage in('identity-hover','source-identity-hover')else'clicked',{});c.need(node.get('selector')==command['locator']['value'],'configured-discovery-input-selector');
   if stage=='search':c.need(node.get('attributes',{}).get('value')==command['value'],'configured-discovery-search-effect')
   else:
    if stage not in('identity-hover','source-identity-hover'):c.need(result.get('kind')==command['kind'],'configured-discovery-input-kind')
    expected=c.doc(op['config']);row=next(r for r in expected['entries']if r['id']==op['entry_id']);name=c.source_bootstrap_input(c.doc(observation['raw_reply'])['result'],op,stage)['name']if stage in('source-identity-hover','open-picker')else(row['provider']if stage=='identity-hover'else'确认'if stage=='confirmation'else row['company']);c.need(node.get('name')==name,'configured-discovery-input-name')
    receipt={'kind':'configured-company-input-v2','operation':state['operation'],'key':key,'before':call['before'],'command':command,'reply':reply_ref,'state':'confirmed','at':self.clock().isoformat()};call['receipt']=immutable(self.path.parent/('input-'+stage+'.json'),receipt)
   call.update(state='confirmed',reply=reply_ref);self.save(state);return state
  except BaseException as error:call['error']=str(error);self.save(state);raise

# Public context-discovery executor. Authority is an explicit supervisor input,
# never produced here. A trusted Root fixed launcher must pin its literal ref.
# This executor never creates a task, changes a lease, or turns context into
# acquisition/business authority. Business company switches use Workflow.
def inspect_complete(path):
 state=json.loads(c.regular(path).read_bytes());c.need(state.get('state')=='complete','configured-discovery-not-complete');before=ref(path);out=Runner(path,lambda cmd:(_ for _ in ()).throw(ValueError('inspect-no-transport')),lambda op:(_ for _ in ()).throw(ValueError('inspect-no-lease'))).step();c.need(ref(path)==before,'configured-discovery-inspect-changed');return {'state':'complete','operation':out['operation'],'proof':out['proof'],'transport_calls':0,'business_resume':False}

class LeaseSystem:
 """Read-only OS metadata, no argv/environment/pixels. Tests replace this port."""
 def __init__(self,root):
  import sys
  sys.path.insert(0,str(root/'packages/workshop-director'))
  from workshop_director import common
  self.common=common
 def same_process(self,p):return self.common.same_process(p)
 def process_rows(self):
  import subprocess
  raw=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,stat=,comm='],text=True,timeout=5)
  rows=[]
  for line in raw.splitlines():
   fields=line.split(None,3)
   if len(fields)==4:rows.append({'pid':int(fields[0]),'ppid':int(fields[1]),'stat':fields[2],'executable':fields[3]})
  return rows

def queue_snapshot(root):
 import sqlite3
 path=c.regular(root/'runtime/standalone-workshop-director/queue.sqlite3');db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
 try:
  db.row_factory=sqlite3.Row
  return {name:[dict(row)for row in db.execute('SELECT * FROM '+name+' ORDER BY '+key)]for name,key in(('tasks','id'),('plans','id'),('meta','key'),('events','seq'))}
 finally:db.close()
def executor_sources(root):
 return {'discovery':root/'skills/douyin-laike-operator/scripts/configured_company_discovery.py','configuration':root/'skills/workshop-director/scripts/company_configuration.py','bridge':root/'skills/chrome-dom-export/scripts/bridge.py','content':root/'skills/chrome-dom-export/extension/content.js','policy':root/'skills/chrome-dom-export/extension/policy.js','system':root/'packages/workshop-director/workshop_director/common.py'}
def executor_authority(reference,*,clock=None):
 now=(clock or(lambda:datetime.now(timezone.utc)))();a=c.doc(reference);fields={'kind','operation','state_path','project','queue_sha256','coordinator','worker_exits','processes','source_refs','issued_at','expires_at','max_steps','max_readonly_scopes','max_identity_hover','expected_owner'};c.need(type(a)is dict and set(a)==fields and a['kind']in('configured-company-discovery-executor-authorization-v2','configured-company-discovery-bootstrap-executor-authorization-v3'),'configured-discovery-explicit-authority');root=Path(__file__).absolute().parents[3];c.need(a['project']==str(root)and root==root.resolve()and a['expected_owner']is None,'configured-discovery-unowned-project-only');start=datetime.fromisoformat(a['issued_at']);end=datetime.fromisoformat(a['expires_at']);c.need(start.utcoffset()is not None and end.utcoffset()is not None and start<=now<=end and 0<(end-start).total_seconds()<=300,'configured-discovery-executor-expired');op=c.doc(a['operation']);config=c.approved_config(root/'skills/workshop-director/config/approved-company-scope.json');checked,row=c.operation(config,a['operation'],now=now);c.need(checked['purpose']=='context-discovery'and start>=datetime.fromisoformat(op['issued_at'])and end<=datetime.fromisoformat(op['expires_at']),'configured-discovery-executor-operation-window');bootstrap='source_bootstrap'in op;c.need((a['kind']=='configured-company-discovery-bootstrap-executor-authorization-v3')==bootstrap,'configured-discovery-bootstrap-authority-kind');limit=12 if bootstrap else 8;c.need(type(a['max_steps'])is int and 1<=a['max_steps']<=limit and type(a['max_readonly_scopes'])is int and a['max_readonly_scopes']==limit and type(a['max_identity_hover'])is int and a['max_identity_hover']==(2 if bootstrap else 1),'configured-discovery-executor-budgets');c.need(a['state_path']==str(root/'work/company-discovery'/op['key']/'state.json'),'configured-discovery-fixed-operation-path');expected=executor_sources(root);c.need(Path(c.__file__).absolute()==expected['configuration'],'configured-discovery-loaded-configuration-origin');c.need(set(a['source_refs'])==set(expected),'configured-discovery-source-set')
 for key,path in expected.items():c.need(a['source_refs'][key]['path']==str(path),'configured-discovery-source-path');c.raw(a['source_refs'][key])
 c.need(a['coordinator']['path']==str(root/'runtime/workshop-director/state.json'),'configured-discovery-coordinator-path');return a,op,root

def executor_guard(a,op,root,system):
 raw=queue_snapshot(root);c.need(hashlib.sha256(encode(raw)).hexdigest()==a['queue_sha256'],'configured-discovery-queue-drift');meta={r['key']:json.loads(r['value'])for r in raw['meta']};c.need(meta.get('resource_owner','missing')is None and not any(t['state']in('running','dispatching','unknown','waiting')for t in raw['tasks']),'configured-discovery-resource-busy');coordinator=c.doc(a['coordinator']);c.need(coordinator.get('phase')=='ready','configured-discovery-coordinator-not-ready');exits=a['worker_exits'];attempts={t['active_attempt']for t in raw['tasks']if t.get('active_attempt')};c.need(type(exits)is list and len(exits)==len(attempts)and {x['attempt']for x in exits}==attempts,'configured-discovery-all-natural-exits')
 for x in exits:
  c.need(set(x)=={'attempt','started','exit'},'configured-discovery-worker-exit-schema');folder=Path(x['attempt']);c.need(folder.parent==root/'runtime/standalone-workshop-director/attempts'and x['started']['path']==str(folder/'started.json')and x['exit']['path']==str(folder/'exit.json'),'configured-discovery-worker-canonical');started=c.doc(x['started']);ended=c.doc(x['exit']);c.need(ended.get('kind')=='workshop-worker-exit-v1'and ended.get('attempt_id')==folder.name and type(ended.get('returncode'))is int and not system.same_process(started['process']),'configured-discovery-worker-live-or-no-exit')
 processes=a['processes'];c.need(type(processes)is dict and set(processes)=={'host','daemon'},'configured-discovery-existing-processes');rows=system.process_rows();by={r['pid']:r for r in rows};c.need(len(by)==len(rows),'configured-discovery-process-row-duplicate');ids={}
 for name,item in processes.items():
  c.need(type(item)is dict and set(item)=={'process','executable'}and type(item['executable'])is str and item['executable'].startswith('/'),'configured-discovery-process-schema');process=item['process'];pid=process['pid'];c.need(pid in by and not by[pid]['stat'].startswith('Z')and by[pid]['executable']==item['executable']and system.same_process(process),'configured-discovery-process-identity');ids[name]=pid
 c.need(ids['host']!=ids['daemon']and by[ids['daemon']]['ppid']==ids['host'],'configured-discovery-daemon-parent');children=set();front={ids['host']}
 while front:
  found={r['pid']for r in rows if r['ppid']in front and r['pid']not in children and r['pid']!=ids['host']};children|=found;front=found
 c.need(children=={ids['daemon']},'configured-discovery-unexpected-descendant')
 for r in a['source_refs'].values():c.raw(r)
 return raw

def execute(reference,*,transport=None,system=None,clock=None):
 """Only invoked by explicit local supervisor authorization; import is inert.
 Tests inject TEMP system/transport. CLI has no injected ports or grant builder.
 """
 import contextlib,importlib.util
 a,op,root=executor_authority(reference,clock=clock);system=system or LeaseSystem(root);path=Path(a['state_path']);start=__import__('time').monotonic()
 with contextlib.ExitStack()as stack:
  # Existing common order. Locks must already be real canonical regular files;
  # this actor does not manufacture a runtime or initialize a queue.
  for lockpath in (root/'runtime/workshop-director/browser-wecom.resource.lock',root/'runtime/standalone-workshop-director/scheduler.lock',root/'runtime/workshop-director/.lock'):
   f=stack.enter_context(c.regular(lockpath).open('r'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def guard(checked):
   fresh,again,where=executor_authority(reference,clock=clock);c.need(fresh==a and again==op and where==root and checked==op and __import__('time').monotonic()-start<=300,'configured-discovery-executor-binding-drift');executor_guard(a,op,root,system)
  guard(op);path.parent.mkdir(parents=True,exist_ok=True);binding={'kind':'configured-company-discovery-executor-binding-v2','authorization':reference,'operation':a['operation'],'source_refs':a['source_refs']};immutable(path.parent/'executor-binding.json',binding)
  if not path.exists():prepare(path,a['operation'])
  state=json.loads(c.regular(path).read_bytes());c.need(state['operation']==a['operation'],'configured-discovery-executor-original-operation');guard(op)
  if transport is None:
   b=Path(a['source_refs']['bridge']['path']);spec=importlib.util.spec_from_file_location('configured_discovery_pinned_bridge',b);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);guard(op);transport=lambda command:module.request(command,timeout=15)
  runner=Runner(path,transport,guard,clock=clock)
  for _ in range(a['max_steps']):
   state=runner.step()
   if state['state']=='complete':break
  guard(op);return {'state':state['state'],'operation':a['operation'],'journal':ref(path),'proof':state.get('proof'),'business_resume':False,'acquisition_receipt':False}

def main(argv=None):
 import argparse
 parser=argparse.ArgumentParser(description='Bounded context-only discovery; requires separately supplied supervisor authority. No grant builder or business resume.');sub=parser.add_subparsers(dest='verb',required=True);inspect=sub.add_parser('inspect');inspect.add_argument('--state',required=True);inspect.add_argument('--state-sha256',required=True);run=sub.add_parser('run');run.add_argument('--authorization',required=True);run.add_argument('--authorization-sha256',required=True);args=parser.parse_args(argv)
 try:
  if args.verb=='inspect':c.raw({'path':args.state,'sha256':args.state_sha256});value=inspect_complete(args.state)
  else:value=execute({'path':args.authorization,'sha256':args.authorization_sha256})
  print(json.dumps(value,ensure_ascii=False));return 0 if value['state']=='complete'else 2
 except Exception as error:print(json.dumps({'state':'hold','error':str(error),'retry_input_allowed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
