#!/usr/bin/env python3
"""Permission-only child. No workflow, daemon, RPC, screenshot or authorization request."""
import argparse, ctypes, hashlib, json, os, stat, sys
from pathlib import Path

def probe_file(path, expected):
    p=Path(path)
    if not p.is_absolute() or p.parent != Path.home()/'Downloads' or p.name != expected:
        return {'readable':False,'error':'pinned-download-path-required'}
    fd=None
    try:
        fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
        s=os.fstat(fd)
        if not stat.S_ISREG(s.st_mode):raise ValueError('regular-file-required')
        digest=hashlib.sha256();count=0
        while True:
            b=os.read(fd,65536)
            if not b:break
            digest.update(b);count+=len(b)
        after=os.fstat(fd)
        stable=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
        return {'readable':stable,'regular_file':True,'size':s.st_size,'bytes_read':count,'sha256':digest.hexdigest(),'unchanged_during_read':stable}
    except OSError as e:return {'readable':False,'errno':e.errno,'error':'download-file-read-denied-or-unavailable'}
    except ValueError as e:return {'readable':False,'error':str(e)}
    finally:
        if fd is not None:os.close(fd)

def public_permissions():
    ax=ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
    cg=ctypes.CDLL('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
    ax.AXIsProcessTrusted.argtypes=[];ax.AXIsProcessTrusted.restype=ctypes.c_bool
    cg.CGPreflightScreenCaptureAccess.argtypes=[];cg.CGPreflightScreenCaptureAccess.restype=ctypes.c_bool
    return {'accessibility':bool(ax.AXIsProcessTrusted()),'screen_capture':bool(cg.CGPreflightScreenCaptureAccess())}

def run(c, expected_parent, permissions=public_permissions, file_probe=probe_file):
    parent=os.getppid()
    if parent!=expected_parent:return {'kind':'workshop-child-permission-probe-v1','ok':False,'error':'host-parent-mismatch','pid':os.getpid(),'ppid':parent}
    try:p=permissions()
    except Exception as e:p={'accessibility':False,'screen_capture':False,'error':type(e).__name__}
    download=file_probe(c['probe_file'],c['probe_filename'])
    download['matches_published_export']=download.get('sha256')==c['probe_sha256'] and download.get('size')==c['probe_size']
    return {'kind':'workshop-child-permission-probe-v1','ok':p.get('accessibility') is True and p.get('screen_capture') is True and download.get('readable') is True and download.get('matches_published_export') is True,'pid':os.getpid(),'ppid':parent,'host_parent_verified':True,'permissions':p,'download':download,'business_executed':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--config',required=True);ap.add_argument('--host-pid',required=True,type=int);a=ap.parse_args()
    c=json.loads(Path(a.config).read_text());r=run(c,a.host_pid);print(json.dumps(r));return 0 if r['ok'] else 2
if __name__=='__main__':sys.exit(main())
