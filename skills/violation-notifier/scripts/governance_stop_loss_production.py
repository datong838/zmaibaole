#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Concrete auto-flow ports. Imported by future formal wiring; no CLI/UI on import."""
import copy,json,hashlib,os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
import governance_detail as d
import governance_dom as g
import governance_stop_loss as product
import governance_rates_stop_loss as rates
import governance_stop_loss_integration as integration
import governance_rates_direct_recovery as recovery
import governance_rates_direct_replay as replay
nav=d.nav
KIND='rates-direct-sidebar-roundtrip-v1'
KINDS={'rates':KIND,'stock':'stock-direct-sidebar-roundtrip-v1','operation':'operation-direct-sidebar-roundtrip-v1','operation_control':'operation-control-direct-sidebar-roundtrip-v1'}
MANIFESTS={'rates':'rates-direct-sidebar-list-recovery-v1','stock':'stock-direct-sidebar-list-recovery-v1','operation':'operation-direct-sidebar-list-recovery-v1','operation_control':'operation-control-direct-sidebar-list-recovery-v1'}
def parser(kind):
 if kind=='operation':return rates.parse_operation
 if kind=='operation_control':return rates.parse_operation_control
 if kind=='stock':
  import governance_stock_stop_loss
  return governance_stock_stop_loss.parse
 g.need(kind=='rates','auto-direct-template-unknown');return rates.parse
SIDEBAR='#box-aside-menu > div > div:nth-of-type(8) > div > div:nth-of-type(1) > span > div > span'

def sidebar(raw,kind):
 if kind in ('operation','operation_control') or (kind=='rates' and any(n.get('attributes',{}).get('class')=='flex items-center flex-wrap text-[20px] font-[600] leading-[28px]' and n.get('name')=='门店不接单率超标' for n in g.nodes(raw['tree']))):
  selector='#box-aside-memu-content > div:nth-of-type(2) > div:nth-of-type(10) > div > div > div > div:nth-of-type(1) > span > div > div > span'
  classname='navi_violation_center src-components-AsideMenuV2-index-module__label--DrJTx--212e2 src-components-AsideMenuV2-index-module__second-label--jbRfT--212e2'
 else:
  selector=SIDEBAR;classname='navi_violation_center src-components-AsideMenu-index-module__label--Pcplo--212e2'
 return g.one([n for n in g.nodes(raw['tree']) if n.get('selector')==selector and n.get('tag')=='span' and n.get('role')=='generic' and n.get('attributes',{}).get('class')==classname and not n.get('children') and g.text(n)=='违规中心' and not n.get('disabled')],'auto-direct-sidebar-shape-changed')

def state_path(m,v):return Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])/'state.json'
def own(r,b):r.s['automatic_stop_loss_owner']={'binding_sha256':integration.digest(b),'program_phase':r.s['phase']};r.save()
def direct_source(manifest):
 g.need(manifest.get('kind') in MANIFESTS.values(),'auto-direct-manifest-invalid');m=d.document(manifest['detail_manifest']);v=d.inputs(m);parent=d.document(manifest['parent_state']);stage=parent['automatic_rates_stage'];original=d.document(stage['original_parent']);binding=integration.detect(original,m,v)
 folder=integration.location(m,v,original['current']['notice_id']).parent;g.need(Path(stage['original_parent']['path']).resolve()==folder/'original-parent.json' and Path(manifest['parent_state']['path']).resolve()==folder/'rates-recovery'/('source-parent-'+manifest['parent_state']['sha256']+'.json') and Path(manifest['detail_manifest']['path']).resolve()==folder/'rates-recovery'/'detail-manifest.json','auto-direct-canonical-source-required')
 g.need(binding is not None and binding['kind'] in ('rates','stock','operation','operation_control') and manifest['kind']==MANIFESTS[binding['kind']] and parent['manifest']==m and parent['phase']=='auto-rates-center-ready' and not recovery.unknown(parent),'auto-direct-parent-unsettled');g.need(stage['binding']==binding and original['details']==parent['details'] and original['cursor']==parent['cursor'] and original['calls']==parent['calls'][:len(original['calls'])],'auto-direct-source-prefix-changed');g.need(not recovery.unknown(v['query']),'auto-direct-query-unknown');g.need(original['cursor']==len(original['details']) and original['cursor']<len(v['query']['rows']),'auto-direct-current-cursor-invalid');row=v['query']['rows'][original['cursor']];opening=original['calls'][-1];facts,_=parser(binding['kind'])(d.document(parent['current']['detail_observation']),row,opening,v['job']);g.need(d.same_facts(facts,parent['current']['facts']) and integration.digest({k:x for k,x in facts.items() if k!='observed_at'})==binding['facts_sha256'] and parent['current']['normal_before']==original['current']['normal_before'] and parent['current']['notice_id']==row['notice_id'],'auto-direct-facts-changed')
 calls=parent['calls'][len(original['calls']):];call=g.one(calls,'auto-direct-sidebar-call-not-unique');before=d.document(call['before']);fresh,_=parser(binding['kind'])(before,row,opening,v['job']);g.need(d.same_facts(facts,fresh),'auto-direct-before-sidebar-facts-changed');target=sidebar(before,binding['kind']);expected={**g.click(target,'navigation'),'tabId':m['tab_id']};g.need(call['state']=='confirmed' and call['command']==expected,'auto-direct-sidebar-unconfirmed');d.reply_matches(expected,call['result'],before)
 center=d.document(parent['last_observation']);recovery.scope(center,v['job'],m['tab_id'],g.CENTER);g.need(center['tab']['windowId']==binding['window_id'],'auto-direct-window-changed');return m,v,parent,row

def verify_direct_entry(entry,state,m,v,row):
 g.need(entry.get('template_kind') in KINDS and entry.get('completion_kind')==KINDS[entry['template_kind']] and entry['state']=='complete','auto-direct-completion-invalid');rm=d.document(entry['recovery_manifest']);rs=d.document(entry['recovery_state']);folder=Path(rm['parent_state']['path']).resolve().parent;g.need(Path(entry['recovery_manifest']['path']).resolve()==folder/'manifest.json' and Path(entry['recovery_state']['path']).resolve()==folder/('final-state-'+entry['recovery_state']['sha256']+'.json'),'auto-direct-immutable-final-required');verified=replay.verify_recovery(rm,rs);_,_,parent,source=direct_source(rm);index=parent['cursor'];g.need(entry['template_kind']==parent['automatic_rates_stage']['binding']['kind'],'auto-direct-template-changed');g.need(source==row and parent['details']==state['details'][:index] and parent['calls']==state['calls'][:len(parent['calls'])] and entry['source_parent']==rm['parent_state'],'auto-direct-completed-prefix-changed');g.need(entry['facts']==parent['current']['facts'] and entry['detail_observation']==parent['current']['detail_observation'] and entry['normal_before']==parent['current']['normal_before'],'auto-direct-completed-source-changed');fresh,at=replay.observed(entry['normal_after'],v['job'],m['tab_id'],d.document(parent['last_observation'])['tab']['windowId'],g.RECORDS);g.need(d.normal_page(fresh['tree'],v['job'],v['query'])==verified['restored_page'] and at>=datetime.fromisoformat(d.document(verified['normal_after'])['observed_at']),'auto-direct-final-page-changed');return entry['facts']

class Ports:
 def __init__(self,m,invoke=None):self.m=m;self.v=d.inputs(m);self.invoke=invoke;self.main=state_path(m,self.v)
 def load(self):return json.loads(self.main.read_text())
 def runner(self,cls=d.Runner):return cls(self.m,self.invoke)
 def flow(self,b):return json.loads(integration.location(self.m,self.v,b['notice_id']).read_text())
 def assert_source(self,b,s):
  parent=self.load();g.need(parent['manifest']==self.m and parent['details'][:b['cursor']]==d.document(s['original_parent'])['details'],'auto-port-original-prefix-changed');g.need(not recovery.unknown(parent),'auto-port-parent-unknown')
  folder=integration.location(self.m,self.v,b['notice_id']).parent/'rates-recovery'
  for name in ('state.json','center-range.json','records-range.json'):
   p=folder/name
   if not p.exists():continue
   value=json.loads(p.read_text());g.need(not recovery.unknown(value),'auto-port-child-unknown')
   g.need(not value.get('settling_exhausted') and (not value.get('hold') or (name=='state.json' and value.get('phase')=='normal-restored-ready' and value.get('waiting_for')=='supervisor-verify-rates-roundtrip-before-completion')),'auto-port-child-external-or-exhausted-hold')
 def result(self,b,effect,**kw):
  if 'parent' in kw:
   data=self.main.read_bytes();sha=nav.digest(self.main);snapshot=integration.location(self.m,self.v,b['notice_id']).parent/('parent-after-'+sha+'.json')
   if snapshot.exists():g.need(snapshot.read_bytes()==data,'auto-port-parent-snapshot-conflict')
   else:
    with snapshot.open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
   kw['parent']=d.ref(snapshot)
  return {'binding_sha256':integration.digest(b),'effect':effect,'route_contract':integration.route_contract(b['kind']),'arrow_issued':False,**kw}

 def stage(self,b,receipts):
  f=self.flow(b);r=self.runner(product.Runner if b['kind']=='product' else d.Runner)
  if b['kind']=='product':r.stage(nav.digest(r.file),r.s['last_observation']['sha256'])
  else:
   original=d.document(f['original_parent']);g.need(r.s==original,'auto-rates-stage-original-required');r.observe();raw=d.document(r.s['last_observation']);row=self.v['query']['rows'][b['cursor']];facts,_=parser(b['kind'])(raw,row,b['original_open'],self.v['job']);g.need(integration.digest({k:x for k,x in facts.items() if k!='observed_at'})==b['facts_sha256'],'auto-rates-stage-facts-changed');r.s['automatic_rates_stage']={'binding':b,'original_parent':f['original_parent']};r.s['current'].update(detail_observation=r.s['last_observation'],facts=facts);r.s.update(phase='auto-rates-staged',hold=True,waiting_for='automatic-owned-stage')
  if r.s.get('last_error')=='governance-path-unreviewed':r.s.pop('last_error')
  own(r,b);return self.result(b,'source-revalidated',parent=d.ref(r.file))
 def product_return_once(self,b,receipts):
  r=self.runner(product.Runner);r.return_once();own(r,b);return self.result(b,'return-intent-confirmed',parent=d.ref(r.file))
 def product_read_return(self,b,receipts):
  r=self.runner(product.Runner);r.inspect_return();raw=d.document(r.s['last_observation']);
  if urlsplit(raw['tab']['url']).path==product.PATH:
   product.parse(raw,self.v['query']['rows'][b['cursor']],b['original_open'],self.v['job']);own(r,b);return self.result(b,'pending')
  page=d.normal_page(raw['tree'],self.v['job'],self.v['query']);source=d.normal_page(d.document(r.s['current']['normal_before'])['tree'],self.v['job'],self.v['query']);g.need(page==source,'auto-product-roundtrip-not-restored');own(r,b);return self.result(b,'original-records-restored',parent=d.ref(r.file))
 def product_finish(self,b,receipts):
  r=self.runner(product.Runner)
  if r.s['cursor']==b['cursor']:r.finish_roundtrip(nav.digest(r.file))
  self.verify_completed_parent(b,r.s);r.s.pop('automatic_stop_loss_owner',None);r.save();return self.result(b,'detail-completed',parent=d.ref(r.file))
 def rates_sidebar_once(self,b,receipts):
  r=self.runner();g.need(r.s['phase']=='auto-rates-staged','auto-sidebar-original-stage-required');r.observe();raw=d.document(r.s['last_observation']);facts,_=parser(b['kind'])(raw,self.v['query']['rows'][b['cursor']],b['original_open'],self.v['job']);g.need(d.same_facts(facts,r.s['current']['facts']),'auto-sidebar-facts-changed');target=sidebar(raw,b['kind']);r.action({**g.click(target,'navigation'),'tabId':self.m['tab_id']},'auto-rates-center-pending',r.s['last_observation']);own(r,b);return self.result(b,'sidebar-intent-confirmed',parent=d.ref(r.file))
 def rates_read_center(self,b,receipts):
  r=self.runner();g.need(r.s['phase']=='auto-rates-center-pending','auto-center-original-sidebar-required');r.observe();raw=d.document(r.s['last_observation']);
  if urlsplit(raw['tab']['url']).path==rates.PATH:
   parser(b['kind'])(raw,self.v['query']['rows'][b['cursor']],b['original_open'],self.v['job']);own(r,b);return self.result(b,'pending')
  recovery.scope(raw,self.v['job'],self.m['tab_id'],g.CENTER);g.need(raw['tab']['windowId']==b['window_id'],'auto-center-window-changed');r.s.update(phase='auto-rates-center-ready',hold=True,waiting_for='automatic-owned-list-restore');own(r,b);return self.result(b,'center-observed',parent=d.ref(r.file))
 def rates_restore_lists(self,b,receipts):
  # Every recovery tick owns its existing journal; bounded waiting is propagated
  # as a read-only pending result, never a second navigation input.
  mp=self._prepare_recovery(b);folder=mp.parent
  manifest=json.loads(mp.read_text());r=recovery.Runner(manifest,folder/'state.json',self.invoke)
  for _ in range(100):
   r.step();r.save()
   if r.s['phase']=='normal-restored-ready':break
   if r.s.get('hold') or r.s.get('waiting_for'):return self.result(b,'pending',recovery_manifest=d.ref(mp))
  if r.s['phase']!='normal-restored-ready':return self.result(b,'pending',recovery_manifest=d.ref(mp))
  replay.verify_recovery(manifest,r.s);return self.result(b,'original-records-restored',recovery_manifest=d.ref(mp),recovery_state=d.ref(r.file))
 def reconcile_current_return(self,flow,parent):
  # The outer logical step may have stopped after its nested navigation returned.
  # Complete that current read frontier; this runner cannot issue any input.
  calls=flow.s.get('calls',[]);current=calls[-1]if calls else{}
  if not(current.get('state')=='unknown'and current.get('step')==flow.s.get('phase')=='rates_restore_lists'):return False
  g.need(flow.guarded_parent(parent),'auto-return-current-owner-required');b=flow.binding
  folder=integration.location(self.m,self.v,b['notice_id']).parent/'rates-recovery';mp=folder/'manifest.json'
  # Preparing this current manifest only reads settled source documents. A
  # stopped logical verifier may not have reached its first nested API call.
  if not mp.exists():mp=self._prepare_recovery(b)
  manifest=json.loads(mp.read_text())
  class ReadOnlyReturn(recovery.Runner):
   def act_once(inner,*args,**kwargs):raise ValueError('auto-return-reconciliation-requires-input-no-replay')
  def readonly(command):
   g.need(command.get('op') in ('tabs','ping','tree','readonly-scope'),'auto-return-reconciliation-input-denied')
   return self.invoke(command)
  r=ReadOnlyReturn(manifest,folder/'state.json',readonly)
  g.need(not r.unresolved(),'auto-return-nested-input-outcome-unresolved')
  if r.s.get('phase')in('center-range','center-next','center-read-two','open-records'):
   # Every nested API outcome is settled. Resume the logical step from this
   # current journal; no prior navigation or filter action is reissued.
   result=self.result(b,'pending',recovery_manifest=d.ref(mp));self.verify('rates_restore_lists',result,b,copy.deepcopy(flow.s['receipts']))
   current.update(state='confirmed',result=copy.deepcopy(result),reconciled_from_settled_current_journal=True)
   flow.s.pop('hold',None);flow.s['waiting_for']='owned-list-recovery-readonly-wait';flow.save();return True
  g.need(r.s.get('phase')in('inspect-records','restore-target-page','verify-target-page','normal-restored-ready'),'auto-return-current-read-frontier')
  for unused in range(3):
   if r.s['phase']=='normal-restored-ready':break
   g.need(r.s['phase']in('inspect-records','restore-target-page','verify-target-page'),'auto-return-reconciliation-current-read-only')
   r.step();r.save()
  g.need(r.s['phase']=='normal-restored-ready','auto-return-current-read-not-ready')
  replay.verify_recovery(manifest,r.s)
  result=self.result(b,'original-records-restored',recovery_manifest=d.ref(mp),recovery_state=d.ref(r.file));self.verify('rates_restore_lists',result,b,copy.deepcopy(flow.s['receipts']))
  current.update(state='confirmed',result=copy.deepcopy(result),reconciled_from_current_readonly_return=True);flow.s['receipts'].append(copy.deepcopy(result))
  steps=integration.STEPS[b['kind']];flow.s['phase']=steps[steps.index('rates_restore_lists')+1];flow.s.pop('hold',None);flow.s.pop('waiting_for',None);flow.save();return True
 def rates_finish(self,b,receipts):
  r=self.runner()
  if r.s['cursor']==b['cursor']+1:self.verify_completed_parent(b,r.s);return self.result(b,'detail-completed',parent=d.ref(r.file))
  previous=receipts[-1];rm=d.document(previous['recovery_manifest']);rs=d.document(previous['recovery_state']);replay.verify_recovery(rm,rs);g.need(nav.digest(self.main)==rm['parent_state']['sha256'],'auto-rates-completion-parent-changed');finalpath=Path(previous['recovery_state']['path']).parent/('final-state-'+previous['recovery_state']['sha256']+'.json')
  originalbytes=Path(previous['recovery_state']['path']).read_bytes()
  if finalpath.exists():g.need(finalpath.read_bytes()==originalbytes,'auto-direct-final-snapshot-conflict')
  else:
   with finalpath.open('xb') as out:out.write(originalbytes);out.flush();os.fsync(out.fileno())
  g.need(nav.digest(finalpath)==previous['recovery_state']['sha256'],'auto-direct-final-snapshot-hash-changed')
  r.observe();entry={'state':'complete','completion_kind':KINDS[b['kind']],'template_kind':b['kind'],'notice_id':b['notice_id'],'normal_before':r.s['current']['normal_before'],'detail_observation':r.s['current']['detail_observation'],'facts':copy.deepcopy(r.s['current']['facts']),'normal_after':r.s['last_observation'],'source_parent':rm['parent_state'],'recovery_manifest':previous['recovery_manifest'],'recovery_state':d.ref(finalpath)};verify_direct_entry(entry,r.s,self.m,self.v,self.v['query']['rows'][b['cursor']]);r.s['details'].append(entry);r.s.update(cursor=b['cursor']+1,current=None,phase='complete' if b['cursor']+1==len(self.v['query']['rows']) else 'normal');r.s.pop('hold',None);r.s.pop('waiting_for',None);r.s.pop('automatic_stop_loss_owner',None);r.save();return self.result(b,'detail-completed',parent=d.ref(r.file))
 def verify_completed_parent(self,b,parent):
  g.need(parent['cursor']==b['cursor']+1 and parent['details'][b['cursor']]['notice_id']==b['notice_id'],'auto-completion-cursor-changed');entry=parent['details'][b['cursor']];row=self.v['query']['rows'][b['cursor']]
  if b['kind']=='product':product.verify_entry(entry,parent,self.m,self.v,row)
  else:verify_direct_entry(entry,parent,self.m,self.v,row)
 def verify(self,step,result,b,receipts):
  if result['effect']=='pending':return
  parent=self.load()
  if step.endswith('finish'):self.verify_completed_parent(b,parent)
  elif step=='rates_restore_lists':replay.verify_recovery(d.document(result['recovery_manifest']),d.document(result['recovery_state']))
  else:
   g.need(result['parent']['sha256']==nav.digest(self.main) and d.document(result['parent'])==parent,'auto-port-parent-receipt-changed')
   if step=='stage':g.need(parent['current']['notice_id']==b['notice_id'] and integration.digest({k:x for k,x in parent['current']['facts'].items() if k!='observed_at'})==b['facts_sha256'],'auto-stage-source-changed')
   elif step=='product_read_return':g.need(d.normal_page(d.document(parent['last_observation'])['tree'],self.v['job'],self.v['query'])==d.normal_page(d.document(parent['current']['normal_before'])['tree'],self.v['job'],self.v['query']),'auto-product-return-effect-changed')
   elif step=='rates_read_center':direct_source(json.loads(self._prepare_recovery(b).read_text()))
   else:
    call=parent['calls'][-1];g.need(call['state']=='confirmed','auto-port-navigation-unconfirmed');d.reply_matches(call['command'],call['result'],d.document(call['before']))
 def _prepare_recovery(self,b):
  _,folder=recovery.locations(self.m,self.v);mp=folder/'manifest.json'
  if not mp.exists():
   folder.mkdir(parents=True,exist_ok=True);parentref=d.ref(self.main);snapshot=folder/('source-parent-'+parentref['sha256']+'.json');
   if snapshot.exists():g.need(snapshot.read_bytes()==self.main.read_bytes(),'auto-direct-source-snapshot-conflict')
   else:
    with snapshot.open('xb') as out:out.write(self.main.read_bytes());out.flush();os.fsync(out.fileno())
   mr=folder/'detail-manifest.json';d.exclusive(mr,self.m);manifest={'kind':MANIFESTS[b['kind']],'detail_manifest':d.ref(mr),'parent_state':d.ref(snapshot)};direct_source(manifest);d.exclusive(mp,manifest)
  manifest=json.loads(mp.read_text());g.need(manifest['parent_state']['sha256']==nav.digest(self.main),'auto-direct-live-parent-changed');direct_source(manifest);return mp
 def readonly_reconcile(self,b,s):
  r=self.runner();r.observe();return {'unknown':True,'only_read':True,'observation':r.s['last_observation'],'automatic_resume':False}

def dispatch_step(runner):
 """Future formal Runner.step hook. Caller owns the original role lock.

 Returns handled=False for ordinary details. Always reload parent after ports;
 never save the caller's stale pre-port state over an action intent/result.
 """
 m=runner.manifest;v=runner.v;main=state_path(m,v);g.need(Path(runner.file).resolve()==main,'auto-dispatch-original-role-required')
 if not main.exists():return {'handled':False}
 parent=json.loads(main.read_text());notice=(parent.get('current') or {}).get('notice_id');existing=False
 if notice:
  path=integration.location(m,v,notice);existing=path.exists()
 elif parent.get('details'):
  notice=parent['details'][-1]['notice_id'];path=integration.location(m,v,notice)
  if path.exists():existing=not json.loads(path.read_text()).get('complete')
 if not existing:
  settle=integration.settling(parent,m,v);record=parent.get('stop_loss_settle') or {'checks':0}
  if settle and record.get('checks',0)<integration.SETTLE_CHECKS:
   # One read-only observation: no click, no input, and the reader keeps every reply.
   runner.observe();parent=json.loads(main.read_text());count=record.get('checks',0)+1
   parent['stop_loss_settle']={'reason':settle,'checks':count,'last_observation':parent['last_observation'],'at':nav.stamp()}
   nav.write_json(main,parent);runner.s=parent
   return {'handled':True,'phase':parent['phase'],'settle':{'reason':settle,'checks':count},'complete':False,'business_progress_changed':False}
  if parent.pop('stop_loss_settle',None) is not None:nav.write_json(main,parent)
  if integration.detect(parent,m,v) is None:return {'handled':False}
 ports=Ports(m,runner.invoke);flow=integration.Flow(m,v,parent,ports);ports.reconcile_current_return(flow,parent);result=flow.tick(parent);runner.s=json.loads(main.read_text())
 return {'handled':True,'phase':result['phase'],'complete':result['complete'],'waiting_for':result.get('waiting_for'),'hold':result.get('hold',False),'business_progress_changed':False}

def capture_mapping(source,facts,entry,*,state,manifest,inputs):
 """Explicit direct-template source mapping; no user-facing wording rewrite."""
 g.need(verify_direct_entry(entry,state,manifest,inputs,source)==facts,'auto-capture-facts-changed');kind=entry['template_kind'];schema={'rates':('governance-noaccept-rate-stop-loss-detail-v1' if facts.get('schema')=='governance-noaccept-rate-stop-loss-detail-v1' else 'governance-three-rates-stop-loss-detail-v1'),'stock':'governance-stock-stop-loss-detail-v1'};status={'rates':(source['effective_status'] if facts.get('schema')=='governance-noaccept-rate-stop-loss-detail-v1' else '已结束'),'stock':'已撤销'}
 if kind=='rates' and facts.get('schema')=='governance-noaccept-warning-stop-loss-detail-v1':
  g.need(source['reason']=='门店不接单率超标' and source['disposal']=='特此进行警告，再次违规平台将加重处罚' and source['effective_status']=='已生效' and facts['disposals']==[source['disposal']] and facts['effective_statuses']==['已结束'] and facts['detail_period_observed'] is False,'auto-noaccept-warning-literal-mapping-required')
  ob=g.one(facts['disposal_observations'],'auto-noaccept-warning-action-not-unique');g.need(ob['text']==source['disposal'] and ob['status']=='已结束' and ob['temporal_scope']=='ended-warning' and ob['section']=='对我的影响','auto-noaccept-warning-action-evidence-changed')
  item={'action':source['disposal'],'status':ob['status'],'temporal_scope':ob['temporal_scope'],'original_text':ob['text'],'original_label':ob['section'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':ob['action_selector'],'status_selector':ob['status_selector'],'time':ob['time'],'original_time':ob['original_time'],'time_selector':ob['time_selector']}
  return {'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':[item],'disposal_stage_text':'列表：'+source['effective_status']+'；详情：'+ob['status']+'（'+ob['original_time']+'）','disposal_literal_mapping':{'method':'verified-noaccept-warning-independent-table-status-and-timepoint-v1','table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_effectiveness_status':ob['status'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'time_selector':ob['time_selector']},'detail_object_type_basis':{'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts['object_id'],'store_name':facts['store_name'],'store_id':facts['store_id'],'store_id_observed':facts.get('store_id_observed',True),'source_binding':facts['source_binding'],'observation':entry['detail_observation']},'potential_consequences_excluded_from_actions_and_client_copy':True,'metric_period_is_not_disposal_period':True}
 if kind=='operation':
  g.need(facts['schema']=='governance-operation-stop-loss-detail-v1' and facts['disposals']==[source['disposal']] and facts['effective_statuses']==['已结束'] and source['effective_status']=='已生效','auto-operation-capture-literal-mapping-required')
  ob=g.one(facts['disposal_observations'],'auto-operation-action-not-unique');g.need(ob['text']==source['disposal'] and ob['status']=='已结束' and ob['section']=='对我的影响' and ob['temporal_scope']=='ended-disposal' and facts['detail_period_observed'] is False,'auto-operation-action-evidence-changed')
  item={'action':ob['text'],'status':ob['status'],'temporal_scope':ob['temporal_scope'],'original_text':ob['text'],'original_label':ob['section'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':ob['action_selector'],'status_selector':ob['status_selector'],'time':ob['time'],'time_selector':ob['time_selector'],'original_time':ob['original_time']}
  return {'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':[item],'disposal_stage_text':ob['status']+'：'+ob['text']+'（'+ob['original_time']+'）','disposal_literal_mapping':{'method':'verified-operation-ended-detail-independent-table-status-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_effectiveness_status':ob['status'],'time_selector':ob['time_selector']},'detail_object_type_basis':{'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts['object_id'],'store_name':facts['store_name'],'store_id':facts['store_id'],'store_id_observed':facts.get('store_id_observed',True),'source_binding':facts['source_binding'],'observation':entry['detail_observation']},'business_controls_excluded_from_actions_and_client_copy':True,'notification_time_is_independent_of_disposal_time':True}
 if kind=='operation_control':
  g.need(facts['schema']=='governance-operation-control-stop-loss-detail-v1' and facts['disposals']==[o['text'] for o in facts['disposal_observations']] and facts['effective_statuses']==['已结束']*len(facts['disposals']) and source['effective_status']==('已生效'if len(facts['disposals'])==2 else'已结束') and source['disposal']=='，'.join(facts['disposals']),'auto-operation-control-capture-literal-mapping-required')
  items=[]
  for ob in facts['disposal_observations']:
   g.need(ob['text'] in source['disposal'] and ob['status']=='已结束' and ob['section']=='对我的影响' and ob['temporal_scope']=='ended-disposal','auto-operation-control-action-evidence-changed')
   items.append({'action':ob['text'],'status':ob['status'],'temporal_scope':ob['temporal_scope'],'original_text':ob['text'],'original_label':ob['section'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':ob['action_selector'],'status_selector':ob['status_selector'],'detail_time':ob['detail_time'],'detail_time_selector':ob['detail_time_selector']})
  return {'actions':facts['disposals'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':items,'disposal_stage_text':'；'.join('已结束：'+item['action']+'（'+item['detail_time']+'）' for item in items),'disposal_literal_mapping':{'method':'verified-operation-control-multi-disposal-comma-joined-list-cell-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'detail_effectiveness_status':'已结束','list_join':{'actions':facts['disposals'],'joiner':'，'}},'detail_object_type_basis':{'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts['object_id'],'store_name':facts['store_name'],'store_id':facts['store_id'],'store_id_observed':facts.get('store_id_observed',True),'source_binding':facts['source_binding'],'observation':entry['detail_observation']},'business_controls_excluded_from_actions_and_client_copy':True,'notification_time_is_independent_of_disposal_time':True}
 g.need(facts['schema']==schema[kind] and facts['disposals']==[source['disposal']] and facts['effective_statuses']==[source['effective_status']]==[status[kind]],'auto-capture-literal-mapping-required');ob=g.one(facts['disposal_observations'],'auto-capture-action-not-unique');period=facts['effective_period'];g.need(ob['text']==source['disposal'] and ob['status']==source['effective_status'] and ob['section']=='对我的影响','auto-capture-action-evidence-changed');item={'action':source['disposal'],'status':source['effective_status'],'temporal_scope':ob['temporal_scope'],'original_text':ob['text'],'original_label':ob['section'],'table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'value_selector':ob['action_selector'],'status_selector':ob['status_selector'],'period':period}
 result={'actions':[source['disposal']],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'action_details':[item],'effective_period':period,'disposal_stage_text':status[kind]+'：'+source['disposal']+'（'+period['start']+' ~ '+period['end']+'）','disposal_literal_mapping':{'method':('verified-noaccept-source-status-disposal-period-v1' if facts['schema']=='governance-noaccept-rate-stop-loss-detail-v1' else 'exact-three-rates-ended-disposal-period-v1') if kind=='rates' else 'verified-stock-revoked-disposal-period-v1','table_observation':entry['normal_before'],'detail_observation':entry['detail_observation'],'table_disposal':source['disposal'],'table_effectiveness_status':source['effective_status'],'period_selector':period['selector']}}
 result['detail_object_type_basis']={'schema':facts['schema'],'object_type':facts['object_type'],'object_id':facts.get('object_id'),'store_name':facts.get('store_name'),'store_id':facts.get('store_id'),'store_id_observed':facts.get('store_id_observed'),'source_binding':facts.get('source_binding'),'observation':entry['detail_observation']}
 if kind=='rates':result['potential_consequences_excluded_from_actions_and_client_copy']=True
 else:result['marketing_features_excluded_from_actions_and_client_copy']=True;result['notification_time_is_independent_of_effective_period']=True
 return result

def verify_owned_progress(journal_path):
 """Pure monitor proof. No Runner construction, requests, writes or input.

 Tokens describe verified named steps only. Read-only observations, changing
 parent hashes and child calendar stages deliberately do not count as progress.
 """
 main=Path(journal_path).resolve();parent=json.loads(main.read_text());m=parent['manifest'];v=d.inputs(m);g.need(main==state_path(m,v),'auto-progress-canonical-parent-required');owner=parent.get('automatic_stop_loss_owner',{});notice=(parent.get('current') or {}).get('notice_id');g.need(notice,'auto-progress-owned-current-required');fp=integration.location(m,v,notice);flow=json.loads(fp.read_text());original=d.document(flow['original_parent']);b=integration.detect(original,m,v);g.need(b is not None and flow['schema']==integration.SCHEMA and flow['binding']==b,'auto-progress-original-binding-changed');g.need(Path(flow['original_parent']['path']).resolve()==fp.parent/'original-parent.json','auto-progress-original-location-changed');g.need(owner=={'binding_sha256':integration.digest(b),'program_phase':parent['phase']},'auto-progress-owner-unverified');g.need(not integration.unknown(flow) and not recovery.unknown(parent) and not parent.get('last_error'),'auto-progress-error-or-unknown');d.verify_completed(original,m,v,require_complete=False)
 checker=object.__new__(integration.Flow);checker.m=m;checker.v=v;checker.binding=b;checker.s=flow;g.need(checker.guarded_parent(parent),'auto-progress-parent-not-owned-program-hold')
 steps=integration.STEPS[b['kind']];completed=[];index=0
 def check_parent(snapshot):
  g.need(snapshot['manifest']==m and snapshot['details']==original['details'] and snapshot['cursor']==b['cursor'] and snapshot['calls'][:len(original['calls'])]==original['calls'] and snapshot['current']['normal_before']==original['current']['normal_before'],'auto-progress-receipt-prefix-changed');facts,_=(product.parse if b['kind']=='product' else parser(b['kind']))(d.document(snapshot['current']['detail_observation']),v['query']['rows'][b['cursor']],b['original_open'],v['job']);g.need(integration.digest({k:x for k,x in facts.items() if k!='observed_at'})==b['facts_sha256'] and d.same_facts(facts,snapshot['current']['facts']),'auto-progress-facts-changed');return facts
 for call in flow['calls']:
  step=call['step'];result=call.get('result',{});g.need(call['state']=='confirmed' and index<len(steps) and step==steps[index] and result.get('binding_sha256')==integration.digest(b),'auto-progress-step-chain-changed')
  if b['kind']!='product':g.need(result.get('route_contract')==integration.route_contract(b['kind']) and result.get('arrow_issued') is False,'auto-progress-direct-contract-changed')
  if result.get('effect')=='pending':
   g.need(step in ('rates_restore_lists','rates_read_center','product_read_return'),'auto-progress-pending-step-unreviewed');continue
  g.need(result.get('effect')==integration.EFFECTS[step],'auto-progress-step-effect-changed');g.need(index<len(flow['receipts']) and result==flow['receipts'][index],'auto-progress-receipt-chain-changed')
  if step=='rates_restore_lists':replay.verify_recovery(d.document(result['recovery_manifest']),d.document(result['recovery_state']))
  else:
   pr=result['parent'];g.need(Path(pr['path']).resolve()==fp.parent/('parent-after-'+pr['sha256']+'.json'),'auto-progress-immutable-step-parent-required');snapshot=d.document(pr);check_parent(snapshot)
   if step=='stage':
    if b['kind']=='product':
     role=object.__new__(product.Runner);role.s=snapshot;role.manifest=m;role.v=v;role.job=v['job'];role.original()
    else:g.need(snapshot['automatic_rates_stage']=={'binding':b,'original_parent':flow['original_parent']},'auto-progress-stage-source-changed')
   elif step in ('product_return_once','product_read_return','rates_sidebar_once'):
    calls=snapshot['calls'][len(original['calls']):];action=g.one(calls,'auto-progress-return-call-not-unique');before=d.document(action['before']);facts,command=(product.parse if b['kind']=='product' else parser(b['kind']))(before,v['query']['rows'][b['cursor']],b['original_open'],v['job'])
    if step=='rates_sidebar_once':
     node=sidebar(before,b['kind']);command={**g.click(node,'navigation'),'tabId':m['tab_id']}
    g.need(action['command']==command and action['state']=='confirmed','auto-progress-navigation-command-changed');d.reply_matches(command,action['result'],before)
    if step=='product_read_return':g.need(d.normal_page(d.document(snapshot['last_observation'])['tree'],v['job'],v['query'])==d.normal_page(d.document(original['current']['normal_before'])['tree'],v['job'],v['query']),'auto-progress-original-list-not-restored')
   elif step=='rates_read_center':
    rm=json.loads((fp.parent/'rates-recovery/manifest.json').read_text());_,_,frozen,_=direct_source(rm);g.need(frozen==snapshot,'auto-progress-center-snapshot-changed')
   else:raise ValueError('auto-progress-completed-not-active-hold')
  completed.append(step);index+=1
 g.need(index==len(flow['receipts']) and index<len(steps) and flow['phase']==steps[index],'auto-progress-current-phase-changed')
 # Check every active recovery journal for unknown/errors/manual holds, and
 # verify saved concrete commands/replies before granting the monitor token.
 folder=fp.parent/'rates-recovery'
 for name in ('state.json','center-range.json','records-range.json'):
  childpath=folder/name
  if not childpath.exists():continue
  child=json.loads(childpath.read_text());g.need(not recovery.unknown(child) and not child.get('last_error') and not child.get('settling_exhausted'),'auto-progress-child-error-or-unknown');g.need(not child.get('hold') or (name=='state.json' and child.get('phase')=='normal-restored-ready' and child.get('waiting_for')=='supervisor-verify-rates-roundtrip-before-completion'),'auto-progress-child-manual-hold')
  g.need(child.get('fingerprint')==nav.tag(v['job']) and child.get('tab_id')==m['tab_id'] and child.get('approved_version')==nav.VERSION,'auto-progress-child-scope-changed');query_phase='open-date'
  if name=='state.json':g.need([c.get('purpose') for c in child.get('calls',[])]==['center-top10-next-page','center-records-entry','records-original-target-page'][:len(child.get('calls',[]))],'auto-progress-child-navigation-order-changed')
  for action in child.get('calls',[]):
   before=d.document(action['before']);route=urlsplit(before['tab']['url']).path;g.need(route in (g.CENTER,g.RECORDS),'auto-progress-child-route-changed');recovery.scope(before,v['job'],m['tab_id'],route);g.need(before['tab']['windowId']==b['window_id'],'auto-progress-child-window-changed');d.reply_matches(action['command'],action['result'],before)
   if name=='state.json':
    purpose=action['purpose']
    if purpose=='center-top10-next-page':expected=recovery.center.center_page(before['tree'],start=v['job']['start'],end_exclusive=v['job']['end_exclusive'])['next']
    elif purpose=='center-records-entry':expected=recovery.record_entry(before['tree'])
    else:expected=recovery.target_page_command(before['tree'],g.one([page['page'] for page in v['query']['pages'] if v['query']['rows'][b['cursor']] in page['rows']],'auto-progress-source-page-not-unique'))
   else:
    planned=g.QueryPlan(v['job']['start'],v['job']['end_exclusive']).next(before['tree'],{'phase':query_phase});expected=planned['command'];query_phase=planned['next_phase']
   g.need(action['command']=={**expected,'tabId':m['tab_id']},'auto-progress-child-command-unreviewed')
 return {'schema':'verified-automatic-stop-loss-progress-v1','binding_sha256':integration.digest(b),'notice_id':notice,'template_kind':b['kind'],'completed_steps':completed,'progress_tokens':[integration.digest({'binding':b,'step':step}) for step in completed],'ui_used':False,'owner_verified':True}

def verify_completed_progress(journal_path,notice_id):
 """Pure retirement proof preserving stable auto tokens after owner removal."""
 main=Path(journal_path).resolve();parent=json.loads(main.read_text());m=parent['manifest'];v=d.inputs(m);g.need(main==state_path(m,v),'auto-progress-canonical-parent-required');fp=integration.location(m,v,notice_id);flow=json.loads(fp.read_text());b=integration.detect(d.document(flow['original_parent']),m,v);g.need(b==flow['binding'] and b['notice_id']==notice_id and flow.get('complete') is True and flow['phase']=='complete' and not integration.unknown(flow),'auto-progress-completed-flow-unverified');entry=parent['details'][b['cursor']];g.need(entry['notice_id']==notice_id,'auto-progress-completed-notice-changed')
 if b['kind']=='product':product.verify_entry(entry,parent,m,v,v['query']['rows'][b['cursor']])
 else:verify_direct_entry(entry,parent,m,v,v['query']['rows'][b['cursor']])
 steps=integration.STEPS[b['kind']];completed=[];i=0
 for call in flow['calls']:
  result=call.get('result',{});g.need(call['state']=='confirmed' and i<len(steps) and call['step']==steps[i] and result.get('binding_sha256')==integration.digest(b),'auto-progress-completed-chain-changed')
  if b['kind']!='product':g.need(result.get('route_contract')==integration.route_contract(b['kind']) and result.get('arrow_issued') is False,'auto-progress-direct-contract-changed')
  if result.get('effect')=='pending':continue
  g.need(result==flow['receipts'][i] and result['effect']==integration.EFFECTS[steps[i]],'auto-progress-completed-receipt-changed')
  if 'parent' in result:
   pr=result['parent'];g.need(Path(pr['path']).resolve()==fp.parent/('parent-after-'+pr['sha256']+'.json'),'auto-progress-immutable-step-parent-required');d.document(pr)
  completed.append(steps[i]);i+=1
 g.need(i==len(steps)==len(flow['receipts']),'auto-progress-completed-steps-missing')
 return {'schema':'verified-automatic-stop-loss-progress-v1','binding_sha256':integration.digest(b),'notice_id':notice_id,'template_kind':b['kind'],'completed_steps':completed,'progress_tokens':[integration.digest({'binding':b,'step':step}) for step in completed],'ui_used':False,'retired_after_verified_detail_completion':True}

def can_continue_owned(runner):
 """Cheap pure CLI boundary guard, not a monitor/prefix replay on every tick."""
 try:
  m=runner.manifest;v=runner.v;main=state_path(m,v)
  if Path(runner.file).resolve()!=main or not main.exists():return False
  parent=json.loads(main.read_text())
  if parent!=runner.s or parent.get('last_error') or recovery.unknown(parent):return False
  notice=(parent.get('current') or {}).get('notice_id')
  if not notice:return False
  fp=integration.location(m,v,notice);flow=json.loads(fp.read_text());original=d.document(flow['original_parent']);b=integration.detect(original,m,v)
  if b is None or flow.get('schema')!=integration.SCHEMA or flow.get('binding')!=b or flow.get('hold') or integration.unknown(flow):return False
  if Path(flow['original_parent']['path']).resolve()!=fp.parent/'original-parent.json':return False
  if parent.get('automatic_stop_loss_owner')!={'binding_sha256':integration.digest(b),'program_phase':parent['phase']}:return False
  checker=object.__new__(integration.Flow);checker.m=m;checker.v=v;checker.binding=b;checker.s=flow
  if not checker.guarded_parent(parent):return False
  folder=fp.parent/'rates-recovery'
  for name in ('state.json','center-range.json','records-range.json'):
   path=folder/name
   if not path.exists():continue
   child=json.loads(path.read_text())
   if child.get('fingerprint')!=nav.tag(v['job']) or child.get('tab_id')!=m['tab_id'] or child.get('approved_version')!=nav.VERSION or recovery.unknown(child) or child.get('last_error') or child.get('settling_exhausted'):return False
   if child.get('hold') and not(name=='state.json' and child.get('phase')=='normal-restored-ready' and child.get('waiting_for')=='supervisor-verify-rates-roundtrip-before-completion'):return False
  return True
 except (OSError,ValueError,KeyError,TypeError):return False
