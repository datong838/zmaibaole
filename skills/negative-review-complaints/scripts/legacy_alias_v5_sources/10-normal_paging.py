"""Isolated pure adjacent-page evidence contract. No UI, writes, or legacy changes.
Page 1 is real-observed; later/terminal layouts need live review before release.
"""
import sys,json,re,copy
from pathlib import Path
from datetime import date,timedelta
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'skills/negative-review-complaints/scripts/normal_observation.py').is_file())
sys.path[:0]=[str(ROOT/'skills/negative-review-complaints/scripts')]
import normal_observation as n
import normal_review_body as body
import normal_source_proof_session as source_proof_session
A=n.authority
need=n.need
CONTRACT='normal-negative-pages-until-observed-fold-boundary-v1'
LIST='commentList-hkujq4 isPC-WBFQKh commentList-C8RoYO'
HEAD='header-sQid1u commentListHeader-jKdTh_'
def cl(node):return node.get('attributes',{}).get('class','')
def exact(node,tag,classes):return node.get('tag')==tag and cl(node)==classes
def pager(node,*,_loading_diagnostic=False):
    need(exact(node,'div','pagination-GXvAPk'),'normal-pager-shape')
    children=node.get('children',[]);loading=False
    if len(children)==3:
        indicator=children[0];need(exact(indicator,'img','loading-cihppn') and indicator.get('role')=='img' and indicator.get('name')=='' and not indicator.get('children') and indicator.get('disabled') is False,'normal-pager-shape');loading=True;children=children[1:]
    need(len(children)==2,'normal-pager-shape')
    total,group=children;need(exact(total,'div','text-bjyZFG') and not total.get('children') and exact(group,'div','buttonGroup-GDbp9Y') and len(group['children'])==3,'normal-pager-children')
    prev,current,nxt=group['children'];m=re.fullmatch(r'([1-9]\d*)/([1-9]\d*)',n.literal(current));t=re.fullmatch(r'共([1-9]\d*)条记录',n.literal(total));need(m and t and exact(current,'div','text-bjyZFG'),'normal-pager-text')
    page,pages=map(int,m.groups());count=int(t[1]);need(1<=page<=pages==(count+9)//10,'normal-pager-range')
    for direction,b,disabled in [('previous',prev,True if loading else page==1),('next',nxt,True if loading else page==pages)]:
        need(exact(b,'div','button-j4VxiA'+(' isDisabled-unTBS6' if disabled else '')) and b.get('disabled') is not True and b.get('name')=='' and len(b.get('children',[]))==1,'normal-pager-button')
        icon=b['children'][0]
        for tag in ('svg','g','path'):
            need(icon.get('tag')==tag and icon.get('name')=='' and len(icon.get('children',[]))==(0 if tag=='path' else 1),'normal-pager-icon')
            if tag=='svg':need(cl(icon)=='icon-v6i0WU' and icon.get('role')=='presentation','normal-pager-svg')
            if tag!='path':icon=icon['children'][0]
    need(not loading or _loading_diagnostic,'normal-pager-loading-readonly-wait')
    if _loading_diagnostic:need(loading,'normal-loading-indicator-required')
    return {'page':page,'pages':pages,'platform_pager_total':count,'previous_disabled':page==1,'next_disabled':page==pages,'previous_selector':prev['selector'],'next_selector':nxt['selector']}

IMAGE_ONLY_SCHEMA=body.SCHEMA
def image_only_export_body(card,store,customer,exported,source,expected_source_sha256):
    return body.resolve(card,store,customer,{'image_only_text_schema':IMAGE_ONLY_SCHEMA},exported,source,expected_source_sha256)

def inspect_page(job,page,profile,receipt_ref,*,_source_terminal_page=None,_full_identity=True):
    need(profile.get('contract')==CONTRACT and profile.get('status') in ('pending-live-multipage-validation','live-validated'),'new-pending-profile-required')
    tab,tree=n.context(page,job['groupid']);need(type(tab.get('windowId')) is int,'normal-paging-window-required')
    if _full_identity:n.public_identity(tree,job['identity'])
    from dom_evidence import review_filter_fields,all_store_scope
    all_store_scope(tree);fields=review_filter_fields(tree);end=(date.fromisoformat(job['end_exclusive'])-timedelta(days=1)).isoformat()
    need(fields['评价时间']['attributes'].get('value')==job['start']+' ~ '+end,'normal-paging-date')
    need(all(fields[k]['attributes'].get('value')=='全部' for k in ('评价类型','评价来源','评价状态')),'normal-paging-filters')
    ns=n.flatten(tree['root']);selected=n.one(ns,{'name':'中差评（1-3心）'},'negative');need('isSelected-ov8pOi' in cl(selected).split(),'normal-paging-negative')
    root=n.one(ns,{'attributes':{'class':LIST}},'normal-list');children=root.get('children',[]);need(len(children)>=3 and exact(children[0],'div',HEAD),'normal-page-direct-root')
    pg=pager(children[-1]);header=[x for x in n.flatten(children[0]) if not x.get('children') and re.fullmatch(r'已筛选[1-9]\d*条',x.get('name',''))];need(len(header)==1,'normal-header-count');count=int(re.search(r'\d+',header[0]['name'])[0])
    boundaries=[(i,x) for i,x in enumerate(children[1:-1],1) if 'foldTitleContainer-DwIByI' in cl(x).split()];need(len(boundaries)<=1,'normal-fold-boundary-ambiguous')
    if boundaries:
        terminal=profile.get('terminal_layout')
        witness=_source_terminal_page if _source_terminal_page is not None else page
        if isinstance(terminal,dict) and terminal.get('approved_page'):
            pinned=terminal['approved_page'];path=Path(pinned['path']);need(path.is_absolute() and not path.is_symlink() and A.digest(path)==pinned['sha256'],'terminal-approved-page-changed');witness=json.loads(path.read_bytes());wt,wr=n.context(witness,job['groupid']);need(wt['tabId']==tab['tabId'] and wt['windowId']==tab['windowId'],'terminal-approved-page-scope');wl=n.one(n.flatten(wr['root']),{'attributes':{'class':LIST}},'terminal-approved-list');need(pager(wl['children'][-1])==pg,'terminal-approved-pager');wb=[x for x in wl['children'][1:-1] if 'foldTitleContainer-DwIByI' in cl(x).split()];need(len(wb)==1 and n.matcher(wb[0],terminal.get('boundary_matcher',{})),'terminal-approved-boundary')
        need(isinstance(terminal,dict) and isinstance(terminal.get('page_sha256s'),list) and 1<=len(terminal['page_sha256s'])<=2 and A.data_hash(witness) in terminal['page_sha256s'] and n.matcher(boundaries[0][1],terminal.get('boundary_matcher',{})),'terminal-layout-awaits-live-profile')
        labels=[x for x in n.flatten(boundaries[0][1]) if not x.get('children') and x.get('name')==terminal.get('boundary_label')]
        need(isinstance(terminal.get('boundary_label'),str) and bool(terminal['boundary_label']) and len(labels)==1,'terminal-boundary-label-unverified')
    cutoff=boundaries[0][0] if boundaries else len(children)-1
    # Only direct cards BEFORE the boundary are inspected. Folded subtree text is never consumed.
    cards=children[1:cutoff];need(1<=len(cards)<=10 and all(exact(c,'div','commentItem-jrXo5p') for c in cards),'normal-page-cards-or-terminal-shape')
    if profile.get('terminal_layout',{}).get('first_page_terminal') is True:
        need(pg['page']==1 and bool(boundaries),'first-page-terminal-cannot-accept-later-fold-page')
    if boundaries and pg['page']==1:
        need(terminal.get('first_page_terminal') is True and pg['previous_disabled'] is True and
             len(cards)==count<=10,'terminal-page1-layout-needs-review')
    need(A.digest(receipt_ref['path'])==receipt_ref['sha256']==job['source_receipt_sha256'] and receipt_ref['path']==job['source_receipt'],'normal-paging-receipt-binding')
    receipt=json.loads(Path(receipt_ref['path']).read_bytes());need(receipt['company']==job['company'] and str(receipt['groupid'])==str(job['groupid']) and receipt['identity']==receipt['identity_before']==job['identity'] and receipt['account_verified'] is True and receipt['download_verified'] is True and receipt['source_is_authoritative_export'] is True and receipt.get('backend')=='local-dom-bridge' and receipt.get('operator_skill')=='douyin-laike-operator' and receipt.get('transport_proof',{}).get('safety')=='DOM-only' and receipt.get('transport_proof',{}).get('reviewed_extension_ready') is True and receipt['work_order_id']==job['source_work_order_id'] and receipt['date_range']=={'start':job['start'],'end':end},'normal-paging-receipt-scope')
    need(A.digest(receipt['source'])==receipt['src_sha256'] and A.stamp(page['observed_at'])>=A.stamp(receipt['recorded_at']),'normal-paging-source-or-time')
    exported,_=A.load_export(receipt['source'],job,receipt);rows=[]
    for card in cards:
        scope=n.flatten(card);f={k:n.review_field_literal(n.one(scope,{'attributes':{'class':clname}},k),k,profile.get('text_schema')) for k,clname in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf')]}
        bodies=[x for x in scope if cl(x)=='text-Hl9jZe'];body_evidence={}
        if not bodies and profile.get('image_only_text_schema')==IMAGE_ONLY_SCHEMA:
            f['text'],body_evidence=image_only_export_body(card,f['store'],f['customer'],exported,receipt['source'],receipt['src_sha256'])
        else:f['text']=n.review_field_literal(n.one(scope,{'attributes':{'class':'text-Hl9jZe'}},'text'),'text',profile.get('text_schema'))
        acts=[x for x in scope if not x.get('children') and x.get('name') in ('投诉','查看投诉结果','投诉审核中')];need(len(acts)==1,'normal-page-action')
        matches=[x for x in exported if x['match']==(f['store'],f['customer'],f['text'])];need(len(matches)==1 and matches[0]['stars']<=3,'normal-page-current-exact-negative-join')
        rows.append({**f,**body_evidence,'action':acts[0]['name'],'section':'filtered','text_complete':True,'dom_selector':card['selector'],'page_index':pg['page'],'review_id':matches[0]['review_id']})
    need(len({x['review_id'] for x in rows})==len(rows),'normal-page-duplicate')
    return {'contract':CONTRACT,'page_sha256':A.data_hash(page),'scope':{'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'tabId':tab['tabId'],'windowId':tab['windowId'],'url':tab['url'],'start':job['start'],'end_exclusive':job['end_exclusive'],'receipt_sha256':receipt_ref['sha256'],'source_sha256':receipt['src_sha256']},'normal_header_count':count,'pager':pg,'rows':rows,'observed_at':page['observed_at'],'terminal_boundary':({'selector':boundaries[0][1]['selector'],'direct_normal_cards_before_boundary':len(cards),'folded_text_read':False} if boundaries else None),'all_normal_read':False,'profile_live_validated':False}

def inspect_loading(job,page,profile,receipt_ref,prior,expected_page):
    """Only diagnose the exact loading shell; no row or missing count is accepted."""
    need(profile.get('contract')==CONTRACT and profile.get('status') in ('pending-live-multipage-validation','live-validated'),'new-pending-profile-required')
    need(expected_page==prior['pager']['page']+1,'normal-loading-adjacent-target')
    tab,tree=n.context(page,job['groupid']);n.public_identity(tree,job['identity'])
    from dom_evidence import review_filter_fields,all_store_scope
    all_store_scope(tree);fields=review_filter_fields(tree);end=(date.fromisoformat(job['end_exclusive'])-timedelta(days=1)).isoformat()
    need(fields['评价时间']['attributes'].get('value')==job['start']+' ~ '+end,'normal-paging-date')
    need(all(fields[k]['attributes'].get('value')=='全部' for k in ('评价类型','评价来源','评价状态')),'normal-paging-filters')
    ns=n.flatten(tree['root']);selected=n.one(ns,{'name':'中差评（1-3心）'},'negative');need('isSelected-ov8pOi' in cl(selected).split(),'normal-paging-negative')
    root=n.one(ns,{'attributes':{'class':LIST}},'normal-list');children=root.get('children',[])
    need(len(children)>=3 and exact(children[0],'div',HEAD),'normal-page-direct-root')
    # Loading alone omits 已筛选44条. Validate the four real column labels, without filling it in.
    leaves=[n.literal(x) for x in n.flatten(children[0]) if not x.get('children')]
    need(leaves==['评价','门店','顾客','操作'],'normal-loading-header-shape')
    pg=pager(children[-1],_loading_diagnostic=True);need(pg==prior['pager'],'normal-loading-original-pager-changed')
    need(all(exact(x,'div','commentItem-jrXo5p') for x in children[1:-1]),'normal-loading-normal-root-only')
    need(A.digest(receipt_ref['path'])==receipt_ref['sha256']==job['source_receipt_sha256'] and receipt_ref['path']==job['source_receipt'],'normal-paging-receipt-binding')
    receipt=json.loads(Path(receipt_ref['path']).read_bytes())
    need(receipt['company']==job['company'] and str(receipt['groupid'])==str(job['groupid']) and receipt['identity']==receipt['identity_before']==job['identity'] and receipt['account_verified'] is True and receipt['download_verified'] is True and receipt['source_is_authoritative_export'] is True and receipt['work_order_id']==job['source_work_order_id'] and receipt['date_range']=={'start':job['start'],'end':end},'normal-paging-receipt-scope')
    need(A.digest(receipt['source'])==receipt['src_sha256'] and A.stamp(page['observed_at'])>=A.stamp(receipt['recorded_at']),'normal-paging-source-or-time')
    scope={'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'tabId':tab['tabId'],'windowId':tab['windowId'],'url':tab['url'],'start':job['start'],'end_exclusive':job['end_exclusive'],'receipt_sha256':receipt_ref['sha256'],'source_sha256':receipt['src_sha256']}
    need(scope==prior['scope'],'normal-loading-original-scope-changed')
    return {'kind':'normal-old-page-loading-v1','old_page':pg['page'],'expected_page':expected_page,'raw_sha256':A.data_hash(page),'normal_header_count_observed':None,'rows_accepted':False,'stable_page_accepted':False}

def finalize_pages(job,pages,profile,receipt_ref,*,stable_pairs=None):
    need(profile.get('status')=='live-validated','normal-multipage-profile-awaits-live-validation')
    # Reparse every original page; never trust caller-supplied success/row flags.
    need(isinstance(stable_pairs,list) and len(stable_pairs)==len(pages) and bool(pages),'normal-stable-pairs-required')
    stable=[]
    for page,pair in zip(pages,stable_pairs):
        need(isinstance(pair,list) and len(pair)==2 and A.data_hash(pair[1])==A.data_hash(page),'normal-stable-pair-page-binding')
        before=inspect_page(job,pair[0],profile,receipt_ref);after=inspect_page(job,pair[1],profile,receipt_ref)
        need(A.stamp(before['observed_at'])<A.stamp(after['observed_at']),'normal-two-distinct-read-times-required')
        keys=('scope','normal_header_count','pager','rows','terminal_boundary')
        need(all(before[k]==after[k] for k in keys),'normal-page-not-stable')
        stable.append([before['page_sha256'],after['page_sha256']])
    proofs=[inspect_page(job,p,profile,receipt_ref) for p in pages];need(proofs,'normal-pages-required');first=proofs[0];seen=set();rows=[];previous=None
    for index,p in enumerate(proofs,1):
        need(p['scope']==first['scope'] and p['normal_header_count']==first['normal_header_count'] and p['pager']['platform_pager_total']==first['pager']['platform_pager_total'] and p['pager']['pages']==first['pager']['pages'],'normal-page-scope-changed')
        need(p['pager']['page']==index,'normal-page-sequence')
        need(previous is None or A.stamp(p['observed_at'])>=previous,'normal-page-time-reversed');previous=A.stamp(p['observed_at'])
        need(bool(p['terminal_boundary'])==(index==len(proofs)),'normal-terminal-boundary-required-no-pages-after-fold')
        if index<len(proofs):need(len(p['rows'])==10 and not p['pager']['next_disabled'],'normal-intermediate-page-incomplete')
        for row in p['rows']:need(row['review_id'] not in seen,'normal-page-repeat');seen.add(row['review_id']);rows.append(row)
    need(len(rows)==first['normal_header_count'],'normal-unique-coverage-incomplete')
    return {'contract':CONTRACT,'normal_scope_mode':CONTRACT,'all_normal_read':True,'all_pages_read':True,'filtered_count':len(rows),'platform_pager_total':first['pager']['platform_pager_total'],'observed_normal_pages':len(proofs),'normal_end':'actual-direct-fold-boundary','next_may_remain_enabled_for_excluded_scope':not proofs[-1]['pager']['next_disabled'],'folded_rows_observed':None,'folded_text_read':False,'rows':rows,'proofs':proofs,'stable_page_pair_sha256s':stable,'review_time_scope_only':True,'complaint_time_all_history_proven':False}


def parser_upgrade(original_bytes,job,expected_sha256,*,first_page=None,profile=None,receipt_ref=None):
    """Pure candidate plan. Caller must archive original bytes and atomically save.
    Not wired into production Navigator/CLI; no actual workspace is changed here.
    """
    import hashlib
    need(hashlib.sha256(original_bytes).hexdigest()==expected_sha256,'normal-upgrade-original-state-sha')
    state=json.loads(original_bytes);fingerprint=hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    need(state.get('fingerprint')==fingerprint and state.get('phase')=='observeNegative' and not state.get('stable_normal_verified') and not state.get('normal_probe') and not state.get('stable_read_evidence') and not state.get('pagination_contract'),'normal-upgrade-scope-or-existing-proof')
    need(all(c.get('state')=='confirmed' for c in state.get('calls',[])),'normal-upgrade-unknown')
    need(isinstance(first_page,dict) and isinstance(profile,dict) and isinstance(receipt_ref,dict),'normal-upgrade-first-page-evidence-required')
    first=inspect_page(job,first_page,profile,receipt_ref);need(first['pager']['page']==1 and state.get('tab_id')==first['scope']['tabId'],'normal-upgrade-original-tab-first-page')
    result=copy.deepcopy(state);result['pagination_contract']={'source_scope':first['scope'],'first_page_sha256':first['page_sha256'],'contract':CONTRACT,'job_fingerprint':fingerprint,'original_state_sha256':expected_sha256,'scope':'read-only-normal-pages-profile-discovery','live_profile_validated':False}
    return result

def prepare_adjacent_intent(state,job,page,profile,receipt_ref,direction):
    """No request and no write. Integration MUST save returned state before click.
    Confirmed prior intent returns read-only verification; unknown never replays.
    """
    import hashlib
    fp=hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False).encode()).hexdigest();contract=state.get('pagination_contract',{})
    need(state.get('phase')=='observeNegative' and state.get('fingerprint')==fp==contract.get('job_fingerprint') and contract.get('contract')==CONTRACT,'normal-adjacent-original-contract')
    need(direction in ('next','previous'),'normal-adjacent-direction');proof=inspect_page(job,page,profile,receipt_ref);need(proof['scope']==contract.get('source_scope') and state.get('tab_id')==proof['scope']['tabId'],'normal-adjacent-original-tab-window-scope');pg=proof['pager']
    need((direction=='previous' or not proof['terminal_boundary']) and not pg[direction+'_disabled'],'normal-adjacent-end-or-boundary')
    target=pg['page']+(1 if direction=='next' else -1);key='normal-page:'+str(pg['page'])+'->'+str(target)
    command={'op':'click','tabId':proof['scope']['tabId'],'kind':'navigation','locator':{'by':'selector','value':pg[direction+'_selector']}}
    previous=[c for c in state.get('calls',[]) if c.get('key')==key]
    if previous:
        need(len(previous)==1 and previous[0]['command']==command,'normal-adjacent-intent-conflict');need(previous[0]['state']=='confirmed','normal-adjacent-unknown-no-replay')
        return {'state':copy.deepcopy(state),'command':None,'read_only_verify_target_page':target,'input_replayed':False}
    need(all(c.get('state')=='confirmed' for c in state.get('calls',[])),'normal-adjacent-unresolved-prior-intent')
    result=copy.deepcopy(state);result.setdefault('calls',[]).append({'key':key,'phase':'observeNegative','state':'unknown','command':command,'from_page_sha256':proof['page_sha256'],'expected_target_page':target,'scope':proof['scope']})
    return {'state':result,'command':command,'requires_atomic_save_before_dispatch':True,'expected_target_page':target,'input_replayed':False}


def joined_envelope(job,envelope,profile,receipt_ref):
    arguments={'job':job,'envelope':envelope,'profile':profile,'receipt_ref':receipt_ref}
    return source_proof_session.reconstruct(arguments,lambda:_joined_envelope_uncached(job,envelope,profile,receipt_ref))

def _joined_envelope_uncached(job,envelope,profile,receipt_ref):
    need(envelope.get('source')=='local-dom-bridge' and envelope.get('company')==job['company'] and str(envelope.get('groupid'))==str(job['groupid']),'normal-paged-envelope-scope')
    identity=envelope.get('identity_evidence',{});tab,tree=n.context(identity,job['groupid']);n.public_identity(tree,job['identity'])
    final=finalize_pages(job,envelope.get('pages',[]),profile,receipt_ref,stable_pairs=envelope.get('stable_page_pairs'))
    first=final['proofs'][0];need(tab['tabId']==first['scope']['tabId'] and tab.get('windowId')==first['scope']['windowId'] and A.stamp(identity['observed_at'])<=A.stamp(final['proofs'][0]['observed_at']),'normal-paged-identity-anchor')
    observation={**final,'company':job['company'],'groupid':str(job['groupid']),'source':'local-dom-bridge','url':envelope['pages'][-1]['tab']['url'],'observed_at':envelope['pages'][-1]['observed_at'],'account_verified':True,'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],'negative_filter':'中差评（1-3心）','filter_active':True,'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'},'fold_boundary_verified':True,'profile_sha256':A.data_hash(profile),'identity_evidence_sha256':A.data_hash(identity),'count_semantics':{'filtered_count':'complete-normal-filtered-input','platform_pager_total':'platform-displayed-record-count-not-a-folded-count'},'observed_folded':None,'folded_scope':'not-traversed-not-included'}
    return A.join(job,observation,receipt_ref['path'],receipt_ref['sha256'])


def current_page_for_case(page,job,envelope,profile,source,row):
    """Pure result-reader guard; never navigates. Caller must arrive at case page.
    Full original source is replayed first, not replaced by a partial observation.
    """
    receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']}
    need(joined_envelope(job,envelope,profile,receipt_ref)==source,'normal-case-complete-source-required')
    matches=[x for x in source['rows'] if x['review_id']==row['review_id']];need(len(matches)==1 and matches[0]==row,'normal-case-original-source-row')
    index=row['page_index'];need(type(index) is int and 1<=index<=len(envelope['pages']),'normal-case-source-page-index')
    original=envelope['pages'][index-1];original_proof=source['proofs'][index-1]
    # Preserve the existing result reader's provider + pinned complete identity rule.
    _,tree=n.context(page,job['groupid']);nodes=n.flatten(tree['root'])
    cards=[x for x in nodes if 'UserCard-index-module__outer--' in cl(x)]
    if cards:n.public_identity(tree,job['identity'])
    else:
        titles=[x for x in nodes if any(k.startswith(('src-components-HeaderV2-components-Profile-index-module__title--','src-components-HeaderV3-components-Profile-index-module__title--')) for k in cl(x).split()) and x.get('name')==job['identity']['provider']]
        need(len(titles)==1,'normal-case-current-provider-unverified')
    current=inspect_page(job,page,profile,receipt_ref,_source_terminal_page=original,_full_identity=False)
    need(current['scope']==original_proof['scope'] and current['pager']==original_proof['pager'] and current['normal_header_count']==source['filtered_count'] and current['terminal_boundary']==original_proof['terminal_boundary'],'normal-case-current-page-scope')
    fields=('review_id','store','customer','text','dom_selector','page_index')
    need([{k:x[k] for k in fields} for x in current['rows']]==[{k:x[k] for k in fields} for x in original_proof['rows']],'normal-case-current-ordered-page-changed')
    need(current['pager']['page']==index,'normal-case-not-at-required-page')
    return current
