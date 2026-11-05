#!/usr/bin/env python3
"""Pure offline enrichment of normal filtered DOM rows from THIS acquisition.

No browser, submission or sending. Run with daily-comment-stats/.venv/bin/python.
The caller pins a current operator work_order_id and the receipt file SHA256;
historical statistics receipts, filenames and relative UI dates are insufficient.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse
import export_parse_session
from collections import defaultdict
from datetime import date,datetime,timedelta
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse,parse_qs
from zoneinfo import ZoneInfo

TZ=ZoneInfo('Asia/Shanghai')
REQUIRED=('门店名称','用户昵称','评价时间','推荐等级','文本内容','图片内容','视频内容')
PLATFORM_IDS=('评价ID','评价id','评论ID','评价编号')

class JoinError(ValueError):pass
def need(value,reason):
    if not value:raise JoinError(reason)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def data_hash(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def normalized(value):
    text=unicodedata.normalize('NFC','' if value is None else str(value)).replace('\r\n','\n').replace('\r','\n').strip()
    need('\x00' not in text,'null-character-in-source')
    return text
def stamp(value):
    need(isinstance(value,str) and bool(re.search(r'[T ]\d{2}:\d{2}:\d{2}',value)),'absolute-timestamp-required')
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    need(parsed.utcoffset() is not None,'timestamp-timezone-required')
    return parsed.astimezone(TZ)
def identity(value):
    return isinstance(value,dict) and set(value)=={'provider','account_id','manager'} and all(isinstance(v,str) and v.strip() for v in value.values())
def source_time(value,epoch):
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        from openpyxl.utils.datetime import from_excel
        value=from_excel(value,epoch)
    if isinstance(value,str):
        value=normalized(value).replace('/','-')
        need(bool(re.search(r'[T ]\d{2}:\d{2}:\d{2}',value)),'export-absolute-time-missing')
        try:value=datetime.fromisoformat(value.replace('Z','+00:00'))
        except ValueError as e:raise JoinError('export-time-invalid') from e
    need(isinstance(value,datetime),'export-absolute-time-missing')
    if value.tzinfo is None:value=value.replace(tzinfo=TZ)
    return value.astimezone(TZ).isoformat(timespec='microseconds' if value.microsecond else 'seconds')
def stars(value):
    m=re.fullmatch(r'([1-5])(?:\.0+)?\s*(?:星|心)?',normalized(value))
    need(m is not None,'export-rating-invalid');return int(m[1])
def platform_id(value):
    if value is None or value=='':return ''
    if isinstance(value,(int,float)):
        need(not isinstance(value,bool) and float(value).is_integer() and abs(value)<10**15,'numeric-platform-id-precision-unsafe')
        return str(int(value))
    return normalized(value)

def validate_scope(job,observation,receipt_path,receipt_sha256):
    need(re.fullmatch(r'[0-9a-f]{64}',receipt_sha256 or '') is not None,'receipt-sha256-required')
    need(digest(receipt_path)==receipt_sha256,'receipt-hash-mismatch')
    r=json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    company,gid=job.get('company'),str(job.get('groupid',''))
    need(company and gid.isdigit(),'job-company-required')
    first,end=job['start'],job['end_exclusive']
    need(date.fromisoformat(first)<date.fromisoformat(end),'job-range-invalid')
    inclusive=(date.fromisoformat(end)-timedelta(days=1)).isoformat()
    expected_id=job.get('source_work_order_id')
    need(isinstance(expected_id,str) and expected_id.strip(),'current-source-work-order-id-required')
    need(r.get('work_order_id')==expected_id,'source-work-order-is-not-current')
    need(r.get('company')==company and str(r.get('groupid'))==gid,'receipt-company-mismatch')
    need(r.get('date_range')=={'start':first,'end':inclusive},'receipt-date-range-mismatch')
    need(r.get('operator_skill')=='douyin-laike-operator' and r.get('download_verified') is True and r.get('source_is_authoritative_export') is True,'not-authoritative-current-export')
    need(job.get('account_verified') is True and identity(job.get('identity')),'job-account-unverified')
    need(r.get('account_verified') is True and r.get('identity')==job['identity']==r.get('identity_before'),'receipt-account-mismatch')
    need(r.get('backend') in ('codex-existing-extension','local-dom-bridge'),'receipt-backend-unrecognized')
    if r['backend']=='local-dom-bridge':
        proof=r.get('transport_proof',{})
        need(proof.get('safety')=='DOM-only' and proof.get('reviewed_extension_ready') is True and isinstance(proof.get('safety_version'),str),'bridge-transport-unverified')
    u=urlparse(r.get('record_url',''))
    need(u.scheme=='https' and u.netloc=='life.douyin.com' and '/export_records/' in u.path and parse_qs(u.query).get('groupid')==[gid],'receipt-record-context-mismatch')
    source=Path(r.get('source',''))
    need(source.is_absolute() and source.is_file() and source.suffix.lower()=='.xlsx' and not source.is_symlink(),'authoritative-source-path-invalid')
    need(digest(source)==r.get('src_sha256'),'authoritative-source-hash-mismatch')
    need(r.get('bytes')==source.stat().st_size,'source-size-mismatch')
    need(type(r.get('page_filtered')) is int and r['page_filtered']>=0,'export-total-unverified')
    recorded=stamp(r.get('recorded_at'));observed=stamp(observation.get('observed_at'))
    need(recorded<=observed,'observation-precedes-authoritative-download')
    need(observation.get('company')==company and str(observation.get('groupid'))==gid,'observation-company-mismatch')
    need(observation.get('start')==first and observation.get('end_exclusive')==end,'observation-date-range-mismatch')
    need(observation.get('account_verified') is True and observation.get('identity')==job['identity'],'observation-account-mismatch')
    need(observation.get('source')==r['backend'],'observation-backend-mismatch')
    view=urlparse(observation.get('url',''))
    need(view.scheme=='https' and view.netloc=='life.douyin.com' and parse_qs(view.query).get('groupid')==[gid],'observation-url-mismatch')
    need(observation.get('negative_filter')=='中差评（1-3心）' and observation.get('filter_active') is True,'negative-filter-unverified')
    need(observation.get('other_filters')=={'评价类型':'全部','评价来源':'全部','评价状态':'全部'},'other-filter-unverified')
    need(observation.get('fold_boundary_verified') is True and observation.get('all_pages_read') is True,'normal-scope-or-pagination-unverified')
    need(digest(receipt_path)==receipt_sha256,'receipt-changed-during-validation')
    return r,source

def _load_export_uncached(source,job,receipt):
    try:import openpyxl
    except ImportError as e:raise JoinError('openpyxl-required-use-daily-comment-stats-venv') from e
    wb=openpyxl.load_workbook(source,read_only=True,data_only=False)
    try:
        # Platform exports can declare dimension=A1 while containing the full
        # table. Ignore declared bounds and stream the actual worksheet XML.
        sheet=wb.worksheets[0];sheet.reset_dimensions();iterator=sheet.iter_rows()
        headers=[normalized(c.value) for c in next(iterator,())]
        need(len([v for v in headers if v])==len(set(v for v in headers if v)),'duplicate-export-header')
        need(set(REQUIRED)<=set(headers),'export-required-columns-missing')
        index={h:i for i,h in enumerate(headers)};rows=[];ids=set();tuples=set()
        for source_row,cells in enumerate(iterator,start=2):
            values=[c.value for c in cells]
            if all(v is None or v=='' for v in values):continue
            need(not any(c.data_type=='f' for c in cells),'export-formula-not-literal')
            need(not any(v not in (None,'') for v in values[len(headers):]),'export-row-outside-header')
            get=lambda h:values[index[h]] if h in index and index[h]<len(values) else None
            absolute=source_time(get('评价时间'),wb.epoch);day=absolute[:10]
            need(job['start']<=day<job['end_exclusive'],'export-row-outside-range')
            store,customer,text=map(normalized,(get('门店名称'),get('用户昵称'),get('文本内容')))
            need(store and customer,'export-match-fields-missing')
            rating=stars(get('推荐等级'));product=normalized(get('消费商品'))
            platform_values={platform_id(get(h)) for h in PLATFORM_IDS if h in index and get(h) not in (None,'')}
            need(len(platform_values)<=1,'conflicting-platform-id-columns')
            pid=next(iter(platform_values),'')
            canonical={'company':job['company'],'groupid':str(job['groupid']),'store':store,'customer':customer,'text':text,
                       'time':absolute,'stars':rating,'product':product,'source':normalized(get('评价来源'))}
            tuple_sha=data_hash(canonical)
            need(tuple_sha not in tuples,'duplicate-export-canonical-review');tuples.add(tuple_sha)
            review_id=pid or 'verified-tuple-sha256:'+tuple_sha
            need(review_id not in ids,'duplicate-export-review-id');ids.add(review_id)
            rows.append({'review_id':review_id,'id_source':'platform-export' if pid else 'verified-export-tuple',
                         'canonical_sha256':tuple_sha,'source_row':source_row,'store':store,'customer':customer,'text':text,
                         'date':day,'time':absolute,'stars':rating,'product':product,'match':(store,customer,text)})
        # The export may include folded/all-rating rows that the normal UI scope
        # excludes. Do not equate receipt page count with the raw XLSX row count.
        return rows,headers
    finally:wb.close()

def load_export(source,job,receipt):
    return export_parse_session.load(source,job,receipt,_load_export_uncached)

def join(job,observation,receipt_path,receipt_sha256):
    """Return an enriched capture; no status/ledger writes. Folded rows never join."""
    r,source=validate_scope(job,observation,receipt_path,receipt_sha256)
    exported,headers=load_export(source,job,r)
    if observation.get('normal_scope_mode')=='verified-empty-normal-list':
        need(observation.get('filtered_count')==0 and not observation.get('rows') and not any(x['stars']<=3 for x in exported),'empty-normal-export-negative-conflict')
    index=defaultdict(list)
    for row in exported:index[row['match']].append(row)
    visible=observation.get('rows');need(isinstance(visible,list),'observation-rows-invalid')
    need(all(v.get('section') in ('filtered','folded') for v in visible),'row-section-unknown')
    normal=[v for v in visible if v['section']=='filtered']
    need(type(observation.get('filtered_count')) is int and len(normal)==observation['filtered_count'],'filtered-count-mismatch')
    selected=[];seen=set()
    for row in normal:
        need(row.get('text_complete') is True,'normal-row-full-text-unverified')
        need(all(isinstance(row.get(k),str) for k in ('store','customer','text')),'normal-match-fields-missing')
        key=tuple(normalized(row[k]) for k in ('store','customer','text'))
        matches=index.get(key,[]);need(len(matches)==1,'normal-row-export-match-not-unique:'+str(len(matches)))
        matched=matches[0];need(1<=matched['stars']<=3,'normal-row-matches-positive-export')
        need(matched['review_id'] not in seen,'duplicate-normal-review');seen.add(matched['review_id'])
        for field in ('review_id','date','time','stars'):
            if row.get(field) not in (None,''):
                need(row[field]==matched[field],'visible-authoritative-field-conflict:'+field)
        need(row.get('action') in ('投诉','查看投诉结果','投诉审核中'),'complaint-action-unrecognized')
        if row.get('body_kind'):
            import normal_review_body as rb
            evidence=rb.provenance(row);need(evidence['source_row']==matched['source_row'] and evidence['source_sha256']==r['src_sha256'] and matched['text']=='-','normal-image-body-authority-conflict')
        selected.append({**row,**{k:matched[k] for k in ('review_id','store','customer','text','date','time','stars','product')},
            'authority':{'id_source':matched['id_source'],'canonical_sha256':matched['canonical_sha256'],
                         'source_row':matched['source_row'],'receipt_sha256':receipt_sha256,'source_sha256':r['src_sha256'],
                         'work_order_id':r['work_order_id']}})
    need(digest(source)==r['src_sha256'] and digest(receipt_path)==receipt_sha256,'source-or-receipt-changed-during-join')
    return {**observation,'rows':selected,'excluded_folded_count':len(visible)-len(normal),
        'authority_binding':{'receipt_path':str(Path(receipt_path).resolve()),'receipt_sha256':receipt_sha256,
          'source_path':str(source),'source_sha256':r['src_sha256'],'work_order_id':r['work_order_id'],
          'observation_sha256':data_hash(observation),'company':job['company'],'groupid':str(job['groupid']),
          'start':job['start'],'end_exclusive':job['end_exclusive'],'identity':job['identity'],
          'export_rows':len(exported),'headers':headers,'matching':'NFC+CRLF normalization; outer trim only; exact store/customer/full text; globally unique'}}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('job','observation','receipt','receipt-sha256','out'):p.add_argument('--'+name,required=True)
    args=p.parse_args();load=lambda path:json.loads(Path(path).read_text(encoding='utf-8'))
    result=join(load(args.job),load(args.observation),args.receipt,args.receipt_sha256)
    out=Path(args.out);need(not out.exists(),'output-exists-refuse-overwrite');out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'ok':True,'output':str(out.resolve()),'rows':len(result['rows'])},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (JoinError,KeyError,OSError,ValueError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
