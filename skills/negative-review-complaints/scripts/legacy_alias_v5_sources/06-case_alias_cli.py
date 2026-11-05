#!/usr/bin/env python3
"""Candidate explicit unbound complaint inspection, existing DOM bridge only.
prepare/verify/record-reconciled are offline. run alone may perform the two
existing complaint-read open/close UI actions. Never submit, capture or send.
"""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
if __name__=='__main__':
    sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
    from runtime_entry import ensure_runtime
    ensure_runtime()
sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
import argparse,copy,fcntl,json,re,uuid
from datetime import datetime,timezone
import case_alias as c
import unbound_case_runner as runner
import bridge
need=c.need
need(Path(c.__file__).resolve()==Path(__file__).with_name('case_alias.py').resolve() and Path(runner.__file__).resolve()==Path(__file__).with_name('unbound_case_runner.py').resolve(),'alias-local-module-identity-required')
LEASE=PROJECT/'runtime/workshop-director/state.json'
BUSINESS_ROOT=PROJECT/'runtime/negative-review-complaints'
CONTENT=PROJECT/'skills/chrome-dom-export/extension/content.js'
CODE=[Path(__file__),Path(c.__file__),Path(runner.__file__),Path(runner.e.__file__),Path(runner.n.__file__),Path(runner.r.__file__),Path(runner.workflow.__file__),Path(runner.n.authority.__file__),Path(sys.modules[runner.n.public_identity.__module__].__file__),Path(runner.e.orders_api.__file__),Path(bridge.__file__),CONTENT,CONTENT.with_name('policy.js')]

def canonical(path):
    p=Path(path);need(p.is_absolute() and p==p.resolve() and not any(q.is_symlink() for q in [p,*p.parents]),'alias-cli-canonical-path-required');return p
def order_document(ref):canonical(ref['path']);return c.document(ref)
def archive_bytes(path,raw,expected_sha256):
    import os
    need(c.hashlib.sha256(raw).hexdigest()==expected_sha256,'alias-archive-origin-changed');p=canonical(path)
    if p.exists():need(p.read_bytes()==raw,'alias-archive-bytes-conflict')
    else:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return c.ref(p)
def lease_binding(s,*,readonly_reconcile=False):
    need(s.get('version')==2 and s.get('index')==1 and s.get('phase') in (('running','attention') if readonly_reconcile else ('running',)) and s.get('test_target')=='测试群请忽略' and s.get('production_enabled') is False and s.get('complaint_submission_enabled') is False,'alias-complaint-current-lease-required')
    need(s.get('dispatch_id')==s['day']+':negative-review-complaints:'+str(s['attempt']) and bool(s.get('tool_receipt')),'alias-dispatch-identity-invalid')
    return {k:s[k] for k in ('version','day','index','dispatch_id','attempt','tool_receipt','dispatch_intent_at','dispatched_at','test_target','production_enabled','complaint_submission_enabled')}
def folder(m):return canonical(m['root'])/'existing-result-operations'/c.hashlib.sha256(m['review_key'].encode()).hexdigest()/'unbound-case'
def root_guard(m):
    ledger=c.document(m['inputs']['ledger']);company=ledger.get('company');need(isinstance(company,str) and company not in ('','.','..') and Path(company).name==company,'alias-company-path-invalid')
    need(canonical(m['root'])==canonical(BUSINESS_ROOT)/company,'alias-canonical-business-root-required')
def identity(m,manifest_ref):
    root_guard(m)
    need(c.ref(folder(m)/'manifest.json')==manifest_ref and order_document(manifest_ref)==m,'alias-original-canonical-manifest-required')
    need(m['order']==c.ref(m['order']['path']),'alias-order-changed');order=order_document(m['order']);expected={k:v for k,v in m.items() if k not in ('order','lease','code','original_ledger')};expected=copy.deepcopy(expected);expected['inputs']['ledger']=m['original_ledger'];need(order['manifest']==expected,'alias-order-manifest-mismatch')
    need(set(m['code'])=={str(p.resolve()) for p in CODE} and all(c.ref(p)['sha256']==h for p,h in m['code'].items()),'alias-cli-code-changed')
    snap=order_document(m['lease']['snapshot']);need(m['lease']['snapshot']['sha256']==m['lease']['observed']['sha256'] and m['lease']['observed']['path']==m['lease']['current_path']==str(LEASE) and lease_binding(snap)==m['lease']['binding'],'alias-pinned-lease-invalid')
    return m

def live_guard(m,*,readonly_reconcile=False):
    need(m['lease']['current_path']==str(LEASE),'alias-original-lease-path-required');current=json.loads(canonical(LEASE).read_bytes());need(lease_binding(current,readonly_reconcile=readonly_reconcile)==m['lease']['binding'],'alias-current-lease-changed')
    for path,digest in m['code'].items():need(c.ref(path)['sha256']==digest,'alias-cli-code-changed')
    need(c.ref(m['original_ledger']['path'])==m['original_ledger'],'alias-original-ledger-changed')
    runner.inputs(m) # all actual pinned source/ledger/drawer dependencies re-read

def prepare(order_ref,lease_ref):
    order=order_document(order_ref);need(set(order)=={'kind','manifest','actions','never','person_identity_verified'} and order['kind']=='unbound-complaint-case-read-order-v1' and order['actions']==['complaint-read:open','complaint-read:close'] and order['never']==['complaint','submit','capture','send','record_result','case_memory'] and order['person_identity_verified'] is False,'alias-explicit-read-order-required')
    m=copy.deepcopy(order['manifest']);need(set(m)=={'kind','root','review_key','inputs','old_result','old_drawer','pending_drawers','legacy_operations'} and m['kind']=='unbound-case-inspection-manifest-v1','alias-order-manifest-schema-invalid')
    need(lease_ref['path']==str(LEASE),'alias-canonical-current-lease-required');lease=order_document(lease_ref);binding=lease_binding(lease)
    runner.inputs(m);root_guard(m)
    with runner.e.operation_lock(m['root'],m['review_key']) as parent:
        runner.barriers(parent,m);base=folder(m);base.mkdir(exist_ok=True)
        # Source-root/key path is stable across every reattempt/source nickname.
        # A different order cannot create an alternative journal for old unknown.
        mp=base/'manifest.json'
        if mp.exists():
            previous=json.loads(mp.read_bytes());need(previous.get('order')==order_ref,'alias-original-order-required');identity(previous,c.ref(mp));return c.ref(mp)
        need(not (base/'operation.json').exists(),'alias-existing-unbound-operation-requires-original-manifest')
        original_ledger=m['inputs']['ledger'];c.document(original_ledger);ledger_snapshot=archive_bytes(base/('original-ledger-'+original_ledger['sha256']+'.json'),Path(original_ledger['path']).read_bytes(),original_ledger['sha256'])
        m['inputs']['ledger']=ledger_snapshot;m['original_ledger']=original_ledger
        snapshot=archive_bytes(base/('dispatch-lease-'+lease_ref['sha256']+'.json'),Path(lease_ref['path']).read_bytes(),lease_ref['sha256'])
        m.update(order=order_ref,lease={'snapshot':snapshot,'observed':lease_ref,'current_path':str(LEASE),'binding':binding},code={str(p.resolve()):c.ref(p.resolve())['sha256'] for p in CODE})
        need(c.ref(LEASE)==lease_ref,'alias-lease-changed-during-prepare');return runner.publish(mp,m)

class BridgeTransport:
    def __init__(self,m,base,request=None,*,readonly_reconcile=False):
        self.m=m;self.base=base;self.readonly_reconcile=readonly_reconcile;self.request_fn=request or (lambda cmd:bridge.request(cmd,timeout=50));self.attempt=base/'transport'/uuid.uuid4().hex;self.attempt.mkdir(parents=True);self.sequence=0;self.input_attempted=False
        raw=CONTENT.read_text();build=re.findall(r"const BUILD='([^']+)'",raw);need(len(build)==1,'alias-content-build-ambiguous');self.build=build[0]
    def raw(self,cmd):
        need(not self.readonly_reconcile or cmd.get('op') in ('tabs','ping','tree'),'alias-reconcile-readonly-capability')
        live_guard(self.m,readonly_reconcile=self.readonly_reconcile);self.sequence+=1;p=self.attempt/(str(self.sequence).zfill(3)+'.json')
        if cmd.get('op')=='click':self.input_attempted=True
        try:response=self.request_fn(cmd)
        except Exception as exc:
            runner.publish(p,{'command':cmd,'exception':{'type':type(exc).__name__,'message':str(exc)},'at':datetime.now(timezone.utc).isoformat()});raise
        runner.publish(p,{'command':cmd,'response':response,'at':datetime.now(timezone.utc).isoformat()});need(response.get('ok') is True,'alias-bridge-request-failed');return response['result']
    def fresh(self):
        v=runner.inputs(self.m);expected=v['normal_before']['pages'][0]['tab'];windows=self.raw({'op':'tabs'})
        focused=[w for w in windows if w.get('focused') is True];need(len(focused)==1 and focused[0].get('windowId')==expected['windowId'],'alias-current-window-not-focused')
        tabs=[t for t in focused[0].get('tabs',[]) if t.get('active') is True];need(len(tabs)==1,'alias-active-tab-not-unique');tab=tabs[0]
        need(all(tab.get(k)==expected[k] for k in ('tabId','windowId','url')) and tab.get('allowed') is True,'alias-current-tab-url-changed')
        ping=self.raw({'op':'ping','tabId':tab['tabId']});need(ping.get('version')==bridge.SAFETY_VERSION and ping.get('content_build')==self.build and ping.get('safety')=='DOM-only','alias-reviewed-content-not-loaded')
        tree=self.raw({'op':'tree','tabId':tab['tabId']});after=self.raw({'op':'tabs'});need(after==windows,'alias-tabs-changed-during-read')
        page={'tab':tab,'tree':tree,'observed_at':datetime.now(timezone.utc).isoformat()};runner.page_scope(page,v);return page
    def mutation(self,cmd):
        # A typed click is only issued in the original saved unknown intention,
        # by tick() immediately after its fresh public page. This is not retry.
        s=json.loads((self.base/'operation.json').read_bytes());need(s['manifest']==self.m,'alias-original-operation-required')
        phase=s.get('state');name='open' if phase=='unknown-open' else 'close' if phase=='unknown-close' else None
        need(name is not None and cmd==s[name+'_command'] and cmd.get('op')=='click' and cmd.get('kind')=='complaint-read','alias-unreviewed-command')
        return self.raw(cmd)

def run(manifest_ref,*,steps=10,request=None):
    need(type(steps) is int and 1<=steps<=10,'alias-bounded-ticks-required');m=identity(order_document(manifest_ref),manifest_ref);base=folder(m)
    with (base/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);live_guard(m);path=base/'operation.json'
        if path.exists():
            s=json.loads(path.read_bytes());need(s['manifest']==m,'alias-original-operation-required')
            if s.get('state') in ('unknown-open','unknown-close'):return {'state':'hold','reason':'unknown-no-replay','operation':c.ref(path),'ui_used':False}
            if s.get('state')=='complete':return {'state':'complete','operation':c.ref(path),'alias':runner.verify_complete(s),'ui_used':False}
        transport=BridgeTransport(m,base,request)
        for _ in range(steps):
            s=runner.tick(m,read_page=transport.fresh,request=transport.mutation)
            if s['state'] in ('unknown-open','unknown-close'):break
            if s['state']=='complete':return {'state':'complete','operation':c.ref(path),'alias':runner.verify_complete(s),'ui_used':transport.input_attempted}
        return {'state':s['state'],'operation':c.ref(path),'ui_used':transport.input_attempted}

def reconcile(manifest_ref,*,original_state_sha256,request=None):
    m=identity(order_document(manifest_ref),manifest_ref);base=folder(m)
    with (base/'.run.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);live_guard(m,readonly_reconcile=True);path=base/'operation.json'
        need(c.ref(path)['sha256']==original_state_sha256,'alias-original-state-sha-required');s=json.loads(path.read_bytes());need(s['manifest']==m and s.get('state') in ('unknown-open','unknown-close'),'alias-unknown-only-reconciliation')
        transport=BridgeTransport(m,base,request,readonly_reconcile=True)
        value=runner.reconcile(m,expected_state_sha256=original_state_sha256,read_page=transport.fresh)
        return {'state':value['state'],'operation':c.ref(path),'ui_used':False,'input_replayed':False}

def verify(manifest_ref):
    m=identity(order_document(manifest_ref),manifest_ref);p=folder(m)/'operation.json';s=json.loads(p.read_bytes());need(s['manifest']==m,'alias-original-operation-required');return {'operation':c.ref(p),'alias':runner.verify_complete(s),'ui_used':False}
def record_reconciled(manifest_ref):
    out=verify(manifest_ref);m=order_document(manifest_ref);receipt=runner.record_reconciled(out['operation'],folder(m)/'alias-receipt.json');return {'receipt':receipt,'alias':runner.validate_alias(receipt),'ledger_modified':False,'case_memory_modified':False,'ui_used':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    q=sub.add_parser('prepare')
    for f in ('order','order-sha256','lease','lease-sha256'):q.add_argument('--'+f,required=True)
    for action in ('run','verify','record-reconciled','reconcile'):
        q=sub.add_parser(action);q.add_argument('--manifest',required=True);q.add_argument('--manifest-sha256',required=True)
        if action=='run':q.add_argument('--steps',type=int,default=10)
        if action=='reconcile':q.add_argument('--original-state-sha256',required=True)
    args=p.parse_args()
    if args.action=='prepare':out={'manifest':prepare({'path':args.order,'sha256':args.order_sha256},{'path':args.lease,'sha256':args.lease_sha256}),'ui_used':False}
    else:
        ref={'path':args.manifest,'sha256':args.manifest_sha256}
        out=run(ref,steps=args.steps) if args.action=='run' else reconcile(ref,original_state_sha256=args.original_state_sha256) if args.action=='reconcile' else verify(ref) if args.action=='verify' else record_reconciled(ref)
    print(json.dumps({'ok':True,**out},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'state':'hold','error':str(exc),'retry_input':False},ensure_ascii=False));raise SystemExit(2)
