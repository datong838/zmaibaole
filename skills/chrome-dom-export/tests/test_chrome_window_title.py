"""Exact observed Chrome memory annotation, no fuzzy site-title matching."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import native_window_capture as n
import native_region_capture as r
class Titles(unittest.TestCase):
 def test_observed_actual_and_dynamic_GB_suffix_only(self):
  base=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/screenshot-observations/002-native-focus-readonly.json'
  proof=json.loads(base.read_text());actual=next(w['AXTitle'] for w in proof['windows'] if w['AXMain']);self.assertTrue(n.chrome_window_title(actual,'抖音来客'))
  for value in ('抖音来客','抖音来客 - Google Chrome','抖音来客 - 内存用量高 - 1.7 GB - Google Chrome','抖音来客 - 内存用量高 - 2 GB - Google Chrome','抖音来客 - 内存用量高 - 0.95 GB - Google Chrome','抖音来客 - 内存用量高 - 937 MB - Google Chrome','抖音来客 - 内存用量高 - 1,016 MB - Google Chrome','抖音来客 - 内存用量高 - 512 MB - Google Chrome'):
   with self.subTest(value=value):self.assertTrue(n.chrome_window_title(value,'抖音来客'))
 def test_other_sites_or_unknown_suffix_or_extra_text_rejected(self):
  for value in ('假抖音来客 - 内存用量高 - 1.7 GB - Google Chrome','抖音来客商城 - 内存用量高 - 1.7 GB - Google Chrome','抖音来客 - 内存用量高 - 1.7 GB - Google Chrome extra','抖音来客 - 内存用量高 - -1 GB - Google Chrome','抖音来客 - 内存用量高 - NaN GB - Google Chrome','抖音来客 - 内存用量高 - 1.7 MB - Google Chrome','抖音来客 - 内存用量高 - 1024 MB - Google Chrome','抖音来客 - 内存用量高 - 1,024 MB - Google Chrome','抖音来客 - 内存用量高 - 10,16 MB - Google Chrome','抖音来客 - 内存用量高 - 0 MB - Google Chrome','抖音来客 - 内存用量高 - 937MB - Google Chrome','抖音来客 - Other Chrome','抖音来客 - 内存用量高 - 1.7 GB - Google Chrome\n'):
   with self.subTest(value=value):self.assertFalse(n.chrome_window_title(value,'抖音来客'))
 def test_CG_match_keeps_identity_and_original_title_evidence(self):
  w={'kCGWindowNumber':77,'kCGWindowOwnerPID':55,'kCGWindowOwnerName':'Google Chrome','kCGWindowName':'抖音来客 - 内存用量高 - 1.7 GB - Google Chrome','kCGWindowLayer':0,'kCGWindowIsOnscreen':True,'kCGWindowSharingState':1}
  self.assertEqual(n.window_scope([w],55,'抖音来客')['kCGWindowName'],w['kCGWindowName'])
  with self.assertRaises(ValueError):n.window_scope([w],56,'抖音来客')
  with self.assertRaises(ValueError):n.window_scope([{**w,'kCGWindowName':'抖音来客 - 内存用量高 - 1.8 GB - Google Chrome'}],55,'抖音来客',w)
 def test_AX_observe_reuses_matcher_without_reading_page_contents(self):
  class Fake(r.Geometry):
   def __init__(self):self.root='root';self.pid=55;self.calls=[]
   def get(self,e,k):return {('root','AXFrontmost'):True,('win','AXMain'):True,('win','AXMinimized'):False,('win','AXTitle'):'抖音来客 - 内存用量高 - 1.7 GB - Google Chrome',('win','AXRole'):'AXWindow',('web','AXRole'):'AXWebArea'}.get((e,k))
   def children(self,e,key=None):
    self.calls.append((e,key));return ['win'] if e=='root' else ['web'] if e=='win' else (_ for _ in ()).throw(AssertionError('page descendants forbidden'))
   def url(self,e):return 'https://life.douyin.com/p/governance/violation_list?groupid=123'
   def frame(self,e):return {'x':0,'y':0,'width':1440,'height':850}
  f=Fake();out=f.observe({'title':'抖音来客','url':f.url('web')});self.assertFalse(out['webarea_contents_read']);self.assertFalse(any(c[0]=='web' for c in f.calls))
if __name__=='__main__':unittest.main()
