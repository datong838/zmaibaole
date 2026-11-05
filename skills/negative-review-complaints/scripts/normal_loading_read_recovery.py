#!/usr/bin/env python3
"""One reviewed first-tabs/not-delivered recovery and normal runner, same process/lock."""
import argparse,fcntl,json
from pathlib import Path
import normal_paging_runner as c
import normal_loading_recovery as old
KIND='supervisor-normal-loading-first-tabs-recovery-v1'
def prior_authorization(manifest,m,audit_ref):
    audit=c.document(audit_ref);review=c.document(audit['review']);state=c.document(audit['operation_archive']);nav=c.document(audit['navigation_archive'])
    c.need(review.get('kind')==old.KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('manifest')==manifest and review.get('job')==m['job'],'loading-read-prior-supervisor-review')
    c.need(all(review.get(k) is True for k in ('allow_original_read_resume_only','no_browser_or_business_input','loading_shape_reviewed')) and review.get('later_pages_live_validated') is False,'loading-read-prior-review-boundary')
    c.need(audit.get('manifest')==manifest and audit['operation_archive']['sha256']==review['operation_before']['sha256'] and audit['navigation_archive']['sha256']==review['navigation_sha256']==state['navigation_sha256'] and review['hold_raw']==state['latest_page'],'loading-read-prior-archive-binding')
    c.need(old.origin(manifest,m,state,audit['navigation_archive'])==review['diagnostic'],'loading-read-original-shape-proof')
    before,after=review['code_before'],review['code_after'];c.need(before==m['code'] and set(before)==set(after) and {k for k in before if before[k]!=after[k]}==old.changed_paths(),'loading-read-original-code-amendment')
    c.need(c.ref(old.__file__)==review['recovery_helper'],'loading-read-prior-helper-changed')
    return state,after,audit['navigation_archive']
def validate(manifest,m,review,archive=None):
    c.need(review.get('kind')==KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('manifest')==manifest and review.get('job')==m['job'] and review.get('allow_same_process_resume_and_run') is True,'loading-read-supervisor-grant-required')
    q=archive or review['operation_before'];c.need(q['sha256']==review['operation_before']['sha256'],'loading-read-original-sha');state=c.document(q)
    prior,old_code,nav=prior_authorization(manifest,m,review['prior_loading_authorization'])
    c.need(state.get('loading_shape_recovery')==review['prior_loading_authorization'] and not state.get('loading_read_recovery') and state.get('state')=='hold' and state.get('phase')=='read-first' and state.get('error')=='paging-bridge-read-or-action-failed','loading-read-exact-transport-hold')
    ignore={'state','error','updated_at','loading_wait','loading_shape_recovery','transport'}
    c.need({k:v for k,v in state.items() if k not in ignore}=={k:v for k,v in prior.items() if k not in ignore},'loading-read-original-collection-changed')
    transport=state.get('transport',[]);c.need(len(transport)==len(prior['transport'])+1 and transport[:-1]==prior['transport'] and transport[-1]==review['failure'],'loading-read-single-first-tabs-only')
    failure=c.document(transport[-1]);reply=failure.get('reply',{})
    c.need(failure.get('command')=={'op':'tabs'} and 'exception' not in failure and reply.get('ok') is False and reply.get('error')=='bridge-timeout' and reply.get('outcome')=='not-delivered','loading-read-not-delivered-only')
    wait=state.get('loading_wait',{});attempts=wait.get('attempts',[])
    c.need(wait.get('expected_page')==state['expected_page'] and len(attempts)==1 and set(attempts[0])=={'started_monotonic','at'} and type(wait.get('started_monotonic')) in (float,int) and 0<=attempts[0]['started_monotonic']-wait['started_monotonic']<c.MAX_LOADING_SECONDS,'loading-read-single-unfinished-attempt')
    c.need(review.get('code_before')==old_code and set(review.get('code_after',{}))==set(old_code) and {k for k in old_code if old_code[k]!=review['code_after'][k]}=={str(c.ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py')},'loading-read-only-runner-code-amendment')
    c.need(c.ref(__file__)==review.get('recovery_helper') and all(c.ref(k)['sha256']==v for k,v in review['code_after'].items()),'loading-read-reviewed-source-changed')
    return state,review['code_after'],nav

def verified_code(manifest,m,audit_ref):
    audit=c.document(audit_ref);review=c.document(audit['review']);state,code,nav=validate(manifest,m,review,audit['operation_archive'])
    c.need(audit.get('manifest')==manifest and audit.get('prior_loading_authorization')==review['prior_loading_authorization'] and audit.get('navigation_archive')==nav,'loading-read-audit-binding')
    return code

def recover_and_run(manifest,original_sha,grant,steps,request=None):
    c.need(type(steps) is int and 1<=steps<=25,'paging-bounded-steps-required');m=c.document(manifest);base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=c.Runner(manifest,request);review=c.document(grant)
        c.need(review.get('operation_before',{}).get('sha256')==original_sha,'loading-read-original-sha')
        rearmed=False
        if r.s.get('loading_read_recovery'):
            audit=c.document(r.s['loading_read_recovery']);c.need(audit.get('review')==grant,'loading-read-authorization-already-used');r.guard()
        else:
            original,code,nav=validate(manifest,m,review);c.need(c.ref(r.path)==review['operation_before'] and r.s==original,'loading-read-original-state-changed')
            archive=c.immutable(base/'loading-read-recovery'/'original-first-tabs-hold.json',r.path.read_bytes())
            audit=c.publish(base/'loading-read-recovery'/'authorization.json',{'manifest':manifest,'review':grant,'operation_archive':archive,'navigation_archive':nav,'prior_loading_authorization':review['prior_loading_authorization'],'at':c.now(),'recovery_rpc_used':False,'input_replayed':False})
            r.s['loading_read_recovery']=audit;r.s.update(state='running',loading_wait={'expected_page':r.s['expected_page'],'started_monotonic':None,'attempts':[]});r.s.pop('error',None);r.guard();r.persist();rearmed=True
        result=r.run(steps)
        return {'rearmed':rearmed,'recovery_ui_used':False,'recovery_rpc_used':False,'normal_runner':result,'operation':c.ref(r.path),'outer_clock_reset':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','grant'):ap.add_argument('--'+k,required=True);ap.add_argument('--'+k+'-sha256',required=True)
    ap.add_argument('--original-state-sha256',required=True);ap.add_argument('--steps',type=int,default=25);a=ap.parse_args()
    print(json.dumps(recover_and_run({'path':a.manifest,'sha256':a.manifest_sha256},a.original_state_sha256,{'path':a.grant,'sha256':a.grant_sha256},a.steps),ensure_ascii=False))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'input_replayed':False},ensure_ascii=False));raise SystemExit(2)
