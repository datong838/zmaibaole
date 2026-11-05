#!/usr/bin/env python3
"""Limited, durable DOM discovery for visible account and company-dialog structure."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
BRIDGE = ROOT / 'skills/chrome-dom-export/scripts/bridge.py'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dom_evidence import VERSION
ALLOWED = {'服务商7576493388812273702', '切换公司'}


def atomic(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.discovery-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def call(command):
    proc = subprocess.run([sys.executable, str(BRIDGE), 'request', json.dumps(command, ensure_ascii=False), '--timeout', '60'], capture_output=True, text=True, timeout=75)
    try:
        reply = json.loads(proc.stdout)
    except ValueError:
        raise RuntimeError('bridge-invalid-json-or-process-failure')
    if not reply.get('ok'):
        raise RuntimeError('bridge-command-failed: ' + str(reply.get('error', 'unknown')))
    return reply['result']


def preflight(tab_id, group_id, invoke):
    tabs = invoke({'op': 'tabs'})
    matches = [t for w in tabs for t in w.get('tabs', []) if t.get('tabId') == tab_id]
    if len(matches) != 1 or not matches[0].get('allowed'):
        raise RuntimeError('explicit-tab-not-unique-or-not-allowed')
    from urllib.parse import urlsplit, parse_qs
    url = urlsplit(matches[0]['url'])
    if url.scheme != 'https' or url.netloc != 'life.douyin.com' or parse_qs(url.query).get('groupid') != [group_id]:
        raise RuntimeError('explicit-company-groupid-mismatch')
    ping = invoke({'op': 'ping', 'tabId': tab_id})
    if ping.get('version') != VERSION or ping.get('safety') != 'DOM-only':
        raise RuntimeError('reviewed-content-version-required')
    return {'tab': matches[0], 'ping': ping}


def tree(tab_id, invoke):
    result = invoke({'op': 'tree', 'tabId': tab_id})
    if result.get('truncated') is not False or not isinstance(result.get('root'), dict):
        raise RuntimeError('complete-untruncated-tree-required')
    return result


def execute(tab_id, group_id, out, name=None, invoke=call, operation="click", search=None):
    if search is not None:operation='filter'
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal_path = out / 'receipt.json'
        request = {'tab_id': tab_id, 'group_id': group_id, 'name': name, 'operation': operation, 'search': search}
        if journal_path.exists():
            prior = json.loads(journal_path.read_text())
            if prior.get('request') != request:
                raise RuntimeError('step-directory-request-conflict')
            # Any durable action intent is terminal for this step. Never replay it.
            if prior.get('intent'):
                return prior
        if name is not None and name not in ALLOWED:
            raise RuntimeError('discovery-control-not-allowed')
        evidence = preflight(tab_id, group_id, invoke)
        before = tree(tab_id, invoke)
        atomic(out / 'before-tree.json', before)
        atomic(out / 'identity.json', evidence)
        receipt = {'request': request, 'intent': False, 'status': 'snapshot', 'at': datetime.now(timezone.utc).isoformat()}
        if search is not None:
            if search not in ('烟台一成教育文化咨询有限公司','上海老芗汇餐饮管理有限公司'):raise RuntimeError('unreviewed-company')
            found=invoke({'op':'find','tabId':tab_id,'locator':{'by':'role','value':'textbox'}})
            matches=[n for n in found if n.get('placeholder')=='搜索商户']
            if len(matches)!=1:raise RuntimeError('unique-company-search-required')
            receipt.update(intent=True,status='unknown',matched=matches[0]);atomic(journal_path,receipt)
            try:
                result=invoke({'op':'filter','tabId':tab_id,'locator':{'by':'selector','value':matches[0]['selector']},'value':search})
                receipt.update(status='filter-confirmed',result=result);atomic(journal_path,receipt)
                after=tree(tab_id,invoke);atomic(out/'after-tree.json',after)
                receipt.update(status='complete',after_tree=str(out/'after-tree.json'))
            except Exception as exc:receipt['error']=str(exc)
            atomic(journal_path,receipt);return receipt
        if name is None:
            atomic(journal_path, receipt)
            return receipt
        matches = invoke({'op': 'find', 'tabId': tab_id, 'locator': {'by': 'text', 'value': name}})
        atomic(out / 'exact-find.json', matches)
        if not isinstance(matches, list) or len(matches) != 1 or matches[0].get('disabled'):
            raise RuntimeError('exact-control-not-unique-or-disabled')
        receipt.update(intent=True, status='unknown', matched=matches[0])
        atomic(journal_path, receipt)
        try:
            result = invoke({'op': operation, 'tabId': tab_id, 'locator': {'by': 'text', 'value': name}, 'kind': 'navigation'})
            receipt.update(status='click-confirmed', result=result)
            atomic(journal_path, receipt)
            after = tree(tab_id, invoke)
            atomic(out / 'after-tree.json', after)
            receipt.update(status='complete', after_tree=str(out / 'after-tree.json'))
        except Exception as exc:
            receipt['error'] = str(exc)
            # Preserve unknown / confirmed click; do not clear intent on any error.
        atomic(journal_path, receipt)
        return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tab-id', type=int, required=True)
    p.add_argument('--group-id', required=True, choices=['1767942028615694', '1764303851132943'])
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--search', choices=['烟台一成教育文化咨询有限公司','上海老芗汇餐饮管理有限公司'])
    p.add_argument('--hover', action='store_true', help='Semantic hover only, never coordinates')
    p.add_argument('--open', dest='name', choices=sorted(ALLOWED))
    args = p.parse_args()
    if args.tab_id < 0:
        p.error('tab-id must be nonnegative')
    try:
        result = execute(args.tab_id, args.group_id, args.out, args.name, operation="hover" if args.hover else "click", search=args.search)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] in ('snapshot', 'complete') else 1
    except Exception as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
