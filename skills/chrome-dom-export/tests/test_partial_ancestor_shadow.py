"""Actual036 style in original source, synthetic ancestor bounds only. No UI."""
import copy,json,subprocess,unittest
from pathlib import Path
from test_partial_cell_preview import PartialPreview,ROOT,NODE,b
class AncestorShadow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  PartialPreview.setUpClass();cls.base=copy.deepcopy(PartialPreview.base);cls.spec=PartialPreview.spec
  script=r'''const fs=require('node:fs'),vm=require('node:vm');const file=process.argv[1],c={require,__dirname:require('node:path').dirname(file),console};vm.createContext(c);vm.runInContext(fs.readFileSync(file,'utf8').split("test('actual036")[0]+'\nglobalThis.result=setup().run();',c);console.log(JSON.stringify(c.result));'''.replace('\\"','"').replace("\\\\n","\\n")
  cls.proof=json.loads(subprocess.check_output([NODE,'-e',script,str(ROOT/'skills/chrome-dom-export/tests/partial-ancestor-shadow.test.cjs')],text=True))['partial_cell_previews'][0];cls.base.update(diagnostic_build='viewport-notice-business-cells-v7',partial_cell_previews=[cls.proof])
 def test_actual_style_explicit_safe_box_and_source_ancestor_proof(self):
  p=b.validate_partial_previews(self.base,self.spec);self.assertEqual(len(p),1);facts={'capture_subcontract':b.PARTIAL,'partial_cell_original_clips':[self.proof],'cell_text_completeness':{}};self.assertTrue(b.expected_visibility('rows',facts)['structural_ancestor_shadow_preserved_acknowledged'])
 def test_shadow_cannot_be_forged_via_geometry_source_or_legacy_version(self):
  for mode in ('inset','wrong-style','unknown-radius','moved-safe','outside','unbound-source','legacy','not-original'):
   base=copy.deepcopy(self.base);spec=copy.deepcopy(self.spec);shadow=base['partial_cell_previews'][0]['preserved_ancestor_shadows'][0]
   if mode=='inset':shadow['inset']=True
   if mode=='wrong-style':shadow['box_shadow']='none'
   if mode=='unknown-radius':shadow['radii']['TopLeft']['raw']='5%'
   if mode=='moved-safe':shadow['safe_box']['bottom']+=1;shadow['safe_box']['height']+=1
   if mode=='outside':base['partial_cell_previews'][0]['cells'][0]['raw_box']['left']=0
   if mode=='unbound-source':spec['partial_source']['structural_ancestors']={}
   if mode=='legacy':base['diagnostic_build']='viewport-notice-business-cells-v6'
   if mode=='not-original':shadow['original_pixels_preserved']=False
   with self.subTest(mode=mode),self.assertRaises((ValueError,KeyError)):b.validate_partial_previews(base,spec)
if __name__=='__main__':unittest.main()
