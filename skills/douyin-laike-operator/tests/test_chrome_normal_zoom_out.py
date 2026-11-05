"""Only fake NativeZoom; saved public menu/observation fixtures, no UI."""
import copy,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('normal_zoom',ROOT/'skills/douyin-laike-operator/scripts/chrome-normal-zoom-out.py');z=importlib.util.module_from_spec(spec);spec.loader.exec_module(z)
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class Zoom(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.menu=self.ref(ROOT/'work/live-acceptance/violations/native-menu-diagnostics/native-zoom-menu-readonly.json');state=json.loads((BASE/'.records-region-navigation/7bb6a631114b5351e9d54b7370e2af2a8d4a38e63676a74c98fabee0a4118d2d/state.json').read_text());self.observation=state['last_observation'];self.out=self.base/'zoom.json';self.presses=0;self.constructed=0;self.crash=False;self.bad_scope=False
  outer=self
  class Fake:
   def __init__(self,pid):outer.constructed+=1;self.pid=pid
   def inspect(self,scope):return {'pid':self.pid,'url':'wrong' if outer.bad_scope else scope['url'],'webarea_contents_read':False,'AX_main_window':z.document(outer.menu)['main_window_geometry']}
   def press_once(self,scope):
    outer.presses+=1;assert outer.out.exists();assert json.loads(outer.out.read_text())['state']=='unknown'
    if outer.crash:raise ValueError('actual-outcome-unknown')
    return {'AXPress_return_code':0}
   def close(self):pass
  self.fake=Fake
 def ref(self,path):return {'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 def run_zoom(self):return z.run(86614,self.observation,self.menu,self.out,'single-zoom-test-v1',self.fake)
 def test_one_AXPress_then_no_replay_or_native_on_existing_intent(self):
  result=self.run_zoom();self.assertEqual(result['state'],'action-returned-awaiting-public-proof');self.assertFalse(result['effect_verified']);old=self.out.read_bytes();again=self.run_zoom();self.assertFalse(again['new_input']);self.assertEqual(self.presses,1);self.assertEqual(self.constructed,1);self.assertEqual(self.out.read_bytes(),old)
 def test_unknown_action_never_replays(self):
  self.crash=True
  with self.assertRaisesRegex(ValueError,'outcome-unknown'):self.run_zoom()
  old=self.out.read_bytes();self.assertEqual(self.run_zoom()['state'],'unknown');self.assertEqual(self.presses,1);self.assertEqual(self.out.read_bytes(),old)
 def test_scope_mismatch_refuses_before_intent(self):
  self.bad_scope=True
  with self.assertRaisesRegex(ValueError,'scope-changed'):self.run_zoom()
  self.assertFalse(self.out.exists());self.assertEqual(self.presses,0)
 def test_reviewed_disabled_or_duplicate_shrink_refuses(self):
  for mode in ('disabled','duplicate'):
   proof=copy.deepcopy(z.document(self.menu));items=proof['view_menu']['children'][0]['children'];item=next(x for x in items if x.get('AXTitle')=='缩小')
   if mode=='disabled':item['AXEnabled']=False
   else:items.append(copy.deepcopy(item))
   path=self.base/(mode+'.json');path.write_text(json.dumps(proof));self.menu=self.ref(path)
   with self.assertRaisesRegex(ValueError,'shrink-not-enabled'):self.run_zoom()
   self.assertEqual(self.presses,0);self.assertFalse(self.out.exists())
if __name__=='__main__':unittest.main()
