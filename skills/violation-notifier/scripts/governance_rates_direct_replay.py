#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pure replay verification of the pinned rates-notice list recovery. Never uses UI."""
import argparse,json
from datetime import datetime
from pathlib import Path
import governance_rates_direct_recovery as r
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
    """Verify the current restored list, not past loading observations."""
    m,v,parent,row=r.source_inputs(manifest);job=v['job'];query=v['query'];tab=m['tab_id'];window=d.document(parent['last_observation'])['tab']['windowId']
    g.need(state.get('recovery_manifest')==manifest and state.get('fingerprint')==nav.tag(job) and state.get('tab_id')==tab and state.get('approved_version')==nav.VERSION,'rates-current-return-scope')
    g.need(state.get('phase')=='normal-restored-ready' and state.get('detail_cursor_advanced')is False,'rates-current-return-stage')
    current=state.get('calls',[])[-1:];g.need(current and current[0].get('state')=='confirmed','rates-current-return-input-unresolved')
    g.need(state.get('normal_after')==state.get('last_observation'),'rates-current-return-observation')
    raw,at=observed(state['normal_after'],job,tab,window,g.RECORDS);final=d.normal_page(raw['tree'],job,query)
    target=g.one([p['page']for p in query['pages']if any(d.same_source_row(current,row)for current in p['rows'])],'rates-current-original-target-page')
    g.need(final==state.get('restored_page') and final['page']==target and any(d.same_source_row(current,row)for current in final['rows']),'rates-current-return-notice-mismatch')
    pages=state['center_pages']
    for page in pages:
        entry,_=observed(page['observation'],job,tab,window,g.CENTER);parsed=center.center_page(entry['tree'],start=job['start'],end_exclusive=job['end_exclusive']);g.need(parsed=={k:value for k,value in page.items()if k!='observation'},'rates-current-center-source')
    snapshots=state.get('filter_final_snapshots',{})
    return {'kind':'verified-rates-list-recovery-v1','parent_state':manifest['parent_state'],'detail_manifest':manifest['detail_manifest'],'job_fingerprint':nav.tag(job),'original_cursor':parent['cursor'],'notice_id':row['notice_id'],'query':m['inputs']['query'],'center_pages':pages,'filter_snapshots':snapshots,'normal_after':state['normal_after'],'restored_page':final,'arrow_issued':False,'sidebar_center_return_verified':True,'detail_completed':False,'ui_used':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--state',required=True);args=p.parse_args()
    try:
        manifest=json.loads(Path(args.manifest).read_text());state=json.loads(Path(args.state).read_text());result=verify_recovery(manifest,state);print(json.dumps({'ok':True,**result},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'ui_used':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
