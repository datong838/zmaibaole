#!/usr/bin/env python3
"""Immutable existing-result inspection orders. Offline; no browser/send/submit."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,json
from pathlib import Path
import authoritative_join as authority
import normal_observation as normal

def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':authority.digest(p)}
def document(r):
    normal.need(authority.digest(r['path'])==r['sha256'],'result-order-input-changed');return json.loads(Path(r['path']).read_text())
def prepare(job_path,source_path,envelope_path,profile_path,out):
    refs={k:ref(v) for k,v in [('job',job_path),('source',source_path),('envelope',envelope_path),('profile',profile_path)]};values={k:document(r) for k,r in refs.items()}
    job=values['job'];source=values['source'];normal.need(normal.joined(job,values['envelope'],values['profile'],job['source_receipt'],job['source_receipt_sha256'])==source,'result-orders-current-source-not-reproducible')
    orders=[]
    for row in source['rows']:
        normal.need(row['action'] in ('投诉','查看投诉结果','投诉审核中'),'unrecognized-source-action')
        if row['action']=='投诉':continue
        key=source['groupid']+':'+row['review_id'];orders.append({'review_key':key,'snapshot_sha256':refs['source']['sha256'],'card_selector':row['dom_selector'],'original_action':row['action'],'source_tuple':{k:row[k] for k in ('review_id','store','customer','text','stars','date')},'allowed_actions':['查看投诉结果','投诉审核中'],'click_kind':'complaint-read','never_click':['投诉','再次投诉','提交'],'result_binding':'unique result drawer; exact store/customer/full text; public status and original fields only'})
    result={'kind':'existing-complaint-result-orders-v1','inputs':refs,'company':source['company'],'groupid':source['groupid'],'range':{'start':source['start'],'end_exclusive':source['end_exclusive']},'orders':orders,'skip_policy':'same-key task already has accepted/rejected result bound to this snapshot; never reopen resolved merely for acceptance','submission_enabled':False,'send_enabled':False}
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():normal.need(json.loads(out.read_text())==result,'existing-result-order-conflict')
    else:
        with out.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('job','source','envelope','profile','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args()
    try:r=prepare(a.job,a.source,a.envelope,a.profile,a.out);print(json.dumps({'ok':True,'orders':len(r['orders']),'out':str(Path(a.out).resolve()),'ui_used':False},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
