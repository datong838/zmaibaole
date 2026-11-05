"""One observed center analysis tab; no date/query/data mutation or guessed URL.
Proposed caller: prepare original refs, then run same canonical manifest to ensure analysis view. No UI here
unless run is explicitly invoked by the authorized operator after reviewed hotbuild.
"""
import argparse,fcntl,hashlib,importlib.util,json,sys,uuid
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
spec=importlib.util.spec_from_file_location('legacy_layout_nav',ROOT/'skills/violation-notifier/scripts/bridge-navigation.py');nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
import governance_dom as g
MARKER='observed-analysis-tab-v1';BUILD='governance-center-analysis-tab-v1'
ACCEPTED_BUILDS=(BUILD,'configured-exact-company-v2','governance-center-compact-records-v1','governance-center-analysis-preflight-spacer-v2','normal-review-adjacent-pager-v1','normal-review-export-baseline-pager-v1','normal-review-export-terminal-prev-v2','exact-chongqing-company-discovery-v1')
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

def tabs(tree):
 rows=[]
 def visit(n,parents):
  rows.append((n,parents))
  for c in n.get('children',[]):visit(c,parents+[n])
 visit(tree['root'],[]);root=one([n for n,_ in rows if n.get('attributes',{}).get('id')=='governanceRoot'],'analysis-root-not-unique')
 cls=lambda n:set(n.get('attributes',{}).get('class','').split())
 pair=one([n for n,p in rows if cls(n)=={'governance_merchant-tab-bar-items-inner'} and root in p and any(c.get('tag')=='div' and 'governance_merchant-tab-bar-item' in cls(c) and c.get('name') in ('违规分析','违规预防') for c in n.get('children',[]))],'analysis-tab-pair-not-unique')
 parents=next(p for n,p in rows if n is pair)
 need(parents and cls(parents[-1])=={'governance_merchant-tab-bar-items-container'} and len(pair.get('children',[])) in (3,4),'analysis-tab-pair-shape-invalid')
 analysis,prevent=pair['children'][:2];decorations=pair['children'][2:]
 if len(decorations)==2:
  spacer=decorations[0];need(spacer.get('tag')=='span' and spacer.get('role')=='generic' and cls(spacer)=={'governance_merchant-tab-bar-item-span'} and spacer.get('name','')=='' and not spacer.get('children'),'analysis-tab-spacer-invalid')
 inert=lambda n:not n.get('disabled') and not any(k in n.get('attributes',{}) for k in ('tabindex','contenteditable','href','onclick','onkeydown','onpointerdown'))
 for decoration in decorations:need(inert(decoration),'analysis-tab-decoration-interactive')
 line=decorations[-1];need(line.get('tag')=='div' and line.get('role')=='generic' and cls(line)=={'governance_merchant-tab-bar-items-inner-line'} and line.get('name','')=='' and not line.get('children'),'analysis-tab-indicator-invalid');base={'governance_merchant-tab-bar-item','governance_merchant-tab-bar-item-type-basic'};active='governance_merchant-tab-bar-item-active'
 for n,label in ((analysis,'违规分析'),(prevent,'违规预防')):
  need(n.get('tag')=='div' and n.get('role')=='generic' and n.get('name')==label and cls(n) in (base,base|{active}) and not n.get('disabled') and n.get('selector') and len(n.get('children',[]))==1,'analysis-tab-shape-invalid')
  child=n['children'][0];need(child.get('tag')=='span' and cls(child)=={'governance_merchant-tab-bar-item-label'} and child.get('name')==label and not child.get('children'),'analysis-tab-label-invalid')
  need(not any(p.get('tag') in ('form','a','dialog') or p.get('role')=='dialog' for p in parents),'analysis-tab-unsafe-ancestor')
 aa=active in cls(analysis);pa=active in cls(prevent);need(aa!=pa,'analysis-tab-single-active-required')
 return {'analysis':analysis,'analysis_active':aa,'prevention_active':pa,'click_shape_verified':True}
def target(tree):
 state=tabs(tree);need(state['click_shape_verified'],'analysis-tab-click-shape-unreviewed');need(state['prevention_active'] and not state['analysis_active'],'analysis-tab-original-prevention-required');return state['analysis']
def ready(tree):
 state=tabs(tree);need(state['analysis_active'] and not state['prevention_active'],'analysis-tab-not-active');return g.date_input(tree)

def prepare(job_ref,observation_ref,key):
 job=read(job_ref);before=read(observation_ref);validate(before,job);original=tabs(before['tree']);ready(before['tree']) if original['analysis_active'] else None;need(isinstance(key,str) and key.strip() and len(key)<=100,'layout-stable-key-required')
 folder=Path(job_ref['path']).parent/'.center-analysis-tab'/nav.tag(job);folder.mkdir(parents=True,exist_ok=True)
 m={'kind':'center-analysis-display-tab-navigation-v1','job':job_ref,'before':observation_ref,'tab_id':before['tab_id'],'window_id':before['tab']['windowId'],'key':key,'state_path':str(folder/'state.json')};mp=folder/'manifest.json'
 if mp.exists():need(json.loads(mp.read_text())==m,'layout-original-manifest-required')
 else:nav.write_json(mp,m)
 return ref(mp)

def _run_locked(manifest_ref,invoke=None):
 invoke=invoke or nav.bridge.request;m=read(manifest_ref);need(m.get('kind')=='center-analysis-display-tab-navigation-v1','layout-manifest-kind-invalid');job=read(m['job']);before=read(m['before']);validate(before,job);original=tabs(before['tree']);ready(before['tree']) if original['analysis_active'] else None;need(m['tab_id']==before['tab_id'] and m['window_id']==before['tab']['windowId'],'layout-original-context-conflict')
 canonical=Path(m['job']['path']).parent/'.center-analysis-tab'/nav.tag(job)
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
 if s['phase']=='complete':ready(obs['tree']);return s
 if s['phase']=='prepared':
  current_tabs=tabs(obs['tree'])
  if current_tabs['analysis_active']:
   date=ready(obs['tree']);s.update(phase='complete',waiting_for=None,layout_result='analysis-tab-already-ready-readonly',date_input={'selector':date['selector']},after=s['observations'][-1]);save();return s
  fresh=target(obs['tree']);ping=request({'op':'ping','tabId':m['tab_id']})
  need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('content_build') in ACCEPTED_BUILDS and ping.get('governance_analysis_tab_policy')==MARKER,'layout-reviewed-hotbuild-required')
  current=nav.context(request({'op':'tabs'}),m['tab_id'],job['groupid']);need(current.get('windowId')==m['window_id'] and current['url']==obs['tab']['url'],'layout-before-input-scope-changed')
  command={'op':'click','tabId':m['tab_id'],'locator':{'by':'selector','value':fresh['selector']},'kind':'navigation'}
  s['intent']={'state':'unknown','key':m['key'],'command':command,'before':s['observations'][-1],'at':nav.stamp()};save()
  result=request(command);s['intent']['result']=result;save()
  need(result.get('clicked',{}).get('selector')==fresh['selector'] and result['clicked'].get('name')=='违规分析','layout-click-reply-unverified')
  s['intent']['state']='confirmed';s['phase']='observe-analysis';save();obs=observe()
 try:date=ready(obs['tree'])
 except ValueError as error:
  if str(error)!='analysis-tab-not-active':raise
  s['waiting_for']='analysis-tab-not-yet-active';save();return s
 s.update(phase='complete',waiting_for=None,layout_result='analysis-tab-and-date-input-observed',date_input={'selector':date['selector']},after=s['observations'][-1]);save();return s

def run(manifest_ref,invoke=None):
 m=read(manifest_ref);job=read(m['job']);prior=Path(m['job']['path']).parent/'.center-legacy-layout'/nav.tag(job)/'state.json'
 if prior.exists():need(json.loads(prior.read_text()).get('intent',{}).get('state')!='unknown','analysis-original-layout-intent-unknown')
 canonical=Path(m['job']['path']).parent/'.center-analysis-tab'/nav.tag(job)
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

# Called only from the canonical query Runner before CENTER open-date, never
# DetailProbe/recovery/date-selection phases. This is not a generic retry route.
def ensure_query_analysis(owner,tree):
 current=read(owner.s['last_observation']);need(current['tree']==tree,'analysis-preflight-fresh-observation-mismatch')
 if urlsplit(current['tab']['url']).path!=nav.CENTER:return True
 need(current['tab_id']==owner.tab and current['tab'].get('windowId') is not None,'analysis-preflight-current-scope-required')
 ns=list(nav.nodes(tree));classes=lambda n:set(n.get('attributes',{}).get('class','').split())
 has_basic=any('governance_merchant-tab-bar-item-type-basic' in classes(n) or ('governance_merchant-tab-bar-items-inner' in classes(n) and any(c.get('name') in ('违规分析','违规预防') for c in n.get('children',[]))) for n in ns)
 job_ref=getattr(owner,'navigation_job_ref',None)
 if not job_ref:
  need(not has_basic and not owner.s.get('analysis_preflight',{}).get('manifest'),'analysis-preflight-original-job-ref-required')
  g.date_input(tree);return True # Existing strict non-pair legacy shape only.
 need(read(job_ref)==owner.job,'analysis-preflight-original-job-ref-conflict');validate(current,owner.job)
 canonical=Path(job_ref['path']).parent/'.center-analysis-tab'/nav.tag(owner.job);legacy=Path(job_ref['path']).parent/'.center-legacy-layout'/nav.tag(owner.job)/'state.json'
 if legacy.exists():
  old=json.loads(legacy.read_text());need(old.get('intent',{}).get('state')!='unknown' and not any(c.get('state')=='unknown' for c in old.get('calls',[])),'analysis-original-layout-intent-unknown')
 mp=canonical/'manifest.json';sp=canonical/'state.json';need(not sp.exists() or mp.exists(),'analysis-preflight-original-manifest-missing')
 manifest_ref=ref(mp) if mp.exists() else None
 if manifest_ref:
  m=read(manifest_ref);need(m.get('job')==job_ref and m.get('tab_id')==owner.tab and m.get('window_id')==current['tab']['windowId'] and m.get('state_path')==str(sp),'analysis-preflight-canonical-manifest-conflict')
  recorded=owner.s.get('analysis_preflight',{}).get('manifest');need(not recorded or recorded==manifest_ref,'analysis-preflight-original-manifest-changed')
  if sp.exists():
   prior=json.loads(sp.read_text());need(prior.get('manifest')==manifest_ref,'analysis-preflight-original-state-conflict');intent=prior.get('intent',{});need(intent.get('state')!='unknown','analysis-preflight-original-analysis-unknown');need(prior.get('phase') in ('prepared','observe-analysis','complete') and (not intent or intent.get('state')=='confirmed' and prior['phase'] in ('observe-analysis','complete')),'analysis-preflight-original-state-unreviewed')
 # Do not catch a malformed/ambiguous pair and fall back to legacy or another UI.
 state=tabs(tree) if has_basic else None
 if state is None:
  need(manifest_ref is None,'analysis-preflight-existing-analysis-scope-missing');g.date_input(tree);return True
 if state['analysis_active'] and not manifest_ref:
  date=ready(tree);owner.s['analysis_preflight']={'state':'fresh-analysis-ready-readonly','job':job_ref,'before':owner.s['last_observation'],'date_input':{'selector':date['selector']},'manifest':None};owner.save();return True
 if manifest_ref is None:
  target(tree);manifest_ref=prepare(job_ref,owner.s['last_observation'],'query-analysis-'+nav.tag(owner.job)[:24])
 owner.s['analysis_preflight']={'state':'original-adapter-bound-before-run','job':job_ref,'before':owner.s['last_observation'],'manifest':manifest_ref};owner.save()
 result=run(manifest_ref,owner.invoke);owner.s['analysis_preflight'].update(state=result['phase'],adapter_state=ref(sp),after=result.get('after'),waiting_for=result.get('waiting_for'));owner.save()
 if not state['analysis_active'] or result['phase']!='complete':
  owner.s['waiting_for']='fresh-analysis-observation-before-date' if result['phase']=='complete' else result.get('waiting_for','analysis-display-awaiting-readonly');owner.save();return False
 ready(tree);owner.s.pop('waiting_for',None);owner.save();return True
