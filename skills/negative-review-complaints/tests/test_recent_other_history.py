"""Offline mock evidence only: no UI, group sends or live ledger writes."""
import copy,json,sys,tempfile,unittest
from datetime import datetime,date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import recent_other_history as h
class SampleHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'evidence').mkdir();self.at=datetime.fromisoformat('2026-10-21T12:00:00+08:00');self.target='123:target';self.sample='123:sample';identity={'provider':'服务商123','account_id':'account','manager':'manager'}
        row={'review_id':'sample','store':'测试店','customer':'顾客','text':'源评价','stars':2,'date':'2026-10-19'}
        source={'company':'测试公司','groupid':'123','source':'local-dom-bridge','identity':identity,'account_verified':True,'rows':[row]};src=self.pin(source)
        result={'review_key':self.sample,'snapshot_sha256':src['sha256'],'source':'local-dom-bridge','url':'https://life.douyin.com/p/life_comment/management?groupid=123','status':'rejected','observed_at':'2026-10-21T09:00:00+08:00','original_complaint':{'投诉类型':'其他','投诉时间':'2026-10-19 10:00:00','投诉理由':'历史原文：商家曾提出的说法，仅供措辞参考'},'submitted_by_this_workflow':False};ref=self.pin(result)
        self.state={'company':'测试公司','groupid':'123','mode':'draft-only','browser_backend':'local-dom-bridge','identity':identity,'tasks':{self.target:{},self.sample:{'snapshot':src,'latest_snapshot':src,'review':row,'result':{**result,'evidence':ref}}}};self.persist();self.out=self.root/'samples.json'
    def pin(self,v):
        raw=json.dumps(v,ensure_ascii=False).encode();import hashlib
        sha=hashlib.sha256(raw).hexdigest();p=self.root/'evidence'/(sha+'.json');p.write_bytes(raw);return {'path':str(p),'sha256':sha}
    def persist(self):(self.root/'state.json').write_text(json.dumps(self.state,ensure_ascii=False))
    def build(self):return h.build(self.root,self.target,self.out,at=self.at,window_days=7)
    def test_nonexhaustive_original_samples_keep_observed_time_and_immutable_refs(self):
        p=self.build();self.assertEqual(p['items'][0]['observed_at'],'2026-10-21T09:00:00+08:00');self.assertEqual(p['items'][0]['text'],self.state['tasks'][self.sample]['result']['original_complaint']['投诉理由']);self.assertFalse(p['all_pages_read']);self.assertFalse(p['is_exhaustive']);self.assertFalse(p['no_history']);self.assertEqual(p['start'],'2026-10-14')
        raw=self.out.read_bytes();self.assertEqual(self.build(),p);self.assertEqual(self.out.read_bytes(),raw)
    def test_workflow_attaches_samples_and_requires_wording_only_analysis(self):
        import workflow as w
        from unittest.mock import patch
        doc=self.build();task=self.state['tasks'][self.target];source=self.state['tasks'][self.sample]['snapshot'];task.update(action='投诉',status='pending',review={'text':'不是很甜'},latest_snapshot=source,screenshot=source,wecom=source)
        with patch.object(w,'save',side_effect=lambda root,state,event:state),patch.object(w,'shanghai_today',return_value=date(2026,10,21)):
            w.attach_history(self.root,self.state,self.target,self.out)
            self.assertEqual(task['history']['mode'],h.MODE);self.assertFalse(task['history']['is_exhaustive'])
            analysis={'review_key':self.target,'snapshot_sha256':source['sha256'],'category':'其他','reason':'主观口味体验，需如实核对','draft':'请核实具体消费问题，不断言商家事实','agent_assessed':True,'no_fabricated_facts':True,'quotes':['不是很甜'],'suspected_bulk':False,'history_sha256':task['history']['evidence']['sha256']};p=self.root/'analysis.json';p.write_text(json.dumps(analysis))
            # This test isolates history semantics; category evidence has its own suite.
            with patch.object(w,'final_screenshot',return_value=True),patch('draft_inspection.validate_analysis',return_value={}),patch('classification_policy.validate',return_value={}):
                with self.assertRaisesRegex(ValueError,'facts-must-not-be-reused'):w.analyze(self.root,self.state,self.target,p)
                analysis.update(history_usage='wording-reference-only',sampled_history_facts_reused=False);p.write_text(json.dumps(analysis));w.analyze(self.root,self.state,self.target,p)
            self.assertEqual(task['status'],'draft_ready')

    def test_foreign_root_target_exhaustive_flag_and_reason_tamper_refuse(self):
        p=self.build()
        for mutate in [lambda q:q.update(root='/other'),lambda q:q.update(target_review_key='123:foreign'),lambda q:q.update(all_pages_read=True),lambda q:q['items'][0].update(text='改写伪造理由')]:
            q=copy.deepcopy(p);mutate(q)
            with self.assertRaises(ValueError):h.validate(self.root,self.state,self.target,q,as_of=date(2026,10,21))
    def test_empty_or_stale_samples_cannot_claim_no_history(self):
        self.state['tasks'].pop(self.sample);self.persist()
        with self.assertRaisesRegex(ValueError,'empty-use-full-query'):self.build()
        self.assertFalse(self.out.exists())
    def test_stale_window_and_changed_evidence_reject(self):
        p=self.build()
        with self.assertRaisesRegex(ValueError,'window-stale'):h.validate(self.root,self.state,self.target,p,as_of=date(2026,10,22))
        Path(p['items'][0]['result']['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'hash-mismatch'):h.validate(self.root,self.state,self.target,p,as_of=date(2026,10,21))
    def test_current_company_identity_and_original_result_must_match(self):
        self.state['identity']['manager']='其他经理';self.persist()
        with self.assertRaisesRegex(ValueError,'identity-mismatch'):self.build()
    def test_zero_or_outside_week_does_not_create_empty_evidence(self):
        r=self.state['tasks'][self.sample]['result'];original={k:v for k,v in r.items() if k!='evidence'};original['original_complaint']['投诉时间']='2026-10-13 12:00:00';ref=self.pin(original);self.state['tasks'][self.sample]['result']={**original,'evidence':ref};self.persist()
        with self.assertRaisesRegex(ValueError,'empty-use-full-query'):self.build()
    def test_default_v2_thirty_day_window_includes_older_reference(self):
        r=self.state['tasks'][self.sample]['result'];old={k:v for k,v in r.items() if k!='evidence'};old['original_complaint']['投诉时间']='2026-10-01 12:00:00';self.state['tasks'][self.sample]['result']={**old,'evidence':self.pin(old)};self.persist()
        p=h.build(self.root,self.target,self.out,at=self.at);self.assertEqual(p['kind'],'recent-other-result-samples-v2');self.assertEqual(p['window_days'],30);self.assertEqual(p['start'],'2026-09-21');self.assertEqual(len(p['items']),1)
        with self.assertRaisesRegex(ValueError,'empty-use-full-query'):h.build(self.root,self.target,self.root/'seven.json',at=self.at,window_days=7)
    def test_v1_original_seven_day_bytes_remain_valid_and_never_overwritten(self):
        p=self.build();p['kind']='recent-other-result-samples-v1';p.pop('window_days');self.out.write_text(json.dumps(p,ensure_ascii=False));raw=self.out.read_bytes()
        self.assertEqual(h.window_days(p),7);h.validate(self.root,self.state,self.target,p,as_of=self.at.date());self.assertEqual(self.out.read_bytes(),raw)
        with self.assertRaisesRegex(ValueError,'output-conflict'):h.build(self.root,self.target,self.out,at=self.at)
        self.assertEqual(self.out.read_bytes(),raw)
    def test_window_schema_is_explicit_and_cannot_reinterpret_legacy(self):
        p=self.build()
        for kind,days in [('recent-other-result-samples-v1',30),('recent-other-result-samples-v2',None),('recent-other-result-samples-v2',14),('recent-other-result-samples-v3',30)]:
            q=copy.deepcopy(p);q['kind']=kind
            if days is None:q.pop('window_days',None)
            else:q['window_days']=days
            with self.assertRaises(ValueError):h.validate(self.root,self.state,self.target,q,as_of=self.at.date())
    def test_thirty_day_lower_boundary_is_inclusive_and_upper_exclusive(self):
        original=copy.deepcopy(self.state['tasks'][self.sample]['result'])
        for day,accepted in [('2026-09-21',True),('2026-09-20',False),('2026-10-21',False)]:
            old={k:v for k,v in copy.deepcopy(original).items() if k!='evidence'};old['original_complaint']['投诉时间']=day+' 10:00:00';self.state['tasks'][self.sample]['result']={**old,'evidence':self.pin(old)};self.persist();out=self.root/(day+'.json')
            if accepted:self.assertEqual(len(h.build(self.root,self.target,out,at=self.at)['items']),1)
            else:
                with self.assertRaisesRegex(ValueError,'empty-use-full-query'):h.build(self.root,self.target,out,at=self.at)
                self.assertFalse(out.exists())
    def test_attach_v2_records_explicit_window_and_v1_keeps_legacy_fields(self):
        import workflow as w
        from unittest.mock import patch
        p=h.build(self.root,self.target,self.out,at=self.at)
        with patch.object(w,'save',side_effect=lambda root,state,event:state),patch.object(w,'shanghai_today',return_value=self.at.date()):
            w.attach_history(self.root,self.state,self.target,self.out);entry=self.state['tasks'][self.target]['history'];self.assertEqual(entry['schema'],p['kind']);self.assertEqual(entry['window_days'],30)
            legacy=self.root/'legacy.json';p['kind']='recent-other-result-samples-v1';p.pop('window_days');p['start']='2026-10-14';legacy.write_text(json.dumps(p));w.attach_history(self.root,self.state,self.target,legacy);entry=self.state['tasks'][self.target]['history'];self.assertNotIn('window_days',entry);self.assertNotIn('schema',entry)
if __name__=='__main__':unittest.main()
