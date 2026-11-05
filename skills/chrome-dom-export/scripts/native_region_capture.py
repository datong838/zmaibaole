#!/usr/bin/env python3
"""Crop-only geometry and original-pixel derivation, never input coordinates.
Shared by normal-review and violation adapters; no navigation/scroll or activation.
"""
import ctypes as C,hashlib,json,math,os,sys,time
from pathlib import Path
import native_window_capture as nw
from visible_capture import require,atomic,sha,stamp,validate_png
from ax_capture_grant import NativeAction
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double)]
class Size(C.Structure):_fields_=[('width',C.c_double),('height',C.c_double)]
class Geometry(NativeAction):
    def __init__(self,pid):
        super().__init__(pid)
        self.ax.AXValueGetType.restype=C.c_int;self.ax.AXValueGetType.argtypes=[C.c_void_p]
        self.ax.AXValueGetValue.restype=C.c_bool;self.ax.AXValueGetValue.argtypes=[C.c_void_p,C.c_int,C.c_void_p]
        self.cf.CFURLGetTypeID.restype=C.c_ulong;self.cf.CFURLGetTypeID.argtypes=[]
        self.cf.CFURLGetString.restype=C.c_void_p;self.cf.CFURLGetString.argtypes=[C.c_void_p]
    def pair(self,e,key,typ):
        value=self.raw(e,key);require(value and self.ax.AXValueGetType(value)==typ,'region-public-AX-geometry-unavailable:'+key)
        result=Point() if typ==1 else Size();require(self.ax.AXValueGetValue(value,typ,C.byref(result)),'region-public-AX-geometry-invalid:'+key)
        return {'x':result.x,'y':result.y} if typ==1 else {'width':result.width,'height':result.height}
    def frame(self,e):return {**self.pair(e,'AXPosition',1),**self.pair(e,'AXSize',2)}
    def url(self,e):
        raw=self.raw(e,'AXURL')
        if raw and self.cf.CFGetTypeID(raw)==self.cf.CFURLGetTypeID():return self.decode(self.cf.CFURLGetString(raw))
        return self.decode(raw)
    def observe(self,scope):
        # Chromium publishes web accessibility on demand after the public
        # application-role read. Never set undocumented activation attributes.
        require(self.get(self.root,'AXFrontmost') is True,'region-Chrome-not-frontmost')
        require(self.get(self.root,'AXRole')=='AXApplication','region-AX-application-role-unavailable')
        deadline=time.monotonic()+20;count=0
        for attempt in range(3):
            require(time.monotonic()<deadline,'region-AX-outer-tree-incomplete')
            require(self.get(self.root,'AXFrontmost') is True,'region-Chrome-not-frontmost')
            windows=[w for w in self.children(self.root,'AXWindows') if self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True]
            require(len(windows)==1,'region-main-window-not-unique');window=windows[0]
            require(nw.chrome_window_title(self.get(window,'AXTitle'),scope['title']),'region-AX-title-mismatch')
            areas=[];seen_areas=0
            def walk(e,depth):
                nonlocal count,seen_areas
                count+=1;require(count<=2500 and depth<=24 and time.monotonic()<deadline,'region-AX-outer-tree-incomplete');role=self.get(e,'AXRole')
                require(isinstance(role,str) and role,'region-AX-outer-role-unavailable')
                if role=='AXWebArea':
                    seen_areas+=1
                    if self.url(e)==scope['url']:areas.append(e)
                    return  # Never inspect page children or content.
                for child in self.children(e):walk(child,depth+1)
            walk(window,0)
            require(len(areas)<=1 and (areas or seen_areas==0),'region-WebArea-URL-not-unique')
            if areas:
                geometry={'pid':self.pid,'url':scope['url'],'AX_main_window':self.frame(window),'AX_webarea':self.frame(areas[0]),'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}
                require(time.monotonic()<deadline,'region-AX-outer-tree-incomplete')
                return geometry
            if attempt<2:
                require(time.monotonic()<deadline,'region-AX-outer-tree-incomplete');time.sleep(min(.25,max(0,deadline-time.monotonic())))
        require(False,'region-WebArea-URL-not-unique')

def observe(command,request,native=None,ax=None,*,diagnostic=None):
    native=native or nw.PublicCGWindow();pre=nw.preflight(command,request,native,diagnostic=diagnostic);items=native.windows();nw.window_scope(items,command['pid'],pre['scope']['title'],pre['window'])
    selected=[w for w in items if w.get('kCGWindowNumber')==pre['window']['kCGWindowNumber']];require(len(selected)==1 and isinstance(selected[0].get('kCGWindowBounds'),dict),'region-CG-window-bounds-required')
    bounds=selected[0]['kCGWindowBounds'];cg={'x':bounds['X'],'y':bounds['Y'],'width':bounds['Width'],'height':bounds['Height']}
    own=ax is None;ax=ax or Geometry(command['pid'])
    try:geometry=ax.observe(pre['scope'])
    finally:
        if own:ax.close()
    require(geometry.get('pid')==command['pid'] and geometry.get('url')==command['url'] and geometry.get('webarea_contents_read') is False,'region-AX-scope-mismatch')
    require(all(abs(geometry['AX_main_window'][k]-cg[k])<=.001 for k in cg),'region-AX-CG-main-frame-mismatch')
    return {'scope':pre['scope'],'window':pre['window'],'CG_bounds':cg,'AX':geometry}

def crop_box(proof,geometry,width,height):
    require(proof.get('method')=='public-DOM-evidence-region-proof' and proof.get('geometry_purpose')=='evidence-crop-only' and proof.get('pixel_input_actions') is False and (proof.get('external_painted_overlap') is False or (proof.get('external_painted_overlap')=='unresolved' and proof.get('quality_review_required') is True and (bool(proof.get('unresolved_overlay')) or proof.get('region_build') in ('region-notice-business-cells-v11-manual-neighbor-preview-v2','region-notice-business-cells-v12-manual-date-fragment-v2') and proof.get('evidence_contract')=='notice-five-business-cells-v1' and proof.get('manual_preview_unresolved') is True and bool(proof.get('unresolved_source_neighbor_overlap'))))),'region-proof-purpose-or-overlap-invalid')
    require(proof['scope']=={k:geometry['scope'][k] for k in ('tabId','windowId','groupid')} and proof['url']==geometry['scope']['url'],'region-geometry-proof-scope-mismatch')
    r=proof['region'];v=proof['viewport'];cg=geometry['CG_bounds'];area=geometry['AX']['AX_webarea']
    require(all(type(x) in (int,float) and math.isfinite(x) for x in [*r.values(),*v.values(),*cg.values(),*area.values()]),'region-nonfinite-geometry')
    require(v['visual_scale']==1 and v['width']>0 and v['height']>0 and cg['width']>0 and cg['height']>0 and area['width']>0 and area['height']>0,'region-invalid-viewport-frame')
    require(0<=r['left']<r['right']<=v['width'] and 0<=r['top']<r['bottom']<=v['height'] and abs(r['width']-(r['right']-r['left']))<.001 and abs(r['height']-(r['bottom']-r['top']))<.001,'region-rectangle-outside-viewport')
    require(area['x']>=cg['x'] and area['y']>=cg['y'] and area['x']+area['width']<=cg['x']+cg['width']+.001 and area['y']+area['height']<=cg['y']+cg['height']+.001,'region-WebArea-outside-main-window')
    # Public AX is in screen points; DOM is in CSS pixels. Derive the ratio from
    # both complete viewport dimensions, never a hardcoded toolbar offset/DPR.
    sx=area['width']/v['width'];sy=area['height']/v['height'];require(abs(sx-sy)<=max(sx,sy)*.002,'region-AX-DOM-viewport-scale-mismatch')
    px=width/cg['width'];py=height/cg['height'];require(abs(px-py)<=max(px,py)*.002,'region-raw-window-pixel-scale-mismatch')
    left=(area['x']-cg['x']+r['left']*sx)*px;top=(area['y']-cg['y']+r['top']*sy)*py
    right=(area['x']-cg['x']+r['right']*sx)*px;bottom=(area['y']-cg['y']+r['bottom']*sy)*py
    box=[math.floor(left),math.floor(top),math.ceil(right),math.ceil(bottom)];require(0<=box[0]<box[2]<=width and 0<=box[1]<box[3]<=height,'region-crop-outside-original-png')
    return box

def pillow():
    try:from PIL import Image;return Image
    except ImportError:raise ValueError('Pillow-required-use-bundled-workspace-python-or-daily-venv-with-Pillow')

def derive(raw,proof,geometry,out):
    raw=Path(raw).resolve();out=Path(out).resolve();require(not out.exists() and raw!=out and out.suffix.lower()=='.png','region-new-derived-output-required');out.parent.mkdir(parents=True,exist_ok=True)
    width,height=validate_png(raw.read_bytes());box=crop_box(proof,geometry,width,height);Image=pillow()
    with Image.open(raw) as source:
        source.load();cropped=source.crop(tuple(box));pixels=hashlib.sha256(cropped.convert('RGBA').tobytes()).hexdigest();cropped.save(out,format='PNG')
    validate_png(out.read_bytes())
    return {'source':{'path':str(raw),'sha256':sha(raw),'width':width,'height':height},'image':{'path':str(out),'sha256':sha(out),'width':box[2]-box[0],'height':box[3]-box[1]},'crop_box_pixels':box,'derived_rgba_sha256':pixels,'operation':'unchanged-source-pixel-crop','whole_window':False,'viewport_only':False,'region_only':True,'geometry_purpose':'evidence-crop-only','pixel_input_actions':False}

def validate(value,proof,geometry):
    require(value.get('operation')=='unchanged-source-pixel-crop' and value.get('whole_window') is False and value.get('region_only') is True and value.get('geometry_purpose')=='evidence-crop-only' and value.get('pixel_input_actions') is False,'region-derived-method-invalid')
    raw=value['source'];image=value['image'];require(sha(raw['path'])==raw['sha256'] and sha(image['path'])==image['sha256'],'region-source-or-derived-png-changed')
    width,height=validate_png(Path(raw['path']).read_bytes());require((width,height)==(raw['width'],raw['height']),'region-source-size-changed');box=crop_box(proof,geometry,width,height);require(box==value['crop_box_pixels'],'region-crop-mapping-changed')
    w,h=validate_png(Path(image['path']).read_bytes());require((w,h)==(image['width'],image['height'])==(box[2]-box[0],box[3]-box[1]),'region-derived-size-changed');Image=pillow()
    with Image.open(raw['path']) as source,Image.open(image['path']) as crop:
        expected=source.crop(tuple(box)).convert('RGBA').tobytes();actual=crop.convert('RGBA').tobytes();require(expected==actual and hashlib.sha256(actual).hexdigest()==value['derived_rgba_sha256'],'region-pixels-not-original-source-crop')
    return image
