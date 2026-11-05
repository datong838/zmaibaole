"""Staged collection source proof. Data archives only; never input/client/cursor.
Fresh staged roles only. Legacy completion verifiers remain separate.
"""
import contextlib,hashlib,importlib.util,json,math,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
CONTRACT='three-flow-collection-ready-v1'
ROLES={'negative-review-complaints':('complaint_execution_order','complaint_execution_launcher','complaint_execution','complaint_execution_ports','complaint-director-collection-ready-report-v1'),'violation-notifier':('role_execution_order','role_execution_launcher','violation_execution','violation_execution_ports','violation-director-collection-ready-report-v1')}
def need(ok,code):
 if not ok:raise ValueError(code)
def regular(path):
 p=Path(path);need(p.is_absolute()and p.resolve()==p and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'ready-canonical-source-required');return p
def ref(path):
 p=regular(path);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(r):
 need(type(r)is dict and set(r)=={'path','sha256'},'ready-reference-shape');p=regular(r['path']);data=p.read_bytes();need(hashlib.sha256(data).hexdigest()==r['sha256'],'ready-reference-drift');return data
def doc(r):return json.loads(raw(r))
def immutable(path,data):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);need(not any(p.is_symlink()for p in(path,*path.parents)),'ready-archive-symlink')
 try:
  with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 except FileExistsError:need(path.read_bytes()==data,'ready-archive-conflict')
 return ref(path)
def snapshot(folder,r):return immutable(Path(folder)/'before'/(r['sha256']+Path(r['path']).suffix),raw(r))
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
@contextlib.contextmanager
def role_modules(flow):
 need(flow in ROLES,'ready-fixed-flow')
 order,launch,engine,ports,_=ROLES[flow]
 specs=[(order,ROOT/'skills/workshop-director/scripts'/(order+'.py')),('workflow',ROOT/'skills'/flow/'scripts/workflow.py'),(engine,ROOT/'skills'/flow/'scripts'/(engine+'.py')),(ports,ROOT/'skills'/flow/'scripts'/(ports+'.py'))]
 saved={n:sys.modules.get(n)for n,_ in specs};old_path=sys.path[:];modules={}
 try:
  sys.path[:0]=[str(ROOT/'skills'/s/'scripts')for s in(flow,'workshop-director','daily-comment-stats','douyin-laike-operator','chrome-dom-export','wecom-messenger')]
  for name,path in specs:
   spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);modules[name]=module
  yield modules
 finally:
  sys.path[:]=old_path
  for name,previous in saved.items():
   if previous is None:sys.modules.pop(name,None)
   else:sys.modules[name]=previous

def current_child(parent,folder):
 need(parent.get('status')=='collection-ready'and parent.get('calls'),'ready-original-parent-stage')
 call=parent['calls'][-1];need(call.get('state')=='returned','ready-current-child-unresolved')
 exit=doc(call['result']);need(exit.get('returncode')==0 and exit.get('launch')==call.get('launch'),'ready-current-child-exit')
 output=json.loads(exit['stdout']);need(output==parent.get('child'),'ready-parent-child-drift')
 need(output.get('status')=='collection-ready'and output.get('delivery_complete')is False and output.get('order')==parent['order'],'ready-current-child-stage')
 need(output['engine']['path']==str(folder/'engine.json')and output['collection_ready']['path']==str(folder/'collection-ready.json'),'ready-current-child-path')
 return output

def _value(parent,engine,director,flow,modules,ledgers):
 order_name,_,_,ports_name,_=ROLES[flow];o=modules[order_name];folder=o.location(parent['order']);order=o.validate(parent['order'])
 need(order.get('collection_contract')==CONTRACT and order['workflow']==flow and parent['kind']=='role-execution-launcher-v1'and parent['scope_sha256']==order['scope_sha256'],'ready-original-staged-order')
 output=current_child(parent,folder)
 need(engine.get('order')==parent['order']and engine.get('scope_sha256')==order['scope_sha256']and engine.get('status')=='collection-ready'and engine.get('collection_ready')==output['collection_ready']and not engine.get('handoff'),'ready-engine-stage')
 call=engine['calls'][-1]
 need(call.get('state')=='returned'and call.get('applied')and call.get('step')=='collection-seal'and doc(call['result']).get('ready')==engine['collection_ready'],'ready-current-applied-seal-required')
 need(director.get('phase')=='running'and director.get('dispatch_id')==order['dispatch_id']and director.get('day')==order['day']and director.get('collection_contract')==CONTRACT,'ready-original-director-lease')
 ready=doc(output['collection_ready'])
 port=modules[ports_name].ProductionPorts(parent['tab_id'],parent['pid'],request=lambda *a,**k:(_ for _ in()).throw(ValueError('ready-no-RPC')))
 facts=port.verify_collection_materials(order,engine,ready,ledgers)
 return {'order':parent['order'],'scope_sha256':order['scope_sha256'],'day':order['day'],'dispatch_id':order['dispatch_id'],'workflow':flow,'companies':facts['companies'],'delivery_plan':ready['delivery_plan'],'collection_ready':True,'complete':False,'delivery_complete':False,'cursor_advanced':False}

def report(parent_ref,director_ref,out,flow):
 parent=doc(parent_ref);need(flow in ROLES,'ready-fixed-flow');out=Path(out).resolve()
 with role_modules(flow)as modules:
  o=modules[ROLES[flow][0]];folder=o.location(parent['order']);need(parent_ref['path']==str(folder/'launcher.json')and director_ref['path']==str(folder.parent.parent/'state.json'),'ready-original-canonical-path')
  output=current_child(parent,folder);engine_ref=output['engine'];engine=doc(engine_ref);ledgers=[];order=o.validate(parent['order'])
  for company in order['companies']:
   r=ref(Path(company['root'])/'state.json');ledgers.append({'company':company['company'],'original':r,'archive':snapshot(out.parent,r)})
  for company,cs in zip(order['companies'],engine['companies']):
   if not company['skipped']:need(next(x['original']for x in ledgers if x['company']==company['company'])==cs['artifacts']['ledger_current'],'ready-ledger-not-engine-checkpoint')
  value=_value(parent,engine,doc(director_ref),flow,modules,{x['company']:doc(x['archive'])for x in ledgers})
  sealed={'kind':ROLES[flow][4],**value,'reader':'current-results-v1','collection_contract':CONTRACT,'original_parent':parent_ref,'parent_archive':snapshot(out.parent,parent_ref),'original_engine':engine_ref,'engine_archive':snapshot(out.parent,engine_ref),'original_director':director_ref,'director_archive':snapshot(out.parent,director_ref),'ledgers':ledgers}
  for r in(parent_ref,engine_ref,director_ref,*[x['original']for x in ledgers]):raw(r)
  return immutable(out,encode(sealed))

def facts(report_ref):
 value=doc(report_ref);flow=value['workflow'];need(flow in ROLES and value['kind']==ROLES[flow][4]and value.get('reader')=='current-results-v1','ready-report-kind');base=Path(report_ref['path']).parent
 for original,archive in[(value['original_parent'],value['parent_archive']),(value['original_engine'],value['engine_archive']),(value['original_director'],value['director_archive']),*[(x['original'],x['archive'])for x in value['ledgers']]]:
  need(original['sha256']==archive['sha256']and archive['path']==str(base/'before'/(original['sha256']+Path(original['path']).suffix)),'ready-current-snapshot-binding');raw(archive)
 parent=doc(value['parent_archive']);engine=doc(value['engine_archive'])
 with role_modules(flow)as modules:
  order=modules[ROLES[flow][0]].validate(parent['order']);folder=modules[ROLES[flow][0]].location(parent['order']);output=current_child(parent,folder)
  need(output['engine']==value['original_engine']and value['original_parent']['path']==str(folder/'launcher.json'),'ready-current-parent-binding')
  for company,cs in zip(order['companies'],engine['companies']):
   if not company['skipped']:need(next(x['original']for x in value['ledgers']if x['company']==company['company'])==cs['artifacts']['ledger_current'],'ready-ledger-not-engine-checkpoint')
  expected=_value(parent,engine,doc(value['director_archive']),flow,modules,{x['company']:doc(x['archive'])for x in value['ledgers']})
  need(all(value.get(k)==v for k,v in expected.items()),'ready-report-facts-changed');return {**value,'order_document':order}

def verify_current(report_ref,current_director):
 value=facts(report_ref);need(doc(value['director_archive'])==current_director,'ready-current-director-drift')
 for r in[value['original_parent'],value['original_engine'],*[x['original']for x in value['ledgers']]]:raw(r)
 return value
