"""Exact zero-business constructor recovery; metadata only, no engine/UI entry."""
import argparse,copy,fcntl,hashlib,json,os,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
import role_execution_order as o
FIELD='violation_initial_ledger_recovery'
KIND='verified-violation-initial-ledger-reference-recovery-v1'
ERROR='execution-ledger-changed-before-start'
NAMES={'violation_execution_ports.py':'skills/violation-notifier/scripts/violation_execution_ports.py','role_execution_launcher.py':'skills/workshop-director/scripts/role_execution_launcher.py','role_execution_orchestration.py':'skills/workshop-director/scripts/role_execution_orchestration.py','violation_initial_ledger_recovery.py':'skills/violation-notifier/scripts/violation_initial_ledger_recovery.py'}
GROUPS={'烟台一成教育文化咨询有限公司':'1767942028615694','上海老芗汇餐饮管理有限公司':'1764303851132943'}
def _recovery_checkpoint(stage):
    """Default metadata checkpoint; fixed module binding, no captured state."""
    return None
def paths():return {n:str(o.PROJECT/p) for n,p in NAMES.items()}
def stamp():return datetime.now(timezone.utc).isoformat()
def live_lease(order):
    import director
    state=o.doc(o.ref(o.PROJECT/'runtime/workshop-director/state.json'))
    o.need(state.get('phase')=='running' and state.get('day')==order['day'] and state.get('dispatch_id')==order['dispatch_id'] and director.current(state).get('role')==o.ROLE and any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in state.get('events',[])),'violation-initial-current-acknowledged-lease')
def immutable_bytes(path,b):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);o.canonical(path)
    if path.exists():o.need(path.read_bytes()==b,'violation-initial-archive-conflict');return o.ref(path)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:o.need(path.read_bytes()==b,'violation-initial-archive-conflict')
    finally:os.unlink(tmp)
    return o.ref(path)
def ledger_facts(order,*,live):
    rows=[]
    for c in order['companies']:
        name=c['company'];root=o.PROJECT/'runtime'/o.FLOW/name;o.need(name in GROUPS and c['groupid']==GROUPS[name] and c['root']==str(root),'violation-initial-company-root')
        raw=o.raw(c['ledger']);s=json.loads(raw);o.need(s.get('company')==name and str(s.get('groupid'))==GROUPS[name] and s.get('mode')=='development' and s.get('browser_backend')=='local-dom-bridge','violation-initial-ledger-content')
        current={'path':str(root/'state.json'),'sha256':c['ledger']['sha256']}
        if live:o.need(o.raw(current)==raw,'violation-initial-live-ledger-changed')
        rows.append({'company':name,'groupid':c['groupid'],'canonical':current,'snapshot':c['ledger']})
    o.need(len(rows)==2 and {r['company'] for r in rows}==set(GROUPS),'violation-initial-two-companies')
    return rows
def original_contract(parent,worker_ref,*,live):
    order=o.validate(parent['order']);folder=o.location(parent['order']);o.need(parent['kind']=='role-execution-launcher-v1' and parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and parent.get('mode')=='acceptance' and parent.get('origin')=='fresh' and not parent.get('child') and not parent.get('completion') and FIELD not in parent,'violation-initial-exact-constructor-hold')
    origin=o.doc(parent['origin_ref']);o.need(all(parent.get(k)==v for k,v in origin.items()),'violation-initial-origin-changed')
    o.need(len(parent['calls'])==1 and parent['calls'][0]['state']=='returned','violation-initial-sole-child')
    call=parent['calls'][0];o.need(Path(call['launch']['path'])==folder/'children/0000-launch.json' and Path(call['result']['path'])==folder/'children/0000-exit.json','violation-initial-canonical-child')
    la=o.doc(call['launch']);ex=o.doc(call['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(call['argv']==la['argv']==ex['argv']==argv and la['order']==parent['order'] and la['index']==0 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':ERROR},'violation-initial-exact-local-failure')
    o.need(parent['start_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-initial-clock-order')
    if live:o.need(not (folder/'engine.json').exists() and not (folder/'engine.json').is_symlink() and not (folder/'companies').exists() and not (folder/'companies').is_symlink(),'violation-initial-zero-business-required')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and request['attempt_id'].startswith(request['task']['id']+'-') and Path(worker_ref['path'])==attempt/'exit.json' and Path(worker['request']['path'])==attempt/'request.json' and Path(worker['response']['path'])==attempt/'response.json' and worker['attempt_id']==request['attempt_id'] and type(worker.get('returncode')) is int and worker['returncode']==0,'violation-initial-natural-worker-exit')
    o.need(request['kind']=='workshop-worker-request-v1' and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==request['task']['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'violation-initial-original-worker-binding')
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(pe['argv']==expected and request['config']['python']==expected[0]and request['config']['project']==str(o.PROJECT)and o.doc(request['config_ref'])==request['config'],'violation-local-plan-parent-command');outer=request['task']['outer'];o.need(outer['boot']==parent['boot_identity'] and outer['clock_contract']==parent['clock_contract'] and outer['start_monotonic']<=parent['start_monotonic'] and datetime.fromisoformat(outer['started_at'])<=datetime.fromisoformat(parent['wall_started_at']),'violation-initial-original-outer-clock')
    pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));expected=[request['config']['python'],str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(request['config']['project']==str(o.PROJECT) and request['config']['coordinator_root']==str(o.PROJECT/'runtime/workshop-director') and request['config']['python']==str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==expected and pe['returncode']==0 and not o.raw(pe['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==call['result'] and out['child'] is None and out['completion'] is None,'violation-initial-parent-natural-exit')
    return {'order':order,'ledgers':ledger_facts(order,live=live),'initial_failed_call':call,'worker_task_id':request['task']['id'],'original_outer':request['task']['outer'],'evidence':[parent['order'],parent['origin_ref'],call['launch'],call['result'],worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]}
def reviewed_sources(parent,release_ref,old_refs,*,installed,entry_archive=None,nav_archive=None,quality_archives=None):
    r=o.doc(release_ref);wanted=paths();targets=r['targets'];o.need(r.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(wanted.values()),'violation-initial-exact-four-source-release')
    originals={x['path']:x for x in parent['code_refs']};old={Path(x['path']).name:x for x in old_refs};o.need(len(old_refs)==3 and set(old)=={n+'.before' for n in NAMES if n!='violation_initial_ledger_recovery.py'},'violation-initial-three-old-source-archives');codes=copy.deepcopy(parent['code_refs']);archive=[]
    for t in targets:
        name=Path(t['target']).name;path=t['target'];o.raw(t['after']);o.need(t.get('mode')=='0644','violation-initial-source-mode')
        if name=='violation_initial_ledger_recovery.py':o.need(path not in originals and t['old_sha256'] is None,'violation-initial-new-helper-only');codes.append({'path':path,'sha256':t['after']['sha256']})
        else:
            before=originals[path];saved=old[name+'.before'];o.need(t['old_sha256']==before['sha256']==saved['sha256'],'violation-initial-before-source-binding');o.raw(saved);archive.append(saved);codes[codes.index(before)]={'path':path,'sha256':t['after']['sha256']}
        if installed:o.need(o.ref(Path(path))['sha256']==t['after']['sha256'],'violation-initial-reviewed-source-not-installed')
    changed=set(wanted.values())
    for r in codes:
        if not installed and entry_archive is not None and r['path']==str(o.PROJECT/'skills/violation-notifier/scripts/violation_execution.py'):
            o.need(entry_archive['sha256']==r['sha256'],'violation-initial-entry-archive-binding');o.raw(entry_archive)
        elif not installed and nav_archive is not None and r['path']==str(o.PROJECT/'skills/violation-notifier/scripts/bridge-navigation.py'):
            o.need(nav_archive['sha256']==r['sha256'],'violation-center-nav-archive-binding');o.raw(nav_archive)
        elif not installed and quality_archives is not None and r['path'] in {str(o.PROJECT/'skills/violation-notifier/scripts'/n) for n in ('region_frame_capture.py','program_region_quality.py')}:
            matches=[a for a in quality_archives if a['original']==r];o.need(len(matches)==1 and matches[0]['archive']['sha256']==r['sha256'],'violation-date-fragment-historical-quality-archive');o.raw(matches[0]['archive'])
        elif installed or r['path'] not in changed:o.raw(r)
    return codes
def recovered(parent,proof):
    s=copy.deepcopy(parent);s.update(status='running',**{FIELD:proof});s.pop('error');s.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':ERROR,'recovery':proof});return s
def plan(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-initial-canonical-parent');facts=original_contract(parent,worker_ref,live=True);live_lease(facts['order']);codes=reviewed_sources(parent,release_ref,old_refs,installed=installed)
    return {'kind':KIND,'at':stamp(),'original_parent':parent_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'engine_was_absent':True,'ui_used':False}
def verify_recovered(current,proof_ref,*,installed=True,entry_archive=None,nav_archive=None,quality_archives=None):
    if current.get(FIELD8)==proof_ref:return verify_readonly_wait(current,proof_ref,installed=installed)
    if current.get(FIELD7)==proof_ref:return verify_date_fragment(current,proof_ref,installed=installed)
    if current.get(FIELD6)==proof_ref:return verify_analysis_wait(current,proof_ref,installed=installed,quality_archives=quality_archives)
    if current.get(FIELD5)==proof_ref:return verify_records_entry(current,proof_ref,installed=installed,quality_archives=quality_archives)
    if current.get(FIELD4)==proof_ref:return verify_center(current,proof_ref,installed=installed,quality_archives=quality_archives)
    if current.get(FIELD3)==proof_ref:return verify_company(current,proof_ref,installed=installed,nav_archive=nav_archive,quality_archives=quality_archives)
    if current.get(FIELD2)==proof_ref:return verify_v2(current,proof_ref,installed=installed,nav_archive=nav_archive,quality_archives=quality_archives)
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-initial-ledger-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and current.get(FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and p['engine_was_absent'] is True and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-initial-canonical-proof')
    original=o.doc(p['parent_archive']);o.need(p['parent_archive']['sha256']==p['original_parent']['sha256'] and Path(p['original_parent']['path'])==folder/'launcher.json' and Path(p['parent_archive']['path'])==base/'original-parent.json','violation-initial-parent-archive')
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-initial-canonical-source-archives')
    facts=original_contract(original,p['worker'],live=False);codes=reviewed_sources(original,p['release'],p['old_sources'],installed=installed,entry_archive=entry_archive,nav_archive=nav_archive,quality_archives=quality_archives);expected=recovered(original,proof_ref)
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:1]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()),'violation-initial-original-history-preserved')
    return {'kind':KIND,'proof':proof_ref,'code_refs':codes,'initial_failed_call':original['calls'][0],'evidence':[proof_ref,p['parent_archive'],p['release'],*p['old_sources'],*facts['evidence']]}
def recover(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-initial-ledger-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-initial-original-recovery-inputs')
        else:
            p=plan(parent_ref,worker_ref,release_ref,old_refs);base.mkdir(parents=True,exist_ok=True);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);expected=recovered(original,proof);current=o.doc(o.ref(folder/'launcher.json'))
        if current==original:
            original_contract(original,worker_ref,live=True)
            live_lease(p['facts']['order'])
            from role_execution_launcher import save
            verify_recovered(expected,proof);save(folder/'launcher.json',expected)
        else:o.need(current==expected,'violation-initial-state-changed-no-rewrite')
        verify_recovered(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'proof':proof,'ui_used':False,'engine_created':False}
FIELD2='violation_initial_ledger_entry_recovery'
KIND2='verified-violation-initial-ledger-entry-recovery-v2'
BASE_RELEASE_SHA='8190f7820826c94a64f9b49979424c75cab0b787bf9d121fcece29bcf127be87'
V2_NAMES={n:r for n,r in NAMES.items() if n!='violation_execution_ports.py'}
V2_NAMES['violation_execution.py']='skills/violation-notifier/scripts/violation_execution.py'
def second_worker(parent,worker_ref,call,prior_worker):
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;prior=o.doc(o.doc(prior_worker)['request'])
    task=request['task'];order=o.validate(parent['order']);expected_attempt=task['id']+'-'+str(int(prior['attempt_id'].rsplit('-',1)[1])+1)
    o.need(worker.get('returncode')==0 and type(worker.get('returncode')) is int and worker.get('attempt_id')==request['attempt_id']==expected_attempt and Path(worker_ref['path'])==o.PROJECT/'runtime/standalone-workshop-director/attempts'/expected_attempt/'exit.json','violation-entry-natural-worker')
    o.need(worker['request']['path']==str(attempt/'request.json') and worker['response']['path']==str(attempt/'response.json') and request['kind']=='workshop-worker-request-v1' and task['id']==prior['task']['id'] and task['flow']==o.FLOW and task['day']==order['day'] and task['outer']==prior['task']['outer'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==task['id'] and response['attempt_id']==expected_attempt and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'violation-entry-original-worker-binding')
    cfg=request['config'];pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[cfg['python'],str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(cfg['project']==str(o.PROJECT) and cfg['coordinator_root']==str(o.PROJECT/'runtime/workshop-director') and cfg['python']==str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==argv and type(pe['returncode']) is int and pe['returncode']==0 and not o.raw(pe['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==call['result'] and out['child'] is None and out['completion'] is None,'violation-entry-parent-natural-exit')
    return [worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]
def v2_sources(parent,release_ref,old_refs,*,installed,nav_archive=None,quality_archives=None):
    release=o.doc(release_ref);wanted={n:str(o.PROJECT/r) for n,r in V2_NAMES.items()};old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs}
    o.need(len(old_refs)==4 and set(old)==set(wanted),'violation-entry-four-before-archives')
    prior=o.doc(parent[FIELD]);o.need(prior['release']['sha256']==BASE_RELEASE_SHA,'violation-entry-exact-prior-root-release')
    base=verify_recovered(parent,parent[FIELD],installed=False,entry_archive=old['violation_execution.py'],nav_archive=nav_archive,quality_archives=quality_archives)
    original={r['path']:r for r in base['code_refs']};codes=copy.deepcopy(base['code_refs']);targets=release['targets']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(wanted.values()),'violation-entry-exact-four-source-release')
    for t in targets:
        name=Path(t['target']).name;before=original[t['target']];saved=old[name];o.need(t['old_sha256']==saved['sha256']==before['sha256'] and t.get('mode')=='0644','violation-entry-source-before-binding');o.raw(saved);o.raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def entry_original(parent,worker_ref,release_ref,old_refs,*,installed,live,nav_archive=None,quality_archives=None):
    folder=o.location(parent['order']);o.need(parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and FIELD in parent and FIELD2 not in parent and not parent.get('child') and not parent.get('completion') and len(parent['calls'])==2 and all(c['state']=='returned' for c in parent['calls']),'violation-entry-exact-second-constructor-failure')
    base,codes=v2_sources(parent,release_ref,old_refs,installed=installed,nav_archive=nav_archive,quality_archives=quality_archives);prior=o.doc(parent[FIELD]);prior_original=o.doc(prior['parent_archive']);expected=recovered(prior_original,parent[FIELD]);expected.update(status='hold',error='execution-child-stopped',calls=parent['calls']);o.need(parent==expected,'violation-entry-exact-parent-delta')
    call=parent['calls'][1];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(call['argv']==parent['calls'][0]['argv']==la['argv']==ex['argv'] and Path(call['launch']['path'])==folder/'children/0001-launch.json' and Path(call['result']['path'])==folder/'children/0001-exit.json' and la['order']==parent['order'] and la['index']==1 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':'execution-reference-changed'},'violation-entry-exact-second-call')
    previous=o.doc(parent['calls'][0]['result']);o.need(previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-entry-second-time-order')
    if live:o.need(not (folder/'engine.json').exists() and not (folder/'engine.json').is_symlink() and not (folder/'companies').exists() and not (folder/'companies').is_symlink(),'violation-entry-zero-business-required')
    order=o.validate(parent['order']);ledgers=ledger_facts(order,live=live);worker_evidence=second_worker(parent,worker_ref,call,prior['worker'])
    # The unchanged old entry reads original refs in list order. Pin the first
    # actual difference to the reviewed ports transition, not an arbitrary error.
    old_codes=parent['code_refs'];base_codes={r['path']:r for r in base['code_refs']};diff=[{'before':r,'after':base_codes[r['path']]} for r in old_codes if r!=base_codes[r['path']]]
    o.need(len(diff)==3 and diff[0]['before']['path']==str(o.PROJECT/NAMES['violation_execution_ports.py']),'violation-entry-exact-first-reference-mismatch')
    return {'order':order,'ledgers':ledgers,'initial_failed_calls':parent['calls'],'first_reference_mismatch':diff[0],'evidence':[parent[FIELD],*base['evidence'],call['launch'],call['result'],*worker_evidence]},codes

def recovered_v2(parent,proof):
    s=copy.deepcopy(parent);s.update(status='running',**{FIELD2:proof});s.pop('error');s['resolved_errors'].append({'error':'execution-child-stopped','original_child_error':'execution-reference-changed','recovery':proof});return s

def plan_v2(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-entry-canonical-parent');facts,codes=entry_original(parent,worker_ref,release_ref,old_refs,installed=installed,live=True);live_lease(facts['order'])
    return {'kind':KIND2,'at':stamp(),'original_parent':parent_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'engine_was_absent':True,'ui_used':False}

def verify_v2(current,proof_ref,*,installed=True,nav_archive=None,quality_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-initial-ledger-entry-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND2 and current.get(FIELD2)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and p['engine_was_absent'] is True and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-entry-canonical-proof')
    original=o.doc(p['parent_archive']);o.need(p['parent_archive']['sha256']==p['original_parent']['sha256'] and Path(p['original_parent']['path'])==folder/'launcher.json' and Path(p['parent_archive']['path'])==base/'original-parent.json' and all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-entry-original-archives')
    facts,codes=entry_original(original,p['worker'],p['release'],p['old_sources'],installed=installed,live=False,nav_archive=nav_archive,quality_archives=quality_archives);expected=recovered_v2(original,proof_ref)
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:2]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and current.get(FIELD)==original[FIELD],'violation-entry-original-history-preserved')
    return {'kind':KIND2,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':original['calls'],'evidence':[proof_ref,p['parent_archive'],p['release'],*p['old_sources'],*facts['evidence']]}

def recover_v2(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-initial-ledger-entry-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-entry-original-recovery-inputs')
        else:
            p=plan_v2(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);expected=recovered_v2(original,proof);current=o.doc(o.ref(folder/'launcher.json'))
        if current==original:
            entry_original(original,worker_ref,release_ref,p['old_sources'],installed=True,live=True);live_lease(p['facts']['order']);from role_execution_launcher import save
            verify_v2(expected,proof);save(folder/'launcher.json',expected)
        else:o.need(current==expected,'violation-entry-state-changed-no-rewrite')
        verify_v2(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'proof':proof,'ui_used':False,'engine_created':False}

FIELD3='violation_company_preinput_recovery'
KIND3='verified-violation-company-input-layout-preinput-v1'
COMPANY_ERROR='output-must-be-independent-of-input-directories'
ENTRY_RELEASE_SHA='9acb4a4eda0f419a907a6b0358f14c97ff0922cd33bc03c8e6cd854f2d31064c'
COMPANY_NAMES={n:r for n,r in NAMES.items()}
def company_sources(parent,release_ref,old_refs,*,installed,nav_archive=None,quality_archives=None):
    prior=o.doc(parent[FIELD2]);o.need(prior['release']['sha256']==ENTRY_RELEASE_SHA,'violation-company-exact-prior-release');base=verify_v2(parent,parent[FIELD2],installed=False,nav_archive=nav_archive,quality_archives=quality_archives)
    paths={n:str(o.PROJECT/r) for n,r in COMPANY_NAMES.items()};old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};o.need(len(old_refs)==4 and set(old)==set(paths),'violation-company-exact-four-before')
    release=o.doc(release_ref);targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(paths.values()),'violation-company-exact-four-source-release');codes=copy.deepcopy(base['code_refs']);by_path={r['path']:r for r in codes}
    for t in targets:
        n=Path(t['target']).name;before=by_path[t['target']];o.need(t['old_sha256']==before['sha256']==old[n]['sha256'] and t.get('mode')=='0644','violation-company-before-source-binding');o.raw(old[n]);o.raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def company_engine(original_parent,engine_ref,*,live,original_engine_ref=None):
    import workflow as workflow
    from violation_execution_ports import company_nav,nav
    folder=o.location(original_parent['order']);order=o.validate(original_parent['order']);e=o.doc(engine_ref)
    origin=original_engine_ref or engine_ref
    o.need(origin['sha256']==engine_ref['sha256'] and Path(origin['path'])==folder/'engine.json' and e.get('kind')=='violation-execution-v1' and e.get('order')==original_parent['order'] and e.get('scope_sha256')==order['scope_sha256'] and e.get('status')=='hold' and e.get('phase')=='company' and e.get('index')==0 and e.get('error')==COMPANY_ERROR and len(e.get('calls',[]))==2 and not e.get('business_journals') and 'resolved_preinput_failures' not in e,'violation-company-exact-engine')
    plan_call,failed=e['calls'];company=order['companies'][0];base=folder/'companies/0';artifacts=e['companies'][0]['artifacts'];o.need(len(e['companies'])==2 and e['companies'][0]['phase']=='company' and e['companies'][1]=={'artifacts':{},'phase':'plan'} and set(artifacts)=={'plan','job','identity_receipt'},'violation-company-exact-initial-artifacts')
    context={'order':order,'company':company,'artifacts':{},'folder':str(base),'phase':'plan'}
    o.need(plan_call.get('step')=='plan' and plan_call.get('company_index')==0 and plan_call.get('state')=='returned' and plan_call.get('applied') is True and plan_call.get('context')==context and Path(plan_call['result']['path'])==folder/'receipts/00001.json' and o.doc(plan_call['result'])=={'done':True,'artifacts':artifacts},'violation-company-applied-plan-binding')
    o.need(failed.get('step')=='company' and failed.get('company_index')==0 and failed.get('state')=='failed' and failed.get('error')==COMPANY_ERROR and set(failed)=={'step','company_index','context','state','intent_at','error'} and failed['context']=={**context,'phase':'company','artifacts':artifacts},'violation-company-exact-preinput-call')
    plan=o.doc(artifacts['plan']);o.need(Path(artifacts['plan']['path'])==base/'plan.json' and plan==workflow.plan(o.doc(company['ledger']),order['day']) and Path(artifacts['job']['path'])==base/'navigation-job.json','violation-company-original-plan')
    receipt=o.doc(artifacts['identity_receipt']);job=nav.prepare(artifacts['plan']['path'],artifacts['plan']['sha256'],artifacts['identity_receipt']['path'],artifacts['identity_receipt']['sha256'],receipt['work_order_id']);o.need(o.doc(artifacts['job'])==job,'violation-company-original-navigation-job');company_nav.receipt(artifacts['identity_receipt'])
    registry_ref={'path':str(base/'daily-identity-registry.json'),'sha256':o.ref(base/'daily-identity-registry.json')['sha256']};registry=o.doc(registry_ref)
    # Recompute this local registry from the accepted daily immutable batch.
    # Normal company execution independently revalidates the full daily chain;
    # this preinput history guard does not run that expensive chain again.
    report=o.doc(order['daily_completion']);daily=o.doc(report['verification_parent_state']);batch_ref=daily['completion_proof']['batch'];batch=o.doc(batch_ref)
    expected_registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']}
    o.need(daily.get('status')=='complete' and registry==expected_registry and registry['company_identities'].get(company['groupid'])==receipt['identity'],'violation-company-original-registry')
    if live:
        o.need(not (base/'company-navigation').exists() and not (base/'company-navigation').is_symlink() and not (base/'company-navigation-inputs').exists() and not (base/'company-navigation-inputs').is_symlink(),'violation-company-no-navigation-output-or-intent')
        o.need({x.name for x in base.iterdir()}=={'plan.json','navigation-job.json','daily-identity-registry.json'},'violation-company-only-preinput-files')
        o.need({x.name for x in (folder/'companies').iterdir()}=={'0'},'violation-company-no-other-company-work')
    return {'engine':origin,'original_failed_call':failed,'applied_plan':plan_call,'registry':registry_ref,'artifacts':artifacts,'daily_registry_refs':[order['daily_completion'],report['verification_parent_state'],batch_ref]}

def company_original(parent,worker_ref,engine_ref,release_ref,old_refs,*,installed,live,original_engine_ref=None,nav_archive=None,quality_archives=None):
    o.need(parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and len(parent.get('calls',[]))==3 and all(c.get('state')=='returned' for c in parent['calls']) and FIELD2 in parent and FIELD3 not in parent and not parent.get('child') and not parent.get('completion'),'violation-company-exact-parent')
    base,codes=company_sources(parent,release_ref,old_refs,installed=installed,nav_archive=nav_archive,quality_archives=quality_archives);p=o.doc(parent[FIELD2]);old=o.doc(p['parent_archive']);expected=recovered_v2(old,parent[FIELD2]);expected.update(status='hold',error='execution-child-stopped',calls=parent['calls']);o.need(parent==expected,'violation-company-exact-parent-delta')
    folder=o.location(parent['order']);call=parent['calls'][2];la=o.doc(call['launch']);ex=o.doc(call['result']);previous=o.doc(parent['calls'][1]['result']);o.need(call['argv']==parent['calls'][0]['argv']==la['argv']==ex['argv'] and Path(call['launch']['path'])==folder/'children/0002-launch.json' and Path(call['result']['path'])==folder/'children/0002-exit.json' and la['order']==parent['order'] and la['index']==2 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':COMPANY_ERROR} and previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-company-exact-child-exit')
    engine_facts=company_engine(parent,engine_ref,live=live,original_engine_ref=original_engine_ref);o.need(datetime.fromisoformat(la['at'])<=datetime.fromisoformat(engine_facts['applied_plan']['intent_at'])<=datetime.fromisoformat(engine_facts['applied_plan']['returned_at'])<=datetime.fromisoformat(engine_facts['original_failed_call']['intent_at'])<=datetime.fromisoformat(ex['at']),'violation-company-real-time-order')
    worker_evidence=second_worker(parent,worker_ref,call,p['worker']);ledgers=ledger_facts(o.validate(parent['order']),live=live)
    return {'engine':engine_facts,'ledgers':ledgers,'initial_failed_calls':parent['calls'],'evidence':[*base['evidence'],engine_facts['engine'],*engine_facts['daily_registry_refs'],engine_facts['registry'],*engine_facts['artifacts'].values(),call['launch'],call['result'],*worker_evidence]},codes

def repaired_company(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD3:proof});current.pop('error');current['resolved_errors'].append({'error':'execution-child-stopped','original_child_error':COMPANY_ERROR,'recovery':proof})
    active=copy.deepcopy(engine);failed=active['calls'].pop();active.update(status='running');active.pop('error');active['resolved_preinput_failures']=[{'call':failed,'proof':proof}]
    return current,active

def plan_company(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-company-canonical-parent');engine_ref=o.ref(folder/'engine.json');facts,codes=company_original(parent,worker_ref,engine_ref,release_ref,old_refs,installed=installed,live=True);live_lease(o.validate(parent['order']))
    return {'kind':KIND3,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_company(current,proof_ref,*,installed=True,nav_archive=None,quality_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-company-preinput-recovery'/p['original_parent']['sha256'];o.need(p.get('kind')==KIND3 and current.get(FIELD3)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-company-canonical-proof')
    original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(p['parent_archive']['sha256']==p['original_parent']['sha256'] and Path(p['original_parent']['path'])==folder/'launcher.json' and Path(p['parent_archive']['path'])==base/'original-parent.json' and p['engine_archive']['sha256']==p['original_engine']['sha256'] and Path(p['original_engine']['path'])==folder/'engine.json' and Path(p['engine_archive']['path'])==base/'original-engine.json' and all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-company-original-archives')
    # Historical engine bytes are immutable. The canonical original path was
    # bound above; parse the same bytes using that declared origin, not a new ref.
    facts,codes=company_original(original,p['worker'],p['engine_archive'],p['release'],p['old_sources'],installed=installed,live=False,original_engine_ref=p['original_engine'],nav_archive=nav_archive,quality_archives=quality_archives)
    expected,active=repaired_company(original,engine,proof_ref);live_engine=o.doc(o.ref(folder/'engine.json'))
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:3]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and current.get(FIELD2)==original[FIELD2] and current.get(FIELD)==original[FIELD] and live_engine.get('order')==active['order'] and live_engine.get('scope_sha256')==active['scope_sha256'] and live_engine['calls'][:1]==active['calls'] and live_engine.get('resolved_preinput_failures')==active['resolved_preinput_failures'],'violation-company-original-history-preserved')
    return {'kind':KIND3,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':original['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['release'],*p['old_sources'],*[r for r in facts['evidence'] if r!=p['original_engine']]]}

def recover_company(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-company-preinput-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-company-original-recovery-inputs')
        else:
            p=plan_company(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_company(original,engine,proof);current=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current in (original,expected) and current_engine in (engine,active),'violation-company-state-changed-no-rewrite');live_lease(o.validate(current['order']))
        if current_engine==engine:
            company_original(original,worker_ref,p['original_engine'],release_ref,p['old_sources'],installed=True,live=True);from role_execution_launcher import save
            save(folder/'engine.json',active)
        if current==original:
            from role_execution_launcher import save
            save(folder/'launcher.json',expected)
        verify_company(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False,'plan_replayed':False}

FIELD4='violation_center_readonly_recovery'
KIND4='verified-violation-confirmed-center-intermediate-readonly-v1'
CENTER_ERROR='navigation-tree-path-conflict'
COMPANY_RELEASE_SHA='d4523f8725d0e84ffb5bc299ac9fc4c49b2106d2d79a29dfbe08a845a0bb59f9'
CENTER_NAMES={n:r for n,r in NAMES.items() if n!='violation_execution_ports.py'}
CENTER_NAMES['bridge-navigation.py']='skills/violation-notifier/scripts/bridge-navigation.py'
def center_sources(parent,release_ref,old_refs,*,installed,quality_archives=None):
    old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};paths={n:str(o.PROJECT/r) for n,r in CENTER_NAMES.items()};o.need(len(old_refs)==4 and set(old)==set(paths),'violation-center-four-before-archives');prior=o.doc(parent[FIELD3]);o.need(prior['release']['sha256']==COMPANY_RELEASE_SHA,'violation-center-exact-company-release')
    base=verify_company(parent,parent[FIELD3],installed=False,nav_archive=old['bridge-navigation.py'],quality_archives=quality_archives);release=o.doc(release_ref);targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(paths.values()),'violation-center-four-source-release');codes=copy.deepcopy(base['code_refs']);by_path={r['path']:r for r in codes}
    for t in targets:
        n=Path(t['target']).name;before=by_path[t['target']];o.need(t['old_sha256']==before['sha256']==old[n]['sha256'] and t.get('mode')=='0644','violation-center-before-source-binding');o.raw(old[n]);o.raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def center_nav_facts(parent,engine,nav_ref,*,original_nav_ref=None):
    from types import SimpleNamespace
    from violation_execution_ports import nav
    folder=o.location(parent['order']);base=folder/'companies/0';order=o.validate(parent['order']);company=order['companies'][0];artifacts=engine['companies'][0]['artifacts'];job=o.doc(artifacts['job']);s=o.doc(nav_ref);origin=original_nav_ref or nav_ref
    o.need(origin['sha256']==nav_ref['sha256'] and Path(origin['path'])==base/'center-navigation.json' and s.get('fingerprint')==nav.tag(job) and s.get('tab_id')==parent['tab_id'] and all(s.get(k)==job[k] for k in ('company','groupid','start','end_exclusive')) and s.get('phase')=='observeCenter' and s.get('profile_accepted') is False and s.get('business_progress_changed') is False and s.get('platform_writes') is False and s.get('production_enabled') is False and not s.get('last_error') and not s.get('error') and not s.get('readonly_route_recovery') and not s.get('readonly_route_exhausted') and len(s.get('calls',[]))==1,'violation-center-exact-unconsumed-observation')
    nav.scope(job);owner=SimpleNamespace(s=s,job=job,tab=parent['tab_id']);binding=nav.transition_binding(owner,'center');call=s['calls'][0];o.need(s.get('last_tree')==call.get('before')==s['observations'][-1] and binding['source_path']=='/p/home' and binding['target_path']==nav.CENTER,'violation-center-original-home-click')
    source=o.doc(binding['before']);gid=str(company['groupid']);home='https://life.douyin.com/p/home?groupid='+gid;intermediate='https://life.douyin.com/p/governance/home_overview?enter_from=homepage&groupid='+gid;target='https://life.douyin.com'+nav.CENTER+'?groupid='+gid+'&manual_switch=1';o.need(source['tab']['url']==home and source['tab'].get('active') is True,'violation-center-exact-home-url')
    if s.get('observation_transport') is not None:
        values,transport_refs=nav.observation_members(s,base/'navigation-raw-observations',o.doc);refs=transport_refs
    else:
        refs=s['raw_observations'][-4:];commands=[{'op':'tabs'},{'op':'ping','tabId':parent['tab_id']},{'op':'tree','tabId':parent['tab_id']},{'op':'tabs'}];o.need(len(refs)==4 and len({str(Path(r['path']).parent) for r in refs})==1,'violation-center-four-raw-scope');values=[]
        for i,(r,command) in enumerate(zip(refs,commands)):
            path=Path(r['path']);o.need(set(r)=={'path','sha256','command'} and r['command']==command and path.parent.parent==base/'navigation-raw-observations' and path.name==str(i)+'-'+command['op']+'.json','violation-center-canonical-raw-command');reply=o.doc({k:r[k] for k in ('path','sha256')});o.need(reply.get('ok') is True and reply.get('error') is None and 'result' in reply,'violation-center-raw-transport-failed');values.append(reply['result'])
    before=nav.context(values[0],parent['tab_id'],gid);after=nav.context(values[3],parent['tab_id'],gid)
    o.need(before['url']==intermediate and after['url']==target and before['windowId']==after['windowId']==binding['window_id'] and before.get('active') is True and after.get('active') is True and all(len([w for w in value if w.get('windowId')==binding['window_id'] and w.get('focused') is True])==1 for value in (values[0],values[3])),'violation-center-exact-original-route-race')
    ping,tree=values[1:3];o.need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('url')==tree.get('url')=='https://life.douyin.com'+nav.CENTER,'violation-center-original-target-tree');ns=list(nav.nodes(tree));nav.identity(tree,job['identity']);o.need(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in ns),'violation-center-risk')
    return {'nav':origin,'job':artifacts['job'],'binding':binding,'original_click':call,'source_before':binding['before'],'raw_refs':refs,'source_url':home,'intermediate_url':intermediate,'target_url':target,'full_identity':job['identity'],'unconsumed_readonly_budget':3}

def center_original(parent,worker_ref,engine_ref,nav_ref,release_ref,old_refs,*,installed,live,original_engine_ref=None,original_nav_ref=None,quality_archives=None):
    folder=o.location(parent['order']);o.need(parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and FIELD3 in parent and FIELD4 not in parent and len(parent['calls'])==4 and all(c.get('state')=='returned' for c in parent['calls']) and not parent.get('child') and not parent.get('completion'),'violation-center-exact-parent')
    base,codes=center_sources(parent,release_ref,old_refs,installed=installed,quality_archives=quality_archives);p=o.doc(parent[FIELD3]);old=o.doc(p['parent_archive']);old_engine=o.doc(p['engine_archive']);expected,_=repaired_company(old,old_engine,parent[FIELD3]);expected.update(status='hold',error='execution-child-stopped',calls=parent['calls']);o.need(parent==expected,'violation-center-parent-delta')
    e=o.doc(engine_ref);origin=original_engine_ref or engine_ref;o.need(origin['sha256']==engine_ref['sha256'] and Path(origin['path'])==folder/'engine.json' and e.get('kind')=='violation-execution-v1' and e.get('order')==parent['order'] and e.get('status')=='hold' and e.get('phase')=='center' and e.get('index')==0 and e.get('error')==CENTER_ERROR and len(e.get('calls',[]))>=2 and 'resolved_readonly_failures' not in e,'violation-center-exact-engine')
    prefix=e['calls'][:-1];failed=e['calls'][-1];o.need(all(c.get('state')=='returned' and c.get('applied') is True and c.get('company_index')==0 for c in prefix) and failed.get('state')=='failed' and failed.get('step')=='center' and failed.get('company_index')==0 and failed.get('error')==CENTER_ERROR and set(failed)=={'step','company_index','context','state','intent_at','error'},'violation-center-exact-readonly-failure')
    for c in prefix:o.doc(c['result'])
    a=e['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(e['companies'][0]['phase']=='center' and failed['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'center'} and set(a)=={'plan','job','identity_receipt','company_navigation'},'violation-center-original-context');company_state=o.doc(a['company_navigation']);o.need(Path(a['company_navigation']['path'])==folder/'companies/0/company-navigation/workflow.json' and company_state.get('state')=='complete' and company_state.get('phase')=='done' and all(c.get('state')=='confirmed' for c in company_state.get('calls',[])) and company_state['result']['identity']==o.doc(a['job'])['identity'],'violation-center-confirmed-company-preserved')
    nav_facts=center_nav_facts(parent,e,nav_ref,original_nav_ref=original_nav_ref);call=parent['calls'][3];la=o.doc(call['launch']);ex=o.doc(call['result']);previous=o.doc(parent['calls'][2]['result']);o.need(call['argv']==parent['calls'][0]['argv']==la['argv']==ex['argv'] and Path(call['launch']['path'])==folder/'children/0003-launch.json' and Path(call['result']['path'])==folder/'children/0003-exit.json' and la['order']==parent['order'] and la['index']==3 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':CENTER_ERROR} and previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-center-exact-child-exit')
    if live:o.need(o.ref(folder/'engine.json')==engine_ref and o.ref(folder/'companies/0/center-navigation.json')==nav_ref,'violation-center-current-state-changed')
    workers=second_worker(parent,worker_ref,call,p['worker']);return {'engine':origin,'nav':nav_facts,'original_failed_call':failed,'prefix':prefix,'initial_failed_calls':parent['calls'],'evidence':[*base['evidence'],origin,nav_facts['nav'],nav_facts['job'],nav_facts['source_before'],*[{k:r[k] for k in ('path','sha256')} for r in nav_facts['raw_refs']],a['company_navigation'],call['launch'],call['result'],*workers]},codes

def repaired_center(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD4:proof});current.pop('error');current['resolved_errors'].append({'error':'execution-child-stopped','original_child_error':CENTER_ERROR,'recovery':proof});active=copy.deepcopy(engine);failed=active['calls'].pop();active.update(status='running');active.pop('error');active['resolved_readonly_failures']=[{'call':failed,'proof':proof}];return current,active

def plan_center(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-center-canonical-parent');engine_ref=o.ref(folder/'engine.json');nav_ref=o.ref(folder/'companies/0/center-navigation.json');facts,codes=center_original(parent,worker_ref,engine_ref,nav_ref,release_ref,old_refs,installed=installed,live=True);live_lease(o.validate(parent['order']));return {'kind':KIND4,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'original_nav':nav_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_center(current,proof_ref,*,installed=True,quality_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-center-readonly-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND4 and current.get(FIELD4)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-center-canonical-proof')
    for n,origin in (('parent',folder/'launcher.json'),('engine',folder/'engine.json'),('nav',folder/'companies/0/center-navigation.json')):
        o.need(p[n+'_archive']['sha256']==p['original_'+n]['sha256'] and Path(p['original_'+n]['path'])==origin and Path(p[n+'_archive']['path'])==base/('original-'+n+'.json'),'violation-center-original-archives')
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-center-source-archives');original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=center_original(original,p['worker'],p['engine_archive'],p['nav_archive'],p['release'],p['old_sources'],installed=installed,live=False,original_engine_ref=p['original_engine'],original_nav_ref=p['original_nav'],quality_archives=quality_archives);expected,active=repaired_center(original,engine,proof_ref);live_engine=o.doc(o.ref(folder/'engine.json'))
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:4]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(f)==original[f] for f in (FIELD,FIELD2,FIELD3)) and live_engine.get('order')==active['order'] and live_engine.get('scope_sha256')==active['scope_sha256'] and live_engine['calls'][:len(active['calls'])]==active['calls'] and live_engine.get('resolved_preinput_failures')==active['resolved_preinput_failures'] and ((live_engine.get('resolved_readonly_failures')==active['resolved_readonly_failures'] if installed else live_engine.get('resolved_readonly_failures',[])[:len(active['resolved_readonly_failures'])]==active['resolved_readonly_failures']) if installed else live_engine.get('resolved_readonly_failures',[])[:len(active['resolved_readonly_failures'])]==active['resolved_readonly_failures']),'violation-center-history-preserved')
    return {'kind':KIND4,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':original['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['nav_archive'],p['release'],*p['old_sources'],*[r for r in facts['evidence'] if r not in (p['original_engine'],p['original_nav'])]]}

def recover_center(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-center-readonly-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-center-original-recovery-inputs')
        else:
            p=plan_center(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['nav_archive']=immutable_bytes(base/'original-nav.json',o.raw(p['original_nav']));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_center(original,engine,proof);current=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current in (original,expected) and current_engine in (engine,active),'violation-center-state-changed-no-rewrite');o.need(o.ref(folder/'companies/0/center-navigation.json')==p['original_nav'],'violation-center-nav-changed-no-rewrite');live_lease(o.validate(current['order']))
        from role_execution_launcher import save
        if current_engine==engine:
            center_original(original,worker_ref,p['original_engine'],p['original_nav'],release_ref,p['old_sources'],installed=True,live=True);save(folder/'engine.json',active)
        if current==original:save(folder/'launcher.json',expected)
        verify_center(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'nav_unchanged':p['original_nav'],'proof':proof,'ui_used':False,'input_replayed':False,'remaining_original_readonly_budget':3}

FIELD5='violation_records_entry_recovery'
KIND5='verified-violation-records-entry-before-query-v1'
RECORDS_ENTRY_ERROR='governance-row-before-range'
CENTER_RELEASE_SHA='cec88fdb9965ff83c9465a9a30ba4ebdb22083841813177931681287675dc2a0'
def records_entry_sources(parent,release_ref,old_refs,*,installed,quality_archives=None):
    old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};paths={n:str(o.PROJECT/r) for n,r in NAMES.items()};o.need(len(old_refs)==4 and set(old)==set(paths),'violation-records-entry-four-before');prior=o.doc(parent[FIELD4]);o.need(prior['release']['sha256']==CENTER_RELEASE_SHA,'violation-records-entry-exact-center-release')
    base=verify_center(parent,parent[FIELD4],installed=False,quality_archives=quality_archives);release=o.doc(release_ref);targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(paths.values()),'violation-records-entry-four-source-release');codes=copy.deepcopy(base['code_refs']);by_path={r['path']:r for r in codes}
    for t in targets:
        n=Path(t['target']).name;before=by_path[t['target']];o.need(t['old_sha256']==before['sha256']==old[n]['sha256'] and t.get('mode')=='0644','violation-records-entry-before-source-binding');o.raw(old[n]);o.raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def records_probe_facts(parent,engine,probe_ref,*,original_probe_ref=None):
    from violation_execution_ports import records_entry_from_probe,discovery,nav,g,capture
    folder=o.location(parent['order']);base=folder/'companies/0';a=engine['companies'][0]['artifacts'];job=o.doc(a['job']);s=o.doc(probe_ref);origin=original_probe_ref or probe_ref
    o.need(origin['sha256']==probe_ref['sha256'] and Path(origin['path'])==base/'records-navigation.json' and s.get('fingerprint')==nav.tag(job) and s.get('tab_id')==parent['tab_id'] and s.get('mode')=='records' and s.get('phase')=='profile-required' and s.get('waiting_for')=='review-real-records-tree' and s.get('profile_accepted') is False and s.get('business_progress_changed') is False and s.get('dates_queried') is False and s.get('submission_enabled') is False and len(s.get('calls',[]))==1 and s['calls'][0].get('state')=='confirmed' and len(s.get('observations',[]))==2 and s.get('last_observation')==s['observations'][-1] and s['calls'][0]['before']==s['observations'][0] and not s.get('readonly_route_recovery') and not s.get('readonly_route_exhausted'),'violation-records-entry-exact-probe')
    call=s['calls'][0];before=o.doc(call['before']);target=discovery.center_targets(before['tree'],job['identity'])['records'];expected={'op':'click','tabId':parent['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
    o.need(call['command']==expected and call['result'].get('kind')=='navigation' and call['result'].get('version')==nav.VERSION and call['result'].get('clicked',{}).get('name')=='违规记录' and call['result']['clicked'].get('selector')==target['selector'] and before.get('navigation_fingerprint')==nav.tag(job),'violation-records-entry-original-open')
    raw=records_entry_from_probe(s,job,parent['tab_id']);at=datetime.fromisoformat(raw['observed_at']);o.need(datetime.fromisoformat(before['observed_at'])<=datetime.fromisoformat(call['intent_at'])<=at,'violation-records-entry-original-time-order')
    try:capture.scope(raw,job,parent['tab_id'],before['tab']['windowId'],g.RECORDS)
    except ValueError as error:o.need(str(error)==RECORDS_ENTRY_ERROR,'violation-records-entry-original-range-error')
    else:raise ValueError('violation-records-entry-no-original-range-error')
    return {'probe':origin,'original_open':call,'before':call['before'],'raw':s['last_observation'],'job':a['job'],'observed_date_value':g.date_value(raw['tree']),'dates_queried':False,'no_business_result':True}

def records_entry_original(parent,worker_ref,engine_ref,probe_ref,release_ref,old_refs,*,installed,live,original_engine_ref=None,original_probe_ref=None,quality_archives=None):
    folder=o.location(parent['order']);o.need(parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and FIELD4 in parent and FIELD5 not in parent and len(parent['calls'])==5 and all(c.get('state')=='returned' for c in parent['calls']) and not parent.get('child') and not parent.get('completion'),'violation-records-entry-exact-parent')
    base,codes=records_entry_sources(parent,release_ref,old_refs,installed=installed,quality_archives=quality_archives);p=o.doc(parent[FIELD4]);old=o.doc(p['parent_archive']);old_engine=o.doc(p['engine_archive']);expected,_=repaired_center(old,old_engine,parent[FIELD4]);expected.update(status='hold',error='execution-child-stopped',calls=parent['calls']);o.need(parent==expected,'violation-records-entry-parent-delta')
    e=o.doc(engine_ref);origin=original_engine_ref or engine_ref;order=o.validate(parent['order']);o.need(origin['sha256']==engine_ref['sha256'] and Path(origin['path'])==folder/'engine.json' and e.get('kind')=='violation-execution-v1' and e.get('order')==parent['order'] and e.get('scope_sha256')==order['scope_sha256'] and e.get('status')=='hold' and e.get('phase')=='records-open' and e.get('index')==0 and e.get('error')==RECORDS_ENTRY_ERROR and len(e.get('calls',[]))>=2,'violation-records-entry-exact-engine')
    prefix=e['calls'][:-1];failed=e['calls'][-1];o.need(all(c.get('state')=='returned' and c.get('applied') is True and c.get('company_index')==0 for c in prefix) and failed.get('state')=='failed' and failed.get('step')=='records-open' and failed.get('company_index')==0 and failed.get('error')==RECORDS_ENTRY_ERROR and set(failed)=={'step','company_index','context','state','intent_at','error'},'violation-records-entry-exact-readonly-failure')
    for c in prefix:o.doc(c['result'])
    a=e['companies'][0]['artifacts'];o.need(e['companies'][0]['phase']=='records-open' and failed['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'records-open'} and set(a)=={'plan','job','identity_receipt','company_navigation','center_navigation','center_query_final','center_pages','center_zero'},'violation-records-entry-prequery-context')
    kept=[]
    for field in ('plan','job','identity_receipt','company_navigation','center_navigation','center_query_final'):
        o.doc(a[field]);kept.append(a[field])
    for r in a['center_pages']:o.doc(r);kept.append(r)
    facts=records_probe_facts(parent,e,probe_ref,original_probe_ref=original_probe_ref);call=parent['calls'][4];la=o.doc(call['launch']);ex=o.doc(call['result']);previous=o.doc(parent['calls'][3]['result']);o.need(call['argv']==parent['calls'][0]['argv']==la['argv']==ex['argv'] and Path(call['launch']['path'])==folder/'children/0004-launch.json' and Path(call['result']['path'])==folder/'children/0004-exit.json' and la['order']==parent['order'] and la['index']==4 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':RECORDS_ENTRY_ERROR} and previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-records-entry-exact-child-exit')
    if live:
        o.need(o.ref(folder/'engine.json')==engine_ref and o.ref(folder/'companies/0/records-navigation.json')==probe_ref,'violation-records-entry-state-changed')
        for n in ('records-query.json','records-query.json.lock'):
            path=folder/'companies/0'/n;o.need(not path.exists() and not path.is_symlink(),'violation-records-entry-query-already-started')
    workers=second_worker(parent,worker_ref,call,p['worker']);ledgers=ledger_facts(order,live=live)
    return {'engine':origin,'probe':facts,'prefix':prefix,'original_failed_call':failed,'initial_failed_calls':parent['calls'],'ledgers':ledgers,'evidence':[*base['evidence'],origin,facts['probe'],facts['before'],facts['raw'],*kept,call['launch'],call['result'],*workers]},codes

def repaired_records_entry(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD5:proof});current.pop('error');current['resolved_errors'].append({'error':'execution-child-stopped','original_child_error':RECORDS_ENTRY_ERROR,'recovery':proof});active=copy.deepcopy(engine);failed=active['calls'].pop();active.update(status='running');active.pop('error');active['resolved_readonly_failures'].append({'call':failed,'proof':proof});return current,active

def plan_records_entry(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-records-entry-canonical-parent');engine_ref=o.ref(folder/'engine.json');probe_ref=o.ref(folder/'companies/0/records-navigation.json');facts,codes=records_entry_original(parent,worker_ref,engine_ref,probe_ref,release_ref,old_refs,installed=installed,live=True);live_lease(o.validate(parent['order']));return {'kind':KIND5,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'original_probe':probe_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_records_entry(current,proof_ref,*,installed=True,quality_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-records-entry-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND5 and current.get(FIELD5)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-records-entry-canonical-proof')
    for n,origin in (('parent',folder/'launcher.json'),('engine',folder/'engine.json'),('probe',folder/'companies/0/records-navigation.json')):
        o.need(p[n+'_archive']['sha256']==p['original_'+n]['sha256'] and Path(p['original_'+n]['path'])==origin and Path(p[n+'_archive']['path'])==base/('original-'+n+'.json'),'violation-records-entry-original-archives')
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-records-entry-source-archives');original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=records_entry_original(original,p['worker'],p['engine_archive'],p['probe_archive'],p['release'],p['old_sources'],installed=installed,live=False,original_engine_ref=p['original_engine'],original_probe_ref=p['original_probe'],quality_archives=quality_archives);expected,active=repaired_records_entry(original,engine,proof_ref);live_engine=o.doc(o.ref(folder/'engine.json'))
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:5]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(f)==original[f] for f in (FIELD,FIELD2,FIELD3,FIELD4)) and live_engine.get('order')==active['order'] and live_engine.get('scope_sha256')==active['scope_sha256'] and live_engine['calls'][:len(active['calls'])]==active['calls'] and live_engine.get('resolved_preinput_failures')==active['resolved_preinput_failures'] and (live_engine.get('resolved_readonly_failures')==active['resolved_readonly_failures'] if installed else live_engine.get('resolved_readonly_failures',[])[:len(active['resolved_readonly_failures'])]==active['resolved_readonly_failures']),'violation-records-entry-history-preserved')
    return {'kind':KIND5,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':original['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['probe_archive'],p['release'],*p['old_sources'],*[r for r in facts['evidence'] if r not in (p['original_engine'],p['original_probe'])]]}

def recover_records_entry(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-records-entry-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-records-entry-original-recovery-inputs')
        else:
            p=plan_records_entry(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['probe_archive']=immutable_bytes(base/'original-probe.json',o.raw(p['original_probe']));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_records_entry(original,engine,proof);current=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current in (original,expected) and current_engine in (engine,active),'violation-records-entry-state-changed-no-rewrite');o.need(o.ref(folder/'companies/0/records-navigation.json')==p['original_probe'],'violation-records-entry-probe-changed-no-rewrite');live_lease(o.validate(current['order']))
        for n in ('records-query.json','records-query.json.lock'):
            path=folder/'companies/0'/n;o.need(not path.exists() and not path.is_symlink(),'violation-records-entry-query-already-started')
        from role_execution_launcher import save
        if current_engine==engine:
            records_entry_original(original,worker_ref,p['original_engine'],p['original_probe'],release_ref,p['old_sources'],installed=True,live=True);save(folder/'engine.json',active)
        if current==original:save(folder/'launcher.json',expected)
        verify_records_entry(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'probe_unchanged':p['original_probe'],'proof':proof,'ui_used':False,'input_replayed':False,'dates_queried':False,'resume_phase':'records-open'}

FIELD6='violation_analysis_fresh_wait_recovery'
KIND6='verified-violation-completed-analysis-fresh-wait-v1'
ANALYSIS_WAIT='fresh-analysis-observation-before-date'
RECORDS_ENTRY_RELEASE_SHA='8c0a6ff104998bdaa597f9f8582c27dee9279480de6f1d829510e93165f6256d'
def analysis_wait_sources(parent,release_ref,old_refs,*,installed,quality_archives=None):
    old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};wanted=paths();o.need(len(old_refs)==4 and set(old)==set(wanted),'violation-analysis-wait-four-before')
    prior=o.doc(parent[FIELD5]);o.need(prior['release']['sha256']==RECORDS_ENTRY_RELEASE_SHA,'violation-analysis-wait-exact-prior-release');base=verify_records_entry(parent,parent[FIELD5],installed=False,quality_archives=quality_archives);codes=copy.deepcopy(base['code_refs']);by={r['path']:r for r in codes};release=o.doc(release_ref);targets=release['targets']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(wanted.values()),'violation-analysis-wait-four-source-release')
    for t in targets:
        before=by[t['target']];saved=old[Path(t['target']).name];o.need(t['old_sha256']==before['sha256']==saved['sha256'] and t.get('mode')=='0644','violation-analysis-wait-before-source-binding');o.raw(saved);o.raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def analysis_wait_worker(parent,worker_ref,call,prior_worker):
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;prior=o.doc(o.doc(prior_worker)['request']);task=request['task'];order=o.validate(parent['order']);expected_attempt=task['id']+'-'+str(int(prior['attempt_id'].rsplit('-',1)[1])+1)
    o.need(type(worker.get('returncode')) is int and worker['returncode']==0 and worker.get('attempt_id')==request['attempt_id']==expected_attempt and Path(worker_ref['path'])==o.PROJECT/'runtime/standalone-workshop-director/attempts'/expected_attempt/'exit.json','violation-analysis-wait-natural-worker')
    o.need(worker['request']['path']==str(attempt/'request.json') and worker['response']['path']==str(attempt/'response.json') and request['kind']=='workshop-worker-request-v1' and task['id']==prior['task']['id'] and task['flow']==o.FLOW and task['day']==order['day'] and task['outer']==prior['task']['outer'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==task['id'] and response['attempt_id']==expected_attempt and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'violation-analysis-wait-original-worker-binding')
    cfg=request['config'];pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[cfg['python'],str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(cfg['project']==str(o.PROJECT) and cfg['coordinator_root']==str(o.PROJECT/'runtime/workshop-director') and cfg['python']==str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==argv and type(pe['returncode']) is int and pe['returncode']==0 and not o.raw(pe['stderr']) and out['status']=='hold' and out['error']==ANALYSIS_WAIT and out['last_child_receipt']==call['result'] and out['child']==parent['child'] and out['completion'] is None,'violation-analysis-wait-parent-natural-exit')
    return [worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]

def analysis_wait_company_job(job,company):
    o.need(all(str(job[k])==str(company[k]) for k in ('company','groupid','start','end_exclusive')),'violation-analysis-wait-company-range')

def analysis_wait_ledger_facts(engine,order,*,live,archives=None):
    kept=[]
    for item,c in zip(engine['companies'],order['companies']):
        ledger=item['artifacts'].get('ledger_current')
        if live:o.need(o.ref(Path(c['root'])/'state.json')==(ledger or {'path':str(Path(c['root'])/'state.json'),'sha256':c['ledger']['sha256']}),'violation-analysis-wait-ledger-changed')
        if ledger:
            kept.append(ledger)
            if live:o.raw(ledger)
            else:
                matches=[r for r in (archives or []) if r['original']==ledger];o.need(len(matches)==1 and matches[0]['archive']['sha256']==ledger['sha256'],'violation-analysis-wait-ledger-archive');o.raw(matches[0]['archive'])
    return kept

def analysis_wait_original(parent,worker_ref,engine_ref,query_ref,release_ref,old_refs,*,installed,live,original_engine_ref=None,original_query_ref=None,adapter_archive=None,ledger_archives=None,quality_archives=None):
    from violation_execution_ports import validate_analysis_fresh_wait
    from violation_execution import view
    folder=o.location(parent['order']);order=o.validate(parent['order']);o.need(parent.get('status')=='hold' and parent.get('error')==ANALYSIS_WAIT and FIELD5 in parent and FIELD6 not in parent and not parent.get('completion') and len(parent['calls'])==6 and all(c.get('state')=='returned' for c in parent['calls']),'violation-analysis-wait-exact-parent')
    base,codes=analysis_wait_sources(parent,release_ref,old_refs,installed=installed,quality_archives=quality_archives);p=o.doc(parent[FIELD5]);old=o.doc(p['parent_archive']);old_engine=o.doc(p['engine_archive']);expected,_=repaired_records_entry(old,old_engine,parent[FIELD5]);expected.update(status='hold',error=ANALYSIS_WAIT,calls=parent['calls'],child=parent['child']);o.need(parent==expected and parent['calls'][:5]==old['calls'],'violation-analysis-wait-parent-delta')
    e=o.doc(engine_ref);origin=original_engine_ref or engine_ref;query=o.doc(query_ref);query_origin=original_query_ref or query_ref;index=e.get('index');o.need(type(index) is int and 0<=index<len(order['companies']) and origin['sha256']==engine_ref['sha256'] and Path(origin['path'])==folder/'engine.json' and e.get('kind')=='violation-execution-v1' and e.get('order')==parent['order'] and e.get('scope_sha256')==order['scope_sha256'] and e.get('status')=='hold' and e.get('phase')=='center-query' and e.get('error')==ANALYSIS_WAIT and e.get('calls') and all(c.get('state')=='returned' and c.get('applied') is True for c in e['calls']),'violation-analysis-wait-exact-engine')
    a=e['companies'][index]['artifacts'];job=o.doc(a['job']);analysis_wait_company_job(job,order['companies'][index]);basefolder=folder/'companies'/str(index);o.need(e['companies'][index]['phase']=='center-query' and query_origin['sha256']==query_ref['sha256'] and Path(query_origin['path'])==basefolder/'center-query.json' and Path(a['job']['path'])==basefolder/'navigation-job.json','violation-analysis-wait-query-path')
    facts=validate_analysis_fresh_wait(query,job,a['job'],basefolder/'center-query.json',parent['tab_id'],adapter_archive=adapter_archive);last=e['calls'][-1];context={'order':order,'company':order['companies'][index],'artifacts':a,'folder':str(basefolder),'phase':'center-query'};o.need(last.get('step')=='center-query' and last.get('company_index')==index and last.get('context')==context and o.doc(last['result'])=={'done':False,'hold':ANALYSIS_WAIT,'journal':query_origin},'violation-analysis-wait-last-return')
    for c in e['calls']:o.doc(c['result'])
    call=parent['calls'][5];la=o.doc(call['launch']);ex=o.doc(call['result']);previous=o.doc(parent['calls'][4]['result']);child={'kind':'violation-execution-child-result-v1','order':parent['order'],'engine':origin,**view(e)}
    o.need(parent.get('child')==child and call['argv']==parent['calls'][0]['argv']==la['argv']==ex['argv'] and Path(call['launch']['path'])==folder/'children/0005-launch.json' and Path(call['result']['path'])==folder/'children/0005-exit.json' and la['order']==parent['order'] and la['index']==5 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==0 and ex['stderr']=='' and json.loads(ex['stdout'])==child and previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-analysis-wait-exact-rc0-child')
    if live:o.need(o.ref(folder/'engine.json')==engine_ref and o.ref(basefolder/'center-query.json')==query_ref,'violation-analysis-wait-state-changed')
    # A later date/query action is never eligible for this metadata transition.
    workers=analysis_wait_worker(parent,worker_ref,call,p['worker']);kept=analysis_wait_ledger_facts(e,order,live=live,archives=ledger_archives)
    return {'engine':origin,'query':query_origin,'analysis':facts,'initial_failed_calls':base['initial_failed_calls'],'successful_wait_call':call,'ledger_refs':kept,'evidence':[*base['evidence'],origin,query_origin,*[facts[n] for n in ('job','before','manifest','adapter','after')],call['launch'],call['result'],*workers]},codes

def repaired_analysis_wait(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD6:proof});current.pop('error');current['resolved_errors'].append({'error':ANALYSIS_WAIT,'normal_wait':True,'recovery':proof});active=copy.deepcopy(engine);active.update(status='running');active.pop('error');active.setdefault('resolved_normal_waits',[]).append({'error':ANALYSIS_WAIT,'last_call':len(active['calls'])-1,'recovery':proof});return current,active

def plan_analysis_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-analysis-wait-canonical-parent');engine_ref=o.ref(folder/'engine.json');e=o.doc(engine_ref);query_ref=o.ref(folder/'companies'/str(e['index'])/'center-query.json');facts,codes=analysis_wait_original(parent,worker_ref,engine_ref,query_ref,release_ref,old_refs,installed=installed,live=True);live_lease(o.validate(parent['order']));return {'kind':KIND6,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'original_query':query_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_analysis_wait(current,proof_ref,*,installed=True,quality_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-analysis-fresh-wait-recovery'/p['original_parent']['sha256'];o.need(p.get('kind')==KIND6 and current.get(FIELD6)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-analysis-wait-canonical-proof')
    original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);index=engine['index'];o.need([r['original'] for r in p['ledger_archives']]==p['facts']['ledger_refs'] and all(Path(r['archive']['path'])==base/'ledgers'/(str(i)+'.json') for i,r in enumerate(p['ledger_archives'])),'violation-analysis-wait-canonical-ledger-archives')
    for n,path in (('parent',folder/'launcher.json'),('engine',folder/'engine.json'),('query',folder/'companies'/str(index)/'center-query.json')):o.need(p[n+'_archive']['sha256']==p['original_'+n]['sha256'] and Path(p['original_'+n]['path'])==path and Path(p[n+'_archive']['path'])==base/('original-'+n+'.json'),'violation-analysis-wait-archives')
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-analysis-wait-source-archives');facts,codes=analysis_wait_original(original,p['worker'],p['engine_archive'],p['query_archive'],p['release'],p['old_sources'],installed=installed,live=False,original_engine_ref=p['original_engine'],original_query_ref=p['original_query'],adapter_archive=p['adapter_archive'],ledger_archives=p['ledger_archives'],quality_archives=quality_archives);expected,active=repaired_analysis_wait(original,engine,proof_ref);live_engine=o.doc(o.ref(folder/'engine.json'))
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:6]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(f)==original[f] for f in (FIELD,FIELD2,FIELD3,FIELD4,FIELD5)) and live_engine.get('order')==active['order'] and live_engine.get('scope_sha256')==active['scope_sha256'] and live_engine['calls'][:len(active['calls'])]==active['calls'] and live_engine.get('resolved_preinput_failures')==active.get('resolved_preinput_failures') and (live_engine.get('resolved_readonly_failures')==active.get('resolved_readonly_failures') if installed else live_engine.get('resolved_readonly_failures',[])[:len(active.get('resolved_readonly_failures',[]))]==active.get('resolved_readonly_failures',[])) and live_engine.get('resolved_normal_waits',[])[:len(active['resolved_normal_waits'])]==active['resolved_normal_waits'],'violation-analysis-wait-history-preserved')
    return {'kind':KIND6,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':facts['initial_failed_calls'],'normal_wait_call':facts['successful_wait_call'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['query_archive'],p['adapter_archive'],*[r['archive'] for r in p['ledger_archives']],p['release'],*p['old_sources'],*[r for r in facts['evidence'] if r not in (p['original_engine'],p['original_query'],facts['analysis']['adapter'])]]}

def recover_analysis_wait(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-analysis-fresh-wait-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-analysis-wait-original-inputs')
        else:
            p=plan_analysis_wait(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['query_archive']=immutable_bytes(base/'original-query.json',o.raw(p['original_query']));p['adapter_archive']=immutable_bytes(base/'original-adapter.json',o.raw(p['facts']['analysis']['adapter']));p['ledger_archives']=[{'original':r,'archive':immutable_bytes(base/'ledgers'/(str(i)+'.json'),o.raw(r))} for i,r in enumerate(p['facts']['ledger_refs'])];p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_analysis_wait(original,engine,proof);current=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current in (original,expected) and current_engine in (engine,active),'violation-analysis-wait-state-changed-no-rewrite');o.need(o.ref(p['original_query']['path'])==p['original_query'],'violation-analysis-wait-query-already-progressed');live_lease(o.validate(current['order']))
        from role_execution_launcher import save
        if current_engine==engine:
            analysis_wait_original(original,worker_ref,p['original_engine'],p['original_query'],release_ref,p['old_sources'],installed=True,live=True);save(folder/'engine.json',active)
        if current==original:save(folder/'launcher.json',expected)
        verify_analysis_wait(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'query_unchanged':p['original_query'],'proof':proof,'ui_used':False,'input_replayed':False,'resume_phase':'center-query','preserved_returned_calls':len(engine['calls'])}

def fragment_worker(parent,worker_ref,call,prior_worker):
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;prior=o.doc(o.doc(prior_worker)['request']);task=request['task'];order=o.validate(parent['order']);expected_attempt=task['id']+'-'+str(int(prior['attempt_id'].rsplit('-',1)[1])+3)
    o.need(type(worker.get('returncode')) is int and worker['returncode']==0 and worker.get('attempt_id')==request['attempt_id']==expected_attempt and Path(worker_ref['path'])==o.PROJECT/'runtime/standalone-workshop-director/attempts'/expected_attempt/'exit.json','violation-analysis-wait-natural-worker')
    o.need(worker['request']['path']==str(attempt/'request.json') and worker['response']['path']==str(attempt/'response.json') and request['kind']=='workshop-worker-request-v1' and task['id']==prior['task']['id'] and task['flow']==o.FLOW and task['day']==order['day'] and task['outer']==prior['task']['outer'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==task['id'] and response['attempt_id']==expected_attempt and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'violation-analysis-wait-original-worker-binding')
    cfg=request['config'];pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[cfg['python'],str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(cfg['project']==str(o.PROJECT) and cfg['coordinator_root']==str(o.PROJECT/'runtime/workshop-director') and cfg['python']==str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==argv and type(pe['returncode']) is int and pe['returncode']==0 and not o.raw(pe['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==call['result'] and out['child']==parent['child'] and out['completion'] is None,'violation-analysis-wait-parent-natural-exit')
    return [worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]
FIELD7='violation_anchor_date_fragment_recovery'
KIND7='verified-violation-anchor-date-fragment-pre-native-recovery-v1'
DATE_ERROR='business-date-and-five-labels-not-eligible'
ANALYSIS_RELEASE_SHA='9f6b070276b5a3e5100b8b5f200f5b5dd45816bddc1b758bc69a2d04df2159ae'
DATE_NAMES={**NAMES,'region_frame_capture.py':'skills/violation-notifier/scripts/region_frame_capture.py','program_region_quality.py':'skills/violation-notifier/scripts/program_region_quality.py'}
def fragment_sources(parent,release_ref,old_refs,*,installed):
    old={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};wanted={n:str(o.PROJECT/p) for n,p in DATE_NAMES.items()};o.need(len(old_refs)==6 and set(old)==set(wanted),'violation-date-fragment-six-before')
    archives=[{'original':{'path':wanted[n],'sha256':old[n]['sha256']},'archive':old[n]} for n in ('region_frame_capture.py','program_region_quality.py')];prior=o.doc(parent[FIELD6]);o.need(prior['release']['sha256']==ANALYSIS_RELEASE_SHA,'violation-date-fragment-exact-prior-release');base=verify_analysis_wait(parent,parent[FIELD6],installed=False,quality_archives=archives);codes=copy.deepcopy(base['code_refs']);by={r['path']:r for r in codes};release=o.doc(release_ref);targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and len(targets)==6 and {t['target'] for t in targets}==set(wanted.values()),'violation-date-fragment-six-source-release')
    for t in targets:
        original=by[t['target']];saved=old[Path(t['target']).name];o.need(t['old_sha256']==original['sha256']==saved['sha256'] and t.get('mode')=='0644','violation-date-fragment-before-source-binding');o.raw(saved);o.raw(t['after']);codes[codes.index(original)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return base,codes

def fragment_pre_native(parent,engine,reply_ref,*,live):
    from violation_execution_ports import region
    business=region.business;folder=o.location(parent['order']);base=folder/'companies/1';a=engine['companies'][1]['artifacts'];source=a['source'];profile=a['profile'];obs=a['frame_state']['observation'];chain='violation-'+folder.name[:24]+'-1';out=base/'frames/0000-anchor';record=o.doc(reply_ref);inputs=region.fc.page_inputs(source,obs,profile);operation={'source':source,'observation':obs,'profile':profile,'pid':parent['pid'],'mode':'anchor','key':chain+':0000-anchor','outdir':str(out),'revision':region.capture_revision(profile),'replaces':None,'chain_id':chain};o.need(record.get('kind')=='public-region-proof-transport-reply-v1' and record.get('stage')=='base' and record.get('operation')==operation and record.get('command')==inputs['command'] and record.get('reply',{}).get('ok') is True,'violation-date-fragment-original-base-binding')
    proof=record['reply']['result'];business.validate_base(proof,inputs);geo=proof['business_date']['geometry'];clips=geo.get('text_clips',[]);o.need(geo.get('rendered') is True and geo.get('box_viewport_contained') is True and geo.get('unsupported_css_absent') is True and geo.get('text_unclipped') is False and geo.get('evidence_eligible') is False and len(clips)==1 and all(h['geometry']['evidence_eligible'] is True for h in proof['business_headers']),'violation-date-fragment-only-original-date-clip');clip=clips[0];o.need(clip['selector']==proof['business_date']['selector'] and clip['supported'] is False and clip['text_overflow']=='clip' and clip['line_clamp']=='none' and clip['overflow_x']==clip['overflow_y']=='clip' and all(type(clip[k]) in (int,float) and __import__('math').isfinite(clip[k]) and clip[k]>0 for k in ('client_width','client_height','scroll_width','scroll_height')) and clip['scroll_width']>clip['client_width'] and clip['scroll_height']==clip['client_height'],'violation-date-fragment-exact-horizontal-clip')
    try:business.prepare_region_request(inputs,proof,'anchor')
    except ValueError as error:o.need(str(error)==DATE_ERROR,'violation-date-fragment-original-error')
    else:raise ValueError('violation-date-fragment-original-failure-required')
    o.need(Path(reply_ref['path']).parent==out/'proof-replies' and Path(reply_ref['path']).name.startswith('base-') and Path(reply_ref['path']).suffix=='.json','violation-date-fragment-original-reply-path')
    if live:
        o.need(list(out.rglob('*.png'))==[] and list((base/'.native-region-frame-state').glob('*.json'))==[] and sorted(p for p in out.rglob('*') if p.is_file())==[Path(reply_ref['path'])],'violation-date-fragment-no-capture-intent-required')
    return {'reply':reply_ref,'operation':operation,'source':source,'profile':profile,'observation':obs,'date_value':proof['business_date']['text'],'no_native_capture_intent':True}

def date_fragment_original(parent,worker_ref,engine_ref,reply_ref,release_ref,old_refs,*,installed,live,original_engine_ref=None):
    folder=o.location(parent['order']);order=o.validate(parent['order']);o.need(parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and FIELD6 in parent and FIELD7 not in parent and not parent.get('completion') and len(parent['calls'])==9 and all(c.get('state')=='returned' for c in parent['calls']),'violation-date-fragment-exact-parent');base,codes=fragment_sources(parent,release_ref,old_refs,installed=installed);prior=o.doc(parent[FIELD6]);old=o.doc(prior['parent_archive']);old_engine=o.doc(prior['engine_archive']);expected,_=repaired_analysis_wait(old,old_engine,parent[FIELD6]);expected.update(status='hold',error='execution-child-stopped',calls=parent['calls'],child=parent['child']);o.need(parent==expected and parent['calls'][:6]==old['calls'],'violation-date-fragment-parent-delta')
    e=o.doc(engine_ref);origin=original_engine_ref or engine_ref;o.need(origin['sha256']==engine_ref['sha256'] and Path(origin['path'])==folder/'engine.json' and e.get('kind')=='violation-execution-v1' and e.get('order')==parent['order'] and e.get('scope_sha256')==order['scope_sha256'] and e.get('status')=='hold' and e.get('phase')=='frames' and e.get('index')==1 and e.get('error')==DATE_ERROR and e.get('calls'),'violation-date-fragment-exact-engine');prefix=e['calls'][:-1];failed=e['calls'][-1];o.need(all(c.get('state')=='returned' and c.get('applied') is True for c in prefix) and failed.get('state')=='failed' and failed.get('step')=='frames' and failed.get('company_index')==1 and failed.get('error')==DATE_ERROR and set(failed)=={'step','company_index','context','state','intent_at','error'},'violation-date-fragment-exact-pre-native-failure')
    for call in prefix:o.doc(call['result'])
    a=e['companies'][1]['artifacts'];o.need(e['companies'][1]['phase']=='frames' and a.get('frame_index')==0 and a.get('frames')==[] and a.get('frame_state',{}).get('phase')=='capture' and a.get('frame_schedule',[None])[0]=={'page':1,'mode':'anchor','notice':None} and failed['context']=={'order':order,'company':order['companies'][1],'artifacts':a,'folder':str(folder/'companies/1'),'phase':'frames'},'violation-date-fragment-first-anchor-context')
    facts=fragment_pre_native(parent,e,reply_ref,live=live);previous=o.doc(parent['calls'][5]['result']);success=[]
    for index in (6,7,8):
        call=parent['calls'][index];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(Path(call['launch']['path'])==folder/'children'/(str(index).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(index).zfill(4)+'-exit.json') and la['index']==index and la['order']==parent['order'] and ex['launch']==call['launch'] and ex['argv']==la['argv']==call['argv'] and previous['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'] and type(ex.get('returncode')) is int and not ex['stderr'],'violation-date-fragment-original-call-chain')
        from role_execution_launcher import command
        argv=call['argv'];args=dict(zip(argv[3::2],argv[4::2]));response={'path':args['--response'],'sha256':args['--response-sha256']} if argv[2]=='accept' else None;o.need(argv==command(parent['order'],argv[2],parent,int(args.get('--steps',100)),response),'violation-date-fragment-derived-argv')
        if index<8:
            child=json.loads(ex['stdout']);o.need(ex['returncode']==0 and child.get('kind')=='violation-execution-child-result-v1' and child.get('order')==parent['order'] and child.get('status')==('waiting' if index==6 else 'running') and child.get('company_index')==1 and Path(child['engine']['path'])==folder/'engine.json','violation-date-fragment-prior-success-preserved');success.append(child)
            if response:o.raw(response)
        else:o.need(ex['returncode']==2 and json.loads(ex['stdout'])=={'ok':False,'error':DATE_ERROR} and argv[2]=='run','violation-date-fragment-exact-child-failure')
        previous=ex
    o.need(parent['child']==success[-1],'violation-date-fragment-original-last-success');workers=fragment_worker(parent,worker_ref,parent['calls'][8],prior['worker'])
    if live:o.need(o.ref(folder/'engine.json')==engine_ref,'violation-date-fragment-live-engine-changed');analysis_wait_ledger_facts(e,order,live=True)
    kept=[a[k] for k in ('job','plan','identity_receipt','company_navigation','center_navigation','center_query_final','query_final','detail_manifest','detail_state','source','profile')]
    for r in kept:o.raw(r)
    return {'engine':origin,'prefix':prefix,'failed_engine_call':failed,'initial_failed_calls':base['initial_failed_calls'],'additional_failed_calls':[{'index':8,'call':parent['calls'][8]}],'pre_native':facts,'evidence':[*base['evidence'],origin,reply_ref,*kept,*[r for c in parent['calls'][6:] for r in (c['launch'],c['result'])],*workers]},codes

def repaired_date_fragment(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD7:proof});current.pop('error');current['resolved_errors'].append({'error':'execution-child-stopped','original_child_error':DATE_ERROR,'recovery':proof});active=copy.deepcopy(engine);failed=active['calls'].pop();active.update(status='running');active.pop('error');active['resolved_readonly_failures'].append({'call':failed,'proof':proof});return current,active

def plan_date_fragment(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','violation-date-fragment-canonical-parent');engine_ref=o.ref(folder/'engine.json');replies=list((folder/'companies/1/frames/0000-anchor/proof-replies').glob('base-*.json'));o.need(len(replies)==1,'violation-date-fragment-sole-base-reply');reply_ref=o.ref(replies[0]);facts,codes=date_fragment_original(parent,worker_ref,engine_ref,reply_ref,release_ref,old_refs,installed=installed,live=True);live_lease(o.validate(parent['order']));return {'kind':KIND7,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_date_fragment(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-anchor-date-fragment-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND7 and current.get(FIELD7)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'violation-date-fragment-canonical-proof')
    for n,path in (('parent',folder/'launcher.json'),('engine',folder/'engine.json')):o.need(p[n+'_archive']['sha256']==p['original_'+n]['sha256'] and Path(p['original_'+n]['path'])==path and Path(p[n+'_archive']['path'])==base/('original-'+n+'.json'),'violation-date-fragment-original-archives')
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'violation-date-fragment-source-archives');original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=date_fragment_original(original,p['worker'],p['engine_archive'],p['facts']['pre_native']['reply'],p['release'],p['old_sources'],installed=installed,live=False,original_engine_ref=p['original_engine']);expected,active=repaired_date_fragment(original,engine,proof_ref);live_engine=o.doc(o.ref(folder/'engine.json'));o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:9]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(f)==original[f] for f in (FIELD,FIELD2,FIELD3,FIELD4,FIELD5,FIELD6)) and live_engine['calls'][:len(active['calls'])]==active['calls'] and all(live_engine.get(k)==active.get(k) for k in ('order','scope_sha256','resolved_preinput_failures','resolved_readonly_failures','resolved_normal_waits')),'violation-date-fragment-history-preserved');return {'kind':KIND7,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':facts['initial_failed_calls'],'additional_failed_calls':facts['additional_failed_calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['release'],*p['old_sources'],*[r for r in facts['evidence'] if r!=p['original_engine']]]}

def recover_date_fragment(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-anchor-date-fragment-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for f in (a,b):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and sorted((Path(r['path']).name,r['sha256']) for r in p['old_sources'])==sorted((Path(r['path']).name,r['sha256']) for r in old_refs),'violation-date-fragment-original-inputs')
        else:
            p=plan_date_fragment(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r)) for r in old_refs];proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_date_fragment(original,engine,proof);current=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current in (original,expected) and current_engine in (engine,active),'violation-date-fragment-state-changed-no-rewrite');fragment_pre_native(original,engine,p['facts']['pre_native']['reply'],live=True);live_lease(o.validate(current['order']))
        from role_execution_launcher import save
        if current_engine==engine:
            date_fragment_original(original,worker_ref,p['original_engine'],p['facts']['pre_native']['reply'],release_ref,p['old_sources'],installed=True,live=True);save(folder/'engine.json',active)
        if current==original:save(folder/'launcher.json',expected)
        verify_date_fragment(o.doc(o.ref(folder/'launcher.json')),proof);return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False,'input_replayed':False,'resume_phase':'frames','same_source_profile':True}

# Generic completed-navigation / known readonly preparation failure; data-only recovery.
FIELD8='violation_confirmed_navigation_wait_recovery'
KIND8='verified-confirmed-navigation-readonly-wait-recovery-v1'
WAIT_ERROR='company-search-loading-structure-unverified'
WAIT_NAMES={n:str(PROJECT/p) for n,p in {
 'company_search_wait.py':'skills/douyin-laike-operator/scripts/company_search_wait.py',
 'company_search_recovery.py':'skills/douyin-laike-operator/scripts/company_search_recovery.py',
 'violation_initial_ledger_recovery.py':'skills/violation-notifier/scripts/violation_initial_ledger_recovery.py',
 'role_execution_launcher.py':'skills/workshop-director/scripts/role_execution_launcher.py',
 'role_execution_orchestration.py':'skills/workshop-director/scripts/role_execution_orchestration.py'}.items()}

def _readonly_wait_operator():
    scripts=PROJECT/'skills/douyin-laike-operator/scripts'
    if str(scripts) not in sys.path:sys.path.insert(0,str(scripts))
    import company_search_recovery as recovery
    o.need(Path(recovery.__file__).resolve()==scripts/'company_search_recovery.py','readonly-wait-fixed-operator-helper')
    return recovery

def _readonly_wait_doc(reference,materials=()):
    matches=[x for x in materials if x['original']==reference]
    o.need(len(matches)<=1,'readonly-wait-duplicate-material')
    if matches:
        archive=matches[0]['archive'];o.need(archive['sha256']==reference['sha256'],'readonly-wait-material-hash');return _violation_completed_doc(archive)
    return _violation_completed_doc(reference)


def readonly_wait_sources(parent,release_ref,old_refs,*,installed):
    release=o.doc(release_ref);targets=release.get('targets',[]);by={r['path']:r for r in parent['code_refs']};saved={Path(r['path']).name.removesuffix('.before'):r for r in old_refs}
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and len(targets)==5 and {t['target']for t in targets}==set(WAIT_NAMES.values()) and not release.get('data_targets') and len(old_refs)==5 and set(saved)==set(WAIT_NAMES),'readonly-wait-exact-five-reviewed-sources')
    codes=copy.deepcopy(parent['code_refs'])
    for t in targets:
        path=t['target'];before=by.get(path);archive=saved[Path(path).name]
        o.need(before is not None and t['old_sha256']==before['sha256']==archive['sha256'] and t.get('mode')=='0644','readonly-wait-before-archive-binding');o.raw(archive);o.raw(t['after']);codes[codes.index(before)]={'path':path,'sha256':t['after']['sha256']}
        if Path(path).name in ('company_search_wait.py','company_search_recovery.py'):o.need(t['after']['sha256']=={'company_search_wait.py':'81c2822a957ba5a961c39f1e96bb4eb9c71a8819e256502fbef0b794ff45b089','company_search_recovery.py':'f48372c746dd699aaa6c4fecb7e14ac563d07b088a3dd66caae402af2fa7ab6c'}[Path(path).name],'readonly-wait-frozen-operator-after')
    for r in codes:
        if installed or r['path']not in WAIT_NAMES.values():o.raw(r)
    return codes

def _readonly_wait_receipt_absent(folder,count):
    path=Path(folder)/'receipts'/(str(count).zfill(5)+'.json')
    o.need(not path.exists() and not path.is_symlink(),'readonly-wait-original-failed-result-must-be-absent')
    return str(path)

def readonly_wait_original(parent,worker_ref,engine_ref,*,live,materials=(),original_engine_ref=None):
    read=lambda r:_readonly_wait_doc(r,materials)
    order=o.validate(parent['order']);folder=o.location(parent['order']);engine=read(engine_ref)
    o.need(parent.get('kind')=='role-execution-launcher-v1' and parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and not parent.get('completion') and not parent.get('child') and FIELD8 not in parent,'readonly-wait-original-parent-hold')
    origin=read(parent['origin_ref']);o.need(all(parent.get(k)==v for k,v in origin.items()),'readonly-wait-original-outer-identity')
    o.need(parent.get('calls') and all(c.get('state')=='returned' for c in parent['calls']),'readonly-wait-returned-parent-prefix')
    o.need(engine.get('kind')=='violation-execution-v1' and engine.get('order')==parent['order'] and engine.get('scope_sha256')==order['scope_sha256'] and engine.get('status')=='hold' and engine.get('phase')=='company' and engine.get('error')==WAIT_ERROR and not any(engine.get(k)for k in ('completion','delivery','handoff','acceptance')),'readonly-wait-original-company-engine')
    index=engine['index'];o.need(type(index)is int and 0<=index<len(order['companies']) and len(engine['companies'])==len(order['companies']),'readonly-wait-company-index')
    company=order['companies'][index];active=engine['companies'][index];artifacts=active['artifacts'];calls=engine['calls'];o.need(calls and active['phase']=='company' and set(artifacts)=={'job','plan','identity_receipt'},'readonly-wait-before-company-output')
    failed=calls[-1];prefix=calls[:-1]
    o.need(set(failed)=={'step','company_index','context','state','intent_at','error'} and failed.get('state')=='failed' and failed.get('step')=='company' and failed.get('company_index')==index and failed.get('error')==WAIT_ERROR and failed['context']=={'order':order,'company':company,'artifacts':artifacts,'folder':str(folder/'companies'/str(index)),'phase':'company'},'readonly-wait-exact-last-resultless-call')
    original_engine_ref=original_engine_ref or engine_ref
    o.need(original_engine_ref['path']==str(folder/'engine.json') and original_engine_ref['sha256']==engine_ref['sha256'],'readonly-wait-original-engine-reference')
    evidence=[parent['order'],parent['origin_ref'],original_engine_ref]
    for i,c in enumerate(prefix):
        o.need(c.get('state')=='returned' and c.get('applied')is True and c.get('result',{}).get('path')==str(folder/'receipts'/(str(i+1).zfill(5)+'.json')),'readonly-wait-prior-returned-prefix');read(c['result']);evidence.append(c['result'])
    absent=str(folder/'receipts'/(str(len(calls)).zfill(5)+'.json'))
    if live:_readonly_wait_receipt_absent(folder,len(calls))
    job_ref=artifacts['job'];job=read(job_ref);o.need(Path(job_ref['path'])==folder/'companies'/str(index)/'navigation-job.json' and job['company']==company['company'] and str(job['groupid'])==company['groupid'] and (job.get('start'),job.get('end_exclusive'))==(company['start'],company['end_exclusive']),'readonly-wait-original-navigation-job')
    base=folder/'companies'/str(index)/'company-navigation';operator_job_ref=o.ref(base/'work-order.json') if live else next(x['original']for x in materials if x['original']['path']==str(base/'work-order.json'));operator_state_ref=o.ref(base/'workflow.json') if live else next(x['original']for x in materials if x['original']['path']==str(base/'workflow.json'));operator_job=read(operator_job_ref);operator=read(operator_state_ref);tree_ref=operator['last_tree'];tree=read(tree_ref)
    o.need(operator_job['company']==company['company'] and str(operator_job['groupid'])==company['groupid'] and operator_job['workflow_path']==str(base/'workflow.json') and operator_job['work_order_path']==str(base/'work-order.json') and operator['tab_id']==parent['tab_id'],'readonly-wait-same-operator-order')
    _readonly_wait_operator().block_contract(operator_job,operator,tree,base/'work-order.json')
    for key in ('job','plan','identity_receipt'):read(artifacts[key]);evidence.append(artifacts[key])
    previous=parent['start_monotonic']
    for i,c in enumerate(parent['calls']):
        la=read(c['launch']);ex=read(c['result']);o.need(Path(c['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(c['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json') and la['index']==i and la['order']==parent['order'] and ex['launch']==c['launch'] and ex['argv']==la['argv']==c['argv'] and previous<=la['launched_monotonic']<=ex['exited_monotonic'] and type(ex.get('returncode'))is int and ex['stderr']=='','readonly-wait-child-prefix-binding')
        argv=c['argv'];o.need(len(argv)>=3 and argv[2]=='run' and len(argv[3:])%2==0,'readonly-wait-readonly-run-child');args=dict(zip(argv[3::2],argv[4::2]));from role_execution_launcher import command
        o.need(argv==command(parent['order'],'run',parent,int(args.get('--steps',100))),'readonly-wait-derived-child-argv')
        if i==len(parent['calls'])-1:o.need(ex['returncode']==2 and json.loads(ex['stdout'])=={'ok':False,'error':WAIT_ERROR},'readonly-wait-exact-leaf-exit')
        else:o.need(ex['returncode']==0,'readonly-wait-no-unadmitted-prior-child')
        previous=ex['exited_monotonic'];evidence.extend([c['launch'],c['result']])
    worker=read(worker_ref);request=read(worker['request']);response=read(worker['response']);attempt=Path(worker_ref['path']).parent;task=request['task'];cfg=request['config'];last=parent['calls'][-1]
    o.need(worker.get('kind')=='workshop-worker-exit-v1' and type(worker.get('returncode'))is int and worker['returncode']==0 and worker['attempt_id']==request['attempt_id'] and Path(worker_ref['path'])==PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json' and request['attempt_id'].startswith(task['id']+'-') and worker['request']['path']==str(attempt/'request.json') and worker['response']['path']==str(attempt/'response.json'),'readonly-wait-natural-worker-exit')
    o.need(request['kind']=='workshop-worker-request-v1' and task['flow']==o.FLOW and task['day']==order['day'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==task['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and read(request['config_ref'])==cfg,'readonly-wait-same-worker-task-order')
    outer=task['outer'];o.need(outer['boot']==parent['boot_identity'] and outer['clock_contract']==parent['clock_contract'] and outer['start_monotonic']<=parent['start_monotonic'] and datetime.fromisoformat(outer['started_at'])<=datetime.fromisoformat(parent['wall_started_at']),'readonly-wait-original-outer-clock')
    pe_ref=o.ref(attempt/'parent-run-exit.json') if live else next(x['original']for x in materials if x['original']['path']==str(attempt/'parent-run-exit.json'));pe=read(pe_ref);stdout=_readonly_wait_doc(pe['stdout'],materials);expected=[cfg['python'],str(PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps',args.get('--steps','100')]
    o.need(cfg['project']==str(PROJECT) and cfg['coordinator_root']==str(PROJECT/'runtime/workshop-director') and cfg['python']==str(PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==expected and type(pe['returncode'])is int and pe['returncode']==0 and stdout['status']=='hold' and stdout['error']=='execution-child-stopped' and stdout['last_child_receipt']==last['result'] and stdout['child']==parent.get('child') and stdout['completion']is None,'readonly-wait-parent-natural-exit')
    # Raw stderr is not JSON; exact empty hash checked through byte reader.
    stderr_match=[x for x in materials if x['original']==pe['stderr']];o.need(not o.raw(stderr_match[0]['archive']if stderr_match else pe['stderr']),'readonly-wait-parent-stderr')
    evidence.extend([worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr'],operator_job_ref,operator_state_ref,tree_ref])
    if live:ledger_facts(order,live=True);o.need(o.ref(folder/'engine.json')==engine_ref,'readonly-wait-current-engine-ref')
    return {'order':order,'company_index':index,'failed_engine_index':len(calls)-1,'failed_engine_call':failed,'engine_prefix':prefix,'failed_child_index':len(parent['calls'])-1,'failed_parent_child':last,'absent_receipt_path':absent,'operator_job':operator_job_ref,'operator_state':operator_state_ref,'operator_tree':tree_ref,'worker_task_id':task['id'],'original_outer':outer,'evidence':list({(r['path'],r['sha256']):r for r in evidence}.values())}

def repaired_readonly_wait(parent,engine,proof_ref):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD8:proof_ref});current.pop('error');current.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':WAIT_ERROR,'recovery':proof_ref})
    active=copy.deepcopy(engine);index=len(active['calls'])-1;failed=active['calls'].pop();active.update(status='running');active.pop('error');active.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':proof_ref})
    return current,active

def plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','readonly-wait-canonical-parent');engine_ref=o.ref(folder/'engine.json');facts=readonly_wait_original(parent,worker_ref,engine_ref,live=True);live_lease(facts['order']);codes=readonly_wait_sources(parent,release_ref,old_refs,installed=installed)
    return {'kind':KIND8,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_readonly_wait(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.confirmed-navigation-readonly-wait-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND8 and current.get(FIELD8)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used']is False and datetime.fromisoformat(p['at']).utcoffset()is not None,'readonly-wait-canonical-proof')
    original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(p['parent_archive']['sha256']==p['original_parent']['sha256'] and p['engine_archive']['sha256']==p['original_engine']['sha256'] and p['original_parent']['path']==str(folder/'launcher.json') and p['original_engine']['path']==str(folder/'engine.json') and p['parent_archive']['path']==str(base/'original-parent.json') and p['engine_archive']['path']==str(base/'original-engine.json'),'readonly-wait-original-state-archives')
    for x in p['materials']:o.need(x['archive']['sha256']==x['original']['sha256'] and Path(x['archive']['path'])==base/'materials'/(x['original']['sha256']+Path(x['original']['path']).suffix),'readonly-wait-canonical-material');o.raw(x['archive'])
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'readonly-wait-canonical-source-archives')
    facts=readonly_wait_original(original,p['worker'],p['engine_archive'],live=False,materials=p['materials'],original_engine_ref=p['original_engine']);codes=readonly_wait_sources(original,p['release'],p['old_sources'],installed=installed);expected,active=repaired_readonly_wait(original,engine,proof_ref)
    o.need(facts==p['facts'] and codes==p['code_refs'] and current['calls'][:len(original['calls'])]==original['calls'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(k)==original.get(k) for k in ('order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','origin_ref')),'readonly-wait-parent-history-preserved')
    live_engine=o.doc(o.ref(folder/'engine.json'));o.need(live_engine['calls'][:len(active['calls'])]==active['calls'] and live_engine.get('resolved_readonly_failures',[])[:len(active['resolved_readonly_failures'])]==active['resolved_readonly_failures'] and live_engine['order']==engine['order'] and live_engine['scope_sha256']==engine['scope_sha256'],'readonly-wait-engine-prefix-preserved')
    recovery=_readonly_wait_operator();operator_proof=o.doc(p['operator_recovery']);operator_folder=Path(facts['operator_state']['path']).parent
    o.need(p['operator_recovery']['path']==str(operator_folder/'company-search-loading-recovery'/facts['operator_state']['sha256']/'block-recovery-proof.json') and operator_proof['original_journal']['sha256']==facts['operator_state']['sha256'] and operator_proof['original_job']['sha256']==facts['operator_job']['sha256'] and operator_proof['canonical_tree']==facts['operator_tree'] and operator_proof['original_job_path']==facts['operator_job']['path'],'readonly-wait-exact-operator-recovery-binding')
    archived_operator=_readonly_wait_doc(facts['operator_state'],p['materials']);recovered_operator=copy.deepcopy(archived_operator);recovered_operator.pop('last_error');recovered_operator['company_search_loading_recovery']={'kind':recovery.BLOCK_KIND,'proof':p['operator_recovery']};recovery.verify_block_recovered(recovered_operator,p['operator_recovery'])
    job=_readonly_wait_doc(facts['operator_job'],p['materials']);o.raw(facts['operator_job']);now_operator=o.doc(o.ref(Path(job['workflow_path'])));o.need(now_operator.get('calls',[])[:len(archived_operator['calls'])]==archived_operator['calls'] and all(c.get('state')=='confirmed' for c in now_operator.get('calls',[])) and now_operator.get('company_search_loading_recovery')==recovered_operator['company_search_loading_recovery'] and all(now_operator.get(k)==archived_operator.get(k) for k in ('fingerprint','work_order_id','company','groupid','date_range','tab_id','initial_groupid')),'readonly-wait-operator-history-preserved')
    return {'kind':KIND8,'proof':proof_ref,'code_refs':codes,'initial_failed_calls':[],'additional_failed_calls':[{'index':facts['failed_child_index'],'call':facts['failed_parent_child']}],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['operator_recovery'],p['release'],*p['old_sources'],*[x['archive']for x in p['materials']]]}

def recover_readonly_wait(parent_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as la,(folder/'engine.lock').open('a')as en:
        for f in (la,en):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        proof_path=base/'proof.json'
        if proof_path.exists():
            p=o.doc(o.ref(proof_path));o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and [(Path(r['path']).name,r['sha256'])for r in p['old_sources']]==[(Path(r['path']).name,r['sha256'])for r in old_refs],'readonly-wait-same-transaction-required')
        else:
            plan_path=base/'plan.json'
            if plan_path.exists():p=o.doc(o.ref(plan_path));o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref,'readonly-wait-same-plan-required')
            else:
                p=plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['materials']=[{'original':r,'archive':immutable_bytes(base/'materials'/(r['sha256']+Path(r['path']).suffix),o.raw(r))}for r in p['facts']['evidence']];p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r))for r in old_refs];o.immutable(plan_path,p)
            original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(o.doc(o.ref(folder/'launcher.json'))==original and o.doc(o.ref(folder/'engine.json'))==engine,'readonly-wait-no-state-advance-before-proof');readonly_wait_sources(original,release_ref,p['old_sources'],installed=True);_readonly_wait_receipt_absent(folder,len(engine['calls']));live_lease(o.validate(original['order']))
            job=_readonly_wait_doc(p['facts']['operator_job'],p['materials']);operator_result=_readonly_wait_operator().reconcile_block_loading(Path(job['work_order_path']),p['facts']['operator_state']['sha256']);p['operator_recovery']=operator_result['proof'];o.immutable(proof_path,p)
        proof=o.ref(proof_path);original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);expected,active=repaired_readonly_wait(original,engine,proof);cur=o.doc(o.ref(folder/'launcher.json'));eng=o.doc(o.ref(folder/'engine.json'));o.need(cur in (original,expected) and eng in (engine,active),'readonly-wait-metadata-CAS-conflict');_readonly_wait_receipt_absent(folder,len(engine['calls']));live_lease(o.validate(original['order']));readonly_wait_sources(original,release_ref,p['old_sources'],installed=True)
        operator_job=_readonly_wait_doc(p['facts']['operator_job'],p['materials']);o.raw(p['facts']['operator_job'])
        _readonly_wait_operator().verify_block_recovered(o.doc(o.ref(Path(operator_job['workflow_path']))),p['operator_recovery']) # Initial transaction/reentry is exact; history verification alone permits later progress.
        from role_execution_launcher import save
        if eng==engine:save(folder/'engine.json',active)
        if cur==original:save(folder/'launcher.json',expected)
        verify_readonly_wait(o.doc(o.ref(folder/'launcher.json')),proof)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False,'input_replayed':False,'resume_phase':'company'}


# Successor nodes retain FIELD8. No live reads or operator reconciliation here.
_WAIT8_INITIAL_PLAN=plan_readonly_wait
_WAIT8_INITIAL_RECOVER=recover_readonly_wait
_WAIT8_INITIAL_VERIFY=verify_readonly_wait
WAIT8_SUCCESSOR_KIND='reviewed-confirmed-governance-switch-readonly-successor-v1'
WAIT8_PROVIDER='confirmed-governance-source-switch-readonly-v1'
WAIT8_NEXT_ERROR='execution-company-navigation-unresolved'
WAIT8_SUCCESSOR_PATHS={str(PROJECT/'skills'/p)for p in ('douyin-laike-operator/scripts/switch_read_recovery.py','violation-notifier/scripts/violation_execution_ports.py','violation-notifier/scripts/violation_initial_ledger_recovery.py')}

def _wait8_switch():
    scripts=PROJECT/'skills/douyin-laike-operator/scripts'
    if str(scripts)not in sys.path:sys.path.insert(0,str(scripts))
    import switch_read_recovery as switch
    o.need(Path(switch.__file__).resolve()==scripts/'switch_read_recovery.py','readonly-successor-fixed-switch-provider')
    return switch

def _wait8_data_graph(parent,release_ref,old_sources,previous_codes=None):
    release=o.doc(release_ref);supersession=release.get('source_supersession')
    if supersession is None:return _wait8_data_graph_step(parent,release_ref,old_sources,previous_codes)
    o.need(type(supersession)is dict and set(supersession)=={'kind','previous_source_release'} and supersession['kind']==WAIT8_SOURCE_SUPERSESSION_KIND and supersession['previous_source_release']==WAIT8_UNCONSUMED_SCHEMA_RELEASE and release_ref!=WAIT8_UNCONSUMED_SCHEMA_RELEASE and previous_codes is not None,'readonly-source-supersession-fixed-one-publication')
    original=o.doc(WAIT8_UNCONSUMED_SCHEMA_RELEASE);authority=release.get('confirmed_navigation_wait_successor',{})
    o.need('source_supersession'not in original and authority==original.get('confirmed_navigation_wait_successor') and authority.get('kind')==WAIT8_SCHEMA_KIND and authority.get('provider')==WAIT8_SCHEMA_PROVIDER and release.get('previous_release')==original.get('previous_release')==authority.get('previous_release'),'readonly-source-supersession-same-metadata-authority')
    targets=original.get('targets',[])
    o.need(len(targets)==2 and {t.get('target')for t in targets}==WAIT8_SCHEMA_PATHS and all('before'in t and t['before']['sha256']==t['old_sha256']for t in targets),'readonly-source-supersession-original-before-archives')
    # The fixed old Root and both payload/archive pairs are data, never executed.
    intermediate=_wait8_data_graph_step(parent,WAIT8_UNCONSUMED_SCHEMA_RELEASE,[t['before']for t in targets],previous_codes)
    return _wait8_data_graph_step(parent,release_ref,old_sources,intermediate)

def _wait8_original_states(p,reference):
    parent=_violation_completed_doc(p['parent_archive']);engine=_violation_completed_doc(p['engine_archive']);folder=o.location(parent['order']);base=folder/'.confirmed-navigation-readonly-wait-recovery'/p['original_parent']['sha256']
    o.need(p['kind']==KIND8 and p.get('ui_used')is False and Path(reference['path'])==base/'proof.json' and p['parent_archive']=={'path':str(base/'original-parent.json'),'sha256':p['original_parent']['sha256']} and p['engine_archive']=={'path':str(base/'original-engine.json'),'sha256':p['original_engine']['sha256']} and p['original_parent']['path']==str(folder/'launcher.json') and p['original_engine']['path']==str(folder/'engine.json') and datetime.fromisoformat(p['at']).utcoffset()is not None,'readonly-successor-canonical-node')
    for x in p['materials']:o.need(x['archive']['sha256']==x['original']['sha256'] and Path(x['archive']['path'])==base/'materials'/(x['original']['sha256']+Path(x['original']['path']).suffix),'readonly-successor-material-binding');_violation_completed_raw(x['archive'])
    o.need(all(Path(r['path'])==base/'sources'/Path(r['path']).name for r in p['old_sources']),'readonly-successor-source-archive-path')
    return parent,engine


def _wait8_switch_facts(authority,resume_proof):
    switch=_wait8_switch();owned=authority['original_workflow'];held_ref=owned['original'];archive=owned['archive'];o.need(held_ref['sha256']==archive['sha256'],'readonly-successor-held-archive-hash');held=o.doc(archive);job=o.doc(authority['operator_job']);o.need(held_ref['path']==job['workflow_path'],'readonly-successor-held-canonical-path');schema=authority.get('kind')==WAIT8_SCHEMA_KIND;o.need(authority.get('kind')in (WAIT8_SUCCESSOR_KIND,WAIT8_SCHEMA_KIND) and (not schema or authority.get('provider')==WAIT8_SCHEMA_PROVIDER and 'original_hold_sample'not in authority),'readonly-successor-reviewed-provider-authority');scope=switch.governance_source_resume_facts(job,held,held_ref) if schema else switch.governance_route_resume_facts(job,held,held_ref,authority['original_hold_sample'])
    if resume_proof is None:return {'scope':scope,'held':held,'job':job,'expected_operator':None}
    proof=switch.document(resume_proof);directory=Path(job['workflow_path']).parent/'switch-read-recovery'/held_ref['sha256'];path=Path(resume_proof['path'])
    o.need(path.parent.parent==directory and path.name=='recovery-proof.json' and __import__('re').fullmatch('attempt-[0-9a-f]{32}',path.parent.name)is not None and proof['original_journal']['sha256']==held_ref['sha256'] and switch.document(proof['original_journal'])==held and proof['job']['sha256']==authority['operator_job']['sha256'] and switch.document(proof['job'])==job and proof['original_tree_ref']==held['last_tree'],'readonly-successor-exact-readonly-resume-proof')
    expected=copy.deepcopy(held);expected.update(phase='accountAfterSwitch',revision=held['revision']+1,last_tree=switch.ref(Path(proof['sample']['path']).with_name(Path(proof['sample']['path']).name.replace('-sample.json','-tree.json'))),switch_read_recovery=resume_proof,updated_at=proof['at']);expected.pop('waiting_for',None);expected.pop('company_switch_wait_started',None)
    if expected.get('last_error'):expected.setdefault('resolved_errors',[]).append({**expected.pop('last_error'),'resolved_at':proof['at'],'next_phase':'accountAfterSwitch','recovery_proof':resume_proof})
    verified=switch.verify_recovered(expected,resume_proof)
    return {'scope':scope,'held':held,'job':job,'expected_operator':expected,'resume_facts':verified}

def _wait8_children_worker(parent,worker_ref,known_failed,read,expected_error=WAIT8_NEXT_ERROR):
    order=_violation_completed_order(parent['order']);folder=o.location(parent['order']);previous=parent['start_monotonic'];evidence=[];calls=parent['calls'];o.need(calls and all(c.get('state')=='returned'for c in calls),'readonly-successor-returned-children')
    for i,c in enumerate(calls):
        la=read(c['launch']);ex=read(c['result']);o.need(Path(c['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(c['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json') and la['index']==i and la['order']==parent['order'] and ex['launch']==c['launch'] and c['argv']==la['argv']==ex['argv'] and previous<=la['launched_monotonic']<=ex['exited_monotonic'] and ex['stderr']=='' and type(ex.get('returncode'))is int,'readonly-successor-child-binding')
        argv=c['argv'];o.need(len(argv)>=3 and argv[2]=='run' and len(argv[3:])%2==0,'readonly-successor-run-only');args=dict(zip(argv[3::2],argv[4::2]));from role_execution_launcher import command
        o.need(argv==command(parent['order'],'run',parent,int(args.get('--steps',100))),'readonly-successor-derived-child-command')
        if i==len(calls)-1:o.need(ex['returncode']==2 and json.loads(ex['stdout'])=={'ok':False,'error':expected_error},'readonly-successor-known-last-child')
        else:o.need(ex['returncode']==(2 if any(x['index']==i and x['call']==c for x in known_failed)else 0),'readonly-successor-no-other-failed-child')
        previous=ex['exited_monotonic'];evidence.extend([c['launch'],c['result']])
    worker=read(worker_ref);request=read(worker['request']);response=read(worker['response']);attempt=Path(worker_ref['path']).parent;task=request['task'];cfg=request['config'];o.need(worker.get('kind')=='workshop-worker-exit-v1' and type(worker.get('returncode'))is int and worker['returncode']==0 and worker['attempt_id']==request['attempt_id'] and Path(worker_ref['path'])==PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']/'exit.json' and request['attempt_id'].startswith(task['id']+'-') and worker['request']['path']==str(attempt/'request.json') and worker['response']['path']==str(attempt/'response.json'),'readonly-successor-natural-worker')
    o.need(request['kind']=='workshop-worker-request-v1' and task['flow']==o.FLOW and task['day']==order['day'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==task['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and read(request['config_ref'])==cfg,'readonly-successor-original-worker-binding')
    outer=task['outer'];o.need(outer['boot']==parent['boot_identity'] and outer['clock_contract']==parent['clock_contract'] and outer['start_monotonic']<=parent['start_monotonic'] and datetime.fromisoformat(outer['started_at'])<=datetime.fromisoformat(parent['wall_started_at']),'readonly-successor-original-outer')
    pe_ref=o.ref(attempt/'parent-run-exit.json');pe=read(pe_ref);stdout=read(pe['stdout']);need_argv=[cfg['python'],str(PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps',args.get('--steps','100')]
    o.need(cfg['project']==str(PROJECT) and cfg['coordinator_root']==str(PROJECT/'runtime/workshop-director') and cfg['python']==str(PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==need_argv and type(pe.get('returncode'))is int and pe['returncode']==0 and stdout['status']=='hold' and stdout['error']=='execution-child-stopped' and stdout['last_child_receipt']==calls[-1]['result'] and stdout['child']==parent.get('child') and stdout['completion']is None and not _violation_completed_raw(pe['stderr']),'readonly-successor-parent-natural-exit')
    evidence.extend([worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]);return evidence,task['id'],outer


def _wait8_repaired(parent,engine,proof):
    current=copy.deepcopy(parent);current.update(status='running',**{FIELD8:proof});current.pop('error');current.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':engine['error'],'recovery':proof});active=copy.deepcopy(engine);index=len(active['calls'])-1;failed=active['calls'].pop();active.update(status='running');active.pop('error');active.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':proof});return current,active

def _wait8_successor_original(parent,worker_ref,engine_ref,authority,previous,*,live,materials=(),original_engine_ref=None):
    read=lambda r:_readonly_wait_doc(r,materials);order=o.validate(parent['order']);folder=o.location(parent['order']);engine=read(engine_ref);prior_parent,prior_engine=previous['active_parent'],previous['active_engine'];held=_wait8_switch_facts(authority,None);schema=authority.get('kind')==WAIT8_SCHEMA_KIND;expected_error=WAIT8_SCHEMA_ERROR if schema else WAIT8_NEXT_ERROR
    o.need(parent.get('kind')=='role-execution-launcher-v1' and parent.get('status')=='hold' and parent.get('error')=='execution-child-stopped' and not parent.get('completion') and not parent.get('child') and parent.get(FIELD8)==authority['previous_recovery'],'readonly-successor-original-parent-hold')
    o.need(parent['calls'][:len(prior_parent['calls'])]==prior_parent['calls'] and parent.get('resolved_errors',[])[:len(prior_parent['resolved_errors'])]==prior_parent['resolved_errors'] and all(parent.get(k)==v for k,v in read(parent['origin_ref']).items()) and all(parent.get(k)==prior_parent.get(k)for k in ('order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','origin_ref')),'readonly-successor-parent-prefix-unchanged')
    o.need(engine.get('kind')=='violation-execution-v1' and engine['order']==parent['order'] and engine['scope_sha256']==order['scope_sha256'] and engine.get('status')=='hold' and engine.get('phase')=='company' and engine.get('error')==expected_error and not any(engine.get(k)for k in ('completion','delivery','handoff','acceptance')) and engine['calls'][:len(prior_engine['calls'])]==prior_engine['calls'] and engine.get('resolved_readonly_failures',[])[:len(prior_engine['resolved_readonly_failures'])]==prior_engine['resolved_readonly_failures'],'readonly-successor-original-engine-prefix')
    index=engine['index'];o.need(type(index)is int and 0<=index<len(order['companies']) and len(engine['companies'])==len(order['companies']),'readonly-successor-company-index');company=order['companies'][index];artifacts=engine['companies'][index]['artifacts'];failed=engine['calls'][-1]
    o.need(engine['companies'][index]['phase']=='company' and set(artifacts)=={'job','plan','identity_receipt'} and set(failed)=={'step','company_index','context','state','intent_at','error'} and failed['step']=='company' and failed['company_index']==index and failed['state']=='failed' and failed['error']==expected_error and failed['context']=={'order':order,'company':company,'artifacts':artifacts,'folder':str(folder/'companies'/str(index)),'phase':'company'},'readonly-successor-exact-resultless-company-failure')
    job=held['job'];wf=held['held'];o.need(job['company']==company['company'] and str(job['groupid'])==company['groupid'] and job['workflow_path']==str(folder/'companies'/str(index)/'company-navigation/workflow.json') and wf['tab_id']==parent['tab_id'],'readonly-successor-original-company-job')
    absent=str(folder/'receipts'/(str(len(engine['calls'])).zfill(5)+'.json'));evidence=[parent['order'],parent['origin_ref'],original_engine_ref or engine_ref,authority['original_workflow']['archive'],authority['operator_job'],*([authority['original_hold_sample']] if not schema else held['scope']['historical_refs'])]
    for i,c in enumerate(engine['calls'][:-1]):o.need(c.get('state')=='returned' and c.get('applied')is True and c.get('result',{}).get('path')==str(folder/'receipts'/(str(i+1).zfill(5)+'.json')),'readonly-successor-returned-prefix');read(c['result']);evidence.append(c['result'])
    refs,task,outer=_wait8_children_worker(parent,worker_ref,previous['failed_children'],read,expected_error);o.need(task==previous['facts']['worker_task_id'] and outer==previous['facts']['original_outer'],'readonly-successor-same-task-and-outer');evidence.extend(refs)
    for r in artifacts.values():read(r);evidence.append(r)
    if schema:
        o.need(all(c.get('phase')=='ready'for c in engine['companies'][:index]),'readonly-schema-earlier-company-not-ready')
        def collect(v):
            if isinstance(v,dict):
                if set(v)=={'path','sha256'}:read(v);evidence.append(v)
                else:
                    for value in v.values():collect(value)
            elif isinstance(v,list):
                for value in v:collect(value)
        collect(engine['companies'][:index])
        for i,completed in enumerate(engine['companies'][:index]):
            c=order['companies'][i];a=completed['artifacts'];ready=[call for call in engine['calls'][:-1]if call.get('company_index')==i and call.get('step')=='ready'];o.need(ready,'readonly-schema-applied-ready-receipt-required');call=ready[-1];result=read(call['result']);expected={'batch':a['batch'],'ledger_current':a['ledger_current']}
            o.need(call.get('applied')is True and call.get('state')=='returned' and call['context']['company']==c and call['context']['artifacts']['source']==a['source'] and result.get('done')is True and result.get('artifacts')==expected,'readonly-schema-ready-ledger-update-binding')
            o.need(a['ledger_current']['path']==str(Path(c['root'])/'state.json'),'readonly-schema-canonical-ledger');value=read(a['ledger_current']);source=read(a['source']);batch=value['batches'][a['batch']];o.need(source.get('company')==c['company'] and str(source.get('groupid'))==c['groupid'] and source.get('start')==batch.get('start')==c['start'] and source.get('end_exclusive')==batch.get('end_exclusive')==c['end_exclusive'] and batch['source']['sha256']==a['source']['sha256'] and read(batch['source'])==source,'readonly-schema-preserved-source-batch');evidence.append(batch['source'])
    if live:
        _readonly_wait_receipt_absent(folder,len(engine['calls']))
        if schema:
            for i,row in enumerate(ledger_facts(order,live=False)):
                r=engine['companies'][i]['artifacts']['ledger_current'] if i<index else row['canonical'];o.need(r['path']==row['canonical']['path'],'readonly-schema-canonical-ledger');value=json.loads(o.raw(r));o.need(value.get('company')==row['company'] and str(value.get('groupid'))==row['groupid'] and value.get('mode')=='development' and value.get('browser_backend')=='local-dom-bridge','readonly-schema-ledger-binding')
        else:ledger_facts(order,live=True)
        o.need(o.ref(folder/'engine.json')==engine_ref,'readonly-successor-live-engine-unchanged')
    result={'order':order,'company_index':index,'failed_engine_index':len(engine['calls'])-1,'failed_engine_call':failed,'engine_prefix':engine['calls'][:-1],'failed_child_index':len(parent['calls'])-1,'failed_parent_child':parent['calls'][-1],'absent_receipt_path':absent,'worker_task_id':task,'original_outer':outer,'provider_facts':held['scope'],'evidence':list({(r['path'],r['sha256']):r for r in evidence}.values())}
    if schema:result['preserved_companies']=copy.deepcopy(engine['companies'][:index])
    return result

def _wait8_node(reference,seen=()):
    o.need(reference['sha256']not in seen and len(seen)<16,'readonly-successor-finite-unique-proof-chain');seen=(*seen,reference['sha256']);p=o.doc(reference);parent,engine=_wait8_original_states(p,reference);read=lambda r:_readonly_wait_doc(r,p['materials'])
    if 'previous_recovery'not in p:
        o.need(p.get('provider')is None,'readonly-successor-initial-provider-conflict');facts=readonly_wait_original(parent,p['worker'],p['engine_archive'],live=False,materials=p['materials'],original_engine_ref=p['original_engine']);codes=_wait8_data_graph(parent,p['release'],p['old_sources']);op=_readonly_wait_operator();original_operator=read(facts['operator_state']);operator_job=read(facts['operator_job']);operator_proof=o.doc(p['operator_recovery']);operator_folder=Path(operator_job['workflow_path']).parent
        o.need(p['operator_recovery']['path']==str(operator_folder/'company-search-loading-recovery'/facts['operator_state']['sha256']/'block-recovery-proof.json') and operator_proof['original_journal']['sha256']==facts['operator_state']['sha256'] and operator_proof['original_job']['sha256']==facts['operator_job']['sha256'] and operator_proof['canonical_tree']==facts['operator_tree'] and operator_proof['original_job_path']==facts['operator_job']['path'],'readonly-successor-initial-operator-proof-binding')
        expected_operator=copy.deepcopy(original_operator);expected_operator.pop('last_error');expected_operator['company_search_loading_recovery']={'kind':op.BLOCK_KIND,'proof':p['operator_recovery']};op.verify_block_recovered(expected_operator,p['operator_recovery']);failed_children=[{'index':facts['failed_child_index'],'call':facts['failed_parent_child']}]
    else:
        o.need(p.get('provider')in (WAIT8_PROVIDER,WAIT8_SCHEMA_PROVIDER) and p.get('resume_proof')is not None,'readonly-successor-typed-provider-required');previous=_wait8_node(p['previous_recovery'],seen);release=o.doc(p['release']);authority=release.get('confirmed_navigation_wait_successor',{})
        o.need(authority.get('kind')==_wait8_provider_kind(p['provider']) and authority.get('previous_recovery')==p['previous_recovery'] and authority.get('previous_release')==release.get('previous_release')==previous['proof']['release'] and parent.get(FIELD8)==p['previous_recovery'],'readonly-successor-reviewed-linear-authority')
        facts=_wait8_successor_original(parent,p['worker'],p['engine_archive'],authority,previous,live=False,materials=p['materials'],original_engine_ref=p['original_engine']);codes=_wait8_data_graph(parent,p['release'],p['old_sources'],previous['codes']);provider=_wait8_switch_facts(authority,p['resume_proof']);expected_operator=provider['expected_operator'];operator_job=provider['job'];failed_children=[*previous['failed_children'],{'index':facts['failed_child_index'],'call':facts['failed_parent_child']}]
        o.need(all(x['index']!=facts['failed_child_index']for x in previous['failed_children']),'readonly-successor-failed-child-index-unique')
    o.need(p['facts']==facts and p['code_refs']==codes,'readonly-successor-recomputed-facts-and-graph');active_parent,active_engine=_wait8_repaired(parent,engine,reference)
    evidence=[*(previous['evidence'] if 'previous_recovery'in p else []),reference,p['parent_archive'],p['engine_archive'],p['release'],*p['old_sources'],*[x['archive']for x in p['materials']],p['resume_proof'] if 'previous_recovery'in p else p['operator_recovery']]
    evidence=list({(r['path'],r['sha256']):r for r in evidence}.values())
    return {'proof':p,'facts':facts,'codes':codes,'failed_children':failed_children,'active_parent':active_parent,'active_engine':active_engine,'expected_operator':expected_operator,'operator_job':operator_job,'original_parent':parent,'original_engine':engine,'evidence':evidence}

def _wait8_physical(codes):
    for r in codes:o.raw(r)
    helper=next(r for r in codes if r['path']==str(PROJECT/'skills/violation-notifier/scripts/violation_initial_ledger_recovery.py'));o.need(o.ref(Path(__file__))==helper,'readonly-successor-current-helper-code')

def plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True,resume_proof=None):
    parent=o.doc(parent_ref)
    if not parent.get(FIELD8):
        o.need(resume_proof is None,'readonly-successor-no-resume-on-initial');return _WAIT8_INITIAL_PLAN(parent_ref,worker_ref,release_ref,old_refs,installed=installed)
    o.need(resume_proof is not None,'readonly-successor-readonly-confirmation-required-before-metadata');folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json','readonly-successor-canonical-parent');previous=_wait8_node(parent[FIELD8]);release=o.doc(release_ref);authority=release.get('confirmed_navigation_wait_successor',{})
    o.need(authority.get('kind')in (WAIT8_SUCCESSOR_KIND,WAIT8_SCHEMA_KIND) and authority.get('previous_recovery')==parent[FIELD8] and authority.get('previous_release')==release.get('previous_release')==previous['proof']['release'],'readonly-successor-reviewed-prior-authority');engine_ref=o.ref(folder/'engine.json');facts=_wait8_successor_original(parent,worker_ref,engine_ref,authority,previous,live=True);provider=_wait8_switch_facts(authority,resume_proof);o.need(o.doc(o.ref(Path(provider['job']['workflow_path'])))==provider['expected_operator'],'readonly-successor-operator-must-equal-readonly-result');codes=_wait8_data_graph(parent,release_ref,old_refs,previous['codes'])
    if installed:_wait8_physical(codes)
    live_lease(facts['order']);return {'kind':KIND8,'provider':WAIT8_SCHEMA_PROVIDER if authority['kind']==WAIT8_SCHEMA_KIND else WAIT8_PROVIDER,'at':stamp(),'previous_recovery':parent[FIELD8],'resume_proof':resume_proof,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_readonly_wait(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref)
    if 'previous_recovery'not in p:return _WAIT8_INITIAL_VERIFY(current,proof_ref,installed=installed)
    o.need(current.get(FIELD8)==proof_ref,'readonly-successor-current-proof-marker');node=_wait8_node(proof_ref);parent=node['original_parent'];active=node['active_parent'];engine=o.doc(o.ref(o.location(current['order'])/'engine.json'));expected_engine=node['active_engine']
    if installed:_wait8_physical(node['codes'])
    o.need(current['calls'][:len(parent['calls'])]==parent['calls'] and current.get('resolved_errors',[])[:len(active['resolved_errors'])]==active['resolved_errors'] and all(current.get(k)==parent.get(k)for k in ('order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','origin_ref')) and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'readonly-successor-current-parent-prefix')
    o.need(engine['order']==expected_engine['order'] and engine['scope_sha256']==expected_engine['scope_sha256'] and engine['calls'][:len(expected_engine['calls'])]==expected_engine['calls'] and engine.get('resolved_readonly_failures',[])[:len(expected_engine['resolved_readonly_failures'])]==expected_engine['resolved_readonly_failures'],'readonly-successor-current-engine-prefix')
    job=node['operator_job'];o.raw(o.doc(p['release'])['confirmed_navigation_wait_successor']['operator_job']);state=o.doc(o.ref(Path(job['workflow_path'])));expected_operator=node['expected_operator'];o.need(state['calls'][:len(expected_operator['calls'])]==expected_operator['calls'] and all(c.get('state')=='confirmed'for c in state['calls']) and state.get('switch_read_recovery')==p['resume_proof'] and all(state.get(k)==expected_operator.get(k)for k in ('fingerprint','work_order_id','company','groupid','date_range','tab_id','initial_groupid')),'readonly-successor-current-operator-prefix')
    return {'kind':KIND8,'proof':proof_ref,'code_refs':node['codes'],'initial_failed_calls':[],'additional_failed_calls':node['failed_children'],'evidence':node['evidence']}

def recover_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,resume_proof=None):
    parent=o.doc(parent_ref) if not (Path(parent_ref['path']).parent/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256']/'proof.json').exists() else o.doc(o.doc(o.ref(Path(parent_ref['path']).parent/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256']/'proof.json'))['parent_archive'])
    if not parent.get(FIELD8):o.need(resume_proof is None,'readonly-successor-initial-no-resume');return _WAIT8_INITIAL_RECOVER(parent_ref,worker_ref,release_ref,old_refs)
    o.need(resume_proof is not None,'readonly-successor-readonly-result-required');folder=Path(parent_ref['path']).parent;base=folder/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256'];proof_path=base/'proof.json'
    with (folder/'launcher.lock').open('a')as la,(folder/'engine.lock').open('a')as en:
        for f in (la,en):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if proof_path.exists():p=o.doc(o.ref(proof_path))
        else:
            plan_path=base/'successor-plan.json'
            if plan_path.exists():p=o.doc(o.ref(plan_path))
            else:
                p=plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,resume_proof=resume_proof);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['materials']=[{'original':r,'archive':immutable_bytes(base/'materials'/(r['sha256']+Path(r['path']).suffix),o.raw(r))}for r in p['facts']['evidence']];p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r))for r in old_refs];o.immutable(plan_path,p)
            o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and p['resume_proof']==resume_proof and [(Path(r['path']).name,r['sha256'])for r in p['old_sources']]==[(Path(r['path']).name,r['sha256'])for r in old_refs],'readonly-successor-same-planned-inputs');o.immutable(proof_path,p)
        o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and p['resume_proof']==resume_proof and [(Path(r['path']).name,r['sha256'])for r in p['old_sources']]==[(Path(r['path']).name,r['sha256'])for r in old_refs],'readonly-successor-same-proof-inputs');proof_ref=o.ref(proof_path);node=_wait8_node(proof_ref);original=node['original_parent'];engine=node['original_engine'];expected=node['active_parent'];active=node['active_engine'];cur=o.doc(o.ref(folder/'launcher.json'));eng=o.doc(o.ref(folder/'engine.json'));o.need(cur in (original,expected) and eng in (engine,active),'readonly-successor-metadata-CAS');_readonly_wait_receipt_absent(folder,len(engine['calls']));_wait8_physical(node['codes']);live_lease(node['facts']['order']);o.need(o.doc(o.ref(Path(node['operator_job']['workflow_path'])))==node['expected_operator'],'readonly-successor-initial-operator-CAS')
        from role_execution_launcher import save
        if eng==engine:save(folder/'engine.json',active)
        if cur==original:save(folder/'launcher.json',expected)
        verify_readonly_wait(o.doc(o.ref(folder/'launcher.json')),proof_ref)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof_ref,'ui_used':False,'input_replayed':False,'resume_phase':'company','readonly_reconcile_repeated':False}

def repaired_readonly_wait(parent,engine,proof):
    return _wait8_repaired(parent,engine,proof)




WAIT8_SCHEMA_KIND='reviewed-confirmed-governance-source-schema-readonly-successor-v1'


WAIT8_SCHEMA_PROVIDER='confirmed-governance-source-schema-switch-readonly-v1'


WAIT8_SCHEMA_ERROR='read-recovery-governance-source-risk'


WAIT8_SCHEMA_PATHS={str(PROJECT/'skills'/p)for p in ('douyin-laike-operator/scripts/switch_read_recovery.py','violation-notifier/scripts/violation_initial_ledger_recovery.py')}


def _wait8_provider_kind(provider):
    o.need(provider in (WAIT8_PROVIDER,WAIT8_SCHEMA_PROVIDER),'readonly-successor-provider-unknown')
    return WAIT8_SCHEMA_KIND if provider==WAIT8_SCHEMA_PROVIDER else WAIT8_SUCCESSOR_KIND




WAIT8_SOURCE_SUPERSESSION_KIND='reviewed-unconsumed-readonly-source-publication-supersession-v1'


WAIT8_UNCONSUMED_SCHEMA_RELEASE={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/governance-source-schema-readonly-recovery-candidate/supervisor-release.json', 'sha256': '8f38f87b71d89d2e016daacfae6413d557753aa243c21ef401d3b6ca98e48d60'}


def _wait8_data_graph_step(parent,release_ref,old_sources,previous_codes=None):
    """Historical graph construction only; caller verifies final physical tip."""
    release=o.doc(release_ref);targets=release.get('targets',[]);old={Path(r['path']).name.removesuffix('.before'):r for r in old_sources};codes=copy.deepcopy(previous_codes if previous_codes is not None else parent['code_refs']);by={r['path']:r for r in codes};successor=previous_codes is not None;schema=release.get('confirmed_navigation_wait_successor',{}).get('kind')==WAIT8_SCHEMA_KIND;wanted=(WAIT8_SCHEMA_PATHS if schema else WAIT8_SUCCESSOR_PATHS) if successor else set(WAIT_NAMES.values())
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and len(targets)==len(wanted) and {t['target']for t in targets}==wanted and len(old_sources)==len(wanted) and set(old)=={Path(p).name for p in wanted} and not release.get('data_targets'),'readonly-successor-exact-reviewed-source-set')
    for t in targets:
        path=t['target'];before=by[path];archive=old[Path(path).name];o.need(t.get('mode')=='0644' and t['old_sha256']==before['sha256']==archive['sha256'],'readonly-successor-contiguous-source-CAS');o.raw(archive);o.raw(t['after']);codes[codes.index(before)]={'path':path,'sha256':t['after']['sha256']}
        if not successor and Path(path).name in ('company_search_wait.py','company_search_recovery.py'):o.need(t['after']['sha256']=={'company_search_wait.py':'81c2822a957ba5a961c39f1e96bb4eb9c71a8819e256502fbef0b794ff45b089','company_search_recovery.py':'f48372c746dd699aaa6c4fecb7e14ac563d07b088a3dd66caae402af2fa7ab6c'}[Path(path).name],'readonly-successor-initial-operator-pins')
    return codes


def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('verb',choices=('plan','recover','verify','plan-entry','recover-entry','plan-company','recover-company','plan-center','recover-center','plan-records-entry','recover-records-entry','plan-analysis-wait','recover-analysis-wait','plan-date-fragment','recover-date-fragment','plan-readonly-wait'));a.add_argument('--parent',required=True);a.add_argument('--worker');a.add_argument('--release');a.add_argument('--old-source',action='append',default=[]);a.add_argument('--proof');args=a.parse_args();parent=json.loads(args.parent)
    if args.verb=='verify':out=verify_recovered(o.doc(parent),json.loads(args.proof))
    else:
        fn={'plan':plan,'recover':recover,'plan-entry':plan_v2,'recover-entry':recover_v2,'plan-company':plan_company,'recover-company':recover_company,'plan-center':plan_center,'recover-center':recover_center,'plan-records-entry':plan_records_entry,'recover-records-entry':recover_records_entry,'plan-analysis-wait':plan_analysis_wait,'recover-analysis-wait':recover_analysis_wait,'plan-date-fragment':plan_date_fragment,'recover-date-fragment':recover_date_fragment,'plan-readonly-wait':plan_readonly_wait}[args.verb];out=fn(parent,json.loads(args.worker),json.loads(args.release),[json.loads(x) for x in args.old_source])
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)

# Initial FIELD8 provider for an already-confirmed center navigation's readonly
# route observation. No fixed historical release/company/task IDs or UI replay.
WAIT8_CENTER_PROVIDER='confirmed-center-navigation-readonly-initial-v1'
WAIT8_CENTER_ERROR='navigation-tree-path-conflict'
WAIT8_CENTER_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('bridge-navigation.py','violation_initial_ledger_recovery.py')}

def _center8_navigation():
    import importlib.util
    path=PROJECT/'skills/violation-notifier/scripts/bridge-navigation.py'
    spec=importlib.util.spec_from_file_location('_wait8_center_navigation',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def _center8_sources(parent,release_ref,old_refs,*,installed):
    release=_violation_completed_doc(release_ref);ts=release.get('targets',[]);saved={Path(r['path']).name.removesuffix('.before'):r for r in old_refs};codes=copy.deepcopy(parent['code_refs']);by={r['path']:r for r in codes}
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and not release.get('data_targets')and len(ts)==len(old_refs)==len(saved)==2 and {t['target']for t in ts}==WAIT8_CENTER_PATHS,'center8-exact-two-source-release')
    o.need(len(codes)==len(by)==150,'center8-original150-source-vector')
    for t in ts:
        old=saved.get(Path(t['target']).name);before=by[t['target']]
        o.need(old is not None and t.get('mode')==(420 if _center8_missing()else '0644')and t['before']['sha256']==old['sha256']and t['old_sha256']==before['sha256']==old['sha256']and t['before']['path']==str(Path(release_ref['path']).parent/(Path(t['target']).name+'.before'))and t['after']['sha256']!=t['old_sha256'],'center8-exact-before-after-slot')
        _violation_completed_raw(old);_violation_completed_raw(t['before']);_violation_completed_raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    o.need(sum(a!=b for a,b in zip(codes,parent['code_refs']))==2,'center8-only-two-changed-slots')
    if installed:_wait8_physical(codes)
    else:
        for r in codes:
            if r['path']not in WAIT8_CENTER_PATHS:_violation_completed_raw(r)
    return codes


def _center8_ledgers(order,read,*,live):
    import execution_timing as timing
    policy=order.get('active_company_policy');names=timing.company_names(policy);allowed={c['company']:c['groupid']for c in timing.company_policy(policy)['active']}if policy else GROUPS
    o.need(len(order['companies'])==len(names)and {c['company']for c in order['companies']}==set(names),'center8-exact-order-policy-ledgers');refs=[]
    if policy:read(policy);refs.append(policy)
    for c in order['companies']:
        root=PROJECT/'runtime'/o.FLOW/c['company'];o.need(c['company']in allowed and c['groupid']==allowed[c['company']]and c['root']==str(root),'center8-fixed-company-ledger-root')
        state=read(c['ledger']);o.need(state.get('company')==c['company']and str(state.get('groupid'))==c['groupid']and state.get('mode')=='development'and state.get('browser_backend')=='local-dom-bridge'and state.get('next_start')==c['start'],'center8-original-policy-ledger-content')
        if live:o.need(_violation_completed_raw({'path':str(root/'state.json'),'sha256':c['ledger']['sha256']})==_violation_completed_raw(c['ledger']),'center8-live-ledger-unchanged')
        refs.append(c['ledger'])
    return refs


def _center8_original(parent,worker_ref,engine_ref,nav_ref,*,live,materials=(),original_engine_ref=None):
    expected_error='source-company-mismatch'if _center8_missing()else WAIT8_CENTER_ERROR;read=lambda r:_readonly_wait_doc(r,materials);order=_violation_completed_order(parent['order']);folder=o.location(parent['order']);engine=read(engine_ref);need=o.need
    need(parent.get('kind')=='role-execution-launcher-v1'and parent.get('status')=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and not parent.get('completion')and not parent.get(FIELD8),'center8-original-natural-parent')
    origin=read(parent['origin_ref']);need(all(parent.get(k)==v for k,v in origin.items()),'center8-original-clock-source-identity')
    i=engine.get('index');need(type(i)is int and 0<=i<len(order['companies'])and len(engine['companies'])==len(order['companies'])and engine.get('order')==parent['order']and engine.get('kind')=='violation-execution-v1'and engine.get('scope_sha256')==order['scope_sha256']and engine.get('status')=='hold'and engine.get('phase')=='center'and engine.get('error')==expected_error and not any(engine.get(k)for k in ('completion','delivery','handoff','acceptance')),'center8-original-center-engine')
    original_engine_ref=original_engine_ref or engine_ref;need(original_engine_ref['path']==str(folder/'engine.json')and original_engine_ref['sha256']==engine_ref['sha256'],'center8-original-engine-reference')
    need(i==0 and len(order['companies'])==1 and order.get('active_company_policy')is not None,'center8-initial-single-active-company-only')
    company=order['companies'][i];active=engine['companies'][i];a=active['artifacts'];calls=engine['calls'];need(calls and active['phase']=='center'and set(a)=={'plan','job','identity_receipt','company_navigation'},'center8-no-query-or-capture-artifacts')
    failed=calls[-1];prefix=calls[:-1];need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['state']=='failed'and failed['step']=='center'and failed['company_index']==i and failed['error']==expected_error and failed['context']=={'order':order,'company':company,'artifacts':a,'folder':str(folder/'companies'/str(i)),'phase':'center'},'center8-exact-resultless-readonly-tail')
    evidence=[parent['order'],parent['origin_ref'],original_engine_ref]
    for n,c in enumerate(prefix):
        need(c.get('state')=='returned'and c.get('applied')is True and c.get('company_index')==i and c['result']['path']==str(folder/'receipts'/(str(n+1).zfill(5)+'.json')),'center8-preserved-returned-prefix');read(c['result']);evidence.append(c['result'])
    if live:_readonly_wait_receipt_absent(folder,len(calls))
    job=read(a['job']);nav=_center8_navigation();nav.scope(job);before_state=read(nav_ref)
    need(a['job']['path']==str(folder/'companies'/str(i)/'navigation-job.json')and nav_ref['path']==str(folder/'companies'/str(i)/'center-navigation.json')and job['company']==company['company']and str(job['groupid'])==company['groupid']and job['start']==company['start']and job['end_exclusive']==company['end_exclusive'],'center8-same-company-range-job')
    need(before_state.get('fingerprint')==nav.tag(job)and before_state.get('company')==job['company']and before_state.get('groupid')==str(job['groupid'])and all(before_state.get(k)==job[k]for k in ('start','end_exclusive'))and before_state.get('tab_id')==parent['tab_id']and before_state.get('phase')=='observeCenter'and before_state.get('profile_accepted')is False and before_state.get('business_progress_changed')is False and before_state.get('platform_writes')is False and before_state.get('production_enabled')is False and not before_state.get('last_error')and not before_state.get('error')and (_center8_missing()or not before_state.get('readonly_route_recovery'))and not before_state.get('readonly_route_exhausted')and len(before_state.get('calls',[]))==1,'center8-unconsumed-confirmed-observation')
    from types import SimpleNamespace
    owner=SimpleNamespace(job=job,s=before_state,tab=parent['tab_id'],file=Path(nav_ref['path']));binding=nav.transition_binding(owner,'center');click=before_state['calls'][0]
    need(click['state']=='confirmed'and click['key'].endswith(':openCenter')and binding['target_path']==nav.CENTER,'center8-sole-original-confirmed-open')
    if not _center8_missing():need(before_state['last_tree']==binding['before']==click['before']and before_state['observations'][-1]==click['before'],'center8-sole-original-confirmed-open')
    if before_state.get('observation_transport') is not None:
        values,transport_refs=nav.observation_members(before_state,folder/'companies'/str(i)/'navigation-raw-observations',read);evidence.extend(transport_refs)
    else:
        raw=before_state['raw_observations'][-4:];commands=[{'op':'tabs'},{'op':'ping','tabId':parent['tab_id']},{'op':'tree','tabId':parent['tab_id']},{'op':'tabs'}];need(len(raw)==4 and len({str(Path(r['path']).parent)for r in raw})==1,'center8-original-four-read-sequence');values=[]
        for n,(r,command)in enumerate(zip(raw,commands)):
            path=Path(r['path']);need(set(r)=={'path','sha256','command'}and r['command']==command and path.parent.parent==folder/'companies'/str(i)/'navigation-raw-observations'and path.name==str(n)+'-'+command['op']+'.json','center8-canonical-readonly-command');reference={'path':r['path'],'sha256':r['sha256']};reply=read(reference);need(reply.get('ok')is True and reply.get('error')is None and 'result'in reply,'center8-raw-read-transport');values.append(reply['result']);evidence.append(reference)
    ping,tree=values[1:3];pending_facts=None
    if _center8_missing():pending_facts=_missing8_observations(owner,binding,values,read,evidence)
    else:
        before=nav.context(values[0],parent['tab_id'],job['groupid']);after=nav.context(values[3],parent['tab_id'],job['groupid']);nav.transition_sample_scope(owner,binding,{'before':before,'after':after,'tree':tree})
    need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only'and ping.get('url')in ['https://life.douyin.com'+path for path in nav.transition_paths(owner,binding)],'center8-reviewed-ping-tree-binding')
    company_state=read(a['company_navigation']);need(a['company_navigation']['path']==str(folder/'companies'/str(i)/'company-navigation/workflow.json')and company_state.get('state')=='complete'and company_state.get('phase')=='done'and all(c.get('state')=='confirmed'for c in company_state.get('calls',[]))and company_state['result']['identity']==job['identity'],'center8-preserved-confirmed-company-navigation')
    for r in (a['plan'],a['job'],a['identity_receipt'],a['company_navigation'],binding['before'],nav_ref):read(r);evidence.append(r)
    worker_evidence,task,outer=_wait8_children_worker(parent,worker_ref,[],read,expected_error);evidence.extend(worker_evidence)
    evidence.extend(_center8_ledgers(order,read,live=live))
    if live:need(o.ref(folder/'engine.json')==engine_ref and o.ref(Path(nav_ref['path']))==nav_ref,'center8-current-inputs-unchanged')
    return {**({'missing_gid_transition':pending_facts}if pending_facts is not None else {}),'order':order,'company_index':i,'failed_engine_index':len(calls)-1,'failed_engine_call':failed,'engine_prefix':prefix,'failed_child_index':len(parent['calls'])-1,'failed_parent_child':parent['calls'][-1],'absent_receipt_path':str(folder/'receipts'/(str(len(calls)).zfill(5)+'.json')),'worker_task_id':task,'original_outer':outer,'operator_state':nav_ref,'operator_job':a['job'],'binding':binding,'confirmed_call':click,'evidence':list({(r['path'],r['sha256']):r for r in evidence}.values())}


def _center8_authority(parent_ref,engine_ref,worker_ref,nav_ref,job_ref,release_ref):
    expected={'kind':_center8_provider(),'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'nav':nav_ref,'job':job_ref}
    o.need(_violation_completed_doc(release_ref).get('confirmed_navigation_wait_initial')==expected,'center8-reviewed-initial-authority')


def _center8_node(reference):
    p=_violation_completed_doc(reference);o.need(p.get('provider')==_center8_provider() and 'previous_recovery'not in p and 'resume_proof'not in p,'center8-typed-initial-node');parent,engine=_wait8_original_states(p,reference)
    facts=_center8_original(parent,p['worker'],p['engine_archive'],p['original_nav'],live=False,materials=p['materials'],original_engine_ref=p['original_engine']);o.need(facts==p['facts'],'center8-recomputed-original-facts')
    _center8_authority(p['original_parent'],p['original_engine'],p['worker'],p['original_nav'],facts['operator_job'],p['release']);codes=_center8_sources(parent,p['release'],p['old_sources'],installed=False);o.need(codes==p['code_refs'],'center8-recomputed-effective-graph')
    pp,ee=_wait8_repaired(parent,engine,reference)
    return {'proof':p,'facts':facts,'codes':codes,'original_parent':parent,'original_engine':engine,'active_parent':pp,'active_engine':ee,'evidence':[reference,p['parent_archive'],p['engine_archive'],p['release'],*p['old_sources'],*[x['archive']for x in p['materials']]]}


_CENTER8_PREVIOUS_PLAN=plan_readonly_wait
_CENTER8_PREVIOUS_VERIFY=verify_readonly_wait
_CENTER8_PREVIOUS_RECOVER=recover_readonly_wait

def plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True,resume_proof=None):
    release=o.doc(release_ref)
    if release.get('confirmed_navigation_wait_initial',{}).get('kind')!=_center8_provider():return _CENTER8_PREVIOUS_PLAN(parent_ref,worker_ref,release_ref,old_refs,installed=installed,resume_proof=resume_proof)
    o.need(resume_proof is None,'center8-no-ui-resume-proof');parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json'),'center8-canonical-parent');engine_ref=o.ref(folder/'engine.json');engine=o.doc(engine_ref);nav_ref=o.ref(folder/'companies'/str(engine['index'])/'center-navigation.json');facts=_center8_original(parent,worker_ref,engine_ref,nav_ref,live=True);_center8_authority(parent_ref,engine_ref,worker_ref,nav_ref,facts['operator_job'],release_ref);codes=_center8_sources(parent,release_ref,old_refs,installed=installed);live_lease(facts['order'])
    return {'kind':KIND8,'provider':_center8_provider(),'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'original_nav':nav_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_readonly_wait(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref)
    if p.get('provider')!=_center8_provider():return _CENTER8_PREVIOUS_VERIFY(current,proof_ref,installed=installed)
    o.need(current.get(FIELD8)==proof_ref,'center8-current-marker');node=_center8_node(proof_ref);parent=node['original_parent'];pp=node['active_parent'];ee=node['active_engine'];folder=o.location(current['order']);engine=o.doc(o.ref(folder/'engine.json'))
    if installed:_wait8_physical(node['codes'])
    o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(pp['resolved_errors'])]==pp['resolved_errors']and all(current.get(k)==parent.get(k)for k in ('order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','origin_ref'))and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'center8-preserved-parent-history')
    o.need(engine['order']==ee['order']and engine['scope_sha256']==ee['scope_sha256']and engine['calls'][:len(ee['calls'])]==ee['calls']and engine.get('resolved_readonly_failures',[])[:len(ee['resolved_readonly_failures'])]==ee['resolved_readonly_failures'],'center8-preserved-prefix-and-failed-tombstone')
    nav=o.doc(o.ref(p['original_nav']['path']));before=_readonly_wait_doc(p['original_nav'],p['materials']);o.need(nav['calls'][:len(before['calls'])]==before['calls']and all(c['state']=='confirmed'for c in nav['calls'])and all(nav.get(k)==before.get(k)for k in ('fingerprint','tab_id','company','groupid','start','end_exclusive'))and nav['raw_observations'][:len(before['raw_observations'])]==before['raw_observations'],'center8-original-confirmed-input-and-raw-prefix-preserved')
    return {'kind':KIND8,'proof':proof_ref,'code_refs':node['codes'],'initial_failed_calls':[],'additional_failed_calls':[{'index':node['facts']['failed_child_index'],'call':node['facts']['failed_parent_child']}],'evidence':node['evidence']}

def recover_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,resume_proof=None,checkpoint=_recovery_checkpoint):
    release=o.doc(release_ref)
    if release.get('confirmed_navigation_wait_initial',{}).get('kind')!=_center8_provider():return _CENTER8_PREVIOUS_RECOVER(parent_ref,worker_ref,release_ref,old_refs,resume_proof=resume_proof)
    o.need(resume_proof is None,'center8-no-ui-recovery');folder=Path(parent_ref['path']).parent;base=folder/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256'];proof_path=base/'proof.json';intent_path=base/'intent.json';result_path=base/'result.json';authority={'kind':_center8_provider(),'parent':parent_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs}
    with (folder/'launcher.lock').open('a')as la,(folder/'engine.lock').open('a')as en:
        for f in (la,en):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if proof_path.exists():p=o.doc(o.ref(proof_path));o.need(o.doc(o.ref(intent_path))==authority,'center8-existing-intent-authority')
        else:
            o.need(not result_path.exists()and not result_path.is_symlink(),'center8-terminal-without-proof')
            p=plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['materials']=[{'original':r,'archive':immutable_bytes(base/'materials'/(r['sha256']+Path(r['path']).suffix),o.raw(r))}for r in p['facts']['evidence']];p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r))for r in old_refs];checkpoint('archives');o.immutable(intent_path,authority);checkpoint('intent');o.immutable(proof_path,p);checkpoint('proof')
        o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and [(Path(r['path']).name,r['sha256'])for r in p['old_sources']]==[(Path(r['path']).name,r['sha256'])for r in old_refs],'center8-same-proof-inputs');proof=o.ref(proof_path);node=_center8_node(proof);bp=node['original_parent'];be=node['original_engine'];pp=node['active_parent'];ee=node['active_engine'];cur=o.doc(o.ref(folder/'launcher.json'));eng=o.doc(o.ref(folder/'engine.json'))
        o.need((cur==bp and eng in (be,ee))or(cur==pp and eng==ee),'center8-engine-then-parent-CAS');_readonly_wait_receipt_absent(folder,len(be['calls']))
        expected_result={'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'nav_unchanged':p['original_nav'],'ui_used':False,'input_replayed':False,'resume_phase':'center'}
        if result_path.exists()or result_path.is_symlink():
            o.need(not result_path.is_symlink()and cur==pp and eng==ee and o.doc(o.ref(result_path))==expected_result,'center8-terminal-conflict-before-CAS');return o.doc(o.ref(result_path))
        _wait8_physical(node['codes']);live_lease(node['facts']['order']);o.need(o.ref(p['original_nav']['path'])==p['original_nav'],'center8-original-navigation-CAS')
        from role_execution_launcher import save
        if eng==be:save(folder/'engine.json',ee)
        checkpoint('engine')
        if cur==bp:save(folder/'launcher.json',pp)
        checkpoint('parent');verify_readonly_wait(o.doc(o.ref(folder/'launcher.json')),proof);expected_result.update(launcher=o.ref(folder/'launcher.json'),engine=o.ref(folder/'engine.json'));o.immutable(result_path,expected_result);checkpoint('result');return expected_result

# A source-preparation tail is not navigation recovery. FIELD8 is the existing
# typed admission route; the failed call remains an immutable full tombstone.
SOURCE8_PROVIDER='confirmed-query-settled-center-zero-source-preinput-v1'
SOURCE8_ERROR='center-zero-summary-range-or-literal-mismatch'
SOURCE8_NAMES=('governance_zero_capture.py','violation_execution_ports.py','violation_initial_ledger_recovery.py')

def _source8_zero():
    import governance_zero_capture
    o.need(Path(governance_zero_capture.__file__).resolve()==PROJECT/'skills/violation-notifier/scripts/governance_zero_capture.py','source8-fixed-zero-module')
    return governance_zero_capture

def _source8_original(parent,worker_ref,engine_ref,*,live,materials=(),original_engine_ref=None):
    evidence=[]
    def read(r):
        value=_readonly_wait_doc(r,materials);evidence.append(r);return value
    order=_violation_completed_order(parent['order']);folder=o.location(parent['order']);engine=_readonly_wait_doc(engine_ref,materials);origin=read(parent['origin_ref'])
    o.need(parent.get('kind')=='role-execution-launcher-v1'and parent.get('status')=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and not parent.get('completion')and not parent.get(FIELD8)and all(parent.get(k)==v for k,v in origin.items()),'source8-original-parent-origin')
    o.need(engine.get('kind')=='violation-execution-v1'and engine.get('order')==parent['order']and engine.get('scope_sha256')==order['scope_sha256']and engine.get('status')=='hold'and engine.get('phase')=='source'and engine.get('error')==SOURCE8_ERROR and not any(engine.get(k)for k in ('completion','delivery','handoff','acceptance')),'source8-original-source-hold')
    original_engine_ref=original_engine_ref or engine_ref;o.need(original_engine_ref=={'path':str(folder/'engine.json'),'sha256':engine_ref['sha256']},'source8-original-engine-reference');evidence.append(original_engine_ref)
    i=engine['index'];o.need(type(i)is int and i==0 and len(order['companies'])==len(engine['companies'])==1 and order.get('active_company_policy')is not None,'source8-initial-active-company')
    company=order['companies'][i];active=engine['companies'][i];a=active['artifacts'];calls=engine['calls'];failed=calls[-1]
    o.need(active['phase']=='source'and set(a)=={'plan','job','identity_receipt','company_navigation','center_navigation','center_query_final','center_pages','center_zero','query_final'}and a['center_zero']is True,'source8-no-output-artifacts')
    o.need(set(failed)=={'step','company_index','context','state','intent_at','error'}and failed['step']=='source'and failed['company_index']==i and failed['state']=='failed'and failed['error']==SOURCE8_ERROR and failed['context']=={'order':order,'company':company,'artifacts':a,'folder':str(folder/'companies'/str(i)),'phase':'source'},'source8-exact-resultless-source-tail')
    for n,c in enumerate(calls[:-1]):
        o.need(c.get('state')=='returned'and c.get('applied')is True and c.get('company_index')==i and c['result']['path']==str(folder/'receipts'/(str(n+1).zfill(5)+'.json')),'source8-all-returned-prefix');read(c['result'])
    sub=folder/'companies'/str(i);pages_ref=o.ref(sub/'center-pages.json') if live else next(r for r in (x['original']for x in materials)if r['path']==str(sub/'center-pages.json'))
    refs={'job':a['job'],'center_query':a['center_query_final'],'records_query':a['query_final'],'center_pages':pages_ref,'center_observation':a['center_pages'][0]}
    o.need(all(refs[k]['path']==str(sub/name)for k,name in [('job','navigation-job.json'),('center_query','center-query.json'),('records_query','records-query.json'),('center_pages','center-pages.json'),('center_observation','center-pages-evidence/0000.json')]),'source8-canonical-query-inputs')
    for r in refs.values():read(r)
    zero=_source8_zero();v=zero.sources(refs);job=v['job']
    o.need(all(job[k]==company[k]for k in ('company','groupid','start','end_exclusive'))and job['identity']==v['records_query'].get('identity',job['identity'])and v['tab_id']==parent['tab_id']and v['center_zero']['analysis_zero_verified']is True and v['records_zero']['total']==0 and a['center_pages']==[v['center_observation']],'source8-settled-source-same-order')
    for r in v['rawrefs']:read(r)
    for r in (a['plan'],a['identity_receipt'],a['company_navigation'],a['center_navigation']):read(r)
    for r in (a['company_navigation'],a['center_navigation']):
        journal=read(r);o.need(not journal.get('last_error')and not journal.get('error')and all(c.get('state')=='confirmed'for c in journal.get('calls',[])),'source8-confirmed-navigation-prefix')
    refs2,task,outer=_wait8_children_worker(parent,worker_ref,[],read,SOURCE8_ERROR);evidence.extend(refs2);evidence.extend(_center8_ledgers(order,read,live=live));evidence.append(parent['order'])
    absent=[folder/'receipts'/(str(len(calls)).zfill(5)+'.json'),*[sub/n for n in ('zero-profile.json','capture-manifest.json','source.json')]]
    if live:
        for p in absent:o.need(not p.exists()and not p.is_symlink(),'source8-preinput-output-present')
        o.need(o.ref(folder/'engine.json')==engine_ref,'source8-live-engine-unchanged')
    return {'order':order,'company_index':i,'failed_engine_index':len(calls)-1,'failed_engine_call':failed,'engine_prefix':calls[:-1],'failed_child_index':len(parent['calls'])-1,'failed_parent_child':parent['calls'][-1],'worker_task_id':task,'original_outer':outer,'source_inputs':refs,'center_zero':v['center_zero'],'records_zero':v['records_zero'],'absent_paths':[str(p)for p in absent],'evidence':list({(r['path'],r['sha256']):r for r in evidence}.values())}


def _source8_sources(parent,release_ref,old_refs,*,installed):
    root=_violation_completed_doc(release_ref);targets=root.get('targets');paths={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in SOURCE8_NAMES};codes=copy.deepcopy(parent['code_refs']);by={r['path']:r for r in codes};saved={Path(r['path']).name:r for r in old_refs}
    o.need(root.get('kind')=='supervisor-reviewed-source-release-v1'and root.get('published')is True and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director'and len(codes)==len(by)==150 and type(targets)is list and len(targets)==len(old_refs)==len(saved)==3 and {t['target']for t in targets}==paths,'source8-exact-three-source150')
    for t in targets:
        before=by[t['target']];old=saved.get(Path(t['target']).name+'.before')
        o.need(set(t)=={'target','mode','old_sha256','before','after'}and type(t['mode'])is int and t['mode']==420 and old is not None and t['before']=={'path':str(Path(release_ref['path']).parent/(Path(t['target']).name+'.before')),'sha256':before['sha256']}and t['old_sha256']==old['sha256']==before['sha256']and t['after']['sha256']!=before['sha256'],'source8-before-after-mode-slot')
        _violation_completed_raw(old);_violation_completed_raw(t['before']);_violation_completed_raw(t['after']);codes[codes.index(before)]={'path':t['target'],'sha256':t['after']['sha256']}
    o.need(sum(x!=y for x,y in zip(codes,parent['code_refs']))==3,'source8-only-three-slots')
    for r in codes:
        if installed or r['path']not in paths:_violation_completed_raw(r)
    return codes


def _source8_authority(parent_ref,engine_ref,worker_ref,release_ref,source_inputs):
    expected={'kind':SOURCE8_PROVIDER,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'source_inputs':source_inputs}
    o.need(_violation_completed_doc(release_ref).get('confirmed_navigation_wait_initial')==expected,'source8-reviewed-source-preinput-authority')


def _source8_node(reference):
    p=_violation_completed_doc(reference);o.need(p.get('provider')==SOURCE8_PROVIDER and p.get('kind')==KIND8 and 'previous_recovery'not in p and 'resume_proof'not in p,'source8-typed-initial-proof');parent,engine=_wait8_original_states(p,reference)
    facts=_source8_original(parent,p['worker'],p['engine_archive'],live=False,materials=p['materials'],original_engine_ref=p['original_engine']);o.need(facts==p['facts'],'source8-recomputed-archived-facts');_source8_authority(p['original_parent'],p['original_engine'],p['worker'],p['release'],facts['source_inputs']);codes=_source8_sources(parent,p['release'],p['old_sources'],installed=False);o.need(codes==p['code_refs'],'source8-recomputed150');pp,ee=_wait8_repaired(parent,engine,reference)
    return {'proof':p,'facts':facts,'codes':codes,'original_parent':parent,'original_engine':engine,'active_parent':pp,'active_engine':ee,'evidence':[reference,p['parent_archive'],p['engine_archive'],p['release'],*p['old_sources'],*[x['archive']for x in p['materials']]]}


_SOURCE8_PREVIOUS_PLAN=plan_readonly_wait
_SOURCE8_PREVIOUS_VERIFY=verify_readonly_wait
_SOURCE8_PREVIOUS_RECOVER=recover_readonly_wait

def plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True,resume_proof=None):
    if o.doc(release_ref).get('confirmed_navigation_wait_initial',{}).get('kind')!=SOURCE8_PROVIDER:return _SOURCE8_PREVIOUS_PLAN(parent_ref,worker_ref,release_ref,old_refs,installed=installed,resume_proof=resume_proof)
    o.need(resume_proof is None,'source8-no-ui-proof');parent=o.doc(parent_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json'),'source8-canonical-parent');engine_ref=o.ref(folder/'engine.json');facts=_source8_original(parent,worker_ref,engine_ref,live=True);_source8_authority(parent_ref,engine_ref,worker_ref,release_ref,facts['source_inputs']);codes=_source8_sources(parent,release_ref,old_refs,installed=installed);live_lease(facts['order'])
    return {'kind':KIND8,'provider':SOURCE8_PROVIDER,'at':stamp(),'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_readonly_wait(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref)
    if p.get('provider')!=SOURCE8_PROVIDER:return _SOURCE8_PREVIOUS_VERIFY(current,proof_ref,installed=installed)
    o.need(current.get(FIELD8)==proof_ref,'source8-current-marker');node=_source8_node(proof_ref);parent=node['original_parent'];pp=node['active_parent'];ee=node['active_engine'];folder=o.location(current['order']);engine=o.doc(o.ref(folder/'engine.json'))
    if installed:_wait8_physical(node['codes'])
    o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(pp['resolved_errors'])]==pp['resolved_errors']and all(current.get(k)==parent.get(k)for k in ('order','scope_sha256','mode','origin','clock_contract','boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','origin_ref'))and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'source8-original-parent-clock-prefix')
    o.need(engine['order']==ee['order']and engine['scope_sha256']==ee['scope_sha256']and engine['calls'][:len(ee['calls'])]==ee['calls']and engine.get('resolved_readonly_failures',[])[:len(ee['resolved_readonly_failures'])]==ee['resolved_readonly_failures'],'source8-preserved-engine-prefix-tombstone')
    index=node['facts']['failed_engine_index'];receipt=folder/'receipts'/(str(index+1).zfill(5)+'.json')
    if len(engine['calls'])==index:_readonly_wait_receipt_absent(folder,index+1)
    else:
        call=engine['calls'][index];expected=node['facts']['failed_engine_call']
        o.need(call.get('state')=='returned'and call.get('step')=='source'and call.get('company_index')==expected['company_index']and call.get('context')==expected['context']and not call.get('error')and call.get('result',{}).get('path')==str(receipt),'source8-normal-source-result-owned')
        value=o.doc(call['result']);a=value.get('artifacts',{});o.need(value.get('done')is True and set(a)=={'source','total'}and a['total']==0 and a['source']['path']==str(folder/'companies'/str(expected['company_index'])/'source.json'),'source8-normal-source-receipt')
        source=_source8_zero().validate(a['source']['path']);o.need(o.ref(a['source']['path'])==a['source']and source['source_contract']['analysis_zero']==node['facts']['center_zero']and source['records']['total']==0 and {k:source['source_evidence_refs'][k]for k in node['facts']['source_inputs']}==node['facts']['source_inputs'],'source8-normal-source-derived-facts')
    for r in node['facts']['source_inputs'].values():o.raw(r)
    return {'kind':KIND8,'proof':proof_ref,'code_refs':node['codes'],'initial_failed_calls':[],'additional_failed_calls':[{'index':node['facts']['failed_child_index'],'call':node['facts']['failed_parent_child']}],'evidence':node['evidence']}

def recover_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,resume_proof=None,checkpoint=_recovery_checkpoint):
    if o.doc(release_ref).get('confirmed_navigation_wait_initial',{}).get('kind')!=SOURCE8_PROVIDER:return _SOURCE8_PREVIOUS_RECOVER(parent_ref,worker_ref,release_ref,old_refs,resume_proof=resume_proof)
    o.need(resume_proof is None,'source8-no-ui-recovery');folder=Path(parent_ref['path']).parent;base=folder/'.confirmed-navigation-readonly-wait-recovery'/parent_ref['sha256'];proof_path=base/'proof.json';intent_path=base/'intent.json';result_path=base/'result.json';authority={'kind':SOURCE8_PROVIDER,'parent':parent_ref,'worker':worker_ref,'release':release_ref,'old_sources':old_refs}
    with (folder/'launcher.lock').open('a')as la,(folder/'engine.lock').open('a')as en:
        for f in (la,en):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if proof_path.exists():p=o.doc(o.ref(proof_path));o.need(o.doc(o.ref(intent_path))==authority,'source8-existing-intent-authority')
        else:
            o.need(not result_path.exists()and not result_path.is_symlink(),'source8-terminal-without-proof');p=plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(p['original_engine']));p['materials']=[{'original':r,'archive':immutable_bytes(base/'materials'/(r['sha256']+Path(r['path']).suffix),o.raw(r))}for r in p['facts']['evidence']];p['old_sources']=[immutable_bytes(base/'sources'/Path(r['path']).name,o.raw(r))for r in old_refs];checkpoint('archives');o.immutable(intent_path,authority);checkpoint('intent');o.immutable(proof_path,p);checkpoint('proof')
        o.need(p['original_parent']==parent_ref and p['worker']==worker_ref and p['release']==release_ref and [(Path(r['path']).name,r['sha256'])for r in p['old_sources']]==[(Path(r['path']).name,r['sha256'])for r in old_refs],'source8-same-proof-inputs');proof=o.ref(proof_path);node=_source8_node(proof);bp=node['original_parent'];be=node['original_engine'];pp=node['active_parent'];ee=node['active_engine'];cur=o.doc(o.ref(folder/'launcher.json'));eng=o.doc(o.ref(folder/'engine.json'))
        o.need((cur==bp and eng in (be,ee))or(cur==pp and eng==ee),'source8-engine-before-parent-CAS')
        expected_result={'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False,'input_replayed':False,'resume_phase':'source'}
        if result_path.exists()or result_path.is_symlink():
            o.need(not result_path.is_symlink()and cur==pp and eng==ee and o.doc(o.ref(result_path))==expected_result,'source8-terminal-conflict-before-CAS');return o.doc(o.ref(result_path))
        _wait8_physical(node['codes']);live_lease(node['facts']['order']);_readonly_wait_receipt_absent(folder,len(be['calls']))
        for r in node['facts']['source_inputs'].values():o.raw(r)
        if eng==be:
            for name in ('zero-profile.json','capture-manifest.json','source.json'):o.need(not(folder/'companies'/str(be['index'])/name).exists()and not(folder/'companies'/str(be['index'])/name).is_symlink(),'source8-preCAS-output-present')
        from role_execution_launcher import save
        if eng==be:save(folder/'engine.json',ee)
        checkpoint('engine')
        if cur==bp:save(folder/'launcher.json',pp)
        checkpoint('parent');verify_readonly_wait(o.doc(o.ref(folder/'launcher.json')),proof);expected_result.update(launcher=o.ref(folder/'launcher.json'),engine=o.ref(folder/'engine.json'));o.immutable(result_path,expected_result);checkpoint('result');return expected_result

# Closed completed facts, not new execution authority. Catalogue pin changes
# per reviewed source publication, never per business task/attempt.
from contextvars import ContextVar as _ClosedContextVar
import verification_session as _closed_verification
_CLOSED_SOURCE=_ClosedContextVar('violation_closed_source_materials',default=None)
_CLOSED_CATALOGUE={'path': '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/references/completed-source-catalogues/1c30e60ce11978d3893e29ef05f14c5f05e11f057a37ceec7e6b45cdd0016836.json', 'sha256': '1c30e60ce11978d3893e29ef05f14c5f05e11f057a37ceec7e6b45cdd0016836'}

def completed_source_scope(*,max_bytes=512*1024*1024):
    """Explicit one pure command; existing Session owns all dependencies/expiry."""
    return _closed_verification.validation_scope(max_bytes=max_bytes)

def _closed_raw(reference):
    r=dict(reference);o.need(set(r)=={'path','sha256'},'closed-source-exact-ref');session=_closed_verification.current()
    return session._check((r['path'],r['sha256'])) if session is not None else o.raw(r)

def _closed_doc(reference):
    r=dict(reference);session=_closed_verification.current()
    return copy.deepcopy(session.read_pinned(r['path'],r['sha256'])) if session is not None else o.doc(r)

def _closed_paths():
    return {str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('bridge-navigation.py','violation_initial_ledger_recovery.py','violation_execution_ports.py','governance_zero_capture.py','verification_session.py','workflow.py')} | {str(PROJECT/'skills/wecom-messenger/scripts/files.py'),str(PROJECT/'skills/chrome-dom-export/scripts/bridge.py')} | {str(PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')} | {str(PROJECT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py')} | {'/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/content.js', '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/bridge-profile-discovery.py', '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/center_analysis_tab.py'} | {'/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/role_execution_order.py', '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/violation_execution.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/role_execution_launcher.py', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/role_execution_orchestration.py'} | {'/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/export_baseline_pages.py', '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/sw17.js', '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/policy.js', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/prepare_company_navigation.py'}

def _closed_catalogue():
    c=_closed_doc(_CLOSED_CATALOGUE);o.need(set(c)=={'kind','entries'}and c['kind']=='reviewed-violation-source-generation-catalogue-v1'and type(c['entries'])is list and 0<len(c['entries'])<=32,'closed-catalogue-schema');result={}
    for e in c['entries']:
        o.need(set(e)=={'original','archive','generation'}and (set(e['generation'])=={'release','slot'}or set(e['generation'])=={'kind','parent','vector_sha256'}or set(e['generation'])=={'kind','release','freeze','payload'}),'closed-catalogue-entry');r=e['original'];a=e['archive'];key=(r['path'],r['sha256'])
        o.need(r['path']in _closed_paths()and key not in result and a=={'path':str(PROJECT/'skills/violation-notifier/references/completed-source-archives'/(r['sha256']+'.py')),'sha256':r['sha256']},'closed-catalogue-exact-path-sha')
        if e['generation'].get('kind')=='reviewed-immutable-proof-dag-v3-source-generation-v1':
            _closed_legacy_session_generation(e);_closed_raw(a);result[key]=a;continue
        if 'kind'in e['generation']:
            _closed_source_seed(e);_closed_raw(a);result[key]=a;continue
        if e['generation']=={'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/c4-readonly-scope-candidate/supervisor-release.json', 'sha256': '117c9ec1b803e2c172193cc2a98eefa47f455e9c97ed4c6ad58485c6179393a2'}, 'slot': 'source'}:
            o.need(r=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/export_baseline_pages.py', 'sha256': '9e18d1d5052a967e1bd7d0db4d91e4e0eb2d2730f2ed4b3337616ae55c4f9fd0'},'completed-baseline-exact-published-slot');published=_closed_doc(e['generation']['release']);o.need(published.get('kind')=='supervisor-source-release-v1'and published.get('source')==r['path']and published.get('sha256')==r['sha256']and published.get('UI_calls')==0 and published.get('old_admissions_rewritten')is False,'completed-baseline-published-origin');_closed_raw(a);result[key]=a;continue
        published_origins={'/Users/feibing/work/projects/zmaibaole/work/performance-audit/export-terminal-prev-candidate/supervisor-release.json': {'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/export-terminal-prev-candidate/supervisor-release.json', 'sha256': '9eca07d03ad684968159c1052cde456fa21350acf2d8dfbf05c53872ddddce41'}, 'kind': 'supervisor-reviewed-content-update-release-v1', 'slot': 'published_files', 'sources': {'/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/content.js': '090a35790f9483694fd4c3868f7f8d975eebeea0592086a305c6ec422b2b4080', '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/center_analysis_tab.py': 'd443fd705e0e3b42696d47cd3f9368182f3d09f3e32bb4427d149e58935e11f7', '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/bridge-profile-discovery.py': '70f078bca0fef9849ce9916c9b8f1e13122cc381c85243d12cb0dd42e3f070f4'}}}
        spec=published_origins.get(e['generation']['release']['path'])
        if spec is not None:
            o.need(e['generation']['release']==spec['release']and e['generation']['slot']==spec['slot']and spec['sources'].get(r['path'])==r['sha256'],'completed-typed-published-exact-slot')
            published=_closed_doc(spec['release']);o.need(published.get('kind')==spec['kind']and published.get('published')is True,'completed-typed-published-root')
            items=published['published_files']if spec['slot']=='published_files'else published['files'];matches=[t for t in items if t.get('path')==r['path']]
            o.need(len(matches)==1 and (matches[0].get('sha256')if spec['slot']=='published_files'else matches[0].get('after'))==r['sha256'],'completed-typed-published-payload')
            _closed_raw(a);result[key]=a;continue
        root=_closed_doc(e['generation']['release']);o.need((root.get('kind')in ('supervisor-reviewed-source-release-v1','supervisor-reviewed-role-source-epoch-v1')or (root.get('kind')=='supervisor-reviewed-switch-confirm-settle-anchor-source-release-v1'and e['generation']['release']=={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/switch-confirm-settle-anchor-maintenance-candidate/supervisor-release.json', 'sha256': 'df96d216218d29a4b4a751a9a34e6b6f5efbfa59e8405a8c4d49081fe5d8aaf9'}and r=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/switch_read_recovery.py', 'sha256': '8381addf15630c54d0d48a216f10126f5beb45a417194d78b11186c944560438'}and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director'))and root.get('published')is True and root.get('test_projection_only')is False and root.get('reviewed_by')=='workshop-director','closed-catalogue-published-generation')
        ts=[t for t in root['targets']if t['target']==r['path']];slot=e['generation']['slot'];o.need(len(ts)==1 and slot in ('before','after')and ts[0].get(slot,{}).get('sha256')==r['sha256'],'closed-catalogue-generation-slot');_closed_raw(ts[0][slot]);_closed_raw(a);result[key]=a
    return result

def _closed_seal(current):
    folder=o.location(current['order']);pr=o.ref(folder/'launcher.json');o.need(_closed_doc(pr)==current and current.get('status')=='complete'and not current.get('error')and current.get(FIELD8),'closed-source-exact-completed-parent')
    order=_closed_doc(current['order']);origin=_closed_doc(current['origin_ref']);o.need(order.get('workflow')=='violation-notifier'and order.get('role')=='violation_operator'and current['scope_sha256']==order['scope_sha256']and all(current.get(k)==v for k,v in origin.items()),'closed-source-original-order-origin')
    er=o.ref(folder/'engine.json');engine=_closed_doc(er);fr=current['completion'];final=_closed_doc(fr);last=current['calls'][-1];ex=_closed_doc(last['result']);child=current.get('child');proof_ref=current[FIELD8];proof=_closed_doc(proof_ref)
    o.need(fr['path']==str(folder/'completion.json')and final.get('kind')=='violation-outer-completion-v1'and final.get('order')==engine.get('order')==current['order']and final.get('engine')==er and final.get('start_monotonic')==current['start_monotonic']and final.get('end_monotonic')==current['end_monotonic']and final.get('completed_at')==current['wall_ended_at'],'closed-source-final-binding')
    o.need(type(child)is dict and child.get('kind')=='violation-execution-child-result-v1'and child.get('status')=='complete'and child.get('phase')=='finish'and not child.get('error')and child.get('order')==current['order']and child.get('engine')==er and last.get('state')=='returned'and last['result']['path']==str(folder/'children'/(str(len(current['calls'])-1).zfill(4)+'-exit.json'))and ex.get('returncode')==0 and json.loads(ex['stdout'])==child,'closed-source-natural-terminal')
    o.need(engine.get('status')=='complete'and engine.get('phase')=='finish'and not engine.get('error')and engine.get(FIELD8)is None and final['proof']==engine.get('completion')and final['outcome']==engine['completion']['outcome'],'closed-source-original-client-proof')
    codes=proof.get('code_refs');o.need(proof.get('kind')==KIND8 and proof.get('ui_used')is False and proof.get('provider')in (WAIT8_CENTER_PROVIDER,SOURCE8_PROVIDER,WAIT8_MISSING_PROVIDER)and type(codes)is list and len(codes)==len({r['path']for r in codes})==150,'closed-source-typed-original150')
    clients=final['proof'].get('clients');o.need(type(clients)is list,'closed-source-original-client-refs');pins=[pr,er,current['order'],current['origin_ref'],fr,proof_ref,last['result'],*clients]
    for r in pins:_closed_raw(r)
    return {'historical':copy.deepcopy(codes),'catalogue':_closed_catalogue(),'pins':pins,'proof':proof_ref}

def _closed_material(reference,seal):
    r=dict(reference)
    try:_closed_raw(r);return r
    except ValueError:
        a=seal['catalogue'].get((r['path'],r['sha256']));o.need(r in seal['historical']and a is not None,'closed-source-outside-reviewed-generation');o.canonical(r['path']);_closed_raw(a);return copy.deepcopy(a)

def _violation_completed_raw(reference):
    seal=_CLOSED_SOURCE.get();return _closed_raw(reference if seal is None else _closed_material(reference,seal))

def _violation_completed_doc(reference):
    # Only code bytes may map. JSON evidence retains its original exact ref.
    return _closed_doc(reference)

def _violation_completed_order(reference):
    order=o.validate(dict(reference));_closed_doc(reference)
    offer=_closed_doc(order['offer']);_closed_doc(order['daily_completion'])
    if order.get('active_company_policy'):_closed_doc(order['active_company_policy'])
    for c in order['companies']:_closed_doc(c['ledger'])
    for item in offer.get('ledger_snapshots',[]):_closed_doc(item['snapshot'])
    return order

_CLOSED_CENTER_NODE=_center8_node
_CLOSED_SOURCE_NODE=_source8_node
_CLOSED_PREVIOUS_PHYSICAL=_wait8_physical
_CLOSED_PREVIOUS_VERIFY=verify_readonly_wait

def _center8_node(reference):
    return _closed_verification.memo_proof(_CLOSED_CENTER_NODE,reference) if _CLOSED_SOURCE.get()is not None else _CLOSED_CENTER_NODE(reference)

def _source8_node(reference):
    return _closed_verification.memo_proof(_CLOSED_SOURCE_NODE,reference) if _CLOSED_SOURCE.get()is not None else _CLOSED_SOURCE_NODE(reference)

def _wait8_physical(codes):
    seal=_CLOSED_SOURCE.get()
    if seal is None:return _CLOSED_PREVIOUS_PHYSICAL(codes)
    o.need(codes==seal['historical'],'closed-source-canonical150-unchanged')
    for r in codes:_closed_material(r,seal)

def verify_readonly_wait(current,proof_ref,*,installed=True):
    if not installed or current.get('status')!='complete':
        token=_CLOSED_SOURCE.set(None)
        try:return _CLOSED_PREVIOUS_VERIFY(current,proof_ref,installed=installed)
        finally:_CLOSED_SOURCE.reset(token)
    with completed_source_scope():
        seal=_closed_seal(current);o.need(proof_ref==seal['proof'],'closed-source-requested-proof');token=_CLOSED_SOURCE.set(seal)
        try:
            result=_CLOSED_PREVIOUS_VERIFY(current,proof_ref,installed=True);o.need(result['code_refs']==seal['historical'],'closed-source-public-history-unchanged');materials=[_closed_material(r,seal)for r in seal['historical']]
            for r in seal['pins']:_closed_raw(r)
            return {**result,'code_refs':materials,'historical_effective_code_refs':copy.deepcopy(seal['historical']),'source_verification_kind':'completed-reviewed-generation-data-materials-v1'}
        finally:_CLOSED_SOURCE.reset(token)

import hashlib
def _closed_source_seed(entry):
    """Root-reviewed first-generation files/bridge data only; no future-release cycle."""
    r=entry['original'];g=entry['generation'];o.need(g['kind']=='completed-original-source-vector-seed-v1'and (r['path'],r['sha256'])in {(str(o.PROJECT/'skills/wecom-messenger/scripts/files.py'),'a4d4a6c2e9290b694d7658d21c6fbe28f5c331106ea546ce592923fee8d6961b'),(str(o.PROJECT/'skills/chrome-dom-export/scripts/bridge.py'),'a99b58336b8007825d27458fde04ea7ce68773181471c0d6f0e14a84daca301d'),('/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/violation_execution.py', 'fe77127740de9f2705e42a8767e2fe1e31cf08c284c3828172ebae2427e01bc1')} | {('/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/sw17.js', '4672304381114e8ab9ca21c1a41d1a4b1beb977e6e29c36184102817c874c369'), ('/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/execution_timing.py', 'd38d42e0f0aa221757f591136a3f3b1600975b2ef09b6592058cc75b14dee7af'), ('/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/extension/policy.js', '3464df27fa8c6b2e1fa1bbc0bb6727c49eb4d864faec2bfddf2b4c5489261605'), ('/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/prepare_company_navigation.py', '30022fe829b217d3f874e0b36e64da3d4c0c3ea932405975a5595fa48b1e62d1')},'completed-source-seed-finite-path-sha')
    p=_closed_doc(g['parent']);folder=o.location(p['order']);o.need(g['parent']['path']==str(folder/'launcher.json')and p.get('status')=='complete'and not p.get('error'),'completed-source-seed-canonical-complete')
    origin=_closed_doc(p['origin_ref']);o.need(all(p.get(k)==v for k,v in origin.items()),'completed-source-seed-origin');engine_ref=o.ref(folder/'engine.json');engine=_closed_doc(engine_ref);final=_closed_doc(p['completion']);exit=_closed_doc(p['calls'][-1]['result'])
    o.need(p['completion']['path']==str(folder/'completion.json')and engine.get('status')=='complete'and engine.get('order')==p['order']==final.get('order')and final.get('engine')==engine_ref and final.get('proof')==engine.get('completion')and exit.get('returncode')==0 and json.loads(exit['stdout'])==p['child']and p['child'].get('status')=='complete','completed-source-seed-terminal')
    if p.get('role_source_epoch'):
        epoch=_closed_doc(p['role_source_epoch']);o.need(epoch['order']==p['order'],'completed-source-seed-epoch-order');codes=epoch['effective_code_refs']
    elif p.get('violation_confirmed_navigation_wait_recovery'):
        proof=_closed_doc(p['violation_confirmed_navigation_wait_recovery']);codes=proof['code_refs']
    else:codes=p['code_refs'];o.need(codes==origin['code_refs'],'completed-source-seed-original-vector')
    o.need(len(codes)==len({v['path']for v in codes})and (len(codes)==150if r['path']==str(o.PROJECT/'skills/chrome-dom-export/scripts/bridge.py')else len(codes)in (150,160))and sum(v==r for v in codes)==1 and hashlib.sha256(json.dumps(codes,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()==g['vector_sha256'],'completed-source-seed-vector-binding')

# SeparateCENTER8 subtype. Never changes old failure/error admissibility.
WAIT8_MISSING_PROVIDER='confirmed-center-missing-gid-readonly-initial-v1'
_MISSING8_POLICY=_ClosedContextVar('center_missing_gid_provider',default=False)
def _center8_missing():return _MISSING8_POLICY.get()is True
def _center8_provider():return WAIT8_MISSING_PROVIDER if _center8_missing()else WAIT8_CENTER_PROVIDER

def _missing8_observations(owner,binding,values,read,evidence):
    nav=_center8_navigation();state=owner.s;need=o.need;records=state.get('readonly_route_recovery',[])
    need(len(records)==1 and not state.get('readonly_route_exhausted')and state.get('observation_transport')=='readonly-scope-projection-v1'and len(state.get('scope_projections',[]))>=2,'missing8-exact-existing-one-pending')
    key=hashlib.sha256(json.dumps({'mode':'center','binding':binding,'original_call':state['calls'][-1]},ensure_ascii=False,sort_keys=True).encode()).hexdigest();ref=records[0];record=read({k:ref[k]for k in ('path','sha256')})
    need(ref.get('attempt')==0 and ref.get('transition_key')==key and ref.get('error')=='navigation-transition-target-pending'and record.get('kind')=='confirmed-navigation-readonly-race-v1'and record.get('mode')=='center'and record.get('binding')==binding and record.get('attempt')==0 and record.get('transition_key')==key and record.get('error')=='navigation-transition-target-pending'and record.get('input_replayed')is False,'missing8-original-pending-key')
    projection_ref=state['scope_projections'][-2];projection=read(projection_ref);raw=projection['raw'];rr={k:raw[k]for k in ('path','sha256')};reply=read(rr);need(raw in state['raw_observations']and reply.get('ok')is True and projection==nav.scope_projection(raw,raw['command'],reply['result']),'missing8-overview-owned-projection')
    v=reply['result'];sample={'before':nav.context(v['before'],owner.tab,owner.job['groupid']),'after':nav.context(v['after'],owner.tab,owner.job['groupid']),'tree':v['tree']};nav.transition_sample_scope(owner,binding,sample)
    need(sample==record['sample']and nav.urlsplit(sample['before']['url']).path==nav.urlsplit(sample['after']['url']).path=='/p/governance/home_overview'and sample['tree'].get('url')=='https://life.douyin.com/p/governance/home_overview','missing8-original-overview-pending')
    observation=read(state['last_tree']);need(state['observations'][-1]==state['last_tree']and observation.get('source')=='local-dom-bridge'and observation.get('navigation_fingerprint')==nav.tag(owner.job)and observation.get('tab_id')==owner.tab and observation.get('tab')==sample['before']and observation.get('tree')==sample['tree']and observation.get('transport_projection')==projection_ref,'missing8-original-overview-observation')
    raw=state['raw_observations'][-1];lastref={k:raw[k]for k in ('path','sha256')};last=read(lastref);need(last.get('ok')is True and raw['command']=={'op':'readonly-scope','tabId':owner.tab,'windowId':binding['window_id']}and [last['result'][k]for k in ('before','ping','tree','after')]==values,'missing8-last-mixed-owned-read')
    mixed=nav.missing_gid_scope_sample(owner,last['result']);need(nav.missing_gid_transition_sample(owner,binding,mixed),'missing8-last-missing-only-gid-pending')
    evidence.extend([{k:ref[k]for k in ('path','sha256')},projection_ref,rr,state['last_tree'],lastref])
    return {'transition_key':key,'overview_audit':{k:ref[k]for k in ('path','sha256')},'mixed_raw':lastref,'mixed_sample':mixed,'observations_consumed':2,'max_total_observations':3,'remaining_observations':1,'mixed_not_completed_scope':True,'input_replayed':False}

_MISSING8_PREVIOUS_PLAN=plan_readonly_wait
_MISSING8_PREVIOUS_VERIFY=verify_readonly_wait
_MISSING8_PREVIOUS_RECOVER=recover_readonly_wait

def plan_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,installed=True,resume_proof=None):
    missing=o.doc(release_ref).get('confirmed_navigation_wait_initial',{}).get('kind')==WAIT8_MISSING_PROVIDER;token=_MISSING8_POLICY.set(missing)
    try:return _MISSING8_PREVIOUS_PLAN(parent_ref,worker_ref,release_ref,old_refs,installed=installed,resume_proof=resume_proof)
    finally:_MISSING8_POLICY.reset(token)

def verify_readonly_wait(current,proof_ref,*,installed=True):
    missing=o.doc(proof_ref).get('provider')==WAIT8_MISSING_PROVIDER;token=_MISSING8_POLICY.set(missing)
    try:return _MISSING8_PREVIOUS_VERIFY(current,proof_ref,installed=installed)
    finally:_MISSING8_POLICY.reset(token)

def recover_readonly_wait(parent_ref,worker_ref,release_ref,old_refs,*,resume_proof=None,checkpoint=_recovery_checkpoint):
    missing=o.doc(release_ref).get('confirmed_navigation_wait_initial',{}).get('kind')==WAIT8_MISSING_PROVIDER;token=_MISSING8_POLICY.set(missing)
    try:
        # Select the reviewed initial CENTER transaction directly: older SOURCE8
        # delegation predates checkpoint forwarding. Keep legacy dispatch intact.
        target=_SOURCE8_PREVIOUS_RECOVER if missing else _MISSING8_PREVIOUS_RECOVER
        return target(parent_ref,worker_ref,release_ref,old_refs,resume_proof=resume_proof,checkpoint=checkpoint)
    finally:_MISSING8_POLICY.reset(token)

# One explicitly registered immutable missing-GID CENTER node. All current seal,
# prefix, source and physical checks remain in their existing public callers.
_PURE_CENTER_NAV_LOADER=_center8_navigation
def _center8_navigation():
    session=_closed_verification.current()
    if session is None or not session.enabled or _CLOSED_SOURCE.get()is None or not _center8_missing():return _PURE_CENTER_NAV_LOADER()
    return session.bound_pure_module('closed-center-nav-v1',PROJECT/'skills/violation-notifier/scripts/bridge-navigation.py',_PURE_CENTER_NAV_LOADER)

_PURE_CENTER_HELPER_FUNCTIONS=('_center8_node','_center8_pure_registry','_CLOSED_CENTER_NODE','_CLOSED_PREVIOUS_PHYSICAL','_center8_authority','_center8_ledgers','_center8_missing','_center8_navigation','_PURE_CENTER_NAV_LOADER','_center8_original','_center8_provider','_center8_sources','_closed_doc','_closed_material','_closed_raw','_missing8_observations','_readonly_wait_doc','_readonly_wait_receipt_absent','_violation_completed_doc','_violation_completed_order','_violation_completed_raw','_wait8_children_worker','_wait8_original_states','_wait8_physical','_wait8_repaired')
_PURE_CENTER_NAV_FUNCTIONS=('missing_gid_scope_sample','missing_gid_transition_sample','observation_members','read_pinned','read_scope_projection','require','scope','scope_projection','tag','transition_binding','transition_paths','transition_sample_scope','context','identity','nodes','exact','unique','urlsplit','parse_qs')
def _center8_pure_registry(nav):
    import execution_timing,dom_evidence,readonly_tick_snapshot,role_execution_launcher
    return ((sys.modules[__name__],_PURE_CENTER_HELPER_FUNCTIONS,('FIELD8','GROUPS','KIND8','PROJECT','WAIT8_CENTER_ERROR','WAIT8_CENTER_PATHS','WAIT8_CENTER_PROVIDER','WAIT8_MISSING_PROVIDER','_CLOSED_SOURCE','_MISSING8_POLICY','_CLOSED_CATALOGUE','_PURE_CENTER_HELPER_FUNCTIONS','_PURE_CENTER_NAV_FUNCTIONS','Path','datetime','__file__')),
        (nav,_PURE_CENTER_NAV_FUNCTIONS,('CENTER','MISSING_GID_PENDING','VERSION','ROOT','Path','date','__file__')),
        (o,('build','canonical','digest','doc','encode','location','need','order_path','raw','ref','validate'),('FLOW','KIND','PROJECT','ROLE','Path','date','__file__')),
        (dom_evidence,('context','exact','identity','leaves','nodes','unique','urlsplit','parse_qs'),('VERSION','__file__')),
        (readonly_tick_snapshot,('decode','urlsplit'),('__file__',)),
        (execution_timing,('company_names','company_policy','need'),('COMPANY_GROUPS','Path','TimingError','__file__')),
        (role_execution_launcher,('command','effective_scope','reboot_admission'),('PROJECT','FORMAL','__file__')))

_PURE_CENTER_PREVIOUS_NODE=_center8_node
def _center8_node(reference):
    session=_closed_verification.current();seal=_CLOSED_SOURCE.get()
    if session is None or not session.enabled or seal is None or not _center8_missing():return _PURE_CENTER_PREVIOUS_NODE(reference)
    nav=_center8_navigation();groups=_center8_pure_registry(nav)
    # Full validated source authority partitions identical proof arguments. The
    # seal is freshly derived outside this memo on every public invocation.
    context={'provider':_center8_provider(),'catalogue':_CLOSED_CATALOGUE,'historical':seal['historical'],'materials':[[list(k),v]for k,v in sorted(seal['catalogue'].items())],'proof':seal['proof'],'python':sys.executable}
    return session.memo_registered_pure('closed-center-node-v1',_CLOSED_CENTER_NODE,reference,groups,context)

# A real legacy release declares source_sha256 rather than modern targets.
# This distinct descriptor never manufactures a before/after slot or a seed.
_LEGACY_SESSION_GENERATION={'kind': 'reviewed-immutable-proof-dag-v3-source-generation-v1', 'release': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/immutable-proof-dag-v3-investigation/supervisor-release.json', 'sha256': '49f18c5fe813185e5f44c9e9e1dd2fc7eef4df908f639d4650decfdc68a4eb32'}, 'freeze': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/immutable-proof-dag-v3-investigation/freeze.json', 'sha256': '7193c0a5cce77d42861b2f9510f95e93a6f1c06d3b2827a304a3676e7b1e5647'}, 'payload': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/immutable-proof-dag-v3-investigation/verification_session.py', 'sha256': '52ed58cf2e27a41bdf5ece5071fc1a2c1fabd11601e20eff1617773e9f650d0e'}}
_LEGACY_SESSION_ORIGINAL={'path': '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/verification_session.py', 'sha256': '52ed58cf2e27a41bdf5ece5071fc1a2c1fabd11601e20eff1617773e9f650d0e'}
def _closed_legacy_session_generation(entry):
    generation=entry['generation']
    o.need(set(generation)=={'kind','release','freeze','payload'}and generation==_LEGACY_SESSION_GENERATION and entry['original']==_LEGACY_SESSION_ORIGINAL and entry['original']['path']==str(PROJECT/'skills/violation-notifier/scripts/verification_session.py'),'closed-legacy-session-exact-generation')
    root=_closed_doc(generation['release']);freeze=_closed_doc(generation['freeze']);checksum=entry['original']['sha256']
    o.need(root.get('kind')=='supervisor-immutable-proof-dag-v3-release-v1'and root.get('decision')=='published'and root.get('candidate_freeze_sha256')==generation['freeze']['sha256']and root.get('source_sha256',{}).get('verification_session')==checksum,'closed-legacy-session-published-source')
    o.need(freeze.get('kind')=='immutable-proof-dag-v3-small-recovery-final-freeze'and freeze.get('source_sha256',{}).get('verification_session')==freeze.get('files',{}).get('verification_session.py')==checksum and generation['payload']['sha256']==checksum and generation['payload']['path']==str(Path(generation['freeze']['path']).parent/'verification_session.py'),'closed-legacy-session-frozen-payload')
    _closed_raw(generation['payload'])

# Typed daily DOM identity constructor failure, before any VI engine/business.
DOM_ORIGIN_KIND='verified-violation-typed-dom-preengine-origin-recovery-v1'
DOM_ORIGIN_ERROR='execution-acquisition-copy-path'
def _dom_origin_ledgers(order,*,live):
    from violation_execution_ports import initial_ledger_reference
    rows=[]
    for company in order['companies']:
        snapshot=company['ledger'];o.raw(snapshot);canonical=Path(company['root'])/'state.json'
        if live:initial_ledger_reference(company,order=order)
        rows.append({'company':company['company'],'groupid':company['groupid'],'snapshot':snapshot,'canonical':{'path':str(canonical),'sha256':snapshot['sha256']}})
    return rows
def _dom_origin_contract(parent,worker_ref,*,live):
    order=o.validate(parent['order']);folder=o.location(parent['order']);o.need(parent['kind']=='role-execution-launcher-v1' and parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and parent.get('mode')=='acceptance' and parent.get('origin')=='fresh' and not parent.get('child') and not parent.get('completion') and FIELD not in parent,'violation-initial-exact-constructor-hold')
    origin=o.doc(parent['origin_ref']);o.need(all(parent.get(k)==v for k,v in origin.items()),'violation-initial-origin-changed')
    o.need(len(parent['calls'])==1 and parent['calls'][0]['state']=='returned','violation-initial-sole-child')
    call=parent['calls'][0];o.need(Path(call['launch']['path'])==folder/'children/0000-launch.json' and Path(call['result']['path'])==folder/'children/0000-exit.json','violation-initial-canonical-child')
    la=o.doc(call['launch']);ex=o.doc(call['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(call['argv']==la['argv']==ex['argv']==argv and la['order']==parent['order'] and la['index']==0 and ex['launch']==call['launch'] and type(ex.get('returncode')) is int and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':DOM_ORIGIN_ERROR},'violation-initial-exact-local-failure')
    o.need(parent['start_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-initial-clock-order')
    if live:o.need(not (folder/'engine.json').exists() and not (folder/'engine.json').is_symlink() and not (folder/'companies').exists() and not (folder/'companies').is_symlink(),'violation-initial-zero-business-required')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent
    o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and request['attempt_id'].startswith(request['task']['id']+'-') and Path(worker_ref['path'])==attempt/'exit.json' and Path(worker['request']['path'])==attempt/'request.json' and Path(worker['response']['path'])==attempt/'response.json' and worker['attempt_id']==request['attempt_id'] and type(worker.get('returncode')) is int and worker['returncode']==0,'violation-initial-natural-worker-exit')
    o.need(request['kind']=='workshop-worker-request-v1' and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==parent['order'] and response['kind']=='workshop-worker-result-v1' and response['task_id']==request['task']['id'] and response['attempt_id']==request['attempt_id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'violation-initial-original-worker-binding')
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(pe['argv']==expected and request['config']['python']==expected[0]and request['config']['project']==str(o.PROJECT)and o.doc(request['config_ref'])==request['config'],'violation-local-plan-parent-command');outer=request['task']['outer'];o.need(outer['boot']==parent['boot_identity'] and outer['clock_contract']==parent['clock_contract'] and outer['start_monotonic']<=parent['start_monotonic'] and datetime.fromisoformat(outer['started_at'])<=datetime.fromisoformat(parent['wall_started_at']),'violation-initial-original-outer-clock')
    pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));expected=[request['config']['python'],str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(request['config']['project']==str(o.PROJECT) and request['config']['coordinator_root']==str(o.PROJECT/'runtime/workshop-director') and request['config']['python']==str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python') and pe['argv']==expected and pe['returncode']==0 and not o.raw(pe['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==call['result'] and out['child'] is None and out['completion'] is None,'violation-initial-parent-natural-exit')
    return {'order':order,'ledgers':_dom_origin_ledgers(order,live=live),'initial_failed_call':call,'worker_task_id':request['task']['id'],'original_outer':request['task']['outer'],'evidence':[parent['order'],parent['origin_ref'],call['launch'],call['result'],worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']]}
def _dom_origin_sources(original,release_ref,*,installed):
    release=o.doc(release_ref);targets=release.get('targets',[]);wanted={str(o.PROJECT/p)for p in ('skills/violation-notifier/scripts/violation_execution_ports.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')}
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(targets)==3 and {t['target']for t in targets}==wanted,'violation-dom-exact-source-release')
    codes=copy.deepcopy(original['code_refs']);by={r['path']:r for r in codes}
    for target in targets:
        path=target['target'];before=target['before'];after=target['after']
        o.need(target['mode']==420 and target['old_sha256']==before['sha256']==by[path]['sha256']and Path(before['path']).name==Path(path).name+'.before','violation-dom-source-before');o.raw(before);o.raw(after)
        replacement={'path':path,'sha256':after['sha256']}
        if installed:o.need(o.ref(Path(path))==replacement,'violation-dom-source-not-installed')
        codes[codes.index(by[path])]=replacement
    for source in codes:
        if installed or source['path']not in wanted:o.raw(source)
    return codes

def _dom_origin_facts(original,worker_ref,*,live):
    facts=_dom_origin_contract(original,worker_ref,live=live);order=facts['order'];o.need(order.get('collection_contract')=='three-flow-collection-ready-v1'and order.get('daily_collection_ready'),'violation-dom-staged-order')
    from violation_execution_ports import ProductionPorts
    ports=ProductionPorts(original['tab_id'],original['pid'],request=lambda *a,**k:(_ for _ in()).throw(ValueError('violation-dom-recovery-no-RPC')))
    identities=ports.ready_identities(order);origins=ports.acquisition_origins
    o.need(any(origin.get('kind')=='verified-daily-dom-identity-context-v1'for origin in origins.values())and all(c['skipped']or(c['company']in identities and c['company']in origins)for c in order['companies']),'violation-dom-verified-origins')
    return {**facts,'origins':origins,'identities':identities}

def _dom_origin_repaired(original,proof):
    value=copy.deepcopy(original);value.update(status='running',**{FIELD:proof});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':DOM_ORIGIN_ERROR,'recovery':proof});return value

def plan_dom_origin(parent_ref,worker_ref,release_ref,*,installed=True):
    original=o.doc(parent_ref);o.need(parent_ref['path']==str(o.location(original['order'])/'launcher.json'),'violation-dom-parent-path');facts=_dom_origin_facts(original,worker_ref,live=True);live_lease(facts['order']);codes=_dom_origin_sources(original,release_ref,installed=installed)
    return {'kind':DOM_ORIGIN_KIND,'original_parent':parent_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'engine_was_absent':True,'ui_used':False}

def verify_dom_origin(current,proof_ref,*,installed=True):
    proof=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-dom-origin-recovery'/proof['original_parent']['sha256']
    o.need(proof['kind']==DOM_ORIGIN_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and proof['engine_was_absent']is True and proof['ui_used']is False,'violation-dom-proof-kind-path');archive=proof['parent_archive'];o.need(archive['path']==str(base/'original-parent.json')and archive['sha256']==proof['original_parent']['sha256'],'violation-dom-parent-archive');original=o.doc(archive);facts=_dom_origin_facts(original,proof['worker'],live=False);codes=_dom_origin_sources(original,proof['release'],installed=installed)
    expected=_dom_origin_repaired(original,proof_ref);o.need(facts==proof['facts']and codes==proof['code_refs']and current['calls'][:1]==original['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()),'violation-dom-original-history')
    return {'kind':DOM_ORIGIN_KIND,'code_refs':codes,'initial_failed_call':original['calls'][0],'failed_calls':original['calls'],'evidence':[proof_ref,archive,proof['release'],*facts['evidence']]}

_DOM_ORIGIN_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==DOM_ORIGIN_KIND:return verify_dom_origin(current,proof_ref,installed=kwargs.get('installed',True))
    return _DOM_ORIGIN_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_dom_origin(parent_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-dom-origin-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof_ref=o.ref(base/'proof.json');proof=o.doc(proof_ref);o.need(proof['original_parent']==parent_ref and proof['worker']==worker_ref and proof['release']==release_ref,'violation-dom-original-intent')
        else:
            proof=plan_dom_origin(parent_ref,worker_ref,release_ref);proof['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));proof_ref=o.immutable(base/'proof.json',proof);checkpoint('proof-published')
        original=o.doc(proof['parent_archive']);expected=_dom_origin_repaired(original,proof_ref);current=o.doc(o.ref(folder/'launcher.json'))
        o.need(current==original or current==expected,'violation-dom-current-conflict');verify_dom_origin(expected,proof_ref)
        if current==original:
            o.need(not(folder/'engine.json').exists()and not(folder/'companies').exists(),'violation-dom-zero-business-CAS');live_lease(proof['facts']['order']);from role_execution_launcher import save;save(folder/'launcher.json',expected)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'proof':proof_ref,'engine_created':False,'ui_used':False}

# Pure local plan-result reconciliation; no business input is retried.
LOCAL_PLAN_KIND='verified-violation-local-DOM-plan-result-recovery-v1'
LOCAL_PLAN_ERROR='completed-operator-acquisition-required'
def _local_plan_prior(parent):
    previous=parent[FIELD];proof=o.doc(previous);o.need(proof['kind']==DOM_ORIGIN_KIND and proof['engine_was_absent']is True and proof['ui_used']is False,'violation-local-plan-previous-kind')
    original=o.doc(proof['parent_archive']);o.need(proof['parent_archive']['sha256']==proof['original_parent']['sha256']and previous['path']==str(o.location(parent['order'])/'.violation-dom-origin-recovery'/proof['original_parent']['sha256']/'proof.json'),'violation-local-plan-previous-path')
    expected=_dom_origin_repaired(original,previous);o.need(parent['order']==original['order']and parent['code_refs']==original['code_refs']and parent['calls'][:1]==original['calls']and parent.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(original['origin_ref']).items()),'violation-local-plan-inherited-history')
    release=o.doc(proof['release']);wanted={str(o.PROJECT/p)for p in ('skills/violation-notifier/scripts/violation_execution_ports.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'violation-local-plan-inherited-release')
    codes=copy.deepcopy(original['code_refs']);by={r['path']:r for r in codes}
    for t in release['targets']:
        o.need(t['old_sha256']==t['before']['sha256']==by[t['target']]['sha256']and t['mode']==420,'violation-local-plan-inherited-source');o.raw(t['before']);o.raw(t['after']);codes[codes.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    o.need(codes==proof['code_refs']and proof['facts']['initial_failed_call']==original['calls'][0]and proof['facts']['order']==o.doc(parent['order']),'violation-local-plan-prior-vector')
    # The already executed, hash-bound W45 qualification remains historical;
    # new worker/plan/result/source facts are independently checked below.
    for r in proof['facts']['evidence']:o.raw(r)
    return previous,proof,codes

def _local_plan_sources(codes,release_ref,*,installed):
    release=o.doc(release_ref);targets=release.get('targets',[]);wanted={str(o.PROJECT/p)for p in ('skills/violation-notifier/scripts/violation_execution_ports.py','skills/violation-notifier/scripts/bridge-navigation.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(targets)==4 and {t['target']for t in targets}==wanted,'violation-local-plan-four-sources');result=copy.deepcopy(codes);by={r['path']:r for r in result}
    for t in targets:
        o.need(t['mode']==420 and t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256'],'violation-local-plan-source-before');o.raw(t['before']);o.raw(t['after']);after={'path':t['target'],'sha256':t['after']['sha256']}
        if installed:o.need(o.ref(Path(t['target']))==after,'violation-local-plan-source-installed')
        result[result.index(by[t['target']])]=after
    for r in result:
        if installed or r['path']not in wanted:o.raw(r)
    return result

def _local_plan_contract(parent,engine,worker_ref):
    previous,old,codes=_local_plan_prior(parent);order=o.doc(parent['order']);folder=o.location(parent['order']);o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==2 and all(c['state']=='returned'for c in parent['calls']),'violation-local-plan-parent')
    call=parent['calls'][1];la=o.doc(call['launch']);ex=o.doc(call['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000'];o.need(call['launch']['path']==str(folder/'children/0001-launch.json')and call['result']['path']==str(folder/'children/0001-exit.json')and call['argv']==la['argv']==ex['argv']==argv and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':LOCAL_PLAN_ERROR}and la['index']==1 and la['order']==parent['order']and parent['start_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-local-plan-natural-child')
    o.need(engine['kind']=='violation-execution-v1'and engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==LOCAL_PLAN_ERROR and engine['phase']=='plan'and engine['index']==0 and len(engine['calls'])==1 and not engine.get('business_journals')and all(c.get('phase')=='plan'and c.get('artifacts')=={}for c in engine['companies']),'violation-local-plan-engine');failed=engine['calls'][0];o.need(failed['step']=='plan'and failed['state']=='failed'and failed['error']==LOCAL_PLAN_ERROR and failed['company_index']==0 and 'result'not in failed and failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['artifacts']=={}and failed['context']['folder']==str(folder/'companies/0'),'violation-local-plan-only-call')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));o.need(attempt==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id']and worker['returncode']==0 and request['context']['order']==parent['order']and response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['task_id']==request['task']['id']and response['attempt_id']==request['attempt_id']and request['task']['flow']==o.FLOW and request['task']['day']==order['day']and pe['returncode']==0 and not o.raw(pe['stderr'])and out['status']=='hold'and out['last_child_receipt']==call['result'],'violation-local-plan-worker')
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(pe['argv']==expected and request['config']['python']==expected[0]and request['config']['project']==str(o.PROJECT)and o.doc(request['config_ref'])==request['config'],'violation-local-plan-parent-command');outer=request['task']['outer'];o.need(outer['boot']==parent['boot_identity']and outer['clock_contract']==parent['clock_contract']and outer['start_monotonic']<=parent['start_monotonic']and datetime.fromisoformat(outer['started_at'])<=datetime.fromisoformat(parent['wall_started_at']),'violation-local-plan-outer');return {'previous_proof':previous,'previous_codes':codes,'order':order,'failed_engine_call':failed,'worker':worker_ref,'outer':outer,'evidence':[worker_ref,worker['request'],worker['response'],pe_ref,pe['stdout'],pe['stderr'],call['launch'],call['result']]}

def _local_plan_engine(original,proof_ref,proof):
    value=copy.deepcopy(original);call=value['calls'][0];call.update(state='returned',result=proof['plan_result'],returned_at=proof['at'],local_result_reconciliation={'proof':proof_ref,'original_failed_call':copy.deepcopy(original['calls'][0])});value.update(status='running',local_plan_result_recovery=proof_ref);value.pop('error');return value

def _local_plan_parent(original,proof_ref):
    value=copy.deepcopy(original);value.update(status='running',**{FIELD:proof_ref});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':LOCAL_PLAN_ERROR,'recovery':proof_ref,'result_kind':'reconciled-local-plan-result-not-original-child-success'});return value

def plan_local_plan(parent_ref,engine_ref,worker_ref,release_ref,*,installed=True):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'violation-local-plan-path');facts=_local_plan_contract(parent,engine,worker_ref);live_lease(facts['order']);codes=_local_plan_sources(facts['previous_codes'],release_ref,installed=installed)
    from violation_execution_ports import ProductionPorts
    ports=ProductionPorts(parent['tab_id'],parent['pid'],request=lambda *a,**k:(_ for _ in()).throw(ValueError('violation-local-plan-no-RPC')));result=ports.step('plan',facts['failed_engine_call']['context']);result_ref=o.immutable(folder/'receipts/00001.json',result)
    return {'kind':LOCAL_PLAN_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'plan_result':result_ref,'at':stamp(),'ui_used':False}

def _local_plan_result_check(parent,proof,facts):
    folder=o.location(parent['order']);o.need(proof['kind']==LOCAL_PLAN_KIND and proof['ui_used']is False and datetime.fromisoformat(proof['at']).utcoffset()is not None,'violation-local-plan-result-kind')
    from violation_execution_ports import ProductionPorts
    ports=ProductionPorts(parent['tab_id'],parent['pid'],request=lambda *a,**k:(_ for _ in()).throw(ValueError('violation-local-plan-no-RPC')));result=o.doc(proof['plan_result']);artifacts=result['artifacts'];
    for reference in artifacts.values():o.raw(reference)
    import workflow as workflow_api
    context=facts['failed_engine_call']['context'];o.need(artifacts['plan']['path']==str(Path(context['folder'])/'plan.json')and artifacts['job']['path']==str(Path(context['folder'])/'navigation-job.json')and artifacts['identity_receipt']['path']==str(Path(context['folder'])/'navigation-identity-context.json')and o.doc(artifacts['plan'])==workflow_api.plan(o.doc(context['company']['ledger']),context['order']['day']),'violation-local-plan-exact-plan');regenerated=ports.dom_plan_result(facts['failed_engine_call']['context'],artifacts['plan'],artifacts['identity_receipt']);o.need(regenerated==result and proof['plan_result']['path']==str(folder/'receipts/00001.json'),'violation-local-plan-result-derived');
def verify_local_plan(current,proof_ref,*,installed=True):
    proof=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-local-plan-context-recovery'/proof['original_parent']['sha256'];o.need(proof['kind']==LOCAL_PLAN_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and proof['ui_used']is False,'violation-local-plan-proof');parent=o.doc(proof['parent_archive']);engine=o.doc(proof['engine_archive']);o.need(proof['parent_archive']['sha256']==proof['original_parent']['sha256']and proof['engine_archive']['sha256']==proof['original_engine']['sha256'],'violation-local-plan-original-archives');facts=_local_plan_contract(parent,engine,proof['worker']);codes=_local_plan_sources(facts['previous_codes'],proof['release'],installed=installed)
    o.need(facts==proof['facts']and codes==proof['code_refs'],'violation-local-plan-derived-facts');_local_plan_result_check(parent,proof,facts);expected=_local_plan_parent(parent,proof_ref);o.need(current['calls'][:2]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'violation-local-plan-history')
    live=o.doc(o.ref(folder/'engine.json'));want=_local_plan_engine(engine,proof_ref,proof)['calls'][0];actual=copy.deepcopy(live['calls'][0]);actual.pop('applied',None);o.need(actual==want and live.get('local_plan_result_recovery')==proof_ref and live['order']==parent['order'],'violation-local-plan-engine-prefix')
    return {'kind':LOCAL_PLAN_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,proof['parent_archive'],proof['engine_archive'],proof['plan_result'],proof['release'],facts['previous_proof'],*facts['evidence']]}

_LOCAL_PLAN_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==LOCAL_PLAN_KIND:return verify_local_plan(current,proof_ref,installed=kwargs.get('installed',True))
    return _LOCAL_PLAN_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_local_plan(parent_ref,engine_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-local-plan-context-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            proof_ref=o.ref(base/'proof.json');proof=o.doc(proof_ref);o.need(proof['original_parent']==parent_ref and proof['original_engine']==engine_ref and proof['worker']==worker_ref and proof['release']==release_ref,'violation-local-plan-same-intent')
        else:
            proof=plan_local_plan(parent_ref,engine_ref,worker_ref,release_ref);proof['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));proof['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));proof_ref=o.immutable(base/'proof.json',proof);checkpoint('proof-published')
        parent=o.doc(proof['parent_archive']);engine=o.doc(proof['engine_archive']);expected_parent=_local_plan_parent(parent,proof_ref);expected_engine=_local_plan_engine(engine,proof_ref,proof);current_parent=o.doc(o.ref(folder/'launcher.json'));current_engine=o.doc(o.ref(folder/'engine.json'));o.need(current_parent in(parent,expected_parent)and current_engine in(engine,expected_engine),'violation-local-plan-CAS-frontier')
        # Validate all immutable inputs and exact current prefixes before CAS;
        # verify below requires the resulting engine prefix, so derive it here.
        o.need(proof['parent_archive']['sha256']==parent_ref['sha256']and proof['engine_archive']['sha256']==engine_ref['sha256'],'violation-local-plan-original-binding');facts=_local_plan_contract(parent,engine,worker_ref);codes=_local_plan_sources(facts['previous_codes'],release_ref,installed=True);o.need(facts==proof['facts']and codes==proof['code_refs'],'violation-local-plan-CAS-derived');_local_plan_result_check(parent,proof,facts);live_lease(facts['order'])
        if current_engine==engine:
            from violation_execution import atomic
            atomic(folder/'engine.json',expected_engine);checkpoint('engine-CAS')
        verify_local_plan(expected_parent,proof_ref)
        if current_parent==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',expected_parent)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof_ref,'ui_used':False,'local_result_reconciliation':True}

# Confirmed navigation read recovery: metadata follows the public switch proof.
NAV_CONTRACT_KIND='verified-violation-confirmed-navigation-contract-recovery-v1'
NAV_CONTRACT_ERROR='read-recovery-navigation-only-contract-required'
def _nav_contract_prior(parent):
    reference=parent[FIELD];proof=o.doc(reference);folder=o.location(parent['order']);o.need(proof['kind']==LOCAL_PLAN_KIND and reference['path']==str(folder/'.violation-local-plan-context-recovery'/proof['original_parent']['sha256']/'proof.json'),'violation-nav-prior-local-plan')
    before=o.doc(proof['parent_archive']);engine=o.doc(proof['engine_archive']);o.need(proof['parent_archive']['sha256']==proof['original_parent']['sha256']and proof['engine_archive']['sha256']==proof['original_engine']['sha256'],'violation-nav-prior-archives');facts=_local_plan_contract(before,engine,proof['worker']);o.need(facts==proof['facts'],'violation-nav-prior-facts')
    codes=copy.deepcopy(facts['previous_codes']);by={r['path']:r for r in codes};release=o.doc(proof['release']);wanted={str(o.PROJECT/p)for p in('skills/violation-notifier/scripts/violation_execution_ports.py','skills/violation-notifier/scripts/bridge-navigation.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')}
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==4 and {t['target']for t in release['targets']}==wanted,'violation-nav-prior-release')
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'violation-nav-prior-source');o.raw(t['before']);o.raw(t['after']);codes[codes.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    o.need(codes==proof['code_refs'],'violation-nav-prior-vector');expected=_local_plan_parent(before,reference);o.need(parent['calls'][:len(before['calls'])]==before['calls']and parent['code_refs']==before['code_refs']and parent.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(before['origin_ref']).items()),'violation-nav-prior-history');o.raw(proof['plan_result']);return reference,proof,codes

def _nav_contract_sources(codes,release_ref,installed):
    release=o.doc(release_ref);wanted={str(o.PROJECT/p)for p in('skills/douyin-laike-operator/scripts/switch_read_recovery.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'violation-nav-release');out=copy.deepcopy(codes);by={r['path']:r for r in out}
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'violation-nav-source-before');o.raw(t['before']);o.raw(t['after']);out[out.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in out:o.raw(r)
    return out

def _nav_contract_facts(parent,engine,worker_ref,switch_proof_ref):
    previous,prior,codes=_nav_contract_prior(parent);folder=o.location(parent['order']);order=o.doc(parent['order']);o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==3 and all(c['state']=='returned'for c in parent['calls']),'violation-nav-parent-hold');call=parent['calls'][-1];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(call['launch']['path']==str(folder/'children/0002-launch.json')and call['result']['path']==str(folder/'children/0002-exit.json')and call['argv']==parent['calls'][1]['argv']==la['argv']==ex['argv']and la['order']==parent['order']and la['index']==2 and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':NAV_CONTRACT_ERROR}and o.doc(parent['calls'][1]['result'])['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-nav-natural-child')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==NAV_CONTRACT_ERROR and engine['phase']=='company'and engine['index']==0 and len(engine['calls'])>=2,'violation-nav-engine-hold');failed=engine['calls'][-1];o.need(failed['state']=='failed'and failed['step']=='company'and failed['company_index']==0 and failed['error']==NAV_CONTRACT_ERROR and 'result'not in failed and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:-1]),'violation-nav-engine-failed-call');o.need(failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['folder']==str(folder/'companies/0')and failed['context']['artifacts']==engine['companies'][0]['artifacts'],'violation-nav-engine-context')
    original_call=copy.deepcopy(engine['calls'][0]);original_call.pop('applied',None);o.need(original_call==_local_plan_engine(o.doc(prior['engine_archive']),previous,prior)['calls'][0]and engine.get('local_plan_result_recovery')==previous,'violation-nav-local-plan-prefix')
    import switch_read_recovery as switch
    sp=o.doc(switch_proof_ref);original=o.doc(sp['original_journal']);job=o.doc(sp['job']);o.need(sp['job']['sha256']==o.ref(Path(job['work_order_path']))['sha256']and job['workflow_path']==str(folder/'companies/0/company-navigation/workflow.json')and job['source_identity_context']==failed['context']['artifacts']['identity_receipt']and original['last_error']['code']==original['last_error']['message']==NAV_CONTRACT_ERROR and original['phase']=='verifySwitch'and len(original['calls'])==5 and all(c['state']=='confirmed'for c in original['calls'])and original['date_range']=={},'violation-nav-switch-original');switch.contract(job,original)
    # Validate the exact immutable switch delta; the live journal may later progress.
    expected=copy.deepcopy(original);expected.setdefault('resolved_errors',[]).append({**expected.pop('last_error'),'resolved_at':sp['at'],'next_phase':'accountAfterSwitch','recovery_proof':switch_proof_ref});expected.update(phase='accountAfterSwitch',revision=original['revision']+1,last_tree=switch.ref(Path(sp['sample']['path']).with_name(Path(sp['sample']['path']).name.replace('-sample.json','-tree.json'))),switch_read_recovery=switch_proof_ref,updated_at=sp['at']);expected.pop('waiting_for',None);expected.pop('company_switch_wait_started',None);switch.verify_recovered(expected,switch_proof_ref)
    current=o.doc(o.ref(Path(job['workflow_path'])));o.need(current['calls'][:len(original['calls'])]==original['calls']and current.get('switch_read_recovery')==switch_proof_ref and current['fingerprint']==original['fingerprint']and current['date_range']=={}and not any(c['state']=='unknown'for c in current['calls']),'violation-nav-live-WF-prefix')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;old_request=o.doc(o.doc(prior['worker'])['request']);pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));expected_argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(worker['returncode']==0 and request['task']['id']==old_request['task']['id']and request['task']['outer']==old_request['task']['outer']and request['task']['flow']==o.FLOW and request['context']['order']==response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['attempt_id']==request['attempt_id']==request['task']['id']+'-'+str(int(old_request['attempt_id'].rsplit('-',1)[1])+1)and pe['returncode']==0 and pe['argv']==expected_argv and not o.raw(pe['stderr'])and out['status']=='hold'and out['last_child_receipt']==call['result']and o.doc(request['config_ref'])==request['config']and request['config']['python']==expected_argv[0]and request['config']['project']==str(o.PROJECT),'violation-nav-natural-worker');evidence=[worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr']];return {'order':order,'previous_proof':previous,'previous_codes':codes,'failed_engine_call':failed,'switch_proof':switch_proof_ref,'workflow_original':sp['original_journal'],'workflow_calls':original['calls'],'job':sp['job'],'evidence':evidence}

def _nav_contract_parent(before,pr):
    value=copy.deepcopy(before);value.update(status='running',**{FIELD:pr});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':NAV_CONTRACT_ERROR,'recovery':pr});return value

def _nav_contract_engine(before,pr):
    value=copy.deepcopy(before);index=len(value['calls'])-1;failed=value['calls'].pop();value.update(status='running');value.pop('error');value.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':pr});return value

def plan_navigation_contract(parent_ref,engine_ref,worker_ref,release_ref,switch_proof_ref,*,installed=True):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'violation-nav-path');facts=_nav_contract_facts(parent,engine,worker_ref,switch_proof_ref);codes=_nav_contract_sources(facts['previous_codes'],release_ref,installed);live_lease(facts['order']);return {'kind':NAV_CONTRACT_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'switch_proof':switch_proof_ref,'facts':facts,'code_refs':codes,'at':stamp(),'ui_used':False}

def verify_navigation_contract(current,proof_ref,*,installed=True):
    proof=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-navigation-contract-recovery'/proof['original_parent']['sha256'];o.need(proof['kind']==NAV_CONTRACT_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and proof['parent_archive']['sha256']==proof['original_parent']['sha256']and proof['engine_archive']['sha256']==proof['original_engine']['sha256'],'violation-nav-proof');parent=o.doc(proof['parent_archive']);engine=o.doc(proof['engine_archive']);facts=_nav_contract_facts(parent,engine,proof['worker'],proof['switch_proof']);codes=_nav_contract_sources(facts['previous_codes'],proof['release'],installed);o.need(facts==proof['facts']and codes==proof['code_refs'],'violation-nav-derived');expected=_nav_contract_parent(parent,proof_ref);o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'violation-nav-parent-prefix');live=o.doc(o.ref(folder/'engine.json'));want=_nav_contract_engine(engine,proof_ref);o.need(live['calls'][:len(want['calls'])]==want['calls']and live.get('resolved_readonly_failures',[])[:len(want['resolved_readonly_failures'])]==want['resolved_readonly_failures']and live['order']==parent['order'],'violation-nav-engine-prefix');return {'kind':NAV_CONTRACT_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,proof['parent_archive'],proof['engine_archive'],proof['release'],proof['switch_proof'],*facts['evidence']]}

_NAV_CONTRACT_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==NAV_CONTRACT_KIND:return verify_navigation_contract(current,proof_ref,installed=kwargs.get('installed',True))
    return _NAV_CONTRACT_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_navigation_contract(parent_ref,engine_ref,worker_ref,release_ref,switch_proof_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-navigation-contract-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            pr=o.ref(base/'proof.json');proof=o.doc(pr);o.need((proof['original_parent'],proof['original_engine'],proof['worker'],proof['release'],proof['switch_proof'])==(parent_ref,engine_ref,worker_ref,release_ref,switch_proof_ref),'violation-nav-same-intent')
        else:
            proof=plan_navigation_contract(parent_ref,engine_ref,worker_ref,release_ref,switch_proof_ref);proof['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));proof['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));pr=o.immutable(base/'proof.json',proof);checkpoint('proof-published')
        parent=o.doc(proof['parent_archive']);engine=o.doc(proof['engine_archive']);cp=o.doc(o.ref(folder/'launcher.json'));ce=o.doc(o.ref(folder/'engine.json'));ep=_nav_contract_parent(parent,pr);ee=_nav_contract_engine(engine,pr);o.need(cp in(parent,ep)and ce in(engine,ee),'violation-nav-CAS-frontier');facts=_nav_contract_facts(parent,engine,worker_ref,switch_proof_ref);codes=_nav_contract_sources(facts['previous_codes'],release_ref,True);o.need(proof['kind']==NAV_CONTRACT_KIND and facts==proof['facts']and codes==proof['code_refs'],'violation-nav-CAS-derived');live_lease(facts['order'])
        if ce==engine:
            from violation_execution import atomic
            atomic(folder/'engine.json',ee);checkpoint('engine-CAS')
        verify_navigation_contract(ep,pr)
        if cp==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',ep)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':pr,'ui_used':False}

# Known no-input layout admission failure; the original manifest is resumed.
LAYOUT_BUILD_KIND='verified-violation-layout-build-successor-recovery-v1'
LAYOUT_BUILD_ERROR='layout-reviewed-hotbuild-required'
def _layout_build_prior(parent):
    previous=parent[FIELD];p=o.doc(previous);folder=o.location(parent['order']);o.need(p['kind']==NAV_CONTRACT_KIND and previous['path']==str(folder/'.violation-navigation-contract-recovery'/p['original_parent']['sha256']/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256'],'violation-layout-prior-proof');before=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts=_nav_contract_facts(before,engine,p['worker'],p['switch_proof']);o.need(facts==p['facts'],'violation-layout-prior-facts');codes=copy.deepcopy(facts['previous_codes']);by={r['path']:r for r in codes};release=o.doc(p['release']);wanted={str(o.PROJECT/r)for r in('skills/douyin-laike-operator/scripts/switch_read_recovery.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'violation-layout-prior-release')
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'violation-layout-prior-source');o.raw(t['before']);o.raw(t['after']);codes[codes.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    expected=_nav_contract_parent(before,previous);o.need(codes==p['code_refs']and parent['calls'][:len(before['calls'])]==before['calls']and parent['code_refs']==before['code_refs']and parent.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(before['origin_ref']).items()),'violation-layout-prior-history');return previous,p,codes

def _layout_build_sources(codes,release_ref,installed):
    release=o.doc(release_ref);wanted={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('center_legacy_layout.py','center_analysis_tab.py','bridge-profile-discovery.py','violation_initial_ledger_recovery.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==wanted,'violation-layout-five-sources');out=copy.deepcopy(codes);by={r['path']:r for r in out}
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'violation-layout-source-before');o.raw(t['before']);o.raw(t['after']);out[out.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in out:o.raw(r)
    return out

def _layout_build_facts(parent,engine,worker_ref,query_ref,adapter_ref):
    previous,prior,codes=_layout_build_prior(parent);folder=o.location(parent['order']);order=o.doc(parent['order']);o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==4 and all(c['state']=='returned'for c in parent['calls']),'violation-layout-parent');call=parent['calls'][-1];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(call['launch']['path']==str(folder/'children/0003-launch.json')and call['result']['path']==str(folder/'children/0003-exit.json')and call['argv']==parent['calls'][-2]['argv']==la['argv']==ex['argv']and la['order']==parent['order']and la['index']==3 and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':LAYOUT_BUILD_ERROR}and o.doc(parent['calls'][-2]['result'])['exited_monotonic']<=la['launched_monotonic']<=ex['exited_monotonic'],'violation-layout-natural-child')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==LAYOUT_BUILD_ERROR and engine['phase']=='center-query'and engine['index']==0 and len(engine['calls'])>=2,'violation-layout-engine');failed=engine['calls'][-1];o.need(failed['state']=='failed'and failed['step']=='center-query'and failed['company_index']==0 and failed['error']==LAYOUT_BUILD_ERROR and 'result'not in failed and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:-1])and failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['folder']==str(folder/'companies/0')and failed['context']['artifacts']==engine['companies'][0]['artifacts'],'violation-layout-failed-call');prefix=_nav_contract_engine(o.doc(prior['engine_archive']),previous);o.need(engine['calls'][:len(prefix['calls'])]==prefix['calls']and engine.get('resolved_readonly_failures',[])[:len(prefix['resolved_readonly_failures'])]==prefix['resolved_readonly_failures'],'violation-layout-engine-prior-prefix')
    query=o.doc(query_ref);adapter=o.doc(adapter_ref);pre=query.get('analysis_preflight',{});manifest=o.doc(pre['manifest']);job=o.doc(manifest['job']);expected_query=folder/'companies/0/center-query.json';expected_adapter=folder/'companies/0/.center-analysis-tab'/query['fingerprint']/'state.json';o.need(query['phase']=='open-date'and query['calls']==[]and query['pages']==[]and query['business_progress_changed']is False and query['profile_accepted']is False and query['last_observation']==pre['before']and pre['state']=='original-adapter-bound-before-run'and pre['job']==manifest['job']==failed['context']['artifacts']['job']and manifest['kind']=='center-analysis-display-tab-navigation-v1'and manifest['state_path']==str(expected_adapter)and query['query_job_binding']['query_state_path']==str(expected_query)and query['query_job_binding']['job']==manifest['job'],'violation-layout-original-query');o.need(adapter['manifest']==pre['manifest']and adapter['phase']=='prepared'and not adapter.get('intent')and not adapter.get('calls')and adapter['dates_queried']is False and adapter['business_progress_changed']is False and adapter['profile_accepted']is False,'violation-layout-no-input-adapter')
    from center_analysis_tab import target
    from dom_evidence import context,identity
    obs=o.doc(pre['before']);o.need(obs['source']=='local-dom-bridge'and obs['tab_id']==parent['tab_id']==manifest['tab_id']and obs['tab']['windowId']==manifest['window_id']==query['query_job_binding']['window_id'],'violation-layout-observed-tab');context([{'tabs':[obs['tab']]}],parent['tab_id'],job['groupid']);identity(obs['tree'],job['identity']);target(obs['tree']);o.need(query['fingerprint']==query['query_job_binding']['fingerprint']==__import__('violation_execution_ports').nav.tag(job),'violation-layout-query-fingerprint')
    for r in [pre['manifest'],pre['before'],*adapter['observations']]:o.raw(r)
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);old_request=o.doc(o.doc(prior['worker'])['request']);attempt=Path(worker_ref['path']).parent;pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(worker['returncode']==0 and request['task']['id']==old_request['task']['id']and request['task']['outer']==old_request['task']['outer']and request['context']['order']==response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['attempt_id']==request['attempt_id']==request['task']['id']+'-'+str(int(old_request['attempt_id'].rsplit('-',1)[1])+1)and pe['returncode']==0 and pe['argv']==argv and not o.raw(pe['stderr'])and out['last_child_receipt']==call['result']and o.doc(request['config_ref'])==request['config']and request['config']['python']==argv[0],'violation-layout-worker')
    return {'order':order,'previous_proof':previous,'previous_codes':codes,'failed_call':failed,'query_original':query_ref,'adapter_original':adapter_ref,'query_path':str(expected_query),'adapter_path':str(expected_adapter),'manifest':pre['manifest'],'evidence':[worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr'],call['launch'],call['result']]}

def _layout_build_parent(before,pr):
    value=copy.deepcopy(before);value.update(status='running',**{FIELD:pr});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':LAYOUT_BUILD_ERROR,'recovery':pr});return value

def _layout_build_engine(before,pr):
    value=copy.deepcopy(before);index=len(value['calls'])-1;failed=value['calls'].pop();value.update(status='running');value.pop('error');value.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':pr});return value

def plan_layout_build(parent_ref,engine_ref,worker_ref,release_ref,*,installed=True):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);query_ref=o.ref(folder/'companies/0/center-query.json');query=o.doc(query_ref);adapter_ref=o.ref(Path(o.doc(query['analysis_preflight']['manifest'])['state_path']));o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'violation-layout-path');facts=_layout_build_facts(parent,engine,worker_ref,query_ref,adapter_ref);codes=_layout_build_sources(facts['previous_codes'],release_ref,installed);live_lease(facts['order']);return {'kind':LAYOUT_BUILD_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'at':stamp(),'ui_used':False}

def _layout_build_check(parent,engine,proof):
    facts=_layout_build_facts(parent,engine,proof['worker'],proof['query_archive'],proof['adapter_archive']);facts['query_original']=proof['facts']['query_original'];facts['adapter_original']=proof['facts']['adapter_original'];o.need(proof['query_archive']['sha256']==facts['query_original']['sha256']and proof['adapter_archive']['sha256']==facts['adapter_original']['sha256'],'violation-layout-query-archives');codes=_layout_build_sources(facts['previous_codes'],proof['release'],True);o.need(proof['kind']==LAYOUT_BUILD_KIND and facts==proof['facts']and codes==proof['code_refs'],'violation-layout-derived');liveq=o.doc(o.ref(Path(facts['query_path'])));livea=o.doc(o.ref(Path(facts['adapter_path'])));o.need(liveq['fingerprint']==o.doc(proof['query_archive'])['fingerprint']and not any(c.get('state')=='unknown'for c in liveq['calls'])and livea['manifest']==facts['manifest']and livea.get('intent',{}).get('state')!='unknown','violation-layout-live-prefix');return facts,codes

def verify_layout_build(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-layout-build-recovery'/p['original_parent']['sha256'];o.need(p['kind']==LAYOUT_BUILD_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256'],'violation-layout-proof');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=_layout_build_check(parent,engine,p);expected=_layout_build_parent(parent,proof_ref);o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'violation-layout-parent-prefix');live=o.doc(o.ref(folder/'engine.json'));want=_layout_build_engine(engine,proof_ref);o.need(live['calls'][:len(want['calls'])]==want['calls']and live.get('resolved_readonly_failures',[])[:len(want['resolved_readonly_failures'])]==want['resolved_readonly_failures']and live['order']==parent['order'],'violation-layout-engine-prefix');return {'kind':LAYOUT_BUILD_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['query_archive'],p['adapter_archive'],p['release'],*facts['evidence']]}

_LAYOUT_BUILD_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==LAYOUT_BUILD_KIND:return verify_layout_build(current,proof_ref,installed=kwargs.get('installed',True))
    return _LAYOUT_BUILD_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_layout_build(parent_ref,engine_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-layout-build-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            pr=o.ref(base/'proof.json');p=o.doc(pr);o.need((p['original_parent'],p['original_engine'],p['worker'],p['release'])==(parent_ref,engine_ref,worker_ref,release_ref),'violation-layout-same-intent')
        else:
            p=plan_layout_build(parent_ref,engine_ref,worker_ref,release_ref);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));p['query_archive']=immutable_bytes(base/'original-query.json',o.raw(p['facts']['query_original']));p['adapter_archive']=immutable_bytes(base/'original-adapter.json',o.raw(p['facts']['adapter_original']));pr=o.immutable(base/'proof.json',p);checkpoint('proof-published')
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);ep=_layout_build_parent(parent,pr);ee=_layout_build_engine(engine,pr);cp=o.doc(o.ref(folder/'launcher.json'));ce=o.doc(o.ref(folder/'engine.json'));o.need(cp in(parent,ep)and ce in(engine,ee),'violation-layout-CAS-frontier');_layout_build_check(parent,engine,p);live_lease(p['facts']['order'])
        if ce==engine:
            o.need(o.ref(Path(p['facts']['query_path']))==p['facts']['query_original']and o.ref(Path(p['facts']['adapter_path']))==p['facts']['adapter_original'],'violation-layout-preCAS-original-query');from violation_execution import atomic;atomic(folder/'engine.json',ee);checkpoint('engine-CAS')
        verify_layout_build(ep,pr)
        if cp==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',ep)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':pr,'ui_used':False}

# The original analysis display click is complete; only the read-wait consumer failed.
ANALYSIS_ANCHOR_KIND='verified-violation-analysis-wait-anchor-recovery-v1'
ANALYSIS_ANCHOR_ERROR='execution-analysis-wait-canonical-adapter'
def _analysis_anchor_prior(parent):
    previous=parent[FIELD];p=o.doc(previous);folder=o.location(parent['order']);o.need(p['kind']==LAYOUT_BUILD_KIND and previous['path']==str(folder/'.violation-layout-build-recovery'/p['original_parent']['sha256']/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256'],'analysis-anchor-prior');before=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts=_layout_build_facts(before,engine,p['worker'],p['query_archive'],p['adapter_archive']);facts['query_original']=p['facts']['query_original'];facts['adapter_original']=p['facts']['adapter_original'];o.need(facts==p['facts']and p['query_archive']['sha256']==facts['query_original']['sha256']and p['adapter_archive']['sha256']==facts['adapter_original']['sha256'],'analysis-anchor-prior-facts');codes=copy.deepcopy(facts['previous_codes']);by={r['path']:r for r in codes};release=o.doc(p['release']);wanted={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('center_legacy_layout.py','center_analysis_tab.py','bridge-profile-discovery.py','violation_initial_ledger_recovery.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==wanted,'analysis-anchor-prior-release')
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'analysis-anchor-prior-source');o.raw(t['before']);o.raw(t['after']);codes[codes.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    expected=_layout_build_parent(before,previous);o.need(codes==p['code_refs']and parent['calls'][:len(before['calls'])]==before['calls']and parent['code_refs']==before['code_refs']and parent.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(before['origin_ref']).items()),'analysis-anchor-prior-history');return previous,p,codes

def _analysis_anchor_sources(codes,release_ref):
    release=o.doc(release_ref);wanted={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_execution_ports.py','violation_initial_ledger_recovery.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'analysis-anchor-three-sources');out=copy.deepcopy(codes);by={r['path']:r for r in out}
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'analysis-anchor-source-before');o.raw(t['before']);o.raw(t['after']);out[out.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    for r in out:o.raw(r)
    return out

def _analysis_anchor_facts(parent,engine,worker_ref,query_ref,adapter_ref):
    previous,prior,codes=_analysis_anchor_prior(parent);folder=o.location(parent['order']);order=o.doc(parent['order']);o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==5 and all(c['state']=='returned'for c in parent['calls']),'analysis-anchor-parent');call=parent['calls'][-1];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(call['launch']['path']==str(folder/'children/0004-launch.json')and call['result']['path']==str(folder/'children/0004-exit.json')and call['argv']==parent['calls'][-2]['argv']==la['argv']==ex['argv']and la['order']==parent['order']and la['index']==4 and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':ANALYSIS_ANCHOR_ERROR},'analysis-anchor-natural-child')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==ANALYSIS_ANCHOR_ERROR and engine['phase']=='center-query'and engine['index']==0,'analysis-anchor-engine');failed=engine['calls'][-1];o.need(failed['state']=='failed'and failed['step']=='center-query'and failed['company_index']==0 and failed['error']==ANALYSIS_ANCHOR_ERROR and 'result'not in failed and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:-1])and failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['artifacts']==engine['companies'][0]['artifacts'],'analysis-anchor-failed-call');prefix=_layout_build_engine(o.doc(prior['engine_archive']),previous);o.need(engine['calls'][:len(prefix['calls'])]==prefix['calls']and engine.get('resolved_readonly_failures',[])[:len(prefix['resolved_readonly_failures'])]==prefix['resolved_readonly_failures'],'analysis-anchor-engine-prefix')
    query=o.doc(query_ref);adapter=o.doc(adapter_ref);job_ref=failed['context']['artifacts']['job'];job=o.doc(job_ref);path=folder/'companies/0/center-query.json';from violation_execution_ports import validate_analysis_fresh_wait
    checked=validate_analysis_fresh_wait(query,job,job_ref,path,parent['tab_id'],adapter_archive=adapter_ref);o.need(adapter_ref['sha256']==query['analysis_preflight']['adapter_state']['sha256'],'analysis-anchor-adapter-exact')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);old_request=o.doc(o.doc(prior['worker'])['request']);attempt=Path(worker_ref['path']).parent;pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(worker['returncode']==0 and request['task']['id']==old_request['task']['id']and request['task']['outer']==old_request['task']['outer']and request['context']['order']==response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['attempt_id']==request['attempt_id']==request['task']['id']+'-'+str(int(old_request['attempt_id'].rsplit('-',1)[1])+1)and pe['returncode']==0 and pe['argv']==argv and not o.raw(pe['stderr'])and out['last_child_receipt']==call['result']and o.doc(request['config_ref'])==request['config'],'analysis-anchor-worker');return {'order':order,'previous_proof':previous,'previous_codes':codes,'failed_call':failed,'query_original':query_ref,'adapter_original':adapter_ref,'query_path':str(path),'adapter_path':query['analysis_preflight']['adapter_state']['path'],'wait':checked,'evidence':[worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr'],call['launch'],call['result']]}

def _analysis_anchor_parent(before,pr):
    value=copy.deepcopy(before);value.update(status='running',**{FIELD:pr});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':ANALYSIS_ANCHOR_ERROR,'recovery':pr});return value

def _analysis_anchor_engine(before,pr):
    value=copy.deepcopy(before);index=len(value['calls'])-1;failed=value['calls'].pop();value.update(status='running');value.pop('error');value.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':pr});return value

def plan_analysis_anchor(parent_ref,engine_ref,worker_ref,release_ref):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);q=o.ref(folder/'companies/0/center-query.json');a=o.doc(q)['analysis_preflight']['adapter_state'];o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'analysis-anchor-path');facts=_analysis_anchor_facts(parent,engine,worker_ref,q,a);codes=_analysis_anchor_sources(facts['previous_codes'],release_ref);live_lease(facts['order']);return {'kind':ANALYSIS_ANCHOR_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'at':stamp(),'ui_used':False}

def _analysis_anchor_check(parent,engine,p):
    facts=_analysis_anchor_facts(parent,engine,p['worker'],p['query_archive'],p['adapter_archive']);facts['query_original']=p['facts']['query_original'];facts['adapter_original']=p['facts']['adapter_original'];o.need(p['query_archive']['sha256']==facts['query_original']['sha256']and p['adapter_archive']['sha256']==facts['adapter_original']['sha256'],'analysis-anchor-archives');codes=_analysis_anchor_sources(facts['previous_codes'],p['release']);o.need(p['kind']==ANALYSIS_ANCHOR_KIND and p['ui_used']is False and facts==p['facts']and codes==p['code_refs'],'analysis-anchor-derived');q=o.doc(o.ref(Path(facts['query_path'])));a=o.doc(o.ref(Path(facts['adapter_path'])));o.need(q['fingerprint']==o.doc(p['query_archive'])['fingerprint']and not any(c.get('state')=='unknown'for c in q['calls'])and a['manifest']==facts['wait']['manifest']and a.get('intent',{}).get('state')=='confirmed','analysis-anchor-live-prefix');return facts,codes

def verify_analysis_anchor(current,proof_ref):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-analysis-wait-anchor-recovery'/p['original_parent']['sha256'];o.need(p['kind']==ANALYSIS_ANCHOR_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256'],'analysis-anchor-proof');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=_analysis_anchor_check(parent,engine,p);expected=_analysis_anchor_parent(parent,proof_ref);o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'analysis-anchor-parent-prefix');live=o.doc(o.ref(folder/'engine.json'));want=_analysis_anchor_engine(engine,proof_ref);o.need(live['calls'][:len(want['calls'])]==want['calls']and live.get('resolved_readonly_failures',[])[:len(want['resolved_readonly_failures'])]==want['resolved_readonly_failures'],'analysis-anchor-engine-history');return {'kind':ANALYSIS_ANCHOR_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['query_archive'],p['adapter_archive'],p['release'],*facts['evidence']]}

_ANALYSIS_ANCHOR_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==ANALYSIS_ANCHOR_KIND:return verify_analysis_anchor(current,proof_ref)
    return _ANALYSIS_ANCHOR_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_analysis_anchor(parent_ref,engine_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-analysis-wait-anchor-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            pr=o.ref(base/'proof.json');p=o.doc(pr);o.need((p['original_parent'],p['original_engine'],p['worker'],p['release'])==(parent_ref,engine_ref,worker_ref,release_ref),'analysis-anchor-same-intent')
        else:
            p=plan_analysis_anchor(parent_ref,engine_ref,worker_ref,release_ref);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));p['query_archive']=immutable_bytes(base/'original-query.json',o.raw(p['facts']['query_original']));p['adapter_archive']=immutable_bytes(base/'original-adapter.json',o.raw(p['facts']['adapter_original']));pr=o.immutable(base/'proof.json',p);checkpoint('proof-published')
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);ep=_analysis_anchor_parent(parent,pr);ee=_analysis_anchor_engine(engine,pr);cp=o.doc(o.ref(folder/'launcher.json'));ce=o.doc(o.ref(folder/'engine.json'));o.need(cp in(parent,ep)and ce in(engine,ee),'analysis-anchor-CAS-frontier');_analysis_anchor_check(parent,engine,p);live_lease(p['facts']['order'])
        if ce==engine:
            o.need(o.ref(Path(p['facts']['query_path']))==p['facts']['query_original']and o.ref(Path(p['facts']['adapter_path']))==p['facts']['adapter_original'],'analysis-anchor-preCAS-query');from violation_execution import atomic;atomic(folder/'engine.json',ee);checkpoint('engine-CAS')
        verify_analysis_anchor(ep,pr)
        if cp==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',ep)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':pr,'ui_used':False}

# Accept the already-written source only after its existing public verifier passes.
SOURCE_REF_KIND='verified-violation-saved-source-result-recovery-v1'
SOURCE_REF_ERROR='execution-reference-shape'
def _source_ref_prior(parent):
    previous=parent[FIELD];p=o.doc(previous);folder=o.location(parent['order']);o.need(p['kind']==ANALYSIS_ANCHOR_KIND and previous['path']==str(folder/'.violation-analysis-wait-anchor-recovery'/p['original_parent']['sha256']/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256']and p['ui_used']is False,'source-ref-prior-proof');before=o.doc(p['parent_archive']);expected=_analysis_anchor_parent(before,previous);o.need(parent['calls'][:len(before['calls'])]==before['calls']and parent['code_refs']==before['code_refs']and parent.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(before['origin_ref']).items()),'source-ref-prior-history');codes=copy.deepcopy(p['facts']['previous_codes']);by={r['path']:r for r in codes};release=o.doc(p['release']);wanted={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_execution_ports.py','violation_initial_ledger_recovery.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'source-ref-prior-release')
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'source-ref-prior-source');o.raw(t['before']);o.raw(t['after']);codes[codes.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    o.need(codes==p['code_refs']and p['facts']['order']==o.doc(parent['order']),'source-ref-prior-vector')
    for r in [p['facts']['previous_proof'],p['query_archive'],p['adapter_archive'],*p['facts']['evidence']]:o.raw(r)
    return previous,p,codes

def _source_ref_sources(codes,release_ref):
    release=o.doc(release_ref);wanted={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('bridge-navigation.py','violation_initial_ledger_recovery.py')}|{str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==3 and {t['target']for t in release['targets']}==wanted,'source-ref-three-sources');out=copy.deepcopy(codes);by={r['path']:r for r in out}
    for t in release['targets']:
        o.need(t['before']['sha256']==t['old_sha256']==by[t['target']]['sha256']and t['mode']==420,'source-ref-source-before');o.raw(t['before']);o.raw(t['after']);out[out.index(by[t['target']])]={'path':t['target'],'sha256':t['after']['sha256']}
    for r in out:o.raw(r)
    return out

def _source_ref_facts(parent,engine,worker_ref):
    previous,prior,codes=_source_ref_prior(parent);folder=o.location(parent['order']);order=o.doc(parent['order']);count=len(o.doc(prior['parent_archive'])['calls'])+1;o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==count and all(c['state']=='returned'for c in parent['calls']),'source-ref-parent');call=parent['calls'][-1];la=o.doc(call['launch']);ex=o.doc(call['result']);o.need(call['launch']['path']==str(folder/'children'/(str(count-1).zfill(4)+'-launch.json'))and call['result']['path']==str(folder/'children'/(str(count-1).zfill(4)+'-exit.json'))and call['argv']==parent['calls'][-2]['argv']==la['argv']==ex['argv']and la['order']==parent['order']and la['index']==count-1 and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':SOURCE_REF_ERROR},'source-ref-natural-child')
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==SOURCE_REF_ERROR and engine['phase']=='source'and engine['index']==0,'source-ref-engine');failed=engine['calls'][-1];o.need(failed['state']=='failed'and failed['step']=='source'and failed['company_index']==0 and failed['error']==SOURCE_REF_ERROR and 'result'not in failed and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:-1])and failed['context']['order']==order and failed['context']['company']==order['companies'][0]and failed['context']['artifacts']==engine['companies'][0]['artifacts'],'source-ref-failed-call');prefix=_analysis_anchor_engine(o.doc(prior['engine_archive']),previous);o.need(engine['calls'][:len(prefix['calls'])]==prefix['calls']and engine.get('resolved_readonly_failures',[])[:len(prefix['resolved_readonly_failures'])]==prefix['resolved_readonly_failures'],'source-ref-engine-prefix')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);old_request=o.doc(o.doc(prior['worker'])['request']);attempt=Path(worker_ref['path']).parent;pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);out=json.loads(o.raw(pe['stdout']));argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000'];o.need(worker['returncode']==0 and request['task']['id']==old_request['task']['id']and request['task']['outer']==old_request['task']['outer']and request['context']['order']==response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and response['attempt_id']==request['attempt_id']==request['task']['id']+'-'+str(int(old_request['attempt_id'].rsplit('-',1)[1])+1)and pe['returncode']==0 and pe['argv']==argv and not o.raw(pe['stderr'])and out['last_child_receipt']==call['result']and o.doc(request['config_ref'])==request['config'],'source-ref-worker');return {'order':order,'previous_proof':previous,'previous_codes':codes,'failed_call':failed,'evidence':[worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr'],call['launch'],call['result']]}

def _source_ref_value(parent,engine):
    import governance_capture as capture
    folder=o.location(parent['order'])/'companies/0';art=engine['calls'][-1]['context']['artifacts'];source=o.ref(folder/'source.json');value=capture.validate(source['path']);manifest=o.ref(folder/'capture-manifest.json');m=o.doc(manifest);c=o.doc(parent['order'])['companies'][0];o.need(value['capture_manifest']==manifest and (value['company'],str(value['groupid']),value['start'],value['end_exclusive'])==(c['company'],c['groupid'],c['start'],c['end_exclusive']),'source-ref-source-scope')
    if m['kind']=='governance-zero-capture-manifest-v1':
        expected={'job':art['job'],'center_query':art['center_query_final'],'records_query':art['query_final'],'center_pages':o.ref(folder/'center-pages.json'),'center_observation':art['center_pages'][0],'profile':o.ref(folder/'zero-profile.json')};o.need(art['center_zero']is True and len(art['center_pages'])==1 and value['analysis']['total']==value['records']['total']==0,'source-ref-zero-derivation')
    else:expected={'job':art['job'],'query':art['query_final'],'detail_manifest':art['detail_manifest'],'detail_state':art['detail_state'],'center_pages':art['center_pages']}
    o.need(m['inputs']==expected,'source-ref-original-producer-inputs');return {'done':True,'artifacts':{'source':source,'total':value['records']['total']}}

def _source_ref_parent(before,pr):
    value=copy.deepcopy(before);value.update(status='running',**{FIELD:pr});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':SOURCE_REF_ERROR,'recovery':pr,'result_kind':'existing-source-result-reconciled-not-original-child-success'});return value

def _source_ref_engine(before,pr,p):
    value=copy.deepcopy(before);call=value['calls'][-1];call.update(state='returned',result=p['local_result'],returned_at=p['at'],local_result_reconciliation={'proof':pr,'original_failed_call':copy.deepcopy(before['calls'][-1])});value.update(status='running',source_result_recovery=pr);value.pop('error');return value

def plan_source_reference(parent_ref,engine_ref,worker_ref,release_ref):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'source-ref-path');facts=_source_ref_facts(parent,engine,worker_ref);codes=_source_ref_sources(facts['previous_codes'],release_ref);live_lease(facts['order']);result=_source_ref_value(parent,engine);local=o.immutable(folder/'receipts'/(str(len(engine['calls'])).zfill(5)+'.json'),result);return {'kind':SOURCE_REF_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'local_result':local,'at':stamp(),'ui_used':False}

def _source_ref_check(parent,engine,p):
    facts=_source_ref_facts(parent,engine,p['worker']);codes=_source_ref_sources(facts['previous_codes'],p['release']);o.need(p['kind']==SOURCE_REF_KIND and p['ui_used']is False and facts==p['facts']and codes==p['code_refs'],'source-ref-derived');o.need(p['local_result']['path']==str(o.location(parent['order'])/'receipts'/(str(len(engine['calls'])).zfill(5)+'.json'))and o.doc(p['local_result'])==_source_ref_value(parent,engine),'source-ref-local-result');return facts,codes

def verify_source_reference(current,proof_ref):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-source-reference-recovery'/p['original_parent']['sha256'];o.need(p['kind']==SOURCE_REF_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256'],'source-ref-proof');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts,codes=_source_ref_check(parent,engine,p);expected=_source_ref_parent(parent,proof_ref);o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'source-ref-parent-prefix');live=o.doc(o.ref(folder/'engine.json'));want=_source_ref_engine(engine,proof_ref,p);prefix=copy.deepcopy(live['calls'][:len(want['calls'])]);prefix[-1].pop('applied',None);o.need(prefix==want['calls']and live.get('source_result_recovery')==proof_ref and live['order']==parent['order'],'source-ref-engine-prefix');return {'kind':SOURCE_REF_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['release'],p['local_result'],*facts['evidence']]}

_SOURCE_REF_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==SOURCE_REF_KIND:return verify_source_reference(current,proof_ref)
    return _SOURCE_REF_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_source_reference(parent_ref,engine_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-source-reference-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            pr=o.ref(base/'proof.json');p=o.doc(pr);o.need((p['original_parent'],p['original_engine'],p['worker'],p['release'])==(parent_ref,engine_ref,worker_ref,release_ref),'source-ref-same-intent')
        else:
            p=plan_source_reference(parent_ref,engine_ref,worker_ref,release_ref);p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));pr=o.immutable(base/'proof.json',p);checkpoint('proof-published')
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);ep=_source_ref_parent(parent,pr);ee=_source_ref_engine(engine,pr,p);cp=o.doc(o.ref(folder/'launcher.json'));ce=o.doc(o.ref(folder/'engine.json'));o.need(cp in(parent,ep)and ce in(engine,ee),'source-ref-CAS-frontier');_source_ref_check(parent,engine,p);live_lease(p['facts']['order'])
        if ce==engine:
            from violation_execution import atomic
            atomic(folder/'engine.json',ee);checkpoint('engine-CAS')
        verify_source_reference(ep,pr)
        if cp==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',ep)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':pr,'ui_used':False,'source_rebuilt':False}

# Exact already-executed VI8 local entry failure. Inherit the fixed prior
# successful source admission, never consume its source call for a second time.
GOVERNANCE_ENTRY_KIND='verified-violation-governance-entry-result-recovery-v1'
GOVERNANCE_ENTRY_ERROR='company-entry-reviewed-route'
GOVERNANCE_ENTRY_PRIOR_SHA='c14157c1a8680b3577ea939fbe13de2081384df8982b9146d72d5992018fe3ef'
GOVERNANCE_ENTRY_PARENT_SHA='dd7a4f22356410f3969206fb8a7e20c9c1ae0e146f3ef034a478518e1d483f84'
GOVERNANCE_ENTRY_ENGINE_SHA='74b9da8c95562a6b201ca7833a066e10b3f23b1164c52958e1d45a17685d01d3'

def _governance_entry_facts(parent,engine,worker_ref,*,workflow_ref=None,workflow_archive=None):
    o.need(hashlib.sha256(o.encode(parent)).hexdigest()==GOVERNANCE_ENTRY_PARENT_SHA and hashlib.sha256(o.encode(engine)).hexdigest()==GOVERNANCE_ENTRY_ENGINE_SHA,'governance-entry-exact-saved-frontier')
    folder=o.location(parent['order']);order=o.doc(parent['order']);previous=parent[FIELD];prior=o.doc(previous)
    o.need(previous['sha256']==GOVERNANCE_ENTRY_PRIOR_SHA and prior['kind']==SOURCE_REF_KIND and prior['ui_used']is False and prior['parent_archive']['sha256']==prior['original_parent']['sha256']and prior['engine_archive']['sha256']==prior['original_engine']['sha256'],'governance-entry-inherited-source-admission')
    before=o.doc(prior['parent_archive']);oldengine=o.doc(prior['engine_archive']);expected=_source_ref_parent(before,previous);accepted=_source_ref_engine(oldengine,previous,prior)
    o.need(parent['calls'][:len(before['calls'])]==before['calls']and len(parent['calls'])==len(before['calls'])+1 and parent['resolved_errors']==expected['resolved_errors']and all(parent.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'governance-entry-original-parent-prefix')
    prefix=copy.deepcopy(engine['calls'][:len(accepted['calls'])]);prefix[-1].pop('applied',None)
    o.need(prefix==accepted['calls']and engine.get('source_result_recovery')==previous and engine['companies'][0]['phase']=='ready'and engine['companies'][0]['artifacts']['source']==o.doc(prior['local_result'])['artifacts']['source'],'governance-entry-inherited-source-result')
    o.need(parent['status']=='hold'and parent.get('error')=='execution-child-stopped'and not parent.get('child')and len(parent['calls'])==7 and all(c['state']=='returned'for c in parent['calls']),'governance-entry-parent')
    call=parent['calls'][-1];la=o.doc(call['launch']);ex=o.doc(call['result']);argv=call['argv']
    o.need(call['launch']['path']==str(folder/'children/0006-launch.json')and call['result']['path']==str(folder/'children/0006-exit.json')and argv==parent['calls'][-2]['argv']==la['argv']==ex['argv']and la['order']==parent['order']and la['index']==6 and ex['launch']==call['launch']and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':GOVERNANCE_ENTRY_ERROR},'governance-entry-natural-child')
    failed=engine['calls'][-1]
    o.need(engine['order']==parent['order']and engine['scope_sha256']==parent['scope_sha256']and engine['status']=='hold'and engine.get('error')==GOVERNANCE_ENTRY_ERROR and engine['phase']=='company'and engine['index']==1 and len(engine['calls'])==33 and failed['state']=='failed'and failed['step']=='company'and failed['company_index']==1 and failed['error']==GOVERNANCE_ENTRY_ERROR and 'result'not in failed and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:-1])and failed['context']['order']==order and failed['context']['company']==order['companies'][1]and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'governance-entry-exact-local-failure')
    worker=o.doc(worker_ref);request=o.doc(worker['request']);response=o.doc(worker['response']);attempt=Path(worker_ref['path']).parent;pe_ref=o.ref(attempt/'parent-run-exit.json');pe=o.doc(pe_ref);output=json.loads(o.raw(pe['stdout']))
    o.need(worker_ref['path']==str(o.PROJECT/'runtime/standalone-workshop-director/attempts/task-86161e9560b2bf7aa850c6c2-8/exit.json')and worker['returncode']==0 and request['attempt_id']==response['attempt_id']=='task-86161e9560b2bf7aa850c6c2-8'and request['task']['id']==response['task_id']=='task-86161e9560b2bf7aa850c6c2'and request['context']['order']==response['context']['order']==parent['order']and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and pe['returncode']==0 and not o.raw(pe['stderr'])and output['last_child_receipt']==call['result']and o.doc(request['config_ref'])==request['config'],'governance-entry-original-worker')
    outer=request['task']['outer'];o.need(outer['boot']==parent['boot_identity']and outer['clock_contract']==parent['clock_contract']and outer['start_monotonic']<=parent['start_monotonic'],'governance-entry-original-clock')
    wf_ref=workflow_ref or o.ref(folder/'companies/1/company-navigation/workflow.json');wf=o.doc(workflow_archive or wf_ref);o.need(workflow_archive is None or workflow_archive['sha256']==wf_ref['sha256'],'governance-entry-workflow-archive');job_ref=o.ref(folder/'companies/1/company-navigation/work-order.json');tree_ref=wf['last_tree'];tree=o.doc(tree_ref)
    o.need(wf_ref['sha256']=='995872b9e6451f9f1487efaf372909ed8082693f79d096dcebd1439c4f019618'and len(wf['calls'])==1 and wf['calls'][0]['phase']=='context'and wf['calls'][0]['state']=='confirmed'and wf['phase']=='searchCompany'and wf['last_error']['code']==GOVERNANCE_ENTRY_ERROR and wf['company_configuration_job']==job_ref and tree['url']=='https://life.douyin.com/p/governance/violation_list','governance-entry-original-WF')
    evidence=[previous,prior['parent_archive'],prior['engine_archive'],prior['release'],prior['local_result'],worker_ref,worker['request'],worker['response'],request['config_ref'],pe_ref,pe['stdout'],pe['stderr'],call['launch'],call['result'],wf_ref,job_ref,tree_ref]
    for r in evidence:
        if r!=wf_ref:o.raw(r)
    return {'order':order,'previous_proof':previous,'previous_codes':prior['code_refs'],'original_outer':outer,'failed_call':failed,'workflow':wf_ref,'job':job_ref,'tree':tree_ref,'evidence':evidence}

def _governance_entry_sources(codes,release_ref,*,installed=True,source_archives=None):
    release=o.doc(release_ref);targets={str(o.PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_execution.py','violation_execution_ports.py','violation_initial_ledger_recovery.py','violation_reboot_continuation.py')}|{str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),str(o.PROJECT/'skills/workshop-director/scripts/collection_ready.py')};cc=str(o.PROJECT/'skills/workshop-director/scripts/company_configuration.py')
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==7 and {t['target']for t in release['targets']}==targets|{cc},'governance-entry-seven-sources')
    out=copy.deepcopy(codes);by={r['path']:r for r in out};o.need(cc not in by and len(by)==len(out),'governance-entry-independent-configuration')
    for t in release['targets']:
        o.need(t['mode']==420 and t['before']['sha256']==t['old_sha256'],'governance-entry-release-before');o.raw(t['before']);o.raw(t['after'])
        if t['target']==cc:o.need(t['old_sha256']=='36b3baa3f67090c5229911e9e6c7e3714ab69189b21e3e2eb19c3edf1c827c45','governance-entry-configuration-baseline')
        else:
            old=by[t['target']];o.need(old['sha256']==t['old_sha256'],'governance-entry-original-slot');out[out.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        if installed:o.need(o.ref(Path(t['target']))['sha256']==t['after']['sha256'],'governance-entry-source-not-installed')
    for r in out:
        if r['path']not in targets:
            archive=(source_archives or {}).get(r['path'])
            if archive is None:o.raw(r)
            else:o.need(archive['original']==r and archive['archive']['sha256']==r['sha256'],'governance-exact-source-archive');o.raw(archive['archive'])
    o.need(len(out)==len(codes),'governance-entry-no-added-slot');return out

def _governance_entry_parent(before,pr):
    value=copy.deepcopy(before);value.update(status='running',**{FIELD:pr});value.pop('error');value.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':GOVERNANCE_ENTRY_ERROR,'recovery':pr,'result_kind':'local-entry-retry-not-original-child-success'});return value

def _governance_entry_engine(before,pr):
    value=copy.deepcopy(before);index=len(value['calls'])-1;failed=value['calls'].pop();value.update(status='running');value.pop('error');value.setdefault('resolved_readonly_failures',[]).append({'index':index,'call':failed,'proof':pr});return value

def plan_governance_entry(parent_ref,engine_ref,worker_ref,release_ref,*,installed=True):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(parent_ref['path']==str(folder/'launcher.json')and engine_ref['path']==str(folder/'engine.json'),'governance-entry-canonical-path');facts=_governance_entry_facts(parent,engine,worker_ref);codes=_governance_entry_sources(facts['previous_codes'],release_ref,installed=installed);live_lease(facts['order']);return {'kind':GOVERNANCE_ENTRY_KIND,'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'code_refs':codes,'at':stamp(),'ui_used':False}

def verify_governance_entry(current,proof_ref,*,installed=True,source_archives=None):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.violation-governance-entry-recovery'/p['original_parent']['sha256'];o.need(p['kind']==GOVERNANCE_ENTRY_KIND and current.get(FIELD)==proof_ref and proof_ref['path']==str(base/'proof.json')and p['parent_archive']['sha256']==p['original_parent']['sha256']and p['engine_archive']['sha256']==p['original_engine']['sha256']and p['ui_used']is False,'governance-entry-proof');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);facts=_governance_entry_facts(parent,engine,p['worker'],workflow_ref=p['facts']['workflow'],workflow_archive=p['workflow_archive']);codes=_governance_entry_sources(facts['previous_codes'],p['release'],installed=installed,source_archives=source_archives);o.need(facts==p['facts']and codes==p['code_refs'],'governance-entry-derived');expected=_governance_entry_parent(parent,proof_ref);o.need(current['calls'][:len(parent['calls'])]==parent['calls']and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors']and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()),'governance-entry-parent-preserved');live=o.doc(o.ref(folder/'engine.json'));want=_governance_entry_engine(engine,proof_ref);o.need(live['calls'][:len(want['calls'])]==want['calls']and live.get('resolved_readonly_failures',[])[:len(want['resolved_readonly_failures'])]==want['resolved_readonly_failures']and live['companies'][0]==engine['companies'][0]and live['order']==parent['order'],'governance-entry-engine-preserved');return {'kind':GOVERNANCE_ENTRY_KIND,'code_refs':codes,'failed_calls':parent['calls'],'initial_failed_calls':parent['calls'],'evidence':[proof_ref,p['parent_archive'],p['engine_archive'],p['workflow_archive'],p['release'],*[r for r in facts['evidence']if r!=facts['workflow']]]}

_GOVERNANCE_ENTRY_PREVIOUS_VERIFY=verify_recovered
def verify_recovered(current,proof_ref,**kwargs):
    if o.doc(proof_ref).get('kind')==GOVERNANCE_ENTRY_KIND:return verify_governance_entry(current,proof_ref,**kwargs)
    return _GOVERNANCE_ENTRY_PREVIOUS_VERIFY(current,proof_ref,**kwargs)

def recover_governance_entry(parent_ref,engine_ref,worker_ref,release_ref,*,checkpoint=_recovery_checkpoint):
    folder=Path(parent_ref['path']).parent;base=folder/'.violation-governance-entry-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for handle in(a,b):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if(base/'proof.json').exists():
            pr=o.ref(base/'proof.json');p=o.doc(pr);o.need((p['original_parent'],p['original_engine'],p['worker'],p['release'])==(parent_ref,engine_ref,worker_ref,release_ref),'governance-entry-same-intent')
        else:
            p=plan_governance_entry(parent_ref,engine_ref,worker_ref,release_ref);p['workflow_archive']=immutable_bytes(base/'original-workflow.json',o.raw(p['facts']['workflow']));p['parent_archive']=immutable_bytes(base/'original-parent.json',o.raw(parent_ref));p['engine_archive']=immutable_bytes(base/'original-engine.json',o.raw(engine_ref));pr=o.immutable(base/'proof.json',p);checkpoint('proof-published')
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);ep=_governance_entry_parent(parent,pr);ee=_governance_entry_engine(engine,pr);cp=o.doc(o.ref(folder/'launcher.json'));ce=o.doc(o.ref(folder/'engine.json'));o.need(cp in(parent,ep)and ce in(engine,ee),'governance-entry-CAS-frontier');_governance_entry_facts(parent,engine,p['worker'],workflow_ref=p['facts']['workflow'],workflow_archive=p['workflow_archive']);_governance_entry_sources(p['facts']['previous_codes'],p['release']);live_lease(p['facts']['order'])
        if ce==engine:
            from violation_execution import atomic
            atomic(folder/'engine.json',ee);checkpoint('engine-CAS')
        verify_governance_entry(ep,pr)
        if cp==parent:
            from role_execution_launcher import save
            save(folder/'launcher.json',ep)
        return {'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':pr,'ui_used':False,'source_rebuilt':False}
