"""Saved fifteenth detail/source replay. No bridge, state, send or UI operations."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d
import governance_capture as c
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class CommentReplyTests(unittest.TestCase):
 def setUp(self):
  self.path=ROLE/'state-evidence/0073.json'
  if not self.path.exists():self.skipTest('actual saved fifteenth DOM unavailable')
  self.assertEqual(d.nav.digest(self.path),'fa25d447112910ca75eae42fd4e4b15e5757fb0f3b9b7216795d10e622f7a844')
  self.raw=json.loads(self.path.read_text());self.state=json.loads((ROLE/'state.json').read_text());self.v=d.inputs(self.state['manifest']);self.row=self.v['query']['rows'][14]
  self.entry={'detail_observation':d.ref(self.path),'normal_before':d.ref(ROLE/'state-evidence/0072.json')}
  rs=d.document(self.state['details'][12]['recovery_state']);self.refs=[p['observation'] for p in rs['center_pages']];self.pages=[c.center.center_page(d.document(r)['tree'],start=self.v['job']['start'],end_exclusive=self.v['job']['end_exclusive']) for r in self.refs]
 def find(self,raw,cls):return next(n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')==cls)
 def test_actual_raw_type_subtype_and_conditional_period_remain_distinct(self):
  facts,close=d.parse(self.raw,self.row)
  self.assertEqual(facts['object_type'],'评价');self.assertEqual(facts['object_subtype'],'商家回复');self.assertEqual(facts['object_id'],'7697150429360080930');self.assertEqual(facts['store_name'],self.row['store_name'])
  self.assertEqual(facts['effective_statuses'],['已生效']);self.assertFalse(facts['effective_period']['end_observed']);self.assertEqual(facts['effective_period']['end_condition'],'处置解除');self.assertEqual(close['kind'],'dismiss')
  self.assertNotIn('POI',facts['object_type']);self.assertTrue(facts['normalized_type_basis']['center_distribution_type_not_inferred_here'])
 def test_dynamic_original_reply_is_exactly_joined_not_fixed_to_one_text(self):
  raw=copy.deepcopy(self.raw);row=copy.deepcopy(self.row);obj=self.find(raw,'title-DVm52C');new='新的公开回复原文';obj['name']=obj['children'][0]['name']='评价'+new
  ident=self.find(raw,'overhide-lBaYV8');ident['name']='123456789';row['object']=new+' '+row['store_name']+' 评价ID： 123456789'
  facts,_=d.parse(raw,row);self.assertEqual(facts['object_name'],new);self.assertEqual(facts['object_id'],'123456789')
 def test_changed_id_body_subject_tag_or_extra_child_refused(self):
  for mode in ('id','body','subject','tag','child'):
   raw=copy.deepcopy(self.raw);obj=self.find(raw,'title-DVm52C')
   if mode=='id':self.find(raw,'overhide-lBaYV8')['name']='1'
   elif mode=='body':obj['name']=obj['children'][0]['name']='评价另一段'
   elif mode=='subject':self.find(raw,'poi-o_kcW5')['name']='其他店'
   elif mode=='tag':obj['children'][0]['children'][0]['name']='商品'
   else:obj['children'][0]['children'].append({'tag':'span','name':'未知'})
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.row)
 def test_unknown_period_status_or_tip_control_refused(self):
  for mode in ('period','status','control'):
   raw=copy.deepcopy(self.raw)
   if mode=='period':n=self.find(raw,'time-APdNEp');n['name']=n['children'][0]['name']='2026/10/16 15:41~已解除'
   elif mode=='status':next(n for n in d.g.nodes(raw['tree']) if 'status-Qza4ge' in d.g.cls(n))['name']='已结束'
   else:self.find(raw,'time-APdNEp')['children'][1]['children'][0]['tag']='button'
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.row)
 def test_capture_preserves_table_and_detail_status_with_exact_center_provenance(self):
  facts,_=d.parse(self.raw,self.row);mapped=c.comment_reply_status_mapping(self.row,facts,self.entry,self.pages,self.refs)
  self.assertEqual(mapped['table_effectiveness_status'],'生效中');self.assertEqual(mapped['detail_effectiveness_statuses'],['已生效']);self.assertEqual(mapped['action_details'][0]['status'],'生效中');self.assertEqual(mapped['action_details'][0]['detail_status'],'已生效')
  self.assertTrue(mapped['disposal_literal_mapping']['status_literals_preserved_not_equated']);self.assertEqual(mapped['normalized_type_basis']['center_type_evidence']['bucket']['object_types'],['POI评价商家回复'])
  self.assertFalse(mapped['effective_period']['end_observed'])
 def test_absent_center_type_proof_or_different_bucket_not_accepted(self):
  facts,_=d.parse(self.raw,self.row)
  with self.assertRaisesRegex(ValueError,'center-type-evidence'):c.comment_reply_status_mapping(self.row,facts,self.entry,[],[])
  pages=copy.deepcopy(self.pages)
  for p in pages:
   for r in p['top10']:
    if r['violation_type']==self.row['reason']:r['object_types']=['评价']
  with self.assertRaisesRegex(ValueError,'center-type-evidence'):c.comment_reply_status_mapping(self.row,facts,self.entry,pages,self.refs)
 def test_first_fourteen_complete_facts_remain_byte_equal_and_verified(self):
  prefix=copy.deepcopy(self.state);prefix['details']=prefix['details'][:14];prefix['cursor']=14
  for entry in prefix['details']:
   if entry.get('completion_kind'):continue
   facts,_=d.parse(d.document(entry['detail_observation']),entry['facts']['source_notice_row'])
   self.assertEqual(json.dumps(facts,ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(entry['facts'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
  self.assertEqual(len(d.verify_completed(prefix,prefix['manifest'],self.v,require_complete=False)),14)
if __name__=='__main__':unittest.main()
