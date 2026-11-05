#!/usr/bin/env python3
"""Controlled role child launcher; outer clock includes all child startup/waits.
Candidate violation-only entry. Does not schedule/initialize a director.
"""
import time
ENTRY=time.clock_gettime(time.CLOCK_MONOTONIC)
import argparse,hashlib,json,os,subprocess,sys,fcntl
from datetime import datetime,timezone
WALL_ENTRY=datetime.now(timezone.utc)
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import role_execution_order as o
import execution_timing as timing
PROJECT=Path(__file__).resolve().parents[3]
FORMAL=PROJECT/'skills/violation-notifier/scripts/violation_execution.py'
def code_refs(order=None):
    return []
def reboot_admission(s,clock=None):
    if not s.get('reboot_continuation'):return None
    sys.path.insert(0,str(FORMAL.parent))
    import violation_reboot_continuation as reboot
    a=reboot.verify(s['reboot_continuation'],**({'live_boot':clock.boot()} if clock is not None else {}))
    original=o.doc(a['original']['parent'])
    o.need(s['order']==original['order'] and s['origin_ref']==original['origin_ref'] and all(s.get(k)==original[k] for k in ('boot_identity','start_monotonic','wall_started_at','pid','tab_id','code_refs','scope_sha256','mode','origin')),'execution-reboot-original-parent-changed')
    o.need(s['calls'][:len(original['calls'])]==original['calls'],'execution-reboot-original-calls-changed')
    return a

def live_boot_ok(s,clock):
    a=reboot_admission(s,clock)
    if a is None:return clock.boot()==s['boot_identity']
    import math
    start=a['segment']['start_monotonic'];now=clock.monotonic()
    o.need(type(start) in (int,float) and type(now) in (int,float) and math.isfinite(start) and math.isfinite(now) and 0<=start<=now,'execution-reboot-segment-clock-invalid')
    return True

def effective_scope(s):
    a=reboot_admission(s)
    return a['effective_scope'] if a else {'tab_id':s['tab_id'],'pid':s['pid']}

def performance(s):
    if s.get('reboot_continuation'):
        reboot_admission(s)
        o.need(s.get('acceptance_pass') is False and s.get('end_monotonic') is None and s.get('clock_comparable') is False,'execution-reboot-performance-invalid')
        return {'acceptance_pass':False,'elapsed_seconds':None,'outcome':s.get('completion_outcome'),'functional_completion_is_not_30s_pass':True,'clock_comparable':False,'reboot_continuation':s['reboot_continuation']}
    return {'acceptance_pass':s['acceptance_pass'],'elapsed_seconds':s['end_monotonic']-s['start_monotonic'],'outcome':s.get('completion_outcome'),'functional_completion_is_not_30s_pass':True}

def effective_code_refs(s):
    return []

def save(path,s):
    # Same atomic+fsync protocol as inner engine; imports occur outside pure scopes.
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:json.dump(s,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def command(order,verb,s,steps,response=None):
    scope=effective_scope(s)
    out=[sys.executable,str(FORMAL),verb,'--order',order['path'],'--order-sha256',order['sha256'],'--tab-id',str(scope['tab_id']),'--pid',str(scope['pid'])]
    if verb=='run':out+=['--steps',str(steps)]
    if verb=='accept':out+=['--response',response['path'],'--response-sha256',response['sha256']]
    return out
def view(s,clock):
    a=reboot_admission(s)
    elapsed=None if a else s.get('end_monotonic',clock.monotonic())-s['start_monotonic']
    result={'status':s['status'],'order':s['order'],'elapsed_seconds':elapsed,'deadline_exceeded':None if a else elapsed>30,'acceptance_pass':s.get('acceptance_pass',False),'functional_completion_is_not_30s_pass':True,'child':s.get('child'),'completion':s.get('completion'),'error':s.get('error'),'last_child_receipt':s['calls'][-1].get('result') if s['calls'] else None,'controlled_status_command':[sys.executable,str(Path(__file__).resolve()),'status','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--mode',s['mode']],'start_boundary':'before-order-validation-and-first-role-child-launch','end_boundary':'last-child-exit-and-source-client-replay-complete','launcher_bootstrap_included':False,'final_telemetry_fsync_included':False}
    if a:result.update(clock_comparable=False,acceptance_pass=False,reboot_continuation=s['reboot_continuation'],original_parent_clock=a['original']['parent_clock'],current_segment=s.get('reboot_segment_end') or a['segment'])
    file=o.location(s['order'])/'engine.json'
    if file.exists():
        sys.path.insert(0,str(FORMAL.parent));from violation_execution_ports import ProductionPorts
        state=json.loads(file.read_bytes());o.need(state['order']==s['order'],'execution-original-engine-required');result['engine']=o.ref(file);result['business_journal_candidates']=ProductionPorts(effective_scope(s)['tab_id'],effective_scope(s)['pid']).journals(o.validate(s['order']),state)
    return result
CHILD_STOPPED_RESUME_KIND='role-execution-child-exit-resume-v1'
def resume_after_stopped_child(folder,s,path):
    # B65 (same rule as the complaint launcher): repair() returns the task to
    # queued, but a launcher whose child exited non-zero sits at
    # hold/execution-child-stopped and returns before launching anything, so the
    # re-dispatched attempt does no work. A child that exits zero while the
    # engine itself is on hold parks the launcher at hold with the engine's own
    # error instead (attempt-3). Only a hold is resumable, only with an explicit
    # proof naming these launcher bytes, that exact hold error and the last
    # child's exit receipt, and only once - adopting the proof rewrites
    # launcher.json, so the same bytes can never authorise a second launch.
    # outcome-unknown stays fatal.
    proof_path=folder/'resume-after-stopped-child.json'
    if not proof_path.exists()or s['status']!='hold':return False
    if not s['calls']or s['calls'][-1].get('state')!='returned':return False
    proof=o.doc(o.ref(proof_path));o.need(proof.get('kind')==CHILD_STOPPED_RESUME_KIND,'child-stopped-resume-kind')
    o.need(proof.get('launcher')==o.ref(path),'child-stopped-resume-launcher-bytes')
    o.need(proof.get('exit_receipt')==s['calls'][-1]['result'],'child-stopped-resume-receipt-binding')
    o.need(proof.get('original_error')==s.get('error'),'child-stopped-resume-error')
    o.need(type(proof.get('reason'))is str and proof['reason'],'child-stopped-resume-reason')
    s.update(status='running');s.pop('error',None)
    s.setdefault('child_exit_resumes',[]).append({'proof':o.ref(proof_path),'at':proof.get('at'),'reason':proof['reason'],'resumed_call_index':len(s['calls'])})
    save(path,s);return True
def run(order_ref,verb,*,tab_id=None,pid=None,steps=100,mode='development',response=None,clock=None,runner=None,entry=None):
    clock=clock or timing.Clock();sample=entry or (clock.monotonic(),clock.wall());order=o.validate(order_ref);folder=o.location(order_ref);path=folder/'launcher.json'
    if verb=='status':
        o.need(path.exists(),'execution-not-started-readonly');s=json.loads(path.read_bytes());o.need(s['order']==order_ref and s['scope_sha256']==order['scope_sha256'] and s['mode']==mode,'execution-original-launcher-required');o.need(live_boot_ok(s,clock),'execution-boot-clock-changed')
        for r in effective_code_refs(s):o.raw(r)
        return view(s,clock)
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'launcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if path.exists():
            s=json.loads(path.read_bytes());o.need(s['order']==order_ref and s['scope_sha256']==order['scope_sha256'] and s['mode']==mode,'execution-original-launcher-required');o.need(live_boot_ok(s,clock) and (s.get('reboot_continuation') or clock.monotonic()>=s['start_monotonic']),'execution-boot-clock-changed')
            for ref in effective_code_refs(s):o.raw(ref)
            scope=effective_scope(s);o.need(tab_id in (None,scope['tab_id']) and pid in (None,scope['pid']),'execution-tab-pid-binding-changed')
            if verb=='start':return view(s,clock)
        else:
            o.need(verb=='start' and type(tab_id) is int and tab_id>0 and type(pid) is int and pid>0,'execution-start-explicit-scope-required')
            o.need(mode in ('development','acceptance'),'execution-mode-invalid')
            s={'kind':'role-execution-launcher-v1','order':order_ref,'scope_sha256':order['scope_sha256'],'mode':mode,'origin':order['origin'],'clock_contract':timing.MONOTONIC_CLOCK,'boot_identity':clock.boot(),'start_monotonic':sample[0],'wall_started_at':sample[1].isoformat(),'status':'running','calls':[],'tab_id':tab_id,'pid':pid,'code_refs':code_refs(order)};s['origin_ref']=o.immutable(folder/'origin.json',{k:v for k,v in s.items() if k not in ('calls','status')});save(path,s)
            return view(s,clock)
        if verb!='status'and resume_after_stopped_child(folder,s,path):pass
        if verb=='status' or s['status'] in ('complete','hold','collection-ready'):return view(s,clock)
        o.need(verb in ('run','accept') and type(steps) is int and 1<=steps<=1000,'execution-verb-budget-invalid')
        # A missing child exit receipt is not permission to launch it again.
        for index in range(max(0,len(s['calls'])-1),len(s['calls'])):
            call=s['calls'][index]
            if call['state']=='unknown':
                receipt=folder/'children'/(str(index).zfill(4)+'-exit.json')
                if not receipt.exists():s.update(status='hold',error='execution-child-outcome-unknown-no-replay');save(path,s);return view(s,clock)
                value=o.doc(o.ref(receipt));o.need(value['launch']==call['launch'] and value['argv']==call['argv'],'execution-exit-receipt-conflict');call.update(state='returned',result=o.ref(receipt));save(path,s)
                return consume(s,order,folder,path,call,clock)
        if response:o.raw(response)
        argv=command(order_ref,verb,s,steps,response);index=len(s['calls']);launch=o.immutable(folder/'children'/(str(index).zfill(4)+'-launch.json'),{'argv':argv,'order':order_ref,'index':index,'launched_monotonic':clock.monotonic(),'at':clock.wall().isoformat(),**({'reboot_continuation':s['reboot_continuation'],'boot_identity':clock.boot()} if s.get('reboot_continuation') else {})});call={'state':'unknown','argv':argv,'launch':launch};s['calls'].append(call);save(path,s)
        try:
            proc=runner(argv) if runner else subprocess.run(argv,text=True,capture_output=True)
            receipt=o.immutable(folder/'children'/(str(index).zfill(4)+'-exit.json'),{'launch':launch,'argv':argv,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'exited_monotonic':clock.monotonic(),'at':clock.wall().isoformat(),**({'reboot_continuation':s['reboot_continuation'],'boot_identity':clock.boot()} if s.get('reboot_continuation') else {})});call.update(state='returned',result=receipt);save(path,s)
        except BaseException:
            # No cancellation, restart, alternate key or input retry on timeout.
            raise
        return consume(s,order,folder,path,call,clock)
def consume(s,order,folder,path,call,clock):
    receipt=o.doc(call['result']);o.raw(call['launch']);o.need(receipt['argv']==call['argv'] and receipt['launch']==call['launch'],'execution-child-receipt-binding')
    if receipt['returncode']!=0:s.update(status='hold',error='execution-child-stopped');save(path,s);return view(s,clock)
    output=json.loads(receipt['stdout']);o.need(type(output) is dict and output.get('kind')=='violation-execution-child-result-v1' and output.get('order')==s['order'],'execution-child-output-binding');s['child']=output
    if output['status']=='complete':
        # This is a pure existing-API replay after the last child exits: no UI,
        # sender, complete or progress mutation is performed by this check.
        import importlib.util
        role_dir=FORMAL.parent;sys.path.insert(0,str(role_dir))
        from violation_execution_ports import ProductionPorts
        state=o.doc(output['engine']);need_order=state['order'];o.need(need_order==s['order'] and state['status']=='complete','execution-original-final-engine');scope=effective_scope(s);ports=ProductionPorts(scope['tab_id'],scope['pid'])
        if s.get('reboot_continuation'):ports.reboot_continuation=s['reboot_continuation']
        ports.guard(order,state)
        proof=ports.finish({'order':order,'companies':state['companies'],'delivery':state['delivery'],'folder':str(folder)});o.need(proof==state['completion'],'execution-final-proof-changed')
        end=clock.monotonic();ended_at=clock.wall().isoformat()
        if s.get('reboot_continuation'):
            live_boot_ok(s,clock);a=reboot_admission(s,clock)
            segment_end={'boot':a['segment']['boot'],'end_monotonic':end,'wall_ended_at':ended_at}
            completion={'kind':'violation-reboot-outer-completion-v1','order':s['order'],'engine':output['engine'],'proof':proof,'start_monotonic':s['start_monotonic'],'end_monotonic':None,'completed_at':ended_at,'outcome':proof['outcome'],'reboot_continuation':s['reboot_continuation'],'segment_end':segment_end,'clock_comparable':False,'acceptance_pass':False}
            s.update(status='complete',end_monotonic=None,wall_ended_at=ended_at,acceptance_pass=False,clock_comparable=False,elapsed_seconds=None,reboot_segment_end=segment_end,completion_outcome=proof['outcome'],completion=o.immutable(folder/'completion.json',completion))
        else:
            s.update(status='complete',end_monotonic=end,wall_ended_at=ended_at,acceptance_pass=s['mode']=='acceptance' and s['origin']=='fresh' and end-s['start_monotonic']<=30,completion=o.immutable(folder/'completion.json',{'kind':'violation-outer-completion-v1','order':s['order'],'engine':output['engine'],'proof':proof,'start_monotonic':s['start_monotonic'],'end_monotonic':end,'completed_at':ended_at,'outcome':proof['outcome']}))
    elif output['status']=='hold':s.update(status='hold',error=output.get('error') or 'execution-child-held')
    else:s['status']=output['status']
    save(path,s);return view(s,clock)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=('start','run','accept','status'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--tab-id',type=int);p.add_argument('--pid',type=int);p.add_argument('--steps',type=int,default=100);p.add_argument('--mode',choices=('development','acceptance'),default='development');p.add_argument('--response');p.add_argument('--response-sha256');a=p.parse_args();o.need(bool(a.response)==bool(a.response_sha256),'execution-response-paired-ref-required');r={'path':a.order,'sha256':a.order_sha256};response={'path':a.response,'sha256':a.response_sha256} if a.response else None
    print(json.dumps(run(r,a.verb,tab_id=a.tab_id,pid=a.pid,steps=a.steps,mode=a.mode,response=response,entry=(ENTRY,WALL_ENTRY)),ensure_ascii=False))
_policy_original_run=run
def run(*args,**kwargs):
    import execution_timing as timing
    from violation_execution_ports import identity_history_command
    with identity_history_command(),timing.company_policy_command():return _policy_original_run(*args,**kwargs)

if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
