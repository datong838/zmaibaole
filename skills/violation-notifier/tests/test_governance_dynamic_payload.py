"""Actual readonly templates with explicit synthetic payload variations; never UI."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d,governance_rates_stop_loss as rates,governance_capture as capture
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class DynamicPayloadTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.state=json.loads((ROLE/'state.json').read_text());cls.m=json.loads((BASE/'detail-inspection-manifest.json').read_text());cls.v=d.inputs(cls.m)
 def entry(self,index):return self.state['details'][index]
 def raw(self,index):return d.document(self.entry(index)['detail_observation'])
 def frame_nodes(self,raw):return list(d.g.walk(next(n['public_frame_dom']['root'] for n in d.g.nodes(raw['tree']) if n.get('public_frame_dom'))))
 def test_public_plain_tool_and_ai_advice_are_dynamic_inside_reviewed_boundaries(self):
  for index,label in ((7,self.v['query']['rows'][7]['reason']),(10,'详情')):
   raw=self.raw(index);nodes=self.frame_nodes(raw);paragraph=next(n for n in nodes if n.get('attributes',{}).get('class')=='paragraph-HMGO6N');plain=paragraph['children'][0];plain['name']='这是本次公开整改建议正文。'+label
   facts,_=d.parse(raw,self.v['query']['rows'][index]);self.assertEqual(facts['public_recommendation'],'这是本次公开整改建议正文。');self.assertEqual(facts['public_recommendation_paragraphs'][0]['original_visible_text'],plain['name']);self.assertNotIn(label,facts['public_recommendation'])
  raw=self.raw(4);nodes=self.frame_nodes(raw);paragraphs=[n for n in nodes if n.get('attributes',{}).get('class')=='paragraph-HMGO6N'];paragraphs[1]['children'][0]['name']='新的公开建议，不依赖特定时间戳。';facts,_=d.parse(raw,self.v['query']['rows'][4]);self.assertIn('新的公开建议，不依赖特定时间戳。',facts['public_recommendation']);self.assertNotIn('以下为AI解读建议',facts['public_recommendation']);self.assertNotIn('规则解析',facts['public_recommendation'])
 def test_new_credit_score_preserves_raw_and_does_not_expand_capture_mapping(self):
  raw=self.raw(10)
  for n in self.frame_nodes(raw):
   if 'name' in n:n['name']=n['name'].replace('信用分-直播分-6分','信用分-直播分-9.5分')
  facts,_=d.parse(raw,self.v['query']['rows'][10]);self.assertEqual(facts['disposals'],['直播间警告、','信用分-直播分-9.5分']);self.assertEqual(facts['effective_statuses'],['已生效']);self.assertEqual(facts['effective_action_observations'][1]['text'],'信用分-直播分-9.5分');self.assertIsNone(capture.historical_live_score_mapping(self.v['query']['rows'][10],facts,self.entry(10)))
 def test_invalid_nested_score_syntax_extra_child_and_frame_form_refuse(self):
  for mode in ('score','extra','form','editable'):
   raw=self.raw(10);nodes=self.frame_nodes(raw);action=next(n for n in nodes if n.get('attributes',{}).get('class')=='action-xvEFrF')
   if mode=='score':action['name']='信用分-直播分-未知分'
   elif mode=='extra':action['children'].append(copy.deepcopy(action['children'][0]))
   else:
    root=next(n['public_frame_dom']['root'] for n in d.g.nodes(raw['tree']) if n.get('public_frame_dom'));root['children'].append({'tag':'form' if mode=='form' else 'div','selector':root['selector']+' > injected','attributes':{'contenteditable':'true'} if mode=='editable' else {},'children':[]})
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.v['query']['rows'][10])
 def test_rates_advice_and_potential_threshold_data_do_not_become_executed_actions(self):
  entry=self.entry(12);raw=self.raw(12);original=d.document(entry['source_parent']);stage=d.document(original['rates_stop_loss_stage']['original_state']);opening=stage['calls'][-1];nodes=d.g.nodes(raw['tree']);body=next(n for n in nodes if n.get('attributes',{}).get('class')=='my-[8px] is__content-TWHNZz' and n.get('name','').startswith('建议您查看'));body['name']='请按近期经营情况改善接待与履约。';condition=next(n for n in nodes if n.get('attributes',{}).get('class')=='mt-[4px] leading-[18px] text-[14px] text-[#A8ABB2]');condition['name']='触发条件：差评率>2.15%、商责退单率>3.70%';potential=next(n for n in nodes if n.get('attributes',{}).get('class')=='leading-[28px] text-[14px] text-[#101011]' and n.get('name')=='推荐流量限制（中等）');potential['name']='推荐流量限制（较重）'
  facts,_=rates.parse(raw,self.v['query']['rows'][12],opening,self.v['job']);self.assertEqual(facts['public_recommendation'],body['name']);self.assertEqual(facts['potential_consequences'][0]['condition'],condition['name']);self.assertEqual(facts['potential_consequences'][0]['text'],potential['name']);self.assertFalse(facts['potential_consequences'][0]['execution_observed']);self.assertEqual(facts['disposals'],['推荐流量限制（轻度）']);self.assertNotIn('较重',facts['public_recommendation'])
 def test_wrong_section_or_control_in_advice_still_refuses(self):
  for mode in ('section','child'):
   raw=self.raw(7);nodes=self.frame_nodes(raw)
   if mode=='section':next(n for n in nodes if n.get('attributes',{}).get('class')=='title-MfzSKF')['name']='违规详情'
   else:next(n for n in nodes if n.get('attributes',{}).get('class')=='paragraph-HMGO6N')['children'].append({'tag':'span','name':'extra'})
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.v['query']['rows'][7])
 def test_all_sixteen_existing_facts_canonical_bytes_unchanged(self):
  facts=d.verify_completed(self.state,self.m,self.v)
  self.assertEqual(len(facts),16)
  for actual,entry in zip(facts,self.state['details']):self.assertEqual(json.dumps(actual,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(),json.dumps(entry['facts'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
if __name__=='__main__':unittest.main()
