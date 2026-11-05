"""Supervised retirement of ledger state left by an abandoned workshop day.

Encodes, as reviewed code with fail-closed assertions, the exact retirement
performed for 2026-10-30 (supervised-day-abandonment-v1): when a unified day
is abandoned by the coordinator, its business ledger side-state must follow,
otherwise every later catch-up batch is blocked by
'collection-reservation-pending-delivery' / overlapping original plans.

What this removes (and ONLY this):
  * planned_runs entries whose run_dir belongs to the abandoned batch;
  * collection_reservations in state 'collection-ready' whose run_dir belongs
    to the abandoned batch.

What this never touches: completions, cursors (next_start/covered_through),
initial_start, or any collected artifact on disk. The retirement proof is
written under the abandoned day's coordinator archive (days/<day>/) with the
before/after ledger digests, so the operation is auditable and idempotent.
"""
import hashlib,json,sys
from pathlib import Path
from datetime import datetime,timezone,timedelta

PROJECT=Path(__file__).resolve().parents[3]
LEDGER=PROJECT/'runtime/daily-comment-stats/progress.json'

def retire(abandoned_day,abandoned_run_marker,authorized_by):
    """Retire ledger state belonging to the abandoned batch, fail-closed."""
    need=lambda ok,why: (_ for _ in ()).throw(ValueError(why)) if not ok else None
    need(len(abandoned_day)==10 and abandoned_day[4]=='-','abandon-day-invalid')
    need(abandoned_run_marker and '/' not in abandoned_run_marker,'abandon-run-marker-invalid')
    archive=PROJECT/'runtime/workshop-director/days'/abandoned_day
    need(archive.is_dir(),'abandoned-day-archive-missing:coordinator must abandon the day first')
    proof_path=archive/('retired-reservations-%s.json'%abandoned_day)
    if proof_path.exists():
        return {'idempotent':True,'proof':str(proof_path),'sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest()}
    raw=LEDGER.read_bytes();data=json.loads(raw)
    retired={}
    for company,entry in data['companies'].items():
        res=entry.get('collection_reservations') or {}
        hit=[k for k,r in res.items()
             if r.get('state')=='collection-ready' and abandoned_run_marker in str(r.get('run_dir',''))]
        need(len(hit)<=1,'ambiguous-reservation-match:'+company)
        for k in hit:
            retired[company]=res.pop(k)
        entry['collection_reservations']=res
        planned=entry.get('planned_runs') or {}
        drop=[k for k in planned if abandoned_run_marker in k]
        if drop:
            retired[company]={'reservation':retired.get(company),'retired_planned_runs':drop}
            for k in drop: planned.pop(k)
        entry['planned_runs']=planned
    need(retired,'nothing-to-retire-matcher-mismatch')
    after=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
    need(json.loads(after)==json.loads(raw),'semantic-equivalence-required')
    # Cursors must be byte-identical: retirement never advances coverage.
    before_c={c:(e.get('next_start'),e.get('covered_through'),e.get('initial_start'),len(e.get('completions',[]))) for c,e in json.loads(raw)['companies'].items()}
    after_c={c:(e.get('next_start'),e.get('covered_through'),e.get('initial_start'),len(e.get('completions',[]))) for c,e in data['companies'].items()}
    need(before_c==after_c,'cursor-must-not-move')
    LEDGER.write_bytes(after)
    proof={'kind':'supervised-day-ledger-retirement-v1','day':abandoned_day,
     'abandoned_run_marker':abandoned_run_marker,'retired':retired,
     'collected_artifacts_preserved':True,'ledger_cursor_untouched':True,
     'ledger_sha256_before':hashlib.sha256(raw).hexdigest(),
     'ledger_sha256_after':hashlib.sha256(after).hexdigest(),
     'authorized_by':authorized_by,
     'at':datetime.now(timezone.utc).isoformat(),
     'local_at':datetime.now(timezone(timedelta(hours=8))).isoformat()}
    proof_path.write_text(json.dumps(proof,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    return {'retired':sorted(retired),'proof':str(proof_path),'sha256':hashlib.sha256(proof_path.read_bytes()).hexdigest()}

if __name__=='__main__':
    p=sys.argv
    need_len=len(p)==4
    assert need_len,'usage: supervised_day_retirement.py <abandoned_day> <abandoned_run_marker> <authorized_by>'
    print(json.dumps(retire(p[1],p[2],p[3]),ensure_ascii=False,indent=1))
