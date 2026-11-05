"""Public AppKit activation of one already-verified PID; no app launch or keys."""
import ctypes as C
BUNDLE='com.tencent.WeWorkMac'
class ActivationError(RuntimeError):pass
class PublicRunningApplication:
 def __init__(self):
  C.CDLL('/System/Library/Frameworks/AppKit.framework/AppKit');self.objc=C.CDLL('/usr/lib/libobjc.A.dylib');self.objc.objc_getClass.restype=C.c_void_p;self.objc.objc_getClass.argtypes=[C.c_char_p];self.objc.sel_registerName.restype=C.c_void_p;self.objc.sel_registerName.argtypes=[C.c_char_p];self.application=None;self.pool=self.send(self.objc.objc_getClass(b'NSAutoreleasePool'),'new',C.c_void_p)
 def close(self):
  if self.pool:self.send(self.pool,'drain',None);self.pool=None
 def send(self,target,name,result,*args):
  types=[t for t,v in args];values=[v for t,v in args];fn=C.CFUNCTYPE(result,C.c_void_p,C.c_void_p,*types)(('objc_msgSend',self.objc));return fn(target,self.objc.sel_registerName(name.encode()),*values)
 def identity(self,pid):
  cls=self.objc.objc_getClass(b'NSRunningApplication');self.application=self.send(cls,'runningApplicationWithProcessIdentifier:',C.c_void_p,(C.c_int,pid))
  if not self.application:raise ActivationError('running-app-not-found')
  bundle=self.send(self.application,'bundleIdentifier',C.c_void_p);raw=self.send(bundle,'UTF8String',C.c_char_p) if bundle else None
  return {'pid':self.send(self.application,'processIdentifier',C.c_int),'bundle':raw.decode() if raw else None,'terminated':bool(self.send(self.application,'isTerminated',C.c_bool))}
 def activate(self):return bool(self.send(self.application,'activateWithOptions:',C.c_bool,(C.c_ulong,2)))
def activate_existing(pid,port=None):
 if type(pid) is not int or pid<=0:raise ActivationError('expected-pid-required')
 port=port or PublicRunningApplication()
 try:
  identity=port.identity(pid)
  if identity!={'pid':pid,'bundle':BUNDLE,'terminated':False}:raise ActivationError('running-app-identity-mismatch')
  if port.activate() is not True:raise ActivationError('running-app-activation-rejected')
  return {'pid':pid,'bundle':BUNDLE,'request_accepted':True,'frontmost_verified':False}
 finally:
  if hasattr(port,'close'):port.close()
