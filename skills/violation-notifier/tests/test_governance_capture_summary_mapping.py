"""Actual completed eighth notice mapping; no connector, UI or hand-filled source facts."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_capture as c
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class SummaryMappingTests(unittest.TestCase):
 def setUp(self):
  state=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state.json').read_text());self.entry=next(x for x in state['details'] if x['notice_id']=='202610184762254243');self.facts=self.entry['facts'];self.row=self.facts['source_notice_row']
 def test_actual_complete_pair_keeps_table_summary_and_both_raw_action_refs(self):
  result=c.summary_live_flow_mapping(self.row,self.facts,self.entry);self.assertEqual(result['table_disposal'],'警告');self.assertEqual(result['actions'],['本场直播流量下降','警告']);self.assertEqual([x['status'] for x in result['action_details']],['已生效','已生效']);first=result['action_details'][0];self.assertEqual(first['original_text'],'本场直播流量下降、');self.assertEqual(first['display_normalization'],'remove-one-observed-trailing-enumeration-comma');self.assertEqual(first['detail_observation'],self.entry['detail_observation']);self.assertIn('流量下降',result['disposal_stage_text']);self.assertEqual(result['disposal_literal_mapping']['method'],'table-summary-plus-detail-effective-action-v1')
 def test_nearby_unreviewed_literals_never_match(self):
  for field,value in [('disposal','直播间警告'),('effective_status','生效中')]:
   row=copy.deepcopy(self.row);row[field]=value;self.assertIsNone(c.summary_live_flow_mapping(row,self.facts,self.entry))
  facts=copy.deepcopy(self.facts);facts['disposals']=['本场直播流量下降','警告'];self.assertIsNone(c.summary_live_flow_mapping(self.row,facts,self.entry));facts=copy.deepcopy(self.facts);facts['pending_disposals']=['待扣1分'];self.assertIsNone(c.summary_live_flow_mapping(self.row,facts,self.entry))
 def test_unchanged_literals_but_forged_selector_or_status_fails_raw_reparse(self):
  for field,value in [('label_selector','readonly-frame:#fake'),('status','待生效')]:
   facts=copy.deepcopy(self.facts);facts['disposal_observations'][0][field]=value
   with self.assertRaisesRegex(ValueError,'original-detail-facts-mismatch'):c.summary_live_flow_mapping(self.row,facts,self.entry)
 def test_bad_original_hash_cannot_authorize_mapping(self):
  entry=copy.deepcopy(self.entry);entry['normal_before']['sha256']='0'*64
  with self.assertRaises(ValueError):c.summary_live_flow_mapping(self.row,self.facts,entry)
if __name__=='__main__':unittest.main()
