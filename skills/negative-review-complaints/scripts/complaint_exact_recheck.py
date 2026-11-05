"""Versioned exact-name existing-case recheck. Public reads/open/close only.
Current normal+Excel exact join locates the unchanged original review. This is
not an alias; changed display names require the separate case-alias contract.
"""
import copy,fcntl,hashlib,json,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'workshop-director/scripts'))
import complaint_execution_order as o
import workflow as w
import normal_observation as n
import normal_review_body as body
import existing_result_runner as r
import result_observation as result
import case_memory as memory
need=o.need
KIND='exact-name-existing-case-recheck-v1'
FIELDS=('review_id','store','customer','customer_id','text','stars','date','time','product')
def now():return datetime.now(timezone.utc).isoformat()
def codes():return [o.ref(Path(m.__file__).resolve()) for m in (sys.modules[__name__],o,w,n,r,result,n.authority,body,n.authority.export_parse_session,memory)]+[o.ref(w.SKILL/'scripts/export-results.mjs')]
def base(root,key):return Path(root)/'existing-result-operations'/hashlib.sha256(key.encode()).hexdigest()/'exact-rechecks'
def folder(m):return base(m['root'],m['review_key'])/m['version']
def bytes_archive(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'exact-recheck-archive-changed')
    else:
        with path.open('xb') as f:f.write(raw);f.flush();__import__('os').fsync(f.fileno())
    return o.ref(path)
# One reviewed completed/applied pre-result-wait graph. Archives are data only.
HISTORICAL_CODE = [{'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/complaint_exact_recheck.py', 'sha256': '7e9bb5783bdac844802e83ef7a179f5613237e67526b9d8120d26d9b92770549'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/complaint_execution_order.py', 'sha256': 'edb7555e5010c487a12c544e6c660ba2a841831279b1fca4149b05b655cfcbd2'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/workflow.py', 'sha256': '96ddcea071901d2b7b3e9ff82fcb3bcc6aa8d49824755c3e0ded7002f96f2e75'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_observation.py', 'sha256': '0c3215ca79fe4bbd724dd7ca8620778b74b1b3698bd6a1fdd69eb7bdcde6b14d'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/existing_result_runner.py', 'sha256': 'e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/result_observation.py', 'sha256': '8db833a645c7e338086000287d3e6dd7d4360555c5c0e87a18d81c0325fd75e8'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/authoritative_join.py', 'sha256': '4b6d47f9f990cc0d23ca25099c9b188dfcab4cd0ab3abf27933d03019d37eb60'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_review_body.py', 'sha256': '2d1b9cbb1a1a8d2196d5f948db7984af7cbaf05cc206188f6fd8773fee9183b7'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/export_parse_session.py', 'sha256': '7f1fc217c29339a327dcf0a3cf8e57912431d08dc5c8915d7bfe805996f86a55'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/case_memory.py', 'sha256': 'd69a5ac3151cc35c566491ca4bb00230bc7beb156a111ab8eb967361d4d230c5'}, {'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/export-results.mjs', 'sha256': 'b402c20d52800c396364d7f325ed8bf096ea5719c19f97c5b792412e45c5e98e'}]
HISTORICAL_ARCHIVES = {'/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/complaint_exact_recheck.py': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-exact-historical-code-candidate/complaint_exact_recheck.py.before', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/existing_result_runner.py': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-exact-historical-code-candidate/existing_result_runner.py.before'}

def code_guard(m,*,historical=False):
    # Source snapshots are archival; current original task/input/result bindings
    # are checked by inputs and the completed operation, without code history.
    need(m.get('kind')==KIND,'exact-recheck-kind')


def inputs(m,*,historical=False):
    need(m.get('kind')==KIND and set(m['fresh'])=={'job','source','profile','envelope','page'},'exact-recheck-manifest-shape');order=o.validate(m['order']);validate_lease_binding(m['lease_binding'],order);need(m['dispatch_id']==order['dispatch_id'] and m['day']==order['day'],'exact-recheck-dispatch-day');code_guard(m,historical=historical);v={k:o.doc(x) for k,x in m['fresh'].items()};job=v['job'];source=v['source'];need(n.joined(job,v['envelope'],v['profile'],job['source_receipt'],job['source_receipt_sha256'])==source,'exact-recheck-current-source-not-reproducible');old=o.doc(m['original_ledger']);task=old['tasks'][m['review_key']];need(task['result']['status'] in ('pending','unknown') and task['result']['evidence']==m['previous_result'],'exact-recheck-original-pending-required');oldresult=o.doc(m['previous_result']);need({k:v for k,v in task['result'].items() if k!='evidence'}==oldresult,'exact-recheck-original-result-changed');oldsource=o.doc(task['latest_snapshot']);authority=oldsource['authority_binding'];o.raw({'path':authority['receipt_path'],'sha256':authority['receipt_sha256']});o.raw({'path':authority['source_path'],'sha256':authority['source_sha256']});need(oldsource['company']==source['company']==old['company']==job['company'] and str(oldsource['groupid'])==str(source['groupid'])==str(old['groupid'])==str(job['groupid']) and oldsource['identity']==source['identity']==old['identity']==job['identity'],'exact-recheck-identity-scope');need(m['root']==str(o.PROJECT/'runtime'/o.FLOW/old['company']),'exact-recheck-canonical-root');need(any(c['root']==m['root'] and c['groupid']==str(old['groupid']) and m['review_key'] in c['recheck_ids'] for c in order['companies']),'exact-recheck-original-key-not-dispatched')
    rows=[row for row in source['rows'] if source['groupid']+':'+row['review_id']==m['review_key']];need(len(rows)==1,'exact-recheck-key-changed-needs-alias');row=rows[0];need(all(task['review'].get(k,'')==row.get(k,'') for k in FIELDS),'exact-recheck-tuple-changed-needs-alias');need(row['action'] in ('查看投诉结果','投诉审核中'),'exact-recheck-current-action');need(oldsource['start']<=task['review']['date']<oldsource['end_exclusive'] and job['start']<=task['review']['date']<job['end_exclusive'],'exact-recheck-date-mismatch');oldrows=[x for x in oldsource['rows'] if oldsource['groupid']+':'+x['review_id']==m['review_key']];need(len(oldrows)==1 and all(task['review'].get(k,'')==oldrows[0].get(k,'') for k in FIELDS) and oldresult['snapshot_sha256']==task['latest_snapshot']['sha256'],'exact-recheck-original-source-tuple');[w.verify_evidence(task[k]) for k in ('snapshot','latest_snapshot','screenshot','wecom') if task.get(k)];need(Path(m['origin']['path'])==o.location(m['order'])/'origin.json','exact-recheck-origin-path');origin=o.doc(m['origin']);need(origin['order']==m['order'] and origin['scope_sha256']==order['scope_sha256'],'exact-recheck-origin-scope');need(datetime.fromisoformat(source['observed_at'])>=datetime.fromisoformat(origin['wall_started_at']),'exact-recheck-source-before-current-run');fresh_binding=source['authority_binding'];fresh_receipt=o.doc({'path':fresh_binding['receipt_path'],'sha256':fresh_binding['receipt_sha256']});need(datetime.fromisoformat(origin['wall_started_at'])<=datetime.fromisoformat(fresh_receipt['recorded_at'])<=datetime.fromisoformat(source['observed_at']),'exact-recheck-current-acquisition-required');case=oldresult.get('original_complaint',{});need(set(case)=={'投诉类型','投诉时间','投诉理由'} and all(isinstance(x,str) and x for x in case.values()),'exact-recheck-original-case-fields');n.context(v['page'],job['groupid']);return order,v,old,task,row,case

def canonical_manifest(m,mr,*,historical=False):
    inputs(m,historical=historical);need(Path(mr['path'])==folder(m)/'manifest.json' and o.ref(mr['path'])==mr,'exact-recheck-canonical-manifest');return m

def prepare(order_ref,root,key,fresh):
    root=o.canonical(Path(root));order=o.validate(order_ref);need(set(fresh)=={'job','source','profile','envelope','page'},'exact-recheck-five-inputs');[o.doc(x) for x in fresh.values()]
    with r.operation_lock(root,key):
        raw=(root/'state.json').read_bytes();state=json.loads(raw);task=state['tasks'][key];version=o.digest({'dispatch_id':order['dispatch_id'],'day':order['day'],'key':key,'previous_result':task['result']['evidence']});directory=base(root,key)/version;index=base(root,key)/'active.json'
        if index.exists():
            idx=o.doc(o.ref(index));need(idx['review_key']==key,'exact-recheck-active-owner');oldm=o.doc(idx['manifest'])
            if oldm['version']==version:canonical_manifest(oldm,idx['manifest']);need(oldm['fresh']==fresh and oldm['order']==order_ref,'exact-recheck-original-parameters');return idx['manifest']
            verify_apply(o.ref(folder(oldm)/'apply/operation.json'));need(oldm['day']<order['day'],'exact-recheck-no-repeat-same-business-day')
        # The legacy reader's active operation must be complete before creating
        # a new version; a fresh dispatch cannot wash its unknown intent.
        legacy=base(root,key).parent/'active.json'
        if legacy.exists():
            op=o.doc(o.doc(o.ref(legacy))['operation']);vv,ro,row=r.manifest_inputs(op['manifest'],historical_complete=True);r.verify_complete(op,op['manifest'],vv,ro,row)
        snapshot=bytes_archive(directory/('ledger-'+hashlib.sha256(raw).hexdigest()+'.json'),raw)
        m={'kind':KIND,'version':version,'root':str(root),'review_key':key,'dispatch_id':order['dispatch_id'],'day':order['day'],'order':order_ref,'origin':o.ref(o.location(order_ref)/'origin.json'),'lease_binding':lease_binding(order_ref),'fresh':fresh,'original_ledger':snapshot,'previous_result':task['result']['evidence'],'created_at':now(),'code':codes()};inputs(m);lease_guard(m);need((root/'state.json').read_bytes()==raw,'exact-recheck-prepare-concurrent-change');mr=o.immutable(directory/'manifest.json',m);engine_save(index,{'kind':'exact-recheck-active-v1','review_key':key,'manifest':mr});return mr

def engine_save(path,value):w.atomic(path,value)
LEASE_FIELDS=('version','index','tool_receipt','phase','dispatch_id','day','test_target','production_enabled','complaint_submission_enabled','dispatch_intent_at','dispatched_at')
def validate_lease_binding(lease,order):
    need(set(lease)==set(LEASE_FIELDS) and lease.get('version')==2 and lease.get('index')==1 and bool(lease.get('tool_receipt')) and lease['phase']=='running' and lease['dispatch_id']==order['dispatch_id'] and lease['day']==order['day'] and lease.get('test_target')=='测试群请忽略' and lease.get('production_enabled') is False and lease.get('complaint_submission_enabled') is False,'exact-recheck-live-lease')
    started=datetime.fromisoformat(lease['dispatch_intent_at']);acked=datetime.fromisoformat(lease['dispatched_at']);need(started.utcoffset() is not None and acked.utcoffset() is not None and started<=acked,'exact-recheck-lease-time')
def lease_binding(order_ref):
    lease=o.doc(o.ref(Path(order_ref['path']).parent.parent/'state.json'));binding={k:lease.get(k) for k in LEASE_FIELDS};validate_lease_binding(binding,o.validate(order_ref));return binding
def lease_guard(m):
    need(lease_binding(m['order'])==m['lease_binding'],'exact-recheck-live-lease-changed')

def guard(m,mr):
    canonical_manifest(m,mr);index=o.doc(o.ref(base(m['root'],m['review_key'])/'active.json'));need(index=={'kind':'exact-recheck-active-v1','review_key':m['review_key'],'manifest':mr},'exact-recheck-active-owner-changed');lease_guard(m);need((Path(m['root'])/'state.json').read_bytes()==o.raw(m['original_ledger']),'exact-recheck-live-ledger-changed')
def verify_page_transport(page,m):
    refs=page.get('rpc_evidence');need(type(refs) is list and len(refs)==4,'exact-recheck-raw-rpc-evidence-required');raw=[o.doc(ref) for ref in refs];tab=page['tab'];commands=[{'op':'tabs'},{'op':'ping','tabId':tab['tabId']},{'op':'tree','tabId':tab['tabId']},{'op':'tabs'}];need([x['command'] for x in raw]==commands and all(x['reply'].get('ok') is True for x in raw),'exact-recheck-rpc-command-reply');before=raw[0]['reply']['result'];after=raw[3]['reply']['result'];need(before==after and raw[2]['reply']['result']==page['tree'],'exact-recheck-rpc-observation-changed');tabs=[t for w in after for t in w.get('tabs',[]) if t.get('tabId')==tab['tabId']];need(tabs==[tab],'exact-recheck-rpc-tab-changed');ping=raw[1]['reply']['result'];need(ping.get('version')==__import__('dom_evidence').VERSION and ping.get('safety')=='DOM-only','exact-recheck-rpc-version')
def normal_page(page,v,row):
    need(all(page['tab'].get(k)==v['page']['tab'].get(k) for k in ('tabId','windowId','url')),'exact-recheck-tab-window-changed');order={'card_selector':row['dom_selector'],'original_action':row['action']};return r.normal_page(page,v,order,row,identity=True)
def parsed(m,v,row,page):
    need(all(page['tab'].get(k)==v['page']['tab'].get(k) for k in ('tabId','windowId','url')),'exact-recheck-drawer-tab-window');out=result.parse(v['job'],page,row,text_schema=v['profile'].get('text_schema'));old=o.doc(m['previous_result']);need(out['original_complaint']==old['original_complaint'],'exact-recheck-case-changed');need(out['review_key']==m['review_key'],'exact-recheck-result-key');out.update(snapshot_sha256=o.doc(m['original_ledger'])['tasks'][m['review_key']]['latest_snapshot']['sha256'],matching='versioned exact review/current-export and original public case; original source retained',fresh_source=m['fresh']['source'],previous_result_ref=m['previous_result']);return out

def read(m,mr,request,label):
    order,v,old,task,row,case=inputs(m);tab=v['page']['tab'];records=[]
    def call(command):
        guard(m,mr);reply=request(command);ref=o.immutable(folder(m)/('rpc-'+uuid.uuid4().hex+'.json'),{'command':command,'reply':reply});records.append(ref);need(reply.get('ok') is True,'exact-recheck-read-failed');return reply['result']
    before=call({'op':'tabs'});tabs=[t for w in before for t in w.get('tabs',[]) if t.get('tabId')==tab['tabId']];need(len(tabs)==1 and all(tabs[0].get(k)==tab.get(k) for k in ('tabId','windowId','url','allowed')),'exact-recheck-read-tab');ping=call({'op':'ping','tabId':tab['tabId']});need(ping.get('version')==__import__('dom_evidence').VERSION and ping.get('safety')=='DOM-only','exact-recheck-read-version');tree=call({'op':'tree','tabId':tab['tabId']});after=call({'op':'tabs'});need(before==after,'exact-recheck-read-context-race');page={'tab':tabs[0],'tree':tree,'observed_at':now(),'rpc_evidence':records};n.context(page,v['job']['groupid']);return page,o.immutable(folder(m)/(label+'-'+uuid.uuid4().hex+'.json'),page)

def tick(mr,request=None):
    m=o.doc(mr);canonical_manifest(m,mr);request=request or r.bridge.request;path=folder(m)/'operation.json'
    with r.operation_lock(m['root'],m['review_key']):
        s=o.doc(o.ref(path)) if path.exists() else {'kind':'exact-existing-case-operation-v1','manifest':mr,'state':'preflight','created_at':now(),'ui_used':False,'submission_enabled':False};need(s['manifest']==mr,'exact-recheck-original-operation')
        if s['state']=='complete':verify_complete(o.ref(path));return {'state':'complete','operation':o.ref(path)}
        need(s['state'] not in ('unknown-open','unknown-close'),'exact-recheck-unknown-no-replay');guard(m,mr);_,v,_,_,row,_=inputs(m)
        def save():engine_save(path,s)
        if s['state'] in ('preflight','open-ready'):
            page,ref=read(m,mr,request,'normal-before');target=normal_page(page,v,row);command=r.click(page['tab']['tabId'],target['selector']);s.update(normal_before=ref,open_command=command,state='unknown-open');save();guard(m,mr);reply=request(command);s['open_reply_raw']=o.immutable(folder(m)/('open-reply-'+uuid.uuid4().hex+'.json'),reply);save();need(reply.get('ok') is True,'exact-recheck-open-failed');r.clicked(reply['result'],command);s.update(open_reply=reply['result'],state='opened',ui_used=True);save()
        elif s['state']=='opened':
            page,ref=read(m,mr,request,'drawer');page,ref=r.settle_empty_drawer((page,ref),lambda:read(m,mr,request,'drawer-loading'),{'job':v['job'],'page':v['page']},s,save);value=parsed(m,v,row,page);s.update(drawer=ref,result_input=o.immutable(folder(m)/'observed-result.json',value),state='close-ready');save()
        elif s['state']=='close-ready':
            page,ref=read(m,mr,request,'drawer-before-close');value=parsed(m,v,row,page);old=o.doc(s['result_input']);need(all(value[k]==old[k] for k in ('status','visible_text','original_complaint','review_key')),'exact-recheck-result-changed-before-close');command=r.close_command(page);s.update(drawer_before_close=ref,close_command=command,state='unknown-close');save();guard(m,mr);reply=request(command);s['close_reply_raw']=o.immutable(folder(m)/('close-reply-'+uuid.uuid4().hex+'.json'),reply);save();need(reply.get('ok') is True,'exact-recheck-close-failed');r.clicked(reply['result'],command,close=True);s.update(close_reply=reply['result'],state='verify-closed');save()
        elif s['state']=='verify-closed':
            page,ref=read(m,mr,request,'normal-after');normal_page(page,v,row);s.update(normal_after=ref,state='complete',completed_at=now());save();verify_complete(o.ref(path))
        else:raise ValueError('exact-recheck-phase-invalid')
        return {'state':s['state'],'operation':o.ref(path)}

def verify_complete(operation_ref):
    s=o.doc(operation_ref);m=o.doc(s['manifest']);need(s.get('state')=='complete','exact-recheck-not-complete');canonical_manifest(m,s['manifest'],historical=True);need(Path(operation_ref['path'])==folder(m)/'operation.json' and s['state']=='complete' and s['submission_enabled'] is False,'exact-recheck-not-complete');_,v,_,_,row,_=inputs(m,historical=True);before=o.doc(s['normal_before']);verify_page_transport(before,m);target=normal_page(before,v,row);need(s['open_command']==r.click(before['tab']['tabId'],target['selector']),'exact-recheck-open-command');drawer=o.doc(s['drawer']);verify_page_transport(drawer,m);expected=parsed(m,v,row,drawer);need(o.doc(s['result_input'])==expected,'exact-recheck-result-not-reproducible');closepage=o.doc(s['drawer_before_close']) if s.get('drawer_before_close') else drawer;verify_page_transport(closepage,m);later=parsed(m,v,row,closepage);need(all(later[k]==expected[k] for k in ('status','visible_text','original_complaint','review_key')),'exact-recheck-close-result-changed');need(s['close_command']==r.close_command(closepage),'exact-recheck-close-command');after=o.doc(s['normal_after']);verify_page_transport(after,m);normal_page(after,v,row)
    if s.get('open_reply'):
        raw=o.doc(s['open_reply_raw']);need(raw.get('ok') is True and raw['result']==s['open_reply'],'exact-recheck-open-reply-raw');r.clicked(s['open_reply'],s['open_command'])
    else:need(s.get('open_reconciliation')==s['drawer'],'exact-recheck-open-effect-missing')
    if s.get('close_reply'):
        raw=o.doc(s['close_reply_raw']);need(raw.get('ok') is True and raw['result']==s['close_reply'],'exact-recheck-close-reply-raw');r.clicked(s['close_reply'],s['close_command'],close=True)
    else:need(s.get('close_reconciliation')==s['normal_after'],'exact-recheck-close-effect-missing')
    times=[datetime.fromisoformat(x) for x in (m['created_at'],s['created_at'],before['observed_at'],drawer['observed_at'],o.doc(s['normal_after'])['observed_at'],s['completed_at'])];need(all(t.utcoffset() is not None for t in times) and times==sorted(times),'exact-recheck-time-order');return {'kind':KIND,'manifest':s['manifest'],'operation':operation_ref,'result':s['result_input'],'normal_after':s['normal_after'],'original_review_key':m['review_key'],'person_identity_verified':False}

def receipt(mr):
    m=o.doc(mr);proof=verify_complete(o.ref(folder(m)/'operation.json'));return o.immutable(folder(m)/'receipt.json',proof)
def verify_receipt(ref):
    value=o.doc(ref);m=o.doc(value['manifest']);need(Path(ref['path'])==folder(m)/'receipt.json' and value==verify_complete(value['operation']),'exact-recheck-receipt-changed');return value

def apply(receipt_ref):
    value=verify_receipt(receipt_ref);m=o.doc(value['manifest']);root=Path(m['root']);key=m['review_key'];directory=folder(m)/'apply';path=directory/'operation.json';original=o.doc(m['original_ledger']);task=original['tasks'][key];data={**o.doc(value['result']),'exact_recheck_ref':receipt_ref};result_ref=o.immutable(directory/'result.json',data)
    with r.operation_lock(root,key),w.locked(root):
        if path.exists():
            audit=o.doc(o.ref(path));need(audit['receipt']==receipt_ref and audit['result']==result_ref,'exact-recheck-original-apply');
            if audit['state']=='complete':verify_apply(o.ref(path));return {'state':'complete','operation':o.ref(path),'already_applied':True}
        else:
            guard(m,value['manifest']);audit={'kind':'apply-exact-existing-case-v1','receipt':receipt_ref,'manifest':value['manifest'],'result':result_ref,'state':'record-intent','original_ledger':m['original_ledger']};engine_save(path,audit)
        current=w.load(root)
        if current['tasks'][key].get('result',{}).get('exact_recheck_ref')!=receipt_ref:
            need((root/'state.json').read_bytes()==o.raw(m['original_ledger']),'exact-recheck-apply-ledger-changed');current['tasks'][key].setdefault('result_history',[]).append(copy.deepcopy(task['result']));w.record_result(root,current,key,result_ref['path'])
        current=w.load(root);verify_delta(original,current,key,data);audit['memory_observation']=memory_observation(m,result_ref);audit['recorded_state']=bytes_archive(directory/'recorded-state.json',(root/'state.json').read_bytes());audit['state']='recorded';engine_save(path,audit)
        import current_complaint_workbook as current_book
        inputs_job=o.doc(m['fresh']['job'])
        book_ref,_=current_book.write({'company':current['company'],'start':inputs_job['start'],'end_exclusive':inputs_job['end_exclusive']},{'artifacts':{'completed_units':[{'keys':[key]}]}},current,directory/'current-result')
        book=Path(book_ref['path']);audit['workbook']=bytes_archive(directory/'workbook.xlsx',book.read_bytes());audit.update(state='complete',completed_at=now());engine_save(path,audit);verify_apply(o.ref(path));return {'state':'complete','operation':o.ref(path),'already_applied':False}
def verify_delta(original,current,key,data):
    old=original['tasks'][key];new=current['tasks'][key];need(set(current)==set(original),'exact-recheck-ledger-fields-changed');
    for field in original:
        if field not in ('tasks','events','updated_at','xlsx_dirty'):need(current[field]==original[field],'exact-recheck-ledger-metadata-changed:'+field)
    events=current['events'];need(len(events)==len(original['events'])+1 and events[:-1]==original['events'] and events[-1].get('type')=='platform-result-read' and events[-1].get('id')==key,'exact-recheck-event-delta');need(set(current['tasks'])==set(original['tasks']),'exact-recheck-task-set-changed')
    for other in original['tasks']:
        if other!=key:need(current['tasks'][other]==original['tasks'][other],'exact-recheck-other-task-changed')
    for field in ('review','snapshot','latest_snapshot','screenshot','wecom','send_attempt','action'):
        need(new.get(field)==old.get(field),'exact-recheck-original-task-field-changed:'+field)
    need(new['status']==('resolved' if data['status'] in ('accepted','rejected') else 'existing_pending'),'exact-recheck-result-status');need(new['result_history']==old.get('result_history',[])+[old['result']] and {k:v for k,v in new['result'].items() if k!='evidence'}==data,'exact-recheck-result-delta');need(current['batches']==original['batches'] and current['next_start']==original['next_start'],'exact-recheck-business-range-changed')
def memory_observation(m,result_ref):
    # The current observed platform result is sufficient; case-memory history
    # must not gate recording a completed read of this exact pending task.
    return {'original_review_key':m['review_key'],'result_sha256':result_ref['sha256'],'current_result':result_ref}

def verify_apply(ref):
    audit=o.doc(ref);m=o.doc(audit['manifest']);need(Path(ref['path'])==folder(m)/'apply/operation.json' and audit['kind']=='apply-exact-existing-case-v1' and audit['state']=='complete','exact-recheck-apply-incomplete');value=verify_receipt(audit['receipt']);data={**o.doc(value['result']),'exact_recheck_ref':audit['receipt']};need(o.doc(audit['result'])==data,'exact-recheck-applied-result-changed');verify_delta(o.doc(m['original_ledger']),o.doc(audit['recorded_state']),m['review_key'],data);o.raw(audit['workbook']);need(audit['memory_observation']==memory_observation(m,audit['result']),'exact-recheck-memory-observation-changed');return audit

def reconcile(mr,original_state_sha256,request=None):
    m=o.doc(mr);path=folder(m)/'operation.json';request=request or r.bridge.request
    with r.operation_lock(m['root'],m['review_key']):
        need(o.ref(path)['sha256']==original_state_sha256,'exact-recheck-original-state-sha');s=o.doc(o.ref(path));need(s['manifest']==mr and s['state'] in ('unknown-open','unknown-close'),'exact-recheck-unknown-only');guard(m,mr);_,v,_,_,row,_=inputs(m);page,ref=read(m,mr,request,'readonly-reconciliation')
        if s['state']=='unknown-open':
            value=parsed(m,v,row,page);s.update(state='close-ready',drawer=ref,open_reconciliation=ref,result_input=o.immutable(folder(m)/'observed-result.json',value))
        else:normal_page(page,v,row);s.update(state='complete',normal_after=ref,close_reconciliation=ref,completed_at=now())
        engine_save(path,s);return {'state':s['state'],'operation':o.ref(path),'ui_used':False}

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='verb',required=True)
    a=sub.add_parser('prepare')
    for name in ('order','order-sha256','root','review-key','fresh','fresh-sha256'):a.add_argument('--'+name,required=True)
    for verb in ('run','reconcile','verify','record-reconciled','apply'):
        a=sub.add_parser(verb)
        for name in (('receipt','receipt-sha256') if verb=='apply' else ('manifest','manifest-sha256')):a.add_argument('--'+name,required=True)
        if verb=='reconcile':a.add_argument('--original-state-sha256',required=True)
        if verb=='run':a.add_argument('--steps',type=int,choices=range(1,11),default=1)
    a=p.parse_args();ref=lambda name:{'path':getattr(a,name),'sha256':getattr(a,name+'_sha256')}
    if a.verb=='prepare':out={'manifest':prepare(ref('order'),a.root,a.review_key,o.doc(ref('fresh'))),'ui_used':False}
    elif a.verb=='apply':out=apply(ref('receipt'))
    elif a.verb=='verify':
        m=o.doc(ref('manifest'));canonical_manifest(m,ref('manifest'),historical=True);out=verify_complete(o.ref(folder(m)/'operation.json'))
    elif a.verb=='record-reconciled':out={'receipt':receipt(ref('manifest')),'ui_used':False}
    elif a.verb=='reconcile':out=reconcile(ref('manifest'),a.original_state_sha256)
    else:
        for _ in range(a.steps):
            out=tick(ref('manifest'))
            if out['state']=='complete':break
    print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=False));raise SystemExit(2)
