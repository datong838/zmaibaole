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

def report_fields(form):
    fields={}
    for row in form.get('children',[]):
        children=normal.flatten(row);labels=[n for n in children if 'label-bygbVJ' in n.get('attributes',{}).get('class','').split() and not n.get('children')]
        if len(labels)!=1:continue
        name=normal.literal(labels[0])
        if name not in ('投诉类型','投诉理由','投诉时间'):continue
        values=[n for n in children if 'text-Fp_RCZ' in n.get('attributes',{}).get('class','').split() and not n.get('children')]
        normal.need(name not in fields and len(values)==1,'result-report-field-ambiguous:'+name);fields[name]=normal.literal(values[0])
    normal.need(set(fields)=={'投诉类型','投诉理由','投诉时间'},'result-report-fields-incomplete')
    return fields

def report_forms(drawer):
    scope=normal.flatten(drawer);forms=[n for n in scope if n.get('tag')=='form']
    if len(forms)==1:return forms[0],None
    normal.need(len(forms)==2,'result-report-form-unverified')
    parents={id(child):node for node in scope for child in node.get('children',[])}
    sections={};cards=[]
    for form in forms:
        wrap=parents.get(id(form),{});card=parents.get(id(wrap),{})
        children=card.get('children',[])
        normal.need(wrap.get('children')==[form] and len(children)==2 and children[1] is wrap
          and children[0].get('tag')=='h3' and not children[0].get('children')
          and 'container-card-dQFWGt' in card.get('attributes',{}).get('class','').split(),
          'result-report-semantic-region-unverified')
        title=normal.literal(children[0])
        normal.need(title in ('举报信息','投诉历史') and title not in sections,'result-report-section-ambiguous')
        normal.need(type(form.get('selector')) is str and bool(form['selector']),'result-report-form-selector-required')
        sections[title]=form;cards.append(card)
    parent=parents.get(id(cards[0]),{})
    normal.need(parents.get(id(cards[1])) is parent and 'container-body-_fBjDP' in parent.get('attributes',{}).get('class','').split(),
      'result-report-sections-not-siblings')
    normal.need(sections['举报信息']['selector']!=sections['投诉历史']['selector'],'result-report-form-selector-ambiguous')
    return sections['举报信息'],sections['投诉历史']

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
    current,history=report_forms(drawer);fields=report_fields(current)
    visible='\n'.join([label]+[normal.literal(x) for x in details]+[k+'：'+fields[k] for k in ('投诉类型','投诉理由','投诉时间')])
    out={'review_key':str(job['groupid'])+':'+review['review_id'],'url':tab['url'],'source':normal.BACKEND,'observed_at':page['observed_at'],'status':statuses[label],'visible_text':visible,'platform_status':label,'original_complaint':fields,'result_dom_sha256':authority.data_hash(tree),'matching':'exact current-export store/customer/full text inside the unique public result drawer','submitted_by_this_workflow':False}
    if history is not None:
        previous=report_fields(history)
        normal.need(authority.stamp(previous['投诉时间']+'+08:00')<authority.stamp(fields['投诉时间']+'+08:00')<=authority.stamp(page['observed_at']),'result-report-history-time-invalid')
        out['report_sections_schema']='semantic-current-history-v1'
        out['current_report_section']={'title':'举报信息','form_selector':current['selector']}
        out['complaint_history']=[{'title':'投诉历史','form_selector':history['selector'],'original_complaint':previous,'status':'unknown'}]
        out['visible_text']+='\n投诉历史（未观察独立结果）\n'+'\n'.join(k+'：'+previous[k] for k in ('投诉类型','投诉理由','投诉时间'))
    return out
