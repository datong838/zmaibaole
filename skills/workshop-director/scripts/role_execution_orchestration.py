"""Candidate violation order/launch and current-dispatch pure final adapter.
No director initialization, scheduling, webpage or sender invocation here.
"""
import argparse,json,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import role_execution_order as o
import role_execution_launcher as launch
import director as d
import execution_timing as timing
def commands(reference,mode='acceptance'):
    common=['--order',reference['path'],'--order-sha256',reference['sha256'],'--mode',mode]
    return {verb:[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(Path(__file__).with_name('role_execution_launcher.py')),verb,*common] for verb in ('start','run','accept','status')}
def bind(root,state,offer):
    o.need(state['phase']=='dispatch-intent' and state['dispatch_id']==offer['dispatch_id'] and offer['workflow']==o.FLOW,'execution-new-role-intent-required')
    daily=[]
    for event in state.get('events',[]):
        if event.get('type')==('collection-ready' if offer.get('collection_contract')=='three-flow-collection-ready-v1' else 'completed'):
            report=o.doc(event['report'])
            if report.get('workflow')=='daily-comment-stats' and report.get('day')==state['day']:daily.append(event['report'])
    o.need(daily,'execution-current-daily-finish-required');offer_ref=o.immutable(Path(root)/'dispatch-offers'/( __import__('hashlib').sha256(offer['dispatch_id'].encode()).hexdigest()+'.json'),offer);reference=o.archive(root,offer_ref,daily[-1]);order=o.validate(reference);state['events'].append({'type':'role-execution-bound','dispatch_id':order['dispatch_id'],'order':reference,'at':d.stamp()})
    return {**offer,'role_execution':{'order':reference,'commands':commands(reference),'start_requires_explicit_tab_id_and_pid':True,'handoffs':'Only exact parent handoff refs. AI copy and real PNG supervision are required when requested. Waiting remains timed.','business_progress_journal':'Use returned original child/sender canonical journal, not outer state.','implementation':'candidate-violation-only; not live accepted'},'message':offer['message']+' 违规候选唯一父入口role_execution_launcher：start显式tab/pid→run至copy/真实PNG审核handoff→accept精确response→run至完整client确认与原complete；禁止模型另拼子工单。unknown只原单核验，禁止新key。'}
def performance_fields(s,proof):
    if s.get('reboot_continuation'):
        value=launch.performance(s);value['outcome']=proof['outcome'];return value
    return {'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':proof['outcome'],'functional_completion_is_not_30s_pass':True}

def replay_reboot(parent_ref,s):
    """Historical mixed-boot replay; no live clock, launcher, input or sender."""
    a=launch.reboot_admission(s);order=o.validate(s['order']);folder=o.location(s['order']);original=o.doc(a['original']['parent'])
    o.need(Path(parent_ref['path'])==folder/'launcher.json' and s['kind']=='role-execution-launcher-v1' and s['status']=='complete' and s['scope_sha256']==order['scope_sha256'],'execution-reboot-final-parent-binding')
    o.need(s['clock_contract']==timing.MONOTONIC_CLOCK and s['acceptance_pass'] is False and s.get('clock_comparable') is False and s.get('end_monotonic') is None and s.get('elapsed_seconds') is None,'execution-reboot-final-noncomparable')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items()),'execution-reboot-final-origin-changed')
    for r in a['current_code_refs']:o.raw(r)
    prefix=len(original['calls']);o.need(len(s['calls'])>prefix,'execution-reboot-final-new-child-required')
    end=s['reboot_segment_end'];o.need(end['boot']==a['segment']['boot'] and end['wall_ended_at']==s['wall_ended_at'] and timing.finite(end['end_monotonic']) and timing.finite(a['segment']['start_monotonic']) and 0<=a['segment']['start_monotonic']<=end['end_monotonic'],'execution-reboot-final-segment-end')
    previous_old=original['start_monotonic'];previous_new=a['segment']['start_monotonic']
    for i,call in enumerate(s['calls']):
        o.need(call['state']=='returned' and Path(call['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json'),'execution-reboot-final-child-path')
        before=o.doc(call['launch']);after=o.doc(call['result']);o.need(before['order']==s['order'] and before['index']==i and before['argv']==after['argv']==call['argv'] and after['launch']==call['launch'],'execution-reboot-final-child-binding')
        old=i<prefix;bound=original if old else s
        if old:o.need(call==original['calls'][i] and type(after.get('returncode')) is int and after['returncode'] in (0,2),'execution-reboot-historical-child-changed')
        else:
            o.need(type(after.get('returncode')) is int and (after['returncode']==0 or after['returncode']==2 and __import__('violation_reboot_continuation').historical_child_call(a,i,call)) and all(x.get('reboot_continuation')==s['reboot_continuation'] and x.get('boot_identity')==a['segment']['boot'] for x in (before,after)),'execution-reboot-new-child-segment-binding')
        argv=call['argv'];o.need(len(argv)>=3 and argv[2] in ('run','accept') and len(argv[3:])%2==0,'execution-reboot-child-argv-shape');args=dict(zip(argv[3::2],argv[4::2]));response={'path':args['--response'],'sha256':args['--response-sha256']} if argv[2]=='accept' else None
        o.need(argv==launch.command(s['order'],argv[2],bound,int(args.get('--steps',100)),response),'execution-reboot-child-argv-not-derived')
        start=before['launched_monotonic'];stop=after['exited_monotonic'];previous=previous_old if old else previous_new
        o.need(timing.finite(start) and timing.finite(stop) and previous<=start<=stop and (old or stop<=end['end_monotonic']),'execution-reboot-child-time-order')
        if old:previous_old=stop
        else:previous_new=stop
    last=json.loads(after['stdout']);o.need(last.get('order')==s['order'] and last.get('status')=='complete','execution-reboot-final-child-not-complete');inner=o.doc(last['engine'])
    sys.path.insert(0,str(launch.FORMAL.parent));import violation_reboot_continuation as reboot
    o.need(Path(last['engine']['path'])==folder/'engine.json' and inner['status']=='complete' and inner['order']==s['order'] and reboot.allowed_calls(inner,s['reboot_continuation']),'execution-reboot-final-inner-unresolved');reboot.exception(s,inner,s['reboot_continuation'])
    for i,c in enumerate(inner['calls']):
        if reboot.historical_failed_call(a,i,c):continue
        o.need(c['state']=='returned' and c.get('applied') is True,'execution-reboot-final-call-unapplied');o.doc(c['result'])
    final=o.doc(s['completion']);o.need(final['kind']=='violation-reboot-outer-completion-v1' and final['engine']==last['engine'] and final['order']==s['order'] and final['start_monotonic']==s['start_monotonic'] and final['end_monotonic'] is None and final['completed_at']==s['wall_ended_at'] and final['segment_end']==end and final['reboot_continuation']==s['reboot_continuation'] and final['clock_comparable'] is False and final['acceptance_pass'] is False,'execution-reboot-final-proof-binding')
    from violation_execution_ports import ProductionPorts
    scope=a['effective_scope'];ports=ProductionPorts(scope['tab_id'],scope['pid']);ports.reboot_continuation=s['reboot_continuation'];proof=ports.finish({'order':order,'companies':inner['companies'],'delivery':inner['delivery'],'folder':str(folder)});o.need(proof==final['proof']==inner['completion'] and final['outcome']==proof['outcome'],'execution-reboot-final-source-client-changed')
    return s,order,proof

def replay(parent_ref):
    s=o.doc(parent_ref)
    if s.get('reboot_continuation'):return replay_reboot(parent_ref,s)
    order=o.validate(s['order']);folder=o.location(s['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and s['kind']=='role-execution-launcher-v1' and s['status']=='complete','execution-final-canonical-parent-required');o.need(s['clock_contract']==timing.MONOTONIC_CLOCK and s['boot_identity']==timing.Clock().boot(),'execution-final-clock-contract');o.need(s['scope_sha256']==order['scope_sha256'],'execution-final-scope-conflict')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items()),'execution-final-origin-changed')
    admission=None
    if s.get('violation_confirmed_navigation_wait_recovery'):
        sys.path.insert(0,str(launch.FORMAL.parent));from violation_initial_ledger_recovery import verify_recovered
        admission=verify_recovered(s,s['violation_confirmed_navigation_wait_recovery'])
    elif (s.get('violation_anchor_date_fragment_recovery') or s.get('violation_analysis_fresh_wait_recovery') or s.get('violation_records_entry_recovery') or s.get('violation_center_readonly_recovery') or s.get('violation_company_preinput_recovery') or s.get('violation_initial_ledger_entry_recovery') or s.get('violation_initial_ledger_recovery')):
        sys.path.insert(0,str(launch.FORMAL.parent));from violation_initial_ledger_recovery import verify_recovered
        admission=verify_recovered(s,s.get('violation_anchor_date_fragment_recovery') or s.get('violation_analysis_fresh_wait_recovery') or s.get('violation_records_entry_recovery') or s.get('violation_center_readonly_recovery') or s.get('violation_company_preinput_recovery') or s.get('violation_initial_ledger_entry_recovery') or s['violation_initial_ledger_recovery'])
    for r in admission['code_refs'] if admission else s['code_refs']:o.raw(r)
    previous=s['start_monotonic'];o.need(s['calls'],'execution-final-no-children')
    for i,call in enumerate(s['calls']):
        o.need(call['state']=='returned' and Path(call['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json'),'execution-final-child-path-state');a=o.doc(call['launch']);b=o.doc(call['result']);o.need(a['order']==s['order'] and a['index']==i and a['argv']==b['argv']==call['argv'] and b['launch']==call['launch'] ,'execution-final-child-binding')
        failed=admission.get('initial_failed_calls',[admission.get('initial_failed_call')]) if admission else []
        additional=admission.get('additional_failed_calls',[]) if admission else []
        expected_rc=2 if i<len(failed) and call==failed[i] or any(x['index']==i and x['call']==call for x in additional) else 0
        o.need(type(b.get('returncode')) is int and b['returncode']==expected_rc,'execution-final-child-returncode')
        argv=call['argv'];o.need(len(argv)>=3 and argv[2] in ('run','accept'),'execution-final-child-verb');args=dict(zip(argv[3::2],argv[4::2]));response={'path':args['--response'],'sha256':args['--response-sha256']} if argv[2]=='accept' else None
        expected=launch.command(s['order'],argv[2],s,int(args.get('--steps',100)),response);o.need(argv==expected,'execution-final-child-argv-not-derived');o.need(previous<=a['launched_monotonic']<=b['exited_monotonic'],'execution-final-child-time-order');previous=b['exited_monotonic']
    o.need(b['returncode']==0,'execution-final-last-child-returncode')
    last=json.loads(b['stdout']);o.need(last.get('order')==s['order'] and last.get('status')=='complete','execution-final-child-not-complete');inner=o.doc(last['engine']);o.need(Path(last['engine']['path'])==folder/'engine.json' and inner['status']=='complete' and inner['order']==s['order'] and all(c['state']=='returned' and c.get('applied') for c in inner['calls']),'execution-final-inner-unresolved')
    for c in inner['calls']:o.doc(c['result'])
    final=o.doc(s['completion']);o.need(final['engine']==last['engine'] and final['order']==s['order'] and final['start_monotonic']==s['start_monotonic'] and final['end_monotonic']==s['end_monotonic']>=previous and final['completed_at']==s['wall_ended_at'],'execution-final-clock-proof')
    sys.path.insert(0,str(launch.FORMAL.parent));from violation_execution_ports import ProductionPorts
    proof=ProductionPorts(s['tab_id'],s['pid']).finish({'order':order,'companies':inner['companies'],'delivery':inner['delivery'],'folder':str(folder)});o.need(proof==final['proof']==inner['completion'],'execution-final-source-client-changed')
    # Acceptance is derived; a saved passed boolean cannot upgrade a slow run.
    passed=s['mode']=='acceptance' and s['origin']=='fresh' and s['end_monotonic']-s['start_monotonic']<=30;o.need(s['acceptance_pass']==passed,'execution-final-performance-not-derived')
    return s,order,proof
def report(parent_ref,current_ref,out):
    s,order,proof=replay(parent_ref);current=o.doc(current_ref);o.need(Path(current_ref['path'])==Path(s['order']['path']).parent.parent/'state.json','execution-current-director-path');check_current(current,order,s)
    refs=[parent_ref,s['order'],s['origin_ref'],s['completion'],current_ref,*proof['evidence'],*proof['clients']]
    if not s.get('reboot_continuation') and s.get('violation_confirmed_navigation_wait_recovery'):
        from violation_initial_ledger_recovery import verify_recovered
        refs.extend(verify_recovered(s,s['violation_confirmed_navigation_wait_recovery'])['evidence'])
    elif not s.get('reboot_continuation') and (s.get('violation_anchor_date_fragment_recovery') or s.get('violation_analysis_fresh_wait_recovery') or s.get('violation_records_entry_recovery') or s.get('violation_center_readonly_recovery') or s.get('violation_company_preinput_recovery') or s.get('violation_initial_ledger_entry_recovery') or s.get('violation_initial_ledger_recovery')):
        from violation_initial_ledger_recovery import verify_recovered
        refs.extend(verify_recovered(s,s.get('violation_anchor_date_fragment_recovery') or s.get('violation_analysis_fresh_wait_recovery') or s.get('violation_records_entry_recovery') or s.get('violation_center_readonly_recovery') or s.get('violation_company_preinput_recovery') or s.get('violation_initial_ledger_entry_recovery') or s['violation_initial_ledger_recovery'])['evidence'])
    if s.get('reboot_continuation'):refs.extend([s['reboot_continuation'],launch.reboot_admission(s)['original']['parent'],launch.reboot_admission(s)['original']['engine']])
    evidence=[]
    for r in refs:
        b=o.raw(r);path=Path(out).parent/'evidence'/(r['sha256']+Path(r['path']).suffix);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():o.need(path.read_bytes()==b,'execution-final-snapshot-conflict')
        else:
            with path.open('xb') as f:f.write(b);f.flush();__import__('os').fsync(f.fileno())
        evidence.append(o.ref(path))
    return o.immutable(out,{'kind':'violation-parent-director-completion-v1','workflow':o.FLOW,'role':o.ROLE,'dispatch_id':order['dispatch_id'],'day':order['day'],'completed_at':s['wall_ended_at'],'live':True,'complete':True,'fixture':False,'test_target':'测试群请忽略','production_sent':False,'complaint_submitted':False,'verification_parent':parent_ref,'source_client_proof':proof,'evidence':evidence,'performance':performance_fields(s,proof)})
def check_current(current,order,s):
    o.need(current['day']==order['day'] and current['dispatch_id']==order['dispatch_id'] and current['phase'] in ('running','attention') and d.current(current)['role']==o.ROLE,'execution-final-current-dispatch');o.need(any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in current['events']),'execution-final-ack-required');start=timing.parse_time(current['dispatch_intent_at']);o.need(start<=timing.parse_time(s['wall_started_at'])<=timing.parse_time(s['wall_ended_at'])<=datetime.now(timezone.utc),'execution-final-current-time');o.need(not any(e.get('type')=='completed' and e.get('dispatch_id')==order['dispatch_id'] for e in current['events']),'execution-final-already-consumed')
def verify_completion(path,current):
    r=o.doc(o.ref(path));o.need(r.get('kind')=='violation-parent-director-completion-v1','execution-current-role-parent-required');s,order,proof=replay(r['verification_parent']);check_current(current,order,s);o.need((r['dispatch_id'],r['day'],r['role'],r['completed_at'],r['source_client_proof'])==(order['dispatch_id'],order['day'],o.ROLE,s['wall_ended_at'],proof),'execution-final-report-scope-changed')
    expected=performance_fields(s,proof);o.need(r['performance']==expected,'execution-final-report-performance-changed')
    for ref in r['evidence']:o.raw(ref)
    return r
def collection_ready_report(parent_ref,current_ref,out):
    import collection_ready
    return collection_ready.report(parent_ref,current_ref,out,'violation-notifier')
def verify_collection_ready_report(path,current):
    import collection_ready
    value=collection_ready.verify_current(o.ref(path),current)
    o.need(value['workflow']=='violation-notifier','ready-flow-mismatch')
    return value

def main():
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True);p.add_argument('--parent-sha256',required=True);p.add_argument('--director',required=True);p.add_argument('--director-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--collection-ready',action='store_true');a=p.parse_args();print(json.dumps({'report':(collection_ready_report if a.collection_ready else report)({'path':a.parent,'sha256':a.parent_sha256},{'path':a.director,'sha256':a.director_sha256},a.out),'ui_used':False}))
if __name__=='__main__':main()
