"""Owned inline image drafts: verified own-paste chain, one Return, receipt.

The observed WeCom inline-image bubble is an unlabeled AXButton, not AXImage.
That shape alone is never sufficient: the exact source and own-paste binding,
plus an unchanged transcript prefix, precede the one send key event.
"""
import hashlib
import json
import re
import uuid
import time
from pathlib import Path
import ui
from image_verify import verify_attributed
OWNERSHIP_SESSION=uuid.uuid4().hex

def is_image(job):
    return job.get('type')=='file' and job.get('file_name','').lower().endswith(('.png','.jpg','.jpeg'))

def row_signature(row):
    def shape(node):
        # WeCom adds/removes empty accessibility placeholder labels while a
        # historical file bubble lays out. They carry no message semantics.
        children=[shape(c) for c in node.get('children',[]) if not (
            c.get('role')=='AXStaticText' and not ui.value(c) and not c.get('AXHelp') and not c.get('children'))]
        children.sort(key=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True))
        return {'role':node.get('role'),'subrole':node.get('AXSubrole'),'value':ui.value(node),
                'help':node.get('AXHelp'),'children':children}
    return hashlib.sha256(json.dumps(shape(row),ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def transcript_rows(ctx):
    return [r for r in ctx['transcript'].get('children',[]) if r.get('role')=='AXRow']

def baseline(ctx):return [row_signature(r) for r in transcript_rows(ctx)]

def same_frontier(before,after):
    # Current chat count and tail only; old message presentation is not state.
    return isinstance(before,list)and isinstance(after,list)and len(before)==len(after)and (not before or before[-1]==after[-1])

def image_row(row,caption=None):
    pool=list(ui.nodes(row));buttons=[n for n in pool if n.get('role')=='AXButton']
    if len(buttons)!=1 or ui.value(buttons[0]) or buttons[0].get('AXHelp') or buttons[0].get('AXEnabled') is not True:return False
    allowed=('AXRow','AXCell','AXStaticText','AXButton')+(('AXTextArea',) if caption is not None else ())
    if any(n.get('role') not in allowed for n in pool):return False
    captions=[ui.value(n) for n in pool if n.get('role')=='AXTextArea']
    if captions!=([caption] if caption is not None else []):return False
    labels=[ui.value(n) for n in pool if n.get('role')=='AXStaticText' and ui.value(n)]
    # Only the public timestamp label may accompany the image button.
    return len(labels)<=1 and all(re.fullmatch(r'(?:(?:今天|昨天|前天|星期[一二三四五六日天])\s+|\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+)?\d{1,2}:\d{2}',v) for v in labels)

def draft_proof(native,ctx,job):
    attached=[n for n in ui.nodes(ctx['composer']) if n.get('AXSubrole')=='AXTextAttachment']
    if ui.value(ctx['composer'])!='\ufffc' or len(attached)!=1:raise ui.UIError('image-draft-not-single-owned-attachment')
    return verify_attributed(native.attachment_attributed(ctx['composer']),job)

def attachment_shape(ctx):
    attached=[n for n in ui.nodes(ctx['composer']) if n.get('AXSubrole')=='AXTextAttachment']
    if ui.value(ctx['composer'])!='\ufffc' or len(attached)!=1:raise ui.UIError('image-draft-not-single-owned-attachment')
    return {'composer_value':'\ufffc','attachment_role':attached[0].get('role'),'attachment_subrole':'AXTextAttachment',
            'attachment_url':attached[0].get('AXURL')}

def bind_owned_paste(s,ctx,clipboard,event):
    job=s['job'];ui.verify(ctx,job)
    if s.get('paste_empty_composer_verified') is not True or not any(e.get('stage')=='send-intent' and e.get('sha256')==job['file_sha256'] for e in s.get('events',[])):
        raise ui.UIError('image-empty-source-intent-proof-missing')
    if not clipboard.get('file_url_verified') or 'public.file-url' not in clipboard.get('types',[]) or not isinstance(clipboard.get('change_count'),int):
        raise ui.UIError('image-clipboard-proof-missing')
    if hashlib.sha256(Path(job['file']).read_bytes()).hexdigest()!=job['file_sha256']:raise ui.UIError('image-source-changed-after-paste')
    seed=s.get('image_paste_seed')
    if seed is not None:
        expected={'source_sha256':job['file_sha256'],'pid':s['pid'],'target':job['target'],'kind':job['kind'],'clipboard':clipboard,'transcript':baseline(ctx),'empty_composer_verified':True,'ownership_session':OWNERSHIP_SESSION}
        if {k:v for k,v in seed.items()if k!='transcript'}!={k:v for k,v in expected.items()if k!='transcript'}or not same_frontier(seed.get('transcript'),expected['transcript']):raise ui.UIError('image-paste-seed-or-transcript-changed')
    proof={'method':'owned-source-file-url-clipboard-continuous-paste-chain','source_sha256':job['file_sha256'],
           'pid':s['pid'],'target':job['target'],'kind':job['kind'],'clipboard':clipboard,'attachment':attachment_shape(ctx),
           'transcript':baseline(ctx),'ownership_session':OWNERSHIP_SESSION}
    proof['binding_sha256']=hashlib.sha256(json.dumps(proof,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    s['owned_image_paste']=proof
    event(s,'owned-image-paste-bound',source_sha256=job['file_sha256'],binding_sha256=proof['binding_sha256'])

def owned_proof(s,ctx):
    proof=s.get('owned_image_paste');job=s['job']
    if not isinstance(proof,dict):raise ui.UIError('image-owned-paste-proof-missing')
    content={k:v for k,v in proof.items() if k!='binding_sha256'}
    if proof.get('binding_sha256')!=hashlib.sha256(json.dumps(content,ensure_ascii=False,sort_keys=True).encode()).hexdigest():raise ui.UIError('image-owned-paste-proof-corrupt')
    if proof.get('ownership_session')!=OWNERSHIP_SESSION:raise ui.UIError('image-paste-session-ended-no-replay')
    if proof['source_sha256']!=job['file_sha256'] or proof['pid']!=s.get('pid') or proof['target']!=ctx['name'] or proof['kind']!=ctx['kind']:
        raise ui.UIError('image-owned-paste-scope-mismatch')
    if attachment_shape(ctx)!=proof['attachment'] or not same_frontier(baseline(ctx),proof['transcript']):raise ui.UIError('image-owned-paste-draft-or-transcript-changed')
    if hashlib.sha256(Path(job['file']).read_bytes()).hexdigest()!=job['file_sha256']:raise ui.UIError('image-source-file-changed')
    return proof

def settled_owned_proof(native,s,ctx):
    # Read-only layout settling, never replace the persisted transcript baseline.
    for attempt in range(3):
        try:return owned_proof(s,ctx),ctx
        except ui.UIError as e:
            if str(e)!='image-owned-paste-draft-or-transcript-changed' or attempt==2:raise
            time.sleep(.25*(attempt+1));snapshot=native.tree()
            if snapshot.get('pid')!=s.get('pid'):raise ui.UIError('image-owned-paste-process-changed')
            ctx=ui.context(snapshot);ui.verify(ctx,s['job'])

def confirm_image(native,s,ctx,path,atomic,event):
    job=s['job'];ui.verify(ctx,job)
    if not is_image(job) or not s.get('send_intent_at'):raise ui.UIError('image-paste-not-owned')
    seed_route=not any(e.get('stage')=='file-pasted' for e in s.get('events',[]))
    if seed_route:
        from image_draft_recovery import verify_seed_staging
        verify_seed_staging(s,ctx)
    if s.get('image_return_intent_at'):raise ui.UIError('image-return-unknown-no-replay')
    if seed_route:proof=owned_proof(s,ctx)
    else:proof,ctx=settled_owned_proof(native,s,ctx)
    native.focus(ctx['composer']);snapshot=native.tree()
    if snapshot.get('pid')!=s.get('pid'):raise ui.UIError('image-confirm-process-changed')
    fresh=ui.context(snapshot);ui.verify(fresh,job)
    if seed_route:again=owned_proof(s,fresh)
    else:again,fresh=settled_owned_proof(native,s,fresh)
    if proof!=again:raise ui.UIError('image-draft-changed-after-focus')
    if seed_route:verify_seed_staging(s,fresh,snapshot=snapshot)
    from datetime import datetime
    from zoneinfo import ZoneInfo
    s.update(image_proof=proof,image_transcript_baseline=baseline(fresh),
             image_return_intent_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),
             phase='image-verify-sent',status='unknown',automated_send=True,user_sent=False)
    s.pop('error',None);event(s,'image-return-intent',source_sha256=job['file_sha256'],proof_method=proof['method'])
    atomic(path,s)
    native.key(36,13)

def verify_image(s,ctx,event,finish):
    ui.verify(ctx,s['job'])
    proof=s.get('image_proof');before=s.get('image_transcript_baseline')
    if not s.get('image_return_intent_at') or not proof or proof.get('source_sha256')!=s['job']['file_sha256'] or not isinstance(before,list):
        raise ui.UIError('image-send-proof-missing')
    rows=transcript_rows(ctx)
    if ui.value(ctx['composer']):raise ui.UIError('image-send-draft-still-present-no-replay')
    if len(rows)!=len(before)+1 or (before and row_signature(rows[-2])!=before[-1]):
        raise ui.UIError('image-transcript-difference-ambiguous')
    caption=None
    if s.get('user_approved_current_draft'):
        caption=s.get('user_approved_caption')
        if caption is not None and hashlib.sha256(('\ufffc'+caption).encode()).hexdigest()!=s.get('approved_draft_sha256'):
            raise ui.UIError('image-approved-caption-hash-mismatch')
    if not image_row(rows[-1],caption):raise ui.UIError('image-new-row-not-verified')
    s['image_receipt']={'row_signature':row_signature(rows[-1]),'source_sha256':proof['source_sha256'],
                        'basis':'verified-owned-image-return-empty-composer-unique-new-observed-inline-image-row'}
    event(s,'image-new-row-confirmed',row_signature=s['image_receipt']['row_signature']);finish(s)


def confirm_visible_image(path,attestation):
    """Read-only reconciliation when an inline image has no AX image child.
    The supervisor must have viewed the exact client PNG and source image.
    Never sends, pastes, focuses or changes the composer.
    """
    import messenger,json,hashlib
    from pathlib import Path
    from native import Native
    path=Path(path).resolve()
    with messenger.lock(path.parent):
        original=path.read_bytes();s=json.loads(original)
        a=json.loads(Path(attestation['path']).read_text())
        if hashlib.sha256(Path(attestation['path']).read_bytes()).hexdigest()!=attestation['sha256']:raise ui.UIError('visible-image-attestation-changed')
        if a.get('kind')!='supervisor-visible-client-image-v1' or a.get('reviewer_role')!='supervisor' or a.get('source_image_visual_match')is not True:raise ui.UIError('visible-image-review-required')
        if a.get('sender')!={'path':str(path),'sha256':hashlib.sha256(original).hexdigest()} or a.get('source_sha256')!=s['job']['file_sha256'] or a.get('target')!=s['job']['target']:raise ui.UIError('visible-image-review-binding')
        capture=a['client_capture']
        if hashlib.sha256(Path(capture['path']).read_bytes()).hexdigest()!=capture['sha256'] or not Path(capture['path']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):raise ui.UIError('visible-image-capture-changed')
        if a.get('capture_owner_pid')!=s.get('pid') or s.get('phase')!='image-verify-sent' or s.get('status')!='unknown' or not s.get('send_intent_at')or not s.get('image_return_intent_at'):raise ui.UIError('visible-image-original-send-required')
        proof=s.get('image_proof')or{}
        if proof.get('source_sha256')!=s['job']['file_sha256']:raise ui.UIError('visible-image-owned-source-required')
        n=Native(s['pid'],capability_scope='sender-required')
        try:
            ctx=ui.context(n.chat_tree());ui.verify(ctx,s['job']);rows=transcript_rows(ctx);before=s['image_transcript_baseline']
            if ui.value(ctx['composer'])or not before or len(rows)!=len(before)+1 or row_signature(rows[-2])!=before[-1]:raise ui.UIError('visible-image-current-chat-ambiguous')
            last=rows[-1];cells=last.get('children',[])
            if len(cells)!=1 or cells[0].get('role')!='AXCell':raise ui.UIError('visible-image-empty-AX-representation-changed')
            for node in cells[0].get('children',[]):
                if node.get('role')!='AXStaticText' or node.get('children') or not re.fullmatch(r'(?:(?:今天|昨天|前天|星期[一二三四五六日天])\s+|\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+)?\d{1,2}:\d{2}',ui.value(node)):raise ui.UIError('visible-image-unreviewed-AX-content')
            s['image_receipt']={'row_signature':row_signature(last),'source_sha256':proof['source_sha256'],'basis':'owned-image-send-unique-new-row-empty-composer-and-supervisor-reviewed-client-PNG','visual_confirmation':attestation}
            messenger.event(s,'image-new-row-confirmed',row_signature=s['image_receipt']['row_signature'],visual_confirmation=attestation);messenger.finish(s);messenger.atomic(path,s)
        finally:n.close()
    return s
