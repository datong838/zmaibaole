"""Exact missing-complete-list screenshot pre-input recovery; metadata only.
Preserves the ingested ledger and every failed/returned original call.
"""
import argparse,copy,fcntl,json,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/workshop-director/scripts'),str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import complaint_execution_order as o
import initial_ledger_recovery as h
import review_entry_preinput_recovery as entry
import review_capture as capture
FIELD='review_frames_preinput_recovery'
TAB_FIELD='review_capture_tab_recovery'
KIND='verified-review-frames-preinput-recovery-v1'
ERROR='review-complete-list-profile-invalid'
def paths():return {n:str(o.PROJECT/p) for n,p in {'review_capture.py':'skills/chrome-dom-export/scripts/review_capture.py','initial_ledger_recovery.py':'skills/negative-review-complaints/scripts/initial_ledger_recovery.py','review_entry_preinput_recovery.py':'skills/negative-review-complaints/scripts/review_entry_preinput_recovery.py','review_frames_preinput_recovery.py':'skills/negative-review-complaints/scripts/review_frames_preinput_recovery.py'}.items()}
def source_tip(parent,release_ref,old_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);targets=rel['targets'];ps=paths();old={Path(x['path']).name:x for x in old_refs}
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(targets)==4 and {t['target'] for t in targets}==set(ps.values()) and all(t['mode']=='0644' for t in targets),'review-frames-exact-four-reviewed-targets')
    o.need(len(old_refs)==3 and set(old)=={n+'.before' for n in ps if n!='review_frames_preinput_recovery.py'},'review-frames-exact-three-archives')
    archives=[]
    for n in ps:
        if n=='review_frames_preinput_recovery.py':continue
        t=next(t for t in targets if t['target']==ps[n]);r=old[n+'.before'];o.need(r['sha256']==t['old_sha256'],'review-frames-old-source-binding');o.raw(r);archives.append({'target':ps[n],'archive':r})
    proxy=copy.deepcopy(parent)
    if proxy.get(FIELD):proxy=o.doc(o.doc(proxy[FIELD])['parent_archive'])
    prior=entry.verify_recovered(proxy,proxy[entry.FIELD],installed=False,extra_source_archives=[*[x for x in archives if x['target']==ps['review_capture.py']],*extra_source_archives])
    codes=copy.deepcopy(prior['code_refs']);by_path={r['path']:r for r in codes}
    for t in targets:
        o.raw(t['after']);new={'path':t['target'],'sha256':t['after']['sha256']}
        if t['target']==ps['review_frames_preinput_recovery.py']:
            o.need(t['old_sha256'] is None and t['target'] not in by_path,'review-frames-new-helper-only');codes.append(new)
        else:
            previous=by_path[t['target']];o.need(previous['sha256']==t['old_sha256'],'review-frames-admission-base');codes[codes.index(previous)]=new
    if installed:
        for r in codes:o.raw(r)
        for p in ps.values():o.need(Path(p).stat().st_mode & 0o777==0o644,'review-frames-installed-mode')
    return prior,codes,archives

def ledger_projection(previous,source,snapshot,at):
    """Exact existing workflow.ingest delta for a wholly new, filtered unit.
    Existing-review updates are deliberately outside this recovery contract.
    """
    value=copy.deepcopy(previous);rows=source['rows'];o.need(source['filtered_count']==len(rows) and rows and all(r['section']=='filtered' for r in rows),'review-frames-new-filtered-unit-only')
    o.need(value['company']==source['company'] and value['groupid']==source['groupid'] and value['identity']==source['identity'],'review-frames-ledger-identity')
    for row in rows:
        key=value['groupid']+':'+row['review_id'];o.need(key not in value['tasks'] and row['action']=='投诉','review-frames-original-new-task-only')
        value['tasks'][key]={'id':key,'review':{k:row.get(k,'') for k in ('review_id','store','date','time','stars','customer','customer_id','text','product')},'action':row['action'],'status':'pending','snapshot':snapshot,'latest_snapshot':snapshot,'screenshot':None,'wecom':None,'analysis':None,'history':None,'result':None,'updated_at':at}
        if row.get('body_kind'):
            import normal_review_body as rb
            value['tasks'][key]['body_provenance']=rb.provenance(row)
    batch=source['start']+'_'+source['end_exclusive'];o.need(batch not in value['batches'],'review-frames-new-batch-only')
    value['batches'][batch]={'start':source['start'],'end_exclusive':source['end_exclusive'],'ids':[value['groupid']+':'+r['review_id'] for r in rows],'snapshot':snapshot,'filtered_count':len(rows),'excluded_folded':0,'closed_at':None}
    value['events'].append({'at':at,'type':'scope-captured','batch':batch,'count':len(rows),'excluded_folded':0});value.update(updated_at=at,xlsx_dirty=True);return value

def original_contract(parent,engine,manifest_ref,scroll_ref,ledger_ref,prior):
    order=o.validate(parent['order']);folder=o.location(parent['order']);company=order['companies'][0];a=engine['companies'][0]['artifacts'];x=a['unit_artifacts'];unit=folder/'companies/0/units/0'
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==4 and parent['calls'][:3]==prior['failed_calls'] and not parent.get(FIELD) and not parent.get('child') and not parent.get('completion'),'review-frames-original-parent-hold')
    o.need(engine['kind']=='complaint-execution-v1' and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'] and engine['status']=='hold' and engine['phase']=='collect' and engine['index']==0 and engine.get('error')==ERROR and not engine.get(FIELD) and len(engine['calls'])==44,'review-frames-original-engine-hold')
    oldp=o.doc(parent[entry.FIELD]);olde=o.doc(oldp['engine_archive']);oldparent=o.doc(oldp['parent_archive']);expected=entry.recovered(oldparent,olde,o.doc(oldp['operator_archive']),parent[entry.FIELD])[1]
    o.need(engine['calls'][:5]==olde['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine.get(entry.FIELD)==parent[entry.FIELD],'review-frames-prior-engine-chain')
    for i,c in enumerate(engine['calls']):
        if i in (0,4):continue
        if i==43:o.need(c['step']=='collect' and c['state']=='failed' and c['error']==ERROR and c['company_index']==0,'review-frames-sole-new-failure');continue
        o.need(c['state']=='returned' and c.get('applied') is True and Path(c['result']['path'])==folder/'receipts'/(str(i+1).zfill(5)+'.json'),'review-frames-returned-prefix');o.doc(c['result'])
    o.need(a['unit_index']==0 and a['unit_phase']=='frames' and a['completed_units']==[] and x['frame_index']==x['review_index']==0 and x['operations']==[] and a['units'][0]=={'kind':'new','start':company['start'],'end_exclusive':company['end_exclusive'],'keys':[]} and engine['calls'][-1]['context']=={'order':order,'company':company,'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'review-frames-original-context')
    o.need(o.doc(engine['calls'][42]['result'])['artifacts']=={k:a[k] for k in ('journals','ledger_current','unit_artifacts','unit_phase')},'review-frames-ingest-receipt-binding')
    source=o.doc(x['source']);profile=o.doc(x['profile']);job=o.doc(x['job']);keys=[source['groupid']+':'+r['review_id'] for r in source['rows']]
    o.need(x['keys']==keys and (source['company'],source['groupid'],source['start'],source['end_exclusive'])==(company['company'],company['groupid'],company['start'],company['end_exclusive']) and profile['scope_mode']=='verified-complete-normal-list' and profile['normal_root_exclusive'] is True and 'complete_list' not in profile,'review-frames-original-missing-field-scope')
    o.need(Path(x['source']['path'])==unit/'normal-source.json' and Path(x['profile']['path'])==unit/'normal-profile.json' and Path(x['envelope']['path'])==unit/'normal-envelope.json' and Path(x['job']['path'])==unit/'normal-job.json','review-frames-canonical-unit-inputs')
    for n in ('acquisition','envelope','job','navigation','orders','page','profile','source','work_order'):o.doc(x[n])
    manifest=o.doc(manifest_ref);key=keys[0];o.need(len(keys)==1 and Path(manifest_ref['path'])==unit/'frames'/o.digest(key)/'manifest.json' and set(manifest)=={'job','source','envelope','profile','page','review_keys','capture_key'} and all(manifest[n]==x[n] for n in ('job','source','envelope','profile','page')) and manifest['review_keys']==[key] and manifest['capture_key']=='complaint-parent:'+o.digest({'dispatch':order['dispatch_id'],'key':key,'source':x['source']['sha256']})[:40],'review-frames-original-manifest')
    command=capture.command_from_inputs(*(manifest[n] for n in ('job','source','envelope','profile','page')),manifest['review_keys'])
    scroll=o.doc(scroll_ref);row=source['rows'][0];binding={'source':x['source'],'job':x['job'],'review_key':key,'tab_id':parent['tab_id'],'selector':row['dom_selector']}
    o.need(Path(scroll_ref['path'])==unit/'scrolls'/(o.digest(key)+'.json') and scroll['kind']=='complaint-parent-review-scroll-v1' and scroll['state']=='complete' and scroll['binding']==binding and scroll['command']=={'op':'scroll','tabId':parent['tab_id'],'locator':{'by':'selector','value':row['dom_selector']}} and scroll['visibility_claimed'] is False,'review-frames-completed-scroll-only')
    import normal_observation as normal
    before,after=o.doc(scroll['before']),o.doc(scroll['after']);o.need(before['tab']==after['tab'] and before['tab']['tabId']==parent['tab_id'],'review-frames-scroll-window')
    for raw in (before,after):normal.navigation_probe(raw['tree'],job,text_schema='public-visible-text-v2',image_only_text_schema=profile.get('image_only_text_schema'))
    target=normal.one(normal.flatten(before['tree']['root']),{'selector':row['dom_selector']},'scroll-review');reply=scroll['reply'];o.need(reply.get('ok') is True and reply['result']['version']=='dom-only-20261021-11' and reply['result']['scrolled']['selector']==target['selector'] and reply['result']['scrolled']['tag']==target['tag'],'review-frames-scroll-reply')
    ledger=o.doc(ledger_ref);o.need(ledger_ref['sha256']==a['ledger_current']['sha256'] and Path(a['ledger_current']['path'])==Path(company['root'])/'state.json','review-frames-ingested-ledger-binding')
    snapshot=ledger['tasks'][key]['snapshot'];o.need(Path(snapshot['path'])==Path(company['root'])/'evidence'/(x['source']['sha256']+'.json') and snapshot['sha256']==x['source']['sha256'] and o.raw(snapshot)==o.raw(x['source']),'review-frames-ingested-source-evidence')
    at=ledger['updated_at'];t=datetime.fromisoformat(at);o.need(t.utcoffset() is not None and datetime.fromisoformat(source['observed_at'])<=t<=datetime.fromisoformat(engine['calls'][-1]['intent_at']),'review-frames-ingest-time')
    o.need(ledger==ledger_projection(o.doc(company['ledger']),source,snapshot,at),'review-frames-exact-ingest-delta')
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);argv=parent['calls'][2]['argv'];o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==argv and launch['index']==3 and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':ERROR} and Path(call['launch']['path'])==folder/'children/0003-launch.json' and Path(call['result']['path'])==folder/'children/0003-exit.json','review-frames-exact-outer-failure')
    return {'failed_engine_indices':[0,4,43],'failed_calls':parent['calls'],'ledger_current':a['ledger_current'],'manifest':manifest_ref,'scroll':scroll_ref,'command':command,'unit_inputs':{n:x[n] for n in ('acquisition','envelope','job','navigation','orders','page','profile','source','work_order')},'scroll_observations':[scroll['before'],scroll['after']],'source_snapshot':snapshot}

def worker_evidence(parent,engine_ref,worker_ref):
    ex=o.doc(worker_ref);folder=Path(worker_ref['path']).parent;request=o.doc(ex['request']);response=o.doc(ex['response']);order=o.doc(parent['order']);pe=o.ref(folder/'parent-run-exit.json');r=o.doc(pe);out=json.loads(o.raw(r['stdout']))
    o.need(folder==o.PROJECT/'runtime/standalone-workshop-director/attempts'/request['attempt_id'] and Path(worker_ref['path'])==folder/'exit.json' and ex['returncode']==0 and ex['attempt_id']==request['attempt_id']==response['attempt_id'] and request['task']['id']==response['task_id'] and request['task']['flow']==o.FLOW and request['task']['day']==order['day'] and request['context']['order']==response['context']['order']==parent['order'] and response['outcome']=='failed' and response['error']=='parent-hold-inspect-original' and o.doc(request['config_ref'])==request['config'],'review-frames-natural-worker-binding')
    expected=[str(o.PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(o.PROJECT/'skills/workshop-director/scripts/complaint_execution_launcher.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--mode',parent['mode'],'--steps','1000']
    o.need(r['argv']==expected and r['returncode']==0 and not o.raw(r['stderr']) and out['status']=='hold' and out['error']=='execution-child-stopped' and out['last_child_receipt']==parent['calls'][-1]['result'] and out['engine']==engine_ref,'review-frames-natural-parent-hold')
    return [worker_ref,ex['request'],ex['response'],request['config_ref'],pe,r['stdout'],r['stderr']]

def no_capture(folder,manifest_ref):
    m=o.doc(manifest_ref);unit=Path(m['source']['path']).parent
    for directory in (unit/'.review-region-state',unit/'.review-capture-state',unit/'.account-overlay-preflight',Path(manifest_ref['path']).parent/'capture'):
        o.need(not directory.exists() or not any(directory.iterdir()),'review-frames-capture-or-input-already-exists')

def plan(parent_ref,engine_ref,manifest_ref,scroll_ref,ledger_ref,worker_ref,release_ref,old_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','review-frames-canonical-parent-engine')
    prior,codes,archives=source_tip(parent,release_ref,old_refs,installed=installed);facts=original_contract(parent,engine,manifest_ref,scroll_ref,ledger_ref,prior);evidence=worker_evidence(parent,engine_ref,worker_ref)
    return {'kind':KIND,'original_parent':parent_ref,'original_engine':engine_ref,'manifest':manifest_ref,'scroll':scroll_ref,'original_ledger':facts['ledger_current'],'worker':worker_ref,'release':release_ref,'old_sources':archives,'code_refs':codes,'facts':facts,'worker_evidence':evidence,'ui_used':False}

def recovered(parent,engine,proof):
    values=copy.deepcopy((parent,engine))
    for s in values:s.setdefault('resolved_errors',[]).append({'error':s.pop('error'),'recovery':proof});s.update(status='running',**{FIELD:proof})
    return values

def verify_recovered(current,proof_ref,*,installed=True,extra_source_archives=()):
    if current.get(TAB_FIELD):
        from review_capture_tab import verify_recovered as verify_tab
        return verify_tab(current,current[TAB_FIELD])
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-frames-preinput-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and Path(proof_ref['path'])==base/'proof.json' and current.get(FIELD)==proof_ref and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-frames-canonical-proof')
    for name,original in (('parent','parent'),('engine','engine'),('ledger','ledger')):o.need(Path(p[name+'_archive']['path'])==base/('original-'+name+'.json') and p[name+'_archive']['sha256']==p['original_'+original]['sha256'],'review-frames-original-archive')
    o.need(all(Path(x['archive']['path'])==base/'sources'/Path(x['archive']['path']).name for x in p['old_sources']),'review-frames-source-archive-path')
    original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);prior,codes,_=source_tip(original,p['release'],[x['archive'] for x in p['old_sources']],installed=installed,extra_source_archives=extra_source_archives);facts=original_contract(original,engine,p['manifest'],p['scroll'],p['ledger_archive'],prior);evidence=worker_evidence(original,p['original_engine'],p['worker']);expected=recovered(original,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['worker_evidence']==evidence and p['code_refs']==codes and current['calls'][:4]==original['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(original['origin_ref']).items()) and all(current.get(k)==original.get(k) for k in (h.FIELD,h.PLAN_FIELD,entry.FIELD)),'review-frames-preserved-original-chain')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':original['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['ledger_archive'],p['manifest'],p['scroll'],p['release'],*[x['archive'] for x in p['old_sources']],*evidence]}

def verified_engine_calls(engine):
    if engine.get(TAB_FIELD):
        from review_capture_tab import verified_engine_calls as verify_tab_calls
        return verify_tab_calls(engine)
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'review-frames-engine-parent-proof');verify_recovered(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1]
    o.need(engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'] and engine['calls'][:44]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'review-frames-original-engine-prefix')
    return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]

def current_ledgers(parent,engine):
    order=o.validate(parent['order']);first=engine['companies'][0]['artifacts']['ledger_current'];o.raw(first)
    for c in order['companies'][1:]:o.need(o.raw(o.ref(Path(c['root'])/'state.json'))==o.raw(c['ledger']),'review-frames-other-ledger-changed')
def recover(parent_ref,engine_ref,manifest_ref,scroll_ref,ledger_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-frames-preinput-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'manifest':manifest_ref,'scroll':scroll_ref,'original_ledger':ledger_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted((Path(r['path']).name,r['sha256']) for r in old_refs)==sorted((Path(x['archive']['path']).name,x['archive']['sha256']) for x in p['old_sources']),'review-frames-original-inputs')
        else:
            p=plan(parent_ref,engine_ref,manifest_ref,scroll_ref,ledger_ref,worker_ref,release_ref,old_refs,installed=True);no_capture(folder,manifest_ref);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True);o.canonical(base/'sources')
            for n,r in (('parent',parent_ref),('engine',engine_ref),('ledger',ledger_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            for x in p['old_sources']:x['archive']=h.immutable_bytes(base/'sources'/Path(x['archive']['path']).name,o.raw(x['archive']))
            p['at']=datetime.now(timezone.utc).isoformat();proof=o.immutable(base/'proof.json',p)
        original=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);new_parent,new_engine=recovered(original,engine,proof)
        lease=o.doc(o.ref(Path(original['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(original['order'])['dispatch_id'] and lease['day']==o.doc(original['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-frames-current-lease')
        current_ledgers(original,engine);no_capture(folder,manifest_ref);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],new_parent),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],new_engine)];verify_recovered(new_parent,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        current_ledgers(original,engine)
        for path,value in ((folder/'engine.json',new_engine),(folder/'launcher.json',new_parent)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','engine','manifest','scroll','ledger','worker','release'):parser.add_argument('--'+n,required=True,help='JSON exact path/SHA reference')
    parser.add_argument('--old-source',action='append',required=True);a=parser.parse_args()
    try:print(json.dumps(recover(*[json.loads(getattr(a,n)) for n in ('parent','engine','manifest','scroll','ledger','worker','release')],[json.loads(r) for r in a.old_source]),ensure_ascii=False));return 0
    except Exception as error:print(json.dumps({'ok':False,'error':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())
