#!/usr/bin/env python3
"""Candidate history-only normal pagination. Only existing bridge, durable adjacent clicks.
No export, complaint, screenshot, sender, ingest, case memory, or business cursor.
"""
import argparse,json,hashlib,os,fcntl,uuid,sys,copy,re,time
from pathlib import Path
from datetime import datetime,timezone
import normal_paging as p
ROOT=p.ROOT
sys.path[:0]=[str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import bridge,workflow as w
need=p.need
KIND='normal-history-pages-collection-v1'
CONTENT_BUILD='normal-review-adjacent-pager-v1'
ACCEPTED_CONTENT_BUILDS=('normal-review-terminal-pagination-v3',CONTENT_BUILD,'normal-review-export-baseline-pager-v1','normal-review-export-terminal-prev-v2','exact-chongqing-company-discovery-v1')
MAX_LOADING_READS=3
MAX_LOADING_SECONDS=30.0
def monotonic():return time.clock_gettime(time.CLOCK_MONOTONIC)
def now():return datetime.now(timezone.utc).isoformat()
def ref(path):
 path=Path(path).resolve();return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def document(q):
 path=Path(q['path']);need(path.is_absolute() and not path.is_symlink() and ref(path)==q,'paging-pinned-input-changed');return json.loads(path.read_bytes())
def sync_directory(path):
 fd=os.open(str(Path(path)),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def immutable(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(path.read_bytes()==raw,'paging-immutable-conflict')
 else:
  with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  sync_directory(path.parent)
 return ref(path)
def publish(path,value):return immutable(path,json.dumps(value,ensure_ascii=False,sort_keys=True).encode())
def save(path,value):w.atomic(Path(path),value);sync_directory(Path(path).parent)
def codes():
 files=[Path(__file__).resolve(),Path(p.__file__).resolve(),Path(p.n.__file__).resolve(),Path(bridge.__file__).resolve(),ROOT/'skills/chrome-dom-export/extension/content.js',Path(p.body.__file__).resolve(),Path(p.A.__file__).resolve(),Path(p.A.export_parse_session.__file__).resolve(),Path(p.source_proof_session.__file__).resolve()]
 return {str(f):ref(f)['sha256'] for f in files}
def history_scope(job,nav_path):
 from history_workspace import load
 root=Path(nav_path).parent;s=load(root);need(s['company']==job['company'] and s['groupid']==str(job['groupid']) and s['identity']==job['identity'] and s['history_range']=={'start':job['start'],'end_exclusive':job['end_exclusive']},'paging-original-history-scope-required');return root

def original_source_window(job,journal,tab_id):
 """Canonical completed acquire read evidence; activation is not a requirement.
 Existing activate-backed receipts retain their exact original contract.
 """
 windows={c['result']['windowId']for c in journal['calls']if c.get('command',{}).get('op')=='activate'and c['command'].get('tabId')==tab_id and c.get('state')=='confirmed'and type(c.get('result',{}).get('windowId'))is int}
 if windows:need(len(windows)==1,'paging-original-source-window-required');return next(iter(windows))
 need(journal.get('work_order_id')==job['source_work_order_id']and journal.get('tab_id')==tab_id and journal.get('state')=='complete'and journal.get('phase')=='done'and not journal.get('last_error')and all(c.get('state')=='confirmed'for c in journal['calls'])and journal.get('identity')==job['identity']and str(journal.get('groupid'))==str(job['groupid']),'paging-completed-source-read-scope')
 from readonly_tick_snapshot import decode
 from urllib.parse import urlsplit,parse_qs
 entries=journal.get('review_filter_loading_reads',[]);need(bool(entries),'paging-original-source-window-required');base=Path(job['source_receipt']).parent/'bridge-evidence'
 for entry in entries:
  command=entry.get('command',{});window=command.get('windowId');need(type(window)is int and window>0 and command=={'op':'readonly-scope','tabId':tab_id,'windowId':window},'paging-source-read-command')
  for r in(entry['reply'],entry['tree']):
   path=Path(r['path']);need(path.parent==base and path.resolve()==path and not any(v.is_symlink()for v in(path,*path.parents)),'paging-source-read-canonical')
  raw=document(entry['reply']);need(raw.get('ok')is True and raw.get('error')is None,'paging-source-read-reply');snapshot=decode(raw['result'],tab_id,window);tree=document(entry['tree']);need(snapshot['tree']==tree,'paging-source-read-tree-binding')
  tabs=[]
  for key in('before','after'):
   matches=[t for w in snapshot[key]for t in w.get('tabs',[])if t.get('tabId')==tab_id];need(len(matches)==1,'paging-source-read-unique-tab');tab=matches[0];u=urlsplit(tab['url']);need(u.scheme=='https'and u.netloc=='life.douyin.com'and u.path=='/p/life_comment/management'and parse_qs(u.query).get('groupid')==[str(job['groupid'])]and tab.get('windowId')==window,'paging-source-read-tab-scope');tabs.append(tab)
  need(tabs[0]['url']==tabs[1]['url']and tree.get('url')=='https://life.douyin.com/p/life_comment/management'and tree.get('truncated')is False,'paging-source-read-route-changed');p.n.public_identity(tree,job['identity']);need(snapshot['ping'].get('safety')=='DOM-only'and snapshot['ping'].get('version')=='dom-only-20261021-11','paging-source-read-ping');windows.add(window)
 need(len(windows)==1,'paging-original-source-window-required');return next(iter(windows))

def prepare(job_ref,nav_ref,profile_ref=None):
 if profile_ref is None:profile_ref=publish(Path(nav_ref['path']).parent/'normal-pages-v1/pending-profile.json',{'contract':p.CONTRACT,'status':'pending-live-multipage-validation','text_schema':'public-visible-text-v2','pending_card_policy':'history-unresolved-store-v1'})
 prior=Path(nav_ref['path']).parent/'normal-pages-v1/manifest.json'
 if prior.exists():
  mr=ref(prior);old=document(mr);need(old['job']==job_ref and old['original_navigation']==nav_ref and old['profile']==profile_ref,'paging-original-manifest-conflict');Runner(mr).guard();return mr
 job=document(job_ref);state=document(nav_ref);profile=document(profile_ref);root=history_scope(job,nav_ref['path']);need(Path(job_ref['path']).parent==root and Path(nav_ref['path']).name=='navigation-state.json','paging-original-navigation-path')
 fp=hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False).encode()).hexdigest();need(state.get('fingerprint')==fp and state.get('phase')=='observeNegative' and not state.get('stable_normal_verified') and not state.get('normal_probe') and not state.get('pagination_contract') and all(c.get('state')=='confirmed' for c in state.get('calls',[])),'paging-original-unfinished-observation-required')
 need(profile.get('contract')==p.CONTRACT and profile.get('status')=='pending-live-multipage-validation','paging-pending-profile-required')
 # Reuse the completed acquisition verifier, including original journal/hash/source identity.
 import prepare_company_navigation as company
 receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']};receipt,_,jr=company.receipt(receipt_ref);journal=document(jr)
 need(receipt['work_order_id']==job['source_work_order_id'] and receipt['identity']==job['identity'],'paging-original-acquisition-mismatch')
 window=original_source_window(job,journal,state['tab_id'])
 build=re.findall(r"const BUILD='([^']+)'",(ROOT/'skills/chrome-dom-export/extension/content.js').read_text());need(len(build)==1 and build[0] in ACCEPTED_CONTENT_BUILDS,'paging-reviewed-content-build-not-published')
 base=root/'normal-pages-v1';base.mkdir(exist_ok=True)
 with (base/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);mp=base/'manifest.json'
  if mp.exists():
   old=document(ref(mp));need(old['job']==job_ref and old['original_navigation']==nav_ref and old['profile']==profile_ref,'paging-original-manifest-conflict');return ref(mp)
  need(not (base/'operation.json').exists(),'paging-orphan-operation')
  original=immutable(base/('original-navigation-'+nav_ref['sha256']+'.json'),Path(nav_ref['path']).read_bytes())
  m={'kind':KIND,'job':job_ref,'original_navigation':nav_ref,'navigation_archive':original,'profile':profile_ref,'receipt':receipt_ref,'source_journal':jr,'root':str(root),'tab_id':state['tab_id'],'window_id':window,'code':codes(),'created_at':now()}
  mr=publish(mp,m);save(base/'operation.json',{'kind':KIND,'manifest':mr,'phase':'read-first','state':'running','expected_page':1,'pages':[],'calls':[],'navigation_sha256':nav_ref['sha256'],'created_at':now()});return mr

def terminal_profile_source_codes(review,before):
 if review.get('reuse_reviewed_terminal_first_read') is not True:return before
 need(review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('readonly_second_read_only') is True,'terminal-first-read-supervisor-required')
 target=str(ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py');old=review.get('code_before');after=review.get('code_after')
 need(old==before and isinstance(after,dict) and set(after)==set(before) and {k for k in before if before[k]!=after[k]}=={target},'terminal-first-read-only-runner-amendment')
 release=document(review['source_release']);ts=release.get('targets',[])
 need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('reviewed_by')=='workshop-director' and release.get('published') is True and release.get('test_projection_only') is False and len(ts)==1 and ts[0]['target']==target and ts[0]['old_sha256']==old[target] and ts[0]['after']['sha256']==after[target] and ts[0]['mode']==420,'terminal-first-read-source-release')
 before_ref=ts[0].get('before');need(isinstance(before_ref,dict) and before_ref['path']==str(Path(review['source_release']['path']).parent/'normal_paging_runner.py.before') and ref(before_ref['path'])==before_ref and before_ref['sha256']==old[target],'terminal-first-read-published-before-archive')
 need(all(ref(k)['sha256']==v for k,v in after.items()),'terminal-first-read-installed-sources')
 return after

class Runner:
 def __init__(self,mref,request=None):
  self.mref=mref;self.m=document(mref);self.base=Path(mref['path']).parent;need(self.m['kind']==KIND and self.base==Path(self.m['root'])/'normal-pages-v1','paging-canonical-operation-required');self.path=self.base/'operation.json';self.s=document(ref(self.path));need(self.s['manifest']==mref,'paging-original-operation-required');self.request=request or self.default_request;self.last_fresh=None
 def guard(self,terminal_review=None):
  self.job=document(self.m['job']);self.profile=document(self.m['profile']);document(self.m['receipt']);document(self.m['source_journal']);document(self.m['navigation_archive']);history_scope(self.job,self.m['original_navigation']['path'])
  if self.s.get('profile_amendment'):
   audit=document(self.s['profile_amendment']);need(audit['manifest']==self.mref and audit['job']==self.m['job'] and audit['original_profile']==self.m['profile'],'paging-profile-amendment-binding');self.profile=document(audit['approved_profile']);document(audit['hold_raw'])
  expected_code=self.m['code']
  if self.s.get('body_shape_recovery'):
   from normal_body_shape_recovery import verified_context
   expected_code,body_profile=verified_context(self.mref,self.m,self.s['body_shape_recovery'])
   if not self.s.get('profile_amendment'):self.profile=body_profile
   else:need({k:v for k,v in self.profile.items() if k not in ('status','terminal_layout')}=={k:v for k,v in body_profile.items() if k not in ('status','terminal_layout')},'body-profile-terminal-amendment-changed')
  elif self.s.get('loading_read_recovery'):
   from normal_loading_read_recovery import verified_code
   expected_code=verified_code(self.mref,self.m,self.s['loading_read_recovery'])
  elif self.s.get('loading_shape_recovery'):
   from normal_loading_recovery import verified_code
   expected_code=verified_code(self.mref,self.m,self.s['loading_shape_recovery'])
  if self.s.get('first_page_terminal_recovery'):
   audit=document(self.s['first_page_terminal_recovery']);expected_code,self.profile=self.verify_first_page_review(audit['review'],audit['operation_archive'])
  source_successor=terminal_review or (document(self.s['profile_amendment']) if self.s.get('profile_amendment') else None)
  if source_successor and source_successor.get('reuse_reviewed_terminal_first_read') is True:terminal_profile_source_codes(source_successor,source_successor.get('code_before'))
  if self.s.get('edge_source_recovery'):expected_code,self.verified_edge_source_page=verified_edge_source_recovery(self.mref,self.m,self.s,source_successor=source_successor)
  if self.s.get('profile_amendment'):expected_code=terminal_profile_source_codes(document(self.s['profile_amendment']),expected_code)
  if terminal_review is not None:expected_code=terminal_profile_source_codes(terminal_review,expected_code)
  need(all(ref(k)['sha256']==v for k,v in expected_code.items()),'paging-code-changed')
  need(ref(self.m['original_navigation']['path'])['sha256']==self.s['navigation_sha256'],'paging-original-navigation-changed')
 def default_request(self,command):
  timeout=50
  wait=self.s.get('loading_wait')
  if wait and self.s.get('state')=='running' and self.s.get('phase')=='read-first':
   elapsed=monotonic()-wait['started_monotonic'];need(0<=elapsed<MAX_LOADING_SECONDS,'normal-pager-loading-readonly-exhausted');timeout=min(timeout,MAX_LOADING_SECONDS-elapsed)
  return bridge.request(command,timeout=timeout)
 def loading_edge(self,navigation=None,source_page_ref=None):
  need(self.s.get('phase')=='read-first' and self.s.get('pages') and self.s.get('expected_page')==len(self.s['pages'])+1,'paging-loading-read-first-adjacent-only')
  prior=self.s['pages'][-1]['proof'];target=self.s['expected_page'];need(prior['pager']['page']==target-1,'paging-loading-prior-page')
  calls=self.s.get('calls',[]);need(len(calls)==target-1 and all(x.get('state')=='confirmed' for x in calls),'paging-loading-confirmed-edge-required')
  cmd={'op':'click','tabId':prior['scope']['tabId'],'kind':'navigation','locator':{'by':'selector','value':prior['pager']['next_selector']}}
  need(calls[-1]['command']==cmd,'paging-loading-edge-command')
  reply=document(calls[-1]['reply']);need(reply.get('kind')=='navigation' and reply.get('clicked',{}).get('selector')==cmd['locator']['value'],'paging-loading-edge-reply')
  nav=navigation if navigation is not None else document({'path':self.m['original_navigation']['path'],'sha256':self.s['navigation_sha256']})
  edges=[x for x in nav['calls'] if x.get('key')=='normal-page:'+str(target-1)+'->'+str(target)]
  need(len(edges)==1 and edges[0].get('state')=='confirmed' and edges[0].get('command')==cmd and edges[0].get('expected_target_page')==target and edges[0].get('scope')==prior['scope'] and edges[0].get('result')==reply,'paging-loading-original-navigation-edge')
  source=source_page_ref or calls[-1].get('source_page') or getattr(self,'verified_edge_source_page',None)
  if source is None:need(edges[0].get('from_page_sha256')==prior['page_sha256'],'paging-loading-original-navigation-edge')
  else:
   page=document(source);path=Path(source['path']);need(path.parent==self.base/'pages' and path.resolve()==path and not any(x.is_symlink()for x in(path,*path.parents))and re.fullmatch('[0-9a-f]{32}\\.json',path.name),'paging-edge-source-canonical-page')
   job=getattr(self,'job',None)or document(self.m['job']);profile=getattr(self,'profile',None)or document(self.m['profile']);actual=p.inspect_page(job,page,profile,self.m['receipt'])
   need(actual['page_sha256']==edges[0].get('from_page_sha256') and p.A.stamp(actual['observed_at'])>=p.A.stamp(prior['observed_at'])and all(actual.get(k)==prior.get(k)for k in('scope','normal_header_count','pager','rows','terminal_boundary','pending_rows','visible_normal_card_count')),'paging-edge-source-not-original-stable-page')
  return prior
 def begin_loading_read(self):
  wait=self.s.get('loading_wait')
  if not wait:return
  self.loading_edge();clock=monotonic()
  if not wait['attempts']:
   if wait.get('started_monotonic') is not None:wait['pre_read_started_monotonic']=wait['started_monotonic']
   wait['started_monotonic']=clock
  need(wait['expected_page']==self.s['expected_page'] and 0<=clock-wait['started_monotonic']<MAX_LOADING_SECONDS and len(wait['attempts'])<MAX_LOADING_READS,'normal-pager-loading-readonly-exhausted')
  wait['attempts'].append({'started_monotonic':clock,'at':now()});self.persist()
 def finish_loading_read(self,loading=False):
  wait=self.s.get('loading_wait')
  if not wait:return
  clock=monotonic();attempt=wait['attempts'][-1];attempt.update(completed_monotonic=clock,raw=self.s['latest_page'],loading=loading)
  self.persist();need(0<=clock-wait['started_monotonic']<MAX_LOADING_SECONDS,'normal-pager-loading-readonly-exhausted')
 def persist(self):self.s['updated_at']=now();save(self.path,self.s)
 def raw(self,cmd):
  self.guard();label=str(len(self.s.get('transport',[]))+1).zfill(4)+'-'+uuid.uuid4().hex;q=self.base/'transport'/(label+'.json')
  try:reply=self.request(cmd)
  except Exception as e:
   rr=publish(q,{'command':cmd,'exception':{'type':type(e).__name__,'message':str(e)},'at':now()});self.s.setdefault('transport',[]).append(rr);self.persist();raise
  rr=publish(q,{'command':cmd,'reply':reply,'at':now()});self.s.setdefault('transport',[]).append(rr);self.persist();need(reply.get('ok') is True,'paging-bridge-read-or-action-failed');return reply['result']
 def fresh(self):
  before=self.raw({'op':'tabs'});tabs=[t for x in before for t in x.get('tabs',[]) if t.get('tabId')==self.m['tab_id']];need(len(tabs)==1 and tabs[0].get('windowId')==self.m['window_id'],'paging-tab-window-changed');tab=tabs[0]
  ping=self.raw({'op':'ping','tabId':self.m['tab_id']});need(ping.get('version')==bridge.SAFETY_VERSION and ping.get('safety')=='DOM-only' and ping.get('content_build') in ACCEPTED_CONTENT_BUILDS,'paging-bridge-version')
  tree=self.raw({'op':'tree','tabId':self.m['tab_id']});after=self.raw({'op':'tabs'});a=[t for x in after for t in x.get('tabs',[]) if t.get('tabId')==self.m['tab_id']];need(a==tabs,'paging-tab-changed-during-read')
  page={'tab':tab,'tree':tree,'observed_at':now()};q=publish(self.base/'pages'/(uuid.uuid4().hex+'.json'),page);self.s['latest_page']=q;self.persist();proof=p.inspect_page(self.job,page,self.profile,self.m['receipt']);self.last_fresh=(q,page,proof);return q,page,proof
 def navigation_write(self,value):
  path=Path(self.m['original_navigation']['path']);need(ref(path)['sha256']==self.s['navigation_sha256'],'paging-navigation-write-conflict');raw=path.read_bytes();immutable(self.base/'navigation-history'/(self.s['navigation_sha256']+'.json'),raw);save(path,value);self.s['navigation_sha256']=ref(path)['sha256'];self.persist()
 def approve_profile(self,review_ref):
  review=document(review_ref);self.guard(terminal_review=review)
  need(self.s['state']=='hold' and self.s.get('error')=='terminal-layout-awaits-live-profile' and not self.s.get('profile_amendment') and all(c.get('state')=='confirmed' for c in document({'path':self.m['original_navigation']['path'],'sha256':self.s['navigation_sha256']})['calls']),'paging-profile-review-only-terminal-hold')
  need(review.get('kind')=='normal-paging-terminal-profile-review-v1' and review.get('manifest')==self.mref and review.get('job')==self.m['job'] and review.get('operation_before')==ref(self.path) and review.get('navigation_sha256')==self.s['navigation_sha256'] and review.get('hold_raw')==self.s['latest_page'] and review.get('structure_reviewed') is True and review.get('later_pages_live_validated') is False,'paging-profile-review-scope')
  approved=document(review['approved_profile']);need({k:v for k,v in approved.items() if k not in ('status','terminal_layout')}=={k:v for k,v in self.profile.items() if k not in ('status','terminal_layout')} and approved.get('status')=='live-validated' and approved.get('terminal_layout',{}).get('approved_page')==self.s['latest_page'],'paging-profile-review-contract')
  raw=document(self.s['latest_page']);proof=p.inspect_page(self.job,raw,approved,self.m['receipt']);need(proof['terminal_boundary'] and proof['pager']['page']==self.s['expected_page'],'paging-profile-review-terminal')
  reuse=review.get('reuse_reviewed_terminal_first_read') is True
  if reuse:
   need(review.get('approved') is True and review.get('reviewer_role')=='supervisor' and review.get('readonly_second_read_only') is True,'terminal-first-read-supervisor-required')
   terminal_profile_source_codes(review,review.get('code_before'))
   need(self.s['phase']=='read-first' and self.s['expected_page']>1 and len(self.s['pages'])==self.s['expected_page']-1 and self.s.get('loading_wait',{}).get('expected_page')==self.s['expected_page'] and p.A.stamp(raw['observed_at'])>p.A.stamp(self.s['pages'][-1]['proof']['observed_at']),'terminal-first-read-original-phase-time')
  original=immutable(self.base/'review-history'/(ref(self.path)['sha256']+'.json'),self.path.read_bytes());audit={**review,'review_ref':review_ref,'original_profile':self.m['profile'],'operation_archive':original,'approved_at':now()};ar=publish(self.base/'profile-amendment.json',audit);self.s.update(profile_amendment=ar,state='running',phase='read-second' if reuse else 'read-first');self.s.pop('first_read',None)
  if reuse:self.s['first_read']=self.s['latest_page']
  self.s.pop('error',None);self.persist();return {'state':'running','operation':ref(self.path),'ui_used':False}
 def verify_first_page_review(self,review_ref,archive=None):
  review=document(review_ref)
  need(review.get('kind')=='normal-first-page-terminal-code-profile-review-v1' and review.get('approved') is True and review.get('reviewer_role')=='supervisor','first-terminal-root-review-required')
  need(review.get('manifest')==self.mref and review.get('job')==self.m['job'] and review.get('code_before')==self.m['code'] and review.get('original_profile')==self.m['profile'],'first-terminal-original-binding')
  original_ref=archive or review['operation_before'];need(original_ref['sha256']==review['operation_before']['sha256'],'first-terminal-original-archive-sha');original=document(original_ref)
  need(original.get('manifest')==self.mref and original.get('state')=='hold' and original.get('phase')=='read-first' and original.get('error')=='terminal-layout-awaits-live-profile' and original.get('expected_page')==1 and original.get('pages')==[] and original.get('calls')==[] and original.get('latest_page')==review.get('hold_raw') and original.get('navigation_sha256')==review.get('navigation_sha256'),'first-terminal-only-original-unread-hold')
  need(not any(original.get(k) for k in ('profile_amendment','body_shape_recovery','loading_read_recovery','loading_shape_recovery','first_page_terminal_recovery','loading_wait','first_read')),'first-terminal-other-recovery-forbidden')
  nav=document(self.m['navigation_archive']);need(ref(self.m['navigation_archive']['path'])['sha256']==review['navigation_sha256'] and all(c.get('state')=='confirmed' for c in nav.get('calls',[])),'first-terminal-navigation-before')
  before=review['code_before'];after=review.get('code_after');allowed={str(ROOT/'skills/negative-review-complaints/scripts/normal_paging.py'),str(ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py')}
  need(isinstance(after,dict) and set(before)==set(after) and {k for k in before if before[k]!=after[k]}==allowed and after==codes(),'first-terminal-reviewed-two-source-upgrade')
  approved=document(review['approved_profile']);old=document(self.m['profile'])
  need(('image_only_text_schema' not in old or old['image_only_text_schema']==p.body.SCHEMA) and approved.get('image_only_text_schema')==p.body.SCHEMA,'first-terminal-known-image-body-opt-in')
  need(approved.get('status')=='live-validated' and approved.get('terminal_layout',{}).get('first_page_terminal') is True and approved['terminal_layout'].get('approved_page')==review['hold_raw'] and {k:v for k,v in approved.items() if k not in ('status','terminal_layout','image_only_text_schema')}=={k:v for k,v in old.items() if k not in ('status','terminal_layout','image_only_text_schema')},'first-terminal-approved-profile-contract')
  proof=p.inspect_page(self.job,document(review['hold_raw']),approved,self.m['receipt'])
  need(proof['pager']['page']==1 and proof['pager']['previous_disabled'] and proof['terminal_boundary'] and len(proof['rows'])==proof['normal_header_count']<=10,'first-terminal-reviewed-proof')
  return after,approved
 def approve_first_page_terminal(self,review_ref):
  # Pure typed amendment: no RPC, no input, unchanged original manifest/pins.
  self.job=document(self.m['job']);document(self.m['receipt']);document(self.m['source_journal']);document(self.m['navigation_archive']);history_scope(self.job,self.m['original_navigation']['path'])
  if self.s.get('first_page_terminal_recovery'):
   audit=document(self.s['first_page_terminal_recovery']);need(audit['review']==review_ref,'first-terminal-original-review-no-rearm');self.guard();return {'state':self.s['state'],'operation':ref(self.path),'ui_used':False,'already_applied':True}
  review=document(review_ref);need(ref(self.path)==review.get('operation_before') and self.s.get('navigation_sha256')==ref(self.m['original_navigation']['path'])['sha256'],'first-terminal-current-hold-changed')
  self.verify_first_page_review(review_ref)
  archive=immutable(self.base/'first-page-terminal-recovery'/('before-'+ref(self.path)['sha256']+'.json'),self.path.read_bytes())
  audit=publish(self.base/'first-page-terminal-recovery/authorization.json',{'kind':'normal-first-page-terminal-amendment-v1','manifest':self.mref,'review':review_ref,'operation_archive':archive})
  self.s.update(first_page_terminal_recovery=audit,state='running',phase='read-first');self.s.pop('error',None);self.persist()
  return {'state':'running','operation':ref(self.path),'ui_used':False,'original_outer_clock_reset':False}
 def finalize(self):
  self.guard();need(self.s['state'] in ('collected','complete') and self.s['phase'] in ('await-finalize','source-ready'),'paging-complete-normal-collection-required');pairs=[[document(x) for x in item['pair']] for item in self.s['pages']];env={'source':'local-dom-bridge','company':self.job['company'],'groupid':str(self.job['groupid']),'identity_evidence':pairs[0][0],'pages':[x[1] for x in pairs],'stable_page_pairs':pairs};diagnostic=p.finalize_pages(self.job,env['pages'],self.profile,self.m['receipt'],stable_pairs=pairs)
  if diagnostic.get('pending_count',0):
   refs={'profile':publish(self.base/'final/profile.json',self.profile),'envelope':publish(self.base/'final/envelope.json',env),'diagnostic':publish(self.base/'final/incomplete-history-evidence.json',diagnostic)};self.s.update(state='needs-review',phase='pending-store-review',outputs=refs);self.persist();return {'state':'needs-review','all_normal_read':False,'all_pages_read':True,'verified_count':diagnostic['verified_count'],'pending_count':diagnostic['pending_count'],'outputs':refs,'operation':ref(self.path),'ui_used':False,'business_cursor_changed':False,'source_created':False}
  source=p.joined_envelope(self.job,env,self.profile,self.m['receipt']);refs={'profile':publish(self.base/'final/profile.json',self.profile),'envelope':publish(self.base/'final/envelope.json',env),'source':publish(self.base/'final/source.json',source)};self.s.update(state='complete',phase='source-ready',outputs=refs);self.persist();return {'state':'complete','all_normal_read':True,'outputs':refs,'operation':ref(self.path),'ui_used':False,'business_cursor_changed':False}
 def partial_evidence(self):
  self.guard();need(bool(self.s.get('pages')) and self.profile.get('pending_card_policy')=='history-unresolved-store-v1','paging-partial-history-pages-required');pairs=[[document(x)for x in item['pair']]for item in self.s['pages']];payload=p.partial_history_delivery(self.job,[x[1]for x in pairs],self.profile,self.m['receipt'],stable_pairs=pairs);env={'source':'local-dom-bridge','company':self.job['company'],'groupid':str(self.job['groupid']),'identity_evidence':pairs[0][0],'pages':[x[1]for x in pairs],'stable_page_pairs':pairs};partial=p.partial_history_source(self.job,env,self.profile,self.m['receipt']);source_ref=publish(self.base/'partial-existing-results'/('read-source-'+p.A.data_hash(partial)+'.json'),partial);inputs={'job':self.m['job'],'source':source_ref,'profile':publish(self.base/'partial-existing-results'/('profile-'+p.A.data_hash(self.profile)+'.json'),self.profile),'envelope':publish(self.base/'partial-existing-results'/('envelope-'+p.A.data_hash(env)+'.json'),env)};path=self.base/'partial-existing-results'/('pages-'+str(len(pairs))+'-'+p.A.data_hash(payload)+'.json');return {'state':'needs-review','partial_evidence':publish(path,payload),'history_ingest_inputs':inputs,'existing_result_candidates':len(payload['case_candidates']),'pending_count':payload['pending_count'],'all_normal_read':False,'source_created':False,'ui_used':False}
 def tick(self):
  self.guard()
  if self.s['state']!='running':return self.s
  phase=self.s['phase']
  if phase=='read-first':
   self.begin_loading_read();q,page,proof=self.fresh();self.finish_loading_read()
   if proof['pager']['page']!=self.s['expected_page']:
    self.s['settle_reads']=self.s.get('settle_reads',0)+1;self.persist();need(self.s['settle_reads']<=2,'paging-target-did-not-settle');return self.s
   self.s.pop('settle_reads',None);self.s.pop('waiting_for',None);self.s.pop('loading_wait',None);self.s.update(first_read=q,phase='read-second');self.persist();return self.s
  if phase=='read-second':
   q,page,proof=self.fresh();before=document(self.s['first_read']);prior=p.inspect_page(self.job,before,self.profile,self.m['receipt']);need(p.A.stamp(before['observed_at'])<p.A.stamp(page['observed_at']) and all(prior[k]==proof[k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')+ (('pending_rows','visible_normal_card_count')if self.profile.get('pending_card_policy')else())),'paging-current-page-not-stable')
   existing={x['review_id'] for entry in self.s['pages'] for x in entry['proof']['rows']};need(not any(x['review_id'] in existing for x in proof['rows']),'paging-repeated-normal-review')
   need(proof['pager']['page']==len(self.s['pages'])+1 and (not self.s['pages'] or all(proof[k]==self.s['pages'][0]['proof'][k] for k in ('scope','normal_header_count'))),'paging-page-prefix-changed')
   pending_refs=[publish(self.base/'pending-cards'/('page-'+str(proof['pager']['page'])+'-card-'+str(x['card_index'])+'-'+x['card_sha256']+'.json'),x)for x in proof.get('pending_rows',[])];self.s['pages'].append({'pair':[self.s['first_read'],q],'proof':proof,**({'pending_records':pending_refs}if self.profile.get('pending_card_policy')else{})});self.s['phase']='ready-next';self.persist()
   if not self.s.get('upgraded_navigation'):
    original=Path(self.m['original_navigation']['path']).read_bytes();up=p.parser_upgrade(original,self.job,self.s['navigation_sha256'],first_page=page,profile=self.profile,receipt_ref=self.m['receipt']);planned=publish(self.base/'upgraded-navigation.json',up);self.s['upgrade_intent']=planned;self.persist();self.navigation_write(up);self.s['upgraded_navigation']=planned;self.persist()
   count=sum(len(x['proof']['rows'])+len(x['proof'].get('pending_rows',[])) for x in self.s['pages']);need(count<=proof['normal_header_count'],'paging-normal-count-overflow')
   if self.profile.get('pending_card_policy'):self.s['partial_history_evidence']=self.partial_evidence()['partial_evidence'];self.persist()
   if proof['terminal_boundary']:
    need(count==proof['normal_header_count'],'paging-terminal-normal-count-incomplete');self.s.update(state='collected',phase='await-finalize');self.persist()
   elif count==proof['normal_header_count']:
    self.s.update(state='hold',error='paging-normal-count-complete-boundary-unverified');self.persist()
   return self.s
  need(phase=='ready-next','paging-unknown-phase')
  q,page,proof=self.last_fresh if self.last_fresh is not None else self.fresh()
  need(q==self.s['pages'][-1]['pair'][1] or all(proof[k]==self.s['pages'][-1]['proof'][k] for k in ('scope','normal_header_count','pager','rows','terminal_boundary')+ (('pending_rows','visible_normal_card_count')if self.profile.get('pending_card_policy')else())),'paging-current-source-page-changed')
  nav=document({'path':self.m['original_navigation']['path'],'sha256':self.s['navigation_sha256']});planned=p.prepare_adjacent_intent(nav,self.job,page,self.profile,self.m['receipt'],'next');need(planned.get('command') is not None,'paging-confirmed-edge-readonly-required')
  self.s.update(state='unknown',phase='adjacent-click',command=planned['command'],expected_target_page=planned['expected_target_page'],edge_source_page=q);self.persist();self.navigation_write(planned['state']);reply=self.raw(planned['command']);r=publish(self.base/'replies'/(uuid.uuid4().hex+'.json'),reply);self.s['click_reply']=r;self.persist()
  clicked=reply.get('clicked',{});need(reply.get('kind')=='navigation' and clicked.get('selector')==planned['command']['locator']['value'] and clicked.get('disabled') is not True and clicked.get('attributes',{}).get('class')=='button-j4VxiA' and clicked.get('name')=='','paging-click-reply-unverified')
  call=planned['state']['calls'][-1];call.update(state='confirmed',result=reply);self.navigation_write(planned['state']);self.s['calls'].append({'command':planned['command'],'reply':r,'state':'confirmed','source_page':q});self.s.update(state='running',phase='read-first',expected_page=planned['expected_target_page'],loading_wait={'expected_page':planned['expected_target_page'],'started_monotonic':None,'attempts':[]});self.persist();self.last_fresh=None;return self.s
 def run(self,steps):
  if not self.s.get('body_shape_recovery'):return self._run_uncached(steps)
  self.guard()
  with p.A.export_parse_session.owner_session():return self._run_uncached(steps)
 def _run_uncached(self,steps):
  need(type(steps) is int and 1<=steps<=25,'paging-bounded-steps-required')
  for _ in range(steps):
   if self.s['state']!='running':break
   try:self.tick()
   except Exception as e:
    if str(e)=='normal-pager-loading-readonly-wait':
     try:
      prior=self.loading_edge();diagnostic=p.inspect_loading(self.job,document(self.s['latest_page']),self.profile,self.m['receipt'],prior,self.s['expected_page'])
      need(bool(self.s.get('loading_wait')),'paging-loading-persistent-budget-required');self.finish_loading_read(loading=True)
      self.s.setdefault('loading_observations',[]).append({'raw':self.s['latest_page'],'diagnostic':diagnostic});self.s['waiting_for']='normal-pager-loading-readonly-wait';self.persist()
      if len(self.s['loading_wait']['attempts'])>=MAX_LOADING_READS:raise ValueError('normal-pager-loading-readonly-exhausted')
      continue
     except Exception as loading_error:e=loading_error
    self.s.update(state='unknown' if self.s.get('state')=='unknown' else 'hold',error=str(e));self.persist();break
  return {'state':self.s['state'],'phase':self.s['phase'],'error':self.s.get('error'),'operation':ref(self.path),'normal_pages':len(self.s['pages']),'input_replayed':False,'all_normal_read':False}

EDGE_SOURCE_KIND='supervisor-normal-confirmed-edge-source-recovery-v1'
def edge_source_facts(manifest,m,state,nav,source_ref,navigation_ref=None):
 need(state.get('manifest')==manifest and state.get('state')=='hold'and state.get('phase')=='read-first'and state.get('error')=='paging-loading-original-navigation-edge'and not state.get('edge_source_recovery'),'edge-source-original-hold-required')
 need(state.get('loading_wait')=={'expected_page':state['expected_page'],'started_monotonic':None,'attempts':[]},'edge-source-no-read-attempt-required')
 need(all(c.get('state')=='confirmed'for c in state.get('calls',[]))and all(c.get('state')=='confirmed'for c in nav.get('calls',[])),'edge-source-unresolved-input')
 job=document(m['job']);profile=document(m['profile']);document(m['receipt']);document(m['source_journal']);document(m['navigation_archive']);history_scope(job,m['original_navigation']['path'])
 need(state['latest_page']==source_ref,'edge-source-original-page-or-nav-changed')
 navref=navigation_ref or {'path':m['original_navigation']['path'],'sha256':state['navigation_sha256']};need(navref['sha256']==state['navigation_sha256']and document(navref)==nav,'edge-source-original-navigation-binding')
 r=object.__new__(Runner);r.m=m;r.s=state;r.base=Path(manifest['path']).parent;r.job=job;r.profile=profile
 prior=r.loading_edge(navigation=nav,source_page_ref=source_ref);pair=state['pages'][-1]['pair'];first=p.inspect_page(job,document(pair[0]),profile,m['receipt']);second=p.inspect_page(job,document(pair[1]),profile,m['receipt'])
 keys=('scope','normal_header_count','pager','rows','terminal_boundary','pending_rows','visible_normal_card_count')
 need(second==prior and all(first.get(k)==second.get(k)for k in keys)and p.A.stamp(first['observed_at'])<p.A.stamp(second['observed_at']),'edge-source-original-stable-pair')
 transport=document(state['transport'][-1]);call=state['calls'][-1];reply=document(call['reply']);need(transport.get('command')==call['command']and transport.get('reply')=={'ok':True,'result':reply,'error':None}and p.A.stamp(document(source_ref)['observed_at'])<=p.A.stamp(transport['at']),'edge-source-confirmed-transport-binding')
 return {'source_page':source_ref,'source_page_sha256':p.A.data_hash(document(source_ref)),'stable_page':pair[1],'stable_page_sha256':prior['page_sha256'],'tree_and_scope_semantically_unchanged':True,'confirmed_edge_key':'normal-page:'+str(state['expected_page']-1)+'->'+str(state['expected_page']),'confirmed_reply':call['reply'],'observations_consumed':0,'remaining_observations':MAX_LOADING_READS,'loading_clock_not_started':True,'input_replayed':False}

def edge_source_review(manifest,m,review,original_ref=None,nav_ref=None,source_successor=None):
 need(review.get('kind')==EDGE_SOURCE_KIND and review.get('approved')is True and review.get('reviewer_role')=='supervisor'and review.get('manifest')==manifest and review.get('job')==m['job']and review.get('metadata_only')is True and review.get('allow_input_replay')is False,'edge-source-supervisor-review')
 original=original_ref or review['operation_before'];need(original['sha256']==review['operation_before']['sha256'],'edge-source-original-sha');state=document(original);navref=nav_ref or review['navigation'];need(navref['sha256']==state['navigation_sha256']==review['navigation']['sha256'],'edge-source-navigation-sha');nav=document(navref)
 facts=edge_source_facts(manifest,m,state,nav,review['source_page'],navigation_ref=navref);need(facts==review['facts'],'edge-source-reviewed-facts-changed')
 before=review.get('code_before');after=review.get('code_after');target=str(ROOT/'skills/negative-review-complaints/scripts/normal_paging_runner.py');need(before==m['code']and set(after)==set(before)and {k for k in before if before[k]!=after[k]}=={target},'edge-source-only-runner-code-amendment');need(all(ref(k)['sha256']==v or (source_successor is not None and source_successor.get('reuse_reviewed_terminal_first_read') is True and k==target and source_successor['code_before'].get(k)==v and source_successor['code_after'].get(k)==ref(k)['sha256']) for k,v in after.items()),'edge-source-installed-code-mismatch')
 release=document(review['source_release']);ts=release.get('targets',[]);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('reviewed_by')=='workshop-director'and release.get('published')is True and release.get('test_projection_only')is False and len(ts)==1 and ts[0]['target']==target and ts[0]['old_sha256']==before[target]and ts[0]['after']['sha256']==after[target]and ts[0]['mode']==420,'edge-source-published-release-required')
 return state,after,facts

def verified_edge_source_recovery(manifest,m,current,source_successor=None):
 audit=document(current['edge_source_recovery']);review=document(audit['review']);need(audit.get('kind')==EDGE_SOURCE_KIND and audit.get('manifest')==manifest,'edge-source-audit-binding')
 state,after,facts=edge_source_review(manifest,m,review,audit['operation_archive'],audit['navigation_archive'],source_successor=source_successor);need(audit.get('facts')==facts and current.get('pages',[])[:len(state['pages'])]==state['pages']and current.get('calls',[])[:len(state['calls'])]==state['calls'],'edge-source-original-prefix-changed');return after,facts['source_page']

def recover_edge_source(manifest,review_ref):
 m=document(manifest);base=Path(manifest['path']).parent
 with (base/'.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);review=document(review_ref);folder=base/'edge-source-recovery'/review['operation_before']['sha256'];path=base/'operation.json';current=document(ref(path));intent=folder/'intent.json';proof=folder/'proof.json';result=folder/'result.json'
  if result.exists()or result.is_symlink():
   need(intent.exists()and document(ref(intent))=={'manifest':manifest,'review':review_ref,'operation_before':review['operation_before']},'edge-source-terminal-original-intent');out=document(ref(result));need(proof.exists()and current.get('edge_source_recovery')==ref(proof)and out.get('review')==review_ref and out.get('proof')==ref(proof)and out.get('operation_after')==ref(path),'edge-source-terminal-conflict');Runner(manifest).guard();return out
  if intent.exists():need(document(ref(intent))=={'manifest':manifest,'review':review_ref,'operation_before':review['operation_before']},'edge-source-original-intent-conflict')
  old=folder/'original-operation.json';navold=folder/'original-navigation.json';state,after,facts=edge_source_review(manifest,m,review,ref(old)if old.exists()else None,ref(navold)if navold.exists()else None)
  audit={'kind':EDGE_SOURCE_KIND,'manifest':manifest,'review':review_ref,'operation_archive':{'path':str(old),'sha256':review['operation_before']['sha256']},'navigation_archive':{'path':str(navold),'sha256':review['navigation']['sha256']},'facts':facts}
  # Conflicting proof/terminal is rejected before original operation CAS.
  if proof.exists()or proof.is_symlink():need(document(ref(proof))==audit,'edge-source-proof-conflict')
  expected=dict(state,state='running',edge_source_recovery={'path':str(proof),'sha256':__import__('hashlib').sha256(json.dumps(audit,ensure_ascii=False,sort_keys=True).encode()).hexdigest()});expected.pop('error',None)
  need(current==state or current==expected,'edge-source-original-state-changed');need(ref(m['original_navigation']['path'])==review['navigation'],'edge-source-live-navigation-CAS')
  publish(intent,{'manifest':manifest,'review':review_ref,'operation_before':review['operation_before']});immutable(old,Path(review['operation_before']['path']).read_bytes()if current==state else old.read_bytes());immutable(navold,Path(review['navigation']['path']).read_bytes());pr=publish(proof,audit)
  need(pr==expected['edge_source_recovery'],'edge-source-proof-serialization');need(document(ref(path))==current,'edge-source-operation-CAS')
  if current==state:save(path,expected)
  Runner(manifest).guard();out={'kind':EDGE_SOURCE_KIND,'review':review_ref,'proof':pr,'operation_before':review['operation_before'],'operation_after':ref(path),'source_page':facts['source_page'],'input_replayed':False,'rpc_used':False,'outer_clock_reset':False};publish(result,out);return out

def main():
 ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='action',required=True);q=sub.add_parser('prepare')
 for key in ('job','navigation'):
  q.add_argument('--'+key,required=True);q.add_argument('--'+key+'-sha256',required=True)
 q.add_argument('--profile');q.add_argument('--profile-sha256')
 for action in ('run','status','approve-profile','approve-first-page-terminal','finalize','partial-evidence','recover-edge-source'):
  q=sub.add_parser(action);q.add_argument('--manifest',required=True);q.add_argument('--manifest-sha256',required=True)
  if action=='run':q.add_argument('--steps',type=int,default=25)
  if action in ('approve-profile','approve-first-page-terminal','recover-edge-source'):q.add_argument('--review',required=True);q.add_argument('--review-sha256',required=True)
 args=ap.parse_args()
 if args.action=='prepare':
  need(bool(args.profile)==bool(args.profile_sha256),'paging-explicit-profile-hash-required');out={'manifest':prepare(*[{'path':getattr(args,k),'sha256':getattr(args,k+'_sha256')} for k in ('job','navigation')],{'path':args.profile,'sha256':args.profile_sha256} if args.profile else None),'ui_used':False}
 elif args.action=='recover-edge-source':out=recover_edge_source({'path':args.manifest,'sha256':args.manifest_sha256},{'path':args.review,'sha256':args.review_sha256})
 else:
  mr={'path':args.manifest,'sha256':args.manifest_sha256};base=Path(args.manifest).parent
  with (base/'.lock').open('a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);runner=Runner(mr)
   if args.action=='run':out=runner.run(args.steps)
   elif args.action=='approve-profile':out=runner.approve_profile({'path':args.review,'sha256':args.review_sha256})
   elif args.action=='approve-first-page-terminal':out=runner.approve_first_page_terminal({'path':args.review,'sha256':args.review_sha256})
   elif args.action=='finalize':out=runner.finalize()
   elif args.action=='partial-evidence':out=runner.partial_evidence()
   else:out={'operation':ref(runner.path),'state':runner.s['state'],'phase':runner.s['phase'],'ui_used':False}
 print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':
 from runtime_entry import ensure_runtime
 ensure_runtime()
 try:main()
 except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'retry_input':False},ensure_ascii=False));raise SystemExit(2)
