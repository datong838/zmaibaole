"""Pure original completion verification under the original configured interpreter.
Never calls step, a parent CLI, messenger, browser or business writes.
"""
import argparse,json,sys
from pathlib import Path
# -I intentionally ignores ambient PYTHONPATH; load only this reviewed package.
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from workshop_director.common import pinned,ref,need,digest,read

def original_inputs(request_ref,response_ref):
    request=pinned(request_ref);response=pinned(response_ref);root=Path(request['root']);folder=root/'attempts'/request['attempt_id']
    need(root.is_absolute() and root.resolve()==root and root.name=='standalone-workshop-director','completion-verifier-root')
    need(Path(request_ref['path'])==folder/'request.json' and Path(response_ref['path'])==folder/'response.json' and folder.resolve()==folder,'completion-verifier-canonical-attempt')
    need(request['kind']=='workshop-worker-request-v1' and response['kind']=='workshop-worker-result-v1' and response['outcome']=='complete' and response['task_id']==request['task']['id'] and response['attempt_id']==request['attempt_id'],'completion-verifier-original-response')
    need(pinned(request['config_ref'])==request['config'],'completion-verifier-original-config')
    config=request['config'];project=Path(config['project']);expected=project/'skills/daily-comment-stats/.venv/bin/python'
    need(project.is_absolute() and project.resolve()==project and root==project/'runtime/standalone-workshop-director' and config['python']==str(expected) and expected.is_file(),'completion-verifier-fixed-python')
    need(Path(sys.executable)==expected,'completion-verifier-interpreter-mismatch')
    exit=read(folder/'exit.json');need(exit['returncode']==0 and exit['attempt_id']==request['attempt_id'] and exit['request']==request_ref and exit['response']==response_ref,'completion-verifier-original-natural-exit')
    return request,response,config

def verify(request_ref,response_ref):
    request,response,config=original_inputs(request_ref,response_ref)
    exit_ref=ref(Path(request_ref['path']).parent/'exit.json')
    from workshop_director import adapters
    need(Path(adapters.__file__).resolve().parent==Path(__file__).resolve().parent,'completion-verifier-module-origin')
    codes=[ref(Path(__file__)),ref(Path(adapters.__file__))]
    result=adapters._verify_completion_in_process(request['task'],response,config)
    need(pinned(request_ref)==request and pinned(response_ref)==response and pinned(request['config_ref'])==config and ref(Path(exit_ref['path']))==exit_ref,'completion-verifier-input-changed')
    need([ref(Path(r['path'])) for r in codes]==codes,'completion-verifier-code-changed')
    report=response['completion']['report'];need(pinned(report)==result,'completion-verifier-report-changed')
    return {'kind':'original-config-python-completion-verified-v1','request':request_ref,'response':response_ref,'original_exit':exit_ref,'report':report,'report_digest':digest(result),'code_refs':codes,'ui_used':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--request-sha256',required=True);p.add_argument('--response',required=True);p.add_argument('--response-sha256',required=True);a=p.parse_args()
    try:
        result=verify({'path':a.request,'sha256':a.request_sha256},{'path':a.response,'sha256':a.response_sha256});print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())
