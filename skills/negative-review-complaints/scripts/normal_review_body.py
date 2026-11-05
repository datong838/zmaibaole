"""Pure normal-card image-list/empty-text resolver. No navigation, fetch or drawer guess."""
from pathlib import Path
from datetime import date,timedelta
import json
import authoritative_join as A
SCHEMA='observed-image-list-empty-body-v2'
FIELDS=('body_kind','dom_text_present','dom_text','source_text_placeholder','source_row','source_sha256','image_count','video_present','body_schema')
need=A.need
def cl(n):return n.get('attributes',{}).get('class','')
def exact(n,tag,value):return n.get('tag')==tag and cl(n)==value
def flatten(n):
 yield n
 for child in n.get('children',[]):yield from flatten(child)
def image_region(card):
 need(exact(card,'div','commentItem-jrXo5p'),'image-body-normal-card-required')
 main=[x for x in card['children'] if exact(x,'div','main-OjCeVu')];need(len(main)==1,'image-body-main')
 cols=[x for x in main[0]['children'] if exact(x,'div','secondColumn-NC8I04')];need(len(cols)==1,'image-body-content-column');col=cols[0]
 need(col.get('name')=='' and len(col.get('children',[]))==1,'image-body-content-shape');media=col['children'][0]
 need(exact(media,'div','imageAndVideoList-qrj95L') and media.get('name')=='' and len(media.get('children',[]))==1,'image-body-media');thumbs=media['children'][0]
 need(exact(thumbs,'div','thumbList-IiD0ah') and thumbs.get('name')=='' and len(thumbs.get('children',[]))>0,'image-body-thumbnails-required')
 for thumb in thumbs['children']:
  need(exact(thumb,'div','thumb-mbxSp4') and thumb.get('name')=='' and len(thumb.get('children',[]))==1,'image-body-thumb')
  image=thumb['children'][0];need(exact(image,'img','image-mnMPZ2') and image.get('role')=='img' and image.get('name')=='' and not image.get('children'),'image-body-image')
 need(not any(cl(x)=='text-Hl9jZe' for x in flatten(card)),'image-body-text-node-present')
 return media,len(thumbs['children'])
def current_export(job):
 path=job['source_receipt'];need(A.digest(path)==job['source_receipt_sha256'],'image-body-receipt-changed');r=json.loads(Path(path).read_bytes());end=(date.fromisoformat(job['end_exclusive'])-timedelta(days=1)).isoformat()
 need(r.get('company')==job['company'] and str(r.get('groupid'))==str(job['groupid']) and r.get('identity')==r.get('identity_before')==job['identity'] and r.get('account_verified') is True and r.get('download_verified') is True and r.get('source_is_authoritative_export') is True and r.get('work_order_id')==job['source_work_order_id'] and r.get('date_range')=={'start':job['start'],'end':end},'image-body-current-receipt-scope')
 need(A.digest(r['source'])==r['src_sha256'],'image-body-source-changed');rows,_=A.load_export(r['source'],job,r);return r,rows

def resolve(card,store,customer,profile,exported,source,expected_sha):
 need(profile.get('image_only_text_schema')==SCHEMA,'image-body-explicit-schema-required');media,count=image_region(card)
 matches=[r for r in exported if r['match']==(store,customer,'-') and 1<=r['stars']<=3];need(len(matches)==1,'image-body-unique-export-row-required');row=matches[0]
 need(A.digest(source)==expected_sha,'image-body-pinned-source-changed')
 import openpyxl
 wb=openpyxl.load_workbook(source,read_only=True,data_only=False)
 try:
  sheet=wb.worksheets[0];sheet.reset_dimensions();it=sheet.iter_rows();headers=[A.normalized(c.value) for c in next(it)];cells=next((x for i,x in enumerate(it,2) if i==row['source_row']),None);need(cells is not None and all(c.data_type!='f' for c in cells),'image-body-source-row');raw={h:(cells[i].value if i<len(cells) else None) for i,h in enumerate(headers)}
  need(raw.get('文本内容')=='-' and A.normalized(raw.get('门店名称'))==store and A.normalized(raw.get('用户昵称'))==customer and A.normalized(raw.get('视频内容'))=='-','image-body-source-shape')
  images=A.normalized(raw.get('图片内容')).splitlines();need(len(images)==count and all(x.startswith('https://') and not any(c.isspace() for c in x) for x in images),'image-body-source-count-mismatch')
 finally:wb.close()
 need(A.digest(source)==expected_sha,'image-body-source-changed-during-read')
 return '-',{'body_kind':'image-only-no-text','dom_text_present':False,'dom_text':'','source_text_placeholder':'-','source_row':row['source_row'],'source_sha256':expected_sha,'image_count':count,'video_present':False,'body_schema':SCHEMA}
def for_card(job,card,store,customer,profile):
 receipt,rows=current_export(job);return resolve(card,store,customer,profile,rows,receipt['source'],receipt['src_sha256'])
def provenance(row):
 if row.get('body_kind')!='image-only-no-text':return None
 need(row.get('text')=='-' and row.get('dom_text_present') is False and row.get('dom_text')=='' and row.get('body_schema')==SCHEMA and type(row.get('image_count')) is int and row['image_count']>0 and row.get('video_present') is False,'image-body-provenance-invalid')
 return {k:row[k] for k in FIELDS}
