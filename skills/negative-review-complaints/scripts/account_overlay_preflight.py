#!/usr/bin/env python3
"""Typed one-shot account hover exit before review capture. Never captures pixels."""
import argparse,fcntl,hashlib,json,re,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/chrome-dom-export/scripts'))
import bridge,review_region_capture as region
rc=region.rc
CONTENT=PROJECT/'skills/chrome-dom-export/extension/content.js'
RUNTIME=PROJECT/'runtime/negative-review-complaints/account-hover-preflight'

def need(v,code):
    if not v:raise ValueError(code)
def now():return datetime.now(timezone.utc).isoformat()
def canonical(p):
    p=Path(p);need(p.is_absolute() and p==p.resolve() and not p.is_symlink() and not any(x.is_symlink() for x in p.parents),'overlay-canonical-path-required');return p
def ref(p):return {'path':str(canonical(p)),'sha256':rc.sha(p)}
def document(r):canonical(r['path']);return rc.document(r)
def immutable(p,v):
    if p.exists():need(rc.load(p)==v,'overlay-immutable-evidence-conflict')
    else:rc.atomic(p,v)
    return ref(p)
def no_capture_unknown(source):
    for name in ('.review-capture-state','.review-region-state'):
        for p in (source.parent/name).glob('*.json'):
            s=rc.load(p);need(s.get('state') in ('complete','awaiting-visual-review'),'overlay-capture-intent-unresolved')
def content_identity():
    raw=CONTENT.read_text();build=re.findall(r"const BUILD='([^']+)'",raw);need(len(build)==1,'overlay-content-build-invalid');return {'file':ref(CONTENT),'build':build[0],'version':rc.visible_capture.SAFETY}
def derive(manifest):
    base=rc.command_from_inputs(*(manifest[k] for k in ('job','source','envelope','profile','page')),manifest['review_keys']);source=document(manifest['source']);job=document(manifest['job']);need(source['identity']==job['identity'],'overlay-source-job-identity-conflict')
    scope={k:base[k] for k in ('tabId','windowId','groupid')};page=document(manifest['page']);url=page['tab']['url'];need(page['tab']['windowId']==scope['windowId'],'overlay-source-window-conflict')
    return base,source,scope,url

def card(tree,identity,*,required=False):
    need(tree.get('truncated') is False,'overlay-complete-tree-required');nodes=rc.normal.flatten(tree['root'])
    need(not any(n.get('role')=='dialog' or n.get('attributes',{}).get('aria-modal')=='true' or 'byted-drawer-dialog-show' in n.get('attributes',{}).get('class','').split() for n in nodes),'overlay-dialog-present')
    cards=[n for n in nodes if any(c.startswith(('src-components-HeaderV2-components-UserCard-index-module__outer--','src-components-HeaderV3-components-UserCard-index-module__outer--')) for c in n.get('attributes',{}).get('class','').split())]
    triggers=[n for n in nodes if any(c.startswith(('src-components-HeaderV2-components-Profile-index-module__title--','src-components-HeaderV3-components-Profile-index-module__title--')) for c in n.get('attributes',{}).get('class','').split()) and n.get('name')==identity['provider']]
    need(len(triggers)==1,'overlay-provider-trigger-not-unique')
    if not cards:need(not required,'overlay-required-card-absent');return None,triggers[0]
    need(len(cards)==1,'overlay-card-not-unique');rc.normal.public_identity(tree,identity)
    selected=cards[0];version='V2' if 'HeaderV2' in selected['attributes']['class'] else 'V3'
    need('Header'+version in triggers[0]['attributes']['class'],'overlay-card-trigger-version-conflict')
    wrappers=[n for n in nodes if any(c.startswith('src-components-Header'+version+'-components-Profile-index-module__wrap-profile--') for c in n.get('attributes',{}).get('class','').split()) and all(x in rc.normal.flatten(n) for x in (selected,triggers[0]))]
    need(len(wrappers)==1,'overlay-card-wrapper-unverified');names=[n.get('name') for n in rc.normal.flatten(selected)]
    need(all(x in names for x in ('账户ID','我的客户经理','退出登录')) and ('切换公司' in names or '切换' in names),'overlay-card-public-signature-invalid')
    return selected,triggers[0]
def command(scope,identity,trigger):return {'op':'hover','kind':'account-hover-exit','tabId':scope['tabId'],'groupid':scope['groupid'],'locator':{'by':'selector','value':trigger['selector']},'value':identity}
def validate_reply(reply):
    need(reply.get('ok') is True,'overlay-hover-reply-failed');r=reply.get('result',{})
    need(r=={'action':'account-hover-exit-events-dispatched','event_sequence':['card:mouseout','card:mouseleave','wrapper:mouseleave'],'related_target':'document.body','trusted_event_fabrication':False,'business_clicks':False,'closure_verified':False,'requires_readonly_tree_recheck':True},'overlay-hover-reply-unreviewed')
def blocker(reply):
    need(reply.get('ok') is False and isinstance(reply.get('error'),str) and reply['error'].startswith('region-painted-external-overlap:'),'overlay-not-known-region-blocker')
    d=json.loads(reply['error'].split(':',1)[1]);need(d.get('tag')=='DIV' and type(d.get('selector')) is str and len(d['selector'])<3000 and 'UserCard-index-module__outer--' in d.get('class',''),'overlay-blocker-not-usercard');return d

def ensure(manifest_ref,request=None,*,adopt=None):
    manifest=document(manifest_ref);base,source,scope,url=derive(manifest);source_path=canonical(manifest['source']['path']);no_capture_unknown(source_path);code=content_identity();request=request or (lambda c:bridge.request(c,timeout=50))
    binding={'source':manifest['source'],'job':manifest['job'],'profile':manifest['profile'],'envelope':manifest['envelope'],'identity':source['identity'],'scope':scope,'url':url,'content':code};directory=canonical(RUNTIME);directory.mkdir(parents=True,exist_ok=True);key=rc.digest({'source_sha256':manifest['source']['sha256'],**scope,'identity':source['identity']});path=directory/(key+'.json')
    with (directory/'.source.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);no_capture_unknown(source_path)
        for p in directory.glob('*.json'):
            if p!=path:need(rc.load(p).get('state')=='complete','overlay-other-source-intent-unresolved')
        state=rc.load(path) if path.exists() else {'kind':'review-account-overlay-preflight-v1','binding':binding,'created_at':now(),'state':'preflight','attempts':[]}
        if state.get('kind')=='review-account-overlay-preflight-v1' and state.get('binding')!=binding and state.get('state')=='unknown':
            # Reviewed content-script advance (W96): the recorded reply proves the
            # original hover was rejected BEFORE any event dispatch, so the intent
            # never executed; the safety epoch (version/build) is unchanged.
            stored=state.get('reply');need(type(stored) is dict,'overlay-original-binding-required');recorded=document(stored)
            old_content=state['binding'].get('content',{})
            need(old_content.get('version')==binding['content']['version'] and old_content.get('build')==binding['content']['build'] and old_content.get('file',{}).get('path')==binding['content']['file']['path'],'overlay-original-binding-required')
            need(recorded.get('command')==state.get('command') and recorded.get('response',{}).get('ok') is False and recorded.get('response',{}).get('error')=='account-dismiss-card-fields-missing','overlay-original-binding-required')
            state['original_binding']=state['binding'];state['binding']=binding;rc.atomic(path,state)
        need(state.get('kind')=='review-account-overlay-preflight-v1' and state['binding']==binding and state.get('state') in ('preflight','unknown','await-readonly-close','complete'),'overlay-original-binding-required')
        if state.get('state') in ('unknown','await-readonly-close'):need(isinstance(state.get('command'),dict),'overlay-unresolved-command-missing')
        intent_path=directory/key/'hover-intent.json'
        if intent_path.exists():
            intent=document(ref(intent_path));same_epoch=intent.get('binding',{}).get('content',{}).get('version')==binding['content']['version'] and intent.get('binding',{}).get('content',{}).get('build')==binding['content']['build']
            need(same_epoch and intent.get('binding',{}).get('scope')==binding['scope'] and intent.get('command')==state.get('command'),'overlay-original-intent-mismatch')
        attempt=uuid.uuid4().hex;folder=directory/key/'attempts'/attempt;folder.mkdir(parents=True);audit={'attempt':attempt,'manifest':manifest_ref,'at':now(),'raw':[]};state['attempts'].append(audit)
        def save():rc.atomic(path,state)
        def raw(c,label):
            no_capture_unknown(source_path);need(document(manifest_ref)==manifest,'overlay-manifest-changed')
            for name in ('source','job','profile','envelope','page'):need(rc.sha(manifest[name]['path'])==manifest[name]['sha256'],'overlay-input-reference-changed')
            need(ref(CONTENT)==code['file'],'overlay-content-file-changed')
            try:response=request(c)
            except Exception as e:
                audit['raw'].append(immutable(folder/(str(len(audit['raw'])).zfill(2)+'-'+label+'-exception.json'),{'command':c,'exception':{'type':type(e).__name__,'message':str(e)},'observed_at':now()}));save();raise
            r=immutable(folder/(str(len(audit['raw'])).zfill(2)+'-'+label+'.json'),{'command':c,'response':response,'observed_at':now()});audit['raw'].append(r);save();return response
        def ok(c,label):
            response=raw(c,label);need(response.get('ok') is True,'overlay-read-failed:'+label);return response['result']
        def fresh(label):
            tabs=ok({'op':'tabs'},label+'-tabs-before');focused=[w for w in tabs if w.get('focused') is True];need(len(focused)==1 and focused[0].get('windowId')==scope['windowId'],'overlay-window-focus-conflict');active=[t for t in focused[0].get('tabs',[]) if t.get('active') is True];need(len(active)==1,'overlay-active-tab-not-unique');tab=active[0]
            need(all(tab.get(k)==scope[k] for k in ('tabId','windowId')) and tab.get('url')==url and tab.get('allowed') is True,'overlay-tab-scope-conflict')
            ping=ok({'op':'ping','tabId':scope['tabId']},label+'-ping');need(ping.get('version')==code['version'] and ping.get('content_build')==code['build'] and ping.get('safety')=='DOM-only','overlay-content-policy-not-loaded')
            tree=ok({'op':'tree','tabId':scope['tabId']},label+'-tree');page={'tab':tab,'tree':tree,'observed_at':now()};rc.normal.context(page,scope['groupid']);rc.normal.navigation_probe(tree,document(manifest['job']),text_schema=document(manifest['profile']).get('text_schema'))
            tabs2=ok({'op':'tabs'},label+'-tabs-after');need(tabs2==tabs,'overlay-tabs-changed-during-read');return tree
        save()
        try:
            before=fresh('before');current_card,trigger=card(before,source['identity']);ready_proof=None;observed_absent=current_card is None
            if adopt is not None:
                old=document(adopt);need(not state.get('command') or state.get('adopted_intent')==adopt,'overlay-adoption-conflict');need(old.get('state')=='confirmed' and old.get('source_sha256')==manifest['source']['sha256'],'overlay-adoption-original-required');oldraw=document(old['before']);need(oldraw.get('ok') is True,'overlay-adoption-before-invalid');oldtree=oldraw['result'];rc.normal.context({'tab':document(manifest['page'])['tab'],'tree':oldtree,'observed_at':now()},scope['groupid']);_,oldtrigger=card(oldtree,source['identity'],required=True);expected=command(scope,source['identity'],oldtrigger);need(old.get('command')==expected,'overlay-adoption-command-conflict');validate_reply(old['reply']);state.update(command=expected,adopted_intent=adopt,state='await-readonly-close');save()
            if state.get('command'):
                need(state['command']==command(scope,source['identity'],trigger),'overlay-original-command-changed')
                if current_card is None:pass
                else:
                    # The recorded reply proves a pre-dispatch content rejection;
                    # re-dispatch the exact reviewed command once, then prove closure.
                    stored=state.get('reply');need(type(stored) is dict,'overlay-original-events-unclosed-no-replay');recorded=document(stored)
                    need(recorded.get('command')==state['command'] and recorded.get('response',{}).get('ok') is False and recorded.get('response',{}).get('error')=='account-dismiss-card-fields-missing','overlay-original-events-unclosed-no-replay')
                    reply=raw(state['command'],'hover-reply');state['reply']=audit['raw'][-1];save();validate_reply(reply);state['state']='await-readonly-close';save()
                    after=fresh('after');after_card,_=card(after,source['identity']);need(after_card is None,'overlay-events-did-not-close-no-replay');observed_absent=True
            elif current_card is not None:
                failed=raw(region.region_command(base),'region-before')
                if failed.get('ok') is True:
                    region.checked(failed,region.region_command(base));ready_proof=failed
                else:
                    d=blocker(failed);matched=ok({'op':'find','tabId':scope['tabId'],'locator':{'by':'selector','value':d['selector']}},'blocker-find');need(len(matched)==1 and matched[0].get('selector')==current_card['selector'] and matched[0].get('attributes',{}).get('class')==current_card['attributes']['class'],'overlay-blocker-card-not-same')
                    cmd=command(scope,source['identity'],trigger);state.update(command=cmd,state='unknown',intent_at=now(),original_manifest=manifest_ref);save()
                    state['input_intent']=immutable(intent_path,{'binding':binding,'command':cmd,'before':list(audit['raw']),'at':state['intent_at']});save()
                    reply=raw(cmd,'hover-reply');state['reply']=audit['raw'][-1];save();validate_reply(reply);state['state']='await-readonly-close';save()
                    after=fresh('after');after_card,_=card(after,source['identity']);need(after_card is None,'overlay-events-did-not-close-no-replay');observed_absent=True
            proof=ready_proof or raw(region.region_command(base),'region-after');region.checked(proof,region.region_command(base));state.update(state='complete',completed_at=now(),closure_verified=observed_absent,completion_kind='readonly-original-intent-reconciled' if state.get('command') else 'readonly-region-ready',after_full_identity_rechecked=False,identity_basis='fresh-before-full-card-if-present-and-pinned-source',last_ready_manifest=manifest_ref);save();return {'ready':True,'journal':ref(path),'manifest':manifest_ref,'capture_key':manifest['capture_key'],'input_events_dispatched':not adopt and any(read['path'].endswith('hover-reply.json') for read in audit['raw']),'adopted':adopt is not None,'closure_verified':observed_absent,'after_full_identity_rechecked':False,'capture_attempted':False}
        except Exception as e:audit['error']={'at':now(),'code':str(e)};save();raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--adopt-intent');p.add_argument('--adopt-intent-sha256');a=p.parse_args()
    try:
        need(bool(a.adopt_intent)==bool(a.adopt_intent_sha256),'overlay-adoption-paired-ref-required');print(json.dumps(ensure({'path':a.manifest,'sha256':a.manifest_sha256},adopt={'path':a.adopt_intent,'sha256':a.adopt_intent_sha256} if a.adopt_intent else None),ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
