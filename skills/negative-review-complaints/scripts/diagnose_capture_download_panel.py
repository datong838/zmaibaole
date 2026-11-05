#!/usr/bin/env python3
"""Fixed failed-capture Chrome panel metadata. Read-only; no values or webpage."""
import ctypes as C
import hashlib,json,sys,time,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/wecom-messenger/scripts')]
import native_window_capture as nw
from ax_capture_grant import NativeAction
FAILURE='work/2026-10-24/full-three-flow-run-20261024/complaint2-native-download-panel-preflight-failure.json'
FAILURE_SHA='a3fb5019fa95e3cac808cf6d0c42b0a1b7d2785e501c3f768aa50d35dffe1f27'
TITLE='近期的下载记录';PID=632;WINDOW=613
CLOSE_LABELS={'关闭','关闭下载记录','关闭近期的下载记录'}
ACTIONS={'AXPress','AXCancel','AXRaise'}
def need(ok,code):
 if not ok:raise ValueError(code)
def evidence():
 p=ROOT/FAILURE;need(not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==FAILURE_SHA,'panel-diagnostic-original-failure-changed');f=json.loads(p.read_bytes())
 need(f['actual_frontmost']['kCGWindowNumber']==WINDOW and f['actual_frontmost']['kCGWindowOwnerPID']==PID and f['actual_frontmost']['kCGWindowName']==TITLE and f['capture_attempted'] is False,'panel-diagnostic-original-scope')
 return f
def cg_panel(cg):
 normal=[w for w in cg.windows() if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True];need(normal,'panel-diagnostic-no-normal-window');w=normal[0]
 need(all(w.get(k)==v for k,v in {'kCGWindowNumber':WINDOW,'kCGWindowOwnerPID':PID,'kCGWindowOwnerName':'Google Chrome','kCGWindowName':TITLE}.items()),'panel-diagnostic-exact-front-panel-not-observed')
 return {k:w.get(k) for k in ('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowName','kCGWindowLayer','kCGWindowIsOnscreen')}
def actions(ax,node):
 if hasattr(ax,'action_names'):return ax.action_names(node)
 out=C.c_void_p();error=ax.ax.AXUIElementCopyActionNames(node,C.byref(out))
 try:
  if error:return {'AX_error':int(error),'known':[],'other_count':0}
  need(out.value and ax.cf.CFGetTypeID(out.value)==ax.cf.CFArrayGetTypeID(),'panel-diagnostic-action-array-invalid');count=ax.cf.CFArrayGetCount(out.value);need(0<=count<=32,'panel-diagnostic-action-budget')
  names=[ax.decode(ax.cf.CFArrayGetValueAtIndex(out.value,i)) for i in range(count)]
  return {'AX_error':0,'known':[x for x in names if x in ACTIONS],'other_count':sum(x not in ACTIONS for x in names)}
 finally:
  if out.value:ax.cf.CFRelease(out.value)
def diagnose(*,cg=None,ax_factory=None):
 f=evidence();cg=cg or nw.PublicCGWindow();identity=nw.process_identity(cg,PID);before=cg_panel(cg);ax=(ax_factory or NativeAction)(PID)
 try:
  need(ax.pid==PID,'panel-diagnostic-process-mismatch');windows=ax.children(ax.root,'AXWindows');need(len(windows)<=64,'panel-diagnostic-window-budget');matches=[w for w in windows if ax.get(w,'AXTitle')==TITLE]
  need(len(matches)==1,'panel-diagnostic-AX-panel-not-unique');root=matches[0];need(ax.get(root,'AXRole')=='AXWindow','panel-diagnostic-AX-panel-role')
  nodes=[];deadline=time.monotonic()+8
  def walk(node,path,depth):
   need(len(nodes)<250 and depth<=12 and time.monotonic()<deadline,'panel-diagnostic-structure-budget');role=ax.get(node,'AXRole');sub=ax.get(node,'AXSubrole');label=ax.get(node,'AXTitle');description=ax.get(node,'AXDescription');a=actions(ax,node)
   row={'path':path,'role':role,'subrole':sub,'known_title':label if label in CLOSE_LABELS or not path and label==TITLE else None,'known_description':description if description in CLOSE_LABELS else None,'actions':a};nodes.append(row)
   if role=='AXWebArea':row['web_content_omitted']=True;return
   for i,child in enumerate(ax.children(node)):walk(child,path+[i],depth+1)
  walk(root,[],0);after=cg_panel(cg);need(after==before,'panel-diagnostic-front-panel-changed')
  return {'kind':'same-host-capture-download-panel-structure-v1','status':'observed','failure':{'path':str(ROOT/FAILURE),'sha256':FAILURE_SHA},'original_scope':f['expected_scope'],'scope_fresh_DOM_checked':False,'process':identity,'CG_before':before,'CG_after':after,'AX_window_count':len(windows),'matching_panel_count':1,'nodes':nodes,'AXValue_read':False,'message_or_page_content_recorded':False,'UI_input_used':False,'capture_used':False}
 finally:ax.close()
def main():
 try:print(json.dumps(diagnose(),ensure_ascii=False));return 0
 except Exception as error:print(json.dumps({'kind':'same-host-capture-download-panel-structure-v1','status':'not-verified','error':str(error),'UI_input_used':False,'capture_used':False},ensure_ascii=False));return 2
if __name__=='__main__':
 signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('panel-diagnostic-20-second-timeout')));signal.alarm(20)
 try:raise SystemExit(main())
 finally:signal.alarm(0)
