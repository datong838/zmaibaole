"""Actual030 source and031 dimensions, synthetic next preflight paint. No UI."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'))
import business_cells_capture as b
NODE='/Users/feibing/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
BASE=ROOT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class PartialPreview(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  script=r"""const fs=require('node:fs'),vm=require('node:vm');const file=process.argv[1],c={require,__dirname:require('node:path').dirname(file),console};vm.createContext(c);vm.runInContext(fs.readFileSync(file,'utf8').split("test('independent")[0]+'\nglobalThis.result=setup().run();',c);console.log(JSON.stringify(c.result));"""
  out=subprocess.check_output([NODE,'-e',script,str(ROOT/'skills/chrome-dom-export/tests/partial-cell-preview.test.cjs')],text=True)
  cls.proof=json.loads(out)['partial_cell_previews'][0]
  raw=json.loads((BASE/'screenshot-observations/030-row10-selection-failure-base-readonly.json').read_text());cls.base=raw['reply']['result'];cls.base['diagnostic_build']='viewport-notice-business-cells-v6';cls.base['partial_cell_previews']=[cls.proof]
  obs=json.loads(Path(raw['observation']['path']).read_text());cls.spec=b.spec(obs['tree'],cls.base['scope']['groupid'])
 def test_source_bound_all5_sidecar_validated_and_selectable_without_old_flags_change(self):
  base=copy.deepcopy(self.base);old=copy.deepcopy(base['business_cells']);out=b.validate_partial_previews(base,self.spec);self.assertIn(self.proof['notice_id'],out);rows=b.selectable_rows(base);self.assertIs(rows[-1],base['business_cells'][-1]);self.assertEqual(old,base['business_cells']);self.assertTrue(all(not c['geometry']['box_viewport_contained'] and not c['geometry']['evidence_eligible'] for c in rows[-1]['cells']))
 def test_malformed_source_and_omitted_paint_or_text_fail_closed(self):
  for kind in ('source','label','text','paint','bottom','ellipsis','sourceleaf','container','missingcell'):
   base=copy.deepcopy(self.base);p=base['partial_cell_previews'][0];cell=p['cells'][2]
   if kind=='source':p['notice_id']='wrong'
   if kind=='label':cell['platform_label_clips'][0]['own_ellipsis_active']=True
   if kind=='text':cell['text_ranges'][0]['visible_range']['bottom']=933
   if kind=='paint':cell['paint_bounds'][0]['bounds']['bottom']=933
   if kind=='bottom':cell['visible_box']['bottom']=933
   if kind=='ellipsis':cell['supported_ellipsis_selectors']=['unknown']
   if kind=='sourceleaf':cell['text_ranges']=cell['text_ranges'][:1]
   if kind=='container':p['container_selector']='unknown'
   if kind=='missingcell':p['cells'].pop()
   with self.subTest(kind=kind),self.assertRaises((ValueError,KeyError)):b.validate_partial_previews(base,self.spec)
 def test_sidecar_unknown_never_becomes_legacy_eligible(self):
  bad=copy.deepcopy(self.base);bad['partial_cell_previews'][0]['contract']='unknown'
  with self.assertRaises(ValueError):b.selectable_rows(bad)
  legacy=copy.deepcopy(self.base);legacy.pop('partial_cell_previews');self.assertNotIn(self.proof['notice_id'],[r['notice_id'] for r in b.selectable_rows(legacy)])
 def test_region_facts_require_exact_sidecar_and_preview_and_conservative_union(self):
  from unittest.mock import patch
  base=copy.deepcopy(self.base);p=base['partial_cell_previews'][0];boxes=[c['visible_box'] for c in p['cells']];region={k:fn(v[k] for v in boxes) for k,fn in [('left',min),('top',min),('right',max),('bottom',max)]};region.update(width=region['right']-region['left'],height=region['bottom']-region['top'])
  fragments={p['notice_id']:[{'field':c['field'],'text_complete_in_image':False} for c in p['cells']]}
  coverage={'contract':b.CONTRACT,'capture_subcontract':b.PARTIAL,'partial_cell_original_clips':[p],'notice_ids':[p['notice_id']],'date_filter_visible':False,'list_headers_visible':False,'cell_text_completeness':fragments}
  proof={'base_proof':base,'region_build':'region-notice-business-cells-v6','method':'public-DOM-evidence-region-proof','geometry_purpose':'evidence-crop-only','pixel_input_actions':False,'occlusion_verified':False,'quality_review_required':True,'paint_audit':{'contract':'public-DOM-business-paint-audit-v1','unpainted_count':0,'preserved_count':0,'unresolved_count':0,'roundoff_count':0},'evidence_contract':b.CONTRACT,'derived_business_coverage':coverage,'selectors':[c['selector'] for c in p['cells']],'region':region}
  # Base/source verification is exercised independently; this unit isolates the
  # region-only coverage/preview contract rather than forging a live receipt.
  with patch.object(b,'validate_base'):
   facts=b.facts(proof,{'business_spec':self.spec});self.assertEqual(facts['capture_subcontract'],b.PARTIAL);self.assertTrue(b.expected_visibility('rows',facts)['structural_bottom_omissions_acknowledged'])
   for kind in ('preview','rawcrop','coverage','oldbuild'):
    bad=copy.deepcopy(proof)
    if kind=='preview':bad['quality_review_required']=False
    if kind=='rawcrop':bad['region']['bottom']+=.2;bad['region']['height']+=.2
    if kind=='coverage':bad['derived_business_coverage'].pop('partial_cell_original_clips')
    if kind=='oldbuild':bad['region_build']='region-notice-business-cells-v5'
    with self.subTest(kind=kind),self.assertRaises(ValueError):b.facts(bad,{'business_spec':self.spec})
if __name__=='__main__':unittest.main()
