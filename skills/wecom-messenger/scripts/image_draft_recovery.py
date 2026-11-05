"""One same-job, no-repaste recovery of an owned image draft after process exit."""
import hashlib,json,os,re
from pathlib import Path
import ui,images
from image_draft_copy import copy_selected_image

def input_source_indicator(node,ctx):
    # Observed macOS IME indicator is a separate window, never a send dialog.
    children=node.get('children',[])
    return (node.get('role')=='AXWindow' and node.get('AXSubrole')=='AXDialog' and node.get('path')!=ctx['window'].get('path') and node.get('AXMain') is not True and not ui.value(node) and len(children)==1 and children[0].get('role')=='AXButton' and children[0].get('AXIdentifier')=='InputSource' and children[0].get('AXDescription')=='com.apple.inputmethod.SCIM.ITABC' and children[0].get('AXEnabled') is True and not children[0].get('children') and not children[0].get('AXValue') and not children[0].get('AXTitle'))

def binding_hash(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def seed_original(s):
    import messenger as m
    seed=s.get('image_paste_seed');job=s['job']
    def need(ok):
        if not ok:raise m.SendError('image-seed-recovery-original-chain-invalid')
    m.validate(job,json.loads(m.POLICY.read_text()))
    need(job.get('scope')=='test' and job.get('kind')=='group' and images.is_image(job))
    need(s.get('sent') is False and s.get('ui_confirmed') is False and s.get('delivery_confirmed') is False)
    need(not any(k in s for k in ('owned_image_paste','image_proof','image_return_intent_at','original_file_choice_intent_at','draft_copy_recovery','seed_copy_staging','image_receipt','automated_send')))
    need(s.get('status')=='unknown' and s.get('phase')=='file-confirm' and s.get('error')=='image-paste-seed-or-transcript-changed' and not s.get('owned_image_paste'))
    need(s.get('paste_empty_composer_verified') is True and bool(s.get('send_intent_at')) and type(s.get('pid')) is int)
    need(isinstance(seed,dict) and set(seed)=={'source_sha256','pid','target','kind','clipboard','transcript','empty_composer_verified','ownership_session'})
    need(all(seed.get(k)==v for k,v in {'source_sha256':job['file_sha256'],'pid':s['pid'],'target':job['target'],'kind':job['kind'],'empty_composer_verified':True}.items()))
    need(isinstance(seed['ownership_session'],str) and re.fullmatch('[0-9a-f]{32}',seed['ownership_session']) is not None)
    cb=seed['clipboard'];need(isinstance(cb,dict) and set(cb)=={'change_count','types','file_url_verified'} and type(cb['change_count']) is int and cb['change_count']>=0 and cb['types']==['public.file-url'] and cb['file_url_verified'] is True)
    need(isinstance(seed['transcript'],list) and all(isinstance(x,str) and re.fullmatch('[0-9a-f]{64}',x) for x in seed['transcript']))
    events=s.get('events',[]);send=[e for e in events if e.get('stage')=='send-intent'];persist=[e for e in events if e.get('stage')=='image-paste-seed-persisted'];recipient=[e for e in events if e.get('stage')=='recipient-verified']
    need(len(send)==len(persist)==1 and send[0].get('sha256')==job['file_sha256'] and send[0].get('file')==job['file_name'] and send[0].get('at')==s['send_intent_at'] and persist[0].get('source_sha256')==job['file_sha256'] and bool(recipient) and all(e.get('name')==job['target'] and e.get('kind')==job['kind'] for e in recipient))
    need(not any(s.get(k) for k in ('sent','ui_confirmed','delivery_confirmed','image_proof','image_return_intent_at','original_file_choice_intent_at','draft_copy_recovery','seed_copy_staging','image_receipt','automated_send')))
    need(not any(e.get('stage') in ('file-pasted','owned-image-paste-bound','image-seed-copy-staging-verified') or any(w in str(e.get('stage','')) for w in ('return','confirm-intent','choice-intent','copy-recovery')) for e in events))
    return seed

def seed_copy_proof(proof,job):
    return (isinstance(proof,dict) and proof.get('method')=='public-selected-image-copy-exact-decoded-RGBA' and proof.get('source_sha256')==job['file_sha256'] and all(type(proof.get(k)) is int and proof[k]>0 for k in ('width','height')) and isinstance(proof.get('rgba_sha256'),str) and re.fullmatch('[0-9a-f]{64}',proof['rgba_sha256']) is not None and all(type(proof.get(k)) is int and proof[k]>=0 for k in ('clipboard_before_change_count','clipboard_copy_change_count')) and proof['clipboard_copy_change_count']>proof['clipboard_before_change_count'] and proof.get('clipboard_format') in ('public.png','public.tiff','public.file-url-selected-image') and proof.get('clipboard_restore')=='only-if-still-owned')

def context_binding(ctx,pid):
    return {'window':{'pid':pid,'role':ctx['window']['role'],'title':ui.value(ctx['window'])},'header':{'name':ctx['name'],'kind':ctx['kind']},'composer':{'role':ctx['composer']['role'],'attachment':images.attachment_shape(ctx)},'transcript':{'role':ctx['transcript']['role']}}

def seed_context(snapshot,ctx,pid,paths=None):
    import messenger as m
    if snapshot.get('pid')!=pid:raise m.SendError('image-draft-recovery-process-changed')
    actual=context_binding(ctx,pid)
    if paths is not None and actual!=paths:raise m.SendError('image-seed-recovery-window-or-session-changed')
    for n in ui.nodes(snapshot['tree']):
        if n.get('role')=='AXWindow' and n.get('path')!=ctx['window']['path'] and not input_source_indicator(n,ctx):raise m.SendError('image-seed-recovery-extra-window')
        if (n.get('role') in ('AXSheet','AXDialog') or n.get('AXSubrole')=='AXDialog') and not input_source_indicator(n,ctx):raise m.SendError('image-draft-recovery-dialog-present')
    return actual

def verify_seed_staging(s,ctx,*,snapshot=None):
    """Typed qualification only; never manufactures original file-pasted history."""
    import messenger as m
    def need(ok):
        if not ok:raise ui.UIError('image-seed-copy-staging-unverified')
    stage=s.get('seed_copy_staging');owned=s.get('owned_image_paste');recovery=s.get('draft_copy_recovery');job=s['job']
    need(isinstance(stage,dict) and isinstance(owned,dict) and isinstance(recovery,dict))
    need(set(stage)=={'kind','job_path','fingerprint','original_job','seed_sha256','ownership_session','copy_proof_sha256','owned_binding_sha256','ui_paths'})
    need(stage.get('kind')=='verified-seed-only-image-staging-v1' and stage.get('fingerprint')==s.get('fingerprint')==binding_hash(job) and stage.get('ownership_session')==images.OWNERSHIP_SESSION)
    path=Path(stage.get('job_path',''));need(path.is_absolute() and path.parent==m.RUNTIME.resolve() and path.resolve()==path and not path.is_symlink() and path.name==hashlib.sha256(job['key'].encode()).hexdigest()[:24]+'.json')
    original_ref=stage.get('original_job');need(isinstance(original_ref,dict) and original_ref==recovery.get('original_job') and original_ref.get('path')==str(path.with_name(path.stem+'.before-draft-copy-recovery.json')))
    archive=Path(original_ref['path']);need(archive.is_file() and not archive.is_symlink() and archive.resolve()==archive)
    original=archive.read_bytes();need(hashlib.sha256(original).hexdigest()==original_ref.get('sha256'));old=json.loads(original);seed=seed_original(old)
    need(old['job']==job and old['pid']==s['pid'] and old['fingerprint']==s['fingerprint'] and s.get('image_paste_seed')==seed and stage.get('seed_sha256')==binding_hash(seed))
    copy=owned.get('copy_proof');need(owned.get('method')=='public-selected-image-copy-exact-decoded-RGBA' and recovery.get('method')=='public-sole-image-copy-no-repaste' and recovery.get('qualification')=='seed-only-exact-copy-v1' and seed_copy_proof(copy,job) and copy==recovery.get('proof') and recovery.get('state')=='source-verified' and stage.get('copy_proof_sha256')==binding_hash(copy))
    need(stage.get('owned_binding_sha256')==owned.get('binding_sha256')==binding_hash({k:v for k,v in owned.items() if k!='binding_sha256'}) and owned.get('ownership_session')==images.OWNERSHIP_SESSION)
    need(all(owned.get(k)==seed[k] for k in ('source_sha256','pid','target','kind','clipboard')) and images.same_frontier(owned.get('transcript'),seed['transcript']) and owned.get('attachment')==images.attachment_shape(ctx) and images.same_frontier(images.baseline(ctx),seed['transcript']) and ctx['name']==job['target'] and ctx['kind']==job['kind'])
    need(stage.get('ui_paths')==owned.get('ui_paths')==context_binding(ctx,s['pid']))
    if snapshot is not None:seed_context(snapshot,ctx,s['pid'],stage['ui_paths'])
    need(owned.get('original_seed_sha256')==binding_hash(seed) and owned.get('original_state_sha256')==original_ref['sha256'] and recovery.get('original_seed_sha256')==binding_hash(seed))
    events=[e for e in s.get('events',[]) if e.get('stage')=='image-seed-copy-staging-verified'];need(len(events)==1 and events[0].get('staging_sha256')==binding_hash(stage))
    need(json.loads(path.read_bytes())==s and archive.read_bytes()==original)
    return stage

def recover(path,native_factory=None,copy_verifier=copy_selected_image,*,original_sha256=None):
    import messenger as m
    supplied_path=Path(path);path=supplied_path.resolve()
    with m.lock(path.parent):
        original=path.read_bytes();s=json.loads(original);job=s['job'];m.validate(job,json.loads(m.POLICY.read_text()))
        if hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()!=s['fingerprint']:raise m.SendError('job-changed')
        # The original recipient remains bound and authorized by m.validate above.
        reinspect=(s.get('error')=='image-seed-recovery-window-or-session-changed' and s.get('draft_copy_recovery',{}).get('state')=='unknown' and not s.get('draft_copy_recovery',{}).get('reinspection'))
        if s.get('status')!='unknown' or s.get('phase')!='file-confirm' or job.get('scope')!='test' or job.get('kind')!='group' or not images.is_image(job) or s.get('error') not in ('image-owned-paste-draft-or-transcript-changed','image-paste-session-ended-no-replay','image-paste-seed-or-transcript-changed','image-seed-recovery-window-or-session-changed'):raise m.SendError('image-draft-recovery-scope-invalid')
        if s.get('sent') or s.get('ui_confirmed') or s.get('image_proof') or s.get('image_return_intent_at') or s.get('original_file_choice_intent_at') or (s.get('draft_copy_recovery') and not reinspect) or any(any(w in str(e.get('stage','')) for w in ('return','confirm-intent','choice-intent')) for e in s.get('events',[])):raise m.SendError('image-draft-recovery-send-or-copy-intent-exists')
        proof=s.get('owned_image_paste');seed=s.get('image_paste_seed')
        seed_only=proof is None and (s.get('error')=='image-paste-seed-or-transcript-changed' or reinspect)
        if seed_only:
            if original_sha256!=hashlib.sha256(original).hexdigest() or path.parent!=m.RUNTIME.resolve() or supplied_path!=path or supplied_path.is_symlink() or path.name!=hashlib.sha256(job['key'].encode()).hexdigest()[:24]+'.json':raise m.SendError('image-seed-recovery-original-sha-or-path-required')
            if reinspect:
                prior=s['draft_copy_recovery']['original_job'];data=Path(prior['path']).read_bytes()
                if hashlib.sha256(data).hexdigest()!=prior['sha256']:raise m.SendError('image-reinspection-original-changed')
                old=json.loads(data);seed_original(old)
                if old['job']!=job or old['image_paste_seed']!=seed:raise m.SendError('image-reinspection-current-source-changed')
            else:seed_original(s)
            content=None
        else:
            if not isinstance(proof,dict) or not isinstance(seed,dict):raise m.SendError('image-draft-recovery-owned-seed-required')
            content={k:v for k,v in proof.items() if k!='binding_sha256'}
            if proof.get('binding_sha256')!=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True).encode()).hexdigest():raise m.SendError('image-draft-recovery-proof-corrupt')
            for k,v in {'source_sha256':job['file_sha256'],'pid':s['pid'],'target':job['target'],'kind':job['kind']}.items():
                if proof.get(k)!=v or seed.get(k)!=v:raise m.SendError('image-draft-recovery-original-scope-mismatch')
            if seed.get('clipboard')!=proof.get('clipboard') or not images.same_frontier(seed.get('transcript'),proof.get('transcript')) or seed.get('empty_composer_verified') is not True:raise m.SendError('image-draft-recovery-seed-chain-invalid')
        if hashlib.sha256(Path(job['file']).read_bytes()).hexdigest()!=job['file_sha256']:raise m.SendError('image-draft-recovery-source-changed')
        native=m.Native(s['pid']) if native_factory is None else native_factory()
        try:
            attachment=None;ui_paths=None
            def current():
                nonlocal attachment,ui_paths
                snap=native.tree()
                if snap.get('pid')!=s['pid']:raise m.SendError('image-draft-recovery-process-changed')
                ctx=ui.context(snap);ui.verify(ctx,job)
                if seed_only:
                    if json.loads(path.read_bytes())!=s:raise m.SendError('image-seed-recovery-job-changed-before-input')
                    ui_paths=seed_context(snap,ctx,s['pid'],ui_paths)
                    if attachment is None:attachment=images.attachment_shape(ctx)
                if any((n.get('role') in ('AXSheet','AXDialog') or n.get('AXSubrole')=='AXDialog') and not input_source_indicator(n,ctx) for n in ui.nodes(snap['tree'])):raise m.SendError('image-draft-recovery-dialog-present')
                if images.attachment_shape(ctx)!=(attachment if seed_only else proof['attachment']) or not images.same_frontier(images.baseline(ctx),seed['transcript']):raise m.SendError('image-draft-recovery-original-draft-or-transcript-changed')
                return ctx
            ctx=current();archive=path.with_name(path.stem+'.before-draft-copy-recovery.json')
            if archive.exists()and not reinspect:raise m.SendError('image-draft-recovery-archive-exists')
            if path.read_bytes()!=original:raise m.SendError('image-draft-recovery-original-job-changed')
            if not reinspect:
                with archive.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
            s['draft_copy_recovery']={'state':'unknown','intent_at':m.now(),'original_job':{'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()},**({'reinspection':{'prior_copy_outcome':'unknown-read-only-inspection','original_error':s['error'],'at':m.now()}}if reinspect else{}),**({'original_seed_sha256':binding_hash(seed),'qualification':'seed-only-exact-copy-v1'} if seed_only else {'original_owned_binding_sha256':proof['binding_sha256']}),'method':'public-sole-image-copy-no-repaste'}
            m.event(s,'image-draft-copy-recovery-intent');m.atomic(path,s)
            copy_started=False
            def copy_action():
                nonlocal copy_started
                if copy_started:raise m.SendError('image-draft-recovery-copy-action-already-used')
                copy_started=True
                native.focus(current()['composer']);native.key(0,ord('a'),command=True)
                native.focus(current()['composer']);native.key(8,ord('c'),command=True)
            verified=copy_verifier(job,copy_action)
            if verified.get('method')!='public-selected-image-copy-exact-decoded-RGBA' or verified.get('source_sha256')!=job['file_sha256'] or type(verified.get('clipboard_before_change_count')) is not int or type(verified.get('clipboard_copy_change_count')) is not int or verified['clipboard_copy_change_count']==verified['clipboard_before_change_count']:raise m.SendError('image-draft-recovery-copy-proof-invalid')
            if seed_only and (not copy_started or not seed_copy_proof(verified,job)):raise m.SendError('image-draft-recovery-copy-proof-invalid')
            fresh=current()
            if seed_only:content={k:seed[k] for k in ('source_sha256','pid','target','kind','clipboard','transcript')};content.update(attachment=attachment,ui_paths=ui_paths,original_seed_sha256=binding_hash(seed),original_state_sha256=s['draft_copy_recovery']['original_job']['sha256'])
            new={**content,'method':'public-selected-image-copy-exact-decoded-RGBA','ownership_session':images.OWNERSHIP_SESSION,'copy_proof':verified,'original_binding_sha256':binding_hash(seed) if seed_only else proof['binding_sha256'],'transcript':images.baseline(fresh)}
            new['binding_sha256']=hashlib.sha256(json.dumps(new,ensure_ascii=False,sort_keys=True).encode()).hexdigest();s['owned_image_paste']=new;s['draft_copy_recovery'].update(state='source-verified',proof=verified,verified_at=m.now());m.event(s,'image-draft-copied-source-verified',source_sha256=job['file_sha256']);m.atomic(path,s)
            if seed_only:
                stage={'kind':'verified-seed-only-image-staging-v1','job_path':str(path),'fingerprint':s['fingerprint'],'original_job':s['draft_copy_recovery']['original_job'],'seed_sha256':binding_hash(seed),'ownership_session':images.OWNERSHIP_SESSION,'copy_proof_sha256':binding_hash(verified),'owned_binding_sha256':new['binding_sha256'],'ui_paths':ui_paths}
                s['seed_copy_staging']=stage;m.event(s,'image-seed-copy-staging-verified',staging_sha256=binding_hash(stage));m.atomic(path,s)
            images.confirm_image(native,s,fresh,path,m.atomic,m.event)
        except (ui.UIError,RuntimeError,OSError,ValueError) as e:
            if s.get('draft_copy_recovery'):
                s.update(status='unknown',error=str(e));m.event(s,'stopped',error=str(e));m.atomic(path,s)
            raise m.SendError(str(e)) from e
        finally:native.close()
        s['updated_at']=m.now();m.atomic(path,s);return s

if __name__=='__main__':
    import argparse,messenger as m
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--job',required=True);parser.add_argument('--original-sha256',required=True);args=parser.parse_args()
    try:
        state=recover(args.job,original_sha256=args.original_sha256);print(json.dumps({'phase':state['phase'],'status':state['status'],'return_intent_recorded':bool(state.get('image_return_intent_at'))}))
    except (m.SendError,ui.UIError,OSError,ValueError) as error:print(json.dumps({'ok':False,'error':str(error)}));raise SystemExit(2)
