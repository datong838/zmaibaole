#!/usr/bin/env python3
"""Evidence constraints for AI judgment. No keyword classifier or UI operations."""
import hashlib,json
from pathlib import Path
CATEGORIES=('批量差评','错评错点','同行刷屏','脏话辱骂','其他')
SPECIFIC=CATEGORIES[:-1];VERSION='five-types-v1'
def need(ok,message):
    if not ok:raise ValueError(message)
def data_sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def document(ref):
    need(isinstance(ref,dict),'classification-evidence-reference-required');p=Path(ref.get('path',''))
    need(p.is_absolute() and p.is_file() and not p.is_symlink(),'classification-evidence-file-invalid');raw=p.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==ref.get('sha256'),'classification-evidence-hash-mismatch');return json.loads(raw)
def require_text(value,code):need(isinstance(value,str) and value.strip(),code)
def verified_task(state,key):
    need(key in state.get('tasks',{}) and key.startswith(str(state['groupid'])+':'),'classification-source-task-not-owned')
    task=state['tasks'][key];ref=task.get('latest_snapshot') or task.get('snapshot');source=document(ref)
    need(source.get('company')==state['company'] and str(source.get('groupid'))==str(state['groupid']) and source.get('account_verified') is True and source.get('identity')==state['identity'],'classification-source-company-identity-mismatch')
    need(source.get('source')==state.get('browser_backend'),'classification-source-backend-mismatch')
    rows=[x for x in source.get('rows',[]) if str(state['groupid'])+':'+x.get('review_id','')==key and x.get('section')=='filtered'];need(len(rows)==1,'classification-review-not-in-normal-source')
    row=rows[0];need(all(row.get(k)==task['review'].get(k) for k in ('review_id','store','customer','text','stars','date')),'classification-review-metadata-changed')
    need(type(row.get('stars')) is int and 1<=row['stars']<=3,'classification-source-not-negative')
    return row,ref

def platform_label(category,assessment):
    if category=='同行刷屏':
        need(assessment.get('subtype') in ('peer-review-spam','hotspot-attack'),'classification-peer-subtype-required')
        return {'peer-review-spam':'同行刷评','hotspot-attack':'热点事件攻击'}[assessment['subtype']]
    return category

def assessment_origin(analysis):
    source=analysis.get('analysis_source')
    if source is None:
        need(analysis.get('agent_assessed') is True and analysis.get('no_fabricated_facts') is True,'classification-agent-assessment-required')
        return 'agent'
    need(source=='deterministic-rules-v1' and analysis.get('agent_assessed') is False and analysis.get('no_fabricated_facts') is True,'classification-explicit-rule-origin-required')
    return 'rules'

def validate(state,key,analysis):
    """Validate legacy agent judgments or replay explicit deterministic rule drafts."""
    need(analysis.get('classification_policy_version')==VERSION,'classification-policy-version-required')
    current,current_ref=verified_task(state,key)
    need(analysis.get('review_key')==key and analysis.get('snapshot_sha256')==current_ref['sha256'],'classification-target-scope-mismatch')
    origin=assessment_origin(analysis)
    if origin=='rules':
        import deterministic_analysis
        deterministic_analysis.replay(state,key,analysis)
    assessments=analysis.get('type_assessments');need(isinstance(assessments,dict) and set(assessments)==set(CATEGORIES),'classification-five-assessments-required')
    cache={key:(current,current_ref)};evidence_keys={};main_quotes={}
    for category in CATEGORIES:
        a=assessments[category];need(isinstance(a,dict) and type(a.get('match')) is bool,'classification-match-must-be-boolean');require_text(a.get('reason'),'classification-type-reason-required')
        evidence=a.get('evidence');need(isinstance(evidence,list) and evidence,'classification-type-original-evidence-required');keys=set();quotes=[]
        for e in evidence:
            need(isinstance(e,dict),'classification-evidence-invalid');k=e.get('review_key');need(isinstance(k,str),'classification-evidence-key-invalid')
            if k not in cache:cache[k]=verified_task(state,k)
            row,ref=cache[k];need(e.get('source_sha256')==ref['sha256'],'classification-evidence-source-mismatch');q=e.get('quotes');need(isinstance(q,list),'classification-quotes-required')
            if row['text']=='':need(not q and e.get('original_text_empty') is True,'classification-empty-original-must-be-explicit')
            else:
                need(q and not e.get('original_text_empty'),'classification-original-quotes-required')
                need(all(isinstance(x,str) and x and x in row['text'] for x in q),'classification-quote-not-in-original')
            keys.add(k)
            if k==key:quotes.extend(q)
        need(key in keys,'classification-current-original-evidence-required');evidence_keys[category]=keys;main_quotes[category]=quotes
        if a['match'] and category in ('错评错点','同行刷屏','脏话辱骂'):need(quotes,'classification-specific-type-needs-original-quote')
    matches=[c for c in SPECIFIC if assessments[c]['match']];selected=analysis.get('category');need(selected in CATEGORIES,'classification-category-invalid')
    if matches:
        need(not assessments['其他']['match'] and selected in matches,'classification-other-not-a-fallback-when-specific-match')
        if len(matches)>1:require_text(analysis.get('primary_selection_reason'),'classification-multiple-match-primary-reason-required')
    else:need(assessments['其他']['match'] and selected=='其他','classification-all-excluded-must-select-other')
    if assessments['批量差评']['match']:
        bulk=analysis.get('bulk_evidence',{});ids=bulk.get('review_keys');need(isinstance(ids,list) and all(isinstance(x,str) for x in ids) and len(ids)>=2 and len(set(ids))==len(ids) and key in ids and set(ids)==evidence_keys['批量差评'],'classification-bulk-two-source-tasks-required')
        need(analysis.get('suspected_bulk') is True and bulk.get('identity_uncertain') is True and analysis.get('identity_uncertain') is True,'classification-bulk-is-not-identity-proof');require_text(bulk.get('similarity_reason'),'classification-bulk-similarity-reason-required')
        need(analysis.get('related_ids')==[k for k in ids if k!=key] and analysis.get('similarity_reason')==bulk['similarity_reason'],'classification-bulk-related-evidence-conflict')
        for k in ids:
            row,_=cache[k];need(row['date']==current['date'] and row['customer']==current['customer'],'classification-bulk-same-date-name-required')
    else:need(analysis.get('suspected_bulk') is False,'classification-bulk-verdict-conflict')
    wrong=assessments['错评错点']
    if wrong['match']:
        need(wrong.get('basis') in ('product-content-contradiction','praise-with-low-stars'),'classification-wrong-review-basis-required');require_text(wrong.get('contradiction_reason'),'classification-wrong-review-contradiction-required')
        if wrong['basis']=='product-content-contradiction':
            product=wrong.get('product_evidence',{});need(isinstance(product,dict),'classification-product-evidence-required');need(product.get('source_sha256')==current_ref['sha256'] and current.get('product') and product.get('product')==current['product'],'classification-product-evidence-required')
            need(product.get('content_quote') in main_quotes['错评错点'],'classification-product-quote-required')
    if assessments['同行刷屏']['match']:platform_label('同行刷屏',assessments['同行刷屏']);require_text(assessments['同行刷屏'].get('spam_or_attack_reason'),'classification-peer-semantic-reason-required')
    expected=platform_label(selected,assessments[selected]);need(analysis.get('platform_category',expected)==expected and isinstance(analysis.get('platform_category_evidence'),dict) and analysis['platform_category_evidence'].get('category_label')==expected,'classification-platform-category-mismatch')
    if selected=='其他':
        excluded=analysis.get('exclusion_reasons');need(isinstance(excluded,dict) and set(excluded)==set(SPECIFIC) and all(excluded[c]==assessments[c]['reason'] for c in SPECIFIC),'classification-other-four-exclusions-required')
        need(analysis.get('sampled_history_facts_reused')is not True,'classification-history-facts-forbidden')
    return {'ok':True,'category':selected,'platform_category':expected,'matched_specific_types':matches,'policy_version':VERSION}
