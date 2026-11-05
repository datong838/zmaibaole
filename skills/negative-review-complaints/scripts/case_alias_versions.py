"""Candidate immutable known-case versions; no UI or producer-v2 mutation."""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
import copy,hashlib,json,os,tempfile
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import case_alias_cli as v2
import legacy_alias_code_replay as legacy
import apply_case_alias as apply2
import case_memory # preload outside any audited pure replay transaction
import alias_replay_session as replay
import case_alias_code_release as release
c=v2.c;core=v2.runner;w=core.workflow;need=c.need
KIND='known-public-complaint-case-version-v3'
OP_KIND='known-public-complaint-case-operation-v3'
ZONE=ZoneInfo('Asia/Shanghai')

def now():return datetime.now(timezone.utc).isoformat()
def stamp(t):
    if isinstance(t,datetime):
        need(t.tzinfo is not None and t.utcoffset() is not None,'alias-v3-aware-time-required');return t
    return core.n.authority.stamp(t)
def ref(p):return c.ref(v2.canonical(p))
def doc(r):v2.canonical(r['path']);return c.document(r)
def datahash(v):return core.n.authority.data_hash(v)
def publish(path,value):
    raw=c.encoded(value);path=v2.canonical(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'alias-v3-immutable-conflict')
    else:
        fd,tmp=tempfile.mkstemp(prefix='.alias-v3-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,path)
            except FileExistsError:need(path.read_bytes()==raw,'alias-v3-immutable-conflict')
        finally:os.unlink(tmp)
        dfd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(dfd)
        finally:os.close(dfd)
    return ref(path)
def review_folder(root,key):return v2.canonical(root)/'existing-result-operations'/hashlib.sha256(key.encode()).hexdigest()
def version_id(binding,result_sha):return datahash({'dispatch_id':binding['dispatch_id'],'day':binding['day'],'original_result_sha256':result_sha})
def base(m):return review_folder(m['root'],m['review_key'])/'case-alias-v3'/m['version']
def index_path(m):return review_folder(m['root'],m['review_key'])/'case-alias-active.json'
def code_files():
    return [Path(release.__file__),*legacy.code_files(),Path(replay.__file__),Path(__file__),Path(__file__).with_name('case_alias_v3.py'),Path(__file__).with_name('apply_case_alias_v3.py'),Path(apply2.__file__),*v2.CODE,Path(PROJECT/'skills/negative-review-complaints/scripts/case_memory.py'),Path(PROJECT/'skills/negative-review-complaints/scripts/export-results.mjs')]
def codes():return {str(p.resolve()):ref(p.resolve())['sha256'] for p in code_files()}
def code_guard(m,*,allow_completed=False):
    if allow_completed and release.completed(m,base(m),doc):return
    need(m['code']==codes(),'alias-v3-code-changed')
def canonical_manifest(m,r,*,historical=False):
    need(m.get('kind')==KIND and r==ref(base(m)/'manifest.json') and doc(r)==m,'alias-v3-canonical-manifest-required');code_guard(m,allow_completed=historical)
    need(m['version']==version_id(m['lease']['binding'],m['previous_result']['sha256']),'alias-v3-version-binding-invalid')
    snap=doc(m['lease']['snapshot']);need(v2.lease_binding(snap)==m['lease']['binding'] and m['lease']['snapshot']['sha256']==m['lease']['observed']['sha256'] and m['lease']['observed']['path']==m['lease']['current_path']==str(v2.LEASE),'alias-v3-lease-snapshot-invalid')

def original(origin):
    m=doc(origin['manifest']);legacy.identity(m,origin['manifest']);need(origin['receipt']==ref(v2.folder(m)/'alias-receipt.json') and origin['apply']==ref(v2.folder(m)/'apply'/'operation.json'),'alias-v3-v2-origin-path-invalid')
    receipt=core.validate_alias(origin['receipt']);proof=legacy.verify(origin['manifest']);need(receipt['operation']==proof['operation'],'alias-v3-v2-origin-operation-invalid')
    audit=doc(origin['apply']);need(audit.get('kind')=='apply-public-case-alias-v1' and audit.get('state')=='complete' and audit['receipt']==origin['receipt'],'alias-v3-v2-apply-incomplete')
    oldledger=doc(m['inputs']['ledger']);oldt=oldledger['tasks'][m['review_key']];op=doc(receipt['operation']);value=apply2.result_input(origin['receipt'],op,m,oldt);need(doc(audit['result_input'])==value,'alias-v3-v2-result-invalid')
    ledger=doc(origin['application_ledger']);apply2.check_committed(Path(m['root']),ledger,m['review_key'],oldt,value,audit['result_input'])
    need(audit.get('memory_observation')==apply2.memory_observation(m,oldt,audit['result_input']),'alias-v3-v2-memory-unverified');ref(audit['workbook']['path']);need(ref(audit['workbook']['path'])==audit['workbook'],'alias-v3-origin-workbook-changed')
    return m,proof['alias'],oldledger

def anchor_view(m,origin_manifest):
    a=copy.deepcopy(origin_manifest)
    for name in ('fresh_job','fresh_profile','normal_before'):a['inputs'][name]=m['fresh'][name]
    return a

def context(m,stack=None):
    stack=[] if stack is None else stack;ident=(str(base(m)),m['version']);need(ident not in stack and len(stack)<128,'alias-v3-prior-cycle-or-depth');stack=stack+[ident]
    om,anchor,oldledger=original(m['origin']);need(m['root']==om['root'] and m['review_key']==om['review_key'],'alias-v3-original-key-root-changed')
    current=doc(m['current_ledger']);task=current['tasks'][m['review_key']];oldt=oldledger['tasks'][m['review_key']]
    need(current['company']==oldledger['company'] and str(current['groupid'])==str(oldledger['groupid']) and current['identity']==oldledger['identity'],'alias-v3-current-company-identity-changed')
    need(task['review']==oldt['review'] and task['latest_snapshot']==oldt['latest_snapshot'] and task['result']['evidence']==m['previous_result'] and task['result']['status']=='pending' and task['status']=='existing_pending','alias-v3-current-pending-source-changed')
    need(task['result']['original_complaint']==oldt['result']['original_complaint'],'alias-v3-original-public-case-changed')
    peers=[k for k,t in current['tasks'].items() if (t.get('result') or {}).get('status')=='pending' and all(t.get('review',{}).get(f)==oldt['review'][f] for f in ('store','text','product','stars'))];need(peers==[m['review_key']],'alias-v3-current-pending-case-not-unique')
    prior=m['prior']
    if prior['kind']=='v2':need(prior['apply']==m['origin']['apply'] and m['current_ledger']==m['origin']['application_ledger'],'alias-v3-initial-prior-mismatch')
    else:
        need(prior['kind']=='v3','alias-v3-prior-kind-invalid');previous=doc(prior['manifest']);need(previous['origin']==m['origin'] and previous['root']==m['root'] and previous['review_key']==m['review_key'],'alias-v3-prior-anchor-changed');verify_apply(prior['apply'],stack=stack);audit=doc(prior['apply']);need(audit['manifest']==prior['manifest'] and task['result']['evidence']['sha256']==audit['result_input']['sha256'],'alias-v3-prior-result-mismatch')
        # Exact recorded task, not a new ve task or synthetic alias source.
        recorded=doc(audit['recorded_state'])['tasks'][m['review_key']];need(task==recorded,'alias-v3-prior-current-task-changed')
    view=anchor_view(m,om);v=core.inputs(view)
    need(stamp(m['lease']['binding']['dispatch_intent_at'])<=stamp(m['prepared_at'])<=stamp(now()),'alias-v3-prepared-dispatch-time-invalid')
    return v,current,task,view,anchor

def active_guard(m):
    idx=doc(ref(index_path(m)));need(idx.get('kind')=='review-case-alias-active-v3' and idx['review_key']==m['review_key'] and idx['origin']==m['origin']['manifest'] and idx['current']==ref(base(m)/'manifest.json'),'alias-v3-original-active-owner-required')
    # All prior/canonical existing-result and capture unknown guards stay live.
    om=doc(m['origin']['manifest']);core.barriers(review_folder(m['root'],m['review_key']),om)
    current=w.load(Path(m['root']));need(datahash(current)==datahash(doc(m['current_ledger'])),'alias-v3-current-ledger-changed')
    for folder in (review_folder(m['root'],m['review_key'])/'case-alias-v3').glob('*'):
        if folder!=base(m) and (folder/'manifest.json').exists():
            pm=doc(ref(folder/'manifest.json'));need((folder/'apply'/'operation.json').exists(),'alias-v3-prior-unapplied');verify_apply(ref(folder/'apply'/'operation.json'))
    return idx

def page_scope(page,m,v,*,normal=False):
    first=v['normal_before']['pages'][0];tab,_=core.n.context(page,v['fresh_job']['groupid']);need(all(tab.get(k)==first['tab'].get(k) for k in ('tabId','windowId','url')),'alias-v3-tab-window-changed')
    created=m['lease']['binding']['dispatch_intent_at'];seen=stamp(page['observed_at']);need(stamp(created)<=seen<=stamp(now()),'alias-v3-fresh-page-outside-dispatch-time')
    if normal:
        core.n.public_identity(page['tree'],v['fresh_job']['identity']);env=copy.deepcopy(v['normal_before']);env['pages']=[page];current,_=c.candidates(v['fresh_job'],env,v['fresh_profile'],v['review']);need(current==v['current'] and not core.e.drawers(page),'alias-v3-normal-target-changed')
    return page

def link(m,v,parsed):
    old=v['old_case'];need(old['company']==parsed['company'] and old['groupid']==parsed['groupid'] and old['identity']==parsed['identity'],'alias-v3-case-company-identity-mismatch')
    need(parsed['case']==old['case'] and parsed['review']=={k:v['current'][k] for k in ('store','customer','text')},'alias-v3-case-or-candidate-mismatch')
    need(all(v['current'][k]==v['review'][k] for k in ('store','text','product','stars')),'alias-v3-original-review-facts-changed')
    return {'kind':'known-public-case-reinspection-proof-v3','original_review_key':m['review_key'],'original_customer':v['review']['customer'],'observed_customer':parsed['review']['customer'],'case_signature_sha256':datahash(c.signature(v['review'],old['case'])),'status':parsed['status'],'person_identity_verified':False,'screenshot_authorized':False,'authoritative_source_modified':False,'dispatch_id':m['lease']['binding']['dispatch_id'],'day':m['lease']['binding']['day']}

def verify_operation(operation_ref,*,stack=None):
    s=doc(operation_ref);m=doc(s['manifest']);canonical_manifest(m,s['manifest'],historical=True);need(operation_ref==ref(base(m)/'operation.json') and s.get('kind')==OP_KIND and s.get('state')=='complete' and s.get('submission_enabled') is False and s.get('send_enabled') is False,'alias-v3-operation-incomplete')
    v,_,_,_,_=context(m,stack);before=page_scope(doc(s['normal_before']),m,v,normal=True);drawer=page_scope(doc(s['drawer']),m,v);after=page_scope(doc(s['normal_after']),m,v,normal=True)
    need(stamp(m['prepared_at'])<=stamp(s['created_at'])<=stamp(before['observed_at'])<=stamp(drawer['observed_at'])<=stamp(after['observed_at'])<=stamp(s['completed_at'])<=stamp(now()),'alias-v3-operation-time-invalid')
    need(s['open_command']==core.e.click(before['tab']['tabId'],v['current']['action']['selector']) and s['close_command']==core.e.close_command(drawer),'alias-v3-command-mismatch')
    for step in ('open','close'):
        if s.get(step+'_reply') is not None:
            reply=doc(s[step+'_reply_raw']);need(reply==s[step+'_reply'],'alias-v3-raw-reply-changed');core.e.clicked(reply,s[step+'_command'],close=step=='close')
        else:
            rec=s.get(step+'_reconciliation',{});need(rec.get('ui_used') is False and rec.get('kind')=='readonly-'+step+'-effect-v3','alias-v3-unknown-effect-unverified');p=page_scope(doc(rec['page']),m,v,normal=step=='close')
            if step=='open':link(m,v,c.parse_case(v['fresh_job'],p,text_schema=v['fresh_profile'].get('text_schema')))
    parsed=c.parse_case(v['fresh_job'],drawer,text_schema=v['fresh_profile'].get('text_schema'));need(parsed==doc(s['unbound_case']),'alias-v3-parsed-case-changed');return link(m,v,parsed)

def receipt(operation_ref,*,stack=None):
    s=doc(operation_ref);proof=verify_operation(operation_ref,stack=stack);proof.update(operation=operation_ref,manifest=s['manifest']);return proof

def verify_receipt(receipt_ref):
    r=doc(receipt_ref);s=doc(r['operation']);m=doc(s['manifest']);need(receipt_ref==ref(base(m)/'alias-receipt.json') and r==receipt(r['operation']),'alias-v3-receipt-not-reproducible');return r

def result_for(m,op,receipt_ref):
    v,_,task,view,_=context(m);result=apply2.result_input(receipt_ref,op,view,task);result['matching']='known-public-case-reinspection-v3; exact original public case and source facts; original key/customer retained';return result

def verify_apply(apply_ref,*,stack=None):
    a=doc(apply_ref);m=doc(a['manifest']);canonical_manifest(m,a['manifest'],historical=True);need(apply_ref==ref(base(m)/'apply'/'operation.json') and a.get('kind')=='apply-public-case-alias-v3' and a.get('state')=='complete','alias-v3-apply-incomplete');r=doc(a['receipt']);need(r==receipt(r['operation'],stack=stack) and a['receipt']==ref(base(m)/'alias-receipt.json'),'alias-v3-apply-receipt-invalid');v,_,task,_,_=context(m,stack);op=doc(r['operation']);value=apply2.result_input(a['receipt'],op,anchor_view(m,doc(m['origin']['manifest'])),task);value['matching']='known-public-case-reinspection-v3; exact original public case and source facts; original key/customer retained';need(doc(a['result_input'])==value,'alias-v3-applied-result-changed');ledger=doc(a['recorded_state']);apply2.check_committed(Path(m['root']),ledger,m['review_key'],task,value,a['result_input']);need(a['memory_observation']==apply2.memory_observation(anchor_view(m,doc(m['origin']['manifest'])),task,a['result_input']),'alias-v3-case-memory-unverified');need(ref(a['workbook']['path'])==a['workbook'],'alias-v3-workbook-changed');return a

def progress(operation_ref,*,dispatch_id,dispatch_started_at,present):
    s=doc(operation_ref)
    if s.get('state')!='complete':return None
    if stamp(s['created_at'])<stamp(dispatch_started_at):return None
    m=doc(s['manifest'])
    if m['lease']['binding']['dispatch_id']!=dispatch_id:return None
    proof=verify_operation(operation_ref);idx=doc(ref(index_path(m)));need(idx.get('kind')=='review-case-alias-active-v3' and idx.get('review_key')==m['review_key'] and idx.get('origin')==m['origin']['manifest'],'alias-v3-progress-index-invalid')
    if idx.get('current')!=s['manifest']:return None
    after=stamp(doc(s['normal_after'])['observed_at']);need(stamp(dispatch_started_at)<=stamp(s['created_at'])<=after<=stamp(s['completed_at'])<=stamp(present),'alias-v3-progress-time-invalid')
    return {'schema':'known-case-reinspection-v3','dedup_key':datahash({'kind':'closed-known-public-case','original_review_key':m['review_key']}),'business_binding':{'original_review_key':m['review_key'],'origin_manifest':m['origin']['manifest'],'case_signature_sha256':proof['case_signature_sha256']},'created_at':s['created_at'],'completed_at':after.isoformat(),'operation':operation_ref,'active_index':ref(index_path(m)),'ui_used':False}

# Only pure replay functions are wrapped. active_guard, Transport, prepare,
# mutation, apply writes and current-lease/index/ledger reads remain outside.
def _loaded_function_chain(function):
    import types
    layers=[];seen=set();fn=function
    while isinstance(fn,types.FunctionType):
        need(id(fn) not in seen and len(layers)<8,'alias-v3-runtime-wrapper-cycle')
        seen.add(id(fn));layers.append((fn,fn.__code__,copy.deepcopy(fn.__defaults__),copy.deepcopy(fn.__kwdefaults__)))
        wrapped=getattr(fn,'__wrapped__',None)
        if wrapped is None:break
        need(isinstance(wrapped,types.FunctionType),'alias-v3-runtime-wrapper-unreviewed');fn=wrapped
    return tuple(layers)

def replay_code_token():
    # Files remain the published manifest contract. Loaded function identities and
    # bodies additionally prevent a within-process replacement from reusing memo.
    import types
    runtime=[]
    for module,names in ((sys.modules[__name__],('original','context','verify_operation','receipt','verify_receipt','result_for','verify_apply','canonical_manifest','page_scope','link','doc','ref','codes','code_guard','_completed_entry_reference','_loaded_function_chain','replay_code_token','_memo_authorize')),(release,('encoded','digest','need','strict','reference','publish','graph_id','seal','check','completed','pure_entry','history_active')),(legacy,('catalogue','code_files','completed','identity','verify')),(v2,('canonical','lease_binding','root_guard','order_document')),(c,('document','ref','parse_case')),(core,('inputs','validate_alias','verify_complete')),(apply2,('result_input','check_committed','memory_observation')),(replay,('canonical','digest','inventory','audit','transaction','memo'))):
        for name in names:
            fn=getattr(module,name)
            if isinstance(fn,types.FunctionType):runtime.append((module,name,_loaded_function_chain(fn)))
            else:runtime.append((module,name,id(fn))) # synthetic mocks still fixed per transaction
    runtime.append(('session-class',replay.Session))
    for name,fn in vars(replay.Session).items():
        if isinstance(fn,types.FunctionType):
            runtime.append((replay.Session,name,_loaded_function_chain(fn)))
    return codes(),tuple(runtime)

def _memo_authorize(name,args,kwargs):
    stack=kwargs.get('stack',args[1] if name=='context' and len(args)>1 else None) or []
    need(type(stack) is list and all(type(x) is tuple and len(x)==2 and all(type(y) is str for y in x) for x in stack) and len(stack)<128,'alias-v3-prior-cycle-or-depth')
    m=None;cacheable=True
    if name in ('context','result_for'):
        m=args[0];path=base(m)/'manifest.json'
        if m.get('kind')!=KIND or not path.is_file():cacheable=False
        else:
            mr=ref(path);need(doc(mr)==m,'alias-v3-published-input-mutated');canonical_manifest(m,mr,historical=True)
        if name=='result_for':
            op_path=base(m)/'operation.json'
            cacheable=cacheable and op_path.is_file()
            if cacheable:need(doc(ref(op_path))==args[1],'alias-v3-published-operation-mutated')
    elif name in ('verify_operation','receipt','verify_apply','verify_receipt'):
        value=doc(args[0])
        if name=='verify_receipt':value=doc(value['operation'])
        m=doc(value['manifest']);canonical_manifest(m,value['manifest'],historical=True)
    target=(str(base(m)),m['version']) if m is not None else None
    need(target not in stack,'alias-v3-prior-cycle-or-depth')
    # Complete argument values are signed; traversal stack is checked separately
    # including cached transitive lineage, so it cannot hide a newly formed loop.
    key=replay.canonical((args[0] if name=='context' else args,{k:v for k,v in kwargs.items() if k!='stack'}))
    return key,cacheable,target,tuple(tuple(x) for x in stack)

for _name in ('original','context','verify_operation','receipt','verify_receipt','result_for','verify_apply'):
    globals()[_name]=replay.memo(_name,replay_code_token,lambda args,kwargs,name=_name:_memo_authorize(name,args,kwargs))(globals()[_name])

def _completed_entry_reference(name,value_ref):
    value=doc(value_ref)
    if name=='verify_receipt':value=doc(value['operation'])
    mr=value['manifest'];m=doc(mr);operation_ref=ref(base(m)/'operation.json');operation=doc(operation_ref)
    if operation.get('state')!='complete':return None
    need(operation.get('manifest')==mr,'alias-release-manifest-operation-mismatch')
    if name in ('verify_operation','receipt'):need(value_ref==operation_ref,'alias-release-canonical-operation-required')
    return mr,operation_ref

# Only these explicit pure completed-entry APIs may use a sealed old release.
# Live CLI guard/load/prepare/record remain strict current-source checks.
for _name in ('verify_operation','receipt','verify_receipt','verify_apply'):
    globals()[_name]=release.pure_entry(_name,globals()[_name],_completed_entry_reference)
