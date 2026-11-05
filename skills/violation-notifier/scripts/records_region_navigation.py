#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Source-bound records screenshot navigation. No detail/business-state writes."""
import argparse,fcntl,json,os,re,hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
import prepare_records_profile as profile_api
import governance_detail as d
import governance_dom as g
from governance_rates_recovery import target_page_command
need=g.need
SCHEMA='records-region-navigation-v1'

def pending_frames(source):
    base=Path(source['path']).resolve().parent
    need(base.name.isdigit() and base.parent.name=='companies','records-navigation-current-role-source-required')
    chain='violation-'+base.parent.parent.name[:24]+'-'+base.name
    fingerprint=hashlib.sha256(json.dumps([source['sha256'],chain],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    path=base/'.native-region-frame-state'/(fingerprint+'.json')
    if not path.exists():return None
    state=json.loads(path.read_text());need(state.get('scope',{}).get('source_sha256')==source['sha256'],'records-navigation-current-capture-source')
    current=state.get('frames',[])[-1:]
    if current and current[0].get('state')!='complete':return {'journal':str(path),'state':current[0].get('state')}
    return None

class Runner:
    def __init__(self,source,profile,invoke=None,profile_pair=None,screenshot_anchor=None):
        self.screenshot_anchor=screenshot_anchor
        self.profile_pair=None;self.profile_pair_ref=profile_pair
        if profile_pair is not None:
            import prepare_records_capture_order as pair
            self.profile_pair=pair.validate(profile_pair,source,profile)
        self.source=source;self.profile_ref=profile;self.profile=d.document(profile);profile_api.validate(self.profile,source)
        meta=self.profile['derivation'];self.job=d.document(meta['job']);self.query=d.document(meta['query']);self.tab=meta['tab_id'];self.window=meta['window_id'];self.invoke=invoke or d.nav.bridge.request
        self.folder=Path(source['path']).resolve().parent/'.records-region-navigation'/source['sha256']
        if meta.get('kind')=='governance-records-reboot-derived-profile-v1':
            import violation_reboot_profile as reboot
            self.folder=reboot.nav_root(self.profile,source)
        self.folder.mkdir(parents=True,exist_ok=True)
        self.file=self.folder/'state.json';self.binding={'schema':SCHEMA,'source':source,'profile':profile,'job':meta['job'],'query':meta['query'],'tab_id':self.tab,'window_id':self.window}
        self.s=json.loads(self.file.read_text()) if self.file.exists() else {'binding':self.binding,'observations':[],'operations':[],'business_progress_changed':False}
        need(self.s['binding']==self.binding,'records-navigation-original-binding-required')
    def identity(self,raw):
        if self.screenshot_anchor is None:return d.nav.identity(raw['tree'],self.job['identity'])
        import screenshot_identity as identity
        capture_ref=self.profile_pair['capture_profile_ref'] if self.profile_pair else d.document(self.screenshot_anchor)['profile']
        capture=d.document(capture_ref);need({k:v for k,v in capture.items() if k!='evidence_contract'}=={k:v for k,v in self.profile.items() if k!='evidence_contract'},'records-navigation-anchor-profile-scope-changed')
        return identity.current(self.screenshot_anchor,self.source,capture_ref,raw)
    def save(self):
        temp=self.file.with_suffix('.tmp')
        with temp.open('w',encoding='utf-8') as f:json.dump(self.s,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(temp,self.file)
    def request(self,c):
        r=self.invoke(c);need(r.get('ok') is True,'records-navigation-bridge-failed:'+str(r.get('error')));return r['result']
    def observe(self):
        # Recheck immutable refs, but never instantiate the completed detail runner.
        for ref in (self.source,self.profile_ref,self.binding['job'],self.binding['query']):d.document(ref)
        if self.profile_pair_ref is not None:d.document(self.profile_pair_ref);d.document(self.profile_pair['capture_profile_ref'])
        before=d.nav.context(self.request({'op':'tabs'}),self.tab,self.job['groupid']);ping=self.request({'op':'ping','tabId':self.tab});need(ping.get('version')==d.nav.VERSION and ping.get('safety')=='DOM-only','records-navigation-unreviewed-version')
        tree=self.request({'op':'tree','tabId':self.tab});after=d.nav.context(self.request({'op':'tabs'}),self.tab,self.job['groupid'])
        need(before['url']==after['url'] and before['windowId']==after['windowId']==self.window and urlsplit(after['url']).path==g.RECORDS and tree['url']=='https://life.douyin.com'+g.RECORDS,'records-navigation-tab-window-route-changed')
        self.identity({'source':'local-dom-bridge','tab_id':self.tab,'tab':after,'tree':tree});page=d.normal_page(tree,self.job,self.query)
        for n in g.nodes(tree):need(not any(x in n.get('name','') for x in ('扫码登录','风险验证','安全验证','账号异常')),'records-navigation-risk-stop')
        folder=self.folder/'evidence';folder.mkdir(exist_ok=True);path=folder/(__import__('uuid').uuid4().hex+'.json')
        raw={'source':'local-dom-bridge','observed_at':d.nav.stamp(),'tab_id':self.tab,'tab':after,'tree':tree,'not_business_capture':True};d.exclusive(path,raw);ref=d.ref(path);self.s['observations'].append(ref);self.s['last_observation']=ref;self.save();return raw,page
    def run(self,action,*,key=None,page=None,notice_id=None):
        with self.file.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            # Reload under lock, preventing two stale instances issuing the same intent.
            if self.file.exists():self.s=json.loads(self.file.read_text());need(self.s['binding']==self.binding,'records-navigation-binding-changed')
            raw,current=self.observe()
            if action=='observe':return self.output('observed',current)
            need(action in ('page','row','anchor') and isinstance(key,str) and re.fullmatch(r'[A-Za-z0-9_.:-]{8,128}',key),'records-navigation-action-key-invalid')
            spec={'action':action,'page':page,'notice_id':notice_id}
            old=[x for x in self.s['operations'] if x['key']==key]
            if old:
                op=g.one(old,'records-navigation-key-duplicate');need(op['request']==spec,'records-navigation-key-conflict')
                if op['state']=='complete':return self.output('complete',current,op)
                # An issued request with no validated response can only be observed.
                if op['state']=='unknown':return self.output('unknown-readonly-hold',current,op)
                need(op['state']=='confirmed','records-navigation-state-unreviewed')
                return self.finish(op,raw,current)
            need(all(x['state']=='complete' for x in self.s['operations']),'records-navigation-prior-unresolved-no-new-key')
            need(pending_frames(self.source) is None,'records-navigation-capture-frame-unresolved')
            if action=='page':
                need(isinstance(page,int) and page in [x['page'] for x in self.query['pages']] and notice_id is None,'records-navigation-page-not-in-source')
                command=None if current['page']==page else target_page_command(raw['tree'],page)
            elif action=='row':
                need(page is None and notice_id in [x['notice_id'] for x in self.query['rows']],'records-navigation-notice-not-in-source')
                row=g.one([x for x in current['rows'] if x['notice_id']==notice_id],'records-navigation-notice-not-on-current-page');command={'op':'scroll','locator':{'by':'selector','value':row['selector']}}
            else:
                need(page is None and notice_id is None,'records-navigation-anchor-arguments-invalid');command={'op':'scroll','locator':{'by':'selector','value':g.date_input(raw['tree'])['selector']}}
            op={'key':key,'request':spec,'state':'complete' if command is None else 'unknown','before':self.s['last_observation'],'before_page':current['page'],'intent_at':d.nav.stamp(),'command':None if command is None else {**command,'tabId':self.tab}};self.s['operations'].append(op);self.save()
            if command is None:return self.output('complete',current,op)
            # Persist the full received envelope before interpreting any reply.
            reply=self.invoke(op['command']);op.update(raw_reply=reply,response_at=d.nav.stamp());self.save()
            need(reply.get('ok') is True,'records-navigation-bridge-failed:'+str(reply.get('error')));result=reply['result'];op['result']=result;self.save()
            if action=='page':d.reply_matches(op['command'],result,raw)
            else:self.scroll_reply(op,raw)
            op.update(state='confirmed',result=result);self.save();fresh,parsed=self.observe();return self.finish(op,fresh,parsed)
    def normal(self,raw):
        need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==self.tab,'records-navigation-original-observation-required')
        tab=d.nav.context([{'tabs':[raw['tab']]}],self.tab,self.job['groupid']);need(tab['windowId']==self.window and urlsplit(tab['url']).path==g.RECORDS and raw['tree']['url']=='https://life.douyin.com'+g.RECORDS,'records-navigation-original-observation-scope-changed');self.identity(raw);return d.normal_page(raw['tree'],self.job,self.query)
    def scroll_reply(self,op,before):
        page=self.normal(before);command=op['command'];need(command.get('op')=='scroll' and command.get('tabId')==self.tab and page['page']==op['before_page'],'records-navigation-original-scroll-command-changed')
        node=g.one([n for n in g.nodes(before['tree']) if n.get('selector')==command['locator']['value']],'records-navigation-original-scroll-target-missing')
        if op['request']['action']=='row':
            row=g.one([r for r in page['rows'] if r['notice_id']==op['request']['notice_id']],'records-navigation-original-scroll-notice-missing');need(row['selector']==node['selector'] and node['tag']=='tr','records-navigation-original-scroll-row-changed')
        else:need(op['request']['action']=='anchor' and node['selector']==g.date_input(before['tree'])['selector'],'records-navigation-original-scroll-anchor-changed')
        reply=op['result'];scrolled=reply.get('scrolled',{})
        # Aggregate TR.name contains non-source appeal countdown text. Business
        # semantics are re-parsed from all nine source fields before and after.
        need(reply.get('version')==d.nav.VERSION and all(scrolled.get(k)==node.get(k) for k in ('selector','tag')),'records-navigation-scroll-reply-unverified')
    def reconcile_scroll(self,key,expected_sha,after_ref,proof_ref):
        need(self.profile_pair is not None,'records-navigation-reconcile-original-profile-pair-required')
        with self.file.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);original=self.file.read_bytes();need(hashlib.sha256(original).hexdigest()==expected_sha,'records-navigation-reconcile-original-journal-sha-required');self.s=json.loads(original);need(self.s['binding']==self.binding,'records-navigation-binding-changed')
            op=g.one([o for o in self.s['operations'] if o.get('key')==key],'records-navigation-reconcile-original-key-required');need(op.get('state')=='unknown' and op.get('request',{}).get('action')=='row' and op.get('command',{}).get('op')=='scroll' and 'result' not in op and 'raw_reply' not in op,'records-navigation-reconcile-only-original-lost-reply-row-scroll')
            need(all(o is op or o.get('state')=='complete' for o in self.s['operations']) and pending_frames(self.source) is None,'records-navigation-reconcile-other-unresolved')
            need(after_ref==self.s.get('last_observation') and after_ref in self.s.get('observations',[]) and Path(after_ref['path']).resolve().parent==self.folder/'evidence' and op['before'] in self.s.get('observations',[]),'records-navigation-reconcile-canonical-observations-required')
            before=d.document(op['before']);after=d.document(after_ref);bp=self.normal(before);ap=self.normal(after)
            need(ap['page']==bp['page']==op['before_page'] and op['command'].get('tabId')==self.tab,'records-navigation-reconcile-page-or-tab-changed')
            target=g.one([r for r in bp['rows'] if r['notice_id']==op['request']['notice_id']],'records-navigation-reconcile-original-notice-required');need(op['command']['locator']=={'by':'selector','value':target['selector']} and op['request'].get('page') is None,'records-navigation-reconcile-original-row-selector-required')
            need(datetime.fromisoformat(after['observed_at'].replace('Z','+00:00'))>=datetime.fromisoformat(op['intent_at'].replace('Z','+00:00')),'records-navigation-reconcile-observation-predates-intent')
            import business_cells_capture as business
            inputs=profile_api.fc.page_inputs(self.source,after_ref,self.profile_pair['capture_profile_ref']);raw_proof=d.document(proof_ref)
            if 'reply' in raw_proof:
                need(raw_proof.get('command')==inputs['command'] and raw_proof.get('observation')==after_ref and raw_proof.get('input_actions_used') is False,'records-navigation-reconcile-proof-command-observation-changed');raw_proof=raw_proof['reply']
            need(raw_proof.get('ok') is True and isinstance(raw_proof.get('result'),dict),'records-navigation-reconcile-public-proof-envelope-required');proof=business.validate_base(raw_proof['result'],inputs)
            row=g.one([r for r in proof['business_cells'] if r['notice_id']==target['notice_id']],'records-navigation-reconcile-proof-notice-required');need(row['tr_selector']==target['selector'] and len(row['cells'])==5 and all(c['geometry']['rendered'] and c['geometry']['box_viewport_contained'] for c in row['cells']),'records-navigation-reconcile-target-five-cells-not-in-view')
            # No bridge invocation and no fabricated API reply. Preserve original
            # journal bytes before appending the one explicit readonly repair.
            folder=self.folder/'reconciliations';folder.mkdir(exist_ok=True);archive=folder/(expected_sha+'-original.json')
            if archive.exists():need(archive.read_bytes()==original,'records-navigation-reconcile-original-archive-conflict')
            else:
                with archive.open('xb') as f:f.write(original);f.flush();os.fsync(f.fileno())
            evidence={'kind':'readonly-scroll-effect-reconciled','original_journal':d.ref(archive),'original_operation':json.loads(json.dumps(op)),'after':after_ref,'public_viewport_proof':proof_ref,'profile_pair':self.profile_pair_ref,'target_notice_id':target['notice_id'],'target_selector':target['selector'],'API_reply_observed':False,'input_replayed':False,'region_coverage_verified':False,'screenshot_permission_verified':False,'target_cell_geometry':[{'field':c['field'],'geometry':c['geometry']} for c in row['cells']]}
            op.update(state='complete',completion_kind='readonly-scroll-effect-reconciled',reconciliation=evidence,after=after_ref,completed_at=d.nav.stamp());self.save();return self.output('readonly-scroll-effect-reconciled',ap,op)
    def finish(self,op,raw,page):
        before=d.document(op['before'])
        if op['request']['action']=='page':d.reply_matches(op['command'],op['result'],before)
        else:self.scroll_reply(op,before)
        target=op['request']['page'] if op['request']['action']=='page' else op['before_page']
        if page['page']!=target:return self.output('confirmed-awaiting-readonly-effect',page,op)
        op.update(state='complete',after=self.s['last_observation'],completed_at=d.nav.stamp());self.save();return self.output('complete',page,op)
    def output(self,status,page,op=None):return {'ok':True,'status':status,'journal':d.ref(self.file),'observation':self.s['last_observation'],'page':page['page'],'notice_ids':[x['notice_id'] for x in page['rows']],'operation':op,'viewport_visibility_verified':False,'business_progress_changed':False,**({'navigation_profile_ref':self.profile_pair['navigation_profile_ref'],'capture_profile_ref':self.profile_pair['capture_profile_ref']} if self.profile_pair else {})}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('source','source-sha256','profile','profile-sha256'):p.add_argument('--'+k,required=True)
    p.add_argument('--screenshot-anchor');p.add_argument('--screenshot-anchor-sha256');p.add_argument('--action',required=True,choices=('observe','page','row','anchor','reconcile-scroll'));p.add_argument('--key');p.add_argument('--expected-journal-sha256');p.add_argument('--observation');p.add_argument('--observation-sha256');p.add_argument('--viewport-proof');p.add_argument('--viewport-proof-sha256');p.add_argument('--page',type=int);p.add_argument('--notice-id');p.add_argument('--profile-pair');p.add_argument('--profile-pair-sha256');a=p.parse_args()
    try:
        need(bool(a.screenshot_anchor)==bool(a.screenshot_anchor_sha256),'records-navigation-anchor-incomplete')
        need(bool(a.profile_pair)==bool(a.profile_pair_sha256),'records-navigation-profile-pair-ref-incomplete')
        ref=lambda k:{'path':str(Path(getattr(a,k)).resolve()),'sha256':getattr(a,k+'_sha256')};runner=Runner(ref('source'),ref('profile'),profile_pair=ref('profile_pair') if a.profile_pair and a.profile_pair_sha256 else None,screenshot_anchor=ref('screenshot_anchor') if a.screenshot_anchor else None)
        if a.action=='reconcile-scroll':
            need(all((a.key,a.expected_journal_sha256,a.observation,a.observation_sha256,a.viewport_proof,a.viewport_proof_sha256)) and a.page is None and a.notice_id is None,'records-navigation-reconcile-explicit-refs-required');result=runner.reconcile_scroll(a.key,a.expected_journal_sha256,ref('observation'),ref('viewport_proof'))
        else:result=runner.run(a.action,key=a.key,page=a.page,notice_id=a.notice_id)
        print(json.dumps(result,ensure_ascii=False));return 0
    except (OSError,ValueError,RuntimeError,KeyError) as e:print(json.dumps({'ok':False,'error':str(e),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
