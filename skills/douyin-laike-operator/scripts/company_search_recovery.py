#!/usr/bin/env python3
"""Pure exact-SHA reconciliation of the observed search-modal loading error."""
import argparse,copy,fcntl,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
from role_cli import validate_job,write_json
from company_search_wait import pending
KIND='verified-company-search-loading-recovery-v1'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def read(r):
 p=Path(r['path']);raw=p.read_bytes()
 if sha(raw)!=r['sha256']:raise ValueError('search-recovery-evidence-changed')
 return json.loads(raw)
def immutable(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 try:
  with p.open('xb') as f:f.write(raw)
 except FileExistsError:
  if p.read_bytes()!=raw:raise ValueError('search-recovery-archive-conflict')
def contract(job,state,tree,job_path):
 validate_job(job)
 if job.get('action')!='return-company' or job.get('navigation_only') is not True or any(job.get(k) is not False for k in ('progress_updates_enabled','export_enabled','send_enabled')):raise ValueError('search-recovery-navigation-only-required')
 if Path(job.get('work_order_path','')).resolve()!=Path(job_path).resolve() or not Path(job['workflow_path']).is_absolute():raise ValueError('search-recovery-canonical-order-required')
 fingerprint=sha(json.dumps({k:job.get(k) for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode())
 if state.get('backend')!='local-dom-bridge' or state.get('fingerprint')!=fingerprint or state.get('work_order_id')!=job['work_order_id'] or state.get('company')!=job['company'] or state.get('groupid')!=str(job['groupid']) or state.get('date_range')!={}:raise ValueError('search-recovery-work-order-conflict')
 error=state.get('last_error',{})
 if error.get('code')!='semantic-locator-not-unique' or error.get('message')!='semantic-locator-not-unique':raise ValueError('search-recovery-exact-error-required')
 fresh=copy.deepcopy(state);fresh.pop('last_error')
 if not pending(tree,job,fresh):raise ValueError('search-recovery-exact-loading-required')
 activations=[c for c in state['calls'] if c.get('command',{}).get('op')=='activate']
 if activations:
  url=activations[-1].get('result',{}).get('url','')
  if tree.get('url')!=urlsplit(url)._replace(query='',fragment='').geturl():raise ValueError('search-recovery-original-route-conflict')
 return error

def verify_recovered(current,proof_ref):
 proof=read(proof_ref)
 if proof.get('kind')!=KIND:raise ValueError('search-recovery-proof-kind')
 original=read(proof['original_journal']);job=read(proof['original_job']);tree=read(proof['original_tree'])
 error=contract(job,original,tree,proof['original_job_path'])
 if original.get('last_tree')!=proof.get('canonical_tree') or read(proof['canonical_tree'])!=tree:raise ValueError('search-recovery-original-tree-conflict')
 if datetime.fromisoformat(proof['reconciled_at']).utcoffset() is None:raise ValueError('search-recovery-aware-time-required')
 expected=copy.deepcopy(original);expected.pop('last_error');expected['company_search_loading_recovery']={'kind':KIND,'proof':proof_ref}
 if current!=expected or error!=proof.get('original_error') or original['calls']!=proof.get('original_calls'):raise ValueError('search-recovery-delta-conflict')
 return {'kind':KIND,'original_journal':proof['original_journal'],'proof':proof_ref,'original_error':error}

def reconcile(order_path,original_sha):
 order_path=Path(order_path).resolve();jobraw=order_path.read_bytes();job=json.loads(jobraw);file=Path(job['workflow_path'])
 with file.with_name('.bridge-execution.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);raw=file.read_bytes()
  if sha(raw)!=original_sha:raise ValueError('search-recovery-original-sha-conflict')
  original=json.loads(raw);tree=read(original['last_tree']);error=contract(job,original,tree,order_path)
  folder=file.parent/'company-search-loading-recovery'/original_sha
  for name,data in [('original-journal.json',raw),('original-job.json',jobraw),('original-tree.json',Path(original['last_tree']['path']).read_bytes())]:immutable(folder/name,data)
  proof_path=folder/'recovery-proof.json'
  if not proof_path.exists():
   proof={'kind':KIND,'original_journal':ref(folder/'original-journal.json'),'original_job':ref(folder/'original-job.json'),'original_job_path':str(order_path),'original_tree':ref(folder/'original-tree.json'),'canonical_tree':original['last_tree'],'original_error':error,'original_calls':original['calls'],'reconciled_at':datetime.now(timezone.utc).isoformat(),'ui_used':False,'original_work_orders_only':True}
   immutable(proof_path,(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
  proof_ref=ref(proof_path);expected=copy.deepcopy(original);expected.pop('last_error');expected['company_search_loading_recovery']={'kind':KIND,'proof':proof_ref};verify_recovered(expected,proof_ref)
  if file.read_bytes()!=raw or order_path.read_bytes()!=jobraw:raise ValueError('search-recovery-input-changed')
  write_json(file,expected)
  return {'state':'reconciled','phase':expected['phase'],'journal':ref(file),'proof':proof_ref,'ui_used':False,'original_calls_unchanged':True}

BLOCK_KIND='verified-company-search-block-loading-preinput-recovery-v1'
def block_contract(job,state,tree,job_path):
 error=state.get('last_error',{})
 if error.get('code')!='company-search-loading-structure-unverified' or error.get('message')!='company-search-loading-structure-unverified':raise ValueError('search-recovery-block-exact-error-required')
 # Reuse every original navigation-only/job/fingerprint/route/loading check.
 # This is an in-memory validation adapter; original journal/error are preserved.
 checked=copy.deepcopy(state);checked['last_error']={**error,'code':'semantic-locator-not-unique','message':'semantic-locator-not-unique'}
 contract(job,checked,tree,job_path)
 if state.get('revision')!=len(state.get('calls',[])) or len(state['calls'])!=2 or state['calls'][0].get('command',{}).get('op')!='activate':raise ValueError('search-recovery-block-confirmed-prefix-required')
 return error

def verify_block_recovered(current,proof_ref):
 proof=read(proof_ref)
 if proof.get('kind')!=BLOCK_KIND or proof.get('ui_used')is not False or proof.get('original_work_orders_only')is not True:raise ValueError('search-recovery-block-proof-kind')
 original=read(proof['original_journal']);job=read(proof['original_job']);tree=read(proof['original_tree']);error=block_contract(job,original,tree,proof['original_job_path'])
 if original.get('last_tree')!=proof.get('canonical_tree') or read(proof['canonical_tree'])!=tree:raise ValueError('search-recovery-original-tree-conflict')
 if datetime.fromisoformat(proof['reconciled_at']).utcoffset()is None:raise ValueError('search-recovery-aware-time-required')
 expected=copy.deepcopy(original);expected.pop('last_error');expected['company_search_loading_recovery']={'kind':BLOCK_KIND,'proof':proof_ref}
 if current!=expected or error!=proof.get('original_error') or original['calls']!=proof.get('original_calls'):raise ValueError('search-recovery-delta-conflict')
 return {'kind':BLOCK_KIND,'original_journal':proof['original_journal'],'proof':proof_ref,'original_error':error}

def reconcile_block_loading(order_path,original_sha):
 order_path=Path(order_path).resolve();jobraw=order_path.read_bytes();job=json.loads(jobraw);file=Path(job['workflow_path'])
 with file.with_name('.bridge-execution.lock').open('a')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);raw=file.read_bytes();current=json.loads(raw)
  marker=current.get('company_search_loading_recovery')
  if sha(raw)!=original_sha:
   if not marker or marker.get('kind')!=BLOCK_KIND:raise ValueError('search-recovery-original-sha-conflict')
   expected_proof=file.parent/'company-search-loading-recovery'/original_sha/'block-recovery-proof.json'
   if marker.get('proof',{}).get('path')!=str(expected_proof) or marker['proof']!=ref(expected_proof):raise ValueError('search-recovery-block-reentry-proof-conflict')
   checked=verify_block_recovered(current,marker['proof'])
   if checked['original_journal']['sha256']!=original_sha or read(marker['proof'])['original_job']!={'path':str(file.parent/'company-search-loading-recovery'/original_sha/'original-job.json'),'sha256':sha(jobraw)}:raise ValueError('search-recovery-block-reentry-conflict')
   return {'state':'reconciled','phase':current['phase'],'journal':ref(file),'proof':marker['proof'],'ui_used':False,'original_calls_unchanged':True,'reused':True}
  original=current;tree=read(original['last_tree']);error=block_contract(job,original,tree,order_path);folder=file.parent/'company-search-loading-recovery'/original_sha
  for name,data in [('original-journal.json',raw),('original-job.json',jobraw),('original-tree.json',Path(original['last_tree']['path']).read_bytes())]:immutable(folder/name,data)
  proof_path=folder/'block-recovery-proof.json'
  if not proof_path.exists():
   proof={'kind':BLOCK_KIND,'original_journal':ref(folder/'original-journal.json'),'original_job':ref(folder/'original-job.json'),'original_job_path':str(order_path),'original_tree':ref(folder/'original-tree.json'),'canonical_tree':original['last_tree'],'original_error':error,'original_calls':original['calls'],'reconciled_at':datetime.now(timezone.utc).isoformat(),'ui_used':False,'original_work_orders_only':True}
   immutable(proof_path,(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
  proof_ref=ref(proof_path);expected=copy.deepcopy(original);expected.pop('last_error');expected['company_search_loading_recovery']={'kind':BLOCK_KIND,'proof':proof_ref};verify_block_recovered(expected,proof_ref)
  if file.read_bytes()!=raw or order_path.read_bytes()!=jobraw:raise ValueError('search-recovery-input-changed')
  write_json(file,expected)
  return {'state':'reconciled','phase':expected['phase'],'journal':ref(file),'proof':proof_ref,'ui_used':False,'original_calls_unchanged':True,'reused':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work-order',type=Path,required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--block-loading',action='store_true');a=p.parse_args();print(json.dumps((reconcile_block_loading if a.block_loading else reconcile)(a.work_order,a.original_sha256),ensure_ascii=False))
