#!/usr/bin/env python3
"""Violation DOM region evidence. Reuses shared AX/CG/SCK original-pixel crop.
No UI input, guessed offsets, AI imagery or raw-window final notifications.
"""
import argparse,fcntl,json,re,sys,hashlib
# Keep helper imports on this exact module before a pure code graph is frozen.
if __name__=='__main__':
    if sys.modules.get('region_frame_capture',sys.modules[__name__]) is not sys.modules[__name__]:raise ValueError('region-cli-module-identity-conflict')
    sys.modules['region_frame_capture']=sys.modules[__name__]
import registration_validation as validation
import region_postguard_retake as postguard
import program_region_quality
import program_object_ellipsis_quality
import program_core_region_quality
import program_epoch_rows_quality
import rows_character_range_quality
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import frame_capture as fc
import screenshot_registration as sr
import native_window_capture as nw
import native_region_capture as region
import native_frame_capture as historical
import business_cells_capture as business
from visible_capture import atomic,sha,stamp,SAFETY
BACKEND='screen-capture-kit-dom-region';POLICY=fc.POLICY;need=fc.need
ref=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
def is_business(inputs):return inputs.get('evidence_contract')==business.CONTRACT
def policy(inputs):return business.CONTRACT if is_business(inputs) else POLICY
def region_request(inputs,base,mode,notice_ids=None):return business.prepare_region_request(inputs,base,mode,notice_ids=notice_ids) if is_business(inputs) else historical.prepare_region_request(inputs,base,mode)
def frame_facts(proof,inputs):return business.facts(proof,inputs) if is_business(inputs) else sr.visible_facts(proof['base_proof'])
def metadata_inputs(m):
 b=m['pinned_inputs'];return fc.page_inputs({'path':b['source_path'],'sha256':b['source_sha256']},{'path':b['observation_path'],'sha256':b['observation_sha256']},{'path':b['profile_path'],'sha256':b['profile_sha256']},screenshot_anchor=b.get('screenshot_anchor'))
def checked(reply,command,inputs):
    need(reply.get('ok') is True,'violation-region-proof-failed:'+str(reply.get('error')));p=reply['result']
    need(p.get('method')=='public-DOM-evidence-region-proof' and p.get('geometry_purpose')=='evidence-crop-only' and p.get('pixel_input_actions') is False and (p.get('external_painted_overlap') is False or (p.get('external_painted_overlap')=='unresolved' and p.get('quality_review_required') is True and (bool(p.get('unresolved_overlay')) or p.get('region_build') in ('region-notice-business-cells-v11-manual-neighbor-preview-v2','region-notice-business-cells-v12-manual-date-fragment-v2') and p.get('evidence_contract')==business.CONTRACT and p.get('manual_preview_unresolved') is True and bool(p.get('unresolved_source_neighbor_overlap'))))) and p.get('safety_version')==SAFETY,'violation-region-proof-method-version-invalid')
    if is_business(inputs):business.validate_base(p['base_proof'],inputs);business.facts(p,inputs,command['selectors'])
    else:sr.validate_public_proof(p['base_proof'],inputs['command'],inputs['url'])
    need(p['base_proof']['safety_version']==p['safety_version'] and p.get('scope')==p['base_proof']['scope'] and p.get('url')==inputs['url'] and p.get('selectors')==command['selectors'],'violation-region-base-scope-invalid');return p

def record_region_reply(outdir,stage,operation,command,reply):
    """Keep the actual public reply before validation can reject it.

    This audit is neither a capture intent nor proof of success. Content-named
    files retain failures at the original operation without overwriting them.
    """
    need(stage in ('base','before','after'),'violation-region-reply-stage-invalid')
    value={'kind':'public-region-proof-transport-reply-v1','stage':stage,
           'recorded_at':stamp(),'operation':operation,'command':command,'reply':reply}
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    path=Path(outdir)/'proof-replies'/(stage+'-'+hashlib.sha256(raw).hexdigest()+'.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(json.loads(path.read_text())==value,'violation-region-reply-audit-conflict')
    else:atomic(path,value)
    return reply

def legacy_gate(source,profile,replaces):
    if replaces is None:return
    manifest=sr.document(replaces);src=sr.document(source)
    historical.validate_chain(manifest,source=source,company=src['company'],groupid=src['groupid'],start=src['start'],end_exclusive=src['end_exclusive'],notice_ids=[r['notice_id']for r in src['records']['rows']])


def selection_ids(selection,inputs,source,chain_id,*,profile_sha256,base,before_at=None):
    with validation.pure_scope(sys.modules[__name__]):
        return _selection_ids_uncached(selection,inputs,source,chain_id,profile_sha256=profile_sha256,base=base,before_at=before_at)

def _selection_ids_uncached(selection,inputs,source,chain_id,*,profile_sha256,base,before_at=None):
    """Verify immutable earlier approved frames, never mutable coverage counters."""
    need(is_business(inputs) and isinstance(selection,dict) and set(selection)=={'schema','source','profile_sha256','chain_id','prior_frames','prior_chain','covered_notice_ids','selected_notice_ids'},'violation-uncovered-selection-contract-invalid')
    need(selection['schema']=='verified-uncovered-original-notices-v1' and selection['profile_sha256']==profile_sha256 and selection['chain_id']==chain_id,'violation-uncovered-selection-scope-invalid')
    original_source=selection['source']
    need(isinstance(original_source,dict) and isinstance(source,dict) and original_source.get('sha256')==source.get('sha256'),'violation-uncovered-selection-scope-invalid')
    original_document=sr.document(original_source);current_document=sr.document(source)
    original_bytes=Path(original_source['path']).read_bytes();current_bytes=Path(source['path']).read_bytes()
    need(original_bytes==current_bytes and hashlib.sha256(original_bytes).hexdigest()==source['sha256'] and original_document==current_document,'violation-uncovered-selection-scope-invalid')
    # The immutable original source anchors its canonical capture journal; an
    # evidence copy never invents a new journal or bypasses its current prefix.
    _selection_prefix(selection,original_source,profile_sha256)
    refs=selection['prior_frames'];need(isinstance(refs,list) and 1<=len(refs)<=100 and len({r['path'] for r in refs})==len(refs),'violation-uncovered-prior-frames-invalid');covered=set()
    allids=[r['notice_id'] for r in sr.document(source)['records']['rows']];claimed=selection['covered_notice_ids'];ids=selection['selected_notice_ids']
    need(isinstance(claimed,list) and claimed==[i for i in allids if i in claimed] and len(claimed)==len(set(claimed)),'violation-uncovered-covered-ids-not-derived')
    need(isinstance(ids,list) and bool(ids) and ids==[r['notice_id'] for r in business.selectable_rows(base) if r['notice_id'] not in claimed] and len(ids)==len(set(ids)),'violation-uncovered-selected-ids-invalid')
    # Reject malformed selections cheaply; no successful selection trusts claimed
    # coverage until all approved prior frames below derive the exact same set.
    for frame_ref in refs:
        m=sr.document(frame_ref);need(m.get('state')=='complete' and m.get('chain_id')==chain_id and m.get('visibility_policy')==business.CONTRACT and m['pinned_inputs']['profile_sha256']==selection['profile_sha256'],'violation-uncovered-prior-frame-scope-invalid')
        if before_at is not None:need(sr.when(m['recorded_at'])<sr.when(before_at),'violation-uncovered-prior-frame-not-earlier')
        need(m.get('source_sha256')==source['sha256'] and isinstance(m.get('notice_ids'),list),'violation-uncovered-approved-current-source');covered.update(m['notice_ids'])
    need(claimed==[i for i in allids if i in covered] and covered<=set(allids),'violation-uncovered-covered-ids-not-derived');return ids

def make_uncovered_selection(state,inputs,base,source,profile,chain_id,outdir):
    need(is_business(inputs),'violation-uncovered-business-only');refs=[e['registration'] for e in state['frames']];covered=set()
    for reference in refs:
        # Current approved registrations already bind their derived coverage.
        # Final chain validation checks each image once, without recursive replay.
        m=sr.document(reference);covered.update(m.get('notice_ids',[]))
    allids=[r['notice_id'] for r in sr.document(source)['records']['rows']];ids=[r['notice_id'] for r in business.selectable_rows(base) if r['notice_id'] not in covered]
    need(ids,'violation-uncovered-no-eligible-five-cell-group-see-base-proof-replies')
    snapshot=Path(outdir)/'uncovered-chain-before.json'
    if snapshot.exists():need(sr.document(ref(snapshot))==state,'violation-uncovered-chain-snapshot-conflict')
    else:atomic(snapshot,state)
    selection={'schema':'verified-uncovered-original-notices-v1','source':source,'profile_sha256':profile['sha256'],'chain_id':chain_id,'prior_frames':refs,'prior_chain':ref(snapshot),'covered_notice_ids':[i for i in allids if i in covered],'selected_notice_ids':ids}
    selection_ids(selection,inputs,source,chain_id,profile_sha256=profile['sha256'],base=base);return selection

def _selection_prefix(selection,source,profile_sha256):
    snapshot=sr.document(selection['prior_chain']);expected_scope={'source_sha256':source['sha256'],'profile_sha256':profile_sha256,'chain_id':selection['chain_id']}
    need(snapshot.get('scope')==expected_scope and isinstance(snapshot.get('frames'),list) and all(e.get('state')=='complete' for e in snapshot['frames']),'violation-uncovered-prior-chain-invalid')
    canonical=Path(source['path']).resolve().parent/'.native-region-frame-state'/(fc.fingerprint([source['sha256'],selection['chain_id']])+'.json');current=sr.document(ref(canonical))
    need(current.get('scope')==expected_scope and current['frames'][:len(snapshot['frames'])]==snapshot['frames'],'violation-uncovered-original-chain-prefix-changed')
    need(selection['prior_frames']==[e['registration'] for e in snapshot['frames']],'violation-uncovered-prior-chain-frames-changed')
    return snapshot

def validate_frame(image,m,*,source,allow_preview=False):
    with validation.pure_scope(sys.modules[__name__]):
        return _validate_frame_uncached(image,m,source=source,allow_preview=allow_preview)

def _validate_frame_uncached(image,m,*,source,allow_preview=False):
    need(m.get('state','complete') in (('complete','awaiting-visual-review') if allow_preview else ('complete',)),'violation-region-quality-approval-required')
    b=m.get('pinned_inputs',{});need(m.get('capture_backend')==BACKEND and m.get('whole_window') is False and m.get('region_only') is True and m.get('visibility_policy') in (POLICY,business.CONTRACT) and m.get('frame_mode') in ('anchor','rows'),'violation-region-only-metadata-required');need(b.get('source_sha256')==source['sha256'] and m.get('source_sha256')==source['sha256'],'violation-region-source-conflict')
    src={'path':b.get('source_path'),'sha256':b.get('source_sha256')};obs={'path':b.get('observation_path'),'sha256':b.get('observation_sha256')};profile={'path':b.get('profile_path'),'sha256':b.get('profile_sha256')};need(sr.document(src)==sr.document(source),'violation-region-batch-source-conflict');inputs=fc.page_inputs(src,obs,profile,screenshot_anchor=b.get('screenshot_anchor'));need(m['visibility_policy']==policy(inputs),'violation-region-profile-policy-conflict');need(b.get('command')==inputs['command'] and m.get('page_scope')==inputs['scope'] and m.get('page_fingerprint')==b.get('page_fingerprint')==inputs['page_fingerprint'] and m.get('query_fingerprint')==b.get('query_fingerprint')==inputs['query_fingerprint'] and m.get('chain_id')==b.get('chain_id') and m.get('frame_mode')==b.get('frame_mode'),'violation-region-query-not-derived')
    selection=b.get('uncovered_selection');ids=selection_ids(selection,inputs,source,m['chain_id'],profile_sha256=profile['sha256'],base=m['public_dom_proof']['before']['base_proof'],before_at=m['proof_before_observed_at']) if selection is not None else None
    command=region_request(inputs,m['public_dom_proof']['before']['base_proof'],m['frame_mode'],ids);need(command==b.get('region_command'),'violation-region-selectors-not-derived');before=checked({'ok':True,'result':m['public_dom_proof']['before']},command,inputs);after=checked({'ok':True,'result':m['public_dom_proof']['after']},command,inputs);postguard.verify_pair(m,business=is_business(inputs))
    facts=frame_facts(before,inputs)
    if is_business(inputs):need(m.get('occlusion_verified') is False and m.get('quality_review_required')==bool(before.get('quality_review_required') or m.get('postguard_consistency') or b.get('retake_authorization')),'business-region-quality-or-occlusion-not-derived')
    need(all(m.get(k)==v for k,v in facts.items()),'violation-region-visible-facts-not-derived');meta=sr.document(m['capture_metadata']);native=historical.native_command(inputs,m['native_pid'],b['captureKey']);need(native==b.get('native_command'),'violation-region-native-command-conflict');nw.validate(meta,native,m['derivation']['source']['path']);need(meta['before']['scope']==m['geometry_before']['scope'] and meta['before']['window']==m['geometry_before']['window'],'violation-region-native-scope-map-mismatch')
    output=region.validate(m['derivation'],before,m['geometry_before']);need(output==m['image'] and Path(image).is_absolute() and sha(image)==output['sha256']==m['sha256'] and m['derivation']['source']['sha256']==meta['png']['sha256'],'violation-region-derived-png-mismatch');need(m.get('revision') and b['captureKey'].endswith(':region:'+m['revision']),'violation-region-explicit-revision-invalid')
    need(sr.when(m['proof_before_observed_at'])<=sr.when(meta['intent_at'])<=sr.when(meta['captured_at'])<=sr.when(meta['completed_at'])<=sr.when(m['proof_after_observed_at'])<=sr.when(m['recorded_at']),'violation-region-time-chain-invalid')
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',m['revision']) is not None,'violation-region-revision-format-invalid')
    if m.get('replaces_manifest') is not None:
        parent=sr.document(m['replaces_manifest']);original=sr.document(source);historical.validate_chain(parent,source=source,company=original['company'],groupid=original['groupid'],start=original['start'],end_exclusive=original['end_exclusive'],notice_ids=[r['notice_id'] for r in original['records']['rows']])
    refs=[src,obs,profile,m['capture_metadata'],m['derivation']['source'],m['derivation']['image']]
    if selection is not None:refs.extend([selection['prior_chain'],*selection['prior_frames']])
    if b.get('screenshot_anchor') is not None:
        import screenshot_identity as identity
        anchor=identity.validate(b['screenshot_anchor'],src,profile,chain_id=m['chain_id'],pid=m['native_pid']);refs.extend([b['screenshot_anchor'],*[anchor[k] for k in ('full_identity_observation','job','query','identity_receipt')]])
    if m.get('postguard_audit'):
        refs.extend([m['postguard_audit'],sr.document(m['postguard_audit'])['after_geometry']])
    if b.get('retake_authorization'):refs.extend(postguard.validate_registration(m))
    pixel_facts=None
    if m.get('quality_review_required') and m.get('state')=='complete':
        attestation=validate_attestation(m,source);refs.extend([m['quality_attestation'],sr.document(m['quality_attestation'])['registration_preview']])
        if attestation.get('kind')==program_object_ellipsis_quality.PIXEL_EXCERPT_KIND:
            pixel_facts=attestation['pixel_facts'];refs.append(attestation['review'])
    need(not m.get('quality_review_required') or m.get('state') in ('awaiting-visual-review','complete'),'violation-region-quality-state-required')
    # Image refs carry dimensions; only file/hash are needed in workflow snapshots.
    refs=[{'path':r['path'],'sha256':r['sha256']} for r in refs]
    for r in refs:need(sha(r['path'])==r['sha256'],'violation-region-nested-reference-changed')
    return {'notice_ids':facts['notice_ids'],'version':before['safety_version'],'observed_at':meta['captured_at'],'capture_scope':meta['before']['scope'],'window_scope':meta['before']['window'],'references':refs,'whole_window':False,'region_only':True,'viewport_only':False,**({'effective_pixel_visibility':pixel_facts,'original_DOM_completeness_is_not_pixel_certification':True}if pixel_facts is not None else {})}

def capture_revision(profile,revision=None):
    # Explicit invalid values fail before any profile read or other work.
    if revision is not None:
        need(isinstance(revision,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',revision) is not None,'violation-region-explicit-revision-required')
        return revision
    contract=sr.document(profile).get('projection_contract')
    need(contract in (None,business.gp.RECTIFICATION_CONTRACT),'violation-region-profile-projection-unreviewed')
    return 'rectification-v3' if contract is not None else 'region-v1'

def capture(source,observation,profile,*,pid,mode,chain_id,key,outdir,revision=None,replaces=None,uncovered_only=False,screenshot_anchor=None,request=None,native=None,ax=None,retake_authorization=None):
    revision=capture_revision(profile,revision)
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',revision or '') is not None,'violation-region-explicit-revision-required');need(re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id or '') is not None,'violation-region-chain-id-invalid');inputs=fc.page_inputs(source,observation,profile,screenshot_anchor=screenshot_anchor);request=request or fc.vc.bridge.request;outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True);folder=Path(source['path']).resolve().parent/'.native-region-frame-state';folder.mkdir(exist_ok=True);file=folder/(fc.fingerprint([source['sha256'],chain_id])+'.json');scope={'source_sha256':source['sha256'],'profile_sha256':profile['sha256'],'chain_id':chain_id};operation={'source':source,'observation':observation,'profile':profile,'pid':pid,'mode':mode,'key':key,'outdir':str(outdir),'revision':revision,'replaces':replaces}
    need(type(uncovered_only) is bool and (not uncovered_only or mode=='rows' and is_business(inputs)),'violation-uncovered-rows-business-only')
    if uncovered_only:operation['uncovered_only']=True
    if screenshot_anchor is not None:
        import screenshot_identity as identity
        identity.validate(screenshot_anchor,source,profile,chain_id=chain_id,pid=pid);operation['screenshot_anchor']=screenshot_anchor
    transport=request
    def audited_request(command):
        reply=transport(command)
        if command.get('op')=='viewport-proof':
            record_region_reply(attempt_dir,'base',{**operation,'chain_id':chain_id},command,reply)
        return reply
    request=audited_request
    with file.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads(file.read_text()) if file.exists() else {'scope':scope,'frames':[]};need(state.get('scope')==scope,'violation-region-original-chain-scope-required')
        old=[e for e in state['frames'] if e['operation']['key']==key or e['operation']['outdir']==str(outdir)]
        attempt_dir=outdir;retake=None
        if old:
            entry=old[0];need(len(old)==1 and entry['operation']==operation,'violation-region-original-operation-required')
            if entry['state'] in ('complete','awaiting-visual-review'):
                if retake_authorization is not None:need(entry.get('retake_attempt',{}).get('authorization')==retake_authorization,'violation-region-original-retake-authorization-required')
                m=sr.document(entry['registration']);validate_frame(m['image']['path'],m,source=source,allow_preview=True);return {'image':m['image']['path'],'metadata':entry['registration']['path'],'state':entry['state'],'reused':True}
            need(retake_authorization is not None and not entry.get('retake_attempt'),'violation-region-unknown-no-recapture')
            entry,attempt_dir,retake_key=postguard.begin(retake_authorization,state,file,operation);retake=entry['retake_attempt'];atomic(file,state)
        else:need(retake_authorization is None,'violation-region-retake-requires-original-unknown')
        need(all(e is entry or e['state']=='complete' for e in state['frames']) if retake is not None else all(e['state']=='complete' for e in state['frames']),'violation-region-prior-unknown-no-new-key')
        for sibling in folder.glob('*.json'):
            previous=sr.document(ref(sibling))
            if previous.get('scope',{}).get('source_sha256')==source['sha256']:need((sibling==file and retake is not None) or all(e.get('state')=='complete' for e in previous.get('frames',[])),'violation-region-source-has-unknown-no-new-chain')
        legacy_gate(source,profile,replaces)
        if is_business(inputs):
            if retake is not None:postguard.no_other_unknown(source,file,state)
            else:business.no_unknown_other_capture(source,chain_id)
            business.no_unresolved_navigation(source,profile)
        # Pure source proof and geometry checks precede the durable raw-capture intent.
        base=business.request_base(inputs,request) if is_business(inputs) else fc.proof(inputs['command'],inputs['url'],request);selection=make_uncovered_selection(state,inputs,base,source,profile,chain_id,outdir) if uncovered_only else None;command=region_request(inputs,base,mode,selection['selected_notice_ids'] if selection else None);before=checked(record_region_reply(attempt_dir,'before',{**operation,'chain_id':chain_id},command,request(command)),command,inputs);before_at=stamp();need(not is_business(inputs)or before['base_proof'].get('diagnostic_build')==base.get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1','violation-live-before-producer-generation');capture_key=retake_key if retake is not None else key+':region:'+revision;need(len(capture_key)<=128,'violation-region-key-too-long');cap=historical.native_command(inputs,pid,capture_key);geometry=region.observe(cap,request,native,ax)
        if retake is None:
            entry={'state':'unknown','operation':operation,'intent_at':stamp(),'before':before,'geometry_before':geometry};state['frames'].append(entry)
        else:entry.update(intent_at=stamp(),before=before,geometry_before=geometry)
        atomic(file,state)
        raw=nw.write_capture(cap,attempt_dir/'raw-window.png',request,native);entry['raw_capture_metadata']=ref(raw['result']['metadata']);atomic(file,state)
        after=checked(record_region_reply(attempt_dir,'after',{**operation,'chain_id':chain_id},command,request(command)),command,inputs);after_at=stamp();need(not is_business(inputs)or after['base_proof'].get('diagnostic_build')==before['base_proof'].get('diagnostic_build')=='viewport-notice-business-cells-v13-fractional-auto-padding-v1','violation-live-after-producer-generation')
        try:after_geometry=region.observe(cap,request,native,ax)
        except Exception as error:
            entry['after_geometry_failure']=postguard.publish(attempt_dir/'after-geometry-failure.json',{'kind':'postcapture-native-geometry-unavailable-v1','operation':operation,'error':str(error),'observed_at':stamp()});atomic(file,state);raise
        audit=postguard.write_after(attempt_dir,operation,cap,before,after,geometry,after_geometry,ref(raw['result']['metadata']),before_at,after_at,stamp());entry['postguard_audit']=audit;atomic(file,state)
        consistency=postguard.compare(before,after,geometry,after_geometry,business=is_business(inputs));crop=region.derive(raw['result']['path'],before,geometry,attempt_dir/'list-region.png')
        b={'source_path':source['path'],'source_sha256':source['sha256'],'observation_path':observation['path'],'observation_sha256':observation['sha256'],'profile_path':profile['path'],'profile_sha256':profile['sha256'],'command':inputs['command'],'region_command':command,'native_command':cap,'captureKey':capture_key,'chain_id':chain_id,'frame_mode':mode,'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint']}
        if selection is not None:b['uncovered_selection']=selection
        if screenshot_anchor is not None:b['screenshot_anchor']=screenshot_anchor
        m={'quality_review_required':bool(before.get('quality_review_required') or consistency or retake),'occlusion_verified':False,'state':'awaiting-visual-review' if before.get('quality_review_required') or consistency or retake else 'complete','source':'local-dom-bridge','source_sha256':source['sha256'],'capture_backend':BACKEND,'visibility_policy':policy(inputs),'whole_window':False,'region_only':True,'viewport_only':False,'frame_mode':mode,'chain_id':chain_id,'revision':revision,'replaces_manifest':replaces,'native_pid':pid,'pinned_inputs':b,'page_scope':inputs['scope'],'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint'],'public_dom_proof':{'before':before,'after':after},'proof_before_observed_at':before_at,'proof_after_observed_at':after_at,'geometry_before':geometry,'geometry_after':after_geometry,'capture_metadata':ref(raw['result']['metadata']),'derivation':crop,'image':crop['image'],'sha256':crop['image']['sha256'],'recorded_at':stamp(),**frame_facts(before,inputs)}
        if is_business(inputs):m['postguard_audit']=audit
        if consistency is not None:m['postguard_consistency']=consistency
        if retake is not None:m['pinned_inputs'].update(retake_authorization=retake_authorization,retake_plan=retake['plan'],original_operation_key=key)
        path=attempt_dir/('preview-registration.json' if m['state']=='awaiting-visual-review' else 'region-frame.json');need(not path.exists(),'violation-region-registration-exists');validate_frame(crop['image']['path'],m,source=source,allow_preview=True);atomic(path,m);entry.update(state=m['state'],registration=ref(path))
        if retake is not None:entry['retake_attempt'].update(state='preview-complete' if m['state']=='awaiting-visual-review' else 'complete',registration=ref(path),raw_capture_metadata=m['capture_metadata'],**({'preview_completed_at':stamp()} if m['state']=='awaiting-visual-review' else {'completed_at':stamp()}))
        atomic(file,state);return {'image':crop['image']['path'],'metadata':str(path),'state':m['state'],'region_only':True,'whole_window':False,'business_progress_changed':False}

def finalize_current_raw(source,chain_id,key):
    """Finish the current completed raw capture without any live API or recapture."""
    source= {k:source[k] for k in ('path','sha256')}
    file=Path(source['path']).parent/'.native-region-frame-state'/(fc.fingerprint([source['sha256'],chain_id])+'.json')
    with file.with_suffix('.lock').open('a')as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);state=sr.document(ref(file))
        need_one=[e for e in state['frames']if e['operation']['key']==key]
        need(len(need_one)==1,'current-raw-original-operation-required');entry=need_one[0];op=entry['operation']
        need(state['scope']=={'source_sha256':source['sha256'],'profile_sha256':op['profile']['sha256'],'chain_id':chain_id}and op['source']==source,'current-raw-original-scope')
        need(entry['state']=='unknown'and entry.get('postguard_audit')and entry.get('raw_capture_metadata')and not entry.get('after_geometry_failure')and not entry.get('retake_attempt'),'current-raw-completed-audit-required')
        need(all(e is entry or e['state']=='complete'for e in state['frames']),'current-raw-other-capture-unresolved')
        audit=sr.document(entry['postguard_audit']);raw=sr.document(entry['raw_capture_metadata']);out=Path(op['outdir'])
        need(audit['operation']==op and audit['capture_metadata']==entry['raw_capture_metadata']and audit['before']==entry['before']and audit['geometry_before']==entry['geometry_before'],'current-raw-audit-binding')
        cap=audit['native_command'];rawpath=raw['png']['path'];nw.validate(raw,cap,rawpath)
        before,after=audit['before'],audit['after'];geometry,after_geometry=audit['geometry_before'],audit['geometry_after']
        consistency=postguard.compare(before,after,geometry,after_geometry,business=True)
        inputs=fc.page_inputs(source,op['observation'],op['profile'],screenshot_anchor=op.get('screenshot_anchor'))
        need(op.get('uncovered_only')is True and op['mode']=='rows'and is_business(inputs),'current-raw-business-rows-only')
        snapshot=sr.document(ref(out/'uncovered-chain-before.json'))
        selection=make_uncovered_selection(snapshot,inputs,before['base_proof'],source,op['profile'],chain_id,out)
        command=region_request(inputs,before['base_proof'],'rows',selection['selected_notice_ids']);checked({'ok':True,'result':before},command,inputs);checked({'ok':True,'result':after},command,inputs)
        crop=region.derive(rawpath,before,geometry,out/'list-region.png')
        b={k+'_path':op[k]['path']for k in('source','observation','profile')};b.update({k+'_sha256':op[k]['sha256']for k in('source','observation','profile')})
        b.update(command=inputs['command'],region_command=command,native_command=cap,captureKey=cap['captureKey'],chain_id=chain_id,frame_mode='rows',page_fingerprint=inputs['page_fingerprint'],query_fingerprint=inputs['query_fingerprint'],uncovered_selection=selection)
        if op.get('screenshot_anchor'):b['screenshot_anchor']=op['screenshot_anchor']
        m={'quality_review_required':True,'occlusion_verified':False,'state':'awaiting-visual-review','source':'local-dom-bridge','source_sha256':source['sha256'],'capture_backend':BACKEND,'visibility_policy':policy(inputs),'whole_window':False,'region_only':True,'viewport_only':False,'frame_mode':'rows','chain_id':chain_id,'revision':op['revision'],'replaces_manifest':op['replaces'],'native_pid':op['pid'],'pinned_inputs':b,'page_scope':inputs['scope'],'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint'],'public_dom_proof':{'before':before,'after':after},'proof_before_observed_at':audit['proof_before_observed_at'],'proof_after_observed_at':audit['proof_after_observed_at'],'geometry_before':geometry,'geometry_after':after_geometry,'capture_metadata':entry['raw_capture_metadata'],'derivation':crop,'image':crop['image'],'sha256':crop['image']['sha256'],'recorded_at':stamp(),'postguard_audit':entry['postguard_audit'],'postguard_consistency':consistency,**frame_facts(before,inputs)}
        path=out/'preview-registration.json';need(not path.exists(),'current-raw-preview-already-exists');validate_frame(m['image']['path'],m,source=source,allow_preview=True);atomic(path,m)
        entry.update(state='awaiting-visual-review',registration=ref(path));atomic(file,state)
        return ref(path)

def quality_binding(m):
    inputs=metadata_inputs(m);facts=frame_facts(m['public_dom_proof']['before'],inputs)
    # These facts are derived from the same normal DOM/source chain, never a caller boolean.
    return {'source_sha256':m['source_sha256'],'image':m['image'],'chain_id':m['chain_id'],'revision':m['revision'],'frame_mode':m['frame_mode'],'page_scope':m['page_scope'],'page_fingerprint':m['page_fingerprint'],'query_fingerprint':m['query_fingerprint'],'selectors':m['pinned_inputs']['region_command']['selectors'],**({'postguard_consistency':m['postguard_consistency'],'postguard_audit':m['postguard_audit']} if m.get('postguard_consistency') else {}),**({'retake_authorization':m['pinned_inputs']['retake_authorization'],'retake_plan':m['pinned_inputs']['retake_plan'],'original_operation_key':m['pinned_inputs']['original_operation_key']} if m['pinned_inputs'].get('retake_authorization') else {}),'notice_ids':facts['notice_ids'],'filters_visible':facts['filters_visible'],'list_headers_visible':facts['list_headers_visible'],**({'evidence_contract':business.CONTRACT,'cell_text_completeness':facts['cell_text_completeness']} if is_business(inputs) else {})}

def validate_attestation(m,source):
    with validation.pure_scope(sys.modules[__name__]):
        return _validate_attestation_uncached(m,source)

def _validate_attestation_uncached(m,source):
    a=sr.document(m['quality_attestation'])
    if a.get('kind') in (program_region_quality.KIND,program_core_region_quality.KIND,program_object_ellipsis_quality.KIND,program_object_ellipsis_quality.PIXEL_EXCERPT_KIND,program_epoch_rows_quality.KIND):
        b=m['pinned_inputs'];original={'path':b['source_path'],'sha256':b['source_sha256']};program_region_quality.fragment_source_binding(original,source);source=original
    if a.get('kind')==program_object_ellipsis_quality.PIXEL_EXCERPT_KIND:
        return program_object_ellipsis_quality.pixel_review_verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_epoch_rows_quality.KIND:
        return program_epoch_rows_quality.verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_region_quality.EPOCH_FRAGMENT_KIND:
        return program_region_quality.epoch_fragment_verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_region_quality.FRAGMENT_KIND:
        return program_region_quality.fragment_verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_core_region_quality.KIND:
        return program_core_region_quality.verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_object_ellipsis_quality.KIND:
        return program_object_ellipsis_quality.verify(m['quality_attestation'],m,source)
    if a.get('kind')==program_region_quality.KIND:
        return program_region_quality.verify(m['quality_attestation'],m,source)
    preview=sr.document(a['registration_preview'])
    need(a.get('kind')=='violation-frame-region-quality-attestation-v1' and a.get('reviewer_role')=='supervisor' and a.get('decision')=='approved','violation-region-quality-attestation-invalid')
    expected=dict(m);expected.pop('quality_attestation',None);expected.pop('quality_approved_at',None);expected['state']='awaiting-visual-review'
    need(preview==expected and preview.get('state')=='awaiting-visual-review' and a.get('binding')==quality_binding(m),'violation-region-quality-binding-changed')
    inputs=metadata_inputs(m);facts=frame_facts(m['public_dom_proof']['before'],inputs);expected_fields=business.expected_visibility(m['frame_mode'],facts) if is_business(inputs) else {'date_and_headers':m['frame_mode']=='anchor','rows':{i:dict.fromkeys(('reason','subject','object','effective_status','disposal'),True) for i in quality_binding(m)['notice_ids']}}
    if m.get('postguard_consistency'):expected_fields={**expected_fields,'unresolved_global_epoch_change_acknowledged':True}
    need(a.get('field_visibility')==expected_fields,'violation-region-quality-fields-not-confirmed')
    need(sr.when(m['recorded_at'])<=sr.when(a['reviewed_at'])<=sr.when(m['quality_approved_at']),'violation-region-quality-review-time-invalid')
    # Verify the immutable preview's full source/DOM/native/pixel chain again.
    validate_frame(preview['image']['path'],preview,source=source,allow_preview=True)
    return a

def approve_preview(path,attestation,*,expected_owner=None):
    """Exact metadata commit/reconcile only; never capture or regenerate QA."""
    path=Path(path).resolve();preview_ref=ref(path);m=sr.document(preview_ref);b=m['pinned_inputs'];source={'path':b['source_path'],'sha256':b['source_sha256']}
    folder=Path(source['path']).resolve().parent/'.native-region-frame-state';state_path=folder/(fc.fingerprint([source['sha256'],m['chain_id']])+'.json');before=expected_owner if expected_owner is not None else ref(state_path)
    need(before.get('path')==str(state_path) and ref(state_path)==before,'violation-region-preview-owner-CAS-mismatch')
    validate_frame(m['image']['path'],m,source=source,allow_preview=True);need(m.get('state')=='awaiting-visual-review','violation-region-not-awaiting-visual-review')
    a=sr.document(attestation);need(a.get('registration_preview')==preview_ref,'violation-region-original-preview-required')
    final=path.with_name('registration.json')
    with state_path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);need(ref(state_path)==before,'violation-region-preview-owner-CAS-mismatch');state=sr.document(before)
        final_ref=ref(final)if final.exists()else None;created_final=final_ref is None
        entries=[e for e in state['frames']if e.get('registration')in([preview_ref,final_ref]if final_ref else[preview_ref])];need(len(entries)==1,'violation-region-preview-operation-mismatch');entry=entries[0]
        if entry.get('state')!='complete':
            need(entry.get('state')=='awaiting-visual-review' and entry.get('registration')==preview_ref and entry.get('preview',preview_ref)==preview_ref,'violation-region-preview-owner-conflict')
            if entry.get('retake_attempt'):
                attempt=entry['retake_attempt'];need(attempt.get('state')=='preview-complete' and attempt.get('registration')==preview_ref and attempt.get('raw_capture_metadata')==m['capture_metadata'] and attempt.get('authorization')==m['pinned_inputs'].get('retake_authorization'),'violation-region-preview-retake-conflict')
        if final_ref is not None:
            completed=sr.document(final_ref);need(completed=={**m,'state':'complete','quality_attestation':attestation,'quality_approved_at':completed.get('quality_approved_at')} and completed.get('quality_approved_at') is not None,'violation-region-existing-final-conflict');validate_frame(completed['image']['path'],completed,source=source)
            if entry.get('state')=='complete':
                need(entry.get('preview')==preview_ref and entry.get('registration')==final_ref,'violation-region-completed-owner-conflict')
                if entry.get('retake_attempt'):need(entry['retake_attempt'].get('state')=='complete' and entry['retake_attempt'].get('preview')==preview_ref and entry['retake_attempt'].get('registration')==final_ref and entry['retake_attempt'].get('raw_capture_metadata')==completed['capture_metadata'],'violation-region-completed-retake-conflict')
                return {'metadata':str(final),'image':completed['image']['path'],'state':'complete','business_progress_changed':False}
        else:
            need(entry.get('state')=='awaiting-visual-review' and entry.get('registration')==preview_ref,'violation-region-preview-operation-mismatch');completed={**m,'state':'complete','quality_attestation':attestation,'quality_approved_at':stamp()};validate_frame(completed['image']['path'],completed,source=source);atomic(final,completed);final_ref=ref(final)
        need(entry.get('state')=='awaiting-visual-review' and entry.get('registration')==preview_ref and entry.get('preview',preview_ref)==preview_ref,'violation-region-preview-owner-conflict')
        if entry.get('retake_attempt'):entry['retake_attempt'].update(state='complete',registration=final_ref,preview=preview_ref,**({'completed_at':stamp()}if created_final else{'reconciled_at':stamp()}))
        entry.update(state='complete',registration=final_ref,preview=preview_ref);atomic(state_path,state)
        return {'metadata':str(final),'image':completed['image']['path'],'state':'complete','business_progress_changed':False}

def anchor_date_evidence(m):
    """Approved image fragment is not a claim of complete date visibility."""
    if m.get('date_visible_fragment_in_image') is True:
        need(m.get('state')=='complete' and m.get('capture_subcontract')==business.LOCAL and m.get('date_filter_visible') is False and m.get('date_text_complete_in_image') is False and m.get('list_headers_visible') is True and m.get('quality_review_required') is True and m.get('quality_attestation'),'native-frame-approved-date-fragment-required')
        dates=[e for e in m['pinned_inputs']['command']['elements'] if e['kind']=='date-filter'];need(len(dates)==1 and m.get('date_fragment_source_value')==dates[0]['expected_text'],'native-frame-date-fragment-source-value-conflict')
        # validate_chain already ran validate_frame, including exact source dates,
        # full before/after proof, source/key/image-bound quality attestation.
        return 'approved-source-bound-visible-date-fragment'
    need(m.get('date_filter_visible') is True and m.get('list_headers_visible') is True,'native-frame-full-date-and-headers-required');return 'complete-date-and-header-image'

def frame_epoch_namespace(m):
    """Called only after validate_frame; BUILD owns the viewport closure counter.

    Generic historical proofs keep one legacy domain, including missing BUILD.
    Region renderer builds never create a new viewport epoch namespace.
    """
    base=m['public_dom_proof']['before']['base_proof']
    if m['visibility_policy']==business.CONTRACT:
        known={*(f'viewport-notice-business-cells-v{i}' for i in range(3,9)),
               'viewport-notice-business-cells-v9-provider-manual-preview-v2',
               'viewport-notice-business-cells-v10-business-text-diagnostic-v1',
               'viewport-notice-business-cells-v11-manual-own-text-overflow-v2',
               'viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1'}
        build=base.get('diagnostic_build')
        need(base.get('evidence_contract')==business.CONTRACT and isinstance(build,str) and build in known,'native-frame-epoch-build-unverified')
        return 'business-viewport-build:'+build
    return 'legacy-global-viewport-epoch'

def validate_chain(manifest,*,source,company,groupid,start,end_exclusive,notice_ids):
    with validation.pure_scope(sys.modules[__name__]):
        return _validate_chain_uncached(manifest,source=source,company=company,groupid=groupid,start=start,end_exclusive=end_exclusive,notice_ids=notice_ids)

def _validate_chain_uncached(manifest,*,source,company,groupid,start,end_exclusive,notice_ids):
    need(manifest.get('capture_backend')==BACKEND and manifest.get('visibility_policy') in (POLICY,business.CONTRACT) and manifest.get('source_sha256')==source['sha256'],'native-frame-chain-scope-invalid');frames=manifest.get('frames');need(isinstance(frames,list) and bool(frames),'native-frame-chain-empty');src=sr.document(source);need(src['company']==company and str(src['groupid'])==str(groupid) and src['start']==start and src['end_exclusive']==end_exclusive and {r['notice_id'] for r in src['records']['rows']}==set(notice_ids),'native-frame-chain-source-conflict')
    pages={};entries=[];covered=set();keys=set();profile_sha=None;query=None;version=None;previous_page=0;last_time=None;epoch_counters={};epoch_domains=[];chain_id=manifest.get('chain_id');need(isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'native-frame-chain-id-invalid')
    for frame in frames:
        m=sr.document(frame['metadata']);need(m['chain_id']==chain_id and m['visibility_policy']==manifest['visibility_policy'],'native-frame-chain-id-policy-conflict');checked=validate_frame(frame['image'],m,source=source);page=m['page_scope']['page'];mode=m['frame_mode'];binding=m['pinned_inputs'];key=binding['captureKey'];need(key not in keys,'native-frame-capture-key-duplicate');keys.add(key)
        if query is None:query=m['query_fingerprint'];profile_sha=binding['profile_sha256'];version=checked['version']
        need(query==m['query_fingerprint'] and profile_sha==binding['profile_sha256'] and version==checked['version'],'native-frame-chain-query-profile-version-changed')
        if page not in pages:
            need(mode=='anchor' and page==previous_page+1,'native-frame-page-anchor-required');anchor_date_evidence(m);need(not previous_page or not pages[previous_page]['last_page'],'native-frame-page-after-final');ids=[r['notice_id'] for r in m['page_scope']['page_rows']];need(not any(i in old['ids'] for old in pages.values() for i in ids),'native-frame-id-repeated-across-pages');pages[page]={'fingerprint':m['page_fingerprint'],'ids':ids,'last_page':m['page_scope']['last_page'],'scope':checked['capture_scope'],'window':checked['window_scope']};previous_page=page;epoch_counters={}
        need(page==previous_page and m['page_fingerprint']==pages[page]['fingerprint'] and checked['capture_scope']==pages[page]['scope'] and checked['window_scope']==pages[page]['window'],'native-frame-old-anchor-or-window-reused');at=sr.when(checked['observed_at']);epoch=m['public_dom_proof']['before']['base_proof']['epoch'];namespace=frame_epoch_namespace(m);need(type(epoch) is int and epoch>=0 and (last_time is None or at>=last_time) and (namespace not in epoch_counters or epoch>=epoch_counters[namespace]),'native-frame-time-or-dom-epoch-reset');last_time=at;pair_end=m['public_dom_proof']['after']['base_proof']['epoch'] if m.get('postguard_consistency') else epoch;need(type(pair_end) is int and pair_end>=epoch,'native-frame-time-or-dom-epoch-reset');epoch_counters[namespace]=pair_end;epoch_domains.append({'frame_index':len(entries),'namespace':namespace,'epoch':epoch,**({'after_epoch':pair_end} if m.get('postguard_consistency') else {})});covered.update(checked['notice_ids']);entries.append({'image':{'path':frame['image'],'sha256':m['sha256']},'metadata':frame['metadata'],'references':checked['references'],'notice_ids':checked['notice_ids'],'frame_mode':mode,'page':page})
    need(pages[previous_page]['last_page'] and {i for p in pages.values() for i in p['ids']}==set(notice_ids) and covered==set(notice_ids),'native-frame-chain-full-page-row-coverage-incomplete');return {'entries':entries,'notice_ids':sorted(covered),'visibility_policy':manifest['visibility_policy'],'chain_id':chain_id,'capture_backend':BACKEND,'whole_window':False,'region_only':True,'viewport_only':False,'epoch_domain_sequence':epoch_domains}

def assemble(source_ref,metadata_paths,out):
    src=sr.document(source_ref);frames=[];chain_id=None;chain_policy=None
    for path in metadata_paths:
        m=sr.document(ref(path));cap=sr.document(m['capture_metadata']);chain_id=chain_id or m['chain_id'];chain_policy=chain_policy or m['visibility_policy'];need(chain_policy==m['visibility_policy'],'native-frame-policy-conflict');need(chain_id==m['chain_id'],'native-frame-assemble-chain-conflict');frames.append((sr.when(cap['captured_at']),{'image':m['image']['path'],'metadata':ref(path)}))
    manifest={'capture_backend':BACKEND,'visibility_policy':chain_policy,'source_sha256':source_ref['sha256'],'chain_id':chain_id,'frames':[f for _,f in sorted(frames,key=lambda x:x[0])]};validate_chain(manifest,source=source_ref,company=src['company'],groupid=src['groupid'],start=src['start'],end_exclusive=src['end_exclusive'],notice_ids=[r['notice_id'] for r in src['records']['rows']]);out=Path(out).resolve();need(not out.exists(),'native-frame-manifest-exists');atomic(out,manifest);return ref(out)

def inspect_registration(path):
    with validation.pure_scope(sys.modules[__name__]):
        return _inspect_registration_uncached(path)

def _inspect_registration_uncached(path):
    path=Path(path).resolve();m=sr.document(ref(path));inputs=metadata_inputs(m);source={'path':m['pinned_inputs']['source_path'],'sha256':m['pinned_inputs']['source_sha256']};checked=validate_frame(m['image']['path'],m,source=source,allow_preview=True);facts=frame_facts(m['public_dom_proof']['before'],inputs)
    return {'metadata':ref(path),'image':m['image'],'state':m.get('state','complete'),'verified':checked,'approval_binding':quality_binding(m),'required_visual_confirmation':business.expected_visibility(m['frame_mode'],facts) if is_business(inputs) else {'date_and_headers':m['frame_mode']=='anchor','rows':{i:dict.fromkeys(('reason','subject','object','effective_status','disposal'),True) for i in facts['notice_ids']}},'approval_performed':False,'ui_used':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='op',required=True);i=sub.add_parser('inspect');i.add_argument('--metadata',required=True);q=sub.add_parser('approve');q.add_argument('--preview',required=True);q.add_argument('--attestation',required=True);a=sub.add_parser('capture')
    for key in ('source','source-sha256','observation','observation-sha256','profile','profile-sha256','pid','mode','chain-id','key','outdir'):a.add_argument('--'+key,required=True)
    a.add_argument('--retake-authorization');a.add_argument('--retake-authorization-sha256');a.add_argument('--revision');a.add_argument('--screenshot-anchor');a.add_argument('--screenshot-anchor-sha256');a.add_argument('--uncovered-only',action='store_true');a.add_argument('--replaces-manifest');a.add_argument('--replaces-sha256');a=sub.add_parser('assemble')
    for key in ('source','source-sha256','out'):a.add_argument('--'+key,required=True)
    a.add_argument('--frames',nargs='+',required=True);v=p.parse_args();r=lambda path,h:{'path':str(Path(path).resolve()),'sha256':h}
    if v.op=='inspect':result=inspect_registration(v.metadata)
    elif v.op=='approve':result=approve_preview(v.preview,ref(v.attestation))
    elif v.op=='assemble':result=assemble(r(v.source,v.source_sha256),v.frames,v.out)
    else:
        need(bool(v.replaces_manifest)==bool(v.replaces_sha256),'violation-region-parent-path-and-hash-required');parent=r(v.replaces_manifest,v.replaces_sha256) if v.replaces_manifest else None
        need(bool(v.screenshot_anchor)==bool(v.screenshot_anchor_sha256),'violation-anchor-path-hash-required')
        need(bool(v.retake_authorization)==bool(v.retake_authorization_sha256),'violation-region-retake-authorization-path-and-hash-required')
        result=capture(r(v.source,v.source_sha256),r(v.observation,v.observation_sha256),r(v.profile,v.profile_sha256),pid=int(v.pid),mode=v.mode,chain_id=v.chain_id,key=v.key,outdir=v.outdir,revision=v.revision,replaces=parent,uncovered_only=v.uncovered_only,screenshot_anchor=r(v.screenshot_anchor,v.screenshot_anchor_sha256) if v.screenshot_anchor else None,retake_authorization=r(v.retake_authorization,v.retake_authorization_sha256) if v.retake_authorization else None)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
