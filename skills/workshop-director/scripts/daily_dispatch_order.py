#!/usr/bin/env python3
"""Archive an already-issued daily dispatch offer; never dispatch or run work.

Prepare this artifact at dispatch, before launching the operator. The operator's
future timing.start work_order is this immutable file, not a later batch receipt.
This module grants no authority to bypass the director's three acceptance gates.
"""
import argparse
import hashlib
import json
import os
import re
import tempfile
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import execution_timing as timing

KIND='daily-dispatch-order-v1'
WORKFLOW='daily-comment-stats'
ROLE='daily_stats_operator'
DEFAULT_COMPANIES=Path(__file__).resolve().parents[2]/'daily-comment-stats/config/companies.json'


def need(ok, reason):
    if not ok:raise ValueError(reason)


def canonical_path(root, dispatch_id):
    return Path(root).resolve()/'dispatch-orders'/(hashlib.sha256(dispatch_id.encode()).hexdigest()+'.json')


def iso(value):
    need(type(value) is str,'daily-dispatch-date-invalid')
    try:need(date.fromisoformat(value).isoformat()==value,'daily-dispatch-date-invalid')
    except ValueError:raise ValueError('daily-dispatch-date-invalid')
    return value


def build(offer_ref, companies_ref, *, origin, resumed_from=None, _seen=()):
    offer=timing.pinned(offer_ref);config=timing.pinned(companies_ref)
    need(origin in ('fresh','resume') and ((origin=='resume')==(resumed_from is not None)),'daily-dispatch-origin-invalid')
    need(type(offer) is dict and offer.get('workflow')==WORKFLOW and offer.get('role')==ROLE and offer.get('action')=='dispatch' and (offer.get('tool')=='collaboration.followup_task' and 'dispatcher_protocol' not in offer or offer.get('tool')=='local-subprocess-v1' and offer.get('dispatcher_protocol')=='local-subprocess-v1'),'daily-dispatch-offer-invalid')
    need(offer.get('collection_contract')in(None,'three-flow-collection-ready-v1'),'daily-dispatch-collection-contract')
    dispatch_id=offer.get('dispatch_id');need(type(dispatch_id) is str,'daily-dispatch-id-invalid')
    match=re.fullmatch(r'(\d{4}-\d{2}-\d{2}):daily-comment-stats:(0|[1-9]\d*)',dispatch_id)
    need(match is not None,'daily-dispatch-id-invalid');day=iso(match[1])
    entries=offer.get('ledger_snapshots');need(type(entries) is list and len(entries)==1,'daily-dispatch-one-daily-snapshot-required')
    entry=entries[0];need(type(entry) is dict and entry.get('workflow')==WORKFLOW and entry.get('company') is None,'daily-dispatch-ledger-scope-invalid')
    ledger=timing.pinned(entry.get('snapshot'));need(ledger.get('version')==1 and type(ledger.get('companies')) is dict,'daily-dispatch-ledger-invalid')
    companies=config.get('companies');policy=timing.company_policy(offer.get('active_company_policy'));v2=policy is not None and policy.get('kind')=='active-company-scope-policy-v2';need(type(companies)is dict and (bool(companies)if v2 else len(companies)==2),'daily-dispatch-company-config-invalid')
    import execution_timing as company_scope
    names=company_scope.offer_company_names(offer)
    need(set(names)<=set(companies),'daily-dispatch-policy-company-config')
    companies={name:companies[name]for name in names}
    if v2:
        need(offer.get('collection_contract')=='three-flow-collection-ready-v1','daily-dispatch-v2-requires-unified-collection')
        need(companies=={r['company']:{'groupid':r['groupid']}for r in policy['active']},'daily-dispatch-config-policy-gid-mismatch')
    ranges=[];plans=[];skipped=[]
    need(len({x.get('groupid') for x in companies.values() if type(x) is dict})==len(companies),'daily-dispatch-company-duplicate')
    need(set(entry.get('progress',{}))==set(companies),'daily-dispatch-summary-companies-invalid')
    for company,identity in companies.items():
        need(type(identity) is dict and type(identity.get('groupid')) is str and re.fullmatch(r'\d+',identity['groupid']),'daily-dispatch-company-config-invalid')
        value=ledger['companies'].get(company);need(type(value) is dict,'daily-dispatch-company-ledger-missing')
        start=iso(value.get('next_start'))
        original=value.get('planned_runs',{});need(type(original) is dict,'daily-dispatch-original-plans-invalid')
        expected={k:value.get(k) for k in ('next_start','covered_through','last_completed_on')}
        expected.update(original_plan_ids=list(original),original_batch_ids=list(value.get('batches',{})),original_task_ids=list(value.get('tasks',{})))
        need(entry['progress'][company]==expected,'daily-dispatch-summary-not-derived')
        if start>=day:
            skipped.append({'company':company,'groupid':identity['groupid'],'next_start':start,'reason':'already-covered-through-dispatch-day-exclusive','ledger_snapshot':entry['snapshot']});continue
        for run_dir,plan in original.items():
            need(type(run_dir) is str and Path(run_dir).is_absolute() and type(plan) is dict,'daily-dispatch-original-plan-invalid')
            first,last=iso(plan.get('start')),iso(plan.get('end'));need(first<=last,'daily-dispatch-original-plan-invalid')
            if first<day and last>=start:plans.append({'company':company,'run_dir':run_dir,'date_range':plan})
        ranges.append({'company':company,'groupid':identity['groupid'],'start':start,'end_exclusive':day})
    # Missing files or an old "complete" boolean must not relabel an overlapping
    # original plan as a new run. Business resume checks remain the role's job.
    need(ranges,'daily-dispatch-no-pending-range')
    need(origin!='fresh' or not plans,'daily-dispatch-existing-plan-use-resume')
    scope={'workflow':WORKFLOW,'company_ranges':ranges,'test_target':timing.TARGET,'delivery_contract':timing.DYNAMIC_DELIVERY}
    timing.scope_check(scope)
    resume_identity=None
    if resumed_from:
        source_path=Path(resumed_from['path']);need(str(source_path) not in _seen and len(_seen)<20,'daily-dispatch-resume-cycle')
        previous=validate(resumed_from,source_path.parent.parent,_seen=_seen+(str(source_path),))
        need(previous['workflow']==WORKFLOW and previous['role']==ROLE and previous['day']==day,'daily-dispatch-resume-workflow-day-mismatch')
        need(previous['company_config']==companies_ref and all(x in previous['scope']['company_ranges'] for x in ranges),'daily-dispatch-resume-company-range-mismatch')
        need(previous.get('collection_contract')==offer.get('collection_contract'),'daily-dispatch-resume-collection-contract')
        need(previous['dispatch_id']!=dispatch_id,'daily-dispatch-resume-original-dispatch-required')
        resume_identity={'dispatch_id':previous['dispatch_id'],'work_order':resumed_from,'scope_sha256':previous['scope_sha256']}
    return {'kind':KIND,'dispatch_id':dispatch_id,'day':day,'role':ROLE,'workflow':WORKFLOW,'origin':origin,'resumed_from':resumed_from,'scope':scope,'scope_sha256':timing.digest(scope),'offer':offer_ref,'ledger_snapshot':entry['snapshot'],'company_config':companies_ref,'overlapping_original_plans':plans,'skipped_companies':skipped,'resume_identity':resume_identity,'dispatch_authorization_granted':False,'business_actions_performed':False,'timing_started':False,'operator_start_boundary':'before-role-planning-and-prechecks','production_enabled':False,'complaint_submission_enabled':False,**({'collection_contract':offer['collection_contract']}if offer.get('collection_contract')else{}),**({'active_company_policy':offer['active_company_policy']}if offer.get('active_company_policy')else{})}


def encode(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def archive(root, offer_ref, companies_ref, *, origin, resumed_from=None):
    order=build(offer_ref,companies_ref,origin=origin,resumed_from=resumed_from);path=canonical_path(root,order['dispatch_id']);raw=encode(order)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        need(not path.is_symlink() and path.read_bytes()==raw,'daily-dispatch-immutable-conflict');return timing.ref(path)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,path)
        except FileExistsError:need(not path.is_symlink() and path.read_bytes()==raw,'daily-dispatch-immutable-conflict')
        directory=os.open(str(path.parent),os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return timing.ref(path)


def validate(order_ref, root, *, _seen=()):
    order=timing.pinned(order_ref);need(order.get('kind')==KIND,'daily-dispatch-order-invalid')
    need(Path(order_ref['path'])==canonical_path(root,order['dispatch_id']),'daily-dispatch-canonical-path-required')
    expected=build(order['offer'],order['company_config'],origin=order['origin'],resumed_from=order['resumed_from'],_seen=_seen)
    need(order==expected,'daily-dispatch-order-not-derived');return order


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='verb',required=True)
    a=sub.add_parser('prepare');a.add_argument('--root',required=True);a.add_argument('--offer',required=True);a.add_argument('--companies',default=str(DEFAULT_COMPANIES));a.add_argument('--origin',choices=('fresh','resume'),required=True);a.add_argument('--resumed-from')
    a=sub.add_parser('verify');a.add_argument('--root',required=True);a.add_argument('--order',required=True)
    args=p.parse_args(argv)
    try:
        if args.verb=='prepare':
            result=archive(args.root,timing.ref(args.offer),timing.ref(args.companies),origin=args.origin,resumed_from=timing.ref(args.resumed_from) if args.resumed_from else None)
            print(json.dumps({'order':result,'timing_started':False,'business_actions_performed':False}));return 0
        order=validate(timing.ref(args.order),args.root);print(json.dumps({'valid':True,'dispatch_id':order['dispatch_id'],'scope_sha256':order['scope_sha256'],'origin':order['origin'],'timing_started':False}));return 0
    except (ValueError,OSError,TypeError,KeyError) as e:print(json.dumps({'ok':False,'error':str(e)}));return 2

_policy_original_build=build
def build(*args,**kwargs):
    import execution_timing as timing
    with timing.company_policy_command():return _policy_original_build(*args,**kwargs)

if __name__=='__main__':raise SystemExit(main())
