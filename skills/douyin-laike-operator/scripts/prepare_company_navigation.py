#!/usr/bin/env python3
"""Offline, immutable company-only navigation orders. No browser or daily writes."""
import argparse,fcntl,hashlib,json,re,sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from zipfile import ZipFile,BadZipFile
from role_cli import identity_valid,validate_backend,validate_job,write_json,digest
ROOT=Path(__file__).resolve().parents[1]
def need(ok,code):
    if not ok:raise ValueError(code)
def ref(path,sha):
    p=Path(path);need(p.is_absolute() and not p.is_symlink(),'absolute-nonsymlink-input-required')
    need(re.fullmatch('[a-f0-9]{64}',sha or '') is not None,'explicit-sha256-required')
    return {'path':str(p.resolve()),'sha256':sha}
def read(reference):
    p=Path(reference['path']);raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'input-hash-mismatch');return json.loads(raw),raw
def receipt(reference):
    value,raw=read(reference);need(value.get('operator_skill')=='douyin-laike-operator' and value.get('backend')=='local-dom-bridge' and value.get('download_verified') is True and value.get('source_is_authoritative_export') is True,'completed-operator-acquisition-required')
    validate_backend(value)
    need(identity_valid(value.get('identity')) and value.get('identity')==value.get('identity_before') and value.get('account_verified') is True,'receipt-identity-unverified')
    need(value.get('company') and str(value.get('groupid','')).isdigit() and re.fullmatch(r'服务商\d+',value['identity']['provider']),'receipt-company-invalid')
    dates=value.get('date_range',{});need(date.fromisoformat(dates['start'])<=date.fromisoformat(dates['end']),'receipt-dates-invalid')
    url=urlsplit(value.get('record_url',''));need(url.scheme=='https' and url.netloc=='life.douyin.com' and '/export_records/' in url.path and parse_qs(url.query).get('groupid')==[str(value['groupid'])],'receipt-record-scope-invalid')
    source=Path(value.get('source',''));need(source.is_absolute() and source.is_file() and not source.is_symlink() and source.suffix.lower()=='.xlsx','receipt-source-invalid')
    need(digest(source)==value.get('src_sha256') and source.stat().st_size==value.get('bytes'),'receipt-source-changed')
    try:
        with ZipFile(source) as z:need({'[Content_Types].xml','xl/workbook.xml'}<=set(z.namelist()) and z.testzip() is None,'receipt-xlsx-invalid')
    except BadZipFile:raise ValueError('receipt-xlsx-invalid')
    journal_ref=ref(str(Path(reference['path']).with_name('workflow.json')),value.get('workflow_sha256'));journal,_=read(journal_ref)
    need(journal.get('state')=='complete' and journal.get('phase')=='done' and journal.get('work_order_id')==value.get('work_order_id') and bool(value.get('work_order_id')),'completed-acquisition-journal-required')
    need(journal.get('company')==value['company'] and str(journal.get('groupid'))==str(value['groupid']) and journal.get('date_range')==dates,'acquisition-journal-scope-conflict')
    result=journal.get('result',{});need(result.get('identity')==value['identity'] and result.get('src_sha256')==value['src_sha256'] and result.get('download_verified') is True,'acquisition-journal-result-conflict')
    stages=[c.get('stage') for c in journal.get('checkpoints',[])];position=-1
    for stage in ('identity','switch','navigation','filter','export-intent','export-generated','download-intent','download-complete'):
        try:position=stages.index(stage,position+1)
        except ValueError:raise ValueError('acquisition-checkpoints-incomplete')
    need(digest(source)==value['src_sha256'],'receipt-source-changed');return value,raw,journal_ref

def prepare(source_ref,*,target_company,target_groupid,outdir,purpose,stable_key,registry_ref=None,identity_refs=None,company_policy=None):
    need(bool(registry_ref)!=bool(identity_refs),'one-identity-source-required')
    need(isinstance(purpose,str) and 0<len(purpose.strip())<=120 and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',stable_key or ''),'purpose-stable-key-invalid')
    need(target_company and str(target_groupid).isdigit(),'target-company-invalid')
    out=Path(outdir);need(out.is_absolute() and not out.is_symlink(),'absolute-independent-outdir-required');out=out.resolve()
    references=[source_ref]+([registry_ref] if registry_ref else identity_refs)
    for r in references:
        original=Path(r['path']).resolve().parent
        need(out!=original and original not in out.parents and out not in original.parents,'output-must-be-independent-of-input-directories')
    binding={'version':1,'source':source_ref,'registry':registry_ref,'identity_receipts':identity_refs or [],'company':target_company,'groupid':str(target_groupid),'purpose':purpose,'stable_key':stable_key}
    if company_policy is not None:binding['company_configuration_policy']=company_policy
    for name in ('inputs','navigation-manifest.json','work-order.json','workflow.json'):
        need(not (out/name).is_symlink(),'navigation-output-symlink-forbidden')
    # Reject overlap before creating even a lock or directory in an export tree.
    if not (out/'navigation-manifest.json').exists():
        initial,_,_=receipt(source_ref);source_directory=Path(initial['source']).parent.resolve()
        need(out!=source_directory and source_directory not in out.parents and out not in source_directory.parents,'output-must-not-overlap-export-directory')
    out.mkdir(parents=True,exist_ok=True);manifest=out/'navigation-manifest.json'
    with (out/'.prepare.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if manifest.exists():
            saved=json.loads(manifest.read_text());need(saved.get('binding')==binding,'stable-key-input-conflict')
            for r in saved['snapshots']:need(Path(r['path']).is_file() and digest(r['path'])==r['sha256'],'navigation-snapshot-changed')
            need(digest(saved['work_order_path'])==saved['work_order_sha256'],'navigation-work-order-changed')
            return {**saved,'reused':True}
        need(not (out/'work-order.json').exists() and not (out/'workflow.json').exists(),'existing-navigation-state-without-manifest')
        source,raw,journal_ref=receipt(source_ref)
        need(source['company']==target_company and str(source['groupid'])==str(target_groupid),'target-must-match-acquisition-company')
        source_dir=Path(source['source']).parent.resolve();need(out!=source_dir and source_dir not in out.parents and out not in source_dir.parents,'output-must-not-overlap-export-directory')
        provider=source['identity']['provider'];known={};inputs=[(source_ref,raw)];provenance=[journal_ref]
        if registry_ref:
            registry,data=read(registry_ref);need(registry.get('version')==2 and registry.get('provider_baseline')==provider and isinstance(registry.get('company_identities'),dict),'identity-registry-invalid')
            known=registry['company_identities'];inputs.append((registry_ref,data))
        else:
            for r in identity_refs:
                value,data,provenance_ref=receipt(r);gid=str(value['groupid'])
                need(value['identity']['provider']==provider and (gid not in known or known[gid]==value['identity']),'identity-receipt-conflict')
                known[gid]=value['identity'];inputs.append((r,data));provenance.append(provenance_ref)
        need(len(known)>=1 and all(str(gid).isdigit() and identity_valid(v) and v['provider']==provider for gid,v in known.items()),'known-company-identities-required')
        need(known.get(str(target_groupid))==source['identity'],'target-identity-unknown-or-conflicting')
        snapshots=[]
        for original,data in inputs:
            destination=out/'inputs'/(original['sha256']+'.json')
            destination.parent.mkdir(exist_ok=True)
            if destination.exists():need(destination.read_bytes()==data,'snapshot-hash-collision')
            else:
                with destination.open('xb') as f:f.write(data);f.flush();__import__('os').fsync(f.fileno())
            snapshots.append({'path':str(destination),'sha256':original['sha256']})
        work_order_id=hashlib.sha256(json.dumps(binding,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        job={'action':'return-company','backend':'local-dom-bridge','work_order_id':work_order_id,'company':target_company,'groupid':str(target_groupid),'workflow_path':str(out/'workflow.json'),'work_order_path':str(out/'work-order.json'),'identity_contract':'merchant-v2','provider_baseline':provider,'identity_baseline':known[str(target_groupid)],'known_company_identities':known,'identity_bootstrap':False,'allowed_groupids':sorted(known),'purpose':purpose,'navigation_only':True,'progress_updates_enabled':False,'export_enabled':False,'send_enabled':False,'source_acquisition_work_order_id':source['work_order_id'],'navigation_input_snapshots':snapshots}
        if company_policy is not None:
            import execution_timing as timing
            fields=timing.company_job_fields(company_policy,target_company,str(target_groupid),known=known)
            need(bool(fields),'company-navigation-v2-policy-required');job.update(fields);job['date_range']={**source['date_range'],'end_exclusive':(date.fromisoformat(source['date_range']['end'])+__import__('datetime').timedelta(days=1)).isoformat()}
        validate_job(job);write_json(job['work_order_path'],job)
        result={'ok':True,'binding':binding,'snapshots':snapshots,'source_journal_provenance':provenance,'work_order_path':job['work_order_path'],'work_order_sha256':digest(job['work_order_path']),'workflow_path':job['workflow_path'],'explicit_tab_id_required':True,'prepare_argv':[sys.executable,str(ROOT/'scripts/role_cli.py'),'prepare','--work-order',job['work_order_path']],'required_extra_argv':['--tab-id','FRESHLY_VERIFIED_EXISTING_TAB_ID'],'business_dates_advanced':False,'export_enabled':False,'send_enabled':False,'reused':False}
        write_json(manifest,result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('receipt','receipt-sha256','company','groupid','outdir','purpose','stable-key'):p.add_argument('--'+name,required=True)
    identity=p.add_mutually_exclusive_group(required=True);identity.add_argument('--identity-registry');identity.add_argument('--identity-receipt',nargs=2,action='append',metavar=('PATH','SHA256'))
    p.add_argument('--registry-sha256');a=p.parse_args()
    try:
        result=prepare(ref(a.receipt,a.receipt_sha256),target_company=a.company,target_groupid=a.groupid,outdir=a.outdir,purpose=a.purpose,stable_key=a.stable_key,registry_ref=ref(a.identity_registry,a.registry_sha256) if a.identity_registry else None,identity_refs=[ref(path,sha) for path,sha in a.identity_receipt] if a.identity_receipt else None)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError) as error:print(json.dumps({'ok':False,'error':str(error),'business_dates_advanced':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
