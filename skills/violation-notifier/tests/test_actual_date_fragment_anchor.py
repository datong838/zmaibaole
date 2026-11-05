"""Actual052/base/current0032; real production region JS, fake native transport.
Source/profile copies and all state writes are temporary; not live acceptance.
"""
import unittest,importlib.util,subprocess,json,copy,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
s=importlib.util.spec_from_file_location('anchor_clip_fixture',Path(__file__).with_name('test_actual_four_edge_clip_anchor.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=m.r;b=m.b
ACTUAL=m.BASE/'region-evidence-business-cells-v1/page2-anchor/proof-replies/base-ca55ab1855b2c65427b4e39026c4fe3c086b50f3bd44a35e65323495dd878d67.json'
class DateFragmentAnchor(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  m.ActualClipAndAnchor.setUpClass()
  for key in ('source','job','query','q'):setattr(cls,key,getattr(m.ActualClipAndAnchor,key))
  node='/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node';cls.proof=json.loads(subprocess.check_output([node,str(ROOT/'skills/chrome-dom-export/tests/helpers/date-fragment-actual.cjs')]));cls.proof['safety_version']=r.SAFETY
 def setUp(self):
  m.ActualClipAndAnchor.setUp(self);self.actual=json.loads(ACTUAL.read_text());self.current=self.actual['operation']['observation'];self.mode='anchor'
 write=m.ActualClipAndAnchor.write
 geometry=m.ActualClipAndAnchor.geometry
 inputs=m.ActualClipAndAnchor.inputs
 base=m.ActualClipAndAnchor.base
 capture=m.ActualClipAndAnchor.capture
 def request(self,c):
  if c['op']=='dom-region-proof':self.assertEqual(c['selectors'],self.proof['selectors']);return {'ok':True,'result':copy.deepcopy(self.proof)}
  return m.ActualClipAndAnchor.request(self,c)
 def test_actual052_prepare_real_region_native_crop_pending_and_explicit_approved_chain_anchor(self):
  self.assertEqual(hashlib.sha256(ACTUAL.read_bytes()).hexdigest(),'8c3114603d3343016075a5c529e20c7009c7c39c35fe2c7315ccbef194a269b4');i=self.inputs();p=self.base(i);b.validate_base(p,i);cmd=b.prepare_region_request(i,p,'anchor');self.assertEqual(len(cmd['selectors']),6);self.assertFalse(p['business_date']['geometry']['evidence_eligible']);self.assertFalse(p['business_date']['geometry']['text_unclipped'])
  value=self.capture();self.assertEqual(value['state'],'awaiting-visual-review');meta=r.sr.document(r.ref(value['metadata']));self.assertFalse(meta['date_filter_visible']);self.assertFalse(meta['date_text_complete_in_image']);self.assertTrue(meta['date_visible_fragment_in_image']);self.assertTrue(meta['list_headers_visible']);self.assertFalse(meta['filters_visible']);self.assertEqual(meta['image_filter_coverage'],'date-fragment-only');self.assertEqual(meta['date_fragment_source_value'],'2026/10/16 ～ 2026/10/20');facts=r.frame_facts(meta['public_dom_proof']['before'],r.metadata_inputs(meta));visibility=b.expected_visibility('anchor',facts);self.assertFalse(visibility['date_and_header_labels']);self.assertFalse(visibility['date_text_complete_in_image']);self.assertTrue(visibility['date_visible_fragment_in_image']);self.assertTrue(visibility['five_header_labels_visible'])
  with self.assertRaises(ValueError):r.anchor_date_evidence(meta)
  att=self.write('quality.json',{'kind':'violation-frame-region-quality-attestation-v1','reviewer_role':'supervisor','decision':'approved','registration_preview':r.ref(value['metadata']),'binding':r.quality_binding(meta),'field_visibility':visibility,'reviewed_at':r.stamp()});final=r.approve_preview(value['metadata'],att);approved=r.sr.document(r.ref(final['metadata']));self.assertEqual(r.anchor_date_evidence(approved),'approved-source-bound-visible-date-fragment');self.assertEqual(self.captured,1)
  for mode in ('fullflag','value','unapproved','headers'):
   bad=copy.deepcopy(approved)
   if mode=='fullflag':bad['date_filter_visible']=True
   elif mode=='value':bad['date_fragment_source_value']='2026/10/01 ～ 2026/10/20'
   elif mode=='unapproved':bad['quality_attestation']=None
   else:bad['list_headers_visible']=False
   with self.subTest(mode=mode),self.assertRaises(ValueError):r.anchor_date_evidence(bad)
 def test_date_fragment_eligibility_is_narrow_and_fact_completeness_cannot_be_forged(self):
  i=self.inputs();p=self.base(i)
  for mode in ('viewport','css','vertical','otherselector','hidden','header'):
   bad=copy.deepcopy(p);g=bad['business_date']['geometry'];c=g['text_clips'][0]
   if mode=='viewport':g['box_viewport_contained']=False
   elif mode=='css':g['unsupported_css_absent']=False
   elif mode=='vertical':c['scroll_height']+=1
   elif mode=='otherselector':c['selector']='#other'
   elif mode=='hidden':g['rendered']=False
   else:bad['business_headers'][0]['geometry']['evidence_eligible']=False
   with self.subTest(mode=mode),self.assertRaises(ValueError):b.prepare_region_request(i,bad,'anchor')
  for key,val in (('date_filter_visible',True),('date_text_complete_in_image',True),('date_visible_fragment_in_image',False),('date_fragment_source_value','bad')):
   proof=copy.deepcopy(self.proof);proof['derived_business_coverage'][key]=val
   with self.subTest(key=key),self.assertRaises(ValueError):b.facts(proof,i)
if __name__=='__main__':unittest.main()
