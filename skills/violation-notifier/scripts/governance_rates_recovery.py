#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pinned read/query-only recovery to the original rates-notice records page. No detail completion."""
import argparse,copy,fcntl,json,re
from pathlib import Path
from urllib.parse import urlsplit
import governance_detail as d
import governance_rates_stop_loss as rates
import governance_dom as g
import center_reconciliation as center
nav=d.nav
Q=d.query_api

def unknown(s):return any(c.get('state')=='unknown' for c in s.get('calls',[]))
def locations(m,v):
    parent=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])/'state.json'
    return parent,parent.parent/'rates-recovery'
def source_inputs(manifest):
    g.need(manifest.get('kind')=='rates-notice-list-recovery-v1','rates-recovery-manifest-invalid');m=d.document(manifest['detail_manifest']);v=d.inputs(m);parent=d.document(manifest['parent_state']);g.need(parent['phase']=='rates-center-recovery-route-hold' and parent['manifest']==m and not unknown(parent) and not unknown(v['query']),'rates-recovery-original-state-unsettled');d.verify_completed(parent,m,v,require_complete=False)
    role=object.__new__(rates.Runner);role.s=parent;role.v=v;role.manifest=m;role.job=v['job'];role.tab=m['tab_id'];old,row,opening=role.recovery_original();recovery=parent['rates_center_recovery'];calls=parent['calls'][len(old['calls']):];call=g.one(calls,'rates-recovery-sidebar-call-not-unique');g.need(call['state']=='confirmed' and call['command']==recovery['command'] and call['before']==recovery['before_navigation'],'rates-recovery-sidebar-unconfirmed');d.reply_matches(call['command'],call['result'],d.document(call['before']));rates.parse(d.document(call['before']),row,opening,v['job']);expected={'op':'click','tabId':m['tab_id'],'kind':'navigation','locator':{'by':'selector','value':'#box-aside-menu > div > div:nth-of-type(8) > div > div:nth-of-type(1) > span > div > span'}};g.need(call['command']==expected,'rates-recovery-sidebar-command-unreviewed');g.need(parent['last_observation']==recovery['after_navigation'],'rates-recovery-center-reference-changed');raw=d.document(recovery['after_navigation']);scope(raw,v['job'],m['tab_id'],g.CENTER);g.need(raw['tab'].get('windowId')==d.document(parent['current']['normal_before'])['tab'].get('windowId'),'rates-recovery-source-window-changed');g.need(parent['cursor']==len(parent['details']) and parent['current']['notice_id']==row['notice_id'],'rates-recovery-original-notice-changed');return m,v,parent,row

def scope(raw,job,tab,path):
    g.need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==tab and raw.get('not_business_capture') is True,'rates-recovery-observation-source-invalid');t=nav.context([{'tabs':[raw['tab']]}],tab,job['groupid']);g.need(urlsplit(t['url']).path==path and raw['tree'].get('url')=='https://life.douyin.com'+path,'rates-recovery-route-changed');nav.identity(raw['tree'],job['identity']);g.root(raw['tree'],path);return raw['tree']

def record_entry(tree):
    root=g.root(tree,g.CENTER);tools=g.one(g.classnodes(root,'todoSummary-xpJGcr'),'rates-recovery-tools-not-unique');g.need(g.text(tools).startswith('常用工具 '),'rates-recovery-tools-title-changed');target=g.one([n for n in g.classnodes(tools,'todoLabel-I3rSqB') if n.get('tag')=='p' and not n.get('children') and g.text(n)=='违规记录' and not n.get('disabled')],'rates-recovery-record-entry-not-unique');item=g.one([n for n in g.classnodes(tools,'todoItem-SQ0SNc') if target in list(g.walk(n))],'rates-recovery-record-item-not-unique');g.need(re.fullmatch(r'违规记录 新增[0-9]+',g.text(item)),'rates-recovery-record-entry-count-unreviewed');return g.click(target,'navigation')

def target_page_command(tree,target):
    pager=g.one(g.classnodes(g.root(tree,g.RECORDS),'governance_merchant-pager'),'rates-recovery-record-pager-not-unique');button=g.one([n for n in g.walk(pager) if n.get('tag')=='li' and 'governance_merchant-pager-item' in g.cls(n) and g.text(n)==str(target)],'rates-recovery-target-page-not-unique');g.need(not({'governance_merchant-pager-item-disabled','governance_merchant-pager-item-checked'}&g.cls(button)),'rates-recovery-target-page-unavailable');return g.click(button,'navigation')

class RangeRestore(Q.Runner):
    def __init__(self,job,tab,path,version,route,invoke=None,window=None):self.route=route;self.window=window;super().__init__(job,tab,path,version,invoke)
    def observe(self):
        tree=super().observe();g.root(tree,self.route);g.need(self.window is None or d.document(self.s['last_observation'])['tab'].get('windowId')==self.window,'rates-recovery-filter-window-changed');return tree
    def step(self):
        # The stock query runner immediately follows records pagination. Recovery
        # deliberately intercepts the first verified page, without claiming coverage.
        if self.s['phase']=='range-restored':return self.s
        if self.route==g.RECORDS and self.s['phase']=='collect-page':
            if unknown(self.s):self.s['waiting_for']='original-unknown-intent-no-replay';self.save();return self.s
            tree=self.observe()
            if not self.await_ready(tree):return self.s
            page=g.records_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);self.s.update(phase='range-restored',range_page={**page,'observation':self.s['last_observation']},all_pages_read=False,waiting_for='recovery-original-target-page-required');self.save();return self.s
        return super().step()

class Runner(Q.Runner):
    def __init__(self,manifest,path,invoke=None):
        self.manifest=manifest;self.m,self.v,self.parent,self.row=source_inputs(manifest);self.live_parent,self.folder=locations(self.m,self.v);g.need(Path(path).resolve()==self.folder/'state.json','rates-recovery-canonical-state-required');self.parent_unchanged();self.source_window=d.document(self.parent['last_observation'])['tab']['windowId'];existed=Path(path).exists();actual_invoke=invoke or nav.bridge.request
        def guarded(command):self.parent_unchanged();return actual_invoke(command)
        super().__init__(self.v['job'],self.m['tab_id'],path,self.m['approved_version'],guarded)
        if existed:g.need(self.s.get('recovery_manifest')==manifest,'rates-recovery-original-manifest-required')
        else:self.s.update(recovery_manifest=manifest,phase='center-range',center_pages=[],target_notice=self.row['notice_id'],detail_cursor_advanced=False)
    def parent_unchanged(self):g.need(self.live_parent.is_file() and nav.digest(self.live_parent)==self.manifest['parent_state']['sha256'],'rates-recovery-live-parent-changed')
    def child(self,route):return RangeRestore(self.job,self.tab,self.folder/('center-range.json' if route==g.CENTER else 'records-range.json'),self.version,route,self.invoke,self.source_window)
    def observe(self):
        tree=super().observe();g.need(d.document(self.s['last_observation'])['tab'].get('windowId')==self.source_window,'rates-recovery-window-changed');return tree
    def unresolved(self):
        if unknown(self.s) or unknown(self.parent) or unknown(self.v['query']):return True
        for name in ('center-range.json','records-range.json'):
            p=self.folder/name
            if p.exists() and unknown(json.loads(p.read_text())):return True
        return False
    def act_once(self,command,phase,purpose):
        self.parent_unchanged();g.need(not self.unresolved(),'rates-recovery-unknown-intent-no-replay');command={**command,'tabId':self.tab};entry={'state':'unknown','purpose':purpose,'command':command,'before':self.s['last_observation'],'intent_at':nav.stamp()};self.s['calls'].append(entry);self.s['phase']=phase+'-unknown';self.save();result=self.request(command);d.reply_matches(command,result,d.document(entry['before']));entry.update(state='confirmed',result=result);self.s['phase']=phase;self.save()
    def wait(self,reason):
        n=self.s.get('readonly_checks',0)+1;self.s.update(readonly_checks=n,waiting_for=reason,hold=n>=5);self.save();return self.s
    def center_result(self,ref):
        raw=d.document(ref);scope(raw,self.job,self.tab,g.CENTER);p=center.center_page(raw['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(p['page']==1 and p['page_count']==2,'rates-recovery-center-page-profile-changed');self.s['center_pages']=[{**p,'observation':ref}];self.s.update(phase='center-next',waiting_for=None);self.save()
    def records_result(self,ref):
        raw=d.document(ref);scope(raw,self.job,self.tab,g.RECORDS);p=d.normal_page(raw['tree'],self.job,self.v['query']);self.s.update(records_range_observation=ref,phase='restore-target-page',waiting_for=None);self.save();return p
    def freeze_filter_states(self):
        snapshots={}
        for name in ('center-range.json','records-range.json'):
            path=self.folder/name
            if not path.exists():continue
            digest=nav.digest(path);target=self.folder/(path.stem+'-final-'+digest+'.json');data=path.read_bytes()
            if target.exists():g.need(target.read_bytes()==data,'rates-recovery-filter-snapshot-conflict')
            else:
                with target.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
            snapshots[path.stem]=d.ref(target)
        self.s['filter_final_snapshots']=snapshots
    def step(self):
        self.parent_unchanged()
        if self.s['phase']=='normal-restored-ready':return self.s
        if self.unresolved():
            self.observe();self.s.update(waiting_for='original-or-recovery-unknown-intent-readonly-hold',hold=True);self.save();return self.s
        if self.s.get('hold'):return self.s
        phase=self.s['phase']
        if phase=='center-range':
            childpath=self.folder/'center-range.json'
            if not childpath.exists():
                tree=self.observe();g.root(tree,g.CENTER);self.s['initial_center_range']={'input':g.date_value(tree),'observation':self.s['last_observation']};self.save()
                try:center.center_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive'])
                except ValueError:pass
                else:self.center_result(self.s['last_observation']);return self.s
            child=self.child(g.CENTER);child.step();child.save();self.s['center_filter_state']=d.ref(child.file);self.save()
            if child.s['phase']=='profile-required':self.center_result(child.s['last_observation'])
            else:self.s['waiting_for']=child.s.get('waiting_for');self.save()
            return self.s
        if phase=='records-range':
            child=self.child(g.RECORDS);child.step();child.save();self.s['records_filter_state']=d.ref(child.file);self.save()
            if child.s['phase']=='range-restored':self.records_result(child.s['last_observation'])
            else:self.s['waiting_for']=child.s.get('waiting_for');self.save()
            return self.s
        tree=self.observe();obs=self.s['last_observation']
        # A list route whose counts have not arrived is not an empty result (B43): read
        # again through this journal's own bounded wait instead of parsing the placeholder.
        if g.records_counts_pending(tree):return self.wait('records-list-counts-not-yet-observed')
        if phase=='center-next':
            scope(d.document(obs),self.job,self.tab,g.CENTER);p=center.center_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(p=={k:v for k,v in self.s['center_pages'][0].items() if k!='observation'},'rates-recovery-center-page-one-changed');self.act_once(p['next'],'center-read-two','center-top10-next-page')
        elif phase=='center-read-two':
            scope(d.document(obs),self.job,self.tab,g.CENTER);p=center.center_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive'])
            if p['page']==1:return self.wait('center-next-page-not-yet-observed')
            g.need(p['page']==p['page_count']==2 and p['legend']==self.s['center_pages'][0]['legend'],'rates-recovery-center-page-two-changed');self.s['center_pages'].append({**p,'observation':obs});self.s.update(phase='open-records',readonly_checks=0,waiting_for=None);self.save()
        elif phase=='open-records':
            scope(d.document(obs),self.job,self.tab,g.CENTER);p=center.center_page(tree,start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(p=={k:v for k,v in self.s['center_pages'][1].items() if k!='observation'},'rates-recovery-center-page-two-before-records-changed');self.act_once(record_entry(tree),'inspect-records','center-records-entry')
        elif phase=='inspect-records':
            if urlsplit(tree['url']).path==g.CENTER:return self.wait('records-route-not-yet-observed')
            scope(d.document(obs),self.job,self.tab,g.RECORDS);g.date_input(tree);wanted=self.job['start']+' ~ '+self.plan.end
            if g.date_value(tree)==wanted:self.records_result(obs)
            else:self.s.update(phase='records-range',waiting_for=None);self.save()
        elif phase in ('restore-target-page','verify-target-page'):
            scope(d.document(obs),self.job,self.tab,g.RECORDS);p=d.normal_page(tree,self.job,self.v['query']);target=g.one([x['page'] for x in self.v['query']['pages'] if self.row in x['rows']],'rates-recovery-original-target-page-not-unique')
            if p['page']==target:
                g.need(any(d.same_source_row(row,self.row)for row in p['rows']),'rates-recovery-original-notice-row-changed');self.freeze_filter_states();self.s.update(phase='normal-restored-ready',hold=True,waiting_for='supervisor-verify-rates-roundtrip-before-completion',normal_after=obs,restored_page=p,detail_cursor_advanced=False);self.save()
            elif phase=='verify-target-page':return self.wait('original-records-target-page-not-yet-observed')
            else:self.act_once(target_page_command(tree,target),'verify-target-page','records-original-target-page')
        else:raise ValueError('rates-recovery-phase-unreviewed')
        return self.s

def prepare(manifest_path,state_sha):
    mr=d.ref(manifest_path);m=d.document(mr);v=d.inputs(m);parent,out=locations(m,v);g.need(nav.digest(parent)==state_sha,'rates-recovery-parent-checkpoint-mismatch');out.mkdir(exist_ok=True);g.need(out.resolve()==out,'rates-recovery-canonical-directory-required');snapshot=out/('source-parent-'+state_sha+'.json');data=parent.read_bytes()
    if snapshot.exists():g.need(snapshot.read_bytes()==data,'rates-recovery-source-snapshot-conflict')
    else:
        with snapshot.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
    manifest={'kind':'rates-notice-list-recovery-v1','detail_manifest':mr,'parent_state':d.ref(snapshot)};source_inputs(manifest);mp=out/'manifest.json'
    if mp.exists():g.need(json.loads(mp.read_text())==manifest,'rates-recovery-original-manifest-required')
    else:d.exclusive(mp,manifest)
    return mp

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare');a.add_argument('--detail-manifest',required=True);a.add_argument('--expected-parent-state-sha256',required=True);a=sp.add_parser('run');a.add_argument('--manifest',required=True);a.add_argument('--steps',type=int,choices=range(1,101),default=1);args=p.parse_args()
    try:
        if args.verb=='prepare':mp=prepare(args.detail_manifest,args.expected_parent_state_sha256);result={'ok':True,'manifest':str(mp),'ui_used':False}
        else:
            mp=Path(args.manifest).resolve();manifest=json.loads(mp.read_text());dm=d.document(manifest['detail_manifest']);dv=d.inputs(dm);_,canonical=locations(dm,dv);g.need(mp==canonical/'manifest.json','rates-recovery-canonical-manifest-required')
            with (mp.parent/'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=Runner(manifest,mp.parent/'state.json')
                try:
                    for _ in range(args.steps):
                        r.step();r.save()
                        if r.s.get('hold') or r.s.get('waiting_for'):break
                except Exception as exc:r.s.update(last_error=str(exc),hold=True,waiting_for='new-shape-or-scope-supervisor-review');r.save();raise
                result={'ok':True,'phase':r.s['phase'],'waiting_for':r.s.get('waiting_for'),'state':str(r.file),'state_sha256':nav.digest(r.file),'detail_cursor_advanced':False}
        result['business_progress_changed']=False;print(json.dumps(result,ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
