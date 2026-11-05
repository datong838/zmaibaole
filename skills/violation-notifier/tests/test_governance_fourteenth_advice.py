"""Actual saved DOM replay only; no connector or business state writes."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_detail as d
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
LABEL='抖音生活服务评价违规治理规则解读'
class AdviceTests(unittest.TestCase):
 def setUp(self):
  self.raw=json.loads((ROLE/'state-evidence/0068.json').read_text());self.row=next(x for x in json.loads((BASE/'records-range-query-v9.json').read_text())['rows'] if x['notice_id']=='202610164745326508')
  self.assertEqual(d.nav.digest(ROLE/'state-evidence/0068.json'),'5d762637962550f88b16a710a29b04d9e06e09cece32162c7fde68f73d941121')
 def advice(self,raw):return next(n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')=='textView-GrrExP' and n.get('children') and n['children'][0].get('name')==LABEL)
 def test_actual_link_tail_excluded_and_original_evidence_retained(self):
  f,c=d.parse(self.raw,self.row);n=self.advice(self.raw);p=f['public_recommendation_paragraphs'][0]
  self.assertEqual(f['public_recommendation'],n['name'][:-len(LABEL)]);self.assertEqual(p['original_visible_text'],n['name']);self.assertEqual(p['excluded_link_selector'],n['children'][0]['selector']);self.assertNotIn(LABEL,f['public_recommendation']);self.assertEqual(c['kind'],'dismiss')
 def test_same_reviewed_structure_accepts_dynamic_public_advice_not_fixed_payload(self):
  raw=copy.deepcopy(self.raw);n=self.advice(raw);n['name']='请基于真实消费体验自主评价。'+LABEL
  f,_=d.parse(raw,self.row);self.assertEqual(f['public_recommendation'],'请基于真实消费体验自主评价。')
 def test_changed_link_shape_non_suffix_or_empty_body_refused(self):
  for mode in ('class','label','child','multiple','nonsuffix','empty'):
   raw=copy.deepcopy(self.raw);n=self.advice(raw);a=n['children'][0]
   if mode=='class':a['attributes']['class']='unreviewed'
   elif mode=='label':a['name']='其他规则'
   elif mode=='child':a['children']=[{'tag':'span','name':LABEL}]
   elif mode=='multiple':n['children'].append(copy.deepcopy(a))
   elif mode=='nonsuffix':n['name']+='额外正文'
   else:n['name']=LABEL
   with self.subTest(mode=mode),self.assertRaises(ValueError):d.parse(raw,self.row)
 def test_completed_thirteen_parse_facts_remain_byte_equal(self):
  s=json.loads((ROLE/'state.json').read_text());self.assertGreaterEqual(len(s['details']),13)
  count=0
  for entry in s['details'][:13]:
   if entry.get('completion_kind'):continue
   facts,_=d.parse(d.document(entry['detail_observation']),entry['facts']['source_notice_row'])
   self.assertEqual(json.dumps(facts,ensure_ascii=False,sort_keys=True,separators=(',',':')),json.dumps(entry['facts'],ensure_ascii=False,sort_keys=True,separators=(',',':')));count+=1
  self.assertEqual(count,11) # Two stop-loss facts use their independent parser/verifier.
if __name__=='__main__':unittest.main()
