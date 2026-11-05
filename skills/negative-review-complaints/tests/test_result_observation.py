"""Mock public result drawers only. No browser and no complaint submission."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import result_observation as r

def n(name='',cl='',children=None,tag='div'):return {'name':name,'attributes':{'class':cl},'children':children or [],'tag':tag}
class ResultObservationTests(unittest.TestCase):
    def setUp(self):
        self.job={'groupid':'123'};self.review={'review_id':'verified-tuple-sha256:canonical','store':'测试店','customer':'顾客','text':'完整原文'}
        fields=[n(children=[n(label,'label-bygbVJ'),n(value,'text-Fp_RCZ')]) for label,value in [('投诉类型','其他'),('投诉理由','实际历史理由，不当作本次事实'),('投诉时间','2026-10-19 09:58:21')]]
        self.drawer=n(cl='byted-drawer-dialog-show',children=[n('投诉评价'),n('投诉失败','status-head-DNErJ9'),n('平台说明','status-content-Uk09gi'),n('测试店','poiName-W9HDFV'),n('顾客','nickName-wB7fZf'),n('完整原文','text-Hl9jZe'),n(children=fields,tag='form')])
        self.page={'tab':{'tabId':17,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'},'tree':{'kind':'DOM-derived semantic tree (not native AX)','truncated':False,'url':'https://life.douyin.com/p/life_comment/management','root':n(children=[self.drawer])},'observed_at':'2026-10-21T10:00:00+08:00'}
    def parse(self):return r.parse(self.job,self.page,self.review)
    def test_exact_card_binding_and_original_public_report_fields(self):
        out=self.parse();self.assertEqual(out['status'],'rejected');self.assertEqual(out['review_key'],'123:verified-tuple-sha256:canonical');self.assertEqual(out['original_complaint']['投诉类型'],'其他');self.assertFalse(out['submitted_by_this_workflow']);self.assertIn('实际历史理由',out['visible_text'])
    def test_v2_drawer_raw_body_preserves_exact_newlines_only_when_opted_in(self):
        self.review['text']='第一行\n第二行';body=self.drawer['children'][5];body['name']='第一行 第二行';body['public_visible_text']={'method':'visible-innerText-v1','complete':True,'value':'第一行\n第二行'}
        with self.assertRaisesRegex(ValueError,'review-mismatch:text'):self.parse()
        self.assertEqual(r.parse(self.job,self.page,self.review,text_schema='public-visible-text-v2')['status'],'rejected')
        body['public_visible_text']['value']='第一行 第二行'
        with self.assertRaisesRegex(ValueError,'review-mismatch:text'):r.parse(self.job,self.page,self.review,text_schema='public-visible-text-v2')
        body['public_visible_text']['complete']=False
        with self.assertRaisesRegex(ValueError,'body-evidence-required'):r.parse(self.job,self.page,self.review,text_schema='public-visible-text-v2')

    def test_wrong_drawer_review_or_duplicate_drawer_never_attaches(self):
        self.drawer['children'][3]['name']='别的店'
        with self.assertRaisesRegex(ValueError,'review-mismatch'):self.parse()
        self.drawer['children'][3]['name']='测试店';self.page['tree']['root']['children'].append(copy.deepcopy(self.drawer))
        with self.assertRaisesRegex(ValueError,'single-result'):self.parse()
    def test_unknown_status_or_loading_or_incomplete_report_refuses(self):
        self.drawer['children'][1]['name']='请稍后'
        with self.assertRaisesRegex(ValueError,'status-label'):self.parse()
        self.drawer['children'][1]['name']='投诉失败';self.drawer['children'][-1]['children'].pop()
        with self.assertRaisesRegex(ValueError,'fields-incomplete'):self.parse()
    def test_capped_text_and_foreign_origin_reject(self):
        self.drawer['children'][-1]['children'][1]['children'][1]['name']='字'*800
        with self.assertRaisesRegex(ValueError,'may-be-truncated'):self.parse()
        self.page['tab']['url']='https://evil.test/p/life_comment/management?groupid=123'
        with self.assertRaisesRegex(ValueError,'context-mismatch'):self.parse()
    def test_observed_empty_presentation_svg_does_not_change_complete_body(self):
        icon=n(cl='icon-K1rG1b',tag='svg',children=[n(tag='g',children=[n(tag='path')])]);icon['role']='presentation';self.drawer['children'][5]['children']=[icon]
        self.assertEqual(self.parse()['status'],'rejected')
        icon['children'][0]['children'][0]['name']='其他正文'
        with self.assertRaisesRegex(ValueError,'child-text'):self.parse()
    def test_arbitrary_body_child_is_not_silently_ignored(self):
        self.drawer['children'][5]['children']=[n('完整原文',tag='span')]
        with self.assertRaisesRegex(ValueError,'unreviewed-children'):self.parse()
    def test_actual_pending_m_drawer_binds_same_current_source(self):
        import json
        root=Path(__file__).resolve().parents[3];p=root/'work/live-acceptance/complaints/live-profile/m-existing-drawer-read-3.json';base=root/'work/live-acceptance/complaints/frozen-20261016-20261020/01-yantai'
        if not p.is_file():self.skipTest('actual pending evidence not present')
        source=json.loads((base/'authoritative-normal-capture.json').read_text());review=next(x for x in source['rows'] if x['customer']=='M.');out=r.parse(json.loads((base/'navigation-job.json').read_text()),json.loads(p.read_text()),review)
        self.assertEqual(out['status'],'pending');self.assertEqual(out['platform_status'],'投诉审核中');self.assertEqual(out['original_complaint']['投诉时间'],'2026-10-20 14:08:45');self.assertEqual(out['original_complaint']['投诉类型'],'其他')
if __name__=='__main__':unittest.main()
