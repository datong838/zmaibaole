#!/usr/bin/env python3
"""Pinned governance notice detail reader. Navigation and drawer dismissal only; no submissions or sends."""
import argparse,fcntl,hashlib,importlib.util,json,os,sys
# Keep the formal script and production adapters on one canonical role module.
if __name__=='__main__':sys.modules.setdefault('governance_detail',sys.modules[__name__])
from pathlib import Path
from urllib.parse import urlsplit
import governance_dom as g
spec=importlib.util.spec_from_file_location('governance_detail_query',Path(__file__).with_name('bridge-governance-query.py'));query_api=importlib.util.module_from_spec(spec);spec.loader.exec_module(query_api)
nav=query_api.nav
need=g.need

def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':nav.digest(p)}
def document(r):return nav.read_pinned(r['path'],r['sha256'])
def exclusive(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def drawers(tree):return [n for n in g.nodes(tree) if 'governance_merchant-drawer-dialog-show' in g.cls(n)]
def field(scope,label):
    candidates=[]
    for n in g.walk(scope):
        ch=n.get('children',[])
        if 'item-dOecJQ' in g.cls(n) and len(ch)==2 and ch[0].get('tag')=='span' and ch[0].get('attributes',{}).get('class')=='label-CPZ6GC' and g.text(ch[0])==label:candidates.append(ch[1])
    return g.one(candidates,'governance-detail-field-not-unique:'+label)
def section(drawer,title):
    found=[]
    for n in g.walk(drawer):
        if 'card-eC9eMO' not in g.cls(n):continue
        heads=[c for c in n.get('children',[]) if 'head-T49g6b' in g.cls(c)]
        if len(heads)==1 and g.text(heads[0])==title:found.append(n)
    return g.one(found,'governance-detail-section-unreviewed:'+title)
ADVICE_SECTION='如何避免再次违规'
PROMO_SECTION='规则学习小助手'
def advice_section_pending(tree):
    """The reviewed normal notice drawer paints its advice card after the promo card.

    A capture taken between the two paints shows only three reviewed heads, so the
    section reader would report the advice card as missing. This names that render
    state only: it never substitutes a value and never accepts a different card set.
    """
    try:
        if urlsplit(tree.get('url') or '').path!=g.RECORDS:return False
        shown=drawers(tree)
        if len(shown)!=1:return False
        drawer=shown[0]
        if 'notice-drawer-vBipFK' in g.cls(drawer) or 'notice-drawer-OIp9e3' not in g.cls(drawer):return False
        ns=list(g.walk(drawer));heads=[g.text(n) for n in ns if 'head-T49g6b' in g.cls(n)]
        return ADVICE_SECTION not in heads and PROMO_SECTION in heads
    except Exception:return False
FRAME_PATH='/h5/governance/violation_talent_notice'
def outer_close(observation,drawer):
    close=g.one([n for n in drawer.get('children',[]) if n.get('tag')=='span' and n.get('attributes',{}).get('class')=='governance_merchant-drawer-close-icon'],'governance-detail-close-not-unique');ch=close.get('children',[]);need(len(ch)==1 and ch[0].get('tag')=='span' and ch[0].get('attributes',{}).get('class')=='governance_merchant-icon governance_merchant-icon-close' and not close.get('disabled'),'governance-detail-close-shape-unreviewed')
    return {'op':'click','tabId':observation['tab_id'],'kind':'dismiss','locator':{'by':'selector','value':close['selector']}}

def class_family(value):
    return ' '.join(__import__('re').sub(r'-[A-Za-z0-9_]{6}$','',token) for token in (value or '').split())

def parse_anchor_advice_frame(observation, row, drawer, iframe, frame, ns):
    """The observed anchor reminder is not a violation or a livestream notice."""
    import re
    from urllib.parse import parse_qs
    from datetime import datetime

    def exact(cls):
        return g.one([n for n in ns if class_family(n.get('attributes', {}).get('class')) == cls], 'anchor-frame-field-not-unique:' + cls)
    header = exact('by-header__title_overhide overflow')
    need(not header.get('children') and g.text(header) == '锚点使用建议', 'anchor-frame-title-shape-unreviewed')
    need(row['reason'] == '温馨提醒：锚点类型选择有误' and row['disposal'] == '带货锚点修改为打卡锚点，无' and (row['effective_status'] == '生效中') and (row['rectification_status'] == '-'), 'anchor-frame-source-template-unreviewed')
    page = g.records_page(observation['tree'], require_date=False)
    need(same_source_row(g.one([r for r in page['rows'] if r['notice_id'] == row['notice_id']], 'anchor-frame-original-row-not-unique'), row), 'anchor-frame-original-row-changed')
    q = parse_qs(urlsplit(observation['tab']['url']).query, keep_blank_values=True)
    task = q.get('TaskID', [])
    need(len(task) == 1 and re.fullmatch('CF[A-Za-z0-9_-]{1,96}', task[0]) and (q.get('drawerForV2') == ['MerchantCID']), 'anchor-frame-task-binding-unreviewed')
    reason = exact('title_text')
    need(g.text(reason) == row['reason'] and (not reason.get('children')), 'anchor-frame-reason-mismatch')
    card = g.one([n for n in ns if n.get('attributes', {}).get('id') == 'violation_' + task[0] and class_family(n.get('attributes', {}).get('class')) == 'title'], 'anchor-frame-card-task-mismatch')
    need(reason in card.get('children', []), 'anchor-frame-card-reason-binding-mismatch')
    obj = exact('webcase_right')
    oc = obj.get('children', [])
    need(len(oc) == 3, 'anchor-frame-video-layout-unreviewed')
    name=oc[0]
    need(class_family(name.get('attributes',{}).get('class'))=='title' and not name.get('children') and g.text(name), 'anchor-frame-video-title-unreviewed')
    vals = []
    for (n, label) in zip(oc[1:], ('发布时间:', '视频ID:')):
        ch = n.get('children', [])
        need(class_family(n.get('attributes', {}).get('class')) == 'content' and len(ch) == 2 and (class_family(ch[0].get('attributes', {}).get('class')) == 'label') and (not ch[0].get('children')) and (g.text(ch[0]) == label) and (not ch[1].get('children')), 'anchor-frame-video-field-unreviewed')
        vals.append(ch[1])
    (published, identifier) = vals
    need(re.fullmatch('\\d{1,32}', g.text(identifier)) and row['object'] == g.text(name) + ' 短视频 ' + g.text(identifier), 'anchor-frame-source-video-mismatch')
    pub = datetime.strptime(g.text(published), '%Y/%m/%d %H:%M:%S')
    situation = g.one([n for n in ns if class_family(n.get('attributes',{}).get('class'))=='contain' and len(n.get('children',[]))==2 and class_family(n['children'][0].get('attributes',{}).get('class'))=='header' and any(g.text(x)=='情况说明' and not x.get('children') for x in g.walk(n['children'][0]))], 'anchor-frame-situation-not-unique')
    sc = situation.get('children', [])
    need(len(sc) == 2 and class_family(sc[0].get('attributes', {}).get('class')) == 'header' and (class_family(sc[1].get('attributes', {}).get('class')) == 'richText'), 'anchor-frame-situation-layout-unreviewed')
    hc = sc[0].get('children', [])
    need(len(hc) == 2 and class_family(hc[0].get('attributes', {}).get('class')) == 'title' and (g.text(hc[0]) == '情况说明') and (not hc[0].get('children')) and (class_family(hc[1].get('attributes', {}).get('class')) == 'rule_link') and (g.text(hc[1]) == '平台规则'), 'anchor-frame-situation-heading-unreviewed')
    lc = hc[1].get('children', [])
    need(len(lc) == 2 and lc[0].get('tag') == 'span' and (not lc[0].get('children')) and (g.text(lc[0]) == '平台规则') and (lc[1].get('tag') == 'img') and (not lc[1].get('children')) and (not g.text(lc[1])), 'anchor-frame-rule-link-unreviewed')
    paras = sc[1].get('children', [])
    need(len(paras) == 1 and class_family(paras[0].get('attributes', {}).get('class')) == 'paragraph' and (len(paras[0].get('children', [])) == 1), 'anchor-frame-situation-paragraph-unreviewed')
    explanation = paras[0]['children'][0]
    need(explanation.get('tag') == 'span' and (not explanation.get('children')) and (g.text(explanation) == '您的视频中挂载了抖音生活服务的经营类锚点，但实际视频内容未对锚点下的抖音生活服务相关商品、服务、环境进行展示、营销或种草。该情况不属于违规，不会影响您的视频流量和账号。'), 'anchor-frame-situation-literal-unreviewed')
    tip = exact('tip')
    tc = tip.get('children', [])
    literal = '锚点类型已更换：平台已为您更换至正确的锚点类型，后续发布作品请按照平台要求选择正确锚点类型。'
    advice = '后续发布作品请按照平台要求选择正确锚点类型。'
    need(len(tc) == 1 and tc[0].get('tag') == 'div' and (not tc[0].get('children')) and (g.text(tip) == g.text(tc[0]) == literal), 'anchor-frame-tip-literal-unreviewed')

    def info(label):
        b = g.one([n for n in ns if class_family(n.get('attributes', {}).get('class')) == 'info' and len(n.get('children', [])) == 2 and (class_family(n['children'][0].get('attributes', {}).get('class')) == 'info_label') and (g.text(n['children'][0]) == label)], 'anchor-frame-info-not-unique:' + label)
        value = b['children'][1]
        need(class_family(value.get('attributes', {}).get('class')) == 'info_value' and (not value.get('children')), 'anchor-frame-info-value-unreviewed')
        return (b['children'][0], value)
    (label, modified) = info('修改生效时间')
    mod = datetime.strptime(g.text(modified), '%Y/%m/%d %H:%M')
    need(pub <= mod and mod.date().isoformat() == row['violation_date'], 'anchor-frame-times-unreviewed')
    if any((g.text(n) == '申诉截止时间' and (not n.get('children')) for n in ns)):
        (deadline_label, deadline) = info('申诉截止时间')
        end = datetime.strptime(g.text(deadline), '%Y/%m/%d %H:%M')
        need(mod < end, 'anchor-frame-times-unreviewed')
        deadline_fact = {'text': g.text(deadline), 'selector': deadline['selector'], 'label': '申诉截止时间', 'observed': True, 'appeal_performed': False}
    else:
        expired = g.one([n for n in ns if not n.get('children') and g.text(n) == '申诉逾期'], 'anchor-frame-appeal-status-required')
        deadline_fact = {'observed': False, 'status': '申诉逾期', 'status_selector': expired['selector'], 'appeal_performed': False}
    need(not any((class_family(n.get('attributes', {}).get('class')) == 'info_label' and g.text(n) in ('已生效处置', '待生效处置', '处置生效时间') for n in ns)), 'anchor-frame-mixed-punishment-template')
    facts = {'schema': 'governance-anchor-advice-frame-detail-v1', 'notice_id': row['notice_id'], 'source_notice_row': row, 'notification_time_observed': False, 'notice_id_visible_in_frame': False, 'reason': row['reason'], 'object_name': g.text(name), 'object_type': '短视频', 'object_id': g.text(identifier), 'disposals': ['带货锚点修改为打卡锚点'], 'pending_disposals': [], 'effective_statuses': ['生效中'], 'detail_effectiveness_status_observed': False, 'table_effectiveness_status': row['effective_status'], 'modification_time': g.text(modified), 'modification_time_label': '修改生效时间', 'modification_time_selector': modified['selector'], 'publication_time': g.text(published), 'appeal_deadline': deadline_fact, 'not_business_violation': True, 'situation_explanation': {'text': g.text(explanation), 'selector': explanation['selector'], 'section': '情况说明'}, 'anchor_modification_observation': {'text': literal, 'selector': tc[0]['selector'], 'label': '锚点类型已更换', 'business_action_performed': False}, 'public_recommendation': advice, 'public_recommendation_selectors': [tc[0]['selector']], 'public_recommendation_paragraphs': [{'text': advice, 'selector': tc[0]['selector'], 'original_visible_text': literal, 'excluded_confirmation_prefix': literal[:-len(advice)], 'extraction': 'exact-observed-anchor-change-confirmation-prefix-and-future-advice-suffix'}], 'public_recommendation_section': '锚点类型已更换', 'internal_rules_excluded_from_recommendation': True, 'frame_evidence': {'iframe_selector': iframe['selector'], 'frame_url': frame['url'], 'video_id_selector': identifier['selector'], 'read_only_projection': True, 'outer_task_id': task[0], 'card_id': card['attributes']['id'], 'source_notice_binding': 'exact-visible-background-row-and-outer-task-card'}, 'observed_at': observation['observed_at'], 'submitted': False}
    return (facts, outer_close(observation, drawer))

ANCHOR_GUARD_PROOF_PINS={'kind': 'reviewed-anchor-frame-close-preinput-guard-failure-v1', 'original_detail': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/governance-anchor-close-guard-candidate/original-detail.json', 'sha256': 'e4c1954c7554ca67907d0f379248b35f073674067f31a026c17e3fee28f89144'}, 'source_detail': {'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/companies/1/governance-detail-operations/c2b03d9c8ec7f5bdc0c98222c5602c0c28d7e8b924157c8de5a2e7e5f609d21c/state.json', 'sha256': 'e4c1954c7554ca67907d0f379248b35f073674067f31a026c17e3fee28f89144'}, 'content_family': {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/governance-anchor-close-guard-candidate/content-family.js', 'sha256': '5d9ccab415645fb49b004123e260249264aa7eace1d78bd145a653bd90dd88a7'}, 'request_source': {'path': '/Users/feibing/work/projects/zmaibaole/skills/violation-notifier/scripts/bridge-governance-query.py', 'sha256': '5270ff1e3979c669229b61103a42466d008d2ebbd30b02c42ad128efe1c4ec37'}, 'child_exit': {'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/children/0012-exit.json', 'sha256': '0b357f9d0d715853051561d912319778e00938b53fc723f201f16e490854d8d4'}, 'performance': {'path': '/Users/feibing/work/projects/zmaibaole/runtime/standalone-workshop-director/attempts/task-86161e9560b2bf7aa850c6c2-16/bridge-performance/bridge-request-57770732dde34993bc30b83e264a6824.json', 'sha256': '802c81b37b4c2aa44a0350026d2cfb4734126b1891ce942c4b51ab8a79e71af6'}, 'raw_reply_available': False, 'classification': 'delivered-content-guard-rejection-before-click', 'resident_exact_hash_claimed': False, 'close_replay_authorized': False, 'route_only_authority': True}

def verify_anchor_guard_proof(reference):
    """Finite delivered preinput rejection, never an invented raw reply."""
    proof=document(reference)
    need(proof==ANCHOR_GUARD_PROOF_PINS,'anchor-guard-proof-generation-changed')
    old=document(proof['original_detail']);need(proof['source_detail']['sha256']==proof['original_detail']['sha256'],'anchor-guard-original-archive-changed')
    m=old['manifest'];v={k:document(r) for k,r in m['inputs'].items()};job=v['job'];q=v['query'];nav.scope(job)
    need(old['phase']=='verify-closed-unknown' and old['cursor']==len(old['details'])==2 and len(old['calls'])==6 and all(c.get('state')=='confirmed' for c in old['calls'][:5]),'anchor-guard-exact-original-required')
    row=q['rows'][2];current=old['current'];call=old['calls'][5]
    need(row['notice_id']==current['notice_id']=='202610264826012780' and call['state']=='unknown' and call['before']==current['before_close']==old['last_observation'],'anchor-guard-original-close-required')
    raw=document(call['before']);facts,close=parse(raw,row);need(call['command']==current['close_command']==close and same_facts(facts,current['facts']) and facts['schema']=='governance-anchor-advice-frame-detail-v1' and facts['not_business_violation'] is True,'anchor-guard-complete-advice-facts-required')
    first=document(current['normal_before']);opening=old['calls'][4];need(opening['state']=='confirmed' and opening['before']==current['normal_before'] and opening['command']=={**g.detail_action(first['tree'],row['notice_id'],start=job['start'],end_exclusive=job['end_exclusive']),'tabId':m['tab_id']},'anchor-guard-original-open-required');reply_matches(opening['command'],opening['result'],first)
    for obs in (first,raw):
        tab=nav.context([{'tabs':[obs['tab']]}],m['tab_id'],job['groupid']);need(tab['windowId']==first['tab']['windowId'] and obs['tab_id']==m['tab_id'],'anchor-guard-scope-changed');nav.identity(obs['tree'],job['identity'])
    child=document(proof['child_exit']);launch=document(child['launch']);need(child['returncode']==2 and child['stderr']=='' and json.loads(child['stdout'])=={'ok':False,'error':'governance-bridge-request-failed:governance frame drawer structure unreviewed'} and child['argv']==launch['argv'],'anchor-guard-natural-error-propagation-required')
    perf=document(proof['performance']);need(perf['schema']=='bridge-request-timing-v1' and perf['op']=='click' and perf['ok'] is False and perf['outcome']=='failed' and perf['exception'] is False and perf['service']['state']=='returned' and perf['service']['job_id']=='6398d8d5-aeb5-49e2-814f-ac13e298fca3' and perf['service']['delivery_result_ns']>0,'anchor-guard-returned-performance-required')
    content=_anchor_source_bytes(proof['content_family']);need(hashlib.sha256(content).hexdigest()==proof['content_family']['sha256'],'anchor-guard-code-family-ref');content=content.decode();request=_anchor_source_bytes(proof['request_source']);need(hashlib.sha256(request).hexdigest()==proof['request_source']['sha256'],'anchor-guard-request-source-ref');request=request.decode()
    error="throw Error('governance frame drawer structure unreviewed')";need(content.count(error)==1 and content.index("const frameClose=governanceFrameDrawerCloseRule(e,action);")>content.index('function assertSafe(e, action, companyCap)') and "const e=one(m.locator);const rule=assertSafe(e,m.kind,m.companyCapability);\n        e.click();" in content and "name(x)==='生活服务违规通知'" in content and "name(x)==='违规ID：'" in content and "'governance-bridge-request-failed:'+str(r.get('error'))" in request,'anchor-guard-reviewed-preinput-source-family-required')
    drawer=g.one(drawers(raw['tree']),'anchor-guard-drawer');iframe=g.one([n for n in g.walk(drawer) if n.get('public_frame_dom')],'anchor-guard-frame');ns=list(g.walk(iframe['public_frame_dom']['root']));need(not any('by-header__title_overhide' in g.cls(n) and g.text(n)=='生活服务违规通知' for n in ns) and not any(n.get('tag')=='div' and not n.get('children') and g.text(n)=='违规ID：' for n in ns),'anchor-guard-exact-failed-predicate-required')
    return {'kind':'verified-anchor-frame-close-preinput-guard-failure-v1','proof':reference,'original_detail':proof['original_detail'],'source_detail':proof['source_detail'],'original':old,'manifest':m,'inputs':v,'row':row,'facts':current['facts'],'call_index':5,'command':close,'raw_reply_available':False,'close_replay_authorized':False,'route_only_authority':True,'tab_id':m['tab_id'],'window_id':first['tab']['windowId'],'groupid':str(job['groupid']),'identity':job['identity']}

ANCHOR_ROUTE_PROVIDER_REF={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/anchor-frame-guard-route-recovery-candidate/restore_anchor_route_once.py', 'sha256': 'd0bbe5bb434bbf8959016a813762516cff6119c2c51cef9b971a99143c15018d'}

def _anchor_source_bytes(reference):
    import verification_session as verification
    session=verification.current()
    if session is not None:return session._check((reference['path'],reference['sha256']))
    data=Path(reference['path']).read_bytes();need(hashlib.sha256(data).hexdigest()==reference['sha256'],'anchor-source-bytes-changed');return data

def _load_anchor_route_provider():
    data=_anchor_source_bytes(ANCHOR_ROUTE_PROVIDER_REF)
    module=importlib.util.module_from_spec(importlib.util.spec_from_loader('anchor_guard_route_receipt_provider',loader=None));module.__file__=ANCHOR_ROUTE_PROVIDER_REF['path'];exec(compile(data,module.__file__,'exec'),module.__dict__)
    return module

def verify_anchor_route_completion(reference,guard_reference):
    """Pure independent route receipt verifier; never consults unknown scanners."""
    need(ANCHOR_ROUTE_PROVIDER_REF is not None,'anchor-route-provider-not-frozen')
    module=_load_anchor_route_provider()
    _anchor_source_bytes(module.GUARD_MODULE)
    result=module.verify_complete(dict(reference))
    need(result['guard_proof']==guard_reference,'anchor-route-guard-proof-changed');guard=verify_anchor_guard_proof(guard_reference)
    normal=result['normal_after'];raw=document(normal);job=guard['inputs']['job'];tab=nav.context([{'tabs':[raw['tab']]}],guard['tab_id'],job['groupid']);need(tab['windowId']==guard['window_id'] and raw['tab_id']==guard['tab_id'],'anchor-route-final-scope-changed');nav.identity(raw['tree'],guard['identity']);page=normal_page(raw['tree'],job,guard['inputs']['query']);need(guard['row'] in page['rows'],'anchor-route-original-row-not-restored')
    need(__import__('datetime').datetime.fromisoformat(raw['observed_at'])>=__import__('datetime').datetime.fromisoformat(document(guard['original']['current']['before_close'])['observed_at']),'anchor-route-final-before-failure')
    return {'guard':guard,'normal_after':normal,'route':result}

def verify_anchor_route_entry(entry,state,manifest,inputs,row):
    need(entry.get('completion_kind')=='anchor-frame-guard-route-roundtrip-v1' and entry.get('state')=='complete','anchor-route-entry-kind-required')
    checked=verify_anchor_route_completion(entry['route_complete'],entry['guard_proof']);guard=checked['guard'];old=guard['original'];index=old['cursor']
    need(manifest==old['manifest'] and row==guard['row'] and inputs['query']['rows'][index]==row and state['calls'][:6]==old['calls'] and state['details'][:index]==old['details'],'anchor-route-original-prefix-changed')
    original=old['current'];need(all(entry.get(k)==v for k,v in original.items()) and entry['facts']==guard['facts'] and entry['normal_after']==checked['normal_after'],'anchor-route-entry-facts-changed')
    need(state['details'][index]==entry and state['cursor']>=index+1,'anchor-route-entry-not-committed')
    return entry['facts']

def unresolved_detail_calls(state):
    """Only one independently proven completed route can resolve its original guard call."""
    unresolved=[(index,call) for index,call in enumerate(state.get('calls',[])) if call.get('state')!='confirmed']
    entries=[entry for entry in state.get('details',[]) if entry.get('completion_kind')=='anchor-frame-guard-route-roundtrip-v1']
    if not entries:return [call for _,call in unresolved]
    entry=g.one(entries,'anchor-route-completion-not-unique');guard=verify_anchor_guard_proof(entry['guard_proof']);m=state['manifest'];v=guard['inputs'];verify_anchor_route_entry(entry,state,m,v,guard['row'])
    return [call for index,call in unresolved if index!=guard['call_index']]

def finish_anchor_guard_route(runner):
    marker=runner.s.get('anchor_guard_route_recovery')
    if marker is None:return False
    need(set(marker)=={'kind','guard_proof','route_complete'} and marker['kind']=='verified-anchor-frame-guard-route-completion-v1','anchor-route-marker-invalid')
    checked=verify_anchor_route_completion(marker['route_complete'],marker['guard_proof']);old=checked['guard']['original'];state=runner.s
    if state['cursor']>=3:
        verify_anchor_route_entry(state['details'][2],state,runner.manifest,runner.v,checked['guard']['row']);return False
    need(state['phase']=='verify-closed-unknown' and state['cursor']==len(state['details'])==2 and state['calls']==old['calls'] and state['details']==old['details'] and state['current']==old['current'] and state.get('last_error')==old.get('last_error'),'anchor-route-exact-original-state-required')
    import copy
    state=copy.deepcopy(state)
    entry=copy.deepcopy(old['current']);entry.update(state='complete',completion_kind='anchor-frame-guard-route-roundtrip-v1',guard_proof=marker['guard_proof'],route_complete=marker['route_complete'],normal_after=checked['normal_after'])
    state['details'].append(entry);state.update(cursor=3,current=None,phase='normal',last_observation=checked['normal_after']);state['observations'].append(checked['normal_after']);state.pop('hold',None);state.pop('waiting_for',None)
    verify_anchor_route_entry(entry,state,runner.manifest,runner.v,checked['guard']['row']);runner.s=state;runner.save();return True

def parse_frame(observation,row,drawer):
    iframe=g.one([n for n in g.walk(drawer) if n.get('tag')=='iframe' and n.get('attributes',{}).get('class')=='iframe-TNKSmG'],'governance-frame-not-unique');meta=iframe.get('public_frame',{});frame=iframe.get('public_frame_dom',{})
    need(meta.get('schema')=='public-notice-frame-metadata-v1' and meta.get('document_available') is True and meta.get('source_same_origin') is True and meta.get('source_origin')==meta.get('document_origin')=='https://life.douyin.com' and meta.get('source_path')==meta.get('document_path')==FRAME_PATH and meta.get('frame_input_enabled') is False and meta.get('query_and_fragment_excluded') is True and meta.get('ready_state')=='complete','governance-frame-origin-or-readiness-unverified')
    need(frame.get('kind')=='same-origin public notice DOM (read-only)' and frame.get('url')=='https://life.douyin.com'+FRAME_PATH and frame.get('frame_selector')==iframe['selector'] and frame.get('input_enabled') is False and isinstance(frame.get('root'),dict),'governance-frame-public-projection-invalid');ns=list(g.walk(frame['root']));prefix='readonly-frame:'+iframe['selector']+' :: '
    need(all(n.get('selector','').startswith(prefix) and n.get('tag') not in ('form','input','textarea','select') and not ('contenteditable' in n.get('attributes',{}) and str(n['attributes']['contenteditable']).lower()!='false') for n in ns),'governance-frame-projection-prefix-or-input-invalid')
    title=g.one([n for n in ns if 'by-header__title_overhide' in g.cls(n)],'governance-frame-title-unreviewed')
    if g.text(title)=='锚点使用建议':return parse_anchor_advice_frame(observation,row,drawer,iframe,frame,ns)
    need(g.text(title)=='生活服务违规通知','governance-frame-title-changed')
    idboxes=[n for n in ns if n.get('attributes',{}).get('class')=='contain-JTlbxU'];box=g.one(idboxes,'governance-frame-id-box-unreviewed');ch=box.get('children',[]);need(len(ch)==2 and all(n.get('tag')=='div' and not n.get('children') for n in ch) and g.text(ch[0])=='违规ID：' and g.text(ch[1])==row['notice_id'],'governance-frame-source-id-mismatch')
    name=g.text(g.one([n for n in ns if n.get('attributes',{}).get('class')=='title-CuuGRg'],'governance-frame-live-title-unreviewed'))
    liveboxes=[n for n in ns if n.get('attributes',{}).get('class')=='content-O77F13' and len(n.get('children',[]))==2 and n['children'][0].get('attributes',{}).get('class')=='label-oepqo6' and g.text(n['children'][0])=='直播ID：'];livebox=g.one(liveboxes,'governance-frame-live-id-unreviewed');liveid=g.text(livebox['children'][1]);need(__import__('re').fullmatch(r'\d{1,32}',liveid) and row['object']==name+' 直播 '+liveid,'governance-frame-source-object-mismatch')
    reason=g.text(g.one([n for n in ns if n.get('tag')=='span' and n.get('attributes',{}).get('class')=='title_text-O3Pyp7'],'governance-frame-reason-unreviewed'));need(reason==row['reason'],'governance-frame-source-reason-mismatch')
    def info(label,optional=False):
        found=[n for n in ns if n.get('attributes',{}).get('class')=='info-_P_i_r' and len(n.get('children',[]))==2 and n['children'][0].get('attributes',{}).get('class')=='info_label-tpfKml' and g.text(n['children'][0])==label];
        if optional and not found:
            need(not any(n.get('name')==label for n in ns),'governance-frame-optional-label-malformed:'+label);return None,None
        box=g.one(found,'governance-frame-info-unreviewed:'+label);value=box['children'][1];need(value.get('attributes',{}).get('class')=='info_value-L1R7oy' and g.text(value),'governance-frame-info-value-unreviewed:'+label);return box['children'][0],value
    active_label,active=info('已生效处置');pending_label,pending=info('待生效处置',optional=True);time_label,time=info('处置生效时间');effective_time=g.text(time);need(__import__('re').fullmatch(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}',effective_time),'governance-frame-effective-time-unreviewed')
    leaves=active.get('children',[]);nested_effective_score=(len(leaves)==2 and leaves[0].get('tag')=='span' and not leaves[0].get('children') and g.text(leaves[0])=='直播间警告、' and leaves[1].get('tag')=='span' and leaves[1].get('attributes',{}).get('class')=='action-xvEFrF' and __import__('re').fullmatch(r'信用分-直播分-(?:0|[1-9][0-9]*)(?:\.[0-9]+)?分',g.text(leaves[1])) is not None and len(leaves[1].get('children',[]))==1 and leaves[1]['children'][0].get('tag')=='img' and not leaves[1]['children'][0].get('children') and not g.text(leaves[1]['children'][0]))
    need(leaves and (all(n.get('tag')=='span' and not n.get('children') and g.text(n) for n in leaves) or nested_effective_score),'governance-frame-effective-disposal-unreviewed');actions=[g.text(n) for n in leaves];pending_actions=[]
    if pending is not None:
        pending_children=pending.get('children',[]);need(len(pending_children)==1 and pending_children[0].get('tag')=='span' and pending_children[0].get('attributes',{}).get('class')=='action-xvEFrF' and g.text(pending_children[0])==g.text(pending) and all(n.get('tag')=='img' and not n.get('children') and not n.get('name') for n in pending_children[0].get('children',[])),'governance-frame-pending-disposal-shape-unreviewed');pending_actions=[g.text(pending)]
    regions=[n for n in ns if n.get('attributes',{}).get('class')=='contain-MmKgHi' and len(n.get('children',[]))==2 and n['children'][0].get('attributes',{}).get('class')=='header-H_wrfO' and g.text(n['children'][0]) in ('建议规则','建议规则 平台规则')];region=g.one(regions,'governance-frame-advice-section-unreviewed');heading=region['children'][0].get('children',[]);platform_tool_advice=len(heading)==2
    need(heading and heading[0].get('attributes',{}).get('class')=='title-MfzSKF' and not heading[0].get('children') and g.text(heading[0])=='建议规则','governance-frame-advice-title-unreviewed')
    if platform_tool_advice:
        link=heading[1];lc=link.get('children',[]);need(link.get('tag')=='div' and link.get('attributes',{}).get('class')=='rule_link-eSsqKY' and g.text(link)=='平台规则' and len(lc)==2 and lc[0].get('tag')=='span' and not lc[0].get('children') and g.text(lc[0])=='平台规则' and lc[1].get('tag')=='img' and not lc[1].get('children') and not g.text(lc[1]),'governance-frame-advice-platform-header-unreviewed')
    else:need(len(heading)==1,'governance-frame-advice-title-unreviewed')
    rich=region['children'][1];need(rich.get('attributes',{}).get('class')=='richText-vXrma_','governance-frame-advice-richtext-unreviewed');paragraphs=rich.get('children',[])
    if len(paragraphs)==1:
        paragraph=paragraphs[0];children=paragraph.get('children',[]);need(paragraph.get('attributes',{}).get('class')=='paragraph-HMGO6N' and len(children)==1,'governance-frame-plain-advice-paragraph-unreviewed');plain=children[0];labels=plain.get('children',[])
        if platform_tool_advice:
            need(plain.get('tag')=='span' and len(labels)==1 and labels[0].get('tag')=='span' and not labels[0].get('children') and g.text(labels[0])=='详情' and g.text(plain).endswith('详情'),'governance-frame-tool-advice-unreviewed');advice=g.text(plain)[:-len('详情')].rstrip();need(advice,'governance-frame-tool-advice-empty');advice_paragraphs=[{'text':advice,'selector':plain['selector'],'original_visible_text':g.text(plain),'excluded_link_label':'详情','excluded_link_selector':labels[0]['selector'],'extraction':'exact-parent-text-minus-observed-sole-detail-link-suffix'}]
        else:
            need(plain.get('tag')=='span' and len(labels)==1 and labels[0].get('tag')=='span' and not labels[0].get('children') and g.text(labels[0])==reason and g.text(plain).endswith(reason),'governance-frame-plain-advice-unreviewed');advice=g.text(plain)[:-len(reason)].rstrip();need(advice,'governance-frame-plain-advice-empty');advice_paragraphs=[{'text':advice,'selector':plain['selector'],'original_visible_text':g.text(plain),'excluded_rule_label':reason,'excluded_rule_label_selector':labels[0]['selector'],'extraction':'exact-parent-text-minus-observed-sole-rule-label-suffix'}]
        texts=[plain];advice_texts=[advice]
    else:
        need(len(paragraphs) in (3,4) and all(p.get('attributes',{}).get('class')=='paragraph-HMGO6N' and len(p.get('children',[]))==1 for p in paragraphs),'governance-frame-advice-paragraphs-unreviewed')
        intro=paragraphs[0]['children'][0];link=paragraphs[-1]['children'][0];need(intro.get('tag')=='span' and not intro.get('children') and g.text(intro)=='以下为AI解读建议' and g.text(link) in ('规则解析','【绝对化用语】规则解析'),'governance-frame-advice-boundaries-changed');texts=[p['children'][0] for p in paragraphs[1:-1]];need(all(n.get('tag')=='span' and not n.get('children') and g.text(n) for n in texts),'governance-frame-advice-lines-unreviewed');advice_texts=[g.text(n) for n in texts];advice_paragraphs=[{'text':g.text(n),'selector':n['selector']} for n in texts]

    facts={'schema':'governance-notice-frame-detail-v1','notice_id':row['notice_id'],'source_notice_row':row,'notification_time_observed':False,'reason':reason,'object_name':name,'object_type':'直播','object_id':liveid,'disposals':actions,'pending_disposals':pending_actions,'effective_statuses':['已生效'],'effective_time':effective_time,'effective_status_mapping':{'method':'exact-observed-section-label','label':'已生效处置','status':'已生效','selector':active_label['selector']},'disposal_observations':[{'label':'已生效处置','text':g.text(active),'status':'已生效','label_selector':active_label['selector'],'value_selector':active['selector'],'effective_time':effective_time,'effective_time_selector':time['selector']}]+([{'label':'待生效处置','text':g.text(pending),'status':'待生效','label_selector':pending_label['selector'],'value_selector':pending['selector']}] if pending is not None else []),'current_active_disposal_empty_label':[g.text(n) for n in ns if n.get('attributes',{}).get('class')=='empty-Pfg4kU'],'public_recommendation':'\n'.join(advice_texts),'public_recommendation_selectors':[n['selector'] for n in texts],'public_recommendation_paragraphs':advice_paragraphs,'public_recommendation_section':'建议规则','internal_rules_excluded_from_recommendation':True,'frame_evidence':{'iframe_selector':iframe['selector'],'frame_url':frame['url'],'id_selector':ch[1]['selector'],'live_id_selector':livebox['children'][1]['selector'],'read_only_projection':True},'observed_at':observation.get('observed_at'),'submitted':False}
    if nested_effective_score:
        facts['effective_action_observations']=[{'text':g.text(n),'selector':n['selector'],'label':'已生效处置','label_selector':active_label['selector'],'status':'已生效','temporal_scope':'historical-card'} for n in leaves]
        facts['current_active_disposal_observations']=[{'text':g.text(n),'selector':n['selector'],'temporal_scope':'current-active-banner'} for n in ns if n.get('attributes',{}).get('class')=='empty-Pfg4kU']
    if pending is None:facts['pending_label_observation']={'label':'待生效处置','present':False,'observation':'label-absent-from-complete-readonly-frame-DOM','frame_selector':iframe['selector']}
    return facts,outer_close(observation,drawer)


def comment_reply_object(why,row):
    """The DOM says 评价, not POI商家回复. Preserve that literal type."""
    need(not any(n.get('attributes',{}).get('class') in ('title-dxsxbW','title-iYC0Ic') for n in g.walk(why)),'governance-comment-mixed-object-unreviewed')
    value=field(why,'违规评论');ns=list(g.walk(value))
    obj=g.one([n for n in ns if n.get('attributes',{}).get('class')=='title-DVm52C'],'governance-comment-title-not-unique');children=obj.get('children',[])
    need(obj.get('tag')=='div' and len(children)==1 and children[0].get('tag')=='div','governance-comment-title-shape-unreviewed');body=children[0];tags=body.get('children',[])
    need(len(tags)==1 and tags[0].get('tag')=='span' and tags[0].get('attributes',{}).get('class')=='governance_merchant-tag governance_merchant-tag-size-md governance_merchant-tag-default-light tag-d7m6Jd' and not tags[0].get('children') and g.text(tags[0])=='评价','governance-comment-tag-shape-unreviewed')
    original=g.text(body);need(g.text(obj)==original and original.startswith('评价') and len(original)>2,'governance-comment-body-unverified');text=original[2:]
    subject=g.one([n for n in ns if n.get('attributes',{}).get('class')=='poi-o_kcW5'],'governance-comment-subject-not-unique');ident=g.one([n for n in ns if n.get('attributes',{}).get('class')=='overhide-lBaYV8'],'governance-comment-id-not-unique')
    need(subject.get('tag')=='div' and not subject.get('children') and ident.get('tag')=='div' and not ident.get('children') and __import__('re').fullmatch(r'[0-9]{1,32}',g.text(ident)),'governance-comment-subject-id-shape-unreviewed')
    need(g.text(subject)==row['store_name'] and row['object']==text+' '+g.text(subject)+' 评价ID： '+g.text(ident),'governance-comment-source-object-mismatch')
    need(row['disposal']=='平台对该回复下线' and row['reason']=='内容涉及不友善用语','governance-comment-reply-evidence-unreviewed')
    return text,{'object_id':g.text(ident),'store_name':g.text(subject),'object_subtype':'商家回复','normalized_type_basis':{'method':'exact-comment-field-source-object-and-reply-disposal-v1','raw_detail_type':'评价','subtype':'商家回复','source_disposal':row['disposal'],'source_object':row['object'],'comment_field':'违规评论','body_selector':body['selector'],'tag_selector':tags[0]['selector'],'subject_selector':subject['selector'],'id_selector':ident['selector'],'center_distribution_type_not_inferred_here':True}}

def comment_reply_period(disposal,when):
    actions=[n for n in g.walk(disposal) if n.get('attributes',{}).get('class')=='punishDesc-if9lH1'];statuses=[n for n in g.walk(disposal) if 'status-Qza4ge' in g.cls(n)];times=[n for n in g.walk(disposal) if n.get('attributes',{}).get('class')=='time-APdNEp']
    action=g.one(actions,'governance-comment-action-not-unique');status=g.one(statuses,'governance-comment-status-not-unique');period=g.one(times,'governance-comment-period-not-unique');ch=period.get('children',[])
    need(action.get('tag')=='div' and status.get('tag')=='span' and g.text(action)=='平台对该回复下线' and not action.get('children') and g.text(status)=='已生效' and not status.get('children'),'governance-comment-disposal-status-unreviewed')
    need(len(ch)==2 and ch[0].get('tag')=='span' and not ch[0].get('children') and g.text(ch[0])==when+'~处置解除' and g.text(period)==g.text(ch[0]) and ch[1].get('tag')=='span' and ch[1].get('attributes',{}).get('class')=='governance_merchant-popper-trigger governance_merchant-popper-trigger-hover governance_merchant-tooltip tips-JJfIr5' and len(ch[1].get('children',[]))==1 and ch[1]['children'][0].get('tag')=='svg' and all(n.get('tag') in ('span','svg','g','path') and not g.text(n) for n in g.walk(ch[1])),'governance-comment-period-shape-unreviewed')
    return {'text':g.text(period),'start':when,'end_condition':'处置解除','end_observed':False,'selector':ch[0]['selector']},{'action_selector':action['selector'],'status_selector':status['selector'],'detail_status':'已生效'}

def store_object_matches_source(why,obj,object_name,row):
    # 处置主体 may be the company. Bind the detail's store object to the
    # independent list 违规对象, preserving source store_name as subject.
    boxes=[n for n in g.walk(why)if n.get('attributes',{}).get('class')=='right-eQCLtZ'and len(n.get('children',[]))==2 and n['children'][0]==obj]
    box=g.one(boxes,'governance-detail-store-object-container');info=box['children'][1]
    need(info.get('attributes',{}).get('class')=='info-Ri1b7b'and len(info.get('children',[]))==2,'governance-detail-store-object-info');ident,address=info['children']
    need(ident.get('attributes',{}).get('class')=='id-i6Pk9B'and address.get('attributes',{}).get('class')=='location-mq9rDA','governance-detail-store-object-fields')
    ids=[n for n in ident.get('children',[])if n.get('tag')=='div'and n.get('attributes',{}).get('class')=='overhide-d7VsT8'and not n.get('children')];idnode=g.one(ids,'governance-detail-store-object-id')
    object_id=g.text(idnode);location=g.text(address)
    need(__import__('re').fullmatch(r'[0-9]{1,32}',object_id)and g.text(ident)==object_id and location,'governance-detail-store-object-id-address')
    composed=object_name+' 门店ID： '+object_id+' '+location
    # A captured 违规对象 cell that read empty predates its async fill; the drawer
    # identity judged above is then authoritative and the list cell stays display
    # only. A captured non-empty cell must still equal the drawer exactly.
    need(row['object']==composed or (row['object']=='' and async_object_display(composed) is not None),'governance-detail-source-object-mismatch')

def parse(observation,row):
    tree=observation['tree'];g.root(tree,g.RECORDS);drawer=g.one(drawers(tree),'governance-detail-shown-drawer-not-unique')
    if 'notice-drawer-vBipFK' in g.cls(drawer):return parse_frame(observation,row,drawer)
    need('notice-drawer-OIp9e3' in g.cls(drawer),'governance-detail-drawer-shape-unreviewed');ns=list(g.walk(drawer))
    title=g.one([n for n in ns if n.get('tag')=='h1' and n.get('attributes',{}).get('class')=='title-UTzrUd'],'governance-detail-title-not-unique');need(g.text(title)=='违规通知书','governance-detail-title-changed')
    notice=g.text(field(drawer,'罚单编号'));need(notice==row['notice_id'],'governance-detail-notice-mismatch');when=g.text(field(drawer,'通知时间'));need(__import__('re').fullmatch(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}',when),'governance-detail-notification-time-unreviewed')
    why=section(drawer,'我为什么违规');reason=g.text(field(why,'违规原因'));need(reason==row['reason'],'governance-detail-source-reason-mismatch')
    comment=any(n.get('attributes',{}).get('class')=='title-DVm52C' for n in g.walk(why));comment_fields=None
    merchant_fields=None
    if comment:object_name,comment_fields=comment_reply_object(why,row);object_type='评价'
    elif any(g.text(n)=='违规商家' and not n.get('children') for n in g.walk(why)):
        merchant=field(why,'违规商家');mn=list(g.walk(merchant))
        title=g.one([n for n in mn if class_family(n.get('attributes',{}).get('class'))=='title' and g.text(n)=='商家'+row['store_name']],'governance-merchant-title-mismatch')
        ident=g.one([n for n in mn if not n.get('children') and __import__('re').fullmatch(r'[0-9]{1,32}',g.text(n))],'governance-merchant-id-mismatch')
        object_name=row['store_name'];object_type='商家';need(row['object']==object_name+' 商家ID： '+g.text(ident),'governance-merchant-source-object-mismatch');merchant_fields={'object_id':g.text(ident),'merchant_identity_selector':ident['selector']}
    else:
        objects=[n for n in g.walk(why) if n.get('attributes',{}).get('class') in ('title-dxsxbW','title-iYC0Ic')];obj=g.one(objects,'governance-detail-object-title-unreviewed');ch=obj.get('children',[])
        need(len(ch)==2,'governance-detail-object-type-unreviewed');shop=obj['attributes']['class']=='title-dxsxbW' and ch[0].get('attributes',{}).get('class')=='overhide-d7VsT8' and 'tag-Hci1lf' in g.cls(ch[1]) and g.text(ch[1])=='门店';product=obj['attributes']['class']=='title-iYC0Ic' and ch[0].get('attributes',{}).get('class')=='overhide-moZytb' and 'tag-LV5bTQ' in g.cls(ch[1]) and g.text(ch[1])=='商品'
        need(shop or product,'governance-detail-object-type-unreviewed');object_name=g.text(ch[0]);object_type=g.text(ch[1]);need(object_name,'governance-detail-object-name-missing')
        if object_type=='门店':store_object_matches_source(why,obj,object_name,row)
    disposal=section(drawer,'对我的处置结果');actions=[g.text(n) for n in g.walk(disposal) if n.get('attributes',{}).get('class')=='punishDesc-if9lH1'];statuses=[g.text(n) for n in g.walk(disposal) if 'status-Qza4ge' in g.cls(n)];need(actions and all(actions) and statuses and all(statuses),'governance-detail-disposal-status-unreviewed')
    advice=section(drawer,'如何避免再次违规');texts=[n for n in g.walk(advice) if n.get('tag')=='span' and n.get('attributes',{}).get('class')=='textView-GrrExP'];need(0<len(texts)<=20,'governance-detail-public-advice-unreviewed')
    advice_paragraphs=[];has_evaluation_rule_suffix=False
    for n in texts:
        ch=n.get('children',[]);original=g.text(n);need(original,'governance-detail-public-advice-child-unreviewed');text=original
        if ch:
            need(len(ch)==1 and ch[0].get('tag')=='a' and ch[0].get('attributes',{}).get('class')=='violationLink-vOK7kM' and ch[0].get('role')=='link' and not ch[0].get('children'),'governance-detail-public-advice-child-unreviewed')
            label=g.text(ch[0]);need(label in ('规则解读','抖音生活服务评价违规治理规则解读','抖音生活服务餐饮行业即送商家上传门面照片') and original.endswith(label),'governance-detail-public-advice-child-unreviewed')
            if label in('抖音生活服务评价违规治理规则解读','抖音生活服务餐饮行业即送商家上传门面照片'):
                if label=='抖音生活服务餐饮行业即送商家上传门面照片':need(object_type=='门店'and reason=='门面照片拍摄不完整','governance-detail-storefront-advice-scope')
                text=original[:-len(label)].rstrip();need(text,'governance-detail-public-advice-empty-after-link');has_evaluation_rule_suffix=True
                advice_paragraphs.append({'text':text,'selector':n['selector'],'original_visible_text':original,'excluded_link_label':label,'excluded_link_selector':ch[0]['selector'],'extraction':'parent-visible-text-minus-observed-sole-rule-link-suffix'})
                continue
        advice_paragraphs.append({'text':text,'selector':n['selector']})
    recommendation='\n'.join(p['text'] for p in advice_paragraphs);need(len(recommendation)<=16000,'governance-detail-public-advice-too-long')
    close=g.one([n for n in drawer.get('children',[]) if n.get('tag')=='span' and n.get('attributes',{}).get('class')=='governance_merchant-drawer-close-icon'],'governance-detail-close-not-unique');icons=close.get('children',[]);need(len(icons)==1 and icons[0].get('tag')=='span' and icons[0].get('attributes',{}).get('class')=='governance_merchant-icon governance_merchant-icon-close' and not close.get('disabled'),'governance-detail-close-shape-unreviewed')
    facts={'schema':'governance-notice-detail-v1','notice_id':notice,'source_notice_row':row,'notification_time':when,'reason':reason,'object_name':object_name,'object_type':object_type,'disposals':actions,'effective_statuses':statuses,'public_recommendation':recommendation,'public_recommendation_section':'如何避免再次违规','internal_rules_excluded_from_recommendation':True,'observed_at':observation.get('observed_at'),'submitted':False}
    if merchant_fields:facts.update(**merchant_fields)
    if comment:
        period,status_evidence=comment_reply_period(disposal,when);facts.update(**comment_fields,effective_period=period,reply_disposal_evidence=status_evidence)
    if has_evaluation_rule_suffix:facts.update(public_recommendation_selectors=[n['selector'] for n in texts],public_recommendation_paragraphs=advice_paragraphs)
    elif len(texts)==1:facts['public_recommendation_selector']=texts[0]['selector']
    else:facts.update(public_recommendation_selectors=[n['selector'] for n in texts],public_recommendation_paragraphs=[{'text':g.text(n),'selector':n['selector']} for n in texts])
    return facts,{'op':'click','tabId':observation['tab_id'],'kind':'dismiss','locator':{'by':'selector','value':close['selector']}}

import verification_session as verification
def _inputs_uncached(m):
    need(m.get('kind')=='governance-detail-inspection-manifest-v1' and set(m)<= {'kind','inputs','tab_id','approved_version'},'governance-detail-manifest-invalid');need(set(m['inputs']) in ({'job','query'},{'job','query','adopt_probe','adopt_detail'}),'governance-detail-input-refs-invalid');v={k:document(r) for k,r in m['inputs'].items()};job=v['job'];nav.scope(job);q=v['query']
    need(q.get('fingerprint')==nav.tag(job) and q.get('tab_id')==m['tab_id'] and q.get('approved_version')==m['approved_version']==nav.VERSION and q.get('phase')=='capture-complete' and q.get('business_progress_changed') is False,'governance-detail-query-scope-incomplete')
    if 'preselected_record_range_reconciliation' in q:
        import preselected_record_range_recovery as preselected_range
        preselected_range.verify_continuation(q,job)
    need(g.complete_pages(q['pages'])==q['rows'] and q['rows'],'governance-detail-query-coverage-invalid')
    for page in q['pages']:
        raw=document(page['observation']);parsed=g.records_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']);need(parsed=={k:v for k,v in page.items() if k!='observation'},'governance-detail-original-query-page-changed')
    return v

def reply_matches(command,result,before):
    target=g.one([n for n in g.nodes(before['tree']) if n.get('selector')==command['locator']['value']],'governance-detail-intent-target-not-in-before');clicked=result.get('clicked',{})
    need(result.get('kind')==command['kind'] and result.get('version')==nav.VERSION and clicked.get('tag')==target.get('tag') and clicked.get('name')==target.get('name') and clicked.get('attributes',{}).get('class')==target.get('attributes',{}).get('class') and clicked.get('disabled') is not True,'governance-detail-action-reply-unverified')
    # Existing list page replies serialize a bare LI; the following exact-page
    # observation remains mandatory and is the authoritative effect check.
    need(clicked.get('selector')==command['locator']['value'] or (target.get('tag')=='li' and clicked.get('selector')=='li' and g.text(target).isdigit()),'governance-detail-action-reply-selector-changed')

def same_facts(a,b):
    def current(value,key=''):
        if isinstance(value,dict):return {k:current(v,k)for k,v in value.items()if k!='observed_at'}
        if isinstance(value,list):return [current(v,key)for v in value]
        if isinstance(value,str)and (key.endswith('selector')or key.endswith('selectors')):
            return __import__('re').sub(r':nth-of-type\(1\)','',value)
        return value
    return current(a)==current(b)
def pending_rectification_display(value):
    """Known public label + dynamic display; no deadline or identity assertion."""
    import re
    match=re.fullmatch(r'待整改 ((?:0|[1-9][0-9]*))天((?:[01][0-9]|2[0-3])):([0-5][0-9]):([0-5][0-9])',value) if type(value) is str else None
    if match is None:return None
    return {'label':'待整改','remaining_display':value[len('待整改 '):],'original_display':value}

def async_object_display(value):
    """违规对象 is an async-rendered list column: a capture can legitimately read it
    empty and the live page later shows the composed store identity. Only the exact
    reviewed shape the detail drawer itself builds and verifies (门店名 + 门店ID + 地址,
    see store_object_matches_source) counts as completion; any other text is a fact change."""
    import re
    match=re.fullmatch(r'(.+) 门店ID： ([0-9]{1,32}) (.+)',value) if type(value) is str else None
    if match is None:return None
    return {'shop':match.group(1),'object_id':match.group(2),'location':match.group(3)}


def async_object_completed(source,observed):
    """A later capture that only completed the async 违规对象 column is display, not a
    business fact change. Only the reviewed direction counts: the earlier capture read the
    column empty and the later one shows exactly the composed store identity the detail
    drawer itself rebuilds and verifies (see store_object_matches_source)."""
    return source==observed or (source=='' and async_object_display(observed) is not None)

def same_source_row(observed,source):
    """Compare business fields; each observation owns its current DOM locators."""
    # Pinned evidence arrives frozen: FrozenDict subclasses dict and is immutable by
    # contract, so an exact-type test would reject the same row it just read.
    if not isinstance(observed,dict) or not isinstance(source,dict):return False
    if set(observed)!=set(source):return False
    if any(observed[key]!=source[key] for key in observed if key not in ('object','selector','cell_selectors','detail')):return False
    return async_object_completed(source.get('object'),observed.get('object'))

def normal_page(tree,job,q):
    need(not drawers(tree),'governance-detail-normal-page-still-has-drawer');p=g.records_page(tree,start=job['start'],end_exclusive=job['end_exclusive']);original=g.one([x for x in q['pages'] if x['page']==p['page']],'governance-detail-current-page-not-in-query');need(p['total']==original['total'] and [r['notice_id'] for r in p['rows']]==[r['notice_id'] for r in original['rows']],'governance-detail-current-page-coverage-changed')
    fields=('notice_id','store_name','reason','severity','effective_status','disposal','violation_date')
    changed=[];rendered=[]
    for index,(fresh,source) in enumerate(zip(p['rows'],original['rows'])):
        need(all(fresh[k]==source[k] for k in fields),'governance-detail-current-row-facts-changed')
        if fresh['object']!=source['object']:
            # The list 违规对象 column renders asynchronously after the records
            # response: an empty captured cell that now shows exactly the composed
            # store identity is display completion, never a fact change. Original
            # query and fresh raw evidence stay intact; every downstream check reads
            # the captured (empty) value, as with the 待整改 counter above.
            need(async_object_completed(source['object'],fresh['object']),'governance-detail-current-row-facts-changed')
            rendered.append(index)
        if fresh['rectification_status']!=source['rectification_status']:
            old=pending_rectification_display(source['rectification_status']);new=pending_rectification_display(fresh['rectification_status'])
            need(old is not None and new is not None and old['label']==new['label'],'governance-detail-current-row-facts-changed')
            changed.append(index)
    if changed or rendered:
        # Only the display layer is dynamic. Return original source semantics for
        # membership/roundtrip checks; original query and fresh raw stay intact.
        rows=[dict(row) for row in p['rows']]
        for index in changed:rows[index]['rectification_status']=original['rows'][index]['rectification_status']
        for index in rendered:rows[index]['object']=original['rows'][index]['object']
        p={**p,'rows':rows}
    return p

def adopt(m,v):
    probe=v['adopt_probe'];q=v['query'];job=v['job'];row=q['rows'][0];need(probe.get('phase')=='profile-required' and probe.get('fingerprint')==q['fingerprint'] and probe.get('tab_id')==m['tab_id'] and probe.get('approved_version')==m['approved_version'] and probe.get('detail_notice_id')==row['notice_id'] and probe.get('query_ref')==m['inputs']['query'] and probe.get('last_observation')==m['inputs']['adopt_detail'] and all(c.get('state')=='confirmed' for c in probe.get('calls',[])),'governance-detail-original-probe-adoption-invalid')
    call=probe['calls'][-1];before=document(call['before']);page=normal_page(before['tree'],job,q);need(any(r['notice_id']==row['notice_id'] for r in page['rows']),'governance-detail-probe-normal-notice-missing');need(call['command']=={**g.detail_action(before['tree'],row['notice_id'],start=job['start'],end_exclusive=job['end_exclusive']),'tabId':m['tab_id']},'governance-detail-probe-original-open-mismatch');result=call.get('result',{});clicked=result.get('clicked',{});need(result.get('kind')=='navigation' and result.get('version')==m['approved_version'] and clicked.get('tag')=='a' and clicked.get('name')=='查看详情' and clicked.get('selector')==call['command']['locator']['value'],'governance-detail-probe-confirmation-invalid');parse(v['adopt_detail'],row)
    return {'notice_id':row['notice_id'],'normal_before':call['before'],'adopted_probe':m['inputs']['adopt_probe'],'original_open_call':call}

def _verify_completed_uncached(s,m,v,*,require_complete=True):
    q=v['query'];job=v['job'];need(s.get('manifest')==m and s.get('fingerprint')==q['fingerprint'],'governance-detail-state-manifest-changed')
    if 'stop_loss_route_recovery' in s:
        import stop_loss_route_recovery as route_recovery
        route_recovery.verify_continuation(s)
    if require_complete:need(s.get('phase')=='complete' and s.get('cursor')==len(q['rows']) and len(s.get('details',[]))==len(q['rows']),'governance-detail-inspections-incomplete')
    need(s.get('cursor')==len(s.get('details',[])),'governance-detail-cursor-count-mismatch')
    for i,detail in enumerate(s.get('details',[])):
        row=q['rows'][i];need(detail.get('state')=='complete' and detail.get('notice_id')==row['notice_id'],'governance-detail-completed-order-changed');before=document(detail['normal_before']);normal_page(before['tree'],job,q)
        if detail.get('completion_kind')=='anchor-frame-guard-route-roundtrip-v1':
            verify_anchor_route_entry(detail,s,m,v,row);continue
        if detail.get('completion_kind')=='stop-loss-roundtrip-v1':
            import governance_stop_loss
            governance_stop_loss.verify_entry(detail,s,m,v,row);continue
        if detail.get('completion_kind') in ('rates-direct-sidebar-roundtrip-v1','stock-direct-sidebar-roundtrip-v1','operation-direct-sidebar-roundtrip-v1','operation-control-direct-sidebar-roundtrip-v1'):
            import governance_stop_loss_production
            governance_stop_loss_production.verify_direct_entry(detail,s,m,v,row);continue
        if detail.get('completion_kind')=='rates-stop-loss-recovered-roundtrip-v1':
            import governance_rates_completion
            governance_rates_completion.verify_entry(detail,s,m,v,row);continue
        opening={**g.detail_action(before['tree'],row['notice_id'],start=job['start'],end_exclusive=job['end_exclusive']),'tabId':m['tab_id']}
        if detail.get('adopted_probe'):need(i==0 and detail['adopted_probe']==m['inputs'].get('adopt_probe') and detail['original_open_call']==adopt(m,v)['original_open_call'],'governance-detail-adopted-open-changed')
        else:
            calls=[c for c in s['calls'] if c['command']==opening and c['before']==detail['normal_before']];call=g.one(calls,'governance-detail-open-intent-not-unique')
            if call['state']=='unknown':need(detail.get('open_reconciliation')==detail['detail_observation'],'governance-detail-unknown-open-not-reconciled')
            else:
                need(call['state']=='confirmed','governance-detail-open-outcome-invalid');reply_matches(opening,call['result'],before)
        facts,close=parse(document(detail['detail_observation']),row);need(facts==detail['facts'] and close==detail['close_command'],'governance-detail-completed-facts-changed');recent,close_recent=parse(document(detail['before_close']),row);need(same_facts(facts,recent) and close==close_recent,'governance-detail-close-target-changed')
        closing=g.one([c for c in s['calls'] if c['command']==close and c['before']==detail['before_close']],'governance-detail-close-intent-not-unique')
        if closing['state']=='unknown':need(detail.get('close_reconciliation')==detail['normal_after'],'governance-detail-unknown-close-not-reconciled')
        else:
            need(closing['state']=='confirmed','governance-detail-close-outcome-invalid');reply_matches(close,closing['result'],document(detail['before_close']))
        after=normal_page(document(detail['normal_after'])['tree'],job,q);need(any(r['notice_id']==row['notice_id'] for r in after['rows']),'governance-detail-completed-return-notice-missing')
    return [d['facts'] for d in s.get('details',[])]

def _verify_completed_pinned(s,m,v,*,require_complete=True):
    # Current output verification only. No source-module graph or old prefix replay.
    return _verify_completed_uncached(s,m,v,require_complete=require_complete)

class Runner(query_api.Runner):
    def __init__(self,m,invoke=None):
        import copy
        self._verification_manifest=copy.deepcopy(m)
        binding=verification.Session(enabled=False,max_bytes=0).fingerprint(m,set());parent=verification.owner()
        self._verification_session=parent if parent is not None and getattr(parent,'manifest_binding',None)==binding else verification.Session(max_bytes=64*1024*1024)
        self._verification_session.manifest_binding=binding
        with verification.owner_session(self._verification_session):self._init_uncached(m,invoke)
    def _init_uncached(self,m,invoke=None):
        self.manifest=m;self.v=inputs(m);job=self.v['job'];querypath=Path(m['inputs']['query']['path']).resolve();state=querypath.parent/'governance-detail-operations'/nav.tag(job)/'state.json';state.parent.mkdir(parents=True,exist_ok=True);existed=state.exists();super().__init__(job,m['tab_id'],state,m['approved_version'],invoke)
        if existed:need(self.s.get('manifest')==m,'governance-detail-original-manifest-required')
        else:
            self.s.update(manifest=m,phase='normal',cursor=0,details=[],current=None)
            if 'adopt_probe' in self.v:self.s.update(current=adopt(m,self.v),phase='read-detail')
        self.detail_policy_ready=False;self.frame_detail_policy_ready=False
    def observe(self):
        # Keep all scope, identity, risk and raw evidence checks in the shared reader.
        ping=self.request({'op':'ping','tabId':self.tab});self.detail_policy_ready=ping.get('governance_detail_policy')=='notice-drawer-close-v1';self.frame_detail_policy_ready=ping.get('governance_frame_detail_policy')=='same-origin-notice-frame-v1';return super().observe()
    def action(self,command,phase,observation):
        if command['kind']=='dismiss':
            need(self.detail_policy_ready,'governance-detail-close-policy-not-loaded')
            if self.s.get('current',{}).get('facts',{}).get('schema') in ('governance-notice-frame-detail-v1','governance-anchor-advice-frame-detail-v1'):need(self.frame_detail_policy_ready,'governance-frame-detail-close-policy-not-loaded')
        entry={'state':'unknown','command':command,'before':observation,'intent_at':nav.stamp()};self.s['calls'].append(entry);self.s['phase']=phase+'-unknown';self.save();result=self.request(command);reply_matches(command,result,document(observation));entry.update(state='confirmed',result=result);self.s['phase']=phase;self.save()
    def wait(self,reason):
        n=self.s.get('readonly_wait',{}).get('checks',0)+1;self.s['readonly_wait']={'checks':n,'reason':reason,'phase':self.s['phase'],'last_observation':self.s['last_observation']};self.s['waiting_for']='readonly-state-recheck' if n<5 else 'readonly-state-exhausted-supervisor-repair';self.s['hold']=n>=5;self.save()
    def step(self):
        need(self.manifest==self._verification_manifest,'governance-detail-session-manifest-changed')
        with verification.owner_session(self._verification_session):return self._step_uncached()
    def request(self,command):
        need(verification.current() is None,'governance-detail-live-request-inside-pure-scope')
        return super().request(command)
    def _step_uncached(self):
        nav.scope(self.job)
        import governance_stop_loss_production as automatic
        if finish_anchor_guard_route(self):return self.s
        if automatic.dispatch_step(self).get('handled'):return self.s
        phase=self.s['phase'];q=self.v['query']
        if phase=='complete':verify_completed(self.s,self.manifest,self.v);return self.s
        if self.s.get('hold'):return self.s
        cursor=self.s['cursor'];row=q['rows'][cursor];tree=self.observe();obs=self.s['last_observation'];raw=document(obs)
        if phase in ('verify-page','verify-page-unknown'):
            p=normal_page(tree,self.job,q)
            if p['page']!=self.s['target_page']:self.wait('governance-detail-page-change-not-observed');return self.s
            self.s['phase']='normal';self.s.pop('readonly_wait',None);self.s.pop('waiting_for',None)
        elif phase in ('read-detail','read-detail-unknown'):
            if automatic.dispatch_step(self).get('handled'):return self.s
            frames=[n for n in g.walk(tree) if n.get('tag')=='iframe' and n.get('attributes',{}).get('class')=='iframe-TNKSmG']
            if len(frames)==1:
                meta=frames[0].get('public_frame',{})
                if meta.get('source_origin')==meta.get('document_origin')=='https://life.douyin.com' and meta.get('source_path')==meta.get('document_path')==FRAME_PATH and meta.get('ready_state') in ('loading','interactive'):
                    return self.s
            # Between the two paints the drawer shows the promo card without the advice
            # card. Reading there is a render state, not a missing section: re-read
            # through the existing bounded wait and never parse the transient drawer.
            if advice_section_pending(tree):self.wait('governance-detail-advice-section-not-yet-rendered');return self.s
            facts,close=parse(raw,row);current=self.s['current'];
            if phase=='read-detail-unknown':current['open_reconciliation']=obs
            current.update(detail_observation=obs,facts=facts,close_command=close);self.s['phase']='close-ready';self.s.pop('readonly_wait',None);self.s.pop('waiting_for',None)
        elif phase=='close-ready':
            facts,close=parse(raw,row);need(same_facts(facts,self.s['current']['facts']) and close==self.s['current']['close_command'],'governance-detail-changed-before-close');self.s['current']['before_close']=obs;self.action(close,'verify-closed',obs)
        elif phase in ('verify-closed','verify-closed-unknown'):
            if drawers(tree):
                parse(raw,row);self.wait('governance-detail-close-not-yet-observed');return self.s
            p=normal_page(tree,self.job,q);need(any(r['notice_id']==row['notice_id'] for r in p['rows']),'governance-detail-normal-return-notice-missing');
            if phase=='verify-closed-unknown':self.s['current']['close_reconciliation']=obs
            self.s['current'].update(normal_after=obs,state='complete');self.s['details'].append(self.s['current']);self.s.update(current=None,cursor=cursor+1,phase='complete' if cursor+1==len(q['rows']) else 'normal');self.s.pop('readonly_wait',None);self.s.pop('waiting_for',None)
        elif phase=='normal':
            p=normal_page(tree,self.job,q);target=g.one([x['page'] for x in q['pages'] if any(r['notice_id']==row['notice_id'] for r in x['rows'])],'governance-detail-source-notice-page-not-unique')
            if p['page']!=target:
                pager=g.one(g.classnodes(g.root(tree,g.RECORDS),'governance_merchant-pager'),'governance-detail-pager-not-unique');button=g.one([n for n in g.walk(pager) if n.get('tag')=='li' and 'governance_merchant-pager-item' in g.cls(n) and g.text(n)==str(target)],'governance-detail-target-page-unobserved');need(not({'governance_merchant-pager-item-disabled','governance_merchant-pager-item-checked'}&g.cls(button)),'governance-detail-target-page-unavailable');self.s['target_page']=target;self.action({**g.click(button,'navigation'),'tabId':self.tab},'verify-page',obs)
            else:
                command={**g.detail_action(tree,row['notice_id'],start=self.job['start'],end_exclusive=self.job['end_exclusive']),'tabId':self.tab};self.s['current']={'notice_id':row['notice_id'],'normal_before':obs};self.action(command,'read-detail',obs)
        else:raise ValueError('governance-detail-phase-unreviewed')
        need(self.s['cursor']==len(self.s['details']),'governance-detail-cursor-count-mismatch')
        if self.s['phase']=='complete':verify_completed(self.s,self.manifest,self.v)
        self.save();return self.s


def inputs(m):
    existing=verification.current()
    with verification.validation_scope():
        value=_inputs_uncached(m)
        return value if existing is not None else __import__('copy').deepcopy(value)

def verify_completed(s,m,v,*,require_complete=True):
    existing=verification.current()
    with verification.validation_scope():
        value=_verify_completed_pinned(s,m,v,require_complete=require_complete)
        return value if existing is not None else __import__('copy').deepcopy(value)


DETAIL_SECTION_SUCCESSOR_KIND='verified-violation-detail-advice-render-successor-v1'
DETAIL_SECTION_ERROR='governance-detail-section-unreviewed:'+ADVICE_SECTION

def successor_row(manifest,cursor):
    need(manifest.get('kind')=='governance-detail-inspection-manifest-v1' and isinstance(manifest.get('inputs'),dict),'detail-successor-manifest')
    query=document(manifest['inputs']['query']);job=document(manifest['inputs']['job']);rows=query.get('rows') or []
    need(type(cursor) is int and not isinstance(cursor,bool) and 0<=cursor<len(rows),'detail-successor-cursor-range')
    return query,job,rows[cursor]

def successor_after(engine,launcher,proof):
    """Only the failed read-only detail call moves. Every returned call, both companies
    and the order binding stay byte-identical, so no business fact is rewritten."""
    import copy
    need(engine.get('status')=='hold' and engine.get('error')==DETAIL_SECTION_ERROR,'detail-successor-engine-hold-required')
    calls=engine.get('calls') or []
    need(bool(calls) and calls[-1].get('state')=='failed' and calls[-1].get('step')=='details' and calls[-1].get('error')==DETAIL_SECTION_ERROR and 'result' not in calls[-1],'detail-successor-last-call-failed-detail')
    need(all(c.get('state')=='returned' and c.get('applied') is True for c in calls[:-1]),'detail-successor-prefix-must-be-complete')
    need('resolved_readonly_failures' not in engine and not engine.get('reboot_continuation'),'detail-successor-original-hold-only')
    active=copy.deepcopy(engine);index=len(calls)-1;failed=active['calls'].pop()
    active.update(status='running');active.pop('error');active['resolved_readonly_failures']=[{'index':index,'call':failed,'proof':proof}]
    need(launcher.get('status')=='hold' and launcher.get('error')=='execution-child-stopped' and launcher.get('order')==engine.get('order'),'detail-successor-launcher-hold-required')
    current=copy.deepcopy(launcher);current.update(status='running');current.pop('error')
    current.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':DETAIL_SECTION_ERROR,'recovery':proof})
    return active,current

def successor_verify(reference,*,installed=True):
    """Re-derive the whole admission from pinned evidence and the live journals."""
    value=document(reference)
    need(value.get('kind')==DETAIL_SECTION_SUCCESSOR_KIND and value.get('business_inputs')==0,'detail-successor-proof-schema')
    need(bool(value.get('task_id')) and bool(value.get('attempt_id')) and isinstance(value.get('run_root'),str),'detail-successor-proof-scope')
    root=Path(value['run_root'])
    engine=document(value['engine_before']);launcher=document(value['launcher_before']);state=document(value['detail_state'])
    need(state.get('phase')=='read-detail' and state.get('cursor')==len(state.get('details') or []) and not state.get('hold') and not state.get('waiting_for'),'detail-successor-detail-frontier')
    need(bool(state.get('calls')) and all(c.get('state')=='confirmed' for c in state['calls']),'detail-successor-confirmed-open-only')
    query,job,row=successor_row(state['manifest'],state['cursor'])
    need(state['current']['notice_id']==row['notice_id'],'detail-successor-notice-binding')
    transient=document(value['transient_observation']);settled=document(value['settled_observation'])
    need(advice_section_pending(transient['tree']) is True,'detail-successor-transient-must-be-pending')
    need(advice_section_pending(settled['tree']) is False,'detail-successor-settled-must-not-be-pending')
    need(settled.get('tab_id')==state.get('tab_id') and urlsplit(settled['tree'].get('url') or '').path==g.RECORDS,'detail-successor-settled-scope')
    need(not any(n.get('name') for n in g.nodes(settled['tree']) if n.get('name') in ('扫码登录','风险验证','安全验证','账号异常')),'detail-successor-risk-stop')
    facts,close=parse(settled,row)
    need(facts['schema']=='governance-notice-detail-v1' and facts['notice_id']==row['notice_id'] and bool(facts['public_recommendation']),'detail-successor-settled-parse')
    active,current=successor_after(engine,launcher,reference)
    need(active['order']==engine['order'] and active['companies']==engine['companies'] and active['calls']==engine['calls'][:-1],'detail-successor-business-prefix-changed')
    if installed:
        for name,want in (('engine.json',active),('launcher.json',current)):
            path=root/name;need(path.is_file() and json.loads(path.read_text())==want,'detail-successor-not-installed:'+name)
    return {'row':row,'facts':facts,'close':close,'active':active,'current':current,'transient_heads':3}

DETAIL_REPLAY_SUCCESSOR_KIND='verified-violation-detail-completion-replay-successor-v1'
DETAIL_REPLAY_ERROR='stop-auto-known-template-not-unique'
DETAIL_REPLAY_RESUME_PHASES=('verify-closed','verify-closed-unknown')
# Steps whose port performs no browser input at all, with the only errors admitted for them.
# Re-running one of these repeats no confirmed input; every UI-bearing step must use the
# verify-closed resume point instead, which is why it stays outside this table.
DETAIL_REPLAY_UI_FREE_STEPS=('source','profile')
DETAIL_REPLAY_STEP_ERRORS={'details':(DETAIL_REPLAY_ERROR,),
                           'source':('governance-disposal-literal-mapping-required',),
                           'profile':('governance-projection-rectification-shape',),
                           'frames':('region-AX-title-mismatch',)}
# 'frames' is not in DETAIL_REPLAY_UI_FREE_STEPS: it captures, so it resumes only because its
# own frame_state and capture-focus journal are already persisted at the capture phase.

def replay_successor_after(engine,launcher,proof):
    """Only the failed step moves. The step's already-confirmed inputs stay in the business
    journal; the call chain keeps every returned call byte-identical."""
    import copy
    calls=engine.get('calls') or []
    need(bool(calls) and calls[-1].get('step') in DETAIL_REPLAY_STEP_ERRORS,'detail-replay-successor-step-unreviewed')
    step=calls[-1]['step']
    need(engine.get('status')=='hold' and engine.get('error')==calls[-1].get('error') and engine.get('error') in DETAIL_REPLAY_STEP_ERRORS[step],'detail-replay-successor-engine-hold-required')
    need(calls[-1].get('state')=='failed' and 'result' not in calls[-1],'detail-replay-successor-last-call-failed-detail')
    need(all(c.get('state')=='returned' and c.get('applied') is True for c in calls[:-1]),'detail-replay-successor-prefix-must-be-complete')
    need(not engine.get('reboot_continuation'),'detail-replay-successor-not-a-reboot')
    active=copy.deepcopy(engine);index=len(calls)-1;failed=active['calls'].pop()
    active.update(status='running');active.pop('error')
    active['resolved_readonly_failures']=(engine.get('resolved_readonly_failures') or [])+[{'index':index,'call':failed,'proof':proof}]
    need(launcher.get('status')=='hold' and launcher.get('error')=='execution-child-stopped' and launcher.get('order')==engine.get('order'),'detail-replay-successor-launcher-hold-required')
    current=copy.deepcopy(launcher);current.update(status='running');current.pop('error')
    current.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','original_child_error':engine['error'],'recovery':proof})
    return active,current

def replay_successor_verify(reference,*,installed=True):
    """Re-derive the whole admission from pinned evidence and the live journals."""
    value=document(reference)
    need(value.get('kind')==DETAIL_REPLAY_SUCCESSOR_KIND and value.get('business_inputs')==0,'detail-replay-successor-proof-schema')
    need(bool(value.get('task_id')) and bool(value.get('attempt_id')) and isinstance(value.get('run_root'),str),'detail-replay-successor-proof-scope')
    root=Path(value['run_root'])
    engine=document(value['engine_before']);launcher=document(value['launcher_before']);state=document(value['detail_state'])
    need(bool(engine.get('calls')) and engine['calls'][-1].get('step') in DETAIL_REPLAY_STEP_ERRORS,'detail-replay-successor-step-unreviewed')
    step=engine['calls'][-1]['step']
    manifest=state['manifest'];need(manifest.get('kind')=='governance-detail-inspection-manifest-v1','detail-replay-successor-manifest-required');v=inputs(manifest)
    if step=='details':
        need(state.get('phase') in DETAIL_REPLAY_RESUME_PHASES,'detail-replay-successor-resume-phase')
        need(bool(state.get('details')) and state.get('cursor')==len(state.get('details')) and not state.get('hold') and not state.get('waiting_for'),'detail-replay-successor-detail-frontier')
        need(all(c.get('state')=='confirmed' for c in state.get('calls') or []),'detail-replay-successor-confirmed-inputs-only')
        row=v['query']['rows'][state['cursor']];need(state['current']['notice_id']==row['notice_id'],'detail-replay-successor-notice-binding')
        # The published reader must now finish the same replay the child died in, without UI.
        verify_completed(state,manifest,v,require_complete=False)
        closed=document(state['last_observation'])
        need(not drawers(closed['tree']) and urlsplit(closed['tree'].get('url') or '').path==g.RECORDS,'detail-replay-successor-closed-page-required')
    else:
        need(all(c.get('state')=='confirmed' for c in state.get('calls') or []),'detail-replay-successor-confirmed-inputs-only')
        need(state.get('phase')=='complete' and state.get('cursor')==len(v['query']['rows']) and len(state.get('details') or [])==state['cursor'] and not state.get('hold') and not state.get('waiting_for'),'detail-replay-successor-detail-not-final')
        row=v['query']['rows'][-1]
        verify_completed(state,manifest,v,require_complete=True)
        if step=='frames':
            # The frames port already scrolled and focused for this frame, so this continues the
            # same capture operation from its persisted phase. The title predicate is re-derived
            # from a frozen AX observation, never from the live window.
            pinned=value.get('frame_inputs') or {}
            need(set(pinned)=={'observation','capture_focus','frame_state','ax_title','out'},'detail-replay-successor-frame-inputs-required')
            need(all(isinstance(pinned[k],dict) and set(pinned[k])=={'path','sha256'} and Path(pinned[k]['path']).is_absolute() for k in ('observation','capture_focus','ax_title')),'detail-replay-successor-frame-inputs-required')
            need(isinstance(pinned['frame_state'],dict) and isinstance(pinned['out'],str) and Path(pinned['out']).is_absolute(),'detail-replay-successor-frame-inputs-required')
            state_=pinned['frame_state']
            # The focus journal is append-only evidence and the recorded state was pinned mid-write,
            # so its current bytes legitimately extend that reference: bind the same path, then read
            # and judge the current journal in full.
            need(state_.get('phase')=='capture' and state_.get('observation')==pinned['observation'] and (state_.get('capture_focus') or {}).get('path')==pinned['capture_focus']['path'],'detail-replay-successor-frame-not-at-capture')
            need(not (Path(pinned['out'])/'registration.json').exists(),'detail-replay-successor-frame-already-registered')
            focus=document(pinned['capture_focus'])
            need(focus.get('kind')=='violation-frame-focus-v1' and bool(focus.get('events')),'detail-replay-successor-frame-focus-required')
            last=focus['events'][-1]
            need(last.get('state')=='complete' and bool(last.get('calls')) and all(c.get('state')=='confirmed' for c in last['calls']),'detail-replay-successor-frame-focus-required')
            frozen=document(pinned['ax_title'])
            need(frozen.get('kind')=='violation-frame-ax-title-v1','detail-replay-successor-frame-title-required')
            need(document(pinned['observation']).get('tab',{}).get('title')==frozen.get('tab_title'),'detail-replay-successor-frame-title-required')
            import native_window_capture as window_api
            need(window_api.chrome_window_title(frozen.get('ax_title'),frozen.get('tab_title')) is True,'detail-replay-successor-frame-title-not-matched')
        if step=='profile':
            # The profile port only reads pinned capture bytes. Re-derive it here so the move is
            # admitted on the published generation, never on the one that just failed.
            pinned=value.get('profile_inputs') or {}
            need(set(pinned)=={'source','job','query','out'},'detail-replay-successor-profile-inputs-required')
            need(all(isinstance(pinned[k],dict) and set(pinned[k])=={'path','sha256'} and Path(pinned[k]['path']).is_absolute() for k in ('source','job','query')),'detail-replay-successor-profile-inputs-required')
            need(isinstance(pinned['out'],str) and Path(pinned['out']).is_absolute() and not Path(pinned['out']).exists(),'detail-replay-successor-profile-output-required')
            import prepare_records_profile as profiles
            need(profiles.derive(pinned['source'],pinned['job'],pinned['query'],evidence_contract=profiles.BUSINESS).get('status')=='DOM-derived-ready','detail-replay-successor-profile-not-derivable')
    active,current=replay_successor_after(engine,launcher,reference)
    need(active['order']==engine['order'] and active['companies']==engine['companies'] and active['calls']==engine['calls'][:-1] and active.get('phase')==engine.get('phase') and active.get('index')==engine.get('index'),'detail-replay-successor-business-prefix-changed')
    need(current['calls']==launcher['calls'],'detail-replay-successor-launcher-calls-changed')
    if installed:
        for name,want in (('engine.json',active),('launcher.json',current)):
            path=root/name;need(path.is_file() and json.loads(path.read_text())==want,'detail-replay-successor-not-installed:'+name)
    return {'row':row,'active':active,'current':current,'resume_phase':state['phase'],'step':step,
            'confirmed_inputs':len(state['calls']),'repeated_confirmed_inputs':0,'detail_entries':len(state['details'])}

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare');a.add_argument('--job',required=True);a.add_argument('--query',required=True);a.add_argument('--tab-id',type=int,required=True);a.add_argument('--approved-version',required=True);a.add_argument('--adopt-probe');a.add_argument('--adopt-detail');a.add_argument('--out',required=True);a=sp.add_parser('run');a.add_argument('--manifest',required=True);a.add_argument('--steps',type=int,choices=range(1,101),default=1);a=sp.add_parser('verify');a.add_argument('--manifest',required=True)
    args=p.parse_args()
    try:
        if args.verb=='prepare':
            need(bool(args.adopt_probe)==bool(args.adopt_detail),'governance-detail-adoption-pair-required');m={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':ref(args.job),'query':ref(args.query)},'tab_id':args.tab_id,'approved_version':args.approved_version}
            if args.adopt_probe:m['inputs'].update(adopt_probe=ref(args.adopt_probe),adopt_detail=ref(args.adopt_detail))
            v=inputs(m)
            if args.adopt_probe:adopt(m,v)
            out=Path(args.out).resolve()
            if out.exists():need(json.loads(out.read_text())==m,'governance-detail-manifest-conflict')
            else:exclusive(out,m)
            result={'ok':True,'manifest':str(out),'ui_used':False}
        elif args.verb=='verify':
            m=json.loads(Path(args.manifest).read_text());v=inputs(m);state=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])/'state.json';need(state.is_file(),'governance-detail-state-missing');s=json.loads(state.read_text());facts=verify_completed(s,m,v);result={'ok':True,'phase':'complete','completed_details':len(facts),'state':str(state),'state_sha256':nav.digest(state),'facts':facts,'ui_used':False,'business_progress_changed':False}
        else:
            m=json.loads(Path(args.manifest).read_text());v=inputs(m);folder=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job']);folder.mkdir(parents=True,exist_ok=True)
            with (folder/'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=Runner(m)
                try:
                    for _ in range(args.steps):
                        r.step()
                        if r.s['phase']=='complete':break
                        if r.s.get('waiting_for') or r.s.get('hold'):
                            import governance_stop_loss_production as automatic
                            if not automatic.can_continue_owned(r):break
                    r.save()
                except Exception as e:r.s['last_error']=str(e);r.save();raise
                result={'ok':True,'phase':r.s['phase'],'completed_details':len(r.s['details']),'total':len(v['query']['rows']),'state':str(r.file),'state_sha256':nav.digest(r.file),'waiting_for':r.s.get('waiting_for'),'business_progress_changed':False,'facts':[x['facts'] for x in r.s['details']] if args.verb=='verify' else None}
        print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
