"""Offline recovery tests: fake AX and bridge only, no browser/process access."""
import copy,importlib.util,json,sys,tempfile,unittest
from zipfile import ZipFile
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_chrome_popup_navigation import snapshot,popup_snapshot
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts'
spec=importlib.util.spec_from_file_location('popup_recover_download_tests',SCRIPTS/'popup-recover-download.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
NOW=datetime(2026,10,21,2,0,0,tzinfo=timezone.utc)
def download_shell():
    s=popup_snapshot();link=s['tree']['children'][1]['children'][0];link.update(AXTitle=r.DOWNLOAD_LABEL,AXDescription=r.DOWNLOAD_LABEL)
    return s
class Native:
    def __init__(self,world):self.world=world;self.pid=55
    def tree(self):
        tree=download_shell() if self.world['bubble'] else snapshot()
        if self.world.get('no_icon'):tree['tree']['children'][0]['children']=[]
        return tree
    def press(self,path,window_path):
        self.world['presses']+=1
        if self.world.get('fail_press'):raise RuntimeError('unknown injected AX result')
        if not self.world['bubble']:self.world['bubble']=True
        else:self.world['download_link']=True
    def close(self):pass
class DownloadRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job={'action':'acquire','work_order_id':'fixture','company':'fixture','groupid':'123','date_range':{'start':'2026-10-17','end':'2026-10-19'},'source_dir':str(self.root/'sources'),'workflow_path':str(self.root/'formal.json')}
        self.url='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123'
        command={'op':'click','kind':'download','tabId':9,'selector':'#unique-fixture-download'}
        generated={'state':'success','text':'门店评价_全部门店_2026_10_17-2026_10_19 生成成功','generated_at':'2026-10-21 09:59:00','selector':'#unique-fixture-row'}
        ticket={'ticket':'fixture-ticket-123456789','since':(NOW-timedelta(minutes=1)).isoformat(),'expires':(NOW+timedelta(minutes=9)).timestamp()*1000}
        self.s={'backend':'local-dom-bridge','state':'running','phase':'downloadResult','downloadPending':True,'work_order_id':'fixture','fingerprint':r.workflow.fingerprint(self.job),'record_tab_id':9,'record_url':self.url,'company':'fixture','groupid':'123','date_range':self.job['date_range'],'identity':{'provider':'p','account_id':'a','manager':'m'},'download_command':command,'calls':[{'command':command,'state':'confirmed','result':{'kind':'download'}}],'generated_record':generated,'baseline_records':[],'download_ticket':ticket,'checkpoints':[{'stage':'export-generated',**{k:generated[k] for k in ('text','generated_at')},'record_url':self.url},{'stage':'download-intent','ticket':ticket['ticket'],'generated_at':generated['generated_at']}]}
        self.save();self.world={'bubble':False,'presses':0};self.commands=[];self.factories=0
    def save(self):Path(self.job['workflow_path']).write_text(json.dumps(self.s))
    def tabs(self):return [{'windowId':3,'focused':True,'tabs':[{'tabId':9,'windowId':3,'active':True,'allowed':True,'title':'抖音来客','url':self.url}]}]
    def invoke(self,c):
        self.commands.append(c)
        if c['op']=='activate':return {'ok':True,'result':{'tabId':9,'windowId':3,'url':self.url,'title':'抖音来客','active':True,'windowFocused':True,'observedAt':NOW.isoformat(),'safety_version':'dom-only-20261021-11'}}
        if c['op']=='tabs':return {'ok':True,'result':self.tabs()}
        self.assertIn(c['op'],('download-status','download-reconcile'));self.assertEqual(c['ticket'],self.s['download_ticket']['ticket'])
        return {'ok':True,'result':{'state':'pending','ticket':c['ticket'],**({'readonly':True,'reconciled':True} if c['op']=='download-reconcile' else {})}}
    def factory(self,expected_pid):self.assertEqual(expected_pid,55);self.factories+=1;return Native(self.world)
    def recover(self,**kw):return r.recover(self.job,9,55,self.root/'recovery',self.invoke,self.factory,at=NOW,**kw)
    def expire(self):
        self.s['download_ticket'].update(since=(NOW-timedelta(minutes=11)).isoformat(),expires=(NOW-timedelta(minutes=1)).timestamp()*1000);self.save()
    def test_closed_list_link_single_activate_original_ticket_only(self):
        result=self.recover();self.assertEqual(result['state'],'await-download');self.assertEqual(self.world['presses'],2)
        self.assertEqual([c['op'] for c in self.commands],['download-status','activate','tabs','download-status'])
        intent=json.loads((self.root/'recovery/link-intent.json').read_text());self.assertTrue(intent['press_returned_success']);self.assertEqual(intent['state'],'unknown')
        self.assertFalse(result['new_ticket_created']);self.assertFalse(result['new_download_click'])
    def test_repeat_only_original_ticket_read_no_ax_no_activate(self):
        self.recover();self.commands=[];factories=self.factories
        self.recover();self.assertEqual([c['op'] for c in self.commands],['download-status']);self.assertEqual(self.factories,factories);self.assertEqual(self.world['presses'],2)
    def test_expired_default_waits_no_api_no_ax_and_repeat_same(self):
        self.expire()
        for _ in range(2):self.assertEqual(self.recover()['state'],'await-readonly-reconcile')
        self.assertFalse(self.commands);self.assertEqual(self.factories,0)
    def test_expired_opt_in_fresh_readonly_pending_once_and_repeat_readonly(self):
        self.expire();self.recover(allow_expired_readonly_reconcile=True)
        expected={'op':'download-reconcile','tabId':9,'groupid':'123','ticket':self.s['download_ticket']['ticket'],'since':self.s['download_ticket']['since'],'filename':'门店评价_全部门店_2026_10_17-2026_10_19.xlsx'}
        self.assertEqual(self.commands[0],expected);self.assertEqual(self.commands[-1],expected);self.assertEqual(self.world['presses'],2)
        self.commands=[];factories=self.factories;self.recover(allow_expired_readonly_reconcile=True)
        self.assertEqual(self.commands,[expected]);self.assertEqual(self.factories,factories)
    def test_expired_in_progress_never_presses_popup(self):
        self.expire();original=self.invoke
        def downloading(c):
            response=original(c);response['result']['state']='in_progress';return response
        self.invoke=downloading
        result=self.recover(allow_expired_readonly_reconcile=True)
        self.assertEqual(result['state'],'await-download');self.assertEqual(self.factories,0);self.assertTrue(all(c['op']=='download-reconcile' for c in self.commands))
    def test_completed_original_download_verifies_xlsx_without_ui(self):
        source=self.root/'source.xlsx'
        with ZipFile(source,'w') as z:
            z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml','<workbook/>')
        self.invoke=lambda c:{'ok':True,'result':{'state':'complete','exists':True,'path':str(source),'bytesReceived':source.stat().st_size,'totalBytes':source.stat().st_size}}
        result=self.recover();self.assertEqual(result['state'],'complete');self.assertEqual(result['verified_file']['path'],str(source.resolve()));self.assertEqual(self.factories,0)
    def test_expired_reconciliation_without_readonly_proof_refused(self):
        self.expire();self.invoke=lambda c:{'ok':True,'result':{'state':'pending','ticket':self.s['download_ticket']['ticket']}}
        with self.assertRaisesRegex(RuntimeError,'readonly-reconciliation'):self.recover(allow_expired_readonly_reconcile=True)
        self.assertEqual(self.factories,0)
    def test_expired_unsupported_bridge_stops_before_activate(self):
        self.expire()
        def unsupported(c):self.commands.append(c);return {'ok':False,'error':'unsupported-op'}
        self.invoke=unsupported
        with self.assertRaisesRegex(RuntimeError,'unsupported-op'):self.recover(allow_expired_readonly_reconcile=True)
        self.assertEqual([c['op'] for c in self.commands],['download-reconcile']);self.assertEqual(self.factories,0)
    def test_unknown_press_not_replayed(self):
        self.world['fail_press']=True
        with self.assertRaisesRegex(RuntimeError,'injected'):self.recover()
        presses=self.world['presses'];self.commands=[];self.world['fail_press']=False
        self.recover();self.assertEqual(self.world['presses'],presses);self.assertEqual([c['op'] for c in self.commands],['download-status'])
    def test_confirmation_and_scope_gaps_stop_before_bridge(self):
        mutations=[lambda s:s.update(phase='submit'),lambda s:s['calls'][0].update(state='unknown'),lambda s:s['calls'].append(copy.deepcopy(s['calls'][0])),lambda s:s.update(record_tab_id=99),lambda s:s['generated_record'].update(text='wrong-date'),lambda s:s['baseline_records'].append(copy.deepcopy(s['generated_record'])),lambda s:s['checkpoints'][-1].update(ticket='wrong'),lambda s:s.update(groupid='999'),lambda s:s.update(identity=None)]
        original=copy.deepcopy(self.s)
        for i,mutate in enumerate(mutations):
            self.s=copy.deepcopy(original);mutate(self.s);self.save()
            with self.subTest(i=i),self.assertRaises((RuntimeError,ValueError)):self.recover()
        self.assertFalse(self.commands);self.assertEqual(self.factories,0)
    def test_main_mirror_is_not_standalone_bubble(self):
        shell=snapshot();mirror=download_shell()['tree']['children'][1]['children'][0];shell['tree']['children'][0]['children'].append(mirror)
        with self.assertRaisesRegex(RuntimeError,'bubble-not-unique'):r.download_target(shell,55,'抖音来客')
    def test_changed_label_or_two_links_or_url_denied(self):
        for shape in ('label','duplicate','url'):
            shell=download_shell();bubble=shell['tree']['children'][1];link=bubble['children'][0]
            if shape=='label':link['AXTitle']='different'
            elif shape=='duplicate':bubble['children'].append(copy.deepcopy(link))
            else:link['AXURL']='https://example.com/file'
            with self.subTest(shape=shape),self.assertRaises(RuntimeError):r.download_target(shell,55,'抖音来客')
    def test_existing_bubble_needs_complete_scope_chain(self):
        self.world['bubble']=True
        with self.assertRaisesRegex(RuntimeError,'complete-list-chain'):self.recover()
        self.assertEqual(self.world['presses'],0)
    def test_existing_bubble_reuses_old_verified_list_one_link_only(self):
        self.world['bubble']=True;old=self.root/'old-list.json';old.write_text(json.dumps({'mode':'open-list','state':'complete','expected_pid':55,'bridge_focus':{'tabId':9,'windowId':3,'groupid':'123','url':self.url},'after':download_shell()}))
        self.recover(list_intent=old);self.assertEqual(self.world['presses'],1)
    def test_orphan_intent_stops_before_bridge(self):
        folder=self.root/'recovery';folder.mkdir();(folder/'link-intent.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'orphan'):self.recover()
        self.assertFalse(self.commands)
    def test_live_status_without_ticket_uses_local_original_ticket_binding(self):
        original=self.invoke
        def no_ticket(c):
            response=original(c)
            if c['op']=='download-status':response['result'].pop('ticket')
            return response
        self.invoke=no_ticket
        result=self.recover();self.assertEqual(result['observed_original_ticket'],self.s['download_ticket']['ticket']);self.assertEqual(self.world['presses'],2)
    def test_ticket_mismatch_response_is_refused(self):
        self.invoke=lambda c:{'ok':True,'result':{'state':'pending','ticket':'wrong'}}
        with self.assertRaisesRegex(RuntimeError,'response-mismatch'):self.recover()
        self.assertEqual(self.factories,0)
    def test_auto_probe_without_icon_is_retryable_and_never_admits_action(self):
        self.world['no_icon']=True
        for _ in range(2):
            result=self.recover(probe_pending=True)
            self.assertEqual(result['phase'],'no-blocked-popup-observed')
            self.assertFalse((self.root/'recovery/recovery.json').exists())
            self.assertFalse((self.root/'recovery/list-intent.json').exists())
            self.assertFalse((self.root/'recovery/link-intent.json').exists())
        self.assertEqual(self.world['presses'],0)
        self.world['no_icon']=False;self.commands=[]
        self.recover(probe_pending=True)
        self.assertEqual(self.world['presses'],2)
        self.assertEqual(sum(c['op']=='activate' for c in self.commands),1)
        self.assertTrue((self.root/'recovery/recovery.json').is_file())
        factories=self.factories;self.commands=[]
        self.recover(probe_pending=True)
        self.assertEqual(self.world['presses'],2);self.assertEqual(self.factories,factories)
        self.assertEqual([c['op'] for c in self.commands],['download-status'])
    def test_auto_probe_in_progress_does_not_activate_or_press(self):
        original=self.invoke
        def ongoing(command):
            response=original(command);response['result']['state']='in_progress';return response
        self.invoke=ongoing
        self.assertEqual(self.recover(probe_pending=True)['state'],'await-download')
        self.assertEqual([c['op'] for c in self.commands],['download-status'])
        self.assertEqual(self.factories,0);self.assertFalse((self.root/'recovery/recovery.json').exists())
    def test_auto_probe_existing_unbound_bubble_does_not_create_intent(self):
        self.world['bubble']=True
        result=self.recover(probe_pending=True)
        self.assertEqual(result['phase'],'existing-bubble-needs-complete-list-chain')
        self.assertEqual(self.world['presses'],0);self.assertFalse((self.root/'recovery/recovery.json').exists())
if __name__=='__main__':unittest.main()
