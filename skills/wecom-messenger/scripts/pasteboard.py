"""Temporary file-URL pasteboard via public AppKit API.

Previous formats are kept only in memory and restored unless another application
has changed the pasteboard. No clipboard contents are logged or written to disk.
"""
from contextlib import contextmanager
import ctypes as C
from pathlib import Path
from urllib.parse import urlparse,unquote

class PasteboardError(RuntimeError):pass

class ObjC:
    def __init__(self):
        C.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit',mode=C.RTLD_GLOBAL)
        self.rt=C.CDLL('/usr/lib/libobjc.A.dylib')
        self.rt.objc_getClass.argtypes=[C.c_char_p];self.rt.objc_getClass.restype=C.c_void_p
        self.rt.sel_registerName.argtypes=[C.c_char_p];self.rt.sel_registerName.restype=C.c_void_p
        self.address=C.cast(self.rt.objc_msgSend,C.c_void_p).value
    def cls(self,name):return self.rt.objc_getClass(name.encode())
    def call(self,receiver,selector,*args,result=C.c_void_p):
        types=[t for t,_ in args];values=[v for _,v in args]
        fn=C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*types)(self.address)
        return fn(receiver,self.rt.sel_registerName(selector.encode()),*values)
    def string(self,text):return self.call(self.cls('NSString'),'stringWithUTF8String:',(C.c_char_p,text.encode()))
    def text(self,string):return self.call(string,'UTF8String',result=C.c_char_p).decode()
    def length(self,obj):return self.call(obj,'count',result=C.c_ulong)
    def item(self,obj,index):return self.call(obj,'objectAtIndex:',(C.c_ulong,index))

@contextmanager
def file_url(path):
    o=ObjC();pool=o.call(o.call(o.cls('NSAutoreleasePool'),'alloc'),'init')
    pb=o.call(o.cls('NSPasteboard'),'generalPasteboard');saved=[];written_count=None
    info={'restored':False,'concurrent_change':False}
    try:
        start=o.call(pb,'changeCount',result=C.c_long);items=o.call(pb,'pasteboardItems');total=0
        for i in range(o.length(items)):
            item=o.item(items,i);types=o.call(item,'types');formats=[]
            for j in range(o.length(types)):
                typ=o.item(types,j);data=o.call(item,'dataForType:',(C.c_void_p,typ))
                if not data:raise PasteboardError('clipboard-format-cannot-be-preserved')
                size=o.call(data,'length',result=C.c_ulong);total+=size
                if total>32*1024*1024:raise PasteboardError('clipboard-too-large-to-preserve')
                pointer=o.call(data,'bytes');formats.append((o.text(typ),C.string_at(pointer,size)))
            saved.append(formats)
        if o.call(pb,'changeCount',result=C.c_long)!=start:raise PasteboardError('clipboard-changed-before-stage')
        o.call(pb,'clearContents',result=C.c_long)
        written_count=o.call(pb,'changeCount',result=C.c_long)
        url=o.call(o.cls('NSURL'),'fileURLWithPath:',(C.c_void_p,o.string(path)))
        urls=o.call(o.cls('NSArray'),'arrayWithObject:',(C.c_void_p,url))
        written=o.call(pb,'writeObjects:',(C.c_void_p,urls),result=C.c_bool)
        written_count=o.call(pb,'changeCount',result=C.c_long)
        if not written:raise PasteboardError('file-url-stage-failed')
        def assert_owned():
            if o.call(pb,'changeCount',result=C.c_long)!=written_count:raise PasteboardError('owned-clipboard-changed')
            current_items=o.call(pb,'pasteboardItems')
            if o.length(current_items)!=1:raise PasteboardError('owned-clipboard-item-count')
            types=o.call(o.item(current_items,0),'types');names=[o.text(o.item(types,j)) for j in range(o.length(types))]
            if 'public.file-url' not in names:raise PasteboardError('owned-clipboard-file-url-type-missing')
            own_url=o.call(pb,'stringForType:',(C.c_void_p,o.string('public.file-url')))
            if not own_url:raise PasteboardError('owned-clipboard-file-url-empty')
            parsed=urlparse(o.text(own_url))
            if parsed.scheme!='file' or parsed.netloc not in ('','localhost') or Path(unquote(parsed.path)).resolve()!=Path(path).resolve():
                raise PasteboardError('owned-clipboard-source-mismatch')
            return {'change_count':written_count,'types':sorted(names),'file_url_verified':True}
        info['assert_owned']=assert_owned
        yield info
    finally:
        try:
            if written_count is not None:
                current=o.call(pb,'changeCount',result=C.c_long)
                if current==written_count:
                    restore=o.call(o.cls('NSMutableArray'),'array')
                    for formats in saved:
                        item=o.call(o.call(o.cls('NSPasteboardItem'),'alloc'),'init')
                        try:
                            for typ,raw in formats:
                                buf=C.create_string_buffer(raw)
                                data=o.call(o.cls('NSData'),'dataWithBytes:length:',(C.c_void_p,C.cast(buf,C.c_void_p)),(C.c_ulong,len(raw)))
                                if not o.call(item,'setData:forType:',(C.c_void_p,data),(C.c_void_p,o.string(typ)),result=C.c_bool):raise PasteboardError('clipboard-restore-format-failed')
                            o.call(restore,'addObject:',(C.c_void_p,item),result=None)
                        finally:o.call(item,'release',result=None)
                    o.call(pb,'clearContents',result=C.c_long)
                    if saved and not o.call(pb,'writeObjects:',(C.c_void_p,restore),result=C.c_bool):raise PasteboardError('clipboard-restore-failed')
                    info['restored']=True
                else:info['concurrent_change']=True
        finally:o.call(pool,'drain',result=None)
