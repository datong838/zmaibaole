"""Local dispatch binding and pure completion adapter. Never starts a child/UI."""
import argparse,json,hashlib,os,tempfile
import ast,contextvars,sys,types
from pathlib import Path
import director as d
import daily_dispatch_order as dispatch
import daily_execution_launcher as parent
import execution_timing as t
PROJECT=Path(__file__).resolve().parents[3]

def offer_path(root,dispatch_id):return Path(root)/'dispatch-offers'/(hashlib.sha256(dispatch_id.encode()).hexdigest()+'.json')
def launch_commands(order_ref,root,mode='acceptance'):
    python=PROJECT/'skills/daily-comment-stats/.venv/bin/python';launcher=Path(__file__).with_name('daily_execution_launcher.py')
    common=['--order',order_ref['path'],'--order-sha256',order_ref['sha256'],'--archive-root',str(Path(root).resolve()),'--mode',mode]
    return {v:[str(python),str(launcher),v,*common] for v in ('start','advance','notify','status')}

def bind_daily(root,state,offer,*,companies=None):
    """Only a newly issued offer; unknown/repeated dispatches never call this."""
    d.require(offer.get('action')=='dispatch' and offer.get('role')==dispatch.ROLE and offer.get('workflow')==dispatch.WORKFLOW and state.get('phase')=='dispatch-intent' and state.get('dispatch_id')==offer.get('dispatch_id'),'daily-handoff-new-dispatch-required')
    if companies is None:
        configured=t.company_run_mapping(offer.get('active_company_policy'))
        if configured:
            payload={'companies':configured['companies']};raw=(json.dumps(payload,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();folder=Path(root)/'dispatch-company-configs';folder.mkdir(parents=True,exist_ok=True);companies=parent.immutable(folder/(hashlib.sha256(raw).hexdigest()+'.json'),payload)
        else:companies=t.ref(dispatch.DEFAULT_COMPANIES)
    path=offer_path(root,offer['dispatch_id']);parent.immutable(path,offer);offer_ref=t.ref(path)
    previous=[e['order'] for e in state['events'] if e.get('type')=='daily-execution-bound' and e.get('dispatch_id')!=offer['dispatch_id']]
    prior=None
    if previous:
        prior=previous[-1];old=dispatch.validate(prior,root)
        d.require(old['day']==state['day'],'daily-handoff-cross-day-resume-forbidden')
    order_ref=dispatch.archive(root,offer_ref,companies,origin='resume' if prior else 'fresh',resumed_from=prior)
    order=dispatch.validate(order_ref,root);commands=launch_commands(order_ref,root)
    state['events'].append({'type':'daily-execution-bound','dispatch_id':offer['dispatch_id'],'order':order_ref,'origin':order['origin'],'at':d.stamp()})
    return {**offer,'daily_execution':{'order':order_ref,'archive_root':str(Path(root).resolve()),'origin':order['origin'],'mode':'acceptance','commands':commands,'advance_requires_explicit_tab_id':True,'notify_steps':25,'heartbeat_journal_contract':'Use actual operator workflow.json or canonical sender job; parent/timed-role state is not a semantic progress journal.','business_journal_candidates':[],'business_journal_source':'Use actual operator checkpoint journal reported after handoff or canonical original sender job; batch/parent/timed-role states are unsupported.','parent_status_is_not_business_progress':True,'completion_adapter':{'script':str(Path(__file__).resolve()),'parent_state':str(parent.location(order_ref)/'state.json'),'director_state':str(Path(root)/'state.json'),'out':str(Path(root)/'daily-completions'/Path(order_ref['path']).stem/'report.json'),'explicit_current_hashes_required':True}},'message':offer['message']+' 正式日统唯一入口 daily_execution_launcher.py；禁止直接flow/daily_timed_run绕过全程计时。先执行 '+json.dumps(commands['start'],ensure_ascii=False)+'；后续同order advance必须显式--tab-id，完成采集后notify --steps25，全部同mode acceptance。未知child仅status和原单复核，不重启/换key。原业务operator/sender日志用于heartbeat，parent计时state不作进度。'}

def copy_evidence(root,reference):
    """Portable immutable snapshot; do not pin future-mutable business files."""
    data=t.checked_bytes(reference);p=Path(root)/'evidence'/(reference['sha256']+Path(reference['path']).suffix)
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():d.require(p.read_bytes()==data,'daily-completion-snapshot-conflict')
    else:
        fd,tmp=tempfile.mkstemp(dir=p.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,p)
            except FileExistsError:d.require(p.read_bytes()==data,'daily-completion-snapshot-conflict')
        finally:os.unlink(tmp)
    return t.ref(p)

def completion_report(parent_ref,director_ref,out,*,clock=None):
    """Pure source/client replay, current acknowledged dispatch, immutable report."""
    clock=clock or t.Clock();raw=t.checked_bytes(parent_ref);state=json.loads(raw);order_ref=state['order'];archive=state['archive_root'];path=Path(parent_ref['path'])
    s,order=parent.load(path,order_ref,archive,clock)
    d.require(s['status']=='complete','daily-completion-parent-not-complete');proof=parent.verify_complete(s,order,clock);d.require(proof==s['completion_proof'],'daily-completion-source-client-proof-changed');final=t.pinned(s['completion_ref'])
    d.require(Path(director_ref['path'])==Path(archive)/'state.json','daily-completion-canonical-director-required');ds=t.pinned(director_ref);dispatch_id=order['dispatch_id']
    d.require(ds.get('phase') in ('running','attention') and ds.get('day')==order['day'] and ds.get('dispatch_id')==dispatch_id and d.current(ds).get('role')==dispatch.ROLE,'daily-completion-dispatch-conflict')
    d.require(any(e.get('type')=='dispatched' and e.get('id')==dispatch_id for e in ds.get('events',[])) and ds.get('dispatched_at'),'daily-completion-dispatch-not-acknowledged')
    begun=t.parse_time(ds['dispatch_intent_at']);start=t.parse_time(s['wall_started_at']);ended=t.parse_time(final['wall_ended_at']);d.require(begun<=start<=ended<=clock.wall(),'daily-completion-outside-current-dispatch')
    d.require(not any(e.get('type')=='completed' and e.get('dispatch_id')==dispatch_id for e in ds['events']),'daily-completion-already-consumed')
    receipt=t.pinned(proof['completion']);batch=t.pinned(proof['batch']);refs=[parent_ref,director_ref,s['completion_ref'],s['origin_ref'],order_ref,proof['batch'],proof['outbox'],proof['completion']]
    refs.extend(receipt.get('client_jobs',[]))
    # Source processing receipts/inputs are checked by verify_complete/outbox replay;
    # copy their exact current bytes as completion-time, durable evidence.
    for row in batch['companies']:
        if row.get('status')=='skipped':continue
        rp=Path(row.get('receipt') or Path(row['outdir'])/'receipt.json');rr=t.ref(rp);rv=t.pinned(rr);refs.append(rr)
        src=rv.get('src_file');sha=rv.get('src_sha256')
        if src and sha:refs.append({'path':src,'sha256':sha})
    d.require(t.checked_bytes(parent_ref)==raw and t.pinned(director_ref)==ds,'daily-completion-current-binding-changed')
    evidence=[];seen=set()
    for reference in refs:
        key=(reference['path'],reference['sha256'])
        if key not in seen:seen.add(key);evidence.append(copy_evidence(Path(out).parent,reference))
    value={'kind':'daily-director-completion-report-v1','verification_parent_state':parent_ref,'workflow':dispatch.WORKFLOW,'live':True,'complete':True,'fixture':False,'test_target':t.TARGET,'production_sent':False,'complaint_submitted':False,'dispatch_id':dispatch_id,'day':order['day'],'role':dispatch.ROLE,'completed_at':final['wall_ended_at'],'evidence':evidence,'parent_completion':s['completion_ref'],'source_client_replay_verified':True,'performance':{'acceptance_pass':final['acceptance_pass'],'full_workflow_measured':final['full_workflow_measured'],'elapsed_seconds':final['end_monotonic']-s['start_monotonic'],'origin':s['origin'],'mode':s['mode'],'functional_completion_is_not_30_second_pass':True},'adapter_business_actions_performed':False}
    return parent.immutable(out,value)

def _historical_ready_parent(parent_ref):
    """Read sealed collection history in its producer clock domain only.
    No live Clock, parent.load, execution entry, input or state update is used.
    Current lease/process/boot authorization remains the consuming program's job.
    """
    raw=t.checked_bytes(parent_ref);state=json.loads(raw);root=parent.location(state['order'])
    d.require(parent_ref['path']==str(root/'state.json')and state.get('kind')==parent.KIND and state.get('status')=='collection-ready'and not state.get('completion_ref'),'daily-ready-history-sealed-parent-required')
    pinned=t.pinned(state['origin_ref']);origin_now={k:state[k]for k in parent.ORIGIN_FIELDS}
    if pinned!=origin_now:
        # The launcher may adopt reviewed source generations during its own
        # run (slot adoption recorded in source_generations); origin.json
        # stays the pre-run freeze. Replay the launcher's own path-keyed
        # previous->current chain (the W121 precedent in
        # collection_ready.check_natural_chain) and require it to land
        # exactly on the live code_refs; a broken, duplicated or fabricated
        # chain - and any non-code_refs drift - stays fatal.
        replayed=[dict(r)for r in pinned.get('code_refs',[])]
        by={r['path']:r for r in replayed}
        for g in state.get('source_generations',[]):
            row=by.get(g.get('path'));d.require(row is not None and row['sha256']==g.get('previous_sha256')and {'path','previous_sha256','current_sha256'}<=set(g),'daily-ready-history-origin-changed')
            row['sha256']=g['current_sha256']
        d.require({k:v for k,v in pinned.items() if k!='code_refs'}=={k:v for k,v in origin_now.items() if k!='code_refs'}and replayed==origin_now['code_refs'],'daily-ready-history-origin-changed')
    order=dispatch.validate(state['order'],state['archive_root'])
    d.require(state['scope_sha256']==order['scope_sha256']and state['origin']==order['origin']and state['archive_root']==str(Path(state['archive_root']).resolve())and order.get('collection_contract')=='three-flow-collection-ready-v1','daily-ready-history-original-scope')
    d.require(state.get('clock_contract')==t.MONOTONIC_CLOCK and type(state.get('boot_identity'))is str and bool(state['boot_identity'])and t.finite(state['start_monotonic']),'daily-ready-history-producer-clock')
    d.require(state.get('calls')and all(c.get('state')in('returned','failed')for c in state['calls']),'daily-ready-history-no-unknown-child')
    for reference in state['code_refs']:parent.source_code_bytes(reference,state,root)
    previous=state['start_monotonic'];last=None
    d.require(bool(state.get('calls')),'daily-ready-history-natural-calls-required')
    for index,call in enumerate(state['calls']):
        d.require(call['index']==index and call['verb']in parent.VERBS and call.get('state')in('returned','failed')and call['argv']==parent.argv_for(state['order'],state['archive_root'],call['verb'],state['mode'],call.get('tab_id'),call.get('steps',25)),'daily-ready-history-original-command-chain')
        d.require(t.finite(call['launch_monotonic'])and previous<=call['launch_monotonic'],'daily-ready-history-producer-call-order')
        d.require(t.pinned(call['launch'])=={k:v for k,v in call.items()if k not in('launch','state','result')},'daily-ready-history-launch-changed')
        result=call.get('result');d.require(type(result)is dict and result.get('path')==str(root/'children'/('%04d-result.json'%index)),'daily-ready-history-natural-exit-required');last=t.pinned(result)
        d.require(last.get('kind')=='daily-child-exit-v1'and last.get('launch')==call['launch']and last.get('run_id')==state['run_id']and last.get('order')==state['order']and last['argv']==call['argv']and type(last.get('returncode'))is int and last.get('boot_identity')==state['boot_identity']and t.finite(last['exited_monotonic'])and call['launch_monotonic']<=last['exited_monotonic'],'daily-ready-history-producer-exit-binding')
        previous=last['exited_monotonic']
        if last['returncode']==0:
            d.require(call['state']=='returned','daily-ready-history-success-state');parent.receipt_output(last,state)
        else:
            d.require(call['state']=='failed','daily-ready-history-failed-state')
            approved=parent.approved_failed_child(root,state,call,last)
            d.require(approved,'daily-ready-history-unreviewed-failed-child')
    d.require(last['returncode']==0 and t.checked_bytes(parent_ref)==raw,'daily-ready-history-final-exit-or-parent-changed')
    return state,order,last,previous

def _historical_ready_reference(reference):
    # The configured source is code evidence, not an input authority. Its exact
    # archived before bytes may outlive a reviewed installed successor.
    if reference['path']==str(PROJECT/'skills/workshop-director/scripts/company_configuration.py'):
        material=t.configuration_source_material(reference)
        d.require(material['historical']==reference and material['material']['sha256']==reference['sha256'],'daily-ready-history-configuration-material')
        return t.checked_bytes(material['material'])
    return t.checked_bytes(reference)

def _historical_collection_ready_facts(reference):
    import notification_backlog as backlog
    value=backlog.read_ref(reference)
    d.require(value['progress_before']['path']==str(Path(reference['path']).parent/'inputs'/(value['original_progress']['sha256']+'.json')),'daily-ready-history-progress-archive')
    computed=backlog.collection_ready_value(value['batch']['path'],value['progress_before'],value['company_config'],original_progress_ref=value['original_progress'])
    d.require({k:v for k,v in computed.items()if k!='references'}=={k:v for k,v in value.items()if k!='references'},'daily-ready-history-source-facts-not-derived')
    if computed['references']!=value['references']:
        codepath=str(PROJECT/'skills/workshop-director/scripts/company_configuration.py');old=[r for r in value['references']if r['path']==codepath]
        d.require(len(old)==1,'daily-ready-history-one-configuration-slot');material=t.configuration_source_material(old[0]);d.require(material['historical']==old[0]and material['current']!=old[0]and material['dependencies'],'daily-ready-history-reviewed-source-successor')
        baseline=[material['current']if r==old[0]else r for r in value['references']];extra=material['dependencies'];matches=[]
        for index in range(len(baseline)+1):
            if baseline[:index]+extra+baseline[index:]==computed['references']:matches.append(index)
        d.require(len(matches)==1,'daily-ready-history-exact-source-dependency-succession')
    for r in value['references']:_historical_ready_reference(r)
    return value

def collection_ready_report(parent_ref,director_ref,out,*,clock=None,original_director_ref=None,_historical=False):
    """Distinct artifact-only admission. Never a complete/client/cursor report."""
    raw=t.checked_bytes(parent_ref);state=json.loads(raw);historical_last=None
    if _historical and clock is None:
        current,order,historical_last,_=_historical_ready_parent(parent_ref)
    else:
        clock=clock or t.Clock();current,order=parent.load(Path(parent_ref['path']),state['order'],state['archive_root'],clock)
        d.require(not parent.replay_calls(parent.location(state['order']),current,clock),'daily-ready-unknown-child')
    d.require(current==state and state.get('status')=='collection-ready'and order.get('collection_contract')=='three-flow-collection-ready-v1','daily-ready-original-staged-parent-required')
    timed=Path(state['order']['path']).parent.parent/'daily-executions'/Path(state['order']['path']).stem/'state.json';ts=t.pinned(t.ref(timed))
    d.require(ts.get('phase')=='collection-ready'and ts.get('order')==state['order']and ts.get('scope_sha256')==order['scope_sha256'],'daily-ready-role-stage')
    last=historical_last if historical_last is not None else parent.child_receipt(parent.location(state['order']),current,current['calls'][-1],clock)[1];output=parent.receipt_output(last,current)
    d.require(output.get('phase')=='collection-ready'and output.get('collection_ready')==ts['collection_ready']and output.get('delivery_complete')is False,'daily-ready-natural-child-binding')
    ready_ref=ts['collection_ready']
    import notification_backlog as backlog
    if _historical:
        d.require(out is None and original_director_ref is not None and director_ref['path']==str(Path(director_ref['path']).parent/(original_director_ref['sha256']+'.json')),'daily-ready-historical-archive-only')
        ready=_historical_collection_ready_facts(ready_ref)
    else:ready=backlog.verify_collection_ready(ready_ref)
    d.require(ready_ref['path']==str(timed.parent/'collection-ready.json')and ready.get('kind')=='daily-collection-ready-v1'and ready.get('collection_ready')is True and ready.get('delivery_complete')is False and ready.get('cursor_advanced')is False and ready.get('sender_invoked')is False,'daily-ready-not-delivered')
    ds=t.pinned(director_ref);original_director_ref=original_director_ref or director_ref
    d.require(original_director_ref['path']==str(Path(state['archive_root'])/'state.json')and original_director_ref['sha256']==director_ref['sha256'],'daily-ready-original-director-ref')
    if out is not None:director_ref=parent.immutable_raw(Path(out).parent/'evidence'/(director_ref['sha256']+'.json'),t.checked_bytes(director_ref))
    d.require(ds['day']==order['day']and ds.get('dispatch_id')==order['dispatch_id']and d.current(ds).get('workflow')==dispatch.WORKFLOW and ds.get('phase')in('running','attention'),'daily-ready-director-binding')
    for reference in ready['references']:
        _historical_ready_reference(reference)if _historical else t.checked_bytes(reference)
    expected={(x['company'],x['groupid'],x['start'],x['end_exclusive'])for x in order['scope']['company_ranges']}
    actual={(x['company'],x['groupid'],x['start'],x['end_exclusive'])for x in ready['companies']}
    d.require(actual==expected,'daily-ready-company-range')
    d.require(t.checked_bytes(parent_ref)==raw,'daily-ready-parent-changed')
    value={'kind':'daily-director-collection-ready-report-v1','workflow':dispatch.WORKFLOW,'collection_contract':order['collection_contract'],'dispatch_id':order['dispatch_id'],'day':order['day'],'order':state['order'],'scope_sha256':order['scope_sha256'],'parent':parent_ref,'director_before':director_ref,'original_director':original_director_ref,'role_state':t.ref(timed),'ready':ready_ref,'collection_ready':True,'complete':False,'delivery_complete':False,'cursor_advanced':False}
    return value if out is None else parent.immutable(out,value)

def _verified_collection_ready_uncached(report_ref,*,clock=None):
    """Historical collection facts, never completion/client facts.
    The live successor lease is checked by its own consumer on each action.
    """
    report=t.pinned(report_ref)
    if report.get('reader')=='current-results-v1':
        import current_daily_ready
        return current_daily_ready.facts(report_ref)
    d.require(report.get('kind')=='daily-director-collection-ready-report-v1','daily-ready-report-kind')
    expected=collection_ready_report(report['parent'],report['director_before'],None,clock=clock,original_director_ref=report['original_director'],_historical=True)
    d.require(report==expected,'daily-ready-report-not-derived')
    import notification_backlog as backlog
    ready=_historical_collection_ready_facts(report['ready']);state=t.pinned(report['parent']);order=dispatch.validate(report['order'],state['archive_root'])
    return {'report':report,'ready':ready,'parent':state,'order':order}

# No new command owner: use the caller's existing bounded historical memo only.
_READY_SAMPLE=contextvars.ContextVar('daily_ready_internal_clock_sample',default=None)

class _ReadySampleClock:
    def boot(self):return _READY_SAMPLE.get()[0]
    def monotonic(self):return _READY_SAMPLE.get()[1]
    def wall(self):raise ValueError('daily-ready-unexpected-live-wall-read')

def _ready_module_epoch(module):
    """Refuse caching a resident reader whose executable generation drifted.
    Compare actual module-owned code with the source compiler, not a new SHA
    attached to an old module. Scalar source constants are checked as well.
    Unattestable modules conservatively retain the original uncached path.
    """
    path=Path(module.__file__);raw=path.read_bytes()
    d.require(path.is_absolute()and not path.is_symlink(),'daily-ready-reader-origin')
    compiled=compile(raw,str(path),'exec');codes=[]
    def walk(code):
        codes.append(code)
        for value in code.co_consts:
            if isinstance(value,types.CodeType):walk(value)
    walk(compiled)
    # Every source-defined public binding must still execute that generation.
    # A replaced foreign function must not disappear from the validation loop.
    tree=ast.parse(raw)
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            cls=vars(module).get(node.name);d.require(isinstance(cls,type)and cls.__module__==module.__name__,'daily-ready-reader-generation')
            for child in node.body:
                if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    method=vars(cls).get(child.name)
                    if isinstance(method,(staticmethod,classmethod)):method=method.__func__
                    d.require(isinstance(method,types.FunctionType)and method.__globals__ is vars(module)and any(method.__code__==code for code in codes),'daily-ready-reader-generation')
            continue
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
        value=vars(module).get(node.name)
        d.require(isinstance(value,types.FunctionType),'daily-ready-reader-generation')
        seen=set()
        while getattr(value,'__wrapped__',None)is not None:
            d.require(id(value)not in seen,'daily-ready-reader-generation');seen.add(id(value))
            original=value.__wrapped__;closure=tuple(c.cell_contents for c in(value.__closure__ or ()))
            d.require(any(original is c for c in closure),'daily-ready-reader-generation')
            owner=Path(value.__globals__['__file__']);owner_raw=owner.read_bytes();owner_codes=[]
            def owner_walk(code):
                owner_codes.append(code)
                for item in code.co_consts:
                    if isinstance(item,types.CodeType):owner_walk(item)
            owner_walk(compile(owner_raw,str(owner),'exec'))
            d.require(any(value.__code__==code for code in owner_codes),'daily-ready-reader-generation')
            value=original
        d.require(value.__globals__ is vars(module)and any(value.__code__==code for code in codes),'daily-ready-reader-generation')
    for value in vars(module).values():
        if isinstance(value,types.FunctionType)and value.__globals__ is vars(module):
            d.require(any(value.__code__==code for code in codes),'daily-ready-reader-generation')
        elif isinstance(value,type)and value.__module__==module.__name__:
            for method in vars(value).values():
                if isinstance(method,(staticmethod,classmethod)):method=method.__func__
                if isinstance(method,types.FunctionType)and method.__globals__ is vars(module):
                    d.require(any(method.__code__==code for code in codes),'daily-ready-reader-generation')
    # Literal globals must not be relabelled by a later disk generation.
    # Dynamic bindings remain guarded by their existing admissions/frontier.
    literals={}
    for node in ast.parse(raw).body:
        if isinstance(node,ast.Assign):
            try:value=ast.literal_eval(node.value)
            except (ValueError,TypeError):continue
            if isinstance(value,(str,int,float,bool,type(None),tuple,list,dict,set)):
                for target in node.targets:
                    if isinstance(target,ast.Name):literals[target.id]=value
    for name,value in literals.items():d.require(vars(module).get(name)==value,'daily-ready-reader-generation')
    d.require(path.read_bytes()==raw,'daily-ready-reader-raced')
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}

def _ready_shared_history(report_ref,boot,epochs):
    # Executed epochs were independently compared before entering this reader.
    # Their bytes also join the existing content/metadata/reader frontier.
    for reference in epochs:t.checked_bytes(reference)
    facts=_verified_collection_ready_uncached(report_ref)
    state=facts['parent'];frontier=max([state['start_monotonic'],*[t.pinned(call['result'])['exited_monotonic']for call in state['calls']]])
    d.require(t.finite(frontier),'daily-ready-producer-clock-frontier')
    return {'facts':facts,'reader_boot':boot,'producer_boot':state['boot_identity'],'producer_frontier':frontier}

def _verify_ready_reader_clock(before,after,verified):
    d.require(before[0]==after[0]==verified['reader_boot'],'daily-ready-live-boot-changed')
    d.require(t.finite(before[1])and t.finite(after[1])and after[1]>=before[1],'daily-ready-live-monotonic-invalid')
    if before[0]==verified['producer_boot']:
        d.require(before[1]>=verified['producer_frontier'],'daily-ready-live-monotonic-invalid')

def verified_collection_ready_facts(report_ref,*,clock=None):
    current=t.pinned(report_ref)
    if current.get('reader')=='current-results-v1':
        import current_daily_ready
        return current_daily_ready.facts(report_ref)
    # Explicit caller clocks retain their original semantics, including tests.
    helper=sys.modules.get('initial_ledger_recovery')
    scope=getattr(helper,'_HM_SCOPE',None)
    memo=scope.get()if scope is not None else None
    if clock is not None or memo is None:return _verified_collection_ready_uncached(report_ref,clock=clock)
    import notification_backlog as backlog
    modules=(sys.modules[__name__],parent,t,dispatch,d,backlog,sys.modules['ds_common'])
    try:epochs=[_ready_module_epoch(module)for module in modules]
    except (ValueError,OSError,TypeError,SyntaxError,KeyError,AttributeError):
        return _verified_collection_ready_uncached(report_ref)
    live=t.Clock();before=(live.boot(),live.monotonic())
    d.require(t.finite(before[1]),'daily-ready-live-monotonic-invalid')
    token=_READY_SAMPLE.set(before)
    try:verified=memo.call(_ready_shared_history,(report_ref,before[0],epochs),{})
    finally:_READY_SAMPLE.reset(token)
    after=(live.boot(),live.monotonic())
    _verify_ready_reader_clock(before,after,verified)
    return verified['facts']

def verify_collection_ready_report(report_path,current_director,*,clock=None):
    current_report=t.pinned(t.ref(report_path))
    if current_report.get('reader')=='current-results-v1':
        import current_daily_ready
        facts=current_daily_ready.facts(t.ref(report_path));order=facts['order']
        d.require(current_director['day']==order['day'] and current_director['dispatch_id']==order['dispatch_id'] and current_director['phase']in('running','attention') and d.current(current_director)['workflow']==order['workflow'],'current-ready-director-owner')
        return current_report
    report=t.pinned(t.ref(report_path));original=t.pinned(report['director_before'])
    d.require(original==current_director,'daily-ready-current-director-changed')
    expected=collection_ready_report(report['parent'],report['director_before'],None,clock=clock,original_director_ref=report['original_director'])
    d.require(report==expected,'daily-ready-report-not-derived')
    return report

def verify_completion(report_path,current_director,*,clock=None):
    """Daily finish cannot substitute an old functional acceptance for this run."""
    clock=clock or t.Clock();data=t.pinned(t.ref(report_path));d.require(data.get('kind')=='daily-director-completion-report-v1','daily-finish-parent-adapter-report-required')
    parent_ref=data['verification_parent_state'];raw=t.checked_bytes(parent_ref);s0=json.loads(raw);s,order=parent.load(Path(parent_ref['path']),s0['order'],s0['archive_root'],clock)
    d.require(s['status']=='complete','daily-completion-parent-not-complete');proof=parent.verify_complete(s,order,clock);d.require(proof==s['completion_proof'],'daily-completion-source-client-proof-changed');final=t.pinned(s['completion_ref'])
    d.require(d.read(Path(s['archive_root'])/'state.json')==current_director,'daily-completion-current-director-changed')
    d.require(data.get('dispatch_id')==current_director.get('dispatch_id')==order['dispatch_id'] and data.get('day')==current_director.get('day')==order['day'] and data.get('role')==dispatch.ROLE==d.current(current_director).get('role'),'daily-completion-dispatch-conflict')
    d.require(current_director.get('phase') in ('running','attention') and any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in current_director.get('events',[])),'daily-completion-dispatch-not-acknowledged')
    d.require(t.parse_time(current_director['dispatch_intent_at'])<=t.parse_time(s['wall_started_at'])<=t.parse_time(data['completed_at'])==t.parse_time(final['wall_ended_at'])<=clock.wall(),'daily-completion-outside-current-dispatch')
    d.require(data.get('parent_completion')==s['completion_ref'] and data.get('source_client_replay_verified') is True and data.get('adapter_business_actions_performed') is False,'daily-completion-report-binding-changed')
    expected={'acceptance_pass':final['acceptance_pass'],'full_workflow_measured':final['full_workflow_measured'],'elapsed_seconds':final['end_monotonic']-s['start_monotonic'],'origin':s['origin'],'mode':s['mode'],'functional_completion_is_not_30_second_pass':True}
    d.require(data.get('performance')==expected,'daily-completion-performance-not-derived')
    for reference in data['evidence']:t.checked_bytes(reference)
    return data

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent-state',required=True);p.add_argument('--parent-sha256',required=True);p.add_argument('--director-state',required=True);p.add_argument('--director-sha256',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    try:r=completion_report({'path':str(Path(a.parent_state).resolve()),'sha256':a.parent_sha256},{'path':str(Path(a.director_state).resolve()),'sha256':a.director_sha256},a.out);print(json.dumps({'report':r,'ui_used':False}));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps({'ok':False,'error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())


_policy_original_bind_daily=bind_daily
def bind_daily(*args,**kwargs):
    with t.company_policy_command():return _policy_original_bind_daily(*args,**kwargs)
