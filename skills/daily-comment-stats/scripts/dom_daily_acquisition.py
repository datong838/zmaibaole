"""Offline typed visible-DOM acquisition. Never downloads, opens UI, or certifies export."""
import copy,hashlib,json,math,re,sys,os,tempfile
from pathlib import Path
from datetime import date,datetime,timezone,timedelta
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
from dom_evidence import nodes,identity,context,all_store_scope,verified_review_filter
from readonly_tick_snapshot import decode
CONTRACT='daily-visible-dom-single-day-v1'
POLICY={'id':'dom-visible-ratings-separated-v1','rating_population':'normal+folded','business_metric':'visible_dom_rating_records','official_export_equivalent':False}
LIST='commentList-hkujq4 isPC-WBFQKh commentList-C8RoYO'
FOLD='折叠评价是根据规则计算对用户帮助不大的评价，不计入全部评价数量，消费后无图文的纯星级评价仍加入评分计算，若有其他疑问咨询下方客服，或查看规则'
def need(ok,code):
 if not ok:raise ValueError(code)
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).absolute()),'sha256':h(p)}
def canonical(p):
 p=Path(p);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),'source-path-not-canonical');return p
def pinned(r):
 need(type(r)is dict and set(r)=={'path','sha256'},'reference-shape');p=canonical(r['path']);need(h(p)==r['sha256'],'source-hash-changed');return json.loads(p.read_bytes())
def cl(n):return n.get('attributes',{}).get('class','')
def one(ns,cls):
 a=[n for n in ns if cl(n)==cls];need(len(a)==1,'field-not-unique:'+cls);return a[0]
def literal(n):
 need(type(n.get('name'))is str and len(n['name'])<12000,'field-text-unverified');return n['name']
def pager(n):
 need(cl(n)=='pagination-GXvAPk' and len(n.get('children',[]))==2,'pager-shape');total,buttons=n['children'];need(cl(total)=='text-bjyZFG' and cl(buttons)=='buttonGroup-GDbp9Y' and len(buttons.get('children',[]))==3,'pager-children');prev,cur,nxt=buttons['children'];m=re.fullmatch(r'共([1-9]\d*)条记录',literal(total));q=re.fullmatch(r'([1-9]\d*)/([1-9]\d*)',literal(cur));need(m and q,'pager-text');count=int(m[1]);page,pages=map(int,q.groups());need(1<=page<=pages==math.ceil(count/10),'pager-range')
 for n,disabled in [(prev,page==1),(nxt,page==pages)]:need(cl(n)=='button-j4VxiA'+(' isDisabled-unTBS6' if disabled else ''),'pager-button')
 return page,pages,count
# Class spellings above are checked against the actual source below, not fuzzy matched.
RATING_MAP={'非常差':1,'较差':2,'一般':3,'超赞':5}
RATING_EVIDENCE={'path':str(Path(__file__).absolute().with_name('rating-label-map.json')),'sha256':'62be5c77b3ba3b0e63794118457e76745eb6d5993a26f62be8fb43d0f5f88116'}
def _rating_calibration():
 evidence=pinned(RATING_EVIDENCE);need(set(evidence)=={'kind','version','observed_exact_label_to_rating','audit_original_evidence_sha256'} and evidence['kind']=='reviewed-public-rating-label-map-v1' and evidence['version']==1 and evidence['audit_original_evidence_sha256']=='a7bb9351c5f2e720b9e05f57c15ad077e1a31d172bcbd004d3d29021c78aadb5' and evidence['observed_exact_label_to_rating']==RATING_MAP,'rating-map-evidence-conflict');return dict(RATING_MAP)
def parse_rating(card):
 return _parse_rating(card,_rating_calibration())
def _parse_rating(card,rating_map):
 ns=list(nodes({'truncated':False,'root':card}));attitude=one(ns,'attitude-ts0lI3 isPC-EhBcPu');children=attitude.get('children',[])
 need(len(children)==2 and cl(children[0])=='score-R2K3dS' and cl(children[1])=='text-J4lpcH','rating-sibling-shape')
 score,label=children;need(label.get('tag')=='div' and not label.get('children') and label.get('selector') and literal(label) in rating_map,'rating-label-unknown')
 need(len([n for n in ns if cl(n)=='text-J4lpcH'])==1 and len([n for n in ns if cl(n)=='score-R2K3dS'])==1,'rating-label-not-unique')
 hearts=score.get('children',[]);need(len(hearts)==5 and all(x.get('tag')=='img' and cl(x)=='heart-u6Bc6T' and not x.get('children') for x in hearts),'rating-shape')
 rating=rating_map[literal(label)]
 for n in (attitude,score,label):
  for key in ('data-rating','aria-label'):
   if key in n.get('attributes',{}):
    value=n['attributes'][key];need(value==literal(label) or re.fullmatch(r'[1-5](?:星|心)?',value) and int(value[0])==rating,'rating-attribute-conflict')
 return rating,{'basis':'public-rating-label-v1','literal':literal(label),'label_selector':label['selector'],'attitude_selector':attitude['selector'],'score_selector':score['selector'],'score_img_count_not_rating':len(hearts),'mapping_evidence':RATING_EVIDENCE}
def parse_card(card,section,day,source_ref,page_index):
 return _parse_card(card,section,day,source_ref,page_index,_rating_calibration())
def _parse_card(card,section,day,source_ref,page_index,rating_map):
 need(cl(card)=='commentItem-jrXo5p','card-shape');ns=list(nodes({'truncated':False,'root':card}));store=literal(one(ns,'poiName-W9HDFV'));nick=literal(one(ns,'nickName-wB7fZf'));need(store and nick,'card-identity-empty');score=one(ns,'score-R2K3dS')
 column=one(ns,'secondColumn-NC8I04');parts=column.get('children',[]);texts=[x for x in parts if cl(x)=='text-Hl9jZe'];galleries=[x for x in parts if cl(x)=='imageAndVideoList-qrj95L'];empty=[x for x in parts if cl(x)=='contentPlaceholder-UrfFiC'];need(len(texts)<=1 and len(galleries)<=1 and len(empty)<=1 and len(parts)==len(texts)+len(galleries)+len(empty),'body-shape-unreviewed');need(not empty or (len(parts)==1 and literal(empty[0])=='无内容'),'empty-body-conflict');need(parts,'body-unverified');text=literal(texts[0]) if texts else None
 if texts:need(text and not any(n.get('name') in ('展开','展开全文','收起') for n in nodes({'truncated':False,'root':texts[0]})),'body-collapsed-or-empty')
 has_image=False
 if galleries:
  gallery=galleries[0];need(len(gallery.get('children',[]))==1,'gallery-shape');thumbs=gallery['children'][0];need(cl(thumbs)=='thumbList-IiD0ah' and thumbs.get('children'),'gallery-list')
  for thumb in thumbs['children']:
   need(cl(thumb)=='thumb-mbxSp4' and len(thumb.get('children',[]))==1,'media-kind-unreviewed');img=thumb['children'][0];need(img.get('tag')=='img' and cl(img)=='image-mnMPZ2' and not img.get('children'),'media-kind-unreviewed')
  has_image=True
 rating,rating_evidence=_parse_rating(card,rating_map);selector=card.get('selector');need(type(selector)is str and selector,'card-selector-required');times=[n for n in ns if 'publishTime-DglqtK' in cl(n).split()];need(len(times)==1,'relative-time-shape')
 return {'local_evidence_key':hashlib.sha256((source_ref['sha256']+'|'+selector).encode()).hexdigest(),'platform_review_id':None,'section':section,'page':page_index,'store':store,'nickname':nick,'review_day':day,'review_day_basis':'verified-single-day-query','absolute_review_time':None,'visible_relative_time':literal(times[0]),'rating':rating,'rating_basis':'public-rating-label-v1','rating_label_evidence':rating_evidence,'text':text,'has_text':bool(text),'has_image':has_image,'has_video':False,'image_urls':None,'video_urls':None,'origin':'visible-dom','provenance':{'scope':source_ref,'card_selector':selector,'store_selector':one(ns,'poiName-W9HDFV')['selector'],'nickname_selector':one(ns,'nickName-wB7fZf')['selector'],'rating_selector':score['selector'],'content_selector':column['selector']}}
def derive(job,page_refs,policy):
 rating_map=_rating_calibration()
 need(type(policy)is dict and policy==POLICY and policy.get('official_export_equivalent') is False,'typed-policy-unreviewed');need(set(job)=={'company','groupid','identity','date_range','tab_id','window_id','pid','original_order','original_task','original_outer','original_job','original_request'},'job-shape');need(job['company'] and type(job['pid'])is int and job['pid']>0,'job-binding');order=pinned(job['original_order']);origin=pinned(job['original_job']);request=pinned(job['original_request']);need(request['task']['id']==job['original_task'] and request['task']['outer']==job['original_outer'] and request['context']['order']==job['original_order'] and request['context']['scope']=={'pid':job['pid'],'tab_id':job['tab_id']},'original-request-binding');need(origin['company']==job['company'] and str(origin['groupid'])==str(job['groupid']) and origin['identity_baseline']==job['identity'] and {k:origin['date_range'][k]for k in ('start','end')}==job['date_range'],'original-job-binding');dates=job['date_range'];need(set(dates)=={'start','end'} and dates['start']==dates['end'],'single-day-query-required');day=date.fromisoformat(dates['start']);need(any(x=={'company':job['company'],'groupid':str(job['groupid']),'start':day.isoformat(),'end_exclusive':(day+timedelta(days=1)).isoformat()} for x in order['scope']['company_ranges']),'original-order-range');need(page_refs and len(page_refs)<=100,'pages-required');all_rows=[];headers=[];totals=[];fullurl=None;fold_started=False;seen=set();tuple_seen=set()
 for index,r in enumerate(page_refs,1):
  v=decode(pinned(r),job['tab_id'],job['window_id']);a=context(v['before'],job['tab_id'],job['groupid']);z=context(v['after'],job['tab_id'],job['groupid']);need(a['url']==z['url'] and a['windowId']==z['windowId']==job['window_id'],'scope-changed');need(fullurl is None or a['url']==fullurl,'pages-route-changed');fullurl=a['url'];need(urlsplit(fullurl).path=='/p/life_comment/management' and not urlsplit(fullurl).fragment,'scope-route-not-review');tree=v['tree'];need(tree.get('url')=='https://life.douyin.com/p/life_comment/management','route-not-review');need(v['ping'].get('safety')=='DOM-only' and v['ping'].get('version')==VERSION,'bridge-version');identity(tree,job['identity']);all_store_scope(tree);filtered=verified_review_filter(tree,dates)['page_filtered'];ns=list(nodes(tree))
  for label in ('好评（4-5心）','中差评（1-3心）','未回复','已回复','抖音消费','非抖音消费'):
   found=[n for n in ns if n.get('name')==label and not n.get('children')];need(len(found)==1 and cl(found[0])=='option-YmRyn3','nondefault-shortcut')
  root=one(ns,LIST);children=root.get('children',[]);need(len(children)>=3 and cl(children[0])=='header-sQid1u commentListHeader-jKdTh_','list-shape');page,pages,total=pager(children[-1]);need(page==index,'page-sequence');headers.append(filtered);totals.append((pages,total));local=[]
  for n in children[1:-1]:
   if 'foldTitleContainer-DwIByI' in cl(n).split():need(not fold_started and literal(n)==FOLD,'fold-boundary-unreviewed');fold_started=True;continue
   row=_parse_card(n,'folded' if fold_started else 'normal',dates['start'],r,index,rating_map);need(row['local_evidence_key'] not in seen,'duplicate-evidence-row');seen.add(row['local_evidence_key']);signature=json.dumps([row[k]for k in ('store','nickname','visible_relative_time','rating','text','has_image','has_video')],ensure_ascii=False);need(signature not in tuple_seen,'ambiguous-repeated-visible-card');tuple_seen.add(signature);local.append(row)
  need(len(local)==min(10,total-(index-1)*10),'page-card-count-incomplete');all_rows+=local
 need(len(set(headers))==len(set(totals))==1,'total-count-changed');pages,total=totals[0];need(len(page_refs)==pages and len(all_rows)==total,'all-pages-incomplete');normal=sum(x['section']=='normal' for x in all_rows);folded=len(all_rows)-normal;need(normal==headers[0],'normal-filter-count-conflict');need(sum(x['rating']>=4 for x in all_rows)+sum(x['rating']<=3 for x in all_rows)==total,'rating-count-conflict')
 return {'kind':CONTRACT,'origin':'visible-dom','download_verified':False,'source_is_authoritative_export':False,'original_daily_export_metric_certified':False,'policy':policy,'job':job,'pages':page_refs,'source_url':fullurl,'summary':{'normal':normal,'folded':folded,'visible_rating_records':total,'platform_filtered_normal_count':headers[0],'platform_pager_total':total,'visible_good':sum(x['rating']>=4 for x in all_rows),'visible_negative':sum(x['rating']<=3 for x in all_rows)},'rows':all_rows,'missing_fields':['absolute_review_time','platform_review_id','image_urls','video_urls','export-only-columns'],'snapshot_freshness':'saved-observations-only; not a fresh browser capture','no_platform_score_claim':True}
def workbook_matrices(data):
 summary=[['可见DOM采集 / 非平台导出','值'],['公司',data['job']['company']],['查询日期',data['job']['date_range']['start']]]
 for key in ('normal','folded','visible_rating_records','platform_filtered_normal_count','platform_pager_total','visible_good','visible_negative'):summary.append([key,data['summary'][key]])
 summary += [['统计口径',POLICY['business_metric']+'（normal与folded均保留，不等于旧export指标）'],['缺失字段','绝对时刻、平台评价ID、媒体URL、导出专属字段均null'],['新鲜度','仅保存的DOM观察；生成时间不是观察时间']]
 keys=['section','store','nickname','review_day','review_day_basis','absolute_review_time','visible_relative_time','rating','has_text','text','has_image','has_video','image_urls','video_urls','platform_review_id']
 detail=[keys+['rating_basis','rating_label','rating_label_selector']]+[[row[k] for k in keys]+[row['rating_basis'],row['rating_label_evidence']['literal'],row['rating_label_evidence']['label_selector']]for row in data['rows']]
 evidence=[['来源类型','路径或说明','SHA256']]+[['readonly-scope',r['path'],r['sha256']]for r in data['pages']]+[['rating-label-mapping',RATING_EVIDENCE['path'],RATING_EVIDENCE['sha256']],['producer',str(Path(__file__).resolve()),h(__file__)],['日期依据','唯一筛选日期，不是原绝对评价时刻',None],['归类依据','严格评分文字/正文/缩略图；折叠单列',None]]
 return {'DOM口径摘要':summary,'DOM来源明细':detail,'来源引用':evidence}
def write_workbook(data,path):
 from openpyxl import Workbook
 from openpyxl.styles import Font,PatternFill,Alignment
 wb=Workbook();wb.remove(wb.active)
 for name,rows in workbook_matrices(data).items():
  sheet=wb.create_sheet(name)
  for row in rows:sheet.append(row)
  sheet.freeze_panes='A2';sheet.auto_filter.ref=sheet.dimensions
  for row in sheet:
   for cell in row:
    if isinstance(cell.value,str):cell.data_type='s'
    cell.alignment=Alignment(vertical='top',wrap_text=True)
  for cell in sheet[1]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='284B63')
  for col in sheet.columns:sheet.column_dimensions[col[0].column_letter].width=36 if name!='来源引用' else 54
  for row in range(1,sheet.max_row+1):sheet.row_dimensions[row].height=44
 wb.save(path);wb.close()
def create(job,page_refs,policy,outdir):
 data=derive(job,page_refs,policy);out=Path(outdir);need(out.is_absolute() and out.parent.resolve()==out.parent and not out.is_symlink(),'output-canonical-parent-required');need(not out.exists(),'output-already-exists-do-not-replay');out.mkdir(parents=True)
 xlsx=out/'DOM来源评价.xlsx';write_workbook(data,xlsx)
 manifest=out/'dom-acquisition.json';manifest.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
 receipt={'kind':'daily-visible-dom-workbook-receipt-v1','derived_at':datetime.now(timezone.utc).isoformat(),'observation_wall_time':None,'producer':ref(__file__),'reader_code_refs':[ref(ROOT/'skills/douyin-laike-operator/scripts/dom_evidence.py'),ref(ROOT/'skills/douyin-laike-operator/scripts/readonly_tick_snapshot.py')],'manifest':ref(manifest),'xlsx':ref(xlsx),'download_verified':False,'source_is_authoritative_export':False,'summary':data['summary']}
 rp=out/'receipt.json';rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');verify(ref(rp));return ref(rp)
def verify(receipt_ref):
 from openpyxl import load_workbook
 receipt=pinned(receipt_ref);need(set(receipt)=={'kind','derived_at','observation_wall_time','producer','reader_code_refs','manifest','xlsx','download_verified','source_is_authoritative_export','summary'},'receipt-shape');need(receipt['reader_code_refs']==[ref(ROOT/'skills/douyin-laike-operator/scripts/dom_evidence.py'),ref(ROOT/'skills/douyin-laike-operator/scripts/readonly_tick_snapshot.py')],'reader-code-changed');need(receipt['observation_wall_time'] is None,'invented-observation-time');need(receipt['kind']=='daily-visible-dom-workbook-receipt-v1' and receipt['producer']==ref(__file__) and receipt['download_verified'] is False and receipt['source_is_authoritative_export'] is False,'receipt-contract')
 data=pinned(receipt['manifest']);need(data==derive(data['job'],data['pages'],data['policy']) and receipt['summary']==data['summary'],'manifest-rederive-conflict')
 p=canonical(receipt['xlsx']['path']);need(h(p)==receipt['xlsx']['sha256'],'xlsx-hash-changed');wb=load_workbook(p,data_only=False)
 try:
  need(wb.sheetnames==list(workbook_matrices(data)),'xlsx-sheets')
  need({sh.title:[[c.value for c in row]for row in sh]for sh in wb}==workbook_matrices(data),'xlsx-all-cells-conflict')
  need(not any(c.data_type=='f'for sh in wb for row in sh for c in row),'xlsx-formula-forbidden')
 finally:wb.close()
 return data

def source_evidence(receipt_ref):
 data=verify(receipt_ref);return _source_evidence_from_verified(receipt_ref,data)
def _source_evidence_from_verified(receipt_ref,data):
 receipt=pinned(receipt_ref);job=data['job']
 return {'kind':'daily-visible-dom-source-v1','receipt':receipt_ref,'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'identity_before':job['identity'],'date_range':job['date_range'],'source':receipt['xlsx']['path'],'src_sha256':receipt['xlsx']['sha256'],'account_verified':True,'download_verified':False,'source_is_authoritative_export':False,'page_filtered':data['summary']['platform_filtered_normal_count'],'counts':data['summary'],'policy':POLICY,'snapshot_freshness':data['snapshot_freshness']}
def checked_source(payload,company,date_range,source):
 need(type(payload)is dict,'dom-source-wrapper-conflict');data=verify(payload['receipt']);need(payload==_source_evidence_from_verified(payload['receipt'],data),'dom-source-wrapper-conflict')
 need(payload['company']==company['company'] and str(payload['groupid'])==str(company['groupid']),'dom-source-company-mismatch')
 need(payload['date_range']=={k:date_range[k]for k in ('start','end')} and str(canonical(source))==payload['source'] and h(source)==payload['src_sha256'],'dom-source-range-or-file')
 return data
