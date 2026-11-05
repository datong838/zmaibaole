"""Current-source pure/TEMP native focus regression; no UI, RPC or real capture."""
import sys,unittest,tempfile,copy,json
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts/review_capture_focus.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'skills/wecom-messenger/scripts')]
import review_capture_focus as m
import review_capture_tab as tab
import native_window_capture as nw
o=m.o
class Native:

    def __init__(self):
        self.counts = {}
        self.access = True
        self.items = [{'kCGWindowNumber': 1, 'kCGWindowOwnerPID': 123, 'kCGWindowOwnerName': 'Google Chrome', 'kCGWindowName': 'Title', 'kCGWindowLayer': 0, 'kCGWindowIsOnscreen': True, 'kCGWindowSharingState': 1}]

    def inc(self, k):
        self.counts[k] = self.counts.get(k, 0) + 1

    def preflight(self):
        self.inc('preflight')
        return self.access

    def process_path(self, pid):
        self.inc('process_path')
        return nw.EXE

    def windows(self):
        self.inc('windows')
        return self.items

    def capture(self, *a):
        raise AssertionError('no screenshot')
class Preflight(unittest.TestCase):

    def setUp(self):
        self.c = {'backend': nw.BACKEND, 'pid': 123, 'tabId': 2, 'windowId': 3, 'groupid': '4', 'url': 'https://life.douyin.com/p/user/reviews?groupid=4', 'captureKey': 'capture-key-123'}
        self.calls = []
        self.tabs = [{'windowId': 3, 'focused': True, 'tabs': [{'tabId': 2, 'windowId': 3, 'active': True, 'allowed': True, 'url': self.c['url'], 'title': 'Title'}]}]

    def request(self, c):
        self.calls.append(c)
        return {'ok': True, 'result': self.tabs}

    def test_same_reads_same_return_and_audit_before_guard(self):
        a = Native()
        b = Native()
        out = []
        with patch.object(nw, 'stamp', return_value='2026-10-24T00:00:00+00:00'):
            before = nw.preflight(self.c, self.request, a)
            after = nw.preflight(self.c, self.request, b, diagnostic=out.append)
        self.assertEqual(before, after)
        self.assertEqual(a.counts, b.counts)
        self.assertEqual(a.counts, {'preflight': 1, 'process_path': 1, 'windows': 1})
        self.assertEqual(self.calls, [{'op': 'tabs'}] * 2)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0]['components']['title_matches'])

    def test_mismatch_logged_from_same_inventory_before_unchanged_guard(self):
        a = Native()
        a.items[0]['kCGWindowName'] = '近期的下载记录'
        out = []
        with self.assertRaisesRegex(Exception, 'frontmost-pid-title-mismatch'):
            nw.preflight(self.c, self.request, a, diagnostic=out.append)
        self.assertEqual(len(out), 1)
        self.assertFalse(out[0]['components']['title_matches'])
        self.assertEqual(out[0]['frontmost_normal_window']['kCGWindowName'], '近期的下载记录')
        self.assertEqual(a.counts['windows'], 1)

    def test_writer_failure_stops_before_guard_or_capture(self):
        a = Native()
        with patch.object(nw, 'window_scope', side_effect=AssertionError('guard not reached')), self.assertRaisesRegex(OSError, 'disk-full'):
            nw.preflight(self.c, self.request, a, diagnostic=lambda d: (_ for _ in ()).throw(OSError('disk-full')))
        self.assertEqual(a.counts['windows'], 1)

    def test_original_read_guard_error_survives_writer_failure_once(self):
        a = Native()
        a.access = False
        writes = []

        def bad(d):
            writes.append(d)
            raise OSError('disk-full')
        with self.assertRaisesRegex(Exception, 'screen-capture-access-unavailable'):
            nw.preflight(self.c, self.request, a, diagnostic=bad)
        self.assertEqual(len(writes), 1)
        self.assertEqual(a.counts, {'preflight': 1})
        self.assertEqual(self.calls, [])

    def test_no_other_app_titles_in_diagnostic(self):
        a = Native()
        a.items.insert(0, {**a.items[0], 'kCGWindowNumber': 9, 'kCGWindowOwnerPID': 999, 'kCGWindowOwnerName': 'Other', 'kCGWindowName': 'Private', 'kCGWindowBounds': {}})
        out = []
        with self.assertRaisesRegex(Exception, 'frontmost-pid-title-mismatch'):
            nw.preflight(self.c, self.request, a, diagnostic=out.append)
        self.assertNotIn('kCGWindowName', out[0]['frontmost_normal_window'])
        self.assertNotIn('Private', str(out))
if __name__=="__main__":unittest.main()
