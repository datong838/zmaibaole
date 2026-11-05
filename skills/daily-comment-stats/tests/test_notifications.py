import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
from prepare_notifications import chunks, prepare, TARGET
from ds_processor import process
from ds_common import load_map, MAPPING, sha256
from ds_calendar import compute
from test_workflow import workbook, review, IDENTITY


class NotificationsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.source = self.root / 'source.xlsx'
        self.company = load_map()[0]; self.dates = compute('2026-10-19')

    def verified(self):
        workbook(self.source, [review(star=2, text='完整顾客原文')])
        ev = {'company': self.company['company'], 'groupid': '1767942028615694',
              'date_range': {k: self.dates[k] for k in ('start', 'end')}, 'src_sha256': sha256(self.source),
              'download_verified': True, 'account_verified': True, 'identity': IDENTITY,
              'identity_before': IDENTITY, 'operator_skill': 'douyin-laike-operator', 'backend': 'codex-existing-extension'}
        result = process(self.source, self.company, self.dates, self.root / 'out', MAPPING,
                         page_filtered=1, evidence=ev)
        self.assertEqual(result['status'], 'complete')
        return Path(result['receipt'])

    def test_text_split_preserves_all_characters_and_limits(self):
        for text in ['甲' * 20001, ('第一段\n\n第二段\n' * 500), ('甲' * 99 + '\n') * 4]:
            parts = chunks(text, 100)
            self.assertEqual(''.join(parts), text)
            self.assertTrue(all(0 < len(part) <= 100 for part in parts))

    def test_orders_test_only_and_idempotent_no_send(self):
        path = self.verified(); first = prepare(path); second = prepare(path)
        self.assertEqual(first, second)
        self.assertFalse(first['sent']); self.assertEqual(first['test_target'], TARGET)
        self.assertEqual([o['part'] for o in first['orders']], ['detail', 'stats', 'text-1'])
        for item in first['orders']:
            self.assertEqual(sha256(item['payload']), item['sha256'])
            self.assertIn('prepare', item['prepare_argv'])
            self.assertIn(TARGET, item['prepare_argv']); self.assertIn('test', item['prepare_argv'])
        text = Path(first['orders'][-1]['payload']).read_text()
        self.assertIn('完整顾客原文', text)
        self.assertNotIn('历史Excel', text)

    def test_modified_receipt_cannot_generate_new_message_keys(self):
        path = self.verified(); prepare(path)
        data = json.loads(path.read_text()); data['generated_at'] += ' changed'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'existing-notifications-receipt-conflict'): prepare(path)

    def test_modified_output_is_rejected_before_dispatch(self):
        path = self.verified(); manifest = prepare(path)
        Path(manifest['orders'][0]['payload']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'receipt-or-source-unverified'): prepare(path)

    def test_unverified_manual_source_cannot_notify(self):
        path = self.verified(); data = json.loads(path.read_text()); data['attribution_verified'] = False
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'receipt-or-source-unverified'): prepare(path)


if __name__ == '__main__': unittest.main()
