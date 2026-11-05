#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exact recovered rates-notice completion. Only an explicitly invoked fresh read; no clicks."""
import argparse,copy,fcntl,json,os
from datetime import datetime
from pathlib import Path
import governance_detail as d
import governance_rates_stop_loss as rates
import governance_rates_recovery as recovery
import governance_rates_recovery_verification as replay
import governance_dom as g
nav=d.nav
KIND='rates-stop-loss-recovered-roundtrip-v1'

def verify_entry(entry,state,manifest,inputs,row):
    g.need(entry.get('completion_kind')==KIND and entry.get('state')=='complete','rates-completion-kind-invalid');rm=d.document(entry['recovery_manifest']);_,folder=recovery.locations(manifest,inputs);g.need(Path(entry['recovery_state']['path']).resolve()==folder/('final-state-'+entry['recovery_state']['sha256']+'.json'),'rates-completion-immutable-final-snapshot-required');rs=d.document(entry['recovery_state']);verified=replay.verify_recovery(rm,rs);parent=d.document(rm['parent_state']);g.need(d.document(rm['detail_manifest'])==manifest and rm['parent_state']==entry['source_parent'] and verified['query']==manifest['inputs']['query'] and verified['notice_id']==row['notice_id'],'rates-completion-recovery-source-changed');index=parent['cursor'];g.need(inputs['query']['rows'][index]==row and parent['details']==state['details'][:index] and parent['calls']==state['calls'][:len(parent['calls'])],'rates-completion-original-prefix-changed');old=d.document(parent['rates_stop_loss_stage']['original_state']);opening=old['calls'][-1];current=parent['current'];g.need(entry['normal_before']==current['normal_before'] and entry['detail_observation']==current['detail_observation'],'rates-completion-original-observation-changed');facts,_=rates.parse(d.document(entry['detail_observation']),row,opening,inputs['job']);g.need(facts==entry['facts']==current['facts'],'rates-completion-facts-changed')
    window=d.document(current['normal_before'])['tab']['windowId'];fresh,at=replay.observed(entry['normal_after'],inputs['job'],manifest['tab_id'],window,g.RECORDS);page=d.normal_page(fresh['tree'],inputs['job'],inputs['query']);g.need(page==verified['restored_page'] and row in page['rows'] and at>=datetime.fromisoformat(d.document(verified['normal_after'])['observed_at']),'rates-completion-fresh-original-page-changed');return facts

def snapshot(path,target):
    path=Path(path);target=Path(target);data=path.read_bytes()
    if target.exists():g.need(target.read_bytes()==data,'rates-completion-snapshot-conflict')
    else:
        with target.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    return d.ref(target)

def finish(detail_manifest_path,parent_sha,recovery_sha,invoke=None):
    mr=d.ref(detail_manifest_path);m=d.document(mr);v=d.inputs(m);main,folder=recovery.locations(m,v);mp=folder/'manifest.json';rm=json.loads(mp.read_text());g.need(rm['detail_manifest']==mr and rm['parent_state']['sha256']==parent_sha,'rates-completion-original-manifest-required');parent=d.document(rm['parent_state']);index=parent['cursor'];current_state=json.loads(main.read_text())
    if len(current_state['details'])>index:
        entry=current_state['details'][index];g.need(entry.get('recovery_manifest')==d.ref(mp) and entry.get('recovery_state',{}).get('sha256')==recovery_sha,'rates-completion-already-completed-other-source');verify_entry(entry,current_state,m,v,v['query']['rows'][index]);return {'ok':True,'already_complete':True,'detail_progress_changed':False,'state':str(main),'state_sha256':nav.digest(main)}
    final=folder/'state.json';g.need(nav.digest(final)==recovery_sha,'rates-completion-final-recovery-sha-mismatch');final_ref=snapshot(final,folder/('final-state-'+recovery_sha+'.json'));rs=d.document(final_ref);replay.verify_recovery(rm,rs);r=d.Runner(m,invoke)
    if 'rates_completion_intent' not in r.s:
        g.need(nav.digest(main)==parent_sha and r.s==parent,'rates-completion-original-parent-sha-required');r.s['rates_completion_intent']={'kind':KIND,'source_parent':rm['parent_state'],'recovery_manifest':d.ref(mp),'recovery_state':final_ref,'expected_parent_sha256':parent_sha,'expected_recovery_sha256':recovery_sha};r.s.update(phase='rates-completion-verification',hold=True,waiting_for='fresh-original-notice-before-local-completion');r.save()
    intent=r.s['rates_completion_intent'];g.need(intent=={'kind':KIND,'source_parent':rm['parent_state'],'recovery_manifest':d.ref(mp),'recovery_state':final_ref,'expected_parent_sha256':parent_sha,'expected_recovery_sha256':recovery_sha} and r.s['phase']=='rates-completion-verification' and r.s['cursor']==index and r.s['details']==parent['details'] and r.s['calls']==parent['calls'] and r.s['current']==parent['current'],'rates-completion-original-intent-required')
    r.observe();entry={'state':'complete','completion_kind':KIND,'notice_id':parent['current']['notice_id'],'normal_before':parent['current']['normal_before'],'detail_observation':parent['current']['detail_observation'],'facts':copy.deepcopy(parent['current']['facts']),'normal_after':r.s['last_observation'],'source_parent':rm['parent_state'],'recovery_manifest':d.ref(mp),'recovery_state':final_ref};verify_entry(entry,r.s,m,v,v['query']['rows'][index]);r.s['details'].append(entry);r.s.update(cursor=index+1,current=None,phase='complete' if index+1==len(v['query']['rows']) else 'normal');r.s.pop('rates_completion_intent');r.s.pop('hold',None);r.s.pop('waiting_for',None);r.s.pop('last_error',None);d.verify_completed(r.s,m,v,require_complete=r.s['phase']=='complete');r.save();return {'ok':True,'already_complete':False,'detail_progress_changed':True,'state':str(main),'state_sha256':nav.digest(main),'cursor':r.s['cursor'],'phase':r.s['phase']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--detail-manifest',required=True);p.add_argument('--expected-parent-state-sha256',required=True);p.add_argument('--expected-recovery-state-sha256',required=True);args=p.parse_args()
    try:
        m=d.document(d.ref(args.detail_manifest));v=d.inputs(m);parent,folder=recovery.locations(m,v)
        with (parent.parent/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);result=finish(args.detail_manifest,args.expected_parent_state_sha256,args.expected_recovery_state_sha256);print(json.dumps({**result,'business_progress_changed':False},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as exc:print(json.dumps({'ok':False,'error':str(exc),'business_progress_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
