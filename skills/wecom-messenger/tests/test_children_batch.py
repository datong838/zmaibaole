"""Public AX response doubles only; never constructs a native OS client."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native


class ChildrenBatchTests(unittest.TestCase):
    def subject(self, slot=30, extended_error=0):
        n = native.Native.__new__(native.Native)
        n.refs = []
        n._attribute_batches = {('AXRole',): 10, ('AXRole', 'AXChildren'): 11}
        arrays = {20: [100, slot], 21: [100], 30: [301, 302]}
        calls = []

        def bulk(element, keys, options, out):
            calls.append((element, keys, options))
            if keys == 11 and extended_error:
                return extended_error
            out._obj.value = 20 if keys == 11 else 21
            return 0

        n.ax = SimpleNamespace(
            AXUIElementCopyMultipleAttributeValues=bulk,
            AXUIElementGetTypeID=lambda: 6,
            AXValueGetTypeID=lambda: 5,
            AXValueGetType=lambda value: 5,
        )
        n.cf = SimpleNamespace(
            CFGetTypeID=lambda value: 1 if value in arrays else 6 if value == 1 else 5 if value == 40 else 2,
            CFArrayGetTypeID=lambda: 1,
            CFArrayGetCount=lambda value: len(arrays[value]),
            CFArrayGetValueAtIndex=lambda value, index: arrays[value][index],
        )
        n.decode = lambda value: 'AXGroup' if value == 100 else self.fail('child handles must not be decoded')
        return n, arrays, calls

    def test_raw_children_order_and_outer_result_ownership(self):
        n, _, calls = self.subject()
        fields, children = n.node_attributes_and_children(1, ['AXRole'])
        self.assertEqual(fields, {'AXRole': 'AXGroup'})
        self.assertEqual(children, [301, 302])
        self.assertEqual(n.refs, [20])
        self.assertEqual(calls, [(1, 11, 0)])

    def test_nonarray_child_slot_requires_original_reader_not_empty_children(self):
        for slot in (0, 40, 99):
            with self.subTest(slot=slot):
                n, _, _ = self.subject(slot=slot)
                fields, children = n.node_attributes_and_children(1, ['AXRole'])
                self.assertEqual(fields, {'AXRole': 'AXGroup'})
                self.assertIs(children, native._CHILDREN_FALLBACK)

    def test_unsupported_extended_request_preserves_original_field_request(self):
        for error in (-25201, -25208):
            with self.subTest(error=error):
                n, _, calls = self.subject(extended_error=error)
                fields, children = n.node_attributes_and_children(1, ['AXRole'])
                self.assertEqual(fields, {'AXRole': 'AXGroup'})
                self.assertIs(children, native._CHILDREN_FALLBACK)
                self.assertEqual(calls, [(1, 11, 0), (1, 10, 0)])

    def test_second_read_uses_current_child_array(self):
        n, arrays, calls = self.subject()
        self.assertEqual(n.node_attributes_and_children(1, ['AXRole'])[1], [301, 302])
        arrays[30] = [305]
        self.assertEqual(n.node_attributes_and_children(1, ['AXRole'])[1], [305])
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
