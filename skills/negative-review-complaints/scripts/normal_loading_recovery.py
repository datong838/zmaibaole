#!/usr/bin/env python3
"""Supervisor-pinned, file-only amendment for one original loading HOLD. No RPC/input."""
import argparse,fcntl,json
from pathlib import Path
import normal_paging_runner as c
KIND='supervisor-normal-loading-shape-recovery-v1'
def changed_paths():return {str(c.ROOT/'skills/negative-review-complaints/scripts'/x) for x in ('normal_paging.py','normal_paging_runner.py')}
def origin(manifest,m,state,navigation_archive=None):
    c.need(state.get('manifest')==manifest and state.get('state')=='hold' and state.get('phase')=='read-first' and state.get('error')=='normal-pager-shape' and not state.get('loading_shape_recovery'),'loading-recovery-exact-original-hold-required')
    job=c.document(m['job']);profile=c.document(m['profile']);c.document(m['receipt']);c.document(m['source_journal']);c.document(m['navigation_archive']);c.history_scope(job,m['original_navigation']['path'])
    r=object.__new__(c.Runner);r.m=m;r.s=state
    prior=r.loading_edge(navigation=c.document(navigation_archive) if navigation_archive else None)
    pair=state['pages'][-1]['pair'];first=c.p.inspect_page(job,c.document(pair[0]),profile,m['receipt']);second=c.p.inspect_page(job,c.document(pair[1]),profile,m['receipt'])
    c.need(second==prior and all(first[k]==second[k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')) and c.p.A.stamp(first['observed_at'])<c.p.A.stamp(second['observed_at']),'loading-recovery-original-stable-pair')
    diagnostic=c.p.inspect_loading(job,c.document(state['latest_page']),profile,m['receipt'],prior,state['expected_page'])
    return diagnostic

def validate_review(manifest,m,review,operation_archive=None,navigation_archive=None):
    c.need(review.get('kind')==KIND and review.get('reviewer_role')=='supervisor' and review.get('approved') is True and review.get('manifest')==manifest and review.get('job')==m['job'],'loading-recovery-supervisor-review-required')
    c.need(all(review.get(k) is True for k in ('allow_original_read_resume_only','no_browser_or_business_input','loading_shape_reviewed')) and review.get('later_pages_live_validated') is False,'loading-recovery-review-boundary')
    archive=operation_archive or review['operation_before'];c.need(archive['sha256']==review['operation_before']['sha256'],'loading-recovery-original-archive-sha');state=c.document(archive)
    if navigation_archive:c.need(navigation_archive['sha256']==state['navigation_sha256'],'loading-recovery-navigation-archive-sha')
    diagnostic=origin(manifest,m,state,navigation_archive)
    c.need(review.get('hold_raw')==state['latest_page'] and review.get('navigation_sha256')==state['navigation_sha256'] and review.get('diagnostic')==diagnostic,'loading-recovery-original-bindings')
    before,after=review.get('code_before'),review.get('code_after')
    c.need(before==m['code'] and isinstance(after,dict) and set(after)==set(before) and {k for k in before if before[k]!=after[k]}==changed_paths(),'loading-recovery-only-reviewed-two-file-amendment')
    c.need(c.ref(__file__)==review.get('recovery_helper'),'loading-recovery-helper-changed')
    c.need(all(c.ref(k)['sha256']==v for k,v in after.items()),'loading-recovery-reviewed-code-changed')
    return state,after

def verified_code(manifest,m,audit_ref):
    audit=c.document(audit_ref);review=c.document(audit['review']);state,after=validate_review(manifest,m,review,audit['operation_archive'],audit['navigation_archive'])
    c.need(audit.get('manifest')==manifest and c.document(audit['operation_archive'])==state and audit['operation_archive']['sha256']==review['operation_before']['sha256'],'loading-recovery-immutable-audit-required')
    return after

def resume(manifest,original_sha,grant):
    m=c.document(manifest);base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=c.Runner(manifest);review=c.document(grant)
        c.need(review.get('operation_before',{}).get('sha256')==original_sha,'loading-recovery-original-sha')
        if r.s.get('loading_shape_recovery'):
            audit=c.document(r.s['loading_shape_recovery']);c.need(audit.get('review')==grant,'loading-recovery-already-authorized');r.guard()
            return {'operation':c.ref(r.path),'state':r.s['state'],'rearmed':False,'rpc_used':False,'input_used':False}
        original,after=validate_review(manifest,m,review)
        c.need(c.ref(r.path)==review['operation_before'] and r.s==original,'loading-recovery-original-operation-changed')
        old=c.immutable(base/'loading-recovery'/'original-hold.json',r.path.read_bytes())
        nav=c.immutable(base/'loading-recovery'/'original-navigation.json',Path(m['original_navigation']['path']).read_bytes())
        audit=c.publish(base/'loading-recovery'/'authorization.json',{'manifest':manifest,'review':grant,'operation_archive':old,'navigation_archive':nav,'at':c.now(),'rpc_used':False,'input_used':False})
        r.s['loading_shape_recovery']=audit;r.s.update(state='running',phase='read-first',loading_wait={'expected_page':r.s['expected_page'],'started_monotonic':c.monotonic(),'attempts':[]});r.s.pop('error',None);r.guard();r.persist()
        return {'operation':c.ref(r.path),'state':r.s['state'],'rearmed':True,'rpc_used':False,'input_used':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','grant'):ap.add_argument('--'+k,required=True);ap.add_argument('--'+k+'-sha256',required=True)
    ap.add_argument('--original-state-sha256',required=True);a=ap.parse_args()
    print(json.dumps(resume({'path':a.manifest,'sha256':a.manifest_sha256},a.original_state_sha256,{'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'rpc_used':False,'input_used':False},ensure_ascii=False));raise SystemExit(2)
