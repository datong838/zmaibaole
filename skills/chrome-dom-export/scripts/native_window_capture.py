#!/usr/bin/env python3
"""Shared ScreenCaptureKit whole-window transport. No UI input/permission request.
DOM business proof remains the caller's responsibility; this layer binds the real
focused Chrome tab/window/PID before and after one public system screenshot.
"""
import argparse,fcntl,importlib.util,json,os,re,tempfile
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from visible_capture import require,atomic,sha,stamp,validate_png
import bridge
SOURCE='macos-public-screencapturekit'
METHOD='ScreenCaptureKit/SCScreenshotManager/desktopIndependentWindow'
BACKEND='screen-capture-kit'
EXE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
_spec=importlib.util.spec_from_file_location('public_window_evidence',Path(__file__).resolve().parents[2]/'douyin-laike-operator/scripts/window-evidence.py')
_public=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_public)
PublicCGWindow=_public.PublicCGWindow

def fields(c):
    require(set(c)=={'backend','pid','tabId','windowId','groupid','url','captureKey'} and c['backend']==BACKEND,'native-window-explicit-command-required')
    require(all(type(c[k]) is int and c[k]>0 for k in ('pid','tabId','windowId')) and isinstance(c['groupid'],str) and c['groupid'].isdigit(),'native-window-explicit-scope-required')
    u=urlsplit(c['url']);require(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[c['groupid']],'native-window-site-scope-mismatch')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',c['captureKey']) is not None,'native-window-stable-key-required')

def tab_scope(command,request):
    response=request({'op':'tabs'});require(response.get('ok') is True,'native-window-tabs-unavailable');windows=response.get('result')
    require(isinstance(windows,list),'native-window-tabs-invalid');focused=[w for w in windows if w.get('focused') is True]
    require(len(focused)==1 and focused[0].get('windowId')==command['windowId'],'native-window-browser-focus-mismatch')
    active=[t for t in focused[0].get('tabs',[]) if t.get('active') is True]
    require(len(active)==1,'native-window-active-tab-not-unique');t=active[0]
    require(t.get('tabId')==command['tabId'] and t.get('windowId')==command['windowId'] and t.get('url')==command['url'] and t.get('allowed') is True and isinstance(t.get('title'),str) and 0<len(t['title'])<800,'native-window-active-tab-scope-mismatch')
    return {k:t[k] for k in ('tabId','windowId','url','title')}|{'groupid':command['groupid']}

def chrome_window_title(actual,title):
    """Exact tab title plus the observed Chrome Chinese memory indicator only.

    Chrome prints that indicator in whole MB below one gigabyte (observed 937 MB and 1,016 MB) and in GB
    with one optional decimal at or above it. Only those two reviewed magnitudes are admitted;
    a decimal MB value, a zero, or anything at or above 1024 MB stays a mismatch.
    """
    if not isinstance(actual,str) or not isinstance(title,str) or not title:return False
    if actual in (title,title+' - Google Chrome'):return True
    match=re.fullmatch(re.escape(title)+r' - 内存用量高 - ([0-9]+(?:\.[0-9]+)?|[1-9][0-9]{0,2}(?:,[0-9]{3})+) (GB|MB) - Google Chrome',actual)
    if match is None:return False
    value,unit=match.groups()
    if unit=='GB':return ',' not in value
    return '.' not in value and 0<int(value.replace(',',''))<1024

def window_scope(items,pid,title,expected=None):
    # CG inventory is ordered front-to-back. Bind the sole first ordinary onscreen
    # window to bridge's focused window; identical titles in background are not
    # authority to select a different CGWindowID.
    normal=[w for w in items if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True]
    require(normal,'native-window-no-frontmost-normal-window');w=normal[0]
    require(w.get('kCGWindowOwnerPID')==pid and w.get('kCGWindowOwnerName')=='Google Chrome' and chrome_window_title(w.get('kCGWindowName'),title),'native-window-frontmost-pid-title-mismatch')
    require(type(w.get('kCGWindowNumber')) is int and w['kCGWindowNumber']>0 and w.get('kCGWindowSharingState') in (1,2),'native-window-not-capturable')
    require(len([i for i in items if i.get('kCGWindowNumber')==w['kCGWindowNumber']])==1,'native-window-cg-id-not-unique')
    result={k:w[k] for k in ('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowName','kCGWindowLayer','kCGWindowIsOnscreen','kCGWindowSharingState')}
    if expected is not None:require(result==expected,'native-window-changed-during-capture')
    return result

def process_identity(native,pid):
    observed=native.process_path(pid)
    if observed==EXE:return {'executable':EXE}
    import chrome_process_identity as identity
    require(isinstance(observed,str) and identity.CLONE.fullmatch(observed) is not None,'native-window-main-chrome-path-mismatch')
    return {'executable':observed,'executable_identity':identity.verify(observed)}

def preflight(command,request,native=None,*,diagnostic=None):
    fields(command);native=native or PublicCGWindow()
    audit={'kind':'native-window-preflight-components-v1','command':command,'observed_at':stamp(),'capture_attempted':False,'pixel_actions_used':False}
    attempted=False
    def emit():
        nonlocal attempted
        attempted=True
        if diagnostic is not None:diagnostic(json.loads(json.dumps(audit)))
    try:
        access=native.preflight();audit['screen_capture_access']=bool(access)
        require(access,'screen-capture-access-unavailable-no-permission-requested')
        identity=process_identity(native,command['pid']);audit['process_identity']=identity
        scope=tab_scope(command,request);audit['scope']=scope
        items=native.windows();normal=[w for w in items if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True]
        keys=('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowName','kCGWindowLayer','kCGWindowIsOnscreen','kCGWindowSharingState','kCGWindowBounds')
        def public(w):return {k:w.get(k) for k in keys if k not in ('kCGWindowName','kCGWindowBounds') or w.get('kCGWindowOwnerPID')==command['pid']}
        audit['frontmost_normal_window']=public(normal[0]) if normal else None
        audit['expected_pid_windows']=[public(w) for w in normal if w.get('kCGWindowOwnerPID')==command['pid']]
        audit['components']={'normal_window_present':bool(normal),'owner_pid_matches':bool(normal and normal[0].get('kCGWindowOwnerPID')==command['pid']),'owner_name_matches':bool(normal and normal[0].get('kCGWindowOwnerName')=='Google Chrome'),'title_matches':bool(normal and chrome_window_title(normal[0].get('kCGWindowName'),scope['title']))}
        emit() # The same actual observations are durable BEFORE the unchanged guard.
        window=window_scope(items,command['pid'],scope['title'])
        return {'backend':BACKEND,'source':SOURCE,'capture_method':METHOD,'screen_capture_access':True,'capture_attempted':False,'permission_request_used':False,'scope':scope,'window':window,'pid':command['pid'],**identity,'observed_at':stamp()}
    except Exception as error:
        if not attempted:
            audit['error']={'type':type(error).__name__,'message':str(error)}
            # A diagnostic failure must not hide the original guard/read error.
            try:emit()
            except Exception:pass
        raise

def write_capture(command,out,request,native=None,*,repair_intent=None):
    fields(command);out=Path(out).resolve();meta=out.with_suffix('.json');out.parent.mkdir(parents=True,exist_ok=True)
    require(out.suffix=='.png','native-window-png-output-required')
    with meta.with_name(meta.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if meta.exists():
            old=json.loads(meta.read_text());require(old.get('command')==command,'native-window-original-intent-required')
            if repair_intent is not None:
                import native_capture_repair as repair
                repair.consume(repair_intent,command,out,old)
            else:
                require(old.get('state')=='complete','native-window-capture-unknown-no-replay');validate(old,command,out);return {'ok':True,'result':{'path':str(out),'metadata':str(meta),'sha256':old['png']['sha256'],'reused':True}}
        require(not out.exists(),'native-window-output-exists')
        native=native or PublicCGWindow();before=preflight(command,request,native)
        if hasattr(native,'set_capture_scope'):native.set_capture_scope(command['pid'],before['scope']['title'])
        journal={'version':1,'backend':BACKEND,'source':SOURCE,'capture_method':METHOD,'command':command,'state':'unknown','intent_at':stamp(),'before':before,'whole_window':True,'viewport_only':False,'permission_request_used':False,'pixel_actions_used':False,'window_activation_used':False}
        if repair_intent is not None:journal['repair_intent']=repair_intent
        # Persistent before the first screenshot request; exceptions never replay.
        atomic(meta,journal)
        fd,tmp=tempfile.mkstemp(prefix='.sck-window-',suffix='.png',dir=out.parent);os.close(fd)
        try:
            dimensions=native.capture(before['window']['kCGWindowNumber'],tmp);captured=stamp()
            after_scope=tab_scope(command,request);require(after_scope==before['scope'],'native-window-tab-changed-during-capture')
            after_identity=process_identity(native,command['pid']);require(after_identity=={k:before[k] for k in ('executable','executable_identity') if k in before},'native-window-process-changed')
            after_window=window_scope(native.windows(),command['pid'],before['scope']['title'],before['window'])
            width,height=validate_png(Path(tmp).read_bytes());require(dimensions=={'width':width,'height':height},'native-window-png-dimensions-mismatch')
            os.link(tmp,out)
            journal.update(state='complete',captured_at=captured,completed_at=stamp(),after={'scope':after_scope,'window':after_window,'pid':command['pid'],**after_identity},png={'path':str(out),'sha256':sha(out),'width':width,'height':height})
            validate(journal,command,out);atomic(meta,journal)
            return {'ok':True,'result':{'path':str(out),'metadata':str(meta),'sha256':journal['png']['sha256'],'whole_window':True,'viewport_only':False}}
        except Exception as error:journal['error']=str(error);atomic(meta,journal);raise
        finally:
            if os.path.exists(tmp):os.unlink(tmp)

def validate(metadata,command,png_path):
    fields(command);require(metadata.get('state')=='complete' and metadata.get('command')==command,'native-window-metadata-incomplete')
    require(metadata.get('backend')==BACKEND and metadata.get('source')==SOURCE and metadata.get('capture_method')==METHOD,'native-window-backend-mismatch')
    require(metadata.get('whole_window') is True and metadata.get('viewport_only') is False and all(metadata.get(k) is False for k in ('permission_request_used','pixel_actions_used','window_activation_used')),'native-window-safety-flags-mismatch')
    before=metadata['before'];after=metadata['after'];s=before['scope'];w=before['window']
    require(before.get('backend')==BACKEND and before.get('source')==SOURCE and before.get('screen_capture_access') is True and before.get('capture_attempted') is False and before.get('permission_request_used') is False,'native-window-preflight-invalid')
    identity={k:before[k] for k in ('executable','executable_identity') if k in before}
    if identity.get('executable')!=EXE:
        import chrome_process_identity as process
        process.validate_record(identity.get('executable_identity',{}),identity.get('executable',''))
    else:require('executable_identity' not in identity,'native-window-unexpected-original-path-identity')
    require(after=={'scope':s,'window':w,'pid':command['pid'],**identity} and before.get('pid')==command['pid'],'native-window-before-after-mismatch')
    require(all(s.get(k)==command[k] for k in ('tabId','windowId','groupid','url')) and isinstance(s.get('title'),str) and bool(s['title']),'native-window-scope-mismatch')
    window_scope([w],command['pid'],s['title'],w)
    when=lambda t:__import__('datetime').datetime.fromisoformat(t.replace('Z','+00:00'))
    require(when(before['observed_at'])<=when(metadata['intent_at'])<=when(metadata['captured_at'])<=when(metadata['completed_at']),'native-window-time-order-invalid')
    image=metadata['png'];require(Path(image['path']).resolve()==Path(png_path).resolve() and sha(png_path)==image['sha256'],'native-window-png-hash-mismatch');width,height=validate_png(Path(png_path).read_bytes());require((width,height)==(image['width'],image['height']),'native-window-png-size-mismatch');return image

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--command',required=True);p.add_argument('--out');p.add_argument('--preflight',action='store_true');a=p.parse_args();c=json.loads(Path(a.command).read_text())
    if a.preflight:result=preflight(c,bridge.request)
    else:require(a.out is not None,'native-window-output-required');result=write_capture(c,a.out,bridge.request)
    print(json.dumps({'ok':True,'result':result},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e),'permission_request_used':False},ensure_ascii=False));raise SystemExit(2)
