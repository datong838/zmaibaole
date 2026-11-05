#!/usr/bin/env python3
"""Source-bound complaint options inspection: open once, read, cancel. No form input or submission."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,hashlib,json,re
from pathlib import Path
import existing_result_runner as shared
import normal_observation as normal
import workflow
need=workflow.require
ref=shared.ref
document=shared.document
OPTIONS=['脏话辱骂','未到店消费','侵权','广告引流','无关内容','错评错点','同行刷评','员工差评','热点事件攻击','批量差评','恶意勒索','其他']
LEGACY=shared.PROJECT/'work/live-acceptance/complaints'
CATEGORY={'脏话辱骂':('脏话辱骂',),'错评错点':('错评错点',),'批量差评':('批量差评',),'同行刷屏':('同行刷评','热点事件攻击'),'其他':('其他',)}

def inputs(m,historical=False):
    need(m.get('kind')=='complaint-draft-inspection-manifest-v1' and set(m)<= {'kind','root','review_key','inputs','completed_operation','completed_pages'},'draft-inspection-manifest-invalid')
    need(Path(m['root']).is_absolute() and set(m['inputs'])=={'job','source','profile','envelope','page'},'draft-inspection-pinned-inputs-required')
    v={k:document(r) for k,r in m['inputs'].items()};job=v['job'];source=v['source']
    need(normal.joined(job,v['envelope'],v['profile'],job['source_receipt'],job['source_receipt_sha256'])==source,'draft-inspection-source-not-reproducible')
    rows=[x for x in source['rows'] if source['groupid']+':'+x['review_id']==m['review_key']];need(len(rows)==1 and rows[0]['action']=='投诉','draft-inspection-new-complaint-required');row=rows[0]
    normal.context(v['page'],job['groupid']);s=workflow.load(Path(m['root']));need(s['company']==source['company']==job['company'] and str(s['groupid'])==str(source['groupid'])==str(job['groupid']) and s['browser_backend']=='local-dom-bridge','draft-inspection-ledger-scope-mismatch')
    t=s.get('tasks',{}).get(m['review_key']);need(t is not None,'draft-inspection-review-not-ingested')
    if not historical:need(t['latest_snapshot']['sha256']==m['inputs']['source']['sha256'],'draft-inspection-current-source-mismatch')
    return v,{'card_selector':row['dom_selector'],'original_action':'投诉'},row

def normal_page(p,v,o,row):
    shared.normal_page(p,v,o,row,action=False)
    card=normal.one(normal.flatten(p['tree']['root']),{'selector':o['card_selector']},'draft-card')
    nodes=[n for n in normal.flatten(card) if n.get('name')=='投诉' and not n.get('children') and n.get('attributes',{}).get('class')=='button-vhqEd7' and n.get('disabled') is not True]
    need(len(nodes)==1,'draft-inspection-action-not-unique');return nodes[0]

def cmd(p,selector,kind):return {'op':'click','tabId':p['tab']['tabId'],'kind':kind,'locator':{'by':'selector','value':selector}}
def clicked(reply,c):
    n=reply.get('clicked',{});need(reply.get('kind')==c['kind'] and n.get('selector')==c['locator']['value'] and n.get('disabled') is not True,'draft-inspection-click-reply-invalid')
    need((c['kind']=='complaint-draft' and n.get('name')=='投诉' and n.get('attributes',{}).get('class')=='button-vhqEd7') or (c['kind']=='dismiss' and n.get('name')=='取消' and n.get('role')=='button' and n.get('tag')=='button'),'draft-inspection-click-reply-unreviewed')

def options(p,job):
    normal.context(p,job['groupid']);ds=shared.drawers(p);need(len(ds)==1,'draft-inspection-single-drawer-required');ns=normal.flatten(ds[0])
    need(sum(n.get('name')=='投诉评价' and not n.get('children') for n in ns)==1,'draft-inspection-title-invalid')
    groups=[n for n in ns if n.get('attributes',{}).get('class')=='byted-radio-group byted-radio-group-type-radio byted-radio-group-size-md'];need(len(groups)==1,'draft-inspection-options-group-invalid')
    labels=[n for n in normal.flatten(groups[0]) if n.get('tag')=='label'];need([n.get('name') for n in labels]==OPTIONS and all(n.get('attributes',{}).get('class')=='byted-radio byted-radio-size-md' for n in labels),'draft-inspection-options-changed-or-selected')
    for label in labels:
        ch=label.get('children',[]);need(len(ch)==2 and ch[0].get('attributes',{}).get('class')=='byted-radio-circle byted-radio-circle-size-md' and ch[1].get('attributes',{}).get('class')=='byted-radio-label' and ch[1].get('name')==label['name'],'draft-inspection-option-shape-invalid')
    fields=[n for n in ns if n.get('tag')=='textarea'];need(len(fields)==1 and fields[0].get('name')=='0 / 300' and fields[0].get('attributes',{}).get('value','')=='' and any('最少30字' in n.get('name','') for n in ns),'draft-inspection-reason-not-empty-or-limit-changed')
    buttons=[n for n in ns if n.get('role')=='button' and n.get('tag')=='button'];need([n.get('name') for n in buttons]==['取消','提交审核'] and all(n.get('disabled') is not True for n in buttons),'draft-inspection-footer-unreviewed')
    return {'options':OPTIONS,'draft_utf16_min':30,'draft_utf16_max':300,'platform_selected_in_ui':False,'reason_filled_in_ui':False,'submitted':False},cmd(p,buttons[0]['selector'],'dismiss')

def verify_state(s,m,v,o,row):
    need(s.get('state')=='complete' and s.get('manifest')==m,'draft-inspection-not-complete')
    before=document(s['normal_before']);action=normal_page(before,v,o,row);need(s['open_command']==cmd(before,action['selector'],'complaint-draft'),'draft-inspection-open-mismatch')
    if s.get('open_reply'):clicked(s['open_reply'],s['open_command'])
    else:need(s.get('open_reconciliation')==s['form'],'draft-inspection-open-outcome-unknown')
    form=document(s['form']);need(form['tab']['tabId']==v['page']['tab']['tabId'],'draft-inspection-form-tab-changed')
    f,close=options(form,v['job']);need(f==s['facts'] and close==s['close_command'],'draft-inspection-form-changed')
    if s.get('close_reply'):clicked(s['close_reply'],s['close_command'])
    else:need(s.get('close_reconciliation')==s['normal_after'],'draft-inspection-close-outcome-unknown')
    normal_page(document(s['normal_after']),v,o,row)
    return f

def validate(path,*,root=None,key=None,snapshot=None):
    s=workflow.read(path);m=s['manifest'];v,o,row=inputs(m,historical=True)
    need(root is None or Path(m['root']).resolve()==Path(root).resolve(),'draft-inspection-root-mismatch');need(key is None or m['review_key']==key,'draft-inspection-review-mismatch');need(snapshot is None or m['inputs']['source']['sha256']==snapshot,'draft-inspection-source-mismatch')
    return verify_state(s,m,v,o,row)

def tick(m,request=None):
    v,o,row=inputs(m);snapshot=m['inputs']['source']['sha256'];key=m['review_key'];request=request or (lambda c:shared.bridge.request(c,timeout=50))
    with shared.operation_lock(Path(m['root'])/'draft-inspection',key) as folder:
        index_path=folder/'active.json';index=workflow.read(index_path) if index_path.exists() else {};path=folder/snapshot/'operation.json';path.parent.mkdir(exist_ok=True)
        if index and index['snapshot_sha256']!=snapshot:
            old=Path(index['operation']['path']);need(old.resolve()==(folder/index['snapshot_sha256']/'operation.json').resolve(),'draft-inspection-active-path-mismatch');validate(old,root=m['root'],key=key)
            if index['operation']!=ref(old):
                index.setdefault('completed_pointer_recoveries',[]).append({'old':index['operation'],'verified_complete':ref(old)});index['operation']=ref(old)
        if path.exists():s=workflow.read(path);need(s['manifest']==m,'draft-inspection-original-manifest-required')
        elif m.get('completed_operation'):
            old=document(m['completed_operation']);ps=m['completed_pages'];need(set(ps)=={'normal_before','form','normal_after'} and old.get('state')=='complete' and old.get('review_key')==key and old.get('source_sha256')==snapshot and old.get('submission_enabled') is False and old.get('form_empty') is True and all(old.get(k) is False for k in ('radio_clicked','reason_filled','submitted')),'draft-inspection-adoption-invalid')
            facts,_=options(document(ps['form']),v['job']);s={'state':'complete','manifest':m,**ps,'facts':facts,**{k:old[k] for k in ('open_command','open_reply','close_command','close_reply')},'submission_enabled':False};verify_state(s,m,v,o,row)
        else:
            # A legacy operation for the same review cannot be bypassed by a new manifest.
            legacy=set(Path(m['root']).parent.rglob('draft-inspection/operation.json'))|set(LEGACY.rglob('draft-inspection/operation.json'))
            for oldpath in legacy:
                old=workflow.read(oldpath)
                if old.get('review_key')!=key:continue
                known=False
                if index:
                    prior=document(index['operation']);known=prior.get('state')=='complete' and prior.get('manifest',{}).get('completed_operation')==ref(oldpath)
                need(known,'draft-inspection-existing-operation-needs-explicit-adoption')
            s={'state':'preflight','manifest':m,'submission_enabled':False,'created_at':workflow.now()}
        def persist():workflow.atomic(path,s);workflow.atomic(index_path,{**index,'snapshot_sha256':snapshot,'operation':ref(path)})
        def call(c):
            r=request(c);need(r.get('ok') is True,'draft-inspection-bridge-failed:'+str(r.get('error')));return r['result']
        def page(label):
            windows=call({'op':'tabs'});tabs=[t for w in windows for t in w.get('tabs',[]) if t.get('tabId')==v['page']['tab']['tabId']];need(len(tabs)==1,'draft-inspection-tab-not-unique');p={'tab':tabs[0],'tree':call({'op':'tree','tabId':tabs[0]['tabId']}),'observed_at':workflow.now()};n=max([0]+[int(x.name.split('-',1)[0]) for x in path.parent.glob('[0-9]*-*.json') if x.name.split('-',1)[0].isdigit()])+1;out=path.parent/(str(n).zfill(4)+'-'+label+'.json');shared.immutable_write(out,p);return p,ref(out)
        persist()
        try:
            phase=s['state']
            if phase=='complete':verify_state(s,m,v,o,row)
            elif phase=='preflight':
                call({'op':'activate','tabId':v['page']['tab']['tabId']});p,r=page('normal-before');a=normal_page(p,v,o,row);s.update(normal_before=r,open_command=cmd(p,a['selector'],'complaint-draft'),state='open-ready')
            elif phase=='open-ready':
                p,r=page('normal-before');a=normal_page(p,v,o,row);need(s['open_command']==cmd(p,a['selector'],'complaint-draft'),'draft-inspection-open-target-changed');s.update(normal_before=r,state='open-unknown');persist();reply=call(s['open_command']);clicked(reply,s['open_command']);s.update(open_reply=reply,state='opened')
            elif phase in ('open-unknown','opened'):
                p,r=page('form');facts,close=options(p,v['job']);s.update(form=r,facts=facts,close_command=close,state='close-ready')
                if phase=='open-unknown':s['open_reconciliation']=r
            elif phase=='close-ready':
                p,r=page('form-before-close');facts,close=options(p,v['job']);need(facts==s['facts'] and close==s['close_command'],'draft-inspection-form-changed');s['state']='close-unknown';persist();reply=call(close);clicked(reply,close);s.update(close_reply=reply,state='verify-closed')
            elif phase in ('close-unknown','verify-closed'):
                p,r=page('normal-after');normal_page(p,v,o,row);s.update(normal_after=r,state='complete',completed_at=workflow.now())
                if phase=='close-unknown':s['close_reconciliation']=r
                verify_state(s,m,v,o,row)
            else:need(False,'draft-inspection-phase-invalid')
            s.pop('error',None);persist()
        except (ValueError,KeyError,OSError,RuntimeError) as e:s['error']=str(e);persist();raise
        return {'ok':True,'state':s['state'],'operation':str(path),'facts':s.get('facts'),'ui_used':phase!='complete'}

def validate_analysis(root,s,key,a):
    e=a.get('platform_category_evidence',{});need(isinstance(e.get('inspection_operation'),dict),'draft-inspection-evidence-required');p=e['inspection_operation'];document(p);facts=validate(p['path'],root=root,key=key,snapshot=s['tasks'][key]['latest_snapshot']['sha256'])
    need(e.get('category_label') in CATEGORY.get(a['category'],()) and e['category_label'] in facts['options'],'draft-platform-category-mismatch');need(e.get('platform_selected_in_ui') is False and e.get('reason_filled_in_ui') is False and e.get('submitted') is False,'draft-inspection-no-ui-selection-required')
    length=len(a['draft'].encode('utf-16-le'))//2;need(30<=length<=300,'draft-platform-utf16-length-out-of-range');return facts

def main():
    p=argparse.ArgumentParser(description=__doc__);sp=p.add_subparsers(dest='verb',required=True);a=sp.add_parser('prepare');a.add_argument('--root',required=True);a.add_argument('--review-key',required=True);a.add_argument('--out',required=True)
    for k in ('job','source','profile','envelope','page'):a.add_argument('--'+k,required=True)
    a.add_argument('--completed-operation')
    for k in ('normal-before','form','normal-after'):a.add_argument('--completed-'+k)
    a=sp.add_parser('run');a.add_argument('--manifest',required=True);a.add_argument('--steps',type=int,choices=range(1,9),default=1);a=sp.add_parser('verify');a.add_argument('--operation',required=True);args=p.parse_args()
    try:
        if args.verb=='verify':out={'ok':True,'facts':validate(args.operation),'ui_used':False}
        elif args.verb=='prepare':
            m={'kind':'complaint-draft-inspection-manifest-v1','root':str(Path(args.root).resolve()),'review_key':args.review_key,'inputs':{k:ref(getattr(args,k)) for k in ('job','source','profile','envelope','page')}};ps={k:getattr(args,'completed_'+k) for k in ('normal_before','form','normal_after')};need(bool(args.completed_operation)==all(bool(x) for x in ps.values()) and (args.completed_operation or not any(ps.values())),'draft-inspection-adoption-all-pages-required')
            if args.completed_operation:m.update(completed_operation=ref(args.completed_operation),completed_pages={k:ref(v) for k,v in ps.items()})
            inputs(m);path=Path(args.out).resolve();path.parent.mkdir(parents=True,exist_ok=True)
            if path.exists():need(workflow.read(path)==m,'draft-inspection-manifest-conflict')
            else:shared.immutable_write(path,m)
            out={'ok':True,'manifest':str(path),'ui_used':False}
        else:
            m=workflow.read(args.manifest)
            for _ in range(args.steps):
                out=tick(m)
                if out['state']=='complete':break
        print(json.dumps(out,ensure_ascii=False));return 0
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
