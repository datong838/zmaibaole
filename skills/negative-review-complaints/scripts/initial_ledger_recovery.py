"""Typed one-time recovery of the exact pre-engine snapshot-path comparison failure.
Metadata only. Original origin, clocks, keys, code_refs and failed child remain.
"""
import argparse,copy,fcntl,json,sys,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'skills/workshop-director/scripts'))
import complaint_execution_order as o
FIELD='initial_ledger_origin_recovery';KIND='complaint-initial-ledger-origin-recovery-v1'
NAMES={'complaint_execution_ports.py':'skills/negative-review-complaints/scripts/complaint_execution_ports.py','complaint_execution.py':'skills/negative-review-complaints/scripts/complaint_execution.py','initial_ledger_recovery.py':'skills/negative-review-complaints/scripts/initial_ledger_recovery.py','complaint_execution_launcher.py':'skills/workshop-director/scripts/complaint_execution_launcher.py','complaint_execution_orchestration.py':'skills/workshop-director/scripts/complaint_execution_orchestration.py'}
NAMES.update({'review_region_capture.py':'skills/chrome-dom-export/scripts/review_region_capture.py','program_review_quality.py':'skills/negative-review-complaints/scripts/program_review_quality.py','review-quality-ocr.swift':'skills/negative-review-complaints/scripts/review-quality-ocr.swift','review-quality-ocr':'skills/negative-review-complaints/scripts/review-quality-ocr','review-quality-runtime.json':'skills/negative-review-complaints/scripts/review-quality-runtime.json'})
ADDED_NAMES={'initial_ledger_recovery.py','program_review_quality.py','review-quality-ocr.swift','review-quality-ocr','review-quality-runtime.json'}
REVIEW_ENTRY_FIELD='review_entry_preinput_recovery'
REVIEW_FRAMES_FIELD='review_frames_preinput_recovery'
def review_entry_code_read(reference,archives=()):
    # Closed, ordered generations of reviewed historical CODE slots only.
    base={source_paths()['initial_ledger_recovery.py'],str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')}
    capture=str(o.PROJECT/'skills/chrome-dom-export/scripts/review_capture.py')
    wrapper=str(o.PROJECT/'skills/negative-review-complaints/scripts/capture_review_region.py')
    native={str(o.PROJECT/'skills/chrome-dom-export/scripts'/n) for n in ('native_window_capture.py','native_region_capture.py','review_region_capture.py')}
    quality=str(o.PROJECT/'skills/negative-review-complaints/scripts/program_review_quality.py')
    generations={0:set(),2:base,3:base|{capture},4:base|{capture,wrapper},7:base|{capture,wrapper}|native,8:base|{capture,wrapper}|native|{quality}}
    # One further reviewed bridge generation, never an arbitrary duplicate slot.
    if len(archives) in (9,10,11,12):
        bridge=str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')
        targets=[x['target'] for x in archives]
        expected=generations[8] | ({source_paths()['complaint_execution_ports.py']} if len(archives)>=10 else set()) | ({str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution_normal.py')} if len(archives)>=11 else set()) | ({str(o.PROJECT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py')} if len(archives)==12 else set())
        o.need(set(targets)==expected and targets.count(bridge)==2 and all(targets.count(x)==1 for x in expected-{bridge}) and len({x['archive']['sha256'] for x in archives if x['target']==bridge})==2,'review-entry-exact-nine-or-ten-historical-code-slots')
        matches=[x for x in archives if x['target']==reference['path'] and x['archive']['sha256']==reference['sha256']]
        if reference['path'] in targets:
            o.need(len(matches)==1,'review-entry-historical-code-sha');return o.raw(matches[0]['archive'])
        return o.raw(reference)
    targets={x['target'] for x in archives}
    o.need(len(archives) in generations and len(targets)==len(archives) and targets==generations[len(archives)],'review-entry-exact-historical-code-slots')
    for item in archives:
        if reference['path']==item['target']:
            o.need(item['archive']['sha256']==reference['sha256'],'review-entry-historical-code-sha');return o.raw(item['archive'])
    return o.raw(reference)

def reviewed_runtime(targets):
    by_name={Path(t['target']).name:t for t in targets};runtime=o.doc(by_name['review-quality-runtime.json']['after'])
    o.need(runtime=={'kind':'local-review-quality-runtime-v1','binary_sha256':by_name['review-quality-ocr']['after']['sha256'],'swift_sha256':by_name['review-quality-ocr.swift']['after']['sha256']},'initial-ledger-reviewed-runtime-pins')
def source_paths():return {name:str(o.PROJECT/relative) for name,relative in NAMES.items()}
def phase_directory(s):return o.location(s['order'])
def immutable_bytes(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():o.need(not path.is_symlink() and path.read_bytes()==raw,'initial-ledger-archive-conflict');return o.ref(path)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:o.need(not path.is_symlink() and path.read_bytes()==raw,'initial-ledger-archive-conflict')
    finally:os.unlink(tmp)
    return o.ref(path)
def canonical_launcher(reference):
    s=o.doc(reference);folder=phase_directory(s);o.need(Path(reference['path'])==folder/'launcher.json','initial-ledger-canonical-launcher');return s,folder

def ledger_bytes(order):
    evidence=[]
    for company in order['companies']:
        snapshot=o.raw(company['ledger']);current=o.ref(Path(company['root'])/'state.json');o.need(current['sha256']==company['ledger']['sha256'] and o.raw(current)==snapshot,'initial-ledger-real-bytes-changed');evidence.append({'company':company['company'],'canonical':current,'snapshot':company['ledger']})
    o.need(len(evidence)==2 and len({x['company'] for x in evidence})==2,'initial-ledger-two-companies');return evidence

def original_failure(s,worker_exit_ref,*,require_engine_absent,expected_error='complaint-parent-ledger-changed'):
    order=o.validate(s['order']);folder=phase_directory(s);o.need(s['kind']=='role-execution-launcher-v1' and s['status']=='hold' and s.get('error')=='execution-child-stopped' and s.get('mode')=='acceptance' and s.get('origin')=='fresh' and not s.get('child') and not s.get('completion') and not s.get(FIELD),'initial-ledger-exact-first-hold')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items()),'initial-ledger-origin-changed')
    calls=s['calls'];o.need(len(calls)==1 and calls[0]['state']=='returned','initial-ledger-sole-returned-child');call=calls[0]
    o.need(Path(call['launch']['path'])==folder/'children/0000-launch.json' and Path(call['result']['path'])==folder/'children/0000-exit.json','initial-ledger-child-canonical-path')
    launch=o.doc(call['launch']);result=o.doc(call['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--tab-id',str(s['tab_id']),'--pid',str(s['pid']),'--steps','1000']
    o.need(call['argv']==launch['argv']==result['argv']==argv and launch['order']==s['order'] and launch['index']==0 and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':expected_error},'initial-ledger-exact-child-failure')
    o.need(s['start_monotonic']<=launch['launched_monotonic']<=result['exited_monotonic'],'initial-ledger-child-time-order')
    if require_engine_absent:o.need(not (folder/'engine.json').exists() and not (folder/'engine.json').is_symlink(),'initial-ledger-engine-must-not-exist')
    ex=o.doc(worker_exit_ref);worker_folder=Path(worker_exit_ref['path']).parent;request=o.doc(ex['request']);response=o.doc(ex['response']);expected_root=o.PROJECT/'runtime/standalone-workshop-director'
    o.need(worker_folder==expected_root/'attempts'/request['attempt_id'] and Path(worker_exit_ref['path'])==worker_folder/'exit.json' and ex['attempt_id']==request['attempt_id'] and ex['returncode']==0,'initial-ledger-original-worker-exit')
    o.need(ex['request']['path']==str(worker_folder/'request.json') and ex['response']['path']==str(worker_folder/'response.json') and request['kind']=='workshop-worker-request-v1' and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==s['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==request['task']['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==s['order'],'initial-ledger-original-worker-binding')
    o.need(o.doc(request['config_ref'])==request['config'],'initial-ledger-worker-config-changed')
    parent_exit=o.doc(o.ref(worker_folder/'parent-run-exit.json'));parent_output=json.loads(o.raw(parent_exit['stdout']));o.need(parent_exit['returncode']==0 and parent_output['status']=='hold' and parent_output['error']=='execution-child-stopped' and parent_output['last_child_receipt']==call['result'] and parent_output['child'] is None and parent_output['completion'] is None,'initial-ledger-parent-output')
    parent_argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--mode',s['mode'],'--steps','1000']
    o.need(parent_exit['argv']==parent_argv and parent_exit['stderr']['sha256']==__import__('hashlib').sha256(b'').hexdigest() and not o.raw(parent_exit['stderr']),'initial-ledger-parent-argv')
    evidence=[s['order'],s['origin_ref'],call['launch'],call['result'],worker_exit_ref,ex['request'],ex['response'],request['config_ref'],o.ref(worker_folder/'parent-run-exit.json'),parent_exit['stdout'],parent_exit['stderr']]
    return {'order':order,'evidence':evidence,'worker_task_id':request['task']['id']}

def release_overlay(s,release_ref,old_source_refs,*,installed,source_archives=()):
    release=o.doc(release_ref);paths=source_paths();targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==len(NAMES) and {t['target'] for t in targets}==set(paths.values()),'initial-ledger-exact-reviewed-union-targets')
    originals={r['path']:r for r in s['code_refs']};old={r['path']:r for r in old_source_refs};o.need(len(old_source_refs)==len(NAMES)-len(ADDED_NAMES) and len(old)==len(NAMES)-len(ADDED_NAMES),'initial-ledger-exact-old-sources')
    reviewed_runtime(targets)
    current=list(copy.deepcopy(s['code_refs']));archives=[]
    for name,path in paths.items():
        t=next(t for t in targets if t['target']==path);o.raw(t['after']);mode='0755' if name=='review-quality-ocr' else '0644';o.need(t.get('mode')==mode,'initial-ledger-reviewed-source-mode');new={'path':path,'sha256':t['after']['sha256']}
        if name in ADDED_NAMES:o.need(path not in originals and t['old_sha256'] is None,'initial-ledger-new-helper-only');current.append(new)
        else:
            original=originals[path];o.need(t['old_sha256']==original['sha256'],'initial-ledger-old-source-release-binding');matches=[r for r in old_source_refs if Path(r['path']).name==name+'.before'];o.need(len(matches)==1 and matches[0]['sha256']==original['sha256'],'initial-ledger-old-source-missing');o.raw(matches[0]);archives.append({'target':path,'original_sha256':original['sha256'],'archive':matches[0]});current[current.index(original)]=new
        if installed:
            o.raw(new);o.need((Path(path).stat().st_mode & 0o777)==int(mode,8),'initial-ledger-installed-source-mode')
    changed=set(paths.values())
    for ref in s['code_refs']:
        if ref['path'] not in changed:review_entry_code_read(ref,source_archives)
    return current,archives

def plan(original_ref,worker_exit_ref,release_ref,old_source_refs,*,installed=False):
    s,folder=canonical_launcher(original_ref);facts=original_failure(s,worker_exit_ref,require_engine_absent=True);ledgers=ledger_bytes(facts['order']);current,archives=release_overlay(s,release_ref,old_source_refs,installed=installed)
    return {'kind':KIND,'original_launcher':original_ref,'worker_exit':worker_exit_ref,'release':release_ref,'old_sources':archives,'effective_code_refs':current,'ledgers':ledgers,'evidence':facts['evidence'],'order':s['order'],'scope_sha256':s['scope_sha256'],'original_calls':s['calls'],'original_clock':{k:s[k] for k in ('start_monotonic','wall_started_at','boot_identity','clock_contract')},'original_worker_task_id':facts['worker_task_id'],'ui_used':False}

def _verify_initial_recovered(current,proof_ref,*,installed=True,source_archives=()):
    p=o.doc(proof_ref);folder=phase_directory(current);o.need(Path(proof_ref['path'])==folder/'.initial-ledger-origin-recovery'/p['original_launcher']['sha256']/'proof.json' and p['kind']==KIND and current.get(FIELD)==proof_ref,'initial-ledger-canonical-proof')
    original=o.doc(p['original_archive']);o.need(p['original_archive']['sha256']==p['original_launcher']['sha256'] and Path(p['original_launcher']['path'])==folder/'launcher.json' and Path(p['original_archive']['path'])==Path(proof_ref['path']).parent/'original-launcher.json','initial-ledger-original-archive')
    facts=original_failure(original,p['worker_exit'],require_engine_absent=False);old=[x['archive'] for x in p['old_sources']]
    o.need(all(Path(r['path'])==Path(proof_ref['path']).parent/'sources'/Path(r['path']).name for r in old),'initial-ledger-canonical-code-archive')
    codes,archives=release_overlay(original,p['release'],old,installed=installed,source_archives=source_archives)
    o.need(codes==p['effective_code_refs'] and archives==p['old_sources'] and facts['evidence']==p['evidence'] and p['order']==original['order'] and p['scope_sha256']==original['scope_sha256'] and p['ui_used'] is False,'initial-ledger-proof-derived')
    o.need(datetime.fromisoformat(p['at']).utcoffset() is not None and current['order']==original['order'] and current['code_refs']==original['code_refs'] and current['origin_ref']==original['origin_ref'] and current['calls'][:1]==original['calls'],'initial-ledger-original-prefix-changed')
    o.need(all(current[k]==v for k,v in o.doc(original['origin_ref']).items()) and p['original_clock']=={k:original[k] for k in ('start_monotonic','wall_started_at','boot_identity','clock_contract')},'initial-ledger-original-clock-changed')
    o.need(current.get('resolved_errors',[None])[0]=={'error':original['error'],'recovery':proof_ref},'initial-ledger-resolved-error-evidence')
    # The historical byte equality is pinned; later legitimate ledger changes
    # belong to the normal engine's exact ledger_current checks.
    expected_ledgers=[{'company':c['company'],'canonical':{'path':str(Path(c['root'])/'state.json'),'sha256':c['ledger']['sha256']},'snapshot':c['ledger']} for c in facts['order']['companies']]
    o.need(p['ledgers']==expected_ledgers and p['original_worker_task_id']==facts['worker_task_id'],'initial-ledger-historical-ledger-binding')
    for item in p['ledgers']:o.raw(item['snapshot'])
    if not (folder/'engine.json').exists():ledger_bytes(facts['order'])
    return {'kind':KIND,'original_launcher':p['original_launcher'],'proof':proof_ref,'original_error':original['error'],'code_refs':codes,'initial_failed_call':original['calls'][0],'evidence':[proof_ref,p['original_archive'],p['release'],*[x['archive'] for x in p['old_sources']],*p['evidence']]}

def code_refs(current):
    if not current.get(FIELD):return current['code_refs']
    return verify_recovered(current,current[FIELD])['code_refs']

def recover(original_ref,worker_exit_ref,release_ref,old_source_refs):
    s,folder=canonical_launcher(original_ref)
    lease=o.doc(o.ref(Path(s['order']['path']).parent.parent/'state.json'))
    import director
    o.need(lease['dispatch_id']==o.doc(s['order'])['dispatch_id'] and lease['day']==o.doc(s['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'initial-ledger-current-lease-required')
    with (folder/'launcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);o.need(o.ref(Path(original_ref['path']))==original_ref,'initial-ledger-original-changed');p=plan(original_ref,worker_exit_ref,release_ref,old_source_refs,installed=True);base=folder/'.initial-ledger-origin-recovery'/original_ref['sha256'];base.mkdir(parents=True,exist_ok=True);o.canonical(base)
        archive=immutable_bytes(base/'original-launcher.json',o.raw(original_ref));o.need(archive['sha256']==original_ref['sha256'],'initial-ledger-archive-byte-format')
        # Preserve exact original JSON bytes; launcher save() has a distinct format.
        for row in p['old_sources']:row['archive']=immutable_bytes(base/'sources'/Path(row['archive']['path']).name,o.raw(row['archive']))
        p.update(original_archive=archive)
        if (base/'proof.json').exists():
            existing=o.doc(o.ref(base/'proof.json'));o.need({k:v for k,v in existing.items() if k!='at'}==p,'initial-ledger-original-proof-conflict');p=existing
        else:p['at']=datetime.now(timezone.utc).isoformat()
        proof_ref=o.immutable(base/'proof.json',p);new=copy.deepcopy(s);new.update(status='running',**{FIELD:proof_ref});new.pop('error');new['resolved_errors']=[{'error':s['error'],'recovery':proof_ref}]
        o.need(o.ref(Path(original_ref['path']))==original_ref,'initial-ledger-original-changed');verify_recovered(new,proof_ref)
        import complaint_execution_launcher as launcher
        launcher.save(Path(original_ref['path']),new)
        return {'kind':KIND,'state':'reconciled','launcher':o.ref(Path(original_ref['path'])),'proof':proof_ref,'ui_used':False}


PLAN_FIELD='initial_pure_plan_recovery'
PLAN_KIND='complaint-initial-pure-plan-recovery-v1'
PLAN_KIND2='complaint-initial-pure-plan-unapplied-recovery-v2'
PLAN_NAMES=('complaint_execution_ports.py','initial_ledger_recovery.py','complaint_execution.py','complaint_execution_orchestration.py')

def pending_rechecks(state,full_plan,workflow):
    expected=[key for key,task in state['tasks'].items() if task['status']!='resolved']
    o.need(full_plan['recheck_ids']==expected,'complaint-parent-full-plan-rechecks-changed')
    out=[]
    for key in expected:
        task=state['tasks'][key]
        if task['status']=='draft_ready':
            o.need(workflow.next_action(state,key)=='draft-only-stop','complaint-parent-draft-not-final')
            # A finished draft has no platform result to recheck. Its previous
            # message receipt is not an input to today's collection plan.
        else:out.append(key)
    return out

def business_plan_scope(rows):
    # The complete original full_plan remains in immutable proof/plan artifacts.
    # Instant KB retrieval is analysis context, never identity for a pre-input
    # plan failure. Every other plan field must match, including next_actions.
    result=copy.deepcopy(rows)
    for row in result:row['full_plan'].pop('appeal_case_memory',None)
    return result

def business_plan(state,day,workflow):
    # Exact workflow.plan non-KB projection; no KB reader on historical guards.
    from datetime import date,timedelta
    date.fromisoformat(day)
    return {'company':state['company'],'groupid':state['groupid'],'start':state['next_start'],
            'end_exclusive':day,'end':(date.fromisoformat(day)-timedelta(days=1)).isoformat(),
            'has_new_dates':state['next_start']<day,
            'recheck_ids':[key for key,task in state['tasks'].items() if task['status']!='resolved'],
            'next_actions':{key:workflow.next_action(state,key) for key,task in state['tasks'].items() if task['status']!='resolved' or not workflow.final_screenshot(state,task) or not task['wecom']},
            'xlsx_dirty':state.get('xlsx_dirty',False),'mode':state['mode'],
            'browser_backend':state.get('browser_backend','codex-existing-extension'),
            'submit_enabled':False,'wecom_target':'测试群请忽略'}

def business_scope(order):
    import workflow
    rows=[]
    for company in order['companies']:
        state=o.doc(company['ledger']);full=business_plan(state,order['day'],workflow);pending=pending_rechecks(state,full,workflow)
        o.need((full['start'],full['end_exclusive'],pending)==(company['start'],company['end_exclusive'],company['recheck_ids']),'initial-plan-order-scope-changed')
        rows.append({'company':company['company'],'ledger':company['ledger'],'full_plan':full,'pending_rechecks':pending})
    return rows

def plan_scope(order):
    # Replay the unchanged original full workflow plan. Never replace its list
    # with the smaller existing-result backlog in the saved plan artifact.
    import workflow
    rows=[]
    for company in order['companies']:
        state=o.doc(company['ledger']);full=workflow.plan(state,today=order['day'])
        pending=pending_rechecks(state,full,workflow)
        o.need((full['start'],full['end_exclusive'],pending)==(company['start'],company['end_exclusive'],company['recheck_ids']),'initial-plan-order-scope-changed')
        rows.append({'company':company['company'],'ledger':company['ledger'],'full_plan':full,'pending_rechecks':pending})
    return rows

def pure_plan_engine(engine,parent,order):
    folder=phase_directory(parent)
    o.need(not order['companies'][0]['skipped'] and set(engine)=={'kind','order','scope_sha256','status','phase','index','companies','calls','business_journals','error'} and engine['kind']=='complaint-execution-v1' and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'] and engine['status']=='hold' and engine['error']=='complaint-parent-plan-changed' and engine['phase']=='plan' and engine['index']==0 and engine['companies']==[{'artifacts':{},'phase':'plan'} for _ in order['companies']] and engine['business_journals']==[],'initial-plan-sole-empty-engine-required')
    o.need(len(engine['calls'])==1,'initial-plan-sole-failed-call-required');call=engine['calls'][0]
    context={'order':order,'company':order['companies'][0],'artifacts':{},'folder':str(folder/'companies/0'),'phase':'plan'}
    o.need(set(call)=={'step','company_index','context','state','intent_at','error'} and call['step']=='plan' and call['company_index']==0 and call['context']==context and call['state']=='failed' and call['error']=='complaint-parent-plan-changed','initial-plan-exact-failure-required')
    o.need(datetime.fromisoformat(call['intent_at']).utcoffset() is not None,'initial-plan-aware-intent-required')
    return call

def plan_worker(parent,worker_exit_ref,*,engine_expected=None):
    folder=phase_directory(parent);order=o.doc(parent['order']);calls=parent['calls'];o.need(len(calls)==2 and all(c['state']=='returned' for c in calls),'initial-plan-exact-two-outer-calls')
    call=calls[1];launch=o.doc(call['launch']);result=o.doc(call['result'])
    argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(call['argv']==launch['argv']==result['argv']==argv and launch['order']==parent['order'] and launch['index']==1 and result['launch']==call['launch'] and Path(call['launch']['path'])==folder/'children/0001-launch.json' and Path(call['result']['path'])==folder/'children/0001-exit.json' and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':'complaint-parent-plan-changed'},'initial-plan-exact-child-failure')
    first=o.doc(calls[0]['result']);o.need(parent['start_monotonic']<=first['exited_monotonic']<=launch['launched_monotonic']<=result['exited_monotonic'],'initial-plan-time-order')
    ex=o.doc(worker_exit_ref);wf=Path(worker_exit_ref['path']).parent;request=o.doc(ex['request']);response=o.doc(ex['response'])
    o.need(wf==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and Path(worker_exit_ref['path'])==wf/'exit.json' and ex['attempt_id']==request['attempt_id'] and ex['returncode']==0 and ex['request']['path']==str(wf/'request.json') and ex['response']['path']==str(wf/'response.json'),'initial-plan-worker-natural-exit')
    o.need(request['kind']=='workshop-worker-request-v1' and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==request['task']['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'initial-plan-worker-binding')
    pe=o.ref(wf/'parent-run-exit.json');output=o.doc(pe);value=json.loads(o.raw(output['stdout']))
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(output['argv']==expected and output['returncode']==0 and not o.raw(output['stderr']) and value['status']=='hold' and value['error']=='execution-child-stopped' and value['last_child_receipt']==call['result'] and value['child'] is None and value['completion'] is None and value['engine']==(engine_expected or o.ref(folder/'engine.json')),'initial-plan-parent-output')
    return [worker_exit_ref,ex['request'],ex['response'],request['config_ref'],pe,output['stdout'],output['stderr'],call['launch'],call['result']]

def plan_overlay(prior,release_ref,old_refs,*,installed,source_archives=()):
    release=o.doc(release_ref);paths={source_paths()[name] for name in PLAN_NAMES};targets=release['targets']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==paths,'initial-plan-exact-four-source-tip')
    codes=copy.deepcopy(prior['code_refs']);old={Path(r['path']).name:r for r in old_refs};o.need(set(old)=={n+'.before' for n in PLAN_NAMES} and len(old_refs)==4,'initial-plan-four-before-archives')
    archives=[]
    for target in targets:
        path=target['target'];before=next(r for r in codes if r['path']==path);archive=old[Path(path).name+'.before'];o.need(target['old_sha256']==before['sha256']==archive['sha256'] and target.get('mode')=='0644','initial-plan-source-tip-binding');o.raw(archive);o.raw(target['after']);replacement={'path':path,'sha256':target['after']['sha256']};codes[codes.index(before)]=replacement;archives.append({'target':path,'archive':archive})
    for ref in codes:
        if installed or ref['path'] not in paths:review_entry_code_read(ref,source_archives)
    if installed:
        for path in paths:o.need((Path(path).stat().st_mode & 0o777)==0o644,'initial-plan-source-mode')
    return codes,sorted(archives,key=lambda x:x['target'])

def no_business_artifacts(folder):
    for name in ('companies','receipts','handoffs','acceptances'):
        path=folder/name;o.need(not path.is_symlink() and not any(p.is_file() or p.is_symlink() for p in path.rglob('*')),'initial-plan-business-artifact-present')

def plan_second(original_ref,engine_ref,worker_exit_ref,release_ref,old_refs,*,installed=False,quiet=True):
    parent,folder=canonical_launcher(original_ref);order=o.validate(parent['order'])
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and not parent.get('child') and not parent.get('completion') and not parent.get(PLAN_FIELD) and parent.get(FIELD),'initial-plan-exact-second-hold')
    prior=_verify_initial_recovered(parent,parent[FIELD],installed=False)
    o.need(parent['calls'][0]==prior['initial_failed_call'],'initial-plan-first-history-changed')
    o.need(Path(engine_ref['path'])==folder/'engine.json','initial-plan-canonical-engine');engine=o.doc(engine_ref);call=pure_plan_engine(engine,parent,order)
    evidence=plan_worker(parent,worker_exit_ref);ledgers=ledger_bytes(order);scope=plan_scope(order)
    # The first plan never returned a receipt or any business artifacts.
    if quiet:no_business_artifacts(folder)
    codes,archives=plan_overlay(prior,release_ref,old_refs,installed=installed)
    return {'kind':PLAN_KIND,'original_launcher':original_ref,'original_engine':engine_ref,'worker_exit':worker_exit_ref,'prior_proof':parent[FIELD],'release':release_ref,'old_sources':archives,'effective_code_refs':codes,'ledgers':ledgers,'plan_scope':scope,'order':parent['order'],'original_calls':parent['calls'],'failed_engine_call':call,'evidence':evidence,'ui_used':False}

def _verify_plan_recovered(current,proof_ref,*,installed=True,source_archives=()):
    p=o.doc(proof_ref)
    if p.get('kind')==PLAN_KIND2:return verify_unapplied_recovered(current,proof_ref,installed=installed,source_archives=source_archives)
    folder=phase_directory(current);base=folder/'.initial-pure-plan-recovery'/p['original_launcher']['sha256']
    o.need(p['kind']==PLAN_KIND and current.get(PLAN_FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json','initial-plan-canonical-proof')
    original=o.doc(p['launcher_archive']);engine=o.doc(p['engine_archive'])
    o.need(p['launcher_archive']['sha256']==p['original_launcher']['sha256'] and p['engine_archive']['sha256']==p['original_engine']['sha256'] and Path(p['original_launcher']['path'])==folder/'launcher.json' and Path(p['original_engine']['path'])==folder/'engine.json' and Path(p['launcher_archive']['path'])==base/'original-launcher.json' and Path(p['engine_archive']['path'])==base/'original-engine.json','initial-plan-archive-binding')
    # Reconstruct the historical plan without using current mutable engine/ledger.
    prior=_verify_initial_recovered(original,original[FIELD],installed=False,source_archives=source_archives);order=o.validate(original['order']);failed=pure_plan_engine(engine,original,order)
    o.need(original['status']=='hold' and original.get('error')=='execution-child-stopped' and not original.get('child') and not original.get('completion') and len(original['calls'])==2 and original['calls'][0]==prior['initial_failed_call'] and p['prior_proof']==original[FIELD],'initial-plan-original-hold-binding')
    # All worker/result refs are immutable; compare exact recorded original facts.
    # Worker output's engine SHA is the archived original, never the evolving engine.
    evidence=plan_worker_archived(original,p['worker_exit'],p['original_engine'])
    olds=[x['archive'] for x in p['old_sources']];o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in olds),'initial-plan-source-archive-path')
    codes,archives=plan_overlay(prior,p['release'],olds,installed=installed,source_archives=source_archives)
    expected_ledgers=[{'company':c['company'],'canonical':{'path':str(Path(c['root'])/'state.json'),'sha256':c['ledger']['sha256']},'snapshot':c['ledger']} for c in order['companies']]
    o.need(p['effective_code_refs']==codes and p['old_sources']==archives and p['failed_engine_call']==failed and p['original_calls']==original['calls'] and p['evidence']==evidence and p['ledgers']==expected_ledgers and business_plan_scope(p['plan_scope'])==business_scope(order) and p['order']==original['order'] and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'initial-plan-derived-proof')
    o.need(current['calls'][:2]==original['calls'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and current.get(FIELD)==original[FIELD] and current.get('resolved_errors',[])==original['resolved_errors']+[{'error':original['error'],'recovery':proof_ref}],'initial-plan-original-prefix-changed')
    return {**prior,'kind':PLAN_KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':original['calls'],'failed_engine_call':failed,'evidence':[*prior['evidence'],proof_ref,p['launcher_archive'],p['engine_archive'],p['release'],*olds,*evidence]}

def plan_worker_archived(parent,worker_exit_ref,original_engine):
    # Same validator, explicit immutable original engine identity at replay time.
    return plan_worker(parent,worker_exit_ref,engine_expected=original_engine)

def verify_recovered(current,proof_ref):
    proof=o.doc(proof_ref)
    if proof.get("kind")==EXPECTED_FILTER_KIND and proof.get("facts",{}).get("release")==None:return _verify_current_filter_ready(current,proof_ref)
    if o.doc(proof_ref).get('kind')=='verified-pre-native-page-window-focus-recovery-v1':
        from review_capture_focus import verify_panel_recovered
        return verify_panel_recovered(current,proof_ref)
    o.need(current.get(FIELD)==proof_ref,'initial-ledger-proof-field-binding')
    if current.get(REVIEW_FRAMES_FIELD):
        from review_frames_preinput_recovery import verify_recovered as verified_frames
        return verified_frames(current,current[REVIEW_FRAMES_FIELD])
    if current.get(REVIEW_ENTRY_FIELD):
        from review_entry_preinput_recovery import verify_recovered as verified_entry
        return verified_entry(current,current[REVIEW_ENTRY_FIELD])
    o.need(current.get(FIELD)==proof_ref,'initial-ledger-proof-field-binding')
    if current.get(PLAN_FIELD):return _verify_plan_recovered(current,current[PLAN_FIELD])
    return _verify_initial_recovered(current,proof_ref)

def engine_calls(engine):
    if engine.get(PLAN_FIELD) and o.doc(engine[PLAN_FIELD]).get('kind')=='verified-pre-native-page-window-focus-recovery-v1':
        from review_capture_focus import panel_engine_calls
        return panel_engine_calls(engine)
    if engine.get(REVIEW_FRAMES_FIELD):
        from review_frames_preinput_recovery import verified_engine_calls
        return verified_engine_calls(engine)
    if engine.get(REVIEW_ENTRY_FIELD):
        from review_entry_preinput_recovery import verified_engine_calls
        return verified_engine_calls(engine)
    if not engine.get(PLAN_FIELD):return engine['calls']
    parent=o.doc(o.ref(phase_directory(engine)/'launcher.json'))
    o.need(engine[PLAN_FIELD]==parent.get(PLAN_FIELD) and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'initial-plan-engine-parent-proof')
    admitted=verify_recovered(parent,parent[FIELD]);o.need(engine['calls'][:1]==[admitted['failed_engine_call']] and engine.get('resolved_errors',[None])[0]=={'error':'complaint-parent-plan-changed','recovery':engine[PLAN_FIELD]},'initial-plan-engine-failure-prefix')
    return engine['calls'][1:]

def recovered_pair(parent,engine,proof_ref):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value,error in ((parent,'execution-child-stopped'),(engine,'complaint-parent-plan-changed')):
        value.update(status='running',**{PLAN_FIELD:proof_ref});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof_ref})
    return parent,engine

def exact_metadata_state(path,original_archive,new_value):
    current=o.ref(path);raw=o.raw(current);new_bytes=(json.dumps(new_value,ensure_ascii=False,indent=2)+'\n').encode()
    o.need(raw in (o.raw(original_archive),new_bytes),'initial-plan-progressed-no-reset')
    return current

def recover_second(original_ref,engine_ref,worker_exit_ref,release_ref,old_refs):
    # Locks match the ordinary parent/engine writers. No child invocation.
    folder=Path(original_ref['path']).parent;o.canonical(folder)
    with (folder/'launcher.lock').open('a') as plock, (folder/'engine.lock').open('a') as elock:
        for lock in (plock,elock):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        base=folder/'.initial-pure-plan-recovery'/original_ref['sha256']
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof)
            o.need(p['original_launcher']==original_ref and p['original_engine']==engine_ref and p['worker_exit']==worker_exit_ref and p['release']==release_ref,'initial-plan-original-recovery-inputs')
            # Retry only this exact metadata publication, never a progressed run.
            original=o.doc(p['launcher_archive']);engine=o.doc(p['engine_archive']);new_parent,new_engine=recovered_pair(original,engine,proof)
            exact_metadata_state(folder/'launcher.json',p['launcher_archive'],new_parent);exact_metadata_state(folder/'engine.json',p['engine_archive'],new_engine)
            o.need(sorted((Path(r['path']).name,r['sha256']) for r in old_refs)==sorted((Path(x['archive']['path']).name,x['archive']['sha256']) for x in p['old_sources']),'initial-plan-original-source-inputs')
            _verify_plan_recovered(new_parent,proof);ledger_bytes(o.validate(original['order']));no_business_artifacts(folder)
        else:
            original=o.doc(original_ref);engine=o.doc(engine_ref)
            lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'));import director
            o.need(lease['dispatch_id']==o.doc(original['order'])['dispatch_id'] and lease['day']==o.doc(original['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'initial-plan-current-lease-required')
            p=plan_second(original_ref,engine_ref,worker_exit_ref,release_ref,old_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True);o.canonical(base/'sources')
            p['launcher_archive']=immutable_bytes(base/'original-launcher.json',o.raw(original_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref))
            for row in p['old_sources']:row['archive']=immutable_bytes(base/'sources'/Path(row['archive']['path']).name,o.raw(row['archive']))
            p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p);new_parent,new_engine=recovered_pair(original,engine,proof)
            _verify_plan_recovered(new_parent,proof)
        o.need(folder==phase_directory(original),'initial-plan-canonical-recovery-folder')
        lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(original['order'])['dispatch_id'] and lease['day']==o.doc(original['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'initial-plan-current-lease-required')
        before_parent=exact_metadata_state(folder/'launcher.json',p['launcher_archive'],new_parent);before_engine=exact_metadata_state(folder/'engine.json',p['engine_archive'],new_engine)
        o.need(o.doc(before_parent) in (original,new_parent) and o.doc(before_engine) in (engine,new_engine),'initial-plan-progressed-no-reset')
        import complaint_execution_launcher as launcher
        o.raw(before_parent);o.raw(before_engine)
        if o.doc(before_engine)!=new_engine:launcher.save(folder/'engine.json',new_engine)
        if o.doc(before_parent)!=new_parent:launcher.save(folder/'launcher.json',new_parent)
        return {'kind':PLAN_KIND,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}



def verify_failed_metadata_cli(reference,unapplied):
    receipt=o.doc(reference);intent=o.doc(receipt['intent']);argv=receipt['argv'];worker=o.doc(o.doc(unapplied['worker_exit'])['request'])
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),source_paths()['initial_ledger_recovery.py'],'--plan-only','--launcher',unapplied['original_launcher']['path'],'--original-sha256',unapplied['original_launcher']['sha256'],'--engine-sha256',unapplied['original_engine']['sha256'],'--worker-exit',unapplied['worker_exit']['path'],'--worker-exit-sha256',unapplied['worker_exit']['sha256'],'--release',unapplied['release']['path'],'--release-sha256',unapplied['release']['sha256']]
    o.need(receipt['kind']=='authorized-pure-plan-metadata-recovery-cli-v1' and receipt['returncode']==2 and receipt['stderr']=='' and json.loads(receipt['stdout'])=={'ok':False,'error':'initial-plan-derived-proof'} and receipt['ui_used'] is False and intent['kind']=='authorized-pure-plan-metadata-recovery-intent-v1' and intent['argv']==argv and intent['release']==unapplied['release'] and intent['ui_used'] is False and intent['attempt']==3 and intent['task_id']==worker['task']['id'],'initial-plan-v2-exact-natural-cli-failure')
    o.need(argv[:len(expected)]==expected and len(argv)==len(expected)+8,'initial-plan-v2-original-cli-argv')
    args=argv[len(expected):];originals={Path(x['archive']['path']).name:x['archive']['sha256'] for x in unapplied['old_sources']}
    o.need(args[::2]==['--old-source']*4,'initial-plan-v2-original-cli-source-args')
    sources=[json.loads(x) for x in args[1::2]]
    o.need([Path(r['path']).name for r in sources]==[name+'.before' for name in PLAN_NAMES] and all(r['sha256']==originals[Path(r['path']).name] for r in sources),'initial-plan-v2-original-cli-sources')
    for ref in sources:o.raw(ref)
    return [reference,receipt['intent'],*sources]

def unapplied_base(current,reference,*,source_archives=()):
    p=o.doc(reference);o.need(p['kind']==PLAN_KIND,'initial-plan-v2-only-unapplied-v1')
    # Explicit historical verification with no installed old-helper claim.
    proxy=copy.deepcopy(current);proxy[PLAN_FIELD]=reference
    original=o.doc(p['launcher_archive']);proxy['resolved_errors']=original['resolved_errors']+[{'error':original['error'],'recovery':reference}]
    return p,_verify_plan_recovered(proxy,reference,installed=False,source_archives=source_archives)

def helper_tip(admitted,release_ref,before_ref,*,installed,source_archives=()):
    release=o.doc(release_ref);path=source_paths()['initial_ledger_recovery.py'];targets=release['targets']
    o.need(release['kind']=='supervisor-reviewed-source-release-v1' and len(targets)==1 and targets[0]['target']==path and targets[0]['mode']=='0644','initial-plan-v2-exact-helper-release')
    target=targets[0];codes=copy.deepcopy(admitted['code_refs']);old=next(r for r in codes if r['path']==path)
    o.need(before_ref['sha256']==target['old_sha256']==old['sha256'] and Path(before_ref['path']).name=='initial_ledger_recovery.py.before','initial-plan-v2-admission-tip-binding')
    o.raw(before_ref);o.raw(target['after']);codes[codes.index(old)]={'path':path,'sha256':target['after']['sha256']}
    for ref in codes:
        if installed or ref['path']!=path:review_entry_code_read(ref,source_archives)
    if installed:o.need((Path(path).stat().st_mode & 0o777)==0o644,'initial-plan-v2-helper-mode')
    return codes

def plan_unapplied(original_ref,engine_ref,worker_exit_ref,unapplied_ref,failed_cli_ref,release_ref,before_ref,*,installed=False):
    current,folder=canonical_launcher(original_ref);p=o.doc(unapplied_ref)
    o.need(current['status']=='hold' and current.get('error')=='execution-child-stopped' and not current.get(PLAN_FIELD) and p['original_launcher']==original_ref and p['original_engine']==engine_ref and p['worker_exit']==worker_exit_ref,'initial-plan-v2-unapplied-original-binding')
    original=o.doc(p['launcher_archive']);engine=o.doc(p['engine_archive']);o.need(o.raw(original_ref)==o.raw(p['launcher_archive']) and o.raw(engine_ref)==o.raw(p['engine_archive']),'initial-plan-v2-original-bytes-changed')
    _,admitted=unapplied_base(current,unapplied_ref);evidence=verify_failed_metadata_cli(failed_cli_ref,p);ledger_bytes(o.validate(current['order']));no_business_artifacts(folder);codes=helper_tip(admitted,release_ref,before_ref,installed=installed)
    return {'kind':PLAN_KIND2,'original_launcher':original_ref,'original_engine':engine_ref,'worker_exit':worker_exit_ref,'unapplied_proof':unapplied_ref,'failed_recovery_cli':failed_cli_ref,'helper_release':release_ref,'helper_before':before_ref,'effective_code_refs':codes,'evidence':evidence,'ui_used':False}

def verify_unapplied_recovered(current,proof_ref,*,installed=True,source_archives=()):
    p=o.doc(proof_ref);folder=phase_directory(current);base=folder/'.initial-pure-plan-recovery-v2'/p['original_launcher']['sha256']
    o.need(p['kind']==PLAN_KIND2 and current.get(PLAN_FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and Path(p['helper_before']['path'])==base/'sources/initial_ledger_recovery.py.before' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'initial-plan-v2-canonical-proof')
    old,admitted=unapplied_base(current,p['unapplied_proof'],source_archives=source_archives);o.need(p['original_launcher']==old['original_launcher'] and p['original_engine']==old['original_engine'] and p['worker_exit']==old['worker_exit'],'initial-plan-v2-original-proof-binding')
    original=o.doc(old['launcher_archive']);o.need(current['resolved_errors']==original['resolved_errors']+[{'error':original['error'],'recovery':proof_ref}],'initial-plan-v2-resolved-error-binding')
    evidence=verify_failed_metadata_cli(p['failed_recovery_cli'],old);codes=helper_tip(admitted,p['helper_release'],p['helper_before'],installed=installed,source_archives=source_archives)
    o.need(p['effective_code_refs']==codes and p['evidence']==evidence,'initial-plan-v2-derived-proof')
    return {**admitted,'kind':PLAN_KIND2,'proof':proof_ref,'code_refs':codes,'evidence':[*admitted['evidence'],proof_ref,p['unapplied_proof'],p['helper_release'],p['helper_before'],*evidence]}

def recover_unapplied(original_ref,engine_ref,worker_exit_ref,release_ref,old_refs,unapplied_ref,failed_cli_ref):
    o.need(len(old_refs)==1,'initial-plan-v2-one-helper-before');folder=Path(original_ref['path']).parent;o.canonical(folder)
    with (folder/'launcher.lock').open('a') as plock,(folder/'engine.lock').open('a') as elock:
        for lock in (plock,elock):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        base=folder/'.initial-pure-plan-recovery-v2'/original_ref['sha256'];old=o.doc(unapplied_ref);original=o.doc(old['launcher_archive']);engine=o.doc(old['engine_archive'])
        lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(original['order'])['dispatch_id'] and lease['day']==o.doc(original['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'initial-plan-v2-current-lease-required')
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof)
            o.need(p['original_launcher']==original_ref and p['original_engine']==engine_ref and p['worker_exit']==worker_exit_ref and p['unapplied_proof']==unapplied_ref and p['failed_recovery_cli']==failed_cli_ref and p['helper_release']==release_ref and p['helper_before']['sha256']==old_refs[0]['sha256'],'initial-plan-v2-original-inputs')
        else:
            p=plan_unapplied(original_ref,engine_ref,worker_exit_ref,unapplied_ref,failed_cli_ref,release_ref,old_refs[0],installed=True)
            base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True);o.canonical(base/'sources');p['helper_before']=immutable_bytes(base/'sources/initial_ledger_recovery.py.before',o.raw(old_refs[0]));p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p)
        new_parent,new_engine=recovered_pair(original,engine,proof)
        # Only exact original or exact partially-published metadata may resume.
        before_parent=exact_metadata_state(folder/'launcher.json',old['launcher_archive'],new_parent);before_engine=exact_metadata_state(folder/'engine.json',old['engine_archive'],new_engine)
        ledger_bytes(o.validate(original['order']));no_business_artifacts(folder);verify_unapplied_recovered(new_parent,proof)
        import complaint_execution_launcher as launcher
        o.raw(before_parent);o.raw(before_engine)
        if o.doc(before_engine)!=new_engine:launcher.save(folder/'engine.json',new_engine)
        if o.doc(before_parent)!=new_parent:launcher.save(folder/'launcher.json',new_parent)
        return {'kind':PLAN_KIND2,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

# Independent pre-engine constructor admission; never a ledger recovery alias.
PREENGINE_FIELD='preengine_constructor_recovery'
PREENGINE_KIND='complaint-preengine-acquisition-serialization-recovery-v1'
PREENGINE_NAMES=('complaint_execution_ports.py','initial_ledger_recovery.py','complaint_execution_launcher.py','complaint_execution.py','complaint_execution_orchestration.py')
def preengine_paths():
    return {n:str(o.PROJECT/('skills/workshop-director/scripts/' if n in ('complaint_execution_launcher.py','complaint_execution_orchestration.py') else 'skills/negative-review-complaints/scripts/')/n)for n in PREENGINE_NAMES}
def preengine_constructor_facts(original_ref,worker_exit_ref,*,require_engine_absent=True,original_archive=None):
    raw=o.raw(original_archive or original_ref);o.need(__import__('hashlib').sha256(raw).hexdigest()==original_ref['sha256'],'preengine-original-archive-sha');s=json.loads(raw);folder=o.location(s['order']);order=o.validate(s['order'])
    o.need(Path(original_ref['path'])==folder/'launcher.json' and s['kind']=='role-execution-launcher-v1'and s['status']=='hold'and s.get('error')=='execution-child-stopped'and not s.get('child')and not s.get('completion')and not s.get(PREENGINE_FIELD)and not s.get(FIELD),'preengine-exact-constructor-hold')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items())and s['mode']=='acceptance'and s['origin']=='fresh','preengine-origin-unchanged')
    o.need(len(s['calls'])==1 and s['calls'][0]['state']=='returned','preengine-sole-returned-child');call=s['calls'][0];launch=o.doc(call['launch']);ex=o.doc(call['result'])
    argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--tab-id',str(s['tab_id']),'--pid',str(s['pid']),'--steps','1000']
    o.need(call['launch']['path']==str(folder/'children/0000-launch.json')and call['result']['path']==str(folder/'children/0000-exit.json')and launch['index']==0 and launch['order']==s['order']and call['argv']==launch['argv']==ex['argv']==argv and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':'complaint-parent-acquisition-origin'},'preengine-exact-child-failure')
    o.need(s['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'preengine-time-order')
    if require_engine_absent:o.need(not (folder/'engine.json').exists()and not (folder/'engine.json').is_symlink(),'preengine-engine-absent')
    worker=o.doc(worker_exit_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_exit_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and Path(worker_exit_ref['path'])==attempt/'exit.json'and worker['attempt_id']==request['attempt_id']and worker['returncode']==0 and request['task']['flow']==o.FLOW and request['task']['day']==order['day']and request['context']['order']==s['order']and response['task_id']==request['task']['id']and response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['context']['order']==s['order'],'preengine-worker-failed-structured-binding')
    px=o.doc(o.ref(attempt/'parent-run-exit.json'));output=json.loads(o.raw(px['stdout']));o.need(px['returncode']==0 and output['status']=='hold'and output['error']=='execution-child-stopped'and output['last_child_receipt']==call['result']and output.get('child')is None and not o.raw(px['stderr']),'preengine-parent-exit-binding')
    o.need(px['argv']==[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--mode',s['mode'],'--steps','1000'],'preengine-parent-argv')
    report=o.doc(order['daily_completion']);parent=o.doc(report['verification_parent_state']);proof=parent['completion_proof'];batch=o.doc(proof['batch']);outbox=o.doc(proof['outbox']);registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']}
    o.need(parent['status']=='complete'and report['day']==order['day']and proof['all_expected_client_confirmed']is True,'preengine-daily-closed-binding')
    from complaint_execution_ports import validated_acquisition_origin
    origins=[validated_acquisition_origin(row,batch,proof['batch'],outbox,proof['outbox'],registry)for row in batch['companies']if row.get('status')!='skipped']
    o.need(len(origins)==2 and any(o.raw(x['copy'])!=o.raw(x['original'])for x in origins),'preengine-real-serialization-difference')
    evidence=[s['order'],s['origin_ref'],call['launch'],call['result'],worker_exit_ref,worker['request'],worker['response'],o.ref(attempt/'parent-run-exit.json'),px['stdout'],px['stderr'],order['daily_completion'],report['verification_parent_state'],proof['batch'],proof['outbox']]
    return {'original':s,'order':order,'origins':origins,'evidence':evidence,'failed_calls':[call],'worker_task_id':request['task']['id']}
def preengine_overlay(original,release_ref,old_refs,*,installed):
    release=o.doc(release_ref);paths=preengine_paths();targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-preengine-acquisition-serialization-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and len(targets)==5 and {t['target']for t in targets}==set(paths.values()),'preengine-reviewed-five-target-release')
    old={r['path']:r for r in original['code_refs']};o.need(len(old)==len(original['code_refs'])==160 and len(old_refs)==5,'preengine-original160-five-archives');before={Path(r['path']).name:r for r in old_refs};o.need(set(before)=={n+'.before'for n in PREENGINE_NAMES},'preengine-exact-before-names');codes=copy.deepcopy(original['code_refs']);archives=[]
    for t in targets:
        name=Path(t['target']).name;b=before[name+'.before'];o.need(b['sha256']==old[t['target']]['sha256']==t['old_sha256']==t['before']['sha256']and o.raw(b)==o.raw(t['before']),'preengine-before-cas');o.raw(t['after'])
        if installed:o.need(o.ref(t['target'])['sha256']==t['after']['sha256'],'preengine-current-target-sha')
        for index,r in enumerate(codes):
            if r['path']==t['target']:codes[index]={'path':t['target'],'sha256':t['after']['sha256']}
        archives.append({'target':t['target'],'archive':b})
    for r in codes:
        if r['path']not in paths.values():o.raw(r)
    return codes,archives

def plan_preengine_constructor(original_ref,worker_exit_ref,release_ref,old_refs,*,installed=False):
    facts=preengine_constructor_facts(original_ref,worker_exit_ref);codes,archives=preengine_overlay(facts['original'],release_ref,old_refs,installed=installed)
    return {'kind':PREENGINE_KIND,'original_launcher':original_ref,'worker_exit':worker_exit_ref,'release':release_ref,'old_sources':archives,'effective_code_refs':codes,'origins':facts['origins'],'evidence':facts['evidence'],'failed_calls':facts['failed_calls'],'worker_task_id':facts['worker_task_id'],'order':facts['original']['order'],'ui_used':False}
def repaired_preengine_constructor(original,proof_ref):
    new=copy.deepcopy(original);new['status']='running';new.pop('error',None);new[PREENGINE_FIELD]=proof_ref;new['resolved_errors']=[*original.get('resolved_errors',[]),{'error':original['error'],'recovery':proof_ref}];return new

def verify_preengine_constructor(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);base=o.location(p['order'])/'.preengine-constructor-recovery'/p['original_launcher']['sha256'];o.need(p['kind']==PREENGINE_KIND and current.get(PREENGINE_FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json'and p['original_archive']['path']==str(base/'original-launcher.json'),'preengine-canonical-proof')
    o.need(all(Path(a['archive']['path'])==base/'sources'/(Path(a['target']).name+'.before')for a in p['old_sources'])and datetime.fromisoformat(p['at']).utcoffset()is not None,'preengine-proof-archive-paths-time')
    facts=preengine_constructor_facts(p['original_launcher'],p['worker_exit'],require_engine_absent=False,original_archive=p['original_archive']);o.need(p['order']==facts['original']['order']and p['worker_task_id']==facts['worker_task_id'],'preengine-proof-order-worker');codes,archives=preengine_overlay(facts['original'],p['release'],[x['archive']for x in p['old_sources']],installed=installed)
    o.need(codes==p['effective_code_refs']and archives==p['old_sources']and facts['origins']==p['origins']and facts['evidence']==p['evidence']and facts['failed_calls']==p['failed_calls']and p['ui_used']is False,'preengine-derived-proof')
    original=facts['original'];expected=repaired_preengine_constructor(original,proof_ref)
    for k in ('kind','order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','tab_id','pid','code_refs','origin_ref','resolved_errors',PREENGINE_FIELD):o.need(current.get(k)==expected.get(k),'preengine-original-binding')
    o.need(current['calls'][:1]==original['calls']and all(c.get('state')in ('unknown','returned')for c in current['calls'][1:]),'preengine-original-failed-prefix')
    return {'kind':PREENGINE_KIND,'code_refs':codes,'failed_calls':facts['failed_calls'],'evidence':[proof_ref,p['original_archive'],p['release'],*[x['archive']for x in p['old_sources']],*p['evidence']]}

def recover_preengine_constructor(original_ref,worker_exit_ref,release_ref,old_refs):
    path=Path(original_ref['path']);folder=path.parent;base=folder/'.preengine-constructor-recovery'/original_ref['sha256']
    original=json.loads(o.raw(o.ref(base/'original-launcher.json')) if (base/'original-launcher.json').exists() else o.raw(original_ref));order=o.validate(original['order']);lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'))
    import director
    o.need(lease['dispatch_id']==order['dispatch_id']and lease['day']==order['day']and lease['phase']in ('running','attention')and director.current(lease)['role']==o.ROLE,'preengine-live-lease-required')
    with (folder/'launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_launcher']==original_ref and p['worker_exit']==worker_exit_ref and p['release']==release_ref and sorted((Path(x['archive']['path']).name,x['archive']['sha256'])for x in p['old_sources'])==sorted((Path(x['path']).name,x['sha256'])for x in old_refs),'preengine-continuation-authority-conflict');original=o.doc(p['original_archive']);expected=repaired_preengine_constructor(original,proof);current=json.loads(path.read_bytes());o.need(current==original or current==expected,'preengine-continuation-current-conflict');verify_preengine_constructor(expected,proof)
            if current==original:__import__('complaint_execution_launcher').save(path,expected)
            return {'kind':PREENGINE_KIND,'state':'reconciled','launcher':o.ref(path),'proof':proof,'ui_used':False}
        o.need(o.ref(path)==original_ref,'preengine-original-current-cas');p=plan_preengine_constructor(original_ref,worker_exit_ref,release_ref,old_refs,installed=True);base.mkdir(parents=True,exist_ok=True);p['original_archive']=immutable_bytes(base/'original-launcher.json',o.raw(original_ref));o.immutable(base/'intent.json',{'kind':PREENGINE_KIND,'original_launcher':original_ref,'worker_exit':worker_exit_ref,'release':release_ref,'old_refs':old_refs,'ui_used':False})
        for a in p['old_sources']:a['archive']=immutable_bytes(base/'sources'/Path(a['archive']['path']).name,o.raw(a['archive']))
        p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p);new=repaired_preengine_constructor(o.doc(original_ref),proof);verify_preengine_constructor(new,proof);o.need(o.ref(path)==original_ref,'preengine-final-cas');__import__('complaint_execution_launcher').save(path,new)
        return {'kind':PREENGINE_KIND,'state':'reconciled','launcher':o.ref(path),'proof':proof,'ui_used':False}

# Finite post-constructor readonly failure; legacy PREENGINE verifier stays exact.
FILTER_READONLY_FIELD='confirmed_filter_readonly_recovery'
FILTER_READONLY_KIND='verified-complaint-filter-readonly-successor-v1'
FILTER_READONLY_RELEASE='supervisor-reviewed-complaint-filter-readonly-successor-source-release-v1'
FILTER_ERROR='review-filter-loading-exhausted'
FILTER_OLD_PROOF_SHA='449e42fb9d1e67f024f0a14be7e2a2a8a2411f24465d9fbccd1b1761be71ea30'
FILTER_OLD_RELEASE_SHA='06726597a2507ac40d1daaef4cf8d8e2f787eadddff6c66a7936c21ef45bf1f6'
FILTER_WORKFLOW_RELEASE_SHA='60f706908ee0c69d647326081795d0e88330c505b885a8ebddc577ac561a52c7'

def _filter_paths():
    return {'helper':str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'workflow':str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')}
def _filter_doc(reference,archives=()):
    matches=[x for x in archives if x['original']==reference]
    o.need(len(matches)<=1,'filter-successor-duplicate-material')
    if matches:
        raw=o.raw(matches[0]['archive']);o.need(__import__('hashlib').sha256(raw).hexdigest()==reference['sha256'],'filter-successor-material-sha');return json.loads(raw)
    return o.doc(reference)
def _filter_graph(oldproof_ref,release_ref,*,installed,source_successor=None):
    o.need(source_successor is None or installed is False,'capture-source-archive-data-only')
    o.need(oldproof_ref['sha256']==FILTER_OLD_PROOF_SHA,'filter-successor-exact-old-proof');p=o.doc(oldproof_ref);paths=_filter_paths();root=o.doc(release_ref)
    o.need(root.get('kind')==FILTER_READONLY_RELEASE and root.get('published')is True and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director','filter-successor-reviewed-root')
    authority=root['filter_readonly_successor'];o.need(set(authority)=={'previous_recovery','workflow_release','original_parent','original_engine','original_operator','worker_exit'}and authority['previous_recovery']==oldproof_ref and root['previous_source_release']==authority['workflow_release'],'filter-successor-authority')
    wr=authority['workflow_release'];o.need(wr['sha256']==FILTER_WORKFLOW_RELEASE_SHA,'filter-successor-workflow-release');w=o.doc(wr)
    o.need(w.get('kind')=='supervisor-reviewed-review-filter-latency-source-release-v1'and w.get('published')is True and w.get('test_projection_only')is False and w.get('reviewed_by')=='workshop-director'and w['previous_source_release']==p['release']and p['release']['sha256']==FILTER_OLD_RELEASE_SHA,'filter-successor-finite-ancestry')
    targets=root['targets'];o.need(len(targets)==2 and {t['target']for t in targets}==set(paths.values())and not root.get('data_targets'),'filter-successor-exact-two-targets')
    new={t['target']:t for t in targets};o.need(len(w['targets'])==1 and w['targets'][0]['target']==paths['workflow']and not w.get('data_targets'),'filter-successor-sole-workflow-publication');wt=w['targets'][0]
    original=o.doc(p['original_archive']);old={r['path']:r for r in original['code_refs']};o.need(len(old)==160 and len(original['code_refs'])==160,'filter-successor-original160')
    oldrelease=o.doc(p['release']);o.need(oldrelease.get('kind')=='supervisor-reviewed-preengine-acquisition-serialization-source-release-v1'and oldrelease.get('published')is True and oldrelease.get('test_projection_only')is False,'filter-successor-old-release')
    oldtargets=oldrelease['targets'];o.need(len(oldtargets)==5 and {t['target']for t in oldtargets}==set(preengine_paths().values()),'filter-successor-old-five')
    base=o.location(p['order'])/'.preengine-constructor-recovery'/p['original_launcher']['sha256'];o.need(Path(oldproof_ref['path'])==base/'proof.json'and p['original_archive']['path']==str(base/'original-launcher.json')and datetime.fromisoformat(p['at']).utcoffset()is not None,'filter-successor-old-proof-location')
    before={a['target']:a['archive']for a in p['old_sources']};o.need(len(before)==5 and set(before)==set(preengine_paths().values()),'filter-successor-old-archives');effective=copy.deepcopy(original['code_refs'])
    for t in oldtargets:
        target=t['target'];a=before[target];o.need(Path(a['path'])==base/'sources'/(Path(target).name+'.before')and a['sha256']==old[target]['sha256']==t['old_sha256']==t['before']['sha256']and o.raw(a)==o.raw(t['before']),'filter-successor-old-cas');o.raw(t['after'])
        effective=[{'path':target,'sha256':t['after']['sha256']}if r['path']==target else r for r in effective]
    o.need(effective==p['effective_code_refs'],'filter-successor-old-effective-equality');old_effective={r['path']:r for r in effective}
    o.need(wt['old_sha256']==wt['before']['sha256']==old_effective[paths['workflow']]['sha256']and o.raw(wt['before'])and wt['after']['sha256']==new[paths['workflow']]['old_sha256'],'filter-successor-workflow-cas');o.raw(wt['after'])
    interim={**old_effective,paths['workflow']:{'path':paths['workflow'],'sha256':wt['after']['sha256']}}
    for target,t in new.items():
        o.need(t['old_sha256']==t['before']['sha256']==interim[target]['sha256'],'filter-successor-new-before-cas');o.raw(t['before']);o.raw(t['after'])
        if target==paths['workflow']:o.need(o.raw(t['before'])==o.raw(wt['after']),'filter-successor-workflow-byte-continuity')
    codes=[{'path':r['path'],'sha256':new[r['path']]['after']['sha256']}if r['path']in new else r for r in effective]
    # Only the two reviewed slots bypass old canonical reads; all other 158 stay exact.
    for r in codes:
        if installed or r['path']not in new:_capture_focus_code_raw(r,source_successor)
    return codes,authority,p

def filter_readonly_facts(parent_ref,engine_ref,operator_ref,worker_ref,*,archives=(),require_receipt_absent=True):
    parent=_filter_doc(parent_ref,archives);engine=_filter_doc(engine_ref,archives);state=_filter_doc(operator_ref,archives);folder=o.location(parent['order']);order=o.validate(parent['order']);oldref=parent[PREENGINE_FIELD];old=o.doc(oldref)
    o.need(oldref['sha256']==FILTER_OLD_PROOF_SHA and not parent.get(FILTER_READONLY_FIELD)and not engine.get(FILTER_READONLY_FIELD)and not state.get(FILTER_READONLY_FIELD),'filter-successor-original-no-marker')
    o.need(Path(parent_ref['path'])==folder/'launcher.json'and Path(engine_ref['path'])==folder/'engine.json'and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('completion'),'filter-successor-parent-hold')
    prior=preengine_constructor_facts(old['original_launcher'],old['worker_exit'],require_engine_absent=False,original_archive=old['original_archive']);original=prior['original'];expected=repaired_preengine_constructor(original,oldref)
    o.need(old['order']==original['order']and old['worker_task_id']==prior['worker_task_id']and old['origins']==prior['origins']and old['evidence']==prior['evidence']and old['failed_calls']==prior['failed_calls']and old['ui_used']is False,'filter-successor-old-facts-unchanged')
    for k in ('kind','order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','tab_id','pid','code_refs','origin_ref','resolved_errors',PREENGINE_FIELD):o.need(parent.get(k)==expected.get(k),'filter-successor-original-parent-binding')
    o.need(len(parent['calls'])==2 and parent['calls'][:1]==original['calls']and all(c['state']=='returned'for c in parent['calls']),'filter-successor-two-child-history');call=parent['calls'][1];launch=o.doc(call['launch']);ex=o.doc(call['result'])
    argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(call['launch']['path']==str(folder/'children/0001-launch.json')and call['result']['path']==str(folder/'children/0001-exit.json')and launch['index']==1 and launch['order']==parent['order']and call['argv']==launch['argv']==ex['argv']==argv and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':FILTER_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'filter-successor-exact-child1')
    o.need(engine['kind']=='complaint-execution-v1'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==FILTER_ERROR and engine['index']==0 and engine['phase']=='collect'and len(engine['calls'])==13,'filter-successor-exact-engine')
    for i,c in enumerate(engine['calls'][:12]):
        o.need(c['state']=='returned'and c.get('applied')is True and c['result']['path']==str(folder/'receipts'/(str(i+1).zfill(5)+'.json')),'filter-successor-returned-prefix');o.doc(c['result'])
    failed=engine['calls'][12];o.need(failed['state']=='failed'and failed.get('error')==FILTER_ERROR and failed['step']=='collect'and failed['company_index']==0 and 'result'not in failed and not failed.get('applied')and failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['artifacts']==engine['companies'][0]['artifacts'],'filter-successor-resultless-readonly-failure')
    a=failed['context']['artifacts'];jobref=a['unit_artifacts']['work_order'];job=o.doc(jobref)
    o.need(operator_ref['path']==job['workflow_path']and jobref['path']==job['work_order_path']and operator_ref['path']in a['journals']and state['phase']=='verifyFilter'and state['revision']==11 and state['state']=='running'and state['last_error']['code']==state['last_error']['message']==FILTER_ERROR and state['work_order_id']==job['work_order_id']and state['company']==job['company']and str(state['groupid'])==str(job['groupid'])and state['date_range']=={k:job['date_range'][k]for k in ('start','end')}and state['tab_id']==parent['tab_id'],'filter-successor-operator-binding')
    o.need(len(state['calls'])==5 and all(c['state']=='confirmed'and c['command']['op']=='click'and c['command']['kind']in ('navigation','filter')for c in state['calls'])and state['calls'][-1]['phase']=='pageEnd'and not any(state.get(k)for k in ('exportPending','downloadPending','result')),'filter-successor-five-confirmed-no-unknown')
    from readonly_tick_snapshot import decode
    from dom_evidence import context,identity,VERSION
    from review_filter_loading import is_loading,validate_filter_values,validate_pending_store_scope
    reads=state['review_filter_loading_reads'];o.need(len(reads)==1 and reads[0]['attempt']==0 and reads[0]['tree']==state['last_tree'],'filter-successor-sole-read');read=reads[0];reply=o.doc(read['reply']);cmd=read['command'];o.need(cmd['op']=='readonly-scope'and cmd['tabId']==state['tab_id']and set(cmd)=={'op','tabId','windowId'}and reply['ok']is True,'filter-successor-original-readonly-reply');scope=decode(reply['result'],cmd['tabId'],cmd['windowId']);before=context(scope['before'],cmd['tabId'],job['groupid']);after=context(scope['after'],cmd['tabId'],job['groupid']);tree=o.doc(state['last_tree']);o.need(before['url']==after['url']and scope['tree']==tree and tree==o.doc(read['before_tree'])and tree['url']=='https://life.douyin.com/p/life_comment/management'and scope['ping'].get('version')==VERSION and scope['ping'].get('safety')=='DOM-only','filter-successor-readonly-scope');identity(tree,job['identity_baseline']);o.need(state['identity']==job['identity_baseline']and is_loading(tree),'filter-successor-loading-not-zero');validate_filter_values(tree,state['date_range']);validate_pending_store_scope(tree)
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;pxref=o.ref(attempt/'parent-run-exit.json');px=o.doc(pxref);output=json.loads(o.raw(px['stdout']))
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['attempt_id']==request['attempt_id']and worker['returncode']==0 and response['task_id']==request['task']['id']==old['worker_task_id']and response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['flow']==o.FLOW and request['task']['day']==order['day'],'filter-successor-worker-original')
    o.need(px['returncode']==0 and output['status']=='hold'and output['error']=='execution-child-stopped'and output['last_child_receipt']==call['result']and output.get('child')is None and not o.raw(px['stderr'])and px['argv']==[argv[0],str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'],'filter-successor-parent-natural-exit')
    slot=folder/'receipts/00013.json'
    if require_receipt_absent:o.need(not slot.exists()and not slot.is_symlink(),'filter-successor-receipt13-must-be-absent')
    evidence=[parent_ref,engine_ref,operator_ref,worker_ref,worker['request'],worker['response'],pxref,px['stdout'],px['stderr'],jobref,oldref,*[c[k]for c in parent['calls']for k in ('launch','result')],*[c['result']for c in engine['calls'][:12]],read['before_tree'],read['reply'],read['tree']]
    return {'parent':parent,'engine':engine,'operator':state,'previous_recovery':oldref,'order':parent['order'],'job':jobref,'failed_call':failed,'failed_calls':copy.deepcopy(parent['calls']),'evidence':evidence,'task_id':request['task']['id'],'attempt_id':request['attempt_id'],'outer':request['task']['outer']}

def plan_filter_readonly(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,*,installed=True):
    f=filter_readonly_facts(parent_ref,engine_ref,operator_ref,worker_ref);codes,authority,old=_filter_graph(f['previous_recovery'],release_ref,installed=installed)
    o.need(authority=={'previous_recovery':f['previous_recovery'],'workflow_release':authority['workflow_release'],'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker_exit':worker_ref},'filter-successor-exact-release-facts')
    return {'kind':FILTER_READONLY_KIND,'order':f['order'],'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker_exit':worker_ref,'previous_recovery':f['previous_recovery'],'release':release_ref,'effective_code_refs':codes,'job':f['job'],'failed_call':f['failed_call'],'failed_calls':f['failed_calls'],'task_id':f['task_id'],'attempt_id':f['attempt_id'],'outer':f['outer'],'evidence':f['evidence'],'ui_used':False,'new_mutations':0}
def repaired_filter_readonly(parent,engine,operator,proof_ref,at):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine);operator=copy.deepcopy(operator)
    for value in (parent,engine):
        value['status']='running';value.setdefault('resolved_errors',[]).append({'error':value.pop('error'),'recovery':proof_ref});value[FILTER_READONLY_FIELD]=proof_ref
    engine.setdefault('resolved_readonly_failures',[]).append({'index':12,'call':engine['calls'].pop(),'recovery':proof_ref})
    operator.setdefault('resolved_errors',[]).append({**operator.pop('last_error'),'resolved_at':at,'next_phase':'verifyFilter','recovery_proof':proof_ref});operator[FILTER_READONLY_FIELD]=proof_ref;operator['updated_at']=at
    return parent,engine,operator

def _filter_proof_facts(proof_ref,*,installed,source_successor=None):
    p=o.doc(proof_ref);folder=o.location(p['order']);base=folder/'.filter-readonly-recovery'/p['original_parent']['sha256'];o.need(p['kind']==FILTER_READONLY_KIND and Path(proof_ref['path'])==base/'proof.json'and p['ui_used']is False and p['new_mutations']==0 and datetime.fromisoformat(p['at']).utcoffset()is not None,'filter-successor-canonical-proof')
    archives=p['original_archives'];o.need(len(archives)==3 and [a['original']for a in archives]==[p[k]for k in ('original_parent','original_engine','original_operator')]and all(a['archive']['path']==str(base/n)for a,n in zip(archives,('parent-before.json','engine-before.json','operator-before.json'))),'filter-successor-three-canonical-archives')
    f=filter_readonly_facts(p['original_parent'],p['original_engine'],p['original_operator'],p['worker_exit'],archives=archives,require_receipt_absent=False);codes,authority,old=_filter_graph(p['previous_recovery'],p['release'],installed=installed,source_successor=source_successor)
    for k in ('order','previous_recovery','job','failed_call','failed_calls','task_id','attempt_id','outer','evidence'):o.need(p[k]==f[k],'filter-successor-proof-facts')
    o.need(p['effective_code_refs']==codes and authority['original_parent']==p['original_parent']and authority['original_engine']==p['original_engine']and authority['original_operator']==p['original_operator']and authority['worker_exit']==p['worker_exit'],'filter-successor-proof-release')
    return p,f,codes

def verify_filter_readonly(current,proof_ref,*,installed=True,source_successor=None):
    p,f,codes=_filter_proof_facts(proof_ref,installed=installed,source_successor=source_successor);folder=o.location(p['order']);o.need(current.get(FILTER_READONLY_FIELD)==proof_ref,'filter-successor-current-proof-marker')
    expected,ee,ss=repaired_filter_readonly(f['parent'],f['engine'],f['operator'],proof_ref,p['at'])
    for k in set(expected)-{'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}:o.need(current.get(k)==expected[k],'filter-successor-current-parent-binding')
    o.need(current['calls'][:2]==expected['calls']and all(c['state']in ('unknown','returned')for c in current['calls'][2:]),'filter-successor-parent-exact-prefix')
    actual_engine=o.doc(o.ref(folder/'engine.json'));actual_operator=o.doc(o.ref(p['original_operator']['path']))
    o.need(actual_engine.get(FILTER_READONLY_FIELD)==proof_ref and actual_engine['order']==ee['order']and actual_engine['scope_sha256']==ee['scope_sha256']and actual_engine['calls'][:12]==ee['calls']and actual_engine.get('resolved_readonly_failures')==ee['resolved_readonly_failures'],'filter-successor-current-engine-prefix')
    for k in ('work_order_id','fingerprint','company','groupid','date_range','tab_id','identity_contract',FILTER_READONLY_FIELD):o.need(actual_operator.get(k)==ss.get(k),'filter-successor-current-operator-binding')
    o.need(actual_operator['calls'][:5]==ss['calls']and actual_operator.get('resolved_errors',[])[:len(ss['resolved_errors'])]==ss['resolved_errors']and all(c.get('state')in ('confirmed','unknown')for c in actual_operator['calls'][5:]),'filter-successor-current-operator-prefix')
    return {'kind':FILTER_READONLY_KIND,'code_refs':codes,'failed_calls':f['failed_calls'],'evidence':[proof_ref,p['release'],*[a['archive']for a in p['original_archives']],*[r for r in f['evidence']if r not in [p[k]for k in ('original_parent','original_engine','original_operator')]]]}

def recover_filter_readonly(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,*,checkpoint=lambda stage:None):
    # Caller owns the existing browser-wecom resource lock; these are metadata locks.
    import contextlib
    folder=Path(parent_ref['path']).parent;base=folder/'.filter-readonly-recovery'/parent_ref['sha256']
    with contextlib.ExitStack()as locks:
        for path in (folder/'launcher.lock',folder/'engine.lock',Path(operator_ref['path']).with_name('.bridge-execution.lock')):
            stream=locks.enter_context(path.open('a'));fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        slot=folder/'receipts/00013.json';o.need(not slot.exists()and not slot.is_symlink(),'filter-successor-receipt13-must-be-absent')
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need([p[k]for k in ('original_parent','original_engine','original_operator','worker_exit','release')]==[parent_ref,engine_ref,operator_ref,worker_ref,release_ref],'filter-successor-continuation-authority')
            _filter_proof_facts(proof,installed=True);originals=[_filter_doc(r,p['original_archives'])for r in (parent_ref,engine_ref,operator_ref)]
        else:
            p=plan_filter_readonly(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);originals=[o.doc(r)for r in (parent_ref,engine_ref,operator_ref)];p['original_archives']=[{'original':r,'archive':immutable_bytes(base/n,o.raw(r))}for r,n in zip((parent_ref,engine_ref,operator_ref),('parent-before.json','engine-before.json','operator-before.json'))];checkpoint('archives')
            o.immutable(base/'intent.json',{'kind':FILTER_READONLY_KIND,'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'release':release_ref});checkpoint('intent');p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p);checkpoint('proof')
        changes=repaired_filter_readonly(*originals,proof,p['at'])
        # Check every current value before any new mutable write, including reentry.
        for r,b,a in zip((parent_ref,engine_ref,operator_ref),originals,changes):o.need(o.doc(o.ref(r['path']))in (b,a),'filter-successor-metadata-cas-conflict')
        import complaint_execution_launcher as launcher
        for index in (2,1,0):
            r=(parent_ref,engine_ref,operator_ref)[index];old=originals[index];new=changes[index];cur=o.doc(o.ref(r['path']))
            o.need(cur in (old,new),'filter-successor-write-cas-conflict')
            if cur==old:launcher.save(Path(r['path']),new)
            checkpoint(('parent','engine','operator')[index])
        verify_filter_readonly(o.doc(o.ref(parent_ref['path'])),proof)
        return {'state':'reconciled','proof':proof,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'operator':o.ref(operator_ref['path']),'ui_used':False,'new_mutations':0}

_FILTER_LEGACY_PREENGINE_VERIFY=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(FILTER_READONLY_FIELD):
        o.need(current.get(PREENGINE_FIELD)==proof_ref,'filter-successor-legacy-marker-preserved');return verify_filter_readonly(current,current[FILTER_READONLY_FIELD],installed=installed)
    return _FILTER_LEGACY_PREENGINE_VERIFY(current,proof_ref,installed=installed)
_FILTER_LEGACY_ENGINE_CALLS=engine_calls
def engine_calls(engine):
    if engine.get(FILTER_READONLY_FIELD):
        parent=o.doc(o.ref(phase_directory(engine)/'launcher.json'));o.need(parent.get(FILTER_READONLY_FIELD)==engine[FILTER_READONLY_FIELD],'filter-successor-engine-parent-marker');verify_filter_readonly(parent,engine[FILTER_READONLY_FIELD]);return engine['calls']
    return _FILTER_LEGACY_ENGINE_CALLS(engine)

# One semantic restoration epoch; no historical call is replayed or relabelled.
DATE_RESTORE_FIELD='review_filter_date_restore'
DATE_RESTORE_KIND='source-bound-empty-review-date-restoration-v1'
DATE_SOURCE_FIELD='review_filter_date_source'
DATE_SOURCE_KIND='supervisor-reviewed-empty-review-date-restoration-source-release-v1'
DATE_PREVIOUS_RELEASE_SHA='e8618def1ba9ddcebe43c78610287addae301f1c652b25e77780ca55ffe0fd50'
def date_restore_input_history(job,state):
    from switch_read_recovery import _typed_search_snapshot
    if state.get('company_search_explicit_recovery'):
        facts=_typed_search_snapshot(job,state);o.need(facts is not None,'date-restore-typed-input-history');return facts
    o.need(all(c.get('state')=='confirmed'for c in state['calls']),'date-restore-unknown-or-business-intent');return None

def date_restore_loading_error_transform(job,state,snapshot,scope_ref,original_ref):
    """Pure exact exhausted-before-render loss recovery. No I/O mutation/input.
    New date epoch is linked to old confirmed input; it never replays its keys.
    """
    from readonly_tick_snapshot import decode
    from dom_evidence import identity,context
    from review_filter_loading import is_loading,validate_filter_values,validate_pending_store_scope
    error=state.get('last_error',{});o.need(set(error)=={'at','code','message'}and error['code']==error['message']=='review-filter-loading-exhausted'and state['state']=='running'and state['phase']=='verifyFilter'and not state.get(DATE_RESTORE_FIELD),'date-restore-exact-loading-error')
    from switch_read_recovery import fingerprint
    o.need(state.get('work_order_id')==job['work_order_id']and state.get('fingerprint')==fingerprint(job)and state.get('company')==job['company']and str(state.get('groupid'))==str(job['groupid'])and state.get('date_range')=={k:job['date_range'][k]for k in('start','end')}and state.get('identity_contract')==job.get('identity_contract')=='merchant-v2'and state.get('identity')==job['identity_baseline'],'date-restore-job-binding')
    o.need(o.doc(original_ref)==state and o.doc(scope_ref)==snapshot,'date-restore-exact-loss-state')
    scope,value=date_restore_scope(job,state,snapshot);o.need(value==''and not is_loading(snapshot['tree']),'date-restore-loaded-empty-only')
    reads=state.get('review_filter_loading_reads');o.need(type(reads)is list and len(reads)==3 and [r['attempt']for r in reads]==[0,1,2],'date-restore-original-three-waits');previous=None
    for row in reads:
        o.need(row['command']=={'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']},'date-restore-original-wait-command');reply=o.doc(row['reply']);o.need(reply.get('ok')is True,'date-restore-original-wait-transport');past=decode(reply['result'],scope['tab_id'],scope['window_id']);before=context(past['before'],scope['tab_id'],job['groupid']);after=context(past['after'],scope['tab_id'],job['groupid']);o.need(before['url']==after['url']==scope['url']and past['tree']==o.doc(row['tree'])and is_loading(past['tree']),'date-restore-original-wait-scope');identity(past['tree'],job['identity_baseline']);validate_filter_values(past['tree'],state['date_range']);validate_pending_store_scope(past['tree'])
        # The frozen-page protocol required the pre-wait tree to equal the
        # first observed tree; a progressively rendering page (B59 attempt-36:
        # the body appears during the bounded waits and the post-error
        # last_tree is already loaded) changes between those reads without
        # any input. Each read's integrity stays hash-checked, the chain
        # row[i].before_tree==row[i-1].tree stays exact for i>=1, and the
        # monotone wait-time bound stays; only the frozen-page equivalence
        # is dropped.
        if previous is None:
            o.need(isinstance(row['before_tree'],dict)and row['before_tree'].get('path')and row['before_tree'].get('sha256')==__import__('hashlib').sha256(Path(row['before_tree']['path']).read_bytes()).hexdigest(),'date-restore-original-wait-prefix')
        else:
            o.need(row['before_tree']==previous,'date-restore-original-wait-prefix')
        previous=row['tree'];at=datetime.fromisoformat(row['at']);o.need(at.utcoffset()is not None and at<=datetime.fromisoformat(error['at']),'date-restore-original-wait-time')
    # The post-error last_tree may be a later fresh observe (progressive
    # rendering finished after the budget expired); its integrity is checked
    # instead of the frozen-page equality.
    o.need(isinstance(state.get('last_tree'),dict)and state['last_tree'].get('path')and state['last_tree'].get('sha256')==__import__('hashlib').sha256(Path(state['last_tree']['path']).read_bytes()).hexdigest(),'date-restore-original-final-tree');after=copy.deepcopy(state);after.pop('last_error');after.setdefault('resolved_errors',[]).append({'original_error':copy.deepcopy(error),'resolution':'loaded-empty-date-after-bounded-filter-waits','original_workflow':copy.deepcopy(original_ref),'loss_scope':copy.deepcopy(scope_ref),'original_calls_sha256':__import__('hashlib').sha256(json.dumps(state['calls'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()});return after

def date_restore_scope(job,state,snapshot,binding=None):
    from readonly_tick_snapshot import decode
    from dom_evidence import context,identity,all_store_scope,review_filter_fields,nodes,VERSION
    value=decode(snapshot,state['tab_id'],snapshot['scope']['windowId']);before=context(value['before'],state['tab_id'],job['groupid']);after=context(value['after'],state['tab_id'],job['groupid']);tree=value['tree'];ns=list(nodes(tree));fields=review_filter_fields(tree)
    o.need(before['url']==after['url']and tree['url']=='https://life.douyin.com/p/life_comment/management'and before['url'].split('?')[0]==tree['url']and value['ping'].get('version')==VERSION and value['ping'].get('safety')=='DOM-only','date-restore-scope')
    scope={'tab_id':state['tab_id'],'window_id':value['scope']['windowId'],'url':before['url'],'groupid':str(job['groupid']),'identity':identity(tree,job['identity_baseline'])}
    if binding is not None:o.need(scope==binding,'date-restore-binding-changed')
    o.need(all_store_scope(tree)is True and all(fields[k].get('attributes',{}).get('value')=='全部'for k in ('评价类型','评价来源','评价状态')),'date-restore-defaults-allstores')
    o.need('value'in fields['评价时间'].get('attributes',{})and type(fields['评价时间']['attributes']['value'])is str,'date-restore-date-value-required')
    o.need(not any(n.get('role')in ('dialog','alertdialog')or n.get('attributes',{}).get('aria-modal')=='true'or 'SwitchAccountCardModal'in n.get('attributes',{}).get('class','')for n in ns),'date-restore-foreign-modal')
    date_restore_input_history(job,state)
    o.need(not any(state.get(k)for k in ('exportPending','downloadPending','result'))and not any(c.get('command',{}).get('kind')in ('export-submit','download')for c in state['calls']),'date-restore-unknown-or-business-intent')
    return scope,fields['评价时间']['attributes']['value']
def date_restore_picker(tree,date):
    from dom_evidence import nodes,calendar_day
    containers=[n for n in nodes(tree)if 'byted-date-container'in n.get('attributes',{}).get('class','').split()]
    if not containers:return False
    o.need(len(containers)==1,'date-restore-picker-ambiguous');scope={'root':containers[0],'truncated':False}
    for k in ('start','end'):calendar_day(scope,date[k])
    return True

def date_restore_contract(job,state,snapshot,scope_ref,original_ref):
    from dom_evidence import calendar_day,review_filter_fields,context,identity,VERSION
    from readonly_tick_snapshot import decode
    from hashlib import sha256
    o.need(state['state']=='running'and state['phase']=='verifyFilter'and not state.get('last_error')and not state.get(DATE_RESTORE_FIELD),'date-restore-initial-phase')
    from switch_read_recovery import fingerprint
    expected_fingerprint=fingerprint(job)
    o.need(state['work_order_id']==job['work_order_id']and state['fingerprint']==expected_fingerprint and state['company']==job['company']and str(state['groupid'])==str(job['groupid'])and state['date_range']=={k:job['date_range'][k]for k in ('start','end')}and state['identity_contract']==job['identity_contract']=='merchant-v2'and state['identity']==job['identity_baseline'],'date-restore-job-binding')
    o.need(o.doc(original_ref)==state,'date-restore-original-state-proof');scope,value=date_restore_scope(job,state,snapshot);o.need(value=='','date-restore-only-empty');o.need(o.doc(scope_ref)==snapshot,'date-restore-loss-proof')
    calls=state['calls'];o.need(state['revision']==int(calls[-1]['key'].split(':')[0])+1,'date-restore-original-revision');date_restore_input_history(job,state);o.need((len(calls)==5 if not state.get('company_search_explicit_recovery')else len(calls)>=5)and [c['phase']for c in calls[-5:]]==['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'],'date-restore-original-filter-tail');refs=[];scope_refs=[]
    for call,phase in zip(calls[-3:],('openPageCalendar','pageStart','pageEnd')):
        prefix=call['key'].split(':');o.need(len(prefix)==2 and prefix[0].isdigit()and prefix[1]==phase,'date-restore-original-action-key');path=Path(job['workflow_path']).parent/'bridge-evidence'/(prefix[0].zfill(4)+'-'+phase+'.json');r=o.ref(path);tree=o.doc(r);refs.append(r)
        companions=list(path.parent.glob(prefix[0].zfill(4)+'-'+phase+'-scope-*.json'));o.need(len(companions)==1,'date-restore-original-companion-unique');sr=o.ref(companions[0]);past=decode(o.doc(sr),state['tab_id'],scope['window_id']);pb=context(past['before'],state['tab_id'],job['groupid']);pa=context(past['after'],state['tab_id'],job['groupid']);o.need(past['tree']==tree and pb['url']==pa['url']==scope['url']and past['scope']['windowId']==scope['window_id']and past['ping'].get('version')==VERSION and past['ping'].get('safety')=='DOM-only','date-restore-original-window-url-tree');identity(tree,job['identity_baseline']);scope_refs.append(sr)
        target=review_filter_fields(tree)['评价时间']if phase=='openPageCalendar'else calendar_day(tree,state['date_range']['start'if phase=='pageStart'else'end']);cmd=call['command'];clicked=call['result'].get('clicked',{})
        o.need(cmd=={'op':'click','tabId':state['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'filter'}and clicked.get('selector')==target['selector']and clicked.get('name')==target['name'],'date-restore-original-exact-date-action')
    return {'kind':DATE_RESTORE_KIND,'original_state':original_ref,'job':o.ref(job['work_order_path']),'operator_path':job['workflow_path'],'date_range':state['date_range'],'phase':state['phase'],'revision':state['revision'],'original_calls':copy.deepcopy(calls),'original_date_trees':refs,'original_date_scopes':scope_refs,'loss_scope':scope_ref,'binding':scope,'picker_visible':date_restore_picker(snapshot['tree'],state['date_range']),'max_epochs':1,'max_actions':3,'history_inputs_replayed':False}
def date_restore_epoch_verify(job,state):
    from dom_evidence import calendar_day,review_filter_fields
    epoch=state[DATE_RESTORE_FIELD];p=o.doc(epoch['plan']);o.need(p['kind']==DATE_RESTORE_KIND and p['max_epochs']==1 and p['max_actions']==3 and p['history_inputs_replayed']is False and p['job']==o.ref(job['work_order_path'])and p['operator_path']==job['workflow_path']and p['date_range']=={k:job['date_range'][k]for k in ('start','end')},'date-restore-plan-binding')
    o.need(epoch.get('complete')or(state['phase']==p['phase']and state['revision']==p['revision']),'date-restore-incomplete-phase-revision');original=o.doc(p['original_state']);recomputed=date_restore_contract(job,original,o.doc(p['loss_scope']),p['loss_scope'],p['original_state']);o.need(p==recomputed,'date-restore-plan-recompute')
    expected_base=Path(job['workflow_path']).parent/'review-filter-date-restores'/__import__('hashlib').sha256(json.dumps(p,sort_keys=True,ensure_ascii=False).encode()).hexdigest();o.need(Path(epoch['plan']['path'])==expected_base/'intent.json'and epoch['key']=='filter-date-restore:'+expected_base.name and state['calls'][:len(p['original_calls'])]==p['original_calls'],'date-restore-epoch-key-prefix')
    o.need(set(epoch['actions'])<=({'open','start','end'}if not p['picker_visible']else{'start','end'}),'date-restore-action-set')
    extra=[c for c in state['calls'][len(p['original_calls']):]if c['key'].startswith(epoch['key']+':')];o.need(len(extra)==len({c['key']for c in extra})and len(extra)<=3,'date-restore-action-count')
    for stage,r in epoch['actions'].items():
        a=o.doc(r);o.need(Path(r['path'])==expected_base/(stage+'-intent.json')and a['plan']==epoch['plan']and a['stage']==stage and a['key']==epoch['key']+':'+stage and datetime.fromisoformat(a['at']).utcoffset()is not None,'date-restore-stage-intent');snap=o.doc(a['scope']);_,stage_value=date_restore_scope(job,original,snap,p['binding']);o.need(stage_value=='','date-restore-stage-empty-required');tree=snap['tree'];target=review_filter_fields(tree)['评价时间']if stage=='open'else calendar_day(tree,p['date_range']['start'if stage=='start'else'end']);cmd={'op':'click','tabId':p['binding']['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'filter'};o.need(a['command']==cmd,'date-restore-stage-command')
        found=[c for c in extra if c['key']==a['key']];o.need(len(found)<=1,'date-restore-stage-duplicate')
        if found:o.need(found[0]['command']==cmd and found[0]['state']=='confirmed'and found[0]['result'].get('clicked',{}).get('selector')==target['selector']and found[0]['result'].get('clicked',{}).get('name')==target['name'],'date-restore-unknown-or-result-conflict')
    o.need(all(any(c['key']==epoch['key']+':'+stage for stage in epoch['actions'])for c in extra),'date-restore-foreign-action')
    sequence=['start','end']if p['picker_visible']else['open','start','end'];done=[stage for stage in sequence if any(c['key']==epoch['key']+':'+stage for c in extra)];o.need(done==sequence[:len(done)],'date-restore-stage-order')
    if epoch.get('complete'):
        o.need(done==sequence,'date-restore-incomplete-actions');snapshot=o.doc(epoch['complete']);_,value=date_restore_scope(job,original,snapshot,p['binding']);o.need(value==p['date_range']['start']+' ~ '+p['date_range']['end'],'date-restore-final-date')
    return p,sequence,done

# Source-only successor of the already-reconciled readonly proof; no new failures.
def _date_restore_base_source_codes(current,release_ref,*,installed=True,source_successor=None):
    o.need(source_successor is None or installed is False,'capture-source-base-archive-data-only')
    root=o.doc(release_ref);p=o.doc(current[FILTER_READONLY_FIELD]);o.need(root.get('kind')==DATE_SOURCE_KIND and root.get('published')is True and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director'and root.get('previous_source_release')==p['release']and p['release']['sha256']==DATE_PREVIOUS_RELEASE_SHA,'date-restore-reviewed-source-successor')
    o.need(root['date_restore_source_successor']=={'previous_recovery':current[FILTER_READONLY_FIELD],'previous_source_release':p['release'],'order':current['order']}and len(root['targets'])==2 and {t['target']for t in root['targets']}==set(_filter_paths().values())and not root.get('data_targets'),'date-restore-source-authority')
    old,_,_=_filter_graph(p['previous_recovery'],p['release'],installed=False,source_successor=source_successor);by={r['path']:r for r in old};targets={t['target']:t for t in root['targets']}
    for path,t in targets.items():o.need(t['old_sha256']==t['before']['sha256']==by[path]['sha256'],'date-restore-source-cas');o.raw(t['before']);o.raw(t['after'])
    codes=[{'path':r['path'],'sha256':targets[r['path']]['after']['sha256']}if r['path']in targets else r for r in old]
    for r in codes:
        if installed or r['path']not in targets:_capture_focus_code_raw(r,source_successor)
    return codes
_DATE_LEGACY_FILTER_VERIFY=verify_filter_readonly
def verify_filter_readonly(current,proof_ref,*,installed=True):
    if not current.get(DATE_SOURCE_FIELD):return _DATE_LEGACY_FILTER_VERIFY(current,proof_ref,installed=installed)
    successor=current[DATE_SOURCE_FIELD]if o.doc(current[DATE_SOURCE_FIELD]).get('kind')==CAPTURE_SOURCE_KIND else None
    if successor is not None:_capture_source_release(successor,current)
    value=_DATE_LEGACY_FILTER_VERIFY(current,proof_ref,installed=False,source_successor=successor);value['code_refs']=date_restore_source_codes(current,current[DATE_SOURCE_FIELD],installed=installed);value['evidence']=[*value['evidence'],current[DATE_SOURCE_FIELD]]
    operator=o.doc(o.ref(o.doc(proof_ref)['original_operator']['path']))
    if operator.get(DATE_RESTORE_FIELD):date_restore_epoch_verify(o.doc(o.ref(Path(o.doc(proof_ref)['original_operator']['path']).with_name('work-order.json'))),operator)
    return value

# Exactly one source-only successor of the reviewed a4f3 date source. Old code
# archives are bytes, never imported/executed. This does not resolve focus.
CAPTURE_SOURCE_KIND='supervisor-reviewed-capture-window-readonly-effect-source-successor-v1'
CAPTURE_PREDECESSOR={'path':str(o.PROJECT/'work/performance-audit/review-filter-empty-date-restoration-maintenance-candidate/supervisor-release.json'),'sha256':'a4f3a9e8cbaccdef7ad68c2487971d79f4f5ef28019c178c9cedcd21cfbdfe67'}
CAPTURE_FOCUS_BEFORE='591d40f11181bc22b55b391cf5963c15e2f875a358a9d4b173cc638ac0b5bf9d'
CAPTURE_FOCUS_AFTER='6729f04a40223ab62a41e6b4b7157746d7683ef4f3ac3952b897d024c5227959'
CAPTURE_HELPER_BEFORE='60dcbef7f39b9f8f80a6ca3781574eb20e644a6ed3c5f693641069c908b73122'
CAPTURE_FOCUS_REVIEW={'path':str(o.PROJECT/'work/performance-audit/capture-window-readonly-effect-settle-candidate/root-review-v1.json'),'sha256':'a53092d3c0827f0195ed19cb1e967d914851e83c9b7ff0459e70b0add222b27a'}
CAPTURE_FOCUS_FREEZE={'path':str(o.PROJECT/'work/performance-audit/capture-window-readonly-effect-settle-candidate/freeze.json'),'sha256':'32496950ab2ba84924a6dbeef4d49b24a451c7c74b364b0bfc3d0921d749a0ca'}
CAPTURE_DATE_POINTER={'path':str(o.PROJECT/'work/2026-10-25/review-filter-empty-date-restoration-maintenance/date-source-pointer-result-v1.json'),'sha256':'9282b906e060d5412671ff128f0ed90e29ab03aef226ac689547c8f4d4578ea3'}
def _capture_source_release(release_ref,current=None):
    root=o.doc(release_ref);o.need(set(root)=={'binding','capture_window_source_successor','freeze','intent','kind','previous_source_release','published','published_at','review','reviewed_by','targets','test_projection_only'},'capture-source-exact-root-fields');focus=str(o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_focus.py');helper=_filter_paths()['helper'];paths={helper,focus}
    o.need(root.get('kind')==CAPTURE_SOURCE_KIND and root.get('published')is True and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director'and root.get('previous_source_release')==CAPTURE_PREDECESSOR,'capture-source-reviewed-exact-predecessor')
    prior=o.doc(CAPTURE_PREDECESSOR);o.need(prior.get('kind')==DATE_SOURCE_KIND and prior.get('published')is True and prior.get('test_projection_only')is False and prior.get('reviewed_by')=='workshop-director','capture-source-predecessor-review')
    authority=root['capture_window_source_successor'];o.need(set(authority)=={'previous_date_source','previous_readonly_recovery','order','historical_date_pointer_result','focus_review','focus_freeze'}and authority=={'previous_date_source':CAPTURE_PREDECESSOR,'previous_readonly_recovery':prior['date_restore_source_successor']['previous_recovery'],'order':prior['date_restore_source_successor']['order'],'historical_date_pointer_result':CAPTURE_DATE_POINTER,'focus_review':CAPTURE_FOCUS_REVIEW,'focus_freeze':CAPTURE_FOCUS_FREEZE},'capture-source-exact-authority')
    if current is not None:o.need(current[FILTER_READONLY_FIELD]==authority['previous_readonly_recovery']and current['order']==authority['order']and current[DATE_SOURCE_FIELD]in (CAPTURE_PREDECESSOR,release_ref),'capture-source-current-proof-binding')
    pointer=o.doc(CAPTURE_DATE_POINTER);o.need(pointer.get('single_pointer_deep_delta_verified')is True and pointer.get('task_owner_lease_order_outer_unchanged')is True and pointer.get('source_graph_count')==160,'capture-source-historical-pointer')
    review=o.doc(CAPTURE_FOCUS_REVIEW);freeze=o.doc(CAPTURE_FOCUS_FREEZE);o.need(review['approved_target']=={'path':focus,'before_sha256':CAPTURE_FOCUS_BEFORE,'after_sha256':CAPTURE_FOCUS_AFTER}and any(r['sha256']==CAPTURE_FOCUS_AFTER and Path(r['path']).name=='review_capture_focus.py'for r in freeze['files']),'capture-source-fixed-focus-review')
    targets=root['targets'];o.need(len(targets)==2 and {t['target']for t in targets}==paths and not root.get('data_targets'),'capture-source-exact-two-paths');by={t['target']:t for t in targets};directory=Path(release_ref['path']).parent
    for path,t in by.items():
        o.need(set(t)=={'after','before','mode','old_sha256','target'},'capture-source-exact-target-fields')
        expected=CAPTURE_FOCUS_BEFORE if path==focus else CAPTURE_HELPER_BEFORE
        o.need(type(t['mode'])is int and t['mode']==(420 if path==helper else 384) and t['old_sha256']==t['before']['sha256']==expected and Path(t['before']['path'])==directory/(Path(path).name+'.before'),'capture-source-canonical-before-archive');o.raw(t['before']);o.raw(t['after'])
    o.need(by[focus]['after']['sha256']==CAPTURE_FOCUS_AFTER,'capture-source-exact-focus-after')
    return root,prior,by

def _capture_focus_code_raw(reference,source_successor=None):
    # No generic archive resolver: only one old focus path+SHA can use the
    # before archive of this exact reviewed two-source successor.
    focus=str(o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_focus.py')
    if source_successor is not None and reference=={'path':focus,'sha256':CAPTURE_FOCUS_BEFORE}:
        _,_,targets=_capture_source_release(source_successor);return o.raw(targets[focus]['before'])
    return o.raw(reference)

def date_restore_source_codes(current,release_ref,*,installed=True,archive_successor=None):
    o.need(archive_successor is None or installed is False,'window-hold-archives-historical-only')
    root=o.doc(release_ref)
    if root.get('kind')!=CAPTURE_SOURCE_KIND:return _date_restore_base_source_codes(current,release_ref,installed=installed)
    root,prior,targets=_capture_source_release(release_ref,current)
    old=_date_restore_base_source_codes(current,CAPTURE_PREDECESSOR,installed=False,source_successor=archive_successor or release_ref);by={r['path']:r for r in old};o.need(len(old)==len(by)==160,'capture-source-base160')
    for path,t in targets.items():o.need(by[path]['sha256']==t['old_sha256'],'capture-source-effective-before-cas')
    codes=[{'path':r['path'],'sha256':targets[r['path']]['after']['sha256']}if r['path']in targets else r for r in old]
    o.need(len(codes)==160 and [r['path']for r in codes]==[r['path']for r in old]and sum(a!=b for a,b in zip(codes,old))==2 and all(a==b for a,b in zip(codes,old)if a['path']not in targets),'capture-source-only-two-deltas')
    for r in codes:
        if installed or r['path']not in targets:_capture_focus_code_raw(r,archive_successor)
    return codes

# New code-only candidate: no writer, locks, focus.ensure, CLI or grant producer.
WINDOW_HOLD_FIELD='capture_window_effect_recovery'
WINDOW_HOLD_KIND='verified-original-capture-window-effect-hold-recovery-v1'
WINDOW_HOLD_ERROR='capture-window-unknown-readonly-no-replay'
WINDOW_PUBLISHED_SOURCE={'path':str(o.PROJECT/'work/performance-audit/capture-window-source-successor-deployment-actor-candidate/supervisor-release.json'),'sha256':'9ca3b6115abb54cdc3f2a96fc53028c3eaed999569701e835b75e3bcb4824742'}
def _window_time(value):
    at=datetime.fromisoformat(value);o.need(at.utcoffset()is not None,'window-effect-aware-time');return at
def verify_window_effect_envelope(envelope_ref,*,expected_authority,expected_sources,source_successor=None):
    """Pure immutable consumer. Explicit expected authority SHA is trusted input
    from separately reviewed recovery authority, never inferred from role flags.
    It is NOT an effect producer and never reads AX/UI, activates, or writes.
    """
    import review_capture_focus as focus_module
    p=o.doc(envelope_ref);keys={'kind','authority','actor_source','original_focus','original_archive','after_focus','after_archive','read_intent','natural_exit','source_release','sources','input_performed'}
    o.need(set(p)==keys and p['kind']=='original-capture-window-readonly-effect-envelope-v1'and p['authority']==expected_authority and p['input_performed']is False,'window-effect-envelope-authority')
    a=o.doc(expected_authority);ak={'kind','original_focus','source_release','actor_source','sources','not_before','expires_at','max_reads','input_budget','effect_outdir'}
    o.need(set(a)==ak and a['kind']=='root-approved-original-capture-window-readonly-effect-once-v1'and type(a['max_reads'])is int and a['max_reads']==3 and type(a['input_budget'])is int and a['input_budget']==0,'window-effect-explicit-read-authority')
    o.need(p['original_focus']==a['original_focus']and p['source_release']==a['source_release']==WINDOW_PUBLISHED_SOURCE and p['actor_source']==a['actor_source']and p['sources']==a['sources'],'window-effect-authority-pins')
    o.raw(p['actor_source']);sources=p['sources'];o.need(sources==expected_sources,'window-effect-all-source-pins');o.need(len(sources)==160 and len({r['path']for r in sources})==160,'window-effect-source160')
    focus_path=str(o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_focus.py');o.need(sum(r=={'path':focus_path,'sha256':CAPTURE_FOCUS_AFTER}for r in sources)==1,'window-effect-fixed-verifier-source')
    # Every producer source is immutable evidence. Future code deployments must
    # supply reviewed archives, not silently bypass these physical pins.
    for r in sources:_capture_focus_code_raw(r,source_successor)
    start=_window_time(a['not_before']);end=_window_time(a['expires_at']);o.need(0<(end-start).total_seconds()<=300,'window-effect-bounded-read-window')
    directory=Path(a['effect_outdir']);o.need(directory.is_absolute()and Path(envelope_ref['path'])==directory/'effect-proof.json'and Path(p['original_archive']['path'])==directory/'original-focus.json'and p['original_archive']['sha256']==p['original_focus']['sha256'],'window-effect-canonical-envelope-archive')
    o.need(p['after_archive']['sha256']==p['after_focus']['sha256']and Path(p['after_archive']['path'])==directory/'completed-focus.json','window-effect-canonical-after-archive');before=o.doc(p['original_archive']);after=o.doc(p['after_archive']);o.need(p['after_focus']['path']==p['original_focus']['path']and before['binding']==after['binding']and before['kind']==after['kind']=='review-capture-focus-events-v1','window-effect-same-journal-binding')
    binding=before['binding'];manifest=o.doc(binding['manifest']);key=__import__('hashlib').sha256(json.dumps({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    # Existing library digest is the authority for canonical focus path.
    key=focus_module.previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])})
    journal=Path(manifest['source']['path']).parent/'.review-capture-focus'/(key+'.json');o.need(Path(p['original_focus']['path'])==journal,'window-effect-canonical-original-journal')
    focus_module.validate_events(before,binding);focus_module.validate_events(after,binding)
    o.need(len(before['events'])==len(after['events'])==1,'window-effect-sole-event');be=before['events'][0];ae=after['events'][0];bs=be['window_focus'];ws=ae['window_focus']
    o.need(be['state']=='unknown'and bs['state']=='unknown'and ae['state']=='complete'and ws['state']=='complete'and len(be['calls'])==1 and be['calls'][0]['state']=='confirmed'and ae['calls']==be['calls']and not be.get('native_focus')and not ae.get('native_focus'),'window-effect-only-existing-unknown')
    stage_changed={'state','after','effect','completed_at','effect_checks'};event_changed={'state','after','completed_at','outcome','window_focus'}
    o.need({k:v for k,v in ws.items()if k not in stage_changed}=={k:v for k,v in bs.items()if k not in stage_changed}and {k:v for k,v in ae.items()if k not in event_changed}=={k:v for k,v in be.items()if k not in event_changed},'window-effect-original-input-history')
    o.need({k:v for k,v in after.items()if k not in ('events','reads')}=={k:v for k,v in before.items()if k not in ('events','reads')}and after['reads'][:len(before['reads'])]==before['reads'],'window-effect-state-read-prefix')
    newreads=after['reads'][len(before['reads']):];checks=ws.get('effect_checks',[]);prefix=bs.get('effect_checks',[]);o.need(checks[:len(prefix)]==prefix,'window-effect-old-check-prefix');checks=checks[len(prefix):]
    o.need(1<=len(newreads)<=3 and 1<=len(checks)<=3 and len({r['path']for r in newreads})==len(newreads),'window-effect-read-budget')
    o.need(Path(p['read_intent']['path'])==directory/'read-intent.json'and Path(p['natural_exit']['path'])==directory/'exit.json','window-effect-fixed-stage-paths')
    intent=o.doc(p['read_intent']);o.need(set(intent)=={'kind','authority','original_focus','actor_source','source_release','started_at','operation','argv'}and intent['kind']=='original-window-effect-readonly-intent-v1'and intent['authority']==expected_authority and intent['original_focus']==p['original_focus']and intent['actor_source']==p['actor_source']and intent['source_release']==p['source_release']and intent['operation']=='ensure-original-readonly-no-input','window-effect-original-read-intent')
    argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),p['actor_source']['path'],'--authority',expected_authority['path'],'--sha256',expected_authority['sha256']];o.need(intent['argv']==argv,'window-effect-fixed-reader-argv')
    begun=_window_time(intent['started_at']);o.need(start<=begun<end,'window-effect-read-start')
    for r in newreads:
        v=o.doc(r);o.need(set(v)=={'command','response','observed_at'}and v['command']=={'op':'tabs'}and v['response'].get('ok')is True and type(v['response'].get('result'))is list and begun<=_window_time(v['observed_at'])<end,'window-effect-tabs-only-raw')
    for i,r in enumerate(checks):
        v=o.doc(r);ob=o.doc(v['observation']);o.need(v['number']==i+1 and v['observation']['path'].startswith(str(journal.with_suffix(''))+'/')and ob['tabs_reply']in newreads and ob['tabs']==o.doc(ob['tabs_reply'])['response']['result']and begun<=_window_time(ob['observed_at'])<end,'window-effect-check-fresh-raw-tabs')
    last=o.doc(checks[-1]);o.need(last.get('classification')=='ready'and last.get('effect')==o.doc(ws['effect'])and ws['after']==last['observation']and ae['after']==ws['after']and ae['outcome']=='readonly-original-effect-confirmed'and begun<=_window_time(ws['completed_at'])<=_window_time(ae['completed_at'])<end,'window-effect-exact-final-effect')
    ex=o.doc(p['natural_exit']);o.need(set(ex)=={'kind','intent','authority','returncode','stdout','stderr','started_at','ended_at','argv','elapsed_seconds'}and ex['kind']=='original-window-effect-readonly-natural-exit-v1'and ex['intent']==p['read_intent']and ex['authority']==expected_authority and type(ex['returncode'])is int and ex['returncode']==0 and ex['started_at']==intent['started_at']and _window_time(ae['completed_at'])<=_window_time(ex['ended_at'])<end and o.raw(ex['stderr'])==b'','window-effect-natural-exit')
    o.need(ex['argv']==argv and type(ex['elapsed_seconds'])in (int,float)and ex['elapsed_seconds']==(_window_time(ex['ended_at'])-begun).total_seconds(),'window-effect-natural-argv-elapsed')
    o.need(Path(ex['stdout']['path'])==directory/'stdout.json'and Path(ex['stderr']['path'])==directory/'stderr.txt','window-effect-fixed-stdio-paths')
    result=json.loads(o.raw(ex['stdout']));o.need(result=={'ready':True,'focus_event':be['number'],'input_dispatched':False,'native_input_dispatched':False,'journal':p['after_focus']},'window-effect-exact-no-input-result')
    return {'envelope':envelope_ref,'original_focus':p['original_focus'],'after_focus':p['after_focus'],'binding':binding,'source_release':p['source_release'],'evidence':[envelope_ref,expected_authority,p['actor_source'],p['original_archive'],p['after_archive'],p['read_intent'],p['natural_exit'],ex['stdout'],ex['stderr'],*newreads,*checks,ws['effect'],*[o.doc(r)['observation']for r in checks]]}

def window_hold_shared_transform(parent,engine,proof_ref):
    """Exact immutable-history transformation, no writer/status setter API."""
    p=copy.deepcopy(parent);e=copy.deepcopy(engine)
    o.need(p['status']=='hold'and p.get('error')=='execution-child-stopped'and e['status']=='hold'and e.get('error')==WINDOW_HOLD_ERROR and len(e['calls'])==47 and e['calls'][46]['state']=='failed'and e['calls'][46]['error']==WINDOW_HOLD_ERROR and len(p['calls'])==3,'window-hold-exact-before')
    for v in (p,e):
        error=v.pop('error');v['status']='running';v[WINDOW_HOLD_FIELD]=proof_ref;v.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof_ref})
    # All47 calls retained: one exact proof grants an admission exception only.
    e.setdefault('resolved_window_failures',[]).append({'index':46,'call':copy.deepcopy(e['calls'][46]),'recovery':proof_ref})
    return p,e

def _window_hold_admission(parent,engine,proof_ref,*,qualified_effect,source_codes):
    """Pure checked-facts helper. Public verifier below must fully qualify inputs.
    No public caller may substitute strings/booleans for qualified effects.
    """
    p=o.doc(proof_ref);beforep=o.doc(p['parent_archive']);beforee=o.doc(p['engine_archive']);expectedp,expectede=window_hold_shared_transform(beforep,beforee,proof_ref)
    o.need(p['kind']==WINDOW_HOLD_KIND and p['focus_effect']==qualified_effect['envelope']and p['order']==beforep['order']==beforee['order']==parent['order']==engine['order']and p['source_codes']==source_codes,'window-hold-typed-proof')
    for current,expected,original in ((parent,expectedp,beforep),(engine,expectede,beforee)):
        variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass','phase','index','companies','business_journals','delivery','handoff','waiting_for','acceptance'}if current is engine else {'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
        for k in set(expected)-variable:o.need(current.get(k)==expected[k],'window-hold-preserved-metadata')
        o.need(current['calls'][:len(original['calls'])]==original['calls'],'window-hold-original-calls-prefix')
    o.need(parent.get(WINDOW_HOLD_FIELD)==engine.get(WINDOW_HOLD_FIELD)==proof_ref and engine['resolved_window_failures']==expectede['resolved_window_failures'],'window-hold-common-proof')
    o.need(len(source_codes)==160 and len({r['path']for r in source_codes})==160,'window-hold-source160')
    failed=[*p['previous_failed_children'],beforep['calls'][2]];o.need(len(failed)==3 and all(sum(c==x for x in parent['calls'])==1 for c in failed),'window-hold-three-exact-child-members')
    return {'kind':WINDOW_HOLD_KIND,'proof':proof_ref,'code_refs':source_codes,'failed_calls':failed,'failed_engine_indices':[46],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],*qualified_effect['evidence']]}

def _window_hold_case(p):
    """Specific original failed member, not arbitrary failed/unknown exceptions."""
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);folder=o.location(parent['order']);order=o.validate(parent['order']);worker=o.doc(p['worker_exit']);request=o.doc(worker['request']);response=o.doc(worker['response'])
    o.need(p['original_parent']['path']==str(folder/'launcher.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['original_engine']['path']==str(folder/'engine.json')and p['engine_archive']['sha256']==p['original_engine']['sha256']and parent[DATE_SOURCE_FIELD]==WINDOW_PUBLISHED_SOURCE,'window-hold-canonical-before')
    o.need(parent['order']==engine['order']==p['order']and parent['scope_sha256']==engine['scope_sha256']==order['scope_sha256']and parent['status']=='hold'and parent['error']=='execution-child-stopped'and len(parent['calls'])==3 and all(c['state']=='returned'for c in parent['calls'])and not parent.get('completion')and not parent.get('child'),'window-hold-original-parent')
    o.need(engine['status']=='hold'and engine['error']==WINDOW_HOLD_ERROR and len(engine['calls'])==47 and engine['phase']=='collect'and engine['index']==0 and not engine.get('handoff')and not engine.get('acceptance')and not engine.get('delivery')and not engine.get('completion'),'window-hold-original-engine')
    failed=engine['calls'][46];o.need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['state']=='failed'and failed['error']==WINDOW_HOLD_ERROR and failed['step']=='collect'and failed['company_index']==0 and failed['context']=={'order':order,'company':order['companies'][0],'artifacts':engine['companies'][0]['artifacts'],'folder':str(folder/'companies/0'),'phase':'collect'},'window-hold-exact-resultless-failed46')
    for i,c in enumerate(engine['calls'][:46]):o.need(c['state']=='returned'and c.get('applied')is True and c['result']['path']==str(folder/'receipts'/(str(i+1).zfill(5)+'.json')),'window-hold-returned46-prefix');o.doc(c['result'])
    child=parent['calls'][2];launch=o.doc(child['launch']);ex=o.doc(child['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(child['launch']['path']==str(folder/'children/0002-launch.json')and child['result']['path']==str(folder/'children/0002-exit.json')and child['argv']==launch['argv']==ex['argv']==argv and launch['index']==2 and launch['order']==parent['order']and ex['launch']==child['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':WINDOW_HOLD_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'window-hold-exact-child2')
    o.need(worker['returncode']==0 and worker['attempt_id']==request['attempt_id']==response['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['task']['id']==response['task_id']==p['task_id']and request['attempt_id']==p['attempt_id']and request['context']['order']==response['context']['order']==parent['order']and request['task']['outer']==p['outer'],'window-hold-natural-worker-original-outer')
    o.need(p['operator_job']==engine['companies'][0]['artifacts']['unit_artifacts']['work_order']and p['original_operator']['path']==o.doc(parent[FILTER_READONLY_FIELD])['original_operator']['path'],'window-hold-original-operator-job')
    job=o.doc(p['operator_job']);operator=o.doc(p['operator_archive']);o.need(p['operator_archive']['sha256']==p['original_operator']['sha256']and p['original_operator']['path']==job['workflow_path']and p['operator_job']['path']==job['work_order_path']and operator['work_order_id']==job['work_order_id']and operator['tab_id']==parent['tab_id']and operator['calls'][:5]==o.doc(o.doc(parent[FILTER_READONLY_FIELD])['original_archives'][2]['archive'])['calls']and all(c['state']=='confirmed'for c in operator['calls']),'window-hold-operator-confirmed-prefix')
    date_restore_epoch_verify(job,operator)
    inv=p['preinput_inventory'];before_focus=o.doc(o.doc(p['focus_effect'])['original_archive']);manifest_ref=before_focus['binding']['manifest'];manifest=o.doc(manifest_ref);unit=Path(manifest['source']['path']).parent
    unit_artifacts=engine['companies'][0]['artifacts']['unit_artifacts'];key=unit_artifacts['keys'][unit_artifacts['frame_index']];expected_manifest={k:unit_artifacts[k]for k in ('job','source','envelope','profile','page')};expected_manifest.update(review_keys=[key],capture_key='complaint-parent:'+o.digest({'dispatch':order['dispatch_id'],'key':key,'source':unit_artifacts['source']['sha256']})[:40]);o.need(manifest==expected_manifest and manifest_ref['path']==str(unit/'frames'/o.digest(key)/'manifest.json')and before_focus['binding']['source']==unit_artifacts['source'],'window-hold-original-current-frame-manifest')
    o.need(inv=={'kind':'capture-window-hold-preinput-inventory-v1','manifest':manifest_ref,'capture_state_files':[],'region_state_files':[],'capture_output_files':[],'resultless_receipt':str(folder/'receipts/00047.json')},'window-hold-preinput-inventory-shape')
    o.need(p['previous_failed_children']==parent['calls'][:2],'window-hold-previous-exact-failed-members')
    return parent,engine

def _window_hold_source_root(reference):
    root=o.doc(reference);expected={'kind','previous_source_release','published','test_projection_only','reviewed_by','targets','window_effect_hold_successor','binding','freeze','intent','published_at','review'}
    o.need(set(root)==expected and root['kind']=='supervisor-reviewed-independent-native-window-effect-source-successor-v1'and root['previous_source_release']==WINDOW_PUBLISHED_SOURCE and root['published']is True and root['test_projection_only']is False and root['reviewed_by']=='workshop-director','window-hold-reviewed-four-source-root')
    paths={str(o.PROJECT/'skills/negative-review-complaints/scripts'/n)for n in ('initial_ledger_recovery.py','complaint_execution.py','review_capture_focus.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_orchestration.py')}
    ts=root['targets'];o.need(len(ts)==4 and {t['target']for t in ts}==paths,'window-hold-exact-four-targets')
    for t in ts:
        o.need(set(t)=={'target','mode','old_sha256','before','after'}and type(t['mode'])is int and t['mode']==(384 if Path(t['target']).name=='review_capture_focus.py'else 420) and t['old_sha256']==t['before']['sha256']and Path(t['before']['path'])==Path(reference['path']).parent/(Path(t['target']).name+'.before'),'window-hold-before-archive');o.raw(t['before']);o.raw(t['after'])
    a=root['window_effect_hold_successor'];_verify_native_activation_policy(a['effect_authority'],a['original_focus'])
    o.need(set(a)=={'original_parent','original_engine','original_operator','worker_exit','original_focus','order','effect_authority'}and root['binding']=={k:a[k]for k in ('original_parent','original_engine','original_operator','worker_exit','order')},'window-hold-source-binding')
    frozen=o.doc(root['freeze']);o.need(set(frozen)=={'kind','execution_authorized','files'}and frozen['kind']=='window-effect-typed-admission-source-freeze-v1'and frozen['execution_authorized']is False and all(t['after']in frozen['files']for t in ts),'window-hold-source-freeze')
    for r in frozen['files']:o.raw(r)
    review=o.doc(root['review']);o.need(review=={'kind':'root-reviewed-original-window-effect-typed-admission-source-v1','previous_source_release':WINDOW_PUBLISHED_SOURCE,'targets':ts,'binding':root['binding'],'freeze':root['freeze'],'verdict':'source-candidate-approved-not-runtime-metadata'},'window-hold-source-reviewed-exact-pair')
    intent=o.doc(root['intent']);o.need(set(intent)=={'kind','previous_source_release','targets','freeze','review','binding','at'}and intent['kind']=='window-effect-typed-admission-source-publication-intent-v1'and all(intent[k]==root[k]for k in ('previous_source_release','targets','freeze','review','binding'))and _window_time(intent['at'])<=_window_time(root['published_at']),'window-hold-source-publication-binding')
    return root,{t['target']:t for t in ts}

def window_hold_source_codes(parent,release_ref,*,installed=True):
    root,ts=_window_hold_source_root(release_ref);base=copy.deepcopy(parent);base.pop(WINDOW_HOLD_FIELD,None);base[DATE_SOURCE_FIELD]=WINDOW_PUBLISHED_SOURCE
    # New source-only branch must never weaken the old graph or skip 156 slots.
    old=date_restore_source_codes(base,WINDOW_PUBLISHED_SOURCE,installed=False,archive_successor=release_ref);by={r['path']:r for r in old};o.need(len(old)==len(by)==160,'window-hold-baseline160')
    for path,t in ts.items():o.need(t['old_sha256']==by[path]['sha256'],'window-hold-source-continuous-CAS')
    codes=[{'path':r['path'],'sha256':ts[r['path']]['after']['sha256']}if r['path']in ts else r for r in old]
    o.need(sum(a!=b for a,b in zip(old,codes))==4,'window-hold-only-four-deltas')
    if installed:
        for r in codes:o.raw(r)
    return codes

def verify_window_hold(current,proof_ref,*,installed=True):
    """Public full verification; no checked flag, injected validator or cache."""
    p=o.doc(proof_ref);o.need(set(p)=={'kind','order','task_id','attempt_id','outer','original_parent','original_engine','original_operator','parent_archive','engine_archive','operator_archive','operator_job','worker_exit','previous_failed_children','focus_effect','effect_authority','source_release','source_codes','preinput_inventory','at'}and p['kind']==WINDOW_HOLD_KIND and current.get(WINDOW_HOLD_FIELD)==proof_ref and _window_time(p['at']),'window-hold-proof-schema')
    parent,engine=_window_hold_case(p);folder=o.location(parent['order']);base=folder/'.window-effect-hold-recovery'/p['original_parent']['sha256'];o.need(Path(proof_ref['path'])==base/'proof.json'and all(Path(p[n+'_archive']['path'])==base/(n+'-before.json')for n in ('parent','engine','operator')),'window-hold-canonical-proof-archives')
    root,_=_window_hold_source_root(p['source_release']);o.need(root['window_effect_hold_successor']=={'original_parent':p['original_parent'],'original_engine':p['original_engine'],'original_operator':p['original_operator'],'worker_exit':p['worker_exit'],'original_focus':o.doc(p['focus_effect'])['original_focus'],'order':p['order'],'effect_authority':_window_root_effect_ref(p['effect_authority'])},'window-hold-root-exact-authority')
    import review_capture_focus as focus
    codes=window_hold_source_codes(parent,p['source_release'],installed=installed);_,ts=_window_hold_source_root(p['source_release']);oldcodes=[{'path':r['path'],'sha256':ts[r['path']]['old_sha256']}if r['path']in ts else r for r in codes]
    effect=verify_window_effect_envelope(p['focus_effect'],expected_authority=p['effect_authority'],expected_sources=oldcodes,source_successor=p['source_release']);o.need(_window_time(o.doc(o.doc(p['focus_effect'])['natural_exit'])['ended_at'])<=_window_time(p['at']),'window-hold-proof-after-effect')
    o.need(effect['binding']['manifest']==o.doc(o.doc(p['focus_effect'])['original_archive'])['binding']['manifest']and effect['binding']['pid']==parent['pid']and effect['binding']['scope']['tabId']==parent['tab_id'],'window-hold-original-effect-scope')
    # Existing historical FILTER facts remain fully verified with the narrowly
    # bounded new source archives; no archived Python is executed.
    _DATE_LEGACY_FILTER_VERIFY(parent,parent[FILTER_READONLY_FIELD],installed=False,source_successor=p['source_release'])
    archived_operator=o.doc(p['operator_archive']);live_operator=o.doc(o.ref(p['original_operator']['path']));o.need(live_operator['calls'][:len(archived_operator['calls'])]==archived_operator['calls']and all(c['state']=='confirmed'for c in live_operator['calls'])and live_operator.get(DATE_RESTORE_FIELD)==archived_operator.get(DATE_RESTORE_FIELD),'window-hold-live-operator-prefix');date_restore_epoch_verify(o.doc(p['operator_job']),live_operator)
    actual_engine=o.doc(o.ref(folder/'engine.json'));admission=_window_hold_admission(current,actual_engine,proof_ref,qualified_effect=effect,source_codes=codes)
    # After proof, original event and reads must remain an exact prefix. New
    # ordinary focus events are still governed independently by capture guards.
    saved=o.doc(o.doc(p['focus_effect'])['after_archive']);live=o.doc(o.ref(effect['after_focus']['path']));focus.validate_events(live,saved['binding']);o.need(live['binding']==saved['binding']and live['events'][:1]==saved['events']and live['reads'][:len(saved['reads'])]==saved['reads'],'window-hold-live-effect-prefix')
    return admission

_WINDOW_HOLD_OLD_VERIFY=verify_filter_readonly
_WINDOW_HOLD_OLD_ENGINE_CALLS=engine_calls
def verify_filter_readonly(current,proof_ref,*,installed=True):
    if current.get(WINDOW_HOLD_FIELD):
        o.need(current[FILTER_READONLY_FIELD]==proof_ref,'window-hold-old-filter-marker');return verify_window_hold(current,current[WINDOW_HOLD_FIELD],installed=installed)
    return _WINDOW_HOLD_OLD_VERIFY(current,proof_ref,installed=installed)
def engine_calls(engine):
    if not engine.get(WINDOW_HOLD_FIELD):return _WINDOW_HOLD_OLD_ENGINE_CALLS(engine)
    parent=o.doc(o.ref(phase_directory(engine)/'launcher.json'));o.need(parent.get(WINDOW_HOLD_FIELD)==engine[WINDOW_HOLD_FIELD],'window-hold-parent-engine-marker');a=verify_window_hold(parent,engine[WINDOW_HOLD_FIELD]);o.need(engine==o.doc(o.ref(phase_directory(engine)/'engine.json')),'window-hold-engine-canonical');return [c for i,c in enumerate(engine['calls'])if i not in a['failed_engine_indices']]


def plan_window_hold(parent_ref,engine_ref,operator_ref,job_ref,worker_ref,effect_ref,effect_authority,source_release):
    """Pure qualification/plan. Caller needs separate metadata grant and locks.
    No proof/archive/result is created; no status or journal is written.
    """
    import review_capture_focus as focus
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);root,_=_window_hold_source_root(source_release);codes=window_hold_source_codes(parent,source_release);_,ts=_window_hold_source_root(source_release);oldcodes=[{'path':r['path'],'sha256':ts[r['path']]['old_sha256']}if r['path']in ts else r for r in codes]
    effect=verify_window_effect_envelope(effect_ref,expected_authority=effect_authority,expected_sources=oldcodes,source_successor=source_release);o.raw(effect['after_focus'])
    manifest=effect['binding']['manifest'];focus.no_capture(manifest);folder=o.location(parent['order']);slot=folder/'receipts/00047.json';o.need(not slot.exists()and not slot.is_symlink(),'window-hold-receipt47-absent')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);at=datetime.now(timezone.utc).isoformat();p={'kind':WINDOW_HOLD_KIND,'order':parent['order'],'task_id':request['task']['id'],'attempt_id':request['attempt_id'],'outer':request['task']['outer'],'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'parent_archive':parent_ref,'engine_archive':engine_ref,'operator_archive':operator_ref,'operator_job':job_ref,'worker_exit':worker_ref,'previous_failed_children':parent['calls'][:2],'focus_effect':effect_ref,'effect_authority':effect_authority,'source_release':source_release,'source_codes':codes,'preinput_inventory':{'kind':'capture-window-hold-preinput-inventory-v1','manifest':manifest,'capture_state_files':[],'region_state_files':[],'capture_output_files':[],'resultless_receipt':str(slot)},'at':at}
    _window_hold_case(p);o.need(root['window_effect_hold_successor']=={'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker_exit':worker_ref,'original_focus':o.doc(effect_ref)['original_focus'],'order':parent['order'],'effect_authority':_window_root_effect_ref(effect_authority)},'window-hold-plan-root-authority')
    base=folder/'.window-effect-hold-recovery'/parent_ref['sha256']
    for name in ('parent','engine','operator'):p[name+'_archive']={'path':str(base/(name+'-before.json')),'sha256':p['original_'+name]['sha256']}
    return p


def window_hold_pair_state(current_parent,current_engine,original_parent,original_engine,proof_ref):
    """Read-only exact initial transaction continuation classification.
    Caller must already have run full plan/proof+lease/authority guards. No write.
    """
    after_parent,after_engine=window_hold_shared_transform(original_parent,original_engine,proof_ref)
    o.need(current_parent in (original_parent,after_parent)and current_engine in (original_engine,after_engine),'window-hold-pair-CAS-conflict')
    pair=(current_parent==after_parent,current_engine==after_engine)
    o.need(pair!=(True,False),'window-hold-pair-wrong-commit-order')
    return {(False,False):'before',(False,True):'engine-written',(True,True):'complete'}[pair]

_WINDOW_CAPTURE_PREVIOUS_RAW=_capture_focus_code_raw
def _capture_focus_code_raw(reference,source_successor=None):
    if source_successor is not None and o.doc(source_successor).get('kind')=='supervisor-reviewed-independent-native-window-effect-source-successor-v1':
        root,targets=_window_hold_source_root(source_successor)
        t=targets.get(reference['path'])
        if t is not None and reference['sha256']==t['old_sha256']:return o.raw(t['before'])
        return _WINDOW_CAPTURE_PREVIOUS_RAW(reference,WINDOW_PUBLISHED_SOURCE)
    return _WINDOW_CAPTURE_PREVIOUS_RAW(reference,source_successor)

_NATIVE_WINDOW_PREVIOUS_ENVELOPE=verify_window_effect_envelope
NATIVE_EFFECT_ENVELOPE='independent-native-after-window-effect-envelope-v1'
NATIVE_EFFECT_AUTHORITY='root-approved-independent-native-window-activation-once-v1'
def _window_root_effect_ref(reference):
    value=o.doc(reference)
    return value['policy'] if value.get('kind')==NATIVE_EFFECT_AUTHORITY else reference

def _verify_native_activation_policy(reference,original_focus):
    policy=o.doc(reference);keys={'kind','execution_authorized','original_focus','actor_source','sources','effect_outdir','native_input_budget','AXRaise_budget','max_tabs_reads'}
    o.need(set(policy)==keys and policy['kind']=='reviewed-independent-native-window-activation-policy-v1'and policy['execution_authorized']is False and policy['original_focus']==original_focus and type(policy['native_input_budget'])is int and policy['native_input_budget']==1 and type(policy['AXRaise_budget'])is int and policy['AXRaise_budget']==0 and type(policy['max_tabs_reads'])is int and policy['max_tabs_reads']==5,'native-effect-nonexecution-policy')
    return policy

def verify_native_window_effect_envelope(reference,*,expected_authority,expected_sources,source_successor):
    import review_capture_focus as focus
    p=o.doc(reference);keys={'kind','authority','actor_source','original_focus','original_archive','after_focus','after_archive','worker_intent','natural_exit','source_release','sources','input_performed'}
    o.need(set(p)==keys and p['kind']==NATIVE_EFFECT_ENVELOPE and p['authority']==expected_authority and p['source_release']==source_successor and p['input_performed']is True,'native-effect-exact-envelope')
    root,targets=_window_hold_source_root(source_successor);a=o.doc(expected_authority);ak={'kind','original_focus','source_release','actor_source','sources','not_before','expires_at','max_tabs_reads','native_input_budget','AXRaise_budget','effect_outdir','policy'}
    o.need(set(a)==ak and a['kind']==NATIVE_EFFECT_AUTHORITY and type(a['max_tabs_reads'])is int and a['max_tabs_reads']==5 and type(a['native_input_budget'])is int and a['native_input_budget']==1 and type(a['AXRaise_budget'])is int and a['AXRaise_budget']==0,'native-effect-explicit-one-input-authority')
    o.need(a['policy']==root['window_effect_hold_successor']['effect_authority'] and a['original_focus']==p['original_focus']==root['window_effect_hold_successor']['original_focus'] and a['source_release']==source_successor and a['actor_source']==p['actor_source']and p['actor_source']in o.doc(root['freeze'])['files'],'native-effect-root-actor-binding');policy=_verify_native_activation_policy(a['policy'],a['original_focus']);o.need(policy['actor_source']==a['actor_source']and policy['sources']==a['sources']and policy['effect_outdir']==a['effect_outdir'],'native-effect-policy-grant-binding')
    current_codes=[{'path':r['path'],'sha256':targets[r['path']]['after']['sha256']}if r['path']in targets else r for r in expected_sources];o.need(len(current_codes)==len({r['path']for r in current_codes})==160 and p['sources']==a['sources']==current_codes,'native-effect-current-source160')
    for r in current_codes:_region_history_code_raw(r)
    o.raw(p['actor_source']);start=_window_time(a['not_before']);end=_window_time(a['expires_at']);o.need(0<(end-start).total_seconds()<=300,'native-effect-bounded-authority')
    directory=Path(a['effect_outdir']);o.need(Path(reference['path'])==directory/'effect-proof.json'and Path(p['original_archive']['path'])==directory/'original-focus.json'and p['original_archive']['sha256']==p['original_focus']['sha256']and Path(p['after_archive']['path'])==directory/'completed-focus.json'and p['after_archive']['sha256']==p['after_focus']['sha256'],'native-effect-fixed-archives')
    before=o.doc(p['original_archive']);after=o.doc(p['after_archive']);binding=before['binding'];manifest=o.doc(binding['manifest']);key=focus.previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});journal=Path(manifest['source']['path']).parent/'.review-capture-focus'/(key+'.json')
    o.need(p['original_focus']['path']==p['after_focus']['path']==str(journal)and before['kind']==after['kind']=='review-capture-focus-events-v1'and after['binding']==binding,'native-effect-same-canonical-journal');focus.validate_events(before,binding);focus.validate_events(after,binding)
    o.need(len(before['events'])==len(after['events'])==1,'native-effect-sole-event');be=before['events'][0];ae=after['events'][0];native=ae.get('native_focus')
    o.need(be['state']=='unknown'and be['window_focus']['state']=='unknown'and not be.get('native_focus')and ae['state']=='complete'and ae['window_focus']==be['window_focus']and native and native['state']=='complete'and native['window_fallback']['window_stage']==be['window_focus']and ae['calls']==be['calls'],'native-effect-preserve-prior-unknown')
    changed={'state','after','completed_at','outcome','native_focus'};o.need({k:v for k,v in ae.items()if k not in changed}=={k:v for k,v in be.items()if k not in changed}and {k:v for k,v in after.items()if k not in ('events','reads')}=={k:v for k,v in before.items()if k not in ('events','reads')}and after['reads'][:len(before['reads'])]==before['reads'],'native-effect-only-independent-stage')
    focus.validate_window_native_admission(ae,binding);newreads=after['reads'][len(before['reads']):];o.need(3<=len(newreads)<=a['max_tabs_reads']and len({r['path']for r in newreads})==len(newreads),'native-effect-read-budget')
    intent=o.doc(p['worker_intent']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),p['actor_source']['path'],'--authority',expected_authority['path'],'--sha256',expected_authority['sha256']]
    o.need(Path(p['worker_intent']['path'])==directory/'worker-intent.json'and intent=={'kind':'independent-native-worker-intent-v1','authority':expected_authority,'original_focus':p['original_focus'],'source_release':source_successor,'actor_source':p['actor_source'],'argv':argv,'started_at':intent['started_at']},'native-effect-worker-intent');begun=_window_time(intent['started_at']);o.need(start<=begun<end,'native-effect-worker-start')
    for r in newreads:
        raw=o.doc(r);o.need(set(raw)=={'command','response','observed_at'}and raw['command']=={'op':'tabs'}and raw['response'].get('ok')is True and begun<=_window_time(raw['observed_at'])<end,'native-effect-tabs-only')
    observations=[*native['window_fallback']['observations'],native['after']]
    for r in observations:
        ob=o.doc(r);o.need(Path(r['path']).parent==journal.with_suffix('')and ob['tabs_reply']in newreads and ob['tabs']==o.doc(ob['tabs_reply'])['response']['result']and begun<=_window_time(ob['observed_at'])<end,'native-effect-fresh-observation-raw')
    si=o.doc(native['stage_intent']);o.need(Path(native['stage_intent']['path']).parent==journal.with_suffix('')and si['native_stage']['state']=='unknown'and begun<=_window_time(native['intent_at'])<=_window_time(o.doc(native['after'])['observed_at'])<=_window_time(native['completed_at'])<=_window_time(ae['completed_at'])<end,'native-effect-stage-input-time')
    reply=o.doc(native['reply']);o.need(reply.get('result',{}).get('request_accepted')is True and reply['result'].get('launch_used')is False and reply['result'].get('pid')==binding['pid']and reply['result'].get('bundle')=='com.google.Chrome','native-effect-native-result')
    o.need(ae['after']==native['after'],'native-effect-final-observation')
    ex=o.doc(p['natural_exit']);ek={'kind','intent','authority','returncode','stdout','stderr','started_at','ended_at','argv','elapsed_seconds'}
    o.need(set(ex)==ek and Path(p['natural_exit']['path'])==directory/'exit.json'and ex['kind']=='independent-native-worker-natural-exit-v1'and ex['intent']==p['worker_intent']and ex['authority']==expected_authority and type(ex['returncode'])is int and ex['returncode']==0 and ex['argv']==argv and ex['started_at']==intent['started_at']and _window_time(ae['completed_at'])<=_window_time(ex['ended_at'])<end and ex['elapsed_seconds']==(_window_time(ex['ended_at'])-begun).total_seconds(),'native-effect-natural-exit')
    o.need(Path(ex['stdout']['path'])==directory/'stdout.json'and Path(ex['stderr']['path'])==directory/'stderr.txt'and o.raw(ex['stderr'])==b''and o.doc(ex['stdout'])=={'ready':True,'focus_event':be['number'],'input_dispatched':True,'native_input_dispatched':True,'journal':p['after_focus']},'native-effect-worker-output')
    return {'envelope':reference,'original_focus':p['original_focus'],'after_focus':p['after_focus'],'binding':binding,'source_release':source_successor,'evidence':[reference,expected_authority,p['actor_source'],p['original_archive'],p['after_archive'],p['worker_intent'],p['natural_exit'],ex['stdout'],ex['stderr'],native['readonly_hold'],*o.doc(native['readonly_hold'])['attempts'],native['stage_intent'],native['reply'],native['window_effect'],*observations,*newreads]}
def verify_window_effect_envelope(envelope_ref,*,expected_authority,expected_sources,source_successor=None):
    p=o.doc(envelope_ref)
    if p.get('kind')==NATIVE_EFFECT_ENVELOPE:
        o.need(source_successor is not None,'native-effect-reviewed-source-required');return verify_native_window_effect_envelope(envelope_ref,expected_authority=expected_authority,expected_sources=expected_sources,source_successor=source_successor)
    return _NATIVE_WINDOW_PREVIOUS_ENVELOPE(envelope_ref,expected_authority=expected_authority,expected_sources=expected_sources,source_successor=source_successor)

def main():
    p=argparse.ArgumentParser();p.add_argument('--launcher',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--worker-exit',required=True);p.add_argument('--worker-exit-sha256',required=True);p.add_argument('--release',required=True);p.add_argument('--release-sha256',required=True);p.add_argument('--plan-only',action='store_true');p.add_argument('--unapplied-proof');p.add_argument('--failed-recovery-cli');p.add_argument('--engine-sha256');p.add_argument('--old-source',action='append',required=True,help='JSON exact path/sha ref for each of four reviewed before files');a=p.parse_args()
    try:
        fn=recover
        arguments=[{'path':a.launcher,'sha256':a.original_sha256}]
        if a.plan_only:
            o.need(a.engine_sha256,'initial-plan-engine-sha-required');fn=recover_second;arguments.append({'path':str(Path(a.launcher).with_name('engine.json')),'sha256':a.engine_sha256})
        arguments.extend([{'path':a.worker_exit,'sha256':a.worker_exit_sha256},{'path':a.release,'sha256':a.release_sha256},[json.loads(x) for x in a.old_source]])
        if a.unapplied_proof or a.failed_recovery_cli:
            o.need(a.plan_only and a.unapplied_proof and a.failed_recovery_cli,'initial-plan-v2-explicit-proof-and-cli');fn=recover_unapplied;arguments.extend([json.loads(a.unapplied_proof),json.loads(a.failed_recovery_cli)])
        value=fn(*arguments);print(json.dumps(value,ensure_ascii=False));return 0
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())

# Explicit command-local historical snapshots. Default remains uncached.
# This block wraps only archival computations; all public live-check bodies
# above remain unchanged. No reader/validator monkeypatch or persisted trust.
import contextlib as _hm_contextlib
import contextvars as _hm_contextvars
import functools as _hm_functools
import hashlib as _hm_hashlib
import stat as _hm_stat
import threading as _hm_threading

_HM_SCOPE = _hm_contextvars.ContextVar('window_hold_history_scope', default=None)
_HM_RECORDERS = _hm_contextvars.ContextVar('window_hold_history_recorders', default=())
_HM_BUSY = _hm_contextvars.ContextVar('window_hold_history_observer_busy', default=False)
_HM_AUDIT_INSTALLED = False

def _hm_authority_context():
    # A reviewed successor may bind a finite old-code archive reader in this
    # ContextVar. Partition the memo by the complete mapping, never by only
    # the old release args. The authority itself remains checked by its own
    # existing source validator; this token only prevents cross-context hits.
    context = globals().get('_REGION_HISTORY_SOURCE')
    return None if context is None else context.get()

def _hm_identity():
    return os.getpid(), _hm_threading.get_ident()

def _hm_path_token(value, *, directory=False):
    """Metadata only. Resolve every component to detect symlink retargeting.
    ctime is intentionally included: restoring mtime does not restore ctime.
    """
    p = Path(os.path.abspath(os.fsdecode(value)))
    try:
        p.lstat()
    except FileNotFoundError:
        # An attempted read may legally fall back (imports are one example).
        # Preserve the negative dependency instead of ignoring or trusting it.
        # A later creation, ancestor replacement or symlink redirect changes
        # this exact marker. Unrelated siblings are not dependencies.
        missing = []
        ancestor = p
        while True:
            try:
                ancestor.lstat()
                break
            except FileNotFoundError:
                missing.append(str(ancestor))
                ancestor = ancestor.parent
        components = []
        for part in (ancestor, *ancestor.parents):
            st = part.lstat()
            components.append((str(part), st.st_dev, st.st_ino, st.st_mode,
                               os.readlink(part) if _hm_stat.S_ISLNK(st.st_mode) else None))
        return ('absent', str(p.resolve(strict=False)), tuple(missing), tuple(components))
    chain = []
    for part in (p, *p.parents):
        s = part.lstat()
        chain.append((str(part), s.st_dev, s.st_ino, _hm_stat.S_IFMT(s.st_mode),
                      s.st_mode & 0o7777,
                      # Ancestor directory contents need a membership guard,
                      # not their noisy timestamp changed by unrelated saves.
                      s.st_size if part == p else None,
                      s.st_mtime_ns if part == p else None,
                      s.st_ctime_ns if part == p else None,
                      os.readlink(part) if _hm_stat.S_ISLNK(s.st_mode) else None))
    resolved = p.resolve(strict=True)
    rs = resolved.stat()
    token = (str(resolved), tuple(chain), rs.st_dev, rs.st_ino, rs.st_size,
             rs.st_mtime_ns, rs.st_ctime_ns, rs.st_mode)
    if directory:
        token += (tuple(sorted(os.listdir(p))),)
    return token

class _HistoryReadSet:
    def __init__(self, max_paths):
        self.paths = {}
        self.max_paths = max_paths
        self.valid = True
        self.failures = []
        self.reader_queries = {}
        self.reader_context = _hm_authority_context()

    def observe(self, value, directory=False):
        if not isinstance(value, (str, bytes, os.PathLike)):
            self.valid = False
            return
        key = (os.path.abspath(os.fsdecode(value)), bool(directory))
        if key in self.paths:
            # The original reader still validates every real read. Snapshot
            # freshness needs first/last metadata, not an ancestry walk for
            # every repeated read. ctime/inode differences at the end poison
            # the entry even when original content/mtime are restored.
            return
        try:
            token = _hm_path_token(key[0], directory=key[1])
            self.paths[key] = token
            # Only actual listdir/scandir observations depend on membership.
            # Creating an unrelated log beside an immutable input does not
            # change that file's own inode/content metadata or symlink chain.
            if len(self.paths) > self.max_paths:
                self.valid = False
        except (OSError, ValueError, RuntimeError) as error:
            self.valid = False
            if len(self.failures) < 8:
                self.failures.append((key[0], type(error).__name__))

    def unchanged(self):
        if not self.valid:
            return False
        if any(_dedup_reader_resolution(path, sha) != resolved for (path, sha), resolved in self.reader_queries.items()):
            return False
        try:
            return all(_hm_path_token(path, directory=is_dir) == old
                       for (path, is_dir), old in self.paths.items())
        except (OSError, ValueError, RuntimeError):
            return False

def _hm_audit(event, args):
    """One process-local audit observer, inert outside historical computation.
    It observes nested real readers across imported modules without replacing
    o.raw/o.doc/Path or suppressing any validation. No hook performs writes.
    """
    recorders = _HM_RECORDERS.get()
    if not recorders or _HM_BUSY.get():
        return
    busy = _HM_BUSY.set(True)
    try:
        if event == 'open':
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
            for recorder in recorders:
                if writing:
                    recorder.valid = False
                else:
                    recorder.observe(path)
        elif event in ('os.listdir', 'os.scandir'):
            for recorder in recorders:
                recorder.observe(args[0], directory=True)
        elif event.startswith(('socket.', 'subprocess.')) or event in (
            'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.chmod',
            'os.link', 'os.symlink', 'os.truncate', 'os.utime'):
            for recorder in recorders:
                recorder.valid = False
    finally:
        _HM_BUSY.reset(busy)

from collections import OrderedDict as _hm_OrderedDict

class WindowHoldHistoryMemo:

    def __init__(self, *, enabled=True, max_entries=8, max_paths=4096, max_bytes=8 * 1024 * 1024):
        o.need(type(enabled) is bool and 0 < max_entries <= 16 and (0 < max_paths <= 8192) and (0 < max_bytes <= 32 * 1024 * 1024), 'history-memo-bounds')
        self.enabled = enabled
        (self.max_entries, self.max_paths, self.max_bytes) = (max_entries, max_paths, max_bytes)
        self.owner = _hm_identity()
        self.entries = _hm_OrderedDict()
        self.size = 0
        self.closed = False
        self.counts = {'compute': {}, 'hit': {}, 'invalidated': 0, 'untracked_or_unstable': 0}
        self.refused_snapshots = []
        self.counts.update(capacity_evictions=0,max_entries_seen=0,entries_count=0)

    def clear(self):
        self.entries.clear()
        self.size = 0
        self.counts['entries_count'] = 0

    def call(self, function, args, kwargs):
        o.need(not self.closed and self.owner == _hm_identity(), 'history-memo-owner-scope')
        name = function.__name__
        key = (name, function.__code__, json.dumps(_dedup_key_inputs(function, args, kwargs), sort_keys=True, ensure_ascii=False))
        if self.enabled and key in self.entries:
            (readset, result, size) = self.entries[key]
            busy = _HM_BUSY.set(True)
            try:
                unchanged = readset.unchanged()
            finally:
                _HM_BUSY.reset(busy)
            if unchanged:
                for outer in _HM_RECORDERS.get():
                    if outer.reader_context is _hm_authority_context():
                        for (query, resolved) in readset.reader_queries.items():
                            outer.reader_queries[query] = resolved
                    for (path, directory) in readset.paths:
                        outer.observe(path, directory=directory)
                self.entries.move_to_end(key)
                self.counts['hit'][name] = self.counts['hit'].get(name, 0) + 1
                return copy.deepcopy(result)
            stale = self.entries.pop(key)
            self.size -= stale[2]
            self.counts['entries_count'] = len(self.entries)
            self.counts['invalidated'] += 1
        self.counts['compute'][name] = self.counts['compute'].get(name, 0) + 1
        if not self.enabled:
            return function(*args, **kwargs)
        readset = _HistoryReadSet(self.max_paths)
        token = _HM_RECORDERS.set((*_HM_RECORDERS.get(), readset))
        try:
            result = function(*args, **kwargs)
        except BaseException:
            self.clear()
            raise
        finally:
            _HM_RECORDERS.reset(token)
        busy = _HM_BUSY.set(True)
        try:
            unchanged = readset.unchanged()
        finally:
            _HM_BUSY.reset(busy)
        if unchanged:
            size = len(json.dumps(result, ensure_ascii=False)) + len(key[2]) + len(repr(readset.paths)) + len(repr(readset.reader_queries))
            if size <= self.max_bytes:
                # Remove only an existing same key (normally absent after miss).
                previous = self.entries.pop(key, None)
                if previous is not None:
                    self.size -= previous[2]
                while self.entries and (len(self.entries) >= self.max_entries or self.size + size > self.max_bytes):
                    _, dropped = self.entries.popitem(last=False)
                    self.counts['capacity_evictions'] += 1
                    self.size -= dropped[2]
                self.entries[key] = (readset, copy.deepcopy(result), size)
                self.size += size
                self.counts['entries_count'] = len(self.entries)
                self.counts['max_entries_seen'] = max(self.counts['max_entries_seen'],len(self.entries))
        else:
            self.counts['untracked_or_unstable'] += 1
            if len(self.refused_snapshots) < 8:
                self.refused_snapshots.append((name, tuple(readset.failures)))
        return result


@_hm_contextlib.contextmanager
def window_hold_history_scope(*, enabled=True, **bounds):
    global _HM_AUDIT_INSTALLED
    o.need(_HM_SCOPE.get() is None, 'history-memo-nested-command-scope')
    if not _HM_AUDIT_INSTALLED:
        sys.addaudithook(_hm_audit)
        _HM_AUDIT_INSTALLED = True
    memo = WindowHoldHistoryMemo(enabled=enabled, **bounds)
    token = _HM_SCOPE.set(memo)
    try:
        yield memo
    finally:
        memo.clear()
        memo.closed = True
        _HM_SCOPE.reset(token)

def _hm_history(function):
    @_hm_functools.wraps(function)
    def wrapped(*args, **kwargs):
        memo = _HM_SCOPE.get()
        return function(*args, **kwargs) if memo is None else memo.call(function, args, kwargs)
    return wrapped

# Only these four functions derive historical facts. The original public
# verify_window_hold, legacy FILTER live validation, _window_hold_admission,
# current canonical engine/operator/focus/date-epoch reads remain untouched.
_window_hold_case = _hm_history(_window_hold_case)
_filter_proof_facts = _hm_history(_filter_proof_facts)
window_hold_source_codes = _hm_history(window_hold_source_codes)
verify_window_effect_envelope = _hm_history(verify_window_effect_envelope)

# Isolated append block. Requires the existing initial_ledger_recovery globals.
# No writers, UI ports, status setters, or automatic retry entry point.
REGION_TAIL_KIND='verified-window-hold-transparent-ancestor-preinput-failure-v1'
REGION_TAIL_ERROR_PREFIX='review-region-proof-failed:region-painted-external-overlap:'

def _region_tail_checked_facts(parent,engine,previous_parent,previous_engine,previous_ref,worker_ref,raw_reply_ref,preflight_ref,*,live=True,preflight_origin=None):
    """Private structural qualification AFTER full previous typed verification.

    previous_parent/engine are the exact previous recovery's shared transform,
    not caller status flags. The public composite verifier must supply them.
    This function never admits a failed/unknown input or classifies pixels.
    """
    folder=phase_directory(engine);order=o.validate(engine['order'])
    o.need(parent['order']==engine['order']==previous_parent['order']==previous_engine['order'],'region-tail-original-order')
    o.need(parent.get(WINDOW_HOLD_FIELD)==engine.get(WINDOW_HOLD_FIELD)==previous_ref,'region-tail-previous-common-marker')
    o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and engine['status']=='hold','region-tail-stopped')
    n=len(previous_engine['calls']);k=len(previous_parent['calls'])
    o.need(n>0 and k>0 and len(engine['calls'])==n+1 and len(parent['calls'])==k+1,'region-tail-one-appended-call-child')
    o.need(engine['calls'][:n]==previous_engine['calls']and parent['calls'][:k]==previous_parent['calls'],'region-tail-exact-prefix')
    for current,old in ((parent,previous_parent),(engine,previous_engine)):
        o.need({a:b for a,b in current.items()if a not in ('status','error','calls')}=={a:b for a,b in old.items()if a not in ('status','error','calls')},'region-tail-no-other-metadata-delta')
    failed=engine['calls'][-1];error=failed.get('error','')
    o.need(type(error)is str and engine.get('error')==error and (error.startswith(REGION_TAIL_ERROR_PREFIX)or error=='review-region-proof-failed:region-transparent-ancestor-limit'),'region-tail-known-readonly-proof-error')
    if error.startswith(REGION_TAIL_ERROR_PREFIX):
        diagnostic=json.loads(error[len(REGION_TAIL_ERROR_PREFIX):]);o.need(diagnostic.get('ancestor_opacity')==0 and type(diagnostic.get('ancestor_opacity'))in(int,float)and diagnostic.get('decoration_conditions',{}).get('ancestor_opacity_valid')is True,'region-tail-zero-ancestor-diagnostic')
    o.need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==engine['index']and engine['phase']=='collect','region-tail-resultless-collect')
    i=engine['index'];o.need(type(i)is int and 0<=i<len(order['companies']),'region-tail-company-index')
    expected={'order':order,'company':order['companies'][i],'artifacts':engine['companies'][i]['artifacts'],'folder':str(folder/'companies'/str(i)),'phase':'collect'}
    o.need(failed['context']==expected and not any(engine.get(x)for x in ('handoff','acceptance','delivery','completion')),'region-tail-exact-business-context')
    child=parent['calls'][-1];launch=o.doc(child['launch']);ex=o.doc(child['result'])
    argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(set(child)=={'state','argv','launch','result'}and child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(k).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(k).zfill(4)+'-exit.json')),'region-tail-canonical-child')
    o.need(child['argv']==launch['argv']==ex['argv']==argv and launch['index']==k and launch['order']==parent['order']and ex['launch']==child['launch']and ex['returncode']==2 and type(ex['returncode'])is int and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':error}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'region-tail-natural-exact-child')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response'])
    o.need(type(worker['returncode'])is int and worker['returncode']==0 and worker['attempt_id']==request['attempt_id']==response['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['task']['id']==response['task_id']and request['context']['order']==response['context']['order']==parent['order'],'region-tail-natural-worker')
    # Outer is read from the original immutable request, never reconstructed.
    previous=o.doc(previous_ref);origin=previous if previous['kind']==WINDOW_HOLD_KIND else previous['facts'];o.need(request['task']['outer']==origin['outer']and request['task']['id']==origin['task_id'],'region-tail-original-clock-task')
    raw=o.doc(raw_reply_ref);preflight=o.doc(preflight_ref)
    o.need(set(raw)=={'command','response','observed_at'}and raw['response'].get('ok')is False,'region-tail-original-readonly-failure')
    # Preserve the full failed reply and require its diagnostic, not a summary.
    o.need(raw['response'].get('error')==error.removeprefix('review-region-proof-failed:'),'region-tail-original-diagnostic-binding')
    import account_overlay_preflight as overlay
    artifacts=engine['companies'][i]['artifacts']['unit_artifacts'];review_key=artifacts['keys'][artifacts['frame_index']]
    manifest_ref={'path':str(Path(artifacts['source']['path']).parent/'frames'/o.digest(review_key)/'manifest.json'),'sha256':''}
    manifest_ref=o.ref(manifest_ref['path']);manifest=o.doc(manifest_ref)
    expected_manifest={key:artifacts[key]for key in ('job','source','envelope','profile','page')}
    expected_manifest.update(review_keys=[review_key],capture_key='complaint-parent:'+o.digest({'dispatch':order['dispatch_id'],'key':review_key,'source':artifacts['source']['sha256']})[:40])
    o.need(manifest==expected_manifest,'region-tail-original-manifest')
    base,source,scope,url=overlay.derive(manifest)
    binding={'source':manifest['source'],'job':manifest['job'],'profile':manifest['profile'],'envelope':manifest['envelope'],'identity':source['identity'],'scope':scope,'url':url,'content':overlay.content_identity()}
    key=overlay.rc.digest({'source_sha256':manifest['source']['sha256'],**scope,'identity':source['identity']})
    o.need((preflight_origin or preflight_ref)['path']==str(overlay.RUNTIME/(key+'.json'))and set(preflight)=={'kind','binding','created_at','state','attempts'}and preflight['kind']=='review-account-overlay-preflight-v1'and preflight['binding']==binding and preflight['state']=='preflight'and type(preflight['attempts'])is list and len(preflight['attempts'])>=1,'region-tail-original-no-input-preflight')
    if previous['kind']==REGION_TAIL_KIND:
        prior_preflight=o.doc(previous['preflight_archive']);o.need(preflight['binding']==prior_preflight['binding']and preflight['attempts'][:len(prior_preflight['attempts'])]==prior_preflight['attempts'],'region-tail-preserved-preflight-history')
    attempt=preflight['attempts'][-1];o.need(attempt['manifest']==manifest_ref and attempt['raw'][-1]==raw_reply_ref and attempt['error']['code']==error and raw_reply_ref['path']==str(overlay.RUNTIME/key/'attempts'/attempt['attempt']/'04-region-after.json'),'region-tail-original-raw-preflight-chain')
    o.need(raw['command']==overlay.region.region_command(base)and _window_time(failed['intent_at'])<=_window_time(attempt['at'])<=_window_time(raw['observed_at'])<=_window_time(worker['exited_at']),'region-tail-original-readonly-command-time')
    for past in preflight['attempts']:
        for r in past['raw']:
            read=o.doc(r);o.need(set(read)=={'command','response','observed_at'}and read['command'].get('op')in ('tabs','ping','tree','dom-region-proof'),'region-tail-only-readonly-preflight-history')
    import review_capture_focus as focus
    if live:focus.no_capture(manifest_ref)
    slot=folder/'receipts'/(str(n+1).zfill(5)+'.json')
    if live:o.need(not slot.exists()and not slot.is_symlink(),'region-tail-resultless-receipt-absent')
    return {'kind':REGION_TAIL_KIND,'previous_recovery':previous_ref,'failed_index':n,'failed_call':copy.deepcopy(failed),'child_index':k,'failed_child':copy.deepcopy(child),'error':error,'task_id':request['task']['id'],'attempt_id':request['attempt_id'],'outer':copy.deepcopy(request['task']['outer']),'worker_exit':worker_ref,'raw_reply':raw_reply_ref,'preflight':preflight_ref,'resultless_receipt':str(slot)}

def _region_tail_transform_checked(parent,engine,proof_ref,facts):
    """One deterministic transformation; qualification is mandatory upstream."""
    o.need(facts['kind']==REGION_TAIL_KIND and engine['calls'][facts['failed_index']]==facts['failed_call']and parent['calls'][facts['child_index']]==facts['failed_child'],'region-tail-transform-members')
    p,e=copy.deepcopy(parent),copy.deepcopy(engine)
    for v,error in ((p,'execution-child-stopped'),(e,facts['error'])):
        o.need(v['status']=='hold'and v.get('error')==error,'region-tail-transform-before')
        del v['error'];v['status']='running';v[WINDOW_HOLD_FIELD]=proof_ref
        v.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof_ref})
    e.setdefault('resolved_window_failures',[]).append({'index':facts['failed_index'],'call':copy.deepcopy(facts['failed_call']),'recovery':proof_ref})
    return p,e

# One finite reviewed deployment. The mapping is active only within a verified
# composite call; it reads old code as bytes, never imports archived code.
from contextvars import ContextVar as _RegionContextVar
_REGION_HISTORY_SOURCE=_RegionContextVar('region_tail_reviewed_source',default=None)
_REGION_PREVIOUS_SOURCE_CODES=window_hold_source_codes
_REGION_PREVIOUS_VERIFY=verify_window_hold
_REGION_PREVIOUS_RAW=_capture_focus_code_raw
REGION_SOURCE_KIND='supervisor-reviewed-transparent-ancestor-preinput-source-successor-v1'

_REGION_ROOT_STACK=_RegionContextVar('region_source_root_stack',default=())
def _region_source_root(reference):
    stack=_REGION_ROOT_STACK.get();o.need(len(stack)<16 and reference['sha256']not in stack,'region-source-bounded-acyclic-root')
    token=_REGION_ROOT_STACK.set((*stack,reference['sha256']))
    try:return _region_source_root_checked(reference)
    finally:_REGION_ROOT_STACK.reset(token)

def _region_source_root_checked(reference):
    root=o.doc(reference);keys={'kind','previous_source_release','published','test_projection_only','reviewed_by','targets','region_preinput_successor','binding','freeze','intent','published_at','review'}
    o.need(set(root)==keys and root['kind']==REGION_SOURCE_KIND and root['published']is True and root['test_projection_only']is False and root['reviewed_by']=='workshop-director','region-source-root-schema')
    paths={str(o.PROJECT/r)for r in ('skills/negative-review-complaints/scripts/initial_ledger_recovery.py','skills/negative-review-complaints/scripts/complaint_execution.py','skills/workshop-director/scripts/complaint_execution_launcher.py','skills/chrome-dom-export/extension/region-proof.js')}
    ts=root['targets'];o.need(type(ts)is list and 1<=len(ts)<=len(paths)and len({t['target']for t in ts})==len(ts)and {t['target']for t in ts}<=paths,'region-source-exact-four-paths')
    for t in ts:
        o.need(set(t)=={'target','mode','old_sha256','before','after'}and type(t['mode'])is int and t['mode']==420 and t['old_sha256']==t['before']['sha256']and t['before']['sha256']!=t['after']['sha256']and t['before']['path']==str(Path(reference['path']).parent/(Path(t['target']).name+'.before')),'region-source-exact-CAS-archive')
        o.raw(t['before']);o.raw(t['after'])
    a=root['region_preinput_successor'];ak={'previous_recovery','original_parent','original_engine','original_operator','worker_exit','raw_reply','preflight','order'}
    o.need(set(a)==ak and root['binding']==a and o.doc(a['previous_recovery'])['kind']in (WINDOW_HOLD_KIND,REGION_TAIL_KIND) and o.doc(a['previous_recovery'])['source_release']==root['previous_source_release'],'region-source-original-typed-predecessor')
    previous_source=o.doc(root['previous_source_release'])
    if previous_source.get('kind')==REGION_SOURCE_KIND:_region_source_root(root['previous_source_release'])
    else:_window_hold_source_root(root['previous_source_release'])
    frozen=o.doc(root['freeze']);o.need(set(frozen)=={'kind','execution_authorized','files'}and frozen['kind']=='transparent-ancestor-preinput-source-freeze-v1'and frozen['execution_authorized']is False and all(t['after']in frozen['files']for t in ts),'region-source-nonexecution-freeze')
    for r in frozen['files']:o.raw(r)
    review=o.doc(root['review']);o.need(review=={'kind':'root-reviewed-transparent-ancestor-preinput-source-v1','previous_source_release':root['previous_source_release'],'targets':ts,'binding':a,'freeze':root['freeze'],'verdict':'source-candidate-approved-not-runtime-metadata'},'region-source-exact-review')
    intent=o.doc(root['intent']);o.need(set(intent)=={'kind','previous_source_release','targets','freeze','review','binding','at'}and intent['kind']=='transparent-ancestor-preinput-source-publication-intent-v1'and all(intent[k]==root[k]for k in ('previous_source_release','targets','freeze','review','binding'))and _window_time(intent['at'])<=_window_time(root['published_at']),'region-source-exact-intent')
    return root,{t['target']:t for t in ts}

def _region_history_code_raw(reference):
    context=_REGION_HISTORY_SOURCE.get()
    if context:
        for t in context['archives']:
            if reference['path']==t['target']and reference['sha256']==t['old_sha256']:return o.raw(t['before'])
    return o.raw(reference)

def _capture_focus_code_raw(reference,source_successor=None):
    context=_REGION_HISTORY_SOURCE.get()
    if context:
        for t in context['archives']:
            if reference['path']==t['target']and reference['sha256']==t['old_sha256']:return o.raw(t['before'])
    return _REGION_PREVIOUS_RAW(reference,source_successor)

def window_hold_source_codes(parent,release_ref,*,installed=True):
    if o.doc(release_ref).get('kind')!=REGION_SOURCE_KIND:return _REGION_PREVIOUS_SOURCE_CODES(parent,release_ref,installed=installed)
    root,targets=_region_source_root(release_ref);token=_REGION_HISTORY_SOURCE.set(_region_source_context(release_ref))
    try:old=window_hold_source_codes(parent,root['previous_source_release'],installed=False)
    finally:_REGION_HISTORY_SOURCE.reset(token)
    o.need(len(old)==len({r['path']for r in old})==160,'region-source-baseline160')
    for path,t in targets.items():o.need(sum(r=={'path':path,'sha256':t['old_sha256']}for r in old)==1,'region-source-continuous-slot')
    codes=[{'path':r['path'],'sha256':targets[r['path']]['after']['sha256']}if r['path']in targets else r for r in old]
    o.need(sum(a!=b for a,b in zip(old,codes))==len(targets),'region-source-only-four-deltas')
    if installed:
        for r in codes:o.raw(r)
    return codes

def _region_previous_checked(parent,engine,proof_ref):
    """Full old facts on immutable/current-before pair, not a canonical swap."""
    p=o.doc(proof_ref)
    if p.get('kind')==REGION_TAIL_KIND:
        bp,be,prior=_region_proof_facts(p);codes=window_hold_source_codes(bp,p['source_release'],installed=False)
        return _region_admission_checked(parent,engine,proof_ref,p,bp,be,prior,codes)
    oldkeys={'kind','order','task_id','attempt_id','outer','original_parent','original_engine','original_operator','parent_archive','engine_archive','operator_archive','operator_job','worker_exit','previous_failed_children','focus_effect','effect_authority','source_release','source_codes','preinput_inventory','at'}
    o.need(set(p)==oldkeys and p['kind']==WINDOW_HOLD_KIND and _window_time(p['at']),'region-tail-one-native-predecessor')
    base=phase_directory(parent)/'.window-effect-hold-recovery'/p['original_parent']['sha256']
    o.need(proof_ref['path']==str(base/'proof.json')and all(p[n+'_archive']=={'path':str(base/(n+'-before.json')),'sha256':p['original_'+n]['sha256']}for n in ('parent','engine','operator')),'region-tail-previous-canonical-proof')
    archived_parent,archived_engine=_window_hold_case(p)
    root,ts=_window_hold_source_root(p['source_release'])
    o.need(root['window_effect_hold_successor']=={'original_parent':p['original_parent'],'original_engine':p['original_engine'],'original_operator':p['original_operator'],'worker_exit':p['worker_exit'],'original_focus':o.doc(p['focus_effect'])['original_focus'],'order':p['order'],'effect_authority':_window_root_effect_ref(p['effect_authority'])},'region-tail-old-root-authority')
    codes=_REGION_PREVIOUS_SOURCE_CODES(archived_parent,p['source_release'],installed=False)
    oldcodes=[{'path':r['path'],'sha256':ts[r['path']]['old_sha256']}if r['path']in ts else r for r in codes]
    effect=verify_window_effect_envelope(p['focus_effect'],expected_authority=p['effect_authority'],expected_sources=oldcodes,source_successor=p['source_release'])
    o.need(p['source_codes']==codes and _window_time(o.doc(o.doc(p['focus_effect'])['natural_exit'])['ended_at'])<=_window_time(p['at']),'region-tail-old-effect-codes-time')
    _DATE_LEGACY_FILTER_VERIFY(archived_parent,archived_parent[FILTER_READONLY_FIELD],installed=False,source_successor=p['source_release'])
    return _window_hold_admission(parent,engine,proof_ref,qualified_effect=effect,source_codes=codes)

def _region_live_inputs(p,*,archive_pending=False):
    import review_capture_focus as focus
    previous=o.doc(p['previous_recovery']);archived_operator=o.doc(p['original_operator']if archive_pending else p['operator_archive']);live_operator=o.doc(o.ref(p['original_operator']['path']))
    o.need(live_operator['calls'][:len(archived_operator['calls'])]==archived_operator['calls']and all(c['state']=='confirmed'for c in live_operator['calls'])and live_operator.get(DATE_RESTORE_FIELD)==archived_operator.get(DATE_RESTORE_FIELD),'region-tail-live-confirmed-operator')
    date_restore_epoch_verify(o.doc(p['operator_job']),live_operator)
    old_preflight=o.doc(p['preflight']if archive_pending else p['preflight_archive']);current_preflight=o.doc(o.ref(p['preflight']['path']))
    o.need(current_preflight.get('kind')==old_preflight['kind']and current_preflight.get('binding')==old_preflight['binding']and current_preflight.get('attempts',[])[:len(old_preflight['attempts'])]==old_preflight['attempts'],'region-tail-live-preflight-prefix')
    native=_region_native_predecessor(p['previous_recovery']);effect=o.doc(native['focus_effect']);saved=o.doc(effect['after_archive']);live=o.doc(o.ref(effect['after_focus']['path']))
    focus.validate_events(live,saved['binding']);o.need(live['binding']==saved['binding']and live['events'][:1]==saved['events']and live['reads'][:len(saved['reads'])]==saved['reads'],'region-tail-live-completed-native-prefix')
    if archive_pending:
        for event in live['events'][len(saved['events']):]:o.need(event['state']=='complete'and all(c['state']=='confirmed'for c in event['calls']),'region-tail-plan-no-new-native-or-unknown-intent')

REGION_PROOF_KEYS={'kind','previous_recovery','order','original_parent','original_engine','original_operator','parent_archive','engine_archive','operator_archive','operator_job','worker_exit','raw_reply','preflight','preflight_archive','source_release','source_codes','facts','at'}
def _region_proof_facts(p):
    o.need(set(p)==REGION_PROOF_KEYS and p['kind']==REGION_TAIL_KIND and _window_time(p['at']),'region-tail-proof-schema')
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);previous=o.doc(p['previous_recovery']);root,targets=_region_source_root(p['source_release'])
    o.need(root['region_preinput_successor']=={k:p[k]for k in ('previous_recovery','original_parent','original_engine','original_operator','worker_exit','raw_reply','preflight','order')}and p['order']==parent['order']==engine['order'],'region-tail-proof-source-authority')
    folder=phase_directory(parent);base=folder/'.region-preinput-hold-recovery'/p['original_parent']['sha256']
    for name in ('parent','engine','operator'):
        o.need(p[name+'_archive']=={'path':str(base/(name+'-before.json')),'sha256':p['original_'+name]['sha256']},'region-tail-canonical-before-archive')
    o.need(p['preflight_archive']=={'path':str(base/'preflight-before.json'),'sha256':p['preflight']['sha256']},'region-tail-canonical-preflight-archive')
    o.need(p['original_parent']['path']==str(folder/'launcher.json')and p['original_engine']['path']==str(folder/'engine.json')and p['original_operator']=={'path':previous['original_operator']['path'],'sha256':p['operator_archive']['sha256']}and p['operator_job']==previous['operator_job'],'region-tail-canonical-originals')
    token=_REGION_HISTORY_SOURCE.set(_region_source_context(p['source_release']))
    try:
        admitted=_region_previous_checked(parent,engine,p['previous_recovery'])
        pp,ee=window_hold_shared_transform(o.doc(previous['parent_archive']),o.doc(previous['engine_archive']),p['previous_recovery'])
        facts=_region_tail_checked_facts(parent,engine,pp,ee,p['previous_recovery'],p['worker_exit'],p['raw_reply'],p['preflight_archive'],live=False,preflight_origin=p['preflight'])
        o.need(facts==p['facts'],'region-tail-facts-recomputed')
    finally:_REGION_HISTORY_SOURCE.reset(token)
    return parent,engine,admitted

def verify_window_hold(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref)
    if p.get('kind')!=REGION_TAIL_KIND:return _REGION_PREVIOUS_VERIFY(current,proof_ref,installed=installed)
    parent,engine,previous=_region_proof_facts(p);folder=phase_directory(parent)
    root,targets=_region_source_root(p['source_release']);token=_REGION_HISTORY_SOURCE.set(_region_source_context(p['source_release']))
    try:_region_live_inputs(p)
    finally:_REGION_HISTORY_SOURCE.reset(token)
    for index in [*previous['failed_engine_indices'],p['facts']['failed_index']]:
        slot=folder/'receipts'/(str(index+1).zfill(5)+'.json');o.need(not slot.exists()and not slot.is_symlink(),'region-tail-current-resultless-receipt-absent')
    o.need(proof_ref['path']==str(folder/'.region-preinput-hold-recovery'/p['original_parent']['sha256']/'proof.json'),'region-tail-canonical-proof')
    codes=window_hold_source_codes(parent,p['source_release'],installed=installed);o.need(p['source_codes']==codes,'region-tail-current-codes')
    actual_engine=o.doc(o.ref(folder/'engine.json'))
    return _region_admission_checked(current,actual_engine,proof_ref,p,parent,engine,previous,codes)

def _region_admission_checked(current,actual_engine,proof_ref,p,parent,engine,previous,codes):
    ep,ee=_region_tail_transform_checked(parent,engine,proof_ref,p['facts'])
    for value,expected,old in ((current,ep,parent),(actual_engine,ee,engine)):
        variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
        if value is actual_engine:variable|={'phase','index','companies','business_journals','delivery','handoff','waiting_for','acceptance'}
        for key in set(expected)-variable:o.need(value.get(key)==expected[key],'region-tail-preserved-current-metadata')
        o.need(value['calls'][:len(old['calls'])]==old['calls'],'region-tail-preserved-current-calls')
    o.need(current.get(WINDOW_HOLD_FIELD)==actual_engine.get(WINDOW_HOLD_FIELD)==proof_ref and actual_engine['resolved_window_failures']==ee['resolved_window_failures'],'region-tail-common-current-proof')
    failed=[*previous['failed_calls'],p['facts']['failed_child']];o.need(all(sum(c==f for c in current['calls'])==1 for f in failed),'region-tail-exact-failed-children')
    return {'kind':REGION_TAIL_KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':failed,'failed_engine_indices':[*previous['failed_engine_indices'],p['facts']['failed_index']],'evidence':[proof_ref,p['previous_recovery'],p['parent_archive'],p['engine_archive'],p['operator_archive'],p['preflight_archive'],p['worker_exit'],p['raw_reply'],*previous['evidence']]}

def plan_region_preinput_hold(parent_ref,engine_ref,operator_ref,worker_ref,raw_reply_ref,preflight_ref,source_release):
    """Read-only plan; no archives/intent/metadata are written or authorized."""
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);previous_ref=parent.get(WINDOW_HOLD_FIELD);previous=o.doc(previous_ref);root,targets=_region_source_root(source_release)
    binding={'previous_recovery':previous_ref,'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker_exit':worker_ref,'raw_reply':raw_reply_ref,'preflight':preflight_ref,'order':parent['order']}
    o.need(root['region_preinput_successor']==binding,'region-tail-plan-source-authority')
    codes=window_hold_source_codes(parent,source_release);token=_REGION_HISTORY_SOURCE.set(_region_source_context(source_release))
    try:
        _region_previous_checked(parent,engine,previous_ref)
        pp,ee=window_hold_shared_transform(o.doc(previous['parent_archive']),o.doc(previous['engine_archive']),previous_ref)
        facts=_region_tail_checked_facts(parent,engine,pp,ee,previous_ref,worker_ref,raw_reply_ref,preflight_ref)
        op=o.doc(operator_ref);o.need(operator_ref['path']==previous['original_operator']['path']and op['calls']==o.doc(previous['operator_archive'])['calls'],'region-tail-plan-no-new-business-input')
    finally:_REGION_HISTORY_SOURCE.reset(token)
    base=phase_directory(parent)/'.region-preinput-hold-recovery'/parent_ref['sha256'];arch=lambda name,r:{'path':str(base/(name+'-before.json')),'sha256':r['sha256']}
    pa=arch('preflight',preflight_ref);facts['preflight']=pa
    p={'kind':REGION_TAIL_KIND,**binding,'parent_archive':arch('parent',parent_ref),'engine_archive':arch('engine',engine_ref),'operator_archive':arch('operator',operator_ref),'operator_job':previous['operator_job'],'preflight_archive':pa,'source_release':source_release,'source_codes':codes,'facts':facts,'at':datetime.now(timezone.utc).isoformat()}
    token=_REGION_HISTORY_SOURCE.set(_region_source_context(source_release))
    try:_region_live_inputs(p,archive_pending=True)
    finally:_REGION_HISTORY_SOURCE.reset(token)
    return p

_REGION_PREVIOUS_TRANSFORM=window_hold_shared_transform
def window_hold_shared_transform(parent,engine,proof_ref):
    p=o.doc(proof_ref)
    if p.get('kind')!=REGION_TAIL_KIND:return _REGION_PREVIOUS_TRANSFORM(parent,engine,proof_ref)
    o.need(parent==o.doc(p['parent_archive'])and engine==o.doc(p['engine_archive']),'region-tail-transform-exact-archives')
    return _region_tail_transform_checked(parent,engine,proof_ref,p['facts'])

def _region_native_predecessor(reference):
    seen=set()
    for _ in range(16):
        o.need(reference['sha256']not in seen,'region-tail-proof-cycle');seen.add(reference['sha256']);p=o.doc(reference)
        if p.get('kind')==WINDOW_HOLD_KIND:return p
        o.need(p.get('kind')==REGION_TAIL_KIND,'region-tail-unknown-proof-kind');reference=p['previous_recovery']
    o.need(False,'region-tail-proof-history-bound')

def _region_source_context(reference):
    tip=reference;archives=[];seen=set()
    for _ in range(16):
        o.need(reference['sha256']not in seen,'region-source-cycle');seen.add(reference['sha256']);p=o.doc(reference)
        if p.get('kind')!=REGION_SOURCE_KIND:
            _window_hold_source_root(reference);return {'source_release':tip,'archives':archives}
        root,targets=_region_source_root(reference);archives.extend(targets.values());reference=root['previous_source_release']
    o.need(False,'region-source-history-bound')

# The existing command scope now also includes this immutable successor tip.
# Current pair/operator/focus/preflight prefixes and receipt absence stay outside.
_region_source_root=_hm_history(_region_source_root)
_region_proof_facts=_hm_history(_region_proof_facts)
window_hold_source_codes=_hm_history(window_hold_source_codes)

# Narrow source-ancestry memo key policies. No current-state validation moves.
def _dedup_key_inputs(function, args, kwargs):
    name = function.__name__
    if name == 'window_hold_source_codes':
        parent, release = args[:2]
        # This function only derives source refs: its legacy branch overwrites
        # DATE_SOURCE_FIELD with the pinned native baseline, removes the hold
        # marker, and uses only order + FILTER proof from the supplied parent.
        # Public parent/engine admission checks remain outside this memo.
        binding = {'order': parent['order'],
                   FILTER_READONLY_FIELD: parent[FILTER_READONLY_FIELD]}
        return ((binding, release, *args[2:]), kwargs, 'observed-reader-semantics-v1')
    if name in ('_region_source_root_checked', '_region_proof_facts',
                '_region_source_context','_source_epoch_root','_source_epoch_overlay','_source_epoch_proof','_company_scope_proof_facts'):
        # Exact source/proof ref + file frontier is the authority input.
        # Only actually consumed archive-reader queries bind ambient context.
        return (args, kwargs, 'observed-reader-semantics-v1')
    return args, kwargs, _hm_authority_context()

def _dedup_reader_resolution(path, sha):
    context = _REGION_HISTORY_SOURCE.get()
    if context:
        for target in context['archives']:
            if path == target['target'] and sha == target['old_sha256']:
                before = target['before']
                return before['path'], before['sha256']
    return None

def _dedup_note_reader(reference):
    query = reference['path'], reference['sha256']
    resolved = _dedup_reader_resolution(*query)
    for recorder in _HM_RECORDERS.get():
        if recorder.reader_context is not _hm_authority_context():
            continue
        if query in recorder.reader_queries and recorder.reader_queries[query] != resolved:
            recorder.valid = False
        recorder.reader_queries[query] = resolved

_DEDUP_REGION_READER = _region_history_code_raw
def _region_history_code_raw(reference):
    _dedup_note_reader(reference)
    return _DEDUP_REGION_READER(reference)

_DEDUP_CAPTURE_READER = _capture_focus_code_raw
def _capture_focus_code_raw(reference, source_successor=None):
    _dedup_note_reader(reference)
    return _DEDUP_CAPTURE_READER(reference, source_successor)

# Check cycle/depth every time, including cached recursive subroots. Only the
# context-independent signed root computation is memoized, never this guard.
def _dedup_source_lineage(reference):
    seen = []
    for _ in range(16):
        o.need(reference['sha256'] not in seen, 'region-source-cycle')
        root = o.doc(reference)
        if root.get('kind') != REGION_SOURCE_KIND:
            return tuple(seen)
        seen.append(reference['sha256'])
        reference = root['previous_source_release']
    o.need(o.doc(reference).get('kind') != REGION_SOURCE_KIND,
           'region-source-history-bound')
    return tuple(seen)

_region_source_root_checked = _hm_history(_region_source_root_checked)
def _region_source_root(reference):
    stack = _REGION_ROOT_STACK.get()
    lineage = _dedup_source_lineage(reference)
    o.need(len(stack) + len(lineage) <= 16 and
           not set(stack).intersection(lineage), 'region-source-bounded-acyclic-root')
    token = _REGION_ROOT_STACK.set((*stack, reference['sha256']))
    try:
        return _region_source_root_checked(reference)
    finally:
        _REGION_ROOT_STACK.reset(token)

# Do not count/cache a no-op new-generation dispatcher around the legacy
# native graph. R0 goes straight to its one legacy computation entry.
_DEDUP_REGION_CODES = window_hold_source_codes
def window_hold_source_codes(parent, release_ref, *, installed=True):
    root = o.doc(release_ref)
    if root.get('kind') != REGION_SOURCE_KIND:
        return _REGION_PREVIOUS_SOURCE_CODES(parent, release_ref, installed=installed)
    return _DEDUP_REGION_CODES(parent, release_ref, installed=installed)

_region_source_context = _hm_history(_region_source_context)

# Source versions are independent of business success/failure admission.
SOURCE_EPOCH_FIELD='role_source_epoch'
SOURCE_EPOCH_KIND='role-execution-source-only-epoch-v1'
SOURCE_EPOCH_RELEASE_KIND='supervisor-reviewed-role-source-epoch-v1'
_SOURCE_EPOCH_ARCHIVES=_RegionContextVar('role_source_epoch_archives',default=())
_SOURCE_EPOCH_INSIDE=_RegionContextVar('role_source_epoch_inside',default=False)
_SOURCE_EPOCH_BUSINESS_VERIFY=verify_window_hold
_SOURCE_EPOCH_REGION_CONTEXT=_region_source_context

def _source_epoch_root(reference):
    root=o.doc(reference)
    keys={'kind','previous_source_release','published','test_projection_only','reviewed_by','targets','source_epoch','binding','freeze','intent','published_at','review'}
    o.need(set(root)==keys and root['kind']==SOURCE_EPOCH_RELEASE_KIND and root['published']is True and root['test_projection_only']is False and root['reviewed_by']=='workshop-director','source-epoch-release-schema')
    b=root['binding'];o.need(b==root['source_epoch']and set(b)=={'parent','engine','order','business_proof','previous_epoch'},'source-epoch-binding')
    ts=root['targets'];o.need(type(ts)is list and 1<=len(ts)<=16 and len({t['target']for t in ts})==len(ts),'source-epoch-finite-targets')
    allowed={str(o.PROJECT/r)for r in ('skills/negative-review-complaints/scripts/initial_ledger_recovery.py','skills/negative-review-complaints/scripts/complaint_execution.py','skills/negative-review-complaints/scripts/complaint_execution_ports.py','skills/workshop-director/scripts/complaint_execution_launcher.py','skills/workshop-director/scripts/complaint_execution_orchestration.py','skills/workshop-director/scripts/execution_timing.py','skills/workshop-director/scripts/complaint_execution_order.py','skills/workshop-director/scripts/coordinator.py','skills/workshop-director/scripts/daily_dispatch_order.py','skills/workshop-director/scripts/role_execution_order.py','skills/workshop-director/scripts/director.py','skills/workshop-director/scripts/daily_execution_launcher.py')}
    for t in ts:
        o.need(set(t)=={'target','before','after','old_sha256','mode'}and t['target']in allowed and type(t['mode'])is int and t['mode']==(384 if t['target']==str(o.PROJECT/'skills/workshop-director/scripts/daily_execution_launcher.py')else 420) and t['old_sha256']==t['before']['sha256']and t['after']['sha256']!=t['old_sha256']and t['before']['path']==str(Path(reference['path']).parent/(Path(t['target']).name+'.before')),'source-epoch-exact-reviewed-target')
        o.raw(t['before']);o.raw(t['after'])
    frozen=o.doc(root['freeze']);o.need(set(frozen)=={'kind','execution_authorized','files'}and frozen['kind']=='role-source-epoch-source-freeze-v1'and frozen['execution_authorized']is False and all(t['after']in frozen['files']for t in ts),'source-epoch-source-freeze')
    for r in frozen['files']:o.raw(r)
    review=o.doc(root['review']);o.need(review=={'kind':'root-reviewed-role-source-epoch-v1','previous_source_release':root['previous_source_release'],'targets':ts,'binding':b,'freeze':root['freeze'],'verdict':'source-candidate-approved-not-runtime-metadata'},'source-epoch-exact-review')
    intent=o.doc(root['intent']);o.need(set(intent)=={'kind','previous_source_release','targets','freeze','review','binding','at'}and intent['kind']=='role-source-epoch-publication-intent-v1'and all(intent[k]==root[k]for k in ('previous_source_release','targets','freeze','review','binding'))and _window_time(intent['at'])<=_window_time(root['published_at']),'source-epoch-exact-publication-intent')
    return root

def _region_source_context(reference):
    # Always merge outside the old memo: nesting must not discard epoch CODE archives.
    ctx=copy.deepcopy(_SOURCE_EPOCH_REGION_CONTEXT(reference))
    ctx['archives']=[*copy.deepcopy(_SOURCE_EPOCH_ARCHIVES.get()),*ctx['archives']]
    return ctx

def _source_epoch_overlay(codes,root,*,installed):
    ts={t['target']:t for t in root['targets']};o.need(len(codes)==len({r['path']for r in codes})==160,'source-epoch-exact160');paths={r['path']for r in codes}
    external={str(o.PROJECT/'skills/workshop-director/scripts'/n)for n in ('coordinator.py','daily_dispatch_order.py','role_execution_order.py','director.py','daily_execution_launcher.py')}
    o.need(set(ts)-paths<=external,'source-epoch-only-explicit-fresh-external-targets')
    graph={path:t for path,t in ts.items()if path in paths}
    for path,t in graph.items():o.need(sum(r=={'path':path,'sha256':t['old_sha256']}for r in codes)==1,'source-epoch-continuous-slot')
    result=[{'path':r['path'],'sha256':graph[r['path']]['after']['sha256']}if r['path']in graph else copy.deepcopy(r)for r in codes]
    o.need(sum(a!=b for a,b in zip(codes,result))==len(graph),'source-epoch-no-other-slot-change')
    if installed:
        for r in result:_completed_source_code_raw(r)
        for path,t in ts.items():
            _completed_source_code_raw({'path':path,'sha256':t['after']['sha256']});o.need(Path(path).stat().st_mode&0o777==t['mode'],'source-epoch-installed-mode')
    return result

_SOURCE_EPOCH_PURE_OVERLAY=_source_epoch_overlay
_SOURCE_EPOCH_INSTALLED_OVERLAY=_hm_history(_source_epoch_overlay)
def _source_epoch_overlay(codes,root,*,installed):
    return _SOURCE_EPOCH_INSTALLED_OVERLAY(codes,root,installed=True)if installed else _SOURCE_EPOCH_PURE_OVERLAY(codes,root,installed=False)

def source_epoch_shared_transform(parent,engine,epoch_ref):
    p=o.doc(epoch_ref);previous=p['previous_epoch']
    o.need(parent==o.doc(p['parent_archive'])and engine==o.doc(p['engine_archive'])and parent['order']==engine['order']==p['order']and parent.get(SOURCE_EPOCH_FIELD)==engine.get(SOURCE_EPOCH_FIELD)==previous,'source-epoch-transform-exact-before')
    pp,ee=copy.deepcopy(parent),copy.deepcopy(engine)
    pp[SOURCE_EPOCH_FIELD]=copy.deepcopy(epoch_ref);ee[SOURCE_EPOCH_FIELD]=copy.deepcopy(epoch_ref)
    if p.get('preinput_failure_admission'):
        facts=_epoch_preinput_archived_facts(p);o.need(facts==p['preinput_failure_admission'],'source-epoch-preinput-transform-facts')
        pp['status']=ee['status']='running';pp.pop('error',None);ee.pop('error',None)
    return pp,ee

def _source_epoch_proof(reference):
    p=o.doc(reference)
    keys={'kind','order','original_parent','original_engine','parent_archive','engine_archive','business_proof','previous_epoch','source_release','previous_source_release','old_code_refs','effective_code_refs','at'}
    o.need(set(p)in (keys,keys|{'preinput_failure_admission'}) and p['kind']==SOURCE_EPOCH_KIND and _window_time(p['at']),'source-epoch-proof-schema')
    if 'preinput_failure_admission'in p:o.need(p['preinput_failure_admission']==_epoch_preinput_archived_facts(p),'source-epoch-preinput-proof-facts')
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);folder=phase_directory(parent);base=folder/'.source-epochs'/p['original_parent']['sha256']
    o.need(reference['path']==str(base/'proof.json')and p['original_parent']['path']==str(folder/'launcher.json')and p['original_engine']['path']==str(folder/'engine.json')and all(p[n+'_archive']=={'path':str(base/(n+'-before.json')),'sha256':p['original_'+n]['sha256']}for n in ('parent','engine')),'source-epoch-canonical-archives')
    root=_source_epoch_root(p['source_release']);binding={'parent':p['original_parent'],'engine':p['original_engine'],'order':p['order'],'business_proof':p['business_proof'],'previous_epoch':p['previous_epoch']}
    o.need(root['binding']==binding and p['previous_source_release']==root['previous_source_release']and parent['order']==engine['order']==p['order']and parent.get(WINDOW_HOLD_FIELD)==engine.get(WINDOW_HOLD_FIELD)==p['business_proof']and parent.get(SOURCE_EPOCH_FIELD)==engine.get(SOURCE_EPOCH_FIELD)==p['previous_epoch'],'source-epoch-original-common-binding')
    # Old typed proof remains byte-bound; no failure/admission field is fabricated.
    prior_release=o.doc(p['previous_epoch'])['source_release']if p['previous_epoch']else o.doc(p['business_proof'])['source_release']
    o.need(prior_release==p['previous_source_release'],'source-epoch-previous-release-continuity')
    o.need(_source_epoch_overlay(p['old_code_refs'],root,installed=False)==p['effective_code_refs'],'source-epoch-derived-effective160')
    return p,parent,engine,root

_SOURCE_EPOCH_STACK=_RegionContextVar('role_source_epoch_stack',default=())
def _source_epoch_live_snapshot(current,engine,p,bp,be):
    # Source-only epochs cannot discard any newer business history at adoption.
    for value,before in ((current,bp),(engine,be)):
        variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass',SOURCE_EPOCH_FIELD}
        if value is engine:variable|={'phase','index','companies','business_journals','delivery','handoff','waiting_for','acceptance'}
        for key in set(before)-variable:o.need(value.get(key)==before[key],'source-epoch-preserved-snapshot-metadata')
        o.need(value['calls'][:len(before['calls'])]==before['calls'],'source-epoch-preserved-all-snapshot-calls')
    o.need(current.get(WINDOW_HOLD_FIELD)==engine.get(WINDOW_HOLD_FIELD)==p['business_proof'],'source-epoch-preserved-business-proof')

def _source_epoch_admission(current,epoch_ref,*,installed):
    stack=_SOURCE_EPOCH_STACK.get();o.need(epoch_ref not in stack and len(stack)<16,'source-epoch-acyclic-bounded-chain')
    st=_SOURCE_EPOCH_STACK.set((*stack,epoch_ref))
    try:
        p,bp,be,root=_source_epoch_proof(epoch_ref)
        _source_epoch_live_snapshot(current,o.doc(o.ref(phase_directory(current)/'engine.json')),p,bp,be)
        token=_SOURCE_EPOCH_ARCHIVES.set((*_SOURCE_EPOCH_ARCHIVES.get(),*root['targets']));inside=_SOURCE_EPOCH_INSIDE.set(True)
        try:
            if p['previous_epoch']:admission=_source_epoch_admission(current,p['previous_epoch'],installed=False)
            else:
                ctx=_REGION_HISTORY_SOURCE.set(_region_source_context(p['previous_source_release']))
                try:admission=_SOURCE_EPOCH_BUSINESS_VERIFY(current,p['business_proof'],installed=False)
                finally:_REGION_HISTORY_SOURCE.reset(ctx)
            o.need(admission['code_refs']==p['old_code_refs'],'source-epoch-business-old-graph')
        finally:_SOURCE_EPOCH_INSIDE.reset(inside);_SOURCE_EPOCH_ARCHIVES.reset(token)
        codes=_source_epoch_overlay(admission['code_refs'],root,installed=installed)
        if p.get('preinput_failure_admission'):
            f=p['preinput_failure_admission'];_epoch_preinput_live_guard(current,o.doc(o.ref(phase_directory(current)/'engine.json')),p)
            o.need(f['failed_engine_index']not in admission['failed_engine_indices']and f['failed_child']not in admission['failed_calls'],'source-epoch-preinput-distinct-failure')
            admission={**admission,'failed_engine_indices':[*admission['failed_engine_indices'],f['failed_engine_index']],'failed_calls':[*admission['failed_calls'],f['failed_child']],'evidence':[*admission['evidence'],*f['evidence']]}
        return {**admission,'code_refs':codes,'evidence':[*admission['evidence'],epoch_ref,p['source_release'],p['parent_archive'],p['engine_archive']]}
    finally:_SOURCE_EPOCH_STACK.reset(st)

def verify_source_epoch(current,epoch_ref,*,installed=True):
    engine=o.doc(o.ref(phase_directory(current)/'engine.json'));p=o.doc(epoch_ref)
    o.need(current.get(SOURCE_EPOCH_FIELD)==engine.get(SOURCE_EPOCH_FIELD)==epoch_ref and current['order']==engine['order']==p['order'],'source-epoch-current-common-pointer')
    return _source_epoch_admission(current,epoch_ref,installed=installed)

def verify_window_hold(current,proof_ref,*,installed=True):
    if current.get(SOURCE_EPOCH_FIELD)and not _SOURCE_EPOCH_INSIDE.get():
        o.need(current.get(WINDOW_HOLD_FIELD)==proof_ref,'source-epoch-original-business-marker');return verify_source_epoch(current,current[SOURCE_EPOCH_FIELD],installed=installed)
    return _SOURCE_EPOCH_BUSINESS_VERIFY(current,proof_ref,installed=installed)

# Only immutable root/proof facts are memo candidates; live verifier above never is.
_source_epoch_root=_hm_history(_source_epoch_root)

def plan_source_epoch(parent_ref,engine_ref,release_ref,*,installed=True,preinput_worker_ref=None):
    """Pure graph plan. Caller separately proves stopped workers/original owner under outer locks."""
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=phase_directory(parent);root=_source_epoch_root(release_ref)
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['order']==engine['order']and not parent.get('completion')and all(c['state']=='returned'for c in parent['calls']),'source-epoch-quiescent-parent')
    if parent.get('child'):
        matching=[c for c in parent['calls']if o.doc(c['result'])['returncode']==0 and json.loads(o.doc(c['result'])['stdout'])==parent['child']]
        o.need(len(matching)==1,'source-epoch-cached-natural-child-result')
    previous=parent.get(SOURCE_EPOCH_FIELD);binding={'parent':parent_ref,'engine':engine_ref,'order':parent['order'],'business_proof':parent[WINDOW_HOLD_FIELD],'previous_epoch':previous}
    o.need(engine.get(SOURCE_EPOCH_FIELD)==previous and root['binding']==binding,'source-epoch-plan-original-binding')
    token=_SOURCE_EPOCH_ARCHIVES.set(tuple(root['targets']));inside=_SOURCE_EPOCH_INSIDE.set(True)
    try:
        if previous:old=_source_epoch_admission(parent,previous,installed=False)
        else:
            ctx=_REGION_HISTORY_SOURCE.set(_region_source_context(root['previous_source_release']))
            try:old=_SOURCE_EPOCH_BUSINESS_VERIFY(parent,parent[WINDOW_HOLD_FIELD],installed=False)
            finally:_REGION_HISTORY_SOURCE.reset(ctx)
    finally:_SOURCE_EPOCH_INSIDE.reset(inside);_SOURCE_EPOCH_ARCHIVES.reset(token)
    prior_release=o.doc(previous)['source_release']if previous else o.doc(parent[WINDOW_HOLD_FIELD])['source_release']
    o.need(root['previous_source_release']==prior_release,'source-epoch-plan-release-continuity')
    codes=_source_epoch_overlay(old['code_refs'],root,installed=installed);base=folder/'.source-epochs'/parent_ref['sha256']
    plan={'kind':SOURCE_EPOCH_KIND,'order':parent['order'],'original_parent':parent_ref,'original_engine':engine_ref,'parent_archive':{'path':str(base/'parent-before.json'),'sha256':parent_ref['sha256']},'engine_archive':{'path':str(base/'engine-before.json'),'sha256':engine_ref['sha256']},'business_proof':parent[WINDOW_HOLD_FIELD],'previous_epoch':previous,'source_release':release_ref,'previous_source_release':prior_release,'old_code_refs':old['code_refs'],'effective_code_refs':codes,'at':datetime.now(timezone.utc).isoformat()}
    if preinput_worker_ref is not None:plan['preinput_failure_admission']=_epoch_preinput_failure_facts(parent_ref,engine_ref,preinput_worker_ref)
    return plan

def source_epoch_pair_state(parent,engine,before_parent,before_engine,epoch_ref):
    pp,ee=source_epoch_shared_transform(before_parent,before_engine,epoch_ref)
    if parent==before_parent and engine==before_engine:return 'before'
    if parent==before_parent and engine==ee:return 'engine-written'
    if parent==pp and engine==ee:return 'complete'
    raise ValueError('source-epoch-pair-CAS-conflict')

def adopt_source_epoch(parent_ref,engine_ref,release_ref,*,checkpoint=lambda stage:None,preinput_worker_ref=None):
    """Metadata-only. No CLI exposure; outer resource/scheduler/coordinator locks and
    explicit quiescent authorization/liveness guard are mandatory caller duties.
    Writes only same immutable epoch proof/archives and engine->parent pointer CAS.
    """
    folder=Path(parent_ref['path']).parent;base=folder/'.source-epochs'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as pl,(folder/'engine.lock').open('a')as el:
        for lock in (pl,el):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof)
            o.need((p['original_parent'],p['original_engine'],p['source_release'])==(parent_ref,engine_ref,release_ref),'source-epoch-same-proof-authority')
            o.need(o.doc(o.ref(base/'intent.json'))=={'kind':SOURCE_EPOCH_KIND,'parent':parent_ref,'engine':engine_ref,'release':release_ref},'source-epoch-existing-intent-authority')
            _source_epoch_proof(proof);o.need((p.get('preinput_failure_admission')or{}).get('worker')==preinput_worker_ref,'source-epoch-same-preinput-worker');bp,be=o.doc(p['parent_archive']),o.doc(p['engine_archive'])
        else:
            o.need(not(base/'result.json').exists()and not(base/'result.json').is_symlink(),'source-epoch-terminal-without-proof')
            p=plan_source_epoch(parent_ref,engine_ref,release_ref,preinput_worker_ref=preinput_worker_ref);bp,be=o.doc(parent_ref),o.doc(engine_ref)
            for name,r in (('parent',parent_ref),('engine',engine_ref)):o.need(immutable_bytes(base/(name+'-before.json'),o.raw(r))==p[name+'_archive'],'source-epoch-exact-archive')
            checkpoint('archives');o.immutable(base/'intent.json',{'kind':SOURCE_EPOCH_KIND,'parent':parent_ref,'engine':engine_ref,'release':release_ref});checkpoint('intent')
            proof=o.immutable(base/'proof.json',p);checkpoint('proof')
        pp,ee=source_epoch_shared_transform(bp,be,proof)
        current=lambda:(o.doc(o.ref(parent_ref['path'])),o.doc(o.ref(engine_ref['path'])))
        state=source_epoch_pair_state(*current(),bp,be,proof)
        if (base/'result.json').exists()or(base/'result.json').is_symlink():
            o.need(not(base/'result.json').is_symlink()and state=='complete','source-epoch-terminal-before-complete')
            result=o.ref(base/'result.json');o.need(o.doc(result)=={'kind':SOURCE_EPOCH_KIND,'proof':proof,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'source_release':release_ref,'ui_used':False,'retry_issued':False},'source-epoch-existing-result-authority');return result
        _source_epoch_admission(current()[0],proof,installed=True)
        import complaint_execution_launcher as launch
        if current()[1]==be:launch.save(Path(engine_ref['path']),ee)
        checkpoint('engine');source_epoch_pair_state(*current(),bp,be,proof)
        if current()[0]==bp:launch.save(Path(parent_ref['path']),pp)
        checkpoint('parent');verify_source_epoch(current()[0],proof)
        result=o.immutable(base/'result.json',{'kind':SOURCE_EPOCH_KIND,'proof':proof,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'source_release':release_ref,'ui_used':False,'retry_issued':False})
        checkpoint('result');return result

# Pure failure-member qualification for the existing helper owner to integrate.
# No source epoch adoption, failed-index mutation or metadata writer is implied.
def _retired_company_failure_facts(parent_ref,engine_ref,worker_ref,operation_ref,form_ref,*,_read=None):
    import draft_inspection as draft
    read=_read or o.doc
    parent=read(parent_ref);engine=read(engine_ref);order=o.validate(parent['order']);folder=o.location(parent['order']);operation=read(operation_ref)
    need=o.need;error='draft-inspection-options-changed-or-selected'
    need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['order']==engine['order']and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and engine['status']=='hold'and engine.get('error')==error,'draft-empty-failed-role-pair')
    need(bool(parent['calls'])and bool(engine['calls'])and not parent.get('completion')and engine['phase']=='collect','draft-empty-natural-stopped-role')
    index=len(engine['calls'])-1;failed=engine['calls'][index];i=engine['index'];artifacts=engine['companies'][i]['artifacts'];unit=artifacts['unit_artifacts'];key=unit['keys'][unit['review_index']]
    need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==i and failed['error']==error and artifacts['unit_phase']=='inspect','draft-empty-exact-resultless-tail')
    need(failed['context']=={'order':order,'company':order['companies'][i],'artifacts':artifacts,'folder':str(folder/'companies'/str(i)),'phase':'collect'},'draft-empty-tail-business-binding')
    expected={'kind':'complaint-draft-inspection-manifest-v1','root':order['companies'][i]['root'],'review_key':key,'inputs':{k:unit[k]for k in ('job','source','profile','envelope','page')}}
    need(set(operation)=={'state','manifest','submission_enabled','created_at','normal_before','open_command','open_reply','error'}and operation['state']=='opened'and operation['manifest']==expected and operation['submission_enabled']is False and operation['error']==error,'draft-empty-confirmed-open-no-close-submit')
    canonical=Path(expected['root'])/'draft-inspection/existing-result-operations'/__import__('hashlib').sha256(key.encode()).hexdigest()/unit['source']['sha256']/'operation.json';need(operation_ref['path']==str(canonical)and Path(form_ref['path']).parent==canonical.parent and Path(form_ref['path']).name.endswith('-form.json'),'draft-empty-canonical-original-operation-form')
    v,inspection_order,row=draft.inputs(expected);before=read(operation['normal_before']);action=draft.normal_page(before,v,inspection_order,row);need(operation['open_command']==draft.cmd(before,action['selector'],'complaint-draft'),'draft-empty-original-open-target');draft.clicked(operation['open_reply'],operation['open_command'])
    read(form_ref)  # raw original form preserved; no readiness/UI-effect claim
    child_index=len(parent['calls'])-1;child=parent['calls'][child_index];launch=read(child['launch']);ex=read(child['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(child_index).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(child_index).zfill(4)+'-exit.json'))and child['argv']==launch['argv']==ex['argv']==argv and launch['index']==child_index and launch['order']==parent['order']and ex['launch']==child['launch']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':error},'draft-empty-natural-child-exact-member')
    worker=read(worker_ref);request=read(worker['request']);response=read(worker['response']);need(type(worker['returncode'])is int and worker['returncode']==0 and worker['attempt_id']==request['attempt_id']==response['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['id']==response['task_id'],'draft-empty-natural-worker-original-order')
    if parent.get('child'):
        matching=[c['result']for c in parent['calls'][:-1]if read(c['result'])['returncode']==0 and json.loads(read(c['result'])['stdout'])==parent['child']];need(len(matching)==1,'draft-empty-cached-prior-child-result')
    receipt=folder/'receipts'/(str(index+1).zfill(5)+'.json');need(not receipt.exists()and not receipt.is_symlink(),'draft-empty-failed-receipt-absent')
    return {'error':error,'evidence':[parent_ref,engine_ref,worker_ref,worker['request'],worker['response'],operation_ref,form_ref,operation['normal_before'],child['launch'],child['result']],'kind':'confirmed-draft-open-empty-options-failure-facts-v1','task_id':request['task']['id'],'attempt_id':request['attempt_id'],'outer':request['task']['outer'],'order':parent['order'],'parent':parent_ref,'engine':engine_ref,'worker':worker_ref,'operation':operation_ref,'form':form_ref,'failed_engine_index':index,'failed_engine_call':copy.deepcopy(failed),'failed_child_index':child_index,'failed_child':copy.deepcopy(child),'confirmed_open_command':copy.deepcopy(operation['open_command']),'confirmed_open_reply':copy.deepcopy(operation['open_reply']),'new_input_authorized':False}


COMPANY_SCOPE_FIELD='company_scope_reconciliation'
COMPANY_SCOPE_KIND='retired-company-original-task-scope-reconciliation-v1'
_COMPANY_SCOPE_BUSINESS_VERIFY=_SOURCE_EPOCH_BUSINESS_VERIFY

def _company_policy(reference):
    import execution_timing as timing
    return timing.company_policy(reference)

def _company_scope_transform_checked(parent,engine,proof_ref,active_indices):
    pp,ee=copy.deepcopy(parent),copy.deepcopy(engine)
    for v in (pp,ee):
        v[COMPANY_SCOPE_FIELD]=proof_ref;v['status']='running';v.pop('error',None)
    # Original companies and all calls are immutable history. Retired is never ready.
    ee['index']=active_indices[0];ee['phase']=ee['companies'][ee['index']]['phase']
    return pp,ee

def company_scope_transform(parent,engine,proof_ref):
    p=o.doc(proof_ref);o.need(parent==o.doc(p['parent_archive'])and engine==o.doc(p['engine_archive']),'company-scope-original-archives')
    return _company_scope_transform_checked(parent,engine,proof_ref,p['active_indices'])

def _company_scope_archived_failure_facts(p,reader):
    def archived(reference):
        if reference==p['original_parent']:return reader(p['parent_archive'])
        if reference==p['original_engine']:return reader(p['engine_archive'])
        return reader(reference)
    return _retired_company_failure_facts(p['original_parent'],p['original_engine'],p['worker'],p['operation'],p['form'],_read=archived)

def _company_context_checkpoint(reference,p,policy):
    from urllib.parse import urlsplit,parse_qs
    from dom_evidence import identity
    c=o.doc(reference);active=policy['active'][0];grant=o.doc(c['authorization']);hover=o.doc(c['original_hover']);binding=hover['binding']
    o.need(c.get('kind')=='remaining-company-context-checkpoint-v1'and c.get('company')==active['company']and c.get('groupid')==active['groupid']and c.get('old_business_scope_migrated')is False and c.get('business_resume_authorized')is False and c.get('new_input_count')==0,'company-scope-context-kind')
    o.need(grant.get('kind')=='original-failed10-company-context-recovery-grant-v1'and grant.get('approved')is True and grant.get('readonly_reconcile_only')is True and grant.get('original_hover')==c['original_hover']and grant.get('business_resume_authorized')is False,'company-scope-context-original-grant')
    o.need(binding['task']==grant['task']==p['task_id']and binding['attempt']==grant['attempt']==int(p['attempt_id'].rsplit('-',1)[1])and binding['order']==grant['order']==p['order']and binding['target_company']==grant['target_company']==active['company']and binding['target_gid']==grant['target_gid']==active['groupid']and hover['state']=='confirmed'and hover['business_actions_enabled']is False,'company-scope-context-original-task-target')
    for k in ('tab_id','window_id'):o.need(binding[k]==grant[k],'company-scope-context-same-tab-window')
    observations=[o.doc(r)for r in c['observations']];commands=[{'op':'tabs'},{'op':'tree','tabId':binding['tab_id']},{'op':'tabs'}]
    o.need(len(observations)==3 and [x['command']for x in observations]==commands and all(x['reply']['ok']is True for x in observations),'company-scope-exact-readonly-reconcile')
    before,tree,after=[x['reply']['result']for x in observations]
    def selected(tabs):
        windows=[w for w in tabs if w.get('windowId')==binding['window_id']];found=[t for w in tabs for t in w.get('tabs',[])if t.get('tabId')==binding['tab_id']];o.need(len(windows)==len(found)==1 and windows[0].get('type')=='normal','company-scope-context-tab-window-unique');t=found[0];u=urlsplit(t['url']);q=parse_qs(u.query,keep_blank_values=True)
        o.need(t.get('windowId')==binding['window_id']and t.get('allowed')is True and u.scheme=='https'and u.netloc=='life.douyin.com'and u.path=='/p/home'and not u.fragment and q.get('groupid')==[active['groupid']]and (set(q)=={'groupid'}or(set(q)=={'groupid','life_biz_view_id','life_account_biz_ids'}and q['life_biz_view_id']==['22']and q['life_account_biz_ids']==[''])),'company-scope-context-exact-scope')
        return t
    o.need(selected(before)==selected(after)and tree.get('url')=='https://life.douyin.com/p/home'and tree.get('truncated')is False,'company-scope-context-stable-full-tree')
    o.need(identity(tree,grant['expected_identity'])==c['identity']==grant['expected_identity'],'company-scope-context-full-identity')
    return c

def _company_scope_proof_facts(proof_ref):
    p=o.doc(proof_ref);keys={'kind','policy','order','task_id','attempt_id','outer','original_parent','original_engine','parent_archive','engine_archive','worker','operation','form','facts','active_indices','retired_indices','context_checkpoint','at'}
    o.need(set(p)==keys and p['kind']==COMPANY_SCOPE_KIND and _window_time(p['at']),'company-scope-proof-schema')
    policy=_company_policy(p['policy']);parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);order=o.validate(p['order']);folder=phase_directory(parent);base=folder/'.company-scope-reconciliation'/p['original_parent']['sha256']
    o.need(proof_ref['path']==str(base/'proof.json')and all(p[n+'_archive']=={'path':str(base/(n+'-before.json')),'sha256':p['original_'+n]['sha256']}for n in ('parent','engine')),'company-scope-canonical-archives')
    # The old facts reader requires original canonical refs. Only these two
    # immutable snapshot reads are projected; no current/business validator stub.
    reader=o.doc
    # Do NOT patch o.doc globally: the extracted qualifier accepts a local reader.
    facts=_company_scope_archived_failure_facts(p,reader)
    o.need(facts==p['facts']and facts['task_id']==p['task_id']and facts['attempt_id']==p['attempt_id']and facts['outer']==p['outer']and facts['order']==p['order'],'company-scope-derived-original-failure')
    active=[i for i,c in enumerate(order['companies'])if {'company':c['company'],'groupid':c['groupid']}in policy['active']]
    retired=[i for i,c in enumerate(order['companies'])if any(c['company']==r['company']and c['groupid']==r['groupid']for r in policy['retired'])]
    o.need(active==p['active_indices']==[1]and retired==p['retired_indices']==[0]and engine['index']in retired and engine['companies'][1]=={'artifacts':{},'phase':'plan'},'company-scope-exact-retired-current-active-unstarted')
    _company_context_checkpoint(p['context_checkpoint'],p,policy)
    return p,parent,engine

def _company_scope_admission_checked(current,engine,proof_ref):
    p,bp,be=_company_scope_proof_facts(proof_ref);pp,ee=company_scope_transform(bp,be,proof_ref)
    for value,expected,before in ((current,pp,bp),(engine,ee,be)):
        variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass',SOURCE_EPOCH_FIELD}
        if value is engine:variable|={'phase','index','companies','business_journals','delivery','handoff','waiting_for','acceptance'}
        for key in set(expected)-variable:o.need(value.get(key)==expected[key],'company-scope-preserved-current-metadata')
        o.need(value['calls'][:len(before['calls'])]==before['calls'],'company-scope-preserved-all-original-calls')
    o.need(current.get(COMPANY_SCOPE_FIELD)==engine.get(COMPANY_SCOPE_FIELD)==proof_ref and engine['companies'][0]==be['companies'][0],'company-scope-retired-company-entire-object-preserved')
    f=p['facts'];slot=phase_directory(current)/'receipts'/(str(f['failed_engine_index']+1).zfill(5)+'.json');o.need(not slot.exists()and not slot.is_symlink(),'company-scope-resultless-retired-receipt-absent')
    return {'proof':proof_ref,'policy':p['policy'],'active_indices':p['active_indices'],'retired_indices':p['retired_indices'],'failed_engine_indices':[f['failed_engine_index']],'failed_calls':[f['failed_child']],'retired_incomplete':True,'active_scope_complete':False,'original_scope_complete':False,'evidence':[proof_ref,p['policy'],p['context_checkpoint'],p['parent_archive'],p['engine_archive'],*[r for r in f['evidence']if r not in (p['original_parent'],p['original_engine'])]]}

def _company_scope_business_verify(current,proof_ref,*,installed=True):
    admitted=_COMPANY_SCOPE_BUSINESS_VERIFY(current,proof_ref,installed=installed)
    if not current.get(COMPANY_SCOPE_FIELD):return admitted
    engine=o.doc(o.ref(phase_directory(current)/'engine.json'));scope=_company_scope_admission_checked(current,engine,current[COMPANY_SCOPE_FIELD])
    o.need(not set(scope['failed_engine_indices'])&set(admitted['failed_engine_indices']),'company-scope-distinct-retired-failure')
    return {**admitted,'failed_engine_indices':[*admitted['failed_engine_indices'],*scope['failed_engine_indices']],'failed_calls':[*admitted['failed_calls'],*scope['failed_calls']],'company_scope':scope,'evidence':[*admitted['evidence'],*scope['evidence']]}
_SOURCE_EPOCH_BUSINESS_VERIFY=_company_scope_business_verify

def company_scope_admission(state):
    """Consumer gate. Old orders without marker keep the legacy full scope."""
    if not state.get(COMPANY_SCOPE_FIELD):return None
    parent=o.doc(o.ref(phase_directory(state)/'launcher.json'));o.need(parent.get(COMPANY_SCOPE_FIELD)==state[COMPANY_SCOPE_FIELD]and parent['order']==state['order'],'company-scope-consumer-common-binding')
    admitted=verify_preengine_constructor(parent,parent[PREENGINE_FIELD]);scope=admitted['company_scope'];return {**scope,'retired_failed_indices':scope['failed_engine_indices'],'failed_engine_indices':admitted['failed_engine_indices'],'failed_calls':admitted['failed_calls'],'code_refs':admitted['code_refs'],'source_epoch':parent.get(SOURCE_EPOCH_FIELD),**({k:admitted[k]for k in ('historical_effective_code_refs','source_verification_kind')}if 'historical_effective_code_refs'in admitted else {})}

def plan_company_scope_retirement(parent_ref,engine_ref,worker_ref,operation_ref,form_ref,policy_ref,context_checkpoint_ref):
    """Read-only preplan; never writes, retires an input, selects company or retries."""
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);facts=_retired_company_failure_facts(parent_ref,engine_ref,worker_ref,operation_ref,form_ref)
    _company_policy(policy_ref);folder=phase_directory(parent);base=folder/'.company-scope-reconciliation'/parent_ref['sha256']
    o.need(not parent.get(COMPANY_SCOPE_FIELD)and not engine.get(COMPANY_SCOPE_FIELD),'company-scope-no-existing-marker')
    p={'kind':COMPANY_SCOPE_KIND,'policy':policy_ref,'order':parent['order'],'task_id':facts['task_id'],'attempt_id':facts['attempt_id'],'outer':facts['outer'],'original_parent':parent_ref,'original_engine':engine_ref,'parent_archive':{'path':str(base/'parent-before.json'),'sha256':parent_ref['sha256']},'engine_archive':{'path':str(base/'engine-before.json'),'sha256':engine_ref['sha256']},'worker':worker_ref,'operation':operation_ref,'form':form_ref,'facts':facts,'active_indices':[1],'retired_indices':[0],'context_checkpoint':context_checkpoint_ref,'at':datetime.now(timezone.utc).isoformat()}
    policy=_company_policy(policy_ref);_company_context_checkpoint(context_checkpoint_ref,p,policy)
    order=o.validate(parent['order']);o.need(engine['index']==0 and len(order['companies'])==len(engine['companies'])==2 and engine['companies'][1]=={'artifacts':{},'phase':'plan'},'company-scope-original-active-unstarted')
    return p

# Only immutable archive/failure facts are eligible for memo; canonical state and
# current retirement object/prefix checks remain outside on every public call.
_company_scope_proof_facts=_hm_history(_company_scope_proof_facts)

def recover_company_scope_retirement(plan_ref,source_release_ref,*,checkpoint=lambda stage:None):
    """Candidate metadata API only. Original outer locks/liveness/Root grant are caller duties."""
    plan=o.doc(plan_ref);parent_ref=plan['original_parent'];engine_ref=plan['original_engine'];folder=Path(parent_ref['path']).parent;base=folder/'.company-scope-reconciliation'/parent_ref['sha256'];root=_source_epoch_root(source_release_ref)
    with (folder/'launcher.lock').open('a')as pl,(folder/'engine.lock').open('a')as el:
        for lock in (pl,el):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        token=_SOURCE_EPOCH_ARCHIVES.set(tuple(root['targets']));ctx=_REGION_HISTORY_SOURCE.set(_region_source_context(root['previous_source_release']))
        try:
            if (base/'proof.json').exists():
                proof=o.ref(base/'proof.json');o.need(o.doc(proof)==plan,'company-scope-same-proof-reentry')
                o.need(o.doc(o.ref(base/'intent.json'))=={'kind':COMPANY_SCOPE_KIND,'plan':plan_ref,'source_release':source_release_ref},'company-scope-existing-intent-authority')
            else:
                o.need(not(base/'result.json').exists()and not(base/'result.json').is_symlink(),'company-scope-terminal-without-proof')
                facts=_retired_company_failure_facts(parent_ref,engine_ref,plan['worker'],plan['operation'],plan['form']);o.need(facts==plan['facts'],'company-scope-original-facts-unchanged')
                _company_context_checkpoint(plan['context_checkpoint'],plan,_company_policy(plan['policy']))
                for name,r in (('parent',parent_ref),('engine',engine_ref)):o.need(immutable_bytes(base/(name+'-before.json'),o.raw(r))==plan[name+'_archive'],'company-scope-archive-exact')
                checkpoint('archives');o.immutable(base/'intent.json',{'kind':COMPANY_SCOPE_KIND,'plan':plan_ref,'source_release':source_release_ref});checkpoint('intent');proof=o.immutable(base/'proof.json',plan);checkpoint('proof')
            _company_scope_proof_facts(proof);bp,be=o.doc(plan['parent_archive']),o.doc(plan['engine_archive']);pp,ee=company_scope_transform(bp,be,proof)
            cur=lambda:(o.doc(o.ref(parent_ref['path'])),o.doc(o.ref(engine_ref['path'])))
            o.need(cur()[0]in (bp,pp)and cur()[1]in (be,ee),'company-scope-metadata-pair-CAS')
            o.need(not(cur()[0]==pp and cur()[1]==be),'company-scope-impossible-parent-first')
            if (base/'result.json').exists()or(base/'result.json').is_symlink():
                o.need(not(base/'result.json').is_symlink()and cur()==(pp,ee),'company-scope-terminal-before-complete')
                result=o.ref(base/'result.json');o.need(o.doc(result)=={'kind':COMPANY_SCOPE_KIND,'proof':proof,'plan':plan_ref,'source_release':source_release_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'ui_used':False,'retry_issued':False},'company-scope-existing-result-authority');return result
            # Release binds the deterministic scoped snapshots, not a fabricated failure.
            o.need(root['binding']=={'parent':{'path':parent_ref['path'],'sha256':__import__('hashlib').sha256((json.dumps(pp,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()},'engine':{'path':engine_ref['path'],'sha256':__import__('hashlib').sha256((json.dumps(ee,ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()},'order':plan['order'],'business_proof':pp[WINDOW_HOLD_FIELD],'previous_epoch':pp.get(SOURCE_EPOCH_FIELD)},'company-scope-following-epoch-exact-binding')
            import complaint_execution_launcher as launch
            if cur()[1]==be:launch.save(Path(engine_ref['path']),ee)
            checkpoint('engine')
            o.need(cur()[0]in (bp,pp)and cur()[1]==ee,'company-scope-before-parent-CAS')
            if cur()[0]==bp:launch.save(Path(parent_ref['path']),pp)
            checkpoint('parent');_company_scope_admission_checked(*cur(),proof)
            result=o.immutable(base/'result.json',{'kind':COMPANY_SCOPE_KIND,'proof':proof,'plan':plan_ref,'source_release':source_release_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'ui_used':False,'retry_issued':False});checkpoint('result');return result
        finally:_REGION_HISTORY_SOURCE.reset(ctx);_SOURCE_EPOCH_ARCHIVES.reset(token)

_source_epoch_proof=_hm_history(_source_epoch_proof)


# Explicitly qualified pre-input failure member. This is independent of the
# source-only epoch: no clause means no error change or failure admission.
EPOCH_PREINPUT_KIND='role-source-epoch-confirmed-plan-preinput-source-guard-failure-v1'
def _epoch_preinput_failure_facts(parent_ref,engine_ref,worker_ref,*,reader=None,live=True):
    read=reader or o.doc;parent=read(parent_ref);engine=read(engine_ref);order=read(parent['order']);folder=phase_directory(parent);need=o.need;error='daily-live-source-change-not-authorized'
    need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['order']==engine['order']and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and engine['status']=='hold'and engine.get('error')==error and not parent.get('completion'),'epoch-preinput-exact-stopped-pair')
    need(parent.get(COMPANY_SCOPE_FIELD)==engine.get(COMPANY_SCOPE_FIELD)and bool(parent.get(COMPANY_SCOPE_FIELD))and parent.get(SOURCE_EPOCH_FIELD)==engine.get(SOURCE_EPOCH_FIELD)and bool(parent.get(SOURCE_EPOCH_FIELD)),'epoch-preinput-existing-scope-source')
    i=engine['index'];need(type(i)is int and 0<=i<len(engine['companies'])and engine['phase']=='collect'and engine['companies'][i]['phase']=='collect'and len(engine['calls'])>=2,'epoch-preinput-collect-position')
    index=len(engine['calls'])-1;failed=engine['calls'][index];a=engine['companies'][i]['artifacts'];unit=Path(folder/'companies'/str(i)/'units'/str(a['unit_index']))
    need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['step']=='collect'and failed['state']=='failed'and failed['company_index']==i and failed['error']==error,'epoch-preinput-resultless-exact-tail')
    need(failed['context']=={'order':order,'company':order['companies'][i],'artifacts':a,'folder':str(folder/'companies'/str(i)),'phase':'collect','company_scope_reconciliation':parent[COMPANY_SCOPE_FIELD]},'epoch-preinput-context-full-binding')
    need(a['unit_phase']=='acquire'and not a['journals']and not a['completed_units']and 'unit_artifacts'not in a and set(a)=={'completed_units','immutable_refs','journals','plan','unit_index','unit_phase','units'},'epoch-preinput-acquire-no-business-state')
    prior=engine['calls'][index-1];need(prior['step']=='plan'and prior['state']=='returned'and prior['applied']is True and prior['company_index']==i and prior['context']['order']==order and prior['context']['company']==order['companies'][i]and prior['result']['path']==str(folder/'receipts'/(str(index).zfill(5)+'.json')),'epoch-preinput-preserved-applied-plan-call')
    receipt=read(prior['result']);need(receipt=={'artifacts':a,'done':True}and a['plan']['path']==str(folder/'companies'/str(i)/'plan.json')and a['immutable_refs']==[a['plan']],'epoch-preinput-plan-receipt-exact-artifacts');read(a['plan'])
    slot=folder/'receipts'/(str(index+1).zfill(5)+'.json')
    if live:need(not slot.exists()and not slot.is_symlink()and unit.is_dir()and not unit.is_symlink()and list(unit.iterdir())==[],'epoch-preinput-no-receipt-workorder-workflow')
    ci=len(parent['calls'])-1;child=parent['calls'][ci];launch=read(child['launch']);ex=read(child['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(ci).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(ci).zfill(4)+'-exit.json'))and child['argv']==launch['argv']==ex['argv']==argv and launch['index']==ci and launch['order']==parent['order']and ex['launch']==child['launch']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':error},'epoch-preinput-natural-child-result')
    worker=read(worker_ref);request=read(worker['request']);response=read(worker['response']);need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json')and type(worker['returncode'])is int and worker['returncode']==0 and worker['attempt_id']==request['attempt_id']==response['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['id']==response['task_id'],'epoch-preinput-natural-worker-original-order')
    origin=read(parent['origin_ref']);scope=read(parent[COMPANY_SCOPE_FIELD]);need(all(parent[k]==origin[k]for k in ('wall_started_at','start_monotonic','boot_identity','clock_contract'))and request['task']['outer']==scope['outer']and request['task']['id']==scope['task_id'],'epoch-preinput-original-outer-clock')
    return {'kind':EPOCH_PREINPUT_KIND,'parent':parent_ref,'engine':engine_ref,'worker':worker_ref,'task_id':request['task']['id'],'attempt_id':request['attempt_id'],'outer':request['task']['outer'],'order':parent['order'],'error':error,'failed_engine_index':index,'failed_engine_call':copy.deepcopy(failed),'failed_child_index':ci,'failed_child':copy.deepcopy(child),'company_index':i,'company_snapshot':copy.deepcopy(engine['companies'][i]),'receipt_absence':str(slot),'unstarted_unit':str(unit),'evidence':[worker_ref,worker['request'],worker['response'],parent['origin_ref'],parent[COMPANY_SCOPE_FIELD],child['launch'],child['result'],prior['result'],a['plan']]}

def _epoch_preinput_archived_facts(p):
    f=p['preinput_failure_admission'];refs={p['original_parent']['path']:p['parent_archive'],p['original_engine']['path']:p['engine_archive']}
    def read(r):
        if r['path']in refs:
            archive=refs[r['path']];o.need(r['sha256']==archive['sha256'],'epoch-preinput-original-archive-sha');return o.doc(archive)
        return o.doc(r)
    return _epoch_preinput_failure_facts(p['original_parent'],p['original_engine'],f['worker'],reader=read,live=False)
_epoch_preinput_archived_facts=_hm_history(_epoch_preinput_archived_facts)

def _epoch_preinput_live_guard(current,engine,p):
    f=p['preinput_failure_admission'];bp=o.doc(p['parent_archive']);be=o.doc(p['engine_archive']);need=o.need
    need(current['calls'][:len(bp['calls'])]==bp['calls']and engine['calls'][:len(be['calls'])]==be['calls']and engine['companies'][0]==be['companies'][0],'epoch-preinput-all-history-retired-object-preserved')
    slot=Path(f['receipt_absence']);need(not slot.exists()and not slot.is_symlink(),'epoch-preinput-resultless-receipt-still-absent')
    # Later normal acquisition may create its own files after this explicit
    # admission; only the initial metadata transform requires the unit empty.
    need(current['order']==engine['order']==p['order']and f['failed_engine_call']==engine['calls'][f['failed_engine_index']],'epoch-preinput-live-member-unchanged')





# Completed source bytes are evidence data, never runtime code authority.
_COMPLETED_SOURCE_CONTEXT=_RegionContextVar('completed_complaint_source_seal',default=None)

def _completed_source_paths():
    return {str(o.PROJECT / 'skills/negative-review-complaints/scripts' / n) for n in ('initial_ledger_recovery.py', 'complaint_execution_ports.py', 'history_workspace.py')} | {str(o.PROJECT / 'skills/chrome-dom-export/scripts/bridge.py'), str(o.PROJECT / 'skills/wecom-messenger/scripts/files.py'), str(o.PROJECT / 'skills/workshop-director/scripts/complaint_execution_launcher.py')} | {str(o.PROJECT / 'skills/douyin-laike-operator/scripts/bridge-workflow.py')} | {str(o.PROJECT / 'skills/douyin-laike-operator/scripts/switch_read_recovery.py')} | {'/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/content.js', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_paging_runner.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/legacy_alias_code_replay.py'} | {'/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/complaint_execution_launcher.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/complaint_execution_order.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/complaint_execution_orchestration.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/complaint_execution.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/workflow.py'} | {'/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/export_baseline_pages.py', '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/sw17.js', '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/policy.js', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/prepare_company_navigation.py'} | ({str(o.PROJECT / 'skills/negative-review-complaints/scripts' / n) for n in ('initial_ledger_recovery.py', 'complaint_execution_ports.py', 'history_workspace.py', 'normal_observation.py', 'bridge-navigation.py', 'normal_paging.py', 'normal_case_journey.py', 'existing_result_runner.py')} | {str(o.PROJECT / 'skills/chrome-dom-export/scripts/bridge.py'), str(o.PROJECT / 'skills/wecom-messenger/scripts/files.py'), str(o.PROJECT / 'skills/workshop-director/scripts/complaint_execution_launcher.py')} | {str(o.PROJECT / 'skills/douyin-laike-operator/scripts/bridge-workflow.py')} | {str(o.PROJECT / 'skills/douyin-laike-operator/scripts/switch_read_recovery.py')} | {'/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/content.js', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_paging_runner.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/legacy_alias_code_replay.py'} | {str(o.PROJECT / 'skills/douyin-laike-operator/scripts/export_baseline_pages.py')})

def _completed_regular(path):
    path=Path(path)
    o.need(path.is_absolute()and path.resolve()==path and path.is_file()and not path.is_symlink(),'completed-source-canonical-regular')
    return path

def _completed_source_seal(current):
    """A source-data eligibility seal, not a substitute for business replay."""
    folder=phase_directory(current);parent_path=_completed_regular(folder/'launcher.json');parent_ref=o.ref(parent_path)
    o.need(o.doc(parent_ref)==current and current.get('status')=='complete' and not current.get('error'),'completed-source-exact-canonical-parent')
    order=o.doc(current['order']);o.need(order.get('workflow')=='negative-review-complaints'and order.get('role')=='complaint_operator'and current.get('scope_sha256')==order['scope_sha256'],'completed-source-order-scope')
    origin=o.doc(current['origin_ref']);o.need(all(current.get(k)==v for k,v in origin.items()),'completed-source-origin-changed')
    completion=current.get('completion');o.need(type(completion)is dict and set(completion)=={'path','sha256'}and completion['path']==str(folder/'completion.json'),'completed-source-canonical-final')
    final=o.doc(completion);engine_ref=o.ref(_completed_regular(folder/'engine.json'));engine=o.doc(engine_ref)
    o.need(final.get('kind')=='complaint-outer-completion-v1'and final.get('order')==current['order']==engine.get('order')and final.get('engine')==engine_ref and final.get('start_monotonic')==current['start_monotonic']and final.get('end_monotonic')==current['end_monotonic']and final.get('completed_at')==current['wall_ended_at'],'completed-source-final-binding')
    child=current.get('child');o.need(type(child)is dict and child.get('kind')=='complaint-execution-child-result-v1'and child.get('status')=='complete'and child.get('phase')=='finish'and child.get('order')==current['order']and child.get('engine')==engine_ref and not child.get('error'),'completed-source-terminal-child')
    last=current['calls'][-1];child_exit=o.doc(last['result']);o.need(last.get('state')=='returned'and last['result']['path']==str(folder/'children'/(str(len(current['calls'])-1).zfill(4)+'-exit.json'))and child_exit.get('returncode')==0 and json.loads(child_exit['stdout'])==child,'completed-source-natural-terminal-exit')
    o.need(engine.get('status')=='complete'and engine.get('phase')=='finish'and not engine.get('error')and final.get('proof')==engine.get('completion')and final.get('outcome')==engine['completion']['outcome']and final['proof'].get('submission_enabled')is False and final['proof'].get('production_sent')is False,'completed-source-engine-client-result-binding')
    o.need(current.get(SOURCE_EPOCH_FIELD)==engine.get(SOURCE_EPOCH_FIELD)and current.get(COMPANY_SCOPE_FIELD)==engine.get(COMPANY_SCOPE_FIELD),'completed-source-original-common-proof')
    pins=[parent_ref,engine_ref,current['order'],current['origin_ref'],completion,last['result']]
    if current.get(SOURCE_EPOCH_FIELD):
        epoch_ref=current[SOURCE_EPOCH_FIELD];epoch=o.doc(epoch_ref);codes=epoch.get('effective_code_refs')
        o.need(epoch.get('kind')==SOURCE_EPOCH_KIND and epoch.get('order')==current['order']and epoch_ref['path']==str(folder/'.source-epochs'/epoch['original_parent']['sha256']/'proof.json'),'completed-source-canonical-epoch')
        pins.extend([epoch_ref,epoch['source_release']])
    else:
        o.need(not any(current.get(k)for k in (PREENGINE_FIELD,COMPANY_SCOPE_FIELD,WINDOW_HOLD_FIELD,'initial_ledger_origin_recovery')),'completed-source-unhandled-recovery-lineage')
        codes=current['code_refs'];o.need(codes==origin['code_refs']and all(c.get('state')=='returned'and c.get('applied')and c.get('result')for c in engine['calls']),'completed-source-original-no-recovery-vector')
        for c in current['calls']:
            child_result=o.doc(c['result']);o.need(c.get('state')=='returned'and child_result.get('returncode')==0,'completed-source-original-no-recovery-child');pins.extend([c['launch'],c['result']])
        pins.extend(c['result']for c in engine['calls'])
    o.need(type(codes)is list and len(codes)==len({r['path']for r in codes})==160 and _completed_source_paths()<={r['path']for r in codes},'completed-source-exact-original160')
    external=[]
    if current.get(SOURCE_EPOCH_FIELD):
        original_root=o.doc(epoch['source_release']);graph_paths={r['path']for r in codes}
        external=[{'path':t['target'],'sha256':t['after']['sha256']}for t in original_root['targets']if t['target']not in graph_paths]
        # Existing source-epoch validator authenticates the complete lineage and
        # target whitelist. Only this already-published external drift is mapped.
    if current.get(COMPANY_SCOPE_FIELD):pins.append(current[COMPANY_SCOPE_FIELD])
    clients=final['proof'].get('clients');o.need(type(clients)is list,'completed-source-client-refs-required')
    for reference in clients:
        o.need(type(reference)is dict and set(reference)=={'path','sha256'},'completed-source-client-ref-schema');_completed_regular(reference['path']);o.raw(reference);pins.append(reference)
    return {'kind':'completed-complaint-source-data-seal-v1','pins':pins,'historical_effective_code_refs':copy.deepcopy(codes),'external_refs':external,'allowed_paths':sorted(_completed_source_paths()|{r['path']for r in external}),'catalogue':_completed_generation_catalogue()}

def _completed_source_fresh(seal):
    for reference in seal['pins']:o.raw(reference)

def _completed_source_verification_ref(reference,seal):
    """Fixed SHA archive fallback for exactly two graph slots, only while sealed."""
    path=_completed_regular(reference['path'])
    try:
        o.raw(reference);return copy.deepcopy(reference)
    except ValueError:
        _completed_source_fresh(seal)
        o.need(reference['path']in seal['allowed_paths']and (reference in seal['historical_effective_code_refs']or reference in seal['external_refs']),'completed-source-unreviewed-slot')
        checksum=reference['sha256'];o.need(type(checksum)is str and len(checksum)==64 and all(c in '0123456789abcdef'for c in checksum),'completed-source-sha-format')
        result=seal['catalogue'].get((reference['path'],checksum));o.need(result is not None,'completed-source-unreviewed-generation');o.raw(result);_completed_source_fresh(seal);return copy.deepcopy(result)

def _completed_source_code_raw(reference):
    seal=_COMPLETED_SOURCE_CONTEXT.get()
    if seal is None:return o.raw(reference)
    return o.raw(_completed_source_verification_ref(reference,seal))

# The original overlay stays installed=True and still verifies all160 slots,
# exact targets/modes/archives. Only the two explicit byte reads may be archived.
_COMPLETED_PREVIOUS_VERIFY_SOURCE_EPOCH=verify_source_epoch
_COMPLETED_PREVIOUS_OVERLAY=_source_epoch_overlay

def _source_epoch_overlay(codes,root,*,installed):
    # Avoid any live/archive authority mixing in memo keys: the rare completed
    # verification path checks physical/archive dependencies directly each call.
    if installed and _COMPLETED_SOURCE_CONTEXT.get()is not None:return _SOURCE_EPOCH_PURE_OVERLAY(codes,root,installed=True)
    return _COMPLETED_PREVIOUS_OVERLAY(codes,root,installed=installed)

def verify_source_epoch(current,epoch_ref,*,installed=True):
    if not installed or current.get('status')!='complete':
        # Nested live/historical calls cannot inherit an outer completed seal.
        token=_COMPLETED_SOURCE_CONTEXT.set(None)
        try:return _COMPLETED_PREVIOUS_VERIFY_SOURCE_EPOCH(current,epoch_ref,installed=installed)
        finally:_COMPLETED_SOURCE_CONTEXT.reset(token)
    seal=_completed_source_seal(current);o.need(current[SOURCE_EPOCH_FIELD]==epoch_ref,'completed-source-requested-epoch')
    token=_COMPLETED_SOURCE_CONTEXT.set(seal)
    try:
        result=_COMPLETED_PREVIOUS_VERIFY_SOURCE_EPOCH(current,epoch_ref,installed=True)
        historical=result['code_refs'];o.need(historical==seal['historical_effective_code_refs'],'completed-source-public-historical160-changed')
        materials=[_completed_source_verification_ref(r,seal)for r in historical]
        o.need(len(materials)==160 and len({r['path']for r in materials})==160,'completed-source-verification-material-count')
        external_materials=[_completed_source_verification_ref(r,seal)for r in seal['external_refs']]
        _completed_source_fresh(seal)
        # Explicitly NOT new executable/effective code origins. Existing callers
        # o.raw these material refs; original canonical history is retained.
        return {**result,'code_refs':materials,'historical_effective_code_refs':copy.deepcopy(historical),'source_verification_kind':'completed-sealed-code-data-materials-v1','source_verification_evidence':[_COMPLETED_CATALOGUE_REF,*external_materials],'evidence':[*result['evidence'],_COMPLETED_CATALOGUE_REF,*external_materials]}
    finally:_COMPLETED_SOURCE_CONTEXT.reset(token)

# Public completed verification materials are data, never new execution origins.
import hashlib
_COMPLETED_CATALOGUE_REF={'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/references/completed-source-catalogues/3153ac9a9717a1df65f7c436a50d084481aa1813837c20a49bb80dbe4f132814.json', 'sha256': '3153ac9a9717a1df65f7c436a50d084481aa1813837c20a49bb80dbe4f132814'}
def _completed_generation_catalogue():
    o.need(type(_COMPLETED_CATALOGUE_REF)is dict,'completed-source-catalogue-unbound')
    doc=o.doc(_COMPLETED_CATALOGUE_REF);o.need(set(doc)=={'kind','entries'}and doc['kind']=='reviewed-complaint-source-generation-catalogue-v1'and type(doc['entries'])is list and 0<len(doc['entries'])<=32,'completed-source-catalogue-schema');found={}
    for e in doc['entries']:
        o.need(set(e)=={'original','archive','generation'}and (set(e['generation'])=={'release','slot'}or set(e['generation'])=={'kind','parent','vector_sha256'}),'completed-source-catalogue-entry');r=e['original'];a=e['archive'];key=(r['path'],r['sha256'])
        o.need(r['path']in (_completed_source_paths()|{str(o.PROJECT/'skills/workshop-director/scripts/daily_execution_launcher.py')})and key not in found and a=={'path':str(o.PROJECT/'skills/negative-review-complaints/references/completed-source-archives'/(r['sha256']+'.py')),'sha256':r['sha256']},'completed-source-catalogue-finite-path-sha')
        if 'kind'in e['generation']:
            _completed_source_seed(e);o.raw(a);found[key]=a;continue
        if e['generation']=={'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/c4-readonly-scope-candidate/supervisor-release.json', 'sha256': '117c9ec1b803e2c172193cc2a98eefa47f455e9c97ed4c6ad58485c6179393a2'}, 'slot': 'source'}:
            o.need(r=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/export_baseline_pages.py', 'sha256': '9e18d1d5052a967e1bd7d0db4d91e4e0eb2d2730f2ed4b3337616ae55c4f9fd0'},'completed-baseline-exact-published-slot');published=o.doc(e['generation']['release']);o.need(published.get('kind')=='supervisor-source-release-v1'and published.get('source')==r['path']and published.get('sha256')==r['sha256']and published.get('UI_calls')==0 and published.get('old_admissions_rewritten')is False,'completed-baseline-published-origin');o.raw(a);found[key]=a;continue
        published_origins={'/Users/feibing/work/projects/zmaibaole/work/performance-audit/export-terminal-prev-candidate/supervisor-release.json': {'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/export-terminal-prev-candidate/supervisor-release.json', 'sha256': '9eca07d03ad684968159c1052cde456fa21350acf2d8dfbf05c53872ddddce41'}, 'kind': 'supervisor-reviewed-content-update-release-v1', 'slot': 'published_files', 'sources': {'/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/content.js': '090a35790f9483694fd4c3868f7f8d975eebeea0592086a305c6ec422b2b4080'}}, '/Users/feibing/work/projects/zmaibaole/work/performance-audit/first-page-terminal-candidate/supervisor-publication/release.json': {'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/first-page-terminal-candidate/supervisor-publication/release.json', 'sha256': 'e3fe51a20c2fa73abdfcdb7dd71f850cbb17ee6bc22ace4fbe251e5d4ae10ac5'}, 'kind': 'supervisor-first-page-terminal-profile-code-release-v1', 'slot': 'files_after', 'sources': {'/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_paging_runner.py': '6981acb601e51685914549c54b6a9c128538da750a2ac48eeb5613fcb858a283'}}}
        spec=published_origins.get(e['generation']['release']['path'])
        if spec is not None:
            o.need(e['generation']['release']==spec['release']and e['generation']['slot']==spec['slot']and spec['sources'].get(r['path'])==r['sha256'],'completed-typed-published-exact-slot')
            published=o.doc(spec['release']);o.need(published.get('kind')==spec['kind']and published.get('published')is True,'completed-typed-published-root')
            items=published['published_files']if spec['slot']=='published_files'else published['files'];matches=[t for t in items if t.get('path')==r['path']]
            o.need(len(matches)==1 and (matches[0].get('sha256')if spec['slot']=='published_files'else matches[0].get('after'))==r['sha256'],'completed-typed-published-payload')
            o.raw(a);found[key]=a;continue
        root=o.doc(e['generation']['release']);o.need(root.get('published')is True and ((root.get('kind')=='supervisor-reviewed-switch-confirm-settle-anchor-source-release-v1'and e['generation']['release']=={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/switch-confirm-settle-anchor-maintenance-candidate/supervisor-release.json', 'sha256': 'df96d216218d29a4b4a751a9a34e6b6f5efbfa59e8405a8c4d49081fe5d8aaf9'}and r=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/switch_read_recovery.py', 'sha256': '8381addf15630c54d0d48a216f10126f5beb45a417194d78b11186c944560438'}and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director')or(root.get('kind')in ('supervisor-reviewed-source-release-v1','supervisor-reviewed-role-source-epoch-v1')and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director')or(root.get('kind')=='supervisor-reviewed-completed-complaint-sealed-source-release-v1'and root.get('plans_or_business_authorized')is False and root.get('runtime_metadata_authorized')is False)),'completed-source-catalogue-published')
        ts=[t for t in root.get('targets',root.get('code_targets',[]))if type(t)is dict and t.get('target')==r['path']];slot=e['generation']['slot'];o.need(len(ts)==1 and slot in ('before','after')and ts[0].get(slot,{}).get('sha256')==r['sha256'],'completed-source-catalogue-generation');o.raw(ts[0][slot]);o.raw(a);found[key]=a
    return found

def completed_source_materials(current):
    """No-marker consumer hook; marker paths retain original deep validators."""
    seal=_completed_source_seal(current);o.need(not current.get(SOURCE_EPOCH_FIELD),'completed-source-marker-use-public-validator')
    materials=[_completed_source_verification_ref(r,seal)for r in seal['historical_effective_code_refs']];_completed_source_fresh(seal)
    return {'code_refs':materials,'historical_effective_code_refs':copy.deepcopy(seal['historical_effective_code_refs']),'source_verification_kind':'completed-reviewed-generation-data-materials-v1'}

def _completed_source_seed(entry):
    """Root-reviewed first-generation files/bridge data only; no future-release cycle."""
    r = entry['original']
    g = entry['generation']
    o.need(g['kind'] == 'completed-original-source-vector-seed-v1' and (r['path'], r['sha256']) in {(str(o.PROJECT / 'skills/wecom-messenger/scripts/files.py'), 'a4d4a6c2e9290b694d7658d21c6fbe28f5c331106ea546ce592923fee8d6961b'), (str(o.PROJECT / 'skills/chrome-dom-export/scripts/bridge.py'), 'a99b58336b8007825d27458fde04ea7ce68773181471c0d6f0e14a84daca301d'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts/history_workspace.py'), 'cff7e771f2478aea0cec20686e6c9d5f8124f8532b8f65f191efb21393132f6d'), ('/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/workflow.py', '96ddcea071901d2b7b3e9ff82fcb3bcc6aa8d49824755c3e0ded7002f96f2e75')} | {('/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/sw17.js', '4672304381114e8ab9ca21c1a41d1a4b1beb977e6e29c36184102817c874c369'), ('/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', 'd38d42e0f0aa221757f591136a3f3b1600975b2ef09b6592058cc75b14dee7af'), ('/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/policy.js', '3464df27fa8c6b2e1fa1bbc0bb6727c49eb4d864faec2bfddf2b4c5489261605'), ('/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/prepare_company_navigation.py', '30022fe829b217d3f874e0b36e64da3d4c0c3ea932405975a5595fa48b1e62d1')} | {(str(o.PROJECT / 'skills/wecom-messenger/scripts/files.py'), 'a4d4a6c2e9290b694d7658d21c6fbe28f5c331106ea546ce592923fee8d6961b'), (str(o.PROJECT / 'skills/chrome-dom-export/scripts/bridge.py'), 'a99b58336b8007825d27458fde04ea7ce68773181471c0d6f0e14a84daca301d'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts/history_workspace.py'), 'cff7e771f2478aea0cec20686e6c9d5f8124f8532b8f65f191efb21393132f6d'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_observation.py'), '0c3215ca79fe4bbd724dd7ca8620778b74b1b3698bd6a1fdd69eb7bdcde6b14d'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'bridge-navigation.py'), '629d65fa0ccae17b5dcd0c149a12d216e6797635924e8cafb66bf009407bff58'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_paging.py'), 'fe3601e6b7949ff3c3771a3db139be0b90faa9a86a1052a8374b3e148f193744'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_case_journey.py'), '52ca8ce8a15ca26efe5de32e6d0b9000b280a58c0eb52e2f9a1d54f83523aaa4'), (str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'existing_result_runner.py'), 'a1f14ccab53961bbca35a9907c1f4dc6af50aceb419e68848dc1636709488665')}, 'completed-source-seed-finite-path-sha')
    p = o.doc(g['parent'])
    folder = o.location(p['order'])
    o.need(g['parent']['path'] == str(folder / 'launcher.json') and p.get('status') == 'complete' and (not p.get('error')), 'completed-source-seed-canonical-complete')
    origin = o.doc(p['origin_ref'])
    o.need(all((p.get(k) == v for (k, v) in origin.items())), 'completed-source-seed-origin')
    engine_ref = o.ref(folder / 'engine.json')
    engine = o.doc(engine_ref)
    final = o.doc(p['completion'])
    exit = o.doc(p['calls'][-1]['result'])
    o.need(p['completion']['path'] == str(folder / 'completion.json') and engine.get('status') == 'complete' and (engine.get('order') == p['order'] == final.get('order')) and (final.get('engine') == engine_ref) and (final.get('proof') == engine.get('completion')) and (exit.get('returncode') == 0) and (json.loads(exit['stdout']) == p['child']) and (p['child'].get('status') == 'complete'), 'completed-source-seed-terminal')
    if p.get('role_source_epoch'):
        epoch = o.doc(p['role_source_epoch'])
        o.need(epoch['order'] == p['order'], 'completed-source-seed-epoch-order')
        codes = epoch['effective_code_refs']
    elif p.get('violation_confirmed_navigation_wait_recovery'):
        proof = o.doc(p['violation_confirmed_navigation_wait_recovery'])
        codes = proof['code_refs']
    else:
        codes = p['code_refs']
        o.need(codes == origin['code_refs'], 'completed-source-seed-original-vector')
    o.need(len(codes) == len({v['path'] for v in codes}) and (len(codes) == 160 if r['path'] in (str(o.PROJECT / 'skills/chrome-dom-export/scripts/bridge.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts/history_workspace.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_observation.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'bridge-navigation.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_paging.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'normal_case_journey.py'), str(o.PROJECT / 'skills/negative-review-complaints/scripts' / 'existing_result_runner.py')) else len(codes) in (150, 160)) and (sum((v == r for v in codes)) == 1) and (hashlib.sha256(json.dumps(codes, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest() == g['vector_sha256']), 'completed-source-seed-vector-binding')

_COMPLETED_PREVIOUS_CAPTURE_RAW=_capture_focus_code_raw
_COMPLETED_PREVIOUS_REGION_RAW=_region_history_code_raw
def _capture_focus_code_raw(reference,source_successor=None):
    seal=_COMPLETED_SOURCE_CONTEXT.get()
    if seal is not None and reference in seal['historical_effective_code_refs']and reference['path']in seal['allowed_paths']:return _completed_source_code_raw(reference)
    return _COMPLETED_PREVIOUS_CAPTURE_RAW(reference,source_successor)
def _region_history_code_raw(reference):
    seal=_COMPLETED_SOURCE_CONTEXT.get()
    if seal is not None and reference in seal['historical_effective_code_refs']and reference['path']in seal['allowed_paths']:return _completed_source_code_raw(reference)
    return _COMPLETED_PREVIOUS_REGION_RAW(reference)


# Independent typed DOM identity provenance; no daily rows become complaints.
DOM_PREENGINE_KIND='complaint-preengine-typed-dom-identity-origin-recovery-v1'
DOM_PREENGINE_RELEASE='supervisor-reviewed-complaint-dom-identity-origin-source-release-v1'
DOM_PREENGINE_NAMES=('complaint_execution_ports.py','initial_ledger_recovery.py','collection_ready.py')
def dom_preengine_paths():
    return {n:str(o.PROJECT/('skills/workshop-director/scripts/'if n=='collection_ready.py'else'skills/negative-review-complaints/scripts/')/n)for n in DOM_PREENGINE_NAMES}

def _dom_preengine_facts(original_ref,worker_exit_ref,original_archive):
    original=o.doc(original_archive);o.need(original_archive['sha256']==original_ref['sha256'],'dom-preengine-original-bytes')
    o.need(original_ref['path']==str(phase_directory(original)/'launcher.json')and not original.get(PREENGINE_FIELD),'dom-preengine-original-canonical')
    facts=original_failure(original,worker_exit_ref,require_engine_absent=False,expected_error='complaint-parent-acquisition-copy-path');order=facts['order']
    o.need(order.get('collection_contract')=='three-flow-collection-ready-v1'and len(original['code_refs'])==len({r['path']for r in original['code_refs']})==170,'dom-preengine-staged-original170')
    # order.validate above has already verified this complete public ready graph.
    # Consume its pinned batch and typed origins once, not a second ready replay.
    report=o.doc(order['daily_collection_ready']);ready=o.doc(report['ready']);batch=o.doc(ready['batch']);registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']}
    from complaint_execution_ports import validated_acquisition_origin
    origins=[validated_acquisition_origin(row,batch,ready['batch'],ready,report['ready'],registry,materials_kind='collection-ready')for row in batch['companies']if row.get('status')!='skipped']
    o.need(len(origins)==len(order['companies'])and any(x.get('kind')=='verified-daily-dom-identity-context-v1'for x in origins),'dom-preengine-actual-typed-origin')
    snapshots=[c['ledger']for c in order['companies']]
    for r in snapshots:o.raw(r)
    return {**facts,'original':original,'origins':origins,'evidence':[*facts['evidence'],order['daily_collection_ready'],report['ready'],ready['batch'],*snapshots]}
_dom_preengine_facts=_hm_history(_dom_preengine_facts)

# Immutable proof facts retain historical source vectors. Only the executor
# generation returned by public admission may follow reviewed finite successors.
def _reviewed_historical_bridge_source(reference):
    # Data-only W53 bridge successor, using the already-published W54 resolver.
    import importlib.util
    release_ref={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue54-capture-history-maintenance/source/full2/supervisor-release.json', 'sha256': 'a88d8faa3ba963cf6f1a244dd55eef3f27c414564acb35708d5dece35bd43a13'}
    release=o.doc(release_ref);path=o.PROJECT/'skills/daily-comment-stats/scripts/dom_fresh_capture.py'
    rows=[t for t in release['targets']if t['target']==str(path)]
    o.need(release['kind']=='supervisor-reviewed-source-release-v1'and release['published']is True and release['test_projection_only']is False and len(rows)==1,'role-bridge-reviewed-resolver-release')
    current_source=o.ref(path);o.need(current_source['sha256']==rows[0]['after']['sha256'],'role-bridge-resolver-installed-generation');o.raw(rows[0]['after'])
    spec=importlib.util.spec_from_file_location('_role_reviewed_bridge_history',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    live=o.ref(o.PROJECT/'skills/chrome-dom-export/scripts/bridge.py');dependencies=module.historical_bridge_material(reference,live)
    material=next(r for r in dependencies if r['sha256']==reference['sha256']and r['path']!=reference['path'])
    o.raw(material);return {'historical':reference,'current':live,'material':material,'dependencies':[release_ref,current_source,*dependencies]}


_ROLE_READY_PREFIX=[{'index': 1, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '0f4a166e0ea9675c3a04257d86bce9203790a92fa4b0f8bb589a86dad3230cf9'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '01e3b4f52c8c6885ad014c0bcca378f6b110078b63845533af35c8fc15e1a1c7'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/0f4a166e0ea9675c3a04257d86bce9203790a92fa4b0f8bb589a86dad3230cf9.json', 'sha256': 'c4590a2f0b6469949b08e97bb2f0282a10babc2d2499b8438bf0413acf7f3dd2'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue31-command-history-performance-maintenance/source/material3/supervisor-release.json', 'sha256': 'a29e9375c679eec84d0de8f155f007a784f076fc9855ef11fdc3825e421b4007'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue31-command-history-performance-maintenance/source/material3/collection_ready.py.before', 'sha256': '0f4a166e0ea9675c3a04257d86bce9203790a92fa4b0f8bb589a86dad3230cf9'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/daily-ready-command-history-sharing-v3-closure-candidate/collection_ready.py', 'sha256': '01e3b4f52c8c6885ad014c0bcca378f6b110078b63845533af35c8fc15e1a1c7'}, 'mode': 420, 'target_count': 3, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py']}, {'index': 2, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '01e3b4f52c8c6885ad014c0bcca378f6b110078b63845533af35c8fc15e1a1c7'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'b29afb3b7dfadcc7876e131863ff77709678e137e8a9dc6aad12b4ca1e72e10a'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/01e3b4f52c8c6885ad014c0bcca378f6b110078b63845533af35c8fc15e1a1c7.json', 'sha256': '8c7c85eb6abceac6bd3919779f4c0976689ab8ac141e2117c82c81858e7fc467'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue33-normal-filter-recovery-maintenance/source/material3/supervisor-release.json', 'sha256': 'f3604445baa269a8ac7354ed5ca924315f0ad1e8d26923b40a4a67d16b3b2dcc'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue33-normal-filter-recovery-maintenance/source/material3/collection_ready.py.before', 'sha256': '01e3b4f52c8c6885ad014c0bcca378f6b110078b63845533af35c8fc15e1a1c7'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-normal-filter-bounded-recovery-candidate/snapshot-v4/collection_ready.py', 'sha256': 'b29afb3b7dfadcc7876e131863ff77709678e137e8a9dc6aad12b4ca1e72e10a'}, 'mode': 420, 'target_count': 3, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 3, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'b29afb3b7dfadcc7876e131863ff77709678e137e8a9dc6aad12b4ca1e72e10a'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'cbcf703774e1f53255b1bf8dc55f1983f61c9d18af8226b7513a5195bb7a9e5d'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/b29afb3b7dfadcc7876e131863ff77709678e137e8a9dc6aad12b4ca1e72e10a.json', 'sha256': 'c054a197eabfcf2fc1c59cd6acf73f4e9445a7a37e8dfe93e3a72ccf7a72a210'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue43-ready-runner-consumer-maintenance/source/material1/supervisor-release.json', 'sha256': 'b7460c8272b604dee5381b801e656112d64792c1e58171a111cd96e4727ef8c0'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue43-ready-runner-consumer-maintenance/source/material1/collection_ready.py.before', 'sha256': 'b29afb3b7dfadcc7876e131863ff77709678e137e8a9dc6aad12b4ca1e72e10a'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/ready-pinned-external-runner-consumer-candidate/collection_ready.py', 'sha256': 'cbcf703774e1f53255b1bf8dc55f1983f61c9d18af8226b7513a5195bb7a9e5d'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 4, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'cbcf703774e1f53255b1bf8dc55f1983f61c9d18af8226b7513a5195bb7a9e5d'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '2d04cee466afceb4cfb8507cfdede52f3883121c3c3c5ac4b666eb3787656e29'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/cbcf703774e1f53255b1bf8dc55f1983f61c9d18af8226b7513a5195bb7a9e5d.json', 'sha256': '89b32fbae0ed6ed57633af99c45910c5e6dc36e09949514558b8028024ff620f'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue45-violation2-typed-origin-maintenance/source/material1/supervisor-release.json', 'sha256': '6f1f4770c6b194b8acab226159f64c909d75fa5872f15f7499ba4454bf03b563'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue45-violation2-typed-origin-maintenance/source/material1/collection_ready.py.before', 'sha256': 'cbcf703774e1f53255b1bf8dc55f1983f61c9d18af8226b7513a5195bb7a9e5d'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-typed-dom-preengine-candidate/snapshot-v1/collection_ready.py', 'sha256': '2d04cee466afceb4cfb8507cfdede52f3883121c3c3c5ac4b666eb3787656e29'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 5, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '2d04cee466afceb4cfb8507cfdede52f3883121c3c3c5ac4b666eb3787656e29'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'f5c6b1195fd7fdc519698ecb06725e0a6b8b374171c97a985ef82a74498d22aa'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/2d04cee466afceb4cfb8507cfdede52f3883121c3c3c5ac4b666eb3787656e29.json', 'sha256': '01d5625601d914cfba4f05cb129a8fe8c37dfe53da7c67d61f1b63973acc0750'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue46-violation-local-plan-maintenance/source/material1/supervisor-release.json', 'sha256': '6bfa694f2c9d69d17faf88f1ef07de43628e55ea80db99163dbc886c23f141e1'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue46-violation-local-plan-maintenance/source/material1/collection_ready.py.before', 'sha256': '2d04cee466afceb4cfb8507cfdede52f3883121c3c3c5ac4b666eb3787656e29'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-local-plan-dom-context-candidate/snapshot-v1/collection_ready.py', 'sha256': 'f5c6b1195fd7fdc519698ecb06725e0a6b8b374171c97a985ef82a74498d22aa'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 6, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'f5c6b1195fd7fdc519698ecb06725e0a6b8b374171c97a985ef82a74498d22aa'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '2d01b2d1db9ed95085f015ddc35926bf2276eb31c74f6eb2d91c678dfafc8a4e'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/f5c6b1195fd7fdc519698ecb06725e0a6b8b374171c97a985ef82a74498d22aa.json', 'sha256': '854ae99ddb8484083f30e97950802fc586fd2a2577661cba4e8b4479ad828584'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue47-violation-navigation-contract-maintenance/source/material2/supervisor-release.json', 'sha256': '19f6bc02276c299d44acf84da0a167ea272ffab056b1dfe4d49f2d486da028c8'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue47-violation-navigation-contract-maintenance/source/material2/collection_ready.py.before', 'sha256': 'f5c6b1195fd7fdc519698ecb06725e0a6b8b374171c97a985ef82a74498d22aa'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-navigation-read-contract-candidate/snapshot-v1/collection_ready.py', 'sha256': '2d01b2d1db9ed95085f015ddc35926bf2276eb31c74f6eb2d91c678dfafc8a4e'}, 'mode': 420, 'target_count': 2, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/switch_read_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 7, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '2d01b2d1db9ed95085f015ddc35926bf2276eb31c74f6eb2d91c678dfafc8a4e'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '3148edafbc9bcdc2c81aa54ba951aede4c4bdeb33ff7e9fe619ff0930a390450'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/2d01b2d1db9ed95085f015ddc35926bf2276eb31c74f6eb2d91c678dfafc8a4e.json', 'sha256': '02617930dfab4b95f3425bc89060d0d8a6e59c388992ac69b713bcc0c3355d61'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue48-violation-layout-build-maintenance/source/material1/supervisor-release.json', 'sha256': '4866904bd156187d1e5f1516233b637a2606c3ceac3ff4373519ec9ce01a0c75'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue48-violation-layout-build-maintenance/source/material1/collection_ready.py.before', 'sha256': '2d01b2d1db9ed95085f015ddc35926bf2276eb31c74f6eb2d91c678dfafc8a4e'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-layout-build-successor-candidate/snapshot-v1/collection_ready.py', 'sha256': '3148edafbc9bcdc2c81aa54ba951aede4c4bdeb33ff7e9fe619ff0930a390450'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 8, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '3148edafbc9bcdc2c81aa54ba951aede4c4bdeb33ff7e9fe619ff0930a390450'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '9c375de60ad26e767fd84cfe08d3d4496891baf7c41ba170fa90ecdf56b95e27'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/3148edafbc9bcdc2c81aa54ba951aede4c4bdeb33ff7e9fe619ff0930a390450.json', 'sha256': '7608ff312746d6bc0dc0557a256fe6fac2d75ed43f47465cffae8d4ff0525f29'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue49-violation-analysis-anchor-maintenance/source/material1/supervisor-release.json', 'sha256': 'f5f18a42ec9c07c6d1e6bb61543d882878d3c85623eaf7b92748676c939bef9e'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue49-violation-analysis-anchor-maintenance/source/material1/collection_ready.py.before', 'sha256': '3148edafbc9bcdc2c81aa54ba951aede4c4bdeb33ff7e9fe619ff0930a390450'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-analysis-wait-anchor-candidate/snapshot-v2/collection_ready.py', 'sha256': '9c375de60ad26e767fd84cfe08d3d4496891baf7c41ba170fa90ecdf56b95e27'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 9, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '9c375de60ad26e767fd84cfe08d3d4496891baf7c41ba170fa90ecdf56b95e27'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '9dce91edd57d237bdd8bdeaeb1546e4cab02f7301d268bdba3f2bfd155c613a6'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/9c375de60ad26e767fd84cfe08d3d4496891baf7c41ba170fa90ecdf56b95e27.json', 'sha256': '643796d9b1cd65d48513e9caf74ca236e5c260b94edb92a5efb995e4c46783d7'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue50-violation-source-reference-maintenance/source/material1/supervisor-release.json', 'sha256': '637a35a4deeaeca43078f3d6832f5e87219365ff44882ae8384ee94f1eb0898e'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue50-violation-source-reference-maintenance/source/material1/collection_ready.py.before', 'sha256': '9c375de60ad26e767fd84cfe08d3d4496891baf7c41ba170fa90ecdf56b95e27'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-pinned-reference-boundary-candidate/snapshot-v1/collection_ready.py', 'sha256': '9dce91edd57d237bdd8bdeaeb1546e4cab02f7301d268bdba3f2bfd155c613a6'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 10, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '9dce91edd57d237bdd8bdeaeb1546e4cab02f7301d268bdba3f2bfd155c613a6'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'e593c38a9fefa3b6e6aa5738670f50e54b48c686a2ff6a0cd9ae7a2da1a8187f'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/9dce91edd57d237bdd8bdeaeb1546e4cab02f7301d268bdba3f2bfd155c613a6.json', 'sha256': 'd22f10b1fa166249e773b9933c2eab5ba0b03a407e675fa40eda3168fa2faaf7'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue51-publication-draft/source/material3/supervisor-release.json', 'sha256': '8daf9fdaf4a84165b0089f129c05a580470d62d5686dce02301b00b116f625cb'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue51-publication-draft/source/material3/collection_ready.py.before', 'sha256': '9dce91edd57d237bdd8bdeaeb1546e4cab02f7301d268bdba3f2bfd155c613a6'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/violation-governance-entry-history-combined-candidate/snapshot-v5/collection_ready.py', 'sha256': 'e593c38a9fefa3b6e6aa5738670f50e54b48c686a2ff6a0cd9ae7a2da1a8187f'}, 'mode': 420, 'target_count': 3, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/company_configuration.py']}, {'index': 11, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'e593c38a9fefa3b6e6aa5738670f50e54b48c686a2ff6a0cd9ae7a2da1a8187f'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '83969c8443426090a11453a13a73ef694fd5e74deb1bf44d14fc81bfb8758fcc'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/e593c38a9fefa3b6e6aa5738670f50e54b48c686a2ff6a0cd9ae7a2da1a8187f.json', 'sha256': '58affdbdf51be416c13846af1bbd1dd418330c834d800e1d0b014e3f0a71fe3a'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue53-bridge-generation-maintenance/source/material1/supervisor-release.json', 'sha256': 'd1207e681df4431d298690b79fecbf1b6fb6ba345e75fb57bedf789657bdeb28'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue53-bridge-generation-maintenance/source/material1/collection_ready.py.before', 'sha256': 'e593c38a9fefa3b6e6aa5738670f50e54b48c686a2ff6a0cd9ae7a2da1a8187f'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-preenqueue-source-successor-candidate/snapshot-v2/collection_ready.py', 'sha256': '83969c8443426090a11453a13a73ef694fd5e74deb1bf44d14fc81bfb8758fcc'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 12, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '83969c8443426090a11453a13a73ef694fd5e74deb1bf44d14fc81bfb8758fcc'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '5035c0caac3dbdedd8dc22928848bdf07788538a85000fc06db118157a02b0d3'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/83969c8443426090a11453a13a73ef694fd5e74deb1bf44d14fc81bfb8758fcc.json', 'sha256': '73823f994383f983c00eca66a8393a5d2356af349984aa727736d11661f1dada'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue55-source-maintenance/source/material2/supervisor-release.json', 'sha256': 'f938ecb99575d9d84318358448565b5d89dd59e4aeac6266ff02c39e8f5df04f'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue55-source-maintenance/source/material2/collection_ready.py.before', 'sha256': '83969c8443426090a11453a13a73ef694fd5e74deb1bf44d14fc81bfb8758fcc'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-review-route-restoration-candidate/snapshot-final/collection_ready.py', 'sha256': '5035c0caac3dbdedd8dc22928848bdf07788538a85000fc06db118157a02b0d3'}, 'mode': 420, 'target_count': 2, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 13, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '5035c0caac3dbdedd8dc22928848bdf07788538a85000fc06db118157a02b0d3'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '28f35693ec7f81b7acfc5ff5d0d3b686d5ddd5e274ed241bdbe207dc29c2603c'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/5035c0caac3dbdedd8dc22928848bdf07788538a85000fc06db118157a02b0d3.json', 'sha256': '330f227f38d732a1f52c5ac02ff225e40bbebc608492440201df3ae45a9475b1'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue56-source-maintenance/source/material1/supervisor-release.json', 'sha256': '59f9a42faac8e79acba5119337c6661a77a93d09ac28c617a576f889ae070bd7'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue56-source-maintenance/source/material1/collection_ready.py.before', 'sha256': '5035c0caac3dbdedd8dc22928848bdf07788538a85000fc06db118157a02b0d3'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-detail-subject-object-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': '28f35693ec7f81b7acfc5ff5d0d3b686d5ddd5e274ed241bdbe207dc29c2603c'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 14, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '28f35693ec7f81b7acfc5ff5d0d3b686d5ddd5e274ed241bdbe207dc29c2603c'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'fd16d9d1cd1238f7bb3bab492eb2be8f16d900a358378f156b8c06603f36df21'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/28f35693ec7f81b7acfc5ff5d0d3b686d5ddd5e274ed241bdbe207dc29c2603c.json', 'sha256': 'b801a7dfcfe14ad063ce6dd666539777da79b14656c7024703ff423ddea28f77'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue57-source-maintenance/source/material1/supervisor-release.json', 'sha256': '073c307b7b63ea01be8df784055e70f76ae2c0873c120bebb012cad6961d4ede'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue57-source-maintenance/source/material1/collection_ready.py.before', 'sha256': '28f35693ec7f81b7acfc5ff5d0d3b686d5ddd5e274ed241bdbe207dc29c2603c'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-stop-auto-template-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': 'fd16d9d1cd1238f7bb3bab492eb2be8f16d900a358378f156b8c06603f36df21'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 15, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'fd16d9d1cd1238f7bb3bab492eb2be8f16d900a358378f156b8c06603f36df21'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'c146f67e9e357610c0649b10b26238a7607bda5f6296c4da341ec0aa833cda29'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/fd16d9d1cd1238f7bb3bab492eb2be8f16d900a358378f156b8c06603f36df21.json', 'sha256': 'bf8ab385b2ee641578271cf43fddecc04b030aab5ba44ae856d3d9a5f8c09d8d'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue58-source-maintenance/source/material1/supervisor-release.json', 'sha256': 'd182de2926ac5e25696936420c1560eb5b290a76e88640b32441eb8339fb5e5e'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue58-source-maintenance/source/material1/collection_ready.py.before', 'sha256': 'fd16d9d1cd1238f7bb3bab492eb2be8f16d900a358378f156b8c06603f36df21'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-anchor-advice-frame-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': 'c146f67e9e357610c0649b10b26238a7607bda5f6296c4da341ec0aa833cda29'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 16, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'c146f67e9e357610c0649b10b26238a7607bda5f6296c4da341ec0aa833cda29'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'cd51e44f5cdb30eebc175be98d95b99f810f282fbc43b39bfe0483ec427000fb'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/c146f67e9e357610c0649b10b26238a7607bda5f6296c4da341ec0aa833cda29.json', 'sha256': '8bc7d8541eb91cff702e84e80707dbc5a3c5234aefa2e74a8a6806c25f638430'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue59-source-maintenance/source/material1/supervisor-release.json', 'sha256': '649fbd9aee3387f8ea06484141799fbd077fbefb0ed7438fe07ef2957db0a522'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue59-source-maintenance/source/material1/collection_ready.py.before', 'sha256': 'c146f67e9e357610c0649b10b26238a7607bda5f6296c4da341ec0aa833cda29'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-anchor-guard-route-source-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': 'cd51e44f5cdb30eebc175be98d95b99f810f282fbc43b39bfe0483ec427000fb'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 17, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'cd51e44f5cdb30eebc175be98d95b99f810f282fbc43b39bfe0483ec427000fb'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '7bbf455c226326ee7fa7f97a88667908ab14c28b55a44070a96c309cf5d31bb4'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/cd51e44f5cdb30eebc175be98d95b99f810f282fbc43b39bfe0483ec427000fb.json', 'sha256': 'cae0e2d8d6f7ba5c0eed5c2a4cb731752d9d8176852fd98ed5aca96f2a3d500c'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue60-source-maintenance/source/material1/supervisor-release.json', 'sha256': 'a0e18d0dfb38eae875e623ddeeb360b4b3ef3d931584947c6d74cfaa47ef3ae4'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue60-source-maintenance/source/material1/collection_ready.py.before', 'sha256': 'cd51e44f5cdb30eebc175be98d95b99f810f282fbc43b39bfe0483ec427000fb'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-noaccept-rate-template-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': '7bbf455c226326ee7fa7f97a88667908ab14c28b55a44070a96c309cf5d31bb4'}, 'mode': 420, 'target_count': 1, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'index': 18, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '7bbf455c226326ee7fa7f97a88667908ab14c28b55a44070a96c309cf5d31bb4'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'baf08c5a849fceaf4019d6ea493851011d7749503ff49ea190517f98c22d9849'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/7bbf455c226326ee7fa7f97a88667908ab14c28b55a44070a96c309cf5d31bb4.json', 'sha256': 'b0060d5c9843b3bbd8fbfded6bec124e905b5d806aedbb4220345ac171a51853'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue61-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': '50fc581f614db83e39544063bf5cb44f44e1a5b63d21ea539253ddd05030fb2d'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue61-source-maintenance-draft/source/material2/collection_ready.py.before', 'sha256': '7bbf455c226326ee7fa7f97a88667908ab14c28b55a44070a96c309cf5d31bb4'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-noaccept-warning-template-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': 'baf08c5a849fceaf4019d6ea493851011d7749503ff49ea190517f98c22d9849'}, 'mode': 420, 'target_count': 2, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'index': 19, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': 'baf08c5a849fceaf4019d6ea493851011d7749503ff49ea190517f98c22d9849'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '3e2555c1cfbc6601f29e033f47d2c16bb196743c3cfada9f2086f05ce46e5e8c'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/baf08c5a849fceaf4019d6ea493851011d7749503ff49ea190517f98c22d9849.json', 'sha256': 'f6d60238e18f527bead13a465728c84ed2fd1bea0bda21736b29f762a4af545b'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue62-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': 'f85819d7792cb0efbcf1071208f2c00f331c0e58976aa92d1c553e0c2cc06630'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue62-source-maintenance-draft/source/material2/collection_ready.py.before', 'sha256': 'baf08c5a849fceaf4019d6ea493851011d7749503ff49ea190517f98c22d9849'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-sixth-rate-template-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': '3e2555c1cfbc6601f29e033f47d2c16bb196743c3cfada9f2086f05ce46e5e8c'}, 'mode': 420, 'target_count': 2, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'index': 20, 'from': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '3e2555c1cfbc6601f29e033f47d2c16bb196743c3cfada9f2086f05ce46e5e8c'}, 'to': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', 'sha256': '39abaac92298a03701322cee6b4b62cd70c16cd132d6b2ee5b592cf718bebde8'}, 'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/3e2555c1cfbc6601f29e033f47d2c16bb196743c3cfada9f2086f05ce46e5e8c.json', 'sha256': '3d928f17b7509601b9f8d8bb10c6cf2408d293cb87668892ffb16bd761662e0b'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue63-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': '51cf60c9cb087258b3d1d27299b27ef9e48db59ba0c592d7125587e83068af8d'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue63-source-maintenance-draft/source/material2/collection_ready.py.before', 'sha256': '3e2555c1cfbc6601f29e033f47d2c16bb196743c3cfada9f2086f05ce46e5e8c'}, 'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-native-region-readonly-recovery-candidate/snapshot-final/collection_ready.py', 'sha256': '39abaac92298a03701322cee6b4b62cd70c16cd132d6b2ee5b592cf718bebde8'}, 'mode': 420, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}]
_ROLE_READY_ENDPOINTS=['d4c9da5b61284f2250875314e199f17d8525dc6a2a71bff28808cca67e4067c6', 'c31e973466e6d1d953101ca5531de6e3c0620fc80c5e3c06a39361a8a9938885', 'a4cad5c28b3267311c4745707e1a5f098b9da01c9d6d392bf8916d64198983ca', 'f578eee67e3fbc9119494d2bbd2d04551f0ebffa999e79cef3dd57ada2effeab', '8c8f682a4b5d9f39020ea66d7300bf6cab5ac92687f7b35971bca211ec0050ae']
_ROLE_DELIVERY_MATERIAL={'path':str(o.PROJECT/'work/performance-audit/unified-reminder-source-guard-candidate/SOURCE-MATERIALS.json'),'sha256':'d5bd32d722a0da6bb01e39d72dc2acca36205fae7d10ec840084862a625dcb42'}

def _reviewed_ready_prefix_source(reference):
    import execution_timing as timing
    heads=[step['from']for step in _ROLE_READY_PREFIX];o.need(reference in heads,'role-ready-exact-reviewed-head');path=o.PROJECT/'skills/workshop-director/scripts/collection_ready.py';o.need(reference['path']==str(path),'role-ready-exact-path');live=o.ref(path);o.need(live['sha256']in _ROLE_READY_ENDPOINTS and path.stat().st_mode&0o777==0o644,'role-ready-exact-reviewed-current');cursor=dict(reference);seen=set();dependencies=[];material=None
    for step in _ROLE_READY_PREFIX[heads.index(reference):]:
        o.need(cursor==step['from']and cursor['sha256']not in seen,'role-ready-prefix-cursor-cycle');seen.add(cursor['sha256']);link=o.doc(step['link']);o.need(link=={'kind':'reviewed-configuration-code-successor-link-v1','release':step['release']}and step['link']['path']==str(o.PROJECT/'skills/workshop-director/references/configuration-source-successors'/(cursor['sha256']+'.json')),'role-ready-exact-prefix-link');release=o.doc(step['release']);targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and 1<=len(targets)<=4 and [t['target']for t in targets]==step['target_paths'],'role-ready-exact-prefix-release');row=next(t for t in targets if t['target']==str(path));o.need(row=={'target':str(path),'before':step['before'],'after':step['after'],'old_sha256':cursor['sha256'],'mode':420}and step['mode']==420 and step['before']['sha256']==cursor['sha256']and step['to']=={'path':str(path),'sha256':step['after']['sha256']},'role-ready-exact-prefix-transition');o.raw(step['before']);o.raw(step['after']);material=material or step['before'];dependencies.extend([step['link'],step['release'],step['before'],step['after']]);cursor=step['to']
    o.need(cursor==_ROLE_READY_PREFIX[-1]['to'],'role-ready-fixed-checkpoint');tail=timing.configuration_source_material(cursor);o.need(tail['historical']==cursor and tail['current']==live,'role-ready-tail-endpoint');tail_heads=[Path(r['path']).stem for r in tail['dependencies']if Path(r['path']).parent==o.PROJECT/'skills/workshop-director/references/configuration-source-successors'];o.need(len(tail_heads)==len(set(tail_heads))and not(set(tail_heads)&seen)and live['sha256']not in seen,'role-ready-cross-segment-cycle');return {'historical':reference,'current':live,'material':material,'dependencies':[ *dependencies,tail['material'],*tail['dependencies']]}

def _reviewed_delivery_source(reference):
    value=o.doc(_ROLE_DELIVERY_MATERIAL);freeze=o.doc(value['freeze']);paths={str(o.PROJECT/'skills/workshop-director/scripts'/n)for n in('delivery_commit.py','unified_review_format.py')};o.need(value['kind']=='reviewed-unified-delivery-two-source-frozen-materials-v1'and value['published']is False and value['freeze']['sha256']=='e2c43e89e77d76ef8f685868d9a0828aa2a755635b914caf8a966cb7a401003f'and len(value['targets'])==2 and {t['target']for t in value['targets']}==paths,'role-delivery-reviewed-two-source-materials');rows=[t for t in value['targets']if t['target']==reference['path']];o.need(len(rows)==1,'role-delivery-exact-source-slot');row=rows[0];f=next(t for t in freeze['targets']if t['target']==reference['path']);o.need(row['original']==reference and row['before_archive']['sha256']==reference['sha256']and f=={'target':reference['path'],'before':reference,'payload':row['payload'],'mode':420}and row['mode']==420,'role-delivery-exact-before-and-frozen-payload');o.raw(row['before_archive']);o.raw(row['payload']);path=Path(reference['path']);current=o.ref(path);o.need(current=={'path':reference['path'],'sha256':row['payload']['sha256']}and path.stat().st_mode&0o777==0o644,'role-delivery-actual-installed-payload');o.raw(current);return {'historical':reference,'current':current,'material':row['before_archive'],'dependencies':[_ROLE_DELIVERY_MATERIAL,value['freeze'],row['before_archive'],row['payload'],current]}

def _reviewed_helper_prefix_source():
 import execution_timing as timing
 steps=[{'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/6b3342d86602f1b4f03e70c83bd854eeb862566cb0fc15f25340815d933ce80e.json', 'sha256': 'c4590a2f0b6469949b08e97bb2f0282a10babc2d2499b8438bf0413acf7f3dd2'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue31-command-history-performance-maintenance/source/material3/supervisor-release.json', 'sha256': 'a29e9375c679eec84d0de8f155f007a784f076fc9855ef11fdc3825e421b4007'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/daily-ready-command-history-sharing-v3-closure-candidate/initial_ledger_recovery.py', 'sha256': '289abc048da392062e65c284d2bc33eead2596b0a0ed7771b4fe352a4dc6af9b'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue31-command-history-performance-maintenance/source/material3/initial_ledger_recovery.py.before', 'sha256': '6b3342d86602f1b4f03e70c83bd854eeb862566cb0fc15f25340815d933ce80e'}, 'mode': 420, 'old_sha256': '6b3342d86602f1b4f03e70c83bd854eeb862566cb0fc15f25340815d933ce80e', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/289abc048da392062e65c284d2bc33eead2596b0a0ed7771b4fe352a4dc6af9b.json', 'sha256': '8c7c85eb6abceac6bd3919779f4c0976689ab8ac141e2117c82c81858e7fc467'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue33-normal-filter-recovery-maintenance/source/material3/supervisor-release.json', 'sha256': 'f3604445baa269a8ac7354ed5ca924315f0ad1e8d26923b40a4a67d16b3b2dcc'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-normal-filter-bounded-recovery-candidate/snapshot-v4/initial_ledger_recovery.py', 'sha256': '0c87aee86e69ce99fa85ee0fd349eaa311e07665d3f490280b6097a7d3e1750b'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue33-normal-filter-recovery-maintenance/source/material3/initial_ledger_recovery.py.before', 'sha256': '289abc048da392062e65c284d2bc33eead2596b0a0ed7771b4fe352a4dc6af9b'}, 'mode': 420, 'old_sha256': '289abc048da392062e65c284d2bc33eead2596b0a0ed7771b4fe352a4dc6af9b', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/0c87aee86e69ce99fa85ee0fd349eaa311e07665d3f490280b6097a7d3e1750b.json', 'sha256': 'e82c55683daa4812b20272284b2978b298187f25093721d81724969224e72285'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue34-record-tab-recovery-maintenance/source/material2/supervisor-release.json', 'sha256': 'f2834f1ccf6e64e7bee713fef9d616dbf2fecc458f94b96734be0a014686be6e'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/equivalent-existing-record-tab-candidate/snapshot-v2/initial_ledger_recovery.py', 'sha256': 'e85d2a5a8b58524509579a1c0c33a97cf5ffe259ebf4598c2d0d35fdf13102c0'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue34-record-tab-recovery-maintenance/source/material2/initial_ledger_recovery.py.before', 'sha256': '0c87aee86e69ce99fa85ee0fd349eaa311e07665d3f490280b6097a7d3e1750b'}, 'mode': 420, 'old_sha256': '0c87aee86e69ce99fa85ee0fd349eaa311e07665d3f490280b6097a7d3e1750b', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/e85d2a5a8b58524509579a1c0c33a97cf5ffe259ebf4598c2d0d35fdf13102c0.json', 'sha256': '32f64075a5e1926fd0960c1a966c17bd5473805daac726bb84abbd53b45a1120'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue35-command-generation-maintenance/source/material2/supervisor-release.json', 'sha256': '059c7c67e8e3c4f52ddc6b144783ff359c6016d10c1c92882edaac949640eca5'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/configured-company-single-generation-loader-candidate/snapshot-v2/initial_ledger_recovery.py', 'sha256': '6b8f4e0ab4aaf3c31c44250e3c42057b0ccffa224094d3807008bceea23a96fe'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue35-command-generation-maintenance/source/material2/initial_ledger_recovery.py.before', 'sha256': 'e85d2a5a8b58524509579a1c0c33a97cf5ffe259ebf4598c2d0d35fdf13102c0'}, 'mode': 420, 'old_sha256': 'e85d2a5a8b58524509579a1c0c33a97cf5ffe259ebf4598c2d0d35fdf13102c0', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/bridge-workflow.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/6b8f4e0ab4aaf3c31c44250e3c42057b0ccffa224094d3807008bceea23a96fe.json', 'sha256': '9fb9915855e71686878d385b2eb9a8cdef1fc74eee7cc7b42906aae3a9971662'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue36-review-page-origin-maintenance/source/material3/supervisor-release.json', 'sha256': '917e823cb44314ef258794011723dbb3d8e7b40ce92f88643882c5434d564ad7'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/equivalent-record-prestate-review-focus-candidate/snapshot-v3/initial_ledger_recovery.py', 'sha256': 'a72fa9c16ccbe2f0bc97697e69cc5122e8ba94b5d01a4ebfd6a856c3ff2bfe94'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue36-review-page-origin-maintenance/source/material3/initial_ledger_recovery.py.before', 'sha256': '6b8f4e0ab4aaf3c31c44250e3c42057b0ccffa224094d3807008bceea23a96fe'}, 'mode': 420, 'old_sha256': '6b8f4e0ab4aaf3c31c44250e3c42057b0ccffa224094d3807008bceea23a96fe', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/review_capture_tab.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/a72fa9c16ccbe2f0bc97697e69cc5122e8ba94b5d01a4ebfd6a856c3ff2bfe94.json', 'sha256': '880adcc66ec74daf01bb5a10a1c64ec78b83eeb2730af715110c564f6a85d93b'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue38-capture-window-hold-maintenance/source/material1/supervisor-release.json', 'sha256': '00245b2bf9c8100d8db84d71296f8a2e6681caa9ba9d141a0c3e9a363729c4e1'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/capture-window-existing-readonly-settlement-candidate/snapshot-v2/initial_ledger_recovery.py', 'sha256': '52e1d0a5f3c796704f290dd714d83d379567301645bc7fc678f6bacbd5f81a3c'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue38-capture-window-hold-maintenance/source/material1/initial_ledger_recovery.py.before', 'sha256': 'a72fa9c16ccbe2f0bc97697e69cc5122e8ba94b5d01a4ebfd6a856c3ff2bfe94'}, 'mode': 420, 'old_sha256': 'a72fa9c16ccbe2f0bc97697e69cc5122e8ba94b5d01a4ebfd6a856c3ff2bfe94', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/52e1d0a5f3c796704f290dd714d83d379567301645bc7fc678f6bacbd5f81a3c.json', 'sha256': '403d5f93290fa7dc5d202b6f4386c70fdb1dbf6d181ead72fc9b114266a4fab3'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue40-typed-rapid-quality-maintenance/source/material3/supervisor-release.json', 'sha256': 'de56f279ba5af0e14ab550007466d8f6f66d7c81a2aca14cafd94bcbf7187988'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/typed-local-rapidocr-quality-fallback-candidate/snapshot-v2/initial_ledger_recovery.py', 'sha256': '1958287e14dcbe1927c56e79e458be034679b275e9ac320df9f8bb6fc2e1b3e7'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-28/round009-issue40-typed-rapid-quality-maintenance/source/material3/initial_ledger_recovery.py.before', 'sha256': '52e1d0a5f3c796704f290dd714d83d379567301645bc7fc678f6bacbd5f81a3c'}, 'mode': 420, 'old_sha256': '52e1d0a5f3c796704f290dd714d83d379567301645bc7fc678f6bacbd5f81a3c', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/program_review_quality.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/1958287e14dcbe1927c56e79e458be034679b275e9ac320df9f8bb6fc2e1b3e7.json', 'sha256': 'b0060d5c9843b3bbd8fbfded6bec124e905b5d806aedbb4220345ac171a51853'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue61-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': '50fc581f614db83e39544063bf5cb44f44e1a5b63d21ea539253ddd05030fb2d'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-noaccept-warning-template-recovery-candidate/snapshot-final/initial_ledger_recovery.py', 'sha256': '44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue61-source-maintenance-draft/source/material2/initial_ledger_recovery.py.before', 'sha256': '1958287e14dcbe1927c56e79e458be034679b275e9ac320df9f8bb6fc2e1b3e7'}, 'mode': 420, 'old_sha256': '1958287e14dcbe1927c56e79e458be034679b275e9ac320df9f8bb6fc2e1b3e7', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c.json', 'sha256': 'f6d60238e18f527bead13a465728c84ed2fd1bea0bda21736b29f762a4af545b'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue62-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': 'f85819d7792cb0efbcf1071208f2c00f331c0e58976aa92d1c553e0c2cc06630'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-sixth-rate-template-recovery-candidate/snapshot-final/initial_ledger_recovery.py', 'sha256': '21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue62-source-maintenance-draft/source/material2/initial_ledger_recovery.py.before', 'sha256': '44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c'}, 'mode': 420, 'old_sha256': '44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}, {'link': {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/references/configuration-source-successors/21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10.json', 'sha256': '3d928f17b7509601b9f8d8bb10c6cf2408d293cb87668892ffb16bd761662e0b'}, 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue63-source-maintenance-draft/source/material2/supervisor-release.json', 'sha256': '51cf60c9cb087258b3d1d27299b27ef9e48db59ba0c592d7125587e83068af8d'}, 'target': {'after': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-native-region-readonly-recovery-candidate/snapshot-final/initial_ledger_recovery.py', 'sha256': 'f26701406ed6d8fa07276de4b77a00c9610a77cf6549a266e781bdf2e635133d'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue63-source-maintenance-draft/source/material2/initial_ledger_recovery.py.before', 'sha256': '21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10'}, 'mode': 420, 'old_sha256': '21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10', 'target': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py'}, 'target_paths': ['/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/collection_ready.py', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/initial_ledger_recovery.py']}]
 reference={'path':str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'6b3342d86602f1b4f03e70c83bd854eeb862566cb0fc15f25340815d933ce80e'};cursor=dict(reference);seen=set();dependencies=[];material=None
 for step in steps:
  o.need(cursor['sha256']not in seen,'ready-helper-prefix-cycle');seen.add(cursor['sha256']);link=o.doc(step['link']);o.need(link=={'kind':'reviewed-configuration-code-successor-link-v1','release':step['release']}and step['link']['path']==str(o.PROJECT/'skills/workshop-director/references/configuration-source-successors'/(cursor['sha256']+'.json')),'ready-helper-exact-prefix-link');release=o.doc(step['release']);o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and[t['target']for t in release['targets']]==step['target_paths'],'ready-helper-exact-prefix-release');row=next(t for t in release['targets']if t['target']==reference['path']);o.need(row==step['target']and row['old_sha256']==row['before']['sha256']==cursor['sha256']and row['mode']==420,'ready-helper-exact-prefix-transition');o.raw(row['before']);o.raw(row['after']);material=material or row['before'];dependencies.extend([step['link'],step['release'],row['before'],row['after']]);cursor={'path':reference['path'],'sha256':row['after']['sha256']}
 tail=timing.configuration_source_material(cursor);o.need(tail['historical']==cursor and tail['current']['path']==reference['path']and tail['current']['sha256']not in seen,'ready-helper-strict-tail');heads=[Path(r['path']).stem for r in tail['dependencies']if Path(r['path']).parent==o.PROJECT/'skills/workshop-director/references/configuration-source-successors'];o.need(not(set(heads)&seen)and len(heads)==len(set(heads)),'ready-helper-cross-segment-cycle');return{'historical':reference,'current':tail['current'],'material':material,'dependencies':[*dependencies,tail['material'],*tail['dependencies']]}

_ROLE_NATIVE_MATERIAL={'path':str(o.PROJECT/'work/performance-audit/native-region-application-role-candidate/CONTRACT.json'),'sha256':'1d81eae5fc6ab8d4c20f280917d7edc547fa0a7ed5bbe61fce2da370c73bceb5'}
def _reviewed_native_region_source(reference):
 value=o.doc(_ROLE_NATIVE_MATERIAL);path=o.PROJECT/'skills/chrome-dom-export/scripts/native_region_capture.py';o.need(value['kind']=='W63-native-application-role-source-subpackage-v1'and value['no_original_slot_added']is True and len(value['targets'])==1,'role-native-exact-reviewed-subpackage');row=value['targets'][0];material=value['source_material'];o.need(reference=={'path':str(path),'sha256':'18342b30ff5569c0dc945b056a5791a0037415c98bb9707aa71b5811029f363c'}and row['target']==material['target']==str(path)and row['before']==reference and row['mode']==420 and material['before_archive']['sha256']==reference['sha256']and material['after']==row['payload']and row['payload']['sha256']=='caf681fcc786b03f75c287f19e31ddaa37b256d55bbfc58e9389013ef82235e1','role-native-exact-before-payload');o.raw(material['before_archive']);o.raw(row['payload']);current=o.ref(path);o.need(current=={'path':str(path),'sha256':row['payload']['sha256']}and path.stat().st_mode&0o777==420,'role-native-current-payload');o.raw(current);return{'historical':reference,'current':current,'material':material['before_archive'],'dependencies':[_ROLE_NATIVE_MATERIAL,material['before_archive'],row['payload'],current]}

_ROLE_WAITING_ADAPTER_MATERIAL={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/task8-rows-object-fragment-waiting-candidate/ADAPTER-SOURCE-MATERIAL.json', 'sha256': '9662cb5e077024080aef97ab479806101171345102b5bc337494e869d164339a'}

def _reviewed_waiting_adapter_source(reference):
 value=o.doc(_ROLE_WAITING_ADAPTER_MATERIAL);path=o.PROJECT/'packages/workshop-director/workshop_director/adapters.py';o.need(value['kind']=='W66-exact-waiting-context-adapter-source-material-v1'and value['target']==str(path)and value['mode']==420 and value['no_original_slot_added']is True and value['not_an_installed_release']is True and value['installation_requires_exact_current_payload']is True,'role-waiting-adapter-exact-material');o.need(reference=={'path':str(path),'sha256':'88476dd62c851f8a2fcf57dac227ce089274389163ba99ae15ef5c8e542cac6c'}and value['before']['sha256']==reference['sha256'],'role-waiting-adapter-exact-before');o.raw(value['before']);o.raw(value['after']);o.raw(value['source_membership']);current=o.ref(path);o.need(current=={'path':str(path),'sha256':value['after']['sha256']}and path.stat().st_mode&511==420,'role-waiting-adapter-installed-current');o.raw(current);return {'historical':reference,'current':current,'material':value['before'],'dependencies':[_ROLE_WAITING_ADAPTER_MATERIAL,value['before'],value['after'],value['source_membership'],current]}

_ROLE_W68_BUSINESS={'path':str(o.PROJECT/'work/performance-audit/sixth-row-fractional-auto-clip-candidate/CONTRACT-v4.json'),'sha256':'18db7bb722c8a6454c7b5f6ddd111149139048308ef3c0cf4d715ba9651ae1e9'}
def _reviewed_w68_business_source(reference):
 value=o.doc(_ROLE_W68_BUSINESS);o.need(value['kind']=='W68-fractional-auto-padding-and-public-text-four-source-business-package-v2'and value['no_original_slot_added']is True and len(value['targets'])==4,'role-W68-exact-business-material');paths={str(o.PROJECT/'skills/chrome-dom-export/extension/viewport-proof.js'),*(str(o.PROJECT/'skills/chrome-dom-export/scripts'/n)for n in('business_cells_capture.py','screenshot_registration.py'))};o.need(reference['path']in paths,'role-W68-shared-three-paths');rows=[r for r in value['targets']if r['target']==reference['path']];o.need(len(rows)==1,'role-W68-unique-material');r=rows[0];o.need(r['before']['sha256']==reference['sha256']and r['mode']==420,'role-W68-exact-historical-before');o.raw(r['before']);o.raw(r['payload']);current=o.ref(Path(r['target']));o.need(current['sha256']==r['payload']['sha256']and Path(r['target']).stat().st_mode&0o777==420,'role-W68-actual-current-payload');o.raw(current);return {'historical':reference,'current':current,'material':r['before'],'dependencies':[_ROLE_W68_BUSINESS,r['before'],r['payload'],current]}

_ROLE_W68_COMPLETION={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/unified-completion-admitted-role-sources-candidate/CONTRACT.json', 'sha256': 'e6aaf5bb5b6e201ac101f6f87fd940528d09a90c8dfa33fcd725b6ae9ec3a1a7'}
def _reviewed_w68_completion_source(reference):
 value=o.doc(_ROLE_W68_COMPLETION);o.need(value['kind']=='unified-completion-admitted-role-single-source-package-v1'and value['no_original_slot_added']is True and len(value['targets'])==1,'role-W68-exact-completion-material');r=value['targets'][0];path=o.PROJECT/'skills/workshop-director/scripts/unified_delivery.py';o.need(r['target']==reference['path']==str(path)and r['before']['sha256']==reference['sha256']and r['mode']==420,'role-W68-completion-before');o.raw(r['before']);o.raw(r['payload']);current=o.ref(path);o.need(current['sha256']==r['payload']['sha256']and path.stat().st_mode&0o777==420,'role-W68-completion-current');o.raw(current);return {'historical':reference,'current':current,'material':r['before'],'dependencies':[_ROLE_W68_COMPLETION,r['before'],r['payload'],current]}
_ROLE_W96_CAPTURE_SOURCES={'path':str(o.PROJECT/'work/2026-10-31/round009-issue96-overlay-capture-succession/W96-CONTRACT.json'),'sha256':'1281af32e8c37169780cc0efb123a278b3b24ea646ff9dbf3874e8f6500c3e46'}
def _reviewed_w96_overlay_capture_sources(reference):
    value=o.doc(_ROLE_W96_CAPTURE_SOURCES);o.need(value['kind']=='W96-overlay-capture-source-succession-package-v1'and value['no_original_slot_added']is True and len(value['targets'])==2,'role-W96-exact-material')
    rows=[r for r in value['targets']if r['target']==reference['path']];o.need(len(rows)==1,'role-W96-unique-slot');r=rows[0]
    o.need(r['before']['sha256']==reference['sha256']and r['mode']==420,'role-W96-exact-historical-before');o.raw(r['before']);o.raw(r['payload'])
    current=o.ref(Path(r['target']));o.need(current['sha256']==r['payload']['sha256']and Path(r['target']).stat().st_mode&0o777==0o644,'role-W96-actual-current-payload');o.raw(current)
    return {'historical':reference,'current':current,'material':r['before'],'dependencies':[_ROLE_W96_CAPTURE_SOURCES,r['before'],r['payload'],current]}

def _historical_role_source(reference):
    if reference['path']==str(o.PROJECT/'skills/workshop-director/scripts/unified_delivery.py')and o.ref(Path(reference['path']))!=reference:return _reviewed_w68_completion_source(reference)
    import execution_timing as timing
    if reference['path']in {str(o.PROJECT/'skills/chrome-dom-export/extension/viewport-proof.js'),*(str(o.PROJECT/'skills/chrome-dom-export/scripts'/n)for n in('business_cells_capture.py','screenshot_registration.py'))}and o.ref(Path(reference['path']))!=reference:return _reviewed_w68_business_source(reference)
    if reference['path']==str(o.PROJECT/'packages/workshop-director/workshop_director/adapters.py')and o.ref(Path(reference['path']))!=reference:return _reviewed_waiting_adapter_source(reference)
    if reference=={'path':str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'6b3342d86602f1b4f03e70c83bd854eeb862566cb0fc15f25340815d933ce80e'}:return _reviewed_helper_prefix_source()
    if reference['path']==str(o.PROJECT/'skills/chrome-dom-export/scripts/native_region_capture.py')and o.ref(Path(reference['path']))!=reference:return _reviewed_native_region_source(reference)
    if reference in [step['from']for step in _ROLE_READY_PREFIX]:return _reviewed_ready_prefix_source(reference)
    if reference['path']in {str(o.PROJECT/'skills/workshop-director/scripts'/n)for n in('delivery_commit.py','unified_review_format.py')}and o.ref(Path(reference['path']))!=reference:return _reviewed_delivery_source(reference)
    if reference['path']==str(o.PROJECT/'skills/chrome-dom-export/scripts/bridge.py'):
        if o.ref(Path(reference['path']))==reference:
            o.raw(reference);return {'historical':reference,'current':reference,'material':reference,'dependencies':[]}
        return _reviewed_historical_bridge_source(reference)
    if reference['path']in {str(o.PROJECT/'skills/chrome-dom-export/extension/content.js'),str(o.PROJECT/'skills/negative-review-complaints/scripts/account_overlay_preflight.py')}and o.ref(Path(reference['path']))!=reference:return _reviewed_w96_overlay_capture_sources(reference)
    finite={str(o.PROJECT/'skills/negative-review-complaints/scripts/program_review_quality.py'),str(o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_tab.py'),str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py'),str(o.PROJECT/'skills/workshop-director/scripts/execution_timing.py'),str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),str(o.PROJECT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py'),str(o.PROJECT/'skills/douyin-laike-operator/scripts/export_record_page_recovery.py')}
    if reference['path']not in finite:
        o.raw(reference);return {'historical':reference,'current':reference,'material':reference,'dependencies':[]}
    material=timing.configuration_source_material(reference)
    o.need(material['historical']==reference,'role-source-historical-binding');o.raw(material['material']);return material

def _role_execution_sources(historical,*,installed):
    if not installed:return {'code_refs':copy.deepcopy(historical),'evidence':[]}
    codes=[];evidence=[]
    for reference in historical:
        material=_historical_role_source(reference);codes.append(material['current'])
        for dependency in [material['material'],material['current'],*material['dependencies']]:
            if dependency not in evidence:evidence.append(dependency)
    return {'code_refs':codes,'evidence':evidence}

def dom_preengine_overlay(original,release_ref,old_refs,*,installed):
    release=o.doc(release_ref);paths=set(dom_preengine_paths().values());targets=release.get('targets',[]);old={r['path']:r for r in original['code_refs']}
    o.need(release.get('kind')==DOM_PREENGINE_RELEASE and release.get('published')is True and release.get('test_projection_only')is False and len(targets)==3 and {t['target']for t in targets}==paths,'dom-preengine-reviewed-three-source-release')
    before={Path(r['path']).name:r for r in old_refs};o.need(len(old_refs)==len(before)==3 and set(before)=={n+'.before'for n in DOM_PREENGINE_NAMES},'dom-preengine-exact-old-archives')
    codes=copy.deepcopy(original['code_refs']);archives=[]
    for t in targets:
        b=before[Path(t['target']).name+'.before'];o.need(t.get('mode')=='0644'and old[t['target']]['sha256']==b['sha256']==t['old_sha256']==t['before']['sha256']and o.raw(b)==o.raw(t['before']),'dom-preengine-source-before')
        o.raw(t['after']);new={'path':t['target'],'sha256':t['after']['sha256']}
        if installed:_historical_role_source(new);o.need(Path(t['target']).stat().st_mode&0o777==0o644,'dom-preengine-source-current')
        codes[codes.index(old[t['target']])]=new;archives.append({'target':t['target'],'archive':b})
    for r in codes:
        if r['path']not in paths:_historical_role_source(r)
    return codes,archives

def plan_dom_preengine(original_ref,worker_exit_ref,release_ref,old_refs,*,installed=False):
    original=o.doc(original_ref);folder=phase_directory(original);o.need(not(folder/'engine.json').exists()and not(folder/'engine.json').is_symlink(),'dom-preengine-engine-absent');ledger_bytes(o.doc(original['order']))
    facts=_dom_preengine_facts(original_ref,worker_exit_ref,original_ref);codes,archives=dom_preengine_overlay(original,release_ref,old_refs,installed=installed)
    return {'kind':DOM_PREENGINE_KIND,'original_launcher':original_ref,'worker_exit':worker_exit_ref,'release':release_ref,'old_sources':archives,'effective_code_refs':codes,'origins':facts['origins'],'evidence':facts['evidence'],'failed_calls':original['calls'],'worker_task_id':facts['worker_task_id'],'order':original['order'],'ui_used':False}

def verify_dom_preengine(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);base=phase_directory(current)/'.dom-preengine-origin-recovery'/p['original_launcher']['sha256']
    o.need(p.get('kind')==DOM_PREENGINE_KIND and current.get(PREENGINE_FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and p['original_archive']=={'path':str(base/'original-launcher.json'),'sha256':p['original_launcher']['sha256']}and datetime.fromisoformat(p['at']).utcoffset()is not None,'dom-preengine-canonical-proof')
    o.need(all(x['archive']['path']==str(base/'sources'/(Path(x['target']).name+'.before'))for x in p['old_sources']),'dom-preengine-canonical-source-archives')
    facts=_dom_preengine_facts(p['original_launcher'],p['worker_exit'],p['original_archive']);original=facts['original'];codes,archives=dom_preengine_overlay(original,p['release'],[x['archive']for x in p['old_sources']],installed=installed)
    o.need(p['order']==original['order']and p['worker_task_id']==facts['worker_task_id']and p['origins']==facts['origins']and p['evidence']==facts['evidence']and p['failed_calls']==original['calls']and p['old_sources']==archives and p['effective_code_refs']==codes and p['ui_used']is False,'dom-preengine-derived-proof')
    expected=repaired_preengine_constructor(original,proof_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in expected.items()if k not in variable}and current['calls'][:1]==original['calls']and all(c.get('state')in('unknown','returned')for c in current['calls'][1:]),'dom-preengine-original-prefix-and-metadata')
    execution=_role_execution_sources(codes,installed=installed)
    return {'kind':DOM_PREENGINE_KIND,'code_refs':execution['code_refs'],'failed_calls':original['calls'],'evidence':[proof_ref,p['original_archive'],p['release'],*[a['archive']for a in archives],*p['evidence'],*execution['evidence']]}
_DOM_PREVIOUS_PREENGINE_VERIFY=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if o.doc(proof_ref).get('kind')==DOM_PREENGINE_KIND:return verify_dom_preengine(current,proof_ref,installed=installed)
    return _DOM_PREVIOUS_PREENGINE_VERIFY(current,proof_ref,installed=installed)

def recover_dom_preengine(original_ref,worker_exit_ref,release_ref,old_refs,*,checkpoint=lambda stage:None):
    """Caller holds resource/scheduler/coordinator/operator; owns parent lock here.
    No child or business operation is executed. Same proof-before-CAS reentry only.
    """
    import contextlib,execution_timing as timing,director
    scope=contextlib.nullcontext()if _HM_SCOPE.get()is not None else window_hold_history_scope(max_entries=16)
    with scope,timing.company_policy_command():
        path=Path(original_ref['path']);folder=path.parent;base=folder/'.dom-preengine-origin-recovery'/original_ref['sha256']
        with(folder/'launcher.lock').open('a')as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            archived=o.ref(base/'original-launcher.json')if(base/'original-launcher.json').exists()else original_ref;original=o.doc(archived);o.need(archived['sha256']==original_ref['sha256'],'dom-preengine-continuation-original')
            order=o.doc(original['order']);lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'))
            o.need(lease['dispatch_id']==order['dispatch_id']and lease['day']==order['day']and lease['phase']in('running','attention')and director.current(lease)['role']==o.ROLE,'dom-preengine-original-live-lease');o.need(not(folder/'engine.json').exists()and not(folder/'engine.json').is_symlink(),'dom-preengine-engine-absent');ledger_bytes(order)
            authority={'kind':DOM_PREENGINE_KIND,'original_launcher':original_ref,'worker_exit':worker_exit_ref,'release':release_ref,'old_refs':old_refs,'ui_used':False}
            if(base/'intent.json').exists():o.need(o.doc(o.ref(base/'intent.json'))==authority,'dom-preengine-continuation-authority')
            if(base/'proof.json').exists():
                proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_launcher']==original_ref and p['worker_exit']==worker_exit_ref and p['release']==release_ref and sorted((Path(x['archive']['path']).name,x['archive']['sha256'])for x in p['old_sources'])==sorted((Path(r['path']).name,r['sha256'])for r in old_refs),'dom-preengine-continuation-proof-authority')
            else:
                o.need(o.ref(path)==original_ref,'dom-preengine-original-cas');o.immutable(base/'intent.json',authority);archived=immutable_bytes(base/'original-launcher.json',o.raw(archived))
                facts=_dom_preengine_facts(original_ref,worker_exit_ref,archived);codes,archives=dom_preengine_overlay(original,release_ref,old_refs,installed=True)
                for a in archives:a['archive']=immutable_bytes(base/'sources'/(Path(a['target']).name+'.before'),o.raw(a['archive']))
                p={'kind':DOM_PREENGINE_KIND,'original_launcher':original_ref,'original_archive':archived,'worker_exit':worker_exit_ref,'release':release_ref,'old_sources':archives,'effective_code_refs':codes,'origins':facts['origins'],'evidence':facts['evidence'],'failed_calls':original['calls'],'worker_task_id':facts['worker_task_id'],'order':original['order'],'ui_used':False,'at':datetime.now(timezone.utc).isoformat()};proof=o.immutable(base/'proof.json',p);checkpoint('proof-published')
            expected=repaired_preengine_constructor(original,proof);current=o.doc(o.ref(path));o.need(current in(original,expected),'dom-preengine-current-third-state');verify_dom_preengine(expected,proof)
            if current==original:
                o.need(o.ref(path)==original_ref,'dom-preengine-final-before-cas');__import__('complaint_execution_launcher').save(path,expected)
            return {'kind':DOM_PREENGINE_KIND,'state':'reconciled','launcher':o.ref(path),'proof':proof,'ui_used':False}

import math

# Known readonly classification continuation. The existing reviewed DOM origin
# is inherited as immutable data, not recomputed through the daily source graph.
EXPECTED_FILTER_FIELD='expected_filter_readiness_recovery'
EXPECTED_FILTER_KIND='complaint-known-filter-readonly-ready-continuation-v1'
EXPECTED_FILTER_RELEASE='supervisor-reviewed-complaint-expected-filter-readiness-source-release-v1'
_EXPECTED_DOM_PROOF_SHA='7755616d308ef9780d575f7893c2f3fcd531a33449fa3083290a4cb85a7a4443'
_EXPECTED_DOM_RELEASE_SHA='4444294ed47d17d5a4c794784576b64cb0430cdea780856a6ea95ce01a5d65f7'
_EXPECTED_PROVIDER_OLD_SHA='7c66a662d80a24aa0b2272d6f479ebd1db7ef58ac417fd8866cc2abd67bbf8dc'
def expected_filter_paths():
    return {'initial_ledger_recovery.py':str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'collection_ready.py':str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py'),'filter_readiness_recovery.py':str(o.PROJECT/'packages/workshop-director/workshop_director/filter_readiness_recovery.py')}

@_hm_contextlib.contextmanager
def _expected_filter_provider(release):
    import importlib.util
    path=Path(expected_filter_paths()['filter_readiness_recovery.py']);target=next(t for t in release['targets']if t['target']==str(path));o.need(o.ref(path)=={'path':str(path),'sha256':target['after']['sha256']},'expected-filter-provider-generation')
    spec=importlib.util.spec_from_file_location('_complaint_expected_filter_provider',path);module=importlib.util.module_from_spec(spec);data=o.raw({'path':str(path),'sha256':target['after']['sha256']});exec(compile(data,str(path),'exec'),module.__dict__);old=sys.path[:]
    try:yield module
    finally:sys.path[:]=old

def _expected_filter_sources(parent,release_ref,old_refs,*,installed):
    release=o.doc(release_ref);previous=parent[PREENGINE_FIELD];oldproof=o.doc(previous)
    o.need(previous['sha256']==_EXPECTED_DOM_PROOF_SHA and oldproof.get('kind')==DOM_PREENGINE_KIND and oldproof['release']['sha256']==_EXPECTED_DOM_RELEASE_SHA,'expected-filter-reviewed-prior-origin')
    original=o.doc(oldproof['original_archive']);o.need(oldproof['original_archive']['sha256']==oldproof['original_launcher']['sha256']and parent['code_refs']==original['code_refs']and len(parent['code_refs'])==170,'expected-filter-original170')
    # This exact previously executed proof/release is the reviewed historical
    # authority. Recheck source materials and vector, not Shanghai DOM/XLSX.
    prior,prior_archives=dom_preengine_overlay(original,oldproof['release'],[x['archive']for x in oldproof['old_sources']],installed=False)
    o.need(prior==oldproof['effective_code_refs']and prior_archives==oldproof['old_sources']and parent['calls'][:1]==oldproof['failed_calls'],'expected-filter-prior-vector-prefix')
    expected=repaired_preengine_constructor(original,previous)
    o.need({k:v for k,v in parent.items()if k not in ('status','error','calls','child')}=={k:v for k,v in expected.items()if k not in ('status','error','calls','child')},'expected-filter-prior-parent-identity')
    paths=expected_filter_paths();targets=release.get('targets',[])
    o.need(release.get('kind')==EXPECTED_FILTER_RELEASE and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and release.get('previous_recovery')==previous and release.get('previous_release')==oldproof['release']and release.get('order')==parent['order'],'expected-filter-reviewed-successor')
    o.need(len(targets)==3 and {t['target']for t in targets}==set(paths.values())and len({t['target']for t in targets})==3,'expected-filter-exact-three-targets')
    before={Path(r['path']).name:r for r in old_refs};o.need(len(before)==len(old_refs)==3 and set(before)=={n+'.before'for n in paths},'expected-filter-exact-three-archives')
    codes=copy.deepcopy(prior);by={r['path']:r for r in prior};expected_old={paths[n]:by[paths[n]]['sha256']for n in ('initial_ledger_recovery.py','collection_ready.py')};expected_old[paths['filter_readiness_recovery.py']]=_EXPECTED_PROVIDER_OLD_SHA
    for target in targets:
        archive=before[Path(target['target']).name+'.before'];o.need(target.get('mode')=='0644'and target['old_sha256']==target['before']['sha256']==archive['sha256']==expected_old[target['target']]and o.raw(archive)==o.raw(target['before']),'expected-filter-before-material');o.raw(target['after'])
        current={'path':target['target'],'sha256':target['after']['sha256']}
        if installed:_historical_role_source(current);o.need(Path(target['target']).stat().st_mode&0o777==0o644,'expected-filter-source-current')
        if target['target']in by:codes[codes.index(by[target['target']])]=current
    o.need(len(codes)==170 and len({r['path']for r in codes})==170 and paths['filter_readiness_recovery.py']not in by,'expected-filter-provider-not-a-vector-slot')
    for r in codes:
        if r['path']not in set(paths.values()):_historical_role_source(r)
    return release,codes

def _expected_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,release_ref,old_refs,archives=(),*,installed=True):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));release,codes=_expected_filter_sources(parent,release_ref,old_refs,installed=installed);folder=phase_directory(parent);order=o.doc(parent['order'])
    o.need(release.get('original_parent')==parent_ref and release.get('worker_exit')==worker_ref and release.get('ready_observation')==ready_inputs['ready_observation'],'expected-filter-exact-release-inputs')
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])==2 and all(c['state']=='returned'for c in parent['calls']),'expected-filter-original-parent-failure')
    call=parent['calls'][1];launch=o.doc(call['launch']);exit=o.doc(call['result']);o.need(call['launch']['path']==str(folder/'children/0001-launch.json')and call['result']['path']==str(folder/'children/0001-exit.json')and exit['launch']==call['launch']and exit['argv']==launch['argv']==call['argv']==parent['calls'][0]['argv']and launch['index']==1 and launch['order']==parent['order']and exit['returncode']==2 and exit['stderr']==''and json.loads(exit['stdout'])=={'ok':False,'error':FILTER_ERROR},'expected-filter-exact-natural-failure')
    o.need(parent['start_monotonic']<=launch['launched_monotonic']<=exit['exited_monotonic']and all(type(x)in(int,float)and math.isfinite(x)for x in (launch['launched_monotonic'],exit['exited_monotonic'])),'expected-filter-natural-clock')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256']and engine['status']=='hold'and engine.get('error')==FILTER_ERROR and engine['phase']=='collect'and engine['index']==0 and len(engine['calls'])==4,'expected-filter-original-engine')
    for i,c in enumerate(engine['calls'][:-1],1):o.need(c['state']=='returned'and c.get('applied')is True and c['result']['path']==str(folder/'receipts'/(str(i).zfill(5)+'.json')),'expected-filter-applied-prefix');o.doc(c['result'])
    failed=engine['calls'][-1];o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('company_index')==0 and failed.get('error')==FILTER_ERROR and not failed.get('result')and not failed.get('applied'),'expected-filter-resultless-readonly-failure')
    context=failed['context'];job_ref=context['artifacts']['unit_artifacts']['work_order'];job=o.doc(job_ref)
    o.need(context['order']==order and context['company']==order['companies'][0]and context['artifacts']==engine['companies'][0]['artifacts']and ready_inputs['job']==job_ref and ready_inputs['original']==operator_ref and job['workflow_path']==operator_ref['path'],'expected-filter-original-collect-binding')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;pxref=o.ref(attempt/'parent-run-exit.json');px=o.doc(pxref);output=json.loads(o.raw(px['stdout']))
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['attempt_id']==request['attempt_id']and worker['returncode']==0 and response['attempt_id']==request['attempt_id']and response['task_id']==request['task']['id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['flow']==o.FLOW,'expected-filter-worker-original')
    o.need(px['returncode']==0 and output['status']=='hold'and output['error']=='execution-child-stopped'and output['last_child_receipt']==call['result']and not o.raw(px['stderr']),'expected-filter-parent-natural-return')
    with _expected_filter_provider(release)as provider:
        facts=provider.qualify(ready_inputs,read,lambda r:o.raw(mapped.get((r['path'],r['sha256']),r)))
        o.need(facts.get('provider')==provider.READONLY_PROVIDER,'expected-filter-public-ready-provider')
        index=read(ready_inputs['ready_observation']);o.need(release.get('observer_code')==index['refs']['read_once.py'],'expected-filter-observer-source-binding');authority=read(index['refs']['authority-record.json']);o.need(authority['task']==request['task']['id']and authority['failed_attempt']==request['task']['attempt']+1,'expected-filter-original-observer-task')
    materials=[parent_ref,engine_ref,operator_ref,worker_ref,worker['request'],worker['response'],pxref,px['stdout'],px['stderr'],job_ref,*[c[k]for c in parent['calls']for k in ('launch','result')],*[c['result']for c in engine['calls'][:-1]],*facts['materials']]
    return {'parent':parent,'engine':engine,'operator':state,'ready_inputs':ready_inputs,'release':release_ref,'old_sources':list(old_refs),'effective_code_refs':codes,'ready_facts':facts,'order':parent['order'],'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'task_id':request['task']['id'],'outer':request['task']['outer'],'failed_calls':copy.deepcopy(parent['calls']),'materials':list({(r['path'],r['sha256']):r for r in materials}.values())}
_expected_filter_facts=_hm_history(_expected_filter_facts)

def plan_expected_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,release_ref,old_refs,*,installed=False):
    facts=_expected_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,release_ref,old_refs,installed=installed)
    _expected_filter_initial_boundary(facts);return facts

def _expected_filter_initial_boundary(facts):
    folder=phase_directory(facts['parent']);o.need(not(folder/'receipts/00004.json').exists()and not(folder/'completion.json').exists()and not(folder/'collection-ready.json').exists(),'expected-filter-no-unknown-receipt-or-ready');ledger_bytes(o.doc(facts['order']))

def _expected_filter_delta(facts,proof_ref,wf_proof):
    parent,engine=copy.deepcopy(facts['parent']),copy.deepcopy(facts['engine'])
    for value in (parent,engine):
        value['status']='running';value.setdefault('resolved_errors',[]).append({'error':value.pop('error'),'recovery':proof_ref});value[EXPECTED_FILTER_FIELD]=proof_ref
    engine.setdefault('resolved_readonly_failures',[]).append({'index':len(engine['calls'])-1,'call':engine['calls'].pop(),'recovery':proof_ref})
    return parent,engine

def verify_expected_filter_ready(current,proof_ref,*,installed=True):
    proof=o.doc(proof_ref);facts=proof['facts'];base=phase_directory(facts['parent'])/'.expected-filter-readiness'/facts['originals'][0]['sha256'];o.need(proof['kind']==EXPECTED_FILTER_KIND and proof_ref['path']==str(base/'proof.json')and current.get(EXPECTED_FILTER_FIELD)==proof_ref,'expected-filter-proof-location')
    originals=proof['original_archives']
    for pair in originals:o.need(pair['archive']['path']==str(base/'originals'/(pair['original']['sha256']+'.json'))and pair['archive']['sha256']==pair['original']['sha256'],'expected-filter-original-archive');o.raw(pair['archive'])
    args=[*facts['originals'],facts['worker_exit'],facts['ready_inputs'],facts['release'],facts['old_sources']];derived=_expected_filter_facts(*args,archives=originals,installed=installed);o.need(derived==facts,'expected-filter-proof-derived')
    release=o.doc(facts['release'])
    with _expected_filter_provider(release)as provider:
        wf=provider.verify(proof['workflow_proof']);o.need(wf['facts']==facts['ready_facts']and wf['original']==facts['operator'],'expected-filter-workflow-proof')
    expected,ee=_expected_filter_delta(facts,proof_ref,proof['workflow_proof']);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in expected.items()if k not in variable}and current['calls'][:2]==expected['calls']and all(c['state']in('unknown','returned')for c in current['calls'][2:]),'expected-filter-parent-prefix')
    engine=o.doc(o.ref(phase_directory(current)/'engine.json'));state=o.doc(o.ref(facts['originals'][2]['path']))
    o.need(engine.get(EXPECTED_FILTER_FIELD)==proof_ref and engine['order']==ee['order']and engine['scope_sha256']==ee['scope_sha256']and engine['calls'][:3]==ee['calls']and engine.get('resolved_readonly_failures',[])[:len(ee['resolved_readonly_failures'])]==ee['resolved_readonly_failures'],'expected-filter-engine-prefix')
    o.need(state['calls'][:5]==facts['operator']['calls']and state.get('confirmed_filter_readonly_recovery')==proof['workflow_proof']and all(state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','date_range','identity','tab_id')),'expected-filter-WF-prefix')
    execution=_role_execution_sources(facts['effective_code_refs'],installed=installed)
    return {'kind':EXPECTED_FILTER_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,proof['workflow_proof'],facts['release'],*[a['archive']for a in originals],*facts['materials'],*execution['evidence']]}

_EXPECTED_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(EXPECTED_FILTER_FIELD):
        o.need(current[PREENGINE_FIELD]==proof_ref,'expected-filter-prior-marker-preserved');return verify_expected_filter_ready(current,current[EXPECTED_FILTER_FIELD],installed=installed)
    return _EXPECTED_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_expected_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,release_ref,old_refs,*,guard,checkpoint=lambda stage:None):
    """Caller owns outer resource/scheduler/coordinator/operator; owns parent here.
    No RPC, child, task setter, fresh clock reset, or business input.
    """
    if release_ref is None:
        o.need(not old_refs,'current-filter-no-historical-source-chain')
        return _recover_current_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,guard=guard,checkpoint=checkpoint)
    o.need(callable(guard),'expected-filter-locked-guard-required');path=Path(parent_ref['path']);base=path.parent/'.expected-filter-readiness'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,release_ref,old_refs]
    with path.with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json';intent={'kind':EXPECTED_FILTER_KIND,'args':args}
        if ip.exists():o.need(o.doc(o.ref(ip))['intent']==intent,'expected-filter-foreign-intent');saved=o.doc(o.ref(ip));archives=saved['original_archives'];facts=_expected_filter_facts(*args,archives=archives,installed=True);o.need(facts==saved['facts'],'expected-filter-same-intent-facts')
        else:
            facts=_expected_filter_facts(*args,installed=True);_expected_filter_initial_boundary(facts);archives=[]
            for r in facts['originals']:archives.append({'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))})
            o.immutable(ip,{'intent':intent,'facts':facts,'original_archives':archives});checkpoint('intent')
        expected_ref={'path':str(pp),'sha256':'pending'}
        if pp.exists():
            proof_ref=o.ref(pp);proof=o.doc(proof_ref);o.need(proof.get('kind')==EXPECTED_FILTER_KIND and proof.get('facts')==facts and proof.get('original_archives')==archives,'expected-filter-existing-proof');wf_proof=proof['workflow_proof']
            # Before either mutable control CAS, independently revalidate the
            # persisted WF proof and exact original facts. A corrupt partial
            # proof cannot change parent/engine before failing at final verify.
            with _expected_filter_provider(o.doc(release_ref))as provider:
                checked=provider.verify(wf_proof)
                o.need(checked['facts']==facts['ready_facts']and checked['original']==facts['operator']and o.doc(o.ref(operator_ref['path']))==checked['after'],'expected-filter-existing-workflow-proof')
        else:
            with _expected_filter_provider(o.doc(release_ref))as provider:
                result=provider.recover(ready_inputs,guard=guard,checkpoint=lambda stage:checkpoint('workflow-'+stage));wf_proof=result['proof']
            proof_ref=o.immutable(pp,{'kind':EXPECTED_FILTER_KIND,'facts':facts,'original_archives':archives,'workflow_proof':wf_proof});checkpoint('proof')
        parent_after,engine_after=_expected_filter_delta(facts,proof_ref,wf_proof)
        for r,b,a in ((engine_ref,facts['engine'],engine_after),(parent_ref,facts['parent'],parent_after)):o.need(o.doc(o.ref(r['path']))in(b,a),'expected-filter-CAS-third-state')
        import complaint_execution_launcher as launcher
        for name,r,b,a in (('engine',engine_ref,facts['engine'],engine_after),('parent',parent_ref,facts['parent'],parent_after)):
            guard('before-'+name+'-CAS');current=o.doc(o.ref(r['path']));o.need(current in(b,a),'expected-filter-CAS-raced')
            if current==b:o.need(o.ref(r['path'])==r,'expected-filter-CAS-raw-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_expected_filter_ready(o.doc(o.ref(path)),proof_ref);guard('readback');return {'state':'reconciled','proof':proof_ref,'workflow_proof':wf_proof,'parent':o.ref(path),'engine':o.ref(engine_ref['path']),'operator':o.ref(operator_ref['path']),'new_inputs':0}

# A chained local readonly frontier. Original failed child calls and old W30
# proof remain; this marker adds only one exact later known failure.
BOUNDED_FILTER_FIELD='bounded_filter_readiness_recovery'
BOUNDED_FILTER_KIND='complaint-bounded-filter-ready-continuation-v1'
_BOUNDED_PROBE_SHA='232c94c0bebe52e1cb963495d6de4720491c02474e8e879fcce582d7500aefbf'
@_hm_contextlib.contextmanager
def _bounded_probe(historical_sources=None):
    import importlib.util
    path=o.PROJECT/'packages/workshop-director/workshop_director/filter_readiness_probe.py';reference={'path':str(path),'sha256':_BOUNDED_PROBE_SHA};data=o.raw(reference);spec=importlib.util.spec_from_file_location('_complaint_bounded_filter_probe',path);module=importlib.util.module_from_spec(spec);old=sys.path[:]
    try:
        exec(compile(data,str(path),'exec'),module.__dict__)
        if historical_sources is not None:
            switch_path=o.PROJECT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py';historical={'path':str(switch_path),'sha256':'379b0ccc02d41ebc92342597c109cdb63dc61e29807dd8c654c0f9b2559317d7'};slots=[r for r in historical_sources if r['path']==str(switch_path)];o.need(slots==[historical],'bounded-probe-exact-historical-switch-slot');material=_historical_role_source(historical);o.need(material['current']=={'path':str(switch_path),'sha256':'0ef645c97a6070ea5fa6d252d2a237d6d02a63d3f309f5ec8857cbada6b2affa'},'bounded-probe-exact-reviewed-switch-current');o.raw(material['material']);physical_ref=module.ref
            def source_ref(candidate):
                actual=physical_ref(candidate)
                if str(Path(candidate).absolute())==str(switch_path):
                    o.need(actual==material['current'],'bounded-probe-switch-generation-drift');return dict(historical)
                return actual
            module.ref=source_ref
        yield module
    finally:sys.path[:]=old

def _bounded_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,observation_ref,archives=()):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);order=o.doc(parent['order']);prior_ref=parent.get(EXPECTED_FILTER_FIELD)
    o.need(prior_ref is not None and parent.get(PREENGINE_FIELD)and not parent.get(BOUNDED_FILTER_FIELD),'bounded-filter-prior-lineage')
    # Exact archived original parent is the historical argument. Never strip
    # new current fields to impersonate an old dictionary for a prior verifier.
    prior=verify_expected_filter_ready(parent,prior_ref);oldproof=o.doc(prior_ref)
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])>len(prior['failed_calls'])and all(c['state']=='returned'for c in parent['calls']),'bounded-filter-parent-frontier')
    call=parent['calls'][-1];index=len(parent['calls'])-1;launch=o.doc(call['launch']);exit=o.doc(call['result'])
    o.need(call['launch']['path']==str(folder/'children'/(str(index).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(index).zfill(4)+'-exit.json'))and exit['launch']==call['launch']and launch['argv']==exit['argv']==call['argv']and launch['index']==index and launch['order']==parent['order']and exit['returncode']==2 and exit['stderr']==''and json.loads(exit['stdout'])=={'ok':False,'error':FILTER_ERROR},'bounded-filter-exact-natural-failure')
    for previous in parent['calls'][:-1]:o.need(o.doc(previous['result'])['returncode']==(2 if previous in prior['failed_calls']else 0),'bounded-filter-unapproved-prior-failure')
    o.need(parent['start_monotonic']<=launch['launched_monotonic']<=exit['exited_monotonic'],'bounded-filter-original-clock')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256']and engine['status']=='hold'and engine.get('error')==FILTER_ERROR and engine['phase']=='collect'and type(engine['index'])is int and 0<=engine['index']<len(order['companies'])and engine['calls'],'bounded-filter-engine-frontier')
    failed=engine['calls'][-1];ci=engine['index'];context=failed['context'];job_ref=context['artifacts']['unit_artifacts']['work_order'];job=o.doc(job_ref)
    o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('company_index')==ci and failed.get('error')==FILTER_ERROR and not failed.get('result')and not failed.get('applied')and context['order']==order and context['company']==order['companies'][ci]and context['artifacts']==engine['companies'][ci]['artifacts']and job['workflow_path']==operator_ref['path']and job['company']==context['company']['company']and str(job['groupid'])==str(context['company']['groupid']),'bounded-filter-exact-collect-context')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True and c.get('result'),'bounded-filter-applied-prefix');o.doc(c['result'])
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;pxref=o.ref(attempt/'parent-run-exit.json');px=o.doc(pxref);output=json.loads(o.raw(px['stdout']))
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and request['attempt_id']==worker['attempt_id']==response['attempt_id']and request['task']['flow']==o.FLOW and worker['returncode']==0 and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order'],'bounded-filter-worker-failure')
    o.need(px['returncode']==0 and output['status']=='hold'and output['error']=='execution-child-stopped'and output['last_child_receipt']==call['result']and not o.raw(px['stderr']),'bounded-filter-parent-return')
    inputs={'job':job_ref,'original':operator_ref,'ready_observation':observation_ref}
    with _bounded_probe(oldproof['facts']['effective_code_refs'])as probe:
        ready=probe.qualify(inputs,read,lambda r:o.raw(mapped.get((r['path'],r['sha256']),r)));module=o.ref(Path(probe.__file__))
    o.need(ready['task_id']==request['task']['id']and ready['attempt']==request['task']['attempt']+1 and ready['original_calls']==state['calls'],'bounded-filter-observer-task')
    materials=[*inputs.values(),worker_ref,worker['request'],worker['response'],pxref,px['stdout'],px['stderr'],prior_ref,oldproof['facts']['release'],module,*[c[k]for c in parent['calls']for k in('launch','result')],*[c['result']for c in engine['calls'][:-1]],*ready['materials']]
    return {'kind':BOUNDED_FILTER_KIND,'originals':[parent_ref,engine_ref,operator_ref],'parent':parent,'engine':engine,'operator':state,'worker_exit':worker_ref,'observation':observation_ref,'previous_proof':prior_ref,'prior_failed_calls':prior['failed_calls'],'failed_calls':[*prior['failed_calls'],call],'historical_code_refs':oldproof['facts']['effective_code_refs'],'ready':ready,'module':module,'order':parent['order'],'task_id':request['task']['id'],'outer':request['task']['outer'],'materials':list({(r['path'],r['sha256']):r for r in materials}.values())}
_bounded_filter_facts=_hm_history(_bounded_filter_facts)
def plan_bounded_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,observation_ref):
    return _bounded_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,observation_ref)
def _bounded_filter_delta(facts,proof_ref,wfproof):
    parent,engine=copy.deepcopy(facts['parent']),copy.deepcopy(facts['engine'])
    for value in(parent,engine):value['status']='running';value.setdefault('resolved_errors',[]).append({'error':value.pop('error'),'recovery':proof_ref});value[BOUNDED_FILTER_FIELD]=proof_ref
    engine.setdefault('resolved_readonly_failures',[]).append({'index':len(engine['calls'])-1,'call':engine['calls'].pop(),'recovery':proof_ref})
    return parent,engine

def verify_bounded_filter_ready(current,proof_ref):
    proof=o.doc(proof_ref);facts=proof['facts'];base=phase_directory(facts['parent'])/'.bounded-filter-readiness'/facts['originals'][0]['sha256']
    o.need(proof.get('kind')==BOUNDED_FILTER_KIND and current.get(BOUNDED_FILTER_FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json'),'bounded-filter-proof-location')
    archives=proof['original_archives']
    for pair in archives:o.need(pair['archive']=={'path':str(base/'originals'/(pair['original']['sha256']+'.json')),'sha256':pair['original']['sha256']},'bounded-filter-original-archive');o.raw(pair['archive'])
    args=[*facts['originals'],facts['worker_exit'],facts['observation']];derived=_bounded_filter_facts(*args,archives=archives);o.need(derived==facts,'bounded-filter-proof-derived')
    with _bounded_probe(facts['historical_code_refs'])as probe:
        wf=probe.verify(proof['workflow_proof']);o.need(wf['facts']==facts['ready']and wf['original']==facts['operator'],'bounded-filter-workflow-proof')
    parent,engine=_bounded_filter_delta(facts,proof_ref,proof['workflow_proof']);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls']and all(c.get('state')in('returned','unknown')for c in current['calls'][len(parent['calls']):]),'bounded-filter-parent-prefix')
    live_engine=o.doc(o.ref(phase_directory(current)/'engine.json'));live_state=o.doc(o.ref(facts['originals'][2]['path']));o.need(live_engine.get(BOUNDED_FILTER_FIELD)==proof_ref and live_engine['order']==engine['order']and live_engine['scope_sha256']==engine['scope_sha256']and live_engine['calls'][:len(engine['calls'])]==engine['calls']and live_engine['resolved_readonly_failures'][:len(engine['resolved_readonly_failures'])]==engine['resolved_readonly_failures'],'bounded-filter-engine-prefix')
    o.need(live_state.get('confirmed_bounded_filter_readonly_recovery')==proof['workflow_proof']and live_state['calls'][:len(facts['operator']['calls'])]==facts['operator']['calls']and all(live_state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','date_range','identity','tab_id')),'bounded-filter-WF-prefix')
    execution=_role_execution_sources(facts['historical_code_refs'],installed=True)
    return {'kind':BOUNDED_FILTER_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,proof['workflow_proof'],facts['previous_proof'],*[a['archive']for a in archives],*[next((a['archive']for a in archives if a['original']==r),r)for r in facts['materials']],*execution['evidence']]}
_BOUNDED_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(BOUNDED_FILTER_FIELD):
        o.need(installed and current[PREENGINE_FIELD]==proof_ref,'bounded-filter-prior-marker');return verify_bounded_filter_ready(current,current[BOUNDED_FILTER_FIELD])
    return _BOUNDED_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_bounded_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,observation_ref,*,guard,checkpoint=lambda stage:None):
    """Caller external4 locks; API owns parent lock. No observer/input/retry."""
    import complaint_execution_launcher as launcher
    o.need(callable(guard),'bounded-filter-guard-required');base=Path(parent_ref['path']).parent/'.bounded-filter-readiness'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref,observation_ref]
    with Path(parent_ref['path']).with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json'
        if ip.exists():
            intent=o.doc(o.ref(ip));o.need(intent['kind']==BOUNDED_FILTER_KIND and intent['args']==args,'bounded-filter-original-intent');archives=intent['original_archives'];facts=_bounded_filter_facts(*args,archives=archives);o.need(facts==intent['facts'],'bounded-filter-same-intent-facts')
        else:
            facts=_bounded_filter_facts(*args);archives=[{'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))}for r in facts['originals']];o.immutable(ip,{'kind':BOUNDED_FILTER_KIND,'args':args,'facts':facts,'original_archives':archives});checkpoint('intent')
        with _bounded_probe()as probe:
            wfbase=probe.location(operator_ref);wfpath=wfbase/'proof.json'
            if not wfpath.exists():
                pairs=[{'original':r,'archive':immutable_bytes(wfbase/'materials'/(r['sha256']+'.data'),o.raw(r))}for r in facts['ready']['materials']];wfproof=o.immutable(wfpath,{'kind':probe.KIND,'module':facts['module'],'facts':facts['ready'],'archives':pairs})
            else:wfproof=o.ref(wfpath)
            checked=probe.verify(wfproof);o.need(checked['facts']==facts['ready']and checked['original']==facts['operator'],'bounded-filter-preCAS-workflow-proof');wfafter=checked['after']
        if pp.exists():proofref=o.ref(pp);o.need(o.doc(proofref)=={'kind':BOUNDED_FILTER_KIND,'facts':facts,'original_archives':archives,'workflow_proof':wfproof},'bounded-filter-existing-proof')
        else:proofref=o.immutable(pp,{'kind':BOUNDED_FILTER_KIND,'facts':facts,'original_archives':archives,'workflow_proof':wfproof})
        checkpoint('proof');parent,engine=_bounded_filter_delta(facts,proofref,wfproof)
        for name,r,b,a in(('workflow',operator_ref,facts['operator'],wfafter),('engine',engine_ref,facts['engine'],engine),('parent',parent_ref,facts['parent'],parent)):
            guard('before-'+name+'-CAS');value=o.doc(o.ref(r['path']));o.need(value in(b,a),'bounded-filter-CAS-third-state')
            if value==b:o.need(o.ref(r['path'])==r,'bounded-filter-CAS-raw-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_bounded_filter_ready(o.doc(o.ref(parent_ref['path'])),proofref);guard('readback');return {'state':'reconciled','proof':proofref,'workflow_proof':wfproof,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'operator':o.ref(operator_ref['path']),'new_inputs':0}

# Exact local readonly tab-choice failure. No new WF marker or input authority.
RECORD_CHOICE_FIELD='equivalent_record_tab_recovery'
RECORD_CHOICE_KIND='complaint-equivalent-record-tab-readonly-recovery-v1'
RECORD_CHOICE_ERROR='record-tab-ambiguous'
def _record_choice_facts(parent_ref,engine_ref,operator_ref,worker_ref,scope_ref,archives=(),module_ref=None):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);prior_ref=parent.get(BOUNDED_FILTER_FIELD)
    o.need(prior_ref and not parent.get(RECORD_CHOICE_FIELD),'record-choice-original-lineage');prior=verify_bounded_filter_ready(parent,prior_ref);old=o.doc(prior_ref)
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])==len(prior['failed_calls'])+1 and parent['calls'][:-1]==prior['failed_calls'],'record-choice-parent-frontier')
    child=parent['calls'][-1];ci=len(parent['calls'])-1;launch=o.doc(child['launch']);ex=o.doc(child['result'])
    o.need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(ci).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(ci).zfill(4)+'-exit.json'))and launch['index']==ci and launch['order']==parent['order']and ex['launch']==child['launch']and child['argv']==launch['argv']==ex['argv']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':RECORD_CHOICE_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'record-choice-exact-child')
    o.need(engine['status']=='hold'and engine.get('error')==RECORD_CHOICE_ERROR and engine['phase']=='collect'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['calls'],'record-choice-engine-frontier')
    failed=engine['calls'][-1];context=failed['context'];order=o.doc(parent['order']);index=engine['index'];job_ref=context['artifacts']['unit_artifacts']['work_order'];job=o.doc(job_ref)
    o.need(failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==index and not failed.get('applied')and not failed.get('result')and failed['error']==RECORD_CHOICE_ERROR and context['order']==order and context['company']==order['companies'][index]and context['artifacts']==engine['companies'][index]['artifacts'],'record-choice-exact-collect')
    o.need(job['workflow_path']==operator_ref['path']and state['phase']=='baselineRecordTabs'and state['state']=='running'and state['company']==job['company']and state['groupid']==str(job['groupid'])and state['identity']==job['identity_baseline']and state['date_range']=={k:job['date_range'][k]for k in('start','end')}and (state['last_error']['code'],state['last_error']['message'])==(RECORD_CHOICE_ERROR,RECORD_CHOICE_ERROR),'record-choice-WF-scope')
    calls=state['calls'];last=calls[-1];cmd=last['command'];hover=last['result'].get('hovered',{})
    o.need(all(c['state']=='confirmed'for c in calls)and len({c['key']for c in calls})==len(calls)and last['phase']=='openExportMenu'and cmd=={'op':'hover','tabId':state['tab_id'],'locator':{'by':'selector','value':hover.get('selector')},'kind':'export'}and hover.get('name')=='导出'and last['result'].get('kind')=='export'and int(last['key'].split(':')[0])+2==state['revision'],'record-choice-confirmed-export-hover')
    o.need(not any(state.get(k)for k in('exportPending','downloadPending','submitted_at','baseline_records','record_tab_id','generated_record','ticket')),'record-choice-no-export-start')
    path=o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py';module_ref=module_ref or o.ref(path);o.need(module_ref['path']==str(path),'record-choice-selector-source');material=_historical_role_source(module_ref)
    import importlib.util
    spec=importlib.util.spec_from_file_location('_record_choice_workflow',path);module=importlib.util.module_from_spec(spec);exec(compile(o.raw(material['material']),str(path),'exec'),module.__dict__)
    from readonly_tick_snapshot import decode
    from dom_evidence import context as tab_context,verified_review_filter,all_store_scope,record_tabs
    snapshot=o.doc(scope_ref);window=snapshot['scope']['windowId'];decode(snapshot,state['tab_id'],window)
    o.need(Path(scope_ref['path']).parent==Path(operator_ref['path']).parent/'bridge-evidence'and Path(scope_ref['path']).name.startswith(str(state['revision']).zfill(4)+'-baselineRecordTabs-scope-')and snapshot['tree']==o.doc(state['last_tree']),'record-choice-original-scope')
    source=tab_context(snapshot['before'],state['tab_id'],job['groupid']);after=tab_context(snapshot['after'],state['tab_id'],job['groupid']);o.need(source==after and source['windowId']==window,'record-choice-source-window');verified_review_filter(snapshot['tree'],state['date_range']);all_store_scope(snapshot['tree'])
    chosen=module.existing_record_tab(snapshot['before'],job['groupid'],window,job.get('record_tab_id'));again=module.existing_record_tab(snapshot['after'],job['groupid'],window,job.get('record_tab_id'))
    candidates=record_tabs(snapshot['before'],job['groupid']);o.need(chosen is not None and chosen==again and [t['tabId']for t in candidates]==state['baseline_record_tab_ids']and len(candidates)>1,'record-choice-equivalent-saved-tabs')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json')and worker['returncode']==0 and worker['attempt_id']==response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['outer']==old['facts']['outer']and request['task']['id']==old['facts']['task_id'],'record-choice-worker-terminal')
    return {'kind':RECORD_CHOICE_KIND,'originals':[parent_ref,engine_ref,operator_ref],'parent':parent,'engine':engine,'operator':state,'worker_exit':worker_ref,'scope':scope_ref,'previous_proof':prior_ref,'selector_source':module_ref,'selected':chosen,'failed_calls':[*prior['failed_calls'],child],'historical_code_refs':old['facts']['historical_code_refs'],'order':parent['order'],'outer':request['task']['outer'],'task_id':request['task']['id']}
_record_choice_facts=_hm_history(_record_choice_facts)
def plan_record_tab_choice(parent_ref,engine_ref,operator_ref,worker_ref,scope_ref):return _record_choice_facts(parent_ref,engine_ref,operator_ref,worker_ref,scope_ref)
def _record_choice_delta(facts,proof_ref):
    parent,engine=copy.deepcopy(facts['parent']),copy.deepcopy(facts['engine'])
    for value in(parent,engine):value['status']='running';value.setdefault('resolved_errors',[]).append({'error':value.pop('error'),'recovery':proof_ref});value[RECORD_CHOICE_FIELD]=proof_ref
    engine.setdefault('resolved_readonly_failures',[]).append({'index':len(engine['calls'])-1,'call':engine['calls'].pop(),'recovery':proof_ref})
    return parent,engine

def verify_record_tab_choice(current,proof_ref):
    p=o.doc(proof_ref);facts=p['facts'];base=phase_directory(facts['parent'])/'.equivalent-record-tab-recovery'/facts['originals'][0]['sha256'];archives=p['original_archives']
    o.need(p['kind']==RECORD_CHOICE_KIND and proof_ref['path']==str(base/'proof.json')and current.get(RECORD_CHOICE_FIELD)==proof_ref,'record-choice-proof')
    for pair in archives:o.need(pair['archive']=={'path':str(base/'originals'/(pair['original']['sha256']+'.json')),'sha256':pair['original']['sha256']},'record-choice-archive');o.raw(pair['archive'])
    derived=_record_choice_facts(*facts['originals'],facts['worker_exit'],facts['scope'],archives=archives,module_ref=facts['selector_source']);o.need(derived==facts,'record-choice-proof-derived');parent,engine=_record_choice_delta(facts,proof_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls'],'record-choice-parent-prefix')
    live=o.doc(o.ref(phase_directory(current)/'engine.json'));state=o.doc(o.ref(facts['originals'][2]['path']));o.need(live.get(RECORD_CHOICE_FIELD)==proof_ref and live['order']==engine['order']and live['scope_sha256']==engine['scope_sha256']and live['calls'][:len(engine['calls'])]==engine['calls']and live['resolved_readonly_failures'][:len(engine['resolved_readonly_failures'])]==engine['resolved_readonly_failures'],'record-choice-engine-prefix')
    o.need(state['calls'][:len(facts['operator']['calls'])]==facts['operator']['calls']and all(state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','identity','date_range','tab_id')),'record-choice-WF-prefix');execution=_role_execution_sources(facts['historical_code_refs'],installed=True)
    return {'kind':RECORD_CHOICE_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,facts['previous_proof'],facts['scope'],facts['worker_exit'],*[a['archive']for a in archives],*execution['evidence']]}
_RECORD_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(RECORD_CHOICE_FIELD):
        o.need(installed and current[PREENGINE_FIELD]==proof_ref,'record-choice-prior-marker');return verify_record_tab_choice(current,current[RECORD_CHOICE_FIELD])
    return _RECORD_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_record_tab_choice(parent_ref,engine_ref,operator_ref,worker_ref,scope_ref,*,guard,checkpoint=lambda stage:None):
    """Outer4 caller locks; owns parent lock. WF bytes untouched; normal tick/go resolves its error."""
    import complaint_execution_launcher as launcher
    o.need(callable(guard),'record-choice-guard');base=Path(parent_ref['path']).parent/'.equivalent-record-tab-recovery'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref,scope_ref]
    with Path(parent_ref['path']).with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json'
        if ip.exists():
            intent=o.doc(o.ref(ip));o.need(intent['args']==args and intent['kind']==RECORD_CHOICE_KIND,'record-choice-same-intent');archives=intent['original_archives'];facts=_record_choice_facts(*args,archives=archives,module_ref=intent['facts']['selector_source']);o.need(facts==intent['facts'],'record-choice-same-facts')
        else:
            facts=_record_choice_facts(*args);archives=[{'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))}for r in facts['originals']];o.immutable(ip,{'kind':RECORD_CHOICE_KIND,'args':args,'facts':facts,'original_archives':archives})
        value={'kind':RECORD_CHOICE_KIND,'facts':facts,'original_archives':archives}
        if pp.exists():proof_ref=o.ref(pp);o.need(o.doc(proof_ref)==value,'record-choice-existing-proof')
        else:proof_ref=o.immutable(pp,value)
        checkpoint('proof');parent,engine=_record_choice_delta(facts,proof_ref)
        for name,r,b,a in(('engine',engine_ref,facts['engine'],engine),('parent',parent_ref,facts['parent'],parent)):
            guard('before-'+name+'-CAS');current=o.doc(o.ref(r['path']));o.need(current in(b,a),'record-choice-CAS-third-state')
            if current==b:o.need(o.ref(r['path'])==r,'record-choice-CAS-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_record_tab_choice(o.doc(o.ref(parent_ref['path'])),proof_ref);guard('readback');return {'state':'reconciled','proof':proof_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'workflow_unchanged':operator_ref,'selected_saved_tab':facts['selected'],'new_inputs':0}

# Exact pre-input validator failure after a confirmed export dialog open.
COMMAND_MODULE_FIELD='configured_module_identity_recovery'
COMMAND_MODULE_KIND='complaint-configured-module-instance-readonly-recovery-v1'
COMMAND_MODULE_ERROR='dom-search-command-generation-drift'
COMMAND_MODULE_WF={'path':str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'sha256':'0eed7810b398730740e682820ef3788a0424386ea81d7a06372ce623b089ec43'}
def _command_module_facts(parent_ref,engine_ref,operator_ref,worker_ref,archives=()):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);previous=parent.get(RECORD_CHOICE_FIELD)
    o.need(previous and not parent.get(COMMAND_MODULE_FIELD),'command-module-original-lineage');prior=verify_record_tab_choice(parent,previous);old=o.doc(previous)
    material=_historical_role_source(COMMAND_MODULE_WF);o.raw(material['material'])
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])==len(prior['failed_calls'])+1 and parent['calls'][:-1]==prior['failed_calls'],'command-module-parent-frontier')
    child=parent['calls'][-1];ci=len(parent['calls'])-1;launch=o.doc(child['launch']);ex=o.doc(child['result'])
    o.need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(ci).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(ci).zfill(4)+'-exit.json'))and launch['index']==ci and launch['order']==parent['order']and ex['launch']==child['launch']and child['argv']==launch['argv']==ex['argv']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':COMMAND_MODULE_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'command-module-exact-natural-child')
    o.need(engine['status']=='hold'and engine.get('error')==COMMAND_MODULE_ERROR and engine['phase']=='collect'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['calls'],'command-module-engine-frontier')
    failed=engine['calls'][-1];context=failed['context'];order=o.doc(parent['order']);index=engine['index'];job_ref=context['artifacts']['unit_artifacts']['work_order'];job=o.doc(job_ref)
    o.need(failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==index and not failed.get('applied')and not failed.get('result')and failed['error']==COMMAND_MODULE_ERROR and context['order']==order and context['company']==order['companies'][index]and context['artifacts']==engine['companies'][index]['artifacts'],'command-module-exact-collect')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True and c.get('result'),'command-module-applied-prefix');o.doc(c['result'])
    original=old['facts']['operator'];calls=state['calls'];prefix=original['calls']
    o.need(job['workflow_path']==operator_ref['path']and state['work_order_id']==job['work_order_id']and state['state']=='running'and state['phase']=='exportDialogProfileRequired'and not state.get('last_error')and state['record_tab_id']==old['facts']['selected']['tabId']and state['company']==job['company']and state['groupid']==str(job['groupid'])and state['identity']==job['identity_baseline']and state['date_range']=={k:job['date_range'][k]for k in('start','end')}and calls[:len(prefix)]==prefix and len(calls)==len(prefix)+2 and all(c['state']=='confirmed'for c in calls),'command-module-WF-confirmed-prefix')
    for call,phase,op,name in zip(calls[-2:],('openExportMenuAgain','openExportDialog'),('hover','click'),('导出','导出评价')):
        cmd=call['command'];node=call['result'].get('hovered'if op=='hover'else'clicked',{});o.need(call['phase']==phase and call['key'].split(':')[1]==phase and cmd=={'op':op,'tabId':state['tab_id'],'locator':{'by':'selector','value':node.get('selector')},'kind':'export'}and node.get('name')==name and call['result'].get('kind')=='export','command-module-exact-confirmed-dialog-input')
    o.need(state['revision']==int(calls[-1]['key'].split(':')[0])+1 and not any(state.get(k)for k in('exportPending','downloadPending','submitted_at','generated_record','ticket')),'command-module-no-submit-download')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response'])
    o.need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json')and worker['returncode']==0 and worker['attempt_id']==response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['outer']==old['facts']['outer']and request['task']['id']==old['facts']['task_id'],'command-module-natural-worker')
    return {'kind':COMMAND_MODULE_KIND,'originals':[parent_ref,engine_ref,operator_ref],'parent':parent,'engine':engine,'operator':state,'worker_exit':worker_ref,'previous_proof':previous,'source_fix':COMMAND_MODULE_WF,'failed_calls':[*prior['failed_calls'],child],'historical_code_refs':old['facts']['historical_code_refs'],'order':parent['order'],'outer':request['task']['outer'],'task_id':request['task']['id']}
_command_module_facts=_hm_history(_command_module_facts)
def plan_command_module_identity(parent_ref,engine_ref,operator_ref,worker_ref):return _command_module_facts(parent_ref,engine_ref,operator_ref,worker_ref)
def _command_module_delta(facts,proof_ref):
    parent,engine=_record_choice_delta(facts,proof_ref)
    for value,before in((parent,facts['parent']),(engine,facts['engine'])):value[COMMAND_MODULE_FIELD]=value.pop(RECORD_CHOICE_FIELD);value[RECORD_CHOICE_FIELD]=before[RECORD_CHOICE_FIELD]
    return parent,engine

def verify_command_module_identity(current,proof_ref):
    p=o.doc(proof_ref);facts=p['facts'];base=phase_directory(facts['parent'])/'.configured-module-identity-recovery'/facts['originals'][0]['sha256'];archives=p['original_archives']
    o.need(p['kind']==COMMAND_MODULE_KIND and proof_ref['path']==str(base/'proof.json')and current.get(COMMAND_MODULE_FIELD)==proof_ref,'command-module-proof')
    for pair in archives:o.need(pair['archive']=={'path':str(base/'originals'/(pair['original']['sha256']+'.json')),'sha256':pair['original']['sha256']},'command-module-original-archive');o.raw(pair['archive'])
    derived=_command_module_facts(*facts['originals'],facts['worker_exit'],archives=archives);o.need(derived==facts,'command-module-proof-derived');parent,engine=_command_module_delta(facts,proof_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls'],'command-module-parent-prefix')
    live=o.doc(o.ref(phase_directory(current)/'engine.json'));state=o.doc(o.ref(facts['originals'][2]['path']));o.need(live.get(COMMAND_MODULE_FIELD)==proof_ref and live['order']==engine['order']and live['scope_sha256']==engine['scope_sha256']and live['calls'][:len(engine['calls'])]==engine['calls']and live['resolved_readonly_failures'][:len(engine['resolved_readonly_failures'])]==engine['resolved_readonly_failures'],'command-module-engine-prefix')
    o.need(state['calls'][:len(facts['operator']['calls'])]==facts['operator']['calls']and all(state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','identity','date_range','tab_id')),'command-module-WF-prefix');execution=_role_execution_sources(facts['historical_code_refs'],installed=True);fix=_historical_role_source(facts['source_fix'])
    return {'kind':COMMAND_MODULE_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,facts['previous_proof'],facts['worker_exit'],*[a['archive']for a in archives],fix['material'],fix['current'],*fix['dependencies'],*execution['evidence']]}
_COMMAND_MODULE_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(COMMAND_MODULE_FIELD):
        o.need(installed and current[PREENGINE_FIELD]==proof_ref,'command-module-prior-marker');return verify_command_module_identity(current,current[COMMAND_MODULE_FIELD])
    return _COMMAND_MODULE_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_command_module_identity(parent_ref,engine_ref,operator_ref,worker_ref,*,guard,checkpoint=lambda stage:None):
    """Outer4 caller locks, own parent lock. No WF write, input or retry."""
    import complaint_execution_launcher as launcher
    o.need(callable(guard),'command-module-guard');base=Path(parent_ref['path']).parent/'.configured-module-identity-recovery'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref]
    with Path(parent_ref['path']).with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json'
        if ip.exists():
            intent=o.doc(o.ref(ip));o.need(intent['args']==args and intent['kind']==COMMAND_MODULE_KIND,'command-module-same-intent');archives=intent['original_archives'];facts=_command_module_facts(*args,archives=archives);o.need(facts==intent['facts'],'command-module-same-facts')
        else:
            facts=_command_module_facts(*args);archives=[{'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))}for r in facts['originals']];o.immutable(ip,{'kind':COMMAND_MODULE_KIND,'args':args,'facts':facts,'original_archives':archives})
        value={'kind':COMMAND_MODULE_KIND,'facts':facts,'original_archives':archives}
        if pp.exists():proof_ref=o.ref(pp);o.need(o.doc(proof_ref)==value,'command-module-existing-proof')
        else:proof_ref=o.immutable(pp,value)
        checkpoint('proof');parent,engine=_command_module_delta(facts,proof_ref)
        for name,r,b,a in(('engine',engine_ref,facts['engine'],engine),('parent',parent_ref,facts['parent'],parent)):
            guard('before-'+name+'-CAS');current=o.doc(o.ref(r['path']));o.need(current in(b,a),'command-module-CAS-third-state')
            if current==b:o.need(o.ref(r['path'])==r,'command-module-CAS-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_command_module_identity(o.doc(o.ref(parent_ref['path'])),proof_ref);guard('readback');return {'state':'reconciled','proof':proof_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'workflow_unchanged':operator_ref,'new_inputs':0}

# Exact pre-activation readonly failure: an equivalent record tab was active.
REVIEW_RECORD_FIELD='equivalent_review_record_prestate_recovery'
REVIEW_RECORD_KIND='complaint-equivalent-review-record-prestate-recovery-v1'
REVIEW_RECORD_ERROR='review-tab-active-not-original-record-page'
REVIEW_RECORD_SOURCE={'path':str(o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_tab.py'),'sha256':'1cf5ae71192f4712659e3652d5188ce6eabedebfc413cbd1ad076bb671d9d679'}
def _review_record_facts(parent_ref,engine_ref,operator_ref,worker_ref,activation_ref,archives=()):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);previous=parent.get(COMMAND_MODULE_FIELD)
    o.need(previous and not parent.get(REVIEW_RECORD_FIELD),'review-record-original-lineage');prior=verify_command_module_identity(parent,previous);old=o.doc(previous)
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])==len(prior['failed_calls'])+1 and parent['calls'][:-1]==prior['failed_calls'],'review-record-parent-frontier')
    child=parent['calls'][-1];ci=len(parent['calls'])-1;launch=o.doc(child['launch']);ex=o.doc(child['result'])
    o.need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(ci).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(ci).zfill(4)+'-exit.json'))and launch['index']==ci and launch['order']==parent['order']and ex['launch']==child['launch']and child['argv']==launch['argv']==ex['argv']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':REVIEW_RECORD_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'review-record-exact-natural-child')
    o.need(engine['status']=='hold'and engine.get('error')==REVIEW_RECORD_ERROR and engine['phase']=='collect'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['calls'],'review-record-engine-frontier')
    failed=engine['calls'][-1];context=failed['context'];order=o.doc(parent['order']);index=engine['index'];art=context['artifacts'];unit=art['unit_artifacts'];job=o.doc(unit['work_order'])
    o.need(failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==index and not failed.get('applied')and not failed.get('result')and failed['error']==REVIEW_RECORD_ERROR and context['order']==order and context['company']==order['companies'][index]and art==engine['companies'][index]['artifacts']and art['unit_phase']=='frames'and unit['frame_index']==0 and unit['review_index']==0 and unit['operations']==[],'review-record-exact-frames-frontier')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True and c.get('result'),'review-record-applied-prefix');o.doc(c['result'])
    prefix=old['facts']['operator']['calls'];calls=state['calls']
    o.need(job['workflow_path']==operator_ref['path']and state['work_order_id']==job['work_order_id']and state['state']=='complete'and state['phase']=='done'and not state.get('last_error')and state['record_tab_id']==old['facts']['operator']['record_tab_id']and state['company']==job['company']and state['groupid']==str(job['groupid'])and state['identity']==job['identity_baseline']and state['date_range']=={k:job['date_range'][k]for k in('start','end')}and calls[:len(prefix)]==prefix and all(c['state']=='confirmed'for c in calls)and len({c['key']for c in calls})==len(calls),'review-record-complete-WF-prefix')
    nav_ref=unit['navigation'];nav=read(nav_ref);journal=read(activation_ref);binding=journal['binding'];manifest_ref=binding['manifest'];manifest=o.doc(manifest_ref)
    o.need(nav_ref['path']==str(Path(unit['source']['path']).parent/'navigation-state.json')and nav['phase']=='profileRequired'and nav['tab_id']==binding['scope']['tabId']and nav.get('stable_normal_verified')is True and nav['stable_observations']>=2 and nav['calls']and all(c['state']=='confirmed'for c in nav['calls'])and nav['calls'][-1]['key'].split(':')[1]=='negativeFilter'and nav['calls'][-1]['command'].get('tabId')==nav['tab_id'],'review-record-confirmed-navigation')
    o.need(journal['kind']=='review-capture-tab-activation-v1'and journal['phase']=='frames'and journal['state']=='preflight'and journal['revision']==0 and journal['calls']==[]and len(journal['reads'])==1 and Path(manifest_ref['path']).parent.parent==Path(unit['source']['path']).parent/'frames'and manifest['source']==unit['source']and manifest['job']==unit['job']and manifest['profile']==unit['profile']and manifest['envelope']==unit['envelope']and manifest['page']==unit['page']and bool(manifest['review_keys'])and manifest['review_keys']==unit['keys'][:len(manifest['review_keys'])],'review-record-zero-input-manifest')
    import importlib.util
    material=_historical_role_source(REVIEW_RECORD_SOURCE);path=Path(REVIEW_RECORD_SOURCE['path']);spec=importlib.util.spec_from_file_location('_review_record_prestate',path);module=importlib.util.module_from_spec(spec);oldpath=sys.path[:]
    try:exec(compile(o.raw(material['material']),str(path),'exec'),module.__dict__);derived=module.derive(manifest_ref)
    finally:sys.path[:]=oldpath
    o.need(binding==derived and binding['workflow']==operator_ref and binding['acquisition']==unit['acquisition']and binding['identity']==state['identity']and binding['scope']['groupid']==state['groupid']and binding['scope']['tabId']==state['tab_id'],'review-record-bound-source')
    key=module.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});directory=Path(unit['source']['path']).parent/'.review-tab-activation';o.need(activation_ref['path']==str(directory/(key+'.json')),'review-record-canonical-activation')
    raw_ref=journal['reads'][0];raw=o.doc(raw_ref);o.need(Path(raw_ref['path']).parent.parent==directory/key and Path(raw_ref['path']).name=='000-before-tabs.json'and raw['command']=={'op':'tabs'}and raw['response'].get('ok')is True and module.classify(raw['response']['result'],binding)in('original-record-active','original-record-active-window-unfocused'),'review-record-original-equivalent-prestate')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response'])
    o.need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json')and worker['returncode']==0 and worker['attempt_id']==response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['outer']==old['facts']['outer']and request['task']['id']==old['facts']['task_id'],'review-record-natural-worker')
    return {'kind':REVIEW_RECORD_KIND,'originals':[parent_ref,engine_ref,operator_ref,nav_ref,activation_ref],'parent':parent,'engine':engine,'operator':state,'navigation':nav,'activation':journal,'worker_exit':worker_ref,'previous_proof':previous,'source_fix':REVIEW_RECORD_SOURCE,'failed_calls':[*prior['failed_calls'],child],'historical_code_refs':old['facts']['historical_code_refs'],'order':parent['order'],'outer':request['task']['outer'],'task_id':request['task']['id'],'materials':[manifest_ref,raw_ref,*[unit[k]for k in('work_order','acquisition','source','job','profile','envelope','page','orders')]]}
_review_record_facts=_hm_history(_review_record_facts)
def plan_review_record_prestate(parent_ref,engine_ref,operator_ref,worker_ref,activation_ref):return _review_record_facts(parent_ref,engine_ref,operator_ref,worker_ref,activation_ref)
def _review_record_delta(facts,proof_ref):
    parent,engine=_record_choice_delta(facts,proof_ref)
    for value,before in((parent,facts['parent']),(engine,facts['engine'])):value[REVIEW_RECORD_FIELD]=value.pop(RECORD_CHOICE_FIELD);value[RECORD_CHOICE_FIELD]=before[RECORD_CHOICE_FIELD]
    return parent,engine

def verify_review_record_prestate(current,proof_ref):
    p=o.doc(proof_ref);facts=p['facts'];base=phase_directory(facts['parent'])/'.equivalent-review-record-prestate'/facts['originals'][0]['sha256'];archives=p['original_archives']
    o.need(p['kind']==REVIEW_RECORD_KIND and proof_ref['path']==str(base/'proof.json')and current.get(REVIEW_RECORD_FIELD)==proof_ref,'review-record-proof')
    for pair in archives:o.need(pair['archive']=={'path':str(base/'originals'/(pair['original']['sha256']+'.json')),'sha256':pair['original']['sha256']},'review-record-original-archive');o.raw(pair['archive'])
    derived=_review_record_facts(*facts['originals'][:3],facts['worker_exit'],facts['originals'][4],archives=archives);o.need(derived==facts,'review-record-proof-derived');parent,engine=_review_record_delta(facts,proof_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls'],'review-record-parent-prefix')
    live=o.doc(o.ref(phase_directory(current)/'engine.json'));state=o.doc(o.ref(facts['originals'][2]['path']));nav=o.doc(o.ref(facts['originals'][3]['path']))
    o.need(live.get(REVIEW_RECORD_FIELD)==proof_ref and live['order']==engine['order']and live['scope_sha256']==engine['scope_sha256']and live['calls'][:len(engine['calls'])]==engine['calls']and live['resolved_readonly_failures'][:len(engine['resolved_readonly_failures'])]==engine['resolved_readonly_failures'],'review-record-engine-prefix')
    o.need(state['calls'][:len(facts['operator']['calls'])]==facts['operator']['calls']and all(state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','identity','date_range','tab_id'))and nav['calls'][:len(facts['navigation']['calls'])]==facts['navigation']['calls']and nav['fingerprint']==facts['navigation']['fingerprint']and nav['tab_id']==facts['navigation']['tab_id'],'review-record-WF-navigation-prefix')
    execution=_role_execution_sources(facts['historical_code_refs'],installed=True);fix=_historical_role_source(facts['source_fix'])
    return {'kind':REVIEW_RECORD_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,facts['previous_proof'],facts['worker_exit'],*[a['archive']for a in archives],*facts['materials'],fix['material'],fix['current'],*fix['dependencies'],*execution['evidence']]}
_REVIEW_RECORD_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(REVIEW_RECORD_FIELD):
        o.need(installed and current[PREENGINE_FIELD]==proof_ref,'review-record-prior-marker');return verify_review_record_prestate(current,current[REVIEW_RECORD_FIELD])
    return _REVIEW_RECORD_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_review_record_prestate(parent_ref,engine_ref,operator_ref,worker_ref,activation_ref,*,guard,checkpoint=lambda stage:None):
    """Caller outer four locks; API owns parent lock. Only engine/parent CAS."""
    import complaint_execution_launcher as launcher
    o.need(callable(guard),'review-record-guard');base=Path(parent_ref['path']).parent/'.equivalent-review-record-prestate'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref,activation_ref]
    with Path(parent_ref['path']).with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json'
        if ip.exists():
            intent=o.doc(o.ref(ip));o.need(intent['args']==args and intent['kind']==REVIEW_RECORD_KIND,'review-record-same-intent');archives=intent['original_archives'];facts=_review_record_facts(*args,archives=archives);o.need(facts==intent['facts'],'review-record-same-facts')
        else:
            facts=_review_record_facts(*args);archives=[{'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))}for r in facts['originals']];o.immutable(ip,{'kind':REVIEW_RECORD_KIND,'args':args,'facts':facts,'original_archives':archives})
        value={'kind':REVIEW_RECORD_KIND,'facts':facts,'original_archives':archives}
        if pp.exists():proof_ref=o.ref(pp);o.need(o.doc(proof_ref)==value,'review-record-existing-proof')
        else:proof_ref=o.immutable(pp,value)
        checkpoint('proof');parent,engine=_review_record_delta(facts,proof_ref)
        for name,r,b,a in(('engine',engine_ref,facts['engine'],engine),('parent',parent_ref,facts['parent'],parent)):
            guard('before-'+name+'-CAS');current=o.doc(o.ref(r['path']));o.need(current in(b,a),'review-record-CAS-third-state')
            if current==b:o.need(o.ref(r['path'])==r,'review-record-CAS-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_review_record_prestate(o.doc(o.ref(parent_ref['path'])),proof_ref);guard('readback');return {'state':'reconciled','proof':proof_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'workflow_unchanged':operator_ref,'navigation_unchanged':facts['originals'][3],'activation_unchanged':activation_ref,'new_inputs':0}

# Resume an exact environment UNKNOWN only through existing readonly settlement.
FOCUS_SETTLE_FIELD='existing_window_readonly_settlement_recovery'
FOCUS_SETTLE_KIND='complaint-existing-window-readonly-settlement-recovery-v1'
FOCUS_SETTLE_ERROR='capture-window-unknown-readonly-no-replay'
def _focus_settle_validate(source,focus,binding):
    import importlib.util
    path=o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_focus.py';o.need(source['path']==str(path),'focus-settle-fixed-readonly-source')
    spec=importlib.util.spec_from_file_location('_existing_focus_readonly_validator',path);module=importlib.util.module_from_spec(spec);oldpath=sys.path[:]
    try:exec(compile(o.raw(source),str(path),'exec'),module.__dict__);module.validate_events(focus,binding)
    finally:sys.path[:]=oldpath
def _focus_settle_facts(parent_ref,engine_ref,operator_ref,worker_ref,focus_ref,archives=()):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);previous=parent.get(REVIEW_RECORD_FIELD)
    o.need(previous and not parent.get(FOCUS_SETTLE_FIELD),'focus-settle-original-lineage');prior=verify_review_record_prestate(parent,previous);old=o.doc(previous)
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and len(parent['calls'])==len(prior['failed_calls'])+1 and parent['calls'][:-1]==prior['failed_calls'],'focus-settle-parent-frontier')
    child=parent['calls'][-1];ci=len(parent['calls'])-1;launch=o.doc(child['launch']);ex=o.doc(child['result'])
    o.need(child['state']=='returned'and child['launch']['path']==str(folder/'children'/(str(ci).zfill(4)+'-launch.json'))and child['result']['path']==str(folder/'children'/(str(ci).zfill(4)+'-exit.json'))and launch['index']==ci and launch['order']==parent['order']and ex['launch']==child['launch']and child['argv']==launch['argv']==ex['argv']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':FOCUS_SETTLE_ERROR}and parent['start_monotonic']<=launch['launched_monotonic']<=ex['exited_monotonic'],'focus-settle-exact-natural-child')
    o.need(engine['status']=='hold'and engine.get('error')==FOCUS_SETTLE_ERROR and engine['phase']=='collect'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['calls'],'focus-settle-engine-frontier')
    failed=engine['calls'][-1];context=failed['context'];order=o.doc(parent['order']);index=engine['index'];art=context['artifacts'];unit=art['unit_artifacts'];job=o.doc(unit['work_order'])
    o.need(failed['state']=='failed'and failed['step']=='collect'and failed['company_index']==index and not failed.get('applied')and not failed.get('result')and failed['error']==FOCUS_SETTLE_ERROR and context['order']==order and context['company']==order['companies'][index]and art==engine['companies'][index]['artifacts']and art['unit_phase']=='frames'and unit['operations']==[]and unit['frame_index']==unit['review_index']==0,'focus-settle-exact-frames-frontier')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True and c.get('result'),'focus-settle-applied-prefix');o.doc(c['result'])
    o.need(state==old['facts']['operator']and state['state']=='complete'and state['phase']=='done'and state['work_order_id']==job['work_order_id']and job['workflow_path']==operator_ref['path']and all(c['state']=='confirmed'for c in state['calls']),'focus-settle-original-complete-WF')
    focus=read(focus_ref);binding=focus['binding'];activation_ref=binding['activation'];activation=read(activation_ref);navigation_ref=unit['navigation'];navigation=read(navigation_ref)
    o.need(focus['kind']=='review-capture-focus-events-v1'and len(focus['events'])==1 and focus['events'][0]['state']=='unknown'and binding['source']==unit['source']and binding['manifest']['path'].startswith(str(Path(unit['source']['path']).parent/'frames')+'/')and binding['scope']=={'tabId':state['tab_id'],'windowId':old['facts']['activation']['binding']['scope']['windowId'],'groupid':state['groupid']}and binding['identity']==state['identity'],'focus-settle-original-focus-binding')
    manifest=o.doc(binding['manifest']);import review_capture as capture
    key=capture.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])})
    o.need(activation['binding']==old['facts']['activation']['binding']and binding['manifest']==activation['binding']['manifest']and binding['url']==activation['binding']['url']and manifest['source']==unit['source']and manifest['job']==unit['job']and manifest['profile']==unit['profile']and manifest['envelope']==unit['envelope']and manifest['page']==unit['page']and manifest['review_keys']==unit['keys'][:len(manifest['review_keys'])]and bool(manifest['review_keys']),'focus-settle-original-manifest-scope')
    o.need(focus_ref['path']==str(Path(unit['source']['path']).parent/'.review-capture-focus'/(key+'.json'))and activation['binding']['manifest']==binding['manifest']and activation['state']=='complete'and len(activation['calls'])==1 and activation['calls'][0]['state']=='confirmed'and activation['binding']['workflow']==operator_ref,'focus-settle-original-activation-complete')
    event=focus['events'][0];stage=event.get('window_focus');o.need(stage and stage['state']=='unknown'and stage['action']=='AXRaise-exact-existing-Chrome-window-v1'and not event.get('native_focus')and len(event['calls'])==1 and event['calls'][0]['state']=='confirmed'and event['calls'][0]['command']=={'op':'activate','tabId':state['tab_id']}and stage.get('reply')and stage.get('effect_checks'),'focus-settle-owned-unknown-stage')
    path=o.PROJECT/'skills/negative-review-complaints/scripts/review_capture_focus.py';source=next(r for r in old['facts']['historical_code_refs']if r['path']==str(path))
    _focus_settle_validate(source,focus,binding)
    reply=o.doc(stage['reply']);o.need(reply.get('result')=={'target':stage['target'],'request_accepted':True,'effect_verified':False,'launch_used':False},'focus-settle-accepted-not-effect-authority')
    o.need(navigation==old['facts']['navigation']and navigation['calls']and all(c['state']=='confirmed'for c in navigation['calls']),'focus-settle-navigation-unchanged')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);o.need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json')and worker['returncode']==0 and worker['attempt_id']==response['attempt_id']==request['attempt_id']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and request['context']['order']==response['context']['order']==parent['order']and request['task']['outer']==old['facts']['outer']and request['task']['id']==old['facts']['task_id'],'focus-settle-natural-worker')
    return {'kind':FOCUS_SETTLE_KIND,'originals':[parent_ref,engine_ref,operator_ref,navigation_ref,focus_ref,activation_ref],'parent':parent,'engine':engine,'operator':state,'navigation':navigation,'focus':focus,'activation':activation,'worker_exit':worker_ref,'previous_proof':previous,'readonly_source':source,'failed_calls':[*prior['failed_calls'],child],'historical_code_refs':old['facts']['historical_code_refs'],'order':parent['order'],'outer':request['task']['outer'],'task_id':request['task']['id'],'qualification':'known-original-input-UNKNOWN-only-readonly-settlement-permitted-not-effect-verified'}
_focus_settle_facts=_hm_history(_focus_settle_facts)
def plan_existing_window_readonly(parent_ref,engine_ref,operator_ref,worker_ref,focus_ref):return _focus_settle_facts(parent_ref,engine_ref,operator_ref,worker_ref,focus_ref)
def _focus_settle_delta(facts,proof_ref):
    parent,engine=_record_choice_delta(facts,proof_ref)
    for value,before in((parent,facts['parent']),(engine,facts['engine'])):value[FOCUS_SETTLE_FIELD]=value.pop(RECORD_CHOICE_FIELD);value[RECORD_CHOICE_FIELD]=before[RECORD_CHOICE_FIELD]
    return parent,engine

def verify_existing_window_readonly(current,proof_ref):
    p=o.doc(proof_ref);facts=p['facts'];base=phase_directory(facts['parent'])/'.existing-window-readonly-settlement'/facts['originals'][0]['sha256'];archives=p['original_archives']
    o.need(p['kind']==FOCUS_SETTLE_KIND and proof_ref['path']==str(base/'proof.json')and current.get(FOCUS_SETTLE_FIELD)==proof_ref,'focus-settle-proof')
    for pair in archives:o.need(pair['archive']=={'path':str(base/'originals'/(pair['original']['sha256']+'.json')),'sha256':pair['original']['sha256']},'focus-settle-original-archive');o.raw(pair['archive'])
    derived=_focus_settle_facts(*facts['originals'][:3],facts['worker_exit'],facts['originals'][4],archives=archives);o.need(derived==facts,'focus-settle-derived-proof');parent,engine=_focus_settle_delta(facts,proof_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls'],'focus-settle-parent-prefix')
    live=o.doc(o.ref(phase_directory(current)/'engine.json'));state=o.doc(o.ref(facts['originals'][2]['path']));nav=o.doc(o.ref(facts['originals'][3]['path']));focus=o.doc(o.ref(facts['originals'][4]['path']));before=facts['focus'];old_event=before['events'][0];event=focus['events'][0]
    o.need(live.get(FOCUS_SETTLE_FIELD)==proof_ref and live['order']==engine['order']and live['scope_sha256']==engine['scope_sha256']and live['calls'][:len(engine['calls'])]==engine['calls']and live['resolved_readonly_failures'][:len(engine['resolved_readonly_failures'])]==engine['resolved_readonly_failures'],'focus-settle-engine-prefix')
    o.need(state['calls'][:len(facts['operator']['calls'])]==facts['operator']['calls']and all(state.get(k)==facts['operator'].get(k)for k in('work_order_id','fingerprint','company','groupid','identity','date_range','tab_id'))and nav['calls'][:len(facts['navigation']['calls'])]==facts['navigation']['calls']and nav['fingerprint']==facts['navigation']['fingerprint'],'focus-settle-WF-nav-prefix')
    o.need(focus['binding']==before['binding']and event['calls']==old_event['calls']and all(event['window_focus'].get(k)==old_event['window_focus'].get(k)for k in('binding','before','target','intent_at','action','reply'))and event['window_focus'].get('effect_checks',[])[:len(old_event['window_focus']['effect_checks'])]==old_event['window_focus']['effect_checks'],'focus-settle-original-UNKNOWN-input-preserved')
    _focus_settle_validate(facts['readonly_source'],focus,focus['binding'])
    execution=_role_execution_sources(facts['historical_code_refs'],installed=True);o.raw(facts['readonly_source'])
    return {'kind':FOCUS_SETTLE_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proof_ref,facts['previous_proof'],facts['worker_exit'],facts['readonly_source'],*[a['archive']for a in archives],*execution['evidence']]}
_FOCUS_SETTLE_PREVIOUS_PREENGINE=verify_preengine_constructor
def verify_preengine_constructor(current,proof_ref,*,installed=True):
    if current.get(FOCUS_SETTLE_FIELD):
        o.need(installed and current[PREENGINE_FIELD]==proof_ref,'focus-settle-prior-marker');return verify_existing_window_readonly(current,current[FOCUS_SETTLE_FIELD])
    return _FOCUS_SETTLE_PREVIOUS_PREENGINE(current,proof_ref,installed=installed)

def recover_existing_window_readonly(parent_ref,engine_ref,operator_ref,worker_ref,focus_ref,*,guard,checkpoint=lambda stage:None):
    """Outer4 caller; self parent lock. Archive UNKNOWN, only engine/parent CAS."""
    import complaint_execution_launcher as launcher
    o.need(callable(guard),'focus-settle-guard');base=Path(parent_ref['path']).parent/'.existing-window-readonly-settlement'/parent_ref['sha256'];args=[parent_ref,engine_ref,operator_ref,worker_ref,focus_ref]
    with Path(parent_ref['path']).with_name('launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked');ip=base/'intent.json';pp=base/'proof.json'
        if ip.exists():
            intent=o.doc(o.ref(ip));o.need(intent['args']==args and intent['kind']==FOCUS_SETTLE_KIND,'focus-settle-same-intent');archives=intent['original_archives'];facts=_focus_settle_facts(*args,archives=archives);o.need(facts==intent['facts'],'focus-settle-same-facts')
        else:
            facts=_focus_settle_facts(*args);archives=[{'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))}for r in facts['originals']];o.immutable(ip,{'kind':FOCUS_SETTLE_KIND,'args':args,'facts':facts,'original_archives':archives})
        value={'kind':FOCUS_SETTLE_KIND,'facts':facts,'original_archives':archives}
        if pp.exists():proof_ref=o.ref(pp);o.need(o.doc(proof_ref)==value,'focus-settle-existing-proof')
        else:proof_ref=o.immutable(pp,value)
        checkpoint('proof');parent,engine=_focus_settle_delta(facts,proof_ref)
        for name,r,b,a in(('engine',engine_ref,facts['engine'],engine),('parent',parent_ref,facts['parent'],parent)):
            guard('before-'+name+'-CAS');current=o.doc(o.ref(r['path']));o.need(current in(b,a),'focus-settle-CAS-third-state')
            if current==b:o.need(o.ref(r['path'])==r,'focus-settle-CAS-before');launcher.save(Path(r['path']),a)
            checkpoint(name)
        verify_existing_window_readonly(o.doc(o.ref(parent_ref['path'])),proof_ref);guard('readback');return {'state':'reconciled','proof':proof_ref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'focus_UNKNOWN_unchanged':focus_ref,'workflow_unchanged':operator_ref,'new_inputs':0,'effect_verified':False}

# Narrow immutable successor to the already reviewed W68 business material.
_ROLE_ROOT_BODY_SUCCESSOR={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/W68-body-root-selector-candidate/CONTRACT.json', 'sha256': 'ffe0b59c8ff536cf1f9652294ae0b9b9c77bac01e7ff75867878a145804b9408'}
_W68_PRIOR_BUSINESS_SOURCE=_reviewed_w68_business_source
def _reviewed_w68_business_source(reference):
 path=o.PROJECT/'skills/chrome-dom-export/scripts/business_cells_capture.py'
 if reference['path']!=str(path):return _W68_PRIOR_BUSINESS_SOURCE(reference)
 value=o.doc(_ROLE_ROOT_BODY_SUCCESSOR);old=o.doc(value['prior_business_contract']);row=next(r for r in old['targets']if r['target']==str(path));new=value['targets'][0]
 o.need(value['kind']=='W68-reviewed-source-root-body-selector-successor-v1'and len(value['targets'])==1 and new['target']==str(path)and new['mode']==420 and value['original_before']==row['before']and value['previous_payload']==row['payload']and new['before']['sha256']==row['payload']['sha256']and reference=={'path':str(path),'sha256':row['before']['sha256']},'role-body-exact-original-and-successor')
 o.need(o.raw(new['before'])==o.raw(row['payload']),'role-body-archived-predecessor');o.raw(row['before']);o.raw(new['payload']);current=o.ref(path);o.need(current['sha256']==new['payload']['sha256']and path.stat().st_mode&0o777==420,'role-body-exact-current');o.raw(current)
 return {'historical':reference,'current':current,'material':row['before'],'dependencies':[_ROLE_ROOT_BODY_SUCCESSOR,value['prior_business_contract'],row['before'],row['payload'],new['before'],new['payload'],current]}

# The existing readiness entry also accepts a first, ordinary loading hold.
# It has no historical initialization/source-release prerequisite and uses one
# existing continuation record for parent, engine and workflow, without nesting.
def _current_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives=()):
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref))
    if engine.get('error')=='record-type-not-active':return _current_record_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives)
    if engine.get('error')in('bridge-command-failed: configured-company-admission-rejected','complaint-parent-original-acquisition-held'):return _current_preenqueue_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives)
    if engine.get('error')in(FOCUS_SETTLE_ERROR,'review-pinned-document-changed','overlay-hover-reply-failed'):return _current_window_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives)
    folder=phase_directory(parent);order=o.validate(parent['order'])
    o.need(not any(parent.get(k)for k in (FIELD,PREENGINE_FIELD,EXPECTED_FILTER_FIELD,'company_scope_reconciliation')),'current-filter-ordinary-parent-required')
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and parent['calls'],'current-filter-parent-frontier')
    o.need(engine['status']=='hold'and engine.get('error')==FILTER_ERROR and engine['phase']=='collect'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256'],'current-filter-engine-frontier')
    previous=parent['start_monotonic']
    for i,call in enumerate(parent['calls']):
        o.need(call['state']=='returned'and call['launch']['path']==str(folder/'children'/(str(i).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(i).zfill(4)+'-exit.json')),'current-filter-natural-child-required')
        launch,exit=read(call['launch']),read(call['result'])
        o.need(launch['index']==i and launch['order']==parent['order']and exit['launch']==call['launch']and exit['argv']==launch['argv']==call['argv']and previous<=launch['launched_monotonic']<=exit['exited_monotonic'],'current-filter-child-binding')
        o.need(exit['returncode']==(2 if i==len(parent['calls'])-1 else 0),'current-filter-no-other-child-failure');previous=exit['exited_monotonic']
    o.need(exit['stderr']==''and json.loads(exit['stdout'])=={'ok':False,'error':FILTER_ERROR},'current-filter-exact-readonly-failure')
    ci=engine['index'];failed=engine['calls'][-1];ctx=failed['context'];artifacts=engine['companies'][ci]['artifacts'];jobref=artifacts['unit_artifacts']['work_order'];job=read(jobref)
    o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('error')==FILTER_ERROR and not failed.get('result')and not failed.get('applied')and failed['company_index']==ci and ctx['artifacts']==artifacts and ctx['order']==order and ctx['company']==order['companies'][ci],'current-filter-resultless-collect')
    for call in engine['calls'][:-1]:o.need(call['state']=='returned'and call.get('applied')is True,'current-filter-no-other-engine-failure');read(call['result'])
    o.need(jobref['path']==job['work_order_path']and operator_ref['path']==job['workflow_path']and operator_ref['path']in artifacts['journals']and state['state']=='running'and state['phase']=='verifyFilter'and state['work_order_id']==job['work_order_id']and state['company']==ctx['company']['company']==job['company']and str(state['groupid'])==str(job['groupid'])==str(ctx['company']['groupid'])and state['tab_id']==parent['tab_id'],'current-filter-operator-binding')
    o.need(state.get('last_error',{}).get('code')==state['last_error'].get('message')==FILTER_ERROR and not state.get('confirmed_filter_readonly_recovery')and not any(state.get(k)for k in ('exportPending','downloadPending','result','record_tab_id')),'current-filter-no-postfilter-effects')
    calls=state['calls'];tail=calls[-5:];o.need(len(calls)==5 and all(c['state']=='confirmed'for c in calls)and [c['phase']for c in tail]==['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'],'current-filter-confirmed-filter-prefix')
    o.need(type(ready_inputs)is dict and set(ready_inputs)=={'response','intent'},'current-filter-ready-inputs');intent=read(ready_inputs['intent']);response=read(ready_inputs['response'])
    o.need(intent['original']==operator_ref and intent['business_inputs']==0 and intent['max_requests']==1 and response.get('ok')is True,'current-filter-observation-binding')
    sys.path.insert(0,str(o.PROJECT/'packages/workshop-director'))
    from workshop_director import filter_readiness_recovery as provider
    from switch_read_recovery import fingerprint
    o.need(state['fingerprint']==fingerprint(job),'current-filter-fingerprint')
    reads=state['review_filter_loading_reads'];o.need(len(reads)==3 and [r['attempt']for r in reads]==[0,1,2],'current-filter-spent-read-budget')
    previous_tree=None;pending=None
    for row in reads:
        reply=read(row['reply']);o.need(reply.get('ok')is True and read(row['tree'])==reply['result']['tree'],'current-filter-original-observation')
        found=provider.scope(job,state,reply['result'],read,pending=True)
        o.need(pending in (None,found)and row['command']=={'op':'readonly-scope','tabId':state['tab_id'],'windowId':found['window_id']},'current-filter-original-scope')
        if previous_tree is not None:o.need(row['before_tree']==previous_tree,'current-filter-read-chain')
        else:
            initial=read(row['before_tree']);dom,_,loading=provider.modules();dom.identity(initial,job['identity_baseline']);loading.validate_filter_values(initial,state['date_range']);loading.validate_pending_store_scope(initial);o.need(loading.is_loading(initial),'current-filter-original-pending')
        pending=found;previous_tree=row['tree']
    o.need(state['last_tree']==previous_tree and intent['command']==reads[-1]['command'],'current-filter-final-observation-scope')
    ready=provider.scope(job,state,response['result'],read,pending=False)
    o.need(all(ready[k]==v for k,v in pending.items()if k!='page_filtered'),'current-filter-ready-same-scope')
    worker=read(worker_ref);request=read(worker['request']);response_worker=read(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['attempt_id']==request['attempt_id']and worker['returncode']==0 and response_worker['outcome']=='failed'and response_worker['error']=='parent-hold-inspect-original'and response_worker['task_id']==request['task']['id']and request['context']['order']==response_worker['context']['order']==parent['order'],'current-filter-natural-worker')
    pxref=o.ref(attempt/'parent-run-exit.json');px=read(pxref);output=json.loads(o.raw(px['stdout']));o.need(px['returncode']==0 and output['status']=='hold'and output['error']=='execution-child-stopped'and output['last_child_receipt']==parent['calls'][-1]['result']and not o.raw(px['stderr']),'current-filter-natural-parent-return')
    return {'release':None,'parent':parent,'engine':engine,'operator':state,'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'ready_inputs':ready_inputs,'ready':ready,'failed_calls':[copy.deepcopy(parent['calls'][-1])],'task_id':request['task']['id'],'outer':request['task']['outer']}

def _current_filter_delta(facts,proofref):
    parent,engine,state=copy.deepcopy(facts['parent']),copy.deepcopy(facts['engine']),copy.deepcopy(facts['operator'])
    for value in(parent,engine):
        value['status']='running';value.setdefault('resolved_errors',[]).append({'error':value.pop('error'),'recovery':proofref});value[FIELD]=proofref
    engine.setdefault('resolved_readonly_failures',[]).append({'index':len(engine['calls'])-1,'call':engine['calls'].pop(),'recovery':proofref})
    if not facts.get('window_settle_ready'):
        state.setdefault('resolved_errors',[]).append({**state.pop('last_error'),'next_phase':'verifyFilter','recovery_proof':proofref});
        if not any(facts.get(k)for k in('record_ready','preenqueue_ready','preinput_navigation_ready')):state['confirmed_filter_readonly_recovery']=proofref
    return parent,engine,state

def _verify_current_filter_ready(current,proofref):
    proof=o.doc(proofref);facts=proof['facts'];base=phase_directory(facts['parent'])/'.expected-filter-readiness'/facts['originals'][0]['sha256']
    o.need(proof['kind']==EXPECTED_FILTER_KIND and proofref['path']==str(base/'proof.json')and current.get(FIELD)==proofref,'current-filter-existing-proof-path')
    archives=proof['original_archives'];o.need([a['original']for a in archives]==facts['originals'],'current-filter-original-archives')
    for pair in archives:o.need(pair['archive']['path']==str(base/'originals'/(pair['original']['sha256']+'.json'))and pair['archive']['sha256']==pair['original']['sha256'],'current-filter-original-archive');o.raw(pair['archive'])
    derived=_current_filter_facts(*facts['originals'],facts['worker_exit'],facts['ready_inputs'],archives);o.need(derived==facts,'current-filter-facts-changed')
    parent,engine,state=_current_filter_delta(facts,proofref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need({k:v for k,v in current.items()if k not in variable}=={k:v for k,v in parent.items()if k not in variable}and current['calls'][:len(parent['calls'])]==parent['calls'],'current-filter-parent-prefix')
    actual_engine=o.doc(o.ref(phase_directory(current)/'engine.json'));actual_state=o.doc(o.ref(facts['originals'][2]['path']))
    o.need(actual_engine.get(FIELD)==proofref and actual_engine['order']==engine['order']and actual_engine['calls'][:len(engine['calls'])]==engine['calls']and actual_engine.get('resolved_readonly_failures')==engine['resolved_readonly_failures'],'current-filter-engine-prefix')
    prefix=actual_state['calls'][:len(state['calls'])]
    if facts.get('preenqueue_ready')and prefix!=state['calls']:
        prefix=_current_preenqueue_prefix(facts,actual_state,prefix)
    elif facts.get('preinput_navigation_ready')and prefix!=state['calls']:
        prefix=_current_navigation_prefix(facts,actual_state,prefix)
    fixed=('work_order_id','fingerprint','company','groupid','date_range','tab_id')+(('identity',)if not facts.get('preenqueue_ready')else())
    o.need(actual_state.get('confirmed_filter_readonly_recovery')==state.get('confirmed_filter_readonly_recovery')and actual_state.get('resolved_errors',[])[:len(state.get('resolved_errors',[]))]==state.get('resolved_errors',[])and prefix==state['calls']and all(actual_state.get(k)==state.get(k)for k in fixed),'current-filter-operator-prefix')

    execution=_role_execution_sources(parent['code_refs'],installed=True)
    return {'kind':EXPECTED_FILTER_KIND,'code_refs':execution['code_refs'],'failed_calls':facts['failed_calls'],'evidence':[proofref,*[a['archive']for a in archives],facts['worker_exit'],*facts['ready_inputs'].values(),*execution['evidence']]}

def _recover_current_filter_ready(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,*,guard,checkpoint):
    o.need(callable(guard),'current-filter-locked-guard-required');folder=Path(parent_ref['path']).parent;base=folder/'.expected-filter-readiness'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard('locked')
        pp=base/'proof.json';archives=[]
        if pp.exists():
            proofref=o.ref(pp);proof=o.doc(proofref);archives=proof['original_archives'];facts=_current_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives);o.need(proof['facts']==facts,'current-filter-existing-record')
        else:
            facts=_current_filter_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs)
            o.need(not(folder/'receipts'/(str(len(facts['engine']['calls'])).zfill(5)+'.json')).exists(),'current-filter-result-slot-must-be-absent')
            for r in facts['originals']:archives.append({'original':r,'archive':immutable_bytes(base/'originals'/(r['sha256']+'.json'),o.raw(r))})
            proofref=o.immutable(pp,{'kind':EXPECTED_FILTER_KIND,'facts':facts,'original_archives':archives});checkpoint('record')
        after=_current_filter_delta(facts,proofref)
        for name,r,b,a in zip(('operator','engine','parent'),(operator_ref,engine_ref,parent_ref),(facts['operator'],facts['engine'],facts['parent']),(after[2],after[1],after[0])):
            guard('before-'+name);value=o.doc(o.ref(r['path']));o.need(value in(b,a),'current-filter-third-state')
            if value==b and a!=b:o.need(o.ref(r['path'])==r,'current-filter-before-bytes');import complaint_execution_launcher as launcher;launcher.save(Path(r['path']),a)
            checkpoint(name)
        _verify_current_filter_ready(o.doc(o.ref(parent_ref['path'])),proofref);guard('readback')
        return {'state':'reconciled','proof':proofref,'parent':o.ref(parent_ref['path']),'engine':o.ref(engine_ref['path']),'operator':o.ref(operator_ref['path']),'new_inputs':0}

def _current_window_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives=()):
    """Resume the exact owned capture-window UNKNOWN through the executed
    readonly settlement only. The archived UNKNOWN journal and the completed
    live journal are the sole readiness evidence; no AXRaise, no new native
    or business input, and the completed Chongqing acquisition is unchanged.
    """
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);order=o.validate(parent['order']);prior_ref=parent[FIELD];prior=o.doc(prior_ref);previous=prior['facts']
    o.need(prior['kind']==EXPECTED_FILTER_KIND and previous['release']is None and (previous.get('preinput_navigation_ready')is True or previous.get('window_settle_ready')is True) and prior_ref['path']==str(folder/'.expected-filter-readiness'/previous['originals'][0]['sha256']/'proof.json'),'current-window-accepted-original-record')
    o.need([a['original']for a in prior['original_archives']]==previous['originals'],'current-window-original-archive-list')
    for pair,pkey in zip(prior['original_archives'],('parent','engine','operator')):
        o.need(pair['archive']['path']==str(Path(prior_ref['path']).parent/'originals'/(pair['original']['sha256']+'.json'))and pair['archive']['sha256']==pair['original']['sha256']and o.doc(pair['archive'])==previous[pkey],'current-window-accepted-original-bytes')
    expected,expected_engine,_=_current_filter_delta(previous,prior_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and {k:v for k,v in parent.items()if k not in variable}=={k:v for k,v in expected.items()if k not in variable}and parent['calls'][:-1]==expected['calls'],'current-window-original-parent-prefix')
    o.need(engine.get(FIELD)==prior_ref and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256']and engine['status']=='hold'and engine.get('error')in(FOCUS_SETTLE_ERROR,'review-pinned-document-changed','overlay-hover-reply-failed')and engine['phase']=='collect'and engine['calls'][:len(expected_engine['calls'])]==expected_engine['calls']and engine.get('resolved_readonly_failures')==expected_engine['resolved_readonly_failures'],'current-window-engine-prefix')
    failed=engine['calls'][-1];ci=engine['index'];ctx=failed['context'];a=engine['companies'][ci]['artifacts'];x=a['unit_artifacts']
    o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('error')in(FOCUS_SETTLE_ERROR,'review-pinned-document-changed','overlay-hover-reply-failed')and not failed.get('result')and not failed.get('applied')and failed['company_index']==ci and ctx['order']==order and ctx['company']==order['companies'][ci]and ctx['artifacts']==a and a['unit_phase']=='frames'and x['operations']==[]and x['frame_index']==x['review_index']==0,'current-window-failed-frames-frontier')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True,'current-window-no-other-engine-failure');read(c['result'])
    job=o.doc(x['work_order'])
    o.need(state['state']=='complete'and state['phase']=='done'and all(c['state']=='confirmed'for c in state['calls'])and state['work_order_id']==job['work_order_id']and job['workflow_path']==operator_ref['path'],'current-window-operator-complete')
    mjob=read(x['job']);rec=read({'path':mjob['source_receipt'],'sha256':mjob['source_receipt_sha256']});o.need(str(Path(mjob['source_receipt']).parent/'workflow.json')==operator_ref['path']and rec['workflow_sha256']==operator_ref['sha256']and rec['work_order_id']==job['work_order_id'],'current-window-operator-receipt-pin')
    o.need(type(ready_inputs)is dict and set(ready_inputs)=={'before_focus','settlement'},'current-window-exact-ready-inputs')
    before=read(ready_inputs['before_focus']);settlement=read(ready_inputs['settlement'])
    binding=before['binding'];manifest_ref=binding['manifest'];manifest=read(manifest_ref);key=x['keys'][x['frame_index']]
    expected_manifest={k2:x[k2]for k2 in ('job','source','envelope','profile','page')};expected_manifest.update(review_keys=[key],capture_key='complaint-parent:'+o.digest({'dispatch':order['dispatch_id'],'key':key,'source':x['source']['sha256']})[:40])
    o.need(before['kind']=='review-capture-focus-events-v1'and binding['source']==x['source']and manifest==expected_manifest and manifest_ref['path']==str(Path(x['source']['path']).parent/'frames'/o.digest(key)/'manifest.json'),'current-window-original-frame-manifest')
    import review_capture_focus as focus
    digest=focus.previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])})
    journal=Path(x['source']['path']).parent/'.review-capture-focus'/(digest+'.json');live=o.ref(journal)
    o.need(ready_inputs['before_focus']['path']!=str(journal)and ready_inputs['settlement']['path']!=str(journal),'current-window-refs-not-journal')
    activation=read(binding['activation']);navigation=read(x['navigation'])
    o.need(activation['binding']['manifest']==manifest_ref and activation['state']=='complete'and len(activation['calls'])==1 and activation['calls'][0]['state']=='confirmed'and navigation['calls']and all(c['state']=='confirmed'for c in navigation['calls']),'current-window-activation-navigation-complete')
    o.need(len(before['events'])==1,'current-window-before-sole-event');be=before['events'][0]
    o.need(be['state']=='unknown'and be['window_focus']['state']=='unknown'and not be.get('native_focus')and len(be['calls'])==1 and be['calls'][0]['state']=='confirmed'and be['calls'][0]['command']=={'op':'activate','tabId':binding['scope']['tabId']}and be['window_focus'].get('reply')and be['window_focus'].get('effect_checks'),'current-window-before-owned-unknown')
    o.need(settlement.get('ok')is True and settlement.get('AXRaise_replayed')is False and settlement.get('new_gestures')==1 and settlement['original_focus_effect']['ready']is True and settlement['original_focus_effect']['focus_event']==be['number']and settlement['original_focus_effect']['input_dispatched']is False and settlement['original_focus_effect']['native_input_dispatched']is False and settlement['original_focus_effect']['journal']['path']==str(journal),'current-window-readonly-settlement')
    lv=o.doc(live);o.need(lv['binding']==binding and len(lv['events'])in(1,2),'current-window-live-sole-event');ae=lv['events'][0];bs=be['window_focus'];ws=ae['window_focus']
    o.need(ae['state']=='complete'and ae.get('outcome')=='readonly-original-effect-confirmed'and ws['state']=='complete'and not ae.get('native_focus'),'current-window-readonly-complete')
    stage_changed={'state','after','effect','completed_at','effect_checks'};event_changed={'state','after','completed_at','outcome','window_focus'}
    o.need({k:v for k,v in ws.items()if k not in stage_changed}=={k:v for k,v in bs.items()if k not in stage_changed}and {k:v for k,v in ae.items()if k not in event_changed}=={k:v for k,v in be.items()if k not in event_changed}and ws.get('effect_checks',[])[:len(bs.get('effect_checks',[]))]==bs.get('effect_checks',[]),'current-window-original-input-history')
    if len(lv['events'])==2:
        restore=lv['events'][1]
        o.need(restore['number']==be['number']+1 and restore['binding']==binding and restore['state']=='complete'and restore.get('outcome')=='focus-restore-confirmed'and restore.get('window_focus')is None and not restore.get('native_focus')and len(restore['calls'])==1 and restore['calls'][0]['state']=='confirmed'and restore['calls'][0]['command'].get('op')=='activate','current-window-typed-focus-restore')
    focus.validate_events(before,binding);focus.validate_events(lv,binding);focus.validate_window_stage(ae,binding)
    prev=parent['start_monotonic']
    for i,call in enumerate(parent['calls']):
        o.need(call['state']=='returned'and call['launch']['path']==str(folder/'children'/(str(i).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(i).zfill(4)+'-exit.json')),'current-window-natural-child')
        launch,exit=map(read,(call['launch'],call['result']));o.need(launch['index']==i and launch['order']==parent['order']and exit['launch']==call['launch']and call['argv']==launch['argv']==exit['argv']and prev<=launch['launched_monotonic']<=exit['exited_monotonic'],'current-window-child-binding');prev=exit['exited_monotonic'];approved=call in previous['failed_calls']or i==len(parent['calls'])-1;o.need(exit['returncode']==(2 if approved else 0),'current-window-no-other-child-failure')
    o.need(exit['stderr']==''and json.loads(exit['stdout'])in({'ok':False,'error':FOCUS_SETTLE_ERROR},{'ok':False,'error':'review-pinned-document-changed'},{'ok':False,'error':'overlay-hover-reply-failed'}),'current-window-exact-natural-failure')
    worker=read(worker_ref);request=read(worker['request']);result=read(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['returncode']==0 and worker['attempt_id']==result['attempt_id']==request['attempt_id']and result['task_id']==request['task']['id']and result['outcome']=='failed'and result['error']=='parent-hold-inspect-original'and result['context']['order']==request['context']['order']==parent['order'],'current-window-original-worker')
    return {'release':None,'window_settle_ready':True,'parent':parent,'engine':engine,'operator':state,'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'ready_inputs':ready_inputs,'ready':{'focus_event':be['number']},'failed_calls':previous['failed_calls']+[copy.deepcopy(parent['calls'][-1])],'task_id':request['task']['id'],'outer':request['task']['outer']}

def _current_record_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives=()):
    """Continue the confirmed export; carry the first readonly failure as facts.
    The original readiness record is checked directly, not a recursive chain of
    later recoveries. No submitted export or reload may be repeated.
    """
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);order=o.validate(parent['order']);origin_ref=parent[FIELD];origin=o.doc(origin_ref);first=origin['facts']
    o.need(origin['kind']==EXPECTED_FILTER_KIND and first['release']is None and not first.get('record_ready')and first['originals'][0]['path']==parent_ref['path'],'current-record-first-readonly-origin')
    o.need(_current_filter_facts(*first['originals'],first['worker_exit'],first['ready_inputs'],origin['original_archives'])==first,'current-record-original-readonly-facts')
    expected,expected_engine,_=_current_filter_delta(first,origin_ref)
    variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and {k:v for k,v in parent.items()if k not in variable}=={k:v for k,v in expected.items()if k not in variable}and parent['calls'][:-1]==expected['calls']and parent['status']=='hold'and parent.get('error')=='execution-child-stopped','current-record-original-parent-prefix')
    o.need(engine.get(FIELD)==origin_ref and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256']and engine['status']=='hold'and engine.get('error')=='record-type-not-active'and engine['phase']=='collect'and engine['calls'][:len(expected_engine['calls'])]==expected_engine['calls']and engine.get('resolved_readonly_failures')==expected_engine['resolved_readonly_failures'],'current-record-engine-prefix')
    failed=engine['calls'][-1];ci=engine['index'];ctx=failed['context'];artifacts=engine['companies'][ci]['artifacts'];jobref=artifacts['unit_artifacts']['work_order'];job=read(jobref)
    o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('error')=='record-type-not-active'and not failed.get('result')and not failed.get('applied')and ctx['order']==order and ctx['company']==order['companies'][ci]and ctx['artifacts']==artifacts and failed['company_index']==ci,'current-record-readonly-engine-frontier')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True,'current-record-no-other-engine-failure');read(c['result'])
    o.need(jobref['path']==job['work_order_path']and operator_ref['path']==job['workflow_path']and operator_ref['path']in artifacts['journals']and job['company']==ctx['company']['company']and str(job['groupid'])==str(ctx['company']['groupid']),'current-record-company-binding')
    import export_record_page_recovery as record
    scope=record._postsubmit_contract(job,state,'record-type-not-active');o.need(record.is_loading(read(state['last_tree'])),'current-record-known-loading-header')
    o.need(type(ready_inputs)is dict and set(ready_inputs)=={'response','intent'},'current-record-observation-inputs');intent,response=map(read,(ready_inputs['intent'],ready_inputs['response']))
    o.need(intent['original']==operator_ref and intent['business_inputs']==0 and intent['max_requests']==1 and intent['command']=={'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']}and response.get('ok')is True,'current-record-once-observation')
    from readonly_tick_snapshot import decode
    import dom_evidence as dom
    value=decode(response['result'],scope['tab_id'],scope['window_id'])
    for side in ('before','after'):
        actual=dom.context(value[side],scope['tab_id'],job['groupid'],record=True);o.need(actual['url']==scope['url']and actual['windowId']==scope['window_id'],'current-record-observed-scope')
    o.need(value['ping']['version']==dom.VERSION and value['ping']['safety']=='DOM-only'and value['tree']['url']==scope['url'].split('?')[0],'current-record-observed-source')
    ready=dom.submitted_export_record(value['tree'],state['date_range'],state['baseline_records'],state['submitted_at']);o.need(ready['row']and ready['row']['state']=='success','current-record-original-export-not-ready')
    previous=parent['start_monotonic']
    for i,call in enumerate(parent['calls']):
        o.need(call['state']=='returned'and call['launch']['path']==str(folder/'children'/(str(i).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(i).zfill(4)+'-exit.json')),'current-record-natural-child')
        launch,exit=map(read,(call['launch'],call['result']));o.need(launch['index']==i and launch['order']==parent['order']and exit['launch']==call['launch']and call['argv']==launch['argv']==exit['argv']and previous<=launch['launched_monotonic']<=exit['exited_monotonic'],'current-record-natural-child-binding');previous=exit['exited_monotonic']
        approved=call in first['failed_calls']or i==len(parent['calls'])-1;o.need(exit['returncode']==(2 if approved else 0),'current-record-no-other-child-failure')
    o.need(exit['stderr']==''and json.loads(exit['stdout'])=={'ok':False,'error':'record-type-not-active'},'current-record-natural-last-error')
    worker=read(worker_ref);request=read(worker['request']);result=read(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['returncode']==0 and worker['attempt_id']==result['attempt_id']==request['attempt_id']and result['task_id']==request['task']['id']and result['outcome']=='failed'and result['error']=='parent-hold-inspect-original'and result['context']['order']==request['context']['order']==parent['order'],'current-record-original-worker')
    return {'release':None,'record_ready':True,'parent':parent,'engine':engine,'operator':state,'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'ready_inputs':ready_inputs,'ready':ready,'failed_calls':first['failed_calls']+[copy.deepcopy(parent['calls'][-1])],'task_id':request['task']['id'],'outer':request['task']['outer']}

def _current_preenqueue_facts(parent_ref,engine_ref,operator_ref,worker_ref,ready_inputs,archives=()):
    """Reuse the accepted continuation; the SDK alone grants exact no-enqueue renewal.
    No recursive previous recovery replay and no input/phase/key replacement.
    """
    mapped={(a['original']['path'],a['original']['sha256']):a['archive']for a in archives}
    def read(r):return o.doc(mapped.get((r['path'],r['sha256']),r))
    parent,engine,state=map(read,(parent_ref,engine_ref,operator_ref));folder=phase_directory(parent);order=o.validate(parent['order']);prior_ref=parent[FIELD];prior=o.doc(prior_ref);previous=prior['facts']
    navigation=engine.get('error')=='complaint-parent-original-acquisition-held'
    o.need(prior['kind']==EXPECTED_FILTER_KIND and previous['release']is None and previous.get('preenqueue_ready'if navigation else'record_ready')is True and prior_ref['path']==str(folder/'.expected-filter-readiness'/previous['originals'][0]['sha256']/'proof.json'),'current-preenqueue-accepted-original-record')
    o.need([a['original']for a in prior['original_archives']]==previous['originals'],'current-preenqueue-original-archive-list')
    for pair,key in zip(prior['original_archives'],('parent','engine','operator')):
        o.need(pair['archive']['path']==str(Path(prior_ref['path']).parent/'originals'/(pair['original']['sha256']+'.json'))and pair['archive']['sha256']==pair['original']['sha256']and o.doc(pair['archive'])==previous[key],'current-preenqueue-accepted-original-bytes')
    expected,expected_engine,_=_current_filter_delta(previous,prior_ref);variable={'status','error','calls','child','completion','end_monotonic','wall_ended_at','acceptance_pass'}
    o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json')and parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and {k:v for k,v in parent.items()if k not in variable}=={k:v for k,v in expected.items()if k not in variable}and parent['calls'][:-1]==expected['calls'],'current-preenqueue-original-parent-prefix')
    error='complaint-parent-original-acquisition-held'if navigation else'bridge-command-failed: configured-company-admission-rejected'
    o.need(engine.get(FIELD)==prior_ref and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']==order['scope_sha256']and engine['status']=='hold'and engine.get('error')==error and engine['phase']=='collect'and engine['calls'][:len(expected_engine['calls'])]==expected_engine['calls']and engine.get('resolved_readonly_failures')==expected_engine['resolved_readonly_failures'],'current-preenqueue-engine-prefix')
    failed=engine['calls'][-1];ci=engine['index'];ctx=failed['context'];a=engine['companies'][ci]['artifacts'];jobref=state['company_configuration_job'];job=read(jobref)
    o.need(failed.get('state')=='failed'and failed.get('step')=='collect'and failed.get('error')==error and not failed.get('result')and not failed.get('applied')and failed['company_index']==ci and ctx['order']==order and ctx['company']==order['companies'][ci]and ctx['artifacts']==a and jobref['path']==job['work_order_path']and operator_ref['path']==job['workflow_path']and Path(jobref['path']).parent.parent.parent==folder/'companies'/str(ci)/'units'/str(a['unit_index'])and a['unit_phase']=='acquire'and job['company']==ctx['company']['company']and str(job['groupid'])==str(ctx['company']['groupid']),'current-preenqueue-failed-collect')
    for c in engine['calls'][:-1]:o.need(c['state']=='returned'and c.get('applied')is True,'current-preenqueue-no-other-engine-failure');read(c['result'])
    import importlib.util
    path=o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py';spec=importlib.util.spec_from_file_location('_existing_sdk_preenqueue_policy',path);sdk=importlib.util.module_from_spec(spec);spec.loader.exec_module(sdk);w=sdk.Workflow.__new__(sdk.Workflow);w.file=Path(operator_ref['path']);w.s=copy.deepcopy(state);w.job=job
    entry=w.review_tab_zero_match()if navigation else w.preenqueue_recovery_entry();phase='openReviews'if navigation else'searchCompany'
    o.need(entry is not None and state.get('phase')==phase and state.get('tab_id')==parent['tab_id']and state['work_order_id']==job['work_order_id']and sdk.fingerprint(job)==state['fingerprint'],'current-preenqueue-sdk-exact-no-delivery')
    if navigation:
        o.need(ready_inputs=={}and state.get('last_error',{}).get('message')=='bridge-command-failed: ambiguous-or-missing: 0 visible matches; inspect and scope selector, never guess','current-navigation-exact-last-error')
    else:
        o.need(state.get('last_error',{}).get('message')==error and set(ready_inputs)=={'service_refresh'},'current-preenqueue-refresh-input');refresh=read(ready_inputs['service_refresh']);intent=read(refresh['intent'])
        o.need(refresh.get('kind')=='original-bridge-reload-completed-v1'and refresh.get('old_exited')is True and refresh.get('status',{}).get('reviewedExtensionReady')is True and refresh['workflow_unchanged']==intent['preenqueue_workflow']==operator_ref and refresh['chrome_unchanged']==intent['chrome_unchanged']and refresh['new_process']['boot']==parent['boot_identity'],'current-preenqueue-original-service-refresh')
    prev=parent['start_monotonic']
    for i,call in enumerate(parent['calls']):
        o.need(call['state']=='returned'and call['launch']['path']==str(folder/'children'/(str(i).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(i).zfill(4)+'-exit.json')),'current-preenqueue-natural-child')
        launch,exit=map(read,(call['launch'],call['result']));o.need(launch['index']==i and launch['order']==parent['order']and exit['launch']==call['launch']and call['argv']==launch['argv']==exit['argv']and prev<=launch['launched_monotonic']<=exit['exited_monotonic'],'current-preenqueue-child-binding');prev=exit['exited_monotonic'];approved=call in previous['failed_calls']or i==len(parent['calls'])-1;o.need(exit['returncode']==(2 if approved else 0),'current-preenqueue-no-other-child-failure')
    o.need(exit['stderr']==''and json.loads(exit['stdout'])=={'ok':False,'error':error},'current-preenqueue-exact-natural-failure')
    worker=read(worker_ref);request=read(worker['request']);result=read(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['returncode']==0 and worker['attempt_id']==result['attempt_id']==request['attempt_id']and result['task_id']==request['task']['id']and result['outcome']=='failed'and result['error']=='parent-hold-inspect-original'and result['context']['order']==request['context']['order']==parent['order'],'current-preenqueue-original-worker')
    value={'release':None,'preenqueue_ready':True,'parent':parent,'engine':engine,'operator':state,'originals':[parent_ref,engine_ref,operator_ref],'worker_exit':worker_ref,'ready_inputs':ready_inputs,'ready':{'phase':phase,'call_key':entry['key']},'failed_calls':previous['failed_calls']+[copy.deepcopy(parent['calls'][-1])],'task_id':request['task']['id'],'outer':request['task']['outer']}
    if navigation:value.pop('preenqueue_ready');value['preinput_navigation_ready']=True;value['ready']['owned_preinput_source']=entry['preinput_navigation_source']
    else:value['ready']['owned_pre_enqueue_refusal']=entry['pre_enqueue_rejection']
    return value

def _current_preenqueue_prefix(facts,current,prefix):
    original=facts['operator'];before=original['calls'][-1];o.need(prefix[:-1]==original['calls'][:-1]and len(prefix)==len(original['calls']),'current-preenqueue-stable-prefix');entry=prefix[-1];continuation=entry.get('pre_enqueue_operation_continuation',{})
    o.need(entry.get('pre_enqueue_original')==before and entry.get('pre_enqueue_recovery_attempted')is True and entry.get('key')==before['key']and entry.get('phase')==before['phase']and entry.get('pre_enqueue_rejection')==before['pre_enqueue_rejection']and continuation.get('kind')=='owned-undelivered-operation-successor-v1'and continuation.get('predecessor')==before['command']['companyRequest']and continuation.get('successor')==entry['command']['companyRequest'],'current-preenqueue-owned-successor')
    o.need({k:v for k,v in entry['command'].items()if k!='companyRequest'}=={k:v for k,v in before['command'].items()if k!='companyRequest'},'current-preenqueue-same-command')
    old,new=map(o.doc,(continuation['predecessor'],continuation['successor']));variable={'issued_at','expires_at'};o.need({k:v for k,v in old.items()if k not in variable}=={k:v for k,v in new.items()if k not in variable},'current-preenqueue-same-operation')
    issued,expired,new_issued,new_expired=(datetime.fromisoformat(v)for v in(old['issued_at'],old['expires_at'],new['issued_at'],new['expires_at']));o.need(issued<expired<=new_issued<new_expired and new_expired-new_issued==expired-issued,'current-preenqueue-renewal-time-budget')
    jobref=facts['operator']['company_configuration_job'];job=o.doc(jobref);o.need(current.get('identity')in(original.get('identity'),job['identity_baseline']),'current-preenqueue-company-identity');o.raw(continuation['scope'])
    return prefix[:-1]+[copy.deepcopy(before)]

def _current_navigation_prefix(facts,current,prefix):
    original=facts['operator'];before=original['calls'][-1];o.need(len(prefix)==len(original['calls'])and prefix[:-1]==original['calls'][:-1],'current-navigation-stable-prefix');entry=prefix[-1]
    o.need(entry.get('preinput_navigation_original')==before and entry.get('preinput_navigation_recovery_attempted')is True and entry.get('key')==before['key']and entry.get('phase')==before['phase']and entry.get('preinput_navigation_source')==before['preinput_navigation_source']and {k:v for k,v in entry['command'].items()if k!='locator'}=={k:v for k,v in before['command'].items()if k!='locator'},'current-navigation-once-owned-prefix')
    from readonly_tick_snapshot import decode
    import dom_evidence as dom
    value=o.doc(entry['preinput_navigation_scope']);value=decode(value,current['tab_id'],value['scope']['windowId']);job=o.doc(original['company_configuration_job']);left=dom.context(value['before'],current['tab_id'],job['groupid']);right=dom.context(value['after'],current['tab_id'],job['groupid']);target=dom.all_reviews(value['tree'])
    o.need(left==right and value['tree']['url']=='https://life.douyin.com/p/life_comment/management'and target.get('tag')=='span'and target.get('attributes',{}).get('class')=='byted-tab-bar-item-label'and entry['command']['locator']=={'by':'selector','value':target['selector']}and current['identity']==job['identity_baseline'],'current-navigation-fresh-observed-label')
    return prefix[:-1]+[copy.deepcopy(before)]
