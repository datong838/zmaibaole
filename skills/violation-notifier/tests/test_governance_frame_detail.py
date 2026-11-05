"""Actual readonly same-origin notice frame replay. No bridge or UI calls."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class FrameDetailTests(unittest.TestCase):
 def setUp(self):
  self.raw=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0019.json').read_text());self.row=next(x for x in json.loads((BASE/'records-range-query-v9.json').read_text())['rows'] if x['notice_id']=='202610204776378817')
 def iframe(self,raw):return next(n for n in d.g.nodes(raw['tree']) if n.get('public_frame_dom'))
 def test_actual_frame_keeps_active_pending_and_two_independent_advice_lines(self):
  facts,close=d.parse(self.raw,self.row);self.assertEqual(facts['schema'],'governance-notice-frame-detail-v1');self.assertEqual(facts['object_type'],'直播');self.assertEqual(facts['object_id'],'7698599217086122752');self.assertEqual(facts['disposals'],['直播间警告']);self.assertEqual(facts['pending_disposals'],['信用分-直播分-6分']);self.assertEqual([x['status'] for x in facts['disposal_observations']],['已生效','待生效']);self.assertEqual(facts['current_active_disposal_empty_label'],['暂无生效中处置']);self.assertNotIn('notification_time',facts);self.assertFalse(facts['notification_time_observed']);self.assertEqual(len(facts['public_recommendation_paragraphs']),2);self.assertNotIn('以下为AI解读建议',facts['public_recommendation']);self.assertNotIn('规则解析',facts['public_recommendation']);self.assertNotIn('直播风险帧画面内容',facts['public_recommendation']);self.assertEqual(close['kind'],'dismiss');self.assertNotIn('readonly-frame:',close['locator']['value'])
 def test_actual_sixth_notice_absent_pending_and_single_advice_not_zero_punishment(self):
  raw=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0024.json').read_text());row=next(x for x in json.loads((BASE/'records-range-query-v9.json').read_text())['rows'] if x['notice_id']=='202610204775040085');facts,close=d.parse(raw,row);self.assertEqual(facts['pending_disposals'],[]);self.assertFalse(facts['pending_label_observation']['present']);self.assertEqual(facts['disposals'],['直播间警告']);self.assertEqual(len(facts['disposal_observations']),1);self.assertEqual(len(facts['public_recommendation_paragraphs']),1);self.assertNotIn('规则解析',facts['public_recommendation']);self.assertNotIn('以下为AI解读建议',facts['public_recommendation']);self.assertEqual(close['kind'],'dismiss')
  broken=copy.deepcopy(raw);frame=self.iframe(broken)['public_frame_dom'];leaf=copy.deepcopy(next(n for n in d.g.walk(frame['root']) if n.get('name')=='已生效处置'));leaf['name']='待生效处置';leaf['attributes']['class']='unreviewed';frame['root']['children'].append(leaf)
  with self.assertRaisesRegex(ValueError,'optional-label-malformed'):d.parse(broken,row)
 def test_previous_present_pending_shape_and_stored_fifth_facts_unchanged(self):
  facts,_=d.parse(self.raw,self.row);self.assertNotIn('pending_label_observation',facts);state=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state.json').read_text());entry=state['details'][4];saved,_=d.parse(d.document(entry['detail_observation']),self.row);self.assertEqual(saved,entry['facts'])
 def test_actual_eighth_plain_rule_advice_excludes_sole_rule_name_suffix(self):
  raw=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state-evidence/0033.json').read_text());row=next(x for x in json.loads((BASE/'records-range-query-v9.json').read_text())['rows'] if x['notice_id']=='202610184762254243');facts,_=d.parse(raw,row);self.assertEqual(facts['public_recommendation'],'直播时请勿包含影响用户体验（如与用户无互动）的行为');self.assertEqual(facts['disposals'],['本场直播流量下降、','警告']);self.assertEqual(facts['public_recommendation_paragraphs'][0]['excluded_rule_label'],row['reason']);self.assertTrue(facts['public_recommendation_paragraphs'][0]['original_visible_text'].endswith(row['reason']));self.assertNotIn('固定机位拍摄',facts['public_recommendation'])
  changed=copy.deepcopy(raw);frame=self.iframe(changed)['public_frame_dom'];paragraph=next(n for n in d.g.walk(frame['root']) if n.get('attributes',{}).get('class')=='paragraph-HMGO6N');paragraph['children'][0]['children'][0]['name']='其他规则'
  with self.assertRaisesRegex(ValueError,'plain-advice-unreviewed'):d.parse(changed,row)
 def test_first_seven_completed_facts_reparse_identically_without_rewrite(self):
  state=json.loads((BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca/state.json').read_text());self.assertGreaterEqual(len(state['details']),7)
  for entry in state['details'][:7]:
   with self.subTest(notice=entry['notice_id']):
    parsed,_=d.parse(d.document(entry['detail_observation']),entry['facts']['source_notice_row']);self.assertEqual(parsed,entry['facts'])
 def test_same_origin_path_ready_projection_guards_refuse(self):
  for mode in ('origin','path','ready','input','selector'):
   raw=copy.deepcopy(self.raw);iframe=self.iframe(raw)
   if mode=='origin':iframe['public_frame']['document_origin']='https://foreign.example'
   elif mode=='path':iframe['public_frame']['source_path']='/other'
   elif mode=='ready':iframe['public_frame']['ready_state']='loading'
   elif mode=='input':iframe['public_frame_dom']['input_enabled']=True
   else:iframe['public_frame_dom']['root']['selector']='#outside'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.row)
 def test_actual_source_notice_object_reason_and_advice_titles_cannot_be_substituted(self):
  for mode in ('notice','object','reason','advice'):
   row=copy.deepcopy(self.row);raw=copy.deepcopy(self.raw)
   if mode=='notice':row['notice_id']='other'
   elif mode=='object':row['object']='other'
   elif mode=='reason':row['reason']='other'
   else:next(n for n in d.g.walk(self.iframe(raw)['public_frame_dom']['root']) if n.get('attributes',{}).get('class')=='title-MfzSKF')['name']='违规详情'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,row)
 def test_missing_new_close_marker_fails_before_any_request_or_intent(self):
  facts,command=d.parse(self.raw,self.row);r=object.__new__(d.Runner);r.s={'current':{'facts':facts},'calls':[]};r.detail_policy_ready=True;r.frame_detail_policy_ready=False
  with self.assertRaisesRegex(ValueError,'frame-detail-close-policy-not-loaded'):r.action(command,'verify-closed',{})
  self.assertEqual(r.s['calls'],[])
if __name__=='__main__':unittest.main()
