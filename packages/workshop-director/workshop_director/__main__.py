import argparse,json,os,signal,sys,time
from pathlib import Path
from .common import *
from .engine import Engine
from . import service

def poll_delay(result,idle_interval):
    # A harvested continuation is dispatched inside the same locked tick.
    # Only a live original process or just-spawned worker needs fast polling.
    return .05 if result.get('action') in ('spawned','wait-original-process','environment-restoration-continue') else idle_interval

def serve_loop(e,interval,stopping,*,sleep=time.sleep):
    while not stopping[0]:
        try:result=e.tick()
        except Exception as err:
            with e.s.transaction():e.s.event('daemon-error',error=str(err))
            result={'action':'error'}
        sleep(poll_delay(result,interval))

def configure_serve_dependencies(root):
    # Host keeps its reviewed framework identity; receipt consumers use the
    # same fixed, version-matched package environment as configured workers.
    project=service.PROJECT;root=Path(root).resolve()
    need(root==project/'runtime/standalone-workshop-director','daemon-fixed-dependency-root')
    config=read(root/'config.json');venv=project/'skills/daily-comment-stats/.venv'
    need(config.get('project')==str(project)and config.get('python')==str(venv/'bin/python')and (venv/'bin/python').is_file(),'daemon-fixed-worker-python')
    cfg=dict(line.split(' = ',1)for line in (venv/'pyvenv.cfg').read_text().splitlines()if ' = 'in line)
    need(cfg.get('version')=='.'.join(map(str,sys.version_info[:3]))and cfg.get('include-system-site-packages')=='false','daemon-dependency-python-version')
    site=venv/'lib'/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages'
    need(site.is_dir()and site.resolve()==site and not any(p.is_symlink()for p in(site,*site.parents)),'daemon-dependency-site-path')
    # Do not execute .pth files, mutate global Python, or rebuild the venv.
    if str(site)not in sys.path:sys.path.append(str(site))
    import importlib
    modules=[importlib.import_module(name)for name in('openpyxl','et_xmlfile')]
    need(all(site in Path(m.__file__).resolve().parents for m in modules),'daemon-dependency-module-origin')
    return {'site_packages':str(site),'python_version':cfg['version'],'modules':{m.__name__:str(Path(m.__file__).resolve())for m in modules}}

def main(argv=None):
    p=argparse.ArgumentParser(description='Local durable workshop scheduler, no coding-agent runtime');p.add_argument('--root',required=True,type=Path);sub=p.add_subparsers(dest='verb',required=True)
    z=sub.add_parser('init');z.add_argument('--project',required=True,type=Path);z.add_argument('--acceptance',required=True,type=Path);z.add_argument('--start-date',required=True);z.add_argument('--paused',action='store_true');z.add_argument('--tab-id',type=int);z.add_argument('--pid',type=int)
    z=sub.add_parser('plan');ss=z.add_subparsers(dest='op',required=True);ss.add_parser('list');a=ss.add_parser('add');a.add_argument('--id',required=True);a.add_argument('--workflow',choices=FLOWS);a.add_argument('--at');a.add_argument('--daily-at');a.add_argument('--start-date');a.add_argument('--priority',type=int,default=50);a.add_argument('--task-id');a.add_argument('--calendar-mode',choices=('cn-workdays',));a.add_argument('--collection-contract',choices=('three-flow-collection-ready-v1',),help='Collect all three flows before unified delivery; requires --paused');a.add_argument('--paused',action='store_true',help='Create a new plan paused; does not pause an existing plan')
    for v in ('pause','resume','cancel'):ss.add_parser(v).add_argument('--id',required=True)
    for v in ('tasks','issues','status'):sub.add_parser(v)
    z=sub.add_parser('tick');z.add_argument('--once',action='store_true',required=True)
    z=sub.add_parser('serve');z.add_argument('--interval',type=float,default=5)
    z=sub.add_parser('accept');z.add_argument('--task',required=True);z.add_argument('--response',required=True,type=Path);z.add_argument('--sha256',required=True)
    for v in ('retry','reconcile'):z=sub.add_parser(v);z.add_argument('--task',required=True);z.add_argument('--repair',type=Path,required=True);z.add_argument('--sha256',required=True)
    z=sub.add_parser('prepare-round-grant');z.add_argument('--request',required=True,type=Path);z.add_argument('--sha256',required=True);z.add_argument('--out-dir',required=True,type=Path)
    z=sub.add_parser('park-round');z.add_argument('--grant',required=True,type=Path);z.add_argument('--sha256',required=True)
    sub.add_parser('reconcile-round')
    z=sub.add_parser('cancel-task');z.add_argument('--task',required=True)
    z=sub.add_parser('service');ss=z.add_subparsers(dest='op',required=True);ss.add_parser('health');a=ss.add_parser('generate');a.add_argument('--out',type=Path,required=True);a=ss.add_parser('install');a.add_argument('--plist',type=Path,required=True);a.add_argument('--install',action='store_true');a=ss.add_parser('uninstall');a.add_argument('--uninstall',action='store_true')
    for op in ('stop','reload'):
        a=ss.add_parser(op);a.add_argument('--out',type=Path,required=True);a.add_argument('--execute',action='store_true')
    a=p.parse_args(argv);root=a.root.resolve()
    if a.verb=='plan' and a.op=='add' and a.collection_contract:need(a.paused,'collection-contract-requires-paused-plan')
    if a.verb=='init':
        need((a.tab_id is None and a.pid is None) or (type(a.tab_id) is int and a.tab_id>0 and type(a.pid) is int and a.pid>0),'explicit-scope-requires-positive-tab-and-pid');context={} if a.tab_id is None else {'tab_id':a.tab_id,'pid':a.pid}
        root.mkdir(parents=True,exist_ok=True);need(not (root/'config.json').exists(),'already-initialized');project=a.project.resolve();need(root==project/'runtime/standalone-workshop-director','fixed-local-scheduler-root-required');accept=a.acceptance.resolve();need(project.is_dir() and accept.is_file(),'project-and-acceptance-required');config={'kind':'standalone-workshop-director-config-v1','project':str(project),'coordinator_root':str(project/'runtime/workshop-director'),'acceptance':str(accept),'python':str(project/'skills/daily-comment-stats/.venv/bin/python'),'resource_lock':str(project/'runtime/workshop-director/browser-wecom.resource.lock'),'mode':'acceptance','context':context,'worker_argv':None,'dispatcher':'local-subprocess-v1'};atomic(root/'config.json',config);e=Engine(root)
        try:
            e.add_plan('morning',daily_at='08:30',start=a.start_date)
            if a.paused:e.set_plan('morning','paused')
        finally:e.close()
        return {'initialized':str(root),'morning':'Asia/Shanghai 08:30','no_dispatch_started':True}
    if a.verb=='service':
        if a.op=='health':return service.health(root)
        if a.op=='generate':return service.generate(root,a.out)
        if a.op=='install':return {'installed':service.install(root,a.plist,a.install)}
        if a.op in ('stop','reload'):
            from . import service_lifecycle
            ticket=service_lifecycle.prepare(root,a.out,a.op)
            return service_lifecycle.apply(ticket,True) if a.execute else {'prepared':ticket,'service_action_executed':False}
        service.uninstall(a.uninstall);return {'uninstalled':True}
    if a.verb=='serve':configure_serve_dependencies(root)
    e=Engine(root)
    try:
        if a.verb=='plan':
            if a.op=='list':return e.s.plans()
            if a.op=='add':return {'plan_id':e.add_plan(a.id,at=a.at,start=a.start_date,daily_at=a.daily_at,workflow=a.workflow,priority=a.priority,task_id=a.task_id,calendar_mode=a.calendar_mode,collection_contract=a.collection_contract,initial_state='paused' if a.paused else 'active')}
            e.set_plan(a.id,{'pause':'paused','resume':'active','cancel':'cancelled'}[a.op]);return {'plan_id':a.id,'state':a.op}
        if a.verb in ('tasks','status'):
            value={'resource_owner':e.s.get('resource_owner'),'tasks':e.s.tasks()};holds=e.calendar_holds()
            if holds:value['calendar_holds']=holds
            return value
        if a.verb=='issues':return [t for t in e.s.tasks() if t['state'] in ('waiting','failed','unknown')]
        if a.verb=='tick':return e.tick()
        if a.verb=='accept':e.accept(a.task,{'path':str(a.response.resolve()),'sha256':a.sha256});return {'resumed_original_task':a.task}
        if a.verb in ('retry','reconcile'):e.repair(a.task,{'path':str(a.repair.resolve()),'sha256':a.sha256},unknown=a.verb=='reconcile');return {'original_task':a.task,'operation':a.verb}
        if a.verb=='prepare-round-grant':
            from . import quiescent_lease_handoff as handoff
            return {'grant':handoff.issue_grant(e,{'path':str(a.request.resolve()),'sha256':a.sha256},a.out_dir),'business_started':False}
        if a.verb in ('park-round','reconcile-round'):
            from . import quiescent_lease_handoff as handoff
            return handoff.start(e,{'path':str(a.grant.resolve()),'sha256':a.sha256}) if a.verb=='park-round' else handoff.advance(e)
        if a.verb=='cancel-task':e.cancel_task(a.task);return {'cancelled':a.task}
        need(a.interval>=.2,'daemon-interval-too-small')
        with lock(root/'daemon.lock',False):
            with e.s.transaction():e.s.set('daemon',{'process':identity(os.getpid()),'started_at':now()})
            stopping=[False]
            signal.signal(signal.SIGTERM,lambda *_:stopping.__setitem__(0,True));signal.signal(signal.SIGINT,lambda *_:stopping.__setitem__(0,True))
            serve_loop(e,a.interval,stopping)
            # Exiting the scheduler never sends a signal to an original worker.
            return {'scheduler_stopped_workers_preserved':True}
    finally:e.close()
if __name__=='__main__':
    try:print(json.dumps(main(),ensure_ascii=False,default=str))
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
