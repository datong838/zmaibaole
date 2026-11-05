"""Persistent per-company continuous coverage. Completion is not message delivery.

Only validated live collection receipts advance coverage; manual imports, test
messages, failed runs and unverified zero-row files cannot skip missing days.
"""
import json
from datetime import date,timedelta
from pathlib import Path
from ds_common import PROJECT,FlowError,atomic_json,lock,now,sha256,receipt_valid

DEFAULT_PROGRESS=PROJECT/'runtime/daily-comment-stats/progress.json'

def read(path):
    path=Path(path)
    if not path.exists():return {'version':1,'companies':{}}
    data=json.loads(path.read_text())
    if not isinstance(data,dict) or data.get('version')!=1 or not isinstance(data.get('companies'),dict):raise FlowError('progress-invalid')
    return data

def save(path,data):
    data['updated_at']=now();atomic_json(path,data)

def ensure(path=DEFAULT_PROGRESS):
    path=Path(path).resolve()
    with lock(path.parent):
        data=read(path)
        if not path.exists():save(path,data)
        return data

def initialize(path,company,start,reason='explicit initial backlog'):
    """Declare a pending start only. Never invent a completed date."""
    date.fromisoformat(start);path=Path(path).resolve()
    with lock(path.parent):
        data=read(path);entry=data['companies'].get(company)
        if entry:
            if entry['initial_start']!=start:raise FlowError('progress-already-initialized','Never reset an existing completion cursor')
            return entry
        entry={'initial_start':start,'covered_through':None,'next_start':start,
               'last_completed_on':None,'last_completed_at':None,'last_run_date':None,
               'completions':[],'planned_runs':{},'initial_reason':reason}
        data['companies'][company]=entry;save(path,data);return entry

def unresolved_run(entry,company,current):
    for reservation in entry.get('collection_reservations',{}).values():
        if reservation.get('state')=='collection-ready' and reservation.get('run_dir')!=str(Path(current).resolve()):
            raise FlowError('collection-reservation-pending-delivery','Resume original unified batch; do not recollect')
    for previous in entry.get('planned_runs',{}):
        if Path(previous).resolve()==Path(current).resolve():continue
        rp=Path(previous)/'batch_receipt.json'
        if not rp.is_file():continue
        state=json.loads(rp.read_text())
        row=next((r for r in state.get('companies',[]) if r['company']==company),None)
        if not row or row.get('status') in ('complete','zero_rows','needs_review','skipped'):continue
        if row.get('status')=='acquired' or row.get('export_pending'):
            raise FlowError('previous-run-unresolved','Resume previous run before new collection: '+previous)
        for p in (Path(row['outdir'])/'operator').glob('*/workflow.json'):
            journal=json.loads(p.read_text())
            if journal.get('exportPending') or journal.get('downloadPending'):
                raise FlowError('previous-run-unresolved','Resume previous run before new collection: '+previous)

def plan(company,base,path,run_dir):
    """Freeze this company's range; keep the initial start even if its first run fails."""
    path=Path(path).resolve()
    with lock(path.parent):
        data=read(path);entry=data['companies'].get(company)
        if entry:unresolved_run(entry,company,run_dir)
        if date.fromisoformat(base['end'])>=date.fromisoformat(base['today']):raise FlowError('today-excluded-from-range')
        if not entry:
            entry={'initial_start':base['start'],'covered_through':None,'next_start':base['start'],
                   'last_completed_on':None,'last_completed_at':None,'last_run_date':None,'completions':[],'planned_runs':{}}
            data['companies'][company]=entry
        first=base['start'] if base['mode']=='manual' else entry['next_start']
        if first>base['end']:
            return {**base,'ok':False,'reason':'already_covered','covered_through':entry['covered_through']}
        dates={**base,'start':first,'days':(date.fromisoformat(base['end'])-date.fromisoformat(first)).days+1,
               'mode':base['mode'] if base['mode']=='manual' else 'catchup' if first!=base['start'] else base['mode']}
        entry['planned_runs'][str(Path(run_dir).resolve())]={'start':first,'end':base['end'],'planned_on':base['today']}
        save(path,data);return dates

def eligible(receipt):
    if receipt.get('status') not in ('complete','zero_rows'):return False
    count=receipt.get('row_count')
    from ds_common import source_count_matches
    return (type(count) is int and count>=0 and receipt.get('attribution_verified') is True
            and source_count_matches(receipt)
            and not receipt.get('warnings') and not receipt.get('mismatch')
            and (receipt['status']!='zero_rows' or count==0))

def record(path,receipt_path,company,dates,mapping_hash):
    receipt_path=Path(receipt_path).resolve();receipt=json.loads(receipt_path.read_text())
    if not eligible(receipt):return {'recorded':False,'reason':'result-not-verified-complete'}
    source=Path(receipt['src_file'])
    if not source.is_file() or not receipt_valid(receipt,source,company,dates,mapping_hash):raise FlowError('progress-receipt-invalid')
    if date.fromisoformat(dates['end'])>=date.fromisoformat(dates['today']):raise FlowError('today-excluded-from-range')
    path=Path(path).resolve()
    with lock(path.parent):
        data=read(path);entry=data['companies'].get(company['company'])
        if not entry:raise FlowError('progress-plan-missing')
        if any(r.get('state')=='collection-ready'for r in entry.get('collection_reservations',{}).values()):raise FlowError('staged-delivery-confirmation-required')
        digest=sha256(receipt_path)
        event={'start':dates['start'],'end':dates['end'],'run_date':dates['today'],
               'completed_at':receipt['generated_at'],'completed_on':receipt['generated_at'][:10],
               'receipt':str(receipt_path),'receipt_sha256':digest,'src_sha256':receipt['src_sha256']}
        if not any(c['receipt_sha256']==digest and c['receipt']==str(receipt_path) for c in entry['completions']):
            entry['completions'].append(event)
            # Move the cursor only over a continuous interval from the original anchor.
            cursor=date.fromisoformat(entry['initial_start'])
            for item in sorted(entry['completions'],key=lambda c:(c['start'],c['end'])):
                first,last=date.fromisoformat(item['start']),date.fromisoformat(item['end'])
                if first>cursor:break
                if last>=cursor:cursor=last+timedelta(days=1)
            entry['next_start']=cursor.isoformat()
            entry['covered_through']=(cursor-timedelta(days=1)).isoformat() if cursor>date.fromisoformat(entry['initial_start']) else None
            # Most recent real completion, distinct from the last covered data date.
            latest=max(entry['completions'],key=lambda c:c['completed_at'])
            for key in ('completed_at','completed_on'):entry['last_'+key]=latest[key]
            entry['last_run_date']=latest['run_date'];save(path,data)
        return {'recorded':True,'covered_through':entry['covered_through'],'next_start':entry['next_start'],
                'last_completed_on':entry['last_completed_on'],'receipt_sha256':digest}


def reserve_collection(path,receipt_path,company,dates,mapping_hash,run_dir):
    """Opt-in staged collection, no completed coverage or cursor mutation."""
    receipt_path=Path(receipt_path).resolve();receipt=json.loads(receipt_path.read_bytes())
    if not eligible(receipt):raise FlowError('reservation-receipt-not-ready')
    source=Path(receipt['src_file'])
    if not receipt_valid(receipt,source,company,dates,mapping_hash):raise FlowError('reservation-receipt-invalid')
    if date.fromisoformat(dates['end'])>=date.fromisoformat(dates['today']):raise FlowError('today-excluded-from-range')
    run_dir=Path(run_dir).resolve()
    if run_dir not in receipt_path.parents:raise FlowError('reservation-receipt-outside-run')
    import hashlib
    key=hashlib.sha256((str(run_dir)+'\0'+company['company']).encode()).hexdigest()
    reservation={'kind':'daily-collection-reservation-v1','state':'collection-ready','run_dir':str(run_dir),'company':company['company'],'start':dates['start'],'end':dates['end'],'receipt':{'path':str(receipt_path),'sha256':sha256(receipt_path)},'source':{'path':str(source.resolve()),'sha256':sha256(source)},'mapping_sha256':mapping_hash}
    path=Path(path).resolve()
    with lock(path.parent):
        data=read(path);entry=data['companies'].get(company['company'])
        if not entry or str(run_dir)not in entry.get('planned_runs',{}):raise FlowError('reservation-original-plan-required')
        plan=entry['planned_runs'][str(run_dir)]
        if (plan['start'],plan['end'])!=(dates['start'],dates['end'])or entry['next_start']!=dates['start']:raise FlowError('reservation-plan-or-cursor-changed')
        existing=entry.setdefault('collection_reservations',{})
        for k,v in existing.items():
            if k!=key and v.get('state')=='collection-ready':raise FlowError('collection-reservation-pending-delivery')
        if key in existing:
            if existing[key]!=reservation:
                # B94: a supervised re-collection rewrites the receipt/source
                # bytes, so the reservation slot for the same run+company+dates
                # must be rebound to the freshly verified artifact. Rebinding is
                # allowed only while the existing reservation is undelivered
                # ('collection-ready'); any consumed state still refuses, and
                # the plan/cursor guards above keep bounding the slot.
                if existing[key].get('state')!='collection-ready':raise FlowError('reservation-binding-conflict')
                existing[key]=reservation;save(path,data)
        else:existing[key]=reservation;save(path,data)
    return {'reservation_key':key,'reservation':reservation,'cursor_advanced':False,'delivery_complete':False}


def commit_collection_value(data,ready_ref,client_proof_ref,delivery_folder,*,sender_directory,completed_at):
    """Pure deterministic staged coverage value, gated by all three real clients.
    Never writes progress. The fixed delivery worker must CAS exact before/after
    under its original scheduler/resource/workflow locks; no arbitrary setter.
    """
    import copy,hashlib
    import notification_backlog as backlog,unified_delivery as delivery
    from datetime import datetime
    plan=delivery.verify_client_proof(client_proof_ref,delivery_folder,sender_directory=sender_directory)
    import daily_orchestration
    facts=daily_orchestration.verified_collection_ready_facts(plan['ready_reports']['daily-comment-stats'])
    if facts['report']['ready']!=ready_ref:raise FlowError('staged-progress-original-ready-required')
    ready=backlog.collection_ready_facts(ready_ref)
    return _commit_collection_facts(data,ready,client_proof_ref,completed_at=completed_at)

def _commit_collection_facts(data,ready,client_proof_ref,*,completed_at):
    import copy,hashlib
    import notification_backlog as backlog
    from datetime import datetime
    before=backlog.read_ref(ready['progress_before'])
    if data!=before:raise FlowError('staged-progress-original-before-required')
    stamp=datetime.fromisoformat(completed_at)
    if stamp.utcoffset() is None:raise FlowError('staged-progress-aware-time-required')
    mapping,_=backlog.batch_mapping(backlog.read_ref(ready['batch']));batch=backlog.read_ref(ready['batch']);out=copy.deepcopy(data)
    for company in mapping:
        name=company['company'];row=next(x for x in ready['companies']if x['company']==name);receipt=backlog.read_ref(row['receipt']);batch_row=next(x for x in batch['companies']if x['company']==name);dates=batch_row['date_range']
        if {k:dates[k]for k in('start','end')}!=receipt['date_range']or dates.get('today')!=batch['requested_date_range']['today']:raise FlowError('staged-progress-original-batch-dates')
        run_dir=str(Path(batch['run_dir']).resolve());key=hashlib.sha256((run_dir+'\0'+name).encode()).hexdigest();entry=out['companies'][name]
        expected={'kind':'daily-collection-reservation-v1','state':'collection-ready','run_dir':run_dir,'company':name,'start':dates['start'],'end':dates['end'],'receipt':row['receipt'],'source':row['source'],'mapping_sha256':batch['mapping_sha256']}
        if entry.get('collection_reservations',{}).get(key)!=expected or entry['next_start']!=dates['start']:raise FlowError('staged-progress-reservation-conflict')
        if not eligible(receipt)or not receipt_valid(receipt,Path(receipt['src_file']),{**company,'groupid':row['groupid']},dates,batch['mapping_sha256']):raise FlowError('staged-progress-receipt-invalid')
        if stamp<datetime.fromisoformat(receipt['generated_at']):raise FlowError('staged-progress-before-collection')
        event={'start':dates['start'],'end':dates['end'],'run_date':dates['today'],'completed_at':receipt['generated_at'],'completed_on':receipt['generated_at'][:10],'receipt':row['receipt']['path'],'receipt_sha256':row['receipt']['sha256'],'src_sha256':receipt['src_sha256']}
        if any(c['receipt_sha256']==event['receipt_sha256']and c['receipt']==event['receipt']for c in entry['completions']):raise FlowError('staged-progress-already-recorded')
        entry['completions'].append(event);cursor=date.fromisoformat(entry['initial_start'])
        for item in sorted(entry['completions'],key=lambda c:(c['start'],c['end'])):
            first,last=date.fromisoformat(item['start']),date.fromisoformat(item['end'])
            if first>cursor:break
            if last>=cursor:cursor=last+timedelta(days=1)
        entry['next_start']=cursor.isoformat();entry['covered_through']=(cursor-timedelta(days=1)).isoformat()if cursor>date.fromisoformat(entry['initial_start'])else None
        latest=max(entry['completions'],key=lambda c:c['completed_at'])
        for field in('completed_at','completed_on'):entry['last_'+field]=latest[field]
        entry['last_run_date']=latest['run_date'];entry['collection_reservations'][key]={**expected,'state':'client-confirmed','delivery_proof':client_proof_ref,'delivery_completed_at':completed_at}
    out['updated_at']=completed_at
    return out
