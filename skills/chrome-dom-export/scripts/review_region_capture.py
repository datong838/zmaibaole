#!/usr/bin/env python3
"""Revisioned normal-review region evidence. No UI input. Raw window retained."""
import argparse,fcntl,json,re,uuid,hashlib
from pathlib import Path
import review_capture as rc
import program_review_quality
import native_region_capture as region
import native_window_capture as nw
import bridge

def region_command(base):
    rc.require(len(base['reviews'])==1,'review-region-exactly-one-card-required')
    return {'op':'dom-region-proof',**{k:base[k] for k in ('tabId','windowId','groupid')},'base':base,'selectors':[base['reviews'][0]['card']],'purpose':'evidence-crop-only'}

def checked(response,command):
    rc.require(response.get('ok') is True,'review-region-proof-failed:'+str(response.get('error')));p=response['result']
    rc.require(p.get('safety_version')==rc.visible_capture.SAFETY and p.get('method')=='public-DOM-evidence-region-proof' and p.get('geometry_purpose')=='evidence-crop-only' and p.get('pixel_input_actions') is False and (p.get('external_painted_overlap') is False or (p.get('external_painted_overlap')=='unresolved' and p.get('quality_review_required') is True and bool(p.get('unresolved_overlay')))),'review-region-proof-method-version-invalid')
    base=rc.proof_response({'ok':True,'result':p['base_proof']},command['base'])
    rc.require(p.get('scope')==base['scope'] and p.get('url')==base['url'] and p.get('selectors')==command['selectors'] and p.get('review_action') in ('投诉','投诉审核中','查看投诉结果'),'review-region-current-scope-action-invalid')
    return p

def legacy_gate(manifest,replaces):
    source=Path(manifest['source']['path']);key=rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});state=source.parent/'.review-capture-state'/(key+'.json')
    if state.exists():
        old=rc.load(state);rc.require(old.get('state')=='complete','review-region-cannot-bypass-unknown-window-capture')
        rc.require(replaces is not None and replaces.get('sha256')==old['registration_sha256'] and rc.sha(old['registration'])==old['registration_sha256'],'review-region-explicit-completed-revision-parent-required')
    if replaces is not None:
        import review_registration
        value=rc.document(replaces);review_registration.verify(replaces['path']);rc.require(value['source']['sha256']==manifest['source']['sha256'] and value['review_keys']==manifest['review_keys'],'review-region-correction-parent-source-key-mismatch')

def capture(manifest,outdir,request,*,pid,revision,replaces=None,native=None,ax=None):
    rc.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',revision) is not None,'review-region-explicit-revision-required')
    base=rc.command_from_inputs(*(manifest[k] for k in ('job','source','envelope','profile','page')),manifest['review_keys']);command=region_command(base)
    outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True);source=Path(manifest['source']['path']);states=source.parent/'.review-region-state';states.mkdir(exist_ok=True);key=rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});state=states/(key+'.json')
    operation={'kind':'normal-review-region-capture-v1','manifest':manifest,'outdir':str(outdir),'pid':pid,'revision':revision,'replaces':replaces}
    with (states/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if state.exists():
            old=rc.load(state)
            if old.get('observation_revision'):return capture_observation_revision(state,old,operation,command,request,native=native,ax=ax)
            rc.require(old.get('operation')==operation,'review-region-original-operation-required')
            if old.get('pre_native_authorization'):return continue_pre_native(state,old,operation,command,request,native=native,ax=ax)
            if old.get('state')=='unknown' and old.get('journal_contract')==NORMAL_V2:
                rc.require('derivation_intent' in old,'review-region-unknown-no-recapture');return finish_normal_v2(state,old,command)
            if old.get('state')=='unknown' and old.get('postguard_continuation'):return continue_postguard(state,old,command,request,native=native,ax=ax)
            rc.require(old.get('state') in ('complete','awaiting-visual-review'),'review-region-unknown-no-recapture')
            verify(old['registration']['path'],allow_preview=old['state']=='awaiting-visual-review');return rc.document(old['registration'])
        legacy_gate(manifest,replaces)
        return capture_normal_v2(state,operation,command,request,native=native,ax=ax)

def verify(path,*,allow_preview=False):
    v=rc.load(path);rc.require(v.get('kind')=='normal-review-region-registration-v1' and v.get('state') in (('complete','awaiting-visual-review') if allow_preview else ('complete',)),'review-region-registration-incomplete');base=rc.command_from_inputs(*(v[k] for k in ('job','source','envelope','profile','page')),v['review_keys']);command=region_command(base)
    # Historical verification keeps the exact reviewed version on both proofs.
    before=checked({'ok':True,'result':v['proof_before']},command);after=checked({'ok':True,'result':v['proof_after']},command);rc.require(before==after and v['geometry_before']==v['geometry_after'],'review-region-proof-or-native-frame-pair-changed')
    cap={'backend':'screen-capture-kit','pid':v['native_pid'],**{k:base[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':v['capture_key']};meta=rc.document(v['capture_metadata']);nw.validate(meta,cap,v['derivation']['source']['path']);rc.require(meta['before']['scope']==v['geometry_before']['scope'] and meta['before']['window']==v['geometry_before']['window'],'review-region-raw-map-scope-mismatch')
    image=region.validate(v['derivation'],before,v['geometry_before']);rc.require(image==v['image'] and v.get('whole_window') is False and v.get('region_derived') is True and v.get('image_scope')=='derived-dom-review-region','review-region-output-contract-invalid')
    expected={r['review_key']:r['text_complete_in_image'] for r in before['base_proof']['reviews']};rc.require(v['text_complete_in_image']==expected,'review-region-text-completeness-changed');when=rc.authority.stamp
    if any(k in v for k in NORMAL_FIELDS) or (Path(meta['png']['path']).parent/'capture-v2/derivation-intent.json').exists():
        rc.require(all(k in v for k in NORMAL_FIELDS) and not any(k in v for k in ('postguard_continuation','proof_before_checkpoint_at','proof_before_time_basis','postguard_attempt','postguard_reply','postguard_geometry')),'review-v2-complete-typed-fields-required');verify_normal_v2(v,command)
    elif any(k in v for k in ('postguard_continuation','proof_before_checkpoint_at','proof_before_time_basis','postguard_attempt','postguard_reply','postguard_geometry')):
        rc.require(all(k in v for k in ('postguard_continuation','proof_before_checkpoint_at','proof_before_time_basis','postguard_attempt','postguard_reply','postguard_geometry')),'review-postguard-complete-typed-fields-required');verify_continuation(v,command,meta)
    else:rc.require(when(rc.document(v['source'])['observed_at'])<=when(v['proof_before_observed_at'])<=when(meta['intent_at'])<=when(meta['captured_at'])<=when(v['proof_after_observed_at'])<=when(v['recorded_at']),'review-region-time-chain-invalid')
    if any(k in v for k in ('observation_revision','revision_registration','observation_revision_contract')):verify_observation_revision(v,path,command)
    if before.get('quality_review_required') and v['state']=='complete':validate_attestation(v,path)
    return {'ok':True,'quality_review_required':before.get('quality_review_required',False),'state':v['state'],'review_keys':v['review_keys'],'image':image,'image_scope':'derived-dom-review-region','whole_window':False,'region_derived':True,'capture_backend':v['capture_backend'],'text_complete_in_image':expected,'occlusion_verified':False}

# New captures persist every stage. Only a durable ready-to-derive frontier can
# resume locally; no UI/native read or screenshot is repeated by that path.
NORMAL_V2='durable-normal-region-capture-v2'
NORMAL_FIELDS=('normal_capture_contract','normal_derivation_intent','derivation_verified_at')
def durable(path,value):
    path=Path(path);rc.require(not path.exists() and path.resolve()==path,'review-v2-evidence-path-exists-or-alias');rc.atomic(path,value);return rc.ref(path)
def normal_evidence(journal):
    out=Path(journal['operation']['outdir'])/'capture-v2'
    return out/'pre-native-continuation-v1' if journal.get('pre_native_authorization') else out

def normal_read(journal,state,command,request,label):
    started=rc.stamp();path=normal_evidence(journal)/label
    try:response=request(command)
    except Exception as error:
        journal[label]=durable(path,{'operation':journal['operation'],'command':command,'started_at':started,'observed_at':rc.stamp(),'error':{'type':type(error).__name__,'message':str(error)}});rc.atomic(state,journal);raise
    record={'operation':journal['operation'],'command':command,'started_at':started,'observed_at':rc.stamp(),'response':response};journal[label]=durable(path,record);rc.atomic(state,journal);return record

def normal_geometry(journal,state,cap,request,native,ax,label):
    started=rc.stamp();out=normal_evidence(journal)
    def diagnostic(value):durable(out/(label+'-diagnostic.json'),value)
    try:value=region.observe(cap,request,native,ax,diagnostic=diagnostic)
    except Exception as error:
        journal[label]=durable(out/label,{'operation':journal['operation'],'started_at':started,'observed_at':rc.stamp(),'error':{'type':type(error).__name__,'message':str(error)}});rc.atomic(state,journal);raise
    record={'operation':journal['operation'],'started_at':started,'observed_at':rc.stamp(),'geometry':value};journal[label]=durable(out/label,record);rc.atomic(state,journal);return value

def capture_normal_v2(state,operation,command,request,*,native,ax,pre_native_authorization=None):
    out=Path(operation['outdir']);evidence=out/'capture-v2'
    if pre_native_authorization is not None:
        import review_capture_focus
        review_capture_focus.panel_capture_state(pre_native_authorization,operation,require_fresh=True);evidence=evidence/'pre-native-continuation-v1'
    rc.require(not evidence.exists() and not any((out/n).exists() for n in ('raw-window.png','raw-window.json','review-region.png','registration.json','preview-registration.json')),'review-v2-existing-output-no-new-capture')
    evidence.mkdir();journal={'journal_contract':NORMAL_V2,'state':'unknown','operation':operation,'created_at':rc.stamp()}
    if pre_native_authorization is not None:journal['pre_native_authorization']=pre_native_authorization
    rc.atomic(state,journal)
    before_record=normal_read(journal,state,command,request,'before-reply.json');before=checked(before_record['response'],command)
    rc.require(rc.authority.stamp(rc.document(operation['manifest']['source'])['observed_at'])<=rc.authority.stamp(before_record['observed_at']),'review-region-source-time-invalid')
    cap={'backend':'screen-capture-kit','pid':operation['pid'],**{k:command[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':operation['manifest']['capture_key']+':region:'+operation['revision']};rc.require(len(cap['captureKey'])<=128,'review-region-capture-key-too-long')
    geometry=normal_geometry(journal,state,cap,request,native,ax,'before-geometry.json');journal.update(proof_before=before,geometry_before=geometry,intent_at=rc.stamp());rc.atomic(state,journal)
    raw=nw.write_capture(cap,out/'raw-window.png',request,native);meta_ref=rc.ref(raw['result']['metadata']);meta=rc.document(meta_ref);image=nw.validate(meta,cap,raw['result']['path'])
    journal['native_complete']=durable(evidence/'native-complete.json',{'operation':operation,'command':cap,'metadata':meta_ref,'image':image,'observed_at':rc.stamp()});rc.atomic(state,journal)
    post=normal_read(journal,state,command,request,'after-reply.json');after=checked(post['response'],command);after_geometry=normal_geometry(journal,state,cap,request,native,ax,'after-geometry.json')
    rc.require(before==after and geometry==after_geometry,'review-region-dom-or-native-geometry-changed')
    journal['ready_at']=rc.stamp();checkpoint=durable(evidence/'ready-checkpoint.json',journal)
    intent={'kind':NORMAL_V2,'operation':operation,'checkpoint':checkpoint,'output':str(out/'review-region.png'),'created_at':rc.stamp()}
    if pre_native_authorization is not None:intent['pre_native_authorization']=pre_native_authorization
    journal['derivation_intent']=durable(evidence/'derivation-intent.json',intent);rc.atomic(state,journal)
    return finish_normal_v2(state,journal,command)

def continue_pre_native(state,old,operation,command,request,*,native,ax):
    import review_capture_focus
    proof=old['pre_native_authorization'];review_capture_focus.panel_capture_state(proof,operation)
    child=Path(operation['outdir'])/'capture-v2/pre-native-continuation-v1/state.json'
    if child.exists():
        journal=rc.load(child);rc.require(journal['operation']==operation and journal.get('pre_native_authorization')==proof,'review-pre-native-original-branch-required')
        if journal['state']=='unknown':
            rc.require('derivation_intent' in journal,'review-pre-native-unknown-no-recapture');value=finish_normal_v2(child,journal,command)
        else:
            rc.require(journal['state'] in ('complete','awaiting-visual-review'),'review-pre-native-child-state');verify(journal['registration']['path'],allow_preview=True);value=rc.document(journal['registration'])
    else:value=capture_normal_v2(child,operation,command,request,native=native,ax=ax,pre_native_authorization=proof)
    journal=rc.load(child);current=rc.load(state);rc.require(current==old,'review-pre-native-original-state-changed');current.update(state=journal['state'],registration=journal['registration']);rc.atomic(state,current);return value

def normal_path(path):
    value=Path(path);rc.require(value.is_absolute() and value.resolve()==value and not value.is_symlink(),'review-v2-canonical-path-required');return value

def normal_frontier(intent_ref,command):
    normal_path(intent_ref['path'])
    intent=rc.document(intent_ref);op=intent['operation'];out=Path(op['outdir']);evidence=out/'capture-v2';checkpoint=rc.document(intent['checkpoint'])
    if 'pre_native_authorization' in intent or 'pre_native_authorization' in checkpoint:
        rc.require(intent.get('pre_native_authorization')==checkpoint.get('pre_native_authorization') and intent.get('pre_native_authorization') is not None,'review-pre-native-typed-authority-required')
        import review_capture_focus
        review_capture_focus.verify_pre_native_authorization(intent['pre_native_authorization'],op);evidence=evidence/'pre-native-continuation-v1'
    normal_path(intent['checkpoint']['path']);normal_path(out);normal_path(intent['output'])
    rc.require(intent['kind']==NORMAL_V2 and Path(intent_ref['path'])==evidence/'derivation-intent.json' and Path(intent['checkpoint']['path'])==evidence/'ready-checkpoint.json' and intent['output']==str(out/'review-region.png') and checkpoint['journal_contract']==NORMAL_V2 and checkpoint['state']=='unknown' and checkpoint['operation']==op,'review-v2-derivation-intent-binding')
    m=op['manifest'];base=rc.command_from_inputs(*(m[k] for k in ('job','source','envelope','profile','page')),m['review_keys']);rc.require(region_command(base)==command,'review-v2-current-inputs-changed')
    values={}
    for name in ('before-reply.json','before-geometry.json','native_complete','after-reply.json','after-geometry.json'):
        ref=checkpoint[name];normal_path(ref['path']);expected='native-complete.json' if name=='native_complete' else name;rc.require(Path(ref['path'])==evidence/expected,'review-v2-evidence-path-binding');value=rc.document(ref);rc.require(value['operation']==op,'review-v2-evidence-operation-binding');values[name]=value
    pre=values['before-reply.json'];post=values['after-reply.json'];rc.require(pre['command']==post['command']==command,'review-v2-DOM-command-binding');before=checked(pre['response'],command);after=checked(post['response'],command)
    gb=values['before-geometry.json'];ga=values['after-geometry.json'];rc.require(before==after==checkpoint['proof_before'] and gb['geometry']==ga['geometry']==checkpoint['geometry_before'],'review-v2-proof-or-geometry-changed')
    cap={'backend':'screen-capture-kit','pid':op['pid'],**{k:command[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':m['capture_key']+':region:'+op['revision']};nr=values['native_complete'];normal_path(nr['metadata']['path']);normal_path(nr['image']['path']);meta=rc.document(nr['metadata']);rc.require(nr['command']==cap and Path(nr['metadata']['path'])==out/'raw-window.json' and Path(nr['image']['path'])==out/'raw-window.png' and nw.validate(meta,cap,nr['image']['path'])==nr['image'],'review-v2-native-complete-binding')
    rc.require(meta['before']['scope']==gb['geometry']['scope'] and meta['before']['window']==gb['geometry']['window'],'review-v2-native-geometry-binding')
    when=rc.authority.stamp;times=[rc.document(m['source'])['observed_at'],pre['started_at'],pre['observed_at'],gb['started_at'],gb['observed_at'],checkpoint['intent_at'],meta['intent_at'],meta['captured_at'],meta['completed_at'],nr['observed_at'],post['started_at'],post['observed_at'],ga['started_at'],ga['observed_at'],checkpoint['ready_at'],intent['created_at']];stamps=[when(t) for t in times];rc.require(all(a<=b for a,b in zip(stamps,stamps[1:])),'review-v2-stage-time-chain-invalid')
    return intent,checkpoint,values,before,cap

def existing_normal_crop(raw,proof,geometry,out):
    # Construct only metadata; region.validate independently compares every RGBA
    # pixel with the exact crop from the original, already-validated raw PNG.
    normal_path(raw['path']);normal_path(out)
    width,height=region.validate_png(Path(raw['path']).read_bytes());box=region.crop_box(proof,geometry,width,height);w,h=region.validate_png(Path(out).read_bytes());Image=region.pillow()
    with Image.open(out) as image:pixels=hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()
    value={'source':raw,'image':{'path':str(out),'sha256':rc.sha(out),'width':w,'height':h},'crop_box_pixels':box,'derived_rgba_sha256':pixels,'operation':'unchanged-source-pixel-crop','whole_window':False,'viewport_only':False,'region_only':True,'geometry_purpose':'evidence-crop-only','pixel_input_actions':False};region.validate(value,proof,geometry);return value

def finish_normal_v2(state,journal,command):
    rc.require(journal.get('journal_contract')==NORMAL_V2 and journal.get('state')=='unknown' and 'derivation_intent' in journal,'review-v2-valid-derivation-intent-required');intent,checkpoint,records,before,cap=normal_frontier(journal['derivation_intent'],command)
    expected={**checkpoint,'derivation_intent':journal['derivation_intent']};rc.require(journal==expected and rc.load(state)==journal,'review-v2-original-journal-changed')
    op=intent['operation'];m=op['manifest'];out=Path(op['outdir']);path=out/('preview-registration.json' if before.get('quality_review_required') else 'registration.json')
    if path.exists():
        value=rc.load(path);rc.require(value.get('normal_derivation_intent')==journal['derivation_intent'],'review-v2-existing-registration-binding');verify(path,allow_preview=True)
    else:
        raw=records['native_complete']['image'];geometry=checkpoint['geometry_before'];image_path=Path(intent['output'])
        crop=existing_normal_crop(raw,before,geometry,image_path) if image_path.exists() else region.derive(raw['path'],before,geometry,image_path)
        region.validate(crop,before,geometry);verified_at=rc.stamp()
        value={'kind':'normal-review-region-registration-v1','state':'awaiting-visual-review' if before.get('quality_review_required') else 'complete',**{k:m[k] for k in ('job','source','envelope','profile','page','review_keys')},'revision':op['revision'],'replaces_registration':op['replaces'],'capture_backend':'screen-capture-kit-dom-region','native_pid':op['pid'],'capture_key':cap['captureKey'],'proof_before':before,'proof_after':records['after-reply.json']['response']['result'],'proof_before_observed_at':records['before-reply.json']['observed_at'],'proof_after_observed_at':records['after-reply.json']['observed_at'],'geometry_before':geometry,'geometry_after':records['after-geometry.json']['geometry'],'capture_metadata':records['native_complete']['metadata'],'derivation':crop,'image':crop['image'],'whole_window':False,'region_derived':True,'image_scope':'derived-dom-review-region','text_complete_in_image':{r['review_key']:r['text_complete_in_image'] for r in before['base_proof']['reviews']},'occlusion_verified':False,'normal_capture_contract':NORMAL_V2,'normal_derivation_intent':journal['derivation_intent'],'derivation_verified_at':verified_at,'recorded_at':rc.stamp()}
        if 'pre_native_authorization' in journal:value['pre_native_authorization']=journal['pre_native_authorization']
        rc.require(not path.exists(),'review-v2-registration-already-exists');rc.atomic(path,value);verify(path,allow_preview=True)
    journal.update(state=value['state'],registration=rc.ref(path));rc.atomic(state,journal);return value

def verify_normal_v2(value,command):
    intent,checkpoint,records,before,cap=normal_frontier(value['normal_derivation_intent'],command);op=intent['operation'];m=op['manifest']
    rc.require(value.get('pre_native_authorization')==intent.get('pre_native_authorization'),'review-pre-native-registration-authority')
    rc.require(value['normal_capture_contract']==NORMAL_V2 and all(value[k]==m[k] for k in ('job','source','envelope','profile','page','review_keys')) and value['revision']==op['revision'] and value['replaces_registration']==op['replaces'] and value['native_pid']==op['pid'] and value['capture_key']==cap['captureKey'],'review-v2-registration-operation-binding')
    rc.require(value['proof_before']==value['proof_after']==before and value['geometry_before']==value['geometry_after']==checkpoint['geometry_before'] and value['proof_before_observed_at']==records['before-reply.json']['observed_at'] and value['proof_after_observed_at']==records['after-reply.json']['observed_at'] and value['capture_metadata']==records['native_complete']['metadata'] and value['derivation']['source']==records['native_complete']['image'],'review-v2-registration-evidence-binding')
    when=rc.authority.stamp;rc.require(when(intent['created_at'])<=when(value['derivation_verified_at'])<=when(value['recorded_at']),'review-v2-derivation-time-invalid')


# This contract completes a missing readonly postguard, never a second capture.
CONTINUATION='original-region-intent-checkpoint-and-new-readonly-postguard-v1'
def original_complete_region(original,state_path):
    rc.require(set(original)=={'state','operation','intent_at','proof_before','geometry_before'} and original['state']=='unknown','review-postguard-exact-original-unknown-required')
    op=original['operation'];m=op['manifest'];out=Path(op['outdir']);source=Path(m['source']['path']);key=rc.digest({'source':m['source']['sha256'],'review_keys':sorted(m['review_keys'])})
    rc.require(Path(state_path)==source.parent/'.review-region-state'/(key+'.json') and out.is_absolute() and not out.is_symlink(),'review-postguard-canonical-original-required')
    base=rc.command_from_inputs(*(m[k] for k in ('job','source','envelope','profile','page')),m['review_keys']);command=region_command(base);before=checked({'ok':True,'result':original['proof_before']},command)
    rc.require(op['kind']=='normal-review-region-capture-v1' and type(op['pid']) is int and op['pid']>0 and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',op['revision']) is not None,'review-postguard-original-operation-invalid')
    cap={'backend':'screen-capture-kit','pid':op['pid'],**{k:base[k] for k in ('tabId','windowId','groupid')},'url':before['url'],'captureKey':m['capture_key']+':region:'+op['revision']}
    for path in (out/'raw-window.json',out/'raw-window.png'):rc.require(path.is_file() and not path.is_symlink(),'review-postguard-original-native-files-required')
    meta_ref=rc.ref(out/'raw-window.json');meta=rc.document(meta_ref);image=nw.validate(meta,cap,out/'raw-window.png')
    rc.require(meta['before']['scope']==original['geometry_before']['scope'] and meta['before']['window']==original['geometry_before']['window'],'review-postguard-original-geometry-native-mismatch')
    when=rc.authority.stamp;rc.require(when(rc.document(m['source'])['observed_at'])<=when(original['intent_at'])<=when(meta['intent_at'])<=when(meta['captured_at'])<=when(meta['completed_at']),'review-postguard-original-checkpoint-time-invalid')
    return {'command':command,'capture_command':cap,'native_metadata':meta_ref,'raw_image':image}

def postguard_authorization(proof_ref):
    import review_capture_focus as recovery
    p=rc.document(proof_ref);parent=recovery.o.doc(recovery.o.ref(recovery.o.location(p['order'])/'launcher.json'));recovery.verify_recovered(parent,proof_ref)
    rc.require(p.get('recovery_stage')=='region-readonly-postguard' and p.get('ui_used') is False,'review-postguard-typed-authorization-required')
    original=rc.document(p['region_archive']);facts=original_complete_region(original,p['original_region']['path'])
    rc.require(facts==p['facts']['region'],'review-postguard-original-facts-changed')
    return p,original,facts

def continuation_value(original,proof_ref,attempt,reply_ref,geometry_ref,crop,meta_ref):
    op=original['operation'];m=op['manifest'];post=rc.document(reply_ref);geometry=rc.document(geometry_ref)
    return {'kind':'normal-review-region-registration-v1','state':'awaiting-visual-review' if original['proof_before'].get('quality_review_required') else 'complete',**{k:m[k] for k in ('job','source','envelope','profile','page','review_keys')},'revision':op['revision'],'replaces_registration':op['replaces'],'capture_backend':'screen-capture-kit-dom-region','native_pid':op['pid'],'capture_key':m['capture_key']+':region:'+op['revision'],'proof_before':original['proof_before'],'proof_after':post['response']['result'],'proof_before_checkpoint_at':original['intent_at'],'proof_before_time_basis':CONTINUATION,'proof_after_observed_at':post['observed_at'],'geometry_before':original['geometry_before'],'geometry_after':geometry['geometry'],'capture_metadata':meta_ref,'derivation':crop,'image':crop['image'],'whole_window':False,'region_derived':True,'image_scope':'derived-dom-review-region','text_complete_in_image':{r['review_key']:r['text_complete_in_image'] for r in original['proof_before']['base_proof']['reviews']},'occlusion_verified':False,'recorded_at':rc.stamp(),'postguard_continuation':proof_ref,'postguard_attempt':str(attempt),'postguard_reply':reply_ref,'postguard_geometry':geometry_ref}

def verify_continuation(v,command,meta):
    p,original,facts=postguard_authorization(v['postguard_continuation']);op=original['operation'];attempt=Path(v['postguard_attempt']);base=Path(op['outdir'])/'postguard-continuations'/p['original_region']['sha256']
    rc.require(attempt.parent==base and re.fullmatch(r'[0-9a-f]{32}',attempt.name) is not None and not attempt.is_symlink(),'review-postguard-canonical-attempt-required')
    rc.require(v['proof_before_time_basis']==CONTINUATION and 'proof_before_observed_at' not in v and v['proof_before_checkpoint_at']==original['intent_at'] and v['proof_before']==original['proof_before'] and v['geometry_before']==original['geometry_before'],'review-postguard-original-checkpoint-binding')
    post=rc.document(v['postguard_reply']);geometry=rc.document(v['postguard_geometry']);rc.require(Path(v['postguard_reply']['path'])==attempt/'post-reply.json' and Path(v['postguard_geometry']['path'])==attempt/'after-geometry.json' and post['command']==command==facts['command'] and post['original_region']==p['original_region'] and geometry['original_region']==p['original_region'],'review-postguard-original-read-bindings')
    after=checked(post['response'],command);rc.require(after==v['proof_after']==original['proof_before'] and geometry['geometry']==v['geometry_after']==original['geometry_before'] and v['capture_metadata']==facts['native_metadata'] and v['derivation']['source']==facts['raw_image'],'review-postguard-exact-original-pair-required')
    rc.require(v['revision']==op['revision'] and v['native_pid']==op['pid'] and v['capture_key']==facts['capture_command']['captureKey'] and v['replaces_registration']==op['replaces'] and all(v[k]==op['manifest'][k] for k in ('job','source','envelope','profile','page','review_keys')),'review-postguard-original-operation-binding')
    when=rc.authority.stamp;rc.require(when(rc.document(v['source'])['observed_at'])<=when(v['proof_before_checkpoint_at'])<=when(meta['intent_at'])<=when(meta['captured_at'])<=when(meta['completed_at'])<=when(post['request_started_at'])<=when(post['observed_at'])==when(v['proof_after_observed_at'])<=when(geometry['observed_at'])<=when(v['recorded_at']),'review-postguard-time-chain-invalid')

def continue_postguard(state,old,command,request,*,native=None,ax=None):
    proof_ref=old['postguard_continuation'];p,original,facts=postguard_authorization(proof_ref)
    rc.require(Path(state)==Path(p['original_region']['path']) and old=={**original,'postguard_continuation':proof_ref} and command==facts['command'],'review-postguard-authorized-original-state-required')
    out=Path(original['operation']['outdir']);path=out/('preview-registration.json' if original['proof_before'].get('quality_review_required') else 'registration.json')
    if path.exists():
        v=rc.load(path);rc.require(v.get('postguard_continuation')==proof_ref,'review-postguard-existing-registration-binding');verify(path,allow_preview=True);old.update(state=v['state'],registration=rc.ref(path));rc.atomic(state,old);return v
    rc.require(not (out/'review-region.png').exists() and not (out/'preview-registration.json').exists() and not (out/'registration.json').exists(),'review-postguard-existing-derived-output-hold')
    attempt=out/'postguard-continuations'/p['original_region']['sha256']/uuid.uuid4().hex;attempt.mkdir(parents=True,exist_ok=False)
    started=rc.stamp()
    try:response=request(command)
    except Exception as error:
        rc.atomic(attempt/'post-request-error.json',{'command':command,'original_region':p['original_region'],'request_started_at':started,'observed_at':rc.stamp(),'error':{'type':type(error).__name__,'message':str(error)}});raise
    post={'command':command,'response':response,'original_region':p['original_region'],'request_started_at':started,'observed_at':rc.stamp()};rc.atomic(attempt/'post-reply.json',post);reply_ref=rc.ref(attempt/'post-reply.json')
    after=checked(response,command);rc.require(after==original['proof_before'],'review-postguard-DOM-changed-original-unknown-preserved')
    geometry=region.observe(facts['capture_command'],request,native,ax);rc.atomic(attempt/'after-geometry.json',{'original_region':p['original_region'],'geometry':geometry,'observed_at':rc.stamp()});geometry_ref=rc.ref(attempt/'after-geometry.json')
    rc.require(geometry==original['geometry_before'],'review-postguard-geometry-changed-original-unknown-preserved')
    # Recheck native PNG and all original source references after external reads.
    rc.require(original_complete_region(original,state)==facts and rc.load(state)==old,'review-postguard-original-inputs-changed')
    crop=region.derive(facts['raw_image']['path'],original['proof_before'],geometry,out/'review-region.png');v=continuation_value(original,proof_ref,attempt,reply_ref,geometry_ref,crop,facts['native_metadata']);rc.atomic(path,v);verify(path,allow_preview=True)
    old.update(state=v['state'],registration=rc.ref(path));rc.atomic(state,old);return v

# A new observation revision is independent of business side effects. Its only
# inputs are the already pinned source/manifest and a reviewed original hold.
OBSERVATION_REVISION='controlled-fresh-region-observation-revision-v1'
def observation_authorization(proof_ref):
    import review_capture_focus as recovery
    p=rc.document(proof_ref);parent=recovery.o.doc(recovery.o.ref(recovery.o.location(p['order'])/'launcher.json'));recovery.verify_recovered(parent,proof_ref)
    rc.require(p.get('recovery_stage')=='fresh-observation-revision' and p.get('ui_used') is False,'review-observation-typed-authorization-required')
    original=rc.document(p['region_archive']);op=original['operation'];new=observation_operation(op)
    rc.require(new==p['facts']['new_operation'] and p['facts']['old_native']['native_metadata']['path']==str(Path(op['outdir'])/'raw-window.json'),'review-observation-original-operation-changed')
    return p,original,new

def observation_operation(original):
    revision=original['revision']+'.r1';rc.require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,39}',revision) is not None,'review-observation-revision-too-long')
    return {**original,'revision':revision,'outdir':str(Path(original['outdir'])/'revisions'/revision)}

def verify_observation_revision(v,path,command):
    rc.require(all(k in v for k in ('observation_revision','revision_registration','observation_revision_contract')) and v['observation_revision_contract']==OBSERVATION_REVISION,'review-observation-complete-typed-fields-required');p,original,new=observation_authorization(v['observation_revision']);child_ref=v['revision_registration'];out=Path(new['outdir']);child=rc.document(child_ref)
    rc.require(Path(child_ref['path'])==out/('preview-registration.json' if child['state']=='awaiting-visual-review' else 'registration.json') and Path(path) in (Path(original['operation']['outdir'])/'preview-registration.json',Path(original['operation']['outdir'])/'registration.json'),'review-observation-registration-path-binding')
    rc.require(child.get('normal_capture_contract')==NORMAL_V2 and child['revision']==new['revision'] and child['capture_key']==new['manifest']['capture_key']+':region:'+new['revision'] and Path(child['capture_metadata']['path'])==out/'raw-window.json' and child['derivation']['image']['path']==str(out/'review-region.png'),'review-observation-new-native-output-binding');verify(child_ref['path'],allow_preview=True)
    _,_,records,_,_=normal_frontier(child['normal_derivation_intent'],command);when=rc.authority.stamp;post=rc.document(p['original_post']);rc.require(when(post['observed_at'])<=when(p['at'])<=when(records['before-reply.json']['started_at'])<=when(records['before-reply.json']['observed_at']),'review-observation-new-before-must-follow-authorization')
    expected=dict(v)
    for k in ('observation_revision','revision_registration','observation_revision_contract','quality_attestation','quality_approved_at'):expected.pop(k,None)
    expected['state']=child['state'];rc.require(expected==child,'review-observation-original-registration-changed')

def capture_observation_revision(state,old,operation,command,request,*,native=None,ax=None):
    proof_ref=old['observation_revision'];p,original,new=observation_authorization(proof_ref);rc.require(Path(state)==Path(p['original_region']['path']) and operation==original['operation'],'review-observation-same-business-operation-required')
    if old.get('state') in ('complete','awaiting-visual-review'):
        verify(old['registration']['path'],allow_preview=old['state']=='awaiting-visual-review');return rc.document(old['registration'])
    rc.require(old=={**original,'observation_revision':proof_ref},'review-observation-original-unknown-binding');out=Path(new['outdir']);local=out/'capture-state.json'
    if local.exists():
        journal=rc.load(local);rc.require(journal['operation']==new,'review-observation-local-operation-changed')
        if journal.get('state')=='unknown':value=finish_normal_v2(local,journal,command)
        else:
            rc.require(journal.get('state') in ('complete','awaiting-visual-review'),'review-observation-local-state-unknown');verify(journal['registration']['path'],allow_preview=True);value=rc.document(journal['registration'])
    else:
        rc.require(not out.exists() or not any(out.iterdir()),'review-observation-foreign-revision-output');out.mkdir(parents=True,exist_ok=True);value=capture_normal_v2(local,new,command,request,native=native,ax=ax)
    child=rc.ref(out/('preview-registration.json' if value['state']=='awaiting-visual-review' else 'registration.json'));alias={**value,'observation_revision_contract':OBSERVATION_REVISION,'observation_revision':proof_ref,'revision_registration':child};path=Path(original['operation']['outdir'])/('preview-registration.json' if value['state']=='awaiting-visual-review' else 'registration.json')
    if path.exists():rc.require(rc.load(path)==alias,'review-observation-existing-top-registration-changed')
    else:rc.atomic(path,alias)
    verify(path,allow_preview=True);rc.atomic(state,{'state':value['state'],'operation':operation,'observation_revision':proof_ref,'prior_attempt':p['region_archive'],'registration':rc.ref(path)});return alias

def validate_attestation(v,path):
    a=rc.document(v['quality_attestation'])
    if a.get('kind')==program_review_quality.KIND:
        return program_review_quality.verify(v['quality_attestation'],v)
    preview=rc.document(a['registration_preview'])
    rc.require(a.get('kind')=='dom-review-region-quality-attestation-v1' and a.get('reviewer_role')=='supervisor' and a.get('decision')=='approved','review-region-quality-attestation-invalid')
    rc.require(preview.get('state')=='awaiting-visual-review' and a['image']==v['image'] and a['source_sha256']==v['source']['sha256'] and a['review_keys']==v['review_keys'],'review-region-quality-attestation-binding-mismatch')
    expected=dict(v);expected.pop('quality_attestation',None);expected.pop('quality_approved_at',None);expected['state']='awaiting-visual-review'
    rc.require(expected==preview,'review-region-approved-preview-changed')
    rc.require(a.get('field_visibility')==dict.fromkeys(('score','body_visible_fragment','store','customer','action'),True),'review-region-quality-fields-not-confirmed')
    rc.require(rc.authority.stamp(v['recorded_at'])<=rc.authority.stamp(a['reviewed_at'])<=rc.authority.stamp(v['quality_approved_at']),'review-region-quality-review-time-invalid')
    return a

def approve_preview(path,attestation):
    path=Path(path).resolve();verify(path,allow_preview=True);v=rc.load(path)
    rc.require(v['state']=='awaiting-visual-review','review-region-not-awaiting-visual-review')
    a=rc.document(attestation);rc.require(a.get('registration_preview')==rc.ref(path),'review-region-attestation-original-preview-required')
    source=Path(v['source']['path']);key=rc.digest({'source':v['source']['sha256'],'review_keys':sorted(v['review_keys'])});states=source.parent/'.review-region-state';state=states/(key+'.json')
    with (states/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);old=rc.load(state)
        rc.require(old.get('state')=='awaiting-visual-review' and old.get('registration')==rc.ref(path),'review-region-preview-operation-state-mismatch')
        final=path.with_name('registration.json');rc.require(not final.exists(),'review-region-final-registration-already-present')
        v.update(state='complete',quality_attestation=attestation,quality_approved_at=rc.stamp());validate_attestation(v,path)
        rc.atomic(final,v);verify(final);old.update(state='complete',registration=rc.ref(final),preview=rc.ref(path),quality_attestation=attestation);rc.atomic(state,old)
        return v

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify-preview');p.add_argument('--approve-preview');p.add_argument('--quality-attestation');p.add_argument('--manifest');p.add_argument('--outdir');p.add_argument('--pid',type=int);p.add_argument('--revision');p.add_argument('--replaces-registration');p.add_argument('--replaces-sha256');a=p.parse_args();
    if a.verify_preview:
        rc.require(not any((a.approve_preview,a.quality_attestation,a.manifest,a.outdir,a.pid,a.revision)),'review-region-verify-only-arguments-required');print(json.dumps(verify(a.verify_preview,allow_preview=True),ensure_ascii=False));return
    if a.approve_preview:
        rc.require(a.quality_attestation and not any((a.manifest,a.outdir,a.pid,a.revision)),'review-region-approve-only-arguments-required');value=approve_preview(a.approve_preview,rc.ref(a.quality_attestation));print(json.dumps({'ok':True,'registration':str(Path(a.approve_preview).with_name('registration.json')),'state':value['state']},ensure_ascii=False));return
    rc.require(all((a.manifest,a.outdir,a.pid,a.revision)),'review-region-capture-arguments-required');rc.require(bool(a.replaces_registration)==bool(a.replaces_sha256),'review-region-parent-path-and-hash-required');parent={'path':str(Path(a.replaces_registration).resolve()),'sha256':a.replaces_sha256} if a.replaces_registration else None
    value=capture(rc.load(a.manifest),a.outdir,lambda c:bridge.request(c,timeout=50),pid=a.pid,revision=a.revision,replaces=parent);print(json.dumps({'ok':True,'registration':str(Path(a.outdir).resolve()/('preview-registration.json' if value['state']=='awaiting-visual-review' else 'registration.json')),'image':value['image'],'image_scope':value['image_scope'],'state':value['state']},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(2)
