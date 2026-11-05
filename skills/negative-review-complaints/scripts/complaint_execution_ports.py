"""Fixed complaint role API wiring, draft-only and test target only.
No custom weak collector: original operator, normal.joined, region, inspection,
classification, sender and close validators own each business boundary.
"""
import copy,contextlib,fcntl,importlib.util,io,json,re,sys,subprocess
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import complaint_execution_order as o
import delivery_targets
import complaint_execution as engine
import workflow as w
import normal_observation as normal
import complaint_execution_normal as normal_api
import prepare_result_orders as orders
import existing_result_runner as results
import draft_inspection as draft
import capture_review_region as screenshot
import recent_other_history as history
ROOT=o.PROJECT
need=o.need

def module(name,path):
    if name in sys.modules:
        v=sys.modules[name];need(Path(v.__file__).resolve()==path.resolve(),'complaint-parent-module-origin-conflict');return v
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
company_api=module('complaint_parent_company_api',ROOT/'skills/douyin-laike-operator/scripts/prepare_company_navigation.py')
operator=module('complaint_parent_operator_api',ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')
role_cli=module('complaint_parent_role_cli',ROOT/'skills/douyin-laike-operator/scripts/role_cli.py')
nav=module('complaint_parent_navigation',ROOT/'skills/negative-review-complaints/scripts/bridge-navigation.py')

def initial_ledger_reference(company,reason='complaint-parent-ledger-changed'):
    # The dispatch source is a pinned byte snapshot, not its canonical live path.
    expected=o.raw(company['ledger']);current=o.ref(Path(company['root'])/'state.json')
    need(current['sha256']==company['ledger']['sha256'] and o.raw(current)==expected,reason)
    return current

def resume_positive_switch_read(work_order,path,request):
    """B62/W132: one durable read-only resume of a held company-switch read.

    The daily parent performs this in adapters.resume_switch_transport; the
    complaint/violation parent had no counterpart, so a confirmed switch whose
    first read landed inside the post-switch navigation window held forever
    (waiting_for blocks _run_steps, and only Workflow.__init__ kept touching
    updated_at). Admission, sampling and verification stay in the reviewed
    helper: this only decides when to ask it, exactly once, and never clicks.
    """
    need(path.is_absolute() and not path.is_symlink(),'complaint-parent-switch-read-resume-path')
    if not path.exists():return False
    state=json.loads(path.read_bytes())
    if not(state.get('state')=='running'and state.get('phase')=='verifySwitch'and state.get('waiting_for')=='company-switch-readonly-scope'and state.get('last_error')is None):return False
    hold=state.get('switch_read_hold',{});need(hold.get('state')=='hold'and hold.get('ui_used')is False and hold.get('original_unchanged')is True,'complaint-parent-switch-read-resume-hold-required')
    import switch_read_recovery as recovery
    need(recovery.classify_switch_read(hold.get('error'))in('positive','retry'),'complaint-parent-switch-read-resume-not-retryable')
    current=o.ref(path);proof=recovery.readonly_resume_contract(work_order['path'],current['sha256'])
    out=recovery.reconcile(work_order['path'],current['sha256'],request);need(out.get('state')=='reconciled','complaint-parent-switch-read-resume-exhausted:'+str(out.get('error','unknown')))
    new=o.doc(out['journal']);[o.doc(r)for r in proof['historical_refs']];recovery.verify_recovered(new,out['proof'])
    need(new.get('calls')==state.get('calls')and new.get('phase')=='accountAfterSwitch','complaint-parent-switch-read-resume-original-chain')
    return True

def planned_pending_rechecks(state,plan):
    from initial_ledger_recovery import pending_rechecks
    return pending_rechecks(state,plan,w)

def validated_dom_identity_origin(row,batch,batch_ref,ready,ready_ref,registry):
    """Fresh DOM source is identity provenance, never a platform export or a
    complaint review population. Normal complaint acquisition still runs later.
    """
    from ds_common import dom_command,dom_capture_data,dom_source_data,dom_original_download
    directory=Path(row['outdir']);copied=Path(row['evidence']);need(directory.is_absolute()and directory.resolve()==directory and not directory.is_symlink()and copied==directory/'dom-acquisition.json'and copied.resolve()==copied and not copied.is_symlink()and directory.parent==Path(batch_ref['path']).parent,'complaint-parent-dom-origin-path')
    copy_ref=o.ref(copied);payload=o.doc(copy_ref);receipt_path=directory/'receipt.json';need(row.get('receipt')==str(receipt_path),'complaint-parent-dom-receipt-path');matches=[r for r in ready['references']if r['path']==str(receipt_path)];need(len(matches)==1,'complaint-parent-dom-pinned-receipt');receipt_ref=matches[0];receipt=o.doc(receipt_ref);dates={k:row['date_range'][k]for k in('start','end')}
    need(receipt.get('source_kind')==row['source_kind']=='daily-visible-dom-source-v1'and payload==receipt.get('dom_source')and receipt.get('dom_capture')==row.get('dom_capture')and receipt.get('company')==row['company']and receipt.get('date_range')==dates and receipt.get('src_file')==row['source']==payload.get('source')and receipt.get('src_sha256')==payload.get('src_sha256')and receipt.get('attribution_verified')is True and receipt.get('download_verified')is False and receipt.get('source_is_authoritative_export')is False,'complaint-parent-dom-source-binding')
    company=[x for x in ready['companies']if x.get('company')==row['company']];need(len(company)==1 and company[0].get('source_kind')==row['source_kind']and company[0].get('dom_source')==payload and company[0].get('dom_capture')==row['dom_capture']and company[0].get('download_verified')is False and company[0].get('source_is_authoritative_export')is False,'complaint-parent-dom-ready-binding')
    need(payload.get('company')==row['company']and str(payload.get('groupid'))==str(row['groupid'])and payload.get('date_range')==dates and payload.get('identity')==payload.get('identity_before')==registry['company_identities'].get(str(row['groupid']))and payload['identity']['provider']==registry['provider_baseline'],'complaint-parent-dom-identity')
    checkpoints=[x for x in row.get('checkpoints',[])if x.get('stage')=='dom-acquisition-complete'];need(len(checkpoints)==1 and checkpoints[0]['counts']==receipt.get('dom_counts'),'complaint-parent-dom-count-scope')
    with dom_command():
        capture=dom_capture_data(row['dom_capture'],payload,batch,row)
        data=dom_source_data(payload,row,dates,Path(row['source']))
        original=dom_original_download(data)
    checkpoints=[x for x in row.get('checkpoints',[])if x.get('stage')=='dom-acquisition-complete'];need(len(checkpoints)==1 and checkpoints[0]['original_workflow']==original and checkpoints[0]['receipt']==payload['receipt']and checkpoints[0]['capture']==row['dom_capture']and checkpoints[0]['counts']==data['summary']and receipt['dom_counts']==data['summary'],'complaint-parent-dom-checkpoint')
    for r in(copy_ref,receipt_ref,row['dom_capture'],payload['receipt'],original,batch_ref,ready_ref):o.raw(r)
    return {'kind':'verified-daily-dom-identity-context-v1','original':row['dom_capture'],'copy':copy_ref,'daily_receipt':receipt_ref,'source_journal':original,'batch':batch_ref,'collection_ready':ready_ref,'dom_source':payload['receipt'],'download_verified':False,'source_is_authoritative_export':False,'complaint_rows_reused':False,'complaint_population':'new-normal-only-acquisition-required'}

def validated_acquisition_origin(row,batch,batch_ref,outbox,outbox_ref,registry,*,materials_kind="completed-outbox"):
    """Exact semantic serialization compatibility inside the verified daily parent.
    Both byte refs stay pinned; only the original role receipt is authority.
    """
    need(materials_kind in ('completed-outbox','collection-ready'),'complaint-parent-daily-material-kind')
    if materials_kind=='collection-ready':need(outbox.get('kind')=='daily-collection-ready-v1'and outbox.get('delivery_complete')is False,'complaint-parent-ready-material-kind')
    need(o.doc(batch_ref)==batch and o.doc(outbox_ref)==outbox and outbox.get('batch')==batch_ref,'complaint-parent-acquisition-parent-binding')
    need(len([r for r in batch['companies']if r==row])==1 and row.get('status')in ('complete','zero_rows'),'complaint-parent-acquisition-batch-row')
    if row.get('source_kind')=='daily-visible-dom-source-v1':
        need(materials_kind=='collection-ready','complaint-parent-dom-staged-only')
        return validated_dom_identity_origin(row,batch,batch_ref,outbox,outbox_ref,registry)
    directory=Path(row['outdir']);copied=Path(row['evidence'])
    need(directory.is_absolute()and directory.resolve()==directory and not directory.is_symlink()and copied==directory/'acquisition.json'and copied.resolve()==copied and not copied.is_symlink()and directory.parent==Path(batch_ref['path']).parent,'complaint-parent-acquisition-copy-path')
    copy_ref=o.ref(copied);value=o.doc(copy_ref);key=value.get('work_order_id','');need(type(key)is str and re.fullmatch('[0-9a-f]{64}',key)is not None,'complaint-parent-acquisition-work-order')
    original=directory/'operator'/key[:16]/'acquisition.json';need(original.resolve()==original and not original.is_symlink(),'complaint-parent-acquisition-original-path');original_ref=o.ref(original);original_value=o.doc(original_ref)
    need(value==original_value,'complaint-parent-acquisition-origin')
    receipt_path=directory/'receipt.json';need(row.get('receipt')==str(receipt_path),'complaint-parent-acquisition-receipt-path');refs=[r for r in outbox['references']if r.get('path')==str(receipt_path)];need(len(refs)==1,'complaint-parent-acquisition-pinned-receipt');receipt_ref=refs[0];receipt=o.doc(receipt_ref)
    dates={k:row['date_range'][k]for k in ('start','end')}
    need(value.get('company')==row['company']==receipt.get('company')and str(value.get('groupid'))==str(row['groupid'])and value.get('date_range')==dates==receipt.get('date_range')and value.get('source')==row.get('source')==receipt.get('src_file')and value.get('src_sha256')==receipt.get('src_sha256')and receipt.get('attribution_verified')is True,'complaint-parent-acquisition-source-binding')
    need(registry['company_identities'].get(str(value['groupid']))==value.get('identity')and value.get('identity_before')==value['identity']and value['identity'].get('provider')==registry['provider_baseline'],'complaint-parent-acquisition-identity')
    checked,raw,journal_ref=company_api.receipt(original_ref)
    need(checked==value and raw==o.raw(original_ref)and Path(journal_ref['path'])==original.with_name('workflow.json'),'complaint-parent-acquisition-role-validation')
    # Original finalized bytes and copy formatting may differ, never their data.
    for r in (copy_ref,original_ref,receipt_ref,batch_ref,outbox_ref,journal_ref):o.raw(r)
    need(o.ref(copied)==copy_ref and o.ref(original)==original_ref,'complaint-parent-acquisition-concurrent-change')
    return {'original':original_ref,'copy':copy_ref,'daily_receipt':receipt_ref,'source_journal':journal_ref,'batch':batch_ref,**({'collection_ready':outbox_ref}if materials_kind=='collection-ready'else{'outbox':outbox_ref})}

def completed_daily_identity_facts(completion_ref):
    """Pure derived facts; full original provenance remains mandatory on misses.
    Only the existing explicit history scope may reuse the observed read frontier.
    No live lease/company/date decision is cached here.
    """
    import daily_execution_launcher as parent
    import execution_timing as timing
    report=o.doc(completion_ref);p=o.doc(report['verification_parent_state']);clock=timing.Clock()
    loaded,daily=parent.load(Path(report['verification_parent_state']['path']),p['order'],p['archive_root'],clock)
    need(loaded==p and p['status']=='complete','complaint-parent-current-daily-required')
    proof=parent.verify_complete(p,daily,clock);need(proof==p['completion_proof'],'complaint-parent-daily-proof-changed')
    batch=o.doc(proof['batch']);outbox=o.doc(proof['outbox'])
    registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']};origins={};found={}
    for row in batch['companies']:
        if row.get('status')=='skipped':continue
        origin=validated_acquisition_origin(row,batch,proof['batch'],outbox,proof['outbox'],registry)
        origins[row['company']]=origin;found[row['company']]=origin['original']
    return {'day':daily['day'],'boot_identity':p['boot_identity'],'start_monotonic':p['start_monotonic'],'end_monotonic':p['end_monotonic'],'registry':registry,'acquisition_origins':origins,'found':found}

def ready_daily_identity_facts(ready_report_ref):
    import daily_orchestration as orchestration
    facts=orchestration.verified_collection_ready_facts(ready_report_ref)
    ready=facts['ready'];daily=facts['order'];batch=o.doc(ready['batch'])
    registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']}
    found={};origins={}
    for company in ready['companies']:
        gid=str(company['groupid']);need(gid in registry['company_identities'],'complaint-current-identity-missing')
        need(registry['company_identities'][gid]['provider']==registry['provider_baseline'],'complaint-current-provider-conflict')
        found[company['company']]=company['receipt']
        origins[company['company']]={'original':company['receipt'],'complaint_rows_reused':False}
    return {'day':daily['day'],'registry':registry,'acquisition_origins':origins,'found':found,'collection_ready':facts['report']['ready'],'delivery_complete':False,'current_results':True}

class ProductionPorts:
    def __init__(self,tab_id,pid,*,request=None):
        need(type(tab_id) is int and tab_id>0 and type(pid) is int and pid>0,'complaint-parent-explicit-tab-pid');self.tab=tab_id;self.pid=pid;self.request=request or nav.bridge.request
    def identities(self,order):
        import execution_timing as timing
        from initial_ledger_recovery import _hm_history
        # Existing command scope owns this cache; no instance/process-lifetime
        # cache or boolean certificate. Every observed dependency is rechecked.
        if order.get('collection_contract')=='three-flow-collection-ready-v1':facts=ready_daily_identity_facts(order['daily_collection_ready'])
        else:
            need(order.get('collection_contract')is None,'complaint-parent-collection-contract-invalid')
            facts=_hm_history(completed_daily_identity_facts)(order['daily_completion'])
        clock=timing.Clock();need(facts['day']==order['day'],'complaint-parent-current-daily-required')
        if not facts.get('current_results'):
            now=clock.monotonic();need(clock.boot()==facts['boot_identity']and timing.finite(now)and now>=facts['end_monotonic']>=facts['start_monotonic'],'complaint-parent-daily-clock-changed')
        self.registry=copy.deepcopy(facts['registry']);self.acquisition_origins=copy.deepcopy(facts['acquisition_origins'])
        return copy.deepcopy(facts['found'])
    def validate_origins(self,order):
        found=self.identities(order)
        for c in order['companies']:
            initial_ledger_reference(c)
            if not c['skipped']:need(bool(found) and c['groupid'] in self.registry['company_identities'],'complaint-parent-current-daily-origin-unavailable')
    def skipped(self,c):initial_ledger_reference(c,'complaint-parent-skipped-ledger-changed')
    def guard(self,order,s):
        import director
        lease=json.loads((Path(s['order']['path']).parent.parent/'state.json').read_bytes());need(lease['day']==order['day'] and lease['dispatch_id']==order['dispatch_id'] and lease['phase']=='running' and director.current(lease)['role']==order['role'],'complaint-parent-live-lease');need(any(x.get('type')=='dispatched' and x.get('id')==order['dispatch_id'] for x in lease['events']),'complaint-parent-ack-required');need(not any(x['state'] in ('unknown','failed') for x in engine.guarded_calls(s)),'complaint-parent-unresolved-no-replay')
        for c,cs in zip(order['companies'],s['companies']):
            a=cs['artifacts'];expected=a['ledger_current'] if 'ledger_current' in a else initial_ledger_reference(c,'complaint-parent-external-ledger-change');need(o.ref(Path(c['root'])/'state.json')==expected,'complaint-parent-external-ledger-change')
            for r in a.get('immutable_refs',[]):o.raw(r)
            for unit in a.get('completed_units',[])+[a.get('unit_artifacts',{})]:
                for field in ('job','work_order','acquisition','source','profile','page','envelope','orders'):
                    if field in unit:o.raw(unit[field])
                for ref in unit.get('operations',[]):o.raw(ref)
    def folder(self,ctx):p=Path(ctx['folder']);p.mkdir(parents=True,exist_ok=True);return p
    def ledger(self,c):return w.load(Path(c['root']))
    def changed(self,ctx,**artifacts):return {'ledger_current':o.ref(Path(ctx['company']['root'])/'state.json'),**artifacts}
    def journals(self,order,state):
        out=[]
        for cs in state['companies']:
            for value in cs['artifacts'].get('journals',[]):
                if Path(value).is_file():out.append(value)
        return list(dict.fromkeys(out))
    def read_normal_scope(self,job,folder,anchor):
        # Navigation currently persists a tree, not a window binding. Discover
        # that window with one fresh tabs read; never guess or reuse it later.
        state=o.doc(anchor)
        need(anchor['path']==str(folder/'navigation-state.json')and state.get('fingerprint')==nav.tag(job)and state.get('tab_id')==self.tab and state.get('phase')=='profileRequired'and state.get('stable_normal_verified')is True and all(c.get('state')=='confirmed'for c in state.get('calls',[])),'complaint-normal-scope-navigation-anchor')
        normal.public_identity(o.doc(state['last_tree']),job['identity'])
        directory=folder/('normal-scope-'+__import__('uuid').uuid4().hex)
        def sampled(command,name):
            reply=self.request(command);reference=o.immutable(directory/name,{'command':command,'reply':reply})
            need(reply.get('ok')is True,'complaint-parent-read-failed')
            return reference,reply['result']
        bootstrap,tabs=sampled({'op':'tabs'},'bootstrap.json');known=nav.context(tabs,self.tab,job['groupid'])
        normal.context({'tab':known,'tree':o.doc(state['last_tree']),'observed_at':datetime.now(timezone.utc).isoformat()},job['groupid'])
        window=known.get('windowId');need(type(window)is int and window>0,'complaint-normal-scope-window-anchor')
        command={'op':'readonly-scope','tabId':self.tab,'windowId':window};raw,value=sampled(command,'readonly-scope.json')
        from readonly_tick_snapshot import decode
        value=decode(value,self.tab,window);before=nav.context(value['before'],self.tab,job['groupid']);after=nav.context(value['after'],self.tab,job['groupid'])
        need(before==after and before==known,'complaint-parent-read-context-changed')
        ping=value['ping'];need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only','complaint-parent-bridge-version')
        tree=value['tree'];page={'source':'local-dom-bridge','observed_at':datetime.now(timezone.utc).isoformat(),'tab':after,'tree':tree,'ping':ping}
        normal.context(page,job['groupid']);normal.public_identity(tree,job['identity'])
        checksum=lambda v:__import__('hashlib').sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        page['transport_projection']={'kind':'complaint-normal-readonly-scope-projection-v1','anchor':anchor,'bootstrap':bootstrap,'raw':raw,'command':command,'source_rpc_count':1,'bootstrap_rpc_count':1,'inner_read_count':4,'members':[{'index':i,'key':key,'command':value['commands'][i],'value_sha256':checksum(value[key])}for i,key in enumerate(('before','ping','tree','after'))]}
        return o.immutable(folder/('normal-'+__import__('uuid').uuid4().hex+'.json'),page)
    def read(self,job,folder,label):
        def rpc(cmd):
            r=self.request(cmd);need(r.get('ok') is True,'complaint-parent-read-failed');return r['result']
        before=nav.context(rpc({'op':'tabs'}),self.tab,job['groupid']);ping=rpc({'op':'ping','tabId':self.tab});need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only','complaint-parent-bridge-version');tree=rpc({'op':'tree','tabId':self.tab});after=nav.context(rpc({'op':'tabs'}),self.tab,job['groupid']);need(before==after,'complaint-parent-read-context-changed')
        value={'source':'local-dom-bridge','observed_at':datetime.now(timezone.utc).isoformat(),'tab':after,'tree':tree,'ping':ping};normal.context(value,job['groupid']);p=folder/(label+'-'+__import__('uuid').uuid4().hex+'.json');return o.immutable(p,value)
    def units(self,c,s):
        out=[]
        if c['start']<c['end_exclusive']:out.append({'kind':'new','start':c['start'],'end_exclusive':c['end_exclusive'],'keys':[]})
        bydate={}
        for key in c['recheck_ids']:
            t=s['tasks'][key]
            bydate.setdefault(t['review']['date'],[]).append(key)
        for day,keys in sorted(bydate.items()):
            if c['start']<=day<c['end_exclusive']:continue
            out.append({'kind':'recheck','start':day,'end_exclusive':(date.fromisoformat(day)+timedelta(days=1)).isoformat(),'keys':keys})
        return out
    def acquire_job(self,ctx,u,folder):
        engine.scope_for_context(ctx);found=self.identities(ctx['order']);need(ctx['company']['company']in found,'complaint-parent-current-company-daily-origin-unavailable');origin=found[ctx['company']['company']];known=self.registry['company_identities'];gid=ctx['company']['groupid'];need(type(known)is dict and bool(known)and gid in known,'complaint-parent-known-identities');identity=known[gid];need(type(identity)is dict and identity.get('provider')==self.registry['provider_baseline'],'complaint-parent-known-identity-provider');binding={'dispatch':ctx['order']['dispatch_id'],'company':ctx['company']['company'],'unit':u,'identity_receipt':origin};key=o.digest(binding);base=folder/'operator'/key[:16]
        job={'action':'return-company','navigation_only':True,'backend':'local-dom-bridge','company':ctx['company']['company'],'groupid':ctx['company']['groupid'],'date_range':{'ok':True,'start':u['start'],'end':(date.fromisoformat(u['end_exclusive'])-timedelta(days=1)).isoformat(),'end_exclusive':u['end_exclusive'],'mode':'explicit-complaint-parent','warnings':[]},'work_order_id':key,'work_order_path':str(base/'work-order.json'),'workflow_path':str(base/'workflow.json'),'source_dir':str(folder/'exports'),'output_dir':str(base),'operator_skill':'douyin-laike-operator','identity_contract':'merchant-v2','provider_baseline':identity['provider'],'identity_baseline':identity,'known_company_identities':known,'identity_bootstrap':False,'allowed_groupids':sorted(known),'explicit_tab_id_required':True,'source_purpose':'complaint-draft-only-current-dispatch','progress_updates_enabled':False,'send_enabled':False,'submit_enabled':False}
        import execution_timing as timing
        job.update(timing.company_job_fields(ctx['order'].get('active_company_policy'),job['company'],job['groupid'],known=known))
        role_cli.validate_job(job);return o.immutable(base/'work-order.json',job)
    def step(self,phase,ctx):
        engine.scope_for_context(ctx)
        folder=self.folder(ctx)
        if phase=='plan':
            c=ctx['company'];s=self.ledger(c);p=w.plan(s,today=ctx['order']['day']);need(p['start']==c['start'] and p['end_exclusive']==c['end_exclusive'] and planned_pending_rechecks(s,p)==c['recheck_ids'],'complaint-parent-plan-changed');plan=o.immutable(folder/'plan.json',p);units=self.units(c,s);
            return {'done':True,'artifacts':{'plan':plan,'units':units,'unit_index':0,'unit_phase':'acquire','completed_units':[],'immutable_refs':[plan],'journals':[]}}
        if phase=='collect':return self.collect(ctx)
        if phase=='ready':return {'done':True}
        if phase=='collection-workbook':return self.collection_workbook(ctx)
        if phase=='collection-seal':return self.collection_seal(ctx)
        if phase=='seal':return self.seal(ctx)
        if phase=='send':return self.send(ctx)
        if phase=='analyze':return self.analyze(ctx)
        if phase=='complete-company':return self.close(ctx)
        if phase=='finish':return self.finish(ctx)
        raise ValueError('complaint-parent-unknown-fixed-phase')
    def notify_ready_screenshot(self,ctx,folder,key):
        engine.scope_for_context(ctx)
        """Seal one registered image before the original sender may prepare it.
        Existing uncertain transport is held for original-job reconciliation.
        """
        import execution_timing as timing
        c=ctx['company'];root=Path(c['root']);s=self.ledger(c);task=s['tasks'][key]
        need(w.final_screenshot(s,task),'complaint-parent-final-region-required')
        order=w.send_order(root,s,key)
        need(order.get('scope')=='test' and order.get('target')==delivery_targets.target('negative-review-complaints') and order.get('kind')=='group' and order.get('review_key')==key,'complaint-parent-test-only')
        item={'company':c['company'],'root':str(root),'review_key':key,'order':order,'image_sha256':task['screenshot']['sha256'],'source':task['latest_snapshot']}
        seal=o.immutable(folder/'ready-deliveries'/o.digest(key)/'seal.json',{'kind':'complaint-single-image-ready-seal-v1','dispatch_id':ctx['order']['dispatch_id'],'scope_sha256':ctx['order']['scope_sha256'],'item':item})
        path=timing.sender_path(order['key'])
        if ctx['order'].get('collection_contract')=='three-flow-collection-ready-v1':
            need(not path.exists()and not task.get('wecom')and not task.get('send_attempt'),'complaint-staged-preexisting-sender-hold')
            engine_file=Path(ctx['folder']).parent.parent/'engine.json';state=o.doc(o.ref(engine_file));order_ref=state['order']
            need(o.validate(order_ref)==ctx['order'],'complaint-staged-original-order')
            staged_seal=o.immutable(folder/'ready-deliveries'/o.digest(key)/'collection-seal.json',{'kind':'complaint-pre-delivery-image-seal-v1','order':order_ref,'item':item})
            w.verified_pre_delivery_image(root,s,key,staged_seal)
            return {'seal':staged_seal,'collection_ready':True,'sent_now':False}
        if task.get('wecom'):
            return {'seal':seal,'client':self.client(item,task),'sent_now':False}
        # Never invoke run/prepare over an existing unconfirmed sender, including
        # an unknown send outcome. Its original canonical job must be reconciled.
        need(not path.exists() and not task.get('send_attempt'),'complaint-parent-preexisting-unconfirmed-sender')
        with w.locked(root):
            fresh=self.ledger(c)
            need(w.final_screenshot(fresh,fresh['tasks'][key]) and w.send_order(root,fresh,key)==order and fresh['tasks'][key]['latest_snapshot']==item['source'],'complaint-parent-ready-seal-changed')
            need(not fresh['tasks'][key].get('wecom') and not fresh['tasks'][key].get('send_attempt') and not path.exists(),'complaint-parent-preexisting-unconfirmed-sender')
            w.send_test(root,fresh,key)
        return {'seal':seal,'client':self.client(item,self.ledger(c)['tasks'][key]),'sent_now':True}
    def collect(self,ctx):
        engine.scope_for_context(ctx)
        a=copy.deepcopy(ctx['artifacts']);c=ctx['company'];root=Path(c['root']);i=a['unit_index'];need(a['units']==self.units(c,o.doc(c['ledger'])) and type(i) is int and 0<=i<=len(a['units']),'complaint-parent-original-collection-units-required')
        if i==len(a['units']):return {'done':True}
        u=a['units'][i];folder=self.folder(ctx)/'units'/str(i);folder.mkdir(parents=True,exist_ok=True);x=a.get('unit_artifacts',{});phase=a['unit_phase'];journals=a.get('journals',[])
        def result(next_phase=None,**extra):
            update={'unit_artifacts':x,'journals':list(dict.fromkeys(journals)),**extra}
            if next_phase:update['unit_phase']=next_phase
            update=self.changed(ctx,**update)
            return {'done':False,'artifacts':update,'journal':o.ref(journals[-1]) if journals and Path(journals[-1]).is_file() else None}
        if phase=='acquire':
            from current_complaint_source import prepare
            normaljob,source_ref=prepare(ctx['order'],c,u,folder)
            nav.scope(normaljob)
            x['acquisition']=source_ref;x['job']=o.immutable(folder/'normal-job.json',normaljob)
            return result('navigation')
        job=o.doc(x['job']);need(job['company']==c['company'] and str(job['groupid'])==c['groupid'] and job['start']==u['start'] and job['end_exclusive']==u['end_exclusive'],'complaint-parent-unit-job-scope')
        if phase=='navigation':
            if not x.get('company_context_verified'):
                reply=self.request({'op':'tabs'});need(reply.get('ok'),'complaint-current-tabs-unavailable')
                matching=[t for window in reply['result'] for t in window.get('tabs',[])if t.get('tabId')==self.tab]
                need(len(matching)==1,'complaint-current-tab-ambiguous')
                from urllib.parse import urlsplit,parse_qs
                current_gid=parse_qs(urlsplit(matching[0]['url']).query).get('groupid')
                if current_gid!=[c['groupid']] or x.get('context_work_order'):
                    if not x.get('context_work_order'):x['context_work_order']=self.acquire_job(ctx,u,folder)
                    context_job=o.doc(x['context_work_order']);context_path=Path(context_job['workflow_path']);context_path.parent.mkdir(parents=True,exist_ok=True)
                    with context_path.with_name('.bridge-execution.lock').open('a')as lock:
                        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        workflow=operator.Workflow(context_job,self.tab,invoke=self.request)
                        with contextlib.redirect_stdout(io.StringIO()):operator.run_steps(workflow,context_path,4,False)
                    if str(context_path)not in journals:journals.append(str(context_path))
                    need(not workflow.s.get('last_error')and workflow.s.get('state')!='failed','complaint-company-context-held')
                    if workflow.s['state']!='complete':return result()
                x['company_context_verified']=True
            path=folder/'navigation-state.json'
            with path.with_name(path.name+'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=nav.Navigator(job,self.tab,path,invoke=self.request)
                # Exact opt-in supported visible text schema from the first read;
                # never amend an already observed or active old job.
                if not path.exists():
                    import normal_review_body as rb
                    r.s['parser_contract']={'text_schema':'public-visible-text-v2','image_only_text_schema':rb.SCHEMA,'job_fingerprint':nav.tag(job)}
                r.tick();r.save()
            journals.append(str(path));need(all(t['state']=='confirmed' for t in r.s['calls']),'complaint-parent-navigation-unknown')
            if r.s['phase']!='profileRequired':return result()
            need(r.s.get('stable_normal_verified') is True,'complaint-parent-normal-not-stable');x['navigation']=o.ref(path);return result('normal')
        if phase=='normal':
            page=self.read_normal_scope(job,folder,x['navigation']);raw=o.doc(page);normal.public_identity(raw['tree'],job['identity']);profile,envelope,source=normal_api.build(job,raw,raw,image_only_text_schema=o.doc(x['navigation']).get('parser_contract',{}).get('image_only_text_schema'))
            x.update(page=page,profile=o.immutable(folder/'normal-profile.json',profile),envelope=o.immutable(folder/'normal-envelope.json',envelope),source=o.immutable(folder/'normal-source.json',source));return result('ingest')
        source=o.doc(x['source'])
        if phase=='ingest':
            s=self.ledger(c)
            if u['kind']=='recheck':
                x.update(recheck_keys=u['keys'],review_index=0,operations=[]);return result('recheck')
            # A possible display-name change is never fed to ordinary ingester.
            # Only an already case-linked pending task may use alias v3.
            aliases=[]
            for key in u['keys']:
                task=s['tasks'][key]
                if (task.get('result') or {}).get('alias_ref'):aliases.append(key)
                else:
                    match=[row for row in source['rows'] if s['groupid']+':'+row['review_id']==key]
                    need(len(match)==1 and all(task['review'].get(k,'')==match[0].get(k,'') for k in ('review_id','store','customer','customer_id','text','stars','date','time','product')),'complaint-parent-recheck-needs-explicit-case-alias')
            for oldkey,task in s['tasks'].items():
                for row in source['rows']:
                    if task['review'].get('customer')!=row.get('customer') and all(task['review'].get(k,'')==row.get(k,'') for k in ('store','text','stars','date','product')):
                        need(oldkey in aliases,'complaint-parent-display-name-conflict-needs-case-alias')
            need(not aliases or len(aliases)==len(u['keys']) and u['kind']=='recheck','complaint-parent-mixed-alias-unit-needs-reviewed-split')
            if aliases:
                x.update(alias_keys=aliases,review_index=0,operations=[]);return result('alias')
            with w.locked(root):
                s=self.ledger(c);w.ingest(root,s,x['source']['path'])
            x['keys']=[source['groupid']+':'+row['review_id'] for row in source['rows']];x.update(frame_index=0,review_index=0,operations=[])
            orders.prepare(*(x[k]['path'] for k in ('job','source','envelope','profile')),folder/'result-orders.json');x['orders']=o.ref(folder/'result-orders.json');return result('frames')
        if phase=='recheck':
            import case_alias_v3 as alias
            import apply_case_alias_v3 as apply
            index=x['review_index']
            if index==len(x['recheck_keys']):return result('unit-done')
            for field in ('alias_manifest','exact_manifest'):
                if x.get(field):
                    operation=Path(x[field]['path']).with_name('operation.json')
                    if operation.exists():need(not o.doc(o.ref(operation)).get('state','').startswith('unknown'),'complaint-parent-recheck-unknown-no-replay')
            # Pinned normal reads need not have brought their tab to the front.
            # This separate durable navigation never changes an alias manifest.
            import review_capture_tab as recheck_tab
            focus=recheck_tab.ensure_recheck({k:x[k] for k in ('job','source','profile','envelope')},request=self.request)
            if focus['journal']['path'] not in journals:journals.append(focus['journal']['path'])
            key=x['recheck_keys'][index];task=self.ledger(c)['tasks'][key]
            if not (task.get('result') or {}).get('alias_ref'):
                import complaint_exact_recheck as exact
                # The role order lives two levels above the canonical execution
                # folder; use the exact launcher-owned order, never a new key.
                launcher=o.doc(o.ref(Path(ctx['folder']).parents[1]/'launcher.json'));order_ref=launcher['order']
                if not x.get('exact_manifest'):
                    x['exact_manifest']=exact.prepare(order_ref,root,key,{k:x[k] for k in ('job','source','profile','envelope','page')});return result()
                out=exact.tick(x['exact_manifest'],request=self.request);journals.append(out['operation']['path'])
                if out['state']!='complete':return result()
                receipt=exact.receipt(x['exact_manifest']);applied=exact.apply(receipt);x['operations'].append(applied['operation']);x['review_index']+=1;x.pop('exact_manifest');return result()
            old=o.doc(task['result']['alias_ref']);oldop=o.doc(old['operation']);oldm=oldop['manifest']
            if type(oldm) is dict and set(oldm)=={'path','sha256'}:
                previous=o.doc(oldm);origin=previous['origin']['manifest'];prior=o.ref(alias.v.base(previous)/'apply/operation.json')
            else:
                origin=o.ref(alias.v.v2.folder(oldm)/'manifest.json');prior=o.ref(alias.v.v2.folder(oldm)/'apply/operation.json')
            if not x.get('alias_manifest'):
                prepared=alias.prepare(origin,prior,{'fresh_job':x['job'],'fresh_profile':x['profile'],'normal_before':x['envelope']},o.ref(alias.v.v2.LEASE));need(prepared.get('run_permitted') is not False,'complaint-parent-alias-no-new-current-dispatch-observation');x['alias_manifest']=prepared['manifest'];return result()
            manifest=x['alias_manifest'];out=alias.run(manifest,steps=1,request=self.request);journals.append(str(alias.v.base(o.doc(manifest))/'operation.json'))
            need(out.get('state')!='hold','complaint-parent-original-alias-held');
            if out.get('state')!='complete':return result()
            alias.verify(manifest);receipt=alias.record(manifest)['receipt'];applied=apply.apply(receipt);need(applied['state']=='complete','complaint-parent-alias-apply-incomplete');x['operations'].append(applied['operation']);x['review_index']+=1;x.pop('alias_manifest');return result()
        if phase=='frames':
            index=x['frame_index']
            if index==len(x['keys']):return result('inspect')
            key=x['keys'][index];s=self.ledger(c);task=s['tasks'][key]
            if w.final_screenshot(s,task):
                notified=self.notify_ready_screenshot(ctx,folder,key);journals.append((notified.get('client')or notified['seal'])['path']);x.setdefault('ready_seals',{})[key]=notified['seal'];x['frame_index']+=1;return result()
            self.scroll_review(job,source,x,key,folder)
            # Same original source/notice, deterministic manifest and top key.
            m={k:x[k] for k in ('job','source','envelope','profile','page')};m.update(review_keys=[key],capture_key='complaint-parent:'+o.digest({'dispatch':ctx['order']['dispatch_id'],'key':key,'source':x['source']['sha256']})[:40]);mr=o.immutable(folder/'frames'/o.digest(key)/'manifest.json',m);outdir=Path(mr['path']).parent/'capture';v=screenshot.capture(mr,outdir,pid=self.pid,revision='complaint-region-v1',request=self.request)
            if v['state']=='awaiting-visual-review':
                try:
                    quality=screenshot.region.program_review_quality.create(o.ref(outdir/'preview-registration.json'),outdir/'program-quality')
                except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
                    handoff={'response_kind':'complaint-region-qa-response-v1','preview':o.ref(outdir/'preview-registration.json'),'manifest':mr,'root':str(root),'review_key':key,'program_quality_exception':str(error),'instruction':'Program quality unresolved; keep original preview and no automatic approval.'}
                    return {'done':False,'artifacts':self.changed(ctx,unit_artifacts=x,journals=journals),'handoff':handoff}
                screenshot.region.approve_preview(outdir/'preview-registration.json',quality)
                v={**v,'state':'complete'}
            if v['state']=='awaiting-visual-review':
                handoff={'response_kind':'complaint-region-qa-response-v1','preview':o.ref(outdir/'preview-registration.json'),'manifest':mr,'root':str(root),'review_key':key,'instruction':'Root must view actual PNG and provide existing region quality attestation; never auto-approve.'}
                return {'done':False,'artifacts':self.changed(ctx,unit_artifacts=x,journals=journals),'handoff':handoff}
            need(v['state']=='complete','complaint-parent-region-not-complete')
            with w.locked(root):w.register_review_screenshot(root,self.ledger(c),key,outdir/'registration.json')
            notified=self.notify_ready_screenshot(ctx,folder,key);journals.append((notified.get('client')or notified['seal'])['path']);x.setdefault('ready_seals',{})[key]=notified['seal'];x['frame_index']+=1;return result()
        if phase=='inspect':
            # Resume old units already at inspect without touching an opened form:
            # finish their registered screenshot notifications first, then retain
            # the original inspection manifest/operation and its no-replay guard.
            for ready_key in x['keys']:
                notified=self.notify_ready_screenshot(ctx,folder,ready_key);journals.append((notified.get('client')or notified['seal'])['path']);x.setdefault('ready_seals',{})[ready_key]=notified['seal']
                if notified['sent_now']:return result()
            index=x['review_index']
            if index==len(x['keys']):return result('unit-done')
            key=x['keys'][index];task=self.ledger(c)['tasks'][key];paths={k:x[k]['path'] for k in ('job','source','envelope','profile','page')};mp=folder/'inspections'/o.digest(key)/'manifest.json'
            if task['action'] in ('查看投诉结果','投诉审核中'):
                m=results.prepare(root,{**paths,'orders':x['orders']['path']},key,mp);out=results.tick(m,request=self.request)
                if out['state']!='complete':journals.append(out['operation']);return result()
                state=o.doc(o.ref(out['operation']));values,order,row=results.manifest_inputs(m,historical_complete=True);results.verify_complete(state,m,values,order,row)
            else:
                m={'kind':'complaint-draft-inspection-manifest-v1','root':str(root),'review_key':key,'inputs':{k:x[k] for k in ('job','source','profile','envelope','page')}};draft.inputs(m);o.immutable(mp,m);out=draft.tick(m,request=self.request)
                if out['state']!='complete':journals.append(out['operation']);return result()
                draft.validate(out['operation'],root=root,key=key,snapshot=x['source']['sha256'])
            journals.append(out['operation']);x['operations'].append(o.ref(out['operation']));x['review_index']+=1;return result()
        if phase=='unit-done':
            finished={k:copy.deepcopy(x[k]) for k in x};finished['unit']=u
            return result('acquire',unit_index=i+1,unit_artifacts={},completed_units=a['completed_units']+[finished])
        raise ValueError('complaint-parent-collection-phase-invalid')
    def scroll_review(self,job,source,refs,key,folder):
        rows=[r for r in source['rows'] if source['groupid']+':'+r['review_id']==key];need(len(rows)==1,'complaint-parent-scroll-review-not-unique');row=rows[0];path=folder/'scrolls'/(o.digest(key)+'.json');binding={'source':refs['source'],'job':refs['job'],'review_key':key,'tab_id':self.tab,'selector':row['dom_selector']}
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.with_name(path.name+'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if path.exists():
                previous=o.doc(o.ref(path));need(previous['binding']==binding and previous['state']=='complete','complaint-parent-scroll-unknown-no-replay');o.doc(previous['before']);o.doc(previous['after']);return
            before=self.read(job,path.parent,'before');raw=o.doc(before);normal.navigation_probe(raw['tree'],job,text_schema='public-visible-text-v2',image_only_text_schema=o.doc(refs['profile']).get('image_only_text_schema'));target=normal.one(normal.flatten(raw['tree']['root']),{'selector':row['dom_selector']},'scroll-review');need(target.get('attributes',{}).get('class')=='commentItem-jrXo5p','complaint-parent-scroll-card-shape')
            command={'op':'scroll','tabId':self.tab,'locator':{'by':'selector','value':target['selector']}};state={'kind':'complaint-parent-review-scroll-v1','binding':binding,'before':before,'command':command,'state':'unknown'};engine.atomic(path,state)
            reply=self.request(command);state['reply']=reply;engine.atomic(path,state)
            need(reply.get('ok') is True,'complaint-parent-scroll-reply-failed');node=reply['result'].get('scrolled',{});need(node.get('selector')==target['selector'] and isinstance(target.get('tag'),str) and bool(target['tag']) and node.get('tag')==target['tag'] and reply['result'].get('version')==nav.VERSION,'complaint-parent-scroll-reply-unverified')
            after=self.read(job,path.parent,'after');fresh=o.doc(after);need(fresh['tab']==raw['tab'],'complaint-parent-scroll-window-changed');normal.navigation_probe(fresh['tree'],job,text_schema='public-visible-text-v2',image_only_text_schema=o.doc(refs['profile']).get('image_only_text_schema'));state.update(state='complete',after=after,visibility_claimed=False);engine.atomic(path,state)
    def zero_notice_item(self,order,c,company_state):
        zn=_zero_notice_module()
        units=[u for u in company_state['artifacts']['completed_units']if u['unit']['kind']=='new']
        if not units or any(o.doc(u['source'])['rows']for u in units):return None
        work=o.ref(o.order_path(ROOT/'runtime/workshop-director',order['dispatch_id']));index=order['companies'].index(c);folder=o.location(work)/'companies'/str(index)/'zero-result-notice'
        native=zn.prepare(folder,'negative-review-complaints',c['company'],c['start'],c['end_exclusive'],work,[u['source']for u in units],module_ref=_ZERO_NOTICE_MODULE)
        return {'company':c['company'],'root':c['root'],'zero_result':True,'order':native}
    def expected_orders(self,order,companies,*,active=None,zero_notices=False):
        items=[];seen=set()
        for i,(c,cs) in enumerate(zip(order['companies'],companies)):
            if active is not None and i not in active:continue
            if c['skipped']:continue
            root=Path(c['root']);s=self.ledger(c)
            if order.get('collection_contract')=='three-flow-collection-ready-v1':items.append(self.collection_workbook_item(order,c,cs,s))
            if zero_notices:
                notice=self.zero_notice_item(order,c,cs)
                if notice:items.append(notice)
            for u in cs['artifacts']['completed_units']:
                for key in u.get('keys',[]):
                    if (str(root),key) in seen:continue
                    seen.add((str(root),key));send=w.send_order(root,s,key);need(send['scope']=='test' and send['target']==delivery_targets.target('negative-review-complaints'),'complaint-parent-test-only');items.append({'company':c['company'],'root':str(root),'review_key':key,'order':send,'image_sha256':s['tasks'][key]['screenshot']['sha256'],'source':s['tasks'][key]['latest_snapshot']})
        return items
    def seal(self,ctx):
        admission=engine.scope_for_context(ctx);active=admission['active_indices']if admission else None
        items=self.expected_orders(ctx['order'],ctx['companies'],active=active,zero_notices=True)
        import execution_timing as timing
        for item in items:
            if item.get('collection_workbook'):
                need(not timing.sender_path(item['order']['key']).exists(),'complaint-workbook-preexisting-sender');continue
            if item.get('zero_result'):
                zn=_zero_notice_module()
                if zn.sender_path(item['order']['key']).exists():
                    need((Path(item['order']['text_file']).parent/'notice-intent.json').exists(),'complaint-zero-unowned-sender');zn.client(item['order'])
                continue
            t=self.ledger({'root':item['root']})['tasks'][item['review_key']];path=timing.sender_path(item['order']['key'])
            # Old legitimately confirmed screenshots retain their original key;
            # otherwise a canonical preexisting sender cannot be washed fresh.
            if path.exists():
                need(t.get('wecom') and o.doc(o.ref(path))==o.doc(t['wecom']),'complaint-parent-preexisting-unconfirmed-sender');self.client(item,t)
        manifest=o.immutable(Path(ctx['folder'])/'delivery-manifest.json',{'zero_result_contract':'notify-confirmed-zero-v1','zero_module_ref':_ZERO_NOTICE_MODULE,'kind':'complaint-complete-delivery-set-v1','dispatch_id':ctx['order']['dispatch_id'],'scope_sha256':ctx['order']['scope_sha256'],'orders':items,'no_prepare_before_seal':True})
        return {'manifest':manifest,'orders':len(items)}
    def collection_workbook(self,ctx):
        engine.scope_for_context(ctx);need(ctx['order'].get('collection_contract')=='three-flow-collection-ready-v1','complaint-staged-policy-required')
        import collection_ready
        c=ctx['company'];root=Path(c['root']);state=self.ledger(c);before=copy.deepcopy(state)
        with w.locked(root):
            need(self.ledger(c)==before,'complaint-workbook-ledger-race')
            import current_complaint_workbook
            book,_=current_complaint_workbook.write(c,{'artifacts':ctx['artifacts']},state,Path(ctx['folder'])/'current-workbook');state['xlsx_dirty']=False;w.atomic(root/'state.json',state)
        current=self.ledger(c);need({k:v for k,v in current.items()if k!='xlsx_dirty'}=={k:v for k,v in before.items()if k!='xlsx_dirty'}and current.get('xlsx_dirty')is False,'complaint-workbook-nonartifact-mutation')
        folder=Path(ctx['folder'])/'collection-workbook';file=collection_ready.immutable(folder/'投诉处理结果汇总.xlsx',o.raw(book));source=collection_ready.immutable(folder/'ledger.json',o.raw(o.ref(root/'state.json')))
        material={'kind':'complaint-collection-workbook-v1','company':c['company'],'groupid':c['groupid'],'start':c['start'],'end_exclusive':c['end_exclusive'],'file':file,'ledger_source':source,'producer':'current-business-rows'}
        return {'done':True,'artifacts':self.changed(ctx,collection_workbook=material)}
    def collection_workbook_item(self,order,c,cs,ledger):
        material=cs['artifacts']['collection_workbook'];need(material.get('kind')=='complaint-collection-workbook-v1'and all(material.get(k)==c[k]for k in('company','groupid','start','end_exclusive'))and o.doc(material['ledger_source'])==ledger,'complaint-ready-workbook-source')
        o.raw(material['file'])
        key='complaint-summary:'+o.digest({'dispatch_id':order['dispatch_id'],'company':c['company'],'groupid':c['groupid'],'start':c['start'],'end_exclusive':c['end_exclusive']})[:40]
        return {'company':c['company'],'root':c['root'],'collection_workbook':True,'order':{'part':'summary-workbook','type':'file','key':key,'kind':'group','target':delivery_targets.target('negative-review-complaints'),'scope':'test','file':material['file']['path'],'file_sha256':material['file']['sha256']}}
    def collection_seal(self,ctx):
        engine.scope_for_context(ctx);need(ctx['order'].get('collection_contract')=='three-flow-collection-ready-v1','complaint-staged-policy-required')
        for c,cs in zip(ctx['order']['companies'],ctx['companies']):
            if c['skipped']:continue
            state=self.ledger(c)
            for unit in cs['artifacts']['completed_units']:
                for key in unit.get('keys',[]):
                    task=state['tasks'][key];w.verified_pre_delivery_image(Path(c['root']),state,key,unit['ready_seals'][key])
                    need(w.collection_processed(task),'complaint-staged-processing-not-ready')
            need(not any(b.get('closed_at')for b in state['batches'].values()if b.get('start')==c['start']and b.get('end_exclusive')==c['end_exclusive']),'complaint-staged-cursor-already-closed')
        delivery=self.seal(ctx)
        value={'kind':'complaint-collection-ready-v1','order':o.ref(o.order_path(Path(ctx['folder']).parent.parent,ctx['order']['dispatch_id'])),'scope_sha256':ctx['order']['scope_sha256'],'companies':ctx['companies'],'delivery_plan':delivery['manifest'],'collection_ready':True,'delivery_complete':False,'cursor_advanced':False}
        return {'done':True,'ready':o.immutable(Path(ctx['folder'])/'collection-ready.json',value)}
    def send(self,ctx):
        engine.scope_for_context(ctx)
        c=ctx['company'];a=ctx['artifacts'];manifest=o.doc(a['delivery_manifest']);items=[x for x in manifest['orders'] if x['company']==c['company']];_zero_notice_module(manifest['zero_module_ref'])if manifest.get('zero_result_contract')=='notify-confirmed-zero-v1'else None;s=self.ledger(c);root=Path(c['root'])
        for item in items:
            if item.get('zero_result'):
                zn=_zero_notice_module()
                r=zn.send(Path(item['order']['text_file']).parent,item['order']);a={**a,'zero_result_notification':r};continue
            key=item['review_key'];need(w.send_order(root,s,key)==item['order'],'complaint-parent-sealed-order-changed')
            if s['tasks'][key].get('wecom'):self.client(item,s['tasks'][key]);continue
            with w.locked(root):s=self.ledger(c);w.send_test(root,s,key)
            t=self.ledger(c)['tasks'][key];client=self.client(item,t);journals=a.get('journals',[])+[t['send_attempt']['job_path']];return {'done':False,'journal':client,'artifacts':self.changed(ctx,journals=journals,**({'zero_result_notification':a['zero_result_notification']}if a.get('zero_result_notification')else{}))}
        return {'done':True,'artifacts':self.changed(ctx,**({'zero_result_notification':a['zero_result_notification']}if a.get('zero_result_notification')else{}))}
    def client(self,item,t):
        import execution_timing as timing
        r=t['wecom'];state=o.doc(r);job=state['job'];path=timing.sender_path(item['order']['key']);need(path.is_file() and o.doc(o.ref(path))==state,'complaint-parent-canonical-client-required');need(job.get('key')==item['order']['key'] and job.get('file_sha256')==item['image_sha256'] and job.get('target')==delivery_targets.target('negative-review-complaints') and job.get('scope')=='test' and state.get('status')=='complete' and state.get('phase')=='done' and state.get('sent') is True and state.get('ui_confirmed') is True and not state.get('error') and any(event.get('stage')=='ui-confirmed' for event in state.get('events',[])),'complaint-parent-client-not-confirmed');need(state.get('fingerprint')==__import__('hashlib').sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'complaint-parent-client-fingerprint');return o.ref(path)
    def analysis_requests(self,ctx):
        engine.scope_for_context(ctx)
        c=ctx['company'];s=self.ledger(c);folder=self.folder(ctx);requests=[]
        for unit in ctx['artifacts']['completed_units']:
            for key in unit.get('keys',[]):
                task=s['tasks'][key]
                if task['action']!='投诉' or task['status']=='draft_ready':continue
                request=w.analysis_order(s,key)
                if ctx['order'].get('collection_contract')=='three-flow-collection-ready-v1':
                    request['collection_seal']=unit['ready_seals'][key];w.verified_pre_delivery_image(Path(c['root']),s,key,request['collection_seal'])
                ops=[r for r in unit['operations'] if o.doc(r).get('manifest',{}).get('review_key')==key];need(len(ops)==1,'complaint-parent-draft-inspection-required');request['inspection_operation']=ops[0];draft.validate(ops[0]['path'],root=c['root'],key=key,snapshot=task['latest_snapshot']['sha256'])
                requests.append(request)
        return requests
    def analyze(self,ctx):
        requests=self.analysis_requests(ctx)
        if not requests:return {'done':True,'artifacts':self.changed(ctx)}
        return {'done':False,'handoff':{'response_kind':'complaint-analysis-batch-response-v1','root':ctx['company']['root'],'orders':requests,'instruction':'Current review classification/draft only; five-type and current form-option checks remain mandatory. No historical examples. No submit.'}}
    def accept(self,request,response):
        if request['response_kind']=='complaint-region-qa-response-v1':
            need(set(response)=={'kind','request','attestation'},'complaint-parent-qa-response-shape');preview=request['preview'];o.raw(preview);o.raw(response['attestation']);screenshot.region.approve_preview(preview['path'],response['attestation']);final=Path(preview['path']).with_name('registration.json')
            root=Path(request['root'])
            with w.locked(root):w.register_review_screenshot(root,w.load(root),request['review_key'],final)
            return {'ledger_current':o.ref(root/'state.json'),'qa_registration':o.ref(final)}
        need(request['response_kind']=='complaint-analysis-batch-response-v1' and set(response)=={'kind','request','analyses'},'complaint-parent-analysis-response-shape');expected={x['review_key']:x for x in request['orders']};refs=response['analyses'];need(type(refs) is list and len(refs)==len(expected),'complaint-parent-complete-analysis-set');values=[o.doc(r) for r in refs];need({x.get('review_key') for x in values}==set(expected),'complaint-parent-analysis-set-changed');root=Path(request['root'])
        with w.locked(root):
            s=w.load(root)
            for r,a in zip(refs,values):
                original=expected[a['review_key']];key=a['review_key'];need(a['snapshot_sha256']==original['snapshot_sha256'] and a.get('platform_category_evidence',{}).get('inspection_operation')==original['inspection_operation'],'complaint-parent-analysis-original-option-binding')
                w.analyze(root,s,key,r['path'],collection_seal=original.get('collection_seal'));s=w.load(root)
        return {'ledger_current':o.ref(root/'state.json'),'analysis_responses':refs}
    def verify_accept(self,request,response,updates):
        need(o.ref(Path(request['root'])/'state.json')==updates['ledger_current'],'complaint-parent-accept-ledger-changed')
        if request['response_kind']=='complaint-region-qa-response-v1':
            screenshot.region.verify(updates['qa_registration']['path']);w.send_order(Path(request['root']),w.load(Path(request['root'])),request['review_key']);return
        s=w.load(Path(request['root']))
        for r in response['analyses']:
            a=o.doc(r);task=s['tasks'][a['review_key']];need(task['status']=='draft_ready' and {k:v for k,v in task['analysis'].items() if k!='evidence'}==a and task['analysis']['evidence']['sha256']==r['sha256'],'complaint-parent-analysis-accept-not-recorded');draft.validate_analysis(request['root'],s,a['review_key'],a)
            import classification_policy
            classification_policy.validate(s,a['review_key'],a)
    def close(self,ctx):
        engine.scope_for_context(ctx)
        c=ctx['company'];root=Path(c['root']);s=self.ledger(c)
        if c['start']<c['end_exclusive']:
            delivery=o.doc(ctx['artifacts']['delivery_manifest']);_zero_notice_module(delivery['zero_module_ref'])if delivery.get('zero_result_contract')=='notify-confirmed-zero-v1'else None;notice=self.zero_notice_item(ctx['order'],c,{'artifacts':ctx['artifacts']})if delivery.get('zero_result_contract')=='notify-confirmed-zero-v1'else None
            if notice:
                zn=_zero_notice_module()
                need(ctx['artifacts'].get('zero_result_notification')is not None,'complaint-zero-notification-required-before-cursor');zn.client(notice['order'],ctx['artifacts']['zero_result_notification'])
            batch=c['start']+'_'+c['end_exclusive'];need(batch in s['batches'],'complaint-parent-current-batch-required')
            if not s['batches'][batch]['closed_at']:
                with w.locked(root):w.close_batch(root,self.ledger(c),batch)
        s=self.ledger(c)
        if s.get('xlsx_dirty'):
            with w.locked(root):w.export_xlsx(root,self.ledger(c))
        return {'done':True,'artifacts':self.changed(ctx),'ledger':o.ref(root/'state.json'),'workbook':o.ref(root/'投诉处理结果汇总.xlsx')}
    def finish(self,ctx):
        admission=engine.scope_for_context(ctx);active=admission['active_indices']if admission else None
        order=ctx['order'];_zero_notice_module(o.doc(ctx['delivery']['manifest'])['zero_module_ref'])if o.doc(ctx['delivery']['manifest']).get('zero_result_contract')=='notify-confirmed-zero-v1'else None;need(o.doc(ctx['delivery']['manifest'])['orders']==self.expected_orders(order,ctx['companies'],active=active,zero_notices=o.doc(ctx['delivery']['manifest']).get('zero_result_contract')=='notify-confirmed-zero-v1'),'complaint-parent-final-delivery-set-changed');evidence=[];clients=[];count=0
        origin=o.doc(o.ref(Path(ctx['folder'])/'origin.json'));started=datetime.fromisoformat(origin['wall_started_at'])
        for i,(c,cs) in enumerate(zip(order['companies'],ctx['companies'])):
            if active is not None and i not in active:continue
            if c['skipped']:self.skipped(c);evidence.append(c['ledger']);continue
            s=self.ledger(c);need(s['mode']=='draft-only' and s['browser_backend']=='local-dom-bridge' and s['next_start']>=c['end_exclusive'] and not s.get('xlsx_dirty'),'complaint-parent-final-ledger-incomplete');evidence.append(o.ref(Path(c['root'])/'state.json'))
            for unit in cs['artifacts']['completed_units']:
                job=o.doc(unit['job']);source=o.doc(unit['source']);need(normal.joined(job,o.doc(unit['envelope']),o.doc(unit['profile']),job['source_receipt'],job['source_receipt_sha256'])==source,'complaint-parent-final-source-changed');need(datetime.fromisoformat(source['observed_at'])>=started,'complaint-parent-old-source-not-fresh');evidence.extend(unit[k] for k in ('job','source','envelope','profile','page','acquisition'));count+=len(source['rows']) if unit['unit']['kind']=='new' else 0
                for op in unit.get('operations',[]):
                    state=o.doc(op)
                    if state.get('kind')=='apply-exact-existing-case-v1':
                        import complaint_exact_recheck
                        complaint_exact_recheck.verify_apply(op)
                    elif state.get('kind')=='apply-public-case-alias-v3':
                        import case_alias_versions
                        case_alias_versions.verify_apply(op)
                    elif state.get('manifest',{}).get('kind')=='complaint-draft-inspection-manifest-v1':draft.validate(op['path'])
                    else:
                        m=state['manifest'];v,ro,row=results.manifest_inputs(m,historical_complete=True);results.verify_complete(state,m,v,ro,row)
                    evidence.append(op)
            for key in c['recheck_ids']:
                t=s['tasks'][key];need(t['status'] in ('resolved','draft_ready','existing_pending'),'complaint-parent-backlog-unfinished')
                if t['action'] in ('查看投诉结果','投诉审核中'):
                    need(t.get('result') and datetime.fromisoformat(t['result']['observed_at'])>=started,'complaint-parent-backlog-not-rechecked');evidence.append(t['result']['evidence'])
        for item in o.doc(ctx['delivery']['manifest'])['orders']:
            if item.get('zero_result'):
                zn=_zero_notice_module()
                clients.append(zn.client(item['order']))
            else:clients.append(self.client(item,self.ledger({'root':item['root']})['tasks'][item['review_key']]))
        if admission:evidence.extend(admission['evidence'])
        for r in evidence+clients:o.raw(r)
        result={'outcome':'zero-result-client-confirmed-draft-only'if not count and any(i.get('zero_result')for i in o.doc(ctx['delivery']['manifest'])['orders'])else 'data-client-confirmed-draft-only' if count else 'no-new-data-backlog-complete' if clients or any(c['recheck_ids'] for i,c in enumerate(order['companies'])if active is None or i in active) else 'no-data-complete','evidence':evidence,'clients':clients,'submission_enabled':False,'production_sent':False,'source_rows':count}
        if admission:result.update(active_scope_complete=True,original_scope_complete=False,retired_incomplete=True,active_indices=active,retired_indices=admission['retired_indices'],company_scope_reconciliation=admission['proof'])
        return result

    def verify_collection_materials(self,order,state,ready,ledgers):
        need(order.get('collection_contract')=='three-flow-collection-ready-v1'and ready.get('kind')=='complaint-collection-ready-v1'and ready.get('order')==state['order']and ready.get('scope_sha256')==order['scope_sha256']and ready.get('companies')==state['companies']and ready.get('collection_ready')is True and ready.get('delivery_complete')is False and ready.get('cursor_advanced')is False,'complaint-ready-material-shape')
        manifest=o.doc(ready['delivery_plan']);_zero_notice_module(manifest['zero_module_ref']);need(manifest['kind']=='complaint-complete-delivery-set-v1'and manifest['dispatch_id']==order['dispatch_id']and manifest['scope_sha256']==order['scope_sha256'],'complaint-ready-plan-binding')
        expected=[];companies=[];origin=o.doc(o.ref(o.location(state['order'])/'origin.json'));begun=datetime.fromisoformat(origin['wall_started_at'])
        for c,cs in zip(order['companies'],state['companies']):
            if c['skipped']:continue
            ledger=ledgers[c['company']];expected.append(self.collection_workbook_item(order,c,cs,ledger));need(ledger['company']==c['company']and ledger['groupid']==c['groupid']and ledger['mode']=='draft-only'and ledger['browser_backend']=='local-dom-bridge'and ledger['next_start']==c['start'],'complaint-ready-ledger-scope');count=0;keys=set();new_sources=[]
            for unit in cs['artifacts']['completed_units']:
                job=o.doc(unit['job']);source=o.doc(unit['source']);need(normal.joined(job,o.doc(unit['envelope']),o.doc(unit['profile']),job['source_receipt'],job['source_receipt_sha256'])==source,'complaint-ready-source-changed');need(datetime.fromisoformat(source['observed_at'])>=begun,'complaint-ready-old-source');need(source['company']==c['company']and str(source['groupid'])==c['groupid'],'complaint-ready-source-company')
                if unit['unit']['kind']=='new':count+=len(source['rows']);new_sources.append(unit['source']);need((source['start'],source['end_exclusive'])==(c['start'],c['end_exclusive']),'complaint-ready-source-date')
                for op in unit.get('operations',[]):
                    operation=o.doc(op)
                    if operation.get('kind')=='apply-exact-existing-case-v1':__import__('complaint_exact_recheck').verify_apply(op)
                    elif operation.get('kind')=='apply-public-case-alias-v3':__import__('case_alias_versions').verify_apply(op)
                    elif operation.get('manifest',{}).get('kind')=='complaint-draft-inspection-manifest-v1':draft.validate(op['path'])
                    else:
                        values,ro,row=results.manifest_inputs(operation['manifest'],historical_complete=True);results.verify_complete(operation,operation['manifest'],values,ro,row)
                for key in unit.get('keys',[]):
                    task=ledger['tasks'][key];w.verified_pre_delivery_image(Path(c['root']),ledger,key,unit['ready_seals'][key]);need(w.collection_processed(task),'complaint-ready-task-not-processed')
                    if task.get('analysis'):w.verify_evidence(task['analysis']['evidence'])
                    if task.get('result'):w.verify_evidence(task['result']['evidence'])
                    if key not in keys:expected.append({'company':c['company'],'root':c['root'],'review_key':key,'order':w.send_order(Path(c['root']),ledger,key),'image_sha256':task['screenshot']['sha256'],'source':task['latest_snapshot']});keys.add(key)
            if c['start']<c['end_exclusive']:need(len(new_sources)==1,'complaint-ready-current-source-required')
            zero=[x for x in manifest['orders']if x['company']==c['company']and x.get('zero_result')]
            if new_sources and count==0:
                need(len(zero)==1,'complaint-ready-zero-notice-required');item=zero[0];binding=item['order']['zero_result_binding'];need(binding['flow']=='negative-review-complaints'and binding['company']==c['company']and(binding['start'],binding['end_exclusive'])==(c['start'],c['end_exclusive'])and binding['sources']==new_sources and binding['work_order']==state['order'],'complaint-ready-zero-scope');_zero_notice_module().job(item['order']);expected.append(item)
            else:need(not zero,'complaint-ready-foreign-zero-notice')
            companies.append({k:c[k]for k in('company','groupid','start','end_exclusive')}|{'count':count})
        need(sorted(expected,key=lambda x:x['order']['key'])==sorted(manifest['orders'],key=lambda x:x['order']['key']),'complaint-ready-exact-delivery-set')
        return {'companies':companies}

_ZERO_NOTICE_PATH=ROOT/'skills/workshop-director/scripts/zero_result_notice.py'
_ZERO_NOTICE_MODULE={'path':str(_ZERO_NOTICE_PATH),'sha256':__import__('hashlib').sha256(_ZERO_NOTICE_PATH.read_bytes()).hexdigest()}
def _zero_notice_module(reference=None):
    expected=_ZERO_NOTICE_MODULE
    need(reference is None or reference==expected,'zero-notice-module-binding')
    path=Path(expected['path'])
    need(path==ROOT/'skills/workshop-director/scripts/zero_result_notice.py'and path.is_absolute()and path.resolve()==path and not any(p.is_symlink()for p in (path,*path.parents))and path.is_file(),'zero-notice-module-origin')
    need(__import__('hashlib').sha256(path.read_bytes()).hexdigest()==expected['sha256'],'zero-notice-module-code-drift')
    sys.path.insert(0,str(path.parent))
    import zero_result_notice
    need(Path(zero_result_notice.__file__)==path,'zero-notice-loaded-module-origin')
    return zero_result_notice
