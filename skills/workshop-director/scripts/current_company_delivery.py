"""Deliver a completed company from current original tasks, independently.
Uses the original sender and business keys. Never advances collection cursors.
"""
import argparse,fcntl,json,sqlite3,sys
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parents[3]
for name in ('daily-comment-stats','workshop-director'):
 sys.path.insert(0,str(ROOT/'skills'/name/'scripts'))
import collection_ready as c,current_daily_ready,unified_delivery as delivery
import notification_backlog,unified_review_format as formatter,delivery_targets

def build(company,day):
 db=sqlite3.connect(ROOT/'runtime/standalone-workshop-director/queue.sqlite3');db.row_factory=sqlite3.Row
 tasks={r['flow']:{**dict(r),'context':json.loads(r['context'])}for r in db.execute('select * from tasks where day=?',(day,))};db.close()
 c.need(set(tasks)=={'daily-comment-stats','negative-review-complaints','violation-notifier'},'company-original-three-tasks')
 c.need(len({t['plan_id']for t in tasks.values()})==1,'company-original-plan')
 daily_ref=tasks['daily-comment-stats']['context']['collection_ready_receipt']['report'];daily=current_daily_ready.facts(daily_ref)
 complaint_ref=tasks['negative-review-complaints']['context']['collection_ready_receipt']['report'];complaint=c.doc(complaint_ref);c.need(complaint.get('collection_ready')is True,'company-complaint-not-ready')
 order_ref=tasks['violation-notifier']['context']['order'];order=c.doc(order_ref);folder=ROOT/'runtime/workshop-director/role-executions'/Path(order_ref['path']).stem;engine=c.doc(c.ref(folder/'engine.json'))
 index=next(i for i,x in enumerate(order['companies'])if x['company']==company);scope=order['companies'][index];state=engine['companies'][index];c.need(state.get('phase')=='ready','company-violation-not-ready');a=state['artifacts']
 c.need(engine['order']==order_ref and order['day']==day and not scope['skipped'],'company-original-engine')
 violation_ledger=c.doc(a['ledger_current']);batch=violation_ledger['batches'][a['batch']];c.need(not batch.get('completed_at'),'company-already-committed')
 source=c.doc(a['source']);c.need((source['company'],str(source['groupid']),source['start'],source['end_exclusive'])==(company,scope['groupid'],scope['start'],scope['end_exclusive']),'company-violation-scope')
 with c.role_modules('violation-notifier')as modules:
  ports=modules['violation_execution_ports'];ports.capture.validate(a['source']['path'])
  if batch['total']:native_violation=modules['workflow'].send_orders(violation_ledger,a['batch'])
  else:
   zero=ports._zero_notice_module();native_violation=[zero.prepare(folder/'companies'/str(index)/'zero-result-notice','violation-notifier',company,scope['start'],scope['end_exclusive'],order_ref,[a['source']],module_ref=ports._ZERO_NOTICE_MODULE)]
 current=next(x for x in daily['ready']['companies']if x['company']==company);c.need(current['groupid']==scope['groupid'],'company-gid-mismatch')
 start,end=current['start'],current['end_exclusive'];last=(date.fromisoformat(end)-timedelta(days=1)).isoformat();round_key=tasks['daily-comment-stats']['plan_id']+':'+day
 out=ROOT/'runtime/workshop-director/company-delivery'/delivery.digest({'round_key':round_key,'company':company});items=[]
 mapping=next(x for x in notification_backlog.batch_mapping(c.doc(daily['ready']['batch']))[0]if x['company']==company)
 import execution_timing as timing
 profile=timing.company_delivery_profile(daily['order'].get('active_company_policy'),company,scope['groupid'],mapping['wecom_group']);brand=profile['brand']if profile else notification_backlog.pn.BRANDS.get(company)or mapping['wecom_group']
 copy=c.doc(batch['copy_evidence'])if batch['total']else None
 text=formatter.render(delivery.daily_review_facts(current),brand,mapping['wecom_group'],'online',violation_summary=formatter.violation_brief(source,a['source']['sha256'],copy))
 key='unified-review:'+delivery.digest({'round_key':round_key,'company':company,'groupid':scope['groupid'],'start':start,'end_exclusive':end})[:48]
 for i,body in enumerate(notification_backlog.pn.chunks(text),1):
  heading='评价日报｜'+company+'｜'+start+'～'+last;message=('【%s %d/%d】\n'%(heading,i,len(notification_backlog.pn.chunks(text))) if i>1 else '')+body;itemkey=key+':%03d'%i;payload=c.immutable(out/'texts'/(delivery.digest(itemkey)+'.txt'),message.encode());items.append({'key':itemkey,'kind':'group','target':delivery_targets.target('daily-comment-stats'),'scope':'test','type':'text','payload':payload})
 for part,refs in (('detail',current['detail']),('stats',current['statistics'])):
  c.need(len(refs)==1,'company-exact-daily-file');r=refs[0];items.append({'key':'daily-comments:'+company+':'+start+':'+last+':'+part,'kind':'group','target':delivery_targets.target('daily-comment-stats'),'scope':'test','type':'file','payload':{k:r[k]for k in ('path','sha256')}})
 def native(item):
  typ=item['type'];r={'path':item['file'if typ=='file'else'text_file'],'sha256':item['file_sha256'if typ=='file'else'text_sha256']};c.raw(r);return {'key':item['key'],'kind':item['kind'],'target':item['target'],'scope':item['scope'],'type':typ,'payload':r}
 complaint_engine=c.doc(complaint['engine_archive']);complaint_order=c.doc(complaint['order']);ci=next(i for i,x in enumerate(complaint_order['companies'])if x['company']==company);complaint_company=complaint_order['companies'][ci];complaint_state=complaint_engine['companies'][ci];complaint_ledger=c.doc(next(x['archive']for x in complaint['ledgers']if x['company']==company));keys=list(dict.fromkeys(k for unit in complaint_state['artifacts']['completed_units']for k in unit.get('keys',[])));new_count=next(x['count']for x in complaint['companies']if x['company']==company)
 complaint_text=formatter.complaint_summary(company,complaint_company['start'],complaint_company['end_exclusive'],new_count,complaint_ledger,keys)
 if complaint_text:
  base='unified-complaint:'+delivery.digest({'round_key':round_key,**{k:complaint_company[k]for k in('company','groupid','start','end_exclusive')}})[:48];parts=notification_backlog.pn.chunks(complaint_text);heading='差评投诉流程｜'+company+'｜'+complaint_company['start']+'～'+(date.fromisoformat(complaint_company['end_exclusive'])-timedelta(days=1)).isoformat()
  for index,body in enumerate(parts,1):
   itemkey=base+':%03d'%index;message=('【%s %d/%d】\n'%(heading,index,len(parts))if index>1 else'')+body;payload=c.immutable(out/'texts'/(delivery.digest(itemkey)+'.txt'),message.encode());items.append({'key':itemkey,'kind':'group','target':delivery_targets.target('negative-review-complaints'),'scope':'test','type':'text','payload':payload})
 for item in c.doc(complaint['delivery_plan'])['orders']:
  if item['company']==company:
   selected=item['order']
   if item.get('image_sha256'):selected={**selected,'type':'file','file_sha256':item['image_sha256']}
   if item.get('collection_workbook'):
    import current_complaint_workbook
    complaint_engine=c.doc(complaint['engine_archive']);complaint_order=c.doc(complaint['order']);ci=next(i for i,x in enumerate(complaint_order['companies'])if x['company']==company);ledger=c.doc(next(x['archive']for x in complaint['ledgers']if x['company']==company));selected=current_complaint_workbook.delivery_order(selected,complaint_order['companies'][ci],complaint_engine['companies'][ci],ledger)
   items.append(native(selected))
 items.extend(native(item)for item in native_violation)
 target=delivery_targets.target('daily-comment-stats');c.need(all(i['target']==target for i in items),'company-recipient-mismatch')
 for item in items:
  delivery.sender_job(item);path=delivery.sender_path(item,ROOT/'runtime/wecom-messenger')
  if path.exists():
   prior=delivery.confirmed(item,ROOT/'runtime/wecom-messenger');item.update(preconfirmed_client=prior,prior_client_evidence=prior)
 plan={'kind':'current-company-client-delivery-v1','company':company,'day':day,'round_key':round_key,'scope':[[x[k]for k in ('company','groupid','start','end_exclusive')]for x in sorted(daily['ready']['companies'],key=lambda x:x['company'])],'items':items,'current_inputs':{'daily':daily_ref,'complaint':complaint_ref,'violation_order':order_ref,'violation_source':a['source'],**({'violation_chain':a['chain']}if a.get('chain')else{}),'violation_ledger':a['ledger_current']},'cursor_advanced':False}
 return out,c.immutable(out/'current-batch.json',c.encode(plan)),plan

def output_path(company,day):
 db=sqlite3.connect(ROOT/'runtime/standalone-workshop-director/queue.sqlite3')
 row=db.execute("select plan_id from tasks where day=? and flow='daily-comment-stats'",(day,)).fetchone();db.close();c.need(row is not None,'company-original-task')
 return ROOT/'runtime/workshop-director/company-delivery'/delivery.digest({'round_key':row[0]+':'+day,'company':company})

def current_plan(company,day):
 out=output_path(company,day);path=out/'current-batch.json'
 if not path.exists():return build(company,day)
 reference=c.ref(path);plan=c.doc(reference);c.need(plan['kind']=='current-company-client-delivery-v1'and plan['company']==company and plan['day']==day,'company-current-plan')
 for value in plan['current_inputs'].values():c.raw(value)
 for item in plan['items']:
  c.need(item['target']==delivery_targets.target('daily-comment-stats'),'company-current-recipient');delivery.sender_job(item)
 return out,reference,plan

def send_plan(out,reference,plan):
 receipts=[]
 for index,item in enumerate(plan['items']):
  part=out/'current-items'/str(index).zfill(4);result=part/'item-result.json'
  if result.exists():receipt=delivery.confirmed(item,ROOT/'runtime/wecom-messenger',c.doc(c.ref(result))['client'])
  else:receipt=delivery._send_item(reference,index,part,sender_directory=ROOT/'runtime/wecom-messenger',checked_plan=plan)
  receipts.append(receipt);print(json.dumps({'company':plan['company'],'confirmed_item':index+1,'items':len(plan['items']),'client':receipt},ensure_ascii=False),flush=True,file=sys.stderr)
 final=c.immutable(out/'current-all-clients-confirmed.json',c.encode({'kind':'current-company-clients-confirmed-v1','batch':reference,'clients':receipts,'cursor_advanced':False}));print(json.dumps({'company_delivery_confirmed':final},ensure_ascii=False),flush=True,file=sys.stderr)
 return final

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--company',required=True);ap.add_argument('--day',required=True);ap.add_argument('--send',action='store_true');args=ap.parse_args()
 resource=ROOT/'runtime/workshop-director/browser-wecom.resource.lock'
 with resource.open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);out,reference,plan=current_plan(args.company,args.day)
  print(json.dumps({'plan':reference,'items':len(plan['items']),**({'first_text':c.raw(plan['items'][0]['payload']).decode()}if not args.send else{})},ensure_ascii=False),flush=True)
  if not args.send:return
  send_plan(out,reference,plan)
if __name__=='__main__':main()
