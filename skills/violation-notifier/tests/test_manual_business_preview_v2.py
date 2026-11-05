"""Synthetic SCK/native transport; actual immutable source/schema. No live UI."""
import unittest,importlib.util,json,copy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
spec=importlib.util.spec_from_file_location('v2_helper_fixture',Path(__file__).with_name('test_business_cells_capture.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
r=fixture.r;b=fixture.b
import screenshot_identity as si
class ManualPreviewV2(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  fixture.BusinessCells.setUpClass()
  for key in ('source','job','query','q'):setattr(cls,key,getattr(fixture.BusinessCells,key))
 def setUp(self):
  fixture.BusinessCells.setUp(self);self.ellipsis=False;rawref=self.q['pages'][0]['observation'];nav=json.loads(self.nav_file.read_text());nav['observations']=[rawref];r.atomic(self.nav_file,nav);self.anchor=self.write('anchor.json',si.create(self.src,self.pr,rawref,chain_id='business-five-chain',pid=55))
 write=fixture.BusinessCells.write
 geometry=fixture.BusinessCells.geometry
 def inputs(self):return r.fc.page_inputs(self.src,self.q['pages'][0]['observation'],self.pr,screenshot_anchor=self.anchor)
 def base(self,i):
  p=fixture.BusinessCells.base(self,i);p.update(hash_contract='gov-records-provider-scope-v2',diagnostic_build='viewport-notice-business-cells-v9-provider-manual-preview-v2',preview_contract=b.MANUAL,manual_preview_viewport={'width':1440,'height':763},public_identity={'provider':self.profile['derivation'] and r.sr.document(self.src)['identity']['provider'],'actual_url':i['url'],'visible_card':None})
  row=p['business_cells'][0];cells=[]
  for j,c in enumerate(row['cells']):
   raw={'left':300+j*150,'right':450+j*150,'top':200,'bottom':400,'width':150,'height':200};cells.append({'index':j,'field':c['field'],'selector':c['selector'],'raw_box':raw,'visible_box':dict(raw),'ancestor_clips':[],'text_complete_in_image':False})
  p['manual_local_previews']=[{'contract':b.LOCAL,'notice_id':row['notice_id'],'tr_selector':row['tr_selector'],'cells':cells,'original_full_flags_unchanged':True,'decorative_paint':'unresolved','quality_review_required':True,'coverage_certified':False}];return p
 def request(self,c):
  i=self.inputs();p=self.base(i)
  if c['op']=='tabs':return fixture.BusinessCells.request(self,c)
  if c['op']=='viewport-proof':return {'ok':True,'result':p}
  self.assertEqual(c['op'],'dom-region-proof');row=p['business_cells'][0];coverage={'contract':b.CONTRACT,'capture_subcontract':b.LOCAL,'notice_ids':[row['notice_id']],'date_filter_visible':False,'list_headers_visible':False,'cell_text_completeness':{row['notice_id']:[{'field':c['field'],'text_complete_in_image':False} for c in row['cells']]},'coverage_certified':False}
  return {'ok':True,'result':{'source':'local-dom-bridge','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':p['scope'],'url':i['url'],'base_proof':p,'selectors':c['selectors'],'region':{'left':300,'top':200,'right':1050,'bottom':400,'width':750,'height':200},'viewport':{'width':1440,'height':763,'device_pixel_ratio':2,'visual_scale':1},'safety_version':p['safety_version'],'evidence_contract':b.CONTRACT,'region_build':'region-notice-business-cells-v8-manual-preview-v2','occlusion_verified':False,'derived_business_coverage':coverage,'manual_preview_unresolved':True,'quality_review_required':True}}
 def capture(self):return r.capture(self.src,self.q['pages'][0]['observation'],self.pr,pid=55,mode='rows',chain_id='business-five-chain',key='original-manual-rows3',outdir=self.root/'rows3',revision='r1',screenshot_anchor=self.anchor,request=self.request,native=self.native,ax=self.ax)
 def test_same_operation_pending_no_send_then_explicit_original_png_attestation(self):
  value=self.capture();self.assertEqual(value['state'],'awaiting-visual-review');self.assertEqual(self.captured,1);m=r.sr.document(r.ref(value['metadata']));self.assertEqual(m['pinned_inputs']['screenshot_anchor'],self.anchor)
  with self.assertRaisesRegex(ValueError,'quality-approval-required'):r.validate_frame(value['image'],m,source=self.src)
  facts=r.frame_facts(m['public_dom_proof']['before'],r.metadata_inputs(m));self.assertTrue(all(not c['text_complete_in_image'] for c in facts['cell_text_completeness'][m['notice_ids'][0]]));visibility=b.expected_visibility('rows',facts);self.assertTrue(visibility['unresolved_decorative_paint_acknowledged'])
  att=self.write('quality.json',{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(value['metadata']),'binding':r.quality_binding(m),'field_visibility':visibility,'reviewed_at':r.stamp()});final=r.approve_preview(value['metadata'],att);r.validate_frame(final['image'],r.sr.document(r.ref(final['metadata'])),source=self.src);self.assertEqual(self.captured,1)
 def test_unknown_original_cannot_bypass_with_v2_or_new_key(self):
  folder=self.root/'.native-region-frame-state';folder.mkdir();r.atomic(folder/(r.fc.fingerprint([self.src['sha256'],'business-five-chain'])+'.json'),{'scope':{'source_sha256':self.src['sha256'],'profile_sha256':self.pr['sha256'],'chain_id':'business-five-chain'},'frames':[{'state':'unknown','operation':{'key':'original-manual-rows3','outdir':str(self.root/'rows3')}}]})
  with self.assertRaisesRegex(ValueError,'original-operation|unknown'):self.capture()
  self.assertEqual(self.captured,0)
 def test_malformed_sidecar_and_complete_claim_refused(self):
  i=self.inputs();p=self.base(i)
  for mode in ('complete','crop','selector','missing'):
   bad=copy.deepcopy(p);v=bad['manual_local_previews'][0]
   if mode=='complete':v['coverage_certified']=True
   elif mode=='crop':v['cells'][0]['visible_box']['bottom']-=1;v['cells'][0]['visible_box']['height']-=1
   elif mode=='selector':v['cells'][0]['selector']=v['cells'][1]['selector']
   else:v['cells'].pop()
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.validate_base(bad,i)
if __name__=='__main__':unittest.main()
