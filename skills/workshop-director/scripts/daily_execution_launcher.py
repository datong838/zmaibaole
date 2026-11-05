#!/usr/bin/env python3
"""Controlled parent for daily_timed_run CLI; never initializes a director.

The acceptance interval starts before the first daily Python child is launched
and ends after the final notify child exits AND source/client replay succeeds.
It spans later invocations, handoffs and waits using system CLOCK_MONOTONIC.
The parent's own initial interpreter bootstrap and final telemetry fsync are
outside this boundary. Inner API timing is diagnostic, never the final gate.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
# Public script and isolated API have the same fixed proof dependency closure.
PROJECT=Path(__file__).resolve().parents[3]
for _directory in (PROJECT/'skills/workshop-director/scripts',PROJECT/'skills/daily-comment-stats/scripts',PROJECT/'skills/douyin-laike-operator/scripts'):
    if _directory.resolve()!=_directory or not _directory.is_dir()or any(p.is_symlink()for p in(_directory,*_directory.parents)):raise ValueError('daily-parent-fixed-bootstrap-origin')
    sys.path.insert(0,str(_directory))
import execution_timing as timing
import daily_dispatch_order as dispatch

PROJECT=Path(__file__).resolve().parents[3]
FORMAL_CLI=PROJECT/'skills/daily-comment-stats/scripts/daily_timed_run.py'
KIND='daily-parent-execution-v1'
VERBS=('start','advance','notify')
FINAL_FIELDS=('outcome','end_monotonic','wall_ended_at','acceptance_pass','full_workflow_measured','completion_proof')
ORIGIN_FIELDS=('kind','run_id','order','archive_root','scope_sha256','origin','mode','clock_contract','boot_identity','start_monotonic','wall_started_at','code_refs')


def need(ok,reason):
    if not ok:raise ValueError(reason)
def read(path):return json.loads(Path(path).read_bytes())
def location(order_ref):
    p=Path(order_ref['path']).resolve();return p.parent.parent/'daily-parent-executions'/p.stem

def code_refs():
    paths=[Path(__file__),FORMAL_CLI,Path(timing.__file__),Path(dispatch.__file__),FORMAL_CLI.with_name('notification_backlog.py'),FORMAL_CLI.with_name('flow.py')]
    return [timing.ref(p) for p in paths]

# Only these reviewed historical bytes are data. They are never imported/executed.
LEGACY_INIT_CODES = {'/Users/feibing/work/projects/zmaibaole/skills/daily-comment-stats/scripts/daily_timed_run.py': '99e5b8abbcff13879b64366a53013b48bbf631f10a13ee8c2c9297800662a0f0', '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/daily_execution_launcher.py': 'fdaca1a9a9ebff89af518fdf18ac9be329afc8da7b2aeb33377caebc22a10c70'}
ZERO_INIT_PARENT_SHA='8b77c546a45e9bd495433e661e9384971f75ca5a7eb7cb2821bf6145fcc269af'
ZERO_INIT_ROLE_SHA='9b9429f676f6de6e9d56335d07ea1edfbd9c8a352497e519251d8ca520ba99ce'
ZERO_INIT_FAILURE_SHA='b9bbfe78352a921ecd36903185be5741770b129d39293aec9a0e4eca428568d9'
ZERO_INIT_ORDER_SHA='96f26ec7156530f140fe05aa17c792cf33221b51e75396a580c0a89fe95c87a9'

def historical_code_bytes(r,*,sealed=False):
    p=Path(r['path']);need(p.is_absolute() and not p.is_symlink() and str(p.resolve())==str(p),'daily-source-canonical-required')
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()==r['sha256']:return raw
    need(LEGACY_INIT_CODES.get(str(p))==r['sha256'] or sealed and str(p) in {v['path'] for v in code_refs()},'daily-unreviewed-historical-source')
    archive=PROJECT/'skills/workshop-director/references/daily-source-archives'/(r['sha256']+'.py')
    need(not archive.is_symlink() and archive.resolve()==archive,'daily-archive-canonical-required')
    return timing.checked_bytes({'path':str(archive),'sha256':r['sha256']})

def immutable_raw(path,raw):
    import os,tempfile
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(not path.is_symlink() and path.read_bytes()==raw,'daily-raw-archive-conflict');return timing.ref(path)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:need(not path.is_symlink() and path.read_bytes()==raw,'daily-raw-archive-conflict')
    finally:os.unlink(tmp)
    return timing.ref(path)

def zero_init_exception(root,s,call,receipt,*,historical=False):
    path=Path(root)/'zero-init-recovery.json'
    if not path.exists():return False
    if historical:need(s.get('status')=='complete' and s.get('completion_proof',{}).get('zero_init_recovery')==timing.ref(path),'daily-zero-init-historical-seal-required')
    recovery=read(path);need(recovery.get('kind')=='daily-known-calendar-zero-init-recovery-v1','daily-zero-init-recovery-kind')
    baseline=timing.pinned(recovery['parent_before']);need(recovery['parent_before']['sha256']==ZERO_INIT_PARENT_SHA and baseline['order']['sha256']==ZERO_INIT_ORDER_SHA,'daily-zero-init-fixed-parent')
    need(s['origin_ref']==baseline['origin_ref'] and all(s[k]==baseline[k] for k in ORIGIN_FIELDS),'daily-zero-init-origin-changed')
    need(call==baseline['calls'][0] and receipt==timing.pinned(call['result']) and recovery['failed_child']==call['result'],'daily-zero-init-failed-prefix-changed')
    need(call['index']==0 and call['verb']=='start' and call['state']=='failed' and receipt['returncode']==2 and json.loads(receipt['stdout'])=={'ok':False,'error':'daily-timing-batch-binding-invalid','acceptance_pass':False},'daily-zero-init-not-known-exit')
    need(recovery['role_before']['sha256']==ZERO_INIT_ROLE_SHA and timing.pinned(recovery['role_before'])['phase']=='init-intent','daily-zero-init-role-changed')
    need(recovery['failure']['sha256']==ZERO_INIT_FAILURE_SHA,'daily-zero-init-failure-not-reviewed');timing.pinned(recovery['failure'])
    if historical:
        refs=recovery['current_code_refs'];need(len(refs)==6 and len({v['path'] for v in refs})==6 and {v['path'] for v in refs}=={v['path'] for v in code_refs()},'daily-zero-init-historical-source-set')
        for ref in refs:historical_code_bytes(ref,sealed=True)
    else:
        need(recovery['current_code_refs']==code_refs(),'daily-zero-init-current-source-changed')
        for ref in recovery['current_code_refs']:timing.checked_bytes(ref)
    return True

def completed_source_seal(s,root):
    """Completed immutable evidence may read pinned archived code as data only.
    This does not admit a live source migration or certify business completion;
    the existing verify_complete replay remains required by every consumer.
    """
    root=Path(root)
    need(s.get('status')=='complete' and root==location(s['order']),'daily-historical-complete-parent-required')
    need(timing.pinned(s['origin_ref'])=={k:s[k]for k in ORIGIN_FIELDS},'daily-historical-origin-changed')
    r=s.get('completion_ref');need(type(r)is dict and set(r)=={'path','sha256'} and r['path']==str(root/'completion.json'),'daily-historical-canonical-completion-required')
    final=timing.pinned(r)
    need(final=={'kind':'daily-parent-completion-v1','run_id':s['run_id'],'order':s['order'],'origin_ref':s['origin_ref'],**{k:s[k]for k in FINAL_FIELDS}},'daily-historical-completion-record-changed')
    refs=s['code_refs'];need(type(refs)is list and len(refs)==6 and len({v['path']for v in refs})==6 and {v['path']for v in refs}=={v['path']for v in code_refs()},'daily-historical-exact-six-source-set')
    return True

def source_code_bytes(r,s,root):
    if s.get(BACKLOG_INIT_FIELD):
        admitted=verify_backlog_init_recovery(s,s[BACKLOG_INIT_FIELD]);need(r in s['code_refs'],'daily-backlog-init-original-slot');return historical_code_bytes(r,sealed=True)if s['status']=='complete'else timing.checked_bytes(next(x['material']for x in admitted['verification_refs']if x['original']==r))
    if s.get(NOTIFY_RECOVERY_FIELD) and s.get('status')=='complete':
        completed_source_seal(s,root);verify_notify_prepare_recovery(s,s[NOTIFY_RECOVERY_FIELD]);need(r in s['code_refs'],'daily-notify-completed-original-slot');return historical_code_bytes(r,sealed=True)
    if s.get(NOTIFY_RECOVERY_FIELD):
        admitted=verify_notify_prepare_recovery(s,s[NOTIFY_RECOVERY_FIELD]);need(r in s['code_refs'],'daily-notify-original-code-slot');return timing.checked_bytes(next(x for x in admitted['verification_refs']if x['original']==r)['material'])
    try:return timing.checked_bytes(r)
    except ValueError:
        if s.get('calls')and staged_init_exception(s,s['calls'][0],timing.pinned(s['calls'][0]['result'])):
            return timing.checked_bytes(timing.configuration_source_material(r)['material'])
        # B94b: a live run accepts reviewed code succession for its own pinned
        # slots - the finite configuration-source chain (published successor
        # link + supervisor-reviewed release) must reach exactly the current
        # bytes, else the walk fails closed and the original gate below stands.
        if s.get('calls'):
            try:return timing.checked_bytes(timing.configuration_source_material(r)['material'])
            except timing.TimingError:pass
        if s.get('status')=='complete':
            completed_source_seal(s,root);need(r in s['code_refs'],'daily-historical-source-not-in-sealed-parent');return historical_code_bytes(r,sealed=True)
        need(s['calls'] and zero_init_exception(root,s,s['calls'][0],timing.pinned(s['calls'][0]['result'])),'daily-live-source-change-not-authorized')
        return historical_code_bytes(r)

def repair_zero_init(failure_ref,*,order_ref=None,archive_root=None,clock=None):
    """One reviewed zero-effect failure; no init, child, dispatch or clock reset."""
    clock=clock or timing.Clock();need(failure_ref['sha256']==ZERO_INIT_FAILURE_SHA,'daily-zero-init-failure-not-reviewed');failure=timing.pinned(failure_ref)
    original_parent=timing.pinned(failure['parent']);need(order_ref is None or order_ref==original_parent['order'],'daily-zero-init-request-order-changed');need(archive_root is None or str(Path(archive_root).resolve())==original_parent['archive_root'],'daily-zero-init-request-root-changed');order_ref=original_parent['order'];root=location(order_ref);path=root/'state.json'
    with timing.locked(path):
        s=read(path);sidecar=root/'zero-init-recovery.json'
        if sidecar.exists():
            need(zero_init_exception(root,s,s['calls'][0],timing.pinned(s['calls'][0]['result'])),'daily-zero-init-recovery-invalid');return timing.ref(sidecar)
        need(timing.ref(path)['sha256']==ZERO_INIT_PARENT_SHA and order_ref['sha256']==ZERO_INIT_ORDER_SHA,'daily-zero-init-fixed-parent')
        order=dispatch.validate(order_ref,s['archive_root']);need(s['scope_sha256']==order['scope_sha256'] and s['status']=='attention' and len(s['calls'])==1,'daily-zero-init-frontier')
        need(timing.pinned(s['origin_ref'])=={k:s[k] for k in ORIGIN_FIELDS} and clock.boot()==s['boot_identity'] and clock.monotonic()>=s['start_monotonic'],'daily-zero-init-original-clock')
        for ref in s['code_refs']:historical_code_bytes(ref)
        call=s['calls'][0];pair=child_receipt(root,s,call,clock);need(pair is not None and call['state']=='failed','daily-zero-init-natural-exit-required');_,receipt=pair
        need(call['index']==0 and call['verb']=='start' and receipt['returncode']==2 and json.loads(receipt['stdout'])=={'ok':False,'error':'daily-timing-batch-binding-invalid','acceptance_pass':False},'daily-zero-init-not-known-exit')
        need(timing.pinned(call['launch'])=={k:v for k,v in call.items() if k not in ('launch','state','result')},'daily-zero-init-launch-changed')
        inner=Path(order_ref['path']).parent.parent/'daily-executions'/Path(order_ref['path']).stem;role=read(inner/'state.json');need(timing.ref(inner/'state.json')['sha256']==ZERO_INIT_ROLE_SHA and role['order']==order_ref and role['phase']=='init-intent','daily-zero-init-role-changed')
        ts=timing.load(inner/'timing.json',clock);need(not ts['events'] and not ts['stages'] and ts['status']=='running','daily-zero-init-business-already-started')
        run=Path(role['run_dir']);need(not run.exists() or not list(run.iterdir()),'daily-zero-init-batch-or-output-present')
        sys.path.insert(0,str(FORMAL_CLI.parent))
        from ds_calendar import compute
        need(compute(order['day']).get('reason')=='today_not_workday','daily-zero-init-not-calendar-skip')
        pp=timing.pinned(order['offer'])['ledger_snapshots'][0];need(timing.ref(pp['original_path'])['sha256']==pp['snapshot']['sha256'],'daily-zero-init-progress-changed')
        before=immutable_raw(root/'zero-init-parent-before.json',path.read_bytes());rb=immutable_raw(root/'zero-init-role-before.json',(inner/'state.json').read_bytes())
        recovery={'kind':'daily-known-calendar-zero-init-recovery-v1','failure':failure_ref,'parent_before':before,'role_before':rb,'failed_child':call['result'],'current_code_refs':code_refs(),'recorded_at':clock.wall().isoformat(),'original_clock_preserved':True,'business_actions_performed':False}
        # Publication is the sole effect. Original parent/role/calls remain bytes-identical.
        return immutable(sidecar,recovery)

def immutable(path,value):
    # Reuse the immutable-publication implementation, without importing any UI
    # code or executing the role. JSON result receipts are never overwritten.
    raw=dispatch.encode(value);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(not path.is_symlink() and path.read_bytes()==raw,'daily-parent-immutable-conflict');return timing.ref(path)
    import os,tempfile
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:need(not path.is_symlink() and path.read_bytes()==raw,'daily-parent-immutable-conflict')
    finally:os.unlink(tmp)
    return timing.ref(path)

def argv_for(order_ref,archive_root,verb,mode,tab_id,steps):
    need(verb in VERBS and mode in ('development','acceptance'),'daily-parent-command-invalid')
    # The scheduler may read receipts under its own Python. Original daily
    # producers use this fixed interpreter, so argv proof is reader-independent.
    python=PROJECT/'skills/daily-comment-stats/.venv/bin/python'
    need(python.is_file(),'daily-parent-fixed-python-required')
    argv=[str(python),str(FORMAL_CLI),verb,'--order',order_ref['path'],'--order-sha256',order_ref['sha256'],'--archive-root',str(Path(archive_root).resolve())]
    if verb=='start':argv+=['--mode',mode]
    if verb=='advance':need(type(tab_id) is int and tab_id>0,'daily-parent-explicit-tab-required');argv+=['--tab-id',str(tab_id)]
    if verb=='notify':need(type(steps) is int and 1<=steps<=100,'daily-parent-step-limit');argv+=['--steps',str(steps)]
    return argv

def subprocess_child(argv):
    # No timeout/cancel/retry on 30s. The original workflow owns all UI intents.
    return subprocess.run(argv,capture_output=True,text=True)

def origin_entry_matches(s,origin):
    # origin.json stays the byte-freeze of the original parent entry; the six
    # code slots only move through reviewed publications. Replay the state's
    # own source_generations chain (path-keyed previous->current, w121
    # precedent in collection_ready) over the frozen refs and require it to
    # land exactly on the live code_refs; any other field drift and a broken,
    # duplicated or fabricated chain stays fatal.
    need(type(origin)is dict and set(origin)==set(ORIGIN_FIELDS),'daily-parent-original-entry-shape')
    projected={k:s[k] for k in ORIGIN_FIELDS}
    need(all(origin[k]==projected[k] for k in ORIGIN_FIELDS if k!='code_refs'),'daily-parent-original-entry-changed')
    replayed=[dict(r)for r in origin['code_refs']]
    by={r['path']:r for r in replayed};need(len(by)==len(replayed),'daily-parent-original-entry-duplicate')
    for g in s.get('source_generations',[]):
        need(type(g)is dict and {'path','previous_sha256','current_sha256'}<=set(g),'daily-parent-generation-fields')
        row=by.get(g['path']);need(row is not None and row['sha256']==g['previous_sha256'],'daily-parent-generation-chain')
        row['sha256']=g['current_sha256']
    need(replayed==projected['code_refs'],'daily-parent-original-entry-changed')
    return True

def load(path,order_ref,archive_root,clock):
    s=read(path);need(s.get('kind')==KIND and s.get('order')==order_ref and s.get('archive_root')==str(Path(archive_root).resolve()),'daily-parent-binding-invalid')
    origin=timing.pinned(s['origin_ref']);origin_entry_matches(s,origin)
    order=dispatch.validate(order_ref,archive_root);need(s['scope_sha256']==order['scope_sha256'] and s['origin']==order['origin'],'daily-parent-scope-invalid')
    need(s.get('clock_contract')==timing.MONOTONIC_CLOCK and clock.boot()==s['boot_identity'],'daily-parent-clock-or-boot-changed')
    now=clock.monotonic();need(timing.finite(s['start_monotonic']) and timing.finite(now) and now>=s['start_monotonic'],'daily-parent-monotonic-invalid')
    for r in s['code_refs']:source_code_bytes(r,s,location(order_ref))
    if s['status']=='complete':
        final=timing.pinned(s['completion_ref']);need(final=={'kind':'daily-parent-completion-v1','run_id':s['run_id'],'order':s['order'],'origin_ref':s['origin_ref'],**{k:s[k] for k in FINAL_FIELDS}},'daily-parent-completion-record-changed')
    need(path==location(order_ref)/'state.json','daily-parent-canonical-path-required')
    return s,order

def child_receipt(root,s,call,clock):
    ref=call.get('result')
    if ref is None:
        p=root/'children'/('%04d-result.json'%call['index'])
        if not p.exists():return None
        ref=timing.ref(p)
    receipt=timing.pinned(ref)
    need(receipt.get('kind')=='daily-child-exit-v1' and receipt.get('launch')==call['launch'] and receipt.get('run_id')==s['run_id'] and receipt.get('order')==s['order'],'daily-parent-child-receipt-invalid')
    need(receipt['argv']==call['argv'] and type(receipt['returncode']) is int and timing.finite(receipt['exited_monotonic']) and receipt['exited_monotonic']>=call['launch_monotonic'] and receipt['exited_monotonic']<=clock.monotonic(),'daily-parent-child-exit-invalid')
    need(receipt['boot_identity']==s['boot_identity'],'daily-parent-child-boot-invalid')
    need(Path(ref['path'])==root/'children'/('%04d-result.json'%call['index']),'daily-parent-canonical-child-receipt-required')
    return ref,receipt

def receipt_output(receipt,s):
    output=json.loads(receipt['stdout']);need(type(output) is dict and type(output.get('timing')) is dict,'daily-parent-child-json-required')
    inner=output['timing'];need(inner.get('run_id')=='daily-'+Path(s['order']['path']).stem and inner.get('mode')==s['mode'] and inner.get('origin')==s['origin'],'daily-parent-child-output-binding-invalid')
    return output

def staged_init_exception(s,call,receipt):
    # Formal init has no browser/sender input. Preserve its natural failure and
    # continue with advance only for the known legacy/staged notification clash.
    if call.get('index')!=0 or call.get('verb')!='start' or receipt.get('returncode')!=2 or receipt.get('stderr')!='':return False
    try:output=json.loads(receipt['stdout'])
    except (ValueError,KeyError,TypeError):return False
    expected="daily-timing-formal-cli-stopped:{'code': 'configuration-error', 'message': 'staged-batch-requires-unified-delivery'}"
    if output!={'ok':False,'error':expected,'acceptance_pass':False}:return False
    return timing.pinned(s['order']).get('collection_contract')=='three-flow-collection-ready-v1'

def staged_reservation_rebind_exception(s,call,receipt):
    """B94: the staged collection reservation stopped the formal CLI because a
    supervised re-collection rewrote the receipt bytes (reservation-binding-
    conflict). The rebind itself is fixed in ds_progress (undelivered
    'collection-ready' slots rebind to the freshly verified artifact); this
    admission is purely factual - the exact error shape on an advance call
    under the staged collection contract - so the repaired advance may run."""
    if call.get('verb')!='advance' or receipt.get('returncode')!=2 or receipt.get('stderr')!='':return False
    try:output=json.loads(receipt['stdout'])
    except (ValueError,KeyError,TypeError):return False
    expected="daily-timing-formal-cli-stopped:{'code': 'reservation-binding-conflict', 'message': 'reservation-binding-conflict'}"
    if output!={'ok':False,'error':expected,'acceptance_pass':False}:return False
    return timing.pinned(s['order']).get('collection_contract')=='three-flow-collection-ready-v1'

def reverify_advance_exception(s,call,receipt):
    """The B59 needs_review advance rejection whose adjudication is the
    supervised reverify admission recorded in the flow world: the stopped
    round-1 batch and receipt are archived verbatim, export_pending is
    cleared and the company is reopened pending with budget left."""
    if call['verb']!='advance':return False
    # The admission was recorded before one typed-advance resume ran after
    # the rejected round-1 advance; that resume performed no input beyond
    # its own acquire handoff. Every later call must be a returned advance
    # or an admitted reverify-shape failed advance (the two shapes below —
    # the original needs_review rejection and the W130k-fixed resume-owner
    # refusal); anything else stays unapproved.
    def admitted_failure(c):
        if c.get('state')!='failed':return False
        try:r=json.loads(Path(c['result']['path']).read_bytes());o=json.loads(r['stdout'])
        except Exception:return False
        if r.get('returncode')!=2 or not(type(o)is dict and o.get('ok')is False and o.get('acceptance_pass')is False):return False
        e=o.get('error')
        return e=='daily-timing-processing-not-complete' or (type(e)is str and e=="daily-timing-formal-cli-stopped:{'code': 'work-order-resume-owned-by-journal', 'message': 'work-order-resume-owned-by-journal'}")
    for c in s['calls'][s['calls'].index(call)+1:]:
        if c.get('verb')!='advance':return False
        if c.get('state')=='returned' or admitted_failure(c):continue
        return False
    if receipt.get('returncode')!=2:return False
    try:out=json.loads(receipt['stdout'])
    except Exception:return False
    if not(type(out)is dict and out.get('ok')is False and out.get('acceptance_pass')is False):return False
    # Two admitted shapes share the same supervised admission and frontier:
    # the original B59 needs_review rejection, and the round's formal CLI
    # stopping on the resume-owner refusal that W130k fixed (the repr text is
    # matched exactly; any other code stays unapproved).
    error=out.get('error')
    if error=='daily-timing-processing-not-complete':pass
    elif type(error)is str and error=="daily-timing-formal-cli-stopped:{'code': 'work-order-resume-owned-by-journal', 'message': 'work-order-resume-owned-by-journal'}":pass
    else:return False
    inner=location(s['order']).parent.parent/'daily-executions'/Path(s['order']['path']).stem
    role=json.loads(timing.checked_bytes(timing.ref(inner/'state.json')))
    # Once the supervised closure has advanced the run to collection-ready the
    # historical rejection is verified against the decided facts, so the inner
    # role phase may legitimately sit one step past acquisition; the
    # adjudicated branch below re-checks the batch it came from. Any other
    # phase drift stays fatal.
    need(role.get('order')==s['order'] and role.get('phase') in ('acquisition','collection-ready'),'daily-reverify-inner-scope')
    batch=json.loads(timing.checked_bytes(timing.ref(Path(role['run_dir'])/'batch_receipt.json')))
    rv=batch.get('reverify')
    if rv is None:return False
    need(type(rv)is dict and rv.get('kind')=='supervised-export-count-reverify-v1' and type(rv.get('round'))is int and rv.get('company')and str(rv.get('groupid')),'daily-reverify-admission-required')
    row=next((r for r in batch['companies'] if r['company']==rv['company']),None)
    # A supervised closure (W130o accept-review) turns the reverify frontier
    # into a decided fact: the row is complete with an on-row adjudication and
    # the receipt itself carries the well-formed count-adjudication block
    # restating the exact receipt numbers for this round. The historical
    # needs_review rejection then stays an admitted failure with its verdict
    # verified here; without the closure the frontier checks below keep
    # gating the admission exactly as before.
    if row is not None and row.get('status')=='complete' and isinstance(row.get('review_adjudication'),dict) and batch.get('status')=='complete' and not batch.get('needs_review'):
        need(batch.get('roundtrip',{}).get('verified')is True and not batch.get('failed') and not [r for r in batch['companies'] if r['status']=='failed'],'daily-reverify-frontier')
        receipt_row=json.loads(timing.checked_bytes(timing.ref(Path(row['receipt']))))
        block=receipt_row.get('count_adjudication')
        need(isinstance(block,dict) and block.get('kind')=='supervised-count-adjudication-v1'
             and block.get('page_filtered')==receipt_row.get('page_filtered') and block.get('row_count')==receipt_row.get('row_count')
             and block.get('round')==rv['round']
             and receipt_row.get('status')=='complete' and receipt_row.get('mismatch')is False and not receipt_row.get('warnings')
             and type(receipt_row.get('page_filtered'))is int and type(receipt_row.get('row_count'))is int
             and receipt_row['row_count']!=receipt_row['page_filtered'],'daily-reverify-adjudication-unverified')
        return True
    need(row is not None and ((row['status']=='pending' and row.get('export_pending')is False and 0<row.get('attempts',0)<3) or (row['status']not in('failed','complete')and row.get('export_pending')is True and row.get('attempts')==rv['round']+1<3)),'daily-reverify-frontier')
    need(not batch.get('failed') and batch.get('roundtrip',{}).get('verified')is True and not [r for r in batch['companies'] if r['status']=='failed'],'daily-reverify-frontier')
    archive=Path(role['run_dir'])/'reverify-archive'
    for record in (rv['first_batch'],rv['first_receipt']):
        need(type(record)is dict and set(record)=={'path','sha256'},'daily-reverify-archive-shape')
        material=archive/(Path(record['path']).stem+'-'+record['sha256']+'.json')
        need(material.is_file() and not material.is_symlink(),'daily-reverify-archive-missing')
        need(hashlib.sha256(timing.checked_bytes(timing.ref(material))).hexdigest()==record['sha256'],'daily-reverify-archive-missing')
    return True

def resumed_pending_export_exception(s,call,receipt):
    """A stopped advance may be retried only after the original flow is reopened.

    This admits the historical failure, not its business result. The original
    operator still owns any pending export and all normal completion checks.
    """
    if call.get('verb')!='advance' or receipt.get('returncode')!=2:return False
    try:out=json.loads(receipt['stdout'])
    except (KeyError,TypeError,ValueError):return False
    if out!={'ok':False,'error':'daily-timing-processing-not-complete','acceptance_pass':False}:return False
    for later in s['calls'][s['calls'].index(call)+1:]:
        if later.get('state')=='returned':continue
        if later.get('state')!='failed' or later.get('verb')!='advance':return False
        try:result=timing.pinned(later['result']);value=json.loads(result['stdout'])
        except Exception:return False
        if result.get('returncode')!=2 or value!=out:return False
    sys.path.insert(0,str(FORMAL_CLI.parent))
    import daily_timed_run as role
    inner=location(s['order']).parent.parent/'daily-executions'/Path(s['order']['path']).stem
    order,state=role.checked(inner,s['order'],s['archive_root'])
    if state.get('phase') not in ('acquisition','collection-ready','notification-ready','notification-pending','complete'):return False
    batch=role.check_batch(json.loads(timing.checked_bytes(timing.ref(Path(state['run_dir'])/'batch_receipt.json'))),order,Path(state['run_dir']))
    if batch.get('reverify') is not None or batch.get('needs_review') or batch.get('failed') or any(r.get('status')=='failed' for r in batch['companies']):return False
    affected=[]
    for row in batch['companies']:
        journals=list((Path(row['outdir'])/'operator').glob('*/workflow.json')) if row.get('outdir') else []
        if len(journals)!=1:continue
        journal=json.loads(timing.checked_bytes(timing.ref(journals[0])))
        if not journal.get('retention_baseline_reconciliation'):continue
        if journal.get('company')!=row.get('company') or str(journal.get('groupid'))!=str(row.get('groupid')) or journal.get('date_range')!={k:row['date_range'][k] for k in ('start','end')}:return False
        if any(c.get('state')!='confirmed' for c in journal.get('calls',[])):return False
        affected.append((row,journal))
    if len(affected)!=1:return False
    row,journal=affected[0]
    if row.get('status')=='complete':return True
    return row.get('status') in ('pending','acquiring','acquired') and row.get('export_pending') is True and journal.get('phase') in ('pollRecords','armDownload','prepareDownload','clickDownload','downloadResult','done')

def approved_failed_child(root,s,call,receipt):
    """One failure policy for live replay and sealed historical admission."""
    if receipt.get('returncode')==0:return False
    if staged_init_exception(s,call,receipt):return True
    if staged_reservation_rebind_exception(s,call,receipt):return True
    if resumed_pending_export_exception(s,call,receipt):return True
    if reverify_advance_exception(s,call,receipt):return True
    if s.get(READY_SEAL_FIELD) and ready_seal_exception(s,call,receipt):return True
    if s.get(LOCAL_PROCESSING_FIELD) and local_processing_exception(s,call,receipt):return True
    if s.get(BACKLOG_INIT_FIELD) and call==verify_backlog_init_recovery(s,s[BACKLOG_INIT_FIELD])['failed_call']:return True
    return notify_prepare_exception(s,call,receipt) if s.get(NOTIFY_RECOVERY_FIELD) else zero_init_exception(root,s,call,receipt)

def replay_calls(root,s,clock):
    """Receipt publication precedes state update; only this known gap recovers.
    An intent without a durable child-exit receipt remains unknown, never rerun.
    """
    unresolved=False;previous_exit=s['start_monotonic']
    for index,call in enumerate(s['calls']):
        need(call['index']==index and call['verb'] in VERBS and call['argv']==argv_for(s['order'],s['archive_root'],call['verb'],s['mode'],call.get('tab_id'),call.get('steps',25)),'daily-parent-command-chain-invalid')
        need(timing.finite(call['launch_monotonic']) and call['launch_monotonic']>=previous_exit,'daily-parent-child-order-invalid')
        launch=timing.pinned(call['launch']);need(launch=={k:v for k,v in call.items() if k not in ('launch','state','result')},'daily-parent-launch-changed')
        result=child_receipt(root,s,call,clock)
        if result is None:need(call['state']=='unknown','daily-parent-exit-receipt-missing');unresolved=True;continue
        ref,receipt=result;call.update(result=ref,state='returned' if receipt['returncode']==0 else 'failed')
        previous_exit=receipt['exited_monotonic']
        if receipt['returncode']!=0:
            if not approved_failed_child(root,s,call,receipt):unresolved=True
        else:receipt_output(receipt,s)
    return unresolved

def started_inner(s,clock):
    root=Path(s['order']['path']).parent.parent/'daily-executions'/Path(s['order']['path']).stem
    inner=timing.load(root/'timing.json',clock)
    need(inner['run_id']=='daily-'+Path(s['order']['path']).stem and inner['work_order']==s['order'] and inner['scope_sha256']==s['scope_sha256'] and inner['origin']==s['origin'] and inner['mode']==s['mode'],'daily-parent-inner-binding-invalid')
    need(inner['start_monotonic']>=s['start_monotonic'] and timing.parse_time(inner['wall_started_at'])>=timing.parse_time(s['wall_started_at']),'daily-parent-inner-predates-launch')
    return root,inner

def verify_complete(s,order,clock):
    """Pure replay of original daily source/outbox and all canonical clients."""
    need(not replay_calls(location(s['order']),s,clock),'daily-parent-unresolved-child')
    root,inner=started_inner(s,clock)
    sys.path.insert(0,str(FORMAL_CLI.parent))
    import daily_timed_run as role
    import notification_backlog as backlog
    _,state=role.checked(root,s['order'],s['archive_root'])
    need(state['phase']=='complete' and inner['status']=='complete' and inner['outcome'] in ('client-confirmed','no-data-complete'),'daily-parent-final-client-proof-required')
    run_dir=Path(state['run_dir']);batch_path=run_dir/'batch_receipt.json';batch=role.check_batch(read(batch_path),order,run_dir)
    need(batch['status']=='complete','daily-parent-business-source-incomplete')
    queues=list((root/'outbox').glob('*/outbox.json'));need(len(queues)==1,'daily-parent-one-original-outbox-required');queue=queues[0];q=backlog.validate_queue(queue)
    need(q['batch']==timing.ref(batch_path) and Path(q['messenger_directory']).resolve()==timing.SENDER_DIRECTORY.resolve(),'daily-parent-source-binding-invalid')
    receipt=timing.pinned(inner['completion'])
    if inner['outcome']=='client-confirmed':
        timing.clients(receipt,inner,clock);need(sorted(inner['delivery']['keys'])==sorted(x['key'] for x in q['items']),'daily-parent-full-key-set-invalid')
        if s['origin']=='fresh':need(inner['delivery'].get('fresh_canonical_absence_checked') is True,'daily-parent-original-send-absence-required')
    else:
        timing.no_data(receipt,inner);need(not q['items'],'daily-parent-zero-has-required-notifications')
    need(s['calls'] and s['calls'][-1]['verb']=='notify' and s['calls'][-1]['state']=='returned','daily-parent-final-notify-exit-required')
    proof={'outcome':inner['outcome'],'inner_timing':timing.ref(root/'timing.json'),'role_state':timing.ref(root/'state.json'),'batch':timing.ref(batch_path),'outbox':timing.ref(queue),'completion':inner['completion'],'all_expected_client_confirmed':inner['outcome']=='client-confirmed'}
    recovery=location(s['order'])/'zero-init-recovery.json'
    if recovery.exists():proof['zero_init_recovery']=timing.ref(recovery)
    if s.get(NOTIFY_RECOVERY_FIELD):
        verify_notify_prepare_recovery(s,s[NOTIFY_RECOVERY_FIELD]);proof[NOTIFY_RECOVERY_FIELD]=s[NOTIFY_RECOVERY_FIELD]
    if s.get(BACKLOG_INIT_FIELD):
        verify_backlog_init_recovery(s,s[BACKLOG_INIT_FIELD]);proof[BACKLOG_INIT_FIELD]=s[BACKLOG_INIT_FIELD]
    if s.get(LOCAL_PROCESSING_FIELD):
        verify_local_processing_recovery(s,s[LOCAL_PROCESSING_FIELD]);proof[LOCAL_PROCESSING_FIELD]=s[LOCAL_PROCESSING_FIELD]
    return proof

def finish_outer(s,order,clock):
    proof=verify_complete(s,order,clock);now=clock.monotonic();root=location(s['order']);path=root/'completion.json'
    last=child_receipt(root,s,s['calls'][-1],clock)[1]
    common={'kind':'daily-parent-completion-v1','run_id':s['run_id'],'order':s['order'],'origin_ref':s['origin_ref'],'completion_proof':proof,'outcome':proof['outcome']}
    if path.exists():
        final=read(path);need(all(final.get(k)==v for k,v in common.items()),'daily-parent-completion-conflict');end=final['end_monotonic']
    else:
        end=now;final={**common,'end_monotonic':end,'wall_ended_at':clock.wall().isoformat(),'acceptance_pass':s['origin']=='fresh' and s['mode']=='acceptance' and proof['all_expected_client_confirmed'] and end-s['start_monotonic']<=timing.LIMIT,'full_workflow_measured':s['origin']=='fresh'}
    need(timing.finite(end) and last['exited_monotonic']<=end<=now,'daily-parent-final-clock-invalid')
    expected=s['origin']=='fresh' and s['mode']=='acceptance' and proof['all_expected_client_confirmed'] and end-s['start_monotonic']<=timing.LIMIT
    need(final['acceptance_pass']==expected and final['full_workflow_measured']==(s['origin']=='fresh'),'daily-parent-final-result-invalid')
    s.update({k:final[k] for k in FINAL_FIELDS});s.update(status='complete',completion_ref=immutable(path,final))

def view(s,clock):
    elapsed=s.get('end_monotonic',clock.monotonic())-s['start_monotonic']
    return {'run_id':s['run_id'],'status':s['status'],'origin':s['origin'],'mode':s['mode'],'elapsed_seconds':elapsed,'deadline_exceeded':elapsed>timing.LIMIT,'acceptance_pass':s.get('acceptance_pass',False),'full_workflow_measured':s.get('full_workflow_measured',False),'outcome':s.get('outcome'),'clock_contract':s['clock_contract'],'start_boundary':'before-first-formal-daily-child-launch','end_boundary':'final-notify-child-exited-and-source-client-replay-complete','inner_timing_is_diagnostic_only':True,'parent_bootstrap_included':False,'final_parent_telemetry_write_included':False,'measurement_only_no_cancel_or_replay':True}

def collection_ready_state(s,order,output):
    """Collection is a durable stopped stage, not delivery/completion."""
    need(order.get('collection_contract')=='three-flow-collection-ready-v1'and output.get('phase')=='collection-ready'and output.get('delivery_complete')is False,'daily-parent-staged-ready-contract')
    import notification_backlog as backlog
    ready_ref=output.get('collection_ready');value=backlog.collection_ready_facts(ready_ref)
    role=location(s['order']).parent.parent/'daily-executions'/Path(s['order']['path']).stem/'state.json';state=timing.pinned(timing.ref(role))
    need(state.get('order')==s['order']and state.get('scope_sha256')==s['scope_sha256']and state.get('phase')=='collection-ready'and state.get('collection_ready')==ready_ref and ready_ref['path']==str(role.parent/'collection-ready.json')and value.get('delivery_complete')is False and value.get('cursor_advanced')is False,'daily-parent-original-ready-source')
    need(not s.get('completion_ref')and not s.get('completion_proof')and not s.get('end_monotonic'),'daily-parent-ready-not-completed')
    s.update(status='collection-ready',collection_ready=ready_ref)
    return s

def execute(order_ref,archive_root,verb,*,mode='development',tab_id=None,steps=25,clock=None,runner=None):
    clock=clock or timing.Clock();entry=(clock.monotonic(),clock.wall(),clock.boot())
    root=location(order_ref);path=root/'state.json';runner=runner or subprocess_child
    with timing.locked(path) as path:
        if path.exists():
            s,order=load(path,order_ref,archive_root,clock)
            need(s['mode']==mode,'daily-parent-mode-conflict')
            unresolved=replay_calls(root,s,clock)
            if s['status']=='complete':
                proof=verify_complete(s,order,clock);need(proof==s['completion_proof'],'daily-parent-completion-changed');return view(s,clock)
            if unresolved:
                s['status']='attention';timing.save(path,s);return view(s,clock)
            if s.get('status')=='collection-ready':
                _,last=child_receipt(root,s,s['calls'][-1],clock);need(last['returncode']==0,'daily-parent-ready-natural-child');collection_ready_state(s,order,receipt_output(last,s));return view(s,clock)
            if s['calls']:started_inner(s,clock)
            if s['calls'] and s['calls'][-1]['verb']=='notify':
                _,last=child_receipt(root,s,s['calls'][-1],clock)
                if last['returncode']==0 and receipt_output(last,s).get('phase')=='complete':
                    finish_outer(s,order,clock);timing.save(path,s);return view(s,clock)
            if verb=='start':return view(s,clock) # Never reset, rescan, or relaunch.
        else:
            need(verb=='start','daily-parent-start-required');order=dispatch.validate(order_ref,archive_root)
            inner=root.parent.parent/'daily-executions'/Path(order_ref['path']).stem
            need(not (inner/'timing.json').exists() and not (inner/'state.json').exists(),'daily-parent-inner-preexists-use-original-launch')
            need(mode in ('development','acceptance') and clock.boot()==entry[2],'daily-parent-mode-or-boot-invalid')
            s={'kind':KIND,'run_id':'daily-parent-'+Path(order_ref['path']).stem,'order':order_ref,'archive_root':str(Path(archive_root).resolve()),'scope_sha256':order['scope_sha256'],'origin':order['origin'],'mode':mode,'clock_contract':timing.MONOTONIC_CLOCK,'boot_identity':entry[2],'start_monotonic':entry[0],'wall_started_at':entry[1].isoformat(),'status':'running','calls':[],'code_refs':code_refs(),'acceptance_pass':False,'full_workflow_measured':False};s['origin_ref']=immutable(root/'origin.json',{k:s[k] for k in ORIGIN_FIELDS});timing.save(path,s)
        argv=argv_for(order_ref,archive_root,verb,mode,tab_id,steps)
        call={'index':len(s['calls']),'verb':verb,'argv':argv,'tab_id':tab_id,'steps':steps,'launch_monotonic':clock.monotonic()};launch=immutable(root/'children'/('%04d-launch.json'%call['index']),call);call.update(launch=launch,state='unknown');s['calls'].append(call);s['status']='running';timing.save(path,s)
        try:
            child=runner(argv);exited=clock.monotonic();need(clock.boot()==s['boot_identity'],'daily-parent-child-boot-changed')
            receipt={'kind':'daily-child-exit-v1','run_id':s['run_id'],'order':order_ref,'launch':launch,'argv':argv,'returncode':child.returncode,'exited_monotonic':exited,'boot_identity':s['boot_identity'],'stdout':child.stdout,'stderr':child.stderr}
            result=immutable(root/'children'/('%04d-result.json'%call['index']),receipt);call.update(result=result,state='returned' if child.returncode==0 else 'failed');timing.save(path,s)
            if child.returncode!=0:s['status']='attention';timing.save(path,s);return view(s,clock)
            output=receipt_output(receipt,s);started_inner(s,clock)
            if output.get('phase')=='collection-ready':collection_ready_state(s,order,output)
            if verb=='notify' and output.get('phase')=='complete':
                finish_outer(s,order,clock)
            timing.save(path,s);value=view(s,clock);value['child_result']=output;return value
        except Exception:
            # No automatic restart even if only stdout parsing was lost. Saved
            # exit receipts permit read-only recovery, not another launch.
            s['status']='attention';timing.save(path,s);raise

def status(order_ref,archive_root,*,clock=None):
    clock=clock or timing.Clock();root=location(order_ref)
    with timing.locked(root/'state.json') as path:
        s,order=load(path,order_ref,archive_root,clock);unresolved=replay_calls(root,s,clock)
        if s['status']=='complete':need(verify_complete(s,order,clock)==s['completion_proof'],'daily-parent-completion-changed')
        if s.get('status')=='collection-ready':
            _,last=child_receipt(root,s,s['calls'][-1],clock);need(last['returncode']==0,'daily-parent-ready-natural-child');collection_ready_state(s,order,receipt_output(last,s))
        # Inspection never promotes an unknown launch without a child receipt
        # to measured completion and never starts a process.
        value=view(s,clock);value['unresolved_child']=unresolved;return value

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('verb',choices=(*VERBS,'status','repair-zero-init'));p.add_argument('--order',required=True);p.add_argument('--order-sha256',required=True);p.add_argument('--archive-root',required=True);p.add_argument('--mode',choices=('development','acceptance'),default='development');p.add_argument('--tab-id',type=int);p.add_argument('--steps',type=int,default=25);p.add_argument('--failure');p.add_argument('--failure-sha256');a=p.parse_args(argv)
    try:
        order={'path':str(Path(a.order).absolute()),'sha256':a.order_sha256}
        if a.verb=='repair-zero-init':
            value=repair_zero_init({'path':str(Path(a.failure).absolute()),'sha256':a.failure_sha256},order_ref=order,archive_root=a.archive_root);print(json.dumps(value,ensure_ascii=False));return 0
        value=status(order,a.archive_root) if a.verb=='status' else execute(order,a.archive_root,a.verb,mode=a.mode,tab_id=a.tab_id,steps=a.steps)
        print(json.dumps(value,ensure_ascii=False));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps({'ok':False,'error':str(e),'acceptance_pass':False},ensure_ascii=False));return 2


# One typed pre-outbox continuation. It grants no sender/dispatch authority.
NOTIFY_RECOVERY_FIELD='notify_preoutbox_recovery'
NOTIFY_RECOVERY_KIND='verified-daily-notify-preoutbox-recovery-v1'
NOTIFY_RECOVERY_ERROR='complete-company-sequence-required'
NOTIFY_RECOVERY_PARENT_SHA='5897bca616116c5e557fc61f40987ec965a117491d700c1b1dd07cb07d0dbe1a'
NOTIFY_RECOVERY_BEFORE={'daily_execution_launcher.py':'94a287637683b13d6ad9548b30532294942e5c3fd0fe14c2bdc34d3e2136731b','notification_backlog.py':'66f64b8f9c1a34124f9b03ad2f5657dd4aae8f303994721ebbe816b3cf4021e1'}

def _notify_targets():return {str(PROJECT/'skills/workshop-director/scripts/daily_execution_launcher.py'):384,str(FORMAL_CLI.with_name('notification_backlog.py')):420}
def _notify_absent(path):
    path=Path(path);need(not path.exists()and not path.is_symlink(),'daily-notify-preinput-output-or-next-child-present')
def _notify_facts(parent_ref,worker_ref,read_ref=timing.pinned,*,live=False):
    materials=[]
    def readpin(r):
        value=read_ref(r);materials.append(r);return value
    s=readpin(parent_ref);root=location(s['order']);need(parent_ref['path']==str(root/'state.json')and s.get('kind')==KIND and s.get('status')=='attention'and len(s.get('calls',[]))==5 and not s.get(NOTIFY_RECOVERY_FIELD)and not s.get('completion_ref'),'daily-notify-original-frontier')
    order=dispatch.validate(s['order'],s['archive_root']);materials.append(s['order']);need(readpin(s['origin_ref'])=={k:s[k]for k in ORIGIN_FIELDS},'daily-notify-original-origin');calls=s['calls'];need([c['verb']for c in calls]==['start','advance','advance','advance','notify']and [c['state']for c in calls]==['returned']*4+['failed'],'daily-notify-exact-five-calls')
    previous=s['start_monotonic']
    for i,c in enumerate(calls):
        need(c['index']==i and c['argv']==argv_for(s['order'],s['archive_root'],c['verb'],s['mode'],c.get('tab_id'),c.get('steps',25))and c['launch']['path']==str(root/'children'/('%04d-launch.json'%i))and c['result']['path']==str(root/'children'/('%04d-result.json'%i)),'daily-notify-original-call-path-argv');launch=readpin(c['launch']);ex=readpin(c['result']);need(launch=={k:v for k,v in c.items()if k not in ('launch','state','result')}and ex.get('kind')=='daily-child-exit-v1'and ex['launch']==c['launch']and ex['argv']==c['argv']and ex['order']==s['order']and ex['run_id']==s['run_id']and ex['boot_identity']==s['boot_identity']and timing.finite(c['launch_monotonic'])and timing.finite(ex['exited_monotonic'])and previous<=c['launch_monotonic']<=ex['exited_monotonic'],'daily-notify-natural-call-chain');previous=ex['exited_monotonic']
        if i<4:need(ex['returncode']==0,'daily-notify-prefix-nonzero');receipt_output(ex,s)
        else:need(type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':NOTIFY_RECOVERY_ERROR,'acceptance_pass':False},'daily-notify-exact-preoutbox-error')
    worker=readpin(worker_ref);request=readpin(worker['request']);response=readpin(worker['response']);need(worker.get('kind')=='workshop-worker-exit-v1'and type(worker['returncode'])is int and worker['returncode']==0 and request['attempt_id']==worker['attempt_id']and request['task']['flow']=='daily-comment-stats'and request['task']['day']==order['day']and request['context']['order']==s['order']and response['task_id']==request['task']['id']and response['attempt_id']==request['attempt_id']and response['outcome']=='failed','daily-notify-natural-worker-same-task')
    inner_root=Path(s['order']['path']).parent.parent/'daily-executions'/Path(s['order']['path']).stem;role_ref=timing.ref(inner_root/'state.json')if live else next(r for r in _NOTIFY_ARCHIVE_INPUTS.get(())if r['path']==str(inner_root/'state.json'));timing_ref=timing.ref(inner_root/'timing.json')if live else next(r for r in _NOTIFY_ARCHIVE_INPUTS.get(())if r['path']==str(inner_root/'timing.json'));role=readpin(role_ref);ts=readpin(timing_ref)
    need(role.get('kind')=='daily-timed-role-v1'and role.get('order')==s['order']and role.get('scope_sha256')==s['scope_sha256']and role.get('phase')=='notification-ready'and role.get('outbox')==str(inner_root/'outbox')and ts.get('status')=='running'and ts.get('work_order')==s['order']and ts.get('scope_sha256')==s['scope_sha256']and ts.get('delivery')=={'status':'unsealed','contract':'seal-once-before-first-sender-prepare-v1'}and not ts.get('completion'),'daily-notify-complete-acquisition-unsealed')
    batch_path=Path(role['run_dir'])/'batch_receipt.json';batch_ref=timing.ref(batch_path)if live else next(r for r in _NOTIFY_ARCHIVE_INPUTS.get(())if r['path']==str(batch_path));batch=readpin(batch_ref);need(batch.get('status')=='complete'and batch.get('failed',0)==batch.get('needs_review',0)==0 and batch.get('dispatch_scope')=={'work_order':s['order'],'scope_sha256':s['scope_sha256'],'active_company_policy':order.get('active_company_policy')}and len(batch['companies'])==1 and batch['companies'][0]['status']=='complete','daily-notify-original-single-complete-batch')
    company=batch['companies'][0];issued=order['scope']['company_ranges'];need(len(issued)==1 and company['company']==issued[0]['company']and str(company['groupid'])==issued[0]['groupid']and company['date_range']['start']==issued[0]['start']and company['date_range']['end_exclusive']==order['day'],'daily-notify-original-company-dates')
    sys.path.insert(0,str(FORMAL_CLI.parent))
    import ds_common
    mapping=next(r for r in ds_common.load_map()if r['company']==company['company']);receipt_ref=timing.ref(company['receipt'])if live else next(r for r in _NOTIFY_ARCHIVE_INPUTS.get(())if r['path']==company['receipt']);receipt=readpin(receipt_ref);need(receipt.get('status')=='complete'and receipt.get('attribution_verified')is True and receipt.get('mismatch')is False and not receipt.get('warnings')and receipt.get('row_count')==receipt.get('page_filtered')and ds_common.receipt_valid(receipt,receipt['src_file'],mapping,company['date_range'],batch['mapping_sha256']),'daily-notify-original-receipt-valid')
    for r in [dict(path=receipt['src_file'],sha256=receipt['src_sha256']),*[{k:a[k]for k in ('path','sha256')}for a in receipt['artifacts']]]:timing.checked_bytes(r);materials.append(r)
    if live:
        for p in [inner_root/'outbox',inner_root/'delivery-manifest.json',inner_root/'client-confirmation.json',inner_root/'no-data-confirmation.json',root/'children/0005-launch.json',root/'children/0005-result.json']:_notify_absent(p)
    return {'original_parent':parent_ref,'worker':worker_ref,'order':s['order'],'original_calls':calls,'failed_index':4,'failed_call':calls[4],'inner':role_ref,'timing':timing_ref,'batch':batch_ref,'worker_task_id':request['task']['id'],'worker_attempt_id':request['attempt_id'],'outer':request['task']['outer'],'materials':list({(r['path'],r['sha256']):r for r in materials}.values())}

from contextvars import ContextVar as _NotifyContextVar
_NOTIFY_ARCHIVE_INPUTS=_NotifyContextVar('notify_preoutbox_archive_inputs',default=())
def _notify_release(s,release_ref,original_parent_ref,*,historical=False):
    need(original_parent_ref['sha256']==NOTIFY_RECOVERY_PARENT_SHA,'daily-notify-reviewed-original-parent')
    release=timing.pinned(release_ref);targets=release.get('targets');wanted=_notify_targets();need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and type(targets)is list and len(targets)==2 and {t['target']for t in targets}==set(wanted)and not release.get('data_targets'),'daily-notify-reviewed-two-source-release');need(release.get('notify_preoutbox_recovery')=={'kind':NOTIFY_RECOVERY_KIND,'original_parent_sha256':original_parent_ref['sha256'],'order':s['order']},'daily-notify-release-original-binding')
    need(len(s['code_refs'])==len({r['path']for r in s['code_refs']})==6,'daily-notify-original-six-slots');refs=[]
    for r in s['code_refs']:
        if r['path']not in wanted:
            if historical:historical_code_bytes(r,sealed=True)
            else:timing.checked_bytes(r)
            refs.append({'original':r,'material':r});continue
        target=next(t for t in targets if t['target']==r['path']);name=Path(r['path']).name;need(set(target)=={'target','before','after','old_sha256','mode'}and type(target['mode'])is int and target['mode']==wanted[r['path']]and r['sha256']==target['old_sha256']==target['before']['sha256']==NOTIFY_RECOVERY_BEFORE[name]and target['before']['path']==str(Path(release_ref['path']).parent/(name+'.before'))and target['after']['sha256']!=r['sha256'],'daily-notify-exact-source-slot');timing.checked_bytes(target['before']);timing.checked_bytes(target['after']);canonical={'path':r['path'],'sha256':target['after']['sha256']};
        if not historical:timing.checked_bytes(canonical);need(Path(r['path']).stat().st_mode&0o777==target['mode'],'daily-notify-source-mode')
        archive={'path':str(PROJECT/'skills/workshop-director/references/daily-source-archives'/(r['sha256']+'.py')),'sha256':r['sha256']};timing.checked_bytes(archive);refs.append({'original':r,'material':archive})
    return refs

def plan_notify_prepare_recovery(parent_ref,worker_ref,release_ref):
    facts=_notify_facts(parent_ref,worker_ref,live=True);s=timing.pinned(parent_ref);_notify_release(s,release_ref,parent_ref);return {'kind':NOTIFY_RECOVERY_KIND,'facts':facts,'release':release_ref,'original_clock_preserved':True,'business_actions_performed':False}
def notify_recovery_shared_transform(original,proof_ref):
    need(NOTIFY_RECOVERY_FIELD not in original,'daily-notify-marker-already-present');import copy
    result=copy.deepcopy(original);result[NOTIFY_RECOVERY_FIELD]=proof_ref;return result

def verify_notify_prepare_recovery(current,proof_ref):
    proof=timing.pinned(proof_ref);need(set(proof)=={'kind','facts','release','original_clock_preserved','business_actions_performed','archives'}and proof['kind']==NOTIFY_RECOVERY_KIND and proof['original_clock_preserved']is True and proof['business_actions_performed']is False,'daily-notify-proof-schema');facts=proof['facts'];base=location(facts['order'])/'.notify-preoutbox-recovery'/facts['original_parent']['sha256'];need(proof_ref['path']==str(base/'proof.json'),'daily-notify-canonical-proof');mapping={}
    for p in proof['archives']:
        r,a=p['original'],p['archive'];need(set(p)=={'original','archive'}and a=={'path':str(base/'materials'/(r['sha256']+'.data')),'sha256':r['sha256']},'daily-notify-exact-proof-archive');timing.checked_bytes(a);need((r['path'],r['sha256'])not in mapping,'daily-notify-duplicate-archive');mapping[r['path'],r['sha256']]=a
    def archived(r):need((r['path'],r['sha256'])in mapping,'daily-notify-missing-archive');return timing.pinned(mapping[r['path'],r['sha256']])
    token=_NOTIFY_ARCHIVE_INPUTS.set(facts['materials'])
    try:need(_notify_facts(facts['original_parent'],facts['worker'],archived,live=False)==facts,'daily-notify-recomputed-facts')
    finally:_NOTIFY_ARCHIVE_INPUTS.reset(token)
    before=archived(facts['original_parent']);historical=current.get('status')=='complete'
    if historical:completed_source_seal(current,location(current['order']));need(current.get('completion_proof',{}).get(NOTIFY_RECOVERY_FIELD)==proof_ref,'daily-notify-completed-proof-seal')
    need(current.get(NOTIFY_RECOVERY_FIELD)==proof_ref and all(current.get(k)==before[k]for k in ORIGIN_FIELDS)and current['origin_ref']==before['origin_ref']and current['calls'][:5]==before['calls'],'daily-notify-preserved-origin-failed-prefix');refs=_notify_release(before,proof['release'],facts['original_parent'],historical=historical);return {'proof':proof_ref,'facts':facts,'verification_refs':refs,'failed_index':4,'failed_call':before['calls'][4]}
def notify_prepare_exception(s,call,receipt):
    admitted=verify_notify_prepare_recovery(s,s[NOTIFY_RECOVERY_FIELD]);return call==admitted['failed_call']and call['index']==admitted['failed_index']and receipt['returncode']==2 and json.loads(receipt['stdout'])=={'ok':False,'error':NOTIFY_RECOVERY_ERROR,'acceptance_pass':False}

def _notify_live_frontier(facts):
    # Recheck current bytes/inventory before CAS, not the full archived history.
    for r in facts['materials']:timing.checked_bytes(r)
    root=location(facts['order']);inner=Path(facts['inner']['path']).parent
    for p in [inner/'outbox',inner/'delivery-manifest.json',inner/'client-confirmation.json',inner/'no-data-confirmation.json',root/'children/0005-launch.json',root/'children/0005-result.json']:_notify_absent(p)

def recover_notify_prepare_recovery(parent_ref,worker_ref,release_ref,*,guard=None,checkpoint=lambda stage:None):
    need(callable(guard),'daily-notify-caller-locked-guard-required');guard('preflight');root=Path(parent_ref['path']).parent;path=root/'state.json';need(parent_ref['path']==str(path),'daily-notify-parent-path');base=root/'.notify-preoutbox-recovery'/parent_ref['sha256'];proof_path=base/'proof.json';intent_path=base/'intent.json';intent={'kind':NOTIFY_RECOVERY_KIND,'parent':parent_ref,'worker':worker_ref,'release':release_ref}
    with timing.locked(path):
        if intent_path.exists()or intent_path.is_symlink():need(timing.pinned(timing.ref(intent_path))==intent,'daily-notify-foreign-intent')
        if proof_path.exists():
            pr=timing.ref(proof_path);proof=timing.pinned(pr);need(proof['facts']['original_parent']==parent_ref and proof['facts']['worker']==worker_ref and proof['release']==release_ref and intent_path.is_file(),'daily-notify-same-proof-inputs');pair=next(p for p in proof['archives']if p['original']==parent_ref);before=timing.pinned(pair['archive']);after=notify_recovery_shared_transform(before,pr);cur=read(path);need(cur in (before,after),'daily-notify-third-state');verify_notify_prepare_recovery(after,pr)
            if cur==after:return pr
        else:
            need(timing.ref(path)==parent_ref,'daily-notify-parent-CAS');plan=plan_notify_prepare_recovery(parent_ref,worker_ref,release_ref);immutable(intent_path,intent);archives=[]
            for r in plan['facts']['materials']:archives.append({'original':r,'archive':immutable_raw(base/'materials'/(r['sha256']+'.data'),timing.checked_bytes(r))})
            pr=immutable(proof_path,{**plan,'archives':archives});before=timing.pinned(parent_ref);after=notify_recovery_shared_transform(before,pr);verify_notify_prepare_recovery(after,pr);checkpoint('proof')
        guard('before-CAS');need(timing.ref(path)==parent_ref,'daily-notify-parent-drift');_notify_live_frontier(timing.pinned(pr)['facts']);timing.save(path,after);checkpoint('parent');guard('readback');verify_notify_prepare_recovery(read(path),pr);return pr

# Explicit command-local facts reuse. No cache survives a command or state change.
_NOTIFY_COMMAND_FACTS=_NotifyContextVar('daily_notify_command_facts',default=None)
_NOTIFY_VERIFY_UNCACHED=verify_notify_prepare_recovery

def verify_notify_prepare_recovery(current,proof_ref):
    facts=_NOTIFY_COMMAND_FACTS.get()
    if facts is None:return _NOTIFY_VERIFY_UNCACHED(current,proof_ref)
    key=json.dumps([current,proof_ref],ensure_ascii=False,sort_keys=True,separators=(',',':'))
    if key not in facts:facts[key]=_NOTIFY_VERIFY_UNCACHED(current,proof_ref)
    return facts[key]

import contextlib as _notify_contextlib
@_notify_contextlib.contextmanager
def notify_recovery_command_scope():
    if _NOTIFY_COMMAND_FACTS.get()is not None:
        yield
        return
    token=_NOTIFY_COMMAND_FACTS.set({})
    try:yield
    finally:_NOTIFY_COMMAND_FACTS.reset(token)

_NOTIFY_RECOVER=recover_notify_prepare_recovery
def recover_notify_prepare_recovery(*args,**kwargs):
    with notify_recovery_command_scope():return _NOTIFY_RECOVER(*args,**kwargs)

_NOTIFY_EXECUTE=execute
_NOTIFY_STATUS=status

def execute(*args,**kwargs):
    token=_NOTIFY_COMMAND_FACTS.set({})
    try:
        import execution_timing as timing
        with timing.company_policy_command():return _NOTIFY_EXECUTE(*args,**kwargs)
    finally:_NOTIFY_COMMAND_FACTS.reset(token)

def status(*args,**kwargs):
    token=_NOTIFY_COMMAND_FACTS.set({})
    try:
        with timing.company_policy_command():return _NOTIFY_STATUS(*args,**kwargs)
    finally:_NOTIFY_COMMAND_FACTS.reset(token)

# Original failed initialization only; no sender, business input or retry authority.
BACKLOG_INIT_FIELD='legacy_zero_backlog_init_recovery'
BACKLOG_INIT_KIND='verified-daily-legacy-zero-backlog-init-recovery-v1'
BACKLOG_INIT_PARENT='0689da48cb6a73eb6fd8579f760e28032659b2297305640e999856c76e60fed7'
BACKLOG_INIT_BEFORE={'daily_execution_launcher.py':'36c5c48c63025a177b42fc5ee68f8085c75c7903b4dfa827900b00b188ad5869','notification_backlog.py':'7c432dcb46a443d8d19ea24596cc2c5fa256439cc572511b4562e236bd5580eb'}
BACKLOG_INIT_ERROR="daily-timing-formal-cli-stopped:{'code': 'notification-backlog-pending', 'message': 'Finish original notification jobs before creating another daily run'}"

def _backlog_init_facts(parent_ref,worker_ref,inner_ref,timing_ref,reader=timing.pinned):
    s=reader(parent_ref);root=location(s['order']);need(parent_ref['sha256']==BACKLOG_INIT_PARENT and parent_ref['path']==str(root/'state.json')and s['status']=='attention'and len(s['calls'])==1 and not s.get('completion_ref')and not s.get(BACKLOG_INIT_FIELD),'daily-backlog-init-original-frontier')
    need(reader(s['origin_ref'])=={k:s[k]for k in ORIGIN_FIELDS},'daily-backlog-init-origin');c=s['calls'][0];ex=reader(c['result'])
    need(c['index']==0 and c['verb']=='start'and c['state']=='failed'and c['argv']==argv_for(s['order'],s['archive_root'],'start',s['mode'],None,25)and c['launch']['path']==str(root/'children/0000-launch.json')and c['result']['path']==str(root/'children/0000-result.json'),'daily-backlog-init-call')
    need(reader(c['launch'])=={k:v for k,v in c.items()if k not in('launch','state','result')}and ex['kind']=='daily-child-exit-v1'and ex['launch']==c['launch']and ex['argv']==c['argv']and ex['order']==s['order']and ex['run_id']==s['run_id']and ex['boot_identity']==s['boot_identity']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':BACKLOG_INIT_ERROR,'acceptance_pass':False}and s['start_monotonic']<=c['launch_monotonic']<=ex['exited_monotonic'],'daily-backlog-init-natural-known-exit')
    w=reader(worker_ref);rq=reader(w['request']);rs=reader(w['response']);need(w['kind']=='workshop-worker-exit-v1'and w['returncode']==0 and w['attempt_id']==rq['attempt_id']==rs['attempt_id']and rq['task']['id']==rs['task_id']and rq['task']['flow']=='daily-comment-stats'and rq['context']=={}and rs['context']['order']==s['order']and rs['outcome']=='failed','daily-backlog-init-original-worker')
    checkpoint_ref=timing.ref(Path(worker_ref['path']).parent/'adapter-context.json');need(rs['context']['stage']=='advance'and reader(checkpoint_ref)=={**rs['context'],'stage':'start'},'daily-backlog-init-response-checkpoint')
    inner=Path(s['archive_root'])/'daily-executions'/Path(s['order']['path']).stem
    need(inner_ref['path']==str(inner/'state.json')and timing_ref['path']==str(inner/'timing.json'),'daily-backlog-init-inner-path');role=reader(inner_ref);ts=reader(timing_ref)
    need(role['kind']=='daily-timed-role-v1'and role['phase']=='init-intent'and role['order']==s['order']and role['scope_sha256']==s['scope_sha256']and ts['status']=='running'and ts['work_order']==s['order']and ts['scope_sha256']==s['scope_sha256']and ts['events']==[]and ts['stages']==[]and not ts.get('completion'),'daily-backlog-init-no-business')
    return {'parent':parent_ref,'worker':worker_ref,'inner':inner_ref,'timing':timing_ref,'order':s['order'],'task':rq['task']['id'],'attempt':rq['attempt_id'],'outer':rq['task']['outer'],'failed_call':c}

def _backlog_init_live(facts):
    s=timing.pinned(facts['parent']);role=timing.pinned(facts['inner']);timing.pinned(facts['timing']);root=location(s['order']);inner=Path(facts['inner']['path']).parent
    for path in (root/'children/0001-launch.json',root/'children/0001-result.json',Path(role['run_dir']),inner/'outbox',inner/'delivery-manifest.json',inner/'client-confirmation.json',inner/'no-data-confirmation.json'):
        need(not path.exists()and not path.is_symlink(),'daily-backlog-init-business-output-present')

def _backlog_init_sources(before,release_ref,disposition,*,historical=False):
    release=timing.pinned(release_ref);targets=release.get('targets');wanted={str(PROJECT/'skills/workshop-director/scripts/daily_execution_launcher.py'):384,str(FORMAL_CLI.with_name('notification_backlog.py')):420}
    need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and type(targets)is list and len(targets)==2 and {t['target']for t in targets}==set(wanted),'daily-backlog-init-source-release')
    need(release.get(BACKLOG_INIT_FIELD)=={'kind':BACKLOG_INIT_KIND,'original_parent_sha256':BACKLOG_INIT_PARENT,'order':before['order'],'disposition':disposition},'daily-backlog-init-reviewed-binding')
    need(len(before['code_refs'])==6 and {r['path']for r in before['code_refs']}=={r['path']for r in code_refs()},'daily-backlog-init-six-slots');refs=[]
    for r in before['code_refs']:
        if r['path']not in wanted:
            if historical:historical_code_bytes(r,sealed=True);material=r
            elif r['path']in {str(PROJECT/'skills/workshop-director/scripts/execution_timing.py'),*[str(FORMAL_CLI.with_name(n))for n in('flow.py','daily_timed_run.py')]}:material=timing.configuration_source_material(r)['material']
            else:timing.checked_bytes(r);material=r
            refs.append({'original':r,'material':material});continue
        t=next(t for t in targets if t['target']==r['path']);need(set(t)=={'target','before','after','old_sha256','mode'}and type(t['mode'])is int and t['mode']==wanted[r['path']]and t['old_sha256']==r['sha256']==t['before']['sha256']==BACKLOG_INIT_BEFORE[Path(r['path']).name]and t['after']['sha256']!=r['sha256']and t['before']['path']==str(Path(release_ref['path']).parent/(Path(r['path']).name+'.before')),'daily-backlog-init-two-source-slot');timing.checked_bytes(t['before']);timing.checked_bytes(t['after'])
        if not historical:
            current={'path':r['path'],'sha256':t['after']['sha256']}
            timing.configuration_source_material(current)
            need(Path(r['path']).stat().st_mode&0o777==t['mode'],'daily-backlog-init-source-mode')
        archive={'path':str(PROJECT/'skills/workshop-director/references/daily-source-archives'/(r['sha256']+'.py')),'sha256':r['sha256']};timing.checked_bytes(archive);refs.append({'original':r,'material':archive})
    return refs

def plan_backlog_init_recovery(parent_ref,worker_ref,outbox_path,release_ref):
    before=timing.pinned(parent_ref);inner=Path(before['archive_root'])/'daily-executions'/Path(before['order']['path']).stem;materials=[]
    def record(r):materials.append(r);return timing.pinned(r)
    facts=_backlog_init_facts(parent_ref,worker_ref,timing.ref(inner/'state.json'),timing.ref(inner/'timing.json'),record);_backlog_init_live(facts)
    dispatch.validate(before['order'],before['archive_root']);sys.path.insert(0,str(FORMAL_CLI.parent));import notification_backlog as backlog
    disposition=backlog.legacy_zero_outbox_disposition(outbox_path);need(disposition is not None,'daily-backlog-init-original-completion-not-qualified');_backlog_init_sources(before,release_ref,disposition)
    return {'kind':BACKLOG_INIT_KIND,'facts':facts,'materials':materials,'release':release_ref,'disposition':disposition,'business_actions_performed':False,'original_clock_preserved':True}

def backlog_init_shared_transform(before,proof_ref):
    need(BACKLOG_INIT_FIELD not in before,'daily-backlog-init-existing-marker');import copy
    after=copy.deepcopy(before);after[BACKLOG_INIT_FIELD]=proof_ref;return after

def verify_backlog_init_recovery(current,proof_ref):
    proof=timing.pinned(proof_ref);need(set(proof)=={'kind','facts','materials','release','disposition','business_actions_performed','original_clock_preserved','archives'}and proof['kind']==BACKLOG_INIT_KIND and proof['business_actions_performed']is False and proof['original_clock_preserved']is True,'daily-backlog-init-proof-schema');facts=proof['facts'];base=location(facts['order'])/'.legacy-zero-backlog-init'/facts['parent']['sha256'];need(proof_ref['path']==str(base/'proof.json'),'daily-backlog-init-proof-path');mapping={}
    for pair in proof['archives']:
        r,a=pair['original'],pair['archive'];need(set(pair)=={'original','archive'}and a=={'path':str(base/'materials'/(r['sha256']+'.data')),'sha256':r['sha256']}and (r['path'],r['sha256'])not in mapping,'daily-backlog-init-archive');timing.checked_bytes(a);mapping[r['path'],r['sha256']]=a
    def archived(r):need((r['path'],r['sha256'])in mapping,'daily-backlog-init-missing-archive');return timing.pinned(mapping[r['path'],r['sha256']])
    need(_backlog_init_facts(facts['parent'],facts['worker'],facts['inner'],facts['timing'],archived)==facts,'daily-backlog-init-recomputed-facts');before=archived(facts['parent'])
    need(current.get(BACKLOG_INIT_FIELD)==proof_ref and all(current.get(k)==before[k]for k in ORIGIN_FIELDS)and current['origin_ref']==before['origin_ref']and current['calls'][:1]==before['calls'],'daily-backlog-init-prefix-preserved')
    historical=current['status']=='complete'
    if historical:completed_source_seal(current,location(current['order']));need(current['completion_proof'].get(BACKLOG_INIT_FIELD)==proof_ref,'daily-backlog-init-completion-seal')
    return {'facts':facts,'verification_refs':_backlog_init_sources(before,proof['release'],proof['disposition'],historical=historical),'failed_call':before['calls'][0]}

def recover_backlog_init_recovery(parent_ref,worker_ref,outbox_path,release_ref,*,guard,checkpoint=lambda stage:None):
    path=Path(parent_ref['path']);root=path.parent;need(path.name=='state.json'and path==path.resolve()and not any(p.is_symlink()for p in(path,*path.parents))and root==location(read(path)['order']),'daily-backlog-init-canonical-parent');base=root/'.legacy-zero-backlog-init'/parent_ref['sha256'];proof_path=base/'proof.json';intent=base/'intent.json'
    with timing.locked(path),notify_recovery_command_scope():
        binding={'kind':BACKLOG_INIT_KIND,'parent':parent_ref,'worker':worker_ref,'outbox':str(outbox_path),'release':release_ref}
        if proof_path.exists():
            pr=timing.ref(proof_path);proof=timing.pinned(pr);need(read(intent)==binding and proof['facts']['parent']==parent_ref and proof['facts']['worker']==worker_ref and proof['release']==release_ref,'daily-backlog-init-same-intent');before=timing.pinned(next(p['archive']for p in proof['archives']if p['original']==parent_ref));after=backlog_init_shared_transform(before,pr);need(read(path)in(before,after),'daily-backlog-init-third-state');verify_backlog_init_recovery(after,pr)
            if read(path)==after:guard('existing-readback');return pr
        else:
            guard('preflight');plan=plan_backlog_init_recovery(parent_ref,worker_ref,outbox_path,release_ref);immutable(intent,binding);archives=[]
            for r in plan['materials']:archives.append({'original':r,'archive':immutable_raw(base/'materials'/(r['sha256']+'.data'),timing.checked_bytes(r))})
            pr=immutable(proof_path,{**plan,'archives':archives});before=timing.pinned(parent_ref);after=backlog_init_shared_transform(before,pr);verify_backlog_init_recovery(after,pr);checkpoint('proof')
        guard('before-CAS');_backlog_init_live(timing.pinned(pr)['facts']);timing.save(path,after);checkpoint('parent');guard('readback');verify_backlog_init_recovery(read(path),pr);return pr

_BACKLOG_INIT_VERIFY_UNCACHED=verify_backlog_init_recovery
def verify_backlog_init_recovery(current,proof_ref):
    scope=_NOTIFY_COMMAND_FACTS.get()
    key='backlog-init:'+json.dumps([current,proof_ref],ensure_ascii=False,sort_keys=True,separators=(',',':'))
    if scope is None:return _BACKLOG_INIT_VERIFY_UNCACHED(current,proof_ref)
    if key not in scope:scope[key]=_BACKLOG_INIT_VERIFY_UNCACHED(current,proof_ref)
    else:
        # Reuse parsed facts only; every actual archive/source dependency hashes
        # again on each lookup, including current four unmodified source slots.
        proof=timing.pinned(proof_ref)
        for pair in proof['archives']:timing.checked_bytes(pair['archive'])
        before=timing.pinned(next(p['archive']for p in proof['archives']if p['original']==proof['facts']['parent']))
        scope[key]['verification_refs']=_backlog_init_sources(before,proof['release'],proof['disposition'],historical=current['status']=='complete')
    return scope[key]


# A natural local processing failure is not an unknown browser outcome. Only
# this exact archived failure + an independently returned public repair may
# authorize later original advances; failed calls and origin remain unchanged.
LOCAL_PROCESSING_FIELD='known_local_processing_recovery'
LOCAL_PROCESSING_KIND='verified-local-export-processing-recovery-v1'
LOCAL_PROCESSING_ERROR="daily-timing-formal-cli-stopped:{'code': 'reservation-receipt-not-ready', 'message': 'reservation-receipt-not-ready'}"

def _local_processing_facts(parent_ref,worker_ref,raw=timing.checked_bytes,refs=None):
    materials=[]
    def take(r):
        if r not in materials:materials.append(r)
        return raw(r)
    def doc(r):return json.loads(take(r))
    def at(p):
        if refs is None:return timing.ref(p)
        matches=[r for r in refs if r['path']==str(p)];need(len(matches)==1,'daily-local-material-path');return matches[0]
    s=doc(parent_ref);root=location(s['order']);need(parent_ref['path']==str(root/'state.json')and s['status']=='attention'and not s.get(LOCAL_PROCESSING_FIELD)and not s.get('completion_ref')and len(s['calls'])>=2,'daily-local-original-parent')
    need(doc(s['origin_ref'])=={k:s[k]for k in ORIGIN_FIELDS},'daily-local-origin')
    call=s['calls'][-1];need(call['verb']=='advance'and call['state']=='failed'and call['index']==len(s['calls'])-1 and call['argv']==argv_for(s['order'],s['archive_root'],'advance',s['mode'],call['tab_id'],call['steps']),'daily-local-failed-advance')
    need(call['launch']['path']==str(root/'children'/('%04d-launch.json'%call['index']))and call['result']['path']==str(root/'children'/('%04d-result.json'%call['index']))and doc(call['launch'])=={k:v for k,v in call.items()if k not in('launch','state','result')},'daily-local-call-chain')
    ex=doc(call['result']);need(ex['kind']=='daily-child-exit-v1'and ex['launch']==call['launch']and ex['argv']==call['argv']and ex['order']==s['order']and ex['run_id']==s['run_id']and ex['boot_identity']==s['boot_identity']and type(ex['returncode'])is int and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':LOCAL_PROCESSING_ERROR,'acceptance_pass':False}and s['start_monotonic']<=call['launch_monotonic']<=ex['exited_monotonic'],'daily-local-exact-exit')
    need(all(c['state']=='returned' or c['index']==0 and c['state']=='failed'and s.get(BACKLOG_INIT_FIELD)for c in s['calls'][:-1]),'daily-local-other-failure-or-unknown')
    w=doc(worker_ref);rq=doc(w['request']);response=doc(w['response']);attempt=Path(worker_ref['path']).parent
    need(worker_ref['path']==str(attempt/'exit.json')and rq['attempt_id']==w['attempt_id']==response['attempt_id']==attempt.name and rq['task']['id']==response['task_id']and rq['task']['flow']=='daily-comment-stats'and w['kind']=='workshop-worker-exit-v1'and w['returncode']==0 and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and rq['context']['stage']==response['context']['stage']=='advance'and rq['context']['order']==response['context']['order']==s['order'],'daily-local-original-worker')
    px=doc(at(attempt/'parent-advance-exit.json'))
    offer=doc(rq['context']['offer']);need(px['returncode']==0 and px['argv']==offer['daily_execution']['commands']['advance']+['--tab-id',str(rq['context']['scope']['tab_id'])]and take(px['stderr'])==b''and json.loads(take(px['stdout']))['status']=='attention','daily-local-parent-returned')
    inner=root.parent.parent/'daily-executions'/Path(s['order']['path']).stem;role_ref=at(inner/'state.json');role=doc(role_ref);need(role['order']==s['order']and role['phase']=='acquisition','daily-local-inner-scope')
    batch_ref=at(Path(role['run_dir'])/'batch_receipt.json');batch=doc(batch_ref);need(batch['status']=='running'and batch['dispatch_scope']['work_order']==s['order']and batch['dispatch_scope']['active_company_policy']==doc(s['order'])['active_company_policy']and batch['delivery_contract']=='three-flow-collection-ready-v1','daily-local-batch-scope')
    failed=[r for r in batch['companies']if r['status']=='failed'];need(len(failed)==1,'daily-local-unique-failed-row');row=failed[0];receipt_ref=at(Path(row['receipt']));receipt=doc(receipt_ref)
    need(receipt['company']==row['company']and receipt['status']=='failed'and receipt['error']=={'code':'source-company-mismatch','message':'Acquisition groupid does not match target company','fatal':True}and not receipt['artifacts']and receipt['src_file']==row['source']and receipt['date_range']=={k:row['date_range'][k]for k in('start','end')},'daily-local-original-processing-failure')
    evidence_ref=at(Path(row['evidence']));evidence=doc(evidence_ref);source_ref={'path':row['source'],'sha256':receipt['src_sha256']};take(source_ref)
    job_refs=[c for c in s['calls']if c['state']=='returned'];need(job_refs,'daily-local-prior-returned-parent')
    wf_ref=at(Path(row['outdir'])/'operator'/evidence['work_order_id'][:16]/'workflow.json');wf=doc(wf_ref);need(wf['state']=='complete'and wf['phase']=='done'and wf['company']==row['company']and str(wf['groupid'])==str(row['groupid'])and all(c['state']=='confirmed'for c in wf['calls'])and wf['work_order_id']==evidence['work_order_id']and evidence['workflow_sha256']==wf_ref['sha256']and all(evidence.get(k)==v for k,v in wf['result'].items()if k!='source')and wf['result']['src_sha256']==source_ref['sha256']and wf['result']['source']==wf['result']['download_receipt']['path'],'daily-local-original-completed-acquisition')
    # Fixed cold public provider import closure; source release is checked
    # before this helper runs, never execute an archived processor module.
    for directory in (FORMAL_CLI.parent,PROJECT/'skills/douyin-laike-operator/scripts'):
        need(directory.resolve()==directory and not any(p.is_symlink()for p in(directory,*directory.parents)),'daily-local-fixed-import-origin');sys.path.insert(0,str(directory))
    import ds_processor
    need(Path(ds_processor.__file__).absolute()==FORMAL_CLI.with_name('ds_processor.py'),'daily-local-processor-module-origin')
    need(ds_processor.acquisition_check(evidence,row,Path(row['source']),row['date_range'],company_policy=batch['dispatch_scope']['active_company_policy'])is True,'daily-local-configured-source')
    return {'parent':parent_ref,'worker':worker_ref,'order':s['order'],'outer':rq['task']['outer'],'task_id':rq['task']['id'],'failed_call':call,'batch':batch_ref,'company':row['company'],'receipt':receipt_ref,'evidence':evidence_ref,'source':source_ref,'workflow':wf_ref,'role':role_ref,'materials':materials}

def _local_processing_release(release_ref):
    release=timing.pinned(release_ref);wanted={str(Path(__file__).absolute()):384,str(FORMAL_CLI.with_name('flow.py')):420,str(FORMAL_CLI.with_name('ds_processor.py')):420};targets=release.get('targets')
    need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and type(targets)is list and len(targets)==3 and {t['target']for t in targets}==set(wanted),'daily-local-three-source-release')
    for t in targets:
        need(set(t)=={'target','before','after','old_sha256','mode'}and t['old_sha256']==t['before']['sha256']and t['before']['path']==str(Path(release_ref['path']).parent/(Path(t['target']).name+'.before'))and t['mode']==wanted[t['target']],'daily-local-source-target')
        timing.checked_bytes(t['before']);timing.checked_bytes(t['after'])
        canonical={'path':t['target'],'sha256':t['after']['sha256']}
        if Path(t['target']).name in ('flow.py','daily_execution_launcher.py'):
            material=timing.configuration_source_material(canonical);timing.checked_bytes(material['material'])
        else:timing.checked_bytes(canonical)
        need(Path(t['target']).stat().st_mode&0o777==t['mode'],'daily-local-source-mode')
    return release

def prepare_local_processing_recovery(parent_ref,worker_ref,release_ref,*,guard):
    """Archive the exact failed frontier BEFORE the official flow repair CLI.
    Caller holds scheduler/resource/coordinator locks; this API owns parentlock.
    An existing prepare is observe-only; no repair subprocess is launched here.
    """
    path=Path(parent_ref['path']);base=path.parent/'.local-processing-recovery'/parent_ref['sha256'];intent=base/'intent.json'
    with timing.locked(path),notify_recovery_command_scope():
        if intent.exists():
            value=timing.pinned(timing.ref(intent));need(value['parent']==parent_ref and value['worker']==worker_ref and value['release']==release_ref,'daily-local-prepare-drift');return timing.ref(intent)
        guard('prepare');need(timing.ref(path)==parent_ref,'daily-local-prepare-parent-drift');_local_processing_release(release_ref);facts=_local_processing_facts(parent_ref,worker_ref);archives=[{'original':r,'archive':immutable_raw(base/'materials'/(r['sha256']+'.data'),timing.checked_bytes(r))}for r in facts['materials']]
        return immutable(intent,{'kind':LOCAL_PROCESSING_KIND,'parent':parent_ref,'worker':worker_ref,'release':release_ref,'facts':facts,'archives':archives})

def _local_processing_prepared(intent_ref):
    intent=timing.pinned(intent_ref);facts=intent['facts'];base=location(facts['order'])/'.local-processing-recovery'/facts['parent']['sha256'];need(set(intent)=={'kind','parent','worker','release','facts','archives'}and intent['kind']==LOCAL_PROCESSING_KIND and intent_ref['path']==str(base/'intent.json')and intent['parent']==facts['parent']and intent['worker']==facts['worker'],'daily-local-intent-schema');mapping={}
    for p in intent['archives']:
        r,a=p['original'],p['archive'];need(set(p)=={'original','archive'}and a=={'path':str(base/'materials'/(r['sha256']+'.data')),'sha256':r['sha256']}and (r['path'],r['sha256'])not in mapping,'daily-local-archive');timing.checked_bytes(a);mapping[r['path'],r['sha256']]=a
    def raw(r):need((r['path'],r['sha256'])in mapping,'daily-local-missing-archive');return timing.checked_bytes(mapping[r['path'],r['sha256']])
    _local_processing_release(intent['release']);need(_local_processing_facts(facts['parent'],facts['worker'],raw,facts['materials'])==facts,'daily-local-recomputed-facts');return intent,raw

def _local_processing_repair_delta(before,after,company):
    import copy
    expected=copy.deepcopy(before);rows=[r for r in expected['companies']if r['company']==company];need(len(rows)==1 and rows[0]['status']=='failed','daily-local-repair-before');rows[0]['status']='acquired';expected['status']='running'
    statuses=[r['status']for r in expected['companies']];expected.update(companies_total=len(statuses),succeeded=statuses.count('complete'),needs_review=statuses.count('needs_review'),failed=statuses.count('failed'),skipped=statuses.count('skipped')+statuses.count('zero_rows'))
    stamp=after['updated_at'];need(timing.parse_time(stamp)>=timing.parse_time(before['updated_at']),'daily-local-repair-time');expected['updated_at']=stamp;expected['elapsed_s']=round((timing.parse_time(stamp)-timing.parse_time(before['created_at'])).total_seconds(),3);need(after==expected,'daily-local-repair-delta');return after

def verify_local_processing_recovery(current,proof_ref):
    proof=timing.pinned(proof_ref);need(set(proof)=={'kind','intent','repair_exit','batch_after','archives'}and proof['kind']==LOCAL_PROCESSING_KIND,'daily-local-proof-schema');intent,raw=_local_processing_prepared(proof['intent']);facts=intent['facts'];base=Path(proof['intent']['path']).parent;need(proof_ref['path']==str(base/'proof.json'),'daily-local-proof-location');mapping={}
    for p in proof['archives']:
        r,a=p['original'],p['archive'];need(set(p)=={'original','archive'}and a=={'path':str(base/'materials'/(r['sha256']+'.data')),'sha256':r['sha256']}and (r['path'],r['sha256'])not in mapping,'daily-local-repair-archive');timing.checked_bytes(a);mapping[r['path'],r['sha256']]=a
    def readnew(r):need((r['path'],r['sha256'])in mapping,'daily-local-missing-repair-archive');return timing.checked_bytes(mapping[r['path'],r['sha256']])
    need(proof['repair_exit']['path']==str(base/'repair-exit.json'),'daily-local-repair-exit-location')
    ex=json.loads(readnew(proof['repair_exit']));before=json.loads(raw(facts['batch']));after=json.loads(readnew(proof['batch_after']));argv=[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(FORMAL_CLI.with_name('flow.py')),'repair','--run-dir',before['run_dir'],'--company',facts['company']]
    need(set(ex)=={'argv','returncode','stdout','stderr','exited_at','timing'}and ex['argv']==argv and ex['returncode']==0 and ex['stdout']['path']==str(base/'repair-stdout.log')and ex['stderr']['path']==str(base/'repair-stderr.log')and _local_processing_clock_allowed(proof['intent'],proof['repair_exit'],ex,base) and timing.finite(ex['timing']['started_monotonic'])and timing.finite(ex['timing']['exited_monotonic'])and ex['timing']['started_monotonic']<=ex['timing']['exited_monotonic']and readnew(ex['stderr'])==b''and timing.parse_time(ex['exited_at'])>=timing.parse_time(before['updated_at']),'daily-local-repair-natural-exit');result=json.loads(readnew(ex['stdout']));row=next(r for r in before['companies']if r['company']==facts['company']);need(result=={'action':'process','company':facts['company'],'source':row['source'],'evidence':row['evidence']},'daily-local-public-repair-output');_local_processing_repair_delta(before,after,facts['company'])
    old=json.loads(raw(facts['parent']));need(current.get(LOCAL_PROCESSING_FIELD)==proof_ref and all(current.get(k)==v for k,v in old.items()if k not in('status','calls',*FINAL_FIELDS,'completion_ref','collection_ready'))and current['calls'][:len(old['calls'])]==old['calls'],'daily-local-preserved-parent-prefix');return {'failed_call':facts['failed_call'],'facts':facts}

def local_processing_exception(s,call,receipt):
    admitted=verify_local_processing_recovery(s,s[LOCAL_PROCESSING_FIELD]);return call==admitted['failed_call']and receipt['returncode']==2 and json.loads(receipt['stdout'])=={'ok':False,'error':LOCAL_PROCESSING_ERROR,'acceptance_pass':False}

def recover_local_processing_recovery(intent_ref,repair_exit_ref,*,guard,checkpoint=lambda stage:None):
    """Consume a natural public flowrepair; never launch/replay it. Self parentlock."""
    intent,raw=_local_processing_prepared(intent_ref);facts=intent['facts'];path=Path(facts['parent']['path']);base=Path(intent_ref['path']).parent;proof_path=base/'proof.json'
    with timing.locked(path),notify_recovery_command_scope():
        before=json.loads(raw(facts['parent']))
        if proof_path.exists():
            pr=timing.ref(proof_path);proof=timing.pinned(pr);need(proof['intent']==intent_ref and proof['repair_exit']==repair_exit_ref,'daily-local-proof-input-drift');after=proof['batch_after']
        else:
            guard('before-proof');need(timing.ref(path)==facts['parent'],'daily-local-parent-drift');ex=timing.pinned(repair_exit_ref);after=timing.ref(Path(facts['batch']['path']));refs=[repair_exit_ref,ex['stdout'],ex['stderr'],after];archives=[{'original':r,'archive':immutable_raw(base/'materials'/(r['sha256']+'.data'),timing.checked_bytes(r))}for r in refs];pr=immutable(proof_path,{'kind':LOCAL_PROCESSING_KIND,'intent':intent_ref,'repair_exit':repair_exit_ref,'batch_after':after,'archives':archives})
        expected={**before,LOCAL_PROCESSING_FIELD:pr};current=read(path);need(current in(before,expected),'daily-local-third-state');verify_local_processing_recovery(expected,pr);checkpoint('proof')
        if current==expected:guard('existing-readback');return pr
        guard('before-CAS');need(timing.ref(path)==facts['parent']and timing.ref(Path(facts['batch']['path']))==after,'daily-local-CAS-drift');timing.save(path,expected);checkpoint('parent');guard('readback');verify_local_processing_recovery(read(path),pr);return pr

_LOCAL_PROCESSING_VERIFY_UNCACHED=verify_local_processing_recovery
def verify_local_processing_recovery(current,proof_ref):
    scope=_NOTIFY_COMMAND_FACTS.get()
    if scope is None:return _LOCAL_PROCESSING_VERIFY_UNCACHED(current,proof_ref)
    key='local-processing:'+json.dumps([current,proof_ref],ensure_ascii=False,sort_keys=True,separators=(',',':'))
    if key not in scope:scope[key]=_LOCAL_PROCESSING_VERIFY_UNCACHED(current,proof_ref)
    else:
        proof=timing.pinned(proof_ref);intent=timing.pinned(proof['intent'])
        for pair in intent['archives']+proof['archives']:timing.checked_bytes(pair['archive'])
        _local_processing_release(intent['release'])
    return scope[key]


# This one reviewed caller version labelled process-local Python monotonic
# diagnostics CLOCK_MONOTONIC. Its original receipt is immutable. A separate
# provenance proof permits only its duration, never a system/outer clock value.
LOCAL_REPAIR_PROCESS_CLOCK_CALLER_SHA='ef6ed4888dcb10bca1c78807bc39ad2590beb67adb94a5a26d10f9cedd8e5510'
LOCAL_REPAIR_PROCESS_CLOCK_KIND='verified-local-repair-process-clock-diagnostic-v1'

def _local_clock_checked_material(reference):
    if reference['path']in (str(Path(__file__).absolute()),str(FORMAL_CLI.with_name('flow.py'))):
        return timing.checked_bytes(timing.configuration_source_material(reference)['material'])
    return timing.checked_bytes(reference)

def _local_processing_clock_facts(intent_ref,repair_exit_ref,metadata_intent_ref):
    intent,raw=_local_processing_prepared(intent_ref);base=Path(intent_ref['path']).parent;facts=intent['facts'];metadata=timing.pinned(metadata_intent_ref);actor=metadata.get('actor');authority=metadata.get('authority');contract_ref=metadata.get('contract');need(type(actor)is dict and actor.get('sha256')==LOCAL_REPAIR_PROCESS_CLOCK_CALLER_SHA,'daily-local-clock-reviewed-caller');timing.checked_bytes(actor);grant=timing.pinned(authority);contract=timing.pinned(contract_ref);work=Path(actor['path']).parent
    need(Path(actor['path']).name=='recover_processing_once.py'and metadata_intent_ref['path']==str(work/'metadata/intent.json')and metadata.get('kind')=='A24-public-local-processing-metadata-once-v1'and metadata['parent']==facts['parent']and metadata['worker']==facts['worker']and metadata['publication_result']==contract['publication_result'],'daily-local-clock-original-caller-intent')
    need(grant.get('kind')=='root-authorized-A24-local-processing-metadata-v1'and grant.get('execution_authorized')is True and grant.get('actor')==actor and grant.get('metadata_contract')==contract_ref and Path(authority['path'])==work/'root-metadata-authorization.json','daily-local-clock-original-authority')
    freeze=timing.pinned(grant['freeze']);need(grant['freeze']['path']==str(work/'metadata-freeze.json')and any(r==actor for r in freeze['refs'])and any(r==contract_ref for r in freeze['refs']),'daily-local-clock-authority-freeze');[_local_clock_checked_material(r)for r in freeze['refs']]
    need(contract['kind']=='A24-three-stage-public-processing-recovery-contract-v1'and contract['parent']==facts['parent']and contract['worker']==facts['worker']and contract['full_release']==intent['release']and contract['workspace']==str(work/'metadata')and contract['no_business_replay']is True,'daily-local-clock-original-contract')
    prepared_ref=timing.ref(work/'metadata/prepared.json');prepared=timing.pinned(prepared_ref);need(prepared=={'intent':metadata_intent_ref,'public_intent':intent_ref},'daily-local-clock-original-prepared')
    launch_ref=timing.ref(base/'caller-repair-launch-intent.json');process_ref=timing.ref(base/'caller-repair-process.json');launch=timing.pinned(launch_ref);process=timing.pinned(process_ref);ex=timing.pinned(repair_exit_ref)
    need(repair_exit_ref['path']==str(base/'repair-exit.json')and launch=={'kind':'A24-official-flow-repair-once-v1','public_intent':intent_ref,'argv':ex['argv'],'authority':authority}and process.get('argv')==ex['argv']and type(process.get('pid'))is int and process['pid']>0,'daily-local-clock-original-launch')
    tm=ex['timing'];need(tm.get('clock')=='CLOCK_MONOTONIC'and all(timing.finite(tm.get(k))for k in('started_monotonic','exited_monotonic','elapsed_seconds'))and 0<=tm['started_monotonic']<=tm['exited_monotonic']and abs(tm['elapsed_seconds']-(tm['exited_monotonic']-tm['started_monotonic']))<=1e-9 and ex['returncode']==0,'daily-local-clock-diagnostic-duration')
    issued=timing.parse_time(grant['issued_at']);expires=timing.parse_time(grant['expires_at']);need(0<(expires-issued).total_seconds()<=300 and issued<=timing.parse_time(metadata['started_at'])<=timing.parse_time(process['at'])<=timing.parse_time(ex['exited_at'])<expires,'daily-local-clock-original-authority-time')
    started_ref=timing.ref(work/'metadata-exec/started.json');outer_process_ref=timing.ref(work/'metadata-exec/process.json');started=timing.pinned(started_ref);outer_process=timing.pinned(outer_process_ref);expected_argv=[sys.executable,'-I','-B',actor['path'],'--authorization-sha',authority['sha256'],'--execute'];need(started['argv']==outer_process['argv']==expected_argv and type(started['wrapper_pid'])is int and type(outer_process['pid'])is int and outer_process['pid']>0 and issued<=timing.parse_time(started['at'])<=timing.parse_time(metadata['started_at'])<expires,'daily-local-clock-original-executor')
    outer_ref=timing.ref(work/'metadata-exec/natural-exit.json');outer=timing.pinned(outer_ref);stderr_ref=timing.ref(work/'metadata-exec/stderr.log');stderr=timing.checked_bytes(stderr_ref);need(outer['returncode']==1 and timing.parse_time(outer['at'])>=timing.parse_time(ex['exited_at'])and stderr.rstrip().endswith(b'ValueError: daily-local-repair-natural-exit'),'daily-local-clock-original-natural-hold')
    original_proof_ref=timing.ref(base/'proof.json');original_proof=timing.pinned(original_proof_ref);need(original_proof.get('kind')==LOCAL_PROCESSING_KIND and original_proof.get('intent')==intent_ref and original_proof.get('repair_exit')==repair_exit_ref,'daily-local-clock-original-proof')
    return {'original_proof':original_proof_ref,'kind':LOCAL_REPAIR_PROCESS_CLOCK_KIND,'intent':intent_ref,'repair_exit':repair_exit_ref,'metadata_intent':metadata_intent_ref,'actor':actor,'authority':authority,'contract':contract_ref,'prepared':prepared_ref,'launch':launch_ref,'process':process_ref,'outer_started':started_ref,'outer_process':outer_process_ref,'outer_exit':outer_ref,'outer_stderr':stderr_ref,'clock_semantics':'python-process-monotonic-diagnostic-duration-only','outer_clock_reinterpreted':False,'repair_replayed':False}

def record_local_processing_clock_compatibility(intent_ref,repair_exit_ref,metadata_intent_ref,*,guard):
    """Append provenance only; original receipt/proof/batch/parent stay untouched.
    Caller owns the original maintenance locks. No repair/input is executed.
    """
    guard('clock-proof-preflight');facts=_local_processing_clock_facts(intent_ref,repair_exit_ref,metadata_intent_ref);path=Path(intent_ref['path']).parent/'repair-clock-proof.json';guard('clock-proof-write');result=immutable(path,facts);verify_local_processing_clock_compatibility(result,intent_ref,repair_exit_ref);return result

def verify_local_processing_clock_compatibility(proof_ref,intent_ref,repair_exit_ref):
    need(proof_ref['path']==str(Path(intent_ref['path']).parent/'repair-clock-proof.json'),'daily-local-clock-proof-location');proof=timing.pinned(proof_ref);need(proof==_local_processing_clock_facts(intent_ref,repair_exit_ref,proof['metadata_intent']),'daily-local-clock-proof-facts');return proof

def _local_processing_clock_allowed(intent_ref,repair_exit_ref,receipt,base):
    if receipt['timing']['clock']==timing.MONOTONIC_CLOCK:return True
    need(receipt['timing']['clock']=='CLOCK_MONOTONIC','daily-local-repair-clock-unrecognized');verify_local_processing_clock_compatibility(timing.ref(base/'repair-clock-proof.json'),intent_ref,repair_exit_ref);return True



READY_SEAL_FIELD='known_ready_seal_failure_recovery'
READY_SEAL_KIND='verified-daily-ready-seal-failure-recovery-v1'
READY_SEAL_ERROR='ready-input-changed-before-seal'

def _ready_seal_release(reference):
    release=timing.pinned(reference);wanted={str(PROJECT/'skills/workshop-director/scripts/daily_execution_launcher.py'):384,str(FORMAL_CLI.with_name('notification_backlog.py')):420};targets=release.get('targets')
    need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and type(targets)is list and len(targets)==2 and {t['target']for t in targets}==set(wanted),'daily-ready-seal-reviewed-two-source-release')
    for target in targets:
        need(set(target)=={'target','before','after','old_sha256','mode'}and target['old_sha256']==target['before']['sha256']and target['before']['path']==str(Path(reference['path']).parent/(Path(target['target']).name+'.before'))and target['mode']==wanted[target['target']],'daily-ready-seal-source-target')
        timing.checked_bytes(target['before']);timing.checked_bytes(target['after']);timing.configuration_source_material({'path':target['target'],'sha256':target['after']['sha256']})
        need(Path(target['target']).stat().st_mode&0o777==target['mode'],'daily-ready-seal-source-mode')
    return release

def _ready_seal_facts(parent_ref,worker_ref,readpin=timing.pinned,refs=None):
    materials=[]
    def take(r):
        value=readpin(r)
        if r not in materials:materials.append(r)
        return value
    def at(path):
        if refs is None:return timing.ref(path)
        matches=[r for r in refs if r['path']==str(path)];need(len(matches)==1,'daily-ready-seal-material-path');return matches[0]
    s=take(parent_ref);root=location(s['order']);need(parent_ref['path']==str(root/'state.json')and s.get('status')=='attention'and not s.get(READY_SEAL_FIELD)and not s.get('completion_ref')and not s.get('collection_ready'),'daily-ready-seal-original-frontier')
    need(take(s['origin_ref'])=={k:s[k]for k in ORIGIN_FIELDS},'daily-ready-seal-origin');call=s['calls'][-1]
    need(call['index']==len(s['calls'])-1 and call['state']=='failed'and call['verb']=='advance'and call['argv']==argv_for(s['order'],s['archive_root'],'advance',s['mode'],call['tab_id'],call['steps']),'daily-ready-seal-original-advance')
    need(call['launch']['path']==str(root/'children'/('%04d-launch.json'%call['index']))and call['result']['path']==str(root/'children'/('%04d-result.json'%call['index']))and take(call['launch'])=={k:v for k,v in call.items()if k not in('launch','state','result')},'daily-ready-seal-original-call')
    ex=take(call['result']);need(ex['kind']=='daily-child-exit-v1'and ex['launch']==call['launch']and ex['argv']==call['argv']and ex['order']==s['order']and ex['run_id']==s['run_id']and ex['boot_identity']==s['boot_identity']and ex['returncode']==2 and type(ex['returncode'])is int and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':READY_SEAL_ERROR,'acceptance_pass':False}and s['start_monotonic']<=call['launch_monotonic']<=ex['exited_monotonic'],'daily-ready-seal-natural-exit')
    need(all(c['state']in('returned','failed')for c in s['calls'][:-1]),'daily-ready-seal-other-unknown')
    worker=take(worker_ref);rq=take(worker['request']);response=take(worker['response']);attempt=Path(worker_ref['path']).parent
    need(worker_ref['path']==str(attempt/'exit.json')and worker['kind']=='workshop-worker-exit-v1'and worker['returncode']==0 and worker['attempt_id']==rq['attempt_id']==response['attempt_id']==attempt.name and rq['task']['id']==response['task_id']and rq['task']['flow']=='daily-comment-stats'and response['outcome']=='failed'and response['error']=='parent-hold-inspect-original'and rq['context']['order']==response['context']['order']==s['order']and rq['context']['stage']==response['context']['stage']=='advance','daily-ready-seal-original-worker')
    px=take(at(attempt/'parent-advance-exit.json'));offer=take(rq['context']['offer']);need(px['returncode']==0 and px['argv']==offer['daily_execution']['commands']['advance']+['--tab-id',str(rq['context']['scope']['tab_id'])],'daily-ready-seal-parent-command')
    # Parent stdout binds its run; exact child/frontier is pinned above.
    out=json.loads(timing.checked_bytes(px['stdout'])if refs is None else readpin(px['stdout'],binary=True));materials.extend([px['stdout'],px['stderr']]);need((timing.checked_bytes(px['stderr'])if refs is None else readpin(px['stderr'],binary=True))==b'','daily-ready-seal-parent-stderr');need(out['status']=='attention'and out['run_id']==s['run_id']and out['origin']==s['origin']and out['mode']==s['mode'],'daily-ready-seal-parent-result')
    inner=root.parent.parent/'daily-executions'/Path(s['order']['path']).stem;role_ref=at(inner/'state.json');role=take(role_ref);need(role['order']==s['order']and role['phase']=='acquisition','daily-ready-seal-inner-acquisition');batch_ref=at(Path(role['run_dir'])/'batch_receipt.json');batch=take(batch_ref)
    need(batch['status']=='complete'and batch['failed']==batch['needs_review']==0 and batch['roundtrip']['required']is True and batch['roundtrip']['verified']is True and batch['dispatch_scope']['work_order']==s['order']and batch['delivery_contract']=='three-flow-collection-ready-v1'and batch['sent']is False,'daily-ready-seal-complete-source')
    return_job=take(role['handoff']['work_order']);return_wf=take(at(return_job['workflow_path']))
    need(role['handoff']['action']==return_job['action']=='return-company'and return_wf['work_order_id']==return_job['work_order_id']and return_wf['state']=='complete'and return_wf['phase']=='done'and return_wf['company']==batch['roundtrip']['target_company']==return_job['company']and str(return_wf['groupid'])==str(return_job['groupid'])and return_wf['identity']==return_job['identity_baseline']and all(c['state']=='confirmed'for c in return_wf['calls']),'daily-ready-seal-return-completed')
    progress_ref=at(batch['progress_file']);progress=take(progress_ref)
    for row in batch['companies']:
        receipt=take(at(row['receipt']));dates=row['date_range'];entry=progress['companies'][row['company']]
        need(row['status']==receipt['status']in('complete','zero_rows')and receipt['company']==row['company']and receipt['attribution_verified']is True and receipt['mismatch']is False and not receipt['warnings']and entry['next_start']==dates['start']and not any(c.get('start')==dates['start']and c.get('end')==dates['end']for c in entry.get('completions',[])),'daily-ready-seal-original-data-and-cursor')
    return {'parent':parent_ref,'worker':worker_ref,'order':s['order'],'task_id':rq['task']['id'],'outer':rq['task']['outer'],'failed_call':call,'role':role_ref,'batch':batch_ref,'progress':progress_ref,'materials':materials}

def verify_ready_seal_recovery(current,proof_ref):
    proof=timing.pinned(proof_ref);need(set(proof)=={'kind','facts','release','archives'}and proof['kind']==READY_SEAL_KIND,'daily-ready-seal-proof-schema');facts=proof['facts'];base=location(facts['order'])/'.ready-seal-recovery'/facts['parent']['sha256'];need(proof_ref['path']==str(base/'proof.json'),'daily-ready-seal-proof-location');mapping={}
    for pair in proof['archives']:
        r,a=pair['original'],pair['archive'];need(set(pair)=={'original','archive'}and a=={'path':str(base/'materials'/(r['sha256']+'.data')),'sha256':r['sha256']},'daily-ready-seal-archive');timing.checked_bytes(a);mapping[r['path'],r['sha256']]=a
    def archived(r,binary=False):
        need((r['path'],r['sha256'])in mapping,'daily-ready-seal-missing-archive');raw=timing.checked_bytes(mapping[r['path'],r['sha256']]);return raw if binary else json.loads(raw)
    need(_ready_seal_facts(facts['parent'],facts['worker'],archived,facts['materials'])==facts,'daily-ready-seal-recomputed-facts');_ready_seal_release(proof['release']);before=archived(facts['parent'])
    need(current.get(READY_SEAL_FIELD)==proof_ref and all(current.get(k)==v for k,v in before.items()if k not in('status','calls',*FINAL_FIELDS,'completion_ref','collection_ready'))and current['calls'][:len(before['calls'])]==before['calls'],'daily-ready-seal-preserved-prefix');return facts

def ready_seal_exception(s,call,receipt):
    if receipt['returncode']!=2 or json.loads(receipt['stdout'])!={'ok':False,'error':READY_SEAL_ERROR,'acceptance_pass':False}:return False
    if call!=timing.pinned(s[READY_SEAL_FIELD])['facts']['failed_call']:return False
    return call==verify_ready_seal_recovery(s,s[READY_SEAL_FIELD])['failed_call']

def recover_ready_seal_failure(parent_ref,worker_ref,release_ref,*,guard,checkpoint=lambda stage:None):
    """Self parent lock, append-only proof/marker; no child or sender is run."""
    path=Path(parent_ref['path']);base=path.parent/'.ready-seal-recovery'/parent_ref['sha256'];proofpath=base/'proof.json'
    with timing.locked(path),notify_recovery_command_scope():
        guard('preflight');_ready_seal_release(release_ref)
        if proofpath.exists():
            pr=timing.ref(proofpath);proof=timing.pinned(pr);need(proof['facts']['parent']==parent_ref and proof['facts']['worker']==worker_ref and proof['release']==release_ref,'daily-ready-seal-same-proof');before=next(timing.pinned(p['archive'])for p in proof['archives']if p['original']==parent_ref)
        else:
            need(timing.ref(path)==parent_ref,'daily-ready-seal-before-drift');facts=_ready_seal_facts(parent_ref,worker_ref);before=timing.pinned(parent_ref)
            inner=Path(facts['role']['path']).parent
            need(not(inner/'collection-ready.json').exists()and not(inner/'outbox').exists(),'daily-ready-seal-output-or-sender-present')
            archives=[{'original':r,'archive':immutable_raw(base/'materials'/(r['sha256']+'.data'),timing.checked_bytes(r))}for r in facts['materials']];pr=immutable(proofpath,{'kind':READY_SEAL_KIND,'facts':facts,'release':release_ref,'archives':archives})
        proof=timing.pinned(pr);expected={**before,READY_SEAL_FIELD:pr};current=read(path);need(current in(before,expected),'daily-ready-seal-third-state');verify_ready_seal_recovery(expected,pr);checkpoint('proof')
        if current==expected:guard('existing-readback');return pr
        guard('before-CAS')
        for r in proof['facts']['materials']:timing.checked_bytes(r)
        inner=Path(timing.pinned(pr)['facts']['role']['path']).parent
        need(not(inner/'collection-ready.json').exists()and not(inner/'outbox').exists(),'daily-ready-seal-output-or-sender-present')
        _notify_absent(path.parent/'children'/('%04d-launch.json'%len(before['calls'])))
        need(timing.ref(path)==parent_ref,'daily-ready-seal-CAS-drift');timing.save(path,expected);checkpoint('parent');guard('readback');verify_ready_seal_recovery(read(path),pr);return pr

if __name__=='__main__':raise SystemExit(main())
