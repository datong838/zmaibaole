#!/usr/bin/env python3
"""Prepare immutable test-group send orders from a verified daily receipt; never sends."""
import argparse
import json
from pathlib import Path
import sys
from ds_common import PROJECT, MAPPING, load_map, select_company, receipt_valid, sha256, atomic_json, lock
from render_update import build, render

BRANDS = {'烟台一成教育文化咨询有限公司': '榴哆哆', '上海老芗汇餐饮管理有限公司': '地锅岁月'}
TARGET = '测试群请忽略'


def chunks(text, limit=6000):
    """Split without losing a character; prefer paragraph/line boundaries."""
    if not text.strip(): raise ValueError('message-empty')
    if not 100 <= limit <= 9000: raise ValueError('message-limit-invalid')
    result = []
    while len(text) > limit:
        cut = text.rfind('\n\n', 0, limit - 1)
        if cut >= limit // 2: cut += 2
        else:
            cut = text.rfind('\n', 0, limit)
            cut = cut + 1 if cut >= limit // 2 else limit
        result.append(text[:cut]); text = text[cut:]
    if text: result.append(text)
    return result


def prepare(receipt_path):
    path = Path(receipt_path).resolve(); r = json.loads(path.read_text())
    if r.get('flow') != 'daily-comment-stats' or r.get('status') != 'complete' or r.get('quality_blocked') is not False:
        raise ValueError('verified-complete-receipt-required')
    company = select_company(load_map(), r['company']); dates = r['date_range']
    source = Path(r['src_file'])
    if not receipt_valid(r, source, company, dates, sha256(MAPPING)) or r.get('attribution_verified') is not True or r.get('mismatch') is not False or r.get('warnings') or r.get('row_count', 0) <= 0 or r.get('row_count') != r.get('page_filtered'):
        raise ValueError('receipt-or-source-unverified')
    detail = [a for a in r['artifacts'] if Path(a['path']).name.startswith('评价明细_')]
    stats = [a for a in r['artifacts'] if Path(a['path']).name.startswith('评价统计_')]
    if len(detail) != 1 or len(stats) != 1 or r['company'] not in BRANDS:
        raise ValueError('report-artifact-or-brand-ambiguous')
    data = build(source, r['company'], dates['start'], dates['end'], stats[0]['path'])
    text = render(data, BRANDS[r['company']], company['wecom_group'], 'test')
    directory = path.parent / 'test-notifications'; manifest = directory / 'orders.json'
    key = f"daily-comments:{r['company']}:{dates['start']}:{dates['end']}"
    messenger = PROJECT / 'skills/wecom-messenger/scripts/messenger.py'
    with lock(directory):
        if manifest.exists():
            old = json.loads(manifest.read_text())
            if old['receipt_sha256'] != sha256(path): raise ValueError('existing-notifications-receipt-conflict')
            for item in old['orders']:
                if sha256(item['payload']) != item['sha256']: raise ValueError('notification-payload-changed')
            return old
        orders = []
        def order(part, payload, flag):
            orders.append({'part': part, 'payload': str(payload), 'sha256': sha256(payload),
                'prepare_argv': [sys.executable, str(messenger), 'prepare', '--key', key + ':' + part,
                                 '--kind', 'group', '--target', TARGET, '--scope', 'test', flag, str(payload)]})
        for part, artifact in [('detail', detail[0]), ('stats', stats[0])]:
            order(part, Path(artifact['path']).resolve(), '--file')
        messages = chunks(text)
        for index, message in enumerate(messages, 1):
            file = directory / f'text-{index:03}.txt'
            file.write_text((f'【评价日报 {index}/{len(messages)}】\n' if len(messages) > 1 else '') + message)
            order('text-' + str(index), file, '--text-file')
        value = {'workflow': 'daily-comment-stats', 'company': r['company'], 'date_range': dates,
                 'source_receipt': str(path), 'receipt_sha256': sha256(path), 'test_target': TARGET,
                 'production_sent': False, 'sent': False, 'orders': orders}
        atomic_json(manifest, value); return value


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--receipt', required=True)
    a = p.parse_args()
    try:
        out = prepare(a.receipt)
        print(json.dumps(out, ensure_ascii=False))
    except (ValueError, KeyError, OSError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False)); raise SystemExit(1)
