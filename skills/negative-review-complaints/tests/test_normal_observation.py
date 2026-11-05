"""Pure mocked DOM+XLSX; no live profile is produced or accepted."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import normal_observation as n
import test_authoritative_join as fixtures

def node(key,name='',children=None,**attributes):return {'selector':key,'role':'generic','name':name,'attributes':attributes,'children':children or []}
class NormalObservationTests(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.AuthoritativeJoinTests();self.f.setUp();self.addCleanup(self.f.doCleanups)
        self.f.identity={'provider':'服务商123456789','account_id':'123456789','manager':'测试经理'};self.f.job['identity']=self.f.identity;self.f.write_source()
        self.f.receipt.update(backend='local-dom-bridge',transport_proof={'safety':'DOM-only','reviewed_extension_ready':True,'safety_version':'dom-only-fixture'});self.f.write_receipt()
        self.job=self.f.job
        m=lambda key:{'selector':key}
        self.profile={'company':self.job['company'],'groupid':self.job['groupid'],'kind':'normal-review-observation-v1','status':'live-validated','revision':'mock-only','normal_root':m('list'),'row':{'attributes':{'class':'card'}},'fold_boundary':m('fold'),'negative_filter':m('negative'),'active_class':'selected','date_filter':m('date'),'other_filters':{k:m(k) for k in ('评价类型','评价来源','评价状态')},'filtered_count':m('count'),'pagination_mode':'count-complete',**{k:{'attributes':{'class':k}} for k in ('store','customer','text','action')}}
        card=node('card',children=[node('s','测试门店',**{'class':'store'}),node('c','顾客甲',**{'class':'customer'}),node('t','完整原文\n仍是原文',**{'class':'text'}),node('a','查看投诉结果',**{'class':'action'})],**{'class':'card'})
        root=node('root',children=[node('negative','中差评（1-3心）',**{'class':'selected'}),node('date',value='2026-10-19 ~ 2026-10-20'),*[node(k,value='全部') for k in self.profile['other_filters']],node('count','评价 已筛选1条'),node('list',children=[card,node('fold','折叠评价'),node('ignored',children=[node('ignored-text','不读取完整原文')],**{'class':'card'})])])
        url='https://life.douyin.com/p/life_comment/management?groupid=123456789'
        page=lambda tree:{'tab':{'tabId':17,'url':url,'allowed':True},'observed_at':'2026-10-21T09:05:00+08:00','tree':{'kind':'DOM-derived semantic tree (not native AX)','truncated':False,'url':url.split('?')[0],'root':tree}}
        ident=node('identity','服务商123456789 账户ID 123456789 我的客户经理 测试经理 退出登录',**{'class':'UserCard-index-module__outer--mock'})
        self.envelope={'source':'local-dom-bridge','company':self.job['company'],'groupid':self.job['groupid'],'identity_evidence':page(ident),'pages':[page(root)]}
    def joined(self):return n.joined(self.job,self.envelope,self.profile,self.f.receipt_path,self.f.receipt_hash)
    def find(self,key):return next(x for x in n.flatten(self.envelope['pages'][0]['tree']['root']) if x['selector']==key)
    def test_generic_card_has_no_id_date_or_rating_then_exact_export_join(self):
        result=self.joined();r=result['rows'][0];self.assertEqual(r['stars'],2);self.assertEqual(r['date'],'2026-10-20');self.assertTrue(r['review_id'].startswith('verified-tuple-sha256:'));self.assertFalse(r['star_dom_value_verified']);self.assertEqual(result['filtered_count'],1);self.assertFalse(result['normal_dom_binding']['screenshot_proof'])
    def test_only_observed_empty_body_presentation_chevron_is_accepted(self):
        self.find('t')['children']=[{'tag':'svg','role':'presentation','name':'','attributes':{'class':'icon-K1rG1b'},'children':[{'tag':'g','name':'','children':[{'tag':'path','name':'','children':[]}]}]}]
        self.assertEqual(self.joined()['rows'][0]['text'],'完整原文\n仍是原文')
        self.find('t')['children'][0]['children'][0]['children'][0]['name']='unreviewed'
        with self.assertRaisesRegex(ValueError,'child-text-or-control'):self.joined()

    def test_folded_count_does_not_claim_observed_absence(self):
        self.assertNotIn('observed_folded',self.joined())
        self.profile['count_schema']='normal-input-counts-v2'
        result=self.joined()
        self.assertEqual(result['excluded_folded_count'],0)
        self.assertIsNone(result['observed_folded'])
        self.assertEqual(result['folded_scope'],'not-traversed-not-included')
        self.assertEqual(result['count_semantics']['excluded_folded_count'],'folded-rows-in-input-only')
    def test_raw_visible_text_requires_explicit_schema_and_exact_export_newlines(self):
        self.find('t')['name']='完整原文 仍是原文'
        self.find('t')['public_visible_text']={'method':'visible-innerText-v1','value':'完整原文\n仍是原文','complete':True}
        with self.assertRaisesRegex(ValueError,'match-not-unique'):self.joined()
        self.profile['text_schema']='public-visible-text-v2'
        self.assertEqual(self.joined()['rows'][0]['text'],'完整原文\n仍是原文')
        self.find('t')['public_visible_text']['complete']=False
        with self.assertRaisesRegex(ValueError,'body-evidence-required'):self.joined()
        self.find('t')['public_visible_text'].update(complete=True,value='完整原文 仍是原文')
        with self.assertRaisesRegex(ValueError,'match-not-unique'):self.joined()

    def empty_case(self):
        self.profile.pop('fold_boundary');self.profile.update(normal_root_exclusive=True,scope_mode='verified-empty-normal-list')
        root=self.envelope['pages'][0]['tree']['root'];root['children']=[x for x in root['children'] if x['selector']!='count']
        ls=self.find('list');ls['children']=[node('head',children=[node('count','已筛选0条')],**{'class':'header-sQid1u commentListHeader-jKdTh_'}),node('empty',children=[{'tag':'img','selector':'empty-image','name':'','children':[]},node('emptytext','暂无相关评价',**{'class':'text-Ll5e7y'})],**{'class':'empty-_JoRz3 isPC-PMji6M'})]
    def test_empty_mode_requires_real_ui_empty_shape_and_export_corroboration(self):
        self.empty_case()
        with self.assertRaisesRegex(ValueError,'export-negative-conflict'):self.joined()
        import openpyxl
        wb=openpyxl.load_workbook(self.f.source);wb.active.cell(2,4,'5星');wb.save(self.f.source);wb.close()
        self.f.receipt.update(src_sha256=n.authority.digest(self.f.source),bytes=self.f.source.stat().st_size);self.f.write_receipt()
        out=self.joined();self.assertEqual(out['rows'],[]);self.assertEqual(out['normal_scope_mode'],'verified-empty-normal-list');self.assertFalse(out['normal_scope_proof']['fold_boundary_applicable']);self.assertIsNone(out['normal_scope_proof']['observed_folded'])
        self.find('emptytext')['name']='加载中'
        with self.assertRaisesRegex(ValueError,'label-unverified'):self.joined()
    def test_empty_mode_rejects_extra_records_pagination_and_nonzero_header(self):
        for change in ['extra','header','pager']:
            self.setUp();self.empty_case()
            if change=='extra':self.find('list')['children'].append(node('foreign','评价'))
            elif change=='header':self.find('count')['name']='已筛选1条'
            else:self.find('empty')['children'].append(node('pager','1/1'))
            with self.assertRaises(ValueError):self.joined()

    def test_original_zero_before_real_fold_boundary_keeps_scope_without_reading_folded(self):
        self.find('list')['children']=self.find('list')['children'][1:]
        self.find('count')['name']='已筛选0条'
        out=self.joined();self.assertEqual(out['rows'],[]);self.assertNotIn('normal_scope_mode',out)
        self.assertEqual(out['authority_binding']['export_rows'],1)

    def test_actual_saved_shanghai_zero_snapshot_has_explicit_empty_scope(self):
        import json
        base=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/frozen-20261020-20261021/02-shanghai'
        p=base/'navigation-evidence/008-observeNegative-read-009.json'
        if not p.exists():self.skipTest('actual immutable discovery fixture absent')
        proof=n.navigation_probe(json.loads(p.read_text()),json.loads((base/'navigation-job.json').read_text()))
        self.assertEqual(proof['normal_count'],0);self.assertEqual(proof['normal_rows'],[]);self.assertIsNone(proof['boundary_selector']);self.assertFalse(proof['normal_scope_proof']['fold_boundary_applicable'])

    def test_actual_complete_normal_list_without_fold_is_verified_not_invented_boundary(self):
        import json
        base=Path(__file__).resolve().parents[3]/'work/live-acceptance/complaints/frozen-20261020-20261021/01-yantai';p=base/'navigation-evidence/009-observeNegative-read-010.json'
        if not p.exists():self.skipTest('actual immutable no-fold discovery absent')
        tree=json.loads(p.read_text());job=json.loads((base/'navigation-job.json').read_text());proof=n.navigation_probe(tree,job)
        self.assertEqual(proof['normal_count'],1);self.assertIsNone(proof['boundary_selector']);self.assertEqual(proof['normal_scope_mode'],'verified-complete-normal-list');self.assertEqual(proof['normal_rows'][0]['action'],'投诉')
        root=next(x for x in n.flatten(tree['root']) if 'commentList-hkujq4' in x.get('attributes',{}).get('class','').split())
        for mutation in ['enabled-next','wrong-total','extra-child']:
            r=copy.deepcopy(root)
            if mutation=='enabled-next':r['children'][-1]['children'][1]['children'][2]['attributes']['class']='button-j4VxiA'
            elif mutation=='wrong-total':r['children'][-1]['children'][0]['name']='共2条记录'
            else:r['children'].append(node('extra','不明内容'))
            with self.assertRaises(ValueError):n.complete_normal_list(r,1)

    def test_pending_profile_never_accepted(self):
        self.profile['status']='awaiting-live-validation'
        with self.assertRaisesRegex(ValueError,'awaiting-live'):self.joined()
    def test_folded_section_excluded_even_unknown_fields_but_body_collapsed_allowed(self):
        self.find('t')['attributes']['class']='text isCollapsed';self.profile['text']={'selector':'t'}
        self.assertEqual(len(self.joined()['rows']),1)
        self.find('fold')['selector']='different'
        with self.assertRaisesRegex(ValueError,'fold-boundary'):self.joined()
    def test_partial_or_whitespace_compressed_text_never_fuzzy_matches(self):
        for text in ('完整原文…','完整原文 仍是原文'):
            self.find('t')['name']=text
            with self.assertRaisesRegex(ValueError,'match-not-unique'):self.joined()
    def test_truncated_aggregate_and_cap_refuse(self):
        self.envelope['pages'][0]['tree']['truncated']=True
        with self.assertRaises(ValueError):self.joined()
        self.envelope['pages'][0]['tree']['truncated']=False;self.find('t')['name']='字'*800
        with self.assertRaisesRegex(ValueError,'may-be-truncated'):self.joined()
        self.find('t')['name']='完整原文\n仍是原文';self.find('t')['children']=[node('hidden','other')]
        with self.assertRaisesRegex(ValueError,'unreviewed-children'):self.joined()
    def test_context_identity_dates_and_selected_filter_required(self):
        original=copy.deepcopy(self.envelope)
        for mutate in [lambda:self.envelope['pages'][0]['tab'].update(url='https://life.douyin.com/p/life_comment/management?groupid=99'),lambda:self.find('date')['attributes'].update(value='2026-10-20 ~ 2026-10-20'),lambda:self.find('negative')['attributes'].update({'class':'unselected'}),lambda:self.envelope['identity_evidence']['tree']['root'].update(name='服务商999999999 账户ID 123456789 我的客户经理 测试经理 退出登录')]:
            self.envelope=copy.deepcopy(original);mutate()
            with self.assertRaises(ValueError):self.joined()
    def test_incomplete_count_and_explicit_page_end_rejected(self):
        self.find('count')['name']='评价 已筛选2条'
        with self.assertRaisesRegex(ValueError,'pagination-count'):self.joined()
        self.find('count')['name']='评价 已筛选1条';self.profile.update(pagination_mode='explicit-pages',current_page={'selector':'page'},next_page={'selector':'next'})
        self.envelope['pages'][0]['tree']['root']['children'] += [node('page','1'),node('next','下一页',**{'aria-disabled':'false'})]
        with self.assertRaisesRegex(ValueError,'page-end'):self.joined()
        self.find('next')['attributes']['aria-disabled']='true';self.assertEqual(len(self.joined()['rows']),1)
    def explicit_fixture(self):
        self.profile.update(pagination_mode='explicit-pages',current_page={'selector':'page'},next_page={'selector':'next'})
        self.envelope['pages'][0]['tree']['root']['children'] += [node('page','1'),node('next','下一页',**{'aria-disabled':'false'})]

    def test_explicit_pages_require_each_page_sequence_and_terminal_evidence(self):
        self.explicit_fixture();first=copy.deepcopy(self.envelope['pages'][0]);second=copy.deepcopy(first)
        self.envelope['pages']=[first,second]
        # Page 1 cannot claim to be terminal while page 2 remains in the source.
        self.find('next')['attributes']['aria-disabled']='true'
        with self.assertRaisesRegex(ValueError,'page-end-unverified'):self.joined()
        self.find('next')['attributes']['aria-disabled']='false'
        with self.assertRaisesRegex(ValueError,'page-sequence-unverified'):self.joined()
        # A missing first page cannot be promoted to complete even if only one
        # page has been supplied; and last-page evidence is mandatory.
        self.envelope['pages']=[second]
        self.find('page')['name']='2';self.find('next')['attributes']['aria-disabled']='true'
        with self.assertRaisesRegex(ValueError,'page-sequence-unverified'):self.joined()
        self.find('page')['name']='1';self.find('next')['attributes']['aria-disabled']='false'
        with self.assertRaisesRegex(ValueError,'page-end-unverified'):self.joined()

    def test_explicit_pages_reject_missing_rows_and_duplicate_canonical_review(self):
        self.explicit_fixture();self.find('count')['name']='已筛选2条'
        self.find('next')['attributes']['aria-disabled']='true'
        with self.assertRaisesRegex(ValueError,'pagination-count-incomplete'):self.joined()
        first=copy.deepcopy(self.envelope['pages'][0]);second=copy.deepcopy(first)
        next(x for x in n.flatten(first['tree']['root']) if x['selector']=='next')['attributes']['aria-disabled']='false'
        next(x for x in n.flatten(second['tree']['root']) if x['selector']=='page')['name']='2'
        self.envelope['pages']=[first,second]
        with self.assertRaisesRegex(ValueError,'duplicate-normal-review'):self.joined()

if __name__=='__main__':unittest.main()
