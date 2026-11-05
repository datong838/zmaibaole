"""File URL paste -> recipient/file confirmation -> transcript verification.

No guessed toolbar index or file-dialog shortcut. Clipboard formats stay in
memory and are restored. Paste can send immediately, so intent precedes paste.
"""
import time
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import unquote,urlparse
import ui
from pasteboard import file_url,PasteboardError

class FileError(ui.UIError):pass

class _StageRead:
    """Single-use in-process handoff, never a persisted passed/read receipt."""
    def __init__(self,native,snapshot,job):
        self.native=native;self.snapshot=snapshot;self.pid=native.pid
        self.generation=native.input_generation;self.paths=native.by_path
        self.target=(job['target'],job['kind']);self.used=False
        self.digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    def take_snapshot(self,native,job):
        if self.used or native is not self.native or native.pid!=self.pid or native.input_generation!=self.generation or native.by_path is not self.paths or (job['target'],job['kind'])!=self.target:
            raise FileError('stage-snapshot-handoff-changed')
        self.used=True
        if hashlib.sha256(json.dumps(self.snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()!=self.digest:raise FileError('stage-snapshot-handoff-mutated')
        ctx=ui.context(self.snapshot);ui.verify(ctx,job);return self.snapshot
    def take(self,native,job):
        return ui.context(self.take_snapshot(native,job))

def stage_read(native,snapshot,job):
    # Older adapters keep their original first read. Production Native supplies
    # a generation incremented before every public input API, including focus.
    if type(getattr(native,'input_generation',None)) is not int or not hasattr(native,'by_path') or getattr(native,'pid',None)!=snapshot.get('pid') or snapshot.get('read_scope')!='application-windows-complete':return None
    ctx=ui.context(snapshot);ui.verify(ctx,job)
    return _StageRead(native,snapshot,job)

class _BoundImageRead:
    """One successful owned binding; later journal mutations cannot grant reuse."""
    fields=('job','pid','phase','status','send_intent_at','paste_empty_composer_verified','image_paste_seed','owned_image_paste','image_return_intent_at','error')
    def __init__(self,read,state):
        self.read=read;self.binding=self.signature(state)
    def signature(self,state):
        return hashlib.sha256(json.dumps({k:state.get(k) for k in self.fields},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    def take_snapshot(self,native,state):
        if self.signature(state)!=self.binding or not any(e.get('stage')=='file-pasted' for e in state.get('events',[])):
            raise FileError('image-binding-handoff-state-changed')
        return self.read.take_snapshot(native,state['job'])

def attachment_path(url):
    parsed=urlparse(url)
    if parsed.scheme!='file' or parsed.netloc not in ('','localhost'):return None
    return str(Path(unquote(parsed.path)).resolve())

def _wait_image_binding(native,s,path,atomic,event,info,clipboard,deadline):
    """Only an exact original seed's transcript may settle; no input here.
    The existing 8 reads/20s budget admits reads, and late reads cannot bind.
    """
    import images
    job=s['job'];seed=json.loads(json.dumps(s['image_paste_seed']));start=deadline-20
    snapshot=None;ctx=None;expected=None;actual_clipboard=None;attempts=0;last_error=None;source_sha=None
    def timed_out():
        return FileError(last_error or 'image-paste-consumption-unverified-no-repaste')
    try:
        for _ in range(8):
            remaining=deadline-time.monotonic()
            if remaining<=0:raise timed_out()
            time.sleep(min(.3,remaining))
            if time.monotonic()>=deadline:raise timed_out()
            snapshot=None;ctx=None;expected=None;actual_clipboard=None
            attempts+=1;snapshot=native.tree()
            if snapshot.get('pid')!=s.get('pid'):raise FileError('image-paste-process-changed')
            if snapshot.get('read_scope') not in (None,'application-windows-complete') or snapshot.get('truncated') is not False:raise FileError('ui-tree-incomplete')
            ctx=ui.context(snapshot);ui.verify(ctx,job)
            if s.get('image_paste_seed')!=seed:raise FileError('image-paste-seed-or-transcript-changed')
            source_sha=hashlib.sha256(Path(job['file']).read_bytes()).hexdigest()
            if source_sha!=job['file_sha256']:raise FileError('image-source-changed-after-paste')
            actual_clipboard=info['assert_owned']()
            if actual_clipboard!=clipboard:raise FileError('image-clipboard-binding-changed')
            current=images.baseline(ctx)
            expected={'source_sha256':job['file_sha256'],'pid':s['pid'],'target':job['target'],'kind':job['kind'],'clipboard':actual_clipboard,'transcript':current,'empty_composer_verified':True,'ownership_session':images.OWNERSHIP_SESSION}
            if set(seed)!=set(expected) or not isinstance(seed.get('transcript'),list) or {k:v for k,v in seed.items() if k!='transcript'}!={k:v for k,v in expected.items() if k!='transcript'}:raise FileError('image-paste-seed-or-transcript-changed')
            if time.monotonic()>=deadline:raise timed_out()
            value=ui.value(ctx['composer'])
            if value=='\ufffc':
                # A multi-attachment or unknown draft is never a settling case.
                images.attachment_shape(ctx)
                trial={**s,'events':list(s.get('events',[]))}
                try:
                    images.bind_owned_paste(trial,ctx,clipboard,event)
                except ui.UIError as error:
                    if str(error)!='image-paste-seed-or-transcript-changed' or current==seed['transcript']:raise
                    last_error=str(error);continue
                if time.monotonic()>=deadline:raise timed_out()
                s['owned_image_paste']=trial['owned_image_paste'];s['events']=trial['events']
                atomic(path,s);read=stage_read(native,snapshot,job)
                return _BoundImageRead(read,s) if read is not None else None
            if value:raise FileError('image-draft-not-single-owned-attachment')
            if current!=seed['transcript']:raise FileError('image-paste-transcript-changed-unverified')
        raise timed_out()
    except (ui.UIError,RuntimeError,OSError,ValueError) as error:
        # No message body/clipboard contents: complete row signatures and exact
        # non-transcript seed differences explain this very read without reread.
        current=images.baseline(ctx) if ctx is not None else None
        old=seed.get('transcript');diff=None if current is None or not isinstance(old,list) else [i for i in range(max(len(old),len(current))) if (old[i] if i<len(old) else None)!=(current[i] if i<len(current) else None)]
        diagnostic={'kind':'image-paste-binding-failure-v1','reason':str(error),'attempts':attempts,'read_limit':8,'budget_seconds':20,'elapsed_seconds':time.monotonic()-start,'deadline_exhausted':time.monotonic()>=deadline,'original_seed_sha256':hashlib.sha256(json.dumps(seed,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'original_transcript':old,'current_transcript':current,'diff_indices':diff,'expected_seed_without_transcript':None if expected is None else {k:v for k,v in expected.items() if k!='transcript'},'seed_diff_fields':None if expected is None else [k for k in sorted(set(seed)|set(expected)) if seed.get(k)!=expected.get(k)],'current_source_sha256':source_sha,'actual_clipboard_proof':actual_clipboard,'snapshot_sha256':None if snapshot is None else hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'snapshot_metadata':None if snapshot is None else {k:snapshot.get(k) for k in ('pid','ok','read_scope','node_count','truncated','truncation_reason')},'observed_recipient':None if ctx is None else {'name':ctx['name'],'kind':ctx['kind']},'message_text_recorded':False,'clipboard_contents_recorded':False,'input_replayed':False}
        s.update(status='unknown',error=str(error),image_paste_binding_failure=diagnostic);event(s,'image-paste-binding-failed',reason=str(error),diagnostic_sha256=hashlib.sha256(json.dumps(diagnostic,ensure_ascii=False,sort_keys=True).encode()).hexdigest());atomic(path,s)
        raise

def stage_file(native,s,path,atomic,event,*,fresh_read=None):
    job=s['job'];ctx=fresh_read.take(native,job) if fresh_read is not None else ui.context(native.tree());ui.verify(ctx,job)
    if ui.value(ctx['composer']):raise FileError('existing-draft-preserved')
    from images import is_image
    native.focus(ctx['composer'])
    # A shown context menu must not intercept the paste shortcut.
    native.key(53,27)
    ctx=ui.context(native.tree());ui.verify(ctx,job)
    if ui.value(ctx['composer']):raise FileError('existing-draft-preserved')
    # Escape can move focus away from the editor; bind a newly read editor again.
    native.focus(ctx['composer'])
    ctx=ui.context(native.tree());ui.verify(ctx,job)
    if ui.value(ctx['composer']):raise FileError('existing-draft-preserved')
    s.update(phase='file-confirm',status='unknown',paste_empty_composer_verified=True,
             send_intent_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'))
    event(s,'send-intent',file=job['file_name'],sha256=job['file_sha256']);atomic(path,s)
    bound_read=None
    with file_url(job['file']) as info:
        from images import is_image,bind_owned_paste,baseline,OWNERSHIP_SESSION
        if is_image(job):
            if hashlib.sha256(Path(job['file']).read_bytes()).hexdigest()!=job['file_sha256']:raise FileError('image-source-changed-before-paste')
            clipboard=info['assert_owned']()
            s['image_paste_seed']={'source_sha256':job['file_sha256'],'pid':s['pid'],'target':job['target'],'kind':job['kind'],'clipboard':clipboard,'transcript':baseline(ctx),'empty_composer_verified':True,'ownership_session':OWNERSHIP_SESSION}
            event(s,'image-paste-seed-persisted',source_sha256=job['file_sha256']);atomic(path,s)
        native.focus(ctx['composer'])  # Exact composer + frontmost rechecked at the input boundary.
        native.key(9,ord('v'),command=True)
        # Keep the file URL available until the application has consumed the paste.
        deadline=time.monotonic()+20
        if is_image(job):
            bound_read=_wait_image_binding(native,s,path,atomic,event,info,clipboard,deadline)
        else:
            for _ in range(3):
                time.sleep(.3);snapshot=native.tree()
                if any(ui.value(n)==job['file_name'] or attachment_path(n.get('AXURL',''))==str(Path(job['file']).resolve()) for n in ui.nodes(snapshot['tree'])):break
    event(s,'file-pasted',clipboard_restored=info['restored'],clipboard_changed_by_other_app=info['concurrent_change']);atomic(path,s)
    # Only a fully bound image read can continue. Clipboard cleanup and durable
    # writes do not grant freshness: the single-use ticket still checks generation,
    # native/PID/path-map/target and exact snapshot bytes before any next input.
    return bound_read

def advance_file(native,s,snapshot,path,atomic,event,finish):
    job=s['job'];ctx=ui.context(snapshot);ui.verify(ctx,job)
    if s['phase']!='file-confirm':raise FileError('file-phase-invalid')
    if ui.message_count(ctx,job['file_name'])>s['baseline'] and not ui.value(ctx['composer']):finish(s);return
    from images import is_image,confirm_image
    if is_image(job):
        if not s.get('owned_image_paste'):raise FileError('image-paste-consumption-unverified-no-repaste')
        confirm_image(native,s,ctx,path,atomic,event);return
    # Current Mac client pastes a real rich-text attachment into the composer.
    # Verify its public AXTextAttachment URL, not a guessed file-picker position.
    attached=[n for n in ui.nodes(ctx['composer']) if n.get('AXSubrole')=='AXTextAttachment']
    if attached:
        from images import is_image,confirm_image
        if is_image(job):
            confirm_image(native,s,ctx,path,atomic,event);return
        expected=str(Path(job['file']).resolve())
        def matches(c):
            items=[n for n in ui.nodes(c['composer']) if n.get('AXSubrole')=='AXTextAttachment']
            return ui.value(c['composer'])=='\ufffc' and len(items)==1 and attachment_path(items[0].get('AXURL',''))==expected
        if not matches(ctx):raise FileError('attachment-path-unverified')
        native.focus(ctx['composer']);fresh=ui.context(native.tree());ui.verify(fresh,job)
        if not matches(fresh):raise FileError('attachment-changed')
        s.pop('error',None);s['phase']='verify-sent';event(s,'file-confirm-intent',attachment_url_verified=True);atomic(path,s)
        native.key(36,13);return
    pool=list(ui.nodes(snapshot['tree']))
    # Mac spreadsheet first-send choice: preserve the original local file. The
    # sender owns this paste intent and main chat was reverified immediately above.
    choices=[]
    for modal in pool:
        if modal.get('role') not in ('AXSheet','AXDialog'):continue
        names=[ui.value(n) for n in ui.nodes(modal)]
        if '发送到聊天' in names and '转为在线表格' in names and '使用原文件' in names:
            choices.append(modal)
    if choices:
        modal=ui.only(choices,'original-file-choice-modal-ambiguous')
        names=[ui.value(n) for n in ui.nodes(modal)]
        if job['file_name'] not in names:raise FileError('original-file-choice-filename-mismatch')
        if not s.get('send_intent_at') or not any(e.get('stage')=='file-pasted' for e in s.get('events',[])):raise FileError('original-file-choice-not-owned')
        if s.get('original_file_choice_intent_at'):raise FileError('original-file-choice-outcome-unknown-no-replay')
        button=ui.only([n for n in ui.nodes(modal) if n.get('role')=='AXButton' and ui.value(n)=='使用原文件'],'original-file-choice-button-ambiguous')
        if button.get('AXEnabled') is not True:raise FileError('original-file-choice-disabled')
        s.pop('error',None);s['original_file_choice_intent_at']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
        event(s,'original-file-choice-intent',filename=job['file_name'],recipient=job['target']);atomic(path,s)
        native.press(button)
        # May create an attachment draft or send immediately; observe next step.
        return
    button=ui.only([n for n in pool if n['role']=='AXButton' and ui.value(n) in ('发送','Send')],'file-confirm-button-ambiguous')
    modals=[n for n in pool if (n['role'] in ('AXSheet','AXDialog') or n['role']=='AXWindow' and n.get('AXSubrole')=='AXDialog') and ui.below(button,n)]
    if not modals:raise FileError('file-confirm-modal-unverified')
    modal=max(modals,key=lambda n:len(n['path']))
    names=[ui.value(n) for n in ui.nodes(modal)]
    if job['file_name'] not in names or not any(job['target']==name or ('发送给'+job['target'])==name.replace(' ','').replace('：','').replace(':','') for name in names):raise FileError('file-confirm-recipient-unverified')
    if button.get('AXEnabled') is not True:raise FileError('file-send-disabled')
    s['phase']='verify-sent';event(s,'file-confirm-intent');atomic(path,s);native.press(button)
