"""Public Top10 is a cross-check, never the complete distribution source.

The full distribution is calculated from complete date-filtered records and
individually read object types, then checked against the center's legend and
every publicly listed Top10 bucket. No chart internals or pixel input.
"""
import re
from collections import defaultdict
from datetime import date,timedelta
import governance_dom as g

def center_page(tree,*,start,end_exclusive):
    root=g.root(tree,g.CENTER)
    end=(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat()
    g.need(g.date_value(tree)==start+' ~ '+end,'center-range-input-mismatch')
    summary=g.one(g.classnodes(root,'summary-RY8k0Q'),'center-summary-not-unique')
    label=g.text(summary).replace('/','-')
    g.need(start in label and end in label,'center-summary-range-mismatch')
    scope=g.one([n for n in g.classnodes(root,'governance_merchant-tab-bar-item') if g.text(n)=='全部'],'center-all-scope-not-unique')
    g.need('governance_merchant-tab-bar-item-active' in g.cls(scope),'center-all-scope-not-selected')
    if any('您暂无违规记录' in g.text(n) for n in g.classnodes(summary,'summaryText-zSe9bU')):
        return center_zero(tree,start=start,end_exclusive=end_exclusive)
    legend=g.one(g.classnodes(root,'legendContainer-qMBl3_'),'center-legend-not-unique')
    names=[g.text(n) for n in g.classnodes(legend,'legendText-wzfAPl')]
    g.need(names and all(names) and len(set(names))==len(names),'center-legend-incomplete-or-duplicate')
    panel=g.one(g.classnodes(root,'topList-DDjs8Y'),'center-top10-not-unique')
    rows=[]
    for item in g.classnodes(panel,'listItem-CaUVh0'):
        name=g.text(g.one(g.classnodes(item,'name-vjRMI5'),'center-bucket-name-not-unique'))
        meta=g.text(g.one(g.classnodes(item,'reasonMeta-MmgSDp'),'center-bucket-object-type-not-unique'))
        count=g.text(g.one(g.classnodes(item,'count-PUTPse'),'center-bucket-count-not-unique'))
        rank=g.text(g.one(g.classnodes(item,'rank-mj9wvJ'),'center-bucket-rank-not-unique'))
        g.need(meta.startswith('违规对象类型：') and re.fullmatch(r'[1-9]\d*',count) and re.fullmatch(r'[1-9]\d*',rank),'center-bucket-literal-invalid')
        types=[x.strip() for x in meta.split('：',1)[1].split('、')]
        g.need(name in names and types and all(types) and len(set(types))==len(types),'center-bucket-type-or-legend-mismatch')
        rows.append({'rank':int(rank),'violation_type':name,'object_types':types,'count':int(count)})
    g.need(rows and len(rows)<=5,'center-top10-page-empty-or-too-large')
    pagers=g.classnodes(panel,'governance_merchant-pager')
    if not pagers:
        # Observed compact Top10 omits its pager when its complete legend fits.
        # This proves one Top10 page only; records still need independent query.
        import center_analysis_tab
        g.need(center_analysis_tab.tabs(tree)['analysis_active'],'center-analysis-tab-not-active')
        distribution=g.one(g.classnodes(root,'distributionView-C7cPRe'),'center-distribution-not-unique')
        g.need(any(n is panel for n in g.walk(distribution)) and any(n is legend for n in g.walk(distribution)),'center-single-page-distribution-conflict')
        children=panel.get('children',[])
        g.need(len(children)==2 and 'header-RySODJ' in g.cls(children[0]) and 'list-FeirmF' in g.cls(children[1]),'center-single-page-structure-conflict')
        title=g.one(g.classnodes(children[0],'title-KYD1nB'),'center-top10-title-not-unique')
        g.need(g.text(title)=='违规原因 Top10','center-top10-title-conflict')
        g.need(all('listItem-CaUVh0' in g.cls(n) for n in children[1].get('children',[])) and len(children[1].get('children',[]))==len(rows),'center-single-page-list-conflict')
        g.need(not g.classnodes(distribution,'governance_merchant-pager-item'),'center-single-page-orphan-pager')
        g.need(not any(n.get('role')=='progressbar' or n.get('attributes',{}).get('aria-busy')=='true' for n in g.walk(distribution)),'center-single-page-loading')
        g.need(len(names)==len(rows)<=5 and {r['violation_type'] for r in rows}==set(names),'center-single-page-legend-incomplete')
        g.need([r['rank'] for r in rows]==list(range(1,len(rows)+1)),'center-ranks-not-consecutive')
        return {'page':1,'page_count':1,'legend':names,'top10':rows,'start':start,'end_exclusive':end_exclusive,'next':None}
    pager=g.one(pagers,'center-pager-not-unique')
    items=g.classnodes(pager,'governance_merchant-pager-item')
    current=g.one([n for n in items if 'governance_merchant-pager-item-checked' in g.cls(n)],'center-current-page-not-unique')
    g.need(re.fullmatch('[1-9][0-9]*',g.text(current)),'center-current-page-invalid')
    page=int(g.text(current));numbers=[int(g.text(n)) for n in items if re.fullmatch('[1-9][0-9]*',g.text(n))]
    g.need(numbers==list(range(1,max(numbers)+1)) and page in numbers,'center-page-numbers-incomplete')
    g.need([r['rank'] for r in rows]==list(range((page-1)*5+1,(page-1)*5+1+len(rows))),'center-ranks-not-consecutive')
    return {'page':page,'page_count':max(numbers),'legend':names,'top10':rows,'start':start,'end_exclusive':end_exclusive,
            'next':None if page==max(numbers) else g.click(g.one([n for n in items if g.text(n)==str(page+1)],'center-next-page-not-unique'),'navigation')}

def center_zero(tree,*,start,end_exclusive):
    """Only analysis is zero; complete independently queried records remain required."""
    root=g.root(tree,g.CENTER);end=(date.fromisoformat(end_exclusive)-timedelta(days=1)).isoformat()
    g.need(g.date_value(tree)==start+' ~ '+end,'center-range-input-mismatch')
    import center_analysis_tab
    g.need(center_analysis_tab.tabs(tree)['analysis_active'],'center-analysis-tab-not-active')
    selected=g.one([n for n in g.classnodes(root,'governance_merchant-tab-bar-item') if g.text(n)=='全部'],'center-all-scope-not-unique');g.need('governance_merchant-tab-bar-item-active' in g.cls(selected),'center-all-scope-not-selected')
    distribution=g.one(g.classnodes(root,'distributionView-C7cPRe'),'center-distribution-not-unique')
    summary=g.one(g.classnodes(distribution,'summary-RY8k0Q'),'center-summary-not-unique');literal=g.one(g.classnodes(summary,'summaryText-zSe9bU'),'center-zero-summary-not-unique')
    expected=start.replace('-','/')+'～'+end.replace('-','/')+'期间 您暂无违规记录，可选择其他时间范围查询相关违规信息～'
    g.need(literal.get('tag')=='p' and not literal.get('children') and g.text(literal)==expected,'center-zero-summary-range-or-literal-mismatch')
    chart=g.one(g.classnodes(distribution,'sectionEmpty-PdpC3y'),'center-zero-chart-not-unique');empty_chart=g.one([n for n in g.classnodes(chart,'governance_merchant-empty-inner-text') if g.text(n)=='暂无图表数据' and not n.get('children')],'center-zero-chart-empty-unverified')
    panel=g.one(g.classnodes(distribution,'topList-DDjs8Y'),'center-top10-not-unique');title=g.one(g.classnodes(panel,'title-KYD1nB'),'center-top10-title-not-unique');g.need(g.text(title)=='违规原因 Top10','center-top10-title-conflict')
    empty_top=g.one([n for n in g.classnodes(panel,'governance_merchant-empty-inner-text') if g.text(n)=='暂无数据' and not n.get('children')],'center-zero-top10-empty-unverified')
    g.need(not g.classnodes(distribution,'listItem-CaUVh0') and not g.classnodes(distribution,'legendText-wzfAPl') and not g.classnodes(distribution,'governance_merchant-pager-item'),'center-zero-positive-evidence-conflict')
    return {'schema':'governance-center-analysis-zero-v1','analysis_total':0,'start':start,'end_exclusive':end_exclusive,'scope':'全部','analysis_zero_verified':True,'records_queried':False,'records_zero_verified':False,'business_zero_verified':False,'source_selectors':{'date':g.date_input(tree)['selector'],'summary':literal['selector'],'chart_empty':empty_chart['selector'],'top10_empty':empty_top['selector']},'basis':'explicit-date-filtered-analysis-zero-summary-and-empty-chart-top10'}

def distribution_type(record,center_bucket=None):
    """Translate only observed detail/center display vocabularies.

    The capture assembler supplies this basis after full detail-chain replay.
    Keep the detail's original object_type; report the translation separately.
    """
    raw=record['object_type'];basis=record.get('detail_object_type_basis',{})
    target=raw
    ref=basis.get('observation',{})
    pinned=isinstance(ref,dict) and bool(ref.get('path')) and bool(re.fullmatch('[0-9a-f]{64}',str(ref.get('sha256',''))))
    if basis.get('object_type')==raw and pinned and re.fullmatch('[0-9]{1,32}',str(basis.get('object_id',''))):
        if (raw=='短视频' and basis.get('schema')=='governance-anchor-advice-frame-detail-v1'
            and record.get('reason')=='温馨提醒：锚点类型选择有误' and record.get('notice_kind')=='platform-anchor-reminder'
            and record.get('not_business_violation') is True and record.get('platform_non_violation_statement')=='该情况不属于违规，不会影响您的视频流量和账号。'
            and center_bucket is not None and center_bucket.get('violation_type')==record['reason'] and center_bucket.get('object_types')==['短视频内容']):target='短视频内容'
        elif raw=='直播' and basis.get('schema')=='governance-notice-frame-detail-v1':target='直播内容'
        elif (raw=='商品' and basis.get('schema')=='governance-stop-loss-detail-v1'
              and record.get('reason')=='门店商品缺货' and basis.get('store_name')==record.get('subject')
              and re.fullmatch('[0-9]{1,32}',str(basis.get('store_id','')))):
            target='门店商品'
        elif (raw=='商品' and basis.get('schema')=='governance-stock-stop-loss-detail-v1'
              and record.get('reason')=='门店商品缺货' and basis.get('store_name')==record.get('subject')):
            source=basis.get('source_binding',{})
            if (source.get('source_subject')==record.get('subject') and source.get('product_id')==basis['object_id']
                and str(source.get('source_object','')).endswith(' 所属门店：'+str(record.get('subject')))):
                target='门店商品'
        elif raw=='评价' and basis.get('schema')=='governance-notice-detail-v1':
            sub=basis.get('normalized_type_basis',{});mapped=record.get('normalized_type_basis',{})
            evidence=mapped.get('center_type_evidence',{})
            if (basis.get('object_subtype')=='商家回复' and record.get('object_subtype')=='商家回复'
                and sub.get('method')=='exact-comment-field-source-object-and-reply-disposal-v1'
                and sub.get('raw_detail_type')=='评价' and sub.get('subtype')=='商家回复'
                and sub.get('source_disposal')=='平台对该回复下线' and sub.get('comment_field')=='违规评论'
                and sub.get('center_distribution_type_not_inferred_here') is True
                and mapped==dict(sub,center_type_evidence=evidence)
                and center_bucket is not None and evidence.get('bucket')==center_bucket
                and center_bucket.get('violation_type')==record.get('reason')
                and center_bucket.get('object_types')==['POI评价商家回复']
                and evidence.get('observation',{}).get('path')
                and re.fullmatch('[0-9a-f]{64}',str(evidence.get('observation',{}).get('sha256','')))):
                target='POI评价商家回复'
    return target,None if raw==target else {'notice_id':record['notice_id'],'detail_object_type':raw,'center_object_type':target,'method':'observed-detail-template-and-center-vocabulary-v1','basis':basis}

def reconcile(pages,records):
    g.need(pages and records,'center-reconciliation-positive-evidence-required')
    first=pages[0]
    g.need([p['page'] for p in pages]==list(range(1,first['page_count']+1)),'center-top10-pagination-incomplete')
    g.need(all(all(p[k]==first[k] for k in ('page_count','legend','start','end_exclusive')) for p in pages),'center-scope-changed-across-pages')
    buckets=defaultdict(lambda:{'count':0,'types':set()});ids=set();type_mappings=[]
    top=[r for p in pages for r in p['top10']]
    g.need(len(top)==min(10,len(first['legend'])) and len({r['violation_type'] for r in top})==len(top),'center-top10-coverage-mismatch')
    center_buckets={r['violation_type']:r for r in top}
    for r in records:
        g.need(r.get('notice_id') and r['notice_id'] not in ids,'center-record-id-missing-or-duplicate');ids.add(r['notice_id'])
        g.need(r.get('detail_read') is True and r.get('object_type') and r.get('reason'),'center-record-detail-required')
        g.need(first['start']<=r['date']<first['end_exclusive'],'center-record-outside-range')
        typ,mapping=distribution_type(r,center_buckets.get(r['reason']))
        if mapping:type_mappings.append(mapping)
        b=buckets[r['reason']];b['count']+=1;b['types'].add(typ)
    g.need(set(buckets)==set(first['legend']),'center-legend-complete-record-reasons-mismatch')
    top=[r for p in pages for r in p['top10']]
    g.need(len(top)==min(10,len(buckets)) and len({r['violation_type'] for r in top})==len(top),'center-top10-coverage-mismatch')
    for r in top:
        b=buckets[r['violation_type']]
        g.need(r['count']==b['count'] and set(r['object_types'])==b['types'],'center-top10-record-bucket-mismatch')
    result={'rows':[{'violation_type':name,'object_types':sorted(buckets[name]['types']),'count':buckets[name]['count']} for name in first['legend']],
            'total':len(records),'start':first['start'],'end_exclusive':first['end_exclusive'],'scope':'全部',
            'all_pages_read':True,'all_reasons_read':True,'filters_verified':True,
            'basis':'complete-records-reconciled-with-center-legend-and-every-top10-page',
            'top10_is_complete_distribution':False}
    if type_mappings:result['detail_to_center_object_type_mappings']=type_mappings
    return result
