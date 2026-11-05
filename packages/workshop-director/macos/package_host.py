#!/usr/bin/env python3
"""Build only. No app opening, installing, permission request or service migration."""
import argparse,hashlib,json,os,plistlib,subprocess
from pathlib import Path
ID='local.workshop-director.host'
FILENAME='门店评价_全部门店_2026_10_22-2026_10_22.xlsx'
SHA='841c1c82700e5f29b791cf318bb8bceeec08dc1d205436075dcc33275fd6dd37'
def ref(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def build(out,python,probe_dir,allow,package,root):
 if not allow:raise ValueError('explicit-local-adhoc-review-required')
 out=Path(out).resolve();probe_dir=Path(probe_dir).resolve();python=Path(python).resolve();package=Path(package).resolve();root=Path(root).resolve()
 if out.exists() or out.suffix!='.app':raise ValueError('new-app-path-required')
 if not python.is_file() or not os.access(python,os.X_OK):raise ValueError('python-executable-required')
 if not (root/'config.json').is_file() or not (package/'workshop_director/__main__.py').is_file():raise ValueError('original-runtime-package-required')
 if not probe_dir.is_dir():raise ValueError('existing-probe-directory-required')
 (out/'Contents/MacOS').mkdir(parents=True);r=out/'Contents/Resources';r.mkdir()
 info={'CFBundleIdentifier':ID,'CFBundleName':'Workshop Director','CFBundleDisplayName':'车间主任授权','CFBundleExecutable':'WorkshopHost','CFBundlePackageType':'APPL','CFBundleVersion':'3','CFBundleShortVersionString':'0.3.0','LSMinimumSystemVersion':'11.0','NSDownloadsFolderUsageDescription':'车间主任需要读取您主动导出的门店评价Excel，用于本地统计；不会上传或更改下载文件。','NSHighResolutionCapable':True}
 (out/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
 c={'kind':'workshop-permission-only-host-config-v3','python':str(python),'package':str(package),'root':str(root),'app_path':str(out),'probe_file':str(Path.home()/'Downloads'/FILENAME),'probe_filename':FILENAME,'probe_sha256':SHA,'probe_size':16659,'probe_dir':str(probe_dir)}
 (r/'host-config.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');(r/'permission_probe.py').write_bytes(Path(__file__).with_name('permission_probe.py').read_bytes())
 subprocess.run(['/usr/bin/clang','-fobjc-arc','-mmacosx-version-min=11.0',str(Path(__file__).with_name('Host.m')),'-framework','Cocoa','-framework','ApplicationServices','-framework','CoreGraphics','-o',str(out/'Contents/MacOS/WorkshopHost')],check=True)
 subprocess.run(['/usr/bin/codesign','--force','--sign','-','--identifier',ID,str(out)],check=True,capture_output=True)
 subprocess.run(['/usr/bin/codesign','--verify','--strict',str(out)],check=True,capture_output=True)
 manifest={'kind':'permission-only-host-release-v3','app':str(out),'identifier':ID,'mode':'local-adhoc-explicit-review','files':[ref(p) for p in sorted(out.rglob('*')) if p.is_file()],'probe_dir':str(probe_dir),'serve_supported':True,'actual_child_permissions_tested':False}
 release=Path(str(out)+'.release.json');release.write_text(json.dumps(manifest,indent=2)+'\n');return ref(release)
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--out',required=True);a.add_argument('--python',required=True);a.add_argument('--probe-dir',required=True);a.add_argument('--package',required=True);a.add_argument('--root',required=True);a.add_argument('--allow-local-adhoc-review',action='store_true');v=a.parse_args();print(json.dumps(build(v.out,v.python,v.probe_dir,v.allow_local_adhoc_review,v.package,v.root)))
if __name__=='__main__':main()
