"""Durable activation of the original management tab before review-region capture.
No new tab, URL navigation, account hover, pixels or sender actions.
"""
import argparse,copy,fcntl,importlib.util,json,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qsl
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/workshop-director/scripts'),str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import complaint_execution_order as o
import initial_ledger_recovery as h
import review_frames_preinput_recovery as previous
import account_overlay_preflight as overlay
FIELD='review_capture_tab_recovery';KIND='verified-review-capture-tab-preinput-recovery-v1';ERROR='overlay-tab-scope-conflict'
def stamp():return datetime.now(timezone.utc).isoformat()
def operator_primitives():
    name='complaint_parent_operator_api';path=ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'
    if name in sys.modules:
        m=sys.modules[name];o.need(Path(m.__file__).resolve()==path,'review-tab-operator-origin');return m.Workflow
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m.Workflow

def derive(manifest_ref):
    manifest=overlay.document(manifest_ref)
    base,source,scope,url=overlay.derive(manifest)
    job=overlay.document(manifest['job'])
    receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']}
    # The joined current page owns the capture tab. An export-record tab or
    # download workflow is unrelated to a current review screenshot.
    return {'manifest':manifest_ref,'source':manifest['source'],'identity':source['identity'],'scope':scope,'url':url,'original_record_tab':{'tabId':-1,'windowId':scope['windowId'],'url':'not-eligible-for-focus-restore'},'acquisition':receipt_ref}

def derive_recheck(inputs):
    import normal_observation as normal
    o.need(set(inputs)=={'job','source','profile','envelope'},'recheck-tab-exact-source-refs')
    job,source,profile,envelope=[o.doc(inputs[k]) for k in ('job','source','profile','envelope')]
    o.need(normal.joined(job,envelope,profile,job['source_receipt'],job['source_receipt_sha256'])==source,'recheck-tab-original-source-join')
    tab=envelope['pages'][0]['tab'];normal.context(envelope['pages'][0],job['groupid'])
    o.need(all(all(p['tab'].get(k)==tab[k] for k in ('tabId','windowId','url')) for p in envelope['pages']),'recheck-tab-original-pages-scope')
    receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']}
    return {'inputs':inputs,'identity':source['identity'],'scope':{'tabId':tab['tabId'],'windowId':tab['windowId'],'groupid':source['groupid']},'url':tab['url'],'original_record_tab':{'tabId':-1,'windowId':tab['windowId'],'url':'not-eligible-for-focus-restore'},'acquisition':receipt_ref}

def ensure_recheck(inputs,*,request=None,readonly=False):
    """One durable existing-tab activation per pinned normal source, never a click.
    A confirmed activation followed by later loss remains HOLD; unknown only reads.
    """
    binding=derive_recheck(inputs);directory=Path(inputs['source']['path']).parent/'.review-recheck-tab-activation';directory.mkdir(exist_ok=True);o.canonical(directory);key=o.digest(inputs);path=directory/(key+'.json');request=request or overlay.bridge.request
    with (directory/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=o.doc(o.ref(path)) if path.exists() else {'kind':'review-recheck-source-tab-activation-v1','binding':binding,'phase':'recheck-source','revision':0,'state':'preflight','calls':[],'reads':[],'created_at':stamp()}
        o.need(state.get('kind')=='review-recheck-source-tab-activation-v1' and state['binding']==binding and state['state'] in ('preflight','unknown','confirmed','complete') and len(state['calls'])<=1,'recheck-tab-original-binding');attempt=directory/key/uuid.uuid4().hex;attempt.mkdir(parents=True);activation=None
        def raw(command,label):
            o.need(derive_recheck(inputs)==binding,'recheck-tab-source-changed');o.need(not readonly or command=={'op':'tabs'},'recheck-tab-readonly-capability')
            record={'command':command,'observed_at':stamp()}
            try:record['response']=request(command)
            except Exception as e:
                record['exception']={'type':type(e).__name__,'message':str(e)};state['reads'].append(overlay.immutable(attempt/(str(len(state['reads'])).zfill(3)+'-'+label+'.json'),record));activation.save();raise
            state['reads'].append(overlay.immutable(attempt/(str(len(state['reads'])).zfill(3)+'-'+label+'.json'),record));activation.save();return record['response']
        activation=Activation(path,state,request,raw);activation.save();reply=raw({'op':'tabs'},'before');o.need(reply.get('ok') is True,'recheck-tab-tabs-failed');status=classify(reply['result'],binding);calls=state['calls'];dispatched=False
        o.need(state['state']!='unknown' or calls,'recheck-tab-unknown-without-intent')
        if calls:
            c=calls[0];o.need(c['key']=='original-management-tab-once' and c['phase']=='recheck-source' and c['command']=={'op':'activate','tabId':binding['scope']['tabId']} and c['state'] in ('unknown','confirmed'),'recheck-tab-original-intent');o.need(status=='active','recheck-tab-outcome-unknown-no-replay')
            if c['state']=='unknown':c.update(state='confirmed',result={**{k:binding['scope'][k] for k in ('tabId','windowId')},'url':binding['url'],'active':True,'windowFocused':True,'observed':True});state['reconciled_readonly_at']=stamp();activation.save()
        elif status!='active':
            o.need(not readonly,'recheck-tab-readonly-effect-not-observed');dispatched=True;result=activation.once({'op':'activate','tabId':binding['scope']['tabId']});o.need(all(result.get(k)==v for k,v in {**{k:binding['scope'][k] for k in ('tabId','windowId')},'url':binding['url'],'active':True,'windowFocused':True}.items()),'recheck-tab-result-scope');state['state']='confirmed';activation.save();reply=raw({'op':'tabs'},'after');o.need(reply.get('ok') is True and classify(reply['result'],binding)=='active','recheck-tab-fresh-effect-unverified')
        o.need(derive_recheck(inputs)==binding,'recheck-tab-source-changed');state.update(state='complete',completed_at=stamp());activation.save()
        return {'ready':True,'journal':o.ref(path),'input_attempted':dispatched,'qualification':'source-tab-only-recheck-still-requires-fresh-identity-and-active-scope'}

def classify(tabs,binding):
    scope=binding['scope'];matches=[(w,t) for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==scope['tabId']];o.need(len(matches)==1,'review-tab-target-not-unique');window,target=matches[0]
    o.need(window.get('windowId')==target.get('windowId')==scope['windowId'] and target.get('allowed') is True and target.get('url')==binding['url'],'review-tab-original-target-changed')
    focused=[w for w in tabs if w.get('focused') is True];o.need(len(focused)<=1 and type(window.get('focused')) is bool,'review-tab-window-focus-unknown-or-ambiguous')
    o.need(all(len([t for t in w.get('tabs',[]) if t.get('active') is True])==1 for w in tabs),'review-tab-window-active-not-unique')
    active=[t for t in window.get('tabs',[]) if t.get('active') is True];o.need(len(active)==1,'review-tab-active-not-unique')
    if active[0] is target:return 'active' if window['focused'] else 'target-active-window-unfocused'
    record=binding['original_record_tab'];record_matches=all(active[0].get(k)==record[k] for k in ('windowId','url'))
    if record.get('tabId')==-1:
        current=urlsplit(active[0].get('url',''));query=dict(parse_qsl(current.query))
        record_matches=current.scheme=='https' and current.netloc=='life.douyin.com' and current.path.startswith('/p/fulfillsettle/export_records/') and query.get('groupid')==str(scope['groupid'])
    o.need(record_matches and active[0].get('allowed') is True,'review-tab-active-not-original-record-page');return 'original-record-active' if window['focused'] else 'original-record-active-window-unfocused'

class Activation:
    def __init__(self,path,state,request,raw):self.path=path;self.s=state;self.request=request;self.raw=raw
    def save(self):overlay.rc.atomic(self.path,self.s)
    def call(self,command):
        o.need(command=={'op':'activate','tabId':self.s['binding']['scope']['tabId']},'review-tab-only-original-activate');response=self.raw(command,'activate');o.need(response.get('ok') is True,'review-tab-activate-failed');return response['result']
    def once(self,command):return operator_primitives().once(self,command,intent_key='original-management-tab-once')

def ensure(manifest_ref,*,request=None,readonly=False,pid=None):
    binding=derive(manifest_ref);manifest=overlay.document(manifest_ref);directory=Path(manifest['source']['path']).parent/'.review-tab-activation';directory.mkdir(exist_ok=True);o.canonical(directory);key=overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});path=directory/(key+'.json');request=request or overlay.bridge.request
    with (directory/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);overlay.no_capture_unknown(Path(manifest['source']['path']))
        state=overlay.document(overlay.ref(path)) if path.exists() else {'kind':'review-capture-tab-activation-v1','binding':binding,'phase':'frames','revision':0,'state':'preflight','calls':[],'reads':[],'created_at':stamp()};o.need(state['kind']=='review-capture-tab-activation-v1' and state['binding']==binding and state['state'] in ('preflight','unknown','confirmed','complete'),'review-tab-original-binding')
        if pid is not None and state['state']=='complete' and len(state['calls'])<=1 and all(c.get('state')=='confirmed' for c in state['calls']):
            import review_capture_focus
            return review_capture_focus.ensure(manifest_ref,activation_ref=overlay.ref(path),pid=pid,request=request,readonly=readonly)
        attempt=uuid.uuid4().hex;folder=directory/key/attempt;folder.mkdir(parents=True);activation=None
        def raw(command,label):
            o.need(derive(manifest_ref)==binding,'review-tab-inputs-changed')
            try:response=request(command)
            except Exception as e:
                ref=overlay.immutable(folder/(str(len(state['reads'])).zfill(3)+'-'+label+'-exception.json'),{'command':command,'exception':{'type':type(e).__name__,'message':str(e)},'observed_at':stamp()});state['reads'].append(ref);activation.save();raise
            ref=overlay.immutable(folder/(str(len(state['reads'])).zfill(3)+'-'+label+'.json'),{'command':command,'response':response,'observed_at':stamp()});state['reads'].append(ref);activation.save();return response
        activation=Activation(path,state,request,raw);activation.save();reply=raw({'op':'tabs'},'before-tabs');o.need(reply.get('ok') is True,'review-tab-tabs-failed');status=classify(reply['result'],binding);dispatched=False
        o.need(len(state['calls'])<=1,'review-tab-extra-intent');calls=state['calls'];o.need(state['state']!='unknown' or bool(calls),'review-tab-unknown-without-original-intent')
        if calls:
            call=calls[0];o.need(call['key']=='original-management-tab-once' and call['phase']=='frames' and call['command']=={'op':'activate','tabId':binding['scope']['tabId']} and call['state'] in ('unknown','confirmed'),'review-tab-original-intent')
            o.need(status=='active','review-tab-outcome-unknown-no-replay')
            if call['state']=='unknown':call.update(state='confirmed',result={'observed':True,'tabId':binding['scope']['tabId'],'windowId':binding['scope']['windowId'],'url':binding['url'],'active':True,'windowFocused':True});state['reconciled_readonly_at']=stamp();activation.save()
        elif status!='active':
            o.need(not readonly,'review-tab-readonly-effect-not-observed');dispatched=True;result=activation.once({'op':'activate','tabId':binding['scope']['tabId']});o.need(all(result.get(k)==v for k,v in {**{k:binding['scope'][k] for k in ('tabId','windowId')},'url':binding['url']}.items()),'review-tab-activate-result-scope');state['state']='confirmed';activation.save()
            reply=raw({'op':'tabs'},'after-tabs');o.need(reply.get('ok') is True and classify(reply['result'],binding)=='active','review-tab-active-effect-unverified')
        o.need(derive(manifest_ref)==binding,'review-tab-inputs-changed');state.update(state='complete',completed_at=stamp(),qualification='original-tab-active-only-not-screenshot-proof');activation.save()
        if pid is not None:
            import review_capture_focus
            return review_capture_focus.ensure(manifest_ref,activation_ref=overlay.ref(path),pid=pid,request=request,readonly=readonly)
        return {'ready':True,'journal':overlay.ref(path),'activation_dispatched_this_call':dispatched,'activation_intent_exists':bool(calls),'full_account_rechecked':False,'next_guard':'original-overlay-fresh-scope-and-identity'}

def paths():return {n:str(ROOT/'skills/negative-review-complaints/scripts'/n) for n in ('capture_review_region.py','initial_ledger_recovery.py','review_frames_preinput_recovery.py','review_capture_tab.py')}
def source_tip(parent,release_ref,old_refs,*,installed,extra_source_archives=()):
    release=o.doc(release_ref);ps=paths();targets=release['targets'];old={Path(r['path']).name:r for r in old_refs}
    o.need(release['kind']=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(ps.values()) and all(t['mode']=='0644' for t in targets),'review-tab-exact-four-target-release')
    o.need(len(old_refs)==3 and set(old)=={n+'.before' for n in ps if n!='review_capture_tab.py'},'review-tab-exact-three-archives');archives=[]
    for name in ps:
        if name=='review_capture_tab.py':continue
        t=next(t for t in targets if t['target']==ps[name]);ref=old[name+'.before'];o.need(ref['sha256']==t['old_sha256'],'review-tab-release-old-binding');o.raw(ref);archives.append({'target':t['target'],'archive':ref})
    original=o.doc(o.doc(parent[FIELD])['parent_archive']) if parent.get(FIELD) else parent
    prior=previous.verify_recovered(original,original[previous.FIELD],installed=False,extra_source_archives=[*[x for x in archives if x['target']==ps['capture_review_region.py']],*extra_source_archives]);codes=copy.deepcopy(prior['code_refs']);by_path={r['path']:r for r in codes}
    for t in targets:
        o.raw(t['after']);new={'path':t['target'],'sha256':t['after']['sha256']}
        if t['target']==ps['review_capture_tab.py']:o.need(t['old_sha256'] is None and t['target'] not in by_path,'review-tab-new-helper-only');codes.append(new)
        else:
            before=by_path[t['target']];o.need(before['sha256']==t['old_sha256'],'review-tab-admission-base');codes[codes.index(before)]=new
    if installed:
        for ref in codes:o.raw(ref)
        for path in ps.values():o.need(Path(path).stat().st_mode & 0o777==0o644,'review-tab-installed-mode')
    return prior,codes,archives

def overlay_failure(parent,overlay_ref,manifest_ref,*,archived_state=None):
    state=o.doc(overlay_ref) if archived_state is None else archived_state;manifest=o.doc(manifest_ref);base,source,scope,url=overlay.derive(manifest);binding={'source':manifest['source'],'job':manifest['job'],'profile':manifest['profile'],'envelope':manifest['envelope'],'identity':source['identity'],'scope':scope,'url':url,'content':overlay.content_identity()};key=overlay.rc.digest({'source_sha256':manifest['source']['sha256'],**scope,'identity':source['identity']});directory=overlay.RUNTIME
    o.need(Path(overlay_ref['path'])==directory/(key+'.json') and state['kind']=='review-account-overlay-preflight-v1' and state['binding']==binding and state['state']=='preflight' and not any(k in state for k in ('command','input_intent','intent_at','reply','adopted_intent')) and len(state['attempts'])==1,'review-tab-original-overlay-read-only')
    attempt=state['attempts'][0];o.need(attempt['manifest']==manifest_ref and len(attempt['raw'])==1 and attempt['error']['code']==ERROR,'review-tab-sole-tabs-failure');ref=attempt['raw'][0];o.need(Path(ref['path'])==directory/key/'attempts'/attempt['attempt']/'00-before-tabs-before.json','review-tab-canonical-original-raw');raw=o.doc(ref);o.need(raw['command']=={'op':'tabs'} and raw['response'].get('ok') is True and classify(raw['response']['result'],derive(manifest_ref))=='original-record-active','review-tab-original-inactive-bound-tab')
    if archived_state is None:o.need(not (directory/key/'hover-intent.json').exists(),'review-tab-original-hover-intent-exists')
    return ref

def original_contract(parent,engine,overlay_ref,prior,*,archived_overlay=None):
    p=o.doc(parent[previous.FIELD]);oldp=o.doc(p['parent_archive']);olde=o.doc(p['engine_archive']);ready_p,ready_e=previous.recovered(oldp,olde,parent[previous.FIELD]);folder=o.location(parent['order'])
    o.need(not parent.get(FIELD) and parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==5 and parent['calls'][:4]==prior['failed_calls'] and not parent.get('child') and not parent.get('completion'),'review-tab-exact-original-parent-hold')
    o.need(engine['status']=='hold' and engine.get('error')==ERROR and len(engine['calls'])==45 and engine['calls'][:44]==olde['calls'] and not engine.get(FIELD),'review-tab-exact-original-engine-hold')
    last=engine['calls'][-1];a=engine['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(last['state']=='failed' and last['error']==ERROR and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'review-tab-exact-new-engine-failure')
    expected_p=copy.deepcopy(ready_p);expected_p['calls'].append(parent['calls'][-1]);expected_p.update(status='hold',error='execution-child-stopped');expected_e=copy.deepcopy(ready_e);expected_e['calls'].append(last);expected_e.update(status='hold',error=ERROR)
    o.need(parent==expected_p and engine==expected_e,'review-tab-no-other-progress-delta');manifest_ref=p['manifest'];raw=overlay_failure(parent,overlay_ref,manifest_ref,archived_state=archived_overlay)
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==parent['calls'][3]['argv'] and launch['index']==4 and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':ERROR} and Path(call['launch']['path'])==folder/'children/0004-launch.json' and Path(call['result']['path'])==folder/'children/0004-exit.json','review-tab-original-natural-rc2')
    return {'failed_engine_indices':[0,4,43,44],'failed_calls':parent['calls'],'manifest':manifest_ref,'overlay':overlay_ref,'raw':raw,'activation_binding':derive(manifest_ref),'ledger_current':a['ledger_current']}

def plan(parent_ref,engine_ref,overlay_ref,worker_ref,release_ref,old_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','review-tab-canonical-originals');prior,codes,archives=source_tip(parent,release_ref,old_refs,installed=installed);facts=original_contract(parent,engine,overlay_ref,prior);evidence=previous.worker_evidence(parent,engine_ref,worker_ref)
    return {'kind':KIND,'original_parent':parent_ref,'original_engine':engine_ref,'overlay':overlay_ref,'worker':worker_ref,'release':release_ref,'old_sources':archives,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}
def recovered(parent,engine,proof):
    values=copy.deepcopy((parent,engine))
    for s in values:s.setdefault('resolved_errors',[]).append({'error':s.pop('error'),'recovery':proof});s.update(status='running',**{FIELD:proof})
    return values

def verify_recovered(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref)
    if p.get('kind')=='verified-review-native-preflight-recovery-v1':
        from review_capture_focus import verify_recovered as verified_focus
        return verified_focus(current,proof_ref)
    folder=o.location(current['order']);base=folder/'.review-tab-preinput-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and Path(proof_ref['path'])==base/'proof.json' and current.get(FIELD)==proof_ref and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-tab-canonical-recovery-proof')
    for name in ('parent','engine','overlay'):o.need(Path(p[name+'_archive']['path'])==base/('original-'+name+'.json') and p[name+'_archive']['sha256']==p['original_'+name]['sha256'],'review-tab-archive-binding')
    o.need(all(Path(x['archive']['path'])==base/'sources'/Path(x['archive']['path']).name for x in p['old_sources']),'review-tab-source-archive-path')
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);prior,codes,_=source_tip(parent,p['release'],[x['archive'] for x in p['old_sources']],installed=installed,extra_source_archives=extra_source_archives)
    # Original overlay journal is a mutable read-only retry log. Historical replay
    # uses exactly the archived original body at its original canonical identity.
    facts=original_contract(parent,engine,p['original_overlay'],prior,archived_overlay=o.doc(p['overlay_archive']))
    evidence=previous.worker_evidence(parent,p['original_engine'],p['worker']);expected=recovered(parent,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['worker_evidence']==evidence and p['code_refs']==codes and current['calls'][:5]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.entry.FIELD,previous.FIELD)),'review-tab-preserved-original-proof')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['overlay_archive'],p['release'],*[x['archive'] for x in p['old_sources']],*evidence]}

def verified_engine_calls(engine):
    if o.doc(engine[FIELD]).get('kind')=='verified-review-native-preflight-recovery-v1':
        from review_capture_focus import verified_engine_calls as focus_calls
        return focus_calls(engine)
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'review-tab-parent-engine-proof');verify_recovered(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['calls'][:45]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'review-tab-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]

def no_capture(manifest_ref):
    manifest=o.doc(manifest_ref);unit=Path(manifest['source']['path']).parent
    for directory in (unit/'.review-region-state',unit/'.review-capture-state',unit/'.review-tab-activation'):o.need(not list(directory.glob('*.json')),'review-tab-input-or-capture-already-exists')
    out=Path(manifest_ref['path']).parent/'capture';o.need(not out.exists() or not any(out.iterdir()),'review-tab-capture-artifact-exists')
def recover(parent_ref,engine_ref,overlay_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-tab-preinput-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_overlay':overlay_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted((Path(r['path']).name,r['sha256']) for r in old_refs)==sorted((Path(x['archive']['path']).name,x['archive']['sha256']) for x in p['old_sources']),'review-tab-original-recovery-inputs')
        else:
            p=plan(parent_ref,engine_ref,overlay_ref,worker_ref,release_ref,old_refs,installed=True);p['original_overlay']=p.pop('overlay');no_capture(p['facts']['manifest']);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True);o.canonical(base/'sources')
            for n,r in (('parent',parent_ref),('engine',engine_ref),('overlay',overlay_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            for x in p['old_sources']:x['archive']=h.immutable_bytes(base/'sources'/Path(x['archive']['path']).name,o.raw(x['archive']))
            p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-tab-current-lease')
        previous.current_ledgers(parent,engine);o.raw(overlay_ref);no_capture(p['facts']['manifest']);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe)];verify_recovered(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        previous.current_ledgers(parent,engine);o.raw(overlay_ref)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True);recoverp=sub.add_parser('recover')
    for n in ('parent','engine','overlay','worker','release'):recoverp.add_argument('--'+n,required=True,help='JSON exact reference')
    recoverp.add_argument('--old-source',action='append',required=True);readonly=sub.add_parser('reconcile-activation');readonly.add_argument('--manifest',required=True,help='JSON exact reference; readonly only')
    args=parser.parse_args()
    try:
        if args.action=='recover':result=recover(*[json.loads(getattr(args,n)) for n in ('parent','engine','overlay','worker','release')],[json.loads(r) for r in args.old_source])
        else:result=ensure(json.loads(args.manifest),readonly=True)
        print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
