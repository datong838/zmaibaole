"""Durable fixed complaint phase graph. No arbitrary commands or transport ports.
ProductionPorts calls the existing role APIs. AI/QA are hash-bound inputs, never
fake completions. Candidate; no UI has been used to validate this parent.
"""
import copy,fcntl,hashlib,json,os,sys
from pathlib import Path
if __name__=='__main__':sys.modules['complaint_execution']=sys.modules[__name__]
ROOT=(Path(__file__).resolve().parents[3]/'skills/daily-comment-stats').resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'workshop-director/scripts'))
import complaint_execution_order as o
PHASES=('plan','collect','ready')
def atomic(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def view(s):
    last=s['calls'][-1] if s['calls'] else None
    return {**({'collection_ready':s['collection_ready'],'delivery_complete':False}if s.get('collection_ready')else{}),'status':s['status'],'phase':s['phase'],'company_index':s['index'],'waiting_for':s.get('waiting_for'),'handoff':s.get('handoff'),'business_journals':s.get('business_journals',[]),'parent_is_not_business_progress':True,'error':s.get('error'),'last_action':{k:last[k] for k in ('step','state','intent_at','result','error') if k in last} if last else None,'recovery_policy':'Original parent status and named child journal only; no restart/new key/automatic reissue for unknown input.'}
SCOPE_FIELD='company_scope_reconciliation'
def scope_admission(state):
    if not state.get(SCOPE_FIELD):return None
    from initial_ledger_recovery import company_scope_admission
    result=company_scope_admission(state)
    o.need(type(result)is dict and result.get('proof')==state[SCOPE_FIELD],'execution-company-scope-admission')
    active=result['active_indices'];retired=result['retired_indices'];n=len(state['companies'])if 'companies'in state else len(o.validate(state['order'])['companies'])
    o.need(type(active)is list and type(retired)is list and active and all(type(i)is int for i in active+retired) and active==sorted(set(active)) and retired==sorted(set(retired)) and set(active).isdisjoint(retired) and sorted(active+retired)==list(range(n)),'execution-company-scope-partition')
    return result

def active_indices(state):
    admission=scope_admission(state)
    return admission['active_indices'] if admission else list(range(len(state['companies'])))

def scoped_context(state,context):
    return {**context,SCOPE_FIELD:state[SCOPE_FIELD]} if state.get(SCOPE_FIELD) else context

def scope_for_context(context):
    folder=Path(context['folder']);folder=folder if 'companies'in context else folder.parent.parent
    path=folder/'engine.json'
    if not context.get(SCOPE_FIELD)and not path.exists():return None
    state=o.doc(o.ref(path))
    if not state.get(SCOPE_FIELD):
        o.need(not context.get(SCOPE_FIELD),'execution-company-scope-context-conflict');return None
    o.need(folder==o.location(state['order']) and o.validate(state['order'])==context['order'] and state.get(SCOPE_FIELD)==context.get(SCOPE_FIELD),'execution-company-scope-context-binding')
    admission=scope_admission(state)
    if 'companies'in context:o.need(context['companies']==state['companies'],'execution-company-scope-companies')
    else:
        matches=[i for i,c in enumerate(context['order']['companies'])if c==context['company']]
        o.need(len(matches)==1 and matches[0]in admission['active_indices'] and context['artifacts']==state['companies'][matches[0]]['artifacts'] and folder/'companies'/str(matches[0])==Path(context['folder']),'execution-retired-company-no-new-operation')
    return admission

def guarded_calls(state):
    # A transition cannot advance past its unresolved current operation.
    # Earlier transactions are archival, not a runtime decision input.
    return state.get('calls',[])[-1:]

ENGINE_HOLD_RESUME_KIND='complaint-engine-hold-readonly-resume-v1'
READONLY_RESUMABLE_STEPS=('plan','collect','collection-seal')
def resume_engine_hold(engine):
    # B66: a failed collect leaves engine.json at hold with one 'failed' call, and
    # step() returns at the terminal-state guard before any tick, so a repaired
    # launcher starts a child that does nothing at all (attempt-9: rc=0, one view()
    # over the previous state). Resuming is allowed only for a read-only step, only
    # for the single failed tail call, only against these exact engine bytes, and
    # only once - adopting the proof rewrites engine.json. The failed call is
    # retired as superseded rather than dropped: its index, step and error stay in
    # the journal as evidence.
    proof_path=engine.file.parent/'resume-engine-hold.json'
    if not proof_path.exists()or engine.s.get('status')!='hold':return False
    proof=o.doc(o.ref(proof_path));o.need(proof.get('kind')==ENGINE_HOLD_RESUME_KIND,'engine-hold-resume-kind')
    o.need(proof.get('engine')==o.ref(engine.file),'engine-hold-resume-engine-bytes')
    o.need(engine.s.get('error')==proof.get('original_error'),'engine-hold-resume-error')
    applied_guard_hold=proof.get('exact_apply') and engine.s.get('error')=='complaint-parent-external-ledger-change' and engine.s['calls'][-1].get('state')=='superseded'
    o.need(bool(engine.s['calls'])and (engine.s['calls'][-1].get('state')=='failed' or applied_guard_hold),'engine-hold-resume-current-failed-tail')
    index=len(engine.s['calls'])-1;call=engine.s['calls'][-1]
    o.need(call.get('step')in READONLY_RESUMABLE_STEPS,'engine-hold-resume-readonly-step')
    o.need(proof.get('failed_call')=={'index':index,'step':call['step'],'error':call.get('error')},'engine-hold-resume-failed-call-binding')
    if proof.get('exact_apply'):
        import complaint_exact_recheck as exact
        o.need(call['step']=='collect','engine-hold-current-apply-step')
        a=engine.s['companies'][engine.s['index']]['artifacts'];x=a['unit_artifacts'];audit=exact.verify_apply(proof['exact_apply']);manifest=o.doc(audit['manifest'])
        o.need(a['unit_phase']=='recheck' and x.get('exact_manifest')==audit['manifest'] and a['ledger_current']['sha256']==manifest['original_ledger']['sha256'],'engine-hold-current-apply-owner')
        current=o.ref(Path(manifest['root'])/'state.json')
        o.need(current['sha256']==audit['recorded_state']['sha256'] and x['recheck_keys'][x['review_index']]==manifest['review_key'],'engine-hold-current-apply-state')
        a['ledger_current']=current;x['operations'].append(proof['exact_apply']);x['review_index']+=1;x.pop('exact_manifest')
    marker={'proof':o.ref(proof_path),'at':proof.get('at'),'reason':proof.get('reason')}
    if applied_guard_hold:call['hold_released_by']=marker
    else:call['state']='superseded';call['superseded_by']=marker
    engine.s.update(status='running');engine.s.pop('error',None)
    engine.s.setdefault('engine_hold_resumes',[]).append({'proof':o.ref(proof_path),'at':proof.get('at'),'call_index':index,'step':call['step']})
    engine.save();return True
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
            self.s={'kind':'complaint-execution-v1','order':self.ref,'scope_sha256':self.order['scope_sha256'],'status':'running','phase':'plan','index':0,'companies':[{'artifacts':{},'phase':'plan'} for _ in self.order['companies']],'calls':[],'business_journals':[]}
            self.save()
        return self.s
    def action(self,name,context):
        o.need(not any(c['state'] in ('unknown','failed') for c in guarded_calls(self.s)),'execution-unknown-no-replay')
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
        for call in self.s['calls']:
            if call['state']=='returned':call['applied']=True
        self.save()
    def accept(self,reference):
        self.load();o.need(self.s['index']in active_indices(self.s),'execution-retired-company-accept');o.need(self.s.get('handoff') and self.s['status']=='waiting','execution-no-handoff');response=o.doc(reference);request=o.doc(self.s['handoff'])
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
        unconsumed=[c for c in self.s['calls'] if c['state']=='returned' and not c.get('applied')]
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
        o.need(not any(c['state'] in ('unknown','failed') for c in guarded_calls(self.s)),'execution-unknown-no-replay')
        indices=active_indices(self.s);index=self.s['index']
        o.need(index in indices,'execution-retired-company-index')
        following=next((i for i in indices if i>index),None)
        if self.s['phase']=='collection-seal':
            result=self.action('collection-seal',scoped_context(self.s,{'order':self.order,'companies':self.s['companies'],'folder':str(self.folder)}))
            self.s.update(status='collection-ready',collection_ready=result['ready']);self.commit();return view(self.s)
        if self.s['phase']=='seal':
            result=self.action('seal',scoped_context(self.s,{'order':self.order,'companies':self.s['companies'],'folder':str(self.folder)}))
            self.s['delivery']=result
            for i in indices:self.s['companies'][i]['artifacts']['delivery_manifest']=result['manifest']
            self.s.update(phase='send',index=indices[0]);self.commit();return view(self.s)
        if self.s['phase']=='finish':
            result=self.action('finish',scoped_context(self.s,{'order':self.order,'companies':self.s['companies'],'delivery':self.s['delivery'],'folder':str(self.folder)}))
            self.s.update(status='complete',completion=result);self.commit();return view(self.s)
        company=self.order['companies'][index];c=self.s['companies'][index];phase=self.s['phase']
        context={'order':self.order,'company':company,'artifacts':copy.deepcopy(c['artifacts']),'folder':str(self.folder/'companies'/str(index)),'phase':phase}
        context=scoped_context(self.s,context)
        if company['skipped']:
            self.ports.skipped(company);result={'done':True,'skipped':True}
        else:result=self.action(phase,context)
        if result.get('journal'):
            path=result['journal']['path'];self.s['business_journals']=[x for x in self.s['business_journals'] if x!=path]+[path]
        c['artifacts'].update(result.get('artifacts',{}))
        if result.get('handoff'):
            h={'kind':'complaint-execution-handoff-v1','order':self.ref,'company':company,'phase':phase,**result['handoff']};self.s['handoff']=o.immutable(self.folder/'handoffs'/(str(len(self.s['calls']))+'.json'),h);self.s.update(status='waiting',waiting_for=h['response_kind']);self.commit();return view(self.s)
        if not result.get('done'):
            if result.get('hold'):self.s.update(status='hold',error=result['hold'])
            self.commit();return view(self.s)
        if phase=='send':
            c['sent']=True
            if following is not None:self.s['index']=following
            else:self.s.update(phase='analyze',index=indices[0])
        elif phase=='analyze':
            c['analyzed']=True
            if following is not None:self.s['index']=following
            else:self.s.update(phase='collection-workbook'if self.order.get('collection_contract')=='three-flow-collection-ready-v1'else'complete-company',index=indices[0])
        elif phase=='collection-workbook':
            o.need(self.order.get('collection_contract')=='three-flow-collection-ready-v1','collection-workbook-fresh-contract')
            if following is not None:self.s['index']=following
            else:self.s.update(phase='collection-seal',index=indices[0])
        elif phase=='complete-company':
            c['completed']=result
            if following is not None:self.s['index']=following
            else:self.s.update(phase='finish',index=indices[0])
        elif company['skipped'] or phase=='ready':
            c['phase']='ready'
            if following is not None:self.s.update(index=following,phase='plan')
            else:self.s.update(index=indices[0],phase='analyze'if self.order.get('collection_contract')=='three-flow-collection-ready-v1'else'seal')
        else:
            # Zero source goes directly to ready, but still passes ingest.
            next_phase=PHASES[PHASES.index(phase)+1]
            self.s['phase']=c['phase']=next_phase
        self.commit();return view(self.s)

def main():
    import argparse
    import execution_timing as timing
    from complaint_execution_ports import ProductionPorts
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=('run','accept','status'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--tab-id',required=True,type=int);p.add_argument('--pid',required=True,type=int);p.add_argument('--steps',type=int,default=100);p.add_argument('--response');p.add_argument('--response-sha256');a=p.parse_args();o.need(type(a.steps) is int and 1<=a.steps<=1000,'execution-step-budget');reference={'path':a.order,'sha256':a.order_sha256};e=Engine(reference,ports=ProductionPorts(a.tab_id,a.pid),clock=timing.Clock())
    if a.verb=='status':
        value=view(e.load());value['business_journal_candidates']=e.ports.journals(e.order,e.s);print(json.dumps({'kind':'complaint-execution-child-result-v1','order':reference,'engine':o.ref(e.file),**value},ensure_ascii=False));return
    parent=o.doc(o.ref(e.folder/'launcher.json'));expected=[sys.executable,str(Path(__file__).resolve()),*sys.argv[1:]]
    o.need(parent.get('order')==reference and parent.get('status') in ('running','waiting') and parent.get('tab_id')==a.tab_id and parent.get('pid')==a.pid and parent.get('calls') and parent['calls'][-1].get('state')=='unknown' and parent['calls'][-1].get('argv')==expected,'execution-controlled-parent-intent-required')
    launch=o.doc(parent['calls'][-1]['launch']);o.need(launch['argv']==expected and launch['order']==reference,'execution-controlled-parent-launch-required')
    e.folder.mkdir(parents=True,exist_ok=True)
    with (e.folder/'engine.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.verb=='accept':o.need(a.response and a.response_sha256,'execution-explicit-handoff-response-required');value=e.accept({'path':a.response,'sha256':a.response_sha256})
        elif a.verb=='status':value=view(e.load())
        else:
            for _ in range(a.steps):
                value=e.step()
                if value['status']!='running':break
        print(json.dumps({'kind':'complaint-execution-child-result-v1','order':reference,'engine':o.ref(e.file),**value},ensure_ascii=False))

# One explicit scope per command; no interprocess or persistent cache.
_history_command_original_main = main
def main(*args, **kwargs):
    from initial_ledger_recovery import window_hold_history_scope
    with window_hold_history_scope(max_entries=16):
        return _history_command_original_main(*args, **kwargs)


_policy_original_main=main
def main(*args,**kwargs):
    import execution_timing as timing
    with timing.company_policy_command():return _policy_original_main(*args,**kwargs)

if __name__=='__main__':
    try:main()
    except Exception as e:
        __import__('traceback').print_exc(file=sys.stderr)
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
