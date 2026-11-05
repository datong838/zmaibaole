#!/usr/bin/env python3
"""Once-only complaint handoff -> rule drafts. No accept/UI/network/model/submit."""
import argparse,fcntl,hashlib,json,os,re,sys,tempfile,time
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import deterministic_analysis as rules
import classification_policy as policy
import case_memory
# Preload actual pure validators before recording the code graph.
import draft_inspection,recent_other_history,normal_paging,normal_review_body
PROJECT=case_memory.SKILL.parents[1]
need=policy.need
VERSION='complaint-rule-batch-producer-v1'
def ref(p):return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()}
def raw(r):
    need(type(r) is dict and set(r)=={'path','sha256'},'producer-reference-required');p=Path(r['path'])
    need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'producer-reference-canonical')
    b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'producer-reference-changed');return b
def doc(r):return json.loads(raw(r))
def syncdir(p):
    fd=os.open(p,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def write(p,b):
    with Path(p).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    syncdir(Path(p).parent);return ref(p)
def immutable(p,value):return write(p,(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
def collect(value,found):
    if isinstance(value,dict):
        if {'path','sha256'}<=set(value) and isinstance(value['path'],str) and re.fullmatch('[a-f0-9]{64}',str(value['sha256'])):
            path=value['path']
            if not Path(path).is_absolute():
                need(re.fullmatch(r'evidence/[a-f0-9]{64}\.json',path) is not None,'producer-relative-kb-reference-invalid');path=str(case_memory.DEFAULT_MEMORY.resolve()/path)
            r={'path':path,'sha256':value['sha256']}
            if path in found:need(found[path]==r,'producer-conflicting-dependency');return
            b=raw(r);found[path]=r
            try:collect(json.loads(b),found)
            except (UnicodeDecodeError,json.JSONDecodeError):pass
            return
        for name,sha in value.items():
            if name.endswith('_sha256') and re.fullmatch('[a-f0-9]{64}',str(sha)):
                other='source' if name=='src_sha256' else name[:-7];path=value.get(other)
                if isinstance(path,str) and Path(path).is_absolute():collect({'path':path,'sha256':sha},found)
        for item in value.values():collect(item,found)
    elif isinstance(value,list):
        for item in value:collect(item,found)
def codes():
    paths={Path(__file__).resolve(),Path(rules.__file__).resolve(),Path(policy.__file__).resolve()}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if not name:continue
        p=Path(name).resolve()
        if p.suffix=='.py' and ((p.is_relative_to(PROJECT/'skills') and p.parent.name=='scripts') or (p.parent==D and p.name in ('public_analysis_producer.py','deterministic_analysis.py','classification_policy.py','workflow.py'))):paths.add(p)
    return [ref(p) for p in sorted(paths)]
def prepare(handoff):
    h=doc(handoff);need(h.get('kind')=='complaint-execution-handoff-v1' and h.get('phase')=='analyze' and h.get('response_kind')=='complaint-analysis-batch-response-v1','producer-only-complaint-analysis')
    root=Path(h['root']);need(root.is_absolute() and root.resolve()==root and h['company'].get('root')==str(root),'producer-original-company-root')
    order=doc(h['order']);need(order.get('workflow')=='negative-review-complaints' and h['company'] in order.get('companies',[]) and h['company'].get('skipped') is False,'producer-original-order-company')
    ledger=ref(root/'state.json');state=doc(ledger);need(state.get('company')==h['company']['company'] and str(state.get('groupid'))==h['company']['groupid'] and state.get('mode')=='draft-only' and state.get('browser_backend')=='local-dom-bridge','producer-original-ledger-identity')
    orders=h.get('orders');need(isinstance(orders,list) and orders and len({x['review_key'] for x in orders})==len(orders),'producer-nonempty-analysis-orders-required')
    deps={handoff['path']:handoff,ledger['path']:ledger};collect(h,deps)
    for item in orders:
        key=item['review_key'];row,snapshot=rules.current(state,key)
        need(item.get('submit_enabled') is False and item.get('review')==state['tasks'][key]['review'] and item.get('snapshot_sha256')==snapshot['sha256'] and item.get('categories')==list(policy.CATEGORIES),'producer-original-review-order')
        raw(item['inspection_operation']);collect(snapshot,deps)
    # The KB read path validates all stored source/result observations, not a model.
    kb=case_memory.DEFAULT_MEMORY/'complaint-cases.jsonl';kbref=ref(kb);collect(kbref,deps)
    records=case_memory.read_records()
    for record in records:
        for field in ('source_ref','result_ref'):collect(record[field],deps)
    return h,state,ledger,[deps[k] for k in sorted(deps)]
def validate_output(root,state,analysis):
    key=analysis['review_key'];effective=state
    if analysis['category']=='其他':effective,_=rules.history_state(root,state,key,analysis['provenance']['inputs'].get('history'))
    policy.validate(effective,key,analysis)
    draft_inspection.validate_analysis(root,effective,key,analysis)

def reuse(handoff,out):
    receipt=doc(ref(out/'receipt.json'));need(receipt.get('kind')=='local-semantic-producer-receipt-v1' and receipt.get('handoff')==handoff and receipt.get('accept_called') is False and receipt.get('producer_method')==VERSION,'producer-prior-receipt-binding')
    raw(handoff);raw(receipt['ledger']);need(receipt['code']==codes(),'producer-code-changed')
    for r in receipt['dependencies']+receipt['code']+receipt['outputs']:raw(r)
    response=doc(receipt['response']);need(set(response)=={'kind','request','analyses'} and response['kind']=='complaint-analysis-batch-response-v1' and response['request']==handoff and response['analyses'] and response['analyses']==receipt['analyses'],'producer-prior-output-binding')
    need(doc(ref(out/'intent.json'))['handoff']==handoff,'producer-prior-intent-binding')
    h=doc(handoff);state=doc(receipt['ledger']);need([doc(r)['review_key'] for r in response['analyses']]==[x['review_key'] for x in h['orders']],'producer-prior-analysis-set')
    for r in response['analyses']:validate_output(h['root'],state,doc(r))
    return {'status':'ready','response':receipt['response'],'receipt':ref(out/'receipt.json')}
def execute(handoff,out):
    out=Path(out);need(out.is_absolute() and out.resolve()==out and not any(p.is_symlink() for p in (out,*out.parents)),'producer-output-canonical')
    if out.exists():
        need((out/'receipt.json').is_file(),'producer-partial-outcome-unknown-no-replay')
        return reuse(handoff,out)
    # Parent waiting state is read only; no accept, mutation or transport call.
    h,state,ledger,dependencies=prepare(handoff);code=codes();started=time.clock_gettime(time.CLOCK_MONOTONIC)
    out.mkdir(parents=True,exist_ok=False);syncdir(out.parent)
    with (out/'claim.lock').open('x') as claim:
        fcntl.flock(claim,fcntl.LOCK_EX|fcntl.LOCK_NB)
        intent=immutable(out/'intent.json',{'kind':'complaint-rule-producer-once-v1','handoff':handoff,'ledger':ledger,'dependencies':dependencies,'code':code,'at':time.time()})
        try:
            frozen=[];origins=[];(out/'inputs').mkdir()
            for r in dependencies:
                b=raw(r);target=out/'inputs'/(r['sha256']+'.bin')
                snapshot=ref(target) if target.exists() else write(target,b)
                need(snapshot['sha256']==r['sha256'],'producer-snapshot-hash');frozen.append(snapshot);origins.append({'original':r,'snapshot':snapshot})
            analyses=[]
            for i,item in enumerate(h['orders']):
                a=rules.produce(h['root'],state,item['review_key'],item['inspection_operation'],item.get('recent_other_history'))
                validate_output(h['root'],state,a)
                analyses.append(immutable(out/('analysis-'+str(i+1)+'.json'),a))
            response=immutable(out/'response.json',{'kind':h['response_kind'],'request':handoff,'analyses':analyses})
            need(codes()==code,'producer-code-graph-changed')
            for r in dependencies+code:raw(r)
            receipt={'kind':'local-semantic-producer-receipt-v1','producer_method':VERSION,'handoff':handoff,'ledger':ledger,'response':response,'analyses':analyses,'dependencies':frozen,'input_origins':origins,'code':code,'outputs':analyses+[response],'accept_called':False,'model_used':False,'intent':intent,'clock_contract':'system-clock-gettime-CLOCK_MONOTONIC-v1','elapsed_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-started}
            return {'status':'ready','response':response,'receipt':immutable(out/'receipt.json',receipt)}
        except BaseException as error:
            immutable(out/'exception.json',{'kind':'deterministic-complaint-analysis-exception-v1','code':str(error),'intent':intent,'accept_called':False,'automatic_replay_allowed':False});raise

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--handoff',required=True);p.add_argument('--handoff-sha256',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args()
    try:result=execute({'path':a.handoff,'sha256':a.handoff_sha256},Path(a.out_dir));rc=0
    except (ValueError,KeyError,OSError,TypeError) as e:result={'status':'exception_handoff','reason':{'kind':'deterministic-complaint-analysis-exception-v1','code':str(e)},'accept_called':False};rc=2
    print(json.dumps(result,ensure_ascii=False));return rc
if __name__=='__main__':raise SystemExit(main())
