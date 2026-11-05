#!/usr/bin/env python3
"""Durable dispatch ledger. Never imports or executes a business workflow."""
import argparse
import importlib.util
import fcntl
import hashlib
import json
import os
from pathlib import Path
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

ROLES = ('daily_stats_operator', 'complaint_operator', 'violation_operator')
FLOWS = ('daily-comment-stats', 'negative-review-complaints', 'violation-notifier')
TARGET = '测试群请忽略'
_progress_spec=importlib.util.spec_from_file_location('workshop_semantic_progress',Path(__file__).with_name('semantic_progress.py'))
progress=importlib.util.module_from_spec(_progress_spec);_progress_spec.loader.exec_module(progress)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def atomic(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')
        f.flush(); os.fsync(f.fileno())
    os.replace(temporary, path)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def scoped_completion(data):
    """Narrow original-scope retirement; not a general complete=False bypass."""
    if data.get('complete')is not False:return False
    require(data.get('kind')=='complaint-parent-director-completion-v1'and data.get('workflow')=='negative-review-complaints'and data.get('active_scope_complete')is True and data.get('original_scope_complete')is False,'scoped-completion-exact-report-kind')
    import execution_timing as timing
    def pinned(reference):
        path=Path(reference['path']);require(path.is_absolute()and path.resolve()==path and not path.is_symlink(),'scoped-completion-canonical-ref');raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==reference['sha256'],'scoped-completion-ref-changed');return json.loads(raw)
    policy=timing.company_policy(data['active_company_policy']);parent=pinned(data['verification_parent']);retirement=pinned(data['company_scope_reconciliation']);order=pinned(parent['order'])
    require(parent.get('company_scope_reconciliation')==data['company_scope_reconciliation']and retirement['kind']=='retired-company-original-task-scope-reconciliation-v1'and retirement['policy']==data['active_company_policy']and retirement['order']==parent['order'],'scoped-completion-parent-retirement-binding')
    require(data['active_companies']==policy['active']and data['retired_companies']==policy['retired'],'scoped-completion-exact-policy-partition')
    active=[i for i,c in enumerate(order['companies'])if {'company':c['company'],'groupid':c['groupid']}in policy['active']]
    retired=[i for i,c in enumerate(order['companies'])if any(c['company']==r['company']and c['groupid']==r['groupid']for r in policy['retired'])]
    require(active==retirement['active_indices']and retired==retirement['retired_indices']and sorted(active+retired)==list(range(len(order['companies'])))and not set(active)&set(retired),'scoped-completion-original-scope-partition')
    client=data['source_client_proof'];require(client.get('active_scope_complete')is True and client.get('original_scope_complete')is False and client.get('company_scope_reconciliation')==data['company_scope_reconciliation'],'scoped-completion-client-proof-binding')
    return True

def proof(path, flow):
    path = Path(path).resolve(); raw = path.read_bytes(); data = json.loads(raw)
    if data.get('kind')=='staged-unified-director-completion-v1':
        import delivery_commit
        delivery_commit.verify_report_value(data)
    require(data.get('workflow') == flow and data.get('live') is True and
            (data.get('complete') is True or scoped_completion(data)) and data.get('fixture') is not True and
            data.get('test_target') == TARGET and data.get('production_sent') is False and
            data.get('complaint_submitted') is False, 'real-completion-report-required')
    refs = data.get('evidence', [])
    require(bool(refs), 'business-evidence-required')
    for ref in refs:
        file = Path(ref['path'])
        require(file.is_absolute() and file.is_file() and
                hashlib.sha256(file.read_bytes()).hexdigest() == ref['sha256'], 'evidence-changed')
    require(path.read_bytes() == raw, 'completion-report-changed-during-verification')
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()}



def verify_current_configuration(s):
    """Runtime decisions use the current workflow configuration only."""
    require(s.get('version')==2 and date.fromisoformat(s['day']).isoformat()==s['day'],'current-director-schema')
    require(type(s.get('index'))is int and 0<=s['index']<=len(FLOWS),'current-workflow-index')
    require(s.get('complaint_submission_enabled')is False,'complaint-submission-disabled-required')
    require(s.get('collection_contract')in(None,'three-flow-collection-ready-v1'),'current-collection-contract')


def initialize(day, acceptance,collection_contract=None,accepted_proofs=None):
    require(collection_contract in(None,'three-flow-collection-ready-v1'),'collection-contract-invalid')
    require(date.fromisoformat(day).isoformat() == day, 'dispatch-day-invalid')
    require(set(acceptance) == set(FLOWS), 'three-acceptances-required')
    if accepted_proofs is None:verified = {flow: proof(acceptance[flow], flow) for flow in FLOWS}
    else:
        require(set(accepted_proofs)==set(FLOWS),'three-accepted-config-proofs-required')
        verified=accepted_proofs
    return {**({'collection_contract':collection_contract}if collection_contract else{}),'version': 2, 'day': day, 'test_target': TARGET, 'production_enabled': False,
            'complaint_submission_enabled': False, 'acceptance': verified, 'index': 0,
            'phase': 'ready', 'attempt': 0, 'events': [], 'updated_at': stamp()}


def migrate(s):
    if s.get('version', 1) >= 2:return
    s['version'] = 2
    if s.get('index') != len(ROLES) and s.get('phase') == 'ready':
        item = current(s)
        dispatch_id = f"{s['day']}:{item['workflow']}:{s['attempt']}"
        s.update(phase='dispatch-intent', dispatch_id=dispatch_id, dispatch_intent_at=stamp(), legacy_dispatch_unknown=True)
        s['events'].append({'type':'legacy-dispatch-unknown','id':dispatch_id,'at':stamp()})
    if s.get('phase') == 'running':
        s.setdefault('last_progress_at',s['last_heartbeat'])
    s['events'].append({'type':'migrated-v2','at':stamp()})


def abandon(s):
    """Supervised day abandonment. A day closed this way is NOT a delivery:
    it binds the exact stuck dispatch to immutable authorization and receipt
    files, and it must never claim business_delivered."""
    record = s.get('abandoned')
    require(isinstance(record, dict), 'abandoned-day-record-required')
    require(set(record) >= {'dispatch_id', 'receipt', 'authorization', 'at', 'business_delivered', 'orphaned_flows'}, 'abandoned-day-record-shape')
    require(record.get('business_delivered') is False, 'abandoned-day-not-a-delivery')
    require(record.get('dispatch_id') == s.get('dispatch_id'), 'abandoned-day-dispatch-binding')
    for key in ('receipt', 'authorization'):
        reference = record.get(key)
        require(isinstance(reference, dict) and set(reference) == {'path', 'sha256'}, 'abandoned-day-' + key + '-required')
        path = Path(reference['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'abandoned-day-' + key + '-missing')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == reference['sha256'], 'abandoned-day-' + key + '-changed')
    return True


def current(s):
    require(s['test_target'] == TARGET and s['production_enabled'] is False and
            s['complaint_submission_enabled'] is False, 'dispatch-policy-conflict')
    require(type(s.get('index')) is int and 0 <= s['index'] <= len(ROLES), 'dispatch-index-invalid')
    if s.get('abandoned'):
        require(abandon(s), 'abandoned-day-invalid')
        return {'action': 'done', 'day': s['day'], 'abandoned': True,
                'abandon_receipt': s['abandoned']['receipt'], 'business_delivered': False}
    if s['index'] == len(ROLES):
        if s.get('collection_contract')=='three-flow-collection-ready-v1':
            if s.get('deferred_download',{}).get('status')=='collecting-other-two':
                require(set(s.get('collection_ready_reports',{}))==set(FLOWS[1:]),'deferred-exact-two-ready-required')
                return {'action':'await-deferred-daily','day':s['day'],'complete':False}
            require(set(s.get('collection_ready_reports',{}))==set(FLOWS),'three-collection-ready-reports-required')
            if s.get('delivery_complete')is True:return {'action':'done','day':s['day']}
            return {'action':'deliver-ready-batch','day':s['day'],'ready_reports':s['collection_ready_reports'],'complete':False}
        return {'action': 'done', 'day': s['day']}
    return {'role': ROLES[s['index']], 'workflow': FLOWS[s['index']]}


def plan(s, dispatcher="codex"):
    require(dispatcher in ("codex","local-subprocess-v1"),"dispatcher-version-invalid")
    item = current(s)
    if item.get('action') in ('done','deliver-ready-batch','await-deferred-daily'):
        return item
    if s['phase'] in ('running', 'attention', 'dispatch-intent'):
        return {**item, 'action': 'inspect-original-run', 'phase': s['phase'],
                'last_heartbeat': s.get('last_heartbeat'), 'dispatch_id': s.get('dispatch_id')}
    require(s['phase'] == 'ready', 'dispatch-phase-invalid')
    verify_current_configuration(s)
    previous_id=s.get('dispatch_id')
    fields=('journal','journal_sha256','journal_dispatch_id','last_semantic_observation','semantic_progress_error')
    fresh_role=bool(previous_id and not previous_id.startswith(s['day']+':'+item['workflow']+':'))
    if fresh_role:
        ready_transition=s.get('collection_contract')=='three-flow-collection-ready-v1'and any(e.get('type')=='collection-ready'and e.get('dispatch_id')==previous_id for e in s.get('events',[]))
        defer=s.get('deferred_download',{})
        deferred_transition=bool(s.get('collection_contract')=='three-flow-collection-ready-v1'and s['index']==1 and defer.get('kind')=='same-round-expired-download-defer-v1'and defer.get('status')=='collecting-other-two'and previous_id.startswith(s['day']+':'+FLOWS[0]+':')and any(e.get('type')=='download-deferred'and e.get('dispatch_id')==previous_id and e.get('session')==defer.get('session')for e in s.get('events',[])))
        require(ready_transition or deferred_transition or any(e.get('type')=='completed' and e.get('dispatch_id')==previous_id for e in s.get('events',[])),'new-role-monitor-reset-requires-completed-previous-dispatch')
        previous_monitor={k:s[k] for k in fields if k in s}
        s['events'].append({'type':'role-monitor-transition','previous_dispatch_id':previous_id,'next_role':item['role'],'previous_monitor':previous_monitor,'at':stamp()})
        for key in fields:s.pop(key,None)
        s['journal_binding_status']='awaiting-first-journal'
    elif not previous_id:
        require(not any(k in s for k in fields),'initial-monitor-binding-without-dispatch')
        s['journal_binding_status']='awaiting-first-journal'
    dispatch_id = f"{s['day']}:{item['workflow']}:{s['attempt']}"
    s.update(phase='dispatch-intent', dispatch_id=dispatch_id, dispatch_intent_at=stamp())
    if dispatcher=='local-subprocess-v1':s['dispatcher_protocol']=dispatcher
    else:s.pop('dispatcher_protocol',None)
    s['events'].append({'type': 'dispatch-intent', 'id': dispatch_id, 'at': s['dispatch_intent_at']})
    return {**item, 'action': 'dispatch', 'tool': 'local-subprocess-v1' if dispatcher=='local-subprocess-v1' else 'collaboration.followup_task',
            **({'dispatcher_protocol':dispatcher} if dispatcher=='local-subprocess-v1' else {}),
            'dispatch_id': dispatch_id,
            'message': f"执行 {item['workflow']}。调度日 {s['day']}，派工 {dispatch_id}。"
                       f"按本岗独立进度补做到调度日{s['day']}不含，优先续原未完成工单。最终仅发{TARGET}；"
                       "不发生产、不真实提交投诉。未知导出/发送结果只复查原意图，不重发。"
                       "独占Chrome和企业微信，完成或异常立即报告监理并记录业务证据。"}


def ack(s, dispatch_id, receipt):
    current(s)
    require((s['phase'] == 'dispatch-intent' or s['phase'] == 'attention' and s.get('attention_reason') == 'dispatch-ack-unknown') and s.get('dispatch_id') == dispatch_id, 'dispatch-conflict')
    require(bool(receipt.strip()), 'dispatch-tool-receipt-required')
    if s.get('dispatcher_protocol')=='local-subprocess-v1':
        import local_dispatch_receipt
        local_dispatch_receipt.verify(receipt,s)
    now = stamp()
    s.update(phase='running', dispatch_id=dispatch_id, dispatched_at=now, last_heartbeat=now, last_progress_at=now, tool_receipt=receipt)
    s.pop('attention_reason', None)
    s['events'].append({'type': 'dispatched', 'id': dispatch_id, 'at': stamp()})


def heartbeat(s, dispatch_id, journal, now=None):
    item=current(s)
    require(s['phase'] in ('running','attention') and s.get('dispatch_id') == dispatch_id, 'lease-conflict')
    file = Path(journal).resolve(); require(file.is_file(), 'journal-required')
    at=now or datetime.now(timezone.utc);require(at.utcoffset() is not None,'heartbeat-aware-time-required')
    observed=at.isoformat();raw=file.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    s.update(last_heartbeat=observed,journal=str(file),journal_sha256=digest,journal_dispatch_id=dispatch_id,journal_binding_status='bound-current-dispatch')
    if s['phase']=='attention':return  # Sticky monitor hold; liveness cannot release it.
    try:
        extracted=progress.extract(json.loads(raw),item['role'],journal_path=file)
        require(file.read_bytes()==raw,'semantic-journal-changed-during-read')
        old_progress_at=s.get('last_progress_at',s['dispatch_intent_at'])
        closure=progress.fresh_completed_evidence(file,extracted['schema'],role=item['role'],dispatch_started_at=s['dispatch_intent_at'],now=at)
        require(file.read_bytes()==raw,'semantic-journal-changed-during-completion-proof')
        known=None
        if closure is not None:
            require(isinstance(closure,dict) and isinstance(closure.get('dedup_key'),str) and isinstance(closure.get('business_binding'),dict) and closure.get('schema')==extracted['schema'],'semantic-fresh-closure-contract-invalid')
            completed=datetime.fromisoformat(closure['completed_at']);created=datetime.fromisoformat(closure['created_at']);begun=datetime.fromisoformat(s['dispatch_intent_at'])
            require(all(value.utcoffset() is not None for value in (completed,created,begun)) and begun<=created<=completed<=at,'semantic-fresh-closure-time-invalid')
            registry=s.get('verified_business_closures',{}).get(dispatch_id,{})
            known=registry.get(closure['dedup_key'])
            if known is not None:require(known['business_binding']==closure['business_binding'],'semantic-fresh-closure-business-binding-changed')
        by_dispatch=s.setdefault('semantic_progress',{})
        history=by_dispatch.setdefault(dispatch_id,{})
        previous=history.get(str(file))
        if previous is None:
            # A fresh path/work-order pins a baseline, including old completed
            # receipts; switching among old logs never refreshes progress time.
            history[str(file)]={**extracted,'first_observed_at':observed}
        else:
            require(previous['schema']==extracted['schema'] and previous['binding']==extracted['binding'],'semantic-original-work-order-changed')
            old,new=previous['tokens'],extracted['tokens']
            require(all(new.get(k)==v for k,v in old.items()) and all(new.get(k)==v for k,v in previous.get('pending_token_floor',{}).items()),'semantic-completed-progress-regressed-or-rewritten')
            if extracted['schema']=='operator-v1':
                prefix=previous.get('confirmed_call_prefix',[]);fresh=extracted.get('confirmed_call_prefix',[])
                require(fresh[:len(prefix)]==prefix,'semantic-confirmed-call-prefix-rewritten')
                previous['confirmed_call_prefix']=fresh
            if extracted.get('pending_operator_intent'):
                previous['pending_token_floor']=new
            else:
                if set(new)-set(old):
                    s['last_progress_at']=observed
                    s['events'].append({'type':'semantic-progress','dispatch_id':dispatch_id,'at':observed,'journal':str(file),'completed':sorted(set(new)-set(old))})
                previous['tokens']=new;previous.pop('pending_token_floor',None)
        if closure is not None:
            # Completion may be first observed after the operation closes.
            # Count its actual proven closure once across all journal paths.
            if known is not None:
                s['last_progress_at']=old_progress_at
            else:
                s.setdefault('verified_business_closures',{}).setdefault(dispatch_id,{})[closure['dedup_key']]=closure
                s['last_progress_at']=max(datetime.fromisoformat(old_progress_at),completed).isoformat()
                s['events'].append({'type':'semantic-verified-business-closure','dispatch_id':dispatch_id,'at':observed,'journal':str(file),'dedup_key':closure['dedup_key'],'completed_at':closure['completed_at'],'business_binding':closure['business_binding'],'read_time_is_not_progress_time':True})
        s['last_semantic_observation']={'schema':extracted['schema'],'journal':str(file),'completed_count':len(extracted['tokens']),'at':observed}
    except (ValueError,KeyError,TypeError,OSError,AttributeError,IndexError) as error:
        s.update(phase='attention',attention_reason='semantic-progress-unverified',semantic_progress_error=str(error))
        s['events'].append({'type':'semantic-progress-attention','dispatch_id':dispatch_id,'at':observed,'journal':str(file),'error':str(error),'automatic_replay_allowed':False})


def supervised_pause_start(s,dispatch_id,error):
    boundary=-1
    for i,event in enumerate(s['events']):
        if event.get('dispatch_id')==dispatch_id and event.get('type') in ('supervisor-known-switch-read-reconciled','supervisor-known-record-page-reconciled','supervisor-known-sender-preinput-reconciled','supervisor-running-intent-reconciled'):boundary=i
    candidates=[event for event in s['events'][boundary+1:] if event.get('type')=='semantic-progress-attention' and event.get('dispatch_id')==dispatch_id and event.get('error')==error]
    require(bool(candidates),'read-reconciliation-original-attention-event-required')
    event=candidates[0]
    return {'start':event['at'],'attention_event_sha256':progress.digest(event)}


def active_age(s,start,at):
    """Only supervisor-consumed quiescent repairs pause the watchdog, not timing."""
    beginning=datetime.fromisoformat(start);require(beginning.utcoffset() is not None and at.utcoffset() is not None and beginning<=at,'clock-before-heartbeat');intervals=[]
    for event in s.get('events',[]):
        if event.get('type') not in ('supervisor-known-switch-read-reconciled','supervisor-known-record-page-reconciled','supervisor-known-sender-preinput-reconciled') or event.get('dispatch_id')!=s.get('dispatch_id'):continue
        pause=event.get('supervised_pause');require(isinstance(pause,dict),'supervised-pause-proof-required')
        report=progress.reference(event['repair_report'])
        require(report==event.get('repair_report_body') and report.get('kind')=={'supervisor-known-switch-read-reconciled':'supervisor-known-switch-read-reconciliation-v1','supervisor-known-record-page-reconciled':'supervisor-known-record-page-reconciliation-v1','supervisor-known-sender-preinput-reconciled':'supervisor-known-sender-preinput-reconciliation-v1'}[event['type']] and report.get('dispatch_id')==s['dispatch_id'] and report.get('day')==s['day'] and report.get('role')==current(s)['role'] and all(report.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')),'supervised-pause-report-invalid')
        attention=[e for e in s['events'] if e.get('type')=='semantic-progress-attention' and e.get('dispatch_id')==s['dispatch_id'] and e.get('error')=='semantic-terminal-error' and progress.digest(e)==pause.get('attention_event_sha256')]
        require(len(attention)==1 and attention[0].get('at')==pause.get('start') and pause.get('end')==event.get('at'),'supervised-pause-attention-invalid')
        left=datetime.fromisoformat(pause['start']);right=datetime.fromisoformat(pause['end'])
        require(left.utcoffset() is not None and right.utcoffset() is not None and datetime.fromisoformat(s['dispatch_intent_at'])<=left<=right<=at,'supervised-pause-time-invalid')
        if right>beginning:intervals.append((max(beginning,left),right))
    merged=[]
    for left,right in sorted(intervals):
        if merged and left<=merged[-1][1]:merged[-1]=(merged[-1][0],max(right,merged[-1][1]))
        else:merged.append((left,right))
    return (at-beginning).total_seconds()-sum((right-left).total_seconds() for left,right in merged)


def reconcile_known_switch_read(s,dispatch_id,repair_report,now=None):
    """Consume a verified same-order read repair; never dispatch or run input."""
    item=current(s)
    require(s['phase']=='attention' and s.get('dispatch_id')==dispatch_id and s.get('attention_reason')=='semantic-progress-unverified' and s.get('semantic_progress_error')=='semantic-terminal-error','read-reconciliation-exact-attention-required')
    require(s.get('dispatched_at') and s.get('tool_receipt') and any(e.get('type')=='dispatched' and e.get('id')==dispatch_id for e in s.get('events',[])),'read-reconciliation-original-ack-required')
    path=Path(repair_report or '').resolve();raw=path.read_bytes();r=json.loads(raw)
    contracts={'supervisor-known-switch-read-reconciliation-v1':('douyin-laike-operator','switch_read_recovery','switch_read_recovery','tab-context-changed-during-read','supervisor-known-switch-read-reconciled','operator-v1'),'supervisor-known-record-page-reconciliation-v1':('douyin-laike-operator','export_record_page_recovery','record_page_recovery','record-pagination-incomplete','supervisor-known-record-page-reconciled','operator-v1'),'supervisor-known-sender-preinput-reconciliation-v1':('wecom-messenger','sender_preinput_recovery','sender_preinput_recovery','ui-tree-incomplete','supervisor-known-sender-preinput-reconciled','wecom-v1')}
    require(r.get('kind') in contracts,'read-reconciliation-known-kind-required')
    skill_name,module_name,proof_field,error_code,event_type,expected_schema=contracts[r['kind']]
    require(r.get('dispatch_id')==dispatch_id and r.get('day')==s['day'] and r.get('role')==item['role'],'read-reconciliation-scope-required')
    require(all(r.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')),'read-reconciliation-quiescence-required')
    source=r.get('journal');document=progress.reference(source);require(source['path']==s.get('journal'),'read-reconciliation-original-journal-required')
    previous=s.get('semantic_progress',{}).get(dispatch_id,{}).get(source['path'])
    initial_sender_baseline=previous is None and expected_schema=='wecom-v1'
    require(initial_sender_baseline or previous and previous['schema']==expected_schema and previous['binding']==r.get('original_binding'),'read-reconciliation-original-binding-required')
    import sys,importlib
    directory=Path(__file__).resolve().parents[2]/skill_name/'scripts';old_path=list(sys.path)
    try:
        sys.path.insert(0,str(directory));verifier=importlib.import_module(module_name)
        require(Path(verifier.__file__).resolve()==directory/(module_name+'.py'),'read-reconciliation-verifier-origin-conflict')
        verified=verifier.verify_recovered(document,document.get(proof_field))
    finally:sys.path[:]=old_path
    require(verified.get('original_error',{}).get('code')==verified.get('original_error',{}).get('message')==error_code and r.get('worker_recovery')==verified['proof'] and r.get('original_journal')==verified['original_journal'],'read-reconciliation-worker-proof-required')
    original=progress.reference(verified['original_journal'])
    if expected_schema=='operator-v1':
        require(document['calls']==original['calls'] and all(c.get('state')=='confirmed' for c in document['calls']),'read-reconciliation-original-calls-required')
    else:
        require(document.get('job')==original.get('job') and document.get('fingerprint')==original.get('fingerprint') and document.get('status')=='running' and document.get('phase')=='locate' and document.get('sent') is False and document.get('ui_confirmed') is False,'read-reconciliation-original-sender-required')
    fresh=progress.extract(document,item['role'],journal_path=source['path'])
    if initial_sender_baseline:
        require(fresh['schema']=='wecom-v1' and fresh['binding']==r.get('original_binding') and any(e.get('type')=='semantic-progress-attention' and e.get('dispatch_id')==dispatch_id and e.get('journal')==source['path'] and e.get('error')=='semantic-terminal-error' for e in s['events']),'read-reconciliation-original-sender-attention-required')
        previous={'schema':fresh['schema'],'binding':fresh['binding'],'tokens':fresh['tokens']}
    require(fresh['schema']==previous['schema'] and fresh['binding']==previous['binding'],'read-reconciliation-binding-changed')
    require(all(fresh['tokens'].get(k)==v for k,v in previous['tokens'].items()) and all(fresh['tokens'].get(k)==v for k,v in previous.get('pending_token_floor',{}).items()),'read-reconciliation-token-regression')
    prefix=previous.get('confirmed_call_prefix',[]);require(fresh.get('confirmed_call_prefix',[])[:len(prefix)]==prefix,'read-reconciliation-call-prefix-regression')
    at=now or datetime.now(timezone.utc);proof=progress.reference(verified['proof']);observed=datetime.fromisoformat(proof['at'].replace('Z','+00:00'))
    require(at.utcoffset() is not None and observed.utcoffset() is not None and datetime.fromisoformat(s['dispatch_intent_at'])<=observed<=at,'read-reconciliation-time-invalid')
    checksum=hashlib.sha256(raw).hexdigest();require(not any(e.get('type')==event_type and e.get('repair_report',{}).get('sha256')==checksum for e in s['events']),'read-reconciliation-already-consumed')
    require(path.read_bytes()==raw and hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256'],'read-reconciliation-evidence-changed')
    pause=supervised_pause_start(s,dispatch_id,'semantic-terminal-error');pause['end']=at.isoformat()
    require(datetime.fromisoformat(s['dispatch_intent_at'])<=datetime.fromisoformat(pause['start'])<=at,'supervised-pause-time-invalid')
    old={k:s.get(k) for k in ('attention_reason','semantic_progress_error','last_heartbeat','last_progress_at','journal_sha256')}
    s.update(phase='running',last_heartbeat=at.isoformat(),journal_sha256=source['sha256'])
    if expected_schema=='operator-v1':previous['confirmed_call_prefix']=fresh['confirmed_call_prefix']
    if initial_sender_baseline:s.setdefault('semantic_progress',{}).setdefault(dispatch_id,{})[source['path']]=previous
    # No checkpoint was completed: keep last_progress_at and prior token set.
    s['events'].append({'type':event_type,'dispatch_id':dispatch_id,'at':at.isoformat(),'supervised_pause':pause,'repair_report':{'path':str(path),'sha256':checksum},'repair_report_body':r,'original_attention':old,'worker_recovery':verified['proof'],'original_journal':verified['original_journal'],'parent_clock_changed':False,'new_dispatch_created':False,'business_replayed':False,'automatic_followup':False,'initial_sender_baseline_without_progress_renewal':initial_sender_baseline})
    return s


def reconcile_running_intent(s,dispatch_id,repair_report,now=None):
    """Pure same-lease recovery from the specific in-flight-unknown false positive.
    Does not follow up, replay input, alter operator files, or reset parent clocks.
    """
    if s.get('semantic_progress_error')=='semantic-terminal-error':return reconcile_known_switch_read(s,dispatch_id,repair_report,now)
    item=current(s);require(s['phase']=='attention' and s.get('dispatch_id')==dispatch_id and s.get('attention_reason')=='semantic-progress-unverified' and s.get('semantic_progress_error')=='semantic-unknown-intent','running-reconciliation-exact-attention-required')
    require(s.get('dispatched_at') and s.get('tool_receipt') and any(e.get('type')=='dispatched' and e.get('id')==dispatch_id for e in s.get('events',[])),'running-reconciliation-original-ack-required')
    path=Path(repair_report or '').resolve();require(path.is_file(),'running-reconciliation-repair-report-required');raw=path.read_bytes();r=json.loads(raw)
    require(r.get('kind')=='supervisor-original-running-intent-reconciliation-v1' and r.get('dispatch_id')==dispatch_id and r.get('day')==s['day'] and r.get('role')==item['role'],'running-reconciliation-scope-required')
    require(all(r.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')),'running-reconciliation-quiescence-required')
    source=r.get('journal');document=progress.reference(source);require(source['path']==s.get('journal'),'running-reconciliation-original-journal-required');previous=s.get('semantic_progress',{}).get(dispatch_id,{}).get(source['path']);require(previous and previous['schema']=='operator-v1' and previous['binding']==r.get('original_binding'),'running-reconciliation-original-binding-required')
    require(document.get('version')==1 and document.get('backend')=='local-dom-bridge' and document.get('state')=='complete' and document.get('phase')=='done' and not any(document.get(k) for k in ('error','last_error','hold','settling_exhausted','waiting_for')),'running-reconciliation-complete-operator-required')
    require(document.get('exportPending') is False and document.get('downloadPending') is False and document.get('calls') and all(c.get('state')=='confirmed' for c in document['calls']),'running-reconciliation-all-intents-confirmed-required')
    extracted=progress.extract(document,item['role'],journal_path=source['path']);require(extracted['schema']==previous['schema'] and extracted['binding']==previous['binding'],'running-reconciliation-original-binding-changed');fresh=extracted['tokens'];require(all(fresh.get(k)==v for k,v in previous['tokens'].items()) and all(fresh.get(k)==v for k,v in previous.get('pending_token_floor',{}).items()),'running-reconciliation-completed-token-regression')
    prefix=previous.get('confirmed_call_prefix',[]);require(extracted.get('confirmed_call_prefix',[])[:len(prefix)]==prefix,'running-reconciliation-confirmed-prefix-regression')
    cps=[c for c in document['checkpoints'] if c.get('stage')=='download-complete'];require(len(cps)==1,'running-reconciliation-unique-download-checkpoint-required');cp=cps[0];result=document.get('result',{});receipt=document.get('download_receipt',{});download={'path':cp.get('path'),'sha256':cp.get('sha256')};progress.reference(download)
    require(result.get('source')==download['path'] and result.get('src_sha256')==download['sha256'] and result.get('download_verified') is True and all(result.get(k)==document.get(k) for k in ('work_order_id','company','groupid','date_range')),'running-reconciliation-download-result-binding-required')
    require(receipt==result.get('download_receipt') and receipt.get('state')=='complete' and receipt.get('exists') is True and receipt.get('path')==download['path'] and type(receipt.get('downloadId')) is int and receipt['downloadId']>0 and receipt.get('bytesReceived')==receipt.get('totalBytes')==Path(download['path']).stat().st_size>0,'running-reconciliation-download-receipt-required')
    require(cp.get('ticket')==document.get('download_ticket',{}).get('ticket')==result.get('download_ticket',{}).get('ticket') and cp.get('ticket'),'running-reconciliation-original-download-ticket-required')
    at=now or datetime.now(timezone.utc);require(at.utcoffset() is not None,'running-reconciliation-aware-time-required')
    completed=datetime.fromisoformat(str(cp.get('at','')).replace('Z','+00:00'));require(completed.utcoffset() is not None and datetime.fromisoformat(s['dispatch_intent_at'])<=completed<=at,'running-reconciliation-download-time-invalid')
    checksum=hashlib.sha256(raw).hexdigest();require(not any(e.get('type')=='supervisor-running-intent-reconciled' and e.get('repair_report',{}).get('sha256')==checksum for e in s['events']),'running-reconciliation-already-consumed')
    require(path.read_bytes()==raw and hashlib.sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256'],'running-reconciliation-evidence-changed')
    original={k:s.get(k) for k in ('attention_reason','semantic_progress_error','last_heartbeat','last_progress_at','journal_sha256')};new=sorted(set(fresh)-set(previous['tokens']))
    s.update(phase='running',last_heartbeat=at.isoformat(),journal_sha256=source['sha256']);previous.update(tokens=fresh,confirmed_call_prefix=extracted.get('confirmed_call_prefix',[]));previous.pop('pending_token_floor',None)
    if new:
        s['last_progress_at']=at.isoformat();s['events'].append({'type':'semantic-progress','dispatch_id':dispatch_id,'at':at.isoformat(),'journal':source['path'],'completed':new,'basis':'verified-original-operator-completion-after-falsepositive'})
    s['events'].append({'type':'supervisor-running-intent-reconciled','dispatch_id':dispatch_id,'at':at.isoformat(),'repair_report':{'path':str(path),'sha256':checksum},'repair_report_body':r,'original_attention':original,'journal':source,'verified_download':download,'new_completed_tokens':new,'parent_clock_changed':False,'new_dispatch_created':False,'business_replayed':False,'diagnostics_preserved':True})
    return s

def inspect(s, timeout=300, now=None):
    require(timeout >= 60, 'timeout-too-short')
    now = now or datetime.now(timezone.utc)
    if s['phase'] == 'dispatch-intent':
        age = (now - datetime.fromisoformat(s['dispatch_intent_at'])).total_seconds()
        require(age >= 0, 'clock-before-dispatch-intent')
        if age >= timeout:
            s.update(phase='attention', attention_reason='dispatch-ack-unknown')
            s['events'].append({'type':'dispatch-ack-unknown','dispatch_id':s['dispatch_id'],'at':stamp()})
            return {**current(s),'action':'supervisor-reconcile-dispatch','dispatch_id':s['dispatch_id'],'automatic_replay_allowed':False,'business_execution_allowed':False}
        return plan(s)
    if s['phase'] != 'running':
        item = current(s)
        return {**item, 'action':'await-plan'} if s['phase'] == 'ready' and item.get('action') != 'done' else item if item.get('action') == 'done' else plan(s)
    age = active_age(s,s['last_heartbeat'],now)
    progress_age = active_age(s,s.get('last_progress_at',s['last_heartbeat']),now)
    require(age >= 0 and progress_age >= 0, 'clock-before-heartbeat')
    if age >= timeout or progress_age >= timeout:
        s.update(phase='attention', attention_reason='journal-no-progress' if progress_age >= timeout else 'heartbeat-timeout')
        s['events'].append({'type': 'stalled', 'dispatch_id': s['dispatch_id'], 'at': stamp()})
        return {**current(s), 'action': 'supervisor-repair', 'idle_seconds': age, 'journal_idle_seconds': progress_age,
                'reason': 'journal-no-progress' if progress_age >= timeout else 'heartbeat-timeout',
                'business_execution_allowed': False, 'automatic_replay_allowed': False}
    return {**current(s), 'action': 'wait', 'idle_seconds': age, 'journal_idle_seconds': progress_age}


def retry(s, dispatch_id, quiescent, repair_report):
    item=current(s)
    require(s['phase'] in ('running', 'attention', 'dispatch-intent') and s.get('dispatch_id') == dispatch_id, 'lease-conflict')
    require(quiescent is True, 'operator-quiescence-required')
    file = Path(repair_report).resolve(); require(file.is_file(), 'repair-report-required')
    raw=file.read_bytes();report=json.loads(raw)
    require(report.get('dispatch_id')==dispatch_id and report.get('day')==s['day'] and report.get('role')==item['role'] and
            all(report.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')), 'repair-dispatch-scope-and-quiescence-required')
    if s['phase'] == 'dispatch-intent' or s.get('attention_reason') == 'dispatch-ack-unknown':
        require(report.get('dispatch_outcome') in ('not-dispatched', 'dispatched-and-stopped'),'unknown-dispatch-reconciliation-required')
    require(file.read_bytes()==raw,'repair-report-changed-during-verification')
    s['events'].append({'type': 'repair-redispatch', 'previous': dispatch_id, 'report': str(file),
                        'sha256': hashlib.sha256(raw).hexdigest(), 'at': stamp()})
    s.update(phase='ready', attempt=s['attempt'] + 1)
    s.pop('attention_reason', None)


def completion_evidence(s, dispatch_id, report):
    item=current(s);evidence=proof(report,item['workflow']);data=read(report)
    require(hashlib.sha256(Path(report).read_bytes()).hexdigest()==evidence['sha256'],'completion-report-changed-during-verification')
    require(data.get('dispatch_id')==dispatch_id and data.get('day')==s['day'] and data.get('role')==item['role'],'completion-dispatch-scope-required')
    completed=datetime.fromisoformat(str(data.get('completed_at','')).replace('Z','+00:00'))
    started=datetime.fromisoformat(s.get('dispatch_intent_at',s.get('dispatched_at',s.get('last_heartbeat',''))))
    require(completed.utcoffset() is not None and started.utcoffset() is not None and started<=completed<=datetime.now(timezone.utc),'completion-time-outside-dispatch')
    require(not any(e.get('type')=='completed' and e.get('report',{}).get('sha256')==evidence['sha256'] for e in s['events']),'completion-report-already-consumed')
    return evidence,data

def consume_completion(s,dispatch_id,evidence):
    raw=Path(evidence['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==evidence['sha256'],'completion-consumption-report-changed');report=json.loads(raw)
    if report.get('complete')is False:
        require(scoped_completion(report),'scoped-completion-not-verified');s['events'].append({'type':'scope-retired-completion','dispatch_id':dispatch_id,'report':evidence,'policy':report['active_company_policy'],'active_scope_complete':True,'original_scope_complete':False,'retired_companies':report['retired_companies'],'at':stamp()})
    s['events'].append({'type':'completed','dispatch_id':dispatch_id,'report':evidence,'at':stamp()})
    s.update(index=s['index']+1,phase='ready',attempt=0)

def accept_collection_ready(s,dispatch_id,report_ref):
    """Coordinator invokes only after the workflow's deep ready validator.
    No completion event, cursor operation, or claim of client confirmation.
    """
    require(s.get('collection_contract')=='three-flow-collection-ready-v1'and s.get('phase')=='running'and s.get('dispatch_id')==dispatch_id,'ready-original-running-dispatch')
    item=current(s)
    if item['workflow']=='daily-comment-stats':
        import daily_orchestration
        daily_orchestration.verify_collection_ready_report(report_ref['path'],s)
    else:
        import collection_ready
        ready_value=collection_ready.verify_current(report_ref,s)
        require(ready_value['workflow']==item['workflow'],'ready-provider-flow-mismatch')
    raw=Path(report_ref['path']).read_bytes();require(hashlib.sha256(raw).hexdigest()==report_ref['sha256'],'ready-report-changed');data=json.loads(raw)
    kinds={'daily-comment-stats':'daily-director-collection-ready-report-v1','negative-review-complaints':'complaint-director-collection-ready-report-v1','violation-notifier':'violation-director-collection-ready-report-v1'}
    require(data.get('kind')==kinds[item['workflow']]and data.get('workflow')==item['workflow']and data.get('dispatch_id')==dispatch_id and data.get('day')==s['day']and data.get('collection_contract')==s['collection_contract'],'ready-dispatch-scope')
    require(data.get('collection_ready')is True and data.get('complete')is False and data.get('delivery_complete')is False and data.get('cursor_advanced')is False,'ready-is-not-completion')
    ready=s.setdefault('collection_ready_reports',{});require(item['workflow']not in ready,'ready-report-already-consumed')
    ready[item['workflow']]=report_ref;s['events'].append({'type':'collection-ready','dispatch_id':dispatch_id,'workflow':item['workflow'],'report':report_ref,'at':stamp()});s.update(index=(3 if s.get('deferred_download',{}).get('status')=='restored-await-original-download'and item['workflow']==FLOWS[0]and set(ready)==set(FLOWS) else s['index']+1),phase='ready',attempt=0)

def finish(s, dispatch_id, report):
    require(s['phase']=='running' and s.get('dispatch_id')==dispatch_id,'lease-conflict')
    evidence,_=completion_evidence(s,dispatch_id,report)
    consume_completion(s,dispatch_id,evidence)

def original_work_order_identity(raw):
    # Read only stable local identity fields. This is NOT a worker progress token
    # and cannot release a hold without the monitor's separately verified report.
    if isinstance(raw.get('job'),dict):
        job=raw['job'];require(hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==raw.get('fingerprint'),'completion-original-job-changed')
        return {'fingerprint':raw['fingerprint'],'key':job['key']}
    if raw.get('work_order_id') and raw.get('fingerprint'):
        return {k:raw[k] for k in ('work_order_id','fingerprint')}
    if raw.get('fingerprint') and type(raw.get('tab_id')) is int:
        return {k:raw[k] for k in ('fingerprint','tab_id')}
    if isinstance(raw.get('manifest'),dict) and raw['manifest'].get('review_key'):
        return {'manifest':raw['manifest']}
    raise ValueError('completion-original-work-order-schema-required')

def reconcile_finish(s,dispatch_id,report,supervisor_report):
    require(s['phase']=='attention' and s.get('dispatch_id')==dispatch_id,'completion-reconciliation-attention-required')
    require(s.get('attention_reason')!='dispatch-ack-unknown' and s.get('dispatched_at') and s.get('tool_receipt') and
            any(e.get('type')=='dispatched' and e.get('id')==dispatch_id for e in s['events']),'completion-reconciliation-original-ack-required')
    item=current(s);evidence,data=completion_evidence(s,dispatch_id,report)
    path=Path(supervisor_report or '').resolve();require(path.is_file(),'supervisor-completion-reconciliation-required');raw=path.read_bytes();r=json.loads(raw)
    require(r.get('kind')=='supervisor-original-dispatch-completion-reconciliation-v1' and r.get('dispatch_id')==dispatch_id and r.get('day')==s['day'] and r.get('role')==item['role'],'supervisor-completion-scope-required')
    require(all(r.get(k) is True for k in ('source_completion_verified','operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')),'supervisor-completion-verification-and-quiescence-required')
    require(r.get('completion_report')==evidence,'supervisor-completion-report-binding-required')
    order=r.get('original_work_order',{});source=order.get('journal');document=progress.reference(source);identity=original_work_order_identity(document)
    covered=source in data.get('evidence',[]) or any(r.get('sha256')==source['sha256'] and progress.reference(r)==document for r in data.get('evidence',[]))
    require(order.get('identity')==identity and covered,'supervisor-original-work-order-binding-required')
    if s.get('journal'):require(source['path']==s['journal'],'supervisor-original-journal-path-conflict')
    previous=s.get('semantic_progress',{}).get(dispatch_id,{}).get(source['path'])
    if previous:require(all(previous['binding'].get(k)==v for k,v in identity.items()),'supervisor-original-work-order-changed')
    require(path.read_bytes()==raw,'supervisor-completion-report-changed-during-verification')
    s['events'].append({'type':'supervisor-original-completion-reconciled','dispatch_id':dispatch_id,'at':stamp(),'previous_attention_reason':s.get('attention_reason'),'supervisor_report':{'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()},'original_work_order':order,'completion_report':evidence,'new_dispatch_created':False,'business_replayed':False})
    consume_completion(s,dispatch_id,evidence)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--acceptance', required=True)
    init.add_argument('--day', default=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat())
    sub.add_parser('plan'); sub.add_parser('status')
    check = sub.add_parser('inspect'); check.add_argument('--timeout', type=int, default=300)
    for verb in ('ack', 'heartbeat', 'retry', 'finish', 'reconcile-finish'):
        q = sub.add_parser(verb); q.add_argument('--dispatch-id', required=True)
        if verb == 'ack': q.add_argument('--tool-receipt', required=True)
        if verb == 'heartbeat': q.add_argument('--journal', required=True)
        if verb == 'retry':
            q.add_argument('--operator-quiescent', action='store_true'); q.add_argument('--repair-report', required=True)
        if verb in ('finish','reconcile-finish'): q.add_argument('--report', required=True)
        if verb=='reconcile-finish':q.add_argument('--supervisor-report',required=True)
    a = p.parse_args(); root = Path(a.root).resolve(); root.mkdir(parents=True, exist_ok=True)
    with (root / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        require(not (root/'coordinator.json').exists() and not (root/'.coordinator-owned.json').exists(), 'use-global-coordinator-entry')
        path = root / 'state.json'
        if a.command == 'init':
            require(not path.exists(), 'existing-day-must-resume')
            s = initialize(a.day, read(a.acceptance)); result = {'ok': True, 'phase': s['phase'], 'day': s['day']}
        else:
            s = read(path); migrate(s)
            if a.command == 'ack': ack(s, a.dispatch_id, a.tool_receipt)
            elif a.command == 'heartbeat': heartbeat(s, a.dispatch_id, a.journal)
            elif a.command == 'retry': retry(s, a.dispatch_id, a.operator_quiescent, a.repair_report)
            elif a.command == 'finish': finish(s, a.dispatch_id, a.report)
            elif a.command == 'reconcile-finish':reconcile_finish(s,a.dispatch_id,a.report,a.supervisor_report)
            result = inspect(s, a.timeout) if a.command == 'inspect' else plan(s) if a.command == 'plan' else s
        s['updated_at'] = stamp(); atomic(path, s)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try: main()
    except (ValueError, KeyError, OSError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False)); raise SystemExit(1)

def accept_unified_delivery(s,bundle_ref):
    """Only exact three ready reports + deep client/cursor proof close this round."""
    import delivery_commit
    bundle=progress.reference(bundle_ref);result=progress.reference(bundle['cursor_commit']);folder=Path(result['batch']['path']).parent/'items'
    reports=delivery_commit.verify_reports(bundle_ref,folder,current=True)
    require(s.get('collection_contract')=='three-flow-collection-ready-v1'and s.get('index')==3 and s.get('phase')=='ready','delivery-original-ready-round')
    require(s.get('collection_ready_reports')=={flow:r['collection_report']for flow,r in reports.items()}and all(r['day']==s['day']for r in reports.values()),'delivery-exact-original-ready-partition')
    existing=s.get('unified_delivery')
    if existing is not None:
        require(existing==bundle_ref and s.get('delivery_complete')is True and all(any(e.get('type')=='completed'and e.get('dispatch_id')==r['dispatch_id']and e.get('report')==bundle['reports'][flow]for e in s['events'])for flow,r in reports.items()),'delivery-terminal-coordinator-conflict');return s
    require(not any(e.get('type')=='completed'and e.get('dispatch_id')in{r['dispatch_id']for r in reports.values()}for e in s['events']),'delivery-unowned-completed-event')
    for flow in FLOWS:s['events'].append({'type':'completed','dispatch_id':reports[flow]['dispatch_id'],'workflow':flow,'report':bundle['reports'][flow],'unified_delivery':bundle_ref,'at':stamp()})
    s.update(unified_delivery=bundle_ref,delivery_complete=True)
    return s
