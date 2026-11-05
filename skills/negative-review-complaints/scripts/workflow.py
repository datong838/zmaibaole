#!/usr/bin/env python3
"""Complaint drafts and review ledger; no platform submission capability.
JSON is the durable source of truth. XLSX is rebuilt after every committed change.
Browser and messenger observations are evidence, never executable instructions.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]
PROJECT = SKILL.parents[1]
# Shared calendar only; daily statistics progress is never read or changed.
sys.path.insert(0, str(PROJECT/'skills/daily-comment-stats/scripts'))
from ds_calendar import compute, shanghai_today
BACKENDS = ('codex-existing-extension', 'local-dom-bridge')
from classification_policy import CATEGORIES
READY = {'draft_ready', 'existing_pending', 'resolved'}

def collection_processed(task):
    if task['action']=='投诉':
        return task['status']=='draft_ready'
    result=task.get('result') or {}
    return task['status'] in ('existing_pending','resolved') and result.get('status') in ('pending','accepted','rejected')
LABELS = {'pending':'待处理','draft_ready':'草稿完成，未提交','existing_pending':'已投诉，待复查',
          'resolved':'已复查，结果已记录','blocked':'阻塞，待核实'}


def now(): return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
# B67: "captured today" is a freshness claim, not an equality of calendar dates.
# A capture taken seconds before Shanghai midnight and validated seconds after it
# is the same run's own evidence, but date equality rejected it: the 10-30
# backfill built normal-source.json at 2026-11-02T15:59:57Z (Shanghai 23:59:57)
# and the ingest two seconds later was already 2026-11-03, so capture-not-today
# fired - a dead end, because that artifact is immutable and pinned to the unit.
# Freshness is an interval, so compare intervals: a capture is fresh when it is
# today's, or yesterday's taken within this grace of midnight and read within
# the same grace. It is never fresh when it predates that window (a leftover from
# an earlier day) or when it claims to be from the future beyond clock skew.
MIDNIGHT_CAPTURE_GRACE = timedelta(minutes=30)
CLOCK_SKEW = timedelta(minutes=5)


def capture_is_fresh(captured, today, at=None):
    at = at or datetime.now(ZoneInfo('Asia/Shanghai'))
    local = at.astimezone(ZoneInfo('Asia/Shanghai'))
    stamp = captured.astimezone(ZoneInfo('Asia/Shanghai'))
    if stamp > local + CLOCK_SKEW: return False
    if stamp.date().isoformat() == today: return True
    if stamp.date() >= local.date(): return False
    # Only a today that came from the clock may admit yesterday's capture; an
    # explicit backfill day keeps the strict equality it always had.
    if today != local.date().isoformat(): return False
    midnight = datetime.combine(local.date(), datetime.min.time(), ZoneInfo('Asia/Shanghai'))
    return (local - midnight) <= MIDNIGHT_CAPTURE_GRACE and (local - stamp) <= MIDNIGHT_CAPTURE_GRACE
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def require(value, message):
    if not value: raise ValueError(message)
def atomic(path, data):
    path=Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.pending-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


@contextmanager
def locked(root):
    root=Path(root).resolve(); root.mkdir(parents=True,exist_ok=True)
    with (root/'.lock').open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX)
        yield root


def evidence(root, path, image=False):
    src=Path(path).resolve()
    require(src.is_file(),'evidence-file-missing')
    if image:
        head=src.read_bytes()[:12]
        require(head.startswith(b'\x89PNG\r\n\x1a\n') or head.startswith(b'\xff\xd8\xff'),'screenshot-format-invalid')
    h=digest(src); dst=root/'evidence'/(h+src.suffix.lower())
    dst.parent.mkdir(exist_ok=True)
    if not dst.exists(): shutil.copyfile(src,dst)
    require(digest(dst)==h,'evidence-hash-mismatch')
    return {'path':str(dst),'sha256':h}


def verify_evidence(item):
    require(Path(item['path']).is_file() and digest(item['path'])==item['sha256'],'evidence-changed')


def check_url(url, groupid):
    u=urlparse(url)
    require(u.scheme=='https' and u.netloc=='life.douyin.com' and
            parse_qs(u.query).get('groupid')==[groupid],'company-origin-mismatch')


def load(root):
    s=read(root/'state.json')
    require(s.get('version')==1 and s.get('mode') in ('draft-only','fixture'),'state-invalid')
    return s


def save(root,s,event):
    if event.get('id') in s['tasks']:
        t=s['tasks'][event['id']]
        event={**event,'record':copy.deepcopy(t)}
    s['events'].append({'at':now(),**event}); s['updated_at']=now(); s['xlsx_dirty']=True
    atomic(root/'state.json',s)
    # Workbook failure never discards the committed event. Next invocation retries export.
    return s


def initialize(root,company,groupid,today=None,start=None,mode='draft-only',backend='codex-existing-extension'):
    require(mode in ('draft-only','fixture'),'submission-disabled')
    require(backend in BACKENDS,'browser-backend-invalid')
    require(company and str(groupid).isdigit(),'company-invalid')
    today=today or shanghai_today().isoformat()
    if (root/'state.json').exists():
        s=load(root); require((s['company'],s['groupid'],s['mode'])==(company,str(groupid),mode),'workspace-scope-conflict')
        require(s.get('browser_backend','codex-existing-extension')==backend,'browser-backend-conflict')
        require(start is None or start==s['initial_start'],'cannot-reset-progress')
        return s
    baseline=compute(today=today,force=True)
    require(not baseline['warnings'],'calendar-unverified')
    first=start or baseline['start']
    require(date.fromisoformat(first)<date.fromisoformat(today),'today-excluded')
    s={'version':1,'company':company,'groupid':str(groupid),'mode':mode,'initial_start':first,
       'next_start':first,'covered_through':None,'last_completed_on':None,'last_completed_at':None,
       'browser_backend':backend,'identity':None,'tasks':{},'batches':{},'events':[],'updated_at':now()}
    return save(root,s,{'type':'initialized','start':first})


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
    old_sha=digest(state_path);backup=root/'state-backups'/('before-'+label+'-'+old_sha+'.json')
    backup.parent.mkdir(exist_ok=True)
    if not backup.exists():
        with backup.open('xb') as f:
            f.write(state_path.read_bytes());f.flush();os.fsync(f.fileno())
    require(digest(backup)==old_sha,'amend-backup-hash-mismatch')
    require(digest(state_path)==old_sha,'amend-state-changed')
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
    today=today or shanghai_today().isoformat(); date.fromisoformat(today)
    return {'company':s['company'],'groupid':s['groupid'],'start':s['next_start'],
            'end_exclusive':today,'end':(date.fromisoformat(today)-timedelta(days=1)).isoformat(),
            'has_new_dates':s['next_start']<today,
            'recheck_ids':[k for k,t in s['tasks'].items() if t['status']!='resolved'],
            'next_actions':{k:next_action(s,k) for k,t in s['tasks'].items() if t['status']!='resolved' or not final_screenshot(s,t) or not t['wecom']},
            'xlsx_dirty':s.get('xlsx_dirty',False),
            'mode':s['mode'],'browser_backend':s.get('browser_backend','codex-existing-extension'),'submit_enabled':False,'wecom_target':'测试群请忽略'}


def final_screenshot(s,t):
    return bool(t.get('screenshot')) and (s['mode']=='fixture' or t['screenshot'].get('image_scope')=='derived-dom-review-region')


def next_action(s,key):
    t=task(s,key)
    if t['status']=='blocked':return 'resolve-block'
    if not t['screenshot']:return 'capture-screenshot'
    if not final_screenshot(s,t):return 'correct-to-region-screenshot' if t.get('wecom') else 'capture-region-screenshot'
    if not t['wecom']:return 'send-test'
    if t['action'] in ('查看投诉结果','投诉审核中'):
        return 'resolved' if t['status']=='resolved' else 'read-existing-result'
    if t['status']=='draft_ready':return 'draft-only-stop'
    return 'inspect-complaint-options-and-analyze'


def analysis_order(s,key):
    t=task(s,key);source=read(t['latest_snapshot']['path'])
    peers=[{'review_key':str(s['groupid'])+':'+r['review_id'],**r}for r in source['rows']if str(s['groupid'])+':'+r['review_id']!=key and r['date']==t['review']['date']and r['customer']==t['review']['customer']]
    return {'review_key':key,'next_action':'classify-current-review-draft-only','review':t['review'],'snapshot_sha256':t['latest_snapshot']['sha256'],'same_day_same_name_candidates':peers,'categories':list(CATEGORIES),'submit_enabled':False,'judgment_rules':['Use current original review, product and current form options only.','Assess all five types and explain exclusions. Do not infer malicious intent from low stars or subjective taste.','No historical examples, case memory or unverified facts. Draft only; never submit.']}


def ingest(root,s,payload,today=None):
    p=read(payload); today=today or shanghai_today().isoformat()
    require(p.get('company')==s['company'] and str(p.get('groupid'))==s['groupid'],'company-mismatch')
    check_url(p['url'],s['groupid'])
    identity=p.get('identity')
    require(p.get('account_verified') is True and isinstance(identity,dict) and all(identity.get(k) for k in ('provider','account_id','manager')),'account-unverified')
    require(s.get('identity') is None or s['identity']==identity,'account-changed')
    s['identity']=identity
    require(p.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'source-not-live')
    require(p.get('negative_filter')=='中差评（1-3心）' and p.get('filter_active') is True,'negative-filter-unverified')
    require(p.get('other_filters')=={'评价类型':'全部','评价来源':'全部','评价状态':'全部'},'unexpected-filters')
    first,end=p['start'],p['end_exclusive']
    require(date.fromisoformat(first)<date.fromisoformat(end)<=date.fromisoformat(today),'date-range-invalid')
    require(p.get('fold_boundary_verified') is True and p.get('all_pages_read') is True,'scope-or-pagination-unverified')
    rows=p['rows']; require(isinstance(rows,list),'rows-invalid')
    eligible=[r for r in rows if r.get('section')=='filtered']
    require(all(r.get('section') in ('filtered','folded') for r in rows),'unknown-review-section')
    require(type(p.get('filtered_count')) is int and len(eligible)==p['filtered_count'],'filtered-count-mismatch')
    ids=[r.get('review_id') for r in eligible]
    require(all(isinstance(i,str) and i.strip() for i in ids) and len(set(ids))==len(ids),'stable-review-id-required')
    snapshot=evidence(root,payload)
    require(p.get('observed_at') and datetime.fromisoformat(p['observed_at']).utcoffset() is not None,'capture-time-required')
    if s['mode']!='fixture':
        require(capture_is_fresh(datetime.fromisoformat(p['observed_at']),today),'capture-not-today')
    for r in eligible:
        require(type(r.get('stars')) is int and 1<=r['stars']<=3,'not-negative-review')
        date.fromisoformat(r['date'])
        require(first<=r['date']<end,'row-date-outside-filter')
        require(r.get('store') and isinstance(r.get('text'),str) and r.get('customer'),'review-fields-missing')
        require(r.get('action') in ('投诉','查看投诉结果','投诉审核中'),'unknown-complaint-action')
        key=s['groupid']+':'+r['review_id']; old=s['tasks'].get(key)
        immutable={k:r.get(k,'') for k in ('review_id','store','date','time','stars','customer','customer_id','text','product')}
        if old:
            require(old['review']==immutable,'review-changed-requires-reconciliation')
            if old['status']=='resolved' and r['action']=='投诉':
                old['status']='blocked';old['block_reason']='resolved-review-shows-complain-again'
            if r['action'] in ('查看投诉结果','投诉审核中') and old['status']!='resolved': old['status']='existing_pending'
            old['action']=r['action'];old['latest_snapshot']=snapshot
        else:
            s['tasks'][key]={'id':key,'review':immutable,'action':r['action'],
                'status':'existing_pending' if r['action'] in ('查看投诉结果','投诉审核中') else 'pending',
                'snapshot':snapshot,'latest_snapshot':snapshot,'screenshot':None,'wecom':None,
                'analysis':None,'history':None,'result':None,'updated_at':now()}
        if r.get('body_kind'):
            import normal_review_body as rb
            body=rb.provenance(r);previous_body=s['tasks'][key].get('body_provenance');require(previous_body in (None,body),'review-body-provenance-changed');s['tasks'][key]['body_provenance']=body
    batch_id=first+'_'+end
    previous=s['batches'].get(batch_id)
    # Re-observation can update a pending batch; closed coverage is immutable.
    if previous and previous.get('closed_at'):
        require(set(previous['ids'])=={s['groupid']+':'+r['review_id'] for r in eligible},'closed-range-changed')
    else:
        s['batches'][batch_id]={'start':first,'end_exclusive':end,'ids':[s['groupid']+':'+r['review_id'] for r in eligible],
            'snapshot':snapshot,'filtered_count':len(eligible),'excluded_folded':len(rows)-len(eligible),'closed_at':None}
    return save(root,s,{'type':'scope-captured','batch':batch_id,'count':len(eligible),'excluded_folded':len(rows)-len(eligible)})


def task(s,key):
    require(key in s['tasks'],'task-not-found'); return s['tasks'][key]


def review_validator():
    scripts=PROJECT/'skills/chrome-dom-export/scripts'
    sys.path.insert(0,str(scripts))
    spec=importlib.util.spec_from_file_location('complaint_review_registration',scripts/'review_registration.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.validate


def validate_review_screenshot(s,key,path,m):
    t=task(s,key);verify_evidence(t['latest_snapshot'])
    require(m.get('review_key')==key and m.get('snapshot_sha256')==t['latest_snapshot']['sha256'],'screenshot-scope-mismatch')
    require(m.get('source')==s.get('browser_backend','codex-existing-extension')=='local-dom-bridge','review-screenshot-backend-required')
    require(m.get('sha256')==digest(path),'screenshot-content-hash-mismatch')
    ref=m.get('registration',{});require(set(ref)=={'path','sha256'},'review-registration-reference-required')
    require(Path(ref['path']).is_absolute() and not Path(ref['path']).is_symlink(),'review-registration-path-invalid');verify_evidence(ref)
    registered=read(ref['path']);source_ref=registered.get('source',{})
    require(source_ref.get('sha256')==t['latest_snapshot']['sha256'],'review-registration-source-mismatch')
    verify_evidence(source_ref);source=read(source_ref['path']);require(source==read(t['latest_snapshot']['path']),'review-registration-not-current-snapshot')
    require(source.get('company')==s['company'] and str(source.get('groupid'))==s['groupid'] and source.get('identity')==s['identity'],'review-registration-merchant-mismatch')
    matched=[r for r in source.get('rows',[]) if s['groupid']+':'+str(r.get('review_id'))==key]
    require(len(matched)==1,'review-registration-key-not-in-normal-source')
    require(all(matched[0].get(k,'')==v for k,v in t['review'].items()),'review-registration-review-changed')
    checked=review_validator()(ref['path'],source_sha256=t['latest_snapshot']['sha256'],review_key=key)
    require(checked.get('ok') is True and key in checked.get('review_keys',[]) and checked.get('review_keys')==registered.get('review_keys'),'review-registration-key-unverified')
    image=checked.get('image',{});require(digest(image['path'])==digest(path)==image.get('sha256'),'review-registration-image-mismatch')
    require(checked.get('occlusion_verified') is False and type(checked.get('text_complete_in_image',{}).get(key)) is bool,'review-registration-limitations-missing')
    require(checked.get('image_scope')=='derived-dom-review-region' and checked.get('whole_window') is False and checked.get('region_derived') is True and checked.get('capture_backend')=='screen-capture-kit-dom-region','review-region-screenshot-required')
    verify_evidence(ref);verify_evidence(source_ref);return ref


def attach_screenshot(root,s,key,path,metadata):
    t=task(s,key);m=read(metadata)
    require(m.get('review_key')==key and m.get('snapshot_sha256')==t['latest_snapshot']['sha256'],'screenshot-scope-mismatch')
    require(m.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'screenshot-not-live')
    registration=None
    if s['mode']=='fixture':require(m.get('filters_visible') is True and m.get('review_visible') is True,'screenshot-content-unverified')
    else:registration=validate_review_screenshot(s,key,path,m)
    require(m.get('sha256')==digest(path),'screenshot-content-hash-mismatch')
    item=evidence(root,path,image=True);item['metadata']=evidence(root,metadata)
    if registration:item['registration']=evidence(root,registration['path'])
    if registration:item['image_scope']='derived-dom-review-region'
    require(not (t['wecom'] or t.get('send_attempt')) or t['screenshot']==item,'cannot-replace-sent-or-unknown-screenshot')
    t['screenshot']=item
    return save(root,s,{'type':'screenshot','id':key})


def register_review_screenshot(root,s,key,registration):
    require(s['mode']=='draft-only','fixture-review-registration-forbidden')
    original=Path(registration);require(not original.is_symlink(),'review-registration-path-invalid');path=original.resolve();r=read(path)
    t=task(s,key);image=r['image']['path']
    metadata={'review_key':key,'snapshot_sha256':t['latest_snapshot']['sha256'],'source':s.get('browser_backend'),'sha256':r['image']['sha256'],'registration':{'path':str(path),'sha256':digest(path)}}
    validate_review_screenshot(s,key,image,metadata)
    wrapper=root/'registration-wrappers'/(hashlib.sha256((key+metadata['registration']['sha256']).encode()).hexdigest()+'.json')
    if wrapper.exists():require(read(wrapper)==metadata,'review-registration-wrapper-conflict')
    else:atomic(wrapper,metadata)
    return attach_screenshot(root,s,key,image,wrapper)


def completed_image_send(t):
    """Authenticate the old complete send before allowing a user correction.
    Unknown/failed sends cannot be replaced with a fresh image/key.
    """
    require(t.get('screenshot') and t.get('wecom') and t.get('send_attempt'),'region-correction-requires-confirmed-original-send')
    verify_evidence(t['screenshot']);verify_evidence(t['wecom'])
    attempt=t['send_attempt'];order=attempt['order'];saved=read(t['wecom']['path']);current=read(attempt['job_path'])
    for receipt in (saved,current):
        req=receipt.get('job',{})
        require(receipt.get('status')=='complete' and receipt.get('phase')=='done' and receipt.get('ui_confirmed') is True and not receipt.get('error'),'region-correction-original-send-not-complete')
        require(receipt.get('fingerprint')==hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'region-correction-original-job-changed')
        require(req.get('key')==order['key'] and req.get('target')=='测试群请忽略' and req.get('kind')=='group' and req.get('scope')=='test' and req.get('file_sha256')==t['screenshot']['sha256'],'region-correction-original-send-scope-mismatch')
    require(saved['fingerprint']==current['fingerprint'],'region-correction-original-job-conflict')
    return {'path':str(Path(attempt['job_path']).resolve()),'sha256':digest(attempt['job_path']),'key':order['key']}


def revise_review_screenshot(root,s,key,registration,reason):
    require(s['mode']=='draft-only' and reason=='user-requested-region-only','region-correction-reason-required')
    t=task(s,key);original_path=Path(registration);require(not original_path.is_symlink(),'review-registration-path-invalid');path=original_path.resolve();r=read(path)
    # Idempotent retry of the same already installed revision never clears a send.
    if final_screenshot(s,t):
        require(t['screenshot']['registration']['sha256']==digest(path),'region-correction-already-applied-different-registration')
        validate_review_screenshot(s,key,t['screenshot']['path'],read(t['screenshot']['metadata']['path']));return s
    original=completed_image_send(t)
    image=r['image']['path'];metadata={'review_key':key,'snapshot_sha256':t['latest_snapshot']['sha256'],'source':s.get('browser_backend'),'sha256':r['image']['sha256'],'registration':{'path':str(path),'sha256':digest(path)}}
    validate_review_screenshot(s,key,image,metadata)
    require(metadata['sha256']!=t['screenshot']['sha256'],'region-correction-image-must-differ')
    old={k:copy.deepcopy(t.get(k)) for k in ('screenshot','wecom','send_attempt')}
    revision={'revision':len(t.get('screenshot_revisions',[]))+1,'reason':reason,'at':now(),'previous':old,'original_complete_job':original,'new_registration':metadata['registration'],'new_image_sha256':metadata['sha256']}
    # Preserve the exact old ledger bytes as well as immutable per-task history.
    state_path=root/'state.json'
    if state_path.is_file():revision['ledger_before']=evidence(root,state_path)
    t.setdefault('screenshot_revisions',[]).append(revision);t['screenshot']=None;t['wecom']=None;t.pop('send_attempt',None)
    try:return register_review_screenshot(root,s,key,path)
    except Exception:
        t.update(old);t['screenshot_revisions'].pop();raise


def send_order(root,s,key):
    t=task(s,key);require(t['screenshot'],'screenshot-required');verify_evidence(t['screenshot'])
    verify_evidence(t['screenshot']['metadata'])
    if s['mode']!='fixture':
        registered=validate_review_screenshot(s,key,t['screenshot']['path'],read(t['screenshot']['metadata']['path']))
        verify_evidence(t['screenshot']['registration']);require(registered['sha256']==t['screenshot']['registration']['sha256'],'review-registration-copy-changed')
    return _collected_send_order(root,s,key)

def _collected_send_order(root,s,key):
    sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'skills/workshop-director/scripts'))
    import delivery_targets
    t=task(s,key)
    # Durable attempted order takes precedence even after a directory relocation.
    if t.get('send_attempt'):
        order=t['send_attempt']['order']
        require(order['file']==t['screenshot']['path'],'send-attempt-screenshot-changed')
        return order
    # Stable key across restart; never mint a fresh key after unknown delivery.
    keyhash=hashlib.sha256((str(root)+key+t['screenshot']['sha256']).encode()).hexdigest()[:24]
    return {'key':'complaint-check-'+keyhash,'kind':'group','target':delivery_targets.target('negative-review-complaints'),'scope':'test',
            'file':t['screenshot']['path'],'review_key':key}


def send_test(root,s,key):
    require(s['mode']=='draft-only','fixture-external-send-forbidden')
    order=send_order(root,s,key)
    cli=PROJECT/'skills/wecom-messenger/scripts/messenger.py'
    command=[sys.executable,str(cli),'prepare','--key',order['key'],'--kind','group','--target',order['target'],'--scope','test','--file',order['file']]
    prepared=subprocess.run(command,capture_output=True,text=True,timeout=30)
    require(prepared.returncode==0,'messenger-prepare-failed: '+prepared.stdout[-800:])
    job_path=Path(json.loads(prepared.stdout)['job_path'])
    sender=read(job_path)
    require(not sender.get('error') and sender.get('status') not in ('failed','abandoned'),'messenger-original-job-needs-supervisor')
    require(sender.get('status')!='unknown' or sender.get('phase') in ('verify-sent','image-verify-sent'),'messenger-original-unknown-hold-no-replay')
    t=task(s,key)
    t['send_attempt']={'order':order,'job_path':str(job_path)}
    save(root,s,{'type':'wecom-job-prepared','id':key,'job_path':str(job_path)})
    # Messenger owns durable send intent and unknown-outcome reconciliation.
    verb='step' if sender.get('status')=='unknown' else 'run'
    try:
        # Public AX verification can require several complete window snapshots.
        executed=subprocess.run([sys.executable,str(cli),verb,'--job',str(job_path)],capture_output=True,text=True,timeout=360)
    except subprocess.TimeoutExpired:
        save(root,s,{'type':'wecom-timeout','id':key,'job_path':str(job_path),'timeout_seconds':360})
        raise ValueError('wecom-timeout: inspect same job; do not generate a new key') from None
    if executed.returncode!=0:
        save(root,s,{'type':'wecom-stopped','id':key,'job_path':str(job_path)})
        raise ValueError('wecom-not-confirmed: inspect same job; do not generate a new key')
    return attach_wecom(root,s,key,job_path)


def attach_wecom(root,s,key,receipt):
    t=task(s,key);order=send_order(root,s,key);r=read(receipt)
    req=r.get('job',{})
    require(req.get('target')==order['target'] and req.get('kind')=='group' and req.get('scope')=='test','wecom-recipient-mismatch')
    require(r.get('status')=='complete' and r.get('phase')=='done' and r.get('ui_confirmed') is True,'send-not-confirmed-no-resend')
    require(r.get('fingerprint')==hashlib.sha256(json.dumps(req,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'wecom-job-changed')
    require(req.get('key')==order['key'],'wecom-idempotency-key-mismatch')
    require(req.get('file_sha256')==t['screenshot']['sha256'],'wecom-file-mismatch')
    t['wecom']=evidence(root,receipt)
    t['send_attempt']={'order':order,'job_path':str(Path(receipt).resolve())}
    return save(root,s,{'type':'test-group-ui-confirmed','id':key,'delivery_confirmed':False})


def attach_history(root,s,key,path):
    t=task(s,key);p=read(path);check_url(p['url'],s['groupid'])
    require(str(p.get('groupid'))==s['groupid'] and p.get('company')==s['company'],'history-company-mismatch')
    require(p.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'history-source-invalid')
    if p.get('mode')=='sampled-recent-results':
        from recent_other_history import validate as validate_samples
        require(s['mode']=='draft-only','sample-history-live-root-required')
        samples=validate_samples(root,s,key,p,as_of=shanghai_today())
        t['history']={'evidence':evidence(root,path),'mode':'sampled-recent-results','start':p['start'],'end_exclusive':p['end_exclusive'],'count':len(samples),'items':samples,'is_exhaustive':False,'assembled_at':p['assembled_at']}
        if p.get('kind')=='recent-other-result-samples-v2':t['history'].update(schema=p['kind'],window_days=p['window_days'])
        return save(root,s,{'type':'other-history-samples-reviewed','id':key,'count':len(samples),'is_exhaustive':False})
    observed=datetime.fromisoformat(p['observed_at'])
    require(observed.utcoffset() is not None,'history-timezone-required')
    day=observed.astimezone(ZoneInfo('Asia/Shanghai')).date();start=(day-timedelta(days=7)).isoformat()
    require(p.get('start')==start and p.get('end_exclusive')==day.isoformat() and p.get('all_pages_read') is True,'history-week-incomplete')
    for x in p['items']:
        require(x.get('category')=='其他' and start<=x['date']<day.isoformat() and x.get('text'),'history-item-invalid')
    t['history']={'evidence':evidence(root,path),'start':start,'end_exclusive':day.isoformat(),
                  'count':len(p['items']),'items':p['items']}
    return save(root,s,{'type':'other-history-reviewed','id':key,'count':len(p['items'])})


def verified_pre_delivery_image(root,s,key,seal_ref):
    """Distinct pre-delivery evidence; never a client confirmation."""
    import complaint_execution_order as original_order
    seal=original_order.doc(seal_ref)
    require(set(seal)=={'kind','order','item'}and seal['kind']=='complaint-pre-delivery-image-seal-v1','pre-delivery-image-seal-shape')
    order=original_order.validate(seal['order'])
    require(order.get('collection_contract')=='three-flow-collection-ready-v1','pre-delivery-staged-order-required')
    company=[c for c in order['companies']if c['company']==s['company']and c['groupid']==s['groupid']and c['root']==str(Path(root).resolve())]
    require(len(company)==1,'pre-delivery-order-company');t=task(s,key);item=seal['item']
    require(final_screenshot(s,t)and item=={'company':s['company'],'root':str(Path(root).resolve()),'review_key':key,'order':send_order(Path(root),s,key),'image_sha256':t['screenshot']['sha256'],'source':t['latest_snapshot']},'pre-delivery-current-image-binding')
    require(not t.get('send_attempt')and not t.get('wecom'),'pre-delivery-not-client-proof')
    verify_evidence(t['screenshot']);verify_evidence(t['latest_snapshot'])
    return seal

def analyze(root,s,key,path,*,collection_seal=None):
    t=task(s,key);a=read(path)
    require(t['action']=='投诉' and t['status']!='resolved','already-complained-do-not-draft-again')
    if collection_seal is not None:verified_pre_delivery_image(root,s,key,collection_seal)
    else:
        require(final_screenshot(s,t) and t['wecom'],'screenshot-and-test-group-check-required')
        verify_evidence(t['screenshot']);verify_evidence(t['wecom'])
    require(a.get('review_key')==key and a.get('snapshot_sha256')==t['latest_snapshot']['sha256'],'analysis-scope-mismatch')
    require(a.get('category') in CATEGORIES and a.get('reason') and a.get('draft'),'analysis-fields-invalid')
    if a.get('analysis_source') is None:
        require(a.get('agent_assessed') is True and a.get('no_fabricated_facts') is True,'agent-assessment-required')
        origin='agent'
    else:
        from classification_policy import assessment_origin
        origin=assessment_origin(a)
    if s['mode']=='draft-only' or origin=='rules':
        from draft_inspection import validate_analysis
        validate_analysis(root,s,key,a)
        from classification_policy import validate as validate_classification
        validate_classification(s,key,a)
    quotes=a.get('quotes',[])
    require(isinstance(quotes,list) and all(q and q in t['review']['text'] for q in quotes),'quote-not-in-original')
    require(a['category']=='其他' or quotes,'specific-category-needs-original-evidence')
    require(a.get('suspected_bulk') in (True,False),'bulk-indicator-required')
    if a['suspected_bulk']:
        peers=[task(s,i) for i in a.get('related_ids',[]) if i!=key]
        require(peers and all(p['review']['date']==t['review']['date'] and p['review']['customer']==t['review']['customer'] for p in peers),'bulk-date-name-evidence-missing')
        require(a.get('similarity_reason') and a.get('identity_uncertain') is True,'bulk-is-suspicion-not-identity-proof')
    # Legacy agent judgments retain their contract; explicit rule drafts are replayed by classification_policy.
    t['analysis']={**a,'evidence':evidence(root,path)};t['status']='draft_ready';t['updated_at']=now()
    return save(root,s,{'type':'draft-ready-not-submitted','id':key,'category':a['category']})


def record_result(root,s,key,path):
    t=task(s,key);p=read(path)
    require(t['action'] in ('查看投诉结果','投诉审核中') or t['status']=='existing_pending','no-platform-complaint-to-recheck')
    require(p.get('review_key')==key and p.get('snapshot_sha256')==t['latest_snapshot']['sha256'],'result-scope-mismatch')
    check_url(p['url'],s['groupid'])
    require(p.get('source')==('fixture' if s['mode']=='fixture' else s.get('browser_backend','codex-existing-extension')),'result-source-invalid')
    require(p.get('status') in ('pending','accepted','rejected','unknown') and p.get('visible_text'),'result-unverified')
    require(p.get('observed_at'),'result-time-required')
    stamp=datetime.fromisoformat(p['observed_at'])
    require(stamp.utcoffset() is not None,'result-timezone-required')
    if s['mode']!='fixture':require(capture_is_fresh(stamp,shanghai_today().isoformat()),'result-not-today')
    t['result']={**p,'evidence':evidence(root,path)}
    t['status']='resolved' if p['status'] in ('accepted','rejected') else 'existing_pending'
    t['updated_at']=now()
    saved=save(root,s,{'type':'platform-result-read','id':key,'result':p['status']})
    return saved


def block(root,s,key,reason):
    t=task(s,key);require(reason,'block-reason-required');t['status']='blocked';t['block_reason']=reason
    return save(root,s,{'type':'blocked','id':key,'reason':reason})


def close_batch(root,s,batch):
    value=close_batch_value(root,s,batch,completed_at=now(),completed_on=shanghai_today().isoformat())
    if s['batches'][batch]['closed_at']:return s
    s.clear();s.update(value)
    return save(root,s,{'type':'draft-batch-completed','batch':batch,'not_platform_submission':True})

def close_batch_value(root,s,batch,*,completed_at,completed_on):
    s=copy.deepcopy(s)
    b=s['batches'][batch];verify_evidence(b['snapshot'])
    for key in b['ids']:
        t=task(s,key)
        require(t['status'] in READY and final_screenshot(s,t) and t['wecom'],'batch-has-unfinished-tasks')
        for e in (t['latest_snapshot'],t['screenshot'],t['wecom']):verify_evidence(e)
        if s['mode']!='fixture':send_order(root,s,key)
        if t['result']:verify_evidence(t['result']['evidence'])
        require(t['action'] not in ('查看投诉结果','投诉审核中') or t['result'],'existing-complaint-needs-result-read')
        if t['analysis']:verify_evidence(t['analysis']['evidence'])
    return _close_collected_batch_value(s,batch,completed_at=completed_at,completed_on=completed_on)

def _close_collected_batch_value(s,batch,*,completed_at,completed_on):
    s=copy.deepcopy(s);b=s['batches'][batch]
    if b['closed_at']: return s
    b['closed_at']=completed_at
    cursor=s['initial_start']
    for x in sorted(s['batches'].values(),key=lambda x:(x['start'],x['end_exclusive'])):
        if x['closed_at'] and x['start']<=cursor<x['end_exclusive']:cursor=x['end_exclusive']
    s['next_start']=cursor
    s['covered_through']=(date.fromisoformat(cursor)-timedelta(days=1)).isoformat() if cursor>s['initial_start'] else None
    s['last_completed_at']=completed_at;s['last_completed_on']=completed_on
    return s


def export_xlsx(root,s):
    raise RuntimeError('current-period-export-requires-explicit-collected-review-keys-use-current-complaint-workbook')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True)
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('init');p.add_argument('--company',required=True);p.add_argument('--groupid',required=True);p.add_argument('--start');p.add_argument('--today');p.add_argument('--mode',choices=['draft-only','fixture'],default='draft-only');p.add_argument('--backend',choices=BACKENDS,default='codex-existing-extension')
    p=sub.add_parser('amend-empty-start');p.add_argument('--start',required=True)
    p=sub.add_parser('amend-empty-backend');p.add_argument('--backend',choices=BACKENDS,required=True)
    p=sub.add_parser('plan');p.add_argument('--today')
    p=sub.add_parser('capture');p.add_argument('--input',required=True);p.add_argument('--today')
    for name in ('screenshot','wecom','history','analyze','result','block'):
        p=sub.add_parser(name);p.add_argument('--id',required=True)
        if name=='screenshot':p.add_argument('--file',required=True);p.add_argument('--metadata',required=True)
        elif name=='block':p.add_argument('--reason',required=True)
        else:p.add_argument('--input',required=True)
    p=sub.add_parser('register-review-screenshot');p.add_argument('--id',required=True);p.add_argument('--registration',required=True)
    p=sub.add_parser('revise-review-screenshot');p.add_argument('--id',required=True);p.add_argument('--registration',required=True);p.add_argument('--reason',required=True,choices=['user-requested-region-only'])
    p=sub.add_parser('send-order');p.add_argument('--id',required=True)
    p=sub.add_parser('analysis-order');p.add_argument('--id',required=True)
    p=sub.add_parser('send-test');p.add_argument('--id',required=True)
    p=sub.add_parser('close');p.add_argument('--batch',required=True)
    sub.add_parser('export');sub.add_parser('status')
    args=ap.parse_args()
    with locked(args.root) as root:
        if (root/'state.json').exists():
            require(load(root).get('workspace_kind')!='negative-review-appeal-history-only-v1',
                    'history-only-workspace-use-history_workspace.py')
        s=initialize(root,args.company,args.groupid,args.today,args.start,args.mode,args.backend) if args.cmd=='init' else load(root)
        if args.cmd=='plan': out=plan(s,args.today)
        elif args.cmd=='send-order':out=send_order(root,s,args.id)
        elif args.cmd=='analysis-order':out=analysis_order(s,args.id)
        else:
            try:
                if args.cmd=='amend-empty-backend':amend_empty_backend(root,s,args.backend)
                elif args.cmd=='amend-empty-start':amend_empty_start(root,s,args.start)
                elif args.cmd=='capture':ingest(root,s,args.input,args.today)
                elif args.cmd=='screenshot':attach_screenshot(root,s,args.id,args.file,args.metadata)
                elif args.cmd=='register-review-screenshot':register_review_screenshot(root,s,args.id,args.registration)
                elif args.cmd=='revise-review-screenshot':revise_review_screenshot(root,s,args.id,args.registration,args.reason)
                elif args.cmd=='send-test':send_test(root,s,args.id)
                elif args.cmd=='wecom':attach_wecom(root,s,args.id,args.input)
                elif args.cmd=='history':attach_history(root,s,args.id,args.input)
                elif args.cmd=='analyze':analyze(root,s,args.id,args.input)
                elif args.cmd=='result':record_result(root,s,args.id,args.input)
                elif args.cmd=='block':block(root,s,args.id,args.reason)
                elif args.cmd=='close':close_batch(root,s,args.batch)
            except Exception as error:
                # Discard uncommitted in-memory edits; retain any sender stop checkpoint.
                durable=load(root)
                save(root,durable,{'type':'operation-stopped','id':getattr(args,'id',None),'operation':args.cmd,'reason':str(error)})
                try:export_xlsx(root,durable)
                except Exception:pass  # xlsx_dirty remains true and JSON is recoverable.
                raise
            xlsx=export_xlsx(root,s)
            out={'ok':True,'plan':plan(s),'tasks':len(s['tasks']),'workbook':xlsx,'xlsx_dirty':False}
        print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'ok':False,'error':str(exc),'submission_enabled':False,'note':'Committed JSON events are retained; export can be retried.'},ensure_ascii=False));sys.exit(1)
