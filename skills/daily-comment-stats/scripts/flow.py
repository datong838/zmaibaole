#!/usr/bin/env python3
"""Durable agent workflow: init -> next -> checkpoint/record -> process -> next.

Only Codex performs browser operations. This CLI never accesses browser profiles,
connects to debugging services or starts Chrome. Send is intentionally absent.
"""
import argparse
import json
from pathlib import Path
import time
import hashlib
import subprocess
import sys
import uuid
import shutil
import os
from datetime import datetime,date

from ds_calendar import compute, CALENDAR
from ds_common import (FlowError, SKILL, PROJECT, MAPPING, VERSION, load_map, match_name,
                       company_dir, output_root, atomic_json, sha256, now, lock)
from ds_processor import process
from ds_common import acquisition_backend_valid
from ds_progress import DEFAULT_PROGRESS,plan as plan_progress,record as record_progress,reserve_collection,read as read_progress,initialize as initialize_progress

FATAL_CODES={'risk-prompt','captcha','login-required','account-changed','source-company-mismatch','identity-unverified','connection-unavailable'}
TERMINAL={'complete','needs_review','zero_rows','skipped'}
ALLOWED_STAGES={'provider-bootstrap','identity','switch','navigation','filter','export-intent','export-submitted','export-generated','export-failed','download-intent','download-complete','return-company'}

def run_root(dates,outdir=None):
    return (Path(outdir) if outdir else SKILL.parents[1]/'work'/dates['today']/'daily' if dates['mode']!='manual' else output_root(dates['today'],dates['start'],dates['end'])).resolve()

def init_scope_inputs(dates,mapping_path,progress_file,dispatch_order=None):
    """Pure preflight, before backlog planning, locks or business file writes."""
    if dispatch_order is None:return load_map(mapping_path),json.loads((SKILL/'config/companies.json').read_text())['companies'],None
    sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
    import daily_dispatch_order as dispatch
    reference=dispatch_order
    if type(reference)is not dict or set(reference)!={'path','sha256'}:raise FlowError('init-dispatch-ref-required')
    order=dispatch.validate(reference,Path(reference['path']).parent.parent)
    if dates['today']!=order['day']or dates.get('end_exclusive')!=order['day']or order.get('production_enabled')is not False or order.get('complaint_submission_enabled')is not False:raise FlowError('init-dispatch-day-or-safety-conflict')
    ranges=order['scope']['company_ranges'];skipped=order['skipped_companies'];selected=[r['company']for r in ranges]+[r['company']for r in skipped]
    if not selected or len(set(selected))!=len(selected):raise FlowError('init-dispatch-company-duplicate')
    configured_run=dispatch.timing.company_run_mapping(order.get('active_company_policy'))
    mapping=configured_run['mapping']if configured_run else load_map(mapping_path)
    identities=configured_run['identities']if configured_run else json.loads((SKILL/'config/companies.json').read_text())['companies']
    by={r['company']:r for r in mapping}
    if len(by)!=len(mapping)or not set(selected)<=set(by):raise FlowError('init-dispatch-mapping-company-missing')
    gids={r['company']:r['groupid']for r in ranges+skipped}
    policy=dispatch.timing.company_policy(order.get('active_company_policy'))
    if policy and policy['kind']=='active-company-scope-policy-v2':
        configured={r['company']:r for r in policy['configured_entries']}
        if any(name not in configured or configured[name]['verified']['groupid']!=gids[name]or configured[name]['production_group']!=by[name]['wecom_group']for name in selected):raise FlowError('init-dispatch-configured-company-mapping-conflict')
        identities={**identities,**{name:{'groupid':configured[name]['verified']['groupid']}for name in selected}}
    if any(identities.get(name,{}).get('groupid')!=gids[name]for name in selected):raise FlowError('init-dispatch-identity-conflict')
    offer=dispatch.timing.pinned(order['offer']);original_progress=offer['ledger_snapshots'][0]['original_path']
    if str(Path(progress_file).resolve())!=original_progress:raise FlowError('init-dispatch-progress-path-conflict')
    if any(r['end_exclusive']!=order['day']or (dates['mode']=='manual'and r['start']!=dates['start'])for r in ranges):raise FlowError('init-dispatch-date-conflict')
    selected_mapping=[r for r in mapping if r['company']in selected]
    return selected_mapping,identities,{'work_order':reference,'scope_sha256':order['scope_sha256'],'active_company_policy':order.get('active_company_policy')}

def _supervised_redispatch_archives_stale_receipt(batch,scope):
    """B85: a batch_receipt pinned to a dispatch that the coordinator has since
    archived through a verified repair-redispatch event must not deadlock the
    successor dispatch (observed 2026-11-03: B35 re-dispatch :3 -> :4 with the
    old inner-run receipt still naming the archived order). Fail closed unless
    the coordinator's own immutable event chain proves the exact transition:
    the last event is a hash-checked repair-redispatch whose report names the
    receipt's dispatch, that dispatch's daily-execution-bound event pinned the
    receipt's order bytes, and the coordinator now runs the successor day."""
    import hashlib
    try:
        state=json.loads((PROJECT/'runtime/workshop-director/state.json').read_bytes())
        events=state.get('events',[])
        archived_idx=[i for i,e in enumerate(events) if e.get('type')=='repair-redispatch']
        if not archived_idx:return False
        idx=archived_idx[-1];event=events[idx]
        # Only dispatch-family events may follow the archival; any unrelated
        # action after it voids the supervised transition.
        allowed={'dispatch-intent','daily-execution-bound','dispatched','business-ledger-snapshot','repair-redispatch'}
        if any(e.get('type') not in allowed for e in events[idx+1:]):return False
        # Every archived dispatch in this family contributes its bound order as
        # a stale-receipt candidate; each report is hash-checked and its
        # quiescence fields verified before its order is accepted.
        archived_orders=[]
        for i in archived_idx:
            ev=events[i]
            report_path=Path(ev.get('report') or '')
            if not report_path.is_file():return False
            raw=report_path.read_bytes()
            if ev.get('sha256') and hashlib.sha256(raw).hexdigest()!=ev['sha256']:return False
            report=json.loads(raw)
            if report.get('dispatch_id')!=ev.get('previous') or not all(report.get(k) is True for k in ('operator_quiescent','browser_quiescent','wecom_quiescent','original_work_orders_only')):return False
            bound=[e for e in events if e.get('type')=='daily-execution-bound' and e.get('dispatch_id')==ev.get('previous')]
            if bound:archived_orders.append(bound[-1].get('order') or {})
        pinned=batch.get('dispatch_scope',{}).get('work_order') or {}
        if pinned not in archived_orders:return False
        if state.get('phase')!='running':return False
        return True
    except Exception:
        return False

def init_scope_guard(root,scope,progress_file,dates,*,rebuild=False):
    policy=PROJECT/'runtime/workshop-director/active-company-policy.json'
    if scope is None and (policy.exists()or policy.is_symlink())and (rebuild or not(root/'batch_receipt.json').is_file()):raise FlowError('init-active-policy-dispatch-order-required')
    receipt=root/'batch_receipt.json'
    if receipt.exists():
        batch=json.loads(receipt.read_bytes())
        if batch.get('dispatch_scope')!=scope:
            # B85: the only legitimate cross-scope receipt is one whose dispatch
            # the coordinator archived via a verified repair-redispatch; archive
            # the stale receipt verbatim and admit the successor scope.
            if scope is None or not _supervised_redispatch_archives_stale_receipt(batch,scope):raise FlowError('init-existing-dispatch-scope-conflict')
            archived=receipt.with_name('batch_receipt-archived-'+hashlib.sha256(receipt.read_bytes()).hexdigest()[:12]+'.json')
            if not archived.exists():atomic_json(archived,batch)
            receipt.unlink()
        if scope is not None:
            sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
            import daily_dispatch_order as dispatch
            order=dispatch.timing.pinned(scope['work_order']);expected=order['scope']['company_ranges']+order['skipped_companies'];rows=batch.get('companies',[])
            if len(rows)!=len(expected)or {r.get('company')for r in rows}!={r['company']for r in expected}or any(str(r.get('groupid'))!=next(x['groupid']for x in expected if x['company']==r['company'])for r in rows):raise FlowError('init-existing-dispatch-companies-conflict')
        return
    if scope is not None:
        sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
        import daily_dispatch_order as dispatch
        order=dispatch.timing.pinned(scope['work_order']);progress=read_progress(progress_file)
        for row in order['scope']['company_ranges']:
            if progress.get('companies',{}).get(row['company'],{}).get('next_start')!=row['start']:raise FlowError('init-dispatch-cursor-changed')
        for row in order['skipped_companies']:
            if progress.get('companies',{}).get(row['company'],{}).get('next_start')!=row['next_start']:raise FlowError('init-dispatch-skipped-cursor-changed')

def init_run(dates,outdir=None,mapping_path=MAPPING,rerun=False,export_dir=None,progress_file=None,require_existing=False,*,dispatch_order=None,delivery_contract=None):
    if delivery_contract not in (None,'three-flow-collection-ready-v1'):raise FlowError('delivery-contract-invalid')
    if not dates['ok']: raise FlowError('today-not-workday')
    progress_file=Path(progress_file or DEFAULT_PROGRESS).resolve()
    root=run_root(dates,outdir)
    mapping,identities,scope=init_scope_inputs(dates,mapping_path,progress_file,dispatch_order)
    configured_run=None
    if scope and scope.get('active_company_policy'):
        import execution_timing as timing
        configured_run=timing.company_run_mapping(scope['active_company_policy'])
        if configured_run:mapping_path=root/'company-run-mapping.csv'
    init_scope_guard(root,scope,progress_file,dates,rebuild=rerun)
    with lock(root):
        init_scope_guard(root,scope,progress_file,dates,rebuild=rerun)
        if configured_run:
            path=Path(mapping_path);raw=configured_run['csv_bytes']
            if path.exists()or path.is_symlink():
                if path.is_symlink()or path.read_bytes()!=raw:raise FlowError('run-mapping-conflict')
            else:
                with path.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
        rp=root/'batch_receipt.json'
        if require_existing and not rp.is_file():raise FlowError('existing-run-disappeared')
        if rp.exists() and not rerun:
            previous=json.loads(rp.read_text())
            if previous.get('mode')!='agent-live' or previous.get('requested_date_range',previous.get('date_range'))!=dates or previous.get('mapping_sha256')!=sha256(mapping_path) or (export_dir and previous.get('export_root')!=str(Path(export_dir).resolve())) or (previous.get('progress_file') and previous['progress_file']!=str(progress_file)):
                raise FlowError('run-conflict','Existing run configuration differs; choose another output directory')
            if previous.get('delivery_contract')!=delivery_contract:raise FlowError('existing-run-delivery-contract-conflict')
            return previous
        if rp.exists() and rerun:
            previous=json.loads(rp.read_text())
            if previous.get('delivery_contract')or delivery_contract:raise FlowError('staged-run-cannot-rerun')
            for journal_path in root.glob('*/operator/*/workflow.json'):
                journal=json.loads(journal_path.read_text())
                if journal.get('state')!='complete' and (journal.get('exportPending') or journal.get('downloadPending')):
                    raise FlowError('export-outcome-unknown','Unresolved operator journal cannot be discarded with --rerun')
            if any(c.get('export_pending') and c.get('status') not in TERMINAL|{'acquired'} for c in previous.get('companies',[])):
                raise FlowError('export-outcome-unknown','Cannot discard an unresolved submitted export with --rerun')
            backup=root/'history'/('batch-'+str(time.time_ns())+'.json');atomic_json(backup,previous)
        companies=[]
        for row in mapping:
            identity=identities.get(row['company'],{})
            item={**row,**identity,'status':'pending','attempts':0,'outdir':str(company_dir(root,row)),'checkpoints':[]}
            if not str(identity.get('groupid','')).isdigit():
                item.update(status='skipped',error={'code':'identity-config-missing','message':'Add a reviewed company groupid; target was not guessed','fatal':False})
                atomic_json(Path(item['outdir'])/'acquisition-failure.json',{'company':row['company'],'error':item['error'],'at':now()})
            else:
                planned=plan_progress(row['company'],dates,progress_file,root)
                item['date_range']=planned
                if not planned['ok']:item.update(status='skipped',skip_reason=planned['reason'])
            companies.append(item)
        valid=[row for row in companies if row['status']!='skipped']
        envelope=dict(dates)
        if valid:
            envelope['start']=min(row['date_range']['start'] for row in valid)
            envelope['days']=(date.fromisoformat(envelope['end'])-date.fromisoformat(envelope['start'])).days+1
            if envelope['start']!=dates['start']:envelope['mode']='catchup'
        identities_path=Path(progress_file).with_name('identity-registry.json')
        registry=read_identity_registry(identities_path)
        if scope and scope.get('active_company_policy'):
            import execution_timing as timing
            policy=timing.company_policy(scope['active_company_policy'])
            if policy['kind']=='active-company-scope-policy-v2':
                configured={r['verified']['groupid']:r['verified']['identity']for r in policy['configured_entries']};provider=policy['configured_entries'][0]['provider']
                if registry and registry.get('provider_baseline')!=provider:raise FlowError('account-changed',fatal=True)
                if any(gid in registry.get('company_identities',{})and registry['company_identities'][gid]!=value for gid,value in configured.items()):raise FlowError('account-changed',fatal=True)
                registry={'provider_baseline':provider,'company_identities':{**registry.get('company_identities',{}),**configured}}
        state={'flow':'daily-comment-stats','version':VERSION,'mode':'agent-live','run_token':uuid.uuid4().hex,'status':'running','created_at':now(),
               'date_range':envelope,'requested_date_range':dates,'progress_file':str(progress_file),'mapping_path':str(Path(mapping_path).resolve()),'mapping_sha256':sha256(mapping_path),
               'run_dir':str(root),'export_root':str(Path(export_dir).resolve()) if export_dir else str(SKILL.parents[1]/'runtime/exports'),'backend':'local-dom-bridge','send_blocked':True,'sent':False,
               'companies':companies,'identity_baseline':None,'identity_contract':'merchant-v2','identity_registry':str(identities_path),
               'provider_baseline':registry.get('provider_baseline'),'company_identities':registry.get('company_identities',{}),
               'identity_bootstrap':not bool(registry),'roundtrip':{'required':len(valid)>1,'verified':False,'target_company':valid[0]['company'] if valid else None},'events':[],**({'delivery_contract':delivery_contract}if delivery_contract else{}),**({'dispatch_scope':scope}if scope is not None else{})}
        save(state);return state

def save(state):
    statuses=[c['status'] for c in state['companies']]
    state.update(companies_total=len(statuses),succeeded=statuses.count('complete'),needs_review=statuses.count('needs_review'),
                 failed=statuses.count('failed'),skipped=statuses.count('skipped')+statuses.count('zero_rows'))
    state['updated_at']=now()
    state['elapsed_s']=round((datetime.fromisoformat(state['updated_at'])-datetime.fromisoformat(state['created_at'])).total_seconds(),3)
    atomic_json(Path(state['run_dir'])/'batch_receipt.json',state)

def load_state(root):
    state=json.loads((Path(root)/'batch_receipt.json').read_text())
    if state.get('mode')!='agent-live': raise FlowError('run-mode-mismatch')
    if sha256(state['mapping_path'])!=state['mapping_sha256']: raise FlowError('mapping-changed','Mapping changed during the run; start a new run')
    return state

def get_company(state,name):
    selected=match_name(name,[r['company'] for r in state['companies']])
    return next(r for r in state['companies'] if r['company']==selected)

def company_dates(state,row):return row.get('date_range',state['date_range'])

def read_identity_registry(path):
    path=Path(path)
    if not path.exists():return {}
    data=json.loads(path.read_text());provider=data.get('provider_baseline');known=data.get('company_identities')
    if data.get('version')!=2 or not isinstance(provider,str) or not provider or not isinstance(known,dict) or not known:raise FlowError('identity-registry-invalid',fatal=True)
    for gid,value in known.items():
        if not str(gid).isdigit() or not isinstance(value,dict) or set(value)!={'provider','account_id','manager'} or any(not isinstance(x,str) or not x for x in value.values()) or value['provider']!=provider:raise FlowError('identity-registry-invalid',fatal=True)
    return data

def persist_identity_registry(state):
    path=Path(state.get('identity_registry') or Path(state['progress_file']).with_name('identity-registry.json'))
    state['identity_registry']=str(path)
    with lock(path.parent/'identity-registry-lock'):
        old=read_identity_registry(path);provider=state.get('provider_baseline');known=state.get('company_identities',{})
        if not provider or not known:return
        if old and old['provider_baseline']!=provider:raise FlowError('account-changed',fatal=True)
        merged=dict(old.get('company_identities',{}))
        for gid,value in known.items():
            if gid in merged and merged[gid]!=value:raise FlowError('account-changed',fatal=True)
            merged[gid]=value
        atomic_json(path,{'version':2,'provider_baseline':provider,'company_identities':merged,'updated_at':now(),'latest_batch':state['run_dir']})

def identity_fields(state,row):
    if state.get('identity_contract')!='merchant-v2':return {'identity_baseline':state.get('identity_baseline')}
    known=state.get('company_identities',{})
    return {'identity_contract':'merchant-v2','provider_baseline':state.get('provider_baseline'),
            'identity_baseline':known.get(str(row['groupid'])),'known_company_identities':known,
            'identity_bootstrap':state.get('identity_bootstrap',False),
            'allowed_groupids':[str(r['groupid']) for r in state['companies'] if str(r.get('groupid','')).isdigit()],
            'identity_contract_upgrade':state.get('identity_contract_upgrade')}

def check_scoped_identity(state,row,payload):
    value=payload.get('identity',{})
    if set(value)!={'provider','account_id','manager'} or any(not isinstance(v,str) or not v.strip() for v in value.values()):raise FlowError('identity-unverified',fatal=True)
    provider=state.get('provider_baseline')
    if provider and value['provider']!=provider:raise FlowError('account-changed',fatal=True)
    gid=str(payload.get('groupid') or row['groupid']);scope=payload.get('identity_scope','company')
    known=state.setdefault('company_identities',{})
    if scope=='entry':
        if payload.get('stage')!='identity' or gid not in {str(r['groupid']) for r in state['companies']}:raise FlowError('entry-identity-scope-invalid',fatal=True)
        if gid in known and value!=known[gid]:raise FlowError('account-changed',fatal=True)
        known.setdefault(gid,value)
    elif scope=='company':
        if gid!=str(row['groupid']):raise FlowError('source-company-mismatch',fatal=True)
        if gid in known and value!=known[gid]:raise FlowError('account-changed',fatal=True)
        known[gid]=value
    else:raise FlowError('identity-scope-invalid',fatal=True)
    if not provider:state['provider_baseline']=value['provider']
    if not state.get('identity_baseline'):state['identity_baseline']=value

def upgrade_identity_scope(state):
    """Explicit audited repair of the old global merchant-ID contract, no UI."""
    if state.get('identity_contract')=='merchant-v2':return dispatch(state)
    known={}
    for row in state['companies']:
        values=[c['identity'] for c in row.get('checkpoints',[]) if c.get('stage') in ('switch','return-company') and str(c.get('groupid'))==str(row['groupid']) and isinstance(c.get('identity'),dict)]
        for value in values:
            if str(row['groupid']) in known and known[str(row['groupid'])]!=value:raise FlowError('account-changed',fatal=True)
            known[str(row['groupid'])]=value
        for path in (Path(row['outdir'])/'operator').glob('*/workflow.json'):
            journal=json.loads(path.read_text())
            if journal.get('state')=='complete':continue
            if journal.get('exportPending') or journal.get('downloadPending') or journal.get('attempts') or any(c.get('stage') in ('export-intent','download-intent') for c in journal.get('checkpoints',[])) or any(c.get('state')=='unknown' for c in journal.get('calls',[])):
                raise FlowError('identity-upgrade-side-effect-forbidden')
    baseline=state.get('identity_baseline')
    if not isinstance(baseline,dict) or not known or baseline not in known.values():raise FlowError('verified-existing-merchant-identity-required')
    if any(v.get('provider')!=baseline.get('provider') for v in known.values()):raise FlowError('account-changed',fatal=True)
    original=Path(state['run_dir'])/'batch_receipt.json';backup=original.with_name('batch-before-merchant-v2-'+sha256(original)[:12]+'.json')
    if not backup.exists():shutil.copyfile(original,backup)
    request={'kind':'merchant-v2','id':uuid.uuid4().hex,'at':now(),'previous_state':str(backup),'sha256':sha256(backup)}
    state.update(identity_contract='merchant-v2',provider_baseline=baseline['provider'],company_identities=known,identity_contract_upgrade=request,identity_bootstrap=False)
    persist_identity_registry(state)
    state['events'].append({'stage':'identity-contract-upgraded',**request});save(state)
    return dispatch(state)

def update_progress(state,row):
    if not state.get('progress_file') or not row.get('receipt'):return
    if state.get('delivery_contract')=='three-flow-collection-ready-v1':
        if row.get('status') not in ('complete','zero_rows'):return
        result=reserve_collection(state['progress_file'],row['receipt'],row,company_dates(state,row),state['mapping_sha256'],state['run_dir'])
        if result!=row.get('collection_reservation'):row['collection_reservation']=result;save(state)
        return
    if state.get('delivery_contract')is not None:raise FlowError('delivery-contract-invalid')
    result=record_progress(state['progress_file'],row['receipt'],row,company_dates(state,row),state['mapping_sha256'])
    if result!=row.get('progress'):
        row['progress']=result;save(state)

def next_task(state):
    if state['status']=='halted': return {'action':'halted','reason':state.get('halt_reason'),'send_blocked':True}
    for row in state['companies']:
        if row['status'] in ('complete','needs_review','zero_rows'):
            rec_path=Path(row['outdir'])/'receipt.json'
            if not rec_path.exists(): return {'action':'repair','company':row['company'],'reason':'receipt-missing'}
            rec=json.loads(rec_path.read_text());src=Path(rec.get('src_file',''))
            from ds_common import receipt_valid
            if not src.is_file() or not receipt_valid(rec,src,row,company_dates(state,row),state['mapping_sha256']):
                return {'action':'repair','company':row['company'],'reason':'artifact-or-source-changed'}
            if not row.get('receipt'):row['receipt']=str(rec_path)
            update_progress(state,row)
            continue
        if row['status']=='skipped': continue
        if row['status']=='failed': continue  # non-risk failures do not block the following company
        if row['status']=='acquired': return {'action':'process','company':row['company'],'source':row['source'],'evidence':row['evidence']}
        # A supervised reverify round starts from a clean frontier: the stopped
        # round-1 progress is archived verbatim (state['reverify'] pins its
        # bytes), so the fresh work order never inherits its resume prefix or
        # export side-effect intent. Attempts carry the shared export budget.
        reverify_open=state.get('reverify',{}).get('company')==row['company']
        # attempts stay row-side (checkpoint('export-intent') re-derives the
        # shared budget); the fresh journal must carry a clean 0 or the bridge
        # reads any truthy resume field as an unknown side-effect migration.
        resume={'latest':None,'checkpoints':[],'export_pending':row.get('export_pending',False),'attempts':0}if reverify_open else {'latest':row.get('latest_checkpoint'),'checkpoints':row['checkpoints'],'export_pending':row.get('export_pending',False),'attempts':row['attempts']}
        return {'action':'acquire','company':row['company'],'groupid':row['groupid'],'date_range':company_dates(state,row),
                'resume':resume,'output_dir':row['outdir'],'source_dir':str(Path(state.get('export_root',str(SKILL.parents[1]/'runtime/exports')))/('%02d_%s'%(row['seq'],row['company']))),
                'operator_skill':'douyin-laike-operator',
                **identity_fields(state,row),'recovery_request':row.get('recovery_request')}
    if state['roundtrip']['required'] and not state['roundtrip']['verified']:
        first=get_company(state,state['roundtrip'].get('target_company') or state['companies'][0]['company'])
        return {'action':'return-company','company':first['company'],'groupid':first['groupid'],**identity_fields(state,first),'operator_skill':'douyin-laike-operator'}
    return {'action':'done','send_blocked':True,'summary':{k:state[k] for k in ('companies_total','succeeded','failed','skipped','needs_review')}}

def reverify(state,row):
    """Supervised page/export count-mismatch reverification admission.
    The first export is already a decided fact: download-complete plus an
    archived receipt whose only warning is page-export-count-mismatch. This
    verb archives the stopped bytes verbatim, clears the export-pending guard
    (the first outcome is no longer unknown) and reopens the company for one
    bounded re-acquisition whose fresh filter read and export decide the
    discrepancy. No export, download or page input is replayed here."""
    if state.get('status')=='halted':raise FlowError('batch-halted','Resolve and use explicit resume after manual verification')
    if state.get('reverify'):raise FlowError('reverify-already-pending')
    if row['status']!='needs_review':raise FlowError('reverify-row-not-needs-review')
    if not row.get('receipt'):raise FlowError('reverify-receipt-missing')
    receipt=json.loads(Path(row['receipt']).read_text())
    if receipt.get('status')!='needs_review' or receipt.get('warnings')!=['page-export-count-mismatch']:raise FlowError('reverify-mismatch-required')
    if not any(c['stage']=='download-complete' for c in row['checkpoints']):raise FlowError('reverify-first-export-incomplete')
    if state.get('roundtrip',{}).get('verified') is not True:raise FlowError('reverify-roundtrip-unverified')
    if state.get('failed'):raise FlowError('reverify-failed-companies-present')
    if row.get('attempts',0)>=3:raise FlowError('export-retries-exhausted')
    archive_dir=Path(state['run_dir'])/'reverify-archive';archive_dir.mkdir(parents=True,exist_ok=True)
    batch_raw=(Path(state['run_dir'])/'batch_receipt.json').read_bytes();receipt_raw=Path(row['receipt']).read_bytes()
    batch_archive=archive_dir/('batch_receipt-'+hashlib.sha256(batch_raw).hexdigest()+'.json')
    receipt_archive=archive_dir/('receipt-'+hashlib.sha256(receipt_raw).hexdigest()+'.json')
    for target,raw in ((batch_archive,batch_raw),(receipt_archive,receipt_raw)):
        if target.exists():
            if target.read_bytes()!=raw:raise FlowError('reverify-archive-conflict')
        else:
            with target.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    state['reverify']={'kind':'supervised-export-count-reverify-v1','company':row['company'],'groupid':row['groupid'],'round':1,
                       'first_receipt':{'path':str(row['receipt']),'sha256':hashlib.sha256(receipt_raw).hexdigest()},
                       'first_batch':{'path':str(Path(state['run_dir'])/'batch_receipt.json'),'sha256':hashlib.sha256(batch_raw).hexdigest()},
                       'adjudicated_at':now()}
    row['export_pending']=False;row['status']='pending'
    # The supervised admission restarts acquisition from a clean frontier. The
    # stopped round-1 progress (checkpoints and latest) stays verbatim in the
    # reverify-archive batch copy; the fresh reverify work order must not
    # inherit the first export's side-effect intent or resume prefix.
    row['checkpoints']=[];row.pop('latest_checkpoint',None)
    state['events'].append({'stage':'reverify-admitted','company':row['company'],'at':now()})
    save(state);return row

def accept_review(state,row,adjudication):
    """Supervised page/export count-adjudication closure.
    The user's explicit ruling is the only authority that accepts a remaining
    page/export count difference after the bounded reverify round. Every
    number the adjudication records is re-read from the receipt and the
    reverify journal (never trusted from the adjudication file itself), the
    reverify journal must be a decided fact, and the first-round receipt must
    stay distinct from the adjudicated one. The archived mismatch facts stay
    on the receipt inside the adjudication block."""
    if state.get('status')=='halted':raise FlowError('batch-halted','Resolve and use explicit resume after manual verification')
    reverify=state.get('reverify')or{}
    if reverify.get('kind')!='supervised-export-count-reverify-v1'or reverify.get('company')!=row['company']:raise FlowError('adjudication-reverify-round-required')
    if state.get('failed'):raise FlowError('adjudication-failed-companies-present')
    if row['status']!='needs_review':raise FlowError('adjudication-row-not-needs-review')
    if not row.get('receipt'):raise FlowError('adjudication-receipt-missing')
    if not (isinstance(adjudication,dict)and adjudication.get('kind')=='supervised-count-adjudication-v1'
            and adjudication.get('decided_by')=='supervisor'
            and isinstance(adjudication.get('user_ruling'),str)and adjudication['user_ruling'].strip()
            and isinstance(adjudication.get('basis'),str)and adjudication['basis'].strip()):raise FlowError('adjudication-invalid')
    if state.get('roundtrip',{}).get('verified') is not True:raise FlowError('adjudication-roundtrip-unverified')
    if not any(c['stage']=='download-complete' for c in row['checkpoints']):raise FlowError('adjudication-export-incomplete')
    if row.get('attempts',0)<2:raise FlowError('adjudication-reverify-not-run')
    receipt_path=Path(row['receipt']);raw=receipt_path.read_bytes();prior_sha=hashlib.sha256(raw).hexdigest()
    receipt=json.loads(raw)
    if (receipt.get('status')!='needs_review'or receipt.get('mismatch')is not True
        or receipt.get('warnings')!=['page-export-count-mismatch']
        or type(receipt.get('page_filtered'))is not int or type(receipt.get('row_count'))is not int
        or receipt['row_count']==receipt['page_filtered']):raise FlowError('adjudication-receipt-not-count-mismatch')
    if reverify.get('first_receipt',{}).get('sha256')==prior_sha:raise FlowError('adjudication-first-round-receipt')
    # The reverify round's own journal must be a decided fact: its stable work
    # order token is re-derived exactly as dispatch does (:reverify-<round>).
    token=hashlib.sha256((state['run_dir']+state.get('run_token',state['created_at'])+'acquire'+row['company']+(':reverify-'+str(reverify['round']))).encode()).hexdigest()
    journal_path=Path(row['outdir'])/'operator'/token[:16]/'workflow.json'
    journal=json.loads(journal_path.read_bytes())
    if journal.get('state')!='complete'or journal.get('phase')!='done'or journal.get('work_order_id')!=token:raise FlowError('adjudication-reverify-journal-undecided')
    receipt['count_adjudication']={'kind':'supervised-count-adjudication-v1','decided_by':'supervisor',
        'user_ruling':adjudication['user_ruling'],'basis':adjudication['basis'],
        'page_filtered':receipt['page_filtered'],'row_count':receipt['row_count'],
        'round':reverify['round'],'attempts':row['attempts'],
        'reverify_receipt':{'path':str(receipt_path),'sha256':prior_sha},
        'reverify_journal':{'path':str(journal_path),'sha256':sha256(journal_path)},
        'first_receipt':dict(reverify['first_receipt']),'adjudicated_at':now()}
    receipt['warnings']=[w for w in receipt['warnings'] if w!='page-export-count-mismatch']
    receipt['stages'].append({'stage':'count-adjudication','ok':True,'at':now(),'page_filtered':receipt['page_filtered'],'row_count':receipt['row_count']})
    # The mismatch is resolved by ruling, not by data: quality_blocked and
    # mismatch flip only together with the recorded adjudication block.
    receipt['mismatch']=False;receipt['quality_blocked']=False;receipt['status']='complete'
    atomic_json(receipt_path,receipt)
    row['review_adjudication']={'receipt_sha256_before':prior_sha,'receipt_sha256_after':sha256(receipt_path),'adjudicated_at':now()}
    row['status']='complete'
    state['events'].append({'stage':'count-adjudicated','company':row['company'],'round':reverify['round'],'at':now()})
    save(state);return row

def checkpoint(state,row,payload):
    stage=payload.get('stage')
    if stage not in ALLOWED_STAGES: raise FlowError('checkpoint-invalid','Unknown stage')
    entry=state.get('identity_contract')=='merchant-v2' and (stage=='provider-bootstrap' or stage=='identity' and payload.get('identity_scope')=='entry')
    if payload.get('groupid') and str(payload['groupid'])!=row['groupid'] and not entry: raise FlowError('source-company-mismatch',fatal=True)
    stages={c['stage'] for c in row['checkpoints']}
    required={'switch':'identity','navigation':'switch','filter':'switch','export-submitted':'export-intent','export-generated':'export-intent',
              'export-failed':'export-intent','download-intent':'export-generated','download-complete':'download-intent'}
    if stage in required and required[stage] not in stages:raise FlowError('checkpoint-out-of-order',stage+' requires '+required[stage])
    if stage=='provider-bootstrap':
        import re
        provider=payload.get('provider')
        if state.get('identity_contract')!='merchant-v2' or state.get('identity_bootstrap') is not True or not isinstance(provider,str) or not re.fullmatch(r'服务商\d+',provider) or str(payload.get('groupid')) not in {str(r['groupid']) for r in state['companies']}:raise FlowError('provider-bootstrap-invalid',fatal=True)
        if state.get('provider_baseline') not in (None,provider):raise FlowError('account-changed',fatal=True)
        state['provider_baseline']=provider
    if stage in ('identity','switch','return-company'):
        if state.get('identity_contract')=='merchant-v2':check_scoped_identity(state,row,payload)
        else:
            identity=payload.get('identity',{})
            if set(identity)!={'provider','account_id','manager'} or any(not isinstance(v,str) or not v.strip() for v in identity.values()): raise FlowError('identity-unverified',fatal=True)
            if state['identity_baseline'] and state['identity_baseline']!=identity: raise FlowError('account-changed',fatal=True)
            if not state['identity_baseline']: state['identity_baseline']=identity
    if stage=='filter':
        if type(payload.get('page_filtered')) is not int or payload['page_filtered']<0: raise FlowError('page-count-invalid')
        if payload.get('date_range')!={'start':company_dates(state,row)['start'],'end':company_dates(state,row)['end']}: raise FlowError('source-date-mismatch')
    if stage=='export-intent':
        if row.get('export_pending'):
            raise FlowError('export-outcome-unknown','Reconcile existing task; new export forbidden')
        if not any(c['stage']=='filter' for c in row['checkpoints']): raise FlowError('filter-unverified')
        if row['attempts']>=3: raise FlowError('export-retries-exhausted')
        row['attempts']+=1;row['export_pending']=True
    if stage=='export-failed':
        if payload.get('platform_status')!='failed' or not payload.get('record_reference'): raise FlowError('export-failure-unverified')
        row['export_pending']=False
    item={**payload,'at':now()};row['checkpoints'].append(item);row['latest_checkpoint']=item;row['status']='acquiring'
    atomic_json(Path(row['outdir'])/'acquisition-progress.json',row)
    state['events'].append({'company':row['company'],'stage':stage,'at':item['at']});save(state)
    if state.get('identity_contract')=='merchant-v2' and stage in ('identity','switch','return-company'):persist_identity_registry(state)

def record_source(state,row,payload,*,capture_ref=None):
    if payload.get('kind')=='current-reconciled-export-source-v1':
        from current_range_source import validate_reconciled_export
        dates=company_dates(state,row);source=Path(payload['source']).resolve()
        validate_reconciled_export(payload,row,dates,source)
        current=json.loads(Path(payload['current_result']['path']).read_bytes())
        expected=state.get('company_identities',{}).get(str(row['groupid']))
        if current['identity']!=expected:raise FlowError('current-source-account-conflict',fatal=True)
        if Path(row['outdir']).resolve() not in Path(current['original_order']).parents:raise FlowError('current-source-original-job-conflict')
        evidence=Path(row['outdir'])/'current-acquisition.json';atomic_json(evidence,payload)
        row.update(status='acquired',source=str(source),evidence=str(evidence),source_kind=payload['kind'])
        row.pop('error',None)
        row.setdefault('checkpoints',[]).append({'stage':'current-source-acquired','at':now(),'current_result':payload['current_result'],'download_verified':False})
        save(state);return
    if payload.get('kind')=='daily-visible-dom-source-v1':return record_dom_source(state,row,payload,capture_ref=capture_ref)
    if not any(c['stage']=='download-complete' for c in row['checkpoints']):raise FlowError('download-checkpoint-missing')
    if not acquisition_backend_valid(payload): raise FlowError('acquisition-backend-mismatch')
    if payload.get('company')!=row['company'] or str(payload.get('groupid'))!=row['groupid']: raise FlowError('source-company-mismatch',fatal=True)
    desired={'start':company_dates(state,row)['start'],'end':company_dates(state,row)['end']}
    if payload.get('date_range')!=desired: raise FlowError('source-date-mismatch')
    if payload.get('download_verified') is not True: raise FlowError('download-unverified')
    identity=payload.get('identity')
    if payload.get('account_verified') is not True or payload.get('identity_before')!=identity: raise FlowError('identity-unverified',fatal=True)
    expected=state.get('company_identities',{}).get(str(row['groupid'])) if state.get('identity_contract')=='merchant-v2' else state.get('identity_baseline')
    if not expected or identity!=expected: raise FlowError('account-changed',fatal=True)
    if type(payload.get('page_filtered')) is not int or payload['page_filtered']<0: raise FlowError('page-count-invalid')
    source=Path(payload.get('source','')).resolve()
    if not source.is_file() or source.suffix.lower()!='.xlsx' or source.stat().st_size==0: raise FlowError('download-missing')
    digest=sha256(source)
    if payload.get('src_sha256') and payload['src_sha256']!=digest: raise FlowError('source-hash-mismatch')
    evidence={**payload,'src_sha256':digest,'account_verified':True,'recorded_at':now()}
    evidence_path=Path(row['outdir'])/'acquisition.json';atomic_json(evidence_path,evidence)
    row.update(status='acquired',source=str(source),evidence=str(evidence_path));save(state)

def record_dom_source(state,row,payload,*,capture_ref):
    """Independent source-ready checkpoint; the old operator/download stays pending."""
    from ds_common import dom_source_data,dom_original_download,dom_capture_data
    dom_capture_data(capture_ref,payload,state,row)
    dates=company_dates(state,row);source=Path(payload.get('source',''))
    data=dom_source_data(payload,row,dates,source)
    if state.get('delivery_contract')!='three-flow-collection-ready-v1':raise FlowError('dom-unified-delivery-required')
    expected=state.get('company_identities',{}).get(str(row['groupid']))if state.get('identity_contract')=='merchant-v2'else state.get('identity_baseline')
    if not expected or payload['identity']!=expected:raise FlowError('dom-account-changed',fatal=True)
    job=data['job'];original=job['original_job'];original_path=Path(original['path'])
    if Path(row['outdir']).resolve()not in original_path.parents:raise FlowError('dom-job-outside-company-run')
    scope=state.get('dispatch_scope',{})
    if scope.get('work_order')!=job['original_order']:raise FlowError('dom-original-order-mismatch')
    before=dom_original_download(data)
    evidence_path=Path(row['outdir'])/'dom-acquisition.json'
    if row.get('source_kind')=='daily-visible-dom-source-v1':
        if row.get('evidence')!=str(evidence_path)or row.get('dom_capture')!=capture_ref or json.loads(evidence_path.read_bytes())!=payload:raise FlowError('dom-source-existing-conflict')
        return
    if evidence_path.exists():raise FlowError('dom-acquisition-already-exists')
    item={'stage':'dom-acquisition-complete','at':now(),'source_kind':'daily-visible-dom-source-v1',
          'receipt':payload['receipt'],'original_workflow':before,'download_verified':False,
          'capture':capture_ref,'source_is_authoritative_export':False,'counts':data['summary']}
    atomic_json(evidence_path,payload)
    row.setdefault('checkpoints',[]).append(item)
    row.update(status='acquired',source=str(source),evidence=str(evidence_path),source_kind=payload['kind'],dom_capture=capture_ref)
    row.pop('error',None);save(state)

def fail_company(state,row,code,message=''):
    fatal=code in FATAL_CODES
    row.update(status='skipped' if code in ('company-not-found','company-ambiguous') else 'failed',error={'code':code,'message':message,'fatal':fatal})
    atomic_json(Path(row['outdir'])/'acquisition-failure.json',{'company':row['company'],'error':row['error'],'at':now()})
    if fatal: state.update(status='halted',halt_reason=row['error'])
    save(state)

def dispatch(state):
    """Materialize a stable work order. The operator owns its own durable journal."""
    job=next_task(state)
    if job['action'] in ('acquire','return-company'):
        row=get_company(state,job['company'])
        # A supervised reverify round opens its own stable work order and
        # journal: the round-1 journal is a decided fact and is never reused
        # or rewritten; other actions and companies keep the original token.
        reverify_round=':reverify-'+str(state['reverify']['round'])if job['action']=='acquire' and state.get('reverify',{}).get('company')==row['company'] else ''
        token=hashlib.sha256((state['run_dir']+state.get('run_token',state['created_at'])+job['action']+row['company']+reverify_round).encode()).hexdigest()
        base=Path(row['outdir'])/('return' if job['action']=='return-company' else 'operator')/token[:16]
        job.update(backend='local-dom-bridge',explicit_tab_id_required=True,work_order_id=token,workflow_path=str(base/'workflow.json'),work_order_path=str(base/'work-order.json'))
        policy=state.get('dispatch_scope',{}).get('active_company_policy')
        if policy:
            import execution_timing as timing
            fields=timing.company_job_fields(policy,row['company'],row['groupid'],known=job.get('known_company_identities'))
            if fields:
                job.update(fields)
                # Company-only return still binds the original collection range.
                if job['action']=='return-company':job['date_range']=dict(row['date_range'])
        path=Path(job['work_order_path'])
        if path.exists():
            if path.is_symlink()or path.resolve()!=path:raise FlowError('work-order-canonical-path-required')
            prior=json.loads(path.read_bytes())
            if {k:v for k,v in prior.items()if k!='resume'}!={k:v for k,v in job.items()if k!='resume'}:raise FlowError('work-order-existing-contract-conflict')
            # Resume is derived progress, not new authority. The original role
            # journal owns it once the stable work order has been started.
            # Before that (no journal yet) the materialized file is still pure
            # derivation: refresh a stale resume to the current derived value
            # and archive the prior bytes verbatim. A frozen derivation is not
            # cosmetic: the bridge refuses any truthy side-effect-intent field
            # on a fresh start, so a stale resume deadlocks the stable work
            # order forever (B59 attempts 32-34).
            # B84: only the acquire action carries a resume key; return-company
            # work orders legitimately have none on both sides. Compare with
            # .get so the drift check cannot KeyError on a resume-less job.
            if prior.get('resume')!=job.get('resume'):
                if Path(job['workflow_path']).exists():
                    # A started journal owns the resume: its own progress is the
                    # authority and sync_operator imports the row-side record
                    # (remaining checkpoints, export budget) right after this
                    # dispatch returns. A running journal keeps its own
                    # progress (the bridge resumes its undecided outcome via
                    # the built-in finish_download reconcile); a decided
                    # journal is a fact; failed is handled by the recovery
                    # branch. The resume drift here is the row-side record of
                    # the round, not a stale pre-start derivation. Only an
                    # unreadable journal state keeps the fail-closed raise.
                    if json.loads(Path(job['workflow_path']).read_bytes()).get('state') not in ('running','complete','failed'):raise FlowError('work-order-resume-owned-by-journal')
                    return prior
                atomic_json(path.with_name('work-order-prior-resume-'+hashlib.sha256(path.read_bytes()).hexdigest()[:12]+'.json'),prior)
                atomic_json(path,job)
                return job
            return prior
        atomic_json(path,job)
    return job

def import_confirmed_second_export_intent(state,row,job,journal,event):
    """Account for the already-confirmed second submission; never submit it again."""
    if event.get('stage')!='export-intent' or row.get('export_pending') is not True:return False
    retention=journal.get('retention_baseline_reconciliation',{})
    if retention.get('kind')!='verified-backed-up-export-removal-v1':return False
    calls=journal.get('calls',[]);submits=[c for c in calls if c.get('phase')=='submitExport'];reloads=[c for c in calls if c.get('phase')=='reloadRecords']
    events=[x for x in journal.get('checkpoints',[]) if x.get('stage')=='export-intent']
    prior=[x for x in row['checkpoints'] if x.get('stage')=='export-intent']
    if (len(submits)!=2 or len(reloads)!=2 or any(c.get('state')!='confirmed' for c in calls)
        or len(events)!=2 or event!=events[-1] or len(prior)!=1 or prior[0].get('event_id')!=events[0].get('event_id')
        or event.get('company')!=row['company'] or str(event.get('groupid'))!=row['groupid']
        or event.get('date_range')!={k:company_dates(state,row)[k] for k in ('start','end')} or row.get('attempts')!=1
        or event.get('event_id') in {x.get('event_id') for x in row['checkpoints']}):return False
    try:
        event_at=datetime.fromisoformat(event['at']);submitted_at=datetime.fromisoformat(journal['submitted_at']);clicked_at=datetime.fromisoformat(submits[-1]['at'])
        if not (event_at.tzinfo and submitted_at.tzinfo and clicked_at.tzinfo and 0 <= (event_at-submitted_at).total_seconds() <= 1 and 0 <= (clicked_at-event_at).total_seconds() <= 10):return False
    except (KeyError,TypeError,ValueError):return False
    # Both input calls have durable confirmations; only import the missing
    # historical event. Preserve export_pending and prevent another input.
    row['attempts']=2;item={**event,'at':now()};row['checkpoints'].append(item);row['latest_checkpoint']=item;row['status']='acquiring'
    atomic_json(Path(row['outdir'])/'acquisition-progress.json',row)
    state['events'].append({'company':row['company'],'stage':'export-intent','at':item['at']});save(state)
    return True

def sync_operator(state,job):
    """Import machine checkpoints once. Never ask an agent to invent/retype evidence."""
    path=Path(job['workflow_path'])
    if not path.exists():return False
    journal=json.loads(path.read_text());row=get_company(state,job['company'])
    if journal.get('work_order_id')!=job['work_order_id'] or journal.get('company')!=row['company'] or str(journal.get('groupid'))!=row['groupid']:
        raise FlowError('source-company-mismatch',fatal=True)
    imported={e.get('event_id') for e in row['checkpoints'] if e.get('event_id')}
    for event in journal.get('checkpoints',[]):
        if not event.get('event_id'):raise FlowError('checkpoint-id-missing')
        if event['event_id'] not in imported:
            prior_status=row['status']
            if not import_confirmed_second_export_intent(state,row,job,journal,event):checkpoint(state,row,event)
            imported.add(event['event_id'])
            if job['action']=='return-company':row['status']=prior_status;save(state)
    if state.get('identity_contract')=='merchant-v2':
        updated=identity_fields(state,row)
        if job.get('company_configuration_policy'):
            if job.get('provider_baseline')!=updated['provider_baseline']or job.get('identity_baseline')!=updated['identity_baseline']or any(updated['known_company_identities'].get(gid)!=value for gid,value in job['known_company_identities'].items()):raise FlowError('configured-original-job-identity-changed',fatal=True)
        else:job.update(updated);atomic_json(job['work_order_path'],job)
    if journal.get('state')=='failed':
        request=job.get('recovery_request') or {}
        if journal.get('error_code')=='connection-unavailable' and request.get('kind')=='connection-recovery' and request.get('id')!=journal.get('lastRecoveryRequestId'):
            return False  # New explicit retry is consumed by the role's next tick.
        if job['action']=='return-company':
            state.update(status='halted',halt_reason={'code':journal.get('error_code','operator-step-failed'),'message':journal.get('error','')});save(state);return True
        fail_company(state,row,journal.get('error_code','operator-step-failed'),journal.get('error',''))
        return True
    if journal.get('state')!='complete':return False
    if job['action']=='return-company':
        result=journal.get('result',{})
        returned=[event for event in journal.get('checkpoints',[]) if event.get('stage')=='switch']
        expected=identity_fields(state,row)['identity_baseline']
        if journal.get('phase')!='done' or not returned or returned[-1].get('identity')!=expected or str(returned[-1].get('groupid'))!=row['groupid']:
            raise FlowError('roundtrip-unverified')
        if result.get('verified') is not True or result.get('identity')!=expected or str(result.get('groupid'))!=row['groupid'] or result.get('company')!=row['company']:
            raise FlowError('roundtrip-unverified')
        state['roundtrip'].update(verified=True,at=now());save(state);return True
    # Call the independent role's public CLI; no cross-role implementation import.
    evidence=Path(job['workflow_path']).with_name('acquisition.json')
    script=SKILL.parent/'douyin-laike-operator/scripts/role_cli.py'
    completed=subprocess.run([sys.executable,str(script),'finalize','--work-order',job['work_order_path'],
                              '--journal',str(path),'--out',str(evidence)],capture_output=True,text=True)
    if completed.returncode:
        raise FlowError('operator-finalize-failed',completed.stdout.strip() or completed.stderr.strip())
    record_source(state,row,json.loads(evidence.read_text()));return True

def advance(state):
    """Only browser collection requires the host; all local handoff/process steps run here."""
    for _ in range(len(state['companies'])*3+4):
        job=dispatch(state)
        if job['action'] in ('acquire','return-company'):
            try:
                if not sync_operator(state,job):return job
            except FlowError as error:
                if job['action']=='return-company':
                    state.update(status='halted',halt_reason={'code':error.code,'message':str(error)});save(state)
                    continue
                fail_company(state,get_company(state,job['company']),error.code,str(error))
                if error.fatal and state['status']!='halted':
                    state.update(status='halted',halt_reason={'code':error.code,'message':str(error)});save(state)
        elif job['action']=='process':
            row=get_company(state,job['company']);evidence=json.loads(Path(row['evidence']).read_text())
            result=process(row['source'],row,company_dates(state,row),row['outdir'],state['mapping_path'],evidence['page_filtered'],evidence,capture_ref=row.get('dom_capture'),company_policy=state.get('dispatch_scope',{}).get('active_company_policy'))
            row.update(status=result['status'],receipt=result['receipt']);save(state);update_progress(state,row)
            if result.get('error',{}).get('fatal'):fail_company(state,row,result['error']['code'],result['error']['message'])
        else:
            if job['action']=='done':
                state['status']='complete_with_failures' if state['failed'] else 'needs_review' if state['needs_review'] else 'complete';save(state)
            return job
    raise FlowError('advance-cycle-limit')

def request_connection_retry(state):
    if state['status']!='halted' or state.get('halt_reason',{}).get('code')!='connection-unavailable':
        raise FlowError('connection-retry-invalid','Only an external connection fault can be retried here; risk/account issues are not cleared')
    rows=[r for r in state['companies'] if r['status']=='failed' and r.get('error',{}).get('code')=='connection-unavailable']
    if len(rows)!=1:raise FlowError('connection-retry-ambiguous')
    row=rows[0]
    token=hashlib.sha256((state['run_dir']+state.get('run_token',state['created_at'])+'acquire'+row['company']).encode()).hexdigest()
    path=Path(row['outdir'])/'operator'/token[:16]/'workflow.json'
    if not path.exists():raise FlowError('connection-journal-missing')
    journal=json.loads(path.read_text())
    if journal.get('work_order_id')!=token or journal.get('company')!=row['company'] or str(journal.get('groupid'))!=row['groupid']:raise FlowError('connection-journal-scope-mismatch')
    if journal.get('state')!='failed' or journal.get('error_code')!='connection-unavailable':raise FlowError('connection-journal-not-retryable')
    if journal.get('downloadPending'):raise FlowError('download-outcome-unknown','Reconcile existing download; never re-click')
    request={'kind':'connection-recovery','id':uuid.uuid4().hex,'at':now()}
    state['events'].append({'stage':'connection-retry-requested','at':now(),'company':row['company'],'request':request,'previous_error':row.get('error')})
    row.update(status='pending',recovery_request=request);row.pop('error',None)
    state['status']='running';state.pop('halt_reason',None);save(state)
    return dispatch(state)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    i=sub.add_parser('init');i.add_argument('--today');i.add_argument('--start');i.add_argument('--end');i.add_argument('--outdir');i.add_argument('--export-dir');i.add_argument('--progress-file');i.add_argument('--mapping',default=str(MAPPING));i.add_argument('--calendar',default=str(CALENDAR));i.add_argument('--force',action='store_true');i.add_argument('--rerun',action='store_true');i.add_argument('--notification-work-root',default=str(PROJECT/'work'));i.add_argument('--dispatch-order');i.add_argument('--dispatch-order-sha256');i.add_argument('--delivery-contract',choices=['three-flow-collection-ready-v1'])
    for verb in ('advance','next','status','checkpoint','record-source','process','fail','retry','repair','reverify','accept-review','roundtrip','resume','resume-connection','upgrade-identity-scope'):
        s=sub.add_parser(verb);s.add_argument('--run-dir',required=True)
        if verb in ('checkpoint','record-source','process','fail','retry','repair','reverify','accept-review'): s.add_argument('--company',required=True)
        if verb in ('checkpoint','record-source','roundtrip','accept-review'): s.add_argument('--file',required=True)
        if verb=='record-source':s.add_argument('--dom-capture');s.add_argument('--dom-capture-sha256')
        if verb=='fail': s.add_argument('--code',required=True);s.add_argument('--message',default='')
    progress=sub.add_parser('progress');progress.add_argument('--progress-file',default=str(DEFAULT_PROGRESS));progress.add_argument('--initial-start');progress.add_argument('--company')
    a=p.parse_args()
    try:
        if a.command=='progress':
            if bool(a.initial_start)!=bool(a.company):raise FlowError('progress-initialization-requires-company-and-date')
            if a.initial_start:
                selected=match_name(a.company,[r['company'] for r in load_map()])
                initialize_progress(a.progress_file,selected,a.initial_start)
            print(json.dumps({'progress_file':str(Path(a.progress_file).resolve()),**read_progress(a.progress_file)},ensure_ascii=False,indent=2));return 0
        if a.command=='init':
            dates=compute(a.today,a.start,a.end,a.force,a.calendar)
            if not dates['ok']: print(json.dumps(dates,ensure_ascii=False));return 0
            root=run_root(dates,a.outdir)
            if bool(a.dispatch_order)!=bool(a.dispatch_order_sha256):raise FlowError('init-dispatch-ref-pair-required')
            dispatch_ref={'path':a.dispatch_order,'sha256':a.dispatch_order_sha256}if a.dispatch_order else None
            _,_,scope=init_scope_inputs(dates,a.mapping,Path(a.progress_file or DEFAULT_PROGRESS).resolve(),dispatch_ref)
            init_scope_guard(root,scope,Path(a.progress_file or DEFAULT_PROGRESS).resolve(),dates,rebuild=a.rerun)
            if (root/'batch_receipt.json').is_file() and not a.rerun:
                # Only init_run's exact existing-configuration check may grant
                # recovery. It preserves the batch and never starts acquisition.
                result=init_run(dates,a.outdir,a.mapping,False,a.export_dir,a.progress_file,require_existing=True,dispatch_order=dispatch_ref,delivery_contract=a.delivery_contract)
            else:
                from notification_backlog import plan
                notification_work=Path(a.notification_work_root).resolve()
                # A validated staged dispatch already fixes prior committed cursors.
                # Its delivery belongs to the unified coordinator, not legacy outboxes.
                staged=scope is not None and a.delivery_contract=='three-flow-collection-ready-v1'
                if staged:
                    from daily_dispatch_order import validate
                    original=validate(dispatch_ref,Path(dispatch_ref['path']).parent.parent)
                    if original.get('collection_contract')!=a.delivery_contract:raise FlowError('init-dispatch-delivery-contract-conflict')
                queued={'can_acquire_new_dates':True}if staged else plan(work_root=notification_work,outbox=notification_work.parent/'runtime/daily-comment-stats/notification-outbox')
                if not queued['can_acquire_new_dates']:
                    pending=queued['next'];item=pending.get('next') or {}
                    print(json.dumps({'ok':False,'action':'resolve-notification-backlog','error':{'code':'notification-backlog-pending','message':'Finish original notification jobs before creating another daily run'},'outbox':pending['outbox'],'next_action':item.get('action'),'job_path':item.get('job_path'),'gate_command':['notification_backlog.py','gate','--work-root',str(notification_work)]},ensure_ascii=False,indent=2));return 3
                result=init_run(dates,a.outdir,a.mapping,a.rerun,a.export_dir,a.progress_file,dispatch_order=dispatch_ref,delivery_contract=a.delivery_contract)
        else:
            with lock(a.run_dir):
                state=load_state(a.run_dir);row=get_company(state,a.company) if hasattr(a,'company') else None
                try:
                    if state['status']=='halted' and a.command not in ('status','next','advance','resume','resume-connection'):
                        raise FlowError('batch-halted','Manually resolve risk/account issue, then explicitly resume')
                    if a.command=='advance':result=advance(state)
                    elif a.command=='next':
                        result=dispatch(state)
                        if result['action']=='done': state['status']='complete_with_failures' if state['failed'] else 'needs_review' if state['needs_review'] else 'complete';save(state)
                    elif a.command=='status': result=state
                    elif a.command=='upgrade-identity-scope':result=upgrade_identity_scope(state)
                    elif a.command=='checkpoint': checkpoint(state,row,json.loads(Path(a.file).read_text()));result=row
                    elif a.command=='record-source':
                        if bool(a.dom_capture)!=bool(a.dom_capture_sha256):raise FlowError('dom-capture-ref-pair')
                        record_source(state,row,json.loads(Path(a.file).read_text()),capture_ref={'path':a.dom_capture,'sha256':a.dom_capture_sha256}if a.dom_capture else None);result=row
                    elif a.command=='fail': fail_company(state,row,a.code,a.message);result=row
                    elif a.command=='retry':
                        if state['status']=='halted': raise FlowError('batch-halted','Resolve and use explicit resume after manual verification')
                        if row['status']!='failed': raise FlowError('retry-invalid','Retry is only for failed companies; use repair for changed outputs')
                        row['status']='pending';row.pop('error',None);save(state);result=row
                    elif a.command=='repair':
                        if not row.get('receipt'): raise FlowError('repair-unavailable')
                        row['status']='acquired' if Path(row.get('source','')).is_file() and Path(row.get('evidence','')).is_file() else 'pending'
                        state['status']='running';save(state);result=next_task(state)
                    elif a.command=='resume-connection':result=request_connection_retry(state)
                    elif a.command=='resume':
                        # This only clears the control stop, never authenticates or bypasses a challenge.
                        if state['status']=='halted': state['status']='running';state['events'].append({'stage':'manual-resume','at':now()});save(state)
                        result=next_task(state)
                    elif a.command=='reverify':result=reverify(state,row)
                    elif a.command=='accept-review':result=accept_review(state,row,json.loads(Path(a.file).read_text()))
                    elif a.command=='roundtrip':
                        data=json.loads(Path(a.file).read_text());first=get_company(state,state['roundtrip'].get('target_company') or state['companies'][0]['company'])
                        if not data.get('verified') or data.get('company')!=first['company'] or str(data.get('groupid'))!=first['groupid']: raise FlowError('roundtrip-unverified')
                        previous_status=first['status']
                        checkpoint(state,first,{'stage':'return-company','groupid':first['groupid'],'identity':data.get('identity')})
                        # Do not overwrite the first company's processing outcome.
                        first['status']=previous_status
                        state['roundtrip']={'required':True,'verified':True,'target_company':first['company'],'at':now()};save(state);result=state['roundtrip']
                    else:
                        if row['status']!='acquired': raise FlowError('source-not-recorded')
                        evidence=json.loads(Path(row['evidence']).read_text())
                        result=process(row['source'],row,company_dates(state,row),row['outdir'],state['mapping_path'],evidence['page_filtered'],evidence,capture_ref=row.get('dom_capture'),company_policy=state.get('dispatch_scope',{}).get('active_company_policy'))
                        row.update(status=result['status'],receipt=result['receipt']);save(state);update_progress(state,row)
                        if result.get('error',{}).get('fatal'):fail_company(state,row,result['error']['code'],result['error']['message'])
                except FlowError as e:
                    if e.fatal: fail_company(state,row or state['companies'][0],e.code,str(e))
                    raise
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 1 if result.get('status')=='failed' else 0
    except (FlowError,ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':{'code':getattr(e,'code','configuration-error'),'message':str(e)}},ensure_ascii=False));return 2


_policy_original_main=main
def main(*args,**kwargs):
    sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
    import execution_timing as timing
    with timing.company_policy_command(),__import__('ds_common').dom_command():return _policy_original_main(*args,**kwargs)

if __name__=='__main__': raise SystemExit(main())


from ds_common import dom_command_function
record_dom_source=dom_command_function(record_dom_source)
advance=dom_command_function(advance)


def _work_order_repair_raw(reference):
    path=Path(reference['path'])
    if not path.is_absolute()or path.resolve()!=path or not path.is_file()or any(p.is_symlink()for p in(path,*path.parents)):raise FlowError('work-order-repair-source-origin')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=reference['sha256']:raise FlowError('work-order-repair-source-drift')
    return raw

def _work_order_repair_ref(path):
    path=Path(path);return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def plan_immutable_work_order_repair(inputs,read_raw=_work_order_repair_raw):
    """Resume-only regression repair, never a new company/download operation."""
    if set(inputs)!={'batch','original_archive','changed_job','workflow','advance_exit','advance_request'}:raise FlowError('work-order-repair-input-schema')
    values={k:json.loads(read_raw(r))for k,r in inputs.items()};batch=values['batch'];old=values['original_archive'];bad=values['changed_job'];wf=values['workflow'];exit=values['advance_exit'];request=values['advance_request']
    if {k:v for k,v in bad.items()if k!='resume'}!={k:v for k,v in old.items()if k!='resume'}or old.get('resume')==bad.get('resume'):raise FlowError('work-order-repair-resume-only')
    if old.get('company_configuration_registry')!='configured-source-index-v2'or old.get('action')!='acquire'or bad.get('work_order_path')!=inputs['changed_job']['path']or bad.get('workflow_path')!=inputs['workflow']['path']:raise FlowError('work-order-repair-configured-original')
    canonical_old={'path':bad['work_order_path'],'sha256':inputs['original_archive']['sha256']}
    if wf.get('company_configuration_job')!=canonical_old or wf.get('work_order_id')!=old['work_order_id']or wf.get('company')!=old['company']or str(wf.get('groupid'))!=str(old['groupid'])or wf.get('date_range')!={k:old['date_range'][k]for k in('start','end')}:raise FlowError('work-order-repair-journal-binding')
    if not wf.get('calls')or any(c.get('state')!='confirmed'for c in wf['calls']):raise FlowError('work-order-repair-input-unknown')
    # The journal, original export/download intent/ticket and all keys are facts
    # only. This repair changes none and cannot repeat their effects.
    row=next((r for r in batch['companies']if r['company']==old['company']and str(r['groupid'])==str(old['groupid'])),None)
    if row is None or str(Path(old['workflow_path']).parents[3])!=batch['run_dir']or row['date_range']['start']!=old['date_range']['start']or row['date_range']['end']!=old['date_range']['end']:raise FlowError('work-order-repair-batch-company-date')
    resume=bad['resume'];prefix=resume.get('checkpoints')
    if set(resume)!={'latest','checkpoints','export_pending','attempts'}or type(resume.get('attempts'))is not int or type(resume.get('export_pending'))is not bool or not isinstance(prefix,list)or row['checkpoints'][:len(prefix)]!=prefix or resume['latest']!=(prefix[-1]if prefix else None):raise FlowError('work-order-repair-derived-prefix')
    by_id={c.get('event_id'):c for c in wf.get('checkpoints',[])if c.get('event_id')}
    for checkpoint in prefix:
        source=by_id.get(checkpoint.get('event_id'))
        if source is None or {k:v for k,v in source.items()if k!='at'}!={k:v for k,v in checkpoint.items()if k!='at'}:raise FlowError('work-order-repair-checkpoint-origin')
    attempts=sum(c['stage']=='export-intent'for c in prefix);pending=False
    for checkpoint in prefix:
        if checkpoint['stage']=='export-intent':pending=True
        elif checkpoint['stage']=='export-failed':pending=False
    if resume['attempts']!=attempts or resume['export_pending']is not pending:raise FlowError('work-order-repair-derived-export-state')
    if exit.get('returncode')!=0 or exit.get('argv',[None,None,None])[2]!='advance'or request.get('kind')!='workshop-worker-request-v1'or request['context']['operator']['work_order']!=canonical_old or request['context'].get('stage')!='advance':raise FlowError('work-order-repair-original-advance')
    offer_ref=request['context']['offer'];offer=json.loads(read_raw(offer_ref));parent=offer.get('daily_execution',{})
    if parent.get('order')!=request['context']['order']or offer.get('workflow')!=request['task']['flow']or offer.get('active_day')!=request['task']['day']or exit['argv']!=parent.get('commands',{}).get('advance',[])+['--tab-id',str(request['context']['scope']['tab_id'])]or Path(inputs['advance_exit']['path']).parent!=Path(inputs['advance_request']['path']).parent or Path(exit['stdout']['path']).parent!=Path(inputs['advance_request']['path']).parent:raise FlowError('work-order-repair-canonical-parent-advance')
    output=json.loads(read_raw(exit['stdout']));handoff=output.get('child_result',{}).get('handoff',{})
    if handoff.get('work_order')!=inputs['changed_job']or handoff.get('action')!='acquire'or output.get('child_result',{}).get('run_dir')!=batch['run_dir']or handoff.get('argv')!=request['context']['operator']['argv']:raise FlowError('work-order-repair-returned-handoff')
    if request['context']['order']!=batch.get('dispatch_scope',{}).get('work_order'):raise FlowError('work-order-repair-original-order')
    return {'kind':'verified-resume-only-original-work-order-repair-v1','inputs':inputs,'canonical_original':canonical_old,'changed_job':inputs['changed_job'],'workflow':inputs['workflow'],'task_id':request['task']['id'],'outer':request['task']['outer'],'order':request['context']['order'],'materials':[*[inputs[k]for k in sorted(inputs)],exit['stdout'],offer_ref],'new_inputs':0,'workflow_unchanged':True}

def verify_immutable_work_order_repair(proof_ref,*,current_job=True):
    proof=json.loads(_work_order_repair_raw(proof_ref))
    if set(proof)!={'kind','facts','archives','module'}or proof['kind']!='verified-resume-only-original-work-order-repair-v1':raise FlowError('work-order-repair-proof-schema')
    if proof['module']!=_work_order_repair_ref(Path(__file__).resolve()):raise FlowError('work-order-repair-module')
    changed=proof['facts']['changed_job'];expected=Path(changed['path']).parent/'immutable-work-order-repairs'/changed['sha256']/'proof.json'
    if proof_ref['path']!=str(expected):raise FlowError('work-order-repair-proof-location')
    mapping={}
    for pair in proof['archives']:
        original,archive=pair['original'],pair['archive']
        if archive['sha256']!=original['sha256']or archive['path']!=str(Path(proof_ref['path']).parent/'materials'/(original['sha256']+'.data')):raise FlowError('work-order-repair-archive')
        mapping[(original['path'],original['sha256'])]=archive
    def raw(reference):return _work_order_repair_raw(mapping[(reference['path'],reference['sha256'])])
    facts=plan_immutable_work_order_repair(proof['facts']['inputs'],raw)
    if facts!=proof['facts']:raise FlowError('work-order-repair-derived-facts')
    if current_job and _work_order_repair_ref(Path(facts['canonical_original']['path']))!=facts['canonical_original']:raise FlowError('work-order-repair-current-original')
    return facts

def repair_immutable_work_order(inputs,*,guard):
    """Caller holds original four locks. Exact bytes restored, no WF/task edits."""
    if not callable(guard):raise FlowError('work-order-repair-locked-guard-required')
    guard('preflight');target=Path(inputs['changed_job']['path']);base=target.parent/'immutable-work-order-repairs'/inputs['changed_job']['sha256'];proof_path=base/'proof.json'
    immutable_bytes=_work_order_repair_immutable
    if proof_path.exists():
        proof_ref=_work_order_repair_ref(proof_path);facts=verify_immutable_work_order_repair(proof_ref,current_job=False)
        if facts['inputs']!=inputs:raise FlowError('work-order-repair-reentry-inputs')
        original_bytes=_work_order_repair_raw(next(p['archive']for p in json.loads(_work_order_repair_raw(proof_ref))['archives']if p['original']==inputs['original_archive']))
    else:
        facts=plan_immutable_work_order_repair(inputs);base.mkdir(parents=True,exist_ok=True);archives=[]
        for reference in facts['materials']:
            archive=immutable_bytes(base/'materials'/(reference['sha256']+'.data'),_work_order_repair_raw(reference));archives.append({'original':reference,'archive':archive})
        intent=immutable_bytes(base/'intent.json',(json.dumps({'kind':facts['kind'],'inputs':inputs,'module':_work_order_repair_ref(Path(__file__).resolve())},sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode())
        proof={'kind':facts['kind'],'facts':facts,'archives':archives,'module':_work_order_repair_ref(Path(__file__).resolve())};proof_ref=immutable_bytes(proof_path,(json.dumps(proof,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode());original_bytes=_work_order_repair_raw(inputs['original_archive'])
    guard('before-CAS')
    if _work_order_repair_ref(target)==inputs['changed_job']:
        if _work_order_repair_ref(Path(inputs['workflow']['path']))!=inputs['workflow']:raise FlowError('work-order-repair-WF-raced')
        tmp=target.with_name(target.name+'.immutable-restore-'+uuid.uuid4().hex);immutable_bytes(tmp,original_bytes)
        if _work_order_repair_ref(target)!=inputs['changed_job']:raise FlowError('work-order-repair-CAS-raced')
        guard('replace');os.replace(tmp,target)
        fd=os.open(target.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    facts=verify_immutable_work_order_repair(proof_ref);guard('readback');return {'state':'restored','original_job':facts['canonical_original'],'proof':proof_ref,'new_inputs':0,'workflow_unchanged':True}


def _work_order_repair_immutable(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data:raise FlowError('work-order-repair-immutable-conflict')
    else:
        with path.open('xb')as output:output.write(data);output.flush();os.fsync(output.fileno())
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    return _work_order_repair_ref(path)
