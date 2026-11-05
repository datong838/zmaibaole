#!/usr/bin/env python3
"""Public DOM profile discovery only. No date selection, data intake or progress.
Reviewed center actions require the supervisor-approved current safety version.
Calendar cells, actual records and detail/advice are observed, never guessed.
"""
import argparse,fcntl,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('violation_discovery_navigation',Path(__file__).with_name('bridge-navigation.py'));nav=importlib.util.module_from_spec(spec);spec.loader.exec_module(nav)
POLICY_VERSION=nav.VERSION
PLACEHOLDER='开始日期 ～ 结束日期'
MODES=('picker','records','all-reasons')
require=nav.require
def unique(items,code):
    require(len(items)==1,code);return items[0]

def classes(node):return set(node.get('attributes',{}).get('class','').split())
def descendants(node):return list(nav.nodes({'truncated':False,'root':node}))
def center_targets(tree,expected_identity):
    nav.identity(tree,expected_identity);require(tree.get('url')=='https://life.douyin.com'+nav.CENTER,'discovery-center-tree-required')
    ns=list(nav.nodes(tree));root=unique([n for n in ns if n.get('attributes',{}).get('id')=='governanceRoot'],'discovery-center-root-not-unique');rows=[]
    def walk(node,parents):
        rows.append((node,parents))
        for c in node.get('children',[]):walk(c,parents+[node])
    walk(root,[])
    def target(mode):
        found=[]
        for node,parents in rows:
            cs=classes(node)
            if mode=='picker':
                match=node.get('role')=='textbox' and node.get('tag')=='input' and node.get('placeholder')==PLACEHOLDER and 'governance_merchant-input' in cs and any({'governance_merchant-date-picker','governance_merchant-date-picker-range'}<=classes(p) for p in parents)
            elif mode=='records':
                item=next((p for p in reversed(parents) if 'todoItem-SQ0SNc' in classes(p)),None);tools=next((p for p in parents if 'todoSummary-xpJGcr' in classes(p)),None)
                match=node.get('name')=='违规记录' and node.get('tag')=='p' and 'todoLabel-I3rSqB' in cs and item is not None and tools is not None and tools.get('name','').startswith('常用工具 ') and re.fullmatch(r'违规记录 新增[0-9]+',item.get('name','')) is not None
                if not match and len(parents)>=3:
                    direct_item,direct_list,direct_tools=parents[-1],parents[-2],parents[-3]
                    match=(node.get('name')=='违规记录' and node.get('tag')=='p' and node.get('role')=='generic' and cs=={'compactLabel-aFEjMF'} and not node.get('children') and classes(direct_item)=={'compactItem-TpyZAq'} and classes(direct_list)=={'compactList-kThnsC'} and classes(direct_tools)=={'todoSummary-xpJGcr','compact-Gcf1ET','boardSuccess-tXR2Eq'} and re.fullmatch(r'违规记录 新增[0-9]+',direct_item.get('name','')) is not None)
            else:
                panel=next((p for p in parents if 'topList-DDjs8Y' in classes(p)),None)
                title=[n for n in descendants(panel) if n.get('name')=='违规原因 Top10' and 'title-KYD1nB' in classes(n)] if panel else []
                match=node.get('name')=='全部' and node.get('tag')=='span' and 'viewAllText-W89JWE' in cs and len(title)==1
            if match:found.append(node)
        result=unique(found,'discovery-observed-'+mode+'-target-not-unique');require(result.get('selector') and not result.get('disabled'),'discovery-target-not-ready');return result
    output={}
    for mode in MODES:
        try:output[mode]=target(mode)
        except ValueError as error:output[mode]={'gap':str(error)}
    return output

def review_observation(job,path,checksum):
    nav.scope(job);obs=nav.read_pinned(path,checksum);tab=obs['tab'];require(tab.get('tabId')==obs['tab_id'],'discovery-observation-tab-conflict');nav.context([{'tabs':[tab]}],obs['tab_id'],job['groupid'])
    targets=center_targets(obs['tree'],job['identity']);return {'source_observation':{'path':str(Path(path).resolve()),'sha256':checksum},'company':job['company'],'groupid':job['groupid'],'targets':targets,'expected_policy':POLICY_VERSION,'profile_accepted':False,'dates_queried':False,'business_progress_changed':False,'waiting_for':['observed治理calendar overlay/cell/month/confirm structure; no guessed date-cell class','date input public value not exposed by v7 bridge','all-reasons resulting view and complete pagination, not Top10 total','actual records route/filter/header/normal row structure and stable notice IDs','actual detail public recommendation separate from internal rules'],'actual_record_role':'unobserved; generic div must not be relabelled row'}

class Probe:
    def __init__(self,job,tab_id,file,mode,invoke=None):
        nav.scope(job);require(mode in MODES and type(tab_id) is int and tab_id>0,'discovery-mode-and-tab-required');self.job=job;self.tab=tab_id;self.file=Path(file).resolve();self.mode=mode;self.invoke=invoke or nav.bridge.request
        if self.file.exists():
            self.s=json.loads(self.file.read_text());require(self.s.get('fingerprint')==nav.tag(job) and self.s.get('tab_id')==tab_id and self.s.get('mode')==mode,'discovery-state-scope-conflict')
        else:self.s={'version':1,'fingerprint':nav.tag(job),'tab_id':tab_id,'mode':mode,'phase':'inspect-center','calls':[],'observations':[],'profile_accepted':False,'business_progress_changed':False,'dates_queried':False,'submission_enabled':False}
    def save(self):nav.write_json(self.file,self.s)
    def call(self,command):
        reply=self.invoke(command);require(reply.get('ok') is True,'discovery-bridge-command-failed:'+str(reply.get('error')));return reply['result']
    def observe(self):
        return nav.bounded_readonly_observation(self,self._observe_once,'records') if self.s['phase']=='observe-result' and self.mode=='records' else self._observe_once()
    def _observe_once(self):
        tab=nav.context(self.call({'op':'tabs'}),self.tab,self.job['groupid']);ping=self.call({'op':'ping','tabId':self.tab});tree=self.call({'op':'tree','tabId':self.tab});list(nav.nodes(tree));nav.identity(tree,self.job['identity'])
        after=nav.context(self.call({'op':'tabs'}),self.tab,self.job['groupid']);self._transition_sample={'before':tab,'after':after,'tree':tree};require(after['url']==tab['url'] and after.get('windowId')==tab.get('windowId'),'discovery-context-changed')
        from urllib.parse import urlsplit
        require(tree.get('url')=='https://life.douyin.com'+urlsplit(tab['url']).path,'discovery-tree-path-conflict')
        for node in nav.nodes(tree):require(not any(term in node.get('name','') for term in ('安全验证','风险验证','扫码登录','账号异常')),'discovery-risk-stop')
        path=self.file.parent/'profile-discovery-evidence'/(str(len(self.s['observations'])).zfill(3)+'-'+self.mode+'.json')
        obs={'source':'local-dom-bridge','observed_at':nav.stamp(),'tab_id':self.tab,'tab':tab,'tree':tree,'navigation_fingerprint':nav.tag(self.job),'not_business_capture':True};nav.write_json(path,obs);ref={'path':str(path),'sha256':nav.digest(path)};self.s['observations'].append(ref);self.s['last_observation']=ref;self.save();return obs,ping
    def step(self):
        if self.s['phase']=='profile-required':return self.s
        if any(c['state']=='unknown' for c in self.s['calls']):self.s['waiting_for']='original-action-outcome-unknown-no-replay';self.save();return self.s
        obs,ping=self.observe()
        if self.s['phase']=='observe-result':
            # Saving a post-action tree is not proof a picker or record list opened.
            self.s.update(phase='profile-required',waiting_for='review-real-'+self.mode+'-tree',picker_open_verified=False,records_open_verified=False,detail_profile_accepted=False);self.save();return self.s
        targets=center_targets(obs['tree'],self.job['identity']);target=targets[self.mode];require('gap' not in target,target.get('gap','discovery-target-missing'))
        self.s['observed_target']={'selector':target['selector'],'name':target.get('name'),'role':target.get('role'),'placeholder':target.get('placeholder')}
        if self.mode=='records' and classes(target)=={'compactLabel-aFEjMF'} and (ping.get('content_build') not in ('governance-center-compact-records-v1','governance-center-analysis-preflight-spacer-v2','normal-review-adjacent-pager-v1','normal-review-export-baseline-pager-v1','normal-review-export-terminal-prev-v2','exact-chongqing-company-discovery-v1','configured-exact-company-v2') or ping.get('governance_compact_records_policy')!='observed-compact-record-entry-v1'):
            self.s.update(waiting_for='reviewed-compact-record-entry-policy-required');self.save();return self.s
        if ping.get('version')!=POLICY_VERSION or ping.get('safety')!='DOM-only':
            self.s.update(waiting_for='reviewed-governance-current-policy-required',observed_version=ping.get('version'));self.save();return self.s
        command={'op':'click','tabId':self.tab,'locator':{'by':'selector','value':target['selector']},'kind':'filter' if self.mode=='picker' else 'navigation'}
        entry={'state':'unknown','command':command,'before':self.s['last_observation'],'intent_at':nav.stamp()};self.s['calls'].append(entry);self.save()
        entry['result']=self.call(command);entry['state']='confirmed';self.s.update(phase='observe-result',waiting_for='fresh-post-action-DOM');self.save();return self.s

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',type=Path,required=True);p.add_argument('--from-observation',type=Path);p.add_argument('--observation-sha256');p.add_argument('--out',type=Path);p.add_argument('--mode',choices=MODES);p.add_argument('--tab-id',type=int);p.add_argument('--state',type=Path);a=p.parse_args();job=json.loads(a.job.read_text())
    if a.from_observation:
        require(a.observation_sha256 and a.out,'discovery-pinned-observation-output-required');require(not a.out.exists(),'discovery-output-exists');result=review_observation(job,a.from_observation,a.observation_sha256);nav.write_json(a.out,result);print(json.dumps({'ok':True,'review':str(a.out.resolve()),'profile_accepted':False,'ui_operations':False}));return
    require(a.state and a.mode,'discovery-state-and-mode-required');a.state.parent.mkdir(parents=True,exist_ok=True)
    with a.state.with_name(a.state.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);probe=Probe(job,a.tab_id,a.state,a.mode)
        try:probe.step();probe.save();print(json.dumps({'phase':probe.s['phase'],'waiting_for':probe.s.get('waiting_for'),'journal':str(probe.file),'profile_accepted':False,'business_progress_changed':False},ensure_ascii=False))
        except Exception as error:probe.s['last_error']=str(error);probe.save();raise
if __name__=='__main__':
    try:main()
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'profile_accepted':False,'business_progress_changed':False},ensure_ascii=False));raise SystemExit(2)
