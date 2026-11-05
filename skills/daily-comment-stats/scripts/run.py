#!/usr/bin/env python3
"""Stage B: process one explicitly attributed company export, no browser/network calls."""
import argparse
import json
from ds_calendar import compute, CALENDAR
from ds_common import MAPPING, FlowError, load_map, select_company, output_root, company_dir
from ds_processor import process

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--src',required=True);p.add_argument('--company');p.add_argument('--start');p.add_argument('--end')
    p.add_argument('--today');p.add_argument('--outdir');p.add_argument('--mapping',default=str(MAPPING))
    p.add_argument('--calendar',default=str(CALENDAR));p.add_argument('--force',action='store_true')
    p.add_argument('--rerun',action='store_true');p.add_argument('--page-filtered',type=int)
    p.add_argument('--source-receipt',help='Verified acquisition evidence JSON; manual import remains flagged without it')
    a=p.parse_args()
    try:
        company=select_company(load_map(a.mapping),a.company)
        dates=compute(a.today,a.start,a.end,a.force,a.calendar)
        if not dates['ok']:
            print(json.dumps({'flow':'daily-comment-stats','status':'skipped','reason':dates['reason'],'date_range':dates},ensure_ascii=False));return 0
        out=a.outdir or company_dir(output_root(dates['today'],dates['start'],dates['end']),company)
        result=process(a.src,company,dates,out,a.mapping,a.page_filtered,a.source_receipt,a.rerun)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 1 if result['status']=='failed' else 0
    except (FlowError,ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':{'code':getattr(e,'code','configuration-error'),'message':str(e)}},ensure_ascii=False));return 2
if __name__=='__main__': raise SystemExit(main())
