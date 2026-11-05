"""Read-only macOS Chrome OUTER UI diagnostic for connection repair.
No business page content, keyboard input, profiles or debugger. Optional semantic action opens ONLY the main Chrome extensions menu.
This is not a replacement browser driver; AXWebArea descendants are omitted.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import time

BUNDLE='com.google.Chrome'
APP=Path('/Applications/Google Chrome.app')

class AXError(RuntimeError):pass

class ChromeShellInspector:
    def __init__(self,expected_pid=None):
        if sys.platform!='darwin':raise AXError('macos-required')
        self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        self.ax=C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        self.cg=C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
        def fn(lib,name,restype,*args):
            f=getattr(lib,name);f.restype=restype;f.argtypes=list(args);return f
        p=C.c_void_p;i=C.c_int;z=C.c_long
        fn(self.cf,'CFStringCreateWithCString',p,p,C.c_char_p,C.c_uint32)
        fn(self.cf,'CFStringGetLength',z,p)
        fn(self.cf,'CFStringGetMaximumSizeForEncoding',z,z,C.c_uint32)
        fn(self.cf,'CFStringGetCString',C.c_bool,p,C.c_void_p,z,C.c_uint32)
        fn(self.cf,'CFGetTypeID',C.c_ulong,p)
        for name in ['CFStringGetTypeID','CFBooleanGetTypeID','CFArrayGetTypeID','CFNumberGetTypeID','CFURLGetTypeID']:
            fn(self.cf,name,C.c_ulong)
        fn(self.cf,'CFBooleanGetValue',C.c_bool,p)
        fn(self.cf,'CFURLGetString',p,p)
        fn(self.cf,'CFArrayGetCount',z,p)
        fn(self.cf,'CFArrayGetValueAtIndex',p,p,z)
        fn(self.cf,'CFNumberGetValue',C.c_bool,p,i,p)
        fn(self.cf,'CFRetain',p,p);fn(self.cf,'CFRelease',None,p)
        fn(self.cf,'CFEqual',C.c_bool,p,p)
        fn(self.ax,'AXIsProcessTrusted',C.c_bool)
        fn(self.ax,'AXUIElementCreateApplication',p,i)
        fn(self.ax,'AXUIElementCopyAttributeValue',i,p,p,C.POINTER(p))
        fn(self.ax,'AXUIElementSetAttributeValue',i,p,p,p)
        fn(self.ax,'AXUIElementPerformAction',i,p,p)
        fn(self.ax,'AXUIElementCopyActionNames',i,p,C.POINTER(p))
        fn(self.ax,'AXUIElementIsAttributeSettable',i,p,p,C.POINTER(C.c_bool))
        fn(self.ax,'AXUIElementSetMessagingTimeout',i,p,C.c_float)
        fn(self.cg,'CGEventCreateKeyboardEvent',p,p,C.c_uint16,C.c_bool)
        fn(self.cg,'CGEventSetFlags',None,p,C.c_uint64)
        fn(self.cg,'CGEventPostToPid',None,i,p)
        if not self.ax.AXIsProcessTrusted():raise AXError('accessibility-permission-required')
        with open(APP/'Contents/Info.plist','rb') as f:info=plistlib.load(f)
        if info.get('CFBundleIdentifier')!=BUNDLE:raise AXError('app-bundle-mismatch')
        exe=str(APP/'Contents/MacOS'/info['CFBundleExecutable'])
        procs=subprocess.run(['/usr/bin/pgrep','-fx',re.escape(exe)],capture_output=True,text=True,timeout=5)
        ids=procs.stdout.split()
        self.refs=[];self.by_path={}
        if expected_pid is not None:
            if str(expected_pid) not in ids:raise AXError('app-process-changed')
            ids=[str(expected_pid)]
        candidates=[]
        for pid in ids:
            root=self.ax.AXUIElementCreateApplication(int(pid));self.ax.AXUIElementSetMessagingTimeout(root,1)
            windows=self.array(root,'AXWindows')
            if any(self.get(w,'AXSubrole')=='AXStandardWindow' for w in windows):candidates.append((int(pid),root))
            else:self.cf.CFRelease(root)
        if len(candidates)!=1:
            for _,root in candidates:self.cf.CFRelease(root)
            for v in self.refs:self.cf.CFRelease(v)
            raise AXError('app-not-running-or-ambiguous')
        self.pid,self.root=candidates[0]

    def string(self,s):return self.cf.CFStringCreateWithCString(None,str(s).encode(),0x08000100)
    def value(self,e,key):
        name=self.string(key);out=C.c_void_p()
        try:error=self.ax.AXUIElementCopyAttributeValue(e,name,C.byref(out))
        finally:self.cf.CFRelease(name)
        if error!=0 or not out.value:return None
        self.refs.append(out.value);return out.value
    def decode(self,v):
        if not v:return None
        typ=self.cf.CFGetTypeID(v)
        if typ==self.cf.CFStringGetTypeID():
            n=self.cf.CFStringGetMaximumSizeForEncoding(self.cf.CFStringGetLength(v),0x08000100)+1
            if n>1_000_000:raise AXError('ax-text-too-large')
            b=C.create_string_buffer(n)
            if self.cf.CFStringGetCString(v,b,n,0x08000100):return b.value.decode('utf-8')
        if typ==self.cf.CFBooleanGetTypeID():return bool(self.cf.CFBooleanGetValue(v))
        if typ==self.cf.CFURLGetTypeID():return self.decode(self.cf.CFURLGetString(v))
        if typ==self.cf.CFNumberGetTypeID():
            n=C.c_longlong();self.cf.CFNumberGetValue(v,4,C.byref(n));return n.value
        return None
    def get(self,e,key):return self.decode(self.value(e,key))
    def array(self,e,key):
        v=self.value(e,key)
        if not v or self.cf.CFGetTypeID(v)!=self.cf.CFArrayGetTypeID():return []
        return [self.cf.CFArrayGetValueAtIndex(v,i) for i in range(self.cf.CFArrayGetCount(v))]
    def tree(self):
        self.by_path={};count=0;deadline=time.monotonic()+25;truncated=False
        def walk(e,path,depth):
            nonlocal count,truncated
            if count>=2500 or depth>22 or time.monotonic()>deadline:truncated=True;return None
            count+=1;self.by_path[tuple(path)]=e
            row={'path':path,'role':self.get(e,'AXRole')}
            if row['role']=='AXWebArea':
                url=self.get(e,'AXURL') or ''
                if not url.startswith('chrome-extension://'):
                    row.update(children=[],web_content_omitted=True);return row
            for key in ['AXMain','AXFocused','AXMinimized','AXTitle','AXDescription','AXValue','AXIdentifier','AXRoleDescription','AXSubrole','AXPlaceholderValue','AXHelp','AXEnabled','AXSelected','AXURL','AXFilename']:
                val=self.get(e,key)
                if key=='AXValue' and row['role'] in ('AXTextField','AXSecureTextField','AXTextArea','AXComboBox'):val='[input value omitted]'
                if isinstance(val,str):val=re.sub(r'(?:sk-[A-Za-z0-9_-]{12,}|eyJ[A-Za-z0-9_.-]{24,}|[A-Fa-f0-9]{40,})','[opaque value omitted]',val)
                if val is not None and val!='':row[key]=val
            actions=C.c_void_p()
            if self.ax.AXUIElementCopyActionNames(e,C.byref(actions))==0 and actions.value:
                self.refs.append(actions.value)
                row['actions']=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(self.cf.CFArrayGetCount(actions.value))]
            if row['role'] in ('AXTextArea','AXTextField','AXComboBox','AXRow','AXCell'):
                for key in ['AXValue','AXSelected','AXFocused']:
                    name=self.string(key);flag=C.c_bool()
                    try:err=self.ax.AXUIElementIsAttributeSettable(e,name,C.byref(flag))
                    finally:self.cf.CFRelease(name)
                    if err==0 and flag.value:row.setdefault('settable',[]).append(key)
            row['children']=[]
            for index,child in enumerate(self.array(e,'AXChildren')):
                node=walk(child,path+[index],depth+1)
                if node is not None:row['children'].append(node)
                if truncated:break
            return row
        result=walk(self.root,[],0)
        return {'ok':True,'bundle_id':BUNDLE,'pid':self.pid,'tree':result,'node_count':count,'truncated':truncated}
    def open_extensions_menu(self):
        snapshot=self.tree()
        def flat(node):
            yield node
            for child in node.get('children',[]):yield from flat(child)
        windows=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXMain') is True]
        if len(windows)!=1:raise AXError('main-chrome-window-not-unique')
        buttons=[n for n in flat(windows[0]) if n.get('role')=='AXPopUpButton' and n.get('AXTitle')=='扩展程序' and n.get('AXDescription')=='扩展程序' and 'AXPress' in n.get('actions',[])]
        if len(buttons)!=1:raise AXError('extensions-menu-button-not-unique')
        element=self.by_path[tuple(buttons[0]['path'])];action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(element,action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('extensions-menu-open-failed:'+str(error))
        return {'ok':True,'action':'opened-existing-extensions-menu','business_actions':False}
    def open_existing_extension(self,name):
        if name not in ('BrowserGPT','ChatGPT'):raise AXError('unobserved-extension-name')
        snapshot=self.tree()
        def flat(node):
            yield node
            for child in node.get('children',[]):yield from flat(child)
        windows=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXMain') is True]
        if len(windows)!=1:raise AXError('main-chrome-window-not-unique')
        buttons=[n for n in flat(windows[0]) if n.get('role')=='AXButton' and n.get('AXTitle')==name and n.get('AXDescription')==name and 'AXPress' in n.get('actions',[])]
        if len(buttons)!=1:raise AXError('existing-extension-popup-button-not-unique')
        element=self.by_path[tuple(buttons[0]['path'])];action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(element,action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('existing-extension-popup-open-failed:'+str(error))
        return {'ok':True,'action':'opened-existing-extension-popup','name':name,'business_actions':False}
    def open_local_dom_control(self):
        snapshot=self.tree()
        def flat(node):
            yield node
            for child in node.get('children',[]):yield from flat(child)
        windows=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXMain') is True]
        if len(windows)!=1:raise AXError('main-chrome-window-not-unique')
        targets=[n for n in flat(windows[0]) if n.get('role')=='AXPopUpButton' and str(n.get('AXTitle','')).split('\n')[0]=='Open local DOM bridge control' and 'AXPress' in n.get('actions',[])]
        if len(targets)!=1:raise AXError('observed-local-dom-control-button-not-unique')
        action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(self.by_path[tuple(targets[0]['path'])],action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('local-dom-control-open-failed:'+str(error))
        return {'ok':True,'action':'opened-existing-local-dom-control','business_actions':False}
    def apply_reviewed_bridge_update(self):
        # Only our explicitly installed/bound extension control page can be refreshed.
        config=Path(__file__).resolve().parents[2]/'chrome-dom-export/.local/config.json'
        ident=json.loads(config.read_text()).get('extensionId')
        if not isinstance(ident,str) or not re.fullmatch('[a-p]{32}',ident):raise AXError('bound-extension-id-missing')
        snapshot=self.tree();expected='chrome-extension://'+ident+'/control.html'
        def flat(node):
            yield node
            for child in node.get('children',[]):yield from flat(child)
        windows=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXMain') is True]
        if len(windows)!=1:raise AXError('main-chrome-window-not-unique')
        areas=[n for n in flat(windows[0]) if n.get('role')=='AXWebArea' and str(n.get('AXURL','')).split('?')[0]==expected]
        if len(areas)!=1:raise AXError('bound-extension-control-page-not-unique')
        targets=[n for n in flat(areas[0]) if n.get('role')=='AXButton' and (n.get('AXTitle') or n.get('AXDescription'))=='加载已审核扩展更新' and n.get('AXEnabled') is True]
        if len(targets)!=1:raise AXError('reviewed-extension-update-button-not-unique')
        element=self.by_path[tuple(targets[0]['path'])]
        if 'AXPress' in targets[0].get('actions',[]):
            action=self.string('AXPress')
            try:error=self.ax.AXUIElementPerformAction(element,action)
            finally:self.cf.CFRelease(action)
            if error:raise AXError('reviewed-bridge-update-failed:'+str(error))
        else:
            # Chrome HTML buttons may omit AXPress but expose semantic focus.
            front=self.string('AXFrontmost');true_value=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
            try:
                if self.ax.AXUIElementSetAttributeValue(self.root,front,true_value):raise AXError('reviewed-update-frontmost-failed')
            finally:self.cf.CFRelease(front)
            focused=self.string('AXFocused');can_set=C.c_bool()
            try:
                error=self.ax.AXUIElementIsAttributeSettable(element,focused,C.byref(can_set))
                if error or not can_set.value:raise AXError('reviewed-update-button-not-focusable')
                true_value=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
                if self.ax.AXUIElementSetAttributeValue(element,focused,true_value):raise AXError('reviewed-update-focus-failed')
            finally:self.cf.CFRelease(focused)
            # AX focus assignment is asynchronous in Chrome. Only wait for the
            # exact already-verified button; never Tab through arbitrary UI.
            actual=self.value(self.root,'AXFocusedUIElement')
            deadline=time.monotonic()+2
            while (not actual or not self.cf.CFEqual(actual,element)) and time.monotonic()<deadline:
                time.sleep(0.05)
                actual=self.value(self.root,'AXFocusedUIElement')
            if not actual or not self.cf.CFEqual(actual,element):
                actual_role=self.get(actual,'AXRole') if actual else None
                actual_title=self.get(actual,'AXTitle') if actual else None
                raise AXError('reviewed-update-focus-not-verified: '+str(actual_role)+' '+str(actual_title))
            for down in (True,False):
                event=self.cg.CGEventCreateKeyboardEvent(None,49,down)
                if not event:raise AXError('reviewed-update-key-failed')
                try:self.cg.CGEventSetFlags(event,0);self.cg.CGEventPostToPid(self.pid,event)
                finally:self.cf.CFRelease(event)
        return {'ok':True,'action':'refreshed-existing-reviewed-extension','chrome_restarted':False,'business_actions':False}
    def close(self):
        for v in reversed(self.refs):self.cf.CFRelease(v)
        self.refs=[]
        if self.root:self.cf.CFRelease(self.root);self.root=None

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--open-extensions-menu',action='store_true');parser.add_argument('--open-existing-extension',choices=['BrowserGPT','ChatGPT']);parser.add_argument('--open-local-dom-control',action='store_true');parser.add_argument('--apply-reviewed-bridge-update',action='store_true');args=parser.parse_args()
    native=None
    try:
        native=ChromeShellInspector()
        result=native.apply_reviewed_bridge_update() if args.apply_reviewed_bridge_update else native.open_local_dom_control() if args.open_local_dom_control else native.open_existing_extension(args.open_existing_extension) if args.open_existing_extension else native.open_extensions_menu() if args.open_extensions_menu else native.tree()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (AXError,OSError,subprocess.SubprocessError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));sys.exit(2)
    finally:
        if native:native.close()
