import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
S=Path(__file__).resolve().parents[1]/'scripts/native_control_maintenance_order.py'
spec=importlib.util.spec_from_file_location('native_maintenance_descriptor',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();source=self.root/'skills/bridge.py';source.parent.mkdir();source.write_text('public reviewed script')
        self.release=self.write('release.json',{'status':'published-files-maintenance-required-not-installed','published':{'skills/bridge.py':m.ref(source)['sha256']}})
        self.ticket=self.write('ticket.json',{'kind':'independent-python-server-and-extension-maintenance-ticket-v1','ticket_id':'original-maintenance-123','target_actor':'operator','readonly_verification_command':{'op':'readonly-scope','tabId':7,'windowId':8}})
        self.g={'kind':'supervisor-existing-browser-maintenance-grant-v1','ticket':self.ticket,'authorized':True,'maintenance_only':True,'one_original_merchant_activation_only':True,'execute_business':False,'test_wecom_send':False,'complaint_submit':False,'chrome_restart':False,'debugging':False,'actor':'operator','unknown_input_outcome_no_replay':True,'formal_release':self.release,'published_files':m.read(self.release)['published']};self.grant=self.write('grant.json',self.g)
    def write(self,name,value):
        p=self.root/name;p.write_text(json.dumps(value));return m.ref(p)
    def run_order(self,grant=None):return m.prepare(self.ticket,grant or self.grant,root=self.root)
    def test_exact_original_refs_and_merchant_in_descriptor(self):
        result=self.run_order();v=m.read(result['order']);self.assertEqual(v['derived_from'],{'maintenance_ticket':self.ticket,'root_grant':self.grant});self.assertEqual(v['ticket_id'],'original-maintenance-123');self.assertIn('return originalmerchant7',v['allowed']);self.assertFalse(result['ui_used']);self.assertFalse(result['new_authorization_invented'])
    def test_repeat_preserves_original_bytes_and_timestamp(self):
        first=self.run_order();before=Path(first['order']['path']).read_bytes();self.assertEqual(first,self.run_order());self.assertEqual(before,Path(first['order']['path']).read_bytes())
    def test_changed_pinned_grant_rejected(self):
        Path(self.grant['path']).write_text('{}')
        with self.assertRaisesRegex(ValueError,'pinned-reference-changed'):self.run_order()
    def test_wrong_original_ticket_or_actor_rejected(self):
        for change in ({'ticket':self.release},{'actor':'other'}):
            g={**self.g,**change}
            with self.subTest(change=change),self.assertRaises(ValueError):self.run_order(self.write('bad.json',g))
    def test_business_debug_restart_and_unknown_replay_rejected(self):
        for change in ({'execute_business':True},{'debugging':True},{'chrome_restart':True},{'unknown_input_outcome_no_replay':False}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.run_order(self.write('bad.json',{**self.g,**change}))
    def test_changed_published_source_rejected(self):
        (self.root/'skills/bridge.py').write_text('changed')
        with self.assertRaisesRegex(ValueError,'published-source-changed'):self.run_order()
    def test_existing_conflicting_descriptor_never_overwritten(self):
        result=self.run_order();p=Path(result['order']['path']);old=p.read_bytes();v=json.loads(old);v['ticket_id']='different';p.write_text(json.dumps(v));bad=p.read_bytes()
        with self.assertRaisesRegex(ValueError,'original-native-maintenance-order-conflict'):self.run_order()
        self.assertEqual(p.read_bytes(),bad)
    def test_boolean_scope_and_symlink_inputs_rejected(self):
        v=m.read(self.ticket);v['readonly_verification_command']['tabId']=True;self.ticket=self.write('ticket.json',v);self.grant=self.write('grant.json',{**self.g,'ticket':self.ticket})
        with self.assertRaisesRegex(ValueError,'original-merchant-scope-required'):self.run_order()
        link=self.root/'link.json';link.symlink_to(self.grant['path'])
        with self.assertRaisesRegex(ValueError,'canonical-reference-required'):m.ref(link)
if __name__=='__main__':unittest.main()
