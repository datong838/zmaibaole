"""Pure completed daily business replay. No Clock/live load/prepare/write entry.
Original boot is historical data. This returns no live/fresh/30s authority.
Readonly order derivation retains the reviewed notification algorithm; ordinary
formal keys only, not a substitute for benchmark/fresh verification.
"""
import hashlib,json,sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/daily-comment-stats/scripts'))
import prepare_notifications as pn
from ds_common import MAPPING,load_map,receipt_valid,sha256
import daily_execution_launcher as parent
import execution_timing as timing
need=parent.need

def reference(path):return {'path':str(Path(path).resolve()),'sha256':sha256(path)}
def read_ref(r):return timing.pinned(r)

def derive_orders(receipt_path,company):
    r=json.loads(Path(receipt_path).read_text());dates=r['date_range'];source=Path(r['src_file'])
    need(r.get('flow')=='daily-comment-stats' and r.get('status') in ('complete','zero_rows') and (r.get('quality_blocked') is False if r.get('status')=='complete' else r.get('quality_blocked') is True and r.get('zero_rows') is True and type(r.get('row_count')) is int and r['row_count']==0 and not r.get('artifacts')) and r.get('attribution_verified') is True and r.get('mismatch') is False and not r.get('warnings') and r.get('row_count')==r.get('page_filtered') and receipt_valid(r,source,company,dates,sha256(MAPPING)),'outbox-receipt-unverified')
    if r['status']=='zero_rows':return r,[],None
    mp=Path(receipt_path).parent/'test-notifications/orders.json'
    # Verification cannot create a missing manifest or acquire a write lock.
    # Retain prepare's positive-row/known-brand conditions; scope, source,
    # artifact, payload, text and argv checks below still all run.
    need(r.get('row_count',0)>0 and r['company'] in pn.BRANDS,'receipt-or-source-unverified')
    manifest=json.loads(mp.read_text())
    need(manifest.get('source_receipt')==str(Path(receipt_path).resolve()) and manifest.get('receipt_sha256')==sha256(receipt_path) and manifest.get('company')==company['company'] and manifest.get('date_range')==dates and manifest.get('test_target')==pn.TARGET,'notification-manifest-scope-conflict')
    artifacts=r['artifacts'];detail=[a for a in artifacts if Path(a['path']).name.startswith('评价明细_')];stats=[a for a in artifacts if Path(a['path']).name.startswith('评价统计_')]
    need(len(detail)==len(stats)==1,'notification-artifacts-ambiguous')
    text=pn.render(pn.build(source,r['company'],dates['start'],dates['end'],stats[0]['path']),pn.BRANDS[r['company']],company['wecom_group'],'test');texts=pn.chunks(text)
    expected=[('detail',Path(detail[0]['path']).resolve(),'file'),('stats',Path(stats[0]['path']).resolve(),'file')]
    expected += [('text-'+str(i),mp.parent/('text-%03d.txt'%i),'text') for i in range(1,len(texts)+1)]
    need([o.get('part') for o in manifest['orders']]==[x[0] for x in expected],'notification-parts-conflict')
    result=[]
    for old,(part,path,kind) in zip(manifest['orders'],expected):
        need(old.get('payload')==str(path) and old.get('sha256')==sha256(path),'notification-payload-conflict')
        need(not Path(receipt_path).is_relative_to(PROJECT/'work/benchmarks'),'historical-formal-daily-only');key='daily-comments:'+r['company']+':'+dates['start']+':'+dates['end']+':'+part
        argv=old.get('prepare_argv',[]);flag='--file' if kind=='file' else '--text-file'
        need(len(argv)==13 and str(Path(argv[1]).resolve())==str((PROJECT/'skills/wecom-messenger/scripts/messenger.py').resolve()) and argv[2:]==['prepare','--key',key,'--kind','group','--target',pn.TARGET,'--scope','test',flag,str(path)],'notification-prepare-argv-conflict')
        if kind=='text':
            i=int(part.split('-')[1]);want=('【评价日报 %d/%d】\n'%(i,len(texts)) if len(texts)>1 else '')+texts[i-1];need(path.read_text()==want,'notification-text-not-derived-from-source')
        result.append({'company':company['company'],'seq':company['seq'],'dates':dates,'part':part,'payload':str(path),'sha256':old['sha256'],'type':kind,'key':key})
    return r,result,mp

def validate_queue_readonly(path):
    path=Path(path);need(path.with_suffix('.sha256').read_text().strip()==sha256(path),'historical-outbox-manifest-changed');q=json.loads(path.read_text());need(q.get('version')==1 and q.get('kind')=='daily-test-notification-outbox' and q.get('target')==pn.TARGET,'historical-outbox-schema')
    for r in q['references']:
        read_ref(r);copy=path.parent/'inputs'/(r['sha256']+'.json');need(copy.is_file() and not copy.is_symlink() and sha256(copy)==r['sha256'],'historical-outbox-snapshot')
    batch=read_ref(q['batch']);mapping=load_map();need(batch.get('flow')=='daily-comment-stats' and batch.get('mode')=='agent-live' and batch.get('status')=='complete' and batch.get('mapping_sha256')==sha256(MAPPING) and batch.get('failed',0)==batch.get('needs_review',0)==0,'historical-complete-live-batch')
    need([r['company'] for r in batch['companies']]==[r['company'] for r in mapping] and [r['seq'] for r in batch['companies']]==[r['seq'] for r in mapping] and len(q['scopes'])==len(mapping),'historical-complete-companies')
    need(not batch.get('roundtrip',{}).get('required') or batch['roundtrip'].get('verified') is True,'historical-company-return')
    expected=[]
    for row,company,scope in zip(batch['companies'],mapping,q['scopes']):
        if row.get('status')=='skipped':
            # This original helper only reads immutable progress/receipts.
            import notification_backlog as backlog
            need(scope==backlog.skipped_scope(batch,row,company,scope['coverage_evidence']['progress_snapshot']),'historical-skipped-scope');continue
        r,orders,_=derive_orders(Path(row.get('receipt') or Path(row['outdir'])/'receipt.json'),company);expected.extend(orders)
    need(expected==q['items'],'historical-outbox-orders-not-derived');return q

def validate_clients(receipt,s,wall_end):
    timing.binding(receipt,s,'workflow-client-confirmation-v1');keys=timing.expected_keys(s)
    if s['scope'].get('delivery_contract')==timing.DYNAMIC_DELIVERY:need(receipt.get('delivery_manifest_sha256')==s['delivery']['manifest_sha256'],'historical-delivery-hash')
    refs=receipt.get('client_jobs');need(isinstance(refs,list) and refs and len({r.get('path') for r in refs})==len(refs),'historical-all-client-jobs');actual=[];earliest=timing.parse_time(s['wall_started_at']).replace(microsecond=0)
    for r in refs:
        job=read_ref(r);payload=job.get('job',{});need(job.get('status')=='complete' and job.get('sent') is True and job.get('ui_confirmed') is True and not job.get('error') and payload.get('target')==timing.TARGET and payload.get('kind')=='group' and payload.get('scope')=='test','historical-client-confirmation')
        need(hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==job.get('fingerprint'),'historical-client-payload')
        need(any(e.get('stage')=='ui-confirmed' for e in job.get('events',[])),'historical-client-event');created=timing.parse_time(job.get('created_at'));completed=timing.parse_time(job.get('completed_at'));need(created<=completed<=wall_end,'historical-client-time')
        if s['origin']=='fresh':need(created>=earliest,'historical-old-client-reused')
        need(isinstance(payload.get('key'),str) and Path(r['path']).resolve()==timing.sender_path(payload['key']),'historical-canonical-client')
        if s['scope'].get('delivery_contract')==timing.DYNAMIC_DELIVERY:
            match=[v for v in s['delivery']['orders'] if v['key']==payload['key']];need(len(match)==1 and all(payload.get(k)==v for k,v in match[0]['sender_payload'].items()),'historical-client-delivery-payload')
        actual.append(payload['key'])
    need(len(actual)==len(set(actual)) and sorted(actual)==sorted(keys),'historical-full-client-key-set');return refs

def completed_inner(path,parent_state):
    s=json.loads(Path(path).read_bytes());need(s.get('kind')==timing.KIND and s.get('status')=='complete' and s.get('monotonic_clock')==timing.MONOTONIC_CLOCK and s.get('boot_identity')==parent_state['boot_identity'],'historical-inner-complete-sameboot')
    read_ref(s['work_order']);timing.scope_check(s['scope']);need(timing.digest(s['scope'])==s['scope_sha256'],'historical-inner-scope')
    need(timing.finite(s.get('start_monotonic')) and timing.finite(s.get('end_monotonic')) and parent_state['start_monotonic']<=s['start_monotonic']<=s['end_monotonic']<=parent_state['end_monotonic'],'historical-inner-time')
    if s['scope'].get('delivery_contract')==timing.DYNAMIC_DELIVERY:
        delivery=s['delivery'];need(delivery.get('contract')==timing.DYNAMIC_DELIVERY and delivery.get('status')=='sealed','historical-inner-delivery-not-sealed');orders=timing.delivery_orders(delivery['manifest'],s);need(orders==delivery['orders'] and delivery['keys']==[v['key'] for v in orders] and delivery['manifest_sha256']==delivery['manifest']['sha256'],'historical-inner-delivery-changed')
    return s

def verify_completed_archive(parent_ref):
    """No caller-selected boot/end and no Clock adapter: bounds are frozen facts."""
    before=timing.checked_bytes(parent_ref);s=json.loads(before);need(s.get('kind')==parent.KIND and s.get('status')=='complete' and Path(parent_ref['path'])==parent.location(s['order'])/'state.json','historical-daily-complete-canonical')
    need(s.get('clock_contract')==timing.MONOTONIC_CLOCK and timing.finite(s.get('start_monotonic')) and timing.finite(s.get('end_monotonic')) and s['start_monotonic']<=s['end_monotonic'],'historical-daily-fixed-end')
    origin=read_ref(s['origin_ref']);need(origin=={k:s[k] for k in parent.ORIGIN_FIELDS},'historical-daily-origin');order=parent.dispatch.validate(s['order'],s['archive_root']);need(s['scope_sha256']==order['scope_sha256'] and s['origin']==order['origin'],'historical-daily-scope')
    for r in s['code_refs']:parent.historical_code_bytes(r)
    final=read_ref(s['completion_ref']);need(final=={'kind':'daily-parent-completion-v1','run_id':s['run_id'],'order':s['order'],'origin_ref':s['origin_ref'],**{k:s[k] for k in parent.FINAL_FIELDS}},'historical-daily-final-record')
    previous=s['start_monotonic'];folder=parent.location(s['order']);need(s['calls'],'historical-no-children')
    for i,call in enumerate(s['calls']):
        need(call['index']==i and call['verb'] in parent.VERBS and call['state'] in ('returned','failed') and call['argv']==parent.argv_for(s['order'],s['archive_root'],call['verb'],s['mode'],call.get('tab_id'),call.get('steps',25)),'historical-child-original-argv')
        need(timing.finite(call['launch_monotonic']) and previous<=call['launch_monotonic']<=s['end_monotonic'],'historical-child-sequence');need(read_ref(call['launch'])=={k:v for k,v in call.items() if k not in ('launch','state','result')},'historical-child-launch')
        r=call['result'];ex=read_ref(r);need(Path(r['path'])==folder/'children'/('%04d-result.json'%i) and ex.get('kind')=='daily-child-exit-v1' and ex.get('launch')==call['launch'] and ex.get('run_id')==s['run_id'] and ex.get('order')==s['order'] and ex.get('argv')==call['argv'] and type(ex.get('returncode')) is int and (ex['returncode']==0 or parent.zero_init_exception(folder,s,call,ex,historical=True)) and ex.get('boot_identity')==s['boot_identity'] and timing.finite(ex.get('exited_monotonic')) and call['launch_monotonic']<=ex['exited_monotonic']<=s['end_monotonic'],'historical-natural-child-exit')
        need(call['state']==('returned' if ex['returncode']==0 else 'failed'),'historical-child-exit-state')
        if ex['returncode']==0:parent.receipt_output(ex,s)
        previous=ex['exited_monotonic']
    need(s['calls'][-1]['verb']=='notify','historical-final-notify')
    root=Path(s['order']['path']).parent.parent/'daily-executions'/Path(s['order']['path']).stem;inner=completed_inner(root/'timing.json',s)
    need(inner['run_id']=='daily-'+Path(s['order']['path']).stem and inner['work_order']==s['order'] and inner['scope_sha256']==s['scope_sha256'] and inner['origin']==s['origin'] and inner['mode']==s['mode'] and timing.parse_time(s['wall_started_at'])<=timing.parse_time(inner['wall_started_at'])<=timing.parse_time(inner['wall_ended_at'])<=timing.parse_time(s['wall_ended_at']),'historical-inner-binding')
    import daily_timed_run as role
    _,state=role.checked(root,s['order'],s['archive_root']);need(state['phase']=='complete' and inner['outcome'] in ('client-confirmed','no-data-complete'),'historical-business-complete')
    run_dir=Path(state['run_dir']);bp=run_dir/'batch_receipt.json';batch=role.check_batch(json.loads(bp.read_bytes()),order,run_dir);need(batch['status']=='complete','historical-source-batch')
    queues=list((root/'outbox').glob('*/outbox.json'));need(len(queues)==1,'historical-one-outbox');queue=queues[0];q=validate_queue_readonly(queue);need(q['batch']==reference(bp) and Path(q['messenger_directory']).resolve()==timing.SENDER_DIRECTORY.resolve(),'historical-outbox-source-binding')
    receipt=read_ref(inner['completion'])
    if inner['outcome']=='client-confirmed':
        validate_clients(receipt,inner,timing.parse_time(inner['wall_ended_at']));need(sorted(inner['delivery']['keys'])==sorted(v['key'] for v in q['items']),'historical-complete-key-set')
        if s['origin']=='fresh':need(inner['delivery'].get('fresh_canonical_absence_checked') is True,'historical-initial-client-absence')
    else:timing.no_data(receipt,inner);need(not q['items'],'historical-zero-outbox-not-empty')
    proof={'outcome':inner['outcome'],'inner_timing':reference(root/'timing.json'),'role_state':reference(root/'state.json'),'batch':reference(bp),'outbox':reference(queue),'completion':inner['completion'],'all_expected_client_confirmed':inner['outcome']=='client-confirmed'}
    if 'zero_init_recovery' in s['completion_proof']:
        ref=s['completion_proof']['zero_init_recovery'];need(Path(ref['path'])==folder/'zero-init-recovery.json','historical-zero-init-canonical');read_ref(ref);proof['zero_init_recovery']=ref
    need(proof==s['completion_proof'] and timing.checked_bytes(parent_ref)==before,'historical-original-completion-proof-changed')
    return {'kind':'historical-completed-daily-business-verified-v1','parent':s,'order':order,'proof':proof,'live_input_authority':False,'fresh_acceptance_authority':False,'performance_authority':False,'historical_boot':s['boot_identity']}
