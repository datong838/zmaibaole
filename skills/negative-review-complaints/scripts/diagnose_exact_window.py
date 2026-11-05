#!/usr/bin/env python3
"""Fixed issue07 public window metadata only; never input or WebArea contents."""
import sys,json,time,signal,hashlib
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/native_region_capture.py').is_file())
sys.path[:0]=[str(ROOT/'skills/chrome-dom-export/scripts')]
import native_window_capture as nw
from native_region_capture import Geometry
FAILURE=ROOT/'work/2026-10-24/full-three-flow-run-20261024/complaint4-page-window-focus-native-admission-failure.json'
SHA='fbdf5fb1c2b37bd1216c471f265b9f8172265d58dd0aff55097b2cece4c231bc'
def need(ok,code):
 if not ok:raise ValueError(code)
def diagnose(*,ax_factory=Geometry,cg=None):
 raw=FAILURE.read_bytes();need(hashlib.sha256(raw).hexdigest()==SHA,'fixed-failure-changed');f=json.loads(raw);target=f['after']['target'];pid=f['after']['application']['pid'];need(pid==632 and target['tabId']==995698666 and target['windowId']==995698665,'fixed-scope-changed')
 cg=cg or nw.PublicCGWindow();process=nw.process_identity(cg,pid);ax=ax_factory(pid)
 try:
  windows=ax.children(ax.root,'AXWindows');need(len(windows)<=64,'window-budget');rows=[];count=0;deadline=time.monotonic()+12
  for i,w in enumerate(windows):
   title=ax.get(w,'AXTitle');row={'index':i,'role':ax.get(w,'AXRole'),'subrole':ax.get(w,'AXSubrole'),'main':ax.get(w,'AXMain'),'minimized':ax.get(w,'AXMinimized'),'known_title':title if title in ('近期的下载记录',target['title'],target['title']+' - Google Chrome') else None,'title_matches_target':nw.chrome_window_title(title,target['title'])};rows.append(row)
   if not row['title_matches_target']:continue
   try:row['frame']=ax.frame(w)
   except Exception as e:row['frame_error']=str(e)
   document=ax.get(w,'AXDocument');row['document_matches_target']=document==target['url'];row['document_present']=document is not None
   areas=[]
   def walk(e,path,depth):
    nonlocal count
    count+=1;need(count<=2500 and depth<=24 and time.monotonic()<deadline,'structure-budget');role=ax.get(e,'AXRole')
    if role=='AXWebArea':
     url=ax.url(e);areas.append({'path':path,'role':role,'url_present':url is not None,'url_matches_target':url==target['url'],'target_url':url if url==target['url'] else None});return
    for j,c in enumerate(ax.children(e)):walk(c,path+[j],depth+1)
   walk(w,[],0);row['webareas']=areas
  public=[]
  for w in cg.windows():
   if w.get('kCGWindowOwnerPID')==pid and w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True:
    public.append({k:w.get(k) for k in ('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowBounds','kCGWindowLayer','kCGWindowIsOnscreen')}|{'title_matches_target':nw.chrome_window_title(w.get('kCGWindowName'),target['title']),'known_title':w.get('kCGWindowName') if w.get('kCGWindowName') in ('近期的下载记录',target['title'],target['title']+' - Google Chrome') else None})
  return {'kind':'issue07-exact-window-public-metadata-v1','failure':{'path':str(FAILURE),'sha256':SHA},'target':target,'process':process,'AX_windows':rows,'CG_ordinary':public,'visited_outer_nodes':count,'AXValue_read':False,'webarea_contents_read':False,'UI_input_used':False,'capture_used':False,'scope_fresh_DOM_checked':False}
 finally:ax.close()
def main():
 try:print(json.dumps(diagnose(),ensure_ascii=False));return 0
 except Exception as e:print(json.dumps({'kind':'issue07-exact-window-public-metadata-v1','status':'not-verified','error':str(e),'UI_input_used':False,'capture_used':False}));return 2
if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('diagnostic-20-second-timeout')));signal.alarm(20)
 raise SystemExit(main())
