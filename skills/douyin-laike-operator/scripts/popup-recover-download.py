#!/usr/bin/env python3
"""Recover one observed blocked XLSX link from an existing confirmed download.

No export/download click or ticket creation. One continuous activate/list/link
chain; repeat can only reconcile the ORIGINAL ticket. Expiry never causes UI.
"""
import argparse
from datetime import datetime,timezone
import fcntl
import importlib.util
import json
from pathlib import Path
import sys
import time
SCRIPTS=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPTS))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
popup=load('download_popup_shell',SCRIPTS/'chrome-popup-navigation.py')
workflow=load('download_popup_workflow',SCRIPTS/'bridge-workflow.py')
require=popup.require
DOWNLOAD_LABEL='•  …douyinstatic.com/…/门店评价_全部门店_2…'

def clock(at=None):return at or datetime.now(timezone.utc)
def live_ticket(ticket,at=None):
    return type(ticket.get('expires')) in (int,float) and ticket['expires']>clock(at).timestamp()*1000
def call(invoke,command):
    response=invoke(command);require(response.get('ok') is True,'download-recovery-bridge-failed:'+str(response.get('error')));return response['result']

def verified_order(job,tab_id):
    workflow.validate_job(job);require(job.get('action')=='acquire','acquire-work-order-required')
    path=Path(job['workflow_path']);require(path.is_absolute() and path.is_file(),'formal-journal-required');s=json.loads(path.read_text())
    require(s.get('backend')=='local-dom-bridge' and s.get('state')=='running' and s.get('phase')=='downloadResult' and s.get('downloadPending') is True,'confirmed-pending-download-phase-required')
    require(s.get('work_order_id')==job.get('work_order_id') and s.get('fingerprint')==workflow.fingerprint(job),'formal-work-order-conflict')
    require(s.get('record_tab_id')==tab_id and s.get('company')==job['company'] and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')=={k:job['date_range'][k] for k in ('start','end')},'formal-download-scope-conflict')
    require(popup.record_url(s.get('record_url',''),job['groupid']),'formal-record-url-unverified')
    identity=s.get('identity');require(isinstance(identity,dict) and all(identity.get(k) for k in ('provider','account_id','manager')),'formal-identity-unverified')
    if job.get('identity_baseline'):require(identity==job['identity_baseline'],'formal-identity-changed')
    command=s.get('download_command',{});require(command.get('op')=='click' and command.get('kind')=='download' and command.get('tabId')==tab_id,'formal-download-command-unverified')
    clicks=[c for c in s.get('calls',[]) if c.get('command',{}).get('kind')=='download']
    require(len(clicks)==1 and clicks[0].get('command')==command and clicks[0].get('state')=='confirmed' and clicks[0].get('result',{}).get('kind')=='download','original-download-click-not-uniquely-confirmed')
    if s.get('company_search_explicit_recovery'):
        # This qualifier reads the canonical saved journal, not pending tick
        # observations. Reuse the same verified terminal/prefix mechanism.
        from switch_read_recovery import _typed_search_snapshot
        require(_typed_search_snapshot(job,s)is not None,'prior-ui-outcome-unknown')
        require(json.loads(path.read_bytes())==s,'download-typed-canonical-changed')
    else:
        require(not any(c.get('state')=='unknown' and c.get('command',{}).get('op') in ('click','filter','activate') for c in s.get('calls',[])),'prior-ui-outcome-unknown')
    generated=s.get('generated_record',{});name='门店评价_全部门店_'+job['date_range']['start'].replace('-','_')+'-'+job['date_range']['end'].replace('-','_')
    require(generated.get('state')=='success' and name in generated.get('text','') and generated.get('generated_at') and generated.get('selector'),'generated-record-date-scope-unverified')
    require(not any(r.get('generated_at')==generated['generated_at'] for r in s.get('baseline_records',[])),'generated-record-not-new')
    checkpoints=[c for c in s.get('checkpoints',[]) if c.get('stage')=='export-generated']
    require(len(checkpoints)==1 and checkpoints[0].get('generated_at')==generated['generated_at'] and checkpoints[0].get('text')==generated['text'] and checkpoints[0].get('record_url')==s['record_url'],'unique-generated-record-proof-required')
    ticket=s.get('download_ticket',{});require(isinstance(ticket.get('ticket'),str) and ticket['ticket'] and ticket.get('since') and type(ticket.get('expires')) in (int,float),'original-download-ticket-required')
    since=datetime.fromisoformat(ticket['since'].replace('Z','+00:00'));require(since.utcoffset() is not None and 0<ticket['expires']-since.timestamp()*1000<=600010,'original-ticket-expiry-contract-invalid')
    intents=[c for c in s.get('checkpoints',[]) if c.get('stage')=='download-intent']
    require(len(intents)==1 and intents[0].get('ticket')==ticket['ticket'] and intents[0].get('generated_at')==generated['generated_at'],'original-ticket-record-binding-mismatch')
    return s,path

def download_target(snapshot,pid,title):
    main=popup.source_main(snapshot,pid,title)
    bubbles=[n for n in popup.flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXUnknown' and n.get('AXTitle')==popup.POPUP_TITLE]
    require(len(bubbles)==1,'download-popup-bubble-not-unique')
    # The main window has a mirror of the popup. Never count/press that mirror.
    links=[n for n in popup.flat(bubbles[0]) if n.get('role')=='AXLink']
    require(len(links)==1,'download-bubble-link-not-unique');link=links[0]
    require(link.get('AXTitle')==DOWNLOAD_LABEL and link.get('AXDescription')==DOWNLOAD_LABEL and link.get('AXEnabled') is True and 'AXPress' in link.get('actions',[]),'reviewed-cdn-download-label-changed')
    require(not link.get('AXURL') and not link.get('AXURL_omitted'),'unreviewed-download-url-shape')
    return main,link

def reconcile(saved,manifest,invoke,at=None):
    expired=not live_ticket(saved['ticket'],at)
    if expired and not saved.get('allow_expired_readonly_reconcile'):
        saved.update(state='await-readonly-reconcile',phase='original-ticket-expired',replayed=False,waiting_for='supervisor-original-since-unique-filename-readonly-reconcile')
    else:
        command=({'op':'download-reconcile','tabId':saved['tab_id'],'groupid':saved['groupid'],'ticket':saved['ticket']['ticket'],'since':saved['ticket']['since'],'filename':saved['filename']} if expired else {'op':'download-status','ticket':saved['ticket']['ticket']})
        receipt=call(invoke,command)
        if expired or 'ticket' in receipt:require(receipt.get('ticket')==saved['ticket']['ticket'],'original-ticket-response-mismatch')
        saved['observed_original_ticket']=saved['ticket']['ticket']
        if expired:require(receipt.get('readonly') is True and receipt.get('reconciled') is True,'expired-readonly-reconciliation-required')
        saved['download_status']=receipt;saved['last_readonly_check_at']=popup.now()
        if receipt.get('state')=='complete':
            file=workflow.Workflow.verify_download(None,receipt)
            saved.update(state='complete',phase='done',verified_file={'path':str(file),'sha256':popup.sha(file)},completed_at=popup.now(),replayed=False)
        else:saved.update(state='await-download',phase='original-ticket-only',replayed=False)
    popup.atomic(manifest,saved);return saved

def live_ticket_native_factory(ticket,factory,at=None):
    """Every native construction/read/press keeps the original ticket deadline.
    run_open_list receives this same wrapper, so its internal press is guarded.
    """
    def build(**kwargs):
        require(live_ticket(ticket,at),'original-ticket-expired-before-native')
        native=factory(**kwargs)
        class BoundNative:
            @property
            def pid(self):return native.pid
            def tree(self):
                require(live_ticket(ticket,at),'original-ticket-expired-before-native-read');return native.tree()
            def press(self,*args,**kwargs):
                require(live_ticket(ticket,at),'original-ticket-expired-before-native-press');return native.press(*args,**kwargs)
            def close(self):return native.close()
        return BoundNative()
    return build

def recover(job,tab_id,pid,outdir,invoke=None,native_factory=popup.PopupShellInspector,list_intent=None,at=None,allow_expired_readonly_reconcile=False,probe_pending=False):
    require(type(pid) is int and pid>0 and type(tab_id) is int and tab_id>0,'explicit-pid-record-tab-required')
    s,formal=verified_order(job,tab_id);outdir=Path(outdir).resolve();outdir.mkdir(parents=True,exist_ok=True);manifest=outdir/'recovery.json'
    invoke=invoke or workflow.bridge.request
    bound={'work_order_id':job['work_order_id'],'fingerprint':workflow.fingerprint(job),'tab_id':tab_id,'expected_pid':pid,'groupid':str(job['groupid']),'ticket':s['download_ticket'],'allow_expired_readonly_reconcile':bool(allow_expired_readonly_reconcile)}
    with (outdir/'.recovery.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if manifest.exists():
            saved=json.loads(manifest.read_text());require(all(saved.get(k)==v for k,v in bound.items()),'download-recovery-output-scope-conflict')
            return reconcile(saved,manifest,invoke,at)  # No AX factory, activate or new ticket.
        # Automatic runtime probes must remain retryable until a real blocked
        # button is proven. Only actual AX action admission creates recovery.json.
        recovery_manifest=manifest
        if probe_pending:manifest=outdir/'probe.json'
        require(not (outdir/'link-intent.json').exists() and not (outdir/'list-intent.json').exists(),'orphan-download-recovery-intent-readonly-only')
        saved={**bound,'filename':workflow.export_tag(s['date_range'])+'.xlsx','version':1,'state':'unknown','phase':'recovery-intent','created_at':popup.now(),'formal_journal':{'path':str(formal.resolve()),'sha256':popup.sha(formal)},'generated_record':s['generated_record'],'replayed':False,'new_download_click':False,'new_ticket_created':False,'settings_changed':False}
        popup.atomic(manifest,saved)
        if not live_ticket(s['download_ticket'],at) and not allow_expired_readonly_reconcile:return reconcile(saved,manifest,invoke,at)
        # An existing actual download may have completed while the UI was blocked.
        checked=reconcile(saved,manifest,invoke,at)
        if checked['state']=='complete':return checked
        if not live_ticket(s['download_ticket'],at):
            saved.update(state='await-readonly-reconcile',phase='original-ticket-expired-readonly-only',replayed=False);popup.atomic(manifest,saved);return saved
        if checked.get('download_status',{}).get('state')!='pending':return checked
        def permission():return live_ticket(s['download_ticket'],at)
        bounded_native=live_ticket_native_factory(s['download_ticket'],native_factory,at)
        try:
            require(permission(),'original-ticket-expired-before-activation')
            saved.update(state='unknown',phase='activate-intent');popup.atomic(manifest,saved)
            require(permission(),'original-ticket-expired-before-activate-dispatch')
            activation=call(invoke,{'op':'activate','tabId':tab_id});tabs=call(invoke,{'op':'tabs'})
            focused=workflow.context(tabs,tab_id,job['groupid']);require(activation.get('url')==focused['url']==s['record_url'],'record-tab-url-changed')
            envelope={'source':'local-dom-bridge','observed_at':(at.isoformat() if at else popup.now()),'expected_pid':pid,'groupid':str(job['groupid']),'tabId':tab_id,'windowId':activation.get('windowId'),'activation':activation,'tabs':tabs}
            focus=outdir/'focus.json';popup.atomic(focus,envelope);proof=popup.focused_bridge_proof(focus,pid,at)
            saved.update(phase='observe-popup',bridge_focus=proof);popup.atomic(manifest,saved)
            native=bounded_native(expected_pid=pid)
            try:
                require(native.pid==pid,'chrome-process-changed');shell=native.tree();popup.source_main(shell,pid,proof['title'])
            finally:native.close()
            popup.atomic(outdir/'observed-shell.json',shell)
            bubbles=[n for n in popup.flat(shell['tree']) if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXUnknown' and n.get('AXTitle')==popup.POPUP_TITLE]
            require(len(bubbles)<=1,'download-bubble-count-ambiguous')
            if probe_pending and not bubbles:
                main=popup.source_main(shell,pid,proof['title'])
                buttons=[n for n in popup.flat(main) if n.get('role')=='AXButton' and n.get('AXEnabled') is True and 'AXPress' in n.get('actions',[]) and (n.get('AXTitle') or n.get('AXDescription'))==popup.LABEL and all(n.get(k) in (None,'',popup.LABEL) for k in ('AXTitle','AXDescription'))]
                if not buttons:
                    saved.update(state='await-download',phase='no-blocked-popup-observed',replayed=False)
                    popup.atomic(manifest,saved);return saved
                popup.popup_target(shell,pid,proof['title']) # multiple/ambiguous refuses
            if probe_pending:
                # Existing open bubbles are usable only with a completed chain;
                # never guess a link or replace an unknown earlier attempt.
                if bubbles and list_intent is None:
                    saved.update(state='await-download',phase='existing-bubble-needs-complete-list-chain',replayed=False)
                    popup.atomic(manifest,saved);return saved
                manifest=recovery_manifest;popup.atomic(manifest,saved)
            if not bubbles:
                popup.popup_target(shell,pid,proof['title']);require(permission(),'original-ticket-expired-before-list')
                popup.atomic(outdir/'confirmed-closed.json',{'bubble_count':0,'observed_at':popup.now(),'shell_sha256':popup.sha(outdir/'observed-shell.json')})
                list_path=outdir/'list-intent.json';popup.run_open_list(list_path,pid,focus,bounded_native,at)
            else:
                require(list_intent is not None,'existing-download-bubble-needs-complete-list-chain');list_path=Path(list_intent).resolve()
            original=json.loads(list_path.read_text());require(original.get('mode')=='open-list' and original.get('state')=='complete' and original.get('expected_pid')==pid,'completed-download-list-intent-required')
            require(all(original.get('bridge_focus',{}).get(k)==proof[k] for k in ('tabId','windowId','groupid','url')),'download-list-focus-scope-mismatch')
            _,observed=download_target(original['after'],pid,proof['title'])
            require(permission(),'original-ticket-expired-before-link')
            native=bounded_native(expected_pid=pid)
            try:
                before=native.tree();window,link=download_target(before,pid,proof['title']);require(link['AXTitle']==observed['AXTitle'],'download-link-observation-changed')
                require(popup.sha(formal)==saved['formal_journal']['sha256'],'formal-download-journal-changed')
                require(permission(),'original-ticket-expired-before-link-intent')
                intent={'mode':'open-download-link','state':'unknown','expected_pid':pid,'bridge_focus':proof,'ticket':s['download_ticket'],
                    'formal_journal':saved['formal_journal'],'list_intent':{'path':str(list_path),'sha256':popup.sha(list_path)},
                    'target':{'path':link['path'],'window_path':window['path'],'label':DOWNLOAD_LABEL},'before':before,'intent_at':popup.now(),'replayed':False}
                popup.atomic(outdir/'link-intent.json',intent);saved.update(phase='download-link-intent',link_intent_sha256=popup.sha(outdir/'link-intent.json'));popup.atomic(manifest,saved)
                require(permission(),'original-ticket-expired-before-sole-link-press')
                native.press(link['path'],window['path']);intent['press_returned_success']=True;popup.atomic(outdir/'link-intent.json',intent)
            finally:native.close()
            return reconcile(saved,manifest,invoke,at)
        except Exception as error:
            saved.update(state='await-readonly-reconcile' if not live_ticket(s['download_ticket'],at) else 'unknown',error=str(error),replayed=False)
            popup.atomic(manifest,saved)
            if not permission():return reconcile(saved,manifest,invoke,at)
            raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-order',type=Path,required=True);p.add_argument('--tab-id',type=int,required=True);p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--outdir',type=Path,required=True);p.add_argument('--list-intent',type=Path);p.add_argument('--allow-expired-readonly-reconcile',action='store_true',help='Requires reviewed v5 public downloads.search; never creates a ticket');a=p.parse_args()
    try:
        result=recover(json.loads(a.work_order.read_text()),a.tab_id,a.expected_pid,a.outdir,list_intent=a.list_intent,allow_expired_readonly_reconcile=a.allow_expired_readonly_reconcile)
        print(json.dumps({'ok':result['state']=='complete','state':result['state'],'phase':result['phase'],'journal':str(a.outdir.resolve()/'recovery.json'),'replayed':False,'new_ticket_created':False,'new_download_click':False},ensure_ascii=False));return 0 if result['state']=='complete' else 2
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'replayed':False,'new_ticket_created':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
