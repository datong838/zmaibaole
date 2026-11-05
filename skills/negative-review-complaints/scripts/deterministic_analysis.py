#!/usr/bin/env python3
"""Conservative rule-generated LOCAL DRAFTS. No model/agent claim, UI or submission."""
import argparse,copy,hashlib,json,re,sys
from pathlib import Path
import classification_policy as policy
import case_memory
SOURCE='deterministic-rules-v1';VERSION='normal-review-explicit-evidence-rules-v1'
INSULTS=('傻逼','混蛋','王八蛋','狗东西','他妈的','妈的')
SUBJECTIVE=('不甜','太甜','太酸','太硬','不好吃','难吃','不新鲜','有头发','有虫','发霉','有异物','送错','太慢','不满意','服务差','太贵','分量少','包装破损','太差','差评','一般','不好','不值','失望','品控')
PRAISE=('非常好吃','很好吃','好吃','非常满意','满意','味道很好','五星好评','很甜','服务很好')
need=policy.need
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def normalized(text):return re.sub(r'[\s，。！？、,.!?；;：:“”「」‘’\"\'（）()]+','',text)
def evidence(key,row,r,quotes=None):return {'review_key':key,'source_sha256':r['sha256'],'quotes':quotes if quotes is not None else [row['text']]}
def current(state,key):
    row,r=policy.verified_task(state,key)
    need(state.get('mode')=='draft-only' and state.get('browser_backend')=='local-dom-bridge','rules-live-draft-only-required')
    need(row.get('folded') is not True and row.get('section')=='filtered','rules-normal-only-no-folded')
    need(state['tasks'][key].get('action')=='投诉','rules-existing-complaint-must-not-redraft')
    need(isinstance(row.get('text'),str) and row['text'].strip() and len(row['text'])<=2000,'rules-empty-or-unknown-review')
    return row,r

def knowledge(state,key,selection=None):
    # read_records deeply replays original case/source/result refs. No KB writes.
    memory=case_memory.DEFAULT_MEMORY.resolve();records=case_memory.read_records(memory)
    eligible={r['observation_id']:r for r in records if r['company']==state['company'] and str(r['groupid'])==str(state['groupid']) and r['identity']==state['identity'] and r['review_key']!=key}
    ids=selection if selection is not None else sorted(eligible,key=lambda k:(eligible[k]['observed_at'],k),reverse=True)[:3]
    need(isinstance(ids,list) and ids and len(ids)==len(set(ids)) and all(k in eligible for k in ids),'rules-verified-kb-style-required')
    result=[]
    for ident in ids:
        r=eligible[ident];text=r['original_reason'];need(isinstance(text,str) and len(text)>=8,'rules-kb-original-text-required')
        at=next((text.find(x) for x in ('请求平台','申请平台','请平台','核查') if text.find(x)>=0),0)
        quote=text[at:at+40] if len(text[at:])>=8 else text[-40:]
        source_ref=ref(memory/r['source_ref']['path']);result_ref=ref(memory/r['result_ref']['path'])
        need(source_ref['sha256']==r['source_ref']['sha256'] and result_ref['sha256']==r['result_ref']['sha256'],'rules-kb-pinned-original-changed')
        result.append({'observation_id':ident,'case_id':r['case_id'],'source':source_ref,'result':result_ref,'outcome':r['outcome'],'quoted_original':quote,'style_observation':'只借鉴先转述反馈再申请核实的结构；历史主张不是本条事实，驳回/待审不作为成功经验。','unverified_facts_reused':False})
    return result

def history_state(root,state,key,history_ref):
    effective=copy.deepcopy(state)
    if history_ref:
        import recent_other_history
        document=policy.document(history_ref);items=recent_other_history.validate(root,state,key,document)
        effective['tasks'][key]['history']={'items':items,'evidence':history_ref}
    h=effective['tasks'][key].get('history') or {};need(h.get('items') and h.get('evidence'),'rules-other-history-required')
    need(policy.document(h['evidence']).get('items')==h['items'],'rules-other-history-changed')
    return effective,h

def produce(root,state,key,inspection,history_ref=None,*,kb_selection=None):
    import draft_inspection
    row,snapshot=current(state,key);text=row['text'];draft_inspection.validate(inspection['path'],root=root,key=key,snapshot=snapshot['sha256']);policy.document(inspection)
    need(not any(x in text for x in ('骂我','说我是','叫我','不是骂','没有骂','店员说','老板说')),'rules-ambiguous-attribution')
    ev=evidence(key,row,snapshot);assess={c:{'match':False,'reason':'当前已核原文未命中本规则版本的明确证据条件。','evidence':[ev]} for c in policy.CATEGORIES}
    peers=[];base=normalized(text)
    for peer in sorted(state['tasks']):
        if peer==key:continue
        p=state['tasks'][peer]['review']
        if p.get('date')==row['date'] and p.get('customer')==row['customer'] and row['customer'] not in ('匿名用户','匿名','抖音用户'):
            p,r=policy.verified_task(state,peer)
            if p.get('folded') is not True and len(base)>=8 and normalized(p['text'])==base:peers.append((peer,p,r))
    if peers:
        assess['批量差评'].update(match=True,reason='同日相同公开昵称存在多条规范化后相同原文，仅为重复评价线索，不能证明同一身份。',evidence=[ev]+[evidence(k,p,r) for k,p,r in peers])
    bad=next((x for x in INSULTS if (re.search(r'(?<!妈)妈的',text) if x=='妈的' else x in text)),None)
    if bad:need(not any(x in text for x in ('说','骂','叫','不是','没有','不算')),'rules-ambiguous-attribution')
    if bad:
        assess['脏话辱骂'].update(match=True,reason='原文逐字出现明确辱骂词；不据此推定消费事实或恶意身份。',evidence=[evidence(key,row,snapshot,[bad])])
    # Only unqualified praise within verified 1–3 star negative filter; mixed/negated praise is NOT inferred.
    rest=normalized(text)
    for word in sorted(PRAISE,key=len,reverse=True):rest=rest.replace(word,'')
    praise=not rest and 1<=row['stars']<=3
    if praise:assess['错评错点'].update(match=True,basis='praise-with-low-stars',contradiction_reason='整条原文只有明确称赞短语，与当前1至3星记录不一致，申请核对误点可能。',reason='明确称赞原文与低星存在可核对矛盾，不推定未消费。')
    promo=re.search(r'别来这家[，,。！!\s]*去[^，。！？\n]{2,16}店',text)
    if promo and peers:assess['同行刷屏'].update(match=True,subtype='peer-review-spam',spam_or_attack_reason='多条重复原文逐字包含其他门店引导，发言者同行身份仍未核实。',reason='存在重复门店引导内容；仅建议平台核对刷屏类规则，不认定发布者身份。',evidence=[evidence(key,row,snapshot,[promo.group()])])
    matches=[c for c in policy.SPECIFIC if assess[c]['match']]
    if not matches:
        # No verified business-category source exists in the current protocol.
        # A transaction product alone cannot prove the merchant's full business scope.
        need(not any(x in text for x in ('理发','美甲','酒店','评价错店','评错店')),'rules-merchant-category-proof-missing')
        need(any(x in text for x in SUBJECTIVE),'rules-insufficient-explicit-evidence')
        assess['其他'].update(match=True,reason='原文为口味或消费体验反馈；本版本未发现支持四项专项类型的明确证据，不认定恶意。')
    category=next(c for c in ('脏话辱骂','同行刷屏','批量差评','错评错点','其他') if assess[c]['match'])
    styles=knowledge(state,key,kb_selection);closing='申请结合对应消费记录复核本条评价。'
    # Only a safe generic wording fragment can enter the draft, never KB facts.
    if any('请求平台核查' in s['quoted_original'] for s in styles):closing='请求平台核查本条评价及对应消费记录。'
    reasons={'批量差评':'同日相同公开昵称出现重复评价内容，昵称不证明同一身份。','脏话辱骂':'原文出现「'+(bad or '')+'」等明确辱骂表述。','错评错点':'原文明确称赞而记录为低星，申请核对是否误评或误点。','同行刷屏':'多条重复原文包含其他门店引导，发布者身份未核实。','其他':'原文反映个人口味或消费体验，现有证据不支持专项类型。'}
    draft='本条评价原文摘录为「'+text[:50]+'」，当前记录为'+str(row['stars'])+'星。'+reasons[category]+closing
    need(30<=len(draft.encode('utf-16-le'))//2<=300,'rules-draft-length-out-of-range')
    inputs={'root':str(Path(root).resolve()),'inspection_operation':inspection,'history':history_ref,'kb_observation_ids':[s['observation_id'] for s in styles]}
    a={'analysis_source':SOURCE,'provenance':{'kind':'deterministic-complaint-draft-v1','producer_version':VERSION,'producer_sha256':ref(__file__)['sha256'],'inputs':inputs,'kb_style_references':styles,'facts_origin':'current-verified-normal-reviews-only','model_used':False,'agent_used':False},'classification_policy_version':policy.VERSION,'review_key':key,'snapshot_sha256':snapshot['sha256'],'agent_assessed':False,'no_fabricated_facts':True,'category':category,'reason':reasons[category],'quotes':assess[category]['evidence'][0]['quotes'],'draft':draft,'suspected_bulk':bool(peers),'related_ids':[k for k,p,r in peers],'identity_uncertain':True,'type_assessments':assess,'platform_category':policy.platform_label(category,assess[category]),'platform_category_evidence':{'category_label':policy.platform_label(category,assess[category]),'inspection_operation':inspection,'platform_selected_in_ui':False,'reason_filled_in_ui':False,'submitted':False}}
    if peers:
        reason=assess['批量差评']['reason'];a.update(similarity_reason=reason,bulk_evidence={'review_keys':[key]+[k for k,p,r in peers],'identity_uncertain':True,'similarity_reason':reason})
    if len(matches)>1:a['primary_selection_reason']='按明确辱骂、重复门店引导、重复原文、称赞低星的固定优先级主选；并存证据保留，不扩展身份结论。'
    if category=='其他':
        effective,h=history_state(root,state,key,history_ref);samples={policy.data_sha(x):x for x in h['items']};refs=[]
        for sha,sample in sorted(samples.items())[:min(3,len(samples))]:
            need(isinstance(sample.get('text'),str) and len(sample['text'])>=8,'rules-other-history-text-required');refs.append({'sample_sha256':sha,'quoted_original':sample['text'][:40],'style_observation':'只借鉴转述反馈后请求核实的结构，不复制历史指控。','unverified_facts_reused':False})
        a.update(exclusion_reasons={c:assess[c]['reason'] for c in policy.SPECIFIC},history_sha256=h['evidence']['sha256'],history_style_references=refs,history_usage='wording-reference-only',sampled_history_facts_reused=False)
    return a

def replay(state,key,analysis):
    p=analysis.get('provenance',{});need(p.get('kind')=='deterministic-complaint-draft-v1' and p.get('producer_version')==VERSION,'rules-provenance-version-required')
    i=p.get('inputs',{});expected=produce(i['root'],state,key,i['inspection_operation'],i.get('history'),kb_selection=i.get('kb_observation_ids'))
    need(analysis==expected,'rules-analysis-not-reproducible');return True

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);p.add_argument('--review-key',required=True);p.add_argument('--inspection-operation',required=True);p.add_argument('--history');p.add_argument('--out',required=True);a=p.parse_args()
    try:
        root=Path(a.root).resolve();state=json.loads((root/'state.json').read_bytes());value=produce(root,state,a.review_key,ref(a.inspection_operation),ref(a.history) if a.history else None);out=Path(a.out).resolve();need(not out.exists(),'rules-existing-output-refused')
        with out.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({'ok':True,'analysis':ref(out),'analysis_source':SOURCE,'agent_assessed':False,'submitted':False}));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps({'ok':False,'error':str(e),'submitted':False}));return 2
if __name__=='__main__':raise SystemExit(main())
