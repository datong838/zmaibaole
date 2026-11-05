"""macOS public Accessibility API via ctypes. No pixel/clipboard/private API.

Only the target application's AX tree is read. Paths are diagnostic, never click
coordinates. Mutations require a fresh semantic match in messenger.py.
"""
import ctypes as C
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import time
import performance_trace as performance
from main_window import native_main_window
from public_app_activation import activate_existing,ActivationError

BUNDLE='com.tencent.WeWorkMac'
APP=Path('/Applications/企业微信.app')

class AXError(RuntimeError):pass
class _ChildrenBatchFallback(AXError):pass
_CHILDREN_FALLBACK=object()

class Native:
    @performance.stage('native.create')
    def __init__(self,expected_pid=None,*,capability_scope='full'):
        if capability_scope not in ('full','sender-required'):raise AXError('capability-scope-invalid')
        self.capability_scope=capability_scope
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
        fn(self.cf,'CFArrayCreate',p,p,C.POINTER(p),z,p)
        fn(self.cf,'CFNumberGetValue',C.c_bool,p,i,p)
        fn(self.cf,'CFRetain',p,p);fn(self.cf,'CFRelease',None,p)
        fn(self.cf,'CFEqual',C.c_bool,p,p)
        fn(self.cf,'CFDataGetTypeID',C.c_ulong)
        fn(self.cf,'CFDataGetLength',z,p)
        fn(self.cf,'CFDataGetBytePtr',p,p)
        fn(self.cf,'CFAttributedStringGetTypeID',C.c_ulong)
        fn(self.ax,'AXIsProcessTrusted',C.c_bool)
        fn(self.ax,'AXUIElementCreateApplication',p,i)
        fn(self.ax,'AXUIElementGetTypeID',C.c_ulong)
        fn(self.ax,'AXUIElementCopyAttributeValue',i,p,p,C.POINTER(p))
        fn(self.ax,'AXUIElementCopyMultipleAttributeValues',i,p,p,C.c_uint32,C.POINTER(p))
        fn(self.ax,'AXValueGetTypeID',C.c_ulong)
        fn(self.ax,'AXValueGetType',C.c_uint32,p)
        fn(self.ax,'AXValueGetValue',C.c_bool,p,C.c_uint32,p)
        fn(self.ax,'AXUIElementSetAttributeValue',i,p,p,p)
        fn(self.ax,'AXUIElementPerformAction',i,p,p)
        fn(self.ax,'AXUIElementCopyActionNames',i,p,C.POINTER(p))
        fn(self.ax,'AXUIElementCopyAttributeNames',i,p,C.POINTER(p))
        fn(self.ax,'AXUIElementCopyParameterizedAttributeNames',i,p,C.POINTER(p))
        fn(self.ax,'AXValueCreate',p,i,p)
        fn(self.ax,'AXUIElementCopyParameterizedAttributeValue',i,p,p,p,C.POINTER(p))
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
        self.refs=[];self.by_path={};self.input_generation=0
        if expected_pid is not None:
            if str(expected_pid) not in ids:raise AXError('app-process-changed')
            ids=[str(expected_pid)]
        candidates=[]
        for pid in ids:
            root=self.ax.AXUIElementCreateApplication(int(pid));self.ax.AXUIElementSetMessagingTimeout(root,1)
            windows=self.array(root,'AXWindows')
            if any(self.get(w,'AXTitle')=='企业微信' and self.get(w,'AXSubrole')=='AXStandardWindow' for w in windows) or len(windows)==1 and native_main_window(self,windows[0]):candidates.append((int(pid),root))
            else:self.cf.CFRelease(root)
        if len(candidates)!=1:
            for _,root in candidates:self.cf.CFRelease(root)
            for v in self.refs:self.cf.CFRelease(v)
            raise AXError('app-not-running-or-ambiguous')
        self.pid,self.root=candidates[0]

    def string(self,s):return self.cf.CFStringCreateWithCString(None,str(s).encode(),0x08000100)
    def value(self,e,key):
        name=self.string(key);out=C.c_void_p()
        try:error=performance.attribute_call(key,self.ax.AXUIElementCopyAttributeValue,e,name,C.byref(out))
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
    @performance.stage('ax.single_fallback_fields')
    def single_node_attributes(self,e,keys):
        """Strict public single-attribute fallback; never substitutes IPC failure for an empty input."""
        result={}
        for key in keys:
            name=self.string(key);value=C.c_void_p()
            try:error=performance.attribute_call(key,self.ax.AXUIElementCopyAttributeValue,e,name,C.byref(value))
            finally:self.cf.CFRelease(name)
            critical=key=='AXRole' or key=='AXValue' and result.get('AXRole') in ('AXTextArea','AXTextField','AXComboBox','AXStaticText')
            if key=='AXValue' and result.get('AXRole') in ('AXTextArea','AXTextField','AXComboBox') and error==-25205:raise AXError('single-input-value-unreadable')
            if error in (-25205,-25212):result[key]=None
            elif error==-25200 and not critical:
                result[key]=None;result.setdefault('__attribute_errors__',{})[key]=error
            elif error:raise AXError('single-attribute-unavailable:'+key+':'+str(error))
            else:
                if value.value:self.refs.append(value.value)
                result[key]=self.decode(value.value)
        return result

    @performance.stage('ax.node_attributes')
    def node_attributes(self,e,keys,*,_children=False):
        """Same public fields in one AX IPC, with unsupported values explicit.

        AXValue error placeholders are not mistaken for an empty draft. The
        API is public since macOS10.4; unsupported bulk API uses the old reads.
        """
        if not callable(getattr(getattr(self,'ax',None),'AXUIElementCopyMultipleAttributeValues',None)):
            return {k:self.get(e,k) for k in keys}
        cache=getattr(self,'_attribute_batches',None)
        if cache is None:self._attribute_batches=cache={}
        keys=tuple(keys)
        if keys not in cache:
            strings=[self.string(k) for k in keys]
            pointers=(C.c_void_p*len(strings))(*strings)
            # Null callbacks: strings are owned by this Native instance until
            # close(), while CFArray copies the pointer array immediately.
            array=self.cf.CFArrayCreate(None,pointers,len(strings),None)
            if not array:
                for value in strings:self.cf.CFRelease(value)
                raise AXError('batch-attribute-key-array-failed')
            self.refs.extend(strings+[array]);cache[keys]=array
        values=C.c_void_p();error=performance.call('ax.rpc.copy_multiple_attributes',self.ax.AXUIElementCopyMultipleAttributeValues,e,cache[keys],0,C.byref(values))
        if error in (-25201,-25208):
            # A few Qt accessibility objects reject the public bulk request.
            # The same verified AX object may still support public individual
            # reads. This is a read API fallback, never a replay of a UI action.
            if error==-25201:
                element_type=getattr(self.ax,'AXUIElementGetTypeID',None)
                if not callable(element_type) or self.cf.CFGetTypeID(e)!=element_type():raise AXError('batch-illegal-argument-element-unverified')
            if _children:raise _ChildrenBatchFallback('children-batch-use-original-fields')
            self.serial_attribute_fallbacks=getattr(self,'serial_attribute_fallbacks',0)+1
            if callable(getattr(self.ax,'AXUIElementCopyAttributeValue',None)):return self.single_node_attributes(e,keys)
            if error==-25201:raise AXError('batch-illegal-argument-single-api-unavailable')
            return {k:self.get(e,k) for k in keys}
        if error or not values.value:raise AXError('batch-attribute-read-failed:'+str(error))
        self.refs.append(values.value)
        if self.cf.CFGetTypeID(values.value)!=self.cf.CFArrayGetTypeID() or self.cf.CFArrayGetCount(values.value)!=len(keys):raise AXError('batch-attribute-result-incomplete')
        result={}
        for index,key in enumerate(keys):
            value=self.cf.CFArrayGetValueAtIndex(values.value,index)
            if _children and key=='AXChildren':
                # Preserve raw AX element handles and array order. The retained
                # outer result owns this array until the existing close().
                result[key]=([self.cf.CFArrayGetValueAtIndex(value,i) for i in range(self.cf.CFArrayGetCount(value))]
                             if value and self.cf.CFGetTypeID(value)==self.cf.CFArrayGetTypeID() else _CHILDREN_FALLBACK)
                continue
            if value and self.cf.CFGetTypeID(value)==self.ax.AXValueGetTypeID() and self.ax.AXValueGetType(value)==5: # kAXValueAXErrorType
                code=C.c_int()
                if not self.ax.AXValueGetValue(value,5,C.byref(code)):raise AXError('batch-attribute-error-unreadable')
                if key=='AXValue' and result.get('AXRole') in ('AXTextArea','AXTextField','AXComboBox') and code.value==-25205:raise AXError('batch-input-value-unreadable')
                if code.value not in (-25205,-25212):
                    critical=key=='AXRole' or key=='AXValue' and result.get('AXRole') in ('AXTextArea','AXTextField','AXComboBox','AXStaticText')
                    if code.value!=-25200 or critical:raise AXError('batch-attribute-unavailable:'+key+':'+str(code.value))
                    # Some Qt nodes report generic Failure for an optional
                    # description. Re-read that exact public field once; do not
                    # mistake any input/value failure for an empty draft.
                    single=getattr(self.ax,'AXUIElementCopyAttributeValue',None)
                    if callable(single):
                        name=self.string(key);single_value=C.c_void_p()
                        try:single_error=performance.attribute_call(key,single,e,name,C.byref(single_value))
                        finally:self.cf.CFRelease(name)
                        if single_error not in (0,-25200,-25205,-25212):raise AXError('single-attribute-unavailable:'+key+':'+str(single_error))
                        if single_error==0 and single_value.value:
                            self.refs.append(single_value.value);result[key]=self.decode(single_value.value)
                        else:result[key]=None
                    else:result[key]=self.get(e,key) # Test adapter/old API compatibility.
                    if result[key] is None:
                        result.setdefault('__attribute_errors__',{})[key]=code.value
                    continue
                result[key]=None
            else:result[key]=self.decode(value)
        self.batch_attribute_reads=getattr(self,'batch_attribute_reads',0)+1
        return result

    def node_attributes_and_children(self,e,keys):
        # Unknown adapters retain their exact original 13-field reader. Cache
        # only the static CFString key array, never any dynamic AX result.
        reader=self.node_attributes
        if getattr(reader,'__func__',None) is not Native.node_attributes or not callable(getattr(getattr(self,'ax',None),'AXUIElementCopyMultipleAttributeValues',None)):
            return reader(e,keys),_CHILDREN_FALLBACK
        try:attributes=reader(e,tuple(keys)+('AXChildren',),_children=True)
        except _ChildrenBatchFallback:return reader(e,keys),_CHILDREN_FALLBACK
        children=attributes.pop('AXChildren')
        return attributes,children

    @performance.stage('ax.full')
    def tree(self,timeout=55,max_nodes=16000,max_depth=40):
        """Retry only whole read-only snapshots after stale AX refs/busy IPC.
        The same total time budget applies; no focus/key/paste/action is repeated.
        """
        deadline=time.monotonic()+timeout;history=[]
        for attempt in range(3):
            snapshot=self._tree_once(timeout=deadline-time.monotonic(),max_nodes=max_nodes,max_depth=max_depth)
            reason=snapshot.get('truncation_reason') or ''
            transient=reason in ('window-set-changed-during-read','scoped-required-array-unavailable:AXChildren','single-attribute-unavailable:AXRole:-25201') or bool(re.fullmatch(r'(?:batch-attribute-read-failed|(?:batch|single)-attribute-unavailable:AX[A-Za-z]+):(?:-25202|-25204)',reason))
            if not snapshot.get('truncated') or not transient or attempt==2:break
            history.append({'attempt':attempt+1,'reason':reason,'node_count':snapshot.get('node_count')})
            delay=.25*(attempt+1)
            if time.monotonic()+delay>=deadline:break
            time.sleep(delay)
        snapshot['readonly_retry_history']=history
        self.last_snapshot_metadata={k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason','readonly_retry_history')}
        if 'capability_scope' in snapshot:self.last_snapshot_metadata['capability_scope']=snapshot['capability_scope']
        return snapshot

    @performance.stage('ax.full_attempt')
    def _tree_once(self,timeout=55,max_nodes=16000,max_depth=40):
        # Only real top-level windows/sheets/dialogs, with original AXChildren
        # indices. Menus are outside this snapshot, never partially traversed.
        capability_scope=getattr(self,'capability_scope','full')
        if capability_scope not in ('full','sender-required'):raise AXError('capability-scope-invalid')
        self.by_path={};count=0;deadline=time.monotonic()+timeout;truncated=False;reason=None;omitted={};seen_windows=[]
        result={'path':[],'role':'AXApplication','children':[]}
        def budget(depth):
            if count>=max_nodes:raise AXError('node-limit')
            if depth>max_depth:raise AXError('depth-limit')
            if time.monotonic()>deadline:raise AXError('deadline')
        def walk(e,path,depth,public_window=False):
            nonlocal count
            budget(depth);count+=1;self.by_path[tuple(path)]=e
            fields=['AXRole','AXTitle','AXDescription','AXValue','AXIdentifier','AXRoleDescription','AXSubrole','AXPlaceholderValue','AXHelp','AXEnabled','AXSelected','AXURL','AXFilename']
            attributes,batched_children=self.node_attributes_and_children(e,fields)
            if not isinstance(attributes.get('AXRole'),str) or not attributes['AXRole']:raise AXError('node-role-unavailable')
            row={'path':path,'role':attributes['AXRole']}
            if attributes.get('__attribute_errors__'):row['optional_attribute_errors']=attributes['__attribute_errors__']
            if row['role'] in ('AXWindow','AXSheet','AXDialog') or public_window:seen_windows.append(e)
            if public_window:row['enumerated_by']='AXWindows'
            for key in fields[1:]:
                val=attributes[key]
                if val is not None and val!='':row[key]=val
            if capability_scope=='full':
                actions=C.c_void_p()
                if performance.call('ax.rpc.copy_action_names',self.ax.AXUIElementCopyActionNames,e,C.byref(actions))==0 and actions.value:
                    self.refs.append(actions.value)
                    row['actions']=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(self.cf.CFArrayGetCount(actions.value))]
            if capability_scope=='sender-required':
                # Actual sender consumers: ui.context/search_field AXValue;
                # messenger.advance conversation AXRow AXSelected. This does
                # not enumerate all actions or all mutable AX attributes.
                keys=['AXValue'] if row['role'] in ('AXTextArea','AXTextField') else ['AXSelected'] if row['role']=='AXRow' else []
            else:keys=['AXValue','AXSelected','AXFocused'] if row['role'] in ('AXTextArea','AXTextField','AXComboBox','AXRow','AXCell') else []
            for key in keys:
                try:
                    if self.scoped_settable(e,key):row.setdefault('settable',[]).append(key)
                except AXError:pass # Optional capability; missing composer/selection fails downstream.
            required=public_window or row['role'] in ('AXWindow','AXSheet','AXDialog','AXGroup','AXSplitGroup','AXScrollArea','AXTable','AXRow','AXCell')
            child_values=self.scoped_array(e,'AXChildren',required) if batched_children is _CHILDREN_FALLBACK else batched_children
            row['children']=[walk(child,path+[i],depth+1) for i,child in enumerate(child_values or [])]
            return row
        try:
            windows=self.scoped_array(self.root,'AXWindows',True)
            children=self.scoped_array(self.root,'AXChildren',True)
            for index,child in enumerate(children):
                budget(1);role=self.get(child,'AXRole')
                if role in ('AXWindow','AXSheet','AXDialog'):result['children'].append(walk(child,[index],1))
                else:omitted[role or 'unknown']=omitted.get(role or 'unknown',0)+1
            # Qt auxiliary windows can be in public AXWindows but absent from
            # AXChildren. Read them completely using their actual public handle;
            # AXWindows is a semantic path namespace, never a pixel/index guess.
            for index,window in enumerate(windows):
                if not any(self.same_element(window,seen) for seen in seen_windows):
                    result['children'].append(walk(window,['AXWindows',index],1,public_window=True))
            if not windows or any(not any(self.same_element(w,seen) for seen in seen_windows) for w in windows):raise AXError('public-window-set-incomplete')
            after=self.scoped_array(self.root,'AXWindows',True)
            if len(windows)!=len(after) or any(not self.same_element(a,b) for a,b in zip(windows,after)):raise AXError('window-set-changed-during-read')
            budget(0)
        except AXError as error:truncated=True;reason=str(error)
        snapshot={'ok':True,'bundle_id':BUNDLE,'pid':self.pid,'tree':result,'node_count':count,'truncated':truncated,'truncation_reason':reason,'read_scope':'application-windows-complete','omitted_nonwindow_roles':omitted}
        if capability_scope=='sender-required':snapshot['capability_scope']='sender-required'
        self.last_snapshot_metadata={k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason')}
        if 'capability_scope' in snapshot:self.last_snapshot_metadata['capability_scope']=snapshot['capability_scope']
        return snapshot
    def scoped_array(self,e,key,required=False):
        value=self.value(e,key)
        if value is None:
            if required:raise AXError('scoped-required-array-unavailable:'+key)
            return None
        if self.cf.CFGetTypeID(value)!=self.cf.CFArrayGetTypeID():raise AXError('scoped-array-invalid:'+key)
        return [self.cf.CFArrayGetValueAtIndex(value,i) for i in range(self.cf.CFArrayGetCount(value))]
    def same_element(self,a,b):return bool(a and b and self.cf.CFEqual(a,b))
    def scoped_settable(self,e,key):
        name=self.string(key);flag=C.c_bool()
        try:error=performance.call('ax.rpc.is_attribute_settable',self.ax.AXUIElementIsAttributeSettable,e,name,C.byref(flag))
        finally:self.cf.CFRelease(name)
        if error:raise AXError('scoped-settable-unverified')
        return bool(flag.value)
    @performance.stage('ax.chat')
    def chat_tree(self):
        from chat_snapshot import capture
        # Only a known read race may restart the whole readonly snapshot.
        # No input/focus is part of chat_tree, and an incomplete attempt is
        # never merged into another or treated as an empty transcript.
        deadline=time.monotonic()+55;history=[]
        for attempt in range(3):
            started=time.monotonic()
            snapshot=capture(self) if attempt==0 else capture(self,timeout=max(0,deadline-started))
            history.append({'attempt':attempt+1,**{k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason','transcript_complete','discovery_node_count')},'elapsed_seconds':time.monotonic()-started})
            transient=(snapshot.get('read_scope')=='current-chat-readonly' and snapshot.get('truncated')is True and snapshot.get('transcript_complete')is False and snapshot.get('truncation_reason')=='node-role-changed-during-read')
            if not transient or attempt==2:break
            delay=.25*(attempt+1)
            if time.monotonic()+delay>=deadline:break
            time.sleep(delay)
        snapshot['readonly_retry_history']=history
        self.last_snapshot_metadata={k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason','transcript_complete','discovery_node_count','readonly_retry_history')}
        return snapshot

    def composer_guard(self,**kwargs):
        from composer_guard import capture
        snapshot=capture(self,**kwargs)
        self.last_snapshot_metadata={k:snapshot.get(k) for k in ('read_scope','node_count','truncated','truncation_reason','guard_complete','history_read','discovery_node_count')}
        return snapshot

    def public_attributes(self,node):
        element=self.by_path.get(tuple(node['path']))
        if not element:raise AXError('element-stale')
        result={}
        for label,fn in [('attributes',self.ax.AXUIElementCopyAttributeNames),('parameterized',self.ax.AXUIElementCopyParameterizedAttributeNames)]:
            values=C.c_void_p();error=fn(element,C.byref(values))
            if error==0 and values.value:
                try:result[label]=[self.decode(self.cf.CFArrayGetValueAtIndex(values.value,i)) for i in range(self.cf.CFArrayGetCount(values.value))]
                finally:self.cf.CFRelease(values.value)
            else:result[label]=[]
        return result
    def attachment_rtf(self,node):
        element=self.by_path.get(tuple(node['path']))
        if not element:raise AXError('element-stale')
        if 'AXRTFForRange' not in self.public_attributes(node)['parameterized']:raise AXError('attachment-rtf-unavailable')
        class CFRange(C.Structure):_fields_=[('location',C.c_long),('length',C.c_long)]
        text_range=CFRange(0,1);parameter=self.ax.AXValueCreate(4,C.byref(text_range))
        if not parameter:raise AXError('attachment-range-create-failed')
        name=self.string('AXRTFForRange');result=C.c_void_p()
        try:error=self.ax.AXUIElementCopyParameterizedAttributeValue(element,name,parameter,C.byref(result))
        finally:self.cf.CFRelease(name);self.cf.CFRelease(parameter)
        if error or not result.value:raise AXError('attachment-rtf-read-failed:'+str(error))
        try:
            if self.cf.CFGetTypeID(result.value)!=self.cf.CFDataGetTypeID():raise AXError('attachment-rtf-not-data')
            size=self.cf.CFDataGetLength(result.value)
            if not 0<size<=32*1024*1024:raise AXError('attachment-rtf-size-invalid')
            return C.string_at(self.cf.CFDataGetBytePtr(result.value),size)
        finally:self.cf.CFRelease(result.value)
    def attachment_attributed(self,node):
        element=self.by_path.get(tuple(node['path']))
        if not element:raise AXError('element-stale')
        if 'AXAttributedStringForRange' not in self.public_attributes(node)['parameterized']:raise AXError('attachment-attributed-unavailable')
        class CFRange(C.Structure):_fields_=[('location',C.c_long),('length',C.c_long)]
        text_range=CFRange(0,1);parameter=self.ax.AXValueCreate(4,C.byref(text_range))
        if not parameter:raise AXError('attachment-range-create-failed')
        name=self.string('AXAttributedStringForRange');result=C.c_void_p()
        try:error=self.ax.AXUIElementCopyParameterizedAttributeValue(element,name,parameter,C.byref(result))
        finally:self.cf.CFRelease(name);self.cf.CFRelease(parameter)
        if error or not result.value:raise AXError('attachment-attributed-read-failed:'+str(error))
        if self.cf.CFGetTypeID(result.value)!=self.cf.CFAttributedStringGetTypeID():
            self.cf.CFRelease(result.value);raise AXError('attachment-attributed-wrong-type')
        self.refs.append(result.value)
        return result.value
    def _mark_input(self):
        self.input_generation=getattr(self,'input_generation',0)+1
    @performance.stage('native.set_text')
    def set_text(self,node,text):
        self._mark_input()
        e=self.by_path.get(tuple(node['path']))
        if not e:raise AXError('element-stale')
        key=self.string('AXValue');value=self.string(text)
        try:error=self.ax.AXUIElementSetAttributeValue(e,key,value)
        finally:self.cf.CFRelease(key);self.cf.CFRelease(value)
        if error:raise AXError('ax-set-value-failed:'+str(error))
    @performance.stage('native.press')
    def press(self,node):
        self._mark_input()
        e=self.by_path.get(tuple(node['path']))
        if not e:raise AXError('element-stale')
        action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(e,action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('ax-press-failed:'+str(error))
    @performance.stage('native.flag')
    def flag(self,node,key,value=True):
        self._mark_input()
        e=self.root if node is None else self.by_path.get(tuple(node['path']))
        if not e:raise AXError('element-stale')
        name=self.string(key);boolean=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue' if value else 'kCFBooleanFalse').value
        try:error=self.ax.AXUIElementSetAttributeValue(e,name,boolean)
        finally:self.cf.CFRelease(name)
        if error:raise AXError('ax-set-flag-failed:'+key+':'+str(error))
    def _restore_main_window_for_focus(self,node,deadline):
        # Only the already enumerated, uniquely qualified application window.
        windows=self.scoped_array(self.root,'AXWindows',True)
        path=tuple(node['path'])
        if len(windows)!=1 or not path or path[0]!=0 or not self.same_element(windows[0],self.by_path.get((0,))):raise AXError('focus-main-window-binding-unverified')
        window=windows[0]
        if self.get(window,'AXRole')!='AXWindow' or not native_main_window(self,window):raise AXError('focus-main-window-shape-unverified')
        minimized=self.get(window,'AXMinimized')
        restore_diagnostic={'kind':'main-window-restore-observation-v1','minimized_before':minimized if type(minimized) is bool else None,'setter_issued':False,'post_set_read_count':0,'last_minimized_state':None,'restore_elapsed_seconds':0,'raise_issued':False,'message_content_recorded':False}
        self.last_snapshot_metadata={**getattr(self,'last_snapshot_metadata',{}),'main_window_restore':restore_diagnostic}
        if type(minimized) is not bool:raise AXError('focus-main-window-minimized-unverified')
        actions=C.c_void_p();error=self.ax.AXUIElementCopyActionNames(window,C.byref(actions))
        try:
            if error or not actions.value or self.cf.CFGetTypeID(actions.value)!=self.cf.CFArrayGetTypeID():raise AXError('focus-main-window-actions-unverified')
            count=self.cf.CFArrayGetCount(actions.value)
            if not 0<=count<=32:raise AXError('focus-main-window-actions-unverified')
            names=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(count)]
            if names.count('AXRaise')!=1:raise AXError('focus-main-window-raise-unsupported')
        finally:
            if actions.value:self.cf.CFRelease(actions.value)
        if minimized:
            if not self.scoped_settable(window,'AXMinimized'):raise AXError('focus-main-window-restore-unsupported')
            restore_started=time.perf_counter();restore_diagnostic['setter_issued']=True
            self.flag({'path':[0]},'AXMinimized',False)
            while True:
                restored=self.get(window,'AXMinimized')
                restore_diagnostic.update(post_set_read_count=restore_diagnostic['post_set_read_count']+1,last_minimized_state='false' if restored is False else 'true' if restored is True else 'unavailable' if restored is None else 'invalid',restore_elapsed_seconds=time.perf_counter()-restore_started)
                if restored is False:break
                remaining=deadline-time.monotonic()
                if restored is not True or remaining<=0:raise AXError('focus-main-window-restore-unverified')
                time.sleep(min(.05,remaining))
        restore_diagnostic['raise_issued']=True
        self._mark_input();action=self.string('AXRaise')
        try:error=self.ax.AXUIElementPerformAction(window,action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('focus-main-window-raise-failed:'+str(error))

    @performance.stage('native.focus')
    def focus(self,node):
        deadline=time.monotonic()+2;activation=None;frontmost=None;actual=None;matches=False
        expected=self.by_path[tuple(node['path'])]
        def fail(code):
            diagnostic={'kind':'exact-composer-focus-failure-v1','pid':self.pid,'app_frontmost':frontmost,'focused_element_present':bool(actual),'focused_element_equals_expected':matches,'activation':activation,'deadline_seconds':2,'message_content_recorded':False}
            self.last_snapshot_metadata={**getattr(self,'last_snapshot_metadata',{}),'focus_diagnostic':diagnostic}
            raise AXError(code)
        frontmost=self.get(self.root,'AXFrontmost')
        if frontmost is not True:
            self._mark_input()
            try:activation=activate_existing(self.pid)
            except ActivationError as error:fail('target-app-activation-unverified:'+str(error))
        current=self.value(self.root,'AXFocusedUIElement')
        if not current or not self.cf.CFEqual(current,expected):
            try:self._restore_main_window_for_focus(node,deadline)
            except AXError as error:fail(str(error))
        self.flag(None,'AXFrontmost');self.flag(node,'AXFocused')
        while True:
            actual=self.value(self.root,'AXFocusedUIElement');frontmost=self.get(self.root,'AXFrontmost');matches=bool(actual and self.cf.CFEqual(actual,expected))
            if frontmost is True and matches:break
            if time.monotonic()>=deadline:fail('composer-focus-or-frontmost-unverified')
            time.sleep(.05)
    @performance.stage('native.key')
    def key(self,keycode,char=0,command=False,shift=False):
        self._mark_input()
        # Public targeted keyboard events, after semantic focus verification.
        # No mouse events or system-wide keyboard target.
        if self.get(self.root,'AXFrontmost') is not True:raise AXError('target-process-not-frontmost-no-key-event')
        flags=((1<<20) if command else 0)|((1<<17) if shift else 0)
        for down in (True,False):
            event=self.cg.CGEventCreateKeyboardEvent(None,keycode,down)
            if not event:raise AXError('keyboard-event-create-failed')
            try:self.cg.CGEventSetFlags(event,flags);self.cg.CGEventPostToPid(self.pid,event)
            finally:self.cf.CFRelease(event)
    @performance.stage('native.close')
    def close(self):
        for v in reversed(self.refs):self.cf.CFRelease(v)
        self.refs=[]
        if self.root:self.cf.CFRelease(self.root);self.root=None

if __name__=='__main__':
    native=None
    try:
        native=Native();print(json.dumps(native.tree(),ensure_ascii=False,indent=2))
    except (AXError,OSError,subprocess.SubprocessError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));sys.exit(2)
    finally:
        if native:native.close()
