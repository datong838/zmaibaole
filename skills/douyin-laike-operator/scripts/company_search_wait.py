"""Bounded read-only wait for the observed post-switch loading modal."""
import json, uuid, time, sys, hashlib, copy
from pathlib import Path
from urllib.parse import urlsplit
from dom_evidence import nodes, unique, identity, company_switch, context, VERSION
from role_cli import write_json, digest

PREFIX='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__'
PREFIXES=(PREFIX,'src-components-HeaderV2-components-UserCard-components-SwitchAccountCardModal-index-module__')
def field(tree):
    fields=[n for n in nodes(tree) if n.get('role')=='textbox' and n.get('placeholder')=='搜索商户']
    if len(fields)>1:raise ValueError('company-search-field-not-unique')
    if fields and (fields[0].get('disabled') or not fields[0].get('selector')):raise ValueError('company-search-field-not-ready')
    return fields[0] if fields else None

def verified_entry_identity(job,state):
    """Legacy copied map or the existing pinned configured-source authority.
    Uses the exact module already admitted by Workflow.configure_company_configuration;
    never creates a wider copied identity registry or trusts caller identity data.
    """
    groupid=state.get('initial_groupid');expected=job.get('known_company_identities',{}).get(groupid)
    if job.get('company_configuration_registry')=='configured-source-index-v2':
        module=sys.modules.get('_workflow_company_configuration');path=Path(__file__).resolve().parents[3]/'skills/workshop-director/scripts/company_configuration.py'
        current={'path':str(path),'sha256':digest(path)}
        if module is None or Path(module.__file__).absolute()!=path or getattr(module,'_WORKFLOW_SOURCE_REF',None)!=current or path.resolve()!=path or any(x.is_symlink()for x in(path,*path.parents)):raise ValueError('company-search-configured-source-origin')
        config,_,original=module.job_configuration(job)
        if state.get('company_configuration_job')!=original or state.get('entry_groupid')!=groupid:raise ValueError('company-search-configured-source-job')
        verified=module.configured_source_identity(job,groupid,config=config)
        if expected is not None and expected!=verified:raise ValueError('company-search-known-source-conflict')
        expected=verified
    if not expected or expected!=state.get('entry_identity')or expected.get('provider')!=state.get('provider_baseline'):raise ValueError('company-search-entry-identity-required')
    return expected

def entry_error_transform(job,state,tree):
    error=state.get('last_error')
    if job.get('company_configuration_registry')!='configured-source-index-v2'or not error or (error.get('code'),error.get('message'))!=('company-search-entry-identity-required','company-search-entry-identity-required'):raise ValueError('company-search-entry-error-not-exact')
    candidate=copy.deepcopy(state);candidate.pop('last_error');pending(tree,job,candidate)
    expected=verified_entry_identity(job,candidate)
    candidate.setdefault('resolved_errors',[]).append({**error,'disposition':'configured-source-entry-authority-corrected-not-search-complete','source_groupid':candidate['initial_groupid'],'source_identity':expected,'policy':job['company_configuration_policy'],'original_tree':candidate['last_tree']})
    candidate['configured_search_entry_recovery']={'kind':'configured-source-entry-authority-corrected-v1','original_tree':candidate['last_tree'],'original_calls':len(candidate['calls'])}
    return candidate

def pending(tree,job,state):
    if state.get('phase')!='searchCompany' or state.get('state')!='running' or job.get('identity_contract')!='merchant-v2':raise ValueError('company-search-wait-scope-required')
    if state.get('last_error'):raise ValueError('explicit-company-search-read-reconciliation-required')
    if state.get('exportPending') or state.get('downloadPending') or any(c.get('state')!='confirmed' for c in state.get('calls',[])):raise ValueError('company-search-wait-intent-conflict')
    if not state.get('calls'):raise ValueError('company-search-switch-confirmation-required')
    c=state['calls'][-1];cmd=c.get('command',{});clicked=c.get('result',{}).get('clicked',{})
    if c.get('phase')!='context' or cmd.get('op')!='click' or cmd.get('kind')!='navigation' or cmd.get('tabId')!=state.get('tab_id') or clicked.get('selector')!=cmd.get('locator',{}).get('value'):raise ValueError('company-search-switch-confirmation-required')
    expected=verified_entry_identity(job,state)
    identity(tree,expected)
    button=company_switch(tree)
    if button.get('selector')!=clicked['selector'] or button.get('name')!=clicked.get('name'):raise ValueError('company-search-switch-selector-changed')
    if field(tree) is not None:return False
    modals=[n for n in nodes(tree) if any(prefix+'login-modal--' in n.get('attributes',{}).get('class','') for prefix in PREFIXES)]
    modal=unique(modals,'company-search-loading-modal-unverified')
    if not {'life-core-modal','life-core-modal-show'}<=set(modal.get('attributes',{}).get('class','').split()):raise ValueError('company-search-loading-modal-unverified')
    prefix=unique([p for p in PREFIXES if p+'login-modal--' in modal.get('attributes',{}).get('class','')],'company-search-loading-modal-unverified')
    inner={'truncated':False,'root':modal};ns=list(nodes(inner))
    for token in ('container--','content--'):
        unique([n for n in ns if prefix+token in n.get('attributes',{}).get('class','')],'company-search-loading-structure-unverified')
    legacy={'life-core-loading-mask','life-core-loading-wrapper'}
    if any(legacy & set(n.get('attributes',{}).get('class','').split()) for n in ns):
        for required in ({'life-core-loading-mask','life-core-loading-mask-show'},{'life-core-loading-wrapper','life-core-loading-wrapper-show'}):
            unique([n for n in ns if required<=set(n.get('attributes',{}).get('class','').split())],'company-search-loading-structure-unverified')
    else:
        # A second positively observed loading representation, not an empty page.
        unique([n for n in ns if prefix+'title--' in n.get('attributes',{}).get('class','') and n.get('name')=='切换公司'],'company-search-loading-structure-unverified')
        content=unique([n for n in ns if prefix+'content--' in n.get('attributes',{}).get('class','')],'company-search-loading-structure-unverified')
        inside=list(nodes({'truncated':False,'root':content}))
        block=unique([n for n in inside if set(n.get('attributes',{}).get('class','').split())=={'life-core-loading','life-core-loading-block'}],'company-search-loading-structure-unverified')
        scope=list(nodes({'truncated':False,'root':block}))
        for token in ('card__body_','card__main_','card__list_','card__loading_'):
            selected=unique([n for n in scope if any(c.startswith(token) for c in n.get('attributes',{}).get('class','').split())],'company-search-loading-structure-unverified')
            scope=list(nodes({'truncated':False,'root':selected}))
        image=unique([n for n in scope if n.get('tag')=='img' and n.get('role')=='img' and n.get('name')=='loading' and any(c.startswith('card__loading-img_') for c in n.get('attributes',{}).get('class','').split())],'company-search-loading-structure-unverified')
        text=unique([n for n in scope if n.get('tag')=='span' and n.get('name')=='加载中...' and any(c.startswith('card__loading-text_') for c in n.get('attributes',{}).get('class','').split())],'company-search-loading-structure-unverified')
        if image.get('children') or text.get('children') or any(n.get('name') not in ('','加载中...','loading') for n in inside if not n.get('children')):raise ValueError('company-search-loading-structure-unverified')
    if any(n.get('role') in ('textbox','button','combobox') for n in ns):raise ValueError('company-search-loading-unexpected-control')
    return True

def wait(workflow,tree,current):
    """Initial sample + capped-backoff readonly re-samples until ready (B82: no time shackle)."""
    if not pending(tree,workflow.job,workflow.s):return field(tree)
    original_calls=json.loads(json.dumps(workflow.s['calls']));deadline=time.monotonic()+86400
    for attempt in range(2000):
        delay=min(.25*(2**attempt),2.0,deadline-time.monotonic())
        if delay<=0:raise ValueError('company-search-loading-timeout-readonly')
        time.sleep(delay) # Only exact loading waits; a ready field is immediate.
        folder=workflow.file.parent/'company-search-read-wait';folder.mkdir(exist_ok=True)
        if workflow.job.get('company_configuration_registry')=='configured-source-index-v2':
            from readonly_tick_snapshot import decode
            command={'op':'readonly-scope','tabId':workflow.s['tab_id'],'windowId':current['windowId']}
            raw=workflow.call(command);scopepath=folder/(uuid.uuid4().hex+'-scope.json');write_json(scopepath,raw);scope_ref={'path':str(scopepath),'sha256':digest(scopepath)}
            value=decode(raw,command['tabId'],command['windowId']);a=context(value['before'],command['tabId'],workflow.s['initial_groupid']);b=context(value['after'],command['tabId'],workflow.s['initial_groupid']);fresh=value['tree']
            if a.get('windowId')!=current.get('windowId')or a.get('url')!=current.get('url')or b.get('windowId')!=a.get('windowId')or b.get('url')!=a.get('url')or fresh.get('url')!=urlsplit(a['url'])._replace(query='',fragment='').geturl():raise ValueError('company-search-read-context-changed')
            if value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only':raise ValueError('reviewed-extension-version-required')
            workflow._last_tick_scope_ref=scope_ref
        else:
            before=workflow.call({'op':'tabs'});a=context(before,workflow.s['tab_id'],workflow.s['initial_groupid'])
            if a.get('windowId')!=current.get('windowId') or a.get('url')!=current.get('url'):raise ValueError('company-search-read-context-changed')
            ping=workflow.call({'op':'ping','tabId':workflow.s['tab_id']})
            if ping.get('version')!=VERSION or ping.get('safety')!='DOM-only':raise ValueError('reviewed-extension-version-required')
            fresh=workflow.call({'op':'tree','tabId':workflow.s['tab_id']})
            after=workflow.call({'op':'tabs'});b=context(after,workflow.s['tab_id'],workflow.s['initial_groupid'])
            if b.get('windowId')!=a.get('windowId') or b.get('url')!=a.get('url') or fresh.get('url')!=urlsplit(a['url'])._replace(query='',fragment='').geturl():raise ValueError('company-search-read-context-changed')

        path=folder/(uuid.uuid4().hex+'.json');write_json(path,fresh)
        ref={'path':str(path),'sha256':digest(path)}
        workflow.s.setdefault('company_search_read_wait',[]).append({**ref,**({'scope':scope_ref}if workflow.job.get('company_configuration_registry')=='configured-source-index-v2'else{})});workflow.save()
        list(nodes(fresh));identity(fresh,workflow.s['entry_identity'])
        target=field(fresh)
        if target is not None:
            if workflow.s['calls']!=original_calls:raise ValueError('company-search-wait-mutated-calls')
            return target
        pending(fresh,workflow.job,workflow.s)
    raise ValueError('company-search-loading-timeout-readonly')
