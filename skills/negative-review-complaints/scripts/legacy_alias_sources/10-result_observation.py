#!/usr/bin/env python3
"""Pure public complaint-result drawer parser. Never clicks or submits."""
import normal_observation as normal
import authoritative_join as authority

def review_literal(node,field,text_schema=None):
    if field=='text' and text_schema=='public-visible-text-v2':return normal.review_field_literal(node,field,text_schema=text_schema)
    # Observed pending-result body includes only an unnamed presentation chevron.
    # It adds no text; never strip arbitrary children/links or shortened bodies.
    if field=='text' and node.get('children'):
        children=node['children']
        normal.need(len(children)==1 and children[0].get('tag')=='svg' and children[0].get('role')=='presentation' and children[0].get('attributes',{}).get('class')=='icon-K1rG1b','result-body-unreviewed-children')
        normal.need(all(n.get('tag') in ('svg','g','path') and not n.get('name') for n in normal.flatten(children[0])),'result-body-child-text-or-control')
        node={**node,'children':[]}
    return normal.literal(node)

def parse(job,page,review,*,text_schema=None):
    tab,tree=normal.context(page,job['groupid']);nodes=normal.flatten(tree['root'])
    drawers=[n for n in nodes if 'byted-drawer-dialog-show' in n.get('attributes',{}).get('class','').split()]
    normal.need(len(drawers)==1,'single-result-drawer-required');drawer=drawers[0];scope=normal.flatten(drawer)
    normal.need(any(n.get('name')=='投诉评价' and not n.get('children') for n in scope),'result-drawer-title-unverified')
    def klass(cl):return [n for n in scope if cl in n.get('attributes',{}).get('class','').split()]
    for field,cl in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf'),('text','text-Hl9jZe')]:
        found=klass(cl);normal.need(len(found)==1 and review_literal(found[0],field,text_schema)==authority.normalized(review[field]),'result-review-mismatch:'+field)
    heads=klass('status-head-DNErJ9');normal.need(len(heads)==1,'result-status-not-unique');label=normal.literal(heads[0]);statuses={'投诉失败':'rejected','投诉成功':'accepted','投诉审核中':'pending'}
    normal.need(label in statuses,'unreviewed-result-status-label')
    details=klass('status-content-Uk09gi');normal.need(len(details)<=1,'result-status-detail-ambiguous')
    fields={}
    forms=[n for n in scope if n.get('tag')=='form'];normal.need(len(forms)==1,'result-report-form-unverified')
    for row in forms[0].get('children',[]):
        children=normal.flatten(row);labels=[n for n in children if 'label-bygbVJ' in n.get('attributes',{}).get('class','').split() and not n.get('children')]
        if len(labels)!=1:continue
        name=normal.literal(labels[0])
        if name not in ('投诉类型','投诉理由','投诉时间'):continue
        values=[n for n in children if 'text-Fp_RCZ' in n.get('attributes',{}).get('class','').split() and not n.get('children')]
        normal.need(name not in fields and len(values)==1,'result-report-field-ambiguous:'+name);fields[name]=normal.literal(values[0])
    normal.need(set(fields)=={'投诉类型','投诉理由','投诉时间'},'result-report-fields-incomplete')
    visible='\n'.join([label]+[normal.literal(x) for x in details]+[k+'：'+fields[k] for k in ('投诉类型','投诉理由','投诉时间')])
    return {'review_key':str(job['groupid'])+':'+review['review_id'],'url':tab['url'],'source':normal.BACKEND,'observed_at':page['observed_at'],'status':statuses[label],'visible_text':visible,'platform_status':label,'original_complaint':fields,'result_dom_sha256':authority.data_hash(tree),'matching':'exact current-export store/customer/full text inside the unique public result drawer','submitted_by_this_workflow':False}
