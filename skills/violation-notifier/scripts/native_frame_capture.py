#!/usr/bin/env python3
"""Violation anchor/row evidence over shared public SCK whole-window transport.
Business coverage is exclusively derived from pinned public DOM frame proofs.
No activeTab grant, image cropping, pixel actions, navigation or business progress.
"""
import argparse,fcntl,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import frame_capture as fc
import screenshot_registration as sr
import native_window_capture as transport
from visible_capture import atomic,sha,stamp
BACKEND=transport.BACKEND
POLICY=fc.POLICY
need=fc.need
ref=lambda path:{'path':str(Path(path).resolve()),'sha256':sha(path)}
def native_command(inputs,pid,key):
    cmd={'backend':BACKEND,'pid':pid,**{k:inputs['command'][k] for k in ('tabId','windowId','groupid')},'url':inputs['url'],'captureKey':key};transport.fields(cmd);return cmd

def prepare_region_request(inputs,public_proof,mode):
    """Pure request builder for the shared forthcoming dom-region-proof.
    Selectors are exclusively the original proof's derived complete elements.
    No rectangle, browser toolbar offset or replacement crop implementation here.
    """
    need(mode in ('anchor','rows'),'native-region-frame-mode-invalid');command=inputs['command'];sr.validate_public_proof(public_proof,command,inputs['url']);facts=sr.visible_facts(public_proof)
    need((facts['date_filter_visible'] and facts['list_headers_visible']) if mode=='anchor' else bool(facts['notice_ids']),'native-region-required-content-not-visible')
    elements=[e for e in public_proof['elements'] if e['fully_visible'] and (mode=='anchor' or e['kind']=='row')]
    selectors=[e['locator']['value'] for e in elements];need(selectors and len(selectors)==len(set(selectors)),'native-region-selector-coverage-invalid')
    return {'op':'dom-region-proof',**{k:command[k] for k in ('tabId','windowId','groupid')},'base':command,'selectors':selectors,'purpose':'evidence-crop-only'}

def validate_frame(image,metadata,*,source):
    m=metadata;binding=m.get('pinned_inputs',{});need(m.get('capture_backend')==BACKEND and m.get('whole_window') is True and m.get('viewport_only') is False and m.get('visibility_policy')==POLICY and m.get('frame_mode') in ('anchor','rows'),'native-frame-explicit-backend-required')
    need(binding.get('source_sha256')==source['sha256'],'native-frame-source-hash-conflict');src={'path':binding.get('source_path'),'sha256':binding.get('source_sha256')};need(sr.document(src)==sr.document(source),'native-frame-batch-source-conflict');obs={'path':binding.get('observation_path'),'sha256':binding.get('observation_sha256')};profile={'path':binding.get('profile_path'),'sha256':binding.get('profile_sha256')};inputs=fc.page_inputs(src,obs,profile);cmd=inputs['command']
    need(binding.get('command')==cmd and m.get('source_sha256')==source['sha256'] and m.get('page_scope')==inputs['scope'] and m.get('page_fingerprint')==binding.get('page_fingerprint')==inputs['page_fingerprint'] and m.get('query_fingerprint')==binding.get('query_fingerprint')==inputs['query_fingerprint'] and m.get('chain_id')==binding.get('chain_id') and m.get('frame_mode')==binding.get('frame_mode'),'native-frame-source-dom-scope-not-derived')
    pair=m.get('public_dom_proof',{});before=pair.get('before');need(set(pair)=={'before','after'} and before==pair.get('after'),'native-frame-before-after-proof-mismatch');sr.validate_public_proof(before,cmd,inputs['url']);need(before['safety_version'] in sr.SUPPORTED,'native-frame-proof-version-unreviewed')
    facts=sr.visible_facts(before);need(all(m.get(k)==value for k,value in facts.items()),'native-frame-visible-facts-not-derived')
    if m['frame_mode']=='anchor':need(facts['date_filter_visible'] and facts['list_headers_visible'],'native-frame-anchor-not-visible')
    else:need(bool(facts['notice_ids']),'native-frame-no-complete-row')
    cap=sr.document(m['capture_metadata']);native=cap.get('command');need(isinstance(native,dict),'native-frame-transport-command-required');expected=native_command(inputs,native.get('pid'),binding['captureKey']);need(native==expected,'native-frame-transport-scope-mismatch');original=Path(cap.get('png',{}).get('path',''));need(original.is_absolute(),'native-frame-original-image-required');transport.validate(cap,expected,original)
    need(Path(image).is_absolute() and sha(image)==m.get('sha256')==cap['png']['sha256'],'native-frame-png-hash-conflict');need(cap['before']['scope']==cap['after']['scope'] and cap['before']['scope']['url']==before['url'],'native-frame-transport-proof-scope-conflict')
    first=sr.when(m.get('proof_before_observed_at'));last=sr.when(m.get('proof_after_observed_at'));need(first<=sr.when(cap['intent_at'])<=sr.when(cap['captured_at'])<=sr.when(cap['completed_at'])<=last,'native-frame-dom-transport-time-conflict')
    need(binding.get('native_command')==expected,'native-frame-bound-native-command-mismatch')
    for r in (src,obs,profile,m['capture_metadata']):sr.document(r)
    return {'notice_ids':facts['notice_ids'],'version':before['safety_version'],'observed_at':cap['captured_at'],'capture_scope':cap['before']['scope'],'window_scope':cap['before']['window'],'references':[src,obs,profile,m['capture_metadata'],ref(original)],'whole_window':True,'viewport_only':False}

def _capture(source_ref,observation_ref,profile_ref,*,pid,mode,chain_id,key,out,request,native=None):
    inputs=fc.page_inputs(source_ref,observation_ref,profile_ref);cmd=inputs['command'];need(mode in ('anchor','rows'),'native-frame-mode-invalid');ncmd=native_command(inputs,pid,key);out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True);registration=out.with_suffix('.native-frame.json');need(not registration.exists(),'native-frame-output-exists')
    before=fc.proof(cmd,inputs['url'],request);facts=sr.visible_facts(before)
    need((facts['date_filter_visible'] and facts['list_headers_visible']) if mode=='anchor' else bool(facts['notice_ids']),'native-frame-required-content-not-visible')
    before_at=stamp();result=transport.write_capture(ncmd,out,request,native);need(result.get('ok') is True,'native-frame-transport-failed');after=fc.proof(cmd,inputs['url'],request);after_at=stamp();need(before==after,'native-frame-public-dom-changed-during-capture')
    binding={'source_path':source_ref['path'],'source_sha256':source_ref['sha256'],'observation_path':observation_ref['path'],'observation_sha256':observation_ref['sha256'],'profile_path':profile_ref['path'],'profile_sha256':profile_ref['sha256'],'command':cmd,'native_command':ncmd,'captureKey':key,'chain_id':chain_id,'frame_mode':mode,'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint']}
    metadata={'source':'local-dom-bridge','source_sha256':source_ref['sha256'],'sha256':sha(out),'capture_backend':BACKEND,'visibility_policy':POLICY,'whole_window':True,'viewport_only':False,'frame_mode':mode,'chain_id':chain_id,'pinned_inputs':binding,'page_scope':inputs['scope'],'page_fingerprint':inputs['page_fingerprint'],'query_fingerprint':inputs['query_fingerprint'],'public_dom_proof':{'before':before,'after':after},'capture_metadata':ref(result['result']['metadata']),'proof_before_observed_at':before_at,'proof_after_observed_at':after_at,**facts}
    validate_frame(str(out),metadata,source=source_ref);atomic(registration,metadata);return {'image':str(out),'metadata':str(registration),'whole_window':True,'viewport_only':False,'business_progress_changed':False}

def capture(source_ref,observation_ref,profile_ref,*,pid,mode,chain_id,key,out,request=None,native=None):
    inputs=fc.page_inputs(source_ref,observation_ref,profile_ref);need(isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'native-frame-chain-id-invalid');native_command(inputs,pid,key);request=request or fc.vc.bridge.request
    folder=Path(source_ref['path']).resolve().parent/'.native-frame-capture-state';folder.mkdir(parents=True,exist_ok=True);file=folder/(fc.fingerprint([source_ref['sha256'],chain_id])+'.json');scope={'source_sha256':source_ref['sha256'],'profile_sha256':profile_ref['sha256'],'chain_id':chain_id}
    with file.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);state=json.loads(file.read_text()) if file.exists() else {'scope':scope,'frames':[]};need(state.get('scope')==scope,'native-frame-chain-scope-conflict');need(all(e['state']=='complete' for e in state['frames']),'native-frame-prior-unknown-no-new-key');need(not any(e['captureKey']==key or e['out']==str(Path(out).resolve()) for e in state['frames']),'native-frame-existing-intent-no-replay')
        entry={'state':'unknown','captureKey':key,'mode':mode,'out':str(Path(out).resolve())};state['frames'].append(entry);atomic(file,state)
        try:
            result=_capture(source_ref,observation_ref,profile_ref,pid=pid,mode=mode,chain_id=chain_id,key=key,out=out,request=request,native=native);entry.update(state='complete',metadata=ref(result['metadata']));atomic(file,state);return result
        except Exception as error:entry['error']=str(error);atomic(file,state);raise

def validate_chain(manifest,*,source,company,groupid,start,end_exclusive,notice_ids):
    need(manifest.get('capture_backend')==BACKEND and manifest.get('visibility_policy')==POLICY and manifest.get('source_sha256')==source['sha256'],'native-frame-chain-scope-invalid');frames=manifest.get('frames');need(isinstance(frames,list) and bool(frames),'native-frame-chain-empty');src=sr.document(source);need(src['company']==company and str(src['groupid'])==str(groupid) and src['start']==start and src['end_exclusive']==end_exclusive and {r['notice_id'] for r in src['records']['rows']}==set(notice_ids),'native-frame-chain-source-conflict')
    pages={};entries=[];covered=set();keys=set();profile_sha=None;query=None;version=None;previous_page=0;last_time=None;last_epoch=None;chain_id=manifest.get('chain_id');need(isinstance(chain_id,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id),'native-frame-chain-id-invalid')
    for frame in frames:
        m=sr.document(frame['metadata']);need(m['chain_id']==chain_id,'native-frame-chain-id-conflict');checked=validate_frame(frame['image'],m,source=source);page=m['page_scope']['page'];mode=m['frame_mode'];binding=m['pinned_inputs'];key=binding['captureKey'];need(key not in keys,'native-frame-capture-key-duplicate');keys.add(key)
        if query is None:query=m['query_fingerprint'];profile_sha=binding['profile_sha256'];version=checked['version']
        need(query==m['query_fingerprint'] and profile_sha==binding['profile_sha256'] and version==checked['version'],'native-frame-chain-query-profile-version-changed')
        if page not in pages:
            need(mode=='anchor' and page==previous_page+1,'native-frame-page-anchor-required');need(not previous_page or not pages[previous_page]['last_page'],'native-frame-page-after-final');ids=[r['notice_id'] for r in m['page_scope']['page_rows']];need(not any(i in old['ids'] for old in pages.values() for i in ids),'native-frame-id-repeated-across-pages');pages[page]={'fingerprint':m['page_fingerprint'],'ids':ids,'last_page':m['page_scope']['last_page'],'scope':checked['capture_scope'],'window':checked['window_scope']};previous_page=page;last_epoch=None
        need(page==previous_page and m['page_fingerprint']==pages[page]['fingerprint'] and checked['capture_scope']==pages[page]['scope'] and checked['window_scope']==pages[page]['window'],'native-frame-old-anchor-or-window-reused');at=sr.when(checked['observed_at']);epoch=m['public_dom_proof']['before']['epoch'];need((last_time is None or at>=last_time) and (last_epoch is None or epoch>=last_epoch),'native-frame-time-or-dom-epoch-reset');last_time=at;last_epoch=epoch;covered.update(checked['notice_ids']);entries.append({'image':{'path':frame['image'],'sha256':m['sha256']},'metadata':frame['metadata'],'references':checked['references'],'notice_ids':checked['notice_ids'],'frame_mode':mode,'page':page})
    need(pages[previous_page]['last_page'] and {i for p in pages.values() for i in p['ids']}==set(notice_ids) and covered==set(notice_ids),'native-frame-chain-full-page-row-coverage-incomplete');return {'entries':entries,'notice_ids':sorted(covered),'visibility_policy':POLICY,'chain_id':chain_id,'capture_backend':BACKEND,'whole_window':True,'viewport_only':False}

def assemble(source_ref,metadata_paths,out):
    src=sr.document(source_ref);frames=[];chain_id=None
    for path in metadata_paths:
        m=sr.document(ref(path));cap=sr.document(m['capture_metadata']);chain_id=chain_id or m['chain_id'];need(chain_id==m['chain_id'],'native-frame-assemble-chain-conflict');frames.append((sr.when(cap['captured_at']),{'image':cap['png']['path'],'metadata':ref(path)}))
    manifest={'capture_backend':BACKEND,'visibility_policy':POLICY,'source_sha256':source_ref['sha256'],'chain_id':chain_id,'frames':[f for _,f in sorted(frames,key=lambda x:x[0])]};validate_chain(manifest,source=source_ref,company=src['company'],groupid=src['groupid'],start=src['start'],end_exclusive=src['end_exclusive'],notice_ids=[r['notice_id'] for r in src['records']['rows']]);out=Path(out).resolve();need(not out.exists(),'native-frame-manifest-exists');atomic(out,manifest);return ref(out)

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='op',required=True);c=sub.add_parser('capture')
    for key in ('source','source-sha256','observation','observation-sha256','profile','profile-sha256','pid','mode','chain-id','key','out'):c.add_argument('--'+key,required=True)
    c.add_argument('--historical-whole-window',action='store_true',help='Historical evidence only; never eligible for final send')
    a=sub.add_parser('assemble');a.add_argument('--source',required=True);a.add_argument('--source-sha256',required=True);a.add_argument('--frames',nargs='+',required=True);a.add_argument('--out',required=True);v=p.parse_args();r=lambda path,h:{'path':str(Path(path).resolve()),'sha256':h}
    if v.op=='capture':need(v.historical_whole_window,'region-only-final-evidence-required-use-shared-region-adapter')
    result=assemble(r(v.source,v.source_sha256),v.frames,v.out) if v.op=='assemble' else capture(r(v.source,v.source_sha256),r(v.observation,v.observation_sha256),r(v.profile,v.profile_sha256),pid=int(v.pid),mode=v.mode,chain_id=v.chain_id,key=v.key,out=v.out)
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
