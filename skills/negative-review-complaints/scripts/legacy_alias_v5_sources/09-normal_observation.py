#!/usr/bin/env python3
"""Offline normal-review DOM intake -> exact current-export join. No UI/actions.
No platform ID/absolute UI date/rating is invented: authoritative_join supplies
those fields only after an exact globally-unique current XLSX match.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,hashlib,json,re,sys
from datetime import date,timedelta
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import authoritative_join as authority
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'douyin-laike-operator/scripts'))
from dom_evidence import identity as public_identity

BACKEND='local-dom-bridge'
def need(ok,code):
    if not ok:raise ValueError(code)
def matcher(node,rule):
    need(isinstance(rule,dict) and rule and not set(rule)-{'selector','role','name','attributes'},'profile-matcher-invalid')
    return all(node.get(k)==v for k,v in rule.items() if k!='attributes') and all(node.get('attributes',{}).get(k)==v for k,v in rule.get('attributes',{}).items())
def one(nodes,rule,label):
    result=[n for n in nodes if matcher(n,rule)];need(len(result)==1,'node-not-unique:'+label);return result[0]
def flatten(root):
    out=[]
    def walk(n):
        need(isinstance(n,dict) and isinstance(n.get('children',[]),list),'tree-node-invalid');out.append(n)
        for c in n.get('children',[]):walk(c)
    walk(root);return out

def literal(node):
    # The bridge's public name is capped at 800. Never promote a capped value,
    # aggregate subtree or shortened ellipsis to a complete source body.
    need(not node.get('children'),'aggregate-text-needs-live-leaf-profile')
    value=node.get('attributes',{}).get('value',node.get('name'))
    need(isinstance(value,str) and len(value)<800 and node.get('truncated') is not True,'public-text-may-be-truncated')
    return authority.normalized(value)
def review_field_literal(node,field,text_schema=None):
    if field=='text' and text_schema=='public-visible-text-v2':
        evidence=node.get('public_visible_text',{})
        need(evidence.get('method')=='visible-innerText-v1' and evidence.get('complete') is True,'public-visible-body-evidence-required')
        value=evidence.get('value')
        need(isinstance(value,str) and len(value)<=16000,'public-visible-body-may-be-truncated')
        return authority.normalized(value)
    # Actual normal Shanghai card has the same empty presentation chevron as
    # the independently reviewed result drawer. Preserve public body verbatim.
    if field=='text' and node.get('children'):
        children=node['children']
        need(len(children)==1 and children[0].get('tag')=='svg' and children[0].get('role')=='presentation' and children[0].get('attributes',{}).get('class')=='icon-K1rG1b','normal-body-unreviewed-children')
        need(all(n.get('tag') in ('svg','g','path') and not n.get('name') for n in flatten(children[0])),'normal-body-child-text-or-control')
        node={**node,'children':[]}
    return literal(node)

def context(page,gid):
    tab=page.get('tab',{});u=urlsplit(tab.get('url',''))
    need(type(tab.get('tabId')) is int and tab['tabId']>0 and tab.get('allowed') is True,'explicit-allowed-tab-required')
    need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/life_comment/management' and parse_qs(u.query).get('groupid')==[str(gid)],'normal-tab-context-mismatch')
    tree=page.get('tree',{});need(tree.get('kind')=='DOM-derived semantic tree (not native AX)' and tree.get('truncated') is False and tree.get('url')==u.scheme+'://'+u.netloc+u.path,'complete-current-dom-tree-required')
    authority.stamp(page.get('observed_at'));flatten(tree.get('root'))
    return tab,tree

def empty_normal_list(root):
    """Observed zero state, not a claim about other sections of the page."""
    children=root.get('children',[])
    need(len(children)==2,'empty-normal-list-shape-unverified')
    header,empty=children
    need(set(header.get('attributes',{}).get('class','').split())=={'header-sQid1u','commentListHeader-jKdTh_'},'empty-normal-header-unverified')
    counts=[literal(x) for x in flatten(header) if not x.get('children') and re.fullmatch(r'已筛选\s*\d+\s*条',x.get('name',''))]
    need(counts==['已筛选0条'],'empty-normal-count-unverified')
    need(set(empty.get('attributes',{}).get('class','').split())=={'empty-_JoRz3','isPC-PMji6M'},'empty-normal-placeholder-unverified')
    es=empty.get('children',[]);need(len(es)==2 and es[0].get('tag')=='img' and not es[0].get('name') and not es[0].get('children'),'empty-normal-decoration-unverified')
    need(es[1].get('attributes',{}).get('class')=='text-Ll5e7y' and literal(es[1])=='暂无相关评价','empty-normal-label-unverified')
    scope=flatten(root)
    need(not any('commentItem-jrXo5p' in x.get('attributes',{}).get('class','').split() or 'foldTitleContainer-DwIByI' in x.get('attributes',{}).get('class','').split() or re.fullmatch(r'\d+/\d+',x.get('name','')) for x in scope),'empty-normal-has-record-or-pagination')
    return {'kind':'verified-empty-normal-list','fold_boundary_applicable':False,'folded_traversed':False,'observed_folded':None,'pagination':'empty-no-pagination'}

def complete_normal_list(root,count):
    """Exact observed header/cards/disabled single-page pager, without fold UI."""
    need(type(count) is int and 0<count<=10,'complete-normal-count-invalid')
    children=root.get('children',[]);need(len(children)==count+2,'complete-normal-direct-shape-unverified')
    head,*cards,pager=children
    need(set(head.get('attributes',{}).get('class','').split())=={'header-sQid1u','commentListHeader-jKdTh_'},'complete-normal-header-unverified')
    labels=[literal(x) for x in flatten(head) if not x.get('children') and re.fullmatch(r'已筛选\s*\d+\s*条',x.get('name',''))]
    need(labels==['已筛选'+str(count)+'条'],'complete-normal-header-count-mismatch')
    need(all(x.get('attributes',{}).get('class')=='commentItem-jrXo5p' for x in cards),'complete-normal-card-shape-unverified')
    need(not any('foldTitleContainer-DwIByI' in x.get('attributes',{}).get('class','').split() for x in flatten(root)),'complete-normal-has-fold-section')
    need(pager.get('attributes',{}).get('class')=='pagination-GXvAPk' and len(pager.get('children',[]))==2,'complete-normal-pagination-unverified')
    total,group=pager['children'];need(total.get('attributes',{}).get('class')=='text-bjyZFG' and literal(total)=='共'+str(count)+'条记录','complete-normal-total-mismatch')
    need(group.get('attributes',{}).get('class')=='buttonGroup-GDbp9Y' and len(group.get('children',[]))==3,'complete-normal-pager-group-unverified')
    previous,current,nxt=group['children'];need(current.get('attributes',{}).get('class')=='text-bjyZFG' and literal(current)=='1/1','complete-normal-not-single-page')
    need(all(set(x.get('attributes',{}).get('class','').split())=={'button-j4VxiA','isDisabled-unTBS6'} and not x.get('name') for x in (previous,nxt)),'complete-normal-page-buttons-not-disabled')
    return {'kind':'verified-complete-normal-list','fold_boundary_applicable':False,'folded_traversed':False,'observed_folded':None,'normal_count':count,'pagination':'1/1'}

def observation(job,envelope,profile):
    need(profile.get('status')=='live-validated' and profile.get('revision'),'normal-profile-awaiting-live-validation')
    need(profile.get('kind')=='normal-review-observation-v1','normal-profile-kind-invalid')
    need(profile.get('company')==job.get('company') and str(profile.get('groupid'))==str(job.get('groupid')),'normal-profile-company-mismatch')
    need(envelope.get('source')==BACKEND,'normal-backend-mismatch')
    need(envelope.get('company')==job.get('company') and str(envelope.get('groupid'))==str(job.get('groupid')),'normal-company-mismatch')
    identity_evidence=envelope.get('identity_evidence',{});identity_tab,identity_tree=context(identity_evidence,job['groupid'])
    need(job.get('account_verified') is True,'job-account-unverified');public_identity(identity_tree,job['identity'])
    pages=envelope.get('pages');need(isinstance(pages,list) and pages,'normal-pages-required')
    need(profile.get('fold_boundary') or profile.get('normal_root_exclusive') is True,'normal-section-profile-unverified')
    need(profile.get('pagination_mode') in ('count-complete','explicit-pages'),'pagination-profile-required')
    complete_mode=profile.get('scope_mode')=='verified-complete-normal-list'
    complete_proof=None
    empty_mode=profile.get('scope_mode')=='verified-empty-normal-list'
    empty_proof=None
    all_rows=[];count=None;seen_selectors=set();page_hashes=[];last_time=authority.stamp(identity_evidence['observed_at'])
    for index,page in enumerate(pages,1):
        tab,tree=context(page,job['groupid']);need(tab['tabId']==identity_tab['tabId'],'normal-source-tab-changed')
        observed=authority.stamp(page['observed_at']);need(observed>=last_time,'normal-evidence-time-reversed');last_time=observed
        nodes=flatten(tree['root']);root=one(nodes,profile['normal_root'],'normal-root');scope=flatten(root)
        boundary=one(nodes,profile['fold_boundary'],'fold-boundary') if profile.get('fold_boundary') else None
        cutoff=next((i for i,n in enumerate(nodes) if n is boundary),len(nodes))
        need(next(i for i,n in enumerate(nodes) if n is root)<cutoff,'normal-root-after-fold-boundary')
        active=one(nodes,profile['negative_filter'],'negative-filter');attrs=active.get('attributes',{})
        need(literal(active)=='中差评（1-3心）','negative-label-mismatch')
        need(attrs.get('aria-selected')=='true' or attrs.get('aria-pressed')=='true' or profile.get('active_class') in attrs.get('class','').split() and bool(profile.get('active_class')),'normal-negative-not-selected')
        end=(date.fromisoformat(job['end_exclusive'])-timedelta(days=1)).isoformat()
        need(literal(one(nodes,profile['date_filter'],'date-filter'))==job['start']+' ~ '+end,'normal-date-filter-mismatch')
        for label in ('评价类型','评价来源','评价状态'):
            need(literal(one(nodes,profile['other_filters'][label],label))=='全部','nondefault-review-filter:'+label)
        header=literal(one(nodes,profile['filtered_count'],'filtered-count'));m=re.fullmatch(r'(?:评价\s*)?已筛选\s*(\d+)\s*条',header);need(m is not None,'normal-filtered-count-unverified')
        current=int(m[1]);need(count is None or count==current,'normal-count-changed');count=current
        if empty_mode:
            one(scope,profile['filtered_count'],'empty-normal-contained-count')
            need(current==0 and profile.get('normal_root_exclusive') is True and not profile.get('fold_boundary'),'empty-normal-profile-invalid')
            empty_proof=empty_normal_list(root)
        if complete_mode:
            need(current>0 and profile.get('normal_root_exclusive') is True and not profile.get('fold_boundary'),'complete-normal-profile-invalid')
            complete_proof=complete_normal_list(root,current)
        rows=[n for n in scope if matcher(n,profile['row']) and next(i for i,x in enumerate(nodes) if x is n)<cutoff]
        for row in rows:
            need(row.get('selector') and (index,row['selector']) not in seen_selectors,'duplicate-normal-card');seen_selectors.add((index,row['selector']))
            children=flatten(row);fields={k:review_field_literal(one(children,profile[k],k),k,profile.get('text_schema')) for k in ('store','customer','action')};body={}
            if not [x for x in children if matcher(x,profile['text'])] and profile.get('image_only_text_schema'):
                import normal_review_body as rb
                fields['text'],body=rb.for_card(job,row,fields['store'],fields['customer'],profile)
            else:fields['text']=review_field_literal(one(children,profile['text'],'text'),'text',profile.get('text_schema'))
            need(fields['store'] and fields['customer'] and fields['action'] in ('投诉','查看投诉结果','投诉审核中'),'normal-review-fields-invalid')
            all_rows.append({**fields,**body,'section':'filtered','text_complete':True,'dom_selector':row['selector'],'page_index':index,'star_dom_value_verified':False})
        if profile['pagination_mode']=='explicit-pages':
            need(literal(one(nodes,profile['current_page'],'current-page'))==str(index),'normal-page-sequence-unverified')
            nxt=one(nodes,profile['next_page'],'next-page');disabled=nxt.get('disabled') is True or nxt.get('attributes',{}).get('aria-disabled')=='true'
            need(disabled==(index==len(pages)),'normal-page-end-unverified')
        else:need(len(pages)==1,'count-complete-requires-single-tree')
        page_hashes.append(authority.data_hash(page))
    need(len(all_rows)==count,'normal-pagination-count-incomplete')
    result={'company':job['company'],'groupid':str(job['groupid']),'source':BACKEND,'url':pages[-1]['tab']['url'],'observed_at':pages[-1]['observed_at'],
        'account_verified':True,'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],
        'negative_filter':'中差评（1-3心）','filter_active':True,'other_filters':{k:'全部' for k in ('评价类型','评价来源','评价状态')},
        'fold_boundary_verified':True,'all_pages_read':True,'filtered_count':count,'rows':all_rows,
        'normal_dom_binding':{'profile_revision':profile['revision'],'profile_sha256':authority.data_hash(profile),'identity_evidence_sha256':authority.data_hash(identity_evidence),'page_sha256':page_hashes,'exact_public_name_only':True,'screenshot_proof':False}}
    # Preserve byte-level reconstruction of historical pinned profiles. New
    # reviewed profiles explicitly opt into the clarified count schema.
    if complete_mode:result.update(normal_scope_mode='verified-complete-normal-list',normal_scope_proof=complete_proof)
    if empty_mode:result.update(normal_scope_mode='verified-empty-normal-list',normal_scope_proof=empty_proof)
    if profile.get('count_schema')=='normal-input-counts-v2':
        result.update(count_semantics={'filtered_count':'complete-normal-filtered-input','excluded_folded_count':'folded-rows-in-input-only'},observed_folded=None,folded_scope='not-traversed-not-included')
    return result

def navigation_probe(tree,job,text_schema=None,image_only_text_schema=None):
    """Observed Yantai normal-list structure; read-only settling gate, not capture.
    A changed structure/pagination remains a profile gap. Folded bodies ignored.
    """
    from dom_evidence import nodes,review_filter_fields,all_store_scope
    all_store_scope(tree);fields=review_filter_fields(tree)
    end=(date.fromisoformat(job['end_exclusive'])-timedelta(days=1)).isoformat()
    need(fields['评价时间']['attributes'].get('value')==job['start']+' ~ '+end,'normal-probe-date-not-applied')
    need(all(fields[k]['attributes'].get('value')=='全部' for k in ('评价类型','评价来源','评价状态')),'normal-probe-other-filter')
    ns=list(nodes(tree));selected=one(ns,{'name':'中差评（1-3心）'},'negative')
    need('isSelected-ov8pOi' in selected.get('attributes',{}).get('class','').split(),'normal-probe-not-selected')
    byclass=lambda scope,cl:[x for x in scope if cl in x.get('attributes',{}).get('class','').split()]
    lists=byclass(ns,'commentList-hkujq4');need(len(lists)==1,'normal-probe-list-unverified');ls=lists[0];scope=flatten(ls)
    heads=byclass(scope,'header-sQid1u');need(len(heads)==1,'normal-probe-header-unverified')
    counts=[literal(x) for x in flatten(heads[0]) if not x.get('children') and re.fullmatch(r'已筛选\s*\d+\s*条',x.get('name',''))]
    need(len(counts)==1,'normal-probe-count-unverified');count=int(re.search(r'\d+',counts[0])[0])
    boundaries=byclass(scope,'foldTitleContainer-DwIByI')
    if count==0 and not boundaries:
        empty_proof=empty_normal_list(ls);boundary=None;cards=[];pagination='empty-no-pagination'
    elif count>0 and not boundaries:
        complete_proof=complete_normal_list(ls,count);boundary=None;cards=byclass(scope,'commentItem-jrXo5p');pagination='1/1'
    else:
        need(len(boundaries)==1,'normal-probe-fold-boundary-required')
        boundary=boundaries[0];cut=next(i for i,n in enumerate(scope) if n is boundary)
        cards=[x for x in scope[:cut] if 'commentItem-jrXo5p' in x.get('attributes',{}).get('class','').split()]
        need(len(cards)==count,'normal-probe-loading-or-incomplete')
        page_labels=[x.get('name') for x in scope if not x.get('children') and re.fullmatch(r'\d+/\d+',x.get('name',''))]
        need(page_labels==['1/1'],'normal-probe-pagination-needs-profile');pagination='1/1'
    receipt_path=job.get('source_receipt');need(receipt_path and authority.digest(receipt_path)==job.get('source_receipt_sha256'),'normal-probe-current-receipt-required')
    r=json.loads(Path(receipt_path).read_text());need(r.get('work_order_id')==job.get('source_work_order_id') and r.get('company')==job['company'] and str(r.get('groupid'))==str(job['groupid']) and r.get('identity')==job['identity'],'normal-probe-source-scope-mismatch')
    need(r.get('download_verified') is True and r.get('source_is_authoritative_export') is True and r.get('account_verified') is True and r.get('identity_before')==job['identity'] and r.get('date_range')=={'start':job['start'],'end':end},'normal-probe-source-unverified')
    need(authority.digest(r['source'])==r['src_sha256'],'normal-probe-source-changed')
    exported,_=authority.load_export(r['source'],job,r);matched=[]
    if count==0 and boundary is None:need(not any(x['stars']<=3 for x in exported),'empty-normal-export-negative-conflict')
    for card in cards:
        cs=flatten(card);f={}
        for key,cl in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf')]:
            found=byclass(cs,cl);need(len(found)==1,'normal-probe-field-unverified:'+key);f[key]=review_field_literal(found[0],key,text_schema)
        bodies=byclass(cs,'text-Hl9jZe')
        if not bodies and image_only_text_schema:
            import normal_review_body as rb
            f['text'],_=rb.resolve(card,f['store'],f['customer'],{'image_only_text_schema':image_only_text_schema},exported,r['source'],r['src_sha256'])
        else:need(len(bodies)==1,'normal-probe-field-unverified:text');f['text']=review_field_literal(bodies[0],'text',text_schema)
        actions=[literal(x) for x in cs if not x.get('children') and x.get('name') in ('投诉','查看投诉结果','投诉审核中')]
        need(len(actions)==1,'normal-probe-action-unverified')
        matches=[x for x in exported if x['match']==(f['store'],f['customer'],f['text'])]
        need(len(matches)==1 and matches[0]['stars']<=3,'normal-probe-current-negative-match-not-unique')
        matched.append({'review_id':matches[0]['review_id'],'action':actions[0],'selector':card['selector']})
    need(len({x['review_id'] for x in matched})==len(matched),'normal-probe-duplicate-review')
    result={'date_range':{'start':job['start'],'end_exclusive':job['end_exclusive']},'normal_count':count,'normal_rows':matched,'boundary_selector':boundary['selector'] if boundary else None,'pagination':pagination,'source_sha256':r['src_sha256']}
    if boundary is None:
        result.update(normal_scope_mode='verified-empty-normal-list' if count==0 else 'verified-complete-normal-list',normal_scope_proof=empty_proof if count==0 else complete_proof)
    return result

def joined(job,envelope,profile,receipt_path,receipt_sha256):
    if profile.get('contract')=='normal-negative-pages-until-observed-fold-boundary-v1':
        from normal_paging import joined_envelope
        return joined_envelope(job,envelope,profile,{'path':receipt_path,'sha256':receipt_sha256})
    observed=observation(job,envelope,profile)
    # Raw DOM text remains unchanged. Whitespace-compressed/partial/capped body
    # cannot match: no fuzzy source enrichment, guessed IDs or relative dates.
    return authority.join(job,observed,receipt_path,receipt_sha256)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('job','envelope','profile','profile-sha256','receipt','receipt-sha256','out'):p.add_argument('--'+key,required=True)
    a=p.parse_args()
    try:
        need(authority.digest(a.profile)==a.profile_sha256,'normal-profile-file-hash-mismatch')
        read=lambda x:json.loads(Path(x).read_text());job=read(a.job);envelope=read(a.envelope);profile=read(a.profile)
        result=joined(job,envelope,profile,a.receipt,a.receipt_sha256);need(authority.digest(a.profile)==a.profile_sha256,'normal-profile-changed')
        out=Path(a.out);need(not out.exists(),'output-exists-refuse-overwrite');out.parent.mkdir(parents=True,exist_ok=True)
        with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
        print(json.dumps({'ok':True,'output':str(out.resolve()),'normal_rows':len(result['rows']),'submission_enabled':False,'live_profile_accepted_by_this_command':False},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,TypeError) as error:print(json.dumps({'ok':False,'error':str(error),'submission_enabled':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
