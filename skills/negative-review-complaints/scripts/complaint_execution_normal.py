"""Known single-page normal-list profile derived from actual public DOM.
Every result is replayed by normal.joined; no count-only completeness shortcut.
Unknown/multi-page shapes stop at the original navigation_probe guard.
"""
import re
import normal_observation as n

def derive(job,page,image_only_text_schema=None):
    n.context(page,job['groupid']);proof=n.navigation_probe(page['tree'],job,text_schema='public-visible-text-v2',image_only_text_schema=image_only_text_schema)
    ns=n.flatten(page['tree']['root']);roots=[x for x in ns if 'commentList-hkujq4' in x.get('attributes',{}).get('class','').split()]
    n.need(len(roots)==1,'parent-normal-root-not-unique');root=roots[0]
    counts=[x for x in n.flatten(root) if not x.get('children') and re.fullmatch(r'已筛选\s*\d+\s*条',x.get('name',''))]
    n.need(len(counts)==1 and counts[0].get('selector'),'parent-normal-count-not-unique')
    cards=[x for x in n.flatten(root) if x.get('selector') in {r['selector'] for r in proof['normal_rows']}]
    actions=[x for card in cards for x in n.flatten(card) if not x.get('children') and x.get('name') in ('投诉','查看投诉结果','投诉审核中')]
    action_classes={x.get('attributes',{}).get('class') for x in actions}
    n.need(action_classes <= {'button-vhqEd7','button-vhqEd7 isHighlight-DoxxP4'},'parent-normal-mixed-action-profile-requires-reviewed-contract')
    # Stable known classes were already verified per card by navigation_probe;
    # joined below checks unique field/action and complete Excel source again.
    p={'kind':'normal-review-observation-v1','status':'live-validated','revision':'parent-derived-known-normal-v1','company':job['company'],'groupid':job['groupid'],'normal_root':{'selector':root['selector']},'row':{'attributes':{'class':'commentItem-jrXo5p'}},'negative_filter':{'name':'中差评（1-3心）'},'active_class':'isSelected-ov8pOi','date_filter':{'role':'textbox','name':'评价时间'},'other_filters':{x:{'role':'textbox','name':x} for x in ('评价类型','评价来源','评价状态')},'filtered_count':{'selector':counts[0]['selector']},'pagination_mode':'count-complete','text_schema':'public-visible-text-v2','count_schema':'normal-input-counts-v2',**{f:{'attributes':{'class':c}} for f,c in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf'),('text','text-Hl9jZe'),('action','button-vhqEd7')]},'producer':{'kind':'public-DOM-derived-known-single-page','complete_proof':proof,'screenshot_proof':False}}
    if image_only_text_schema:
        import normal_review_body as rb
        n.need(image_only_text_schema==rb.SCHEMA,'parent-body-schema-unreviewed');p['image_only_text_schema']=image_only_text_schema
    if action_classes:p['action']={'name':sorted({x['name']for x in actions}),'attributes':{'class':next(iter(action_classes))if len(action_classes)==1 else sorted(action_classes)}}
    if image_only_text_schema:
        # Each card was already verified to have one allowed public action.
        # A shared exact class can legitimately label different case statuses.
        labels={x['name'] for x in actions}
        if len(labels)==1:p['action']['name']=next(iter(labels))
        elif labels:
            for card in cards:
                action=n.one(n.flatten(card),p['action'],'normal-card-action')
                n.need(n.review_field_literal(action,'action',p['text_schema']) in ('投诉','查看投诉结果','投诉审核中'),'parent-normal-mixed-action-label-unreviewed')
    if proof['boundary_selector']:p['fold_boundary']={'selector':proof['boundary_selector']}
    else:p.update(normal_root_exclusive=True,scope_mode=proof['normal_scope_mode'])
    n.need(proof['pagination'] in ('1/1','empty-no-pagination'),'parent-normal-multipage-not-supported')
    return p

def build(job,identity_page,page,image_only_text_schema=None):
    p=derive(job,page,image_only_text_schema=image_only_text_schema);envelope={'source':'local-dom-bridge','company':job['company'],'groupid':job['groupid'],'identity_evidence':identity_page,'pages':[page]}
    source=n.joined(job,envelope,p,job['source_receipt'],job['source_receipt_sha256'])
    return p,envelope,source
