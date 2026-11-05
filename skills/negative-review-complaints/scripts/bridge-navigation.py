#!/usr/bin/env python3
"""Durable, reviewed UI navigation ONLY; stops after selecting negative reviews.
No capture ingestion, complaint action, submission, ledger update or messenger.
Actual normal-row/fold/pagination/full-text profile remains unaccepted.
"""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,fcntl,hashlib,importlib.util,json,sys
from pathlib import Path
from datetime import date,timedelta
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[3]
OPERATOR=ROOT/'skills/douyin-laike-operator/scripts'
sys.path.insert(0,str(OPERATOR))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dom_evidence import context,identity,nodes,exact,unique,review_filter_fields,calendar_day,all_store_scope,all_reviews,VERSION
from role_cli import write_json,digest
from normal_observation import navigation_probe
spec=importlib.util.spec_from_file_location('complaint_navigation_bridge',ROOT/'skills/chrome-dom-export/scripts/bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)

def require(ok,code):
    if not ok:raise ValueError(code)
def scope(job):
    require(job.get('company') and str(job.get('groupid','')).isdigit(),'navigation-company-required')
    require(job.get('account_verified') is True and isinstance(job.get('identity'),dict) and all(job['identity'].get(k) for k in ('provider','account_id','manager')),'navigation-identity-required')
    start=date.fromisoformat(job['start']);end=date.fromisoformat(job['end_exclusive']);require(start<end,'navigation-dates-invalid')
    return {'start':start.isoformat(),'end':(end-timedelta(days=1)).isoformat()}
def job_from_receipt(path,expected_id,expected_sha):
    path=Path(path).resolve();require(path.is_file() and digest(path)==expected_sha,'navigation-source-receipt-hash-mismatch')
    r=json.loads(path.read_text());require(r.get('work_order_id')==expected_id and expected_id,'navigation-current-source-work-order-required')
    require(r.get('operator_skill')=='douyin-laike-operator' and r.get('backend')=='local-dom-bridge' and r.get('download_verified') is True and r.get('source_is_authoritative_export') is True,'navigation-source-not-authoritative-current-bridge-export')
    require(r.get('account_verified') is True and r.get('identity')==r.get('identity_before'),'navigation-source-account-unverified')
    source=Path(r.get('source',''));require(source.is_absolute() and source.is_file() and not source.is_symlink() and source.suffix.lower()=='.xlsx','navigation-authoritative-file-required')
    require(digest(source)==r.get('src_sha256') and source.stat().st_size==r.get('bytes'),'navigation-source-file-changed')
    job={'company':r['company'],'groupid':str(r['groupid']),'start':r['date_range']['start'],'end_exclusive':(date.fromisoformat(r['date_range']['end'])+timedelta(days=1)).isoformat(),
         'account_verified':True,'identity':r['identity'],'source_work_order_id':expected_id,'source_receipt':str(path),'source_receipt_sha256':expected_sha}
    scope(job);require(digest(path)==expected_sha,'navigation-receipt-changed');return job

def tag(job):return hashlib.sha256(json.dumps(job,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
class Navigator:
    def __init__(self,job,tab_id,file,invoke=None):
        self.dates=scope(job);self.job=job;self.tab=tab_id;self.file=Path(file).resolve();self.invoke=invoke or bridge.request
        if self.file.exists():
            self.s=json.loads(self.file.read_text());require(self.s.get('fingerprint')==tag(job) and self.s.get('tab_id')==tab_id,'navigation-state-scope-conflict')
        else:self.s={'version':1,'fingerprint':tag(job),'tab_id':tab_id,'phase':'account','revision':0,'calls':[],'profile_accepted':False,'submission_enabled':False}
        if self.s['phase']=='profileRequired' and not self.s.get('stable_normal_verified'):
            self.s['phase']='observeNegative';self.s['profile_accepted']=False
    def set_text_schema(self,schema,expected_state_sha256):
        require(schema=='public-visible-text-v2','navigation-text-schema-invalid')
        require(self.file.is_file() and digest(self.file)==expected_state_sha256,'navigation-parser-state-hash-mismatch')
        require(self.s['phase']=='observeNegative' and not self.s.get('stable_normal_verified') and not self.s.get('stable_observations') and not self.s.get('normal_probe') and not self.s.get('stable_read_evidence'),'navigation-parser-upgrade-not-empty-observation')
        require(not self.s.get('parser_contract'),'navigation-parser-contract-already-bound')
        raw=self.file.read_bytes();backup=self.file.with_name(self.file.name+'.before-parser-'+expected_state_sha256+'.json')
        require(not backup.exists(),'navigation-parser-backup-exists');backup.write_bytes(raw)
        self.s['parser_contract']={'text_schema':schema,'job_fingerprint':tag(self.job),'previous_state_sha256':expected_state_sha256,'previous_state_path':str(backup),'scope':'readonly-normal-observation-only'}
        self.save()
    def save(self):write_json(self.file,self.s)
    def call(self,command):
        reply=self.invoke(command);require(reply.get('ok') is True,'navigation-bridge-command-failed:'+str(reply.get('error','unknown')));return reply['result']
    def click(self,target,op='click',kind='filter'):
        require(not target.get('disabled') and target.get('selector'),'navigation-target-disabled')
        key=str(self.s['revision'])+':'+self.s['phase'];command={'op':op,'tabId':self.tab,'locator':{'by':'selector','value':target['selector']},'kind':kind}
        previous=[x for x in self.s['calls'] if x['key']==key]
        if previous:
            previous=unique(previous);require(previous['command']==command,'navigation-intent-changed');require(previous['state']=='confirmed','navigation-outcome-unknown-no-replay');return
        entry={'key':key,'command':command,'state':'unknown'};self.s['calls'].append(entry);self.save()
        entry['result']=self.call(command);entry['state']='confirmed';self.save()
    def go(self,phase):self.s['phase']=phase;self.s['revision']+=1;self.save()
    def tick(self):
        if self.s['phase']=='profileRequired':return self.s
        tabs=self.call({'op':'tabs'});tab=context(tabs,self.tab,self.job['groupid'])
        entry_path=urlsplit(tab['url']).path
        require(entry_path=='/p/life_comment/management' or entry_path=='/p/home' and self.s['phase']=='account','review-management-navigation-required')
        ping=self.call({'op':'ping','tabId':self.tab});require(ping.get('version')==VERSION and ping.get('safety')=='DOM-only','reviewed-bridge-version-required')
        tree=self.call({'op':'tree','tabId':self.tab});list(nodes(tree))
        require(tree.get('url')=='https://life.douyin.com'+entry_path,'navigation-tree-path-mismatch')
        after=context(self.call({'op':'tabs'}),self.tab,self.job['groupid']);require(after['url']==tab['url'],'navigation-context-changed')
        self.s['read_sequence']=self.s.get('read_sequence',0)+1
        evidence=self.file.parent/'navigation-evidence'/(str(self.s['revision']).zfill(3)+'-'+self.s['phase']+'-read-'+str(self.s['read_sequence']).zfill(3)+'.json');write_json(evidence,tree)
        self.s['last_tree']={'path':str(evidence),'sha256':digest(evidence)};p=self.s['phase']
        if entry_path=='/p/home':
            if self.s.get('review_entry_dispatched'):
                self.s['waiting_for']='review-menu-navigation-settling';self.save();return self.s
            identity(tree,self.job['identity'])
            target=unique([n for n in nodes(tree) if n.get('name')=='评价管理' and not n.get('children') and 'navi_evaluation' in n.get('attributes',{}).get('class','').split()],'review-management-menu-unverified')
            self.click(target,kind='navigation');self.s['review_entry_dispatched']=True;self.go('account');return self.s
        if p in ('account','readAccount'):
            try:identity(tree,self.job['identity'])
            except ValueError as error:
                if str(error)=='account-changed' or p=='readAccount':raise
                trigger=unique([n for n in nodes(tree) if n.get('name')==self.job['identity']['provider'] and 'Profile-index-module__title--' in n.get('attributes',{}).get('class','')],'account-trigger-unverified')
                self.click(trigger,'hover','navigation');self.go('readAccount');return self.s
            self.go('inspectDate')
        elif p=='inspectDate':
            try:fields=review_filter_fields(tree)
            except ValueError as error:
                if not str(error).startswith('review-filter-unverified:'):raise
                require(not self.s.get('all_reviews_opened'),'review-list-not-ready-after-tab-selection')
                self.click(all_reviews(tree),kind='navigation');self.s['all_reviews_opened']=True;self.go('inspectDate');return self.s
            try:all_store_scope(tree)
            except ValueError:
                scope=unique([n for n in nodes(tree) if n.get('attributes',{}).get('id')=='CommentPoi_select'],'store-scope-unverified')
                if scope.get('name')!='按省市 0家门店':raise
                count=self.s.get('store_scope_loading_reads',0)+1
                require(count<=6,'store-scope-loading-exhausted')
                self.s['store_scope_loading_reads']=count;self.s['waiting_for']='store-scope-loading';self.save();return self.s
            self.s.pop('waiting_for',None)
            require(all(fields[k].get('attributes',{}).get('value')=='全部' for k in ('评价类型','评价来源','评价状态')),'navigation-nondefault-filter')
            self.go('negativeFilter' if fields['评价时间'].get('attributes',{}).get('value')==self.dates['start']+' ~ '+self.dates['end'] else 'openCalendar')
        elif p=='openCalendar':self.click(review_filter_fields(tree)['评价时间']);self.go('startDate')
        elif p=='startDate':self.click(calendar_day(tree,self.dates['start']));self.go('endDate')
        elif p=='endDate':self.click(calendar_day(tree,self.dates['end']));self.go('verifyDate')
        elif p=='verifyDate':
            require(review_filter_fields(tree)['评价时间'].get('attributes',{}).get('value')==self.dates['start']+' ~ '+self.dates['end'],'navigation-date-not-applied');self.go('negativeFilter')
        elif p=='negativeFilter':
            fields=review_filter_fields(tree);all_store_scope(tree)
            require(fields['评价时间'].get('attributes',{}).get('value')==self.dates['start']+' ~ '+self.dates['end'],'navigation-date-changed-before-filter')
            require(all(fields[k].get('attributes',{}).get('value')=='全部' for k in ('评价类型','评价来源','评价状态')),'navigation-nondefault-filter')
            target=exact(tree,'中差评（1-3心）');attrs=target.get('attributes',{})
            if attrs.get('aria-selected')=='true' or attrs.get('aria-pressed')=='true' or set(attrs.get('class','').split())=={'option-YmRyn3','isSelected-ov8pOi'}:self.go('observeNegative')
            else:
                # This exact unselected class was observed in Yantai107 source DOM.
                require(set(attrs.get('class','').split())=={'option-YmRyn3'},'negative-active-state-needs-live-profile')
                self.click(target);self.go('observeNegative')
        elif p=='observeNegative':
            if self.s.get('observe_attempts',0)>=8 and not self.s.get('settled_list_read_recovered'):
                contract=self.s.get('parser_contract',{})
                try:navigation_probe(tree,self.job,text_schema=contract.get('text_schema'),image_only_text_schema=contract.get('image_only_text_schema'))
                except (ValueError,KeyError,OSError):pass
                else:self.s['observe_attempts']=0;self.s['settled_list_read_recovered']=True
            self.s['observe_attempts']=self.s.get('observe_attempts',0)+1
            require(self.s['observe_attempts']<=8,'normal-list-stability-attempt-limit')
            try:
                contract=self.s.get('parser_contract',{})
                require(not contract or contract.get('job_fingerprint')==tag(self.job) and contract.get('text_schema')=='public-visible-text-v2','navigation-parser-contract-scope-mismatch')
                probe=navigation_probe(tree,self.job,**({'text_schema':contract['text_schema'],**({'image_only_text_schema':contract['image_only_text_schema']} if contract.get('image_only_text_schema') else {})} if contract else {}));fingerprint=hashlib.sha256(json.dumps(probe,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            except (ValueError,KeyError,OSError) as error:
                self.s['stable_observations']=0;self.s.pop('normal_fingerprint',None);self.s['waiting_for']='normal-list-not-stable:'+str(error);self.save();return self.s
            if probe.get('normal_scope_mode')=='pending-normal-multipage':
                self.s['stable_observations']=0;self.s.pop('normal_fingerprint',None);self.s.pop('normal_probe',None)
                self.s['normal_paging_required']=probe;self.s['waiting_for']='normal-pages-profile-required';self.save();return self.s
            self.s['stable_observations']=self.s.get('stable_observations',0)+1 if self.s.get('normal_fingerprint')==fingerprint else 1
            self.s['normal_fingerprint']=fingerprint;self.s['normal_probe']=probe
            self.s.setdefault('stable_read_evidence',[]).append(dict(self.s['last_tree'],fingerprint=fingerprint))
            if self.s['stable_observations']<2:self.s['waiting_for']='second-identical-normal-negative-observation';self.save();return self.s
            self.s['stable_normal_verified']=True
            self.s['waiting_for']='live-normal-negative-list-profile';self.s['requirements']=['active negative CSS/ARIA state','normal row boundary and filtered count','full normal-row original text and expansion controls','all normal pages/next disabled proof','complaint action/result overlay','past 7 days other-category complaint history entry']
            self.go('profileRequired')
        else:raise ValueError('navigation-phase-invalid')
        return self.s

def main():
    ap=argparse.ArgumentParser(description=__doc__);source=ap.add_mutually_exclusive_group(required=True);source.add_argument('--job',type=Path);source.add_argument('--receipt',type=Path)
    ap.add_argument('--receipt-sha256');ap.add_argument('--source-work-order-id');ap.add_argument('--prepare-job',type=Path);ap.add_argument('--tab-id',type=int);ap.add_argument('--state',type=Path);ap.add_argument('--text-schema',choices=['public-visible-text-v2']);ap.add_argument('--expected-state-sha256');a=ap.parse_args()
    if a.receipt:
        require(a.receipt_sha256 and a.source_work_order_id,'source-id-and-receipt-hash-required')
        job=job_from_receipt(a.receipt,a.source_work_order_id,a.receipt_sha256)
    else:job=json.loads(a.job.read_text());scope(job)
    if a.prepare_job:
        require(not a.prepare_job.exists(),'navigation-job-output-exists');write_json(a.prepare_job,job);print(json.dumps({'ok':True,'job':str(a.prepare_job.resolve()),'ledger_changed':False}));return 0
    require(a.state and type(a.tab_id) is int and a.tab_id>0,'explicit-tab-and-navigation-state-required')
    a.state=a.state.resolve();a.state.parent.mkdir(parents=True,exist_ok=True)
    with a.state.with_name(a.state.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        n=Navigator(job,a.tab_id,a.state)
        if a.text_schema:n.set_text_schema(a.text_schema,a.expected_state_sha256)
        else:require(not a.expected_state_sha256,'navigation-parser-schema-required')
        try:n.tick();n.save();print(json.dumps(n.s,ensure_ascii=False));return 0
        except Exception as error:n.s['last_error']=str(error);n.save();print(json.dumps({'ok':False,'error':str(error),'submission_enabled':False},ensure_ascii=False));return 2
if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as error:print(json.dumps({'ok':False,'error':str(error),'submission_enabled':False},ensure_ascii=False));raise SystemExit(2)
