"""Pure mocked judgments/evidence. Does not claim AI or live UI acceptance."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import classification_policy as p
class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.key='123:a';identity={'provider':'服务商123','account_id':'account','manager':'经理'}
        self.rows=[{'review_id':k,'store':'测试榴莲店','customer':name,'text':'榴莲很甜很好吃。混蛋，去隔壁某店。','stars':1,'date':'2026-10-20','product':'金枕榴莲','section':'filtered'} for k,name in [('a','顾客甲'),('b','顾客甲'),('c','顾客乙')]]
        self.source=self.pin({'company':'测试公司','groupid':'123','source':'local-dom-bridge','identity':identity,'account_verified':True,'rows':self.rows})
        self.state={'company':'测试公司','groupid':'123','identity':identity,'browser_backend':'local-dom-bridge','tasks':{'123:'+r['review_id']:{'review':r.copy(),'latest_snapshot':self.source} for r in self.rows}}
        self.samples=[{'category':'其他','date':'2026-10-19','text':str(i)+'用户反馈后，请求平台核查相关材料；不直接认定责任。'} for i in range(4)];history=self.pin({'items':self.samples});self.state['tasks'][self.key]['history']={'items':self.samples,'evidence':history}
        self.analysis={'classification_policy_version':p.VERSION,'review_key':self.key,'snapshot_sha256':self.source['sha256'],'agent_assessed':True,'no_fabricated_facts':True,'category':'其他','platform_category_evidence':{'category_label':'其他'},'suspected_bulk':False,'related_ids':[],'type_assessments':{c:{'match':c=='其他','reason':'模型对'+c+'给出的逐项判断理由','evidence':[self.ev(self.key)]} for c in p.CATEGORIES},'history_sha256':history['sha256'],'history_usage':'wording-reference-only','sampled_history_facts_reused':False,'history_style_references':[{'sample_sha256':p.data_sha(x),'quoted_original':'请求平台核查相关材料','style_observation':'先概括反馈再请求核实，仅借鉴句式。','unverified_facts_reused':False} for x in self.samples[:3]]}
        self.analysis['exclusion_reasons']={c:self.analysis['type_assessments'][c]['reason'] for c in p.SPECIFIC}
    def pin(self,v):
        raw=json.dumps(v,ensure_ascii=False).encode();sha=hashlib.sha256(raw).hexdigest();f=self.root/(sha+'.json');f.write_bytes(raw);return {'path':str(f),'sha256':sha}
    def ev(self,key):return {'review_key':key,'source_sha256':self.source['sha256'],'quotes':[self.rows[0]['text']]}
    def validate(self):return p.validate(self.state,self.key,self.analysis)
    def choose(self,c):
        self.analysis['type_assessments'][c]['match']=True;self.analysis['type_assessments']['其他']['match']=False;self.analysis['category']=c;self.analysis['platform_category_evidence']['category_label']=c
    def test_other_requires_all_four_exclusions_and_three_distinct_original_styles(self):
        self.assertEqual(self.validate()['category'],'其他');self.analysis['history_style_references'].pop()
        with self.assertRaisesRegex(ValueError,'more-history'):self.validate()
    def test_missing_category_boolean_or_original_quote_refuses(self):
        for mutate in [lambda a:a['type_assessments'].pop('批量差评'),lambda a:a['type_assessments']['错评错点'].update(match='false'),lambda a:a['type_assessments']['脏话辱骂']['evidence'][0].update(quotes=['原文没有这个辱骂'])]:
            old=copy.deepcopy(self.analysis);mutate(self.analysis)
            with self.assertRaises(ValueError):self.validate()
            self.analysis=old
    def test_other_cannot_override_any_specific_match(self):
        self.analysis['type_assessments']['脏话辱骂']['match']=True
        with self.assertRaisesRegex(ValueError,'not-a-fallback'):self.validate()
    def test_ai_supplied_insult_verdict_uses_exact_quote_without_keyword_engine(self):
        self.choose('脏话辱骂');self.analysis['type_assessments']['脏话辱骂']['evidence'][0]['quotes']=['混蛋'];self.assertEqual(self.validate()['platform_category'],'脏话辱骂')
    def test_multiple_specific_matches_require_primary_explanation(self):
        self.choose('脏话辱骂');wrong=self.analysis['type_assessments']['错评错点'];wrong.update(match=True,basis='praise-with-low-stars',contradiction_reason='原文夸赞但一星，模型评估该矛盾')
        with self.assertRaisesRegex(ValueError,'primary-reason'):self.validate()
        self.analysis['primary_selection_reason']='辱骂直接可见，优先以该类作为主选，低星矛盾作为并存线索。';self.assertEqual(len(self.validate()['matched_specific_types']),2)
    def bulk(self,peer='123:b'):
        self.choose('批量差评');self.analysis['type_assessments']['批量差评']['evidence'].append(self.ev(peer));self.analysis.update(suspected_bulk=True,identity_uncertain=True,related_ids=[peer],similarity_reason='同日同名两条原文相同，身份仍不能确认',bulk_evidence={'review_keys':[self.key,peer],'identity_uncertain':True,'similarity_reason':'同日同名两条原文相同，身份仍不能确认'})
    def test_bulk_requires_at_least_two_same_day_same_name_real_sources(self):
        self.bulk();self.assertEqual(self.validate()['category'],'批量差评');self.analysis['bulk_evidence']['review_keys']=[self.key]
        with self.assertRaisesRegex(ValueError,'two-source'):self.validate()
    def test_bulk_different_customer_or_identity_certainty_refuses(self):
        self.bulk('123:c')
        with self.assertRaisesRegex(ValueError,'same-date-name'):self.validate()
        self.setUp();self.bulk();self.analysis['bulk_evidence']['identity_uncertain']=False
        with self.assertRaisesRegex(ValueError,'not-identity-proof'):self.validate()
    def test_wrong_review_has_either_product_contradiction_or_praise_low_rating(self):
        self.choose('错评错点');a=self.analysis['type_assessments']['错评错点'];a.update(basis='product-content-contradiction',contradiction_reason='模型说明商品与文意的矛盾')
        with self.assertRaisesRegex(ValueError,'product-evidence'):self.validate()
        a['product_evidence']={'source_sha256':self.source['sha256'],'product':'金枕榴莲','content_quote':self.rows[0]['text']};self.assertEqual(self.validate()['category'],'错评错点');a['product_evidence']['product']='未核实商品'
        with self.assertRaisesRegex(ValueError,'product-evidence'):self.validate()
    def test_peer_subtype_maps_only_to_actual_platform_options(self):
        self.choose('同行刷屏');a=self.analysis['type_assessments']['同行刷屏'];a.update(subtype='peer-review-spam',spam_or_attack_reason='模型根据原文解释引导线索')
        with self.assertRaisesRegex(ValueError,'platform-category'):self.validate()
        self.analysis['platform_category_evidence']['category_label']='同行刷评';self.assertEqual(self.validate()['platform_category'],'同行刷评');a['subtype']='hotspot-attack';self.analysis['platform_category_evidence']['category_label']='热点事件攻击';self.assertEqual(self.validate()['platform_category'],'热点事件攻击')
    def test_original_history_quote_duplicate_or_fact_transfer_reject(self):
        for field,value in [('quoted_original','虚构历史原文'),('unverified_facts_reused',True),('sample_sha256','unknown')]:
            old=copy.deepcopy(self.analysis);self.analysis['history_style_references'][0][field]=value
            with self.assertRaises(ValueError):self.validate()
            self.analysis=old
        self.analysis['history_style_references'][1]=copy.deepcopy(self.analysis['history_style_references'][0])
        with self.assertRaisesRegex(ValueError,'unknown-or-duplicate'):self.validate()
    def test_source_or_history_byte_changes_are_not_accepted(self):
        Path(self.source['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash-mismatch'):self.validate()
if __name__=='__main__':unittest.main()
