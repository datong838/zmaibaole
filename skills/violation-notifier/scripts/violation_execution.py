"""Durable fixed violation phase graph. No arbitrary commands or transport ports.
ProductionPorts calls the existing role APIs. AI/QA are hash-bound inputs, never
fake completions. Candidate; no UI has been used to validate this parent.
"""
import copy,fcntl,hashlib,json,os,sys
from pathlib import Path
if __name__=='__main__':sys.modules['violation_execution']=sys.modules[__name__]
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(ROOT/'skills/workshop-director/scripts'))
import role_execution_order as o
PHASES=('plan','company','center','center-query','center-pages','records-open','records-query','details','source','ingest','build','copy','profile','frames','chain','ready')
def atomic(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def view(s):
    last=s['calls'][-1] if s['calls'] else None
    return {**({'collection_ready':s['collection_ready'],'delivery_complete':False}if s.get('collection_ready')else{}),'status':s['status'],'phase':s['phase'],'company_index':s['index'],'waiting_for':s.get('waiting_for'),'handoff':s.get('handoff'),'business_journals':s.get('business_journals',[]),'parent_is_not_business_progress':True,'error':s.get('error'),'last_action':{k:last[k] for k in ('step','state','intent_at','result','error') if k in last} if last else None,'recovery_policy':'Original parent status and named child journal only; no restart/new key/automatic reissue for unknown input.'}
VIOLATION_HOLD_RESUME_KIND='violation-engine-hold-readonly-resume-v1'
READONLY_RESUMABLE_STEPS=('plan','company','records-open','records-query','details','source','frames','company-delivery','collection-seal')
def resume_engine_hold(engine):
    # B85: a failed records-open leaves engine.json at hold with one 'failed'
    # tail call, and step() returns at the terminal-state guard before any
    # tick, so a re-dispatched attempt starts a child that only views the
    # previous state (attempt-3: rc=0, one view, no work). Resuming is allowed
    # only for a read-only step, only for the single failed tail call, only
    # against these exact engine bytes and only once - adopting the proof
    # rewrites engine.json. The failed call is retired as superseded rather
    # than dropped: its index, step and error stay in the journal as evidence,
    # and the engine_hold_resumes record at the same call index is what the
    # collection-ready audit (B83/B83a) admits.
    proof_path=engine.file.parent/'resume-engine-hold.json'
    if not proof_path.exists()or engine.s.get('status')!='hold':return False
    proof=o.doc(o.ref(proof_path));o.need(proof.get('kind')==VIOLATION_HOLD_RESUME_KIND,'engine-hold-resume-kind')
    o.need(proof.get('engine')==o.ref(engine.file),'engine-hold-resume-engine-bytes')
    o.need(engine.s.get('error')==proof.get('original_error'),'engine-hold-resume-error')
    o.need(bool(engine.s['calls']),'engine-hold-resume-current-tail-required')
    index=len(engine.s['calls'])-1;call=engine.s['calls'][-1]
    returned_hold=call.get('state')=='returned' and call.get('applied') and o.doc(call['result']).get('hold')==engine.s['error']
    o.need(call.get('state')=='failed' or returned_hold,'engine-hold-resume-current-held-tail')
    o.need(call.get('step')in READONLY_RESUMABLE_STEPS,'engine-hold-resume-readonly-step')
    if call['step']=='company':
        navigation=o.doc(o.ref(engine.file.parent/'companies'/str(engine.s['index'])/'company-navigation/workflow.json'))
        o.need(navigation.get('state')=='running' and not navigation.get('last_error') and all(x.get('state')=='confirmed'for x in navigation.get('calls',[])),'engine-hold-current-company-frontier')
    if call['step']=='details':
        detail=o.doc(proof['detail_state'])
        read_detail=detail.get('phase')in('read-detail','close-ready') and not detail.get('hold')
        if detail.get('phase')=='close-ready':
            o.need(not detail.get('current',{}).get('before_close'),'engine-hold-resume-close-not-issued')
        return_read=False
        if detail.get('phase')=='auto-rates-center-ready':
            current_return=proof['detail_return_state'];expected=Path(detail['automatic_rates_stage']['original_parent']['path']).parent/'rates-recovery/state.json'
            o.need(current_return['path']==str(expected),'engine-hold-resume-current-return-path')
            returning=o.doc(current_return)
            return_read=returning.get('phase')in('center-range','center-next','center-read-two','open-records','inspect-records','normal-restored-ready') and (not returning.get('calls')or returning['calls'][-1].get('state')=='confirmed')
        o.need((read_detail or return_read) and detail.get('calls') and detail['calls'][-1].get('state')=='confirmed','engine-hold-resume-current-detail-read-required')
    if call['step']=='company-delivery':
        import current_company_delivery as company_delivery
        order=o.doc(engine.ref);company=order['companies'][engine.s['index']]['company'];path=company_delivery.output_path(company,order['day'])/'current-batch.json'
        if not path.exists():o.need(proof.get('company_before_send')is True,'company-resume-before-send-proof-required')
        else:
            o.need(proof.get('company_plan')==o.ref(path),'company-resume-current-plan-required');plan=o.doc(proof['company_plan'])
            o.need(plan['company']==company and plan['day']==order['day'],'company-resume-current-scope')
            for item in plan['items']:
                sender=company_delivery.delivery.sender_path(item,ROOT/'runtime/wecom-messenger')
                if sender.exists():company_delivery.delivery.confirmed(item,ROOT/'runtime/wecom-messenger')
    o.need(proof.get('failed_call')=={'index':index,'step':call['step'],'error':call.get('error')},'engine-hold-resume-failed-call-binding')
    marker={'proof':o.ref(proof_path),'at':proof.get('at'),'reason':proof.get('reason')}
    if returned_hold:call['hold_released_by']=marker
    else:call['state']='superseded';call['superseded_by']=marker
    engine.s.update(status='running');engine.s.pop('error',None)
    engine.s.setdefault('engine_hold_resumes',[]).append({'proof':o.ref(proof_path),'at':proof.get('at'),'call_index':index,'step':call['step']})
    engine.save();return True
def reconcile_interrupted_detail(engine_ref,stopped_child_ref):
    """Adopt the current settled read frontier after a confirmed child exit.

    The caller holds the existing browser resource lock. No browser input is
    allowed here, and an unresolved native action remains unresolved.
    """
    import governance_detail as d
    import governance_stop_loss_production as automatic
    import governance_stop_loss_integration as integration
    state=o.doc(engine_ref);folder=Path(engine_ref['path']).parent
    launcher=o.doc(o.ref(folder/'launcher.json'));exit=o.doc(stopped_child_ref)
    o.need(launcher['status']=='hold' and launcher.get('error')=='execution-child-stopped' and launcher['order']==state['order'],'interrupted-detail-stopped-parent-required')
    last=launcher['calls'][-1]
    o.need(last['state']=='returned' and last['result']==stopped_child_ref and exit['launch']==last['launch'] and exit['argv']==last['argv'] and exit['returncode']!=0,'interrupted-detail-confirmed-exit-required')
    if state['phase']=='frames':
        call=state['calls'][-1];a=state['companies'][state['index']]['artifacts']
        o.need(state['status']=='running' and call['state']=='unknown' and call['step']=='frames' and call['company_index']==state['index'] and call['context']['artifacts']==a,'stopped-frame-current-read-required')
        o.need(a['frame_index']>0 and exit['stderr'].rstrip().endswith('ValueError: candidate-code-graph-changed') and 'm=o.doc(r);checked=region.validate_frame' in exit['stderr'],'stopped-frame-not-proven-before-input')
        if a['frame_state']:
            fs=a['frame_state'];nav=o.doc(fs['navigation_checkpoint'])
            o.need(fs['phase']in('scroll','capture') and nav['binding']['source']==a['source'] and nav['binding']['profile']==a['profile'] and nav['last_observation']==fs['observation'] and nav['operations'][-1]['state']=='complete','stopped-frame-current-navigation-unresolved')
        for frame in a['frames']:o.raw(frame)
        result={'done':False,'interrupted_child_exit':stopped_child_ref,'stopped_before_input':True,'no_business_input':True}
        result_ref=o.immutable(folder/'receipts'/(str(len(state['calls'])).zfill(5)+'.json'),result)
        o.need(o.ref(folder/'engine.json')==engine_ref,'interrupted-detail-engine-changed')
        call.update(state='returned',result=result_ref,applied=True,reconciled_from_stopped_child=stopped_child_ref)
        atomic(folder/'engine.json',state);return result_ref
    o.need(state['status']=='running' and state['phase']=='details' and state['calls'][-1]['state']=='unknown' and state['calls'][-1]['step']=='details','interrupted-detail-current-logical-call-required')
    order=o.doc(state['order']);index=state['index'];call=state['calls'][-1]
    o.need(call['company_index']==index and call['context']['artifacts']==state['companies'][index]['artifacts'],'interrupted-detail-current-company-required')
    manifest=o.doc(o.ref(folder/'companies'/str(index)/'detail-manifest.json'));v=d.inputs(manifest)
    path=automatic.state_path(manifest,v);parent=o.doc(o.ref(path))
    o.need(parent['phase']=='auto-rates-center-ready' and not d.unresolved_detail_calls(parent) and parent['calls'][-1]['state']=='confirmed','interrupted-detail-native-outcome-unresolved')
    def readonly(command):raise ValueError('interrupted-detail-input-and-live-read-denied')
    ports=automatic.Ports(manifest,readonly);flow=integration.Flow(manifest,v,parent,ports)
    o.need(ports.reconcile_current_return(flow,parent),'interrupted-detail-no-settled-return-frontier')
    result={'done':False,'journal':o.ref(path),'interrupted_child_exit':stopped_child_ref,'current_return_state':o.ref(flow.path),'no_business_input':True}
    result_ref=o.immutable(folder/'receipts'/(str(len(state['calls'])).zfill(5)+'.json'),result)
    o.need(o.ref(folder/'engine.json')==engine_ref,'interrupted-detail-engine-changed')
    call.update(state='returned',result=result_ref,applied=True,reconciled_from_stopped_child=stopped_child_ref)
    atomic(folder/'engine.json',state)
    return result_ref

class Engine:
    def __init__(self,order_ref,*,ports,clock):
        self.ref=order_ref;self.ports=ports;self.clock=clock;self.folder=o.location(order_ref);self.file=self.folder/'engine.json'
    def save(self):atomic(self.file,self.s)
    def load(self,*,create=False):
        self.order=o.validate(self.ref)
        if self.file.exists():
            self.s=json.loads(self.file.read_bytes());o.need(self.s['order']==self.ref and self.s['scope_sha256']==self.order['scope_sha256'],'execution-original-engine-required')
        else:
            o.need(create,'execution-not-started-readonly')
            self.ports.validate_origins(self.order)
            self.s={'kind':'violation-execution-v1','order':self.ref,'scope_sha256':self.order['scope_sha256'],'status':'running','phase':'plan','index':0,'companies':[{'artifacts':{},'phase':'plan'} for _ in self.order['companies']],'calls':[],'business_journals':[]}
            self.save()
        return self.s
    def action(self,name,context):
        if self.s.get('reboot_continuation'):
            import violation_reboot_continuation as reboot
            o.need(reboot.allowed_calls(self.s,self.s['reboot_continuation']),'execution-reboot-unresolved-calls')
        else:o.need(not any(c['state'] in ('unknown','failed') for c in self.s['calls'][-1:]),'execution-unknown-no-replay')
        unconsumed=[c for c in self.s['calls'][-1:] if c['state']=='returned' and not c.get('applied')]
        if unconsumed:
            o.need(len(unconsumed)==1 and unconsumed[0]['step']==name and unconsumed[0]['company_index']==self.s['index'] and unconsumed[0]['context']==context,'execution-unconsumed-result-conflict')
            return o.doc(unconsumed[0]['result'])
        call={'step':name,'company_index':self.s['index'],'context':copy.deepcopy(context),'state':'unknown','intent_at':self.clock.wall().isoformat()};self.s['calls'].append(call);self.save()
        try:
            value=self.ports.step(name,context)
            result=o.immutable(self.folder/'receipts'/(str(len(self.s['calls'])).zfill(5)+'.json'),value)
            call.update(state='returned',result=result,returned_at=self.clock.wall().isoformat());self.save();return o.doc(result)
        except Exception as error:
            # Child input may already have happened. Never repeat it from the
            # outer parent, even if a child error looks pre-input.
            call.update(state='failed',error=str(error));self.s.update(status='hold',error=str(error));self.save();raise
    def commit(self):
        for call in self.s['calls'][-1:]:
            if call['state']=='returned':call['applied']=True
        self.save()
    def accept(self,reference):
        self.load();o.need(self.s.get('handoff') and self.s['status']=='waiting','execution-no-handoff');response=o.doc(reference);request=o.doc(self.s['handoff'])
        o.need(response.get('request')==self.s['handoff'] and response.get('kind')==request['response_kind'],'execution-handoff-response-binding')
        previous=self.s.get('acceptance')
        if previous:
            o.need(previous['request']==self.s['handoff'] and previous['response']==reference,'execution-original-handoff-acceptance-required')
            result_path=self.folder/'acceptances'/(self.s['handoff']['sha256']+'-result.json')
            if not result_path.exists():
                self.s.update(status='hold',error='execution-handoff-outcome-unknown-no-reapply');self.save();return view(self.s)
            result=o.doc(o.ref(result_path));o.need(result['request']==previous['request'] and result['response']==reference,'execution-handoff-result-conflict');updates=result['updates']
            guarded=copy.deepcopy(self.s);guarded['companies'][self.s['index']]['artifacts'].update(updates);self.ports.guard(self.order,guarded);self.ports.verify_accept(request,response,updates)
        else:
            self.ports.guard(self.order,self.s)
            self.s['acceptance']={'request':self.s['handoff'],'response':reference,'state':'unknown','intent_at':self.clock.wall().isoformat()};self.save()
            # Only this first attempt can invoke the existing child API.
            updates=self.ports.accept(request,response)
            o.immutable(self.folder/'acceptances'/(self.s['handoff']['sha256']+'-result.json'),{'request':self.s['handoff'],'response':reference,'updates':updates or {}})
        # Ports performs the existing copy/attestation validation and actual
        # registration. Neither a report boolean nor an arbitrary argv is run.
        self.s['companies'][self.s['index']]['artifacts'].update(updates or {})
        self.s['companies'][self.s['index']]['artifacts'].setdefault('responses',[]).append(reference)
        self.s.setdefault('accepted',[]).append(self.s.pop('acceptance'));self.s['accepted'][-1]['state']='complete';self.s.pop('handoff');self.s.pop('waiting_for',None);self.s['status']='running';self.save();return view(self.s)
    def step(self):
        self.load(create=True)
        resume_engine_hold(self)
        # Held/waiting journals are diagnostic reads, not an attempt to execute
        # a guard that is expected to reject their unknown/failed child.
        if self.s['status'] in ('complete','hold','waiting','collection-ready'):return view(self.s)
        guarded=copy.deepcopy(self.s)
        unconsumed=[c for c in self.s['calls'][-1:] if c['state']=='returned' and not c.get('applied')]
        if unconsumed:
            o.need(len(unconsumed)==1 and unconsumed[0]['step']==self.s['phase'] and unconsumed[0]['company_index']==self.s['index'],'execution-unconsumed-step-conflict')
            # The saved immutable return may already have changed this original
            # ledger before the phase commit. Only replay that same return; no
            # child invocation is allowed. Unknowns have no such privilege.
            value=o.doc(unconsumed[0]['result'])
            if self.s['phase'] not in ('seal','finish'):guarded['companies'][self.s['index']]['artifacts'].update(value.get('artifacts',{}))
        try:self.ports.guard(self.order,guarded)
        except Exception as error:
            self.s.update(status='hold',error=str(error));self.save();return view(self.s)
        if self.s.get('reboot_continuation'):
            import violation_reboot_continuation as reboot
            o.need(reboot.allowed_calls(self.s,self.s['reboot_continuation']),'execution-reboot-unresolved-calls')
        else:o.need(not any(c['state'] in ('unknown','failed') for c in self.s['calls'][-1:]),'execution-unknown-no-replay')
        index=self.s['index']
        if self.s['phase']=='collection-seal':
            result=self.action('collection-seal',{'order':self.order,'companies':self.s['companies'],'folder':str(self.folder)})
            self.s.update(status='collection-ready',collection_ready=result['ready']);self.commit();return view(self.s)
        if self.s['phase']=='seal':
            result=self.action('seal',{'order':self.order,'companies':self.s['companies'],'folder':str(self.folder)})
            self.s['delivery']=result
            for row in self.s['companies']:row['artifacts']['delivery_manifest']=result['manifest']
            self.s.update(phase='send',index=0);self.commit();return view(self.s)
        if self.s['phase']=='finish':
            result=self.action('finish',{'order':self.order,'companies':self.s['companies'],'delivery':self.s['delivery'],'folder':str(self.folder)})
            self.s.update(status='complete',completion=result);self.commit();return view(self.s)
        company=self.order['companies'][index];c=self.s['companies'][index];phase=self.s['phase']
        context={'order':self.order,'company':company,'artifacts':copy.deepcopy(c['artifacts']),'folder':str(self.folder/'companies'/str(index)),'phase':phase}
        if company['skipped']:
            self.ports.skipped(company);result={'done':True,'skipped':True}
        else:result=self.action(phase,context)
        if result.get('journal'):
            path=result['journal']['path'];self.s['business_journals']=[x for x in self.s['business_journals'] if x!=path]+[path]
        c['artifacts'].update(result.get('artifacts',{}))
        if result.get('handoff'):
            h={'kind':'violation-execution-handoff-v1','order':self.ref,'company':company,'phase':phase,**result['handoff']};self.s['handoff']=o.immutable(self.folder/'handoffs'/(str(len(self.s['calls']))+'.json'),h);self.s.update(status='waiting',waiting_for=h['response_kind']);self.commit();return view(self.s)
        if not result.get('done'):
            if result.get('hold'):self.s.update(status='hold',error=result['hold'])
            self.commit();return view(self.s)
        if phase=='send':
            c['sent']=True
            if index+1<len(self.order['companies']):self.s['index']+=1
            else:self.s.update(phase='complete-company',index=0)
        elif phase=='complete-company':
            c['completed']=result
            if index+1<len(self.order['companies']):self.s['index']+=1
            else:self.s.update(phase='finish',index=0)
        elif phase=='company-delivery':
            c['company_delivery']=result['company_delivery']
            if index+1<len(self.order['companies']):self.s.update(index=index+1,phase='plan')
            else:self.s.update(index=0,phase='collection-seal')
        elif phase=='ready' and self.order.get('collection_contract')=='three-flow-collection-ready-v1' and not company['skipped']:
            c['phase']='ready';self.s['phase']='company-delivery'
        elif company['skipped'] or phase=='ready':
            c['phase']='ready'
            if index+1<len(self.order['companies']):self.s.update(index=index+1,phase='plan')
            else:self.s.update(index=0,phase='collection-seal'if self.order.get('collection_contract')=='three-flow-collection-ready-v1'else'seal')
        else:
            # Zero source goes directly to ready, but still passes ingest.
            next_phase='ready' if phase=='ingest' and c['artifacts'].get('total')==0 else PHASES[PHASES.index(phase)+1]
            self.s['phase']=c['phase']=next_phase
        self.commit();return view(self.s)

def main():
    import argparse
    import execution_timing as timing
    from violation_execution_ports import ProductionPorts
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=('run','accept','status'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--tab-id',required=True,type=int);p.add_argument('--pid',required=True,type=int);p.add_argument('--steps',type=int,default=100);p.add_argument('--response');p.add_argument('--response-sha256');a=p.parse_args();o.need(type(a.steps) is int and 1<=a.steps<=1000,'execution-step-budget');reference={'path':a.order,'sha256':a.order_sha256};e=Engine(reference,ports=ProductionPorts(a.tab_id,a.pid),clock=timing.Clock())
    if a.verb=='status':
        value=view(e.load());value['business_journal_candidates']=e.ports.journals(e.order,e.s);print(json.dumps({'kind':'violation-execution-child-result-v1','order':reference,'engine':o.ref(e.file),**value},ensure_ascii=False));return
    parent=o.doc(o.ref(e.folder/'launcher.json'));expected=[sys.executable,str(Path(__file__).resolve()),*sys.argv[1:]]
    effective={'tab_id':parent['tab_id'],'pid':parent['pid']}
    if parent.get('reboot_continuation'):
        import violation_reboot_continuation as reboot
        effective=reboot.scope(parent,live_boot=timing.Clock().boot());e.ports.reboot_continuation=parent['reboot_continuation']
    o.need(parent.get('order')==reference and parent.get('status') in ('running','waiting') and effective['tab_id']==a.tab_id and effective['pid']==a.pid and parent.get('calls') and parent['calls'][-1].get('state')=='unknown' and parent['calls'][-1].get('argv')==expected,'execution-controlled-parent-intent-required')
    launch=o.doc(parent['calls'][-1]['launch']);o.need(launch['argv']==expected and launch['order']==reference,'execution-controlled-parent-launch-required')
    import role_execution_launcher as launch_api
    for r in launch_api.effective_code_refs(parent):o.raw(r)
    e.folder.mkdir(parents=True,exist_ok=True)
    with (e.folder/'engine.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.verb=='accept':o.need(a.response and a.response_sha256,'execution-explicit-handoff-response-required');value=e.accept({'path':a.response,'sha256':a.response_sha256})
        elif a.verb=='status':value=view(e.load())
        else:
            for _ in range(a.steps):
                value=e.step()
                if value['status']!='running':break
        print(json.dumps({'kind':'violation-execution-child-result-v1','order':reference,'engine':o.ref(e.file),**value},ensure_ascii=False))

_policy_original_main=main
def main(*args,**kwargs):
    import execution_timing as timing
    from violation_execution_ports import identity_history_command
    with identity_history_command(),timing.company_policy_command():return _policy_original_main(*args,**kwargs)

if __name__=='__main__':
    try:main()
    except Exception as e:
        __import__('traceback').print_exc(file=sys.stderr)
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
