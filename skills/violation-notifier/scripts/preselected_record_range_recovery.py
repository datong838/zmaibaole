"""Current-only read reconciliation of an already committed single-day input.
No date/query click exists here. Saved proof never claims a new selection effect.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,re,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import governance_dom as g
spec=importlib.util.spec_from_file_location('preselected_range_navigation',Path(__file__).with_name('bridge-navigation.py'));nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
KIND='verified-record-preselected-range-reconciliation-v1'
FIELD='preselected_record_range_reconciliation'
need=g.need

def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
import verification_session as verification
def _canonical_uncached(path):
    p=Path(path);need(p.is_absolute() and p.resolve()==p and not p.is_symlink(),'preselected-range-canonical-path-required');return p
def reference(path):p=canonical(path);return {'path':str(p),'sha256':sha(p.read_bytes())}
def document(r):
    need(isinstance(r,dict) and set(r)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(r['sha256'])),'preselected-range-ref-invalid');p=canonical(r['path']);return nav.read_pinned(p,r['sha256'])
def immutable(path,raw):
    p=canonical(path);p.parent.mkdir(parents=True,exist_ok=True)
    try:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except FileExistsError:need(p.read_bytes()==raw,'preselected-range-immutable-conflict')
    return reference(p)
def aware(value):
    t=datetime.fromisoformat(str(value).replace('Z','+00:00'));need(t.utcoffset() is not None,'preselected-range-aware-time-required');return t

def observed(raw,job,tab,window,allow_loading_history=False):
    need(raw.get('source')=='local-dom-bridge' and raw.get('not_business_capture') is True and raw.get('tab_id')==tab,'preselected-range-public-source-required');current=nav.context([{'tabs':[raw['tab']]}],tab,job['groupid']);need(current.get('windowId')==window and urlsplit(current['url']).path==g.RECORDS and raw['tree'].get('url')=='https://life.douyin.com'+g.RECORDS,'preselected-range-window-route-conflict');ns=list(g.nodes(raw['tree']));nav.identity(raw['tree'],job['identity']);g.root(raw['tree'],g.RECORDS)
    need(not any(n.get('role')=='alertdialog' or any(t in n.get('name','') for t in ('扫码登录','风险验证','安全验证','账号异常','请完成验证')) for n in ns),'preselected-range-busy-or-risk');aware(raw['observed_at']);plan=g.QueryPlan(job['start'],job['end_exclusive']);need(g.date_value(raw['tree'])==plan.start+' ~ '+plan.end,'preselected-range-input-not-desired')
    busy=any(n.get('attributes',{}).get('aria-busy')=='true' or n.get('role')=='progressbar' for n in ns)
    if busy:
        need(allow_loading_history,'preselected-range-busy-or-risk');return raw['tree']
    page=g.records_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']);need(page.get('all_scope') is True and all(plan.start<=r['violation_date']<=plan.end for r in page['rows']),'preselected-range-record-scope-conflict');return raw['tree']
def calendar_signature(tree,target):
    panels=[n for n in g.nodes(tree) if 'governance_merchant-date-picker-popper' in g.cls(n)];views=g.calendar(tree);selected=[(day,node) for v in views for day,node in v['cells'].items() if 'governance_merchant-date-selected' in g.cls(node)];need(len(selected)==1 and selected[0][0]==target and 'governance_merchant-date-state-single' in g.cls(selected[0][1]),'preselected-range-sole-selected-single-required');item=selected[0][1]
    need(not any({'governance_merchant-date-state-start','governance_merchant-date-state-end'}&g.cls(n) for p in panels for n in g.walk(p)),'preselected-range-range-edge-forbidden');parent=g.one([n for p in panels for n in g.walk(p) if n.get('tag')=='span' and len(n.get('children',[]))==1 and n['children'][0].get('selector')==item['selector']],'preselected-range-selected-parent-required');need({'governance_merchant-date-selected','governance_merchant-date-state-single'}<=g.cls(parent),'preselected-range-parent-single-required');return sha(encoded(panels)),item

def reply_matches(command,result,raw):
    target=g.one([n for n in g.nodes(raw['tree']) if n.get('selector')==command['locator']['value']],'preselected-range-original-target-not-unique');clicked=result.get('clicked',{});need(result.get('kind')==command['kind'] and result.get('version')==nav.VERSION and all(clicked.get(k)==target.get(k) for k in ('selector','tag','name')) and clicked.get('attributes',{}).get('class')==target.get('attributes',{}).get('class') and clicked.get('disabled') is not True,'preselected-range-original-reply-invalid')
def original_contract(s,job,job_ref,state_path,last_sha):
    nav.scope(job);plan=g.QueryPlan(job['start'],job['end_exclusive']);need(plan.start==plan.end,'preselected-range-current-single-day-only');b=s.get('query_job_binding',{});need(b=={'kind':'governance-query-job-binding-v1','job':job_ref,'fingerprint':nav.tag(job),'tab_id':s.get('tab_id'),'query_state_path':str(state_path),'window_id':b.get('window_id')} and type(b.get('window_id')) is int and b['window_id']>0,'preselected-range-original-job-binding-invalid');need(s.get('fingerprint')==nav.tag(job) and s.get('approved_version')==nav.VERSION and type(s.get('tab_id')) is int,'preselected-range-original-scope-invalid')
    need(s.get('phase')=='select-end' and s.get('settling_exhausted') is True and s.get('business_progress_changed') is False and s.get('profile_accepted') is False and s.get('pages')==[] and not any(s.get(k) for k in ('last_error','error','hold','unknown_intent',FIELD,'calendar_target_repair','selected_single_start_repair','records_zero_reconciliation')),'preselected-range-original-phase-invalid');calls=s.get('calls');refs=s.get('observations');need(isinstance(calls,list) and len(calls)==2 and all(c.get('state')=='confirmed' for c in calls) and isinstance(refs,list) and len(refs)==7,'preselected-range-original-two-calls-seven-reads-required');need(s.get('last_observation')==refs[-1] and refs[-1]['sha256']==last_sha and calls[0].get('before')==refs[0] and calls[1].get('before')==refs[1] and s.get('needs_changed_tree')==refs[1],'preselected-range-original-prefix-invalid')
    pending=s.get('read_only_settling',{});need(pending=={'checks':5,'max_checks':5,'original_call_index':1,'last_observation':refs[-1],'reason':'governance-start-date-selection-not-observed'} and s.get('waiting_for')=='confirmed-action-settling-exhausted-supervisor-reconcile-original-journal','preselected-range-original-stop-invalid')
    raws=[document(r) for r in refs];trees=[observed(r,job,s['tab_id'],b['window_id']) for r in raws];times=[aware(r['observed_at']) for r in raws];need(times==sorted(times),'preselected-range-original-time-order-invalid');signature,item=calendar_signature(trees[1],plan.start)
    for t in trees[1:]:need(calendar_signature(t,plan.start)[0]==signature,'preselected-range-original-calendar-changed')
    for i,phase in enumerate(('open-date','select-start')):
        step=plan.next(trees[i],{'phase':phase});command={**step['command'],'tabId':s['tab_id']};need(calls[i].get('command')==command and calls[i].get('postcondition') is None,'preselected-range-original-command-not-derived');reply_matches(command,calls[i].get('result',{}),raws[i]);need(times[i]<=aware(calls[i]['intent_at'])<=times[i+1],'preselected-range-original-call-time-invalid')
    need(calls[1]['command']['locator']['value']==item['selector'] and {'governance_merchant-date-selected','governance_merchant-date-state-single'}<=g.cls(calls[1]['result']['clicked']),'preselected-range-original-click-was-not-selected-single')
    settled=s.get('settled_actions');need(isinstance(settled,list) and len(settled)==1 and all(settled[0].get(k)==v for k,v in {'checks':1,'max_checks':5,'original_call_index':0,'last_observation':refs[1],'reason':'governance-calendar-not-mounted'}.items()),'preselected-range-original-open-not-settled');return {'desired_range':plan.start+' ~ '+plan.end,'calendar_sha256':signature,'target_selector':item['selector'],'window_id':b['window_id'],'latest_at':raws[-1]['observed_at']}

def _proof_base_uncached(proof_ref):
    proof=document(proof_ref);need(proof.get('kind')==KIND and proof.get('ui_used') is False and proof.get('next_phase')=='verify-date' and proof.get('start_selection_effect_observed') is False and proof.get('records_query_effect_claimed') is False,'preselected-range-proof-invalid');manifest=document(proof['manifest']);need(manifest.get('kind')=='preselected-record-range-recovery-manifest-v1','preselected-range-manifest-invalid');path=canonical(manifest['query_state_path']);directory=path.parent/'.preselected-record-range-recovery'/manifest['original_journal']['sha256'];need(Path(proof_ref['path'])==directory/'proof.json' and Path(proof['manifest']['path'])==directory/'manifest.json' and Path(manifest['original_journal']['path'])==directory/'original-journal.json' and Path(manifest['original_job']['path'])==directory/'original-job.json','preselected-range-proof-canonical-path-invalid');original=document(manifest['original_journal']);job=document(manifest['original_job']);need(document(manifest['canonical_job'])==job and Path(manifest['canonical_job']['path'])==path.parent/'navigation-job.json','preselected-range-canonical-job-invalid');facts=original_contract(original,job,manifest['canonical_job'],path,manifest['original_last_observation']['sha256']);need(manifest['facts']==facts and manifest['original_last_observation']==original['last_observation'] and proof.get('original_stop')=={k:original[k] for k in ('read_only_settling','needs_changed_tree','waiting_for','settling_exhausted')},'preselected-range-proof-original-conflict')
    commands=[{'op':'tabs'},{'op':'ping','tabId':original['tab_id']},{'op':'tree','tabId':original['tab_id']},{'op':'tabs'}];intent=document(proof['readonly_intent']);need(Path(proof['readonly_intent']['path'])==directory/'readonly-intent.json' and intent.get('kind')=='preselected-range-readonly-intent-v1' and intent.get('manifest')==proof['manifest'] and intent.get('commands')==commands and intent.get('ui_input_available') is False,'preselected-range-read-intent-invalid');records=[document(r) for r in proof['read_replies']];need(aware(intent['created_at'])<=aware(records[0]['at']),'preselected-range-read-intent-time-invalid');need(len(records)==4 and all(r.get('command')==c and r.get('reply',{}).get('ok') is True for r,c in zip(records,commands)),'preselected-range-four-read-proof-required');need([Path(r['path']) for r in proof['read_replies']]==[directory/(str(i)+'-read.json') for i in range(4)],'preselected-range-read-path-invalid');fresh=document(proof['fresh_observation']);validate_fresh(records,original,job,facts,fresh);need(Path(proof['fresh_observation']['path'])==directory/'fresh-observation.json' and proof['at']==fresh['observed_at'],'preselected-range-fresh-binding-invalid')
    expected=json.loads(encoded(original));expected['observations'].append(proof['fresh_observation']);expected.update(last_observation=proof['fresh_observation'],phase='verify-date');expected[FIELD]=proof_ref;expected.setdefault('settled_actions',[]).append({**original['read_only_settling'],'reconciled_as':'already-committed-record-date-input','start_selection_effect_observed':False,'recovery_proof':proof_ref,'settled_at':proof['at']})
    for key in ('read_only_settling','needs_changed_tree','waiting_for','settling_exhausted'):expected.pop(key,None)
    return proof,manifest,original,job,expected

def validate_fresh(records,original,job,facts,fresh):
    tab=original['tab_id'];before=nav.context(records[0]['reply']['result'],tab,job['groupid']);ping=records[1]['reply']['result'];tree=records[2]['reply']['result'];after=nav.context(records[3]['reply']['result'],tab,job['groupid']);need(before['url']==after['url'] and before.get('windowId')==after.get('windowId')==facts['window_id'] and tree.get('url')=='https://life.douyin.com'+urlsplit(after['url']).path,'preselected-range-fresh-context-changed');need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('governance_query_policy')=='observed-dom-20261021-v1' and ping.get('governance_calendar_policy')=='date-item-div-v3-single','preselected-range-fresh-policy-required');need(fresh=={'source':'local-dom-bridge','observed_at':records[-1]['at'],'tab_id':tab,'tab':after,'tree':tree,'not_business_capture':True},'preselected-range-fresh-raw-conflict');observed(fresh,job,tab,facts['window_id']);signature,item=calendar_signature(tree,job['start']);need(signature==facts['calendar_sha256'] and item['selector']==facts['target_selector'],'preselected-range-fresh-calendar-changed');times=[aware(r['at']) for r in records];need(aware(facts['latest_at'])<=times[0]<=times[1]<=times[2]<=times[3],'preselected-range-fresh-time-invalid')

def validate_read_stage(records,original,job,facts):
    index=len(records)-1;record=records[-1];value=record['reply']['result'];tab=original['tab_id']
    if index==0:
        current=nav.context(value,tab,job['groupid']);need(current.get('windowId')==facts['window_id'] and urlsplit(current['url']).path==g.RECORDS,'preselected-range-fresh-before-scope-conflict')
    elif index==1:
        need(value.get('version')==nav.VERSION and value.get('safety')=='DOM-only' and value.get('governance_query_policy')=='observed-dom-20261021-v1' and value.get('governance_calendar_policy')=='date-item-div-v3-single','preselected-range-fresh-policy-required')
    elif index==2:
        current=nav.context(records[0]['reply']['result'],tab,job['groupid']);raw={'source':'local-dom-bridge','observed_at':record['at'],'tab_id':tab,'tab':current,'tree':value,'not_business_capture':True};observed(raw,job,tab,facts['window_id']);need(calendar_signature(value,job['start'])[0]==facts['calendar_sha256'],'preselected-range-fresh-calendar-changed')

def verify_recovered(current,proof_ref):
    proof,manifest,original,job,expected=proof_base(proof_ref);need(current==expected,'preselected-range-recovered-delta-invalid');return {'kind':KIND,'original_journal':manifest['original_journal'],'proof':proof_ref,'original_error':{'code':'governance-start-date-selection-not-observed','message':'governance-start-date-selection-not-observed'}}
def verify_continuation(state,job=None,journal_path=None):
    need(FIELD in state,'preselected-range-proof-required');proof,manifest,original,archived_job,base=proof_base(state[FIELD]);need(job is None or job==archived_job,'preselected-range-job-conflict');need(journal_path is None or str(canonical(journal_path))==manifest['query_state_path'],'preselected-range-journal-conflict');n=len(original['calls']);need(state.get('calls',[])[:n]==original['calls'] and state.get('observations',[])[:len(base['observations'])]==base['observations'] and state.get('settled_actions',[])[:len(base['settled_actions'])]==base['settled_actions'],'preselected-range-original-prefix-changed');need(all(state.get(k)==base.get(k) for k in ('fingerprint','tab_id','approved_version','query_job_binding','business_progress_changed','profile_accepted',FIELD)),'preselected-range-continued-binding-changed');need(not any(state.get(k) for k in ('settling_exhausted','hold','error','last_error','unknown_intent')) and all(c.get('state')=='confirmed' for c in state.get('calls',[])),'preselected-range-continued-unresolved')
    need(state.get('last_observation')==state['observations'][-1],'preselected-range-continued-last-ref-invalid')
    if len(state['calls'])==n:
        comparable=json.loads(encoded(state));comparable['observations']=base['observations'];comparable['last_observation']=base['last_observation'];verify_recovered(comparable,state[FIELD])
    else:
        phase='verify-date';index=len(base['observations'])-1;plan=g.QueryPlan(archived_job['start'],archived_job['end_exclusive']);refs=state['observations'];window=manifest['facts']['window_id']
        for ordinal,call in enumerate(state['calls'][n:]):
            need(call.get('before') in refs and (refs.index(call['before'])>=index if ordinal==0 else refs.index(call['before'])>index),'preselected-range-continued-call-order-invalid');index=refs.index(call['before']);raw=document(call['before']);observed(raw,archived_job,state['tab_id'],window)
            if phase=='collect-page':
                page=g.records_page(raw['tree'],start=archived_job['start'],end_exclusive=archived_job['end_exclusive']);need(not page['next']['disabled'],'preselected-range-unexpected-pagination');command={**page['next']['command'],'tabId':state['tab_id']}
            else:command={**plan.next(raw['tree'],{'phase':phase})['command'],'tabId':state['tab_id']}
            need(call.get('command')==command,'preselected-range-continued-command-not-derived');reply_matches(command,call.get('result',{}),raw);phase='collect-page'
        need(state.get('phase') in ('collect-page','page-collected','next-page','capture-complete'),'preselected-range-continued-phase-invalid')
    # Only the independently derived, confirmed first new query authorizes later
    # explicit busy observations as non-result history. Every command before and
    # every published result page remains strictly non-busy.
    query_call=state['calls'][n] if len(state['calls'])>n else None
    query_before=state['observations'].index(query_call['before']) if query_call else None
    result_refs=[p.get('observation') for p in state.get('pages',[])]
    for observation_index,r in enumerate(state['observations'][len(base['observations']):],len(base['observations'])):
        raw=document(r);loading_allowed=query_before is not None and observation_index>query_before and r not in result_refs and not (state.get('phase')=='capture-complete' and r==state['last_observation'])
        observed(raw,archived_job,state['tab_id'],manifest['facts']['window_id'],allow_loading_history=loading_allowed)
        if loading_allowed and any(n.get('attributes',{}).get('aria-busy')=='true' or n.get('role')=='progressbar' for n in g.nodes(raw['tree'])):
            need(aware(raw['observed_at'])>=aware(query_call['intent_at']),'preselected-range-loading-before-query-intent')
    if state.get('phase')=='capture-complete':need(not state.get('needs_changed_tree') and not state.get('read_only_settling'),'preselected-range-completed-query-unresolved')
    return {'kind':KIND,'proof':state[FIELD],'original_call_count':n,'next_phase':'verify-date','original_journal':manifest['original_journal']}

def reconcile(job_path,state_path,expected_sha,last_sha,invoke,checkpoint=None):
    job_path=canonical(job_path);path=canonical(state_path);need(path.name=='records-query.json' and job_path==path.parent/'navigation-job.json','preselected-range-current-canonical-required')
    with path.with_name(path.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);raw=path.read_bytes();jobraw=job_path.read_bytes();state=json.loads(raw);job=json.loads(jobraw);jobref=reference(job_path)
        if FIELD in state:verify_continuation(state,job,path);raise ValueError('preselected-range-already-reconciled-no-read')
        need(sha(raw)==expected_sha,'preselected-range-original-sha-required');facts=original_contract(state,job,jobref,path,last_sha);directory=path.parent/'.preselected-record-range-recovery'/expected_sha;oldref=immutable(directory/'original-journal.json',raw);oldjob=immutable(directory/'original-job.json',jobraw);manifest={'kind':'preselected-record-range-recovery-manifest-v1','query_state_path':str(path),'canonical_job':jobref,'original_journal':oldref,'original_job':oldjob,'original_last_observation':state['last_observation'],'facts':facts};mr=immutable(directory/'manifest.json',encoded(manifest));proofpath=directory/'proof.json'
        if proofpath.exists():pr=reference(proofpath);_,_,_,_,new=proof_base(pr)
        else:
            intent=directory/'readonly-intent.json';commands=[{'op':'tabs'},{'op':'ping','tabId':state['tab_id']},{'op':'tree','tabId':state['tab_id']},{'op':'tabs'}];records=[];refs=[]
            resumed=intent.exists()
            if resumed:
                saved=json.loads(intent.read_bytes());need(saved.get('manifest')==mr and saved.get('commands')==commands,'preselected-range-original-read-intent-changed');need(all((directory/(str(i)+'-read.json')).is_file() for i in range(4)),'preselected-range-incomplete-read-intent-hold-no-replay')
            else:immutable(intent,encoded({'kind':'preselected-range-readonly-intent-v1','created_at':now(),'manifest':mr,'commands':commands,'ui_input_available':False}))
            for i,command in enumerate(commands):
                rp=directory/(str(i)+'-read.json')
                if resumed:r=json.loads(rp.read_bytes());rr=reference(rp)
                else:
                    need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'preselected-range-original-concurrent-change')
                    # This closure exposes only the four fixed public read commands.
                    reply=invoke(command);r={'command':command,'at':now(),'reply':reply};rr=immutable(rp,encoded(r))
                records.append(r);refs.append(rr);need(r.get('command')==command and isinstance(r.get('reply'),dict) and r['reply'].get('ok') is True and 'result' in r['reply'],'preselected-range-read-failed-no-replay');validate_read_stage(records,state,job,facts)
            fresh={'source':'local-dom-bridge','observed_at':records[-1]['at'],'tab_id':state['tab_id'],'tab':nav.context(records[-1]['reply']['result'],state['tab_id'],job['groupid']),'tree':records[2]['reply']['result'],'not_business_capture':True};validate_fresh(records,state,job,facts,fresh);fr=immutable(directory/'fresh-observation.json',encoded(fresh));proof={'kind':KIND,'at':fresh['observed_at'],'manifest':mr,'readonly_intent':reference(intent),'read_replies':refs,'fresh_observation':fr,'original_stop':{k:state[k] for k in ('read_only_settling','needs_changed_tree','waiting_for','settling_exhausted')},'ui_used':False,'start_selection_effect_observed':False,'records_query_effect_claimed':False,'next_phase':'verify-date'};pr=immutable(proofpath,encoded(proof));_,_,_,_,new=proof_base(pr)
        if checkpoint:checkpoint('proof-published')
        verify_recovered(new,pr);need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'preselected-range-original-concurrent-change');tmp=path.with_name(path.name+'.preselected-'+uuid.uuid4().hex);immutable(tmp,encoded(new));os.replace(tmp,path);return {'state':'reconciled','journal':reference(path),'proof':pr,'phase':'verify-date','ui_used':False,'records_query_effect_claimed':False}


def canonical(path):
    session=verification.current()
    return session.guard(_canonical_uncached,path) if session is not None else _canonical_uncached(path)

def proof_base(proof_ref):return verification.memo_proof(_proof_base_uncached,proof_ref)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',type=Path,required=True);parser.add_argument('--state',type=Path,required=True);parser.add_argument('--original-sha256',required=True);parser.add_argument('--last-observation-sha256',required=True);a=parser.parse_args()
    print(json.dumps(reconcile(a.job,a.state,a.original_sha256,a.last_observation_sha256,nav.bridge.request),ensure_ascii=False))
if __name__=='__main__':main()
