#!/usr/bin/env python3
"""Additional v7 local anchor/row frame route. No scrolling, navigation or writes.
All selectors come from a pinned accepted public DOM profile. Physical scrolling
is a separate reviewed semantic operation; each frame uses a fresh pinned tree.
"""
import argparse,hashlib,json,re,os,fcntl
from pathlib import Path
from datetime import date,timedelta
import verified_capture as vc
import screenshot_registration as sr
from visible_capture import write_capture,atomic,sha
HEADERS=('违规原因','处置主体','违规对象','处置生效状态','处置方式')
POLICY='anchored-frames-v1'
def need(ok,code):
    if not ok:raise ValueError(code)
def fingerprint(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def selector_identity(value):
    return re.sub(r':nth-of-type\(1\)', '', value or '')
def matches(node,ref):
    if isinstance(ref,str):return selector_identity(node.get('selector'))==selector_identity(ref)
    need(isinstance(ref,dict) and bool(ref) and not set(ref)-{'selector','role','name','attributes'},'frame-profile-matcher-invalid')
    return all(selector_identity(node.get(k))==selector_identity(v) if k=='selector' else node.get(k)==v for k,v in ref.items() if k!='attributes') and all(node.get('attributes',{}).get(k)==v for k,v in ref.get('attributes',{}).items())
def one(nodes,ref):
    found=[n for n in nodes if matches(n,ref)];need(len(found)==1,'frame-selector-not-unique');return found[0]
def text(node):
    need(not node.get('children'),'frame-scope-text-must-be-leaf');value=' '.join(str(node.get('attributes',{}).get('value',node.get('name',''))).split());need(0<len(value)<800,'frame-text-truncated-or-empty');return value
def integer(value):
    match=re.fullmatch(r'(?:(?:全部|共|违规总数)\s*)?(\d+)(?:\s*条)?',value);need(match is not None,'frame-page-or-total-not-explicit');return int(match[1])
def selected(node):return any(node.get('attributes',{}).get(k)=='true' for k in ('aria-selected','aria-pressed','aria-checked'))
def css_tokens(node):return set(node.get('attributes',{}).get('class','').split())
def governance_all(node,total=None):
    value=' '.join(str(node.get('name','')).split())
    need(node.get('tag')=='div' and {'governance_merchant-tab-bar-item','governance_merchant-tab-bar-item-active'}<=css_tokens(node),'frame-governance-all-tab-not-active')
    match=re.fullmatch(r'全部\s*(\d+)',value);need(match is not None,'frame-governance-all-count-missing')
    if total is not None:need(int(match[1])==total,'frame-governance-all-total-conflict')
    return int(match[1])
def governance_unread_off(node):
    need(node.get('tag')=='label' and node.get('name')=='只看未读' and 'governance_merchant-checkbox' in css_tokens(node),'frame-governance-unread-not-reviewed')
    icons=[n for n in node.get('children',[]) if n.get('tag')=='span' and 'governance_merchant-checkbox-icon' in css_tokens(n)]
    need(len(icons)==1 and 'governance_merchant-checkbox-icon-uncheck' in css_tokens(icons[0]) and not any('checked' in token or token.endswith('-check') for token in css_tokens(icons[0])),'frame-unread-filter-not-disabled')
    need(node.get('attributes',{}).get('aria-checked') in (None,'false'),'frame-unread-filter-not-disabled')
def governance_next_disabled(node):
    need(node.get('tag')=='li' and 'governance_merchant-pager-item' in css_tokens(node),'frame-governance-pager-not-reviewed')
    return 'governance_merchant-pager-item-disabled' in css_tokens(node)
def row_notice_id(row,profile):
    if profile.get('noticeIdMode')=='first-cell-text-v1':
        need(profile.get('domProfile')=='governance-records-v1' and row.get('tag')=='tr' and row.get('role')=='row' and 'governance_merchant-Table-Row' in css_tokens(row),'frame-notice-text-row-not-reviewed')
        cells=row.get('children',[]);need(cells and cells[0].get('tag')=='td' and cells[0].get('role')=='cell','frame-notice-first-cell-required')
        value=str(cells[0].get('name',''));need(len(value)<800,'frame-notice-first-cell-truncated')
        ids=re.findall(r'(?<![A-Za-z0-9_])ID:\s*([A-Za-z0-9_-]+)(?![A-Za-z0-9_-])',value)
        need(len(ids)==1,'frame-notice-first-cell-id-not-unique');return ids[0]
    need(profile.get('noticeIdMode') is None and isinstance(profile.get('idAttribute'),str),'frame-notice-id-profile-unreviewed')
    return str(row.get('attributes',{}).get(profile['idAttribute'],''))

def page_inputs(source_ref,observation_ref,profile_ref,*,screenshot_anchor=None):
    source=sr.document(source_ref);obs=sr.document(observation_ref);profile=sr.document(profile_ref)
    derived=profile.get('derivation',{}).get('kind') in ('governance-records-derived-profile-v1','governance-records-reboot-derived-profile-v1')
    if derived:
        import sys,importlib
        directory=Path(__file__).resolve().parents[3]/'skills/violation-notifier/scripts';previous=list(sys.path)
        try:
            sys.path.insert(0,str(directory));derived_profile=importlib.import_module('prepare_records_profile')
            need(Path(derived_profile.__file__).resolve()==directory/'prepare_records_profile.py','frame-derived-module-origin-conflict')
            derived_profile.validate(profile,source_ref);need(profile.get('status')=='DOM-derived-ready','frame-derived-profile-not-ready')
        finally:sys.path[:]=previous
    else:need(profile.get('status')=='live-validated' and profile.get('revision'),'frame-profile-not-accepted')
    need(source.get('profile_revision')==profile['revision'],'frame-source-profile-revision-conflict')
    need(source.get('source')=='local-dom-bridge' and source.get('account_verified') is True and source.get('records',{}).get('scope')=='全部' and source['records'].get('all_pages_read') is True and source['records'].get('filters_verified') is True and source['records'].get('unread_only') is False,'frame-source-not-verified-records')
    need(obs.get('source')=='local-dom-bridge' and obs.get('observed_at'),'frame-observation-not-verified');sr.when(obs['observed_at']);ns=vc.allnodes(obs['tree'])
    if derived:
        meta=profile['derivation'];derived_profile.d.nav.context([{'tabs':[obs['tab']]}],meta['tab_id'],source['groupid']);need(obs.get('tab_id')==meta['tab_id'] and obs['tab'].get('windowId')==meta['window_id'],'frame-derived-scope-changed');
        if screenshot_anchor is None:derived_profile.d.nav.identity(obs['tree'],source['identity']);one(ns,profile['identity']['card'])
        else:
            import screenshot_identity as identity
            identity.current(screenshot_anchor,source_ref,profile_ref,obs)
        derived_profile.d.normal_page(obs['tree'],derived_profile.d.document(meta['job']),derived_profile.d.document(meta['query']))
    else:
        for field in ('provider','account_id','manager'):need(text(one(ns,profile['identity'][field]))==source['identity'][field],'frame-current-account-changed')
    from urllib.parse import urlsplit
    need(urlsplit(obs['tab']['url']).path==urlsplit(source['url']).path,'frame-record-route-conflict')
    p=profile['records'];governance=p.get('domProfile')=='governance-records-v1';need(p.get('domProfile') in (None,'governance-records-v1'),'frame-dom-profile-unreviewed');date_node=one(ns,p['dateInput']);date_text=derived_profile.g.date_value(obs['tree']) if derived else text(date_node).replace('/','-');end=(date.fromisoformat(source['end_exclusive'])-timedelta(days=1)).isoformat();need(date_text==source['start']+' ~ '+end,'frame-current-date-changed')
    scope=one(ns,p['scope'])
    if governance:governance_all(scope)
    else:need(text(scope)=='全部' and selected(scope),'frame-not-all-records')
    unread=one(ns,p['unreadOnly'])
    if governance:governance_unread_off(unread)
    else:need(unread.get('attributes',{}).get('aria-checked')=='false','frame-unread-filter-not-disabled')
    if derived:
        need(p.get('filter_contract')=='same-source-date-all-unread-full-pages-v1','frame-derived-filter-contract-changed');filters={'scope':'全部','unread_only':False,'contract':p['filter_contract']}
    else:
        need(isinstance(p.get('otherFilters'),dict) and bool(p['otherFilters']),'frame-default-filters-required');filters={}
        for key,rule in p['otherFilters'].items():
            actual=text(one(ns,rule['locator']));need(actual==rule['expected'],'frame-other-filter-changed');filters[key]=actual
    total_node=one(ns,p['total']);total=governance_all(total_node) if governance else integer(text(total_node));page_node=one(ns,p['currentPage']);page=integer(derived_profile.g.text(page_node) if derived else text(page_node));
    if governance:
        governance_all(scope,total);need(page_node.get('tag')=='li' and {'governance_merchant-pager-item','governance_merchant-pager-item-checked'}<=css_tokens(page_node),'frame-governance-current-page-unverified')
    need(page>=1 and total==source['records']['total'] and total>0,'frame-total-or-page-conflict')
    next_node=one(ns,p['next'])
    if governance:last=governance_next_disabled(next_node)
    else:
        need(type(next_node.get('disabled')) is bool or next_node.get('attributes',{}).get('aria-disabled') in ('true','false'),'frame-next-state-unknown');last=next_node.get('disabled') is True or next_node.get('attributes',{}).get('aria-disabled')=='true'
    root=one(ns,p['root']);desc=[]
    def walk(node):
        desc.append(node)
        for child in node.get('children',[]):walk(child)
    walk(root);rows=[n for n in desc if matches(n,p['row'])];need(rows,'frame-page-empty')
    source_rows={r['notice_id']:r for r in source['records']['rows']};need(len(source_rows)==len(source['records']['rows'])==total,'frame-source-total-notices-conflict');page_rows=[];spec=[{'key':'date','kind':'date-filter','selector':date_node['selector'],'notice_id':None}]
    header_refs=profile.get('screenshot',{}).get('headers');need(isinstance(header_refs,dict) and set(header_refs)==set(HEADERS),'frame-five-actual-header-selectors-required')
    for index,name in enumerate(HEADERS):
        header=one(ns,header_refs[name]);need(vc.explicit_header_text(header)==name,'frame-actual-header-mismatch');spec.append({'key':'header'+str(index),'kind':'header','selector':header['selector'],'notice_id':None})
    for index,row in enumerate(rows):
        # v7 intentionally rejects generic div rows; never manufacture role=row.
        need(row.get('role')=='row','frame-live-row-role-not-reviewed');notice=row_notice_id(row,p);need(notice in source_rows and notice not in [r['notice_id'] for r in page_rows],'frame-page-notice-not-in-source')
        sub=[]
        def children(n):
            sub.append(n)
            for c in n.get('children',[]):children(c)
        children(row);subject=text(one(sub,p['subject']));need(subject==source_rows[notice]['subject'],'frame-source-subject-changed')
        page_rows.append({'notice_id':notice,'subject':subject});spec.append({'key':'row'+str(index),'kind':'row','selector':row['selector'],'notice_id':notice})
    business_contract=profile.get('evidence_contract')=='notice-five-business-cells-v1'
    if business_contract:
        import business_cells_capture as business
        need(derived,'frame-business-contract-requires-derived-profile');command=business.make_command(source_ref,obs,spec,screenshot_identity=screenshot_anchor,projection_contract=profile.get('projection_contract'))
    else:command=vc.command_from_inputs(source_ref['path'],source_ref['sha256'],observation_ref['path'],observation_ref['sha256'],spec)
    if derived and not business_contract:
        import governance_projection as projection
        for element in command['elements']:
            element['key']=projection.SCHEMA+':'+element['key']
            if element['kind']=='row':element['expected_text']=projection.row_text(obs['tree'],str(source['groupid']),element['locator']['value'])
        command['dom_sha256']=projection.digest(obs['tree'],str(source['groupid']));vc.bridge.validate_command(command)
    query={'company':source['company'],'groupid':str(source['groupid']),'start':source['start'],'end_exclusive':source['end_exclusive'],'scope':'全部','unread_only':False,'other_filters':filters,'total':total,'source_sha256':source_ref['sha256'],'profile_sha256':profile_ref['sha256']}
    page_scope={**query,'page':page,'last_page':last,'page_rows':page_rows}
    result={'command':command,'scope':page_scope,'query_fingerprint':fingerprint(query),'page_fingerprint':fingerprint(page_scope),'url':obs['tab']['url']}
    if profile.get('evidence_contract') is not None:
        import business_cells_capture as business
        need(derived and profile['evidence_contract']==business.CONTRACT,'frame-business-contract-requires-derived-profile')
        vc.bridge.validate_command(command);result.update(evidence_contract=business.CONTRACT,business_spec=business.spec(obs['tree'],str(source['groupid']),actual_url=obs['tab']['url'] if screenshot_anchor else None,projection_contract=profile.get('projection_contract')))
    if screenshot_anchor is not None:
        import screenshot_identity as identity
        need(business_contract,'frame-anchor-business-only');result['screenshot_identity']=identity.validate(screenshot_anchor,source_ref,profile_ref);result['screenshot_anchor']=screenshot_anchor
    return result

def proof(command,expected_url,request):
    reply=request(command);need(reply.get('ok') is True,'frame-proof-request-failed:'+str(reply.get('error')));result=reply['result'];sr.validate_public_proof(result,command,expected_url);need(result['safety_version']=='dom-only-20261021-11','frame-current-v11-required');return result

def _capture(source_ref,observation_ref,profile_ref,*,mode,chain_id,key,out,request=None):
    need(mode in ('anchor','rows') and isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'frame-mode-or-chain-id-invalid')
    inputs=page_inputs(source_ref,observation_ref,profile_ref);command=inputs['command'];request=request or vc.bridge.request;out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    intent=out.with_suffix('.frame-intent.json');registration=out.with_suffix('.frame.json');need(not intent.exists() and not registration.exists(),'frame-existing-intent-no-replay')
    binding={'source_path':source_ref['path'],'source_sha256':source_ref['sha256'],'observation_path':observation_ref['path'],'observation_sha256':observation_ref['sha256'],'profile_path':profile_ref['path'],'profile_sha256':profile_ref['sha256'],'command':command,'captureKey':key,'chain_id':chain_id,'frame_mode':mode,'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint']}
    with intent.open('x') as f:json.dump({'state':'intent',**binding},f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    try:
        before=proof(command,inputs['url'],request);facts=sr.visible_facts(before)
        need(facts['date_filter_visible'] and facts['list_headers_visible'] if mode=='anchor' else bool(facts['notice_ids']),'frame-required-content-not-fully-visible')
        atomic(intent,{'state':'intent',**binding,'before':before});write_capture({'op':'capture-visible',**{k:command[k] for k in ('tabId','windowId','groupid')},'captureKey':key},out,request)
        after=proof(command,inputs['url'],request);need(before==after,'frame-dom-changed-during-image');need(page_inputs(source_ref,observation_ref,profile_ref)==inputs,'frame-pinned-input-changed')
        metadata={'source':'local-dom-bridge','source_sha256':source_ref['sha256'],'sha256':sha(out),'viewport_only':True,'visibility_policy':POLICY,'frame_mode':mode,'chain_id':chain_id,'page_scope':inputs['scope'],'query_fingerprint':inputs['query_fingerprint'],'page_fingerprint':inputs['page_fingerprint'],**facts,'public_dom_proof':{'before':before,'after':after},'capture_metadata':{'path':str(out.with_suffix('.json')),'sha256':sha(out.with_suffix('.json'))},'pinned_inputs':binding}
        sr.validate_frame_capture_chain(out,metadata,source_sha256=source_ref['sha256'],groupid=command['groupid'],expected_command=command,expected_url=inputs['url']);atomic(registration,metadata);atomic(intent,{'state':'complete',**binding,'registration':str(registration),'sha256':sha(out)})
        return {'image':str(out),'metadata':str(registration),'notice_ids':facts['notice_ids'],'date_filter_visible':facts['date_filter_visible'],'list_headers_visible':facts['list_headers_visible'],'business_progress_changed':False}
    except Exception as error:atomic(intent,{'state':'unknown',**binding,'error':str(error),'retry_permitted':False});raise

def capture(source_ref,observation_ref,profile_ref,*,mode,chain_id,key,out,request=None):
    # Scope failures are pure reads. Only valid jobs reserve a screenshot intent.
    page_inputs(source_ref,observation_ref,profile_ref)
    need(mode in ('anchor','rows') and isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'frame-mode-or-chain-id-invalid')
    folder=Path(source_ref['path']).resolve().parent/'.frame-capture-state';folder.mkdir(parents=True,exist_ok=True)
    file=folder/(fingerprint([source_ref['sha256'],chain_id])+'.json')
    scope={'source_sha256':source_ref['sha256'],'profile_sha256':profile_ref['sha256'],'chain_id':chain_id}
    with file.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if file.exists():
            state=json.loads(file.read_text());need(state.get('scope')==scope,'frame-chain-capture-scope-conflict')
        else:state={'version':1,'scope':scope,'frames':[]}
        previous=[e for e in state['frames'] if e['captureKey']==key or e['out']==str(Path(out).resolve())]
        need(not previous,'frame-existing-intent-no-replay')
        need(all(e['state']=='complete' for e in state['frames']),'frame-chain-prior-unknown-no-new-key')
        entry={'captureKey':key,'out':str(Path(out).resolve()),'state':'unknown','mode':mode};state['frames'].append(entry);atomic(file,state)
        try:
            result=_capture(source_ref,observation_ref,profile_ref,mode=mode,chain_id=chain_id,key=key,out=out,request=request)
            entry.update(state='complete',metadata={'path':result['metadata'],'sha256':sha(result['metadata'])});atomic(file,state);return result
        except Exception as error:entry['error']=str(error);atomic(file,state);raise


def validate_frame(image,metadata,*,source):
    m=metadata;binding=m.get('pinned_inputs',{});need(binding.get('source_sha256')==source['sha256'],'frame-source-hash-conflict')
    src={'path':binding.get('source_path'),'sha256':binding.get('source_sha256')};need(sr.document(src)==sr.document(source),'frame-batch-source-conflict')
    obs={'path':binding.get('observation_path'),'sha256':binding.get('observation_sha256')};profile={'path':binding.get('profile_path'),'sha256':binding.get('profile_sha256')};inputs=page_inputs(src,obs,profile)
    need(binding.get('command')==inputs['command'] and m.get('page_scope')==inputs['scope'] and m.get('page_fingerprint')==inputs['page_fingerprint']==binding.get('page_fingerprint') and m.get('query_fingerprint')==inputs['query_fingerprint']==binding.get('query_fingerprint') and m.get('chain_id')==binding.get('chain_id') and m.get('frame_mode')==binding.get('frame_mode'),'frame-declared-scope-not-derived')
    result=sr.validate_frame_capture_chain(image,m,source_sha256=source['sha256'],groupid=inputs['command']['groupid'],expected_command=inputs['command'],expected_url=inputs['url']);result['references']=[src,obs,profile,result['capture_metadata'],result['capture_png']];return result

def validate_chain(manifest,*,source,company,groupid,start,end_exclusive,notice_ids):
    need(manifest.get('visibility_policy')==POLICY and manifest.get('source_sha256')==source['sha256'],'frame-chain-source-policy-conflict');frames=manifest.get('frames');need(isinstance(frames,list) and bool(frames),'frame-chain-empty')
    src=sr.document(source);need(src['company']==company and str(src['groupid'])==str(groupid) and src['start']==start and src['end_exclusive']==end_exclusive and {r['notice_id'] for r in src['records']['rows']}==set(notice_ids),'frame-chain-batch-scope-conflict')
    pages={};entries=[];covered=set();keys=set();profile_sha=None;query=None;chain_id=manifest.get('chain_id');previous_page=0;last_epoch=None;last_time=None;chain_version=None
    need(isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'frame-chain-id-invalid')
    for f in frames:
        metadata=sr.document(f['metadata']);image=f['image'];need(Path(image).is_absolute(),'frame-chain-image-path-required');need(metadata.get('chain_id')==chain_id,'frame-chain-id-conflict');result=validate_frame(image,metadata,source=source);page=metadata['page_scope']['page'];mode=metadata['frame_mode'];binding=metadata['pinned_inputs'];key=binding['captureKey'];need(key not in keys,'frame-chain-capture-key-reused');keys.add(key)
        if chain_version is None:chain_version=result['version']
        need(result['version']==chain_version,'frame-chain-safety-version-changed')
        if query is None:query=metadata['query_fingerprint'];profile_sha=binding['profile_sha256']
        need(metadata['query_fingerprint']==query and binding['profile_sha256']==profile_sha,'frame-chain-query-or-profile-changed')
        if page not in pages:
            need(mode=='anchor' and page==previous_page+1,'frame-chain-new-page-anchor-required')
            if previous_page:need(pages[previous_page]['last_page'] is False,'frame-chain-page-after-final')
            ids=[r['notice_id'] for r in metadata['page_scope']['page_rows']];need(not any(n in old['ids'] for old in pages.values() for n in ids),'frame-chain-notice-repeated-across-pages')
            pages[page]={'fingerprint':metadata['page_fingerprint'],'ids':ids,'last_page':metadata['page_scope']['last_page'],'capture_scope':result['capture_scope'],'grant_nonce':result['grant_nonce']};previous_page=page;last_epoch=None
        need(page==previous_page and metadata['page_fingerprint']==pages[page]['fingerprint'],'frame-chain-old-anchor-or-page-reused')
        need(result['capture_scope']==pages[page]['capture_scope'] and result['grant_nonce']==pages[page]['grant_nonce'],'frame-chain-page-session-changed')
        frame_time=sr.when(result['observed_at']);need(last_time is None or frame_time>=last_time,'frame-chain-time-order-invalid');last_time=frame_time
        epoch=metadata['public_dom_proof']['before']['epoch'];need(last_epoch is None or epoch>=last_epoch,'frame-chain-document-epoch-reset');last_epoch=epoch
        covered.update(result['notice_ids']);entries.append({'image':{'path':image,'sha256':metadata['sha256']},'metadata':f['metadata'],'references':result['references'],'notice_ids':result['notice_ids'],'frame_mode':mode,'page':page})
    need(pages[previous_page]['last_page'] is True and {n for p in pages.values() for n in p['ids']}==set(notice_ids),'frame-chain-pages-incomplete')
    need(covered==set(notice_ids),'frame-chain-full-row-coverage-incomplete')
    return {'entries':entries,'notice_ids':sorted(covered),'visibility_policy':POLICY,'chain_id':chain_id,'viewport_only':True}

def assemble(source_ref,metadata_paths,out):
    source=sr.document(source_ref);frames=[];chain_id=None
    for path in metadata_paths:
        ref={'path':str(Path(path).resolve()),'sha256':sha(path)};m=sr.document(ref);capture_meta=sr.document(m['capture_metadata'])
        if chain_id is None:chain_id=m.get('chain_id')
        need(m.get('chain_id')==chain_id,'frame-assemble-chain-id-conflict')
        frames.append((sr.when(capture_meta['capture']['observedAt']),{'image':capture_meta['png']['path'],'metadata':ref}))
    frames.sort(key=lambda item:item[0]);manifest={'visibility_policy':POLICY,'source_sha256':source_ref['sha256'],'chain_id':chain_id,'frames':[f for _,f in frames]}
    validate_chain(manifest,source=source_ref,company=source['company'],groupid=source['groupid'],start=source['start'],end_exclusive=source['end_exclusive'],notice_ids=[r['notice_id'] for r in source['records']['rows']])
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
    return {'path':str(out),'sha256':sha(out),'frames':len(frames),'business_progress_changed':False}

def reconcile(source_ref,profile_ref,chain_id):
    """Only reconcile already-saved complete frame evidence; never recapture."""
    sr.document(source_ref);sr.document(profile_ref)
    file=Path(source_ref['path']).resolve().parent/'.frame-capture-state'/(fingerprint([source_ref['sha256'],chain_id])+'.json')
    need(file.is_file(),'frame-chain-journal-required')
    with file.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads(file.read_text())
        need(state.get('scope')=={'source_sha256':source_ref['sha256'],'profile_sha256':profile_ref['sha256'],'chain_id':chain_id},'frame-chain-capture-scope-conflict')
        for entry in state['frames']:
            if entry['state']=='complete':continue
            metadata=Path(entry['out']).with_suffix('.frame.json')
            if not metadata.is_file():continue
            m=json.loads(metadata.read_text());binding=m.get('pinned_inputs',{})
            need(binding.get('captureKey')==entry['captureKey'] and binding.get('profile_sha256')==profile_ref['sha256'] and m.get('chain_id')==chain_id and m.get('frame_mode')==entry['mode'],'frame-reconcile-original-intent-conflict')
            validate_frame(entry['out'],m,source=source_ref)
            entry.update(state='complete',metadata={'path':str(metadata),'sha256':sha(metadata)},reconciled_without_capture=True)
        atomic(file,state)
    return {'state':'complete' if all(e['state']=='complete' for e in state['frames']) else 'await-existing-evidence','journal':str(file),'ui_operations':False,'new_capture':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('capture')
    for name in ('source','source-sha256','observation','observation-sha256','profile','profile-sha256','mode','chain-id','key','out'):a.add_argument('--'+name,required=True)
    a=sub.add_parser('assemble')
    for name in ('source','source-sha256','out'):a.add_argument('--'+name,required=True)
    a.add_argument('--frames',nargs='+',required=True)
    a=sub.add_parser('reconcile')
    for name in ('source','source-sha256','profile','profile-sha256','chain-id'):a.add_argument('--'+name,required=True)
    args=p.parse_args();ref=lambda path,h:{'path':str(Path(path).resolve()),'sha256':h}
    if args.action=='reconcile':result=reconcile(ref(args.source,args.source_sha256),ref(args.profile,args.profile_sha256),args.chain_id)
    elif args.action=='assemble':result=assemble(ref(args.source,args.source_sha256),args.frames,args.out)
    else:result=capture(ref(args.source,args.source_sha256),ref(args.observation,args.observation_sha256),ref(args.profile,args.profile_sha256),mode=args.mode,chain_id=args.chain_id,key=args.key,out=args.out)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
