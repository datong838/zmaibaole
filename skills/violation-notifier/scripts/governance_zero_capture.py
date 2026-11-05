"""Isolated proposed double-zero source assembler. Public saved evidence only; no UI."""
import argparse,json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
import governance_capture as common
import governance_dom as g
import governance_detail as d
import center_reconciliation as center
nav=d.nav;need=g.need
KIND='governance-zero-capture-manifest-v1';SCHEMA='governance-public-dom-zero-capture-v1'
PROFILE='governance-independent-analysis-records-zero-v1'

def observed(ref,job,tab,window,path):
    raw=d.document(ref);need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==tab,'zero-source-tab-conflict')
    current=nav.context([{'tabs':[raw['tab']]}],tab,job['groupid']);need(current.get('windowId')==window and urlsplit(current['url']).path==path and raw['tree'].get('url')=='https://life.douyin.com'+path,'zero-source-window-route-conflict')
    ns=g.nodes(raw['tree']);nav.identity(raw['tree'],job['identity']);need(not any(any(t in n.get('name','') for t in ('扫码登录','风险验证','安全验证','账号异常')) for n in ns),'zero-source-risk-stop')
    at=datetime.fromisoformat(raw['observed_at']);need(at.utcoffset() is not None,'zero-source-aware-time-required')
    if 'navigation_fingerprint' in raw:need(raw['navigation_fingerprint']==nav.tag(job),'zero-source-fingerprint-conflict')
    return raw

def settled_center_zero(pages_ref,query_ref,job_ref,job,tab,window,query_final,*,center_observation):
    """Saved no-input observation after the confirmed date-query prefix.
    Never rewrites the query or treats an earlier positive chart as zero.
    """
    path=Path(query_ref['path']).resolve().with_name('center-pages.json')
    need(Path(pages_ref['path'])==path,'zero-center-pages-canonical-journal')
    pages=d.document(pages_ref);refs=pages.get('center_refs');observations=pages.get('observations')
    need(pages.get('fingerprint')==nav.tag(job) and pages.get('tab_id')==tab and pages.get('approved_version')==nav.VERSION and pages.get('business_progress_changed')is False,'zero-center-pages-scope-conflict')
    need(pages.get('phase')=='open-date' and pages.get('calls')==[] and pages.get('pages')==[] and pages.get('center_public_pages')==[] and pages.get('center_zero')is True and pages.get('center_pages_complete')is True,'zero-center-pages-no-input-complete-zero-required')
    need(not any(pages.get(k) for k in ('unknown_intent','settling_exhausted','read_only_settling','needs_changed_tree','hold','last_error')),'zero-center-pages-unresolved')
    need(isinstance(refs,list) and len(refs)==1 and observations==refs and pages.get('last_observation')==refs[0],'zero-center-pages-single-observation')
    need(pages.get('query_job_binding')=={'kind':'governance-query-job-binding-v1','job':job_ref,'fingerprint':nav.tag(job),'tab_id':tab,'query_state_path':str(path),'window_id':window},'zero-center-pages-original-job-binding')
    need(Path(refs[0]['path'])==path.parent/'center-pages-evidence'/'0000.json','zero-center-pages-canonical-observation')
    need(refs==[center_observation],'zero-center-pages-original-artifact-conflict')
    d.document(center_observation) # Exact engine artifact SHA, never a fresh hash replacement.
    raw=observed(center_observation,job,tab,window,g.CENTER)
    need(raw['tab']==query_final['tab'] and datetime.fromisoformat(raw['observed_at'])>=datetime.fromisoformat(query_final['observed_at']),'zero-center-pages-after-query-scope-time')
    return center.center_zero(raw['tree'],start=job['start'],end_exclusive=job['end_exclusive']),refs

def query(ref,job,tab,window,path,*,center_pages=None,job_ref=None,center_observation=None):
    q=d.document(ref);need(q.get('fingerprint')==nav.tag(job) and q.get('tab_id')==tab and q.get('approved_version')==nav.VERSION and q.get('business_progress_changed') is False,'zero-query-scope-conflict')
    need(not q.get('unknown_intent') and not q.get('settling_exhausted') and not q.get('read_only_settling') and not q.get('needs_changed_tree') and not q.get('hold'),'zero-query-unresolved')
    refs=q.get('observations');need(isinstance(refs,list) and refs and q.get('last_observation')==refs[-1],'zero-query-observations-incomplete')
    raws=[observed(r,job,tab,window,path) for r in refs];calls=q.get('calls');need(isinstance(calls,list) and calls and all(c.get('state')=='confirmed' for c in calls),'zero-query-original-calls-not-confirmed')
    skip=None
    if 'preselected_record_range_reconciliation' in q:
        import preselected_record_range_recovery as preselected_range
        need(path==g.RECORDS,'zero-preselected-skip-records-only');skip=preselected_range.verify_continuation(q,job)
    phase='open-date';plan=g.QueryPlan(job['start'],job['end_exclusive']);index=-1
    for call_index,call in enumerate(calls):
        if skip is not None and call_index==skip['original_call_count']:
            need(phase=='select-end','zero-preselected-original-phase-conflict');phase=skip['next_phase']
        need(call['before'] in refs,'zero-query-call-before-not-in-original-observations');next_index=refs.index(call['before']);need(next_index>index,'zero-query-call-order-invalid');index=next_index
        before=raws[index];step=plan.next(before['tree'],{'phase':phase});expected={**step['command'],'tabId':tab};need(call.get('command')==expected,'zero-query-command-not-derived-from-original-phase')
        expected_condition={'month_delta':step['expected_month_delta']} if step.get('month_navigation') else None
        need(call.get('postcondition')==expected_condition,'zero-query-postcondition-conflict');d.reply_matches(expected,call.get('result',{}),before);phase=step['next_phase']
    need(index<len(refs)-1,'zero-query-post-action-observation-required');final=raws[-1]
    if path==g.CENTER:
        need(phase=='verify-date' and q.get('phase')=='profile-required' and not q.get('pages') and q.get('waiting_for')=='analysis-all-reasons-actual-view-profile-required','zero-center-query-not-final')
        step=plan.next(final['tree'],{'phase':phase});need(step.get('hold')=='analysis-all-reasons-actual-view-profile-required','zero-center-query-range-not-applied')
        if center_pages is None:result=center.center_zero(final['tree'],start=job['start'],end_exclusive=job['end_exclusive'])
        else:
            result,later=settled_center_zero(center_pages,ref,job_ref,job,tab,window,final,center_observation=center_observation);refs=refs+later
    else:
        need(phase=='collect-page' and q.get('phase')=='capture-complete','zero-record-query-not-final');pages=q.get('pages');need(isinstance(pages,list) and len(pages)==1 and pages[0].get('observation')==q['last_observation'],'zero-record-query-single-empty-observation-required')
        result=g.records_page(final['tree'],start=job['start'],end_exclusive=job['end_exclusive']);need(result.get('empty_result',{}).get('schema')=='governance-records-explicit-empty-v1' and result['total']==0 and pages==[{**result,'observation':q['last_observation']}] and g.complete_pages(pages)==q.get('rows')==[],'zero-record-query-derived-page-conflict')
        audit=q.get('records_zero_reconciliation')
        if audit:
            original=d.document(audit['original_journal']);origin=Path(ref['path']).resolve();archive=origin.parent/(origin.name+'.records-zero-original-'+audit['original_journal']['sha256']+'.json')
            need(Path(audit['original_journal']['path'])==archive and audit.get('kind')=='confirmed-query-explicit-empty-readonly-v1' and audit.get('state')=='explicit-empty-query-result-verified' and audit.get('fresh_observation')==q['last_observation'],'zero-record-reconciliation-binding-conflict')
            need(original.get('phase')=='collect-page' and original.get('settling_exhausted') is True and original.get('calls')==calls and original.get('pages')==[] and all(original.get(k)==q.get(k) for k in ('fingerprint','tab_id','approved_version','business_progress_changed')),'zero-record-reconciliation-original-changed')
            pending=original.get('read_only_settling',{});last=original.get('last_observation');need(pending.get('checks')==pending.get('max_checks')==5 and pending.get('original_call_index')==len(calls)-1 and pending.get('last_observation')==last and pending.get('reason')=='governance-all-tab-not-unique' and audit.get('original_last_observation')==last and audit.get('original_call_index')==len(calls)-1,'zero-record-reconciliation-original-stop-unreviewed')
            old=observed(last,job,tab,window,path);need(g.records_page(old['tree'],start=job['start'],end_exclusive=job['end_exclusive'])==result,'zero-record-reconciliation-result-changed')
    return q,result,refs

def sources(refs):
    need(set(refs)in ({'job','center_query','records_query'},{'job','center_query','records_query','center_pages','center_observation'}),'zero-source-refs-invalid');job=d.document(refs['job']);nav.scope(job)
    rq=d.document(refs['records_query']);last=d.document(rq['last_observation']);tab=rq['tab_id'];window=last['tab']['windowId']
    cq,cz,cr=query(refs['center_query'],job,tab,window,g.CENTER,center_pages=refs.get('center_pages'),job_ref=refs['job'],center_observation=refs.get('center_observation'));rq,rz,rr=query(refs['records_query'],job,tab,window,g.RECORDS)
    return {'job':job,'center_query':cq,'records_query':rq,'center_zero':cz,'center_observation':cr[-1],'records_zero':rz,'tab_id':tab,'window_id':window,'rawrefs':cr+rr}

def derive_profile(refs):
    v=sources(refs)
    return {'schema':PROFILE,'source_refs':refs,'company':v['job']['company'],'groupid':str(v['job']['groupid']),'identity':v['job']['identity'],'tab_id':v['tab_id'],'window_id':v['window_id'],'start':v['job']['start'],'end_exclusive':v['job']['end_exclusive'],'center_zero':v['center_zero'],'records_empty':v['records_zero']['empty_result'],'headers':v['records_zero']['headers'],'date_selector':v['records_zero']['date_selector'],'scope':'saved-public-dom-derived-double-zero; no screenshot or notification acceptance'}

def inputs(m):
    need(set(m)=={'kind','inputs'} and m.get('kind')==KIND,'zero-manifest-kind-invalid');refs=m['inputs'];need(set(refs)in ({'job','center_query','records_query','profile'},{'job','center_query','records_query','center_pages','center_observation','profile'}),'zero-manifest-inputs-invalid');source_refs={k:v for k,v in refs.items() if k!='profile'};v=sources(source_refs);profile=d.document(refs['profile']);need(profile==derive_profile(source_refs),'zero-profile-derived-content-conflict');return v

def assemble(m,manifest_ref=None):
    v=inputs(m);job=v['job'];refs=m['inputs'];cz=v['center_zero'];rq=v['records_query'];rawrefs=[]
    for r in v['rawrefs']:
        if r not in rawrefs:rawrefs.append(r)
    times=[datetime.fromisoformat(d.document(r)['observed_at']) for r in rawrefs];basis='independent-explicit-date-filtered-analysis-and-complete-records-zero-v1'
    result={'capture_schema':SCHEMA,'profile_revision':PROFILE,'company':job['company'],'groupid':str(job['groupid']),'source':'local-dom-bridge','url':'https://life.douyin.com'+g.RECORDS+'?groupid='+str(job['groupid']),'observed_at':max(times).isoformat(),'account_verified':True,'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive'],'analysis':{'start':job['start'],'end_exclusive':job['end_exclusive'],'scope':'全部','total':0,'rows':[],'all_pages_read':True,'filters_verified':True,'all_reasons_read':True,'basis':basis},'records':{'start':job['start'],'end_exclusive':job['end_exclusive'],'scope':'全部','total':0,'rows':[],'unread_only':False,'all_pages_read':True,'filters_verified':True},'source_evidence_refs':{**refs,'center_observation':v['center_observation'],'records_observation':rq['last_observation'],'raw_observations':rawrefs},'source_contract':{'basis':basis,'analysis_zero':cz,'records_zero':v['records_zero']['empty_result'],'detail_not_applicable':True,'all_notice_details_verified':False,'platform_mutations':False}}
    if manifest_ref is not None:result['capture_manifest']=manifest_ref
    return result

def validate(path):
    value=d.document(d.ref(path));r=value.get('capture_manifest');need(isinstance(r,dict),'governance-capture-manifest-reference-required');expected=assemble(d.document(r),r);need(value==expected,'governance-capture-derived-payload-mismatch');return value

def build(manifest_path,out):
    r=d.ref(manifest_path);m=d.document(r);value=assemble(m,r);out=Path(out).resolve()
    if out.exists():need(d.document(d.ref(out))==value,'zero-capture-output-conflict')
    else:d.exclusive(out,value)
    validate(out);return value

def prepare(job,center_query,records_query,profile_out,manifest_out,*,center_pages=None,center_observation=None):
    refs={k:d.ref(v) for k,v in {'job':job,'center_query':center_query,'records_query':records_query}.items()}
    if center_pages is not None:
        refs['center_pages']=center_pages if isinstance(center_pages,dict) else d.ref(center_pages)
        pages=d.document(refs['center_pages'])
        if center_observation is None:
            values=pages.get('center_refs');need(isinstance(values,list) and len(values)==1,'zero-center-pages-single-artifact-required');center_observation=values[0]
        d.document(center_observation);refs['center_observation']=center_observation
    else:need(center_observation is None,'zero-center-artifact-without-pages')
    profile=derive_profile(refs);p=Path(profile_out).resolve()
    if p.exists():need(d.document(d.ref(p))==profile,'zero-profile-output-conflict')
    else:d.exclusive(p,profile)
    m={'kind':KIND,'inputs':{**refs,'profile':d.ref(p)}};inputs(m);out=Path(manifest_out).resolve()
    if out.exists():need(d.document(d.ref(out))==m,'zero-manifest-output-conflict')
    else:d.exclusive(out,m)
    return d.ref(out)

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare')
    for k in ('job','center-query','records-query','profile-out','manifest-out'):a.add_argument('--'+k,required=True)
    a.add_argument('--center-pages')
    a=sp.add_parser('build');a.add_argument('--manifest',required=True);a.add_argument('--out',required=True);a=sp.add_parser('verify');a.add_argument('--capture',required=True);args=p.parse_args()
    if args.verb=='prepare':value=prepare(args.job,args.center_query,args.records_query,args.profile_out,args.manifest_out,center_pages=args.center_pages);print(json.dumps({'ok':True,'manifest':value,'ui_used':False}));return
    value=build(args.manifest,args.out) if args.verb=='build' else validate(args.capture);print(json.dumps({'ok':True,'total':value['records']['total'],'basis':value['analysis']['basis'],'ui_used':False}))
if __name__=='__main__':main()
