"""Public Chrome main-code signature identity for macOS code_sign_clone paths.
No resources/profile inspection, mutation, process input, or browser debugging.
"""
import ctypes as C,hashlib,os,plistlib,re,subprocess
from pathlib import Path
EXE='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
TEAM='EQHXZ8M8AV';IDENTIFIER='com.google.Chrome'
CLONE=re.compile(r'/private/var/folders/[A-Za-z0-9_]{2}/[A-Za-z0-9_]+/X/com\.google\.Chrome\.code_sign_clone/code_sign_clone\.[A-Za-z0-9]+/Google Chrome\.app\.bundle/Contents/MacOS/Google Chrome')
def need(ok,code):
    if not ok:raise ValueError(code)
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
def display(path,run=subprocess.run):
    r=run(['/usr/bin/codesign','-d','--verbose=4','-r-',path],capture_output=True,text=True,timeout=10)
    need(r.returncode==0,'chrome-signature-metadata-unavailable');text=r.stdout+'\n'+r.stderr
    values={}
    for key in ('Executable','Identifier','TeamIdentifier','CDHash'):
        matches=re.findall(r'^'+key+r'=(.+)$',text,re.M);need(len(matches)==1,'chrome-signature-field-not-unique:'+key);values[key]=matches[0]
    requirements=re.findall(r'^designated => (.+)$',text,re.M);need(len(requirements)==1 and len(requirements[0])<8000,'chrome-designated-requirement-unavailable');values['designated_requirement']=requirements[0]
    need(values['Executable']==path and values['Identifier']==IDENTIFIER and values['TeamIdentifier']==TEAM and re.fullmatch(r'[a-f0-9]{40,64}',values['CDHash']),'chrome-main-signed-publisher-mismatch')
    return values

def code_validity(path,requirement):
    """SDK SecStaticCode.h: checkAllArchitectures=1<<0, doNotValidateResources=1<<2.
    DoNotValidateExecutable is deliberately absent: all main-code pages checked.
    No allowNetworkAccess/nested-code/resource/strict-bundle flags are requested.
    """
    sec=C.CDLL('/System/Library/Frameworks/Security.framework/Security');cf=C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation');p=C.c_void_p
    def fn(lib,name,result,*args):f=getattr(lib,name);f.restype=result;f.argtypes=list(args);return f
    fn(cf,'CFURLCreateFromFileSystemRepresentation',p,p,C.c_char_p,C.c_long,C.c_bool);fn(cf,'CFStringCreateWithCString',p,p,C.c_char_p,C.c_uint32);fn(cf,'CFRelease',None,p)
    fn(sec,'SecStaticCodeCreateWithPath',C.c_int,p,C.c_uint32,C.POINTER(p));fn(sec,'SecRequirementCreateWithString',C.c_int,p,C.c_uint32,C.POINTER(p));fn(sec,'SecStaticCodeCheckValidity',C.c_int,p,C.c_uint32,p)
    raw=os.fsencode(path);url=cf.CFURLCreateFromFileSystemRepresentation(None,raw,len(raw),False);string=cf.CFStringCreateWithCString(None,requirement.encode(),0x08000100);code=p();req=p()
    need(url and string,'chrome-signature-public-input-allocation-failed')
    try:
        need(sec.SecStaticCodeCreateWithPath(url,0,C.byref(code))==0 and code.value,'chrome-static-code-create-failed')
        need(sec.SecRequirementCreateWithString(string,0,C.byref(req))==0 and req.value,'chrome-static-requirement-create-failed')
        status=sec.SecStaticCodeCheckValidity(code,(1<<0)|(1<<2),req)
        need(status==0,'chrome-signed-main-code-invalid:'+str(status))
        return {'api':'SecStaticCodeCheckValidity','flags':['kSecCSCheckAllArchitectures','kSecCSDoNotValidateResources'],'status':status,'main_executable_pages_verified':True,'bundle_resources_verified':False,'network_access_requested':False}
    finally:
        for value in (code.value,req.value,string,url):
            if value:cf.CFRelease(value)

def bundle_main(path,load=None):
    bundle=Path(path).parent.parent.parent;info=bundle/'Contents/Info.plist'
    if load is None:
        with info.open('rb') as f:v=plistlib.load(f)
    else:v=load(str(info))
    need(v.get('CFBundleIdentifier')==IDENTIFIER and v.get('CFBundleExecutable')=='Google Chrome','chrome-main-bundle-binding-invalid')
    return {'bundle_path':str(bundle),'CFBundleIdentifier':v['CFBundleIdentifier'],'CFBundleExecutable':v['CFBundleExecutable']}

def verify(path,*,display_fn=display,validity_fn=code_validity,bundle_fn=bundle_main,resolve_fn=lambda p:str(Path(p).resolve())):
    need(isinstance(path,str) and CLONE.fullmatch(path) is not None and resolve_fn(path)==path,'chrome-unreviewed-process-clone-path')
    installed=display_fn(EXE);observed=display_fn(path)
    need(installed['Identifier']==observed['Identifier']==IDENTIFIER and installed['TeamIdentifier']==observed['TeamIdentifier']==TEAM and installed['designated_requirement']==observed['designated_requirement'],'chrome-clone-signed-identity-mismatch')
    installed_bundle=bundle_fn(EXE);observed_bundle=bundle_fn(path)
    requirement='('+installed['designated_requirement']+') and identifier "'+IDENTIFIER+'" and certificate leaf[subject.OU] = "'+TEAM+'"'
    a=validity_fn(EXE,requirement);b=validity_fn(path,requirement)
    value={'kind':'macos-chrome-code-sign-clone-v1','validation_scope':'signed-main-executable-code-only','bundle_resources_verified':False,'configured_executable':EXE,'observed_executable':path,'identifier':IDENTIFIER,'team_identifier':TEAM,'designated_requirement':installed['designated_requirement'],'designated_requirement_sha256':digest(installed['designated_requirement']),'installed_cdhash':installed['CDHash'],'observed_cdhash':observed['CDHash'],'installed_bundle':installed_bundle,'observed_bundle':observed_bundle,'installed_code_validation':a,'observed_code_validation':b}
    return validate_record(value,path)

def validate_record(value,path):
    need(isinstance(path,str) and CLONE.fullmatch(path) is not None and isinstance(value,dict) and value.get('kind')=='macos-chrome-code-sign-clone-v1' and value.get('validation_scope')=='signed-main-executable-code-only' and value.get('bundle_resources_verified') is False and value.get('configured_executable')==EXE and value.get('observed_executable')==path and value.get('identifier')==IDENTIFIER and value.get('team_identifier')==TEAM,'chrome-clone-record-scope-invalid')
    requirement=value.get('designated_requirement');need(isinstance(requirement,str) and 0<len(requirement)<8000 and value.get('designated_requirement_sha256')==digest(requirement),'chrome-clone-record-requirement-invalid')
    for field in ('installed_cdhash','observed_cdhash'):need(re.fullmatch(r'[a-f0-9]{40,64}',str(value.get(field,''))) is not None,'chrome-clone-record-cdhash-invalid')
    for field,binary in (('installed_bundle',EXE),('observed_bundle',path)):
        need(value.get(field)=={'bundle_path':str(Path(binary).parent.parent.parent),'CFBundleIdentifier':IDENTIFIER,'CFBundleExecutable':'Google Chrome'},'chrome-clone-record-main-binary-invalid')
    expected={'api':'SecStaticCodeCheckValidity','flags':['kSecCSCheckAllArchitectures','kSecCSDoNotValidateResources'],'status':0,'main_executable_pages_verified':True,'bundle_resources_verified':False,'network_access_requested':False}
    need(all(value.get(field)==expected for field in ('installed_code_validation','observed_code_validation')),'chrome-clone-record-code-validity-invalid')
    return value
