import copy
import json
from pathlib import Path
import unittest
from test_workflow import Fixture, IDENTITY
from ds_common import FlowError
from flow import init_run, checkpoint, identity_fields, upgrade_identity_scope, read_identity_registry


class MerchantScopeTest(Fixture):
    def state(self):
        s=init_run(self.dates,self.out,self.map)
        return s,s['companies'][0],s['companies'][1]
    def establish(self,s,a,b):
        self.first=copy.deepcopy(IDENTITY)
        self.second={**IDENTITY,'account_id':'another-merchant','manager':'另一客户经理'}
        checkpoint(s,a,{'stage':'identity','identity_scope':'entry','groupid':a['groupid'],'identity':self.first})
        checkpoint(s,a,{'stage':'switch','groupid':a['groupid'],'identity':self.first})
        checkpoint(s,b,{'stage':'identity','identity_scope':'entry','groupid':a['groupid'],'identity':self.first})
        checkpoint(s,b,{'stage':'identity','identity_scope':'company','groupid':b['groupid'],'identity':self.second})
        checkpoint(s,b,{'stage':'switch','groupid':b['groupid'],'identity':self.second})
    def test_different_merchant_id_and_manager_same_provider_are_separate(self):
        s,a,b=self.state();self.establish(s,a,b)
        self.assertEqual(s['identity_baseline'],self.first)
        self.assertEqual(identity_fields(s,b)['identity_baseline'],self.second)
        self.assertEqual(s['company_identities'][a['groupid']],self.first)
        registry=read_identity_registry(s['identity_registry'])
        self.assertEqual(registry['company_identities'][b['groupid']],self.second)
    def test_known_merchant_change_or_provider_change_rejected(self):
        s,a,b=self.state();self.establish(s,a,b)
        for changed in ({**self.second,'manager':'changed'},{**self.second,'provider':'another-provider'}):
            with self.assertRaisesRegex(FlowError,'account-changed'):
                checkpoint(s,b,{'stage':'identity','identity_scope':'company','groupid':b['groupid'],'identity':changed})
    def test_unknown_entry_scope_cannot_be_used_as_target(self):
        s,a,b=self.state()
        with self.assertRaisesRegex(FlowError,'entry-identity-scope'):
            checkpoint(s,b,{'stage':'identity','identity_scope':'entry','groupid':'999','identity':IDENTITY})
        self.assertEqual(s['company_identities'],{})
    def test_new_batch_inherits_registry_and_does_not_bootstrap_again(self):
        s,a,b=self.state();self.establish(s,a,b)
        second=init_run(self.dates,self.root/'another-run',self.map)
        self.assertFalse(second['identity_bootstrap'])
        self.assertEqual(second['provider_baseline'],IDENTITY['provider'])
        self.assertEqual(second['company_identities'],s['company_identities'])
    def test_corrupt_registry_never_silently_reboots_identity(self):
        s,a,b=self.state();self.establish(s,a,b)
        Path(s['identity_registry']).write_text('{"version":2}')
        with self.assertRaisesRegex(FlowError,'registry-invalid'):
            init_run(self.dates,self.root/'another-run',self.map)
    def test_explicit_legacy_upgrade_keeps_first_identity_and_archives(self):
        s,a,b=self.state()
        s.pop('identity_contract');s.pop('company_identities');s.pop('provider_baseline')
        checkpoint(s,a,{'stage':'identity','identity':IDENTITY})
        checkpoint(s,a,{'stage':'switch','groupid':a['groupid'],'identity':IDENTITY})
        result=upgrade_identity_scope(s)
        self.assertEqual(result['identity_contract'],'merchant-v2')
        self.assertEqual(s['identity_baseline'],IDENTITY)
        self.assertTrue(Path(s['identity_contract_upgrade']['previous_state']).is_file())
        self.assertEqual(s['company_identities'],{a['groupid']:IDENTITY})


if __name__=='__main__':unittest.main()
