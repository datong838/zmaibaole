#!/usr/bin/env python3
"""Independent Douyin operator handoff CLI. Browser execution lives in acquire.mjs.

prepare validates a work order; finalize verifies an actual tool-reported local XLSX,
copies the immutable export into the designated logistics directory, and emits a
handoff receipt. No dependencies on daily-comment-stats or any browser profile.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, date
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, parse_qs
from zipfile import ZipFile, BadZipFile

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=str(path.parent),prefix='.'+path.name)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def validate_job(job):
    if job.get('action') not in ('acquire','return-company'):raise ValueError('work-order-action-invalid')
    if not job.get('company') or not str(job.get('groupid','')).isdigit():raise ValueError('work-order-identity-invalid')
    dates=job.get('date_range',{})
    if job['action']=='acquire':
        if date.fromisoformat(dates['start'])>date.fromisoformat(dates['end']):raise ValueError('work-order-date-invalid')
        if not Path(job.get('source_dir','')).is_absolute():raise ValueError('absolute-source-directory-required')
    return job

def identity_valid(identity):
    return isinstance(identity,dict) and set(identity)=={'provider','account_id','manager'} and all(isinstance(x,str) and x.strip() for x in identity.values())

def validate_backend(candidate):
    backend=candidate.get('backend','codex-existing-extension')
    if backend not in ('codex-existing-extension','local-dom-bridge'):
        raise ValueError('acquisition-backend-mismatch')
    if backend=='local-dom-bridge':
        proof=candidate.get('transport_proof',{})
        if proof.get('safety_version') not in ('dom-only-20261021-3','dom-only-20261021-4','dom-only-20261021-5','dom-only-20261021-6','dom-only-20261021-7','dom-only-20261021-8','dom-only-20261021-9','dom-only-20261021-10','dom-only-20261021-11','dom-only-20261103-12') or proof.get('safety')!='DOM-only' or proof.get('reviewed_extension_ready') is not True:
            raise ValueError('bridge-transport-unverified')
    return backend

def finalize(job,candidate,out):
    validate_job(job)
    backend=validate_backend(candidate)
    if candidate.get('company')!=job['company'] or str(candidate.get('groupid'))!=str(job['groupid']):raise ValueError('source-company-mismatch')
    desired={k:job['date_range'][k] for k in ('start','end')}
    if candidate.get('date_range')!=desired:raise ValueError('source-date-mismatch')
    account=candidate.get('identity');before=candidate.get('identity_before')
    if not identity_valid(account) or before!=account or candidate.get('account_verified') is not True:raise ValueError('account-unverified-or-changed')
    if job.get('identity_baseline') and account!=job['identity_baseline']:raise ValueError('account-changed')
    if job.get('identity_contract')=='merchant-v2':
        if not isinstance(job.get('provider_baseline'),str) or account['provider']!=job['provider_baseline']:raise ValueError('provider-changed-or-unverified')
        known=job.get('known_company_identities',{}).get(str(job['groupid']))
        if known is not None and known!=account:raise ValueError('account-changed')
    record=urlparse(candidate.get('record_url',''))
    if record.scheme!='https' or record.netloc!='life.douyin.com' or '/export_records/' not in record.path or parse_qs(record.query).get('groupid')!=[str(job['groupid'])]:raise ValueError('record-context-unverified')
    if type(candidate.get('page_filtered')) is not int or candidate['page_filtered']<0:raise ValueError('page-count-unverified')
    source=Path(candidate.get('source','')).expanduser().resolve()
    if not source.is_file() or source.suffix.lower()!='.xlsx' or source.stat().st_size==0:raise ValueError('download-file-unverified')
    try:
        with ZipFile(source) as z:
            if not {'[Content_Types].xml','xl/workbook.xml'}<=set(z.namelist()) or z.testzip():raise ValueError('download-xlsx-invalid')
    except BadZipFile:raise ValueError('download-xlsx-invalid')
    checksum=digest(source)
    if candidate.get('src_sha256') is not None and candidate['src_sha256']!=checksum:raise ValueError('download-changed-after-verification')
    directory=Path(job['source_dir']);directory.mkdir(parents=True,exist_ok=True)
    name='门店评价_全部门店_%s-%s.xlsx'%(desired['start'].replace('-','_'),desired['end'].replace('-','_'))
    dest=directory/name
    if dest.exists() and digest(dest)!=checksum:dest=directory/(Path(name).stem+'_'+checksum[:12]+'.xlsx')
    if source!=dest.resolve() and not dest.exists():
        fd,tmp=tempfile.mkstemp(prefix='.download-',dir=str(directory));os.close(fd)
        try:
            shutil.copyfile(source,tmp)
            if digest(tmp)!=checksum or digest(source)!=checksum:raise ValueError('download-changed-during-copy')
            os.replace(tmp,dest)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    result={**candidate,'source':str(dest.resolve()),'src_sha256':checksum,'download_verified':True,'account_verified':True,
            'backend':backend,'operator_skill':'douyin-laike-operator',
            'recorded_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds'),'bytes':dest.stat().st_size,
            'send_blocked':True,'sent':False,'source_is_authoritative_export':True}
    write_json(out,result);return result

def finalize_journal(job,path,out):
    journal=json.loads(Path(path).read_text())
    if str(Path(path).resolve())!=str(Path(job.get('workflow_path','')).resolve()):raise ValueError('workflow-path-mismatch')
    if journal.get('work_order_id')!=job.get('work_order_id') or not job.get('work_order_id'):raise ValueError('work-order-conflict')
    if journal.get('state')!='complete' or journal.get('phase')!='done':raise ValueError('workflow-incomplete')
    if journal.get('company')!=job['company'] or str(journal.get('groupid'))!=str(job['groupid']):raise ValueError('source-company-mismatch')
    if journal.get('date_range')!={k:job['date_range'][k] for k in ('start','end')}:raise ValueError('source-date-mismatch')
    stages=[e.get('stage') for e in journal.get('checkpoints',[])]
    required=['identity','switch','navigation','filter','export-intent','export-generated','download-intent','download-complete']
    position=-1
    for stage in required:
        try:position=stages.index(stage,position+1)
        except ValueError:raise ValueError('workflow-checkpoints-incomplete')
    result=finalize(job,journal['result'],out)
    result.update(work_order_id=job['work_order_id'],workflow_sha256=digest(path))
    write_json(out,result);return result

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for verb in ('prepare','finalize'):
        s=sub.add_parser(verb);s.add_argument('--work-order',required=True)
        if verb=='prepare':
            s.add_argument('--backend',choices=['codex-existing-extension','local-dom-bridge'],default='local-dom-bridge')
            s.add_argument('--tab-id',type=int)
        if verb=='finalize':
            source=s.add_mutually_exclusive_group(required=True);source.add_argument('--candidate');source.add_argument('--journal')
            s.add_argument('--out',required=True)
    a=p.parse_args()
    try:
        job=validate_job(json.loads(Path(a.work_order).read_text()))
        if a.command=='prepare' and a.backend=='local-dom-bridge':
            if a.tab_id is None or a.tab_id<=0:raise ValueError('explicit-tab-id-required')
            result={'ok':True,'operator_skill':'douyin-laike-operator','backend':'local-dom-bridge',
                    'required_dependency':'chrome-dom-export','protocol':'journal-v1',
                    'tick_argv':[__import__('sys').executable,str(ROOT/'scripts/bridge-workflow.py'),'--work-order',str(Path(a.work_order).resolve()),'--tab-id',str(a.tab_id)],
                    'company':job['company'],'groupid':str(job['groupid']),
                    'next':'Invoke tick_argv once per transition; report any waiting_for or error to supervisor. No fallback actions.'}
        elif a.command=='prepare':
            module=(ROOT/'scripts/workflow-runtime.mjs').as_uri()
            bootstrap='var laikeFs = await import("node:fs"); var laikeModule = await import(%s); var laikeJob = JSON.parse(laikeFs.readFileSync(%s, "utf8")); var laikeWorkflow = await laikeModule.createWorkflow(browser, tab, laikeJob); nodeRepl.write(laikeWorkflow.status());'%(json.dumps(module),json.dumps(str(Path(a.work_order).resolve())))
            result={'ok':True,'operator_skill':'douyin-laike-operator','backend':'codex-existing-extension',
                'required_tool':'mcp__cua_repl.js','runtime_script':str(ROOT/'scripts/workflow-runtime.mjs'),
                'company':job['company'],'groupid':job['groupid'],'resume':job.get('resume'),
                'bootstrap_code':bootstrap,'tick_code':'nodeRepl.write(await laikeWorkflow.tick());',
                'next':'Use bootstrap_code with the selected existing browser/tab; one tick_code per host invocation. flow.py advance imports the journal.'}
        elif a.journal:result=finalize_journal(job,a.journal,a.out)
        else:
            if job.get('work_order_id'):raise ValueError('machine-work-order-requires-journal')
            result=finalize(job,json.loads(Path(a.candidate).read_text()),a.out)
        print(json.dumps(result,ensure_ascii=True,indent=2));return 0
    except (ValueError,KeyError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=True));return 2

if __name__=='__main__':raise SystemExit(main())
