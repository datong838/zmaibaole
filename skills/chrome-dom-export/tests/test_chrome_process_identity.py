import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import chrome_process_identity as c
CLONE='/private/var/folders/h_/abc123/X/com.google.Chrome.code_sign_clone/code_sign_clone.Abc123/Google Chrome.app.bundle/Contents/MacOS/Google Chrome'
class IdentityTests(unittest.TestCase):
 def setUp(self):self.calls=[]
 def display(self,path):return {'Executable':path,'Identifier':c.IDENTIFIER,'TeamIdentifier':c.TEAM,'CDHash':('a' if path==c.EXE else 'b')*40,'designated_requirement':'identifier "com.google.Chrome" and anchor apple generic'}
 def bundle(self,path):return {'bundle_path':str(Path(path).parent.parent.parent),'CFBundleIdentifier':c.IDENTIFIER,'CFBundleExecutable':'Google Chrome'}
 def validity(self,path,requirement):
  self.calls.append((path,requirement));return {'api':'SecStaticCodeCheckValidity','flags':['kSecCSCheckAllArchitectures','kSecCSDoNotValidateResources'],'status':0,'main_executable_pages_verified':True,'bundle_resources_verified':False,'network_access_requested':False}
 def verify(self,**kw):return c.verify(CLONE,display_fn=kw.get('display_fn',self.display),bundle_fn=self.bundle,validity_fn=kw.get('validity_fn',self.validity),resolve_fn=lambda p:p)
 def test_exact_google_clone_validity_different_cdhash_honest_resources_false(self):
  proof=self.verify();self.assertIs(c.validate_record(proof,CLONE),proof);self.assertEqual(len(self.calls),2);self.assertIn('identifier "com.google.Chrome"',self.calls[1][1]);self.assertIn(c.TEAM,self.calls[1][1]);self.assertFalse(proof['bundle_resources_verified'])
 def test_same_dr_does_not_admit_beta_other_team_or_mismatched_requirement(self):
  for field,value in [('Identifier','com.google.Chrome.beta'),('TeamIdentifier','WRONGTEAM'),('designated_requirement','different')]:
   def display(path):v=self.display(path);v[field]=value if path==CLONE else v[field];return v
   with self.assertRaises(ValueError):self.verify(display_fn=display)
 def test_arbitrary_same_name_or_different_os_clone_path_rejected_before_signature(self):
  for path in ['/tmp/Google Chrome.app/Contents/MacOS/Google Chrome',CLONE.replace('com.google.Chrome.code_sign_clone','other.code_sign_clone'),CLONE.replace('/X/','/T/')]:
   with self.assertRaisesRegex(ValueError,'unreviewed'):c.verify(path,display_fn=lambda p:self.fail('must not inspect unreviewed path'))
 def test_invalid_main_code_never_passes_as_resource_exception(self):
  def fail(path,requirement):raise ValueError('chrome-signed-main-code-invalid:-67061')
  with self.assertRaisesRegex(ValueError,'code-invalid'):self.verify(validity_fn=fail)
 def test_offline_record_rejects_fabricated_bundle_or_validation_scope(self):
  proof=self.verify()
  for field,value in [('bundle_resources_verified',True),('team_identifier','OTHER'),('observed_executable','/tmp/Chrome')]:
   bad=copy.deepcopy(proof);bad[field]=value
   with self.assertRaises(ValueError):c.validate_record(bad,CLONE)
  bad=copy.deepcopy(proof);bad['observed_code_validation']['main_executable_pages_verified']=False
  with self.assertRaises(ValueError):c.validate_record(bad,CLONE)
if __name__=='__main__':unittest.main()
