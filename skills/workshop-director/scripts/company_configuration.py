"""Configuration-driven exact company admission. No browser/config writes.
The optional workflow factory writes only its immutable operation artifact.
A configured target is not input authority. The original task/lease and bounded
operation admission remain the caller's responsibility. Never infers a GID.
"""
import contextlib,copy,hashlib,json,re,os
from datetime import timedelta
from pathlib import Path
from datetime import date,datetime,timezone
from contextvars import ContextVar
ROOT=Path(__file__).resolve().parents[3]
CONFIG_POINTER=ROOT/'skills/workshop-director/config/approved-company-scope.json'
_SEARCH_COMMAND=ContextVar('explicit_search_progression_command',default=None)
_SEARCH_HISTORY_ACTIVE=ContextVar('explicit_search_history_pin',default=False)
KINDS={'context-discovery','company-select','company-confirm','business'}
def need(ok,why):
 if not ok:raise ValueError(why)
def regular(path):
 p=Path(path);need(p.is_absolute()and p==p.resolve()and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'company-config-canonical-regular')
 if _SEARCH_HISTORY_ACTIVE.get():
  active=_SEARCH_COMMAND.get();need(active is not None,'search-history-command-scope');timing=active['timing'];state=timing._POLICY_COMMAND.get();token=_SEARCH_HISTORY_ACTIVE.set(False)
  try:timing._policy_pin(state,{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},'source_hashes')
  finally:_SEARCH_HISTORY_ACTIVE.reset(token)
 return p
def raw(reference):
 need(type(reference)is dict and set(reference)=={'path','sha256'}and type(reference['path'])is str and re.fullmatch('[a-f0-9]{64}',str(reference['sha256'])),'company-config-ref');p=regular(reference['path']);b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==reference['sha256'],'company-config-ref-drift');return b
def doc(reference):return json.loads(raw(reference))
def require_no_visible_system_error(tree):
 """Same reviewed toast semantics as review_visible_system_error, not text search.
 The DOM bridge emits visible nodes only, including ancestor-opacity filtering
 for message-content. A merchant/review leaf with this text is not a toast.
 A structured but malformed/ambiguous known toast fails closed as unverified.
 """
 import dom_evidence as dom
 message='系统错误，请稍后再试';ns=list(dom.nodes(tree));candidates=[n for n in ns if n.get('name')==message and 'life-core-message-content'in n.get('attributes',{}).get('class','').split()and not any(c.get('name')==message for c in n.get('children',[]))]
 if not candidates:return
 target=dom.unique(candidates,'company-visible-system-error-ambiguous');need(target.get('tag')=='span'and target.get('attributes',{}).get('class')=='life-core-message-content','company-visible-system-error-unverified');ancestors=[n for n in ns if 'life-core-message-type-error'in n.get('attributes',{}).get('class','').split()and any(x is target for x in dom.nodes({'root':n,'truncated':False}))];dom.unique(ancestors,'company-visible-system-error-unverified');raise ValueError('company-visible-system-error')
# Reviewed DOM-bridge builds accepted for stored evidence. Archived company
# bindings were captured under earlier reviewed builds; equality against the
# CURRENT version alone invalidated every stored binding on each extension
# bump (observed 2026-11-03: v11 archive vs v12 extension). Membership keeps
# the fail-closed property (only reviewed builds) without that cliff.
REVIEWED_DOM_VERSIONS=('dom-only-20261021-10','dom-only-20261021-11','dom-only-20261103-12')
# B83: this module is imported from several entry chains (bridge-workflow runs
# with its own scripts dir on sys.path, but flow.py/daily_timed_run advance do
# not). Locate the reviewed dom_evidence relative to this file so every entry
# chain resolves the same reviewed module instead of ModuleNotFoundError.
import sys as _sys
_douyin_laike_scripts=str(Path(__file__).resolve().parents[2]/'douyin-laike-operator'/'scripts')
if _douyin_laike_scripts not in _sys.path:_sys.path.insert(0,_douyin_laike_scripts)
import dom_evidence as _dom_ev
REVIEWED_DOM_VERSIONS=REVIEWED_DOM_VERSIONS+(_dom_ev.VERSION,)

def full_identity(v):return type(v)is dict and set(v)=={'provider','account_id','manager'}and all(type(v[k])is str and bool(v[k].strip())for k in v)and re.fullmatch(r'服务商[0-9]+',v['provider'])is not None and v['account_id'].isdigit()
def exact_name(v):return type(v)is str and 1<=len(v)<=100 and v==v.strip()and not any(c in v for c in '\r\n\x00')
def decode_config(value):
 need(type(value)is dict and set(value)=={'kind','entries'}and value['kind']=='configured-company-scope-v2'and type(value['entries'])is list and bool(value['entries']),'company-config-schema');byid={};byname={};byg={}
 for row in value['entries']:
  need(type(row)is dict and set(row)=={'id','company','provider','status','capabilities','production_group','brand','verified'}and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',str(row['id']))and exact_name(row['company'])and re.fullmatch(r'服务商[0-9]+',str(row['provider']))and row['status']in('pending-discovery','active','retired')and exact_name(row['production_group'])and exact_name(row['brand']),'company-config-entry')
  need('/'not in row['company']and '\\'not in row['company']and row['company']not in('.','..'),'company-config-company-path-forbidden')
  need(type(row['capabilities'])is list and len(row['capabilities'])==len(set(row['capabilities']))and set(row['capabilities'])<=KINDS,'company-config-capabilities')
  need(row['id']not in byid and row['company']not in byname,'company-config-duplicate-name-id')
  verified=row['verified']
  if verified is None:need(row['status']!='active'and set(row['capabilities'])<={'context-discovery','company-select','company-confirm'},'company-config-unverified-business')
  else:
   need(type(verified)is dict and set(verified)=={'groupid','identity','context_proof'}and type(verified['groupid'])is str and re.fullmatch('[0-9]{1,32}',verified['groupid'])and full_identity(verified['identity'])and verified['identity']['provider']==row['provider'],'company-config-verified-scope');need(verified['groupid']not in byg,'company-config-duplicate-gid');byg[verified['groupid']]=row['id']
   need(type(verified['context_proof'])is dict and set(verified['context_proof'])=={'path','sha256'},'company-config-proof-required')
  if row['status']=='retired':need(not row['capabilities'],'company-config-retired-capability')
  byid[row['id']]=copy.deepcopy(row);byname[row['company']]=row['id']
 return byid,byname
class Config:
 """One explicit command-bound version. No global/persistent config cache.
 Full content hashes at both boundaries, per-lookup inode/ctime/mtime/size
 checks (including the held fd) reject version drift before the next action.
 Live identity/DOM facts are deliberately not cached here.
 """
 def __init__(self,reference):
  self.reference=copy.deepcopy(reference);path=regular(reference['path']);before=self._stamp(path);self.bytes=raw(reference);self.version=self._stamp(path);need(before==self.version,'company-config-raced-during-read');self.byid,self.byname=decode_config(json.loads(self.bytes));self.bygid={r['verified']['groupid']:r['id']for r in self.byid.values()if r['verified']};self.counts={'parses':1,'lookups':0,'fresh_checks':0,'config_reads':1,'config_hashes':1,'fingerprint_checks':0};self._held=None
 @staticmethod
 def _stamp(path):
  s=regular(path).stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode)
 def _version_current(self):
  need(self._stamp(self.reference['path'])==self.version,'company-config-version-drift')
  if self._held is not None:
   s=os.fstat(self._held.fileno());need((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode)==self.version,'company-config-held-version-drift')
  self.counts['fingerprint_checks']+=1
 @contextlib.contextmanager
 def bounded(self):
  need(self._held is None,'company-config-scope-already-active');self._version_current()
  with regular(self.reference['path']).open('rb')as held:
   self._held=held
   try:
    self._version_current();yield self;self._version_current();need(raw(self.reference)==self.bytes,'company-config-command-exit-drift');self.counts['config_reads']+=1;self.counts['config_hashes']+=1;self._version_current()
   finally:self._held=None
 def fresh(self):
  if self._held is not None:self._version_current()
  else:
   need(raw(self.reference)==self.bytes,'company-config-current-changed');self.counts['config_reads']+=1;self.counts['config_hashes']+=1
  self.counts['fresh_checks']+=1
 def entry(self,entry_id,*,purpose):
  self.fresh();self.counts['lookups']+=1;need(purpose in KINDS and entry_id in self.byid,'company-config-entry-unapproved');v=self.byid[entry_id];need(v['status']!='retired'and purpose in v['capabilities'],'company-config-not-authorized');return copy.deepcopy(v)
 def business(self,entry_id):
  v=self.entry(entry_id,purpose='business');need(v['status']=='active'and v['verified']is not None and full_identity(v['verified']['identity'])and v['verified']['identity']['provider']==v['provider'],'company-config-business-unverified');return v

_CONFIG_COMMAND=ContextVar('configured_company_command',default=None)
@contextlib.contextmanager
def configuration_command():
 """Explicit bounded command only, complete hashes at enter/exit per version."""
 need(_CONFIG_COMMAND.get()is None,'company-config-command-already-active')
 with contextlib.ExitStack()as stack:
  cache={};token=_CONFIG_COMMAND.set((cache,stack))
  try:yield cache
  finally:_CONFIG_COMMAND.reset(token)
def get_config(reference):
 active=_CONFIG_COMMAND.get()
 if active is None:return Config(reference)
 cache,stack=active;key=json.dumps(reference,sort_keys=True,separators=(',',':'))
 if key not in cache:
  config=Config(reference);stack.enter_context(config.bounded());cache[key]=config
 return cache[key]

def approved_config(pointer=CONFIG_POINTER):
 p=regular(pointer);value=json.loads(p.read_bytes());need(type(value)is dict and set(value)=={'kind','config'}and value['kind']=='approved-company-configuration-pointer-v1','company-config-approved-pointer');return get_config(value['config'])
def configured_source_identity(job,groupid,*,config=None):
 """Fresh v2 jobs pin one configuration authority, not N copied identities.
 Only an active, proof-verified source in that exact policy can be recognized.
 Any legacy supplied identities remain data-only unless their GID is selected.
 """
 need(job.get('company_configuration_registry')=='configured-source-index-v2','company-configured-source-contract');policy=doc(job['company_configuration_policy']);config=config or get_config(policy['configuration']);need(policy['kind']=='active-company-scope-policy-v2'and policy['configuration']==config.reference,'company-configured-source-policy');config.fresh();entry=config.bygid.get(str(groupid));need(entry is not None and entry in policy['active_ids'],'company-configured-source-inactive-or-unknown');row=config.business(entry);need(row['provider']==job['provider_baseline'],'company-configured-source-provider');known=job.get('known_company_identities',{}).get(str(groupid));need(known is None or known==row['verified']['identity'],'company-configured-source-known-conflict');return row['verified']['identity']

def operation(config,reference,*,now=None):
 """Exact operation input only; never constructs/extends its authorization."""
 v=doc(reference);base={'kind','config','entry_id','key','tab_id','window_id','source_groupid','provider','source_identity','date_range','issued_at','expires_at','purpose','original_job'};search_only=type(v)is dict and v.get('purpose')=='explicit-single-company-search-only-v1';confirm_only=type(v)is dict and v.get('purpose')=='configured-business-confirm-successor-v1';remaining=type(v)is dict and v.get('purpose')in('configured-business-remaining-context-v1','configured-business-confirm-successor-v1');schemas=(base|{'allowed_action'},base|{'allowed_action','source_entry'})if search_only else((base|{'recovery_proof','predecessor','selection','supersedes','allowed_action'},base|{'recovery_proof','predecessor','selection','supersedes','allowed_action','source_entry'})if confirm_only else((base|{'recovery_proof'},base|{'recovery_proof','source_entry'})if remaining else(base,base|{'source_entry'},base|{'source_bootstrap'})));need(type(v)is dict and set(v)in schemas and v['kind']=='configured-company-operation-v2'and v['config']==config.reference,'company-operation-schema');need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',str(v['key']))and v['purpose']in('context-discovery','configured-business-company-context','explicit-single-company-search-only-v1','configured-business-remaining-context-v1','configured-business-confirm-successor-v1'),'company-operation-key-purpose');
 if search_only:need(v['allowed_action']=={'op':'filter','kind':'filter','max_inputs':1}and type(v['allowed_action']['max_inputs'])is int,'company-search-only-action')
 if not search_only and not remaining:
  caller_path=Path(reference['path']).parent/'action-intent.json'
  if caller_path.exists():need(json.loads(regular(caller_path).read_bytes()).get('kind')!='explicit-original-search-action-intent-v1','company-search-ticket-purpose-widening')
 need(all(type(v[k])is int and 0<v[k]<=9007199254740991 for k in('tab_id','window_id'))and type(v['source_groupid'])is str and re.fullmatch('[0-9]{1,32}',v['source_groupid']),'company-operation-scope')
 start=datetime.fromisoformat(v['issued_at']);end=datetime.fromisoformat(v['expires_at']);now=now or datetime.now(timezone.utc);need(start.utcoffset()is not None and end.utcoffset()is not None and now.utcoffset()is not None and start<=now<=end and 0<(end-start).total_seconds()<=300,'company-operation-expired-or-unbounded');d=v['date_range'];need(type(d)is dict and set(d)=={'start','end_exclusive'}and date.fromisoformat(d['start'])<date.fromisoformat(d['end_exclusive']),'company-operation-dates')
 row=config.entry(v['entry_id'],purpose='context-discovery'if v['purpose']=='context-discovery'else'business');need(v['provider']==row['provider']and full_identity(v['source_identity'])and v['source_identity']['provider']==v['provider'],'company-operation-provider')
 if v['purpose']=='context-discovery':need(v['original_job']is None,'company-discovery-not-business-job')
 else:
  job=doc(v['original_job']);need(job.get('action')in('acquire','return-company')and job.get('work_order_path')==v['original_job']['path']and job.get('work_order_id')and job.get('company_configuration_entry')==row['id']and job.get('company')==row['company'],'company-operation-original-job')
  policy=doc(job['company_configuration_policy']);need(policy.get('kind')=='active-company-scope-policy-v2'and policy['configuration']==config.reference and row['id']in policy['active_ids'],'company-operation-original-policy');source=policy['configuration_code'];need(source['path']==str(Path(__file__).resolve())and configuration_code_bytes(source),'company-operation-original-code')
  known=config.business(row['id']);source_identity=configured_source_identity(job,v['source_groupid'],config=config)if job.get('company_configuration_registry')=='configured-source-index-v2'else(job.get('known_company_identities',{}).get(v['source_groupid'])if v['source_groupid']in job.get('allowed_groupids',[])else None);need(source_identity==v['source_identity'],'company-operation-known-original-source');need(str(job.get('groupid'))==known['verified']['groupid']and job.get('identity_baseline')==known['verified']['identity']and job.get('known_company_identities',{}).get(str(job['groupid']))==job['identity_baseline']and job.get('provider_baseline')==known['provider'],'company-operation-business-target');dates=job.get('date_range',{});need(dates.get('start')==d['start']and dates.get('end_exclusive')==d['end_exclusive'],'company-operation-business-date')
 if 'source_bootstrap'in v:
  need(v['purpose']=='context-discovery','company-bootstrap-discovery-only');source_bootstrap_authority(config,v)
 if 'source_entry'in v:
  if v['purpose']in('configured-business-company-context','explicit-single-company-search-only-v1','configured-business-remaining-context-v1','configured-business-confirm-successor-v1'):need(v['source_entry']=={'kind':'original-job-login-company-picker-v2','authority':v['original_job']},'company-login-original-authority')
  else:login_discovery_authority(config,v)
 if remaining:
  facts=verify_search_terminal(v['recovery_proof'],v['original_job']);need(facts['job']==v['original_job']and v['key'].startswith('configured-confirm:'if confirm_only else'configured-remaining:')and v['key']!=facts['operation']['key']and {k:v[k]for k in('config','entry_id','tab_id','window_id','source_groupid','provider','source_identity','date_range','original_job')}=={k:facts['operation'][k]for k in('config','entry_id','tab_id','window_id','source_groupid','provider','source_identity','date_range','original_job')},'company-remaining-original-task-binding')
 if confirm_only:_confirm_successor_data(config,reference,v,row,facts)
 return v,row

def login_discovery_authority(config,op):
 """An approved discovery operation also binds one verified existing source.
 The login DOM itself cannot supply provider/account/GID authorization.
 """
 from readonly_tick_snapshot import decode
 import dom_evidence as dom
 x=op['source_entry'];need(type(x)is dict and set(x)=={'kind','authority'}and x['kind']=='verified-config-login-company-picker-v2','company-login-source-authority');reply=doc(x['authority']);value=decode(reply.get('result')if reply.get('ok')is True else reply,op['tab_id'],op['window_id']);before=entry_context(value['before'],op['tab_id'],op['window_id']);after=entry_context(value['after'],op['tab_id'],op['window_id']);need(before==after and before['groupid']==op['source_groupid']and value['tree'].get('truncated')is False and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-login-source-observation');observed=dom.identity(value['tree'],op['source_identity']);sources=[v for v in config.byid.values()if v.get('verified')and v['verified']['groupid']==op['source_groupid']];source=dom.unique(sources,'company-login-source-config-unique');actual=config.business(source['id']);need(actual['verified']['identity']==observed and actual['provider']==op['provider'],'company-login-source-config-identity')

def source_bootstrap_authority(config,op):
 """New bounded operation only. A pinned verified source is not a target receipt."""
 x=op['source_bootstrap'];need(type(x)is dict and set(x)=={'kind','authority'}and x['kind']=='verified-source-account-picker-bootstrap-v2','company-bootstrap-authority')
 # Reuse the exact already verified source scope/config identity contract.
 proxy=dict(op,source_entry={'kind':'verified-config-login-company-picker-v2','authority':x['authority']});login_discovery_authority(config,proxy)

def source_bootstrap_scope(snapshot,op):
 from readonly_tick_snapshot import decode
 from urllib.parse import urlsplit,parse_qs
 import dom_evidence as dom
 need('source_bootstrap'in op and 'source_entry'not in op,'company-bootstrap-explicit-operation');value=decode(snapshot,op['tab_id'],op['window_id']);before=entry_context(value['before'],op['tab_id'],op['window_id']);after=entry_context(value['after'],op['tab_id'],op['window_id']);need(before==after and before['groupid']==op['source_groupid']and parse_qs(urlsplit(before['url']).query,keep_blank_values=True).get('groupid')==[op['source_groupid']]and value['tree'].get('url')==before['url'].split('?')[0]and value['tree'].get('truncated')is False and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-bootstrap-source-scope');require_no_visible_system_error(value['tree']);return value

def source_bootstrap_input(snapshot,op,stage):
 """Exact observed HeaderV3 account trigger / existing semantic switch only."""
 import dom_evidence as dom
 value=source_bootstrap_scope(snapshot,op);tree=value['tree'];ns=list(dom.nodes(tree));need(not any(n.get('role')=='dialog'for n in ns),'company-bootstrap-dialog-already-present')
 if stage=='open-picker':
  dom.identity(tree,op['source_identity']);target=dom.company_switch(tree);need(target.get('selector')and not target.get('disabled'),'company-bootstrap-switch-ready');return target
 need(stage=='source-identity-hover'and not any('UserCard-index-module__outer--'in n.get('attributes',{}).get('class','')for n in ns),'company-bootstrap-profile-missing-only')
 try:dom.identity(tree)
 except ValueError as error:need(str(error)in('identity-provider-unverified','identity-account-unverified','identity-manager-unverified'),'company-bootstrap-profile-not-missing')
 else:raise ValueError('company-bootstrap-profile-already-complete')
 prefix='src-components-HeaderV3-components-Profile-index-module__title--';target=dom.unique([n for n in dom.leaves(tree)if n.get('name')==op['provider']and n.get('tag')=='div'and n.get('role')=='generic'and any(x.startswith(prefix)for x in n.get('attributes',{}).get('class','').split())],'company-bootstrap-trigger-unique');need(target.get('selector','').startswith('#main-app > section > section > header > ')and not target.get('disabled'),'company-bootstrap-header-control');return target

def verify_source_bootstrap(proof,op,last):
 """Receipts remain evidence of distinct once-only inputs, never a replay permit."""
 if 'source_bootstrap'not in proof:return last
 need('source_bootstrap'in op and type(proof['source_bootstrap'])is dict and set(proof['source_bootstrap'])=={'identity_hover','open_picker'},'company-context-bootstrap-schema')
 for key,stage in(('identity_hover','source-identity-hover'),('open_picker','open-picker')):
  reference=proof['source_bootstrap'][key]
  if reference is None:need(key=='identity_hover','company-context-bootstrap-open-required');continue
  step=doc(reference);need(type(step)is dict and set(step)=={'kind','operation','key','before','command','reply','state','at'}and step['kind']=='configured-company-input-v2'and step['operation']==proof['operation']and step['key']==op['key']+':'+stage and step['state']=='confirmed','company-context-bootstrap-prefix');prior=doc(step['before']);need(prior.get('ok')is True,'company-context-bootstrap-before');target=source_bootstrap_input(prior['result'],op,stage);action='hover'if stage=='source-identity-hover'else'click';need(step['command']=={'op':action,'tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},'company-context-bootstrap-command');reply=doc(step['reply']);node=reply.get('result',{}).get('hovered'if action=='hover'else'clicked',{});need(reply.get('ok')is True and node.get('name')==target['name']and node.get('selector')==target['selector']and (action=='hover'or reply['result'].get('kind')=='navigation'),'company-context-bootstrap-effect');at=datetime.fromisoformat(step['at']);need(at.utcoffset()is not None and last<=at<=datetime.fromisoformat(op['expires_at']),'company-context-bootstrap-time');last=at
 return last

def admit_command(command,*,pointer=CONFIG_POINTER,now=None,_claim_search_only=False):
 """Called only by authenticated bridge server before queueing. A caller may
 provide an operation ref, never the derived company capability. The fixed
 local approved pointer cannot be replaced by any command field.
 """
 need(type(command)is dict and 'companyCapability'not in command,'company-capability-caller-forbidden')
 if 'companyRequest'not in command:return copy.deepcopy(command)
 reference=command['companyRequest']
 if _claim_search_only:
  initial=doc(reference);claim=Path(reference['path']).parent/'server-search-intent.json'
  if initial.get('purpose')=='explicit-single-company-search-only-v1'and(claim.exists()or claim.is_symlink()):raise SearchOpportunityConsumed('company-search-opportunity-consumed')
  if initial.get('purpose')=='configured-business-confirm-successor-v1':
   claim=Path(reference['path']+'.server-intent.json')
   if claim.exists()or claim.is_symlink():raise SearchOpportunityConsumed('company-confirm-opportunity-consumed')
 config=approved_config(pointer);op,row=operation(config,reference,now=now);search_only=op['purpose']=='explicit-single-company-search-only-v1';
 if op['purpose']=='configured-business-remaining-context-v1':need(command.get('op')=='click'and command.get('kind')in('company','company-confirm'),'company-remaining-no-search')
 if op['purpose']=='configured-business-confirm-successor-v1':need(command.get('op')=='click'and command.get('kind')=='company-confirm','company-confirm-successor-no-search-select')
 if search_only:
  need(_claim_search_only is True,'company-search-only-server-claim-protocol-required')
  need(command.get('op')=='filter'and command.get('kind')=='filter','company-search-only-no-select-confirm')
 need(command.get('tabId')==op['tab_id']and command.get('op')in('filter','click'),'company-command-scope');action='company-select'if command.get('kind')=='company'else'company-confirm'if command.get('kind')=='company-confirm'else('business'if op['purpose']in('configured-business-company-context','explicit-single-company-search-only-v1','configured-business-remaining-context-v1','configured-business-confirm-successor-v1')else'context-discovery');config.entry(row['id'],purpose=action)
 if command['op']=='filter':need(set(command)in({'op','tabId','locator','value','companyRequest'},{'op','tabId','locator','value','kind','companyRequest'})and command.get('kind','filter')=='filter'and command.get('value')==row['company'],'company-command-exact-search')
 else:need(set(command)=={'op','tabId','locator','kind','companyRequest'}and command.get('kind')in('company','company-confirm'),'company-command-action')
 cap={'kind':'approved-exact-company-capability-v2','config':config.reference,'request':reference,'entry_id':row['id'],'company':row['company'],'provider':row['provider'],'tabId':op['tab_id'],'windowId':op['window_id'],'sourceGroupid':op['source_groupid'],'sourceIdentity':op['source_identity'],'key':op['key'],'expires_at':op['expires_at']};
 if 'source_entry'in op:cap['sourceEntry']=copy.deepcopy(op['source_entry'])
 out={k:copy.deepcopy(v)for k,v in command.items()if k!='companyRequest'};out['companyCapability']=cap
 if search_only:
  facts=_explicit_search_facts(reference,op,command,now=now)
  if _claim_search_only:_claim_explicit_search(reference,op,command,facts,now=now)
 if op['purpose']=='configured-business-confirm-successor-v1':
  need(_claim_search_only is True,'company-confirm-server-claim-required');_claim_confirm_successor(reference,op,command,now=now)
 return out


def _explicit_search_facts(reference,op,command,*,now=None,_historical=False):
 """Data proof only. Approval authenticity remains the independently reviewed
 Root fixed invocation/local authenticated CLI boundary, not a JSON marker.
 This cannot grant selection/confirmation or manufacture/renew an authority.
 """
 now=now or datetime.now(timezone.utc);folder=regular(reference['path']).parent;need(Path(reference['path']).name=='new-operation.json','company-search-operation-name');ir={'path':str(folder/'action-intent.json'),'sha256':hashlib.sha256(regular(folder/'action-intent.json').read_bytes()).hexdigest()};intent=doc(ir)
 keys={'kind','authority','consent','original_workflow','original_unknown','original_archive','recovery_key','scope','operation','command','at'}
 need(type(intent)is dict and set(intent)==keys and intent['kind']=='explicit-original-search-action-intent-v1'and intent['operation']==reference and intent['command']==command,'company-search-caller-intent')
 authority_ref=intent['authority'];a=doc(authority_ref);keys={'kind','execution_authorized','actor','consent','original_workflow','job','original_operation','task','attempt','outer','ticket','recovery_key','issued_at','expires_at','max_inputs'}
 need(type(a)is dict and set(a)==keys and a['kind']=='root-explicit-single-company-search-recovery-v1'and a['execution_authorized']is True and type(a['max_inputs'])is int and a['max_inputs']==1 and a['ticket']==str(folder)and a['job']==op['original_job']and a['recovery_key']==op['key']==intent['recovery_key'],'company-search-authority-binding');raw(a['actor'])
 start=datetime.fromisoformat(a['issued_at']);end=datetime.fromisoformat(a['expires_at']);at=datetime.fromisoformat(intent['at']);need(start.utcoffset()is not None and end.utcoffset()is not None and at.utcoffset()is not None and start<=at<=now<end and 0<(end-start).total_seconds()<=300 and op['issued_at']==a['issued_at']and op['expires_at']==a['expires_at'],'company-search-authority-expired')
 expected={'kind':'explicit-user-company-search-recovery-approval-v1','approved':True,'task':a['task'],'attempt':a['attempt'],'job':a['job'],'original_workflow':a['original_workflow'],'original_call_key':'2:searchCompany','allow_new_search':True,'max_inputs':1,'original_unknown_preserved':True,'issued_at':a['issued_at'],'expires_at':a['expires_at']}
 consent=doc(a['consent']);need(intent['consent']==a['consent']and consent==expected and consent.get('approved')is True and consent.get('allow_new_search')is True and consent.get('original_unknown_preserved')is True and type(consent.get('max_inputs'))is int,'company-search-explicit-consent')
 archive={'path':str(folder/'original-workflow.json'),'sha256':a['original_workflow']['sha256']};need(intent['original_workflow']==a['original_workflow']and intent['original_archive']==archive,'company-search-original-archive');wf=doc(archive);need(_historical or raw(a['original_workflow'])==raw(archive),'company-search-original-current-drift');calls=wf['calls'];need(wf['phase']=='searchCompany'and wf['revision']==2 and len(calls)==2 and calls[0]['state']=='confirmed'and calls[1]['state']=='unknown'and calls[1]['key']=='2:searchCompany'and calls[1]==intent['original_unknown'],'company-search-original-unknown')
 old=calls[1]['command'];need(old.get('op')=='filter'and old.get('kind')=='filter'and old.get('companyRequest')==a['original_operation']==wf['company_configuration_operation']and command=={**old,'companyRequest':reference}and any(r.get('call_key')=='2:searchCompany' and r.get('command')==old and r.get('reply')is None and r.get('raw_reply_available')is False for r in wf.get('bridge_failures',[])),'company-search-original-command')
 previous=doc(a['original_operation']);need({k:v for k,v in op.items()if k not in('key','issued_at','expires_at','purpose','allowed_action')}=={k:v for k,v in previous.items()if k not in('key','issued_at','expires_at','purpose')}and op['key']!=previous['key'],'company-search-operation-scope-drift')
 scope=intent['scope'];need(type(scope)is dict and set(scope)=={'raw','observed_at'},'company-search-before-scope');observed=datetime.fromisoformat(scope['observed_at']);need(observed.utcoffset()is not None and 0<=(now-observed).total_seconds()<=5,'company-search-before-stale')
 job=doc(a['job']);base={k:v for k,v in command.items()if k!='companyRequest'};planned,checked=business_command(job,base,scope['raw'],reference,Path(reference['path']),op['key'],now=now);need(planned==command and checked==reference,'company-search-fresh-strict-input');need(_historical or not(folder/'action-result.json').exists(),'company-search-already-terminal')
 return {'intent':ir,'authority':authority_ref,'expires':end}

class SearchOpportunityConsumed(ValueError):pass

def _claim_explicit_search(reference,op,command,facts,*,now=None):
 """Single durable server enqueue opportunity. Never remove/reuse a claim.
 A crash after this claim but before Jobs.add is HOLD, not retry permission.
 """
 path=Path(reference['path']).parent/'server-search-intent.json';need(path==path.resolve()and not any(x.is_symlink()for x in(path,*path.parents)),'company-search-server-intent-path');value={'kind':'explicit-single-search-server-intent-v1','operation':reference,'caller_intent':facts['intent'],'authority':facts['authority'],'command':copy.deepcopy(command),'max_inputs':1};data=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
 # All validation/encoding is complete before the final clock/open boundary.
 clock=now or datetime.now(timezone.utc);need(clock<facts['expires'],'company-search-expired-before-enqueue')
 try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
 except FileExistsError:raise SearchOpportunityConsumed('company-search-opportunity-consumed')from None
 # O_EXCL success consumes the opportunity, even if no valid JSON or fsync
 # follows. Never classify ANY ordinary post-create failure as retryable denial.
 stream=None
 try:
  stream=os.fdopen(fd,'wb');fd=None
  with stream as f:f.write(data);f.flush();os.fsync(f.fileno())
  d=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(d)
  finally:os.close(d)
  if not(now or datetime.now(timezone.utc))<facts['expires']:raise SearchOpportunityConsumed('company-search-opportunity-consumed')
 except Exception:
  if fd is not None:
   try:os.close(fd)
   except Exception:pass
  if stream is not None:
   try:stream.close()
   except Exception:pass
  raise SearchOpportunityConsumed('company-search-opportunity-consumed')from None


def verify_context_proof(reference):
 """Deep context-only proof. Never treats picker observations as acquisition.
 Historical operation authorization is checked at its original issued time;
 current business admission separately rehashes the current config per action.
 """
 from urllib.parse import urlsplit,parse_qs
 import dom_evidence as dom
 from readonly_tick_snapshot import decode
 proof=doc(reference)
 if proof.get('kind')=='verified-acquisition-company-context-v2':return acquisition_context(proof)
 if proof.get('kind')=='observed-company-context-import-v2':return observed_context(proof)
 base={'kind','operation','selection','confirmation','observations'};need(type(proof)is dict and base<=set(proof)<=base|{'identity_hover','source_bootstrap'}and proof['kind']in('configured-company-context-proof-v2','configured-login-company-context-proof-v2'),'company-context-proof-schema');op=doc(proof['operation']);need(op.get('purpose')=='context-discovery','company-context-registration-discovery-only');config=get_config(op['config']);op,row=operation(config,proof['operation'],now=datetime.fromisoformat(op['issued_at']));last=datetime.fromisoformat(op['issued_at'])
 last=verify_source_bootstrap(proof,op,last)
 login=proof['kind']=='configured-login-company-context-proof-v2';need((proof['confirmation']is None and 'source_entry'in op)if login else('source_entry'not in op),'company-context-proof-entry-kind')
 for phase,action in ([('selection','company')]if login else[('selection','company'),('confirmation','company-confirm')]):
  step=doc(proof[phase]);need(type(step)is dict and set(step)=={'kind','operation','key','before','command','reply','state','at'}and step['kind']=='configured-company-input-v2'and step['operation']==proof['operation']and step['key']==op['key']+':'+phase and step['state']=='confirmed','company-context-confirmed-input-required');command=step['command'];need(command.get('op')=='click'and command.get('tabId')==op['tab_id']and command.get('kind')==action and command.get('companyRequest')==proof['operation'],'company-context-input-binding');prior=doc(step['before']);need(prior.get('ok')is True,'company-context-input-before-error');target=input_before(prior['result'],op,row,action);need(command.get('locator')=={'by':'selector','value':target['selector']},'company-context-input-locator');reply=doc(step['reply']);need(reply.get('ok')is True and type(reply.get('result'))is dict and reply['result'].get('kind')==action and reply['result'].get('clicked',{}).get('selector')==target['selector']and reply['result']['clicked'].get('name')==target['name'],'company-context-input-effect');at=datetime.fromisoformat(step['at']);need(at.utcoffset()is not None and last<=at<=datetime.fromisoformat(op['expires_at']),'company-context-input-time');last=at
 if 'identity_hover'in proof:
  step=doc(proof['identity_hover']);need(type(step)is dict and set(step)=={'kind','operation','key','before','command','reply','state','at'}and step['kind']=='configured-company-input-v2'and step['operation']==proof['operation']and step['key']==op['key']+':identity-hover'and step['state']=='confirmed','company-context-hover-prefix');prior=doc(step['before']);need(prior.get('ok')is True,'company-context-hover-before');target,gid=identity_hover_before(prior['result'],op,row);need(step['command']=={'op':'hover','tabId':op['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},'company-context-hover-command');reply=doc(step['reply']);need(reply.get('ok')is True and reply['result'].get('hovered',{}).get('name')==row['provider']and reply['result']['hovered'].get('selector')==target['selector'],'company-context-hover-effect');at=datetime.fromisoformat(step['at']);need(at.utcoffset()is not None and last<=at<=datetime.fromisoformat(op['expires_at']),'company-context-hover-time');last=at
 observations=proof['observations'];need(type(observations)is list and len(observations)==2 and observations[0]!=observations[1],'company-context-two-fresh-observations');identities=[];gids=[];seen=set()
 for item in observations:
  need(type(item)is dict and set(item)=={'command','raw_reply','observed_at'}and item['command']=={'op':'readonly-scope','tabId':op['tab_id'],'windowId':op['window_id']}and item['raw_reply']['path']not in seen,'company-context-observation-binding');seen.add(item['raw_reply']['path']);reply=doc(item['raw_reply']);need(reply.get('ok')is True,'company-context-observation-error');value=decode(reply['result'],op['tab_id'],op['window_id']);before=dom.context(value['before'],op['tab_id']);after=dom.context(value['after'],op['tab_id']);need(before==after and before['windowId']==op['window_id'],'company-context-observation-scope');u=urlsplit(before['url']);need(u.path in('/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management')and not u.fragment and before['groupid'].isdigit()and parse_qs(u.query,keep_blank_values=True).get('groupid')==[before['groupid']],'company-context-observation-route');tree=value['tree'];require_no_visible_system_error(tree);need(tree.get('truncated')is False and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-context-reviewed-tree');identity=dom.identity(tree);label=company_label(tree);need(identity['provider']==row['provider']and label.get('name')==row['company'],'company-context-exact-company-identity');at=datetime.fromisoformat(item['observed_at']);need(at.utcoffset()is not None and last<at<=datetime.fromisoformat(op['expires_at']),'company-context-fresh-observation-time');last=at;identities.append(identity);gids.append(before['groupid'])
 need(identities[0]==identities[1]and gids[0]==gids[1],'company-context-stable-identity-required');raw(reference)
 return {'company':row['company'],'groupid':gids[0],'identity':identities[0],'context_only':True,'acquisition_receipt':False,'business_resume':False}


ENTRY_PATHS=('/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management')
def entry_context(tabs,tab_id,window_id,*,login=False):
 from urllib.parse import urlsplit,parse_qs
 import dom_evidence as dom
 matches=[(w,t)for w in tabs for t in w.get('tabs',[])if t.get('tabId')==tab_id];w,t=dom.unique(matches,'company-entry-tab-unique');u=urlsplit(t.get('url',''));need(t.get('allowed')is True and w.get('windowId')==window_id and t.get('windowId')==window_id and u.scheme=='https'and u.netloc=='life.douyin.com'and not u.fragment,'company-entry-window-origin')
 if login:need(u.path=='/p/login'and not u.query,'company-login-exact-route');return dict(t,groupid=None,login_company_picker=True)
 if u.path=='/p/governance/violation_list':
  # Entry before switching only. Target context observations retain their own
  # stricter post-switch home/review whitelist.
  q=parse_qs(u.query,keep_blank_values=True);basic={'groupid','StartTime','EndTime','enter_from'};filters={'ViolationReasons','IndicatorTags'};merchant={'life_biz_view_id','life_account_biz_ids'}
  need(basic<=set(q)<=basic|filters|merchant and set(q)&merchant in(set(),merchant)and all(len(v)==1 for v in q.values()),'company-entry-governance-query')
  need(q['groupid'][0].isdigit()and q['enter_from']==['home_violation_center']and q.get('ViolationReasons',['[]'])==['[]']and q.get('IndicatorTags',[''])==['']and all(q[k][0].isdigit()for k in('StartTime','EndTime'))and int(q['StartTime'][0])<=int(q['EndTime'][0])and(not set(q)&merchant or(q['life_biz_view_id']==['22']and q['life_account_biz_ids']==[''])),'company-entry-governance-query')
  return dict(t,groupid=q['groupid'][0])
 need(u.path in ENTRY_PATHS,'company-entry-reviewed-route');return dom.context(tabs,tab_id)
def picker_parts(tree,*,login=False):
 import dom_evidence as dom
 need(tree.get('truncated')is False,'company-picker-complete-tree');ns=list(dom.nodes(tree))
 if login:
  root=dom.unique([n for n in ns if n.get('tag')=='div'and 'src-pages-Login-components-LoginFlowCard-index-module__container--'in n.get('attributes',{}).get('class','')],'company-login-picker-unique');children=list(dom.nodes({'root':root,'truncated':False}));dom.unique([n for n in children if n.get('tag')=='p'and n.get('name')=='选择你的公司'and 'LoginFlowCard-index-module__title--'in n.get('attributes',{}).get('class','')],'company-login-title-unique')
 else:
  prefix='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__'
  def reviewed_modal(n):
   classes=n.get('attributes',{}).get('class','');tokens=set(classes.split())
   return prefix in classes and (n.get('role')=='dialog'or(n.get('tag')=='div'and n.get('role')=='generic'and prefix+'login-modal--'in classes and {'life-core-modal','life-core-modal-show','life-core-modal-content-container'}<=tokens))
  root=dom.unique([n for n in ns if reviewed_modal(n)],'company-picker-unique-reviewed-modal');children=list(dom.nodes({'root':root,'truncated':False}))
  if root.get('role')=='generic':
   container=dom.unique([n for n in children if n.get('tag')=='div'and prefix+'container--'in n.get('attributes',{}).get('class','')],'company-picker-container-unique')
   scope=list(dom.nodes({'root':container,'truncated':False}));dom.unique([n for n in scope if n.get('tag')=='p'and n.get('name')=='切换公司'and prefix+'title--'in n.get('attributes',{}).get('class','')],'company-picker-title-unique')
   content=dom.unique([n for n in scope if n.get('tag')=='div'and prefix+'content--'in n.get('attributes',{}).get('class','')],'company-picker-content-unique')
   fields=[n for n in dom.nodes({'root':content,'truncated':False})if n.get('tag')=='input'and n.get('role')=='textbox'and n.get('placeholder')=='搜索商户']
   dom.unique(fields,'company-picker-content-search-unique')
 need(not any(n.get('tag')in('iframe','form')for n in children),'company-picker-foreign-form');field=dom.unique([n for n in children if n.get('tag')=='input'and n.get('role')=='textbox'and n.get('placeholder')=='搜索商户'],'company-picker-search-unique');need(field.get('selector')and not field.get('disabled'),'company-picker-search-ready')
 if login:dom.unique([n for n in children if n.get('attributes',{}).get('class')=='card__list_582b9'],'company-login-list-unique')
 return root,children,field
def picker_source(snapshot,op):
 import dom_evidence as dom
 from readonly_tick_snapshot import decode
 login='source_entry'in op;value=decode(snapshot,op['tab_id'],op['window_id']);require_no_visible_system_error(value['tree']);before=entry_context(value['before'],op['tab_id'],op['window_id'],login=login);after=entry_context(value['after'],op['tab_id'],op['window_id'],login=login);need(before==after and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-picker-reviewed-source')
 if login:
  x=op['source_entry'];need(type(x)is dict and set(x)=={'kind','authority'}and ((x=={'kind':'original-job-login-company-picker-v2','authority':op['original_job']}and op['purpose']=='configured-business-company-context')or(x['kind']=='verified-config-login-company-picker-v2'and op['purpose']=='context-discovery')),'company-login-original-authority')
 else:need(before['groupid']==op['source_groupid'],'company-picker-source-gid');dom.identity(value['tree'],op['source_identity'])
 need(value['tree'].get('url')==before['url'].split('?')[0],'company-picker-tree-route');return value,picker_parts(value['tree'],login=login)
def picker_confirm_nodes(children):
 """The picker footer's enabled 确认, by reviewed shape only.

 B68: extracted so the live discovery can ask "is the footer rendered yet?"
 without restating the locator rule. The uniqueness demand stays where it
 belongs - in input_before, which also serves every replay of a saved command.
 """
 return [n for n in children if n.get('tag')=='button'and n.get('role')=='button'and n.get('name')=='确认'and not n.get('disabled')]
def input_before(snapshot,op,row,action):
 """A login picker proves no identity. Only original-job authority permits it;
 target business identity is established by subsequent independent fresh reads.
 """
 import dom_evidence as dom
 value,(root,children,field)=picker_source(snapshot,op);need(field.get('attributes',{}).get('value')==row['company'],'company-picker-search-exact');target=dom.unique([n for n in children if not n.get('children')and n.get('name')==row['company']],'company-picker-target-unique');need(target.get('tag')=='div'and target.get('role')=='generic'and target.get('attributes',{}).get('class')=='name_4a8f8'and not target.get('disabled'),'company-picker-target-shape')
 if 'source_entry'in op:
  listing=dom.unique([n for n in children if n.get('attributes',{}).get('class')=='card__list_582b9'],'company-login-list-unique');need(any(n is target for n in dom.nodes({'root':listing,'truncated':False})),'company-login-target-list');parents=[n for n in children if target in n.get('children',[])];main=dom.unique(parents,'company-login-target-parent');need(main.get('attributes',{}).get('class')=='main_4a8f8','company-login-target-main');dom.unique([n for n in children if main in n.get('children',[])and n.get('attributes',{}).get('class')=='box-account-item_4a8f8'],'company-login-target-row')
 if action=='company':return target
 need('source_entry'not in op,'company-login-no-invented-confirm');return dom.unique(picker_confirm_nodes(children),'company-picker-confirm-unique')


def identity_hover_before(snapshot,op,row):
 """Observed HomeV3 header only, absent full profile, no guessed control."""
 from readonly_tick_snapshot import decode
 import dom_evidence as dom
 from urllib.parse import urlsplit
 value=decode(snapshot,op['tab_id'],op['window_id']);before=entry_context(value['before'],op['tab_id'],op['window_id']);after=entry_context(value['after'],op['tab_id'],op['window_id']);need(before==after and urlsplit(before['url']).path=='/p/home'and value['tree'].get('url')=='https://life.douyin.com/p/home'and value['tree'].get('truncated')is False and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-identity-hover-scope');tree=value['tree'];require_no_visible_system_error(tree);label=company_label(tree);need(label.get('name')==row['company']and 'src-pages-HomeV3-'in label.get('attributes',{}).get('class',''),'company-identity-hover-target-label');ns=list(dom.nodes(tree));need(not any('UserCard-index-module__outer--'in n.get('attributes',{}).get('class','')for n in ns),'company-identity-hover-profile-already-present')
 try:dom.identity(tree)
 except ValueError as error:need(str(error)in('identity-provider-unverified','identity-account-unverified','identity-manager-unverified'),'company-identity-hover-not-missing')
 else:raise ValueError('company-identity-hover-already-complete')
 prefix='src-components-HeaderV3-components-Profile-index-module__title--';target=dom.unique([n for n in dom.leaves(tree)if n.get('name')==row['provider']and n.get('tag')=='div'and n.get('role')=='generic'and any(x.startswith(prefix)for x in n.get('attributes',{}).get('class','').split())],'company-identity-hover-trigger-unique');need(target.get('selector','').startswith('#main-app > section > section > header > ')and not target.get('disabled'),'company-identity-hover-header-control');return target,before['groupid']

def company_labels(tree):
 """Reviewed leaf class families, never a company-name allowlist."""
 import dom_evidence as dom
 result=[]
 for n in dom.leaves(tree):
  classes=n.get('attributes',{}).get('class','')
  # HomeV3's companyName leaf is the numeric account ID; its name leaf
  # carries the company. The older AccountInfo profile uses companyName.
  if 'AccountInfo-module__name--'in classes or ('AccountInfo-module__companyName--'in classes and 'src-pages-HomeV3-'not in classes):result.append(n)
 return result
def company_label(tree):
 import dom_evidence as dom
 return dom.unique(company_labels(tree),'company-context-company-label-unique')

def job_configuration(job):
 """Pinned config consumer. It does not grant input or register a company."""
 need(type(job)is dict and 'company_configuration_policy'in job and 'company_configuration_entry'in job,'company-job-configuration-pair')
 original={'path':job.get('work_order_path'),'sha256':''};path=regular(original['path']);b=path.read_bytes();original['sha256']=hashlib.sha256(b).hexdigest();need(json.loads(b)==job,'company-job-original-bytes')
 policy=doc(job['company_configuration_policy']);need(type(policy)is dict and set(policy)=={'kind','configuration','configuration_code','active_ids','retired_ids'}and policy['kind']=='active-company-scope-policy-v2','company-job-policy-schema');source=policy['configuration_code'];need(source['path']==str(Path(__file__).absolute())and configuration_code_bytes(source),'company-job-code-origin');config=get_config(policy['configuration']);entry=config.business(job['company_configuration_entry']);need(entry['id']in policy['active_ids']and len(policy['active_ids'])==len(set(policy['active_ids']))and not set(policy['active_ids'])&set(policy['retired_ids']),'company-job-policy-active');need(entry['company']==job.get('company')and entry['verified']['groupid']==str(job.get('groupid'))and entry['verified']['identity']==job.get('identity_baseline')and job.get('known_company_identities',{}).get(str(job['groupid']))==job['identity_baseline']and entry['provider']==job.get('provider_baseline'),'company-job-target-identity')
 return config,entry,original

def business_command(job,command,scope_ref,operation_ref,path,key,*,now=None):
 """Return one exact input plan. Writes only its immutable operation artifact.
 No transport, new authorization, expiration renewal or unknown reconciliation.
 The caller must persist its input intent before dispatch and own task/lease.
 """
 from readonly_tick_snapshot import decode
 import dom_evidence as dom
 now=now or datetime.now(timezone.utc);config,row,original=job_configuration(job);raw_scope=doc(scope_ref);scope=decode(raw_scope,command['tabId'],raw_scope.get('scope',{}).get('windowId'));login=scope['tree'].get('url')=='https://life.douyin.com/p/login';before=entry_context(scope['before'],command['tabId'],scope['scope']['windowId'],login=login);after=entry_context(scope['after'],command['tabId'],scope['scope']['windowId'],login=login);need(before==after,'company-business-fresh-window');identity=row['verified']['identity']if login else dom.identity(scope['tree']);source_gid=row['verified']['groupid']if login else before['groupid'];expected_source=configured_source_identity(job,source_gid,config=config)if job.get('company_configuration_registry')=='configured-source-index-v2'else job.get('known_company_identities',{}).get(source_gid);need(identity==expected_source and identity['provider']==row['provider']and scope['ping'].get('version')in REVIEWED_DOM_VERSIONS and scope['ping'].get('safety')=='DOM-only','company-business-fresh-identity');picker_parts(scope['tree'],login=login)
 need(command.get('op')in('filter','click')and command.get('kind')in('filter','company','company-confirm'),'company-business-command')
 if operation_ref is None:
  dates=job.get('date_range',{});need('start'in dates and 'end_exclusive'in dates,'company-business-date-range-required');value={'kind':'configured-company-operation-v2','config':config.reference,'entry_id':row['id'],'key':key,'tab_id':command['tabId'],'window_id':before['windowId'],'source_groupid':source_gid,'provider':row['provider'],'source_identity':identity,'date_range':{k:dates[k]for k in('start','end_exclusive')},'issued_at':now.isoformat(),'expires_at':(now+timedelta(seconds=300)).isoformat(),'purpose':'configured-business-company-context','original_job':original};
  if login:value['source_entry']={'kind':'original-job-login-company-picker-v2','authority':original}
  dest=Path(path);need(dest.is_absolute()and dest.parent==dest.parent.resolve()and not any(x.is_symlink()for x in(dest,*dest.parents)),'company-business-artifact-path');dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():
   operation_ref={'path':str(dest),'sha256':hashlib.sha256(regular(dest).read_bytes()).hexdigest()};old=doc(operation_ref);need({k:v for k,v in old.items()if k not in('issued_at','expires_at')}=={k:v for k,v in value.items()if k not in('issued_at','expires_at')},'company-business-operation-conflict')
  else:
   data=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
   with dest.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
   fd=os.open(dest.parent,os.O_RDONLY)
   try:os.fsync(fd)
   finally:os.close(fd)
   operation_ref={'path':str(dest),'sha256':hashlib.sha256(data).hexdigest()}
 op,checked=operation(config,operation_ref,now=now);need(op['key']==key and op['original_job']==original and op['entry_id']==row['id']and op['tab_id']==command['tabId']and op['window_id']==before['windowId']and op['source_groupid']==source_gid and op['source_identity']==identity,'company-business-operation-source-drift')
 # Every input uses its own freshly obtained tree; selectors never span input.
 if command['op']=='filter':
  need(command.get('value')==row['company'],'company-business-exact-search');_,(_,_,target)=picker_source(scope,op)
 else:target=input_before(scope,op,checked,command['kind'])
 need(command.get('locator')=={'by':'selector','value':target.get('selector')}and target.get('selector'),'company-business-fresh-locator');return {**copy.deepcopy(command),'companyRequest':copy.deepcopy(operation_ref)},operation_ref


def acquisition_context(proof):
 """Existing real acquisition consumer; output is identity context, not new export."""
 need(type(proof)is dict and set(proof)=={'kind','receipt'},'company-acquisition-context-schema')
 import importlib.util
 path=regular(ROOT/'skills/douyin-laike-operator/scripts/prepare_company_navigation.py');before=path.read_bytes();spec=importlib.util.spec_from_file_location('_configured_acquisition_context_validator',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);need(regular(path).read_bytes()==before,'company-acquisition-validator-drift');value,_,journal=module.receipt(proof['receipt']);need(regular(path).read_bytes()==before,'company-acquisition-validator-drift');raw(proof['receipt'])
 return {'company':value['company'],'groupid':str(value['groupid']),'identity':value['identity'],'context_only':True,'acquisition_receipt':False,'business_resume':False,'identity_origin':'verified-original-acquisition','original_receipt':proof['receipt'],'original_journal':journal}

def _observed_scope(reference,binding,*,source=False):
 from readonly_tick_snapshot import decode
 import dom_evidence as dom
 from urllib.parse import urlsplit,parse_qs
 reply=doc(reference);value=reply.get('result')if reply.get('ok')is True else reply
 value=decode(value,binding['tab_id'],binding['window_id']);a=dom.context(value['before'],binding['tab_id']);b=dom.context(value['after'],binding['tab_id']);need(a==b and a['windowId']==binding['window_id']and a['groupid'].isdigit(),'company-import-stable-scope');url=urlsplit(a['url']);need(url.path in('/p/home','/p/home/home_overview','/p/home/homeV2','/p/life_comment/management')and not url.fragment and parse_qs(url.query,keep_blank_values=True).get('groupid')==[a['groupid']],'company-import-route');tree=value['tree'];need(tree.get('truncated')is False and value['ping'].get('version')in REVIEWED_DOM_VERSIONS and value['ping'].get('safety')=='DOM-only','company-import-reviewed-tree');identity=dom.identity(tree)
 if source:need(a['groupid']==binding['source_gid']and identity==binding['source_identity'],'company-import-source-identity')
 else:need(company_label(tree).get('name')==binding['target_company']and identity['provider']==binding['source_identity']['provider'],'company-import-target-identity')
 return a,identity,value

def observed_context(proof):
 """Data-only import of a completed observed context lineage. No old code exec.
 It cannot dispatch, create/extend authority, create acquisition or activate config.
 """
 need(type(proof)is dict and set(proof)=={'kind','handoff'},'company-observed-import-schema');handoff=doc(proof['handoff']);need(handoff.get('kind')=='observed-company-context-handoff-v1'and handoff.get('state')=='complete'and handoff.get('business_resume')is False and handoff.get('acquisition_receipt')is False,'company-observed-import-handoff');opref=handoff['operation'];op=doc(opref);need(set(op)=={'kind','binding','binding_sha256','state','calls','observations','checkpoint','select_rejection'}and op['kind']=='exact-company-discovery-operation-v1'and op['state']=='complete','company-observed-import-operation');binding=op['binding'];need(set(binding)=={'business_resume','range','source_gid','source_identity','source_snapshot','tab_id','target_company','window_id'}and binding['business_resume']is False and exact_name(binding['target_company'])and full_identity(binding['source_identity'])and all(type(binding[k])is int and binding[k]>0 for k in('tab_id','window_id')),'company-observed-import-binding');digest=lambda v:hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();need(op['binding_sha256']==digest(binding),'company-observed-import-binding-hash');_observed_scope(binding['source_snapshot'],binding,source=True)
 calls=op['calls'];stages=['open-picker','search','select','select-opportunity','confirm','identity-hover'];need(type(calls)is list and [c.get('stage')for c in calls]==stages and len({c.get('key')for c in calls})==len(calls),'company-observed-import-call-prefix');folder=regular(opref['path']).parent
 for call in calls:
  intent_path=folder/('input-'+call['stage']+'-intent.json');intent=json.loads(regular(intent_path).read_bytes());base_intent={'binding_sha256':op['binding_sha256'],'command':call['command'],'key':call['key'],'stage':call['stage']}
  if call['stage']=='identity-hover':
   need(set(intent)==set(base_intent)|{'authorization','fresh_scope'}and {k:intent[k]for k in base_intent}==base_intent,'company-observed-import-hover-intent');hover_auth=doc(intent['authorization']);need(hover_auth.get('kind')=='root-authorized-original-home-identity-hover-v1'and hover_auth.get('approved')is True and hover_auth.get('business_resume')is False and hover_auth.get('max_identity_hover')==1 and hover_auth.get('old_key_replay')is False and hover_auth.get('operation_before',{}).get('path')==opref['path'],'company-observed-import-hover-authority');raw(intent['fresh_scope'])
  else:need(intent==base_intent,'company-observed-import-intent-prefix')
  command=call['command'];need(command.get('tabId')==binding['tab_id']and command.get('locator',{}).get('by')=='selector'and command['locator'].get('value'),'company-observed-import-command')
  if call['stage']=='select':continue
  need(call.get('state')=='confirmed'and call.get('reply',{}).get('ok')is True,'company-observed-import-unconfirmed');result=call['reply']['result'];node=result.get({'click':'clicked','filter':'filtered','hover':'hovered'}.get(command.get('op')),{})
  need(node.get('selector')==command['locator']['value'],'company-observed-import-effect-selector')
  if call['stage']=='search':need(command.get('op')=='filter'and command.get('value')==binding['target_company']and node.get('attributes',{}).get('value')==binding['target_company'],'company-observed-import-exact-search')
  elif call['stage']=='select-opportunity':need(command.get('op')=='click'and command.get('kind')=='company'and node.get('name')==binding['target_company'],'company-observed-import-exact-selection')
  elif call['stage']=='confirm':need(command.get('op')=='click'and command.get('kind')=='company-confirm'and node.get('name')=='确认','company-observed-import-confirm')
  elif call['stage']=='open-picker':need(command.get('op')=='click'and node.get('name')=='切换','company-observed-import-picker')
  else:need(command.get('op')=='hover'and node.get('name')==binding['source_identity']['provider'],'company-observed-import-provider-hover')
 # Preserve the rejected original key and its UNKNOWN archive; only the precise
 # independently authorized opportunity can account for the later select input.
 rejected=calls[2];pr=doc(op['select_rejection']);need(pr.get('kind')=='explicit-preaction-select-denial-and-fresh-opportunity-v1'and pr.get('old_key_replay')is False and pr.get('new_stage')=='select-opportunity'and pr.get('new_key')==calls[3]['key']and rejected.get('state')=='rejected-before-action','company-observed-import-opportunity');original=doc(pr['original_operation_archive']);need(pr['original_operation']['path']==opref['path']and pr['original_operation_archive']['sha256']==pr['original_operation']['sha256']and original['binding']==binding and original['calls'][-1]==pr['original_call']and original['calls'][-1]['state']=='unknown','company-observed-import-unknown-archive');need({k:v for k,v in rejected.items()if k!='state'}=={k:v for k,v in pr['original_call'].items()if k!='state'}and rejected['reply']=={'error':'not in offline reviewed click allowlist','ok':False,'result':None},'company-observed-import-explicit-denial');need(doc(pr['original_intent'])=={'binding_sha256':op['binding_sha256'],'command':rejected['command'],'key':rejected['key'],'stage':'select'},'company-observed-import-denied-intent');authorization=doc(pr['authorization']);continuation=doc(pr['time_continuation']);release=doc(pr['source_release']);need(authorization.get('kind')=='root-authorized-rejected-select-single-opportunity-v1'and authorization.get('approved')is True and authorization.get('new_opportunities')==1 and authorization.get('old_key_replay')is False and authorization.get('denied_key')==rejected['key']and authorization.get('operation_before')==pr['original_operation'],'company-observed-import-original-opportunity-authority');need(continuation.get('approved')is True and continuation.get('old_key_replay')is False and continuation.get('original_operation')==pr['original_operation']and continuation.get('published_release')==pr['source_release']and continuation.get('target_company')==binding['target_company']and release.get('published')is True and release.get('test_projection_only')is False,'company-observed-import-original-source-continuation');_observed_scope(pr['fresh_scope'],binding,source=True)
 checkpoint=op['checkpoint'];need(checkpoint==handoff['checkpoint']and checkpoint.get('kind')=='observed-exact-company-identity-checkpoint-v1'and checkpoint.get('company')==binding['target_company']and checkpoint.get('business_resume')is False and checkpoint.get('acquisition_receipt')is False,'company-observed-import-checkpoint');refs=checkpoint['stable_identity_evidence'];need(type(refs)is list and len(refs)==2 and refs[0]['path']!=refs[1]['path']and op['observations'][-2:]==refs and checkpoint['evidence']==refs[-1],'company-observed-import-two-observations');samples=[_observed_scope(r,binding)for r in refs];need(samples[0][:2]==samples[1][:2]and samples[0][0]['groupid']==checkpoint['groupid']and samples[0][1]==checkpoint['identity']and samples[0][0]['url']==checkpoint['actual_url'],'company-observed-import-stable-identity')
 result=doc(handoff['result']);need(result.get('state')=='complete'and result.get('reason')is None and result.get('business_resume')is False and result.get('checkpoint')==checkpoint and result.get('operation_after')==opref and result.get('observations',[])[-2:]==refs,'company-observed-import-natural-result');terminal=handoff['natural_terminal'];need(terminal.get('observed_exit_code')==0 and terminal.get('program_elapsed_seconds')==result.get('elapsed_seconds')and result['elapsed_seconds']>0,'company-observed-import-recorded-exit');intent=doc(result['intent']);need(intent.get('confirmed_prefix')==calls[:-1],'company-observed-import-hover-prefix');raw(proof['handoff'])
 return {'company':checkpoint['company'],'groupid':checkpoint['groupid'],'identity':checkpoint['identity'],'context_only':True,'acquisition_receipt':False,'business_resume':False,'identity_origin':'original-observed-context-lineage','recorded_natural_exit':True}

def registration_proposal(profiles):
 """Pure proposed data only. Not an active config, pointer, grant or receipt."""
 need(type(profiles)is list and bool(profiles),'company-registration-profile-list');entries=[]
 for profile in profiles:
  need(type(profile)is dict and set(profile)=={'id','company','production_group','brand','context_proof'},'company-registration-profile-schema');observed=verify_context_proof(profile['context_proof']);need(observed.get('context_only')is True and observed.get('acquisition_receipt')is False and observed.get('business_resume')is False and observed.get('company')==profile['company'],'company-registration-observed-exact-name');entries.append({'id':profile['id'],'company':observed['company'],'provider':observed['identity']['provider'],'status':'pending-discovery','capabilities':[],'production_group':profile['production_group'],'brand':profile['brand'],'verified':{'groupid':observed['groupid'],'identity':observed['identity'],'context_proof':profile['context_proof']}})
 decode_config({'kind':'configured-company-scope-v2','entries':entries})
 return {'kind':'company-registration-proposal-v2','execution_authorized':False,'active_policy_created':False,'approved_pointer_created':False,'entries':entries}


def _configuration_timing():
 import importlib.util,sys
 path=regular(Path(__file__).absolute().with_name('execution_timing.py'));before=path.read_bytes();expected={'path':str(path),'sha256':hashlib.sha256(before).hexdigest()};prior=sys.modules.get('execution_timing')
 if prior is not None:
  need(getattr(prior,'__file__',None)==str(path)and getattr(prior,'_CONFIGURATION_MODULE_SOURCE',None)==expected,'company-code-loaded-resolver-drift');return prior
 spec=importlib.util.spec_from_file_location('execution_timing',path);module=importlib.util.module_from_spec(spec)
 # Execute only bytes read from the independently checked canonical source.
 exec(compile(before,str(path),'exec'),module.__dict__);need(regular(path).read_bytes()==before and module._CONFIGURATION_MODULE_SOURCE==expected,'company-code-resolver-drift');sys.modules['execution_timing']=module;return module

def configuration_code_bytes(source):
 timing=_configuration_timing()
 need(source['path']==str(Path(__file__).absolute()),'company-code-source-origin')
 admitted=timing.configuration_source_material(source)
 need(admitted['current']=={'path':str(Path(__file__).absolute()),'sha256':hashlib.sha256(regular(__file__).read_bytes()).hexdigest()},'company-code-current-origin')
 return timing.checked_bytes(admitted['material'])

PICKER_RECOVERY_KIND='verified-company-picker-structure-preinput-recovery-v1'
def picker_preinput_facts(job_ref,original_ref,scope_ref):
 import dom_evidence as dom
 from readonly_tick_snapshot import decode
 job=doc(job_ref);config,row,checked=job_configuration(job);need(checked==job_ref,'company-picker-recovery-job-ref');s=_picker_original_doc(original_ref)
 need(original_ref['path']==job['workflow_path']and s.get('state')=='running'and s.get('phase')=='searchCompany'and s.get('revision')==2 and s.get('company_configuration_job')==job_ref and s.get('last_error',{}).get('code')==s.get('last_error',{}).get('message')=='company-picker-unique-reviewed-modal'and len(s.get('calls',[]))==1 and not any(s.get(k)for k in('exportPending','downloadPending','export_pending','download_pending','attempts','submittedAt','result','company_configuration_operation','company_search_loading_recovery')),'company-picker-recovery-known-preinput')
 need(s['work_order_id']==job['work_order_id']and s['company']==job['company']and s['groupid']==str(job['groupid'])and s['date_range']=={'start':job['date_range']['start'],'end':job['date_range']['end']}and s['fingerprint']and job.get('explicit_tab_id_required')is True and type(s['tab_id'])is int and s['tab_id']>0,'company-picker-recovery-job-binding')
 call=s['calls'][0];cmd=call.get('command',{});clicked=call.get('result',{}).get('clicked',{})
 need(call.get('key')=='1:context'and call.get('phase')=='context'and call.get('state')=='confirmed'and cmd.get('op')=='click'and cmd.get('kind')=='navigation'and cmd.get('tabId')==s['tab_id']and clicked.get('name')=='切换'and clicked.get('selector')==cmd.get('locator',{}).get('value'),'company-picker-recovery-confirmed-prefix')
 path=regular(scope_ref['path']);need(path.parent==Path(original_ref['path']).parent/'bridge-evidence'and path.name.startswith('0002-searchCompany-scope-')and path.suffix=='.json','company-picker-recovery-original-scope-path');scope=doc(scope_ref);value=decode(scope,s['tab_id'],scope.get('scope',{}).get('windowId'));need(value['tree']==doc(s['last_tree']),'company-picker-recovery-original-tree');op={'tab_id':s['tab_id'],'window_id':value['scope']['windowId'],'source_groupid':s['initial_groupid'],'source_identity':s['entry_identity']};picker_source(scope,op)
 need(configured_source_identity(job,s['initial_groupid'],config=config)==s['entry_identity']and s['provider_baseline']==s['entry_identity']['provider']and dom.company_switch(value['tree'])['selector']==clicked['selector'],'company-picker-recovery-source-identity')
 return {'job':job_ref,'original':original_ref,'scope':scope_ref,'tree':s['last_tree'],'original_calls':s['calls'],'original_error':s['last_error']}

def picker_preinput_shared_transform(original,proof_ref):
 need('company_search_loading_recovery'not in original,'company-picker-recovery-existing-marker');after=copy.deepcopy(original);after.pop('last_error');after['company_search_loading_recovery']={'kind':PICKER_RECOVERY_KIND,'proof':proof_ref};return after

def verify_picker_preinput_recovery(current,job_ref):
 marker=current.get('company_search_loading_recovery');need(type(marker)is dict and set(marker)=={'kind','proof'}and marker['kind']==PICKER_RECOVERY_KIND,'company-picker-recovery-marker');proof=doc(marker['proof']);need(type(proof)is dict and set(proof)=={'kind','facts','original_archive','approved_code'}and proof['kind']==PICKER_RECOVERY_KIND,'company-picker-recovery-proof-schema');facts=proof['facts'];base=Path(facts['original']['path']).parent/'company-picker-preinput-recovery'/facts['original']['sha256'];need(marker['proof']['path']==str(base/'proof.json')and proof['original_archive']=={'path':str(base/'original-workflow.json'),'sha256':facts['original']['sha256']}and facts['job']==job_ref,'company-picker-recovery-proof-binding')
 original=doc(proof['original_archive']);archive_reader=doc
 # Recompute public eligibility from exact archived original, without treating
 # its archive path as the original canonical workflow path.
 def old_read(reference):return original if reference==facts['original']else archive_reader(reference)
 token=_PICKER_ORIGINAL_READER.set(old_read)
 try:need(_picker_facts_reader(facts['job'],facts['original'],facts['scope'])==facts,'company-picker-recovery-recomputed-facts')
 finally:_PICKER_ORIGINAL_READER.reset(token)
 need(current['calls'][:len(original['calls'])]==original['calls']and all(current.get(k)==original.get(k)for k in('company','groupid','date_range','fingerprint','work_order_id','tab_id','initial_groupid','entry_identity','provider_baseline','entry_groupid','identity_contract','company_configuration_job')),'company-picker-recovery-preserved-prefix')
 timing=_configuration_timing()
 need(proof['approved_code']['path']==str(Path(__file__).absolute()),'company-picker-recovery-approved-code-path');timing.configuration_source_material(proof['approved_code']);return facts

# Reader authority is scoped only to the one archived original journal. All
# job/config/raw/source verification still uses normal exact ref consumers.
_PICKER_ORIGINAL_READER=ContextVar('picker_preinput_original_reader',default=None)
_picker_facts_reader=picker_preinput_facts
# Keep the pure facts function's ordinary production reader intact. Only this
# private reader access is replaceable via the explicitly scoped archive above.
def _picker_original_doc(reference):
 reader=_PICKER_ORIGINAL_READER.get();return reader(reference)if reader else doc(reference)

def recover_picker_preinput(job_ref,original_ref,scope_ref,*,guard):
 import fcntl
 job=doc(job_ref);path=regular(job['workflow_path']);need(original_ref['path']==str(path),'company-picker-recovery-canonical-workflow');base=path.parent/'company-picker-preinput-recovery'/original_ref['sha256'];proof_path=base/'proof.json'
 def immutable(path,data):
  if path.exists():need(not path.is_symlink()and path.read_bytes()==data,'company-picker-recovery-immutable-conflict')
  else:
   with path.open('xb')as file:file.write(data);file.flush();os.fsync(file.fileno())
  return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest()}
 lock_path=regular(path.with_name('.bridge-execution.lock'))
 with lock_path.open('r+b')as file:
  fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(file.fileno());current=regular(lock_path).stat();need((held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'company-picker-recovery-lock-drift');guard('preflight')
  if proof_path.exists():
   pr={'path':str(proof_path),'sha256':hashlib.sha256(regular(proof_path).read_bytes()).hexdigest()};proof=doc(pr);need(proof['facts']['original']==original_ref and proof['facts']['job']==job_ref and proof['facts']['scope']==scope_ref,'company-picker-recovery-same-proof');before=doc(proof['original_archive'])
  else:
   facts=picker_preinput_facts(job_ref,original_ref,scope_ref);before=doc(original_ref);base.mkdir(parents=True,exist_ok=True);ar=immutable(base/'original-workflow.json',raw(original_ref));code={'path':str(Path(__file__).absolute()),'sha256':hashlib.sha256(regular(__file__).read_bytes()).hexdigest()};pr=immutable(proof_path,(json.dumps({'kind':PICKER_RECOVERY_KIND,'facts':facts,'original_archive':ar,'approved_code':code},ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
  after=picker_preinput_shared_transform(before,pr);verify_picker_preinput_recovery(after,job_ref);current=json.loads(path.read_bytes());need(current in(before,after),'company-picker-recovery-third-state')
  if current==after:guard('existing-readback');return pr
  guard('before-CAS');need(raw(original_ref),'company-picker-recovery-before-drift');from role_cli import write_json;write_json(path,after);guard('readback');verify_picker_preinput_recovery(json.loads(path.read_bytes()),job_ref);return pr

_COMPANY_BUSINESS_COMMAND=business_command
def business_command(*args,**kwargs):
 with _configuration_timing().company_policy_command():return _COMPANY_BUSINESS_COMMAND(*args,**kwargs)
_COMPANY_ADMIT_COMMAND=admit_command
def admit_command(*args,**kwargs):
 with _configuration_timing().company_policy_command():return _COMPANY_ADMIT_COMMAND(*args,**kwargs)


@contextlib.contextmanager
def search_progression_command():
 existing=_SEARCH_COMMAND.get()
 if existing is not None:yield existing['counts'];return
 timing=_configuration_timing()
 with timing.company_policy_command():
  state={'timing':timing,'facts':{},'counts':{'terminal_computes':0,'terminal_hits':0,'live_checks':0}};token=_SEARCH_COMMAND.set(state)
  try:yield state['counts']
  finally:_SEARCH_COMMAND.reset(token)

def verify_search_terminal(proof_ref,job_ref):
 """One pure historical computation per explicitly bounded command. All files
 touched by strict company verification are held/pinned by the existing timing
 command (full hashes at boundaries, fd/path frontier on reuse). No global cache.
 """
 active=_SEARCH_COMMAND.get()
 if active is None:
  with search_progression_command():return verify_search_terminal(proof_ref,job_ref)
 key=json.dumps([proof_ref,job_ref],sort_keys=True,separators=(',',':'))
 if key in active['facts']:
  active['timing']._policy_check(active['timing']._POLICY_COMMAND.get());active['counts']['terminal_hits']+=1;return copy.deepcopy(active['facts'][key])
 token=_SEARCH_HISTORY_ACTIVE.set(True)
 try:
  regular(Path(__file__).absolute());result=doc(proof_ref);need(set(result)=={'kind','state','intent','reply','after_scope','original_unknown_preserved'}and result['kind']=='explicit-original-search-action-result-v1'and result['state']=='confirmed'and result['original_unknown_preserved']is True,'search-terminal-schema');intent=doc(result['intent']);operation_ref=intent['operation'];op=doc(operation_ref);folder=regular(operation_ref['path']).parent
  need(proof_ref['path']==str(folder/'action-result.json')and result['intent']['path']==str(folder/'action-intent.json'),'search-terminal-canonical');at=datetime.fromisoformat(intent['at']);command=intent['command'];facts=_explicit_search_facts(operation_ref,op,command,now=at,_historical=True);need(result['intent']==facts['intent'],'search-terminal-same-intent');a=doc(facts['authority']);need(a['job']==job_ref,'search-terminal-original-job');archive=intent['original_archive'];before=doc(archive);unknown=intent['original_unknown'];need(before['calls'][1]==unknown,'search-terminal-original-prefix')
  claim_path=folder/'server-search-intent.json';claim_ref={'path':str(claim_path),'sha256':hashlib.sha256(regular(claim_path).read_bytes()).hexdigest()};claim=doc(claim_ref);need(claim=={'kind':'explicit-single-search-server-intent-v1','operation':operation_ref,'caller_intent':result['intent'],'authority':facts['authority'],'command':command,'max_inputs':1}and type(claim['max_inputs'])is int,'search-terminal-server-claim')
  reply=result['reply'];need(type(reply)is dict and set(reply)=={'ok','result','error'}and reply['ok']is True and reply['error']is None and type(reply['result'])is dict and set(reply['result'])=={'filtered'},'search-terminal-real-reply-schema');job=doc(job_ref);node=reply['result']['filtered'];need(node.get('selector')==command['locator']['value']and node.get('attributes',{}).get('value')==job['company'],'search-terminal-reply-effect')
  after=result['after_scope'];need(type(after)is dict and set(after)=={'raw','observed_at'},'search-terminal-after-schema');after_at=datetime.fromisoformat(after['observed_at']);need(at<=after_at<=facts['expires'],'search-terminal-after-time');base={k:v for k,v in command.items()if k!='companyRequest'};planned,checked=business_command(job,base,after['raw'],operation_ref,Path(operation_ref['path']),op['key'],now=after_at);need(planned==command and checked==operation_ref,'search-terminal-after-company');_,(_,_,field)=picker_source(doc(after['raw']),op);need(field.get('selector')==node['selector']and field.get('attributes',{}).get('value')==job['company'],'search-terminal-after-value')
  value={'proof':copy.deepcopy(proof_ref),'job':copy.deepcopy(job_ref),'authority':a,'authority_ref':facts['authority'],'original':before,'archive':archive,'unknown':unknown,'operation':op,'operation_ref':operation_ref,'input_at':intent['at'],'server_claim':claim_ref};active['facts'][key]=value;active['counts']['terminal_computes']+=1;return copy.deepcopy(value)
 finally:_SEARCH_HISTORY_ACTIVE.reset(token)

def search_recovery_transform(before,proof_ref,job_ref):
 facts=verify_search_terminal(proof_ref,job_ref);need(before==facts['original'],'search-recovery-exact-before');after=copy.deepcopy(before);after['company_search_explicit_recovery']={'kind':'authorized-search-superseded-for-progression-v1','proof':copy.deepcopy(proof_ref),'original_workflow':facts['authority']['original_workflow'],'original_archive':facts['archive'],'original_call_key':'2:searchCompany'};error=after.pop('last_error',None)
 if error:after.setdefault('resolved_errors',[]).append({'original_error':error,'resolution':'new-explicit-search-confirmed-original-unknown-preserved','proof':copy.deepcopy(proof_ref)})
 after['phase']='chooseCompany';after['revision']=before['revision']+1;after['company_search_wait_started']=facts['input_at'];return after

def search_progression_admission(current,job_ref,*,_saved_snapshot=False):
 marker=current.get('company_search_explicit_recovery')
 if marker is None:return None
 facts=verify_search_terminal(marker['proof'],job_ref);old=facts['original'];need(marker=={'kind':'authorized-search-superseded-for-progression-v1','proof':facts['proof'],'original_workflow':facts['authority']['original_workflow'],'original_archive':facts['archive'],'original_call_key':'2:searchCompany'},'search-progression-marker');need(current['calls'][:len(old['calls'])]==old['calls']and current.get('phase')not in('account','context','searchCompany')and type(current['revision'])is int and current['revision']>=3 and current.get('state')=='running','search-progression-prefix-phase')
 for k in('work_order_id','fingerprint','company','groupid','date_range','tab_id','initial_groupid','entry_identity','provider_baseline','entry_groupid','identity_contract','company_configuration_job','company_configuration_operation'):
  need(current.get(k)==old.get(k),'search-progression-original-binding')
 need(len({c['key']for c in current['calls']})==len(current['calls'])and all(c.get('state')=='confirmed'for c in current['calls'][len(old['calls']):]),'search-progression-additional-unknown')
 job=doc(job_ref)
 if not _saved_snapshot:
  canonical=json.loads(regular(job['workflow_path']).read_bytes());need(canonical==current,'search-progression-current-canonical')
 active=_SEARCH_COMMAND.get()
 if active is not None:active['counts']['live_checks']+=1
 return facts

def remaining_company_command(job,command,scope_ref,current,path,*,now=None):
 """Ordinary remaining task authority, not exception authority or a renewal.
 Only normal selection/confirmation; new operation binds successful search proof.
 """
 now=now or datetime.now(timezone.utc)
 if command.get('kind')=='company-confirm'and current.get('company_configuration_remaining_operation'):
  old=doc(current['company_configuration_remaining_operation'])
  if current.get('company_configuration_confirm_operation')or datetime.fromisoformat(old['expires_at'])<now:return remaining_confirm_successor_command(job,command,scope_ref,current,path,now=now)
 job_ref={'path':job['work_order_path'],'sha256':hashlib.sha256(regular(job['work_order_path']).read_bytes()).hexdigest()};facts=search_progression_admission(current,job_ref);need(facts is not None and command.get('op')=='click'and command.get('kind')in('company','company-confirm')and current['phase']==('chooseCompany'if command['kind']=='company'else'confirmSwitch'),'company-remaining-phase-action');key='configured-remaining:'+hashlib.sha256(json.dumps([job_ref,facts['proof']],sort_keys=True).encode()).hexdigest();path=Path(path);existing=current.get('company_configuration_remaining_operation')
 if existing is None:
  value={k:copy.deepcopy(v)for k,v in facts['operation'].items()if k!='allowed_action'};value.update(purpose='configured-business-remaining-context-v1',recovery_proof=facts['proof'],key=key,issued_at=now.isoformat(),expires_at=(now+timedelta(seconds=300)).isoformat());need(path.is_absolute()and path.parent==path.parent.resolve()and not any(x.is_symlink()for x in(path,*path.parents)),'company-remaining-operation-path');data=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
  with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  directory=os.open(path.parent,os.O_RDONLY)
  try:os.fsync(directory)
  finally:os.close(directory)
  existing={'path':str(path),'sha256':hashlib.sha256(data).hexdigest()}
 else:need(existing['path']==str(path),'company-remaining-operation-canonical')
 request,checked=business_command(job,command,scope_ref,existing,path,key,now=now);need(checked==existing,'company-remaining-ref');return request,existing

def verify_saved_search_progression(snapshot,job_ref):
 """Pure archived switch-contract facts only; never permits input or live CAS."""
 return search_progression_admission(snapshot,job_ref,_saved_snapshot=True)


def remaining_confirm_preflight(job,current,scope_ref,*,now=None):
 """Ordinary remaining confirmation only; no search/select renewal or transport."""
 now=now or datetime.now(timezone.utc);job_ref={'path':job['work_order_path'],'sha256':hashlib.sha256(regular(job['work_order_path']).read_bytes()).hexdigest()};facts=search_progression_admission(current,job_ref);need(facts is not None and current.get('phase')=='confirmSwitch','company-confirm-successor-phase')
 original=facts['original']['calls'];tail=current['calls'][len(original):];need(len(tail)==1,'company-confirm-successor-no-confirm-intent');selected=tail[0];old_ref=current.get('company_configuration_remaining_operation');need(type(old_ref)is dict and selected.get('state')=='confirmed'and selected.get('phase')=='chooseCompany'and selected.get('command',{}).get('op')=='click'and selected['command'].get('kind')=='company'and selected['command'].get('companyRequest')==old_ref,'company-confirm-successor-selection')
 config,row,_=job_configuration(job);old=doc(old_ref);need(old.get('purpose')=='configured-business-remaining-context-v1','company-confirm-successor-predecessor');operation(config,old_ref,now=datetime.fromisoformat(old['issued_at']));chosen=datetime.fromisoformat(selected['at']);need(datetime.fromisoformat(old['issued_at'])<=chosen<=datetime.fromisoformat(old['expires_at'])<now,'company-confirm-successor-expiry')
 clicked=selected.get('result',{}).get('clicked',{});need(clicked.get('name')==job['company']and clicked.get('selector')and selected['command'].get('locator')=={'by':'selector','value':clicked['selector']},'company-confirm-successor-selection-effect')
 value=doc(scope_ref);button=input_before(value,old,row,'company-confirm');need(button.get('selector')and not button.get('disabled'),'company-confirm-successor-ready');return {'facts':facts,'predecessor':old_ref,'operation':old,'selection':copy.deepcopy(selected),'button':button,'scope':copy.deepcopy(scope_ref)}

def remaining_confirm_expiry_transform(job,current,scope_ref,*,now=None):
 error=current.get('last_error',{});need(set(error)=={'at','code','message'}and error.get('code')==error.get('message')=='company-operation-expired-or-unbounded','company-confirm-expiry-exact-error');facts=remaining_confirm_preflight(job,current,scope_ref,now=now);after=copy.deepcopy(current);prior=after.pop('last_error');after.setdefault('resolved_errors',[]).append({'original_error':prior,'resolution':'expired-ordinary-operation-confirm-only-successor','predecessor':facts['predecessor'],'scope':scope_ref,'proof':facts['facts']['proof']});return after


def _confirm_successor_data(config,reference,op,row,facts):
 need(op['allowed_action']=={'op':'click','kind':'company-confirm','max_inputs':1}and type(op['allowed_action']['max_inputs'])is int,'company-confirm-successor-only-action');old=doc(op['predecessor']);need(old.get('purpose')=='configured-business-remaining-context-v1','company-confirm-successor-old-purpose');operation(config,op['predecessor'],now=datetime.fromisoformat(old['issued_at']));need(old['recovery_proof']==op['recovery_proof']and {k:op[k]for k in ('config','entry_id','tab_id','window_id','source_groupid','provider','source_identity','date_range','original_job')}=={k:old[k]for k in ('config','entry_id','tab_id','window_id','source_groupid','provider','source_identity','date_range','original_job')}and datetime.fromisoformat(old['expires_at'])<datetime.fromisoformat(op['issued_at']),'company-confirm-successor-original-binding')
 selected=op['selection'];clicked=selected.get('result',{}).get('clicked',{});need(selected.get('state')=='confirmed'and selected.get('phase')=='chooseCompany'and selected.get('command',{}).get('companyRequest')==op['predecessor']and selected['command'].get('op')=='click'and selected['command'].get('kind')=='company'and selected['command'].get('tabId')==op['tab_id']and clicked.get('name')==row['company']and selected['command'].get('locator')=={'by':'selector','value':clicked.get('selector')}and clicked.get('selector')and datetime.fromisoformat(old['issued_at'])<=datetime.fromisoformat(selected['at'])<=datetime.fromisoformat(old['expires_at']),'company-confirm-successor-selected')
 if op['supersedes']is not None:
  previous=doc(op['supersedes']);need(previous.get('purpose')==op['purpose']and all(previous.get(k)==op[k]for k in('config','entry_id','tab_id','window_id','source_groupid','provider','source_identity','date_range','original_job','predecessor','selection','recovery_proof','allowed_action'))and datetime.fromisoformat(previous['expires_at'])<datetime.fromisoformat(op['issued_at']),'company-confirm-successor-unconsumed-lineage')

def remaining_confirm_successor_command(job,command,scope_ref,current,path,*,now=None):
 now=now or datetime.now(timezone.utc);need(command.get('op')=='click'and command.get('kind')=='company-confirm','company-confirm-successor-no-search-select');facts=remaining_confirm_preflight(job,current,scope_ref,now=now);existing=current.get('company_configuration_confirm_operation')
 if existing is not None:
  config,_,_=job_configuration(job);previous=doc(existing);operation(config,existing,now=datetime.fromisoformat(previous['issued_at']))
 if existing is not None and(Path(existing['path']+'.server-intent.json').exists()or Path(existing['path']+'.server-intent.json').is_symlink()):raise SearchOpportunityConsumed('company-confirm-opportunity-consumed')
 if existing is not None and now<=datetime.fromisoformat(doc(existing)['expires_at']):
  op=doc(existing);return business_command(job,command,scope_ref,existing,Path(existing['path']),op['key'],now=now)
 # No confirm intent exists (preflight), so expired unconsumed operation data can
 # be superseded. The original select operation and all input records stay exact.
 value=copy.deepcopy(facts['operation']);value.update(purpose='configured-business-confirm-successor-v1',predecessor=facts['predecessor'],selection=facts['selection'],supersedes=existing,allowed_action={'op':'click','kind':'company-confirm','max_inputs':1},issued_at=now.isoformat(),expires_at=(now+timedelta(seconds=300)).isoformat());value['key']='configured-confirm:'+hashlib.sha256(json.dumps([facts['predecessor'],facts['facts']['proof'],now.isoformat()],sort_keys=True).encode()).hexdigest();dest=Path(path).with_name('configured-company-confirm-'+value['key'].split(':')[1]+'.json');need(dest.is_absolute()and dest.parent==dest.parent.resolve()and not any(p.is_symlink()for p in(dest,*dest.parents)),'company-confirm-successor-path');data=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
 with dest.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 fd=os.open(dest.parent,os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
 reference={'path':str(dest),'sha256':hashlib.sha256(data).hexdigest()};return business_command(job,command,scope_ref,reference,dest,value['key'],now=now)

def _claim_confirm_successor(reference,op,command,*,now=None):
 job=doc(op['original_job']);current=json.loads(regular(job['workflow_path']).read_bytes());facts=verify_search_terminal(op['recovery_proof'],op['original_job']);prefix=facts['original']['calls']+[op['selection']];calls=current['calls'];need(calls[:len(prefix)]==prefix and len(calls)==len(prefix)+1 and current.get('phase')=='confirmSwitch','company-confirm-successor-live-prefix');intent=calls[-1];need(intent.get('state')=='unknown'and intent.get('phase')=='confirmSwitch'and intent.get('key')==str(current['revision'])+':confirmSwitch'and intent.get('command')==command and command.get('companyRequest')==reference,'company-confirm-successor-input-intent');base=copy.deepcopy(current);base['calls']=prefix;search_progression_admission(base,op['original_job'],_saved_snapshot=True)
 claim=Path(reference['path']).with_name(Path(reference['path']).name+'.server-intent.json');value={'kind':'ordinary-confirm-successor-server-intent-v1','operation':reference,'command':command,'workflow_input_key':intent['key'],'max_inputs':1};data=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode();need((now or datetime.now(timezone.utc))<=datetime.fromisoformat(op['expires_at']),'company-operation-expired-or-unbounded')
 try:fd=os.open(claim,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
 except FileExistsError:raise SearchOpportunityConsumed('company-confirm-opportunity-consumed')from None
 try:
  with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
  d=os.open(claim.parent,os.O_RDONLY)
  try:os.fsync(d)
  finally:os.close(d)
  if (now or datetime.now(timezone.utc))>datetime.fromisoformat(op['expires_at']):raise ValueError('company-confirm-expired-after-claim')
 except Exception:raise SearchOpportunityConsumed('company-confirm-opportunity-consumed')from None
