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

def unknown(s):
 if s.get('manifest',{}).get('kind')=='governance-detail-inspection-manifest-v1':return bool(d.unresolved_detail_calls(s))
 return any(c.get('state')=='unknown' for c in s.get('calls',[]))
def locations(m,v):
    parent=Path(m['inputs']['query']['path']).resolve().parent/'governance-detail-operations'/nav.tag(v['job'])/'state.json'
    state=__import__('json').loads(parent.read_text());notice=state['current']['notice_id'];folder=parent.parent/'automatic-stop-loss'/__import__('hashlib').sha256(notice.encode()).hexdigest()/'rates-recovery'
    return parent,folder

def source_inputs(manifest):
    import governance_stop_loss_production as production
    return production.direct_source(manifest)

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
        if self.s.get('hold') or self.s.get('settling_exhausted'):return self.s
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
        raw=d.document(ref);scope(raw,self.job,self.tab,g.CENTER);p=center.center_page(raw['tree'],start=self.job['start'],end_exclusive=self.job['end_exclusive']);g.need(p['page']==1 and p['page_count'] in (1,2),'rates-recovery-center-page-profile-changed');self.s['center_pages']=[{**p,'observation':ref}];self.s.update(phase='open-records' if p['page_count']==1 else 'center-next',waiting_for=None);self.save()
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
        if phase in ('center-range','center-next','center-read-two'):
            # The center is a transit page, not a second business collection.
            tree=self.observe();scope(d.document(self.s['last_observation']),self.job,self.tab,g.CENTER)
            self.s.update(phase='open-records',center_pages=[],waiting_for=None);self.save();return self.s
        if phase=='records-range':
            child=self.child(g.RECORDS);g.need(not child.s.get('hold') and not child.s.get('settling_exhausted'),'auto-direct-child-manual-or-exhausted-hold');child.step();child.save();self.s['records_filter_state']=d.ref(child.file);self.save()
            if child.s['phase']=='range-restored':self.records_result(child.s['last_observation'])
            else:self.s['waiting_for']=child.s.get('waiting_for');self.save()
            return self.s
        tree=self.observe();obs=self.s['last_observation']
        if g.records_counts_pending(tree):return self.wait('records-list-counts-not-yet-observed')
        if phase=='open-records':
            scope(d.document(obs),self.job,self.tab,g.CENTER);self.act_once(record_entry(tree),'inspect-records','center-records-entry')
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

# No standalone mutation CLI. Only the locked formal detail runner may own this flow.
