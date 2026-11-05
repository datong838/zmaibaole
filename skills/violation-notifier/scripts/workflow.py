#!/usr/bin/env python3
"""Independent violation reporting. Read/export only, development sends to test group.
No browser debug connection, hidden API, appeal, rectification or settings mutation.
"""
import argparse
import csv
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import date,datetime,timedelta
from urllib.parse import urlparse,parse_qs
from zoneinfo import ZoneInfo
from contextlib import contextmanager

SKILL=Path(__file__).resolve().parents[1]
PROJECT=SKILL.parents[1]
sys.path.insert(0,str(PROJECT/'skills/daily-comment-stats/scripts'))
from ds_calendar import compute,shanghai_today
NODE=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
import delivery_targets
TEST_GROUP=delivery_targets.target('violation-notifier')
SENT_LABEL='客户端已显示，不代表已读'


def require(ok,message):
    if not ok:raise ValueError(message)
def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def fingerprint(data):return hashlib.sha256(json.dumps(data,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.pending-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
@contextmanager
def lock(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/'.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX);yield root

def evidence(root,path,image=False):
    p=Path(path).resolve();require(p.is_file(),'evidence-file-missing')
    if image:require(p.read_bytes().startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff')),'image-format-invalid')
    digest=sha(p);out=root/'evidence'/(digest+p.suffix.lower());out.parent.mkdir(exist_ok=True)
    if not out.exists():shutil.copyfile(p,out)
    require(sha(out)==digest,'evidence-corrupt')
    return {'path':str(out),'sha256':digest}

def verify(e):require(Path(e['path']).is_file() and sha(e['path'])==e['sha256'],'evidence-changed')
def load(root):
    s=read(root/'state.json');require(s.get('version')==1 and s.get('mode') in ('development','fixture'),'state-invalid');return s

def save(root,s,event):
    s['updated_at']=now();s['events'].append({'at':s['updated_at'],**event});atomic(root/'state.json',s);return s

def route(company,company_policy=None):
    if company_policy is not None:
        sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
        import execution_timing as timing
        configured=timing.company_run_target(company_policy,company)
        if configured is not None:return configured['groupid'],configured['production_group']
    cfg=PROJECT/'skills/daily-comment-stats/config'
    companies=read(cfg/'companies.json')['companies']
    with (cfg/'company_wecom_map.csv').open(encoding='utf-8-sig') as f:
        rows=[r for r in csv.DictReader(f) if r['公司名称']==company]
    require(len(rows)==1 and company in companies,'company-routing-not-unique')
    return str(companies[company]['groupid']),rows[0]['企业微信群']

BACKENDS = ('codex-existing-extension', 'local-dom-bridge')

def initialize(root,company,today=None,start=None,mode='development',backend='codex-existing-extension',*,company_policy=None):
    require(mode in ('development','fixture'),'mode-invalid')
    require(backend in BACKENDS,'browser-backend-invalid')
    gid,group=route(company,company_policy)
    if (root/'state.json').exists():
        s=load(root);require((s['company'],s['groupid'],s['brand_group'],s['mode'])==(company,gid,group,mode),'scope-conflict')
        require(s.get('browser_backend','codex-existing-extension')==backend,'browser-backend-conflict')
        require(start is None or start==s['initial_start'],'progress-reset-forbidden');return s
    today=today or shanghai_today().isoformat();cal=compute(today=today,force=True)
    require(not cal['warnings'],'calendar-needs-update');start=start or cal['start']
    require(date.fromisoformat(start)<date.fromisoformat(today),'today-excluded')
    s={'version':1,'mode':mode,'company':company,'groupid':gid,'brand_group':group,'initial_start':start,
       'next_start':start,'covered_through':None,'last_completed_on':None,'last_completed_at':None,
       'browser_backend':backend,'identity':None,'batches':{},'events':[]}
    return save(root,s,{'type':'initialized','start':start})

def require_empty_ledger(root,s,identity_empty=False):
    require(s.get('next_start')==s['initial_start'],'amend-progress-not-empty')
    fields=('tasks','batches','completions','completion','send_jobs','send_attempt','send_attempts',
            'receipts','sent','messages_sent','completed_at','covered_through','last_completed_on','last_completed_at',
            'coverage','send','send_intent','send_intents','completed','sent_at','completed_ranges','completion_history')
    require(not any(s.get(k) for k in fields),'amend-progress-not-empty')
    require(all(e.get('type') in ('initialized','empty-start-amended','empty-backend-amended') or (e.get('type') in ('operation-stopped','stopped') and e.get('operation',e.get('command')) in ('amend-empty-start','amend-empty-backend')) for e in s.get('events',[])),'amend-processing-history-present')
    if identity_empty:
        require(s.get('identity') is None and not any(s.get(k) for k in ('identity_before','identity_baseline','account_verified')),'amend-identity-not-empty')
    require(read(root/'state.json')==s,'amend-stale-state')


def empty_backup(root,s,label):
    require(read(root/'state.json')==s,'amend-stale-state')
    state_path=root/'state.json'
    old_sha=sha(state_path);backup=root/'state-backups'/('before-'+label+'-'+old_sha+'.json')
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        with backup.open('xb') as f:
            f.write(state_path.read_bytes());f.flush();os.fsync(f.fileno())
    require(sha(backup)==old_sha,'amend-backup-hash-mismatch')
    require(sha(state_path)==old_sha,'amend-state-changed')
    return {'path':str(backup.resolve()),'sha256':old_sha}


def amend_empty_start(root,s,start,today=None):
    """Backfill an untouched ledger only; never reset processed or sent data."""
    today=today or shanghai_today().isoformat()
    parsed=date.fromisoformat(start)
    require(parsed.isoformat()==start and start<s['initial_start'] and start<today,'amend-start-must-be-earlier')
    require_empty_ledger(root,s)
    backup=empty_backup(root,s,'empty-start')
    previous=s['initial_start'];s['initial_start']=start;s['next_start']=start
    return save(root,s,{'type':'empty-start-amended','previous_start':previous,'start':start,
                        'backup':backup,'not_completion':True})


def amend_empty_backend(root,s,backend):
    require(backend in BACKENDS,'browser-backend-invalid')
    require_empty_ledger(root,s,identity_empty=True)
    previous=s.get('browser_backend','codex-existing-extension')
    if backend==previous:return s
    backup=empty_backup(root,s,'empty-backend')
    s['browser_backend']=backend
    return save(root,s,{'type':'empty-backend-amended','previous_backend':previous,'backend':backend,
                        'backup':backup,'not_completion':True})


def plan(s,today=None):
    today=today or shanghai_today().isoformat();date.fromisoformat(today)
    return {'company':s['company'],'groupid':s['groupid'],'start':s['next_start'],
            'end_exclusive':today,'end':(date.fromisoformat(today)-timedelta(days=1)).isoformat(),
            'has_new_dates':s['next_start']<today,'brand_group':s['brand_group'],'send_target':TEST_GROUP,
            'unfinished_batches':[k for k,b in s['batches'].items() if not b.get('completed_at')],
            'browser_backend':s.get('browser_backend','codex-existing-extension'),'production_enabled':False,'platform_writes':False}

def check_source(p,s,today):
    require(p.get('company')==s['company'] and str(p.get('groupid'))==s['groupid'],'company-mismatch')
    u=urlparse(p['url'])
    require(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[s['groupid']],'origin-company-mismatch')
    require(p.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'source-invalid')
    stamp=datetime.fromisoformat(p['observed_at']);require(stamp.utcoffset() is not None,'timezone-required')
    if s['mode']!='fixture':require(stamp.astimezone(ZoneInfo('Asia/Shanghai')).date().isoformat()==today==shanghai_today().isoformat(),'live-capture-not-today')
    identity=p.get('identity')
    require(p.get('account_verified') is True and isinstance(identity,dict) and all(identity.get(k) for k in ('provider','account_id','manager')),'account-unverified')
    require(s['identity'] is None or s['identity']==identity,'account-changed')
    first,end=p['start'],p['end_exclusive']
    require(date.fromisoformat(first)<date.fromisoformat(end)<=date.fromisoformat(today),'range-invalid')
    return identity

def ingest(root,s,path,today=None):
    p=read(path);today=today or shanghai_today().isoformat();identity=check_source(p,s,today)
    if s['mode']!='fixture' and ('capture_manifest' in p or p.get('capture_schema') in ('governance-public-dom-capture-v1','governance-public-dom-zero-capture-v1')):
        require(s.get('browser_backend')=='local-dom-bridge' and p.get('source')=='local-dom-bridge','governance-capture-backend-mismatch')
    if s['mode']!='fixture' and s.get('browser_backend')=='local-dom-bridge':
        from governance_capture import validate as validate_public_capture
        require(validate_public_capture(path)==p,'governance-capture-intake-payload-changed')
    analysis,records=p['analysis'],p['records'];first,end=p['start'],p['end_exclusive']
    for section in (analysis,records):
        require(section.get('start')==first and section.get('end_exclusive')==end,'analysis-list-date-mismatch')
        require(section.get('all_pages_read') is True and section.get('filters_verified') is True,'pagination-or-filter-unverified')
        require(type(section.get('total')) is int and section['total']>=0,'total-invalid')
    require(analysis.get('scope')=='全部' and analysis.get('all_reasons_read') is True,'top10-is-not-complete')
    require(records.get('scope')=='全部' and records.get('unread_only') is False,'records-not-all')
    rows=analysis['rows'];keys=[]
    for r in rows:
        require(r.get('violation_type') and isinstance(r.get('object_types'),list) and r['object_types'],'analysis-fields-missing')
        require(all(isinstance(v,str) and v.strip() for v in r['object_types']),'object-types-invalid')
        require(type(r.get('count')) is int and r['count']>0,'analysis-count-invalid')
        keys.append((r['violation_type'],tuple(sorted(r['object_types']))))
    require(len(set(keys))==len(keys),'duplicate-analysis-bucket')
    require(sum(r['count'] for r in rows)==analysis['total'],'analysis-total-mismatch')
    items=records['rows'];require(len(items)==records['total'],'records-total-mismatch')
    require(analysis['total']==records['total'],'analysis-record-count-needs-reconciliation')
    ids=[r.get('notice_id') for r in items]
    require(all(isinstance(i,str) and i for i in ids) and len(set(ids))==len(ids),'notice-id-missing-or-duplicate')
    for r in items:
        require(first<=date.fromisoformat(r['date']).isoformat()<end,'record-outside-range')
        for key in ('subject','reason','object_type','object_name','effectiveness_status','rectification_status'):
            require(isinstance(r.get(key),str) and r[key].strip(),'record-field-missing:'+key)
        if r.get('reason')=='温馨提醒：锚点类型选择有误' or r.get('notice_kind')=='platform-anchor-reminder':require(platform_reminder(r),'platform-reminder-classification-required')
        actions=r.get('actions')
        require(isinstance(actions,list) and actions and all(isinstance(x,str) and x.strip() for x in actions),'disposal-actions-missing')
        # Public advice is a separate structured field, never the internal rule text.
        require(r.get('detail_read') is True and isinstance(r.get('public_recommendation'),str) and r['public_recommendation'].strip(),'detail-public-recommendation-required')
        require('…' not in r['subject']+r['reason']+r['object_name'],'truncated-record-needs-detail')
    batch=first+'_'+end;old=s['batches'].get(batch);fp=fingerprint(p)
    if old:
        if old['input_fingerprint']==fp:return s
        # Sealed zero-batch adoption (B35): a supervised archive-redispatch
        # re-captures the same scope under a changed site baseline. When the
        # sealed batch is the exact zero-verified send-free shape and this fresh
        # capture is also a fully verified zero for the same company and range,
        # the sealed batch stays authoritative and the fresh capture is archived
        # as re-capture evidence. Nothing is replaced; any other difference
        # still requires explicit reconciliation.
        sealed=(old.get('status')=='zero_verified' and old.get('total')==0 and old.get('send_jobs')=={} and old.get('analysis')==old.get('records')==[] and old.get('artifacts')is None and old.get('copy')is None and old.get('copy_evidence')is None and old.get('copy_parts')==[] and old.get('screenshots')==[] and old.get('screenshot_chains',[])==[] and old.get('blocked_reason')is None and old.get('completed_at')is None)
        require(sealed and old.get('start')==first and old.get('end_exclusive')==end and analysis['total']==0 and records['total']==0,'existing-batch-changed-reconcile-before-replacing')
        snap=evidence(root,path)
        return save(root,s,{'type':'zero-batch-recaptured','batch':batch,'recapture':snap})
    for previous in s['batches'].values():
        # Different batch ranges must never re-notify an already collected notice.
        require(not set(ids)&{r['notice_id'] for r in previous['records']},'notice-already-recorded-in-another-batch')
    snap=evidence(root,path);s['identity']=identity
    s['batches'][batch]={'start':first,'end_exclusive':end,'source':snap,'input_fingerprint':fp,
        'analysis':rows,'records':items,'total':records['total'],'captured_at':p['observed_at'],
        'status':'zero_verified' if records['total']==0 else 'captured','artifacts':None,'screenshots':[],
        'copy':None,'copy_parts':[],'copy_evidence':None,'send_jobs':{},'completed_at':None,'blocked_reason':None}
    return save(root,s,{'type':'captured','batch':batch,'total':records['total']})

def get_batch(s,batch):require(batch in s['batches'],'batch-missing');return s['batches'][batch]

def zero_recapture_aligned(s,b,source):
    """Supervised zero-recapture adoption (B35). The sealed zero-verified batch
    keeps its original authoritative source and binding fingerprint; the fresh
    capture is accepted only when it is the same company, groupid and scope and
    a fully verified zero. Identity and range validity were already enforced by
    check_source on ingest; this guards the send binding."""
    require(s['company']==source['company'] and str(s['groupid'])==str(source['groupid']),'zero-recapture-company-mismatch')
    require(b['start']==source['start'] and b['end_exclusive']==source['end_exclusive'],'zero-recapture-scope-mismatch')
    require(source['analysis']['total']==0 and source['records']['total']==0 and source['analysis']['rows']==[] and source['records']['rows']==[],'zero-recapture-not-zero')
    require(source.get('account_verified') is True,'zero-recapture-identity-unverified')
    return True

# Exact disposal facts/status are appended by code. Agent rewrites only reason/advice.
INTERNAL_MARKERS=('规则编号','规则依据','内部规则','判定明细','风控命中','算法判定','恶意商家','欺诈商家','垃圾信息发布者')
def check_public(text,records):
    require(isinstance(text,str) and text.strip(),'public-text-empty')
    forbidden=list(INTERNAL_MARKERS)
    for r in records:
        forbidden.extend(x for x in (r.get('internal_rule_basis'),r.get('internal_judgment_detail')) if x)
    require(not any(x in text for x in forbidden),'internal-or-accusatory-text-forbidden')

def client_object_label(record):
    # The original offending reply remains in Excel/evidence. Client notices
    # identify the object without repeating hostile words to the customer.
    if record.get('object_type')=='评价' and record.get('object_subtype')=='商家回复':
        basis=record.get('detail_object_type_basis',{});kind=basis.get('normalized_type_basis',{})
        ident=str(basis.get('object_id',''))
        require(kind.get('method')=='exact-comment-field-source-object-and-reply-disposal-v1'
                and kind.get('subtype')=='商家回复' and kind.get('source_disposal')=='平台对该回复下线'
                and ident.isascii() and ident.isdigit() and 1<=len(ident)<=32,'client-reply-object-proof-required')
        return '评价商家回复（评价ID：'+ident+'）'
    label=record['object_name'];basis=record.get('detail_object_type_basis',{});ident=basis.get('object_id');kind=record.get('object_type')
    if ident is not None:
        require(basis.get('object_type')==kind and isinstance(ident,str) and ident.isascii() and ident.isdigit() and 1<=len(ident)<=32,'client-object-id-proof-required')
        labels={'短视频':'短视频ID','直播':'直播ID','门店':'门店ID','商品':'商品ID','评价':'评价ID','商家':'商家ID'}
        require(kind in labels,'client-object-id-type-unreviewed');label+='（'+labels[kind]+'：'+ident+'）'
    store=basis.get('store_id')
    if kind!='门店' and store is not None and basis.get('store_id_observed') is True:
        require(isinstance(store,str) and store.isascii() and store.isdigit() and 1<=len(store)<=32,'client-store-id-proof-required');label+='（门店ID：'+store+'）'
    return label

def copy_order(s,batch):
    b=get_batch(s,batch)
    return {'batch':batch,'source_sha256':b['source']['sha256'],
            'items':[{'notice_id':r['notice_id'],'subject':r['subject'],'reason':r['reason'],'object_name':r['object_name'],
                'actions':r['actions'],'effectiveness_status':r['effectiveness_status'],
                'action_details':r.get('action_details',[]),'disposal_stage_text':r.get('disposal_stage_text',''),
                'public_recommendation':r['public_recommendation']} for r in b['records']],
            'output_fields':['notice_id','gentle_reason','recommendation'],
            'rules':['只改写违规原因和建议；主体、对象标识、处置动作和生效状态由代码保留。评价商家回复用评价ID标识，不在对客正文复述不友善原话。',
                     '措辞委婉、不作人身指控；建议须有可执行的整改出口。',
                     '不写内部规则依据、判定明细；不能承诺恢复流量、重新上架或改期，除非详情明确支持。',
                     '截图和Excel保留平台原文；文字版只用审核后的对客措辞。']}

def platform_reminder(record):
    return (record.get('notice_kind')=='platform-anchor-reminder' and record.get('not_business_violation') is True
            and record.get('reason')=='温馨提醒：锚点类型选择有误' and record.get('object_type')=='短视频'
            and record.get('actions')==['带货锚点修改为打卡锚点']
            and record.get('platform_non_violation_statement')=='该情况不属于违规，不会影响您的视频流量和账号。')

def set_copy(root,s,batch,path):
    b=get_batch(s,batch);require(b['total']>0,'zero-no-notification');require(not b['send_jobs'],'cannot-edit-after-send-prepared')
    p=read(path);require(p.get('source_sha256')==b['source']['sha256'],'copy-source-mismatch')
    import public_copy_template as templates
    if p.get('kind')==templates.KIND:
        require(p==templates.document(b['source']['sha256'],b['records']),'program-copy-template-provenance-conflict')
    else:
        require(p.get('agent_reviewed') is True and p.get('facts_preserved') is True and p.get('no_internal_rules') is True,'agent-copy-review-required')
    items=p['items'];require(len(items)==b['total'],'copy-item-count-mismatch')
    byid={x['notice_id']:x for x in items};require(len(byid)==len(items) and set(byid)=={r['notice_id'] for r in b['records']},'copy-id-mismatch')
    blocks=[]
    for n,r in enumerate(b['records'],1):
        x=byid[r['notice_id']];check_public(x['gentle_reason'],b['records']);check_public(x['recommendation'],b['records'])
        # Exact facts cannot be softened away (e.g. 下架 != 仅调整展示).
        actions='；'.join(r['actions'])
        disposal_lines=[f"    处置方式：{actions}（{r['effectiveness_status']}）"]
        if r.get('disposal_stage_text'):
            disposal_lines=[f"    处置方式：{actions}",f"    处置状态：{r['disposal_stage_text']}"]
        reason_label='违规原因'
        if platform_reminder(r):
            require(x['gentle_reason']==r['reason']+'。','platform-reminder-reason-must-remain-literal')
            reason_label='平台温馨提醒'
            disposal_lines=[f"    平台调整：{actions}",f"    调整说明：{r['disposal_stage_text']}",f"    平台说明：{r['platform_non_violation_statement']}"]
        blocks.append('\n'.join([f"{n}. {r['subject']}",f"    {reason_label}：{x['gentle_reason']}",f"    涉及对象：{client_object_label(r)}",
            *disposal_lines,f"    建议：{x['recommendation']}"]))
    require(all(len(block)<=7500 for block in blocks),'single-notice-message-needs-copy-shortening')
    groups=[];current=[];length=0
    for block in blocks:
        if current and length+len(block)+2>8500:groups.append(current);current=[];length=0
        current.append(block);length+=len(block)+2
    if current:groups.append(current)
    reminders=sum(platform_reminder(r) for r in b['records'])
    title=(f"平台通知汇总 {b['total']} 条（违规 {b['total']-reminders} 条，非违规提醒 {reminders} 条）" if reminders else f"违规汇总 {b['total']} 条")
    text=title+'\n'+'\n\n'.join(blocks)+'\n'
    out=root/'batches'/batch/'违规汇总通知.txt';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(text,encoding='utf-8')
    b['copy']={'path':str(out),'sha256':sha(out)};b['copy_parts']=[]
    for n,group in enumerate(groups,1):
        suffix=f'（第{n}/{len(groups)}部分）' if len(groups)>1 else ''
        part=out.parent/f'违规汇总通知-{n:02d}.txt'
        part.write_text(f"{title}{suffix}\n"+'\n\n'.join(group)+'\n',encoding='utf-8')
        require(len(part.read_text())<=10000,'message-part-too-long')
        b['copy_parts'].append({'path':str(part),'sha256':sha(part)})
    b['copy_evidence']=evidence(root,path)
    return save(root,s,{'type':'public-copy-reviewed','batch':batch})

def add_screenshot(root,s,batch,path,metadata):
    b=get_batch(s,batch);require(b['total']>0,'zero-no-notification');require(not b['send_jobs'],'cannot-change-after-send-prepared')
    metadata_bytes=Path(metadata).read_bytes();m=json.loads(metadata_bytes);metadata_sha=hashlib.sha256(metadata_bytes).hexdigest();require(m.get('source_sha256')==b['source']['sha256'] and m.get('sha256')==sha(path),'screenshot-source-mismatch')
    require(m.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'screenshot-source-invalid')
    require(m.get('filters_visible') is True and m.get('list_headers_visible') is True,'screenshot-scope-unverified')
    ids=m.get('notice_ids');require(isinstance(ids,list) and ids and len(ids)==len(set(ids)),'screenshot-ids-invalid')
    require(set(ids)<={r['notice_id'] for r in b['records']},'screenshot-unknown-record')
    chain=None
    if s['mode']!='fixture' and s.get('browser_backend','codex-existing-extension')=='local-dom-bridge':
        sys.path.insert(0,str(PROJECT/'skills/chrome-dom-export/scripts'))
        from screenshot_registration import validate_violation_registration
        chain=validate_violation_registration(path,m,source=b['source'],company=s['company'],groupid=s['groupid'],start=b['start'],end_exclusive=b['end_exclusive'],notice_ids=[r['notice_id'] for r in b['records']])
    entry={'file':evidence(root,path,True),'metadata':evidence(root,metadata),'notice_ids':ids}
    if chain:
        references=[]
        for ref in chain['references']:
            snapshot=evidence(root,ref['path']);require(snapshot['sha256']==ref['sha256'],'screenshot-proof-changed-before-snapshot');references.append(snapshot)
        require(entry['file']['sha256']==m['sha256'] and entry['metadata']['sha256']==metadata_sha,'screenshot-changed-before-snapshot')
        verify(b['source'])
        entry['public_dom_chain']={'version':chain['version'],'viewport_only':True,'references':references}
    if not any(x['file']['sha256']==entry['file']['sha256'] for x in b['screenshots']):b['screenshots'].append(entry)
    return save(root,s,{'type':'list-screenshot','batch':batch,'notice_ids':ids})

def add_screenshot_chain(root,s,batch,manifest_path):
    b=get_batch(s,batch);require(s['mode']=='development' and s.get('browser_backend')=='local-dom-bridge','frame-chain-live-bridge-only')
    require(b['total']>0 and not b['send_jobs'],'frame-chain-batch-not-editable')
    raw=Path(manifest_path).read_bytes();manifest=json.loads(raw);manifest_sha=hashlib.sha256(raw).hexdigest()
    previous=[c for c in b.get('screenshot_chains',[]) if c['chain_id']==manifest.get('chain_id')]
    if previous:
        require(len(previous)==1 and previous[0]['manifest']['sha256']==manifest_sha,'frame-chain-id-conflict')
        verify(previous[0]['manifest'])
        for f in previous[0]['frames']:
            verify(f['file']);verify(f['metadata'])
            for ref in f['references']:verify(ref)
        return s
    sys.path.insert(0,str(PROJECT/'skills/chrome-dom-export/scripts'))
    require(manifest.get('capture_backend') in (None,'screen-capture-kit','screen-capture-kit-dom-region'),'frame-chain-backend-unreviewed')
    if manifest.get('capture_backend')=='screen-capture-kit-dom-region':
        from region_frame_capture import validate_chain
    elif manifest.get('capture_backend')=='screen-capture-kit':
        from native_frame_capture import validate_chain
    else:
        from frame_capture import validate_chain
    checked=validate_chain(manifest,source=b['source'],company=s['company'],groupid=s['groupid'],start=b['start'],end_exclusive=b['end_exclusive'],notice_ids=[r['notice_id'] for r in b['records']])
    def snapshot(ref):
        copied=evidence(root,ref['path']);require(copied['sha256']==ref['sha256'],'frame-chain-changed-before-snapshot');return copied
    frames=[]
    for frame in checked['entries']:
        frames.append({'file':snapshot(frame['image']),'metadata':snapshot(frame['metadata']),'references':[snapshot(ref) for ref in frame['references']],
                       'notice_ids':frame['notice_ids'],'frame_mode':frame['frame_mode'],'page':frame['page']})
    manifest_evidence=snapshot({'path':str(Path(manifest_path).resolve()),'sha256':manifest_sha});verify(b['source'])
    entry={'chain_id':checked['chain_id'],'visibility_policy':checked['visibility_policy'],'source_sha256':b['source']['sha256'],'manifest':manifest_evidence,'frames':frames,'notice_ids':checked['notice_ids']}
    if checked.get('capture_backend')=='screen-capture-kit':entry.update(capture_backend='screen-capture-kit',whole_window=True,viewport_only=False)
    elif checked.get('capture_backend')=='screen-capture-kit-dom-region':entry.update(capture_backend='screen-capture-kit-dom-region',whole_window=False,region_only=True,viewport_only=False)
    b.setdefault('screenshot_chains',[]).append(entry)
    return save(root,s,{'type':'list-screenshot-chain','batch':batch,'chain_id':entry['chain_id'],'frames':len(frames),'notice_ids':entry['notice_ids']})


def build(root,s,batch):
    b=get_batch(s,batch);require(b['total']>0,'zero-no-artifacts-required');verify(b['source'])
    require(not b['send_jobs'],'cannot-rebuild-after-send-prepared')
    out=root/'batches'/batch;out.mkdir(parents=True,exist_ok=True)
    job=out/'build-input.json';atomic(job,{'company':s['company'],'mode':s['mode'],'batch':batch,**b})
    proc=subprocess.run([str(NODE),str(SKILL/'scripts/build-report.mjs'),str(job),str(out)],capture_output=True,text=True,timeout=120)
    require(proc.returncode==0,'report-export-failed: '+proc.stderr[-1000:])
    manifest=read(out/'artifacts.json')
    require(manifest.get('source_sha256')==b['source']['sha256'],'artifact-source-mismatch')
    for item in manifest['files']:verify(item)
    validate_artifact_coverage(manifest,b)
    b['artifacts']=manifest;b['status']='built'
    return save(root,s,{'type':'xlsx-and-complete-table-images','batch':batch})

def validate_artifact_coverage(manifest,b):
    require(len([f for f in manifest['files'] if f['kind']=='workbook'])==1,'workbook-count-invalid')
    for kind,total in [('analysis_image',len(b['analysis'])),('records_image',len(b['records']))]:
        cursor=1
        pages=[f for f in manifest['files'] if f['kind']==kind]
        require(pages,'table-images-missing')
        for page in pages:
            require(page.get('headers_repeated') is True and page.get('total_rows')==total,'table-image-metadata-invalid')
            require(page.get('first_row')==cursor and page.get('last_row',0)>=cursor,'table-image-gap-or-overlap')
            require(page.get('row_count')==page['last_row']-cursor+1,'table-image-row-count-invalid')
            cursor=page['last_row']+1
        require(cursor==total+1,'table-image-not-complete')


def send_orders(s,batch):
    b=get_batch(s,batch);require(b['total']>0 and b['artifacts'] and b['copy'],'artifacts-and-copy-required')
    verify(b['source']);verify(b['copy']);verify(b['copy_evidence'])
    require(b['artifacts'].get('source_sha256')==b['source']['sha256'],'artifact-source-mismatch')
    validate_artifact_coverage(b['artifacts'],b)
    covered=set()
    for e in b['screenshots']:
        verify(e['file']);verify(e['metadata'])
        if s['mode']!='fixture' and s.get('browser_backend','codex-existing-extension')=='local-dom-bridge':
            require(e.get('public_dom_chain',{}).get('version') in ('dom-only-20261021-6','dom-only-20261021-7','dom-only-20261021-8','dom-only-20261021-9','dom-only-20261021-10','dom-only-20261021-11','dom-only-20261103-12') and len(e['public_dom_chain'].get('references',[]))==4,'screenshot-live-chain-required')
            for ref in e['public_dom_chain']['references']:verify(ref)
        require(s['mode']=='fixture','region-only-final-evidence-required-historical-viewport')
        covered.update(e['notice_ids'])
    for chain in b.get('screenshot_chains',[]):
        require(s['mode']=='development' and s.get('browser_backend')=='local-dom-bridge' and chain.get('visibility_policy') in ('anchored-frames-v1','notice-five-business-cells-v1') and chain.get('source_sha256')==b['source']['sha256'],'frame-chain-send-scope-conflict')
        verify(chain['manifest']);require(bool(chain['frames']),'frame-chain-send-empty')
        require(chain.get('capture_backend') in (None,'screen-capture-kit','screen-capture-kit-dom-region'),'frame-chain-send-backend-unreviewed')
        stored_manifest=json.loads(Path(chain['manifest']['path']).read_text())
        require(stored_manifest.get('capture_backend')==chain.get('capture_backend'),'frame-chain-send-backend-conflict')
        if chain.get('capture_backend') in ('screen-capture-kit','screen-capture-kit-dom-region'):
            if chain['capture_backend']=='screen-capture-kit-dom-region':
                require(chain.get('whole_window') is False and chain.get('region_only') is True and chain.get('viewport_only') is False,'region-chain-image-scope-invalid')
            else:
                require(chain.get('whole_window') is True and chain.get('viewport_only') is False,'native-chain-image-scope-invalid')
            # Assembly already approved these exact registrations. Sending uses
            # their pinned bytes and coverage, never replays capture validation.
            require(stored_manifest['chain_id']==chain['chain_id'] and stored_manifest['source_sha256']==b['source']['sha256'] and len(stored_manifest['frames'])==len(chain['frames']),'native-chain-registered-coverage-changed')
            frame_ids=set()
            for registered,actual in zip(chain['frames'],stored_manifest['frames']):
                require(registered['metadata']['sha256']==actual['metadata']['sha256'],'native-chain-registered-frame-changed')
                verify(actual['metadata']);verify({'path':actual['image'],'sha256':registered['file']['sha256']})
                frame_ids.update(registered['notice_ids'])
            require(frame_ids==set(chain['notice_ids']),'native-chain-registered-coverage-changed')
        for frame in chain['frames']:
            verify(frame['file']);verify(frame['metadata'])
            # Region references are derived by the full validator and matched above,
            # including their exact SHA order; prefix/manual evidence has variable size.
            if chain.get('capture_backend')!='screen-capture-kit-dom-region':
                require(len(frame['references'])==5,'frame-chain-send-proof-incomplete')
            for ref in frame['references']:verify(ref)
        require(chain.get('capture_backend')!='screen-capture-kit','whole-window-historical-evidence-not-final-send')
        require(chain.get('capture_backend')=='screen-capture-kit-dom-region','region-only-final-evidence-required-historical-viewport')
        covered.update(chain['notice_ids'])
    require(covered=={r['notice_id'] for r in b['records']},'list-screenshot-coverage-incomplete')
    files=b['artifacts']['files']
    orders=[]
    for n,f in enumerate(files):
        verify(f);orders.append({'part':f['kind']+':'+str(n),'type':'file','file':f['path'],'file_sha256':f['sha256']})
    parts=b.get('copy_parts') or [b['copy']]
    for n,part in enumerate(parts,1):
        verify(part)
        label='public_text' if len(parts)==1 else f'public_text:{n}'
        orders.append({'part':label,'type':'text','text_file':part['path'],'text_sha256':part['sha256']})
    for n,e in enumerate(b['screenshots']):
        orders.append({'part':'source_list_screenshot:'+str(n),'type':'file','file':e['file']['path'],'file_sha256':e['file']['sha256']})
    for n,chain in enumerate(b.get('screenshot_chains',[])):
        for index,frame in enumerate(chain['frames']):
            orders.append({'part':f'source_list_screenshot:chain{n}:{index}','type':'file','file':frame['file']['path'],'file_sha256':frame['file']['sha256']})
    for o in orders:
        o.update(key='violation-'+fingerprint([s['groupid'],batch,o])[:28],kind='group',target=TEST_GROUP,scope='test')
    return orders

def dispatch(root,s,batch,*,sealed_orders=None):
    require(s['mode']=='development','fixture-external-send-forbidden');b=get_batch(s,batch)
    cli=PROJECT/'skills/wecom-messenger/scripts/messenger.py'
    import dispatch_validation_context
    context=dispatch_validation_context.derive(sys.modules[__name__],s,batch)
    orders=context.orders()
    if sealed_orders is not None:require(orders==sealed_orders,'execution-delivery-orders-changed-after-seal')
    for order in orders:
        context.check(s,batch,order)
        part=order['part'];entry=b['send_jobs'].get(part)
        content=['--file',order['file']] if order['type']=='file' else ['--text-file',order['text_file']]
        if not entry:
            proc=subprocess.run([sys.executable,str(cli),'prepare','--key',order['key'],'--kind','group','--target',TEST_GROUP,'--scope','test',*content],text=True,capture_output=True,timeout=30)
            require(proc.returncode==0,'send-prepare-failed: '+proc.stdout[-500:])
            entry={'order':order,'job_path':json.loads(proc.stdout)['job_path'],'confirmed':False};b['send_jobs'][part]=entry
            save(root,s,{'type':'send-job-prepared','batch':batch,'part':part,'job_path':entry['job_path']})
        require(entry['order']==order,'send-order-changed')
        if entry['confirmed']:continue
        context.check(s,batch,order)
        try:
            proc=subprocess.run([sys.executable,str(cli),'run','--job',entry['job_path']],capture_output=True,text=True,timeout=180)
        except subprocess.TimeoutExpired as error:
            save(root,s,{'type':'send-job-run-timeout','batch':batch,'part':part,'key':order['key'],'job_path':entry['job_path'],'timeout_seconds':error.timeout,'outcome':'unknown-pending-same-job-receipt'})
        # A timeout never authorizes another run/key; reconcile only this sender job.
        accept_receipt(root,s,batch,part,entry['job_path'],_dispatch_context=context)
    return s

def accept_receipt(root,s,batch,part,path,*,_dispatch_context=None):
    if _dispatch_context is None:orders={o['part']:o for o in send_orders(s,batch)}
    else:
        import dispatch_validation_context
        require(type(_dispatch_context) is dispatch_validation_context.DispatchContext and _dispatch_context.workflow is sys.modules[__name__],'dispatch-context-type-conflict')
        orders=_dispatch_context.checked_orders(s,batch)
    b=get_batch(s,batch);require(part in orders,'send-part-invalid')
    o=orders[part];r=read(path);job=r.get('job',{})
    require(job.get('key')==o['key'] and job.get('target')==TEST_GROUP and job.get('kind')=='group' and job.get('scope')=='test','send-receipt-scope-mismatch')
    require(r.get('fingerprint')==fingerprint(job),'sender-job-corrupt')
    require(r.get('status')=='complete' and r.get('phase')=='done' and r.get('ui_confirmed') is True,'send-unknown-stop-no-resend')
    require(job.get('type')==o['type'],'message-type-mismatch')
    if o['type']=='file':require(job.get('file_sha256')==o['file_sha256'],'sent-file-mismatch')
    else:require(hashlib.sha256(job.get('text','').encode()).hexdigest()==o['text_sha256'],'sent-text-mismatch')
    b['send_jobs'][part]={'order':o,'job_path':str(Path(path).resolve()),'confirmed':True,'receipt':evidence(root,path),'confirmation':SENT_LABEL}
    return save(root,s,{'type':'test-group-ui-confirmed','batch':batch,'part':part})

def complete(root,s,batch,*,zero_notice=None):
    value=complete_value(root,s,batch,zero_notice=zero_notice,completed_at=now(),completed_on=shanghai_today().isoformat())
    if s['batches'][batch]['completed_at']:return s
    s.clear();s.update(value)
    return save(root,s,{'type':'completed','batch':batch,'status':s['batches'][batch]['status'],'production_sent':False})

def complete_value(root,s,batch,*,zero_notice=None,completed_at,completed_on):
    s=__import__('copy').deepcopy(s)
    b=get_batch(s,batch);verify(b['source'])
    if b['completed_at']:return s
    if not b['total']and s.get('mode')!='fixture':require(zero_notice is not None,'zero-notice-required-before-completion')
    if b['total']:
        for o in send_orders(s,batch):
            entry=b['send_jobs'].get(o['part']);require(entry and entry['confirmed'],'notifications-not-complete');verify(entry['receipt'])
    if not b['total']and zero_notice is not None:
        zn=_zero_notice_module()
        require(set(zero_notice)=={'order','client'},'zero-notice-completion-shape');binding=zero_notice['order']['zero_result_binding'];_zero_notice_module(binding['zero_module_ref']);require(binding['flow']=='violation-notifier'and binding['company']==s['company']and binding['start']==b['start']and binding['end_exclusive']==b['end_exclusive']and binding['sources']==[b['source']],'zero-notice-completion-source');zn.client(zero_notice['order'],zero_notice['client']);b['zero_result_notification']=zero_notice
    return _complete_collected_value(s,batch,zero_notice=zero_notice,completed_at=completed_at,completed_on=completed_on)

def _complete_collected_value(s,batch,*,zero_notice=None,completed_at,completed_on):
    s=__import__('copy').deepcopy(s);b=get_batch(s,batch)
    if b['completed_at']:return s
    b['completed_at']=completed_at;b['status']='zero_notification_client_confirmed'if not b['total']and zero_notice is not None else 'zero_no_notification' if not b['total'] else 'test_notifications_complete'
    cursor=s['initial_start']
    for x in sorted(s['batches'].values(),key=lambda x:(x['start'],x['end_exclusive'])):
        if x['completed_at'] and x['start']<=cursor<x['end_exclusive']:cursor=x['end_exclusive']
    s['next_start']=cursor;s['covered_through']=(date.fromisoformat(cursor)-timedelta(days=1)).isoformat() if cursor>s['initial_start'] else None
    s['last_completed_at']=completed_at;s['last_completed_on']=completed_on
    return s

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True);sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init');p.add_argument('--company',required=True);p.add_argument('--start');p.add_argument('--today');p.add_argument('--mode',choices=['development','fixture'],default='development');p.add_argument('--backend',choices=BACKENDS,default='codex-existing-extension');p.add_argument('--company-policy');p.add_argument('--company-policy-sha256')
    p=sub.add_parser('amend-empty-start');p.add_argument('--start',required=True)
    p=sub.add_parser('amend-empty-backend');p.add_argument('--backend',choices=BACKENDS,required=True)
    p=sub.add_parser('plan');p.add_argument('--today')
    p=sub.add_parser('capture');p.add_argument('--input',required=True);p.add_argument('--today')
    for name in ('copy-order','copy','screenshot','screenshot-chain','build','send-orders','send-test','receipt','complete','block'):
        p=sub.add_parser(name);p.add_argument('--batch',required=True)
        if name in ('copy','receipt','screenshot-chain'):p.add_argument('--input',required=True)
        if name=='receipt':p.add_argument('--part',required=True)
        if name=='complete':p.add_argument('--zero-notice',help='JSON {order,client}; existing complete validator verifies source and original sender receipt')
        if name=='screenshot':p.add_argument('--file',required=True);p.add_argument('--metadata',required=True)
        if name=='block':p.add_argument('--reason',required=True)
    sub.add_parser('status');a=ap.parse_args()
    policy_ref=None
    if a.cmd=='init':
        require((a.company_policy is None)==(a.company_policy_sha256 is None),'company-policy-paired-ref-required')
        if a.company_policy is not None:policy_ref={'path':str(Path(a.company_policy)),'sha256':a.company_policy_sha256}
    with lock(a.root) as root:
        s=initialize(root,a.company,a.today,a.start,a.mode,a.backend,company_policy=policy_ref) if a.cmd=='init' else load(root)
        try:
            if a.cmd=='plan':out=plan(s,a.today)
            elif a.cmd=='copy-order':out=copy_order(s,a.batch)
            elif a.cmd=='send-orders':out=send_orders(s,a.batch)
            else:
                if a.cmd=='amend-empty-backend':amend_empty_backend(root,s,a.backend)
                elif a.cmd=='amend-empty-start':amend_empty_start(root,s,a.start)
                elif a.cmd=='capture':ingest(root,s,a.input,a.today)
                elif a.cmd=='copy':set_copy(root,s,a.batch,a.input)
                elif a.cmd=='screenshot':add_screenshot(root,s,a.batch,a.file,a.metadata)
                elif a.cmd=='screenshot-chain':add_screenshot_chain(root,s,a.batch,a.input)
                elif a.cmd=='build':build(root,s,a.batch)
                elif a.cmd=='send-test':dispatch(root,s,a.batch)
                elif a.cmd=='receipt':accept_receipt(root,s,a.batch,a.part,a.input)
                elif a.cmd=='complete':complete(root,s,a.batch,zero_notice=read(Path(a.zero_notice))if a.zero_notice else None)
                elif a.cmd=='block':
                    get_batch(s,a.batch)['blocked_reason']=a.reason;save(root,s,{'type':'blocked','batch':a.batch,'reason':a.reason})
                out={'ok':True,'plan':plan(s),'batches':{k:{'total':b['total'],'status':b['status']} for k,b in s['batches'].items()}}
            print(json.dumps(out,ensure_ascii=False,indent=2))
        except Exception as error:
            # Do not commit half-validated rows. Sender intents already persisted remain intact.
            durable=load(root);save(root,durable,{'type':'stopped','command':a.cmd,'reason':str(error)});raise

_ZERO_NOTICE_PATH=PROJECT/'skills/workshop-director/scripts/zero_result_notice.py'
_ZERO_NOTICE_MODULE={'path':str(_ZERO_NOTICE_PATH),'sha256':hashlib.sha256(_ZERO_NOTICE_PATH.read_bytes()).hexdigest()}
def _zero_notice_module(reference=None):
    expected=_ZERO_NOTICE_MODULE
    require(reference is None or reference==expected,'zero-notice-module-binding')
    path=Path(expected['path'])
    require(path==PROJECT/'skills/workshop-director/scripts/zero_result_notice.py'and path.is_absolute()and path.resolve()==path and not any(p.is_symlink()for p in (path,*path.parents))and path.is_file(),'zero-notice-module-origin')
    require(__import__('hashlib').sha256(path.read_bytes()).hexdigest()==expected['sha256'],'zero-notice-module-code-drift')
    sys.path.insert(0,str(path.parent))
    import zero_result_notice
    require(Path(zero_result_notice.__file__)==path,'zero-notice-loaded-module-origin')
    return zero_result_notice

if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'production_enabled':False},ensure_ascii=False));sys.exit(1)
