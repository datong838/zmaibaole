#!/usr/bin/env python3
"""B92 read-only artifact-identity reconcile for export-outcome-unknown-no-resubmit.

Doctrine: an unknown export submission is reconciled only from records, never
replayed. When the reviewed record page proves the submission created nothing
(total unchanged, zero post-baseline records) and the exact-range artifact
already exists as a unique success row generated the same day (bound
provenance: it is a baseline row), bind that platform record as this run's
generated artifact. No UI, no deletion, no resubmission.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import dom_evidence as d
from role_cli import validate_job,write_json
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('local_dom_bridge',ROOT/'skills/chrome-dom-export/scripts/bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
KIND='export-artifact-identity-recovery-v1'
EXPECTED_ERROR='export-outcome-unknown-no-resubmit'
def need(ok,code):
    if not ok:raise ValueError(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def strict_path(value):
    p=Path(value);need(p.is_absolute() and p==p.resolve() and not p.is_symlink(),'artifact-recovery-absolute-nonsymlink-path-required');return p
def immutable(path,raw):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'artifact-recovery-immutable-conflict')
    else:
        with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    return ref(path)
def fingerprint(job):
    from switch_read_recovery import fingerprint as configured_fingerprint
    return configured_fingerprint(job)
def contract(job,s):
    validate_job(job)
    need(s.get('fingerprint')==fingerprint(job) and s.get('work_order_id')==job['work_order_id'] and s.get('company')==job['company'] and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')=={k:job['date_range'][k] for k in ('start','end')},'artifact-recovery-original-job-conflict')
    need(s.get('backend')=='local-dom-bridge' and s.get('state')=='running' and s.get('phase')=='pollRecords' and s.get('exportPending') is True and s.get('attempts')==1,'artifact-recovery-original-phase-invalid')
    need(not any(s.get(k) for k in ('downloadPending','download_ticket','download_command','download_receipt','result')),'artifact-recovery-download-already-started')
    error=s.get('last_error');need(type(error)is dict and error.get('code')==error.get('message')==EXPECTED_ERROR and error.get('at'),'artifact-recovery-only-known-error')
    need(s.get('waiting_for')=='generated-export-record-not-visible-or-ready-on-first-page','artifact-recovery-waiting-state-invalid')
    need(not s.get('generated_record'),'artifact-recovery-already-bound')
    need(s.get('identity')==s.get('identity_before')==job.get('identity_baseline') and s.get('provider_baseline')==job.get('provider_baseline'),'artifact-recovery-full-identity-required')
    calls=s.get('calls',[]);need(calls and all(c.get('state')=='confirmed' for c in calls),'artifact-recovery-unknown-no-replay')
    submits=[c for c in calls if c.get('phase')=='submitExport'];reloads=[c for c in calls if c.get('phase')=='reloadRecords']
    need(len(submits)==len(reloads)==1 and calls.index(submits[0])+1==calls.index(reloads[0])==len(calls)-1,'artifact-recovery-one-submit-reload-required')
    sub,rel=submits[0],reloads[0]
    result=rel.get('result',{})
    need(result.get('reloaded') is True and result.get('loadComplete') is True and result.get('tabId')==s['record_tab_id'],'artifact-recovery-reload-reply-invalid')
    submitted=datetime.fromisoformat(s['submitted_at']);need(submitted.utcoffset() is not None,'artifact-recovery-timezone-required')
    need((datetime.now(timezone.utc)-submitted).total_seconds()>600,'artifact-recovery-not-yet-unknown')
    return {'tab_id':s['record_tab_id'],'window_id':result['windowId'],'submitted_at':s['submitted_at']}
def fresh_tree(scope,job):
    reply=bridge.request({'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']})
    need(reply.get('ok')is True,'artifact-recovery-bridge-read-failed')
    from readonly_tick_snapshot import decode
    value=decode(reply['result'],scope['tab_id'],scope['window_id'])
    tree=value['tree']
    from urllib.parse import urlsplit
    need(tree.get('url')=='https://life.douyin.com/p/fulfillsettle/export_records/20101','artifact-recovery-record-url-changed')
    need(value['ping'].get('version')==d.VERSION and value['ping'].get('safety')=='DOM-only','artifact-recovery-dom-version-changed')
    return tree
def bind(job_path,original_sha256):
    job_path=strict_path(job_path);jobraw=job_path.read_bytes();job=json.loads(jobraw)
    need(job.get('work_order_path')==str(job_path),'artifact-recovery-canonical-work-order-required')
    path=strict_path(job['workflow_path']);raw=path.read_bytes();s=json.loads(raw)
    if isinstance(s.get('generated_record'),dict) and s['generated_record'].get('bound_by')==KIND:
        need(s['generated_record'].get('identity_proof',{}).get('sha256'),'artifact-recovery-bound-proof-missing');return {'state':'reconciled','journal':ref(path),'already_reconciled':True,'ui_used':False}
    need(sha(raw)==original_sha256,'artifact-recovery-original-sha-mismatch')
    scope=contract(job,s)
    tree=fresh_tree(scope,job)
    proof_parse=d.submitted_export_record(tree,job['date_range'],s['baseline_records'],scope['submitted_at'])
    page=proof_parse['page']
    need(page['total']==len(s['baseline_records']),'artifact-recovery-submission-created-records')
    from urllib.parse import urlsplit
    need(tree.get('url')!=urlsplit('')and page['visible_rows']==min(page['total'],10),'artifact-recovery-page-incomplete')
    tag=d.export_tag(job['date_range'])
    submitted_day=datetime.fromisoformat(scope['submitted_at']).astimezone(ZoneInfo('Asia/Shanghai')).date()
    candidates=[r for r in d.records({'truncated':False,'root':_body(tree)}) if r['text'].split(' ',1)[0]==tag and r['state']=='success' and datetime.strptime(r['generated_at'],'%Y-%m-%d %H:%M:%S').date()==submitted_day]
    need(len(candidates)==1,'artifact-recovery-candidate-not-unique')
    row=candidates[0]
    baseline_ids={(r['text'],r['generated_at']) for r in s['baseline_records']}
    need((row['text'],row['generated_at'])in baseline_ids,'artifact-recovery-candidate-not-in-baseline')
    directory=path.parent/'export-artifact-identity-recovery'/original_sha256
    at=datetime.now(timezone.utc).isoformat()
    proof={'kind':KIND,'at':at,'new_mutations':0,'ui_used':False,'canonical_work_order':str(job_path),
           'original_journal':immutable(directory/'original-journal.json',raw),
           'job':immutable(directory/'original-job.json',jobraw),
           'fresh_tree':immutable(directory/'record-page-tree.json',(json.dumps(tree,ensure_ascii=False,sort_keys=True)+'\n').encode()),
           'facts':{'tag':tag,'filename':row['text'].split(' ',1)[0],'generated_at':row['generated_at'],'state':row['state'],'total':page['total'],'baseline_count':len(s['baseline_records']),'submitted_at':scope['submitted_at']},
           'next_phase':'pollRecords'}
    proof_ref=immutable(directory/'recovery-proof.json',(json.dumps(proof,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    current=json.loads(raw)
    error=current.pop('last_error')
    current.setdefault('resolved_errors',[]).append({'original_error':error,'resolution':KIND,'proof':proof_ref,'resolved_at':at})
    current['generated_record']={**row,'bound_by':KIND,'submitted_at':scope['submitted_at'],'identity_proof':proof_ref}
    current['record_url']=s.get('record_url') or tree.get('url')
    current.pop('waiting_for',None)
    current['updated_at']=at
    need(path.read_bytes()==raw,'artifact-recovery-concurrent-journal-change')
    write_json(path,current)
    return {'state':'reconciled','journal':ref(path),'proof':proof_ref,'phase':'pollRecords','ui_used':False,'bound':proof['facts']}
def _body(tree):
    def classes(n):return set(n.get('attributes',{}).get('class','').split())
    ns=list(d.nodes(tree))
    table=d.unique([n for n in ns if {'byted-table-container','byted-table-container-row'}<=classes(n)],'record-page-table-not-unique')
    scoped=list(d.nodes({'truncated':False,'root':table}))
    return d.unique([n for n in scoped if 'byted-table-body' in classes(n)],'record-page-body-not-unique')
def reconcile(job_path,original_sha256):
    job_path=strict_path(job_path)
    job=json.loads(job_path.read_bytes());path=strict_path(job['workflow_path'])
    with (path.parent/'.bridge-execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        return bind(job_path,original_sha256)
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--work-order',required=True)
    ap.add_argument('--original-sha256',required=True)
    a=ap.parse_args()
    result=reconcile(a.work_order,a.original_sha256)
    print(json.dumps(result,ensure_ascii=False,indent=1))
if __name__=='__main__':
    main()
