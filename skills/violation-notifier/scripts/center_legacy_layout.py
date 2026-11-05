"""One observed center layout button; no date/query/data mutation or guessed URL.
Proposed caller: prepare original refs, then run same canonical manifest. No UI here
unless run is explicitly invoked by the authorized operator after reviewed hotbuild.
"""
import argparse,fcntl,hashlib,importlib.util,json,sys,uuid
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
spec=importlib.util.spec_from_file_location('legacy_layout_nav',ROOT/'skills/violation-notifier/scripts/bridge-navigation.py');nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
import governance_dom as g
MARKER='observed-return-legacy-v1';BUILD='governance-center-legacy-layout-v1'
ACCEPTED_BUILDS=(BUILD,'configured-exact-company-v2')
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':nav.digest(p)}
def read(r):return nav.read_pinned(r['path'],r['sha256'])
def need(ok,code):nav.require(ok,code)
def one(items,code):
 need(len(items)==1,code);return items[0]
def validate(obs,job):
 nav.scope(job);need(obs.get('source')=='local-dom-bridge' and obs.get('tab_id')==obs['tab'].get('tabId'),'layout-source-tab-conflict')
 tab=nav.context([{'tabs':[obs['tab']]}],obs['tab_id'],job['groupid']);need(tab.get('windowId') is not None and urlsplit(tab['url']).path==nav.CENTER,'layout-center-scope-required')
 t=obs['tree'];need(t.get('url')=='https://life.douyin.com'+nav.CENTER,'layout-tree-scope-conflict');nodes=list(nav.nodes(t));nav.identity(t,job['identity'])
 need(not any(any(s in n.get('name','') for s in ('扫码登录','风险验证','安全验证','账号异常','请完成验证')) for n in nodes),'layout-risk-stop')
 need(not any(n.get('role')=='dialog' or n.get('tag')=='dialog' or (n.get('tag')=='button' and n.get('name') in ('保存','提交','确认','确定','应用配置')) for n in nodes),'layout-unexpected-confirmation-stop')
 return t

def target(tree):
 rows=[]
 def visit(n,parents):
  rows.append((n,parents))
  for c in n.get('children',[]):visit(c,parents+[n])
 visit(tree['root'],[])
 roots=[n for n,_ in rows if n.get('attributes',{}).get('id')=='governanceRoot'];root=one(roots,'layout-root-not-unique')
 button,parents=one([(n,p) for n,p in rows if n.get('name')=='回到旧版' and n.get('tag')=='button'],'layout-back-button-not-unique')
 cls=lambda n:set(n.get('attributes',{}).get('class','').split())
 need(button.get('role')=='button' and not button.get('disabled') and not button.get('children') and not any(n.get('tag') in ('form','a','dialog') or n.get('role')=='dialog' for n in parents),'layout-button-shape-invalid')
 need(cls(button)==set('governance_merchant-btn governance_merchant-btn-size-md governance_merchant-btn-type-text governance_merchant-btn-shape-angle governance_merchant-can-input-grouped backButton-cbYsPY'.split()),'layout-button-class-invalid')
 need(len(parents)>=4,'layout-button-ancestry-invalid');actions,header,container=parents[-1],parents[-2],parents[-3]
 need(cls(actions)=={'actions-lq_eBp'} and cls(header)=={'header-EaBIRz'} and cls(container)=={'container-a3IjFk'} and parents[-4] is root,'layout-button-ancestry-invalid')
 title=one([n for n in header.get('children',[]) if n.get('tag')=='p' and cls(n)=={'title-N66Jpb'}],'layout-title-not-unique');need(title.get('name')=='违规中心' and not title.get('children'),'layout-title-invalid')
 return button

def prepare(job_ref,observation_ref,key):
 job=read(job_ref);before=read(observation_ref);validate(before,job);target(before['tree']);need(isinstance(key,str) and key.strip() and len(key)<=100,'layout-stable-key-required')
 folder=Path(job_ref['path']).parent/'.center-legacy-layout'/nav.tag(job);folder.mkdir(parents=True,exist_ok=True)
 m={'kind':'center-legacy-layout-display-navigation-v1','job':job_ref,'before':observation_ref,'tab_id':before['tab_id'],'window_id':before['tab']['windowId'],'key':key,'state_path':str(folder/'state.json')};mp=folder/'manifest.json'
 if mp.exists():need(json.loads(mp.read_text())==m,'layout-original-manifest-required')
 else:nav.write_json(mp,m)
 return ref(mp)

def _run_locked(manifest_ref,invoke=None):
 invoke=invoke or nav.bridge.request;m=read(manifest_ref);need(m.get('kind')=='center-legacy-layout-display-navigation-v1','layout-manifest-kind-invalid');job=read(m['job']);before=read(m['before']);validate(before,job);target(before['tree']);need(m['tab_id']==before['tab_id'] and m['window_id']==before['tab']['windowId'],'layout-original-context-conflict')
 canonical=Path(m['job']['path']).parent/'.center-legacy-layout'/nav.tag(job)
 need(Path(manifest_ref['path'])==canonical/'manifest.json' and Path(m['state_path'])==canonical/'state.json','layout-canonical-path-required');path=Path(m['state_path'])
 s=json.loads(path.read_text()) if path.exists() else {'manifest':manifest_ref,'phase':'prepared','observations':[],'business_progress_changed':False,'dates_queried':False,'profile_accepted':False}
 need(s.get('manifest')==manifest_ref,'layout-original-state-required')
 def save():nav.write_json(path,s)
 def request(c):
  reply=invoke(c);need(reply.get('ok') is True,'layout-bridge-request-failed:'+str(reply.get('error')));return reply['result']
 def observe():
  tab=nav.context(request({'op':'tabs'}),m['tab_id'],job['groupid']);tree=request({'op':'tree','tabId':m['tab_id']});after=nav.context(request({'op':'tabs'}),m['tab_id'],job['groupid'])
  need(tab['url']==after['url'] and tab.get('windowId')==after.get('windowId')==m['window_id'],'layout-current-context-changed')
  obs={'source':'local-dom-bridge','observed_at':nav.stamp(),'tab_id':m['tab_id'],'tab':after,'tree':tree};validate(obs,job);p=canonical/'evidence'/(uuid.uuid4().hex+'.json');nav.write_json(p,obs);s['observations'].append(ref(p));save();return obs
 obs=observe()
 if s.get('intent',{}).get('state')=='unknown':s['waiting_for']='original-layout-click-unknown-no-replay';save();return s
 if s['phase']=='complete':need(g.date_input(obs['tree']),'layout-legacy-date-input-required');return s
 if s['phase']=='prepared':
  fresh=target(obs['tree']);ping=request({'op':'ping','tabId':m['tab_id']})
  need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('content_build') in ACCEPTED_BUILDS and ping.get('governance_center_layout_policy')==MARKER,'layout-reviewed-hotbuild-required')
  current=nav.context(request({'op':'tabs'}),m['tab_id'],job['groupid']);need(current.get('windowId')==m['window_id'] and current['url']==obs['tab']['url'],'layout-before-input-scope-changed')
  command={'op':'click','tabId':m['tab_id'],'locator':{'by':'selector','value':fresh['selector']},'kind':'navigation'}
  s['intent']={'state':'unknown','key':m['key'],'command':command,'before':s['observations'][-1],'at':nav.stamp()};save()
  result=request(command);s['intent']['result']=result;save()
  need(result.get('clicked',{}).get('selector')==fresh['selector'] and result['clicked'].get('name')=='回到旧版','layout-click-reply-unverified')
  s['intent']['state']='confirmed';s['phase']='observe-legacy';save();obs=observe()
 try:date=g.date_input(obs['tree'])
 except ValueError:s['waiting_for']='legacy-layout-date-input-not-yet-observed';save();return s
 s.update(phase='complete',waiting_for=None,layout_result='legacy-layout-observed',date_input={'selector':date['selector']},after=s['observations'][-1]);save();return s

def run(manifest_ref,invoke=None):
 m=read(manifest_ref);job=read(m['job']);canonical=Path(m['job']['path']).parent/'.center-legacy-layout'/nav.tag(job)
 need(Path(manifest_ref['path'])==canonical/'manifest.json' and Path(m['state_path'])==canonical/'state.json','layout-canonical-path-required')
 with (canonical/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return _run_locked(manifest_ref,invoke)

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
 a=sub.add_parser('prepare');a.add_argument('--job',required=True);a.add_argument('--job-sha256',required=True);a.add_argument('--observation',required=True);a.add_argument('--observation-sha256',required=True);a.add_argument('--key',required=True)
 a=sub.add_parser('run');a.add_argument('--manifest',required=True);a.add_argument('--manifest-sha256',required=True);args=p.parse_args()
 if args.mode=='prepare':out=prepare({'path':str(Path(args.job).resolve()),'sha256':args.job_sha256},{'path':str(Path(args.observation).resolve()),'sha256':args.observation_sha256},args.key)
 else:out=run({'path':str(Path(args.manifest).resolve()),'sha256':args.manifest_sha256})
 print(json.dumps(out,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
