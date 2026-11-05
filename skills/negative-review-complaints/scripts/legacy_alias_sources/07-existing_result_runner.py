#!/usr/bin/env python3
"""Pinned existing-complaint result reader. No submit, screenshot, or send actions."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,fcntl,hashlib,json,sys,os,re
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import normal_observation as normal,result_observation as result,workflow
import prepare_result_orders as orders_api
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/chrome-dom-export/scripts'))
import bridge
LEGACY=PROJECT/'work/live-acceptance/complaints/live-profile'
need=workflow.require
ref=orders_api.ref
document=orders_api.document

def manifest_inputs(m,*,historical_complete=False):
    need(m.get('kind')=='existing-result-inspection-manifest-v1' and set(m)-{'kind','root','inputs','review_key','completed_operation','completed_pages'}==set(),'result-runner-manifest-invalid')
    need(Path(m['root']).is_absolute() and set(m['inputs'])=={'job','source','profile','envelope','page','orders'},'result-runner-explicit-refs-required')
    v={k:document(r) for k,r in m['inputs'].items()};job,source,profile,envelope=v['job'],v['source'],v['profile'],v['envelope'];orders=v['orders']
    need(profile.get('text_schema') in (None,'public-visible-text-v2'),'result-runner-text-schema-invalid')
    need(orders.get('kind')=='existing-complaint-result-orders-v1' and orders.get('submission_enabled') is False and orders.get('send_enabled') is False,'result-runner-readonly-orders-required')
    need(orders['inputs']=={k:m['inputs'][k] for k in ('job','source','envelope','profile')},'result-runner-order-inputs-mismatch')
    need(normal.joined(job,envelope,profile,job['source_receipt'],job['source_receipt_sha256'])==source,'result-runner-source-not-reproducible')
    need(orders.get('company')==job['company']==source['company'] and str(orders['groupid'])==str(job['groupid'])==str(source['groupid']) and orders['range']=={k:source[k] for k in ('start','end_exclusive')},'result-runner-company-range-mismatch')
    matched=[o for o in orders['orders'] if o.get('review_key')==m['review_key']];need(len(matched)==1,'result-runner-order-not-unique');order=matched[0]
    rows=[r for r in source['rows'] if source['groupid']+':'+r['review_id']==m['review_key']];need(len(rows)==1,'result-runner-source-review-not-unique');row=rows[0]
    need(order['snapshot_sha256']==m['inputs']['source']['sha256'] and order['card_selector']==row['dom_selector'] and order['source_tuple']=={k:row[k] for k in ('review_id','store','customer','text','stars','date')} and order['original_action']==row['action'] and order['original_action'] in ('查看投诉结果','投诉审核中') and order['click_kind']=='complaint-read' and order['allowed_actions']==['查看投诉结果','投诉审核中'] and order['never_click']==['投诉','再次投诉','提交'],'result-runner-order-review-mismatch')
    normal.context(v['page'],job['groupid']);need(v['page']['tab']['tabId']>0,'result-runner-tab-required')
    ledger=workflow.load(Path(m['root']));need(ledger.get('company')==job['company'] and str(ledger.get('groupid'))==str(job['groupid']) and ledger.get('browser_backend')=='local-dom-bridge','result-runner-ledger-company-backend-mismatch')
    if ledger.get('workspace_kind')=='negative-review-appeal-history-only-v1':
        from history_workspace import load as load_history
        ledger=load_history(m['root'])
        need(ledger['identity']==job['identity'] and ledger['history_range']['start']<=job['start']<job['end_exclusive']<=ledger['history_range']['end_exclusive'],'result-runner-history-identity-range-mismatch')
    task=ledger.get('tasks',{}).get(m['review_key']);need(task is not None,'result-runner-review-not-ingested')
    if ledger.get('workspace_kind')=='negative-review-appeal-history-only-v1':need(task.get('action')==row['action'] and all(task.get('review',{}).get(k)==row.get(k) for k in ('review_id','store','customer','text','stars','date','product')),'result-runner-history-task-tuple-mismatch')
    if not m.get('completed_operation') and not historical_complete:need(task.get('latest_snapshot',{}).get('sha256')==m['inputs']['source']['sha256'],'result-runner-ledger-current-snapshot-mismatch')
    v['_ledger']=ledger
    return v,order,row

def runtime_identity(tree,job):
    nodes=normal.flatten(tree['root']);cards=[n for n in nodes if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')]
    if cards:
        normal.public_identity(tree,job['identity']);return {'runtime_full_identity_rechecked':True,'runtime_identity_basis':'complete-visible-UserCard'}
    titles=[n for n in nodes if any(c.startswith(('src-components-HeaderV2-components-Profile-index-module__title--','src-components-HeaderV3-components-Profile-index-module__title--')) for c in n.get('attributes',{}).get('class','').split()) and n.get('name')==job['identity']['provider']]
    need(len(titles)==1,'result-runner-current-provider-trigger-not-unique');return {'runtime_full_identity_rechecked':False,'runtime_identity_basis':'visible-provider-trigger-and-pinned-source-full-identity'}

def normal_page(page,v,order,row,*,action=True,identity=True,facts=None):
    job,profile=v['job'],v['profile'];tab,tree=normal.context(page,job['groupid']);need(not drawers(page),'result-runner-normal-page-has-open-drawer');need(tab['tabId']==v['page']['tab']['tabId'],'result-runner-tab-changed')
    normal.navigation_probe(tree,job,text_schema=profile.get('text_schema'))
    if identity:
        value=runtime_identity(tree,job)
        if facts is not None:facts.update(value)
    card=normal.one(normal.flatten(tree['root']),{'selector':order['card_selector']},'existing-result-card');nodes=normal.flatten(card)
    for field,cl in [('store','poiName-W9HDFV'),('customer','nickName-wB7fZf'),('text','text-Hl9jZe')]:need(normal.review_field_literal(normal.one(nodes,{'attributes':{'class':cl}},field),field,text_schema=profile.get('text_schema'))==row[field],'result-runner-current-review-changed:'+field)
    if not action:return None
    actions=[n for n in nodes if not n.get('children') and n.get('name')==order['original_action'] and n.get('attributes',{}).get('class')=='button-vhqEd7 isHighlight-DoxxP4'];need(len(actions)==1 and actions[0].get('disabled') is not True,'result-runner-action-not-unique');return actions[0]

def click(tab,selector):return {'op':'click','tabId':tab,'kind':'complaint-read','locator':{'by':'selector','value':selector}}
def clicked(reply,command,*,close=False):
    n=reply.get('clicked',{});need(reply.get('kind')=='complaint-read' and n.get('selector')==command['locator']['value'] and n.get('disabled') is not True,'result-runner-click-reply-unverified')
    need(n.get('attributes',{}).get('class')==('byted-drawer-close-icon' if close else 'button-vhqEd7 isHighlight-DoxxP4') and (n.get('name')=='' if close else n.get('name') in ('查看投诉结果','投诉审核中')),'result-runner-click-reply-unreviewed')

def ledger_record(root,key,path):
    # A dedicated history root shares the exact reader, never the daily writer.
    if workflow.load(Path(root)).get('workspace_kind')=='negative-review-appeal-history-only-v1':
        from history_workspace import record_result
        return record_result(root,key,path)
    with workflow.locked(root) as root:
        s=workflow.load(root);current=s['tasks'][key].get('result');p=workflow.read(path)
        if not current or {k:v for k,v in current.items() if k!='evidence'}!=p:workflow.record_result(root,s,key,path)
        workflow.export_xlsx(root,workflow.load(root))

def verify_complete(s,m,v,order,row):
    need(s.get('state')=='complete' and s.get('manifest')==m,'result-runner-complete-manifest-mismatch')
    before=document(s['normal_before']);action=normal_page(before,v,order,row);need(s['open_command']==click(before['tab']['tabId'],action['selector']),'result-runner-complete-open-mismatch');
    if s.get('open_reply'):clicked(s['open_reply'],s['open_command'])
    else:need(s.get('open_reconciliation')=={'method':'exact-public-result-drawer','drawer':s['drawer']},'result-runner-open-outcome-unverified')
    parsed=result.parse(v['job'],document(s['drawer']),row,text_schema=v['profile'].get('text_schema'));parsed['snapshot_sha256']=m['inputs']['source']['sha256'];need(parsed==document(s['result_input']),'result-runner-complete-result-changed')
    if s.get('close_reply'):clicked(s['close_reply'],s['close_command'],close=True)
    else:need(s.get('close_reconciliation')=={'method':'absent-drawer-exact-normal-page','normal_after':s['normal_after']},'result-runner-close-outcome-unverified')
    after=document(s['normal_after']);need(not drawers(after),'result-runner-complete-drawer-still-open');normal_page(after,v,order,row,action=False,identity=False)
    need(s['close_command']==close_command(document(s.get('drawer_before_close',s['drawer']))),'result-runner-complete-close-mismatch')
    return parsed

def drawers(page):return [n for n in normal.flatten(page['tree']['root']) if 'byted-drawer-dialog-show' in n.get('attributes',{}).get('class','').split()]
def close_command(page):
    ds=drawers(page);need(len(ds)==1,'result-runner-single-drawer-required');scope=normal.flatten(ds[0]);need(any(n.get('name')=='投诉评价' and not n.get('children') for n in scope),'result-runner-drawer-title-unverified');icons=[n for n in scope if n.get('attributes',{}).get('class')=='byted-drawer-close-icon'];need(len(icons)==1 and icons[0].get('disabled') is not True,'result-runner-close-not-unique');return click(page['tab']['tabId'],icons[0]['selector'])

def adopt_completed(m,v,order,row):
    old=document(m['completed_operation']);need(old.get('state')=='complete' and old.get('review_key')==m['review_key'] and old.get('source_sha256')==m['inputs']['source']['sha256'] and old.get('submission_enabled') is False,'result-runner-legacy-complete-scope-invalid')
    pages=m.get('completed_pages');need(isinstance(pages,dict) and set(pages)=={'normal_before','drawer','normal_after'},'result-runner-legacy-complete-pages-required')
    parsed=result.parse(v['job'],document(pages['drawer']),row,text_schema=v['profile'].get('text_schema'));parsed['snapshot_sha256']=m['inputs']['source']['sha256'];need(parsed==old.get('result'),'result-runner-legacy-result-mismatch')
    state={'state':'complete','manifest':m,'normal_before':pages['normal_before'],'drawer':pages['drawer'],'normal_after':pages['normal_after'],'open_command':old['open_command'],'open_reply':old['open_reply'],'close_command':old['close_command'],'close_reply':old['close_reply']}
    # Immutable parsed result is referenced in the old ledger evidence, or written
    # only into the new adoption directory by the caller; legacy files stay intact.
    return state,parsed

def legacy_guard(key,index,declared,history=None):
    known=index.get('adopted_legacy',[]);known=set((r['path'],r['sha256']) for r in known)
    audit=[]
    for path in LEGACY.glob('*result-operation.json'):
        value=workflow.read(path)
        if value.get('review_key')!=key:continue
        r=ref(path)
        if (r['path'],r['sha256']) in known:continue
        if history and history[0].get('workspace_kind')=='negative-review-appeal-history-only-v1':
            from history_workspace import verify_prior_for_legacy
            audit.append(verify_prior_for_legacy(history[0],key,r,history[1]));continue
        need(declared==r and value.get('state')=='complete','result-runner-existing-legacy-operation-requires-explicit-complete-adoption')
    return audit

def immutable_write(path,value):
    path=Path(path)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())

def recovered_result(path,v,row,snapshot,current):
    expected=workflow.read(path);matches=[]
    for candidate in path.parent.glob('*-drawer.json'):
        page=workflow.read(candidate)
        try:
            parsed=result.parse(v['job'],page,row,text_schema=v['profile'].get('text_schema'));parsed['snapshot_sha256']=snapshot
            if parsed==expected:matches.append(ref(candidate))
        except (ValueError,KeyError):continue
    need(len(matches)==1,'result-runner-orphan-result-needs-unique-original-drawer')
    need(all(current[k]==expected[k] for k in ('review_key','snapshot_sha256','status','visible_text','original_complaint')),'result-runner-orphan-result-current-drawer-changed')
    return matches[0]

def previous_complete(index,folder,m):
    snapshot=index['snapshot_sha256'];need(re.fullmatch(r'[a-f0-9]{64}',snapshot) is not None,'result-runner-active-source-invalid')
    path=folder/snapshot/'operation.json';need(Path(index['operation']['path']).resolve()==path.resolve(),'result-runner-active-path-invalid');s=workflow.read(path)
    need(s.get('state')=='complete' and s['manifest']['root']==m['root'] and s['manifest']['review_key']==m['review_key'],'result-runner-prior-source-operation-unfinished')
    v,o,row=manifest_inputs(s['manifest'],historical_complete=True);verify_complete(s,s['manifest'],v,o,row)
    current=ref(path)
    if current!=index['operation']:
        index.setdefault('completed_pointer_recoveries',[]).append({'old':index['operation'],'verified_complete':current});index['operation']=current
    return index

@contextmanager
def operation_lock(root,key):
    folder=Path(root)/'existing-result-operations'/hashlib.sha256(key.encode()).hexdigest();folder.mkdir(parents=True,exist_ok=True)
    with (folder/'.lock').open('a') as f:fcntl.flock(f,fcntl.LOCK_EX);yield folder

def tick(m,request=None,record=None):
    request=request or (lambda c:bridge.request(c,timeout=50));record=record or ledger_record
    v,order,row=manifest_inputs(m);root=Path(m['root']).resolve();key=m['review_key'];snapshot=m['inputs']['source']['sha256']
    with operation_lock(root,key) as folder:
        index_path=folder/'active.json';index=workflow.read(index_path) if index_path.exists() else {};prior_audit=legacy_guard(key,index,m.get('completed_operation'),history=(v.get('_ledger',{}),row))
        path=folder/snapshot/'operation.json';path.parent.mkdir(exist_ok=True)
        if index and index['snapshot_sha256']!=snapshot:index=previous_complete(index,folder,m)
        if path.exists():s=workflow.read(path);need(s.get('manifest')==m,'result-runner-original-manifest-required')
        else:
            if m.get('completed_operation'):
                s,parsed=adopt_completed(m,v,order,row);p=path.parent/'adopted-result.json';workflow.atomic(p,parsed);s['result_input']=ref(p);verify_complete(s,m,v,order,row)
            else:
                previous=v.get('_ledger',{}).get('tasks',{}).get(key,{}).get('result') or {};need(not(previous.get('status') in ('accepted','rejected') and previous.get('snapshot_sha256')==snapshot),'result-runner-resolved-ledger-result-requires-complete-adoption')
                s={'state':'preflight','manifest':m,'submission_enabled':False,'send_enabled':False,'created_at':workflow.now(),'reads':0}
            workflow.atomic(path,s)
        if prior_audit:
            need(s.get('verified_history_priors',prior_audit)==prior_audit,'result-runner-history-prior-binding-changed')
            s['verified_history_priors']=prior_audit
        if index and index['snapshot_sha256']==snapshot and s.get('state')=='complete' and index['operation']!=ref(path):index=previous_complete(index,folder,m)
        def persist():
            workflow.atomic(path,s);workflow.atomic(index_path,{**index,'snapshot_sha256':snapshot,'operation':ref(path),'adopted_legacy':index.get('adopted_legacy',[])+([m['completed_operation']] if m.get('completed_operation') and m['completed_operation'] not in index.get('adopted_legacy',[]) else [])})
        persist()
        def call(command):
            r=request(command);need(r.get('ok') is True,'result-runner-bridge-failed:'+str(r.get('error')));return r['result']
        def page(label):
            windows=call({'op':'tabs'});tabs=[t for w in windows for t in w.get('tabs',[]) if t.get('tabId')==v['page']['tab']['tabId']];need(len(tabs)==1,'result-runner-explicit-tab-not-unique');p={'tab':tabs[0],'tree':call({'op':'tree','tabId':tabs[0]['tabId']}),'observed_at':datetime.now(timezone.utc).isoformat()};normal.context(p,v['job']['groupid']);existing=[int(f.name.split('-',1)[0]) for f in path.parent.glob('[0-9]*-*.json') if f.name.split('-',1)[0].isdigit()];s['reads']=max([s.get('reads',0)]+existing)+1;out=path.parent/(str(s['reads']).zfill(4)+'-'+label+'.json');immutable_write(out,p);return p,ref(out)
        try:
            phase=s['state']
            if phase=='complete':verify_complete(s,m,v,order,row)
            elif phase=='preflight':
                call({'op':'activate','tabId':v['page']['tab']['tabId']});p,r=page('normal-before');facts={};action=normal_page(p,v,order,row,facts=facts);s.update(**facts,normal_before=r,open_command=click(p['tab']['tabId'],action['selector']),state='open-ready')
            elif phase=='open-ready':
                p,r=page('normal-before');facts={};action=normal_page(p,v,order,row,facts=facts);s.update(facts);need(s['open_command']==click(p['tab']['tabId'],action['selector']),'result-runner-open-target-changed');s['normal_before']=r;s['state']='open-unknown';persist();reply=call(s['open_command']);clicked(reply,s['open_command']);s.update(open_reply=reply,state='opened')
            elif phase in ('open-unknown','opened'):
                p,r=page('drawer');parsed=result.parse(v['job'],p,row,text_schema=v['profile'].get('text_schema'));parsed['snapshot_sha256']=snapshot
                # A lost open reply is resolved only by the exact current drawer;
                # never click the original action twice.
                if phase=='open-unknown':s['open_reconciliation']={'method':'exact-public-result-drawer','drawer':r}
                inp=path.parent/'result-input.json'
                if inp.exists():r=recovered_result(inp,v,row,snapshot,parsed)
                else:immutable_write(inp,parsed)
                s.update(drawer=r,result_input=ref(inp),state='record-ready')
            elif phase=='record-ready':record(root,key,Path(s['result_input']['path']));s['state']='close-ready'
            elif phase=='close-ready':
                p,r=page('drawer-before-close');parsed=result.parse(v['job'],p,row,text_schema=v['profile'].get('text_schema'));parsed['snapshot_sha256']=snapshot;old=document(s['result_input']);need(all(parsed[k]==old[k] for k in ('review_key','snapshot_sha256','status','visible_text','original_complaint')),'result-runner-result-changed-before-close');s.update(drawer_before_close=r,close_command=close_command(p),state='close-unknown');persist();reply=call(s['close_command']);clicked(reply,s['close_command'],close=True);s.update(close_reply=reply,state='verify-closed')
            elif phase in ('close-unknown','verify-closed'):
                p,r=page('normal-after');need(not drawers(p),'result-runner-close-not-yet-observed');normal_page(p,v,order,row,action=False,identity=False)
                if phase=='close-unknown':s['close_reconciliation']={'method':'absent-drawer-exact-normal-page','normal_after':r}
                s.update(normal_after=r,state='complete',completed_at=workflow.now());verify_complete(s,m,v,order,row)
            else:need(False,'result-runner-phase-invalid')
            s.pop('error',None);persist()
        except (ValueError,KeyError,OSError,RuntimeError) as e:s['error']=str(e);persist();raise
        return {'ok':True,'state':s['state'],'operation':str(path),'review_key':key,'result':document(s['result_input']) if s.get('result_input') else None,'ui_used':phase!='complete'}

def prepare(root,paths,key,out,completed=None,pages=None):
    m={'kind':'existing-result-inspection-manifest-v1','root':str(Path(root).resolve()),'inputs':{k:ref(p) for k,p in paths.items()},'review_key':key}
    if completed:m.update(completed_operation=ref(completed),completed_pages={k:ref(p) for k,p in pages.items()})
    manifest_inputs(m);out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():need(workflow.read(out)==m,'result-runner-manifest-exists-different')
    else:workflow.atomic(out,m)
    return m

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare');a.add_argument('--root',required=True);a.add_argument('--review-key',required=True);a.add_argument('--out',required=True)
    for k in ('job','source','profile','envelope','page','orders'):a.add_argument('--'+k,required=True)
    a.add_argument('--completed-operation')
    for k in ('normal-before','drawer','normal-after'):a.add_argument('--completed-'+k)
    a=sp.add_parser('run');a.add_argument('--manifest',required=True);a.add_argument('--steps',type=int,choices=range(1,11),default=1)
    args=p.parse_args()
    try:
        if args.verb=='prepare':
            pages={k:getattr(args,'completed_'+k) for k in ('normal_before','drawer','normal_after')};need((bool(args.completed_operation) and all(bool(x) for x in pages.values())) or (not args.completed_operation and not any(pages.values())),'result-runner-complete-adoption-all-pages-required');m=prepare(args.root,{k:getattr(args,k) for k in ('job','source','profile','envelope','page','orders')},args.review_key,args.out,args.completed_operation,pages);out={'ok':True,'manifest':str(Path(args.out).resolve()),'ui_used':False}
        else:
            m=workflow.read(args.manifest)
            for _ in range(args.steps):
                out=tick(m)
                if out['state']=='complete':break
        print(json.dumps(out,ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
