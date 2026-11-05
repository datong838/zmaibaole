#!/usr/bin/env python3
"""One diagnostic public-DOM read. Never edits the original navigation journal."""
import argparse,fcntl,hashlib,importlib.util,json,os,sys,uuid,types
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
spec=importlib.util.spec_from_file_location('probe_navigation',ROOT/'skills/violation-notifier/scripts/bridge-navigation.py');nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def immutable(p,value):
 raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode();p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 return {'path':str(p.resolve()),'sha256':sha(raw)}
def read(path,expected):
 p=Path(path);raw=p.read_bytes();need(sha(raw)==expected,'probe-pinned-input-changed');return json.loads(raw)
def original_contract(job,s):
 nav.scope(job)
 need(s.get('fingerprint')==nav.tag(job) and s.get('phase')=='observeCenter' and s.get('last_error')=='navigation-tree-path-conflict','probe-exact-original-state-required')
 need(s.get('company')==job['company'] and s.get('groupid')==str(job['groupid']) and s.get('start')==job['start'] and s.get('end_exclusive')==job['end_exclusive'],'probe-original-binding-conflict')
 need(len(s.get('calls',[]))==1,'probe-unique-original-click-required')
 owner=types.SimpleNamespace(job=job,s=s,tab=s['tab_id']);binding=nav.transition_binding(owner,'center')
 need(binding['before']==s['last_tree'],'probe-original-before-required')
 return owner,binding

def tab_scope(tabs,owner,binding):
 tab=nav.context(tabs,owner.tab,owner.job['groupid']);u=urlsplit(tab['url'])
 need(tab.get('windowId')==binding['window_id'] and u.path in (binding['source_path'],nav.CENTER),'probe-tab-scope-risk')
 return tab

def probe(job_path,jobsha,state_path,statesha,invoke):
 job_path=Path(job_path).resolve();state_path=Path(state_path).resolve();jobraw=job_path.read_bytes();original=state_path.read_bytes();job=read(job_path,jobsha);s=read(state_path,statesha);owner,binding=original_contract(job,s);folder=state_path.parent/'navigation-read-probe'/statesha/('attempt-'+uuid.uuid4().hex);refs=[];stage='before';sample={};error=None
 def call(cmd,key):
  raw=invoke(cmd);reference=immutable(folder/(str(len(refs))+'-'+key+'-reply.json'),raw);refs.append({'command':cmd,'reply':reference})
  need(isinstance(raw,dict) and raw.get('ok') is True,'probe-transport-error:'+str(raw.get('error','unknown') if isinstance(raw,dict) else 'invalid-reply'));return raw['result']
 try:
  sample['before']=tab_scope(call({'op':'tabs'},'before'),owner,binding)
  stage='ping';sample['ping']=call({'op':'ping','tabId':owner.tab},'ping');need(sample['ping'].get('version')==nav.VERSION and sample['ping'].get('safety')=='DOM-only','probe-reviewed-version-required')
  stage='tree';sample['tree']=call({'op':'tree','tabId':owner.tab},'tree')
  stage='after';sample['after']=tab_scope(call({'op':'tabs'},'after'),owner,binding)
  stage='tree-scope';ns=list(nav.nodes(sample['tree']));need(sample['tree'].get('url') in ['https://life.douyin.com'+p for p in (binding['source_path'],nav.CENTER)],'probe-tree-path-risk')
  need(not any(any(t in n.get('name','') for t in ('扫码登录','安全验证','风险验证','账号异常','请完成验证')) for n in ns),'probe-risk-stop')
  stage='identity';nav.identity(sample['tree'],job['identity'])
 except Exception as e:error=str(e)
 need(state_path.read_bytes()==original and job_path.read_bytes()==jobraw,'probe-original-concurrent-change')
 result={'kind':'original-navigation-read-probe-v1','at':now(),'state':'hold' if error else 'observed','stage':stage,'error':error,'original_state':{'path':str(state_path),'sha256':statesha},'job':{'path':str(job_path),'sha256':jobsha},'binding':binding,'raw_replies':refs,'sample':sample,'original_journal_unchanged':True,'ui_input_used':False,'business_progress_changed':False,'automatic_resume_allowed':False}
 r=immutable(folder/'report.json',result);return {'state':result['state'],'stage':stage,'error':error,'report':r,'raw_replies':refs,'original_journal_unchanged':True,'ui_input_used':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',type=Path,required=True);p.add_argument('--job-sha256',required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--original-sha256',required=True);a=p.parse_args()
 with a.state.with_name(a.state.name+'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=probe(a.job,a.job_sha256,a.state,a.original_sha256,nav.bridge.request)
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
