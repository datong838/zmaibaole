import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('reconcile_bridge',Path(__file__).parents[1]/'scripts/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)


class ReconcileCommandTest(unittest.TestCase):
    def command(self):
        return {'op':'download-reconcile','tabId':9,'groupid':'123',
                'ticket':'2243af46-9390-47c2-a0ba-4f11dffc5f83','since':'2026-10-20T18:12:18Z',
                'filename':'门店评价_全部门店_2026_10_16-2026_10_19.xlsx'}
    def test_exact_original_scope_is_readable(self):
        c=self.command();self.assertEqual(b.validate_command(c),c)
    def test_no_arbitrary_file_url_or_forged_scope(self):
        for patch in [{'filename':'credentials.xlsx'},{'tabId':True},{'groupid':'123&x=1'},
                      {'since':'not-a-date'},{'ticket':'short'},{'url':'https://example.com'}]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                b.validate_command({**self.command(),**patch})
    def test_reconcile_scope_fields_are_not_general_commands(self):
        for op in ('tree','tabs','click'):
            with self.assertRaises(ValueError):b.validate_command({**self.command(),'op':op})


if __name__=='__main__':unittest.main()
