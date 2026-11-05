#!/usr/bin/env python3
"""One supervisor-pinned image-only text profile amendment, original job/run/lock."""
import argparse,fcntl,json
from pathlib import Path
import normal_paging_runner as c
import normal_loading_read_recovery as read_history
KIND='supervisor-normal-image-only-body-review-v1'
def previous_code(manifest,m,audit_ref):
    """Replay the previous narrow recovery from its archives; never rearm it."""
    audit=c.document(audit_ref);review=c.document(audit['review']);state=c.document(audit['operation_archive'])
    c.need(review.get('kind')==read_history.KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('manifest')==manifest and review.get('job')==m['job'] and review.get('allow_same_process_resume_and_run') is True,'body-prior-read-review')
    prior,before,nav=read_history.prior_authorization(manifest,m,review['prior_loading_authorization'])
    c.need(audit.get('manifest')==manifest and audit['operation_archive']['sha256']==review['operation_before']['sha256'] and audit.get('navigation_archive')==nav and audit.get('prior_loading_authorization')==review['prior_loading_authorization'],'body-prior-read-archive-binding')
    c.need(state.get('loading_shape_recovery')==review['prior_loading_authorization'] and not state.get('loading_read_recovery') and state.get('state')=='hold' and state.get('phase')=='read-first' and state.get('error')=='paging-bridge-read-or-action-failed','body-prior-read-hold')
    ignore={'state','error','updated_at','loading_wait','loading_shape_recovery','transport'}
    c.need({k:v for k,v in state.items() if k not in ignore}=={k:v for k,v in prior.items() if k not in ignore},'body-prior-read-collection-changed')
    transport=state['transport'];c.need(len(transport)==len(prior['transport'])+1 and transport[:-1]==prior['transport'] and transport[-1]==review['failure'],'body-prior-read-first-failure')
    failure=c.document(transport[-1]);reply=failure.get('reply',{});c.need(failure.get('command')=={'op':'tabs'} and 'exception' not in failure and reply.get('ok') is False and reply.get('error')=='bridge-timeout' and reply.get('outcome')=='not-delivered','body-prior-read-not-delivered')
    wait=state['loading_wait'];attempts=wait['attempts'];c.need(wait['expected_page']==state['expected_page'] and len(attempts)==1 and set(attempts[0])=={'started_monotonic','at'} and 0<=attempts[0]['started_monotonic']-wait['started_monotonic']<c.MAX_LOADING_SECONDS,'body-prior-read-attempt')
    after=review['code_after'];c.need(review['code_before']==before and set(after)==set(before) and {k for k in before if before[k]!=after[k]}=={str(c.ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py')},'body-prior-read-code-graph')
    c.need(c.ref(read_history.__file__)==review['recovery_helper'],'body-prior-read-helper-changed')
    return after

def origin(manifest,m,state,profile,navigation_archive=None):
    c.need(state.get('manifest')==manifest and state.get('state')=='hold' and state.get('phase')=='read-first' and state.get('error')=='node-not-unique:text' and not state.get('body_shape_recovery'),'body-exact-original-hold')
    job=c.document(m['job']);old_profile=c.document(m['profile']);c.document(m['receipt']);c.document(m['source_journal']);c.document(m['navigation_archive']);c.history_scope(job,m['original_navigation']['path'])
    c.need(profile=={**old_profile,'image_only_text_schema':c.p.IMAGE_ONLY_SCHEMA},'body-only-reviewed-profile-addition')
    r=object.__new__(c.Runner);r.m=m;r.s=state;r.loading_edge(navigation=c.document(navigation_archive) if navigation_archive else None)
    for item in state['pages']:
        pair=[c.document(q) for q in item['pair']];proofs=[c.p.inspect_page(job,x,profile,m['receipt']) for x in pair]
        c.need(proofs[1]==item['proof'] and c.p.A.stamp(proofs[0]['observed_at'])<c.p.A.stamp(proofs[1]['observed_at']) and all(proofs[0][k]==proofs[1][k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')),'body-original-stable-prefix-changed')
    raw=c.document(state['latest_page'])
    try:c.p.inspect_page(job,raw,old_profile,m['receipt'])
    except ValueError as e:c.need(str(e)=='node-not-unique:text','body-original-failure-mismatch')
    else:raise ValueError('body-original-schema-must-fail')
    proof=c.p.inspect_page(job,raw,profile,m['receipt']);new=[x for x in proof['rows'] if x.get('body_kind')=='image-only-no-text']
    c.need(proof['pager']['page']==state['expected_page'] and len(new)==1 and proof['scope']==state['pages'][0]['proof']['scope'] and proof['normal_header_count']==state['pages'][0]['proof']['normal_header_count'],'body-current-page-scope')
    return {'raw':state['latest_page'],'pager':proof['pager'],'rows':len(proof['rows']),'image_only_row':new[0],'stable_page_accepted':False}

def cache_sources(review):
    sources=review.get('pure_source_dependencies',{})
    expected={str(c.ROOT/'skills/negative-review-complaints/scripts'/name):module for name,module in (('authoritative_join.py',c.p.A),('export_parse_session.py',c.p.A.export_parse_session),('normal_review_body.py',c.p.body))}
    c.need(type(sources) is dict and set(sources)==set(expected),'body-parse-cache-exact-sources')
    c.need(all(type(sources[path]) is str and c.ref(path)['sha256']==sources[path] and c.ref(module.__file__)['sha256']==sources[path] for path,module in expected.items()),'body-parse-cache-source-changed')

def validate(manifest,m,review,archive=None,navigation_archive=None):
    cache_sources(review)
    c.need(review.get('kind')==KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('manifest')==manifest and review.get('job')==m['job'] and review.get('allow_same_process_resume_and_run') is True,'body-supervisor-grant-required')
    q=archive or review['operation_before'];c.need(q['sha256']==review['operation_before']['sha256'],'body-original-operation-sha');state=c.document(q)
    c.need(state.get('loading_read_recovery')==review['prior_read_authorization'] and state.get('loading_shape_recovery')==c.document(review['prior_read_authorization'])['prior_loading_authorization'],'body-prior-read-lineage');before=previous_code(manifest,m,review['prior_read_authorization'])
    profile=c.document(review['approved_profile']);diagnostic=origin(manifest,m,state,profile,navigation_archive)
    c.need(review.get('hold_raw')==state['latest_page'] and review.get('navigation_sha256')==state['navigation_sha256'] and review.get('diagnostic')==diagnostic,'body-original-evidence-binding')
    after=review['code_after'];expected={str(c.ROOT/'skills/negative-review-complaints/scripts'/n) for n in ('normal_paging.py','normal_paging_runner.py','normal_observation.py')}
    c.need(review.get('code_before')==before and set(after)==set(before) and {k for k in before if before[k]!=after[k]}==expected,'body-only-three-source-amendment')
    c.need(c.ref(__file__)==review.get('recovery_helper') and all(c.ref(k)['sha256']==v for k,v in after.items()),'body-reviewed-source-changed')
    return state,after,profile

def verified_context(manifest,m,audit_ref):
    audit=c.document(audit_ref);review=c.document(audit['review']);state,code,profile=validate(manifest,m,review,audit['operation_archive'],audit['navigation_archive'])
    c.need(audit.get('manifest')==manifest and audit.get('prior_read_authorization')==review['prior_read_authorization'] and audit['navigation_archive']['sha256']==state['navigation_sha256'],'body-immutable-audit-required')
    return code,profile

def recover_and_run(manifest,original_sha,grant,steps,request=None):
    c.need(type(steps) is int and 1<=steps<=25,'paging-bounded-steps-required');m=c.document(manifest);base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=c.Runner(manifest,request);review=c.document(grant);c.need(review.get('operation_before',{}).get('sha256')==original_sha,'body-original-operation-sha');rearmed=False
        if r.s.get('body_shape_recovery'):
            audit=c.document(r.s['body_shape_recovery']);c.need(audit.get('review')==grant,'body-authorization-already-used');r.guard()
        else:
            original,code,profile=validate(manifest,m,review);c.need(c.ref(r.path)==review['operation_before'] and r.s==original,'body-original-state-changed')
            old=c.immutable(base/'body-shape-recovery'/'original-hold.json',r.path.read_bytes());nav=c.immutable(base/'body-shape-recovery'/'original-navigation.json',Path(m['original_navigation']['path']).read_bytes())
            audit=c.publish(base/'body-shape-recovery'/'authorization.json',{'manifest':manifest,'review':grant,'operation_archive':old,'navigation_archive':nav,'prior_read_authorization':review['prior_read_authorization'],'at':c.now(),'recovery_input_used':False,'recovery_rpc_used':False})
            r.s['body_shape_recovery']=audit;r.s.update(state='running',loading_wait={'expected_page':r.s['expected_page'],'started_monotonic':None,'attempts':[]});r.s.pop('error',None);r.guard();r.persist();rearmed=True
        return {'rearmed':rearmed,'normal_runner':r.run(steps),'operation':c.ref(r.path),'outer_clock_reset':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','grant'):ap.add_argument('--'+k,required=True);ap.add_argument('--'+k+'-sha256',required=True)
    ap.add_argument('--original-state-sha256',required=True);ap.add_argument('--steps',type=int,default=25);a=ap.parse_args();print(json.dumps(recover_and_run({'path':a.manifest,'sha256':a.manifest_sha256},a.original_state_sha256,{'path':a.grant,'sha256':a.grant_sha256},a.steps),ensure_ascii=False))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'input_replayed':False},ensure_ascii=False));raise SystemExit(2)
