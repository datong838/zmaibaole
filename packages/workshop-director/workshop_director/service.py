import hashlib,os,plistlib,subprocess,sys
from pathlib import Path
from .common import *
LABEL='local.workshop-director'
# This release's fixed local authorization identity; updates require reviewed pins.
PROJECT=Path('/Users/feibing/work/projects/zmaibaole')
HOST_APP=PROJECT/'dist/WorkshopDirectorHost.app'
HOST_RELEASE=Path(str(HOST_APP)+'.release.json')
HOST_RELEASE_SHA='968aae7069cf2ffd9f13259007df2feaaca78efcc76b782129b8b686679171ee'
def host_plist(root):
    root=Path(root).resolve();need(sys.platform=='darwin','launchd-macos-only');need(root==PROJECT/'runtime/standalone-workshop-director','reviewed-host-runtime-required')
    release=pinned({'path':str(HOST_RELEASE),'sha256':HOST_RELEASE_SHA})
    need(release.get('app')==str(HOST_APP) and release.get('identifier')=='local.workshop-director.host' and release.get('serve_supported') is True,'reviewed-host-release-required')
    paths=list(HOST_APP.rglob('*'));need(not HOST_APP.is_symlink() and not any(p.is_symlink() for p in paths),'host-bundle-symlink-refused')
    actual=sorted(str(p) for p in paths if p.is_file());need(actual==sorted(f['path'] for f in release['files']),'host-bundle-file-set-changed')
    for item in release['files']:
        need(Path(item['path']).is_relative_to(HOST_APP),'host-release-file-outside-bundle');pinned_bytes=Path(item['path']).read_bytes();need(hashlib.sha256(pinned_bytes).hexdigest()==item['sha256'],'host-bundle-bytes-changed')
    info=plistlib.loads((HOST_APP/'Contents/Info.plist').read_bytes());need(info.get('CFBundleIdentifier')=='local.workshop-director.host' and info.get('CFBundleExecutable')=='WorkshopHost','host-bundle-identity-changed')
    config=read(HOST_APP/'Contents/Resources/host-config.json');need(config.get('root')==str(root) and config.get('app_path')==str(HOST_APP) and config.get('package')==str(PROJECT/'packages/workshop-director'),'host-config-scope-changed')
    checked=subprocess.run(['/usr/bin/codesign','--verify','--strict',str(HOST_APP)],capture_output=True,text=True,timeout=15);need(checked.returncode==0,'host-signature-verification-failed')
    return {'Label':LABEL,'ProgramArguments':[str(HOST_APP/'Contents/MacOS/WorkshopHost'),'--serve'],'RunAtLoad':True,'KeepAlive':{'SuccessfulExit':False},'ThrottleInterval':30,'ProcessType':'Interactive','WorkingDirectory':str(root),'StandardOutPath':str(root/'host.stdout.log'),'StandardErrorPath':str(root/'host.stderr.log')}
def generate(root,out):
    value=host_plist(root)
    installed=Path.home()/'Library/LaunchAgents'/(LABEL+'.plist')
    if installed.exists():need(plistlib.loads(installed.read_bytes())==value,'installed-route-differs-use-reviewed-migration')
    p=Path(out).resolve();need(not p.exists(),'plist-already-exists');p.write_bytes(plistlib.dumps(value));return ref(p)
def install(root,plist,confirm=False):
    need(confirm,'explicit-install-flag-required');value=plistlib.loads(Path(plist).read_bytes());need(value==host_plist(root),'reviewed-host-plist-scope-required')
    dest=Path.home()/'Library/LaunchAgents'/(LABEL+'.plist');need(not dest.exists(),'service-already-installed-use-reviewed-migration');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(plist).read_bytes());subprocess.run(['/bin/launchctl','bootstrap','gui/'+str(os.getuid()),str(dest)],check=True);return str(dest)
def uninstall(confirm=False):
    need(confirm,'explicit-uninstall-flag-required');need(sys.platform=='darwin','launchd-macos-only');dest=Path.home()/'Library/LaunchAgents'/(LABEL+'.plist');need(dest.exists(),'service-not-installed');subprocess.run(['/bin/launchctl','bootout','gui/'+str(os.getuid()),str(dest)],check=True);dest.unlink()
def health(root):
    from .store import Store
    s=Store(root)
    try:
        v=s.get('daemon');return {'configured':(Path(root)/'config.json').is_file(),'daemon':v,'daemon_identity_alive':same_process(v.get('process')) if v else False,'resource_owner':s.get('resource_owner'),'task_counts':{x:sum(t['state']==x for t in s.tasks()) for x in ('queued','running','waiting','failed','unknown','complete')}}
    finally:s.close()
