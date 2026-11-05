import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from native import Native
class SnapshotRetry(unittest.TestCase):
    def subject(self,results):
        n=Native.__new__(Native);self.calls=[]
        def once(**kwargs):self.calls.append(kwargs);return results.pop(0)
        n._tree_once=once;return n
    def failed(self,why):return {'truncated':True,'truncation_reason':why,'node_count':196}
    @patch('native.time.sleep')
    def test_stale_element_rebuilds_snapshot_not_action(self,sleep):
        n=self.subject([self.failed('batch-attribute-read-failed:-25202'),{'truncated':False,'node_count':379}])
        out=n.tree();self.assertFalse(out['truncated']);self.assertEqual(len(self.calls),2);sleep.assert_called_once_with(.25)
        self.assertEqual(out['readonly_retry_history'][0]['reason'],'batch-attribute-read-failed:-25202')
        self.assertLessEqual(self.calls[1]['timeout'],self.calls[0]['timeout'])
    @patch('native.time.sleep')
    def test_busy_attribute_and_window_race_are_bounded(self,sleep):
        n=self.subject([self.failed('batch-attribute-unavailable:AXValue:-25204')]*3)
        self.assertTrue(n.tree()['truncated']);self.assertEqual(len(self.calls),3)
        n=self.subject([self.failed('window-set-changed-during-read'),{'truncated':False}]);self.assertFalse(n.tree()['truncated'])
    @patch('native.time.sleep')
    def test_unknown_error_and_deadline_never_replayed(self,sleep):
        for why in ('deadline','batch-attribute-read-failed:-25201','batch-attribute-unavailable:AXValue:-25200','public-window-set-incomplete'):
            n=self.subject([self.failed(why)]);self.assertTrue(n.tree()['truncated']);self.assertEqual(len(self.calls),1)
        sleep.assert_not_called()
if __name__=='__main__':unittest.main()
