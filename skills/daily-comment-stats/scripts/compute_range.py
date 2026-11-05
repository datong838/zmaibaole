#!/usr/bin/env python3
"""Print inclusive export dates and an explicit exclusive cutoff."""
import argparse
import json
from ds_calendar import compute, CALENDAR, is_workday, load_calendar

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('today',nargs='?');p.add_argument('--start');p.add_argument('--end')
    p.add_argument('--force',action='store_true');p.add_argument('--calendar',default=str(CALENDAR))
    a=p.parse_args()
    try: result=compute(a.today,a.start,a.end,a.force,a.calendar)
    except (ValueError,OSError) as e: result={'ok':False,'error':str(e)}
    print(json.dumps(result,ensure_ascii=False));return 0 if result.get('ok') else 2
if __name__=='__main__': raise SystemExit(main())
