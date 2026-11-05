#!/usr/bin/env python3
"""Shanghai morning coordinator. One global lock/day, no business execution.
Reads only five fixed business ledgers; never modifies them or starts automation.
"""
import argparse,fcntl,hashlib,json,os,tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import director as d
PROJECT=Path(__file__).resolve().parents[3]
DEFAULT_ROOT=PROJECT/'runtime/workshop-director'
COMPANIES=('烟台一成教育文化咨询有限公司','上海老芗汇餐饮管理有限公司')
ZONE=ZoneInfo('Asia/Shanghai')
def sha(raw):return hashlib.sha256(raw).hexdigest()
def today(now=None):
    now=now or datetime.now(ZONE);d.require(now.utcoffset() is not None,'coordinator-aware-time-required');return now.astimezone(ZONE).date().isoformat()
def immutable(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():d.require(path.read_bytes()==raw,'coordinator-immutable-conflict');return
    # Publish only fully flushed bytes. A crash while writing the temporary file
    # cannot leave a partial archive at the immutable destination.
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name+'.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        try: os.link(temporary, path)
        except FileExistsError:
            d.require(path.read_bytes()==raw, 'coordinator-immutable-conflict')
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def company_policy(reference):
    import execution_timing as scope
    return scope.company_policy(reference)
def company_names(reference=None):
    import execution_timing as scope
    return scope.company_names(reference)

def fixed_ledgers(project=PROJECT,policy=None):
    return [(d.FLOWS[0],None,Path(project)/'runtime/daily-comment-stats/progress.json')]+[(flow,company,Path(project)/'runtime'/flow/company/'state.json') for flow in d.FLOWS[1:] for company in company_names(policy)]
def ledger_snapshot(root,project=PROJECT,policy=None):
    entries=[]
    for flow,company,path in fixed_ledgers(project,policy):
        d.require(path.is_file(),'coordinator-fixed-ledger-missing:'+flow);raw=path.read_bytes();data=json.loads(raw);d.require(data.get('version')==1,'coordinator-business-ledger-version-invalid')
        if company:d.require(data.get('company')==company,'coordinator-business-ledger-company-mismatch');scopes={company:data}
        else:d.require(set(company_names(policy))<=set(data.get('companies',{})),'coordinator-daily-company-progress-missing');scopes={c:data['companies'][c] for c in company_names(policy)}
        summary={}
        for c,value in scopes.items():
            d.require(isinstance(value,dict) and value.get('next_start'),'coordinator-next-start-required')
            summary[c]={k:value.get(k) for k in ('next_start','covered_through','last_completed_on')}
            # Keep original planning/task/batch identity exactly in hashed raw snapshots.
            summary[c]['original_plan_ids']=list(value.get('planned_runs',{}));summary[c]['original_batch_ids']=list(value.get('batches',{}));summary[c]['original_task_ids']=list(value.get('tasks',{}))
        digest=sha(raw);copy=Path(root)/'ledger-snapshots'/(digest+'.json');immutable(copy,raw);d.require(path.read_bytes()==raw,'coordinator-business-ledger-changed-during-read');entries.append({'workflow':flow,'company':company,'original_path':str(path.resolve()),'snapshot':ref(copy),'progress':summary})
    for entry in entries:d.require(sha(Path(entry['original_path']).read_bytes())==entry['snapshot']['sha256'],'coordinator-ledger-snapshot-stale-before-dispatch')
    return entries
@contextmanager
def locked(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    d.require(not (root/'.coordinator-owned.json').exists(),'coordinator-cannot-use-day-archive-as-root')
    with (root/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);yield root

def exchange_quiescent_state(root,before_state,before_config,after_state,after_config):
    """Caller holds coordinator lock; exact durable before/after only, no plan."""
    root=Path(root).resolve()
    pairs=[(root/'state.json',before_state,after_state),(root/'coordinator.json',before_config,after_config)]
    for target,before,after in pairs:
        d.require(not target.is_symlink() and ref(target) in ({'path':str(target),'sha256':before['sha256']},{'path':str(target),'sha256':after['sha256']}),'coordinator-lease-CAS-conflict')
        raw=Path(after['path']).read_bytes();d.require(sha(raw)==after['sha256'],'coordinator-lease-snapshot-changed')
    for target,before,after in pairs:
        raw=Path(after['path']).read_bytes();fd,temp=tempfile.mkstemp(dir=root,prefix='.lease-exchange-')
        try:
            with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.replace(temp,target)
        finally:
            if os.path.exists(temp):os.unlink(temp)
    d.require(d.read(root/'coordinator.json')['active_day']==d.read(root/'state.json')['day'],'coordinator-lease-day-conflict')

def bind_config(root,acceptance):
    path=root/'coordinator.json'
    if path.exists():
        c=d.read(path);d.require(c.get('timezone')=='Asia/Shanghai' and c.get('root')==str(root),'coordinator-root-scope-conflict')
        if acceptance:d.require({k:str(Path(v).resolve()) for k,v in d.read(acceptance).items()}==c['acceptance'],'coordinator-acceptance-change-not-allowed')
        # Old configuration inherits the ORIGINAL state pins, never fresh file
        # hashes. Read-only recovery remains possible even if evidence changed.
        if 'acceptance_proofs' not in c:
            state=d.read(root/'state.json');c={**c,'acceptance_proofs':state.get('acceptance',{})}
        return c
    d.require(acceptance,'coordinator-initial-acceptance-required');accepted=d.read(acceptance);d.require(set(accepted)==set(d.FLOWS),'three-acceptances-required');accepted={k:str(Path(v).resolve()) for k,v in accepted.items()}
    # Enforce real live acceptance even when adopting a legacy dispatch state.
    proofs={flow:d.proof(accepted[flow],flow) for flow in d.FLOWS}
    c={'version':1,'root':str(root),'timezone':'Asia/Shanghai','acceptance':accepted,'acceptance_proofs':proofs,'active_day':None,'archives':[],'created_at':d.stamp()};d.atomic(path,c);return c

def archive(root,s,c):
    day=s['day'];folder=root/'days'/day;folder.mkdir(parents=True,exist_ok=True);raw=(root/'state.json').read_bytes();immutable(folder/'state.json',raw);immutable(folder/'.coordinator-owned.json',json.dumps({'root':str(root),'day':day},sort_keys=True).encode());entry={'day':day,'state':ref(folder/'state.json')}
    previous=[a for a in c['archives'] if a['day']==day]
    if previous:d.require(previous==[entry],'coordinator-archive-conflict')
    else:c['archives'].append(entry)

def recover_archives(root,c):
    for path in sorted((root/'days').glob('*/state.json')):
        state=d.read(path);d.require(path.parent.name==state['day'] and d.current(state).get('action')=='done','coordinator-invalid-day-archive')
        marker=d.read(path.parent/'.coordinator-owned.json');d.require(marker=={'root':str(root),'day':state['day']},'coordinator-archive-owner-conflict');entry={'day':state['day'],'state':ref(path)};old=[v for v in c['archives'] if v['day']==state['day']]
        if old:d.require(old==[entry],'coordinator-archive-changed')
        else:c['archives'].append(entry)

def verify_config_acceptance(c,s):
    # Historical acceptance reports are archival, never runtime dependencies.
    d.verify_current_configuration(s)


def company_policy_location(root,configuration,state):
    """Explicit pinned version policy; legacy canonical v1 bytes stay unchanged."""
    root=Path(root).resolve();cp=configuration.get('active_company_policy');sp=state.get('active_company_policy')
    d.require(not(cp and sp)or cp==sp,'coordinator-company-policy-config-state-conflict');pin=cp or sp;legacy=root/'active-company-policy.json'
    if pin is None:return legacy,None
    d.require(type(pin)is dict and set(pin)=={'path','sha256'}and type(pin['sha256'])is str and len(pin['sha256'])==64 and all(c in '0123456789abcdef'for c in pin['sha256']),'coordinator-policy-reference-shape')
    path=Path(pin['path']);d.require(path.is_absolute()and path.resolve()==path and path.is_file()and not any(p.is_symlink()for p in(path,*path.parents))and ref(path)==pin,'coordinator-adopted-company-policy-removed-or-changed')
    if path!=legacy:
        d.require(path==root/'company-policies'/(pin['sha256']+'.json'),'coordinator-version-policy-location');value=d.read(path);d.require(type(value)is dict and set(value)=={'kind','configuration','configuration_code','active_ids','retired_ids'}and value['kind']=='active-company-scope-policy-v2','coordinator-version-policy-v2-required')
    return path,pin

def dispatch_plan(root,s,project=PROJECT,dispatcher="codex"):
    if d.current(s).get('action')=='deliver-ready-batch':return d.current(s)
    if s['phase']=='ready' and d.current(s).get('action')!='done':
        verify_config_acceptance(bind_config(root,None),s)
        # Persist role ledger snapshots before plan can emit a dispatch offer.
        configuration=bind_config(root,None)
        policy_path,pinned_policy=company_policy_location(root,configuration,s)
        if pinned_policy: d.require(policy_path.is_file()and not policy_path.is_symlink()and ref(policy_path)==pinned_policy,'coordinator-adopted-company-policy-removed-or-changed')
        if policy_path.exists():
            policy_ref=ref(policy_path);company_policy(policy_ref)
            d.require(not pinned_policy or pinned_policy==policy_ref,'coordinator-company-policy-replacement-needs-explicit-migration')
            s['active_company_policy']=policy_ref
            if not configuration.get('active_company_policy'):
                configuration['active_company_policy']=policy_ref;d.atomic(Path(root)/'coordinator.json',configuration)
        s['ledger_snapshots']=ledger_snapshot(root,project,s.get('active_company_policy'));s['events'].append({'type':'business-ledger-snapshot','at':d.stamp(),'snapshots':s['ledger_snapshots']});d.atomic(root/'state.json',s)
    result=d.plan(s,dispatcher=dispatcher);d.atomic(root/'state.json',s)
    if result.get('action')=='dispatch':
        result['ledger_snapshots']=[e for e in s['ledger_snapshots'] if e['workflow']==result['workflow']]
        if s.get('active_company_policy'):result['active_company_policy']=s['active_company_policy']
        if s.get('collection_contract'):result['collection_contract']=s['collection_contract']
        result['message']+=' 本次已固定本岗进度快照：'+json.dumps(result['ledger_snapshots'],ensure_ascii=False)+'；核对原业务台账，保留原任务/工单，不由调度器推进日期。'
        if result['workflow']==d.FLOWS[0]:
            import daily_orchestration
            try:
                result=daily_orchestration.bind_daily(root,s,result)
                d.atomic(root/'state.json',s)
            except (ValueError,OSError,KeyError,TypeError) as error:
                # No followup has been issued. Keep the original intent for
                # monitor reconciliation rather than offering a second dispatch.
                s.update(phase='attention',attention_reason='daily-order-preparation-failed-before-dispatch')
                s['events'].append({'type':'daily-order-preparation-stopped','dispatch_id':s['dispatch_id'],'error':str(error),'dispatch_outcome':'not-dispatched','at':d.stamp()});d.atomic(root/'state.json',s)
                raise
        elif result['workflow'] in (d.FLOWS[1],d.FLOWS[2]):
            if result['workflow']==d.FLOWS[1]:import complaint_execution_orchestration as role_execution_orchestration
            else:import role_execution_orchestration
            try:
                result=role_execution_orchestration.bind(root,s,result)
                d.atomic(root/'state.json',s)
            except (ValueError,OSError,KeyError,TypeError) as error:
                s.update(phase='attention',attention_reason='role-order-preparation-failed-before-dispatch')
                s['events'].append({'type':'role-order-preparation-stopped','dispatch_id':s['dispatch_id'],'error':str(error),'dispatch_outcome':'not-dispatched','at':d.stamp()});d.atomic(root/'state.json',s)
                raise
    return result

def morning(root,acceptance=None,now=None,project=PROJECT,dispatcher="codex",requested_day=None,collection_contract=None):
    with locked(root) as root:
        c=bind_config(root,acceptance);path=root/'state.json';day=today(now)
        if requested_day is not None:
            d.require(dispatcher=='local-subprocess-v1' and datetime.strptime(requested_day,'%Y-%m-%d').date().isoformat()==requested_day and requested_day<=day,'local-requested-day-invalid');day=requested_day
        if path.exists():
            s=d.read(path);d.migrate(s);d.require(s['day']<=day,'coordinator-clock-before-active-day')
            if s['day']<day and d.current(s).get('action')=='done':
                verify_config_acceptance(c,s)
                archive(root,s,c);s=d.initialize(day,c['acceptance'],collection_contract=collection_contract,accepted_proofs=c['acceptance_proofs']);d.atomic(path,s)
        else:s=d.initialize(day,c['acceptance'],collection_contract=collection_contract,accepted_proofs=c['acceptance_proofs']);d.atomic(path,s)
        d.require(s.get('collection_contract')==collection_contract,'coordinator-original-collection-contract')
        # Recover a crash after new state persisted but before coordinator pointer.
        c['active_day']=s['day'];d.atomic(root/'coordinator.json',c)
        result=dispatch_plan(root,s,project,dispatcher=dispatcher);return {**result,'active_day':s['day'],'requested_day':day,'timezone':'Asia/Shanghai','resuming_old_day':s['day']<day,'coordinator_executes_business':False}

def verify_role_completion(report,s):
    if d.current(s).get('workflow')==d.FLOWS[1] and 'pure_completion_contract' in d.read(report):
        import sys
        sys.path.insert(0,str(PROJECT/'packages/workshop-director'))
        from workshop_director import complaint_completion_report as pure
        d.require(Path(pure.__file__).resolve()==PROJECT/'packages/workshop-director/workshop_director/complaint_completion_report.py','coordinator-fixed-complaint-report-helper')
        return pure.verify_report(report,s)
    if d.current(s).get('workflow')==d.FLOWS[1]:import complaint_execution_orchestration as role_execution_orchestration
    else:import role_execution_orchestration
    return role_execution_orchestration.verify_completion(report,s)

def command(root,verb,*,dispatch_id=None,tool_receipt=None,journal=None,quiescent=False,repair_report=None,report=None,supervisor_report=None,authorization=None,timeout=300,project=PROJECT,dispatcher="codex"):
    with locked(root) as root:
        c=bind_config(root,None);s=d.read(root/'state.json');d.migrate(s);d.require(c['active_day']==s['day'],'coordinator-active-day-mismatch')
        if verb=='plan':return dispatch_plan(root,s,project,dispatcher=dispatcher)
        if verb=='ack':d.ack(s,dispatch_id,tool_receipt)
        elif verb=='heartbeat':d.heartbeat(s,dispatch_id,journal)
        elif verb=='reconcile-running-intent':
            repair=Path(repair_report or '').resolve();d.require(repair.is_file(),'running-reconciliation-repair-report-required');raw=repair.read_bytes();copy=root/'operation-receipts'/('running-reconciliation-'+sha(raw)+'.json');immutable(copy,raw);d.reconcile_running_intent(s,dispatch_id,copy)
        elif verb=='retry':d.retry(s,dispatch_id,quiescent,repair_report)
        elif verb=='finish-delivery':
            d.accept_unified_delivery(s,ref(Path(report)))
        elif verb=='collection-ready':
            d.require(s.get('collection_contract')=='three-flow-collection-ready-v1','ready-policy-required')
            d.accept_collection_ready(s,dispatch_id,ref(Path(report)))
        elif verb=='finish':
            if d.current(s).get('workflow')==d.FLOWS[0]:
                import daily_orchestration
                daily_orchestration.verify_completion(report,s)
            elif d.current(s).get('workflow') in (d.FLOWS[1],d.FLOWS[2]):
                verify_role_completion(report,s)
            d.finish(s,dispatch_id,report)
        elif verb=='reconcile-finish':
            if d.current(s).get('workflow')==d.FLOWS[0]:
                import daily_orchestration
                daily_orchestration.verify_completion(report,s)
            elif d.current(s).get('workflow') in (d.FLOWS[1],d.FLOWS[2]):
                verify_role_completion(report,s)
            d.reconcile_finish(s,dispatch_id,report,supervisor_report)
        elif verb=='abandon-day':
            # Supervised, evidence-bound closure of a day that will NOT be
            # delivered. Never a completion and never a delivery: the state
            # keeps business_delivered=False and the orphaned scope on record.
            source=Path(authorization or '').resolve()
            d.require(source.is_file() and not source.is_symlink(),'abandon-authorization-required')
            raw=source.read_bytes();auth=json.loads(raw)
            d.require(auth.get('kind')=='supervised-day-abandonment-v1','abandon-authorization-kind')
            d.require(auth.get('day')==s['day'] and auth.get('dispatch_id')==dispatch_id,'abandon-authorization-binding')
            d.require(s['phase'] in ('running','attention','dispatch-intent') and s.get('dispatch_id')==dispatch_id,'abandon-day-exact-stuck-dispatch-required')
            d.require(auth.get('business_delivered') is False,'abandon-authorization-not-a-delivery')
            d.require(auth.get('live_process_absent') is True and auth.get('live_evidence'),'abandon-live-process-evidence-required')
            ready=sorted(s.get('collection_ready_reports',{}))
            d.require(auth.get('orphaned_flows')==ready,'abandon-orphaned-scope-mismatch')
            receipt=root/'operation-receipts'/('abandon-day-'+sha(raw)+'.json');immutable(receipt,raw)
            s['abandoned']={'dispatch_id':dispatch_id,'receipt':ref(receipt),'authorization':ref(source),'at':d.stamp(),'business_delivered':False,'orphaned_flows':ready,'reason':auth.get('reason')}
            s['index']=len(d.ROLES);s['phase']='ready'
            s['events'].append({'type':'day-abandoned','dispatch_id':dispatch_id,'day':s['day'],'orphaned_flows':ready,'business_delivered':False,'abandon_receipt':s['abandoned']['receipt'],'authorization':s['abandoned']['authorization'],'at':d.stamp()})
        elif verb not in ('status','inspect'):raise ValueError('coordinator-command-invalid')
        result=d.inspect(s,timeout) if verb=='inspect' else s;d.atomic(root/'state.json',s)
        if verb=='finish-delivery':
            bundle=ref(Path(report));base=root/'operation-receipts/unified-delivery'/bundle['sha256'];statecopy=base/'state-after.json';immutable(statecopy,(root/'state.json').read_bytes());immutable(base/'receipt.json',json.dumps({'kind':'three-flow-coordinator-delivery-consumed-v1','bundle':bundle,'state':ref(statecopy)},ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n')
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(DEFAULT_ROOT));p.add_argument('--dispatcher',choices=('codex','local-subprocess-v1'),default='codex');sub=p.add_subparsers(dest='verb',required=True);m=sub.add_parser('morning');m.add_argument('--acceptance');m.add_argument('--day');sub.add_parser('plan');sub.add_parser('status');q=sub.add_parser('inspect');q.add_argument('--timeout',type=int,default=300)
    for verb in ('ack','heartbeat','retry','finish','finish-delivery','collection-ready','reconcile-finish','reconcile-running-intent','abandon-day'):
        q=sub.add_parser(verb);q.add_argument('--dispatch-id',required=True)
        if verb=='ack':q.add_argument('--tool-receipt',required=True)
        if verb=='heartbeat':q.add_argument('--journal',required=True)
        if verb=='retry':q.add_argument('--operator-quiescent',action='store_true');q.add_argument('--repair-report',required=True)
        if verb=='reconcile-running-intent':q.add_argument('--repair-report',required=True)
        if verb=='abandon-day':q.add_argument('--authorization',required=True)
        if verb in ('finish','finish-delivery','collection-ready','reconcile-finish'):q.add_argument('--report',required=True)
        if verb=='reconcile-finish':q.add_argument('--supervisor-report',required=True)
    a=p.parse_args();d.require(Path(a.root).resolve()==DEFAULT_ROOT.resolve(),'coordinator-fixed-global-root-required');result=morning(a.root,a.acceptance,dispatcher=a.dispatcher,requested_day=a.day) if a.verb=='morning' else command(a.root,a.verb,dispatch_id=getattr(a,'dispatch_id',None),tool_receipt=getattr(a,'tool_receipt',None),journal=getattr(a,'journal',None),quiescent=getattr(a,'operator_quiescent',False),repair_report=getattr(a,'repair_report',None),report=getattr(a,'report',None),supervisor_report=getattr(a,'supervisor_report',None),authorization=getattr(a,'authorization',None),timeout=getattr(a,'timeout',300),dispatcher=a.dispatcher);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as error:print(json.dumps({'ok':False,'error':str(error),'business_execution_allowed':False},ensure_ascii=False));raise SystemExit(2)
