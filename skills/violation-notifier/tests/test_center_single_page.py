import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'))
import center_reconciliation as m
SOURCE=Path(__file__).with_name('fixtures')/'center-single-page-20261021.json'
class SinglePageTests(unittest.TestCase):
 def tree(self):return json.loads(SOURCE.read_bytes())['tree']
 def parse(self,t):return m.center_page(t,start='2026-10-21',end_exclusive='2026-10-22')
 def find(self,t,c):return m.g.one(m.g.classnodes(m.g.root(t),c),'fixture-class')
 def test_actual_single_bucket_is_not_record_completion(self):
  p=self.parse(self.tree());self.assertEqual((p['page'],p['page_count'],p['next']),(1,1,None));self.assertEqual(p['top10'],[{'rank':1,'violation_type':'商品资质缺失','object_types':['商品'],'count':4}]);self.assertNotIn('all_reasons_read',p)
  with self.assertRaises(ValueError):m.reconcile([p],[])
 def test_independent_records_must_match(self):
  p=self.parse(self.tree());rows=[{'notice_id':str(i),'reason':'商品资质缺失','object_type':'商品','detail_read':True,'date':'2026-10-21'} for i in range(4)]
  self.assertEqual(m.reconcile([p],rows)['total'],4)
  with self.assertRaisesRegex(ValueError,'bucket-mismatch'):m.reconcile([p],rows[:-1])
 def test_incomplete_legend_rejects(self):
  t=self.tree();legend=self.find(t,'legendContainer-qMBl3_');n=copy.deepcopy(self.find(t,'legendText-wzfAPl'));n['name']='额外原因';legend['children'].append(n)
  with self.assertRaisesRegex(ValueError,'legend-incomplete'):self.parse(t)
 def test_missing_rows_rejects(self):
  t=self.tree();self.find(t,'list-FeirmF')['children']=[]
  with self.assertRaisesRegex(ValueError,'empty-or-too-large'):self.parse(t)
 def test_wrong_rank_rejects(self):
  t=self.tree();self.find(t,'rank-mj9wvJ')['name']='2'
  with self.assertRaisesRegex(ValueError,'ranks-not-consecutive'):self.parse(t)
 def test_wrong_title_rejects(self):
  t=self.tree();self.find(t,'title-KYD1nB')['name']='预警原因 Top10'
  with self.assertRaisesRegex(ValueError,'title-conflict'):self.parse(t)
 def test_unknown_structure_rejects(self):
  t=self.tree();self.find(t,'topList-DDjs8Y')['children'].append({'tag':'div','name':'下一页','children':[]})
  with self.assertRaisesRegex(ValueError,'structure-conflict'):self.parse(t)
 def test_loading_rejects(self):
  t=self.tree();self.find(t,'list-FeirmF')['attributes']['aria-busy']='true'
  with self.assertRaisesRegex(ValueError,'loading'):self.parse(t)
 def test_orphan_pager_rejects(self):
  t=self.tree();self.find(t,'header-RySODJ')['children'].append({'tag':'li','name':'2','attributes':{'class':'governance_merchant-pager-item'},'children':[]})
  with self.assertRaisesRegex(ValueError,'orphan-pager'):self.parse(t)
 def test_truncated_tree_rejects(self):
  t=self.tree();t['truncated']=True
  with self.assertRaisesRegex(ValueError,'complete-tree'):self.parse(t)
 def test_multi_page_legend_without_pager_cannot_claim_one_page(self):
  t=self.tree();legend=self.find(t,'legendContainer-qMBl3_');original=copy.deepcopy(self.find(t,'legendText-wzfAPl'))
  for i in range(5):
   n=copy.deepcopy(original);n['name']='其他原因'+str(i);legend['children'].append(n)
  with self.assertRaisesRegex(ValueError,'legend-incomplete'):self.parse(t)
if __name__=='__main__':unittest.main()
