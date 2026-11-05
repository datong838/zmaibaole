"""Public saved first page plus synthetic reconciliation; no browser operations."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import center_reconciliation as m
PROJECT=Path(__file__).resolve().parents[3]
PAGE=PROJECT/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/profile-discovery-evidence/000-all-reasons.json'

class CenterTests(unittest.TestCase):
    def saved(self):
        return m.center_page(json.loads(PAGE.read_text())['tree'],start='2026-10-16',end_exclusive='2026-10-21')
    def synthetic(self):
        first=self.saved();second=copy.deepcopy(first);second.update(page=2,next=None)
        second['top10']=[{'rank':i+1,'violation_type':name,'object_types':['模拟对象'],'count':1} for i,name in enumerate(first['legend'][5:10],5)]
        types={r['violation_type']:r['object_types'][0] for r in first['top10']+second['top10']}
        counts={r['violation_type']:r['count'] for r in first['top10']+second['top10']}
        rows=[]
        for name in first['legend']:
            for _ in range(counts.get(name,1)):
                rows.append({'notice_id':'mock-'+str(len(rows)),'reason':name,'object_type':types.get(name,'模拟对象'),'detail_read':True,'date':'2026-10-18'})
        return [first,second],rows
    def test_actual_saved_first_page_does_not_claim_full_distribution(self):
        p=self.saved();self.assertEqual((p['page'],p['page_count'],len(p['legend']),len(p['top10'])),(1,2,12,5))
        self.assertEqual([r['count'] for r in p['top10']],[2,2,2,2,1]);self.assertEqual(p['next']['kind'],'navigation')
    def test_partial_top10_cannot_stand_in_for_all_reasons(self):
        pages,rows=self.synthetic()
        with self.assertRaisesRegex(ValueError,'pagination-incomplete'):m.reconcile(pages[:1],rows)
    def test_full_synthetic_records_drive_all_twelve_buckets(self):
        pages,rows=self.synthetic();result=m.reconcile(pages,rows)
        self.assertEqual(len(result['rows']),12);self.assertEqual(result['total'],16)
        self.assertFalse(result['top10_is_complete_distribution']);self.assertIn('complete-records',result['basis'])
    def test_legend_count_type_detail_and_date_conflicts_refuse(self):
        changes=[lambda ps,rs:rs[0].update(reason='不在图例中'),lambda ps,rs:rs[0].update(object_type='错误对象'),
                 lambda ps,rs:rs[0].update(detail_read=False),lambda ps,rs:rs[0].update(date='2026-10-21'),
                 lambda ps,rs:ps[0]['top10'][0].update(count=3),lambda ps,rs:rs[1].update(notice_id=rs[0]['notice_id'])]
        for change in changes:
            pages,rows=self.synthetic();change(pages,rows)
            with self.assertRaises(ValueError):m.reconcile(pages,rows)
    def test_wrong_range_rejects_actual_tree(self):
        with self.assertRaisesRegex(ValueError,'range-input'):m.center_page(json.loads(PAGE.read_text())['tree'],start='2026-10-17',end_exclusive='2026-10-21')

if __name__=='__main__':unittest.main()
