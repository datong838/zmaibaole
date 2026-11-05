#!/usr/bin/env python3
"""One-shot normal Chrome Cmd+T -> verified blank tab -> bound toolbar control.
No merchant WebArea content, address input, browser settings, debug or replay.
"""
import argparse,ctypes as C,fcntl,hashlib,importlib.util,json,time
from pathlib import Path
from datetime import datetime,timezone
SCRIPTS=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('maintenance_chrome_shell',SCRIPTS/'chrome-shell-diagnostic.py')
shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
LABEL='Open local DOM bridge control'
BLANK={'chrome://newtab','chrome://newtab/','chrome://new-tab-page','chrome://new-tab-page/'}
def need(ok,code):
    if not ok:raise shell.AXError(code)
def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,value):
    tmp=path.with_name(path.name+'.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
class MaintenanceInspector(shell.ChromeShellInspector):
    def front(self):
        name=self.string('AXFrontmost');yes=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
        try:need(self.ax.AXUIElementSetAttributeValue(self.root,name,yes)==0,'maintenance-chrome-front-failed')
        finally:self.cf.CFRelease(name)
        deadline=time.monotonic()+2
        while self.get(self.root,'AXFrontmost') is not True:
            need(time.monotonic()<deadline,'maintenance-chrome-front-not-confirmed');time.sleep(.05)
    def observe(self):
        need(self.get(self.root,'AXFrontmost') is True,'chrome-not-frontmost')
        windows=[w for w in self.array(self.root,'AXWindows') if self.get(w,'AXSubrole')=='AXStandardWindow' and self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True]
        need(len(windows)==1,'main-chrome-window-not-unique');window=windows[0]
        main=self.value(self.root,'AXMainWindow');need(main and self.cf.CFEqual(main,window),'chrome-main-window-conflict')
        if hasattr(self,'bound_window'):need(self.cf.CFEqual(self.bound_window,window),'maintenance-window-changed')
        else:self.bound_window=window
        areas=[];targets=[];count=0;deadline=time.monotonic()+10
        def walk(e,toolbar=False,depth=0):
            nonlocal count
            count+=1;need(count<=2500 and depth<=25 and time.monotonic()<deadline,'maintenance-shell-truncated')
            role=self.get(e,'AXRole')
            if role=='AXWebArea':
                # Only public browser-level URL; never any page attributes/children.
                areas.append(self.get(e,'AXURL'));return
            toolbar=toolbar or role=='AXToolbar'
            if toolbar and role in ('AXButton','AXPopUpButton') and self.get(e,'AXEnabled') is True and str(self.get(e,'AXTitle') or '').split('\n')[0]==LABEL:
                actions=C.c_void_p()
                if self.ax.AXUIElementCopyActionNames(e,C.byref(actions))==0 and actions.value:
                    self.refs.append(actions.value)
                    names=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(self.cf.CFArrayGetCount(actions.value))]
                    if 'AXPress' in names:targets.append(e)
            for child in self.array(e,'AXChildren'):walk(child,toolbar,depth+1)
        walk(window)
        self.maintenance_targets=targets
        return {'pid':self.pid,'frontmost':True,'main_window_verified':True,'same_window':True,'web_areas_count':len(areas),'blank_url':areas[0] if len(areas)==1 and areas[0] in BLANK else None,'blank_verified':len(areas)==1 and areas[0] in BLANK,'toolbar_targets':len(targets),'business_page_content_read':False}
    def new_tab(self):
        self.observe() # Same frontmost/main window immediately before key emission.
        for down in (True,False):
            event=self.cg.CGEventCreateKeyboardEvent(None,17,down)
            need(event,'maintenance-cmd-t-event-failed')
            try:self.cg.CGEventSetFlags(event,1<<20);self.cg.CGEventPostToPid(self.pid,event)
            finally:self.cf.CFRelease(event)
    def open_control(self):
        proof=self.observe();need(proof['blank_verified'],'maintenance-active-tab-not-blank');need(proof['toolbar_targets']==1,'maintenance-toolbar-not-unique')
        action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(self.maintenance_targets[0],action)
        finally:self.cf.CFRelease(action)
        need(error==0,'maintenance-control-open-outcome-unknown')

def run(pid,out,native_factory=MaintenanceInspector):
    need(type(pid) is int and pid>0,'explicit-chrome-pid-required');out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_name(out.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():
            saved=json.loads(out.read_text());need(saved.get('mode')=='open-maintenance-control' and saved.get('expected_pid')==pid,'maintenance-intent-scope-conflict');return {**saved,'replayed':False,'already_recorded':True}
        native=None;saved={'mode':'open-maintenance-control','expected_pid':pid,'state':'unknown','phase':'verify-shell','created_at':now(),'replayed':False,'merchant_tab_modified':False}
        try:
            native=native_factory(expected_pid=pid);need(native.pid==pid,'chrome-process-changed')
            if hasattr(native,'front'):native.front()
            before=native.observe()
            need(before.get('frontmost') is True and before.get('main_window_verified') is True,'maintenance-shell-unverified')
            saved.update(phase='cmd-t-intent',before=before);atomic(out,saved)
            native.new_tab();saved.update(phase='verify-blank',cmd_t_returned=True);atomic(out,saved)
            deadline=time.monotonic()+2
            while True:
                after=native.observe()
                if after.get('blank_verified') is True:break
                need(time.monotonic()<deadline,'maintenance-active-tab-not-blank');time.sleep(.05)
            need(after.get('same_window') is True and after.get('web_areas_count')==1 and after.get('blank_url') in BLANK and after.get('toolbar_targets')==1,'maintenance-blank-or-toolbar-unverified')
            saved.update(phase='toolbar-intent',blank_proof=after);atomic(out,saved)
            native.open_control();saved.update(state='complete',phase='toolbar-action-returned',control_page_verified=False,toolbar_press_returned=True,completed_at=now());atomic(out,saved);return saved
        except Exception as error:
            saved.update(error=str(error),state='unknown');atomic(out,saved);raise
        finally:
            if native:native.close()

def resume_verified_blank(pid,out,original_sha,native_factory=MaintenanceInspector):
    """Continue only an unattempted toolbar step; never repeat Cmd+T or a press."""
    out=Path(out).resolve();need(type(pid) is int and pid>0,'explicit-chrome-pid-required')
    with out.with_name(out.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raw=out.read_bytes();need(hashlib.sha256(raw).hexdigest()==original_sha,'maintenance-original-intent-changed')
        saved=json.loads(raw)
        need(saved.get('mode')=='open-maintenance-control' and saved.get('expected_pid')==pid,'maintenance-intent-scope-conflict')
        need(saved.get('state')=='unknown' and saved.get('phase')=='verify-blank' and saved.get('cmd_t_returned') is True and saved.get('error')=='maintenance-active-tab-not-blank' and 'blank_proof' not in saved and not saved.get('toolbar_press_returned') and 'blank_recovery' not in saved,'maintenance-not-unattempted-toolbar-step')
        native=None
        try:
            native=native_factory(expected_pid=pid);need(native.pid==pid,'chrome-process-changed')
            if hasattr(native,'front'):native.front()
            proof=native.observe()
            need(proof.get('frontmost') is True and proof.get('main_window_verified') is True and proof.get('same_window') is True and proof.get('web_areas_count')==1 and proof.get('blank_verified') is True and proof.get('blank_url') in BLANK and proof.get('toolbar_targets')==1,'maintenance-recovery-current-blank-unverified')
            saved.update(phase='toolbar-intent',blank_proof=proof,blank_recovery={'original_intent_sha256':original_sha,'original_error':saved['error'],'at':now(),'cmd_t_repeated':False})
            atomic(out,saved)
            native.open_control()
            saved.update(state='complete',phase='toolbar-action-returned',control_page_verified=False,toolbar_press_returned=True,completed_at=now());atomic(out,saved);return saved
        except Exception as error:
            # A failed preflight performs no input; a persisted toolbar intent
            # remains unknown and can never re-enter this recovery path.
            if saved.get('phase')=='toolbar-intent':saved.update(state='unknown',error=str(error));atomic(out,saved)
            raise
        finally:
            if native:native.close()
def main():
    p=argparse.ArgumentParser(description=__doc__);modes=p.add_mutually_exclusive_group(required=True);modes.add_argument('--open-maintenance-control',action='store_true');modes.add_argument('--resume-verified-blank',action='store_true');p.add_argument('--original-intent-sha256');p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:
        result=resume_verified_blank(a.expected_pid,a.out,a.original_intent_sha256) if a.resume_verified_blank else run(a.expected_pid,a.out);print(json.dumps(result,ensure_ascii=False));return 0 if result['state']=='complete' else 2
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'replayed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
