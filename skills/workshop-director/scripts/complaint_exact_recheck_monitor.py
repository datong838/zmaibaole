"""Pure exact-case monitor. Real closure AND result/Excel/KB application only.
No UI, runner construction, live lease hash, writer or self-reported authority.
"""
import hashlib,importlib,json,sys
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime,timezone
SCHEMA='exact-existing-case-recheck-v1'
KIND='exact-existing-case-operation-v1'
DIRECTORY=Path(__file__).resolve().parents[2]/'negative-review-complaints/scripts'
def need(ok,code):
    if not ok:raise ValueError(code)
def stamp(value):
    value=value if isinstance(value,datetime) else datetime.fromisoformat(value);need(value.utcoffset() is not None,'exact-monitor-aware-time');return value
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@contextmanager
def reader():
    previous=list(sys.path)
    try:
        sys.path.insert(0,str(DIRECTORY));x=importlib.import_module('complaint_exact_recheck');need(Path(x.__file__).resolve()==DIRECTORY/'complaint_exact_recheck.py','exact-monitor-module-origin');refs={};raw=x.o.raw
        def tracked(ref):
            data=raw(ref);key=(ref['path'],ref['sha256']);refs[key]=dict(ref);return data
        # Exact producer's pure replay entry points use this one SHA reader.
        # It still validates current bytes on EVERY read; nothing is memoized.
        x.o.raw=tracked
        try:yield x,refs
        finally:x.o.raw=raw
        for ref in refs.values():raw(ref)
    finally:sys.path[:]=previous

def inspect(path,state):
    need(state.get('kind')==KIND and state.get('submission_enabled') is False and not any(state.get(k) for k in ('error','hold','last_error')),'exact-monitor-policy-or-error');need(state.get('state') in ('preflight','open-ready','opened','close-ready','verify-closed','complete'),'exact-monitor-unknown-state')
    with reader() as (x,refs):
        path=x.o.canonical(Path(path));journal=x.o.ref(path);need(x.o.doc(journal)==state,'exact-monitor-original-journal');mr=state['manifest'];m=x.o.doc(mr);x.canonical_manifest(m,mr);need(path==x.folder(m)/'operation.json','exact-monitor-canonical-operation');idx=x.o.ref(x.base(m['root'],m['review_key'])/'active.json');need(x.o.doc(idx)=={'kind':'exact-recheck-active-v1','review_key':m['review_key'],'manifest':mr},'exact-monitor-current-owner');_,v,old,task,row,case=x.inputs(m)
        created=stamp(state['created_at']);need(stamp(m['created_at'])<=created<=datetime.now(timezone.utc),'exact-monitor-created-time')
        phase=state['state'];closure=None
        if phase in ('opened','close-ready','verify-closed'):
            before=x.o.doc(state['normal_before']);x.verify_page_transport(before,m);target=x.normal_page(before,v,row);need(state['open_command']==x.r.click(before['tab']['tabId'],target['selector']),'exact-monitor-open-command')
            if state.get('open_reply'):
                raw=x.o.doc(state['open_reply_raw']);need(raw.get('ok') is True and raw['result']==state['open_reply'],'exact-monitor-open-reply');x.r.clicked(state['open_reply'],state['open_command'])
            else:need(state.get('open_reconciliation')==state.get('drawer'),'exact-monitor-open-reconcile')
            if phase in ('close-ready','verify-closed'):
                drawer=x.o.doc(state['drawer']);x.verify_page_transport(drawer,m);value=x.parsed(m,v,row,drawer);need(value==x.o.doc(state['result_input']),'exact-monitor-drawer-result')
            if phase=='verify-closed':
                close=x.o.doc(state['drawer_before_close']);x.verify_page_transport(close,m);need(state['close_command']==x.r.close_command(close),'exact-monitor-close-command');raw=x.o.doc(state['close_reply_raw']);need(raw.get('ok') is True and raw['result']==state['close_reply'],'exact-monitor-close-reply');x.r.clicked(state['close_reply'],state['close_command'],close=True)
        apply_path=x.folder(m)/'apply/operation.json'
        if phase=='complete':
            proof=x.verify_complete(journal)
            if apply_path.exists():
                ar=x.o.ref(apply_path);audit=x.o.doc(ar);need(audit.get('kind')=='apply-exact-existing-case-v1' and audit.get('manifest')==mr and audit.get('state') in ('record-intent','recorded','complete') and not audit.get('error'),'exact-monitor-apply-shape')
                if audit['state']=='complete':
                    x.verify_apply(ar);current=x.o.doc(x.o.ref(Path(m['root'])/'state.json'));recorded=x.o.doc(audit['recorded_state']);need(current['tasks'][m['review_key']]==recorded['tasks'][m['review_key']],'exact-monitor-current-task-rewritten');receipt=x.o.doc(audit['receipt']);need(receipt['operation']==journal and receipt['manifest']==mr,'exact-monitor-original-closure');after=stamp(x.o.doc(state['normal_after'])['observed_at']);before=stamp(x.o.doc(state['normal_before'])['observed_at']);drawer=stamp(x.o.doc(state['drawer'])['observed_at']);ended=stamp(state['completed_at']);applied=stamp(audit['completed_at']);need(created<=before<=drawer<=after<=ended<=applied<=datetime.now(timezone.utc),'exact-monitor-time-order')
                    # Mutable append-only KB: recheck the selected observation,
                    # not the whole JSONL hash (other cases may legitimately add).
                    obs=audit['memory_observation'];records=[r for r in x.memory.read_records() if r.get('observation_id')==obs['observation_id']];need(len(records)==1,'exact-monitor-memory-record');record=records[0]
                    for label in ('source','result'):
                        ref=record['original_observation_refs'][label];need(ref['sha256']==record[label+'_ref']['sha256'],'exact-monitor-memory-original-ref');x.o.raw(ref)
                    business={'company':old['company'],'review_key':m['review_key'],'original_source_sha256':task['latest_snapshot']['sha256'],'case_signature':digest({'review':task['review'],'case':case})};closure={'operation':journal,'manifest':mr,'apply':ar,'result':audit['result'],'identity':{'kind':'closed-exact-existing-case','review_key':m['review_key']},'business_binding':business,'created_at':created.isoformat(),'completed_at':after.isoformat(),'operation_completed_at':ended.isoformat(),'apply_completed_at':applied.isoformat(),'normal_before':state['normal_before'],'normal_after':state['normal_after'],'dispatch_id':m['dispatch_id'],'day':m['day'],'dispatch_started_at':m['lease_binding']['dispatch_intent_at']}
        elif apply_path.exists():need(x.o.doc(x.o.ref(apply_path)).get('state')!='complete','exact-monitor-completed-regressed')
        # Reading source/normal/profile, raw replies, original order, code and
        # archives above traverses the exact verifier's real SHA dependencies.
        x.o.raw(x.o.ref(Path(__file__).resolve()));x.o.raw(journal);need(x.o.doc(journal)==state,'exact-monitor-state-changed-at-end');binding={'manifest':mr,'active_index':idx,'original_review_key':m['review_key'],'dispatch_id':m['dispatch_id']}
    return {'schema':SCHEMA,'binding':binding,'closure':closure,'artifact_refs':list(refs.values())}
def semantic(path,state,*,role):
    need(role=='complaint_operator','exact-monitor-role');proof=inspect(path,state);closed=proof['closure'];return {'schema':SCHEMA,'binding':proof['binding'],'tokens':{'closed-applied-exact-case':digest(closed)} if closed else {}}
def fresh(path,*,role,dispatch_started_at,now):
    need(role=='complaint_operator','exact-monitor-role');started=stamp(dispatch_started_at);present=stamp(now)
    with reader() as (x,refs):state=x.o.doc(x.o.ref(Path(path)))
    if state.get('state')!='complete' or not state.get('created_at') or not state.get('completed_at'):return None
    created=stamp(state['created_at']);ended=stamp(state['completed_at']);need(started<=present and created<=ended<=present,'exact-monitor-fresh-time')
    if created<started:return None
    checked=inspect(path,state);closed=checked['closure']
    if not closed:return None
    if stamp(closed['dispatch_started_at'])!=started:return None
    # Raw observation time, never the time the supervisor happened to read it.
    before=stamp(__import__('json').loads(Path(closed['normal_before']['path']).read_bytes())['observed_at']);after=stamp(closed['completed_at']);need(started<=created<=before<=after<=ended<=stamp(closed['apply_completed_at'])<=present,'exact-monitor-fresh-window')
    return {'kind':'verified-fresh-completed-evidence-v1','schema':SCHEMA,'dedup_key':digest(closed['identity']),'business_identity':closed['identity'],'business_binding':closed['business_binding'],'created_at':created.isoformat(),'completed_at':after.isoformat(),'artifact_refs':checked['artifact_refs']}
