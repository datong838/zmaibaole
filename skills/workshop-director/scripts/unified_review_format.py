#!/usr/bin/env python3
"""WeCom brief formatting from original XLSX rows. Never sends messages.

The screenshot supplies layout only. Counts/details come exclusively from XLSX;
Uses separately verified same-scope public violation facts only for the brief.
Complaint messages remain independent. This module never collects or sends.
"""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import openpyxl
from ds_common import load_map,select_company
from ds_workbooks import load_reviews,aggregate,CATEGORIES,rating,empty,verify_stats

def verify_stats_rows(path,company,reviews):
    """Both sheets must equal every source-derived day/store/category cell.
    Grand totals alone cannot certify distribution or the four main quadrants.
    """
    daily,stores=aggregate(reviews);summary=['公司名称','日期','好评总数','图文好评','纯星好评','差评总数','图文差评','纯星差评','中间态合计','当日总计','中间态明细'];detail=['公司名称','日期','门店名称','新增评总数','好评总数','图文好评','纯星好评','差评反馈总数','图文差评','纯星差评','中间态合计']+CATEGORIES[4:]
    middle=lambda c:sum(c[k]for k in CATEGORIES[4:]);expected=[(summary,[[company,day,c['好评总数'],c['图文好评'],c['纯星好评'],c['差评总数'],c['图文差评'],c['纯星差评'],middle(c),c['当日总计'],'; '.join('%s：%d'%(k,c[k])for k in CATEGORIES[4:]if c[k])or'无']for day,c in sorted(daily.items())]),(detail,[[company,day,store,c['当日总计'],c['好评总数'],c['图文好评'],c['纯星好评'],c['差评总数'],c['图文差评'],c['纯星差评'],middle(c)]+[c[k]for k in CATEGORIES[4:]]for(day,store),c in sorted(stores.items())])]
    book=openpyxl.load_workbook(path,data_only=False)
    try:
        if book.sheetnames!=['每日四象限统计','按门店每日明细']:raise ValueError('unified-stats-sheet-schema')
        for sheet,(headers,rows)in zip(book.worksheets,expected):
            actual=[list(row)for row in sheet.iter_rows(values_only=True)]
            if not actual or actual[0]!=headers or actual[1:]!=rows:raise ValueError('unified-stats-day-store-category-mismatch')
            if any(type(actual[r][k])is not int for r,row in enumerate(rows,1)for k,value in enumerate(row)if type(value)is int):raise ValueError('unified-stats-numeric-cell-type')
    finally:book.close()
    return {'days':len(daily),'store_days':len(stores),'rows':len(reviews),'all_cells_reconciled':True}

def build(source,company,start,end,stats=None,*,dom_source=None):
    if dom_source is not None:
        from ds_common import dom_source_data
        from ds_workbooks import dom_reviews,dom_report_facts
        data=dom_source_data(dom_source,{'company':company,'groupid':dom_source['groupid']},{'start':start,'end':end},source)
        if stats:verify_stats_rows(stats,company,dom_reviews(data))
        return dom_report_facts(data,source)
    source=Path(source);reviews,headers=load_reviews(source,start,end)
    if stats:verify_stats_rows(stats,company,reviews)
    wb=openpyxl.load_workbook(source,data_only=False)
    try:
        ws=wb.active;columns=[c.value for c in ws[1]];raw=[]
        for rownum,cells in enumerate(ws.iter_rows(min_row=2,values_only=True),2):
            if all(empty(v) for v in cells):continue
            raw.append((rownum,dict(zip(columns,cells))))
    finally:wb.close()
    if len(raw)!=len(reviews):raise ValueError('source-row-count-mismatch')
    totals=Counter(r['category'] for r in reviews);daily,_=aggregate(reviews)
    stores={}
    for r in reviews:
        c=stores.setdefault(r['store'],Counter());c['total']+=1;c['good' if r['stars']>=4 else 'bad']+=1
    bad=[]
    for rownum,r in raw:
        if rating(r['推荐等级'])>3:continue
        text=str(r['文本内容']) if not empty(r['文本内容']) else '无文字内容'
        replied=r.get('商家是否回复')
        bad.append({'row':rownum,'store':r['门店名称'],'time':str(r['评价时间']),'stars':rating(r['推荐等级']),
                    'text':text,'image':not empty(r['图片内容']),'video':not empty(r['视频内容']),
                    'product':str(r.get('消费商品') or '未提供'),'source':str(r.get('评价来源') or '未提供'),
                    'reply':'未回复' if replied=='否' else '已回复' if replied=='是' else '未提供',
                    'reply_text':str(r.get('商家回复内容')) if not empty(r.get('商家回复内容')) else None})
    good=sum(v for k,v in totals.items() if k.endswith('好评'));negative=len(reviews)-good
    if negative!=len(bad) or sum(totals.values())!=len(reviews):raise ValueError('report-count-mismatch')
    return {'company':company,'start':start,'end':end,'source':str(source.resolve()),
            'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':len(reviews),'good':good,'bad':negative,
            'totals':dict(totals),'daily':{k:dict(v) for k,v in sorted(daily.items())},
            'stores':{k:dict(v) for k,v in sorted(stores.items())},'bad_details':bad,'test_only':True}

def render(d,brand,group,format_mode='test',*,violation_summary=None):
    if format_mode not in ('test','online'):raise ValueError('report-format-invalid')
    short=lambda iso:date.fromisoformat(iso).strftime('%m.%d')
    counts=d['totals']
    if (any(type(counts.get(k,0)) is not int or counts.get(k,0)<0 for k in CATEGORIES)
        or set(counts)-set(CATEGORIES) or sum(counts.values())!=d['rows']
        or sum(counts.get(k,0) for k in CATEGORIES if k.endswith('好评'))!=d['good']
        or d['good']+d['bad']!=d['rows']
        or sum(c['total'] for c in d['stores'].values())!=d['rows']
        or any(c.get('good',0)+c.get('bad',0)!=c['total'] for c in d['stores'].values())):
        raise ValueError('report-count-mismatch')
    period=short(d['start']) if d['start']==d['end'] else short(d['start'])+'—'+short(d['end'])
    lines=[f"【{brand}】{period}评价情况，请查收🌹"]
    if format_mode=='test':lines.extend(['（仅发测试群）',f'拟发群：{group}',f"统计范围：{d['start']}至{d['end']}，共{len(d['stores'])}家有评价门店。"])
    lines.extend(['',
           '评价方面：',f"本期新增{d['rows']}条评价，好评{d['good']}条，中差评{d['bad']}条。",(f"好评占比：{d['good']/d['rows']:.2%}（4—5星）。" if d['rows'] else "好评占比：—（本期无评价；4—5星）。")])
    if d.get('source_basis'):
        basis=d['source_basis'];basis_counts=basis['counts']
        if basis.get('kind')!='daily-visible-dom-source-v1'or basis.get('download_verified')is not False or basis.get('source_is_authoritative_export')is not False:raise ValueError('report-dom-basis-invalid')
        lines[lines.index('评价方面：')+1]=f"评价记录共{d['rows']}条（正常{basis_counts['normal']}条，折叠纯星{basis_counts['folded']}条），好评{d['good']}条，中差评{d['bad']}条。"
    for suffix,label in [('好评','好评分类'),('差评','中差评分类')]:
        parts=[f'{k[:-len(suffix)]}{counts.get(k,0)}条' for k in CATEGORIES if k.endswith(suffix) and counts.get(k,0)]
        lines.append(label+'：'+('；'.join(parts) if parts else '0条')+'。')
    lines.extend(['','按日汇总：'])
    for day,c in d['daily'].items():lines.append(f"{short(day)}：新增{c['当日总计']}条，好评{c.get('好评总数',0)}条，中差评{c.get('差评总数',0)}条。")
    lines.extend(['',f"中差评详情：共{d['bad']}条"])
    for index,r in enumerate(d['bad_details'],1):
        lines.extend([f"{index}. {r['store']}",f"评价时间：{r['time']}；评分：{r['stars']}星。",
                      f"顾客原文：{r['text']}",f"评价来源：{r['source']}；{'有图片' if r['image'] else '无图片'}，{'有视频' if r['video'] else '无视频'}。",
                      f"消费商品：{r['product']}",f"商家回复：{r['reply']}。"])
        if r.get('reply_text'):lines.append('回复内容：'+r['reply_text'])
        if index<len(d['bad_details']):lines.append('')
    lines.extend(['','门店汇总：'])
    for store,c in d['stores'].items():lines.append(f"{store}：共{c['total']}条，好评{c.get('good',0)}条，中差评{c.get('bad',0)}条。")
    if violation_summary is not None:
        if type(violation_summary)is not str or not violation_summary.startswith('违规方面：\n'):raise ValueError('report-violation-summary-invalid')
        lines.extend(['',violation_summary])
    pending=sum(r['reply']=='未回复' for r in d['bad_details'])
    lines.extend(['',f'待跟进：表内有{pending}条中差评尚未回复，请核实后处理。' if pending else '待跟进：请结合中差评详情核实处理情况。'])
    return '\n'.join(lines)+'\n'


def violation_brief(source,source_sha,copy_document=None):
    rows=source['records']['rows'];count=source['records']['total']
    if type(count)is not int or count<0 or len(rows)!=count or source['analysis']['total']!=count:raise ValueError('unified-violation-count-not-reconciled')
    if not count:return '违规方面：\n违规0条，违规分析与违规记录列表均已核对。'
    if copy_document is None or copy_document.get('source_sha256')!=source_sha:raise ValueError('unified-violation-reviewed-copy-source')
    items=copy_document['items'];byid={x['notice_id']:x for x in items}
    if len(byid)!=len(items)or set(byid)!={r['notice_id']for r in rows}:raise ValueError('unified-violation-reviewed-copy-ids')
    # Load the violation producer explicitly: the caller also loads a complaint
    # module named workflow, so a bare workflow import can classify wrongly.
    import importlib.util
    path=Path(__file__).resolve().parents[3]/'skills/violation-notifier/scripts/workflow.py'
    spec=importlib.util.spec_from_file_location('_unified_violation_workflow',path)
    workflow=importlib.util.module_from_spec(spec);spec.loader.exec_module(workflow)
    reminders=[workflow.platform_reminder(row)for row in rows]
    for row,reminder in zip(rows,reminders):
        if row.get('notice_kind')=='platform-anchor-reminder'or row.get('not_business_violation')is True or row.get('reason')=='温馨提醒：锚点类型选择有误':
            if not reminder:raise ValueError('unified-platform-reminder-classification-required')
    total_reminders=sum(reminders)
    title=(f'本期核实平台通知{count}条，其中违规{count-total_reminders}条、非违规提醒{total_reminders}条。'if total_reminders else f'本期核实违规{count}条。')
    lines=['违规方面：',title]
    for index,row in enumerate(rows,1):
        copy=byid[row['notice_id']];reason=copy['gentle_reason'];advice=copy['recommendation'];actions='；'.join(row['actions'])
        if not all(type(x)is str and x.strip()for x in(row['subject'],reason,advice,actions,row['effectiveness_status'])):raise ValueError('unified-violation-public-fields-missing')
        if reminders[index-1]:
            if reason!=row['reason']+'。'or not row.get('disposal_stage_text'):raise ValueError('unified-platform-reminder-public-facts')
            lines.append(f"{index}. 门店/主体：{row['subject']}；平台温馨提醒：{reason}；平台调整：{actions}；调整说明：{row['disposal_stage_text']}；平台说明：{row['platform_non_violation_statement']}；建议：{advice}")
        else:
            stage=row.get('disposal_stage_text')
            if stage is not None and (type(stage)is not str or not stage.strip()):raise ValueError('unified-violation-disposal-stage-invalid')
            disposal=(f"{actions}；处置状态：{stage}"if stage else f"{actions}（{row['effectiveness_status']}）")
            lines.append(f"{index}. 门店/主体：{row['subject']}；原因：{reason}；处置：{disposal}；建议：{advice}")
    return '\n'.join(lines)

def complaint_summary(company,start,end_exclusive,new_count,ledger,keys):
    """Draft/result facts only. Never calls a submission or labels drafts submitted."""
    if type(new_count)is not int or new_count<0 or len(keys)!=len(set(keys)):raise ValueError('unified-complaint-count-or-keys')
    tasks=[ledger['tasks'][key]for key in keys]
    if not tasks:return None # Original explicit zero notice is retained separately.
    allowed={'draft_ready','existing_pending','resolved'}
    if any(t['status']not in allowed or (t['status']!='draft_ready' and (t.get('result')or{}).get('status')not in('pending','accepted','rejected'))for t in tasks):raise ValueError('unified-complaint-processing-not-ready')
    draft=sum(t['status']=='draft_ready'for t in tasks);reviewed=sum(t.get('result')is not None for t in tasks);pending=sum((t.get('result')or{}).get('status')=='pending'for t in tasks);historical=sum(not(start<=t['review']['date']<end_exclusive)for t in tasks)
    last=(date.fromisoformat(end_exclusive)-__import__('datetime').timedelta(days=1)).isoformat()
    return f'【差评投诉流程】\n公司：{company}\n日期：{start}～{last}\n本期新增核验中差评{new_count}条；本次处理/复查{len(tasks)}条，其中历史复查{historical}条。\n投诉草稿{draft}条，已复查{reviewed}条，其中平台处理中{pending}条。'
