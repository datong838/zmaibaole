#!/usr/bin/env python3
"""Dispatch-bound daily role entry. No director initialization or scheduling.
start includes order validation and formal flow init; advance hands the existing
browser work order to the operator only after web-action-intent is durable.
notify seals every required original order before calling the original outbox.

Use start --mode acceptance, advance --tab-id ID, execute only the returned
browser argv, then advance again. When notification-ready, use notify. Repeat
commands preserve the clock and original keys; unknowns remain original holds.
This is a formal business entry, not a rehearsal or foreman activation command.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
import execution_timing as timing
import daily_dispatch_order as dispatch


def need(ok,reason):
    if not ok:raise ValueError(reason)
def write(path,value):timing.save(Path(path),value)
def read(path):return json.loads(Path(path).read_bytes())
def location(order_path):
    # The order filename is the fixed dispatch identity; never accept a free
    # run/key/output path that could hide an earlier unknown intent.
    p=Path(order_path).resolve();return p.parent.parent/'daily-executions'/p.stem

def immutable(path,value):
    raw=dispatch.encode(value);path=Path(path)
    if path.exists():need(path.read_bytes()==raw,'daily-timing-immutable-conflict')
    else:
        import os,tempfile
        path.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,path)
            except FileExistsError:need(path.read_bytes()==raw,'daily-timing-immutable-conflict')
        finally:os.unlink(tmp)
    return timing.ref(path)

class FormalPorts:
    def command(self,args):
        p=subprocess.run([sys.executable,*map(str,args)],capture_output=True,text=True)
        try:value=json.loads(p.stdout)
        except ValueError:raise ValueError('daily-timing-formal-cli-output-invalid')
        need(p.returncode==0,'daily-timing-formal-cli-stopped:'+str(value.get('error',value.get('action','unknown'))));return value
    def init(self,order,run_dir,progress):
        # The dispatch has already fixed every company's cursor -> exclusive day.
        # Calendar scheduling belongs before dispatch, not a second planning gate.
        need(order.get('scope',{}).get('workflow')=='daily-comment-stats' and order['scope'].get('company_ranges') and all(x['start']<x['end_exclusive']==order['day'] for x in order['scope']['company_ranges']),'daily-timing-explicit-dispatch-range-required')
        archive_root=Path(order['offer']['path']).parent.parent;order_ref=timing.ref(dispatch.canonical_path(archive_root,order['dispatch_id']))
        need(dispatch.validate(order_ref,archive_root)==order,'daily-timing-original-init-order-required')
        argv=[Path(__file__).with_name('flow.py'),'init','--today',order['day'],'--outdir',run_dir,'--progress-file',progress,'--notification-work-root',PROJECT/'work','--force','--dispatch-order',order_ref['path'],'--dispatch-order-sha256',order_ref['sha256']]
        if order.get('collection_contract'):argv+=['--delivery-contract',order['collection_contract']]
        return self.command(argv)
    def advance(self,run_dir):return self.command([Path(__file__).with_name('flow.py'),'advance','--run-dir',run_dir])
    def prepare(self,batch_path,outbox):
        import notification_backlog as b
        return b.prepare_batch(batch_path,outbox,timing.SENDER_DIRECTORY)
    def inspect(self,queue):
        import notification_backlog as b
        return b.inspect(queue,True)
    def run(self,outbox,steps):
        import notification_backlog as b
        return b.run(outbox,steps)


def checked(root,order_ref,archive_root):
    order=dispatch.validate(order_ref,archive_root);s=read(root/'state.json');need(s['order']==order_ref and s['scope_sha256']==order['scope_sha256'],'daily-timing-original-execution-required');need(root==location(order_ref['path']),'daily-timing-canonical-execution-required');return order,s

def check_batch(batch,order,run_dir):
    need(not (batch.get('ok') is False and batch.get('reason')=='today_not_workday'),'daily-calendar-not-workday-no-batch-created')
    need(batch.get('flow')=='daily-comment-stats' and batch.get('mode')=='agent-live' and batch.get('run_dir')==str(run_dir) and batch.get('requested_date_range',{}).get('today')==order['day'],'daily-timing-batch-binding-invalid')
    expected={x['company']:x for x in order['scope']['company_ranges']};skipped={x['company'] for x in order['skipped_companies']};rows=batch.get('companies',[])
    need(len(rows)==len(expected)+len(skipped) and {r['company'] for r in rows}==set(expected)|skipped,'daily-timing-company-set-invalid')
    for r in rows:
        if r['company'] in skipped:need(r.get('status')=='skipped' and r.get('skip_reason')=='already_covered','daily-timing-completed-company-reexecuted');continue
        x=expected[r['company']];from datetime import date,timedelta
        need(str(r.get('groupid'))==x['groupid'] and r.get('date_range',{}).get('start')==x['start'] and r.get('date_range',{}).get('end')==(date.fromisoformat(x['end_exclusive'])-timedelta(days=1)).isoformat(),'daily-timing-company-range-invalid')
    need(batch.get('delivery_contract')==order.get('collection_contract'),'daily-timing-collection-contract-mismatch')
    return batch


def start(order_ref,archive_root,*,mode='development',clock=None,ports=None):
    clock=clock or timing.Clock()
    # First substantive operator call: the timing API samples before dispatch
    # validation. No business imports, progress reads or planning precede it.
    timing.start_from_order(lambda:location(order_ref['path'])/'timing.json','daily-'+Path(order_ref['path']).stem,order_ref,lambda r:dispatch.validate(r,archive_root),mode=mode,clock=clock)
    root=location(order_ref['path']);order=dispatch.validate(order_ref,archive_root);ports=ports or FormalPorts()
    with timing.locked(root/'state.json') as state_path:
        if state_path.exists():
            _,s=checked(root,order_ref,archive_root);return result(root,s,clock)
        offer=timing.pinned(order['offer']);entry=offer['ledger_snapshots'][0];progress=Path(entry['original_path']);need(progress.is_file() and timing.ref(progress)['sha256']==entry['snapshot']['sha256'],'daily-timing-progress-changed-before-plan')
        run_dir=PROJECT/'work'/order['day']/('daily-timed-'+Path(order_ref['path']).stem[:24])
        if order['origin']=='resume':
            prior_root=location(order['resumed_from']['path']);prior=read(prior_root/'state.json');need(prior['order']==order['resumed_from'] and prior['phase']!='complete','daily-timing-resume-execution-missing');previous=dispatch.validate(order['resumed_from'],archive_root);need(previous['scope']==order['scope'],'daily-timing-resume-scope-changed-use-original-execution');run_dir=Path(prior['run_dir'])
        else:need(not (run_dir/'batch_receipt.json').exists(),'daily-timing-fresh-business-run-preexists')
        s={'kind':'daily-timed-role-v1','order':order_ref,'scope_sha256':order['scope_sha256'],'run_dir':str(run_dir),'phase':'init-intent','outbox':str(root/'outbox')};write(state_path,s)
    return initialize(root,order_ref,archive_root,clock=clock,ports=ports)


def initialize(root,order_ref,archive_root,*,clock,ports):
    with timing.locked(root/'state.json') as path:
        order,s=checked(root,order_ref,archive_root)
        if s['phase']=='init-intent':
            progress=timing.pinned(order['offer'])['ledger_snapshots'][0]['original_path'];batch=ports.init(order,Path(s['run_dir']),progress);check_batch(batch,order,Path(s['run_dir']));s['phase']='acquisition';write(path,s)
        return result(root,s,clock)


def result(root,s,clock):
    with timing.locked(root/'timing.json') as path:
        ts=timing.load(path,clock)
        if ts['status']=='complete' and ts.get('outcome')=='client-confirmed':timing.clients(timing.pinned(ts['completion']),ts,clock)
        elif ts['status']=='complete' and ts.get('outcome')=='no-data-complete':timing.no_data(timing.pinned(ts['completion']),ts)
        telemetry=timing.view(ts,clock)
    return {'phase':s['phase'],'run_dir':s['run_dir'],'timing':telemetry,**({'collection_ready':s['collection_ready'],'delivery_complete':False}if s.get('collection_ready')else{}),**({'handoff':s['handoff']} if s.get('handoff') else {})}


@__import__('ds_common').dom_command_function
def advance(order_ref,archive_root,tab_id,*,clock=None,ports=None):
    need(type(tab_id) is int and tab_id>0,'daily-timing-explicit-tab-required');clock=clock or timing.Clock();ports=ports or FormalPorts();root=location(order_ref['path'])
    if read(root/'state.json')['phase']=='init-intent':initialize(root,order_ref,archive_root,clock=clock,ports=ports)
    with timing.locked(root/'state.json') as path:
        order,s=checked(root,order_ref,archive_root);need(s['phase']=='acquisition','daily-timing-not-acquisition');batch_path=Path(s['run_dir'])/'batch_receipt.json';check_batch(read(batch_path),order,Path(s['run_dir']))
        job=ports.advance(Path(s['run_dir']));check_batch(read(batch_path),order,Path(s['run_dir']))
        if job.get('action') in ('acquire','return-company'):
            with timing.locked(root/'timing.json') as tp:ts=timing.load(tp,clock)
            if not any(e['kind']=='first-webpage-action-intent' for e in ts['events']):timing.mark_web_action(root/'timing.json',clock=clock)
            need(job.get('backend')=='local-dom-bridge' and job.get('explicit_tab_id_required') is True and Path(job['work_order_path']).is_file(),'daily-timing-original-browser-handoff-required')
            s['handoff']={'work_order':timing.ref(job['work_order_path']),'argv':[sys.executable,str(PROJECT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'--work-order',job['work_order_path'],'--tab-id',str(tab_id),'--steps','25'],'action':job['action']}
        elif job.get('action')=='done':
            batch=read(batch_path);need(batch.get('status')=='complete','daily-timing-processing-not-complete');s.pop('handoff',None)
            if order.get('collection_contract')=='three-flow-collection-ready-v1':
                import notification_backlog as backlog
                progress=Path(timing.pinned(order['offer'])['ledger_snapshots'][0]['original_path'])
                ready=backlog.prepare_collection_ready(batch_path,root/'collection-ready.json',timing.ref(progress),order['company_config'])
                s['collection_ready']=ready;s['phase']='collection-ready'
            else:s['phase']='notification-ready'
        else:s['handoff']=job
        write(path,s);return result(root,s,clock)


def zero_reference(root,s,order,row,receipt,clock):
    # prepare_batch has already replayed receipt_valid and source provenance.
    acquisition=Path(row['outdir'])/'acquisition.json';a=read(acquisition);x=next(x for x in order['scope']['company_ranges'] if x['company']==row['company'])
    need(a.get('account_verified') is True and a.get('company')==row['company'] and str(a.get('groupid'))==x['groupid'] and a.get('page_filtered')==0 and a.get('backend')=='local-dom-bridge','daily-timing-zero-source-unverified')
    from ds_processor import acquisition_check
    r=read(receipt);need(acquisition_check(a,row,Path(r['src_file']),row['date_range']) is True and a.get('page_filtered')==r.get('row_count')==0,'daily-timing-zero-source-unverified')
    observed=a.get('recorded_at',a.get('observed_at'));need(observed is not None,'daily-timing-zero-observation-time-required')
    value={'workflow':'daily-comment-stats','run_id':read(root/'timing.json')['run_id'],'work_order':s['order'],'scope_sha256':order['scope_sha256'],'source':'local-dom-bridge','fixture':False,'account_verified':True,'complete':True,'row_count':0,'raw_evidence':[timing.ref(receipt),timing.ref(acquisition)],'observed_at':observed,**x}
    return immutable(root/('zero-'+timing.digest(x)+'.json'),value)


def notify(order_ref,archive_root,*,steps=25,clock=None,ports=None):
    clock=clock or timing.Clock();ports=ports or FormalPorts();root=location(order_ref['path']);need(type(steps) is int and 1<=steps<=100,'daily-timing-step-limit')
    with timing.locked(root/'state.json') as path:
        order,s=checked(root,order_ref,archive_root)
        if s['phase']=='complete':return result(root,s,clock)
        need(s['phase'] in ('notification-ready','notification-pending'),'daily-timing-not-notification-ready');batch_path=Path(s['run_dir'])/'batch_receipt.json';batch=check_batch(read(batch_path),order,Path(s['run_dir']));need(batch['status']=='complete','daily-timing-processing-not-complete')
        with timing.locked(root/'timing.json') as tp:prior_timing=timing.load(tp,clock)
        if prior_timing['status']=='complete':
            receipt=timing.pinned(prior_timing['completion']);need(prior_timing['outcome'] in ('client-confirmed','no-data-complete'),'daily-timing-incomplete-not-business-complete')
            if prior_timing['outcome']=='client-confirmed':timing.clients(receipt,prior_timing,clock)
            else:timing.no_data(receipt,prior_timing)
            s['phase']='complete';write(path,s);return result(root,s,clock)
        queue=Path(ports.prepare(batch_path,Path(s['outbox'])));q=read(queue);need(q['batch']==timing.ref(batch_path) and Path(q['messenger_directory']).resolve()==timing.SENDER_DIRECTORY.resolve(),'daily-timing-outbox-binding-invalid')
        plans=[];zeros=[];sources=[timing.ref(batch_path),timing.ref(queue)];pending={x['company'] for x in order['scope']['company_ranges']}
        for row in batch['companies']:
            if row['company'] not in pending:continue
            receipt=Path(row.get('receipt') or Path(row['outdir'])/'receipt.json');sources.append(timing.ref(receipt))
            if row['status']=='zero_rows'and q.get('zero_result_contract')!='notify-confirmed-zero-v1':zeros.append(zero_reference(root,s,order,row,receipt,clock))
            else:plans.append(timing.ref(receipt.parent/'test-notifications/orders.json'))
        ts=read(root/'timing.json');common={'run_id':ts['run_id'],'work_order':order_ref,'scope_sha256':order['scope_sha256']}
        if q['items']:
            manifest={'kind':'workflow-delivery-manifest-v1',**common,'company_ranges':order['scope']['company_ranges'],'source_refs':sources,'source_plans':plans,'expected_send_keys':[x['key'] for x in q['items']]}
            if zeros:manifest['zero_acquisitions']=zeros
            mr=immutable(root/'delivery-manifest.json',manifest);timing.seal_delivery(root/'timing.json',mr,clock=clock)
            s['phase']='notification-pending';s['queue']=timing.ref(queue);write(path,s)
            # Sole send boundary. All keys, payloads and mixed-zero sources are
            # sealed above before the original runner can first prepare a job.
            need(list(Path(s['outbox']).glob('*/outbox.json'))==[queue],'daily-timing-unexpected-outbox-scope');ports.run(Path(s['outbox']),steps);inspection=ports.inspect(queue)
            if not inspection['complete']:return result(root,s,clock)
            acceptance=timing.pinned(inspection['acceptance']);cr=immutable(root/'client-confirmation.json',{'kind':'workflow-client-confirmation-v1',**common,'delivery_manifest_sha256':mr['sha256'],'client_jobs':[{'path':r['path'],'sha256':r['sha256']} for r in acceptance['jobs']]});timing.finish(root/'timing.json','client-confirmed',cr,clock=clock)
        else:
            need(len(zeros)==len(pending),'daily-timing-allzero-evidence-incomplete');cr=immutable(root/'no-data-confirmation.json',{'kind':'workflow-no-data-completion-v1',**common,'fixture':False,'live':True,'row_count':0,'acquisitions':zeros});timing.finish(root/'timing.json','no-data-complete',cr,clock=clock)
        s['phase']='complete';write(path,s);return result(root,s,clock)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=('start','advance','notify','status'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--archive-root',required=True);p.add_argument('--mode',choices=('development','acceptance'),default='development');p.add_argument('--tab-id',type=int);p.add_argument('--steps',type=int,default=25);a=p.parse_args(argv)
    try:
        order_ref={'path':str(Path(a.order).absolute()),'sha256':a.order_sha256}
        if a.verb=='start':value=start(order_ref,a.archive_root,mode=a.mode)
        elif a.verb=='advance':value=advance(order_ref,a.archive_root,a.tab_id)
        elif a.verb=='notify':value=notify(order_ref,a.archive_root,steps=a.steps)
        else:
            root=location(a.order);_,s=checked(root,order_ref,a.archive_root);value=result(root,s,timing.Clock())
        print(json.dumps(value,ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps({'ok':False,'error':str(e),'acceptance_pass':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
