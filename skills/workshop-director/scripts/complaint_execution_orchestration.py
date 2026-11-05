"""Candidate complaint order/launch and current-dispatch pure final adapter.
No director initialization, scheduling, webpage or sender invocation here.
"""
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import complaint_execution_order as o
import complaint_execution_launcher as launch
import director as d
import execution_timing as timing
def commands(reference,mode='acceptance'):
    common=['--order',reference['path'],'--order-sha256',reference['sha256'],'--mode',mode]
    return {verb:[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(Path(__file__).with_name('complaint_execution_launcher.py')),verb,*common] for verb in ('start','run','accept','status')}
def bind(root,state,offer):
    o.need(state['phase']=='dispatch-intent' and state['dispatch_id']==offer['dispatch_id'] and offer['workflow']==o.FLOW,'execution-new-role-intent-required')
    daily=[]
    for event in state.get('events',[]):
        if event.get('type')==('collection-ready' if offer.get('collection_contract')=='three-flow-collection-ready-v1' else 'completed'):
            report=o.doc(event['report'])
            if report.get('workflow')=='daily-comment-stats' and report.get('day')==state['day']:daily.append(event['report'])
    o.need(daily,'execution-current-daily-finish-required');offer_ref=o.immutable(Path(root)/'dispatch-offers'/( __import__('hashlib').sha256(offer['dispatch_id'].encode()).hexdigest()+'.json'),offer);reference=o.archive(root,offer_ref,daily[-1]);order=o.validate(reference);state['events'].append({'type':'role-execution-bound','dispatch_id':order['dispatch_id'],'order':reference,'at':d.stamp()})
    return {**offer,'role_execution':{'order':reference,'commands':commands(reference),'start_requires_explicit_tab_id_and_pid':True,'handoffs':'Only exact parent handoff refs. AI classification/draft and real PNG supervision are required when requested. Waiting remains timed.','business_progress_journal':'Use returned original child/sender canonical journal, not outer state.','implementation':'candidate-complaint-only; not live accepted'},'message':offer['message']+' 投诉候选唯一父入口complaint_execution_launcher：start显式tab/pid→run至copy/真实PNG审核handoff→accept精确response→run至完整client确认与原complete；禁止模型另拼子工单。unknown只原单核验，禁止新key。'}
def final_engine_calls(inner,parent):
    if inner.get('company_scope_reconciliation')or parent.get('company_scope_reconciliation'):
        o.need(inner.get('company_scope_reconciliation')==parent.get('company_scope_reconciliation'),'execution-final-company-scope-marker')
        from complaint_execution import guarded_calls
        return guarded_calls(inner)
    o.need(inner.get('initial_pure_plan_recovery')==parent.get('initial_pure_plan_recovery'),'execution-final-engine-recovery-binding')
    if inner.get('capture_window_effect_recovery') or parent.get('capture_window_effect_recovery'):
        o.need(inner.get('capture_window_effect_recovery')==parent.get('capture_window_effect_recovery'),'execution-final-window-effect-marker-binding')
        from initial_ledger_recovery import engine_calls
        return engine_calls(inner)
    if not inner.get('initial_pure_plan_recovery'):return inner['calls']
    from initial_ledger_recovery import engine_calls
    return engine_calls(inner)

def reviewed_failed_children(admission,parent_calls):
    """Verified compact history is an exact set, never a positional prefix."""
    if not admission:return []
    approved=admission.get('failed_calls')
    if approved is None:approved=[admission['initial_failed_call']] if admission.get('initial_failed_call') else []
    o.need(type(approved) is list,'execution-final-admitted-calls-invalid')
    refs=set()
    for saved in approved:
        o.need(type(saved) is dict and saved.get('state')=='returned' and sum(saved==c for c in parent_calls)==1,'execution-final-admitted-child-not-unique')
        for field in ('launch','result'):
            ref=saved.get(field);o.need(type(ref) is dict and set(ref)=={'path','sha256'},'execution-final-admitted-ref-invalid');key=(field,ref['path'],ref['sha256']);o.need(key not in refs,'execution-final-duplicate-admitted-ref');refs.add(key)
    if admission.get('initial_failed_call'):o.need(sum(admission['initial_failed_call']==c for c in approved)==1,'execution-final-initial-failure-not-admitted')
    return approved

def replay(parent_ref):
    s=o.doc(parent_ref);order=o.validate(s['order']);folder=o.location(s['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and s['kind']=='role-execution-launcher-v1' and s['status']=='complete','execution-final-canonical-parent-required');o.need(s['clock_contract']==timing.MONOTONIC_CLOCK and s['boot_identity']==timing.Clock().boot(),'execution-final-clock-contract');o.need(s['scope_sha256']==order['scope_sha256'],'execution-final-scope-conflict')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items()),'execution-final-origin-changed')
    admission=None
    if s.get('initial_ledger_origin_recovery')and not s.get('company_scope_reconciliation'):
        sys.path.insert(0,str(launch.FORMAL.parent));from initial_ledger_recovery import verify_recovered
        admission=verify_recovered(s,s['initial_ledger_origin_recovery'])
    if s.get('preengine_constructor_recovery')and not s.get('company_scope_reconciliation'):
        o.need(admission is None,'execution-no-mixed-preengine-recovery');sys.path.insert(0,str(launch.FORMAL.parent));from initial_ledger_recovery import verify_preengine_constructor
        admission=verify_preengine_constructor(s,s['preengine_constructor_recovery'])
    if s.get('company_scope_reconciliation'):
        from initial_ledger_recovery import company_scope_admission
        scope=company_scope_admission(s);admission={**(admission or {}),**scope}
    for r in admission['code_refs'] if admission and 'code_refs'in admission else launch.effective_code_refs(s):o.raw(r)
    previous=s['start_monotonic'];o.need(s['calls'],'execution-final-no-children');approved_failed=reviewed_failed_children(admission,s['calls'])
    for i,call in enumerate(s['calls']):
        o.need(call['state']=='returned' and Path(call['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json'),'execution-final-child-path-state');a=o.doc(call['launch']);b=o.doc(call['result']);o.need(a['order']==s['order'] and a['index']==i and a['argv']==b['argv']==call['argv'] and b['launch']==call['launch'],'execution-final-child-binding')
        initial_failed=any(call==saved for saved in approved_failed)
        o.need(type(b.get('returncode')) is int and b['returncode']==(2 if initial_failed else 0),'execution-final-child-returncode')
        argv=call['argv'];o.need(len(argv)>=3 and argv[2] in ('run','accept'),'execution-final-child-verb');args=dict(zip(argv[3::2],argv[4::2]));response={'path':args['--response'],'sha256':args['--response-sha256']} if argv[2]=='accept' else None
        expected=launch.command(s['order'],argv[2],s,int(args.get('--steps',100)),response);o.need(argv==expected,'execution-final-child-argv-not-derived');o.need(previous<=a['launched_monotonic']<=b['exited_monotonic'],'execution-final-child-time-order');previous=b['exited_monotonic']
    last=json.loads(b['stdout']);o.need(last.get('order')==s['order'] and last.get('status')=='complete','execution-final-child-not-complete');inner=o.doc(last['engine']);o.need(Path(last['engine']['path'])==folder/'engine.json' and inner['status']=='complete' and inner['order']==s['order'] and all(c['state']=='returned' and c.get('applied') for c in final_engine_calls(inner,s)),'execution-final-inner-unresolved')
    for c in final_engine_calls(inner,s):o.doc(c['result'])
    final=o.doc(s['completion']);o.need(final['engine']==last['engine'] and final['order']==s['order'] and final['start_monotonic']==s['start_monotonic'] and final['end_monotonic']==s['end_monotonic']>=previous and final['completed_at']==s['wall_ended_at'],'execution-final-clock-proof')
    sys.path.insert(0,str(launch.FORMAL.parent));from complaint_execution_ports import ProductionPorts
    from complaint_execution import scoped_context
    proof=ProductionPorts(s['tab_id'],s['pid']).finish(scoped_context(inner,{'order':order,'companies':inner['companies'],'delivery':inner['delivery'],'folder':str(folder)}));o.need(proof==final['proof']==inner['completion'],'execution-final-source-client-changed')
    # Acceptance is derived; a saved passed boolean cannot upgrade a slow run.
    passed=s['mode']=='acceptance' and s['origin']=='fresh' and s['end_monotonic']-s['start_monotonic']<=30;o.need(s['acceptance_pass']==passed,'execution-final-performance-not-derived')
    return s,order,proof
def report(parent_ref,current_ref,out):
    s,order,proof=replay(parent_ref);current=o.doc(current_ref);o.need(Path(current_ref['path'])==Path(s['order']['path']).parent.parent/'state.json','execution-current-director-path');check_current(current,order,s)
    refs=[parent_ref,s['order'],s['origin_ref'],s['completion'],current_ref,*proof['evidence'],*proof['clients']]
    if s.get('initial_ledger_origin_recovery')and not s.get('company_scope_reconciliation'):
        from initial_ledger_recovery import verify_recovered
        refs.extend(verify_recovered(s,s['initial_ledger_origin_recovery'])['evidence'])
    evidence=[]
    for r in refs:
        b=o.raw(r);path=Path(out).parent/'evidence'/(r['sha256']+Path(r['path']).suffix);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():o.need(path.read_bytes()==b,'execution-final-snapshot-conflict')
        else:
            with path.open('xb') as f:f.write(b);f.flush();__import__('os').fsync(f.fileno())
        evidence.append(o.ref(path))
    value={'kind':'complaint-parent-director-completion-v1','workflow':o.FLOW,'role':o.ROLE,'dispatch_id':order['dispatch_id'],'day':order['day'],'completed_at':s['wall_ended_at'],'live':True,'complete':True,'fixture':False,'test_target':'测试群请忽略','production_sent':False,'complaint_submitted':False,'verification_parent':parent_ref,'source_client_proof':proof,'evidence':evidence,'performance':{'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':proof['outcome'],'functional_completion_is_not_30s_pass':True}}
    if s.get('company_scope_reconciliation'):
        from initial_ledger_recovery import company_scope_admission
        admission=company_scope_admission(s)
        value.update(complete=False,active_scope_complete=True,original_scope_complete=False,retired_incomplete=True,company_scope_reconciliation=admission['proof'],active_company_policy=admission['policy'],active_companies=[{k:order['companies'][i][k]for k in ('company','groupid')}for i in admission['active_indices']],retired_companies=[{**{k:order['companies'][i][k]for k in ('company','groupid')},'disposition':'retired-incomplete-history-preserved'}for i in admission['retired_indices']])
    return o.immutable(out,value)
def check_current(current,order,s):
    o.need(current['day']==order['day'] and current['dispatch_id']==order['dispatch_id'] and current['phase'] in ('running','attention') and d.current(current)['role']==o.ROLE,'execution-final-current-dispatch');o.need(any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in current['events']),'execution-final-ack-required');start=timing.parse_time(current['dispatch_intent_at']);o.need(start<=timing.parse_time(s['wall_started_at'])<=timing.parse_time(s['wall_ended_at'])<=datetime.now(timezone.utc),'execution-final-current-time');o.need(not any(e.get('type')=='completed' and e.get('dispatch_id')==order['dispatch_id'] for e in current['events']),'execution-final-already-consumed')
def verify_completion(path,current):
    r=o.doc(o.ref(path));o.need(r.get('kind')=='complaint-parent-director-completion-v1','execution-current-role-parent-required');s,order,proof=replay(r['verification_parent']);check_current(current,order,s);o.need((r['dispatch_id'],r['day'],r['role'],r['completed_at'],r['source_client_proof'])==(order['dispatch_id'],order['day'],o.ROLE,s['wall_ended_at'],proof),'execution-final-report-scope-changed')
    if s.get('company_scope_reconciliation'):o.need(r.get('complete')is False and r.get('active_scope_complete')is True and r.get('original_scope_complete')is False and r.get('retired_incomplete')is True and r.get('company_scope_reconciliation')==s['company_scope_reconciliation'],'execution-final-scope-completion-flags')
    if s.get('company_scope_reconciliation'):
        from initial_ledger_recovery import company_scope_admission
        admission=company_scope_admission(s)
        o.need(r.get('active_company_policy')==admission['policy']and r.get('active_companies')==[{k:order['companies'][i][k]for k in ('company','groupid')}for i in admission['active_indices']]and r.get('retired_companies')==[{**{k:order['companies'][i][k]for k in ('company','groupid')},'disposition':'retired-incomplete-history-preserved'}for i in admission['retired_indices']],'execution-final-active-policy-binding')
    expected={'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':proof['outcome'],'functional_completion_is_not_30s_pass':True};o.need(r['performance']==expected,'execution-final-report-performance-changed')
    for ref in r['evidence']:o.raw(ref)
    return r
def collection_ready_report(parent_ref,current_ref,out):
    import collection_ready
    return collection_ready.report(parent_ref,current_ref,out,'negative-review-complaints')
def verify_collection_ready_report(path,current):
    import collection_ready
    value=collection_ready.verify_current(o.ref(path),current)
    o.need(value['workflow']=='negative-review-complaints','ready-flow-mismatch')
    return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--parent-sha256',required=True);p.add_argument('--director',required=True);p.add_argument('--director-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--collection-ready',action='store_true');a=p.parse_args();print(json.dumps({'report':(collection_ready_report if a.collection_ready else report)({'path':a.parent,'sha256':a.parent_sha256},{'path':a.director,'sha256':a.director_sha256},a.out),'ui_used':False}))
if __name__=='__main__':main()
