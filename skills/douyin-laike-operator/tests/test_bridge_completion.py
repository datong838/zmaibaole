"""End-to-end state machine tests with fake bridge and temporary synthetic XLSX."""
import copy,importlib.util,json,sys,tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from zipfile import ZipFile
from unittest.mock import patch
SCRIPTS=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('bridge_completion_runtime',SCRIPTS/'bridge-workflow.py');bw=importlib.util.module_from_spec(spec);spec.loader.exec_module(bw)
from role_cli import finalize_journal
IDENTITY={'provider':'服务商123456789','account_id':'987654321','manager':'测试经理'}
def leaf(name,selector,**kw):return {'name':name,'selector':selector,'children':[],**kw}
def source(dates,count=107,modal=True):
    fields=[leaf(name,'#'+str(i),role='textbox',attributes={'value':value}) for i,(name,value) in enumerate([('评价时间',dates['start']+' ~ '+dates['end']),('评价类型','全部'),('评价来源','全部'),('评价状态','全部')])]
    fields.extend([leaf('评价 已筛选 '+str(count)+' 条','#count'),leaf('按省市 全部门店','#scope',attributes={'id':'CommentPoi_select'})])
    if modal:fields.append({'name':'请选择要导出的评价范围 所属门店 按省市 全部门店 评价时间','selector':'#modal','attributes':{'class':'byted-modal'},'children':[leaf('','#range',role='textbox',placeholder='请选择日期范围，不选则为近一年',attributes={'value':dates['start']+' ~ '+dates['end']}),leaf('导出','#submit',role='button')]})
    return {'url':'https://life.douyin.com/p/life_comment/management','truncated':False,'root':{'name':'','children':fields}}
def record_tree(dates,stamps):
    # Portable synthetic rendering of the reviewed six-cell byted table + pager.
    def n(name,selector,cs='',children=(),tag='div'):
        return {'name':name,'selector':selector,'tag':tag,'role':'generic','attributes':{'class':cs},'children':list(children)}
    rows=[]
    for i,(stamp,status) in enumerate(stamps):
        values=[bw.export_tag(dates),'门店评价',stamp,status,'','下载 删除'];cells=[]
        for j,value in enumerate(values):
            content=[leaf('下载','#download'+str(i)),leaf('删除','#delete'+str(i))] if j==5 else []
            cells.append(n(value,'#r'+str(i)+'-c'+str(j),'byted-table-cell byted-table-cell-body',content))
        label=' '.join(x for x in values if x);rows.append(n(label,'#r'+str(i),'byted-table-column byted-table-row',[n(label,'#r'+str(i)+'-visible','byted-table-column-visible',[n(label,'#r'+str(i)+'-scroll','byted-table-column-scroller',cells)])]))
    head=n('报表名称 报表类型 开始生成时间 状态 操作','#head','byted-table-head',[n(value,'#h'+str(i),'byted-table-cell byted-table-cell-head') for i,value in enumerate(['报表名称','报表类型','开始生成时间','状态','','操作'])])
    pager=n('共'+str(len(rows))+'条记录 1','#pager','byted-pager',[n('共'+str(len(rows))+'条记录','#total','byted-pager-record',tag='span'),n('1','#group','byted-pager-item-group',[n('','#prev','byted-pager-item byted-pager-item-disabled',[n('','#left','byted-icon-left')],tag='li'),n('1','#one','byted-pager-item byted-pager-item-checked',tag='li'),n('','#next','byted-pager-item byted-pager-item-disabled',[n('','#right','byted-icon-right')],tag='li')],tag='ul')])
    return {'url':'https://life.douyin.com/p/fulfillsettle/export_records/20101','truncated':False,'root':{'children':[n('门店评价','#active','byted-tab-bar-item-active'),n('','#table','byted-table-container byted-table-container-row',[head,n('','#body','byted-table-body',rows),pager])]}}
class FakeBridge:
    def __init__(self,job):self.job=job;self.calls=[];self.exported=False;self.refreshed=False;self.failure=None;self.record_group='123';self.download=self.job['workflow_path']+'.download.xlsx';self.stamps=[];self.bad_download=False;self.receipt_override={}
    def __call__(self,c):
        self.calls.append(copy.deepcopy(c));op=c['op'];s=json.loads(Path(self.job['workflow_path']).read_text())
        if op=='tabs':return {'ok':True,'result':[{'tabs':[{'tabId':5,'allowed':True,'url':'https://life.douyin.com/p/life_comment/management?groupid=123'},{'tabId':6,'allowed':True,'url':'https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid='+self.record_group}]}]}
        if op=='ping':return {'ok':True,'result':{'version':bw.VERSION,'safety':'DOM-only'}}
        if op=='tree':
            result=record_tree(self.job['date_range'],self.stamps if self.refreshed else []) if c['tabId']==6 else source(self.job['date_range'],modal=not self.exported)
            return {'ok':True,'result':result}
        current=[e for e in s['calls'] if e['key']==str(s['revision'])+':'+s['phase']]
        if op in ('click','reload-records','download-begin'):
            assert len(current)==1 and current[0]['state']=='unknown','side effect must have persisted intent'
        if op=='click' and c['kind']=='export':
            assert s['exportPending'] and any(e['stage']=='export-intent' for e in s['checkpoints'])
            self.exported=True;self.stamps=[((datetime.now(ZoneInfo('Asia/Shanghai'))+timedelta(seconds=2)).strftime('%Y-%m-%d %H:%M:%S'),'生成成功')]
            if self.failure=='submit':raise TimeoutError('unknown submit outcome')
            return {'ok':True,'result':{'clicked':True}}
        if op=='reload-records':
            self.refreshed=True
            if self.failure=='reload':raise TimeoutError('unknown reload outcome')
            return {'ok':True,'result':{'reloaded':True,'tabId':6}}
        if op=='download-begin':
            if self.failure=='ticket':raise TimeoutError('unknown ticket outcome')
            return {'ok':True,'result':{'ticket':'fixture-ticket','since':datetime.now(timezone.utc).isoformat(),'expires':int((datetime.now(timezone.utc).timestamp()+600)*1000)}}
        if op=='click' and c['kind']=='download':
            assert s['downloadPending'] and any(e['stage']=='download-intent' for e in s['checkpoints'])
            if self.bad_download:Path(self.download).write_bytes(b'not a workbook')
            else:
                with ZipFile(self.download,'w') as z:z.writestr('[Content_Types].xml','<Types/>');z.writestr('xl/workbook.xml','<workbook/>')
            if self.failure=='download':raise TimeoutError('unknown download click')
            return {'ok':True,'result':{'clicked':True}}
        if op=='download-status':
            size=Path(self.download).stat().st_size
            return {'ok':True,'result':{'state':'complete','path':self.download,'exists':True,'bytesReceived':size,'totalBytes':size,'downloadId':8,**self.receipt_override}}
        raise AssertionError('unexpected command '+str(c))
    def count(self,kind):return sum(c.get('op')=='click' and c.get('kind')==kind for c in self.calls)
class CompletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.job={'action':'acquire','work_order_id':'fixture','company':'fixture','groupid':'123','date_range':{'start':'2026-10-16','end':'2026-10-19'},'source_dir':str(self.root/'immutable'),'workflow_path':str(self.root/'workflow.json'),'identity_baseline':IDENTITY}
        self.fake=FakeBridge(self.job);w=self.w();w.s.update(phase='readyToExport',initial_groupid='123',identity=IDENTITY,page_filtered=107,baseline_records=[],record_tab_id=6,record_url='https://life.douyin.com/p/fulfillsettle/export_records/20101?groupid=123',transport_proof={'safety_version':bw.VERSION,'safety':'DOM-only','reviewed_extension_ready':True},checkpoints=[{'stage':s} for s in ('identity','switch','navigation','filter')]);w.save()
    def w(self):return bw.Workflow(self.job,5,self.fake)
    def phase(self):return json.loads(Path(self.job['workflow_path']).read_text())['phase']
    def until(self,phase,limit=20):
        for i in range(limit):
            if self.phase()==phase:return self.w()
            self.w().tick()
        self.fail('did not reach '+phase+'; current '+self.phase())
    def test_full_export_download_finalize_from_fresh_process_each_tick(self):
        w=self.until('done');self.assertEqual(w.s['state'],'complete');self.assertEqual(self.fake.count('export'),1);self.assertEqual(self.fake.count('download'),1)
        result=finalize_journal(self.job,Path(self.job['workflow_path']),self.root/'receipt.json')
        self.assertTrue(result['download_verified']);self.assertEqual(result['page_filtered'],107);self.assertEqual(result['identity_before'],IDENTITY);self.assertTrue(Path(result['source']).is_file())
        before=len(self.fake.calls);w.tick();self.assertEqual(len(self.fake.calls),before)
    def test_expired_ticket_reconciles_original_scope_without_second_download(self):
        self.until('downloadResult');w=self.w();original=copy.deepcopy(w.s['download_ticket']);seen=[]
        def invoke(command):
            if command['op']=='download-status':return {'ok':False,'error':'download ticket missing or expired'}
            if command['op']=='download-reconcile':
                seen.append(copy.deepcopy(command))
                return self.fake({'op':'download-status','ticket':command['ticket']})
            return self.fake(command)
        w.invoke=invoke;w.tick()
        self.assertEqual(w.s['state'],'complete');self.assertEqual(self.fake.count('download'),1)
        self.assertEqual(seen,[{'op':'download-reconcile','tabId':6,'groupid':'123','ticket':original['ticket'],
                               'since':original['since'],'filename':bw.export_tag(self.job['date_range'])+'.xlsx'}])
        self.assertEqual(sum(c['op']=='download-begin' for c in self.fake.calls),1)
    def test_other_download_errors_do_not_start_reconciliation(self):
        self.until('downloadResult');w=self.w();seen=[]
        def invoke(command):
            if command['op']=='download-status':return {'ok':False,'error':'ambiguous downloads'}
            if command['op']=='download-reconcile':seen.append(command)
            return self.fake(command)
        w.invoke=invoke
        with self.assertRaisesRegex(RuntimeError,'ambiguous'):w.tick()
        self.assertEqual(seen,[]);self.assertEqual(self.fake.count('download'),1)
    def test_unknown_submit_reconciles_new_row_without_second_submit(self):
        self.until('submitExport');self.fake.failure='submit'
        with self.assertRaises(TimeoutError):self.w().tick()
        self.fake.failure=None;self.until('done');self.assertEqual(self.fake.count('export'),1);self.assertEqual(self.fake.count('download'),1)
    def test_unknown_download_click_reads_existing_ticket_never_clicks_again(self):
        self.until('clickDownload');self.fake.failure='download'
        with self.assertRaises(TimeoutError):self.w().tick()
        self.fake.failure=None;self.until('done');self.assertEqual(self.fake.count('download'),1)
    def test_unknown_ticket_does_not_arm_second_ticket_or_download(self):
        self.until('armDownload');self.fake.failure='ticket'
        with self.assertRaises(TimeoutError):self.w().tick()
        self.fake.failure=None
        with self.assertRaisesRegex(ValueError,'unknown-do-not-replay'):self.w().tick()
        self.assertEqual(sum(c['op']=='download-begin' for c in self.fake.calls),1);self.assertEqual(self.fake.count('download'),0)
    def test_confirmed_submit_cached_after_crash_before_phase_advance(self):
        self.until('submitExport');w=self.w();w.go=lambda phase:(_ for _ in ()).throw(RuntimeError('crash before next phase'))
        with self.assertRaisesRegex(RuntimeError,'crash'):w.tick()
        self.until('done');self.assertEqual(self.fake.count('export'),1)
    def test_unknown_refresh_never_issues_a_new_reload_key(self):
        self.until('reloadRecords');self.fake.failure='reload'
        with self.assertRaises(TimeoutError):self.w().tick()
        self.fake.failure=None;self.fake.stamps=[];self.w().tick()
        with self.assertRaisesRegex(ValueError,'refresh-outcome-unknown'):self.w().tick()
        keys=[c['reloadKey'] for c in self.fake.calls if c['op']=='reload-records'];self.assertEqual(len(keys),1);self.assertEqual(self.fake.count('export'),1)
    def test_stale_same_name_baseline_row_cannot_satisfy_new_export(self):
        old=bw.export_tag(self.job['date_range'])+' 门店评价 2026-10-01 00:00:00 生成成功 下载 删除'
        w=self.w();w.s['baseline_records']=[{'text':old,'generated_at':'2026-10-01 00:00:00','state':'success','selector':'#old'}];w.save()
        self.until('pollRecords');self.fake.stamps=[('2026-10-01 00:00:00','生成成功')];self.w().tick();self.assertEqual(self.phase(),'pollRecords');self.assertIn('not-visible-or-ready',self.w().s['waiting_for']);self.assertEqual(self.fake.count('download'),0)
    def test_submit_rederives_fresh_modal_target_and_refuses_drift_or_disabled(self):
        self.until('submitExport');original=self.fake.__class__.__call__
        for change in ('selector','disabled'):
            def invoke(command):
                result=original(self.fake,command)
                if command['op']=='tree' and command['tabId']==5:
                    modal=result['result']['root']['children'][-1];target=modal['children'][-1]
                    if change=='selector':target['selector']='#different-control'
                    else:target['disabled']=True
                return result
            w=bw.Workflow(self.job,5,invoke)
            with self.subTest(change=change),self.assertRaisesRegex(ValueError,'target-changed|element-not-ready'):w.tick()
        self.assertEqual(self.fake.count('export'),0)
    def test_changed_count_during_ready_state_never_submits(self):
        w=self.w();w.s['page_filtered']=106;w.save()
        with self.assertRaisesRegex(ValueError,'count-changed'):w.tick()
        self.assertEqual(self.fake.count('export'),0)
    def test_other_company_record_tab_blocks_before_submission(self):
        self.fake.record_group='999'
        with self.assertRaisesRegex(ValueError,'source-company'):self.w().tick()
        self.assertEqual(self.fake.count('export'),0)
    def test_no_new_record_waits_without_reexport(self):
        self.until('pollRecords');self.fake.stamps=[];self.w().tick();self.assertEqual(self.phase(),'pollRecords');self.assertIn('not-visible-or-ready',self.w().s['waiting_for']);self.assertEqual(self.fake.count('export'),1)
    def test_multiple_new_matching_records_stop_before_download(self):
        self.until('pollRecords');stamp=self.fake.stamps[0][0];future=(datetime.strptime(stamp,'%Y-%m-%d %H:%M:%S')+timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S');self.fake.stamps.append((future,'生成成功'))
        with self.assertRaisesRegex(ValueError,'ambiguous'):self.w().tick()
        self.assertEqual(self.fake.count('download'),0)
    def test_failed_record_does_not_submit_again(self):
        self.until('pollRecords');self.fake.stamps[0]=(self.fake.stamps[0][0],'生成失败');w=self.w();w.tick();self.assertEqual(w.s['state'],'failed');self.assertEqual(w.s['error_code'],'platform-export-failed');w.tick();self.assertEqual(self.fake.count('export'),1)
    def test_invalid_workbook_does_not_finish_or_redownload(self):
        self.until('clickDownload');self.fake.bad_download=True;self.w().tick()
        with self.assertRaisesRegex(ValueError,'xlsx-invalid'):self.w().tick()
        self.assertEqual(self.phase(),'downloadResult');self.assertEqual(self.fake.count('download'),1)
    def test_download_size_and_exists_proof_must_match_local_file(self):
        self.until('downloadResult')
        for override in ({'exists':False},{'bytesReceived':1},{'path':'relative.xlsx'}):
            self.fake.receipt_override=override
            with self.subTest(override=override),self.assertRaises(ValueError):self.w().tick()
        self.assertEqual(self.fake.count('download'),1)
    def test_pending_download_invokes_fixed_recovery_after_status_then_finishes(self):
        self.until('downloadResult');w=self.w();seen=[]
        original=w.download_status
        def pending():seen.append('status');return {'state':'pending'}
        def recovered():seen.append('recovery');return {'download_status':original()}
        with patch.object(w,'download_status',pending),patch.object(w,'recover_download_popup',recovered):w.tick()
        self.assertEqual(seen,['status','recovery']);self.assertEqual(w.s['state'],'complete')
        self.assertEqual(self.fake.count('download'),1)
    def test_pending_without_icon_stays_pending_and_does_not_redownload(self):
        self.until('downloadResult');w=self.w()
        with patch.object(w,'download_status',return_value={'state':'pending'}),patch.object(w,'recover_download_popup',return_value={'state':'await-download','phase':'no-blocked-popup-observed'}) as recovery:w.tick()
        recovery.assert_called_once_with();self.assertEqual(w.s['phase'],'downloadResult')
        self.assertEqual(w.s['waiting_for'],'download-complete');self.assertEqual(self.fake.count('download'),1)
    def test_in_progress_does_not_start_native_recovery(self):
        self.until('downloadResult');w=self.w()
        with patch.object(w,'download_status',return_value={'state':'in_progress'}),patch.object(w,'recover_download_popup',side_effect=AssertionError('must not recover')):w.tick()
        self.assertEqual(w.s['phase'],'downloadResult');self.assertEqual(self.fake.count('download'),1)
    def test_unknown_download_does_not_construct_native_recovery(self):
        self.until('downloadResult');w=self.w()
        [c for c in w.s['calls'] if c.get('command',{}).get('kind')=='download'][0]['state']='unknown'
        w.save()
        result=w.recover_download_popup()
        self.assertEqual(result['phase'],'download-click-outcome-unconfirmed')
        self.assertFalse((self.root/'native-download-navigation').exists())
if __name__=='__main__':unittest.main()
