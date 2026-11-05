"""Actual eleventh notice DOM, exact historical/current stage separation. No live UI."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_capture as cap
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
DIR=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class HistoricalScoreTests(unittest.TestCase):
 def setUp(self):
  self.query=json.loads((BASE/'records-range-query-v9.json').read_text());self.row=self.query['rows'][10];self.raw=json.loads((DIR/'state-evidence/0050.json').read_text());self.entry={'detail_observation':d.ref(DIR/'state-evidence/0050.json'),'normal_before':d.ref(DIR/'state-evidence/0049.json')}
 def frame(self,raw):return next(n['public_frame_dom']['root'] for n in d.g.nodes(raw['tree']) if n.get('public_frame_dom'))
 def test_actual_historical_two_actions_and_current_empty_are_distinct(self):
  facts,close=d.parse(self.raw,self.row);self.assertEqual(facts['disposals'],['直播间警告、','信用分-直播分-6分']);self.assertEqual(facts['effective_statuses'],['已生效']);self.assertEqual(facts['effective_time'],'2026/10/17 19:08');self.assertEqual(facts['pending_disposals'],[]);self.assertEqual(facts['current_active_disposal_empty_label'],['暂无生效中处置']);self.assertEqual([o['temporal_scope'] for o in facts['effective_action_observations']],['historical-card']*2);self.assertEqual(close['kind'],'dismiss');self.assertEqual(facts['public_recommendation'],'为保障用户合法权益，建议通过小房子/小风车/小雪花等工具进行商品售卖或交易');self.assertNotIn('详情',facts['public_recommendation']);self.assertNotIn('平台规则',facts['public_recommendation']);self.assertTrue(facts['public_recommendation_paragraphs'][0]['original_visible_text'].endswith('详情'))
 def test_nested_unknown_control_or_changed_advice_is_rejected(self):
  for mode in ('score','image','header','detail_link','advice'):
   raw=copy.deepcopy(self.raw);nodes=list(d.g.walk(self.frame(raw)))
   if mode in ('score','image'):
    n=next(n for n in nodes if n.get('attributes',{}).get('class')=='action-xvEFrF' and n.get('name')=='信用分-直播分-6分')
    if mode=='score':n['name']='信用分-直播分-8分'
    else:n['children'][0]['tag']='button'
   elif mode=='header':next(n for n in nodes if n.get('attributes',{}).get('class')=='rule_link-eSsqKY')['attributes']['class']='unreviewed'
   else:
    plain=next(n for n in nodes if n.get('tag')=='span' and n.get('name','').startswith('为保障用户合法权益') and n.get('children'))
    if mode=='advice':plain['name']='未知建议详情'
    else:plain['children'][0]['name']='学习'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.row)
 def test_exact_capture_mapping_preserves_table_and_history_not_pending(self):
  facts,_=d.parse(self.raw,self.row);mapped=cap.historical_live_score_mapping(self.row,facts,self.entry);self.assertEqual(mapped['table_disposal'],'创作者信用分扣分');self.assertEqual(mapped['table_effectiveness_status'],'已生效');self.assertEqual(mapped['actions'],['直播间警告','信用分-直播分-6分']);self.assertEqual(mapped['disposal_stage_text'],'历史已生效：直播间警告；历史已生效：信用分-直播分-6分；当前：暂无生效中处置');self.assertEqual([x['status'] for x in mapped['action_details']],['已生效']*2);self.assertEqual([x['temporal_scope'] for x in mapped['action_details']],['historical-card']*2);self.assertEqual(mapped['action_details'][0]['original_text'],'直播间警告、');self.assertEqual(mapped['action_details'][1]['effective_time'],'2026/10/17 19:08')
 def test_mapping_reparses_original_and_cannot_hide_score_or_replace_table(self):
  facts,_=d.parse(self.raw,self.row);wrong=copy.deepcopy(facts);wrong['effective_action_observations'][1]['status']='待生效'
  with self.assertRaisesRegex(ValueError,'original-detail-facts'):cap.historical_live_score_mapping(self.row,wrong,self.entry)
  other=copy.deepcopy(self.row);other['disposal']='警告';self.assertIsNone(cap.historical_live_score_mapping(other,facts,self.entry));wrong=copy.deepcopy(facts);wrong['disposals']=['直播间警告、','信用分-直播分-8分'];self.assertIsNone(cap.historical_live_score_mapping(self.row,wrong,self.entry))
 def test_prior_ten_saved_facts_reverify_without_changes(self):
  m=json.loads((BASE/'detail-inspection-manifest.json').read_text());v=d.inputs(m);s=json.loads((DIR/'state.json').read_text());s['details']=s['details'][:10];s['cursor']=10;s['phase']='normal';expected=copy.deepcopy(s['details']);d.verify_completed(s,m,v,require_complete=False);self.assertEqual(s['details'],expected)
if __name__=='__main__':unittest.main()
