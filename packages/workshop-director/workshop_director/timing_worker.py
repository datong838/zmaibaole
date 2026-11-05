"""Opt-in diagnostic entry for a NEW original workflow request, delegates original worker.
No direct UI/native/browser/messenger calls and no automatic dispatch/retry.
"""
import argparse,os,sys,time
from pathlib import Path
from .common import *

def run(request_path,response_path,step=None):
    request_path=Path(request_path);response_path=Path(response_path);rr=ref(request_path);request=pinned(rr);config=pinned(request['config_ref']);need(config==request['config'],'timing-worker-original-config')
    project=Path(config['project']);root=project/'runtime/standalone-workshop-director';folder=root/'attempts'/request['attempt_id'];python=project/'skills/daily-comment-stats/.venv/bin/python'
    need(request.get('kind')=='workshop-worker-request-v1' and request['root']==str(root) and request_path==folder/'request.json' and response_path==folder/'response.json' and folder.resolve()==folder,'timing-worker-original-attempt')
    need(config['python']==str(python) and Path(sys.executable)==python,'timing-worker-fixed-python')
    need(config.get('worker_argv')==[str(python),'-m','workshop_director.timing_worker'],'timing-worker-explicit-opt-in-config')
    need(request['task']['flow'] in FLOWS and not request['task'].get('payload',{}).get('benchmark'),'timing-worker-known-flow-only-not-benchmark')
    target=str(folder/'wecom-performance');old=os.environ.get('WECOM_PERFORMANCE_DIR');need(old in (None,target),'timing-worker-existing-diagnostic-directory')
    bridge_directory=folder/'bridge-performance';bridge_target=str(bridge_directory);bridge_old=os.environ.get('BRIDGE_REQUEST_PERFORMANCE_DIR')
    need(bridge_directory.resolve()==bridge_directory and not bridge_directory.is_symlink(),'timing-worker-bridge-diagnostic-directory-alias')
    need(bridge_old in (None,bridge_target),'timing-worker-existing-bridge-diagnostic-directory')
    from . import local_worker
    sources=[Path(__file__),Path(local_worker.__file__),project/'skills/wecom-messenger/scripts/performance_trace.py',project/'skills/chrome-dom-export/scripts/bridge.py']
    code=[ref(p) for p in sources];binding={'kind':'wecom-timing-worker-opt-in-v1','request':rr,'config_ref':request['config_ref'],'directory':target,'code_refs':code,'business_entry':'workshop_director.local_worker.step','extra_ui_reads':0,'bridge_directory':bridge_target,'diagnostic_only':True,'bridge_log_fields':['schema','op','elapsed_monotonic_ns','ok','outcome','exception','service','worker'],'command_payload_logged':False}
    immutable(folder/'timing-worker-binding.json',binding);start=time.clock_gettime(time.CLOCK_MONOTONIC);failed=True
    try:
        os.environ['WECOM_PERFORMANCE_DIR']=target;os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR']=bridge_target;result=(step or local_worker.step)(request,folder);immutable(response_path,result);failed=False;return result
    except Exception as error:
        checkpoint=folder/'adapter-context.json'
        result={'kind':'workshop-worker-result-v1','task_id':request['task']['id'],'attempt_id':request['attempt_id'],'context':read(checkpoint) if checkpoint.exists() else request['context'],'outcome':'failed','error':str(error)}
        immutable(response_path,result)
        return result
    finally:
        if old is None:os.environ.pop('WECOM_PERFORMANCE_DIR',None)
        else:os.environ['WECOM_PERFORMANCE_DIR']=old
        if bridge_old is None:os.environ.pop('BRIDGE_REQUEST_PERFORMANCE_DIR',None)
        else:os.environ['BRIDGE_REQUEST_PERFORMANCE_DIR']=bridge_old
        try:immutable(folder/'timing-worker-scope.json',{'kind':'wecom-timing-worker-scope-v1','request':rr,'clock':'CLOCK_MONOTONIC','elapsed_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-start,'business_exception':failed,'business_receipt_modified':False,'no_performance_pass_claim':True})
        except Exception:pass # diagnostics cannot replace a business exception/result

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--response',required=True);a=p.parse_args();run(a.request,a.response)
if __name__=='__main__':main()
