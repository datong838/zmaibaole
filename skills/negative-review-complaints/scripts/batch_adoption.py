#!/usr/bin/env python3
"""B95 explicit source-bound adoption of one preexisting unfinished batch.

The 10-30/10-31 supervised abandonment left ledger batches open (no
closed_at). build() refuses preexisting unfinished batches: adopting one that
predates this parent is an explicit, evidence-verified migration - never a
fresh key or a replayed delivery. The batch's snapshot is hash-verified, its
tasks must all sit in a READY state (no failed work is adopted), an immutable
adoption manifest is archived, and the batch is closed through the same
cursor logic as a natural close, stamped `adopted` so it is never mistaken
for a delivered batch.
"""
import argparse,fcntl,hashlib,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent))
import workflow
KIND='complaint-batch-adoption-v1'
def need(ok,code):
    if not ok:raise ValueError(code)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ledger',required=True)
    ap.add_argument('--batch',required=True)
    ap.add_argument('--original-sha256',required=True)
    a=ap.parse_args()
    ledger=Path(a.ledger).resolve();need(ledger.is_file() and not ledger.is_symlink() and ledger.name=='state.json','adoption-canonical-ledger-required')
    need(sha(ledger)==a.original_sha256,'adoption-original-sha-mismatch')
    root=ledger.parent
    s=json.loads(ledger.read_bytes())
    need(s.get('mode')=='draft-only','adoption-draft-only-required')
    batches=s.get('batches',{});need(a.batch in batches,'adoption-batch-missing')
    b=batches[a.batch]
    if b.get('closed_at'):
        need(b.get('adopted',{}).get('sha256'),'adoption-already-closed-not-adopted')
        print(json.dumps({'state':'already-adopted','batch':a.batch,'adopted':b['adopted']},ensure_ascii=False));return
    need(b.get('ids')is not None and b.get('snapshot'),'adoption-batch-shape-invalid')
    workflow.verify_evidence(b['snapshot'])
    statuses={}
    # B95: adoption closes the capture window, not the work. READY states are
    # finished ledger items; 'pending' items were never started by the
    # abandoned round and stay open in the ledger - build() counts them into
    # recheck_ids so this parent's scope picks them up. Failed or blocked work
    # is never adopted.
    allowed=workflow.READY|{'pending'}
    for key in b['ids']:
        t=s['tasks'].get(key);need(t is not None,'adoption-task-missing:'+key)
        statuses[key]=t.get('status');need(t.get('status') in allowed,'adoption-task-not-ready:'+key+':'+str(t.get('status')))
    directory=root/'batch-adoption'/a.original_sha256
    at=datetime.now(timezone.utc).isoformat()
    manifest={'kind':KIND,'at':at,'ledger':ref(ledger),'batch':a.batch,
              'batch_facts':{'start':b['start'],'end_exclusive':b['end_exclusive'],'ids':len(b['ids']),'statuses':statuses,'filtered_count':b.get('filtered_count')},
              'snapshot':b['snapshot'],'not_platform_submission':True}
    mp=directory/'manifest.json'
    if mp.exists():need(sha(mp)==ref(mp)['sha256'] and json.loads(mp.read_bytes()).get('batch')==a.batch,'adoption-manifest-conflict')
    else:
        mp.parent.mkdir(parents=True,exist_ok=True)
        with mp.open('xb') as f:f.write((json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    mref=ref(mp)
    with (root/'state.json.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        need(sha(ledger)==a.original_sha256,'adoption-concurrent-ledger-change')
        s=json.loads(ledger.read_bytes());b=s['batches'][a.batch]
        if b.get('closed_at'):
            need(b.get('adopted',{}).get('sha256')==mref['sha256'],'adoption-already-closed-conflict')
            print(json.dumps({'state':'already-adopted','batch':a.batch},ensure_ascii=False));return
        value=workflow._close_collected_batch_value(s,a.batch,completed_at=workflow.now(),completed_on=workflow.shanghai_today().isoformat())
        value['batches'][a.batch]['adopted']=mref
        workflow.save(root,value,{'type':'batch-adopted','batch':a.batch,'manifest':mref,'not_platform_submission':True})
    print(json.dumps({'state':'adopted','batch':a.batch,'manifest':mref,'next_start':value.get('next_start')},ensure_ascii=False))
if __name__=='__main__':
    main()
