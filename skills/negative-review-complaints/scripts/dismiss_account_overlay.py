#!/usr/bin/env python3
"""Dismiss only the verified merchant account hover card. One durable Escape.
Public Chrome AX shell + local DOM bridge; no website AX, coordinates or settings.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,ctypes as C,hashlib,importlib.util,json,os,sys,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
sys.path.insert(0,str(ROOT/'skills/douyin-laike-operator/scripts'))
import bridge
from dom_evidence import context,identity,nodes
spec=importlib.util.spec_from_file_location('chrome_shell_overlay',ROOT/'skills/douyin-laike-operator/scripts/chrome-shell-diagnostic.py');shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
def need(v,c):
 if not v:raise ValueError(c)
def stamp():return datetime.now(timezone.utc).isoformat()
def atomic(p,d):
 fd,tmp=tempfile.mkstemp(prefix='.overlay-',dir=p.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def overlay(tree,expected):
 ns=list(nodes(tree));need(not any(n.get('role')=='dialog' or n.get('attributes',{}).get('aria-modal')=='true' or 'byted-drawer-dialog-show' in n.get('attributes',{}).get('class','').split() for n in ns),'other-dialog-present')
 cards=[n for n in ns if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
 if not cards:return False
 need(len(cards)==1,'account-overlay-not-unique');identity(tree,expected)
 texts=[n.get('name') for n in nodes({'truncated':False,'root':cards[0]})]
 need(all(t in texts for t in ('账户ID','我的客户经理','切换公司','退出登录')),'account-overlay-signature-mismatch');return True
class NativeDismiss:
 def __init__(self,pid):self.n=shell.ChromeShellInspector(pid)
 def guard(self,title):
  n=self.n;need(n.get(n.root,'AXFrontmost') is True,'chrome-not-frontmost')
  windows=[w for w in n.array(n.root,'AXWindows') if n.get(w,'AXMain') is True]
  need(len(windows)==1,'native-main-window-not-unique');w=windows[0]
  need(n.get(w,'AXSubrole')=='AXStandardWindow' and n.get(w,'AXTitle') in (title,title+' - Google Chrome'),'native-main-title-mismatch')
  focused=n.value(n.root,'AXFocusedWindow');need(focused and n.cf.CFEqual(focused,w),'native-main-focus-mismatch')
  need(not n.array(w,'AXSheets'),'native-sheet-present')
 def foreground(self):
  n=self.n;key=n.string('AXFrontmost')
  try:
   flag=C.c_void_p.in_dll(n.cf,'kCFBooleanTrue');need(n.ax.AXUIElementSetAttributeValue(n.root,key,flag)==0,'native-frontmost-set-failed')
  finally:n.cf.CFRelease(key)
  deadline=time.monotonic()+3
  while n.get(n.root,'AXFrontmost') is not True and time.monotonic()<deadline:time.sleep(.05)
 def escape(self):
  n=self.n
  for down in (True,False):
   event=n.cg.CGEventCreateKeyboardEvent(None,53,down);need(event,'native-escape-event-unavailable')
   try:n.cg.CGEventPostToPid(n.pid,event)
   finally:n.cf.CFRelease(event)
def run(source,source_sha,tab,pid,out,request=None,native_factory=NativeDismiss):
 out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True);source=Path(source).resolve();need(hashlib.sha256(source.read_bytes()).hexdigest()==source_sha,'source-hash-mismatch');s=json.loads(source.read_text());binding={'source_sha256':source_sha,'tab_id':tab,'pid':pid,'groupid':s['groupid']}
 if out.exists():
  old=json.loads(out.read_text());need(old.get('binding')==binding,'overlay-intent-conflict');need(old.get('state')=='complete','overlay-unknown-no-replay');return old
 request=request or bridge.request
 def call(c):
  r=request(c);need(r.get('ok') is True,'bridge-operation-failed');return r['result']
 def fresh():
  tabs=call({'op':'tabs'});t=context(tabs,tab,s['groupid']);ws=[w for w in tabs if w.get('focused') is True];need(len(ws)==1 and ws[0]['windowId']==t['windowId'] and t.get('active') is True,'bridge-focused-tab-mismatch');return t,call({'op':'tree','tabId':tab})
 d={'binding':binding,'state':'preflight','started_at':stamp(),'escape_issued':False};atomic(out,d)
 try:
  call({'op':'activate','tabId':tab});n=native_factory(pid);n.foreground();t,before=fresh();n.guard(t['title']);d['before']=before
  if not overlay(before,s['identity']):d.update(state='complete',result='already-absent',completed_at=stamp());atomic(out,d);return d
  d.update(state='unknown',escape_issued=True,escape_intent_at=stamp());atomic(out,d);n.guard(t['title']);n.escape()
  t2,after=fresh();d['after']=after;need(t2==t,'tab-changed-after-escape');need(not overlay(after,s['identity']),'account-overlay-still-present-no-replay');d.update(state='complete',result='dismissed',completed_at=stamp());atomic(out,d);return d
 except Exception as e:d.update(error=str(e));atomic(out,d);raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('source','source-sha256','out'):p.add_argument('--'+name,required=True)
 p.add_argument('--tab-id',type=int,required=True);p.add_argument('--expected-pid',type=int,required=True);a=p.parse_args()
 try:print(json.dumps({'ok':True,**run(a.source,a.source_sha256,a.tab_id,a.expected_pid,a.out)},ensure_ascii=False));raise SystemExit(0)
 except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
