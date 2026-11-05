#!/usr/bin/env python3
"""Controlled role child launcher; outer clock includes all child startup/waits.
Candidate complaint-only entry. Does not schedule/initialize a director.
"""
import time
ENTRY=time.clock_gettime(time.CLOCK_MONOTONIC)
import argparse,hashlib,json,os,subprocess,sys,fcntl
from datetime import datetime,timezone
WALL_ENTRY=datetime.now(timezone.utc)
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import complaint_execution_order as o
import execution_timing as timing
PROJECT=(Path(__file__).resolve().parents[3]/'skills/daily-comment-stats').resolve().parents[1]
FORMAL=Path(__file__).resolve().parents[2]/'negative-review-complaints/scripts/complaint_execution.py'
def code_refs(order=None):
    # Runtime code is imported normally. Historical source inventories do not
    # participate in a current operation or authorize an input.
    return []
def effective_code_refs(s):return []
def save(path,s):
    # Same atomic+fsync protocol as inner engine; imports occur outside pure scopes.
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('w') as f:json.dump(s,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
def command(order,verb,s,steps,response=None):
    out=[sys.executable,str(FORMAL),verb,'--order',order['path'],'--order-sha256',order['sha256'],'--tab-id',str(s['tab_id']),'--pid',str(s['pid'])]
    if verb=='run':out+=['--steps',str(steps)]
    if verb=='accept':out+=['--response',response['path'],'--response-sha256',response['sha256']]
    return out
def view(s,clock):
    elapsed=s.get('end_monotonic',clock.monotonic())-s['start_monotonic']
    result={'status':s['status'],'order':s['order'],'elapsed_seconds':elapsed,'deadline_exceeded':elapsed>30,'acceptance_pass':s.get('acceptance_pass',False),'functional_completion_is_not_30s_pass':True,'child':s.get('child'),'completion':s.get('completion'),'error':s.get('error'),'last_child_receipt':s['calls'][-1].get('result') if s['calls'] else None,'controlled_status_command':[sys.executable,str(Path(__file__).resolve()),'status','--order',s['order']['path'],'--order-sha256',s['order']['sha256'],'--mode',s['mode']],'start_boundary':'before-order-validation-and-first-role-child-launch','end_boundary':'last-child-exit-and-source-client-replay-complete','launcher_bootstrap_included':False,'final_telemetry_fsync_included':False}
    file=o.location(s['order'])/'engine.json'
    if file.exists():
        sys.path.insert(0,str(FORMAL.parent));from complaint_execution_ports import ProductionPorts
        state=json.loads(file.read_bytes());o.need(state['order']==s['order'],'execution-original-engine-required');result['engine']=o.ref(file);result['business_journal_candidates']=ProductionPorts(s['tab_id'],s['pid']).journals(o.validate(s['order']),state)
    if s.get('company_scope_reconciliation'):
        from initial_ledger_recovery import company_scope_admission
        admission=company_scope_admission(s);result.update(active_scope_complete=s['status']=='complete',original_scope_complete=False,retired_incomplete=True,active_indices=admission['active_indices'],retired_indices=admission['retired_indices'])
    return result
CHILD_STOPPED_RESUME_KIND='role-execution-child-exit-resume-v1'
def resume_after_stopped_child(folder,s,path):
    # B65: repair() returns the task to queued, but a launcher whose child exited
    # non-zero sits at hold/execution-child-stopped and returns before launching
    # anything, so the re-dispatched attempt does no work at all (attempt-8: the
    # whole run was one view() over the previous start_monotonic). Only that exact
    # stop is resumable, only with an explicit proof naming these launcher bytes
    # and that child's exit receipt, and only once - adopting the proof rewrites
    # launcher.json, so the same bytes can never authorise a second launch.
    # outcome-unknown stays a hard stop: no receipt, no resume.
    proof_path=folder/'resume-after-stopped-child.json'
    if not proof_path.exists()or s['status']!='hold':return False
    if not s['calls']or s['calls'][-1].get('state')!='returned':return False
    proof=o.doc(o.ref(proof_path));o.need(proof.get('kind')==CHILD_STOPPED_RESUME_KIND,'child-stopped-resume-kind')
    o.need(proof.get('launcher')==o.ref(path),'child-stopped-resume-launcher-bytes')
    o.need(proof.get('exit_receipt')==s['calls'][-1]['result'],'child-stopped-resume-receipt-binding')
    o.need(type(proof.get('reason'))is str and proof['reason'],'child-stopped-resume-reason')
    error=s.get('error');receipt=o.doc(s['calls'][-1]['result'])
    if error!='execution-child-stopped':
        # A child that exits 0 while reporting hold is the second, equally
        # verifiable shape: the hold must be readable back out of that child's own
        # exit receipt, so a proof cannot invent an error the child never returned.
        output=json.loads(receipt.get('stdout')or'{}')
        o.need(receipt.get('returncode')==0 and output.get('status')=='hold'and output.get('error')==error,'child-stopped-resume-hold-binding')
    o.need(proof.get('original_error')==error,'child-stopped-resume-error-binding')
    s.update(status='running');s.pop('error',None)
    s.setdefault('child_exit_resumes',[]).append({'proof':o.ref(proof_path),'at':proof.get('at'),'reason':proof['reason'],'original_error':error,'resumed_call_index':len(s['calls'])})
    save(path,s);return True
def run(order_ref,verb,*,tab_id=None,pid=None,steps=100,mode='development',response=None,clock=None,runner=None,entry=None):
    clock=clock or timing.Clock();sample=entry or (clock.monotonic(),clock.wall());order=o.validate(order_ref);folder=o.location(order_ref);path=folder/'launcher.json'
    if verb=='status':
        o.need(path.exists(),'execution-not-started-readonly');s=json.loads(path.read_bytes());o.need(s['order']==order_ref and s['scope_sha256']==order['scope_sha256'] and s['mode']==mode,'execution-original-launcher-required');o.need(clock.boot()==s['boot_identity'],'execution-boot-clock-changed')
        for r in effective_code_refs(s):o.raw(r)
        return view(s,clock)
    folder.mkdir(parents=True,exist_ok=True)
    with (folder/'launcher.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if path.exists():
            s=json.loads(path.read_bytes());o.need(s['order']==order_ref and s['scope_sha256']==order['scope_sha256'] and s['mode']==mode,'execution-original-launcher-required');o.need(clock.boot()==s['boot_identity'] and clock.monotonic()>=s['start_monotonic'],'execution-boot-clock-changed')
            for ref in effective_code_refs(s):o.raw(ref)
            o.need(tab_id in (None,s['tab_id']) and pid in (None,s['pid']),'execution-tab-pid-binding-changed')
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
        for index,call in enumerate(s['calls']):
            if call['state']=='unknown':
                receipt=folder/'children'/(str(index).zfill(4)+'-exit.json')
                if not receipt.exists():s.update(status='hold',error='execution-child-outcome-unknown-no-replay');save(path,s);return view(s,clock)
                value=o.doc(o.ref(receipt));o.need(value['launch']==call['launch'] and value['argv']==call['argv'],'execution-exit-receipt-conflict');call.update(state='returned',result=o.ref(receipt));save(path,s)
                return consume(s,order,folder,path,call,clock)
        if response:o.raw(response)
        argv=command(order_ref,verb,s,steps,response);index=len(s['calls']);launch=o.immutable(folder/'children'/(str(index).zfill(4)+'-launch.json'),{'argv':argv,'order':order_ref,'index':index,'launched_monotonic':clock.monotonic(),'at':clock.wall().isoformat()});call={'state':'unknown','argv':argv,'launch':launch};s['calls'].append(call);save(path,s)
        try:
            proc=runner(argv) if runner else subprocess.run(argv,text=True,capture_output=True)
            receipt=o.immutable(folder/'children'/(str(index).zfill(4)+'-exit.json'),{'launch':launch,'argv':argv,'returncode':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr,'exited_monotonic':clock.monotonic(),'at':clock.wall().isoformat()});call.update(state='returned',result=receipt);save(path,s)
        except BaseException:
            # No cancellation, restart, alternate key or input retry on timeout.
            raise
        return consume(s,order,folder,path,call,clock)
def consume(s,order,folder,path,call,clock):
    receipt=o.doc(call['result']);o.raw(call['launch']);o.need(receipt['argv']==call['argv'] and receipt['launch']==call['launch'],'execution-child-receipt-binding')
    if receipt['returncode']!=0:s.update(status='hold',error='execution-child-stopped');save(path,s);return view(s,clock)
    output=json.loads(receipt['stdout']);o.need(type(output) is dict and output.get('kind')=='complaint-execution-child-result-v1' and output.get('order')==s['order'],'execution-child-output-binding');s['child']=output
    if output['status']=='complete':
        # This is a pure existing-API replay after the last child exits: no UI,
        # sender, complete or progress mutation is performed by this check.
        import importlib.util
        role_dir=FORMAL.parent;sys.path.insert(0,str(role_dir))
        from complaint_execution_ports import ProductionPorts
        state=o.doc(output['engine']);need_order=state['order'];o.need(need_order==s['order'] and state['status']=='complete','execution-original-final-engine');ports=ProductionPorts(s['tab_id'],s['pid']);ports.guard(order,state)
        import complaint_execution as engine
        proof=ports.finish(engine.scoped_context(state,{'order':order,'companies':state['companies'],'delivery':state['delivery'],'folder':str(folder)}));o.need(proof==state['completion'],'execution-final-proof-changed')
        end=clock.monotonic();ended_at=clock.wall().isoformat();s.update(status='complete',end_monotonic=end,wall_ended_at=ended_at,acceptance_pass=s['mode']=='acceptance' and s['origin']=='fresh' and end-s['start_monotonic']<=30,completion=o.immutable(folder/'completion.json',{'kind':'complaint-outer-completion-v1','order':s['order'],'engine':output['engine'],'proof':proof,'start_monotonic':s['start_monotonic'],'end_monotonic':end,'completed_at':ended_at,'outcome':proof['outcome']}))
    elif output['status']=='hold':s.update(status='hold',error=output.get('error') or 'execution-child-held')
    else:s['status']=output['status']
    save(path,s);return view(s,clock)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=('start','run','accept','status'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--tab-id',type=int);p.add_argument('--pid',type=int);p.add_argument('--steps',type=int,default=100);p.add_argument('--mode',choices=('development','acceptance'),default='development');p.add_argument('--response');p.add_argument('--response-sha256');a=p.parse_args();o.need(bool(a.response)==bool(a.response_sha256),'execution-response-paired-ref-required');r={'path':a.order,'sha256':a.order_sha256};response={'path':a.response,'sha256':a.response_sha256} if a.response else None
    print(json.dumps(run(r,a.verb,tab_id=a.tab_id,pid=a.pid,steps=a.steps,mode=a.mode,response=response,entry=(ENTRY,WALL_ENTRY)),ensure_ascii=False))

# One explicit scope per command; no interprocess or persistent cache.
_history_command_original_run = run
def run(*args, **kwargs):
    from initial_ledger_recovery import window_hold_history_scope
    import execution_timing as timing
    with window_hold_history_scope(max_entries=16),timing.company_policy_command():
        return _history_command_original_run(*args, **kwargs)

if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
