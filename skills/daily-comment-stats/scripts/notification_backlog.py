#!/usr/bin/env python3
"""Durable test-only notification outbox. plan/status are offline; run owns UI.
No processing-date writes, automatic resume, new send keys or acceptance by assertion.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
import prepare_notifications as pn
from ds_common import PROJECT,MAPPING,load_map,receipt_valid,sha256,atomic_json,lock
sys.path.insert(0,str(PROJECT/'skills/wecom-messenger/scripts'))
spec=importlib.util.spec_from_file_location('daily_outbox_messenger',PROJECT/'skills/wecom-messenger/scripts/messenger.py');messenger=importlib.util.module_from_spec(spec);spec.loader.exec_module(messenger)
OUTBOX=PROJECT/'runtime/daily-comment-stats/notification-outbox'
def need(ok,code):
    if not ok:raise ValueError(code)
def digest_value(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def reference(path):return {'path':str(Path(path).resolve()),'sha256':sha256(path)}
def read_ref(ref):
    p=Path(ref['path']);need(p.is_absolute() and p.is_file() and not p.is_symlink() and sha256(p)==ref['sha256'],'outbox-input-changed');return json.loads(p.read_text())
def job_for(item,directory):
    if item.get('part')=='zero-result':_zero_notice_module()
    key=item['key'];job={'version':messenger.VERSION,'key':key,'kind':'group','target':pn.TARGET,'scope':'test','type':item['type']}
    p=Path(item['payload']);need(p.is_absolute() and p.is_file() and not p.is_symlink() and sha256(p)==item['sha256'],'outbox-payload-changed')
    if item['type']=='text':job['text']=p.read_text()
    else:job.update(file=str(p),file_sha256=item['sha256'],file_name=p.name)
    messenger.validate(job,json.loads(messenger.POLICY.read_text()))
    return job,Path(directory)/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json')
def derive_orders(receipt_path,company,*,zero_notice=False):
    r=json.loads(Path(receipt_path).read_text());dates=r['date_range'];source=Path(r['src_file'])
    need(r.get('flow')=='daily-comment-stats' and r.get('status') in ('complete','zero_rows') and (r.get('quality_blocked') is False if r.get('status')=='complete' else r.get('quality_blocked') is True and r.get('zero_rows') is True and type(r.get('row_count')) is int and r['row_count']==0 and not r.get('artifacts')) and r.get('attribution_verified') is True and r.get('mismatch') is False and not r.get('warnings') and r.get('row_count')==r.get('page_filtered') and receipt_valid(r,source,company,dates,sha256(MAPPING)),'outbox-receipt-unverified')
    if r['status']=='zero_rows':
        if not zero_notice:return r,[],None  # Existing immutable outboxes stay legacy.
        sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
        zn=_zero_notice_module()
        from datetime import date,timedelta
        end=(date.fromisoformat(dates['end'])+timedelta(days=1)).isoformat();folder=Path(receipt_path).resolve().parent/'test-notifications'
        native=zn.prepare(folder,'daily-comment-stats',r['company'],dates['start'],end,reference(receipt_path),[reference(receipt_path)],module_ref=_ZERO_NOTICE_MODULE)
        argv=[sys.executable,str(PROJECT/'skills/wecom-messenger/scripts/messenger.py'),'prepare','--key',native['key'],'--kind','group','--target',pn.TARGET,'--scope','test','--text-file',native['text_file']]
        item={'company':company['company'],'seq':company['seq'],'dates':dates,'part':'zero-result','payload':native['text_file'],'sha256':native['text_sha256'],'type':'text','key':native['key']}
        manifest={'workflow':'daily-comment-stats','company':r['company'],'date_range':dates,'test_target':pn.TARGET,'zero_module_ref':_ZERO_NOTICE_MODULE,'orders':[{'part':'zero-result','payload':native['text_file'],'sha256':native['text_sha256'],'prepare_argv':argv}]};mp=folder/'orders.json';zn.immutable(mp,zn.encode(manifest));return r,[item],mp
    manifest=pn.prepare(receipt_path);mp=Path(receipt_path).parent/'test-notifications/orders.json'
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
        key='daily-comments:'+r['company']+':'+dates['start']+':'+dates['end']+':'+part
        argv=old.get('prepare_argv',[]);flag='--file' if kind=='file' else '--text-file'
        need(len(argv)==13 and str(Path(argv[1]).resolve())==str((PROJECT/'skills/wecom-messenger/scripts/messenger.py').resolve()) and argv[2:]==['prepare','--key',key,'--kind','group','--target',pn.TARGET,'--scope','test',flag,str(path)],'notification-prepare-argv-conflict')
        if kind=='text':
            i=int(part.split('-')[1]);want=('【评价日报 %d/%d】\n'%(i,len(texts)) if len(texts)>1 else '')+texts[i-1];need(path.read_text()==want,'notification-text-not-derived-from-source')
        result.append({'company':company['company'],'seq':company['seq'],'dates':dates,'part':part,'payload':str(path),'sha256':old['sha256'],'type':kind,'key':key})
    return r,result,mp

def skipped_scope(batch,row,company,progress_ref):
    """Verify an already-covered company from immutable progress and receipt refs.
    Never treat missing company/account/risk skips as completed coverage.
    """
    from datetime import date,timedelta
    from ds_progress import eligible
    dates=row.get('date_range',{});requested=batch.get('requested_date_range',batch.get('date_range',{}))
    need(row.get('status')=='skipped' and row.get('skip_reason')=='already_covered' and dates.get('ok') is False and dates.get('reason')=='already_covered' and dates.get('today')==requested.get('today') and dates.get('end')==requested.get('end'),'outbox-skip-not-already-covered')
    progress=read_ref(progress_ref);need(progress.get('version')==1,'outbox-skip-progress-invalid');entry=progress.get('companies',{}).get(company['company']);need(type(entry) is dict,'outbox-skip-company-missing')
    cursor=date.fromisoformat(entry['initial_start']);end=date.fromisoformat(dates['end']);refs=[]
    for event in sorted(entry.get('completions',[]),key=lambda c:(c['start'],c['end'])):
        first,last=date.fromisoformat(event['start']),date.fromisoformat(event['end'])
        if first>cursor:break
        if last<cursor:continue
        rr={'path':event['receipt'],'sha256':event['receipt_sha256']};r=read_ref(rr);source=Path(r['src_file'])
        need(r.get('company')==company['company'] and eligible(r) and r.get('date_range',{}).get('start')==event['start'] and r.get('date_range',{}).get('end')==event['end'] and receipt_valid(r,source,company,r['date_range'],sha256(MAPPING)),'outbox-skip-receipt-unverified')
        refs.append(rr);cursor=last+timedelta(days=1)
        if cursor>end:break
    need(cursor>end and entry.get('next_start')>dates['end'] and dates.get('covered_through')>=dates['end'],'outbox-skip-coverage-unverified')
    return {'company':company['company'],'seq':company['seq'],'date_range':dates,'zero_rows':False,'already_covered':True,'coverage_evidence':{'progress_snapshot':progress_ref,'receipts':refs}}

def snapshot_progress(batch,directory):
    p=Path(batch.get('progress_file',''));need(p.is_absolute() and p.is_file() and not p.is_symlink(),'outbox-skip-progress-required');raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();path=directory/'inputs'/(digest+'.json');path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'outbox-skip-progress-snapshot-conflict')
    else:
        import os,tempfile
        fd,tmp=tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,path)
            except FileExistsError:need(path.read_bytes()==raw,'outbox-skip-progress-snapshot-conflict')
        finally:os.unlink(tmp)
    return reference(path)


def batch_mapping(batch):
    """Authenticate issued scope, then retain canonical mapping order/sequence."""
    scope=batch.get('dispatch_scope')
    if scope is None:return load_map(),[]
    need(type(scope)is dict and set(scope)=={'work_order','scope_sha256','active_company_policy'},'outbox-dispatch-scope-schema')
    sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
    import daily_dispatch_order as dispatch
    order_ref=scope['work_order'];order=read_ref(order_ref)
    need(order.get('kind')=='daily-dispatch-order-v1'and order.get('workflow')=='daily-comment-stats','outbox-current-dispatch-kind')
    need(scope['scope_sha256']==order['scope_sha256']and scope['active_company_policy']==order.get('active_company_policy')and order.get('production_enabled')is False and order.get('complaint_submission_enabled')is False,'outbox-dispatch-scope-binding')
    requested=batch.get('requested_date_range',batch.get('date_range',{}));need(requested.get('today')==requested.get('end_exclusive')==order['day']and batch.get('date_range',{}).get('today')==order['day'],'outbox-dispatch-day-mapping')
    configured_run=batch.get('mapping_path')==str(Path(batch['run_dir'])/'company-run-mapping.csv')
    if configured_run:
        need(order.get('collection_contract')=='three-flow-collection-ready-v1'and batch.get('delivery_contract')==order['collection_contract'],'outbox-configured-staged-only')
        path=Path(batch['mapping_path'])
        need(path.is_absolute()and path.resolve()==path and not path.is_symlink()and sha256(path)==batch['mapping_sha256'],'outbox-current-run-mapping')
        mapping=load_map(path)
    else:
        need(batch.get('mapping_sha256')==sha256(MAPPING),'outbox-dispatch-day-mapping');mapping=load_map()
    config=read_ref(order['company_config'])['companies'];ranges=order['scope']['company_ranges'];skipped=order['skipped_companies'];selected=ranges+skipped;names=[r['company']for r in selected];by={r['company']:r for r in mapping}
    need(names and len(names)==len(set(names))and len(by)==len(mapping)and set(names)<=set(by),'outbox-dispatch-company-set')
    for row in selected:need(config.get(row['company'],{}).get('groupid')==row['groupid'],'outbox-dispatch-company-gid')
    filtered=[r for r in mapping if r['company']in names];rows=batch['companies'];need([r['company']for r in rows]==[r['company']for r in filtered]and [r['seq']for r in rows]==[r['seq']for r in filtered],'complete-company-sequence-required')
    from datetime import date,timedelta
    for row in rows:
        issued=next(r for r in selected if r['company']==row['company']);dates=row['date_range'];need(str(row.get('groupid'))==issued['groupid']and dates.get('today')==order['day']and dates.get('end_exclusive')==order['day']and dates.get('end')==(date.fromisoformat(order['day'])-timedelta(days=1)).isoformat(),'outbox-dispatch-row-gid-date')
        if issued in ranges:need(dates.get('start')==issued['start']and issued['end_exclusive']==order['day'],'outbox-dispatch-range')
        else:need(row.get('status')=='skipped'and row.get('skip_reason')=='already_covered','outbox-dispatch-skipped-row')
    refs=[order_ref,order['company_config']]
    if configured_run:refs.append(reference(batch['mapping_path']))
    return filtered,refs

def collection_ready_value(batch_path,progress_ref,company_config_ref,*,original_progress_ref=None):
    """New staged producer: real receipt/XLSX verification, no sender or cursor API.
    Requires unadvanced original progress. Does not fabricate a completion report.
    Caller must opt into a staged collector before source acquisition starts.
    """
    bp=Path(batch_path).resolve();batch_ref=reference(bp);batch=read_ref(batch_ref)
    mapping,scope_refs=batch_mapping(batch)
    run_mapping=Path(batch.get('run_dir',''))/'company-run-mapping.csv'
    configured_run=bool(batch.get('dispatch_scope')and batch.get('mapping_path')==str(run_mapping)and reference(run_mapping)in scope_refs)
    if not configured_run:need(company_config_ref['path']==str(PROJECT/'skills/daily-comment-stats/config/companies.json'),'ready-company-config-path')
    mapping_hash=batch['mapping_sha256']if configured_run else sha256(MAPPING)
    config=read_ref(company_config_ref)['companies']
    if batch.get('dispatch_scope'):need(company_config_ref in scope_refs,'ready-issued-company-config-required')
    need(batch.get('flow')=='daily-comment-stats'and batch.get('mode')=='agent-live'and batch.get('status')=='complete'and batch.get('failed',0)==0 and batch.get('needs_review',0)==0 and batch.get('mapping_sha256')==mapping_hash,'ready-complete-live-batch-required')
    need(not batch.get('roundtrip',{}).get('required')or batch['roundtrip'].get('verified')is True,'ready-company-return-unverified')
    rows=batch['companies'];need([x['company']for x in rows]==[x['company']for x in mapping]and[x['seq']for x in rows]==[x['seq']for x in mapping],'ready-company-sequence')
    original_progress_ref=original_progress_ref or progress_ref
    need(batch.get('progress_file')==original_progress_ref['path']and original_progress_ref['sha256']==progress_ref['sha256'],'ready-original-progress-binding')
    progress=read_ref(progress_ref);need(progress.get('version')==1,'ready-progress-schema');companies=[];refs=[batch_ref,progress_ref,company_config_ref,*scope_refs]
    for row,company in zip(rows,mapping):
        need(row.get('status')in('complete','zero_rows'),'ready-active-collected-company-required')
        rp=Path(row.get('receipt')or Path(row['outdir'])/'receipt.json').resolve();need(rp.parent==Path(row['outdir']).resolve()and bp.parent in rp.parents,'ready-receipt-path')
        rr=reference(rp);r=read_ref(rr);dates=r['date_range'];source=Path(r['src_file'])
        from ds_common import source_count_matches
        need(r.get('flow')=='daily-comment-stats'and r.get('company')==company['company']and r.get('status')==row['status']and r.get('attribution_verified')is True and r.get('mismatch')is False and not r.get('warnings')and source_count_matches(r)and receipt_valid(r,source,({**company,'groupid':config[company['company']]['groupid']}if r.get('source_kind')=='daily-visible-dom-source-v1'else company),dates,mapping_hash),'ready-receipt-unverified')
        is_dom=r.get('source_kind')=='daily-visible-dom-source-v1'
        if is_dom:
            from ds_common import dom_source_data,dom_original_download,dom_capture_data
            dom_data=dom_source_data(r['dom_source'],{**company,'groupid':config[company['company']]['groupid']},dates,source)
            dom_capture_data(r['dom_capture'],r['dom_source'],batch,row)
            original=dom_original_download(dom_data)
            checkpoints=[c for c in row.get('checkpoints',[])if c.get('stage')=='dom-acquisition-complete']
            need(len(checkpoints)==1 and checkpoints[0]['original_workflow']==original and checkpoints[0]['receipt']==r['dom_source']['receipt'],'ready-dom-original-checkpoint')
            refs.extend([original,r['dom_source']['receipt'],r['dom_capture']])
        need(all(dates[k]==row['date_range'][k]for k in('start','end')),'ready-date-mismatch')
        from datetime import date,timedelta
        end=(date.fromisoformat(dates['end'])+timedelta(days=1)).isoformat();entry=progress['companies'].get(company['company'],{})
        need(entry.get('next_start')==dates['start']and not any(x.get('start')==dates['start']and x.get('end')==dates['end']for x in entry.get('completions',[])),'ready-cursor-already-committed')
        details=[];stats=[]
        for artifact in r.get('artifacts',[]):
            read_ref(artifact)if Path(artifact['path']).suffix=='.json'else need(sha256(artifact['path'])==artifact['sha256'],'ready-artifact-drift')
            if Path(artifact['path']).name.startswith('评价明细_'):details.append(artifact)
            if Path(artifact['path']).name.startswith('评价统计_'):stats.append(artifact)
        if r['status']=='complete':need(len(details)==len(stats)==1 and r.get('quality_blocked')is False,'ready-review-artifacts')
        else:need(r.get('zero_rows')is True and r.get('row_count')==0 and r.get('quality_blocked')is True and not r.get('artifacts'),'ready-zero-receipt')
        if is_dom:
            from ds_workbooks import dom_report_facts
            data=dom_report_facts(dom_data,source)
        else:data=pn.build(source,company['company'],dates['start'],dates['end'],stats[0]['path'])if stats else None
        companies.append({'company':company['company'],'groupid':config[company['company']]['groupid'],'start':dates['start'],'end_exclusive':end,'receipt':rr,'source':reference(source),'detail':details,'statistics':stats,'review_facts':data,'row_count':r['row_count']})
        if is_dom:companies[-1].update(source_kind=r['source_kind'],dom_source=r['dom_source'],dom_capture=r['dom_capture'],dom_counts=r['dom_counts'],download_verified=False,source_is_authoritative_export=False)
        refs.extend([rr,reference(source),*[{'path':a['path'],'sha256':a['sha256']}for a in r.get('artifacts',[])]])
    value={'kind':'daily-collection-ready-v1','workflow':'daily-comment-stats','batch':batch_ref,'progress_before':progress_ref,'original_progress':original_progress_ref,'company_config':company_config_ref,'companies':companies,'references':refs,'producer':reference(Path(__file__)),'collection_ready':True,'delivery_complete':False,'cursor_advanced':False,'sender_invoked':False,'sender_target':pn.TARGET}
    return value

def prepare_collection_ready(batch_path,out,progress_ref,company_config_ref):
    # Initial seal consumes the actual canonical progress, then archives those
    # exact before bytes. Later typed completion may advance canonical progress.
    value=collection_ready_value(batch_path,progress_ref,company_config_ref);bp=Path(batch_path).resolve()
    need(str(Path(progress_ref['path']).resolve())==progress_ref['path'],'ready-progress-canonical')
    out=Path(out).resolve();need(out!=bp and bp not in out.parents,'ready-output-path')
    with lock(out.parent):
        raw=Path(progress_ref['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==progress_ref['sha256'],'ready-progress-changed-before-archive')
        snapshot=out.parent/'inputs'/(progress_ref['sha256']+'.json');snapshot.parent.mkdir(exist_ok=True)
        if snapshot.exists():need(snapshot.read_bytes()==raw,'ready-progress-archive-conflict')
        else:
            with snapshot.open('xb')as file:file.write(raw);file.flush();__import__('os').fsync(file.fileno())
        value=collection_ready_value(batch_path,reference(snapshot),company_config_ref,original_progress_ref=progress_ref);refs=value['references']
        for r in refs:need(sha256(r['path'])==r['sha256'],'ready-input-changed-before-seal')
        if out.exists():need(read_ref(reference(out))==value,'ready-existing-conflict')
        else:atomic_json(out,value)
    return reference(out)

def collection_ready_facts(reference_value):
    value=read_ref(reference_value)
    need(value['progress_before']['path']==str(Path(reference_value['path']).parent/'inputs'/(value['original_progress']['sha256']+'.json')),'ready-progress-archive-path')
    need(value==collection_ready_value(value['batch']['path'],value['progress_before'],value['company_config'],original_progress_ref=value['original_progress']),'ready-not-derived')
    return value

def verify_collection_ready(reference_value):
    value=collection_ready_facts(reference_value)
    need(sha256(value['original_progress']['path'])==value['original_progress']['sha256'],'ready-live-progress-drift')
    return value

def prepare_batch(batch_path,outbox=OUTBOX,messenger_dir=messenger.RUNTIME,expected_sha=None):
    bp=Path(batch_path).resolve();batch_ref=reference(bp)
    if expected_sha:need(batch_ref['sha256']==expected_sha,'explicit-batch-hash-mismatch')
    batch=json.loads(bp.read_text());mapping,scope_refs=batch_mapping(batch)
    need(not batch.get('delivery_contract'),'staged-batch-requires-unified-delivery')
    need(batch.get('flow')=='daily-comment-stats' and batch.get('mode')=='agent-live' and batch.get('status')=='complete' and batch.get('failed',0)==0 and batch.get('needs_review',0)==0 and batch.get('mapping_sha256')==sha256(MAPPING),'complete-live-batch-required')
    companies=batch.get('companies',[]);need([r['company'] for r in companies]==[r['company'] for r in mapping] and [r['seq'] for r in companies]==[r['seq'] for r in mapping],'complete-company-sequence-required')
    need(not batch.get('roundtrip',{}).get('required') or batch['roundtrip'].get('verified') is True,'batch-company-return-unverified')
    directory=Path(outbox).resolve()/hashlib.sha256(str(bp).encode()).hexdigest()[:24]
    existing=directory/'outbox.json'
    if existing.exists() and existing.with_suffix('.sha256').exists():
        q=validate_queue(existing);need(q['batch']==batch_ref,'existing-outbox-binding-conflict');return existing
    refs=[batch_ref,*scope_refs];items=[];scopes=[]
    for row,company in zip(companies,mapping):
        if row.get('status')=='skipped':
            scope=skipped_scope(batch,row,company,snapshot_progress(batch,directory));scopes.append(scope);refs.extend([scope['coverage_evidence']['progress_snapshot']]+scope['coverage_evidence']['receipts']);continue
        need(row.get('status') in ('complete','zero_rows'),'company-processing-incomplete')
        receipt_path=Path(row.get('receipt') or Path(row['outdir'])/'receipt.json').resolve();need(receipt_path.parent==Path(row['outdir']).resolve() and bp.parent in receipt_path.parents,'receipt-outside-complete-batch')
        rr=reference(receipt_path);r,orders,mp=derive_orders(receipt_path,company,zero_notice=True);need(r['company']==row['company'],'company-receipt-conflict')
        if row.get('date_range'):need(all(r['date_range'][k]==row['date_range'][k] for k in ('start','end')),'company-date-conflict')
        refs.append(rr)
        if mp:refs.append(reference(mp))
        items.extend(orders);scopes.append({'company':r['company'],'seq':company['seq'],'date_range':r['date_range'],'zero_rows':r['status']=='zero_rows'})
    queue={'zero_result_contract':'notify-confirmed-zero-v1','zero_module_ref':_ZERO_NOTICE_MODULE,'version':1,'kind':'daily-test-notification-outbox','batch':batch_ref,'references':refs,'scopes':scopes,'items':items,'messenger_directory':str(Path(messenger_dir).resolve()),'target':pn.TARGET}
    directory=Path(outbox).resolve()/hashlib.sha256(str(bp).encode()).hexdigest()[:24];path=directory/'outbox.json'
    with lock(directory):
        if path.exists():need(json.loads(path.read_text())==queue,'existing-outbox-binding-conflict')
        else:
            snapshots=[]
            for r in refs:
                data=Path(r['path']).read_bytes();need(hashlib.sha256(data).hexdigest()==r['sha256'],'outbox-input-changed');snapshot=directory/'inputs'/(r['sha256']+'.json');snapshot.parent.mkdir(exist_ok=True)
                if not snapshot.exists():snapshot.write_bytes(data)
                snapshots.append(snapshot)
            atomic_json(path,queue)
    checksum=path.with_suffix('.sha256')
    if checksum.exists():need(checksum.read_text().strip()==sha256(path),'outbox-manifest-changed')
    else:checksum.write_text(sha256(path)+'\n')
    validate_queue(path);return path

def validate_queue(path):
    path=Path(path);need(path.with_suffix('.sha256').read_text().strip()==sha256(path),'outbox-manifest-changed')
    q=json.loads(path.read_text());_zero_notice_module(q['zero_module_ref'])if q.get('zero_result_contract')=='notify-confirmed-zero-v1'else None;need(q.get('zero_result_contract')in (None,'notify-confirmed-zero-v1'),'outbox-zero-result-contract');need(q.get('version')==1 and q.get('kind')=='daily-test-notification-outbox' and q.get('target')==pn.TARGET,'outbox-schema-invalid')
    for ref in q['references']:
        read_ref(ref);copy=Path(path).parent/'inputs'/(ref['sha256']+'.json');need(copy.is_file() and sha256(copy)==ref['sha256'],'outbox-snapshot-changed')
    # Re-derive expected stable keys, full messages, artifacts and target. Neither
    # handwritten orders nor an acceptance.json assertion can authorize sending.
    batch=read_ref(q['batch']);mapping,scope_refs=batch_mapping(batch);need(all(r in q['references']for r in scope_refs),'outbox-dispatch-refs-incomplete')
    need(batch.get('flow')=='daily-comment-stats' and batch.get('mode')=='agent-live' and batch.get('status')=='complete' and batch.get('mapping_sha256')==sha256(MAPPING) and batch.get('failed',0)==0 and batch.get('needs_review',0)==0,'complete-live-batch-required')
    need([r['company'] for r in batch['companies']]==[r['company'] for r in mapping] and [r['seq'] for r in batch['companies']]==[r['seq'] for r in mapping] and all(r['status'] in ('complete','zero_rows','skipped') for r in batch['companies']),'complete-company-sequence-required')
    need(not batch.get('roundtrip',{}).get('required') or batch['roundtrip'].get('verified') is True,'batch-company-return-unverified')
    expected=[]
    need(len(q['scopes'])==len(batch['companies']),'outbox-company-scopes-incomplete')
    for row,company,scope in zip(batch['companies'],mapping,q['scopes']):
        if row.get('status')=='skipped':
            need(scope==skipped_scope(batch,row,company,scope['coverage_evidence']['progress_snapshot']),'outbox-skipped-scope-conflict');continue
        r,orders,_=derive_orders(Path(row.get('receipt') or Path(row['outdir'])/'receipt.json'),company,zero_notice=q.get('zero_result_contract')=='notify-confirmed-zero-v1');expected.extend(orders)
    need(expected==q['items'],'outbox-orders-not-derived');return q

def has_intent(s):
    return any(v and any(w in k.lower() for w in ('intent','paste','return','choice')) for k,v in s.items()) or any(any(w in str(e.get('stage','')).lower() for w in ('intent','paste','return','choice')) for e in s.get('events',[]))
def item_status(item,directory):
    job,path=job_for(item,directory);base={'company':item['company'],'part':item['part'],'key':item['key'],'job_path':str(path),'payload_sha256':item['sha256']}
    if not path.exists():return {**base,'action':'prepare','status':'missing'}
    need(not path.is_symlink(),'sender-job-symlink');raw=path.read_bytes();job_hash=hashlib.sha256(raw).hexdigest();s=json.loads(raw);need(s.get('job')==job and s.get('fingerprint')==digest_value(job),'sender-job-binding-conflict')
    messenger.validate(s['job'],json.loads(messenger.POLICY.read_text()));need(sha256(path)==job_hash,'sender-job-changed-during-read');base.update(job_sha256=job_hash,status=s.get('status'),phase=s.get('phase'))
    if s.get('status')=='complete':
        events=s.get('events',[]);need(s.get('phase')=='done' and s.get('sent') is True and s.get('ui_confirmed') is True and type(s.get('pid')) is int and s['pid']>0 and s.get('send_intent_at') and s.get('completed_at') and not s.get('error') and any(e.get('stage')=='send-intent' for e in events) and any(e.get('stage')=='ui-confirmed' and e.get('recipient')==pn.TARGET and e.get('recipient_kind')=='group' for e in events),'sender-completion-evidence-incomplete')
        return {**base,'action':'skip-complete','ui_confirmed':True}
    readonly_owned=s.get('send_intent_at') and any(e.get('stage')=='send-intent' for e in s.get('events',[]))
    if s.get('status')=='unknown':return {**base,'action':'verify-readonly' if s.get('phase')=='verify-sent' and readonly_owned else 'hold-unknown'}
    if s.get('status')=='failed':return {**base,'action':'supervisor-safe-resume' if not has_intent(s) else 'hold-failed-intent'}
    if s.get('status')=='running':
        if s.get('error'):return {**base,'action':'hold-running-error'}
        if has_intent(s):return {**base,'action':'verify-readonly' if s.get('phase')=='verify-sent' and readonly_owned else 'hold-intent'}
        need(s.get('phase') in ('locate','verify','stage','ready'),'unreviewed-running-phase');return {**base,'action':'advance'}
    return {**base,'action':'hold-state'}

def completed_legacy_no_data(batch_path,facts=None):
    """Original closed no-notification contract, never sender acceptance.
    Only canonical original parent replay qualifies; no date/task allowlist.
    """
    bp=Path(batch_path);batch_ref=reference(bp)
    batch=read_ref(batch_ref)
    if batch.get('delivery_contract')or not batch.get('companies')or any(r.get('status')!='zero_rows'for r in batch['companies']):return None
    scope=batch.get('dispatch_scope');order_ref=scope.get('work_order')if type(scope)is dict else None
    if not order_ref:return None
    archive=PROJECT/'runtime/workshop-director';op=Path(order_ref['path'])
    need(op.parent==archive/'dispatch-orders'and op.suffix=='.json'and len(op.stem)==64 and op==op.resolve()and not any(p.is_symlink()for p in(op,*op.parents)),'legacy-zero-canonical-order')
    root=archive/'daily-parent-executions'/op.stem;parent=root/'state.json'
    if not parent.is_file():return None
    original=read_ref(reference(parent))
    if original.get('status')!='complete'or original.get('outcome')!='no-data-complete':return None
    sys.path[:0]=[str(PROJECT/'skills'/n/'scripts')for n in('workshop-director','douyin-laike-operator','chrome-dom-export')]
    import daily_execution_launcher as launcher
    launcher.completed_source_seal(original,root)
    for ref in original['code_refs']:launcher.source_code_bytes(ref,original,root)
    order=launcher.dispatch.validate(order_ref,archive)
    need(original['order']==order_ref and original['completion_proof']['batch']==batch_ref and scope=={'work_order':order_ref,'scope_sha256':order['scope_sha256'],'active_company_policy':order.get('active_company_policy')},'legacy-zero-original-batch-scope')
    proof=launcher.verify_complete(__import__('copy').deepcopy(original),order,launcher.timing.Clock())
    need(proof==original['completion_proof']and proof['outcome']=='no-data-complete'and proof['all_expected_client_confirmed']is False,'legacy-zero-original-public-proof')
    queue=read_ref(proof['outbox']);need(not queue.get('zero_result_contract')and queue['batch']==batch_ref and queue['items']==[]and all(r.get('zero_rows')is True for r in queue['scopes']),'legacy-zero-original-empty-outbox')
    value={'kind':'verified-original-legacy-no-notification-v1','batch':batch_ref,'parent':reference(parent),'completion':original['completion_ref'],'original_outbox':proof['outbox'],'zero_completion':proof['completion'],'scope':queue['scopes'],'client_send_confirmed':False,'original_contract_satisfied':True}
    return value

def legacy_zero_outbox_disposition(path,facts=None):
    """Preserve an erroneously projected new notice; any sender footprint HOLDs."""
    path=Path(path);q=read_ref(reference(path))
    if q.get('zero_result_contract')!='notify-confirmed-zero-v1':return None
    closed=completed_legacy_no_data(q['batch']['path'],facts)
    if closed is None:return None
    need(path.parent.name==hashlib.sha256(q['batch']['path'].encode()).hexdigest()[:24]and q['batch']==closed['batch']and q['scopes']==closed['scope'],'legacy-zero-derived-outbox-binding')
    # Require all pre-existing inputs before strict re-derivation: no creation.
    for r in q['references']:read_ref(r)
    for item in q['items']:
        need(item['part']=='zero-result'and item['type']=='text'and Path(item['payload']).is_file(),'legacy-zero-not-only-zero-notice');need(sha256(item['payload'])==item['sha256'],'legacy-zero-payload-drift')
        job=Path(q['messenger_directory'])/(hashlib.sha256(item['key'].encode()).hexdigest()[:24]+'.json');need(not job.exists()and not job.is_symlink(),'legacy-zero-sender-footprint-HOLD')
    need(path.with_suffix('.sha256').read_text().strip()==sha256(path)and q.get('version')==1 and q.get('kind')=='daily-test-notification-outbox'and q.get('target')==pn.TARGET and q.get('messenger_directory')==str(messenger.RUNTIME.resolve()),'legacy-zero-derived-schema')
    zn=_zero_notice_module(q['zero_module_ref']);batch=read_ref(q['batch']);expected=[]
    for r in q['references']:
        copy=path.parent/'inputs'/(r['sha256']+'.json');need(copy.is_file()and not copy.is_symlink()and sha256(copy)==r['sha256'],'legacy-zero-derived-snapshot')
    for row in batch['companies']:
        rr=reference(row.get('receipt')or Path(row['outdir'])/'receipt.json');need(rr in q['references'],'legacy-zero-derived-receipt');receipt=read_ref(rr);dates=receipt['date_range']
        from datetime import date,timedelta
        end=(date.fromisoformat(dates['end'])+timedelta(days=1)).isoformat();zn.qualify('daily-comment-stats',row['company'],dates['start'],end,[rr]);title,summary=zn.FLOWS['daily-comment-stats'];text=f'【{title}】\n公司：{row["company"]}\n日期：{dates["start"]}～{dates["end"]}\n{summary}';payload=Path(rr['path']).parent/'test-notifications/zero-result.txt'
        need(payload.read_text()==text,'legacy-zero-derived-text');key='daily-comments:'+row['company']+':'+dates['start']+':'+dates['end']+':zero-result'
        expected.append({'company':row['company'],'seq':row['seq'],'dates':dates,'part':'zero-result','payload':str(payload),'sha256':sha256(payload),'type':'text','key':key})
    need(q['items']==expected,'legacy-zero-derived-items')
    return {'outbox':str(path),'date_start':min(r['date_range']['start']for r in q['scopes']),'date_end':max(r['date_range']['end']for r in q['scopes']),'complete':False,'original_contract_satisfied':True,'disposition':'not-required-by-original-completed-contract','evidence':closed,'items':[],'next':None}

def inspect(path,write_acceptance=False,*,historical_facts=None):
    historical=legacy_zero_outbox_disposition(path,historical_facts)
    if historical is not None:return historical
    path=Path(path).resolve();q=validate_queue(path);states=[item_status(i,q['messenger_directory']) for i in q['items']];complete=all(s['action']=='skip-complete' for s in states)
    result={'outbox':str(path),'date_start':min(s['date_range']['start'] for s in q['scopes']),'date_end':max(s['date_range']['end'] for s in q['scopes']),'complete':complete,'items':states,'next':next((s for s in states if s['action']!='skip-complete'),None)}
    if complete and write_acceptance:
        acceptance={'version':1,'outbox_sha256':sha256(path),'batch':q['batch'],'target':pn.TARGET,'scopes':q['scopes'],'all_required_client_ui_confirmed':True,'delivery_confirmed':False,'no_messages_required':not bool(states),'jobs':[{'path':s['job_path'],'sha256':s['job_sha256'],'key':s['key'],'payload_sha256':s['payload_sha256']} for s in states]}
        need(all(sha256(s['job_path'])==s['job_sha256'] for s in states),'sender-job-changed-before-acceptance');ap=Path(path).with_name('acceptance.json');atomic_json(ap,acceptance);ap.with_suffix('.sha256').write_text(sha256(ap)+'\n');result['acceptance']=reference(ap)
    return result

def backlog(outbox=OUTBOX,write_acceptance=False,*,historical_facts=None):
    historical_facts={}if historical_facts is None else historical_facts
    rows=[inspect(p,write_acceptance,historical_facts=historical_facts) for p in Path(outbox).glob('*/outbox.json')];rows.sort(key=lambda r:(r['date_start'],r['date_end'],r['outbox']));settled=lambda r:r['complete']or r.get('original_contract_satisfied')is True
    return {'batches':rows,'next':next((r for r in rows if not settled(r)),None),'complete':all(r['complete']for r in rows),'can_acquire_new_dates':all(settled(r)for r in rows),'historical_closed':[r for r in rows if r.get('original_contract_satisfied')is True]}
def discover(work_root):
    need(Path(work_root).is_dir(),'notification-work-root-missing')
    result=[]
    for p in Path(work_root).resolve().rglob('batch_receipt.json'):
        value=json.loads(p.read_text())
        if value.get('flow')=='daily-comment-stats' and value.get('mode')=='agent-live' and value.get('status')=='complete':result.append(p)
    return sorted(result,key=lambda p:(json.loads(p.read_text())['date_range']['start'],str(p)))
def plan(work_root=None,receipt=None,receipt_sha=None,outbox=OUTBOX,messenger_dir=messenger.RUNTIME):
    paths=discover(work_root) if work_root else []
    if receipt:
        rp=Path(receipt).resolve();need(receipt_sha and sha256(rp)==receipt_sha,'explicit-receipt-hash-required')
        if rp.name=='batch_receipt.json':paths=[rp]
        else:
            bp=rp.parent.parent/'batch_receipt.json';need(bp.is_file(),'complete-parent-batch-required');b=json.loads(bp.read_text());need(any(Path(row.get('receipt') or Path(row['outdir'])/'receipt.json').resolve()==rp for row in b['companies']),'receipt-not-in-parent-batch');paths=[bp]
    need(work_root or receipt,'work-root-or-receipt-required')
    historical_facts={}
    for p in paths:
        # An existing projection is qualified exactly once by inspect below.
        existing=Path(outbox)/hashlib.sha256(str(p.resolve()).encode()).hexdigest()[:24]/'outbox.json'
        if existing.exists():continue
        if completed_legacy_no_data(p)is None:prepare_batch(p,outbox,messenger_dir,receipt_sha if receipt and Path(receipt).name=='batch_receipt.json' else None)
    return backlog(outbox,True,historical_facts=historical_facts)
def sender_run(path):
    # Existing sender owns its complete normal phase chain and all durable
    # intent/recipient/file-choice guards. Never reproduce those decisions here.
    result=subprocess.run([sys.executable,str(PROJECT/'skills/wecom-messenger/scripts/messenger.py'),'run','--job',str(path)],capture_output=True,text=True)
    need(result.returncode in (0,2),'sender-run-process-failed')
    try:summary=json.loads(result.stdout)
    except (ValueError,TypeError):raise ValueError('sender-run-output-invalid')
    need(summary.get('job_path')==str(Path(path).resolve()),'sender-run-result-unbound')
    return summary

def run(outbox=OUTBOX,max_steps=25,advance=None,run_job=None):
    run_job=run_job or (advance if advance is not None else sender_run)
    advance=advance or messenger.advance;verified=set();started=set()
    with lock(Path(outbox)/'.runner'):
        for _ in range(max_steps):
            status=backlog(outbox,True);batch=status['next']
            if batch is None:return status
            current=batch['next'];action=current['action'];path=Path(current['job_path']);q=validate_queue(batch['outbox']);item=next(i for i in q['items'] if i['key']==current['key'])
            if action=='prepare':
                kwargs={'text':Path(item['payload']).read_text()} if item['type']=='text' else {'file':item['payload']}
                messenger.prepare(item['key'],'group',pn.TARGET,scope='test',directory=q['messenger_directory'],**kwargs);continue
            if action=='verify-readonly':
                if str(path) in verified:return status
                verified.add(str(path));advance(path)
            elif action=='advance':
                if str(path) in started:return status
                started.add(str(path));run_job(path)
                # A failed/unknown outcome from this invocation is not a new
                # authorization to continue or retry, even at verify-sent.
                after=item_status(item,q['messenger_directory'])
                if after['action']!='skip-complete':return backlog(outbox,True)
            else:return status
        return backlog(outbox,True)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','status','run','gate']);source=p.add_mutually_exclusive_group();source.add_argument('--work-root');source.add_argument('--receipt');p.add_argument('--receipt-sha256');p.add_argument('--outbox',default=str(OUTBOX));p.add_argument('--steps',type=int,default=25);a=p.parse_args()
    try:
        need(1<=a.steps<=100,'step-limit-invalid')
        if a.command=='status':result=backlog(a.outbox)
        else:
            result=plan(a.work_root,a.receipt,a.receipt_sha256,a.outbox,messenger.RUNTIME)
            if a.command=='run':result=run(a.outbox,a.steps)
        if a.command=='gate':result['gate']='clear' if result['can_acquire_new_dates'] else 'blocked-notification-backlog'
        print(json.dumps(result,ensure_ascii=False,indent=2));return 3 if a.command=='gate' and not result['can_acquire_new_dates'] else 0
    except (ValueError,KeyError,OSError,messenger.SendError) as error:print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=False));return 2

_ZERO_NOTICE_PATH=PROJECT/'skills/workshop-director/scripts/zero_result_notice.py'
_ZERO_NOTICE_MODULE={'path':str(_ZERO_NOTICE_PATH),'sha256':__import__('hashlib').sha256(_ZERO_NOTICE_PATH.read_bytes()).hexdigest()}
def _zero_notice_module(reference=None):
    expected=_ZERO_NOTICE_MODULE
    need(reference is None or reference==expected,'zero-notice-module-binding')
    path=Path(expected['path'])
    need(path==PROJECT/'skills/workshop-director/scripts/zero_result_notice.py'and path.is_absolute()and path.resolve()==path and not any(p.is_symlink()for p in (path,*path.parents))and path.is_file(),'zero-notice-module-origin')
    need(__import__('hashlib').sha256(path.read_bytes()).hexdigest()==expected['sha256'],'zero-notice-module-code-drift')
    sys.path.insert(0,str(path.parent))
    import zero_result_notice
    need(Path(zero_result_notice.__file__)==path,'zero-notice-loaded-module-origin')
    return zero_result_notice

if __name__=='__main__':raise SystemExit(main())


from ds_common import dom_command_function
collection_ready_value=dom_command_function(collection_ready_value)
