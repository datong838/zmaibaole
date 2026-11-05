import copy,io,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'));sys.path.insert(0,str(Path(__file__).resolve().parent))
import review_region_capture as rr
import review_registration as registration
import native_region_capture as nr
import bridge
import test_review_capture as fixtures
from test_native_window_capture import FakeNative
class RegionCaptureTests(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.ReviewCaptureTests();self.f.setUp();self.addCleanup(self.f.doCleanups);f=self.f
  self.native=FakeNative();self.native.items[0]['kCGWindowBounds']={'X':0,'Y':30,'Width':1440,'Height':850}
  def capture(cg,path):self.native.count+=1;nr.pillow().new('RGB',(2880,1700),(17,23,42)).save(path);return {'width':2880,'height':1700}
  self.native.capture=capture
  self.ax=type('AX',(),{'observe':lambda _,scope:{'pid':55,'url':scope['url'],'AX_main_window':{'x':0,'y':30,'width':1440,'height':850},'AX_webarea':{'x':0,'y':117,'width':1440,'height':763},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}})()
  self.region={'source':'local-dom-bridge','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':f.proof['scope'],'url':f.proof['url'],'base_proof':f.proof,'selectors':['#card'],'region':{'left':300,'top':200,'right':1100,'bottom':400,'width':800,'height':200},'viewport':{'width':1440,'height':763,'device_pixel_ratio':2,'visual_scale':1},'review_action':'投诉审核中','safety_version':f.proof['safety_version']}
 def request(self,c):
  if c['op']=='tabs':return {'ok':True,'result':[{'windowId':2,'focused':True,'tabs':[{'tabId':1,'windowId':2,'active':True,'allowed':True,'url':self.f.scope['url'],'title':'来客'}]}]}
  self.assertEqual(c['op'],'dom-region-proof');return {'ok':True,'result':copy.deepcopy(self.region)}
 def test_whole_raw_preserved_but_final_registration_is_verified_region_pixels(self):
  f=self.f
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command):
   v=rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='corrected-region-v1',native=self.native,ax=self.ax);checked=registration.validate(f.root/'region/registration.json',source_sha256=f.manifest['source']['sha256'],review_key=f.key)
   self.assertTrue(checked['region_derived']);self.assertFalse(checked['whole_window']);self.assertEqual(checked['image_scope'],'derived-dom-review-region');self.assertEqual(checked['image']['width'],1600);self.assertTrue((f.root/'region/raw-window.png').exists());self.assertEqual(self.native.count,1)
   rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='corrected-region-v1',native=self.native,ax=self.ax);self.assertEqual(self.native.count,1)
 def test_unknown_capture_cannot_switch_revision_or_replay(self):
  f=self.f
  def fail(*a):self.native.count+=1;raise ValueError('unknown window image')
  self.native.capture=fail
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command):
   with self.assertRaisesRegex(ValueError,'unknown window'):rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax)
   with self.assertRaisesRegex(ValueError,'unknown-no-recapture'):rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax)
   with self.assertRaisesRegex(ValueError,'original-operation'):rr.capture(f.manifest,f.root/'region2',self.request,pid=55,revision='r2',native=self.native,ax=self.ax)
  self.assertEqual(self.native.count,1)
 def test_correction_cannot_bypass_unknown_old_whole_capture(self):
  f=self.f;p=f.root/'.review-capture-state';p.mkdir();key=rr.rc.digest({'source':f.manifest['source']['sha256'],'review_keys':sorted(f.manifest['review_keys'])});(p/(key+'.json')).write_text(json.dumps({'state':'unknown'}))
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command),self.assertRaisesRegex(ValueError,'cannot-bypass-unknown'):rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax)
  self.assertEqual(self.native.count,0)
 def test_completed_parent_can_use_identical_evidence_copy_not_new_identity(self):
  f=self.f;p=f.root/'.review-capture-state';p.mkdir();value={'source':f.manifest['source'],'review_keys':f.manifest['review_keys']};original=f.root/'original-parent.json';copy_path=f.root/'parent-evidence-copy.json';original.write_text(json.dumps(value));copy_path.write_bytes(original.read_bytes());key=rr.rc.digest({'source':f.manifest['source']['sha256'],'review_keys':sorted(f.manifest['review_keys'])});(p/(key+'.json')).write_text(json.dumps({'state':'complete','registration':str(original),'registration_sha256':rr.rc.sha(original)}))
  with patch.object(registration,'verify',return_value={'ok':True}):rr.legacy_gate(f.manifest,rr.rc.ref(copy_path))
 def test_formal_bridge_schema_accepts_only_verified_region_base(self):
  cmd=rr.region_command(self.f.command);bridge.validate_command(cmd);cmd['purpose']='input-targeting'
  with self.assertRaises(ValueError):bridge.validate_command(cmd)
 def test_unresolved_background_preview_requires_bound_supervisor_approval_without_recapture(self):
  f=self.f;self.region.update(external_painted_overlap='unresolved',quality_review_required=True,unresolved_overlay=[{'classification':'unmeasured-presented-static-background','background_image':{'sha256':'a'*64,'source_kind':'non-data-uri'}}])
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command):
   v=rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax);preview=f.root/'region/preview-registration.json';original=preview.read_bytes()
   self.assertEqual(v['state'],'awaiting-visual-review');rr.verify(preview,allow_preview=True)
   with self.assertRaisesRegex(ValueError,'incomplete'):registration.validate(preview,source_sha256=f.manifest['source']['sha256'],review_key=f.key)
   rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax);self.assertEqual(self.native.count,1)
   a={'kind':'dom-review-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':rr.rc.ref(preview),'image':v['image'],'source_sha256':v['source']['sha256'],'review_keys':v['review_keys'],'field_visibility':dict.fromkeys(('score','body_visible_fragment','store','customer','action'),True),'reviewed_at':rr.rc.stamp()};att=f.root/'attestation.json';rr.rc.atomic(att,a)
   rr.approve_preview(preview,rr.rc.ref(att));self.assertEqual(preview.read_bytes(),original);self.assertTrue(rr.verify(f.root/'region/registration.json')['ok']);self.assertEqual(self.native.count,1)
   with self.assertRaisesRegex(ValueError,'state-mismatch'):rr.approve_preview(preview,rr.rc.ref(att))
 def test_preview_approval_rejects_wrong_image_or_invisible_fields(self):
  f=self.f;self.region.update(external_painted_overlap='unresolved',quality_review_required=True,unresolved_overlay=[{'classification':'unmeasured-presented-static-background'}])
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command):
   v=rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='r1',native=self.native,ax=self.ax);preview=f.root/'region/preview-registration.json'
   a={'kind':'dom-review-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':rr.rc.ref(preview),'image':dict(v['image'],sha256='f'*64),'source_sha256':v['source']['sha256'],'review_keys':v['review_keys'],'field_visibility':dict.fromkeys(('score','body_visible_fragment','store','customer','action'),True),'reviewed_at':rr.rc.stamp()};att=f.root/'attestation.json';rr.rc.atomic(att,a)
   with self.assertRaisesRegex(ValueError,'binding-mismatch'):rr.approve_preview(preview,rr.rc.ref(att))
   self.assertFalse((f.root/'region/registration.json').exists());self.assertEqual(self.native.count,1)
 def test_approval_cli_is_offline_and_uses_existing_preview_and_attestation(self):
  import contextlib
  f=self.f;att=f.root/'quality.json';att.write_text('{}');preview=f.root/'preview-registration.json'
  args=['review_region_capture.py','--approve-preview',str(preview),'--quality-attestation',str(att)]
  with patch.object(sys,'argv',args),patch.object(rr,'approve_preview',return_value={'state':'complete'}) as approve,patch.object(bridge,'request',side_effect=AssertionError('approval must not request browser')),contextlib.redirect_stdout(io.StringIO()):rr.main()
  approve.assert_called_once_with(str(preview),rr.rc.ref(att))
 def test_region_preserves_explicit_complete_list_base_without_fake_boundary(self):
  f=self.f;f.command['scope'].pop('boundary');f.command['scope'].update(scope_mode='verified-complete-normal-list',complete_list={'pager':'#pager','total':'#total','current':'#current','previous':'#previous','next':'#next'});f.proof['query'].pop('fold_boundary');f.proof['query'].update(scope_mode='verified-complete-normal-list',normal_list_complete=True,pagination={'total':1,'current':'1/1','previous_disabled':True,'next_disabled':True});bridge.validate_command(rr.region_command(f.command))
  with patch.object(rr.rc,'command_from_inputs',return_value=f.command):
   value=rr.capture(f.manifest,f.root/'region',self.request,pid=55,revision='complete-list-r1',native=self.native,ax=self.ax);self.assertEqual(value['state'],'complete');self.assertNotIn('fold_boundary',value['proof_before']['base_proof']['query']);self.assertTrue(rr.verify(f.root/'region/registration.json')['ok'])
 def test_cli_uses_formal_bridge_request(self):
  import contextlib
  f=self.f;manifest=f.root/'manifest.json';manifest.write_text(json.dumps(f.manifest));args=['review_region_capture.py','--manifest',str(manifest),'--outdir',str(f.root/'out'),'--pid','55','--revision','r1']
  def capture(manifest,out,request,**kwargs):request({'op':'ping','tabId':1});self.assertEqual(kwargs,{'pid':55,'revision':'r1','replaces':None});return {'image':{'path':'crop.png'},'image_scope':'derived-dom-review-region','state':'complete'}
  with patch.object(sys,'argv',args),patch.object(rr,'capture',side_effect=capture),patch.object(bridge,'request',return_value={'ok':True}) as request,contextlib.redirect_stdout(io.StringIO()):rr.main()
  request.assert_called_once_with({'op':'ping','tabId':1},timeout=50)
if __name__=='__main__':unittest.main()
