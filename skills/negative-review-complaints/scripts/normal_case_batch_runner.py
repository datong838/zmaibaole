#!/usr/bin/env python3
"""Bounded original case batch with one process-local immutable XLSX owner."""
if __name__ == '__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse
import json
import normal_case_journey as j

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True)
    parser.add_argument('--source-sha256',required=True)
    parser.add_argument('--steps',type=int,default=25)
    args=parser.parse_args(argv)
    j.need(type(args.steps) is int and 1<=args.steps<=25,'case-batch-bounded-steps')
    with j.p.A.export_parse_session.owner_session():
        result=j.batch(args.root,args.source_sha256,args.steps)
    print(json.dumps(result,ensure_ascii=False))
    return result

if __name__ == '__main__':
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:
        print(json.dumps({'state':'hold','error':str(e)},ensure_ascii=False))
        raise SystemExit(2)
