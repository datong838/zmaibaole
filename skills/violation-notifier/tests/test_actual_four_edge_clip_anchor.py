"""Replay actual saved0028/base; only native SCK/region DOM transport is fake.
No UI or real journal writes. The fake region covers the actual visible candidates.
"""
import unittest,importlib.util,json,copy,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
s=importlib.util.spec_from_file_location('manual_fixture',Path(__file__).with_name('test_manual_business_preview_v2.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;b=m.b
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ACTUAL=BASE/'region-evidence-business-cells-v1/page1-rows3/proof-replies/base-afe3bfd7e3a5eab2f156829f659f3d9f85308c59f82d621101a19b6d67072ae2.json'
class ActualClipAndAnchor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m.ManualPreviewV2.setUpClass()
  for key in ('source','job','query','q'):setattr(cls,key,getattr(m.ManualPreviewV2,key))
 def setUp(self):
  m.ManualPreviewV2.setUp(self);self.actual=json.loads(ACTUAL.read_text());self.current=self.actual['operation']['observation'];self.mode='rows';self.native.items[0]['kCGWindowBounds']={'X':0,'Y':30,'Width':1920,'Height':1104}
  def capture(cg,out):self.captured+=1;r.region.pillow().new('RGB',(1920,1104),(17,23,42)).save(out);return {'width':1920,'height':1104}
  self.native.capture=capture;self.ax=type('AX',(),{'observe':lambda _,scope:{'pid':55,'url':scope['url'],'AX_main_window':{'x':0,'y':30,'width':1920,'height':1104},'AX_webarea':{'x':0,'y':117,'width':1920,'height':1017},'webarea_contents_read':False,'geometry_purpose':'evidence-crop-only','input_actions_used':False}})()
 write=m.ManualPreviewV2.write
 geometry=m.ManualPreviewV2.geometry
 def inputs(self):return r.fc.page_inputs(self.src,self.current,self.pr,screenshot_anchor=self.anchor)
 def base(self,i):return copy.deepcopy(self.actual['reply']['result'])
 def request(self,c):
  i=self.inputs();p=self.base(i)
  if c['op']=='tabs':return {'ok':True,'result':[{'windowId':i['command']['windowId'],'focused':True,'tabs':[{'tabId':i['command']['tabId'],'windowId':i['command']['windowId'],'active':True,'allowed':True,'url':i['url'],'title':'来客'}]}]}
  if c['op']=='viewport-proof':return {'ok':True,'result':p}
  self.assertEqual(c['op'],'dom-region-proof');selected=c['selectors'];anchor=selected==[p['business_date']['selector'],*[h['selector'] for h in p['business_headers']]];groups=[row for row in p['manual_local_previews'] if all(cell['selector'] in selected for cell in row['cells'])];fields={row['notice_id']:[{'field':cell['field'],'text_complete_in_image':False} for cell in row['cells']] for row in groups}
  boxes=[cell['visible_box'] for row in groups for cell in row['cells']];roi={'left':min(x['left'] for x in boxes),'top':min(x['top'] for x in boxes),'right':max(x['right'] for x in boxes),'bottom':max(x['bottom'] for x in boxes)} if boxes else {'left':300,'top':100,'right':1800,'bottom':200};roi.update(width=roi['right']-roi['left'],height=roi['bottom']-roi['top'])
  return {'ok':True,'result':{'source':'local-dom-bridge','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'external_painted_overlap':False,'scope':p['scope'],'url':i['url'],'base_proof':p,'selectors':selected,'region':roi,'viewport':{'width':1920,'height':1017,'device_pixel_ratio':1,'visual_scale':1},'safety_version':p['safety_version'],'evidence_contract':b.CONTRACT,'region_build':'region-notice-business-cells-v9-manual-anchor-v2','occlusion_verified':False,'manual_preview_unresolved':True,'quality_review_required':True,'derived_business_coverage':{'contract':b.CONTRACT,'capture_subcontract':b.LOCAL,'notice_ids':[row['notice_id'] for row in groups],'date_filter_visible':anchor,'list_headers_visible':anchor,'cell_text_completeness':fields,'coverage_certified':False}}}
 def capture(self):return r.capture(self.src,self.current,self.pr,pid=55,mode=self.mode,chain_id='business-five-chain',key='original-manual-rows3',outdir=self.root/'rows3',revision='r1',screenshot_anchor=self.anchor,request=self.request,native=self.native,ax=self.ax)
 def test_actual_base_four_edges_id_reset_ancestry_through_pending_fake_native(self):
  self.assertEqual(hashlib.sha256(ACTUAL.read_bytes()).hexdigest(),'a1969c09ed39fdb1f289fa744a320492dee0c47e4aeb98884c3c5f530010d04f');i=self.inputs();base=self.base(i);b.validate_base(base,i);cmd=b.prepare_region_request(i,base,'rows',notice_ids=['ZS202610174754837331']);self.assertEqual(len(cmd['selectors']),5)
  value=self.capture();self.assertEqual(value['state'],'awaiting-visual-review');self.assertEqual(self.captured,1);meta=r.sr.document(r.ref(value['metadata']));self.assertIn('ZS202610174754837331',meta['notice_ids']);r.validate_frame(value['image'],meta,source=self.src,allow_preview=True)
  with self.assertRaisesRegex(ValueError,'quality-approval-required'):r.validate_frame(value['image'],meta,source=self.src)
 def test_actual_raw_visible_rectangles_stay_six_field_strict_and_clip_tamper_refused(self):
  i=self.inputs();base=self.base(i)
  for mode in ('raw4','clipnan','clipzero','notancestor','intersection'):
   bad=copy.deepcopy(base);cell=bad['manual_local_previews'][-1]['cells'][0]
   if mode=='raw4':cell['raw_box'].pop('width');cell['raw_box'].pop('height')
   elif mode=='clipnan':cell['ancestor_clips'][0]['box']['bottom']=float('nan')
   elif mode=='clipzero':cell['ancestor_clips'][0]['box']['bottom']=cell['ancestor_clips'][0]['box']['top']
   elif mode=='notancestor':cell['ancestor_clips'][0]['selector']='#governanceRoot > not-a-real-ancestor'
   else:cell['visible_box']['bottom']-=1;cell['visible_box']['height']-=1
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.validate_base(bad,i)
 def test_anchor_provider_only_strict_geometry_pending_and_approved_original_operation(self):
  # Geometry below is explicitly synthetic; actual rows/base remain the replay.
  self.mode='anchor';self.current=self.q['pages'][1]['observation'];oldbase=self.base
  def anchorbase(i):
   p=m.ManualPreviewV2.base(self,i);p['manual_local_previews']=[];p['manual_preview_viewport']={'width':1920,'height':1017};return p
  self.base=anchorbase;value=self.capture();self.assertEqual(value['state'],'awaiting-visual-review');meta=r.sr.document(r.ref(value['metadata']));self.assertEqual(meta['notice_ids'],[]);self.assertTrue(meta['date_filter_visible'] and meta['list_headers_visible']);facts=r.frame_facts(meta['public_dom_proof']['before'],r.metadata_inputs(meta));visibility=b.expected_visibility('anchor',facts);self.assertNotIn('original_platform_clipping_acknowledged',visibility);self.assertEqual(visibility['rows'],{})
  att=self.write('quality.json',{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(value['metadata']),'binding':r.quality_binding(meta),'field_visibility':visibility,'reviewed_at':r.stamp()});final=r.approve_preview(value['metadata'],att);self.assertEqual(final['state'],'complete');self.assertEqual(self.captured,1)
if __name__=='__main__':unittest.main()
