"""Pure fresh closure verification. Does not update the director progress registry."""
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
import hashlib,importlib,importlib.util,json,re,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
class EvidenceError(ValueError):pass
def need(value,code):
    if not value:raise EvidenceError(code)
def timestamp(value):
    try:out=value if isinstance(value,datetime) else datetime.fromisoformat(value)
    except (TypeError,ValueError):raise EvidenceError('fresh-aware-time-required')
    need(out.utcoffset() is not None,'fresh-aware-time-required');return out

def canonical(path):
    path=Path(path);need(path.is_absolute() and path==path.resolve() and not path.is_symlink() and not any(p.is_symlink() for p in path.parents),'fresh-canonical-path-required');return path

def reference(path):
    path=canonical(path);return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def read(ref):
    path=canonical(ref['path']);raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'fresh-artifact-changed');return json.loads(raw)
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
@contextmanager
def modules(skill,names):
    directory=PROJECT/'skills'/skill/'scripts';previous=list(sys.path)
    try:
        sys.path.insert(0,str(directory));loaded=[importlib.import_module(n) for n in names]
        for name,module in zip(names,loaded):need(Path(module.__file__).resolve()==directory/(name+'.py'),'fresh-module-origin-conflict:'+name)
        yield loaded
    finally:sys.path[:]=previous

def inspection(s,path,started,completed,now):
    m=s.get('manifest',{});kind=m.get('kind');need(kind in ('existing-result-inspection-manifest-v1','complaint-draft-inspection-manifest-v1'),'fresh-inspection-kind-invalid')
    need(s.get('submission_enabled') is False and s.get('send_enabled',False) is False and not any(s.get(k) for k in ('submitted','radio_clicked','reason_filled')),'fresh-inspection-not-readonly')
    key=m['review_key'];source=m['inputs']['source'];root=canonical(m['root']);folder='existing-result-operations' if kind=='existing-result-inspection-manifest-v1' else 'draft-inspection'
    need(path==root/folder/hashlib.sha256(key.encode()).hexdigest()/source['sha256']/'operation.json','fresh-inspection-canonical-operation-required')
    with modules('negative-review-complaints',['existing_result_runner','draft_inspection']) as (runner,draft):
        need(Path(runner.workflow.__file__).resolve()==PROJECT/'skills/negative-review-complaints/scripts/workflow.py','fresh-workflow-origin-conflict')
        if kind=='existing-result-inspection-manifest-v1':
            v,order,row=runner.manifest_inputs(m,historical_complete=True);runner.verify_complete(s,m,v,order,row)
        else:
            draft.validate(path,root=root,key=key,snapshot=source['sha256']);v,order,row=draft.inputs(m,historical=True)
    refs=[]
    def add(r):
        if r not in refs:read(r);refs.append(r)
    for r in m['inputs'].values():add(r)
    pagekeys=['normal_before','drawer','normal_after'] if kind=='existing-result-inspection-manifest-v1' else ['normal_before','form','normal_after']
    observed=[]
    for name in pagekeys:
        r=s[name];add(r);observed.append(timestamp(read(r)['observed_at']))
    created=timestamp(s['created_at']);need(created<=observed[0]<=observed[1]<=observed[2]<=now and started<=observed[0],'fresh-inspection-page-time-invalid')
    # completed_at is serialized to seconds after parsing the normal page.
    # Raw microseconds may fall within that serialized second. Progress uses
    # the earlier raw closure observation, never a later edited state time.
    need(observed[-1]<completed+timedelta(seconds=1),'fresh-inspection-completion-time-mismatch')
    for name in ('result_input','drawer_before_close'):
        if s.get(name):add(s[name])
    job=v['job'];receipt=job.get('source_receipt');receipt_sha=job.get('source_receipt_sha256')
    if receipt and receipt_sha:add({'path':str(canonical(receipt)),'sha256':receipt_sha})
    add(reference(root/'state.json'))
    return {'kind':'closed-complaint-inspection','review_key':key}, {'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'source_sha256':source['sha256'],'range':{k:job[k] for k in ('start','end_exclusive')},'inspection_kind':kind},refs,min(completed,observed[-1])

def sender(s,path,started,completed,now,role):
    job=s.get('job',{});key=job.get('key');need(type(key) is str and key,'fresh-sender-key-required')
    with modules('workshop-director',['execution_timing','semantic_progress']) as (timing,progress):
        need(path==timing.sender_path(key),'fresh-sender-canonical-path-required')
        # Reuse the formal end-to-end canonical client-receipt replay; this
        # performs no Native construction, UI input or send.
        state={'run_id':'fresh-closure-replay','work_order':{},'scope_sha256':'fresh-closure-replay','scope':{'expected_send_keys':[key]},'origin':'fresh','wall_started_at':started.isoformat()}
        receipt={'kind':'workflow-client-confirmation-v1','run_id':state['run_id'],'work_order':{},'scope_sha256':state['scope_sha256'],'client_jobs':[reference(path)]}
        class Clock:
            def wall(self):return now
        timing.clients(receipt,state,Clock());need(progress.extract(s,role,journal_path=path)['schema']=='wecom-v1','fresh-client-semantic-schema-invalid')
    need(s.get('phase')=='done' and not s.get('last_error'),'fresh-client-not-complete')
    expected=hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest();need(expected==s.get('fingerprint'),'fresh-client-fingerprint-mismatch')
    refs=[]
    if job.get('type')=='file':
        r={'path':str(canonical(job['file'])),'sha256':job['file_sha256']};need(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'],'fresh-client-file-changed');refs.append(r)
    else:need(job.get('type')=='text','fresh-client-type-invalid')
    events=s.get('events',[]);need(events and all(timestamp(s['created_at'])<=timestamp(e.get('at'))<=completed for e in events),'fresh-client-event-time-invalid')
    confirmations=[e for e in events if e.get('stage')=='ui-confirmed'];need(len(confirmations)==1 and timestamp(confirmations[0]['at'])==completed and confirmations[0].get('recipient')==job['target'] and confirmations[0].get('recipient_kind')==job['kind'],'fresh-client-confirmation-event-invalid')
    intents=[e for e in events if e.get('stage')=='send-intent'];need(len(intents)==1,'fresh-client-original-send-intent-required')
    if job['type']=='file':need(intents[0].get('sha256')==job['file_sha256'] and intents[0].get('file')==job['file_name'],'fresh-client-original-file-intent-mismatch')
    return {'kind':'client-confirmed-sender','key':key}, {'fingerprint':expected,'kind':job['kind'],'scope':job['scope'],'target':job['target']},refs,completed

def alias_verified(path,s):
    """Pure canonical unbound-case closure replay; never runs its connector."""
    path=canonical(path);m=s.get('manifest',{})
    need(s.get('kind')=='unbound-case-operation-v1' and m.get('kind')=='unbound-case-inspection-manifest-v1','fresh-alias-kind-invalid')
    root=canonical(m['root']);key=m['review_key']
    need(path==root/'existing-result-operations'/hashlib.sha256(key.encode()).hexdigest()/'unbound-case'/'operation.json','fresh-alias-canonical-operation-required')
    need(s.get('submission_enabled') is False and s.get('send_enabled') is False,'fresh-alias-policy-invalid')
    with modules('negative-review-complaints',['case_alias_cli','unbound_case_runner']) as (cli,runner):
        manifest_ref=reference(path.with_name('manifest.json'));cli.identity(m,manifest_ref)
        proof=runner.verify_complete(s)
    need(proof.get('original_review_key')==key and proof.get('person_identity_verified') is False and proof.get('screenshot_authorized') is False and proof.get('authoritative_source_modified') is False,'fresh-alias-proof-invalid')
    refs=[reference(path),manifest_ref]
    for r in list(m['inputs'].values())+[m['old_result'],m['old_drawer'],m['order'],m['lease']['snapshot']]+list(m['pending_drawers'].values()):
        if r not in refs:read(r);refs.append(r)
    for name in ('normal_before','drawer','normal_after','unbound_case','open_reply_raw','close_reply_raw'):
        if s.get(name):read(s[name]);refs.append(s[name])
    for name in ('open_reconciliation','close_reconciliation'):
        if s.get(name):read(s[name]['page']);refs.append(s[name]['page'])
    binding={'company':read(m['inputs']['old_job'])['company'],'review_key':key,'old_source_sha256':m['inputs']['old_source']['sha256'],'old_result_sha256':m['old_result']['sha256'],'case_signature_sha256':proof['case_signature_sha256']}
    return proof,binding,refs


def case_alias_v3_monitor():
    directory=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('workshop_case_alias_v3_monitor',directory/'case_alias_v3_monitor.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(Path(module.__file__).resolve()==directory/'case_alias_v3_monitor.py','semantic-v3-monitor-origin-conflict')
    return module

def fresh_completed_evidence(journal_path,schema,*,role,dispatch_started_at,now):
    if schema=='exact-existing-case-recheck-v1':return exact_recheck_monitor().fresh(journal_path,role=role,dispatch_started_at=dispatch_started_at,now=now)
    if schema=='known-case-reinspection-v3':return case_alias_v3_monitor().fresh(journal_path,role=role,dispatch_started_at=dispatch_started_at,now=now)
    if schema not in ('complaint-inspection-v1','wecom-v1','complaint-case-alias-inspection-v1'):return None
    path=canonical(journal_path);journal=reference(path);s=read(journal)
    if (s.get('state') if schema in ('complaint-inspection-v1','complaint-case-alias-inspection-v1') else s.get('status'))!='complete':return None
    need(not s.get('error') and not s.get('last_error') and not any(c.get('state')=='unknown' for c in s.get('calls',[])),'fresh-complete-has-error-or-unknown')
    if not s.get('created_at') or not s.get('completed_at'):return None
    started=timestamp(dispatch_started_at);present=timestamp(now);created=timestamp(s.get('created_at'));completed=timestamp(s.get('completed_at'))
    need(started<=present and created<=completed<=present,'fresh-closure-time-invalid')
    if created<started:return None
    if schema=='complaint-case-alias-inspection-v1':
        need(role=='complaint_operator','fresh-role-schema-conflict');proof,binding,refs=alias_verified(path,s)
        before=timestamp(read(s['normal_before'])['observed_at']);body=timestamp(read(s['drawer'])['observed_at']);after=timestamp(read(s['normal_after'])['observed_at'])
        need(started<=created<=before<=body<=after<=completed<=present,'fresh-alias-page-time-invalid')
        identity={'kind':'closed-public-case-alias','review_key':proof['original_review_key']};progress_completed=after
    elif schema=='complaint-inspection-v1':
        need(role=='complaint_operator','fresh-role-schema-conflict');identity,binding,refs,progress_completed=inspection(s,path,started,completed,present)
    else:
        need(role in ('daily_stats_operator','complaint_operator','violation_operator'),'fresh-role-schema-conflict');identity,binding,refs,progress_completed=sender(s,path,started,completed,present,role)
    refs=[journal]+refs
    for r in refs:
        need(hashlib.sha256(canonical(r['path']).read_bytes()).hexdigest()==r['sha256'],'fresh-artifact-changed-at-end')
    return {'kind':'verified-fresh-completed-evidence-v1','schema':schema,'dedup_key':digest(identity),'business_identity':identity,'business_binding':binding,'created_at':created.isoformat(),'completed_at':progress_completed.isoformat(),'artifact_refs':refs}

def exact_recheck_monitor():
    file=Path(__file__).with_name('complaint_exact_recheck_monitor.py')
    spec=importlib.util.spec_from_file_location('workshop_complaint_exact_recheck_monitor',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
