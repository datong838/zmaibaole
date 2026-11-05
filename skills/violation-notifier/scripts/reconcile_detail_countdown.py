#!/usr/bin/env python3
"""Pure exact-state recovery after the approved countdown-only normal-page fix."""
import argparse,copy,fcntl,hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import governance_detail as d
KIND='verified-detail-zero-input-countdown-reconciliation-v1'
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':sha(p.read_bytes())}
def read(r):return d.document(r)
def immutable(p,raw):
 p.parent.mkdir(parents=True,exist_ok=True)
 try:
  with p.open('xb') as f:f.write(raw)
 except FileExistsError:need(p.read_bytes()==raw,'detail-zero-recovery-archive-conflict')
 return ref(p)
def replay(manifest,state,parser_ref):
 need(Path(parser_ref['path']).resolve()==Path(d.__file__).resolve() and sha(Path(d.__file__).read_bytes())==parser_ref['sha256'],'detail-zero-recovery-approved-parser-required')
 v=d.inputs(manifest);job=v['job'];q=v['query'];expected_path=Path(manifest['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/d.nav.tag(job)/'state.json'
 need(state.get('manifest')==manifest and state.get('fingerprint')==d.nav.tag(job) and state.get('tab_id')==manifest['tab_id'] and state.get('approved_version')==manifest['approved_version'],'detail-zero-recovery-original-binding-required')
 need(state.get('phase')=='normal' and state.get('cursor')==0 and state.get('current') is None and state.get('calls')==[] and state.get('details')==[] and state.get('pages')==[] and state.get('profile_accepted') is False and state.get('business_progress_changed') is False and state.get('last_error')=='governance-detail-current-row-facts-changed' and not state.get('hold'),'detail-zero-recovery-exact-zero-input-error-required')
 need(state.get('observations')==[state.get('last_observation')],'detail-zero-recovery-single-fresh-observation-required');raw=read(state['last_observation']);source=read(q['last_observation']);need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==state['tab_id'] and raw.get('tree',{}).get('truncated') is False,'detail-zero-recovery-fresh-source-conflict')
 tab=d.nav.context([{'tabs':[raw['tab']]}],state['tab_id'],job['groupid']);need(tab.get('windowId')==source['tab']['windowId'] and __import__('urllib.parse',fromlist=['urlsplit']).urlsplit(tab['url']).path==d.g.RECORDS and raw['tree'].get('url')=='https://life.douyin.com'+d.g.RECORDS,'detail-zero-recovery-fresh-route-conflict');d.nav.identity(raw['tree'],job['identity']);ns=d.g.nodes(raw['tree']);need(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in ns),'detail-zero-recovery-risk-stop')
 # The published normal-page parser must independently approve this exact pair.
 approved=d.normal_page(raw['tree'],job,q);page=d.g.records_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']);original=d.g.one([p for p in q['pages'] if p['page']==page['page']],'detail-zero-recovery-original-page-required');need(approved=={k:v for k,v in original.items() if k!='observation'},'detail-zero-recovery-normalized-source-mismatch');need(len(page['rows'])==len(original['rows'])==4,'detail-zero-recovery-exact-four-rows-required');changes=[]
 for old,new in zip(original['rows'],page['rows']):
  need(set(old)==set(new) and all(old[k]==new[k] for k in old if k!='rectification_status'),'detail-zero-recovery-noncountdown-facts-changed')
  if old['rectification_status']!=new['rectification_status']:
   need(d.pending_rectification_display(new['rectification_status']) is not None and d.pending_rectification_display(old['rectification_status']) is not None,'detail-zero-recovery-known-pending-label-required');changes.append({'notice_id':old['notice_id'],'old':old['rectification_status'],'fresh':new['rectification_status']})
 need(len(changes)==1,'detail-zero-recovery-single-countdown-diff-required');return {'expected_state_path':str(expected_path),'fresh_observation':state['last_observation'],'source_query':manifest['inputs']['query'],'rows':4,'countdown_only_differences':changes,'stable_rectification_label':'待整改','deadline_equivalence_claimed':False,'ui_used':False}

def verify_recovered(current,proof_ref):
 proof=read(proof_ref);need(proof.get('kind')==KIND,'detail-zero-recovery-proof-kind');old=read(proof['original_state']);manifest=read(proof['original_manifest']);facts=replay(manifest,old,proof['parser']);need(facts==proof.get('facts'),'detail-zero-recovery-facts-conflict')
 for canonical,archive in proof['archives']:need(read(canonical)==read(archive) and canonical['sha256']==archive['sha256'],'detail-zero-recovery-archive-conflict')
 expected=copy.deepcopy(old);expected.pop('last_error');expected['detail_zero_input_reconciliation']={'kind':KIND,'proof':proof_ref};need(current==expected,'detail-zero-recovery-only-error-delta-required');return {'kind':KIND,'original_journal':proof['original_state'],'proof':proof_ref,'facts':facts,'original_error':old['last_error']}

def reconcile(manifest_path,manifest_sha,state_path,state_sha,parser_sha):
 manifest_path=Path(manifest_path).resolve();state_path=Path(state_path).resolve();manifest=read({'path':str(manifest_path),'sha256':manifest_sha});oldref={'path':str(state_path),'sha256':state_sha};old=read(oldref);raw=state_path.read_bytes();parser=ref(d.__file__);need(parser['sha256']==parser_sha,'detail-zero-recovery-parser-sha-conflict');facts=replay(manifest,old,parser);need(str(state_path)==facts['expected_state_path'],'detail-zero-recovery-canonical-state-required');folder=state_path.parent/'zero-input-countdown-recovery'/state_sha;oldarchive=immutable(folder/'original-state.json',raw);marchive=immutable(folder/'original-manifest.json',manifest_path.read_bytes());archives=[]
 refs=[{'path':str(manifest_path),'sha256':manifest_sha}]+list(manifest['inputs'].values())+[old['last_observation']]+[p['observation'] for p in read(manifest['inputs']['query'])['pages']]
 for i,r in enumerate(refs):archives.append((r,immutable(folder/('input-'+str(i)+'.json'),Path(r['path']).read_bytes())))
 proofpath=folder/'recovery-proof.json';proof={'kind':KIND,'at':datetime.now(timezone.utc).isoformat(),'original_state':oldarchive,'original_manifest':marchive,'archives':archives,'parser':parser,'facts':facts,'ui_used':False}
 if not proofpath.exists():immutable(proofpath,(json.dumps(proof,ensure_ascii=False,indent=2)+'\n').encode())
 proofref=ref(proofpath);new=copy.deepcopy(old);new.pop('last_error');new['detail_zero_input_reconciliation']={'kind':KIND,'proof':proofref};verify_recovered(new,proofref);need(state_path.read_bytes()==raw,'detail-zero-recovery-original-concurrent-change');d.nav.write_json(state_path,new);return {'state':'reconciled','phase':new['phase'],'cursor':new['cursor'],'journal':ref(state_path),'proof':proofref,'ui_used':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--parser-sha256',required=True);a=p.parse_args()
 with a.state.with_name('.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=reconcile(a.manifest,a.manifest_sha256,a.state,a.original_sha256,a.parser_sha256)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
