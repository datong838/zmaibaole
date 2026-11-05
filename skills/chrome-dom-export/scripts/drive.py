#!/usr/bin/env python3
"""Compatibility guard: implicit tab selection and guessed click targets removed.

Use bridge.py for the reviewed protocol, or the independent operator's durable
bridge-workflow.py with an explicit work order and tab ID.
"""
import json
import sys

def main():
    print(json.dumps({'ok':False,'error':'legacy-ambiguous-driver-retired',
        'reason':'Explicit tab binding and a durable work order are required; no first-tab, shortest-selector or repeated-click fallback.',
        'read_protocol':'scripts/bridge.py',
        'workflow':'../douyin-laike-operator/scripts/bridge-workflow.py'},ensure_ascii=False))
    return 2
if __name__=='__main__':sys.exit(main())
