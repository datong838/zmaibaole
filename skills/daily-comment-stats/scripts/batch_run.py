#!/usr/bin/env python3
"""Offline Stage B batch. CSV order, independent receipts, fail-closed sources."""
import argparse
import json
from pathlib import Path
import re
import time
from ds_calendar import compute, CALENDAR
from ds_common import MAPPING, FlowError, load_map, normalize, match_name, company_dir, output_root, now, atomic_json, lock
from ds_processor import process

def find_source(company, files):
    candidates={}
    for path in files:
        if path.name.startswith('评价统计_') or path.name.startswith('~$'): continue
        name=re.sub(r'^评价明细_', '', path.stem)
        name=re.sub(r'_(?:\d{4}-\d{2}-\d{2}至\d{4}-\d{2}-\d{2}|\d{4}-\d{4})$', '', name)
        candidates.setdefault(name,[]).append(path)
    chosen=match_name(company,list(candidates))
    if len(candidates[chosen])!=1: raise FlowError('source-ambiguous','Multiple exports for the company; use a manifest or remove ambiguity')
    return candidates[chosen][0]

def batch(src_dir,dates,outdir,mapping_path=MAPPING,rerun=False,dry_run=False):
    if not Path(src_dir).is_dir(): raise FlowError('source-directory-missing')
    rows=load_map(mapping_path);root=Path(outdir);files=[p for p in Path(src_dir).iterdir() if p.is_file() and p.suffix.lower()=='.xlsx']
    result={'flow':'daily-comment-stats','version':'1.0.0','mode':'offline-batch','date_range':{'start':dates['start'],'end':dates['end']},'generated_at':now(),'dry_run':dry_run,'send_blocked':True,'results':[]}
    started=time.monotonic()
    def run():
        halted=False
        for row in rows:
            item={**row,'outdir':str(company_dir(root,row))}
            if halted: item.update(status='not_run',reason='batch-halted')
            else:
                try:
                    source=find_source(row['company'],files);item['src']=str(source.resolve())
                    if dry_run: item['status']='planned'
                    else:
                        evidence=source.with_suffix('.acquisition.json')
                        ev=json.loads(evidence.read_text()) if evidence.exists() else None
                        rec=process(source,row,dates,item['outdir'],mapping_path,
                                    ev.get('page_filtered') if ev else None,ev,rerun)
                        item.update(status=rec['status'],action=rec.get('action'),receipt=rec['receipt'])
                        if rec.get('error'): item['error']=rec['error'];halted=bool(rec['error'].get('fatal'))
                except FlowError as e: item.update(status='skipped',reason=e.code);halted=e.fatal
                except (OSError,ValueError) as e: item.update(status='failed',reason='source-error',message=str(e))
            result['results'].append(item)
            if not dry_run: save()
    def save():
        counts={s:sum(i['status']==s for i in result['results']) for s in ('complete','needs_review','zero_rows','failed','skipped','not_run','planned')}
        result.update(companies_total=len(rows),succeeded=counts['complete'],needs_review=counts['needs_review'],failed=counts['failed'],skipped=counts['skipped']+counts['zero_rows'],not_run=counts['not_run'],elapsed_s=round(time.monotonic()-started,3),counts=counts)
        if not dry_run: atomic_json(root/'batch_receipt.json',result)
    if dry_run: run();save()
    else:
        with lock(root): run();save()
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--src-dir',required=True);p.add_argument('--start');p.add_argument('--end');p.add_argument('--today')
    p.add_argument('--outdir');p.add_argument('--mapping',default=str(MAPPING));p.add_argument('--calendar',default=str(CALENDAR))
    p.add_argument('--force',action='store_true');p.add_argument('--rerun',action='store_true');p.add_argument('--dry-run',action='store_true')
    a=p.parse_args()
    try:
        dates=compute(a.today,a.start,a.end,a.force,a.calendar)
        if not dates['ok']: print(json.dumps(dates,ensure_ascii=False));return 0
        out=a.outdir or output_root(dates['today'],dates['start'],dates['end'])
        result=batch(a.src_dir,dates,out,a.mapping,a.rerun,a.dry_run)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 1 if result['failed'] else 0
    except (FlowError,ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':{'code':getattr(e,'code','configuration-error'),'message':str(e)}},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
