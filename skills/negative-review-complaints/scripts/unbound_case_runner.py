"""Isolated unbound reader API; transport is explicitly injected, never created.
Candidate only: no production ledger/capture/submit/send entry point.
"""
import copy,hashlib,json,os,uuid
from datetime import datetime,timezone
from pathlib import Path
import case_alias as c
import existing_result_runner as e
import normal_observation as n
import result_observation as r
import workflow
need=c.need
def now():return datetime.now(timezone.utc).isoformat()

def publish(path,value):
    raw=c.encoded(value);p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():need(p.read_bytes()==raw,'alias-immutable-evidence-conflict')
    else:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return c.ref(p)
def save(path,value):
    # Reuse the existing fsync/atomic implementation, not an alternative writer.
    workflow.atomic(Path(path),value)

def task_source_review(task_review,row):
    # Actual workflow stores the nine business fields, while the source row
    # additionally carries DOM/authority/action metadata. Compare exact facts,
    # not differently shaped serialization envelopes. No nickname is omitted.
    fields={'customer','customer_id','date','product','review_id','stars','store','text','time'}
    need(set(task_review)==fields,'alias-task-review-schema-invalid')
    need(task_review=={k:row.get(k,'') if k=='customer_id' else row[k] for k in fields},'alias-original-review-source-facts-mismatch')

def verify_old_order(v,m,review):
    orders=v['old_orders'];src=v['old_source'];job=v['old_job']
    need(orders.get('kind')=='existing-complaint-result-orders-v1' and orders.get('submission_enabled') is False and orders.get('send_enabled') is False,'alias-original-read-orders-required')
    need(orders['inputs']=={k:m['inputs']['old_'+k] for k in ('job','source','envelope','profile')},'alias-original-order-inputs-mismatch')
    need(orders.get('company')==job['company']==src['company'] and str(orders.get('groupid'))==str(job['groupid'])==str(src['groupid']) and orders.get('range')=={k:src[k] for k in ('start','end_exclusive')},'alias-original-order-scope-mismatch')
    found=[o for o in orders['orders'] if o.get('review_key')==m['review_key']];need(len(found)==1,'alias-original-order-not-unique');o=found[0]
    need(o['snapshot_sha256']==m['inputs']['old_source']['sha256'] and o['card_selector']==review['dom_selector'] and o['source_tuple']=={k:review[k] for k in ('review_id','store','customer','text','stars','date')} and o['original_action']==review['action'] and o['original_action'] in ('查看投诉结果','投诉审核中') and o['click_kind']=='complaint-read' and o['allowed_actions']==['查看投诉结果','投诉审核中'] and o['never_click']==['投诉','再次投诉','提交'],'alias-original-order-tuple-or-action-mismatch')

def inputs(m):
    need(m.get('kind')=='unbound-case-inspection-manifest-v1','alias-manifest-kind')
    v={k:c.document(q) for k,q in m['inputs'].items()}
    need(set(v)=={'ledger','old_job','old_source','old_envelope','old_profile','old_orders','fresh_job','fresh_profile','normal_before'},'alias-explicit-inputs-required')
    root=Path(m['root']);origin=m.get('original_ledger',m['inputs']['ledger']);need(root.is_absolute() and origin['path']==str(root/'state.json') and origin['sha256']==m['inputs']['ledger']['sha256'],'alias-canonical-ledger-required')
    oldjob=v['old_job'];src=v['old_source'];fresh=v['fresh_job'];ledger=v['ledger'];key=m['review_key']
    need(n.joined(oldjob,v['old_envelope'],v['old_profile'],oldjob['source_receipt'],oldjob['source_receipt_sha256'])==src,'alias-original-source-not-reproducible')
    need(ledger.get('browser_backend')=='local-dom-bridge','alias-live-ledger-backend-required')
    need(all(oldjob[k]==fresh[k] for k in ('company','groupid','identity')) and ledger['company']==oldjob['company'] and str(ledger['groupid'])==str(oldjob['groupid']),'alias-scope-identity-mismatch')
    rows=[x for x in src['rows'] if str(src['groupid'])+':'+x['review_id']==key];need(len(rows)==1,'alias-old-review-not-unique');review={**rows[0],'review_key':key}
    verify_old_order(v,m,review)
    task=ledger['tasks'][key];task_source_review(task['review'],rows[0]);need(task['result']['status']=='pending' and task['result']['evidence']==m['old_result'],'alias-original-ledger-review-result-mismatch')
    original=c.document(m['old_result']);oldpage=c.document(m['old_drawer']);parsed=r.parse(oldjob,oldpage,review,text_schema=v['old_profile'].get('text_schema'))
    need(all(original.get(k)==val for k,val in parsed.items()),'alias-old-result-not-reproducible');old=c.parse_case(oldjob,oldpage,text_schema=v['old_profile'].get('text_schema'))
    pending=[]
    relevant={k:t for k,t in ledger['tasks'].items() if (t.get('result') or {}).get('status')=='pending' and all(t.get('review',{}).get(f)==review[f] for f in ('store','text','product','stars'))}
    need(set(m['pending_drawers'])==set(relevant),'alias-complete-pending-scope-required')
    for k,t in relevant.items():
        p=c.document(m['pending_drawers'][k]);pout=r.parse(oldjob,p,t['review'],text_schema=v['old_profile'].get('text_schema'));ev=c.document(t['result']['evidence'])
        need(all(ev.get(f)==val for f,val in pout.items()),'alias-pending-result-not-reproducible')
        pending.append({'review_key':k,'review':t['review'],'case':c.parse_case(oldjob,p,text_schema=v['old_profile'].get('text_schema'))['case']})
    need(len(v['normal_before'].get('pages',[]))==1,'alias-multipage-live-reader-not-supported')
    need(type(v['normal_before']['pages'][0]['tab'].get('windowId')) is int,'alias-explicit-window-required')
    current,obs=c.candidates(fresh,v['normal_before'],v['fresh_profile'],review)
    need(current['customer']!=review['customer'],'alias-no-name-conflict')
    v.update(review=review,old_case=old,pending=pending,current=current,normal_observation=obs)
    return v

def page_scope(page,v,*,after=False):
    first=v['normal_before']['pages'][v['current'].get('page_index',1)-1];tab,_=n.context(page,v['fresh_job']['groupid']);before=first['tab']
    need(all(tab.get(k)==before.get(k) for k in ('tabId','windowId','url')) and type(tab.get('windowId')) is int,'alias-tab-window-url-changed')
    need(n.authority.stamp(page['observed_at'])>=n.authority.stamp(first['observed_at']),'alias-page-time-reversed')
    if after:
        n.public_identity(page['tree'],v['fresh_job']['identity'])
        env=copy.deepcopy(v['normal_before']);need(len(env['pages'])==1,'alias-multipage-live-reader-not-supported');env['pages']=[page]
        current,_=c.candidates(v['fresh_job'],env,v['fresh_profile'],v['review']);need(current==v['current'],'alias-normal-after-candidate-changed')
        need(not e.drawers(page),'alias-normal-after-drawer-present')
    return page

def barriers(folder,m):
    for dirname in ('.review-capture-state','.review-region-state'):
        for p in (Path(m['inputs']['old_source']['path']).parent/dirname).glob('*.json'):
            value=json.loads(p.read_bytes());need(value.get('state')=='complete','alias-original-capture-unresolved')
    active=Path(folder)/'active.json'
    if active.exists():
        idx=json.loads(active.read_bytes());op=c.document(idx['operation']);need(op.get('state')=='complete','alias-original-active-operation-unfinished')
        vv,oo,rr=e.manifest_inputs(op['manifest'],historical_complete=True);e.verify_complete(op,op['manifest'],vv,oo,rr)
    # Known legacy operation references must be explicitly supplied and complete;
    # never infer a missing old operation as permission to reopen.
    declared=m.get('legacy_operations',[])
    for p in e.LEGACY.glob('*result-operation.json'):
        old=json.loads(p.read_bytes())
        if old.get('review_key')==m['review_key']:
            need(c.ref(p) in declared and old.get('state')=='complete','alias-legacy-operation-needs-explicit-adoption')
    for q in declared:
        old=c.document(q);need(old.get('review_key')==m['review_key'] and old.get('state')=='complete' and old.get('submission_enabled') is False,'alias-legacy-operation-invalid')
        # Existing public reply guards, plus independently replayed old drawer.
        e.clicked(old['open_reply'],old['open_command']);e.clicked(old['close_reply'],old['close_command'],close=True)

def tick(m,*,read_page,request):
    """One durable step. Callbacks reuse the existing authorized connector only.
    Unknown commands never replay; they require explicit readonly reconcile().
    """
    v=inputs(m)
    with e.operation_lock(m['root'],m['review_key']) as folder:
        barriers(folder,m);base=Path(folder)/'unbound-case';base.mkdir(exist_ok=True);path=base/'operation.json'
        s=json.loads(path.read_bytes()) if path.exists() else {'kind':'unbound-case-operation-v1','state':'ready','created_at':now(),'manifest':m,'submission_enabled':False,'send_enabled':False}
        need(s['manifest']==m,'alias-original-manifest-required')
        if s['state'] in ('unknown-open','unknown-close'):return s
        if s['state']=='complete':verify_complete(s);return s
        def capture(label):
            p=read_page();page_scope(p,v);q=publish(base/(label+'-'+uuid.uuid4().hex+'.json'),p);s[label]=q;save(path,s);return p
        if s['state']=='ready':
            before=capture('normal_before');page_scope(before,v,after=True)
            cmd=e.click(before['tab']['tabId'],v['current']['action']['selector']);s.update(state='unknown-open',open_command=cmd);save(path,s)
            reply=request(cmd);s['open_reply_raw']=publish(base/('open-reply-'+uuid.uuid4().hex+'.json'),reply);save(path,s);e.clicked(reply,cmd);s.update(state='opened',open_reply=reply);save(path,s);return s
        if s['state']=='opened':
            page=capture('drawer');page,_=e.settle_empty_drawer((page,s['drawer']),lambda:(capture('drawer'),s['drawer']),{'job':v['fresh_job'],'page':c.document(s['normal_before'])},s,lambda:save(path,s))
            parsed=c.parse_case(v['fresh_job'],page,text_schema=v['fresh_profile'].get('text_schema'));need(parsed['review']=={k:v['current'][k]for k in ('store','customer','text')},'alias-current-drawer-review-changed')
            # Complete mismatch is evidence, never implicit linkage or a retry.
            s['unbound_case']=publish(base/'unbound-case.json',parsed);s.update(state='unknown-close',close_command=e.close_command(page));save(path,s)
            reply=request(s['close_command']);s['close_reply_raw']=publish(base/('close-reply-'+uuid.uuid4().hex+'.json'),reply);save(path,s);e.clicked(reply,s['close_command'],close=True);s.update(state='closed',close_reply=reply);save(path,s);return s
        need(s['state']=='closed','alias-operation-phase-invalid');after=capture('normal_after');page_scope(after,v,after=True);s['state']='complete';s['completed_at']=now();save(path,s);verify_complete(s);return s

def verify_complete(s):
    need(s.get('state')=='complete' and s.get('submission_enabled') is False and s.get('send_enabled') is False,'alias-operation-not-complete');v=inputs(s['manifest'])
    before=page_scope(c.document(s['normal_before']),v,after=True);drawer=page_scope(c.document(s['drawer']),v);page_scope(c.document(s['normal_after']),v,after=True)
    need(n.authority.stamp(s['created_at'])<=n.authority.stamp(before['observed_at'])<=n.authority.stamp(drawer['observed_at'])<=n.authority.stamp(c.document(s['normal_after'])['observed_at'])<=n.authority.stamp(s['completed_at']),'alias-operation-time-reversed')
    need(s['open_command']==e.click(before['tab']['tabId'],v['current']['action']['selector']) and s['close_command']==e.close_command(drawer),'alias-saved-command-changed')
    for step in ('open','close'):
        if s.get(step+'_reply_raw'):
            raw=c.document(s[step+'_reply_raw']);need(raw==s[step+'_reply'],'alias-raw-reply-changed');e.clicked(raw,s[step+'_command'],close=step=='close')
        else:
            rec=s.get(step+'_reconciliation',{});need(rec.get('ui_used') is False and rec.get('kind')=='readonly-'+step+'-effect-v1','alias-unknown-effect-unverified')
            p=page_scope(c.document(rec['page']),v,after=step=='close')
            if step=='open':need(c.parse_case(v['fresh_job'],p,text_schema=v['fresh_profile'].get('text_schema'))['review']=={k:v['current'][k] for k in ('store','customer','text')},'alias-reconciliation-review-changed')
    parsed=c.parse_case(v['fresh_job'],drawer,text_schema=v['fresh_profile'].get('text_schema'));need(parsed==c.document(s['unbound_case']),'alias-unbound-case-changed')
    return c.link(v['old_case'],parsed,v['review'],v['current'],v['pending'])

def record_reconciled(operation_ref,out):
    """Offline immutable receipt, never workflow.record_result or ledger mutation.
    Future explicit consumer must replay this operation. No screenshot grant.
    """
    s=c.document(operation_ref);proof=verify_complete(s);proof['operation']=operation_ref;proof['original_inputs']=s['manifest']['inputs'];proof['old_result']=s['manifest']['old_result'];proof['old_drawer']=s['manifest']['old_drawer']
    return publish(out,proof)


def reconcile(m,*,expected_state_sha256,read_page):
    """Explicit one-read effect reconciliation. Never calls request or makes reply."""
    v=inputs(m)
    with e.operation_lock(m['root'],m['review_key']) as folder:
        barriers(folder,m);base=Path(folder)/'unbound-case';path=base/'operation.json';need(c.ref(path)['sha256']==expected_state_sha256,'alias-original-state-sha-required');s=json.loads(path.read_bytes());need(s['manifest']==m and s['state'] in ('unknown-open','unknown-close'),'alias-unknown-only-reconciliation')
        need(s['open_command']==e.click(c.document(s['normal_before'])['tab']['tabId'],v['current']['action']['selector']),'alias-original-open-command-changed')
        if s['state']=='unknown-close':need(s['close_command']==e.close_command(c.document(s['drawer'])),'alias-original-close-command-changed')
        page=read_page();page_scope(page,v);q=publish(base/('reconcile-'+uuid.uuid4().hex+'.json'),page)
        if s['state']=='unknown-open':
            parsed=c.parse_case(v['fresh_job'],page,text_schema=v['fresh_profile'].get('text_schema'));need(parsed['review']=={k:v['current'][k] for k in ('store','customer','text')},'alias-reconcile-wrong-review');s['drawer']=q;s['open_reconciliation']={'kind':'readonly-open-effect-v1','ui_used':False,'page':q};s['state']='opened'
        else:
            page_scope(page,v,after=True);s['normal_after']=q;s['close_reconciliation']={'kind':'readonly-close-effect-v1','ui_used':False,'page':q};s['state']='closed'
        save(path,s);return s


def validate_alias(receipt_ref):
    receipt=c.document(receipt_ref);s=c.document(receipt['operation']);expected=verify_complete(s)
    expected.update(operation=receipt['operation'],original_inputs=s['manifest']['inputs'],old_result=s['manifest']['old_result'],old_drawer=s['manifest']['old_drawer'])
    need(receipt==expected,'alias-receipt-not-reproducible');return expected
