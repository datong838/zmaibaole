"""Synthetic TEMP observation revisions, fake public ports only; no business/UI."""
import sys,copy,unittest,importlib.util
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_region_capture.py').is_file() and (p/'run_tests.py').is_file())
sys.path[:0]=[str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/chrome-dom-export/tests'),str(R/'skills/negative-review-complaints/scripts')]
import review_region_capture as rr
spec=importlib.util.spec_from_file_location('observation_revision_fake_fixture',R/'skills/chrome-dom-export/tests/test_review_region_capture.py');fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
class Revision(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.RegionCaptureTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.b=self.f.f;self.b.root=self.b.root.resolve();self.out=self.b.root/'capture';self.out.mkdir();self.requests=[];self.epoch=34
  self.patcher=patch.object(rr.rc,'command_from_inputs',return_value=self.b.command);self.patcher.start();self.addCleanup(self.patcher.stop)
  self.command=rr.region_command(self.b.command);before=copy.deepcopy(self.f.region);before['base_proof']['epoch']=32;op={'kind':'normal-review-region-capture-v1','manifest':self.b.manifest,'outdir':str(self.out),'pid':55,'revision':'complaint-region-v1','replaces':None};cap={'backend':'screen-capture-kit','pid':55,**before['scope'],'url':before['url'],'captureKey':self.b.manifest['capture_key']+':region:'+op['revision']};geometry=rr.region.observe(cap,self.f.request,self.f.native,self.f.ax);original={'state':'unknown','operation':op,'intent_at':rr.rc.stamp(),'proof_before':before,'geometry_before':geometry};rr.nw.write_capture(cap,self.out/'raw-window.png',self.f.request,self.f.native)
  key=rr.rc.digest({'source':self.b.manifest['source']['sha256'],'review_keys':sorted(self.b.manifest['review_keys'])});self.state=self.b.root/'.review-region-state'/(key+'.json');self.state.parent.mkdir();rr.rc.atomic(self.state,original);self.old_ref=rr.rc.ref(self.state);self.archive=self.b.root/'original-region.json';rr.rc.atomic(self.archive,original);self.proof={'path':str(self.b.root/'reviewed-proof.json'),'sha256':'b'*64};post=self.b.root/'failed-post.json';rr.rc.atomic(post,{'observed_at':rr.rc.stamp()});self.p={'at':rr.rc.stamp(),'original_post':rr.rc.ref(post),'original_region':self.old_ref,'region_archive':rr.rc.ref(self.archive),'facts':{'new_operation':rr.observation_operation(op)}};self.original=original;self.new=rr.observation_operation(op);self.old={**original,'observation_revision':self.proof};rr.rc.atomic(self.state,self.old);self.raw=(self.out/'raw-window.png').read_bytes();self.meta=(self.out/'raw-window.json').read_bytes()
  self.auth=patch.object(rr,'observation_authorization',return_value=(self.p,self.original,self.new));self.auth.start();self.addCleanup(self.auth.stop)
 def request(self,c):
  self.requests.append(copy.deepcopy(c));r=self.f.request(c)
  if c['op']=='dom-region-proof':r['result']['base_proof']['epoch']=self.epoch
  return r
 def run_capture(self,request=None):return rr.capture(self.b.manifest,self.out,request or self.request,pid=55,revision='complaint-region-v1',native=self.f.native,ax=self.f.ax)
 def assert_old(self):self.assertEqual((self.out/'raw-window.png').read_bytes(),self.raw);self.assertEqual((self.out/'raw-window.json').read_bytes(),self.meta)
 def test_new_fresh_pair_and_native_revision_not_old_cached_raw(self):
  v=self.run_capture();self.assertEqual(self.f.native.count,2);self.assertNotEqual(v['capture_key'],self.original['operation']['manifest']['capture_key']+':region:complaint-region-v1');self.assertEqual(v['revision'],'complaint-region-v1.r1');self.assertEqual(v['proof_before']['base_proof']['epoch'],34);self.assertEqual(v['proof_before'],v['proof_after']);self.assertEqual(Path(v['capture_metadata']['path']).parent,Path(self.new['outdir']));self.assertTrue(rr.verify(self.out/'registration.json')['ok']);self.assert_old()
  self.run_capture(lambda c:(_ for _ in ()).throw(AssertionError('no read after known complete')));self.assertEqual(self.f.native.count,2)
 def test_new_after_difference_remains_unknown_no_second_capture_or_read(self):
  def changed(c):
   r=self.request(c)
   if c['op']=='dom-region-proof' and len([x for x in self.requests if x['op']=='dom-region-proof'])>1:r['result']['base_proof']['epoch']=35
   return r
  with self.assertRaisesRegex(ValueError,'dom-or-native-geometry-changed'):self.run_capture(changed)
  self.assertEqual(self.f.native.count,2);self.assertEqual(rr.rc.load(self.state),self.old);self.assert_old()
  with self.assertRaisesRegex(ValueError,'derivation-intent-required'):self.run_capture(lambda c:(_ for _ in ()).throw(AssertionError('unknown cannot read or capture')))
  self.assertEqual(self.f.native.count,2)
 def test_top_alias_commit_interruption_consumes_existing_child_only(self):
  real=rr.rc.atomic
  def fail(p,v):
   if Path(p)==self.state and v.get('state')=='complete':raise OSError('top seal interrupted')
   return real(p,v)
  with patch.object(rr.rc,'atomic',side_effect=fail),self.assertRaisesRegex(OSError,'seal interrupted'):self.run_capture()
  self.assertEqual(self.f.native.count,2);self.run_capture(lambda c:(_ for _ in ()).throw(AssertionError('child already complete')));self.assertEqual(self.f.native.count,2);self.assert_old()
 def test_unknown_before_derivation_never_repeats_capture(self):
  original=self.f.native.capture
  def fail(*args):original(*args);raise OSError('native result unknown')
  self.f.native.capture=fail
  with self.assertRaisesRegex(OSError,'native result unknown'):self.run_capture()
  n=self.f.native.count
  with self.assertRaisesRegex(ValueError,'derivation-intent-required'):self.run_capture(lambda c:(_ for _ in ()).throw(AssertionError('no repeated RPC')))
  self.assertEqual(self.f.native.count,n);self.assert_old()
 def test_partial_typed_alias_fields_cannot_fall_back_to_normal(self):
  self.run_capture();p=self.out/'registration.json';v=rr.rc.load(p)
  for key in ('observation_revision','revision_registration','observation_revision_contract'):
   changed=copy.deepcopy(v);changed.pop(key);rr.rc.atomic(p,changed)
   with self.subTest(key=key),self.assertRaisesRegex(ValueError,'typed-fields'):rr.verify(p)
 def test_changed_task_operation_or_duplicate_new_dir_rejected(self):
  with self.assertRaisesRegex(ValueError,'same-business-operation'):rr.capture(self.b.manifest,self.out,self.request,pid=56,revision='complaint-region-v1',native=self.f.native,ax=self.f.ax)
  d=Path(self.new['outdir']);d.mkdir(parents=True);(d/'foreign').write_text('not prior capture')
  with self.assertRaisesRegex(ValueError,'foreign-revision-output'):self.run_capture()
  self.assertEqual(self.f.native.count,1)
 def test_changed_child_or_old_native_bytes_rejected(self):
  self.run_capture();v=rr.rc.load(self.out/'registration.json');child=Path(v['revision_registration']['path']);child.write_bytes(child.read_bytes()+b' ')
  with self.assertRaises(ValueError):rr.verify(self.out/'registration.json')
 def test_preview_quality_approval_keeps_local_child_and_top_owner(self):
  # Synthetic preview shape, public unresolved background must still be approved.
  self.f.region.update(external_painted_overlap='unresolved',quality_review_required=True,unresolved_overlay=[{'classification':'unmeasured-presented-static-background'}]);self.run_capture();preview=self.out/'preview-registration.json';v=rr.rc.load(preview)
  with self.assertRaisesRegex(ValueError,'incomplete'):rr.verify(preview)
  a={'kind':'dom-review-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':rr.rc.ref(preview),'image':v['image'],'source_sha256':v['source']['sha256'],'review_keys':v['review_keys'],'field_visibility':dict.fromkeys(('score','body_visible_fragment','store','customer','action'),True),'reviewed_at':rr.rc.stamp()};att=self.b.root/'quality.json';rr.rc.atomic(att,a);rr.approve_preview(preview,rr.rc.ref(att));self.assertTrue(rr.verify(self.out/'registration.json')['ok']);self.assertEqual(self.f.native.count,2);self.assert_old()
 def test_fresh_before_must_postdate_reviewed_authorization(self):
  self.epoch=35;v=self.run_capture();self.assertEqual(v['proof_before']['base_proof']['epoch'],35);self.assertEqual(v['proof_before'],v['proof_after']);self.p['at']='2999-01-01T00:00:00+00:00'
  with self.assertRaisesRegex(ValueError,'new-before-must-follow-authorization'):rr.verify(self.out/'registration.json')
if __name__=='__main__':unittest.main()
