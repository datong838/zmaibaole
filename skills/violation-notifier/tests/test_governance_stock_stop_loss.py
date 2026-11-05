"""Actual stock-page replay + deliberately altered copies; no UI/business writes."""
import copy,json,sys,unittest
from pathlib import Path
HERE=Path(__file__).resolve();sys.path.insert(0,str(HERE.parents[1]/'scripts'))
import governance_stock_stop_loss as stock
import governance_detail as d
BASE=HERE.parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
ROLE=BASE/'governance-detail-operations/9890b61119299693bb0af8cdbb061d40072a3675bbfec9313deb5b99f4a39dca'
class StockTests(unittest.TestCase):
 def setUp(self):
  path=ROLE/'state-evidence/0078.json'
  if not path.exists():self.skipTest('actual saved stock detail unavailable')
  self.assertEqual(d.nav.digest(path),'9b7157ec9b9a1a5d6fc7d03401f928c586cb01aca33854fb6a9f725ef7264ea8')
  self.raw=json.loads(path.read_text());state=json.loads((ROLE/'state.json').read_text());v=d.inputs(state['manifest']);self.job=v['job'];self.row=v['query']['rows'][15];self.before=d.ref(ROLE/'state-evidence/0077.json');self.opening=d.g.one([c for c in state['calls'] if c.get('before')==self.before and c['command'].get('locator')==self.row['detail']['locator']],'actual original opening')
 def parse(self,raw=None,row=None,opening=None):return stock.parse(raw or self.raw,row or self.row,opening or self.opening,self.job)
 def find(self,raw,cls):return d.g.one([n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')==cls],'fixture node')
 def test_actual_two_timestamps_revoked_status_product_store_and_no_return_action(self):
  f,command=self.parse();self.assertIsNone(command);self.assertFalse(f['return_action_provided']);self.assertEqual(f['notification_time'],'2026/10/16 13:07');self.assertEqual(f['effective_period']['start'],'2026/10/16 12:15');self.assertEqual(f['effective_period']['end'],'2026/10/17 12:15')
  self.assertEqual(f['object_type'],'商品');self.assertEqual(f['object_id'],'1878370263889955');self.assertEqual(f['store_name'],'Yoshare榴哆哆榴莲体验馆(四马路店)');self.assertFalse(f['store_id_observed']);self.assertNotIn('store_id',f);self.assertEqual(f['source_binding']['source_object'],self.row['object']);self.assertEqual(f['source_binding']['source_subject'],self.row['store_name']);self.assertEqual(f['source_binding']['product_id'],f['object_id']);self.assertEqual(f['source_binding']['recommendation_selector'],f['public_recommendation_selectors'][0])
  self.assertEqual(f['disposals'],['门店商品不展示1天']);self.assertEqual(f['effective_statuses'],['已撤销']);self.assertEqual(f['table_effectiveness_status'],'已撤销')
 def test_dynamic_stock_advice_is_read_from_sole_nonmarketing_body(self):
  raw=copy.deepcopy(self.raw);bodies=[n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')=='my-[8px] is__content-TWHNZz' and not n.get('children')];self.assertEqual(len(bodies),1);bodies[0]['name']='请及时核对门店可售库存并补充备货，保障用户接待。'
  f,_=self.parse(raw);self.assertEqual(f['public_recommendation'],bodies[0]['name']);self.assertEqual(f['public_recommendation_selectors'],[bodies[0]['selector']])
 def test_marketing_metrics_and_buttons_are_excluded(self):
  f,_=self.parse();self.assertNotIn('开通',f['public_recommendation']);self.assertNotIn('14140',f['public_recommendation']);self.assertNotIn('去查看',f['public_recommendation']);self.assertNotIn('去反馈',f['public_recommendation']);self.assertTrue(f['excluded_marketing_sections'][0]['excluded_from_actions_and_client_copy'])
 def test_product_id_store_reason_and_source_row_tamper_refused(self):
  for mode in ('id','store','reason','row'):
   raw=copy.deepcopy(self.raw);row=copy.deepcopy(self.row)
   if mode=='id':self.find(raw,'flex items-center leading-[22px] flex items-center text-[14px] text-[#95989d]')['name']='1'
   elif mode=='store':next(n for n in d.g.nodes(raw['tree']) if n.get('attributes',{}).get('class')=='ml-[4px] text-[#95989d]' and not n.get('children') and n.get('name')==self.row['store_name'])['name']='另一门店'
   elif mode=='reason':self.find(raw,'inner-ypwT7g')['name']='另一原因'
   else:row['notice_id']='different'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.parse(raw,row)
 def test_unknown_open_scope_route_or_window_refuses(self):
  for mode in ('unknown','window','group','origin','query'):
   raw=copy.deepcopy(self.raw);opening=copy.deepcopy(self.opening)
   if mode=='unknown':opening['state']='unknown'
   elif mode=='window':raw['tab']['windowId']+=1
   elif mode=='group':raw['tab']['url']=raw['tab']['url'].replace(self.job['groupid'],'999')
   elif mode=='origin':raw['tab']['url']=raw['tab']['url'].replace('life.douyin.com','example.com')
   else:raw['tab']['url']+='&unreviewed=1'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.parse(raw,opening=opening)
 def test_changed_status_action_period_or_notification_id_refuses(self):
  for mode in ('status','action','period','notification'):
   raw=copy.deepcopy(self.raw)
   if mode=='status':next(n for n in d.g.nodes(raw['tree']) if 'govern_fulfillment_v2-tag-default' in d.g.cls(n) and not n.get('children'))['name']='已生效'
   elif mode=='action':self.find(raw,'leading-[28px] text-[14px] text-[#101011]')['name']='限流'
   elif mode=='period':self.find(raw,'mt-[4px] leading-[18px] text-[14px] text-[#a8abb2]')['name']='周期：2026/10/17 12:15 ~ 2026/10/16 12:15'
   else:self.find(raw,'flex items-center text-[14px] leading-[22px] text-[#6C737A]')['name']='通知时间 2026/10/16 13:07 通知单ID other'
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.parse(raw)
 def test_unknown_advice_control_or_extra_block_refused(self):
  for mode in ('child','block'):
   raw=copy.deepcopy(self.raw);blocks=[n for n in d.g.nodes(raw['tree']) if 'is-Lx65EE' in d.g.cls(n)];self.assertEqual(len(blocks),2)
   if mode=='child':blocks[1]['children'][1]['children']=[{'tag':'button','name':'开通'}]
   else:blocks[1]['children'].append({'tag':'div','name':'新内容'})
   with self.subTest(mode=mode),self.assertRaises(ValueError):self.parse(raw)
if __name__=='__main__':unittest.main()
