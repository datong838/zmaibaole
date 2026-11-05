import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError
import test_normal_paging_runner as fixture
import normal_paging_runner as c
import normal_read_recovery as repair
class Tests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.RunnerTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        def refused(command):raise URLError(ConnectionRefusedError(61,'Connection refused'))
        self.output=c.Runner(self.f.mr,refused).run(1);self.path=self.f.base/'operation.json';self.before=c.ref(self.path)['sha256'];self.nav=Path(self.f.nr['path']).read_bytes()
        self.health=c.publish(self.f.root/'health.json',{'actual-service-proof-fixture':True})
        self.g={'kind':'supervisor-original-normal-read-recovery-grant-v1','manifest':self.f.mr,'original_state_sha256':self.before,'service_health':self.health,'service_running_verified':True,'original_navigation_unchanged':True,'allow_original_read_resume_only':True,'no_browser_or_business_input':True};self.grant=c.publish(self.f.root/'grant.json',self.g)
    def run_repair(self,grant=None,sha=None):
        with patch.object(c.bridge,'request',side_effect=AssertionError('repair must never request')):return repair.resume(self.f.mr,sha or self.before,grant or self.grant)
    def test_exact_refusal_resumes_original_read_only_and_preserves_all_prior_evidence(self):
        self.assertEqual(self.output['state'],'hold');out=self.run_repair();self.assertTrue(out['rearmed']);s=json.loads(self.path.read_bytes());self.assertEqual((s['state'],s['phase'],s['expected_page']),('running','read-first',1));self.assertEqual(s['calls'],[]);self.assertEqual(len(s['transport']),1);self.assertEqual(Path(self.f.nr['path']).read_bytes(),self.nav);self.assertFalse(out['rpc_used']);self.assertTrue((self.f.base/'read-recovery/original-hold.json').exists())
    def test_repeat_does_not_rearm_later_failure_or_reset_state(self):
        self.run_repair();s=json.loads(self.path.read_bytes());s.update(state='hold',error='later failure');c.save(self.path,s);before=self.path.read_bytes();out=self.run_repair();self.assertFalse(out['rearmed']);self.assertEqual(out['state'],'hold');self.assertEqual(self.path.read_bytes(),before)
    def test_wrong_original_sha_does_not_write(self):
        before=self.path.read_bytes()
        with self.assertRaises(ValueError):self.run_repair(sha='0'*64)
        self.assertEqual(self.path.read_bytes(),before)
    def test_any_unknown_or_prior_input_cannot_resume(self):
        for changes in ({'state':'unknown'},{'calls':[{'state':'unknown','command':{'op':'click'}}]},{'pages':[{}]},{'expected_page':2}):
            original=json.loads(self.path.read_bytes());s={**original,**changes};c.save(self.path,s);new=c.ref(self.path)['sha256'];g={**self.g,'original_state_sha256':new};gr=c.publish(self.f.root/('grant-'+str(len(list(self.f.root.glob('grant-*'))))+'.json'),g)
            with self.subTest(changes=changes),self.assertRaises(ValueError):self.run_repair(grant=gr,sha=new)
            c.save(self.path,original)
    def test_service_grant_and_failure_evidence_are_pinned(self):
        Path(self.health['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'pinned-input-changed'):self.run_repair()
    def test_unapproved_resume_cannot_write(self):
        g={**self.g,'service_running_verified':False};gr=c.publish(self.f.root/'bad-grant.json',g);before=self.path.read_bytes()
        with self.assertRaisesRegex(ValueError,'approval-required'):self.run_repair(grant=gr)
        self.assertEqual(self.path.read_bytes(),before)
if __name__=='__main__':unittest.main()
