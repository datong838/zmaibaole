import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from dom_evidence import identity, context, exact, calendar_day, verified_review_filter, all_store_scope, generated_record, export_tag, export_calendar_day, company_switch

def tree(children):return {'truncated':False,'root':{'name':'','children':children}}
def leaf(name,**kw):return {'name':name,'selector':'#'+name,'children':[],**kw}
class EvidenceTest(unittest.TestCase):
    def test_identity_requires_every_visible_field_and_stable_baseline(self):
        t=tree([leaf('服务商123456789'),leaf('账户ID'),leaf('987654321'),leaf('我的客户经理'),leaf('李先生')])
        expected={'provider':'服务商123456789','account_id':'987654321','manager':'李先生'}
        self.assertEqual(identity(t),expected)
        with self.assertRaisesRegex(ValueError,'account-changed'):identity(t,{**expected,'manager':'其他人'})
        with self.assertRaises(ValueError):identity(tree(t['root']['children'][:-1]))
    def test_explicit_tab_company_and_origin(self):
        tabs=[{'tabs':[{'tabId':5,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'}]}]
        self.assertEqual(context(tabs,5,'123')['groupid'],'123')
        for tab,gid in [(6,'123'),(5,'456')]:
            with self.assertRaises(ValueError):context(tabs,tab,gid)
    def test_duplicate_leaf_and_truncated_tree_rejected(self):
        with self.assertRaises(ValueError):exact(tree([leaf('导出'),leaf('导出')]),'导出')
        with self.assertRaises(ValueError):exact({'truncated':True,'root':{}},'导出')
    def test_new_export_record_cannot_reuse_old_same_name(self):
        dates={'start':'2026-10-16','end':'2026-10-19'};tag=export_tag(dates)
        def row(stamp):return leaf(tag+' '+stamp+' 生成成功 下载 删除',attributes={'class':'byted-table-row'})
        old={'text':tag+' 2026-10-20 14:00:00 生成中','generated_at':'2026-10-20 14:00:00'}
        self.assertIsNone(generated_record(tree([row('2026-10-20 14:00:00')]),dates,[old]))
        actual=generated_record(tree([row('2026-10-20 14:00:00'),row('2026-10-21 02:00:00')]),dates,[old])
        self.assertEqual(actual['generated_at'],'2026-10-21 02:00:00')
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            generated_record(tree([row('2026-10-21 02:00:00'),row('2026-10-21 02:00:01')]),dates,[old])
    def test_all_store_scope_cannot_be_replaced_by_one_store(self):
        node=leaf('按省市 全部门店',attributes={'id':'CommentPoi_select'})
        self.assertTrue(all_store_scope(tree([node])))
        node['name']='按省市 某一家门店'
        with self.assertRaisesRegex(ValueError,'nondefault-store-scope'):all_store_scope(tree([node]))
    def test_new_merchant_switch_bound_to_verified_identity_card(self):
        button=leaf('切换',role='button',attributes={'class':'SwitchCard-index-module__switch-card-button--observed'})
        switch={'name':'商户 服务商123456789 切换','attributes':{'class':'SwitchCard-index-module__switch-card--observed'},'children':[button]}
        card={'name':'服务商123456789 账户ID987654321 我的客户经理陈方圆 退出登录','attributes':{'class':'UserCard-index-module__outer--observed'},'children':[switch]}
        t=tree([leaf('切换',role='button'),card])
        self.assertIs(company_switch(t),button)
        switch['name']='商户 服务商999999999 切换'
        with self.assertRaisesRegex(ValueError,'merchant-switch-card-unverified'):company_switch(t)
    def test_day_scoped_to_explicit_month(self):
        def month(label):
            return {'name':label+' 16','children':[{'name':'16','attributes':{'class':'byted-date-col byted-date-date'},'children':[leaf('16')]}]}
        t=tree([month('2026年9月'),month('2026年10月')])
        self.assertEqual(calendar_day(t,'2026-10-16')['name'],'16')
        with self.assertRaises(ValueError):calendar_day(t,'2026-11-16')
    def test_export_calendar_excludes_background_picker(self):
        def month(selector):
            return {'name':'2026年10月 16','children':[{'name':'16','attributes':{'class':'byted-date-col byted-date-date'},'children':[dict(leaf('16'),selector=selector)]}]}
        dates={'start':'2026-10-16','end':'2026-10-19'}
        field=leaf('',role='textbox',placeholder='请选择日期范围，不选则为近一年')
        modal={'name':'请选择要导出的评价范围 *所属门店 按省市 全部门店','attributes':{'class':'byted-modal'},'children':[field,month('#modal-day')]}
        t=tree([month('#background-day'),modal])
        with self.assertRaisesRegex(ValueError,'calendar-day-or-month-unverified'):calendar_day(t,dates['start'])
        self.assertEqual(export_calendar_day(t,dates,dates['start'])['selector'],'#modal-day')
        modal['children'].append(month('#ambiguous-modal-day'))
        with self.assertRaisesRegex(ValueError,'calendar-day-or-month-unverified'):export_calendar_day(t,dates,dates['start'])
    def test_duplicate_or_missing_group_query_and_foreign_origin_rejected(self):
        for url in ('https://life.douyin.com/?groupid=123&groupid=123','https://life.douyin.com/','https://example.com/?groupid=123'):
            tabs=[{'tabs':[{'tabId':5,'allowed':True,'url':url}]}]
            with self.assertRaises(ValueError):context(tabs,5,'123')
    def test_ambiguous_or_truncated_identity_rejected(self):
        t=tree([leaf('服务商123456789'),leaf('服务商111111111'),leaf('账户ID987654321'),leaf('我的客户经理李先生')])
        with self.assertRaisesRegex(ValueError,'identity-provider'):identity(t)
        t=tree([leaf('服务商123456789\n账户ID987654321\n我的客户经理李先生'+'x'*800,attributes={'class':'UserCard-index-module__outer--fixture'})])
        with self.assertRaisesRegex(ValueError,'may-be-truncated'):identity(t)
    def test_review_filter_rejects_other_filters_or_wrong_range(self):
        dates={'start':'2026-10-16','end':'2026-10-19'}
        inputs=[leaf(label,role='textbox',attributes={'value':value}) for label,value in [('评价时间','2026-10-16 ~ 2026-10-19'),('评价类型','全部'),('评价来源','全部'),('评价状态','全部')]]
        t=tree(inputs+[leaf('评价 已筛选 23 条')])
        self.assertEqual(verified_review_filter(t,dates)['page_filtered'],23)
        inputs[1]['attributes']['value']='差评'
        with self.assertRaisesRegex(ValueError,'nondefault-review-filter'):verified_review_filter(t,dates)
if __name__=='__main__':unittest.main()
