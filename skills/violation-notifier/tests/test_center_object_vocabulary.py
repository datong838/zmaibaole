"""Actual archived detail vocabulary plus negative scope tests; no live input."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import center_reconciliation as c
import governance_detail as d
BASE=Path(__file__).resolve().parents[3]/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司'
class VocabularyTests(unittest.TestCase):
 def rows(self):
  s=json.loads(next((BASE/'governance-detail-operations').glob('*/state.json')).read_text());out=[]
  for e in s['details']:
   f=e['facts'];out.append({'notice_id':f['notice_id'],'object_type':f['object_type'],'subject':f['source_notice_row']['store_name'],'reason':f['reason'],'detail_object_type_basis':{**{k:f.get(k) for k in ('schema','object_type','object_id','store_name','store_id')},'observation':e['detail_observation']}})
  return out
 def test_actual_frame_and_store_product_vocabulary(self):
  rows=self.rows();live=next(r for r in rows if r['notice_id']=='202610174754039434');product=next(r for r in rows if r['notice_id']=='ZS202610174754837331')
  self.assertEqual(c.distribution_type(live)[0],'直播内容');self.assertEqual(c.distribution_type(product)[0],'门店商品')
  self.assertEqual(live['object_type'],'直播');self.assertEqual(product['object_type'],'商品')
  for r in (live,product):self.assertEqual(c.distribution_type(r)[1]['basis']['observation'],r['detail_object_type_basis']['observation'])
 def test_no_global_alias_and_wrong_subject_schema_or_id_stays_raw(self):
  p=next(r for r in self.rows() if r['notice_id']=='ZS202610174754837331')
  for key,value in (('schema','unverified'),('store_name','其他门店'),('store_id',None),('object_id','bad'),('object_type','门店'),('observation',{})):
   r=copy.deepcopy(p);r['detail_object_type_basis'][key]=value
   with self.subTest(key=key):self.assertEqual(c.distribution_type(r),('商品',None))
  r=copy.deepcopy(p);r['reason']='商品资质缺失';self.assertEqual(c.distribution_type(r),('商品',None))
 def test_actual_plain_product_not_store_product(self):
  r=next(r for r in self.rows() if r['notice_id']=='202610204778556479');self.assertEqual(c.distribution_type(r),('商品',None))
 def test_actual_reply_requires_matching_center_bucket_and_explicit_subtype(self):
  role=next((BASE/'governance-detail-operations').glob('*/state.json')).parent
  raw=d.ref(role/'state-evidence/0073.json');source=json.loads((BASE/'records-range-query-v9.json').read_text())['rows'][14]
  facts,_=d.parse(d.document(raw),source)
  page_ref=d.ref(role/'rates-recovery/state-evidence/0002.json')
  page=c.center_page(d.document(page_ref)['tree'],start='2026-10-16',end_exclusive='2026-10-21')
  bucket=next(x for x in page['top10'] if x['violation_type']==source['reason'])
  r={'notice_id':facts['notice_id'],'reason':facts['reason'],'object_type':facts['object_type'],'object_subtype':facts['object_subtype'],
     'detail_object_type_basis':{**{k:facts.get(k) for k in ('schema','object_type','object_id','object_subtype','normalized_type_basis')},'observation':raw},
     'normalized_type_basis':dict(facts['normalized_type_basis'],center_type_evidence={'observation':page_ref,'bucket':bucket})}
  self.assertEqual(c.distribution_type(r,bucket)[0],'POI评价商家回复');self.assertEqual(r['object_type'],'评价')
  self.assertEqual(c.distribution_type(r),('评价',None))
  wrong=copy.deepcopy(bucket);wrong['object_types']=['评价'];self.assertEqual(c.distribution_type(r,wrong),('评价',None))
  r['detail_object_type_basis']['normalized_type_basis']['subtype']='消费者评价';self.assertEqual(c.distribution_type(r,bucket),('评价',None))
 def test_actual_stock_store_relation_without_fabricated_store_id(self):
  import governance_stock_stop_loss as stock
  role=next((BASE/'governance-detail-operations').glob('*/state.json')).parent;s=json.loads((role/'state.json').read_text())
  source=json.loads((BASE/'records-range-query-v9.json').read_text())['rows'][15]
  opening=next(x for x in s['calls'] if x['state']=='confirmed' and x['command'].get('locator')==source['detail']['locator'] and any(r['notice_id']==source['notice_id'] for r in d.g.records_page(d.document(x['before'])['tree'],require_date=False)['rows']))
  raw=d.ref(role/'state-evidence/0078.json');facts,_=stock.parse(d.document(raw),source,opening,json.loads((BASE/'navigation-job.json').read_text()))
  basis={**{k:facts.get(k) for k in ('schema','object_type','object_id','store_name','store_id','source_binding')},'observation':raw}
  r={'notice_id':facts['notice_id'],'reason':facts['reason'],'subject':source['store_name'],'object_type':facts['object_type'],'detail_object_type_basis':basis}
  self.assertIsNone(basis['store_id']);self.assertEqual(c.distribution_type(r)[0],'门店商品')
  basis['source_binding']=dict(basis['source_binding'],source_subject='其他门店');self.assertEqual(c.distribution_type(r),('商品',None))
if __name__=='__main__':unittest.main()
