#!/usr/bin/env python3
"""Resume the original bounded batch with explicitly approved source-proof owner."""
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,hashlib,json,re,sys
from pathlib import Path
from types import FunctionType,ModuleType
import normal_case_journey as j
import history_workspace as h
import normal_source_proof_session as P
import dom_evidence
p=j.p;A=p.A;C=A.export_parse_session
KIND='supervisor-normal-source-proof-run-admission-v1'

def loaded_guard(modules=(sys.modules[__name__],p,p.n,A,p.body,C,P,dom_evidence,h,j,j.c,j.results,h.orders_api,h.workflow,j.results.result,h.memory_api)):
    # Existing parser signer once, then explicit actual pure script graph.
    parser=C._token(A._load_export_uncached);entries=[]
    for module in modules:
        items=[]
        for name,value in sorted(vars(module).items()):
            if isinstance(value,FunctionType):items.append((name,C._function(value)))
            elif isinstance(value,type):
                methods=[]
                for key,fn in sorted(vars(value).items()):
                    if isinstance(fn,(staticmethod,classmethod)):fn=fn.__func__
                    if isinstance(fn,FunctionType):methods.append((key,C._function(fn)))
                    elif isinstance(fn,property):methods.append((key,tuple(C._function(f) if f else None for f in (fn.fget,fn.fset,fn.fdel))))
                items.append((name,value,tuple(methods)))
            elif isinstance(value,ModuleType):items.append((name,('module-alias',value)))
            elif name.isupper():items.append((name,type(value),repr(value)))
        entries.append((module,tuple(items)))
    return (parser,tuple(entries))

def code_refs():
    files={Path(module.__file__).resolve() for module in loaded_guard.__defaults__[0]}
    files.update(Path(token[1][0]) for token in C._token(A._load_export_uncached).values())
    return {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}

def admission_inputs(root,source_sha):
    root=Path(root);j.need(root.is_absolute() and root.resolve()==root and not any(q.is_symlink() for q in (root,*root.parents)),'source-proof-original-root')
    j.need(type(source_sha) is str and re.fullmatch('[0-9a-f]{64}',source_sha),'source-proof-source-sha')
    state=h.load(root);j.need(source_sha in state['sources'],'source-proof-source-not-owned');entry=state['sources'][source_sha]
    refs=entry['inputs'];j.need(set(refs)=={'job','source','envelope','profile'} and refs['source']['sha256']==source_sha,'source-proof-original-inputs')
    job=h.document(refs['job']);receipt_ref={'path':job['source_receipt'],'sha256':job['source_receipt_sha256']};receipt=h.document(receipt_ref)
    six={**refs,'receipt':receipt_ref,'xlsx':{'path':receipt['source'],'sha256':receipt['src_sha256']}}
    for reference in six.values():P._bytes(reference)
    scope={'root':str(root),'source_sha256':source_sha,'company':job['company'],'groupid':str(job['groupid']),'identity':job['identity'],'start':job['start'],'end_exclusive':job['end_exclusive']}
    return six,scope

def proposal(root,source_sha,boundary_ref):
    import openpyxl  # Initialize reviewed parser modules before fixed graph admission.
    refs,scope=admission_inputs(root,source_sha)
    return {'kind':KIND,'approved':False,'reviewer_role':'supervisor','refs':refs,'scope':scope,'code_refs':code_refs(),'release_boundary':boundary_ref,'no_old_code_pin_rewrite':True,'requires_closed_clean_handoff':True}

def run_bound(root,source_sha,steps,admission_ref):
    j.need(type(steps) is int and 1<=steps<=25,'case-batch-bounded-steps')
    import openpyxl
    grant=json.loads(P._bytes(admission_ref));refs,scope=admission_inputs(root,source_sha)
    j.need(grant.get('kind')==KIND and grant.get('approved') is True and grant.get('reviewer_role')=='supervisor' and grant.get('no_old_code_pin_rewrite') is True and grant.get('requires_closed_clean_handoff') is True,'source-proof-supervisor-admission')
    j.need(grant.get('refs')==refs and grant.get('scope')==scope and grant.get('code_refs')==code_refs(),'source-proof-admission-current-graph')
    boundary=json.loads(P._bytes(grant['release_boundary']))
    j.need(boundary.get('kind')=='supervisor-four-cases-closed-source-update-boundary-v1' and boundary.get('accepted_for_source_update') is True and boundary.get('read_cases_completed')==4,'source-proof-closed-handoff-required')
    j.need(p.source_proof_session is P,'source-proof-central-hook-not-loaded')
    providers=((C,'_token'),(C,'_function'),(P,'_function'),(P,'_api_token'))
    with C.owner_session():
        with P.owner_session(refs,scope,[{'path':path,'sha256':sha} for path,sha in grant['code_refs'].items()],loaded_guard,providers=providers):
            return j.batch(root,source_sha,steps)

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True);ap.add_argument('--source-sha256',required=True);ap.add_argument('--steps',type=int,default=25);ap.add_argument('--admission',required=True);ap.add_argument('--admission-sha256',required=True);a=ap.parse_args(argv)
    out=run_bound(a.root,a.source_sha256,a.steps,{'path':a.admission,'sha256':a.admission_sha256});print(json.dumps(out,ensure_ascii=False));return out
if __name__=='__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e)},ensure_ascii=False));raise SystemExit(2)
