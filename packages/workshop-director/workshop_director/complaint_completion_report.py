"""Fixed completed-only complaint receipt replay. No run/accept/step/UI/finish.
Historical orchestration stays installed byte-for-byte; only admitted exit semantics
are corrected here. Root release pins the exact original completed request chain.
"""
import argparse,json,sys,hashlib
from pathlib import Path
from datetime import datetime,timezone
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
import complaint_execution_order as o
import complaint_execution_launcher as launch
import execution_timing as timing
import director as d
CONTRACT='reviewed-admitted-exits-completed-parent-v1'
RELEASE=PROJECT/'work/performance-audit/complaint-completion-report-candidate/supervisor-release.json'
LEGACY=PROJECT/'skills/workshop-director/scripts/complaint_execution_orchestration.py'
LEGACY_SHA='5c9e170e62d698a056cf3e5b58d927fc811183c1e68bb520c808c09edbc7bacd'
HELPER=PROJECT/'packages/workshop-director/workshop_director/complaint_completion_report.py'
TARGETS={str(HELPER),str(PROJECT/'packages/workshop-director/workshop_director/adapters.py'),str(PROJECT/'skills/workshop-director/scripts/coordinator.py')}

BEFORE={'/Users/feibing/work/projects/zmaibaole/packages/workshop-director/workshop_director/complaint_completion_report.py': None, '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/workshop_director/adapters.py': '9876deed679a2d6073bfccd312dc4c54bcef9230e542480481df2615a3178241', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/coordinator.py': 'f1e9b4cab1031f9e34abd2687e322c056a29ab732279c8fac77bdca84d5cd562'}

def release_binding(reference):
    o.need(Path(reference['path'])==RELEASE,'complaint-report-fixed-release-path');r=o.doc(reference)
    o.need(r.get('kind')=='supervisor-reviewed-source-release-v1' and type(r.get('targets')) is list and len(r['targets'])==3 and {x['target'] for x in r['targets']}==TARGETS,'complaint-report-reviewed-targets')
    for t in r['targets']:
        o.raw(t['after']);o.need(t.get('old_sha256')==BEFORE[t['target']] and t.get('mode')=='0644' and o.ref(Path(t['target']))['sha256']==t['after']['sha256'],'complaint-report-installed-source-changed')
    o.need(o.ref(LEGACY)['sha256']==LEGACY_SHA,'complaint-report-legacy-orchestration-changed')
    o.need(o.ref(HELPER)['sha256']==hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'complaint-report-helper-origin')
    return r

def original_inputs(release_ref,parent_ref):
    r=release_binding(release_ref);pins=r.get('completion_report_recovery');o.need(type(pins) is dict and set(pins)=={'request','parent','parent_exit','worker_exit'},'complaint-report-original-recovery-pins')
    o.need(pins['parent']==parent_ref,'complaint-report-original-parent-ref');s=o.doc(parent_ref);request=o.doc(pins['request']);pe=o.doc(pins['parent_exit']);we=o.doc(pins['worker_exit']);folder=Path(pins['request']['path']).parent
    o.need(folder==PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and Path(pins['request']['path'])==folder/'request.json' and Path(pins['parent_exit']['path'])==folder/'parent-run-exit.json' and Path(pins['worker_exit']['path'])==folder/'exit.json','complaint-report-original-attempt-path')
    o.need(request['kind']=='workshop-worker-request-v1' and request['task']['flow']==o.FLOW and request['context']['order']==s['order'] and s['status']=='complete' and s['kind']=='role-execution-launcher-v1','complaint-report-completed-original-only')
    config=request['config'];o.need(o.doc(request['config_ref'])==config and config['project']==str(PROJECT) and config['python']==str(PROJECT/'skills/daily-comment-stats/.venv/bin/python') and config['coordinator_root']==str(PROJECT/'runtime/workshop-director'),'complaint-report-original-config')
    order=o.validate(s['order']);o.need(request['task']['day']==order['day'] and order['workflow']==o.FLOW and datetime.fromisoformat(request['task']['outer']['started_at'])<=datetime.fromisoformat(s['wall_started_at']),'complaint-report-task-day-clock')
    expected=[config['python'],str(PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--mode',s['mode'],'--steps','1000']
    output=json.loads(o.raw(pe['stdout']));o.need(type(pe.get('returncode')) is int and pe['returncode']==0 and pe['argv']==expected and not o.raw(pe['stderr']) and output.get('status')=='complete' and output.get('order')==s['order'] and output.get('child')==s['child'] and output.get('completion')==s['completion'] and output.get('last_child_receipt')==s['calls'][-1]['result'],'complaint-report-original-natural-parent-exit')
    o.need(we['request']==pins['request'] and we['attempt_id']==request['attempt_id'] and we['returncode']==1 and we['response'] is None and 'execution-final-child-returncode' in o.raw(we['stderr']).decode() and datetime.fromisoformat(s['wall_ended_at'])<=datetime.fromisoformat(pe['exited_at'])<=datetime.fromisoformat(we['exited_at']),'complaint-report-known-report-failure')
    return pins,request

def final_engine_calls(inner,parent):
    o.need(inner.get('initial_pure_plan_recovery')==parent.get('initial_pure_plan_recovery'),'execution-final-engine-recovery-binding')
    if not inner.get('initial_pure_plan_recovery'):return inner['calls']
    from initial_ledger_recovery import engine_calls
    return engine_calls(inner)

def admitted_child_returncode(admission,index,call):
    """Only a fully verified admission can supply an exact historical exit."""
    original=None
    if admission:
        calls=admission.get('failed_calls',[])
        o.need(type(calls) is list,'execution-final-admitted-calls-invalid')
        if index<len(calls):original=calls[index]
        elif index==0:original=admission.get('initial_failed_call')
    if original is None:return 0
    o.need(call==original,'execution-final-admitted-child-changed')
    receipt=o.doc(original['result'])
    o.need(receipt.get('launch')==original['launch'] and receipt.get('argv')==original['argv'] and type(receipt.get('returncode')) is int,'execution-final-admitted-exit-binding')
    return receipt['returncode']

def replay(parent_ref):
    s=o.doc(parent_ref);order=o.validate(s['order']);folder=o.location(s['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and s['kind']=='role-execution-launcher-v1' and s['status']=='complete','execution-final-canonical-parent-required');o.need(s['clock_contract']==timing.MONOTONIC_CLOCK and s['boot_identity']==timing.Clock().boot(),'execution-final-clock-contract');o.need(s['scope_sha256']==order['scope_sha256'],'execution-final-scope-conflict')
    origin=o.doc(s['origin_ref']);o.need(all(s.get(k)==v for k,v in origin.items()),'execution-final-origin-changed')
    admission=None
    if s.get('initial_ledger_origin_recovery'):
        sys.path.insert(0,str(launch.FORMAL.parent));from initial_ledger_recovery import verify_recovered
        admission=verify_recovered(s,s['initial_ledger_origin_recovery'])
    for r in admission['code_refs'] if admission else s['code_refs']:o.raw(r)
    previous=s['start_monotonic'];o.need(s['calls'],'execution-final-no-children')
    for i,call in enumerate(s['calls']):
        o.need(call['state']=='returned' and Path(call['launch']['path'])==folder/'children'/(str(i).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(i).zfill(4)+'-exit.json'),'execution-final-child-path-state');a=o.doc(call['launch']);b=o.doc(call['result']);o.need(a['order']==s['order'] and a['index']==i and a['argv']==b['argv']==call['argv'] and b['launch']==call['launch'],'execution-final-child-binding')
        expected_returncode=admitted_child_returncode(admission,i,call)
        o.need(type(b.get('returncode')) is int and b['returncode']==expected_returncode,'execution-final-child-returncode')
        if expected_returncode==0:
            output=json.loads(b['stdout']);o.need(type(output) is dict and output.get('kind')=='complaint-execution-child-result-v1' and output.get('order')==s['order'],'execution-final-success-child-output')
        argv=call['argv'];o.need(len(argv)>=3 and argv[2] in ('run','accept'),'execution-final-child-verb');args=dict(zip(argv[3::2],argv[4::2]));response={'path':args['--response'],'sha256':args['--response-sha256']} if argv[2]=='accept' else None
        expected=launch.command(s['order'],argv[2],s,int(args.get('--steps',100)),response);o.need(argv==expected,'execution-final-child-argv-not-derived');o.need(previous<=a['launched_monotonic']<=b['exited_monotonic'],'execution-final-child-time-order');previous=b['exited_monotonic']
    o.need(b['returncode']==0,'execution-final-last-child-returncode')
    last=json.loads(b['stdout']);o.need(last.get('order')==s['order'] and last.get('status')=='complete','execution-final-child-not-complete');inner=o.doc(last['engine']);o.need(Path(last['engine']['path'])==folder/'engine.json' and inner['status']=='complete' and inner['order']==s['order'] and all(c['state']=='returned' and c.get('applied') for c in final_engine_calls(inner,s)),'execution-final-inner-unresolved')
    for c in final_engine_calls(inner,s):o.doc(c['result'])
    final=o.doc(s['completion']);o.need(final['engine']==last['engine'] and final['order']==s['order'] and final['start_monotonic']==s['start_monotonic'] and final['end_monotonic']==s['end_monotonic']>=previous and final['completed_at']==s['wall_ended_at'],'execution-final-clock-proof')
    sys.path.insert(0,str(launch.FORMAL.parent));from complaint_execution_ports import ProductionPorts
    proof=ProductionPorts(s['tab_id'],s['pid']).finish({'order':order,'companies':inner['companies'],'delivery':inner['delivery'],'folder':str(folder)});o.need(proof==final['proof']==inner['completion'],'execution-final-source-client-changed')
    # Acceptance is derived; a saved passed boolean cannot upgrade a slow run.
    passed=s['mode']=='acceptance' and s['origin']=='fresh' and s['end_monotonic']-s['start_monotonic']<=30;o.need(s['acceptance_pass']==passed,'execution-final-performance-not-derived')
    return s,order,proof

def check_current(current,order,s):
    o.need(current['day']==order['day'] and current['dispatch_id']==order['dispatch_id'] and current['phase'] in ('running','attention') and d.current(current)['role']==o.ROLE,'execution-final-current-dispatch');o.need(any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in current['events']),'execution-final-ack-required');start=timing.parse_time(current['dispatch_intent_at']);o.need(start<=timing.parse_time(s['wall_started_at'])<=timing.parse_time(s['wall_ended_at'])<=datetime.now(timezone.utc),'execution-final-current-time');o.need(not any(e.get('type')=='completed' and e.get('dispatch_id')==order['dispatch_id'] for e in current['events']),'execution-final-already-consumed')

def report(parent_ref,current_ref,release_ref,out):
    pins,request=original_inputs(release_ref,parent_ref);s,order,proof=replay(parent_ref)
    o.need(Path(current_ref['path'])==PROJECT/'runtime/workshop-director/state.json','execution-current-director-path');check_current(o.doc(current_ref),order,s)
    refs=[parent_ref,s['order'],s['origin_ref'],s['completion'],current_ref,release_ref,o.ref(HELPER),o.ref(LEGACY),*pins.values(),*proof['evidence'],*proof['clients']]
    if s.get('initial_ledger_origin_recovery'):
        from initial_ledger_recovery import verify_recovered
        refs.extend(verify_recovered(s,s['initial_ledger_origin_recovery'])['evidence'])
    evidence=[]
    for r in refs:
        b=o.raw(r);path=Path(out).parent/'evidence'/(r['sha256']+Path(r['path']).suffix);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():o.need(path.read_bytes()==b,'execution-final-snapshot-conflict')
        else:
            with path.open('xb') as f:f.write(b);f.flush();__import__('os').fsync(f.fileno())
        evidence.append(o.ref(path))
    original_inputs(release_ref,parent_ref)
    return o.immutable(out,{'kind':'complaint-parent-director-completion-v1','pure_completion_contract':CONTRACT,'pure_completion_provenance':{'release':release_ref,'helper':o.ref(HELPER),'legacy_orchestration':o.ref(LEGACY),'original':pins},'workflow':o.FLOW,'role':o.ROLE,'dispatch_id':order['dispatch_id'],'day':order['day'],'completed_at':s['wall_ended_at'],'live':True,'complete':True,'fixture':False,'test_target':'测试群请忽略','production_sent':False,'complaint_submitted':False,'verification_parent':parent_ref,'source_client_proof':proof,'evidence':evidence,'performance':{'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':proof['outcome'],'functional_completion_is_not_30s_pass':True}})

def verify_report_value(r,current=None):
    o.need(r.get('kind')=='complaint-parent-director-completion-v1' and r.get('pure_completion_contract')==CONTRACT,'complaint-report-exact-contract')
    p=r.get('pure_completion_provenance');o.need(type(p) is dict and set(p)=={'release','helper','legacy_orchestration','original'},'complaint-report-provenance-required')
    pins,request=original_inputs(p['release'],r['verification_parent']);o.need(p=={'release':p['release'],'helper':o.ref(HELPER),'legacy_orchestration':o.ref(LEGACY),'original':pins},'complaint-report-provenance-changed')
    s,order,proof=replay(r['verification_parent'])
    if current is not None:check_current(current,order,s)
    o.need((r['workflow'],r['dispatch_id'],r['day'],r['role'],r['completed_at'],r['source_client_proof'])==(o.FLOW,order['dispatch_id'],order['day'],o.ROLE,s['wall_ended_at'],proof),'execution-final-report-scope-changed')
    o.need(r.get('live') is True and r.get('complete') is True and r.get('fixture') is False and r.get('test_target')=='测试群请忽略' and r.get('production_sent') is False and r.get('complaint_submitted') is False,'complaint-report-test-draft-only')
    expected={'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':proof['outcome'],'functional_completion_is_not_30s_pass':True};o.need(r['performance']==expected,'execution-final-report-performance-changed')
    for reference in r['evidence']:o.raw(reference)
    original_inputs(p['release'],r['verification_parent']);return r

def verify_report(path,current):return verify_report_value(o.doc(o.ref(Path(path))),current)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','director','release'):
        p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    parent={'path':a.parent,'sha256':a.parent_sha256};release={'path':a.release,'sha256':a.release_sha256}
    pins,request=original_inputs(release,parent);o.need(Path(sys.executable)==Path(request['config']['python']),'complaint-report-fixed-interpreter')
    result=report(parent,{'path':a.director,'sha256':a.director_sha256},release,a.out)
    print(json.dumps({'kind':'reviewed-complaint-completion-report-produced-v1','report':result,'release':release,'parent':parent,'ui_used':False},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)}));raise SystemExit(2)
