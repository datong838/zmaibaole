#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One explicit normal Chrome 显示→缩小 AXPress, then await public DOM proof.
No shortcuts, coordinates, Chrome settings-page access, reload or account/business
data changes; only one normal display zoom action. No activation/WebArea contents.
"""
import argparse,ctypes as C,fcntl,hashlib,json,os,re,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'chrome-dom-export/scripts'))
from native_region_capture import Geometry

def need(value,reason):
    if not value:raise ValueError(reason)
def stamp():return datetime.now(timezone.utc).isoformat()
def document(ref):
    data=Path(ref['path']).read_bytes();need(hashlib.sha256(data).hexdigest()==ref['sha256'],'zoom-pinned-file-changed');return json.loads(data)
def atomic(path,value):
    fd,tmp=tempfile.mkstemp(prefix='.normal-zoom-',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def scope_inputs(pid,observation,menu):
    raw=document(observation);proof=document(menu);tab=raw.get('tab',{});u=urlsplit(tab.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
    need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==tab.get('tabId') and type(tab.get('windowId')) is int and tab.get('active') is True and tab.get('allowed') is True and u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and len(q.get('groupid',[]))==1 and q['groupid'][0]==tab.get('groupid'),'zoom-original-public-records-tab-required')
    need(proof.get('purpose')=='readonly-Chrome-native-zoom-menu-discovery' and proof.get('pid')==pid and proof.get('AXFrontmost') is True and proof.get('webarea_URL_verified') is True and proof.get('webarea_contents_read') is False and proof.get('input_actions_used') is False,'zoom-observed-normal-menu-proof-required')
    view=proof.get('view_menu',{});need(view.get('role')=='AXMenuBarItem' and view.get('AXTitle')=='显示' and view.get('AXEnabled') is True,'zoom-reviewed-view-menu-required')
    menus=[m for m in view.get('children',[]) if m.get('role')=='AXMenu'];need(len(menus)==1,'zoom-reviewed-menu-not-unique');items=[n for n in menus[0].get('children',[]) if n.get('role')=='AXMenuItem' and n.get('AXTitle')=='缩小'];need(len(items)==1 and items[0].get('AXEnabled') is True and 'AXPress' in items[0].get('actions',[]),'zoom-reviewed-shrink-not-enabled')
    return {'pid':pid,'tab_id':raw['tab_id'],'window_id':tab['windowId'],'url':tab['url'],'title':tab['title'],'groupid':tab['groupid']},proof['main_window_geometry']
class NativeZoom(Geometry):
    def actions(self,e):
        value=C.c_void_p();err=self.ax.AXUIElementCopyActionNames(e,C.byref(value));need(err==0 and value.value,'zoom-public-action-names-unavailable');self.refs.append(value.value)
        return [self.decode(self.cf.CFArrayGetValueAtIndex(value.value,i)) for i in range(self.cf.CFArrayGetCount(value.value))]
    def inspect(self,scope):
        geometry=self.observe(scope);windows=[w for w in self.children(self.root,'AXWindows') if self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True];need(len(windows)==1,'zoom-current-main-window-not-unique')
        if hasattr(self,'bound_window'):need(self.cf.CFEqual(self.bound_window,windows[0]),'zoom-main-window-handle-changed')
        else:self.bound_window=windows[0]
        bars=self.raw(self.root,'AXMenuBar');need(bars and self.get(bars,'AXRole')=='AXMenuBar','zoom-current-menubar-unavailable')
        views=[x for x in self.children(bars) if self.get(x,'AXRole')=='AXMenuBarItem' and self.get(x,'AXTitle')=='显示'];need(len(views)==1 and self.get(views[0],'AXEnabled') is True,'zoom-current-view-menu-not-unique')
        menus=[x for x in self.children(views[0]) if self.get(x,'AXRole')=='AXMenu'];need(len(menus)==1,'zoom-current-view-submenu-not-unique')
        items=[x for x in self.children(menus[0]) if self.get(x,'AXRole')=='AXMenuItem' and self.get(x,'AXTitle')=='缩小'];need(len(items)==1 and self.get(items[0],'AXEnabled') is True and 'AXPress' in self.actions(items[0]),'zoom-current-shrink-not-unique-enabled')
        self.target=(views[0],menus[0],items[0]);return geometry
    def press_once(self,scope):
        previous=self.target;self.inspect(scope);need(all(self.cf.CFEqual(a,b) for a,b in zip(previous,self.target)),'zoom-menu-handle-changed-before-action')
        view,menu,item=self.target
        for child,parent in ((menu,view),(item,menu)):
            actual=self.raw(child,'AXParent');need(actual and self.cf.CFEqual(actual,parent),'zoom-menu-ancestry-changed')
        action=self.string('AXPress')
        try:err=self.ax.AXUIElementPerformAction(item,action)
        finally:self.cf.CFRelease(action)
        need(err==0,'zoom-AXPress-outcome-unknown');return {'AXPress_return_code':err,'target':'显示→缩小'}
def run(pid,observation,menu,out,key,native_factory=NativeZoom):
    need(type(pid) is int and pid>0 and isinstance(key,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',key),'zoom-explicit-pid-key-required');out=Path(out).resolve();scope,expected=scope_inputs(pid,observation,menu);binding={'schema':'chrome-normal-zoom-out-v1','scope':scope,'observation':observation,'menu_proof':menu,'key':key};out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_suffix(out.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():
            old=json.loads(out.read_text());need(old.get('binding')==binding,'zoom-original-intent-binding-required');return {'state':old['state'],'intent':str(out),'replayed':False,'effect_verified':False,'new_input':False}
        native=native_factory(pid)
        try:
            geometry=native.inspect(scope);need(geometry.get('pid')==pid and geometry.get('url')==scope['url'] and geometry.get('webarea_contents_read') is False and geometry.get('AX_main_window')==expected,'zoom-current-main-WebArea-scope-changed')
            value={'binding':binding,'state':'unknown','intent_at':stamp(),'geometry_before':geometry,'action':'AXMenuBarItem显示/AXMenu/AXMenuItem缩小:AXPress','effect_verified':False};atomic(out,value)
            try:result=native.press_once(scope)
            except Exception as e:value.update(error=str(e),outcome_at=stamp());atomic(out,value);raise
            value.update(state='action-returned-awaiting-public-proof',result=result,returned_at=stamp());atomic(out,value);return {'state':value['state'],'intent':str(out),'replayed':False,'effect_verified':False,'new_input':True}
        finally:native.close()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True)
    for name in ('observation','menu-proof'):
        p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
    p.add_argument('--out',required=True);p.add_argument('--key',required=True);a=p.parse_args();ref=lambda n:{'path':str(Path(getattr(a,n)).resolve()),'sha256':getattr(a,n+'_sha256')}
    try:print(json.dumps(run(a.pid,ref('observation'),ref('menu_proof'),a.out,a.key),ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'effect_verified':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
