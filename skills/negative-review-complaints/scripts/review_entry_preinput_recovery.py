"""Exact openReviews locator pre-input recovery. Metadata only; no UI port."""
import argparse,copy,fcntl,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/workshop-director/scripts'),str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/douyin-laike-operator/scripts')]
import complaint_execution_order as o
import initial_ledger_recovery as h
import dom_evidence as d
from readonly_tick_snapshot import decode
FIELD='review_entry_preinput_recovery';KIND='verified-open-reviews-preinput-recovery-v1'
def paths():return {'bridge-workflow.py':str(o.PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'initial_ledger_recovery.py':str(o.PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'review_entry_preinput_recovery.py':str(o.PROJECT/'skills/negative-review-complaints/scripts/review_entry_preinput_recovery.py')}
def source_tip(parent,release_ref,old_refs,*,installed,extra_source_archives=()):
    release=o.doc(release_ref);by_path=paths();targets=release['targets'];old={Path(r['path']).name:r for r in old_refs}
    o.need(release['kind']=='supervisor-reviewed-source-release-v1' and len(targets)==3 and {t['target'] for t in targets}==set(by_path.values()) and all(t['mode']=='0644' for t in targets),'review-entry-exact-three-reviewed-targets')
    o.need(set(old)=={'bridge-workflow.py.before','initial_ledger_recovery.py.before'} and len(old_refs)==2,'review-entry-exact-old-archives')
    archives=[]
    for name in ('bridge-workflow.py','initial_ledger_recovery.py'):
        t=next(t for t in targets if t['target']==by_path[name]);r=old[name+'.before'];o.need(r['sha256']==t['old_sha256'],'review-entry-old-code-release-binding');o.raw(r);archives.append({'target':t['target'],'archive':r})
    # Preserve the previous entire admission chain while reading only these
    # precise reviewed historical source bytes from their pinned archives.
    proxy=copy.deepcopy(parent)
    if proxy.get(FIELD):
        original=o.doc(o.doc(parent[FIELD])['parent_archive']);proxy['resolved_errors']=original['resolved_errors']
    prior=h._verify_plan_recovered(proxy,proxy[h.PLAN_FIELD],installed=False,source_archives=[*archives,*extra_source_archives])
    codes=copy.deepcopy(prior['code_refs']);by_code={r['path']:r for r in codes}
    for t in targets:
        o.raw(t['after']);new={'path':t['target'],'sha256':t['after']['sha256']}
        if t['target']==by_path['review_entry_preinput_recovery.py']:
            o.need(t['old_sha256'] is None and t['target'] not in by_code,'review-entry-new-helper-only');codes.append(new)
        else:
            previous=by_code[t['target']];o.need(previous['sha256']==t['old_sha256'],'review-entry-original-admission-base');codes[codes.index(previous)]=new
    if installed:
        for ref in codes:o.raw(ref)
        for path in by_path.values():o.need((Path(path).stat().st_mode & 0o777)==0o644,'review-entry-installed-mode')
    return prior,codes,archives

def locator(tree):
    candidates=[n for n in d.nodes(tree) if n.get('name')=='评价管理' and not n.get('children') and 'navi_evaluation' in n.get('attributes',{}).get('class','').split()]
    target=d.unique(candidates,'review-management-sidebar-not-unique');roots=[n for n in d.nodes(tree) if n.get('selector')=='#box-aside-menu']
    if roots:o.need(any(n is target for n in subtree(d.unique(roots))),'review-management-sidebar-scope-invalid')
    o.need(not target.get('disabled') and target.get('selector'),'element-not-ready');return target

def subtree(node):
    yield node
    for child in node.get('children',[]):yield from subtree(child)

def original_contract(parent,engine,state,job,scope,prior):
    order=o.validate(parent['order']);folder=o.location(parent['order']);company=order['companies'][0];artifacts=engine['companies'][0]['artifacts']
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and not parent.get(FIELD) and not parent.get('child') and not parent.get('completion') and len(parent['calls'])==3 and parent['calls'][:2]==prior['failed_calls'],'review-entry-original-parent-hold')
    o.need(engine['kind']=='complaint-execution-v1' and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'] and engine['status']=='hold' and engine['phase']=='collect' and engine['index']==0 and engine.get('error')=='semantic-locator-not-unique' and not engine.get(FIELD) and len(engine['calls'])==5 and engine['calls'][0]==prior['failed_engine_call'],'review-entry-original-engine-hold')
    o.need([c['step'] for c in engine['calls']]==['plan','plan','collect','collect','collect'] and all(c['state']=='returned' and c.get('applied') is True for c in engine['calls'][1:4]) and engine['calls'][-1]['state']=='failed' and engine['calls'][-1]['error']=='semantic-locator-not-unique','review-entry-exact-engine-failure-prefix')
    for index,c in enumerate(engine['calls'][1:4],1):
        o.need(Path(c['result']['path'])==folder/'receipts'/(str(index+1).zfill(5)+'.json'),'review-entry-return-receipt-path');o.doc(c['result'])
    o.need(artifacts['unit_index']==0 and artifacts['unit_phase']=='acquire' and artifacts['completed_units']==[] and engine['calls'][-1]['context']=={'order':order,'company':company,'artifacts':artifacts,'folder':str(folder/'companies/0'),'phase':'collect'},'review-entry-original-collect-context')
    o.need(artifacts['units'][0]=={'kind':'new','start':company['start'],'end_exclusive':company['end_exclusive'],'keys':[]} and Path(job['workflow_path'])==folder/'companies/0/units/0/operator'/job['work_order_id'][:16]/'workflow.json' and Path(job['work_order_path'])==Path(job['workflow_path']).with_name('work-order.json') and artifacts['unit_artifacts']['work_order']==o.ref(Path(job['work_order_path'])) and engine['business_journals']==[job['workflow_path']],'review-entry-canonical-work-order')
    from role_cli import validate_job
    validate_job(job)
    o.need(job['action']=='acquire' and job['source_purpose']=='complaint-draft-only-current-dispatch' and all(job.get(k) is False for k in ('progress_updates_enabled','send_enabled','submit_enabled','identity_bootstrap')) and job['identity_contract']=='merchant-v2' and (job['company'],str(job['groupid']),job['date_range']['start'],job['date_range']['end_exclusive'])==(company['company'],company['groupid'],company['start'],company['end_exclusive']),'review-entry-original-job-scope')
    expected_fingerprint=hashlib.sha256(json.dumps({k:job.get(k) for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    o.need(state['backend']=='local-dom-bridge' and state['state']=='running' and state['phase']=='openReviews' and state['revision']==2 and state['fingerprint']==expected_fingerprint and state['work_order_id']==job['work_order_id'] and state['company']==job['company'] and state['groupid']==str(job['groupid']) and state['date_range']=={k:job['date_range'][k] for k in ('start','end')} and state.get('last_error',{}).get('code')==state['last_error'].get('message')=='semantic-locator-not-unique','review-entry-original-operator-error')
    o.need(len(state['calls'])==1 and not any(k in state for k in ('exportPending','downloadPending','result',FIELD)),'review-entry-no-business-input')
    call=state['calls'][0];o.need(call['phase']=='account' and call['state']=='confirmed' and call['command']=={'op':'activate','tabId':parent['tab_id']} and call['result']['tabId']==parent['tab_id'],'review-entry-only-account-activation')
    window=call['result']['windowId'];decode(scope,parent['tab_id'],window);before=d.context(scope['before'],parent['tab_id'],job['groupid']);after=d.context(scope['after'],parent['tab_id'],job['groupid']);tree=scope['tree'];o.need(before['url']==after['url']==call['result']['url'] and before['windowId']==after['windowId']==window and urlsplit(before['url']).path=='/p/home' and tree==o.doc(state['last_tree']) and tree['url']=='https://life.douyin.com/p/home' and scope['ping'].get('version')==d.VERSION and scope['ping'].get('safety')=='DOM-only','review-entry-original-read-scope')
    o.need(all(d.unique([w for w in scope[key] if w.get('windowId')==window]).get('focused') is True and d.context(scope[key],parent['tab_id'],job['groupid']).get('active') is True for key in ('before','after')),'review-entry-original-tab-not-active')
    identity=job['identity_baseline'];o.need(state['identity']==state['entry_identity']==state['identity_before']==identity==job['known_company_identities'][str(job['groupid'])] and state['initial_groupid']==state['entry_groupid']==str(job['groupid']),'review-entry-original-account-identity');d.identity(tree,identity)
    try:d.exact(tree,'评价管理')
    except ValueError as error:o.need(str(error)=='semantic-locator-not-unique','review-entry-original-locator-failure')
    else:raise ValueError('review-entry-not-original-ambiguity')
    target=locator(tree)
    # The retained child receipt proves this phase failed before mutate/once.
    call=parent['calls'][2];launch=o.doc(call['launch']);result=o.doc(call['result']);argv=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/negative-review-complaints/scripts/complaint_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(parent['tab_id']),'--pid',str(parent['pid']),'--steps','1000']
    o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==argv and launch['index']==2 and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':'semantic-locator-not-unique'} and Path(call['launch']['path'])==folder/'children/0002-launch.json' and Path(call['result']['path'])==folder/'children/0002-exit.json','review-entry-exact-outer-rc2')
    return {'target':{k:target[k] for k in ('name','selector','tag')},'failed_engine_indices':[0,4],'failed_calls':parent['calls']}

def worker_evidence(parent,engine_ref,worker_ref):
    ex=o.doc(worker_ref);folder=Path(worker_ref['path']).parent;request=o.doc(ex['request']);response=o.doc(ex['response']);order=o.doc(parent['order'])
    o.need(folder==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and Path(worker_ref['path'])==folder/'exit.json' and ex['attempt_id']==request['attempt_id'] and ex['returncode']==0 and request.get('kind')=='workshop-worker-request-v1' and response.get('kind')=='workshop-worker-result-v1' and ex['request']['path']==str(folder/'request.json') and ex['response']['path']==str(folder/'response.json') and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==parent['order'] and response['attempt_id']==request['attempt_id'] and response['task_id']==request['task']['id'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and response['context']['order']==parent['order'] and o.doc(request['config_ref'])==request['config'],'review-entry-natural-worker-binding')
    pe=o.ref(folder/'parent-run-exit.json');r=o.doc(pe);out=json.loads(o.raw(r['stdout']));o.need(r['returncode']==0 and not o.raw(r['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==parent['calls'][2]['result'] and out['engine']==engine_ref,'review-entry-worker-parent-result')
    return [worker_ref,ex['request'],ex['response'],request['config_ref'],pe,r['stdout'],r['stderr']]

def plan(parent_ref,engine_ref,operator_ref,job_ref,scope_ref,worker_ref,release_ref,old_refs,*,installed=False):
    parent=o.doc(parent_ref);folder=o.location(parent['order']);engine=o.doc(engine_ref);state=o.doc(operator_ref);job=o.doc(job_ref)
    o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json' and Path(operator_ref['path'])==Path(job['workflow_path']) and Path(job_ref['path'])==Path(job['work_order_path']) and Path(scope_ref['path']).parent==Path(job['workflow_path']).parent/'bridge-evidence','review-entry-canonical-inputs')
    prior,codes,archives=source_tip(parent,release_ref,old_refs,installed=installed);facts=original_contract(parent,engine,state,job,o.doc(scope_ref),prior);evidence=worker_evidence(parent,engine_ref,worker_ref);h.ledger_bytes(o.validate(parent['order']))
    return {'kind':KIND,'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'job':job_ref,'scope':scope_ref,'worker':worker_ref,'release':release_ref,'old_sources':archives,'code_refs':codes,'facts':facts,'worker_evidence':evidence,'ui_used':False}

def recovered(parent,engine,operator,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine);operator=copy.deepcopy(operator)
    for state in (parent,engine):state.setdefault('resolved_errors',[]).append({'error':state.pop('error'),'recovery':proof});state.update(status='running',**{FIELD:proof})
    operator.setdefault('resolved_errors',[]).append({**operator.pop('last_error'),'recovery_proof':proof,'next_phase':'openReviews'});operator[FIELD]=proof
    return parent,engine,operator

def verify_recovered(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-entry-preinput-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and Path(proof_ref['path'])==base/'proof.json' and current.get(FIELD)==proof_ref and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-entry-canonical-proof')
    original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);state=o.doc(p['operator_archive']);job=o.doc(p['job']);o.need(p['parent_archive']['sha256']==p['original_parent']['sha256'] and p['engine_archive']['sha256']==p['original_engine']['sha256'] and p['operator_archive']['sha256']==p['original_operator']['sha256'] and Path(p['parent_archive']['path'])==base/'original-parent.json' and Path(p['engine_archive']['path'])==base/'original-engine.json' and Path(p['operator_archive']['path'])==base/'original-operator.json','review-entry-archive-binding')
    o.need(all(Path(x['archive']['path'])==base/'sources'/Path(x['archive']['path']).name for x in p['old_sources']),'review-entry-canonical-source-archives')
    prior,codes,_=source_tip(current,p['release'],[x['archive'] for x in p['old_sources']],installed=installed,extra_source_archives=extra_source_archives);facts=original_contract(original,engine,state,job,o.doc(p['scope']),prior);evidence=worker_evidence(original,p['original_engine'],p['worker']);expected=recovered(original,engine,state,proof_ref)[0]
    o.need(p['facts']==facts and p['worker_evidence']==evidence and p['code_refs']==codes and current['calls'][:3]==original['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()),'review-entry-proof-derived-original-preserved')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':original['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['operator_archive'],p['job'],p['scope'],p['release'],*[x['archive'] for x in p['old_sources']],*evidence]}

def verified_engine_calls(engine):
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'review-entry-engine-parent-proof');admission=verify_recovered(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,o.doc(p['operator_archive']),proof)[1]
    o.need(engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'] and engine['calls'][:5]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'review-entry-engine-original-prefix')
    return [call for i,call in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]

def recover(parent_ref,engine_ref,operator_ref,job_ref,scope_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;operator_path=Path(operator_ref['path']);base=folder/'.review-entry-preinput-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b,operator_path.with_name('.bridge-execution.lock').open('a') as c:
        for lock in (a,b,c):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'job':job_ref,'scope':scope_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted((Path(r['path']).name,r['sha256']) for r in old_refs)==sorted((Path(x['archive']['path']).name,x['archive']['sha256']) for x in p['old_sources']),'review-entry-original-inputs')
        else:
            original_parent=o.doc(parent_ref);lease=o.doc(o.ref(Path(original_parent['order']['path']).parent.parent/'state.json'));import director
            o.need(lease['dispatch_id']==o.doc(original_parent['order'])['dispatch_id'] and lease['day']==o.doc(original_parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-entry-current-lease-required')
            p=plan(parent_ref,engine_ref,operator_ref,job_ref,scope_ref,worker_ref,release_ref,old_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True);o.canonical(base/'sources')
            for field,name,ref in [('parent_archive','original-parent.json',parent_ref),('engine_archive','original-engine.json',engine_ref),('operator_archive','original-operator.json',operator_ref)]:p[field]=h.immutable_bytes(base/name,o.raw(ref))
            for item in p['old_sources']:item['archive']=h.immutable_bytes(base/'sources'/Path(item['archive']['path']).name,o.raw(item['archive']))
            p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);state=o.doc(p['operator_archive']);new_parent,new_engine,new_operator=recovered(original,engine,state,proof)
        lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(original['order'])['dispatch_id'] and lease['day']==o.doc(original['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-entry-current-lease-required')
        h.ledger_bytes(o.validate(original['order']));refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],new_parent),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],new_engine),h.exact_metadata_state(operator_path,p['operator_archive'],new_operator)];o.raw(job_ref);verify_recovered(new_parent,proof)
        import complaint_execution_launcher as launcher
        for ref in refs:o.raw(ref)
        for path,value in ((operator_path,new_operator),(folder/'engine.json',new_engine),(folder/'launcher.json',new_parent)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'operator':o.ref(operator_path),'proof':proof,'ui_used':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','engine','operator','job','scope','worker','release'):parser.add_argument('--'+name,required=True,help='JSON exact path/SHA reference')
    parser.add_argument('--old-source',action='append',required=True);a=parser.parse_args()
    try:print(json.dumps(recover(*[json.loads(getattr(a,n)) for n in ('parent','engine','operator','job','scope','worker','release')],[json.loads(r) for r in a.old_source]),ensure_ascii=False));return 0
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())
