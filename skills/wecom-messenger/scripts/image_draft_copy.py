"""Public selected-composer-image copy proof; no paste, database, or coordinates.
Clipboard contents stay in memory and are restored only while still owned.
"""
import ctypes as C
import hashlib
import time
from pathlib import Path
from urllib.parse import urlparse,unquote
from pasteboard import ObjC,PasteboardError
from image_verify import pixels,ImageProofError

def copy_selected_image(job,copy_action):
    o=ObjC();pool=o.call(o.call(o.cls('NSAutoreleasePool'),'alloc'),'init');pb=o.call(o.cls('NSPasteboard'),'generalPasteboard');saved=[];owned=None
    try:
        start=o.call(pb,'changeCount',result=C.c_long);items=o.call(pb,'pasteboardItems');total=0
        for i in range(o.length(items)):
            item=o.item(items,i);types=o.call(item,'types');formats=[]
            for j in range(o.length(types)):
                typ=o.item(types,j);data=o.call(item,'dataForType:',(C.c_void_p,typ))
                if not data:raise PasteboardError('image-copy-clipboard-cannot-preserve')
                size=o.call(data,'length',result=C.c_ulong);total+=size
                if total>32*1024*1024:raise PasteboardError('image-copy-clipboard-preservation-limit')
                formats.append((o.text(typ),C.string_at(o.call(data,'bytes'),size)))
            saved.append(formats)
        if o.call(pb,'changeCount',result=C.c_long)!=start:raise PasteboardError('image-copy-clipboard-changed-before-copy')
        copy_action()
        for _ in range(20):
            current=o.call(pb,'changeCount',result=C.c_long)
            if current!=start:break
            time.sleep(.1)
        if current==start:raise ImageProofError('image-copy-did-not-change-clipboard')
        owned=current;items=o.call(pb,'pasteboardItems')
        if o.length(items)!=1:raise ImageProofError('image-copy-not-single-selected-item')
        item=o.item(items,0);types=o.call(item,'types');names=[o.text(o.item(types,j)) for j in range(o.length(types))]
        data=None;kind=None
        for typ in ('public.png','public.tiff'):
            if typ in names:
                data=o.call(item,'dataForType:',(C.c_void_p,o.string(typ)));kind=typ;break
        if not data and 'public.file-url' in names:
            value=o.call(item,'stringForType:',(C.c_void_p,o.string('public.file-url')))
            if not value:raise ImageProofError('image-copy-file-url-empty')
            url=urlparse(o.text(value))
            if url.scheme!='file' or url.netloc not in ('','localhost'):raise ImageProofError('image-copy-selected-file-url-not-local')
            selected=Path(unquote(url.path));size=selected.stat().st_size
            if size<=0 or size>32*1024*1024:raise ImageProofError('image-copy-selected-file-limit')
            data=o.call(o.cls('NSData'),'dataWithContentsOfFile:',(C.c_void_p,o.string(str(selected))));kind='public.file-url-selected-image'
        if not data:raise ImageProofError('image-copy-public-image-format-unavailable')
        source=Path(job['file']);source_bytes=source.read_bytes()
        if hashlib.sha256(source_bytes).hexdigest()!=job['file_sha256']:raise ImageProofError('image-copy-source-changed')
        original=o.call(o.cls('NSData'),'dataWithContentsOfFile:',(C.c_void_p,o.string(str(source.resolve()))))
        expected=pixels(o,original,include_bytes=True);actual=pixels(o,data,include_bytes=True)
        if actual!=expected:raise ImageProofError('image-copy-decoded-pixels-not-source')
        if o.call(pb,'changeCount',result=C.c_long)!=owned:raise ImageProofError('image-copy-clipboard-changed-during-proof')
        return {'method':'public-selected-image-copy-exact-decoded-RGBA','source_sha256':job['file_sha256'],'width':actual['width'],'height':actual['height'],'rgba_sha256':actual['rgba_sha256'],'clipboard_before_change_count':start,'clipboard_copy_change_count':owned,'clipboard_format':kind,'clipboard_restore':'only-if-still-owned'}
    finally:
        try:
            if owned is not None and o.call(pb,'changeCount',result=C.c_long)==owned:
                restore=o.call(o.cls('NSMutableArray'),'array')
                for formats in saved:
                    item=o.call(o.call(o.cls('NSPasteboardItem'),'alloc'),'init')
                    try:
                        for typ,raw in formats:
                            buf=C.create_string_buffer(raw);data=o.call(o.cls('NSData'),'dataWithBytes:length:',(C.c_void_p,C.cast(buf,C.c_void_p)),(C.c_ulong,len(raw)))
                            if not o.call(item,'setData:forType:',(C.c_void_p,data),(C.c_void_p,o.string(typ)),result=C.c_bool):raise PasteboardError('image-copy-clipboard-restore-format-failed')
                        o.call(restore,'addObject:',(C.c_void_p,item),result=None)
                    finally:o.call(item,'release',result=None)
                o.call(pb,'clearContents',result=C.c_long)
                if saved and not o.call(pb,'writeObjects:',(C.c_void_p,restore),result=C.c_bool):raise PasteboardError('image-copy-clipboard-restore-failed')
        finally:o.call(pool,'drain',result=None)
