#!/usr/bin/env python3
"""Typed read-only pre-input recovery. No sending or UI mutation capability."""
import argparse
import hashlib
import json
import os
from datetime import datetime,timezone
import re
import uuid
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
SCRIPTS=HERE if (HERE/'messenger.py').exists() else HERE.parents[2]/'skills/wecom-messenger/scripts'
sys.path.insert(0,str(SCRIPTS))
import messenger as m
import ui
KIND='verified-wecom-preinput-read-recovery-v1'
FIELD='sender_preinput_recovery'
def need(v,code):
    if not v:raise ValueError(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def strict(p):
    p=Path(p);need(p.is_absolute() and p==p.resolve() and not p.is_symlink() and not any(x.is_symlink() for x in p.parents),'recovery-path-invalid');return p
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def document(r):
    p=strict(r['path']);b=p.read_bytes();need(sha(b)==r['sha256'],'recovery-ref-changed');return json.loads(b)
def publish(p,x):
    if p.exists():need(json.loads(p.read_text())==x,'recovery-evidence-conflict')
    else:m.atomic(p,x)
    return ref(p)
def original(s,p):
    need(p.parent==m.RUNTIME.resolve() and p.name==sha(s['job']['key'].encode())[:24]+'.json','recovery-canonical-job-required')
    need(s.get('status')=='failed' and s.get('phase') in ('locate','verify','stage') and s.get('error')=='ui-tree-incomplete','recovery-original-error-required')
    need(s.get('last_read',{}).get('truncated') is True and s['last_read'].get('truncation_reason')=='scoped-required-array-unavailable:AXChildren','recovery-original-read-required')
    need(type(s.get('pid')) is int and s['pid']>0,'recovery-pid-required')
    job=s['job'];m.validate(job,json.loads(m.POLICY.read_text()))
    need(job.get('kind')=='group' and job.get('scope')=='test' and job.get('target')=='测试群请忽略' and job.get('type')=='file','recovery-test-file-only')
    need(sha(json.dumps(job,ensure_ascii=False,sort_keys=True).encode())==s['fingerprint'],'recovery-fingerprint-mismatch')
    need(not any(v for k,v in s.items() if any(w in k.lower() for w in ('intent','paste','choice','return'))),'recovery-input-intent-present')
    need(not any(any(w in str(e.get('stage','')).lower() for w in ('intent','paste','choice','return','confirmed')) for e in s.get('events',[])),'recovery-input-event-present')
    need(not any(s.get(k) for k in ('sent','ui_confirmed','delivery_confirmed','automated_send','user_sent','image_proof')),'recovery-send-present')
def snapshot_check(snap,s):
    need(snap.get('read_scope')=='application-windows-complete' and snap.get('pid')==s['pid'],'recovery-full-snapshot-pid-required')
    ctx=ui.context(snap);ui.verify(ctx,s['job'])
    need(not ui.value(ctx['composer']) and not any(n.get('role')=='AXTextAttachment' or n.get('AXSubrole')=='AXTextAttachment' for n in ui.nodes(ctx['composer'])),'recovery-composer-not-empty')
    need(not any(n.get('role')=='AXSheet' or n.get('AXSubrole')=='AXDialog' for n in ui.nodes(snap['tree'])),'recovery-modal-present')
def expected_delta(current,old,snap):
    events=current.get('events',[]);need(len(events)==len(old.get('events',[]))+1 and events[:-1]==old.get('events',[]) and set(events[-1])=={'stage','at'} and events[-1]['stage']=='resumed-before-send','recovery-event-delta-invalid')
    expected=dict(old);expected.update(status='running',phase='locate',events=events,last_read={k:snap.get(k) for k in ('read_scope','node_count','truncated','truncation_reason')});expected.pop('error',None)
    actual=dict(current);actual.pop(FIELD,None)
    need(actual==expected,'recovery-state-delta-invalid')
def verify_recovered(current,proof_ref):
    proof=document(proof_ref);need(proof.get('kind')==KIND and proof.get('ui_used') is False and proof.get('new_inputs')==0 and proof.get('next_phase')=='locate','recovery-proof-contract-invalid')
    at=datetime.fromisoformat(proof['at']);need(at.utcoffset()==timezone.utc.utcoffset(at),'recovery-proof-utc-required')
    old=document(proof['original_journal']);p=strict(proof['canonical_job_path']);original(old,p)
    base=p.parent/'preinput-read-recovery'/proof['original_sha256']
    need(strict(proof_ref['path'])==base/'recovery-proof.json' and strict(proof['original_journal']['path'])==base/'original-journal.json' and re.fullmatch(r'[0-9a-f]{32}',proof.get('attempt','')) and strict(proof['fresh_snapshot']['path'])==base/'attempts'/proof['attempt']/'fresh-snapshot.json','recovery-proof-path-invalid')
    need(proof['original_journal']['sha256']==proof['original_sha256'],'recovery-original-sha-mismatch')
    snap=document(proof['fresh_snapshot']);snapshot_check(snap,old);expected_delta(current,old,snap)
    need(current.get(FIELD)==proof_ref,'recovery-proof-binding-invalid')
    return {'kind':KIND,'original_journal':proof['original_journal'],'proof':proof_ref,'original_error':{'code':old['error'],'message':old['error']}}
def reconcile(path,original_sha256,native_factory=None):
    p=strict(path);base=p.parent/'preinput-read-recovery'/original_sha256
    # resume_before_send owns the sender lock. The supplied capability has only
    # tree/close, verifies original bytes under that lock, and archives before read.
    b=p.read_bytes();s=json.loads(b)
    if s.get(FIELD):
        need(document(s[FIELD]).get('original_sha256')==original_sha256,'recovery-original-sha-mismatch');return verify_recovered(s,s[FIELD])
    archive=base/'original-journal.json';attempt=uuid.uuid4().hex;fresh=base/'attempts'/attempt/'fresh-snapshot.json'
    resumed=None
    if sha(b)!=original_sha256:
        need(archive.exists() and sha(archive.read_bytes())==original_sha256,'recovery-original-sha-mismatch')
        old=json.loads(archive.read_text());original(old,p);matches=[]
        candidates=sorted((base/'attempts').glob('*/fresh-snapshot.json'));need(len(candidates)<=64,'recovery-too-many-snapshots')
        for candidate in candidates:
            need(re.fullmatch(r'[0-9a-f]{32}',candidate.parent.name),'recovery-attempt-path-invalid')
            snap=document(ref(candidate))
            try:snapshot_check(snap,old);expected_delta(s,old,snap)
            except (ValueError,ui.UIError):continue
            matches.append(candidate)
        need(len(matches)==1,'recovery-resume-snapshot-not-unique')
        fresh=matches[0];attempt=fresh.parent.name;resumed=s;s=old
    else:original(s,p)
    class ReadOnly:
        def __init__(self):
            need(p.read_bytes()==b,'recovery-concurrent-job-change')
            archive.parent.mkdir(parents=True,exist_ok=True)
            if archive.exists():need(archive.read_bytes()==b,'recovery-archive-conflict')
            else:
                with archive.open('xb') as stream:stream.write(b);stream.flush();os.fsync(stream.fileno())
            self.n=(native_factory or m.Native)(s['pid'])
        def tree(self):
            snap=self.n.tree();publish(fresh,snap);snapshot_check(snap,s)
            need(p.read_bytes()==b,'recovery-concurrent-job-change');return snap
        def close(self):self.n.close()
    # A crash after the existing resume commit is recoverable from its exact delta;
    # no second UI read or fabricated resume event is needed.
    out=resumed if resumed is not None else m.resume_before_send(p,native_factory=ReadOnly);committed=p.read_bytes()
    proof={'kind':KIND,'at':datetime.now(timezone.utc).isoformat(),'attempt':attempt,'canonical_job_path':str(p),'original_sha256':original_sha256,'original_journal':ref(archive),'fresh_snapshot':ref(fresh),'ui_used':False,'new_inputs':0,'next_phase':'locate'}
    with m.lock(p.parent):
        need(p.read_bytes()==committed,'recovery-concurrent-job-change');expected_delta(out,s,document(proof['fresh_snapshot']))
        proof_path=base/'recovery-proof.json'
        if proof_path.exists():
            saved=document(ref(proof_path));expected=dict(proof);expected['at']=saved.get('at');need(saved==expected,'recovery-proof-conflict');proof=saved
        pr=publish(proof_path,proof);out[FIELD]=pr;verify_recovered(out,pr);m.atomic(p,out)
    return {'state':'reconciled','journal':ref(p),'proof':pr,'phase':'locate','ui_used':False}
def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--job',required=True);a.add_argument('--original-sha256',required=True);args=a.parse_args()
    try:print(json.dumps(reconcile(Path(args.job),args.original_sha256),ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
