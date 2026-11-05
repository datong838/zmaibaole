"""Immutable result orders; synthetic inputs, no browser or messenger."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_observation as normal
import prepare_result_orders as p
import test_normal_observation as fixtures
class ResultOrderTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.NormalObservationTests();self.f.setUp();self.addCleanup(self.f.doCleanups);self.root=self.f.f.root
        self.f.job.update(source_receipt=str(self.f.f.receipt_path),source_receipt_sha256=self.f.f.receipt_hash)
        self.paths={k:self.root/(k+'.json') for k in ('job','source','envelope','profile')};self.out=self.root/'result-orders.json';self.write()
    def write(self):
        source=self.f.joined()
        for key,obj in [('job',self.f.job),('source',source),('envelope',self.f.envelope),('profile',self.f.profile)]:self.paths[key].write_text(json.dumps(obj))
    def prepare(self):return p.prepare(*(self.paths[k] for k in ('job','source','envelope','profile')),self.out)
    def test_exact_current_inputs_generate_idempotent_readonly_order(self):
        result=self.prepare();self.assertEqual(self.prepare(),result);self.assertEqual(len(result['orders']),1);self.assertFalse(result['submission_enabled']);self.assertEqual(result['orders'][0]['click_kind'],'complaint-read');self.assertIn('再次投诉',result['orders'][0]['never_click'])
    def test_new_uncomplained_review_never_gets_result_read_order(self):
        self.f.find('a')['name']='投诉';self.write();self.assertEqual(self.prepare()['orders'],[])
    def test_modified_source_or_changed_input_ref_cannot_replace_order(self):
        self.prepare();data=json.loads(self.paths['source'].read_text());data['rows'][0]['stars']=3;self.paths['source'].write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'not-reproducible'):self.prepare()
        self.write();self.paths['profile'].write_text(self.paths['profile'].read_text()+' ')
        with self.assertRaisesRegex(ValueError,'order-conflict'):self.prepare()
if __name__=='__main__':unittest.main()
