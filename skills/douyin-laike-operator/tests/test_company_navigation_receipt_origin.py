"""Original acquisition authority is required; a byte copy is not journal provenance."""
import importlib.util,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'scripts'))
import prepare_company_navigation as n
spec=importlib.util.spec_from_file_location('company_navigation_origin_fixtures',HERE/'test_prepare_company_navigation.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
class ReceiptOriginTests(unittest.TestCase):
 def setUp(self):
  self.f=fixture.CompanyNavigationTests('test_legal_order_fixed_company_only_and_snapshot_bytes');self.f.setUp();self.addCleanup(self.f.doCleanups)
 def snapshot(self):
  p=self.f.root/'plan-snapshots/acquisition.snapshot.json';p.parent.mkdir();p.write_bytes(Path(self.f.primary['path']).read_bytes());return n.ref(str(p),n.digest(p))
 def test_legal_original_with_sibling_journal_and_independent_outdir(self):
  snapshot=self.snapshot();self.assertEqual(snapshot['sha256'],self.f.primary['sha256'])
  result=n.prepare(self.f.primary,**self.f.kw)
  self.assertEqual(result['binding']['source'],self.f.primary)
  self.assertEqual(result['source_journal_provenance'][0]['path'],str(Path(self.f.primary['path']).with_name('workflow.json')))
  self.assertNotEqual(Path(result['work_order_path']).parent,Path(snapshot['path']).parent)
 def test_snapshot_with_same_bytes_and_external_origin_metadata_is_not_receipt(self):
  snapshot=self.snapshot();meta={'path':snapshot['path'],'sha256':snapshot['sha256'],'original_path':self.f.primary['path']}
  (self.f.root/'plan-snapshots/origin.json').write_text(json.dumps(meta))
  with self.assertRaises(FileNotFoundError):n.prepare(snapshot,**self.f.kw)
  self.assertFalse(self.f.out.exists())
 def test_missing_original_sibling_journal_fails_before_creating_order(self):
  Path(self.f.primary['path']).with_name('workflow.json').unlink()
  with self.assertRaises(FileNotFoundError):n.prepare(self.f.primary,**self.f.kw)
  self.assertFalse(self.f.out.exists())
if __name__=='__main__':unittest.main()
