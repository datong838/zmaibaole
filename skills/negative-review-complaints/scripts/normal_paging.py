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
    exported,_=A.load_export(receipt['source'],job,receipt);rows=[];pending=[]
    pending_policy=profile.get('pending_card_policy')
    need(pending_policy in (None,'history-unresolved-store-v1'),'normal-pending-policy-invalid')
    if pending_policy:need(len({c.get('selector')for c in cards})==len(cards) and all(c.get('selector')for c in cards),'normal-pending-card-selector')
    for card_index,card in enumerate(cards):
        scope=n.flatten(card);f={k:n.review_field_literal(n.one(scope,{'attributes':{'class':clname}},k),k,profile.get('text_schema')) for k,clname in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf')]}
        bodies=[x for x in scope if cl(x)=='text-Hl9jZe'];body_evidence={}
        if not bodies and profile.get('image_only_text_schema')==IMAGE_ONLY_SCHEMA:
            f['text'],body_evidence=image_only_export_body(card,f['store'],f['customer'],exported,receipt['source'],receipt['src_sha256'])
        else:f['text']=n.review_field_literal(n.one(scope,{'attributes':{'class':'text-Hl9jZe'}},'text'),'text',profile.get('text_schema'))
        acts=[x for x in scope if not x.get('children') and x.get('name') in ('投诉','查看投诉结果','投诉审核中')];need(len(acts)==1,'normal-page-action')
        # An explicitly history-only collector can retain a genuinely blank
        # store as unresolved evidence. It never enriches from a two-field match,
        # invents an ID/star, or places this card among authoritative rows.
        if pending_policy and not f['store']:
            store_nodes=[x for x in scope if cl(x)=='poiName-W9HDFV'];need(len(store_nodes)==1 and not store_nodes[0].get('children') and bool(f['customer']) and bool(f['text']),'normal-pending-store-shape')
            pending.append({'kind':'unresolved-normal-card-v1','reason':'missing-visible-store','company':job['company'],'groupid':str(job['groupid']),'start':job['start'],'end_exclusive':job['end_exclusive'],'page_index':pg['page'],'card_index':card_index,'dom_selector':card['selector'],'card_sha256':A.data_hash(card),'customer':f['customer'],'text':f['text'],'action':acts[0]['name'],'source_receipt':receipt_ref,'source_sha256':receipt['src_sha256'],'matched':False,'complaint_candidate':False})
            continue
        matches=[x for x in exported if x['match']==(f['store'],f['customer'],f['text'])];need(len(matches)==1 and matches[0]['stars']<=3,'normal-page-current-exact-negative-join')
        rows.append({**f,**body_evidence,'action':acts[0]['name'],'section':'filtered','text_complete':True,'dom_selector':card['selector'],'page_index':pg['page'],'review_id':matches[0]['review_id']})
    need(len({x['review_id'] for x in rows})==len(rows),'normal-page-duplicate')
    result={'contract':CONTRACT,'page_sha256':A.data_hash(page),'scope':{'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'tabId':tab['tabId'],'windowId':tab['windowId'],'url':tab['url'],'start':job['start'],'end_exclusive':job['end_exclusive'],'receipt_sha256':receipt_ref['sha256'],'source_sha256':receipt['src_sha256']},'normal_header_count':count,'pager':pg,'rows':rows,'observed_at':page['observed_at'],'terminal_boundary':({'selector':boundaries[0][1]['selector'],'direct_normal_cards_before_boundary':len(cards),'folded_text_read':False} if boundaries else None),'all_normal_read':False,'profile_live_validated':False}
    if pending_policy:result.update(pending_rows=pending,visible_normal_card_count=len(cards),pending_policy=pending_policy)
    return result

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
        keys=('scope','normal_header_count','pager','rows','terminal_boundary')+ (('pending_rows','visible_normal_card_count')if profile.get('pending_card_policy')else())
        need(all(before[k]==after[k] for k in keys),'normal-page-not-stable')
        stable.append([before['page_sha256'],after['page_sha256']])
    proofs=[inspect_page(job,p,profile,receipt_ref) for p in pages];need(proofs,'normal-pages-required');first=proofs[0];seen=set();rows=[];pending=[];pending_keys=set();previous=None
    for index,p in enumerate(proofs,1):
        need(p['scope']==first['scope'] and p['normal_header_count']==first['normal_header_count'] and p['pager']['platform_pager_total']==first['pager']['platform_pager_total'] and p['pager']['pages']==first['pager']['pages'],'normal-page-scope-changed')
        need(p['pager']['page']==index,'normal-page-sequence')
        need(previous is None or A.stamp(p['observed_at'])>=previous,'normal-page-time-reversed');previous=A.stamp(p['observed_at'])
        need(bool(p['terminal_boundary'])==(index==len(proofs)),'normal-terminal-boundary-required-no-pages-after-fold')
        if index<len(proofs):need(len(p['rows'])+len(p.get('pending_rows',[]))==10 and not p['pager']['next_disabled'],'normal-intermediate-page-incomplete')
        for row in p['rows']:need(row['review_id'] not in seen,'normal-page-repeat');seen.add(row['review_id']);rows.append(row)
        for row in p.get('pending_rows',[]):
            key=(row['page_index'],row['dom_selector']);need(key not in pending_keys,'normal-pending-repeat');pending_keys.add(key);pending.append(row)
    need(len(rows)+len(pending)==first['normal_header_count'],'normal-unique-coverage-incomplete')
    if pending:
        return {'contract':CONTRACT,'normal_scope_mode':CONTRACT,'state':'needs-review','all_normal_read':False,'all_pages_read':True,'source_verified':False,'filtered_count':first['normal_header_count'],'verified_count':len(rows),'pending_count':len(pending),'platform_pager_total':first['pager']['platform_pager_total'],'observed_normal_pages':len(proofs),'normal_end':'actual-direct-fold-boundary','folded_rows_observed':None,'folded_text_read':False,'rows':rows,'pending_rows':pending,'proofs':proofs,'stable_page_pair_sha256s':stable,'complaint_admission':False}
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


def partial_history_delivery(job,pages,profile,receipt_ref,*,stable_pairs):
    """Independent verified existing-result candidates, never a full source.
    A missing store is recorded separately and is never enriched or assigned ID.
    This payload cannot satisfy joined_envelope/history._inputs.
    """
    need(profile.get('pending_card_policy')=='history-unresolved-store-v1' and bool(pages) and len(pages)==len(stable_pairs),'history-partial-explicit-pages-required')
    proofs=[];seen=set();pending=[];verified=[];pairs=[]
    for index,(page,pair)in enumerate(zip(pages,stable_pairs),1):
        need(isinstance(pair,list) and len(pair)==2 and A.data_hash(pair[1])==A.data_hash(page),'history-partial-stable-pair')
        before=inspect_page(job,pair[0],profile,receipt_ref);after=inspect_page(job,page,profile,receipt_ref)
        need(A.stamp(before['observed_at'])<A.stamp(after['observed_at']) and all(before.get(k)==after.get(k)for k in('scope','normal_header_count','pager','rows','terminal_boundary','pending_rows','visible_normal_card_count')),'history-partial-page-not-stable')
        need(after['pager']['page']==index and (not proofs or all(after[k]==proofs[0][k]for k in('scope','normal_header_count'))),'history-partial-page-sequence')
        need(not proofs or all(after['pager'][k]==proofs[0]['pager'][k]for k in('pages','platform_pager_total')),'history-partial-pager-scope-changed')
        need(not proofs or not proofs[-1]['terminal_boundary'],'history-partial-page-after-fold')
        for row in after['rows']:
            need(row['review_id']not in seen,'history-partial-repeat');seen.add(row['review_id']);verified.append(row)
        pending+=after.get('pending_rows',[]);proofs.append(after);pairs.append([before['page_sha256'],after['page_sha256']])
    count=sum(len(x['rows'])+len(x.get('pending_rows',[]))for x in proofs);need(count<=proofs[0]['normal_header_count'],'history-partial-count-overflow')
    receipt=json.loads(Path(receipt_ref['path']).read_bytes());exported,_=A.load_export(receipt['source'],job,receipt);candidates=[];skipped=[]
    for row in verified:
        exact=[x for x in exported if x['review_id']==row['review_id'] and x['match']==(row['store'],row['customer'],row['text'])];need(len(exact)==1 and exact[0]['stars']<=3,'history-partial-current-export-row')
        item={'review_key':str(job['groupid'])+':'+row['review_id'],'row':{k:v for k,v in exact[0].items()if k!='match'},'action':row['action'],'page_index':row['page_index'],'dom_selector':row['dom_selector'],'use':'existing-complaint-readonly-check-only','new_complaint_authorized':False}
        if row['action']in('查看投诉结果','投诉审核中'):candidates.append(item)
        else:need(row['action']=='投诉','history-partial-unreviewed-action');skipped.append({'review_key':item['review_key'],'reason':'uncomplained-not-a-history-result'})
    return {'kind':'history-partial-existing-result-candidates-v1','company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],'coverage':'needs-review','all_normal_read':False,'authoritative_full_source':False,'observed_cards':count,'normal_header_count':proofs[0]['normal_header_count'],'verified_count':len(verified),'pending_count':len(pending),'fold_boundary_observed':bool(proofs[-1]['terminal_boundary']),'case_candidates':candidates,'uncomplained_skipped':skipped,'pending_records':pending,'source_receipt':receipt_ref,'source_sha256':receipt['src_sha256'],'page_sha256s':[x['page_sha256']for x in proofs],'stable_page_pair_sha256s':pairs,'profile_sha256':A.data_hash(profile),'no_submission':True,'no_send':True}

def _partial_history_source_uncached(job,envelope,profile,receipt_ref):
    need(envelope.get('source')=='local-dom-bridge'and envelope.get('company')==job['company']and str(envelope.get('groupid'))==str(job['groupid']),'history-partial-envelope-scope')
    identity=envelope.get('identity_evidence',{});tab,tree=n.context(identity,job['groupid']);n.public_identity(tree,job['identity'])
    delivery=partial_history_delivery(job,envelope['pages'],profile,receipt_ref,stable_pairs=envelope['stable_page_pairs']);proofs=[inspect_page(job,x,profile,receipt_ref)for x in envelope['pages']]
    need(tab['tabId']==proofs[0]['scope']['tabId']and tab.get('windowId')==proofs[0]['scope']['windowId']and A.stamp(identity['observed_at'])<=A.stamp(envelope['pages'][0]['observed_at']),'history-partial-identity-anchor')
    rows=[{**x['row'],'section':'filtered','folded':False,'action':x['action'],'dom_selector':x['dom_selector'],'page_index':x['page_index']}for x in delivery['case_candidates']]
    return {'kind':'history-partial-normal-source-v1','company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'source':'local-dom-bridge','account_verified':True,'start':job['start'],'end_exclusive':job['end_exclusive'],'url':envelope['pages'][-1]['tab']['url'],'observed_at':envelope['pages'][-1]['observed_at'],'normal_scope_mode':CONTRACT,'filtered_count':delivery['normal_header_count'],'rows':rows,'proofs':proofs,'delivery':delivery,'coverage':'needs-review','all_normal_read':False,'authoritative_full_source':False,'new_complaint_authorized':False,'all_pages_read':delivery['fold_boundary_observed']}

def joined_envelope(job,envelope,profile,receipt_ref):
    arguments={'job':job,'envelope':envelope,'profile':profile,'receipt_ref':receipt_ref}
    return source_proof_session.reconstruct(arguments,lambda:_joined_envelope_uncached(job,envelope,profile,receipt_ref))

def _joined_envelope_uncached(job,envelope,profile,receipt_ref):
    need(envelope.get('source')=='local-dom-bridge' and envelope.get('company')==job['company'] and str(envelope.get('groupid'))==str(job['groupid']),'normal-paged-envelope-scope')
    identity=envelope.get('identity_evidence',{});tab,tree=n.context(identity,job['groupid']);n.public_identity(tree,job['identity'])
    final=finalize_pages(job,envelope.get('pages',[]),profile,receipt_ref,stable_pairs=envelope.get('stable_page_pairs'))
    need(final.get('all_normal_read')is True and not final.get('pending_rows'),'normal-unresolved-cards-cannot-be-authoritative-source');first=final['proofs'][0];need(tab['tabId']==first['scope']['tabId'] and tab.get('windowId')==first['scope']['windowId'] and A.stamp(identity['observed_at'])<=A.stamp(final['proofs'][0]['observed_at']),'normal-paged-identity-anchor')
    observation={**final,'company':job['company'],'groupid':str(job['groupid']),'source':'local-dom-bridge','url':envelope['pages'][-1]['tab']['url'],'observed_at':envelope['pages'][-1]['observed_at'],'account_verified':True,'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],'negative_filter':'中差评（1-3心）','filter_active':True,'other_filters':{'评价类型':'全部','评价来源':'全部','评价状态':'全部'},'fold_boundary_verified':True,'profile_sha256':A.data_hash(profile),'identity_evidence_sha256':A.data_hash(identity),'count_semantics':{'filtered_count':'complete-normal-filtered-input','platform_pager_total':'platform-displayed-record-count-not-a-folded-count'},'observed_folded':None,'folded_scope':'not-traversed-not-included'}
    return A.join(job,observation,receipt_ref['path'],receipt_ref['sha256'])


def current_page_for_case(page,job,envelope,profile,source,row):
    """Pure result-reader guard; never navigates. Caller must arrive at case page.
    Full original source is replayed first, not replaced by a partial observation.
    """
    receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']}
    reconstructed=partial_history_source(job,envelope,profile,receipt_ref,expected_source=source)if source.get('kind')=='history-partial-normal-source-v1'else joined_envelope(job,envelope,profile,receipt_ref)
    need(reconstructed==source,'normal-case-complete-source-required')
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

# Explicit one-command history-only memo. No ledger, current page, UI or task
# state enters this cache. Every caller still verifies its pinned input refs.
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from collections import OrderedDict
_PARTIAL_COMMAND=ContextVar('normal_partial_source_command',default=None)
_PARTIAL_VERSION='immutable-partial-source-command-v1'
_PARTIAL_CAP=64*1024*1024
_PARTIAL_MAX=8

def _partial_file_token(path):
 path=Path(path);need(path.is_absolute() and path.resolve()==path and not any(x.is_symlink()for x in(path,*path.parents)),'partial-memo-canonical-dependency')
 st=path.stat();need(path.is_file(),'partial-memo-file-dependency')
 return (str(path),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)

def _partial_code_token():
 from types import FunctionType,ModuleType
 modules=(sys.modules[__name__],n,body,A,A.export_parse_session)
 rows=[];paths=[]
 for module in modules:
  paths.append(str(Path(module.__file__).resolve()))
  rows.append((module,tuple(sorted((k,x,x.__code__,repr(x.__defaults__),repr(x.__kwdefaults__))for k,x in vars(module).items()if isinstance(x,FunctionType)))))
 return tuple(rows),paths

@contextmanager
def partial_source_command_scope():
 current=_PARTIAL_COMMAND.get()
 if current is not None:yield current['stats'];return
 state={'entries':OrderedDict(),'bindings':{},'bytes':0,'stats':{'compute':0,'hits':0,'invalidated':0,'evictions':0,'bypass':0}};token=_PARTIAL_COMMAND.set(state)
 try:yield state['stats']
 finally:state['entries'].clear();state['bindings'].clear();_PARTIAL_COMMAND.reset(token)

def partial_source_command(function):
 @wraps(function)
 def wrapped(*args,**kwargs):
  with partial_source_command_scope():return function(*args,**kwargs)
 return wrapped

def partial_history_source(job,envelope,profile,receipt_ref,*,expected_source=None,expected_source_ref=None):
 owner=_PARTIAL_COMMAND.get()
 if owner is None or expected_source is None:return _partial_history_source_uncached(job,envelope,profile,receipt_ref)
 semantic=A.data_hash(expected_source)
 if expected_source_ref is not None:
  need(set(expected_source_ref)=={'path','sha256'} and A.digest(expected_source_ref['path'])==expected_source_ref['sha256'],'partial-memo-original-source-changed')
  need(json.loads(Path(expected_source_ref['path']).read_bytes())==expected_source,'partial-memo-source-semantic-mismatch')
  old=owner['bindings'].get(semantic);need(old is None or old==expected_source_ref,'partial-memo-source-ref-conflict')
  if old is None:
   if len(owner['bindings'])>=_PARTIAL_MAX:owner['stats']['bypass']+=1;return _partial_history_source_uncached(job,envelope,profile,receipt_ref)
   owner['bindings'][semantic]=copy.deepcopy(expected_source_ref)
 source_ref=owner['bindings'].get(semantic)
 if source_ref is None:owner['stats']['bypass']+=1;return _partial_history_source_uncached(job,envelope,profile,receipt_ref)
 api,codepaths=_partial_code_token();receipt=json.loads(Path(receipt_ref['path']).read_bytes())
 paths=sorted(set(codepaths+[source_ref['path'],receipt_ref['path'],receipt['source']]+([profile['terminal_layout']['approved_page']['path']]if profile.get('terminal_layout',{}).get('approved_page')else[])))
 tokens=tuple(_partial_file_token(x)for x in paths)
 key=(_PARTIAL_VERSION,source_ref['path'],source_ref['sha256'],semantic,A.data_hash({'job':job,'envelope':envelope,'profile':profile,'receipt_ref':receipt_ref}))
 entry=owner['entries'].get(key)
 if entry is not None:
  if entry['tokens']==tokens and entry['api']==api:
   owner['entries'].move_to_end(key);owner['stats']['hits']+=1;return copy.deepcopy(entry['result'])
  owner['bytes']-=entry['weight'];owner['entries'].pop(key);owner['stats']['invalidated']+=1
 need(A.digest(source_ref['path'])==source_ref['sha256'],'partial-memo-original-source-changed')
 owner['stats']['compute']+=1;value=_partial_history_source_uncached(job,envelope,profile,receipt_ref)
 need(value==expected_source,'partial-memo-reconstructed-source-changed')
 if tokens!=tuple(_partial_file_token(x)for x in paths) or _partial_code_token()[0]!=api:owner['stats']['bypass']+=1;return value
 # Serialized result bound also bounds the retained deepcopy, with a conservative
 # factor; oversized entries bypass without clearing unrelated facts.
 weight=len(json.dumps(value,ensure_ascii=False).encode())*8+4096
 if weight>_PARTIAL_CAP:owner['stats']['bypass']+=1;return value
 while owner['entries'] and (len(owner['entries'])>=_PARTIAL_MAX or owner['bytes']+weight>_PARTIAL_CAP):
  _,removed=owner['entries'].popitem(last=False);owner['bytes']-=removed['weight'];owner['stats']['evictions']+=1
 owner['entries'][key]={'tokens':tokens,'api':api,'result':copy.deepcopy(value),'weight':weight};owner['bytes']+=weight
 return value
