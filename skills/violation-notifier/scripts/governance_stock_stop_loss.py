"""Observed stock stop-loss public-page parser only. No UI, state or return action."""
import re
from datetime import datetime
from urllib.parse import urlsplit,parse_qs
import governance_detail as d
import governance_dom as g
nav=d.nav
PATH='/p/govern_fulfillment_v2/violation_stop_lose_notice'
SCHEMA='governance-stock-stop-loss-detail-v1'

def parse(raw,row,opening,job):
    nav.scope(job)
    g.need(raw.get('source')=='local-dom-bridge' and raw.get('not_business_capture') is True,'stock-stop-loss-source-invalid')
    before=d.document(opening['before']);g.need(before.get('source')=='local-dom-bridge' and before.get('tab_id')==raw.get('tab_id'),'stock-stop-loss-original-source-tab-changed')
    page=g.records_page(before['tree'],start=job['start'],end_exclusive=job['end_exclusive']);g.need(d.same_source_row(g.one([r for r in page['rows'] if r['notice_id']==row['notice_id']],'stock-stop-loss-original-row-not-unique'),row),'stock-stop-loss-original-row-changed')
    command={**g.detail_action(before['tree'],row['notice_id'],start=job['start'],end_exclusive=job['end_exclusive']),'tabId':raw['tab_id']}
    g.need(opening.get('state')=='confirmed' and opening.get('command')==command,'stock-stop-loss-original-open-unverified');d.reply_matches(command,opening['result'],before)
    tab=nav.context([{'tabs':[raw['tab']]}],raw['tab_id'],job['groupid']);old=nav.context([{'tabs':[before['tab']]}],raw['tab_id'],job['groupid']);u=urlsplit(tab['url']);q=parse_qs(u.query,keep_blank_values=True)
    g.need(tab.get('windowId')==old.get('windowId') and u.scheme=='https' and u.netloc=='life.douyin.com' and u.path==PATH and not u.fragment and set(q)=={'EnterFrom','TaskID','groupid'} and q['EnterFrom']==['home_violation_center'] and q['groupid']==[str(job['groupid'])] and len(q['TaskID'])==1 and re.fullmatch(r'ST[a-f0-9]{24}',q['TaskID'][0]),'stock-stop-loss-route-unreviewed')
    tree=raw['tree'];g.need(tree.get('url')=='https://life.douyin.com'+PATH,'stock-stop-loss-tree-route-changed');nav.identity(tree,job['identity'])
    root=g.one([n for n in g.nodes(tree) if n.get('attributes',{}).get('id')=='root'],'stock-stop-loss-root-not-unique');ns=list(g.walk(root))
    def exact(scope,classname,*,leaf=False):
        return g.one([n for n in g.walk(scope) if n.get('attributes',{}).get('class')==classname and (not leaf or not n.get('children'))],'stock-stop-loss-field-not-unique:'+classname)
    header=exact(root,'flex items-center my-[20px] mx-[32px]');hc=header.get('children',[])
    g.need(len(hc)==2 and hc[1].get('attributes',{}).get('class')=='flex items-center flex-wrap text-[20px] font-[600] leading-[28px]','stock-stop-loss-header-shape-changed')
    heading=hc[1];tags=heading.get('children',[]);g.need(len(tags)==1 and tags[0].get('tag')=='span' and tags[0].get('attributes',{}).get('class')=='flex justify-center items-center w-[64px] h-[28px] box-border tag-uZcwHX ml-[12px] text-[14px]' and not tags[0].get('children') and g.text(tags[0])=='已撤销' and g.text(heading)=='门店商品缺货 已撤销' and row['reason']=='门店商品缺货','stock-stop-loss-title-reason-status-mismatch')
    cards=[n for n in ns if {'pb-[8px]','rounded-[6px]'}<=g.cls(n)]
    def section(title):
        return g.one([n for n in cards if len(n.get('children',[]))==2 and n['children'][0].get('attributes',{}).get('class')=='flex items-center justify-between' and g.text(n['children'][0])==title],'stock-stop-loss-section-unreviewed:'+title)
    issue=section('我存在什么问题');product=exact(issue,'flex items-center leading-[22px] font-[500] text-[14px]',leaf=True);product_type=exact(issue,'px-[4px] ml-[8px] rounded-[2px] flex items-center h-[20px] box-border text-[#95989D] text-[12px] border-solid border-[#d3d9e0] border-[0.5px] flex-shrink-0',leaf=True)
    price=exact(issue,'flex items-center leading-[22px] text-[#95989D] text-[14px]',leaf=True);ident=exact(issue,'flex items-center leading-[22px] flex items-center text-[14px] text-[#95989d]');shop=exact(issue,'ml-[4px] text-[#95989d]',leaf=True);reason=exact(issue,'inner-ypwT7g',leaf=True)
    g.need(g.text(product_type)=='商品' and re.fullmatch(r'[0-9]{1,32}',g.text(ident)) and len(ident.get('children',[]))==2 and all(n.get('tag') in ('svg','g','path') and not g.text(n) for child in ident['children'] for n in g.walk(child)),'stock-stop-loss-product-id-or-tag-unreviewed')
    g.need(g.text(reason)==row['reason'] and g.text(shop)==row['store_name'] and row['object']==g.text(product)+' 商品 '+g.text(price)+' '+g.text(ident)+' 所属门店：'+g.text(shop),'stock-stop-loss-original-product-store-mismatch')
    impact=section('对我的影响');status=g.one([n for n in g.walk(impact) if n.get('tag')=='span' and not n.get('children') and 'govern_fulfillment_v2-tag-default' in g.cls(n)],'stock-stop-loss-impact-status-not-unique');action=exact(impact,'leading-[28px] text-[14px] text-[#101011]',leaf=True);period=exact(impact,'mt-[4px] leading-[18px] text-[14px] text-[#a8abb2]',leaf=True)
    pm=re.fullmatch(r'周期：(\d{4}/\d{2}/\d{2} \d{2}:\d{2}) ~ (\d{4}/\d{2}/\d{2} \d{2}:\d{2})',g.text(period))
    g.need(g.text(action)==row['disposal']=='门店商品不展示1天' and g.text(status)==row['effective_status']=='已撤销' and pm,'stock-stop-loss-disposal-period-status-mismatch')
    start,end=[datetime.strptime(x,'%Y/%m/%d %H:%M') for x in pm.groups()];g.need(start<end and start.date().isoformat()==row['violation_date'],'stock-stop-loss-period-date-mismatch')
    info=exact(root,'flex items-center text-[14px] leading-[22px] text-[#6C737A]');im=re.fullmatch(r'通知时间 (\d{4}/\d{2}/\d{2} \d{2}:\d{2}) 通知单ID ([A-Za-z0-9_-]+)',g.text(info));g.need(im and im.group(2)==row['notice_id'] and datetime.strptime(im.group(1),'%Y/%m/%d %H:%M').date().isoformat()==row['violation_date'],'stock-stop-loss-notification-binding-mismatch')
    # Notification timestamp is independent of the disposition period's start.
    advice=section('我该如何避免');blocks=g.classnodes(advice,'is-Lx65EE');g.need(len(blocks)==2,'stock-stop-loss-advice-block-count-unreviewed')
    marketing,stock=blocks;mc=marketing.get('children',[]);sc=stock.get('children',[])
    g.need(len(mc)==4 and mc[0].get('attributes',{}).get('class')=='is__title-g9Yj25' and not mc[0].get('children') and g.text(mc[0])=='开通体验补偿赔券','stock-stop-loss-marketing-boundary-unreviewed')
    g.need(len(sc)==2 and sc[0].get('attributes',{}).get('class')=='is__title-g9Yj25' and not sc[0].get('children') and g.text(sc[0])=='建议缺货门店及时备货，做好用户接待' and sc[1].get('attributes',{}).get('class')=='my-[8px] is__content-TWHNZz' and not sc[1].get('children') and g.text(sc[1]),'stock-stop-loss-stock-advice-shape-unreviewed')
    body=sc[1]
    facts={'schema':SCHEMA,'notice_id':row['notice_id'],'source_notice_row':row,'reason':row['reason'],'notification_time':im.group(1),'notification_time_label':'通知时间','notification_id_label':'通知单ID','notification_info_selector':info['selector'],'object_type':'商品','object_name':g.text(product),'object_id':g.text(ident),'store_name':g.text(shop),'store_id_observed':False,'disposals':[g.text(action)],'effective_statuses':[g.text(status)],'detail_effectiveness_status_observed':True,'table_effectiveness_status':row['effective_status'],'effective_period':{'start':pm.group(1),'end':pm.group(2),'original_text':g.text(period),'selector':period['selector'],'notification_time_is_independent':True},'disposal_observations':[{'text':g.text(action),'status':g.text(status),'section':'对我的影响','action_selector':action['selector'],'status_selector':status['selector'],'period_selector':period['selector'],'temporal_scope':'revoked-disposal'}],'public_recommendation':g.text(body),'public_recommendation_section':'我该如何避免','public_recommendation_selectors':[body['selector']],'public_recommendation_paragraphs':[{'text':g.text(body),'selector':body['selector'],'heading':g.text(sc[0]),'heading_selector':sc[0]['selector']}],'excluded_marketing_sections':[{'title':g.text(mc[0]),'selector':marketing['selector'],'reason':'feature-promotion-and-statistics-not-stock-rectification','excluded_from_actions_and_client_copy':True}],'internal_rules_excluded_from_recommendation':True,'source_binding':{'opening_before':opening['before'],'opening_command':opening['command'],'source_object':row['object'],'source_subject':row['store_name'],'product_id':g.text(ident),'recommendation_selector':body['selector'],'task_id':q['TaskID'][0],'route':PATH,'product_selector':product['selector'],'product_id_selector':ident['selector'],'store_selector':shop['selector'],'reason_selector':reason['selector'],'header_status_selector':tags[0]['selector']},'observed_at':raw['observed_at'],'submitted':False,'return_action_provided':False}
    return facts,None
