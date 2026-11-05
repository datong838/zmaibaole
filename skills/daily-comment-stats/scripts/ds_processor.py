"""Stage B: durable per-company processing and verified idempotence."""
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import uuid

from ds_common import (FlowError, VERSION, SKILL, MAPPING, atomic_json, now, sha256, lock, receipt_valid)
from ds_workbooks import load_reviews, write_stats
from ds_common import acquisition_backend_valid

def acquisition_check(evidence, company, source, date_range,*,company_policy=None):
    if not evidence: return False
    if isinstance(evidence,(str,Path)): evidence=json.loads(Path(evidence).read_text())
    if evidence.get('kind')=='current-reconciled-export-source-v1':
        from current_range_source import validate_reconciled_export
        return validate_reconciled_export(evidence,company,date_range,source)
    if evidence.get('kind')=='daily-visible-dom-source-v1':
        from ds_common import dom_source_data
        dom_source_data(evidence,company,date_range,source);return True
    if evidence.get('company')!=company['company']: raise FlowError('source-company-mismatch',fatal=True)
    configured=None
    if company_policy is not None:
        import execution_timing as timing
        configured=timing.company_job_fields(company_policy,company['company'],str(company.get('groupid','')))
    if configured:
        expected={'groupid':str(company['groupid'])}
        if evidence.get('identity')!=configured['identity_baseline'] or evidence.get('identity_before')!=configured['identity_baseline']:
            raise FlowError('source-company-mismatch','Acquisition identity does not match configured target',fatal=True)
    else:
        expected=json.loads((SKILL/'config/companies.json').read_text())['companies'].get(company['company'])
    if not expected or str(evidence.get('groupid'))!=expected['groupid']: raise FlowError('source-company-mismatch','Acquisition groupid does not match target company',fatal=True)
    if evidence.get('date_range')!={'start':date_range['start'],'end':date_range['end']}: raise FlowError('source-date-mismatch','Acquisition date range differs')
    if evidence.get('src_sha256')!=sha256(source): raise FlowError('source-hash-mismatch')
    if evidence.get('download_verified') is not True or evidence.get('account_verified') is not True: raise FlowError('acquisition-unverified')
    if not acquisition_backend_valid(evidence): raise FlowError('acquisition-backend-mismatch')
    identity=evidence.get('identity')
    if not isinstance(identity,dict) or set(identity)!={'provider','account_id','manager'} or any(not isinstance(v,str) or not v.strip() for v in identity.values()) or evidence.get('identity_before')!=identity:
        raise FlowError('acquisition-unverified','Account fingerprint is incomplete')
    return True

def archive_outputs(directory, previous, source=None):
    names=[]
    for item in previous.get('artifacts',[]):
        p=Path(item.get('path','')).resolve()
        if p.parent==directory.resolve() and p.is_file() and p!=source: names.append(p)
    # Only this workflow's previously recorded files are moved; never external source files.
    if names:
        backup=directory/'history'/uuid.uuid4().hex;backup.mkdir(parents=True)
        for p in names: shutil.move(str(p),str(backup/p.name))
        atomic_json(backup/'receipt.json',previous)

def process(source, company, date_range, outdir, mapping_path=MAPPING, page_filtered=None,
            evidence=None, rerun=False,*,capture_ref=None,company_policy=None):
    typed=json.loads(Path(evidence).read_text())if isinstance(evidence,(str,Path))else evidence
    if isinstance(typed,dict)and typed.get('kind')=='daily-visible-dom-source-v1':
        return process_dom(source,company,date_range,outdir,mapping_path,page_filtered,typed,rerun=rerun,capture_ref=capture_ref)
    source=Path(source).resolve(); directory=Path(outdir).resolve(); rp=directory/'receipt.json'
    if type(page_filtered) not in (int,type(None)) or page_filtered is not None and page_filtered<0:
        raise FlowError('page-count-invalid')
    with lock(directory):
        mapping_hash=sha256(mapping_path)
        try:
            previous=json.loads(rp.read_text()) if rp.exists() else {}
            if not isinstance(previous,dict): raise ValueError('Receipt must be an object')
        except ValueError:
            backup=directory/'history'/uuid.uuid4().hex;backup.mkdir(parents=True)
            shutil.copyfile(rp,backup/'receipt.corrupt.json')
            tag='%s至%s'%(date_range['start'],date_range['end'])
            known=[directory/('评价明细_%s_%s.xlsx'%(company['company'],tag)),directory/('评价统计_%s_%s.xlsx'%(company['company'],tag)),directory/'公司-企微群映射.csv']
            previous={'status':'corrupt','artifacts':[{'path':str(p)} for p in known if p.is_file()]}
        if source.is_file() and not rerun and receipt_valid(previous,source,company,date_range,mapping_hash):
            # New evidence/page counts can change the quality gate, even for identical XLSX bytes.
            same_count=page_filtered is None or page_filtered==previous.get('page_filtered')
            try: same_evidence=not evidence or (previous.get('attribution_verified') and acquisition_check(evidence,company,source,date_range,company_policy=company_policy))
            except FlowError: same_evidence=False
            if same_count and same_evidence: return {**previous,'action':'skipped','skip_reason':'already_done','receipt':str(rp)}
        archive_outputs(directory,previous,source)
        started=time.monotonic()
        receipt={'flow':'daily-comment-stats','version':VERSION,'status':'processing','company':company['company'],
                 'wecom_group':company['wecom_group'],'generated_at':now(),'date_range':{'start':date_range['start'],'end':date_range['end']},
                 'mapping_sha256':mapping_hash,'src_file':str(source),'send_blocked':True,'sent':False,
                 'warnings':list(date_range.get('warnings',[])),'range_warnings':list(date_range.get('warnings',[])),
                 'stages':[],'artifacts':[],'outputs':[]}
        def stage(name,ok=True,**details):
            receipt['stages'].append({'stage':name,'ok':ok,'at':now(),**details});atomic_json(rp,receipt)
        try:
            stage('range',**{k:v for k,v in date_range.items() if k not in ('ok',)})
            if not source.is_file(): raise FlowError('source-missing')
            receipt['src_sha256']=sha256(source)
            receipt['attribution_verified']=acquisition_check(evidence,company,source,date_range,company_policy=company_policy)
            if isinstance(typed,dict) and typed.get('kind')=='current-reconciled-export-source-v1':
                receipt.update(source_kind=typed['kind'],download_verified=False,source_is_authoritative_export=False,current_result=typed['current_result'])
            stage('company',verified=receipt['attribution_verified'])
            reviews,headers=load_reviews(source,date_range['start'],date_range['end'])
            if len(headers)!=20: receipt['warnings'].append('source-column-count-changed: expected 20 fields, inspect original export')
            count=len(reviews);receipt['row_count']=count;receipt['source_columns']=headers
            receipt['page_filtered']=page_filtered
            receipt['mismatch']=page_filtered!=count if page_filtered is not None else None
            stage('load',row_count=count,column_count=len(headers))
            if count==0:
                receipt['zero_rows']=True;receipt['status']='zero_rows';receipt['quality_blocked']=True
                stage('gate_zero_rows',triggered=True);return {**receipt,'receipt':str(rp)}
            receipt['zero_rows']=False
            stage('gate_zero_rows',triggered=False)
            if receipt['mismatch']: receipt['warnings'].append('page-export-count-mismatch')
            if page_filtered is None: receipt['warnings'].append('page-count-unverified')
            if not receipt['attribution_verified']: receipt['warnings'].append('source-company-unverified: manual import')
            stage('cross_check',page_filtered is not None and not receipt['mismatch'],page_filtered=page_filtered,exported=count,
                  result='unverified' if page_filtered is None else 'mismatch' if receipt['mismatch'] else 'matched')
            tag='%s至%s'%(date_range['start'],date_range['end'])
            names=['评价明细_%s_%s.xlsx'%(company['company'],tag),'评价统计_%s_%s.xlsx'%(company['company'],tag),'公司-企微群映射.csv']
            # No output is published until all three artifacts validate. Receipt is committed last.
            with tempfile.TemporaryDirectory(prefix='.staging-',dir=str(directory)) as tmp:
                tmp=Path(tmp);shutil.copyfile(source,tmp/names[0]);shutil.copyfile(mapping_path,tmp/names[2])
                receipt['summary']=write_stats(tmp/names[1],company['company'],reviews)
                if sha256(tmp/names[0])!=receipt['src_sha256'] or sha256(source)!=receipt['src_sha256']: raise FlowError('source-changed-during-run')
                stage('stats',summary=receipt['summary'])
                receipt['artifacts']=[{'path':str(directory/n),'sha256':sha256(tmp/n),'bytes':(tmp/n).stat().st_size} for n in names]
                for name in names: os.replace(tmp/name,directory/name)
            receipt['outputs']=[item['path'] for item in receipt['artifacts']]
            receipt['quality_blocked']=bool(receipt['warnings'])
            receipt['status']='needs_review' if receipt['quality_blocked'] else 'complete'
            receipt['elapsed_s']=round(time.monotonic()-started,3)
            stage('commit',artifacts_verified=True)
            return {**receipt,'receipt':str(rp)}

        except Exception as e:
            receipt['status']='failed';receipt['quality_blocked']=True
            receipt['error']={'code':e.code if isinstance(e,FlowError) else 'processing-error','message':str(e),'fatal':bool(getattr(e,'fatal',False))}
            receipt['elapsed_s']=round(time.monotonic()-started,3);stage('failure',False,error=receipt['error'])
            return {**receipt,'receipt':str(rp)}


def process_dom(source,company,dates,outdir,mapping_path,page_filtered,payload,*,rerun=False,capture_ref=None):
    from ds_common import dom_source_data,validated_dom_receipt,dom_capture_data
    from ds_workbooks import dom_reviews
    source=Path(source).resolve();directory=Path(outdir).resolve();rp=directory/'receipt.json'
    if capture_ref:dom_capture_data(capture_ref,payload)
    data=dom_source_data(payload,company,dates,source);reviews=dom_reviews(data)
    if page_filtered!=data['summary']['platform_filtered_normal_count']:raise FlowError('dom-normal-count-conflict')
    with lock(directory):
        mapping_hash=sha256(mapping_path)
        previous=json.loads(rp.read_bytes())if rp.exists()else{}
        if previous and not rerun:
            validated_dom_receipt(previous,source,company,dates,mapping_hash)
            if previous['dom_source']!=payload:raise FlowError('dom-existing-source-conflict')
            return {**previous,'action':'skipped','receipt':str(rp)}
        archive_outputs(directory,previous,source)
        receipt={'flow':'daily-comment-stats','version':VERSION,'source_kind':'daily-visible-dom-source-v1',
                 'dom_source':payload,'company':company['company'],'wecom_group':company['wecom_group'],
                 'generated_at':now(),'date_range':{k:dates[k]for k in ('start','end')},'range_warnings':dates.get('warnings',[]),
                 'mapping_sha256':mapping_hash,'src_file':str(source),'src_sha256':sha256(source),
                 'download_verified':False,'source_is_authoritative_export':False,'origin':'visible-dom',
                 'row_count':len(reviews),'page_filtered':page_filtered,'dom_counts':data['summary'],
                 'attribution_verified':True,'mismatch':False,'warnings':list(dates.get('warnings',[])),
                 'status':'complete'if reviews else'zero_rows','zero_rows':not bool(reviews),'quality_blocked':not bool(reviews),
                 'send_blocked':True,'sent':False,'artifacts':[],'outputs':[]}
        if receipt['warnings']:raise FlowError('dom-range-warning')
        if capture_ref:receipt['dom_capture']=capture_ref
        if reviews:
            tag='%s至%s'%(dates['start'],dates['end']);names=['评价明细_%s_%s.xlsx'%(company['company'],tag),'评价统计_%s_%s.xlsx'%(company['company'],tag),'公司-企微群映射.csv']
            with tempfile.TemporaryDirectory(prefix='.dom-staging-',dir=directory)as stage:
                stage=Path(stage);shutil.copyfile(source,stage/names[0]);shutil.copyfile(mapping_path,stage/names[2])
                receipt['summary']=write_stats(stage/names[1],company['company'],reviews)
                if sha256(stage/names[0])!=receipt['src_sha256']or sha256(source)!=receipt['src_sha256']:raise FlowError('source-changed-during-run')
                receipt['artifacts']=[{'path':str(directory/n),'sha256':sha256(stage/n),'bytes':(stage/n).stat().st_size}for n in names]
                for n in names:os.replace(stage/n,directory/n)
            receipt['outputs']=[a['path']for a in receipt['artifacts']]
        if not capture_ref:
            receipt.update(status='needs_review',quality_blocked=True,warnings=['saved-dom-evaluation-only'])
        atomic_json(rp,receipt);return {**receipt,'receipt':str(rp)}


from ds_common import dom_command_function
process=dom_command_function(process)
