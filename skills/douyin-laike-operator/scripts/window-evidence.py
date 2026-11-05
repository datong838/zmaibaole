#!/usr/bin/env python3
"""Whole Chrome window evidence via public ScreenCaptureKit. No pixel actions.
No permission request, Chrome launch, debugging, profile or credential access.
DOM proof binds scope; window image still requires review for visible row coverage.
"""
import argparse
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import sys
import tempfile
import subprocess
import platform
from urllib.parse import urlsplit, parse_qs

class EvidenceError(ValueError):pass

def require(ok,code):
    if not ok:raise EvidenceError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.now(timezone.utc).isoformat()
def atomic(path,value):
    path=Path(path);fd,tmp=tempfile.mkstemp(prefix='.evidence-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def scope_proof(path,at=None):
    """Validate observed tab enumeration + complete DOM, no caller supplied true flags."""
    path=Path(path).resolve();require(path.is_file(),'dom-evidence-file-missing')
    p=json.loads(path.read_text());require(p.get('source')=='local-dom-bridge','dom-source-not-local-bridge')
    try:observed=datetime.fromisoformat(str(p['observed_at']).replace('Z','+00:00'));age=((at or datetime.now(timezone.utc))-observed).total_seconds()
    except Exception:raise EvidenceError('dom-observation-time-invalid')
    require(observed.utcoffset() is not None and 0<=age<=60,'dom-evidence-stale-or-future')
    windows=[w for w in p.get('tabs',[]) if w.get('focused') is True]
    require(len(windows)==1,'focused-browser-window-not-unique');w=windows[0]
    tabs=[t for t in w.get('tabs',[]) if t.get('active') is True]
    require(len(tabs)==1,'active-tab-not-unique');tab=tabs[0]
    require(tab.get('tabId')==p.get('tab_id') and tab.get('windowId')==w.get('windowId') and tab.get('allowed') is True,'active-tab-binding-unverified')
    require(str(p.get('groupid','')).isdigit(),'dom-group-id-required')
    u=urlsplit(tab.get('url',''));require(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[str(p.get('groupid'))],'tab-group-origin-mismatch')
    require(tab.get('title') and len(tab['title'])<800,'tab-title-unverified')
    tree=p.get('tree',{});require(tree.get('kind')=='DOM-derived semantic tree (not native AX)' and tree.get('truncated') is False and isinstance(tree.get('root'),dict),'complete-dom-tree-required')
    require(tree.get('url')==u._replace(query='',fragment='').geturl(),'dom-tab-path-mismatch')
    nodes=[];stack=[tree['root']]
    while stack:
        n=stack.pop();require(isinstance(n,dict) and len(nodes)<10000,'dom-tree-invalid');nodes.append(n);stack.extend(n.get('children',[]))
    bindings=p.get('bindings',{});require(set(bindings)>={'date','headers'},'date-header-bindings-required')
    def leaf(binding):
        require(isinstance(binding,dict) and set(binding)=={'selector','text'},'dom-binding-contract-invalid')
        found=[n for n in nodes if n.get('selector')==binding['selector']]
        require(len(found)==1,'dom-binding-not-unique');n=found[0]
        require(not n.get('children'),'dom-binding-must-be-leaf')
        value=str(n.get('attributes',{}).get('value',n.get('name',''))).strip()
        require(value and len(value)<800 and value==binding['text'],'dom-binding-text-mismatch-or-truncated');return value
    dates=p.get('date_range',{});first,end=dates.get('start'),dates.get('end')
    try:datetime.strptime(first,'%Y-%m-%d');datetime.strptime(end,'%Y-%m-%d')
    except Exception:raise EvidenceError('dom-date-range-invalid')
    require(first<=end,'dom-date-range-invalid')
    require(leaf(bindings['date']).replace('/','-')==first+' ~ '+end,'dom-date-filter-mismatch')
    require(isinstance(bindings['headers'],list) and bindings['headers'],'dom-headers-required')
    headers=[leaf(x) for x in bindings['headers']]
    return {'path':str(path),'sha256':sha(path),'observed_at':p['observed_at'],'tab_id':tab['tabId'],'chrome_window_id':w['windowId'],'title':tab['title'],'url':tab['url'],'groupid':str(p['groupid']),'date_range':dates,'headers':headers}

class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double)]
class Size(C.Structure):_fields_=[('width',C.c_double),('height',C.c_double)]
class Rect(C.Structure):_fields_=[('origin',Point),('size',Size)]

def build_helper(cache=None,runner=subprocess.run):
    """Compile only; this function never loads capture frameworks or requests consent."""
    source=Path(__file__).with_name('window-capture.swift')
    cache=Path(cache) if cache else Path(__file__).resolve().parents[3]/'runtime/douyin-laike-operator/screen-capture-kit'
    cache.mkdir(parents=True,exist_ok=True)
    machine=platform.machine();require(machine in ('arm64','x86_64'),'sck-unsupported-build-architecture')
    fingerprint=hashlib.sha256(source.read_bytes()+machine.encode()).hexdigest()[:24]
    target=cache/('window-capture-'+fingerprint)
    if target.is_file() and os.access(target,os.X_OK):return target
    fd,tmp=tempfile.mkstemp(prefix='.compile-',dir=cache);os.close(fd)
    try:
        result=runner(['/usr/bin/xcrun','swiftc','-parse-as-library',
             '-module-cache-path',str(cache/'module-cache'),str(source),'-o',tmp],capture_output=True,text=True,timeout=90)
        require(result.returncode==0,'sck-helper-compile-failed:'+result.stderr[-2000:])
        require(Path(tmp).is_file() and Path(tmp).stat().st_size>0,'sck-helper-compiler-produced-no-binary')
        os.chmod(tmp,0o700);os.replace(tmp,target);return target
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

class PublicCGWindow:
    capture_source='macos-public-screencapturekit'
    capture_method='ScreenCaptureKit/SCScreenshotManager/desktopIndependentWindow'
    def __init__(self):
        require(sys.platform=='darwin','macos-cgwindow-unavailable')
        self.cg=C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.proc=C.CDLL('/usr/lib/libproc.dylib');self.capture_scope=None
        def fn(lib,name,result,*args):
            try:f=getattr(lib,name)
            except AttributeError:raise EvidenceError('public-api-unavailable:'+name)
            f.restype=result;f.argtypes=list(args);return f
        p=C.c_void_p;z=C.c_size_t
        fn(self.cg,'CGPreflightScreenCaptureAccess',C.c_bool)
        fn(self.cg,'CGWindowListCopyWindowInfo',p,C.c_uint32,C.c_uint32)
        fn(self.cf,'CFPropertyListCreateData',p,p,p,C.c_long,C.c_ulong,p)
        fn(self.cf,'CFDataGetLength',C.c_long,p);fn(self.cf,'CFDataGetBytePtr',p,p);fn(self.cf,'CFRelease',None,p)
        fn(self.proc,'proc_pidpath',C.c_int,C.c_int,p,C.c_uint32)
    def preflight(self):return bool(self.cg.CGPreflightScreenCaptureAccess())
    def process_path(self,pid):
        buf=C.create_string_buffer(4096);require(self.proc.proc_pidpath(pid,buf,len(buf))>0,'chrome-pid-path-unavailable');return os.fsdecode(buf.value)
    def windows(self):
        array=self.cg.CGWindowListCopyWindowInfo(1|16,0);require(array,'window-inventory-unavailable');data=None
        try:
            data=self.cf.CFPropertyListCreateData(None,array,100,0,None);require(data,'window-inventory-not-decodable')
            return plistlib.loads(C.string_at(self.cf.CFDataGetBytePtr(data),self.cf.CFDataGetLength(data)))
        finally:
            if data:self.cf.CFRelease(data)
            self.cf.CFRelease(array)
    def set_capture_scope(self,pid,title):self.capture_scope=(pid,title)
    def capture(self,window_id,path):
        require(self.preflight(),'screen-capture-access-unavailable-no-permission-requested')
        require(self.capture_scope is not None,'sck-explicit-pid-title-scope-required')
        pid,title=self.capture_scope;helper=build_helper()
        result=subprocess.run([str(helper),'--pid',str(pid),'--window-id',str(window_id),'--title',title,'--out',str(Path(path).resolve())],capture_output=True,text=True,timeout=45)
        try:reported=json.loads(result.stdout)
        except ValueError:raise EvidenceError('sck-helper-response-invalid:'+result.stderr[-1000:])
        require(result.returncode==0 and reported.get('ok') is True,'sck-helper-failed:'+str(reported.get('error')))
        require(reported.get('backend')=='ScreenCaptureKit/SCScreenshotManager' and reported.get('pid')==pid and reported.get('window_id')==window_id and reported.get('title')==title,'sck-helper-scope-mismatch')
        require(reported.get('whole_window') is True and reported.get('window_activation_used') is False and reported.get('permission_request_used') is False and reported.get('pixel_actions_used') is False,'sck-helper-safety-mismatch')
        return {'width':reported['width'],'height':reported['height']}

def choose_window(items,pid,window_id,title):
    target=[w for w in items if w.get('kCGWindowNumber')==window_id];require(len(target)==1,'explicit-window-not-unique')
    w=target[0];require(w.get('kCGWindowOwnerPID')==pid and w.get('kCGWindowOwnerName')=='Google Chrome','window-pid-owner-mismatch')
    require(w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True and w.get('kCGWindowSharingState') in (1,2),'window-not-capturable')
    require(w.get('kCGWindowName') in (title,title+' - Google Chrome'),'window-active-tab-title-mismatch')
    normal=[i for i in items if i.get('kCGWindowLayer')==0 and i.get('kCGWindowIsOnscreen') is True]
    require(normal and normal[0].get('kCGWindowNumber')==window_id,'chrome-target-window-not-frontmost')
    same=[i for i in normal if i.get('kCGWindowOwnerPID')==pid and i.get('kCGWindowName')==w['kCGWindowName']]
    require(len(same)==1,'chrome-window-tab-title-ambiguous')
    return {k:w.get(k) for k in ('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowName','kCGWindowLayer','kCGWindowIsOnscreen','kCGWindowSharingState')}

def capture_evidence(pid,window_id,dom_path,out,native=None,at=None):
    require(type(pid) is int and pid>0 and type(window_id) is int and window_id>0,'explicit-positive-pid-window-required')
    proof=scope_proof(dom_path,at);out=Path(out).resolve();meta=out.with_suffix('.json')
    require(out.suffix.lower()=='.png' and not out.exists() and not meta.exists(),'new-png-output-required');out.parent.mkdir(parents=True,exist_ok=True)
    native=native or PublicCGWindow();require(native.preflight(),'screen-capture-access-unavailable-no-permission-requested')
    executable=native.process_path(pid);require(executable.endswith('/Google Chrome.app/Contents/MacOS/Google Chrome'),'pid-is-not-chrome-main-process')
    before=choose_window(native.windows(),pid,window_id,proof['title'])
    if hasattr(native,'set_capture_scope'):native.set_capture_scope(pid,proof['title'])
    fd,tmp=tempfile.mkstemp(prefix='.window-evidence-',suffix='.png',dir=out.parent);os.close(fd)
    try:
        dimensions=native.capture(window_id,tmp)
        require(all(type(dimensions.get(k)) is int and dimensions[k]>0 for k in ('width','height')),'capture-dimensions-invalid')
        after=choose_window(native.windows(),pid,window_id,proof['title']);require(before==after,'window-changed-during-capture')
        require(sha(dom_path)==proof['sha256'],'dom-evidence-changed-during-capture')
        require(Path(tmp).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),'capture-output-not-png')
        os.replace(tmp,out)
        metadata={'version':1,'source':getattr(native,'capture_source','macos-public-cgwindow'),'browser_backend':'local-dom-bridge','capture_method':getattr(native,'capture_method','mock-whole-window'),'captured_at':stamp(),'pid':pid,'window_id':window_id,'executable':executable,'window':after,'dom_evidence':proof,'png':{'path':str(out),'sha256':sha(out),**dimensions},'pixel_actions_used':False,'live_accepted':False,'content_review_required':True,'coverage_verified':False,'limitations':['DOM headers may be outside the visible viewport; manually verify actual image coverage before registering workflow screenshot.','No post-capture DOM acquisition was performed; execution role must revalidate active tab/group/date after capture.']}
        atomic(meta,metadata);return {'png':str(out),'metadata':str(meta),'sha256':metadata['png']['sha256'],'coverage_verified':False}
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build-helper',action='store_true');p.add_argument('--pid',type=int);p.add_argument('--window-id',type=int);p.add_argument('--dom-evidence',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    try:
        if a.build_helper:
            require(all(v is None for v in (a.pid,a.window_id,a.dom_evidence,a.out)),'build-only-does-not-accept-capture-arguments')
            print(json.dumps({'ok':True,'compile_only':True,'capture_attempted':False,'helper':str(build_helper())},ensure_ascii=False));return 0
        require(a.dom_evidence is not None and a.out is not None,'dom-evidence-and-output-required')
        print(json.dumps({'ok':True,**capture_evidence(a.pid,a.window_id,a.dom_evidence,a.out)},ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e),'live_accepted':False},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
