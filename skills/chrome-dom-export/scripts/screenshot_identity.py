"""Screenshot-only identity anchor; no UI, global identity relaxation or source edits.
A current frame proves public provider + exact URL/tab/window; full account comes
from the pinned verified entry observation, and is rechecked if a card is visible.
The caller must retire this contract on company/login/browser-lease changes.
"""
import importlib,json,sys,re,os
from pathlib import Path
from contextlib import contextmanager
from urllib.parse import urlsplit,parse_qs
import governance_projection as gp
import screenshot_registration as sr
from visible_capture import sha,atomic
SCHEMA=gp.PROVIDER_SCHEMA
@contextmanager
def api():
 directory=Path(__file__).resolve().parents[3]/'skills/violation-notifier/scripts';old=list(sys.path)
 try:
  sys.path.insert(0,str(directory));d=importlib.import_module('governance_detail');p=importlib.import_module('prepare_records_profile')
  gp.need(Path(d.__file__).resolve()==directory/'governance_detail.py','anchor-module-origin');yield d,p
 finally:sys.path[:]=old

def _scope(obs,gid,tab,window,*,projection_contract=None):
 gp.need(obs.get('source')=='local-dom-bridge' and obs.get('tab_id')==tab and obs.get('tab',{}).get('tabId')==tab and obs['tab'].get('windowId')==window,'anchor-tab-window')
 u=urlsplit(obs['tab']['url']);gp.need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and parse_qs(u.query,keep_blank_values=True).get('groupid')==[str(gid)],'anchor-url-group')
 gp.project(obs['tree'],gid,actual_url=obs['tab']['url'],projection_contract=projection_contract)

def create(source,profile,observation,*,chain_id,pid,_check_navigation=True):
 src=sr.document(source);pr=sr.document(profile);raw=sr.document(observation)
 gp.need(type(pid) is int and pid>0 and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',chain_id or ''),'anchor-session-required')
 with api() as (d,p):
  p.validate(pr,source);meta=pr['derivation'];job=d.document(meta['job']);query=d.document(meta['query']);d.nav.scope(job)
  _scope(raw,src['groupid'],meta['tab_id'],meta['window_id'],projection_contract=pr.get('projection_contract'));d.nav.identity(raw['tree'],job['identity']);d.normal_page(raw['tree'],job,query)
  gp.need(job['identity']==src['identity'],'anchor-source-identity')
  receipt=job.get('identity_context') or {'path':job['identity_receipt'],'sha256':job['identity_receipt_sha256']};d.document(receipt)
  navpath=Path(source['path']).resolve().parent/'.records-region-navigation'/source['sha256']/'state.json'
  if meta.get('kind')=='governance-records-reboot-derived-profile-v1':
   import violation_reboot_profile as reboot
   navpath=reboot.nav_root(pr,source)/'state.json'
  nav=json.loads(navpath.read_text())
  gp.need(nav['binding']['source']==source and nav['binding']['job']==meta['job'] and nav['binding']['query']==meta['query'],'anchor-original-nav-binding')
  if _check_navigation:gp.need(all(o.get('state')=='complete' for o in nav['operations']),'anchor-original-nav-unresolved')
  gp.need(observation in nav['observations'],'anchor-observation-not-canonical')
 return {'schema':SCHEMA,'source':source,'profile':profile,'full_identity_observation':observation,'job':meta['job'],'query':meta['query'],'identity_receipt':receipt,'identity':src['identity'],'groupid':str(src['groupid']),'tab_id':meta['tab_id'],'window_id':meta['window_id'],'chain_id':chain_id,'native_pid':pid,'continuity_scope':'original-company-screenshot-session-only','invalidated_by':['company-switch','login-change','browser-lease-change'],'created_at':raw['observed_at']}

def validate(anchor_ref,source,profile,*,chain_id=None,pid=None):
 a=sr.document(anchor_ref);want=create(a['source'],a['profile'],a['full_identity_observation'],chain_id=a['chain_id'],pid=a['native_pid'],_check_navigation=False)
 gp.need(a==want and a['source']==source and a['profile']==profile,'anchor-binding-changed')
 if chain_id is not None:gp.need(chain_id==a['chain_id'],'anchor-chain-changed')
 if pid is not None:gp.need(pid==a['native_pid'],'anchor-pid-changed')
 return a

def current(anchor_ref,source,profile,obs):
 a=validate(anchor_ref,source,profile);_scope(obs,a['groupid'],a['tab_id'],a['window_id'],projection_contract=sr.document(profile).get('projection_contract'));ns=list(gp.walk(obs['tree']['root']))
 provider=gp.one([n for n in ns if 'Profile-index-module__title--' in n.get('attributes',{}).get('class','') and re.fullmatch(r'服务商[0-9]+',n.get('name',''))],'anchor-public-provider')
 gp.need(provider['name']==a['identity']['provider'],'anchor-provider-changed')
 cards=[n for n in ns if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')];gp.need(len(cards)<=1,'anchor-visible-card-ambiguous')
 with api() as (d,p):
  if cards:d.nav.identity(obs['tree'],a['identity'])
  d.normal_page(obs['tree'],d.document(a['job']),d.document(a['query']))
 for n in ns:gp.need(not any(x in n.get('name','') for x in ('扫码登录','风险验证','安全验证','账号异常')),'anchor-risk-stop')
 return {'contract':SCHEMA,'public_provider':provider['name'],'actual_url':obs['tab']['url'],'full_identity_source':'pinned-entry-observation','visible_full_identity':a['identity'] if cards else None}

if __name__=='__main__':
 import argparse
 q=argparse.ArgumentParser(description=__doc__)
 for k in ('source','source-sha256','profile','profile-sha256','observation','observation-sha256','chain-id','pid','out'):q.add_argument('--'+k,required=True)
 v=q.parse_args();ref=lambda k:{'path':str(Path(getattr(v,k)).resolve()),'sha256':getattr(v,k+'_sha256')};out=Path(v.out).resolve();a=create(ref('source'),ref('profile'),ref('observation'),chain_id=v.chain_id,pid=int(v.pid))
 if out.exists():gp.need(sr.document({'path':str(out),'sha256':sha(out)})==a,'anchor-existing-conflict')
 else:
  with out.open('x') as f:json.dump(a,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
 print(json.dumps({'path':str(out),'sha256':sha(out)},ensure_ascii=False))
