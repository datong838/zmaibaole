#!/usr/bin/env python3
"""Reviewed public-DOM governance query capture only; no ingest/send/progress.
Requires explicitly reviewed loaded safety version, pinned original role job.
Unknown intents never replay. Unobserved detail/recommendation stops for review.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,re
from pathlib import Path
import governance_dom as g
import preselected_record_range_recovery as preselected_range
spec=importlib.util.spec_from_file_location('governance_query_navigation',Path(__file__).with_name('bridge-navigation.py'));nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
from urllib.parse import urlsplit
from readonly_tick_snapshot import decode as decode_readonly_scope
def verified_query_job(state,observation,journal_path):
    """Pure replay of a newly pinned query job; no inferred date or browser call."""
    binding=state.get('query_job_binding')
    g.need(isinstance(binding,dict) and binding.get('kind')=='governance-query-job-binding-v1','semantic-zero-query-job-binding-required')
    g.need(set(binding)=={'kind','job','fingerprint','tab_id','query_state_path','window_id'},'semantic-zero-query-binding-shape')
    ref=binding.get('job');g.need(isinstance(ref,dict) and set(ref)=={'path','sha256'} and Path(ref['path']).is_absolute(),'semantic-zero-query-job-ref-required')
    job=nav.read_pinned(ref['path'],ref['sha256']);nav.scope(job)
    g.need(binding['fingerprint']==state.get('fingerprint')==nav.tag(job) and binding['tab_id']==state.get('tab_id'),'semantic-zero-query-job-fingerprint-conflict')
    g.need(journal_path and binding['query_state_path']==str(Path(journal_path).resolve()),'semantic-zero-query-original-journal-required')
    g.need(type(binding['window_id']) is int and binding['window_id']>0,'semantic-zero-query-window-unverified')
    g.need(observation.get('source')=='local-dom-bridge' and observation.get('tab_id')==state['tab_id'] and isinstance(observation.get('tab'),dict),'semantic-zero-query-observation-required')
    current=nav.context([{'tabs':[observation['tab']]}],state['tab_id'],job['groupid'])
    g.need(current.get('windowId')==binding['window_id'] and urlsplit(current['url']).path==g.RECORDS and observation['tree'].get('url')=='https://life.douyin.com'+g.RECORDS,'semantic-zero-query-route-conflict')
    nav.identity(observation['tree'],job['identity'])
    if preselected_range.FIELD in state:preselected_range.verify_continuation(state,job,journal_path)
    return job


class Runner:
    def __init__(self,job,tab_id,state,approved_version,invoke=None,job_ref=None):
        nav.scope(job);g.need(approved_version==nav.VERSION,'governance-loaded-policy-version-unreviewed');self.job=job;self.tab=tab_id;self.file=Path(state).resolve();self.version=approved_version;self.invoke=invoke or nav.bridge.request;self.plan=g.QueryPlan(job['start'],job['end_exclusive']);self.query_policy_ready=False;self.calendar_policy_ready=False;self.navigation_job_ref=job_ref
        existed=self.file.exists()
        self.s=json.loads(self.file.read_text()) if self.file.exists() else {'fingerprint':nav.tag(job),'tab_id':tab_id,'approved_version':approved_version,'phase':'open-date','calls':[],'pages':[],'observations':[],'business_progress_changed':False,'profile_accepted':False}
        g.need(self.s['fingerprint']==nav.tag(job) and self.s['tab_id']==tab_id and self.s['approved_version']==approved_version,'governance-query-state-scope-conflict')
        if job_ref is not None:
            g.need(isinstance(job_ref,dict) and set(job_ref)=={'path','sha256'} and Path(job_ref['path']).is_absolute() and nav.read_pinned(job_ref['path'],job_ref['sha256'])==job,'governance-query-pinned-job-conflict')
            if not existed:
                self.s['query_job_binding']={'kind':'governance-query-job-binding-v1','job':job_ref,'fingerprint':nav.tag(job),'tab_id':tab_id,'query_state_path':str(self.file),'window_id':None}
                self.save() # Pin before the first observation or action.
            elif 'query_job_binding' in self.s:
                b=self.s['query_job_binding'];g.need(b.get('job')==job_ref and b.get('fingerprint')==nav.tag(job) and b.get('tab_id')==tab_id and b.get('query_state_path')==str(self.file),'governance-query-original-job-binding-conflict')
            # Legacy journals are never retrofitted, including completed sources.
        if preselected_range.FIELD in self.s:preselected_range.verify_continuation(self.s,self.job,self.file)

    def save(self):nav.write_json(self.file,self.s)
    def request(self,c):
        r=self.invoke(c);g.need(r.get('ok') is True,'governance-bridge-request-failed:'+str(r.get('error')));return r['result']
    def observe(self):
        window=self.s.get('query_job_binding',{}).get('window_id')
        if window is None and self.s.get('last_observation'):
            old=self.s['last_observation'];raw=nav.read_pinned(old['path'],old['sha256']);g.need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==self.tab,'governance-query-original-observation-scope');window=nav.context([{'tabs':[raw['tab']]}],self.tab,self.job['groupid']).get('windowId')
        if window is None:
            window=nav.context(self.request({'op':'tabs'}),self.tab,self.job['groupid']).get('windowId')
        g.need(type(window)is int and window>0,'governance-query-original-window-conflict')
        snapshot=decode_readonly_scope(self.request({'op':'readonly-scope','tabId':self.tab,'windowId':window}),self.tab,window)
        before=nav.context(snapshot['before'],self.tab,self.job['groupid']);ping=snapshot['ping'];g.need(ping.get('version')==self.version and ping.get('safety')=='DOM-only','governance-bridge-version-conflict');self.query_policy_ready=ping.get('governance_query_policy')=='observed-dom-20261021-v1';self.calendar_policy_ready=ping.get('governance_calendar_policy')=='date-item-div-v3-single';tree=snapshot['tree'];nav.identity(tree,self.job['identity']);g.nodes(tree);after=nav.context(snapshot['after'],self.tab,self.job['groupid']);g.need(before['url']==after['url'] and before.get('windowId')==after.get('windowId') and tree['url']=='https://life.douyin.com'+urlsplit(after['url']).path,'governance-query-scope-changed')
        for n in g.nodes(tree):g.need(not any(t in n.get('name','') for t in ['扫码登录','风险验证','安全验证','账号异常']),'governance-query-risk-stop')
        if 'query_job_binding' in self.s:
            b=self.s['query_job_binding'];window=after.get('windowId')
            g.need(type(window) is int and window>0 and b.get('window_id') in (None,window),'governance-query-original-window-conflict')
            b['window_id']=window
        folder=self.file.parent/(self.file.stem+'-evidence');folder.mkdir(parents=True,exist_ok=True);number=max([len(self.s['observations'])-1]+[int(p.stem) for p in folder.glob('*.json') if p.stem.isdigit()])+1;path=folder/(str(number).zfill(4)+'.json')
        with path.open('x',encoding='utf-8') as f:json.dump({'source':'local-dom-bridge','observed_at':nav.stamp(),'tab_id':self.tab,'tab':after,'tree':tree,'not_business_capture':True},f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        ref={'path':str(path),'sha256':nav.digest(path)};self.s['observations'].append(ref);self.s['last_observation']=ref;self.save();return tree
    def act(self,command,next_phase,postcondition=None):
        # Current version alone never authorizes absent reviewed query capability.
        g.need(self.query_policy_ready,'governance-query-policy-not-yet-loaded')
        entry={'state':'unknown','command':{**command,'tabId':self.tab},'before':self.s['last_observation'],'intent_at':nav.stamp(),'postcondition':postcondition};self.s['calls'].append(entry);self.save();result=self.request(entry['command']);entry.update(state='confirmed',result=result);self.s['phase']=next_phase;self.s['needs_changed_tree']=self.s['last_observation'];self.save()
    def await_ready(self,tree):
        """Only confirmed actions get bounded read-only settling. No click retries.
        Scope/identity/version failures are checked by observe() before this method.
        Exhaustion freezes this original journal until supervisor repair.
        """
        if not self.s.get('needs_changed_tree'):return True
        entry=self.s['calls'][-1];g.need(entry['state']=='confirmed','governance-pending-action-not-confirmed')
        previous=nav.read_pinned(entry['before']['path'],entry['before']['sha256'])['tree'];condition=entry.get('postcondition') or {};phase=self.s['phase'];ready=False;reason='governance-confirmed-action-awaiting-public-dom'
        busy=any(n.get('attributes',{}).get('aria-busy')=='true' or n.get('role')=='progressbar' for n in g.nodes(tree))
        try:
            if busy:reason='governance-public-ui-busy'
            elif condition.get('month_delta'):
                before=[v['year']*12+v['month'] for v in g.calendar(previous)];after=[v['year']*12+v['month'] for v in g.calendar(tree)];ready=after==[m+condition['month_delta'] for m in before];reason='governance-month-did-not-advance-exactly-once'
            elif phase=='select-start':g.calendar(tree);ready=True;reason='governance-calendar-not-mounted'
            elif phase=='select-end':
                def calendar_repr(t):
                    panels=[n for n in g.nodes(t) if 'governance_merchant-date-picker-popper' in g.cls(n)];return json.dumps(panels,ensure_ascii=False,sort_keys=True)
                g.calendar(tree);ready=calendar_repr(tree)!=calendar_repr(previous);reason='governance-start-date-selection-not-observed'
            elif phase=='verify-date':
                ready=g.date_value(tree)==self.plan.start+' ~ '+self.plan.end;reason='governance-selected-range-not-confirmed'
                if ready and urlsplit(tree['url']).path==g.CENTER:
                    summary=g.one(g.classnodes(g.root(tree,g.CENTER),'summary-RY8k0Q'),'governance-analysis-summary-not-unique');label=g.text(summary).replace('/','-');ready=self.plan.start in label and self.plan.end in label;reason='governance-analysis-range-not-applied'
            elif condition.get('expected_page'):
                page=g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);ready=page['page']==condition['expected_page'];reason='governance-requested-page-not-observed'
            elif phase in ('next-page','collect-page'):
                page=g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);ready=page['page']==len(self.s['pages'])+1;reason='governance-page-did-not-advance'
            else:ready=tree!=previous
        except ValueError as error:reason=str(error)
        pending=self.s.setdefault('read_only_settling',{'checks':0,'max_checks':5,'original_call_index':len(self.s['calls'])-1})
        g.need(pending['original_call_index']==len(self.s['calls'])-1,'governance-pending-call-binding-changed')
        pending['checks']+=1;pending.update(last_observation=self.s['last_observation'],reason=reason)
        if ready:
            self.s.setdefault('settled_actions',[]).append({**pending,'settled_at':nav.stamp()});self.s.pop('read_only_settling',None);self.s.pop('needs_changed_tree',None);self.s.pop('waiting_for',None);self.s.pop('settling_exhausted',None);self.save();return True
        if pending['checks']>=pending['max_checks']:self.s['waiting_for']='confirmed-action-settling-exhausted-supervisor-reconcile-original-journal';self.s['settling_exhausted']=True
        else:self.s['waiting_for']='confirmed-action-pending-readonly-recheck'
        self.save();return False
    def reconcile_calendar_target(self,expected_state_sha256,expected_last_sha256):
        """Explicit read-only repair of one confirmed, observed no-effect SPAN target.
        Original bytes/call stay intact; this only prepares a new corrected DIV intent.
        """
        nav.scope(self.job);g.need(nav.digest(self.file)==expected_state_sha256,'governance-calendar-repair-original-sha-mismatch')
        g.need(not self.s.get('calendar_target_repair'),'governance-calendar-repair-already-recorded')
        g.need(self.s.get('phase')=='select-end' and self.s.get('settling_exhausted') is True and not self.s.get('pages') and all(c['state']=='confirmed' for c in self.s['calls']),'governance-calendar-repair-original-phase-invalid')
        index=len(self.s['calls'])-1;entry=self.s['calls'][index];pending=self.s.get('read_only_settling',{})
        g.need(pending.get('original_call_index')==index and pending.get('checks')==pending.get('max_checks')==5 and pending.get('reason')=='governance-start-date-selection-not-observed','governance-calendar-repair-not-confirmed-no-effect')
        last=self.s['last_observation'];g.need(last['sha256']==expected_last_sha256 and pending['last_observation']==last,'governance-calendar-repair-last-evidence-mismatch')
        old=nav.read_pinned(last['path'],last['sha256'])['tree'];before=nav.read_pinned(entry['before']['path'],entry['before']['sha256'])['tree']
        def signature(tree):
            return json.dumps([n for n in g.nodes(tree) if 'governance_merchant-date-picker-popper' in g.cls(n)],ensure_ascii=False,sort_keys=True)
        g.need(g.date_value(old)==g.date_value(before) and signature(old)==signature(before),'governance-calendar-repair-old-date-or-calendar-changed')
        target=g.calendar_action(old,self.plan.start);command={**target['action'],'tabId':self.tab};g.need(not target['month_navigation'],'governance-calendar-repair-target-not-current')
        span=g.one([n for n in g.nodes(old) if n.get('selector')==entry['command'].get('locator',{}).get('value')],'governance-calendar-repair-original-target-missing')
        g.need(span.get('tag')=='span' and len(span.get('children',[]))==1 and span['children'][0]['selector']==command['locator']['value'] and entry['command']=={**g.click(span),'tabId':self.tab},'governance-calendar-repair-original-span-not-exact-parent')
        r=entry.get('result',{});g.need(r.get('kind')=='filter' and r.get('version')==self.version and r.get('clicked',{}).get('selector')==span['selector'] and r['clicked'].get('tag')=='span' and r['clicked'].get('name')==self.plan.start[-2:].lstrip('0'),'governance-calendar-repair-original-confirmation-invalid')
        archive=self.file.parent/(self.file.name+'.calendar-target-repair-original-'+expected_state_sha256+'.json');g.need(not archive.exists(),'governance-calendar-repair-archive-already-exists')
        with archive.open('xb') as f:f.write(self.file.read_bytes())
        self.s['calendar_target_repair']={'state':'readonly-verification','kind':'confirmed-span-no-effect-to-date-item-div-v2','original_journal':{'path':str(archive),'sha256':expected_state_sha256},'query_fingerprint':self.s['fingerprint'],'original_call_index':index,'original_call_sha256':hashlib.sha256(json.dumps(entry,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'original_last_observation':last,'corrected_command':command,'old_confirmation_not_claimed_effective':True};self.save()
        fresh=self.observe();g.need(self.calendar_policy_ready,'governance-calendar-corrected-policy-not-loaded')
        g.need(g.date_value(fresh)==g.date_value(old) and signature(fresh)==signature(old),'governance-calendar-repair-fresh-date-or-calendar-changed')
        fresh_target=g.calendar_action(fresh,self.plan.start);g.need({**fresh_target['action'],'tabId':self.tab}==command and not fresh_target['month_navigation'],'governance-calendar-repair-fresh-target-changed')
        self.s['calendar_target_repair'].update(state='corrected-target-ready',verified_at=nav.stamp(),fresh_observation=self.s['last_observation']);self.s['phase']='select-start'
        for k in ('settling_exhausted','read_only_settling','waiting_for','needs_changed_tree'):self.s.pop(k,None)
        self.save();return self.s

    def reconcile_selected_single_start(self,expected_state_sha256,expected_last_sha256):
        """Read-only recognition of an effective DIV start click; never reselect start."""
        nav.scope(self.job);g.need(nav.digest(self.file)==expected_state_sha256,'governance-single-state-repair-original-sha-mismatch')
        g.need(not self.s.get('selected_single_start_repair'),'governance-single-state-repair-already-recorded')
        g.need(self.s.get('phase')=='select-end' and self.s.get('settling_exhausted') is True and not self.s.get('pages') and all(c['state']=='confirmed' for c in self.s['calls']),'governance-single-state-repair-original-phase-invalid')
        index=len(self.s['calls'])-1;entry=self.s['calls'][index];pending=self.s.get('read_only_settling',{});last=self.s['last_observation']
        g.need(pending.get('original_call_index')==index and pending.get('checks')==pending.get('max_checks')==5 and pending.get('reason')=='governance-calendar-date-item-invalid' and last['sha256']==expected_last_sha256 and pending['last_observation']==last,'governance-single-state-repair-original-evidence-mismatch')
        old=nav.read_pinned(last['path'],last['sha256'])['tree'];before=nav.read_pinned(entry['before']['path'],entry['before']['sha256'])['tree'];target=g.calendar_action(before,self.plan.start)
        command={**target['action'],'tabId':self.tab};g.need(not target['month_navigation'] and entry['command']==command,'governance-single-state-repair-original-start-div-mismatch')
        result=entry.get('result',{});item=result.get('clicked',{});g.need(result.get('kind')=='filter' and result.get('version')==self.version and item.get('tag')=='div' and item.get('selector')==command['locator']['value'] and item.get('name')==str(int(self.plan.start[-2:])) and 'governance_merchant-date-item' in g.cls(item) and 'governance_merchant-date-selected' not in g.cls(item),'governance-single-state-repair-original-confirmation-invalid')
        def selected_start(tree):
            views=g.calendar(tree);selected=[(day,node) for v in views for day,node in v['cells'].items() if 'governance_merchant-date-selected' in g.cls(node)];g.need(len(selected)==1 and selected[0][0]==self.plan.start and selected[0][1]['selector']==command['locator']['value'] and 'governance_merchant-date-state-single' in g.cls(selected[0][1]),'governance-single-state-repair-start-not-sole-single')
            panels=[n for n in g.nodes(tree) if 'governance_merchant-date-picker-popper' in g.cls(n)];g.need(not any({'governance_merchant-date-state-end','governance_merchant-date-state-start'}&g.cls(n) for p in panels for n in g.walk(p)),'governance-single-state-repair-end-or-range-already-selected')
            parent=g.one([n for p in panels for n in g.walk(p) if n.get('tag')=='span' and len(n.get('children',[]))==1 and n['children'][0]['selector']==command['locator']['value']],'governance-single-state-repair-parent-missing');g.need({'governance_merchant-date-selected','governance_merchant-date-state-single'}<=g.cls(parent),'governance-single-state-repair-parent-not-single')
            return json.dumps(panels,ensure_ascii=False,sort_keys=True)
        oldsignature=selected_start(old);g.need(g.date_value(old)==g.date_value(before),'governance-single-state-repair-input-committed-or-changed')
        archive=self.file.parent/(self.file.name+'.selected-single-start-repair-original-'+expected_state_sha256+'.json');g.need(not archive.exists(),'governance-single-state-repair-archive-already-exists')
        with archive.open('xb') as f:f.write(self.file.read_bytes())
        self.s['selected_single_start_repair']={'state':'readonly-verification','kind':'recognize-effective-start-div-state-single','original_journal':{'path':str(archive),'sha256':expected_state_sha256},'query_fingerprint':self.s['fingerprint'],'original_call_index':index,'original_last_observation':last,'effective_start_command':command,'start_will_not_be_reclicked':True};self.save()
        fresh=self.observe();g.need(self.calendar_policy_ready,'governance-calendar-single-policy-not-loaded');g.need(g.date_value(fresh)==g.date_value(old) and selected_start(fresh)==oldsignature,'governance-single-state-repair-fresh-selection-or-date-changed')
        self.s['selected_single_start_repair'].update(state='effective-start-verified-continue-select-end',fresh_observation=self.s['last_observation'],verified_at=nav.stamp());self.s.setdefault('settled_actions',[]).append({**pending,'reconciled_as':'effective-start-date-single','settled_at':nav.stamp()})
        for k in ('settling_exhausted','read_only_settling','waiting_for','needs_changed_tree'):self.s.pop(k,None)
        self.save();return self.s

    def reconcile_records_zero(self,expected_state_sha256,expected_last_sha256):
        """Read only: recognize the original query's explicit empty result, never query again."""
        nav.scope(self.job);archive=self.file.parent/(self.file.name+'.records-zero-original-'+expected_state_sha256+'.json');existing=self.s.get('records_zero_reconciliation')
        if existing:
            g.need(existing.get('kind')=='confirmed-query-explicit-empty-readonly-v1' and existing.get('state') in ('pending-readonly','explicit-empty-query-result-verified') and existing.get('original_journal')=={'path':str(archive),'sha256':expected_state_sha256},'governance-zero-repair-original-audit-mismatch')
            original=nav.read_pinned(archive,expected_state_sha256)
            g.need(self.s['calls']==original['calls'] and all(self.s.get(k)==original.get(k) for k in ('fingerprint','tab_id','approved_version','business_progress_changed')),'governance-zero-repair-original-binding-changed')
            g.need(self.s.get('phase')==('capture-complete' if existing['state']=='explicit-empty-query-result-verified' else 'collect-page'),'governance-zero-repair-resume-phase-invalid')
        else:
            g.need(nav.digest(self.file)==expected_state_sha256,'governance-zero-repair-original-sha-mismatch');original=json.loads(self.file.read_text())
        g.need(original.get('phase')=='collect-page' and original.get('settling_exhausted') is True and not original.get('pages') and original.get('calls') and all(c.get('state')=='confirmed' for c in original['calls']),'governance-zero-repair-original-phase-invalid')
        pending=original.get('read_only_settling',{});last=original['last_observation'];index=len(original['calls'])-1;entry=original['calls'][index]
        g.need(pending.get('checks')==pending.get('max_checks')==5 and pending.get('original_call_index')==index and pending.get('reason')=='governance-all-tab-not-unique' and pending.get('last_observation')==last and last['sha256']==expected_last_sha256,'governance-zero-repair-original-evidence-mismatch')
        old=nav.read_pinned(last['path'],last['sha256']);before=nav.read_pinned(entry['before']['path'],entry['before']['sha256'])
        def checked(raw):
            g.need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==self.tab,'governance-zero-repair-source-conflict');tab=nav.context([{'tabs':[raw['tab']]}],self.tab,self.job['groupid']);g.need(urlsplit(tab['url']).path==g.RECORDS and raw['tree'].get('url')=='https://life.douyin.com'+g.RECORDS,'governance-zero-repair-route-conflict');g.nodes(raw['tree']);nav.identity(raw['tree'],self.job['identity']);return tab
        tab=checked(old);g.need(checked(before).get('windowId')==tab.get('windowId'),'governance-zero-repair-window-conflict')
        command={**self.plan.next(before['tree'],{'phase':'verify-date'})['command'],'tabId':self.tab};g.need(command==entry['command'],'governance-zero-repair-original-query-command-mismatch')
        target=g.one([n for n in g.nodes(before['tree']) if n.get('selector')==command['locator']['value']],'governance-zero-repair-query-target-missing');result=entry.get('result',{});clicked=result.get('clicked',{})
        g.need(result.get('kind')=='filter' and result.get('version')==self.version and all(clicked.get(k)==target.get(k) for k in ('selector','tag','name','attributes')) and clicked.get('disabled') is not True,'governance-zero-repair-query-reply-invalid')
        original_page=g.records_page(old['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(original_page.get('empty_result',{}).get('schema')=='governance-records-explicit-empty-v1','governance-zero-repair-not-explicit-empty')
        if existing and existing['state']=='explicit-empty-query-result-verified':
            fresh_raw=nav.read_pinned(existing['fresh_observation']['path'],existing['fresh_observation']['sha256']);g.need(checked(fresh_raw).get('windowId')==tab.get('windowId'),'governance-zero-repair-fresh-window-conflict')
            page=g.records_page(fresh_raw['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(page==original_page and self.s.get('pages')==[{**page,'observation':existing['fresh_observation']}] and self.s.get('rows')==[],'governance-zero-repair-completed-result-changed');return self.s
        if not existing:
            if archive.exists():g.need(archive.read_bytes()==self.file.read_bytes() and nav.digest(archive)==expected_state_sha256,'governance-zero-repair-existing-archive-conflict')
            else:
                with archive.open('xb') as f:f.write(self.file.read_bytes());f.flush();os.fsync(f.fileno())
            audit={'kind':'confirmed-query-explicit-empty-readonly-v1','state':'pending-readonly','original_journal':{'path':str(archive),'sha256':expected_state_sha256},'original_call_index':index,'original_last_observation':last,'query_will_not_be_reclicked':True}
            self.s['records_zero_reconciliation']=audit;self.save()
        else:
            audit=existing;g.need(audit.get('original_call_index')==index and audit.get('original_last_observation')==last,'governance-zero-repair-original-audit-binding-changed')
        fresh=self.observe();fresh_raw=nav.read_pinned(self.s['last_observation']['path'],self.s['last_observation']['sha256']);g.need(checked(fresh_raw).get('windowId')==tab.get('windowId'),'governance-zero-repair-fresh-window-conflict')
        page=g.records_page(fresh,start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(page==original_page,'governance-zero-repair-fresh-result-changed')
        audit.update(fresh_observation=self.s['last_observation'],verified_at=nav.stamp(),state='explicit-empty-query-result-verified')
        page['observation']=self.s['last_observation'];self.s['pages']=[page];self.s['rows']=g.complete_pages(self.s['pages']);self.s.setdefault('settled_actions',[]).append({**pending,'reconciled_as':'explicit-empty-records-result','settled_at':nav.stamp()})
        for k in ('settling_exhausted','read_only_settling','waiting_for','needs_changed_tree'):self.s.pop(k,None)
        self.s.update(phase='capture-complete',waiting_for='independent-analysis-zero-and-source-verification-required',records_zero_verified=True,zero_verified=False);self.save();return self.s

    def step(self):
        nav.scope(self.job)
        if self.s['phase'] in ('profile-required','capture-complete'):return self.s
        if self.s.get('settling_exhausted'):
            if self.s['phase']!='collect-page':return self.s
            g.need(all(c.get('state')=='confirmed'for c in self.s['calls']),'governance-settled-read-unresolved-input')
            fresh=self.observe()
            if not self.await_ready(fresh):
                if self.s.get('read_only_settling',{}).get('reason')=='governance-row-before-range' and not self.s.get('stale_query_refreshed') and not self.s.get('pages'):
                    entry=self.s['calls'][-1];before=nav.read_pinned(entry['before']['path'],entry['before']['sha256'])['tree']
                    def projection(tree):
                        table=g.one([n for n in g.nodes(tree)if n.get('tag')=='table'and 'governance_merchant-Table-Implement'in g.cls(n)],'governance-stale-table')
                        result=[]
                        for row in g.walk(table):
                            cells=[n for n in row.get('children',[])if n.get('tag')=='td'and n.get('role')=='cell']
                            if not cells:continue
                            g.need(len(cells)==len(g.HEADERS),'governance-stale-row-shape')
                            match=re.search(r'ID:\s*([A-Za-z0-9_-]+)',g.text(cells[0]));g.need(match,'governance-stale-row-id');result.append((match[1],g.text(cells[5])))
                        return result
                    g.need(projection(before)==projection(fresh) and g.date_value(fresh)==self.plan.start+' ~ '+self.plan.end,'governance-stale-query-current-scope')
                    command=self.plan.next(fresh,{'phase':'verify-date'})['command'];g.need({**command,'tabId':self.tab}==entry['command'],'governance-stale-query-target-changed')
                    self.s['stale_query_refreshed']={'original_call_index':len(self.s['calls'])-1,'observation':self.s['last_observation']}
                    for key in ('settling_exhausted','read_only_settling','waiting_for','needs_changed_tree'):self.s.pop(key,None)
                    self.act(command,'collect-page');return self.s
                return self.s
        if any(c['state']=='unknown' for c in self.s['calls']):self.s['waiting_for']='original-unknown-intent-no-replay';self.save();return self.s
        tree=self.observe()
        if not self.await_ready(tree):return self.s
        if type(self) is Runner and self.s['phase']=='open-date':
            import center_analysis_tab
            try:
                if not center_analysis_tab.ensure_query_analysis(self,tree):return self.s
            except ValueError as error:
                if str(error) not in ('analysis-original-layout-intent-unknown','analysis-preflight-original-analysis-unknown'):raise
                self.s['waiting_for']=str(error);self.save();return self.s
        if self.s['phase']=='next-page':self.s['phase']='collect-page'
        if self.s['phase']=='page-collected':
            previous=self.s['pages'][-1];g.need(not previous['next']['disabled'],'governance-completed-page-reconcile-required');self.act(previous['next']['command'],'next-page');return self.s
        result=self.plan.next(tree,self.s)
        if result.get('command'):
            if result.get('selected_date'):g.need(self.calendar_policy_ready,'governance-calendar-corrected-policy-not-loaded')
            self.act(result['command'],result['next_phase'],{'month_delta':result.get('expected_month_delta')} if result.get('month_navigation') else None);return self.s
        if result.get('page'):
            page=result['page'];g.need(page['page']==len(self.s['pages'])+1,'governance-page-order-conflict');page['observation']=self.s['last_observation'];self.s['pages'].append(page);self.s['phase']='page-collected';self.save()
            if page['next']['disabled']:
                self.s['rows']=g.complete_pages(self.s['pages']);self.s.update(phase='capture-complete',waiting_for='readonly-detail-profile-and-analysis-full-distribution-required',zero_verified=False);self.save();return self.s
            self.act(page['next']['command'],'next-page');return self.s
        self.s.update(phase='profile-required',waiting_for=result.get('hold','review-required'));self.save();return self.s

class DetailProbe(Runner):
    """One exact current-page notice, then complete raw detail tree and HOLD.
    Public advice selectors are still unobserved and must not be invented.
    """
    def __init__(self,job,tab_id,state,approved_version,notice_id,invoke=None,query_ref=None):
        existed=Path(state).exists();super().__init__(job,tab_id,state,approved_version,invoke)
        g.need(isinstance(notice_id,str) and __import__('re').fullmatch(r'[A-Za-z0-9_-]+',notice_id),'governance-detail-notice-invalid')
        if existed:g.need(self.s.get('detail_notice_id')==notice_id,'governance-detail-notice-binding-changed')
        else:self.s.update(phase='inspect-detail',detail_notice_id=notice_id,query_ref=query_ref)
        g.need(self.s.get('query_ref')==query_ref,'governance-detail-query-reference-changed')
    def step(self):
        nav.scope(self.job)
        if self.s['phase']=='profile-required':return self.s
        if any(c['state']=='unknown' for c in self.s['calls']):self.s['waiting_for']='original-unknown-intent-no-replay';self.save();return self.s
        tree=self.observe()
        if self.s['phase']=='observe-detail':
            self.s.update(phase='profile-required',waiting_for='review-observed-detail-public-recommendation-and-return-route',detail_open_verified=False,advice_extracted=False);self.save();return self.s
        if self.s['phase']=='goto-detail-page':
            if not self.await_ready(tree):return self.s
            self.s['phase']='inspect-detail'
        g.need(self.s['phase']=='inspect-detail','governance-detail-phase-invalid')
        current=g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive'])
        if not any(r['notice_id']==self.s['detail_notice_id'] for r in current['rows']):
            ref=self.s.get('query_ref');g.need(isinstance(ref,dict),'governance-detail-not-on-current-page-query-reference-required')
            query=nav.read_pinned(ref['path'],ref['sha256']);g.need(query.get('phase')=='capture-complete' and query.get('fingerprint')==nav.tag(self.job) and query.get('tab_id')==self.tab and query.get('approved_version')==self.version,'governance-detail-original-query-scope-conflict')
            full=g.complete_pages(query['pages']);g.need(full==query['rows'],'governance-detail-original-query-rows-changed');pages=[p['page'] for p in query['pages'] if any(r['notice_id']==self.s['detail_notice_id'] for r in p['rows'])];target=g.one(pages,'governance-detail-notice-not-in-captured-query')
            pager=g.one(g.classnodes(g.root(tree,g.RECORDS),'governance_merchant-pager'),'governance-detail-return-pager-not-unique');button=g.one([n for n in g.walk(pager) if n.get('tag')=='li' and 'governance_merchant-pager-item' in g.cls(n) and g.text(n)==str(target)],'governance-detail-return-page-not-observed');g.need(not ({'governance_merchant-pager-item-disabled','governance_merchant-pager-item-checked'}&g.cls(button)),'governance-detail-return-page-unavailable');self.act(g.click(button,'navigation'),'goto-detail-page',{'expected_page':target});return self.s
        command=g.detail_action(tree,self.s['detail_notice_id'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);self.act(command,'observe-detail');return self.s

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',type=Path,required=True);p.add_argument('--tab-id',type=int,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--approved-version',required=True);p.add_argument('--detail-notice-id');p.add_argument('--first-detail-from-query',action='store_true');p.add_argument('--query-state',type=Path);p.add_argument('--query-state-sha256');p.add_argument('--reconcile-confirmed-calendar-no-effect',action='store_true');p.add_argument('--reconcile-selected-single-start',action='store_true');p.add_argument('--reconcile-records-zero',action='store_true');p.add_argument('--expected-state-sha256');p.add_argument('--expected-last-observation-sha256');a=p.parse_args();a.state.parent.mkdir(parents=True,exist_ok=True)
    if a.first_detail_from_query:
        g.need(a.query_state and a.query_state_sha256 and not a.detail_notice_id,'governance-first-detail-pinned-query-required');query=nav.read_pinned(a.query_state,a.query_state_sha256);g.need(query.get('phase')=='capture-complete' and bool(query.get('rows')),'governance-first-detail-no-complete-nonempty-query');a.detail_notice_id=query['rows'][0]['notice_id']
    with a.state.with_name(a.state.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);job_raw=a.job.read_bytes();job=json.loads(job_raw);job_ref={'path':str(a.job.resolve()),'sha256':hashlib.sha256(job_raw).hexdigest()};r=DetailProbe(job,a.tab_id,a.state,a.approved_version,a.detail_notice_id,query_ref={'path':str(a.query_state.resolve()),'sha256':a.query_state_sha256} if a.query_state and a.query_state_sha256 else None) if a.detail_notice_id else Runner(job,a.tab_id,a.state,a.approved_version,job_ref=job_ref)
        try:
            g.need(sum((a.reconcile_confirmed_calendar_no_effect,a.reconcile_selected_single_start,a.reconcile_records_zero))<=1,'governance-calendar-repair-modes-conflict')
            if a.reconcile_records_zero:
                g.need(not a.detail_notice_id and not a.first_detail_from_query and a.expected_state_sha256 and a.expected_last_observation_sha256,'governance-zero-repair-explicit-shas-required');r.reconcile_records_zero(a.expected_state_sha256,a.expected_last_observation_sha256)
            elif a.reconcile_selected_single_start:
                g.need(not a.detail_notice_id and not a.first_detail_from_query and a.expected_state_sha256 and a.expected_last_observation_sha256,'governance-single-state-repair-explicit-shas-required');r.reconcile_selected_single_start(a.expected_state_sha256,a.expected_last_observation_sha256)
            elif a.reconcile_confirmed_calendar_no_effect:
                g.need(not a.detail_notice_id and not a.first_detail_from_query and a.expected_state_sha256 and a.expected_last_observation_sha256,'governance-calendar-repair-explicit-shas-required');r.reconcile_calendar_target(a.expected_state_sha256,a.expected_last_observation_sha256)
            else:r.step()
            r.save();print(json.dumps({'phase':r.s['phase'],'waiting_for':r.s.get('waiting_for'),'business_progress_changed':False,'state_path':str(r.file),'state_sha256':nav.digest(r.file)},ensure_ascii=False))
        except Exception as e:r.s['last_error']=str(e);r.save();raise
if __name__=='__main__':
    try:main()
    except Exception as e:print(json.dumps({'ok':False,'error':str(e),'business_progress_changed':False},ensure_ascii=False));raise SystemExit(2)
