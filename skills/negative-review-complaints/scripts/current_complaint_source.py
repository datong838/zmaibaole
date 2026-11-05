"""Complaint input reuses the current daily file; live normal UI is still required."""
import hashlib,json
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import complaint_execution_order as o
KIND='current-daily-reuse-source-v1'
def verify(receipt,job):
 import daily_orchestration
 facts=daily_orchestration.verified_collection_ready_facts(receipt['daily_ready'])
 ready=facts['ready'];batch=o.doc(ready['batch'])
 entries=[c for c in ready['companies']if c['company']==job['company']and str(c['groupid'])==str(job['groupid'])]
 o.need(len(entries)==1,'complaint-current-source-company');entry=entries[0]
 if receipt.get('pending_recheck'):
  binding=receipt['pending_recheck'];ledger=o.doc(binding['ledger']);o.need(ledger['company']==job['company']and str(ledger['groupid'])==str(job['groupid']),'complaint-recheck-ledger-company')
  o.need(bool(binding['keys'])and len(binding['keys'])==len(binding['snapshots']),'complaint-recheck-current-keys')
  for key,snapshot_ref in zip(binding['keys'],binding['snapshots']):
   task=ledger['tasks'][key];o.need(task['status']=='existing_pending'and task['latest_snapshot']==snapshot_ref,'complaint-recheck-current-pending-task')
   snapshot=o.doc(snapshot_ref);authority=snapshot['authority_binding']
   o.need(snapshot['company']==job['company']and str(snapshot['groupid'])==str(job['groupid'])and snapshot['identity']==job['identity'],'complaint-recheck-source-identity')
   o.need(snapshot['start']<=job['start']<job['end_exclusive']<=snapshot['end_exclusive']and authority['source_path']==receipt['source']and authority['source_sha256']==receipt['src_sha256'],'complaint-recheck-named-source-range')
  o.need(o.ref(receipt['source'])=={'path':receipt['source'],'sha256':receipt['src_sha256']}and receipt['download_verified']is False and receipt['source_is_authoritative_export']is False,'complaint-recheck-source-bytes')
  o.need(batch['company_identities'][str(job['groupid'])]==job['identity']==receipt['identity']==receipt['identity_before'],'complaint-recheck-live-config-identity')
  return True
 o.need(entry['start']<=job['start']<job['end_exclusive']<=entry['end_exclusive'],'complaint-current-source-range')
 o.need(receipt['source']==entry['source']['path']and receipt['src_sha256']==entry['source']['sha256']and o.ref(receipt['source'])==entry['source'],'complaint-current-source-bytes')
 o.need(receipt['parent_range']=={'start':entry['start'],'end_exclusive':entry['end_exclusive']}and batch['company_identities'][str(job['groupid'])]==job['identity']==receipt['identity']==receipt['identity_before'],'complaint-current-source-identity')
 o.need(receipt['download_verified']is False and receipt['source_is_authoritative_export']is False,'complaint-reused-source-not-new-download')
 return True

def prepare(order,company,unit,folder):
 import daily_orchestration,authoritative_join as authority
 facts=daily_orchestration.verified_collection_ready_facts(order['daily_collection_ready']);ready=facts['ready'];batch=o.doc(ready['batch'])
 entry=next(c for c in ready['companies']if c['company']==company['company']);identity=batch['company_identities'][company['groupid']]
 pending=None
 if unit.get('kind')=='recheck':
  ledger=o.doc(company['ledger']);snapshots=[ledger['tasks'][key]['latest_snapshot']for key in unit['keys']];snapshot=o.doc(snapshots[0]);source_binding=snapshot['authority_binding']
  entry={**entry,'source':{'path':source_binding['source_path'],'sha256':source_binding['source_sha256']},'start':snapshot['start'],'end_exclusive':snapshot['end_exclusive']}
  pending={'ledger':company['ledger'],'keys':unit['keys'],'snapshots':snapshots}
 source=Path(entry['source']['path']);key=o.digest({'dispatch':order['dispatch_id'],'company':company['company'],'unit':unit,'source':entry['source']})
 path=Path(folder)/'current-source.json'
 job={'company':company['company'],'groupid':company['groupid'],'start':unit['start'],'end_exclusive':unit['end_exclusive'],'account_verified':True,'identity':identity,'source_work_order_id':key,'source_receipt':str(path)}
 receipt={'kind':KIND,'company':company['company'],'groupid':company['groupid'],'work_order_id':key,'date_range':{'start':unit['start'],'end':(date.fromisoformat(unit['end_exclusive'])-timedelta(days=1)).isoformat()},'parent_range':{'start':entry['start'],'end_exclusive':entry['end_exclusive']},'daily_ready':order['daily_collection_ready'],'source':str(source),'src_sha256':entry['source']['sha256'],'bytes':source.stat().st_size,'account_verified':True,'identity':identity,'identity_before':identity,'backend':'local-dom-bridge','download_verified':False,'source_is_authoritative_export':False,'recorded_at':datetime.now(timezone.utc).isoformat()}
 if pending:receipt['pending_recheck']=pending
 if path.exists():receipt=o.doc(o.ref(path))
 verify(receipt,job);rows,_=authority.load_export(source,job,receipt);receipt['page_filtered']=len(rows)
 reference=o.immutable(path,receipt);job['source_receipt_sha256']=reference['sha256'];return job,reference
