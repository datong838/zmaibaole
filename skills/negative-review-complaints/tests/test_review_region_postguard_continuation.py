"""Synthetic TEMP pixels and public-port shapes; no real UI, RPC or business state.
The authorization proof is mocked here; opt-in actual metadata tests deeply replay it.
"""
import sys,copy,unittest,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_region_capture.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/chrome-dom-export/tests'),str(R/'skills/negative-review-complaints/scripts')]
import review_region_capture as rr
spec=importlib.util.spec_from_file_location('postguard_synthetic_region_fixture',R/'skills/chrome-dom-export/tests/test_review_region_capture.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
class Continuation(unittest.TestCase):
 def setUp(self):
  self.f=fixture.RegionCaptureTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.base=self.f.f;self.base.root=self.base.root.resolve();self.out=self.base.root/'region';self.requests=[]
  self.command_patch=patch.object(rr.rc,'command_from_inputs',return_value=self.base.command);self.command_patch.start();self.addCleanup(self.command_patch.stop)
  def first(c):
   if c['op']=='dom-region-proof':
    self.requests.append(c)
    if len(self.requests)>1:return {'ok':False,'error':'capture-target-not-active-focused-stable-site'}
   return self.f.request(c)
  with self.assertRaisesRegex(ValueError,'capture-target-not-active'):rr.capture(self.base.manifest,self.out,first,pid=55,revision='r1',native=self.f.native,ax=self.f.ax)
  key=rr.rc.digest({'source':self.base.manifest['source']['sha256'],'review_keys':sorted(self.base.manifest['review_keys'])});self.state=self.base.root/'.review-region-state'/(key+'.json');self.original={k:rr.rc.load(self.state)[k] for k in ('state','operation','intent_at','proof_before','geometry_before')};rr.rc.atomic(self.state,self.original);self.raw=(self.out/'raw-window.png').read_bytes();self.meta=(self.out/'raw-window.json').read_bytes()
  self.original_ref=rr.rc.ref(self.state);self.archive=self.base.root/'original-region.json';rr.rc.atomic(self.archive,self.original);self.proof={'path':str(self.base.root/'proof.json'),'sha256':'f'*64};self.p={'original_region':self.original_ref,'region_archive':rr.rc.ref(self.archive)};self.facts=rr.original_complete_region(self.original,self.state)
  self.authpatch=patch.object(rr,'postguard_authorization',return_value=(self.p,self.original,self.facts));self.authpatch.start();self.addCleanup(self.authpatch.stop)
  self.old={**self.original,'postguard_continuation':self.proof};rr.rc.atomic(self.state,self.old)
  self.nativepatch=patch.object(rr.nw,'write_capture',side_effect=AssertionError('must not capture again'));self.nativepatch.start();self.addCleanup(self.nativepatch.stop)
 def run_continuation(self,request=None):return rr.capture(self.base.manifest,self.out,request or self.f.request,pid=55,revision='r1',native=self.f.native,ax=self.f.ax)
 def assert_unchanged(self):
  self.assertEqual(rr.rc.load(self.state),self.old);self.assertEqual((self.out/'raw-window.png').read_bytes(),self.raw);self.assertEqual((self.out/'raw-window.json').read_bytes(),self.meta);self.assertEqual(self.f.native.count,1)
 def test_complete_same_key_uses_real_raw_crop_no_recapture_and_checkpoint(self):
  v=self.run_continuation();self.assertEqual(v['state'],'complete');self.assertNotIn('proof_before_observed_at',v);self.assertEqual(v['proof_before_checkpoint_at'],self.original['intent_at']);self.assertEqual(v['proof_before_time_basis'],rr.CONTINUATION);self.assertTrue(rr.verify(self.out/'registration.json')['ok']);self.assertEqual((self.out/'raw-window.png').read_bytes(),self.raw);self.assertEqual(self.f.native.count,1)
  self.run_continuation(lambda c:(_ for _ in ()).throw(AssertionError('completed must not read')))
 def test_failed_reply_durable_before_checked_unknown_and_raw_unchanged(self):
  def fail(c):return {'ok':False,'error':'strict-current-guard'}
  with self.assertRaisesRegex(ValueError,'strict-current-guard'):self.run_continuation(fail)
  files=list((self.out/'postguard-continuations').rglob('post-reply.json'));self.assertEqual(len(files),1);self.assertEqual(rr.rc.load(files[0])['response'],{'ok':False,'error':'strict-current-guard'});self.assert_unchanged();self.assertFalse((self.out/'registration.json').exists())
 def test_any_DOM_difference_refuses_before_geometry(self):
  def changed(c):
   value=self.f.request(c)
   if c['op']=='dom-region-proof':value['result']['region']['left']+=1
   return value
  with patch.object(rr.region,'observe',side_effect=AssertionError('must reject DOM first')),self.assertRaisesRegex(ValueError,'DOM-changed'):self.run_continuation(changed)
  self.assert_unchanged()
 def test_new_geometry_persisted_before_exact_guard(self):
  g=copy.deepcopy(self.original['geometry_before']);g['CG_bounds']['width']+=1
  with patch.object(rr.region,'observe',return_value=g),self.assertRaisesRegex(ValueError,'geometry-changed'):self.run_continuation()
  files=list((self.out/'postguard-continuations').rglob('after-geometry.json'));self.assertEqual(rr.rc.load(files[0])['geometry'],g);self.assert_unchanged()
 def test_unknown_without_typed_authorization_cannot_continue(self):
  rr.rc.atomic(self.state,self.original)
  with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.run_continuation(lambda c:(_ for _ in ()).throw(AssertionError('no read')))
 def test_original_native_source_or_pixels_change_rejected(self):
  self.out.joinpath('raw-window.png').write_bytes(self.raw+b'changed')
  with self.assertRaisesRegex(ValueError,'png-hash'):rr.original_complete_region(self.original,self.state)
 def test_missing_or_noncomplete_native_metadata_rejected(self):
  for value in ('unknown','failed'):
   meta=rr.rc.load(self.out/'raw-window.json');meta['state']=value;rr.rc.atomic(self.out/'raw-window.json',meta)
   with self.assertRaisesRegex(ValueError,'metadata-incomplete'):rr.original_complete_region(self.original,self.state)
 def test_changed_operation_and_foreign_unknown_cannot_use_authorization(self):
  changed=copy.deepcopy(self.old);changed['operation']['pid']=56;rr.rc.atomic(self.state,changed)
  with self.assertRaisesRegex(ValueError,'original-operation'):self.run_continuation()
 def test_no_pretend_old_observed_time_or_checkpoint_mutation(self):
  self.run_continuation();p=self.out/'registration.json';v=rr.rc.load(p)
  for key,value in (('proof_before_observed_at',self.original['intent_at']),('proof_before_checkpoint_at','2000-01-01T00:00:00+00:00'),('proof_before_time_basis','fallback')):
   changed=copy.deepcopy(v);changed[key]=value;rr.rc.atomic(p,changed)
   with self.assertRaisesRegex(ValueError,'checkpoint-binding'):rr.verify(p)
 def test_output_write_crash_seals_existing_verified_registration_without_RPC(self):
  real=rr.rc.atomic
  def interrupted(path,v):
   if Path(path)==self.state and v.get('state')=='complete':raise OSError('simulated after registration before state')
   return real(path,v)
  with patch.object(rr.rc,'atomic',side_effect=interrupted),self.assertRaisesRegex(OSError,'simulated'):self.run_continuation()
  self.assert_unchanged();self.assertTrue((self.out/'registration.json').exists());self.run_continuation(lambda c:(_ for _ in ()).throw(AssertionError('no repeat post read')));self.assertEqual(rr.rc.load(self.state)['state'],'complete')
 def test_removed_type_key_cannot_fall_back_to_legacy_time(self):
  self.run_continuation();p=self.out/'registration.json';v=rr.rc.load(p)
  keys=('postguard_continuation','proof_before_checkpoint_at','proof_before_time_basis','postguard_attempt','postguard_reply','postguard_geometry')
  for key in keys:
   changed=copy.deepcopy(v);changed.pop(key);changed['proof_before_observed_at']=self.original['intent_at'];rr.rc.atomic(p,changed)
   with self.subTest(missing=key),self.assertRaisesRegex(ValueError,'typed-fields'):rr.verify(p)
  changed=copy.deepcopy(v)
  for key in keys:changed.pop(key)
  changed.update(proof_before_time_basis=rr.CONTINUATION,proof_before_observed_at=self.original['intent_at']);rr.rc.atomic(p,changed)
  with self.assertRaisesRegex(ValueError,'typed-fields'):rr.verify(p)
if __name__=='__main__':unittest.main()
