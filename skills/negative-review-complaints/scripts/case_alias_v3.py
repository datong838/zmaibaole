#!/usr/bin/env python3
"""Candidate versioned known-case read CLI. Existing bridge only; no submit/send."""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
if __name__=='__main__':
    sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,copy,fcntl,json,re,uuid
import case_alias_versions as v
c=v.c;core=v.core;need=v.need

def current_lease(ref):
    need(ref['path']==str(v.v2.LEASE),'alias-v3-canonical-lease-required');return v.v2.lease_binding(v.doc(ref))
def origin_refs(manifest_ref,apply_ref,current_ledger_ref):
    om=v.doc(manifest_ref);v.legacy.identity(om,manifest_ref);need(apply_ref==v.ref(v.v2.folder(om)/'apply'/'operation.json'),'alias-v3-original-v2-apply-required')
    return {'manifest':manifest_ref,'receipt':v.ref(v.v2.folder(om)/'alias-receipt.json'),'apply':apply_ref,'application_ledger':current_ledger_ref}

def prepare(origin_manifest_ref,prior_apply_ref,fresh,lease_ref):
    need(set(fresh)=={'fresh_job','fresh_profile','normal_before'},'alias-v3-fresh-refs-required');[v.doc(r) for r in fresh.values()];binding=current_lease(lease_ref);om=v.doc(origin_manifest_ref);v.legacy.identity(om,origin_manifest_ref);root=Path(om['root']);key=om['review_key'];parent=v.review_folder(root,key)
    with core.e.operation_lock(root,key):
        root_raw=(root/'state.json').read_bytes();current=json.loads(root_raw);task=current['tasks'][key];need(task['status']=='existing_pending' and task['result']['status']=='pending','alias-v3-no-pending-original-case')
        version=v.version_id(binding,task['result']['evidence']['sha256']);directory=parent/'case-alias-v3'/version;directory.mkdir(parents=True,exist_ok=True);ip=parent/'case-alias-active.json';mp=directory/'manifest.json'
        if ip.exists():
            idx=v.doc(v.ref(ip));need(idx.get('kind')=='review-case-alias-active-v3' and idx['review_key']==key and idx['origin']==origin_manifest_ref,'alias-v3-active-anchor-conflict');previous=v.doc(idx['current']);applied_previous=None
            if previous.get('code')==v.codes():v.canonical_manifest(previous,idx['current'])
            else:
                # Old sources authorize no live entry. Only the exact completed,
                # applied predecessor can supply canonical historical identity.
                need(prior_apply_ref==v.ref(v.base(previous)/'apply'/'operation.json'),'alias-v3-original-prior-apply-required')
                applied_previous=v.verify_apply(prior_apply_ref)
                need(applied_previous.get('manifest')==idx['current'] and v.doc(idx['current'])==previous and previous['root']==str(root) and previous['review_key']==key and previous['origin']['manifest']==origin_manifest_ref,'alias-v3-prior-applied-manifest-required')
            if previous['version']==version:
                need(previous['fresh']==fresh and previous['lease']['binding']==binding and previous['previous_result']==task['result']['evidence'],'alias-v3-original-version-parameters-required');return {'state':'existing-version','manifest':idx['current'],'ui_used':False}
            # Even a changed dispatch cannot wash unknown/unapplied previous work.
            need(prior_apply_ref==v.ref(v.base(previous)/'apply'/'operation.json'),'alias-v3-original-prior-apply-required')
            if applied_previous is None:v.verify_apply(prior_apply_ref)
            if binding['day']<=previous['lease']['binding']['day']:
                need(binding['day']==previous['lease']['binding']['day'],'alias-v3-dispatch-day-regressed');return {'state':'already-complete-business-day','manifest':idx['current'],'fresh_recheck':False,'run_permitted':False,'ui_used':False}
            origin=previous['origin'];prior={'kind':'v3','manifest':idx['current'],'apply':prior_apply_ref}
        else:
            existing=list((parent/'case-alias-v3').glob('*/manifest.json'))
            # Restore only the exact unpublished-index crash owner, never fork.
            if existing:
                need(existing==[mp] and mp.exists(),'alias-v3-active-index-missing-with-existing-version');same=v.doc(v.ref(mp));v.canonical_manifest(same,v.ref(mp));need(same['fresh']==fresh and same['lease']['binding']==binding and same['previous_result']==task['result']['evidence'],'alias-v3-original-version-parameters-required');v.context(same);v.w.atomic(ip,{'kind':'review-case-alias-active-v3','review_key':key,'origin':origin_manifest_ref,'current':v.ref(mp)});return {'state':'restored-exact-preinput-index','manifest':v.ref(mp),'ui_used':False}
            # First v3 generation explicitly deep-adopts complete/applied v2.
            v2lease=om['lease']['binding'];audit=v.doc(prior_apply_ref)
            need(audit.get('state')=='complete','alias-v3-v2-apply-incomplete')
            if binding['day']<=v2lease['day']:
                need(binding['day']==v2lease['day'],'alias-v3-dispatch-day-regressed');snapshot=v.v2.archive_bytes(directory/('ledger-'+c.hashlib.sha256(root_raw).hexdigest()+'.json'),root_raw,c.hashlib.sha256(root_raw).hexdigest());v.original(origin_refs(origin_manifest_ref,prior_apply_ref,snapshot));return {'state':'already-complete-business-day','legacy_manifest':origin_manifest_ref,'fresh_recheck':False,'run_permitted':False,'ui_used':False}
            origin=None;prior={'kind':'v2','apply':prior_apply_ref}
        core.barriers(parent,om)
        snapshot=v.v2.archive_bytes(directory/('ledger-'+c.hashlib.sha256(root_raw).hexdigest()+'.json'),root_raw,c.hashlib.sha256(root_raw).hexdigest())
        if origin is None:origin=origin_refs(origin_manifest_ref,prior_apply_ref,snapshot)
        lease_snapshot=v.v2.archive_bytes(directory/('lease-'+lease_ref['sha256']+'.json'),Path(lease_ref['path']).read_bytes(),lease_ref['sha256'])
        graph=v.codes();sealed=v.release.seal(graph);need(v.codes()==graph,'alias-v3-code-changed-during-seal')
        m={'code_release':sealed,'kind':v.KIND,'root':str(root),'review_key':key,'version':version,'origin':origin,'prior':prior,'current_ledger':snapshot,'previous_result':task['result']['evidence'],'fresh':fresh,'lease':{'snapshot':lease_snapshot,'observed':lease_ref,'current_path':str(v.v2.LEASE),'binding':binding},'prepared_at':v.now(),'code':graph}
        v.context(m);need((root/'state.json').read_bytes()==root_raw and v.ref(v.v2.LEASE)==lease_ref,'alias-v3-prepare-live-source-changed');mr=v.publish(mp,m);v.w.atomic(ip,{'kind':'review-case-alias-active-v3','review_key':key,'origin':origin_manifest_ref,'current':mr});return {'state':'prepared','manifest':mr,'ui_used':False}

def guard(m,*,readonly=False):
    # A scope, never a memoized guard: current lease/index/ledger and barriers
    # execute afresh on EVERY call. Only their pure historical nodes share DAG
    # results. Terminal byte checks finish before Transport calls the network.
    with v.replay.transaction(v.replay_code_token) as session:
        v.code_guard(m);current=session.read_current_lease(readonly_reconcile=readonly);need(v.v2.lease_binding(current,readonly_reconcile=readonly)==m['lease']['binding'],'alias-v3-current-lease-changed');v.active_guard(m);v.context(m)

class Transport:
    def __init__(self,m,request=None,*,readonly=False):
        self.m=m;self.fn=request or (lambda cmd:v.v2.bridge.request(cmd,timeout=50));self.readonly=readonly;self.attempt=v.base(m)/'transport'/uuid.uuid4().hex;self.attempt.mkdir(parents=True);self.n=0;self.input_attempted=False;matches=re.findall(r"const BUILD='([^']+)'",v.v2.CONTENT.read_text());need(len(matches)==1,'alias-v3-content-build-ambiguous');self.build=matches[0]
    def raw(self,cmd):
        need(v.replay.ACTIVE.get() is None,'alias-v3-transport-outside-pure-scope-required')
        need(not self.readonly or cmd.get('op') in ('tabs','ping','tree'),'alias-v3-readonly-capability');guard(self.m,readonly=self.readonly);self.n+=1;path=self.attempt/(str(self.n).zfill(3)+'.json')
        if cmd.get('op')=='click':self.input_attempted=True
        try:r=self.fn(cmd)
        except Exception as exc:v.publish(path,{'command':cmd,'exception':{'type':type(exc).__name__,'message':str(exc)},'at':v.now()});raise
        v.publish(path,{'command':cmd,'response':r,'at':v.now()});need(r.get('ok') is True,'alias-v3-bridge-failed');return r['result']
    def fresh(self):
        context,_,_,_,_=v.context(self.m);expected=context['normal_before']['pages'][0]['tab'];windows=self.raw({'op':'tabs'});focused=[w for w in windows if w.get('focused') is True];need(len(focused)==1 and focused[0].get('windowId')==expected['windowId'],'alias-v3-focus-window-changed');tabs=[t for t in focused[0].get('tabs',[]) if t.get('active') is True];need(len(tabs)==1 and all(tabs[0].get(k)==expected[k] for k in ('tabId','windowId','url')) and tabs[0].get('allowed') is True,'alias-v3-active-tab-changed');tab=tabs[0]
        ping=self.raw({'op':'ping','tabId':tab['tabId']});need(ping.get('version')==v.v2.bridge.SAFETY_VERSION and ping.get('content_build')==self.build and ping.get('safety')=='DOM-only','alias-v3-content-not-loaded');tree=self.raw({'op':'tree','tabId':tab['tabId']});need(self.raw({'op':'tabs'})==windows,'alias-v3-tabs-changed');p={'tab':tab,'tree':tree,'observed_at':v.now()};v.page_scope(p,self.m,context);return p
    def mutation(self,cmd):
        s=v.doc(v.ref(v.base(self.m)/'operation.json'));step='open' if s.get('state')=='unknown-open' else 'close' if s.get('state')=='unknown-close' else None;need(step and s['manifest']==v.ref(v.base(self.m)/'manifest.json') and cmd==s[step+'_command'] and cmd.get('op')=='click' and cmd.get('kind')=='complaint-read','alias-v3-exact-saved-intent-required');return self.raw(cmd)

def tick(m,mr,transport):
    with core.e.operation_lock(m['root'],m['review_key']):
        guard(m);context,_,_,_,_=v.context(m);path=v.base(m)/'operation.json';s=v.doc(v.ref(path)) if path.exists() else {'kind':v.OP_KIND,'state':'ready','manifest':mr,'created_at':v.now(),'submission_enabled':False,'send_enabled':False}
        need(s['manifest']==mr and s['kind']==v.OP_KIND,'alias-v3-original-operation-required')
        if s['state'] in ('unknown-open','unknown-close'):return s
        if s['state']=='complete':v.verify_operation(v.ref(path));return s
        def save():v.w.atomic(path,s)
        def page(label,normal=False):
            p=transport.fresh();v.page_scope(p,m,context,normal=normal);s[label]=v.publish(v.base(m)/(label+'-'+uuid.uuid4().hex+'.json'),p);save();return p
        if s['state']=='ready':
            p=page('normal_before',True);s.update(state='unknown-open',open_command=core.e.click(p['tab']['tabId'],context['current']['action']['selector']));save();reply=transport.mutation(s['open_command']);s['open_reply_raw']=v.publish(v.base(m)/('open-reply-'+uuid.uuid4().hex+'.json'),reply);save();core.e.clicked(reply,s['open_command']);s.update(state='opened',open_reply=reply);save();return s
        if s['state']=='opened':
            p=page('drawer');p,_=core.e.settle_empty_drawer((p,s['drawer']),lambda:(page('drawer'),s['drawer']),{'job':context['fresh_job'],'page':v.doc(s['normal_before'])},s,save)
            parsed=c.parse_case(context['fresh_job'],p,text_schema=context['fresh_profile'].get('text_schema'));need(parsed['review']=={k:context['current'][k]for k in ('store','customer','text')},'alias-v3-current-drawer-review-changed');s['unbound_case']=v.publish(v.base(m)/'unbound-case.json',parsed);s.update(state='unknown-close',close_command=core.e.close_command(p));save();reply=transport.mutation(s['close_command']);s['close_reply_raw']=v.publish(v.base(m)/('close-reply-'+uuid.uuid4().hex+'.json'),reply);save();core.e.clicked(reply,s['close_command'],close=True);s.update(state='closed',close_reply=reply);save();return s
        need(s['state']=='closed','alias-v3-phase-invalid');page('normal_after',True);s.update(state='complete',completed_at=v.now());save();v.verify_operation(v.ref(path));return s

def load(mr):m=v.doc(mr);v.canonical_manifest(m,mr);return m

def run(mr,*,steps=10,request=None):
    need(type(steps) is int and 1<=steps<=10,'alias-v3-bounded-ticks-required');m=load(mr);path=v.base(m)/'operation.json'
    with (v.base(m)/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if path.exists():
            s=v.doc(v.ref(path));need(s['manifest']==mr,'alias-v3-original-operation-required')
            if s['state'] in ('unknown-open','unknown-close'):return {'state':'hold','reason':'unknown-no-replay','operation':v.ref(path),'ui_used':False}
            if s['state']=='complete':return {'state':'complete','operation':v.ref(path),'proof':v.verify_operation(v.ref(path)),'ui_used':False}
        guard(m);t=Transport(m,request)
        for _ in range(steps):
            s=tick(m,mr,t)
            if s['state']=='complete':return {'state':'complete','operation':v.ref(path),'proof':v.verify_operation(v.ref(path)),'ui_used':t.input_attempted}
            if s['state'] in ('unknown-open','unknown-close'):break
        return {'state':s['state'],'operation':v.ref(path),'ui_used':t.input_attempted}

def reconcile(mr,*,original_state_sha256,request=None):
    m=load(mr);path=v.base(m)/'operation.json'
    with (v.base(m)/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        with core.e.operation_lock(m['root'],m['review_key']):
            need(v.ref(path)['sha256']==original_state_sha256,'alias-v3-original-state-sha-required');s=v.doc(v.ref(path));need(s['manifest']==mr and s.get('state') in ('unknown-open','unknown-close'),'alias-v3-unknown-only-reconcile');guard(m,readonly=True);context,_,_,_,_=v.context(m);need(s['open_command']==core.e.click(v.doc(s['normal_before'])['tab']['tabId'],context['current']['action']['selector']),'alias-v3-original-open-command-changed');t=Transport(m,request,readonly=True);p=t.fresh();r=v.publish(v.base(m)/('reconcile-'+uuid.uuid4().hex+'.json'),p)
            if s['state']=='unknown-open':v.link(m,context,c.parse_case(context['fresh_job'],p,text_schema=context['fresh_profile'].get('text_schema')));s.update(state='opened',open_reconciliation={'kind':'readonly-open-effect-v3','ui_used':False,'page':r})
            else:
                need(s['close_command']==core.e.close_command(v.doc(s['drawer'])),'alias-v3-original-close-command-changed');v.page_scope(p,m,context,normal=True);s.update(state='closed',close_reconciliation={'kind':'readonly-close-effect-v3','ui_used':False,'page':r})
            v.w.atomic(path,s);return {'state':s['state'],'operation':v.ref(path),'ui_used':False,'input_replayed':False}

def verify(mr):m=v.doc(mr);r=v.ref(v.base(m)/'operation.json');return {'operation':r,'proof':v.verify_operation(r),'ui_used':False}
def record(mr):
    m=load(mr);r=v.ref(v.base(m)/'operation.json');proof=v.receipt(r);v.code_guard(m);receipt=v.publish(v.base(m)/'alias-receipt.json',proof);return {'receipt':receipt,'proof':v.verify_receipt(receipt),'ui_used':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='action',required=True);p=sub.add_parser('prepare')
    for x in ('origin-manifest','prior-apply','fresh-job','fresh-profile','normal-before','lease'):p.add_argument('--'+x,required=True);p.add_argument('--'+x+'-sha256',required=True)
    for action in ('run','reconcile','verify','record-reconciled','apply'):
        p=sub.add_parser(action);p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha256',required=True)
        if action=='run':p.add_argument('--steps',type=int,default=10)
        if action=='reconcile':p.add_argument('--original-state-sha256',required=True)
    args=ap.parse_args();r=lambda name:{'path':getattr(args,name.replace('-','_')),'sha256':getattr(args,name.replace('-','_')+'_sha256')}
    if args.action=='prepare':out=prepare(r('origin-manifest'),r('prior-apply'),{k:r(k.replace('_','-')) for k in ('fresh_job','fresh_profile','normal_before')},r('lease'))
    elif args.action=='run':out=run(r('manifest'),steps=args.steps)
    elif args.action=='reconcile':out=reconcile(r('manifest'),original_state_sha256=args.original_state_sha256)
    elif args.action=='verify':out=verify(r('manifest'))
    elif args.action=='record-reconciled':out=record(r('manifest'))
    else:
        import apply_case_alias_v3
        out=apply_case_alias_v3.apply(record(r('manifest'))['receipt'])
    print(json.dumps({'ok':True,**out},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'state':'hold','error':str(exc),'retry_input':False},ensure_ascii=False));raise SystemExit(2)
