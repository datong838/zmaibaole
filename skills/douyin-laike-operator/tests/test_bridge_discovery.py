import importlib.util
from pathlib import Path
import tempfile
import unittest

s=importlib.util.spec_from_file_location('discovery',Path(__file__).resolve().parents[1]/'scripts/bridge-discovery.py');d=importlib.util.module_from_spec(s);s.loader.exec_module(d)
class DiscoveryTest(unittest.TestCase):
 def run_case(self, *, ambiguous=False, failure=False, truncated=False):
  calls=[]
  def fake(c):
   calls.append(c)
   op=c['op']
   if op=='tabs':return [{'tabs':[{'tabId':7,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=1767942028615694'}]}]
   if op=='ping':return {'version':d.VERSION,'safety':'DOM-only'}
   if op=='tree':return {'truncated':truncated,'root':{}}
   if op=='find':return [{'disabled':False}]*(2 if ambiguous else 1)
   if op=='click':
    if failure:raise RuntimeError('lost response')
    return {'clicked':True}
  return fake,calls
 def test_once_and_idempotent(self):
  f,c=self.run_case()
  with tempfile.TemporaryDirectory() as p:
   a=d.execute(7,'1767942028615694',p,'切换公司',f);b=d.execute(7,'1767942028615694',p,'切换公司',f)
   self.assertEqual(a,b);self.assertEqual(a['status'],'complete');self.assertEqual(sum(x['op']=='click' for x in c),1)
 def test_unknown_never_replayed(self):
  f,c=self.run_case(failure=True)
  with tempfile.TemporaryDirectory() as p:
   self.assertEqual(d.execute(7,'1767942028615694',p,'切换公司',f)['status'],'unknown');d.execute(7,'1767942028615694',p,'切换公司',f)
   self.assertEqual(sum(x['op']=='click' for x in c),1)
 def test_ambiguous_stops(self):
  f,c=self.run_case(ambiguous=True)
  with tempfile.TemporaryDirectory() as p,self.assertRaisesRegex(RuntimeError,'not-unique'):d.execute(7,'1767942028615694',p,'切换公司',f)
  self.assertFalse(any(x['op']=='click' for x in c))
 def test_truncation_stops(self):
  f,c=self.run_case(truncated=True)
  with tempfile.TemporaryDirectory() as p,self.assertRaisesRegex(RuntimeError,'untruncated'):d.execute(7,'1767942028615694',p,'切换公司',f)
  self.assertFalse(any(x['op']=='click' for x in c))
 def test_no_confirm_allowed(self):
  f,c=self.run_case()
  with tempfile.TemporaryDirectory() as p,self.assertRaisesRegex(RuntimeError,'not-allowed'):d.execute(7,'1767942028615694',p,'确认',f)
  self.assertEqual(c,[])
 def test_group_mismatch_stops(self):
  f,c=self.run_case()
  with tempfile.TemporaryDirectory() as p,self.assertRaisesRegex(RuntimeError,'groupid-mismatch'):d.execute(7,'1764303851132943',p,'切换公司',f)
  self.assertFalse(any(x['op']=='click' for x in c))
if __name__=='__main__':unittest.main()
