"""One-shot local semantic producer bridge; original parent accepts next attempt.
No AI inference, image approval, browser, messenger or business API here.
"""
import argparse,copy,json,subprocess,sys
from pathlib import Path
from . import adapters
from .common import need,read,ref,pinned,immutable,now,identity,digest,lock

ALLOWED={
 'negative-review-complaints':('complaint-execution-handoff-v1','complaint-analysis-batch-response-v1','analyze'),
 'violation-notifier':('violation-execution-handoff-v1','violation-copy-response-v1','copy'),
}
def reference(value):
 need(type(value) is dict and set(value)=={'path','sha256'},'local-worker-reference-required')
 path=Path(value['path'])
 need(path.is_absolute() and path.is_file() and not path.is_symlink() and ref(path)==value,'local-worker-reference-changed');return value

def parent_binding(request,result):
 outer_ref=reference(result['handoff']);outer=pinned(outer_ref)
 need(outer.get('kind')=='workshop-handoff-v1' and outer.get('task_id')==request['task']['id'] and outer.get('reason')=='parent-ai-or-png-review-required' and outer.get('response_kind')=='workshop-handoff-response-v1','local-worker-outer-binding')
 parent_ref=reference(outer['details']['parent_handoff']);parent=pinned(parent_ref)
 flow=request['task']['flow'];allowed=ALLOWED.get(flow)
 if not allowed or parent.get('response_kind')!=allowed[1]:return None
 need(parent.get('kind')==allowed[0] and parent.get('phase')==allowed[2],'local-worker-semantic-kind-phase')
 order_ref=reference(result['context']['order']);order=pinned(order_ref)
 offer=pinned(reference(result['context']['offer']))
 need(parent.get('order')==order_ref and offer.get('role_execution',{}).get('order')==order_ref and order.get('workflow')==flow and offer.get('workflow')==flow and order.get('day')==offer.get('active_day')==request['task']['day'] and order.get('dispatch_id')==offer.get('dispatch_id'),'local-worker-original-flow-order')
 need(parent.get('company') in order.get('companies',[]),'local-worker-original-company')
 need(parent.get('root')==parent['company'].get('root') and Path(parent['root']).is_absolute(),'local-worker-original-company-root')
 status=outer['details']['parent_status']
 need(status.get('status')=='waiting' and status.get('order')==order_ref and status.get('child',{}).get('handoff')==parent_ref,'local-worker-parent-status-binding')
 return outer_ref,parent_ref,parent

def run_logged(argv,base):
 # Applies to the entire producer Python process and inherited children.
 # Mechanical adapters run outside this subprocess and retain their loopback UI.
 actual_argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)']+argv
 launch=immutable(base/'launch.json',{'kind':'local-producer-network-denied-launch-v1','actual_argv':actual_argv})
 with (base/'stdout.log').open('wb') as out,(base/'stderr.log').open('wb') as err:
  proc=subprocess.Popen(actual_argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
  immutable(base/'process.json',{'pid':proc.pid,'process':identity(proc.pid),'at':now(),'launch':launch,'actual_argv':actual_argv})
  return proc.wait()

def local_entry(config,prefix):
 # Only a pinned physical script in this Python runtime; no shell/-m/URL entry.
 need(type(prefix) is list and len(prefix)==2 and all(type(a) is str and a for a in prefix),'local-worker-local-producer-argv-required')
 executable=Path(prefix[0]);script=Path(prefix[1])
 need(executable.is_absolute() and executable.resolve()==Path(sys.executable).resolve(),'local-worker-local-python-required')
 entry=reference(config['local_semantic_worker_entry'])
 need(script.is_absolute() and str(script)==entry['path'] and script.suffix=='.py','local-worker-pinned-local-entry-required')
 return ref(executable.resolve()),entry

def producer_config(config,flow):
 # A present map owns routing completely; missing entries never use legacy AI.
 need(flow in ALLOWED,'local-worker-unreviewed-flow')
 if 'local_semantic_workers' not in config:
  return config if config.get('local_semantic_worker_argv') else None
 workers=config['local_semantic_workers']
 need(type(workers) is dict and set(workers)<=set(ALLOWED),'local-worker-type-map-invalid')
 if flow not in workers:return None
 selected=workers[flow]
 need(type(selected) is dict and set(selected)=={'argv','entry'},'local-worker-type-entry-invalid')
 return {'local_semantic_worker_argv':selected['argv'],'local_semantic_worker_entry':selected['entry']}

def step(request,folder,*,adapter_step=None,producer_run=None):
 with lock(Path(folder).resolve()/'local-worker.lock'):
  return _step(request,folder,adapter_step=adapter_step,producer_run=producer_run)

def _step(request,folder,*,adapter_step=None,producer_run=None):
 folder=Path(folder).resolve();request_ref=ref(folder/'request.json')
 need(pinned(request_ref)==request,'local-worker-original-request-file')
 source=ref(Path(__file__).resolve());snapshot=folder/'local-worker-adapter-result.json'
 stage_intent={'kind':'local-worker-mechanical-stage-once-v1','request':request_ref,'source':source}
 stage_path=folder/'local-worker-stage-intent.json'
 # Reentry reuses the ORIGINAL mechanical stage outcome, never invokes it twice.
 if snapshot.exists():
  need(pinned(ref(stage_path))==stage_intent,'local-worker-original-stage-intent-changed')
  old=pinned(ref(snapshot));need(old['request']==request_ref and old['source']==source,'local-worker-original-stage-changed');result=old['result']
 else:
  need(not stage_path.exists(),'local-worker-stage-outcome-unknown-no-replay')
  immutable(stage_path,stage_intent)
  result=(adapter_step or adapters.step)(request,folder)
  need(result.get('task_id')==request['task']['id'] and result.get('attempt_id')==request['attempt_id'],'local-worker-stage-task-binding')
  immutable(snapshot,{'request':request_ref,'source':source,'result':result})
 if result.get('outcome')!='waiting':return result
 outer=pinned(reference(result['handoff']))
 if outer.get('reason')!='parent-ai-or-png-review-required':return result
 if 'local_semantic_workers' not in request['config'] and not request['config'].get('local_semantic_worker_argv'):return result
 result=copy.deepcopy(result)
 try:
  binding=parent_binding(request,result)
  if binding is None:return result # PNG/region and other handoffs never auto-approve.
  outer_ref,parent_ref,parent=binding
  selected=producer_config(request['config'],request['task']['flow'])
  if selected is None:return result
  prefix=selected['local_semantic_worker_argv']
  interpreter,entry=local_entry(selected,prefix)
  base=folder/'local-semantic-worker';base.mkdir(exist_ok=True)
  argv=prefix+['--handoff',parent_ref['path'],'--handoff-sha256',parent_ref['sha256'],'--out-dir',str(base/'outputs')]
  intent={'kind':'local-semantic-worker-once-v1','request':request_ref,'source':source,'outer_handoff':outer_ref,'parent_handoff':parent_ref,'argv':argv,'interpreter':interpreter,'entry':entry}
  intent_path=base/'intent.json';exit_path=base/'exit.json'
  if intent_path.exists():
   need(pinned(ref(intent_path))==intent,'local-worker-original-intent-changed')
   need(exit_path.exists(),'local-producer-outcome-unknown-no-replay')
  else:
   need(not any(base.iterdir()),'local-producer-partial-no-replay')
   immutable(intent_path,intent) # file + directory fsync before subprocess input
   rc=(producer_run or run_logged)(argv,base)
   immutable(exit_path,{'intent':ref(intent_path),'returncode':rc,'stdout':ref(base/'stdout.log'),'stderr':ref(base/'stderr.log'),'exited_at':now()})
  exited=pinned(ref(exit_path));need(exited['intent']==ref(intent_path),'local-worker-exit-intent-binding')
  reference(source);reference(interpreter);reference(entry)
  for name in ('stdout','stderr'):reference(exited[name])
  need(exited['returncode']==0,'local-producer-failed-no-retry')
  output=json.loads(Path(exited['stdout']['path']).read_text())
  need(output.get('status')=='ready','local-producer-exception-handoff-no-accept')
  response_ref=reference(output['response']);receipt_ref=reference(output['receipt']);response=pinned(response_ref);receipt=pinned(receipt_ref)
  need(response.get('kind')==parent['response_kind'] and response.get('request')==parent_ref,'local-producer-typed-response-binding')
  need(receipt.get('kind')=='local-semantic-producer-receipt-v1' and receipt.get('handoff')==parent_ref and receipt.get('response')==response_ref and receipt.get('accept_called') is False,'local-producer-receipt-binding')
  reference(receipt['ledger']);need(receipt['ledger']['path']==str(Path(parent['root'])/'state.json'),'local-producer-original-ledger')
  for field in ('dependencies','code','outputs'):
   need(type(receipt.get(field)) is list and receipt[field],'local-producer-receipt-nonempty-ref-list')
   for item in receipt[field]:reference(item)
  need(entry in receipt['code'],'local-producer-entry-not-in-code')
  need(response_ref in receipt['outputs'],'local-producer-response-not-in-outputs')
  if parent['response_kind']=='violation-copy-response-v1':
   need(set(response)=={'kind','request','copy'},'local-producer-copy-fields');reference(response['copy'])
   need(response['copy'] in receipt['outputs'],'local-producer-copy-not-in-outputs')
  else:
   need(set(response)=={'kind','request','analyses'} and type(response['analyses']) is list and response['analyses'],'local-producer-analysis-fields')
   for item in response['analyses']:
    reference(item);need(item in receipt['outputs'],'local-producer-analysis-not-in-outputs')
  # Parent/dependency references remain verified again by original parent accept.
  outer_response=immutable(base/'workshop-response.json',{'kind':'workshop-handoff-response-v1','request':outer_ref,'task_id':request['task']['id'],'parent_response':response_ref})
  result['context']['response']=outer_response;result['outcome']='continue'
  result['local_semantic_worker']={'status':'ready','receipt':receipt_ref,'response':response_ref,'accept_called':False}
  return result
 except (ValueError,KeyError,OSError,subprocess.SubprocessError) as exc:
  # Never infer that a failed/partial producer did not run, and never restart it.
  failure={'kind':'local-semantic-worker-unresolved-v1','request':request_ref,'error':str(exc),'automatic_retry':False,'accept_called':False}
  diagnostic=immutable(folder/'local-worker-diagnostics'/(digest(failure)+'.json'),failure)
  result['local_semantic_worker']={'status':'exception_handoff','diagnostic':diagnostic};return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--response',required=True);a=p.parse_args()
 request=read(a.request);immutable(a.response,step(request,Path(a.request).parent))
if __name__=='__main__':main()
