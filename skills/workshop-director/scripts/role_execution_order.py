"""Immutable role handoff. Candidate: violation only, no dispatch/UI/ledger writes."""
import hashlib,json,os,re,tempfile
from datetime import date
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
FLOW='violation-notifier';ROLE='violation_operator';KIND='role-execution-order-v1'
def need(ok,why):
    if not ok:raise ValueError(why)
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def digest(v):return hashlib.sha256(encode(v)).hexdigest()
def canonical(p):
    p=Path(p);need(p.is_absolute() and not p.is_symlink() and p.resolve()==p,'execution-absolute-canonical-path-required');return p
def ref(p):
    p=canonical(Path(p).absolute());return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def raw(r):
    need(type(r) is dict and set(r)=={'path','sha256'},'execution-reference-shape');p=canonical(r['path']);b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'execution-reference-changed');return b
def doc(r):return json.loads(raw(r))
def immutable(p,v):
    p=Path(p);b=encode(v);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():need(p.read_bytes()==b,'execution-immutable-conflict')
    else:
        fd,tmp=tempfile.mkstemp(dir=p.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,p)
            except FileExistsError:need(p.read_bytes()==b,'execution-immutable-conflict')
        finally:os.unlink(tmp)
    return ref(p)
def order_path(root,dispatch):return canonical(root)/'role-execution-orders'/(hashlib.sha256(dispatch.encode()).hexdigest()+'.json')
def location(order):return canonical(order['path']).parent.parent/'role-executions'/Path(order['path']).stem
def build(offer_ref,daily_report_ref):
    offer=doc(offer_ref);need(offer.get('workflow')==FLOW and offer.get('role')==ROLE and (offer.get('tool')=='collaboration.followup_task' and 'dispatcher_protocol' not in offer or offer.get('tool')=='local-subprocess-v1' and offer.get('dispatcher_protocol')=='local-subprocess-v1') and offer.get('action')=='dispatch','execution-exact-role-offer-required')
    match=re.fullmatch(r'(\d{4}-\d{2}-\d{2}):violation-notifier:(0|[1-9]\d*)',offer.get('dispatch_id',''));need(match is not None,'execution-dispatch-id-invalid');day=match[1];date.fromisoformat(day)
    report=doc(daily_report_ref);staged=offer.get('collection_contract')=='three-flow-collection-ready-v1'
    need(offer.get('collection_contract')in(None,'three-flow-collection-ready-v1'),'execution-collection-contract-invalid')
    if staged:
        import daily_orchestration
        facts=daily_orchestration.verified_collection_ready_facts(daily_report_ref)
        need(report.get('workflow')=='daily-comment-stats'and report.get('day')==day and report.get('collection_ready')is True and report.get('complete')is False and facts['order']['day']==day,'execution-current-daily-ready-required')
    else:need(report.get('workflow')=='daily-comment-stats' and report.get('day')==day and report.get('kind')=='daily-director-completion-report-v1' and report.get('complete') is True and report.get('live') is True and report.get('test_target')=='测试群请忽略' and report.get('production_sent') is False,'execution-current-daily-completion-required')
    import execution_timing as company_scope
    names=company_scope.offer_company_names(offer)
    entries=offer.get('ledger_snapshots');need(type(entries) is list and len(entries)==len(names)and {e.get('company')for e in entries}==set(names),'execution-exact-policy-company-ledgers-required');companies=[]
    for e in entries:
        state=doc(e['snapshot']);name=e['company'];need(name in names,'execution-inactive-company');root=PROJECT/'runtime'/FLOW/name
        need(e.get('workflow')==FLOW and e.get('original_path')==str(root/'state.json') and state.get('company')==name and str(state.get('groupid','')).isdigit(),'execution-canonical-company-ledger-required')
        need(state.get('mode')=='development' and state.get('browser_backend')=='local-dom-bridge','execution-test-localdom-only')
        start=state['next_start'];date.fromisoformat(start);need(start<=day,'execution-future-cursor')
        unfinished=[k for k,b in state['batches'].items() if not b.get('completed_at')]
        # Existing parent restarts reuse the same order. Adopting a batch that
        # predates this parent needs an explicit source-bound migration, never
        # a fresh key or guessed original workdir. One supervised exception
        # (B35): a sealed zero-verified send-free batch is a terminal zero
        # result whose key is exactly this order's scope; the archive-redispatch
        # protocol re-issues that identical scope and the execution ports
        # re-verify the same key, source, fingerprint and sealed shape before
        # the zero notice. Only that exact shape is adoptable here.
        adoptable=[k for k in unfinished
                   if state['batches'][k].get('start')==start and state['batches'][k].get('end_exclusive')==day and k==start+'_'+day
                   and state['batches'][k].get('status')=='zero_verified' and state['batches'][k].get('total')==0
                   and state['batches'][k].get('send_jobs')=={} and state['batches'][k].get('analysis')==[] and state['batches'][k].get('records')==[]
                   and state['batches'][k].get('artifacts')is None and state['batches'][k].get('copy')is None and state['batches'][k].get('copy_evidence')is None
                   and state['batches'][k].get('copy_parts')==[] and state['batches'][k].get('screenshots')==[] and state['batches'][k].get('screenshot_chains',[])==[]
                   and state['batches'][k].get('blocked_reason')is None and state['batches'][k].get('completed_at')is None]
        need(not [k for k in unfinished if k not in adoptable],'execution-preexisting-batch-needs-explicit-adoption')
        companies.append({'company':name,'groupid':str(state['groupid']),'root':str(root),'ledger':e['snapshot'],'start':start,'end_exclusive':day,'skipped':start==day})
    need(len({c['company'] for c in companies})==len(names) and len({c['groupid'] for c in companies})==len(names),'execution-duplicate-company')
    need(any(not c['skipped'] for c in companies),'execution-no-pending-company-range')
    scope={'workflow':FLOW,'company_ranges':[{k:c[k] for k in ('company','groupid','start','end_exclusive')} for c in companies if not c['skipped']],'test_target':'测试群请忽略','production_enabled':False,'platform_writes':False}
    return {'kind':KIND,'workflow':FLOW,'role':ROLE,'dispatch_id':offer['dispatch_id'],'day':day,'offer':offer_ref,**({'collection_contract':offer['collection_contract'],'daily_collection_ready':daily_report_ref}if staged else{'daily_completion':daily_report_ref}),'companies':companies,'scope':scope,'scope_sha256':digest(scope),'origin':'fresh',**({'active_company_policy':offer['active_company_policy']}if offer.get('active_company_policy')else{})}
def validate(reference):
    order=doc(reference);need(Path(reference['path'])==order_path(Path(reference['path']).parent.parent,order['dispatch_id']),'execution-canonical-order-required');need(order==build(order['offer'],order['daily_collection_ready']if order.get('collection_contract')else order['daily_completion']),'execution-order-not-derived');return order
def archive(root,offer,daily):
    v=build(offer,daily);return immutable(order_path(root,v['dispatch_id']),v)
