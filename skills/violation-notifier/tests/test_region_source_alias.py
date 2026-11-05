"""Only source alias/prefix layer mocked at later pixel validator; no live evidence."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'skills/violation-notifier/scripts'),str(ROOT/'skills/chrome-dom-export/scripts')]
import region_frame_capture as r
class SourceAlias(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.original=self.root/'original/source.json';self.original.parent.mkdir();self.original.write_text(json.dumps({'company':'mock','groupid':'1','records':{'rows':[{'notice_id':'a'},{'notice_id':'b'}]}}));self.source=self.ref(self.original);self.copy=self.root/'evidence/copy.json';self.copy.parent.mkdir();self.copy.write_bytes(self.original.read_bytes());self.alias=self.ref(self.copy);self.chain='fixture-chain-1';self.profile='a'*64
  prior=self.write(self.root/'prior.json',{'state':'complete','chain_id':self.chain,'visibility_policy':r.business.CONTRACT,'pinned_inputs':{'profile_sha256':self.profile},'recorded_at':'2026-10-21T00:00:00+00:00','image':{'path':str(self.root/'unused.png')}})
  self.state={'scope':{'source_sha256':self.source['sha256'],'profile_sha256':self.profile,'chain_id':self.chain},'frames':[{'state':'complete','registration':prior}]}
  snapshot=self.write(self.root/'before.json',self.state);self.canonical=self.original.parent/'.native-region-frame-state'/(r.fc.fingerprint([self.source['sha256'],self.chain])+'.json');self.write(self.canonical,self.state)
  self.selection={'schema':'verified-uncovered-original-notices-v1','source':self.source,'profile_sha256':self.profile,'chain_id':self.chain,'prior_frames':[prior],'prior_chain':snapshot,'covered_notice_ids':['a'],'selected_notice_ids':['b']}
 def ref(self,path):return {'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 def write(self,path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value));return self.ref(path)
 def run_selection(self,source=None,selection=None):
  with patch.object(r,'is_business',lambda inputs:True),patch.object(r.business,'selectable_rows',lambda base:[{'notice_id':'b'}]),patch.object(r,'validate_frame',lambda *args,**kwargs:{'notice_ids':['a']}):
   return r._selection_ids_uncached(selection or self.selection,{},source or self.source,self.chain,profile_sha256=self.profile,base={})
 def test_original_and_exact_copy_keep_original_only_canonical_journal(self):
  self.assertEqual(self.run_selection(),['b']);self.assertFalse((self.copy.parent/'.native-region-frame-state').exists());self.assertEqual(self.run_selection(self.alias),['b']);self.assertFalse((self.copy.parent/'.native-region-frame-state').exists())
 def test_different_bytes_with_original_claimed_sha_rejected(self):
  self.copy.write_text('{}')
  with self.assertRaisesRegex(ValueError,'reference-changed'):self.run_selection(self.alias)
 def test_valid_different_source_and_same_json_different_encoding_rejected(self):
  self.copy.write_text(json.dumps({'company':'other','records':{'rows':[]}}))
  with self.assertRaisesRegex(ValueError,'selection-scope-invalid'):self.run_selection(self.ref(self.copy))
  self.copy.write_text(json.dumps(json.loads(self.original.read_text()),indent=2))
  with self.assertRaisesRegex(ValueError,'selection-scope-invalid'):self.run_selection(self.ref(self.copy))
 def test_copy_fake_journal_cannot_replace_missing_original(self):
  self.canonical.unlink();copy_journal=self.copy.parent/'.native-region-frame-state'/self.canonical.name;self.write(copy_journal,self.state)
  with self.assertRaises(FileNotFoundError):self.run_selection(self.alias)
 def test_original_current_prefix_unknown_or_changed_is_rejected(self):
  current=copy.deepcopy(self.state);current['frames'][0]['state']='unknown';self.write(self.canonical,current)
  with self.assertRaisesRegex(ValueError,'original-chain-prefix-changed'):self.run_selection(self.alias)
 def test_profile_chain_and_selected_ids_constraints_unchanged(self):
  for key,value in (('profile_sha256','b'*64),('chain_id','other-chain'),('selected_notice_ids',['a'])):
   selected=copy.deepcopy(self.selection);selected[key]=value
   with self.assertRaises(ValueError):self.run_selection(self.alias,selected)
if __name__=='__main__':unittest.main()
