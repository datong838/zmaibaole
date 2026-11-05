#!/usr/bin/env python3
"""Read-only public Chrome 显示→缩小 menu proof for chrome-normal-zoom-out.
No activation, action, event, bridge, screenshot or WebArea contents/children.
Main-window geometry is evidence binding, never input coordinates.
"""
import argparse,ctypes as C,hashlib,json,math,os,re,sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'chrome-dom-export/scripts'))
from native_region_capture import Geometry
from native_window_capture import chrome_window_title

def need(ok,code):
 if not ok:raise ValueError(code)
def canonical(value):
 p=Path(value);need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'zoom-menu-canonical-path-required');return p
def document(reference):
 need(isinstance(reference,dict) and set(reference)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(reference['sha256'])),'zoom-menu-pinned-reference-required');raw=canonical(reference['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'zoom-menu-observation-changed');return json.loads(raw)
def scope_inputs(pid,observation):
 need(type(pid) is int and pid>0,'zoom-menu-explicit-pid-required');raw=document(observation);tab=raw.get('tab',{});u=urlsplit(tab.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
 need(raw.get('source')=='local-dom-bridge' and type(tab.get('tabId')) is int and tab['tabId']>0 and raw.get('tab_id')==tab['tabId'] and type(tab.get('windowId')) is int and tab['windowId']>0 and tab.get('active') is True and tab.get('allowed') is True and isinstance(tab.get('title'),str) and bool(tab['title']) and u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and not u.fragment and len(q.get('groupid',[]))==1 and q['groupid'][0]==tab.get('groupid') and re.fullmatch('[0-9]+',str(tab['groupid'])),'zoom-menu-original-public-records-scope-required')
 return raw,tab
class NativeMenuRead(Geometry):
 def observe(self,scope):
  need(self.get(self.root,'AXFrontmost') is True,'zoom-menu-Chrome-not-frontmost');windows=[w for w in self.children(self.root,'AXWindows') if self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True];need(len(windows)==1,'zoom-menu-main-window-not-unique');window=windows[0];need(chrome_window_title(self.get(window,'AXTitle'),scope['title']),'zoom-menu-main-window-title-mismatch');areas=[];count=0
  def walk(e,depth):
   nonlocal count
   count+=1;need(count<=2500 and depth<=24,'zoom-menu-outer-tree-bound-exceeded');role=self.get(e,'AXRole')
   if role=='AXWebArea':
    if self.url(e)==scope['url']:areas.append(e)
    return # URL only: no WebArea attributes/content/children or frame reads.
   for child in self.children(e):walk(child,depth+1)
  walk(window,0);need(len(areas)==1,'zoom-menu-WebArea-URL-not-unique');return {'pid':self.pid,'url':scope['url'],'AX_main_window':self.frame(window),'webarea_contents_read':False,'webarea_children_read':False,'webarea_geometry_read':False}
 def actions(self,e):
  value=C.c_void_p();err=self.ax.AXUIElementCopyActionNames(e,C.byref(value));need(err==0 and value.value and self.cf.CFGetTypeID(value.value)==self.cf.CFArrayGetTypeID(),'zoom-menu-action-names-unavailable');self.refs.append(value.value);size=self.cf.CFArrayGetCount(value.value);need(0<=size<=32,'zoom-menu-actions-bound-exceeded');return [self.decode(self.cf.CFArrayGetValueAtIndex(value.value,i)) for i in range(size)]
 def menu(self):return self.raw(self.root,'AXMenuBar')
 def menu_children(self,e):
  value=self.raw(e,'AXChildren')
  if not value:need(self.get(e,'AXRole')=='AXMenuItem','zoom-menu-required-children-unavailable');return []
  need(self.cf.CFGetTypeID(value)==self.cf.CFArrayGetTypeID(),'zoom-menu-children-not-array');size=self.cf.CFArrayGetCount(value);need(0<=size<=300,'zoom-menu-children-bound-exceeded');return [self.cf.CFArrayGetValueAtIndex(value,i) for i in range(size)]
def collect(native,pid,scope):
 frame=native.observe(scope);need(frame.get('pid')==pid and frame.get('url')==scope['url'] and frame.get('webarea_contents_read') is False,'zoom-menu-native-scope-changed');geometry=frame.get('AX_main_window');need(isinstance(geometry,dict) and set(geometry)=={'x','y','width','height'} and all(type(v) in (int,float) and math.isfinite(v) for v in geometry.values()) and geometry['width']>0 and geometry['height']>0,'zoom-menu-main-geometry-invalid');bar=native.menu();need(bar and native.get(bar,'AXRole')=='AXMenuBar','zoom-menu-menubar-unavailable');top=native.menu_children(bar);need(len(top)<=32,'zoom-menu-top-bound-exceeded');titles=[];views=[]
 for e in top:
  role=native.get(e,'AXRole');need(role=='AXMenuBarItem','zoom-menu-top-role-invalid');title=native.get(e,'AXTitle');need(isinstance(title,str) and len(title)<=256,'zoom-menu-title-invalid');enabled=native.get(e,'AXEnabled');titles.append({'role':role,'title':title,'enabled':enabled})
  if title=='显示':views.append(e)
 need(len(views)==1,'zoom-menu-view-not-unique');count=0
 def walk(e,depth=0):
  nonlocal count
  count+=1;need(count<=300 and depth<=8,'zoom-menu-tree-bound-exceeded');role=native.get(e,'AXRole');need(role in ('AXMenuBarItem','AXMenu','AXMenuItem'),'zoom-menu-unexpected-role');out={'role':role}
  for key in ('AXTitle','AXEnabled','AXMenuItemCmdChar','AXMenuItemCmdModifiers','AXMenuItemMarkChar'):
   v=native.get(e,key);need(v is None or type(v) in (str,int,bool),'zoom-menu-attribute-type-invalid');need(not isinstance(v,str) or len(v)<=256,'zoom-menu-attribute-bound-exceeded')
   if v is not None:out[key]=v
  out['actions']=native.actions(e);need(isinstance(out['actions'],list) and len(out['actions'])<=32 and all(type(v) is str and len(v)<=128 for v in out['actions']),'zoom-menu-actions-invalid');out['children']=[walk(c,depth+1) for c in native.menu_children(e)];return out
 view=walk(views[0]);need(view.get('AXEnabled') is True,'zoom-menu-view-disabled');menus=[n for n in view['children'] if n['role']=='AXMenu'];need(len(menus)==1,'zoom-menu-view-submenu-not-unique');items=[n for n in menus[0]['children'] if n['role']=='AXMenuItem' and n.get('AXTitle')=='缩小'];need(len(items)==1 and items[0].get('AXEnabled') is True and 'AXPress' in items[0]['actions'],'zoom-menu-shrink-not-unique-enabled');need(native.get(native.root,'AXFrontmost') is True,'zoom-menu-frontmost-changed')
 return {'purpose':'readonly-Chrome-native-zoom-menu-discovery','observed_at':datetime.now(timezone.utc).isoformat(),'pid':pid,'AXFrontmost':True,'main_window_geometry':geometry,'webarea_URL_verified':True,'webarea_contents_read':False,'webarea_children_read':False,'webarea_geometry_read':False,'top_menus':titles,'view_menu':view,'node_count':count,'truncated':False,'bridge_used':False,'input_actions_used':False,'screenshot_used':False}
def run(pid,observation,out,native_factory=NativeMenuRead):
 raw,scope=scope_inputs(pid,observation);out=canonical(out);need(not out.exists(),'zoom-menu-new-output-required');native=native_factory(pid)
 try:proof=collect(native,pid,scope)
 finally:native.close()
 need(document(observation)==raw,'zoom-menu-observation-changed');proof['binding']={'schema':'chrome-normal-zoom-menu-proof-v1','pid':pid,'observation':observation,'tab_id':scope['tabId'],'window_id':scope['windowId'],'groupid':scope['groupid'],'url':scope['url'],'title':scope['title']};out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x',encoding='utf-8') as f:json.dump(proof,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
 return {'path':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'purpose':proof['purpose'],'node_count':proof['node_count'],'ui_used':False,'input_actions_used':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pid',type=int,required=True);p.add_argument('--observation',required=True);p.add_argument('--observation-sha256',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 try:print(json.dumps(run(a.pid,{'path':str(Path(a.observation).resolve()),'sha256':a.observation_sha256},str(Path(a.out).resolve())),ensure_ascii=False));return 0
 except (ValueError,OSError,KeyError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e),'ui_used':False,'input_actions_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
