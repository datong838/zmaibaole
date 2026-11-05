"""Observed public home routing shape; no browser or network access."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'scripts/switch_read_recovery.py'
spec = importlib.util.spec_from_file_location('routing_read_recovery', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RoutingQueryTests(unittest.TestCase):
    scope = {'tab_id': 7, 'window_id': 8, 'initial_groupid': '123', 'groupid': '456'}

    def check(self, suffix, route='/p/home'):
        tab = {'tabId': 7, 'windowId': 8, 'allowed': True, 'active': False,
               'url': 'https://life.douyin.com' + route + '?' + suffix}
        return m.tab_scope([{'windowId': 8, 'focused': False, 'tabs': [tab]}], self.scope)

    def test_observed_home_metadata_accepts_target_without_focusing(self):
        result = self.check('groupid=456&life_biz_view_id=22&life_account_biz_ids=')
        self.assertEqual(result['groupid'], '456')
        self.assertFalse(result['active'])

    def test_original_single_groupid_still_accepts_old_and_target(self):
        for gid in ('123', '456'):
            self.assertEqual(self.check('groupid=' + gid)['groupid'], gid)

    def test_home_metadata_never_grants_other_or_duplicate_group(self):
        for suffix in ('groupid=123&life_biz_view_id=22&life_account_biz_ids=',
                       'groupid=999&life_biz_view_id=22&life_account_biz_ids=',
                       'groupid=456&groupid=456&life_biz_view_id=22&life_account_biz_ids='):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.check(suffix)

    def test_unknown_nonempty_missing_or_duplicate_metadata_rejected(self):
        for suffix in ('groupid=456&life_biz_view_id=23&life_account_biz_ids=',
                       'groupid=456&life_biz_view_id=22&life_account_biz_ids=secret',
                       'groupid=456&life_biz_view_id=22',
                       'groupid=456&life_biz_view_id=22&life_biz_view_id=22&life_account_biz_ids=',
                       'groupid=456&life_biz_view_id=22&life_account_biz_ids=&extra=1'):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                self.check(suffix)

    def test_metadata_does_not_extend_other_routes(self):
        with self.assertRaises(ValueError):
            self.check('groupid=456&life_biz_view_id=22&life_account_biz_ids=', '/p/life_comment/management')

if __name__ == '__main__':
    unittest.main()
