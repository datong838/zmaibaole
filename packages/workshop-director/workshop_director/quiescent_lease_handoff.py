"""Reviewed, quiescent old/new round lease exchange. No completion is invented.
Only scheduler task state/owner and the SAME coordinator state/config are swapped.
Each cross-store write is recoverable solely through its immutable exact intent.
"""
import copy,importlib,sys
from datetime import date,timedelta
from pathlib import Path
from .common import *
KIND='quiescent-round-lease-handoff-v1'
KEY='quiescent_round_handoff'
def coordinator(e):
    sys.path.insert(0,str(Path(e.config['project'])/'skills/workshop-director/scripts'))
    c=importlib.import_module('coordinator');need(Path(c.__file__).resolve()==Path(e.config['project'])/'skills/workshop-director/scripts/coordinator.py','handoff-coordinator-origin');return c

def quiet(e):
    need(next(p for p in e.s.plans() if p['id']=='morning')['state']=='paused','handoff-morning-must-stay-paused')
    need(not any(t['state']in('running','dispatching','unknown')for t in e.s.tasks()),'handoff-live-or-unknown-task')

def no_unknown(value):
    if isinstance(value,dict):
        need(value.get('state')not in('unknown','dispatching','intent'),'handoff-input-frontier-unresolved')
        for key in ('calls','operations','events','frames'):
            for item in value.get(key,[]) if isinstance(value.get(key,[]),list) else []:
                if isinstance(item,dict):need(item.get('state')not in('unknown','dispatching','running','intent'),'handoff-input-frontier-unresolved')
        for v in value.values():no_unknown(v)
    elif isinstance(value,list):
        for v in value:no_unknown(v)

def original_exit(task):
    folder=Path(task['active_attempt']);exitref=ref(folder/'exit.json');exit=pinned(exitref);request=pinned(exit['request']);response=pinned(exit['response']);started=read(folder/'started.json')
    need(exit['attempt_id']==folder.name==request['attempt_id']==response['attempt_id'] and request['task']['id']==response['task_id']==task['id'] and (exit['returncode']!=0 or response['outcome']=='failed'),'handoff-original-natural-failure-required')
    need(not same_process(started['process']),'handoff-original-worker-live');return exitref

def code_guard(e,c,grant):
    expected={str(Path(__file__).resolve()),str(Path(sys.modules[e.__class__.__module__].__file__).resolve()),str(Path(__file__).with_name('__main__.py').resolve()),str(Path(c.__file__).resolve())}
    refs=grant['code_refs'];need(len(refs)==4 and {r['path']for r in refs}==expected,'handoff-exact-four-source-pins-required')
    for r in refs:need(ref(Path(r['path']))==r,'handoff-current-source-changed')

def session(e):
    pointer=e.s.get(KEY)
    if not pointer:return None
    value=pinned(pointer);need(value['kind']==KIND and value['root']==str(e.root) and value['coordinator_root']==e.config['coordinator_root'],'handoff-session-scope')
    if phase(e,value)['phase']!='complete':code_guard(e,coordinator(e),pinned(value['grant']))
    return value

def journal(e,s):return e.root/'lease-handoffs'/s['grant']['sha256']
def snapshot(c,path,reference):
    raw=Path(reference['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'handoff-snapshot-input-changed');c.immutable(path,raw);return ref(path)

def phase(e,s):
    p=journal(e,s)/'phase.json';return read(p) if p.exists() else {'phase':'pending-park'}

def transition(e,c,s,label,task_before,task_after,state_after,config_after,owner):
    """Caller holds scheduler+coordinator locks; no RPC or worker invocation."""
    folder=journal(e,s)/label;intent=folder/'intent.json';root=Path(e.config['coordinator_root'])
    if not intent.exists():
        before={'task':task_before,'owner':e.s.get('resource_owner'),'state':ref(root/'state.json'),'config':ref(root/'coordinator.json')}
        after={'task':task_after,'owner':owner,'state':immutable(folder/'state-after.json',state_after),'config':immutable(folder/'config-after.json',config_after)}
        if label=='restore-old':after['state']=s['old_state'];after['config']=s['old_config']
        if label=='restore-new':after['state']=ref(journal(e,s)/'new-paused-state.json')
        immutable(intent,{'kind':'quiescent-lease-exchange-intent-v1','session':e.s.get(KEY),'label':label,'before':before,'after':after})
    plan=read(intent);need(task_before['id']==pinned(s['grant'])['task_id'] and task_after['id']==task_before['id'],'handoff-intent-original-task-required');need(plan['session']==e.s.get(KEY) and plan['label']==label,'handoff-intent-binding');before,after=plan['before'],plan['after'];task=e.s.task(task_before['id']);need(task in(before['task'],after['task']),'handoff-task-raced')
    c.exchange_quiescent_state(root,before['state'],before['config'],after['state'],after['config'])
    with e.s.transaction():
        current=e.s.task(task_before['id']);need(current in(before['task'],after['task']) and e.s.get('resource_owner')in(before['owner'],after['owner']),'handoff-queue-raced')
        need({k:v for k,v in before['task'].items()if k!='state'}=={k:v for k,v in after['task'].items()if k!='state'},'handoff-cannot-rewrite-original-task')
        e.s.update(task_before['id'],state=after['task']['state']);e.s.set('resource_owner',after['owner'])
        e.s.event('quiescent-lease-exchanged',task_before['id'],intent=ref(intent))
    immutable(folder/'returned.json',{'intent':ref(intent),'task':after['task'],'state':ref(root/'state.json'),'config':ref(root/'coordinator.json'),'owner':after['owner']})

def issue_grant(e,request_ref,out,*,at=None):
    request=pinned(request_ref);need(request.get('kind')=='reviewed-quiescent-round-handoff-request-v1','handoff-reviewed-request-required');when=at or datetime.now(ZONE);need(when.utcoffset()is not None,'handoff-aware-issue-time');value={**request,'kind':'reviewed-quiescent-round-handoff-grant-v1','request':request_ref,'issued_at':when.isoformat(),'new_day':when.astimezone(ZONE).date().isoformat()};code_guard(e,coordinator(e),value);need(value['new_day']>value['old_day'],'handoff-new-day-after-old');return immutable(Path(out)/(digest(value)+'.json'),value)

def start(e,grant_ref,*,at=None):
    g=pinned(grant_ref);need(g.get('kind')=='reviewed-quiescent-round-handoff-grant-v1' and g['root']==str(e.root) and g['coordinator_root']==e.config['coordinator_root'],'handoff-grant-scope')
    target=g['browser_scope_target'];need(set(target)=={'tab_id','window_id','url','groupid'} and type(target['tab_id'])is int and target['tab_id']>0 and type(target['window_id'])is int and target['window_id']>0,'handoff-explicit-browser-target-required')
    when=at or datetime.now(ZONE);need(when.utcoffset()is not None and g['new_day']>g['old_day'] and date.fromisoformat(g['new_day']).isoformat()==g['new_day'] and timestamp(g['issued_at']).astimezone(ZONE).date().isoformat()==g['new_day'],'handoff-current-issued-day-required')
    if not e.s.get(KEY):need(g['new_day']==when.astimezone(ZONE).date().isoformat(),'handoff-date-expired-reprepare-before-park')
    need(g['quiescent_refs'] and all(g.get(k)is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_keys_preserved')),'handoff-reviewed-quiescence-required')
    c=coordinator(e)
    with lock(e.root/'scheduler.lock'),lock(Path(e.config.get('resource_lock',str(Path(e.config['coordinator_root'])/'browser-wecom.resource.lock'))),False),c.locked(Path(e.config['coordinator_root'])) as root:
        quiet(e);code_guard(e,c,g)
        if e.s.get(KEY):need(session(e)['grant']==grant_ref,'handoff-other-session');return advance_locked(e,c,session(e))
        need(isinstance(g['new_plan_id'],str) and re.fullmatch('[A-Za-z0-9_-]{8,128}',g['new_plan_id']),'handoff-new-plan-id')
        task=e.s.task(g['task_id']);need(task==pinned(g['task']) and task['state']=='failed' and task['flow']==FLOWS[2] and task['day']==g['old_day'] and e.s.get('resource_owner')==task['id'],'handoff-exact-failed-original-owner')
        need(original_exit(task)==g['natural_exit'],'handoff-natural-exit-changed')
        for r in g['quiescent_refs']:no_unknown(pinned(r))
        need(ref(root/'state.json')==g['coordinator_state'] and ref(root/'coordinator.json')==g['coordinator_config'],'handoff-canonical-changed')
        state=pinned(g['coordinator_state']);config=pinned(g['coordinator_config']);need(state['day']==g['old_day'] and state['index']==2 and config['active_day']==g['old_day'],'handoff-original-last-role-only');c.verify_config_acceptance(config,state)
        e.add_plan(g['new_plan_id'],at=g['new_day']+'T00:00:00+08:00',initial_state='paused')
        folder=e.root/'lease-handoffs'/grant_ref['sha256'];session_ref=immutable(folder/'session.json',{'kind':KIND,'root':str(e.root),'coordinator_root':e.config['coordinator_root'],'grant':grant_ref,'task':g['task'],'old_state':snapshot(c,folder/'old-state.json',g['coordinator_state']),'old_config':snapshot(c,folder/'old-config.json',g['coordinator_config']),'new_state':immutable(folder/'initial-new-state.json',c.d.initialize(g['new_day'],config['acceptance']))})
        with e.s.transaction():e.s.set(KEY,session_ref)
        return advance_locked(e,c,pinned(session_ref))

def advance_locked(e,c,s):
    quiet(e);folder=journal(e,s);g=pinned(s['grant']);p=phase(e,s);root=Path(e.config['coordinator_root']);task=e.s.task(g['task_id']);state=read(root/'state.json');config=read(root/'coordinator.json')
    # A crash can publish either coordinator JSON before the task/phase row.
    # Reconcile the SAME intent first, regardless of the current active day.
    for label,before_phase,after_phase in (('park-old','pending-park','new-first-two'),('restore-old','new-first-two','old-restored'),('restore-new','old-restored','new-final-role')):
        ip=folder/label/'intent.json'
        if p['phase']==before_phase and ip.exists():
            plan=read(ip);before,after=plan['before'],plan['after'];original=pinned(s['task'])
            if label=='park-old':need(before['task']==original and after['task']=={**original,'state':'parked'},'handoff-park-intent-task-changed')
            if label=='restore-old':need(before['task']=={**original,'state':'parked'} and after['task']==original and after['state']==s['old_state'] and after['config']==s['old_config'],'handoff-restore-intent-task-changed')
            if label=='restore-new':need(before['task']['state']==after['task']['state']=='complete' and before['task']==after['task'] and after['state']==ref(folder/'new-paused-state.json'),'handoff-complete-intent-changed')
            transition(e,c,s,label,before['task'],after['task'],pinned(after['state']),pinned(after['config']),after['owner']);atomic(folder/'phase.json',{'phase':after_phase});return {'action':'quiescent-round-handoff','phase':after_phase,'original_task':g['task_id']}
    if p['phase']=='pending-park':
        old=pinned(s['task']);parked={**old,'state':'parked'};nc={**pinned(s['old_config']),'active_day':g['new_day']};transition(e,c,s,'park-old',old,parked,pinned(s['new_state']),nc,None);atomic(folder/'phase.json',{'phase':'new-first-two'})
    elif p['phase']=='new-first-two' and state['day']==g['new_day'] and state['index']==2 and state['phase']=='ready':
        need(e.s.get('resource_owner')is None,'handoff-boundary-owner-not-released')
        need(all(any(t['day']==g['new_day'] and t['plan_id']==g['new_plan_id'] and t['flow']==flow and t['state']=='complete' for t in e.s.tasks()) for flow in FLOWS[:2]),'handoff-new-first-two-not-complete')
        need(not any(t['day']==g['new_day'] and t['flow']==FLOWS[2] and t['attempt'] for t in e.s.tasks()),'handoff-new-violation-already-dispatched')
        parked={**pinned(s['task']),'state':'parked'};need(task==parked,'handoff-parked-task-changed');snapshot(c,folder/'new-paused-state.json',ref(root/'state.json'));snapshot(c,folder/'new-paused-config.json',ref(root/'coordinator.json'));transition(e,c,s,'restore-old',parked,pinned(s['task']),pinned(s['old_state']),pinned(s['old_config']),task['id']);atomic(folder/'phase.json',{'phase':'old-restored'})
    elif p['phase']=='old-restored' and task['state']=='complete':
        need(e.s.get('resource_owner')is None,'handoff-boundary-owner-not-released')
        need(state['day']==g['old_day'] and c.d.current(state).get('action')=='done','handoff-old-real-completion-required');c.archive(root,state,config)
        ns=read(folder/'new-paused-state.json');nc=read(folder/'new-paused-config.json');nc['archives']=config['archives'];transition(e,c,s,'restore-new',task,task,ns,nc,None);atomic(folder/'phase.json',{'phase':'new-final-role'})
    elif p['phase']=='new-final-role' and state['day']==g['new_day'] and c.d.current(state).get('action')=='done':
        need(all(t['state']=='complete'for t in e.s.tasks()if t['day']==g['new_day']),'handoff-new-tasks-not-complete');atomic(folder/'phase.json',{'phase':'complete'})
    return {'action':'quiescent-round-handoff','phase':phase(e,s)['phase'],'original_task':g['task_id']}

def _advance(e):
    s=session(e)
    if not s or phase(e,s)['phase']=='complete':return None
    if any(t['state']in('running','dispatching')for t in e.s.tasks()):return None
    c=coordinator(e)
    with lock(e.root/'scheduler.lock'),lock(Path(e.config.get('resource_lock',str(Path(e.config['coordinator_root'])/'browser-wecom.resource.lock'))),False),c.locked(Path(e.config['coordinator_root'])):
        # Active original children are harvested normally; never swap under them.
        if any(t['state']in('running','dispatching')for t in e.s.tasks()):return None
        result=advance_locked(e,c,s)
    restoration=resume_old(e,s)
    return restoration or result

def advance(e):
    if not e.s.get(KEY):return None
    with lock(e.root/'lease-handoff.lock',False):return _advance(e)

def admission(e):
    s=session(e)
    if not s:return None
    p=phase(e,s)['phase']
    if p=='complete':return None
    g=pinned(s['grant'])
    need(p!='pending-park','handoff-incomplete-intent-no-dispatch')
    for folder in journal(e,s).glob('*'):
        if folder.is_dir() and (folder/'intent.json').exists():need((folder/'returned.json').exists(),'handoff-unreconciled-intent-no-dispatch')
    return {'phase':p,'old_task':g['task_id'],'old_day':g['old_day'],'new_day':g['new_day'],'new_plan':g['new_plan_id']}

def eligible(binding,task):
    if not binding or binding['phase']=='complete':return True
    if binding['phase']=='new-first-two':return task['plan_id']==binding['new_plan'] and task['day']==binding['new_day'] and task['flow']in FLOWS[:2]
    if binding['phase']=='old-restored':return task['id']==binding['old_task']
    if binding['phase']=='new-final-role':return task['plan_id']==binding['new_plan'] and task['day']==binding['new_day'] and task['flow']==FLOWS[2]
    return False

def discover_scope(e):
    """Current public process/tabs read; never inherit config's old tab/PID."""
    from .adapters import browser_processes
    found=browser_processes();need(len(found['candidates'])==1,'handoff-unique-current-Chrome-required')
    import importlib.util
    path=Path(e.config['project'])/'skills/chrome-dom-export/scripts/bridge.py';spec=importlib.util.spec_from_file_location('handoff_public_bridge',path);bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    reply=bridge.request({'op':'tabs'});need(reply.get('ok')is True,'handoff-current-tabs-unavailable')
    from urllib.parse import urlsplit
    active=session(e);target=pinned(active['grant'])['browser_scope_target'] if active else None;initial=journal(e,active)/'initial-browser-scope.json' if active else None
    prior=pinned(ref(initial)) if initial and initial.exists() else None
    if prior:need(found['candidates'][0]['process']==prior['process_discovery']['candidates'][0]['process'],'handoff-current-browser-process-changed')
    from urllib.parse import parse_qs
    targets=[]
    for window in reply['result']:
        for tab in window.get('tabs',[]):
            u=urlsplit(tab.get('url',''))
            if not(tab.get('active')is True and tab.get('allowed')is True and tab.get('windowId')==window.get('windowId') and u.scheme=='https' and u.netloc=='life.douyin.com'):continue
            if target and not(tab.get('tabId')==target['tab_id'] and tab.get('windowId')==target['window_id']):continue
            if target and not prior and not(tab['url']==target['url'] and u.path=='/p/governance/violation_list' and parse_qs(u.query).get('groupid')==[str(target['groupid'])]):continue
            targets.append(tab)
    need(len(targets)==1,'handoff-unique-current-existing-tab-required');return {'scope':{'tab_id':targets[0]['tabId'],'pid':found['candidates'][0]['pid']},'process_discovery':found,'tabs_reply':reply,'observed_at':now(),'no_input_used':True}

def local_day():return datetime.now(ZONE).date().isoformat()

def bind_new_scope(e,binding,task):
    first=bool(binding and task['day']==binding['new_day'] and not any(t['plan_id']==binding['new_plan'] and t['attempt'] for t in e.s.tasks()))
    if first:need(task['day']==local_day(),'handoff-date-expired-before-first-flow-reprepare')
    if not binding or task['day']!=binding['new_day'] or task['attempt'] or task['context'].get('scope'):return task
    s=session(e);folder=journal(e,s)/'browser-scopes';proof=discover_scope(e)
    immutable(journal(e,s)/'initial-browser-scope.json',pinned(ref(journal(e,s)/'initial-browser-scope.json')) if (journal(e,s)/'initial-browser-scope.json').exists() else proof)
    reference=immutable(folder/(task['id']+'-'+str(len(list(folder.glob(task['id']+'-*.json')))).zfill(4)+'.json'),proof)
    if first:need(task['day']==local_day(),'handoff-date-expired-before-first-flow-reprepare')
    selected=proof['process_discovery']['candidates'][0]
    browser_binding={'kind':'task-browser-process-binding-v1','scope':proof['scope'],'comm':selected['comm'],'process':selected['process'],'discovery':proof['process_discovery']}
    context={**task['context'],'scope':proof['scope'],'browser_binding':browser_binding,'program_scope_discovery':reference}
    e.s.update(task['id'],context=context);return e.s.task(task['id'])

def resume_old(e,s):
    g=pinned(s['grant']);task=e.s.task(g['task_id'])
    if phase(e,s)['phase']!='old-restored' or task['state']!='failed':return
    need(task==pinned(s['task']),'handoff-old-task-before-repair-changed');folder=journal(e,s)/'ordinary-old-repair';intent=folder/'intent.json';returned=folder/'returned.json'
    sys.path.insert(0,str(Path(e.config['project'])/'skills/violation-notifier/scripts'));r=importlib.import_module('violation_reboot_continuation');timing=importlib.import_module('execution_timing')
    expected={'kind':'reviewed-original-source-repair-then-retry-v1','task':s['task'],'release':g['repair_release'],'activation':g['activation']}
    first=not intent.exists();immutable(intent,expected)
    if first:result=r.repair_source(g['repair_release'],clock=timing.Clock(),process_reader=identity)
    else:
        # An interrupted call is never dispatched twice: only its already-durable
        # original source repair may be reconciled through the real validator.
        value=r.verify(g['activation'],live_boot=boot());result=value['source_repair']
    value=r.verify(g['activation'],live_boot=boot());need(value==r.verify(r.doc(g['activation'])['admission'],live_boot=boot()) and r.doc(r.doc(result)['transition'])['release']==g['repair_release'],'handoff-old-repair-not-complete')
    immutable(returned,{'intent':ref(intent),'source_repair':result})
    proof=immutable(folder/'retry-proof.json',{'kind':'workshop-repair-v1','task_id':task['id'],'attempt_id':Path(task['active_attempt']).name,'outcome':'repaired-existing-order',**{k:g[k]for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_keys_preserved')}})
    # Engine's established proof uses this exact field spelling.
    value=pinned(proof);value['original_order_keys_preserved']=value.pop('original_keys_preserved');proof=immutable(folder/'ordinary-retry-proof.json',value)
    restoration=r.restore_environment(s['grant'],clock=timing.Clock(),process_reader=identity)
    need(type(restoration)is dict and restoration.get('status')in('continue','complete'),'handoff-environment-restore-contract')
    if restoration['status']=='continue':
        pinned(restoration['journal']);return {'action':'environment-restoration-continue','journal':restoration['journal'],'task':task['id']}
    r.verify_environment(restoration['completion'],s['grant'],live=True)
    immutable(folder/'environment-complete.json',{'completion':restoration['completion'],'grant':s['grant']})
    e.repair(task['id'],proof)
