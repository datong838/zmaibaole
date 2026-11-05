#!/usr/bin/env python3
"""Independent history-only workspace: verified normal source -> existing results -> case memory.
No new complaint, screenshot, message, draft, Excel, or business-cursor capability.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse
import copy
import hashlib
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import authoritative_join as authority
import case_memory as memory_api
import existing_result_runner as runner
import normal_observation as normal
import prepare_result_orders as orders_api
import workflow

KIND = 'negative-review-appeal-history-only-v1'
DOMAIN = 'negative-review-appeal-cases'
READ_ACTIONS = ('查看投诉结果', '投诉审核中')
FORBIDDEN = ('next_start', 'initial_start', 'covered_through', 'last_completed_on', 'batches')
CAPABILITIES = {'read_existing_results': True, 'new_complaint': False, 'analyze': False,
                'screenshot': False, 'send': False, 'submit': False, 'advance_business_cursor': False}
need = workflow.require
ref = orders_api.ref
document = orders_api.document


def checked_ref(path, checksum):
    p = Path(path)
    need(p.is_absolute() and p.is_file() and not p.is_symlink(), 'history-explicit-input-path-required')
    r = {'path': str(p.resolve()), 'sha256': checksum}
    document(r)
    return r


def load(root):
    state = workflow.load(Path(root))
    need(state.get('workspace_kind') == KIND and state.get('domain') == DOMAIN and state.get('mode') == 'draft-only', 'history-only-workspace-required')
    need(state.get('capabilities') == CAPABILITIES and state.get('browser_backend') == 'local-dom-bridge', 'history-capabilities-invalid')
    need(not any(k in state for k in FORBIDDEN), 'history-business-progress-forbidden')
    need(authority.identity(state.get('identity')) and str(state.get('groupid', '')).isdigit(), 'history-identity-invalid')
    need(state.get('binding_sha256') == authority.data_hash(state['binding']), 'history-init-binding-changed')
    for key in ('company', 'groupid', 'identity', 'history_range'):
        need(state.get(key) == state['binding'].get(key), 'history-init-scope-changed')
    for task in state.get('tasks', {}).values():
        need(task.get('action') in READ_ACTIONS and not any(task.get(k) for k in ('analysis', 'wecom', 'screenshot')), 'history-non-readonly-task-forbidden')
    receipt = document(state['identity_receipt'])
    need(state['identity_receipt']['sha256'] == state['binding']['identity_receipt']['sha256'] and receipt.get('company') == state['company'] and str(receipt.get('groupid')) == state['groupid'] and receipt.get('identity') == receipt.get('identity_before') == state['identity'] and receipt.get('account_verified') is True and receipt.get('operator_skill') == 'douyin-laike-operator', 'history-pinned-identity-receipt-changed')
    return state


def _save(root, state, event):
    need(not any(k in state for k in FORBIDDEN), 'history-business-progress-forbidden')
    state['events'].append({'at': workflow.now(), **event})
    state['updated_at'] = workflow.now()
    workflow.atomic(Path(root) / 'state.json', state)
    return state


def initialize(root, company, gid, start, end_exclusive, identity_receipt, *, today=None):
    import prepare_company_navigation as company_api
    root = Path(root)
    need(root.is_absolute() and not root.is_symlink(), 'history-explicit-root-required')
    root = root.resolve()
    day = today or datetime.now(memory_api.ZONE).date().isoformat()
    need(date.fromisoformat(start) < date.fromisoformat(end_exclusive) <= date.fromisoformat(day), 'history-date-range-invalid')
    original, raw, journal_ref = company_api.receipt(identity_receipt)
    need(original['company'] == company and str(original['groupid']) == str(gid) and original['backend'] == 'local-dom-bridge', 'history-identity-receipt-scope-mismatch')
    binding = {'company': company, 'groupid': str(gid), 'identity': original['identity'],
               'history_range': {'start': start, 'end_exclusive': end_exclusive}, 'identity_receipt': identity_receipt}
    with workflow.locked(root):
        if (root / 'state.json').exists():
            state = load(root)
            need(state['binding'] == binding, 'history-existing-binding-conflict')
            return state
        need(not any(p.name != '.lock' for p in root.iterdir()), 'history-root-must-be-new-not-copied-ledger')
        owned = workflow.evidence(root, identity_receipt['path'])
        state = {'version': 1, 'workspace_kind': KIND, 'domain': DOMAIN, 'mode': 'draft-only',
                 'browser_backend': 'local-dom-bridge', 'capabilities': CAPABILITIES.copy(),
                 **{k: binding[k] for k in ('company', 'groupid', 'identity', 'history_range')},
                 'binding': binding, 'binding_sha256': authority.data_hash(binding), 'identity_receipt': owned,
                 'original_identity_journal': journal_ref, 'tasks': {}, 'sources': {}, 'prior_operations': [], 'events': []}
        return _save(root, state, {'type': 'history-initialized', 'not_business_completion': True})


def _inputs(state, refs):
    need(set(refs) == {'job', 'source', 'envelope', 'profile'}, 'history-four-pinned-inputs-required')
    values = {k: document(r) for k, r in refs.items()}
    job, source = values['job'], values['source']
    need(job.get('company') == source.get('company') == state['company'] and str(job.get('groupid')) == str(source.get('groupid')) == state['groupid'], 'history-source-company-mismatch')
    need(job.get('identity') == source.get('identity') == state['identity'] and job.get('account_verified') is True, 'history-source-identity-mismatch')
    a, b = job['start'], job['end_exclusive']
    need(state['history_range']['start'] <= a < b <= state['history_range']['end_exclusive'], 'history-source-outside-range')
    need(source.get('start') == a and source.get('end_exclusive') == b and source.get('source') == 'local-dom-bridge', 'history-source-date-backend-mismatch')
    if source.get('kind')=='history-partial-normal-source-v1':
        from normal_paging import partial_history_source
        need(source.get('coverage')=='needs-review'and source.get('all_normal_read')is False and source.get('new_complaint_authorized')is False,'history-partial-source-claims')
        reconstructed=partial_history_source(job,values['envelope'],values['profile'],{'path':job['source_receipt'],'sha256':job['source_receipt_sha256']},expected_source=source,expected_source_ref=refs['source'])
    else:reconstructed=normal.joined(job,values['envelope'],values['profile'],job['source_receipt'],job['source_receipt_sha256'])
    need(reconstructed==source,'history-current-source-not-reproducible')
    profile=values['profile']
    if profile.get('pagination_mode')=='count-complete' and profile.get('scope_mode') not in ('verified-empty-normal-list','verified-complete-normal-list'):
        # Historical reconstruction stays byte-identical. A NEW history source
        # cannot promote the old count-only shortcut to monthly page coverage.
        pages=values['envelope']['pages'];need(len(pages)==1,'history-single-page-proof-required')
        proof=normal.navigation_probe(pages[0]['tree'],job,text_schema=profile.get('text_schema'))
        need(proof.get('pagination')=='1/1' and proof.get('normal_count')==source['filtered_count'],'history-current-single-page-proof-required')
    need(all(r.get('section') == 'filtered' and r.get('action') in ('投诉', *READ_ACTIONS) for r in source['rows']), 'history-source-unreviewed-row')
    return values


def ingest(root, refs):
    root = Path(root).resolve()
    with workflow.locked(root):
        state = load(root)
        values = _inputs(state, refs)
        source = values['source']; checksum = refs['source']['sha256']
        if checksum in state['sources']:
            need(state['sources'][checksum]['original_inputs'] == refs, 'history-existing-source-binding-conflict')
            return state
        a, b = source['start'], source['end_exclusive']
        partial=source.get('kind')=='history-partial-normal-source-v1'
        overlaps=[v for v in state['sources'].values()if v['start']<b and a<v['end_exclusive']]
        need(not overlaps or partial and all(v.get('partial_evidence')is True and v['original_inputs']['job']==refs['job']for v in overlaps),'history-source-ranges-overlap')
        owned = {k: workflow.evidence(root, r['path']) for k, r in refs.items()}
        for k in refs:
            need(owned[k]['sha256'] == refs[k]['sha256'], 'history-input-changed-during-copy')
        ids, skipped = [], []
        for row in source['rows']:
            key = state['groupid'] + ':' + row['review_id']
            if row['action'] == '投诉':
                skipped.append(key)
                continue
            if key in state['tasks']and partial:
                old=state['tasks'][key];need(old['action']==row['action']and old['review']=={k:row.get(k,'')for k in('review_id','store','customer','text','stars','date','product')},'history-partial-existing-review-changed');ids.append(key);continue
            need(key not in state['tasks'], 'history-duplicate-task')
            ids.append(key)
            state['tasks'][key] = {'id': key, 'review': {k: row.get(k, '') for k in ('review_id', 'store', 'customer', 'text', 'stars', 'date', 'product')},
                                   'action': row['action'], 'status': 'existing_pending', 'snapshot': owned['source'],
                                   'latest_snapshot': owned['source'], 'screenshot': None, 'wecom': None, 'analysis': None,
                                   'history': None, 'result': None, 'updated_at': workflow.now()}
            if row.get('body_kind'):
                import normal_review_body as rb
                state['tasks'][key]['body_provenance']=rb.provenance(row)
        state['sources'][checksum] = {'start': a, 'end_exclusive': b, 'inputs': owned, 'original_inputs': refs,
                                     'normal_count': len(source['rows']), 'existing_ids': ids, 'skipped_uncomplained_ids': skipped,**({'partial_evidence':True,'coverage':'needs-review','pending_records':source['delivery']['pending_records']}if partial else{})}
        return _save(root, state, {'type': 'history-source-verified', 'source_sha256': checksum,
                                   'existing_results': len(ids), 'uncomplained_skipped': len(skipped)})


def prepare_acquisition(root, identity_receipts):
    """Generate a separate standard operator order; never executes the export."""
    import prepare_company_navigation as company_api
    from role_cli import validate_job
    root = Path(root).resolve()
    with workflow.locked(root):
        state = load(root); known = {}; originals = []
        need(not state.get('completed_acquisition_adoption') and not (root/'completed-acquisition-adoption.json').exists() and not (root/'completed-acquisition-adoption.json').is_symlink(),'history-source-already-adopted-use-normal-job')
        need(isinstance(identity_receipts,list) and identity_receipts,'history-acquisition-identities-required')
        identity_receipts=sorted(identity_receipts,key=lambda r:(r['path'],r['sha256']))
        need(len({(r['path'],r['sha256']) for r in identity_receipts})==len(identity_receipts),'history-acquisition-duplicate-identity-input')
        for reference in identity_receipts:
            value, raw, journal = company_api.receipt(reference)
            gid = str(value['groupid']); identity = value['identity']
            need(identity['provider'] == state['identity']['provider'] and (gid not in known or known[gid] == identity), 'history-acquisition-known-identity-conflict')
            known[gid] = identity
            owned = workflow.evidence(root, reference['path']); need(owned['sha256'] == reference['sha256'], 'history-acquisition-receipt-changed')
            originals.append({'original':reference, 'snapshot':owned, 'journal':journal})
        need(len(known) >= 1 and known.get(state['groupid']) == state['identity'], 'history-acquisition-target-identity-required')
        binding = {'kind':'history-source-acquisition-binding-v1','history_root':str(root),'workspace_binding':state['binding_sha256'],'identity_inputs':originals,'known_company_identities':known}
        existing=list((root/'acquisition').glob('*/prepare-manifest.json'))
        if existing:
            need(len(existing)==1,'history-acquisition-multiple-orders-forbidden')
            saved=workflow.read(existing[0]);need(saved['binding']==binding,'history-acquisition-original-order-required');document(saved['work_order'])
            return saved
        work_id = authority.data_hash(binding); folder = root/'acquisition'/work_id[:16]; folder.mkdir(parents=True,exist_ok=True)
        first,exclusive = state['history_range']['start'],state['history_range']['end_exclusive']
        job = {'action':'acquire','backend':'local-dom-bridge','company':state['company'],'groupid':state['groupid'],
               'date_range':{'ok':True,'start':first,'end':(date.fromisoformat(exclusive)-timedelta(days=1)).isoformat(),'end_exclusive':exclusive,'mode':'explicit-history','warnings':[]},
               'work_order_id':work_id,'work_order_path':str(folder/'work-order.json'),'workflow_path':str(folder/'workflow.json'),
               'source_dir':str(root/'exports'),'output_dir':str(folder),'operator_skill':'douyin-laike-operator',
               'identity_contract':'merchant-v2','provider_baseline':state['identity']['provider'],'identity_baseline':state['identity'],
               'known_company_identities':known,'identity_bootstrap':False,'allowed_groupids':sorted(known),
               'explicit_tab_id_required':True,'source_purpose':'negative-review-appeal-history-only',
               'progress_updates_enabled':False,'send_enabled':False,'submit_enabled':False}
        validate_job(job)
        output = folder/'work-order.json'; manifest = folder/'prepare-manifest.json'
        if output.exists(): need(workflow.read(output)==job,'history-acquisition-existing-order-conflict')
        else: workflow.atomic(output,job)
        prepared = {'ok':True,'binding':binding,'work_order':ref(output),'acquisition_receipt_expected':str(folder/'acquisition.json'),
                    'prepare_argv':[sys.executable,str(Path(__file__).resolve().parents[2]/'douyin-laike-operator/scripts/role_cli.py'),'prepare','--work-order',str(output),'--tab-id','FRESH_VERIFIED_EXISTING_TAB_ID'],
                    'finalize_argv':[sys.executable,str(Path(__file__).resolve().parents[2]/'douyin-laike-operator/scripts/role_cli.py'),'finalize','--work-order',str(output),'--journal',job['workflow_path'],'--out',str(folder/'acquisition.json')],
                    'journal_path':job['workflow_path'],'export_executed':False,'business_cursor_updated':False,'ui_used':False}
        if manifest.exists(): need(workflow.read(manifest)==prepared,'history-acquisition-existing-manifest-conflict')
        else: workflow.atomic(manifest,prepared)
        return prepared


def prepare_normal_job(root, acquisition_receipt, out, *, completed_acquisition_adoption_ref=None):
    """Bind a completed monthly acquisition before collecting actual normal DOM."""
    import prepare_company_navigation as company_api
    root=Path(root).resolve();state=load(root);value,raw,journal=company_api.receipt(acquisition_receipt)
    need(value['company']==state['company'] and str(value['groupid'])==state['groupid'] and value['identity']==state['identity'],'history-normal-job-identity-mismatch')
    first,exclusive=state['history_range']['start'],state['history_range']['end_exclusive']
    need(value['date_range']=={'start':first,'end':(date.fromisoformat(exclusive)-timedelta(days=1)).isoformat()},'history-normal-job-exact-range-required')
    manifests=list((root/'acquisition').glob('*/prepare-manifest.json'))
    matched=[workflow.read(p) for p in manifests if workflow.read(workflow.read(p)['work_order']['path'])['work_order_id']==value['work_order_id']]
    if state.get('completed_acquisition_adoption') or completed_acquisition_adoption_ref is not None:
        need(completed_acquisition_adoption_ref==state.get('completed_acquisition_adoption') and completed_acquisition_adoption_ref is not None and not matched,'history-adopted-source-explicit-only-no-second-prepare')
        from history_completed_acquisition import validate as validate_adopted
        validate_adopted(root,state,completed_acquisition_adoption_ref,acquisition_receipt)
    else:
        need(len(matched)==1,'history-normal-job-owned-acquisition-required');document(matched[0]['work_order'])
    job={'company':state['company'],'groupid':state['groupid'],'start':first,'end_exclusive':exclusive,
         'account_verified':True,'identity':state['identity'],'source_work_order_id':value['work_order_id'],
         'source_receipt':acquisition_receipt['path'],'source_receipt_sha256':acquisition_receipt['sha256']}
    out=Path(out).resolve();need(root in out.parents,'history-normal-job-output-must-be-owned')
    if out.exists():need(workflow.read(out)==job,'history-normal-job-output-conflict')
    else:workflow.atomic(out,job)
    return {'ok':True,'job':ref(out),'ui_used':False,'profile_status':'requires-real-normal-page-validation'}


@__import__('normal_paging').partial_source_command
def prepare(root, key):
    root = Path(root).resolve()
    with workflow.locked(root):
        state = load(root); task = state['tasks'].get(key)
        need(task is not None and task['action'] in READ_ACTIONS, 'history-existing-result-only')
        checksum = task['latest_snapshot']['sha256']; inputs = state['sources'][checksum]['inputs']; values = _inputs(state, inputs)
        rows = [r for r in values['source']['rows'] if state['groupid'] + ':' + r['review_id'] == key]
        need(len(rows) == 1 and rows[0]['action'] in READ_ACTIONS, 'history-existing-result-only')
        index = rows[0].get('page_index'); need(type(index) is int and 1 <= index <= len(values['envelope']['pages']), 'history-source-page-required')
        folder = root / 'read-orders' / checksum
        folder.mkdir(parents=True, exist_ok=True)
        order_path = folder / 'orders.json'
        if values['source'].get('kind')=='history-partial-normal-source-v1':
            source=values['source'];orders=[]
            for r in source['rows']:
                need(r['action']in READ_ACTIONS,'history-partial-only-existing-results');orders.append({'review_key':state['groupid']+':'+r['review_id'],'snapshot_sha256':inputs['source']['sha256'],'card_selector':r['dom_selector'],'original_action':r['action'],'source_tuple':{k:r[k]for k in('review_id','store','customer','text','stars','date')},'allowed_actions':list(READ_ACTIONS),'click_kind':'complaint-read','never_click':['投诉','再次投诉','提交']})
            order={'kind':'existing-complaint-result-orders-v1','inputs':inputs,'company':source['company'],'groupid':source['groupid'],'range':{k:source[k]for k in('start','end_exclusive')},'orders':orders,'submission_enabled':False,'send_enabled':False}
            if order_path.exists():need(workflow.read(order_path)==order,'history-partial-orders-conflict')
            else:workflow.atomic(order_path,order)
        else:orders_api.prepare(*(inputs[k]['path'] for k in ('job','source','envelope','profile')),order_path)
        page_path = folder / ('source-page-' + str(index) + '.json')
        raw = values['envelope']['pages'][index - 1]
        if page_path.exists(): need(workflow.read(page_path) == raw, 'history-source-page-changed')
        else: workflow.atomic(page_path, raw)
        paths = {k: inputs[k]['path'] for k in ('job', 'source', 'profile', 'envelope')}
        paths.update(page=page_path, orders=order_path)
        output = folder / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        manifest = runner.prepare(root, paths, key, output)
        return {'ok': True, 'manifest': ref(output), 'review_key': key, 'ui_used': False,
                'run_argv': [sys.executable, str(Path(__file__).resolve()), 'run', '--manifest', str(output), '--steps', '10']}


def record_result(root, key, path, *, memory=None):
    root = Path(root).resolve()
    with workflow.locked(root):
        state = load(root); task = state['tasks'].get(key)
        need(task is not None and task['action'] in READ_ACTIONS, 'history-existing-result-only')
        result = workflow.read(path)
        need(result.get('snapshot_sha256') == task['latest_snapshot']['sha256'], 'history-result-source-mismatch')
        source = document(task['latest_snapshot'])
        memory_api._facts(source, result, key)
        need(authority.stamp(result['observed_at']) >= authority.stamp(source['observed_at']), 'history-result-before-source')
        previous = task.get('result')
        if not previous or {k: v for k, v in previous.items() if k != 'evidence'} != result:
            task['result'] = {**result, 'evidence': workflow.evidence(root, path)}
            task['status'] = 'resolved' if result['status'] in ('accepted', 'rejected') else 'existing_pending'
            task['updated_at'] = workflow.now()
            _save(root, state, {'type': 'history-existing-result-read', 'id': key, 'status': result['status']})
        kwargs = {} if memory is None else {'memory': memory}
        imported = memory_api.auto_import(root, key, **kwargs)
        if imported.get('appended'):
            out = memory_api.SKILL / 'references/投诉案例记忆.md' if memory is None else Path(memory).parent / 'references/投诉案例记忆.md'
            memory_api.render_document(out, **kwargs)
        return imported


def _prior(proof, state, *, row=None):
    need(proof.get('kind') == 'history-prior-verified-complete-v1', 'history-prior-kind-invalid')
    operation = document(proof['operation']); manifest = operation['manifest']
    values, order, prior_row = runner.manifest_inputs(manifest, historical_complete=True)
    runner.verify_complete(operation, manifest, values, order, prior_row)
    legacy = document(proof['legacy'])
    need(manifest.get('completed_operation') == proof['legacy'] and legacy.get('state') == 'complete' and legacy.get('review_key') == manifest['review_key'] and legacy.get('source_sha256') == manifest['inputs']['source']['sha256'], 'history-prior-legacy-not-verified-adoption')
    need(proof.get('review_key') == manifest['review_key'] and manifest['review_key'].startswith(state['groupid'] + ':'), 'history-prior-review-key-mismatch')
    job = values['job']
    need(job['company'] == state['company'] and str(job['groupid']) == state['groupid'] and job['identity'] == state['identity'], 'history-prior-company-identity-mismatch')
    need(state['history_range']['start'] <= prior_row['date'] < state['history_range']['end_exclusive'], 'history-prior-review-outside-range')
    if row is not None:
        need(all(row.get(k) == prior_row.get(k) for k in ('review_id','store','customer','text','stars','date','product')), 'history-prior-current-review-tuple-changed')
    return {'review_key': manifest['review_key'], 'legacy': proof['legacy'], 'operation': proof['operation'],
            'source': manifest['inputs']['source'], 'use': 'closed-prior-audit-only; never substitutes current monthly source or result read'}


def pin_prior(root, operation, legacy):
    root = Path(root).resolve()
    with workflow.locked(root):
        state = load(root); old = document(operation)
        proof = {'kind':'history-prior-verified-complete-v1', 'review_key':old['manifest']['review_key'], 'operation':operation, 'legacy':legacy}
        _prior(proof, state)
        matches = [p for p in state['prior_operations'] if p['legacy']['path'] == legacy['path']]
        if matches:
            need(matches == [proof], 'history-prior-binding-conflict')
        else:
            state['prior_operations'].append(proof)
            _save(root,state,{'type':'history-prior-complete-pinned','id':proof['review_key'],'proof':proof})
        return {'ok':True,'proof':proof,'ui_used':False}


def verify_prior_for_legacy(state, key, legacy, row):
    need(state.get('workspace_kind') == KIND, 'history-prior-only-in-history-workspace')
    matches = [p for p in state.get('prior_operations',[]) if p.get('review_key') == key and p.get('legacy') == legacy]
    need(len(matches) == 1,'history-prior-complete-proof-required')
    return _prior(matches[0],state,row=row)


@__import__('normal_paging').partial_source_command
def run(manifest_path, *, steps=1, request=None, memory=None):
    need(type(steps) is int and 1 <= steps <= 10, 'history-steps-invalid')
    manifest = workflow.read(manifest_path)
    state = load(manifest['root']); need(manifest['review_key'] in state['tasks'], 'history-review-not-owned')
    task = state['tasks'][manifest['review_key']]
    need(task['action'] in READ_ACTIONS and manifest['inputs']['source'] == task['latest_snapshot'], 'history-manifest-task-source-mismatch')
    profile = runner.document(manifest['inputs']['profile'])
    if profile.get('contract') == 'normal-negative-pages-until-observed-fold-boundary-v1':
        from normal_case_journey import ensure_for_result
        route = ensure_for_result(manifest_path, request=request)
        if route['state'] != 'complete':
            return {**route, 'ok':False, 'review_key':manifest['review_key'], 'result':None}
    for _ in range(steps):
        output = runner.tick(manifest, request=request, record=lambda root,key,path:record_result(root,key,path,memory=memory))
        if output['state'] == 'complete':
            operation = ref(output['operation'])
            with workflow.locked(manifest['root']) as root:
                state = load(root); task = state['tasks'][manifest['review_key']]
                if task.get('completed_operation') != operation:
                    task['completed_operation'] = operation
                    _save(root, state, {'type': 'history-reader-closed', 'id': manifest['review_key'], 'operation': operation})
            break
    return output


def verify_coverage(root, *, memory=None):
    root = Path(root).resolve(); state = load(root); cursor = state['history_range']['start']; missing = []
    for entry in sorted(state['sources'].values(), key=lambda x: x['start']):
        _inputs(state, entry['inputs'])
        if entry.get('partial_evidence'):
            missing.append('partial-evidence-never-date-coverage:'+entry['inputs']['source']['sha256']);continue
        need(entry['start'] == cursor, 'history-date-coverage-gap')
        cursor = entry['end_exclusive']
        for key in entry['existing_ids']:
            task = state['tasks'][key]
            if not task.get('result') or not task.get('completed_operation'):
                missing.append(key); continue
            operation = document(task['completed_operation']); manifest = operation['manifest']
            need(manifest['root'] == str(root) and manifest['review_key'] == key and manifest['inputs']['source'] == task['latest_snapshot'], 'history-completed-operation-scope-mismatch')
            values, order, row = runner.manifest_inputs(manifest)
            parsed = runner.verify_complete(operation, manifest, values, order, row)
            need(parsed == {k: v for k, v in task['result'].items() if k != 'evidence'}, 'history-ledger-result-completion-mismatch')
    if cursor != state['history_range']['end_exclusive']:
        missing.append('source-coverage:' + cursor + '..' + state['history_range']['end_exclusive'])
    need(not missing, 'history-incomplete:' + ','.join(missing))
    records = memory_api.read_records(**({} if memory is None else {'memory': memory}))
    for key, task in state['tasks'].items():
        need(any(r['review_key'] == key and r['result_ref']['sha256'] == task['result']['evidence']['sha256'] for r in records), 'history-result-not-in-case-memory')
    return {'ok': True, 'kind': 'negative-review-appeal-history-coverage-v1', 'domain': DOMAIN,
            'company': state['company'], 'groupid': state['groupid'], 'identity': state['identity'],
            'range': state['history_range'], 'coverage_basis': 'normal-filtered-review-date; existing-complaint results only',
            'source_refs': [v['inputs']['source'] for v in state['sources'].values()],
            'closed_operations': [t['completed_operation'] for t in state['tasks'].values()],
            'existing_results_read': len(state['tasks']), 'uncomplained_skipped': sum(len(v['skipped_uncomplained_ids']) for v in state['sources'].values()),
            'folded_traversed': False, 'messages_sent': 0, 'submissions': 0, 'business_cursor_updated': False,
            'scope': 'currently displayed platform normal middle/negative filter: existing complaint or pending-review cases only',
            'scope_exclusions': ['platform folded section', 'uncomplained reviews', 'already removed or otherwise not displayed records'],
            'scope_complete': True, 'company_all_history_complete': False, 'verified_at': workflow.now()}


def main():
    ap = argparse.ArgumentParser(description=__doc__); sub = ap.add_subparsers(dest='verb', required=True)
    p = sub.add_parser('init')
    for k in ('root', 'company', 'groupid', 'start', 'end-exclusive', 'identity-receipt', 'identity-receipt-sha256'): p.add_argument('--'+k, required=True)
    p = sub.add_parser('ingest'); p.add_argument('--root', required=True)
    for k in ('job', 'source', 'profile', 'envelope'):
        p.add_argument('--'+k, required=True); p.add_argument('--'+k+'-sha256', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--root', required=True); p.add_argument('--id', required=True)
    p = sub.add_parser('run'); p.add_argument('--manifest', required=True); p.add_argument('--steps', type=int, choices=range(1,11), default=1)
    p = sub.add_parser('verify-coverage'); p.add_argument('--root', required=True); p.add_argument('--out', required=True)
    p = sub.add_parser('status'); p.add_argument('--root', required=True)
    p = sub.add_parser('pin-prior'); p.add_argument('--root', required=True)
    for k in ('operation','legacy'):
        p.add_argument('--'+k, required=True); p.add_argument('--'+k+'-sha256', required=True)
    p = sub.add_parser('prepare-acquisition');p.add_argument('--root',required=True);p.add_argument('--identity-receipt',nargs=2,action='append',required=True,metavar=('PATH','SHA256'))
    p = sub.add_parser('prepare-normal-job');p.add_argument('--root',required=True);p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--out',required=True);p.add_argument('--completed-acquisition-adoption');p.add_argument('--completed-acquisition-adoption-sha256')
    a = ap.parse_args()
    try:
        if a.verb == 'init':
            state = initialize(a.root,a.company,a.groupid,a.start,a.end_exclusive,checked_ref(a.identity_receipt,a.identity_receipt_sha256)); output = {'ok':True,'workspace_kind':state['workspace_kind'],'history_range':state['history_range'],'ui_used':False}
        elif a.verb == 'ingest':
            state = ingest(a.root,{k:checked_ref(getattr(a,k),getattr(a,k+'_sha256')) for k in ('job','source','profile','envelope')}); output = {'ok':True,'existing_tasks':len(state['tasks']),'sources':len(state['sources']),'ui_used':False}
        elif a.verb == 'prepare': output = prepare(a.root,a.id)
        elif a.verb == 'pin-prior': output = pin_prior(a.root,checked_ref(a.operation,a.operation_sha256),checked_ref(a.legacy,a.legacy_sha256))
        elif a.verb == 'prepare-acquisition': output=prepare_acquisition(a.root,[checked_ref(path,checksum) for path,checksum in a.identity_receipt])
        elif a.verb == 'prepare-normal-job':
            need(bool(a.completed_acquisition_adoption)==bool(a.completed_acquisition_adoption_sha256),'history-adoption-paired-ref-required')
            adoption=checked_ref(a.completed_acquisition_adoption,a.completed_acquisition_adoption_sha256)if a.completed_acquisition_adoption else None
            output=prepare_normal_job(a.root,checked_ref(a.receipt,a.receipt_sha256),a.out,completed_acquisition_adoption_ref=adoption)
        elif a.verb == 'run': output = run(a.manifest,steps=a.steps)
        elif a.verb == 'verify-coverage':
            output = verify_coverage(a.root); p = Path(a.out).resolve(); need(not p.exists(),'history-coverage-output-exists'); workflow.atomic(p,output)
        else:
            state = load(a.root); output = {'ok':True,'workspace_kind':KIND,'company':state['company'],'history_range':state['history_range'],'sources':len(state['sources']),'existing_results':len(state['tasks']),'read':sum(bool(t.get('completed_operation')) for t in state['tasks'].values()),'capabilities':CAPABILITIES,'ui_used':False}
        print(json.dumps(output,ensure_ascii=False)); return 0
    except (ValueError, KeyError, OSError, RuntimeError, TypeError) as e:
        print(json.dumps({'ok':False,'error':str(e),'send_enabled':False,'submit_enabled':False},ensure_ascii=False)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
