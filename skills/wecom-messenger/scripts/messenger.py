#!/usr/bin/env python3
"""WeCom text/file sender. Fixed CLI state machine; exact recipient allowlist.

prepare -> step/run -> status. Send intent is durable before any send action;
unknown outcomes are read-only reconciled, never retried automatically.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import performance_trace as performance
from zoneinfo import ZoneInfo
from native import Native,AXError
import ui

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'config/policy.json'
RUNTIME=ROOT.parents[1]/'runtime/wecom-messenger'
VERSION='1.0.0'
class SendError(RuntimeError):pass

def now():return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def atomic(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
@contextmanager
def lock(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    with open(directory/'.sender.lock','a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SendError('sender-busy')
        try:yield
        finally:fcntl.flock(f,fcntl.LOCK_UN)

def validate(job,policy):
    if job.get('kind') not in ('group','person') or not isinstance(job.get('target'),str) or not job['target'].strip():raise SendError('recipient-invalid')
    if job.get('scope') not in ('test','production'):raise SendError('scope-invalid')
    allowed=[r for r in policy['allowed_recipients'] if r['kind']==job['kind'] and r['name']==job['target'] and r.get('scope','test')==job['scope']]
    if len(allowed)!=1:raise SendError('recipient-not-authorized')
    if job['scope']=='production' and policy.get('production_enabled') is not True:raise SendError('production-disabled')
    if job.get('type')=='text':
        if not isinstance(job.get('text'),str) or not job['text'].strip() or len(job['text'])>10000 or '\x00' in job['text']:raise SendError('text-invalid')
    elif job.get('type')=='file':
        if policy.get('attachments_enabled') is not True:raise SendError('attachments-disabled')
        p=Path(job.get('file',''))
        if not p.is_absolute() or not p.is_file() or p.is_symlink() or not 0<p.stat().st_size<=20*1024*1024:raise SendError('file-invalid')
        if job.get('file_sha256')!=digest(p):raise SendError('file-changed')
    else:raise SendError('message-type-invalid')
    return job

def prepare(key,kind,target,text=None,file=None,scope='test',directory=RUNTIME):
    if not key or len(key)>160:raise SendError('idempotency-key-required')
    job={'version':VERSION,'key':key,'kind':kind,'target':target,'scope':scope,'type':'file' if file else 'text'}
    if file:
        source=Path(file).absolute()
        if source.is_symlink() or not source.is_file() or not 0<source.stat().st_size<=20*1024*1024:raise SendError('file-invalid')
        job.update(file=str(source),file_sha256=digest(source),file_name=source.name)
    else:job['text']=text
    policy=json.loads(POLICY.read_text());validate(job,policy)
    fingerprint=hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    path=Path(directory).resolve()/(hashlib.sha256(key.encode()).hexdigest()[:24]+'.json')
    with lock(path.parent):
        if path.exists():
            state=json.loads(path.read_text())
            if state['fingerprint']!=fingerprint:raise SendError('idempotency-conflict')
            return path,state
        state={'job':job,'fingerprint':fingerprint,'phase':'locate','status':'running','created_at':now(),
               'sent':False,'ui_confirmed':False,'delivery_confirmed':False,'events':[]}
        atomic(path,state);return path,state

def event(s,stage,**data):s['events'].append({'stage':stage,'at':now(),**data})
def finish(s):
    s.update(status='complete',phase='done',sent=True,ui_confirmed=True,completed_at=now())
    s.pop('error',None)
    event(s,'ui-confirmed',recipient=s['job']['target'],recipient_kind=s['job']['kind'])

def advance(path,native_factory=Native):
    path=Path(path).resolve()
    with lock(path.parent):
        s=json.loads(path.read_text());job=s['job'];validate(job,json.loads(POLICY.read_text()))
        with performance.sender_scope(s):
            # Check immutable job payload even if a caller edited the local JSON.
            if hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()!=s['fingerprint']:raise SendError('job-changed')
            if s['status'] in ('complete','failed','abandoned') or s.get('locate_input_intent'):return s
            native=None
            try:
                native=Native(s.get('pid'),capability_scope='sender-required') if native_factory is Native else native_factory()
                snapshot=native.chat_tree() if s['phase'] in ('verify-sent','image-verify-sent') and callable(getattr(native,'chat_tree',None)) else native.tree()
                s['last_read']={k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason','transcript_complete','discovery_node_count')}
                if 'capability_scope' in snapshot:s['last_read']['capability_scope']=snapshot['capability_scope']
                if s.get('pid') and snapshot['pid']!=s['pid']:raise SendError('app-process-changed')
                s['pid']=snapshot['pid'];phase=s['phase'];ctx=ui.locate_context(snapshot) if phase=='locate' else ui.context(snapshot)
                label=job.get('text') if job['type']=='text' else job['file_name']
                if s.get('text_parts'):
                    import text_parts
                    label=text_parts.validate(s)
                # Collapse the initial no-input phase segment in this same call. The
                # existing single-use full-snapshot ticket binds PID, native instance,
                # path map, input generation, target and immutable snapshot bytes.
                chain_read=None
                if s['status']=='running' and not s.get('error') and phase in ('locate','verify') and ctx['name']==job['target'] and ctx['kind']==job['kind'] and not s.get('send_intent_at'):
                    from files import stage_read
                    chain_read=stage_read(native,snapshot,job)
                    if chain_read is not None:
                        if phase=='locate':
                            s['phase']='verify';s['updated_at']=now();atomic(path,s);phase='verify'
                        ui.verify(ctx,job)
                        if ui.value(ctx['composer']):raise SendError('existing-draft-preserved')
                        # File names are display labels, not content fingerprints. Keep
                        # their count as the pre-paste baseline; job SHA and owned
                        # attachment confirmation still bind the new send.
                        s['baseline']=ui.message_count(ctx,label)
                        if job['type']=='text' and s['baseline']:raise SendError('same-content-already-visible')
                        event(s,'recipient-verified',name=ctx['name'],kind=ctx['kind']);s['phase']='stage';s['updated_at']=now();atomic(path,s);phase='stage'
                if phase=='locate':
                    if ctx['name']==job['target'] and ctx['kind']==job['kind']:s['phase']='verify'
                    else:
                        field=ui.search_field(ctx);query=ui.value(field)
                        if query and query!=job['target']:raise SendError('search-has-existing-input')
                        try:row=ui.recent_row(ctx,job['target'])
                        except ui.UIError as e:
                            if str(e)=='recipient-not-unique:0' and not s.get('searched'):
                                if query==job['target']:
                                    s['searched']=True;event(s,'search-reused',target=job['target'])
                                else:
                                    s.update(status='unknown',locate_input_intent={'kind':'search','pid':s['pid'],'target':job['target'],'path':field['path']});atomic(path,s)
                                    native.set_text(field,job['target']);s.pop('locate_input_intent');s['status']='running';s['searched']=True;event(s,'searched')
                            else:raise
                        else:
                            if 'AXSelected' not in row.get('settable',[]):raise SendError('recipient-row-not-selectable')
                            s.update(status='unknown',locate_input_intent={'kind':'select','pid':s['pid'],'target':job['target'],'path':row['path']});atomic(path,s)
                            native.flag(row,'AXSelected');s.pop('locate_input_intent');s['status']='running';s['phase']='verify';event(s,'selected',name=job['target'])
                elif phase=='verify':
                    ui.verify(ctx,job)
                    if ui.value(ctx['composer']):raise SendError('existing-draft-preserved')
                    s['baseline']=ui.message_count(ctx,label)
                    if job['type']=='text' and s['baseline']:raise SendError('same-content-already-visible')
                    event(s,'recipient-verified',name=ctx['name'],kind=ctx['kind']);s['phase']='stage'
                elif phase=='stage':
                    ui.verify(ctx,job)
                    owned_rejected=(s.get('text_parts',{}).get('index')==0 and s.get('length_rejection',{}).get('cancel_confirmed_at') and ui.value(ctx['composer'])==job.get('text'))
                    if ui.value(ctx['composer']) and not owned_rejected:raise SendError('existing-draft-preserved')
                    if job['type']=='text':
                        if chain_read is not None:ctx=chain_read.take(native,job)
                        if s.get('text_parts'):s['baseline']=ui.message_count(ctx,label)
                        native.set_text(ctx['composer'],label);s['phase']='ready';event(s,'draft-staged')
                    else:
                        from files import stage_file,stage_read
                        fresh=chain_read if chain_read is not None else stage_read(native,snapshot,job)
                        bound=stage_file(native,s,path,atomic,event) if fresh is None else stage_file(native,s,path,atomic,event,fresh_read=fresh)
                        if bound is not None:
                            # No input intervenes after the successful postpaste read.
                            # confirm_image still reads a complete fresh tree after
                            # focus and persists unknown Return intent before input.
                            from files import advance_file
                            advance_file(native,s,bound.take_snapshot(native,s),path,atomic,event,finish)
                elif phase=='ready':
                    ui.verify(ctx,job)
                    if ui.value(ctx['composer'])!=label:raise SendError('draft-changed')
                    native.focus(ctx['composer'])
                    # Re-read after focus, then persist irreversible intent BEFORE key event.
                    fresh=ui.context(native.tree());ui.verify(fresh,job)
                    if ui.value(fresh['composer'])!=label:raise SendError('draft-changed')
                    s.update(phase='verify-sent',status='unknown',send_intent_at=now());event(s,'send-intent');atomic(path,s)
                    native.key(36,13)
                elif phase=='image-verify-sent':
                    from images import verify_image
                    verify_image(s,ctx,event,finish)
                elif phase=='verify-sent':
                    ui.verify(ctx,job)
                    count=ui.message_count(ctx,label)
                    if count>s['baseline'] and not ui.value(ctx['composer']):
                        if s.get('text_parts'):
                            from text_parts import confirm
                            confirm(s,event,finish,count)
                        else:finish(s)
                    else:
                        if not s.get('text_parts') and ui.value(ctx['composer'])==job.get('text'):
                            from text_parts import recover_rejection
                            if recover_rejection(native,s,path,atomic,event):
                                atomic(path,s);return s
                        s['checks']=s.get('checks',0)+1
                        if s['checks']>=5:s['status']='unknown';s['error']='send-outcome-unknown'
                elif phase=='text-limit-cancel-pending':
                    from text_parts import finish_cancel
                    finish_cancel(native,s,event)
                elif phase.startswith('file-'):
                    from files import advance_file
                    advance_file(native,s,snapshot,path,atomic,event,finish)
                else:raise SendError('phase-invalid')
            except (AXError,ui.UIError,SendError,OSError,RuntimeError) as error:
                if s.get('send_intent_at') or s.get('locate_input_intent'):s.update(status='unknown',error=str(error))
                else:s.update(status='failed',error=str(error))
                event(s,'stopped',error=str(error))
            finally:
                if native:
                    if getattr(native,'last_snapshot_metadata',None):s['last_read']=dict(native.last_snapshot_metadata)
                    native.close()
            s['updated_at']=now();atomic(path,s);return s

def summary(path,s):return {'job_path':str(Path(path).resolve()),'status':s['status'],'phase':s['phase'],
    'target':s['job']['target'],'kind':s['job']['kind'],'type':s['job']['type'],'sent':s['sent'],
    'ui_confirmed':s['ui_confirmed'],'delivery_confirmed':s['delivery_confirmed'],'error':s.get('error'),'last_read':s.get('last_read')}

def initial_locate_failure(s):
    events=s.get('events',[])
    return (s.get('status')=='failed' and s.get('phase')=='locate' and s.get('pid') is None and s.get('error')=='app-not-running-or-ambiguous' and len(events)==1 and events[0].get('stage')=='stopped' and events[0].get('error')==s['error'] and not any(s.get(k) for k in ('sent','ui_confirmed','delivery_confirmed','automated_send','user_sent','last_read','completed_at','receipt','image_proof','result')) and not any(v and any(word in k.lower() for word in ('intent','paste','choice','return','receipt','unknown')) for k,v in s.items()))
def initial_resume_archive(path,raw):
    directory=path.parent/'.initial-locate-resume'/path.stem/hashlib.sha256(raw).hexdigest();directory.mkdir(parents=True,exist_ok=True);p=directory/'original.json'
    try:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except FileExistsError:
        if p.is_symlink() or p.read_bytes()!=raw:raise SendError('initial-resume-original-changed')
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest()}

INITIAL_LOCATE_DIAGNOSTIC_SHA='9ea972b4b397c1ea12f4f00a19b1091522ac67b6564867ad8fd1f3fbec836d27'
def initial_locate_diagnostic(path,state):
    """Diagnostic-only child of the same Host worker; original sender untouched."""
    import subprocess
    script=Path(__file__).with_name('diagnose_locate.py')
    if script.is_symlink() or digest(script)!=INITIAL_LOCATE_DIAGNOSTIC_SHA:raise SendError('initial-locate-diagnostic-source-changed')
    directory=os.environ.get('WECOM_PERFORMANCE_DIR')
    if not directory or not Path(directory).is_absolute():raise SendError('initial-locate-diagnostic-attempt-directory-required')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    if directory.is_symlink() or directory.resolve()!=directory:raise SendError('initial-locate-diagnostic-directory-alias')
    try:
        result=subprocess.run([sys.executable,'-I','-B',str(script),'--expected-pid','636'],capture_output=True,text=True,timeout=20)
        value=json.loads(result.stdout);returncode=result.returncode
    except subprocess.TimeoutExpired:
        value={'kind':'wecom-initial-locate-public-diagnostic-v1','status':'diagnostic-timeout','timeout_seconds':20,'UI_input_used':False};returncode=None
    if value.get('kind')!='wecom-initial-locate-public-diagnostic-v1' or value.get('UI_input_used') is not False:raise SendError('initial-locate-diagnostic-output-invalid')
    record={'kind':'same-host-initial-locate-failure-diagnostic-v1','script':{'path':str(script),'sha256':INITIAL_LOCATE_DIAGNOSTIC_SHA},'sender':{'path':str(path),'sha256':digest(path)},'sender_fingerprint':state['fingerprint'],'diagnostic_returncode':returncode,'diagnostic':value,'original_error_preserved':True,'new_inputs':0}
    output=directory/('initial-locate-'+state['fingerprint'][:16]+'-'+__import__('uuid').uuid4().hex+'.json');atomic(output,record);return {'path':str(output),'sha256':digest(output)}

def resume_before_send(path,native_factory=Native):
    path=Path(path).resolve()
    with lock(path.parent):
        original_raw=path.read_bytes();s=json.loads(original_raw);validate(s['job'],json.loads(POLICY.read_text()))
        intent_keys=[k for k,v in s.items() if v and any(word in k.lower() for word in ('intent','paste','choice','return'))]
        intent_events=[e for e in s.get('events',[]) if any(word in str(e.get('stage','')).lower() for word in ('intent','paste','choice','return','confirmed'))]
        if s['status']!='failed' or intent_keys or intent_events or s.get('sent') or s.get('ui_confirmed') or s.get('automated_send') or s.get('user_sent') or s.get('image_proof') or s['phase'] not in ('locate','verify','stage','file-dialog'):raise SendError('resume-not-safe')
        if hashlib.sha256(json.dumps(s['job'],ensure_ascii=False,sort_keys=True).encode()).hexdigest()!=s['fingerprint']:raise SendError('job-changed')
        initial=initial_locate_failure(s);original_ref=initial_resume_archive(path,original_raw) if initial else None
        try:n=Native(s.get('pid')) if native_factory is Native else native_factory()
        except AXError as error:
            if initial and str(error)=='app-not-running-or-ambiguous':
                try:initial_locate_diagnostic(path,s)
                except Exception:pass # Diagnostics never replace the original failed constructor.
            raise
        try:
            snap=n.tree()
            try:ctx=ui.locate_context(snap) if initial else ui.context(snap)
            except ui.UIError as error:
                if initial:
                    # Persist only metadata from this already-read tree. No new AX read.
                    output=Path(original_ref['path']).with_name('startup-rejection-'+__import__('uuid').uuid4().hex+'.json')
                    atomic(output,{'kind':'initial-startup-context-rejection-v1','original':original_ref,'error':str(error),'snapshot_sha256':hashlib.sha256(json.dumps(snap,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'observation':ui.startup_rejection_summary(snap),'ui_input_used':False})
                raise
            if (type(snap.get('pid')) is not int or snap['pid']<=0 or snap['pid']!=getattr(n,'pid',None) if initial else snap['pid']!=s.get('pid')) or (not ctx.get('navigation_only') and ui.value(ctx['composer'])):raise SendError('resume-context-unverified')
            if s['phase'] in ('verify','stage'):ui.verify(ctx,s['job'])
            s['last_read']={k:snap.get(k) for k in ('read_scope','node_count','truncated','truncation_reason')}
            if initial:
                snapshot_path=Path(original_ref['path']).with_name('fresh.json');atomic(snapshot_path,snap);s['pid']=snap['pid'];s['initial_process_binding']={'kind':'verified-initial-locate-process-binding-v1','original':original_ref,'fresh':{'path':str(snapshot_path),'sha256':digest(snapshot_path)},'pid':snap['pid'],'ui_input_used':False}
        finally:n.close()
        if initial and path.read_bytes()!=original_raw:raise SendError('resume-original-concurrent-change')
        s.update(status='running',phase='locate');s.pop('error',None);event(s,'resumed-before-send');atomic(path,s);return s

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('tree')
    prep=sub.add_parser('prepare');prep.add_argument('--key',required=True);prep.add_argument('--kind',choices=['group','person'],required=True);prep.add_argument('--target',required=True)
    content=prep.add_mutually_exclusive_group(required=True);content.add_argument('--text');content.add_argument('--text-file');content.add_argument('--file')
    prep.add_argument('--scope',choices=['test','production'],default='test');prep.add_argument('--directory',default=str(RUNTIME))
    for verb in ['step','run','status','resume']:
        child=sub.add_parser(verb);child.add_argument('--job',required=True)
    draft_recovery=sub.add_parser('recover-image-draft');draft_recovery.add_argument('--job',required=True)
    repair_parser=sub.add_parser('repair-image-paste');repair_parser.add_argument('--job',required=True);repair_parser.add_argument('--report',required=True);repair_parser.add_argument('--report-sha256',required=True)
    a=p.parse_args()
    try:
        if a.command in ('doctor','tree'):
            native=Native()
            try:
                result=native.tree()
                if a.command=='doctor':
                    ctx=ui.context(result);result={'ok':True,'bundle_id':result['bundle_id'],'accessibility_trusted':True,'current_chat_kind':ctx['kind'],'current_chat':ctx['name'],'draft_present':bool(ui.value(ctx['composer'])),'coordinate_actions':False}
            finally:native.close()
        elif a.command=='prepare':
            text=Path(a.text_file).read_text() if a.text_file else a.text
            path,s=prepare(a.key,a.kind,a.target,text,a.file,a.scope,a.directory);result=summary(path,s)
        elif a.command=='status':result=summary(a.job,json.loads(Path(a.job).read_text()))
        elif a.command=='recover-image-draft':
            from image_draft_recovery import recover
            result=summary(a.job,recover(a.job))
        elif a.command=='repair-image-paste':
            from image_paste_repair import repair
            result=summary(a.job,repair(a.job,{'path':str(Path(a.report).resolve()),'sha256':a.report_sha256}))
        elif a.command=='resume':result=summary(a.job,resume_before_send(a.job))
        else:
            s=advance(a.job)
            if a.command=='run':
                budget=15
                if s['job']['type']=='text'and len(s['job']['text'].encode())>1900:
                    from text_parts import split
                    budget=max(budget,len(split(s['job']['text']))*4+8)
                for _ in range(budget):
                    if s['status'] in ('complete','failed','abandoned') or s.get('error'):break
                    time.sleep(0.5);s=advance(a.job)
            result=summary(a.job,s)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result.get('status') not in ('failed','unknown') else 2
    except (SendError,AXError,ui.UIError,OSError,ValueError) as error:
        print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=False));return 2

if __name__=='__main__':
    # Recovery helpers import this module; keep one SendError/state-machine identity.
    sys.modules['messenger']=sys.modules[__name__]
    raise SystemExit(main())
