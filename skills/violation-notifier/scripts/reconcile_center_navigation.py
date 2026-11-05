#!/usr/bin/env python3
"""Pure reconciliation of one confirmed center navigation and fresh pinned probe."""
import argparse,copy,fcntl,hashlib,json,sys,uuid
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import navigation_read_probe as p
nav=p.nav;KIND='verified-center-navigation-probe-reconciliation-v1'
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(path):path=Path(path).resolve();return {'path':str(path),'sha256':sha(path.read_bytes())}
def read(reference):return p.read(reference['path'],reference['sha256'])
def immutable(path,raw):
 path.parent.mkdir(parents=True,exist_ok=True)
 try:
  with path.open('xb') as f:f.write(raw)
 except FileExistsError:need(path.read_bytes()==raw,'center-recovery-archive-conflict')
 return ref(path)
def replay(job,original,probe):
 owner,binding=p.original_contract(job,original)
 need(probe.get('kind')=='original-navigation-read-probe-v1' and probe.get('state')=='observed' and probe.get('stage')=='identity' and probe.get('error') is None and probe.get('ui_input_used') is False and probe.get('original_journal_unchanged') is True and probe.get('business_progress_changed') is False and probe.get('automatic_resume_allowed') is False,'center-recovery-observed-probe-required')
 need(probe.get('binding')==binding,'center-recovery-original-before-conflict')
 entries=probe.get('raw_replies',[]);need([v.get('command') for v in entries]==[{'op':'tabs'},{'op':'ping','tabId':owner.tab},{'op':'tree','tabId':owner.tab},{'op':'tabs'}],'center-recovery-four-readonly-replies-required')
 replies=[read(v['reply']) for v in entries];need(all(isinstance(v,dict) and v.get('ok') is True for v in replies),'center-recovery-raw-transport-failed')
 before=p.tab_scope(replies[0]['result'],owner,binding);ping=replies[1]['result'];tree=replies[2]['result'];after=p.tab_scope(replies[3]['result'],owner,binding)
 need(before['url']==after['url'] and before['windowId']==after['windowId'] and urlsplit(before['url']).path==urlsplit(after['url']).path==nav.CENTER and tree.get('url')=='https://life.douyin.com'+nav.CENTER,'center-recovery-stable-target-required')
 need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('url')==tree['url'],'center-recovery-reviewed-version-required')
 ns=list(nav.nodes(tree));need(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in ns),'center-recovery-risk-stop')
 actual=nav.identity(tree,job['identity'])
 need(probe.get('sample')=={'before':before,'ping':ping,'tree':tree,'after':after},'center-recovery-sample-raw-conflict')
 when=datetime.fromisoformat(probe['at']);clicked=datetime.fromisoformat(original['calls'][0]['intent_at']);need(when.utcoffset() is not None and when>=clicked,'center-recovery-aware-observation-required')
 return {'tab_id':owner.tab,'window_id':binding['window_id'],'groupid':str(job['groupid']),'url':before['url'],'identity':actual,'full_identity_observed':True,'probe_observed_at':probe['at']}
def verify_recovered(current,proof_ref):
 proof=read(proof_ref);need(proof.get('kind')==KIND and proof.get('ui_used') is False,'center-recovery-proof-kind')
 job=read(proof['original_job']);old=read(proof['original_state']);probe=read(proof['probe']);facts=replay(job,old,probe);need(facts==proof.get('facts'),'center-recovery-proof-facts')
 need(probe['original_state']==proof['canonical_original_state'] and probe['job']==proof['canonical_original_job'],'center-recovery-probe-original-input-conflict')
 need(len(proof.get('raw_reply_archives',[]))==4,'center-recovery-four-raw-archives-required')
 for original,archived in zip(probe['raw_replies'],proof['raw_reply_archives']):
  need(archived.get('command')==original['command'] and archived.get('canonical_reply')==original['reply'] and read(archived['archive'])==read(original['reply']) and archived['archive']['sha256']==original['reply']['sha256'],'center-recovery-raw-archive-conflict')
 need(read(proof['original_before'])==read(old['last_tree']) and proof['original_before']['sha256']==old['last_tree']['sha256'],'center-recovery-original-before-archive-conflict')
 expected=copy.deepcopy(old);expected.pop('last_error');expected['center_navigation_probe_reconciliation']={'kind':KIND,'proof':proof_ref}
 need(current==expected,'center-recovery-only-error-delta-required')
 return {'kind':KIND,'original_journal':proof['original_state'],'proof':proof_ref,'original_error':old['last_error'],'facts':facts}
def reconcile(job_path,jobsha,state_path,statesha,probe_path,probesha):
 job_path=Path(job_path).resolve();state_path=Path(state_path).resolve();probe_path=Path(probe_path).resolve();job=p.read(job_path,jobsha);raw=state_path.read_bytes();need(sha(raw)==statesha,'center-recovery-original-state-sha');old=json.loads(raw);observed=p.read(probe_path,probesha);need(observed.get('original_state')=={'path':str(state_path),'sha256':statesha} and observed.get('job')=={'path':str(job_path),'sha256':jobsha},'center-recovery-probe-input-conflict');facts=replay(job,old,observed)
 folder=state_path.parent/'center-navigation-reconciliation'/statesha;jobref=immutable(folder/'original-job.json',job_path.read_bytes());oldref=immutable(folder/'original-state.json',raw);proberef=immutable(folder/'probe-report.json',probe_path.read_bytes());proofpath=folder/'recovery-proof.json'
 raw_archives=[]
 for i,item in enumerate(observed['raw_replies']):raw_archives.append({'command':item['command'],'canonical_reply':item['reply'],'archive':immutable(folder/('raw-'+str(i)+'-reply.json'),Path(item['reply']['path']).read_bytes())})
 before_archive=immutable(folder/'original-before.json',Path(old['last_tree']['path']).read_bytes())
 proof={'raw_reply_archives':raw_archives,'original_before':before_archive,'kind':KIND,'at':datetime.now(timezone.utc).isoformat(),'original_job':jobref,'original_state':oldref,'probe':proberef,'canonical_original_job':{'path':str(job_path),'sha256':jobsha},'canonical_original_state':{'path':str(state_path),'sha256':statesha},'facts':facts,'ui_used':False}
 if not proofpath.exists():immutable(proofpath,(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
 proofref=ref(proofpath);new=copy.deepcopy(old);new.pop('last_error');new['center_navigation_probe_reconciliation']={'kind':KIND,'proof':proofref};verify_recovered(new,proofref)
 need(state_path.read_bytes()==raw and sha(job_path.read_bytes())==jobsha and sha(probe_path.read_bytes())==probesha,'center-recovery-original-concurrent-change');nav.write_json(state_path,new)
 return {'state':'reconciled','phase':new['phase'],'journal':ref(state_path),'proof':proofref,'ui_used':False,'normal_tick_not_run':True}
def main():
 a=argparse.ArgumentParser(description=__doc__)
 for flag in ('job','state','probe-report'):a.add_argument('--'+flag,type=Path,required=True)
 for flag in ('job-sha256','original-sha256','probe-sha256'):a.add_argument('--'+flag,required=True)
 v=a.parse_args()
 with v.state.with_name(v.state.name+'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=reconcile(v.job,v.job_sha256,v.state,v.original_sha256,v.probe_report,v.probe_sha256)
 print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
