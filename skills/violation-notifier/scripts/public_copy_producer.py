#!/usr/bin/env python3
"""Stdlib-only typed violation copy. No AI, browser, accept, send or attest."""
import argparse,hashlib,json,sys,time
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import public_copy_template as templates
ORDER_FIELDS=('notice_id','subject','reason','object_name','actions','effectiveness_status')
def need(ok,code):
 if not ok:raise ValueError(code)
def ref(p):return {'path':str(Path(p).resolve()),'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()}
def raw(r):
 need(type(r) is dict and set(r)=={'path','sha256'},'producer-reference-required');p=Path(r['path'])
 need(p.is_absolute() and p.resolve()==p and not any(q.is_symlink() for q in (p,*p.parents)),'producer-reference-canonical')
 b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'producer-reference-changed');return b
def doc(r):return json.loads(raw(r))
def refs(v,found):
 if isinstance(v,dict):
  if set(v)=={'path','sha256'}:raw(v);found[v['path']]=v
  else:
   for value in v.values():refs(value,found)
 elif isinstance(v,list):
  for value in v:refs(value,found)
def immutable(p,value):
 with Path(p).open('x',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 return ref(p)
def prepare(handoff):
 request=doc(handoff);need(request.get('kind')=='violation-execution-handoff-v1' and request.get('phase')=='copy' and request.get('response_kind')=='violation-copy-response-v1','producer-only-violation-copy')
 root=Path(request['root']);need(root.is_absolute() and request['ledger']['path']==str(root/'state.json'),'producer-ledger-root')
 state=doc(request['ledger']);source=doc(request['source']);batch=state['batches'][request['batch']]
 need(batch['source']['sha256']==request['source']['sha256'] and raw(batch['source'])==raw(request['source']) and batch['records']==source['records']['rows'] and batch['total']==len(batch['records']) and batch['total']>0,'producer-source-records-binding')
 need(source['company']==state['company'] and str(source['groupid'])==str(state['groupid']) and source['identity']==state['identity'] and source.get('account_verified') is True and (source['start'],source['end_exclusive'])==(batch['start'],batch['end_exclusive']),'producer-source-identity-range')
 need(not batch.get('send_jobs') and not batch.get('copy'),'producer-not-fresh-copy')
 expected=[{**{k:r[k] for k in ORDER_FIELDS},'action_details':r.get('action_details',[]),'disposal_stage_text':r.get('disposal_stage_text',''),'public_recommendation':r['public_recommendation']} for r in batch['records']]
 order=request['copy_order'];need(order['batch']==request['batch'] and order['source_sha256']==request['source']['sha256'] and order['items']==expected,'producer-original-copy-order')
 value=templates.document(request['source']['sha256'],batch['records']);dependencies={handoff['path']:handoff,batch['source']['path']:batch['source']};refs(request,dependencies)
 return request,value,list(dependencies.values())
def execute(handoff,out):
 started=time.monotonic();request,value,dependencies=prepare(handoff);code=[ref(Path(__file__)),ref(Path(templates.__file__))]
 out=Path(out);need(out.is_absolute() and out.resolve()==out and not any(p.is_symlink() for p in (out,*out.parents)),'producer-output-canonical')
 if out.exists():
  receipt=doc(ref(out/'receipt.json'));need(receipt['handoff']==handoff and receipt['ledger']==request['ledger'] and receipt['accept_called'] is False and receipt['producer_method']==templates.VERSION and receipt['dependencies']==dependencies,'producer-prior-binding')
  for item in receipt['dependencies']+receipt['code']+receipt['outputs']:raw(item)
  response=doc(receipt['response']);need(response=={'kind':request['response_kind'],'request':handoff,'copy':ref(out/'copy.json')} and doc(response['copy'])==value and receipt['code']==code,'producer-prior-output-changed')
  return {'status':'ready','response':receipt['response'],'receipt':ref(out/'receipt.json')}
 out.mkdir(parents=True,exist_ok=False);copy_ref=immutable(out/'copy.json',value);response_ref=immutable(out/'response.json',{'kind':request['response_kind'],'request':handoff,'copy':copy_ref})
 # No acceptance: ensure all inputs/code are still the same before declaring ready.
 for item in dependencies+code:raw(item)
 receipt={'kind':'local-semantic-producer-receipt-v1','producer_method':templates.VERSION,'handoff':handoff,'ledger':request['ledger'],'response':response_ref,'dependencies':dependencies,'code':code,'outputs':[copy_ref,response_ref],'accept_called':False,'elapsed_seconds':time.monotonic()-started}
 return {'status':'ready','response':response_ref,'receipt':immutable(out/'receipt.json',receipt)}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--handoff',required=True);p.add_argument('--handoff-sha256',required=True);p.add_argument('--out-dir',required=True);a=p.parse_args()
 try:result=execute({'path':a.handoff,'sha256':a.handoff_sha256},Path(a.out_dir));rc=0
 except (ValueError,KeyError,OSError,TypeError) as error:result={'status':'exception_handoff','reason':{'kind':'deterministic-violation-copy-exception-v1','code':str(error)},'accept_called':False};rc=2
 print(json.dumps(result,ensure_ascii=False));return rc
if __name__=='__main__':raise SystemExit(main())
