#!/usr/bin/env python3
"""Approve reviewed terminal profile, retire loaded-page wait, run/finalize original."""
import argparse,fcntl,json,sys
from pathlib import Path
ROOT=Path('/Users/feibing/work/projects/zmaibaole')
sys.path.insert(0,str(ROOT/'skills/negative-review-complaints/scripts'))
import normal_paging_runner as c
import normal_identity_visible_recovery as identity
KIND='supervisor-normal-terminal-coordinator-v1'
def validate(r,g,grant,archive=None):
    c.need(g.get('kind')==KIND and g.get('approved') is True and g.get('reviewer_role')=='supervisor' and g.get('manifest')==r.mref and g.get('job')==r.m['job'],'terminal-coordinator-root-grant')
    c.need(g.get('helper')==c.ref(__file__) and g.get('identity_helper')==c.ref(identity.__file__) and g.get('code_pins')==c.codes(),'terminal-coordinator-source-pins')
    c.need(g.get('allow_approve_terminal_profile') is True and g.get('allow_retire_loaded_terminal_wait') is True and g.get('allow_original_run_and_finalize') is True and g.get('outer_clock_reset') is False,'terminal-coordinator-boundary')
    r.guard();original=archive or g['operation_before'];c.need(original['sha256']==g['operation_before']['sha256'],'terminal-coordinator-archive-sha');old=c.document(original);review=c.document(g['terminal_review'])
    c.need(old.get('state')=='hold' and old.get('phase')=='read-first' and old.get('error')=='terminal-layout-awaits-live-profile' and old.get('expected_page')==5 and len(old['pages'])==4 and sum(len(x['proof']['rows']) for x in old['pages'])==40 and len(old['calls'])==4 and all(x.get('state')=='confirmed' for x in old['calls']),'terminal-coordinator-original-hold')
    c.need(old.get('loading_wait',{}).get('expected_page')==5 and old['loading_wait'].get('attempts') and old.get('identity_visibility_recovery')==g.get('identity_visibility_recovery') and not old.get('profile_amendment'),'terminal-coordinator-original-wait')
    c.need(old['manifest']==r.mref and review.get('operation_before')==g['operation_before'] and review.get('manifest')==r.mref and review.get('job')==r.m['job'] and review.get('hold_raw')==old['latest_page'] and review.get('navigation_sha256')==g.get('navigation_sha256')==old['navigation_sha256'],'terminal-coordinator-review-binding')
    c.document(old['latest_page']);ia=c.document(g['identity_visibility_recovery']);ig=c.document(ia['grant']);c.document(ia['operation_archive']);c.document(ia['navigation_archive'])
    c.need(ig.get('kind')==identity.KIND and ig.get('approved') is True and ig.get('manifest')==r.mref and ig.get('helper')==g['identity_helper'],'terminal-coordinator-prior-identity-grant')
    return old,ig['max_hovers']
def execute(manifest,grant,request=None):
    base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=c.Runner(manifest);g=c.document(grant)
        path=base/'terminal-coordinator/operation.json'
        if path.exists():
            s=c.document(c.ref(path));c.need(s['grant']==grant and s['manifest']==manifest,'terminal-coordinator-existing-binding')
            old,max_hovers=validate(r,g,grant,s['original_operation'])
            if s['phase']=='complete':
                r.guard()
                c.need(r.s.get('state')=='complete' and r.s.get('phase')=='source-ready' and s.get('operation')==c.ref(r.path),'terminal-coordinator-completed-operation-changed')
                outputs=r.s.get('outputs',{});c.need(set(outputs)=={'profile','envelope','source'},'terminal-coordinator-completed-outputs')
                documents={k:c.document(v) for k,v in outputs.items()}
                c.need(documents['profile']==r.profile,'terminal-coordinator-completed-profile-changed')
                return s
        else:
            old,max_hovers=validate(r,g,grant)
            c.need(c.ref(r.path)==g['operation_before'] and r.s==old,'terminal-coordinator-original-operation-changed')
            archive=c.immutable(base/'terminal-coordinator/original-hold.json',r.path.read_bytes())
            s={'kind':'normal-terminal-coordinator-operation-v1','grant':grant,'manifest':manifest,'original_operation':archive,'phase':'prepared','outer_clock_reset':False};c.save(path,s)
        if not r.s.get('profile_amendment'):
            c.need(s['phase']=='prepared' and not (base/'profile-amendment.json').exists(),'terminal-coordinator-partial-approval-needs-review')
            s['phase']='approval-intent';c.save(path,s)
            r.approve_profile(g['terminal_review']) # Public original method owns all terminal validation.
        amendment=c.document(r.s['profile_amendment'])
        c.need(amendment['review_ref']==g['terminal_review'] and amendment['operation_archive']['sha256']==g['operation_before']['sha256'],'terminal-coordinator-approved-profile-binding')
        c.document(amendment['operation_archive']);r.guard()
        if not r.s.get('terminal_loading_retirement'):
            c.need(r.s['state']=='running' and r.s['phase']=='read-first' and r.s['loading_wait']==old['loading_wait'],'terminal-coordinator-only-original-loaded-wait')
            retirement={'kind':'normal-reviewed-terminal-loading-retirement-v1','grant':grant,'manifest':manifest,'profile_amendment':r.s['profile_amendment'],'original_operation_archive':amendment['operation_archive'],'original_loading_wait':old['loading_wait'],'reason':'reviewed-loaded-terminal-page-not-loading','outer_clock_reset':False}
            rr=c.publish(base/'terminal-coordinator/loading-retirement.json',retirement)
            s.update(phase='retirement-intent',retirement=rr);c.save(path,s)
            r.s['terminal_loading_retirement']=rr;r.s.pop('loading_wait');r.persist()
        rr=c.document(r.s['terminal_loading_retirement']);c.need(rr['grant']==grant and rr['profile_amendment']==r.s['profile_amendment'] and rr['original_loading_wait']==old['loading_wait'] and 'loading_wait' not in r.s,'terminal-coordinator-retirement-binding')
        s.update(phase='run-original',retirement=r.s['terminal_loading_retirement']);c.save(path,s)
        a=identity.Adapter(r,request or r.default_request,max_hovers)
        if any(e['state']=='unknown' for e in a.s['events']):
            a.reconcile_unknown();s.update(phase='hold',error='identity-hover-reconciled-no-business-resume');c.save(path,s);return s
        r.request=a
        if r.s['state']=='running':s['run_result']=r.run(25);c.save(path,s)
        if r.s['state'] in ('collected','complete'):
            s['finalize_result']=r.finalize();s.update(phase='complete',operation=c.ref(r.path));c.save(path,s)
        else:s.update(phase='hold',operation=c.ref(r.path),error=r.s.get('error'));c.save(path,s)
        return s
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','grant'):p.add_argument('--'+k,required=True);p.add_argument('--'+k+'-sha256',required=True)
    a=p.parse_args();print(json.dumps(execute({'path':a.manifest,'sha256':a.manifest_sha256},{'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'input_replayed':False},ensure_ascii=False));raise SystemExit(2)
