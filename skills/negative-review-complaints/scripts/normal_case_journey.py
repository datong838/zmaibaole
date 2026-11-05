#!/usr/bin/env python3
"""Bounded original-source/original-inspection page journey, never complaint actions.
A collection edge is not reused: each case has one canonical immutable journey.
"""
import sys,json,hashlib,fcntl,uuid,copy,argparse
from pathlib import Path
import normal_paging_runner as c
p=c.p;need=c.need
import existing_result_runner as results
KIND='normal-existing-case-page-journey-v1'
def result_path(m):return Path(m['root'])/'existing-result-operations'/hashlib.sha256(m['review_key'].encode()).hexdigest()/m['inputs']['source']['sha256']/'operation.json'
def casecodes():return {**c.codes(),str(Path(__file__).resolve()):c.ref(__file__)['sha256'],str(Path(results.__file__).resolve()):c.ref(results.__file__)['sha256']}
def inputs(inspect_ref):
 m=c.document(inspect_ref);v,order,row=results.manifest_inputs(m);need(v['_ledger'].get('workspace_kind')=='negative-review-appeal-history-only-v1' and v['profile'].get('contract')==p.CONTRACT and (v['profile'].get('status')=='live-validated'or v['source'].get('kind')=='history-partial-normal-source-v1'and v['profile'].get('pending_card_policy')=='history-unresolved-store-v1') and not m.get('completed_operation'),'case-journey-current-history-source-required');return m,v,order,row
def prepare(inspect_ref):
 m,v,order,row=inputs(inspect_ref);root=Path(m['root']).resolve();folder=root/'normal-case-page-journeys'/hashlib.sha256(m['review_key'].encode()).hexdigest();folder.mkdir(parents=True,exist_ok=True)
 with (folder/'.lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);base=folder/m['inputs']['source']['sha256'];mp=base/'manifest.json';active=folder/'active.json'
  if mp.exists():
   q=c.ref(mp);old=c.document(q);need(old['inspection']==inspect_ref,'case-journey-original-inspection-required');CaseRunner(q).guard();return q
  if active.exists():
   old=c.document(c.ref(active));prev=CaseRunner(old['manifest']);prev.guard();need(prev.s.get('state')=='complete','case-journey-prior-unfinished-no-new-version');prior_m,prior_v,prior_o,prior_row=inputs(prev.m['inspection']);op=c.document(c.ref(result_path(prior_m)));results.verify_complete(op,prior_m,prior_v,prior_o,prior_row)
  path=result_path(m)
  if path.exists():need(c.document(c.ref(path)).get('state') in ('preflight','open-ready'),'case-journey-result-already-open-or-unknown')
  base.mkdir(exist_ok=True);page=v['page'];need(type(page['tab'].get('windowId')) is int,'case-journey-window-required');m2={'kind':KIND,'inspection':inspect_ref,'root':str(root),'review_key':m['review_key'],'source':m['inputs']['source'],'tab_id':page['tab']['tabId'],'window_id':page['tab']['windowId'],'target_page':row['page_index'],'code':casecodes(),'created_at':c.now()};mr=c.publish(mp,m2);c.save(base/'operation.json',{'kind':KIND,'manifest':mr,'state':'running','phase':'read-first','calls':[],'created_at':c.now()});c.save(active,{'manifest':mr});return mr
ROUTE_KIND='supervisor-history-only-verified-navigation-superset-v1'
def route_inputs(m,v,route_refs):
 """Validate an owned immutable superset for navigation, never case admission."""
 import history_workspace as h
 need(set(route_refs)=={'job','source','envelope','profile'} and route_refs['job']==m['inputs']['job'],'case-route-exact-inputs')
 state=h.load(m['root']);entry=state['sources'].get(route_refs['source']['sha256']);need(entry is not None and entry['inputs']==route_refs,'case-route-owned-source-required')
 rv=h._inputs(state,route_refs);need(rv['job']==v['job'] and rv['source'].get('kind')=='history-partial-normal-source-v1' and v['source'].get('kind')=='history-partial-normal-source-v1','case-route-history-only-scope')
 before=v['envelope'];after=rv['envelope'];n=len(before['pages'])
 need(len(after['pages'])>n and after['pages'][:n]==before['pages'] and after['stable_page_pairs'][:n]==before['stable_page_pairs'] and after['identity_evidence']==before['identity_evidence'],'case-route-original-page-prefix')
 need(rv['source']['proofs'][:n]==v['source']['proofs'] and rv['source']['filtered_count']==v['source']['filtered_count'],'case-route-original-proof-prefix')
 need({k:x for k,x in rv['profile'].items() if k not in ('status','terminal_layout')}=={k:x for k,x in v['profile'].items() if k not in ('status','terminal_layout')},'case-route-profile-semantic-change')
 for row in v['source']['rows']:need([r for r in rv['source']['rows']if r['review_id']==row['review_id']]==[row],'case-route-original-case-changed')
 # May use only pages that contain at least one already-verified existing-result
 # row; no fabricated row is supplied merely to pass the case verifier.
 need({r['page_index']for r in rv['source']['rows']}==set(range(1,len(after['pages'])+1)),'case-route-no-existing-result-anchor-on-page')
 return rv

def route_review(mref,m,state,review,original=None,source_successor=None):
 need(review.get('kind')==ROUTE_KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('navigation_only') is True and review.get('new_case_admission') is False,'case-route-root-review-required')
 need(review['manifest']==mref and review['inspection']==m['inspection'] and review['original_source']==m['source'],'case-route-original-manifest')
 old=c.document(original or review['operation_before']);need(old.get('manifest')==mref and old['state']=='hold' and old['phase']=='read-first' and old.get('error')=='case-journey-page-outside-normal-source' and old.get('calls')==[] and old.get('latest_page')==review['hold_page'],'case-route-original-read-only-hold')
 im,v,order,row=inputs(m['inspection']);rv=route_inputs(im,v,review['route_inputs']);need(rv['source']['rows'] and row in v['source']['rows'],'case-route-original-case-required')
 raw=c.document(review['hold_page']);_,tree=p.n.context(raw,v['job']['groupid']);lst=p.n.one(p.n.flatten(tree['root']),{'attributes':{'class':p.LIST}},'case-route-hold-list');index=p.pager(lst['children'][-1])['page'];anchors=[r for r in rv['source']['rows']if r['page_index']==index];need(anchors,'case-route-observed-page-uncovered');p.current_page_for_case(raw,v['job'],rv['envelope'],rv['profile'],rv['source'],anchors[0])
 before=review['code_before'];after=review['code_after'];target=str(ROOT_CASE_PATH)
 graph_changed={str(c.ROOT/'skills/negative-review-complaints/scripts'/name)for name in('normal_case_journey.py','normal_paging.py','existing_result_runner.py')};external=str(c.ROOT/'skills/negative-review-complaints/scripts/history_workspace.py');allowed=graph_changed|{external}
 need(before==m['code'] and set(after)==set(before) and {k for k in before if before[k]!=after[k]}==graph_changed,'case-route-exact-three-graph-slots')
 release=c.document(review['source_release']);ts=release.get('targets',[]);need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published') is True and release.get('test_projection_only') is False and release.get('reviewed_by')=='workshop-director' and len(ts)==4 and {t['target']for t in ts}==allowed,'case-route-exact-published-sources')
 for t in ts:
  need(t['mode']==420 and t['before']['path']==str(Path(review['source_release']['path']).parent/(Path(t['target']).name+'.before')) and c.ref(t['before']['path'])==t['before'] and t['before']['sha256']==t['old_sha256'] and _terminal_physical_hash(t['target'],source_successor)==t['after']['sha256'],'case-route-exact-before-and-after')
  if t['target']in graph_changed:need(t['old_sha256']==before[t['target']] and t['after']['sha256']==after[t['target']],'case-route-source-vector-binding')
 need(all(_terminal_physical_hash(k,source_successor)==x for k,x in after.items()),'case-route-source-physical-mismatch')
 return rv,after,old
ROOT_CASE_PATH=c.ROOT/'skills/negative-review-complaints/scripts/normal_case_journey.py'

TERMINAL_KIND='supervisor-verified-terminal-previous-preaction-rejection-v1'
TERMINAL_BUILD='normal-review-terminal-pagination-v3'
TERMINAL_ERROR='unreviewed terminal normal previous only'

def _terminal_source_successor(review):
 release=c.document(review['source_release']);ts=release.get('targets',[]);allowed={str(ROOT_CASE_PATH),str(c.ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py'),str(c.ROOT/'skills/chrome-dom-export/extension/content.js')}
 need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published') is True and release.get('test_projection_only') is False and release.get('reviewed_by')=='workshop-director' and len(ts)==3 and {t['target']for t in ts}==allowed,'terminal-previous-three-published-sources')
 for t in ts:
  need(t['mode']==420 and t['before']['path']==str(Path(review['source_release']['path']).parent/(Path(t['target']).name+'.before')) and c.ref(t['before']['path'])==t['before'] and t['before']['sha256']==t['old_sha256'] and c.ref(t['target'])['sha256']==t['after']['sha256'],'terminal-previous-exact-source-before-after')
 return {t['target']:t['old_sha256']for t in ts},{t['target']:t['after']['sha256']for t in ts}

def _terminal_physical_hash(path,review):
 if review is None:return c.ref(path)['sha256']
 before,after=_terminal_source_successor(review)
 return before[str(path)]if str(path)in before else c.ref(path)['sha256']

def _terminal_clock(review,now=None):
 now=now or c.datetime.now(c.timezone.utc);issued=c.datetime.fromisoformat(review['issued_at']);expires=c.datetime.fromisoformat(review['expires_at'])
 need(issued.tzinfo is not None and expires.tzinfo is not None and 0<(expires-issued).total_seconds()<=900 and issued<=now<=expires,'terminal-previous-opportunity-expired')

def _terminal_opportunity_budget(review,index,source_index):
 enabled=index==source_index
 need(type(review.get('maximum_new_opportunities')) is int and review['maximum_new_opportunities']==(1 if enabled else 0) and review.get('one_new_input_authorized') is enabled,'terminal-previous-single-opportunity-budget')

def terminal_previous_facts(mref,m,review,original=None,*,check_time=False):
 need(review.get('kind')==TERMINAL_KIND and review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('navigation_only') is True and review.get('old_key_replay') is False and review.get('new_case_admission') is False,'terminal-previous-root-review')
 need(review['manifest']==mref and review['inspection']==m['inspection'] and review['original_source']==m['source'],'terminal-previous-original-manifest')
 original=original or review['operation_before'];need(original['sha256']==review['operation_before']['sha256'],'terminal-previous-original-archive-sha');old=c.document(original)
 need(old['manifest']==mref and old['state']=='unknown' and old['phase']=='adjacent-click' and old.get('error')=='paging-bridge-read-or-action-failed' and len(old['calls'])==1 and old['calls'][0]['state']=='unknown' and old.get('route_source_adoption'),'terminal-previous-exact-original-unknown')
 call=old['calls'][0];source_index=old['first_proof']['pager']['page'];target_index=source_index-1;need(source_index>1 and review['denied_key']==call['key'] and call['expected_page']==target_index and call['key']==mref['sha256']+':'+str(source_index)+'->'+str(target_index) and call['command']['op']=='click' and call['command']['kind']=='navigation' and call['command']['tabId']==m['tab_id'],'terminal-previous-original-navigation-command')
 transport=c.document(old['transport'][-1]);need(transport['command']==call['command'] and transport['reply']=={'ok':False,'error':TERMINAL_ERROR,'result':None} and review['denied_reply']==old['transport'][-1],'terminal-previous-explicit-preaction-reply')
 routeproof=c.document(old['route_source_adoption']);routeauth=c.document(routeproof['review']);rv,effective,_=route_review(mref,m,old,routeauth,routeproof['operation_archive'],source_successor=review)
 before,after=_terminal_source_successor(review);need(all(effective.get(k)==v for k,v in before.items()),'terminal-previous-exact-inherited-source-graph')
 content=next(t for t in c.document(review['source_release'])['targets']if t['target'].endswith('/content.js'));text=Path(content['before']['path']).read_text()
 need(text.count("throw Error('unreviewed terminal normal previous only')")==1 and "const e=one(m.locator);const rule=assertSafe(e,m.kind);\n        e.click();"in text,'terminal-previous-listener-before-click')
 sw=c.ROOT/'skills/chrome-dom-export/extension/sw.js';need(review['listener_transport']==c.ref(sw),'terminal-previous-listener-transport-source');swtext=sw.read_text();need("if(!r?.ok) throw Error(r?.error || 'content script unavailable')"in swtext and "response={ok:false,error:String(e.message || e)}"in swtext,'terminal-previous-exact-error-propagation')
 page=c.document(call['from_page']);rows=[x for x in rv['source']['rows']if x['page_index']==source_index];need(rows,'terminal-previous-page-anchor');proof=p.current_page_for_case(page,rv['job'],rv['envelope'],rv['profile'],rv['source'],rows[0]);need(proof['terminal_boundary'] and proof['pager']['page']==source_index and call['command']['locator']=={'by':'selector','value':proof['pager']['previous_selector']},'terminal-previous-original-terminal-previous')
 # A real diagnostic is immutable evidence, not a fabricated absolute timestamp.
 # Parser comparison uses the prior source time only as a lower-bound witness;
 # the NEW operation itself still performs two independent fresh scopes.
 diagnostic=c.document(review['diagnostic_result']);intent=c.document(review['diagnostic_intent']);raw=c.document(review['diagnostic_response']);prior_outer=c.document(review['prior_attempt_outer']);prior_result=c.document(review['prior_attempt_result']);need(prior_result.get('last_state')=='unknown' and prior_result.get('last_error')=='paging-bridge-read-or-action-failed' and type(prior_result.get('elapsed_seconds'))in(int,float) and prior_result['elapsed_seconds']>0 and type(intent.get('at_monotonic'))in(int,float) and intent['at_monotonic']>=prior_outer['start_monotonic']+prior_result['elapsed_seconds'],'terminal-previous-diagnostic-after-original-attempt');need(diagnostic['exit_code']==0 and diagnostic['response']==review['diagnostic_response'] and diagnostic.get('operation_unchanged') is True and intent['operation_before']==review['operation_before'] and intent.get('one_request_only') is True,'terminal-previous-native-readonly-diagnostic')
 rr=raw.get('result');need(raw.get('ok') is True and isinstance(rr,dict) and rr.get('schema')=='readonly-scope-v1' and rr.get('scope')=={'tabId':m['tab_id'],'windowId':m['window_id']} and rr.get('commands')==[{'op':'tabs'},{'op':'ping','tabId':m['tab_id']},{'op':'tree','tabId':m['tab_id']},{'op':'tabs'}],'terminal-previous-diagnostic-scope')
 tabs=lambda windows:[t for w in windows for t in w.get('tabs',[])if t.get('tabId')==m['tab_id']]
 b=tabs(rr['before']);need(len(b)==1 and b==tabs(rr['after']) and b[0].get('windowId')==m['window_id'] and rr['ping'].get('version')==c.bridge.SAFETY_VERSION and rr['ping'].get('safety')=='DOM-only' and rr['ping'].get('content_build')in c.ACCEPTED_CONTENT_BUILDS,'terminal-previous-diagnostic-identity-transport')
 diagnostic_page={'tab':b[0],'tree':rr['tree'],'observed_at':page['observed_at']};_,tree=p.n.context(diagnostic_page,rv['job']['groupid']);p.n.public_identity(tree,rv['job']['identity']);lst=p.n.one(p.n.flatten(tree['root']),{'attributes':{'class':p.LIST}},'terminal-diagnostic-list');index=p.pager(lst['children'][-1])['page'];anchors=[x for x in rv['source']['rows']if x['page_index']==index];need(index in (target_index,source_index)and anchors,'terminal-previous-diagnostic-unexpected-page');p.current_page_for_case(diagnostic_page,rv['job'],rv['envelope'],rv['profile'],rv['source'],anchors[0])
 _terminal_opportunity_budget(review,index,source_index)
 if check_time:_terminal_clock(review)
 return {'old':old,'call':call,'route':rv,'effective':{**effective,**after},'current_page':index,'source_page':source_index,'target_page':target_index,'request_click_effect':False}

@p.partial_source_command
def adopt_terminal_previous_rejection(mref,review_ref):
 m=c.document(mref);base=Path(mref['path']).parent;path=base/'operation.json'
 with (base.parent/'.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);review=c.document(review_ref);folder=base/'.terminal-previous-adoption'/review['operation_before']['sha256'];intent=folder/'intent.json';proofpath=folder/'proof.json';result=folder/'result.json';current=c.document(c.ref(path));ir={'manifest':mref,'review':review_ref,'operation_before':review['operation_before']}
  if result.exists()or result.is_symlink():
   need(not result.is_symlink()and intent.exists()and c.document(c.ref(intent))==ir and proofpath.exists(),'terminal-previous-terminal-conflict');out=c.document(c.ref(result));need(out['review']==review_ref and out['proof']==c.ref(proofpath)and out['operation_after']==c.ref(path),'terminal-previous-terminal-result-conflict');CaseRunner(mref).guard();return out
  if intent.exists()or intent.is_symlink():need(not intent.is_symlink()and c.document(c.ref(intent))==ir,'terminal-previous-original-intent-conflict')
  original=folder/'operation.before.json';oldref=c.ref(original)if original.exists()else review['operation_before'];facts=terminal_previous_facts(mref,m,review,oldref,check_time=True);old=facts['old'];need(review['operation_before']['path']==str(path),'terminal-previous-canonical-original-operation')
  proof={'kind':TERMINAL_KIND,'manifest':mref,'review':review_ref,'operation_archive':{'path':str(original),'sha256':review['operation_before']['sha256']},'original_call':facts['call'],'request_click_effect':False,'original_state_preserved':'unknown','old_key_replay_allowed':False};raw=json.dumps(proof,ensure_ascii=False,sort_keys=True).encode();pr={'path':str(proofpath),'sha256':hashlib.sha256(raw).hexdigest()};expected=copy.deepcopy(old);expected.update(state='running',phase='read-first',expected_page=facts['current_page'],terminal_previous_adoption=pr);expected.pop('error',None)
  if facts['current_page']==facts['source_page']:expected['terminal_previous_opportunity']={'key':facts['call']['key']+':opportunity:1:'+review_ref['sha256'],'denied_key':facts['call']['key'],'from_page':facts['source_page'],'expected_page':facts['target_page'],'state':'armed','review':review_ref}
  if proofpath.exists()or proofpath.is_symlink():need(not proofpath.is_symlink()and c.document(c.ref(proofpath))==proof,'terminal-previous-proof-conflict')
  need(current in (old,expected),'terminal-previous-original-CAS');c.publish(intent,ir);c.immutable(original,Path(oldref['path']).read_bytes());c.immutable(proofpath,raw)
  if current==old:c.save(path,expected)
  CaseRunner(mref).guard();out={'kind':TERMINAL_KIND,'review':review_ref,'proof':pr,'operation_before':review['operation_before'],'operation_after':c.ref(path),'old_key_replayed':False,'ui_rpc':False};c.publish(result,out);return out

class CaseRunner(c.Runner):
 def __init__(self,mref,request=None):
  self.mref=mref;self.m=c.document(mref);self.base=Path(mref['path']).parent;expected=Path(self.m['root'])/'normal-case-page-journeys'/hashlib.sha256(self.m['review_key'].encode()).hexdigest()/self.m['source']['sha256'];need(self.m.get('kind')==KIND and self.base==expected,'case-journey-canonical-path');self.path=self.base/'operation.json';self.s=c.document(c.ref(self.path));need(self.s['manifest']==mref,'case-journey-operation-binding');self.request=request or (lambda cmd:c.bridge.request(cmd,timeout=50));self.last_fresh=None
 def guard(self):
  self.im,self.v,self.order,self.row=inputs(self.m['inspection']);self.job=self.v['job'];self.profile=self.v['profile'];need(self.im['root']==self.m['root'] and self.im['review_key']==self.m['review_key'] and self.im['inputs']['source']==self.m['source'] and self.row['page_index']==self.m['target_page'],'case-journey-source-or-case-changed');expected=self.m['code'];self.route_v=self.v;terminal_review=None;self.rejected_preaction_call=None
  if self.s.get('terminal_previous_adoption'):
   terminal_proof=c.document(self.s['terminal_previous_adoption']);terminal_review=c.document(terminal_proof['review']);_terminal_source_successor(terminal_review)
  if self.s.get('route_source_adoption'):
   proof=c.document(self.s['route_source_adoption']);review=c.document(proof['review']);need(self.s['route_source_adoption']['path']==str(self.base/'.route-source-adoption'/review['operation_before']['sha256']/'proof.json') and review['operation_before']['path']==str(self.path),'case-route-proof-canonical-path');self.route_v,expected,old=route_review(self.mref,self.m,self.s,review,proof['operation_archive'],source_successor=terminal_review);need(proof['manifest']==self.mref and proof['original_source']==self.m['source'] and self.s['calls'][:len(old['calls'])]==old['calls'],'case-route-proof-original-prefix')
  if terminal_review is not None:
   facts=terminal_previous_facts(self.mref,self.m,terminal_review,terminal_proof['operation_archive']);need(self.s['terminal_previous_adoption']['path']==str(self.base/'.terminal-previous-adoption'/terminal_review['operation_before']['sha256']/'proof.json')and terminal_proof['manifest']==self.mref and terminal_proof['original_call']==facts['call']and self.s['calls'][:1]==[facts['call']],'terminal-previous-original-call-prefix');expected=facts['effective'];self.rejected_preaction_call=facts['call']
   opportunity=self.s.get('terminal_previous_opportunity')
   if opportunity:
    need(opportunity['denied_key']==facts['call']['key'] and opportunity['key']==facts['call']['key']+':opportunity:1:'+terminal_proof['review']['sha256'] and opportunity['review']==terminal_proof['review'] and opportunity['state']in ('armed','intent-committed','confirmed'),'terminal-previous-opportunity-binding')
    if opportunity['state']=='intent-committed' and self.s['calls'][-1].get('state')=='unknown':_terminal_clock(terminal_review)
  need(all(c.ref(k)['sha256']==v for k,v in expected.items()),'case-journey-code-changed')
  rp=result_path(self.im)
  if rp.exists():need(c.document(c.ref(rp)).get('state') in ('preflight','open-ready') or self.s['state']=='complete','case-journey-result-open-or-unknown')
 def reviewed_terminal_build(self,ping):
  if self.s.get('terminal_previous_adoption'):need(ping.get('content_build')==TERMINAL_BUILD,'terminal-previous-reviewed-build-not-ready')
 def fresh(self):
  before=self.raw({'op':'tabs'});tabs=[t for w in before for t in w.get('tabs',[]) if t.get('tabId')==self.m['tab_id']];need(len(tabs)==1 and tabs[0].get('windowId')==self.m['window_id'],'case-journey-tab-window');ping=self.raw({'op':'ping','tabId':self.m['tab_id']});need(ping.get('version')==c.bridge.SAFETY_VERSION and ping.get('content_build') in c.ACCEPTED_CONTENT_BUILDS and ping.get('safety')=='DOM-only','case-journey-content-build');self.reviewed_terminal_build(ping);tree=self.raw({'op':'tree','tabId':self.m['tab_id']});after=self.raw({'op':'tabs'});need([t for w in after for t in w.get('tabs',[]) if t.get('tabId')==self.m['tab_id']]==tabs,'case-journey-tab-changed-during-read');page={'tab':tabs[0],'tree':tree,'observed_at':c.now()};q=c.publish(self.base/'pages'/(uuid.uuid4().hex+'.json'),page);self.s['latest_page']=q;self.persist();_,root=p.n.context(page,self.job['groupid']);lst=p.n.one(p.n.flatten(root['root']),{'attributes':{'class':p.LIST}},'case-current-list');index=p.pager(lst['children'][-1])['page'];route=self.route_v;rows=[r for r in route['source']['rows'] if r['page_index']==index];need(rows,'case-journey-page-outside-normal-source');proof=p.current_page_for_case(page,self.job,route['envelope'],route['profile'],route['source'],rows[0]);self.last_fresh=(q,page,proof);return q,page,proof
 def tick(self):
  self.guard()
  if self.s['state']!='running':return self.s
  q,page,proof=self.fresh();phase=self.s['phase']
  if self.s.get('expected_page') and proof['pager']['page']!=self.s['expected_page']:
   self.s['settle_reads']=self.s.get('settle_reads',0)+1;self.persist();need(self.s['settle_reads']<=2,'case-journey-target-did-not-settle');return self.s
  self.s.pop('settle_reads',None)
  if phase=='read-first':self.s.update(first_read=q,first_proof=proof,phase='read-second');self.persist();return self.s
  need(phase=='read-second','case-journey-phase');old=self.s['first_proof'];need(p.A.stamp(old['observed_at'])<p.A.stamp(proof['observed_at']) and all(old[k]==proof[k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')),'case-journey-page-not-stable')
  index=proof['pager']['page'];target=self.m['target_page']
  if index==target:self.s.update(state='complete',phase='at-case-page',normal_before=q,completed_at=c.now());self.persist();return self.s
  direction='next' if index<target else 'previous';pg=proof['pager'];need(not pg[direction+'_disabled'] and (direction=='previous' or not proof['terminal_boundary']),'case-journey-normal-end');expected=index+(1 if direction=='next' else -1);need(1<=expected<=len(self.route_v['envelope']['pages']),'case-journey-target-outside-normal-source');key=self.mref['sha256']+':'+str(index)+'->'+str(expected);opportunity=self.s.get('terminal_previous_opportunity');use_opportunity=opportunity is not None and opportunity['denied_key']==key
  if use_opportunity:
   need(opportunity['state']=='armed' and self.rejected_preaction_call is not None,'terminal-previous-opportunity-already-used');_terminal_clock(c.document(opportunity['review']));key=opportunity['key']
  need(not any(x['key']==key for x in self.s['calls']) and all(x['state']=='confirmed' or x==self.rejected_preaction_call for x in self.s['calls']),'case-journey-existing-intent-no-replay');cmd={'op':'click','tabId':self.m['tab_id'],'kind':'navigation','locator':{'by':'selector','value':pg[direction+'_selector']}};entry={'key':key,'state':'unknown','command':cmd,'from_page':q,'expected_page':expected};self.s['calls'].append(entry);self.s.update(state='unknown',phase='adjacent-click')
  if use_opportunity:opportunity['state']='intent-committed'
  self.persist();reply=self.raw(cmd);rr=c.publish(self.base/'replies'/(uuid.uuid4().hex+'.json'),reply);entry['reply']=rr;self.persist();clicked=reply.get('clicked',{});need(reply.get('kind')=='navigation' and clicked.get('selector')==cmd['locator']['value'] and clicked.get('attributes',{}).get('class')=='button-j4VxiA' and clicked.get('name')=='' and clicked.get('disabled') is not True,'case-journey-click-reply');entry['state']='confirmed'
  if use_opportunity:opportunity['state']='confirmed'
  self.s.update(state='running',phase='read-first',expected_page=expected);self.persist();return self.s
 @p.partial_source_command
 def run(self,steps):
  need(type(steps) is int and 1<=steps<=25,'case-journey-bounded-steps')
  for _ in range(steps):
   if self.s['state']!='running':break
   try:self.tick()
   except Exception as e:self.s.update(state='unknown' if self.s['state']=='unknown' else 'hold',error=str(e));self.persist();break
  return {'state':self.s['state'],'phase':self.s['phase'],'error':self.s.get('error'),'operation':c.ref(self.path),'complaint_actions_used':False}
@p.partial_source_command
def recover_route_source(manifest_ref,review_ref):
 """Metadata-only adoption under original journey lock; outer caller owns resource locks."""
 m=c.document(manifest_ref);base=Path(manifest_ref['path']).parent;path=base/'operation.json'
 with (base.parent/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);review=c.document(review_ref);folder=base/'.route-source-adoption'/review['operation_before']['sha256'];intent=folder/'intent.json';proofpath=folder/'proof.json';result=folder/'result.json';current=c.document(c.ref(path));ir={'manifest':manifest_ref,'review':review_ref,'operation_before':review['operation_before']}
  if result.exists()or result.is_symlink():
   need(not result.is_symlink() and intent.exists() and c.document(c.ref(intent))==ir and proofpath.exists(),'case-route-terminal-conflict');out=c.document(c.ref(result));need(out['review']==review_ref and out['proof']==c.ref(proofpath) and out['operation_after']==c.ref(path),'case-route-terminal-result-conflict');CaseRunner(manifest_ref).guard();return out
  if intent.exists()or intent.is_symlink():need(not intent.is_symlink() and c.document(c.ref(intent))==ir,'case-route-original-intent-conflict')
  original=folder/'operation.before.json';oldref=c.ref(original)if original.exists() else review['operation_before'];need(oldref['sha256']==review['operation_before']['sha256'],'case-route-original-before-conflict');rv,after,old=route_review(manifest_ref,m,current,review,oldref)
  proof={'kind':ROUTE_KIND,'manifest':manifest_ref,'original_source':m['source'],'review':review_ref,'operation_archive':{'path':str(original),'sha256':review['operation_before']['sha256']},'route_inputs':review['route_inputs'],'new_case_admission':False};raw=json.dumps(proof,ensure_ascii=False,sort_keys=True).encode();pr={'path':str(proofpath),'sha256':hashlib.sha256(raw).hexdigest()};expected=copy.deepcopy(old);expected.update(state='running',route_source_adoption=pr);expected.pop('error',None)
  if proofpath.exists()or proofpath.is_symlink():need(not proofpath.is_symlink() and c.document(c.ref(proofpath))==proof,'case-route-proof-conflict')
  need(current==old or current==expected,'case-route-state-CAS');c.publish(intent,ir);c.immutable(original,Path(oldref['path']).read_bytes());c.immutable(proofpath,raw)
  if current==old:c.save(path,expected)
  CaseRunner(manifest_ref).guard();out={'kind':ROUTE_KIND,'manifest':manifest_ref,'review':review_ref,'proof':pr,'operation_before':review['operation_before'],'operation_after':c.ref(path),'ui_rpc_click':False,'original_case_source_unchanged':True};c.publish(result,out);return out

def ensure_for_result(manifest_path,*,request=None,steps=25):
 """Thin existing-reader handoff. Never leave an opened/unknown drawer to page."""
 ir=c.ref(manifest_path);m,v,order,row=inputs(ir);path=result_path(m)
 if path.exists():
  op=c.document(c.ref(path));need(op.get('manifest')==m,'case-journey-original-result-operation-required')
  if op.get('state') not in ('preflight','open-ready'):
   need(op.get('state') in ('open-unknown','opened','record-ready','close-ready','close-unknown','verify-closed','complete'),'case-journey-result-phase-unsupported')
   return {'state':'complete','navigation_used':False,'resume_original_result_only':True}
 mr=prepare(ir)
 with (Path(mr['path']).parent.parent/'.lock').open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);return CaseRunner(mr,request).run(steps)
@p.partial_source_command
def batch(root,source_sha256,steps,*,request=None,memory=None):
 """One bounded process uses existing history prepare/run; no duplicate reader."""
 import history_workspace as h
 need(type(steps) is int and 1<=steps<=25,'case-batch-bounded-steps');root=Path(root).resolve();state=h.load(root);need(source_sha256 in state['sources'],'case-batch-source-not-owned');entry=state['sources'][source_sha256];v=h._inputs(state,entry['inputs']);need(v['profile'].get('contract')==p.CONTRACT,'case-batch-multipage-contract-required');keys=[state['groupid']+':'+r['review_id'] for r in v['source']['rows'] if r['action'] in h.READ_ACTIONS];need(keys==entry['existing_ids'],'case-batch-source-order-conflict');folder=root/'normal-case-batches'/source_sha256;folder.mkdir(parents=True,exist_ok=True);mp=folder/'manifest.json';m={'kind':'normal-existing-case-batch-v1','root':str(root),'source':entry['inputs']['source'],'keys':keys,'inputs':entry['inputs']};mr=c.publish(mp,m)
 with (folder/'.lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);path=folder/'operation.json';s=c.document(c.ref(path)) if path.exists() else {'manifest':mr,'state':'running','completed':[]};need(s['manifest']==mr,'case-batch-original-manifest-required')
  for _ in range(steps):
   if s['state']!='running':break
   key=next((k for k in keys if k not in s['completed']),None)
   if key is None:s.update(state='complete',completed_at=c.now());c.save(path,s);break
   try:
    prepared=h.prepare(root,key);route=ensure_for_result(prepared['manifest']['path'],request=request,steps=1);s.update(current_key=key,journey=route);c.save(path,s)
    if route['state'] not in ('complete','running'):s.update(state=route['state'],error=route.get('error'));break
    if route['state']!='complete':continue
    out=h.run(prepared['manifest']['path'],steps=1,request=request,memory=memory);s['result']=out
    if out['state']=='complete':s['completed'].append(key)
    elif out['state'] not in ('preflight','open-ready','opened','record-ready','close-ready','verify-closed'):s.update(state='hold',error='case-batch-result-outcome-unresolved');break
   except Exception as e:s.update(state='hold',error=str(e));break
   finally:c.save(path,s)
  c.save(path,s);return {'state':s['state'],'operation':c.ref(path),'completed_cases':len(s['completed']),'total_cases':len(keys),'error':s.get('error'),'business_cursor_changed':False}
def main():
 ap=argparse.ArgumentParser(description=__doc__);sp=ap.add_subparsers(dest='action',required=True);q=sp.add_parser('prepare');q.add_argument('--inspection',required=True);q.add_argument('--inspection-sha256',required=True);q=sp.add_parser('run');q.add_argument('--manifest',required=True);q.add_argument('--manifest-sha256',required=True);q.add_argument('--steps',type=int,default=25);q=sp.add_parser('batch');q.add_argument('--root',required=True);q.add_argument('--source-sha256',required=True);q.add_argument('--steps',type=int,default=25);a=ap.parse_args()
 if a.action=='prepare':out={'manifest':prepare({'path':a.inspection,'sha256':a.inspection_sha256}),'ui_used':False}
 elif a.action=='batch':out=batch(a.root,a.source_sha256,a.steps)
 else:
  with (Path(a.manifest).parent.parent/'.lock').open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);out=CaseRunner({'path':a.manifest,'sha256':a.manifest_sha256}).run(a.steps)
 print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':
 from runtime_entry import ensure_runtime
 ensure_runtime()
 try:main()
 except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e)},ensure_ascii=False));raise SystemExit(2)
