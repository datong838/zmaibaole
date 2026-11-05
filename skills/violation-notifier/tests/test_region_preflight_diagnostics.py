"""Rejected transport replies survive before capture intent; no UI used."""
import json
from pathlib import Path
import tempfile
import unittest

import test_business_cells_capture as fixture_api
import region_frame_capture as r


class RegionReplyTests(unittest.TestCase):
    def test_empty_visible_selection_retains_original_base_before_region_request(self):
        fixture_api.BusinessCells.setUpClass()
        fixture = fixture_api.BusinessCells()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        seen = []

        def request(command):
            seen.append(command['op'])
            reply = fixture.request(command)
            if command['op'] == 'viewport-proof':
                for row in reply['result']['business_cells']:
                    for cell in row['cells']:
                        cell['geometry'].update(box_viewport_contained=False,
                                                evidence_eligible=False,
                                                preview_required=False)
            return reply

        out = fixture.root / 'empty-selection'
        with self.assertRaisesRegex(ValueError, 'violation-uncovered-no-eligible-five-cell-group'):
            r.capture(fixture.src, fixture.q['pages'][0]['observation'], fixture.pr,
                      pid=55, mode='rows', chain_id='diagnostic-original-chain',
                      key='diagnostic-empty-key', outdir=out, revision='r1',
                      uncovered_only=True, request=request, native=fixture.native, ax=fixture.ax)
        records = list((out / 'proof-replies').glob('base-*.json'))
        self.assertEqual(len(records), 1)
        saved = json.loads(records[0].read_text())
        self.assertEqual(saved['command']['op'], 'viewport-proof')
        self.assertEqual(saved['operation']['key'], 'diagnostic-empty-key')
        self.assertTrue(saved['reply']['ok'])
        self.assertTrue(all(not c['geometry']['evidence_eligible']
                            for row in saved['reply']['result']['business_cells']
                            for c in row['cells']))
        self.assertNotIn('dom-region-proof', seen)
        self.assertEqual(fixture.captured, 0)
        self.assertFalse(list((fixture.root / '.native-region-frame-state').glob('*.json')))

    def test_rejected_before_reply_is_saved_without_capture_intent_or_png(self):
        fixture_api.BusinessCells.setUpClass()
        fixture = fixture_api.BusinessCells()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        failure = {'ok': False, 'error': 'region-business-foreign-effect-overlap:actual-cell'}

        def request(command):
            if command['op'] == 'dom-region-proof':
                return failure
            return fixture.request(command)

        out = fixture.root / 'rejected-proof'
        with self.assertRaisesRegex(ValueError, 'actual-cell'):
            r.capture(fixture.src, fixture.q['pages'][0]['observation'], fixture.pr,
                      pid=55, mode='rows', chain_id='diagnostic-original-chain',
                      key='diagnostic-original-key', outdir=out, revision='r1',
                      request=request, native=fixture.native, ax=fixture.ax)
        records = list((out / 'proof-replies').glob('before-*.json'))
        self.assertEqual(len(records), 1)
        saved = json.loads(records[0].read_text())
        self.assertEqual(saved['reply'], failure)
        self.assertEqual(saved['operation']['key'], 'diagnostic-original-key')
        self.assertEqual(saved['operation']['chain_id'], 'diagnostic-original-chain')
        self.assertEqual(saved['command']['op'], 'dom-region-proof')
        self.assertEqual(fixture.captured, 0)
        self.assertFalse(list(out.glob('*.png')))
        self.assertFalse(list((fixture.root / '.native-region-frame-state').glob('*.json')))

    def test_after_reply_retains_distinct_original_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            operation = {'key': 'same-key', 'chain_id': 'same-chain'}
            command = {'op': 'dom-region-proof'}
            first = {'ok': True, 'result': {'original': 'before'}}
            second = {'ok': False, 'error': 'original after error'}
            self.assertIs(r.record_region_reply(directory, 'before', operation, command, first), first)
            self.assertIs(r.record_region_reply(directory, 'after', operation, command, second), second)
            files = list((Path(directory) / 'proof-replies').glob('*.json'))
            self.assertEqual(len(files), 2)
            by_stage = {json.loads(p.read_text())['stage']: json.loads(p.read_text()) for p in files}
            self.assertEqual(by_stage['before']['reply'], first)
            self.assertEqual(by_stage['after']['reply'], second)
            self.assertFalse(list(Path(directory).glob('*.png')))


if __name__ == '__main__':
    unittest.main()
