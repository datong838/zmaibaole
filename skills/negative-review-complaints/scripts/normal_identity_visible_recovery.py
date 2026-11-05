#!/usr/bin/env python3
"""Typed account-card visibility recovery, using the unchanged normal Runner."""
import argparse, copy, fcntl, json, sys, uuid
from pathlib import Path
ROOT=Path('/Users/feibing/work/projects/zmaibaole')
sys.path[:0]=[str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/douyin-laike-operator/scripts')]
import normal_paging_runner as c
KIND='supervisor-normal-identity-visible-recovery-v1'
def flat(tree):return c.p.n.flatten(tree['root'])
def cl(n):return n.get('attributes',{}).get('class','')
def absent(tree):return not any('UserCard-index-module__outer--' in cl(n) for n in flat(tree))
def stable(proof):
    value=copy.deepcopy({k:proof[k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')})
    value['scope'].pop('identity',None) # Baseline job identity is not observed here.
    return value
def local_preflight(r,tab,tree):
    """Not identity evidence, and never a collected page or source row."""
    c.need(tab['tabId']==r.m['tab_id'] and tab['windowId']==r.m['window_id'],'identity-visible-tab-window')
    ns=flat(tree)
    c.need(not any(n.get('role')=='dialog' or n.get('attributes',{}).get('aria-modal')=='true' or 'drawer' in cl(n).lower() or 'SwitchCard' in cl(n) for n in ns),'identity-visible-other-modal')
    proof=c.p.inspect_page(r.job,{'tab':tab,'tree':tree,'observed_at':c.now()},r.profile,r.m['receipt'],_full_identity=False)
    proof['scope'].pop('identity',None)
    proof.update(full_identity_verified=False,page_accepted=False,preflight_only=True)
    proof['preflight_card_names']=[n['name'] for n in ns if cl(n)=='commentItem-jrXo5p']
    c.need(proof['pager']['page']==r.s['expected_page'],'identity-visible-page')
    if r.s['pages']:
        prior=r.s['pages'][0]['proof'];scope=dict(prior['scope']);scope.pop('identity',None)
        c.need(proof['scope']==scope and proof['normal_header_count']==prior['normal_header_count'],'identity-visible-original-scope')
    expected=next((x['proof'] for x in r.s['pages'] if x['proof']['pager']['page']==r.s['expected_page']),None)
    if expected is None and r.s.get('latest_page'):
        old=c.document(r.s['latest_page'])
        try:expected=c.p.inspect_page(r.job,old,r.profile,r.m['receipt'],_full_identity=False)
        except ValueError as e:
            # A prior old-page loading shell cannot supply stable row evidence.
            if str(e)!='normal-pager-loading-readonly-wait':raise
        if expected is not None and expected['pager']['page']!=r.s['expected_page']:expected=None
    if expected is not None:c.need(stable(proof)==stable(expected),'identity-visible-known-page-changed')
    triggers=[n for n in ns if n.get('name')==r.job['identity']['provider'] and 'Profile-index-module__title--' in cl(n) and n.get('selector','').startswith('#main-app > section > section > header >') and not n.get('children') and not n.get('disabled')]
    c.need(len(triggers)==1,'identity-visible-provider-trigger')
    return proof,triggers[0]

class Adapter:
    """A transparent request adapter; all returned trees are actual RPC replies."""
    def __init__(self,r,request,max_hovers):
        self.r=r;self.request=request;self.path=r.base/'identity-visible-recovery/adapter.json';self.max_hovers=max_hovers;self.tabs=None
        self.s=c.document(c.ref(self.path)) if self.path.exists() else {'kind':'normal-identity-visible-adapter-v1','events':[],'transport':[]}
    def save(self):c.save(self.path,self.s)
    def raw(self,cmd):
        path=self.path.parent/'transport'/(uuid.uuid4().hex+'.json')
        try:reply=self.request(cmd)
        except Exception as e:
            rr=c.publish(path,{'command':cmd,'exception':{'type':type(e).__name__,'message':str(e)},'at':c.now()});self.s['transport'].append(rr);self.save();raise
        rr=c.publish(path,{'command':cmd,'reply':reply,'at':c.now()});self.s['transport'].append(rr);self.save()
        c.need(reply.get('ok') is True,'identity-visible-bridge-failed');return reply
    def tab(self,tabs):
        pairs=[(w,t) for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==self.r.m['tab_id']]
        c.need(len(pairs)==1,'identity-visible-tab-unique');w,t=pairs[0]
        c.need(t.get('windowId')==w.get('windowId')==self.r.m['window_id'] and t.get('active') is True and w.get('focused') is True,'identity-visible-active-window')
        from urllib.parse import urlsplit,parse_qs
        u=urlsplit(t['url']);c.need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/life_comment/management' and parse_qs(u.query)=={'groupid':[str(self.r.job['groupid'])]},'identity-visible-route')
        return t
    def fresh(self):
        before=self.raw({'op':'tabs'})['result'];t=self.tab(before)
        ping=self.raw({'op':'ping','tabId':self.r.m['tab_id']})['result'];c.need(ping.get('version')==c.bridge.SAFETY_VERSION and ping.get('safety')=='DOM-only' and ping.get('content_build')==c.CONTENT_BUILD,'identity-visible-build')
        reply=self.raw({'op':'tree','tabId':self.r.m['tab_id']});after=self.raw({'op':'tabs'})['result'];c.need(self.tab(after)==t,'identity-visible-tab-changed')
        return t,reply
    def verify_event(self,event):
        tab,reply=self.fresh();tree=reply['result'];proof,_=local_preflight(self.r,tab,tree)
        c.p.n.public_identity(tree,self.r.job['identity'])
        c.need(stable(proof)==event['before_local_scope'],'identity-visible-hover-changed-business-scope')
        c.need(proof.get('preflight_card_names')==event['before_card_names'],'identity-visible-hover-changed-card-names')
        event.update(state='verified',verified_at=c.now(),full_identity_verified=True,after_reply=self.s['transport'][-2]);self.save();return reply
    def reconcile_unknown(self):
        unknown=[e for e in self.s['events'] if e['state']=='unknown'];c.need(len(unknown)==1,'identity-visible-unknown-not-unique')
        return self.verify_event(unknown[0])
    def __call__(self,command):
        c.need(not any(e['state']=='unknown' for e in self.s['events']),'identity-visible-hover-unknown-readonly-required')
        reply=self.raw(command)
        if command.get('op')=='tabs':self.tabs=reply['result'];return reply
        if command.get('op')!='tree':return reply
        c.need(command=={'op':'tree','tabId':self.r.m['tab_id']},'identity-visible-tree-command')
        if not absent(reply['result']):return reply
        c.need(self.tabs is not None,'identity-visible-prior-tabs-required');tab=self.tab(self.tabs)
        proof,trigger=local_preflight(self.r,tab,reply['result'])
        c.need(len(self.s['events'])<self.max_hovers,'identity-visible-hover-budget')
        cmd={'op':'hover','tabId':self.r.m['tab_id'],'locator':{'by':'selector','value':trigger['selector']},'kind':'navigation'}
        event={'state':'unknown','command':cmd,'before_local_scope':stable(proof),'before_card_names':proof.get('preflight_card_names'),'local_scope_full_identity':False,'local_scope_accepted':False,'before_reply':self.s['transport'][-1],'intent_at':c.now()}
        self.s['events'].append(event);self.save() # file and parent directory fsync, before input
        result=self.raw(cmd);event['hover_reply']=self.s['transport'][-1];event['action_returned_at']=c.now();self.save()
        c.need(result['result'].get('kind')=='navigation' and result['result'].get('hovered',{}).get('selector')==trigger['selector'],'identity-visible-hover-reply')
        return self.verify_event(event)

def validate(r,review,original_sha,grant,*,verify_runner=True):
    c.need(review.get('kind')==KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('manifest')==r.mref and review.get('job')==r.m['job'],'identity-visible-root-grant')
    c.need(review.get('operation_before',{}).get('sha256')==original_sha and review.get('body_shape_recovery')==r.s.get('body_shape_recovery') and review.get('navigation_sha256')==r.s['navigation_sha256'],'identity-visible-original-binding')
    c.need(review.get('helper')==c.ref(__file__) and review.get('allow_same_process_recovery_and_run') is True and review.get('allow_identity_navigation_hover') is True and review.get('outer_clock_reset') is False,'identity-visible-reviewed-helper')
    c.need(review.get('new_read_window')=={'seconds':30.0,'max_reads':3,'starts_at_first_read':True} and type(review.get('max_hovers')) is int and 1<=review['max_hovers']<=12,'identity-visible-explicit-window')
    release=c.document(review['source_release']);c.need(release.get('published') is True and release.get('source_count')==15 and len(release['files'])==15,'identity-visible-published-source-release')
    c.need(all(c.ref(x['target'])['sha256']==x['after_sha256'] for x in release['files']),'identity-visible-published-source-changed')
    c.need(review.get('code_pins')==c.codes(),'identity-visible-current-code-pins')
    if verify_runner:r.guard()
    original=c.document(review['operation_before'])
    c.need(original.get('state')=='hold' and original.get('phase')=='read-first' and original.get('error')=='identity-account-unverified' and original.get('expected_page')==3 and len(original['pages'])==2 and sum(len(x['proof']['rows']) for x in original['pages'])==20 and len(original['calls'])==2 and all(x.get('state')=='confirmed' for x in original['calls']),'identity-visible-exact-original-hold')
    c.need(original.get('latest_page')==review.get('hold_raw') and original.get('loading_wait',{}).get('attempts') and original.get('body_shape_recovery')==review['body_shape_recovery'],'identity-visible-original-evidence')
    c.document(review['hold_raw']);c.document(review['body_shape_recovery'])
    return original

def recover_and_run(manifest,original_sha,grant,steps=25,request=None):
    c.need(steps==25,'identity-visible-fixed-run-budget');base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=c.Runner(manifest);review=c.document(grant);audit_path=base/'identity-visible-recovery/authorization.json'
        if audit_path.exists():
            audit=c.document(c.ref(audit_path));c.need(audit['grant']==grant and audit['manifest']==manifest and audit['operation_archive']['sha256']==original_sha,'identity-visible-existing-grant')
            # Guard the grant using the immutable original archive, not mutable operation.
            r.guard();archived=copy.deepcopy(r.s);r.s=c.document(audit['operation_archive'])
            try:validate(r,{**review,'operation_before':audit['operation_archive']},original_sha,grant,verify_runner=False)
            finally:r.s=archived
            c.need(r.s.get('identity_visibility_recovery')==c.ref(audit_path),'identity-visible-audit-reference')
            r.guard();a=Adapter(r,request or r.default_request,review['max_hovers'])
            if any(x['state']=='unknown' for x in a.s['events']):
                a.reconcile_unknown();return {'state':'readonly-reconciled','operation':c.ref(r.path),'business_run_resumed':False,'outer_clock_reset':False}
            c.need(r.s['state']=='running','identity-visible-no-second-rearm')
        else:
            c.need(c.ref(r.path)==review['operation_before'],'identity-visible-original-state-changed');original=validate(r,review,original_sha,grant)
            c.need(r.s==original,'identity-visible-original-state-changed')
            old=c.immutable(base/'identity-visible-recovery/original-hold.json',r.path.read_bytes());nav=c.immutable(base/'identity-visible-recovery/original-navigation.json',Path(r.m['original_navigation']['path']).read_bytes())
            audit=c.publish(audit_path,{'grant':grant,'manifest':manifest,'operation_archive':old,'navigation_archive':nav,'at':c.now(),'prior_loading_wait':original['loading_wait'],'outer_clock_reset':False})
            r.s['identity_visibility_recovery']=audit;r.s.update(state='running',loading_wait={'expected_page':r.s['expected_page'],'started_monotonic':None,'attempts':[]});r.s.pop('error',None);r.guard();r.persist()
            a=Adapter(r,request or r.default_request,review['max_hovers'])
        r.request=a
        return {'normal_runner':r.run(25),'operation':c.ref(r.path),'identity_adapter':c.ref(a.path) if a.path.exists() else None,'outer_clock_reset':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('manifest','grant'):p.add_argument('--'+k,required=True);p.add_argument('--'+k+'-sha256',required=True)
    p.add_argument('--original-state-sha256',required=True);a=p.parse_args()
    print(json.dumps(recover_and_run({'path':a.manifest,'sha256':a.manifest_sha256},a.original_state_sha256,{'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'input_replayed':False},ensure_ascii=False));raise SystemExit(2)
