#!/usr/bin/env python3
"""WeCom brief formatting from original XLSX rows. Never sends messages.

The screenshot supplies layout only. Counts/details come exclusively from XLSX;
Only review statistics, review details and merchant replies belong to this workflow.
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

def build(source,company,start,end,stats=None):
    source=Path(source);reviews,headers=load_reviews(source,start,end)
    if not reviews:raise ValueError('zero-rows-no-message')
    if stats:verify_stats(stats,company,len(reviews))
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

def render(d,brand,group,format_mode='test'):
    if format_mode not in ('test','online'):raise ValueError('report-format-invalid')
    short=lambda iso:date.fromisoformat(iso).strftime('%m.%d')
    counts=d['totals']
    lines=[f"【{brand}】{short(d['start'])}—{short(d['end'])}评价情况，请查收🌹"]
    if format_mode=='test':lines.extend(['（仅发测试群）',f'拟发群：{group}'])
    lines.extend([f"统计范围：{d['start']}至{d['end']}，共{len(d['stores'])}家有评价门店。",'',
           '评价方面：',f"本期新增{d['rows']}条评价，好评{d['good']}条，中差评{d['bad']}条。",f"好评占比：{d['good']/d['rows']:.2%}（4—5星）。"])
    for suffix,label in [('好评','好评分类'),('差评','中差评分类')]:
        parts=[f'{k[:-len(suffix)]}{counts.get(k,0)}条' for k in CATEGORIES if k.endswith(suffix)]
        lines.append(label+'：'+'；'.join(parts)+'。')
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
    pending=sum(r['reply']=='未回复' for r in d['bad_details'])
    lines.extend(['',f'待跟进：表内有{pending}条中差评尚未回复，请核实后处理。' if pending else '待跟进：请结合中差评详情核实处理情况。'])
    return '\n'.join(lines)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ['src','company','brand','start','end','out']:p.add_argument('--'+arg,required=True)
    p.add_argument('--stats');p.add_argument('--format',choices=['test','online'],default='test')
    a=p.parse_args();company=select_company(load_map(),a.company)
    data=build(a.src,company['company'],a.start,a.end,a.stats)
    text=render(data,a.brand,company['wecom_group'],a.format)
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
    out.with_suffix('.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(out.resolve()),'rows':data['rows'],'format':a.format,'test_only':True,'sending_authorized':False},ensure_ascii=False))
