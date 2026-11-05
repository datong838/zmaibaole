"""Explicit unresolved epoch previews and one supervisor-bound fresh retake.
No UI here. Archiving/authorization never certifies or crops the failed old PNG.
"""
import copy,json,hashlib,re,os,math,fcntl
from pathlib import Path
from datetime import datetime,timezone
CONSISTENCY='unresolved-global-epoch-change-v1'
PLAN='failed-region-postguard-retake-plan-v1'
AUTH='supervisor-region-postguard-retake-once-v1'
def need(ok,code):
 if not ok:raise ValueError(code)
def canonical(p):
 p=Path(p);need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'retake-canonical-path-required');return p
def sha(p):return hashlib.sha256(canonical(p).read_bytes()).hexdigest()
def ref(p):return {'path':str(canonical(p)),'sha256':sha(p)}
def read(r):
 need(isinstance(r,dict) and set(r)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(r['sha256'])),'retake-reference-invalid');p=canonical(r['path']);raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==r['sha256'],'retake-reference-changed');return json.loads(raw)
def publish(p,v):
 p=canonical(p);p.parent.mkdir(parents=True,exist_ok=True);raw=v if isinstance(v,bytes) else (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 try:
  with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 except FileExistsError:need(p.read_bytes()==raw,'retake-immutable-evidence-conflict')
 return ref(p)
def compare(before,after,geometry,after_geometry,*,business):
 need(geometry==after_geometry,'violation-region-dom-or-native-frame-changed')
 if before==after:return None
 a={**before,'base_proof':{k:v for k,v in before.get('base_proof',{}).items()if k!='epoch'}};b={**after,'base_proof':{k:v for k,v in after.get('base_proof',{}).items()if k!='epoch'}};x=before.get('base_proof',{}).get('epoch');y=after.get('base_proof',{}).get('epoch')
 need(business and a==b and type(x) is int and type(y) is int and 0<=x<y,'violation-region-dom-or-native-frame-changed')
 return {'contract':CONSISTENCY,'before_epoch':x,'after_epoch':y,'semantic_or_layout_history_resolved':False,'outside_scope_cause_proven':False,'automatic_certification':False,'requires_supervisor_pixel_field_review':True}
# v13-only diagnostic successor. The legacy epoch comparator remains unchanged.
_EPOCH_ONLY_COMPARE=compare
V13_BUILD='viewport-notice-business-cells-v13-fractional-auto-padding-v1'
V13_DIAGNOSTIC_PROJECTION='unselected-header0-readonly-diagnostic-history-unresolved-v1'
def _v13_diagnostic(d):
 need(isinstance(d,dict)and set(d)=={'purpose','candidates','candidate_count','truncated'}and d['purpose']=='readonly-overlay-diagnostic-only','v13-diagnostic-schema')
 n=d['candidate_count'];items=d['candidates'];need(type(n)is int and 0<=n<=100000 and isinstance(items,list)and len(items)==min(n,12)and type(d['truncated'])is bool and d['truncated']==(n>len(items)),'v13-diagnostic-bounds')
 keys={'selector','tag','class','class_truncated','position','pointer_events','opacity','background_color','background_image_present','has_text'}
 for item in items:
  need(isinstance(item,dict)and set(item)==keys,'v13-diagnostic-candidate-schema');need(item['selector']is None or isinstance(item['selector'],str)and len(item['selector'])<=1500,'v13-diagnostic-selector')
  need(isinstance(item['class'],str)and len(item['class'])<=500 and all(type(item[k])is bool for k in('class_truncated','background_image_present','has_text')),'v13-diagnostic-class-bools');need(all(isinstance(item[k],str)and len(item[k])<=200 for k in('tag','position','pointer_events','opacity','background_color')),'v13-diagnostic-strings')
def compare_v13_unselected_header(before,after,geometry,after_geometry):
 need(geometry==after_geometry,'violation-region-dom-or-native-frame-changed')
 need(all(p.get('base_proof',{}).get('diagnostic_build')==V13_BUILD for p in(before,after)),'v13-diagnostic-build-required')
 for p in(before,after):
  cov=p.get('derived_business_coverage',{});ids=cov.get('notice_ids');need(isinstance(ids,list)and 1<=len(ids)<=100 and len(set(ids))==len(ids)and all(isinstance(n,str)and 1<=len(n)<=100 for n in ids)and cov.get('list_headers_visible')is False and cov.get('date_filter_visible')is False,'v13-diagnostic-business-rows-only')
  need(p.get('occlusion_verified')is False and p.get('quality_review_required')is True,'v13-diagnostic-pixel-review-required')
 a=copy.deepcopy(before);b=copy.deepcopy(after);x=a['base_proof'].pop('epoch',None);y=b['base_proof'].pop('epoch',None);need(type(x)is int and type(y)is int and 0<=x<y,'v13-diagnostic-forward-epoch')
 ae=a['base_proof']['elements'];be=b['base_proof']['elements'];need(isinstance(ae,list)and isinstance(be,list)and len(ae)==len(be)and 1<len(ae)<=101,'v13-diagnostic-element-bounds');changed=[]
 for i,(left,right)in enumerate(zip(ae,be)):
  if left.get('possible_overlay_diagnostic')==right.get('possible_overlay_diagnostic'):continue
  need(all(e.get('kind')in('header','row') and e.get('notice_id')not in ids and e.get('possible_overlay_absent')is False and e.get('fully_visible')is False for e in(left,right)),'v13-diagnostic-selected-or-visible-element-changed')
  _v13_diagnostic(left['possible_overlay_diagnostic']);_v13_diagnostic(right['possible_overlay_diagnostic']);del left['possible_overlay_diagnostic'];del right['possible_overlay_diagnostic'];changed.append(i)
 need(bool(changed)and a==b,'v13-diagnostic-non-diagnostic-material-changed')
 return {'contract':CONSISTENCY,'before_epoch':x,'after_epoch':y,'semantic_or_layout_history_resolved':False,'outside_scope_cause_proven':False,'automatic_certification':False,'requires_supervisor_pixel_field_review':True,'diagnostic_projection':(V13_DIAGNOSTIC_PROJECTION if changed==[1]else'v13-unselected-elements-diagnostic-only-v1'),'changed_unselected_elements':changed,'global_epoch_history_resolved':False,'occlusion_verified':False,'original_before_digest':hashlib.sha256(json.dumps(before,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),'original_after_digest':hashlib.sha256(json.dumps(after,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()}
def compare(before,after,geometry,after_geometry,*,business):
 if business and all(p.get('base_proof',{}).get('diagnostic_build')==V13_BUILD for p in(before,after)):
  a={**before,'base_proof':{k:v for k,v in before.get('base_proof',{}).items()if k!='epoch'}};b={**after,'base_proof':{k:v for k,v in after.get('base_proof',{}).items()if k!='epoch'}}
  if a!=b:return compare_v13_unselected_header(before,after,geometry,after_geometry)
 return _EPOCH_ONLY_COMPARE(before,after,geometry,after_geometry,business=business)

def write_after(directory,operation,command,before,after,geometry,after_geometry,capture_metadata,before_at,after_at,geometry_at):
 directory=canonical(directory);g=publish(directory/'after-geometry.json',{'kind':'actual-postcapture-native-geometry-v1','operation':operation,'native_command':command,'observed_at':geometry_at,'geometry':after_geometry})
 audit={'kind':'actual-region-postguard-comparison-v1','operation':operation,'native_command':command,'before':before,'after':after,'geometry_before':geometry,'geometry_after':after_geometry,'after_geometry':g,'capture_metadata':capture_metadata,'proof_before_observed_at':before_at,'proof_after_observed_at':after_at,'geometry_observed_at':geometry_at}
 return publish(directory/'postguard-comparison.json',audit)
def verify_pair(m,*,business):
 before=m['public_dom_proof']['before'];after=m['public_dom_proof']['after'];claim=m.get('postguard_consistency')
 need(not (isinstance(claim,dict) and claim.get('contract')==W67_CONSISTENCY) or business,'W67-business-only')
 expected=reviewed_original_pair(before,after,m['geometry_before'],m['geometry_after']) if isinstance(claim,dict) and claim.get('contract')==W67_CONSISTENCY else compare(before,after,m['geometry_before'],m['geometry_after'],business=business)
 need(claim==expected,'region-postguard-consistency-not-derived')
 if m['pinned_inputs'].get('retake_authorization'):need('postguard_audit' in m,'retake-actual-postguard-audit-required')
 if 'postguard_audit' in m:
  a=read(m['postguard_audit']);need(isinstance(a.get('after_geometry'),dict),'region-postguard-actual-after-geometry-required');g=read(a['after_geometry']);need(a.get('kind')=='actual-region-postguard-comparison-v1' and all(a.get(k)==m[v] for k,v in (('geometry_before','geometry_before'),('geometry_after','geometry_after'),('proof_before_observed_at','proof_before_observed_at'),('proof_after_observed_at','proof_after_observed_at'),('capture_metadata','capture_metadata'))) and a.get('before')==before and a.get('after')==after and a.get('native_command')==m['pinned_inputs']['native_command'] and g=={'kind':'actual-postcapture-native-geometry-v1','operation':a['operation'],'native_command':a['native_command'],'observed_at':a['geometry_observed_at'],'geometry':m['geometry_after']},'region-postguard-audit-changed')
  when=lambda v:datetime.fromisoformat(v)
  need(when(m['proof_after_observed_at'])<=when(a['geometry_observed_at'])<=when(m['recorded_at']),'region-postguard-geometry-time-invalid')
  b=m['pinned_inputs'];directory=canonical(m['capture_metadata']['path']).parent;operation={k:{'path':b[k+'_path'],'sha256':b[k+'_sha256']} for k in ('source','observation','profile')};operation.update(pid=m['native_pid'],mode=m['frame_mode'],revision=m['revision'],key=b.get('original_operation_key',b['captureKey'].rsplit(':region:',1)[0]),outdir=str(directory.parent if b.get('retake_authorization') else directory),replaces=m.get('replaces_manifest'))
  if b.get('screenshot_anchor') is not None:operation['screenshot_anchor']=b['screenshot_anchor']
  if b.get('uncovered_selection') is not None:operation['uncovered_only']=True
  need(a['operation']==operation,'region-postguard-operation-changed')
  # A new audit cannot be attached afterwards to an old failed raw. The actual
  # capture transaction must already have durably recorded this exact audit.
  import region_frame_capture as r
  journal=canonical(b['source_path']).parent/'.native-region-frame-state'/(r.fc.fingerprint([b['source_sha256'],m['chain_id']])+'.json');owner=read(ref(journal));entries=[e for e in owner.get('frames',[]) if e.get('operation')==operation]
  need(owner.get('scope')=={'source_sha256':b['source_sha256'],'profile_sha256':b['profile_sha256'],'chain_id':m['chain_id']} and len(entries)==1,'region-postguard-canonical-owner-required');entry=entries[0]
  need(entry.get('state') in ('unknown','awaiting-visual-review','complete') and entry.get('postguard_audit')==m['postguard_audit'] and entry.get('raw_capture_metadata')==m['capture_metadata'] and entry.get('before')==before and entry.get('geometry_before')==m['geometry_before'],'region-postguard-not-persisted-by-original-capture')
  if b.get('retake_authorization'):
   attempt=entry.get('retake_attempt',{});need(attempt.get('authorization')==b['retake_authorization'],'region-postguard-retake-owner-mismatch');need(attempt.get('state')=={'unknown':'issued-unknown','awaiting-visual-review':'preview-complete','complete':'complete'}[entry['state']],'region-postguard-retake-outcome-mismatch')
   if entry['state']!='unknown':need(attempt.get('registration')==entry.get('registration') and attempt.get('raw_capture_metadata')==m['capture_metadata'],'region-postguard-retake-outcome-reference-mismatch')
  need(canonical(m['postguard_audit']['path'])==Path(m['capture_metadata']['path']).parent/'postguard-comparison.json' and canonical(a['after_geometry']['path'])==Path(m['capture_metadata']['path']).parent/'after-geometry.json','region-postguard-audit-location-invalid')
 else:need(expected is None,'region-epoch-preview-missing-actual-geometry-audit')
 if expected is not None:need(m.get('quality_review_required') is True and m.get('occlusion_verified') is False,'region-epoch-drift-requires-manual-preview')
 return expected

def no_other_unknown(source,journal,expected_current):
 """Only the exact bound failed/authorized own entry is exempt. Other attempts remain locked."""
 base=canonical(source['path']).parent;journal=canonical(journal)
 need(journal.parent==base/'.native-region-frame-state' and read(ref(journal))==expected_current,'retake-current-journal-changed')
 for folder in ('.frame-capture-state','.native-frame-capture-state','.native-region-frame-state'):
  for path in (base/folder).glob('*.json'):
   state=read(ref(path))
   if state.get('scope',{}).get('source_sha256')==source['sha256']:
    if canonical(path)==journal:need(state==expected_current,'retake-current-journal-changed')
    else:need(all(e.get('state')=='complete' for e in state.get('frames',[])),'retake-other-capture-unresolved')

def _cli(cli,operation,r):
 need(cli.get('returncode')==1 and 'violation-region-dom-or-native-frame-changed' in cli.get('stderr','') and not cli.get('stdout'),'retake-original-cli-not-postguard-failure');argv=cli.get('argv',[]);need(len(argv)>=3 and canonical(argv[1])==canonical(Path(r.fc.__file__).resolve().parents[3]/'skills/violation-notifier/scripts/region_frame_capture.py') and argv[2]=='capture','retake-cli-entry-mismatch');args=argv[3:];need(len(args)%2==0 and len(set(args[::2]))==len(args)//2,'retake-cli-options-invalid');actual=dict(zip(args[::2],args[1::2]));expected={}
 for name in ('source','observation','profile'):
  expected['--'+name]=operation[name]['path'];expected['--'+name+'-sha256']=operation[name]['sha256']
 expected.update({'--pid':str(operation['pid']),'--mode':operation['mode'],'--chain-id':operation['chain_id'],'--key':operation['key'],'--outdir':operation['outdir'],'--revision':operation['revision']})
 for name,opt in (('screenshot_anchor','screenshot-anchor'),('replaces','replaces-manifest')):
  if operation.get(name):expected['--'+opt]=operation[name]['path'];expected['--'+('screenshot-anchor-sha256' if name=='screenshot_anchor' else 'replaces-sha256')]=operation[name]['sha256']
 need(actual==expected,'retake-original-cli-operation-mismatch');need(type(cli.get('start_clock_monotonic')) in (int,float) and type(cli.get('end_clock_monotonic')) in (int,float) and math.isfinite(cli['start_clock_monotonic']) and math.isfinite(cli['end_clock_monotonic']) and 0<=cli['start_clock_monotonic']<cli['end_clock_monotonic'],'retake-original-cli-time-invalid')
def _derive(state,journal,files,r,*,execution=False):
 need(isinstance(state.get('frames'),list) and len(state['frames'])==1,'retake-current-only-single-failed-frame');entry=state['frames'][0];need(set(entry)=={'state','operation','intent_at','before','geometry_before'} and entry['state']=='unknown','retake-original-failed-entry-required');op=copy.deepcopy(entry['operation']);source=op['source'];profile=op['profile'];chain=state['scope']['chain_id'];op['chain_id']=chain
 need(state['scope']=={'source_sha256':source['sha256'],'profile_sha256':profile['sha256'],'chain_id':chain} and canonical(journal)==Path(source['path']).parent/'.native-region-frame-state'/(r.fc.fingerprint([source['sha256'],chain])+'.json'),'retake-original-canonical-chain-required');need(op['mode']=='anchor' and not op.get('uncovered_only'),'retake-current-anchor-only')
 inputs=r.fc.page_inputs(source,op['observation'],profile,screenshot_anchor=op.get('screenshot_anchor'));need(r.is_business(inputs),'retake-business-only');r.legacy_gate(source,profile,op.get('replaces'));
 if execution:no_other_unknown(source,journal,state);r.business.no_unresolved_navigation(source,profile)
 _cli(read(files['failed_cli']),op,r);root=canonical(op['outdir']);expected={'raw':root/'raw-window.png','native_metadata':root/'raw-window.json'};need(all(canonical(files[k]['path'])==p for k,p in expected.items()),'retake-original-artifact-location-invalid')
 need(not (root/'list-region.png').exists() and not any((root/n).exists() for n in ('preview-registration.json','region-frame.json','registration.json','after-geometry.json','postguard-comparison.json')),'retake-original-output-or-after-geometry-present')
 before_envelope=read(files['before']);after_envelope=read(files['after']);base_envelope=read(files['base'])
 for stage,envelope in (('base',base_envelope),('before',before_envelope),('after',after_envelope)):
  need(envelope.get('kind')=='public-region-proof-transport-reply-v1' and envelope.get('stage')==stage and envelope.get('operation')==op,'retake-original-proof-operation-mismatch');need(canonical(files[stage]['path']).parent==root/'proof-replies','retake-original-proof-path-invalid')
 before=r.checked(before_envelope['reply'],before_envelope['command'],inputs);after=r.checked(after_envelope['reply'],after_envelope['command'],inputs);need(before==entry['before'] and before_envelope['command']==after_envelope['command']==r.region_request(inputs,before['base_proof'],op['mode']),'retake-original-proof-not-derived');r.business.validate_base(base_envelope['reply']['result'],inputs);need(base_envelope['command']==inputs['command'],'retake-original-base-command-invalid');need(compare(before,after,entry['geometry_before'],entry['geometry_before'],business=True) is not None,'retake-original-failure-not-epoch-only')
 command=r.historical.native_command(inputs,op['pid'],op['key']+':region:'+op['revision']);meta=read(files['native_metadata']);r.nw.validate(meta,command,files['raw']['path']);need(meta['png']['sha256']==files['raw']['sha256'] and meta['before']['scope']==entry['geometry_before']['scope'] and meta['before']['window']==entry['geometry_before']['window'],'retake-original-native-binding-invalid')
 need(r.sr.when(entry['intent_at'])<=r.sr.when(meta['intent_at'])<=r.sr.when(meta['captured_at'])<=r.sr.when(meta['completed_at'])<=r.sr.when(after_envelope['recorded_at']),'retake-original-time-chain-invalid')
 return {'operation':entry['operation'],'scope':state['scope'],'old_capture_key':command['captureKey'],'old_after_geometry_available':False,'old_image_certified':False,'old_image_may_be_reused':False}

def derive_plan(state_ref,cli_ref):
 import region_frame_capture as r
 state=read(state_ref);need(len(state.get('frames',[]))==1,'retake-current-only-single-failed-frame');root=canonical(state['frames'][0]['operation']['outdir']);files={'failed_cli':cli_ref,'raw':ref(root/'raw-window.png'),'native_metadata':ref(root/'raw-window.json')}
 for stage in ('base','before','after'):
  matches=list((root/'proof-replies').glob(stage+'-*.json'));need(len(matches)==1,'retake-original-proof-file-not-unique');files[stage]=ref(matches[0])
 facts=_derive(state,canonical(state_ref['path']),files,r,execution=True);need(read(state_ref)==state,'retake-original-live-state-changed');need(all(sha(v['path'])==v['sha256'] for v in files.values()),'retake-original-evidence-changed');return {'kind':PLAN,'canonical_journal':state_ref['path'],'original_state_sha256':state_ref['sha256'],'original_files':files,'derived':facts}
def prepare(state_ref,cli_ref):
 journal=canonical(state_ref['path'])
 with journal.with_suffix('.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan=derive_plan(state_ref,cli_ref);folder=journal.parent/'.postguard-retakes'/state_ref['sha256'];archives={'state':publish(folder/'original-state.json',journal.read_bytes())}
  for name,r in plan['original_files'].items():archives[name]=publish(folder/('original-'+name+Path(r['path']).suffix),canonical(r['path']).read_bytes())
  need(read(state_ref)==read(archives['state']) and all(archives[k]['sha256']==v['sha256'] for k,v in plan['original_files'].items()),'retake-archive-not-original-bytes');plan['archives']=archives;return publish(folder/'plan.json',plan)
def validate_plan(plan_ref):
 import region_frame_capture as r
 p=read(plan_ref);need(p.get('kind')==PLAN,'retake-plan-kind-invalid');folder=canonical(p['canonical_journal']).parent/'.postguard-retakes'/p['original_state_sha256'];need(canonical(plan_ref['path'])==folder/'plan.json' and canonical(p['archives']['state']['path'])==folder/'original-state.json' and p['archives']['state']['sha256']==p['original_state_sha256'],'retake-plan-canonical-invalid');state=read(p['archives']['state'])
 for name,original in p['original_files'].items():
  archive=p['archives'][name];need(canonical(archive['path'])==folder/('original-'+name+Path(original['path']).suffix) and archive['sha256']==original['sha256'] and canonical(archive['path']).read_bytes()==canonical(original['path']).read_bytes(),'retake-archive-evidence-changed');read(original) if name!='raw' else need(sha(original['path'])==original['sha256'],'retake-old-raw-changed')
 need(_derive(state,canonical(p['canonical_journal']),p['original_files'],r)==p['derived'],'retake-plan-not-derived');return p,state
def authorization(auth_ref):
 a=read(auth_ref);need(set(a)=={'kind','decision','reviewer_role','at','plan'} and a['kind']==AUTH and a['decision']=='one-fresh-retake-same-operation' and a['reviewer_role']=='supervisor' and datetime.fromisoformat(a['at']).utcoffset() is not None,'retake-supervisor-authorization-required');p,old=validate_plan(a['plan']);need(canonical(auth_ref['path'])==canonical(a['plan']['path']).parent/'supervisor-authorization.json','retake-canonical-authorization-required');op=p['derived']['operation'];token=auth_ref['sha256'][:16];directory=canonical(op['outdir'])/('retake-'+token);key=op['key']+':retake:'+token+':region:'+op['revision'];need(len(key)<=128 and key!=p['derived']['old_capture_key'],'retake-derived-native-key-invalid');return a,p,old,directory,key
def begin(auth_ref,state,journal,operation):
 a,p,old,directory,key=authorization(auth_ref);need(str(canonical(journal))==p['canonical_journal'] and state==old and operation==p['derived']['operation'] and sha(journal)==p['original_state_sha256'],'retake-original-live-state-changed');need(not directory.exists(),'retake-attempt-directory-already-exists');no_other_unknown(operation['source'],journal,state);entry=state['frames'][0];entry['retake_attempt']={'kind':'fresh-region-retake-attempt-v1','authorization':auth_ref,'plan':a['plan'],'attempt_directory':str(directory),'native_capture_key':key,'state':'issued-unknown','issued_at':datetime.now(timezone.utc).isoformat(),'original_entry_sha256':hashlib.sha256(json.dumps(old['frames'][0],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()};return entry,directory,key

def validate_registration(m):
 verify_pair(m,business=True)  # standalone retake validation cannot bypass the actual audit/owner
 b=m['pinned_inputs'];a,p,old,directory,key=authorization(b['retake_authorization']);op=p['derived']['operation'];need(b.get('retake_plan')==a['plan'] and m['chain_id']==p['derived']['scope']['chain_id'] and b['captureKey']==key and all(b.get(k+'_sha256')==op[k]['sha256'] and b.get(k+'_path')==op[k]['path'] for k in ('source','observation','profile')) and m['native_pid']==op['pid'] and m['frame_mode']==op['mode'] and m['revision']==op['revision'] and b.get('original_operation_key')==op['key'],'retake-registration-scope-changed');need(canonical(m['capture_metadata']['path'])==directory/'raw-window.json' and canonical(m['derivation']['source']['path'])==directory/'raw-window.png' and canonical(m['image']['path']).parent==directory,'retake-fresh-image-path-required');need(str(directory/'raw-window.png')!=p['original_files']['raw']['path'],'retake-cannot-reuse-original-raw');return [b['retake_authorization'],a['plan'],*p['archives'].values(),*p['original_files'].values()]

def main():
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
 a=sub.add_parser('plan');a.add_argument('--state',required=True);a.add_argument('--state-sha256',required=True);a.add_argument('--failed-cli',required=True);a.add_argument('--failed-cli-sha256',required=True);a.add_argument('--archive',action='store_true',help='Publish immutable canonical plan archives; never UI or state mutation.')
 a=sub.add_parser('verify-authorization');a.add_argument('--authorization',required=True);a.add_argument('--authorization-sha256',required=True)
 v=parser.parse_args()
 if v.action=='plan':
  state={'path':v.state,'sha256':v.state_sha256};cli={'path':v.failed_cli,'sha256':v.failed_cli_sha256};result=prepare(state,cli) if v.archive else derive_plan(state,cli)
 else:
  a,p,old,directory,key=authorization({'path':v.authorization,'sha256':v.authorization_sha256});result={'plan':a['plan'],'canonical_journal':p['canonical_journal'],'attempt_directory':str(directory),'native_capture_key':key,'old_image_may_be_reused':False,'ui_used':False}
 print(json.dumps(result,ensure_ascii=False,sort_keys=True))


# Exact original W67 pair, separate from the unchanged general compare.
W67_CONSISTENCY = 'reviewed-unselected-overlay-diagnostic-history-unresolved-v1'
W67_ORIGINAL_AUDIT = {'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/companies/1/frames/0005-rows/postguard-comparison.json', 'sha256': '16af8474d805110daf8734d7771f2867d2cac680114c0bb39133d9ece196eb1a'}
W67_NOTICE = 'ZS202610264820919207'
W67_TARGETS = {1: ('header', 'notice-five-business-cells-v1:header0', None), 6: ('row', 'notice-five-business-cells-v1:row0', '202610274830958481')}
W67_DKEYS = {'purpose', 'candidates', 'candidate_count', 'truncated'}
W67_CKEYS = {'selector', 'tag', 'class', 'class_truncated', 'position', 'pointer_events', 'opacity', 'background_color', 'background_image_present', 'has_text'}

def _w67_digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def _w67_diagnostic(d):
    need(type(d) is dict and set(d) == W67_DKEYS and (d['purpose'] == 'readonly-overlay-diagnostic-only'), 'W67-diagnostic-schema')
    n = d['candidate_count']
    c = d['candidates']
    need(type(n) is int and n >= 0 and (type(c) is list) and (len(c) == min(n, 12)) and (type(d['truncated']) is bool) and (d['truncated'] == (n > len(c))), 'W67-diagnostic-bounds')
    for x in c:
        need(type(x) is dict and set(x) == W67_CKEYS, 'W67-candidate-schema')
        need(x['selector'] is None or (type(x['selector']) is str and len(x['selector']) <= 1500), 'W67-selector-bounds')
        need(type(x['class']) is str and len(x['class']) <= 500, 'W67-class-bounds')
        need(all((type(x[k]) is bool for k in ('class_truncated', 'background_image_present', 'has_text'))), 'W67-candidate-bool')
        need(all((type(x[k]) is str for k in ('tag', 'position', 'pointer_events', 'opacity', 'background_color'))), 'W67-candidate-string')

def _w67_qualify(before, after, geometry, after_geometry, *, original_audit):
    """An exact pair, not a generic projection tolerance or a certification."""
    need(geometry == after_geometry == original_audit['geometry_before'] == original_audit['geometry_after'], 'W67-native-geometry-changed')
    need(before.get('derived_business_coverage', {}).get('notice_ids') == [W67_NOTICE] and after.get('derived_business_coverage', {}).get('notice_ids') == [W67_NOTICE], 'W67-selected-notice-changed')
    for p in (before, after):
        cov = p['derived_business_coverage']
        need(cov.get('list_headers_visible') is False and cov.get('date_filter_visible') is False, 'W67-selected-header-or-date')
        need(p['selectors'] == original_audit['before']['selectors'] and p['region'] == original_audit['before']['region'], 'W67-original-region-changed')
        for (i, identity) in W67_TARGETS.items():
            e = p['base_proof']['elements'][i]
            need(tuple((e.get(k) for k in ('kind', 'key', 'notice_id'))) == identity and e.get('notice_id') != W67_NOTICE, 'W67-unselected-target-changed')
            need(e['possible_overlay_absent'] is False and e['fully_visible'] is False, 'W67-occlusion-eligibility-changed')
            _w67_diagnostic(e['possible_overlay_diagnostic'])
    a = copy.deepcopy(before)
    b = copy.deepcopy(after)
    need(a['base_proof'].pop('epoch') == 5252 and b['base_proof'].pop('epoch') == 5254, 'W67-original-epoch-pair-required')
    for i in W67_TARGETS:
        del a['base_proof']['elements'][i]['possible_overlay_diagnostic']
        del b['base_proof']['elements'][i]['possible_overlay_diagnostic']
    need(a == b, 'W67-other-proof-change')
    need(before == original_audit['before'] and after == original_audit['after'], 'W67-exact-original-pair-required')
    return {'contract': W67_CONSISTENCY, 'original_before_digest': _w67_digest(before), 'original_after_digest': _w67_digest(after), 'selected_notice_ids': [W67_NOTICE], 'changed_unselected_elements': list(W67_TARGETS), 'semantic_or_layout_history_resolved': False, 'global_epoch_history_resolved': False, 'outside_scope_cause_proven': False, 'automatic_certification': False, 'occlusion_verified': False, 'requires_independent_five_field_pixel_review': True, 'row6_covered': False}

def reviewed_original_pair(before, after, geometry, after_geometry):
    """Contract-fixed original audit; callers cannot substitute an audit view."""
    return _w67_qualify(before, after, geometry, after_geometry, original_audit=read(W67_ORIGINAL_AUDIT))

if __name__=='__main__':main()
