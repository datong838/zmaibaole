"""Pure local journal fixtures. No business execution, UI or real ledger writes."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import director as d
import test_director as base

class SemanticProgressTests(base.DirectorTest):
    # Reuse temporary resources, not inherited tests, below through load_tests.
    def heartbeat(self,s,key,minute,path=None):
        start=datetime.fromisoformat(s['dispatched_at'])
        d.heartbeat(s,key,path or self.journal,now=start+timedelta(minutes=minute))
    def mutate(self,**changes):
        value=d.read(self.journal);value.update(changes);d.atomic(self.journal,value);return value
    def governance_manifest(self,ids):
        job={'company':'explicit-fixture-only','groupid':'123','start':'2026-10-16','end_exclusive':'2026-10-21'};fingerprint=hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        refs={}
        for key,value in [('job',job),('query',{'fingerprint':fingerprint,'tab_id':7,'rows':[{'notice_id':i} for i in ids]})]:
            path=self.root/(key+'.json');d.atomic(path,value);refs[key]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        return {'kind':'governance-detail-inspection-manifest-v1','inputs':refs},fingerprint
    def test_pending_download_changes_only_liveness_not_progress(self):
        s=self.state();key=self.dispatch(s);start=s['last_progress_at'];self.heartbeat(s,key,0)
        for minute in range(1,7):
            self.mutate(updated_at=str(minute),waiting_for='download-complete',download_reconciliation={'at':str(minute),'readonly':True},last_tree={'sha256':str(minute)})
            self.heartbeat(s,key,minute)
        self.assertEqual(s['last_progress_at'],start)
        out=d.inspect(s,now=datetime.fromisoformat(s['last_heartbeat']));self.assertEqual(out['reason'],'journal-no-progress');self.assertEqual(out['idle_seconds'],0)
    def test_same_phase_navigation_observations_and_phase_cycles_never_progress(self):
        s=self.state();s['index']=1;key=self.dispatch(s)
        value={'version':1,'fingerprint':'n'*64,'tab_id':7,'phase':'account','calls':[],'profile_accepted':False};d.atomic(self.journal,value);self.heartbeat(s,key,0);initial=s['last_progress_at']
        for minute in range(1,7):
            value.update(phase='account' if minute%2 else 'observeNegative',read_sequence=minute,readonly_checks=minute,observations=[{'at':str(minute)}],last_tree={'path':'readonly-'+str(minute)})
            d.atomic(self.journal,value);self.heartbeat(s,key,minute)
        self.assertEqual(s['last_progress_at'],initial);self.assertEqual(d.inspect(s,now=datetime.fromisoformat(s['last_heartbeat']))['reason'],'journal-no-progress')
    def test_new_completed_stage_once_then_uuid_time_churn_cannot_keep_alive(self):
        s=self.state();key=self.dispatch(s);self.heartbeat(s,key,0)
        self.mutate(checkpoints=[{'stage':'navigation','event_id':'first','at':'ignored','groupid':'123'}]);self.heartbeat(s,key,4);at=s['last_progress_at']
        self.mutate(checkpoints=[{'stage':'navigation','event_id':'second','at':'later','groupid':'123'}]);self.heartbeat(s,key,8)
        self.assertEqual(s['last_progress_at'],at);self.assertEqual(d.inspect(s,now=datetime.fromisoformat(s['dispatched_at'])+timedelta(minutes=10))['reason'],'journal-no-progress')
    def test_rewriting_completed_stage_or_workorder_or_removing_stage_is_attention(self):
        for change in ({'checkpoints':[]},{'checkpoints':[{'stage':'navigation','groupid':'999'}]},{'work_order_id':'different-job'}):
            s=self.state();key=self.dispatch(s);self.mutate(checkpoints=[{'stage':'navigation','groupid':'123'}]);self.heartbeat(s,key,0);self.mutate(**change);self.heartbeat(s,key,1)
            self.assertEqual(s['phase'],'attention');self.assertEqual(s['attention_reason'],'semantic-progress-unverified');self.assertEqual(s['attempt'],0)
            self.mutate(work_order_id='fixed-fixture-job',checkpoints=[])
    def test_switching_to_old_completed_logs_or_back_never_resets_timer(self):
        s=self.state();key=self.dispatch(s);self.heartbeat(s,key,0);initial=s['last_progress_at']
        for minute in range(1,7):
            other=self.root/(str(minute)+'.json');value=d.read(self.journal);value.update(work_order_id='historical-'+str(minute),checkpoints=[{'stage':'navigation','groupid':'123'}]);d.atomic(other,value);self.heartbeat(s,key,minute,other)
        self.assertEqual(s['last_progress_at'],initial);self.assertEqual(d.inspect(s,now=datetime.fromisoformat(s['last_heartbeat']))['reason'],'journal-no-progress')
    def test_unknown_schema_intent_error_or_explicit_hold_goes_attention_without_replay(self):
        for change in ({'calls':[{'state':'unknown'}]},{'last_error':{'message':'blocked'}},{'hold':True},{'totally':'unsupported'}):
            s=self.state();key=self.dispatch(s)
            if 'totally' in change:d.atomic(self.journal,change)
            else:self.mutate(**change)
            self.heartbeat(s,key,0);self.assertEqual(s['phase'],'attention');self.assertIn('semantic-',s['semantic_progress_error']);self.assertEqual(s['attempt'],0)
            d.atomic(self.journal,{'backend':'local-dom-bridge','work_order_id':'fixed-fixture-job','fingerprint':'f'*64,'state':'running','phase':'downloadResult','calls':[],'checkpoints':[]})
    def test_new_intents_confirmed_calls_and_arbitrary_worker_tokens_are_not_progress(self):
        s=self.state();key=self.dispatch(s);self.heartbeat(s,key,0);initial=s['last_progress_at']
        for minute in range(1,7):
            value=d.read(self.journal);value.update(progress_token=str(minute),actual_progress=str(minute),checkpoints=[{'stage':'export-intent','event_id':str(minute),'at':str(minute)}]);value['calls'].append({'state':'confirmed','command':{'op':'click','selector':str(minute)}});d.atomic(self.journal,value);self.heartbeat(s,key,minute)
        self.assertEqual(s['last_progress_at'],initial);self.assertEqual(d.inspect(s,now=datetime.fromisoformat(s['last_heartbeat']))['reason'],'journal-no-progress')
    def test_download_complete_requires_actual_local_file_hash(self):
        s=self.state();key=self.dispatch(s);self.heartbeat(s,key,0);file=self.root/'download.xlsx';file.write_bytes(b'explicit-fixture-only')
        self.mutate(checkpoints=[{'stage':'download-complete','path':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'ticket':'original'}]);self.heartbeat(s,key,2);self.assertEqual(s['phase'],'running');self.assertNotEqual(s['last_progress_at'],s['dispatched_at'])
        file.write_bytes(b'changed');self.heartbeat(s,key,3);self.assertEqual(s['phase'],'attention');self.assertIn('evidence-changed',s['semantic_progress_error'])
    def test_governance_cursor_requires_closed_refs_and_cannot_decrease(self):
        s=self.state();s['index']=2;key=self.dispatch(s)
        proof=self.root/'normal.json';d.atomic(proof,{'source':'actual-shaped-fixture'});ref={'path':str(proof),'sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}
        manifest,fp=self.governance_manifest(['notice1']);value={'fingerprint':fp,'manifest':manifest,'tab_id':7,'phase':'normal','calls':[],'cursor':0,'details':[],'observations':[]};d.atomic(self.journal,value);self.heartbeat(s,key,0)
        value['details']=[{'state':'complete','notice_id':'notice1','normal_before':ref,'normal_after':ref,'detail_observation':ref,'facts':{'advice':'公开建议'}}];value['cursor']=1;d.atomic(self.journal,value);self.heartbeat(s,key,3);self.assertEqual(s['phase'],'running');self.assertNotEqual(s['last_progress_at'],s['dispatched_at'])
        value.update(cursor=0,details=[]);d.atomic(self.journal,value);self.heartbeat(s,key,4);self.assertEqual(s['phase'],'attention')
    def test_attention_heartbeat_is_readonly_liveness_and_cannot_release_hold(self):
        s=self.state();key=self.dispatch(s);self.mutate(error='blocked');self.heartbeat(s,key,0);self.assertEqual(s['phase'],'attention');initial=s['last_progress_at']
        self.mutate(error=None,checkpoints=[{'stage':'navigation','groupid':'123'}]);self.heartbeat(s,key,8)
        self.assertEqual(s['phase'],'attention');self.assertEqual(s['last_progress_at'],initial);self.assertEqual(d.plan(s)['action'],'inspect-original-run')
    def test_new_sender_ui_receipt_progress_and_unknown_terminal(self):
        s=self.state();key=self.dispatch(s);job={'version':'1.0.0','key':'original-key','kind':'group','scope':'test','target':d.TARGET,'type':'text','text':'fixture'}
        value={'job':job,'fingerprint':hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'status':'running','phase':'verify','events':[]};d.atomic(self.journal,value);self.heartbeat(s,key,0)
        value.update(status='complete',phase='done',sent=True,ui_confirmed=True,completed_at='fixture',events=[{'stage':'ui-confirmed','recipient':d.TARGET}]);d.atomic(self.journal,value);self.heartbeat(s,key,2);self.assertEqual(s['phase'],'running');self.assertEqual(len(s['events'][-1]['completed']),1)
        value.update(status='unknown',phase='verify-sent',checks=5,events=[]);d.atomic(self.journal,value);self.heartbeat(s,key,3);self.assertEqual(s['phase'],'attention')
    def test_query_page_progress_is_reparsed_from_original_public_dom(self):
        root=Path(__file__).resolve().parents[3];path=root/'work/live-acceptance/violations/2026-10-21/preparation/01_烟台一成教育文化咨询有限公司/records-range-query-v9.json'
        if not path.exists():self.skipTest('actual immutable query fixture unavailable')
        query=d.read(path);pages=copy.deepcopy(query['pages'])
        value={'fingerprint':query['fingerprint'],'tab_id':query['tab_id'],'phase':'page-collected','calls':[],'pages':pages}
        result=d.progress.extract(value,'violation_operator');self.assertEqual(len(result['tokens']),len(pages))
        value['pages'][0]['rows'][0]['notice_id']='invented'
        with self.assertRaisesRegex(ValueError,'not-proved-by-dom'):d.progress.extract(value,'violation_operator')
    def test_detail_cursor_cannot_extend_beyond_fixed_query_even_with_refs(self):
        manifest,fp=self.governance_manifest([])
        value={'fingerprint':fp,'manifest':manifest,'tab_id':7,'phase':'normal','calls':[],'cursor':1,'details':[{'state':'complete','notice_id':'invented'}]}
        with self.assertRaisesRegex(ValueError,'outside-workorder'):d.progress.extract(value,'violation_operator')
    def test_missing_or_changed_evidence_cannot_claim_completed_cursor(self):
        s=self.state();s['index']=2;key=self.dispatch(s)
        manifest,fp=self.governance_manifest(['n1']);value={'fingerprint':fp,'manifest':manifest,'tab_id':7,'phase':'normal','calls':[],'cursor':1,'details':[{'state':'complete','notice_id':'n1','normal_before':{'path':str(self.root/'missing.json'),'sha256':'0'*64}}]};d.atomic(self.journal,value);self.heartbeat(s,key,0);self.assertEqual(s['phase'],'attention');self.assertIn('evidence-changed',s['semantic_progress_error'])

def load_tests(loader,tests,pattern):
    names=[n for n in SemanticProgressTests.__dict__ if n.startswith('test_')]
    return unittest.TestSuite(SemanticProgressTests(n) for n in names)
if __name__=='__main__':unittest.main()
