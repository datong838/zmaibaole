"""Real original coordinator/order/parent adapters. No implicit AI or GUI agent.
Each subprocess makes one durable stage, never replays an unresolved invocation.
"""
import argparse,inspect,os,subprocess,sys,time
from pathlib import Path
from .common import *

CHROME_MAIN='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
def browser_processes():
    # comm is the executable, never argv/environment/profile or browser contents.
    argv=['/bin/ps','-ax','-o','pid=','-o','comm=']
    raw=subprocess.check_output(argv,text=True,stderr=subprocess.DEVNULL,timeout=5)
    candidates=[]
    for line in raw.splitlines():
        pair=line.strip().split(None,1)
        if len(pair)==2 and pair[0].isdigit() and pair[1]==CHROME_MAIN:
            pid=int(pair[0]);process=identity(pid)
            if process:candidates.append({'pid':pid,'comm':pair[1],'process':process})
    return {'kind':'public-ps-chrome-main-observation-v1','argv':argv,'observed_at':now(),'stdout_sha256':hashlib.sha256(raw.encode()).hexdigest(),'candidates':candidates}

def browser_tab_inventory(config):
    # Existing DOM extension transport only; no activation, focus or page input.
    command={'op':'tabs'}
    argv=[config['python'],'-B',str(Path(config['project'])/'skills/chrome-dom-export/scripts/bridge.py'),'request',json.dumps(command),'--timeout','20']
    reply=subprocess.run(argv,capture_output=True,text=True,timeout=25)
    need(reply.returncode==0,'browser-tab-discovery-command-failed')
    value=json.loads(reply.stdout);need(value.get('ok') is True and isinstance(value.get('result'),list),'browser-tab-discovery-pending')
    return {'kind':'dom-only-browser-tab-inventory-v1','command':command,'observed_at':now(),'windows':value['result']}

def business_tab_candidates(inventory,groupids):
    from urllib.parse import urlsplit,parse_qs
    windows=inventory.get('windows');need(inventory.get('kind')=='dom-only-browser-tab-inventory-v1' and inventory.get('command')=={'op':'tabs'} and isinstance(windows,list),'browser-tab-inventory-invalid')
    need(groupids and all(isinstance(g,str) and g.isdigit() for g in groupids),'browser-tab-order-groupids-required')
    need(len({w.get('windowId') for w in windows})==len(windows),'browser-tab-window-duplicate')
    candidates=[]
    paths={'/p/home','/p/life_comment/management','/p/governance/violation_list','/p/governance/home_violation_center'}
    keys={'groupid','life_biz_view_id','life_account_biz_ids','EndTime','StartTime','enter_from','ViolationReasons','IndicatorTags','manual_switch'}
    all_ids=[t.get('tabId') for w in windows for t in w.get('tabs',[])]
    need(len(set(all_ids))==len(all_ids),'browser-tab-id-duplicate')
    for w in windows:
        need(type(w.get('windowId')) is int and w['windowId']>0 and isinstance(w.get('tabs'),list),'browser-tab-window-invalid')
        if w.get('type')!='normal':continue
        for t in w['tabs']:
            u=urlsplit(t.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
            records=u.path.startswith('/p/fulfillsettle/') and '/export_records/' in u.path and u.path.rstrip('/').endswith('/20101')
            if not (t.get('allowed') is True and u.scheme=='https' and u.netloc=='life.douyin.com' and (u.path in paths or records)):continue
            need(type(t.get('tabId')) is int and t['tabId']>0 and t.get('windowId')==w['windowId'],'browser-tab-scope-invalid')
            # Everything below decides whether THIS tab is a usable candidate.
            # It is a filter, not an invariant of the world: one unrelated tab
            # must never disable the whole batch. A violation_list tab carrying
            # TaskID/isNextNotice/drawerForV2 (a notice drawer opened from the
            # violation centre) made the daily 10-30 complaint task wait ten
            # hours and then block every queued day behind it. An unqualified
            # tab is skipped; an empty candidate set still fails closed in
            # select_new_task_tab. The inventory's own structure stays asserted
            # above (duplicate window/tab ids, window shape, tab id in range).
            if u.fragment or not set(q)<=keys or any(len(v)!=1 for v in q.values()):continue
            if q.get('groupid',[None])[0] not in groupids:continue
            if 'manual_switch' in q and not(u.path=='/p/governance/home_violation_center' and q['manual_switch']==['1']):continue
            pair={'life_biz_view_id','life_account_biz_ids'}&set(q)
            if pair and not(pair=={'life_biz_view_id','life_account_biz_ids'} and q['life_biz_view_id']==['22'] and q['life_account_biz_ids']==['']):continue
            candidates.append({'tab_id':t['tabId'],'window_id':w['windowId'],'url':t['url'],'groupid':q['groupid'][0],'selection':'unique-normal-window-allowed-business-tab','identity_verified':False})
    return candidates

def completed_task_browser_scope(task,current_process):
    context=task.get('context',{});binding=context.get('browser_binding',{});scope=context.get('scope',{})
    if binding.get('process')==current_process:
        need(binding.get('kind')=='task-browser-process-binding-v1'and binding.get('comm')==CHROME_MAIN and binding.get('scope')==scope and scope.get('pid')==current_process['pid'],'browser-predecessor-binding')
        return scope
    if not context.get('reboot_continuation') or not context.get('effective_scope'):return None
    resolved=pinned(context['scope_resolution'])
    need(resolved.get('kind')=='resolved-reboot-browser-scope-v1'and resolved.get('reason')is None and resolved['reboot_continuation']==context['reboot_continuation']and resolved['binding']==binding and resolved['original_scope']==scope and resolved['scope']==context['effective_scope'],'browser-predecessor-recovered-scope')
    found=resolved['discovery']['candidates']
    if len(found)==1 and found[0]['process']!=current_process:return None
    need(len(found)==1 and found[0]['comm']==CHROME_MAIN and found[0]['pid']==current_process['pid']and found[0]['process']==current_process and resolved['scope']['pid']==current_process['pid'],'browser-predecessor-recovered-process')
    return resolved['scope']

def validate_completed_browser_predecessor(value,current_process):
    # Shallow already-completed program facts only. Never replay old business graphs.
    need(set(value)=={'kind','scheduler_root','process','same_process_completed_count','selected','completed_before'} and value['kind']=='completed-task-browser-predecessor-v1','browser-predecessor-schema')
    need(value['process']==current_process and type(value['same_process_completed_count']) is int and value['same_process_completed_count']>=0,'browser-predecessor-process')
    cutoff=datetime.fromisoformat(value['completed_before'].replace('Z','+00:00'));need(cutoff.tzinfo is not None,'browser-predecessor-cutoff-aware')
    selected=value['selected'];count=value['same_process_completed_count']
    if selected is None:
        need(count==0,'browser-predecessor-missing-selection');return None
    need(count>0 and set(selected)=={'task','task_sha256','request','exit','response'},'browser-predecessor-selection')
    task=selected['task'];need(selected['task_sha256']==digest(task) and task['state']=='complete' and task['flow'] in FLOWS and task['error'] is None,'browser-predecessor-completed-task')
    context=task['context'];scope=completed_task_browser_scope(task,current_process);outer=task['outer']
    need(scope is not None,'browser-predecessor-binding')
    need(type(scope['tab_id']) is int and scope['tab_id']>0,'browser-predecessor-tab')
    end=datetime.fromisoformat(outer['ended_at'].replace('Z','+00:00'));start=datetime.fromisoformat(outer['started_at'].replace('Z','+00:00'))
    need(end.tzinfo is not None and start.tzinfo is not None and start<=end<cutoff,'browser-predecessor-completed-clock')
    root=Path(value['scheduler_root']);need(root.is_absolute() and root.resolve()==root,'browser-predecessor-root')
    attempt=Path(task['active_attempt']);need(attempt==root/'attempts'/(task['id']+'-'+str(task['attempt'])),'browser-predecessor-attempt')
    need(selected['request']['path']==str(attempt/'request.json') and selected['exit']['path']==str(attempt/'exit.json') and selected['response']['path']==str(attempt/'response.json'),'browser-predecessor-receipt-path')
    request=pinned(selected['request']);exited=pinned(selected['exit']);response=pinned(selected['response'])
    need(request['root']==str(root) and request['task']['id']==task['id'] and request['attempt_id']==attempt.name,'browser-predecessor-request')
    need(exited['kind']=='workshop-worker-exit-v1' and exited['attempt_id']==attempt.name and exited['returncode']==0 and exited['request']==selected['request'] and exited['response']==selected['response'],'browser-predecessor-natural-exit')
    expected_context={**response['context'],'unified_delivery_completion':response['unified_completion']}if response.get('outcome')=='batch-complete'else response['context']
    need(response['kind']=='workshop-worker-result-v1' and ((response['outcome']=='complete'and isinstance(response.get('completion'),dict))or(response['outcome']=='batch-complete'and isinstance(response.get('unified_completion'),dict))) and response['task_id']==task['id'] and response['attempt_id']==attempt.name and expected_context==context,'browser-predecessor-complete-response')
    exited_at=datetime.fromisoformat(exited['exited_at'].replace('Z','+00:00'));need(exited_at.tzinfo is not None and start<=exited_at<=end,'browser-predecessor-exit-clock')
    return selected

def completed_browser_predecessor(config,current_process,*,completed_before=None):
    import sqlite3
    completed_before=completed_before or now();cutoff=datetime.fromisoformat(completed_before.replace('Z','+00:00'));need(cutoff.tzinfo is not None,'browser-predecessor-cutoff-aware')
    root=Path(config['project']).resolve()/'runtime/standalone-workshop-director';db=root/'queue.sqlite3'
    need(db.is_file() and not db.is_symlink(),'browser-predecessor-canonical-queue')
    try:connection=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    except sqlite3.Error as exc:raise ValueError('browser-predecessor-queue-read-failed:'+type(exc).__name__) from exc
    connection.row_factory=sqlite3.Row
    try:
        connection.execute('BEGIN')
        rows=connection.execute("SELECT * FROM tasks WHERE state='complete'").fetchall()
        compatible=[]
        for row in rows:
            task=dict(row)
            for key in ('context','outer','payload'):
                if isinstance(task.get(key),str):task[key]=json.loads(task[key])
            if completed_task_browser_scope(task,current_process)is None:continue
            outer=task.get('outer') or {};end=datetime.fromisoformat(outer['ended_at'].replace('Z','+00:00'));need(end.tzinfo is not None,'browser-predecessor-completed-clock')
            need(end<cutoff,'browser-predecessor-after-task-start');compatible.append((end,task))
        result={'kind':'completed-task-browser-predecessor-v1','scheduler_root':str(root),'process':current_process,'same_process_completed_count':len(compatible),'selected':None,'completed_before':completed_before}
        if compatible:
            latest=max(x[0] for x in compatible);matches=[task for ended,task in compatible if ended==latest];need(len(matches)==1,'browser-predecessor-latest-ambiguous');task=matches[0];attempt=Path(task['active_attempt'])
            result['selected']={'task':task,'task_sha256':digest(task),'request':ref(attempt/'request.json'),'exit':ref(attempt/'exit.json'),'response':ref(attempt/'response.json')}
        validate_completed_browser_predecessor(result,current_process)
        return result
    except sqlite3.Error as exc:raise ValueError('browser-predecessor-queue-read-failed:'+type(exc).__name__) from exc
    finally:connection.close()

def parked_company_tab(inventory,tab_id,groupids):
    """The company's own tab, parked on some other page of the merchant app.

    B61: three flows share one entry page and a tab is reused per company, so a
    finished task very often leaves its tab on a notice drawer, an export-records
    list or a violation detail page. Such a tab is still the right start point -
    the bridge walks back through the one sidebar entry by itself - but it is not
    an entry-page candidate, and demanding one deadlocked the whole day: no other
    tab can stand in for it.
    """
    from urllib.parse import urlsplit,parse_qs
    windows=inventory.get('windows');need(inventory.get('kind')=='dom-only-browser-tab-inventory-v1' and isinstance(windows,list),'browser-tab-inventory-invalid')
    for w in windows:
        if w.get('type')!='normal':continue
        for t in w.get('tabs',[]):
            if t.get('tabId')!=tab_id or t.get('allowed')is not True:continue
            u=urlsplit(t.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
            if u.scheme!='https' or u.netloc!='life.douyin.com':return None
            groupid=q.get('groupid',[None])[0]
            if groupid not in groupids:return None
            return {'tab_id':t['tabId'],'window_id':w['windowId'],'url':t['url'],'groupid':groupid,'selection':'parked-company-tab','identity_verified':False}
    return None

def select_new_task_tab(inventory,groupids,*,predecessor=None,current_process=None,initialize_new_session=False):
    candidates=business_tab_candidates(inventory,groupids)
    prior=validate_completed_browser_predecessor(predecessor,current_process) if predecessor is not None else None
    if prior is not None:
        parked_scope=completed_task_browser_scope(prior['task'],current_process)
        need(parked_scope is not None,'completed-browser-tab-not-currently-eligible')
        matches=[x for x in candidates if x['tab_id']==parked_scope['tab_id']]
        if len(matches)==1:return {**matches[0],'selection':'latest-completed-program-same-process-tab','predecessor':predecessor}
        # The predecessor tab is this company's own tab, just not on an entry
        # page any more (B60 also drops tabs whose URL carries UI state). Accept
        # it: the bridge returns to the review entry on its own. A tab that is
        # gone, disallowed or foreign stays fatal.
        parked=parked_company_tab(inventory,parked_scope['tab_id'],groupids)
        need(parked is not None,'completed-browser-tab-not-currently-eligible')
        return {**parked,'selection':'predecessor-tab-parked-elsewhere','predecessor':predecessor}
    if len(candidates)==1:return {**candidates[0],**({'predecessor':predecessor} if predecessor is not None else {})}
    if initialize_new_session:
        need(predecessor is not None and predecessor['same_process_completed_count']==0 and predecessor['selected'] is None,'browser-new-session-no-history-required')
        focused=[w for w in inventory['windows'] if w.get('focused') is True and w.get('type')=='normal']
        need(len(focused)==1,'new-session-unique-focused-window-required')
        ids=[t['tabId'] for t in focused[0]['tabs'] if t.get('active') is True]
        matches=[x for x in candidates if x['window_id']==focused[0]['windowId'] and x['tab_id'] in ids]
        need(len(ids)==1 and len(matches)==1,'new-session-unique-focused-active-business-tab-required')
        return {**matches[0],'selection':'new-process-session-unique-focused-active-business-tab','predecessor':predecessor}
    need(False,'unique-business-tab-required')

def resolve_browser_scope(context,config,*,response_scope=None,parent=None,scan=None,tab_scan=None,predecessor_scan=None,completed_before=None):
    if context.get('reboot_continuation'):
        sys.path.insert(0,str(Path(config['project'])/'skills/violation-notifier/scripts'))
        import violation_reboot_continuation as reboot
        value=reboot.verify(context['reboot_continuation'],live_boot=boot());scope=value['effective_scope'];observed=(scan or browser_processes)();found=observed['candidates']
        need(len(found)==1 and found[0]['pid']==scope['pid'] and found[0]['process']=={k:value['effective_process'][k] for k in ('pid','started','boot')},'reboot-current-browser-process-changed')
        need(parent is not None and parent.get('reboot_continuation')==context['reboot_continuation'] and parent['order']==value['original']['order'],'reboot-original-parent-admission')
        need(context.get('browser_binding')==reboot.doc(value['original']['response'])['context']['browser_binding'] and context.get('scope')==reboot.doc(value['original']['response'])['context']['scope'],'reboot-old-binding-must-not-change')
        return {'kind':'resolved-reboot-browser-scope-v1','scope':scope,'binding':context['browser_binding'],'original_scope':context['scope'],'reboot_continuation':context['reboot_continuation'],'discovery':observed,'reason':None}
    hint=context.get('scope') or config.get('context',{})
    wanted=response_scope or hint
    evidence={'kind':'resolved-browser-scope-v1','legacy_hint':hint,'requested_scope':wanted,'scope':None,'binding':None,'reason':None}
    fresh_bootstrap=parent is None and not context.get('browser_binding') and response_scope is None
    if not fresh_bootstrap and (type(wanted.get('tab_id')) is not int or wanted['tab_id']<=0):
        evidence['reason']='public-browser-tab-required';return evidence
    try:observed=(scan or browser_processes)()
    except (OSError,subprocess.SubprocessError) as e:
        evidence.update(reason='browser-process-discovery-failed',error=type(e).__name__);return evidence
    evidence['discovery']=observed;found=observed['candidates']
    if len(found)!=1:
        evidence['reason']='unique-chrome-main-required';return evidence
    selected=found[0];need(selected['comm']==CHROME_MAIN and selected['process']['pid']==selected['pid'],'browser-process-evidence-invalid')
    binding=context.get('browser_binding')
    if fresh_bootstrap:
        try:
            order=pinned(context['order']);groupids={str(x['groupid']) for x in order['scope']['company_ranges']}
            inventory=(tab_scan or browser_tab_inventory)(config);evidence['tab_discovery']=inventory;prior=(predecessor_scan or completed_browser_predecessor)(config,selected['process'],completed_before=completed_before);evidence['predecessor']=prior;selected_tab=select_new_task_tab(inventory,groupids,predecessor=prior,current_process=selected['process'],initialize_new_session=prior['same_process_completed_count']==0)
        except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as exc:
            evidence.update(reason='fresh-browser-tab-scope-required',tab_discovery_error=str(exc));return evidence
        evidence['tab_discovery']=inventory;evidence['tab_selection']=selected_tab
        wanted={'tab_id':selected_tab['tab_id']};evidence['requested_scope']=wanted
    # Existing old parents lack a start-identity record. Never adopt a newly
    # found PID into them, even if its number happens to equal an old hint.
    if parent is not None and not binding:
        evidence['reason']='existing-parent-browser-identity-unbound';return evidence
    scope={'tab_id':wanted['tab_id'],'pid':selected['pid']}
    if binding and (binding['scope']!=scope or binding['process']!=selected['process']):
        evidence['reason']='original-browser-process-changed';return evidence
    if parent is not None and (parent.get('tab_id') not in (None,scope['tab_id']) or parent.get('pid') not in (None,scope['pid'])):
        evidence['reason']='existing-parent-browser-scope-conflict';return evidence
    evidence.update(scope=scope,binding=binding or {'kind':'task-browser-process-binding-v1','scope':scope,'comm':CHROME_MAIN,'process':selected['process'],'discovery':observed})
    if fresh_bootstrap:evidence['binding']['tab_bootstrap']={'order':context['order'],'inventory':inventory,'selection':selected_tab}
    return evidence

def fixed_director_import_dirs(project):
    # Shared policy/context proof closure for all flows; no environment logging.
    names=('workshop-director','daily-comment-stats','negative-review-complaints','violation-notifier','douyin-laike-operator','chrome-dom-export','wecom-messenger')
    dirs=[Path(project)/'skills'/name/'scripts' for name in names]
    need(all(p.is_dir()and p.resolve()==p and not any(v.is_symlink()for v in(p,*p.parents))for p in dirs),'director-fixed-import-closure-missing')
    return dirs

def modules(config):
    project=Path(config['project']).resolve()
    need(Path(config['coordinator_root']).resolve()==project/'runtime/workshop-director','canonical-coordinator-root-required')
    sys.path[:0]=[str(p)for p in fixed_director_import_dirs(project)]
    import coordinator,director
    need('dispatcher' in inspect.signature(coordinator.morning).parameters,'local-subprocess-v1-overlay-not-published')
    need(coordinator.PROJECT==project,'coordinator-project-binding')
    return coordinator,director

def complaint_report_modules(config):
    """Fixed in-process complaint report dependency closure, no child or UI.
    Both completed-before-browser and post-run reporting use this bootstrap.
    """
    project=Path(config['project']).resolve()
    dirs=[project/('skills/'+name+'/scripts')for name in ('negative-review-complaints','workshop-director','chrome-dom-export','douyin-laike-operator','wecom-messenger')]
    need(all(p.is_dir()and not p.is_symlink()and p.resolve()==p for p in dirs),'complaint-report-fixed-import-closure-missing')
    sys.path[:0]=[str(p)for p in dirs]
    import complaint_execution_orchestration as orch
    import initial_ledger_recovery as helper
    need(Path(orch.__file__).resolve()==dirs[1]/'complaint_execution_orchestration.py'and Path(helper.__file__).resolve()==dirs[0]/'initial_ledger_recovery.py','complaint-report-module-origin-conflict')
    return orch

def _snapshot_finished_body(c,d,root,task):
    paths=[root/'state.json',root/'days'/task['day']/'state.json']
    for path in paths:
        if not path.exists():continue
        state=read(path)
        if state['day']!=task['day']:continue
        found=[e for e in state['events'] if e.get('type')=='completed' and e.get('dispatch_id','').startswith(task['day']+':'+task['flow']+':')]
        if found:
            report=found[-1]['report'];d.proof(report['path'],task['flow']);r=pinned(report)
            # Existing generic live booleans are not enough: only real formal
            # parent/source/client replay may satisfy this scheduler.
            deep_parent(r)
            return {'report':report,'finished_state':ref(path)}
    return None

def snapshot_finished(c,d,root,task,*,config=None):
    if task['flow']!=FLOWS[1]:return _snapshot_finished_body(c,d,root,task)
    need(type(config)is dict and Path(config['coordinator_root']).resolve()==Path(root).resolve(),'complaint-snapshot-original-config-required')
    complaint_report_modules(config)
    from initial_ledger_recovery import window_hold_history_scope
    import execution_timing as timing
    with window_hold_history_scope(max_entries=16),timing.company_policy_command():
        return _snapshot_finished_body(c,d,root,task)

def deep_parent(report):
    flow=report['workflow']
    if report.get('kind')=='staged-unified-director-completion-v1':
        import delivery_commit
        return delivery_commit.verify_report_value(report)
    if flow==FLOWS[0]:
        import daily_execution_launcher as parent,execution_timing as timing
        rr=report['verification_parent_state'];v=pinned(rr);s,order=parent.load(Path(rr['path']),v['order'],v['archive_root'],timing.Clock());proof=parent.verify_complete(s,order,timing.Clock());need(proof==s['completion_proof'] and s['status']=='complete','daily-deep-source-client-required');need(report['parent_completion']==s['completion_ref'] and report['dispatch_id']==order['dispatch_id'],'daily-report-parent-binding')
    elif flow==FLOWS[2]:
        import role_execution_orchestration as orch
        s,order,proof=orch.replay(report['verification_parent']);need(report['source_client_proof']==proof and report['dispatch_id']==order['dispatch_id'],'violation-report-parent-binding')
    elif flow==FLOWS[1]:
        import complaint_execution_orchestration as orch
        if 'pure_completion_contract' in report:
            from . import complaint_completion_report as pure
            return pure.verify_report_value(report)
        s,order,proof=orch.replay(report['verification_parent']);need(report.get('kind')=='complaint-parent-director-completion-v1' and report['source_client_proof']==proof and (report['dispatch_id'],report['day'],report['role'],report['completed_at'])==(order['dispatch_id'],order['day'],order['role'],s['wall_ended_at']),'complaint-report-parent-binding')
    else:raise ValueError('unsupported-completion-workflow')
    return report

def _verify_completion_body(task,response,config):
    c,d=modules(config);e=response['completion'];r=pinned(e['report']);need(r['workflow']==task['flow'] and r['day']==task['day'],'completion-task-scope');d.proof(e['report']['path'],task['flow']);deep_parent(r)
    state=pinned(e['finished_state']);need(state['day']==task['day'] and any(x.get('type')=='completed' and x.get('dispatch_id')==r['dispatch_id'] and x.get('report')==e['report'] for x in state['events']),'completion-canonical-consumption-required')
    root=Path(config['coordinator_root']);allowed=[root/'state.json',root/'days'/task['day']/'state.json'];need(Path(e['finished_state']['path']) in allowed,'completion-canonical-state-required')
    return r

def _verify_completion_in_process(task,response,config):
    if task['flow']!=FLOWS[1]:return _verify_completion_body(task,response,config)
    complaint_report_modules(config)
    from initial_ledger_recovery import window_hold_history_scope
    import execution_timing as timing
    with window_hold_history_scope(max_entries=16),timing.company_policy_command():
        return _verify_completion_body(task,response,config)

def verify_completion(task,response,config):
    # Parent argv is tied to its real interpreter, never the scheduler's Python.
    project=Path(config['project']);python=project/'skills/daily-comment-stats/.venv/bin/python'
    need(project.is_absolute() and project.resolve()==project and config['python']==str(python) and python.is_file(),'completion-fixed-python-required')
    if Path(sys.executable)==python:return _verify_completion_in_process(task,response,config)
    folder=Path(task['active_attempt']);request_ref=ref(folder/'request.json');response_ref=ref(folder/'response.json');request=pinned(request_ref)
    need(pinned(response_ref)==response and request['task']['id']==task['id'] and request['attempt_id']==folder.name,'completion-original-attempt-required')
    need(all(request['task'][key]==task[key] for key in ('id','day','flow','plan_id','outer','payload')),'completion-original-task-changed')
    need(all(request['config'][key]==config[key] for key in ('project','python','coordinator_root','dispatcher')) and pinned(request['config_ref'])==request['config'],'completion-original-config-changed')
    exit_ref=ref(folder/'exit.json');helper=Path(__file__).with_name('completion_verifier.py');codes=[ref(helper),ref(Path(__file__))];report=response['completion']['report'];value=pinned(report)
    argv=[str(python),'-I','-B',str(helper),'--request',request_ref['path'],'--request-sha256',request_ref['sha256'],'--response',response_ref['path'],'--response-sha256',response_ref['sha256']]
    # Fresh pure-verification evidence, never reuse another invocation's output.
    diagnostic_root=folder/'completion-verifications'
    need(folder.is_absolute()and folder.resolve()==folder and not folder.is_symlink()and diagnostic_root.resolve()==diagnostic_root and not diagnostic_root.is_symlink()and (not diagnostic_root.exists()or diagnostic_root.is_dir()),'completion-verifier-diagnostic-canonical-directory-required')
    diagnostic=diagnostic_root/uuid.uuid4().hex
    need(not diagnostic.exists()and not diagnostic.is_symlink(),'completion-verifier-diagnostic-fresh-invocation-required')
    started=time.clock_gettime(time.CLOCK_MONOTONIC)
    intent=immutable(diagnostic/'intent.json',{'kind':'original-completion-verifier-observation-intent-v1','request':request_ref,'response':response_ref,'original_exit':exit_ref,'config':request['config_ref'],'report':report,'code_refs':codes,'argv':argv,'started_at':now(),'started_monotonic':started,'ui_used':False})
    try:
        child=subprocess.run(argv,capture_output=True,text=True)
    except BaseException as error:
        ended=time.clock_gettime(time.CLOCK_MONOTONIC)
        immutable(diagnostic/'result.json',{'kind':'original-completion-verifier-observation-result-v1','intent':intent,'natural_exit_observed':False,'returncode':None,'stdout':None,'stderr':None,'exception':{'type':type(error).__name__,'message':str(error)},'ended_at':now(),'elapsed_seconds':ended-started,'ui_used':False})
        raise
    ended=time.clock_gettime(time.CLOCK_MONOTONIC)
    immutable(diagnostic/'result.json',{'kind':'original-completion-verifier-observation-result-v1','intent':intent,'natural_exit_observed':True,'returncode':child.returncode,'stdout':child.stdout,'stderr':child.stderr,'ended_at':now(),'elapsed_seconds':ended-started,'ui_used':False})
    need(child.returncode==0 and not child.stderr,'completion-verifier-child-failed:'+str(child.returncode))
    checked=json.loads(child.stdout)
    need(checked=={'kind':'original-config-python-completion-verified-v1','request':request_ref,'response':response_ref,'original_exit':exit_ref,'report':report,'report_digest':digest(value),'code_refs':codes,'ui_used':False},'completion-verifier-child-proof-invalid')
    need(ref(folder/'request.json')==request_ref and ref(folder/'response.json')==response_ref and ref(folder/'exit.json')==exit_ref and pinned(request['config_ref'])==request['config'] and pinned(report)==value and [ref(Path(r['path'])) for r in codes]==codes,'completion-verifier-input-or-code-changed')
    return value

def expected_company_search_wait(job,current,tab_id):
    """One specifically known positive wait, never success or an input grant."""
    if not(current.get('state')=='running' and current.get('phase')=='chooseCompany' and current.get('waiting_for')=='company-search-results' and not current.get('last_error')):return False
    try:
        need(current.get('backend')==job.get('backend')=='local-dom-bridge' and current.get('identity_contract')==job.get('identity_contract')=='merchant-v2' and job.get('action')in ('acquire','return-company') and str(current['tab_id'])==str(tab_id),'company-wait-original-job')
        need(all(current[k]==job[k]for k in ('work_order_id','company'))and str(current['groupid'])==str(job['groupid'])and current['date_range']==job.get('date_range',{}),'company-wait-original-job')
        fingerprint=hashlib.sha256(json.dumps({k:job.get(k)for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        need(current['fingerprint']==fingerprint and not any(current.get(k)for k in ('exportPending','downloadPending','result','attempts','submitted_at')),'company-wait-business-intent')
        calls=current['calls'];need(len(calls)>=2 and all(c.get('state')=='confirmed'for c in calls)and not any(c.get('phase')in ('chooseCompany','confirmSwitch')for c in calls),'company-wait-confirmed-only')
        search=calls[-1];cmd=search['command'];filtered=search['result']['filtered'];need(search['phase']=='searchCompany'and search['key']==str(current['revision']-1)+':searchCompany'and cmd.get('op')=='filter'and cmd.get('kind')=='filter'and cmd.get('tabId')==current['tab_id']and cmd.get('value')==job['company']and filtered.get('selector')==cmd.get('locator',{}).get('value')and filtered.get('attributes',{}).get('value')==job['company'],'company-wait-search-binding')
        context=calls[-2];clicked=context.get('result',{}).get('clicked',{});cc=context.get('command',{});need(context.get('phase')=='context'and cc.get('op')=='click'and cc.get('kind')=='navigation'and cc.get('tabId')==current['tab_id']and clicked.get('selector')==cc.get('locator',{}).get('value'),'company-wait-context-binding')
        initial=str(current['initial_groupid']);known=job['known_company_identities'];need(initial!=str(job['groupid'])and current['entry_groupid']==initial and current['entry_identity']==known[initial]and current['provider_baseline']==known[initial]['provider']==job['provider_baseline']and job['identity_baseline']==known[str(job['groupid'])],'company-wait-identity-binding')
        started=datetime.fromisoformat(current['company_search_wait_started']);updated=datetime.fromisoformat(current['updated_at']);present=datetime.now(timezone.utc);searched=datetime.fromisoformat(search['at']);need(all(t.utcoffset()is not None for t in (started,updated,present,searched))and searched<=started<=updated<=present and 0<=(present-started).total_seconds()<=60,'company-wait-budget')
        import importlib.util
        path=Path(__file__).resolve().parents[3]/'skills/douyin-laike-operator/scripts/dom_evidence.py';spec=importlib.util.spec_from_file_location('operator_wait_dom_evidence',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        tree=pinned(current['last_tree']);module.identity(tree,current['entry_identity']);ns=list(module.nodes(tree));field=module.unique([n for n in ns if n.get('role')=='textbox'and n.get('placeholder')=='搜索商户'],'company-wait-search-field')
        need(field.get('attributes',{}).get('value')==job['company']and not any(n.get('name')==job['company']and not any(c.get('name')==job['company']for c in n.get('children',[]))for n in ns),'company-wait-results-changed')
        return True
    except (ValueError,KeyError,TypeError,OSError):return False

def command_output(raw,argv,label):
    # Only the fixed bridge operator emits JSONL. Parent CLIs emit one JSON.
    if label!='parent-operator':return json.loads(raw)
    need(len(argv)==8 and Path(argv[1]).name=='bridge-workflow.py' and argv[2]=='--work-order' and argv[4]=='--tab-id' and argv[6]=='--steps' and argv[7]=='25','operator-jsonl-command-contract')
    job=pinned(ref(Path(argv[3])));journal=Path(job['workflow_path']);rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
    need(1<=len(rows)<=25,'operator-jsonl-row-count')
    for i,row in enumerate(rows):
        need(type(row) is dict and set(row)=={'state','phase','waiting_for','journal','step'},'operator-jsonl-fields')
        need(row['journal']==str(journal) and row['state'] in ('running','complete','hold') and type(row['phase']) is str and type(row['step']) is int,'operator-jsonl-scope')
        need(row['step']==(0 if len(rows)==1 and row['step']==0 else i+1),'operator-jsonl-step-sequence')
    current=read(journal);last=rows[-1]
    need(all(last[k]==current.get(k) for k in ('state','phase','waiting_for')),'operator-jsonl-journal-mismatch')
    need(last['step']>0 or last['state']=='complete' or expected_company_search_wait(job,current,argv[5]),'operator-no-progress-requires-reconciliation:'+str((current.get('last_error') or {}).get('code') or last.get('waiting_for') or last['phase']))
    return last

def parent_command_environment(argv,folder,label):
    # Fixed canonical launchers need the same shared proof dependencies in a
    # fresh child: sys.path changes in modules() do not cross Popen boundaries.
    project=Path(__file__).resolve().parents[3];scripts=project/'skills/workshop-director/scripts'
    verbs={'daily_execution_launcher.py':('start','advance','notify','status','repair-zero-init'),
           'complaint_execution_launcher.py':('start','run','accept','status'),
           'role_execution_launcher.py':('start','run','accept','status')}
    match=next((name for name in verbs if len(argv)>=2 and argv[1]==str(scripts/name)),None)
    if match is None:
        if label!='parent-operator':return None
        child_env=os.environ.copy()
        child_env['BRIDGE_REQUEST_PERFORMANCE_DIR']=str(Path(folder).resolve()/'bridge-timings')
        return child_env
    need(len(argv)>=3 and argv[2]in verbs[match],'parent-bootstrap-verb-required')
    launcher=scripts/match
    need(launcher.is_file()and launcher.resolve()==launcher and not any(p.is_symlink()for p in(launcher,*launcher.parents)),'parent-canonical-launcher-required')
    dirs=fixed_director_import_dirs(project)
    child_env=os.environ.copy();inherited=child_env.get('PYTHONPATH')
    child_env['PYTHONPATH']=os.pathsep.join([str(p)for p in dirs]+([inherited]if inherited else []))
    return child_env

def run_command(argv,folder,label):
    # Every deterministic command has its own intent, child PID and natural exit.
    # If process death interrupts this function, the outer attempt is UNKNOWN.
    folder=Path(folder);need(not (folder/(label+'-intent.json')).exists(),'command-intent-already-exists-no-replay')
    started=time.clock_gettime(time.CLOCK_MONOTONIC)
    immutable(folder/(label+'-intent.json'),{'argv':argv,'at':now(),'started_monotonic':started})
    options={}
    child_env=parent_command_environment(argv,folder,label)
    if child_env is not None:options['env']=child_env
    with (folder/(label+'-stdout.log')).open('wb') as out,(folder/(label+'-stderr.log')).open('wb') as err:
        proc=subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,**options);immutable(folder/(label+'-process.json'),{'pid':proc.pid,'process':identity(proc.pid),'at':now()});rc=proc.wait()
        ended=time.clock_gettime(time.CLOCK_MONOTONIC)
    receipt={'argv':argv,'returncode':rc,'stdout':ref(folder/(label+'-stdout.log')),'stderr':ref(folder/(label+'-stderr.log')),'exited_at':now(),'timing':{'clock':'CLOCK_MONOTONIC','started_monotonic':started,'exited_monotonic':ended,'elapsed_seconds':ended-started}};immutable(folder/(label+'-exit.json'),receipt);need(rc==0,'original-command-failed:'+label)
    return command_output((folder/(label+'-stdout.log')).read_bytes(),argv,label)

def dispatch(request,context,folder,c,d,config):
    task=request['task'];root=Path(config['coordinator_root']);done=snapshot_finished(c,d,root,task,config=config)
    if done:return context,done
    # Complaint must not be issued without its actual published full parent.
    if task['flow']==FLOWS[1] and not (Path(config['project'])/'skills/workshop-director/scripts/complaint_execution_launcher.py').is_file():return {**context,'pending_dependency':'complaint-full-parent-not-published'},None
    # Cursor coverage alone is NOT a completion proof. Do not even issue a new
    # empty order: original formal same-day evidence was checked above; absent
    # that, the business no-op proof contract is an explicit publishing blocker.
    ledgers=[ref(path) for flow,company,path in c.fixed_ledgers(config['project']) if flow==task['flow']]
    values=[]
    for reference in ledgers:
        value=pinned(reference);values.extend(value['companies'].values() if 'companies' in value else [value])
    if values and all(v.get('next_start','')>=task['day'] for v in values):return {**context,'pending_dependency':'covered-cursor-without-formal-same-day-or-empty-scope-proof','pending_ledgers':ledgers},None
    need(not context.get('offer'),'existing-offer-must-not-be-reissued')
    local_intent=immutable(Path(folder)/'coordinator-call-intent.json',{'kind':'local-coordinator-call-intent-v1','request':ref(Path(folder)/'request.json'),'day':task['day'],'flow':task['flow'],'at':now()})
    offer=c.morning(root,config['acceptance'],dispatcher='local-subprocess-v1',requested_day=task['day'],collection_contract=task['payload'].get('collection_contract'))
    immutable(Path(folder)/'coordinator-call-result.json',{'intent':local_intent,'offer':offer})
    need(offer.get('active_day')==task['day'] and offer.get('workflow')==task['flow'] and offer.get('action')=='dispatch' and offer.get('tool')=='local-subprocess-v1','canonical-coordinator-not-new-local-offer-inspect-original')
    offered=immutable(Path(folder)/'offer.json',offer);intent=immutable(Path(folder)/'coordinator-dispatch-intent.json',{'kind':'local-coordinator-dispatch-intent-v1','request':ref(Path(folder)/'request.json'),'dispatch_id':offer['dispatch_id'],'offer':offered,'at':now()})
    ack=immutable(Path(folder)/'local-spawn-ack.json',{'kind':'local-subprocess-spawn-ack-v1','dispatcher_protocol':'local-subprocess-v1','dispatch_id':offer['dispatch_id'],'day':task['day'],'pid':os.getpid(),'process':identity(os.getpid()),'request':ref(Path(folder)/'request.json'),'attempt_id':request['attempt_id'],'offer':offered,'dispatch_intent':intent,'at':now()})
    c.command(root,'ack',dispatch_id=offer['dispatch_id'],tool_receipt=json.dumps(ack),dispatcher='local-subprocess-v1');immutable(Path(folder)/'coordinator-ack-result.json',{'dispatch_id':offer['dispatch_id'],'ack':ack,'state':ref(root/'state.json')})
    return {**{k:v for k,v in context.items() if k!='pending_dependency'},'offer':offered,'stage':'start'},None

def result(request,context,outcome,**kwargs):return {'kind':'workshop-worker-result-v1','task_id':request['task']['id'],'attempt_id':request['attempt_id'],'context':context,'outcome':outcome,**kwargs}
def waiting(request,context,folder,reason,details):
    handoff=immutable(Path(folder)/'handoff.json',{'kind':'workshop-handoff-v1','task_id':request['task']['id'],'reason':reason,'details':details,'original_outer':request['task']['outer'],'response_kind':'workshop-handoff-response-v1','no_automatic_replay':True})
    return result(request,context,'waiting',handoff=handoff)

def resume_switch_transport(context,config,folder):
    """One durable read-only helper call; never reruns a confirmed switch."""
    job_ref=context['operator']['work_order'];job=pinned(job_ref);path=Path(job['workflow_path'])
    need(not path.is_symlink(),'switch-read-resume-workflow-symlink')
    if not path.exists():return False
    state=read(path)
    return_error=state.get('last_error') or {}
    known_return_error=(job.get('action')=='return-company' and return_error.get('code')==return_error.get('message')=='read-recovery-navigation-only-contract-required')
    if not(state.get('phase')=='verifySwitch' and (state.get('waiting_for')=='company-switch-readonly-scope' or known_return_error)):return False
    import importlib.util
    helper=Path(config['project'])/'skills/douyin-laike-operator/scripts/switch_read_recovery.py'
    need(helper.is_file() and not helper.is_symlink(),'switch-read-resume-helper-origin');spec=importlib.util.spec_from_file_location('standalone_switch_transport_read_resume',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);current=ref(path);proof=module.readonly_resume_contract(job_ref['path'],current['sha256']);immutable(Path(folder)/'switch-read-resume-contract.json',proof)
    argv=[config['python'],str(helper),'--work-order',job_ref['path'],'--original-sha256',current['sha256']];out=run_command(argv,folder,'operator-switch-read-resume');need(out.get('state')=='reconciled','switch-read-resume-exhausted:'+str(out.get('error','unknown')));new=pinned(out['journal']);[pinned(r) for r in proof['historical_refs']];module.verify_recovered(new,out['proof']);need(new['calls']==state['calls'] and new['phase']=='accountAfterSwitch','switch-read-resume-original-chain');return True

def daily_notification_snapshot(order,project):
    """Deep existing outbox inspection only; no sender prepare/run or UI read."""
    sys.path.insert(0,str(Path(project)/'skills/daily-comment-stats/scripts'))
    import notification_backlog as backlog
    root=Path(order['path']).parent.parent/'daily-executions'/Path(order['path']).stem;path=root/'state.json'
    if not path.exists():return None
    need(not path.is_symlink(),'daily-notification-role-symlink');role_ref=ref(path);role=pinned(role_ref);need(role.get('order')==order,'daily-notification-order-binding')
    if role.get('phase')!='notification-pending':return None
    queue_ref=role.get('queue');need(type(queue_ref) is dict,'daily-notification-queue-required');pinned(queue_ref);queue=Path(queue_ref['path']);need(queue.is_relative_to(root/'outbox') and queue.name=='outbox.json','daily-notification-queue-origin')
    inspection=backlog.inspect(queue,False);need(ref(path)==role_ref and ref(queue)==queue_ref,'daily-notification-concurrent-change')
    return inspection

def known_initial_constructor_failure(context,config,folder,directory,original,state,argv):
    """Only an immutable immediately preceding natural pre-input failure qualifies."""
    request=pinned(read(Path(folder)/'intent.json')['request']);task=request['task'];root=Path(request['root']);previous=Path(task['active_attempt'])
    need(previous.parent==root/'attempts' and previous.name==task['id']+'-'+str(task['attempt']) and previous!=Path(folder) and root==Path(config['project'])/'runtime/standalone-workshop-director','initial-constructor-prior-attempt')
    prior=pinned(read(previous/'intent.json')['request']);need(prior['attempt_id']==previous.name and prior['task']['id']==task['id'] and prior['context']['order']==context['order'],'initial-constructor-prior-order')
    old_intent=pinned(ref(directory/'adapter-intent.json'));need(old_intent.get('kind')=='initial-locate-sender-readonly-resume-intent-v1' and old_intent.get('job')==original and old_intent.get('fingerprint')==state['fingerprint'] and old_intent.get('order')==context['order'] and old_intent.get('ui_input_used') is False,'initial-constructor-original-intent')
    need(pinned({'path':str(directory/'original.json'),'sha256':original['sha256']})==state and pinned(original)==state,'initial-constructor-original-changed')
    need(not any(p.exists() or p.is_symlink() for p in (directory/'fresh.json',directory/'adapter-result.json')),'initial-constructor-fresh-or-result-present')
    exit_path=previous/'sender-initial-locate-resume-exit.json';exit=read(exit_path);intent=read(previous/'sender-initial-locate-resume-intent.json');worker_exit=read(previous/'exit.json')
    need(worker_exit.get('request')==ref(previous/'request.json'),'initial-constructor-worker-request')
    if worker_exit.get('response'):
        response=pinned(worker_exit['response']);need(response.get('outcome')=='failed' and response.get('error')=='original-command-failed:sender-initial-locate-resume','initial-constructor-natural-worker-failure')
    else:
        need(worker_exit.get('returncode')==1,'initial-constructor-worker-exit-required')
        for key in ('stdout','stderr'):need(worker_exit[key]['path']==str(previous/(key+'.log')) and ref(previous/(key+'.log'))==worker_exit[key],'initial-constructor-worker-log-binding')
        outer_error=(previous/'stderr.log').read_text();need((previous/'stdout.log').read_bytes()==b'' and outer_error.endswith('ValueError: original-command-failed:sender-initial-locate-resume\n') and str(Path(config['project'])/'packages/workshop-director/workshop_director/local_worker.py') in outer_error and 'in resume_initial_sender' in outer_error and 'in run_command' in outer_error,'initial-constructor-known-outer-exit')
    need(exit.get('argv')==intent.get('argv')==argv and exit.get('returncode') in (1,2) and exit['timing']['started_monotonic']==intent['started_monotonic'] and exit['timing']['exited_monotonic']>=intent['started_monotonic'],'initial-constructor-exit-binding')
    for key in ('stdout','stderr'):
        expected=previous/('sender-initial-locate-resume-'+key+'.log');need(exit[key]['path']==str(expected) and not expected.is_symlink() and ref(expected)==exit[key],'initial-constructor-log-binding')
    if exit.get('returncode')==2:
        # Exact reviewed same-Host diagnostic pass; sender and adapter intent
        # were deliberately left untouched, never an unknown UI action.
        summary_ref={'path':str(Path(config['project'])/'work/2026-10-24/full-three-flow-run-20261024/initial-locate-same-host-diagnostic-summary.json'),'sha256':'b0acdf1d10971970d9bfa9cdb1adaecfbae3471544b6977b5e5470652ab26203'}
        summary=pinned(summary_ref);diagnostic=pinned(summary['diagnostic'])
        need(summary.get('task')==task['id'] and summary.get('attempt')==task['attempt'] and summary.get('worker_exit')==ref(previous/'exit.json') and summary.get('sender_unchanged')==original and summary.get('no_inputs') is True,'initial-constructor-diagnostic-original-binding')
        need(summary['diagnostic']['path'].startswith(str(previous/'wecom-performance')+'/') and summary['diagnostic']['sha256']=='f95cff14d16f7caea3d4a0c7704df035b97e77e88306a77b443479c40bc75491','initial-constructor-diagnostic-reference')
        need(diagnostic.get('kind')=='same-host-initial-locate-failure-diagnostic-v1' and diagnostic.get('sender')==original and diagnostic.get('sender_fingerprint')==state['fingerprint'] and diagnostic.get('new_inputs')==0 and diagnostic.get('original_error_preserved') is True and diagnostic.get('diagnostic_returncode')==0 and diagnostic.get('diagnostic',{}).get('UI_input_used') is False,'initial-constructor-diagnostic-no-input')
        need(json.loads(Path(exit['stdout']['path']).read_text())=={'ok':False,'error':'app-not-running-or-ambiguous'} and Path(exit['stderr']['path']).read_bytes()==b'','initial-constructor-known-locate-only')
        need(ref(Path(original['path']))==original,'initial-constructor-current-changed')
        return {'kind':'verified-initial-locate-empty-shell-diagnostic-failure-v1','original_intent':ref(directory/'adapter-intent.json'),'original':original,'prior_request':ref(previous/'request.json'),'exit':ref(exit_path),'worker_exit':ref(previous/'exit.json'),'stdout':exit['stdout'],'stderr':exit['stderr'],'diagnostic_summary':summary_ref,'diagnostic':summary['diagnostic'],'ui_input_used':False}
    stderr=Path(exit['stderr']['path']).read_text();need(Path(exit['stdout']['path']).read_bytes()==b'' and stderr.startswith('Traceback (most recent call last):') and stderr.endswith("TypeError: 'NoneType' object is not iterable\n") and 'in resume_before_send' in stderr and 'in __init__' in stderr and 'in read' in stderr and str(Path(config['project'])/'skills/wecom-messenger/scripts/main_window.py') in stderr and "for c in native.scoped_array(e,'AXChildren',role in STRUCTURAL)" in stderr,'initial-constructor-known-none-children-only')
    need(ref(Path(original['path']))==original,'initial-constructor-current-changed')
    return {'kind':'verified-initial-locate-none-children-failure-v1','original_intent':ref(directory/'adapter-intent.json'),'original':original,'prior_request':ref(previous/'request.json'),'exit':ref(exit_path),'worker_exit':ref(previous/'exit.json'),'stdout':exit['stdout'],'stderr':exit['stderr'],'ui_input_used':False}

def known_startup_context_failure(context,config,folder,directory,original,state,argv):
    """One fixed natural pre-input startup failure; never an unknown search/send."""
    failure_ref={'path':str(Path(config['project'])/'work/2026-10-24/full-three-flow-run-20261024/daily29-startup-context-preinput-failure.json'),'sha256':'1f744a5d09fc4874db9a96d9b6500b37e8418f6b546fbcd0639796e2df00555c'}
    failure=pinned(failure_ref);request=pinned(read(Path(folder)/'intent.json')['request']);task=request['task'];previous=Path(task['active_attempt']);root=Path(request['root'])
    need(task['id']==failure['task'] and task['attempt']==failure['attempt']==29 and previous==root/'attempts'/(task['id']+'-29') and previous!=Path(folder) and root==Path(config['project'])/'runtime/standalone-workshop-director','startup-context-prior-attempt')
    for item in list(failure['natural_refs'].values())+failure['original_adapter_intents_and_archives']:
        need(not Path(item['path']).is_symlink() and ref(item['path'])==item,'startup-context-evidence-bytes-changed')
    prior=pinned(failure['natural_refs']['request.json']);need(prior['attempt_id']==previous.name and prior['task']['id']==task['id'] and prior['context']['order']==context['order'],'startup-context-prior-order')
    need(failure['sender_unchanged']==original and pinned(original)==state and failure['no_input_intent'] is True and failure['original_sender_bytes_preserved'] is True and failure['new_fresh_snapshot_present'] is False,'startup-context-original-binding')
    exit=pinned(failure['natural_refs']['sender-initial-locate-resume-exit.json']);intent=pinned(failure['natural_refs']['sender-initial-locate-resume-intent.json'])
    need(exit.get('argv')==intent.get('argv')==argv and exit.get('returncode')==2 and exit['timing']['started_monotonic']==intent['started_monotonic'] and exit['timing']['exited_monotonic']>=intent['started_monotonic'],'startup-context-natural-exit')
    need(json.loads(Path(exit['stdout']['path']).read_text())=={'ok':False,'error':'startup-not-empty-chat-shell'} and Path(exit['stderr']['path']).read_bytes()==b'','startup-context-known-preinput-only')
    known=directory/'known-constructor-recovery-v1';known_ref=ref(known/'adapter-intent.json');need(known_ref in failure['original_adapter_intents_and_archives'],'startup-context-known-intent-reference')
    old=pinned(known_ref);need(old.get('kind')=='initial-locate-sender-readonly-resume-intent-v1' and old.get('job')==original and old.get('fingerprint')==state['fingerprint'] and old.get('order')==context['order'] and old.get('ui_input_used') is False,'startup-context-known-intent-binding')
    need(pinned({'path':str(directory/'original.json'),'sha256':original['sha256']})==state,'startup-context-original-archive')
    need(not any(x.exists() or x.is_symlink() for parent in (directory,known) for x in (parent/'fresh.json',parent/'adapter-result.json')),'startup-context-fresh-or-result-present')
    return {'kind':'verified-startup-context-preinput-failure-v1','failure':failure_ref,'original_intent':known_ref,'original':original,'prior_request':failure['natural_refs']['request.json'],'exit':failure['natural_refs']['sender-initial-locate-resume-exit.json'],'ui_input_used':False}

def resume_initial_sender(context,config,folder,inspection):
    current=inspection.get('next') or {}
    if current.get('action')!='supervisor-safe-resume':return False
    sys.path.insert(0,str(Path(config['project'])/'skills/daily-comment-stats/scripts'));import notification_backlog as backlog
    path=Path(current['job_path']);need(path.parent==Path(config['project'])/'runtime/wecom-messenger' and not path.is_symlink(),'initial-sender-canonical-path');original={'path':str(path),'sha256':current['job_sha256']};state=pinned(original)
    if not backlog.messenger.initial_locate_failure(state):return False
    need(path.stem==hashlib.sha256(state['job']['key'].encode()).hexdigest()[:24] and state['job']['scope']=='test' and state['job']['target']==backlog.pn.TARGET,'initial-sender-original-binding')
    argv=[config['python'],str(Path(config['project'])/'skills/wecom-messenger/scripts/messenger.py'),'resume','--job',str(path)]
    directory=path.parent/'.initial-locate-resume'/path.stem/original['sha256'];intent=directory/'adapter-intent.json'
    if intent.exists():
        if (directory/'known-constructor-recovery-v1'/'adapter-intent.json').exists():
            evidence=known_startup_context_failure(context,config,folder,directory,original,state,argv);directory=directory/'known-constructor-recovery-v1'/'known-startup-preinput-recovery-v1'
        else:
            evidence=known_initial_constructor_failure(context,config,folder,directory,original,state,argv);directory=directory/'known-constructor-recovery-v1'
        intent=directory/'adapter-intent.json';need(not intent.exists(),'initial-sender-resume-already-issued-no-replay');immutable(directory/'original-failure.json',evidence);immutable(directory/'failed-adapter-intent.json',pinned(evidence['original_intent']))
    need(not intent.exists(),'initial-sender-resume-already-issued-no-replay');immutable(intent,{'kind':'initial-locate-sender-readonly-resume-intent-v1','job':original,'fingerprint':state['fingerprint'],'order':context['order'],'at':now(),'ui_input_used':False})
    output=run_command(argv,folder,'sender-initial-locate-resume');new=read(path);binding=new.get('initial_process_binding',{})
    need(output.get('job_path')==str(path) and output.get('status')=='running' and output.get('phase')=='locate' and new['job']==state['job'] and new['fingerprint']==state['fingerprint'] and new.get('status')=='running' and new.get('phase')=='locate' and binding.get('kind')=='verified-initial-locate-process-binding-v1' and binding.get('ui_input_used') is False and binding.get('original',{}).get('sha256')==original['sha256'] and type(new.get('pid')) is int and new['pid']>0,'initial-sender-resume-result-invalid');pinned(binding['original']);pinned(binding['fresh']);immutable(directory/'adapter-result.json',{'job':ref(path),'binding':binding,'at':now()});return True

def resume_pre_paste_focus_sender(context,config,folder,inspection):
    current=inspection.get('next') or {}
    if current.get('action')!='supervisor-safe-resume':return False
    path=Path(current['job_path']);original={'path':str(path),'sha256':current['job_sha256']};state=pinned(original)
    if not (state.get('status')=='failed' and state.get('phase')=='stage' and state.get('error') in ('composer-focus-or-frontmost-unverified','focus-main-window-restore-unverified') and type(state.get('pid')) is int and state['pid']>0):return False
    need(path.parent==Path(config['project'])/'runtime/wecom-messenger' and path.stem==hashlib.sha256(state['job']['key'].encode()).hexdigest()[:24] and state['job']['scope']=='test' and state['job']['kind']=='group' and state['job']['target']=='测试群请忽略','prepaste-focus-original-scope')
    events=state.get('events',[]);need(events and events[-1].get('stage')=='stopped' and events[-1].get('error')==state['error'] and any(e.get('stage')=='recipient-verified' and e.get('name')==state['job']['target'] and e.get('kind')=='group' for e in events) and not any(any(w in str(e.get('stage','')).lower() for w in ('intent','paste','return','choice','confirmed')) for e in events),'prepaste-focus-input-evidence')
    need(not any(v and any(w in k.lower() for w in ('intent','paste','return','choice','receipt')) for k,v in state.items()) and not any(state.get(k) for k in ('sent','ui_confirmed','delivery_confirmed','image_proof','automated_send','user_sent')),'prepaste-focus-input-forbidden')
    directory=path.parent/'.prepaste-focus-resume'/path.stem/original['sha256'];intent=directory/'intent.json';need(not intent.exists(),'prepaste-focus-resume-issued-no-replay');directory.mkdir(parents=True,exist_ok=True);raw=path.read_bytes();need(ref(path)==original,'prepaste-focus-original-changed');archive=directory/'original.json'
    need(directory.resolve()==directory and not archive.is_symlink(),'prepaste-focus-archive-path')
    try:
        with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except FileExistsError:need(archive.read_bytes()==raw,'prepaste-focus-archive-changed')
    immutable(intent,{'kind':'prepaste-focus-readonly-resume-intent-v1','original':ref(archive),'job':original,'order':context['order'],'at':now(),'ui_input_used':False})
    argv=[config['python'],str(Path(config['project'])/'skills/wecom-messenger/scripts/messenger.py'),'resume','--job',str(path)];output=run_command(argv,folder,'sender-prepaste-focus-resume');new=read(path)
    need(output.get('job_path')==str(path) and output.get('status')=='running' and output.get('phase')=='locate' and new.get('job')==state['job'] and new.get('fingerprint')==state['fingerprint'] and new.get('pid')==state['pid'] and new.get('status')=='running' and new.get('phase')=='locate' and not new.get('error') and new.get('events',[])[:-1]==events and new['events'][-1].get('stage')=='resumed-before-send','prepaste-focus-resume-result-invalid');immutable(directory/'result.json',{'job':ref(path),'original':ref(archive),'at':now()});return True

def daily_notification_progress(child,context,folder):
    """Only actual sender outcome/phase changes count, never elapsed/call count."""
    if child.get('phase')!='notification-pending':return None
    state=child.get('notification');need(type(state) is dict and state.get('complete') is False and type(state.get('items')) is list and state['items'],'daily-notification-diagnostic-required')
    states=state['items'];need(all(type(x) is dict and x.get('key') and x.get('job_path') and x.get('action') for x in states),'daily-notification-diagnostic-invalid')
    next_item=next((x for x in states if x['action']!='skip-complete'),None);need(next_item and state.get('next')==next_item,'daily-notification-next-invalid')
    signature=[{k:x.get(k) for k in ('key','action','status','phase','ui_confirmed')} for x in states]
    previous=context.get('notification_progress');audit=immutable(Path(folder)/('daily-notification-progress-'+str(len(list(Path(folder).glob('daily-notification-progress-*.json'))))+'.json'),{'kind':'daily-notification-progress-check-v1','notification':state,'previous':previous,'current':signature,'timestamp_is_not_progress':True})
    context['notification_progress']=signature
    if next_item['action'] not in ('prepare','advance','verify-readonly'):
        return {'error':'daily-notification-blocked:'+next_item['action'],'evidence':audit,'sender':next_item}
    if previous==signature:return {'error':'daily-notification-no-semantic-progress','evidence':audit,'sender':next_item}
    return None

def reviewed_completion_scope(parent_path):
    from . import complaint_completion_report as pure
    if not pure.RELEASE.is_file():return False
    release=pinned(ref(pure.RELEASE));need(release.get('kind')=='supervisor-reviewed-source-release-v1','complaint-report-release-kind')
    return release.get('completion_report_recovery',{}).get('parent',{}).get('path')==str(parent_path)

def completed_complaint_report(request,context,folder,parent_path,coordinator,root,offer):
    """Pure completed-parent harvest before any browser or parent invocation."""
    from . import complaint_completion_report as pure
    parent_ref=ref(parent_path);release_ref=ref(pure.RELEASE);pins,original=pure.original_inputs(release_ref,parent_ref)
    need(all(request['task'][k]==original['task'][k] for k in ('id','day','flow','plan_id','outer','payload')) and context['order']==original['context']['order'],'complaint-report-original-task-required')
    need(all(request['config'][k]==original['config'][k] for k in ('project','python','coordinator_root','dispatcher')) and pinned(request['config_ref'])==request['config'],'complaint-report-current-config-required')
    base=parent_path.parent/'.pure-completion-report'/release_ref['sha256'];base.mkdir(parents=True,exist_ok=True);intent=base/'finish-intent.json'
    need(not intent.exists(),'complaint-report-finish-issued-no-replay')
    report_path=base/'completion-report.json'
    if report_path.exists():
        report_ref=ref(report_path);pure.verify_report(report_path,read(root/'state.json'))
    else:
        argv=[original['config']['python'],'-I','-B',str(pure.HELPER),'--parent',parent_ref['path'],'--parent-sha256',parent_ref['sha256'],'--director',str(root/'state.json'),'--director-sha256',ref(root/'state.json')['sha256'],'--release',release_ref['path'],'--release-sha256',release_ref['sha256'],'--out',str(report_path)]
        output=run_command(argv,folder,'parent-completion-report')
        need(output=={'kind':'reviewed-complaint-completion-report-produced-v1','report':ref(report_path),'release':release_ref,'parent':parent_ref,'ui_used':False},'complaint-report-helper-output')
        report_ref=output['report']
    need(ref(parent_path)==parent_ref and ref(pure.RELEASE)==release_ref,'complaint-report-original-or-release-changed')
    immutable(intent,{'kind':'reviewed-completed-complaint-finish-intent-v1','request':ref(Path(folder)/'request.json'),'original_request':pins['request'],'parent':parent_ref,'report':report_ref,'dispatch_id':offer['dispatch_id'],'at':now()})
    coordinator.command(root,'finish',dispatch_id=offer['dispatch_id'],report=report_ref['path'])
    finished=ref(root/'state.json');immutable(base/'finish-result.json',{'intent':ref(intent),'report':report_ref,'finished_state':finished,'at':now()})
    return result(request,context,'complete',completion={'report':report_ref,'finished_state':finished})


def harvest_complaint_report(request,context,folder,parent_path,coordinator,root,offer):
    """One pure-history memo lifetime for report construction and its replay.
    Live marker/lease/artifact guards stay in their original functions; writes
    still invalidate observed dependencies, and the scope always clears on exit.
    """
    orch=complaint_report_modules(request['config'])
    from initial_ledger_recovery import window_hold_history_scope
    import execution_timing as timing
    with window_hold_history_scope(max_entries=16),timing.company_policy_command():
        report=orch.report(ref(parent_path),ref(root/'state.json'),Path(folder)/'completion-report.json')
        coordinator.command(root,'finish',dispatch_id=offer['dispatch_id'],report=report['path'])
        return result(request,context,'complete',completion={'report':report,'finished_state':ref(root/'state.json')})

def harvest_collection_ready(request,context,folder,parent_path,coordinator,root,offer):
    need(offer.get('collection_contract')=='three-flow-collection-ready-v1','ready-fresh-offer-contract')
    flow=request['task']['flow']
    if flow==FLOWS[0]:
        import daily_orchestration as orch
    elif flow==FLOWS[1]:
        complaint_report_modules(request['config'])
        import complaint_execution_orchestration as orch
    else:
        import role_execution_orchestration as orch
    report=orch.collection_ready_report(ref(parent_path),ref(root/'state.json'),Path(folder)/'collection-ready-report.json')
    coordinator.command(root,'collection-ready',dispatch_id=offer['dispatch_id'],report=report['path'])
    return result(request,context,'collection-ready',collection_ready={'report':report,'coordinator_after':ref(root/'state.json')})

def verify_collection_ready(task,response,config):
    value=response.get('collection_ready');need(type(value)is dict and set(value)=={'report','coordinator_after'},'worker-ready-proof-required')
    c,d=modules(config);report=pinned(value['report']);state=pinned(value['coordinator_after']);offer=pinned(response['context']['offer'])
    need(offer.get('collection_contract')=='three-flow-collection-ready-v1'and task['payload'].get('collection_contract')==offer['collection_contract']and report.get('workflow')==task['flow']and report.get('day')==task['day']and report.get('dispatch_id')==offer['dispatch_id'],'worker-ready-original-scope')
    if task['flow']==FLOWS[0]:
        import daily_orchestration
        daily_orchestration.verified_collection_ready_facts(value['report'])
    else:
        import collection_ready
        collection_ready.facts(value['report'])
    need(state.get('collection_contract')==offer['collection_contract']and state.get('phase')=='ready'and state.get('collection_ready_reports',{}).get(task['flow'])==value['report']and any(e.get('type')=='collection-ready'and e.get('dispatch_id')==offer['dispatch_id']and e.get('report')==value['report']for e in state.get('events',[])),'worker-ready-coordinator-receipt')
    need(ref(Path(config['coordinator_root'])/'state.json')==value['coordinator_after'],'worker-ready-coordinator-drift')
    return value

def staged_modules(config):
    project=Path(config['project']);names=('workshop-director','daily-comment-stats','negative-review-complaints','violation-notifier','douyin-laike-operator','chrome-dom-export','wecom-messenger')
    dirs=[project/'skills'/n/'scripts'for n in names]
    need(all(p.is_dir()and p.resolve()==p and not any(x.is_symlink()for x in(p,*p.parents))for p in dirs),'staged-fixed-import-closure')
    sys.path[:0]=[str(p)for p in dirs]
    import unified_delivery,delivery_commit
    need(Path(unified_delivery.__file__)==dirs[0]/'unified_delivery.py'and Path(delivery_commit.__file__)==dirs[0]/'delivery_commit.py','staged-fixed-module-origin')
    return unified_delivery,delivery_commit

def unified_delivery_step(request,context,folder,c,root):
    """One bounded sealed batch, original per-item intents; never collect again."""
    delivery,commit=staged_modules(request['config']);task=request['task'];need(task['flow']==FLOWS[-1]and task['payload'].get('collection_contract')==delivery.CONTRACT and context.get('stage')=='unified-delivery','delivery-final-original-task')
    request_ref=ref(Path(folder)/'request.json');need(pinned(request_ref)==request,'delivery-original-request-bytes');round_key=task['plan_id']+':'+task['day'];base=root/'unified-delivery'/hashlib.sha256(round_key.encode()).hexdigest();items=base/'items'
    ready={v['flow']:v['context']['collection_ready_receipt']['report']for v in context['delivery_ready_tasks']};guard=commit.WorkerGuard(request_ref)
    # After any commit prefix, no sender path is entered again. apply() accepts
    # only exact original-prefix reentry; unknown/foreign after bytes hold.
    transaction=base/'completion/intent.json'
    if not transaction.exists():
        with guard.locked([]):
            batch_path=base/'batch.json'
            if batch_path.exists():
                plan_ref=delivery.ref(batch_path);original_batch=delivery.doc(plan_ref)
                need(isinstance(original_batch.get('accepted_request'),dict),'delivery-existing-batch-request-required')
                commit.reentry_request(request_ref,original_batch['accepted_request'])
                plan=delivery.check_plan(plan_ref)
            else:
                plan_ref=delivery.derive(ready,round_key,base,write=True,accepted_request=request_ref);plan=delivery._transport_plan(delivery.doc(plan_ref))
            for index,item in enumerate(plan['items']):
                itemfolder=items/str(index).zfill(4)
                # Even existing terminal results are strictly rechecked. Each
                # item has its own exclusive input intent; UNKNOWN stops here,
                # before any later item, never a new worker/key or re-collection.
                delivery._send_item(plan_ref,index,itemfolder,sender_directory=delivery.ROOT/'runtime/wecom-messenger',checked_plan=delivery._transport_plan(delivery.doc(plan_ref)));guard.check()
            proof=delivery.seal_clients(plan_ref,items,sender_directory=delivery.ROOT/'runtime/wecom-messenger');guard.check()
    else:
        original=pinned(ref(transaction));commit.reentry_request(request_ref,original['request']);proof=original['client_proof']
    committed=commit.apply(request_ref,proof,items);bundle=commit.seal_reports(committed,items)
    c.command(root,'finish-delivery',report=bundle['path']);receipt=ref(root/'operation-receipts/unified-delivery'/bundle['sha256']/'receipt.json')
    return result(request,context,'batch-complete',unified_completion={'reports':bundle,'coordinator_receipt':receipt})

def verify_unified_completion(task,response,config):
    delivery,commit=staged_modules(config);value=response['unified_completion'];bundle=pinned(value['reports']);cursor=pinned(bundle['cursor_commit']);items=Path(cursor['batch']['path']).parent/'items';reports=commit.verify_reports(value['reports'],items,current=True)
    need(task['flow']==FLOWS[-1]and task['payload'].get('collection_contract')==delivery.CONTRACT and response['context']==task['context']and task['context'].get('stage')=='unified-delivery','delivery-completion-original-task')
    original_request=pinned(cursor['intent'])['request'];request=pinned(original_request);commit.reentry_request(ref(Path(task['active_attempt'])/'request.json'),original_request);need(request['task']['id']==task['id']and request['context']==task['context'],'delivery-final-natural-worker-request')
    receipt=pinned(value['coordinator_receipt']);root=Path(config['coordinator_root']);need(value['coordinator_receipt']['path']==str(root/'operation-receipts/unified-delivery'/value['reports']['sha256']/'receipt.json')and receipt=={'kind':'three-flow-coordinator-delivery-consumed-v1','bundle':value['reports'],'state':receipt.get('state')},'delivery-coordinator-receipt-binding');state=pinned(receipt['state'])
    need(receipt['state']['path']==str(Path(value['coordinator_receipt']['path']).parent/'state-after.json')and state.get('unified_delivery')==value['reports']and state.get('delivery_complete')is True and state.get('index')==3 and state.get('phase')=='ready'and state.get('day')==task['day'],'delivery-coordinator-terminal-state')
    need(all(any(e.get('type')=='completed'and e.get('dispatch_id')==r['dispatch_id']and e.get('report')==bundle['reports'][flow]for e in state['events'])for flow,r in reports.items()),'delivery-coordinator-all-consumed')
    return reports

def daily_dom_operator_handoff(context,order):
    """Only a genuine independent DOM acquisition supersedes the pending reader.
    The original operator workflow/download/calls are evidence, never completed.
    """
    handoff=context['operator'];job=pinned(handoff['work_order'])
    if job.get('action')=='return-company':
        need(handoff.get('action')=='return-company','daily-return-handoff-action-conflict');return False
    run_dir=Path(job['workflow_path']).parents[3];batch_path=run_dir/'batch_receipt.json'
    if not batch_path.is_file():return False
    import flow
    from ds_common import dom_command,dom_capture_data,dom_original_download
    batch=flow.load_state(run_dir)
    rows=[row for row in batch['companies']if row['company']==job['company']]
    need(len(rows)==1,'daily-dom-handoff-company-not-unique');row=rows[0]
    if row.get('source_kind')!='daily-visible-dom-source-v1':return False
    need(batch.get('delivery_contract')=='three-flow-collection-ready-v1'and batch['dispatch_scope']['work_order']==order and row.get('status')in('acquired','complete'),'daily-dom-handoff-batch-scope')
    need(row.get('evidence')==str(Path(row['outdir'])/'dom-acquisition.json')and Path(row['outdir'])in Path(handoff['work_order']['path']).parents,'daily-dom-handoff-evidence-location')
    payload=read(row['evidence'])
    with dom_command():
        facts=dom_capture_data(row.get('dom_capture'),payload,batch,row)
        need(facts['job']['original_job']==handoff['work_order']and facts['job']['original_order']==order,'daily-dom-handoff-original-job')
        original=dom_original_download(facts['producer_data'])
        checkpoints=[x for x in row.get('checkpoints',[])if x.get('stage')=='dom-acquisition-complete']
        need(len(checkpoints)==1 and checkpoints[0]['capture']==row['dom_capture']and checkpoints[0]['receipt']==payload['receipt']and checkpoints[0]['original_workflow']==original and checkpoints[0]['download_verified']is False and checkpoints[0]['source_is_authoritative_export']is False,'daily-dom-handoff-checkpoint')
    return True

def returned_daily_dom_parent_output(context,order,prior,folder):
    """Read an already-returned original advance; never rerun that child.
    Only the DOM-backed old handoff may yield to its canonical new handoff.
    """
    import daily_execution_launcher as launch,daily_timed_run as role
    if not prior or not prior.get('calls'):return None
    call=prior['calls'][-1]
    if call.get('verb')!='advance' or call.get('state')!='returned':return None
    root=role.location(order['path']);role_state=read(root/'state.json')
    next_handoff=role_state.get('handoff')
    if not next_handoff or next_handoff.get('work_order')==context['operator']['work_order']:return None
    path=launch.location(order)/'state.json';before=ref(path)
    observed=launch.status(order,prior['archive_root'])
    need(observed.get('unresolved_child')is False and observed.get('status')=='running','daily-dom-returned-parent-unresolved')
    canonical=read(path);need(canonical==prior and ref(path)==before,'daily-dom-returned-parent-raced')
    clock=launch.timing.Clock();receipt_ref,receipt=launch.child_receipt(path.parent,canonical,call,clock)
    need(receipt['returncode']==0,'daily-dom-returned-parent-exit');child=launch.receipt_output(receipt,canonical)
    checked_order,checked_role=role.checked(root,order,prior['archive_root'])
    need(checked_role==role_state and role_state.get('phase')==child.get('phase')=='acquisition' and child.get('run_dir')==role_state['run_dir'] and child.get('handoff')==next_handoff,'daily-dom-returned-role-handoff')
    batch=role.check_batch(read(Path(role_state['run_dir'])/'batch_receipt.json'),checked_order,Path(role_state['run_dir']))
    job=pinned(next_handoff['work_order']);matches=[r for r in batch['companies']if r['company']==job['company']and str(r['groupid'])==str(job['groupid'])]
    need(len(matches)==1 and Path(job['workflow_path']).parents[3]==Path(role_state['run_dir'])and matches[0]['date_range']['start']==job['date_range']['start']and matches[0]['date_range']['end']==job['date_range']['end'],'daily-dom-returned-next-job-scope')
    expected=[call['argv'][0],str(Path(context['operator']['argv'][1])),'--work-order',next_handoff['work_order']['path'],'--tab-id',str(call['tab_id']),'--steps','25']
    need(next_handoff.get('argv')==expected and next_handoff.get('action')==job.get('action')in('acquire','return-company'),'daily-dom-returned-next-argv')
    need(ref(path)==before and read(root/'state.json')==role_state,'daily-dom-returned-source-raced')
    immutable(Path(folder)/'daily-dom-returned-parent-handoff.json',{'kind':'verified-returned-daily-dom-parent-handoff-v1','parent':before,'child_receipt':receipt_ref,'role_state':ref(root/'state.json'),'batch':ref(Path(role_state['run_dir'])/'batch_receipt.json'),'old_work_order':context['operator']['work_order'],'new_handoff':next_handoff,'original_order':order,'business_child_replayed':False})
    return {**observed,'child_result':child}

def adopt_restored_operator_work_order(request,context,folder):
    """Consume only the public resume-only repair, not arbitrary job drift.
    The original failed attempt/context remains immutable. New normal context
    receives the already-sealed original order and the exact same argv.
    """
    import flow
    handoff=context['operator'];changed=handoff['work_order'];path=Path(changed['path']);proof=path.parent/'immutable-work-order-repairs'/changed['sha256']/'proof.json'
    facts=flow.verify_immutable_work_order_repair(ref(proof))
    need(facts['changed_job']==changed and facts['canonical_original']['path']==changed['path']and facts['task_id']==request['task']['id']and facts['outer']==request['task']['outer']and facts['order']==context['order'],'restored-work-order-original-task')
    need(ref(Path(facts['workflow']['path']))==facts['workflow'],'restored-work-order-current-WF')
    job=pinned(facts['canonical_original']);need(job['workflow_path']==facts['workflow']['path']and job['action']==handoff['action']=='acquire'and handoff['argv']==[request['config']['python'],str(Path(request['config']['project'])/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'--work-order',changed['path'],'--tab-id',str(context['scope']['tab_id']),'--steps','25'],'restored-work-order-original-argv')
    adopted={**handoff,'work_order':facts['canonical_original']};immutable(Path(folder)/'restored-operator-work-order.json',{'kind':'verified-original-work-order-resume-repair-handoff-v1','proof':ref(proof),'original_handoff':handoff,'adopted_handoff':adopted,'task_id':request['task']['id'],'outer':request['task']['outer'],'business_command_replayed':False});return adopted

def adopt_refreshed_operator_work_order(request,context,prior,folder):
    """Consume only the derived-resume refresh of a materialized-but-never-
    started stable work order (B59 attempts 32-35). The handoff pins the
    frozen W130-generation resume: a truthy attempts field under an empty
    checkpoint prefix — underivable, never owned by a journal (none exists),
    and the bridge refuses any truthy side-effect field on a fresh start, so
    the stable work order can never start and dispatch will never run again.
    The refresh applies the current clean derivation to that one frozen
    field; every other field stays identical to the frozen bytes, the
    supervised reverify world must back it, and the frozen file must be the
    handoff of the original returned advance. The original failed
    attempt/context remains immutable; no input is replayed."""
    handoff=context['operator'];frozen=handoff['work_order'];path=Path(frozen['path'])
    if not path.is_absolute()or path.is_symlink()or path.resolve()!=path:raise ValueError('refreshed-work-order-path')
    base=path.parent/'immutable-work-order-resume-refreshes'/frozen['sha256']
    frozen_ref=ref(base/'frozen.data')
    need(frozen_ref['sha256']==frozen['sha256'],'refreshed-work-order-frozen-bytes')
    original=json.loads((base/'frozen.data').read_bytes())
    live=json.loads(path.read_bytes())
    need({k:v for k,v in live.items()if k!='resume'}=={k:v for k,v in original.items()if k!='resume'},'refreshed-work-order-field-drift')
    fr=original.get('resume')
    need(set(fr)=={'latest','checkpoints','export_pending','attempts'} and fr.get('latest')is None and fr.get('checkpoints')==[] and fr.get('export_pending')is False and type(fr.get('attempts'))is int and fr['attempts']>0,'refreshed-work-order-frozen-resume-underivable')
    need(live.get('resume')=={'latest':None,'checkpoints':[],'export_pending':False,'attempts':0},'refreshed-work-order-derived-resume')
    # An already-adopted refresh may have started the journal (attempt-36):
    # progress then belongs to it. Re-adoption on later retries is still
    # lawful while the journal belongs to this same work order; a foreign
    # journal stays fatal.
    journal_path=Path(original['workflow_path'])
    if journal_path.exists():
        j=json.loads(journal_path.read_text())
        need(j.get('work_order_id')==original['work_order_id'] and j.get('company')==original['company'] and str(j.get('groupid'))==str(original['groupid']),'refreshed-work-order-journal-foreign')
    run_dir=Path(original['workflow_path']).parents[3]
    batch=read(run_dir/'batch_receipt.json')
    rv=batch.get('reverify')
    need(type(rv)is dict and rv.get('kind')=='supervised-export-count-reverify-v1' and type(rv.get('round'))is int and rv.get('company')==original['company'] and str(rv.get('groupid'))==str(original['groupid']),'refreshed-work-order-reverify-scope')
    rows=[r for r in batch['companies']if r['company']==original['company']and str(r['groupid'])==str(original['groupid'])]
    need(len(rows)==1 and rows[0]['status']=='pending' and rows[0].get('export_pending')is False,'refreshed-work-order-row-frontier')
    need(not batch.get('failed') and batch.get('roundtrip',{}).get('verified')is True and not [r for r in batch['companies']if r['status']=='failed'],'refreshed-work-order-world')
    archive=run_dir/'reverify-archive'
    for record in (rv['first_batch'],rv['first_receipt']):
        need(type(record)is dict and set(record)=={'path','sha256'},'refreshed-work-order-archive-shape')
        material=archive/(Path(record['path']).stem+'-'+record['sha256']+'.json')
        need(material.is_file() and not material.is_symlink() and hashlib.sha256(material.read_bytes()).hexdigest()==record['sha256'],'refreshed-work-order-archive-missing')
    import daily_execution_launcher as launch,daily_timed_run as role
    call=prior['calls'][-1]
    need(call.get('verb')=='advance' and call.get('state')=='returned','refreshed-work-order-original-advance')
    canonical_path=launch.location(context['order'])/'state.json'
    canonical=read(canonical_path)
    clock=launch.timing.Clock();receipt_ref,receipt=launch.child_receipt(canonical_path.parent,canonical,call,clock)
    need(receipt['returncode']==0,'refreshed-work-order-original-advance-exit')
    child=launch.receipt_output(receipt,canonical)
    emitted=child.get('handoff',{}).get('work_order')
    need(emitted==frozen,'refreshed-work-order-original-handoff')
    adopted={**handoff,'work_order':{'path':str(path),'sha256':ref(path)['sha256']}}
    immutable(Path(folder)/'refreshed-operator-work-order.json',{'kind':'verified-original-work-order-resume-refresh-handoff-v1','frozen':frozen,'refreshed':adopted['work_order'],'frozen_bytes':frozen_ref,'original_advance_receipt':receipt_ref,'reverify':{'company':rv['company'],'round':rv['round']},'task_id':request['task']['id'],'outer':request['task']['outer'],'business_command_replayed':False});return adopted

REDISPATCH_LAUNCHER_STATUS=('running','hold','collection-ready')
def offer_parent(offer):
    """The dispatch offer's parent execution, keyed by flow family.

    Daily flows bind 'daily_execution'; complaint/violation flows bind
    'role_execution'. A keyed lookup keeps the supervised redispatch path from
    crashing with KeyError on offers whose flow key differs (observed on the
    2026-11-02 daily redispatch after a supervised coordinator retry).
    """
    for key in ('daily_execution','role_execution'):
        parent=offer.get(key)
        if isinstance(parent,dict) and isinstance(parent.get('order'),dict):return parent
    need(False,'offer-parent-execution-missing')

def continuation_order_refs(state,offer):
    """Same-family orders bound before the current offer, newest first.

    The coordinator records every role-execution binding in its own event log,
    so the orders this task already ran under stay provable after a supervised
    archive-then-re-dispatch replaced the outer offer.
    """
    prefix=offer['dispatch_id'].rsplit(':',1)[0]+':'
    def seq(value):
        tail=value.rsplit(':',1)[1] if isinstance(value,str) and value.count(':')>=2 else ''
        return int(tail) if tail.isdigit() else -1
    bound={}
    for event in state.get('events',[]):
        if event.get('type')=='role-execution-bound' and isinstance(event.get('dispatch_id'),str) and isinstance(event.get('order'),dict):
            if event['dispatch_id'].startswith(prefix):bound[event['dispatch_id']]=event['order']
    current=seq(offer['dispatch_id'])
    return [(key,bound[key])for key in sorted(bound,key=seq,reverse=True)if seq(key)<current]

def continuation_launcher(order_ref,config):
    """The tab an earlier order of THIS task already owned, or None if unstarted."""
    root=Path(config['coordinator_root']);order=pinned(order_ref)
    original=Path(order_ref['path'])
    # Same fixed location rule the launcher itself uses: the order file's stem.
    need(original.parent==root/'role-execution-orders'and original.suffix=='.json','redispatch-continuation-order-path')
    path=root/'role-executions'/original.stem/'launcher.json'
    if not path.is_file():return None
    launcher=read(path)
    need(launcher.get('kind')=='role-execution-launcher-v1'and launcher.get('order')==order_ref,'redispatch-continuation-launcher-order')
    need(launcher.get('scope_sha256')==order.get('scope_sha256'),'redispatch-continuation-launcher-scope')
    if launcher.get('status')not in REDISPATCH_LAUNCHER_STATUS:return None
    # A pid alone is not an identity; the launcher must also belong to this boot.
    need(launcher.get('boot_identity')==boot(),'redispatch-continuation-launcher-boot')
    tab_id=launcher.get('tab_id');pid=launcher.get('pid')
    need(type(tab_id)is int and tab_id>0 and type(pid)is int and pid>0,'redispatch-continuation-launcher-scope-shape')
    return {'launcher':ref(path),'scope':{'tab_id':tab_id,'pid':pid}}

def continuation_tab_identity(inventory,tab_id,groupids):
    """Prove one already-owned tab still exists as the same live browser tab (B38).

    A fresh bootstrap re-uses the last completed program's tab and refuses
    anything else, which is right for a brand-new task. A supervised
    re-dispatch instead continues this task's own tab, so no tab is discovered
    here: the tab is proved by identity. It may legitimately sit on a deep page
    the original order opened (an operation-control notice, a detail drawer), so
    no canonical business path is required, while scheme/host/allowance/window
    and duplicate-id shape checks stay exactly as strict as the bootstrap
    inventory and an order company must still match the URL's groupid.
    """
    from urllib.parse import urlsplit,parse_qs
    windows=inventory.get('windows')
    need(inventory.get('kind')=='dom-only-browser-tab-inventory-v1'and inventory.get('command')=={'op':'tabs'}and isinstance(windows,list),'browser-tab-inventory-invalid')
    need(groupids and all(isinstance(value,str)and value.isdigit()for value in groupids),'browser-tab-order-groupids-required')
    need(len({window.get('windowId')for window in windows})==len(windows),'browser-tab-window-duplicate')
    all_ids=[tab.get('tabId')for window in windows for tab in window.get('tabs',[])]
    need(len(set(all_ids))==len(all_ids),'browser-tab-id-duplicate')
    found=[]
    for window in windows:
        need(type(window.get('windowId'))is int and window['windowId']>0 and isinstance(window.get('tabs'),list),'browser-tab-window-invalid')
        if window.get('type')!='normal':continue
        for tab in window['tabs']:
            if tab.get('tabId')!=tab_id:continue
            need(tab.get('windowId')==window['windowId'],'browser-tab-scope-invalid')
            url=urlsplit(tab.get('url')or'');query=parse_qs(url.query,keep_blank_values=True)
            need(tab.get('allowed')is True and url.scheme=='https'and url.netloc=='life.douyin.com'and not url.fragment,'redispatch-continuation-tab-url')
            groups=query.get('groupid')or[]
            need(len(groups)==1 and groups[0]in groupids,'redispatch-continuation-tab-company')
            pair={'life_biz_view_id','life_account_biz_ids'}&set(query)
            need(not pair or pair=={'life_biz_view_id','life_account_biz_ids'}and query['life_biz_view_id']==['22']and query['life_account_biz_ids']==[''],'redispatch-continuation-tab-merchant')
            found.append({'tab_id':tab['tabId'],'window_id':window['windowId'],'groupid':groups[0],'url':tab['url'],'selection':'original-task-tab-preserved-across-supervised-redispatch'})
    need(len(found)==1,'redispatch-continuation-tab-not-available')
    return found[0]

def continuation_browser_scope(context,state,offer,config,*,scan=None,tab_scan=None):
    """Prove the tab this task already owned survives the supervised re-dispatch (B38).

    B35's re-dispatch dropped the outer binding, so the following step fell back
    to the brand-new-task bootstrap, which only accepts the last completed
    program's tab; once that foreign tab was closed the task could never bind
    again. Continuing the task's own tab is both narrower and safer than
    adopting another tab mid-task. Two pinned sources are tried newest first:
    the outer context's own binding, then the launcher of an earlier same-family
    order recorded in the coordinator's role-execution-bound events. A dead tab
    is a hold, never a fresh binding.
    """
    evidence={'kind':'supervised-redispatch-browser-continuation-v1','current_dispatch_id':offer['dispatch_id'],'source':None,'scope':None,'binding':None,'candidates':[],'reason':None}
    sources=[];scope=context.get('scope');binding=context.get('browser_binding')
    if isinstance(scope,dict)and isinstance(binding,dict):
        shaped=binding.get('kind')=='task-browser-process-binding-v1'and binding.get('comm')==CHROME_MAIN and binding.get('scope')==scope and type(scope.get('tab_id'))is int and scope['tab_id']>0 and type(scope.get('pid'))is int and scope['pid']>0
        if shaped:sources.append({'source':'task-context','scope':scope,'binding':binding})
        else:evidence['candidates'].append({'source':'task-context','reason':'redispatch-continuation-binding-shape'})
    for dispatch_id,order_ref in continuation_order_refs(state,offer):
        try:value=continuation_launcher(order_ref,config)
        except (ValueError,KeyError,TypeError)as error:
            evidence['candidates'].append({'source':'prior-order-launcher','dispatch_id':dispatch_id,'order':order_ref,'reason':str(error)});continue
        if value is None:
            evidence['candidates'].append({'source':'prior-order-launcher','dispatch_id':dispatch_id,'order':order_ref,'reason':'redispatch-continuation-launcher-not-started'});continue
        evidence['candidates'].append({'source':'prior-order-launcher','dispatch_id':dispatch_id,'launcher':value['launcher'],'scope':value['scope']})
        sources.append({'source':'prior-order-launcher','dispatch_id':dispatch_id,'scope':value['scope'],'binding':None})
    ranges=[str(row['groupid'])for row in pinned(offer_parent(offer)['order'])['scope']['company_ranges']]
    evidence['groupids']=ranges
    if not sources:
        evidence['reason']='redispatch-continuation-no-prior-binding';return evidence
    try:observed=(scan or browser_processes)()
    except (OSError,subprocess.SubprocessError)as error:
        evidence.update(reason='redispatch-continuation-browser-discovery-failed',error=type(error).__name__);return evidence
    evidence['discovery']=observed;found=observed['candidates']
    if len(found)!=1:
        evidence['reason']='unique-chrome-main-required';return evidence
    live=found[0];inventory=None;failures=[]
    for candidate in sources:
        scope=candidate['scope'];binding=candidate['binding']
        if live['pid']!=scope['pid']or(binding is not None and binding.get('process')!=live['process']):
            failures.append('redispatch-continuation-browser-process-changed');continue
        if inventory is None:
            try:inventory=(tab_scan or browser_tab_inventory)(config)
            except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError)as error:
                evidence.update(reason='redispatch-continuation-tab-discovery-failed',error=str(error));return evidence
            evidence['tab_inventory']=inventory
        try:tab=continuation_tab_identity(inventory,scope['tab_id'],ranges)
        except (ValueError,KeyError,TypeError)as error:
            failures.append('redispatch-continuation-tab-not-available');evidence['candidates'].append({'source':candidate['source'],'tab_error':str(error)});continue
        chosen=binding or {'kind':'task-browser-process-binding-v1','scope':scope,'comm':CHROME_MAIN,'process':live['process'],'discovery':observed}
        evidence.update(source=candidate['source'],scope=scope,binding=chosen,tab=tab)
        return evidence
    evidence['reason']=failures[0] if failures else 'redispatch-continuation-no-prior-binding'
    return evidence

ENTRY_TAB_PATHS=('/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management')
def reviewed_entry_group(url,groupids):
    """The order company a tab's reviewed entry page belongs to, else None.

    Mirrors the company entry policy's own pre-switch whitelist. A violation
    list page is deliberately absent: it carries its own reviewed query shape
    and is never adopted as a fresh start page here.
    """
    from urllib.parse import urlsplit,parse_qs
    u=urlsplit(url or '');q=parse_qs(u.query,keep_blank_values=True)
    if u.scheme!='https'or u.netloc!='life.douyin.com'or u.fragment:return None
    groups=q.get('groupid')or[]
    if len(groups)!=1 or groups[0]not in groupids or u.path not in ENTRY_TAB_PATHS:return None
    pair={'life_biz_view_id','life_account_biz_ids'}&set(q)
    if pair and (pair!={'life_biz_view_id','life_account_biz_ids'}or q.get('life_biz_view_id')!=['22']or q.get('life_account_biz_ids')!=['']):return None
    return groups[0]

def entry_rebind_candidates(inventory,groupids):
    """Every live tab the entry policy would accept, sorted by tab id."""
    found=[]
    for window in inventory.get('windows',[]):
        if window.get('type')!='normal':continue
        for tab in window.get('tabs',[]):
            if tab.get('allowed')is not True:continue
            group=reviewed_entry_group(tab.get('url'),groupids)
            if group is None:continue
            found.append({'tab_id':tab['tabId'],'window_id':window['windowId'],'groupid':group,'url':tab['url']})
    return sorted(found,key=lambda row:row['tab_id'])

REDISPATCH_ENTRY_HANDOFF='redispatch-entry-page-rebind-required'
def handoff_response_authorization(request,context):
    """The supervisor's later answer to this task's own entry-rebind hold (B42).

    The supervised archive report is written before the worker can know whether the proven
    tab still hosts the company entry step, and the coordinator pins that report by sha in
    its own repair-redispatch event, so a decision taken afterwards can never be appended to
    it. The scheduler already accepts a bound later decision for this task: the handoff
    response, which the engine binds to this task's exact waiting hold. Only a response
    answering this task's own entry-rebind hold is read, and the authorization inside it is
    still checked against the live tab set, so a stale or transplanted answer is ignored
    instead of becoming authority.
    """
    reference=context.get('response')
    if not isinstance(reference,dict) or not isinstance(reference.get('path'),str):return None
    value=pinned(reference)
    need(value.get('kind')=='workshop-handoff-response-v1' and value.get('task_id')==request['task']['id'],'redispatch-rebind-response-binding')
    answered=value.get('request')
    if not isinstance(answered,dict) or not isinstance(answered.get('path'),str):return None
    try:handoff=pinned(answered)
    except (OSError,ValueError):return None
    if not (handoff.get('kind')=='workshop-handoff-v1' and handoff.get('task_id')==request['task']['id'] and handoff.get('reason')==REDISPATCH_ENTRY_HANDOFF):return None
    return value.get('entry_rebind_authorization')

def supervised_entry_rebind(continuation,report,config,*,scan=None,tab_scan=None,response_authorization=None):
    """Verify the supervisor's authorized replacement for an unstartable tab (B39).

    A proven tab may sit on a reviewed detail page or on the v2 app shell, where
    the company entry step cannot start at all. The task must not silently begin
    there, and no other tab may be adopted by guesswork, so the replacement is
    authorized by the supervisor inside the coordinator's own supervised repair
    report and verified here against the live inventory: the recorded candidate
    set must equal today's live set, and the chosen tab must be that exact tab.
    """
    evidence={'kind':'supervised-entry-rebind-verification-v1','needed':False,'authorized':None,'current_tab':continuation.get('tab'),'candidates':[],'scope':None,'binding':None,'reason':None}
    scope=continuation.get('scope')
    if not isinstance(scope,dict):evidence['reason']='redispatch-entry-rebind-no-proven-tab';return evidence
    groupids=continuation.get('groupids')or[]
    if reviewed_entry_group((continuation.get('tab')or{}).get('url'),groupids)is not None:return evidence
    evidence['needed']=True
    authorization=report.get('supervised_entry_rebind')
    if not isinstance(authorization,dict):authorization=response_authorization
    if not isinstance(authorization,dict):
        evidence['reason']='redispatch-entry-page-rebind-required';return evidence
    need(authorization.get('kind')=='supervised-entry-rebind-authorization-v1','redispatch-entry-rebind-kind')
    need(authorization.get('authorized_by')=='supervisor'and isinstance(authorization.get('reason'),str)and bool(authorization['reason']),'redispatch-entry-rebind-authorization')
    need(authorization.get('from_scope')==scope,'redispatch-entry-rebind-from-scope')
    selected=authorization.get('selected')or{}
    need(type(selected.get('tab_id'))is int and selected['tab_id']>0,'redispatch-entry-rebind-selected-shape')
    try:observed=(scan or browser_processes)()
    except (OSError,subprocess.SubprocessError)as error:
        evidence.update(reason='redispatch-entry-rebind-browser-discovery-failed',error=type(error).__name__);return evidence
    evidence['discovery']=observed;found=observed['candidates']
    if len(found)!=1:
        evidence['reason']='unique-chrome-main-required';return evidence
    try:inventory=(tab_scan or browser_tab_inventory)(config)
    except (ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError)as error:
        evidence.update(reason='redispatch-entry-rebind-tab-discovery-failed',error=str(error));return evidence
    evidence['tab_inventory']=inventory
    live=entry_rebind_candidates(inventory,groupids);evidence['candidates']=live
    if authorization.get('candidates')!=live:
        evidence['reason']='redispatch-entry-rebind-candidates-changed';return evidence
    if selected['tab_id']==scope['tab_id']:
        evidence['reason']='redispatch-entry-rebind-same-tab';return evidence
    matches=[row for row in live if row['tab_id']==selected['tab_id']]
    if len(matches)!=1:
        evidence['reason']='redispatch-entry-rebind-tab-not-available';return evidence
    new_scope={'tab_id':matches[0]['tab_id'],'pid':found[0]['pid']}
    binding={'kind':'task-browser-process-binding-v1','scope':new_scope,'comm':CHROME_MAIN,'process':found[0]['process'],'discovery':observed}
    evidence.update(authorized=authorization,scope=new_scope,binding=binding,tab=matches[0])
    return evidence

def redispatch_fresh_context(context,continuation):
    """Outer context handed to the canonical coordinator for the new dispatch.

    The archived offer and its stale scope proofs are always dropped so the new
    dispatch recaptures its own baseline; only the tab this task already proved
    it owns is carried across. None means the task must hold instead.
    """
    reason=continuation['reason']
    if reason is None:preserved={'scope':continuation['scope'],'browser_binding':continuation['binding']}
    elif reason=='redispatch-continuation-no-prior-binding':preserved={}
    else:return None
    fresh={k:v for k,v in context.items() if k not in('offer','pending_dependency','scope_pending','scope_resolution','scope','browser_binding')}
    fresh.update(preserved);return fresh

def redispatch_archived_offer(request,context,folder,c,d,config,offer,state):
    """Supervised archive-then-redispatch protocol for a stale outer offer (B35).
    A dispatch archived by the supervisor's coordinator retry leaves the
    coordinator phase='ready' with the archived dispatch_id still pinned, while
    the outer task context keeps the original offer. The coordinator itself
    supports re-dispatch from 'ready' (plan increments the attempt); only the
    stale offer blocks it. Re-dispatching archives the stale offer and issues a
    fresh order whose child re-captures the site baseline, which is the
    designed recovery for a governance hold caused by real site-side fact
    completion. Nothing is forged: every field below is verified against the
    coordinator's own immutable retry evidence before a new dispatch is issued.
    """
    task=request['task'];root=Path(config['coordinator_root'])
    archived=state.get('dispatch_id');prefix=offer['dispatch_id'].rsplit(':',1)[0]+':'
    def seq(value):
        tail=value.rsplit(':',1)[1] if isinstance(value,str) and value.count(':')>=2 else ''
        return int(tail) if tail.isdigit() else -1
    # The archived dispatch is either the offer's own id (single archive) or a
    # later same-family successor that earlier protocol rounds created and the
    # supervisor archived again (multi-round recovery). Anything else — a
    # running dispatch, a different role/day, or an older sequence — is fatal.
    need(state['phase']=='ready' and isinstance(archived,str) and archived.startswith(prefix) and seq(archived)>=seq(offer['dispatch_id']),'redispatch-state-not-archived-ready')
    events=state.get('events',[])
    need(bool(events) and events[-1].get('type')=='repair-redispatch' and events[-1].get('previous')==archived,'redispatch-last-action-not-supervised-archive')
    event=events[-1];need(ref(event['report'])['sha256']==event['sha256'],'redispatch-repair-report-changed')
    report=json.loads(Path(event['report']).read_bytes());role=d.ROLES[d.FLOWS.index(task['flow'])]
    need(report.get('dispatch_id')==archived and report.get('day')==task['day'] and report.get('role')==role and
         all(report.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')),'redispatch-supervised-report-scope')
    need(context.get('offer') and pinned(context['offer'])==offer,'redispatch-context-offer-mismatch')
    dispatch_id=offer['dispatch_id']
    immutable(Path(folder)/'archived-offer-redispatch-intent.json',{'kind':'supervised-archive-redispatch-intent-v1','archived_offer':context['offer'],'archived_dispatch_id':dispatch_id,'archived_successor_dispatch_id':archived,'archive_event':event,'repair_report':ref(event['report']),'task_id':task['id'],'attempt_id':request['attempt_id'],'at':now()})
    continuation=continuation_browser_scope(context,state,offer,config)
    continuation_ref=immutable(Path(folder)/'archived-offer-redispatch-continuation.json',continuation)
    if continuation['reason']is None:
        rebind=supervised_entry_rebind(continuation,report,config,response_authorization=handoff_response_authorization(request,context))
        if rebind['needed']:
            rebind_ref=immutable(Path(folder)/'entry-rebind.json',rebind)
            if rebind['reason']:
                return waiting(request,context,folder,rebind['reason'],{'archived_dispatch_id':dispatch_id,'archived_offer':context['offer'],'continuation':continuation_ref,'entry_rebind':rebind_ref,'no_new_dispatch_issued':True})
            continuation={**continuation,'scope':rebind['scope'],'binding':rebind['binding'],'source':'supervised-entry-rebind','entry_rebind':rebind_ref}
    fresh=redispatch_fresh_context(context,continuation)
    if fresh is None:
        # A tab this task already owned is gone: hold with that reason instead
        # of silently adopting a different merchant tab for the same task.
        return waiting(request,context,folder,continuation['reason'],{'archived_dispatch_id':dispatch_id,'archived_offer':context['offer'],'continuation':continuation_ref,'no_new_dispatch_issued':True})
    new_context,done=dispatch(request,fresh,folder,c,d,config)
    need(done is None and new_context.get('offer'),'redispatch-new-dispatch-required')
    new_offer=pinned(new_context['offer'])
    need(seq(new_offer['dispatch_id'])>seq(archived) and new_offer['dispatch_id'].startswith(prefix),'redispatch-new-dispatch-id-shape')
    need(new_offer['workflow']==offer['workflow'] and new_offer['active_day']==offer['active_day'],'redispatch-scope-drift')
    need([str(row['groupid'])for row in pinned(offer_parent(new_offer)['order'])['scope']['company_ranges']]==continuation['groupids'],'redispatch-continuation-order-scope-changed')
    immutable(Path(folder)/'archived-offer-redispatch.json',{'kind':'supervised-archive-redispatch-protocol-v1','archived_offer':context['offer'],'archived_dispatch_id':dispatch_id,'archived_successor_dispatch_id':archived,'archive_event':event,'repair_report':ref(event['report']),'new_offer':new_context['offer'],'new_dispatch_id':new_offer['dispatch_id'],'coordinator_state_after_dispatch':ref(root/'state.json'),'browser_continuation':continuation_ref,'task_id':task['id'],'attempt_id':request['attempt_id'],'worker_replayed_no_business_command':True,'order_origin_fresh_baseline_recaptured':True})
    return new_context

def redispatch_or_propagate(request,context,folder,c,d,config,offer,state):
    """A supervised handoff is a result, never a context.

    The protocol returns a worker result whenever it must ask the supervisor for something
    (an entry rebind, a dead tab, a changed candidate set). Only a real new context may
    replace the caller's, so the handoff is returned separately and propagated unchanged;
    dereferencing a result as a context crashes the exact path that asks for help.
    """
    value=redispatch_archived_offer(request,context,folder,c,d,config,offer,state)
    if isinstance(value,dict) and value.get('kind')=='workshop-worker-result-v1':return None,value
    return value,None

def step(request,folder):
    config=request['config'];context=dict(request['context']);task=request['task']
    c,d=modules(config);root=Path(config['coordinator_root'])
    if context.get('stage')=='unified-delivery':return unified_delivery_step(request,context,Path(folder),c,root)
    if not context.get('offer'):
        context,done=dispatch(request,context,folder,c,d,config)
        if done:return result(request,context,'complete',completion=done)
        if context.get('pending_dependency'):return waiting(request,context,folder,context['pending_dependency'],{'workflow':task['flow'],'no_order_faked':True})
    atomic(Path(folder)/'adapter-context.json',context)
    offer=pinned(context['offer']);need(offer['workflow']==task['flow'] and offer['active_day']==task['day'],'original-offer-scope')
    state=read(root/'state.json')
    if not(state['phase']=='running' and state['dispatch_id']==offer['dispatch_id']):
        # Supervised archive-then-redispatch (B35): the coordinator is left in
        # its own documented post-retry shape and the outer context still
        # carries the archived offer. The protocol re-dispatches through the
        # canonical coordinator path; any other mismatch stays fatal.
        context,handoff=redispatch_or_propagate(request,context,folder,c,d,config,offer,state)
        if handoff is not None:return handoff
        atomic(Path(folder)/'adapter-context.json',context)
        offer=pinned(context['offer'])
        state=read(root/'state.json')
    need(state['phase']=='running' and state['dispatch_id']==offer['dispatch_id'],'original-dispatch-not-running-supervision-required')
    response=pinned(context.pop('response')) if context.get('response') else None
    flow=task['flow'];daily=flow==FLOWS[0]
    key='daily_execution' if daily else 'role_execution';parent=offer[key];order=parent['order'];context['order']=order;stage=context.get('stage','start');commands=parent['commands'];argv=None
    if daily:
        import daily_execution_launcher as launch
        path=launch.location(order)/'state.json'
    else:
        if flow==FLOWS[2]:import role_execution_order as ordermod
        else:import complaint_execution_order as ordermod
        path=ordermod.location(order)/'launcher.json'
    prior=read(path) if path.exists() else None
    current_ready=Path(order['path']).parent.parent/'daily-executions'/Path(order['path']).stem/'collection-ready.json'
    if daily and current_ready.is_file():
        import current_daily_ready
        report=current_daily_ready.build_report(order,root,Path(folder)/'collection-ready-report.json')
        c.command(root,'collection-ready',dispatch_id=offer['dispatch_id'],report=report['path'])
        return result(request,context,'collection-ready',collection_ready={'report':report,'coordinator_after':ref(root/'state.json')})
    if flow==FLOWS[1] and prior and prior.get('status')=='complete' and reviewed_completion_scope(path):
        return completed_complaint_report(request,context,Path(folder),path,c,root,offer)
    if flow==FLOWS[1] and prior and prior.get('status')=='complete':
        return harvest_complaint_report(request,context,Path(folder),path,c,root,offer)
    if prior and prior.get('status')=='collection-ready':return harvest_collection_ready(request,context,Path(folder),path,c,root,offer)
    if response and response.get('waiting_source_successor'):
        sys.path.insert(0,str(Path(config['project'])/'skills/violation-notifier/scripts'))
        import violation_reboot_continuation as source_recovery
        context=source_recovery.w66_effective_context(request,context,response,prior)
    resolved=resolve_browser_scope(context,config,response_scope=response.get('scope') if response and context.get('scope_pending') else None,parent=prior,completed_before=task['outer']['started_at'])
    proof=immutable(Path(folder)/'browser-scope-resolution.json',resolved)
    if resolved['reason']:
        context.update(scope_pending=True,scope_resolution=proof)
        atomic(Path(folder)/'adapter-context.json',context)
        return waiting(request,context,folder,resolved['reason'],{'order_already_issued':True,'offer':context['offer'],'resolution':proof,'no_parent_pid_change':True})
    scope=resolved['scope']
    if context.get('reboot_continuation'):context.update(effective_scope=scope,scope_pending=False,scope_resolution=proof)
    else:context.update(scope=scope,browser_binding=resolved['binding'],scope_pending=False,scope_resolution=proof)
    if daily:
        import daily_execution_launcher as launch,daily_orchestration as orch
        path=launch.location(order)/'state.json';typed_parent_advance=False;returned_parent_output=None
        if stage=='start':argv=commands['start'];nextstage='advance'
        elif stage in ('advance','notify'):
            argv=commands[stage]+(['--tab-id',str(scope['tab_id'])] if stage=='advance' else ['--steps','25']);nextstage=stage
        elif stage=='operator':
            h=context['operator']
            try:pinned(h['work_order'])
            except ValueError as error:
                if str(error)!='pinned-file-changed':raise
                try:h=adopt_restored_operator_work_order(request,context,folder)
                except FileNotFoundError:h=adopt_refreshed_operator_work_order(request,context,prior,folder)
                context['operator']=h
            if resume_switch_transport(context,config,folder):
                atomic(Path(folder)/'adapter-context.json',context);return result(request,context,'continue')
            expected=[config['python'],str(Path(config['project'])/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'--work-order',h['work_order']['path'],'--tab-id',str(scope['tab_id']),'--steps','25'];need(h['argv']==expected,'daily-handoff-fixed-argv-required')
            typed_parent_advance=daily_dom_operator_handoff(context,order)
            argv=commands['advance']+['--tab-id',str(scope['tab_id'])] if typed_parent_advance else expected;nextstage='advance'
            if typed_parent_advance:returned_parent_output=returned_daily_dom_parent_output(context,order,prior,folder)
        else:raise ValueError('daily-stage-invalid')
        if stage=='notify':
            observed=daily_notification_snapshot(order,config['project'])
            if observed and not observed.get('complete'):
                if resume_pre_paste_focus_sender(context,config,folder,observed):
                    atomic(Path(folder)/'adapter-context.json',context);return result(request,context,'continue')
                if resume_initial_sender(context,config,folder,observed):
                    atomic(Path(folder)/'adapter-context.json',context);return result(request,context,'continue')
                before_child={'phase':'notification-pending','notification':observed}
                context.pop('notification_progress',None)
                blocked=daily_notification_progress(before_child,context,folder)
                if blocked:return result(request,context,'failed',error=blocked['error'],notification_guard=blocked)
                # Seed comparison from current canonical sender semantics, never
                # a prior parent timestamp or its ever-growing calls list.
        atomic(Path(folder)/'adapter-context.json',context)
        output=returned_parent_output if returned_parent_output is not None else run_command(argv,folder,'parent-advance'if typed_parent_advance else'parent-'+stage);context['stage']=nextstage
        if stage=='operator'and not typed_parent_advance:return result(request,context,'continue')
        if output.get('status') in ('attention','hold'):return result(request,context,'failed',error='parent-hold-inspect-original')
        if output.get('status')=='collection-ready':return harvest_collection_ready(request,context,Path(folder),path,c,root,offer)
        if output.get('status')=='complete':
            report=orch.completion_report(ref(path),ref(root/'state.json'),Path(folder)/'completion-report.json');c.command(root,'finish',dispatch_id=offer['dispatch_id'],report=report['path']);return result(request,context,'complete',completion={'report':report,'finished_state':ref(root/'state.json')})
        child=output.get('child_result',{})
        if child.get('handoff'):
            context.update(stage='operator',operator=child['handoff']);return result(request,context,'continue')
        if child.get('phase')=='notification-pending':child={**child,'notification':daily_notification_snapshot(order,config['project'])}
        blocked=daily_notification_progress(child,context,folder)
        if blocked:return result(request,context,'failed',error=blocked['error'],notification_guard=blocked)
        if child.get('phase') in ('notification-ready','notification-pending'):context['stage']='notify'
        return result(request,context,'continue')
    else:
        if flow==FLOWS[2]:import role_execution_order as ordermod,role_execution_orchestration as orch
        else:import complaint_execution_order as ordermod,complaint_execution_orchestration as orch
        path=ordermod.location(order)/'launcher.json'
        if stage=='start':argv=commands['start']+['--tab-id',str(scope['tab_id']),'--pid',str(scope['pid'])]
        elif response:
            need(response.get('parent_response'),'parent-typed-response-required');r=response['parent_response'];pinned(r);argv=commands['accept']+['--response',r['path'],'--response-sha256',r['sha256']]
        else:argv=commands['run']+['--steps','1000']
        atomic(Path(folder)/'adapter-context.json',context)
        output=run_command(argv,folder,'parent-'+stage);context['stage']='run'
        if output.get('status')=='collection-ready':return harvest_collection_ready(request,context,Path(folder),path,c,root,offer)
        if output.get('status')=='complete':
            if flow==FLOWS[1] and reviewed_completion_scope(path):
                return completed_complaint_report(request,context,Path(folder),path,c,root,offer)
            if flow==FLOWS[1]:return harvest_complaint_report(request,context,Path(folder),path,c,root,offer)
            report=orch.report(ref(path),ref(root/'state.json'),Path(folder)/'completion-report.json');c.command(root,'finish',dispatch_id=offer['dispatch_id'],report=report['path']);return result(request,context,'complete',completion={'report':report,'finished_state':ref(root/'state.json')})
        if output.get('status') in ('hold','attention'):return result(request,context,'failed',error='parent-hold-inspect-original')
        child=output.get('child') or {}
        if output.get('status')=='waiting' or child.get('handoff'):return waiting(request,context,folder,'parent-ai-or-png-review-required',{'parent_handoff':child.get('handoff'),'parent_status':output,'accept_command':commands['accept']})
        return result(request,context,'continue')

def main():
    p=argparse.ArgumentParser();p.add_argument('--request',required=True);p.add_argument('--response',required=True);a=p.parse_args();r=read(a.request)
    try:value=step(r,Path(a.request).parent)
    except Exception as e:
        checkpoint=Path(a.request).parent/'adapter-context.json';value=result(r,read(checkpoint) if checkpoint.exists() else r['context'],'failed',error=str(e))
    immutable(a.response,value)
if __name__=='__main__':main()
