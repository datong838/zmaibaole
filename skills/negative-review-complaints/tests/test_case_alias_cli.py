"""Synthetic transport and lease fixtures. Not a real ve drawer or UI test."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'skills/negative-review-complaints/scripts'))
import case_alias_cli as cli
from test_case_alias import page,card,node
class CliTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.business=Path(self.t.name).resolve();self.root=self.business/'公司';self.root.mkdir();self.ledger=self.root/'state.json';self.ledger.write_text('{"company":"公司"}');self.lease=self.business/'director.json'
        self.s={'version':2,'index':1,'phase':'running','day':'2026-10-22','attempt':2,'dispatch_id':'2026-10-22:negative-review-complaints:2','tool_receipt':'synthetic-tool','dispatch_intent_at':'2026-10-22T00:00:00+00:00','dispatched_at':'2026-10-22T00:00:01+00:00','test_target':'测试群请忽略','production_enabled':False,'complaint_submission_enabled':False};self.lease.write_text(json.dumps(self.s));self.patches=[patch.object(cli,'LEASE',self.lease),patch.object(cli,'BUSINESS_ROOT',self.business),patch.object(cli.runner,'inputs',return_value={}),patch.object(cli.runner,'barriers')]
        for p in self.patches:p.start();self.addCleanup(p.stop)
        self.m={'kind':'unbound-case-inspection-manifest-v1','root':str(self.root),'review_key':'123:old','inputs':{'ledger':cli.c.ref(self.ledger)},'old_result':{},'old_drawer':{},'pending_drawers':{},'legacy_operations':[]}
        self.order={'kind':'unbound-complaint-case-read-order-v1','manifest':self.m,'actions':['complaint-read:open','complaint-read:close'],'never':['complaint','submit','capture','send','record_result','case_memory'],'person_identity_verified':False};self.op=self.root/'order.json';self.op.write_text(json.dumps(self.order));self.order_ref=cli.c.ref(self.op)
    def prepare(self):return cli.prepare(self.order_ref,cli.c.ref(self.lease))
    def test_prepare_is_pure_pins_order_and_archives_original_ledger_bytes(self):
        with patch.object(cli.bridge,'request',side_effect=AssertionError('no network')):
            q=self.prepare();m=cli.c.document(q);self.assertEqual(cli.identity(m,q),m);self.assertEqual(Path(m['inputs']['ledger']['path']).read_bytes(),self.ledger.read_bytes());self.assertEqual(m['original_ledger'],cli.c.ref(self.ledger));self.assertFalse((cli.folder(m)/'operation.json').exists())
    def test_copied_business_root_cannot_open_parallel_operation(self):
        self.m['root']=str(self.business/'copied-root');(self.business/'copied-root').mkdir();self.op.write_text(json.dumps({**self.order,'manifest':self.m}));self.order_ref=cli.c.ref(self.op)
        with self.assertRaisesRegex(ValueError,'business-root'):self.prepare()
    def test_repeat_prepare_returns_original_manifest_heartbeat_does_not_rekey(self):
        q=self.prepare();self.s['last_heartbeat']='later';self.lease.write_text(json.dumps(self.s));self.assertEqual(q,self.prepare())
    def test_changed_order_or_noncanonical_manifest_rejected(self):
        q=self.prepare();m=cli.c.document(q);p=self.root/'copy.json';p.write_bytes(Path(q['path']).read_bytes())
        with self.assertRaisesRegex(ValueError,'canonical-manifest'):cli.identity(m,cli.c.ref(p))
        self.order['never']=[];self.op.write_text(json.dumps(self.order))
        with self.assertRaises(ValueError):self.prepare()
    def test_actual_lease_attention_wrong_dispatch_or_ledger_change_stops_no_rpc(self):
        q=self.prepare();m=cli.c.document(q)
        for field,value in [('phase','attention'),('dispatch_id','different'),('index',2)]:
            bad={**self.s,field:value};self.lease.write_text(json.dumps(bad))
            with self.subTest(field=field),patch.object(cli.bridge,'request') as rpc,self.assertRaises(ValueError):cli.run(q)
            rpc.assert_not_called()
        self.lease.write_text(json.dumps(self.s));self.ledger.write_text('{"changed":1}')
        with self.assertRaisesRegex(ValueError,'ledger-changed'):cli.live_guard(m)
    def test_unknown_run_does_not_construct_transport_or_request(self):
        q=self.prepare();m=cli.c.document(q);cli.runner.publish(cli.folder(m)/'operation.json',{'state':'unknown-open','manifest':m})
        with patch.object(cli,'BridgeTransport',side_effect=AssertionError('no transport')):
            r=cli.run(q);self.assertEqual(r['reason'],'unknown-no-replay');self.assertFalse(r['ui_used'])
    def test_complete_run_pure_replay_without_transport(self):
        q=self.prepare();m=cli.c.document(q);cli.runner.publish(cli.folder(m)/'operation.json',{'state':'complete','manifest':m})
        with patch.object(cli,'BridgeTransport',side_effect=AssertionError('no transport')),patch.object(cli.runner,'verify_complete',return_value={'person_identity_verified':False}):self.assertEqual(cli.run(q)['state'],'complete')
    def test_explicit_unknown_reconcile_reads_only_same_lease_and_missing_effect_stays_unknown(self):
        q=self.prepare();m=cli.c.document(q);job={'groupid':'123','company':'公司','identity':{}};normal=page();normal['tree']['root']=node(children=[card()]);v={'normal_before':{'pages':[normal]},'fresh_job':job,'fresh_profile':{},'current':cli.c.candidate_fields(card())};base=cli.folder(m);before=cli.runner.publish(base/'synthetic-before.json',normal);cmd=cli.runner.e.click(7,'#action');s={'manifest':m,'state':'unknown-open','normal_before':before,'open_command':cmd,'created_at':'2026-10-22T05:00:00+00:00'};p=base/'operation.json';cli.runner.publish(p,s);original=cli.c.ref(p);original_bytes=p.read_bytes();self.s['phase']='attention';self.lease.write_text(json.dumps(self.s));calls=[];show={'drawer':False};build=cli.re.findall(r"const BUILD='([^']+)'",cli.CONTENT.read_text())[0];tab={**normal['tab'],'active':True};windows=[{'focused':True,'windowId':8,'tabs':[tab]}]
        def rpc(cmd):
            calls.append(cmd['op']);self.assertIn(cmd['op'],('tabs','ping','tree'));return {'ok':True,'result':windows if cmd['op']=='tabs' else {'version':cli.bridge.SAFETY_VERSION,'content_build':build,'safety':'DOM-only'} if cmd['op']=='ping' else page()['tree'] if show['drawer'] else normal['tree']}
        with patch.object(cli.runner,'inputs',return_value=v),patch.object(cli.runner,'page_scope',side_effect=lambda p,v,**kw:p):
            with self.assertRaisesRegex(ValueError,'single-drawer'):cli.reconcile(q,original_state_sha256=original['sha256'],request=rpc)
            self.assertEqual(p.read_bytes(),original_bytes);self.assertEqual(calls,['tabs','ping','tree','tabs']);calls.clear();show['drawer']=True;out=cli.reconcile(q,original_state_sha256=original['sha256'],request=rpc);self.assertEqual(out['state'],'opened');self.assertFalse(out['ui_used']);self.assertFalse(out['input_replayed']);self.assertEqual(calls,['tabs','ping','tree','tabs']);self.assertNotIn('open_reply',json.loads(p.read_bytes()))
            calls.clear()
            with self.assertRaisesRegex(ValueError,'state-sha'):cli.reconcile(q,original_state_sha256=original['sha256'],request=rpc)
            self.assertFalse(calls)
    def test_run_bounded_steps_and_code_change_stops(self):
        q=self.prepare()
        with self.assertRaisesRegex(ValueError,'bounded'):cli.run(q,steps=11)
        m=cli.c.document(q);m['code'][str(cli.CODE[0].resolve())]='0'*64
        with self.assertRaisesRegex(ValueError,'code-changed'):cli.live_guard(m)
    def test_fresh_transport_exact_sequence_and_raw_saved_before_ping_failure(self):
        q=self.prepare();m=cli.c.document(q);expected=page()['tab'];windows=[{'focused':True,'windowId':8,'tabs':[{**expected,'active':True}]}];calls=[]
        def rpc(cmd):
            calls.append(cmd['op']);return {'ok':True,'result':windows if cmd['op']=='tabs' else {'version':cli.bridge.SAFETY_VERSION,'content_build':transport.build,'safety':'DOM-only'} if cmd['op']=='ping' else page()['tree']}
        with patch.object(cli.runner,'inputs',return_value={'normal_before':{'pages':[page()]}}),patch.object(cli.runner,'page_scope',side_effect=lambda p,v:p):
            transport=cli.BridgeTransport(m,cli.folder(m),rpc);out=transport.fresh();self.assertEqual(calls,['tabs','ping','tree','tabs']);self.assertEqual(out['tab']['tabId'],7);self.assertEqual(len(list(transport.attempt.glob('*.json'))),4)
            calls.clear()
            def bad(cmd):return {'ok':True,'result':windows if cmd['op']=='tabs' else {'safety':'bad'}}
            transport=cli.BridgeTransport(m,cli.folder(m),bad)
            with self.assertRaisesRegex(ValueError,'content-not-loaded'):transport.fresh()
            self.assertEqual(len(list(transport.attempt.glob('*.json'))),2)
    def test_run_whole_fake_bridge_cycle_then_verify_and_receipt_without_ui(self):
        q=self.prepare();m=cli.c.document(q);job={'groupid':'123','company':'公司','identity':{'provider':'P','account_id':'A','manager':'M'}};review={'review_key':'123:old','store':'店','customer':'M.','text':'正文','product':'完整商品','stars':1};old=cli.c.parse_case(job,page('M.'));normal=page();normal['tree']['root']=node(children=[card()]);v={'normal_before':{'pages':[normal]},'fresh_job':job,'fresh_profile':{},'current':cli.c.candidate_fields(card()),'review':review,'old_case':old,'pending':[{'review_key':'123:old','review':review,'case':old['case']}]};state={'opened':False};calls=[]
        raw=cli.CONTENT.read_text();build=cli.re.findall(r"const BUILD='([^']+)'",raw)[0];tab={**normal['tab'],'active':True};windows=[{'focused':True,'windowId':8,'tabs':[tab]}]
        def rpc(cmd):
            calls.append(cmd)
            if cmd['op']=='tabs':out=windows
            elif cmd['op']=='ping':out={'version':cli.bridge.SAFETY_VERSION,'content_build':build,'safety':'DOM-only'}
            elif cmd['op']=='tree':out=page()['tree'] if state['opened'] else normal['tree']
            else:
                closing=cmd['locator']['value']=='#close';state['opened']=not closing;out={'kind':'complaint-read','clicked':{'selector':cmd['locator']['value'],'name':'' if closing else '投诉审核中','attributes':{'class':'byted-drawer-close-icon' if closing else 'button-vhqEd7 isHighlight-DoxxP4'}}}
            return {'ok':True,'result':out}
        with patch.object(cli.runner,'inputs',return_value=v),patch.object(cli.runner,'page_scope',side_effect=lambda p,v,**kw:p):
            out=cli.run(q,request=rpc);self.assertEqual(out['state'],'complete');self.assertEqual([x['op'] for x in calls].count('click'),2);self.assertEqual(len(calls),14);self.assertEqual(cli.verify(q)['alias']['original_review_key'],'123:old');receipt=cli.record_reconciled(q);self.assertFalse(receipt['ledger_modified']);self.assertFalse(receipt['case_memory_modified']);self.assertEqual(json.loads(self.ledger.read_text()),{'company':'公司'})
            calls.clear();self.assertEqual(cli.run(q,request=rpc)['state'],'complete');self.assertFalse(calls)
    def test_transport_mutation_only_exact_saved_intent_and_kind(self):
        q=self.prepare();m=cli.c.document(q);cmd={'op':'click','kind':'complaint-read','tabId':7,'locator':{'by':'selector','value':'#action'}};p=cli.folder(m)/'operation.json';cli.runner.publish(p,{'manifest':m,'state':'unknown-open','open_command':cmd});calls=[]
        transport=cli.BridgeTransport(m,cli.folder(m),lambda cmd:calls.append(cmd) or {'ok':True,'result':{'synthetic':'reply'}})
        with self.assertRaisesRegex(ValueError,'unreviewed-command'):transport.mutation({**cmd,'kind':'complaint'})
        self.assertFalse(calls);self.assertEqual(transport.mutation(cmd),{'synthetic':'reply'});self.assertEqual(len(calls),1)
if __name__=='__main__':unittest.main()
