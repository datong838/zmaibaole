"""One-shot public WeCom process/window metadata, never a sender or UI input.
Run by the existing independent Host operator, not as a Codex permission test.
Only top-level titles and role/subrole/child membership are read; no AXValue,
AXDescription, clipboard, transcript, recipient labels, screenshots or activation.
"""
import argparse,ctypes as C,hashlib,json,plistlib,re,subprocess,sys,time
from pathlib import Path
ROOT=Path('/Users/feibing/work/projects/zmaibaole');SCRIPTS=ROOT/'skills/wecom-messenger/scripts';sys.path.insert(0,str(SCRIPTS))
from main_window import STOP,REQUIRED_CHILD_PATHS,dialog_shape
from public_app_activation import PublicRunningApplication
APP=Path('/Applications/企业微信.app');BUNDLE='com.tencent.WeWorkMac'
class DiagnosticError(RuntimeError):pass
class PublicAX:
 def __init__(self):
  if sys.platform!='darwin':raise DiagnosticError('macos-required')
  self.cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation');self.ax=C.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices');self.refs=[];self.errors=[]
  def fn(lib,name,result,*args):
   f=getattr(lib,name);f.restype=result;f.argtypes=list(args)
  p=C.c_void_p;i=C.c_int;z=C.c_long
  for name,result,args in [('CFStringCreateWithCString',p,(p,C.c_char_p,C.c_uint32)),('CFStringGetLength',z,(p,)),('CFStringGetMaximumSizeForEncoding',z,(z,C.c_uint32)),('CFStringGetCString',C.c_bool,(p,p,z,C.c_uint32)),('CFGetTypeID',C.c_ulong,(p,)),('CFStringGetTypeID',C.c_ulong,()),('CFArrayGetTypeID',C.c_ulong,()),('CFArrayGetCount',z,(p,)),('CFArrayGetValueAtIndex',p,(p,z)),('CFRelease',None,(p,))]:fn(self.cf,name,result,*args)
  fn(self.ax,'AXIsProcessTrusted',C.c_bool);fn(self.ax,'AXUIElementCreateApplication',p,i);fn(self.ax,'AXUIElementSetMessagingTimeout',i,p,C.c_float);fn(self.ax,'AXUIElementCopyAttributeValue',i,p,p,C.POINTER(p))
 def trusted(self):return bool(self.ax.AXIsProcessTrusted())
 def root(self,pid):
  root=self.ax.AXUIElementCreateApplication(pid)
  if not root:raise DiagnosticError('AX-application-unavailable')
  self.refs.append(root);error=self.ax.AXUIElementSetMessagingTimeout(root,1.)
  if error:raise DiagnosticError('AX-timeout-setting-failed:'+str(error))
  return root
 def value(self,e,key):
  if key not in {'AXWindows','AXChildren','AXRole','AXSubrole','AXTitle'}:raise DiagnosticError('diagnostic-attribute-forbidden')
  name=self.cf.CFStringCreateWithCString(None,key.encode(),0x08000100);out=C.c_void_p()
  try:error=int(self.ax.AXUIElementCopyAttributeValue(e,name,C.byref(out)))
  finally:self.cf.CFRelease(name)
  if out.value:self.refs.append(out.value)
  if error or not out.value:self.errors.append({'attribute':key,'error':error,'present':bool(out.value)})
  return error,out.value
 def text(self,e,key):
  error,v=self.value(e,key)
  if error or not v:return {'error':error,'present':bool(v),'value':None}
  if self.cf.CFGetTypeID(v)!=self.cf.CFStringGetTypeID():return {'error':0,'present':True,'value':None,'type_error':True}
  n=self.cf.CFStringGetMaximumSizeForEncoding(self.cf.CFStringGetLength(v),0x08000100)+1
  if n>4096:return {'error':0,'present':True,'value':None,'oversize':True}
  raw=C.create_string_buffer(n)
  if not self.cf.CFStringGetCString(v,raw,n,0x08000100):return {'error':0,'present':True,'value':None,'decode_error':True}
  return {'error':0,'present':True,'value':raw.value.decode('utf-8')}
 def get(self,e,key):return self.text(e,key)['value']
 def array(self,e,key,required=False):
  error,v=self.value(e,key)
  if error or not v:
   if not required and error in (0,-25205,-25212):return None
   raise DiagnosticError(key+'-unavailable:'+str(error)+':present='+str(bool(v)))
  if self.cf.CFGetTypeID(v)!=self.cf.CFArrayGetTypeID():raise DiagnosticError(key+'-not-array')
  count=self.cf.CFArrayGetCount(v)
  if count<0 or count>(32 if key=='AXWindows' else 250):raise DiagnosticError(key+'-count-limit')
  return [self.cf.CFArrayGetValueAtIndex(v,i) for i in range(count)]
 def close(self):
  for value in reversed(self.refs):self.cf.CFRelease(value)
  self.refs=[]
def role_shape(port,window):
 count=0
 def read(e,path=()):
  nonlocal count
  count+=1
  if count>250 or len(path)>12:raise DiagnosticError('main-dialog-shape-budget')
  role=port.get(e,'AXRole');row={'role':role,'AXSubrole':port.get(e,'AXSubrole')}
  if not path:row['AXTitle']=port.get(e,'AXTitle')
  if role not in STOP:
   children=port.array(e,'AXChildren',path in REQUIRED_CHILD_PATHS)
   row['children']=[read(c,path+(i,)) for i,c in enumerate(children or [])]
  return row
 return read(window)
def public_processes():
 with (APP/'Contents/Info.plist').open('rb') as f:info=plistlib.load(f)
 if info.get('CFBundleIdentifier')!=BUNDLE:raise DiagnosticError('installed-bundle-mismatch')
 executable=str(APP/'Contents/MacOS'/info['CFBundleExecutable']);done=subprocess.run(['/usr/bin/pgrep','-fx',re.escape(executable)],capture_output=True,text=True,timeout=5)
 if done.returncode not in (0,1):raise DiagnosticError('exact-process-query-failed')
 ids=done.stdout.split()
 if any(not re.fullmatch('[1-9][0-9]*',p) for p in ids) or len(ids)>8:raise DiagnosticError('exact-process-output-invalid')
 return [int(p) for p in ids]
def public_identity(pid):
 port=PublicRunningApplication()
 try:return port.identity(pid)
 finally:port.close()
def diagnose(expected_pid,*,process_reader=public_processes,identity_reader=public_identity,ax_factory=PublicAX):
 if type(expected_pid) is not int or expected_pid<=0:raise DiagnosticError('expected-existing-pid-required')
 started=time.monotonic();ids=process_reader();report={'kind':'wecom-initial-locate-public-diagnostic-v1','host_process':{'pid':__import__('os').getpid(),'ppid':__import__('os').getppid(),'python':sys.executable},'expected_pid':expected_pid,'bundle':BUNDLE,'exact_process_ids':ids,'exact_process_count':len(ids),'windows':[],'UI_input_used':False,'sender_or_recovery_authority':False,'message_or_recipient_content_read':False}
 report['predicate_source_refs']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (SCRIPTS/'native.py',SCRIPTS/'main_window.py')]
 if expected_pid not in ids:report['status']='zero-exact-processes' if not ids else 'expected-exact-process-absent';report['elapsed_seconds']=time.monotonic()-started;return report
 identity=identity_reader(expected_pid);report['running_application']=identity
 if identity!={'pid':expected_pid,'bundle':BUNDLE,'terminated':False}:report['status']='public-bundle-identity-mismatch';report['elapsed_seconds']=time.monotonic()-started;return report
 port=ax_factory()
 try:
  report['accessibility_trusted']=port.trusted()
  if not report['accessibility_trusted']:report['status']='accessibility-not-trusted';return report
  root=port.root(expected_pid)
  try:windows=port.array(root,'AXWindows',True)
  except Exception as exc:report['status']='AXWindows-unavailable';report['AXWindows_error']=str(exc);return report
  report['AXWindows_count']=len(windows)
  for index,window in enumerate(windows):
   fields={key:port.text(window,key) for key in ('AXRole','AXSubrole','AXTitle')};row={'index':index,'attributes':fields,'legacy_standard_match':fields['AXTitle']['value']=='企业微信' and fields['AXSubrole']['value']=='AXStandardWindow','dialog_shape_evaluated':False}
   if len(windows)==1 and fields['AXTitle']['value']=='企业微信' and fields['AXSubrole']['value']=='AXDialog':
    row['dialog_shape_evaluated']=True
    try:row['public_role_shape']=role_shape(port,window);row['current_dialog_shape_match']=dialog_shape(row['public_role_shape'])
    except Exception as exc:row['current_dialog_shape_match']=False;row['shape_error']=str(exc)
   report['windows'].append(row)
  matched=any(w['legacy_standard_match'] for w in report['windows']) or len(windows)==1 and report['windows'][0].get('current_dialog_shape_match') is True
  report['current_Native_process_candidate']=matched;report['unpinned_Native_process_selection_complete']=len(ids)==1;report['main_window_match_count']=sum(w['legacy_standard_match'] or w.get('current_dialog_shape_match') is True for w in report['windows']);report['status']='zero-AXWindows' if not windows else 'current-main-predicate-matched' if matched else 'window-main-predicate-not-matched';report['attribute_errors']=list(port.errors)
  return report
 finally:port.close();report['elapsed_seconds']=time.monotonic()-started
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--expected-pid',type=int);args=parser.parse_args()
 try:
  ids=public_processes();pid=args.expected_pid if args.expected_pid is not None else ids[0] if len(ids)==1 else None
  result=diagnose(pid,process_reader=lambda:ids) if pid is not None else {'kind':'wecom-initial-locate-public-diagnostic-v1','status':'zero-exact-processes' if not ids else 'multiple-exact-processes-no-selection','exact_process_ids':ids,'UI_input_used':False,'sender_or_recovery_authority':False}
  print(json.dumps(result,ensure_ascii=False,indent=2))
 except Exception as exc:print(json.dumps({'kind':'wecom-initial-locate-public-diagnostic-v1','status':'diagnostic-error','error':str(exc),'UI_input_used':False},ensure_ascii=False));raise SystemExit(2)
