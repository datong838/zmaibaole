"""Real archived ban detail; no UI or business-state writes."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import governance_capture as c
BASE=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class BanTests(unittest.TestCase):
 def setUp(self):
  self.entry=json.loads(next((BASE/'governance-detail-operations').glob('*/state.json')).read_text())['details'][6]
  self.facts=self.entry['facts'];self.source=self.facts['source_notice_row']
  self.assertEqual(self.entry['detail_observation']['sha256'],'ab6df5f221ea3af9c04acad66878d745d945f729c6bd870e77f713509812e1ca')
 def test_actual_permanent_label_and_two_literal_statuses_preserved(self):
  m=c.permanent_product_ban_mapping(self.source,self.facts,self.entry)
  self.assertEqual(m['actions'],['封禁商品永久']);self.assertEqual(m['table_disposal'],'封禁商品')
  self.assertEqual(m['table_effectiveness_status'],'生效中');self.assertEqual(m['detail_effectiveness_statuses'],['已生效'])
  self.assertIn('永久',m['disposal_stage_text']);self.assertFalse(m['effective_period']['end_observed'])
  self.assertEqual(m['effective_period']['end_condition'],'处置解除');self.assertTrue(m['disposal_literal_mapping']['status_literals_preserved_not_equated'])
 def test_changed_source_or_facts_cannot_relabel_other_action(self):
  for key,val in (('disposal','下架商品'),('effective_status','已结束'),('reason','未知原因')):
   s=dict(self.source);s[key]=val;self.assertIsNone(c.permanent_product_ban_mapping(s,self.facts,self.entry))
  f=copy.deepcopy(self.facts);f['public_recommendation']='任意改写'
  with self.assertRaisesRegex(ValueError,'original-facts-mismatch'):c.permanent_product_ban_mapping(self.source,f,self.entry)
if __name__=='__main__':unittest.main()
