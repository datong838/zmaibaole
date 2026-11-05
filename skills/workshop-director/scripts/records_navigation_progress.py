"""Pure, zero-token normal records navigation observer. No Runner/UI constructors.
Observation is liveness only: always zero business progress tokens.
"""
import hashlib,importlib,json,re,sys
from datetime import datetime
from pathlib import Path

def need(ok,why):
 if not ok:raise ValueError('semantic-records-navigation-'+why)
def canonical(path):
 p=Path(path);need(p.is_absolute() and p.resolve()==p and not p.is_symlink() and p.is_file(),'canonical-file-required');return p
def aware(value):
 at=datetime.fromisoformat(str(value).replace('Z','+00:00'));need(at.utcoffset() is not None,'operation-time-invalid');return at

def verify_operations(operations,refs,entries,query,tab,d,g,target_page_command):
 need(isinstance(operations,list),'operations-required');keys=[];prior=-1;last_end=None
 for op in operations:
  need(isinstance(op,dict) and op.get('state')=='complete' and not op.get('completion_kind') and not op.get('reconciliation'),'operation-unresolved-or-special-reconciliation')
  need(set(op)<= {'key','request','state','before','before_page','intent_at','command','raw_reply','response_at','result','after','completed_at'},'operation-fields-unreviewed')
  key=op.get('key');need(isinstance(key,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',key) and key not in keys,'operation-key-invalid');keys.append(key)
  request=op.get('request');need(isinstance(request,dict) and set(request)=={'action','page','notice_id'},'operation-request-invalid')
  need(op.get('before') in refs,'operation-before-not-observed');i=refs.index(op['before']);need(i>=prior,'operation-observation-order');before,page=entries[i];need(type(op.get('before_page')) is int and op.get('before_page')==page['page'],'operation-before-page-conflict');intent=aware(op.get('intent_at'));need(intent>=aware(before['observed_at']) and (last_end is None or intent>=last_end),'operation-intent-order')
  action=request['action'];target=page['page'];node=None
  if action=='page':
   target=request['page'];need(type(target) is int and target in [x['page'] for x in query['pages']] and request['notice_id'] is None,'operation-page-outside-source')
   command=None if target==page['page'] else {**target_page_command(before['tree'],target),'tabId':tab}
  elif action in ('row','anchor'):
   need(request['page'] is None,'operation-scroll-page-invalid')
   if action=='row':
    need(request['notice_id'] in [x['notice_id'] for x in query['rows']],'operation-notice-outside-source');row=g.one([x for x in page['rows'] if x['notice_id']==request['notice_id']],'monitor-row-not-on-page');selector=row['selector']
   else:need(request['notice_id'] is None,'operation-anchor-arguments');selector=g.date_input(before['tree'])['selector']
   node=g.one([n for n in g.nodes(before['tree']) if n.get('selector')==selector],'monitor-scroll-target-not-unique');need(node.get('tag')==('tr' if action=='row' else 'input'),'operation-scroll-target-tag');command={'op':'scroll','locator':{'by':'selector','value':selector},'tabId':tab}
  else:raise ValueError('semantic-records-navigation-operation-action-unreviewed')
  need(op.get('command')==command,'operation-command-changed')
  if command is None:
   need(not any(k in op for k in ('raw_reply','response_at','result','after','completed_at')),'noop-has-input-evidence');prior=i;last_end=intent;continue
  reply=op.get('raw_reply');need(isinstance(reply,dict) and reply.get('ok') is True and reply.get('result')==op.get('result') and isinstance(op.get('result'),dict),'operation-reply-conflict')
  response=aware(op.get('response_at'));need(response>=intent,'operation-response-order')
  if action=='page':d.reply_matches(command,op['result'],before)
  else:
   result=op['result'];scrolled=result.get('scrolled',{});need(result.get('version')==d.nav.VERSION and all(scrolled.get(k)==node.get(k) for k in ('selector','tag')),'operation-scroll-reply-unverified')
  need(op.get('after') in refs,'operation-after-not-observed');j=refs.index(op['after']);need(j>i,'operation-effect-order');after,actual=entries[j]
  need(actual['page']==target and aware(after['observed_at'])>=response and aware(op.get('completed_at'))>=aware(after['observed_at']),'operation-effect-or-time-unverified');prior=j;last_end=aware(op['completed_at'])

def verify(state,journal_path,*,role,records_directory):
 need(role=='violation_operator','role-conflict');path=canonical(journal_path);original=path.read_bytes();need(json.loads(original)==state,'journal-changed')
 b=state.get('binding',{});need(b.get('schema')=='records-region-navigation-v1','schema-conflict')
 need(set(state)<= {'binding','observations','operations','business_progress_changed','last_observation','updated_at'},'state-fields-unreviewed')
 need(isinstance(state.get('operations'),list) and all(o.get('state')=='complete' and not o.get('completion_kind') for o in state['operations']),'operation-unresolved-or-special-reconciliation');need(state.get('business_progress_changed') is False,'business-progress-claim')
 directory=Path(records_directory).resolve();previous=list(sys.path)
 try:
  sys.path[:0]=[str(directory),str(directory.parents[1]/'chrome-dom-export/scripts')]
  d=importlib.import_module('governance_detail');p=importlib.import_module('prepare_records_profile');gp=importlib.import_module('governance_projection');v=importlib.import_module('verification_session')
  need(Path(d.__file__).resolve()==directory/'governance_detail.py' and Path(p.__file__).resolve()==directory/'prepare_records_profile.py','module-origin-conflict')
  with v.validation_scope() as session:
   dependencies=set();session.frames.append(dependencies)
   try:
    loaded={}
    def document(ref):
     need(isinstance(ref,dict) and set(ref)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(ref.get('sha256',''))),'ref-required')
     f=canonical(ref['path']);raw=f.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'evidence-changed');loaded[f]=raw;return d.document(ref)
    source=document(b.get('source'));profile=document(b.get('profile'));job=document(b.get('job'));query=document(b.get('query'))
    expected_path=Path(b['source']['path']).parent/'.records-region-navigation'/b['source']['sha256']/'state.json';need(path==expected_path,'journal-path-conflict')
    # Full source replay precedes profile/entry proofs; no passed boolean accepted.
    need(p.source_api.validate(b['source']['path'])==source,'source-replay-conflict');p.validate(profile,b['source']);meta=profile['derivation']
    need(b=={'schema':'records-region-navigation-v1','source':b['source'],'profile':b['profile'],'job':meta['job'],'query':meta['query'],'tab_id':meta['tab_id'],'window_id':meta['window_id']},'binding-conflict')
    need(source['identity']==job['identity'] and str(source['groupid'])==str(job['groupid']),'source-identity-conflict')
    # Existing profile replay requires visible full identity at each source query entry.
    for page in query['pages']:d.nav.identity(document(page['observation'])['tree'],job['identity'])
    refs=state.get('observations');need(isinstance(refs,list) and refs and len({json.dumps(r,sort_keys=True) for r in refs})==len(refs) and state.get('last_observation')==refs[-1],'observation-sequence-invalid')
    last=None;visible=[];entries=[]
    for ref in refs:
     f=canonical(ref['path']);need(f.parent==path.parent/'evidence' and re.fullmatch(r'[0-9]{4,}\.json',f.name),'observation-path-conflict');raw=document(ref)
     need(raw.get('source')=='local-dom-bridge' and raw.get('not_business_capture') is True and raw.get('tab_id')==b['tab_id'] and raw.get('tab',{}).get('tabId')==b['tab_id'],'observation-source-conflict')
     at=datetime.fromisoformat(raw['observed_at'].replace('Z','+00:00'));need(at.utcoffset() is not None and (last is None or at>=last),'observation-time-invalid');last=at
     tab=d.nav.context([{'tabs':[raw['tab']]}],b['tab_id'],job['groupid']);need(tab['windowId']==b['window_id'],'window-conflict')
     gp.project(raw['tree'],str(job['groupid']),actual_url=tab['url'],projection_contract=profile.get('projection_contract'))
     entries.append((raw,d.normal_page(raw['tree'],job,query)))
     nodes=list(gp.walk(raw['tree']['root']));cards=[n for n in nodes if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
     need(len(cards)<=1,'identity-card-ambiguous')
     if cards:d.nav.identity(raw['tree'],job['identity'])
     provider=gp.one([n for n in nodes if 'Profile-index-module__title--' in n.get('attributes',{}).get('class','') and re.fullmatch(r'服务商[0-9]+',n.get('name',''))],'monitor-provider')
     need(provider['name']==job['identity']['provider'],'provider-conflict');visible.append(bool(cards))
     need(not any(any(x in n.get('name','') for x in ('扫码登录','风险验证','安全验证','账号异常')) for n in nodes),'risk-stop')
    recovery=importlib.import_module('governance_rates_recovery')
    verify_operations(state['operations'],refs,entries,query,b['tab_id'],d,d.g,recovery.target_page_command)
    for dependency in tuple(dependencies):session._check(dependency)
    for f,raw in loaded.items():need(f.read_bytes()==raw,'evidence-changed-at-end')
    need(path.read_bytes()==original,'journal-changed-at-end')
    return {'schema':'records-region-navigation-v1','binding':b,'tokens':{},'readonly_navigation':{'scope':'observations-and-confirmed-normal-navigation-only','business_progress_changed':False,'full_identity_source':'verified-source-query-entry','visible_full_identity_per_observation':visible,'observations_are_progress':False}}
   finally:session.frames.pop()

 finally:sys.path[:]=previous
