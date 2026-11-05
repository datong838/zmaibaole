"""Portable public metadata ports; no real AppKit, AX, CG, RPC or input."""
import sys,unittest,tempfile,copy,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/negative-review-complaints/scripts/review_capture_focus.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'skills/wecom-messenger/scripts')]
import review_capture_focus as m
o=m.o;tab=m.previous;nw=m.nw
spec=importlib.util.spec_from_file_location('freshness_portable_native_fixture',R/'skills/negative-review-complaints/tests/test_review_native_app_focus_stage.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
class App:
 def __init__(self,ns=999,broken=False):self.ns=ns;self.broken=broken;self.closed=False;self.objc=type('O',(),{'objc_getClass':lambda s,n:1})()
 def identity(self,pid):return {'pid':pid,'bundle':'com.google.Chrome','terminated':False}
 def send(self,target,name,result):
  if self.broken:raise RuntimeError('diagnostic-only unavailable')
  return self.ns if name=='processIdentifier' else 1
 def close(self):self.closed=True
class CG:
 def __init__(self,pid=123):self.count=0;self.items=[{'kCGWindowNumber':4,'kCGWindowOwnerPID':pid,'kCGWindowOwnerName':'Google Chrome' if pid==123 else 'Other','kCGWindowName':'private-title-if-other','kCGWindowLayer':0,'kCGWindowIsOnscreen':True}]
 def process_path(self,pid):return nw.EXE
 def windows(self):self.count+=1;return self.items
class AX:
 def __init__(self,value=True,error=0,present=True):self.value={'AX_error':error,'present':present,'value':value};self.closed=False
 def frontmost_metadata(self):return self.value
 def close(self):self.closed=True
class Freshness(unittest.TestCase):
 def read(self,app=None,cg=None,ax=None):return m.front_identity(123,app_port=app or App(),cg_port=cg or CG(),ax_port=ax or AX())
 def test_fresh_AX_CG_agree_despite_stale_NS_diagnostic(self):
  cg=CG();app=App(999);ax=AX();r=self.read(app,cg,ax);self.assertEqual(r['frontmost_pid'],123);self.assertEqual(r['nsworkspace_frontmost_pid'],999);self.assertEqual(r['frontmost_source'],m.FRONT_SOURCE);self.assertTrue(app.closed and ax.closed);self.assertEqual(cg.count,1)
 def test_external_authority_requires_AX_false_and_other_CG(self):
  r=self.read(App(123),CG(999),AX(False));self.assertEqual(r['frontmost_pid'],999);self.assertNotIn('private-title-if-other',str(r))
 def test_AX_error_missing_or_non_boolean_never_false_or_ready(self):
  for ax in (AX(None,-25204,False),AX(None,0,False),AX(1),AX(None),AX(False,-25212),AX(True,False)):
   with self.subTest(ax=ax.value):r=self.read(App(123),CG(),ax);self.assertIsNone(r['frontmost_pid']);self.assertIn('frontmost_error',r)
 def test_CG_missing_or_mismatched_AX_never_NS_fallback(self):
  for cg,ax in ((CG(999),AX(True)),(CG(),AX(False))):
   r=self.read(App(123),cg,ax);self.assertIsNone(r['frontmost_pid']);self.assertIn('evidence-conflict',r['frontmost_error'])
  cg=CG();cg.items=[];r=self.read(App(123),cg,AX());self.assertIsNone(r['frontmost_pid'])
 def test_NS_diagnostic_error_does_not_prevent_public_authority(self):
  r=self.read(App(broken=True));self.assertEqual(r['frontmost_pid'],123);self.assertEqual(r['nsworkspace_error']['type'],'RuntimeError')
 def fixture(self):
  case=base.Stage();case.setUp();self.addCleanup(case.doCleanups);case.create_original_browser_confirmed();return case
 def test_legacy_NS_observation_unchanged_and_native_unknown_readonly_closes(self):
  case=self.fixture();before=o.doc(o.ref(case.path()));old_ref=before['events'][0]['before'];old_bytes=o.raw(old_ref)
  with self.assertRaises(RuntimeError):case.ensure(lambda p:(_ for _ in ()).throw(RuntimeError('native reply lost')))
  count=case.presses()
  with patch.object(case,'reader',side_effect=lambda pid:self.read()):r=case.ensure(lambda pid:(_ for _ in ()).throw(AssertionError('no reactivation')))
  self.assertTrue(r['ready']);self.assertFalse(r['input_dispatched']);self.assertEqual(case.presses(),count);self.assertEqual(o.raw(old_ref),old_bytes);self.assertNotIn('frontmost_source',o.doc(old_ref));state=o.doc(o.ref(case.path()));self.assertEqual(state['events'][0]['native_focus']['state'],'complete');self.assertEqual(o.doc(state['events'][0]['after'])['frontmost_source'],m.FRONT_SOURCE)
 def test_unknown_native_public_conflict_stays_unknown_without_input(self):
  case=self.fixture()
  with self.assertRaises(RuntimeError):case.ensure(lambda p:(_ for _ in ()).throw(RuntimeError('native reply lost')))
  count=case.presses()
  with patch.object(case,'reader',side_effect=lambda pid:self.read(App(123),CG(999),AX(True))),self.assertRaisesRegex(ValueError,'evidence-conflict'):case.ensure(lambda p:(_ for _ in ()).throw(AssertionError('no activation')))
  self.assertEqual(case.presses(),count);self.assertEqual(o.doc(o.ref(case.path()))['events'][0]['native_focus']['state'],'unknown')
if __name__=='__main__':unittest.main()
