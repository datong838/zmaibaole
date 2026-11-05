import importlib.util,unittest
from pathlib import Path
from unittest.mock import patch
sp=importlib.util.spec_from_file_location('candidate_native_retry',(Path(__file__).with_name('native.py') if Path(__file__).with_name('native.py').exists() else Path(__file__).resolve().parents[1]/'scripts/native.py'));mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
class Retry(unittest.TestCase):
 def subject(self,results):
  n=mod.Native.__new__(mod.Native);self.calls=[]
  def once(**kw):self.calls.append(kw);return results.pop(0)
  n._tree_once=once;return n
 def failed(self,reason='scoped-required-array-unavailable:AXChildren'):return {'truncated':True,'truncation_reason':reason,'node_count':230}
 def test_exact_children_rebuilds_then_complete(self):
  with patch.object(mod.time,'sleep'):
   n=self.subject([self.failed(),{'truncated':False,'node_count':400}]);out=n.tree();self.assertFalse(out['truncated']);self.assertEqual(len(self.calls),2);self.assertLessEqual(self.calls[1]['timeout'],55)
 def test_three_failures_remain_incomplete(self):
  with patch.object(mod.time,'sleep'):
   n=self.subject([self.failed()]*3);self.assertTrue(n.tree()['truncated']);self.assertEqual(len(self.calls),3)
 def test_deadline_no_retry_and_other_array_not_retry(self):
  for reason in ['scoped-required-array-unavailable:AXWindows','deadline']:
   n=self.subject([self.failed(reason)]);self.assertTrue(n.tree()['truncated']);self.assertEqual(len(self.calls),1)
  with patch.object(mod.time,'monotonic',side_effect=[0,0,55]),patch.object(mod.time,'sleep') as sleep:
   n=self.subject([self.failed()]);self.assertTrue(n.tree()['truncated']);self.assertEqual(len(self.calls),1);sleep.assert_not_called()
if __name__=='__main__':unittest.main()
