#!/usr/bin/env python3
"""One public AXPress on the EXISTING extension action, target page unchanged.

Not activation, not control-page tick, not programmatic activeTab authorization.
Only the subsequent Chrome capture API can prove actual screenshot permission.
No browser launch, page AX reads, coordinates, keyboard, or OS permission request.
"""
import argparse
import ctypes as C
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import bridge

LABEL='Open local DOM bridge control'
from visible_capture import SAFETY
class GrantError(ValueError):pass
def need(ok,code):
    if not ok:raise GrantError(code)
def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,value):
    fd,tmp=tempfile.mkstemp(prefix='.action-grant-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def checked_executable_identity(path):
    # Shared read-only constructor identity; no AX/input action is performed.
    exe='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if path==exe:return {'executable':exe}
    import chrome_process_identity as identity
    need(isinstance(path,str) and identity.CLONE.fullmatch(path) is not None,'chrome-main-executable-path-mismatch')
    return {'executable':path,'executable_identity':identity.verify(path)}

class NativeAction:
    def __init__(self,pid):
        need(sys.platform=='darwin','macos-required');self.pid=pid;self.refs=[];self.nodes={}
        exe='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        found=subprocess.run(['/usr/bin/pgrep','-fx',re.escape(exe)],capture_output=True,text=True,timeout=5)
        need(str(pid) in found.stdout.split(),'expected-chrome-main-pid-not-running')
        proc=C.CDLL('/usr/lib/libproc.dylib');proc.proc_pidpath.restype=C.c_int;proc.proc_pidpath.argtypes=[C.c_int,C.c_void_p,C.c_uint32]
        executable=C.create_string_buffer(4096);need(proc.proc_pidpath(pid,executable,len(executable))>0,'chrome-main-executable-path-unavailable')
        self.process_identity=checked_executable_identity(os.fsdecode(executable.value))
        self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax=C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        def fn(lib,name,result,*args):f=getattr(lib,name);f.restype=result;f.argtypes=list(args)
        p=C.c_void_p;i=C.c_int;z=C.c_long
        for name in ('CFStringGetTypeID','CFBooleanGetTypeID','CFArrayGetTypeID'):fn(self.cf,name,C.c_ulong)
        fn(self.cf,'CFEqual',C.c_bool,p,p);fn(self.cf,'CFGetTypeID',C.c_ulong,p);fn(self.cf,'CFRelease',None,p)
        fn(self.cf,'CFStringCreateWithCString',p,p,C.c_char_p,C.c_uint32)
        fn(self.cf,'CFStringGetLength',z,p);fn(self.cf,'CFStringGetMaximumSizeForEncoding',z,z,C.c_uint32)
        fn(self.cf,'CFStringGetCString',C.c_bool,p,p,z,C.c_uint32);fn(self.cf,'CFBooleanGetValue',C.c_bool,p)
        fn(self.cf,'CFArrayGetCount',z,p);fn(self.cf,'CFArrayGetValueAtIndex',p,p,z)
        fn(self.ax,'AXIsProcessTrusted',C.c_bool);fn(self.ax,'AXUIElementCreateApplication',p,i)
        fn(self.ax,'AXUIElementSetMessagingTimeout',i,p,C.c_float)
        fn(self.ax,'AXUIElementCopyAttributeValue',i,p,p,C.POINTER(p))
        fn(self.ax,'AXUIElementCopyActionNames',i,p,C.POINTER(p));fn(self.ax,'AXUIElementPerformAction',i,p,p)
        need(self.ax.AXIsProcessTrusted(),'existing-accessibility-permission-required-no-request')
        self.root=self.ax.AXUIElementCreateApplication(pid);self.ax.AXUIElementSetMessagingTimeout(self.root,1)
    def string(self,value):return self.cf.CFStringCreateWithCString(None,value.encode(),0x08000100)
    def raw(self,element,key):
        name=self.string(key);out=C.c_void_p()
        try:error=self.ax.AXUIElementCopyAttributeValue(element,name,C.byref(out))
        finally:self.cf.CFRelease(name)
        if error or not out.value:return None
        self.refs.append(out.value);return out.value
    def decode(self,value):
        if not value:return None
        typ=self.cf.CFGetTypeID(value)
        if typ==self.cf.CFBooleanGetTypeID():return bool(self.cf.CFBooleanGetValue(value))
        if typ==self.cf.CFStringGetTypeID():
            size=self.cf.CFStringGetMaximumSizeForEncoding(self.cf.CFStringGetLength(value),0x08000100)+1
            need(size<100000,'outer-AX-text-too-large');buf=C.create_string_buffer(size)
            if self.cf.CFStringGetCString(value,buf,size,0x08000100):return buf.value.decode()
        return None
    def get(self,e,key):return self.decode(self.raw(e,key))
    def children(self,e,key='AXChildren'):
        value=self.raw(e,key)
        if not value or self.cf.CFGetTypeID(value)!=self.cf.CFArrayGetTypeID():return []
        return [self.cf.CFArrayGetValueAtIndex(value,i) for i in range(self.cf.CFArrayGetCount(value))]
    def tree(self,title):
        need(self.get(self.root,'AXFrontmost') is True,'chrome-not-frontmost-no-activation')
        windows=[w for w in self.children(self.root,'AXWindows') if self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True]
        need(len(windows)==1,'main-chrome-window-not-unique');self.window=windows[0]
        need(self.get(self.window,'AXTitle') in (title,title+' - Google Chrome'),'outer-window-title-mismatch')
        self.nodes={};count=0;deadline=time.monotonic()+20
        def walk(e,path,depth):
            nonlocal count
            count+=1;need(count<=2500 and depth<=22 and time.monotonic()<deadline,'outer-tree-incomplete')
            role=self.get(e,'AXRole');self.nodes[tuple(path)]=e;row={'role':role,'path':path,'children':[]}
            if role=='AXWebArea':row['web_content_omitted']=True;return row
            for key in ('AXTitle','AXDescription','AXEnabled'):
                value=self.get(e,key)
                if value is not None:row[key]=value
            actions=C.c_void_p()
            if self.ax.AXUIElementCopyActionNames(e,C.byref(actions))==0 and actions.value:
                self.refs.append(actions.value);row['actions']=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(self.cf.CFArrayGetCount(actions.value))]
            row['children']=[walk(c,path+[i],depth+1) for i,c in enumerate(self.children(e))];return row
        return walk(self.window,[],0)
    def press(self,node,title):
        need(self.get(self.window,'AXMain') is True and self.get(self.root,'AXFrontmost') is True and self.get(self.window,'AXTitle') in (title,title+' - Google Chrome'),'window-changed-before-extension-action')
        actual=self.raw(self.root,'AXMainWindow');need(actual and self.cf.CFEqual(actual,self.window),'main-window-changed-before-extension-action')
        e=self.nodes[tuple(node['path'])]
        need(self.get(e,'AXRole')==node['role'] and self.get(self.nodes[tuple(node['toolbar_path'])],'AXRole')=='AXToolbar','extension-toolbar-ancestry-changed')
        toolbar=self.nodes[tuple(node['toolbar_path'])];parent=self.raw(e,'AXParent');in_toolbar=False
        for _ in range(22):
            if not parent or self.get(parent,'AXRole')=='AXWebArea':break
            if self.cf.CFEqual(parent,toolbar):in_toolbar=True;break
            parent=self.raw(parent,'AXParent')
        need(in_toolbar,'extension-action-left-reviewed-toolbar')
        need(self.get(e,'AXEnabled') is True and (self.get(e,'AXTitle') or self.get(e,'AXDescription') or '').split('\n')[0]==LABEL,'extension-action-changed')
        action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(e,action)
        finally:self.cf.CFRelease(action)
        need(error==0,'extension-action-press-outcome-unknown')
    def close(self):
        for v in reversed(self.refs):self.cf.CFRelease(v)
        self.cf.CFRelease(self.root)

def target(tree):
    found=[]
    def walk(n,toolbar=None):
        if n.get('role')=='AXWebArea':return
        if n.get('role')=='AXToolbar':toolbar=n
        if toolbar is not None and n.get('role') in ('AXButton','AXPopUpButton') and n.get('AXEnabled') is True and 'AXPress' in n.get('actions',[]) and (n.get('AXTitle') or n.get('AXDescription') or '').split('\n')[0]==LABEL:
            found.append({**n,'toolbar_path':toolbar['path']})
        for c in n.get('children',[]):walk(c,toolbar)
    walk(tree)
    need(len(found)==1,'existing-extension-action-not-unique-or-not-visible-in-toolbar');return found[0]

def observe(scope,request,extension_id):
    response=request({'op':'capture-grant-status',**scope});need(response.get('ok') is True,'capture-scope-or-bridge-unavailable')
    result=response['result'];need(result.get('safety_version')==SAFETY and result.get('extensionId')==extension_id,'audited-bound-extension-required')
    need(all(result.get('scope',{}).get(k)==v for k,v in scope.items()),'capture-grant-status-scope-mismatch')
    return result

def invoke(scope,pid,out,extension_id,request=bridge.request,native_factory=NativeAction):
    need(type(pid) is int and pid>0,'explicit-chrome-pid-required');need(isinstance(extension_id,str) and re.fullmatch('[a-p]{32}',extension_id),'bound-extension-id-required');bridge.validate_command({'op':'capture-grant-status',**scope})
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_name(out.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():
            old=json.loads(out.read_text());need(old.get('scope')==scope and old.get('pid')==pid,'action-journal-conflict')
            return {**old,'replayed':False,'already_recorded':True}
        before=observe(scope,request,extension_id);native=native_factory(pid)
        try:
            node=target(native.tree(before['scope']['title']))
            # Re-query real active/focused bridge scope immediately before sole AXPress.
            fresh=observe(scope,request,extension_id);need(fresh['scope']==before['scope'],'capture-target-changed-before-action')
            journal={'scope':scope,'pid':pid,'state':'unknown','intent_at':now(),'before':before,'target_path':node['path'],
                     'action':LABEL,'permission_granted':False,'capture_attempted':False,'replayed':False}
            atomic(out,journal)
            native.press(node,before['scope']['title'])
            old=(before.get('grant') or {}).get('nonce')
            for attempt in range(3):
                after=observe(scope,request,extension_id);grant=after.get('grant') or {}
                need(after['scope']==before['scope'],'capture-target-changed-after-action')
                if after.get('invocationObserved') is True and grant.get('nonce') and grant['nonce']!=old:break
                if attempt<2:time.sleep(.2)  # Passive observation only; never another AXPress.
            need(after['scope']==before['scope'] and after.get('invocationObserved') is True and grant.get('nonce') and grant['nonce']!=old and grant.get('via')=='chrome.action.onClicked','real-extension-invocation-not-observed-no-retry')
            need(datetime.fromisoformat(grant['invokedAt'].replace('Z','+00:00'))>=datetime.fromisoformat(journal['intent_at']),'stale-action-invocation')
            journal.update(state='action-invocation-observed-permission-unproven',after=after,completed_at=now())
            atomic(out,journal);return journal
        except Exception as error:
            if 'journal' in locals():journal['error']=str(error);atomic(out,journal)
            raise
        finally:native.close()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid',type=int,required=True);p.add_argument('--tab-id',type=int,required=True);p.add_argument('--window-id',type=int,required=True);p.add_argument('--groupid',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=invoke({'tabId':a.tab_id,'windowId':a.window_id,'groupid':a.groupid},a.pid,a.out,bridge.read_config()['extensionId'])
    print(json.dumps({'ok':True,'state':result['state'],'journal':str(a.out.resolve()),'permission_granted':False,'capture_attempted':False,'already_recorded':result.get('already_recorded',False)},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as error:print(json.dumps({'ok':False,'error':str(error)},ensure_ascii=False));raise SystemExit(2)
