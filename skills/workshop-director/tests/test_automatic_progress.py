"""Monitor adapter only: fake pure verifier, no business execution or UI."""
import hashlib,json,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import test_semantic_progress as base
import director as d

class AutomaticProgressTests(base.SemanticProgressTests):
    def setup_owned(self):
        s=self.state();s['index']=2;key=self.dispatch(s)
        m,fp=self.governance_manifest(['A','B'])
        value={'fingerprint':fp,'manifest':m,'tab_id':7,'phase':'auto-rates-center-pending','calls':[],'cursor':0,'details':[], 'current':{'notice_id':'A'},'hold':True,'waiting_for':'automatic-owned-list-restore','automatic_stop_loss_owner':{'binding_sha256':'a'*64,'program_phase':'auto-rates-center-pending'}}
        d.atomic(self.journal,value);return s,key,value
    def proof(self,notice,steps,retired=False):
        return {'schema':'verified-automatic-stop-loss-progress-v1','binding_sha256':hashlib.sha256(notice.encode()).hexdigest(),'notice_id':notice,'completed_steps':steps,'progress_tokens':[hashlib.sha256((notice+step).encode()).hexdigest() for step in steps],'ui_used':False,('retired_after_verified_detail_completion' if retired else 'owner_verified'):True}
    def test_verified_owned_hold_and_pending_observation_do_not_refresh_timer(self):
        s,key,v=self.setup_owned();api=Mock();api.verify_owned_progress.return_value=self.proof('A',['stage'])
        with patch.object(d.progress,'automatic_verifier',return_value=api):
            self.heartbeat(s,key,0);initial=s['last_progress_at'];self.assertEqual(s['phase'],'running')
            for minute in range(1,7):
                v.update(read_sequence=minute,updated_at=str(minute));d.atomic(self.journal,v);self.heartbeat(s,key,minute)
            self.assertEqual(s['last_progress_at'],initial);self.assertEqual(d.inspect(s,now=__import__('datetime').datetime.fromisoformat(s['last_heartbeat']))['reason'],'journal-no-progress')
    def test_real_verified_new_step_once_counts_progress(self):
        s,key,v=self.setup_owned();api=Mock();api.verify_owned_progress.return_value=self.proof('A',['stage'])
        with patch.object(d.progress,'automatic_verifier',return_value=api):
            self.heartbeat(s,key,0);api.verify_owned_progress.return_value=self.proof('A',['stage','rates_sidebar_once']);self.heartbeat(s,key,2)
            self.assertEqual(s['phase'],'running');self.assertNotEqual(s['last_progress_at'],s['dispatched_at']);self.assertEqual(s['events'][-1]['completed'],['automatic:A:rates_sidebar_once'])
    def test_forged_owner_or_unknown_error_and_manual_hold_are_attention(self):
        for change in ({},{'calls':[{'state':'unknown'}]},{'last_error':'unknown'},{'settling_exhausted':True}):
            s,key,v=self.setup_owned();v.update(change);d.atomic(self.journal,v)
            api=Mock();api.verify_owned_progress.side_effect=ValueError('forged-or-unverified-owner')
            with patch.object(d.progress,'automatic_verifier',return_value=api):self.heartbeat(s,key,0)
            self.assertEqual(s['phase'],'attention');self.assertEqual(s['attempt'],0)
        s,key,v=self.setup_owned();v.pop('automatic_stop_loss_owner');d.atomic(self.journal,v)
        with patch.object(d.progress,'automatic_verifier') as api:self.heartbeat(s,key,0);api.assert_not_called()
        self.assertEqual(s['phase'],'attention')
    def test_completion_and_next_notice_preserve_original_automatic_tokens(self):
        s,key,v=self.setup_owned();api=Mock();api.verify_owned_progress.return_value=self.proof('A',['stage'])
        with patch.object(d.progress,'automatic_verifier',return_value=api):
            self.heartbeat(s,key,0)
            evidence=self.root/'closed.json';d.atomic(evidence,{'actual-shaped-fixture':True});ref={'path':str(evidence),'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest()}
            v.update(cursor=1,details=[{'state':'complete','notice_id':'A','normal_before':ref,'normal_after':ref,'detail_observation':ref,'facts':{}}],phase='normal',current=None,hold=False);v.pop('automatic_stop_loss_owner')
            folder=self.journal.parent/'automatic-stop-loss'/hashlib.sha256(b'A').hexdigest();folder.mkdir(parents=True);d.atomic(folder/'state.json',{'canonical-placeholder-for-pure-verifier':True})
            api.verify_completed_progress.return_value=self.proof('A',['stage','rates_sidebar_once'],True);d.atomic(self.journal,v);self.heartbeat(s,key,2)
            self.assertEqual(s['phase'],'running');tokens=s['semantic_progress'][key][str(self.journal.resolve())]['tokens'];self.assertIn('automatic:A:stage',tokens);self.assertIn('detail:A',tokens)
            v.update(phase='auto-rates-center-pending',current={'notice_id':'B'},hold=True,automatic_stop_loss_owner={'binding_sha256':'b'*64,'program_phase':'auto-rates-center-pending'});api.verify_owned_progress.return_value=self.proof('B',['stage']);d.atomic(self.journal,v);self.heartbeat(s,key,3)
            self.assertEqual(s['phase'],'running');tokens=s['semantic_progress'][key][str(self.journal.resolve())]['tokens'];self.assertIn('automatic:A:stage',tokens);self.assertIn('automatic:B:stage',tokens)
            api.verify_completed_progress.side_effect=ValueError('closed-chain-changed');self.heartbeat(s,key,4);self.assertEqual(s['phase'],'attention')
    def test_owned_proof_needs_original_file_and_exact_verified_contract(self):
        s,key,v=self.setup_owned()
        with self.assertRaisesRegex(ValueError,'parent-required'):d.progress.extract(v,'violation_operator')
        api=Mock();proof=self.proof('A',['stage']);proof['owner_verified']=False;api.verify_owned_progress.return_value=proof
        with patch.object(d.progress,'automatic_verifier',return_value=api):self.heartbeat(s,key,0)
        self.assertEqual(s['phase'],'attention')

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(AutomaticProgressTests(n) for n in AutomaticProgressTests.__dict__ if n.startswith('test_'))
if __name__=='__main__':unittest.main()
