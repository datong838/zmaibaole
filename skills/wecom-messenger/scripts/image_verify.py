"""Verify an owned composer image through public AX RTF + AppKit/ImageIO.
No clipboard, screenshot coordinates, client database or modified image output.
"""
import ctypes as C
import hashlib
from pathlib import Path
from pasteboard import ObjC

class ImageProofError(RuntimeError):pass
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double)]
class Size(C.Structure):_fields_=[('width',C.c_double),('height',C.c_double)]
class Rect(C.Structure):_fields_=[('origin',Point),('size',Size)]

def pixels(o,data,*,include_bytes=False):
    imageio=C.CDLL('/System/Library/Frameworks/ImageIO.framework/ImageIO')
    cg=C.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
    def fn(lib,name,restype,*args):
        f=getattr(lib,name);f.restype=restype;f.argtypes=list(args);return f
    p=C.c_void_p;z=C.c_size_t
    fn(imageio,'CGImageSourceCreateWithData',p,p,p);fn(imageio,'CGImageSourceCreateImageAtIndex',p,p,z,p)
    fn(cg,'CGImageGetWidth',z,p);fn(cg,'CGImageGetHeight',z,p);fn(cg,'CGColorSpaceCreateDeviceRGB',p)
    fn(cg,'CGBitmapContextCreate',p,p,z,z,z,z,p,C.c_uint32);fn(cg,'CGContextDrawImage',None,p,Rect,p)
    fn(cg,'CGImageRelease',None,p);fn(cg,'CGContextRelease',None,p);fn(cg,'CGColorSpaceRelease',None,p)
    fn(cf,'CFRelease',None,p)
    source=imageio.CGImageSourceCreateWithData(data,None)
    if not source:raise ImageProofError('image-data-not-decodable')
    image=context=space=None
    try:
        image=imageio.CGImageSourceCreateImageAtIndex(source,0,None)
        if not image:raise ImageProofError('image-source-empty')
        w,h=cg.CGImageGetWidth(image),cg.CGImageGetHeight(image)
        if not w or not h or w*h>30_000_000:raise ImageProofError('image-dimensions-outside-verification-limit')
        storage=C.create_string_buffer(w*h*4);space=cg.CGColorSpaceCreateDeviceRGB()
        context=cg.CGBitmapContextCreate(storage,w,h,8,w*4,space,1|(4<<12))
        if not context:raise ImageProofError('image-context-unavailable')
        cg.CGContextDrawImage(context,Rect(Point(0,0),Size(w,h)),image)
        return {'width':w,'height':h,'rgba_sha256':hashlib.sha256(storage.raw).hexdigest(),**({'rgba_bytes':storage.raw} if include_bytes else {})}
    finally:
        if context:cg.CGContextRelease(context)
        if space:cg.CGColorSpaceRelease(space)
        if image:cg.CGImageRelease(image)
        cf.CFRelease(source)

def verify_rtf(rtf,job):
    source=Path(job['file']).read_bytes()
    if hashlib.sha256(source).hexdigest()!=job['file_sha256']:raise ImageProofError('image-source-file-changed')
    o=ObjC();pool=o.call(o.call(o.cls('NSAutoreleasePool'),'alloc'),'init')
    attributed=None
    try:
        buf=C.create_string_buffer(rtf)
        data=o.call(o.cls('NSData'),'dataWithBytes:length:',(C.c_void_p,C.cast(buf,C.c_void_p)),(C.c_ulong,len(rtf)))
        attributed=o.call(o.call(o.cls('NSAttributedString'),'alloc'),'initWithRTF:documentAttributes:',(C.c_void_p,data),(C.c_void_p,None))
        if not attributed or o.call(attributed,'length',result=C.c_ulong)!=1:raise ImageProofError('draft-rtf-not-single-attachment')
        attachment=o.call(attributed,'attribute:atIndex:effectiveRange:',(C.c_void_p,o.string('NSAttachment')),(C.c_ulong,0),(C.c_void_p,None))
        if not attachment:raise ImageProofError('draft-rtf-no-image-attachment')
        wrapper=o.call(attachment,'fileWrapper');image_data=None
        if wrapper and o.call(wrapper,'isRegularFile',result=C.c_bool):image_data=o.call(wrapper,'regularFileContents')
        if not image_data:
            image=o.call(attachment,'image')
            if image:image_data=o.call(image,'TIFFRepresentation')
        if not image_data:raise ImageProofError('draft-image-data-unavailable')
        original=o.call(o.cls('NSData'),'dataWithContentsOfFile:',(C.c_void_p,o.string(str(Path(job['file']).resolve()))))
        expected=pixels(o,original);actual=pixels(o,image_data)
        if actual!=expected:raise ImageProofError('draft-image-pixels-do-not-match-source')
        return {**expected,'source_sha256':job['file_sha256'],'rtf_sha256':hashlib.sha256(rtf).hexdigest(),'method':'public-AXRTFForRange-exact-decoded-pixels'}
    finally:
        if attributed:o.call(attributed,'release',result=None)
        o.call(pool,'drain',result=None)

def verify_attributed(attributed,job):
    """AX returns a public CFAttributedString, toll-free with NSAttributedString."""
    source=Path(job['file']).read_bytes()
    if hashlib.sha256(source).hexdigest()!=job['file_sha256']:raise ImageProofError('image-source-file-changed')
    o=ObjC();pool=o.call(o.call(o.cls('NSAutoreleasePool'),'alloc'),'init')
    try:
        if not attributed or o.call(attributed,'length',result=C.c_ulong)!=1:raise ImageProofError('draft-attributed-not-single-attachment')
        text=o.text(o.call(attributed,'string'))
        if text!='\ufffc':raise ImageProofError('draft-attributed-not-image-character')
        attachment=o.call(attributed,'attribute:atIndex:effectiveRange:',(C.c_void_p,o.string('NSAttachment')),(C.c_ulong,0),(C.c_void_p,None))
        if not attachment:raise ImageProofError('draft-attributed-no-NSAttachment')
        wrapper=o.call(attachment,'fileWrapper');data=None
        if wrapper and o.call(wrapper,'isRegularFile',result=C.c_bool):data=o.call(wrapper,'regularFileContents')
        if not data:
            image=o.call(attachment,'image')
            if image:data=o.call(image,'TIFFRepresentation')
        if not data:raise ImageProofError('draft-attributed-image-data-unavailable')
        original=o.call(o.cls('NSData'),'dataWithContentsOfFile:',(C.c_void_p,o.string(str(Path(job['file']).resolve()))))
        expected=pixels(o,original);actual=pixels(o,data)
        if actual!=expected:raise ImageProofError('draft-image-pixels-do-not-match-source')
        return {**expected,'source_sha256':job['file_sha256'],'method':'public-AXAttributedStringForRange-exact-decoded-pixels'}
    finally:o.call(pool,'drain',result=None)
