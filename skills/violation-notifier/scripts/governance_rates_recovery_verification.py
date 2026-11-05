#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure replay verification of the pinned rates-notice list recovery. Never uses UI."""
import argparse,json
from datetime import datetime
from pathlib import Path
import governance_rates_recovery as r
import governance_detail as d
import governance_dom as g
import center_reconciliation as center
nav=d.nav

def observed(ref,job,tab,window,route):
    raw=d.document(ref);r.scope(raw,job,tab,route);g.need(raw['tab'].get('windowId')==window,'rates-replay-window-changed');at=datetime.fromisoformat(raw['observed_at']);g.need(at.utcoffset() is not None,'rates-replay-observed-time-missing');return raw,at

def selected_start(tree,start):
    candidates=[v['cells'][start] for v in g.calendar(tree) if start in v['cells']];n=g.one(candidates,'rates-replay-start-cell-not-unique');g.need('governance_merchant-date-selected' in g.cls(n) and bool({'governance_merchant-date-state-start','governance_merchant-date-state-single'}&g.cls(n)),'rates-replay-start-selection-not-observed')

def verify_filter(ref,route,job,tab,window,query):
    state=d.document(ref);g.need(state.get('fingerprint')==nav.tag(job) and state.get('tab_id')==tab and state.get('approved_version')==nav.VERSION and not r.unknown(state),'rates-replay-filter-scope-or-unknown');g.need(state.get('phase')==('profile-required' if route==g.CENTER else 'range-restored'),'rates-replay-filter-not-complete');refs=state.get('observations',[]);g.need(refs and state['last_observation']==refs[-1],'rates-replay-filter-observation-chain-missing');raws=[];times=[]
    for rawref in refs:
        raw,at=observed(rawref,job,tab,window,route);raws.append(raw);times.append(at)
    g.need(times==sorted(times),'rates-replay-filter-time-reversed');plan=g.QueryPlan(job['start'],job['end_exclusive']);phase='open-date';calls=state.get('calls',[]);g.need(calls,'rates-replay-filter-calls-missing');previous_index=-1
    for call in calls:
        g.need(call.get('state')=='confirmed' and call.get('before') in refs,'rates-replay-filter-call-unconfirmed');index=refs.index(call['before']);g.need(index>previous_index and index+1<len(refs),'rates-replay-filter-after-observation-missing');before=raws[index];result=plan.next(before['tree'],{'phase':phase});expected={**result['command'],'tabId':tab};g.need(call['command']==expected,'rates-replay-filter-command-not-from-plan');d.reply_matches(expected,call['result'],before);post={'month_delta':result.get('expected_month_delta')} if result.get('month_navigation') else None;g.need(call.get('postcondition')==post,'rates-replay-filter-postcondition-changed');after=raws[index+1:][0]
        # Settling may have multiple read-only observations. Validate the actual
        # effect at the next command's before, or the final source observation.
        next_call=calls[calls.index(call)+1] if calls.index(call)+1<len(calls) else None
        effect_index=refs.index(next_call['before']) if next_call else len(raws)-1;effect=raws[effect_index];intent=datetime.fromisoformat(call['intent_at']);g.need(times[index]<=intent<=times[effect_index],'rates-replay-filter-intent-time-invalid')
        if result.get('month_navigation'):
            a=[v['year']*12+v['month'] for v in g.calendar(before['tree'])];b=[v['year']*12+v['month'] for v in g.calendar(effect['tree'])];g.need(b==[x+result['expected_month_delta'] for x in a],'rates-replay-calendar-month-effect-missing')
        elif phase=='open-date':g.calendar(effect['tree'])
        elif phase=='select-start':selected_start(effect['tree'],job['start'])
        elif phase=='select-end':g.need(g.date_value(effect['tree'])==plan.start+' ~ '+plan.end,'rates-replay-end-range-not-observed')
        elif phase=='verify-date':d.normal_page(effect['tree'],job,query)
        phase=result['next_phase'];previous_index=index
    final=raws[-1]
    if route==g.CENTER:
        g.need(phase=='verify-date' and plan.next(final['tree'],{'phase':phase}).get('hold')=='analysis-all-reasons-actual-view-profile-required','rates-replay-center-filter-range-unverified');center.center_page(final['tree'],start=job['start'],end_exclusive=job['end_exclusive'])
    else:
        g.need(phase=='collect-page' and state.get('all_pages_read') is False,'rates-replay-records-filter-coverage-overclaim');page=d.normal_page(final['tree'],job,query);g.need(state.get('range_page')=={**page,'observation':state['last_observation']},'rates-replay-records-filter-page-changed')
    return state

def verify_recovery(manifest,state):
    m,v,parent,row=r.source_inputs(manifest);job=v['job'];query=v['query'];tab=m['tab_id'];window=d.document(parent['last_observation'])['tab']['windowId'];g.need(state.get('recovery_manifest')==manifest and state.get('fingerprint')==nav.tag(job) and state.get('tab_id')==tab and state.get('approved_version')==nav.VERSION,'rates-replay-state-scope-changed');g.need(state.get('phase')=='normal-restored-ready' and not r.unknown(state),'rates-replay-recovery-incomplete-or-unknown');refs=state.get('observations',[]);g.need(refs and state.get('normal_after')==state.get('last_observation')==refs[-1],'rates-replay-final-observation-missing');raws=[];times=[]
    for ref in refs:
        raw=d.document(ref);route=r.urlsplit(raw['tab']['url']).path;g.need(route in (g.CENTER,g.RECORDS),'rates-replay-unreviewed-route');raw,at=observed(ref,job,tab,window,route);raws.append(raw);times.append(at)
    g.need(times==sorted(times),'rates-replay-observation-time-reversed');g.need(times[0]>=datetime.fromisoformat(d.document(parent['last_observation'])['observed_at']),'rates-replay-observations-predate-parent')
    snapshots=state.get('filter_final_snapshots',{});g.need(set(snapshots)<={'center-range','records-range'},'rates-replay-filter-snapshot-key-unreviewed');_,folder=r.locations(m,v);filters={}
    for name,ref in snapshots.items():
        p=Path(ref['path']).resolve();g.need(p==folder/(name+'-final-'+ref['sha256']+'.json'),'rates-replay-filter-snapshot-location-changed');filters[name]=verify_filter(ref,g.CENTER if name=='center-range' else g.RECORDS,job,tab,window,query)
    pages=state.get('center_pages',[]);g.need(len(pages)==2,'rates-replay-center-two-pages-required');parsed=[]
    for i,page in enumerate(pages):
        raw,_=observed(page['observation'],job,tab,window,g.CENTER);p=center.center_page(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']);g.need(p=={k:x for k,x in page.items() if k!='observation'} and p['page']==i+1 and p['page_count']==2,'rates-replay-center-page-changed');parsed.append(p)
    g.need(parsed[0]['legend']==parsed[1]['legend'] and len({x['violation_type'] for p in parsed for x in p['top10']})==sum(len(p['top10']) for p in parsed),'rates-replay-center-coverage-changed')
    initial=state.get('initial_center_range',{});g.need(initial.get('observation')==refs[0] and initial.get('input')==g.date_value(raws[0]['tree']),'rates-replay-initial-center-range-changed')
    try:center.center_page(raws[0]['tree'],start=job['start'],end_exclusive=job['end_exclusive']);needs_center_filter=False
    except ValueError:needs_center_filter=True
    g.need(needs_center_filter==('center-range' in filters),'rates-replay-center-filter-not-proven')
    if needs_center_filter:
        child=filters['center-range'];g.need(child['last_observation']==pages[0]['observation'] and g.date_value(d.document(child['observations'][0])['tree'])==initial['input'],'rates-replay-center-filter-connection-changed')
    else:g.need(pages[0]['observation']==refs[0],'rates-replay-center-skip-not-linked')
    calls=state.get('calls',[]);g.need([c.get('purpose') for c in calls] in (['center-top10-next-page','center-records-entry'],['center-top10-next-page','center-records-entry','records-original-target-page']),'rates-replay-navigation-chain-unreviewed');record_after=None;last_index=-1;target=g.one([p['page'] for p in query['pages'] if row in p['rows']],'rates-replay-source-page-not-unique')
    for number,call in enumerate(calls):
        g.need(call['state']=='confirmed' and call.get('before') in refs,'rates-replay-navigation-unconfirmed');index=refs.index(call['before']);end=refs.index(calls[number+1]['before']) if number+1<len(calls) else len(refs)-1;g.need(index>last_index and end>index,'rates-replay-navigation-after-missing');before=raws[index];purpose=call['purpose'];effect_index=None
        if purpose=='center-top10-next-page':
            page=center.center_page(before['tree'],start=job['start'],end_exclusive=job['end_exclusive']);g.need(page==parsed[0],'rates-replay-next-before-page-changed');command=page['next'];g.need(pages[1]['observation'] in refs[index+1:end+1],'rates-replay-next-effect-outside-action-window');effect_index=refs.index(pages[1]['observation'])
            for k in range(index+1,end+1):
                got=center.center_page(raws[k]['tree'],start=job['start'],end_exclusive=job['end_exclusive']);g.need(got==parsed[0 if k<effect_index else 1],'rates-replay-next-effect-not-observed')
        elif purpose=='center-records-entry':
            g.need(center.center_page(before['tree'],start=job['start'],end_exclusive=job['end_exclusive'])==parsed[1],'rates-replay-records-entry-before-changed');command=r.record_entry(before['tree'])
            for k in range(index+1,end+1):
                path=r.urlsplit(raws[k]['tab']['url']).path
                if path==g.CENTER:
                    g.need(effect_index is None and center.center_page(raws[k]['tree'],start=job['start'],end_exclusive=job['end_exclusive'])==parsed[1],'rates-replay-records-entry-returned-back-or-changed')
                else:
                    r.scope(raws[k],job,tab,g.RECORDS);g.records_page(raws[k]['tree'],require_date=False)
                    if effect_index is None:effect_index=k;record_after=refs[k]
            g.need(effect_index is not None,'rates-replay-records-entry-effect-missing')
        else:
            page=d.normal_page(before['tree'],job,query);g.need(page['page']!=target,'rates-replay-unnecessary-target-page-action');command=r.target_page_command(before['tree'],target);g.need(state['normal_after'] in refs[index+1:end+1],'rates-replay-target-effect-outside-action-window');effect_index=refs.index(state['normal_after'])
            for k in range(index+1,end+1):
                got=d.normal_page(raws[k]['tree'],job,query);g.need(got['page']==(page['page'] if k<effect_index else target),'rates-replay-target-page-effect-missing')
        g.need(call['command']=={**command,'tabId':tab},'rates-replay-navigation-command-changed');d.reply_matches(call['command'],call['result'],before);intent=datetime.fromisoformat(call['intent_at']);g.need(times[index]<=intent<=times[effect_index],'rates-replay-navigation-intent-time-invalid');last_index=index
    g.need(record_after is not None,'rates-replay-records-entry-missing');record_raw=d.document(record_after);wanted=job['start']+' ~ '+g.QueryPlan(job['start'],job['end_exclusive']).end;needs_records_filter=g.date_value(record_raw['tree'])!=wanted;g.need(needs_records_filter==('records-range' in filters),'rates-replay-records-filter-not-proven')
    range_ref=state['records_range_observation'];range_raw,_=observed(range_ref,job,tab,window,g.RECORDS);range_page=d.normal_page(range_raw['tree'],job,query);g.need((range_page['page']!=target)==(len(calls)==3),'rates-replay-target-page-action-not-proven')
    if needs_records_filter:g.need(range_ref==filters['records-range']['last_observation'],'rates-replay-records-filter-connection-changed')
    else:g.need(range_ref==record_after,'rates-replay-records-skip-not-linked')
    final=d.normal_page(raws[-1]['tree'],job,query);g.need(final==state.get('restored_page') and final['page']==target and row in final['rows'],'rates-replay-final-source-notice-mismatch')
    return {'kind':'verified-rates-list-recovery-v1','parent_state':manifest['parent_state'],'detail_manifest':manifest['detail_manifest'],'job_fingerprint':nav.tag(job),'original_cursor':parent['cursor'],'notice_id':row['notice_id'],'query':m['inputs']['query'],'center_pages':pages,'filter_snapshots':snapshots,'normal_after':state['normal_after'],'restored_page':final,'arrow_return_effect':'not-observed','sidebar_center_return_verified':True,'detail_completed':False,'ui_used':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--state',required=True);args=p.parse_args()
    try:
        manifest=json.loads(Path(args.manifest).read_text());state=json.loads(Path(args.state).read_text());result=verify_recovery(manifest,state);print(json.dumps({'ok':True,**result},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'ui_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
