#!/usr/bin/env python3
"""Candidate single review-region entry: typed overlay preflight then fresh capture.
Existing region operations keep their original lock/key/receipt and no UI replay.
"""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
if __name__=='__main__':
    sys.path.insert(0,str(PROJECT/'skills/negative-review-complaints/scripts'))
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,fcntl,json,re
import account_overlay_preflight as overlay
region=overlay.region
rc=region.rc

def capture(manifest_ref,outdir,*,pid,revision,replaces=None,adopt=None,request=None,native=None,ax=None):
    manifest=overlay.document(manifest_ref)
    rc.require(set(manifest)=={'job','source','envelope','profile','page','review_keys','capture_key'},'review-manifest-fields-invalid')
    rc.require(type(pid) is int and pid>0,'review-native-pid-required')
    rc.require(isinstance(revision,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',revision) is not None,'review-region-explicit-revision-required')
    rc.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',manifest['capture_key']) is not None,'review-stable-capture-key-required')
    # Exactly the existing pure source/profile/tuple contract, no shortcut flags.
    overlay.derive(manifest)
    if replaces is not None:overlay.document(replaces)
    outdir=Path(outdir).resolve();source=overlay.canonical(manifest['source']['path']);states=source.parent/'.review-region-state';states.mkdir(exist_ok=True)
    key=rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});state=states/(key+'.json')
    operation={'kind':'normal-review-region-capture-v1','manifest':manifest,'outdir':str(outdir),'pid':pid,'revision':revision,'replaces':replaces}
    request=request or (lambda command:overlay.bridge.request(command,timeout=50))
    # Hold the ORIGINAL capture lock while inspecting and doing any overlay input.
    # Release before region.capture reacquires it; its own operation/unknown guard
    # is authoritative if another caller wins the boundary race after release.
    with (states/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if state.exists():
            rc.require(adopt is None,'review-overlay-adoption-only-new-capture')
            old=rc.load(state);rc.require(old.get('operation')==operation,'review-region-original-operation-required')
            # A single reviewed pre-native failure has no screenshot intent.
            # Its old state/files stay in place; the fresh observations use a typed branch.
            if old.get('pre_native_authorization'):
                import review_capture_focus
                review_capture_focus.panel_capture_state(old['pre_native_authorization'],operation)
                child=outdir/'capture-v2/pre-native-continuation-v1/state.json'
                if not child.exists():
                    review_capture_focus.ensure(manifest_ref,activation_ref=overlay.ref(review_capture_focus.activation_path(manifest)),pid=pid,request=request,pre_native_authorization=old['pre_native_authorization'])
            # Every other unknown remains unchanged and cannot read or recapture.
        else:
            region.legacy_gate(manifest,replaces)
            overlay.no_capture_unknown(source)
            import review_capture_tab
            review_capture_tab.ensure(manifest_ref,request=request,pid=pid)
            overlay.ensure(manifest_ref,request=request,adopt=adopt)
            rc.require(overlay.document(manifest_ref)==manifest,'review-overlay-wrapper-manifest-changed')
    return region.capture(manifest,outdir,request,pid=pid,revision=revision,replaces=replaces,native=native,ax=ax)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','manifest-sha256','outdir','revision'):p.add_argument('--'+name,required=True)
    p.add_argument('--pid',required=True,type=int)
    for name in ('replaces-registration','replaces-sha256','adopt-intent','adopt-intent-sha256'):p.add_argument('--'+name)
    a=p.parse_args()
    rc.require(bool(a.replaces_registration)==bool(a.replaces_sha256),'review-region-parent-path-and-hash-required')
    rc.require(bool(a.adopt_intent)==bool(a.adopt_intent_sha256),'overlay-adoption-paired-ref-required')
    replaces={'path':a.replaces_registration,'sha256':a.replaces_sha256} if a.replaces_registration else None
    adopt={'path':a.adopt_intent,'sha256':a.adopt_intent_sha256} if a.adopt_intent else None
    value=capture({'path':a.manifest,'sha256':a.manifest_sha256},a.outdir,pid=a.pid,revision=a.revision,replaces=replaces,adopt=adopt)
    print(json.dumps({'ok':True,'state':value['state'],'registration':str(Path(a.outdir).resolve()/('preview-registration.json' if value['state']=='awaiting-visual-review' else 'registration.json')),'image':value['image'],'image_scope':value['image_scope']},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as exc:print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False));raise SystemExit(2)
