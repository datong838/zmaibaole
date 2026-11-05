#!/usr/bin/env python3
"""Build nonempty, immutable recent Other-result samples. No UI or ledger writes."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,hashlib,json
from datetime import datetime,timedelta
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from zoneinfo import ZoneInfo
ZONE=ZoneInfo('Asia/Shanghai');MODE='sampled-recent-results'
def need(ok,code):
    if not ok:raise ValueError(code)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def evidence(root,ref):
    p=Path(ref.get('path',''));need(p.is_absolute() and not p.is_symlink() and p.is_file(),'sample-history-evidence-path-invalid')
    need(p.resolve().parent==(Path(root).resolve()/'evidence') and p.name==ref.get('sha256','')+'.json','sample-history-evidence-not-owned')
    need(digest(p)==ref.get('sha256'),'sample-history-evidence-hash-mismatch');return read(p)
def item(root,state,key):
    task=state['tasks'][key];result=task.get('result') or {};ref=result.get('evidence');need(isinstance(ref,dict),'sample-history-result-required');r=evidence(root,ref)
    need(r=={k:v for k,v in result.items() if k!='evidence'},'sample-history-result-record-mismatch')
    need(r.get('review_key')==key and r.get('submitted_by_this_workflow') is False,'sample-history-result-key-mismatch')
    source_refs=[v for v in (task.get('snapshot'),task.get('latest_snapshot')) if isinstance(v,dict) and v.get('sha256')==r.get('snapshot_sha256')]
    need(source_refs,'sample-history-source-not-owned');src_ref=source_refs[0];src=evidence(root,src_ref)
    need(src.get('company')==state['company'] and str(src.get('groupid'))==str(state['groupid']) and src.get('source')==state['browser_backend'] and src.get('identity')==state['identity'] and src.get('account_verified') is True,'sample-history-company-identity-mismatch')
    rows=[x for x in src.get('rows',[]) if str(state['groupid'])+':'+x.get('review_id','')==key];need(len(rows)==1,'sample-history-source-review-missing')
    need(all(rows[0].get(k)==task['review'].get(k) for k in ('review_id','store','customer','text','stars','date')),'sample-history-source-review-changed')
    u=urlsplit(r.get('url',''));need(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[str(state['groupid'])] and r.get('source')==state['browser_backend'],'sample-history-result-source-mismatch')
    old=r.get('original_complaint',{});need(old.get('投诉类型')=='其他' and isinstance(old.get('投诉理由'),str) and old['投诉理由'].strip(),'sample-history-not-other-original-text')
    complaint=datetime.fromisoformat(old.get('投诉时间',''));complaint=complaint.replace(tzinfo=ZONE) if complaint.tzinfo is None else complaint.astimezone(ZONE)
    observed=datetime.fromisoformat(r.get('observed_at',''));need(observed.utcoffset() is not None,'sample-history-original-observation-time-required')
    return {'review_key':key,'category':'其他','date':complaint.date().isoformat(),'complaint_at':old['投诉时间'],'text':old['投诉理由'],'observed_at':r['observed_at'],'result':ref,'source':src_ref}
def window_days(p):
    kind=p.get('kind');need(kind in ('recent-other-result-samples-v1','recent-other-result-samples-v2') and p.get('mode')==MODE,'sample-history-mode-invalid')
    days=p.get('window_days',7) if kind=='recent-other-result-samples-v1' else p.get('window_days')
    need(type(days) is int and days in (7,30) and (kind!='recent-other-result-samples-v1' or days==7),'sample-history-window-schema-invalid');return days

def validate(root,state,target,p,*,as_of=None):
    days=window_days(p);day=as_of or datetime.now(ZONE).date();start=(day-timedelta(days=days)).isoformat()
    need(p.get('root')==str(Path(root).resolve()) and p.get('target_review_key')==target and target in state['tasks'],'sample-history-root-target-mismatch')
    need(p.get('company')==state['company'] and str(p.get('groupid'))==str(state['groupid']) and p.get('source')==state['browser_backend'],'sample-history-company-mismatch')
    need(p.get('start')==start and p.get('end_exclusive')==day.isoformat() and p.get('as_of')==day.isoformat(),'sample-history-window-stale')
    assembled=datetime.fromisoformat(p.get('assembled_at',''));need(assembled.utcoffset() is not None and assembled.astimezone(ZONE).date()==day,'sample-history-assembly-time-invalid')
    need(p.get('all_pages_read') is False and p.get('is_exhaustive') is False and p.get('no_history') is False,'sample-history-must-not-claim-exhaustive')
    samples=p.get('items');need(isinstance(samples,list) and samples,'sample-history-empty-use-full-query');seen=set()
    for sample in samples:
        key=sample.get('review_key');need(key in state['tasks'] and key!=target and key not in seen,'sample-history-task-not-owned-or-duplicate');seen.add(key)
        expected=item(root,state,key);need(sample==expected,'sample-history-original-content-changed')
        need(start<=sample['date']<day.isoformat(),'sample-history-outside-window')
        need(datetime.fromisoformat(sample['observed_at'])<=assembled,'sample-history-observed-after-assembly')
    return samples

def build(root,target,out,*,at=None,window_days=30):
    need(type(window_days) is int and window_days in (7,30),'sample-history-window-schema-invalid')
    root=Path(root).resolve();state=read(root/'state.json');at=at or datetime.now(ZONE);need(at.utcoffset() is not None,'sample-history-assembly-time-invalid');day=at.astimezone(ZONE).date();start=(day-timedelta(days=window_days)).isoformat()
    need(state.get('mode')=='draft-only' and state.get('browser_backend')=='local-dom-bridge' and target in state['tasks'],'sample-history-live-root-required')
    samples=[]
    for key,t in state['tasks'].items():
        if key==target or not t.get('result') or t['result'].get('original_complaint',{}).get('投诉类型')!='其他':continue
        value=item(root,state,key)
        if start<=value['date']<day.isoformat():samples.append(value)
    p={'kind':'recent-other-result-samples-v2','window_days':window_days,'mode':MODE,'root':str(root),'target_review_key':target,'company':state['company'],'groupid':str(state['groupid']),'source':state['browser_backend'],'url':'https://life.douyin.com/p/life_comment/management?groupid='+str(state['groupid']),'as_of':day.isoformat(),'start':start,'end_exclusive':day.isoformat(),'assembled_at':at.isoformat(),'all_pages_read':False,'is_exhaustive':False,'no_history':False,'items':samples,'use':'wording-reference-only; original merchant assertions are not verified facts for the new draft'}
    validate(root,state,target,p,as_of=day);out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():
        existing=read(out);validate(root,state,target,existing,as_of=day);need({k:v for k,v in existing.items() if k!='assembled_at'}=={k:v for k,v in p.items() if k!='assembled_at'},'sample-history-output-conflict');return existing
    with out.open('x') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
    return p

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('root','id','out'):ap.add_argument('--'+k,required=True)
    ap.add_argument('--window-days',type=int,choices=(7,30),default=30)
    a=ap.parse_args()
    try:p=build(a.root,a.id,a.out,window_days=a.window_days);print(json.dumps({'ok':True,'items':len(p['items']),'mode':MODE,'schema':p['kind'],'window_days':p['window_days'],'out':str(Path(a.out).resolve()),'sha256':digest(a.out),'ui_used':False},ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
