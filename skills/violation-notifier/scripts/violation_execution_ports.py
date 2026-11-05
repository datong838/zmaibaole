"""Concrete existing-API ports for violation_execution; no pretend collector.
All mutations retain the child API's own durable intent/lock/unknown guard.
Only the known public-DOM center/records/detail/profile contracts are supported.
"""
import importlib.util,json,sys,fcntl,copy,contextlib,io,subprocess,time,re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlsplit
import role_execution_order as o
import violation_execution as engine
import workflow as w
import governance_detail as d
import governance_dom as g
import governance_capture as capture
import governance_zero_capture as zero
import center_reconciliation as center
import prepare_records_profile as profiles
import records_region_navigation as screenshot_nav
import region_frame_capture as region
ROOT=Path(__file__).resolve().parents[3]
need=o.need
def module(name,path):
    if name in sys.modules:
        m=sys.modules[name];need(Path(m.__file__).resolve()==path.resolve(),'execution-module-origin-conflict');return m
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
nav=d.nav
discovery=module('violation_execution_discovery',Path(__file__).with_name('bridge-profile-discovery.py'))
company_nav=module('violation_execution_company',ROOT/'skills/douyin-laike-operator/scripts/prepare_company_navigation.py')
operator=module('violation_execution_operator',ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py')
query=d.query_api

COMPANY_GROUPS={'烟台一成教育文化咨询有限公司':'1767942028615694','上海老芗汇餐饮管理有限公司':'1764303851132943'}

# Public primitives copied exactly from the reviewed complaint focus reader.
import ctypes as C
import native_window_capture as nw
sys.path.insert(0,str(ROOT/'skills/wecom-messenger/scripts'))
from public_app_activation import PublicRunningApplication
from ax_capture_grant import NativeAction
FRONT_SOURCE='public-expected-PID-AXFrontmost-and-CG-first-ordinary-v1'
def front_identity(pid,*,app_port=None,cg_port=None,ax_port=None):
    # NSWorkspace may be a per-process cached snapshot without a GUI runloop.
    # Keep it as diagnostic; AX+CG must independently agree for authority.
    port=app_port or PublicRunningApplication();ax=None
    try:
        app=port.identity(pid);diagnostic={}
        try:
            ws=port.send(port.objc.objc_getClass(b'NSWorkspace'),'sharedWorkspace',C.c_void_p);current=port.send(ws,'frontmostApplication',C.c_void_p);ns=port.send(current,'processIdentifier',C.c_int) if current else None
        except Exception as error:ns=None;diagnostic['nsworkspace_error']={'type':type(error).__name__,'message':str(error)}
        native=cg_port or nw.PublicCGWindow();process=nw.process_identity(native,pid);ax=ax_port or NativeAction(pid)
        if hasattr(ax,'frontmost_metadata'):attribute=ax.frontmost_metadata()
        else:
            name=ax.string('AXFrontmost');out=C.c_void_p()
            try:error=ax.ax.AXUIElementCopyAttributeValue(ax.root,name,C.byref(out))
            finally:ax.cf.CFRelease(name)
            if out.value:ax.refs.append(out.value)
            value=ax.decode(out.value) if error==0 and out.value and ax.cf.CFGetTypeID(out.value)==ax.cf.CFBooleanGetTypeID() else None
            attribute={'AX_error':int(error),'present':bool(out.value),'value':value}
        items=native.windows();normal=[w for w in items if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True];first=normal[0] if normal else None
        keys=('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowLayer','kCGWindowIsOnscreen');public={k:first.get(k) for k in keys} if first else None
        if first and first.get('kCGWindowOwnerPID')==pid:public['kCGWindowName']=first.get('kCGWindowName')
        result={'application':app,**diagnostic,'frontmost_source':FRONT_SOURCE,'nsworkspace_frontmost_pid':ns,'expected_AXFrontmost':attribute,'CG_first_ordinary':public,'process':process,'frontmost_pid':None}
        try:result['frontmost_pid']=public_frontmost(result,pid)
        except ValueError as error:result['frontmost_error']=str(error)
        return result
    finally:
        if ax:ax.close()
        port.close()

def public_frontmost(observation,pid):
    a=observation['expected_AXFrontmost'];g=observation['CG_first_ordinary'];o.need(type(a.get('AX_error')) is int and a.get('AX_error')==0 and a.get('present') is True and type(a.get('value')) is bool,'capture-focus-public-AX-frontmost-unavailable');o.need(isinstance(g,dict) and type(g.get('kCGWindowOwnerPID')) is int and g['kCGWindowOwnerPID']>0 and type(g.get('kCGWindowNumber')) is int and g['kCGWindowNumber']>0 and g.get('kCGWindowLayer')==0 and g.get('kCGWindowIsOnscreen') is True,'capture-focus-public-CG-frontmost-unavailable');owner=g['kCGWindowOwnerPID'];o.need(a['value']==(owner==pid),'capture-focus-public-frontmost-evidence-conflict')
    if owner==pid:o.need(g.get('kCGWindowOwnerName')=='Google Chrome','capture-focus-public-CG-owner-name-mismatch')
    return owner

def activate_original_chrome(pid,port=None,process=None):
    # This is not WeCom's fixed-bundle activate_existing wrapper. No launch.
    o.need(type(pid) is int and pid>0,'capture-focus-native-explicit-pid')
    native=process or nw.PublicCGWindow();identity=nw.process_identity(native,pid);port=port or PublicRunningApplication()
    try:
        actual=port.identity(pid);o.need(actual=={'pid':pid,'bundle':'com.google.Chrome','terminated':False},'capture-focus-native-app-identity-mismatch');accepted=port.activate();o.need(accepted is True,'capture-focus-native-activation-rejected');return {'pid':pid,'bundle':'com.google.Chrome','process':identity,'request_accepted':True,'frontmost_verified':False,'launch_used':False}
    finally:port.close()

def capture_native_admission(observation,binding):
    windows=observation['tabs'];hits=[(w,t) for w in windows for t in w.get('tabs',[]) if t.get('tabId')==binding['scope']['tabId']]
    need(len(hits)==1,'execution-capture-focus-native-target-unique');w,t=hits[0]
    need(w.get('windowId')==t.get('windowId')==binding['scope']['windowId'] and t.get('url')==binding['url'] and t.get('allowed') is True,'execution-capture-focus-native-target-binding')
    return public_frontmost(observation,binding['pid'])!=binding['pid'] and t.get('active') is True and (w.get('focused') is True or all(x.get('focused') is False for x in windows))

def initial_ledger_reference(company,reason='execution-ledger-changed-before-start',*,order=None):
    # The original dispatch ledger is a byte snapshot, not the live path.
    name=company.get('company');root=o.PROJECT/'runtime'/o.FLOW/str(name)
    groups=COMPANY_GROUPS
    if order and order.get('active_company_policy'):
        import execution_timing as timing
        policy=timing.company_policy(order['active_company_policy'])
        if policy['kind']=='active-company-scope-policy-v2':groups={r['company']:r['groupid']for r in policy['active']}
    need(name in groups and company.get('groupid')==groups[name] and company.get('root')==str(root),'execution-initial-ledger-company-root')
    expected=o.raw(company['ledger']);snapshot=json.loads(expected)
    need(snapshot.get('company')==name and str(snapshot.get('groupid'))==groups[name] and snapshot.get('mode')=='development' and snapshot.get('browser_backend')=='local-dom-bridge','execution-initial-ledger-company-content')
    current=o.ref(root/'state.json');need(current['sha256']==company['ledger']['sha256'] and o.raw(current)==expected,reason)
    return current

def records_entry_scope(raw,job,tab_id,window_id):
    # Opening the list is not the target-date query or source capture.
    need(raw.get('source')=='local-dom-bridge' and raw.get('tab_id')==tab_id and raw.get('navigation_fingerprint')==nav.tag(job) and raw.get('not_business_capture') is True,'execution-records-entry-source-binding')
    tab=nav.context([{'tabs':[raw['tab']]}],tab_id,job['groupid']);tree=raw['tree'];need(tab.get('windowId')==window_id and urlsplit(tab['url']).path==g.RECORDS and tree.get('url')=='https://life.douyin.com'+g.RECORDS,'execution-records-entry-scope')
    ns=list(g.nodes(tree));nav.identity(tree,job['identity']);need(not any(any(t in n.get('name','') for t in ('安全验证','风险验证','扫码登录','账号异常','请完成验证')) for n in ns),'execution-records-entry-risk')
    at=datetime.fromisoformat(raw.get('observed_at',''));need(at.utcoffset() is not None,'execution-records-entry-time-required');g.date_input(tree)
    # B84: the entry probe certifies scope only, so a records list whose counts
    # have not mounted yet (bare 全部 over an empty tbody, B43) must not be read
    # as a page: records_page would route to the zero-page branch and raise
    # governance-zero-date-binding-required on require_date=False. Skip the
    # parse while counts are pending; the dated query flow re-reads with full
    # date binding under its own settling loop.
    if not g.records_counts_pending(tree):g.records_page(tree,require_date=False)
    return at

def records_entry_from_probe(state,job,tab_id):
    need(state.get('mode')=='records' and state.get('phase')=='profile-required' and state.get('dates_queried') is False and len(state.get('calls',[]))==1 and state['calls'][0].get('state')=='confirmed','execution-records-entry-original-probe')
    anchor=o.doc(state['calls'][0]['before']);before=nav.context([{'tabs':[anchor['tab']]}],tab_id,job['groupid']);nav.identity(anchor['tree'],job['identity']);need(anchor.get('navigation_fingerprint')==nav.tag(job) and urlsplit(before['url']).path==nav.CENTER and anchor['tree'].get('url')=='https://life.douyin.com'+nav.CENTER,'execution-records-entry-original-center')
    raw=o.doc(state['last_observation']);at=records_entry_scope(raw,job,tab_id,before['windowId']);before_at=datetime.fromisoformat(anchor.get('observed_at',''));need(before_at.utcoffset() is not None and before_at<=at,'execution-records-entry-observation-order');return raw

def validate_analysis_fresh_wait(state,job,job_ref,path,tab_id,*,adapter_archive=None):
    """Only a completed original display navigation may request a fresh tick."""
    import center_analysis_tab as analysis
    need(state.get('phase')=='open-date' and state.get('waiting_for')=='fresh-analysis-observation-before-date' and state.get('calls')==[] and not any(state.get(k) for k in ('error','last_error','hold','settling_exhausted')),'execution-analysis-wait-query-state')
    need(state.get('fingerprint')==nav.tag(job) and state.get('tab_id')==tab_id and state.get('approved_version')==nav.VERSION,'execution-analysis-wait-job-scope')
    b=state.get('query_job_binding',{});need(b=={'kind':'governance-query-job-binding-v1','job':job_ref,'fingerprint':nav.tag(job),'tab_id':tab_id,'window_id':b.get('window_id'),'query_state_path':str(path)},'execution-analysis-wait-query-binding')
    pre=state.get('analysis_preflight',{});need(pre.get('state')=='complete' and pre.get('job')==job_ref and pre.get('waiting_for') is None and state.get('last_observation')==pre.get('before') and state.get('observations') and state['observations'][-1]==pre['before'],'execution-analysis-wait-preflight')
    before=o.doc(pre['before']);analysis.validate(before,job);analysis.target(before['tree']);need(before['tab_id']==tab_id and before['tab']['windowId']==b['window_id'],'execution-analysis-wait-original-window')
    canonical=Path(job_ref['path']).parent/'.center-analysis-tab'/nav.tag(job);manifest=o.doc(pre['manifest']);need(adapter_archive is None or adapter_archive['sha256']==pre['adapter_state']['sha256'],'execution-analysis-wait-adapter-archive');adapter=o.doc(adapter_archive or pre['adapter_state']);need(Path(pre['manifest']['path'])==canonical/'manifest.json' and Path(pre['adapter_state']['path'])==canonical/'state.json' and manifest.get('kind')=='center-analysis-display-tab-navigation-v1' and manifest.get('job')==job_ref and manifest.get('before')in state['observations']and state['observations'].index(manifest['before'])<=state['observations'].index(pre['before']) and manifest.get('tab_id')==tab_id and manifest.get('window_id')==b['window_id'] and manifest.get('state_path')==str(canonical/'state.json'),'execution-analysis-wait-canonical-adapter')
    need(adapter.get('manifest')==pre['manifest'] and adapter.get('phase')=='complete' and adapter.get('waiting_for') is None and adapter.get('business_progress_changed') is False and adapter.get('dates_queried') is False and adapter.get('profile_accepted') is False and not adapter.get('calls') and not adapter.get('error') and not adapter.get('last_error') and adapter.get('layout_result')=='analysis-tab-and-date-input-observed','execution-analysis-wait-adapter-complete')
    intent=adapter.get('intent',{});observations=adapter.get('observations',[]);need(intent.get('state')=='confirmed' and intent.get('key')==manifest['key'] and len(observations)>=2 and len({json.dumps(r,sort_keys=True)for r in observations})==len(observations)and intent.get('before')==observations[-2] and adapter.get('after')==pre.get('after')==observations[-1],'execution-analysis-wait-sole-navigation')
    anchor=o.doc(manifest['before']);analysis.validate(anchor,job);analysis.target(anchor['tree']);need(anchor['tab_id']==tab_id and anchor['tab']['windowId']==b['window_id']and anchor['tab']['url']==before['tab']['url'],'execution-analysis-wait-original-anchor')
    anchor_at=datetime.fromisoformat(anchor['observed_at']);previous_at=anchor_at
    for reference in observations[:-2]:
        p=Path(reference['path']);need(p.parent==canonical/'evidence'and p.suffix=='.json'and len(p.stem)==32 and all(c in '0123456789abcdef'for c in p.stem),'execution-analysis-wait-readonly-prefix-path');prior=o.doc(reference);analysis.validate(prior,job);analysis.target(prior['tree']);at=datetime.fromisoformat(prior['observed_at']);need(at.utcoffset()is not None and previous_at<=at and prior['tab_id']==tab_id and prior['tab']['windowId']==b['window_id']and prior['tab']['url']==before['tab']['url'],'execution-analysis-wait-readonly-prefix');previous_at=at
    fresh=o.doc(intent['before']);analysis.validate(fresh,job);need(anchor_at.utcoffset()is not None and anchor_at<=datetime.fromisoformat(before['observed_at'])and previous_at<=datetime.fromisoformat(fresh['observed_at']),'execution-analysis-wait-readonly-prefix-time');target=analysis.target(fresh['tree']);command={'op':'click','tabId':tab_id,'locator':{'by':'selector','value':target['selector']},'kind':'navigation'};need(intent.get('command')==command and intent.get('result',{}).get('clicked',{}).get('selector')==target['selector'] and intent['result']['clicked'].get('name')=='违规分析','execution-analysis-wait-confirmed-navigation')
    after=o.doc(pre['after']);analysis.validate(after,job);date=analysis.ready(after['tree']);need(adapter.get('date_input')=={'selector':date['selector']} and all(x['tab_id']==tab_id and x['tab']['windowId']==b['window_id'] and x['tab']['url']==before['tab']['url'] for x in (fresh,after)),'execution-analysis-wait-after-scope')
    times=[datetime.fromisoformat(x) for x in (before['observed_at'],fresh['observed_at'],intent['at'],after['observed_at'])];need(all(x.utcoffset() is not None for x in times) and times==sorted(times),'execution-analysis-wait-time-order')
    return {'job':job_ref,'before':pre['before'],'manifest':pre['manifest'],'adapter':pre['adapter_state'],'navigation':intent,'after':pre['after'],'query_phase':'open-date','business_complete':False}

def validated_dom_identity_origin(row,batch,batch_ref,ready,ready_ref,registry):
    """Fresh DOM source is identity provenance, never a platform export or a
    violation data population. Normal violation acquisition still runs later.
    """
    from ds_common import dom_command,dom_capture_data,dom_source_data,dom_original_download
    directory=Path(row['outdir']);copied=Path(row['evidence']);need(directory.is_absolute()and directory.resolve()==directory and not directory.is_symlink()and copied==directory/'dom-acquisition.json'and copied.resolve()==copied and not copied.is_symlink()and directory.parent==Path(batch_ref['path']).parent,'execution-dom-origin-path')
    copy_ref=o.ref(copied);payload=o.doc(copy_ref);receipt_path=directory/'receipt.json';need(row.get('receipt')==str(receipt_path),'execution-dom-receipt-path');matches=[r for r in ready['references']if r['path']==str(receipt_path)];need(len(matches)==1,'execution-dom-pinned-receipt');receipt_ref=matches[0];receipt=o.doc(receipt_ref);dates={k:row['date_range'][k]for k in('start','end')}
    need(receipt.get('source_kind')==row['source_kind']=='daily-visible-dom-source-v1'and payload==receipt.get('dom_source')and receipt.get('dom_capture')==row.get('dom_capture')and receipt.get('company')==row['company']and receipt.get('date_range')==dates and receipt.get('src_file')==row['source']==payload.get('source')and receipt.get('src_sha256')==payload.get('src_sha256')and receipt.get('attribution_verified')is True and receipt.get('download_verified')is False and receipt.get('source_is_authoritative_export')is False,'execution-dom-source-binding')
    company=[x for x in ready['companies']if x.get('company')==row['company']];need(len(company)==1 and company[0].get('source_kind')==row['source_kind']and company[0].get('dom_source')==payload and company[0].get('dom_capture')==row['dom_capture']and company[0].get('download_verified')is False and company[0].get('source_is_authoritative_export')is False,'execution-dom-ready-binding')
    need(payload.get('company')==row['company']and str(payload.get('groupid'))==str(row['groupid'])and payload.get('date_range')==dates and payload.get('identity')==payload.get('identity_before')==registry['company_identities'].get(str(row['groupid']))and payload['identity']['provider']==registry['provider_baseline'],'execution-dom-identity')
    checkpoints=[x for x in row.get('checkpoints',[])if x.get('stage')=='dom-acquisition-complete'];need(len(checkpoints)==1 and checkpoints[0]['counts']==receipt.get('dom_counts'),'execution-dom-count-scope')
    with dom_command():
        capture=dom_capture_data(row['dom_capture'],payload,batch,row)
        data=dom_source_data(payload,row,dates,Path(row['source']))
        original=dom_original_download(data)
    checkpoints=[x for x in row.get('checkpoints',[])if x.get('stage')=='dom-acquisition-complete'];need(len(checkpoints)==1 and checkpoints[0]['original_workflow']==original and checkpoints[0]['receipt']==payload['receipt']and checkpoints[0]['capture']==row['dom_capture']and checkpoints[0]['counts']==data['summary']and receipt['dom_counts']==data['summary'],'execution-dom-checkpoint')
    for r in(copy_ref,receipt_ref,row['dom_capture'],payload['receipt'],original,batch_ref,ready_ref):o.raw(r)
    return {'kind':'verified-daily-dom-identity-context-v1','original':row['dom_capture'],'copy':copy_ref,'daily_receipt':receipt_ref,'source_journal':original,'batch':batch_ref,'collection_ready':ready_ref,'dom_source':payload['receipt'],'download_verified':False,'source_is_authoritative_export':False,'violation_rows_reused':False,'violation_population':'new-normal-role-acquisition-required'}

def validated_acquisition_origin(row,batch,batch_ref,outbox,outbox_ref,registry,*,materials_kind="completed-outbox"):
    """Exact semantic serialization compatibility inside the verified daily parent.
    Both byte refs stay pinned; only the original role receipt is authority.
    """
    need(materials_kind in ('completed-outbox','collection-ready'),'execution-daily-material-kind')
    if materials_kind=='collection-ready':need(outbox.get('kind')=='daily-collection-ready-v1'and outbox.get('delivery_complete')is False,'execution-ready-material-kind')
    need(o.doc(batch_ref)==batch and o.doc(outbox_ref)==outbox and outbox.get('batch')==batch_ref,'execution-acquisition-parent-binding')
    need(len([r for r in batch['companies']if r==row])==1 and row.get('status')in ('complete','zero_rows'),'execution-acquisition-batch-row')
    if row.get('source_kind')=='daily-visible-dom-source-v1':
        need(materials_kind=='collection-ready','execution-dom-staged-only')
        return validated_dom_identity_origin(row,batch,batch_ref,outbox,outbox_ref,registry)
    directory=Path(row['outdir']);copied=Path(row['evidence'])
    need(directory.is_absolute()and directory.resolve()==directory and not directory.is_symlink()and copied==directory/'acquisition.json'and copied.resolve()==copied and not copied.is_symlink()and directory.parent==Path(batch_ref['path']).parent,'execution-acquisition-copy-path')
    copy_ref=o.ref(copied);value=o.doc(copy_ref);key=value.get('work_order_id','');need(type(key)is str and re.fullmatch('[0-9a-f]{64}',key)is not None,'execution-acquisition-work-order')
    original=directory/'operator'/key[:16]/'acquisition.json';need(original.resolve()==original and not original.is_symlink(),'execution-acquisition-original-path');original_ref=o.ref(original);original_value=o.doc(original_ref)
    need(value==original_value,'execution-acquisition-origin')
    receipt_path=directory/'receipt.json';need(row.get('receipt')==str(receipt_path),'execution-acquisition-receipt-path');refs=[r for r in outbox['references']if r.get('path')==str(receipt_path)];need(len(refs)==1,'execution-acquisition-pinned-receipt');receipt_ref=refs[0];receipt=o.doc(receipt_ref)
    dates={k:row['date_range'][k]for k in ('start','end')}
    need(value.get('company')==row['company']==receipt.get('company')and str(value.get('groupid'))==str(row['groupid'])and value.get('date_range')==dates==receipt.get('date_range')and value.get('source')==row.get('source')==receipt.get('src_file')and value.get('src_sha256')==receipt.get('src_sha256')and receipt.get('attribution_verified')is True,'execution-acquisition-source-binding')
    need(registry['company_identities'].get(str(value['groupid']))==value.get('identity')and value.get('identity_before')==value['identity']and value['identity'].get('provider')==registry['provider_baseline'],'execution-acquisition-identity')
    checked,raw,journal_ref=company_nav.receipt(original_ref)
    need(checked==value and raw==o.raw(original_ref)and Path(journal_ref['path'])==original.with_name('workflow.json'),'execution-acquisition-role-validation')
    # Original finalized bytes and copy formatting may differ, never their data.
    for r in (copy_ref,original_ref,receipt_ref,batch_ref,outbox_ref,journal_ref):o.raw(r)
    need(o.ref(copied)==copy_ref and o.ref(original)==original_ref,'execution-acquisition-concurrent-change')
    return {'original':original_ref,'copy':copy_ref,'daily_receipt':receipt_ref,'source_journal':journal_ref,'batch':batch_ref,**({'collection_ready':outbox_ref}if materials_kind=='collection-ready'else{'outbox':outbox_ref})}

from contextvars import ContextVar
_IDENTITY_HISTORY=ContextVar('violation_command_identity_history',default=None)
_IDENTITY_ORIGIN_INPUT=ContextVar('violation_identity_pure_input',default=None)

@contextlib.contextmanager
def identity_history_command():
    yield None

def _identity_reader_epochs(state):
    import daily_orchestration as daily
    import ds_common
    modules=(sys.modules[__name__],nav,company_nav,ds_common,state['helper'])
    result=[]
    for module in modules:
        path=Path(module.__file__);stamp=path.stat();token=(stamp.st_dev,stamp.st_ino,stamp.st_size,stamp.st_mtime_ns,stamp.st_ctime_ns)
        # Attribute identities detect in-process code replacement even when
        # file metadata did not change. The public epoch validates bytecode.
        functions=[]
        for key,value in vars(module).items():
            if isinstance(value,__import__('types').FunctionType):functions.append((key,value.__code__))
            elif isinstance(value,type)and value.__module__==module.__name__:
                functions.extend((key+'.'+n,m.__func__.__code__ if isinstance(m,(staticmethod,classmethod))else m.__code__)for n,m in vars(value).items()if isinstance(m,(__import__('types').FunctionType,staticmethod,classmethod)))
        signature=tuple(functions);cached=state['epochs'].get(module.__name__)
        if module is state['helper']:
            need(o.ref(path)==state['source']and all(getattr(vars(module).get(k),'__code__',None)is code for k,code in state['helper_code'].items()),'execution-history-helper-code-generation')
            result.append(state['source']);continue
        if cached is not None:
            # A command owns one execution generation. A changed disk epoch or
            # function cannot inherit facts obtained by the old reader.
            need(cached[:2]==(token,signature),'execution-identity-reader-generation')
        else:
            epoch=daily._ready_module_epoch(module);state['epochs'][module.__name__]=(token,signature,epoch)
        result.append(state['epochs'][module.__name__][2])
    return result

def _ready_identity_origins(report_ref,day,epochs):
    facts=_IDENTITY_ORIGIN_INPUT.get();need(facts is not None and facts['order']['day']==day,'execution-identity-history-context');ready=facts['ready'];batch=o.doc(ready['batch']);registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']};found={};origins={}
    for row in batch['companies']:
        if row.get('status')=='skipped':continue
        origin=validated_acquisition_origin(row,batch,ready['batch'],ready,facts['report']['ready'],registry,materials_kind='collection-ready');origins[row['company']]=origin;found[row['company']]=origin['original']
    return {'registry':registry,'origins':origins,'found':found}

class ProductionPorts:
    def __init__(self,tab_id,pid,*,request=None):
        need(type(tab_id) is int and tab_id>0 and type(pid) is int and pid>0,'execution-public-tab-pid-required');self.tab=tab_id;self.pid=pid;self.request=request or nav.bridge.request
    def identities(self,order):
        # Validate the actual accepted daily parent/source/client chain. The
        # report's booleans and a copied acquisition JSON are not authority.
        import daily_execution_launcher as parent
        import execution_timing as timing
        if order.get('collection_contract')=='three-flow-collection-ready-v1':return self.ready_identities(order)
        need(order.get('collection_contract')is None,'execution-collection-contract-invalid')
        report=o.doc(order['daily_completion']);p=o.doc(report['verification_parent_state'])
        if getattr(self,'reboot_continuation',None):
            from daily_completed_archive import verify_completed_archive
            archived=verify_completed_archive(report['verification_parent_state']);loaded=archived['parent'];daily=archived['order'];proof=archived['proof']
        else:
            clock=timing.Clock();loaded,daily=parent.load(Path(report['verification_parent_state']['path']),p['order'],p['archive_root'],clock);proof=parent.verify_complete(p,daily,clock)
        need(loaded==p and p['status']=='complete' and daily['day']==order['day'],'execution-daily-parent-binding');need(proof==p['completion_proof'],'execution-daily-proof-changed');batch=o.doc(proof['batch']);outbox=o.doc(proof['outbox']);found={};self.acquisition_origins={}
        # The accepted daily batch pins the full reviewed registry even when
        # one company's daily acquisition was skipped as already covered.
        self._registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']}
        for row in batch['companies']:
            if row.get('status')=='skipped':continue
            origin=validated_acquisition_origin(row,batch,proof['batch'],outbox,proof['outbox'],self._registry);self.acquisition_origins[row['company']]=origin;found[row['company']]=origin['original']
        return found
    def ready_identities(self,order):
        import daily_orchestration
        facts=daily_orchestration.verified_collection_ready_facts(order['daily_collection_ready'])
        need(facts['order']['day']==order['day'],'execution-current-daily-ready-day')
        batch=o.doc(facts['ready']['batch']);self._registry={'version':2,'provider_baseline':batch['provider_baseline'],'company_identities':batch['company_identities']};found={};self.acquisition_origins={}
        for c in facts['ready']['companies']:
            gid=str(c['groupid']);identity=self._registry['company_identities'][gid]
            need(identity['provider']==self._registry['provider_baseline'],'execution-current-provider-conflict')
            self.acquisition_origins[c['company']]={'kind':'current-daily-ready-identity-v1','daily_report':order['daily_collection_ready'],'identity':identity,'date_range':{'start':c['start'],'end':(__import__('datetime').date.fromisoformat(c['end_exclusive'])-__import__('datetime').timedelta(days=1)).isoformat()}}
            found[c['company']]=c['receipt']
        return found
    def validate_origins(self,order):
        self._company_scope_order=order
        found=self.identities(order)
        for c in order['companies']:
            initial_ledger_reference(c,order=order)
            if not c['skipped']:need(c['company'] in found,'execution-current-daily-acquisition-unavailable')
    def skipped(self,c,order=None):initial_ledger_reference(c,'execution-skipped-ledger-changed',order=order or getattr(self,'_company_scope_order',None))
    def journals(self,order,state):
        """Pure canonical candidates; director still performs semantic deep replay.
        This lets a supervisor bind a sender while batch dispatch is in flight.
        No parent timestamp or self-reported token is progress.
        """
        result=[];folder=o.location(state['order']);i=state['index']
        if i<len(order['companies']):
            base=folder/'companies'/str(i)
            for path in (base/'company-navigation/workflow.json',base/'center-navigation.json',base/'center-query.json',base/'records-query.json'):
                if path.is_file():result.append(str(path))
            a=state['companies'][i]['artifacts']
            if a.get('job'):
                path=base/'governance-detail-operations'/nav.tag(o.doc(a['job']))/'state.json'
                if path.exists():result.append(str(path))
        if state.get('delivery'):
            import execution_timing as timing
            for item in o.doc(state['delivery']['manifest'])['orders']:
                path=timing.sender_path(item['key'])
                if path.exists():
                    sender=json.loads(path.read_bytes());job=sender.get('job',{});need(job.get('key')==item['key'] and sender.get('fingerprint')==w.fingerprint(job) and job.get('target')==w.TEST_GROUP and job.get('scope')=='test','execution-live-sender-candidate-scope');result.append(str(path))
        return list(dict.fromkeys(result))
    def reboot_artifacts(self,a):
        if not getattr(self,'reboot_continuation',None) or a.get('source') is None:return a
        import violation_reboot_continuation as reboot
        value=reboot.verify(self.reboot_continuation)
        if value.get('kind')in(getattr(reboot,'TASK8_KIND',None),getattr(reboot,'W53_KIND',None),getattr(reboot,'W55_KIND',None),getattr(reboot,'W56_KIND',None),getattr(reboot,'W57_KIND',None),getattr(reboot,'W58_KIND',None),getattr(reboot,'W59_KIND',None),getattr(reboot,'W60_KIND',None),getattr(reboot,'W61_KIND',None),getattr(reboot,'W62_KIND',None),getattr(reboot,'W63_KIND',None),getattr(reboot,'W64_KIND',None),getattr(reboot,'W65_KIND',None),getattr(reboot,'W66_KIND',None),getattr(reboot,'W67_KIND',None),getattr(reboot,'W68_KIND',None),getattr(reboot,'W70_KIND',None),getattr(reboot,'W71_KIND',None)):return a
        if a['source']!=value['original']['source']:return a
        need(a['profile']==value['original']['profile'],'execution-reboot-original-profile-changed')
        current=dict(a.get('reboot_capture',{}))
        if 'frame_state' not in current:current['frame_state']={'phase':'capture','observation':value['fresh_observation']}
        return {**a,**current,'profile':value['derived_profile']}
    def reboot_context(self,ctx):
        return {**ctx,'artifacts':self.reboot_artifacts(ctx['artifacts'])} if 'artifacts' in ctx else ctx
    def guard(self,order,s):
        import director
        state=json.loads((Path(s['order']['path']).parent.parent/'state.json').read_bytes())
        need(state.get('day')==order['day'] and state.get('dispatch_id')==order['dispatch_id'] and state.get('phase')=='running' and director.current(state).get('role')==order['role'],'execution-current-acknowledged-lease-required')
        need(any(e.get('type')=='dispatched' and e.get('id')==order['dispatch_id'] for e in state.get('events',[])),'execution-ack-required')
        if s.get('reboot_continuation'):
            import violation_reboot_continuation as reboot
            import execution_timing as timing
            reboot.verify(s['reboot_continuation'],live_boot=timing.Clock().boot())
            need(s['reboot_continuation']==getattr(self,'reboot_continuation',None) and reboot.allowed_calls(s,s['reboot_continuation']),'execution-reboot-unresolved-parent')
        else:need(not any(x['state'] in ('unknown','failed') for x in s['calls']),'execution-unresolved-parent')
        for c,entry in zip(order['companies'],s['companies']):
            a=entry['artifacts'];expected=a['ledger_current'] if 'ledger_current' in a else initial_ledger_reference(c,'execution-external-ledger-change',order=order);need(o.ref(Path(c['root'])/'state.json')==expected,'execution-external-ledger-change')
            for field in ('source','job','detail_manifest','query_final','center_query_final','profile','identity_receipt'):
                if field in a:o.raw(a[field])
    def job(self,ctx):return o.doc(ctx['artifacts']['job'])
    def folder(self,ctx):p=Path(ctx['folder']);p.mkdir(parents=True,exist_ok=True);return p
    def child(self,r,*,done=False,artifacts=None,allow_wait=()):
        s=r.s
        unresolved=bool(d.unresolved_detail_calls(s)) if s.get('manifest',{}).get('kind')=='governance-detail-inspection-manifest-v1'else any(c.get('state')!='confirmed' for c in s.get('calls',[]))
        error=s.get('last_error') or s.get('error') or ('unknown-child-intent' if unresolved else None)
        wait=s.get('waiting_for')
        if s.get('hold') or s.get('settling_exhausted') or error:return {'done':False,'hold':error or wait or 'child-held','journal':o.ref(r.file)}
        if wait and wait not in allow_wait:return {'done':False,'hold':wait,'journal':o.ref(r.file)}
        return {'done':done,'artifacts':artifacts or {},'journal':o.ref(r.file)}
    def query_tick(self,ctx,center_mode):
        folder=self.folder(ctx);job=self.job(ctx);path=folder/('center-query.json' if center_mode else 'records-query.json')
        with path.with_name(path.name+'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=query.Runner(job,self.tab,path,nav.VERSION,invoke=self.request,job_ref=ctx['artifacts']['job']);r.step();r.save()
            expected='profile-required' if center_mode else 'capture-complete';done=r.s['phase']==expected
            if done and center_mode:need(r.s.get('waiting_for')=='analysis-all-reasons-actual-view-profile-required','execution-center-query-review-required')
            repair=not center_mode and r.s.get('settling_exhausted') and r.s.get('phase')=='select-end'
            if repair:
                import preselected_record_range_recovery as preselected
                # This exact existing typed contract is the only accepted
                # no-effect repair. A false predicate stops, never clears it.
                preselected.original_contract(r.s,job,ctx['artifacts']['job'],path,r.s['last_observation']['sha256'])
        if repair:
            preselected.reconcile(Path(ctx['artifacts']['job']['path']),path,nav.digest(path),r.s['last_observation']['sha256'],self.request)
            r.s=json.loads(path.read_bytes())
        fresh_wait=center_mode and r.s.get('waiting_for')=='fresh-analysis-observation-before-date'
        if fresh_wait:validate_analysis_fresh_wait(r.s,job,ctx['artifacts']['job'],path,self.tab)
        values={('center_query_final' if center_mode else 'query_final'):o.ref(path)} if done else {}
        return self.child(r,done=done,artifacts=values,allow_wait=(('fresh-analysis-observation-before-date',) if fresh_wait else ())+('confirmed-action-pending-readonly-recheck','analysis-all-reasons-actual-view-profile-required','readonly-detail-profile-and-analysis-full-distribution-required','independent-analysis-zero-and-source-verification-required'))
    def center_pages(self,ctx):
        folder=self.folder(ctx);job=self.job(ctx);file=folder/'center-pages.json'
        # Existing query reader enforces tabs/ping/tree/tabs, identity, risk,
        # versions and persisted raw observations. New pager intent below uses
        # its existing act() before a single public navigation request.
        with file.with_name(file.name+'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=query.Runner(job,self.tab,file,nav.VERSION,invoke=self.request,job_ref=ctx['artifacts']['job'])
            if r.s.get('center_pages_complete'):return self.child(r,done=True,artifacts={'center_pages':r.s['center_refs'],'center_zero':r.s.get('center_zero',False)})
            need(not any(c['state']!='confirmed' for c in r.s['calls']),'execution-center-pager-unknown');tree=r.observe();parsed=center.center_page(tree,start=job['start'],end_exclusive=job['end_exclusive'])
            refs=r.s.setdefault('center_refs',[]);pages=r.s.setdefault('center_public_pages',[])
            if parsed.get('schema')=='governance-center-analysis-zero-v1':
                need(not refs and not r.s['calls'],'execution-center-zero-after-paging');r.s.update(center_zero=True,center_pages_complete=True,center_refs=[r.s['last_observation']]);r.save();return self.child(r,done=True,artifacts={'center_pages':r.s['center_refs'],'center_zero':True})
            expected=len(pages)+1
            if parsed['page']!=expected:
                # Only a confirmed prior pager can be pending, never invent
                # a target success or issue another click.
                need(r.s['calls'] and parsed['page']==len(pages),'execution-center-page-not-expected');r.s['center_settling']=r.s.get('center_settling',0)+1;need(r.s['center_settling']<=5,'execution-center-page-settling-exhausted');r.save();return self.child(r)
            pages.append(parsed);refs.append(r.s['last_observation']);r.s.pop('needs_changed_tree',None);r.s.pop('center_settling',None)
            if parsed['next'] is None:r.s['center_pages_complete']=True;r.save();return self.child(r,done=True,artifacts={'center_pages':refs,'center_zero':False})
            r.act(parsed['next'],'observe-center-next');r.save();return self.child(r)
    def dom_plan_result(self,ctx,plan,identity_context):
        value=nav.dom_identity_context(identity_context);c=ctx['company'];need(value['company']==c['company']and value['groupid']==str(c['groupid']),'execution-DOM-plan-target')
        job=nav.prepare_dom_context(plan['path'],plan['sha256'],identity_context);jobref=o.immutable(self.folder(ctx)/'navigation-job.json',job)
        return {'done':True,'artifacts':{'plan':plan,'job':jobref,'identity_receipt':identity_context}}
    def prepare_dom_company(self,ctx,identity_context,registry):
        value=nav.dom_identity_context(identity_context);c=ctx['company'];known=o.doc(registry);need(value['company']==c['company']and value['groupid']==str(c['groupid'])and known==self._registry and known['company_identities'].get(str(c['groupid']))==value['identity'],'execution-DOM-company-target')
        out=self.folder(ctx)/'company-navigation';binding={'kind':'typed-DOM-company-navigation-v1','context':identity_context,'registry':registry,'company':c['company'],'groupid':str(c['groupid']),'dispatch':ctx['order']['dispatch_id']};key=o.digest(binding)
        job={'action':'return-company','backend':'local-dom-bridge','work_order_id':key,'work_order_path':str(out/'work-order.json'),'workflow_path':str(out/'workflow.json'),'company':c['company'],'groupid':str(c['groupid']),'identity_contract':'merchant-v2','provider_baseline':value['identity']['provider'],'identity_baseline':value['identity'],'known_company_identities':known['company_identities'],'identity_bootstrap':False,'allowed_groupids':sorted(known['company_identities']),'purpose':'dispatch-bound violation source collection','navigation_only':True,'progress_updates_enabled':False,'export_enabled':False,'send_enabled':False,'source_identity_context':identity_context,'navigation_input_snapshots':[identity_context,registry]}
        import execution_timing as timing
        job.update(timing.company_job_fields(ctx['order'].get('active_company_policy'),c['company'],str(c['groupid']),known=known['company_identities']));dates=value['date_range'];job['date_range']={**dates,'end_exclusive':( __import__('datetime').date.fromisoformat(dates['end'])+__import__('datetime').timedelta(days=1)).isoformat()}
        from role_cli import validate_job
        validate_job(job);work=o.immutable(out/'work-order.json',job);o.immutable(out/'identity-context-manifest.json',{'binding':binding,'work_order':work,'download_verified':False,'source_is_authoritative_export':False});return {'work_order_path':work['path'],'workflow_path':job['workflow_path'],'source_kind':nav.DOM_IDENTITY_KIND}
    def step(self,phase,ctx):
        if phase!='frames':ctx=self.reboot_context(ctx)
        if phase in ('seal','finish'):return getattr(self,phase)(ctx)
        if phase=='collection-seal':return self.collection_seal(ctx)
        if phase=='company-delivery':
            import current_company_delivery
            out,reference,plan=current_company_delivery.current_plan(ctx['company']['company'],ctx['order']['day'])
            return {'done':True,'company_delivery':current_company_delivery.send_plan(out,reference,plan)}
        c=ctx['company'];a=ctx['artifacts'];folder=self.folder(ctx);root=Path(c['root'])
        if phase=='plan':
            state=w.load(root);p=w.plan(state,ctx['order']['day']);need((p['company'],str(p['groupid']),p['start'],p['end_exclusive'])==(c['company'],c['groupid'],c['start'],c['end_exclusive']),'execution-role-plan-scope');receipt=self.identities(ctx['order'])[c['company']];plan=o.immutable(folder/'plan.json',p);origin=self.acquisition_origins[c['company']]
            if origin.get('kind')=='current-daily-ready-identity-v1':
                payload=origin;value={'kind':nav.DOM_IDENTITY_KIND,'company':c['company'],'groupid':str(c['groupid']),'identity':payload['identity'],'date_range':payload['date_range'],'origin':origin,'download_verified':False,'source_is_authoritative_export':False};value['identity_context_id']=__import__('hashlib').sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();context=o.immutable(folder/'navigation-identity-context.json',value);return self.dom_plan_result(ctx,plan,context)
            v=company_nav.receipt(receipt)[0];job=nav.prepare(plan['path'],plan['sha256'],receipt['path'],receipt['sha256'],v['work_order_id']);jobref=o.immutable(folder/'navigation-job.json',job)
            return {'done':True,'artifacts':{'plan':plan,'job':jobref,'identity_receipt':receipt}}
        if phase=='company':
            self.identities(ctx['order']);target=a['identity_receipt'];registry=o.immutable(folder/'company-navigation-inputs/daily-identity-registry.json',self._registry);prepared=self.prepare_dom_company(ctx,target,registry)if o.doc(target).get('kind')==nav.DOM_IDENTITY_KIND else company_nav.prepare(target,target_company=c['company'],target_groupid=c['groupid'],outdir=folder/'company-navigation',purpose='dispatch-bound violation source collection',stable_key=Path(ctx['folder']).parent.parent.name[:32]+'-'+str(ctx['order']['companies'].index(c)),registry_ref=registry,company_policy=ctx['order'].get('active_company_policy'))
            work=Path(prepared['work_order_path']);journal=Path(prepared['workflow_path'])
            # Formal Workflow owns its .bridge-execution.lock and durable calls.
            with journal.with_name('.bridge-execution.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);runner=operator.Workflow(json.loads(work.read_bytes()),self.tab,invoke=self.request)
                with contextlib.redirect_stdout(io.StringIO()):operator.run_steps(runner,journal,1,False)
            state=json.loads(journal.read_bytes());need(not state.get('error') and state.get('state')!='failed','execution-company-navigation-held')
            if state.get('waiting_for')=='company-switch-readonly-scope':
                from switch_read_recovery import verified_pending_wait
                verified_pending_wait(json.loads(work.read_bytes()),state)
                return {'done':False,'journal':o.ref(journal)}
            if state.get('waiting_for') in ('company-search-results','company-switch-result','post-switch-home-account-trigger') and not state.get('last_error') and all(x.get('state')=='confirmed' for x in state.get('calls',[])):
                return {'done':False,'journal':o.ref(journal)}
            need(not state.get('last_error') and not state.get('waiting_for') and all(x.get('state')=='confirmed' for x in state.get('calls',[])),'execution-company-navigation-unresolved')
            if state.get('state')=='complete':need(state['phase']=='done' and state['result']['identity']==self.job(ctx)['identity'] and str(state['result']['groupid'])==c['groupid'],'execution-company-final-identity');return {'done':True,'journal':o.ref(journal),'artifacts':{'company_navigation':o.ref(journal)}}
            return {'done':False,'journal':o.ref(journal)}
        if phase=='center':
            path=folder/'center-navigation.json'
            with path.with_name(path.name+'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=nav.Navigator(self.job(ctx),self.tab,path,invoke=self.request);r.tick();r.save();done=r.s['phase']=='profileRequired'
                if done:need(r.s.get('identity_verified_at'),'execution-center-entry-identity')
                return self.child(r,done=done,artifacts={'center_navigation':o.ref(path)} if done else {},allow_wait=('live-violation-analysis-date-and-pagination-profile',))
        if phase=='center-query':return self.query_tick(ctx,True)
        if phase=='center-pages':return self.center_pages(ctx)
        if phase=='records-open':
            path=folder/'records-navigation.json'
            with path.with_name(path.name+'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=discovery.Probe(self.job(ctx),self.tab,path,'records',invoke=self.request);r.step();r.save();done=r.s['phase']=='profile-required'
                if done:
                    records_entry_from_probe(r.s,self.job(ctx),self.tab)
                return self.child(r,done=done,allow_wait=('review-real-records-tree','fresh-post-action-DOM'))
        if phase=='records-query':return self.query_tick(ctx,False)
        if phase=='details':
            q=o.doc(a['query_final'])
            if not q['rows']:need(a['center_zero'] is True,'execution-center-record-count-conflict');return {'done':True}
            need(a['center_zero'] is False,'execution-analysis-zero-positive-record-conflict');m={'kind':'governance-detail-inspection-manifest-v1','inputs':{'job':a['job'],'query':a['query_final']},'tab_id':self.tab,'approved_version':nav.VERSION};dm=o.immutable(folder/'detail-manifest.json',m);d.inputs(m)
            lockpath=folder/'governance-detail-operations'/nav.tag(self.job(ctx));lockpath.mkdir(parents=True,exist_ok=True)
            with (lockpath/'.lock').open('a') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);r=d.Runner(m,invoke=self.request);r.step();r.save();done=r.s['phase']=='complete'
                if done:d.verify_completed(r.s,m,d.inputs(m))
            values={'detail_manifest':dm,'detail_state':o.ref(r.file)} if done else {}
            if not done and (r.s.get('waiting_for') or r.s.get('hold')):
                import governance_stop_loss_production as automatic
                if automatic.can_continue_owned(r):
                    need(not r.s.get('last_error') and not d.unresolved_detail_calls(r.s),'execution-auto-detail-error');return {'done':False,'artifacts':values,'journal':o.ref(r.file)}
            return self.child(r,done=done,artifacts=values,allow_wait=('readonly-state-recheck',))
        if phase=='source':
            path=folder/'source.json'
            if not o.doc(a['query_final'])['rows']:
                need(a.get('center_zero')is True and isinstance(a.get('center_pages'),list)and len(a['center_pages'])==1,'execution-zero-center-single-artifact');mr=zero.prepare(a['job']['path'],a['center_query_final']['path'],a['query_final']['path'],folder/'zero-profile.json',folder/'capture-manifest.json',center_pages=folder/'center-pages.json',center_observation=a['center_pages'][0])
            else:
                m={'kind':'governance-capture-manifest-v1','profile_revision':capture.PROFILE,'inputs':{'job':a['job'],'query':a['query_final'],'detail_manifest':a['detail_manifest'],'detail_state':a['detail_state'],'center_pages':a['center_pages']}};capture.inputs(m);mr=o.immutable(folder/'capture-manifest.json',m)
            value=capture.build(mr['path'],path);return {'done':True,'artifacts':{'source':o.ref(path),'total':value['records']['total']}}
        if phase in ('ingest','build','copy','chain','send','complete-company','ready'):
            return self.business(phase,ctx)
        if phase=='profile':
            result=profiles.prepare(a['source'],a['job'],a['query_final'],folder/'screenshot-profile.json',evidence_contract=profiles.BUSINESS)
            querydoc=o.doc(a['query_final']);schedule=[]
            for page in querydoc['pages']:
                schedule.append({'page':page['page'],'mode':'anchor','notice':None})
                schedule.extend({'page':page['page'],'mode':'rows','notice':r['notice_id']} for r in page['rows'])
            return {'done':True,'artifacts':{'profile':result['profile'],'frame_schedule':schedule,'frame_index':0,'frames':[],'frame_state':{}}}
        if phase=='frames':return self.frames(ctx)
        raise ValueError('execution-phase-unimplemented:'+phase)

    def business(self,phase,ctx):
        c=ctx['company'];a=ctx['artifacts'];root=Path(c['root']);batch=c['start']+'_'+c['end_exclusive']
        with w.lock(root):
            s=w.load(root)
            if phase=='ingest':w.ingest(root,s,a['source']['path'])
            elif phase=='build':
                if not s['batches'][batch]['artifacts']:w.build(root,s,batch)
                else:w.validate_artifact_coverage(s['batches'][batch]['artifacts'],s['batches'][batch])
            elif phase=='copy':
                b=s['batches'][batch]
                if not b['copy']:
                    return {'done':False,'handoff':{'response_kind':'violation-copy-response-v1','root':str(root),'batch':batch,'source':a['source'],'ledger':o.ref(root/'state.json'),'copy_order':w.copy_order(s,batch),'requirements':'Return {request,kind,copy:{path,sha256}}. Existing set_copy validates full original IDs/source. Supply reviewed agent wording or the exact deterministic public-template contract; never assert human review for program output.'}}
                for ref in (b['copy'],b['copy_evidence'],*b['copy_parts']):w.verify(ref)
            elif phase=='chain':
                out=self.folder(ctx)/'screenshot-chain.json'
                if out.exists():
                    manifest=o.doc(o.ref(out));src=o.doc(a['source']);region.validate_chain(manifest,source=a['source'],company=c['company'],groupid=c['groupid'],start=c['start'],end_exclusive=c['end_exclusive'],notice_ids=[r['notice_id'] for r in src['records']['rows']])
                else:region.assemble(a['source'],[r['path'] for r in a['frames']],out)
                if not any(x['manifest']==o.ref(out) for x in s['batches'][batch].get('screenshot_chains',[])):w.add_screenshot_chain(root,s,batch,out)
            elif phase=='send':
                source=capture.validate(a['source']['path'])
                delivery=o.doc(a['delivery_manifest']);_zero_notice_module(delivery['zero_module_ref'])if delivery.get('zero_result_contract')=='notify-confirmed-zero-v1'else None;expected=next(x for x in delivery['companies'] if x['company']==c['company'])
                if s['batches'][batch]['total']==0:
                    b=s['batches'][batch]
                    need(type(b['total'])is int and b['status']=='zero_verified' and b['send_jobs']=={} and b['analysis']==b['records']==[] and b['artifacts']is None and b['copy']is None and b['copy_evidence']is None and b['copy_parts']==b['screenshots']==[] and b.get('screenshot_chains',[])==[],'execution-zero-send-batch-conflict')
                    if b['source']['sha256']==a['source']['sha256']:
                        need(s['company']==source['company']==c['company'] and s['groupid']==source['groupid']==c['groupid'] and b['start']==source['start']==c['start'] and b['end_exclusive']==source['end_exclusive']==c['end_exclusive'] and source['analysis']['total']==source['records']['total']==0 and source['analysis']['rows']==source['records']['rows']==[] and o.raw(b['source'])==o.raw(a['source']) and b['input_fingerprint']==w.fingerprint(source),'execution-zero-send-source-ledger-conflict')
                    else:
                        # Supervised zero-recapture adoption (B35): the sealed
                        # batch keeps its original authoritative source and
                        # binding fingerprint; the fresh validated capture must
                        # agree on company, groupid, scope and verified zero.
                        # The fresh capture stays the delivery's own source ref.
                        o.raw(b['source']);need(b['input_fingerprint']==w.fingerprint(o.doc(b['source'])) and w.zero_recapture_aligned(s,b,source),'execution-zero-send-source-ledger-conflict')
                    need(delivery['scope_sha256']==ctx['order']['scope_sha256'] and len([x for x in delivery['companies'] if x['company']==c['company']])==1 and expected['batch']==batch and expected['source']==a['source'] and len(expected['orders'])==1 and expected['orders'][0].get('part')=='zero-result','execution-zero-send-sealed-orders-conflict')
                    zn=_zero_notice_module()
                    zn.job(expected['orders'][0])
                for ref in expected['dependencies']:
                    import violation_reboot_continuation as reboot
                    reboot._sealed_delivery_dependency(ref,a['delivery_manifest'])
                # Existing batch dispatch validates an immutable in-process
                # context, same canonical sender keys, timeout receipt checks.
                if not s['batches'][batch]['total']:
                    r=zn.send(Path(expected['orders'][0]['text_file']).parent,expected['orders'][0]);a['zero_result_notification']=r
                if s['batches'][batch]['total']!=0:w.dispatch(root,s,batch,sealed_orders=expected['orders'])
            elif phase=='complete-company':
                notice=None
                if not s['batches'][batch]['total']:
                    sealed=o.doc(a['delivery_manifest']);_zero_notice_module(sealed['zero_module_ref']);native=next(x for x in sealed['companies']if x['company']==c['company'])['orders'][0]
                    zn=_zero_notice_module()
                    need(a.get('zero_result_notification')is not None,'execution-zero-notification-required-before-cursor');receipt=zn.client(native,a['zero_result_notification']);notice={'order':native,'client':receipt}
                w.complete(root,s,batch,zero_notice=notice)
            elif phase!='ready':raise ValueError('execution-business-phase-unimplemented')
            current=o.ref(root/'state.json');values={'batch':batch,'ledger_current':current}
            if phase=='send'and a.get('zero_result_notification'):values['zero_result_notification']=a['zero_result_notification']
            if phase=='chain':values['chain']=o.ref(self.folder(ctx)/'screenshot-chain.json')
            return {'done':True,'artifacts':values,'journal':current}

    def accept(self,request,response):
        root=Path(request['root']) if 'root' in request else None
        if request['response_kind']=='violation-copy-response-v1':
            need(set(response)=={'request','kind','copy'},'execution-copy-response-fields');o.raw(request['source']);o.raw(response['copy'])
            with w.lock(root):
                need(o.ref(root/'state.json')==request['ledger'],'execution-copy-ledger-changed');s=w.load(root);w.set_copy(root,s,request['batch'],response['copy']['path']);return {'ledger_current':o.ref(root/'state.json')}
        need(request['response_kind']=='violation-frame-qa-response-v1' and set(response)=={'request','kind','attestation'},'execution-qa-response-fields')
        o.raw(request['preview']);att=o.doc(response['attestation']);need(att.get('registration_preview')==request['preview'],'execution-qa-preview-binding')
        preview=Path(request['preview']['path']);final=preview.with_name('registration.json')
        if final.exists():
            value=o.doc(o.ref(final));region.validate_frame(value['image']['path'],value,source=request['source']);need(value.get('quality_attestation')==response['attestation'],'execution-qa-already-applied-different-proof')
        else:region.approve_preview(preview,response['attestation'])
        return {}

    def verify_accept(self,request,response,updates):
        """Only an already durable exact accept result; never invoke a writer."""
        if request['response_kind']=='violation-copy-response-v1':
            need(set(updates)=={'ledger_current'},'execution-copy-accept-result-fields');o.raw(updates['ledger_current']);s=w.load(Path(request['root']));b=s['batches'][request['batch']];o.raw(response['copy']);need(b['copy_evidence']['sha256']==response['copy']['sha256'],'execution-copy-accepted-evidence-changed')
            for r in (b['source'],b['copy'],b['copy_evidence'],*b['copy_parts']):w.verify(r)
            return
        need(request['response_kind']=='violation-frame-qa-response-v1' and updates=={},'execution-qa-accept-result-fields');final=Path(request['preview']['path']).with_name('registration.json');value=o.doc(o.ref(final));need(value.get('quality_attestation')==response['attestation'],'execution-qa-accepted-proof-changed');region.validate_frame(value['image']['path'],value,source=request['source'])

    def identity_navigation_reuse(self,path,navigation_ref,observation,raw,state,save):
        """Snapshot current evidence, preserving earlier refs and all input keys."""
        need(not state['calls'] and state['state'] in ('preflight','complete'),'execution-identity-reuse-input-pending')
        need(o.doc(observation)==raw,'execution-identity-reuse-observation-changed');blob=o.raw(navigation_ref);navigation=json.loads(blob)
        need(navigation.get('last_observation')==observation and navigation.get('observations',[])[-1:]==[observation] and all(v.get('state')=='complete'for v in navigation.get('operations',[])),'execution-identity-reuse-navigation-changed')
        def publish(target,value):
            if target.exists():
                reference=o.ref(target);need(o.raw(reference)==o.encode(value),'execution-immutable-conflict');return reference
            return o.immutable(target,value)
        snapshot_value={'kind':'identity-display-navigation-byte-snapshot-v1','origin':navigation_ref,'raw_hex':blob.hex()}
        snapshot=publish(path.parent/(path.stem+'-navigation-snapshot-'+navigation_ref['sha256']+'.json'),snapshot_value)
        value={'kind':'saved-navigation-identity-display-precheck-only-v2','navigation':snapshot,'navigation_origin':navigation_ref,'observation':observation,'raw':raw,'requires_original_live_capture_and_navigation_guards':True}
        reused=publish(path.parent/(path.stem+'-reused-navigation-'+o.digest(value)+'.json'),value)
        need(o.ref(Path(navigation_ref['path']))==navigation_ref,'execution-identity-reuse-navigation-changed');o.raw(observation)
        if state.get('state')=='complete' and state.get('after')==reused and state.get('reused_navigation')==reused:return o.ref(path)
        if state.get('after') and state['after']!=reused:
            history=state.setdefault('after_history',[])
            if state['after']not in history:history.append(state['after'])
        state.update(state='complete',after=reused,reused_navigation=reused);save();return o.ref(path)

    def ensure_screenshot_full_identity(self,source,profile,observation,chain,folder,out,key,*,fresh_observation=None,fresh_navigation=None):
        """One source/phase-bound public provider hover; unknown is read-only."""
        import screenshot_identity
        if o.doc(profile)['derivation'].get('kind')=='governance-records-reboot-derived-profile-v1':
            folder=Path(o.doc(profile)['derivation']['reboot_continuation']['path']).parent
        selection=folder/'screenshot-selection-identity.json'
        if selection.exists():anchor=o.ref(selection);screenshot_identity.validate(anchor,source,profile,chain_id=chain,pid=self.pid)
        else:anchor=o.immutable(selection,screenshot_identity.create(source,profile,observation,chain_id=chain,pid=self.pid))
        a=o.doc(anchor);binding={'source':source,'profile':profile,'identity':anchor,'chain_id':chain,'pid':self.pid,'tab_id':self.tab,'window_id':a['window_id'],'key':key};path=out/'identity-display'/(__import__('hashlib').sha256(key.encode()).hexdigest()+'.json')
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            state=o.doc(o.ref(path)) if path.exists() else {'kind':'source-bound-screenshot-full-identity-display-v1','binding':binding,'phase':'display-identity','state':'preflight','calls':[],'observations':[],'read_attempts':0}
            need(state.get('kind')=='source-bound-screenshot-full-identity-display-v1' and type(state.get('read_attempts')) is int and 0<=state['read_attempts']<=3 and state['binding']==binding and state['state'] in ('preflight','unknown','complete') and len(state['calls'])<=1,'execution-identity-display-binding');need(state['state']!='unknown' or state['calls'],'execution-identity-display-unknown-without-intent')
            def save():
                if state['state']!='complete' and any(c.get('state')=='unknown'for c in state['calls']):state['state']='unknown'
                engine.atomic(path,state)
            def sample():
                need(state['read_attempts']<3,'execution-identity-display-read-budget-exhausted');read_index=state['read_attempts'];state['read_attempts']+=1;save();record={'at':nav.stamp(),'commands':[]}
                def read(command):
                    reply=self.request(command);record['commands'].append({'command':command,'reply':reply});o.immutable(path.parent/(path.stem+'-read-'+str(read_index)+'-'+str(len(record['commands']))+'.json'),record);need(reply.get('ok') is True,'execution-identity-display-read-failed');return reply['result']
                before_all=read({'op':'tabs'});before=nav.context(before_all,self.tab,a['groupid']);ping=read({'op':'ping','tabId':self.tab});need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only','execution-identity-display-version');tree=read({'op':'tree','tabId':self.tab});after_all=read({'op':'tabs'});after=nav.context(after_all,self.tab,a['groupid']);need(before['url']==after['url'] and before['windowId']==after['windowId']==a['window_id'],'execution-identity-display-window-route');raw={'source':'local-dom-bridge','observed_at':nav.stamp(),'tab_id':self.tab,'tab':after,'tree':tree};screenshot_identity.current(anchor,source,profile,raw);record['raw']=raw;record['input_scope_ready']=all(tab.get('active') is True and len([w for w in windows if w.get('windowId')==a['window_id']])==1 for windows,tab in ((before_all,before),(after_all,after)));reference=o.immutable(path.parent/(path.stem+'-observation-'+str(len(state['observations']))+'.json'),record);state['observations'].append(reference);save();cards=[n for n in nav.nodes(tree)if 'UserCard-index-module__outer--'in n.get('attributes',{}).get('class','')]
                if cards:nav.identity(tree,a['identity']);return raw,True
                return raw,False
            navigation_path=Path(source['path']).parent/'.records-region-navigation'/source['sha256']/'state.json'
            if o.doc(profile)['derivation'].get('kind')=='governance-records-reboot-derived-profile-v1':
                import violation_reboot_profile as reboot_profile
                navigation_path=reboot_profile.nav_root(o.doc(profile),source)/'state.json'
            navigation_ref=o.ref(navigation_path);navigation=o.doc(navigation_ref);profile_value=o.doc(profile);meta=profile_value['derivation'];need(navigation['binding']=={'schema':screenshot_nav.SCHEMA,'source':source,'profile':profile,'job':meta['job'],'query':meta['query'],'tab_id':self.tab,'window_id':a['window_id']} and all(x['state']=='complete'for x in navigation['operations']),'execution-identity-display-navigation-unresolved')
            # This only avoids an eager display read. Original live navigation
            # and capture guards must still prove their own current full card.
            stale_checkpoint=fresh_navigation is not None and fresh_navigation!=navigation_ref
            raw,ready=sample()
            if ready:state.update(state='complete',after=state['observations'][-1]);save();return o.ref(path)
            need(not state['calls'],'execution-identity-display-prior-input-readonly-hold');need(not stale_checkpoint,'execution-identity-display-stale-navigation-no-hover');need(o.doc(state['observations'][-1])['input_scope_ready'],'execution-identity-display-hover-active-scope-required');target=nav.exact(raw['tree'],a['identity']['provider']);command={'op':'hover','tabId':self.tab,'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
            class Once:
                s=state
                def save(inner):save()
                def call(inner,c):
                    reply=self.request(c);state['hover_reply']=reply;save();need(reply.get('ok') is True,'execution-identity-display-hover-failed');result=reply['result'];need(result.get('kind')=='navigation' and all(result.get('hovered',{}).get(k)==target.get(k)for k in ('selector','tag','name')),'execution-identity-display-hover-reply');return result
            operator.Workflow.once(Once(),command,intent_key=key)
            while state['read_attempts']<3:
                raw,ready=sample()
                if ready:state.update(state='complete',after=state['observations'][-1]);save();return o.ref(path)
            raise ValueError('execution-identity-display-read-budget-exhausted')

    def capture_focus_location(self,binding,observation,out,environment_restoration=None):
        """New exact URL gets a reviewed environment-bound focus epoch only."""
        out=Path(out);original_path=out/'capture-focus.json'
        if not original_path.exists():return original_path,None
        previous=o.ref(original_path);old=o.doc(previous)
        if old.get('binding')==binding:return original_path,None
        need(old.get('kind')=='violation-frame-focus-v1' and type(old.get('events'))is list and type(old.get('reads'))is list and old['reads'],'execution-focus-url-original-shape')
        need(set(old['binding'])==set(binding) and {k:v for k,v in old['binding'].items()if k!='url'}=={k:v for k,v in binding.items()if k!='url'},'execution-focus-url-stable-binding-changed')
        need(all(e.get('state')=='complete' and all(c.get('state')=='confirmed'for c in e.get('calls',[])) and (not e.get('native_focus')or e['native_focus'].get('state')=='complete') for e in old['events']),'execution-focus-url-prior-unknown')
        need(environment_restoration is not None,'execution-focus-url-restoration-required')
        import violation_reboot_continuation as reboot
        restoration=o.doc(environment_restoration);verified=reboot.verify_environment(environment_restoration,restoration['grant']);need(verified==restoration,'execution-focus-url-restoration-changed')
        meta=o.doc(binding['profile'])['derivation'];scope=restoration['scope'];activation=restoration['binding']['activation']
        need(restoration['binding']['source']==binding['source'] and restoration['binding']['job']==meta['job'] and restoration['original_refs']['profile']==meta['original_profile'] and meta['source']==binding['source'] and activation==getattr(self,'reboot_continuation',None) and o.doc(activation)['admission']==meta['reboot_continuation'] and scope=={'pid':binding['pid'],'tab_id':binding['tab_id'],'window_id':binding['window_id']},'execution-focus-url-restored-scope')
        restored=o.doc(restoration['observation']);raw=o.doc(observation);need(raw['tab']['url']==restored['tab']['url']==binding['url'] and all(raw['tab'][k]==restored['tab'][k]==binding[v]for k,v in (('tabId','tab_id'),('windowId','window_id'))),'execution-focus-url-current-observation')
        job=o.doc(meta['job']);query=o.doc(meta['query']);nav.identity(raw['tree'],job['identity']);need(d.normal_page(raw['tree'],job,query)==restoration['page'],'execution-focus-url-current-page-facts')
        from urllib.parse import parse_qsl
        left=urlsplit(old['binding']['url']);right=urlsplit(binding['url']);lq=parse_qsl(left.query,keep_blank_values=True);rq=parse_qsl(right.query,keep_blank_values=True);ld=dict(lq);rd=dict(rq)
        need(left.scheme==right.scheme=='https' and left.netloc==right.netloc=='life.douyin.com' and left.path==right.path==g.RECORDS and not left.fragment and not right.fragment and len(ld)==len(lq) and len(rd)==len(rq) and all(rd.get(k)==v for k,v in ld.items()) and set(rd)-set(ld)=={'StartTime','EndTime','enter_from'} and rd['enter_from']=='home_violation_center' and rd.get('groupid')==str(job['groupid']) and rd['StartTime'].isdigit() and rd['EndTime'].isdigit() and int(rd['StartTime'])<int(rd['EndTime']),'execution-focus-url-query-transition')
        # URL timestamps are observed route metadata, never substituted for the
        # exact source/job date range proved by normal_page above.
        for ref in old['reads']:o.raw(ref)
        need(o.ref(original_path)==previous,'execution-focus-url-prior-concurrent-change')
        authority={'kind':'source-bound-environment-focus-url-revision-v1','previous':previous,'environment':environment_restoration,'observation':restoration['observation'],'original_binding':old['binding']}
        path=out/'capture-focus-revisions'/o.digest(binding)/'capture-focus.json'
        if path.exists():
            epoch=o.doc(o.ref(path));need(epoch.get('kind')=='violation-frame-focus-v1' and epoch.get('binding')==binding and epoch.get('revision_authority')==authority and type(epoch.get('events'))is list and type(epoch.get('reads'))is list and epoch['reads'] and all(e.get('state')=='complete' and all(c.get('state')=='confirmed'for c in e.get('calls',[])) and (not e.get('native_focus')or e['native_focus'].get('state')=='complete')for e in epoch['events']),'execution-focus-url-existing-epoch-unresolved')
            for ref in epoch['reads']:o.raw(ref)
        else:
            need(not screenshot_nav.pending_frames(binding['source']) and not any((out/name).exists()for name in ('preview-registration.json','registration.json','region-frame.json','raw-window.png','raw-window.png.json')),'execution-focus-url-native-or-QA-pending')
        return path,authority

    def ensure_capture_focus(self,source,observation,profile,chain,out,environment_restoration=None,*,allow_input=True):
        """Fresh AX+CG authority before the unchanged strict viewport proof."""
        public_binding={'pid':self.pid,'scope':{'tabId':self.tab,'windowId':o.doc(profile)['derivation']['window_id']},'url':o.doc(observation)['tab']['url']}
        src=o.doc(source);meta=o.doc(profile)['derivation'];raw=o.doc(observation);tab=raw['tab'];window=meta['window_id']
        need(meta['tab_id']==self.tab and tab['tabId']==self.tab and tab['windowId']==window and str(tab.get('groupid',src['groupid']))==str(src['groupid']),'execution-capture-focus-original-scope')
        url=tab['url'];u=urlsplit(url);need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path==g.RECORDS and __import__('urllib.parse',fromlist=['parse_qs']).parse_qs(u.query).get('groupid')==[str(src['groupid'])],'execution-capture-focus-records-route')
        binding={'source':source,'profile':profile,'chain':chain,'pid':self.pid,'tab_id':self.tab,'window_id':window,'url':url};path,authority=self.capture_focus_location(binding,observation,out,environment_restoration);path.parent.mkdir(parents=True,exist_ok=True)
        with path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            state=o.doc(o.ref(path))if path.exists()else {'kind':'violation-frame-focus-v1','binding':binding,'events':[],'reads':[],**({'revision_authority':authority}if authority else {})}
            need(state.get('kind')=='violation-frame-focus-v1' and state['binding']==binding and state.get('revision_authority')==authority,'execution-capture-focus-binding-changed')
            def save():engine.atomic(path,state)
            def sample(label,event=None):
                o.raw(source);o.raw(profile);reply=self.request({'op':'tabs'});rr=o.immutable(path.parent/'capture-focus-reads'/(str(len(state['reads'])).zfill(4)+'-'+label+'.json'),{'command':{'op':'tabs'},'reply':reply,'response':reply,'observed_at':nav.stamp()})
                state['reads'].append(rr)
                if event is not None:event.setdefault('reads',[]).append(rr)
                save()
                need(reply.get('ok')is True,'execution-capture-focus-tabs-failed');windows=reply['result'];hits=[(w,t)for w in windows for t in w.get('tabs',[])if t.get('tabId')==self.tab];need(len(hits)==1,'execution-capture-focus-tab-not-unique');w,t=hits[0]
                need(w.get('windowId')==t.get('windowId')==window and t.get('url')==url and t.get('allowed')is True and type(t.get('active'))is bool and type(w.get('focused'))is bool and sum(x.get('focused')is True for x in windows)<=1,'execution-capture-focus-current-scope')
                need(len([x for x in w['tabs']if x.get('active')is True])==1,'execution-capture-focus-active-ambiguous');
                front={**front_identity(self.pid),'tabs':windows,'tabs_reply':rr,'observed_at':nav.stamp()}
                frontref=o.immutable(path.parent/'capture-focus-reads'/(str(len(state['reads'])).zfill(4)+'-'+label+'-public.json'),front);state['reads'].append(frontref);save()
                need(front['application']=={'pid':self.pid,'bundle':'com.google.Chrome','terminated':False} and front.get('frontmost_source')==FRONT_SOURCE,'execution-capture-focus-public-app')
                owner=public_frontmost(front,self.pid);need(owner==front.get('frontmost_pid'),'execution-capture-focus-public-authority')
                return t['active']and w['focused']and owner==self.pid,frontref
            # A durable fully-ready native completion can seal its outer event
            # after a crash; subsequent genuine loss gets a new ordinal.
            for completed in state['events']:
                native=completed.get('native_focus')
                if completed['state']!='complete' and native and native.get('state')=='complete' and all(c.get('state')=='confirmed' for c in completed['calls']):
                    after=o.doc(native['after']);hits=[(w,t) for w in after['tabs'] for t in w.get('tabs',[]) if t.get('tabId')==self.tab]
                    need(native['binding']==binding and len(hits)==1 and hits[0][0].get('windowId')==hits[0][1].get('windowId')==window and hits[0][1].get('url')==url,'execution-capture-focus-native-completion-binding')
                    if public_frontmost(after,self.pid)==self.pid and hits[0][1].get('active')is True and hits[0][0].get('focused')is True:
                        completed.update(state='complete',completed_at=native['completed_at'],outcome='sealed-native-completion');save()
            previous=state['events'][-1]if state['events']else None
            # Every call samples current state; completed events are not live facts.
            ready,read=sample('before',previous)
            if previous and previous['state']!='complete':
                need(previous['state']in('unknown','confirmed') and (len(previous['calls'])==1 or previous.get('native_focus')),'execution-capture-focus-event-state');need(ready,'execution-capture-focus-unknown-no-replay');
                if previous.get('native_focus'):previous['native_focus'].update(state='complete',after=read,completed_at=nav.stamp())
                previous.update(state='complete',reconciled_readonly=read,completed_at=nav.stamp());save();return {'input_attempted':False,'refresh_observation':True,'journal':o.ref(path),'fresh_capture_proof_required':True}
            if ready:return {'input_attempted':False,'journal':o.ref(path)if path.exists()else None,'fresh_capture_proof_required':True}
            need(not screenshot_nav.pending_frames(source) and not any((out/name).exists()for name in ('preview-registration.json','registration.json','region-frame.json','raw-window.png','raw-window.png.json')),'execution-capture-focus-native-or-QA-pending-no-input')
            need(allow_input,'execution-preintent-marker-focus-changed-no-input')
            event={'state':'unknown','phase':'capture-focus','revision':len(state['events']),'calls':[],'reads':[read]};state['events'].append(event);save()
            def native_once(current):
                observed=o.doc(current)
                if public_frontmost(observed,self.pid)==self.pid:return False
                target=next(t for w in observed['tabs'] for t in w.get('tabs',[]) if t.get('tabId')==self.tab)
                if target.get('active') is not True:return False
                need(not event.get('native_focus') and capture_native_admission(observed,public_binding),'execution-capture-focus-native-admission')
                native={'state':'unknown','action':'activate-existing-Chrome-PID-only','binding':binding,'before':current,'intent_at':nav.stamp()};event['native_focus']=native;save()
                try:result=activate_original_chrome(self.pid)
                except Exception as error:
                    native['exception']={'type':type(error).__name__,'message':str(error)};save();raise
                native['result']=result;save();need(result.get('pid')==self.pid and result.get('bundle')=='com.google.Chrome' and result.get('request_accepted')is True and result.get('launch_used')is False,'execution-capture-focus-native-result')
                return True
            def await_native(event):
                started=time.monotonic()
                for count in range(3):
                    current,current_ref=sample('after-native',event)
                    if public_frontmost(o.doc(current_ref),self.pid)==self.pid:
                        event['native_focus'].update(state='complete',after=current_ref,completed_at=nav.stamp());save();return current,current_ref
                    if time.monotonic()-started>=2:break
                    if count<2:time.sleep(.05)
                raise ValueError('execution-capture-focus-native-effect-unverified-no-replay')
            native_input=native_once(read)
            if native_input:ready,read=await_native(event)
            if ready:event.update(state='complete',completed_at=nav.stamp());save();return {'input_attempted':True,'journal':o.ref(path),'fresh_capture_proof_required':True}
            class Once:
                s=event
                def save(inner):save()
                def call(inner,command):
                    need(command=={'op':'activate','tabId':self.tab},'execution-capture-focus-only-original-tab');reply=self.request(command);event['reply']=reply;save();need(reply.get('ok')is True,'execution-capture-focus-activate-failed');result=reply['result'];need(all(result.get(k)==v for k,v in {'tabId':self.tab,'windowId':window,'url':url,'active':True,'windowFocused':True}.items()),'execution-capture-focus-result-scope');return result
            operator.Workflow.once(Once(),{'op':'activate','tabId':self.tab},intent_key='original-frame-focus-'+str(event['revision']));event['state']='confirmed';save();ready,read=sample('after',event)
            if not ready and native_once(read):
                ready,read=await_native(event)
            need(ready,'execution-capture-focus-effect-unverified');event.update(state='complete',completed_at=nav.stamp());save();return {'input_attempted':True,'journal':o.ref(path),'fresh_capture_proof_required':True}

    def capture_frame_started(self,source,out,key):
        out=Path(out);base=Path(source['path']).resolve().parent
        chain=key.rsplit(':',1)[0]
        path=base/'.native-region-frame-state'/(region.fc.fingerprint([source['sha256'],chain])+'.json')
        if path.exists():
            journal=o.doc(o.ref(path));need(journal.get('scope',{}).get('source_sha256')==source['sha256'],'execution-current-frame-source')
            frame=next((f for f in journal.get('frames',[])if f.get('operation',{}).get('key')==key),None)
            if frame is not None:return True
        return any((out/name).exists()for name in ('preview-registration.json','registration.json','region-frame.json','raw-window.png.json','raw-window.png'))

    def fresh_preintent_capture_state(self,reader,state,source,profile,out,key):
        """Commit one preintent observation first; a later strict proof authorizes capture."""
        out=Path(out);need(out.is_absolute() and out.resolve()==out,'execution-preintent-canonical-out');base=Path(source['path']).resolve().parent
        binding={'source':source,'profile':profile,'key':key,'outdir':str(out)};marker=state.get('preintent_observation_refresh')
        if marker is not None:
            need(set(marker)=={'kind','binding','before','fresh','journal'} and marker['kind']=='source-bound-frame-preintent-observation-v1' and marker['binding']==binding and state['observation']==marker['fresh'] and state['navigation_checkpoint']==marker['journal'],'execution-preintent-refresh-binding-changed')
            before=o.doc(marker['before']);fresh=o.doc(marker['fresh']);o.raw(marker['journal'])
            need(before.get('tab_id')==fresh.get('tab_id')==self.tab and all(fresh['tab'].get(k)==before['tab'].get(k)for k in ('tabId','windowId','url')),'execution-preintent-scope-changed')
            need(reader.normal(fresh)==reader.normal(before),'execution-preintent-source-page-changed')
        started=self.capture_frame_started(source,out,key)
        if marker is not None or started:
            return state,None  # Existing capture/QA never receives a new observation.
        old_ref=state['observation'];old=o.doc(old_ref);current=reader.run('observe');need(current.get('ok') is True and current.get('status')=='observed','execution-preintent-observation-not-ready');fresh=o.doc(current['observation'])
        need(old.get('tab_id')==fresh.get('tab_id')==self.tab and all(fresh['tab'].get(k)==old['tab'].get(k)for k in ('tabId','windowId','url')),'execution-preintent-scope-changed')
        need(reader.normal(fresh)==reader.normal(old),'execution-preintent-source-page-changed')
        state.update(observation=current['observation'],navigation_checkpoint=current['journal'],preintent_observation_refresh={'kind':'source-bound-frame-preintent-observation-v1','binding':binding,'before':old_ref,'fresh':current['observation'],'journal':current['journal']})
        return state,current['journal']

    def capture_identity_anchor(self,source,observation,profile,chain,folder,out,mode):
        import screenshot_identity
        if o.doc(profile)['derivation'].get('kind')=='governance-records-reboot-derived-profile-v1':
            folder=Path(o.doc(profile)['derivation']['reboot_continuation']['path']).parent
        if mode!='anchor':return None
        path=folder/'screenshot-identity.json'
        selection=folder/'screenshot-selection-identity.json'
        if selection.exists():selection_ref=o.ref(selection);screenshot_identity.validate(selection_ref,source,profile,chain_id=chain,pid=self.pid)
        else:selection_ref=o.immutable(selection,screenshot_identity.create(source,profile,observation,chain_id=chain,pid=self.pid))
        inputs=region.fc.page_inputs(source,observation,profile,screenshot_anchor=selection_ref);reply=self.request(inputs['command']);record={'kind':'readonly-business-anchor-contract-selection-v1','source':source,'observation':observation,'profile':profile,'chain_id':chain,'pid':self.pid,'command':inputs['command'],'reply':reply,'selection_identity':selection_ref,'observed_at':nav.stamp()};o.immutable(out/'contract-selection'/(__import__('hashlib').sha256(json.dumps(record,ensure_ascii=False,sort_keys=True).encode()).hexdigest()+'.json'),record);need(reply.get('ok') is True,'execution-anchor-contract-proof-failed');base=reply['result'];region.business.validate_base(base,inputs)
        if base['business_date']['geometry']['evidence_eligible'] is True:
            if base['public_identity'].get('visible_card') is None:self.ensure_screenshot_full_identity(source,profile,observation,chain,folder,out,chain+':'+out.name+':full-date-identity')
            return None
        need(region.program_region_quality.fragment_date_geometry(base) and all(h['geometry']['evidence_eligible'] is True for h in base['business_headers']),'execution-anchor-contract-unreviewed-date-or-headers')
        if path.exists():
            reference=o.ref(path);screenshot_identity.validate(reference,source,profile,chain_id=chain,pid=self.pid);return reference
        return o.immutable(path,screenshot_identity.create(source,profile,observation,chain_id=chain,pid=self.pid))

    def frames(self,ctx):
        original=ctx['artifacts'];effective=self.reboot_context(ctx)
        value=self._frames(effective)
        if effective['artifacts'] is not original and 'artifacts' in value:
            updates=value['artifacts'];nested={**original.get('reboot_capture',{})}
            for k in ('frame_state','frame_index','frames'):
                if k in updates:nested[k]=updates[k]
            value={**value,'artifacts':{**{k:v for k,v in updates.items() if k not in ('frame_state','frame_index','frames')},'reboot_capture':nested}}
        return value
    def completed_capture_frame(self,source,observation,profile,chain,out,mode,key):
        """Pure exact owner/operation consumption before any live focus work."""
        path=Path(source['path']).resolve().parent/'.native-region-frame-state'/(region.fc.fingerprint([source['sha256'],chain])+'.json')
        if not path.exists():return None
        owner_ref=o.ref(path);owner=o.doc(owner_ref);need(owner.get('scope')=={'source_sha256':source['sha256'],'profile_sha256':profile['sha256'],'chain_id':chain},'execution-completed-frame-owner-scope')
        entries=[e for e in owner['frames'] if e['operation']['key']==key or e['operation']['outdir']==str(out.resolve())]
        if not entries:return None
        need(len(entries)==1,'execution-completed-frame-operation-ambiguous');entry=entries[0]
        if entry.get('state')!='complete':return None
        metadata=entry['registration'];need(metadata.get('path')==str(out.resolve()/'registration.json'),'execution-completed-frame-registration-path');m=o.doc(metadata);anchor=m.get('pinned_inputs',{}).get('screenshot_anchor')
        operation={'source':source,'observation':observation,'profile':profile,'pid':self.pid,'mode':mode,'key':key,'outdir':str(out.resolve()),'revision':region.capture_revision(profile),'replaces':None}
        if mode=='rows':operation['uncovered_only']=True
        if anchor is not None:operation['screenshot_anchor']=anchor
        need(entry['operation']==operation and m.get('state')=='complete' and m.get('chain_id')==chain and m.get('frame_mode')==mode and m.get('native_pid')==self.pid,'execution-completed-frame-operation-changed')
        b=m['pinned_inputs'];need({'path':b['source_path'],'sha256':b['source_sha256']}==source and {'path':b['observation_path'],'sha256':b['observation_sha256']}==observation and {'path':b['profile_path'],'sha256':b['profile_sha256']}==profile,'execution-completed-frame-inputs-changed')
        need(m.get('source_sha256')==source['sha256'],'execution-completed-frame-current-source');o.raw({k:m['image'][k]for k in('path','sha256')});checked={'notice_ids':m['notice_ids']};need(o.ref(path)==owner_ref,'execution-completed-frame-owner-changed');o.raw(metadata)
        return metadata,checked

    def _frames(self,ctx):
        a=ctx['artifacts'];schedule=a['frame_schedule'];frames=a['frames'];cursor=a['frame_index'];folder=self.folder(ctx)
        if cursor>=len(schedule):return {'done':True}
        task=schedule[cursor];source=a['source'];profile=a['profile'];covered=set()
        for r in frames:
            m=o.doc(r);need(m.get('state')=='complete' and m.get('source_sha256')==source['sha256'],'execution-current-approved-frame-required');covered.update(m['notice_ids'])
        if task['mode']=='rows' and task['notice'] in covered:return {'done':False,'artifacts':{'frame_index':cursor+1,'frame_state':{}}}
        state=copy.deepcopy(a['frame_state']);chain='violation-'+Path(ctx['folder']).parent.parent.name[:24]+'-'+str(ctx['order']['companies'].index(ctx['company']));stem=str(cursor).zfill(4)+'-'+task['mode'];out=folder/'frames'/stem
        if state.get('phase')=='capture':
            completed=self.completed_capture_frame(source,state['observation'],profile,chain,out,task['mode'],chain+':'+stem)
            if completed is not None:
                metadata,checked=completed
                if task['mode']=='rows':need(task['notice'] in checked['notice_ids'],'execution-target-row-not-covered')
                return {'done':False,'artifacts':{'frames':frames+[metadata],'frame_index':cursor+1,'frame_state':{}}}
        if task['mode']=='rows':self.ensure_screenshot_full_identity(source,profile,state.get('observation') or o.doc(a['query_final'])['last_observation'],chain,folder,out,chain+':'+stem+':'+state.get('phase','page')+':full-identity',fresh_observation=state.get('observation'),fresh_navigation=state.get('navigation_checkpoint'))
        reader=screenshot_nav.Runner(source,profile,invoke=self.request)
        if not state:
            value=reader.run('page',key=chain+':'+stem+':page',page=task['page']);need(value['status']=='complete','execution-screenshot-page-not-ready');state={'phase':'scroll','observation':value['observation'],'navigation_checkpoint':value['journal']}
            return {'done':False,'artifacts':{'frame_state':state},'journal':value['journal']}
        if state['phase']=='scroll':
            value=reader.run('anchor' if task['mode']=='anchor' else 'row',key=chain+':'+stem+':scroll',notice_id=task['notice']);need(value['status']=='complete','execution-screenshot-scroll-not-ready');state.update(phase='capture',observation=value['observation'],navigation_checkpoint=value['journal'])
            return {'done':False,'artifacts':{'frame_state':state},'journal':value['journal']}
        need(state['phase']=='capture','execution-frame-phase-invalid')
        if state.get('preintent_observation_refresh') is not None:
            state,unused=self.fresh_preintent_capture_state(reader,state,source,profile,out,chain+':'+stem)
            need(unused is None,'execution-preintent-marker-refresh-conflict')
        original_bound=state.get('preintent_observation_refresh') is not None or self.capture_frame_started(source,out,chain+':'+stem)
        focus=self.ensure_capture_focus(source,state['observation'],profile,chain,out,environment_restoration=a.get('environment_restoration'),allow_input=not original_bound)
        if focus['input_attempted'] or focus.get('refresh_observation'):
            need(not original_bound,'execution-preintent-marker-focus-refresh-HOLD')
            current=reader.run('observe');state.update(observation=current['observation'],navigation_checkpoint=current['journal'],capture_focus=focus['journal'])
            return {'done':False,'artifacts':{'frame_state':state},'journal':current['journal']}
        if getattr(self,'reboot_continuation',None) and not state.get('reboot_current_observation'):
            need(not original_bound,'execution-preintent-marker-reboot-refresh-HOLD')
            pending=screenshot_nav.pending_frames(source);need(not pending,'execution-reboot-native-pending-no-new-input')
            self.ensure_screenshot_full_identity(source,profile,state['observation'],chain,folder,out,chain+':'+stem+':reboot-current-identity')
            current=reader.run('observe');state.update(observation=current['observation'],navigation_checkpoint=current['journal'],reboot_current_observation=True)
            return {'done':False,'artifacts':{'frame_state':state},'journal':current['journal']}
        # Persisted observation is part of the original capture operation. QA
        # continuation must not substitute a newer observation/key/outdir.
        state,refresh_journal=self.fresh_preintent_capture_state(reader,state,source,profile,out,chain+':'+stem)
        if refresh_journal is not None:return {'done':False,'artifacts':{'frame_state':state},'journal':refresh_journal}
        screenshot_anchor=self.capture_identity_anchor(source,state['observation'],profile,chain,folder,out,task['mode'])
        value=region.capture(source,state['observation'],profile,**({'screenshot_anchor':screenshot_anchor} if screenshot_anchor is not None else {}),pid=self.pid,mode=task['mode'],chain_id=chain,key=chain+':'+stem,outdir=out,uncovered_only=task['mode']=='rows',request=self.request)
        metadata=o.ref(value['metadata']);m=o.doc(metadata)
        if value['state']=='awaiting-visual-review':
            try:
                producer=region.program_epoch_rows_quality.create if m.get('frame_mode')=='rows' and m.get('postguard_consistency') is not None else(region.program_region_quality.fragment_create if m.get('date_visible_fragment_in_image') is True else region.program_region_quality.create)
                attestation=producer(metadata,source,out/('program-quality-epoch-rows'if producer is region.program_epoch_rows_quality.create else'program-quality'))
            except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
                inspection=region.inspect_registration(metadata['path']);return {'done':False,'handoff':{'response_kind':'violation-frame-qa-response-v1','source':source,'preview':metadata,'inspection':inspection,'program_quality_exception':str(error),'requirements':'Program quality unresolved; no automatic approval. Preserve original preview.'}}
            region.approve_preview(metadata['path'],attestation)
            metadata=o.ref(out/'registration.json');m=o.doc(metadata)
            value={**value,'state':'complete'}
        if value['state']=='awaiting-visual-review':
            inspection=region.inspect_registration(metadata['path']);return {'done':False,'handoff':{'response_kind':'violation-frame-qa-response-v1','source':source,'preview':metadata,'inspection':inspection,'requirements':'Supervisor views exact PNG and returns {request,kind,attestation:{path,sha256}}. Never synthesize field visibility.'}}
        need(m.get('state')=='complete' and m.get('source_sha256')==source['sha256'],'execution-current-capture-result-required');o.raw({k:m['image'][k]for k in('path','sha256')});checked={'notice_ids':m['notice_ids']}
        if task['mode']=='rows':need(task['notice'] in checked['notice_ids'],'execution-target-row-not-covered')
        return {'done':False,'artifacts':{'frames':frames+[metadata],'frame_index':cursor+1,'frame_state':{}}}

    def seal(self,ctx):
        import execution_timing as timing
        order=ctx['order'];companies=[];all_orders=[]
        for c,entry in zip(order['companies'],ctx['companies']):
            if c['skipped']:self.skipped(c);continue
            a=self.reboot_artifacts(entry['artifacts']);s=w.load(Path(c['root']));batch=a['batch'];b=s['batches'][batch];capture.validate(a['source']['path'])
            import dispatch_validation_context
            # Derive only this company's current business orders.
            context=dispatch_validation_context.derive(w,s,batch) if b['total'] else None
            orders=context.orders() if context is not None else []
            if not b['total']:
                zn=_zero_notice_module()
                work=o.ref(o.order_path(ROOT/'runtime/workshop-director',order['dispatch_id']));index=order['companies'].index(c)
                zero_source=b['source']if order.get('collection_contract')=='three-flow-collection-ready-v1'else a['source']
                if order.get('collection_contract')=='three-flow-collection-ready-v1'and zero_source['sha256']==a['source']['sha256']:need(o.raw(zero_source)==o.raw(a['source']),'execution-staged-zero-ledger-source-copy')
                elif order.get('collection_contract')=='three-flow-collection-ready-v1':
                    # Supervised zero-recapture adoption (B35/W100): the sealed
                    # batch keeps its original authoritative source and binding
                    # fingerprint; the delivery's own fresh capture stays the
                    # manifest source, so the zero notice binds the fresh capture
                    # exactly as the send phase re-checks (expected['source']).
                    source=capture.validate(a['source']['path'])
                    o.raw(b['source']);need(b['status']=='zero_verified' and b['input_fingerprint']==w.fingerprint(o.doc(b['source'])) and w.zero_recapture_aligned(s,b,source),'execution-staged-zero-ledger-source-adoption')
                    zero_source=a['source']
                orders=[zn.prepare(Path(ctx['folder'])/'companies'/str(index)/'zero-result-notice','violation-notifier',c['company'],c['start'],c['end_exclusive'],work,[zero_source],module_ref=_ZERO_NOTICE_MODULE)]
            dependencies=[]
            # Bind current batch artifacts; source-code and historical sessions
            # are not delivery inputs.
            def collect(v):
                if isinstance(v,dict):
                    if set(v)=={'path','sha256'}:
                        o.raw(v)
                        if v not in dependencies:dependencies.append(v)
                    else:
                        for x in v.values():collect(x)
                elif isinstance(v,list):
                    for x in v:collect(x)
            collect(b);rows={'company':c['company'],'batch':batch,'orders':orders,'source':a['source'],'dependencies':dependencies};companies.append(rows);all_orders.extend(orders)
        need(len({x['key'] for x in all_orders})==len(all_orders),'execution-delivery-key-duplicate')
        for order in all_orders:
            path=timing.sender_path(order['key'])
            if path.exists():
                import unified_delivery
                typ=order['type'];item={'key':order['key'],'kind':order['kind'],'target':order['target'],'scope':order['scope'],'type':typ,'payload':{'path':order['file'if typ=='file'else'text_file'],'sha256':order['file_sha256'if typ=='file'else'text_sha256']}}
                unified_delivery.confirmed(item,ROOT/'runtime/wecom-messenger')
        value={'zero_result_contract':'notify-confirmed-zero-v1','zero_module_ref':_ZERO_NOTICE_MODULE,'kind':'violation-complete-delivery-manifest-v1','scope_sha256':ctx['order']['scope_sha256'],'companies':companies,'orders':all_orders,'fresh_canonical_absence_checked':True}
        manifest=o.immutable(Path(ctx['folder'])/'delivery.json',value)
        # Engine propagates this single manifest into all company's send context.
        return {'manifest':manifest,'keys':[x['key'] for x in all_orders]}
    def collection_seal(self,ctx):
        need(ctx['order'].get('collection_contract')=='three-flow-collection-ready-v1','execution-staged-policy-required');delivery=self.seal(ctx);companies=[]
        for c,entry in zip(ctx['order']['companies'],ctx['companies']):
            if c['skipped']:continue
            a=self.reboot_artifacts(entry['artifacts']);state=w.load(Path(c['root']));batch=state['batches'][a['batch']];capture.validate(a['source']['path'])
            need(not batch.get('completed_at')and not batch.get('sent'),'execution-staged-not-completed');need(type(batch['total'])is int and batch['total']>=0,'execution-staged-count')
            companies.append({'company':c['company'],'groupid':c['groupid'],'start':c['start'],'end_exclusive':c['end_exclusive'],'count':batch['total'],'source':a['source'],'ledger':o.ref(Path(c['root'])/'state.json')})
        original=o.doc(o.ref(Path(ctx['folder'])/'engine.json'))['order'];need(o.validate(original)==ctx['order'],'execution-staged-original-order')
        ready={'kind':'violation-collection-ready-v1','order':original,'scope_sha256':ctx['order']['scope_sha256'],'companies':companies,'delivery_plan':delivery['manifest'],'collection_ready':True,'delivery_complete':False,'cursor_advanced':False}
        return {'done':True,'ready':o.immutable(Path(ctx['folder'])/'collection-ready.json',ready)}
    def finish(self,ctx):
        import execution_timing as timing
        order=ctx['order'];outer=o.doc(o.ref(Path(ctx['folder'])/'launcher.json'));need(outer['scope_sha256']==order['scope_sha256'],'execution-final-outer-scope');begun=timing.parse_time(outer['wall_started_at']);sealed=o.doc(ctx['delivery']['manifest']);_zero_notice_module(sealed['zero_module_ref'])if sealed.get('zero_result_contract')=='notify-confirmed-zero-v1'else None;need(sealed['scope_sha256']==order['scope_sha256'],'execution-final-delivery-scope');clients=[];evidence=[ctx['delivery']['manifest']]
        for index,(c,entry) in enumerate(zip(order['companies'],ctx['companies'])):
            if c['skipped']:self.skipped(c);continue
            a=self.reboot_artifacts(entry['artifacts']);s=w.load(Path(c['root']));src=capture.validate(a['source']['path']);batch=a['batch'];b=s['batches'][batch]
            need(Path(a['source']['path'])==Path(ctx['folder'])/'companies'/str(index)/'source.json','execution-final-original-source-path');need(src['source_evidence_refs']['job']==a['job'],'execution-final-source-job-not-original')
            rawrefs=src['source_evidence_refs']['raw_observations'];need(rawrefs,'execution-final-raw-observations-required')
            for reference in rawrefs:need(begun<=timing.parse_time(o.doc(reference)['observed_at'])<=timing.Clock().wall(),'execution-old-source-not-fresh-run')
            need(b['completed_at'] and s['next_start']>=c['end_exclusive'] and src['company']==c['company'] and (src['start'],src['end_exclusive'])==(c['start'],c['end_exclusive']),'execution-final-batch-not-complete');expected=next(x for x in sealed['companies'] if x['company']==c['company']);orders=w.send_orders(s,batch) if b['total'] else expected['orders'];need(orders==expected['orders'],'execution-final-delivery-set-changed')
            for ref in expected['dependencies']:
                import violation_reboot_continuation as reboot
                reboot._sealed_delivery_dependency(ref,ctx['delivery']['manifest'])
            for order_item in orders:
                if not b['total']:
                    zn=_zero_notice_module()
                    need(b.get('zero_result_notification',{}).get('order')==order_item,'execution-final-zero-notice-binding');clients.append(zn.client(order_item,b['zero_result_notification']['client']));continue
                import execution_timing as timing
                entry=b['send_jobs'][order_item['part']];canonical=timing.sender_path(order_item['key']);need(Path(entry['job_path'])==canonical,'execution-final-sender-not-canonical');r=o.doc(entry['receipt']);job=r['job'];need(r.get('status')=='complete' and r.get('phase')=='done' and r.get('sent') is True and r.get('ui_confirmed') is True and not r.get('error') and r['fingerprint']==w.fingerprint(job),'execution-final-client-not-confirmed');need(job['key']==order_item['key'] and job['scope']=='test' and job['kind']=='group' and job['target']==w.TEST_GROUP and job['type']==order_item['type'],'execution-final-client-scope');need(job.get('file_sha256')==order_item.get('file_sha256') if job['type']=='file' else __import__('hashlib').sha256(job['text'].encode()).hexdigest()==order_item['text_sha256'],'execution-final-client-content');clients.append(entry['receipt'])
            evidence.extend([a['source'],o.ref(Path(c['root'])/'state.json')])
        need(len(clients)==len(sealed['orders']),'execution-final-client-set-incomplete');return {'kind':'violation-execution-source-client-proof-v1','outcome':'client-confirmed' if clients else 'no-data-complete','clients':clients,'evidence':evidence,'scope_sha256':order['scope_sha256']}

    def verify_collection_materials(self,order,state,ready,ledgers):
        need(order.get('collection_contract')=='three-flow-collection-ready-v1'and ready.get('kind')=='violation-collection-ready-v1'and ready.get('order')==state['order']and ready.get('scope_sha256')==order['scope_sha256']and ready.get('collection_ready')is True and ready.get('delivery_complete')is False and ready.get('cursor_advanced')is False,'violation-ready-material-shape')
        manifest=o.doc(ready['delivery_plan']);_zero_notice_module(manifest['zero_module_ref']);need(manifest['kind']=='violation-complete-delivery-manifest-v1'and manifest['scope_sha256']==order['scope_sha256'],'violation-ready-plan-binding')
        import execution_timing as timing
        origin=o.doc(o.ref(o.location(state['order'])/'origin.json'));begun=timing.parse_time(origin['wall_started_at']);companies=[];all_orders=[]
        for index,(c,cs)in enumerate(zip(order['companies'],state['companies'])):
            if c['skipped']:continue
            a=cs['artifacts'];ledger=ledgers[c['company']];need(ledger['company']==c['company']and ledger['groupid']==c['groupid']and ledger['next_start']==c['start'],'violation-ready-ledger-scope');source=capture.validate(a['source']['path']);batch=ledger['batches'][a['batch']]
            need(source['company']==c['company']and(source['start'],source['end_exclusive'])==(c['start'],c['end_exclusive'])and source['source_evidence_refs']['job']==a['job']and not batch.get('completed_at'),'violation-ready-source-scope')
            rawrefs=source['source_evidence_refs']['raw_observations'];need(rawrefs,'violation-ready-raw-required')
            for r in rawrefs:need(begun<=timing.parse_time(o.doc(r)['observed_at'])<=timing.Clock().wall(),'violation-ready-source-time')
            expected=next(x for x in manifest['companies']if x['company']==c['company'])
            if batch['total']:
                orders=w.send_orders(ledger,a['batch']);need(orders==expected['orders'],'violation-ready-orders-not-derived')
            else:
                orders=expected['orders'];need(source['analysis']['total']==source['records']['total']==batch['total']==0 and len(orders)==1,'violation-ready-authoritative-zero');item=orders[0];binding=item['zero_result_binding']
                if binding['sources']==[batch['source']]and batch['source']['sha256']==a['source']['sha256']and o.raw(batch['source'])==o.raw(a['source']):pass
                elif order.get('collection_contract')=='three-flow-collection-ready-v1':
                 # Supervised zero-recapture adoption (B35/W100/W120): the
                 # sealed batch keeps its original authoritative source and
                 # fingerprint; the delivery order binds the fresh capture
                 # exactly as the seal and send phases both re-check.
                 o.raw(batch['source']);need(batch['status']=='zero_verified'and batch['input_fingerprint']==w.fingerprint(o.doc(batch['source']))and w.zero_recapture_aligned(ledger,batch,source)and binding['sources']==[a['source']],'violation-ready-zero-adoption')
                else:need(False,'violation-ready-zero-scope')
                need(binding['flow']=='violation-notifier'and binding['company']==c['company']and(binding['start'],binding['end_exclusive'])==(c['start'],c['end_exclusive'])and binding['work_order']==state['order'],'violation-ready-zero-scope');_zero_notice_module().job(item)
            for r in expected['dependencies']:o.raw(r)
            all_orders.extend(orders);companies.append({k:c[k]for k in('company','groupid','start','end_exclusive')}|{'count':batch['total'],'source':a['source'],'ledger':next(x['ledger']for x in ready['companies']if x['company']==c['company'])})
        need(all_orders==manifest['orders']and companies==ready['companies'],'violation-ready-exact-materials')
        return {'companies':companies}

_ZERO_NOTICE_PATH=ROOT/'skills/workshop-director/scripts/zero_result_notice.py'
_ZERO_NOTICE_MODULE={'path':str(_ZERO_NOTICE_PATH),'sha256':__import__('hashlib').sha256(_ZERO_NOTICE_PATH.read_bytes()).hexdigest()}
def _zero_notice_module(reference=None):
    expected=_ZERO_NOTICE_MODULE
    need(reference is None or reference==expected,'zero-notice-module-binding')
    path=Path(expected['path'])
    need(path==ROOT/'skills/workshop-director/scripts/zero_result_notice.py'and path.is_absolute()and path.resolve()==path and not any(p.is_symlink()for p in (path,*path.parents))and path.is_file(),'zero-notice-module-origin')
    need(__import__('hashlib').sha256(path.read_bytes()).hexdigest()==expected['sha256'],'zero-notice-module-code-drift')
    sys.path.insert(0,str(path.parent))
    import zero_result_notice
    need(Path(zero_result_notice.__file__)==path,'zero-notice-loaded-module-origin')
    return zero_result_notice
