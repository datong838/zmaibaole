"""Read-only, schema-bound progress extraction. Never runs a business workflow.
Liveness timestamps, UI phases, observation counters and intent counts are NOT progress.
"""
import hashlib,importlib.util,json,re,sys
from pathlib import Path

_records_directory=(Path(__file__).resolve().parents[2]/'violation-notifier/scripts').resolve()
_spec=importlib.util.spec_from_file_location('workshop_public_records_parser',_records_directory/'governance_dom.py')
records=importlib.util.module_from_spec(_spec)
# The public parser has sibling pure-verification helpers. Keep its import
# context explicit even when the director is launched from another directory.
_previous_import_path=list(sys.path)
try:
    sys.path.insert(0,str(_records_directory));_spec.loader.exec_module(records)
    if Path(records.verification.__file__).resolve()!=_records_directory/'verification_session.py':raise ImportError('workshop-verification-module-origin-conflict')
finally:sys.path[:]=_previous_import_path

class ProgressError(ValueError):pass

def need(ok,reason):
    if not ok:raise ProgressError(reason)
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def checksum(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def reference(r):
    need(isinstance(r,dict) and isinstance(r.get('path'),str) and Path(r['path']).is_absolute() and re.fullmatch('[0-9a-f]{64}',str(r.get('sha256',''))),'semantic-evidence-ref-required')
    p=Path(r['path']);need(p.is_file() and not p.is_symlink(),'semantic-evidence-changed');raw=p.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==r['sha256'] and p.read_bytes()==raw,'semantic-evidence-changed')
    return json.loads(raw) if p.suffix=='.json' else None

_automatic_module=None

class ScopedAutomaticVerifier:
    """Keep public parser dependencies available for the entire pure replay.

    Some existing verifiers lazily import each other. Canonical module names
    prevent a second production module, while the path never escapes this call.
    """
    def invoke(self,name,*args):
        directory=Path(__file__).resolve().parents[2]/'violation-notifier/scripts'
        previous=list(sys.path)
        try:
            sys.path.insert(0,str(directory))
            module=importlib.import_module('governance_stop_loss_production')
            need(Path(module.__file__).resolve()==directory/'governance_stop_loss_production.py','semantic-automatic-module-origin-conflict')
            return getattr(module,name)(*args)
        finally:sys.path[:]=previous
    def verify_owned_progress(self,path):return self.invoke('verify_owned_progress',path)
    def verify_completed_progress(self,path,notice):return self.invoke('verify_completed_progress',path,notice)

def automatic_verifier():
    global _automatic_module
    if _automatic_module is None:_automatic_module=ScopedAutomaticVerifier()
    return _automatic_module

def automatic_tokens(s,role,journal_path):
    active='automatic_stop_loss_owner' in s
    paths=[]
    if journal_path:
        paths=[(item.get('notice_id'),Path(journal_path).resolve().parent/'automatic-stop-loss'/hashlib.sha256(str(item.get('notice_id')).encode()).hexdigest()/'state.json') for item in s.get('details',[])]
    completed=[notice for notice,path in paths if path.is_file()]
    if not active and not completed:return {}
    need(role=='violation_operator' and journal_path and isinstance(s.get('manifest'),dict) and s['manifest'].get('kind')=='governance-detail-inspection-manifest-v1','semantic-automatic-parent-required')
    path=Path(journal_path).resolve()
    need(json.loads(path.read_bytes())==s,'semantic-automatic-journal-changed')
    verifier=automatic_verifier();tokens={}
    def accept(proof,notice,retired):
        need(proof.get('schema')=='verified-automatic-stop-loss-progress-v1' and proof.get('ui_used') is False and proof.get('notice_id')==notice and re.fullmatch('[0-9a-f]{64}',str(proof.get('binding_sha256',''))),'semantic-automatic-proof-invalid')
        need(proof.get('retired_after_verified_detail_completion') is True if retired else proof.get('owner_verified') is True,'semantic-automatic-owner-unverified')
        steps=proof.get('completed_steps');values=proof.get('progress_tokens')
        need(isinstance(steps,list) and isinstance(values,list) and len(steps)==len(values) and len(steps)==len(set(steps)),'semantic-automatic-step-proof-invalid')
        for step,value in zip(steps,values):
            need(isinstance(step,str) and re.fullmatch('[0-9a-f]{64}',str(value)),'semantic-automatic-step-proof-invalid')
            tokens['automatic:'+notice+':'+step]=value
    for notice in completed:accept(verifier.verify_completed_progress(path,notice),notice,True)
    if active:
        notice=(s.get('current') or {}).get('notice_id');need(isinstance(notice,str) and notice,'semantic-automatic-current-required')
        accept(verifier.verify_owned_progress(path),notice,False)
    need(json.loads(path.read_bytes())==s,'semantic-automatic-journal-changed')
    return tokens

def operator_tail_pending(s):
    """In-flight intent is liveness, never completed progress or replay authority."""
    calls=s.get('calls',[]);unknown=[i for i,c in enumerate(calls) if c.get('state')=='unknown']
    if not unknown:return None
    need(not isinstance(s.get('job'),dict) and not isinstance(s.get('manifest'),dict) and s.get('version')==1 and s.get('backend')=='local-dom-bridge' and s.get('work_order_id') and s.get('fingerprint') and isinstance(s.get('checkpoints'),list) and s.get('state')=='running','semantic-unknown-intent')
    need(len(unknown)==1 and unknown[0]==len(calls)-1 and all(c.get('state')=='confirmed' for c in calls[:-1]),'semantic-unknown-intent')
    need(not any(s.get(k) for k in ('error','last_error','hold','settling_exhausted','waiting_for')),'semantic-unknown-intent')
    call=calls[-1];phase=s.get('phase');need(isinstance(phase,str) and phase not in ('done','failed','error') and call.get('phase')==phase and type(s.get('revision')) is int and call.get('key')==str(s['revision'])+':'+phase,'semantic-unknown-intent')
    from datetime import datetime
    try:at=datetime.fromisoformat(str(call.get('at','')).replace('Z','+00:00'));aware=at.utcoffset() is not None
    except (ValueError,TypeError):aware=False
    command=call.get('command');need(aware and isinstance(command,dict) and command.get('op') in ('click','hover','filter','reload-records','download-begin') and type(command.get('tabId')) is int and command['tabId'] in (s.get('tab_id'),s.get('record_tab_id')),'semantic-unknown-intent')
    keys=[c.get('key') for c in calls];need(all(isinstance(k,str) and k for k in keys) and len(set(keys))==len(keys),'semantic-unknown-intent')
    if command['op'] in ('click','hover'):need(isinstance(command.get('locator'),dict) and command['locator'].get('by') in ('selector','text','role') and isinstance(command['locator'].get('value'),str) and command['locator']['value'] and command.get('kind') in ('navigation','company','company-confirm','filter','export','download'),'semantic-unknown-intent')
    if command['op']=='filter':need(command.get('kind')=='filter' and isinstance(command.get('locator'),dict),'semantic-unknown-intent')
    if command['op']=='reload-records':need(str(command.get('groupid'))==str(s.get('groupid')) and command.get('reloadKey')==s['work_order_id']+'-records-'+str(s['revision']),'semantic-unknown-intent')
    return {'key':call['key'],'phase':phase,'command_sha256':digest(command),'at':call['at'],'completion_claimed':False,'automatic_replay_allowed':False}

def pinned_zero_query_job(state,observation,journal_path):
    """Use the original frozen job range, never a zero flag or displayed date."""
    previous=list(sys.path)
    try:
        sys.path.insert(0,str(_records_directory))
        spec=importlib.util.spec_from_file_location('workshop_pinned_query_verifier',_records_directory/'bridge-governance-query.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        need(Path(module.g.__file__).resolve()==_records_directory/'governance_dom.py','semantic-query-verifier-origin-conflict')
        return module.verified_query_job(state,observation,journal_path)
    finally:sys.path[:]=previous


def sender_file_pending(s,job):
    """Recognize the existing durable paste intent; never claim it completed."""
    if not (s.get('status')=='unknown' and s.get('phase')=='file-confirm'):return False
    need(job.get('type')=='file' and s.get('paste_empty_composer_verified') is True and type(s.get('pid')) is int and s['pid']>0 and type(s.get('baseline')) is int and s['baseline']>=0,'semantic-file-pending-contract-invalid')
    from datetime import datetime
    intended=datetime.fromisoformat(s.get('send_intent_at','').replace('Z','+00:00'));need(intended.utcoffset() is not None,'semantic-file-pending-aware-intent-required')
    intents=[e for e in s.get('events',[]) if e.get('stage')=='send-intent']
    need(len(intents)==1 and intents[0].get('file')==job.get('file_name') and intents[0].get('sha256')==job.get('file_sha256'),'semantic-file-pending-original-intent-required')
    observed=datetime.fromisoformat(intents[0].get('at','').replace('Z','+00:00'));need(observed.utcoffset() is not None and observed>=intended,'semantic-file-pending-event-time-invalid')
    read=s.get('last_read',{});need(read.get('read_scope')=='application-windows-complete' and read.get('truncated') is False and not read.get('truncation_reason'),'semantic-file-pending-complete-snapshot-required')
    reference({'path':job.get('file'),'sha256':job.get('file_sha256')})
    return True


def case_alias_v3_monitor():
    directory=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('workshop_case_alias_v3_monitor',directory/'case_alias_v3_monitor.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(Path(module.__file__).resolve()==directory/'case_alias_v3_monitor.py','semantic-v3-monitor-origin-conflict')
    return module

def fresh_completed_evidence(journal_path,schema,*,role,dispatch_started_at,now):
    directory=Path(__file__).resolve().parent
    spec=importlib.util.spec_from_file_location('workshop_fresh_completed_evidence',directory/'fresh_completed_evidence.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.fresh_completed_evidence(journal_path,schema,role=role,dispatch_started_at=dispatch_started_at,now=now)


def verified_center_profile_pending(s,role,journal_path):
    """A pinned center date-query review gate is liveness, never completion."""
    need(role=='violation_operator' and s.get('phase')=='profile-required' and s.get('waiting_for')=='analysis-all-reasons-actual-view-profile-required','semantic-center-profile-gate-required')
    need(s.get('profile_accepted') is False and s.get('business_progress_changed') is False and s.get('pages')==[] and not any(s.get(k) for k in ('unknown_intent','read_only_settling','needs_changed_tree','settling_exhausted','hold','error','last_error')),'semantic-center-profile-unresolved')
    b=s.get('query_job_binding');need(isinstance(b,dict) and set(b)=={'kind','job','fingerprint','tab_id','query_state_path','window_id'} and b['kind']=='governance-query-job-binding-v1','semantic-center-profile-job-binding-required')
    directory=Path(__file__).resolve().parents[2]/'violation-notifier/scripts';previous=list(sys.path)
    try:
        sys.path.insert(0,str(directory));detail=importlib.import_module('governance_detail');g=importlib.import_module('governance_dom');nav=detail.nav
        need(Path(detail.__file__).resolve()==directory/'governance_detail.py' and Path(g.__file__).resolve()==directory/'governance_dom.py','semantic-center-profile-module-origin-conflict')
        job=reference(b['job']);nav.scope(job)
        need(b['fingerprint']==s['fingerprint']==nav.tag(job) and b['tab_id']==s['tab_id'] and journal_path and b['query_state_path']==str(Path(journal_path).resolve()) and type(b['window_id']) is int and b['window_id']>0 and s.get('approved_version')==nav.VERSION,'semantic-center-profile-original-scope-conflict')
        refs=s.get('observations');need(isinstance(refs,list) and refs and s.get('last_observation')==refs[-1],'semantic-center-profile-observations-required');raws=[]
        for r in refs:
            raw=reference(r);need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==s['tab_id'],'semantic-center-profile-source-conflict');tab=nav.context([{'tabs':[raw['tab']]}],s['tab_id'],job['groupid'])
            from urllib.parse import urlsplit
            need(tab.get('windowId')==b['window_id'] and urlsplit(tab['url']).path==g.CENTER and raw['tree'].get('url')=='https://life.douyin.com'+g.CENTER,'semantic-center-profile-route-conflict');ns=g.nodes(raw['tree']);nav.identity(raw['tree'],job['identity']);need(not any(any(t in n.get('name','') for t in ('扫码登录','风险验证','安全验证','账号异常','请完成验证')) for n in ns),'semantic-center-profile-risk-stop');raws.append(raw)
        calls=s.get('calls');need(isinstance(calls,list) and calls and all(c.get('state')=='confirmed' for c in calls),'semantic-center-profile-confirmed-calls-required');phase='open-date';plan=g.QueryPlan(job['start'],job['end_exclusive']);index=-1
        for call in calls:
            need(call.get('before') in refs,'semantic-center-profile-original-before-required');i=refs.index(call['before']);need(i>index,'semantic-center-profile-call-order-invalid');index=i;step=plan.next(raws[i]['tree'],{'phase':phase});command={**step['command'],'tabId':s['tab_id']};need(call.get('command')==command and call.get('postcondition')==({'month_delta':step['expected_month_delta']} if step.get('month_navigation') else None),'semantic-center-profile-call-not-derived');detail.reply_matches(command,call.get('result',{}),raws[i]);phase=step['next_phase']
        need(index<len(refs)-1 and phase=='verify-date' and plan.next(raws[-1]['tree'],{'phase':phase}).get('hold')=='analysis-all-reasons-actual-view-profile-required','semantic-center-profile-date-not-proved')
        return {'kind':'verified-center-profile-awaiting-human-v1','job':b['job'],'last_observation':refs[-1],'completion_claimed':False,'business_progress_changed':False}
    finally:sys.path[:]=previous

def verified_preselected_record_query(s,role,journal_path):
    need(role=='violation_operator' and journal_path,'semantic-preselected-record-query-required')
    previous=list(sys.path)
    try:
        sys.path.insert(0,str(_records_directory));module=importlib.import_module('preselected_record_range_recovery')
        need(Path(module.__file__).resolve()==_records_directory/'preselected_record_range_recovery.py','semantic-preselected-module-origin-conflict')
        return module.verify_continuation(s,journal_path=journal_path)
    finally:sys.path[:]=previous

_navigation_profile_path=Path(__file__).with_name('navigation_profile_progress.py')
def verified_navigation_profile_pending(s,role,journal_path):
    need(journal_path,'semantic-navigation-profile-journal-required')
    spec=importlib.util.spec_from_file_location('workshop_navigation_profile_progress',_navigation_profile_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verify(s,journal_path,role=role,navigation_directory=_records_directory)

def records_navigation_progress(s,role,journal_path):
    need(journal_path,'semantic-records-navigation-journal-required')
    file=Path(__file__).with_name('records_navigation_progress.py')
    spec=importlib.util.spec_from_file_location('workshop_records_navigation_progress',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verify(s,journal_path,role=role,records_directory=_records_directory)

def extract(s,role,journal_path=None):
    need(isinstance(s,dict),'semantic-journal-object-required')
    need(not(s.get('error') or s.get('last_error')),'semantic-terminal-error')
    # Only the active verify-switch hold is terminal. Historical holds retained
    # after typed accountAfterSwitch recovery remain audit evidence.
    active_switch_hold=(s.get('backend')=='local-dom-bridge' and s.get('phase')=='verifySwitch' and s.get('waiting_for')=='company-switch-readonly-scope')
    held=s.get('switch_read_hold',{})
    need(not(active_switch_hold and isinstance(held,dict) and (held.get('state')=='hold' or held.get('error'))),'semantic-switch-read-hold')
    # Unknown transport/UI outcomes require monitor attention. This does not
    # authorize retry; the original operator still owns read-only reconciliation.
    pending=operator_tail_pending(s) if any(c.get('state')=='unknown' for c in s.get('calls',[])) else None
    automatic=automatic_tokens(s,role,journal_path)
    # Owner presence is usable only after automatic_tokens proved the canonical
    # production chain above; an unverified owner raises before this exception.
    need(not s.get('settling_exhausted') and (not s.get('hold') or 'automatic_stop_loss_owner' in s),'semantic-explicit-hold')
    tokens={};schema=None;binding=None;profile_review_pending=None
    def add(label,facts):tokens[label]=digest(facts)
    if isinstance(s.get('binding'),dict) and s['binding'].get('schema')=='records-region-navigation-v1':
        return records_navigation_progress(s,role,journal_path)
    elif isinstance(s.get('job'),dict) and 'status' in s and 'fingerprint' in s:
        job=s['job'];need(hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==s['fingerprint'],'semantic-sender-job-changed')
        need(job.get('scope')=='test' and job.get('kind')=='group' and job.get('target')=='测试群请忽略','semantic-sender-target-conflict')
        schema='wecom-v1';binding={'key':job['key'],'fingerprint':s['fingerprint']}
        sender_pending=s.get('status')=='unknown' and s.get('phase') in ('verify-sent','image-verify-sent') and s.get('checks',0)<5 and not s.get('error')
        sender_pending=sender_pending or sender_file_pending(s,job)
        need(s.get('status') not in ('failed','abandoned') and (s.get('status')!='unknown' or sender_pending),'semantic-terminal-sender-outcome')
        for event in s.get('events',[]):
            stage=event.get('stage')
            if stage=='recipient-verified':
                need(event.get('name')==job['target'] and event.get('kind')==job['kind'],'semantic-sender-recipient-proof')
                add(stage,{'target':job['target'],'kind':job['kind']})
            elif stage=='draft-staged' and job['type']=='text':add(stage,{'text':job['text']})
        if s.get('status')=='complete':
            need(s.get('phase')=='done' and s.get('sent') is True and s.get('ui_confirmed') is True and s.get('completed_at') and any(e.get('stage')=='ui-confirmed' and e.get('recipient')==job['target'] for e in s.get('events',[])),'semantic-sender-receipt-required')
            if s.get('image_receipt'):
                need(s['image_receipt'].get('source_sha256')==job.get('file_sha256') and s['image_receipt'].get('row_signature'),'semantic-image-receipt-invalid')
            add('ui-confirmed',{'job':job,'image_receipt':s.get('image_receipt')})
    elif s.get('backend')=='local-dom-bridge' and s.get('work_order_id') and isinstance(s.get('checkpoints'),list):
        schema='operator-v1';binding={k:s.get(k) for k in ('work_order_id','fingerprint','company','groupid','date_range')}
        need(s.get('state') in ('running','complete'),'semantic-operator-terminal-state')
        for cp in s['checkpoints']:
            stage=cp.get('stage')
            # Intent is not completed progress; UUID/time cannot add stages.
            if stage not in ('identity','switch','navigation','filter','export-generated','download-complete'):continue
            facts={k:v for k,v in cp.items() if k not in ('at','event_id')}
            if stage in ('identity','switch'):need(isinstance(cp.get('identity'),dict) and all(cp['identity'].get(k) for k in ('provider','account_id','manager')),'semantic-identity-checkpoint-incomplete')
            if stage=='filter':need(cp.get('date_range')==s.get('date_range') and type(cp.get('page_filtered')) is int,'semantic-filter-checkpoint-incomplete')
            if stage=='export-generated':need(cp.get('generated_at') and cp.get('record_url'),'semantic-generated-receipt-incomplete')
            if stage=='download-complete':reference({'path':cp.get('path'),'sha256':cp.get('sha256')})
            label=stage+(':'+str(cp.get('identity_scope','legacy')) if stage=='identity' else '')
            # Different proofs for an existing stage are a changed binding, not
            # another achievement. The director compares every old token.
            if label in tokens:need(tokens[label]==digest(facts),'semantic-completed-stage-rewritten')
            add(label,facts)
    elif s.get('kind')=='exact-existing-case-operation-v1':
        need(role=='complaint_operator' and journal_path,'semantic-role-schema-conflict')
        return exact_recheck_monitor().semantic(Path(journal_path),s,role=role)
    elif s.get('kind')=='known-public-complaint-case-operation-v3':
        need(role=='complaint_operator' and journal_path,'semantic-role-schema-conflict')
        return case_alias_v3_monitor().semantic(Path(journal_path),s,role=role)
    elif s.get('kind')=='unbound-case-operation-v1':
        need(role=='complaint_operator' and journal_path,'semantic-role-schema-conflict');schema='complaint-case-alias-inspection-v1';m=s.get('manifest',{});binding={'manifest':m}
        need(m.get('kind')=='unbound-case-inspection-manifest-v1' and s.get('submission_enabled') is False and s.get('send_enabled') is False,'semantic-alias-policy-invalid')
        for ref in m.get('inputs',{}).values():reference(ref)
        need(s.get('state') in ('ready','opened','closed','complete'),'semantic-unknown-alias-inspection')
        if s['state']=='complete':
            directory=Path(__file__).resolve().parent
            spec=importlib.util.spec_from_file_location('workshop_alias_completion_verifier',directory/'fresh_completed_evidence.py');verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
            proof,_,_=verifier.alias_verified(Path(journal_path),s)
            add('closed-case-alias',{'review_key':m['review_key'],'proof':proof,'normal_before':s['normal_before'],'drawer':s['drawer'],'normal_after':s['normal_after']})
    elif isinstance(s.get('manifest'),dict) and s['manifest'].get('kind') in ('existing-result-inspection-manifest-v1','complaint-draft-inspection-manifest-v1'):
        schema='complaint-inspection-v1';m=s['manifest'];need(role=='complaint_operator','semantic-role-schema-conflict');binding={'manifest':m}
        for ref in m.get('inputs',{}).values():reference(ref)
        need('unknown' not in str(s.get('state','')),'semantic-unknown-inspection')
        if s.get('state')=='complete':
            for key in ('normal_before','normal_after'):reference(s.get(key))
            reference(s.get('drawer') or s.get('form'))
            add('closed-inspection',{'review_key':m['review_key'],'before':s['normal_before'],'after':s['normal_after'],'body':s.get('drawer') or s.get('form')})
    elif s.get('fingerprint') and type(s.get('tab_id')) is int and isinstance(s.get('calls'),list) and 'phase' in s:
        schema='dom-navigation-v1';binding={'fingerprint':s['fingerprint'],'tab_id':s['tab_id']}
        if 'preselected_record_range_reconciliation' in s:verified_preselected_record_query(s,role,journal_path)
        need(role in ('complaint_operator','violation_operator'),'semantic-role-schema-conflict')
        need('unknown' not in str(s['phase']),'semantic-unknown-navigation')
        if s.get('phase') in ('profile-required','profileRequired') and not s.get('stable_normal_verified'):
            if role=='violation_operator' and s.get('phase')=='profile-required' and s.get('waiting_for')=='analysis-all-reasons-actual-view-profile-required':
                profile_review_pending=verified_center_profile_pending(s,role,journal_path)
            elif role=='violation_operator' and s.get('phase')=='profileRequired' and s.get('waiting_for')=='live-violation-analysis-date-and-pagination-profile':
                profile_review_pending=verified_navigation_profile_pending(s,role,journal_path)
            else:raise ProgressError('semantic-profile-review-required')
        if s.get('stable_normal_verified'):
            need(role=='complaint_operator' and s.get('normal_probe') and len(s.get('stable_read_evidence',[]))>=2,'semantic-normal-proof-incomplete')
            for r in s['stable_read_evidence']:reference(r)
            add('normal-source-verified',s['normal_probe'])
        pages=s.get('pages',[])
        need([p.get('page') for p in pages]==list(range(1,len(pages)+1)),'semantic-query-page-sequence-invalid')
        if pages:
            ids=[r['notice_id'] for p in pages for r in p['rows']];need(len(ids)==len(set(ids))<=pages[0]['total'] and all(p['total']==pages[0]['total'] for p in pages),'semantic-query-page-coverage-changed')
        for p in s.get('pages',[]):
            need(role=='violation_operator' and p.get('query_verified') is True and type(p.get('page')) is int,'semantic-query-page-invalid')
            raw=reference(p.get('observation'));need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==s['tab_id'],'semantic-query-source-changed')
            zero=p.get('total')==0 or 'empty_result' in p
            if zero:
                job=pinned_zero_query_job(s,raw,journal_path)
                parsed=records.records_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive'],require_date=True)
            else:parsed=records.records_page(raw['tree'],require_date=False)
            need(parsed=={k:v for k,v in p.items() if k not in ('observation','query_verified') }|{'query_verified':bool(zero)},'semantic-query-page-not-proved-by-dom')
            add('records-page:'+str(p['page']),{k:p[k] for k in ('page','total','rows','next')})
        if 'details' in s:
            need(role=='violation_operator' and s.get('cursor')==len(s['details']),'semantic-detail-cursor-invalid')
            manifest=s.get('manifest',{});need(manifest.get('kind')=='governance-detail-inspection-manifest-v1','semantic-detail-source-manifest-required')
            source=reference(manifest['inputs']['query']);job=reference(manifest['inputs']['job'])
            need(source.get('fingerprint')==s['fingerprint'] and hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==s['fingerprint'] and source.get('tab_id')==s['tab_id'],'semantic-detail-source-binding-changed')
            expected=[r['notice_id'] for r in source['rows']];need(len(set(expected))==len(expected) and len(s['details'])<=len(expected),'semantic-detail-source-cursor-outside-workorder')
            binding['source_manifest']=manifest
            ids=[]
            for item in s['details']:
                need(item.get('state')=='complete' and item.get('notice_id') and item['notice_id'] not in ids,'semantic-detail-closure-required');ids.append(item['notice_id']);need(ids==expected[:len(ids)],'semantic-detail-source-order-changed')
                for k in ('normal_before','normal_after','detail_observation'):reference(item.get(k))
                add('detail:'+item['notice_id'],{'notice_id':item['notice_id'],'facts':item.get('facts'),'normal_after':item['normal_after']})
    else:raise ProgressError('semantic-journal-schema-unsupported')
    need(binding and binding.get('fingerprint',True),'semantic-journal-identity-required')
    tokens.update(automatic)
    result={'schema':schema,'binding':binding,'tokens':tokens}
    if profile_review_pending is not None:result['profile_review_pending']=profile_review_pending
    if schema=='operator-v1':
        result['confirmed_call_prefix']=[digest(c) for c in s.get('calls',[]) if c.get('state')=='confirmed']
        if pending:result['pending_operator_intent']=pending
    return result

def exact_recheck_monitor():
    file=Path(__file__).with_name('complaint_exact_recheck_monitor.py')
    spec=importlib.util.spec_from_file_location('workshop_complaint_exact_recheck_monitor',file)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
