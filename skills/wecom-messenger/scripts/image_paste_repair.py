"""Explicit same-job image-paste repair. Never sends, focuses, pastes or presses.
A supervisor-reviewed public window image is required when AX cannot expose an
empty editor. This is not an unlock for unknown message/Return outcomes.
"""
import hashlib,importlib.util,json,os
from pathlib import Path
import ui
from images import is_image,baseline
from native import Native

def need(ok,code):
    if not ok:raise ui.UIError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def pinned(r):
    need(isinstance(r,dict) and set(r)=={'path','sha256'} and Path(r['path']).is_absolute() and not Path(r['path']).is_symlink() and sha(r['path'])==r['sha256'],'image-paste-repair-evidence-changed');return Path(r['path'])
def empty(ctx):
    need(not ui.value(ctx['composer']) and not any(n.get('AXSubrole')=='AXTextAttachment' or n.get('role') in ('AXImage',) for n in ui.nodes(ctx['composer'])),'image-paste-repair-draft-present')
    need(not any(n.get('role') in ('AXSheet','AXDialog') or n.get('AXSubrole')=='AXDialog' for n in ctx['pool']),'image-paste-repair-modal-present')
def verify_visual(value,pid):
    image=pinned(value['image']);meta=load(pinned(value['capture_metadata']))
    need(value.get('reviewed_by')=='root-supervisor' and value.get('composer_empty') is True and value.get('no_attachment_or_preview') is True and value.get('target')=='测试群请忽略' and value.get('pid')==pid,'image-paste-repair-visual-review-required')
    need(meta.get('pid')==pid and meta.get('whole_window') is True and meta.get('pixel_actions_used') is False and meta.get('permission_request_used') is False and meta.get('capture_method') in ('macos-public-screencapture-window-id','ScreenCaptureKit/SCScreenshotManager/desktopIndependentWindow'),'image-paste-repair-public-window-capture-required')
    w=meta.get('window',meta.get('before',{}).get('window',{}));need(w.get('kCGWindowOwnerPID')==pid and w.get('kCGWindowName')=='企业微信' and w.get('kCGWindowNumber')==meta.get('window_id'),'image-paste-repair-window-pid-title-mismatch')
    need(meta.get('executable')=='/Applications/企业微信.app/Contents/MacOS/企业微信','image-paste-repair-executable-mismatch')
    need(meta.get('png',{}).get('sha256')==sha(image) and Path(meta['png']['path']).resolve()==image.resolve(),'image-paste-repair-visual-png-mismatch')
    spec=importlib.util.spec_from_file_location('public_png_integrity',Path(__file__).resolve().parents[2]/'chrome-dom-export/scripts/visible_capture.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    width,height=module.validate_png(image.read_bytes());need((width,height)==(meta['png']['width'],meta['png']['height']),'image-paste-repair-visual-size-mismatch')

def repair(path,report_ref,*,native_factory=Native):
    import messenger as m
    path=Path(path).resolve()
    with m.lock(path.parent):
        s=load(path);job=s['job'];m.validate(job,load(m.POLICY))
        need(hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()==s['fingerprint'],'job-changed')
        need(is_image(job) and job.get('scope')=='test' and job['target']=='测试群请忽略' and job['kind']=='group' and s.get('phase')=='file-confirm' and s.get('status')=='unknown','image-paste-repair-only-test-file-confirm')
        need(s.get('error') in ('file-confirm-button-ambiguous:0','image-paste-consumption-unverified-no-repaste'),'image-paste-repair-not-paste-recognition-error')
        forbidden=('image_return_intent_at','original_file_choice_intent_at','image_proof','owned_image_paste','image_receipt','automated_send','sent','ui_confirmed','image_paste_repair')
        need(not any(s.get(k) for k in forbidden),'image-paste-repair-send-or-repair-intent-present')
        events=s.get('events',[]);need(not any(e.get('stage') in ('file-confirm-intent','image-return-intent','original-file-choice-intent','ui-confirmed','image-new-row-confirmed','image-paste-repair-authorized') for e in events),'image-paste-repair-send-event-present')
        intents=[e for e in events if e.get('stage')=='send-intent'];need(len(intents)==1 and intents[0].get('file')==job['file_name'] and intents[0].get('sha256')==job['file_sha256'] and any(e.get('stage')=='file-pasted' and e.get('clipboard_restored') is True and e.get('clipboard_changed_by_other_app') is False for e in events),'image-paste-repair-original-paste-not-bounded')
        need(sha(job['file'])==job['file_sha256'],'image-paste-repair-source-changed')
        report=load(pinned(report_ref));need(report.get('kind')=='wecom-image-paste-repair-v1' and report.get('root_authorization')=='retry-same-job-image-paste-once' and report.get('job')=={'path':str(path),'sha256':sha(path)},'image-paste-repair-report-order-conflict')
        failed=load(pinned(report['failed_snapshot']));failed_ctx=ui.context(failed);ui.verify(failed_ctx,job);empty(failed_ctx);need(failed.get('pid')==s.get('pid'),'image-paste-repair-failed-pid-changed')
        # AX missing an editor AXValue is not promoted to proof of visual emptiness.
        verify_visual(report['visual_empty'],s['pid'])
        native=native_factory(s['pid']) if native_factory is Native else native_factory()
        try:
            fresh=native.tree();ctx=ui.context(fresh);ui.verify(ctx,job);empty(ctx)
            need(fresh.get('pid')==s['pid'] and baseline(ctx)==baseline(failed_ctx),'image-paste-repair-current-transcript-or-pid-changed')
        finally:native.close()
        root=path.parent/'image-paste-repairs'/path.stem;need(not root.exists(),'image-paste-repair-once-only');root.mkdir(parents=True)
        refs={}
        for name,p in [('original-job',path),('failed-snapshot',pinned(report['failed_snapshot'])),('supervisor-report',pinned(report_ref))]:
            raw=p.read_bytes();out=root/(name+'.json')
            with out.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            refs[name]={'path':str(out),'sha256':sha(out)}
        m.atomic(root/'fresh-snapshot.json',fresh)
        intent={'kind':'same-job-image-paste-repair-once-v1','original':refs,'fresh_snapshot':{'path':str(root/'fresh-snapshot.json'),'sha256':sha(root/'fresh-snapshot.json')},'key':job['key'],'pid':s['pid'],'source_sha256':job['file_sha256'],'authorized_at':m.now(),'send_performed':False,'paste_performed':False}
        m.atomic(root/'repair-intent.json',intent)
        s.update(status='running',phase='stage',image_paste_repair={'path':str(root/'repair-intent.json'),'sha256':sha(root/'repair-intent.json')})
        for key in ('send_intent_at','error','paste_empty_composer_verified','image_paste_seed'):s.pop(key,None)
        m.event(s,'image-paste-repair-authorized',key=job['key'],source_sha256=job['file_sha256'],original=refs['original-job']);s['updated_at']=m.now();m.atomic(path,s);return s
