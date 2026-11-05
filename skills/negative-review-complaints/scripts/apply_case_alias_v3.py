#!/usr/bin/env python3
"""Candidate original-key versioned result consumer. No browser or sender."""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,copy,json,os,tempfile
import case_alias_versions as v
cli=v.v2;runner=v.core;c=v.c;workflow=v.w;need=v.need
current_guard=v.apply2.current_guard
unchanged_original_task=v.apply2.unchanged_original_task
target_invariants=v.apply2.target_invariants
check_committed=v.apply2.check_committed
memory_observation=v.apply2.memory_observation

def verified(receipt_ref):
    receipt=v.verify_receipt(receipt_ref);op=v.doc(receipt['operation']);m=v.doc(op['manifest']);base=v.base(m)
    _,original,task,_,_=v.context(m)
    # No current-lease hash in historical verification; actual ledger equality is
    # checked by the existing result consumer under BOTH original business locks.
    return receipt,op,m,base,original,task

def index_owner(m,manifest_ref):
    idx=v.doc(v.ref(v.index_path(m)))
    need(idx.get('kind')=='review-case-alias-active-v3' and idx.get('review_key')==m['review_key'] and idx.get('origin')==m['origin']['manifest'] and idx.get('current')==manifest_ref,'alias-v3-apply-active-owner-required')

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

def apply(receipt_ref):
    receipt,op,m,base,original,original_task=verified(receipt_ref);root=Path(m['root']);key=m['review_key'];directory=base/'apply';directory.mkdir(exist_ok=True);journal=directory/'operation.json';result_path=directory/'reconciled-result.json'
    if journal.exists():
        previous=c.document(c.ref(journal))
        if previous.get('state')=='complete':
            need(previous.get('receipt')==receipt_ref,'alias-v3-original-completed-receipt-required');v.verify_apply(c.ref(journal))
            return {'state':'complete','already_applied':True,'operation':c.ref(journal),'result':previous['result_input'],'ui_used':False,'record_replayed':False,'xlsx_reexported':False}
    with runner.e.operation_lock(root,key):
        with workflow.locked(root):
            # Recheck immutable chain after acquiring BOTH existing business locks.
            receipt,op,m,base,original,original_task=verified(receipt_ref);index_owner(m,op['manifest']);s=workflow.load(root);current_guard(s,m,original);value=v.result_for(m,op,receipt_ref);result_ref=immutable(result_path,value);code_sha=c.ref(Path(__file__).resolve())['sha256']
            audit=json.loads(journal.read_bytes()) if journal.exists() else None
            if audit:
                need(audit['receipt']==receipt_ref and audit['result_input']==result_ref and audit['consumer_code_sha256']==code_sha,'alias-apply-original-operation-required')
                need(c.document(audit['original_task'])==original_task,'alias-apply-original-task-archive-changed');before_doc=c.document(audit['before_state']);need(before_doc['tasks'][key]['review']==original_task['review'] and before_doc['tasks'][key]['latest_snapshot']==original_task['latest_snapshot'] and before_doc['tasks'][key]['result']==original_task['result'],'alias-apply-original-state-archive-changed')
                if audit.get('recorded_state'):c.document(audit['recorded_state'])
                if audit['state']=='memory-hook-unconfirmed':
                    # Pure proof only: no second record_result/auto_import call.
                    audit['memory_observation']=memory_observation(m,original_task,result_ref);audit['state']='recorded';audit.pop('error',None);audit['recorded_state']=immutable_bytes(directory/'recorded-state.json',(root/'state.json').read_bytes());save(journal,audit)
            else:
                unchanged_original_task(s['tasks'][key],original_task)
                before_state=immutable_bytes(directory/'before-state.json',(root/'state.json').read_bytes())
                audit={'kind':'apply-public-case-alias-v3','state':'record-intent','manifest':op['manifest'],'receipt':receipt_ref,'result_input':result_ref,'original_task':immutable(directory/'original-task.json',original_task),'before_state':before_state,'consumer_code_sha256':code_sha,'created_at':runner.now(),'ui_used':False,'send_enabled':False,'submission_enabled':False};save(journal,audit)
            if audit['state']=='record-intent':
                is_already=s['tasks'][key].get('result',{}).get('alias_ref')==receipt_ref
                if is_already:
                    check_committed(root,s,key,original_task,value,result_ref)
                    audit['memory_observation']=memory_observation(m,original_task,result_ref)
                    # Crash after JSON commit is not permission to record again.
                    audit['state']='recorded';audit['recorded_state']=immutable_bytes(directory/'recorded-state.json',(root/'state.json').read_bytes());audit['recovery']='existing-original-key-record-verified-no-record-replay';save(journal,audit)
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
                v.verify_apply(c.ref(journal));c.document(audit['result_input']);need(Path(audit['workbook']['path'])==directory/('workbook-'+audit['workbook']['sha256']+'.xlsx') and c.ref(audit['workbook']['path'])==audit['workbook'],'alias-apply-workbook-archive-changed');return {'state':'complete','already_applied':True,'operation':c.ref(journal),'result':result_ref,'ui_used':False,'record_replayed':False,'xlsx_reexported':False}
            need(audit['state'] in ('recorded','awaiting-xlsx'),'alias-apply-state-invalid')
            try:
                if s.get('xlsx_dirty'):
                    workbook=workflow.export_xlsx(root,s)
                else:
                    p=root/'投诉处理结果汇总.xlsx';need(p.is_file(),'alias-apply-clean-workbook-missing');workbook=c.ref(p)
                archive=directory/('workbook-'+workbook['sha256']+'.xlsx');audit['workbook']=immutable_bytes(archive,Path(workbook['path']).read_bytes());need(audit['workbook']['sha256']==workbook['sha256'],'alias-apply-workbook-hash-changed')
            except Exception as exc:
                audit.update(state='awaiting-xlsx',error={'type':type(exc).__name__,'message':str(exc)});save(journal,audit);raise
            audit.update(state='complete',completed_at=runner.now());audit.pop('error',None);save(journal,audit);v.verify_apply(c.ref(journal))
            return {'state':'complete','already_applied':False,'operation':c.ref(journal),'result':result_ref,'workbook':audit['workbook'],'ui_used':False,'record_replayed':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);a=p.parse_args();print(json.dumps({'ok':True,**apply({'path':a.receipt,'sha256':a.receipt_sha256})},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'ui_used':False,'retry_input':False},ensure_ascii=False));raise SystemExit(2)
