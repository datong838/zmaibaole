#!/usr/bin/env python3
"""Assemble and verify governance captures from immutable public DOM evidence. No UI."""
import argparse,json
from datetime import datetime,date,timedelta
from pathlib import Path
from urllib.parse import urlsplit
import governance_detail as detail
import governance_dom as g
import center_reconciliation as center
nav=detail.nav
need=g.need
PROFILE='observed-governance-public-dom-capture-v1'
class MappingRequired(ValueError):
    def __init__(self,report):super().__init__('governance-disposal-literal-mapping-required');self.report=report

def scope(observation,job,tab_id,window_id,path):
    need(observation.get('source')=='local-dom-bridge' and observation.get('tab_id')==tab_id,'governance-capture-observation-source-tab-mismatch')
    tab=nav.context([{'tabs':[observation['tab']]}],tab_id,job['groupid']);need(tab.get('windowId')==window_id,'governance-capture-window-changed');tree=observation['tree'];need(urlsplit(tab['url']).path==path and tree.get('url')=='https://life.douyin.com'+path,'governance-capture-route-mismatch');g.nodes(tree);nav.identity(tree,job['identity'])
    if 'navigation_fingerprint' in observation:need(observation['navigation_fingerprint']==nav.tag(job),'governance-capture-navigation-fingerprint-mismatch')
    if path==g.RECORDS:
        g.records_page(tree,start=job['start'],end_exclusive=job['end_exclusive'])
    at=datetime.fromisoformat(observation.get('observed_at',''));need(at.utcoffset() is not None,'governance-capture-observation-time-required');return at

def inputs(m):
    if m.get('kind')=='governance-zero-capture-manifest-v1':
        import governance_zero_capture as zero
        return zero.inputs(m)
    need(m.get('kind')=='governance-capture-manifest-v1' and set(m)=={'kind','profile_revision','inputs'} and m.get('profile_revision')==PROFILE,'governance-capture-manifest-invalid');refs=m['inputs'];need(set(refs)=={'job','query','detail_manifest','detail_state','center_pages'} and isinstance(refs['center_pages'],list) and refs['center_pages'],'governance-capture-inputs-invalid')
    v={k:detail.document(r) for k,r in refs.items() if k!='center_pages'};v['centers']=[detail.document(r) for r in refs['center_pages']];dm=v['detail_manifest'];need(dm['inputs']['job']==refs['job'] and dm['inputs']['query']==refs['query'],'governance-capture-detail-source-mismatch');dv=detail.inputs(dm);need(dv['job']==v['job'] and dv['query']==v['query'],'governance-capture-detail-inputs-changed')
    expected=Path(refs['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])/'state.json';need(Path(refs['detail_state']['path']).resolve()==expected,'governance-capture-original-detail-state-required');v['facts']=detail.verify_completed(v['detail_state'],dm,dv);return v

def anchor_advice_mapping(source,facts,entry,*,job):
    if facts.get('schema')!='governance-anchor-advice-frame-detail-v1':return None
    raw=detail.document(entry['detail_observation']);before=detail.document(entry['normal_before']);window=before['tab']['windowId'];tab=before['tab_id']
    for observation in (before,raw):scope(observation,job,tab,window,g.RECORDS)
    parsed,_=detail.parse(raw,source);need(parsed==facts and facts.get('not_business_violation') is True,'anchor-mapping-original-facts-required')
    page=g.records_page(before['tree'],require_date=False);need(detail.same_source_row(g.one([r for r in page['rows'] if r['notice_id']==source['notice_id']],'anchor-mapping-original-row-not-unique'),source),'anchor-mapping-original-row-changed')
    statement='该情况不属于违规，不会影响您的视频流量和账号。'
    explanation=facts['situation_explanation'];need(explanation['text'].endswith(statement) and source['reason']=='温馨提醒：锚点类型选择有误' and source['disposal']=='带货锚点修改为打卡锚点，无' and source['effective_status']=='生效中','anchor-mapping-literal-scope-required')
    return {'actions':['带货锚点修改为打卡锚点'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'notice_kind':'platform-anchor-reminder','not_business_violation':True,'platform_non_violation_statement':statement,'platform_situation_explanation':explanation,'action_details':[{'action':'带货锚点修改为打卡锚点','status':'平台已更换','temporal_scope':'observed-anchor-adjustment','original_text':facts['anchor_modification_observation']['text'],'original_label':'锚点类型已更换','value_selector':facts['anchor_modification_observation']['selector'],'effective_time':facts['modification_time'],'effective_time_selector':facts['modification_time_selector'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation']}],'disposal_stage_text':'平台锚点调整：'+facts['anchor_modification_observation']['text']+'（修改生效时间：'+facts['modification_time']+'）','disposal_literal_mapping':{'method':'exact-observed-anchor-reminder-and-platform-modification-v1','table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'trailing_none_preserved_in_table_literal':True,'platform_non_violation_statement':statement,'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation']},'detail_object_type_basis':{'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts['object_id'],'observation':entry['detail_observation'],'frame_evidence':facts['frame_evidence']}}

def staged_live_score_mapping(source,facts,entry):
    """Only the observed exact warning + pending six-point livestream pair.
    Reparse the pinned original DOM and table; caller supplied facts cannot grant this mapping.
    """
    if not(source.get('disposal')=='直播间警告，创作者信用分扣分' and source.get('effective_status')=='已生效' and facts.get('schema')=='governance-notice-frame-detail-v1' and facts.get('object_type')=='直播' and facts.get('disposals')==['直播间警告'] and facts.get('pending_disposals')==['信用分-直播分-6分'] and facts.get('effective_statuses')==['已生效']):return None
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source);need(parsed==facts,'governance-stage-mapping-original-detail-facts-mismatch')
    table_raw=detail.document(entry['normal_before']);page=g.records_page(table_raw['tree'],require_date=False);table=g.one([r for r in page['rows'] if r['notice_id']==source['notice_id']],'governance-stage-mapping-original-table-notice-missing');need(table['disposal']==source['disposal'] and table['effective_status']==source['effective_status'],'governance-stage-mapping-original-table-literals-mismatch')
    observations=facts.get('disposal_observations',[]);need(len(observations)==2 and [(o.get('label'),o.get('text'),o.get('status')) for o in observations]==[('已生效处置','直播间警告','已生效'),('待生效处置','信用分-直播分-6分','待生效')],'governance-stage-mapping-observed-labels-mismatch')
    mapping=facts.get('effective_status_mapping',{});need(mapping.get('method')=='exact-observed-section-label' and mapping.get('label')=='已生效处置' and mapping.get('status')=='已生效' and mapping.get('selector')==observations[0].get('label_selector'),'governance-stage-mapping-status-evidence-mismatch')
    actions=['直播间警告','创作者信用分扣分'];items=[]
    for action,obs in zip(actions,observations):
        need(obs.get('label_selector','').startswith('readonly-frame:') and obs.get('value_selector','').startswith('readonly-frame:'),'governance-stage-mapping-selector-evidence-missing')
        item={'action':action,'status':obs['status'],'original_text':obs['text'],'original_label':obs['label'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'label_selector':obs['label_selector'],'value_selector':obs['value_selector']}
        if 'effective_time' in obs:item['effective_time']=obs['effective_time'];item['effective_time_selector']=facts['disposal_observations'][0].get('effective_time_selector')
        items.append(item)
    return {'actions':actions,'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':items,'disposal_stage_text':'已生效：直播间警告；待生效（待扣，尚未扣除）：信用分-直播分-6分','disposal_literal_mapping':{'method':'observed-frame-warning-and-pending-live-score-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status']}}

def notice_drawer_effective_state_mapping(source,facts,entry):
    """Observed normal notice drawer whose disposal section already shows 已生效 while the
    table 生效情况 column still reads 生效中. Both literals are re-read from the pinned
    drawer leaves and the pinned table row; the row keeps the table literal as authoritative.
    """
    if not(facts.get('schema')=='governance-notice-detail-v1' and facts.get('disposals')==[source.get('disposal')] and len(facts.get('disposals') or [])==1 and facts.get('effective_statuses')==['已生效'] and source.get('effective_status')=='生效中'):return None
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source);need(parsed==facts,'governance-notice-state-mapping-original-detail-facts-mismatch')
    page=g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False);table=g.one([r for r in page['rows'] if r['notice_id']==source['notice_id']],'governance-notice-state-mapping-original-table-notice-missing');need(table['disposal']==source['disposal'] and table['effective_status']=='生效中','governance-notice-state-mapping-original-table-literals-mismatch')
    drawer=g.one(detail.drawers(raw['tree']),'governance-notice-state-mapping-drawer-not-unique');disposal=detail.section(drawer,'对我的处置结果')
    actions=[n for n in g.walk(disposal) if n.get('attributes',{}).get('class')=='punishDesc-if9lH1'];statuses=[n for n in g.walk(disposal) if 'status-Qza4ge' in g.cls(n)]
    need(len(actions)==1 and len(statuses)==1 and g.text(actions[0])==source['disposal'] and g.text(statuses[0])=='已生效','governance-notice-state-mapping-observed-leaves-changed')
    action=source['disposal'];binding={'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':actions[0]['selector'],'status_selector':statuses[0]['selector']}
    return {'actions':[action],'disposal_stage_text':'表列生效情况：生效中；处置区已生效：'+action,'action_details':[{'action':action,'status':'已生效','original_text':g.text(actions[0]),'original_label':'对我的处置结果',**binding}],'disposal_literal_mapping':{'method':'observed-notice-drawer-effective-state-v1','table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_observed_status':'已生效',**binding}}

def notice_summary_actions_mapping(source,facts,entry):
    """Expand the current table's action count using this notice's full drawer."""
    import re
    summary=re.fullmatch(r'(.+?)，(.+?)等([1-9][0-9]*)项处置',source.get('disposal',''))
    if facts.get('schema')!='governance-notice-detail-v1' or not summary:return None
    actions=facts['disposals'];statuses=facts['effective_statuses'];count=int(summary.group(3))
    need(len(actions)==len(statuses)==count and count>=2 and actions[0]==summary.group(1) and re.fullmatch(re.escape(summary.group(2))+r'(?:[1-9][0-9]*天)?',actions[1]) is not None,'governance-summary-actions-not-matched')
    need(statuses==[source['effective_status']]*count,'governance-summary-action-statuses-unmatched')
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source);need(parsed==facts,'governance-summary-actions-current-facts-changed')
    table=g.one([r for r in g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False)['rows']if r['notice_id']==source['notice_id']],'governance-summary-actions-current-row-missing')
    need(detail.same_source_row(table,source),'governance-summary-actions-current-row-changed')
    section=detail.section(g.one(detail.drawers(raw['tree']),'governance-summary-actions-current-drawer'),'对我的处置结果');action_nodes=g.classnodes(section,'punishDesc-if9lH1');status_nodes=g.classnodes(section,'status-Qza4ge')
    need([g.text(n)for n in action_nodes]==actions and [g.text(n)for n in status_nodes]==statuses,'governance-summary-actions-literals-changed')
    binding={'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation']}
    details=[{'action':action,'status':status,'original_text':action,'original_label':'对我的处置结果','value_selector':node['selector'],'status_selector':status_node['selector'],**binding}for action,status,node,status_node in zip(actions,statuses,action_nodes,status_nodes)]
    return {'actions':actions,'action_details':details,'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'disposal_stage_text':source['effective_status']+'：'+'；'.join(actions),'disposal_literal_mapping':{'method':'current-table-summary-expanded-by-current-drawer-v1','table_summary':source['disposal'],'detail_actions':actions,**binding}}

def summary_live_flow_mapping(source,facts,entry):
    """Observed table summary warning plus both effective detail action leaves."""
    absent=facts.get('pending_label_observation',{})
    if not(source.get('disposal')=='警告' and source.get('effective_status')=='已生效' and facts.get('schema')=='governance-notice-frame-detail-v1' and facts.get('object_type')=='直播' and facts.get('disposals')==['本场直播流量下降、','警告'] and facts.get('effective_statuses')==['已生效'] and facts.get('pending_disposals')==[] and absent.get('label')=='待生效处置' and absent.get('present') is False):return None
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source);need(parsed==facts,'governance-summary-mapping-original-detail-facts-mismatch')
    table=g.one([r for r in g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False)['rows'] if r['notice_id']==source['notice_id']],'governance-summary-mapping-original-table-notice-missing');need(table['disposal']=='警告' and table['effective_status']=='已生效','governance-summary-mapping-original-table-literals-mismatch')
    observations=facts.get('disposal_observations',[]);need(len(observations)==1 and observations[0].get('label')=='已生效处置' and observations[0].get('text')=='本场直播流量下降、警告' and observations[0].get('status')=='已生效','governance-summary-mapping-observed-labels-mismatch');obs=observations[0]
    mapping=facts.get('effective_status_mapping',{});need(mapping.get('method')=='exact-observed-section-label' and mapping.get('label')=='已生效处置' and mapping.get('status')=='已生效' and mapping.get('selector')==obs.get('label_selector'),'governance-summary-mapping-status-evidence-mismatch')
    iframe=g.one([n for n in g.nodes(raw['tree']) if n.get('public_frame_dom')],'governance-summary-mapping-frame-not-unique');frame_nodes=list(g.walk(iframe['public_frame_dom']['root']));value=g.one([n for n in frame_nodes if n.get('selector')==obs.get('value_selector')],'governance-summary-mapping-action-parent-missing');leaves=value.get('children',[]);need(len(leaves)==2 and [n.get('name') for n in leaves]==['本场直播流量下降、','警告'] and all(n.get('tag')=='span' and not n.get('children') for n in leaves),'governance-summary-mapping-action-leaves-changed')
    actions=['本场直播流量下降','警告'];items=[]
    for index,(action,leaf) in enumerate(zip(actions,leaves)):
        items.append({'action':action,'status':'已生效','original_text':leaf['name'],'original_label':obs['label'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'label_selector':obs['label_selector'],'value_selector':leaf['selector'],'effective_time':obs['effective_time'],'effective_time_selector':obs['effective_time_selector'],'display_normalization':'remove-one-observed-trailing-enumeration-comma' if index==0 else 'none'})
    return {'actions':actions,'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':items,'disposal_stage_text':'已生效：本场直播流量下降；已生效：警告','disposal_literal_mapping':{'method':'table-summary-plus-detail-effective-action-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'raw_effective_actions':['本场直播流量下降、','警告']}}

def historical_live_score_mapping(source,facts,entry):
    """Observed score summary with two historical effective actions and current banner."""
    if not(source.get('disposal')=='创作者信用分扣分' and source.get('effective_status')=='已生效' and facts.get('schema')=='governance-notice-frame-detail-v1' and facts.get('reason')=='以不当方式引导用户私下建立联系并交易' and facts.get('object_type')=='直播' and facts.get('disposals')==['直播间警告、','信用分-直播分-6分'] and facts.get('effective_statuses')==['已生效'] and facts.get('pending_disposals')==[] and facts.get('pending_label_observation',{}).get('present') is False and facts.get('current_active_disposal_empty_label')==['暂无生效中处置']):return None
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source);need(parsed==facts,'governance-historical-score-original-detail-facts-mismatch');table=g.one([r for r in g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False)['rows'] if r['notice_id']==source['notice_id']],'governance-historical-score-table-notice-missing');need(table==source,'governance-historical-score-table-literals-mismatch')
    observations=facts.get('effective_action_observations',[]);banner=facts.get('current_active_disposal_observations',[]);labels=facts.get('disposal_observations',[]);need(len(observations)==2 and [o.get('text') for o in observations]==facts['disposals'] and len(banner)==1 and banner[0].get('text')=='暂无生效中处置' and banner[0].get('temporal_scope')=='current-active-banner' and len(labels)==1 and labels[0].get('label')=='已生效处置' and labels[0].get('status')=='已生效','governance-historical-score-stage-evidence-mismatch');label=labels[0];mapping=facts.get('effective_status_mapping',{});need(mapping=={'method':'exact-observed-section-label','label':'已生效处置','status':'已生效','selector':label['label_selector']},'governance-historical-score-status-label-mismatch')
    items=[];actions=['直播间警告','信用分-直播分-6分']
    for index,(action,o) in enumerate(zip(actions,observations)):
        need(o.get('label')=='已生效处置' and o.get('status')=='已生效' and o.get('temporal_scope')=='historical-card' and o.get('label_selector')==label['label_selector'] and o.get('selector','').startswith('readonly-frame:'),'governance-historical-score-action-ref-mismatch');items.append({'action':action,'status':'已生效','temporal_scope':'historical-card','original_text':o['text'],'original_label':o['label'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'label_selector':o['label_selector'],'value_selector':o['selector'],'effective_time':label['effective_time'],'effective_time_selector':label['effective_time_selector'],'display_normalization':'remove-one-observed-trailing-enumeration-comma' if index==0 else 'none'})
    return {'actions':actions,'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':items,'current_active_disposal_empty_label':facts['current_active_disposal_empty_label'],'current_active_disposal_observations':[dict(banner[0],observation=entry['detail_observation'])],'disposal_stage_text':'历史已生效：直播间警告；历史已生效：信用分-直播分-6分；当前：暂无生效中处置','disposal_literal_mapping':{'method':'table-score-summary-plus-historical-detail-actions-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'raw_effective_actions':facts['disposals'],'current_banner':banner[0]}}

def stop_loss_mapping(source,facts,entry,*,state,manifest,inputs):
    if facts.get('schema')!='governance-stop-loss-detail-v1':return None
    import governance_stop_loss as stop
    need(stop.verify_entry(entry,state,manifest,inputs,source)==facts,'governance-stop-loss-original-detail-facts-mismatch')
    need(facts['disposals']==[source['disposal']] and facts['effective_statuses']==[] and facts.get('detail_effectiveness_status_observed') is False and facts.get('table_effectiveness_status')==source['effective_status'],'governance-stop-loss-status-provenance-mismatch')
    original=detail.document(entry['normal_before']);table=g.one([r for r in g.records_page(original['tree'],start=inputs['job']['start'],end_exclusive=inputs['job']['end_exclusive'])['rows'] if r['notice_id']==source['notice_id']],'governance-stop-loss-table-row-not-unique');need(table==source,'governance-stop-loss-source-row-changed')
    item={'action':source['disposal'],'status':source['effective_status'],'status_basis':'original-records-table','original_text':facts['disposals'][0],'original_label':'处置方式','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_action_selector':table['cell_selectors']['处置方式'],'table_status_selector':table['cell_selectors']['处置生效状态'],'detail_status_observed':False}
    return {'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'status_basis':'original-records-table','detail_effectiveness_status_observed':False,'action_details':[item],'disposal_stage_text':source['effective_status']+'（原违规记录表）：'+source['disposal'],'disposal_literal_mapping':{'method':'exact-stop-loss-disposal-table-status-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_status_observed':False}}

def rates_recovered_mapping(source,facts,entry,*,state,manifest,inputs):
    import governance_rates_completion as completion
    need(completion.verify_entry(entry,state,manifest,inputs,source)==facts,'governance-rates-recovered-original-facts-mismatch');need(facts.get('schema')=='governance-three-rates-stop-loss-detail-v1' and facts['disposals']==[source['disposal']] and facts['effective_statuses']==[source['effective_status']]==['已结束'] and source['disposal']=='推荐流量限制（轻度）','governance-rates-recovered-disposal-status-mismatch');ob=g.one(facts['disposal_observations'],'governance-rates-recovered-action-not-unique');period=facts['effective_period'];need(ob['text']==source['disposal'] and ob['status']==source['effective_status'] and ob['section']=='对我的影响','governance-rates-recovered-action-evidence-changed')
    action={'action':source['disposal'],'status':source['effective_status'],'temporal_scope':'ended-disposal','original_text':ob['text'],'original_label':ob['section'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':ob['action_selector'],'status_selector':ob['status_selector'],'period':period}
    return {'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':[action],'effective_period':period,'potential_consequences_excluded_from_actions_and_client_copy':True,'disposal_stage_text':'已结束：'+source['disposal']+'（'+period['start']+' ~ '+period['end']+'）','disposal_literal_mapping':{'method':'exact-three-rates-ended-disposal-period-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'period_selector':period['selector']}}


def permanent_product_ban_mapping(source,facts,entry):
    if not(source.get('reason')=='低质引流品履约差处置' and source.get('disposal')=='封禁商品'
           and source.get('effective_status')=='生效中' and facts.get('schema')=='governance-notice-detail-v1'
           and facts.get('object_type')=='商品' and facts.get('disposals')==['封禁商品永久']
           and facts.get('effective_statuses')==['已生效']):return None
    raw=detail.document(entry['detail_observation']);parsed,_=detail.parse(raw,source)
    need(parsed==facts,'governance-permanent-ban-original-facts-mismatch')
    table=g.one([r for r in g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False)['rows'] if r['notice_id']==source['notice_id']],'governance-permanent-ban-table-row-missing')
    need(table==source,'governance-permanent-ban-table-row-changed')
    section=detail.section(g.one(detail.drawers(raw['tree']),'governance-permanent-ban-drawer-required'),'对我的处置结果')
    action=g.one(g.classnodes(section,'punishDesc-if9lH1'),'governance-permanent-ban-action-not-unique')
    status=g.one(g.classnodes(section,'status-Qza4ge'),'governance-permanent-ban-status-not-unique')
    period=g.one(g.classnodes(section,'time-APdNEp'),'governance-permanent-ban-period-not-unique');children=period.get('children',[])
    need(not action.get('children') and g.text(action)=='封禁商品永久' and not status.get('children') and g.text(status)=='已生效'
         and len(children)==1 and children[0].get('tag')=='span' and not children[0].get('children')
         and g.text(period)==g.text(children[0])==facts['notification_time']+'~处置解除','governance-permanent-ban-detail-evidence-changed')
    observed_period={'text':g.text(period),'start':facts['notification_time'],'end_condition':'处置解除','end_observed':False,'selector':children[0]['selector']}
    item={'action':'封禁商品永久','status':source['effective_status'],'detail_status':'已生效','status_basis':'original-records-table-current-status',
          'original_text':g.text(action),'value_selector':action['selector'],'detail_status_selector':status['selector'],
          'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'effective_period':observed_period}
    return {'actions':['封禁商品永久'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],
            'detail_effectiveness_statuses':['已生效'],'action_details':[item],'effective_period':observed_period,
            'disposal_stage_text':'生效中（原违规记录表）：封禁商品；已生效（详情）：封禁商品永久；处置时段：'+g.text(period),
            'disposal_literal_mapping':{'method':'permanent-product-ban-table-current-and-detail-literals-v1','table_observation':entry['normal_before'],
                'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'detail_disposal':'封禁商品永久',
                'table_status':source['effective_status'],'detail_status':'已生效','status_literals_preserved_not_equated':True,'permanent_label_preserved':True}}

def comment_reply_status_mapping(source,facts,entry,center_pages,center_refs):
    if not(facts.get('schema')=='governance-notice-detail-v1' and facts.get('object_type')=='评价' and facts.get('object_subtype')=='商家回复' and source.get('reason')=='内容涉及不友善用语' and source.get('disposal')=='平台对该回复下线' and source.get('effective_status')=='生效中'):return None
    need(facts['disposals']==[source['disposal']] and facts['effective_statuses']==['已生效'],'governance-comment-table-detail-status-unreviewed')
    parsed,_=detail.parse(detail.document(entry['detail_observation']),source);need(parsed==facts,'governance-comment-mapping-original-facts-mismatch')
    table=g.one([r for r in g.records_page(detail.document(entry['normal_before'])['tree'],require_date=False)['rows'] if r['notice_id']==source['notice_id']],'governance-comment-mapping-table-row-missing');need(table==source,'governance-comment-mapping-table-row-changed')
    buckets=[{'observation':ref,'bucket':row} for page,ref in zip(center_pages,center_refs) for row in page['top10'] if row['violation_type']==source['reason'] and row['object_types']==['POI评价商家回复']]
    need(len(buckets)==1,'governance-comment-center-type-evidence-required')
    ob=facts['reply_disposal_evidence'];period=facts['effective_period']
    item={'action':source['disposal'],'status':source['effective_status'],'status_basis':'original-records-table-current-status','detail_status':'已生效','original_text':facts['disposals'][0],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_status_selector':source['cell_selectors']['处置生效状态'],'value_selector':ob['action_selector'],'detail_status_selector':ob['status_selector'],'effective_period':period}
    return {'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_effectiveness_statuses':facts['effective_statuses'],'action_details':[item],'effective_period':period,'object_subtype':facts['object_subtype'],'normalized_type_basis':dict(facts['normalized_type_basis'],center_type_evidence=buckets[0]),'disposal_stage_text':'生效中（原违规记录表）：'+source['disposal']+'；已生效（详情）：'+source['disposal']+'；处置时段：'+period['text'],'disposal_literal_mapping':{'method':'reply-removal-table-current-status-detail-effective-period-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_status':source['effective_status'],'detail_statuses':facts['effective_statuses'],'status_literals_preserved_not_equated':True,'period':period}}

def assemble(m,manifest_ref=None):
    if m.get('kind')=='governance-zero-capture-manifest-v1':
        import governance_zero_capture as zero
        return zero.assemble(m,manifest_ref)
    v=inputs(m);job=v['job'];query=v['query'];state=v['detail_state'];refs=m['inputs'];tab_id=v['detail_manifest']['tab_id'];raw_query=[detail.document(p['observation']) for p in query['pages']];window=raw_query[0]['tab']['windowId'];times=[];evidence=[]
    def observed(r,path):
        raw=detail.document(r);times.append(scope(raw,job,tab_id,window,path));evidence.append(r);return raw
    for p in query['pages']:observed(p['observation'],g.RECORDS)
    pages=[]
    for r in refs['center_pages']:
        raw=observed(r,g.CENTER);pages.append(center.center_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']))
    need(len(state['details'])==len(query['rows'])==len(v['facts']),'governance-capture-detail-coverage-incomplete')
    rows=[];mismatches=[];staged_mapping_used=False;stop_loss_mapping_used=False;rates_mapping_used=False;rates_chains=[]
    for source,facts,entry in zip(query['rows'],v['facts'],state['details']):
        need(source==facts.get('source_notice_row') and source['notice_id']==facts['notice_id']==entry['notice_id'],'governance-capture-notice-source-mismatch')
        if entry.get('completion_kind')=='anchor-frame-guard-route-roundtrip-v1':
            detail.verify_anchor_route_entry(entry,state,v['detail_manifest'],detail.inputs(v['detail_manifest']),source)
            for key in ('normal_before','detail_observation','before_close','normal_after'):observed(entry[key],g.RECORDS)
            checked=detail.verify_anchor_route_completion(entry['route_complete'],entry['guard_proof'])
            route=checked['route'];route_state=detail.document(route['route_state']);rawrefs=[route['center_after'],entry['normal_after']]
            for reference in rawrefs:
                raw=detail.document(reference);path=urlsplit(raw['tab']['url']).path;need(path in (g.CENTER,g.RECORDS),'anchor-capture-route-unreviewed');observed(reference,path)
            mapped=anchor_advice_mapping(source,facts,entry,job=job);staged_mapping_used=True
        elif entry.get('completion_kind') in ('rates-direct-sidebar-roundtrip-v1','stock-direct-sidebar-roundtrip-v1','operation-direct-sidebar-roundtrip-v1','operation-control-direct-sidebar-roundtrip-v1'):
            import governance_stop_loss_production as automatic
            for key in ('normal_before','normal_after'):observed(entry[key],g.RECORDS)
            observed(entry['detail_observation'],automatic.rates.PATH);rm=detail.document(entry['recovery_manifest']);rs=detail.document(entry['recovery_state']);parent=detail.document(rm['parent_state'])
            rawrefs=[parent['last_observation'],rs['normal_after']]
            for rawref in rawrefs:
                raw=detail.document(rawref);path=urlsplit(raw['tab']['url']).path;need(path in (g.CENTER,g.RECORDS,automatic.rates.PATH),'governance-direct-recovery-source-route-unreviewed');observed(rawref,path)
            rates_chains.append({'notice_id':source['notice_id'],'template_kind':entry['template_kind'],'manifest':entry['recovery_manifest'],'state':entry['recovery_state'],'source_parent':rm['parent_state'],'filter_snapshots':rs['filter_final_snapshots'],'center_pages':rs['center_pages']});mapped=automatic.capture_mapping(source,facts,entry,state=state,manifest=v['detail_manifest'],inputs=detail.inputs(v['detail_manifest']));rates_mapping_used=True
        elif entry.get('completion_kind')=='rates-stop-loss-recovered-roundtrip-v1':
            import governance_rates_stop_loss as rates
            for key in ('normal_before','normal_after'):observed(entry[key],g.RECORDS)
            observed(entry['detail_observation'],rates.PATH);rm=detail.document(entry['recovery_manifest']);rs=detail.document(entry['recovery_state']);parent=detail.document(rm['parent_state'])
            rawrefs=[parent['last_observation'],rs['normal_after']]
            for rawref in rawrefs:
                raw=detail.document(rawref);path=urlsplit(raw['tab']['url']).path;need(path in (g.CENTER,g.RECORDS,rates.PATH),'governance-rates-recovery-source-route-unreviewed');observed(rawref,path)
            rates_chains.append({'notice_id':source['notice_id'],'manifest':entry['recovery_manifest'],'state':entry['recovery_state'],'source_parent':rm['parent_state'],'filter_snapshots':rs['filter_final_snapshots'],'center_pages':rs['center_pages']});mapped=rates_recovered_mapping(source,facts,entry,state=state,manifest=v['detail_manifest'],inputs=detail.inputs(v['detail_manifest']));rates_mapping_used=True
        elif entry.get('completion_kind')=='stop-loss-roundtrip-v1':
            import governance_stop_loss as stop
            for key in ('normal_before','return_observation','normal_after'):observed(entry[key],g.RECORDS)
            for key in ('detail_observation','before_return'):observed(entry[key],stop.PATH)
            observed(entry['stage_evidence']['original_observation'],stop.PATH)
            mapped=stop_loss_mapping(source,facts,entry,state=state,manifest=v['detail_manifest'],inputs=detail.inputs(v['detail_manifest']));stop_loss_mapping_used=True
        else:
            for key in ('normal_before','detail_observation','before_close','normal_after'):observed(entry[key],g.RECORDS)
            mapped=notice_drawer_effective_state_mapping(source,facts,entry) or notice_summary_actions_mapping(source,facts,entry) or anchor_advice_mapping(source,facts,entry,job=job) or staged_live_score_mapping(source,facts,entry) or summary_live_flow_mapping(source,facts,entry) or historical_live_score_mapping(source,facts,entry) or comment_reply_status_mapping(source,facts,entry,pages,refs['center_pages']) or permanent_product_ban_mapping(source,facts,entry)
        if mapped:staged_mapping_used=True
        if mapped is None and (facts['disposals']!=[source['disposal']] or facts['effective_statuses']!=[source['effective_status']]):
            mismatches.append({'notice_id':source['notice_id'],'table':{'disposal':source['disposal'],'effective_status':source['effective_status']},'detail':{'disposals':facts['disposals'],'effective_statuses':facts['effective_statuses']},'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'query':refs['query'],'detail_state':refs['detail_state'],'decision':'unmapped-no-semantic-substitution'})
        rows.append({'notice_id':source['notice_id'],'date':source['violation_date'],'subject':source['store_name'],'reason':source['reason'],'object_type':facts['object_type'],'object_name':facts['object_name'],'actions':facts['disposals'],'effectiveness_status':source['effective_status'],'rectification_status':source['rectification_status'],'detail_read':True,'public_recommendation':facts['public_recommendation'],'public_recommendation_basis':{'section':facts['public_recommendation_section'],'selectors':facts.get('public_recommendation_selectors',[facts.get('public_recommendation_selector')]),'observation':entry['detail_observation']},'disposal_literal_mapping':{'method':'exact-single-literal-table-and-detail','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation']}})
        rows[-1]['detail_object_type_basis']={'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts.get('object_id'),'store_name':facts.get('store_name'),'store_id':facts.get('store_id'),'observation':entry['detail_observation']}
        if facts.get('object_subtype'):rows[-1]['detail_object_type_basis'].update(object_subtype=facts['object_subtype'],normalized_type_basis=facts['normalized_type_basis'])
        if mapped:rows[-1].update(mapped)
    if mismatches:raise MappingRequired({'kind':'governance-disposal-mapping-required-v1','profile_revision':PROFILE,'inputs':refs,'mismatches':mismatches,'capture_generated':False,'ui_used':False})
    analysis=center.reconcile(pages,rows)
    seen=set();unique=[]
    for r in evidence:
        key=(r['path'],r['sha256'])
        if key not in seen:seen.add(key);unique.append(r)
    result={'capture_schema':'governance-public-dom-capture-v1','profile_revision':PROFILE,'company':job['company'],'groupid':str(job['groupid']),'source':'local-dom-bridge','url':'https://life.douyin.com'+g.RECORDS+'?groupid='+str(job['groupid']),'observed_at':max(times).isoformat(),'account_verified':True,'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],'analysis':analysis,'records':{'start':job['start'],'end_exclusive':job['end_exclusive'],'scope':'全部','total':len(rows),'unread_only':False,'all_pages_read':True,'filters_verified':True,'rows':rows},'source_evidence_refs':{'job':refs['job'],'query':refs['query'],'detail_manifest':refs['detail_manifest'],'detail_state':refs['detail_state'],'center_pages':refs['center_pages'],'raw_observations':unique},'source_contract':{'record_distribution_basis':analysis['basis'],'top10_is_complete_distribution':False,'all_notice_details_verified':True,'disposal_mapping':'exact-single-literal-table-and-detail','platform_mutations':False}}
    if staged_mapping_used:result['source_contract']['disposal_mapping']='per-record-verified-literal-or-observed-frame-stage-mapping-v1'
    if stop_loss_mapping_used:result['source_contract']['disposal_mapping']='per-record-verified-literal-or-observed-frame-stage-or-stop-loss-table-status-v1'
    if rates_mapping_used:
        result['source_contract']['disposal_mapping']='per-record-verified-governance-template-mappings-v1';result['source_evidence_refs']['rates_recovery_chains']=rates_chains
    if manifest_ref is not None:result['capture_manifest']=manifest_ref
    return result

def _validate_uncached(path):
    path=Path(path).resolve();capture=json.loads(path.read_text());r=capture.get('capture_manifest');need(isinstance(r,dict),'governance-capture-manifest-reference-required');m=detail.document(r);expected=assemble(m,r);need(capture==expected,'governance-capture-derived-payload-mismatch');return capture

def validate(path):
    """Consume current producer output; never reassemble its acquisition chain."""
    capture=json.loads(Path(path).read_text());manifest=detail.document(capture['capture_manifest']);refs=manifest['inputs'];job=detail.document(refs['job'])
    need(manifest.get('kind')in('governance-capture-manifest-v1','governance-zero-capture-manifest-v1'),'governance-current-capture-manifest')
    need(capture.get('capture_schema')in('governance-public-dom-capture-v1','governance-public-dom-zero-capture-v1') and capture.get('source')=='local-dom-bridge' and capture.get('account_verified')is True,'governance-current-capture-contract')
    if capture['capture_schema']=='governance-public-dom-zero-capture-v1':need(manifest['kind']=='governance-zero-capture-manifest-v1' and capture['records']['total']==capture['analysis']['total']==0,'governance-current-zero-manifest')
    need(all(capture.get(k)==job[k]for k in('company','groupid','start','end_exclusive','identity')),'governance-current-capture-scope')
    records=capture['records'];rows=records['rows'];need(records['start']==job['start'] and records['end_exclusive']==job['end_exclusive'] and records.get('all_pages_read')is True and records.get('filters_verified')is True and records['total']==len(rows),'governance-current-record-scope')
    query=detail.document(refs.get('query')or refs['records_query']);need([r['notice_id']for r in query['rows']]==[r['notice_id']for r in rows],'governance-current-notice-coverage')
    if rows:
        state=detail.document(refs['detail_state']);need(state.get('phase')=='complete' and state['cursor']==len(state['details'])==len(rows),'governance-current-details-incomplete')
        for row,source,entry in zip(rows,query['rows'],state['details']):
            facts=entry['facts'];need(entry['state']=='complete' and entry['notice_id']==row['notice_id'] and facts['source_notice_row']==source,'governance-current-detail-source')
            expected={'notice_id':source['notice_id'],'date':source['violation_date'],'subject':source['store_name'],'reason':source['reason'],'object_type':facts['object_type'],'object_name':facts['object_name'],'actions':facts['disposals'],'effectiveness_status':source['effective_status'],'rectification_status':source['rectification_status'],'public_recommendation':facts['public_recommendation'],'detail_read':True}
            need(all(row.get(k)==value for k,value in expected.items()),'governance-current-business-field-changed')
    else:need(records['total']==capture['analysis']['total']==0,'governance-current-zero-conflict')
    return capture

def build(manifest_path,out):
    r=detail.ref(manifest_path);m=detail.document(r);capture=assemble(m,r);out=Path(out).resolve()
    if out.exists():need(json.loads(out.read_text())==capture,'governance-capture-output-conflict')
    else:detail.exclusive(out,capture)
    validate(out);return capture

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare')
    for k in ('job','query','detail-manifest','detail-state','out'):a.add_argument('--'+k,required=True)
    a.add_argument('--center-page',action='append',required=True);a.add_argument('--mapping-required-out');a=sp.add_parser('build');a.add_argument('--manifest',required=True);a.add_argument('--out',required=True);a.add_argument('--mapping-required-out');a=sp.add_parser('verify');a.add_argument('--capture',required=True);args=p.parse_args()
    try:
        if args.verb=='prepare':
            m={'kind':'governance-capture-manifest-v1','profile_revision':PROFILE,'inputs':{k:detail.ref(getattr(args,k)) for k in ('job','query','detail_manifest','detail_state')}};m['inputs']['center_pages']=[detail.ref(p) for p in args.center_page];assemble(m);out=Path(args.out).resolve()
            if out.exists():need(json.loads(out.read_text())==m,'governance-capture-manifest-conflict')
            else:detail.exclusive(out,m)
            result={'ok':True,'manifest':str(out),'ui_used':False}
        else:
            capture=build(args.manifest,args.out) if args.verb=='build' else validate(args.capture);result={'ok':True,'total':capture['records']['total'],'basis':capture['analysis']['basis'],'ui_used':False}
        print(json.dumps(result,ensure_ascii=False));return 0
    except MappingRequired as e:
        out=getattr(args,'mapping_required_out',None)
        if out:
            path=Path(out).resolve()
            if path.exists():need(json.loads(path.read_text())==e.report,'governance-capture-mapping-report-conflict')
            else:detail.exclusive(path,e.report)
        print(json.dumps({'ok':False,'error':str(e),'mapping_evidence':e.report,'ui_used':False},ensure_ascii=False));return 2
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'ui_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
