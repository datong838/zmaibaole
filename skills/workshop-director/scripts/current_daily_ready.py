"""Daily ready handoff from the current sealed result, without parent replay."""
import json
from pathlib import Path
from collection_ready import doc,ref,raw,need,immutable,encode
CONTRACT='three-flow-collection-ready-v1'

def facts(report_ref):
 report=doc(report_ref);need(report.get('kind')=='daily-director-collection-ready-report-v1','current-ready-report-kind')
 order=doc(report['order']);ready=doc(report['ready'])
 need(report['workflow']==order['workflow']=='daily-comment-stats' and report['collection_contract']==order['collection_contract']==CONTRACT,'current-ready-workflow')
 need(report['day']==order['day'] and report['dispatch_id']==order['dispatch_id'] and report['scope_sha256']==order['scope_sha256'],'current-ready-original-order')
 need(ready.get('kind')=='daily-collection-ready-v1'and ready.get('collection_ready')is True and ready.get('sender_invoked')is False and ready.get('delivery_complete')is False and ready.get('cursor_advanced')is False,'current-ready-stage')
 need(report.get('collection_ready')is True and report.get('complete')is False and report.get('delivery_complete')is False and report.get('cursor_advanced')is False,'current-report-stage')
 expected={(r['company'],str(r['groupid']),r['start'],r['end_exclusive'])for r in order['scope']['company_ranges']}
 actual={(r['company'],str(r['groupid']),r['start'],r['end_exclusive'])for r in ready['companies']}
 need(bool(expected)and actual==expected,'current-ready-company-date-scope')
 batch=doc(ready['batch']);need(batch['dispatch_scope']['work_order']==report['order']and batch['status']=='complete','current-ready-batch-original-order')
 for c in ready['companies']:
  receipt=doc(c['receipt']);need(receipt['company']==c['company']and receipt['status']in('complete','zero_rows')and receipt.get('attribution_verified')is True and receipt.get('warnings')==[]and receipt.get('mismatch')is False,'current-ready-company-result')
  for reference in [c['source'],*c['detail'],*c['statistics']]:raw({k:reference[k]for k in ('path','sha256')})
 return {'report':report,'ready':ready,'order':order}

def build_report(order_ref,coordinator_root,out):
 import notification_backlog as backlog
 order=doc(order_ref);ready_path=Path(order_ref['path']).parent.parent/'daily-executions'/Path(order_ref['path']).stem/'collection-ready.json';ready_ref=ref(ready_path)
 # One producer seal checks the current batch, outputs and reserved progress.
 backlog.verify_collection_ready(ready_ref)
 director=Path(coordinator_root)/'state.json';state=json.loads(director.read_bytes())
 need(state['day']==order['day']and state['dispatch_id']==order['dispatch_id']and state['phase']in('running','attention'),'current-ready-dispatch-owner')
 report={'kind':'daily-director-collection-ready-report-v1','reader':'current-results-v1','workflow':'daily-comment-stats','collection_contract':CONTRACT,'order':order_ref,'day':order['day'],'dispatch_id':order['dispatch_id'],'scope_sha256':order['scope_sha256'],'ready':ready_ref,'collection_ready':True,'complete':False,'delivery_complete':False,'cursor_advanced':False}
 result=immutable(Path(out),encode(report));facts(result);return result
