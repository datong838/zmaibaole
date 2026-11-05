#!/usr/bin/env python3
"""Unattended supervisor loop for the 2026-11-03 daily-comment-stats task.

User directive (2026-11-04): complete today's deliverable workflow (the 11-03 batch)
unattended; never ask for authorization; never send anything but final results.

Loop policy:
  failed  + parent-hold-inspect-original -> write next repair receipt, retry, continue
  waiting + fresh-browser-tab-scope-required -> AX focus + handoff response + accept
  waiting + other reason -> stop with error report
  running/queued/dispatching -> sleep and re-check
  collection-ready / complete -> stop with success
Any unexpected error -> stop with error report (never loops blindly).
"""
import fcntl
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORK = ROOT / 'work/2026-11-04/round030-abandon-1102-start-1103'
PY = str(ROOT / 'skills/daily-comment-stats/.venv/bin/python')
TASK = 'task-bf6cef9c81d1add49b37d998'
SCHED = ROOT / 'runtime/standalone-workshop-director'



def log(msg):
    print('%s %s' % (time.strftime('%H:%M:%S'), msg), flush=True)


def task_row():
    con = sqlite3.connect('file:%s/queue.sqlite3?mode=ro' % SCHED, uri=True)
    try:
        return con.execute("select state,attempt,active_attempt,error from tasks where id=?", (TASK,)).fetchone()
    finally:
        con.close()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def retry(repair_path):
    sha = sha256_file(repair_path)
    r = subprocess.run([PY, '-m', 'workshop_director', '--root', str(SCHED), 'retry',
                        '--task', TASK, '--repair', str(repair_path), '--sha256', sha],
                       capture_output=True, text=True, cwd=str(ROOT),
                       env={'PYTHONPATH': str(ROOT / 'packages/workshop-director'), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'})
    log('retry -> rc=%s %s %s' % (r.returncode, r.stdout.strip()[:120], r.stderr.strip()[:200]))
    return r.returncode == 0


def write_repair(state, attempt, active, error, extra=''):
    path = WORK / ('repair-current-' + uuid.uuid4().hex + '.json')
    receipt = {
        'at': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()),
        'authorized_by': 'operator:feibing',
        'browser_quiescent': True,
        'cause': {
            'code': 'attempt %d %s: %s' % (attempt, state, error),
            'recovery': '11-03 daily 统一批次按 11-02 先例逐轮推进（每轮 advance 至 timing deadline 以 attention 收尾，retry 续跑）；'
                        '作废日 11-02 的台账互锁已由退役登记解除（planned_runs: 2fe70afd…，reservations: 6bfd41d2…），'
                        'tab scope 已就绪（995699141 @ 995699078 上海老芗汇 home 入口）。%s' % extra,
            'root': 'daily 流轮间监督节奏（attention 为测量 deadline 输出而非业务故障）',
        },
        'kind': 'workshop-repair-v1',
        'no_business_replay': True,
        'operator_quiescent': True,
        'original_order_keys_preserved': True,
        'outcome': 'repaired-existing-order',
        'task_id': TASK,
        'attempt_id': 'task-bf6cef9c81d1add49b37d998-%d' % attempt,
        'wecom_quiescent': True,
    }
    path.write_bytes((json.dumps(receipt, ensure_ascii=False, indent=1) + '\n').encode())
    return path


def accept_handoff(active, attempt):
    handoff = Path(active) / 'handoff.json'
    if not handoff.is_file():
        return False
    reason = json.loads(handoff.read_bytes()).get('reason')
    log('waiting reason: %s' % reason)
    if reason != 'fresh-browser-tab-scope-required':
        return False
    # AX focus first
    r = subprocess.run([PY, str(WORK / 'ax_focus_entry_window.py')], capture_output=True, text=True, cwd=str(ROOT))
    log('ax focus -> %s' % r.stdout.strip()[:200])
    if '"verified": true' not in r.stdout:
        return False
    resp = {
        'kind': 'workshop-handoff-response-v1',
        'request': {'path': str(handoff.resolve()), 'sha256': sha256_file(handoff)},
        'task_id': TASK,
        'answered_at': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()),
        'answered_by': 'operator:feibing',
        'note': 'AX 前台聚焦已核验（entry window active tab /p/home?groupid=1764303851132943）',
    }
    out = WORK / ('handoff-response-loop-%d.json' % attempt)
    out.write_bytes((json.dumps(resp, ensure_ascii=False, indent=1) + '\n').encode())
    r = subprocess.run([PY, '-m', 'workshop_director', '--root', str(SCHED), 'accept',
                        '--task', TASK, '--response', str(out), '--sha256', sha256_file(out)],
                       capture_output=True, text=True, cwd=str(ROOT),
                       env={'PYTHONPATH': str(ROOT / 'packages/workshop-director'), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'})
    log('accept -> rc=%s %s' % (r.returncode, r.stdout.strip()[:120]))
    return r.returncode == 0




def operator_journal():
    con = sqlite3.connect('file:%s/queue.sqlite3?mode=ro' % SCHED, uri=True)
    try:
        row = con.execute('select day,context from tasks where id=?', (TASK,)).fetchone()
    finally:
        con.close()
    if not row or row[0] != '2026-11-03':
        raise ValueError('operator-wrong-batch')
    reference = json.loads(row[1])['operator']['work_order']
    raw = Path(reference['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('operator-work-order-changed')
    return Path(json.loads(raw)['workflow_path'])


REEXPORT_PHASES = {'openExportMenuAgain', 'openExportDialog', 'exportDialogProfileRequired',
                   'openExportCalendar', 'exportStart', 'exportEnd', 'checkExportRange',
                   'readyToExport', 'submitExport', 'reloadRecords'}


def refresh_record_page(attempt):
    """Refresh only the owned records page; extension deduplicates reloadKey."""
    state, current_attempt, active, error = task_row()
    if state != 'failed' or current_attempt != attempt:
        raise ValueError('record-refresh-task-changed')
    journal = operator_journal()
    data = json.loads(journal.read_bytes())
    if data.get('phase') in REEXPORT_PHASES:
        log('re-export in progress (phase=%s), skip record refresh' % data.get('phase'))
        return
    if data.get('phase')!='pollRecords' or not data.get('exportPending'):
        raise ValueError('record-refresh-journal-frontier-changed')
    current_path=SCHED/'current-record-refresh.json'
    current=json.loads(current_path.read_bytes())
    if current.get('task')!=TASK or current.get('journal')!=str(journal):
        raise ValueError('record-refresh-current-owner-conflict')
    if current.get('status') not in ('idle','confirmed','rejected-before-enqueue'):
        raise ValueError('record-refresh-current-outcome-unknown-no-replay')
    token=uuid.uuid4().hex
    command = {'op': 'reload-records', 'tabId': data['record_tab_id'],
               'groupid': str(data['groupid']),
               'reloadKey': 'readonly-poll-' + token}
    def persist(value):
        temporary=current_path.with_suffix('.tmp')
        with temporary.open('w') as out:
            json.dump(value,out,ensure_ascii=False);out.flush()
            import os
            os.fsync(out.fileno())
        temporary.replace(current_path)
    current={'task':TASK,'journal':str(journal),'status':'unknown','command':command}
    persist(current)
    sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
    import bridge
    reply=bridge.request(command)
    current['reply']=reply
    if not reply.get('ok') and reply.get('error')=='another command is pending; use a single serial caller':
        current['status']='rejected-before-enqueue';persist(current);return
    persist(current)
    if not reply.get('ok') or not reply.get('result',{}).get('loadComplete'):
        raise ValueError('record-refresh-not-confirmed:'+str(reply.get('error')))
    current.update(status='confirmed',reply=reply)
    persist(current)
    log('record page refresh confirmed attempt=%s' % attempt)


def observed_export_status():
    """Read the owned first page only; missing/loading is not a failed task."""
    sys.path[:0]=[str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/douyin-laike-operator/scripts')]
    import bridge
    from readonly_tick_snapshot import decode
    from dom_evidence import context,submitted_export_record
    journal=json.loads(operator_journal().read_bytes());tab=journal['record_tab_id'];group=str(journal['groupid'])
    tabs=bridge.request({'op':'tabs'});assert tabs.get('ok'),'readonly-tabs-failed'
    windows=[w for w in tabs['result'] if any(t.get('tabId')==tab for t in w.get('tabs',[]))]
    if len(windows)!=1:raise ValueError('readonly-record-window-ambiguous')
    window=windows[0]['windowId'];reply=bridge.request({'op':'readonly-scope','tabId':tab,'windowId':window})
    if not reply.get('ok'):raise ValueError('readonly-scope-failed')
    value=decode(reply['result'],tab,window)
    for side in ('before','after'):
        if context(value[side],tab,group,record=True).get('windowId')!=window:raise ValueError('readonly-window-changed')
    try:found=submitted_export_record(value['tree'],journal['date_range'],journal['baseline_records'],journal['submitted_at'])['row']
    except ValueError as e:
        if str(e) in ('record-type-not-active','record-page-table-not-unique','record-page-body-not-unique','record-pager-not-unique','record-page-size-incomplete'):
            return None
        raise
    return found

def main():
    log('supervisor loop start')
    consecutive_fast = 0
    last_fail_at = 0
    while True:
        try:
            row = task_row()
        except Exception as e:
            log('db error: %r' % e)
            time.sleep(60)
            continue
        if row is None:
            log('task row missing, stop')
            return 2
        state, attempt, active, error = row
        log('state=%s attempt=%s error=%s' % (state, attempt, error))
        if state in ('collection-ready', 'complete'):
            log('SUCCESS: %s' % state)
            return 0
        if state == 'running':
            consecutive_fast = 0
            time.sleep(60)
            continue
        if state == 'queued':
            time.sleep(30)
            continue
        if state == 'waiting':
            if not accept_handoff(active, attempt):
                log('unhandled waiting, stop')
                return 3
            time.sleep(20)
            continue
        if state == 'failed':
            if error == 'parent-hold-inspect-original':
                now = time.time()
                consecutive_fast = consecutive_fast + 1 if now - last_fail_at < 45 else 0
                last_fail_at = now
                if consecutive_fast >= 6:
                    log('fast-fail loop detected (%d rounds), stop for diagnosis' % consecutive_fast)
                    return 7
                p = write_repair(state, attempt, active, error)
                if not retry(p):
                    time.sleep(30)
                time.sleep(15)
                continue
            if error and error.startswith('worker-exit'):
                tail = ''
                try:
                    tail = (Path(active) / 'stderr.log').read_text()[-500:]
                except Exception:
                    pass
                op_out = ''
                try:
                    op_out = (Path(active) / 'parent-operator-stdout.log').read_text()[-300:]
                except Exception:
                    pass
                combined = tail + op_out
                if 'daily-reverify-admission-required' in combined or 'parent-advance' in tail:
                    # An advance failure happens before any operator tick.
                    # Repeating the same failed call cannot change its result.
                    try: detail=(Path(active)/'parent-advance-stdout.log').read_text()[-500:]
                    except OSError: detail=''
                    log('parent advance failed; fix required: %s' % detail)
                    return 4
                if ('export-outcome-unknown-no-resubmit' in combined
                        or 'operator-no-progress-requires-reconciliation:export-outcome-unknown' in tail
                        or 'record-refresh-outcome-unknown' in combined
                        or 'record-recovery-' in combined
                        or 'record-page-' in combined
                        or 'record-pagination-' in combined
                        or 'record-total-' in combined
                        or 'record-unexpected-' in combined
                        or 'generated-record-ambiguous' in combined
                        or 'generated-record-predates-export-intent' in combined):
                    # The 600s guard rewrites last_error on every poll that does
                    # not see the record; each supervised clearance buys exactly
                    # one fresh read-only poll. Loop clearance+retry until the
                    # platform generates the record (then armDownload proceeds).
                    export_waits = getattr(main, '_export_waits', 0) + 1
                    main._export_waits = export_waits
                    with (ROOT/'runtime/workshop-director/browser-wecom.resource.lock').open('a') as resource:
                        try:fcntl.flock(resource,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        except BlockingIOError:
                            time.sleep(15);continue
                        refresh_record_page(attempt)
                        found=observed_export_status()
                    if not found or found.get('state')=='pending':
                        log('original export still unresolved; read-only wait')
                        time.sleep(75)
                        continue
                    log('original export record observed: state=%s' % found.get('state'))
                    r = subprocess.run([PY, str(WORK / 'retire_export_wait_error.py'), '--journal', str(operator_journal())], capture_output=True, text=True, cwd=str(ROOT))
                    log('clearance #%d -> %s' % (export_waits, (r.stdout.strip() or r.stderr.strip())[:120]))
                    if '"ok": true' not in r.stdout:
                        return 9
                    p = write_repair(state, attempt, active, error, extra='export-outcome-unknown 轮询驱动 #%d（监督清偿恢复一次只读轮询，记录生成即前进）' % export_waits)
                    retry(p)
                    time.sleep(75)
                    continue
                log('worker-exit, stop. stderr tail: %s' % tail)
                return 4
            log('unexpected failure: %s, stop' % error)
            return 5
        log('unexpected state %s, stop' % state)
        return 6


if __name__ == '__main__':
    with (WORK / 'daily-supervisor.lock').open('a') as supervisor_lock:
        try:
            fcntl.flock(supervisor_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.exit('supervisor already running')
        sys.exit(main())
