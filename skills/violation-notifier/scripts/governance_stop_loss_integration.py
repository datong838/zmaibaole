#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Isolated durable dispatch for known stop-loss templates.

No live entry point: the formal runner must supply the reviewed concrete ports.
Ports never receive an arbitrary command/URL; each method is one named step.
Historical maintenance journals are not adopted or rewritten by this module.
"""
import copy,hashlib,json
from pathlib import Path
from urllib.parse import urlsplit
import governance_detail as d
import governance_stop_loss as product
import governance_rates_stop_loss as rates
import governance_stock_stop_loss as stock

g=d.g
SCHEMA='known-stop-loss-auto-flow-v1'
DIRECT='rates-direct-sidebar-v1'
STOCK_DIRECT='stock-direct-sidebar-v1'
def route_contract(kind):return STOCK_DIRECT if kind=='stock' else DIRECT
STEPS={
 'product':('stage','product_return_once','product_read_return','product_finish'),
 'rates':('stage','rates_sidebar_once','rates_read_center','rates_restore_lists','rates_finish'),
 'operation':('stage','rates_sidebar_once','rates_read_center','rates_restore_lists','rates_finish'),
 'operation_control':('stage','rates_sidebar_once','rates_read_center','rates_restore_lists','rates_finish'),
 'stock':('stage','rates_sidebar_once','rates_read_center','rates_restore_lists','rates_finish'),
}
# These are intentionally semantic effects, not a confirmed-input==success flag.
EFFECTS={'stage':'source-revalidated','product_return_once':'return-intent-confirmed',
 'product_read_return':'original-records-restored','product_finish':'detail-completed',
 'rates_sidebar_once':'sidebar-intent-confirmed','rates_read_center':'center-observed',
 'rates_restore_lists':'original-records-restored','rates_finish':'detail-completed'}

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def unknown(s):
 if s.get('manifest',{}).get('kind')=='governance-detail-inspection-manifest-v1':return bool(d.unresolved_detail_calls(s))
 return any(c.get('state')=='unknown' for c in s.get('calls',[]))
def location(m,v,notice):
 parent=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/d.nav.tag(v['job'])
 return parent/'automatic-stop-loss'/hashlib.sha256(notice.encode()).hexdigest()/'state.json'

SETTLE_CHECKS=3
# The reviewed control template renders its 门店信息 block after the route settles: a capture
# taken inside that window shows the whole reviewed skeleton without the block. Only that
# exact skeleton may authorize a read-only re-observation; every other shape stays an
# unreviewed-template question, so nothing here converts a real mismatch into a wait.
CONTROL_TITLE_TEXT='门店经营异常管控'
CONTROL_SECTIONS=('我存在什么问题','对我的影响','我该如何避免')
CONTROL_STORE_CLASSES={'wrapper-zPANxR','my-[12px]'}
def rendering_state(raw):
 if raw.get('source')!='local-dom-bridge' or raw.get('not_business_capture') is not True:return None
 tree=raw.get('tree') or {}
 if tree.get('truncated') is not False or urlsplit(tree.get('url') or '').path!=product.PATH:return None
 ns=list(g.nodes(tree));texts={g.text(n) for n in ns if not n.get('children')}
 if CONTROL_TITLE_TEXT not in texts or not set(CONTROL_SECTIONS)<=texts:return None
 if any(CONTROL_STORE_CLASSES<=g.cls(n) for n in ns):return None
 return 'operation-control-store-block-not-rendered'
def settling(parent,m,v):
 """Read-only re-observation eligibility; same source preconditions as detect()."""
 if parent.get('last_error') not in (None,'governance-path-unreviewed'):return None
 if parent.get('phase')!='read-detail' or parent.get('hold') or parent.get('waiting_for') or unknown(parent):return None
 if 'stop_loss_route_recovery' in parent:return None
 row=v['query']['rows'][parent['cursor']]
 if (parent.get('current') or {}).get('notice_id')!=row['notice_id']:return None
 return rendering_state(d.document(parent['last_observation']))

def detect(parent,m,v):
 """Pure source check. Only a confirmed original open at read-detail is eligible."""
 if parent.get('last_error') not in (None,'governance-path-unreviewed'):return None
 if parent.get('phase')!='read-detail' or parent.get('hold') or parent.get('waiting_for') or unknown(parent):return None
 if 'stop_loss_route_recovery' in parent:
  import stop_loss_route_recovery as route_recovery
  route_recovery.verify_continuation(parent)
 row=v['query']['rows'][parent['cursor']];current=parent['current'];g.need(current['notice_id']==row['notice_id'] and parent['cursor']==len(parent['details']),'stop-auto-source-cursor-changed')
 raw=d.document(parent['last_observation']);path=urlsplit(raw['tab']['url']).path
 if path!=product.PATH:return None
 opening=parent['calls'][-1];g.need(opening['state']=='confirmed' and opening['before']==current['normal_before'],'stop-auto-original-open-unconfirmed');d.reply_matches(opening['command'],opening['result'],d.document(opening['before']))
 # Both observed templates share a route. Their independently strict parsers
 # distinguish the exact query/DOM/source bindings; unknown shapes stay errors.
 matches=[];parsers=[('product',product.parse),('rates',rates.parse),('stock',stock.parse),('operation',rates.parse_operation),('operation_control',rates.parse_operation_control)]
 for kind,parser in parsers:
  try:facts,command=parser(raw,row,opening,v['job'])
  except (ValueError,KeyError):continue
  matches.append((kind,facts,command))
 kind,facts,command=g.one(matches,'stop-auto-known-template-not-unique')
 window=d.document(current['normal_before'])['tab']['windowId'];g.need(raw['tab_id']==m['tab_id'] and raw['tab'].get('windowId')==window,'stop-auto-window-changed')
 return {'kind':kind,'notice_id':row['notice_id'],'cursor':parent['cursor'],'tab_id':m['tab_id'],'window_id':window,'groupid':v['job']['groupid'],'fingerprint':d.nav.tag(v['job']),'manifest_sha256':digest(m),'query':m['inputs']['query'],'source_observation':parent['last_observation'],'original_open':copy.deepcopy(opening),'prefix_sha256':digest(parent['details']),'calls_prefix_sha256':digest(parent['calls']), 'original_call_count':len(parent['calls']),'facts_sha256':digest({k:x for k,x in facts.items() if k!='observed_at'}),'rates_route':route_contract(kind) if kind in ('rates','stock','operation','operation_control') else None}

class Flow:
 """One durable semantic step per tick; concrete ports are deliberately injected.

 A port receives immutable binding and prior receipts, rechecks the fresh source,
 persists native action intent in its original owner journal, and returns only
 after its source-specific verifier passes. Unknown exceptions lock this flow;
 reconcile() is exclusively read-only and can never resume an unknown input.
 """
 def __init__(self,m,v,parent,ports,path=None):
  self.m=m;self.v=v;self.ports=ports
  notice=(parent.get('current') or {}).get('notice_id')
  if notice is None and parent.get('details'):notice=parent['details'][-1]['notice_id']
  g.need(notice,'stop-auto-current-notice-required');expected=location(m,v,notice).resolve();self.path=Path(path or expected).resolve();g.need(self.path==expected,'stop-auto-canonical-path-required')
  if self.path.exists():
   self.s=json.loads(self.path.read_text());g.need(self.s.get('schema')==SCHEMA,'stop-auto-schema-invalid');self.binding=self.s['binding'];original=d.document(self.s['original_parent']);g.need(detect(original,m,v)==self.binding,'stop-auto-original-source-required')
   self.guarded_parent(parent)
  else:
   self.binding=detect(parent,m,v);g.need(self.binding is not None,'stop-auto-not-eligible');self.path.parent.mkdir(parents=True,exist_ok=True)
   source=self.path.parent/'original-parent.json'
   if source.exists():g.need(json.loads(source.read_text())==parent,'stop-auto-original-snapshot-conflict')
   else:d.exclusive(source,parent)
   self.s={'schema':SCHEMA,'binding':self.binding,'original_parent':d.ref(source),'phase':STEPS[self.binding['kind']][0],'calls':[],'receipts':[],'complete':False};d.exclusive(self.path,self.s)
 def save(self):d.nav.write_json(self.path,self.s)
 def guarded_parent(self,parent):
  b=self.binding;g.need(parent.get('manifest')==self.m and digest(parent['details'][:b['cursor']])==b['prefix_sha256'],'stop-auto-parent-source-changed')
  if parent['cursor']==b['cursor']+1:
   g.need(self.s['phase'] in ('product_finish','rates_finish','complete') and len(parent['details'])==parent['cursor'] and parent['details'][-1]['notice_id']==b['notice_id'],'stop-auto-unexpected-completion');self.ports.verify_completed_parent(b,parent);return True
  g.need(parent['cursor']==len(parent['details'])==b['cursor'] and parent['current']['notice_id']==b['notice_id'],'stop-auto-parent-source-changed')
  original=d.document(self.s['original_parent']);g.need(parent['calls'][:len(original['calls'])]==original['calls'] and parent['current']['normal_before']==original['current']['normal_before'],'stop-auto-original-open-changed')
  if parent.get('last_error') not in (None,'governance-path-unreviewed') or unknown(parent):return False
  if parent.get('hold') or parent.get('waiting_for'):
   owner=parent.get('automatic_stop_loss_owner',{});return owner=={'binding_sha256':digest(b),'program_phase':parent['phase']} and parent['phase'] in ('stop-loss-staging','stop-loss-return-ready','stop-loss-return-route-hold','auto-rates-staged','auto-rates-center-pending','auto-rates-center-ready') and parent.get('waiting_for') in ('stop-loss-readonly-stage','supervisor-reviewed-single-stop-loss-return','supervisor-review-observed-return-route','automatic-owned-stage','automatic-owned-list-restore')
  return True
 def tick(self,parent):
  if self.s['complete']:return copy.deepcopy(self.s)
  # A finish can commit the verified local detail before its outer receipt is
  # saved. Reconcile only that local commit; never repeat a browser operation.
  if parent['cursor']==self.binding['cursor']+1 and self.s['phase'] in ('product_finish','rates_finish'):
   self.guarded_parent(parent);self.ports.verify_completed_parent(self.binding,parent)
   g.need(self.s['calls'] and self.s['calls'][-1]['step']==self.s['phase'] and self.s['calls'][-1]['state']=='unknown','stop-auto-finish-original-intent-required')
   result=getattr(self.ports,self.s['phase'])(copy.deepcopy(self.binding),copy.deepcopy(self.s['receipts']));self.ports.verify(self.s['phase'],result,self.binding,copy.deepcopy(self.s['receipts']));g.need(result.get('effect')=='detail-completed' and result.get('binding_sha256')==digest(self.binding),'stop-auto-finish-reconciliation-unverified');self.s['calls'][-1].update(state='confirmed',result=result,reconciled_from_verified_local_completion=True);self.s['receipts'].append(result);self.s.update(phase='complete',complete=True);self.s.pop('hold',None);self.s.pop('waiting_for',None);self.save();return copy.deepcopy(self.s)
  if not self.guarded_parent(parent) or self.s.get('hold') or unknown(self.s):return copy.deepcopy(self.s)
  step=self.s['phase'];g.need(step in STEPS[self.binding['kind']],'stop-auto-step-unreviewed')
  # Global nested guards belong to the port: parent + child + action unknowns.
  self.ports.assert_source(self.binding,copy.deepcopy(self.s))
  call={'step':step,'state':'unknown','intent_at':d.nav.stamp(),'binding_sha256':digest(self.binding)};self.s['calls'].append(call);self.save()
  try:
   result=getattr(self.ports,step)(copy.deepcopy(self.binding),copy.deepcopy(self.s['receipts']))
   self.ports.verify(step,result,self.binding,copy.deepcopy(self.s['receipts']))
   g.need(result.get('binding_sha256')==digest(self.binding),'stop-auto-port-binding-unverified')
   if self.binding['kind'] in ('rates','stock','operation','operation_control'):g.need(result.get('route_contract')==route_contract(self.binding['kind']) and result.get('arrow_issued') is False,'stop-auto-rates-arrow-forbidden')
   if result.get('effect')=='pending':
    g.need(step in ('rates_restore_lists','rates_read_center','product_read_return'),'stop-auto-unreviewed-pending-step');call.update(state='confirmed',result=copy.deepcopy(result));self.s['waiting_for']='owned-list-recovery-readonly-wait';self.save();return copy.deepcopy(self.s)
   g.need(result.get('effect')==EFFECTS[step] and result.get('binding_sha256')==digest(self.binding),'stop-auto-port-effect-unverified')
   if self.binding['kind'] in ('rates','stock','operation','operation_control'):g.need(result.get('route_contract')==route_contract(self.binding['kind']) and result.get('arrow_issued') is False,'stop-auto-rates-arrow-forbidden')
  except Exception:
   self.s.update(hold=True,waiting_for='stop-auto-step-outcome-readonly-reconciliation');self.save();raise
  self.s.pop('waiting_for',None);call.update(state='confirmed',result=copy.deepcopy(result));self.s['receipts'].append(copy.deepcopy(result));steps=STEPS[self.binding['kind']];i=steps.index(step)
  if i+1==len(steps):self.s.update(phase='complete',complete=True)
  else:self.s['phase']=steps[i+1]
  self.save();return copy.deepcopy(self.s)
 def reconcile(self):
  """No key clearing, no phase advance, no inputs, even if normal route returned."""
  if unknown(self.s):return self.ports.readonly_reconcile(self.binding,copy.deepcopy(self.s))
  return {'unknown':False,'ui_used':False}
