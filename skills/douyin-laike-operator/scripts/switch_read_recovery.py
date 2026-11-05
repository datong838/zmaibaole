"""Original-order company-switch read reconciliation. No UI command is issued here."""
import argparse, copy, hashlib, importlib.util, json, os, re, sys, time, uuid
from pathlib import Path
# Isolated (-I) CLI omits the script directory; these are reviewed sibling modules.
_OPERATOR_SCRIPTS=Path(__file__).resolve().parents[3]/'skills/douyin-laike-operator/scripts'
if str(_OPERATOR_SCRIPTS)not in sys.path:sys.path.insert(0,str(_OPERATOR_SCRIPTS))
from datetime import datetime, timezone
from urllib.parse import urlsplit,parse_qs
from dom_evidence import VERSION

KIND='verified-company-switch-read-recovery-v1'
def need(ok,code):
    if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def immutable(p,raw):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    try:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except FileExistsError:need(p.read_bytes()==raw,'read-recovery-artifact-conflict')
    return {'path':str(p.resolve()),'sha256':sha(raw)}
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def document(r):
    p=Path(r['path']);need(p.is_absolute() and p.is_file() and not p.is_symlink(),'read-recovery-ref-invalid');b=p.read_bytes();need(sha(b)==r['sha256'],'read-recovery-evidence-changed');return json.loads(b)
def fingerprint(job):
    keys=('work_order_id','company','groupid','date_range','source_dir')
    if 'company_configuration_policy'in job or 'company_configuration_entry'in job:keys+=('company_configuration_policy','company_configuration_entry')
    if 'company_configuration_registry'in job:keys+=('company_configuration_registry',)
    return sha(json.dumps({k:job.get(k)for k in keys},sort_keys=True,ensure_ascii=False).encode())
def walk(tree):
    need(tree.get('truncated') is False and isinstance(tree.get('root'),dict),'read-recovery-tree-incomplete');stack=[tree['root']];n=0
    while stack:
        node=stack.pop();n+=1;need(n<=10000,'read-recovery-tree-limit');yield node;stack.extend(reversed(node.get('children',[])))
def formal_daily_return(job):
    # Exact shape emitted by daily flow.next_task + dispatch; missing flags are
    # never treated as false on any other work-order shape.
    keys={'action','company','groupid','identity_contract','provider_baseline','identity_baseline','known_company_identities','identity_bootstrap','allowed_groupids','identity_contract_upgrade','operator_skill','backend','explicit_tab_id_required','work_order_id','workflow_path','work_order_path'}
    configured_keys={'company_configuration_policy','company_configuration_entry','company_configuration_registry','date_range'}
    if set(job)==keys|configured_keys:
        # Configured daily dispatch carries the collection date as immutable
        # job metadata. The return workflow remains navigation-only (dates={}).
        if job.get('company_configuration_registry')!='configured-source-index-v2':return False
        configured_source_module(job).job_configuration(job)
        job={key:job[key] for key in keys}
    if set(job)!=keys:return False
    if not (job.get('action')=='return-company' and job.get('identity_contract')=='merchant-v2' and job.get('operator_skill')=='douyin-laike-operator' and job.get('backend')=='local-dom-bridge' and job.get('explicit_tab_id_required') is True and job.get('identity_bootstrap') is False and job.get('identity_contract_upgrade') is None):return False
    key=job.get('work_order_id');p=Path(job.get('work_order_path',''));w=Path(job.get('workflow_path',''))
    return bool(type(key) is str and re.fullmatch('[0-9a-f]{64}',key) and p.is_absolute() and w.is_absolute() and p.name=='work-order.json' and w==p.with_name('workflow.json') and p.parent.name==key[:16] and p.parent.parent.name=='return' and p.resolve()==p and w.resolve()==w and not p.is_symlink() and not w.is_symlink())
def explicit_navigation_only(job):
    # return-company has no export branch. Optional date fields are source
    # scope metadata, while the navigation workflow itself keeps dates={}.
    if not(job.get('action')=='return-company'and job.get('navigation_only')is True and job.get('progress_updates_enabled')is False and job.get('send_enabled')is False and job.get('export_enabled')is not True):return False
    dates=job.get('date_range',{})
    if not dates:return True
    from datetime import date,timedelta
    need(type(dates)is dict and {'start','end','end_exclusive'}<=set(dates),'read-recovery-navigation-date-metadata')
    start=date.fromisoformat(dates['start']);end=date.fromisoformat(dates['end'])
    need(start<=end and date.fromisoformat(dates['end_exclusive'])==end+timedelta(days=1),'read-recovery-navigation-date-metadata')
    return True

def return_navigation_only(job):
    return formal_daily_return(job) or explicit_navigation_only(job)
def saved_confirm_settle_anchor(job,s):
    """Only the normal producer's explicit immutable read chain, never a glob."""
    from readonly_tick_snapshot import decode
    from dom_evidence import identity,context
    reads=s.get('company_confirm_settle_reads');need(type(reads)is list and 1<=len(reads)<=3 and reads[-1].get('tree')==s.get('last_tree'),'read-recovery-settle-journal-binding')
    original=copy.deepcopy(s);original['last_tree']=reads[0]['before_tree']
    # This is necessarily the original canonical confirmSwitch tree/scope.
    need(re.fullmatch(r'[0-9]+-confirmSwitch(?:-recovered-[0-9a-f]{32})?\.json',Path(original['last_tree']['path']).name)is not None,'read-recovery-settle-original-tree')
    base,window=saved_active_window_anchor(job,original);directory=Path(job['workflow_path']).parent/'bridge-evidence';previous=original['last_tree'];last=None
    chosen=datetime.fromisoformat(next(c['at']for c in s['calls']if c['phase']=='chooseCompany'));confirmed=datetime.fromisoformat(s['calls'][-1]['at']);prior_at=chosen
    for index,entry in enumerate(reads):
        need(set(entry)=={'index','before_tree','at','command','settle_delay_seconds','reply','tree'}and type(entry['index'])is int and entry['index']==index and entry['before_tree']==previous,'read-recovery-settle-chain')
        need(entry['command']=={'op':'readonly-scope','tabId':s['tab_id'],'windowId':window}and type(entry['settle_delay_seconds'])in (int,float)and 0<entry['settle_delay_seconds']<=.25*(2**index),'read-recovery-settle-command')
        at=datetime.fromisoformat(entry['at']);need(all(t.utcoffset()is not None for t in (chosen,confirmed,at))and prior_at<=at<=confirmed,'read-recovery-settle-time')
        tp=Path(entry['tree']['path']);rp=Path(entry['reply']['path']);match=re.fullmatch('confirm-settle-'+str(index)+r'-([0-9a-f]{32})-tree\.json',tp.name)
        need(match and tp.parent==rp.parent==directory and rp.name=='confirm-settle-'+str(index)+'-'+match[1]+'-reply.json','read-recovery-settle-artifact-path')
        snapshot=document(entry['reply']);tree=document(entry['tree']);decode(snapshot,s['tab_id'],window)
        need(snapshot['tree']==tree and snapshot['before']==snapshot['after']and snapshot['ping'].get('version')==VERSION and snapshot['ping'].get('safety')=='DOM-only','read-recovery-settle-snapshot-binding')
        before=context(snapshot['before'],s['tab_id'],s['initial_groupid']);after=context(snapshot['after'],s['tab_id'],s['initial_groupid']);need(before['url']==after['url']and before.get('windowId')==after.get('windowId')==window and tree.get('url')==urlsplit(before['url'])._replace(query='',fragment='').geturl(),'read-recovery-settle-source-scope')
        windows=[w for w in snapshot['before']if w.get('windowId')==window];need(len(windows)==1 and windows[0].get('type')=='normal','read-recovery-settle-window');identity(tree,s['entry_identity']);document(previous)
        previous=entry['tree'];last=entry['reply'];prior_at=at
    need(previous==s['last_tree'],'read-recovery-settle-last-tree');return last,window

def saved_active_window_anchor(job,s):
    """A DOM source needs no activate input; use its original exact scope.
    Only the exact last confirmSwitch tree's one canonical companion is read.
    """
    from readonly_tick_snapshot import decode
    from dom_evidence import identity,context
    tree_ref=s.get('last_tree',{});treepath=Path(tree_ref.get('path',''));workflow=Path(job.get('workflow_path',''));jobpath=Path(job.get('work_order_path',''));call=s['calls'][-1];parts=call['key'].split(':')
    need(type(s.get('revision')) is int and len(parts)==2 and parts[0].isdigit() and int(parts[0])==s['revision']-1 and parts[1]=='confirmSwitch','read-recovery-anchor-revision')
    prefix=str(int(parts[0])).zfill(4)+'-confirmSwitch';directory=workflow.parent/'bridge-evidence'
    if tree_ref==((s.get('company_confirm_settle_reads')or[{}])[-1].get('tree')):
        need(workflow.is_absolute() and workflow.resolve()==workflow and not workflow.is_symlink() and workflow==jobpath.with_name('workflow.json'),'read-recovery-anchor-canonical-tree');return saved_confirm_settle_anchor(job,s)
    valid_tree=treepath.parent==directory and re.fullmatch(re.escape(prefix)+r'(?:-recovered-[0-9a-f]{32})?\.json',treepath.name) is not None
    need(workflow.is_absolute() and workflow.resolve()==workflow and not workflow.is_symlink() and workflow==jobpath.with_name('workflow.json') and valid_tree and treepath.resolve()==treepath and not treepath.is_symlink(),'read-recovery-anchor-canonical-tree')
    tree=document(tree_ref)
    if 'companyRequest'in call.get('command',{}):
        # The producer persists this exact pre-input scope with the operation and
        # call key. Equal DOM trees from other commands are not provenance.
        # B78: an intent refused before delivery is retried under the SAME key, so
        # the key alone no longer names one observation - the operation the
        # dispatched click actually carries does, and the binding check below
        # already required exactly that. Every other rule here is unchanged.
        rows=[r for r in s.get('company_configuration_observations',[])if r.get('key')==call['key']and r.get('operation')==call['command']['companyRequest']]
        # B88: the renewal writer used to append the same provenance row twice
        # (its own record plus the caller's), milliseconds apart with identical
        # key, scope and operation. That is one observation recorded twice, not
        # ambiguous provenance - different scopes or operations still refuse -
        # so exact duplicates collapse onto their earliest record and the
        # one-observation contract below keeps its meaning.
        provenance={(json.dumps(r.get('scope'),sort_keys=True),json.dumps(r.get('operation'),sort_keys=True))for r in rows}
        need(len(provenance)==1,'read-recovery-anchor-observation-not-unique');row=rows[0]
        # B93: after B87 the producer may record the settle-companion reply as
        # the observation scope when the confirm click was dispatched in the
        # same tick as its settle read (click authority = settle scope, same
        # window). The reply document is itself a full readonly snapshot and
        # the settle chain is validated by saved_confirm_settle_anchor; such a
        # companion is accepted only when it is exactly the chain's last
        # reply. Anything else still refuses.
        _reads=s.get('company_confirm_settle_reads') or []
        _companion_scope=bool(re.fullmatch(r'confirm-settle-[0-9]+-[0-9a-f]{32}-reply\.json',Path(row['scope']['path']).name) and _reads and row['scope']==_reads[-1]['reply'])
        need(set(row)=={'key','scope','operation','at'}and row['operation']==call['command']['companyRequest']and call.get('state')=='confirmed'and call.get('phase')=='confirmSwitch'and call['command'].get('op')=='click'and call['command'].get('kind')=='company-confirm','read-recovery-anchor-observation-binding')
        op=document(row['operation']);need(op.get('original_job')==ref(jobpath)and op.get('tab_id')==s['tab_id']and op.get('source_groupid')==s['initial_groupid']and op.get('source_identity')==s['entry_identity'],'read-recovery-anchor-operation-binding')
        # B78: a retried intent keeps the `at` of its original attempt, which
        # predates the operation that finally dispatched it, so that timestamp
        # cannot bound the window the click was sent under. The retry records its
        # own moment; journals written before that record fall back to this exact
        # operation's observation, taken in the same tick just before dispatch.
        sent=call.get('pre_enqueue_recovery_at',row['at'])
        need(type(sent)is str,'read-recovery-anchor-observation-time')
        times=[datetime.fromisoformat(v)for v in(op['issued_at'],row['at'],sent,op['expires_at'])]
        need(all(t.utcoffset()is not None for t in times)and times==sorted(times),'read-recovery-anchor-observation-time')
        scope_ref=row['scope'];snapshot=document(scope_ref);p=Path(scope_ref['path'])
        need(p.parent==directory and snapshot.get('scope',{}).get('windowId')==op.get('window_id'),'read-recovery-anchor-operation-window')
    else:
        # Historical unconfigured journals have no producer operation link.
        # Keep their original unique-companion contract; never guess a match.
        companions=[]
        for candidate in directory.glob(prefix+'-scope-*.json'):
            need(candidate.resolve()==candidate and not candidate.is_symlink() and re.fullmatch(re.escape(prefix)+r'-scope-[0-9a-f]{32}\.json',candidate.name),'read-recovery-anchor-canonical-scope')
            if document(ref(candidate)).get('tree')==tree:companions.append(candidate)
        need(len(companions)==1,'read-recovery-anchor-scope-not-unique');p=companions[0];scope_ref=ref(p);snapshot=document(scope_ref)
    need(p.resolve()==p and not p.is_symlink() and ((_companion_scope and re.fullmatch(r'confirm-settle-[0-9]+-[0-9a-f]{32}-reply\.json',p.name)and p.parent==directory)or re.fullmatch(re.escape(prefix)+r'-scope-[0-9a-f]{32}\.json',p.name)),'read-recovery-anchor-canonical-scope');window_id=snapshot.get('scope',{}).get('windowId');need(type(window_id) is int and window_id>0,'read-recovery-anchor-window')
    decode(snapshot,s['tab_id'],window_id)
    if _companion_scope:
        # B93: the settle reply is the authoritative snapshot of the tick that
        # dispatched the confirm click; the pre-settle tree ref in this chain
        # is a recovered derivation, so the snapshot-equality contract binds
        # the reply's own tree and identity instead.
        need(snapshot['before']==snapshot['after'] and snapshot['ping'].get('version')==VERSION and snapshot['ping'].get('safety')=='DOM-only' and document(scope_ref)==snapshot,'read-recovery-anchor-original-snapshot')
        identity(snapshot['tree'],s['entry_identity'])
        tab=context(snapshot['before'],s['tab_id'],s['initial_groupid']);windows=[w for w in snapshot['before'] if w.get('windowId')==window_id]
        need(len(windows)==1 and windows[0].get('type')=='normal' and tab.get('windowId')==window_id,'read-recovery-anchor-window-scope-invalid');return scope_ref,window_id
    need(snapshot['tree']==tree and snapshot['before']==snapshot['after'] and snapshot['ping'].get('version')==VERSION and snapshot['ping'].get('safety')=='DOM-only','read-recovery-anchor-original-snapshot')
    tab=context(snapshot['before'],s['tab_id'],s['initial_groupid']);windows=[w for w in snapshot['before'] if w.get('windowId')==window_id]
    need(len(windows)==1 and windows[0].get('type')=='normal' and tab.get('windowId')==window_id,'read-recovery-anchor-window-scope-invalid')
    identity(tree,s['entry_identity']);need(document(scope_ref)==snapshot and document(tree_ref)==tree,'read-recovery-anchor-changed');return scope_ref,window_id

def reviewed_context_epoch_chain(job,s):
    """Only the explicit one-shot review context epoch; old switch jobs are unchanged."""
    epoch=s.get('review_context_recovery')
    if epoch is None:return None
    need(type(epoch)is dict and set(epoch)=={'plan','original_prefix_count','max_epochs'}and epoch['max_epochs']==1,'read-recovery-context-marker')
    path=Path(epoch['plan']['path']);need(path.resolve()==path and not any(p.is_symlink()for p in(path,*path.parents)),'read-recovery-context-plan-path');plan=document(epoch['plan'])
    need(plan.get('kind')=='initial-review-system-error-context-recovery-plan-v1'and plan.get('recovery_action')=='reselect-original-company-once'and plan.get('max_context_epochs')==1 and plan.get('old_calls_replayed')is False,'read-recovery-context-plan-kind')
    prefix=plan['original_calls'];calls=s.get('calls',[]);count=epoch['original_prefix_count']
    need(type(count)is int and count==len(prefix)==5 and calls[:count]==prefix and plan['original_state']['calls']==prefix and plan['original_state']['revision']==plan['original_revision']==11,'read-recovery-context-original-prefix')
    need(plan['job']==ref(job['work_order_path'])and document(plan['job'])==job and plan['company']==s['company']==job['company']and plan['groupid']==str(job['groupid'])and plan['date_range']==s['date_range']and plan['bound_tab']==s['tab_id'],'read-recovery-context-job-binding')
    tail=calls[count:];phases=('context','searchCompany','chooseCompany','confirmSwitch')
    need(len(tail)==4 and tuple(c.get('phase')for c in tail)==phases and all(c.get('key')==str(12+i)+':'+phase and c.get('state')=='confirmed'for i,(c,phase)in enumerate(zip(tail,phases)))and s.get('revision')==16,'read-recovery-context-exact-confirm-tail')
    need(tail[0]['command'].get('op')=='click'and tail[0]['command'].get('kind')=='navigation'and tail[1]['command'].get('op')=='filter'and tail[1]['command'].get('kind')=='filter'and tail[1]['command'].get('value')==job['company']and all(c['command'].get('tabId')==s['tab_id']for c in tail),'read-recovery-context-search-chain')
    need(str(s['initial_groupid'])==plan['groupid']and s['entry_identity']==job['identity_baseline']and plan.get('fresh_scope')and plan.get('fresh_exit'),'read-recovery-context-same-company-identity')
    return {'plan':plan,'choose':tail[-2],'confirm':tail[-1]}

def context_confirmation_ack(job,s,call):
    """Click node is serialized AFTER click; a detached modal loses one root path.
    This is only an acknowledgement identity check, never a switch-effect proof.
    """
    cmd=call['command'];clicked=call.get('result',{}).get('clicked',{});selector=cmd.get('locator',{}).get('value');tree=document(s['last_tree']);matches=[n for n in walk(tree)if n.get('selector')==selector]
    need(len(matches)==1,'read-recovery-context-confirm-node-unique');node=matches[0]
    need(node.get('tag')=='button'and node.get('role')=='button'and node.get('name')=='确认'and node.get('disabled')is False and node.get('children')==[],'read-recovery-context-confirm-node-shape')
    need(all(clicked.get(k)==node.get(k)for k in('tag','role','name','disabled','attributes'))and call['result'].get('kind')=='company-confirm'and call['result'].get('version')==VERSION,'read-recovery-context-confirm-ack-identity')
    parts=selector.split(' > ');need(re.fullmatch(r'div:nth-of-type\([1-9][0-9]*\)',parts[0])and clicked.get('selector')==' > '.join(parts[1:]),'read-recovery-context-detached-selector')
    # The existing exact canonical tree/scope companion decoder supplies the
    # full tab/window/GID/entry identity binding; do not accept a filename alone.
    saved_active_window_anchor(job,s)
    return True

def configured_source_module(job):
    # The same canonical reviewed module as Workflow, never an arbitrary callback.
    root=Path(__file__).resolve().parents[3];scripts=root/'skills/workshop-director/scripts';need(scripts.resolve()==scripts and not any(p.is_symlink()for p in(scripts,*scripts.parents)),'read-search-module-origin')
    if str(scripts)not in sys.path:sys.path.insert(0,str(scripts))
    import execution_timing as timing
    source=document(job['company_configuration_policy'])['configuration_code'];admitted=timing.configuration_source_material(source);path=root/'skills/workshop-director/scripts/company_configuration.py';current=ref(path);need(admitted['current']==current and current['path']==source['path'],'read-search-module-source')
    module=sys.modules.get('_workflow_company_configuration')
    if module is None:
        data=path.read_bytes();need(sha(data)==current['sha256'],'read-search-module-drift');spec=importlib.util.spec_from_file_location('_workflow_company_configuration',path);module=importlib.util.module_from_spec(spec);exec(compile(data,str(path),'exec'),module.__dict__);module._WORKFLOW_SOURCE_REF=current;sys.modules['_workflow_company_configuration']=module
    need(getattr(module,'__file__',None)==str(path)and getattr(module,'_WORKFLOW_SOURCE_REF',None)==current,'read-search-loaded-module-drift')
    return module

def _typed_search_snapshot(job,s):
    return configured_source_module(job).verify_saved_search_progression(s,ref(Path(job['work_order_path'])))

def contract(job,s):
    need(job.get('identity_contract')==s.get('identity_contract')=='merchant-v2' and job.get('action') in ('acquire','return-company'),'read-recovery-contract-required')
    navigation=job.get('action')=='return-company'
    if navigation:need(return_navigation_only(job) and s.get('date_range')=={},'read-recovery-navigation-only-contract-required')
    need(s.get('version')==1 and s.get('backend')=='local-dom-bridge' and s.get('state')=='running' and s.get('phase')=='verifySwitch' and s.get('fingerprint')==fingerprint(job),'read-recovery-original-phase-required')
    need(all(s.get(k)==job.get(k) for k in ('work_order_id','company')) and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')==({} if navigation else {k:job['date_range'][k] for k in ('start','end')}),'read-recovery-binding-conflict')
    need(not any(s.get(k) for k in ('error','hold','exportPending','downloadPending','export_pending','download_pending','attempts','submittedAt','result')),'read-recovery-business-intent-forbidden')
    need(not any(c.get('stage') in ('export-intent','download-intent') for c in s.get('checkpoints',[])),'read-recovery-business-intent-forbidden')
    calls=s.get('calls',[])
    if s.get('company_search_explicit_recovery'):need(calls and _typed_search_snapshot(job,s)is not None,'read-recovery-unknown-forbidden')
    else:need(calls and all(c.get('state')=='confirmed' for c in calls),'read-recovery-unknown-forbidden')
    need(not any(c.get('command',{}).get('kind') in ('export','export-submit','download') or c.get('phase')=='submitExport' for c in calls),'read-recovery-business-intent-forbidden')
    epoch=reviewed_context_epoch_chain(job,s)
    chain=calls[s['review_context_recovery']['original_prefix_count']:]if epoch is not None else calls
    choose=[c for c in chain if c.get('phase')=='chooseCompany'];confirm=[c for c in chain if c.get('phase')=='confirmSwitch']
    need(len(choose)==len(confirm)==1 and calls.index(choose[0])<calls.index(confirm[0])==len(calls)-1,'read-recovery-confirm-chain-invalid')
    for c,label,kind in ((choose[0],job['company'],'company'),(confirm[0],'确认','company-confirm')):
        cmd=c.get('command',{});clicked=c.get('result',{}).get('clicked',{})
        need(cmd.get('op')=='click' and cmd.get('kind')==kind and cmd.get('tabId')==s['tab_id'] and cmd.get('locator',{}).get('by')=='selector' and clicked.get('name')==label and (clicked.get('selector')==cmd['locator'].get('value')or epoch is not None and c is confirm[0]and context_confirmation_ack(job,s,c)),'read-recovery-confirm-chain-invalid')
    provider=job.get('provider_baseline');known=job.get('known_company_identities',{});initial=str(s.get('initial_groupid'));target=str(job['groupid']);entry_identity=known.get(initial);target_identity=known.get(target)
    configured=job.get('company_configuration_registry')=='configured-source-index-v2'
    if configured:
        module=configured_source_module(job);config,_,original=module.job_configuration(job)
        need(s.get('company_configuration_job')==original,'read-recovery-configured-original-job')
        entry_identity=module.configured_source_identity(job,initial,config=config);target_identity=module.configured_source_identity(job,target,config=config)
    elif s.get('company_search_explicit_recovery')and entry_identity is None:
        entry_identity=sys.modules['_workflow_company_configuration'].configured_source_identity(job,initial)
    need((initial!=target or epoch is not None)and entry_identity is not None and target_identity is not None and provider==s.get('provider_baseline')==entry_identity.get('provider')==target_identity.get('provider')and s.get('entry_identity')==entry_identity and s.get('entry_groupid')==initial and job.get('identity_baseline')==target_identity,'read-recovery-identity-registry-conflict')
    focus=[c for c in calls if c.get('command',{}).get('op')=='activate' and c.get('command',{}).get('tabId')==s['tab_id']]
    anchor=None
    if focus:
        need(type(focus[0].get('result',{}).get('windowId')) is int,'read-recovery-window-anchor-required');window_id=focus[0]['result']['windowId']
    else:anchor,window_id=saved_active_window_anchor(job,s)
    error=s.get('last_error');need(error is None or (error.get('code')==error.get('message') and error.get('at') and (error['code'] in ('tab-context-changed-during-read','read-recovery-governance-source-risk') or configured and error['code']=='read-recovery-identity-registry-conflict' or epoch is not None and error['code']=='read-recovery-confirm-chain-invalid' or anchor is not None and error['code'] in ('read-recovery-window-anchor-required','read-recovery-anchor-canonical-tree','read-recovery-anchor-canonical-scope','read-recovery-anchor-source-not-active','read-recovery-anchor-scope-not-unique','read-recovery-anchor-observation-not-unique') or navigation and error['code']=='read-recovery-navigation-only-contract-required')),'read-recovery-error-not-allowed')
    scope={'tab_id':s['tab_id'],'window_id':window_id,'initial_groupid':initial,'groupid':target,'provider':provider,'allow_queryless_home':navigation}
    if anchor is not None:scope['window_anchor_ref']=anchor
    # Source URL is an original confirmed input/snapshot fact, never a new match.
    source_url=focus[0]['result'].get('url','') if focus else next(t['url'] for w in document(anchor)['before'] for t in w.get('tabs',[]) if t.get('tabId')==s['tab_id'])
    if urlsplit(source_url).path=='/p/governance/violation_list':
        governance_source_url(source_url,scope);scope['governance_source_url']=source_url
    if error and error['code']=='read-recovery-governance-source-risk':need('governance_source_url'in scope,'read-recovery-governance-error-source-required')
    return scope

def governance_source_url(url,scope):
    u=urlsplit(url);q=parse_qs(u.query,keep_blank_values=True)
    basic={'groupid','StartTime','EndTime','enter_from','ViolationReasons','IndicatorTags'};merchant={'life_biz_view_id','life_account_biz_ids'}
    need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and not u.fragment and set(q) in (basic,basic|merchant) and all(len(v)==1 for v in q.values()),'read-recovery-governance-source-risk')
    need(q['groupid']==[scope['initial_groupid']] and q['enter_from']==['home_violation_center'] and (set(q)==basic or q['life_biz_view_id']==['22'] and q['life_account_biz_ids']==['']) and q['ViolationReasons']==['[]'] and q['IndicatorTags']==[''] and all(re.fullmatch(r'[0-9]+',q[k][0])for k in ('StartTime','EndTime')) and int(q['StartTime'][0])<=int(q['EndTime'][0]),'read-recovery-governance-query-risk')
    return True

def tab_scope(tabs,scope):
    need(isinstance(tabs,list),'read-recovery-tabs-invalid');matches=[(w,t) for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==scope['tab_id']];need(len(matches)==1,'read-recovery-tab-not-unique');w,t=matches[0]
    u=urlsplit(t.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
    need(t.get('allowed') is True and u.scheme=='https' and u.netloc=='life.douyin.com' and not u.fragment and u.path in ('/p/home','/p/life_comment/management','/p/governance/violation_list'),'read-recovery-route-risk')
    if u.path=='/p/governance/violation_list':
        need(scope.get('governance_source_url')==t['url'],'read-recovery-governance-original-url-required');governance_source_url(t['url'],scope)
        need(t.get('windowId')==w.get('windowId')==scope['window_id'],'read-recovery-window-risk')
        return dict(t,groupid=scope['initial_groupid'],post_switch_home=False) # Pending only; verify_sample still requires target identity.
    basic=set(q)=={'groupid'}
    # Observed merchant home routing metadata; never a substitute for groupid.
    merchant_home=(u.path=='/p/home' and set(q)=={'groupid','life_biz_view_id','life_account_biz_ids'} and q['life_biz_view_id']==['22'] and q['life_account_biz_ids']==[''] and q.get('groupid')==[scope['groupid']])
    merchant_management=(u.path=='/p/life_comment/management' and set(q)=={'groupid','life_biz_view_id','life_account_biz_ids'} and q['life_biz_view_id']==['22'] and q['life_account_biz_ids']==[''] and q.get('groupid') in ([scope['initial_groupid']],[scope['groupid']]))
    queryless_home=u.path=='/p/home' and not u.query and scope.get('allow_queryless_home') is True
    need(queryless_home or (basic or merchant_home or merchant_management) and len(q['groupid'])==1 and q['groupid'][0] in (scope['initial_groupid'],scope['groupid']),'read-recovery-group-risk')
    need(t.get('windowId')==w.get('windowId')==scope['window_id'],'read-recovery-window-risk')
    return dict(t,groupid=None if queryless_home else q['groupid'][0],post_switch_home=queryless_home)
def home_account_company_label(tree,job):
    """HomeV3 observed name/account pair, scoped to its unique account container.
    Returns None for the legacy layout; never treats aggregate page text as a label.
    """
    allnodes=list(walk(tree))
    names=[n for n in allnodes if 'AccountInfo-module__name--' in n.get('attributes',{}).get('class','')]
    if not names:return None
    roots=[n for n in allnodes if n.get('attributes',{}).get('id')=='core-account-info']
    need(len(roots)==1 and roots[0].get('tag')=='div' and 'HomeV3' in roots[0].get('attributes',{}).get('class','') and 'AccountInfo-module__container--' in roots[0].get('attributes',{}).get('class',''),'read-recovery-company-label-unverified')
    containers=[n for n in walk({'root':roots[0],'truncated':False}) if 'AccountInfo-module__namesContainer--' in n.get('attributes',{}).get('class','')]
    need(len(containers)==1 and containers[0].get('tag')=='div','read-recovery-company-label-unverified')
    inside=list(walk({'root':containers[0],'truncated':False}));labels=[n for n in inside if 'AccountInfo-module__name--' in n.get('attributes',{}).get('class','')];accounts=[n for n in inside if 'AccountInfo-module__companyName--' in n.get('attributes',{}).get('class','')]
    need(len(names)==len(labels)==1 and names[0] is labels[0] and len(accounts)==1,'read-recovery-company-label-unverified')
    label=labels[0];account=accounts[0]
    need(label.get('tag')==account.get('tag')=='span' and label.get('children')==account.get('children')==[],'read-recovery-company-label-unverified')
    if label.get('name')==job['company']:
        need(account.get('name')==job['identity_baseline']['account_id'] and containers[0].get('name')==job['company']+' '+job['identity_baseline']['account_id'],'read-recovery-company-label-unverified')
        return label
    # The other observed HomeV3 shape displays a brand at the top and the
    # legal company (not an account ID) in the direct companyName leaf.
    brand=label.get('name');tops=[n for n in inside if 'AccountInfo-module__namesContainer__top--' in n.get('attributes',{}).get('class','')]
    need(type(brand)is str and 0<len(brand)<=160 and brand.strip()==brand and not brand.isdigit() and account.get('name')==job['company'],'read-recovery-company-label-unverified')
    need(len(tops)==1 and tops[0].get('tag')=='div' and tops[0].get('children')==[label] and tops[0].get('name')==brand and containers[0].get('children')==[tops[0],account] and containers[0].get('name')==brand+' '+job['company'],'read-recovery-company-label-unverified')
    return account

def verify_sample(job,s,sample):
    scope=contract(job,s);before=tab_scope(sample['before'],scope);after=tab_scope(sample['after'],scope);tree=sample['tree'];allnodes=list(walk(tree));u=urlsplit(after['url'])
    need(tree.get('url')==u._replace(query='',fragment='').geturl(),'read-recovery-tree-route-race')
    need(before['url']==after['url'],'read-recovery-route-unsettled')
    need(after['groupid']==scope['groupid'] or after.get('post_switch_home') is True and scope.get('allow_queryless_home') is True,'read-recovery-old-company-pending')
    titles=[n for n in allnodes if 'Profile-index-module__title--' in n.get('attributes',{}).get('class','')]
    if len(titles)==1 and titles[0].get('name')=='' and titles[0].get('children')==[] and any(prefix in titles[0].get('attributes',{}).get('class','')for prefix in ('src-components-HeaderV2-components-Profile-index-module__title--','src-components-HeaderV3-components-Profile-index-module__title--')):
        raise ValueError('read-recovery-provider-not-ready')
    if titles:need(len(titles)==1 and titles[0].get('name')==scope['provider'],'read-recovery-provider-conflict')
    if u.path=='/p/home' and not titles and not any('AccountInfo' in n.get('attributes',{}).get('class','') or 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','') for n in allnodes):raise ValueError('read-recovery-provider-not-ready')
    observed_home_label=home_account_company_label(tree,job) if u.path=='/p/home' else None
    labels=([observed_home_label] if observed_home_label is not None else [n for n in allnodes if 'AccountInfo-module__companyName--' in n.get('attributes',{}).get('class','')])
    legacy_home_v2=False
    if u.path=='/p/home' and not labels:
        roots=[n for n in allnodes if 'src-pages-HomeV2-index-module__container--' in n.get('attributes',{}).get('class','')]
        legacy_home_v2=(after.get('groupid')==scope['groupid'] and not after.get('post_switch_home') and len(roots)==1 and roots[0].get('tag')=='div' and len(titles)==1 and 'src-components-HeaderV2-components-Profile-index-module__title--' in titles[0].get('attributes',{}).get('class','') and titles[0].get('name')==scope['provider'] and titles[0].get('children')==[] and not any('HomeV3' in n.get('attributes',{}).get('class','') or 'AccountInfo' in n.get('attributes',{}).get('class','') or 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','') for n in allnodes))
    if u.path=='/p/home' and not legacy_home_v2:need(len(labels)==1 and labels[0].get('tag')=='span' and labels[0].get('name')==job['company'] and not labels[0].get('children'),'read-recovery-company-label-unverified')
    elif labels:need(len(labels)==1 and labels[0].get('name')==job['company'],'read-recovery-company-label-unverified')
    cards=[n for n in allnodes if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
    if cards:
        need(len(cards)==1,'read-recovery-card-not-unique');text=cards[0].get('name','');expected=job['identity_baseline'];need(len(text)<800,'read-recovery-card-truncated')
        accounts=re.findall(r'账户ID\s*[：:]?\s*(\d{8,})',text);managers=re.findall(r'我的客户经理\s*[：:]?\s*([^\n]+?)(?=\s*(?:切换公司|退出登录)|$)',text)
        need(sorted(set(re.findall(r'服务商\d+',text)))==[scope['provider']] and sorted(set(accounts))==[expected['account_id']] and sorted(set(m.strip() for m in managers))==[expected['manager']],'read-recovery-card-identity-risk')
    need(sample['ping'].get('safety')=='DOM-only' and sample['ping'].get('version')==VERSION,'read-recovery-version-required')
    facts={'url':after['url'],'groupid':after['groupid'],'tab_id':scope['tab_id'],'window_id':scope['window_id'],'provider_baseline':scope['provider'],'provider_observed':bool(titles or cards),'provider':(scope['provider'] if titles or cards else None),'full_identity_observed':bool(cards)}
    if legacy_home_v2:facts.update(legacy_home_v2_provisional=True,company_label_observed=False,full_identity_observed=False)
    if after.get('post_switch_home'):facts.update(target_groupid=scope['groupid'],url_groupid_observed=False)
    if 'window_anchor_ref' in scope:facts['window_anchor_ref']=scope['window_anchor_ref']
    return facts

def transient_transport(failure):
    prefix='read-recovery-transport-error:'
    if not isinstance(failure,str) or not failure.startswith(prefix):return False
    error=failure[len(prefix):]
    return (error=='Could not establish connection. Receiving end does not exist.' or
            re.fullmatch(r'Frame with id 0 was removed\.?',error,re.I) is not None or
            re.fullmatch(r'No frame with id 0 in tab \d+\.?',error,re.I) is not None)

# ---------------------------------------------------------------------------
# W131e three-state read judgement (blueprint P5). The bounded read loop used
# to spell the same error sets out inline twice - once for "wait before the
# next sample" and once for "a fresh sample may succeed" - which is exactly how
# the two lists drift apart. They are now one positive set plus one explicit
# extra member, and a single classifier decides:
#   positive -> the read is still settling; wait the backoff before resampling
#   retry    -> the read failed but another sample may succeed right away
#   None     -> hold; the caller reports the original code, unchanged
# No code is added, removed or renamed by this consolidation.
# ---------------------------------------------------------------------------
POSITIVE_SWITCH_WAIT=frozenset({'read-recovery-route-unsettled','read-recovery-tree-route-race',
                                'read-recovery-old-company-pending','read-recovery-provider-not-ready'})
RETRYABLE_SWITCH_ERRORS=POSITIVE_SWITCH_WAIT|{'read-recovery-company-label-unverified'}
def classify_switch_read(failure):
    if failure in POSITIVE_SWITCH_WAIT:return 'positive'
    if transient_transport(failure) or failure in RETRYABLE_SWITCH_ERRORS:return 'retry'
    return None

def readonly_resume_contract(job_path,expected_sha):
    """Pure admission of a saved transient hold, not permission for any input.
    A new bounded read invocation may outlive the old tick's 60s wait budget;
    its original started-at and elapsed time stay in immutable archives/proof.
    """
    job_path=Path(job_path);need(job_path.is_absolute() and job_path.is_file() and not job_path.is_symlink(),'read-resume-job-path');job=json.loads(job_path.read_bytes());path=Path(job['workflow_path']);need(path.is_absolute() and path.is_file() and not path.is_symlink() and Path(job['work_order_path'])==job_path,'read-resume-canonical-job');current_raw=path.read_bytes();need(sha(current_raw)==expected_sha,'read-resume-current-sha');current=json.loads(current_raw);refs=[]
    def pinned_history(file):
        r=ref(file);value=document(r);refs.append(r);return value
    error=current.get('last_error') or {}
    if return_navigation_only(job) and error.get('code')==error.get('message')=='read-recovery-navigation-only-contract-required':
        contract(job,current);need(not current.get('waiting_for') and not current.get('switch_read_hold'),'read-resume-return-unexpected-hold')
        document(current['last_tree']);refs.extend([current['last_tree'],ref(job_path)])
        started=datetime.fromisoformat(current['company_switch_wait_started']);failed=datetime.fromisoformat(error['at']);updated=datetime.fromisoformat(current['updated_at'])
        need(all(x.utcoffset() is not None for x in (started,failed,updated)) and started<=failed<=updated<=datetime.now(timezone.utc),'read-resume-original-time')
        need(path.read_bytes()==current_raw,'read-resume-current-concurrent-change')
        return {'historical_refs':refs,'kind':'known-formal-daily-return-contract-read-resume-v1','current_journal':ref(path),'original_journal':ref(path),'original_error':error,'original_started_at':current['company_switch_wait_started'],'elapsed_before_read_seconds':(datetime.now(timezone.utc)-started).total_seconds(),'ui_used':False,'outer_clock_reset':False}
    if current.get('phase')=='verifySwitch' and current.get('waiting_for')=='company-switch-readonly-scope' and current.get('last_error')is None and current.get('switch_read_hold',{}).get('error')in POSITIVE_SWITCH_WAIT|{'read-recovery-provider-conflict','read-recovery-company-label-unverified'}:
        pending=verified_pending_wait(job,current);started=datetime.fromisoformat(current['company_switch_wait_started'])
        need(path.read_bytes()==current_raw,'read-resume-current-concurrent-change')
        return {'kind':'known-positive-switch-read-resume-v1','historical_refs':[ref(job_path),pending['sample']],'current_journal':ref(path),'original_journal':ref(path),'original_started_at':current['company_switch_wait_started'],'elapsed_before_read_seconds':(datetime.now(timezone.utc)-started).total_seconds(),'ui_used':False,'outer_clock_reset':False}
    need(current.get('phase')=='verifySwitch' and current.get('waiting_for')=='company-switch-readonly-scope' and current.get('last_error') is None,'read-resume-original-hold-required');hold=current.get('switch_read_hold',{});need(hold.get('state')=='hold' and hold.get('ui_used') is False and hold.get('original_unchanged') is True and transient_transport(hold.get('error')),'read-resume-known-transport-required')
    oldsha=hold.get('original_journal_sha256','');need(re.fullmatch('[0-9a-f]{64}',oldsha) is not None,'read-resume-original-sha');directory=path.parent/'switch-read-recovery'/oldsha;original_ref={'path':str(directory/'original-journal.json'),'sha256':oldsha};original=document(original_ref);refs.append(original_ref);archived_job=pinned_history(directory/'original-job.json');need({k:v for k,v in archived_job.items() if k!='resume'}=={k:v for k,v in job.items() if k!='resume'},'read-resume-job-core-changed');scope=contract(job,original)
    sample_path=Path(hold['sample']['path']);need(sample_path.is_absolute() and sample_path.parent.parent==directory and re.fullmatch(r'attempt-[0-9a-f]{32}',sample_path.parent.name) and re.fullmatch(r'[0-2]-sample\.json',sample_path.name),'read-resume-canonical-sample');sample=document(hold['sample']);refs.append(hold['sample']);need(sample.get('kind')=='company-switch-readonly-sample-v1' and sample.get('error',{}).get('code')==hold['error'],'read-resume-original-error');commands=[{'op':'tabs'},{'op':'ping','tabId':scope['tab_id']},{'op':'tree','tabId':scope['tab_id']},{'op':'tabs'}];n=len(sample.get('commands',[]));need(1<=n<=4 and sample['commands']==commands[:n],'read-resume-readonly-command-prefix');keys=['before','ping','tree','after'];index=sample_path.name.split('-')[0]
    for i,key in enumerate(keys[:n]):
        transport=pinned_history(sample_path.parent/(index+'-'+key+'-transport.json'))
        if i==n-1:need(type(transport) is dict and transport.get('ok') is False and 'read-recovery-transport-error:'+str(transport.get('error'))==hold['error'],'read-resume-transport-failure-binding')
        else:
            value=transport.get('result') if type(transport) is dict and 'ok' in transport else transport;need(not(type(transport) is dict and 'ok' in transport) or transport.get('ok') is True,'read-resume-prior-read-failed');need(sample.get(key)==value==pinned_history(sample_path.parent/(index+'-'+key+'.json')),'read-resume-transport-sample-changed')
    if 'before' in sample:tab_scope(sample['before'],scope)
    if 'after' in sample:tab_scope(sample['after'],scope)
    expected=copy.deepcopy(original);expected.update(waiting_for='company-switch-readonly-scope',switch_read_hold=hold,updated_at=current.get('updated_at'));need(current==expected,'read-resume-current-delta');started=datetime.fromisoformat(original['company_switch_wait_started']);sample_at=datetime.fromisoformat(sample['at']);updated=datetime.fromisoformat(current['updated_at']);need(all(x.utcoffset() is not None for x in (started,sample_at,updated)) and started<=sample_at<=updated<=datetime.now(timezone.utc),'read-resume-original-time')
    for history in refs:document(history)
    need(path.read_bytes()==current_raw,'read-resume-current-concurrent-change')
    return {'historical_refs':refs,'kind':'known-switch-transport-read-resume-v1','current_journal':ref(path),'original_journal':original_ref,'original_hold':hold,'original_started_at':original['company_switch_wait_started'],'elapsed_before_read_seconds':(datetime.now(timezone.utc)-started).total_seconds(),'ui_used':False,'outer_clock_reset':False}

MERCHANT_ROUTE_FAILURE_SHA='a6194883015889f6682e1102f0c3489fc35180b990f4890d888e906f124b6929'
def merchant_route_resume_contract(job_path,expected_sha,failure_ref):
    """Reviewed semantic tabs-only rejection, never a transport retry grant.
    The old sample/hold/started_at remain evidence; no input or clock reset.
    """
    need(failure_ref.get('sha256')==MERCHANT_ROUTE_FAILURE_SHA,'merchant-read-resume-failure-not-reviewed');failure=document(failure_ref)
    job_path=Path(job_path);need(job_path.is_absolute() and not job_path.is_symlink() and ref(job_path)==failure['job'],'merchant-read-resume-original-job');job=json.loads(job_path.read_bytes());path=Path(job['workflow_path']);current_raw=path.read_bytes();need(path.is_absolute() and not path.is_symlink() and ref(path)==failure['workflow'] and sha(current_raw)==expected_sha and Path(job['work_order_path'])==job_path,'merchant-read-resume-original-journal');current=json.loads(current_raw)
    need(formal_daily_return(job) and current.get('phase')=='verifySwitch' and current.get('waiting_for')=='company-switch-readonly-scope' and current.get('last_error') is None,'merchant-read-resume-original-hold')
    hold=current.get('switch_read_hold',{});need(hold==failure['hold'] and hold.get('state')=='hold' and hold.get('error')=='read-recovery-group-risk' and hold.get('ui_used') is False and hold.get('original_unchanged') is True,'merchant-read-resume-exact-semantic-hold')
    oldsha=hold.get('original_journal_sha256','');need(re.fullmatch('[0-9a-f]{64}',oldsha) is not None,'merchant-read-resume-original-sha');directory=path.parent/'switch-read-recovery'/oldsha;original_ref={'path':str(directory/'original-journal.json'),'sha256':oldsha};original=document(original_ref);refs=[failure_ref,ref(job_path),original_ref]
    jobref=ref(directory/'original-job.json');need(document(jobref)==job,'merchant-read-resume-job-core-changed');refs.append(jobref);scope=contract(job,original)
    sample_path=Path(hold['sample']['path']);need(sample_path.is_absolute() and sample_path.parent.parent==directory and re.fullmatch(r'attempt-[0-9a-f]{32}',sample_path.parent.name) and sample_path.name=='0-sample.json','merchant-read-resume-canonical-sample');sample=document(hold['sample']);refs.append(hold['sample'])
    need(sample.get('kind')=='company-switch-readonly-sample-v1' and sample.get('commands')==[{'op':'tabs'}] and set(sample)=={'kind','at','commands','before','error'} and sample['error'].get('code')==hold['error'],'merchant-read-resume-tabs-only-prefix')
    transport_ref=ref(sample_path.with_name('0-before-transport.json'));before_ref=ref(sample_path.with_name('0-before.json'));transport=document(transport_ref);before=document(before_ref);refs.extend([transport_ref,before_ref]);need(type(transport) is dict and transport.get('ok') is True and transport.get('result')==before==sample['before'],'merchant-read-resume-successful-tabs-binding')
    tab=tab_scope(before,scope);u=urlsplit(tab['url']);q=parse_qs(u.query,keep_blank_values=True)
    need(u.path=='/p/life_comment/management' and set(q)=={'groupid','life_biz_view_id','life_account_biz_ids'} and q['life_biz_view_id']==['22'] and q['life_account_biz_ids']==[''] and q['groupid']==[scope['initial_groupid']],'merchant-read-resume-observed-metadata-required')
    expected=copy.deepcopy(original);expected.update(waiting_for='company-switch-readonly-scope',switch_read_hold=hold,updated_at=current.get('updated_at'));need(current==expected,'merchant-read-resume-current-delta')
    started=datetime.fromisoformat(original['company_switch_wait_started']);sample_at=datetime.fromisoformat(sample['at']);updated=datetime.fromisoformat(current['updated_at']);need(all(x.utcoffset() is not None for x in (started,sample_at,updated)) and started<=sample_at<=updated<=datetime.now(timezone.utc),'merchant-read-resume-original-time')
    for r in refs:document(r)
    need(path.read_bytes()==current_raw,'merchant-read-resume-concurrent-change')
    return {'kind':'known-switch-merchant-metadata-read-resume-v1','historical_refs':refs,'current_journal':ref(path),'original_journal':original_ref,'original_hold':hold,'original_started_at':original['company_switch_wait_started'],'elapsed_before_read_seconds':(datetime.now(timezone.utc)-started).total_seconds(),'ui_used':False,'outer_clock_reset':False}

CONFIRM_ANCHOR_FAILURE_SHA='dff5a561d30c5a20412eef3da99c97ec2e62ed4e5f4052823e5c083aa7b09b4a'
def confirm_anchor_resume_contract(job_path,expected_sha,failure_ref):
    need(failure_ref.get('sha256')==CONFIRM_ANCHOR_FAILURE_SHA,'confirm-anchor-failure-not-reviewed');failure=document(failure_ref)
    job_path=Path(job_path);need(job_path.is_absolute() and job_path.resolve()==job_path and not job_path.is_symlink() and ref(job_path)==failure['job'],'confirm-anchor-original-job');job=document(failure['job']);path=Path(job['workflow_path']);need(ref(path)==failure['workflow'] and expected_sha==failure['workflow']['sha256'] and Path(job['work_order_path'])==job_path,'confirm-anchor-original-journal');s=document(failure['workflow'])
    need(s.get('phase')=='verifySwitch' and s.get('revision')==failure['workflow_revision']==5 and s.get('calls')==failure['workflow_calls'] and len(s['calls'])==failure['confirmed_count']==4 and all(c.get('state')=='confirmed' for c in s['calls']) and s.get('last_error')==failure['last_error'] and s['last_error']['code']==s['last_error']['message']=='read-recovery-anchor-canonical-tree' and s.get('last_tree')==failure['last_tree'] and s.get('company_switch_wait_started')==failure['original_wait_started'],'confirm-anchor-exact-preinput-frontier')
    scope=contract(job,s);need(scope.get('window_anchor_ref')==failure['scope'] and document(failure['scope'])['tree']==document(s['last_tree']),'confirm-anchor-scope-binding')
    return {'kind':'known-confirm-switch-anchor-read-resume-v1','failure':failure_ref,'job':failure['job'],'journal':failure['workflow'],'tree':s['last_tree'],'scope':failure['scope'],'ui_used':False,'new_mutations':0,'outer_clock_reset':False}

def reconcile(job_path,expected_sha,invoke,max_samples=3):
    """At most three fresh read-only samples per explicit call, never an input."""
    need(max_samples>=3,'read-recovery-bounded-contract');job_path=Path(job_path).resolve();jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);raw=path.read_bytes();s=json.loads(raw)
    directory=path.parent/'switch-read-recovery'/expected_sha
    original_path=directory/'original-journal.json'
    if original_path.exists():
        original=original_path.read_bytes();need(sha(original)==expected_sha,'read-recovery-original-changed');need(raw==original,'read-recovery-current-original-changed')
    else:need(sha(raw)==expected_sha,'read-recovery-original-sha-required');original=raw
    need(path.is_absolute() and not path.is_symlink() and Path(job.get('work_order_path','')).resolve()==job_path,'read-recovery-canonical-path-required')
    scope=contract(job,s);immutable(original_path,original);jobref=immutable(directory/'original-job.json',jobraw)
    oldtree=s.get('last_tree');document(oldtree);oldref=immutable(directory/'original-tree.json',Path(oldtree['path']).read_bytes())
    attempt=directory/('attempt-'+uuid.uuid4().hex);attempt.mkdir(parents=True)
    read_deadline=time.monotonic()+86400 # B82: no artificial time shackle on readonly sampling.
    for i in range(max_samples):
        sample={'kind':'company-switch-readonly-sample-v1','at':now(),'commands':[]};failure=None
        def call(cmd,key):
            sample['commands'].append(cmd);value=invoke(cmd);immutable(attempt/(str(i)+'-'+key+'-transport.json'),encoded(value))
            if isinstance(value,dict) and 'ok' in value:
                need(value.get('ok') is True,'read-recovery-transport-error:'+str(value.get('error','unknown')));value=value['result']
            sample[key]=value;immutable(attempt/(str(i)+'-'+key+'.json'),encoded(value));return value
        try:
            before=call({'op':'tabs'},'before');tab_scope(before,scope)
            call({'op':'ping','tabId':scope['tab_id']},'ping')
            call({'op':'tree','tabId':scope['tab_id']},'tree')
            after=call({'op':'tabs'},'after');tab_scope(after,scope)
            facts=verify_sample(job,s,sample)
        except Exception as e:failure=str(e);sample['error']={'code':failure,'at':now()}
        positive_wait=failure is not None and classify_switch_read(failure)=='positive' and i+1<max_samples
        delay=min(.25*(2**i),2.0) if positive_wait else 0
        budget_ok=not positive_wait or time.monotonic()+delay<=read_deadline
        if positive_wait:sample['readonly_wait']={'seconds_before_next_sample':delay if budget_ok else 0,'budget_exhausted':not budget_ok}
        sample_ref=immutable(attempt/(str(i)+'-sample.json'),encoded(sample))
        if failure:
            retryable=failure is not None and classify_switch_read(failure) in ('positive','retry')
            if retryable and i+1<max_samples and budget_ok:
                if positive_wait:time.sleep(delay) # Ready/error risks never incur this delay.
                continue
            return {'state':'hold','error':failure,'original_journal_sha256':expected_sha,'sample':sample_ref,'ui_used':False,'original_unchanged':path.read_bytes()==original}
        proof={'kind':KIND,'at':now(),'job':jobref,'original_journal':ref(original_path),'original_tree':oldref,'original_tree_ref':oldtree,'sample':sample_ref,'facts':facts,'calls_sha256':sha(encoded(s['calls'])),'next_phase':'accountAfterSwitch','ui_used':False,'new_mutations':0}
        if 'window_anchor_ref' in scope:proof['window_anchor_ref']=scope['window_anchor_ref']
        proofref=immutable(attempt/'recovery-proof.json',encoded(proof));new=copy.deepcopy(s)
        if new.get('last_error'):new.setdefault('resolved_errors',[]).append({**new.pop('last_error'),'resolved_at':proof['at'],'next_phase':'accountAfterSwitch','recovery_proof':proofref})
        new['phase']='accountAfterSwitch';new['revision']+=1;new['last_tree']=ref(attempt/(str(i)+'-tree.json'));new['switch_read_recovery']=proofref;new.pop('waiting_for',None);new.pop('company_switch_wait_started',None);new['updated_at']=proof['at']
        need(path.read_bytes()==original and job_path.read_bytes()==jobraw,'read-recovery-original-concurrent-change')
        verify_recovered(new,proofref)
        temporary=path.with_name(path.name+'.read-recovery-'+uuid.uuid4().hex);immutable(temporary,encoded(new));os.replace(temporary,path)
        return {'state':'reconciled','journal':ref(path),'proof':proofref,'phase':new['phase'],'ui_used':False}

def verify_recovered(current,proof_ref):
    proof=document(proof_ref);need(proof.get('kind')==KIND and proof.get('ui_used') is False and proof.get('new_mutations')==0 and proof.get('next_phase')=='accountAfterSwitch','read-recovery-proof-invalid')
    original=document(proof['original_journal']);job=document(proof['job']);scope=contract(job,original);need(proof.get('window_anchor_ref')==scope.get('window_anchor_ref'),'read-recovery-anchor-proof-binding');sample=document(proof['sample']);facts=verify_sample(job,original,sample)
    need(proof['facts']==facts and proof['original_tree_ref']==original.get('last_tree') and document(proof['original_tree'])==document(proof['original_tree_ref']),'read-recovery-proof-binding-invalid')
    need(sample['commands']==[{'op':'tabs'},{'op':'ping','tabId':original['tab_id']},{'op':'tree','tabId':original['tab_id']},{'op':'tabs'}],'read-recovery-nonread-command')
    expected=copy.deepcopy(original)
    if expected.get('last_error'):expected.setdefault('resolved_errors',[]).append({**expected.pop('last_error'),'resolved_at':proof['at'],'next_phase':'accountAfterSwitch','recovery_proof':proof_ref})
    expected.update(phase='accountAfterSwitch',revision=original['revision']+1,last_tree=ref(Path(proof['sample']['path']).with_name(Path(proof['sample']['path']).name.replace('-sample.json','-tree.json'))),switch_read_recovery=proof_ref,updated_at=proof['at']);expected.pop('waiting_for',None);expected.pop('company_switch_wait_started',None)
    need(document(expected['last_tree'])==sample['tree'],'read-recovery-tree-copy-changed')
    need(current==expected and sha(encoded(current['calls']))==proof['calls_sha256'],'read-recovery-current-journal-changed')
    return {'kind':KIND,'original_journal':proof['original_journal'],'proof':proof_ref,'facts':facts,'original_calls':original['calls'],'original_error':original.get('last_error')}

def verified_pending_wait(job,state):
    """A complete, bounded readonly observation may be pending, never done."""
    need(state.get('state')=='running' and state.get('phase')=='verifySwitch' and state.get('waiting_for')=='company-switch-readonly-scope' and state.get('last_error')is None,'read-recovery-pending-state')
    scope=contract(job,state);hold=state.get('switch_read_hold',{});need(hold.get('state')=='hold' and hold.get('error')in POSITIVE_SWITCH_WAIT|{'read-recovery-provider-conflict','read-recovery-company-label-unverified'} and hold.get('ui_used')is False and hold.get('original_unchanged')is True,'read-recovery-positive-pending-required')
    oldsha=hold.get('original_journal_sha256','');need(re.fullmatch('[0-9a-f]{64}',oldsha)is not None,'read-recovery-pending-original-sha');directory=Path(job['workflow_path']).parent/'switch-read-recovery'/oldsha;original=document({'path':str(directory/'original-journal.json'),'sha256':oldsha});need(document(ref(directory/'original-job.json'))==job and contract(job,original)==scope,'read-recovery-pending-original-job')
    samplepath=Path(hold['sample']['path']);need(samplepath.parent.parent==directory and re.fullmatch('attempt-[0-9a-f]{32}',samplepath.parent.name)is not None and re.fullmatch('[0-2]-sample.json',samplepath.name)is not None,'read-recovery-pending-canonical-sample');sample=document(hold['sample'])
    need(sample.get('kind')=='company-switch-readonly-sample-v1' and sample.get('commands')==[{'op':'tabs'},{'op':'ping','tabId':scope['tab_id']},{'op':'tree','tabId':scope['tab_id']},{'op':'tabs'}] and sample.get('error',{}).get('code')==hold['error'] and sample.get('ping',{}).get('version')==VERSION and sample.get('ping',{}).get('safety')=='DOM-only','read-recovery-pending-exact-readonly-sample')
    for name in ('before','ping','tree','after'):
        saved=samplepath.with_name(samplepath.name.replace('-sample.json','-'+name+'.json'));transport=samplepath.with_name(samplepath.name.replace('-sample.json','-'+name+'-transport.json'));value=document(ref(saved));reply=document(ref(transport));need(value==sample[name] and reply.get('ok')is True and reply.get('result')==value,'read-recovery-pending-transport-binding')
    try:verify_sample(job,original,sample)
    except ValueError as error:need((str(error)==hold['error']and str(error)in POSITIVE_SWITCH_WAIT)or(hold['error']=='read-recovery-provider-conflict'and str(error)=='read-recovery-provider-not-ready')or(hold['error']=='read-recovery-company-label-unverified'and str(error)=='read-recovery-provider-not-ready'),'read-recovery-pending-observation-conflict')
    else:raise ValueError('read-recovery-pending-cannot-claim-complete')
    expected=copy.deepcopy(original);expected.update(waiting_for='company-switch-readonly-scope',switch_read_hold=hold,updated_at=state.get('updated_at'));need(state==expected,'read-recovery-pending-metadata-conflict')
    return {'kind':'verified-company-switch-positive-readonly-pending-v1','journal_phase':'verifySwitch','sample':hold['sample'],'done':False,'input_replayed':False}

def governance_route_resume_facts(job,current,held_ref,hold_ref):
    """Pure archived semantic-hold facts; caller authenticates held dictionary bytes.
    It never reads the mutable canonical workflow/job; all material below is the
    original switch-read archive. held_ref retains original canonical provenance.
    """
    job_path=Path(job['work_order_path']);path=Path(job['workflow_path'])
    need(job_path.is_absolute() and job_path.resolve()==job_path and path==job_path.with_name('workflow.json') and held_ref.get('path')==str(path) and re.fullmatch('[0-9a-f]{64}',held_ref.get('sha256',''))is not None,'governance-read-resume-canonical-provenance')
    need(current.get('phase')=='verifySwitch' and current.get('state')=='running' and current.get('waiting_for')=='company-switch-readonly-scope' and current.get('last_error')is None,'governance-read-resume-original-hold')
    hold=current.get('switch_read_hold',{});need(hold.get('state')=='hold' and hold.get('error')=='read-recovery-route-risk' and hold.get('sample')==hold_ref and hold.get('ui_used')is False and hold.get('original_unchanged')is True,'governance-read-resume-exact-semantic-hold')
    oldsha=hold.get('original_journal_sha256','');need(re.fullmatch('[0-9a-f]{64}',oldsha)is not None,'governance-read-resume-original-sha');directory=path.parent/'switch-read-recovery'/oldsha;original_ref={'path':str(directory/'original-journal.json'),'sha256':oldsha};original=document(original_ref);job_ref=ref(directory/'original-job.json');need(document(job_ref)==job,'governance-read-resume-original-job');scope=contract(job,original)
    sample_path=Path(hold_ref['path']);need(sample_path.is_absolute() and sample_path.resolve()==sample_path and not sample_path.is_symlink() and sample_path.parent.parent==directory and re.fullmatch('attempt-[0-9a-f]{32}',sample_path.parent.name)is not None and sample_path.name=='0-sample.json','governance-read-resume-canonical-sample');sample=document(hold_ref)
    need(set(sample)=={'kind','at','commands','before','error'} and sample['kind']=='company-switch-readonly-sample-v1' and sample['commands']==[{'op':'tabs'}] and sample['error'].get('code')==hold['error'],'governance-read-resume-tabs-only-prefix')
    transport_ref=ref(sample_path.with_name('0-before-transport.json'));before_ref=ref(sample_path.with_name('0-before.json'));transport=document(transport_ref);before=document(before_ref);need(transport.get('ok')is True and transport.get('result')==before==sample['before'],'governance-read-resume-successful-tabs-binding')
    tab=tab_scope(before,scope);need(tab['url']==scope.get('governance_source_url') and tab['groupid']==scope['initial_groupid'] and urlsplit(tab['url']).path=='/p/governance/violation_list','governance-read-resume-original-source-pending')
    expected=copy.deepcopy(original);expected.update(waiting_for='company-switch-readonly-scope',switch_read_hold=hold,updated_at=current.get('updated_at'));need(current==expected,'governance-read-resume-current-delta')
    started=datetime.fromisoformat(original['company_switch_wait_started']);observed=datetime.fromisoformat(sample['at']);updated=datetime.fromisoformat(current['updated_at']);need(all(t.utcoffset()is not None for t in (started,observed,updated)) and started<=observed<=updated<=datetime.now(timezone.utc),'governance-read-resume-original-time')
    return {'kind':'known-confirmed-governance-source-readonly-resume-v1','current_journal':held_ref,'original_journal':original_ref,'original_hold':hold,'original_started_at':original['company_switch_wait_started'],'historical_refs':[job_ref,original_ref,hold_ref,transport_ref,before_ref],'ui_used':False,'input_replayed':False,'outer_clock_reset':False,'pending_is_not_workflow_resume':True}

def governance_route_resume_contract(job_path,expected_sha,hold_ref):
    """Live oldSHA qualification before one existing bounded readonly reconcile.
    A pending result never permits the expired ordinary workflow tick.
    """
    job_path=Path(job_path);need(job_path.is_absolute() and job_path.resolve()==job_path and not job_path.is_symlink(),'governance-read-resume-canonical-job');jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);need(path.is_absolute() and path.resolve()==path and not path.is_symlink() and Path(job['work_order_path'])==job_path,'governance-read-resume-canonical-workflow');raw=path.read_bytes();need(sha(raw)==expected_sha,'governance-read-resume-original-sha')
    facts=governance_route_resume_facts(job,json.loads(raw),{'path':str(path),'sha256':sha(raw)},hold_ref)
    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'governance-read-resume-concurrent-change')
    return facts


def governance_source_resume_facts(job,current,held_ref):
    """Pure qualification of a source-schema failure before fresh switch reads.
    Caller authenticates held bytes. This never clears error, resets the timer,
    resolves identity or dispatches input; only existing reconcile may advance.
    """
    path=Path(job['workflow_path']);jobpath=Path(job['work_order_path'])
    need(path.is_absolute() and path.resolve()==path and path==jobpath.with_name('workflow.json') and jobpath.is_absolute() and jobpath.resolve()==jobpath and held_ref.get('path')==str(path) and re.fullmatch('[0-9a-f]{64}',held_ref.get('sha256',''))is not None,'governance-source-resume-canonical-binding')
    error=current.get('last_error',{})
    need(set(error)=={'at','code','message'} and error['code']==error['message']=='read-recovery-governance-source-risk' and not current.get('waiting_for') and not current.get('switch_read_hold') and not current.get('switch_read_recovery'),'governance-source-resume-exact-pre-read-error')
    scope=contract(job,current);need('governance_source_url'in scope,'governance-source-resume-original-url-required')
    started=datetime.fromisoformat(current['company_switch_wait_started']);at=datetime.fromisoformat(error['at']);updated=datetime.fromisoformat(current['updated_at']);confirmed=datetime.fromisoformat(current['calls'][-1]['at'])
    need(all(t.utcoffset()is not None for t in (started,at,updated,confirmed)) and confirmed<=started<=at<=updated<=datetime.now(timezone.utc),'governance-source-resume-original-time')
    tree=current['last_tree'];document(tree);evidence=[tree]
    if 'window_anchor_ref'in scope:evidence.append(scope['window_anchor_ref'])
    return {'kind':'known-confirmed-governance-source-schema-readonly-resume-v1','current_journal':held_ref,'scope':scope,'original_error':error,'original_started_at':current['company_switch_wait_started'],'calls_sha256':sha(encoded(current['calls'])),'historical_refs':evidence,'ui_used':False,'input_replayed':False,'outer_clock_reset':False,'identity_effect_verified':False,'requires_explicit_readonly_reconcile':True}

def governance_source_resume_contract(job_path,expected_sha):
    job_path=Path(job_path);need(job_path.is_absolute() and job_path.resolve()==job_path and not job_path.is_symlink(),'governance-source-resume-canonical-job');jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);need(path.is_absolute() and path.resolve()==path and not path.is_symlink() and Path(job['work_order_path'])==job_path,'governance-source-resume-canonical-workflow');raw=path.read_bytes();need(sha(raw)==expected_sha,'governance-source-resume-original-sha')
    facts=governance_source_resume_facts(job,json.loads(raw),{'path':str(path),'sha256':sha(raw)})
    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'governance-source-resume-concurrent-change');return facts

def dom_anchor_resume_facts(job,current,held_ref):
    """Pure original confirmed-switch DOM-anchor failure admission, no read/input."""
    path=Path(job['workflow_path']);jobpath=Path(job['work_order_path'])
    need(path.is_absolute() and path.resolve()==path and path==jobpath.with_name('workflow.json') and jobpath.is_absolute() and jobpath.resolve()==jobpath and held_ref.get('path')==str(path) and re.fullmatch('[0-9a-f]{64}',held_ref.get('sha256','')) is not None,'dom-anchor-resume-canonical-binding')
    error=current.get('last_error',{})
    need(set(error)=={'at','code','message'} and error['code']==error['message']=='read-recovery-anchor-source-not-active' and not any(current.get(k) for k in ('waiting_for','switch_read_hold','switch_read_recovery')),'dom-anchor-resume-exact-pre-read-error')
    scope=contract(job,current);need('window_anchor_ref' in scope,'dom-anchor-resume-saved-scope-required')
    times=[datetime.fromisoformat(x) for x in (current['calls'][-1]['at'],current['company_switch_wait_started'],error['at'],current['updated_at'])]
    need(all(t.utcoffset() is not None for t in times) and times==sorted(times) and times[-1]<=datetime.now(timezone.utc),'dom-anchor-resume-original-time')
    return {'kind':'known-confirmed-switch-dom-anchor-readonly-resume-v1','current_journal':held_ref,'scope':scope,'original_error':error,'original_started_at':current['company_switch_wait_started'],'calls_sha256':sha(encoded(current['calls'])),'historical_refs':[current['last_tree'],scope['window_anchor_ref']],'ui_used':False,'input_replayed':False,'outer_clock_reset':False,'identity_effect_verified':False,'requires_explicit_readonly_reconcile':True}

def dom_anchor_resume_contract(job_path,expected_sha):
    job_path=Path(job_path);need(job_path.is_absolute() and job_path.resolve()==job_path and not job_path.is_symlink(),'dom-anchor-resume-canonical-job');jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);need(path.is_absolute() and path.resolve()==path and not path.is_symlink() and Path(job['work_order_path'])==job_path,'dom-anchor-resume-canonical-workflow');raw=path.read_bytes();need(sha(raw)==expected_sha,'dom-anchor-resume-original-sha')
    facts=dom_anchor_resume_facts(job,json.loads(raw),{'path':str(path),'sha256':sha(raw)})
    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'dom-anchor-resume-concurrent-change');return facts

def confirm_settle_anchor_resume_contract(job_path,expected_sha):
    job_path=Path(job_path);need(job_path.is_absolute()and job_path.resolve()==job_path and not job_path.is_symlink(),'settle-anchor-resume-canonical-job');jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);need(path.is_absolute()and path.resolve()==path and not path.is_symlink()and Path(job['work_order_path'])==job_path,'settle-anchor-resume-canonical-workflow');raw=path.read_bytes();need(sha(raw)==expected_sha,'settle-anchor-resume-original-sha');s=json.loads(raw)
    error=s.get('last_error',{});need(set(error)=={'at','code','message'}and error['code']==error['message']=='read-recovery-anchor-canonical-tree'and not any(s.get(k)for k in ('waiting_for','switch_read_hold','switch_read_recovery')),'settle-anchor-resume-exact-error')
    scope=contract(job,s);need(s.get('company_confirm_settle_reads')and scope.get('window_anchor_ref')==s['company_confirm_settle_reads'][-1]['reply'],'settle-anchor-resume-explicit-chain')
    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'settle-anchor-resume-concurrent-change');return {'kind':'known-confirm-settle-anchor-readonly-resume-v1','current_journal':{'path':str(path),'sha256':sha(raw)},'scope':scope,'original_error':error,'original_started_at':s['company_switch_wait_started'],'original_calls':s['calls'],'ui_used':False,'input_replayed':False,'identity_effect_verified':False,'outer_clock_reset':False}

def observation_anchor_resume_contract(job_path,expected_sha):
    """B79: one-shot admission of the failed pre-read anchor, no read and no input.

    W132q fixed why the anchor could not name ONE observation (a retried intent
    keeps its call key), but the journal still carried that error name, and the
    anchor gate below only admitted the *other* anchor failures - so the very
    next line refused the run with `read-recovery-error-not-allowed`, and the
    tick's own `explicit-switch-read-reconciliation-required` guard kept the unit
    from ever asking again. This admission binds the exact saved failure (code,
    original journal bytes, the confirmed confirmSwitch call and its declared
    successor continuation, the successor's own scope), and reconcile moves the
    error into resolved_errors, so this exact frontier exists once.
    """
    job_path=Path(job_path);need(job_path.is_absolute()and job_path.resolve()==job_path and not job_path.is_symlink(),'observation-anchor-resume-canonical-job');jobraw=job_path.read_bytes();job=json.loads(jobraw);path=Path(job['workflow_path']);need(path.is_absolute()and path.resolve()==path and not path.is_symlink()and Path(job['work_order_path'])==job_path,'observation-anchor-resume-canonical-workflow');raw=path.read_bytes();need(sha(raw)==expected_sha,'observation-anchor-resume-original-sha');s=json.loads(raw)
    error=s.get('last_error',{});need(set(error)=={'at','code','message'}and error['code']==error['message']=='read-recovery-anchor-observation-not-unique'and not any(s.get(k)for k in ('waiting_for','switch_read_hold','switch_read_recovery')),'observation-anchor-resume-exact-error')
    calls=s.get('calls')or[];need(calls and calls[-1].get('phase')=='confirmSwitch'and calls[-1].get('state')=='confirmed'and 'companyRequest'in calls[-1].get('command',{}),'observation-anchor-resume-confirmed-frontier')
    continuation=calls[-1].get('pre_enqueue_operation_continuation')or{};need(continuation.get('kind')=='owned-undelivered-operation-successor-v1'and continuation.get('successor')==calls[-1]['command']['companyRequest'],'observation-anchor-resume-continuation-required')
    document(continuation['predecessor']);document(continuation['scope'])
    scope=contract(job,s);need(scope.get('window_anchor_ref')==continuation['scope'],'observation-anchor-resume-scope-binding')
    times=[datetime.fromisoformat(x)for x in (calls[-1]['at'],s['company_switch_wait_started'],error['at'],s['updated_at'])];need(all(t.utcoffset()is not None for t in times)and times==sorted(times),'observation-anchor-resume-original-time')
    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'observation-anchor-resume-concurrent-change')
    return {'kind':'known-confirmed-switch-observation-anchor-readonly-resume-v1','current_journal':{'path':str(path),'sha256':sha(raw)},'scope':scope,'original_error':error,'original_started_at':s['company_switch_wait_started'],'original_calls':calls,'ui_used':False,'input_replayed':False,'identity_effect_verified':False,'outer_clock_reset':False}

def main():
    a=argparse.ArgumentParser();a.add_argument('--work-order',type=Path,required=True);a.add_argument('--original-sha256',required=True);a.add_argument('--merchant-metadata-failure',type=Path);a.add_argument('--merchant-metadata-failure-sha256');a.add_argument('--confirm-anchor-failure',type=Path);a.add_argument('--confirm-anchor-failure-sha256');a.add_argument('--governance-route-hold',type=Path);a.add_argument('--governance-route-hold-sha256');a.add_argument('--governance-source-schema-failure',action='store_true');a.add_argument('--dom-anchor-scope-failure',action='store_true');a.add_argument('--confirm-settle-anchor-failure',action='store_true');a.add_argument('--observation-anchor-failure',action='store_true');args=a.parse_args()
    import importlib.util
    p=Path(__file__).resolve().parents[3]/'skills/chrome-dom-export/scripts/bridge.py';spec=importlib.util.spec_from_file_location('switch_readonly_bridge',p);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    import fcntl
    job=json.loads(args.work_order.read_bytes());lock=Path(job['workflow_path']).with_name('.bridge-execution.lock')
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.merchant_metadata_failure is not None:
            merchant_route_resume_contract(args.work_order,args.original_sha256,{'path':str(args.merchant_metadata_failure.absolute()),'sha256':args.merchant_metadata_failure_sha256})
        if args.confirm_anchor_failure is not None:
            confirm_anchor_resume_contract(args.work_order,args.original_sha256,{'path':str(args.confirm_anchor_failure.absolute()),'sha256':args.confirm_anchor_failure_sha256})
        if args.governance_route_hold is not None:
            governance_route_resume_contract(args.work_order,args.original_sha256,{'path':str(args.governance_route_hold.absolute()),'sha256':args.governance_route_hold_sha256})
        if args.governance_source_schema_failure:governance_source_resume_contract(args.work_order,args.original_sha256)
        if args.dom_anchor_scope_failure:dom_anchor_resume_contract(args.work_order,args.original_sha256)
        if args.confirm_settle_anchor_failure:confirm_settle_anchor_resume_contract(args.work_order,args.original_sha256)
        if args.observation_anchor_failure:observation_anchor_resume_contract(args.work_order,args.original_sha256)
        def invoke(cmd):
            return b.request(cmd,timeout=50)
        print(json.dumps(reconcile(args.work_order,args.original_sha256,invoke),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
