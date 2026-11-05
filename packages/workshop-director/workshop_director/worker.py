"""Ordinary subprocess supervisor; receipt before exit, never retries a command."""
import argparse,os,subprocess,sys,time
from pathlib import Path
from .common import *
def run(folder):
    folder=Path(folder).resolve();intent=read(folder/'intent.json');request=pinned(intent['request']);config=pinned(request['config_ref']);need(config==request['config'],'configuration-changed-after-intent')
    root=Path(request['root']);resource=config['resource_lock'];staged=request['task'].get('payload',{}).get('collection_contract')=='three-flow-collection-ready-v1'
    if staged:
        resource_path=Path(resource);need(resource_path==Path(config['project'])/'runtime/workshop-director/browser-wecom.resource.lock'and resource_path.resolve()==resource_path and not any(p.is_symlink()for p in(resource_path,*resource_path.parents)),'staged-fixed-resource-path')
    with lock(folder/'claim.lock',False),lock(resource,False)as resource_handle:
        need(not (folder/'started.json').exists() and not (folder/'exit.json').exists(),'attempt-already-started-never-replay')
        resource_binding=None
        if staged:
            stat=os.fstat(resource_handle.fileno());resource_binding={'kind':'staged-inherited-resource-lock-v1','path':resource,'device':stat.st_dev,'inode':stat.st_ino,'fd':resource_handle.fileno(),'supervisor_source':ref(Path(__file__))}
        immutable(folder/'started.json',{'attempt_id':folder.name,'process':identity(os.getpid()),'at':now(),'request':intent['request'],**({'resource_binding':resource_binding}if staged else{})})
        response=folder/'response.json';argv=config.get('worker_argv') or [config['python'],'-m','workshop_director.adapters']
        need(isinstance(argv,list) and argv and all(type(x) is str for x in argv),'worker-argv-required')
        argv=argv+['--request',intent['request']['path'],'--response',str(response)]
        immutable(folder/'child-intent.json',{'attempt_id':folder.name,'argv':argv,'at':now(),'request':intent['request']})
        with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
            # No timeout, cancellation, shell, credential sourcing, or implicit retry.
            if staged:
                env=os.environ.copy();need('WORKSHOP_STAGED_RESOURCE_FD'not in env,'staged-resource-fd-env-already-present');env['WORKSHOP_STAGED_RESOURCE_FD']=str(resource_handle.fileno())
                proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=config['project'],env=env,pass_fds=(resource_handle.fileno(),))
            else:proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=config['project'])
            immutable(folder/'child-process.json',{'attempt_id':folder.name,'process':identity(proc.pid),'pid':proc.pid,'argv':argv,'at':now(),**({'resource_binding':resource_binding}if staged else{})});rc=proc.wait()
        value={'kind':'workshop-worker-exit-v1','attempt_id':folder.name,'request':intent['request'],'returncode':rc,'exited_at':now(),'exited_monotonic':time.monotonic(),'response':ref(response) if response.exists() else None,'stdout':ref(folder/'stdout.log'),'stderr':ref(folder/'stderr.log')}
        immutable(folder/'exit.json',value)
def main():
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);a=p.parse_args()
    try:run(a.attempt);return 0
    except BaseException as e:
        # A missing exit is UNKNOWN even if the supervisor itself crashed. Never
        # invent a child failure receipt that could authorize another input.
        try:atomic(Path(a.attempt)/'supervisor-error.json',{'at':now(),'error':str(e),'automatic_replay_allowed':False})
        except Exception:pass
        return 2
if __name__=='__main__':raise SystemExit(main())
