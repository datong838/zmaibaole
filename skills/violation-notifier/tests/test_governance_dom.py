"""Offline public DOM fixtures; no bridge calls or business batches."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import governance_dom as g
seq=0
def n(name='',tag='div',cs='',children=None,**kw):
 global seq;seq+=1
 return dict(name=name,tag=tag,role={'input':'textbox','th':'columnheader','td':'cell','tr':'row','table':'table'}.get(tag,'generic'),attributes={'class':cs},selector='#n'+str(seq),children=children or [],**kw)
def tree():
 subject=n('模拟店','span','name-iUMfRa');cells=[n('一般 模拟原因 ID: TEST123','td'),n('模拟店 门店ID：123','td',children=[subject]),*[n(x,'td') for x in ['模拟商品','已生效','警告','2026/10/20','-','不可申诉','-']],n('查看详情','td',children=[n('查看详情','a','governance_merchant-link link-gpKMLO')])]
 table=n(tag='table',cs='governance_merchant-Table-Implement',children=[n(tag='thead',children=[n(tag='tr',cs='governance_merchant-Table-Row',children=[n(x,'th') for x in g.HEADERS])]),n(tag='tbody',children=[n(tag='tr',cs='governance_merchant-Table-Row',children=cells)])])
 datefield=n('违规时间','input','governance_merchant-input',placeholder='请选择');datefield['attributes']['value']='2026/10/16 ～ 2026/10/20'
 pager=n(cs='governance_merchant-pager',children=[n('1','li','governance_merchant-pager-item governance_merchant-pager-item-checked'),n('','li','governance_merchant-pager-item governance_merchant-pager-item-disabled',children=[n(cs='governance_merchant-icon-right')])])
 r=n(children=[n(cs='governance_merchant-date-picker-range',children=[datefield]),n('全部1',cs='governance_merchant-tab-bar-item governance_merchant-tab-bar-item-active'),n('只看未读','label','governance_merchant-checkbox',children=[n(cs='governance_merchant-checkbox-icon-uncheck')]),table,pager,n('查询','button','governance_merchant-btn')]);r['attributes']['id']='governanceRoot';return {'url':'https://life.douyin.com'+g.RECORDS,'truncated':False,'root':r}
def with_calendar(t):
 views=[]
 for month,side in [(9,'start'),(10,'end')]:
  view=n(cs='governance_merchant-date-view governance_merchant-date-position-'+side,children=[n(f'2026年{month}月',cs='governance_merchant-date-title'),n('',cs='governance_merchant-date-nav-prev',children=[n(cs='governance_merchant-icon-left')]),n('',cs='governance_merchant-date-nav-next',children=[n(cs='governance_merchant-icon-right')]),*[n(str(d),tag='span',cs='governance_merchant-date-col governance_merchant-date-grid-in',children=[n(str(d),cs='governance_merchant-date-date governance_merchant-date-item governance_merchant-date-grid-in')]) for d in [16,20]]]);views.append(view)
 t['root']['children'].append(n(cs='governance_merchant-date-picker-popper',children=views));return t
class GovernanceTests(unittest.TestCase):
 def test_actual_tr_columns_id_and_subject_parse(self):
  p=g.records_page(tree(),start='2026-10-16',end_exclusive='2026-10-21');self.assertEqual(p['rows'][0]['notice_id'],'TEST123');self.assertEqual(g.complete_pages([p])[0]['store_name'],'模拟店')
 def test_date_not_exposed_or_not_applied_never_claims_query(self):
  t=tree();field=g.date_input(t);field['attributes'].pop('value')
  with self.assertRaisesRegex(ValueError,'not-exposed'):g.records_page(t,start='2026-10-16',end_exclusive='2026-10-21')
 def test_wrong_dates_rows_and_truncation_stop(self):
  for mode in ['date','range','truncated']:
   t=tree()
   if mode=='date':g.date_input(t)['attributes']['value']='2026/10/15 ~ 2026/10/20'
   elif mode=='truncated':t['truncated']=True
   with self.subTest(mode=mode),self.assertRaises(ValueError):g.records_page(t,start='2026-10-19' if mode=='range' else '2026-10-16',end_exclusive='2026-10-20' if mode=='range' else '2026-10-21')
 def test_duplicate_id_generic_row_unread_and_wrong_headers_stop(self):
  for mode in ['duplicate','generic','unread','header']:
   t=tree();ns=g.nodes(t);row=next(x for x in ns if x['tag']=='tr' and x.get('children') and x['children'][0]['tag']=='td')
   if mode=='duplicate':next(x for x in ns if x['tag']=='tbody')['children'].append(copy.deepcopy(row))
   elif mode=='generic':row['role']='generic'
   elif mode=='unread':next(x for x in ns if x['tag']=='label')['children'][0]['attributes']['class']='governance_merchant-checkbox-icon-check'
   else:next(x for x in ns if x['tag']=='th')['name']='未知表头'
   with self.subTest(mode=mode),self.assertRaises(ValueError):
    p=g.records_page(t,start='2026-10-16',end_exclusive='2026-10-21');g.complete_pages([p])
 def test_calendar_absolute_date_selects_in_month_only(self):
  t=with_calendar(tree());a=g.calendar_action(t,'2026-10-16');self.assertEqual(a['selects_date'],'2026-10-16');self.assertFalse(a['month_navigation'])
 def test_disabled_missing_day_rejected_month_navigation_uses_observed_icon(self):
  t=with_calendar(tree());a=g.calendar_action(t,'2026-08-16');self.assertTrue(a['month_navigation']);self.assertEqual(a['expected_month_delta'],-1)
  with self.assertRaisesRegex(ValueError,'disabled-or-missing'):g.calendar_action(t,'2026-10-17')
 def test_duplicate_calendar_or_month_title_rejected(self):
  t=with_calendar(tree());t['root']['children'].append(copy.deepcopy(t['root']['children'][-1]))
  with self.assertRaises(ValueError):g.calendar(t)
 def test_page_coverage_requires_all_unique_ids_consistent_total_and_final_page(self):
  p=g.records_page(tree(),start='2026-10-16',end_exclusive='2026-10-21')
  for changed in [[{**p,'page':2}],[{**p,'total':2}],[{**p,'next':{'disabled':False}}],[{**p,'query_verified':False}]]:
   with self.subTest(changed=changed),self.assertRaises(ValueError):g.complete_pages(changed)
 def test_query_plan_has_no_guessing_or_replay(self):
  q=g.QueryPlan('2026-10-16','2026-10-21');t=with_calendar(tree());self.assertEqual(q.next(t,{'phase':'select-start'})['selected_date'],'2026-10-16');self.assertEqual(q.next(t,{'phase':'select-end'})['selected_date'],'2026-10-20');self.assertEqual(q.next(t,{'phase':'verify-date'})['next_phase'],'collect-page')
  with self.assertRaisesRegex(ValueError,'unknown-intent'):q.next(t,{'unknown_intent':True})
if __name__=='__main__':unittest.main()
