#!/usr/bin/env python3
"""Navigate only reviewed public menu labels, then hold for live center profile.
Does not ingest a batch, query unknown dates, claim zero, or advance workflow state.
"""
import argparse,copy,fcntl,hashlib,importlib.util,json,sys,uuid
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
from dom_evidence import context,identity,nodes,exact,unique,VERSION
from role_cli import write_json,digest
spec=importlib.util.spec_from_file_location('violation_navigation_bridge',ROOT/'skills/chrome-dom-export/scripts/bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
CENTER='/p/governance/home_violation_center'
def require(ok,code):
    if not ok:raise ValueError(code)
def read_pinned(path,checksum):
    import verification_session as verification
    session=verification.current()
    if session is not None:return session.read_pinned(path,checksum)
    path=Path(path).resolve();require(path.is_file(),'navigation-pinned-evidence-changed');data=path.read_bytes();require(hashlib.sha256(data).hexdigest()==checksum,'navigation-pinned-evidence-changed');return json.loads(data.decode('utf-8'))
def stamp():return datetime.now(timezone.utc).isoformat()
def tag(job):return hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
DOM_IDENTITY_KIND='verified-violation-DOM-navigation-identity-v1'
def dom_identity_context(reference):
    value=copy.deepcopy(read_pinned(reference['path'],reference['sha256']));require(value.get('kind')==DOM_IDENTITY_KIND and value.get('download_verified')is False and value.get('source_is_authoritative_export')is False,'navigation-DOM-context-kind')
    origin=value['origin'];require(origin.get('kind')=='current-daily-ready-identity-v1','navigation-current-identity-origin')
    import current_daily_ready
    facts=current_daily_ready.facts(origin['daily_report']);batch=current_daily_ready.doc(facts['ready']['batch'])
    rows=[r for r in facts['ready']['companies']if r['company']==value['company']and str(r['groupid'])==value['groupid']];require(len(rows)==1,'navigation-current-company-row')
    row=rows[0];identity=batch['company_identities'][value['groupid']];dates={'start':row['start'],'end':(__import__('datetime').date.fromisoformat(row['end_exclusive'])-__import__('datetime').timedelta(days=1)).isoformat()}
    require(value['identity']==origin['identity']==identity and identity['provider']==batch['provider_baseline'] and value['date_range']==origin['date_range']==dates,'navigation-current-identity-binding')
    binding={k:v for k,v in value.items()if k!='identity_context_id'};require(value['identity_context_id']==hashlib.sha256(json.dumps(binding,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'navigation-DOM-context-id');return value

def prepare_dom_context(plan_path,plan_sha,reference):
    plan=read_pinned(plan_path,plan_sha);value=dom_identity_context(reference);job={k:plan[k]for k in('company','groupid','start','end_exclusive')};job.update(account_verified=True,identity=value['identity'],source_context_id=value['identity_context_id'],identity_context=reference,plan_path=str(Path(plan_path).resolve()),plan_sha256=plan_sha);scope(job);return job

def scope(job):
    require(job.get('company') and str(job.get('groupid','')).isdigit(),'navigation-company-required')
    require(job.get('account_verified') is True and isinstance(job.get('identity'),dict) and all(job['identity'].get(k) for k in ('provider','account_id','manager')),'navigation-reviewed-identity-required')
    typed=job.get('identity_context')
    if not typed:require(type(job.get('source_work_order_id')) is str and job['source_work_order_id'],'navigation-source-work-order-required')
    plan=read_pinned(job['plan_path'],job['plan_sha256'])
    require(all(plan.get(k)==job[k] for k in ('company','start','end_exclusive')) and str(plan.get('groupid'))==str(job['groupid']),'navigation-independent-plan-conflict')
    require(plan.get('browser_backend')=='local-dom-bridge' and plan.get('production_enabled') is False and plan.get('platform_writes') is False and plan.get('send_target') in ('测试群请忽略',__import__('delivery_targets').target('violation-notifier')),'navigation-test-plan-required')
    require(plan.get('has_new_dates') is True and date.fromisoformat(job['start'])<date.fromisoformat(job['end_exclusive']),'navigation-plan-dates-invalid')
    if typed:
        proof=dom_identity_context(typed);require(proof['company']==job['company']and proof['groupid']==str(job['groupid'])and proof['identity']==job['identity']and proof['identity_context_id']==job['source_context_id']and 'source_work_order_id'not in job,'navigation-DOM-job-identity')
    else:
        proof=read_pinned(job['identity_receipt'],job['identity_receipt_sha256'])
        require(proof.get('operator_skill')=='douyin-laike-operator' and proof.get('backend')=='local-dom-bridge' and proof.get('work_order_id')==job['source_work_order_id'],'navigation-reviewed-receipt-required')
        require(proof.get('company')==job['company'] and str(proof.get('groupid'))==str(job['groupid']) and proof.get('account_verified') is True and proof.get('identity')==proof.get('identity_before')==job['identity'],'navigation-receipt-identity-conflict')
    # The receipt establishes reviewed identity only. Its export dates never replace this role's plan.
    return plan
def prepare(plan_path,plan_sha,receipt_path,receipt_sha,source_id):
    plan=read_pinned(plan_path,plan_sha);receipt=read_pinned(receipt_path,receipt_sha)
    job={k:plan[k] for k in ('company','groupid','start','end_exclusive')}
    job.update(account_verified=True,identity=receipt.get('identity'),source_work_order_id=source_id,plan_path=str(Path(plan_path).resolve()),plan_sha256=plan_sha,identity_receipt=str(Path(receipt_path).resolve()),identity_receipt_sha256=receipt_sha)
    scope(job);return job

def transition_binding(owner,mode):
    s=owner.s;job=owner.job
    require(mode in ('center','records'),'navigation-transition-mode-unreviewed')
    require(s.get('phase')==('observeCenter' if mode=='center' else 'observe-result'),'navigation-transition-phase-conflict')
    require(not any(c.get('state')=='unknown' for c in s['calls']),'navigation-transition-unknown-no-replay')
    entry=s['calls'][-1];command=entry['command']
    require(entry.get('state')=='confirmed' and command.get('op')=='click' and command.get('kind')=='navigation' and command.get('tabId')==owner.tab,'navigation-transition-confirmed-click-required')
    clicked=entry.get('result',{}).get('clicked',{})
    require(isinstance(clicked,dict) and clicked.get('selector')==command.get('locator',{}).get('value') and clicked.get('name')==('违规中心' if mode=='center' else '违规记录'),'navigation-transition-confirmed-reply-required')
    if mode=='center':require(entry.get('key','').endswith(':openCenter') and s.get('identity_verified_at') and sum(c.get('key','').endswith(':openCenter') for c in s['calls'])==1,'navigation-transition-original-center-required')
    else:require(s.get('mode')=='records','navigation-transition-original-records-required')
    reference=entry.get('before')
    if not reference:
        # Old Navigator journals pinned this pre-click observation as last_tree.
        reference=s.get('readonly_center_before') or s.get('last_tree',{})
        require(mode=='center' and '-openCenter-' in Path(reference.get('path','')).name,'navigation-transition-before-required')
    prior=read_pinned(reference['path'],reference['sha256'])
    require(prior.get('source')=='local-dom-bridge' and prior.get('navigation_fingerprint')==tag(job) and prior.get('tab_id')==owner.tab,'navigation-transition-original-source-conflict')
    tab=prior['tab'];context([{'tabs':[tab]}],owner.tab,job['groupid']);list(nodes(prior['tree']));identity(prior['tree'],job['identity'])
    source=urlsplit(tab['url']).path
    require(prior['tree'].get('url')=='https://life.douyin.com'+source and source.startswith('/p/'),'navigation-transition-original-path-conflict')
    label='违规中心' if mode=='center' else '违规记录';target=exact(prior['tree'],label)
    require(target.get('selector')==command.get('locator',{}).get('value'),'navigation-transition-target-conflict')
    if mode=='records':require(source==CENTER,'navigation-transition-original-center-required')
    require(tab.get('windowId') is not None,'navigation-transition-original-window-required')
    return {'before':reference,'window_id':tab['windowId'],'source_path':source,'target_path':CENTER if mode=='center' else '/p/governance/violation_list'}

def transition_paths(owner,binding):
    paths=(binding['source_path'],binding['target_path'])
    # Observed intermediate is never a target: only a scope/identity-bound confirmed center
    # transition may read through it under the original three-sample budget.
    calls=owner.s.get('calls',[])
    centers=[c for c in calls if c.get('key','').endswith(':openCenter')]
    if (owner.s.get('phase')=='observeCenter' and binding['target_path']==CENTER and len(centers)==1 and centers[0] is calls[-1] and all(c.get('state')=='confirmed' for c in calls)):
        return paths+('/p/governance/home_overview',)
    return paths

MISSING_GID_PENDING='navigation-center-missing-gid-pending'
def missing_gid_transition_sample(owner,binding,sample):
    """Only classify an observed missing-GID center transition as pending.
    It is never a completed/identity-authorizing scope observation.
    """
    if not isinstance(sample,dict)or set(sample)!={'before','after','tree'}:return False
    before,after,tree=sample['before'],sample['after'],sample['tree'];u=urlsplit(before.get('url',''));query=parse_qs(u.query,keep_blank_values=True)
    if 'groupid'in query:return False # Wrong/empty/duplicate GID is not missing.
    if owner.s.get('phase')!='observeCenter'or binding.get('target_path')!=CENTER:return False
    require(u.scheme=='https'and u.netloc=='life.douyin.com'and not u.fragment and u.path==CENTER and query=={'manual_switch':['1']},'navigation-missing-gid-before-scope')
    require(before.get('tabId')==after.get('tabId')==owner.tab and before.get('allowed')is True and before.get('windowId')==after.get('windowId')==binding['window_id'],'navigation-missing-gid-tab-window')
    target=context([{'tabs':[after]}],owner.tab,owner.job['groupid']);au=urlsplit(target['url']);aq=parse_qs(au.query,keep_blank_values=True)
    require(au.path==CENTER and not au.fragment and aq=={'groupid':[str(owner.job['groupid'])],'manual_switch':['1'],'life_biz_view_id':['22'],'life_account_biz_ids':['']},'navigation-missing-gid-target-scope')
    require(tree.get('url')=='https://life.douyin.com'+CENTER,'navigation-missing-gid-tree-path');ns=list(nodes(tree));identity(tree,owner.job['identity'])
    require(not any(any(t in n.get('name','')for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证'))for n in ns),'navigation-transition-risk-stop')
    # Original clicked source/identity/window and sole confirmed center input.
    require(transition_binding(owner,'center')==binding,'navigation-missing-gid-original-binding')
    return True

def transition_sample_scope(owner,binding,sample):
    require(isinstance(sample,dict) and set(sample)=={'before','after','tree'},'navigation-transition-sample-incomplete')
    if missing_gid_transition_sample(owner,binding,sample):return {'classification':MISSING_GID_PENDING}
    paths=transition_paths(owner,binding)
    for tab in (sample['before'],sample['after']):
        context([{'tabs':[tab]}],owner.tab,owner.job['groupid'])
        require(tab.get('windowId')==binding['window_id'] and urlsplit(tab['url']).path in paths,'navigation-transition-scope-conflict')
    require(sample['tree'].get('url') in ['https://life.douyin.com'+p for p in paths],'navigation-transition-tree-scope-conflict')
    ns=list(nodes(sample['tree']));identity(sample['tree'],owner.job['identity'])
    require(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in ns),'navigation-transition-risk-stop')

def missing_gid_scope_sample(owner,value):
    from readonly_tick_snapshot import decode
    value=decode(copy.deepcopy(value),owner.tab,owner.s['readonly_scope_routing']['window_id'])
    require(value['ping'].get('version')==VERSION and value['ping'].get('safety')=='DOM-only'and value['ping'].get('url')==value['tree'].get('url'),'navigation-missing-gid-ping')
    before=dict(unique([t for w in value['before']for t in w.get('tabs',[])if t.get('tabId')==owner.tab],'explicit-tab-not-unique'))
    return {'before':before,'after':context(value['after'],owner.tab,owner.job['groupid']),'tree':value['tree']}

def missing_gid_last_observation(owner,read=None):
    read=read or(lambda r:read_pinned(r['path'],r['sha256']))
    require(owner.s.get('observation_transport')=='readonly-scope-projection-v1','navigation-missing-gid-composite-required')
    values,evidence=observation_members(owner.s,owner.file.parent/'navigation-raw-observations',read)
    raw=owner.s['raw_observations'][-1];reply=read({'path':raw['path'],'sha256':raw['sha256']});require(raw['command']=={'op':'readonly-scope','tabId':owner.tab,'windowId':owner.s['readonly_scope_routing']['window_id']},'navigation-missing-gid-original-command')
    sample=missing_gid_scope_sample(owner,reply['result']);require([reply['result'][k]for k in ('before','ping','tree','after')]==values,'navigation-missing-gid-original-projection')
    return {'sample':sample,'evidence':evidence,'source_raw':dict(raw)}

def _adopt_missing_gid_pending(owner,binding,key,consumed):
    if owner.s.get('observation_transport')!='readonly-scope-projection-v1':return consumed
    value=missing_gid_last_observation(owner)
    if not missing_gid_transition_sample(owner,binding,value['sample']):return consumed
    for r in owner.s.get('readonly_route_recovery',[]):
        old=read_pinned(r['path'],r['sha256'])
        if old.get('transition_key')==key and old.get('sample')==value['sample']:return consumed
    require(consumed<3,'navigation-transition-settling-exhausted')
    path=owner.file.parent/'navigation-transition-evidence'/(uuid.uuid4().hex+'.json')
    # This reuses a durable original read. recorded_at is NOT a fresh read time.
    write_json(path,{'kind':'confirmed-navigation-readonly-race-v1','recorded_at':stamp(),'mode':'center','attempt':consumed,'transition_key':key,'error':MISSING_GID_PENDING,'binding':binding,'sample':value['sample'],'source_raw':value['source_raw'],'reused_original_read':True,'input_replayed':False})
    owner.s.setdefault('readonly_route_recovery',[]).append({'path':str(path),'sha256':digest(path),'error':MISSING_GID_PENDING,'attempt':consumed,'transition_key':key});owner.save();return consumed+1

def bounded_readonly_observation(owner,read,mode):
    codes={'navigation-tree-path-conflict','navigation-context-changed'} if mode=='center' else {'discovery-tree-path-conflict','discovery-context-changed'}
    require(not any(c.get('state')=='unknown' for c in owner.s.get('calls',[])),'navigation-transition-unknown-no-replay')
    binding=None;transition_key=None;consumed=0
    center_transition=mode=='center' and owner.s.get('phase')=='observeCenter'
    if center_transition:
        # Resolve the old immutable pre-click anchor before observe() updates
        # last_tree. Legacy journals need a durable ref, never a guessed path.
        binding=transition_binding(owner,mode)
        if not owner.s['calls'][-1].get('before') and not owner.s.get('readonly_center_before'):
            owner.s['readonly_center_before']=binding['before'];owner.save()
        codes.add('navigation-transition-target-pending');codes.add(MISSING_GID_PENDING)
    if owner.s.get('readonly_route_recovery'):
        binding=binding or transition_binding(owner,mode)
        transition_key=hashlib.sha256(json.dumps({'mode':mode,'binding':binding,'original_call':owner.s['calls'][-1]},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        for ref in owner.s['readonly_route_recovery']:
            if ref.get('transition_key')!=transition_key:continue
            prior=read_pinned(ref['path'],ref['sha256'])
            require(prior.get('kind')=='confirmed-navigation-readonly-race-v1' and prior.get('transition_key')==transition_key and prior.get('binding')==binding and prior.get('mode')==mode and prior.get('attempt')==consumed,'navigation-transition-original-audit-conflict')
            transition_sample_scope(owner,binding,prior['sample'])
            if prior.get('error')==MISSING_GID_PENDING:
                raw=prior.get('source_raw');require(raw in owner.s['raw_observations']and raw['command']=={'op':'readonly-scope','tabId':owner.tab,'windowId':binding['window_id']},'navigation-missing-gid-audit-owned-read');reply=read_pinned(raw['path'],raw['sha256']);require(reply.get('ok')is True and missing_gid_scope_sample(owner,reply['result'])==prior['sample'],'navigation-missing-gid-audit-raw-binding')
            consumed+=1
    if center_transition:
        transition_key=transition_key or hashlib.sha256(json.dumps({'mode':mode,'binding':binding,'original_call':owner.s['calls'][-1]},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        consumed=_adopt_missing_gid_pending(owner,binding,transition_key,consumed)
    # Retry budgets belong to the original confirmed input, not this process.
    if owner.s.get('readonly_route_exhausted') or consumed>=3:
        raise ValueError('navigation-transition-settling-exhausted')
    for attempt in range(3):
        owner._transition_sample=None
        try:
            result=read()
            if binding is not None:transition_sample_scope(owner,binding,owner._transition_sample)
            if center_transition:
                require(urlsplit(result[0]['url']).path==CENTER and result[1].get('url')=='https://life.douyin.com'+CENTER,'navigation-transition-target-pending')
            return result
        except ValueError as error:
            if str(error) not in codes:raise
            try:
                binding=binding or transition_binding(owner,mode)
                transition_sample_scope(owner,binding,owner._transition_sample)
            except (ValueError,KeyError,IndexError,OSError):raise error
            if transition_key is None:
                transition_key=hashlib.sha256(json.dumps({'mode':mode,'binding':binding,'original_call':owner.s['calls'][-1]},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
                consumed=sum(r.get('transition_key')==transition_key for r in owner.s.get('readonly_route_recovery',[]))
            folder=owner.file.parent/'navigation-transition-evidence';path=folder/(uuid.uuid4().hex+'.json')
            write_json(path,{'kind':'confirmed-navigation-readonly-race-v1','observed_at':stamp(),'mode':mode,'attempt':consumed,'transition_key':transition_key,'error':str(error),'binding':binding,'sample':owner._transition_sample,'input_replayed':False,**({'source_raw':dict(owner.s['raw_observations'][-1]),'reused_original_read':False}if str(error)==MISSING_GID_PENDING else {})})
            owner.s.setdefault('readonly_route_recovery',[]).append({'path':str(path),'sha256':digest(path),'error':str(error),'attempt':consumed,'transition_key':transition_key})
            consumed+=1
            if consumed>=3:owner.s['readonly_route_exhausted']={'transition_key':transition_key,'last_error':str(error),'max_total_samples':3}
            owner.save()
            if consumed>=3:raise

def scope_projection(reference,command,value):
    """One raw composite RPC, four named inner values; never four fake replies."""
    from readonly_tick_snapshot import decode
    # Pinned Session objects are immutable dict/list subclasses; decoder owns
    # strict plain-JSON schema. Materialize data only, never archived code.
    value=decode(copy.deepcopy(value),command['tabId'],command['windowId'])
    keys=('before','ping','tree','after')
    checksum=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'kind':'navigation-readonly-scope-projection-v1','raw':reference,'command':command,'source_rpc_count':1,'inner_read_count':4,'members':[{'index':i,'key':key,'command':value['commands'][i],'value_sha256':checksum(value[key])}for i,key in enumerate(keys)]}

def read_scope_projection(reference,read=None):
    read=read or (lambda r:read_pinned(r['path'],r['sha256']))
    projection=read(reference);raw=projection['raw'];command=projection['command']
    require(set(raw)=={'path','sha256','command'} and raw['command']==command and set(command)=={'op','tabId','windowId'} and command['op']=='readonly-scope','navigation-scope-projection-command')
    reply=read_pinned(raw['path'],raw['sha256']);require(reply.get('ok')is True and 'result'in reply,'navigation-scope-projection-raw-failed')
    require(projection==scope_projection(raw,command,reply['result']),'navigation-scope-projection-changed')
    return reply['result']


def observation_members(state,directory,read=None):
    """Verified transport adapter: returns four values, not four RPC receipts."""
    read=read or (lambda r:read_pinned(r['path'],r['sha256']))
    directory=Path(directory);tab=state['tab_id'];commands=[{'op':'tabs'},{'op':'ping','tabId':tab},{'op':'tree','tabId':tab},{'op':'tabs'}]
    transport=state.get('observation_transport')
    if transport is None:
        refs=state['raw_observations'][-4:];require(len(refs)==4 and len({str(Path(r['path']).parent)for r in refs})==1,'navigation-legacy-four-read-sequence');values=[];evidence=[]
        for i,(r,c)in enumerate(zip(refs,commands)):
            path=Path(r['path']);require(set(r)=={'path','sha256','command'}and r['command']==c and path.parent.parent==directory and path.name==str(i)+'-'+c['op']+'.json','navigation-legacy-canonical-read-command')
            reference={k:r[k]for k in ('path','sha256')};reply=read(reference);require(reply.get('ok')is True and reply.get('error')is None and 'result'in reply,'navigation-legacy-read-transport');values.append(reply['result']);evidence.append(reference)
        return values,evidence
    require(transport=='readonly-scope-projection-v1','navigation-unreviewed-transport')
    projection=state['scope_projections'][-1];require(set(projection)=={'path','sha256'},'navigation-projection-ref-schema');path=Path(projection['path']);require(path.is_absolute()and path.parent.parent==directory and path.name=='scope-projection.json'and __import__('re').fullmatch('[0-9a-f]{32}',path.parent.name)is not None,'navigation-projection-canonical-path')
    p=read(projection);raw=p['raw'];require(raw==state['raw_observations'][-1]and raw['path']==str(path.parent/'1-readonly-scope.json'),'navigation-projection-raw-journal-binding')
    value=read_scope_projection(projection,read);require(p['command']['tabId']==tab,'navigation-projection-tab-binding')
    routing=state['readonly_scope_routing'];bootstrap=routing['bootstrap'];require(set(routing)=={'window_id','bootstrap'}and bootstrap in state['raw_observations']and bootstrap['command']=={'op':'tabs'}and value['scope']['windowId']==routing['window_id'],'navigation-projection-routing-binding')
    bp=Path(bootstrap['path']);require(bp.parent.parent==directory and bp.name=='0-tabs.json','navigation-projection-bootstrap-path');br={k:bootstrap[k]for k in ('path','sha256')};b=read(br);require(b.get('ok')is True and b.get('error')is None and context(b['result'],tab,state['groupid'])['windowId']==routing['window_id'],'navigation-projection-bootstrap-scope')
    return [value[k]for k in ('before','ping','tree','after')],[br,{k:raw[k]for k in ('path','sha256')},projection]

class Navigator:
    def __init__(self,job,tab_id,file,invoke=None):
        scope(job);require(type(tab_id) is int and tab_id>0,'navigation-explicit-tab-required')
        self.job=job;self.tab=tab_id;self.file=Path(file).resolve();self.invoke=invoke or bridge.request
        if self.file.exists():
            self.s=json.loads(self.file.read_text());require(self.s.get('fingerprint')==tag(job) and self.s.get('tab_id')==tab_id,'navigation-state-scope-conflict');require(self.s.get('observation_transport')in (None,'readonly-scope-projection-v1'),'navigation-unreviewed-transport')
        else:self.s={'observation_transport':'readonly-scope-projection-v1','version':1,'fingerprint':tag(job),'tab_id':tab_id,'company':job['company'],'groupid':str(job['groupid']),'start':job['start'],'end_exclusive':job['end_exclusive'],'phase':'account','revision':0,'calls':[],'profile_accepted':False,'business_progress_changed':False,'platform_writes':False,'production_enabled':False}
    def save(self):write_json(self.file,self.s)
    def call(self,c):
        reply=self.invoke(c);require(reply.get('ok') is True,'navigation-bridge-command-failed:'+str(reply.get('error','unknown')));return reply['result']
    def click(self,target,op='click'):
        key=str(self.s['revision'])+':'+self.s['phase'];command={'op':op,'tabId':self.tab,'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
        previous=[x for x in self.s['calls'] if x['key']==key]
        if previous:
            require(len(previous)==1 and previous[0]['command']==command,'navigation-intent-changed');require(previous[0]['state']=='confirmed','navigation-outcome-unknown-no-replay');return
        require(not target.get('disabled') and target.get('selector'),'navigation-target-disabled')
        entry={'key':key,'command':command,'state':'unknown','intent_at':stamp(),'before':self.s.get('last_tree')};self.s['calls'].append(entry);self.save()
        entry['result']=self.call(command);entry['state']='confirmed';self.save()
    def go(self,phase):self.s.update(phase=phase,revision=self.s['revision']+1);self.save()
    def _observe_legacy(self):
        # Preserve each full transport reply before validating its contents.
        # These diagnostics never authorize a retry or count as business progress.
        folder=self.file.parent/'navigation-raw-observations'/uuid.uuid4().hex
        observed=[]
        def sampled(command):
            reply=self.invoke(command)
            path=folder/(str(len(observed))+'-'+command['op']+'.json')
            write_json(path,reply)
            reference={'path':str(path),'sha256':digest(path),'command':command}
            observed.append(reference)
            self.s.setdefault('raw_observations',[]).append(reference);self.save()
            require(reply.get('ok') is True,'navigation-bridge-command-failed:'+str(reply.get('error','unknown')))
            return reply['result']
        before=context(sampled({'op':'tabs'}),self.tab,self.job['groupid']);require(urlsplit(before['url']).path.startswith('/p/'),'navigation-public-page-required')
        ping=sampled({'op':'ping','tabId':self.tab});require(ping.get('version')==VERSION and ping.get('safety')=='DOM-only','navigation-reviewed-bridge-required')
        tree=sampled({'op':'tree','tabId':self.tab});all_nodes=list(nodes(tree))
        require(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in all_nodes),'navigation-risk-stop')
        after=context(sampled({'op':'tabs'}),self.tab,self.job['groupid'])
        self._transition_sample={'before':before,'after':after,'tree':tree}
        require(tree.get('url')=='https://life.douyin.com'+urlsplit(before['url']).path,'navigation-tree-path-conflict')
        require(after['url']==before['url'] and after.get('windowId')==before.get('windowId'),'navigation-context-changed')
        path=self.file.parent/'navigation-evidence'/(str(self.s['revision']).zfill(3)+'-'+self.s['phase']+'-'+uuid.uuid4().hex[:12]+'.json')
        observation={'source':'local-dom-bridge','observed_at':stamp(),'company':self.job['company'],'groupid':str(self.job['groupid']),'tab_id':self.tab,'tab':before,'tree':tree,'navigation_fingerprint':tag(self.job),'plan_sha256':self.job['plan_sha256'],'not_business_capture':True,'name_text_limit':800,'full_field_text_verified':False}
        write_json(path,observation);self.s['last_tree']={'path':str(path),'sha256':digest(path)};self.s.setdefault('observations',[]).append(self.s['last_tree'])
        self.save()
        return before,tree,all_nodes

    def observe(self):
        if self.s.get('observation_transport') is None:return self._observe_legacy()
        # Future fresh journal only. Each raw file represents one real outer RPC.
        require(self.s.get('observation_transport')=='readonly-scope-projection-v1','navigation-atomic-fresh-journal-required')
        folder=self.file.parent/'navigation-raw-observations'/uuid.uuid4().hex
        def sampled(command,index):
            reply=self.invoke(command);path=folder/(str(index)+'-'+command['op']+'.json');write_json(path,reply)
            reference={'path':str(path),'sha256':digest(path),'command':command}
            self.s.setdefault('raw_observations',[]).append(reference);self.save()
            require(reply.get('ok') is True,'navigation-bridge-command-failed:'+str(reply.get('error','unknown')))
            return reference,reply['result']
        routing=self.s.get('readonly_scope_routing')
        if routing is None:
            # A one-time read discovers the explicit window, never guesses it.
            bootstrap,tabs=sampled({'op':'tabs'},0);tab=context(tabs,self.tab,self.job['groupid'])
            require(urlsplit(tab['url']).path.startswith('/p/') and type(tab.get('windowId'))is int,'navigation-public-window-required')
            routing={'window_id':tab['windowId'],'bootstrap':bootstrap};self.s['readonly_scope_routing']=routing;self.save()
        require(set(routing)=={'window_id','bootstrap'} and type(routing['window_id'])is int,'navigation-atomic-routing-invalid')
        bootstrap=routing['bootstrap'];require(set(bootstrap)=={'path','sha256','command'} and bootstrap['command']=={'op':'tabs'} and bootstrap in self.s['raw_observations'],'navigation-atomic-bootstrap-required')
        prior=read_pinned(bootstrap['path'],bootstrap['sha256']);require(prior.get('ok')is True,'navigation-atomic-bootstrap-failed')
        known=context(prior['result'],self.tab,self.job['groupid']);require(known.get('windowId')==routing['window_id'],'navigation-atomic-bootstrap-window-conflict')
        command={'op':'readonly-scope','tabId':self.tab,'windowId':routing['window_id']};reference,value=sampled(command,1)
        from readonly_tick_snapshot import decode
        value=decode(value,self.tab,routing['window_id'])
        projection=scope_projection(reference,command,value);projection_path=folder/'scope-projection.json';write_json(projection_path,projection)
        projected={'path':str(projection_path),'sha256':digest(projection_path)};read_scope_projection(projected)
        self.s.setdefault('scope_projections',[]).append(projected);self.save()
        ping=value['ping'];require(ping.get('version')==VERSION and ping.get('safety')=='DOM-only','navigation-reviewed-bridge-required')
        tree=value['tree'];all_nodes=list(nodes(tree))
        require(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in all_nodes),'navigation-risk-stop')
        raw_before=dict(unique([t for window in value['before']for t in window.get('tabs',[])if t.get('tabId')==self.tab],'explicit-tab-not-unique'))
        after=context(value['after'],self.tab,self.job['groupid']);self._transition_sample={'before':raw_before,'after':after,'tree':tree}
        if self.s.get('phase')=='observeCenter':
            binding=transition_binding(self,'center')
            if missing_gid_transition_sample(self,binding,self._transition_sample):raise ValueError(MISSING_GID_PENDING)
        before=context(value['before'],self.tab,self.job['groupid']);require(urlsplit(before['url']).path.startswith('/p/'),'navigation-public-page-required');self._transition_sample['before']=before
        require(tree.get('url')=='https://life.douyin.com'+urlsplit(before['url']).path,'navigation-tree-path-conflict')
        require(after['url']==before['url'] and after.get('windowId')==before.get('windowId'),'navigation-context-changed')
        path=self.file.parent/'navigation-evidence'/(str(self.s['revision']).zfill(3)+'-'+self.s['phase']+'-'+uuid.uuid4().hex[:12]+'.json')
        observation={'source':'local-dom-bridge','observed_at':stamp(),'company':self.job['company'],'groupid':str(self.job['groupid']),'tab_id':self.tab,'tab':before,'tree':tree,'navigation_fingerprint':tag(self.job),'plan_sha256':self.job['plan_sha256'],'not_business_capture':True,'name_text_limit':800,'full_field_text_verified':False,'transport_projection':projected}
        write_json(path,observation);self.s['last_tree']={'path':str(path),'sha256':digest(path)};self.s.setdefault('observations',[]).append(self.s['last_tree']);self.save();return before,tree,all_nodes
    def tick(self):
        scope(self.job)
        if self.s['phase']=='profileRequired':return self.s
        before,tree,all_nodes=bounded_readonly_observation(self,self.observe,'center')
        phase=self.s['phase']
        if phase not in ('account','readAccount'):
            try:identity(tree,self.job['identity'])
            except ValueError as error:
                if str(error)=='account-changed':raise
        if phase in ('account','readAccount'):
            try:identity(tree,self.job['identity'])
            except ValueError as error:
                if str(error)=='account-changed' or phase=='readAccount':raise
                self.click(exact(tree,self.job['identity']['provider']),'hover');self.go('readAccount');return self.s
            self.s['identity_verified_at']=stamp();self.go('menu')
        elif phase=='menu':
            if urlsplit(before['url']).path==CENTER:self.go('profileRequired')
            else:
                try:exact(tree,'违规中心')
                except ValueError as error:
                    # Missing/ambiguous submenu must not trigger a guessed selector.
                    matches=[n for n in all_nodes if n.get('name')=='违规中心']
                    if matches:raise error
                    self.click(exact(tree,'经营保障'));self.go('openCenter');return self.s
                self.go('openCenter')
        elif phase=='openCenter':self.click(exact(tree,'违规中心'));self.go('observeCenter')
        elif phase=='observeCenter':require(urlsplit(before['url']).path==CENTER,'navigation-center-path-unverified');self.go('profileRequired')
        else:raise ValueError('navigation-phase-invalid')
        if self.s['phase']=='profileRequired':
            self.s.update(waiting_for='live-violation-analysis-date-and-pagination-profile',requirements=['actual analysis date control and all-reason total/pagination','independently queried record date filters/unread/all/total/pagination','record stable ID plus full subject/actions/effectiveness/rectification','public detail recommendation separated from internal rules','viewport evidence geometry and all visible row boundaries'],zero_verified=False)
        return self.s

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--job',type=Path);ap.add_argument('--prepare-job',type=Path);ap.add_argument('--plan',type=Path);ap.add_argument('--plan-sha256');ap.add_argument('--identity-receipt',type=Path);ap.add_argument('--receipt-sha256');ap.add_argument('--source-work-order-id');ap.add_argument('--tab-id',type=int);ap.add_argument('--state',type=Path);a=ap.parse_args()
    if a.prepare_job:
        require(a.plan and a.plan_sha256 and a.identity_receipt and a.receipt_sha256 and a.source_work_order_id,'navigation-pinned-inputs-required');require(not a.prepare_job.exists(),'navigation-job-output-exists')
        job=prepare(a.plan,a.plan_sha256,a.identity_receipt,a.receipt_sha256,a.source_work_order_id);write_json(a.prepare_job,job);print(json.dumps({'ok':True,'job':str(a.prepare_job.resolve()),'business_progress_changed':False}));return 0
    require(a.job and a.state,'navigation-job-and-state-required');job=json.loads(a.job.read_text());a.state=a.state.resolve();a.state.parent.mkdir(parents=True,exist_ok=True)
    with a.state.with_name(a.state.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);n=Navigator(job,a.tab_id,a.state)
        try:n.tick();n.save();print(json.dumps(n.s,ensure_ascii=False));return 0
        except Exception as error:n.s['last_error']=str(error);n.save();print(json.dumps({'ok':False,'error':str(error),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as error:print(json.dumps({'ok':False,'error':str(error),'business_progress_changed':False},ensure_ascii=False));raise SystemExit(2)
