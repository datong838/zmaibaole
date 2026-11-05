#!/usr/bin/env python3
"""Candidate offline consumption of a verified alias into the ORIGINAL task.
No browser, sender, source ingest, capture, submission or new customer key.
"""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,copy,json,os,tempfile
import case_alias_cli as cli
runner=cli.runner
c=cli.c
workflow=runner.workflow
need=c.need

def immutable_bytes(path,raw):
    path=cli.canonical(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'alias-apply-immutable-conflict')
    else:
        fd,tmp=tempfile.mkstemp(prefix='.alias-pending-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,path)
            except FileExistsError:need(path.read_bytes()==raw,'alias-apply-immutable-conflict')
            dfd=os.open(path.parent,os.O_RDONLY)
            try:os.fsync(dfd)
            finally:os.close(dfd)
        finally:os.unlink(tmp)
    return c.ref(path)
def immutable(path,value):return immutable_bytes(path,c.encoded(value))
def save(path,value):workflow.atomic(path,value)

def verified(receipt_ref):
    receipt=runner.validate_alias(receipt_ref);op=c.document(receipt['operation']);m=op['manifest'];base=cli.folder(m)
    need(receipt_ref==c.ref(base/'alias-receipt.json'),'alias-apply-original-canonical-receipt-required')
    checked=cli.verify(c.ref(base/'manifest.json'));need(checked['operation']==receipt['operation'],'alias-apply-original-operation-changed')
    original=c.document(m['inputs']['ledger']);source=c.document(m['inputs']['old_source']);need(original.get('company')==source.get('company') and str(original.get('groupid'))==str(source.get('groupid')) and original.get('identity')==source.get('identity'),'alias-apply-original-source-identity-mismatch');task=original['tasks'][m['review_key']]
    need(task['status']=='existing_pending' and task['result']['status']=='pending' and task['result']['evidence']==m['old_result'],'alias-apply-original-pending-required')
    need(task['latest_snapshot']['sha256']==m['inputs']['old_source']['sha256']==task['result']['snapshot_sha256'],'alias-apply-original-source-snapshot-required')
    need(c.document(task['latest_snapshot'])==c.document(m['inputs']['old_source']),'alias-apply-source-alias-bytes-mismatch')
    return receipt,op,m,base,original,task

def result_input(receipt_ref,op,m,original_task):
    page=c.document(op['drawer']);parsed=c.parse_case(c.document(m['inputs']['fresh_job']),page,text_schema=c.document(m['inputs']['fresh_profile']).get('text_schema'))
    scope=runner.n.flatten(page['tree']['root']);drawers=runner.e.drawers(page);need(len(drawers)==1,'alias-apply-result-drawer-not-unique');scope=runner.n.flatten(drawers[0])
    details=[x for x in scope if x.get('attributes',{}).get('class')=='status-content-Uk09gi'];need(len(details)<=1,'alias-apply-status-detail-not-unique');detail_text=[runner.n.literal(x) for x in details]
    visible='\n'.join([parsed['platform_status']]+detail_text+[k+'：'+parsed['case'][k] for k in ('投诉类型','投诉理由','投诉时间')])
    return {'review_key':m['review_key'],'snapshot_sha256':original_task['latest_snapshot']['sha256'],'url':parsed['tab']['url'],'source':'local-dom-bridge','observed_at':parsed['observed_at'],'status':parsed['status'],'visible_text':visible,'platform_status':parsed['platform_status'],'platform_status_detail':detail_text,'original_complaint':parsed['case'],'result_dom_sha256':parsed['result_dom_sha256'],'matching':'public-case-alias: exact public type/second-time/full reason and unique source-bound store/body/product/stars; no current-export nickname join','submitted_by_this_workflow':False,'alias_ref':receipt_ref,'observed_customer':parsed['review']['customer'],'person_identity_verified':False,'previous_result_ref':original_task['result']['evidence']}

def current_guard(s,m,original):
    need(s.get('mode')=='draft-only' and s.get('browser_backend')=='local-dom-bridge','alias-apply-live-workflow-required')
    need(s.get('company')==original['company'] and str(s.get('groupid'))==str(original['groupid']) and s.get('identity')==original['identity'],'alias-apply-root-company-mismatch')
    import case_memory
    case_memory._workflow_domain(s)
    need(m['review_key'] in s.get('tasks',{}),'alias-apply-original-task-missing')

def unchanged_original_task(task,original_task):
    need(task['review']==original_task['review'] and task['latest_snapshot']==original_task['latest_snapshot'],'alias-apply-original-review-or-source-changed')
    need(task['status']=='existing_pending' and task['result']==original_task['result'],'alias-apply-original-pending-result-changed')
    c.document(task['latest_snapshot']);c.document(task['result']['evidence'])

def target_invariants(before,after,key):
    need(set(before)==set(after),'alias-apply-ledger-schema-changed')
    for name in before:
        if name not in ('tasks','events','updated_at','xlsx_dirty'):need(before[name]==after[name],'alias-apply-unrelated-ledger-changed:'+name)
    need(set(before['tasks'])==set(after['tasks']),'alias-apply-task-set-changed')
    for k in before['tasks']:
        if k!=key:need(before['tasks'][k]==after['tasks'][k],'alias-apply-other-task-changed')
        else:
            old,new=before['tasks'][k],after['tasks'][k]
            for f in set(old)|set(new):
                if f not in ('result','status','updated_at','result_history'):need(old.get(f)==new.get(f),'alias-apply-original-task-metadata-changed:'+f)
    need(after['events'][:len(before['events'])]==before['events'] and len(after['events'])==len(before['events'])+1,'alias-apply-record-event-count-invalid')

def committed(s,key,original_task,value,result_ref):
    task=s['tasks'][key]
    expected={**value,'evidence':task.get('result',{}).get('evidence')};need(task.get('result')==expected,'alias-apply-current-result-changed')
    evidence=task['result']['evidence'];p=Path(evidence['path']);need(p.parent==Path(s['_root'])/'evidence' and p.name==result_ref['sha256']+'.json' and evidence['sha256']==result_ref['sha256'] and c.document(evidence)==value,'alias-apply-owned-result-evidence-invalid')
    need(task['review']==original_task['review'] and task['latest_snapshot']==original_task['latest_snapshot'],'alias-apply-original-review-or-source-changed')
    need(task.get('status')==('resolved' if value['status'] in ('accepted','rejected') else 'existing_pending'),'alias-apply-result-status-changed')
    need(task.get('result_history')==original_task.get('result_history',[])+[original_task['result']],'alias-apply-original-result-history-changed')
    events=[e for e in s['events'] if e.get('type')=='platform-result-read' and e.get('id')==key and e.get('record',{}).get('result',{}).get('alias_ref')==value['alias_ref']]
    need(len(events)==1 and events[0]['record']['review']==original_task['review'] and events[0]['record']['result']==task['result'],'alias-apply-exactly-one-original-key-event-required')
    return True

def check_committed(root,s,key,original_task,value,result_ref):
    check=copy.deepcopy(s);check['_root']=str(root);return committed(check,key,original_task,value,result_ref)

def memory_observation(m,original_task,result_ref):
    import case_memory
    source=c.document(original_task['latest_snapshot']);old=c.document(original_task['result']['evidence']);old_case_id=case_memory._case_id(case_memory._facts(source,old,m['review_key']))
    records=case_memory.read_records()
    matches=[r for r in records if r.get('review_key')==m['review_key'] and r.get('company')==source['company'] and r.get('source_ref',{}).get('sha256')==original_task['latest_snapshot']['sha256'] and r.get('result_ref',{}).get('sha256')==result_ref['sha256']]
    need(len(matches)==1 and matches[0]['case_id']==old_case_id,'alias-apply-original-case-observation-not-confirmed')
    return {'case_id':old_case_id,'observation_id':matches[0]['observation_id'],'result_sha256':result_ref['sha256'],'original_result_ref':original_task['result']['evidence'],'original_review_key':m['review_key']}

def apply(receipt_ref):
    receipt,op,m,base,original,original_task=verified(receipt_ref);root=Path(m['root']);key=m['review_key'];directory=base/'apply';directory.mkdir(exist_ok=True);journal=directory/'operation.json';result_path=directory/'reconciled-result.json'
    with runner.e.operation_lock(root,key):
        with workflow.locked(root):
            # Recheck immutable chain after acquiring BOTH existing business locks.
            receipt,op,m,base,original,original_task=verified(receipt_ref);s=workflow.load(root);current_guard(s,m,original);value=result_input(receipt_ref,op,m,original_task);result_ref=immutable(result_path,value);code_sha=c.ref(Path(__file__).resolve())['sha256']
            audit=json.loads(journal.read_bytes()) if journal.exists() else None
            if audit:
                need(audit['receipt']==receipt_ref and audit['result_input']==result_ref and audit['consumer_code_sha256']==code_sha,'alias-apply-original-operation-required')
                need(c.document(audit['original_task'])==original_task,'alias-apply-original-task-archive-changed');before_doc=c.document(audit['before_state']);need(before_doc['tasks'][key]['review']==original_task['review'] and before_doc['tasks'][key]['latest_snapshot']==original_task['latest_snapshot'] and before_doc['tasks'][key]['result']==original_task['result'],'alias-apply-original-state-archive-changed')
                if audit.get('recorded_state'):c.document(audit['recorded_state'])
                if audit['state']=='memory-hook-unconfirmed':
                    # Pure proof only: no second record_result/auto_import call.
                    audit['memory_observation']=memory_observation(m,original_task,result_ref);audit['state']='recorded';audit.pop('error',None);save(journal,audit)
            else:
                unchanged_original_task(s['tasks'][key],original_task)
                before_state=immutable_bytes(directory/'before-state.json',(root/'state.json').read_bytes())
                audit={'kind':'apply-public-case-alias-v1','state':'record-intent','receipt':receipt_ref,'result_input':result_ref,'original_task':immutable(directory/'original-task.json',original_task),'before_state':before_state,'consumer_code_sha256':code_sha,'created_at':runner.now(),'ui_used':False,'send_enabled':False,'submission_enabled':False};save(journal,audit)
            if audit['state']=='record-intent':
                is_already=s['tasks'][key].get('result',{}).get('alias_ref')==receipt_ref
                if is_already:
                    check_committed(root,s,key,original_task,value,result_ref)
                    audit['memory_observation']=memory_observation(m,original_task,result_ref)
                    # Crash after JSON commit is not permission to record again.
                    audit['state']='recorded';audit['recovery']='existing-original-key-record-verified-no-record-replay';save(journal,audit)
                else:
                    unchanged_original_task(s['tasks'][key],original_task);before=copy.deepcopy(s);s['tasks'][key]['result_history']=original_task.get('result_history',[])+[copy.deepcopy(original_task['result'])]
                    try:workflow.record_result(root,s,key,result_path)
                    except Exception as exc:
                        actual=workflow.load(root)
                        if actual['tasks'][key].get('result',{}).get('alias_ref')==receipt_ref:
                            audit.update(state='memory-hook-unconfirmed',error={'type':type(exc).__name__,'message':str(exc)});save(journal,audit)
                        raise
                    s=workflow.load(root);target_invariants(before,s,key);check_committed(root,s,key,original_task,value,result_ref);audit['memory_observation']=memory_observation(m,original_task,result_ref);audit['state']='recorded';audit['recorded_state']=immutable_bytes(directory/'recorded-state.json',(root/'state.json').read_bytes());save(journal,audit)
            s=workflow.load(root);check_committed(root,s,key,original_task,value,result_ref);need(audit.get('memory_observation')==memory_observation(m,original_task,result_ref),'alias-apply-memory-observation-changed')
            if audit['state']=='complete':
                c.document(audit['result_input']);need(Path(audit['workbook']['path'])==directory/('workbook-'+audit['workbook']['sha256']+'.xlsx') and c.ref(audit['workbook']['path'])==audit['workbook'],'alias-apply-workbook-archive-changed');return {'state':'complete','already_applied':True,'operation':c.ref(journal),'result':result_ref,'ui_used':False,'record_replayed':False,'xlsx_reexported':False}
            need(audit['state'] in ('recorded','awaiting-xlsx'),'alias-apply-state-invalid')
            try:
                if s.get('xlsx_dirty'):
                    workbook=workflow.export_xlsx(root,s)
                else:
                    p=root/'投诉处理结果汇总.xlsx';need(p.is_file(),'alias-apply-clean-workbook-missing');workbook=c.ref(p)
                archive=directory/('workbook-'+workbook['sha256']+'.xlsx');audit['workbook']=immutable_bytes(archive,Path(workbook['path']).read_bytes());need(audit['workbook']['sha256']==workbook['sha256'],'alias-apply-workbook-hash-changed')
            except Exception as exc:
                audit.update(state='awaiting-xlsx',error={'type':type(exc).__name__,'message':str(exc)});save(journal,audit);raise
            audit.update(state='complete',completed_at=runner.now());audit.pop('error',None);save(journal,audit)
            return {'state':'complete','already_applied':False,'operation':c.ref(journal),'result':result_ref,'workbook':audit['workbook'],'ui_used':False,'record_replayed':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);a=p.parse_args();print(json.dumps({'ok':True,**apply({'path':a.receipt,'sha256':a.receipt_sha256})},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'ui_used':False,'retry_input':False},ensure_ascii=False));raise SystemExit(2)
