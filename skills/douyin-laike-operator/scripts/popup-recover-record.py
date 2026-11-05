#!/usr/bin/env python3
"""Fixed, durable recovery of a known blocked record-list navigation. No export.
Activation, proof, closed-bubble observation, list press and link press are ordered
in one process. A repeat only enumerates tabs and never invokes AX or activation.
"""
import argparse
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
SCRIPTS=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPTS))
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
popup=load_module('popup_navigation_recovery',SCRIPTS/'chrome-popup-navigation.py')
workflow=load_module('bridge_workflow_recovery',SCRIPTS/'bridge-workflow.py')
require=popup.require

def call(invoke,command):
    reply=invoke(command);require(reply.get('ok') is True,'bridge-recovery-command-failed');return reply['result']
def verified_order(job,tab_id):
    workflow.validate_job(job);require(job.get('action')=='acquire','acquire-work-order-required')
    path=Path(job['workflow_path']);require(path.is_absolute() and path.is_file(),'formal-journal-required')
    s=json.loads(path.read_text())
    require(s.get('backend')=='local-dom-bridge' and s.get('state')=='running' and s.get('phase')=='recordTabAfterOpen','formal-record-navigation-phase-required')
    require(s.get('work_order_id')==job.get('work_order_id') and s.get('fingerprint')==workflow.fingerprint(job),'formal-work-order-conflict')
    require(s.get('tab_id')==tab_id and s.get('company')==job['company'] and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')=={k:job['date_range'][k] for k in ('start','end')},'formal-scope-conflict')
    require(not workflow.has_side_effect_intent(s) and not workflow.has_side_effect_intent(job.get('resume',{})),'export-or-download-intent-forbids-popup-recovery')
    require(not any(c.get('state')=='unknown' for c in s.get('calls',[])),'prior-ui-outcome-unknown')
    identity=s.get('identity');require(isinstance(identity,dict) and all(identity.get(k) for k in ('provider','account_id','manager')),'formal-identity-unverified')
    if job.get('identity_baseline'):require(identity==job['identity_baseline'],'formal-identity-changed')
    return s,path

def record_candidates(tabs,group,before_ids):
    return [t for w in tabs for t in w.get('tabs',[]) if t.get('tabId') not in before_ids and t.get('allowed') is True and popup.record_url(t.get('url',''),group)]

def recover(job,tab_id,pid,outdir,invoke=None,native_factory=popup.PopupShellInspector,list_intent=None,at=None):
    require(type(pid) is int and pid>0 and type(tab_id) is int and tab_id>0,'explicit-pid-tab-required')
    state,formal=verified_order(job,tab_id);outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True)
    invoke=invoke or workflow.bridge.request;manifest=outdir/'recovery.json';bound={'work_order_id':job['work_order_id'],'fingerprint':workflow.fingerprint(job),'tab_id':tab_id,'expected_pid':pid,'groupid':str(job['groupid'])}
    with (outdir/'.recovery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if manifest.exists():
            saved=json.loads(manifest.read_text());require(all(saved.get(k)==v for k,v in bound.items()),'recovery-output-scope-conflict')
            tabs=call(invoke,{'op':'tabs'});saved['recheck_tabs']=tabs
            candidates=record_candidates(tabs,str(job['groupid']),saved.get('baseline_tab_ids',[])) if 'baseline_tab_ids' in saved else []
            if len(candidates)==1:saved.update(state='complete',record_tab=candidates[0],verified_by='read-only-repeat-enumeration')
            saved.update(replayed=False,last_readonly_check_at=popup.now());popup.atomic(manifest,saved);return saved
        require(not (outdir/'list-intent.json').exists() and not (outdir/'link-intent.json').exists(),'orphan-popup-intent-needs-readonly-reconciliation')
        saved={**bound,'version':1,'state':'unknown','phase':'activate-intent','formal_journal':{'path':str(formal.resolve()),'sha256':popup.sha(formal)},'created_at':popup.now(),'replayed':False,'settings_changed':False,'exports_created':False}
        popup.atomic(manifest,saved)
        try:
            activation=call(invoke,{'op':'activate','tabId':tab_id});tabs=call(invoke,{'op':'tabs'})
            focused=workflow.context(tabs,tab_id,job['groupid']);require(activation.get('url')==focused['url'],'activate-url-binding-mismatch')
            envelope={'source':'local-dom-bridge','observed_at':(at.isoformat() if at else popup.now()),'expected_pid':pid,'groupid':str(job['groupid']),'tabId':tab_id,'windowId':activation.get('windowId'),'activation':activation,'tabs':tabs}
            focus=outdir/'focus.json';popup.atomic(focus,envelope);proof=popup.focused_bridge_proof(focus,pid,at)
            saved.update(phase='observe-popup',bridge_focus=proof,baseline_tab_ids=[t.get('tabId') for w in tabs for t in w.get('tabs',[])]);popup.atomic(manifest,saved)
            native=native_factory(expected_pid=pid)
            try:
                require(native.pid==pid,'chrome-process-changed');shell=native.tree();popup.source_main(shell,pid,proof['title'])
            finally:native.close()
            popup.atomic(outdir/'observed-shell.json',shell)
            bubbles=[n for n in popup.flat(shell['tree']) if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXUnknown' and n.get('AXTitle')==popup.POPUP_TITLE]
            require(len(bubbles)<=1,'popup-bubble-count-ambiguous')
            if not bubbles:
                popup.popup_target(shell,pid,proof['title'])
                closed={'observed_at':popup.now(),'bubble_count':0,'closed_confirmed_by_outer_ax':True,'bridge_focus':proof,'shell':{'path':str((outdir/'observed-shell.json').resolve()),'sha256':popup.sha(outdir/'observed-shell.json')},'not_unknown_outcome':True}
                popup.atomic(outdir/'confirmed-closed.json',closed)
                saved.update(phase='reopen-confirmed-closed-list',closed_evidence_sha256=popup.sha(outdir/'confirmed-closed.json'));popup.atomic(manifest,saved)
                list_path=outdir/'list-intent.json';popup.run_open_list(list_path,pid,focus,native_factory,at)
            else:
                require(list_intent is not None,'existing-popup-needs-complete-list-chain')
                list_path=Path(list_intent).resolve();original=json.loads(list_path.read_text())
                require(original.get('mode')=='open-list' and original.get('state')=='complete' and original.get('expected_pid')==pid,'existing-popup-list-not-complete')
                require(all(original.get('bridge_focus',{}).get(k)==proof[k] for k in ('tabId','windowId','groupid','url')),'existing-popup-list-scope-mismatch')
            saved.update(phase='record-link',list_intent={'path':str(list_path.resolve()),'sha256':popup.sha(list_path)});popup.atomic(manifest,saved)
            result=popup.run_record_link(outdir/'link-intent.json',pid,focus,list_path,popup.sha(list_path),native_factory,lambda:call(invoke,{'op':'tabs'}),at)
            require(result.get('state')=='complete','record-link-outcome-unknown');saved.update(state='complete',phase='done',record_tab=result['record_tab'],completed_at=popup.now());popup.atomic(manifest,saved);return saved
        except Exception as error:
            saved.update(state='unknown',error=str(error));popup.atomic(manifest,saved);raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-order',type=Path,required=True);p.add_argument('--tab-id',type=int,required=True);p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--outdir',type=Path,required=True);p.add_argument('--list-intent',type=Path);a=p.parse_args()
    try:
        result=recover(json.loads(a.work_order.read_text()),a.tab_id,a.expected_pid,a.outdir,list_intent=a.list_intent)
        print(json.dumps({'ok':result['state']=='complete','state':result['state'],'phase':result.get('phase'),'record_tab':result.get('record_tab'),'journal':str(a.outdir.resolve()/'recovery.json'),'replayed':False,'exports_created':False},ensure_ascii=False));return 0 if result['state']=='complete' else 2
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'replayed':False,'exports_created':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
