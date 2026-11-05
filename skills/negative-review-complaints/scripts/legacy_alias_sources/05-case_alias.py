"""Experimental pure case linkage. No authority/nickname gate or ledger override.
New drawer shape is not live validated. No screenshot or person identity claim.
"""
import hashlib,json,re
from datetime import datetime
from pathlib import Path
import normal_observation as n
import result_observation as result
import authoritative_join as a
need=n.need
KIND='public-complaint-case-alias-v1'

def encoded(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def ref(path):
    p=Path(path);need(p.is_absolute() and not p.is_symlink(),'alias-ref-absolute-nonsymlink-required')
    return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def document(r):
    need(type(r) is dict and set(r)=={'path','sha256'},'alias-ref-invalid')
    p=Path(r['path']);need(p.is_absolute() and not p.is_symlink(),'alias-ref-absolute-nonsymlink-required')
    raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==r['sha256'],'alias-ref-changed');return json.loads(raw)
def klass(nodes,cl):return n.one(nodes,{'attributes':{'class':cl}},cl)
def body_fields(scope,text_schema=None):
    return {k:result.review_literal(klass(scope,cl),k,text_schema) for k,cl in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf'),('text','text-Hl9jZe')]}
def case_fields(form):
    fields={};selectors={}
    for row in form.get('children',[]):
        ns=n.flatten(row);labels=[x for x in ns if x.get('attributes',{}).get('class')=='label-bygbVJ' and not x.get('children')]
        if not labels:continue
        need(len(labels)==1,'alias-case-label-ambiguous');label=n.literal(labels[0])
        # Unknown report fields are not promoted to stable identifiers.
        if label not in ('投诉类型','投诉时间','投诉理由'):continue
        vals=[x for x in ns if x.get('attributes',{}).get('class')=='text-Fp_RCZ' and not x.get('children')]
        need(label not in fields and len(vals)==1 and vals[0].get('selector'),'alias-case-value-ambiguous')
        fields[label]=n.literal(vals[0]);selectors[label]=vals[0]['selector']
    need(set(fields)=={'投诉类型','投诉时间','投诉理由'} and all(fields.values()),'alias-case-fields-incomplete')
    need(re.fullmatch(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',fields['投诉时间']) is not None,'alias-case-time-not-exact-seconds')
    datetime.strptime(fields['投诉时间'],'%Y-%m-%d %H:%M:%S')
    return fields,selectors

def parse_case(job,page,*,text_schema=None):
    tab,tree=n.context(page,job['groupid']);ds=[x for x in n.flatten(tree['root']) if 'byted-drawer-dialog-show' in x.get('attributes',{}).get('class','').split()]
    need(len(ds)==1,'alias-case-single-drawer-required');scope=n.flatten(ds[0])
    need(sum(x.get('name')=='投诉评价' and not x.get('children') for x in scope)==1,'alias-case-title-unverified')
    forms=[x for x in scope if x.get('tag')=='form'];need(len(forms)==1,'alias-case-form-ambiguous')
    # Case reading permits the existing report form but never editable fields.
    need(not any(x.get('tag') in ('input','textarea','select') or x.get('attributes',{}).get('contenteditable') in ('','true') for x in scope),'alias-case-editable-control')
    fields,selectors=case_fields(forms[0]);head=klass(scope,'status-head-DNErJ9');label=n.literal(head)
    statuses={'投诉审核中':'pending','投诉成功':'accepted','投诉失败':'rejected'};need(label in statuses,'alias-case-status-unreviewed')
    return {'kind':'unbound-public-complaint-case-v1','company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'tab':tab,'observed_at':page['observed_at'],
        'review':body_fields(scope,text_schema),'case':fields,'field_selectors':selectors,'status':statuses[label],'platform_status':label,'drawer_selector':ds[0]['selector'],
        'result_dom_sha256':a.data_hash(tree),'review_identity_bound':False,'person_identity_verified':False,'submitted_by_this_workflow':False}

def candidate_fields(card,text_schema=None):
    need(card.get('attributes',{}).get('class')=='commentItem-jrXo5p','alias-card-shape-unreviewed');scope=n.flatten(card);v=body_fields(scope,text_schema)
    product=n.literal(klass(scope,'spuName-j3ysmF'));need(product.startswith('已消费') and len(product)>3,'alias-complete-product-required')
    # Only the observed one-star semantic label is supported; no image counting.
    need(n.literal(klass(scope,'text-J4lpcH'))=='非常差','alias-rating-profile-required')
    actions=[x for x in scope if x.get('attributes',{}).get('class')=='button-vhqEd7 isHighlight-DoxxP4' and not x.get('children') and x.get('name') in ('投诉审核中','查看投诉结果') and x.get('disabled') is not True]
    need(len(actions)==1 and actions[0].get('selector'),'alias-read-action-not-unique')
    return {**v,'product':product[3:],'stars':1,'selector':card['selector'],'action':actions[0]}

def candidates(job,envelope,profile,review):
    observation=n.observation(job,envelope,profile);found=[]
    for row in observation['rows']:
        if (row['store'],row['text'])!=(review['store'],review['text']):continue
        page=envelope['pages'][row['page_index']-1];card=n.one(n.flatten(page['tree']['root']),{'selector':row['dom_selector']},'alias-normal-card');v=candidate_fields(card,profile.get('text_schema'))
        if all(v[k]==review[k] for k in ('store','text','product','stars')):found.append(v)
    need(len(found)==1,'alias-candidate-not-one-to-one');return found[0],observation

def signature(review,case):
    need(type(review.get('stars')) is int and 1<=review['stars']<=5,'alias-stars-invalid')
    return {**{k:review[k] for k in ('store','text','product','stars')},'case':case}

def link(old,new,old_review,current,old_pending):
    need(old['company']==new['company'] and old['groupid']==new['groupid'] and old['identity']==new['identity'],'alias-company-identity-mismatch')
    need(old['status']=='pending' and old['review']=={k:old_review[k] for k in ('store','customer','text')},'alias-old-pending-review-unverified')
    need(new['review']=={k:current[k] for k in ('store','customer','text')},'alias-current-drawer-review-mismatch')
    need(all(current[k]==old_review[k] for k in ('store','text','product','stars')),'alias-product-or-rating-mismatch')
    need(old['case']==new['case'],'alias-complaint-case-mismatch')
    sig=signature(old_review,old['case'])
    matches=[x for x in old_pending if signature(x['review'],x['case'])==sig]
    need(len(matches)==1 and matches[0]['review_key']==old_review['review_key'],'alias-old-pending-not-one-to-one')
    need(old_review['customer']!=current['customer'],'alias-name-conflict-required')
    return {'kind':KIND,'original_review_key':old_review['review_key'],'old_customer':old_review['customer'],'observed_customer':current['customer'],'case_signature_sha256':a.data_hash(sig),
        'matching':'exact-public-case-type-second-time-full-reason-and-store-body-product-stars-one-to-one-v1','person_identity_verified':False,'screenshot_authorized':False,'authoritative_source_modified':False,'status':new['status']}
