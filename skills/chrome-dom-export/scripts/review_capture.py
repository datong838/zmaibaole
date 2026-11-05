#!/usr/bin/env python3
"""Normal-review viewport capture, independent of violation notice IDs.
No navigation/scroll/action except the existing activeTab-granted screenshot.
Inputs are pinned files. Unknown capture outcomes never replay, even with a new key.
"""
import argparse,fcntl,hashlib,json,os,re,sys
from pathlib import Path
from datetime import date,timedelta
from visible_capture import write_capture,atomic,sha,stamp,require
import visible_capture
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'negative-review-complaints/scripts'))
import normal_observation as normal
import authoritative_join as authority

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':sha(p)}
def document(r):
    require(set(r)=={'path','sha256'} and sha(r['path'])==r['sha256'],'review-pinned-document-changed');return load(r['path'])
def text(n):return normal.literal(n)
def complete_list_nodes(profile,root,expected):
    scope=normal.flatten(root)
    if 'complete_list' not in profile:
        # The exact full-list structure was already verified by the caller.
        # Older parent profiles omit the redundant selector rules. Derive only
        # from those five actual nodes, never from a name/count or a new page.
        require(all(isinstance(n.get('selector'),str) and n['selector'] and n['selector'].strip()==n['selector'] for n in expected.values()),'review-complete-list-selector-missing')
        rules={k:{'selector':n['selector']} for k,n in expected.items()}
    else:
        rules=profile['complete_list'];require(type(rules) is dict and set(rules)==set(expected),'review-complete-list-profile-invalid')
    complete={k:normal.one(scope,rules[k],'complete-'+k) for k in expected}
    require(all(complete[k] is expected[k] for k in expected),'review-complete-list-profile-position-mismatch')
    return complete

def command_from_inputs(job_ref,source_ref,envelope_ref,profile_ref,page_ref,review_keys):
    job,source,envelope,profile,page=map(document,(job_ref,source_ref,envelope_ref,profile_ref,page_ref))
    # Rebuild the original join from its pinned normal DOM and actual XLSX.
    observed=normal.observation(job,envelope,profile);binding=source['authority_binding']
    rebuilt=authority.join(job,observed,binding['receipt_path'],binding['receipt_sha256'])
    require(rebuilt==source,'review-authoritative-source-revalidation-failed')
    tab,tree=normal.context(page,source['groupid']);nodes=normal.flatten(tree['root'])
    require(tab['tabId']==envelope['identity_evidence']['tab']['tabId'],'review-current-tab-changed')
    require(normal.authority.stamp(page['observed_at'])>=normal.authority.stamp(source['observed_at']),'review-page-precedes-source')
    # A fresh page may follow semantic scrolling; identity comes from the pinned
    # source identity proof, while exact source selectors/tuple/query bind now.
    root=normal.one(nodes,profile['normal_root'],'normal-root');exclusive=profile.get('scope_mode')=='verified-complete-normal-list'
    if exclusive:
        require(profile.get('normal_root_exclusive') is True and not profile.get('fold_boundary'),'review-exclusive-profile-invalid');normal.complete_normal_list(root,source['filtered_count'])
        children=root['children'];pager=children[-1];group=pager['children'][1];expected={'pager':pager,'total':pager['children'][0],'previous':group['children'][0],'current':group['children'][1],'next':group['children'][2]}
        complete=complete_list_nodes(profile,root,expected);cards=children[1:-1]
    else:
        boundary=normal.one(nodes,profile['fold_boundary'],'fold-boundary');require(boundary in root.get('children',[]),'review-boundary-not-direct')
        cutoff=root['children'].index(boundary);cards=[n for n in root['children'][:cutoff] if normal.matcher(n,profile['row'])]
    require(len(cards)==source['filtered_count'],'review-normal-count-changed')
    one=lambda rule,label:normal.one(nodes,rule,label)
    date_node=one(profile['date_filter'],'date');end=(date.fromisoformat(source['end_exclusive'])-timedelta(days=1)).isoformat();date_text=source['start']+' ~ '+end
    require(text(date_node)==date_text,'review-date-changed')
    negative=one(profile['negative_filter'],'negative');require(text(negative)=='中差评（1-3心）' and profile['active_class'] in negative.get('attributes',{}).get('class','').split(),'review-negative-filter-changed')
    count=one(profile['filtered_count'],'count');require(re.fullmatch(r'(?:评价\s*)?已筛选\s*'+str(len(cards))+r'\s*条',text(count)) is not None,'review-count-changed')
    filters={k:one(v,k) for k,v in profile['other_filters'].items()};require(set(filters)=={'评价类型','评价来源','评价状态'} and all(text(n)=='全部' for n in filters.values()),'review-other-filter-changed')
    source_rows={source['groupid']+':'+r['review_id']:r for r in source['rows']}
    require(review_keys and len(set(review_keys))==len(review_keys) and set(review_keys)<=set(source_rows),'review-key-not-current-normal-source')
    specs=[]
    for key in review_keys:
        row=source_rows[key];require(row['review_id']=='verified-tuple-sha256:'+row['authority']['canonical_sha256'],'review-external-canonical-mismatch')
        card=normal.one(cards,{'selector':row['dom_selector']},'normal-card');children=normal.flatten(card)
        fields={k:normal.one(children,profile[k],k) for k in ('store','customer','text')}
        require(all(normal.review_field_literal(fields[k],k,text_schema=profile.get('text_schema'))==row[k] for k in fields),'review-source-tuple-changed')
        heart=normal.one(children,{'attributes':{'class':'score-R2K3dS'}},'heart-region')
        specs.append({'review_key':key,'card':card['selector'],'store':fields['store']['selector'],'customer':fields['customer']['selector'],'body':fields['text']['selector'],'heart':heart['selector'],'store_text':row['store'],'customer_text':row['customer'],'body_text':row['text'],**({'body_text_schema':'public-visible-text-v2'} if profile.get('text_schema')=='public-visible-text-v2' else {})})
    return {'op':'review-viewport-proof','tabId':tab['tabId'],'windowId':tab['windowId'],'groupid':source['groupid'],'source_sha256':source_ref['sha256'],
      'dom_sha256':hashlib.sha256(json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),
      'scope':{'list':root['selector'],**({'scope_mode':'verified-complete-normal-list','complete_list':{k:n['selector'] for k,n in complete.items()}} if exclusive else {'boundary':boundary['selector']}),'date':date_node['selector'],'negative':negative['selector'],'count':count['selector'],'other_filters':{k:n['selector'] for k,n in filters.items()},'date_text':date_text,'active_class':profile['active_class'],'normal_count':len(cards)},'reviews':specs}

def proof_response(response,command,*,versions=None):
    require(response.get('ok') is True,'review-proof-request-failed:'+str(response.get('error')));p=response['result']
    require(p.get('method')=='public-DOM-normal-review-viewport-proof' and p.get('source')=='local-dom-bridge' and p.get('safety_version') in (versions or (visible_capture.SAFETY,)),'review-proof-method-version-mismatch')
    require(p.get('scope')=={k:command[k] for k in ('tabId','windowId','groupid')} and p.get('source_sha256')==command['source_sha256'] and p.get('reference_dom_sha256')==command['dom_sha256'],'review-proof-source-scope-mismatch')
    require(p.get('viewport_only') is True and p.get('pixel_coordinates_returned') is False and p.get('pixel_actions_used') is False and p.get('occlusion_verified') is False,'review-proof-limitations-mismatch')
    require(p.get('all_cards_visible') is True and re.fullmatch('[a-f0-9]{64}',str(p.get('semantic_sha256',''))),'review-viewport-not-contained')
    require(p.get('query')=={'date':command['scope']['date_text'],'negative_filter':'中差评（1-3心）','normal_count':command['scope']['normal_count'],**({'scope_mode':'verified-complete-normal-list','normal_list_complete':True,'pagination':{'total':command['scope']['normal_count'],'current':'1/1','previous_disabled':True,'next_disabled':True}} if command['scope'].get('scope_mode')=='verified-complete-normal-list' else {'fold_boundary':command['scope']['boundary']}),'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'}},'review-query-proof-mismatch')
    actual=p.get('reviews');require(isinstance(actual,list) and len(actual)==len(command['reviews']),'review-proof-row-count-mismatch')
    for r,s in zip(actual,command['reviews']):
        require(all(r.get(k)==s[v] for k,v in (('review_key','review_key'),('card','card'),('store','store_text'),('customer','customer_text'),('body','body_text'))),'review-proof-tuple-mismatch')
        gs=r.get('geometry',{});require(set(gs)=={'card','store','customer','body','heart'},'review-geometry-fields-invalid')
        for g in gs.values():
            require(set(g)=={'rendered','visible_region','viewport_contained','text_unclipped','unsupported_css_absent','occlusion_verified','fully_visible'} and all(type(v) is bool for v in g.values()) and g['occlusion_verified'] is False,'review-geometry-invalid')
            require(not g['viewport_contained'] or g['visible_region'],'review-contained-region-conflict')
            require(g['fully_visible']==all(g[k] for k in ('rendered','viewport_contained','text_unclipped','unsupported_css_absent')),'review-geometry-derived-flag-conflict')
        core=lambda g:all(g[k] for k in ('rendered','viewport_contained','unsupported_css_absent'))
        require(r['card_visible']==(core(gs['card']) and all(gs['body'][k] for k in ('rendered','visible_region','unsupported_css_absent')) and all(gs[k]['fully_visible'] for k in ('store','customer','heart'))) and r['text_complete_in_image']==gs['body']['fully_visible'] and r['heart_region_visible']==gs['heart']['fully_visible'],'review-visibility-flags-conflict')
        require(r.get('normal_section') is True and r.get('card_visible') is True and r.get('heart_region_visible') is True and type(r.get('text_complete_in_image')) is bool,'review-proof-card-incomplete')
    return p

def validate_capture(metadata,command,png_path,proof,*,versions=None):
    require(metadata.get('state')=='complete' and metadata.get('command')==command,'review-capture-not-complete')
    c=metadata['capture'];before=c['before'];require({k:before.get(k) for k in ('tabId','windowId','groupid')}==proof['scope'],'review-capture-proof-scope-mismatch');require(before==c['after'] and all(before.get(k)==command[k] for k in ('tabId','windowId','groupid')) and before.get('url')==proof['url'],'review-capture-context-changed')
    require(c.get('safety_version') in (versions or (visible_capture.SAFETY,)) and c.get('safety_version')==proof['safety_version'] and c.get('capture_method')=='chrome.tabs.captureVisibleTab' and c.get('captureKey')==command['captureKey'] and c.get('viewport_only') is True and c.get('pixel_actions_used') is False,'review-capture-method-invalid')
    grant=c.get('grant',{});require(grant.get('via')=='chrome.action.onClicked' and grant.get('scope')==before and grant.get('safety_version')==c.get('safety_version') and isinstance(grant.get('nonce'),str) and bool(grant['nonce']),'review-real-activeTab-grant-required')
    require(authority.stamp(grant['invokedAt'])<=authority.stamp(c['observedAt']),'review-activeTab-time-mismatch')
    require(authority.stamp(metadata['intent_at'])<=authority.stamp(c['observedAt'])<=authority.stamp(metadata['completed_at']),'review-capture-time-invalid')
    require('imageDataUrl' not in c and Path(png_path).resolve()==Path(metadata['png']['path']).resolve() and sha(png_path)==metadata['png']['sha256'],'review-original-png-changed')
    width,height=visible_capture.validate_png(Path(png_path).read_bytes());require((width,height)==(metadata['png']['width'],metadata['png']['height']),'review-png-size-changed')
    return metadata['png']

def capture(manifest,outdir,request,*,backend='chrome-active-tab',pid=None,native=None,repair_report=None):
    require(backend in ('chrome-active-tab','screen-capture-kit'),'review-capture-backend-invalid')
    if backend=='screen-capture-kit':require(type(pid) is int and pid>0,'review-native-pid-required')
    require(set(manifest)=={'job','source','envelope','profile','page','review_keys','capture_key'},'review-manifest-fields-invalid')
    command=command_from_inputs(*(manifest[k] for k in ('job','source','envelope','profile','page')),manifest['review_keys'])
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',manifest['capture_key']) is not None,'review-stable-capture-key-required')
    outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    # Per source+review tuple, a changed output directory/key cannot replay capture.
    source_path=Path(manifest['source']['path']);state_dir=source_path.parent/'.review-capture-state';state_dir.mkdir(exist_ok=True)
    key=digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});state=state_dir/(key+'.json')
    with (state_dir/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if state.exists():
            old=load(state);require(old.get('manifest')==manifest and old.get('outdir')==str(outdir) and old.get('backend','chrome-active-tab')==backend,'review-original-intent-required')
            if repair_report is not None:
                import native_capture_repair as repair
                repair.eligible(state,outdir/'review.json',manifest,outdir,backend,pid,repair_report)
            else:
                require(old.get('state')=='complete','review-capture-unknown-no-replay');registration=load(old['registration']);require(sha(old['registration'])==old['registration_sha256'],'review-registration-changed');import review_registration;review_registration.verify(old['registration']);return registration
        require(repair_report is None or state.exists(),'native-repair-original-state-required')
        repair_intent=None
        before=proof_response(request(command),command);before_at=stamp();source_observed=document(manifest['source'])['observed_at'];require(authority.stamp(source_observed)<=authority.stamp(before_at),'review-proof-precedes-source')
        if backend=='screen-capture-kit':
            import native_window_capture as nw
            native_command={'backend':backend,'pid':pid,**{k:command[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':manifest['capture_key']}
            fresh_preflight=nw.preflight(native_command,request,native)  # No screenshot intent or permission request.
            if repair_report is not None:
                repair_intent=repair.prepare(state,outdir/'review.json',manifest,outdir,backend,pid,repair_report,fresh_preflight)
        intent={'state':'unknown','backend':backend,'manifest':manifest,'outdir':str(outdir),'intent_at':stamp(),'proof_before':before}
        if repair_intent is not None:intent['repair_intent']=repair_intent
        atomic(state,intent)
        cap={'op':'capture-visible',**{k:command[k] for k in ('tabId','windowId','groupid')},'captureKey':manifest['capture_key']}
        if backend=='screen-capture-kit':result=nw.write_capture(native_command,outdir/'review.png',request,native,repair_intent=repair_intent)
        else:result=write_capture(cap,outdir/'review.png',request)
        after=proof_response(request(command),command);after_at=stamp()
        require(before==after,'review-proof-changed-during-capture')
        metadata=load(result['result']['metadata'])
        if backend=='screen-capture-kit':
            image=nw.validate(metadata,native_command,result['result']['path']);require(metadata['before']['scope']=={**before['scope'],'url':before['url'],'title':metadata['before']['scope']['title']},'review-native-proof-scope-mismatch')
        else:image=validate_capture(metadata,cap,result['result']['path'],before)
        registration={'kind':'normal-review-viewport-registration-v1','state':'complete','source':manifest['source'],'profile':manifest['profile'],'page':manifest['page'],'job':manifest['job'],'envelope':manifest['envelope'],'review_keys':manifest['review_keys'],'proof_before':before,'proof_after':after,'capture_backend':backend,'native_pid':pid if backend=='screen-capture-kit' else None,'whole_window':backend=='screen-capture-kit','capture_key':manifest['capture_key'],'proof_before_observed_at':before_at,'proof_after_observed_at':after_at,'capture_metadata':ref(result['result']['metadata']),'image':image,'viewport_only':backend!='screen-capture-kit','occlusion_verified':False,'coverage':'selected normal review cards in current viewport; collapsed body may be incomplete','text_complete_in_image':{r['review_key']:r['text_complete_in_image'] for r in before['reviews']},'recorded_at':stamp()}
        path=outdir/'registration.json';require(not path.exists(),'review-registration-exists');atomic(path,registration);import review_registration;review_registration.verify(path);intent.update(state='complete',registration=str(path),registration_sha256=sha(path));atomic(state,intent);return registration

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--outdir',required=True);p.add_argument('--backend',choices=('chrome-active-tab','screen-capture-kit'),default='chrome-active-tab');p.add_argument('--pid',type=int);p.add_argument('--retry-native-pre-output-after-repair');p.add_argument('--repair-report-sha256');a=p.parse_args()
    import bridge
    request=lambda cmd:bridge.request(cmd,timeout=50)
    require(bool(a.retry_native_pre_output_after_repair)==bool(a.repair_report_sha256),'native-repair-report-and-hash-required')
    repair_ref={'path':str(Path(a.retry_native_pre_output_after_repair).resolve()),'sha256':a.repair_report_sha256} if a.retry_native_pre_output_after_repair else None
    options={'backend':a.backend,'pid':a.pid}
    if repair_ref is not None:options['repair_report']=repair_ref
    result=capture(load(a.manifest),a.outdir,request,**options);print(json.dumps({'ok':True,'registration':str(Path(a.outdir).resolve()/'registration.json'),'review_keys':result['review_keys'],'text_complete_in_image':result['text_complete_in_image']},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
