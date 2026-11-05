"""Exact saved public DOM replay; target tabs are explicitly synthetic."""
import json,unittest
from pathlib import Path
from switch_read_fixture import m
class SavedHomeIntegration(unittest.TestCase):
 def test_actual_saved_home_tree_without_provider_is_transition_only(self):
  # This is an offline raw-tree replay. The tabs below are synthetic, not a
  # claim that fresh actual Chrome has already reached this target URL.
  b=Path(__file__).resolve().parent/'fixtures/company-switch-home-fa777'
  if not b.exists():self.skipTest('Optional exact saved public-tree fixture unavailable')
  manifest=json.loads((b/'provenance.json').read_bytes())
  for name,source in manifest['files'].items():self.assertEqual(m.sha((b/name).read_bytes()),source['sha256'])
  job=json.loads((b/'job.json').read_bytes());s=json.loads((b/'original-journal.json').read_bytes());tree=json.loads((b/'tree.json').read_bytes())
  self.assertEqual(m.sha((b/'tree.json').read_bytes()),'fa777a755426a629bdbe1303e40b29adb465a62f9d49fef8ee7294d9f6197d6f')
  synthetic_tabs=[{'windowId':995698278,'focused':True,'tabs':[{'tabId':995698279,'windowId':995698278,'allowed':True,'active':True,'url':'https://life.douyin.com/p/home?groupid=1764303851132943'}]}]
  facts=m.verify_sample(job,s,{'before':synthetic_tabs,'after':synthetic_tabs,'tree':tree,'ping':{'version':'dom-only-20261021-11','safety':'DOM-only'}})
  self.assertFalse(facts['provider_observed']);self.assertFalse(facts['full_identity_observed']);self.assertIsNone(facts['provider']);self.assertEqual(facts['provider_baseline'],job['provider_baseline'])

if __name__=='__main__':unittest.main()
