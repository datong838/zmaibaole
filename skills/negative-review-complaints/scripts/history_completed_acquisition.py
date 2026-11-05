"""Adopt an approved original completed acquisition into a history-only root.
No acquisition creation, browser, export, sender or business-cursor capability.
"""
import argparse,hashlib,json,os
from datetime import date,timedelta
from pathlib import Path
KIND='history-completed-acquisition-adoption-v2'
APPROVAL='reviewed-completed-acquisition-history-adoption-v2'
def need(ok,message):
 if not ok:raise ValueError(message)
def ref(path):
 p=Path(path);need(p.is_absolute()and p.resolve()==p and p.is_file()and not any(v.is_symlink()for v in(p,*p.parents)),'adoption-canonical-ref');return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def doc(reference):need(ref(reference['path'])==reference,'adoption-ref-changed');return json.loads(Path(reference['path']).read_bytes())
def encoded(value):return(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))).encode()
def completed_journal(state):
 need(state.get('state')=='complete'and state.get('phase')=='done'and not state.get('last_error')and not state.get('error')and bool(state.get('calls'))and all(c.get('state')=='confirmed'for c in state['calls']),'completed-source-has-unresolved-call-or-error')

def bootstrap(manifest_ref,receipt_ref):
 import prepare_company_navigation as api
 m=doc(manifest_ref);need(m.get('kind')=='observed-company-history-acquire-prepared-v1','original-bootstrap-manifest-required');b=m['binding'];need(set(b)=={'kind','operation','identity_review','company','groupid','identity','range','purpose'}and b['kind']=='observed-company-history-acquire-binding-v1'and b['purpose']=='negative-review-appeal-history-only','original-bootstrap-binding-schema');need(type(b['company'])is str and b['company']and type(b['groupid'])is str and b['groupid'].isdigit(),'approved-company-binding')
 job=doc(m['work_order']);base=Path(m['work_order']['path']).parent;key=hashlib.sha256(encoded(b)).hexdigest();need(manifest_ref['path']==str(base/'prepare-manifest.json')and job['work_order_id']==key and job['work_order_path']==str(base/'work-order.json')and job['workflow_path']==str(base/'workflow.json')and job['output_dir']==str(base),'bootstrap-owned-paths');need(job.get('action')=='acquire'and job.get('backend')=='local-dom-bridge'and job['company']==b['company']and str(job['groupid'])==b['groupid']and job.get('identity_baseline')==b['identity']and job.get('known_company_identities')=={b['groupid']:b['identity']}and job.get('identity_bootstrap')is False and job.get('source_purpose')==b['purpose']and all(job.get(k)is False for k in('progress_updates_enabled','send_enabled','submit_enabled')),'bootstrap-history-only-identity')
 dates=b['range'];need(set(dates)=={'start','end_exclusive'}and date.fromisoformat(dates['start'])<date.fromisoformat(dates['end_exclusive']),'bootstrap-range');inclusive=(date.fromisoformat(dates['end_exclusive'])-timedelta(days=1)).isoformat();need(job['date_range']['start']==dates['start']and job['date_range']['end_exclusive']==dates['end_exclusive']and job['date_range']['end']==inclusive,'bootstrap-exact-range');need(receipt_ref['path']==str(base/'acquisition.json')==m['expected_acquisition_receipt'],'physical-original-receipt-required')
 # Completed source is authoritative: no temporary discovery/builder code is
 # executed or installed. Original discovery refs remain immutable provenance.
 observed=doc(b['operation']);review=doc(b['identity_review']);checkpoint=observed.get('checkpoint',{});need(observed.get('state')=='complete'and observed.get('binding',{}).get('target_company')==b['company']and observed['binding'].get('range')==dates and checkpoint.get('company')==b['company']and str(checkpoint.get('groupid'))==b['groupid']and checkpoint.get('identity')==b['identity']and checkpoint.get('business_resume')is False and checkpoint.get('acquisition_receipt')is False,'bootstrap-original-observed-identity');need(review.get('approved')is True and review.get('operation')==b['operation']and review.get('company')==b['company']and str(review.get('groupid'))==b['groupid']and review.get('identity')==b['identity']and review.get('range')==dates,'bootstrap-original-identity-review');value,raw,journal=api.receipt(receipt_ref);s=doc(journal);completed_journal(s);need(journal['path']==job['workflow_path']and value['work_order_id']==key and value['company']==b['company']and str(value['groupid'])==b['groupid']and value['identity']==b['identity']and value['date_range']=={'start':dates['start'],'end':inclusive},'completed-original-source-scope');need(Path(value['source']).parent==Path(job['source_dir']).resolve(),'original-owned-export-directory');return m,job,value,journal

def approval(root,manifest_ref,receipt_ref,approval_ref):
 a=doc(approval_ref);need(set(a)=={'kind','approved','bootstrap_manifest','receipt','history_root','source_purpose'}and a['kind']==APPROVAL and a['approved']is True and a['bootstrap_manifest']==manifest_ref and a['receipt']==receipt_ref and a['history_root']==str(root)and a['source_purpose']=='negative-review-appeal-history-only','explicit-completed-adoption-approval');return a

def expected_artifact(root,manifest_ref,receipt_ref,approval_ref,value,journal):return {'kind':KIND,'history_root':str(root),'bootstrap_manifest':manifest_ref,'receipt':receipt_ref,'journal':journal,'source':{'path':value['source'],'sha256':value['src_sha256']},'approval':approval_ref,'source_purpose':'negative-review-appeal-history-only','export_replayed':False}
def expected_job(value,receipt_ref,dates):return {'company':value['company'],'groupid':str(value['groupid']),'start':dates['start'],'end_exclusive':dates['end_exclusive'],'account_verified':True,'identity':value['identity'],'source_work_order_id':value['work_order_id'],'source_receipt':receipt_ref['path'],'source_receipt_sha256':receipt_ref['sha256']}
def matches(state,value,receipt_ref,dates):need(state['company']==value['company']and state['groupid']==str(value['groupid'])and state['identity']==value['identity']and state['history_range']==dates and state['identity_receipt']['sha256']==receipt_ref['sha256'],'history-target-binding-conflict-before-write')
def validate(root,state,adoption_ref,receipt_ref):
 root=Path(root).resolve();need(adoption_ref==state.get('completed_acquisition_adoption')and adoption_ref['path']==str(root/'completed-acquisition-adoption.json'),'owned-adoption-pointer-required');a=doc(adoption_ref);approval(root,a['bootstrap_manifest'],receipt_ref,a['approval']);m,job,value,journal=bootstrap(a['bootstrap_manifest'],receipt_ref);need(a==expected_artifact(root,a['bootstrap_manifest'],receipt_ref,a['approval'],value,journal),'adoption-kind-root-source-scope');matches(state,value,receipt_ref,m['binding']['range']);return {'receipt':receipt_ref,'bootstrap_manifest':a['bootstrap_manifest'],'journal':journal,'source':a['source'],'use':'completed-original-source-only-no-new-prepare-or-export'}
def adopt(root,manifest_ref,receipt_ref,approval_ref,*,history_api):
 root=Path(root);need(root.is_absolute()and root.resolve()==root and not any(v.is_symlink()for v in(root,*root.parents)),'absolute-history-root');approval(root,manifest_ref,receipt_ref,approval_ref);m,job,value,journal=bootstrap(manifest_ref,receipt_ref);dates=m['binding']['range'];artifact=expected_artifact(root,manifest_ref,receipt_ref,approval_ref,value,journal);path=root/'completed-acquisition-adoption.json';out=root/'navigation-job.json';expected=expected_job(value,receipt_ref,dates)
 # Check immutable/terminal conflicts before initialize or any state mutation.
 if path.exists()or path.is_symlink():need(doc(ref(path))==artifact,'original-adoption-conflict')
 if out.exists()or out.is_symlink():need(doc(ref(out))==expected,'history-normal-job-output-conflict-before-write')
 need(not list((root/'acquisition').glob('*/prepare-manifest.json')),'history-second-prepare-present')
 if(root/'state.json').exists():matches(history_api.load(root),value,receipt_ref,dates)
 else:history_api.initialize(root,value['company'],str(value['groupid']),dates['start'],dates['end_exclusive'],receipt_ref)
 with history_api.workflow.locked(root):
  state=history_api.load(root);matches(state,value,receipt_ref,dates);need(not list((root/'acquisition').glob('*/prepare-manifest.json')),'history-second-prepare-present')
  if not state.get('completed_acquisition_adoption'):need(not state['tasks']and not state['sources'],'history-not-empty-before-adoption')
  if path.exists():need(doc(ref(path))==artifact,'original-adoption-conflict')
  else:
   with path.open('x')as file:json.dump(artifact,file,ensure_ascii=False,indent=2);file.write('\n');file.flush();os.fsync(file.fileno())
  pointer=ref(path)
  if state.get('completed_acquisition_adoption')is not None:need(state['completed_acquisition_adoption']==pointer,'original-adoption-pointer-conflict')
  else:state['completed_acquisition_adoption']=pointer;history_api._save(root,state,{'type':'history-completed-source-adopted','adoption':pointer,'new_export':False})
  validate(root,state,pointer,receipt_ref)
 return history_api.prepare_normal_job(root,receipt_ref,out,completed_acquisition_adoption_ref=pointer)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--bootstrap-manifest',required=True);p.add_argument('--bootstrap-manifest-sha256',required=True);p.add_argument('--receipt',required=True);p.add_argument('--receipt-sha256',required=True);p.add_argument('--approval',required=True);p.add_argument('--approval-sha256',required=True);x=p.parse_args();import history_workspace as h;r=adopt(Path(x.root),{'path':x.bootstrap_manifest,'sha256':x.bootstrap_manifest_sha256},{'path':x.receipt,'sha256':x.receipt_sha256},{'path':x.approval,'sha256':x.approval_sha256},history_api=h);print(json.dumps(r,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
