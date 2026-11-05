"""Observed review-list loading is not a count/result. Pure metadata recovery."""
import argparse,copy,fcntl,hashlib,json,os,re,uuid
from pathlib import Path
from datetime import datetime,timezone
KIND='verified-review-filter-loading-recovery-v1'
def need(ok,code):
    if not ok:raise ValueError(code)
def now():return datetime.now(timezone.utc).isoformat()
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def ref(p):
    p=Path(p);need(p.is_absolute() and p.is_file() and not p.is_symlink(),'filter-loading-ref-path');return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def doc(r):
    p=Path(r['path']);need(ref(p)==r,'filter-loading-evidence-changed');return json.loads(p.read_bytes())
def immutable(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    try:
        with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    except FileExistsError:need(p.read_bytes()==raw,'filter-loading-artifact-conflict')
    return ref(p)
def is_loading(tree):
    from dom_evidence import nodes,unique
    ns=list(nodes(tree));spinners=[n for n in ns if 'loading-cihppn' in n.get('attributes',{}).get('class','').split()]
    if not spinners:return is_header_pending(tree)
    spinner=unique(spinners,'review-filter-loading-not-unique');need(spinner.get('tag')=='img' and spinner.get('name')=='' and not spinner.get('children') and spinner.get('attributes',{}).get('class')=='loading-cihppn','review-filter-loading-shape')
    pager=unique([n for n in ns if spinner in n.get('children',[])],'review-filter-loading-pager');need(pager.get('tag')=='div' and pager.get('attributes',{}).get('class')=='pagination-GXvAPk','review-filter-loading-pager')
    listing=unique([n for n in ns if pager in n.get('children',[])],'review-filter-loading-list');need(listing.get('tag')=='div' and 'commentList-hkujq4' in listing.get('attributes',{}).get('class','').split(),'review-filter-loading-list');return True

def is_header_pending(tree):
    """Observed header-only shell is pending, never a verified result/zero.

    Store linkage may already be established before the result count arrives.
    Its exact all-store selector must pass; no rows/count/empty result is inferred.
    """
    from dom_evidence import nodes,unique
    ns=list(nodes(tree))
    if any(n.get('name','')in ('暂无评价','暂无数据','暂无相关评价')for n in ns):return False
    if any(re.fullmatch(r'(?:评价\s*)?已筛选\s*(\d+)\s*条',n.get('name',''))for n in ns):return False
    lists=[n for n in ns if 'commentList-hkujq4' in n.get('attributes',{}).get('class','').split()]
    if len(lists)!=1:return False
    listing=lists[0]
    if listing.get('tag')!='div' or set(listing.get('attributes',{}).get('class','').split())!={'commentList-hkujq4','isPC-WBFQKh','commentList-C8RoYO'}:return False
    children=listing.get('children',[])
    if len(children)!=1:return False
    header=children[0]
    if header.get('tag')!='div' or set(header.get('attributes',{}).get('class','').split())!={'header-sQid1u','commentListHeader-jKdTh_'}:return False
    cells=header.get('children',[])
    if [n.get('name')for n in cells]!=['评价','门店','顾客','操作'] or [n.get('attributes',{}).get('class')for n in cells]!=['comment-bBq56G','poi-vEQ_4m','custom-JQlfcA','operator-yoWSV8']:return False
    labels=[n for n in ns if n.get('attributes',{}).get('class')=='byted-tab-bar-item-label']
    names=[n.get('name','')for n in labels]
    if len(names)!=2 or names.count('全部评价 0')!=1:return False
    stores=[re.fullmatch(r'全部门店 (0|[1-9]\d*)',name)for name in names if name!='全部评价 0']
    if len(stores)!=1 or stores[0]is None:return False
    if int(stores[0][1])>0:
        from dom_evidence import all_store_scope
        try:all_store_scope(tree)
        except ValueError:return False
    active=[n for n in ns if 'byted-tab-bar-item-active' in n.get('attributes',{}).get('class','').split()]
    return len(active)==1 and active[0].get('name')=='全部评价 0' and active[0].get('children')==[next(n for n in labels if n.get('name')=='全部评价 0')]

def validate_window_anchor(job,s,window):
    anchors={c.get('result',{}).get('windowId')for c in s['calls']if c.get('command')=={'op':'activate','tabId':s['tab_id']}}
    if anchors:need(anchors=={window},'filter-loading-original-window');return
    # Normal DOM path no longer emits activate; use its pinned post-switch fact.
    proof=doc(s['switch_read_recovery']);facts=proof.get('facts',{});proof_job=doc(proof['job'])
    need(proof.get('kind')=='verified-company-switch-read-recovery-v1' and proof.get('ui_used')is False and proof.get('new_mutations')==0 and proof_job['work_order_id']==job['work_order_id'] and proof_job['identity_baseline']==job['identity_baseline'] and facts.get('tab_id')==s['tab_id'] and facts.get('window_id')==window and str(facts.get('groupid'))==str(job['groupid']) and any(c.get('stage')=='switch' and c.get('identity')==job['identity_baseline'] and str(c.get('groupid'))==str(job['groupid'])for c in s.get('checkpoints',[])),'filter-loading-original-window')

def validate_pending_store_scope(tree):
    """A placeholder permits waiting only, never store/zero certification."""
    from dom_evidence import nodes,unique,all_store_scope
    try:return all_store_scope(tree)
    except ValueError as error:
        if str(error)!='nondefault-store-scope':raise
    need(is_header_pending(tree),'filter-pending-store-not-established')
    scope=unique([n for n in nodes(tree)if n.get('attributes',{}).get('id')=='CommentPoi_select'],'store-scope-unverified')
    need(scope.get('tag')=='div' and scope.get('attributes',{}).get('class')=='poiSelect-XbcLu_' and scope.get('name')=='按省市 0家门店','filter-pending-store-placeholder')
    placeholders=[n for n in nodes(tree)if n.get('attributes',{}).get('class')=='detail-indicator__placeholder_4a1a7']
    need(len(placeholders)==1 and placeholders[0].get('name')=='0家门店' and placeholders[0].get('tag')=='div' and placeholders[0].get('children')==[],'filter-pending-store-placeholder')
    return False # Explicitly no verified all-store scope.

def validate_filter_values(tree,date_range):
    from dom_evidence import review_filter_fields
    fields=review_filter_fields(tree)
    need(fields['评价时间'].get('attributes',{}).get('value')==date_range['start']+' ~ '+date_range['end'],'filter-date-unverified')
    for label in ('评价类型','评价来源','评价状态'):
        need(fields[label].get('attributes',{}).get('value')=='全部','nondefault-review-filter:'+label)

def validate_original(job,s,scope):
    from dom_evidence import identity,all_store_scope,verified_review_filter,nodes,context,VERSION
    from readonly_tick_snapshot import decode
    need(s.get('phase')=='verifyFilter' and s.get('state')=='running' and s.get('last_error',{}).get('code')==s['last_error'].get('message')=='page-count-unverified','filter-loading-original-error');need(s.get('identity_contract')==job.get('identity_contract')=='merchant-v2' and s.get('work_order_id')==job.get('work_order_id') and s.get('company')==job.get('company') and str(s.get('groupid'))==str(job['groupid']) and s.get('date_range')=={k:job['date_range'][k] for k in ('start','end')},'filter-loading-original-scope');need(s.get('identity')==job['identity_baseline']==job['known_company_identities'][str(job['groupid'])],'filter-loading-original-identity');need(not any(s.get(k) for k in ('exportPending','downloadPending','result')) and s['calls'] and all(c.get('state')=='confirmed' for c in s['calls']),'filter-loading-input-unknown')
    last=s['calls'][-1];cmd=last.get('command',{});clicked=last.get('result',{}).get('clicked',{});need(last.get('phase')=='pageEnd' and cmd.get('op')=='click' and cmd.get('kind')=='filter' and cmd.get('tabId')==s['tab_id'] and clicked.get('selector')==cmd.get('locator',{}).get('value') and clicked.get('name')==str(int(job['date_range']['end'][-2:])),'filter-loading-original-end-confirmed')
    window=scope['scope']['windowId'];decode(scope,s['tab_id'],window);before=context(scope['before'],s['tab_id'],job['groupid']);after=context(scope['after'],s['tab_id'],job['groupid']);need(before['url']==after['url'] and before['url'].split('?')[0]=='https://life.douyin.com/p/life_comment/management' and scope['ping'].get('version')==VERSION and scope['ping'].get('safety')=='DOM-only','filter-loading-scope-version');validate_window_anchor(job,s,window);need(scope['tree']==doc(s['last_tree']) and scope['tree']['url']=='https://life.douyin.com/p/life_comment/management','filter-loading-original-tree');validate_pending_store_scope(scope['tree'])
    identity(scope['tree'],s['identity'])
    need(is_loading(scope['tree']),'filter-loading-original-not-loading');validate_filter_values(scope['tree'],job['date_range'])
    try:verified_review_filter(scope['tree'],job['date_range'])
    except ValueError as e:need(str(e)=='page-count-unverified','filter-loading-original-not-loading')
    else:raise ValueError('filter-loading-original-not-loading')

def recover(job_path,expected_sha,scope_ref):
    job_path=Path(job_path);job=json.loads(job_path.read_bytes());p=Path(job['workflow_path']);need(p.is_absolute() and not p.is_symlink() and Path(job['work_order_path'])==job_path,'filter-loading-canonical-job');raw=p.read_bytes();s=json.loads(raw)
    if hashlib.sha256(raw).hexdigest()!=expected_sha:
        proof=s.get('review_filter_loading_recovery');need(proof and doc(proof)['original']['sha256']==expected_sha,'filter-loading-original-sha');verify_recovered(s,proof);return {'state':'already-reconciled','journal':ref(p),'proof':proof}
    scope=doc(scope_ref);need(Path(scope_ref['path']).parent==p.parent/'bridge-evidence','filter-loading-scope-origin');validate_original(job,s,scope);d=p.parent/'review-filter-loading-recovery'/expected_sha;original=immutable(d/'original-journal.json',raw);jobref=immutable(d/'original-job.json',job_path.read_bytes());proof={'kind':KIND,'at':now(),'original':original,'job':jobref,'scope':scope_ref,'tree':s['last_tree'],'next_phase':'verifyFilter','ui_used':False,'new_mutations':0};pr=immutable(d/'proof.json',encoded(proof));new=copy.deepcopy(s);new.setdefault('resolved_errors',[]).append({**new.pop('last_error'),'resolved_at':proof['at'],'next_phase':'verifyFilter','recovery_proof':pr});new.update(review_filter_loading_recovery=pr,updated_at=proof['at']);verify_recovered(new,pr);need(p.read_bytes()==raw,'filter-loading-concurrent-change');tmp=p.with_name(p.name+'.filter-loading-'+uuid.uuid4().hex);immutable(tmp,encoded(new));os.replace(tmp,p);return {'state':'reconciled','journal':ref(p),'proof':pr,'phase':'verifyFilter','ui_used':False}
def verify_recovered(current,proof_ref):
    p=doc(proof_ref);need(p.get('kind')==KIND and p.get('next_phase')=='verifyFilter' and p.get('ui_used') is False and p.get('new_mutations')==0,'filter-loading-proof-policy');old=doc(p['original']);job=doc(p['job']);validate_original(job,old,doc(p['scope']));need(p['tree']==old['last_tree'],'filter-loading-tree-binding');expected=copy.deepcopy(old);expected.setdefault('resolved_errors',[]).append({**expected.pop('last_error'),'resolved_at':p['at'],'next_phase':'verifyFilter','recovery_proof':proof_ref});expected.update(review_filter_loading_recovery=proof_ref,updated_at=p['at']);need(current==expected,'filter-loading-recovery-delta');return p

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work-order',type=Path,required=True);ap.add_argument('--original-sha256',required=True);ap.add_argument('--scope-observation',type=Path,required=True);ap.add_argument('--scope-sha256',required=True);a=ap.parse_args();job=json.loads(a.work_order.read_bytes());p=Path(job['workflow_path'])
    with p.with_name('.bridge-execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(recover(a.work_order,a.original_sha256,{'path':str(a.scope_observation),'sha256':a.scope_sha256}),ensure_ascii=False))
if __name__=='__main__':main()
