"""Pure monitor adapter for canonical closed AND applied v3 case reinspection.
No current lease read, connector, business writer or self-reported proof authority.
"""
import hashlib,importlib,json,sys
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
PROJECT=Path(__file__).resolve().parents[3]
VERSIONS_DIRECTORY=PROJECT/'skills/negative-review-complaints/scripts'
SCHEMA='known-case-reinspection-v3'
KIND='known-public-complaint-case-operation-v3'
class MonitorError(ValueError):pass
def need(ok,code):
    if not ok:raise MonitorError(code)
def timestamp(value):
    try:at=value if isinstance(value,datetime) else datetime.fromisoformat(value)
    except (ValueError,TypeError):raise MonitorError('monitor-v3-aware-time-required')
    need(at.utcoffset() is not None,'monitor-v3-aware-time-required');return at
def canonical(path):
    p=Path(path);need(p.is_absolute() and p==p.resolve() and not any(x.is_symlink() for x in [p,*p.parents]),'monitor-v3-canonical-path-required');return p
def reference(path):
    p=canonical(path);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(ref):
    p=canonical(ref['path']);raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'monitor-v3-artifact-changed');return json.loads(raw)
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@contextmanager
def versions():
    directory=canonical(VERSIONS_DIRECTORY);previous=list(sys.path)
    try:
        sys.path.insert(0,str(directory));names=('case_alias_versions','alias_replay_session','case_alias_v3','apply_case_alias_v3');modules=[importlib.import_module(n) for n in names]
        for name,module in zip(names,modules):need(Path(module.__file__).resolve()==directory/(name+'.py'),'monitor-v3-module-origin-conflict:'+name)
        v=modules[0];production=PROJECT/'skills/negative-review-complaints/scripts'
        for module,name in ((v.v2,'case_alias_cli'),(v.core,'unbound_case_runner'),(v.apply2,'apply_case_alias'),(v.w,'workflow')):need(Path(module.__file__).resolve()==production/(name+'.py'),'monitor-v3-original-module-origin-conflict:'+name)
        yield v
    finally:sys.path[:]=previous

def inspect(journal_path,state):
    """Deep snapshot. Incomplete/unapplied gets no closure; unknown refuses."""
    path=canonical(journal_path);journal=reference(path);need(read(journal)==state,'monitor-v3-original-journal-required')
    need(state.get('kind')==KIND and state.get('send_enabled') is False and state.get('submission_enabled') is False,'monitor-v3-policy-invalid')
    need(not any(state.get(k) for k in ('error','last_error','hold')) and not any(c.get('state')=='unknown' for c in state.get('calls',[])),'monitor-v3-error-or-unknown')
    need(state.get('state') in ('ready','opened','closed','complete'),'monitor-v3-unknown-state')
    with versions() as v:
        with v.replay.transaction(v.replay_code_token) as session:
            reference(Path(__file__).resolve());need(read(journal)==state,'monitor-v3-original-journal-required');m=read(state['manifest']);v.canonical_manifest(m,state['manifest']);need(path==v.base(m)/'operation.json','monitor-v3-canonical-operation-required')
            origin=read(m['origin']['manifest']);key=m['review_key'];need(key==origin['review_key'] and m['root']==origin['root'],'monitor-v3-original-business-required')
            idx_ref=reference(v.index_path(m));idx=read(idx_ref);need(idx=={'kind':'review-case-alias-active-v3','review_key':key,'origin':m['origin']['manifest'],'current':state['manifest']},'monitor-v3-active-owner-required')
            # Pure immutable source/prefix replay only. No live_guard/current
            # lease observed SHA or present root ledger is read by this adapter.
            v.context(m)
            binding={'active_index':idx_ref,'manifest':state['manifest'],'original_review_key':key,'origin_manifest':m['origin']['manifest'],'dispatch_id':m['lease']['binding']['dispatch_id']}
            closed=None
            apply_path=v.base(m)/'apply'/'operation.json'
            if state['state']!='complete' and apply_path.exists():
                need(read(reference(apply_path)).get('state')!='complete','monitor-v3-completed-operation-regressed')
            if state['state']=='complete':
                proof=v.verify_operation(journal)
                need(proof.get('kind')=='known-public-case-reinspection-proof-v3' and proof.get('original_review_key')==key and proof.get('person_identity_verified') is False and proof.get('screenshot_authorized') is False and proof.get('authoritative_source_modified') is False,'monitor-v3-proof-invalid')
                apply_path=v.base(m)/'apply'/'operation.json'
                if apply_path.exists():
                    applied_ref=reference(apply_path);audit=read(applied_ref)
                    need(audit.get('kind')=='apply-public-case-alias-v3' and audit.get('manifest')==state['manifest'],'monitor-v3-original-apply-required')
                    need(audit.get('state') in ('record-intent','recorded','awaiting-xlsx','memory-hook-unconfirmed','complete'),'monitor-v3-unknown-apply-state')
                    need(not audit.get('error') and not audit.get('last_error'),'monitor-v3-apply-error')
                    if audit['state']=='complete':
                        verified=v.verify_apply(applied_ref);need(verified==audit,'monitor-v3-apply-changed');receipt=read(audit['receipt']);need(receipt['operation']==journal and receipt['manifest']==state['manifest'],'monitor-v3-original-closure-required')
                        before=timestamp(read(state['normal_before'])['observed_at']);drawer=timestamp(read(state['drawer'])['observed_at']);after=timestamp(read(state['normal_after'])['observed_at']);created=timestamp(state['created_at']);ended=timestamp(state['completed_at']);app_created=timestamp(audit['created_at']);app_ended=timestamp(audit['completed_at'])
                        need(created<=before<=drawer<=after<=ended<=app_created<=app_ended<=timestamp(v.now()),'monitor-v3-closure-time-invalid')
                        business={'company':read(origin['inputs']['old_job'])['company'],'review_key':key,'old_source_sha256':origin['inputs']['old_source']['sha256'],'old_result_sha256':origin['old_result']['sha256'],'case_signature_sha256':proof['case_signature_sha256']}
                        # Same identity as v2: nicknames/version paths cannot make
                        # a second global business closure within this dispatch.
                        identity={'kind':'closed-public-case-alias','review_key':key}
                        closed={'proof':proof,'apply':applied_ref,'result':audit['result_input'],'normal_after':state['normal_after'],'identity':identity,'business_binding':business,'created_at':created.isoformat(),'completed_at':after.isoformat(),'operation_completed_at':ended.isoformat(),'apply_completed_at':app_ended.isoformat(),'lease':m['lease']['binding']}
            # All audited transitive artifacts (including prior results/receipts,
            # archived lease snapshots and immutable workbook) remain SHA-bound.
        refs=[{'path':p,'sha256':h[0]} for p,h in sorted(session.files.items())]
        for r in refs:need(reference(r['path'])==r,'monitor-v3-artifact-changed-at-end')
    need(reference(path)==journal and read(journal)==state,'monitor-v3-journal-changed-at-end')
    return {'schema':SCHEMA,'binding':binding,'closure':closed,'artifact_refs':refs}

def semantic(journal_path,state,*,role):
    need(role=='complaint_operator','monitor-v3-role-schema-conflict');checked=inspect(journal_path,state);tokens={};closed=checked['closure']
    if closed:
        tokens['closed-applied-known-case']=digest({k:closed[k] for k in ('identity','apply','result','normal_after')}|{'operation':reference(journal_path),'manifest':state['manifest']})
    return {'schema':SCHEMA,'binding':checked['binding'],'tokens':tokens}

def fresh(journal_path,*,role,dispatch_started_at,now):
    need(role=='complaint_operator','monitor-v3-role-schema-conflict');path=canonical(journal_path);state=read(reference(path))
    if state.get('state')!='complete':return None
    if not state.get('created_at') or not state.get('completed_at'):return None
    started=timestamp(dispatch_started_at);present=timestamp(now);created=timestamp(state['created_at']);ended=timestamp(state['completed_at']);need(started<=present and created<=ended<=present,'monitor-v3-time-invalid')
    if created<started:return None
    # Match this exact dispatch by its immutable start instant; no live lease
    # lookup, local calendar-day equality or timestamp/clock reset is used.
    m=read(state['manifest'])
    if timestamp(m['lease']['binding']['dispatch_intent_at'])!=started:return None
    checked=inspect(path,state);closed=checked['closure']
    if closed is None:return None
    need(started<=created<=timestamp(closed['completed_at'])<=timestamp(closed['operation_completed_at'])<=timestamp(closed['apply_completed_at'])<=present,'monitor-v3-fresh-closure-time-invalid')
    return {'kind':'verified-fresh-completed-evidence-v1','schema':SCHEMA,'dedup_key':digest(closed['identity']),'business_identity':closed['identity'],'business_binding':closed['business_binding'],'created_at':created.isoformat(),'completed_at':closed['completed_at'],'dispatch_id':closed['lease']['dispatch_id'],'artifact_refs':checked['artifact_refs']}
