"""Build current range data from exact-day captures; no historical receipts."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/douyin-laike-operator/scripts'),str(Path(__file__).parent)]
from readonly_tick_snapshot import decode
from dom_evidence import nodes,verified_review_filter,identity,context as tab_context,all_store_scope
import dom_daily_acquisition as parser

def build(state,tab,window,company,start,end,source_ref,job):
 from datetime import date,timedelta
 first,last=date.fromisoformat(start),date.fromisoformat(end)
 days=[(first+timedelta(days=i)).isoformat()for i in range((last-first).days+1)]
 if set(days)!=set(state['captures']):raise ValueError('current-range-days-incomplete')
 rows=[];counts={}
 for day in days:
  capture=state['captures'][day];raw=capture['scope'];value=decode(raw['result'],tab,window);tree=value['tree']
  for side in ('before','after'):
   current=tab_context(value[side],tab,str(job['groupid']))
   if current['windowId']!=window:raise ValueError('current-capture-window-conflict')
  identity(tree,job['identity_baseline']);all_store_scope(tree)
  if value['ping'].get('safety')!='DOM-only':raise ValueError('current-capture-transport-conflict')
  filtered=verified_review_filter(tree,{'start':day,'end':day})['page_filtered']
  if filtered!=capture['filtered']:raise ValueError('current-range-count-conflict')
  scope=dict(source_ref)
  lists=[n for n in nodes(tree)if parser.cl(n)==parser.LIST];local=[];fold=False
  if len(lists)>1:raise ValueError('current-list-ambiguous')
  if lists:
   for child in lists[0]['children']:
    if parser.cl(child).startswith('foldTitleContainer-'):fold=True
    if parser.cl(child)!='commentItem-jrXo5p':continue
    card=copy.deepcopy(child)
    for n in nodes({'root':card,'truncated':False}):
     if parser.cl(n)=='secondColumn-NC8I04':
      normalized=[]
      for part in n.get('children',[]):
       if parser.cl(part)=='textClamp-XfZfzV content-vNnPMp isCollapsed-y94VHh':
        children=part.get('children',[])
        if len(children)!=1 or parser.cl(children[0])!='text-Hl9jZe':raise ValueError('current-text-wrapper-unknown')
        if any(x.get('name')in('展开','展开全文')for x in nodes({'root':part,'truncated':False})):raise ValueError('current-text-incomplete')
        normalized.append(children[0])
       else:normalized.append(part)
      n['children']=normalized
    local.append(parser._parse_card(card,'folded'if fold else'normal',day,scope,1,parser.RATING_MAP))
   pagers=[n for n in lists[0]['children']if parser.cl(n)=='pagination-GXvAPk']
   if local:
    if len(pagers)!=1:raise ValueError('current-page-coverage-unknown')
    page,pages,total=parser.pager(pagers[0])
    if page!=1 or pages!=1 or total!=len(local):raise ValueError('current-page-coverage-incomplete')
  if sum(r['section']=='normal'for r in local)!=filtered:raise ValueError('current-normal-count-conflict')
  rows.extend(local);counts[day]={'normal':filtered,'folded':len(local)-filtered}
 return {'kind':'current-dom-range-source-v1','company':company,'groupid':str(job['groupid']),'task':state['task'],'original_order':job.get('work_order_path'),'identity':job['identity_baseline'],'date_range':{'start':start,'end':end},'download_verified':False,'source_is_authoritative_export':False,'counts_by_day':counts,'rows':rows,'normal':sum(c['normal']for c in counts.values()),'folded':sum(c['folded']for c in counts.values()),'ready':False}
def write_outputs(data,directory):
 from ds_workbooks import dom_reviews,write_stats
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 summary={'normal':data['normal'],'folded':data['folded'],'visible_rating_records':len(data['rows']),'platform_filtered_normal_count':data['normal'],'platform_pager_total':len(data['rows']),'visible_good':sum(r['rating']>=4 for r in data['rows']),'visible_negative':sum(r['rating']<=3 for r in data['rows'])}
 enriched={**data,'summary':summary,'job':{'company':data['company'],'date_range':data['date_range']},'pages':[data['rows'][0]['provenance']['scope']]if data['rows']else[]}
 reviews=dom_reviews(enriched);artifacts=[]
 detail=directory/'页面评价明细.xlsx';parser.write_workbook(enriched,detail)
 artifacts.append(detail)
 for section,label in ((None,'全部可见评价统计'),('normal','正常评价统计'),('folded','折叠纯星评价统计')):
  selected=[r for r in reviews if section is None or r['section']==section]
  path=directory/(label+'.xlsx');write_stats(path,data['company'],selected);artifacts.append(path)
 return {'kind':'current-range-processing-result-v1','company':data['company'],'date_range':data['date_range'],'summary':summary,'download_verified':False,'source_is_authoritative_export':False,'delivery_complete':False,'artifacts':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in artifacts]}

def validate_reconciled_export(payload,company,dates,source):
 import re,openpyxl
 from ds_workbooks import empty,rating,review_day
 if payload.get('company')!=company['company'] or str(payload.get('groupid'))!=str(company['groupid']):raise ValueError('current-export-company-conflict')
 if payload.get('date_range')!={k:dates[k]for k in ('start','end')}:raise ValueError('current-export-range-conflict')
 reference=payload['current_result'];path=Path(reference['path'])
 if hashlib.sha256(path.read_bytes()).hexdigest()!=reference['sha256']:raise ValueError('current-result-changed')
 data=json.loads(path.read_bytes())
 if data['company']!=company['company'] or data['groupid']!=str(company['groupid']) or data['date_range']!=payload['date_range']:raise ValueError('current-result-scope-conflict')
 if hashlib.sha256(Path(source).read_bytes()).hexdigest()!=payload['src_sha256']:raise ValueError('current-export-source-changed')
 book=openpyxl.load_workbook(source,read_only=False,data_only=False)
 try:
  sheet=book.worksheets[0];headers=[c.value for c in sheet[1]];expected=[]
  if len(headers)!=20 or len(set(headers))!=20:raise ValueError('current-export-schema-conflict')
  for cells in sheet.iter_rows(min_row=2):
   if not any(c.value is not None for c in cells):continue
   if any(c.data_type=='f'for c in cells):raise ValueError('current-export-formula')
   row=dict(zip(headers,[c.value for c in cells]));expected.append((str(row['门店名称']).strip(),str(row['用户昵称']).strip(),re.sub(r'\s+',' ',str(row['文本内容']or'').strip()),rating(row['推荐等级']),not empty(row['图片内容']),not empty(row['视频内容']),review_day(row['评价时间'],book.epoch).isoformat()))
 finally:book.close()
 actual=[(r['store'],r['nickname'],re.sub(r'\s+',' ',(r['text']or'').strip()),r['rating'],r['has_image'],r['has_video'],r['review_day'])for r in data['rows']if r['section']=='normal']
 from collections import Counter
 if len(set(actual))!=len(actual) or Counter(actual)!=Counter(expected) or len(actual)!=data['normal']:raise ValueError('current-export-row-conflict')
 return True

if __name__=='__main__':
 path=ROOT/'runtime/standalone-workshop-director/current-day-capture.json';state=json.loads(path.read_bytes())
 import sqlite3
 with sqlite3.connect('file:'+str(path.parent/'queue.sqlite3')+'?mode=ro',uri=True)as db:
  context=json.loads(db.execute('select context from tasks where id=?',(state['task'],)).fetchone()[0])
 job=json.loads(Path(context['operator']['work_order']['path']).read_bytes());journal=json.loads(Path(job['workflow_path']).read_bytes());tab=journal['tab_id']
 first=next(iter(state['captures'].values()))['scope']['result']
 windows=[w for w in first['before']if any(t.get('tabId')==tab for t in w.get('tabs',[]))]
 if len(windows)!=1:raise ValueError('current-source-window-ambiguous')
 data=build(state,tab,windows[0]['windowId'],job['company'],job['date_range']['start'],job['date_range']['end'],{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()},job)
 output=path.with_name('current-range-source.json');output.write_text(json.dumps(data,ensure_ascii=False,indent=2))
 processed=write_outputs(data,path.parent/'current-daily-results')
 output.with_name('current-range-processing.json').write_text(json.dumps(processed,ensure_ascii=False,indent=2))
 print(json.dumps({'normal':data['normal'],'folded':data['folded'],'counts_by_day':data['counts_by_day']},ensure_ascii=False))
