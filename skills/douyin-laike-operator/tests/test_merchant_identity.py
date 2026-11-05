"""Merchant-v2 contract mocks and offline parsing; never touches real journals/UI."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_bridge_workflow import bw,Mock,leaf
ENTRY={'provider':'服务商123456789','account_id':'987654321','manager':'原经理'}
TARGET={**ENTRY,'account_id':'111222333','manager':'新经理'}
def card(value,tail='退出登录'):
    return {'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'children':[leaf(value['provider']+' 账户ID '+value['account_id']+' 我的客户经理 '+value['manager']+' '+tail,attributes={'class':'UserCard-index-module__outer--fixture'})]}}
class MerchantIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job={'action':'acquire','work_order_id':'fixture','company':'fixture-target','groupid':'123','date_range':{'start':'2026-10-16','end':'2026-10-19'},'source_dir':str(self.root/'sources'),'workflow_path':str(self.root/'journal.json'),'identity_contract':'merchant-v2','provider_baseline':ENTRY['provider'],'identity_baseline':None,'known_company_identities':{'456':ENTRY}}
        self.bridge=Mock('456');self.bridge.t=card(ENTRY)
    def w(self):return bw.Workflow(self.job,5,self.bridge)
    def entry(self):
        w=self.w();w.tick();self.assertEqual(w.s['entry_identity'],ENTRY);self.assertNotIn('identity',w.s);return w
    def target(self,w=None):
        w=w or self.entry();w.s['phase']='identityAfterSwitch';w.save();self.bridge.group='123';self.bridge.t=card(TARGET);w.tick();return w
    def legacy(self,**changes):
        legacy_job={k:v for k,v in self.job.items() if k not in ('identity_contract','provider_baseline','known_company_identities')}
        w=bw.Workflow(legacy_job,5,self.bridge);w.s.update(initial_groupid='456',phase='identityAfterSwitch',identity=ENTRY,checkpoints=[{'stage':'identity','identity':ENTRY}],calls=[{'key':'5:confirmSwitch','phase':'confirmSwitch','state':'confirmed','command':{'op':'click','kind':'company-confirm'},'result':{'clicked':True}}]);w.s.update(changes);w.save()
        return Path(self.job['workflow_path']).read_bytes()
    def request_upgrade(self):self.job['identity_contract_upgrade']={'kind':'merchant-v2','id':'fixture-contract-recovery'}
    def test_manager_parse_stops_at_both_visible_actions(self):
        for tail in ('退出登录','切换公司','退出登录 切换公司'):
            self.assertEqual(bw.identity(card(TARGET,tail)),TARGET)
    def test_same_provider_new_merchant_binds_only_after_target_context(self):
        w=self.entry();self.assertEqual(w.s['checkpoints'][-1]['identity_scope'],'entry')
        w.s['phase']='identityAfterSwitch';w.save();self.bridge.t=card(TARGET)
        with self.assertRaisesRegex(ValueError,'source-company-mismatch'):w.tick()
        self.assertNotIn('identity',w.s)
        self.bridge.group='123';w.tick()
        self.assertEqual(w.s['identity'],TARGET);self.assertEqual(w.s['identity_before'],TARGET)
        identity_cp=[c for c in w.s['checkpoints'] if c['stage']=='identity'][-1]
        self.assertEqual(identity_cp['identity_scope'],'company');self.assertEqual(identity_cp['groupid'],'123')
        self.assertEqual([c['stage'] for c in w.s['checkpoints']][-2:],['identity','switch'])
    def test_unknown_entry_or_wrong_known_identity_refused_without_hover(self):
        for known in ({},{'456':TARGET}):
            with self.subTest(known=known):
                self.job['known_company_identities']=known
                with self.assertRaises(ValueError):self.w().tick()
                self.assertFalse(self.bridge.mutations())
    def test_known_target_full_identity_and_provider_changes_refused(self):
        self.job['identity_baseline']=TARGET;self.job['known_company_identities']['123']=TARGET;w=self.entry();w.s['phase']='identityAfterSwitch';w.save();self.bridge.group='123'
        for value in ({**TARGET,'manager':'另一个经理'},{**TARGET,'account_id':'222333444'},{**TARGET,'provider':'服务商999999999'}):
            self.bridge.t=card(value)
            with self.subTest(value=value),self.assertRaises(ValueError):w.tick()
            self.assertNotIn('identity',w.s)
        self.assertFalse(self.bridge.mutations())
    def test_first_target_provider_change_and_later_pinned_changes_rejected(self):
        w=self.entry();w.s['phase']='identityAfterSwitch';w.save();self.bridge.group='123';self.bridge.t=card({**TARGET,'provider':'服务商999999999'})
        with self.assertRaisesRegex(ValueError,'provider-changed'):w.tick()
        self.bridge.t=card(TARGET);w.tick();self.bridge.t=card({**TARGET,'manager':'changed'})
        with self.assertRaisesRegex(ValueError,'account-changed'):w.tick()
    def test_unknown_scope_or_early_target_establishment_rejected(self):
        w=self.entry()
        for gid,scope in [('unknown','company'),('123','unverified'),('123','company')]:
            with self.subTest(gid=gid,scope=scope),self.assertRaises(ValueError):w.set_identity(TARGET,gid,scope)
    def test_upgrade_archives_exact_old_bytes_preserves_company_calls(self):
        raw=self.legacy();self.request_upgrade();w=self.w();upgrade=w.s['identity_contract_upgrade']
        self.assertEqual(Path(upgrade['archive']).read_bytes(),raw);self.assertEqual(upgrade['sha256'],hashlib.sha256(raw).hexdigest())
        self.assertEqual(w.s['calls'][0]['command']['kind'],'company-confirm');self.assertEqual(w.s['checkpoints'][0]['identity_scope'],'entry');self.assertNotIn('identity',w.s)
        self.bridge.group='123';self.bridge.t=card(TARGET);w.tick();self.assertEqual(w.s['identity_before'],TARGET)
        self.assertEqual(self.w().s['identity'],TARGET)
    def test_upgrade_unknown_checkpoint_scope_rejected_without_rewrite(self):
        raw=self.legacy(checkpoints=[{'stage':'identity','identity':ENTRY,'identity_scope':'company','groupid':'123'}]);self.request_upgrade()
        with self.assertRaisesRegex(ValueError,'checkpoint-scope'):self.w()
        self.assertEqual(Path(self.job['workflow_path']).read_bytes(),raw)
    def test_upgrade_requires_explicit_request_and_same_scope(self):
        raw=self.legacy()
        with self.assertRaisesRegex(ValueError,'explicit-identity-contract'):self.w()
        self.assertEqual(Path(self.job['workflow_path']).read_bytes(),raw)
        self.request_upgrade();self.job['date_range']['start']='2026-10-15'
        with self.assertRaisesRegex(ValueError,'work-order-conflict'):self.w()
    def test_upgrade_refuses_processed_unknown_or_completed_journals(self):
        mutations=[{'exportPending':True},{'downloadPending':True},{'attempts':1},{'state':'complete'}, {'calls':[{'state':'unknown','command':{'op':'click','kind':'navigation'}}]}, {'checkpoints':[{'stage':'export-intent'}]}, {'calls':[{'state':'confirmed','command':{'op':'click','kind':'export'}}]}]
        for changes in mutations:
            with self.subTest(changes=changes):
                Path(self.job['workflow_path']).unlink(missing_ok=True)
                raw=self.legacy(**copy.deepcopy(changes));self.request_upgrade()
                with self.assertRaisesRegex(ValueError,'side-effect-or-unknown'):self.w()
                self.assertEqual(Path(self.job['workflow_path']).read_bytes(),raw)
    def test_already_target_entry_known_identity_is_pinned_and_no_cross_merchant_reuse(self):
        self.bridge.group='123';self.bridge.t=card(TARGET);self.job['known_company_identities']['123']=TARGET
        w=self.w();w.tick();self.assertEqual(w.s['entry_identity'],TARGET);self.assertEqual(w.s['identity_before'],TARGET)
        self.job['identity_baseline']=ENTRY
        with self.assertRaisesRegex(ValueError,'account-changed'):self.w().tick()
    def bootstrap_job(self):
        self.job.update(identity_bootstrap=True,provider_baseline=None,known_company_identities={},allowed_groupids=['123','456'])
    def test_explicit_empty_bootstrap_pins_entry_provider_once_then_target_full(self):
        self.bootstrap_job();w=self.entry();self.assertEqual(w.s['provider_baseline'],ENTRY['provider'])
        self.assertEqual(len([c for c in w.s['checkpoints'] if c['stage']=='provider-bootstrap']),1)
        w=self.w();self.assertEqual(w.s['provider_baseline'],ENTRY['provider'])
        w=self.target(w);self.assertEqual(w.s['identity_before'],TARGET)
        self.assertEqual(w.s['provider_baseline'],ENTRY['provider'])
        self.assertEqual(len([c for c in w.s['checkpoints'] if c['stage']=='provider-bootstrap']),1)
    def test_bootstrap_none_job_baseline_never_repins_changed_provider(self):
        self.bootstrap_job();w=self.entry();w.s.update(phase='readAccount');w.save()
        self.bridge.t=card({**ENTRY,'provider':'服务商999999999'})
        with self.assertRaises(ValueError):self.w().tick()
        self.assertEqual(self.w().s['provider_baseline'],ENTRY['provider'])
        w=self.w();w.s['phase']='identityAfterSwitch';w.save();self.bridge.group='123';self.bridge.t=card({**TARGET,'provider':'服务商999999999'})
        with self.assertRaisesRegex(ValueError,'provider-changed'):self.w().tick()
    def test_bootstrap_requires_empty_config_explicit_flag_and_allowed_entry(self):
        original=copy.deepcopy(self.job)
        variants=[{'identity_bootstrap':False},{'known_company_identities':{'456':ENTRY}}, {'provider_baseline':ENTRY['provider']}, {'allowed_groupids':[]}, {'allowed_groupids':['123']}, {'identity_baseline':TARGET}]
        for change in variants:
            with self.subTest(change=change):
                Path(self.job['workflow_path']).unlink(missing_ok=True)
                self.job=copy.deepcopy(original);self.bootstrap_job();self.job.update(change)
                with self.assertRaises(ValueError):self.w().tick()
        self.assertFalse(self.bridge.mutations())
    def test_bootstrap_cannot_replace_old_ledger_or_change_allowed_scope(self):
        raw=self.legacy();self.bootstrap_job()
        with self.assertRaisesRegex(ValueError,'fresh-empty'):self.w()
        self.assertEqual(Path(self.job['workflow_path']).read_bytes(),raw)
        Path(self.job['workflow_path']).unlink();self.entry();self.job['allowed_groupids']=['123']
        with self.assertRaisesRegex(ValueError,'origin-conflict'):self.w()
    def test_known_provider_current_target_unknown_full_identity_pins_once(self):
        self.job['known_company_identities']={};self.bridge.group='123';self.bridge.t=card(TARGET)
        w=self.w();w.tick();self.assertEqual(w.s['identity_before'],TARGET)
        self.bridge.t=card({**TARGET,'manager':'changed'});w.s['phase']='readAccount';w.save()
        with self.assertRaisesRegex(ValueError,'account-changed'):self.w().tick()
    def test_verified_registry_refresh_after_bootstrap_keeps_pinned_scope(self):
        self.bootstrap_job();w=self.target();self.job.update(provider_baseline=ENTRY['provider'],known_company_identities={'456':ENTRY,'123':TARGET},identity_baseline=TARGET)
        self.assertEqual(self.w().s['identity'],TARGET)
        self.job['provider_baseline']='服务商999999999'
        with self.assertRaisesRegex(ValueError,'provider-changed'):self.w()
if __name__=='__main__':unittest.main()
