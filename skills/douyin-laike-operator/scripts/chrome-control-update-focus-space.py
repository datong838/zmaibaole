#!/usr/bin/env python3
"""One exact public AX focus+Space action on the installed local control update button."""
import argparse,ctypes as C,fcntl,importlib.util,json,os,time,hashlib
from pathlib import Path
from datetime import datetime,timezone
SCRIPTS=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('control_update_shell',SCRIPTS/'chrome-shell-diagnostic.py');shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
URL='chrome-extension://egeefdmlpipoboehjpheioppnmkpaehb/control.html';LABEL='加载已审核扩展更新'
def need(ok,code):
 if not ok:raise shell.AXError(code)
def now():return datetime.now(timezone.utc).isoformat()
def atomic(p,value):
 tmp=p.with_name(p.name+'.tmp')
 with tmp.open('w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 tmp.replace(p)
class ControlInspector(shell.ChromeShellInspector):
 def inspect(self,require_frontmost=True):
  is_front=self.get(self.root,'AXFrontmost') is True
  if require_frontmost:need(is_front,'control-update-chrome-not-frontmost')
  windows=[w for w in self.array(self.root,'AXWindows') if self.get(w,'AXRole')=='AXWindow' and self.get(w,'AXSubrole')=='AXStandardWindow' and self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True]
  need(len(windows)==1,'control-update-main-window-not-unique');window=windows[0];actual=self.value(self.root,'AXMainWindow');need(actual and self.cf.CFEqual(window,actual),'control-update-main-window-conflict')
  if hasattr(self,'bound_window'):need(self.cf.CFEqual(window,self.bound_window),'control-update-main-window-changed')
  else:self.bound_window=window
  areas=[];count=[0];deadline=time.monotonic()+10
  def outer(e,depth=0):
   count[0]+=1;need(count[0]<=2000 and depth<=25 and time.monotonic()<deadline,'control-update-scope-truncated')
   if self.get(e,'AXRole')=='AXWebArea':areas.append((e,self.get(e,'AXURL')));return
   for child in self.array(e,'AXChildren'):outer(child,depth+1)
  outer(window);need(len(areas)==1 and areas[0][1]==URL,'control-update-active-exact-control-required');area=areas[0][0]
  if hasattr(self,'bound_area'):need(self.cf.CFEqual(area,self.bound_area),'control-update-webarea-changed')
  else:self.bound_area=area
  targets=[]
  def inside(e,depth=0):
   count[0]+=1;need(count[0]<=2000 and depth<=25 and time.monotonic()<deadline,'control-update-scope-truncated')
   role=self.get(e,'AXRole');title=self.get(e,'AXTitle');description=self.get(e,'AXDescription')
   if role=='AXButton' and (title or description)==LABEL and self.get(e,'AXEnabled') is True:targets.append(e)
   for child in self.array(e,'AXChildren'):inside(child,depth+1)
  inside(area);need(len(targets)==1,'control-update-enabled-button-not-unique');button=targets[0]
  if hasattr(self,'bound_button'):need(self.cf.CFEqual(button,self.bound_button),'control-update-button-handle-changed')
  else:self.bound_button=button
  return {'pid':self.pid,'frontmost':is_front,'main_window_verified':True,'same_window':True,'active_control_url':URL,'single_webarea':True,'button_role':'AXButton','button_label':LABEL,'button_enabled':True,'same_button':True}
 def front_once(self):
  # Only an already-bound exact main control page permits app-level activation.
  self.inspect(require_frontmost=False)
  name=self.string('AXFrontmost');yes=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
  try:error=self.ax.AXUIElementSetAttributeValue(self.root,name,yes)
  finally:self.cf.CFRelease(name)
  need(error==0,'control-update-frontmost-assignment-unknown');deadline=time.monotonic()+2
  while self.get(self.root,'AXFrontmost') is not True:
   need(time.monotonic()<deadline,'control-update-frontmost-not-confirmed');time.sleep(.05)
  return self.inspect()
 def can_focus(self):
  self.inspect();name=self.string('AXFocused');flag=C.c_bool()
  try:error=self.ax.AXUIElementIsAttributeSettable(self.bound_button,name,C.byref(flag))
  finally:self.cf.CFRelease(name)
  self.last_evidence={'scope':self.inspect(),'AXFocused_settable_return_code':error,'AXFocused_public_settable':bool(flag.value)}
  need(error==0 and flag.value,'control-update-AXFocused-not-public-settable');return {'AXFocused_public_settable':True}
 def focus(self):
  self.can_focus();name=self.string('AXFocused');yes=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
  try:error=self.ax.AXUIElementSetAttributeValue(self.bound_button,name,yes)
  finally:self.cf.CFRelease(name)
  need(error==0,'control-update-focus-assignment-failed');deadline=time.monotonic()+2
  while True:
   actual=self.value(self.root,'AXFocusedUIElement')
   self.last_evidence={**getattr(self,'last_evidence',{}),'focused_CFEqual_button':bool(actual and self.cf.CFEqual(actual,self.bound_button)),'button_AXFocused':self.get(self.bound_button,'AXFocused')}
   if actual and self.cf.CFEqual(actual,self.bound_button) and self.get(self.bound_button,'AXFocused') is True:break
   need(time.monotonic()<deadline,'control-update-exact-focus-not-confirmed');time.sleep(.05)
  self.verify_key_boundary();return {'focused_ui_element_CFEqual_button':True,'button_AXFocused':True}
 def verify_key_boundary(self):
  proof=self.inspect();actual=self.value(self.root,'AXFocusedUIElement');need(actual and self.cf.CFEqual(actual,self.bound_button) and self.get(self.bound_button,'AXFocused') is True,'control-update-focus-lost-before-key');return {**proof,'focused_ui_element_CFEqual_button':True}
 def space_once(self):
  proof=self.verify_key_boundary();events=[]
  try:
   for down in (True,False):
    event=self.cg.CGEventCreateKeyboardEvent(None,49,down);need(event,'control-update-space-event-create-failed');events.append(event);self.cg.CGEventSetFlags(event,0)
   # Scope/focus/PID are checked again after allocating both events and before keydown.
   self.verify_key_boundary()
   for event in events:self.cg.CGEventPostToPid(self.pid,event)
  finally:
   for event in events:self.cf.CFRelease(event)
  return proof

def run(expected_pid,out,native_factory=ControlInspector,resume_preflight_sha=None):
 need(type(expected_pid) is int and expected_pid>0,'control-update-explicit-pid-required');out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 with out.with_name(out.name+'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  old=None
  if out.exists():
   raw=out.read_bytes();old=json.loads(raw);need(old.get('kind')=='one-shot-public-AX-control-update-v1' and old.get('expected_pid')==expected_pid and old.get('control_url')==URL,'control-update-intent-scope-conflict')
   if resume_preflight_sha is None:return {**old,'already_recorded':True,'replayed':False}
   need(hashlib.sha256(raw).hexdigest()==resume_preflight_sha,'control-update-resume-original-sha-conflict')
   need(set(old)=={'kind','expected_pid','control_url','button_label','state','phase','created_at','replayed','space_posted','extension_version_verified','business_actions','last_native_evidence','error'} and old.get('button_label')==LABEL and old.get('replayed') is False and old.get('business_actions') is False and old.get('extension_version_verified') is False and old.get('last_native_evidence') is None and isinstance(old.get('created_at'),str) and bool(old['created_at']) and old.get('state')=='stopped-before-input' and old.get('phase')=='verify-scope' and old.get('error')=='control-update-chrome-not-frontmost' and old.get('space_posted') is False and not any(k in old for k in ('scope','focus','boundary','space_intent_at','preflight_recovery','activation_intent_at')),'control-update-only-known-zero-input-preflight-resumable')
   archive=out.with_name(out.name+'.preflight-original-'+resume_preflight_sha+'.json')
   if archive.exists():need(archive.read_bytes()==raw,'control-update-preflight-archive-conflict')
   else:
    with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   proof=out.with_name(out.name+'.preflight-recovery-'+resume_preflight_sha+'.json');body={'kind':'verified-zero-input-control-preflight-recovery-v1','at':now(),'outpath':str(out),'original':{'path':str(archive),'sha256':resume_preflight_sha},'original_error':old['error'],'created_at_preserved':old['created_at'],'known_zero_input_verified':True,'no_prior_focus_or_key_intent':True,'no_new_key_or_outpath':True}
   need(not proof.exists(),'control-update-preflight-recovery-already-used')
   with proof.open('x') as f:json.dump(body,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
   saved=dict(old);saved.pop('error');saved['preflight_recovery']={'kind':body['kind'],'original':body['original'],'proof':{'path':str(proof),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}};saved.update(state='preflight',phase='verify-scope');atomic(out,saved)
  else:
   need(resume_preflight_sha is None,'control-update-resume-original-intent-required')
   saved={'kind':'one-shot-public-AX-control-update-v1','expected_pid':expected_pid,'control_url':URL,'button_label':LABEL,'state':'preflight','phase':'verify-scope','created_at':now(),'replayed':False,'space_posted':False,'extension_version_verified':False,'business_actions':False}
  native=None
  try:
   native=native_factory(expected_pid=expected_pid);need(native.pid==expected_pid,'control-update-process-changed');saved['preactivation_scope']=native.inspect(require_frontmost=False)
   if saved['preactivation_scope'].get('frontmost') is not True:
    saved.update(state='unknown',phase='activate-intent',activation_intent_at=now());atomic(out,saved)
    saved['activation']=native.front_once()
   saved['scope']=native.inspect();saved['settable']=native.can_focus();saved.update(state='unknown',phase='focus-intent');atomic(out,saved)
   saved['focus']=native.focus();saved['boundary']=native.verify_key_boundary();saved.update(state='unknown',phase='space-intent',space_intent_at=now());atomic(out,saved)
   native.space_once();saved.update(state='action-returned',phase='space-post-returned',space_posted=True,completed_at=now());atomic(out,saved);return saved
  except Exception as e:
   saved['last_native_evidence']=getattr(native,'last_evidence',None)
   saved.update(error=str(e),state='unknown' if saved['phase'] in ('activate-intent','focus-intent','space-intent') else 'stopped-before-input');atomic(out,saved);raise
  finally:
   if native:native.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--resume-preflight',action='store_true');p.add_argument('--original-sha','--original-sha256',dest='original_sha256');a=p.parse_args();need(bool(a.resume_preflight)==bool(a.original_sha256),'control-update-explicit-resume-sha-required')
 try:r=run(a.expected_pid,a.out,resume_preflight_sha=a.original_sha256 if a.resume_preflight else None);print(json.dumps(r,ensure_ascii=False));return 0 if r['state']=='action-returned' else 2
 except Exception as e:print(json.dumps({'ok':False,'error':str(e),'replayed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
