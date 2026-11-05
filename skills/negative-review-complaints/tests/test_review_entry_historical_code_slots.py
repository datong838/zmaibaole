"""Historical CODE archive slots: TEMP bytes only; no runtime/KB/UI/OCR."""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

R = next(p for p in Path(__file__).resolve().parents
         if (p / 'run_tests.py').is_file()
         and (p / 'skills/negative-review-complaints/scripts').is_dir())
sys.path[:0] = [str(R / 'skills/negative-review-complaints/scripts'),
                str(R / 'skills/workshop-director/scripts')]
import initial_ledger_recovery as h


class HistoricalCodeSlots(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='historical-code-slots-')
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name).resolve()
        root = h.o.PROJECT / 'skills'
        base = {str(root / 'negative-review-complaints/scripts/initial_ledger_recovery.py'),
                str(root / 'douyin-laike-operator/scripts/bridge-workflow.py')}
        capture = str(root / 'chrome-dom-export/scripts/review_capture.py')
        wrapper = str(root / 'negative-review-complaints/scripts/capture_review_region.py')
        native = {str(root / 'chrome-dom-export/scripts' / n) for n in
                  ('native_window_capture.py', 'native_region_capture.py', 'review_region_capture.py')}
        self.quality = str(root / 'negative-review-complaints/scripts/program_review_quality.py')
        self.slots = {0: set(), 2: base, 3: base | {capture},
                      4: base | {capture, wrapper},
                      7: base | {capture, wrapper} | native,
                      8: base | {capture, wrapper} | native | {self.quality}}
        self.archives = []
        for i, target in enumerate(sorted(self.slots[8])):
            path = self.folder / ('source-' + str(i))
            path.write_bytes(('immutable historical bytes ' + str(i)).encode())
            self.archives.append({'target': target, 'archive': h.o.ref(path)})

    def generation(self, size):
        archives = [a for a in self.archives if a['target'] in self.slots[size]]
        if size == 0:
            path = self.folder / 'unarchived'
            path.write_bytes(b'current reference fallback')
            self.assertEqual(h.review_entry_code_read(h.o.ref(path), archives), path.read_bytes())
        for item in archives:
            reference = {'path': item['target'], 'sha256': item['archive']['sha256']}
            self.assertEqual(h.review_entry_code_read(reference, archives),
                             Path(item['archive']['path']).read_bytes())

    def quality_reference(self):
        item = next(a for a in self.archives if a['target'] == self.quality)
        return {'path': self.quality, 'sha256': item['archive']['sha256']}, item

    def test_generation_0(self): self.generation(0)
    def test_generation_2(self): self.generation(2)
    def test_generation_3(self): self.generation(3)
    def test_generation_4(self): self.generation(4)
    def test_generation_7(self): self.generation(7)
    def test_generation_8(self): self.generation(8)

    def test_foreign_target_rejected(self):
        bad = copy.deepcopy(self.archives)
        bad[0]['target'] = str(self.folder / 'foreign')
        with self.assertRaisesRegex(ValueError, 'exact-historical-code-slots'):
            h.review_entry_code_read(self.quality_reference()[0], bad)

    def test_duplicate_target_rejected(self):
        bad = copy.deepcopy(self.archives)
        bad[0] = bad[1]
        with self.assertRaisesRegex(ValueError, 'exact-historical-code-slots'):
            h.review_entry_code_read(self.quality_reference()[0], bad)

    def test_missing_original_slot_rejected(self):
        # Seven entries including Q are not the reviewed original seven.
        bad = [a for a in self.archives if a['target'] !=
               str(h.o.PROJECT / 'skills/chrome-dom-export/scripts/native_window_capture.py')]
        with self.assertRaisesRegex(ValueError, 'exact-historical-code-slots'):
            h.review_entry_code_read(self.quality_reference()[0], bad)

    def test_wrong_reference_hash_rejected(self):
        reference, _ = self.quality_reference()
        reference['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'historical-code-sha'):
            h.review_entry_code_read(reference, self.archives)

    def test_same_size_archive_mutation_rejected(self):
        reference, item = self.quality_reference()
        path = Path(item['archive']['path'])
        original = path.read_bytes()
        path.write_bytes(b'X' + original[1:])
        self.assertEqual(path.stat().st_size, len(original))
        with self.assertRaisesRegex(ValueError, 'reference-changed'):
            h.review_entry_code_read(reference, self.archives)



class NineHistoricalCodeSlots(unittest.TestCase):
    setUp = HistoricalCodeSlots.setUp

    def nine(self):
        bridge = str(h.o.PROJECT / 'skills/douyin-laike-operator/scripts/bridge-workflow.py')
        path = self.folder / 'second-bridge'
        path.write_bytes(b'second reviewed bridge bytes')
        archives = copy.deepcopy(self.archives)
        archives.append({'target': bridge, 'archive': h.o.ref(path)})
        return bridge, archives

    def test_two_bridge_SHA_pairs_read_exact_bytes(self):
        bridge, archives = self.nine()
        for item in (a for a in archives if a['target'] == bridge):
            ref = {'path': bridge, 'sha256': item['archive']['sha256']}
            self.assertEqual(h.review_entry_code_read(ref, archives),
                             Path(item['archive']['path']).read_bytes())

    def test_pair_matching_independent_of_archive_order(self):
        bridge, archives = self.nine()
        for item in (a for a in archives if a['target'] == bridge):
            ref = {'path': bridge, 'sha256': item['archive']['sha256']}
            self.assertEqual(h.review_entry_code_read(ref, list(reversed(archives))),
                             Path(item['archive']['path']).read_bytes())

    def test_same_bridge_SHA_duplicate_rejected(self):
        bridge, archives = self.nine()
        original = next(a for a in archives[:-1] if a['target'] == bridge)
        archives[-1]['archive'] = copy.deepcopy(original['archive'])
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': bridge, 'sha256': original['archive']['sha256']}, archives)

    def test_duplicate_nonbridge_instead_of_second_bridge_rejected(self):
        bridge, archives = self.nine()
        archives[-1]['target'] = self.quality
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': bridge, 'sha256': archives[-1]['archive']['sha256']}, archives)

    def test_unknown_bridge_SHA_rejected(self):
        bridge, archives = self.nine()
        with self.assertRaisesRegex(ValueError, 'historical-code-sha'):
            h.review_entry_code_read({'path': bridge, 'sha256': '0' * 64}, archives)

    def test_second_bridge_same_size_mutation_rejected(self):
        bridge, archives = self.nine()
        item = archives[-1]
        path = Path(item['archive']['path'])
        original = path.read_bytes()
        path.write_bytes(b'X' + original[1:])
        self.assertEqual(path.stat().st_size, len(original))
        with self.assertRaisesRegex(ValueError, 'reference-changed'):
            h.review_entry_code_read({'path': bridge, 'sha256': item['archive']['sha256']}, archives)


class TenHistoricalCodeSlots(unittest.TestCase):
    setUp = HistoricalCodeSlots.setUp
    nine = NineHistoricalCodeSlots.nine

    def ten(self):
        bridge, archives = self.nine()
        ports = str(h.o.PROJECT / 'skills/negative-review-complaints/scripts/complaint_execution_ports.py')
        path = self.folder / 'ports-archive'
        path.write_bytes(b'unique reviewed ports archive')
        archives.append({'target': ports, 'archive': h.o.ref(path)})
        return bridge, ports, archives

    def test_exact_ten_all_pairs_and_order(self):
        bridge, ports, archives = self.ten()
        self.assertEqual(len(archives), 10)
        self.assertEqual({a['target'] for a in archives}, self.slots[8] | {ports})
        self.assertEqual(sum(a['target'] == bridge for a in archives), 2)
        self.assertEqual(sum(a['target'] == ports for a in archives), 1)
        for order in (archives, list(reversed(archives))):
            for item in archives:
                reference = {'path': item['target'], 'sha256': item['archive']['sha256']}
                self.assertEqual(h.review_entry_code_read(reference, order),
                                 Path(item['archive']['path']).read_bytes())

    def test_duplicate_ports_rejected(self):
        _, ports, archives = self.ten()
        next(a for a in archives if a['target'] == self.quality)['target'] = ports
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': ports, 'sha256': archives[-1]['archive']['sha256']}, archives)

    def test_second_quality_instead_of_ports_rejected(self):
        _, ports, archives = self.ten()
        archives[-1]['target'] = self.quality
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': ports, 'sha256': archives[-1]['archive']['sha256']}, archives)

    def test_third_bridge_instead_of_ports_rejected(self):
        bridge, _, archives = self.ten()
        archives[-1]['target'] = bridge
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': bridge, 'sha256': archives[-1]['archive']['sha256']}, archives)

    def test_unknown_ports_hash_rejected(self):
        _, ports, archives = self.ten()
        with self.assertRaisesRegex(ValueError, 'historical-code-sha'):
            h.review_entry_code_read({'path': ports, 'sha256': '0' * 64}, archives)

    def test_foreign_tenth_target_rejected(self):
        _, ports, archives = self.ten()
        archives[-1]['target'] = str(self.folder / 'foreign')
        with self.assertRaisesRegex(ValueError, 'exact-nine-or-ten-historical-code-slots'):
            h.review_entry_code_read({'path': ports, 'sha256': archives[-1]['archive']['sha256']}, archives)

    def test_ports_archive_same_size_mutation_rejected(self):
        _, ports, archives = self.ten()
        item = archives[-1]
        path = Path(item['archive']['path'])
        original = path.read_bytes()
        path.write_bytes(b'X' + original[1:])
        self.assertEqual(path.stat().st_size, len(original))
        with self.assertRaisesRegex(ValueError, 'reference-changed'):
            h.review_entry_code_read({'path': ports, 'sha256': item['archive']['sha256']}, archives)

if __name__ == '__main__':
    unittest.main()
