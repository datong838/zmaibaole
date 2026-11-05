#!/usr/bin/env python3
"""Offline verification of a normal-review capture; never captures/replays UI."""
import argparse,json
from pathlib import Path
import review_capture as rc
HISTORICAL_REVIEW_VERSIONS=('dom-only-20261021-10','dom-only-20261021-11')

def verify(path):
    value=rc.load(path)
    if value.get('kind')=='normal-review-region-registration-v1':
        import review_region_capture
        return review_region_capture.verify(path)
    rc.require(value.get('kind')=='normal-review-viewport-registration-v1' and value.get('state')=='complete','review-registration-incomplete')
    command=rc.command_from_inputs(*(value[k] for k in ('job','source','envelope','profile','page')),value['review_keys'])
    before=rc.proof_response({'ok':True,'result':value['proof_before']},command,versions=HISTORICAL_REVIEW_VERSIONS)
    after=rc.proof_response({'ok':True,'result':value['proof_after']},command,versions=HISTORICAL_REVIEW_VERSIONS);rc.require(before==after,'review-registration-proof-pair-changed')
    metadata=rc.document(value['capture_metadata']);capture_command={'op':'capture-visible',**{k:command[k] for k in ('tabId','windowId','groupid')},'captureKey':value['capture_key']}
    backend=value.get('capture_backend','chrome-active-tab');rc.require(backend in ('chrome-active-tab','screen-capture-kit'),'review-registration-backend-invalid')
    if backend=='screen-capture-kit':
        import native_window_capture as nw
        native_command={'backend':backend,'pid':value['native_pid'],**{k:command[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':value['capture_key']}
        image=nw.validate(metadata,native_command,value['image']['path']);rc.require({k:metadata['before']['scope'].get(k) for k in ('tabId','windowId','groupid')}==before['scope'] and metadata['before']['scope']['url']==before['url'],'review-native-proof-scope-mismatch')
        captured_at=metadata['captured_at'];rc.require(value.get('whole_window') is True and value.get('viewport_only') is False,'review-native-whole-window-required')
    else:
        image=rc.validate_capture(metadata,capture_command,value['image']['path'],before,versions=HISTORICAL_REVIEW_VERSIONS);captured_at=metadata['capture']['observedAt'];rc.require(value.get('whole_window',False) is False and value.get('viewport_only') is True,'review-active-tab-viewport-required')
    when=rc.authority.stamp;source=rc.document(value['source']);rc.require(when(source['observed_at'])<=when(value['proof_before_observed_at'])<=when(metadata['intent_at'])<=when(captured_at)<=when(value['proof_after_observed_at'])<=when(value['recorded_at']),'review-registration-time-order-invalid')
    rc.require(image==value['image'],'review-registration-image-changed')
    rc.require(value.get('occlusion_verified') is False and value['text_complete_in_image']=={r['review_key']:r['text_complete_in_image'] for r in before['reviews']},'review-registration-derived-flags-changed')
    return {'ok':True,'review_keys':value['review_keys'],'image':image,'text_complete_in_image':value['text_complete_in_image'],'occlusion_verified':False,'capture_backend':backend,'whole_window':backend=='screen-capture-kit','viewport_only':backend=='chrome-active-tab'}
def validate(path,*,source_sha256,review_key):
    result=verify(path);value=rc.load(path)
    rc.require(value['source']['sha256']==source_sha256 and review_key in result['review_keys'],'review-registration-current-source-key-mismatch')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registration',required=True);a=p.parse_args();print(json.dumps(verify(a.registration),ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
