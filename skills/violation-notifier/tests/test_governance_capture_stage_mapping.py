"""Narrow action-stage mapping from the actual completed fifth notice, no UI."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_capture as c
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class StageMappingTests(unittest.TestCase):
 def setUp(self):
  state=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state.json').read_text());self.entry=next(x for x in state['details'] if x['notice_id']=='202610204776378817');self.facts=self.entry['facts'];self.row=self.facts['source_notice_row']
 def test_actual_completed_pair_retains_table_actions_and_pending_not_deducted(self):
  mapped=c.staged_live_score_mapping(self.row,self.facts,self.entry);self.assertEqual(mapped['actions'],['直播间警告','创作者信用分扣分']);self.assertEqual(mapped['table_disposal'],self.row['disposal']);self.assertEqual(mapped['table_effectiveness_status'],'已生效');details=mapped['action_details'];self.assertEqual([x['status'] for x in details],['已生效','待生效']);self.assertEqual(details[1]['original_text'],'信用分-直播分-6分');self.assertIn('尚未扣除',mapped['disposal_stage_text']);self.assertEqual(details[1]['detail_observation'],self.entry['detail_observation']);self.assertTrue(details[1]['label_selector'].startswith('readonly-frame:'))
 def test_every_other_literal_pair_is_unmapped(self):
  for change in ('score','active','status','table','type'):
   row=copy.deepcopy(self.row);facts=copy.deepcopy(self.facts)
   if change=='score':facts['pending_disposals']=['信用分-直播分-3分']
   elif change=='active':facts['disposals']=['限流']
   elif change=='status':row['effective_status']='生效中'
   elif change=='table':row['disposal']='警告，信用分扣分'
   else:facts['object_type']='商品'
   with self.subTest(change=change):self.assertIsNone(c.staged_live_score_mapping(row,facts,self.entry))
 def test_matching_literal_but_forged_selector_or_stage_fact_cannot_grant_mapping(self):
  for change in ('selector','label'):
   facts=copy.deepcopy(self.facts)
   if change=='selector':facts['disposal_observations'][1]['label_selector']='readonly-frame:#forged'
   else:facts['disposal_observations'][1]['status']='已生效'
   with self.subTest(change=change),self.assertRaisesRegex(ValueError,'original-detail-facts-mismatch'):c.staged_live_score_mapping(self.row,facts,self.entry)
 def test_original_raw_hash_is_rechecked_instead_of_trusting_handfilled_facts(self):
  entry=copy.deepcopy(self.entry);entry['detail_observation']['sha256']='0'*64
  with self.assertRaises(ValueError):c.staged_live_score_mapping(self.row,self.facts,entry)
if __name__=='__main__':unittest.main()
