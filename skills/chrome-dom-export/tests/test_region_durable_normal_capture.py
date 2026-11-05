"""Synthetic TEMP PNGs with actual source validators; no UI/native/default bridge."""
import sys,unittest,copy,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_region_capture.py').is_file())
sys.path[:0]=[str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/chrome-dom-export/tests'),str(R/'skills/negative-review-complaints/scripts')]
import review_region_capture as rr
spec=importlib.util.spec_from_file_location('normal_v2_formal_fixture',R/'skills/chrome-dom-export/tests/test_review_region_capture.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
class DurableNormal(unittest.TestCase):
 def setUp(self):
  self.f=fixture.RegionCaptureTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.base=self.f.f;self.out=self.base.root.resolve()/'normal-v2';self.commands=[]
  p=patch.object(rr.rc,'command_from_inputs',return_value=self.base.command);p.start();self.addCleanup(p.stop)
  for owner,name in ((rr.nw,'PublicCGWindow'),(rr.bridge,'request')):
   p=patch.object(owner,name,side_effect=AssertionError('default OS/bridge prohibited'));p.start();self.addCleanup(p.stop)
 def request(self,c):self.commands.append(copy.deepcopy(c));return self.f.request(c)
 def capture(self,request=None):return rr.capture(self.base.manifest,self.out,request or self.request,pid=55,revision='r1',native=self.f.native,ax=self.f.ax)
 def state(self):return next((self.base.root/'.review-region-state').glob('*.json'))
 def no_read(self,*a,**k):raise AssertionError('local recovery must not read UI/capture')
 def crash_after_crop(self):
  original=rr.region.derive
  def crash(*a):original(*a);raise RuntimeError('after-local-crop')
  with patch.object(rr.region,'derive',side_effect=crash),self.assertRaisesRegex(RuntimeError,'after-local-crop'):self.capture()
 def test_normal_records_actual_before_after_geometry_native_refs_and_reentry(self):
  value=self.capture();j=rr.rc.load(self.state());self.assertEqual(j['journal_contract'],rr.NORMAL_V2);self.assertEqual(value['proof_before_observed_at'],rr.rc.document(j['before-reply.json'])['observed_at']);self.assertEqual(value['proof_after_observed_at'],rr.rc.document(j['after-reply.json'])['observed_at'])
  self.assertEqual(rr.rc.document(j['native_complete'])['metadata'],value['capture_metadata']);self.assertTrue(rr.verify(self.out/'registration.json')['ok']);self.assertEqual(self.f.native.count,1);self.assertEqual(value['normal_capture_contract'],rr.NORMAL_V2)
  for key in ('before-geometry.json','after-geometry.json'):
   doc=rr.rc.document(j[key]);self.assertLessEqual(doc['started_at'],doc['observed_at'])
  self.capture(self.no_read);self.assertEqual(self.f.native.count,1)
 def test_failed_before_reply_is_saved_before_checked_and_unknown_never_retries(self):
  with self.assertRaisesRegex(ValueError,'bad-before'):self.capture(lambda c:{'ok':False,'error':'bad-before'})
  j=rr.rc.load(self.state());self.assertEqual(rr.rc.document(j['before-reply.json'])['response'],{'ok':False,'error':'bad-before'});self.assertEqual(self.f.native.count,0)
  with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.capture(self.no_read)
 def test_failed_post_reply_preserves_nativecomplete_and_refuses_new_reads(self):
  seen=[]
  def request(c):
   if c['op']=='dom-region-proof':
    seen.append(c)
    if len(seen)==2:return {'ok':False,'error':'bad-after'}
   return self.request(c)
  with self.assertRaisesRegex(ValueError,'bad-after'):self.capture(request)
  j=rr.rc.load(self.state());self.assertIn('native_complete',j);self.assertEqual(rr.rc.document(j['after-reply.json'])['response']['error'],'bad-after');self.assertEqual(self.f.native.count,1)
  with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.capture(self.no_read)
 def test_transport_error_is_durable_without_faked_response(self):
  with self.assertRaisesRegex(TimeoutError,'synthetic'):self.capture(lambda c:(_ for _ in ()).throw(TimeoutError('synthetic')))
  doc=rr.rc.document(rr.rc.load(self.state())['before-reply.json']);self.assertNotIn('response',doc);self.assertEqual(doc['error']['type'],'TimeoutError');self.assertEqual(self.f.native.count,0)
 def test_real_fresh_geometry_difference_is_saved_not_copied(self):
  observe=rr.region.observe;seen=[]
  def changed(*a,**k):
   value=observe(*a,**k);seen.append(1)
   if len(seen)==2:value['CG_bounds']['width']+=1
   return value
  with patch.object(rr.region,'observe',side_effect=changed),self.assertRaisesRegex(ValueError,'geometry-changed'):self.capture()
  j=rr.rc.load(self.state());self.assertNotEqual(rr.rc.document(j['before-geometry.json'])['geometry'],rr.rc.document(j['after-geometry.json'])['geometry']);self.assertNotIn('derivation_intent',j)
 def test_crop_written_registration_missing_resumes_pixels_locally_once(self):
  self.crash_after_crop();raw=(self.out/'raw-window.png').read_bytes();crop=(self.out/'review-region.png').read_bytes();j=rr.rc.load(self.state());self.assertEqual(j['state'],'unknown');self.assertTrue(rr.rc.document(j['derivation_intent']))
  with patch.object(rr.nw,'write_capture',side_effect=self.no_read),patch.object(rr.region,'observe',side_effect=self.no_read),patch.object(rr.region,'derive',side_effect=self.no_read):value=self.capture(self.no_read)
  self.assertEqual(raw,(self.out/'raw-window.png').read_bytes());self.assertEqual(crop,(self.out/'review-region.png').read_bytes());self.assertEqual(self.f.native.count,1);self.assertEqual(value['state'],'complete');self.assertTrue(rr.verify(self.out/'registration.json')['ok'])
 def test_intent_written_before_crop_can_resume_only_pure_local_derivation(self):
  with patch.object(rr.region,'derive',side_effect=RuntimeError('before-crop')),self.assertRaisesRegex(RuntimeError,'before-crop'):self.capture()
  self.assertFalse((self.out/'review-region.png').exists())
  with patch.object(rr.nw,'write_capture',side_effect=self.no_read),patch.object(rr.region,'observe',side_effect=self.no_read):self.capture(self.no_read)
  self.assertEqual(self.f.native.count,1)
 def test_foreign_crop_pixels_refuse_registration(self):
  self.crash_after_crop();path=self.out/'review-region.png';Image=rr.region.pillow()
  with Image.open(path) as old:size=old.size
  Image.new('RGB',size,(200,0,0)).save(path)
  with self.assertRaisesRegex(ValueError,'pixels-not-original'):self.capture(self.no_read)
  self.assertEqual(rr.rc.load(self.state())['state'],'unknown');self.assertFalse((self.out/'registration.json').exists())
 def test_raw_or_evidence_mutation_refuses_local_resume(self):
  self.crash_after_crop();p=self.out/'raw-window.png';p.write_bytes(p.read_bytes()+b'changed')
  with self.assertRaisesRegex(ValueError,'png-hash'):self.capture(self.no_read)
  self.assertFalse((self.out/'registration.json').exists())
 def test_unknown_missing_intent_cannot_trust_existing_crop(self):
  self.crash_after_crop();p=self.state();j=rr.rc.load(p);j.pop('derivation_intent');rr.rc.atomic(p,j)
  with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):self.capture(self.no_read)
 def test_complete_registration_before_state_save_can_seal_locally(self):
  atomic=rr.rc.atomic
  def crash(path,value):
   if Path(path).parent.name=='.review-region-state' and value.get('state')=='complete':raise OSError('after-registration')
   return atomic(path,value)
  with patch.object(rr.rc,'atomic',side_effect=crash),self.assertRaisesRegex(OSError,'after-registration'):self.capture()
  self.assertTrue((self.out/'registration.json').exists());self.capture(self.no_read);self.assertEqual(rr.rc.load(self.state())['state'],'complete');self.assertEqual(self.f.native.count,1)
 def test_version_field_removal_and_mixed_checkpoint_contract_refuse(self):
  self.capture();p=self.out/'registration.json';value=rr.rc.load(p)
  for field in rr.NORMAL_FIELDS:
   changed=copy.deepcopy(value);changed.pop(field);rr.rc.atomic(p,changed)
   with self.assertRaisesRegex(ValueError,'complete-typed'):rr.verify(p)
  changed=copy.deepcopy(value);changed['postguard_continuation']={'path':'/not-used','sha256':'0'*64};rr.rc.atomic(p,changed)
  with self.assertRaisesRegex(ValueError,'complete-typed'):rr.verify(p)
 def test_saved_actual_before_time_cannot_be_replaced(self):
  self.capture();p=self.out/'registration.json';value=rr.rc.load(p);value['proof_before_observed_at']='2000-01-01T00:00:00+00:00';rr.rc.atomic(p,value)
  with self.assertRaisesRegex(ValueError,'evidence-binding'):rr.verify(p)
 def test_stage_evidence_changes_are_not_trusted(self):
  self.crash_after_crop();j=rr.rc.load(self.state());p=Path(j['after-reply.json']['path']);p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(ValueError,'review-pinned-document-changed'):self.capture(self.no_read)
  self.assertFalse((self.out/'registration.json').exists())
 def test_identical_byte_symlink_crop_is_not_a_canonical_output(self):
  self.crash_after_crop();p=self.out/'review-region.png';other=self.out/'foreign.png';other.write_bytes(p.read_bytes());p.unlink();p.symlink_to(other)
  with self.assertRaisesRegex(ValueError,'canonical-path'):self.capture(self.no_read)
 def test_new_contract_cannot_drop_all_markers_into_legacy_branch(self):
  self.capture();p=self.out/'registration.json';v=rr.rc.load(p)
  for key in rr.NORMAL_FIELDS:v.pop(key)
  rr.rc.atomic(p,v)
  with self.assertRaisesRegex(ValueError,'complete-typed'):rr.verify(p)
if __name__=='__main__':unittest.main()
