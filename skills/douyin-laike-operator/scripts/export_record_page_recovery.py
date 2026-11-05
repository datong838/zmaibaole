"""Pure original-order repair for one known post-submit pagination guard. No UI."""
import argparse,copy,fcntl,hashlib,json,os,re
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
import dom_evidence as d
from role_cli import validate_job,write_json
KIND='verified-export-record-page-recovery-v1'
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(data):return hashlib.sha256(data).hexdigest()
def ref(path):p=Path(path).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def strict_path(value):
 p=Path(value);need(p.is_absolute() and p==p.resolve() and not p.is_symlink(),'record-recovery-absolute-nonsymlink-path-required');return p
def read(r):
 p=strict_path(r['path']);raw=p.read_bytes();need(sha(raw)==r['sha256'],'record-recovery-pinned-bytes-changed');return json.loads(raw)
def immutable(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(path.read_bytes()==raw,'record-recovery-immutable-conflict')
 else:
  with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return ref(path)
def fingerprint(job):
 if job.get('company_configuration_registry')=='configured-source-index-v2':
  from switch_read_recovery import fingerprint as configured_fingerprint
  return configured_fingerprint(job)
 return sha(json.dumps({k:job.get(k) for k in ('work_order_id','company','groupid','date_range','source_dir')},sort_keys=True,ensure_ascii=False).encode())
def _postsubmit_contract(job,s,expected_error):
 validate_job(job);need(s.get('fingerprint')==fingerprint(job) and s.get('work_order_id')==job['work_order_id'] and s.get('company')==job['company'] and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')=={k:job['date_range'][k] for k in ('start','end')},'record-recovery-original-job-conflict')
 need(s.get('backend')=='local-dom-bridge' and s.get('state')=='running' and s.get('phase')=='pollRecords' and s.get('exportPending') is True and s.get('attempts')==1 and not any(s.get(k) for k in ('downloadPending','download_ticket','download_command','download_receipt','result','generated_record','waiting_for')),'record-recovery-original-phase-invalid')
 error=s.get('last_error');need(error is None if expected_error is None else type(error)is dict and error.get('code')==error.get('message')==expected_error and error.get('at'),'record-recovery-only-known-error')
 need(s.get('identity')==s.get('identity_before')==job.get('identity_baseline') and s.get('provider_baseline')==job.get('provider_baseline'),'record-recovery-full-identity-required')
 calls=s.get('calls',[]);need(calls and all(c.get('state')=='confirmed' for c in calls),'record-recovery-unknown-no-replay')
 submits=[c for c in calls if c.get('phase')=='submitExport'];reloads=[c for c in calls if c.get('phase')=='reloadRecords']
 if len(submits)==len(reloads)==2:
  retention=s.get('retention_baseline_reconciliation',{});need(retention.get('kind')=='verified-backed-up-export-removal-v1','record-recovery-retention-reconciliation-required')
  previous=read(retention['original_journal']);verdict=read(retention['verdict']);removed=retention['removed'];key=(removed['export_name'],removed['generated_at'])
  identity=lambda row:(row.get('text','').split(' ',1)[0],row.get('generated_at'))
  old=previous.get('baseline_records',[]);need(verdict.get('outcome')=='confirmed-absent' and verdict.get('removed')==removed and len(old)==30 and len(s.get('baseline_records',[]))==29 and sum(identity(r)==key for r in old)==1 and [r for r in old if identity(r)!=key]==s['baseline_records'],'record-recovery-retention-baseline-changed')
  need(previous.get('calls')==calls and previous.get('submitted_at')==s.get('submitted_at') and all(calls.index(x)+1==calls.index(y) for x,y in zip(submits,reloads)),'record-recovery-retention-calls-changed')
 else:need(len(submits)==len(reloads)==1,'record-recovery-one-submit-reload-required')
 need(calls.index(submits[-1])+1==calls.index(reloads[-1])==len(calls)-1,'record-recovery-last-submit-reload-required')
 sub,rel=submits[-1],reloads[-1];cmd=sub.get('command',{});clicked=sub.get('result',{}).get('clicked',{});need(cmd.get('op')=='click' and cmd.get('tabId')==s['tab_id'] and cmd.get('kind')=='export' and clicked.get('selector')==cmd.get('locator',{}).get('value') and clicked.get('tag')=='button' and clicked.get('name')=='导出' and sub['result'].get('kind')=='export' and sub['result'].get('version')==d.VERSION,'record-recovery-submit-reply-invalid')
 cmd=rel['command'];result=rel.get('result',{});need(cmd.get('op')=='reload-records' and cmd.get('tabId')==s['record_tab_id'] and cmd.get('groupid')==str(job['groupid']) and cmd.get('reloadKey')==job['work_order_id']+'-records-'+rel['key'].split(':')[0] and result.get('reloaded') is True and result.get('loadComplete') is True and result.get('reloadKey')==cmd['reloadKey'] and result.get('tabId')==s['record_tab_id'] and result.get('groupid')==str(job['groupid']) and result.get('safety_version')==d.VERSION,'record-recovery-reload-reply-invalid')
 u=urlsplit(result.get('url',''));need(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[str(job['groupid'])] and result.get('url')==s['record_url'],'record-recovery-reload-source-conflict')
 return {'tab_id':s['record_tab_id'],'window_id':result['windowId'],'url':result['url'],'groupid':str(job['groupid'])}
def contract(job,s):return _postsubmit_contract(job,s,'record-pagination-incomplete')
def parsed(job,original,baseline_ref,tree_ref):
 scope=contract(job,original);directory=Path(job['workflow_path']).resolve().parent/'bridge-evidence';basepath=Path(baseline_ref['path']).resolve();match=re.fullmatch(r'([0-9]+)-recordsProfileRequired-tab-'+str(scope['tab_id'])+r'\.json',basepath.name)
 need(basepath.parent==directory and match and int(match.group(1))<int(next(c['key'] for c in original['calls'] if c.get('phase')=='submitExport').split(':')[0]),'record-recovery-original-baseline-path-invalid')
 baseline=read(baseline_ref);tree=read(tree_ref);need(tree_ref==original['last_tree'] and Path(tree_ref['path']).resolve().parent==directory and 'pollRecords-tab-'+str(scope['tab_id']) in Path(tree_ref['path']).name,'record-recovery-original-record-ref-conflict')
 url=urlsplit(scope['url'])._replace(query='',fragment='').geturl();need(tree.get('url')==baseline.get('url')==url,'record-recovery-tree-source-conflict');need(d.complete_record_list(baseline)==original['baseline_records'],'record-recovery-full-baseline-conflict')
 proof=d.submitted_export_record(tree,original['date_range'],original['baseline_records'],original['submitted_at']);need(proof['row'] and proof['row']['state']=='success','record-recovery-new-target-not-ready');return {**scope,**proof}
def expected_current(original,proof,proof_ref):
 current=copy.deepcopy(original);error=current.pop('last_error');current.setdefault('resolved_errors',[]).append({'original_error':error,'resolution':KIND,'proof':proof_ref,'resolved_at':proof['at']});current['record_page_recovery']=proof_ref;current['updated_at']=proof['at'];return current

def verify_recovered(current,proof_ref):
 proof=read(proof_ref);need(proof.get('kind')==KIND and proof.get('new_mutations')==0 and proof.get('ui_used') is False and proof.get('next_phase')=='pollRecords','record-recovery-proof-kind-invalid');original=read(proof['original_journal']);job=read(proof['job']);directory=Path(job['workflow_path']).resolve().parent/'export-record-page-recovery'/proof['original_journal']['sha256']
 need(Path(proof_ref['path']).resolve()==directory/'recovery-proof.json' and Path(proof['original_journal']['path']).resolve()==directory/'original-journal.json' and Path(proof['job']['path']).resolve()==directory/'original-job.json','record-recovery-proof-canonical-required')
 need(proof.get('canonical_work_order')==job.get('work_order_path') and strict_path(proof['canonical_work_order']).read_bytes()==Path(proof['job']['path']).read_bytes() and strict_path(job['workflow_path'])==Path(proof_ref['path']).resolve().parents[2]/'workflow.json','record-recovery-canonical-job-binding-changed')
 facts=parsed(job,original,proof['original_baseline_ref'],proof['original_tree_ref']);need(facts==proof['facts'],'record-recovery-proof-facts-changed')
 need(read(proof['baseline_snapshot'])==read(proof['original_baseline_ref']) and read(proof['tree_snapshot'])==read(proof['original_tree_ref']),'record-recovery-snapshot-changed');need(current==expected_current(original,proof,proof_ref),'record-recovery-current-not-exact-repair')
 return {'kind':KIND,'original_journal':proof['original_journal'],'proof':proof_ref,'original_error':original['last_error']}

def _reconcile_locked(job_path,original_sha256,baseline_ref):
 job_path=strict_path(job_path);jobraw=job_path.read_bytes();job=json.loads(jobraw);need(job.get('work_order_path')==str(job_path),'record-recovery-canonical-work-order-required');path=strict_path(job['workflow_path']);raw=path.read_bytes();s=json.loads(raw);directory=path.parent/'export-record-page-recovery'/original_sha256
 if s.get('record_page_recovery'):
  verified=verify_recovered(s,s['record_page_recovery']);need(read(verified['proof'])['original_baseline_ref']==baseline_ref,'record-recovery-original-baseline-ref-required');need(verified['original_journal']['sha256']==original_sha256,'record-recovery-original-sha-mismatch');return {'state':'reconciled','journal':ref(path),'proof':verified['proof'],'ui_used':False,'already_reconciled':True}
 need(sha(raw)==original_sha256,'record-recovery-original-sha-mismatch');facts=parsed(job,s,baseline_ref,s['last_tree']);proof={'kind':KIND,'at':datetime.now(timezone.utc).isoformat(),'new_mutations':0,'ui_used':False,'canonical_work_order':str(job_path),'original_journal':immutable(directory/'original-journal.json',raw),'job':immutable(directory/'original-job.json',jobraw),'original_tree_ref':s['last_tree'],'original_baseline_ref':baseline_ref,'tree_snapshot':immutable(directory/'original-tree.json',Path(s['last_tree']['path']).read_bytes()),'baseline_snapshot':immutable(directory/'original-baseline.json',Path(baseline_ref['path']).read_bytes()),'facts':facts,'next_phase':'pollRecords'}
 proofpath=directory/'recovery-proof.json'
 if proofpath.exists():
  old=read(ref(proofpath));need({k:v for k,v in old.items() if k!='at'}=={k:v for k,v in proof.items() if k!='at'},'record-recovery-existing-proof-conflict');proof=old
 proof_ref=immutable(proofpath,(json.dumps(proof,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());current=expected_current(s,proof,proof_ref);verify_recovered(current,proof_ref);need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'record-recovery-concurrent-journal-or-job-change');write_json(path,current)
 return {'state':'reconciled','journal':ref(path),'proof':proof_ref,'phase':'pollRecords','ui_used':False}
def reconcile(job_path,original_sha256,baseline_ref):
 job_path=strict_path(job_path);jobraw=job_path.read_bytes();job=json.loads(jobraw);need(job.get('work_order_path')==str(job_path),'record-recovery-canonical-work-order-required');path=strict_path(job['workflow_path'])
 with (path.parent/'.bridge-execution.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);need(job_path.read_bytes()==jobraw,'record-recovery-concurrent-job-change');return _reconcile_locked(job_path,original_sha256,baseline_ref)
LOADING_KIND='verified-postsubmit-record-skeleton-pending-recovery-v1'
def is_loading(tree):
 # The full application header arrives before the record type tabs/rows.
 # This shape authorizes bounded readonly waiting only, never a zero result.
 ns=list(d.nodes(tree))
 if tree.get('url')=='https://life.douyin.com/p/fulfillsettle/export_records/20101':
  titles=[n for n in ns if n.get('attributes',{}).get('class')=='headerTitle--KfObV'and n.get('tag')=='span'and n.get('name')=='导出记录']
  bars=[n for n in ns if n.get('attributes',{}).get('class')=='byted-tab-bar-items-inner']
  labels=[n for n in ns if 'byted-tab-bar-item-label'in n.get('attributes',{}).get('class','').split()or 'byted-tab-bar-item-active'in n.get('attributes',{}).get('class','').split()]
  if len(titles)==len(bars)==1 and not labels:
   kids=bars[0].get('children',[])
   if len(kids)==1 and kids[0].get('tag')=='div'and kids[0].get('name')==''and kids[0].get('attributes')=={'class':'byted-tab-bar-items-inner-line'}and kids[0].get('children')==[]:return True
 ns=list(d.nodes(tree));root=tree.get('root',{});children=root.get('children',[])
 if root.get('tag')!='body' or root.get('name')!='' or len(children)!=2:return False
 main,skeleton=children
 if main.get('attributes')!={'id':'main-app'} or main.get('tag')!='div' or main.get('name')!='' or main.get('children')!=[] or skeleton.get('attributes')!={'id':'skeleton-container'}:return False
 classes=['src-components-HomeSkeleton-index-module__home-skeleton-container--mfgyq--212e2','life-core-progress life-core-progress-shape-line life-core-progress-size-xs','life-core-progress-wrap','life-core-progress-outer','life-core-progress-inner','life-core-progress-bg']
 node=skeleton
 for label in classes:
  kids=node.get('children',[])
  if len(kids)!=1:return False
  node=kids[0]
  if node.get('tag')!='div' or node.get('name')!='' or node.get('attributes')!={'class':label}:return False
 return node.get('children')==[] and len(ns)==9

def loading_scope(job,s):
 return _postsubmit_contract(job,s,None)

def validate_loading_original(job,s,scope):
 from readonly_tick_snapshot import decode
 original=_postsubmit_contract(job,s,'record-type-not-active');window=original['window_id']
 decode(scope,s['tab_id'],window)
 before=d.context(scope['before'],s['tab_id'],job['groupid']);after=d.context(scope['after'],s['tab_id'],job['groupid'])
 for side in ('before','after'):
  record=d.context(scope[side],s['record_tab_id'],job['groupid'],record=True);need(record.get('windowId')==window and record['url']==original['url'],'record-loading-original-record-scope')
 need(before['url']==after['url'] and scope['tree'].get('url')==urlsplit(before['url'])._replace(query='',fragment='').geturl() and scope['ping'].get('version')==d.VERSION and scope['ping'].get('safety')=='DOM-only','record-loading-source-scope');d.identity(scope['tree'],job['identity_baseline'])
 tree=read(s['last_tree']);path=Path(s['last_tree']['path']);directory=Path(job['workflow_path']).parent/'bridge-evidence'
 need(path.parent==directory and re.fullmatch(str(s['revision']).zfill(4)+'-pollRecords-tab-'+str(s['record_tab_id'])+r'\.json',path.name)and tree.get('url')==urlsplit(original['url'])._replace(query='',fragment='').geturl()and is_loading(tree),'record-loading-original-skeleton')
 need(isinstance(s.get('baseline_records'),list)and s.get('submitted_at'),'record-loading-baseline-required');return original

def _loading_expected(old,proof,pr):
 new=copy.deepcopy(old);error=new.pop('last_error');new.setdefault('resolved_errors',[]).append({'original_error':error,'resolution':LOADING_KIND,'proof':pr,'resolved_at':proof['at']});new.update(record_loading_recovery=pr,updated_at=proof['at']);return new

def verify_loading_recovered(current,pr):
 p=read(pr);need(p.get('kind')==LOADING_KIND and p.get('ui_used')is False and p.get('new_mutations')==0,'record-loading-proof-policy');old=read(p['original']);job=read(p['job']);scope=read(p['scope']);directory=Path(job['workflow_path']).parent/'export-record-loading-recovery'/p['original']['sha256'];need(Path(pr['path'])==directory/'proof.json' and Path(p['original']['path'])==directory/'original-journal.json' and Path(p['job']['path'])==directory/'original-job.json' and Path(p['scope']['path']).parent==Path(job['workflow_path']).parent/'bridge-evidence' and strict_path(job['work_order_path']).read_bytes()==Path(p['job']['path']).read_bytes(),'record-loading-proof-canonical');need(p['tree']==old['last_tree']and read(p['tree_snapshot'])==read(p['tree']),'record-loading-proof-tree');need(validate_loading_original(job,old,scope)==p['facts'],'record-loading-proof-facts');need(current==_loading_expected(old,p,pr),'record-loading-current-delta');return p

def recover_loading(job_path,original_sha256,scope_ref):
 job_path=strict_path(job_path);jobraw=job_path.read_bytes();job=json.loads(jobraw);path=strict_path(job['workflow_path']);need(job['work_order_path']==str(job_path),'record-loading-canonical-job');raw=path.read_bytes();s=json.loads(raw)
 if sha(raw)!=original_sha256:
  pr=s.get('record_loading_recovery');need(pr and read(pr)['original']['sha256']==original_sha256 and read(pr)['scope']==scope_ref,'record-loading-original-sha');verify_loading_recovered(s,pr);return {'state':'already-reconciled','journal':ref(path),'proof':pr,'ui_used':False}
 need(Path(scope_ref['path']).parent==path.parent/'bridge-evidence' and re.fullmatch(str(s['revision']).zfill(4)+r'-pollRecords-scope-[0-9a-f]{32}\.json',Path(scope_ref['path']).name),'record-loading-original-companion');facts=validate_loading_original(job,s,read(scope_ref));directory=path.parent/'export-record-loading-recovery'/original_sha256
 proof={'kind':LOADING_KIND,'at':datetime.now(timezone.utc).isoformat(),'ui_used':False,'new_mutations':0,'original':immutable(directory/'original-journal.json',raw),'job':immutable(directory/'original-job.json',jobraw),'scope':scope_ref,'tree':s['last_tree'],'tree_snapshot':immutable(directory/'original-tree.json',Path(s['last_tree']['path']).read_bytes()),'facts':facts};pr=immutable(directory/'proof.json',(json.dumps(proof,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode());new=_loading_expected(s,proof,pr);verify_loading_recovered(new,pr);need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'record-loading-concurrent-change');write_json(path,new);return {'state':'reconciled','journal':ref(path),'proof':pr,'ui_used':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-order',required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--baseline-observation',required=True);p.add_argument('--baseline-sha256',required=True);a=p.parse_args();print(json.dumps(reconcile(a.work_order,a.original_sha256,{'path':str(strict_path(a.baseline_observation)),'sha256':a.baseline_sha256}),ensure_ascii=False))
if __name__=='__main__':main()
