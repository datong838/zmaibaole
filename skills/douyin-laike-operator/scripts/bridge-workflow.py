#!/usr/bin/env python3
"""One durable semantic-DOM transition per invocation. Never starts Chrome."""
import argparse, contextlib, fcntl, hashlib, importlib.util, json, os, re, sys, time, uuid
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from zipfile import ZipFile, BadZipFile
from dom_evidence import VERSION, nodes, leaves, unique, exact, identity, context, all_reviews, calendar_day, records, review_filter_fields, verified_review_filter, record_tabs, export_tag, generated_record, all_store_scope, export_range_input, complete_record_list, submitted_export_record, verified_export_dialog, export_calendar_day, company_switch
from role_cli import validate_job, write_json, digest
import export_baseline_pages
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('local_dom_bridge',ROOT/'skills/chrome-dom-export/scripts/bridge.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)

# ---------------------------------------------------------------------------
# W131a shared transient primitives (docs/瞬态代际证据链治理整改蓝图-Easel-n8n学习采纳.md,
# items P1/P2/P3/P4/P5). Pure, offline-deterministic (sleep/monotonic injectable).
# Consumers are wired in per-phase waves; until then these are exercised only
# by check131a. Discipline: an unresolved transient is UNCONFIRMED, never data.
# ---------------------------------------------------------------------------
PARTIAL_SUFFIXES=('.crdownload','.download','.part')
EXPORT_MENU_ITEMS=('导出评价','评价导出记录')
def poll_stable(sig,budget,interval=.25,sleep=time.sleep,monotonic=time.monotonic):
    # Easel account_stats.py:422 _poll_stable: sample sig() until two
    # consecutive readings agree AND are parseable; None means "not rendered
    # yet" and never counts as a value (the async 0-placeholder trap: a real
    # zero also stabilizes quickly, a placeholder never agrees with the
    # filled value twice in a row).
    end=monotonic()+budget;probes=0;prev=_POLL_UNSET=object()
    while True:
        value=sig();probes+=1
        if value is not None and probes>1 and value==prev:return value,probes
        prev=value
        delay=min(interval,max(0.0,end-monotonic()))
        if delay<=0:raise ValueError('poll-stable-unconfirmed')
        sleep(delay)
def settle(read,budget,interval=.25,grace=1.0,sleep=time.sleep,monotonic=time.monotonic):
    # Easel web_publisher.py:832 _settle_login: after a transition, judge only
    # on an explicit signal. Negative wins immediately and is the most
    # reliable signal; positive needs a grace margin (the body may lag the
    # mask - B57); expiry stays unknown for the caller to fail closed.
    # read() returns 'positive' | 'negative' | None.
    end=monotonic()+budget
    while True:
        signal=read()
        if signal=='negative':return 'gone'
        if signal=='positive':
            rest=end-monotonic()
            if rest<=0:raise ValueError('settle-positive-window-exhausted')
            sleep(min(grace,rest));return 'ready' if read()=='positive' else 'unknown'
        if monotonic()+interval>end:return 'unknown'
        sleep(interval)
def wait_rendered(present,items,budget,interval=.2,sleep=time.sleep,monotonic=time.monotonic):
    # Easel xhs_comment.py:355 _do_delete two-way split for hover-late-render
    # (B56/W126): container absent is an ACTION-level failure (the hover may
    # be retried); container present with zero items is DATA lag (keep
    # waiting). Exhaustion keeps that distinction instead of one blurred
    # timeout: 'absent' returns for retry, present-but-empty fails closed.
    end=monotonic()+budget;saw_container=False
    while True:
        if present():
            got=items()
            if got:return 'ready',got
            saw_container=True
        if monotonic()+interval>end:
            if saw_container:raise ValueError('wait-rendered-items-unconfirmed')
            return 'absent',None
        sleep(interval)
def file_size_stable(path,budget,interval=.25,grace=.3,sleep=time.sleep,monotonic=time.monotonic,wall=time.time):
    # Easel filesystem double-read stability (account_stats.py:422 idea applied
    # to downloads, P4): no partial suffix, size equal on two consecutive
    # reads, and mtime older than the grace margin. Partial suffix present is
    # itself a definitive not-done signal inside the budget.
    end=monotonic()+budget;prev=None
    while True:
        p=Path(path)
        if p.exists() and not p.is_symlink():
            if not any(p.name.endswith(s)for s in PARTIAL_SUFFIXES):
                size=p.stat().st_size
                if size==prev and wall()-p.stat().st_mtime>=grace:return size
                prev=size
            else:prev=None
        if monotonic()+interval>end:raise ValueError('download-size-unconfirmed')
        sleep(interval)
def prepare_download_target(directory,name):
    # Easel web/app.py:1500 _unique_upload_path write-side avoidance (P4):
    # the export lands in a directory where the target name is provably free,
    # so a Chrome " (2)" collision can never be created. Never delete or
    # overwrite: an occupied name is a caller decision (archive first).
    d=Path(directory);target=d/name
    if target.exists() or target.is_symlink():raise ValueError('download-target-occupied')
    d.mkdir(parents=True,exist_ok=True)
    if target.exists() or target.is_symlink():raise ValueError('download-target-occupied')
    return target
def unique_incremental(directory,stem,ext):
    # Easel _unique_upload_path: last-resort collision avoidance when the
    # caller must keep an existing artifact - first free stem(1) stem(2)...
    d=Path(directory);candidate=d/(stem+ext);n=1
    while candidate.exists() or candidate.is_symlink():
        candidate=d/('%s(%d)%s'%(stem,n,ext));n+=1
    return candidate
def record_page_fingerprint(tree):
    # W131b (blueprint P1/P2): a fingerprint that never raises, so a transient
    # page can always be compared. Row count + row-text digest + pager text;
    # None while the virtual table body has not rendered at all (B57). None is
    # never a value and two equal readings are what "settled" means.
    has_body=False;rows=[];pager=[]
    for n in nodes(tree):
        classes=n.get('attributes',{}).get('class','').split()
        if 'byted-table-body' in classes:has_body=True
        if 'byted-table-row' in classes:rows.append(n.get('name',''))
        if 'byted-pager-record' in classes:pager.append(n.get('name',''))
    if not has_body:return None
    return {'rows':len(rows),'text':hashlib.sha256('\x00'.join(rows).encode()).hexdigest()[:16],'pager':pager}
def export_menu_probe(tree):
    # W131c (blueprint P3): the confirmed export hover opens a dropdown that
    # renders late (B56/W126). Two facts decide everything and neither may be
    # guessed: does the trigger still exist (action-level), and which panel
    # items are rendered (data-level). Never raises, so a half-rendered tree
    # is always comparable. The trigger predicate is the exact one the
    # supervised re-hover gate uses (reconcile_export_menu_hover), so the
    # natural and reconciled paths agree on what "the trigger" is.
    try:all_nodes=list(nodes(tree))
    except Exception:return None
    triggers=[n for n in all_nodes if n.get('name')=='导出' and 'byted-popper-trigger-hover' in (n.get('attributes',{}).get('class','') or '').split()]
    present=[label for label in EXPORT_MENU_ITEMS if any(n.get('name')==label for n in all_nodes)]
    return {'triggers':len(triggers),'items':present,'missing':[l for l in EXPORT_MENU_ITEMS if l not in present],
            'ready':len(present)==len(EXPORT_MENU_ITEMS)}

def preenqueue_rejection(reply):
    # Only the exact owned server response emitted before Jobs.add qualifies.
    keys={'ok','error','error_type','stage','outcome','job_created','execution_started','retry'}
    if type(reply)is not dict or set(reply)!=keys:return False
    known=reply.get('error_type')in('ValueError','KeyError','TypeError','TimingError')
    return (reply['ok']is False and reply['job_created']is False and reply['execution_started']is False and
            reply['stage']=='pre-enqueue'and reply['outcome']=='not-delivered'and
            reply['error_type']in('ValueError','KeyError','TypeError','ModuleNotFoundError','ImportError','AttributeError','OSError','FileNotFoundError','PermissionError','TimingError','AdmissionError')and
            reply['error']==('configured-company-admission-rejected'if known else'configured-company-admission-unavailable')and
            reply['retry']=='Never replay an existing UNKNOWN intent; reconcile its original evidence.')

def _preenqueue_binding(entry,record,scope):
    material={'key':entry['key'],'at':entry['at'],'phase':entry['phase'],'command':entry['command'],'observation':record,'source_scope':scope}
    return hashlib.sha256(json.dumps(material,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def legacy_fingerprint(job):
    payload=[1,job.get('work_order_id'),job.get('action'),job.get('company'),str(job.get('groupid')),
             {k:job.get('date_range',{}).get(k) for k in ('start','end')},job.get('source_dir')]
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def has_side_effect_intent(state):
    return bool(state.get('exportPending') or state.get('downloadPending') or state.get('export_pending') or
                state.get('download_pending') or state.get('attempts') or state.get('submittedAt') or state.get('result') or
                state.get('phase') in ('submit','armDownload','clickDownload','downloadResult','done') or
                any(c.get('stage') in ('export-intent','download-intent') for c in state.get('checkpoints',[])) or
                any(c.get('command',{}).get('kind') in ('export-submit','download') or c.get('phase')=='submitExport' for c in state.get('calls',[])))

def now():return datetime.now(timezone.utc).isoformat()
def fingerprint(job):
    keys=('work_order_id','company','groupid','date_range','source_dir')
    if 'company_configuration_policy'in job or 'company_configuration_entry'in job:keys+=('company_configuration_policy','company_configuration_entry');
    if 'company_configuration_registry'in job:keys+=('company_configuration_registry',)
    return hashlib.sha256(json.dumps({k:job.get(k) for k in keys},sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def review_management_target(tree):
    # The established sidebar label is a distinct public navigation scope.
    # HomeV2 may also expose the same label in its shortcuts; that is not a
    # second sidebar action and must not make this target ambiguous.
    candidates=[n for n in nodes(tree) if n.get('name')=='评价管理' and not n.get('children') and 'navi_evaluation' in n.get('attributes',{}).get('class','').split()]
    if candidates:
        target=unique(candidates,'review-management-sidebar-not-unique')
        roots=[n for n in nodes(tree) if n.get('selector')=='#box-aside-menu']
        if roots:
            root=unique(roots,'review-management-sidebar-root-not-unique')
            if not any(n is target for n in _review_subtree(root)):raise ValueError('review-management-sidebar-scope-invalid')
        if target.get('disabled') or not target.get('selector'):raise ValueError('element-not-ready')
        return target
    # Preserve the former unique exact-label behavior for older public shapes.
    return exact(tree,'评价管理')

def _review_subtree(root):
    yield root
    for child in root.get('children',[]):yield from _review_subtree(child)

def review_shortcut_reset_target(tree):
    labels=('好评（4-5心）','中差评（1-3心）','未回复','已回复','抖音消费','非抖音消费')
    controls=[exact(tree,label) for label in labels]
    selected=[]
    for label,node in zip(labels,controls):
        classes=set(node.get('attributes',{}).get('class','').split())
        if classes=={'option-YmRyn3'}:continue
        if label=='中差评（1-3心）' and classes=={'option-YmRyn3','isSelected-ov8pOi'}:selected.append(node)
        else:raise ValueError('nondefault-review-shortcut:'+label)
    if not selected:return None
    if tree.get('url')!='https://life.douyin.com/p/life_comment/management':raise ValueError('review-shortcut-reset-route')
    parent=unique([n for n in nodes(tree) if all(any(c is target for c in n.get('children',[])) for target in controls)],'review-shortcut-reset-scope')
    if parent.get('tag')!='div' or parent.get('attributes',{}).get('class')!='otherSelectGroup-PCCUqW' or not parent.get('selector','').startswith('#root > '):raise ValueError('review-shortcut-reset-scope')
    children=parent.get('children',[]);expected=[labels[0],labels[1],'',labels[2],labels[3],'',labels[4],labels[5]]
    if [n.get('name') for n in children]!=expected:raise ValueError('review-shortcut-reset-shape')
    for node in children:
        if node.get('tag')!='div' or node.get('role')!='generic' or node.get('children') or node.get('disabled') or not node.get('selector'):raise ValueError('review-shortcut-reset-shape')
        if node['name']=='' and node.get('attributes',{}).get('class')!='divider-t1NIxB':raise ValueError('review-shortcut-reset-divider')
    return selected[0]

COMPANY_CONFIRM_FAILURE_SHA='0445b6af863ddffdf88d8fef10385d615b9acac8a20edddfb7d5f4a9ff18a209'
EXPORT_MENU_FAILURE_SHA='d514ea731628b33259ab4c7962c09eb7d23c45aa643d4c3d4ce4240e1d7e19b7'
# B70: the picker footer fatals before any confirm intent is issued, so the exit
# below can only retire that exact code - never a transport, identity or input error.
COMPANY_CONFIRM_PENDING_FOOTER='company-picker-confirm-unique'
COMPANY_CONFIRM_PENDING_FOOTER_KIND='company-confirm-pending-footer-read-v1'
# B72: the confirm guard refuses EVERY journal that still carries a last_error,
# and an exit enumerated one code at a time locks the unit again the moment the
# next refusal has a different name - which is exactly what happened between
# W132i and W132j. The exit is therefore a closed set of refusals that all share
# one verifiable shape: they happen while PREPARING the confirm input, so no
# input intent was ever journaled, and each of them already has its own fix.
# Adding a name here is a claim that such a fix exists, and check132k proves the
# shape on real evidence rather than trusting this comment.
COMPANY_CONFIRM_RETIRABLE_REFUSALS=frozenset((
    'company-picker-confirm-unique',        # W132g: footer renders after the row
    'company-operation-expired-or-unbounded',  # W132j: 300s window while held
    # B77: the page-shape reader's own refusal. It is raised while reading the
    # picker, before any input exists, and it was the one error class the closed
    # set still missed - so the run retired one refusal and then died on the
    # next, whose name nothing could retire. Same shape as the two above: it
    # carries no intent of its own.
    'company-confirm-settle-unknown-intent',
))
COMPANY_CONFIRM_REFUSAL_KIND='company-confirm-preparation-refusal-v1'

def owned_undelivered_confirm_call(state,call):
    """B76: a confirm click the bridge refused before Jobs.add is still `unknown`
    in the journal - the original intent must stay intact as evidence - but
    nothing was ever dispatched for it. The retirement record is the durable
    proof: it is written only after the reviewed non-delivery envelope
    (job_created false, execution_started false, not-delivered) has been matched
    to this exact key and command. Once it exists, the page-shape readers must
    stop calling that entry an unsettled input, or the retry it authorises can
    never reach the page it needs.
    """
    command=call.get('command',{})
    if call.get('state')!='unknown'or command.get('op')!='click'or command.get('kind')!='company-confirm':return False
    owned=[e for e in state.get('resolved_errors',[])if e.get('resolution')=='company-confirm-preparation-refusal-v1'and (e.get('non_delivery')or{}).get('entry_key')==call.get('key')]
    return len(owned)==1

def company_confirmation_loading(tree,job,state):
    """Only the observed post-selection modal may settle with zero input."""
    from company_search_wait import PREFIXES
    ns=list(nodes(tree))
    # The existing unique ready-confirm path remains unchanged, including the
    # legacy identity contract. Only zero-confirm loading needs the new proof.
    ready=[n for n in ns if n.get('name')=='确认' and n.get('role')=='button' and not any(c.get('name')=='确认' for c in n.get('children',[]))]
    if ready and any(n.get('placeholder')=='搜索商户' for n in ns):
        # B76: only an intent that may really have been dispatched is unsettled.
        unsettled=[c for c in state.get('calls',[])if c.get('state')!='confirmed']
        if [c for c in unsettled if not owned_undelivered_confirm_call(state,c)]:
            if not state.get('company_search_explicit_recovery'):raise ValueError('company-confirm-settle-unknown-intent')
            # Pure loading diagnosis only; actual input still requires live admission.
            from switch_read_recovery import _typed_search_snapshot
            _typed_search_snapshot(job,state)
        if any({'life-core-loading-mask','life-core-loading-mask-show'}<=set(n.get('attributes',{}).get('class','').split()) for n in ns):raise ValueError('company-confirm-button-with-loading')
        exact(tree,'确认','button');return False
    if state.get('state')!='running' or state.get('phase')!='confirmSwitch' or job.get('identity_contract')!='merchant-v2' or has_side_effect_intent(state):raise ValueError('company-confirm-settle-scope-required')
    calls=state.get('calls',[])
    typed_search=None
    if not calls:raise ValueError('company-confirm-settle-unknown-intent')
    unsettled=[c for c in calls if c.get('state')!='confirmed']
    if [c for c in unsettled if not owned_undelivered_confirm_call(state,c)]:
        if not state.get('company_search_explicit_recovery'):raise ValueError('company-confirm-settle-unknown-intent')
        # Same pure typed prefix/terminal admission as the ready-confirm branch.
        # This diagnoses read-only loading; actual inputs keep canonical gates.
        from switch_read_recovery import _typed_search_snapshot
        typed_search=_typed_search_snapshot(job,state)
    # B76: the provably undelivered confirm click is not the selection this
    # branch validates; the last confirmed input is.
    last=([c for c in calls if c.get('state')=='confirmed']or calls)[-1];cmd=last.get('command',{});clicked=last.get('result',{}).get('clicked',{})
    if last.get('phase')!='chooseCompany' or cmd.get('op')!='click' or cmd.get('kind')!='company' or cmd.get('tabId')!=state.get('tab_id') or cmd.get('locator')!={'by':'selector','value':clicked.get('selector')} or not clicked.get('selector') or clicked.get('name')!=job['company']:raise ValueError('company-confirm-selection-unverified')
    from company_search_wait import verified_entry_identity
    expected=verified_entry_identity(job,state)if typed_search is None else None
    if typed_search is not None:
        source=typed_search['operation']
        if source.get('source_groupid')!=state.get('initial_groupid'):raise ValueError('company-confirm-entry-identity-required')
        expected=source.get('source_identity')
    if not expected or expected!=state.get('entry_identity') or expected.get('provider')!=state.get('provider_baseline'):raise ValueError('company-confirm-entry-identity-required')
    fields=[n for n in ns if n.get('placeholder')=='搜索商户']
    if not fields:return False
    field=unique(fields,'company-confirm-search-not-unique')
    if field.get('role')!='textbox' or field.get('disabled') or not field.get('selector') or field.get('attributes',{}).get('value')!=job['company']:raise ValueError('company-confirm-search-value-changed')
    buttons=[n for n in ns if n.get('name')=='确认' and n.get('role')=='button' and not any(c.get('name')=='确认' for c in n.get('children',[]))]
    if buttons:
        if any({'life-core-loading-mask','life-core-loading-mask-show'}<=set(n.get('attributes',{}).get('class','').split()) for n in ns):raise ValueError('company-confirm-button-with-loading')
        exact(tree,'确认','button') # Ambiguous/disabled remains the original failure.
        return False
    modal=unique([n for n in ns if any(p+'login-modal--' in n.get('attributes',{}).get('class','') for p in PREFIXES)],'company-confirm-loading-modal-unverified')
    classes=set(modal.get('attributes',{}).get('class','').split())
    if not {'life-core-modal','life-core-modal-show'}<=classes:raise ValueError('company-confirm-loading-modal-unverified')
    inner=list(nodes({'truncated':False,'root':modal}));prefix=unique([p for p in PREFIXES if p+'login-modal--' in modal.get('attributes',{}).get('class','')])
    if not any(n is field for n in inner):raise ValueError('company-confirm-search-outside-modal')
    for token in ('container--','content--'):unique([n for n in inner if prefix+token in n.get('attributes',{}).get('class','')],'company-confirm-loading-structure-unverified')
    for required in ({'life-core-loading-mask','life-core-loading-mask-show'},{'life-core-loading-wrapper','life-core-loading-wrapper-show'}):unique([n for n in inner if required<=set(n.get('attributes',{}).get('class','').split())],'company-confirm-loading-structure-unverified')
    if any(n.get('role') in ('button','combobox') for n in inner):raise ValueError('company-confirm-loading-unexpected-control')
    return True

def typed_company_confirmation_error_transform(job,before,original_ref):
    """Pure exact failed-loading metadata delta; caller owns locks/CAS/archive.
    No transport, new intent, phase/call edit or input permission is produced.
    """
    path=Path(job['workflow_path'])
    if original_ref.get('path')!=str(path) or path!=path.resolve() or any(p.is_symlink()for p in(path,*path.parents)) or not path.is_file():raise ValueError('typed-confirm-original-canonical')
    original=path.read_bytes()
    if hashlib.sha256(original).hexdigest()!=original_ref.get('sha256') or json.loads(original)!=before:raise ValueError('typed-confirm-original-drift')
    error=before.get('last_error',{})
    if set(error)!={'at','code','message'} or error.get('code')!=error.get('message') or error.get('code')!='company-confirm-settle-unknown-intent' or before.get('phase')!='confirmSwitch' or before.get('revision')!=4 or len(before.get('calls',[]))!=3 or not before.get('company_search_explicit_recovery'):raise ValueError('typed-confirm-exact-loading-error')
    tree_ref=before['last_tree'];tree_path=Path(tree_ref['path'])
    if tree_path.parent!=path.parent/'bridge-evidence' or not re.fullmatch(r'0004-confirmSwitch-recovered-[0-9a-f]{32}\.json',tree_path.name) or tree_path!=tree_path.resolve() or any(p.is_symlink()for p in(tree_path,*tree_path.parents)) or digest(tree_path)!=tree_ref['sha256']:raise ValueError('typed-confirm-original-loading-tree')
    if not company_confirmation_loading(json.loads(tree_path.read_bytes()),job,before):raise ValueError('typed-confirm-original-not-loading')
    after=json.loads(json.dumps(before));prior=after.pop('last_error');after.setdefault('resolved_errors',[]).append({'original_error':prior,'resolution':'typed-original-search-confirmed-loading-guard-fixed','original_workflow':dict(original_ref),'original_tree':dict(tree_ref),'proof':before['company_search_explicit_recovery']['proof']})
    return after

def review_visible_system_error(tree):
    """A visible backend error is neither a pending count nor a verified zero."""
    message='系统错误，请稍后再试';ns=list(nodes(tree))
    candidates=[n for n in ns if n.get('name')==message and not any(c.get('name')==message for c in n.get('children',[]))]
    if not candidates:return None
    target=unique(candidates,'review-filter-system-error-message-ambiguous')
    if target.get('tag')!='span' or target.get('attributes',{}).get('class')!='life-core-message-content':raise ValueError('review-filter-system-error-toast-unverified')
    ancestors=[n for n in ns if 'life-core-message-type-error'in n.get('attributes',{}).get('class','').split()and any(x is target for x in _review_subtree(n))]
    unique(ancestors,'review-filter-system-error-toast-unverified')
    return {'kind':'visible-review-backend-system-error','message':message,'selector':target.get('selector'),'zero_certified':False,'company_context_loss_proven':False}

def require_no_review_system_error(tree):
    if review_visible_system_error(tree) is not None:raise ValueError('review-filter-system-error')

def plan_review_system_error_recovery(job_path,original_sha,scope_ref,outer_ref):
    """Read-only qualification/plan only; no source/state/UI mutation or grant."""
    from readonly_tick_snapshot import decode
    from review_filter_loading import validate_filter_values
    def read(reference):
        path=Path(reference['path']);assert path.is_file()and path.resolve()==path and not path.is_symlink(),'system-error-canonical-ref'
        assert digest(path)==reference['sha256'],'system-error-ref-drift';return json.loads(path.read_bytes())
    job_path=Path(job_path);assert job_path.resolve()==job_path and not job_path.is_symlink(),'system-error-job-canonical';job=json.loads(job_path.read_bytes());file=Path(job['workflow_path']);assert file.parent==job_path.parent and job['work_order_path']==str(job_path),'system-error-job-location'
    original={'path':str(file),'sha256':original_sha};state=read(original)
    assert state['state']=='running'and state['phase']=='verifyFilter'and state['last_error']['code']==state['last_error']['message']and state['last_error']['code']in ('review-filter-loading-exhausted','review-filter-system-error'),'system-error-original-frontier'
    assert state['work_order_id']==job['work_order_id']and state['company']==job['company']and str(state['groupid'])==str(job['groupid'])and state['date_range']=={k:job['date_range'][k]for k in ('start','end')}and state['identity_contract']==job['identity_contract']=='merchant-v2'and state['fingerprint']==fingerprint(job),'system-error-original-job'
    assert not has_side_effect_intent(state)and not state.get('downloadPending'),'system-error-side-effect-forbidden'
    calls=state['calls'];assert len(calls)==5 and all(c['state']=='confirmed'for c in calls)and [c['phase']for c in calls]==['openReviews','openReviews','openPageCalendar','pageStart','pageEnd'],'system-error-confirmed-five-required'
    assert state['revision']==int(calls[-1]['key'].split(':')[0])+1 and len({c['key']for c in calls})==5,'system-error-revision-or-key'
    reads=state['review_filter_loading_reads'];assert reads and reads[-1]['reply']==scope_ref and reads[-1]['tree']==state['last_tree']and Path(scope_ref['path']).parent==file.parent/'bridge-evidence','system-error-original-owned-scope'
    raw=read(scope_ref);assert raw.get('ok')is True,'system-error-original-scope-failed';scope=decode(raw['result'],state['tab_id'],raw['result']['scope']['windowId']);before=context(scope['before'],state['tab_id'],job['groupid']);after=context(scope['after'],state['tab_id'],job['groupid']);assert before['url']==after['url']and before['windowId']==after['windowId'],'system-error-context-changed'
    tree=read(state['last_tree']);assert tree==scope['tree']and tree.get('url')=='https://life.douyin.com/p/life_comment/management','system-error-original-tree'
    identity(tree,job['identity_baseline']);assert state['identity']==job['identity_baseline']==job['known_company_identities'][str(job['groupid'])],'system-error-fullidentity'
    validate_filter_values(tree,state['date_range']);problem=review_visible_system_error(tree);assert problem is not None,'system-error-visible-toast-required'
    outer=read(outer_ref);assert outer.get('start_monotonic')and outer.get('company')==job['company']and str(outer.get('groupid'))==str(job['groupid']),'system-error-original-clock'
    return {'kind':'initial-review-system-error-context-recovery-plan-v1','execution_authorized':False,'job':{'path':str(job_path),'sha256':digest(job_path)},'original_workflow':original,'original_scope':scope_ref,'original_tree':state['last_tree'],'original_outer':outer_ref,'original_calls':json.loads(json.dumps(calls)),'original_state':json.loads(json.dumps(state)),'original_revision':state['revision'],'original_phase':state['phase'],'company':job['company'],'groupid':str(job['groupid']),'date_range':state['date_range'],'bound_tab':state['tab_id'],'bound_window':before['windowId'],'bound_url':before['url'],'problem':problem,'context_loss_proven':False,'zero_certified':False,'max_context_epochs':1,'max_new_calendar_actions':3,'old_calls_replayed':False,'new_work_order':False,'next':'One separately authorized fresh readonly classification; if the exact error persists, explicitly reviewed same-order company reselection context epoch with new keys. Keep old five calls and outer. Recheck full company identity; requested date intact => skip calendar; empty => bounded fresh selector restore; other nonempty value/unknown/risk => HOLD. No export until strict date/default filters/all-store/count proof.','implementation_gap':'Existing context phase skips reselect when gid already equals target; force-reselect needs explicit epoch branch. Existing reviewProfileRequired always opens calendar; epoch branch must skip intact date. Existing date_restore_contract requires exactly original five calls, so cannot blindly apply after new context actions.'}

def bind_review_system_error_fresh(plan,fresh_scope_ref,fresh_exit_ref):
    """Bind the sole existing readonly diagnostic; never issues another read."""
    from readonly_tick_snapshot import decode
    def read(r):
        path=Path(r['path']);assert path.resolve()==path and path.is_file()and not path.is_symlink()and digest(path)==r['sha256'],'context-fresh-ref';return json.loads(path.read_bytes())
    assert plan['execution_authorized']is False and plan['kind']=='initial-review-system-error-context-recovery-plan-v1','context-plan-kind'
    result=read(fresh_exit_ref);assert result['returncode']==0 and result['raw_stdout']==fresh_scope_ref and result['workflow_after']==plan['original_workflow']and result['workflow_unchanged']is True and result['inputs']==0 and result['requests_issued']==1 and result['automatic_retry']is False and result['resources_released_on_exit']is True,'context-fresh-natural-exit'
    job=read(plan['job']);raw=read(fresh_scope_ref);assert raw.get('ok')is True,'context-fresh-read-failed';value=decode(raw['result'],plan['bound_tab'],plan['bound_window']);before=context(value['before'],plan['bound_tab'],plan['groupid']);after=context(value['after'],plan['bound_tab'],plan['groupid']);assert before['url']==after['url']==plan['bound_url'],'context-fresh-scope';identity(value['tree'],job['identity_baseline']);
    from review_filter_loading import validate_filter_values
    validate_filter_values(value['tree'],plan['date_range']);assert review_visible_system_error(value['tree'])is not None,'context-fresh-error-no-longer-present'
    return {**plan,'fresh_scope':fresh_scope_ref,'fresh_exit':fresh_exit_ref,'recovery_action':'reselect-original-company-once','key_policy':'new revision phase keys strictly after original revision; original five entries preserved verbatim','resume_phase':'context','date_policy':'exact requested date skips calendar; empty or recognized ISO range restored from fresh selectors once; malformed value HOLD','implementation_gap':None,'next':'Existing sole diagnostic consumed. After separate source/metadata authorization, original program may execute one same-order company context epoch using fresh normal ticks and new revision keys; do not issue another diagnostic, replay old calls, reset outer or accept count with error.'}

def expected_review_context_recovery(state,plan_ref,plan):
    """Pure metadata transform for a separately authorized locked caller."""
    assert digest(Path(plan_ref['path']))==plan_ref['sha256']and json.loads(Path(plan_ref['path']).read_bytes())==plan,'context-plan-ref'
    assert 'fresh_scope'in plan and plan['recovery_action']=='reselect-original-company-once'and plan['max_context_epochs']==1,'context-plan-bound-fresh'
    assert state==plan['original_state'],'context-exact-original-state'
    assert state['calls']==plan['original_calls']and state['revision']==plan['original_revision']and state['phase']==plan['original_phase']and not state.get('review_context_recovery')and state['last_error']['code']in ('review-filter-loading-exhausted','review-filter-system-error'),'context-original-state'
    assert not has_side_effect_intent(state)and all(c['state']=='confirmed'for c in state['calls']),'context-side-effect-or-unknown'
    new=json.loads(json.dumps(state));error=new.pop('last_error');new.setdefault('resolved_errors',[]).append({**error,'recovery_plan':plan_ref,'disposition':'context-reselection-required-not-success'});new['review_context_recovery']={'plan':plan_ref,'original_prefix_count':len(state['calls']),'max_epochs':1};new['phase']='context';new['revision']+=1
    return new

def export_dialog_scope_pending(tree,date_range):
    """Observed empty modal selector: pending only, never page-scope fallback."""
    try:
        list(nodes(tree));all_store_scope(tree);verified_review_filter(tree,date_range)
        modal=unique([n for n in nodes(tree)if 'byted-modal'in n.get('attributes',{}).get('class','').split()and n.get('name','').startswith('请选择要导出的评价范围')],'export-dialog-unverified')
        inner={'truncated':False,'root':modal};export_range_input(inner)
        rows=[n for n in nodes(inner)if 'form-container-coOwg9'in n.get('attributes',{}).get('class','').split()and '所属门店'in n.get('name','')]
        if len(rows)!=1:return False
        row=rows[0];cs=row.get('children',[])
        if row.get('tag')!='div'or row.get('name')!='*所属门店 按省市'or len(cs)!=2:return False
        if cs[0].get('attributes',{}).get('class')!='form-container-title-OzLGPk'or cs[0].get('name')!='*所属门店'or cs[1].get('attributes',{}).get('class')!='indicators_4a1a7'or cs[1].get('name')!='按省市':return False
        placeholders=[n for n in nodes(inner)if n.get('attributes',{}).get('class')=='detail-indicator__placeholder_4a1a7']
        return len(placeholders)==1 and placeholders[0].get('tag')=='div'and placeholders[0].get('name')==''and placeholders[0].get('children')==[]
    except ValueError:return False

def existing_record_tab(tabs,groupid,window_id,explicit=None):
    """Read-only reuse. Equal old record tabs are not duplicate export inputs."""
    if type(window_id)is not int:raise ValueError('record-tab-source-window-required')
    candidates=[t for t in record_tabs(tabs,groupid)if t.get('windowId')==window_id]
    if explicit is not None:
        return unique([t for t in candidates if t['tabId']==explicit],'record-tab-explicit-not-unique')
    if not candidates:return None
    if len({t['tabId']for t in candidates})!=len(candidates)or any(type(t['tabId'])is not int for t in candidates):raise ValueError('record-tab-identity-ambiguous')
    if len({t['url']for t in candidates})!=1:raise ValueError('record-tab-ambiguous')
    return min(candidates,key=lambda t:t['tabId'])

def configured_entry_error_transform(job,state,tree):
    from company_search_wait import entry_error_transform,pending,verified_entry_identity
    error=state.get('last_error',{})
    if (error.get('code'),error.get('message'))not in tuple((code,)*2 for code in('company-entry-reviewed-route','company-entry-governance-query','explicit-company-search-read-reconciliation-required')):
        return entry_error_transform(job,state,tree)
    if job.get('company_configuration_registry')!='configured-source-index-v2'or tree.get('url')!='https://life.douyin.com/p/governance/violation_list':raise ValueError('company-entry-governance-recovery-scope')
    candidate=json.loads(json.dumps(state));candidate.pop('last_error');pending(tree,job,candidate);expected=verified_entry_identity(job,candidate)
    # pending checks exact configured source identity, original confirmed context
    # selector and no unknown/export/download. A new readonly tick must still
    # validate the full current route/query before any new company input.
    candidate.setdefault('resolved_errors',[]).append({**error,'disposition':'reviewed-governance-entry-not-search-complete','source_groupid':candidate['initial_groupid'],'source_identity':expected,'policy':job['company_configuration_policy'],'original_tree':candidate['last_tree']})
    candidate['configured_search_entry_recovery']={'kind':'reviewed-governance-company-entry-v1','original_tree':candidate['last_tree'],'original_calls':len(candidate['calls'])}
    return candidate

class Workflow:
    def __init__(self,job,tab_id,invoke=None):
        validate_job(job)
        self.job=job;self.file=Path(job['workflow_path']);self.invoke=invoke or bridge.request
        if not job.get('work_order_id') or not self.file.is_absolute():raise ValueError('work-order-invalid')
        if self.file.exists():
            self.s=json.loads(self.file.read_text())
            if self.s.get('backend')!='local-dom-bridge':
                if has_side_effect_intent(job.get('resume',{})):raise ValueError('unknown-side-effect-migration-forbidden')
                old=self.s;request=job.get('recovery_request',{})
                if old.get('state')!='failed' or old.get('error_code')!='connection-unavailable' or request.get('kind')!='connection-recovery' or not request.get('id'):
                    raise ValueError('explicit-connection-recovery-required-for-backend-migration')
                if has_side_effect_intent(old):
                    raise ValueError('unknown-side-effect-migration-forbidden')
                if old.get('backend') not in (None,'codex-existing-extension') or old.get('version')!=1 or old.get('fingerprint')!=legacy_fingerprint(job):raise ValueError('work-order-conflict')
                if old.get('date_range')!={k:job['date_range'].get(k) for k in ('start','end')}:raise ValueError('work-order-conflict')
                if old.get('work_order_id')!=job['work_order_id'] or old.get('company')!=job['company'] or str(old.get('groupid'))!=str(job['groupid']):raise ValueError('work-order-conflict')
                archive=self.file.with_name('workflow-before-bridge-'+digest(self.file)[:12]+'.json')
                if not archive.exists():write_json(archive,old)
                self.s=self.initial(tab_id)
                if old.get('identity'):self.s['identity']=old['identity']
                self.s['migration']={'from':'codex-existing-extension','archive':str(archive),'sha256':digest(archive),'recovery_request':request,'at':now()}
            elif self.s.get('fingerprint')!=fingerprint(job) or self.s.get('tab_id')!=tab_id:raise ValueError('work-order-conflict')
        else:
            if has_side_effect_intent(job.get('resume',{})):raise ValueError('unknown-side-effect-migration-forbidden')
            self.s=self.initial(tab_id)
        self.configure_company_configuration()
        if self.s.get('company_search_explicit_recovery'):
            with self.search_command_lifecycle():
                self.configure_identity_contract();self.save()
        else:
            self.configure_identity_contract();self.save()
    def initial(self,tab_id):
        return {'version':1,'backend':'local-dom-bridge','work_order_id':self.job['work_order_id'],'fingerprint':fingerprint(self.job),'company':self.job['company'],'groupid':str(self.job['groupid']),'date_range':({k:self.job['date_range'][k] for k in ('start','end')} if self.job['action']=='acquire' else {}),'tab_id':tab_id,'state':'running','phase':'account','initial_groupid':None,'checkpoints':[],'calls':[],'revision':0}
    def configure_company_configuration(self):
        # Opt-in only from an immutable original job; legacy jobs load no config.
        self._company_configuration=None
        if not any(k in self.job for k in ('company_configuration_policy','company_configuration_entry')):return
        path=ROOT/'skills/workshop-director/scripts/company_configuration.py'
        if not path.is_absolute()or not path.is_file()or any(p.is_symlink()for p in(path,*path.parents))or path!=path.resolve():raise ValueError('company-config-module-origin')
        policy_ref=self.job.get('company_configuration_policy',{});policy_path=Path(policy_ref.get('path',''))
        if not policy_path.is_absolute()or not policy_path.is_file()or any(p.is_symlink()for p in(policy_path,*policy_path.parents))or digest(policy_path)!=policy_ref.get('sha256'):raise ValueError('company-config-job-policy-ref')
        policy=json.loads(policy_path.read_bytes());source=policy.get('configuration_code',{})
        configuration_timing=_configured_timing()
        if source.get('path')!=str(path):raise ValueError('company-config-module-pin')
        admitted=configuration_timing.configuration_source_material(source)
        if admitted['current']!={'path':str(path),'sha256':digest(path)}:raise ValueError('company-config-module-pin')
        module=sys.modules.get('_workflow_company_configuration')
        if module is not None and getattr(module,'__file__',None)!=str(path):raise ValueError('company-config-loaded-module-origin')
        if module is None or getattr(module,'_WORKFLOW_SOURCE_REF',None)!=admitted['current']:
            data=path.read_bytes()
            if hashlib.sha256(data).hexdigest()!=admitted['current']['sha256']:raise ValueError('company-config-module-load-drift')
            spec=importlib.util.spec_from_file_location('_workflow_company_configuration',path);module=importlib.util.module_from_spec(spec);exec(compile(data,str(path),'exec'),module.__dict__)
            if digest(path)!=admitted['current']['sha256']:raise ValueError('company-config-module-load-drift')
            module._WORKFLOW_SOURCE_REF=admitted['current'];sys.modules['_workflow_company_configuration']=module
        _,_,original=module.job_configuration(self.job)
        prior=self.s.get('company_configuration_job')
        if prior is None:
            if self.s.get('calls')or self.s.get('checkpoints')or self.s.get('revision')!=0:raise ValueError('company-config-fresh-journal-only')
            self.s['company_configuration_job']=original
        elif prior!=original:raise ValueError('company-config-original-job-changed')
        self._company_configuration=module
        if self.s.get('company_search_loading_recovery',{}).get('kind')==module.PICKER_RECOVERY_KIND:module.verify_picker_preinput_recovery(self.s,original)
    def calls_progression_safe(self):
        if not self.s.get('company_search_explicit_recovery'):return all(c.get('state')=='confirmed'for c in self.s.get('calls',[]))
        module=getattr(self,'_company_configuration',None)
        if module is None:raise ValueError('search-progression-module-required')
        original=self.s['company_configuration_job'];checked=getattr(self,'_typed_canonical_bytes',None)
        if checked is not None:
            # The command entered through strict canonical admission. Fresh
            # read-only observations may now be pending persistence in memory.
            # Check its held CAS frontier, then validate immutable history only.
            if module.regular(self.file).read_bytes()!=checked:raise ValueError('search-progression-canonical-CAS-conflict')
            saved=json.loads(checked);observational={'last_tree','transport_proof'}
            if {k:v for k,v in self.s.items()if k not in observational}!={k:v for k,v in saved.items()if k not in observational}:raise ValueError('search-progression-unpersisted-business-state')
            if self.s.get('transport_proof')!=saved.get('transport_proof')and self.s.get('transport_proof')!={'safety_version':VERSION,'safety':'DOM-only','reviewed_extension_ready':True}:raise ValueError('search-progression-unverified-transport-proof')
            return module.verify_saved_search_progression(self.s,original)is not None
        return module.search_progression_admission(self.s,original)is not None

    def renew_undelivered_confirm_operation(self,command,scope):
        """B71: an ordinary business operation lives 300 seconds; this unit sat in
        hold for hours, so the authority behind its next confirm input had already
        expired before anything was dispatched. The existing pre-enqueue renewal
        only covers a call that was refused AFTER its intent was journaled; this
        one was refused while building the command, so there is no intent to bind.
        The same rule still decides it: nothing was ever dispatched from the old
        authority (no server-intent claim, no confirm input in the journal), so it
        can be superseded once, and the expired artifact stays on disk verbatim as
        evidence. A renewal may not change a single field except its own window.
        """
        module=self._company_configuration
        old_ref=self.s.get('company_configuration_operation')
        if type(old_ref)is not dict or not old_ref.get('path'):raise ValueError('company-renewal-original-required')
        old=module.doc(old_ref)
        if old.get('purpose')!='configured-business-company-context':raise ValueError('company-renewal-ordinary-operation-required')
        if Path(old_ref['path']+'.server-intent.json').exists():raise ValueError('company-renewal-operation-consumed')
        if any(c.get('command',{}).get('kind')=='company-confirm' for c in self.s.get('calls',[])):raise ValueError('company-renewal-confirm-intent-exists')
        if has_side_effect_intent(self.s):raise ValueError('company-renewal-side-effect-intent')
        config,_,original=module.job_configuration(self.job)
        module.operation(config,old_ref,now=datetime.fromisoformat(old['issued_at']))
        if datetime.now(timezone.utc)<=datetime.fromisoformat(old['expires_at']):raise ValueError('company-renewal-not-expired')
        renewals=self.s.setdefault('company_operation_renewals',[])
        if any(r['predecessor']['sha256']==old_ref['sha256'] for r in renewals):raise ValueError('company-renewal-once-only')
        destination=self.file.parent/('configured-company-renewed-'+old_ref['sha256']+'.json')
        request,new_ref=module.business_command(self.job,command,scope,None,destination,old['key'])
        new=module.doc(new_ref);variable={'issued_at','expires_at'}
        if {k:v for k,v in old.items()if k not in variable}!={k:v for k,v in new.items()if k not in variable}or new['original_job']!=original:raise ValueError('company-renewal-operation-drift')
        renewals.append({'kind':'expired-unconsumed-ordinary-operation-successor-v1',
                         'predecessor':old_ref,'successor':new_ref,'scope':scope,'at':now()})
        self.s['company_configuration_operation']=new_ref
        # B88: this renewal no longer appends its own provenance observation.
        # The caller below appends the exact same (key, scope, operation) row on
        # every path, and the double record broke the post-switch anchor's
        # one-observation contract (read-recovery-anchor-observation-not-unique).
        # The successor artifact is already durable, so the journal must name it
        # before this returns; a crash in between would leave an authority on disk
        # that no journal points at.
        self.save()
        return request,new_ref

    def _observation_scope(self,scope):
        # B93: provenance rows always name the canonical per-tick observation
        # scope; a settle companion reply (B87 click authority, same tick and
        # window) must never replace it in company_configuration_observations.
        if scope is not None and re.fullmatch(r'confirm-settle-[0-9]+-[0-9a-f]{32}-reply\.json',Path(scope['path']).name):
            canonical=getattr(self,'_canonical_tick_scope_ref',None)
            if canonical is not None:return dict(canonical)
        return scope
    def configured_company_command(self,command):
        module=getattr(self,'_company_configuration',None)
        if module is None:return command
        company_input=(self.s['phase']=='searchCompany'and command.get('op')=='filter')or(command.get('op')=='click'and command.get('kind')in('company','company-confirm'))
        if not company_input:return command
        scope=getattr(self,'_last_tick_scope_ref',None)
        if scope is None:raise ValueError('company-config-fresh-scope-required')
        if self.s.get('company_search_explicit_recovery'):
            if not hasattr(self,'_typed_canonical_bytes'):
                module.search_progression_admission(self.s,self.s['company_configuration_job'])
                self._typed_canonical_bytes=self.file.read_bytes()
            self.save() # Persist this tick's read-only observations before strict input admission.
            request,operation=module.remaining_company_command(self.job,command,scope,self.s,self.file.parent/'configured-company-remaining-operation.json')
            if module.doc(operation)['purpose']=='configured-business-confirm-successor-v1':self.s['company_configuration_confirm_operation']=operation
            else:self.s['company_configuration_remaining_operation']=operation
            self.s.setdefault('company_configuration_observations',[]).append({'key':str(self.s['revision'])+':'+self.s['phase'],'scope':self._observation_scope(scope),'operation':operation,'at':now()})
            return request
        original=self.s['company_configuration_job'];key='configured-company:'+hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest()
        try:request,operation=module.business_command(self.job,command,scope,self.s.get('company_configuration_operation'),self.file.parent/'configured-company-operation.json',key)
        except ValueError as error:
            # Only the expired window is renewable here. Every other refusal - the
            # unrendered footer, a changed identity, a consumed opportunity - stays
            # fatal exactly as before.
            if str(error)!='company-operation-expired-or-unbounded':raise
            request,operation=self.renew_undelivered_confirm_operation(command,scope)
        self.s['company_configuration_operation']=operation
        self.s.setdefault('company_configuration_observations',[]).append({'key':str(self.s['revision'])+':'+self.s['phase'],'scope':self._observation_scope(scope),'operation':self.s['company_configuration_operation'],'at':now()})
        # B88: the single provenance append for this command - including the
        # renewal path above - is persisted here so an expired successor on disk
        # is never left unnamed in the journal.
        self.save()
        return request
    def configure_identity_contract(self):
        contract=self.job.get('identity_contract')
        if contract not in (None,'merchant-v2'):raise ValueError('identity-contract-unsupported')
        if self.s.get('identity_contract')=='merchant-v2' and contract!='merchant-v2':raise ValueError('identity-contract-downgrade-forbidden')
        if contract!='merchant-v2':return
        provider=self.job.get('provider_baseline')
        known=self.job.get('known_company_identities',{})
        bootstrap=self.job.get('identity_bootstrap') is True
        existing=self.s.get('identity_contract')=='merchant-v2'
        origin=self.s.get('identity_bootstrap_origin')
        if provider is None:
            allowed=self.job.get('allowed_groupids')
            if not bootstrap or known or self.job.get('identity_baseline') or not isinstance(allowed,list) or not allowed or any(not isinstance(g,str) or not g.isdigit() for g in allowed) or str(self.job['groupid']) not in allowed:raise ValueError('provider-baseline-required')
            if existing:
                if not origin or origin.get('allowed_groupids')!=allowed:raise ValueError('bootstrap-origin-conflict')
                pinned=self.s.get('provider_baseline')
                if pinned is None and (self.s.get('phase') not in ('account','readAccount') or self.s.get('entry_identity') or has_side_effect_intent(self.s)):raise ValueError('bootstrap-provider-unverified')
                if pinned is not None and (not isinstance(pinned,str) or not re.fullmatch(r'服务商\d+',pinned)):raise ValueError('provider-changed')
                # Resume uses the first provider pinned in this journal; a None
                # job baseline never resets it or authorizes a second bootstrap.
                return
            if self.file.exists() or self.s.get('identity') or self.s.get('entry_identity') or has_side_effect_intent(self.s):raise ValueError('bootstrap-only-fresh-empty-journal')
            self.s.update(identity_contract='merchant-v2',provider_baseline=None,
                          identity_bootstrap_origin={'allowed_groupids':allowed,'at':now(),'registry_was_empty':True})
            return
        if not isinstance(provider,str) or not re.fullmatch(r'服务商\d+',provider):raise ValueError('provider-baseline-required')
        if bootstrap and not (existing and origin and self.s.get('provider_baseline')):raise ValueError('bootstrap-config-conflict')
        if existing:
            if self.s.get('provider_baseline')!=provider:raise ValueError('provider-changed')
            return
        # A pristine new state is initialized directly; an old running ledger
        # requires an explicit, narrowly scoped audited contract upgrade.
        if self.file.exists():
            request=self.job.get('identity_contract_upgrade',{})
            if request.get('kind')!='merchant-v2' or not request.get('id'):raise ValueError('explicit-identity-contract-upgrade-required')
            scope={k:self.job[k] for k in ('company','groupid')}
            if self.s.get('work_order_id')!=self.job['work_order_id'] or self.s.get('fingerprint')!=fingerprint(self.job) or str(self.s.get('groupid'))!=str(scope['groupid']) or self.s.get('company')!=scope['company'] or self.s.get('date_range')!={k:self.job.get('date_range',{}).get(k) for k in ('start','end')}:raise ValueError('identity-upgrade-scope-conflict')
            if self.s.get('state')!='running' or has_side_effect_intent(self.s) or any(c.get('state')!='confirmed' or c.get('command',{}).get('kind') in ('export','export-submit','download') for c in self.s.get('calls',[])):raise ValueError('identity-upgrade-side-effect-or-unknown-forbidden')
            initial=self.s.get('initial_groupid')
            if not initial:raise ValueError('identity-upgrade-entry-scope-required')
            old=self.s.get('identity')
            expected=self.job.get('known_company_identities',{}).get(str(initial))
            if not expected or old!=expected or old.get('provider')!=provider:raise ValueError('identity-upgrade-entry-identity-unverified')
            for checkpoint in self.s.get('checkpoints',[]):
                if checkpoint.get('stage')=='identity' and (checkpoint.get('identity')!=old or checkpoint.get('identity_scope') not in (None,'entry') or checkpoint.get('groupid') not in (None,str(initial))):raise ValueError('identity-upgrade-checkpoint-scope-unverified')
            if self.s.get('phase') not in ('account','readAccount','context','searchCompany','chooseCompany','confirmSwitch','verifySwitch','accountAfterSwitch','identityAfterSwitch'):raise ValueError('identity-upgrade-phase-unverified')
            raw=self.file.read_bytes();sha=hashlib.sha256(raw).hexdigest();archive=self.file.with_name('workflow-before-merchant-v2-'+sha[:12]+'.json')
            if archive.exists():
                if archive.read_bytes()!=raw:raise ValueError('identity-upgrade-backup-conflict')
            else:
                with archive.open('xb') as backup:backup.write(raw)
            self.s['entry_identity']=old;self.s['entry_groupid']=str(initial)
            self.s.pop('identity',None);self.s.pop('identity_before',None)
            for checkpoint in self.s.get('checkpoints',[]):
                if checkpoint.get('stage')=='identity':checkpoint.update(identity_scope='entry',groupid=str(initial))
            self.s['identity_contract_upgrade']={'request':request,'archive':str(archive),'sha256':sha,'at':now()}
        self.s.update(identity_contract='merchant-v2',provider_baseline=provider)

    def scoped_identity_baseline(self,groupid,scope):
        if self.job.get('identity_contract')!='merchant-v2':return self.job.get('identity_baseline') if scope=='entry' else self.s.get('identity')
        groupid=str(groupid);target=str(self.job['groupid'])
        if scope not in ('entry','company') or (scope=='company' and groupid!=target):raise ValueError('identity-scope-unverified')
        known=self.job.get('known_company_identities',{}).get(groupid)
        if self.job.get('company_configuration_registry')=='configured-source-index-v2':
            module=getattr(self,'_company_configuration',None)
            if module is None:raise ValueError('company-configured-source-module-required')
            verified=module.configured_source_identity(self.job,groupid)
            if known is not None and known!=verified:raise ValueError('account-changed')
            known=verified
        if scope=='entry':
            if self.s.get('initial_groupid') is not None and groupid!=str(self.s['initial_groupid']):raise ValueError('identity-entry-scope-unverified')
            baseline=self.job.get('identity_baseline') if groupid==target else None
            if baseline and known and baseline!=known:raise ValueError('account-changed')
            expected=self.s.get('entry_identity') or known or baseline
            if expected and known and expected!=known:raise ValueError('account-changed')
            if not expected:
                origin=self.s.get('identity_bootstrap_origin')
                boot_allowed=bool(origin and groupid in origin.get('allowed_groupids',[]) and self.s.get('phase') in ('account','readAccount') and not self.s.get('entry_identity') and not has_side_effect_intent(self.s))
                if not boot_allowed and not (groupid==target and self.s.get('provider_baseline')):raise ValueError('entry-company-identity-unknown')
            return expected
        baseline=self.job.get('identity_baseline')
        if baseline and known and baseline!=known:raise ValueError('account-changed')
        expected=baseline or known
        pinned=self.s.get('identity')
        if pinned and expected and pinned!=expected:raise ValueError('account-changed')
        return pinned or expected

    def save(self):self.s['updated_at']=now();write_json(self.file,self.s)
    def remember_bridge_failure(self,command,reply,exception=None):
        # Preserve returned JSON verbatim in the durable journal. An exception
        # has no raw reply; never fabricate one from its normalized message.
        unknown=[c for c in self.s['calls'] if c.get('state')=='unknown' and c.get('command')==command]
        record={'kind':'operator-failed-bridge-observation-v1','command':command,'reply':reply,
                'raw_reply_available':reply is not None,'phase':self.s['phase'],'revision':self.s['revision'],
                'call_key':unknown[0]['key'] if len(unknown)==1 else None,'observed_at':now(),
                'exception':({'type':type(exception).__name__,'message':str(exception)} if exception is not None else None)}
        self.s.setdefault('bridge_failures',[]).append(record);self.save()
    def call(self,command):
        self._export_cluster_token=None # Any actual command attempt ends reuse.
        readonly=command.get('op') in ('tree','tabs','ping','download-status','download-reconcile','readonly-scope')
        for attempt in range(3):
            try:reply=self.invoke(command)
            except Exception as exc:
                try:self.remember_bridge_failure(command,None,exc)
                except Exception as persistence_error:raise exc from persistence_error
                raise
            if reply.get('ok'):return reply['result']
            error=str(reply.get('error','unknown'))
            try:self.remember_bridge_failure(command,reply)
            except Exception as persistence_error:raise RuntimeError('bridge-command-failed: '+error) from persistence_error
            transient=error=='Could not establish connection. Receiving end does not exist.' or bool(re.fullmatch(r'Frame with id 0 was removed\.?',error,re.I)) or bool(re.fullmatch(r'No frame with id 0 in tab \d+\.?',error,re.I))
            if not readonly or not transient or attempt==2:raise RuntimeError('bridge-command-failed: '+error)
            time.sleep(attempt+1)
    def tree(self,tab=None):
        return self.remember_tree(self.call({'op':'tree','tabId':tab or self.s['tab_id']}),tab)
    def remember_tree(self,t,tab=None):
        list(nodes(t))
        directory=self.file.parent/'bridge-evidence';directory.mkdir(exist_ok=True)
        dest=directory/(str(self.s['revision']).zfill(4)+'-'+self.s['phase']+(('-tab-'+str(tab)) if tab is not None else '')+'.json')
        if (self.s['phase']=='baselineRecordTabs'and (self.s.get('last_error',{}).get('code'),self.s.get('last_error',{}).get('message'))==('record-tab-ambiguous','record-tab-ambiguous'))or (self.s['phase']=='exportDialogProfileRequired'and self.s.get('confirmed_export_dialog_readonly_recovery')) or self.s['phase']=='confirmSwitch' or (self.s['phase']=='searchCompany' and (self.s.get('company_search_loading_recovery')or self.s.get('configured_search_entry_recovery'))) or (self.s['phase']=='verifyFilter' and (self.s.get('review_filter_loading_recovery') or self.s.get('confirmed_filter_readonly_recovery') or self.s.get('confirmed_bounded_filter_readonly_recovery') or self.s.get('review_filter_loading_reads'))) or (self.s['phase']=='pollRecords' and self.s.get('record_loading_recovery')) or (self.s['phase']=='openReviews' and self.s.get('review_entry_preinput_recovery')):
            dest=directory/(str(self.s['revision']).zfill(4)+'-'+self.s['phase']+'-recovered-'+uuid.uuid4().hex+'.json')
            # Preserve the stopped original 0002 tree, even on later failures.
        if dest.exists():dest=directory/(str(self.s['revision']).zfill(4)+'-'+self.s['phase']+'-observation-'+uuid.uuid4().hex+'.json')
        write_json(dest,t)
        self.s['last_tree']={'path':str(dest),'sha256':digest(dest)}
        return t
    def settle_company_confirmation(self,tree,tabs,current):
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit
        if self.s.get('last_error'):raise ValueError('explicit-company-confirm-read-reconciliation-required')
        original_calls=json.loads(json.dumps(self.s['calls']));deadline=time.monotonic()+86400 # B82: no artificial time shackle - wait as long as the page actually needs.
        while company_confirmation_loading(tree,self.job,self.s):
            if current['groupid']!=self.s['initial_groupid']:raise ValueError('source-company-changed-before-confirm')
            reads=self.s.setdefault('company_confirm_settle_reads',[])
            if len(reads)>=2000:raise ValueError('company-confirm-loading-exhausted-readonly')
            delay=min(.25*(2**len(reads)),2.0,deadline-time.monotonic())
            if delay<=0:raise ValueError('company-confirm-loading-deadline-readonly')
            time.sleep(delay) # Only the positively observed loading branch waits.
            scope={'op':'readonly-scope','tabId':self.s['tab_id'],'windowId':current['windowId']}
            entry={'index':len(reads),'before_tree':self.s['last_tree'],'at':now(),'command':scope,'settle_delay_seconds':delay};reads.append(entry);self.save()
            reply=self.call(scope);directory=self.file.parent/'bridge-evidence';directory.mkdir(exist_ok=True);token=uuid.uuid4().hex
            path=directory/('confirm-settle-'+str(entry['index'])+'-'+token+'-reply.json');write_json(path,reply);entry['reply']={'path':str(path),'sha256':digest(path)};self.save()
            value=decode(reply,scope['tabId'],scope['windowId']);a=context(value['before'],scope['tabId']);b=context(value['after'],scope['tabId'])
            if a['url']!=b['url'] or a['windowId']!=current['windowId'] or a['groupid'] not in (self.s['initial_groupid'],str(self.job['groupid'])) or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only' or value['tree'].get('url')!=urlsplit(a['url'])._replace(query='',fragment='').geturl():raise ValueError('company-confirm-settle-scope-changed')
            tree=value['tree'];list(nodes(tree));tabs=value['after'];current=b
            path=directory/('confirm-settle-'+str(entry['index'])+'-'+token+'-tree.json');write_json(path,tree);self.s['last_tree']={'path':str(path),'sha256':digest(path)};entry['tree']=self.s['last_tree'];self.save()
            if self.s['calls']!=original_calls:raise ValueError('company-confirm-settle-mutated-calls')
        return tree,tabs,current

    @classmethod
    def read_company_confirmation_reconciliation(cls,job,tab_id):
        # Normal __init__ saves updated_at; exact failed-SHA admission must read
        # the stopped bytes before any write, including a metadata-only save.
        validate_job(job);w=cls.__new__(cls);w.job=job;w.file=Path(job['workflow_path']);w.invoke=bridge.request
        if not w.file.is_absolute() or not w.file.is_file():raise ValueError('company-confirm-original-journal-required')
        w.s=json.loads(w.file.read_bytes())
        if w.s.get('backend')!='local-dom-bridge' or w.s.get('fingerprint')!=fingerprint(job) or w.s.get('tab_id')!=tab_id:raise ValueError('work-order-conflict')
        w.configure_identity_contract();return w

    @classmethod
    def read_export_menu_reconciliation(cls,job,tab_id):
        # Normal __init__ saves updated_at; exact failed-SHA admission must read
        # the stopped bytes before any write, including a metadata-only save.
        validate_job(job);w=cls.__new__(cls);w.job=job;w.file=Path(job['workflow_path']);w.invoke=bridge.request
        if not w.file.is_absolute() or not w.file.is_file():raise ValueError('export-menu-original-journal-required')
        w.s=json.loads(w.file.read_bytes())
        if w.s.get('backend')!='local-dom-bridge' or w.s.get('fingerprint')!=fingerprint(job) or w.s.get('tab_id')!=tab_id:raise ValueError('work-order-conflict')
        w.configure_identity_contract();return w

    def reconcile_company_confirmation_loading(self,failure_ref):
        if failure_ref.get('sha256')!=COMPANY_CONFIRM_FAILURE_SHA or digest(Path(failure_ref['path']))!=failure_ref['sha256']:raise ValueError('company-confirm-recovery-failure-not-reviewed')
        failure=json.loads(Path(failure_ref['path']).read_bytes());prior=failure['operator'];tree_ref=failure['last_tree']
        if Path(prior['path'])!=self.file or self.s.get('phase')!='confirmSwitch' or self.s.get('revision')!=5 or len(self.s.get('calls',[]))!=5:raise ValueError('company-confirm-recovery-frontier-changed')
        tree=json.loads(Path(tree_ref['path']).read_bytes())
        if digest(Path(tree_ref['path']))!=tree_ref['sha256'] or not company_confirmation_loading(tree,self.job,self.s):raise ValueError('company-confirm-recovery-tree-changed')
        previous=self.s.get('company_confirmation_loading_recovery')
        if previous:
            if previous['failure']!=failure_ref or previous['original_tree']!=tree_ref or digest(Path(previous['original_journal']['path']))!=prior['sha256'] or self.s.get('last_error'):raise ValueError('company-confirm-recovery-changed')
            return self.s
        if digest(self.file)!=prior['sha256'] or self.s.get('last_error',{}).get('message')!='semantic-locator-not-unique' or self.s.get('last_tree')!=tree_ref:raise ValueError('company-confirm-recovery-original-required')
        archive=self.file.with_name('workflow-before-confirm-loading-'+prior['sha256']+'.json');raw=self.file.read_bytes()
        if archive.exists():
            if archive.read_bytes()!=raw:raise ValueError('company-confirm-recovery-archive-conflict')
        else:
            with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        error=self.s.pop('last_error');self.s.setdefault('resolved_errors',[]).append({**error,'resolved_at':now(),'reason':'known-zero-confirm-input-loading'})
        self.s['company_confirmation_loading_recovery']={'failure':failure_ref,'original_tree':tree_ref,'original_journal':{'path':str(archive),'sha256':digest(archive)},'at':now(),'ui_action_performed':False}
        self.save();return self.s

    def owned_confirm_prenenqueue_refusal(self,entry=None):
        """B74: the bridge can refuse the confirm click before Jobs.add, and that
        reply proves the input never happened. The tick records it as
        `bridge-command-failed: <error>`, whose code is only the generic prefix,
        so a name list can never recognise it, and an older journal never got the
        pre_enqueue_rejection marker because its writer only knew the searchCompany
        shape. The evidence is therefore read from the recorded refusal itself:
        one record, this exact intent key and command, the reviewed non-delivery
        envelope, and the same error the journal kept.
        """
        if self.s.get('phase')!='confirmSwitch':return None
        entry=entry if entry is not None else self.current_call()
        if not entry or entry.get('state')!='unknown':return None
        command=entry.get('command',{})
        if command.get('op')!='click' or command.get('kind')!='company-confirm':return None
        records=[r for r in self.s.get('bridge_failures',[])if r.get('kind')=='operator-failed-bridge-observation-v1'and r.get('call_key')==entry.get('key')and r.get('command')==command and r.get('phase')==entry.get('phase')and r.get('revision')==self.s.get('revision')and r.get('exception')is None and r.get('raw_reply_available')is True and preenqueue_rejection(r.get('reply'))]
        if len(records)!=1:return None
        record=records[0];error=self.s.get('last_error')
        # After the retirement the journal no longer carries the error, and that
        # is precisely when the retry needs this proof; compare only when an
        # error is still present.
        if error is not None and (type(error)is not dict or error.get('message')!='bridge-command-failed: '+record['reply']['error']):return None
        return {'entry_key':entry['key'],'observation_index':self.s['bridge_failures'].index(record),'reply':record['reply']}

    def company_confirmation_refusal_retirable(self):
        """B75: W132m taught the exit to recognise the bridge's pre-delivery
        refusal, but the call site still entered it by the error's NAME, and that
        code is only the generic `bridge-command-failed` prefix - so the new
        branch was unreachable and the run stayed exactly where it was. The
        decision belongs to the evidence classes the exit already validates: a
        named preparation refusal, or an owned non-delivery the recorded reply
        proves. This predicate asks that question without mutating anything, so
        the call site and the exit can never disagree again.
        """
        error=self.s.get('last_error')
        if type(error)is not dict or not error.get('at'):return False
        if error.get('code')in COMPANY_CONFIRM_RETIRABLE_REFUSALS and error.get('message')==error.get('code'):return True
        return self.owned_confirm_prenenqueue_refusal()is not None

    def require_unmarked_confirmation_retry_scope(self,entry,scope):
        """B75: a refusal recorded before the marker writer knew the confirm shape
        carries no journaled source scope, so freshness cannot be compared to it.
        It is proven against the refusal's own durable observation instead: the
        retry must be authorised by a strict read written STRICTLY after that
        observation, of the exact page it is about to click. No scope, no retry.
        """
        command=entry.get('command',{})
        if self.s.get('phase')!='confirmSwitch'or command.get('op')!='click'or command.get('kind')!='company-confirm':raise ValueError('unmarked-confirmation-retry-required')
        if type(scope)is not dict or not scope.get('path')or not scope.get('sha256'):raise ValueError('preenqueue-recovery-fresh-scope-required')
        path=Path(scope['path'])
        if not path.is_file()or digest(path)!=scope['sha256']:raise ValueError('unmarked-confirmation-scope-changed')
        owned=self.owned_confirm_prenenqueue_refusal(entry)
        if owned is None:raise ValueError('preenqueue-recovery-owned-refusal-required')
        observed=self.s['bridge_failures'][owned['observation_index']].get('observed_at')
        if not observed:raise ValueError('preenqueue-recovery-observation-time-required')
        if path.stat().st_mtime<=datetime.fromisoformat(observed).timestamp():raise ValueError('preenqueue-recovery-scope-not-fresh')

    def reconcile_company_confirmation_refusal(self):
        # B70/B72: the confirm guard refuses any journal still carrying a
        # last_error, and nothing in the tree could clear one, so a refusal raised
        # while PREPARING the confirm input locked the unit permanently. The first
        # version of this exit named a single code, so it simply moved the lock to
        # the next refusal's name. This one retires a closed set of preparation
        # refusals, each of which already has its own fix, and retires each code
        # at most once: the same code coming back means the fix did not hold and
        # must stay fatal. It performs no input, adds no call and no revision; the
        # retired refusal keeps its own time and tree as evidence.
        error=self.s.get('last_error')
        if type(error)is not dict or not error.get('at'):raise ValueError('company-confirm-refusal-not-retirable')
        named=error.get('code')in COMPANY_CONFIRM_RETIRABLE_REFUSALS and error.get('message')==error.get('code')
        # B74: a refusal the bridge emitted before delivery has no dedicated code
        # of its own - the tick only keeps the generic bridge-command-failed
        # prefix - so its evidence is the recorded non-delivery reply, which also
        # proves the click never happened.
        owned=None if named else self.owned_confirm_prenenqueue_refusal()
        if not named and owned is None:raise ValueError('company-confirm-refusal-not-retirable')
        if self.s.get('phase')!='confirmSwitch' or self.s.get('state')!='running':raise ValueError('company-confirm-refusal-frontier-changed')
        if has_side_effect_intent(self.s):raise ValueError('company-confirm-refusal-intent-conflict')
        # B77: a call whose exact key already carries a retirement record proved
        # nothing was dispatched for it, so it is not the unsettled intent this
        # guard exists to protect; only the remaining calls can be.
        raw=[c for c in self.s.get('calls',[])if c.get('state')not in('confirmed','rejected')]
        proven=[c for c in raw if owned_undelivered_confirm_call(self.s,c)]
        if owned is None and [c for c in raw if c not in proven]:raise ValueError('company-confirm-refusal-unknown-intent')
        if owned is not None and (len(raw)!=1 or raw[0].get('key')!=owned['entry_key']):raise ValueError('company-confirm-refusal-unknown-intent')
        retired=[e for e in self.s.get('resolved_errors',[])if e.get('message')==error.get('message')]
        if retired:raise ValueError('company-confirm-refusal-already-retired')
        tree_ref=self.s.get('last_tree')
        if type(tree_ref)is not dict or not tree_ref.get('path')or not Path(tree_ref['path']).is_file():raise ValueError('company-confirm-refusal-original-tree-required')
        if digest(Path(tree_ref['path']))!=tree_ref.get('sha256'):raise ValueError('company-confirm-refusal-original-tree-changed')
        record={**error,'resolution':COMPANY_CONFIRM_REFUSAL_KIND,'original_tree':tree_ref,'original_calls':len(self.s['calls']),'disposition':'preparation-refusal-retired-not-confirm-complete','resolved_at':now()}
        if owned is not None:record['non_delivery']=owned
        self.s.setdefault('resolved_errors',[]).append(record)
        recovery={'kind':COMPANY_CONFIRM_REFUSAL_KIND,'code':error['code'],'original_tree':tree_ref,'original_calls':len(self.s['calls']),'at':now(),'ui_action_performed':False}
        if owned is not None:recovery['non_delivery']=owned
        self.s['company_confirm_refusal_recoveries']=list(self.s.get('company_confirm_refusal_recoveries',[]))+[recovery]
        self.s.pop('last_error')
        self.save();return self.s

    def reconcile_export_menu_hover(self,failure_ref):
        """One supervised re-hover after the reviewed natural transient where the
        confirmed export hover produced no dropdown panel before the profile
        read. Verbatim original journal archive; canonical go() transform."""
        if failure_ref.get('sha256')!=EXPORT_MENU_FAILURE_SHA or digest(Path(failure_ref['path']))!=failure_ref['sha256']:raise ValueError('export-menu-recovery-failure-not-reviewed')
        failure=json.loads(Path(failure_ref['path']).read_bytes());prior=failure['operator'];tree_ref=failure['last_tree']
        phase=self.s.get('phase');fresh=Path(prior['path'])==self.file and phase=='exportProfileRequired' and self.s.get('last_error',{}).get('code')=='semantic-locator-not-unique' and self.s.get('last_error',{}).get('message')=='semantic-locator-not-unique'
        settled=Path(prior['path'])==self.file and phase=='openExportMenu' and not self.s.get('last_error')
        if not (fresh or settled):raise ValueError('export-menu-recovery-frontier-changed')
        tree=json.loads(Path(tree_ref['path']).read_bytes())
        if digest(Path(tree_ref['path']))!=tree_ref['sha256'] or self.s.get('last_tree')!=tree_ref:raise ValueError('export-menu-recovery-tree-changed')
        triggers=[n for n in nodes(tree) if n.get('name')=='导出' and 'byted-popper-trigger-hover' in (n.get('attributes',{}).get('class','') or '').split()]
        items=[n for n in nodes(tree) if n.get('name') in ('导出评价','评价导出记录')]
        if len(triggers)!=1 or items:raise ValueError('export-menu-recovery-tree-shape')
        previous=self.s.get('export_menu_hover_recovery')
        if previous:
            if previous['failure']!=failure_ref or previous['original_tree']!=tree_ref or digest(Path(previous['original_journal']['path']))!=prior['sha256'] or self.s.get('last_error'):raise ValueError('export-menu-recovery-changed')
            return self.s
        if digest(self.file)!=prior['sha256']:raise ValueError('export-menu-recovery-journal-drift')
        archive=self.file.with_name('workflow-before-export-menu-'+prior['sha256']+'.json');raw=self.file.read_bytes()
        if archive.exists():
            if archive.read_bytes()!=raw:raise ValueError('export-menu-recovery-archive-conflict')
        else:
            with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        self.s['export_menu_hover_recovery']={'failure':failure_ref,'original_tree':tree_ref,'original_journal':{'path':str(archive),'sha256':digest(archive)},'at':now(),'ui_action_performed':False}
        self.go('openExportMenu');return self.s

    def advance_date_restore(self,snapshot,current):
        # Exact ready date keeps the old path and does not even load recovery code.
        value=review_filter_fields(snapshot['tree'])['评价时间'].get('attributes',{}).get('value')
        expected=self.s['date_range']['start']+' ~ '+self.s['date_range']['end']
        if not self.s.get('review_filter_date_restore')and value==expected:return False
        if self.s.get('state')!='running' or self.s.get('phase')!='verifyFilter':raise ValueError('date-restore-live-phase-or-error')
        sys.path.insert(0,str(ROOT/'skills/negative-review-complaints/scripts'))
        import initial_ledger_recovery as recovery
        field=recovery.DATE_RESTORE_FIELD
        def evidence(value,name):
            raw=(json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode();directory=self.file.parent/'review-filter-date-observations';path=directory/(name+'-'+hashlib.sha256(raw).hexdigest()+'.json');return recovery.immutable_bytes(path,raw)
        error=self.s.get('last_error')
        if error:
            # The transform resolves a lost date: bounded waits exhausted, then
            # the page loaded with an empty date. When the date epoch is already
            # complete the exhaustion belongs to the filter-result wait, not to
            # the date; the settle rearm archives that error verbatim, so the
            # transform must not consume it.
            epoch=self.s.get('review_filter_date_restore')
            if not(type(error)is dict and set(error)=={'at','code','message'} and error['code']==error['message']=='review-filter-loading-exhausted' and type(epoch)is dict and epoch.get('complete')):
                scope_ref=evidence(snapshot,'scope');original_ref=evidence(self.s,'loading-error-original-state')
                self.s=recovery.date_restore_loading_error_transform(self.job,self.s,snapshot,scope_ref,original_ref)
                self.save() # Typed command CAS before any new epoch intent or input.
        if not self.s.get(field):
            scope_ref=evidence(snapshot,'scope');plan=recovery.date_restore_contract(self.job,self.s,snapshot,scope_ref,evidence(self.s,'original-state'));base=self.file.parent/'review-filter-date-restores'/hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest();plan_ref=recovery.immutable_bytes(base/'intent.json',(json.dumps(plan,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode());self.s[field]={'plan':plan_ref,'key':'filter-date-restore:'+base.name,'actions':{}};self.save()
        plan,sequence,done=recovery.date_restore_epoch_verify(self.job,self.s);epoch=self.s[field];_,value=recovery.date_restore_scope(self.job,self.s,snapshot,plan['binding'])
        if epoch.get('complete'):
            if value!=expected:raise ValueError('date-restore-budget-exhausted-or-conflict')
            return False
        if len(done)==len(sequence):
            if value!=expected:raise ValueError('date-restore-final-date-unverified')
            epoch['complete']=evidence(snapshot,'complete');self.save();return False
        if value!='':raise ValueError('date-restore-nonempty-conflict')
        stage=sequence[len(done)];tree=snapshot['tree']
        if stage=='open':
            if recovery.date_restore_picker(tree,self.s['date_range']):raise ValueError('date-restore-unexpected-open-picker')
            target=review_filter_fields(tree)['评价时间']
        else:
            if not recovery.date_restore_picker(tree,self.s['date_range']):raise ValueError('date-restore-matching-picker-required')
            target=calendar_day(tree,self.s['date_range']['start'if stage=='start'else'end'])
        command={'op':'click','tabId':self.s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'filter'};key=epoch['key']+':'+stage
        if stage not in epoch['actions']:
            intent={'plan':epoch['plan'],'stage':stage,'key':key,'scope':evidence(snapshot,'before-'+stage),'command':command,'at':now()};path=Path(epoch['plan']['path']).with_name(stage+'-intent.json');epoch['actions'][stage]=recovery.o.ref(path)if path.exists()else recovery.immutable_bytes(path,(json.dumps(intent,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode());self.save();recovery.date_restore_epoch_verify(self.job,self.s)
        else:
            intent=recovery.o.doc(epoch['actions'][stage])
            if intent['command']!=command:raise ValueError('date-restore-prepared-command-changed')
        self.once(command,intent_key=key);self.save();return True

    def review_filter_loading_round_still_loading(self,reads):
        """A spent wait round is a slow page, never a result and never a zero.

        B80: the exhausted budget was only reusable after a completed date
        restore, so the first slow paint - the page really was still rendering
        when the twenty-second window closed, and it rendered correctly a moment
        later - pinned the unit forever. A round is rearmable only when its own
        last read still resolves, still carries the requested filter values,
        still refuses any store or zero claim and is still loading; every other
        shape stays fail-closed. No UI action is taken or authorised here.
        """
        last=reads[-1]if type(reads)is list and reads else None
        tree_ref=last.get('tree')if type(last)is dict else None
        budget=self.s.get('review_filter_loading_budget')
        if type(tree_ref)is not dict or type(budget)is not dict:return False
        if len(reads)!=budget.get('maximum_reads'):return False
        expiry=budget.get('deadline_monotonic')
        if not isinstance(expiry,(int,float)):return False
        path=Path(tree_ref.get('path')or'')
        if not path.is_file()or digest(path)!=tree_ref.get('sha256'):return False
        from review_filter_loading import is_loading,validate_filter_values,validate_pending_store_scope
        tree=json.loads(path.read_bytes())
        try:
            require_no_review_system_error(tree)
            validate_pending_store_scope(tree)
            validate_filter_values(tree,self.s['date_range'])
            if not is_loading(tree):return False
        except ValueError:return False
        return time.clock_gettime(time.CLOCK_MONOTONIC)>=expiry

    def verified_review_filter_settled(self,t,tabs,current,desired):
        """B91: the 已筛选 N 条 label renders after the loading mask clears, so a
        settled-looking page can still miss the count the filter verdict needs.
        The fast path is the old strict read; only a positively missing count
        enters bounded read-only settling (same budget shape as the confirm
        settle), re-reading until exactly one count value is on the page. Any
        other verdict error, a scope change or a service error stays fatal."""
        from dom_evidence import verified_review_filter
        try:return verified_review_filter(t,desired)
        except ValueError as e:
            if str(e)!='page-count-unverified':raise
        t,tabs,current=self.settle_review_page_count(t,tabs,current,desired)
        return verified_review_filter(t,desired)

    def settle_review_page_count(self,t,tabs,current,desired):
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit
        from dom_evidence import verified_review_filter
        require_no_review_system_error(t)
        original_calls=json.loads(json.dumps(self.s['calls']))
        reads=self.s.setdefault('review_page_count_reads',[])
        deadline=time.monotonic()+86400 # B82: no artificial time shackle - wait as long as the page actually needs.
        while True:
            try:
                verified_review_filter(t,desired);return t,tabs,current
            except ValueError as e:
                if str(e)!='page-count-unverified':raise
            if current['groupid'] not in (self.s['initial_groupid'],str(self.job['groupid'])):raise ValueError('review-page-count-scope-changed')
            if len(reads)>=2000:raise ValueError('review-page-count-exhausted-readonly')
            delay=min(.25*(2**len(reads)),2.0,deadline-time.monotonic())
            if delay<=0:raise ValueError('review-page-count-deadline-readonly')
            time.sleep(delay) # Only the positively missing-count branch waits.
            scope={'op':'readonly-scope','tabId':self.s['tab_id'],'windowId':current['windowId']}
            entry={'index':len(reads),'at':now(),'command':scope,'settle_delay_seconds':delay};reads.append(entry);self.save()
            reply=self.call(scope);directory=self.file.parent/'bridge-evidence';directory.mkdir(exist_ok=True);token=uuid.uuid4().hex
            path=directory/('page-count-settle-'+str(entry['index'])+'-'+token+'-reply.json');write_json(path,reply);entry['reply']={'path':str(path),'sha256':digest(path)};self.save()
            value=decode(reply,scope['tabId'],scope['windowId']);a=context(value['before'],scope['tabId']);b=context(value['after'],scope['tabId'])
            if a['url']!=b['url'] or a['windowId']!=current['windowId'] or a['groupid'] not in (self.s['initial_groupid'],str(self.job['groupid'])) or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only' or value['tree'].get('url')!=urlsplit(a['url'])._replace(query='',fragment='').geturl():raise ValueError('review-page-count-scope-changed')
            t=value['tree'];list(nodes(t));require_no_review_system_error(t);tabs=value['after'];current=b
            path=directory/('page-count-settle-'+str(entry['index'])+'-'+token+'-tree.json');write_json(path,t);self.s['last_tree']={'path':str(path),'sha256':digest(path)};entry['tree']=self.s['last_tree'];self.save()
            if self.s['calls']!=original_calls:raise ValueError('review-page-count-mutated-calls')

    def settle_review_filter(self,t,current):
        from readonly_tick_snapshot import decode
        from review_filter_loading import is_loading as review_filter_loading, validate_filter_values, validate_pending_store_scope
        # A visible service error must not spend the loading budget or certify zero.
        require_no_review_system_error(t)
        # A ready ordinary snapshot adds no calls or artificial delay.
        if not review_filter_loading(t):return t
        validate_filter_values(t,self.s['date_range']);validate_pending_store_scope(t)
        scope={'op':'readonly-scope','tabId':self.s['tab_id'],'windowId':current['windowId']}
        # Bound the number of fresh observations, independently of bridge latency.
        # Backoff totals 7s; real request timeout is bounded by remaining20s.
        # Ready fastpath above has no added read or wait; originalouter unchanged.
        reads=self.s.setdefault('review_filter_loading_reads',[])
        if type(reads)is not list or len(reads)>3 or [r.get('attempt')for r in reads]!=list(range(len(reads))):raise ValueError('review-filter-loading-read-prefix')
        if len(reads)>=3:
            # A spent round may be rearmed at most twice, and only when it ended
            # on a page that was still rendering rather than on a verdict: the
            # exhausted round (reads, budget, last_error, last_tree) is archived
            # verbatim to bridge-evidence and a fresh budget is issued. The date
            # epoch path keeps its single rearm; B80 adds the page-still-loading
            # path, which is the only one available when no date restore ran. Any
            # other error, an absent budget or a round spent on a settled page
            # stays fail-closed.
            rounds=self.s.get('review_filter_loading_rounds',1)
            error=self.s.get('last_error');epoch=self.s.get('review_filter_date_restore')
            exact=type(error)is dict and set(error)=={'at','code','message'} and error['code']==error['message']=='review-filter-loading-exhausted'
            if not exact or self.s.get('review_filter_loading_budget')is None:raise ValueError('review-filter-loading-exhausted')
            after_date=type(epoch)is dict and epoch.get('complete') and rounds<2
            still_loading=rounds<3 and self.review_filter_loading_round_still_loading(reads)
            if not(after_date or still_loading):raise ValueError('review-filter-loading-exhausted')
            directory=self.file.parent/'bridge-evidence';token=uuid.uuid4().hex
            archive={'kind':'review-filter-loading-rearm-v1','mode':'date-epoch'if after_date else'page-still-loading','round':rounds,'archived_at':now(),'reads':reads,'budget':self.s['review_filter_loading_budget'],'last_error':error,'last_tree':self.s.get('last_tree')}
            rawpath=directory/('filter-settle-rearm-'+token+'.json');write_json(rawpath,archive);ref={'path':str(rawpath),'sha256':digest(rawpath)}
            self.s.setdefault('review_filter_loading_rearms',[]).append(ref)
            self.s.setdefault('resolved_errors',[]).append({**error,'resolved_at':now(),'resolution':'review-filter-loading-rearm-v1','round':rounds,'archive':ref})
            self.s['review_filter_loading_reads']=[];self.s.pop('review_filter_loading_budget',None);self.s.pop('last_error',None);self.s['review_filter_loading_rounds']=rounds+1;self.save()
            reads=[]
        if any(r.get('command')!=scope for r in reads):raise ValueError('review-filter-loading-read-scope-prefix')
        # Existing pending budget only: never a second group of reads. CLOCK_
        # MONOTONIC is system-wide on supported runtime, unlike process-relative
        # time.monotonic on Python3.9/macOS. Old partial rows consume their index.
        clock=lambda:time.clock_gettime(time.CLOCK_MONOTONIC)
        started=clock();last_clock=started
        wall=lambda:datetime.fromisoformat(now()).timestamp()
        budget=self.s.get('review_filter_loading_budget')
        if budget is None:
            origin=datetime.fromisoformat(reads[0]['at']).timestamp()if reads else wall()
            budget={'kind':'bounded-filter-readonly-wait-v1','clock':'system-clock-gettime-CLOCK_MONOTONIC-v1','started_monotonic':started,'deadline_monotonic':started+86400.0,'started_wall':origin,'deadline_wall':origin+86400.0,'maximum_reads':2000}
            self.s['review_filter_loading_budget']=budget;self.save()
        if set(budget)!={'kind','clock','started_monotonic','deadline_monotonic','started_wall','deadline_wall','maximum_reads'}or budget.get('kind')!='bounded-filter-readonly-wait-v1'or budget.get('maximum_reads')!=2000 or budget.get('clock')!='system-clock-gettime-CLOCK_MONOTONIC-v1'or abs((budget['deadline_monotonic']-budget['started_monotonic'])-86400.0)>1e-6 or abs((budget['deadline_wall']-budget['started_wall'])-86400.0)>1e-6:raise ValueError('review-filter-loading-budget-binding')
        def remaining():
            nonlocal last_clock
            current_clock=clock();current_wall=wall()
            if not all(__import__('math').isfinite(v)for v in(current_clock,current_wall,budget['deadline_monotonic'],budget['deadline_wall']))or current_clock<last_clock or current_clock<budget['started_monotonic']or current_wall<budget['started_wall']:raise ValueError('review-filter-loading-clock-regressed')
            last_clock=current_clock;left=min(budget['deadline_monotonic']-current_clock,budget['deadline_wall']-current_wall)
            if left<=0:raise ValueError('review-filter-loading-exhausted')
            return left
        for index in range(len(reads),2000):
            if not review_filter_loading(t):return t
            delay=min(float(2**index),5.0) # capped backoff; budget is no longer the shackle (B82).
            if remaining()<=delay:raise ValueError('review-filter-loading-exhausted')
            time.sleep(delay);remaining()
            self.s.setdefault('review_filter_loading_reads',[]).append({'before_tree':self.s['last_tree'],'at':now(),'command':scope,'attempt':index});self.save()
            try:reply=self.invoke(scope,timeout=remaining())
            except Exception as error:
                self.s['review_filter_loading_reads'][-1]['exception']={'type':type(error).__name__,'message':str(error),'at':now()};self.save();raise
            directory=self.file.parent/'bridge-evidence';token=uuid.uuid4().hex;rawpath=directory/('filter-settle-'+token+'-reply.json');write_json(rawpath,reply);entry=self.s['review_filter_loading_reads'][-1];entry['reply']={'path':str(rawpath),'sha256':digest(rawpath)};self.save();remaining()
            if not reply.get('ok'):
                error=str(reply.get('error','unknown'));transient=(error=='Could not establish connection. Receiving end does not exist.' or re.fullmatch(r'Frame with id 0 was removed\.?',error,re.I) or re.fullmatch(r'No frame with id 0 in tab \d+\.?',error,re.I))
                if transient:continue
                raise RuntimeError('bridge-command-failed: '+error)
            value=decode(reply['result'],scope['tabId'],scope['windowId']);before=context(value['before'],scope['tabId'],self.job['groupid']);after=context(value['after'],scope['tabId'],self.job['groupid'])
            if before['url']!=after['url'] or before['url']!=current['url'] or value['tree'].get('url')!='https://life.douyin.com/p/life_comment/management' or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only':raise ValueError('review-filter-settle-scope-changed')
            t=value['tree'];list(nodes(t))
            treepath=directory/('filter-settle-'+token+'-tree.json');write_json(treepath,t);self.s['last_tree']={'path':str(treepath),'sha256':digest(treepath)};entry['tree']=self.s['last_tree'];self.save()
            require_no_review_system_error(t)
            validate_pending_store_scope(t)
            identity(t,self.scoped_identity_baseline(self.job['groupid'],'company'))
            # Recheck exact requested filter values even while result is loading.
            validate_filter_values(t,self.s['date_range'])
            
        remaining()
        if review_filter_loading(t):raise ValueError('review-filter-loading-exhausted')
        return t

    def settle_export_menu(self,tree,required=EXPORT_MENU_ITEMS):
        # W131c: the confirmed export hover opens a dropdown that renders late
        # (B56/W126). Two-way split (Easel _do_delete discipline): an absent
        # trigger is ACTION-level, a present trigger with an incomplete panel
        # is DATA-level. A tick that already sees the full panel costs zero
        # extra reads, so the normal path stays byte-identical; only an
        # unready panel opens one bounded window that re-reads the page.
        probe=export_menu_probe(tree)
        if probe is None:return 'unreadable',None
        if probe['triggers']>1:return 'ambiguous',probe
        def satisfied(p):return all(label in p['items'] for label in required)
        if satisfied(probe):
            # Original strictness is kept: a rendered label that is disabled or
            # has no selector is still element-not-ready, not "ready".
            for label in required:exact(tree,label)
            return 'ready',probe
        cache={'at':time.monotonic(),'tree':tree,'probe':probe}
        def current():
            if time.monotonic()-cache['at']>=.05:
                fresh=self.tree();fresh_probe=export_menu_probe(fresh)
                if fresh_probe is not None:cache.update(tree=fresh,probe=fresh_probe,at=time.monotonic())
            return cache['tree'],cache['probe']
        def items():
            # The contract is "every required item", not "some panel": a
            # partially rendered dropdown is still unloading data.
            got=[label for label in required if label in current()[1]['items']]
            return got if len(got)==len(required) else []
        try:state,_=wait_rendered(lambda:current()[1]['triggers']==1,items,2.0,.25)
        except ValueError as error:
            if str(error)!='wait-rendered-items-unconfirmed':raise
            return 'incomplete',current()[1]
        final_tree,final_probe=current()
        if state=='ready':
            for label in required:exact(final_tree,label)
            return 'ready',final_probe
        return state,final_probe

    def retry_export_menu_hover(self,start_tree):
        # An absent trigger is an ACTION failure, so exactly one supervised
        # re-hover is allowed - and only from a trigger this workflow itself
        # resolved on the tick's own tree. The second absence keeps the
        # original code so the reviewed reconciliation gate remains the only
        # escalation path.
        trigger_node=lambda t:unique([n for n in nodes(t) if n.get('name')=='导出' and 'byted-popper-trigger-hover' in (n.get('attributes',{}).get('class','') or '').split()])
        previous=self.s.get('export_menu_hover_retry')
        if previous:
            self.s['export_menu_hover_retry']={**previous,'absent_again_at':now(),'attempts':previous.get('attempts',1)+1}
            self.save()
            for label in EXPORT_MENU_ITEMS:exact(start_tree,label)
            raise ValueError('semantic-locator-not-unique')
        trigger=trigger_node(start_tree)
        self.mutate('hover',trigger,'export')
        self.s['export_menu_hover_retry']={'at':now(),'evidence':self.s.get('last_tree'),'trigger_selector':trigger.get('selector'),
                                           'ui_action_performed':True,'attempts':1,'reason':'export-menu-trigger-absent'}
        self.s['waiting_for']='export-menu-hover-retried';self.save()
        return self.s

    def settle_export_dialog(self,tree,current):
        from readonly_tick_snapshot import decode
        try:verified_export_dialog(tree,self.s['date_range'],require_dates=False);return tree
        except ValueError as error:
            if str(error)!='export-store-scope-unverified'or not export_dialog_scope_pending(tree,self.s['date_range']):raise
        self._export_cluster_extra_read=True;self._export_cluster_blocked=True;self._export_cluster_token=None
        calls=self.s.get('calls',[])
        if not calls or any(c.get('state')!='confirmed'for c in calls)or calls[-1].get('phase')!='openExportDialog'or calls[-1].get('command',{}).get('op')!='click'or calls[-1]['command'].get('kind')!='export'or calls[-1]['command'].get('tabId')!=self.s['tab_id']or any(self.s.get(k)for k in ('exportPending','downloadPending','result')):raise ValueError('export-dialog-pending-input-state')
        def validate(t):
            identity(t,self.scoped_identity_baseline(self.job['groupid'],'company'));all_store_scope(t)
            if verified_review_filter(t,self.s['date_range'])['page_filtered']!=self.s['page_filtered']:raise ValueError('export-dialog-main-filter-changed')
        validate(tree);command={'op':'readonly-scope','tabId':self.s['tab_id'],'windowId':current['windowId']}
        for index in range(2000): # B82: reads until the store scope settles; no 3-read shackle.
            time.sleep(min(.25*(2**index),2.0));entry={'before_tree':self.s['last_tree'],'command':command,'attempt':index,'at':now()};self.s.setdefault('export_dialog_loading_reads',[]).append(entry);self.save()
            reply=self.invoke(command);directory=self.file.parent/'bridge-evidence';token=uuid.uuid4().hex;rp=directory/('export-dialog-settle-'+token+'-reply.json');write_json(rp,reply);entry['reply']={'path':str(rp),'sha256':digest(rp)};self.save()
            if not reply.get('ok'):raise RuntimeError('bridge-command-failed: '+str(reply.get('error','unknown')))
            value=decode(reply['result'],command['tabId'],command['windowId']);before=context(value['before'],command['tabId'],self.job['groupid']);after=context(value['after'],command['tabId'],self.job['groupid'])
            if before['url']!=after['url']or before['url']!=current['url']or value['tree'].get('url')!='https://life.douyin.com/p/life_comment/management'or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only':raise ValueError('export-dialog-settle-scope-changed')
            tree=value['tree'];validate(tree);tp=directory/('export-dialog-settle-'+token+'-tree.json');write_json(tp,tree);entry['tree']={'path':str(tp),'sha256':digest(tp)};self.s['last_tree']=entry['tree'];self.save()
            try:verified_export_dialog(tree,self.s['date_range'],require_dates=False);return tree
            except ValueError as error:
                if str(error)!='export-store-scope-unverified'or not export_dialog_scope_pending(tree,self.s['date_range']):raise
        raise ValueError('export-dialog-store-scope-loading-exhausted')

    def _resolve_record_row(self,record_tree,desired):
        # B92: first page resolution by submission window; when nothing new was
        # created and a verified identity binding exists (a provably
        # pre-existing artifact for the exact range, see
        # export-artifact-identity-recovery-v1), resolve by identity instead.
        proof=submitted_export_record(record_tree,desired,self.s['baseline_records'],self.s['submitted_at'])
        row=proof['row']
        if row is None:
            bound=self.s.get('generated_record')
            if isinstance(bound,dict) and bound.get('bound_by')=='export-artifact-identity-recovery-v1':
                from dom_evidence import bound_generated_record
                resolved=bound_generated_record(record_tree,desired,self.s['baseline_records'],bound);row=resolved['row']
        return proof,row
    def settle_record_page(self,tree,record_tab):
        from urllib.parse import urlsplit
        from export_record_page_recovery import is_loading,loading_scope
        from readonly_tick_snapshot import decode
        if not is_loading(tree):return self._settle_stable_record_tree(tree,record_tab)
        scope=loading_scope(self.job,self.s)
        if record_tab['url']!=scope['url'] or record_tab['windowId']!=scope['window_id']:raise ValueError('record-loading-original-scope-changed')
        # B82: no artificial time shackle - the record microapp mounts when it
        # mounts (observed >300s across attempts 26-32 on 2026-11-03, company 2).
        # Wait in capped-backoff reads until the page is actually ready.
        deadline=time.monotonic()+86400
        for index in range(2000):
            if not is_loading(tree):break
            delay=min(.25*(2**index),2.0)
            if time.monotonic()+delay>deadline:raise ValueError('record-page-loading-exhausted')
            time.sleep(delay);command={'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']}
            entry={'at':now(),'command':command,'before_tree':self.s['last_tree'],'attempt':index};self.s.setdefault('record_loading_reads',[]).append(entry);self.save()
            reply=self.invoke(command);directory=self.file.parent/'bridge-evidence';token=uuid.uuid4().hex;rp=directory/('record-settle-'+token+'-reply.json');write_json(rp,reply);entry['reply']={'path':str(rp),'sha256':digest(rp)};self.save()
            if reply.get('ok')is not True:raise RuntimeError('bridge-command-failed: '+str(reply.get('error','unknown')))
            value=decode(reply['result'],scope['tab_id'],scope['window_id'])
            for side in ('before','after'):
                observed=context(value[side],scope['tab_id'],self.job['groupid'],record=True)
                if observed['url']!=scope['url'] or observed.get('windowId')!=scope['window_id']:raise ValueError('record-loading-scope-changed')
            tree=value['tree'];list(nodes(tree))
            if tree.get('url')!=urlsplit(scope['url'])._replace(query='',fragment='').geturl() or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only':raise ValueError('record-loading-scope-changed')
            tp=directory/('record-settle-'+token+'-tree.json');write_json(tp,tree);entry['tree']={'path':str(tp),'sha256':digest(tp)};self.s['last_tree']=entry['tree'];self.save()
        if is_loading(tree):raise ValueError('record-page-loading-exhausted')
        return self._settle_stable_record_tree(tree,record_tab)
    def _record_settle_read(self,record_tab):
        # One extra readonly snapshot under the same evidence discipline as the
        # loading loop: reply and tree bytes are written before they are used.
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit
        command={'op':'readonly-scope','tabId':record_tab['tabId'],'windowId':record_tab['windowId']}
        reply=self.invoke(command);directory=self.file.parent/'bridge-evidence';token=uuid.uuid4().hex
        rp=directory/('record-stable-'+token+'-reply.json');write_json(rp,reply)
        if reply.get('ok')is not True:raise RuntimeError('bridge-command-failed: '+str(reply.get('error','unknown')))
        value=decode(reply['result'],record_tab['tabId'],record_tab['windowId'])
        tree=value['tree'];list(nodes(tree))
        if tree.get('url')!=urlsplit(record_tab['url'])._replace(query='',fragment='').geturl() or value['ping'].get('version')!=VERSION or value['ping'].get('safety')!='DOM-only':raise ValueError('record-stable-scope-changed')
        tp=directory/('record-stable-'+token+'-tree.json');write_json(tp,tree)
        return tree,{'command':command,'reply':{'path':str(rp),'sha256':digest(rp)},'tree':{'path':str(tp),'sha256':digest(tp)}}
    def _settle_stable_record_tree(self,tree,record_tab):
        # W131b (blueprint P1/P2, Easel account_stats._poll_stable): a vanished
        # loading mask is not a filled table (B57) and object columns fill
        # asynchronously (B36/W101). The tree becomes a baseline only when two
        # independent readonly readings agree; an unrendered body (None) is
        # never a value, and an unsettled page returns None so the caller can
        # wait instead of persisting a fake baseline.
        budget=1.5;interval=.2
        end=time.monotonic()+budget;current=record_page_fingerprint(tree)
        for attempt in range(2):
            if time.monotonic()+interval>end:break
            time.sleep(interval)
            tree,proof=self._record_settle_read(record_tab)
            observed=record_page_fingerprint(tree);settled=current is not None and observed==current
            entry={'at':now(),'attempt':attempt,'fingerprint_before':current,'fingerprint_after':observed,'settled':settled,**proof}
            self.s.setdefault('record_settle_reads',[]).append(entry);self.s['last_tree']=proof['tree'];self.save()
            if settled:return tree
            current=observed
        return None

    def preenqueue_recovery_entry(self):
        entry=self.current_call()
        if self.s.get('state')!='running'or self.s.get('phase')not in('searchCompany','confirmSwitch')or not entry or entry.get('state')!='unknown' or has_side_effect_intent(self.s):return None
        if [x for x in self.s['calls']if x.get('state')=='unknown']!=[entry]:return None
        proof=entry.get('pre_enqueue_rejection')
        if type(proof)is not dict or set(proof)!={'kind','observation_index','binding','source_scope'}or proof['kind']!='owned-preenqueue-no-delivery-v1':
            # B74: an older confirm refusal carries no marker, because the writer
            # only knew the searchCompany shape; its non-delivery reply is still
            # on disk, so the same one-shot retry is still justified.
            return entry if self.owned_confirm_prenenqueue_refusal(entry)is not None and not entry.get('pre_enqueue_recovery_attempted')else None
        index=proof['observation_index'];records=self.s.get('bridge_failures',[])
        if type(index)is not int or not 0<=index<len(records):return None
        record=records[index];command=entry['command']
        # B74: the same proof admits the confirm click; the phase decides which
        # input shape is legitimate, so a filter can never arrive as a click or
        # the other way round.
        shape=((command.get('op')=='filter'and command.get('kind')=='filter')if self.s['phase']=='searchCompany'else(command.get('op')=='click'and command.get('kind')=='company-confirm'))
        # B79: an expired ordinary operation may have been renewed (B71) between
        # the pre-enqueue refusal and this recovery, so the journal's current
        # operation is the renewal successor of the intent's companyRequest.
        # Accept that journaled successor exactly as renew_undelivered_company_operation
        # does; anything else stays fatal.
        if not shape or not command.get('companyRequest')or (command['companyRequest']!=self.s.get('company_configuration_operation') and not self.renewal_chain_links(command['companyRequest'],self.s.get('company_configuration_operation'))):return None
        if record.get('kind')!='operator-failed-bridge-observation-v1'or record.get('command')!=command or record.get('call_key')!=entry['key']or record.get('phase')!=entry['phase']or record.get('revision')!=self.s['revision']or record.get('exception')is not None or record.get('raw_reply_available')is not True or not preenqueue_rejection(record.get('reply')):return None
        if proof['binding']!=_preenqueue_binding(entry,record,proof['source_scope'])or entry.get('pre_enqueue_recovery_attempted'):return None
        error=self.s.get('last_error')
        if error and error.get('message')!='bridge-command-failed: '+record['reply']['error']:return None
        return entry

    def renewal_chain_links(self,predecessor,successor):
        """B79: verify two operation refs are joined by the journaled B71 renewal
        chain (possibly across several hops - each renewal may itself expire while
        the intent still waits). The chain must be acyclic and branch-free, which
        renew_undelivered_confirm_operation's once-only rule already guarantees."""
        if not isinstance(predecessor,dict)or not isinstance(successor,dict):return False
        want=successor.get('sha256')
        if not want:return False
        links={}
        for r in self.s.get('company_operation_renewals',[]):
            if r.get('kind')!='expired-unconsumed-ordinary-operation-successor-v1':continue
            p=r.get('predecessor');s=r.get('successor')
            if not isinstance(p,dict)or not isinstance(s,dict)or not p.get('sha256')or not s.get('sha256'):return False
            if p['sha256']in links:return False
            links[p['sha256']]=s
        cur=predecessor.get('sha256')
        for _ in range(8):
            nxt=links.get(cur)
            if nxt is None:return False
            if nxt.get('sha256')==want:return True
            cur=nxt['sha256']
        return False

    def governance_search_rejection(self):
        """Recognize only the owned, returned route guard before the setter.
        No transport timeout, reply-null or other UNKNOWN can enter this path.
        The original call and the pre-enqueue refusal remain unchanged.
        """
        if self.s.get('extension_guard_route_recovery')or self.job.get('company_configuration_registry')!='configured-source-index-v2' or self.s.get('phase')!='searchCompany' or self.s.get('state')!='running':return None
        entry=self.current_call()
        if not entry or entry.get('state')!='unknown' or entry.get('extension_guard_recovery_attempted') or entry.get('pre_enqueue_recovery_attempted')is not True or has_side_effect_intent(self.s):return None
        if [c for c in self.s['calls']if c.get('state')=='unknown']!=[entry]:return None
        command=entry['command'];records=self.s.get('bridge_failures',[])
        failed=[r for r in records if r.get('command')==command and r.get('call_key')==entry['key'] and r.get('phase')=='searchCompany' and r.get('revision')==self.s['revision'] and r.get('raw_reply_available')is True and r.get('exception')is None and r.get('reply')=={'ok':False,'result':None,'error':'company capability source scope changed'}]
        if len(failed)!=1 or command.get('op')!='filter' or command.get('kind')!='filter' or command.get('value')!=self.job['company'] or command.get('companyRequest')!=self.s.get('company_configuration_operation'):return None
        original=entry.get('pre_enqueue_original',entry);proof=original.get('pre_enqueue_rejection',{});index=proof.get('observation_index')
        if type(index)is not int or not 0<=index<len(records):return None
        refusal=records[index]
        if not preenqueue_rejection(refusal.get('reply')) or refusal.get('command')!=original['command'] or proof.get('binding')!=_preenqueue_binding(original,refusal,proof.get('source_scope')):return None
        if entry.get('pre_enqueue_original'):
            continuation=entry.get('pre_enqueue_operation_continuation',{})
            if continuation.get('predecessor')!=original['command']['companyRequest'] or continuation.get('successor')!=command['companyRequest']:return None
        module=self._company_configuration;op=module.doc(command['companyRequest']);_,_,jobref=module.job_configuration(self.job)
        if op.get('purpose')!='configured-business-company-context' or op.get('original_job')!=jobref or op['tab_id']!=self.s['tab_id'] or op['source_groupid']!=self.s['initial_groupid']:return None
        observation=self.s['company_configuration_observations'][-1]
        if observation['key']!=entry['key'] or observation['operation']!=command['companyRequest']:return None
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit
        scope=decode(module.doc(observation['scope']),op['tab_id'],op['window_id']);a=module.entry_context(scope['before'],op['tab_id'],op['window_id']);b=module.entry_context(scope['after'],op['tab_id'],op['window_id'])
        if a!=b or a['groupid']!=op['source_groupid'] or urlsplit(a['url']).path!='/p/governance/violation_list' or identity(scope['tree'],op['source_identity'])!=op['source_identity']:return None
        fields=[n for n in nodes(scope['tree'])if n.get('selector')==command['locator']['value']]
        if len(fields)!=1 or fields[0].get('role')!='textbox' or fields[0].get('placeholder')!='搜索商户' or fields[0].get('attributes',{}).get('value','')!='':return None
        ping=scope['ping'];content=ROOT/'skills/chrome-dom-export/extension/content.js'
        if ping.get('version')!=VERSION or ping.get('content_build')!='configured-exact-company-v2' or ping.get('company_selection_policy')!='configured-exact-company-v2' or digest(content) not in ('fef02caf2812fca2070982c4ef0f322d6923840ffcf24a8162d21c8028345f22','db07b670c1091677697e05180b83d872a4d3a5ccb920c8c10310f3c1fca337f3','15d0e9b6300a6a87b264f8fde65f1d3da38a10e648433d7331361d918f334eac'):return None
        source=content.read_text();branch=source[source.index("else if(m.op==='filter')"):source.index("} else throw Error('unsupported operation')")]
        if source.count("throw Error('company capability source scope changed')")!=1 or not branch.index('companySearchField(e,m.companyCapability)')<branch.index('setter.call(e,value)'):return None
        return entry

    def review_entry_target(self,tree):
        target=unique([n for n in leaves(tree)if n.get('name')=='评价管理'],'review-entry-label-unique')
        if target.get('tag')!='span' or target.get('role')!='generic' or not target.get('selector','').startswith('#box-aside-memu-content > ') or 'src-components-AsideMenuV2-index-module__label--'not in target.get('attributes',{}).get('class','') or target.get('disabled'):raise ValueError('review-entry-sidebar-unverified')
        return target

    def restore_governance_search_entry(self,entry):
        """One normal sidebar navigation; a missing result is HOLD, never replay.
        This is action bookkeeping, not a recursive historical proof provider.
        """
        from urllib.parse import urlsplit
        module=self._company_configuration;op=module.doc(entry['command']['companyRequest']);marker=self.s.get('company_entry_route')
        snapshot,tabs,current=self.tick_snapshot();tree=snapshot['tree']
        after=module.entry_context(snapshot['after'],self.s['tab_id'],op['window_id'])
        def settling():
            elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(marker['at'])).total_seconds()
            if not 0<=elapsed<=86400:raise ValueError('review-entry-readonly-settle-exhausted')
            time.sleep(.25);return self.s
        stable=current==after and tree.get('url')==urlsplit(current['url'])._replace(query='',fragment='').geturl()
        if not stable:
            if marker is None:raise ValueError('review-entry-source-read-changed')
            if marker.get('state')!='returned':raise ValueError('review-entry-navigation-unconfirmed-no-replay')
            return settling()
        if current['groupid']!=op['source_groupid'] or current['windowId']!=op['window_id'] or identity(tree,op['source_identity'])!=op['source_identity']:raise ValueError('review-entry-source-changed')
        if marker is None:
            if urlsplit(current['url']).path!='/p/governance/violation_list':raise ValueError('review-entry-original-route-required')
            target=self.review_entry_target(tree);command={'op':'click','tabId':self.s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
            marker={'kind':'owned-company-entry-route-v1','original_call':json.loads(json.dumps(entry)),'before':self._last_tick_scope_ref,'command':command,'state':'unknown','at':now()};self.s['company_entry_route']=marker;self.save()
            result=self.call(command);marker.update(state='returned',result=result);self.save();return self.s
        if marker.get('kind')!='owned-company-entry-route-v1' or marker.get('original_call')!=entry or marker.get('state')not in('returned','ready') or marker.get('result',{}).get('kind')!='navigation' or marker.get('result',{}).get('clicked',{}).get('name')!='评价管理' or marker.get('result',{}).get('clicked',{}).get('selector')!=marker.get('command',{}).get('locator',{}).get('value'):raise ValueError('review-entry-navigation-unconfirmed-no-replay')
        if urlsplit(current['url']).path!='/p/life_comment/management':return settling()
        from company_search_wait import field
        if field(tree)is None:
            picker=marker.get('picker')
            if picker is not None:
                if picker.get('state')!='returned' or picker.get('result',{}).get('clicked',{}).get('selector')!=picker.get('command',{}).get('locator',{}).get('value'):raise ValueError('review-entry-picker-unconfirmed-no-replay')
                return settling()
            target=company_switch(tree);command={'op':'click','tabId':self.s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'}
            picker={'command':command,'state':'unknown','before':self._last_tick_scope_ref};marker['picker']=picker;self.save()
            result=self.call(command);picker.update(state='returned',result=result);self.save();return self.s
        if field(tree).get('attributes',{}).get('value','')!='':raise ValueError('review-entry-existing-search-preserved')
        marker.update(state='ready',scope=self._last_tick_scope_ref);self.save();return self.s

    def extension_guard_recovery_entry(self):
        marker=self.s.get('extension_guard_route_recovery')
        if marker is None:return self.governance_search_rejection()
        if type(marker)is not dict or set(marker)!={'kind','proof','route_complete'}or marker['kind']!='verified-workflow-extension-guard-route-recovery-v1':raise ValueError('extension-guard-marker-shape')
        entry=self.current_call()
        if not entry or entry.get('extension_guard_recovery_attempted'):return None
        if self.s.get('phase')!='searchCompany'or self.s.get('state')!='running'or entry.get('state')!='unknown'or entry.get('pre_enqueue_recovery_attempted')is not True or has_side_effect_intent(self.s):raise ValueError('extension-guard-original-unknown-required')
        if [c for c in self.s['calls']if c.get('state')=='unknown']!=[entry]:raise ValueError('extension-guard-only-original-unknown')
        import importlib.util
        root=Path(__file__).resolve().parents[3];path=root/'work/performance-audit/extension-guard-preinput-proof-candidate/guard_proof.py'
        if digest(path)!='3a1a29eb021563e4013d7daf848e53dc5ba069c3f39966de8dfffdefb3ae67db':raise ValueError('extension-guard-verifier-generation')
        spec=importlib.util.spec_from_file_location('_workflow_extension_guard_proof',path);verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier);proof=verifier.verify(marker['proof']);before=verifier.doc(proof['workflow_archive'])
        if self.s.get('bridge_failures',[])!=before.get('bridge_failures',[])or self.s.get('last_error')not in(None,before.get('last_error')):raise ValueError('extension-guard-original-failure-prefix')
        if self.s['calls']!=before['calls']or entry['key']!=proof['call_key']or self.s['revision']!=before['revision']or self.s['company_configuration_job']!=before['company_configuration_job']:raise ValueError('extension-guard-original-call-prefix')
        if marker['route_complete']!={'path':str(root/'work/2026-10-29/round009-issue55-original-recovery/review-route-once/complete.json'),'sha256':'1403e5a356d09868dde34e022747dc86a80e89b1fcb5c8701dd2866ca638edcc'}:raise ValueError('extension-guard-fixed-route-ticket')
        module=self._company_configuration;route=module.doc(marker['route_complete']);intent=module.doc(route['intent']);reply=module.doc(route['navigation_returned'])
        if route.get('kind')!='verified-original-failed12-review-route-restoration-v1'or route['proof']!=marker['proof']or route['WF_unchanged']is not True or route['search_granted']is not False or intent['proof']!=marker['proof']or intent['original_workflow']!=proof['workflow']or reply.get('ok')is not True or reply.get('result',{}).get('clicked',{}).get('name')!='评价管理':raise ValueError('extension-guard-route-ticket')
        if route['result']['scope']!={'tab_id':self.s['tab_id'],'window_id':module.doc(proof['renewed_operation'])['window_id']}or route['result']['identity']!=proof['current_identity']or route['result']['groupid']!=proof['source_groupid']or route['result']['search_performed']is not False:raise ValueError('extension-guard-route-identity')
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit,parse_qs
        raw=module.doc(route['after']);value=decode(raw['result']if raw.get('ok')is True else raw,self.s['tab_id'],route['result']['scope']['window_id']);window=route['result']['scope']['window_id'];a=module.entry_context(value['before'],self.s['tab_id'],window);b=module.entry_context(value['after'],self.s['tab_id'],window);url=urlsplit(a['url'])
        if a!=b or url.path!='/p/life_comment/management'or a['groupid']!=proof['source_groupid']or identity(value['tree'],proof['current_identity'])!=proof['current_identity']:raise ValueError('extension-guard-route-source')
        return entry

    def resume_extension_guard_operation(self,entry,command,scope):
        if self.extension_guard_recovery_entry()is not entry:raise ValueError('extension-guard-exact-recovery-required')
        if self.s.get('extension_guard_route_recovery')is None:
            marker=self.s.get('company_entry_route',{});module=self._company_configuration;old_ref=entry['command']['companyRequest'];old=module.doc(old_ref)
            if marker.get('state')!='ready' or marker.get('original_call')!=entry:raise ValueError('review-entry-restoration-required')
            from readonly_tick_snapshot import decode
            from urllib.parse import urlsplit
            value=decode(module.doc(scope),self.s['tab_id'],old['window_id']);a=module.entry_context(value['before'],self.s['tab_id'],old['window_id']);b=module.entry_context(value['after'],self.s['tab_id'],old['window_id'])
            if a!=b or urlsplit(a['url']).path!='/p/life_comment/management' or a['groupid']!=old['source_groupid'] or identity(value['tree'],old['source_identity'])!=old['source_identity']:raise ValueError('review-entry-fresh-source-required')
            from company_search_wait import field
            target=field(value['tree'])
            if target is None or target.get('attributes',{}).get('value','')!='' or command.get('locator')!={'by':'selector','value':target['selector']}:raise ValueError('review-entry-empty-field-required')
            if {k:v for k,v in command.items()if k!='locator'}!={k:v for k,v in entry['command'].items()if k not in('companyRequest','locator')}:raise ValueError('review-entry-original-command-required')
            destination=self.file.parent/('configured-company-review-entry-'+old_ref['sha256']+'.json');request,new_ref=module.business_command(self.job,command,scope,None,destination,old['key']);new=module.doc(new_ref)
            if {k:v for k,v in old.items()if k not in('issued_at','expires_at')}!={k:v for k,v in new.items()if k not in('issued_at','expires_at')}:raise ValueError('review-entry-operation-drift')
            entry['extension_guard_original']=json.loads(json.dumps(entry));entry['extension_guard_operation_continuation']={'kind':'owned-route-rejected-search-continuation-v1','route':json.loads(json.dumps(marker)),'predecessor':old_ref,'successor':new_ref,'scope':scope};entry['command']=request;entry['extension_guard_recovery_attempted']=True;self.s['company_configuration_operation']=new_ref;self.s.setdefault('company_configuration_observations',[]).append({'key':entry['key'],'scope':scope,'operation':new_ref,'at':now()});self.save();return request
        marker=self.s['extension_guard_route_recovery'];module=self._company_configuration;old_ref=entry['command']['companyRequest'];old=module.doc(old_ref);base={k:v for k,v in entry['command'].items()if k not in('companyRequest','locator')}
        if {k:v for k,v in command.items()if k!='locator'}!=base:raise ValueError('extension-guard-business-command-drift')
        from readonly_tick_snapshot import decode
        raw=module.doc(scope);value=decode(raw,self.s['tab_id'],old['window_id']);a=module.entry_context(value['before'],self.s['tab_id'],old['window_id']);b=module.entry_context(value['after'],self.s['tab_id'],old['window_id'])
        from urllib.parse import urlsplit
        if a!=b or urlsplit(a['url']).path!='/p/life_comment/management'or a['groupid']!=old['source_groupid']or identity(value['tree'],old['source_identity'])!=old['source_identity']:raise ValueError('extension-guard-fresh-review-scope')
        field=unique([n for n in nodes(value['tree'])if n.get('role')=='textbox'and n.get('placeholder')=='搜索商户'],'extension-guard-fresh-search-field')
        if field.get('attributes',{}).get('value','')!=''or command['locator']!={'by':'selector','value':field['selector']}:raise ValueError('extension-guard-fresh-empty-field')
        destination=self.file.parent/('configured-company-extension-guard-'+marker['proof']['sha256']+'.json');request,new_ref=module.business_command(self.job,command,scope,None,destination,old['key']);new=module.doc(new_ref);variable={'issued_at','expires_at'}
        if {k:v for k,v in old.items()if k not in variable}!={k:v for k,v in new.items()if k not in variable}:raise ValueError('extension-guard-operation-drift')
        entry['extension_guard_original']=json.loads(json.dumps(entry));entry['extension_guard_operation_continuation']={'kind':'known-extension-preinput-guard-operation-successor-v1','proof':marker['proof'],'route_complete':marker['route_complete'],'predecessor':old_ref,'successor':new_ref,'scope':scope};entry['command']=request;entry['extension_guard_recovery_attempted']=True;self.s['company_configuration_operation']=new_ref;self.s.setdefault('company_configuration_observations',[]).append({'key':entry['key'],'scope':scope,'operation':new_ref,'at':now()});self.save();return request

    def renew_undelivered_company_operation(self,entry,command,scope):
        """One exact pre-enqueue refusal may outlive its bounded operation.
        Keep the expired authority and original UNKNOWN intact as evidence;
        create a fresh ordinary operation only for this same input opportunity.
        """
        if self.preenqueue_recovery_entry()is not entry:raise ValueError('preenqueue-renewal-owned-refusal-required')
        module=self._company_configuration;old_ref=entry['command']['companyRequest'];old=module.doc(old_ref)
        if old.get('purpose')!='configured-business-company-context':raise ValueError('preenqueue-renewal-ordinary-operation-required')
        config,_,original=module.job_configuration(self.job)
        module.operation(config,old_ref,now=datetime.fromisoformat(old['issued_at']))
        if datetime.now(timezone.utc)<=datetime.fromisoformat(old['expires_at']):raise ValueError('preenqueue-renewal-expired-required')
        destination=self.file.parent/('configured-company-undelivered-'+old_ref['sha256']+'.json')
        request,new_ref=module.business_command(self.job,command,scope,None,destination,old['key'])
        new=module.doc(new_ref);variable={'issued_at','expires_at'}
        if {k:v for k,v in old.items()if k not in variable}!={k:v for k,v in new.items()if k not in variable}or new['original_job']!=original:raise ValueError('preenqueue-renewal-operation-drift')
        if {k:v for k,v in request.items()if k!='companyRequest'}!={k:v for k,v in entry['command'].items()if k!='companyRequest'}:raise ValueError('preenqueue-renewal-command-drift')
        # The caller persists all of this together with attempted=True before
        # dispatch. A crash/transport failure afterwards is observe-only.
        entry['pre_enqueue_original']=json.loads(json.dumps(entry))
        entry['pre_enqueue_operation_continuation']={'kind':'owned-undelivered-operation-successor-v1','predecessor':old_ref,'successor':new_ref,'scope':scope}
        entry['command']=request;self.s['company_configuration_operation']=new_ref
        self.s.setdefault('company_configuration_observations',[]).append({'key':entry['key'],'scope':scope,'operation':new_ref,'at':now()})
        return request

    def review_tab_source(self,entry):
        source=entry.get('preinput_navigation_source',self.s.get('last_tree',{}));directory=self.file.parent/'bridge-evidence';path=Path(source.get('path',''));wanted=source.get('sha256','')
        if path.parent!=directory or not re.fullmatch('[a-f0-9]{64}',wanted):return None
        if not path.is_file()or digest(path)!=wanted:path=directory/('preinput-original-tree-'+wanted+'.json')
        if path.is_file()and not path.is_symlink()and path.resolve()==path and digest(path)==wanted:return {'path':str(path),'sha256':wanted}
        return None

    def review_tab_zero_match(self):
        if self.s.get('phase')!='openReviews' or self.s.get('state')!='running' or self.job.get('company_configuration_registry')!='configured-source-index-v2' or has_side_effect_intent(self.s):return None
        entry=self.current_call()
        if not entry or entry.get('state')!='unknown' or entry.get('preinput_navigation_recovery_attempted') or [c for c in self.s['calls']if c.get('state')=='unknown']!=[entry]:return None
        command=entry['command']
        if set(command)!={'op','tabId','locator','kind'} or command['op']!='click' or command['kind']!='navigation' or command['tabId']!=self.s['tab_id']:return None
        expected={'ok':False,'result':None,'error':'ambiguous-or-missing: 0 visible matches; inspect and scope selector, never guess'}
        failed=[r for r in self.s.get('bridge_failures',[])if r.get('command')==command and r.get('reply')==expected and r.get('raw_reply_available')is True and r.get('exception')is None and r.get('phase')=='openReviews' and r.get('revision')==self.s['revision'] and r.get('call_key')==entry['key']]
        if len(failed)!=1 or digest(ROOT/'skills/chrome-dom-export/extension/content.js') not in ('fef02caf2812fca2070982c4ef0f322d6923840ffcf24a8162d21c8028345f22','db07b670c1091677697e05180b83d872a4d3a5ccb920c8c10310f3c1fca337f3','15d0e9b6300a6a87b264f8fde65f1d3da38a10e648433d7331361d918f334eac'):return None
        source=self.review_tab_source(entry)
        if source is None:return None
        path=Path(source['path'])
        tree=json.loads(path.read_bytes())
        try:target=all_reviews(tree)
        except ValueError:return None
        if tree.get('url')!='https://life.douyin.com/p/life_comment/management' or target.get('tag')!='span' or target.get('attributes',{}).get('class')!='byted-tab-bar-item-label' or command['locator']!={'by':'selector','value':target['selector']}:return None
        return entry

    def prepare_review_tab_preinput(self):
        entry=self.review_tab_zero_match()
        if entry is None:return
        source=self.review_tab_source(entry)
        if source is None:raise ValueError('review-tab-original-tree-changed')
        previous=entry.get('preinput_navigation_source')
        if previous==source:return
        if previous is not None:entry['preinput_navigation_source_provenance']={'original_path':previous['path'],'original_sha256':previous['sha256'],'recovered_material':source}
        entry['preinput_navigation_source']=source;self.save()

    def resume_review_tab_preinput(self,entry,command):
        if self.review_tab_zero_match()is not entry:raise ValueError('review-tab-original-zero-match-required')
        source=entry.get('preinput_navigation_source',{});path=Path(source.get('path',''))
        if not path.is_file() or digest(path)!=source.get('sha256'):raise ValueError('review-tab-original-tree-changed')
        original=all_reviews(json.loads(path.read_bytes()))
        if entry['command']['locator']!={'by':'selector','value':original['selector']} or original.get('attributes',{}).get('class')!='byted-tab-bar-item-label':raise ValueError('review-tab-original-label-required')
        from readonly_tick_snapshot import decode
        from urllib.parse import urlsplit
        module=self._company_configuration;scope=getattr(self,'_last_tick_scope_ref',None)
        if scope is None:raise ValueError('review-tab-fresh-scope-required')
        raw=module.doc(scope);window=raw.get('scope',{}).get('windowId');fresh=decode(raw,self.s['tab_id'],window);a=context(fresh['before'],self.s['tab_id'],self.job['groupid']);b=context(fresh['after'],self.s['tab_id'],self.job['groupid'])
        if a!=b or a.get('windowId')!=window or urlsplit(a['url']).path!='/p/life_comment/management' or self.s.get('identity')!=self.job['identity_baseline']:raise ValueError('review-tab-original-company-required')
        if any('UserCard-index-module__outer--'in n.get('attributes',{}).get('class','')for n in nodes(fresh['tree'])):identity(fresh['tree'],self.job['identity_baseline'])
        target=all_reviews(fresh['tree'])
        if target.get('tag')!='span' or target.get('attributes',{}).get('class')!='byted-tab-bar-item-label' or command.get('locator')!={'by':'selector','value':target['selector']} or {k:v for k,v in command.items()if k!='locator'}!={k:v for k,v in entry['command'].items()if k!='locator'}:raise ValueError('review-tab-fresh-label-required')
        entry['preinput_navigation_original']=json.loads(json.dumps(entry));entry['preinput_navigation_recovery_attempted']=True;entry['preinput_navigation_scope']=scope;entry['command']=command;self.save();return command

    def once(self,command,intent_key=None):
        self._export_cluster_token=None # Also invalidate confirmed/no-dispatch paths.
        key=intent_key or str(self.s['revision'])+':'+self.s['phase']
        if any(x.get('original_call',{}).get('key')==key for x in self.s.get('retired_intents',[])):raise ValueError('ui-intent-retired-do-not-replay')
        previous=[x for x in self.s['calls'] if x['key']==key]
        if not previous and any(x.get('state')=='unknown'and x.get('pre_enqueue_rejection')for x in self.s['calls']):raise ValueError('preenqueue-original-key-required')
        if previous:
            entry=unique(previous)
            guard_entry=self.extension_guard_recovery_entry()
            navigation_entry=self.review_tab_zero_match()
            actual=entry.get('command',{})
            if getattr(self,'_company_configuration',None)is not None and 'companyRequest'in actual:
                expected=self.s.get('company_configuration_operation')
                if self.s.get('company_search_explicit_recovery')and actual.get('op')=='click'and actual.get('kind')in('company','company-confirm'):
                    if not self.calls_progression_safe():raise ValueError('company-remaining-progression-required')
                    expected=self.s.get('company_configuration_confirm_operation')if actual.get('kind')=='company-confirm'and self.s.get('company_configuration_confirm_operation')else self.s.get('company_configuration_remaining_operation')
                # B79: the journaled intent's companyRequest may trail the current
                # operation through the B71 renewal chain; only a journaled
                # successor explains that difference - anything else is a conflict.
                if actual['companyRequest']!=expected and not self.renewal_chain_links(actual['companyRequest'],expected):raise ValueError('company-config-intent-operation-conflict')
                actual={k:v for k,v in actual.items()if k!='companyRequest'}
            if actual!=command and guard_entry is not entry and navigation_entry is not entry:raise ValueError('ui-intent-command-conflict')
            if entry['state']=='confirmed':return entry['result']
            if navigation_entry is entry:
                command=self.resume_review_tab_preinput(entry,command)
            elif guard_entry is entry:
                scope=getattr(self,'_last_tick_scope_ref',None)
                if not scope:raise ValueError('extension-guard-fresh-scope-required')
                command=self.resume_extension_guard_operation(entry,command,scope)
            else:
                if self.preenqueue_recovery_entry()is not entry:raise ValueError('ui-outcome-unknown-do-not-replay')
                # The normal phase already took a new strict scope observation.
                # Consume the sole opportunity durably BEFORE retrying this exact key.
                scope=getattr(self,'_last_tick_scope_ref',None)
                marker=entry.get('pre_enqueue_rejection')
                if marker is not None:
                    if not scope or scope==marker.get('source_scope'):raise ValueError('preenqueue-recovery-fresh-scope-required')
                else:
                    # B75: the older confirm refusal has no marker, so its own
                    # recorded observation authorises freshness instead.
                    self.require_unmarked_confirmation_retry_scope(entry,scope)
                try:retry_command=self.configured_company_command(command)
                except ValueError as error:
                    # B75: with a confirm intent now journaled, the ordinary
                    # successor refuses by design and the pre-enqueue successor
                    # is the correct authority - both mean the same thing here:
                    # the authority behind this undelivered intent was spent.
                    if str(error)not in('company-operation-expired-or-unbounded','company-renewal-confirm-intent-exists'):raise
                    retry_command=self.renew_undelivered_company_operation(entry,command,scope)
                if retry_command!=entry['command']:
                    # B79: configured_company_command may lawfully renew the expired
                    # ordinary operation on this very recovery (B71 renew_undelivered_confirm_operation),
                    # so the rebuilt request carries the renewal successor while the
                    # journaled intent still names the expired predecessor. Accept
                    # that successor exactly as renew_undelivered_company_operation
                    # does: every other field must match verbatim and the renewal
                    # must be journaled; then bind the continuation into the entry
                    # like every other operation continuation does.
                    if {k:v for k,v in retry_command.items()if k!='companyRequest'}!={k:v for k,v in entry['command'].items()if k!='companyRequest'}or not self.renewal_chain_links(entry['command'].get('companyRequest'),retry_command.get('companyRequest')):raise ValueError('preenqueue-recovery-command-drift')
                    entry['pre_enqueue_original']=json.loads(json.dumps(entry))
                    entry['pre_enqueue_operation_continuation']={'kind':'owned-undelivered-operation-successor-v1','via':'renew-undelivered-confirm-operation-v1','predecessor':entry['command']['companyRequest'],'successor':retry_command['companyRequest']}
                    entry['command']=retry_command
                # B78: the retry dispatches under the same key but a NEWER
                # operation, so the intent's original `at` no longer bounds the
                # window it was sent under. Record the moment this attempt
                # consumed its one opportunity, before the dispatch, so the
                # post-switch read can prove the click happened inside the
                # operation it actually carries.
                entry['pre_enqueue_recovery_attempted']=True;entry['pre_enqueue_recovery_at']=now();self.save()
                command=entry['command']
        else:
            if getattr(self,'_company_configuration',None)is not None:command=self.configured_company_command(command)
            entry={'key':key,'at':now(),'phase':self.s['phase'],'command':command,'state':'unknown'}
            self.s['calls'].append(entry);self.save()
        observation_count=len(self.s.get('bridge_failures',[]))
        try:result=self.call(command)
        except Exception:
            # A reply-null transport failure NEVER creates this marker.
            records=self.s.get('bridge_failures',[])
            if len(records)==observation_count+1:
                record=records[-1]
                if record.get('command')==command and record.get('call_key')==key and record.get('exception')is None and record.get('raw_reply_available')is True and preenqueue_rejection(record.get('reply')):
                    # B74: a refusal emitted before Jobs.add proves the main
                    # process never delivered this intent, so it is the same
                    # owned non-delivery the searchCompany filter already
                    # recognised. The confirm click differs only in phase and in
                    # being the input this run has been trying to make for hours,
                    # so it is admitted here under the identical reply contract.
                    owned=(self.s.get('phase')=='searchCompany'and command.get('op')=='filter'and command.get('kind')=='filter')or(self.s.get('phase')=='confirmSwitch'and command.get('op')=='click'and command.get('kind')=='company-confirm')
                    if owned and command.get('companyRequest')==self.s.get('company_configuration_operation')and command.get('companyRequest')and getattr(self,'_last_tick_scope_ref',None)and 'pre_enqueue_rejection'not in entry:
                        entry['pre_enqueue_rejection']={'kind':'owned-preenqueue-no-delivery-v1','observation_index':len(records)-1,'binding':_preenqueue_binding(entry,record,self._last_tick_scope_ref),'source_scope':json.loads(json.dumps(self._last_tick_scope_ref))};self.save()
            raise
        entry.update(state='confirmed',result=result);self.save();return result
    def current_call(self):
        key=str(self.s['revision'])+':'+self.s['phase']
        return unique([x for x in self.s['calls'] if x['key']==key]) if any(x['key']==key for x in self.s['calls']) else None
    def reconcile_rejected_company_switch(self):
        """Only the synchronous pre-action policy denial can retire this intent.
        Transport errors, timeouts and every other unknown remain unreplayable.
        """
        if self.s.get('state')!='running' or self.s.get('phase')!='context' or has_side_effect_intent(self.s):raise ValueError('rejected-switch-phase-required')
        if self.s.get('last_error',{}).get('message')!='bridge-command-failed: not in offline reviewed click allowlist':raise ValueError('explicit-pre-action-policy-denial-required')
        entry=self.current_call()
        if not entry or entry.get('state')!='unknown' or entry.get('command',{}).get('op')!='click' or entry['command'].get('kind')!='navigation':raise ValueError('single-rejected-switch-intent-required')
        if [c for c in self.s['calls'] if c.get('state')=='unknown']!=[entry]:raise ValueError('other-unknown-intent-present')
        ref=self.s.get('last_tree',{});path=Path(ref.get('path',''))
        if not path.is_file() or digest(path)!=ref.get('sha256'):raise ValueError('original-rejected-switch-tree-required')
        original=json.loads(path.read_text());button=company_switch(original)
        if button.get('name')!='切换' or entry['command'].get('locator')!={'by':'selector','value':button['selector']}:raise ValueError('rejected-merchant-switch-command-mismatch')
        ping=self.call({'op':'ping','tabId':self.s['tab_id']})
        # Transport consistency only: VERSION is the reviewed constant imported
        # from dom_evidence; the extension must report exactly that build. The
        # former hardcoded v7 equality was a dead migration guard that broke
        # every later reviewed version bump (observed on 2026-11-03 v12).
        if ping.get('version')!=VERSION:raise ValueError('reviewed-merchant-switch-policy-upgrade-required')
        tabs=self.call({'op':'tabs'});current=context(tabs,self.s['tab_id'],self.s['initial_groupid'])
        fresh=self.call({'op':'tree','tabId':self.s['tab_id']})
        if identity(fresh)!=identity(original) or company_switch(fresh)['selector']!=button['selector']:raise ValueError('rejected-switch-page-changed')
        archive=self.file.with_name('workflow-before-policy-rejection-'+digest(self.file)[:12]+'.json')
        if not archive.exists():archive.write_bytes(self.file.read_bytes())
        entry.update(state='rejected',rejection={'before_action':True,'message':self.s['last_error']['message'],'original_tree':ref,'archive':str(archive),'archive_sha256':digest(archive),'reviewed_policy_version':VERSION,'at':now()})
        self.s['revision']+=1;self.s.pop('last_error',None)
        self.s.setdefault('recovery_events',[]).append({'kind':'policy-rejection-reconciled','key':entry['key'],'groupid':current['groupid'],'policy_version':VERSION,'at':now()})
        self.save();return self.s
    def switch_home_contract(self):
        from switch_read_recovery import formal_daily_return
        if not ((self.job.get('navigation_only') is True or formal_daily_return(self.job)) and self.job.get('action')=='return-company' and self.job.get('identity_contract')=='merchant-v2' and self.s['phase'] in ('verifySwitch','accountAfterSwitch','identityAfterSwitch')):raise ValueError('post-switch-home-phase-unverified')
        if self.s.get('company_search_explicit_recovery'):
            if not self.calls_progression_safe():raise ValueError('post-switch-home-unknown-intent')
        elif any(c.get('state')=='unknown' for c in self.s['calls']):raise ValueError('post-switch-home-unknown-intent')
        chosen=unique([c for c in self.s['calls'] if c.get('phase')=='chooseCompany' and c.get('command',{}).get('kind')=='company'],'post-switch-home-selection-unverified')
        confirmed=unique([c for c in self.s['calls'] if c.get('phase')=='confirmSwitch' and c.get('command',{}).get('kind')=='company-confirm'],'post-switch-home-confirm-unverified')
        for call,name in ((chosen,self.job['company']),(confirmed,'确认')):
            if call.get('state')!='confirmed' or call['command'].get('op')!='click' or call['command'].get('tabId')!=self.s['tab_id'] or call.get('result',{}).get('clicked',{}).get('name')!=name or call['result']['clicked'].get('selector')!=call['command'].get('locator',{}).get('value'):raise ValueError('post-switch-home-confirm-unverified')
        if self.s['calls'].index(chosen)>=self.s['calls'].index(confirmed):raise ValueError('post-switch-home-confirm-order-unverified')
        expected=self.scoped_identity_baseline(str(self.job['groupid']),'company')
        known=self.job.get('known_company_identities',{})
        if not expected or expected.get('provider')!=self.s.get('provider_baseline') or [gid for gid,value in known.items() if value==expected]!=[str(self.job['groupid'])]:raise ValueError('post-switch-home-registry-unverified')
        return expected
    def source_context(self,tabs):
        from urllib.parse import urlsplit
        tab=unique([t for w in tabs for t in w.get('tabs',[]) if t.get('tabId')==self.s['tab_id']],'explicit-tab-not-unique')
        u=urlsplit(tab.get('url',''))
        if getattr(self,'_company_configuration',None)is not None and u.path=='/p/login':
            if self.s['phase']not in('account','context','searchCompany','chooseCompany','confirmSwitch'):raise ValueError('configured-login-unexpected-stage')
            self._company_configuration.job_configuration(self.job)
            return self._company_configuration.entry_context(tabs,self.s['tab_id'],tab.get('windowId'),login=True)
        if u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/home' and not u.query and not u.fragment:
            self.switch_home_contract()
            if not tab.get('allowed'):raise ValueError('tab-origin-unverified')
            return dict(tab,groupid=None,post_switch_home=True)
        return context(tabs,self.s['tab_id'])
    def verify_home_company(self,t):
        self.switch_home_contract()
        labels=[n for n in nodes(t) if 'src-pages-HomeV3-components-DataOverviewAndAccountInfo-AccountInfo-AccountInfo-module__companyName--' in n.get('attributes',{}).get('class','')]
        label=unique(labels,'post-switch-home-company-unverified')
        if label.get('name')!=self.job['company'] or label.get('tag')!='span' or label.get('children'):raise ValueError('post-switch-home-company-unverified')

    def ensure_source_active(self,tabs,current):
        phases={'account','readAccount','context','searchCompany','chooseCompany','confirmSwitch','verifySwitch','accountAfterSwitch','identityAfterSwitch','openReviews','waitReviewManagement','readReviewFilters','verifyFilter','dismissOnboarding','waitOnboardingClosed'}
        if self.s['phase'] not in phases:return tabs,current
        prefix='source-focus:'+str(self.s['revision'])+':'+self.s['phase']+':'
        windows=[w for w in tabs if any(t.get('tabId')==self.s['tab_id'] for t in w.get('tabs',[]))]
        window=unique(windows,'source-window-not-unique')
        previous=[c for c in self.s['calls'] if c['key'].startswith(prefix)]
        unknown=[c for c in previous if c['state']=='unknown']
        if unknown:
            # Focus is reconciled from public tab/window state, never reissued.
            if current.get('active') is not True or window.get('focused') is not True:raise ValueError('source-focus-outcome-unknown')
            unique(unknown).update(state='confirmed',result={'observed':True,'tabId':self.s['tab_id'],'windowId':window.get('windowId'),'url':current['url'],'active':True,'windowFocused':True});self.save()
        # Normal semantic DOM reads/actions address this exact allowed tab;
        # OS/window focus and active-tab status belong to capture/native gates.
        # Never issue activate merely to acquire DOM. Historical unknown focus
        # above still needs its original full effect; this change cannot retire it.
        return tabs,current
    def tick_snapshot(self):
        reused=self._take_export_cluster()
        if reused is not None:return reused
        # Only the original tab's stable window ID is reused. Every DOM/read
        # result is newly obtained, including after any input that focuses it.
        from readonly_tick_snapshot import decode
        tab_id=self.s['tab_id'];window_id=getattr(self,'_readonly_window_id',None)
        focused=[c for c in self.s.get('calls',[]) if c.get('key','').startswith('source-focus:') and c.get('state')=='confirmed' and c.get('command')=={'op':'activate','tabId':tab_id} and c.get('result',{}).get('tabId')==tab_id]
        if focused:window_id=focused[-1]['result'].get('windowId')
        if type(window_id) is not int or window_id<0:
            tabs=self.call({'op':'tabs'});current=self.source_context(tabs)
            tabs,current=self.ensure_source_active(tabs,current)
            window=unique([w for w in tabs if any(t.get('tabId')==tab_id for t in w.get('tabs',[]))],'source-window-not-unique')
            window_id=window.get('windowId')
            if type(window_id) is not int or window_id<0:raise ValueError('source-window-id-required')
        self._readonly_window_id=window_id
        def read():
            value=decode(self.call({'op':'readonly-scope','tabId':tab_id,'windowId':window_id}),tab_id,window_id)
            directory=self.file.parent/'bridge-evidence';directory.mkdir(exist_ok=True)
            path=directory/(str(self.s['revision']).zfill(4)+'-'+self.s['phase']+'-scope-'+uuid.uuid4().hex+'.json');write_json(path,value)
            self._last_tick_scope_ref={'path':str(path),'sha256':digest(path)}
            # B93: the canonical per-tick observation scope. settle_company_confirmation
            # may repoint _last_tick_scope_ref at its own companion reply (B87 click
            # authority), but the provenance row must keep naming this file.
            self._canonical_tick_scope_ref=dict(self._last_tick_scope_ref)
            return value
        snapshot=read();tabs=snapshot['before'];current=self.source_context(tabs)
        self.ensure_source_active(tabs,current)
        return snapshot,tabs,current
    def mutate(self,op,target,kind,tab=None,**extra):
        self._export_cluster_token=None
        if target.get('disabled') or not target.get('selector'):raise ValueError('element-not-ready')
        return self.once({'op':op,'tabId':tab or self.s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':kind,**extra})
    def checkpoint(self,stage,**data):self.s['checkpoints'].append({'stage':stage,'event_id':uuid.uuid4().hex,'at':now(),**data})
    def go(self,phase):
        if self.s.get('last_error'):
            self.s.setdefault('resolved_errors',[]).append({**self.s.pop('last_error'),'resolved_at':now(),'next_phase':phase})
        self.s['phase']=phase;self.s['revision']+=1;self.save()
    def _export_cluster_binding(self):
        # All live state except explicit phase bookkeeping and this audit must
        # remain exact. No cache is restored from persisted consumer records.
        excluded={'phase','revision','updated_at','last_tree','export_pure_phase_consumers'}
        value={'job':self.job,'state':{k:v for k,v in self.s.items()if k not in excluded}}
        return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    def _take_export_cluster(self):
        token=getattr(self,'_export_cluster_token',None);self._export_cluster_token=None
        if token is None or not getattr(self,'_export_cluster_active',False):return None
        if self.s['phase']!=token['phase']or self.s['revision']!=token['revision']or self._export_cluster_binding()!=token['binding']or self.s.get('last_tree')!=token['tree']:return None
        from readonly_tick_snapshot import decode
        scope=token['scope'];tree=token['tree']
        if digest(Path(scope['path']))!=scope['sha256']or digest(Path(tree['path']))!=tree['sha256']:raise ValueError('export-pure-snapshot-evidence-changed')
        value=json.loads(Path(scope['path']).read_bytes());value=decode(value,self.s['tab_id'],token['window_id'])
        if json.loads(Path(tree['path']).read_bytes())!=value['tree']:raise ValueError('export-pure-snapshot-tree-changed')
        self._export_cluster_reused=True;self._export_cluster_origin=token['origin'];self._last_tick_scope_ref=scope
        self.s.setdefault('export_pure_phase_consumers',[]).append({'source_scope_ref':scope,'source_tree_ref':tree,'source_phase':token['origin']['phase'],'source_revision':token['origin']['revision'],'consuming_phase':self.s['phase'],'consuming_revision':self.s['revision'],'validation_at':now(),'reuse':True})
        self.save();tabs=value['before'];current=self.source_context(tabs);self.ensure_source_active(tabs,current)
        return value,tabs,current
    def tick(self):
        self._export_cluster_reused=False;self._export_cluster_extra_read=False
        barrier=any(self.s.get(k)for k in ('last_error','waiting_for','exportPending','downloadPending','attempts'))
        phase,revision=self.s['phase'],self.s['revision'];self._export_cluster_origin={'phase':phase,'revision':revision}
        try:
            result=self._tick()
            edges={'exportDialogProfileRequired':'checkExportRange','checkExportRange':'readyToExport'}
            allowed=(getattr(self,'_export_cluster_active',False)and not barrier and not getattr(self,'_export_cluster_blocked',False)and edges.get(phase)==self.s['phase']and self.s['revision']==revision+1 and self.s['state']=='running'and not any(self.s.get(k)for k in ('waiting_for','last_error','exportPending','downloadPending','attempts'))and not self._export_cluster_extra_read and all(c.get('state')=='confirmed'for c in self.s['calls']))
            self._export_cluster_token=None
            if allowed:
                scope=getattr(self,'_last_tick_scope_ref',None);tree=self.s.get('last_tree')
                if scope and tree:
                    # Only a coherent original scope/tree may seed a pure edge.
                    value=json.loads(Path(scope['path']).read_bytes())
                    if json.loads(Path(tree['path']).read_bytes())==value['tree']:
                        self._export_cluster_token={'scope':scope,'tree':tree,'window_id':value['scope']['windowId'],'phase':self.s['phase'],'revision':self.s['revision'],'binding':self._export_cluster_binding(),'origin':self._export_cluster_origin}
            return result
        except BaseException:
            self._export_cluster_token=None;raise

    def configured_login_identity(self,value,current):
        expected=self.job['identity_baseline'];scope=self._last_tick_scope_ref
        if current.get('groupid')!=str(self.job['groupid'])or value!=expected:raise ValueError('configured-login-target-identity-changed')
        observations=self.s.setdefault('configured_login_identity_observations',[])
        if any(x['scope']==scope for x in observations):raise ValueError('configured-login-independent-observations-required')
        observations.append({'scope':scope,'groupid':current['groupid'],'identity':value,'at':now()})
        if len(observations)>2000:raise ValueError('configured-login-identity-budget')
        return len(observations)==2

    def configured_login_tick(self,snapshot,t,current):
        # Distinct entry, never treats an absent GID as current business scope.
        # The immutable original job/config authorizes only its exact target.
        module=self._company_configuration;_,row,_=module.job_configuration(self.job)
        if not self.calls_progression_safe():raise ValueError('configured-login-unknown-no-replay')
        root,children,field=module.picker_parts(t,login=True)
        if self.s.get('initial_groupid')is None:self.s['initial_groupid']=row['verified']['groupid']
        self.s.setdefault('configured_login_entry',{'kind':'original-job-login-company-picker-v2','authority':self.s['company_configuration_job']})
        phase=self.s['phase']
        if phase in('account','context'):self.go('searchCompany');return self.s
        if phase=='searchCompany':self.mutate('filter',field,'filter',value=row['company']);self.go('chooseCompany');return self.s
        if field.get('attributes',{}).get('value')!=row['company']:raise ValueError('configured-login-search-value-changed')
        if phase=='chooseCompany':
            matches=[n for n in children if not n.get('children')and n.get('name')==row['company']]
            if len(matches)>1:raise ValueError('configured-login-target-duplicate')
            if matches:self.mutate('click',matches[0],'company');self.go('confirmSwitch');return self.s
        # Login selection may navigate directly. There is no observed confirm
        # control in this profile; never invent/click one or repeat selection.
        started=self.s.setdefault('configured_login_wait_started',now())
        if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('configured-login-result-timeout-readonly')
        self.s['waiting_for']='configured-login-result';self.save();return self.s

    def verify_review_context_epoch(self):
        epoch=self.s.get('review_context_recovery')
        if epoch is None:return None
        reference=epoch['plan'];path=Path(reference['path'])
        if path.resolve()!=path or path.is_symlink()or digest(path)!=reference['sha256']:raise ValueError('review-context-plan-drift')
        plan=json.loads(path.read_bytes());prefix=plan['original_calls']
        if plan.get('kind')!='initial-review-system-error-context-recovery-plan-v1'or plan.get('recovery_action')!='reselect-original-company-once'or plan.get('max_context_epochs')!=1 or epoch['max_epochs']!=1 or epoch['original_prefix_count']!=len(prefix)or self.s['calls'][:len(prefix)]!=prefix:raise ValueError('review-context-prefix-or-plan-drift')
        if plan['job']!={'path':self.job['work_order_path'],'sha256':digest(Path(self.job['work_order_path']))}or self.s['company']!=plan['company']or str(self.s['groupid'])!=plan['groupid']or self.s['date_range']!=plan['date_range']:raise ValueError('review-context-job-drift')
        if not self.calls_progression_safe():raise ValueError('review-context-unknown-do-not-replay')
        if self.s.get('last_error'):raise ValueError('review-context-recovery-held-no-new-epoch')
        return plan

    def _tick(self):
        if self.s['state']!='running':return self.s
        self.prepare_review_tab_preinput()
        rejected=self.governance_search_rejection()
        if rejected is not None and self.s.get('company_entry_route',{}).get('state')!='ready':return self.restore_governance_search_entry(rejected)
        context_plan=self.verify_review_context_epoch()
        if self.s['phase']=='downloadResult':return self.finish_download()
        if self.s['phase']=='verifySwitch' and self.job.get('action') in ('acquire','return-company') and (self.job.get('action')=='acquire' or self.job.get('work_order_path')) and self.job.get('identity_contract')=='merchant-v2' and self.s.get('calls') and self.s['calls'][-1].get('phase')=='confirmSwitch':
            # A confirmed company switch may route during the read. Never repeat
            # its click, focus, or hover; preserve every bounded read separately.
            if self.s.get('last_error'):raise ValueError('explicit-switch-read-reconciliation-required')
            from switch_read_recovery import reconcile
            started=self.s.setdefault('company_switch_wait_started',now())
            if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('company-switch-result-timeout-readonly')
            self.save()
            result=reconcile(self.job['work_order_path'],digest(self.file),self.invoke)
            self.s=json.loads(self.file.read_bytes())
            if result['state']=='hold':self.s['waiting_for']='company-switch-readonly-scope';self.s['switch_read_hold']=result;self.save()
            return self.s
        if self.s['phase']=='searchCompany' and self.s.get('last_error') and self.preenqueue_recovery_entry()is None and self.extension_guard_recovery_entry()is None:
            # Only this known pre-search registry mismatch can self-reconcile.
            # Verify original saved identity/modal/call prefix before any new read.
            error_pair=(self.s['last_error'].get('code'),self.s['last_error'].get('message'))
            if self.job.get('company_configuration_registry')!='configured-source-index-v2'or error_pair not in tuple((code,)*2 for code in('company-search-entry-identity-required','company-entry-reviewed-route','company-entry-governance-query','explicit-company-search-read-reconciliation-required')):raise ValueError('explicit-company-search-read-reconciliation-required')
            from company_search_wait import entry_error_transform
            original=self.file.read_bytes()
            if json.loads(original)!=self.s:raise ValueError('company-search-entry-canonical-drift')
            saved=self.s.get('last_tree',{});treepath=Path(saved.get('path',''))
            if not treepath.is_file()or digest(treepath)!=saved.get('sha256'):raise ValueError('company-search-entry-original-tree-drift')
            updated=configured_entry_error_transform(self.job,self.s,json.loads(treepath.read_bytes()))
            backup=self.file.with_name('workflow-before-configured-entry-'+hashlib.sha256(original).hexdigest()+'.json')
            if backup.exists():
                if backup.read_bytes()!=original:raise ValueError('company-search-entry-archive-conflict')
            else:
                with backup.open('xb')as archive:archive.write(original)
            if self.file.read_bytes()!=original:raise ValueError('company-search-entry-canonical-drift')
            self.s=updated;self.s['configured_search_entry_recovery']['original_workflow']={'path':str(backup),'sha256':digest(backup)};self.save()
        snapshot,tabs,current=self.tick_snapshot()
        ping=snapshot['ping']
        if ping.get('version')!=VERSION or ping.get('safety')!='DOM-only':raise ValueError('reviewed-extension-version-required')
        self.s['transport_proof']={'safety_version':VERSION,'safety':'DOM-only','reviewed_extension_ready':True}
        t=snapshot['tree'] if self._export_cluster_reused else self.remember_tree(snapshot['tree']);p=self.s['phase'];desired=self.s['date_range']
        from urllib.parse import urlsplit
        after_tabs=snapshot['after'];after=self.source_context(after_tabs)
        if current.get('login_company_picker')or after.get('login_company_picker'):
            if current!=after:raise ValueError('configured-login-transition-during-read')
            return self.configured_login_tick(snapshot,t,current)
        if after['url']!=current['url']:
            if not (p=='verifySwitch' and after.get('post_switch_home') and t.get('url')=='https://life.douyin.com/p/home' and current.get('windowId')==after.get('windowId') and current.get('groupid')==self.s.get('initial_groupid')):raise ValueError('tab-context-changed-during-read')
            current=after;tabs=after_tabs
        if t.get('url')!=urlsplit(current['url'])._replace(query='',fragment='').geturl():raise ValueError('tree-context-path-mismatch')
        home=current.get('post_switch_home') is True
        if home:
            if after.get('windowId')!=current.get('windowId') or current.get('windowId') is None:raise ValueError('post-switch-home-window-changed')
            self.verify_home_company(t)
        initial=self.s.get('initial_groupid')
        if initial is None:
            if p!='account':raise ValueError('initial-company-evidence-missing')
            initial=current['groupid'];self.s['initial_groupid']=initial;self.save()
        target=str(self.job['groupid'])
        if p in ('openReviews','waitReviewManagement','readReviewFilters','reviewProfileRequired','openPageCalendar','calendarProfileRequired','pageStart','pageEnd','verifyFilter'):
            if context_plan is not None and review_visible_system_error(t)is not None:raise ValueError('review-filter-context-recovery-exhausted')
            require_no_review_system_error(t)
        guides=[n for n in nodes(t) if 'src-pages-HomeV3-components-Guide-index-module__guide-modal--' in n.get('attributes',{}).get('class','')]
        if guides and p in ('openReviews','waitReviewManagement','readReviewFilters','verifyFilter'):
            if current['groupid']!=target:raise ValueError('source-company-mismatch')
            self.s['onboarding_resume_phase']=p;self.go('dismissOnboarding');return self.s
        if not home and current['groupid'] not in (initial,target):raise ValueError('source-company-mismatch')
        if p in ('searchCompany','chooseCompany') and current['groupid']!=initial:raise ValueError('source-company-changed-before-confirm')
        if p in ('accountAfterSwitch','identityAfterSwitch','openReviews','waitReviewManagement','readReviewFilters','reviewProfileRequired','openPageCalendar','calendarProfileRequired','pageStart','pageEnd','verifyFilter','clearReviewNegativeShortcut','verifyClearedReviewShortcut','openExportMenu','exportProfileRequired','baselineRecordTabs','openRecordMenu','recordTabAfterOpen','recordsProfileRequired','openExportMenuAgain','openExportDialog','exportDialogProfileRequired','openExportCalendar','exportStart','exportEnd','checkExportRange','readyToExport','submitExport','reloadRecords','pollRecords','armDownload','prepareDownload','clickDownload','downloadResult') and not home and current['groupid']!=target:raise ValueError('source-company-mismatch')
        if self.job.get('identity_contract')=='merchant-v2' and self.s.get('identity') and current['groupid']==target and any('UserCard-index-module__outer--' in n.get('attributes',{}).get('class','') for n in nodes(t)):
            identity(t,self.scoped_identity_baseline(target if home else current['groupid'],'company'))
        if p=='dismissOnboarding':
            guide=unique(guides,'onboarding-guide-not-unique')
            if not all(x in guide.get('name','') for x in ('新来客 新生意','抖音来客全新升级!','导航升级','首页升级')):raise ValueError('onboarding-guide-text-changed')
            if current['groupid']!=target:raise ValueError('source-company-mismatch')
            self.mutate('click',exact({'truncated':False,'root':guide},'立即体验','button'),'onboarding-dismiss');self.go('waitOnboardingClosed')
        elif p=='waitOnboardingClosed':
            if current['groupid']!=target:raise ValueError('source-company-mismatch')
            if guides:
                started=self.s.setdefault('onboarding_wait_started',now())
                if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('onboarding-close-timeout-readonly')
                self.s['waiting_for']='onboarding-close';self.save();return self.s
            self.s.pop('waiting_for',None);self.s.pop('onboarding_wait_started',None);self.go(self.s['onboarding_resume_phase'])
        elif p=='account':
            baseline=self.scoped_identity_baseline(current['groupid'],'entry')
            try:account=identity(t,baseline)
            except ValueError as e:
                if str(e) in ('account-changed',):raise
                provider=unique(sorted(set(re.findall(r'服务商\d+',n['name'])[0] for n in leaves(t) if re.fullmatch(r'服务商\d+',n['name']))),'identity-provider-unverified')
                self.mutate('hover',exact(t,provider),'navigation');self.go('readAccount');return self.s
            self.set_identity(account,current['groupid'],'entry');self.go('context')
        elif p=='readAccount':self.set_identity(identity(t,self.scoped_identity_baseline(current['groupid'],'entry')),current['groupid'],'entry');self.go('context')
        elif p=='context':
            from urllib.parse import urlsplit
            if current['groupid']!=str(self.job['groupid']) and urlsplit(current['url']).path=='/p/governance/violation_list':
                self.mutate('click',self.review_entry_target(t),'navigation');self.go('account');return self.s
            if any(n.get('placeholder')=='搜索商户' for n in nodes(t)):
                self.go('searchCompany');return self.s
            if context_plan is not None and not self.s['review_context_recovery'].get('filter_verified'):
                self.mutate('click',company_switch(t),'navigation');self.go('searchCompany');return self.s
            if current['groupid']==str(self.job['groupid']):
                self.checkpoint('switch',identity=self.s['identity'],company=self.job['company'],groupid=current['groupid']);self.after_switch()
            else:self.mutate('click',company_switch(t),'navigation');self.go('searchCompany')
        elif p=='searchCompany':
            from company_search_wait import field, wait
            target=field(t)
            if target is None:target=wait(self,t,current)
            self.mutate('filter',target,'filter',value=self.job['company']);self.go('chooseCompany')
        elif p=='chooseCompany':
            matches=[n for n in nodes(t) if n.get('name')==self.job['company'] and not any(c.get('name')==self.job['company'] for c in n.get('children',[]))]
            if not matches:
                field=unique([n for n in nodes(t) if n.get('role')=='textbox' and n.get('placeholder')=='搜索商户'])
                if field.get('attributes',{}).get('value')!=self.job['company']:raise ValueError('company-search-value-changed')
                started=self.s.setdefault('company_search_wait_started',now())
                if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('company-search-result-timeout-readonly')
                self.s['waiting_for']='company-search-results';self.save();return self.s
            self.s.pop('waiting_for',None);self.s.pop('company_search_wait_started',None)
            self.mutate('click',exact(t,self.job['company']),'company');self.go('confirmSwitch')
        elif p=='confirmSwitch':
            if self.s.get('configured_login_entry'):
                if current.get('groupid')!=target or any(n.get('placeholder')=='搜索商户'for n in nodes(t)):raise ValueError('configured-login-result-not-stable')
                chosen=[c for c in self.s['calls']if c.get('phase')=='chooseCompany'and c.get('command',{}).get('kind')=='company']
                if len(chosen)!=1 or chosen[0].get('state')!='confirmed' or chosen[0]['command'].get('companyRequest')!=(self.s.get('company_configuration_remaining_operation')if self.s.get('company_search_explicit_recovery')else self.s.get('company_configuration_operation')):raise ValueError('configured-login-original-selection-required')
                identity(t,self.scoped_identity_baseline(target,'company'));self.s.pop('waiting_for',None);self.s.pop('configured_login_wait_started',None);self.go('accountAfterSwitch');return self.s
            if self.s.get('company_search_explicit_recovery')and self.s.get('last_error',{}).get('message')=='company-operation-expired-or-unbounded':
                self.save() # Persist this command's read-only snapshot before strict canonical admission.
                self.s=self._company_configuration.remaining_confirm_expiry_transform(self.job,self.s,self._last_tick_scope_ref)
                self.save() # Typed command CAS; no phase/revision/call or outer-clock change.
            if self.company_confirmation_refusal_retirable():self.reconcile_company_confirmation_refusal()
            settled=len(self.s.get('company_confirm_settle_reads') or [])
            t,tabs,current=self.settle_company_confirmation(t,tabs,current)
            # B87: the click's input authority must come from the same read its
            # locator does. The tick's own scope can predate the picker footer
            # (it renders after the row, while the loading mask is still up),
            # and building the company-confirm command from that stale ref made
            # input_before fail with company-picker-confirm-unique even though
            # the settle read above had already proven the enabled 确认 button.
            # Any settle read appended by this tick is strictly newer than the
            # tick scope, so pointing at its reply keeps locator and authority
            # from ever disagreeing again. Older entries are never used.
            reads=self.s.get('company_confirm_settle_reads') or []
            if len(reads)>settled and isinstance(reads[-1].get('reply'),dict) and reads[-1]['reply'].get('path'):
                self._last_tick_scope_ref=dict(reads[-1]['reply'])
            if not any(n.get('placeholder')=='搜索商户' for n in nodes(t)):
                context(tabs,self.s['tab_id'],self.job['groupid']);self.go('accountAfterSwitch')
            else:
                if current['groupid']!=initial:raise ValueError('source-company-changed-before-confirm')
                self.mutate('click',exact(t,'确认','button'),'company-confirm');self.go('verifySwitch')
        elif p=='verifySwitch':
            if current['groupid']==initial and initial!=target:
                started=self.s.setdefault('company_switch_wait_started',now())
                if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('company-switch-result-timeout-readonly')
                self.s['waiting_for']='company-switch-result';self.save();return self.s
            self.s.pop('waiting_for',None);self.s.pop('company_switch_wait_started',None)
            if not home:context(tabs,self.s['tab_id'],self.job['groupid'])
            self.go('accountAfterSwitch')
        elif p=='accountAfterSwitch':
            try:
                if home:unique([n for n in nodes(t) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')],'identity-card-unverified')
                checked_identity=identity(t,self.scoped_identity_baseline(target if home else current['groupid'],'company'))
                if self.s.get('configured_login_entry'):self.configured_login_identity(checked_identity,current)
            except ValueError as e:
                if str(e)=='account-changed':raise
                provider=(self.job['provider_baseline']if self.s.get('configured_login_entry')else self.s.get('entry_identity',self.s.get('identity',{}))['provider'])
                triggers=[n for n in nodes(t) if n.get('name')==provider and 'Profile-index-module__title--' in n.get('attributes',{}).get('class','')]
                if not triggers and not any(n.get('name') for n in nodes(t) if 'Profile-index-module__title--' in n.get('attributes',{}).get('class','')):
                    started=self.s.setdefault('post_switch_home_account_wait_started',now())
                    if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('post-switch-home-account-load-timeout-readonly')
                    self.s['waiting_for']='post-switch-home-account-trigger';self.save();return self.s
                trigger=unique(triggers,'account-trigger-unverified');self.mutate('hover',trigger,'navigation')
            if self.s.get('last_error',{}).get('code')=='account-trigger-unverified' and all(c.get('state')=='confirmed' for c in self.s.get('calls',[])):
                self.s['resolved_account_read_error']=self.s.pop('last_error')
            self.s.pop('post_switch_home_account_wait_started',None)
            if self.s.get('waiting_for')=='post-switch-home-account-trigger':self.s.pop('waiting_for',None)
            self.go('identityAfterSwitch')
        elif p=='identityAfterSwitch':
            if home:unique([n for n in nodes(t) if 'UserCard-index-module__outer--' in n.get('attributes',{}).get('class','')],'identity-card-unverified')
            value=identity(t,self.scoped_identity_baseline(target if home else current['groupid'],'company'))
            if self.s.get('configured_login_entry')and not self.configured_login_identity(value,current):self.save();return self.s
            if home:
                expected=self.switch_home_contract()
                if value!=expected:raise ValueError('account-changed')
                self.s['post_switch_scope_evidence']={'url':current['url'],'tab_id':self.s['tab_id'],'window_id':current.get('windowId'),'url_groupid_observed':False,'groupid':target,'groupid_basis':'confirmed-exact-company-switch-and-unique-full-identity-registry','full_identity_rechecked':True,'identity':value}
            self.set_identity(value,target if home else current['groupid'],'company');self.checkpoint('switch',identity=self.s['identity'],company=self.job['company'],groupid=str(self.job['groupid']));self.after_switch()
        elif p=='openReviews':
            context(tabs,self.s['tab_id'],self.job['groupid'])
            if not any(re.fullmatch(r'全部评价\s+\d+',n['name']) for n in leaves(t)):
                self.mutate('click',review_management_target(t),'navigation');self.go('waitReviewManagement')
            else:self.mutate('click',all_reviews(t),'navigation');self.go('readReviewFilters')
        elif p=='waitReviewManagement':
            if not any(re.fullmatch(r'全部评价\s+\d+',n['name']) for n in leaves(t)):
                started=self.s.setdefault('review_navigation_wait_started',now())
                if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()>60:raise ValueError('review-navigation-timeout-readonly')
                self.s['waiting_for']='review-management-load';self.save();return self.s
            self.s.pop('waiting_for',None);self.s.pop('review_navigation_wait_started',None);self.go('openReviews')
        elif p=='readReviewFilters':
            # Live review DOM must be reviewed before enabling the next fixed phase.
            self.checkpoint('navigation',groupid=str(self.job['groupid']));self.go('reviewProfileRequired')
        elif p=='reviewProfileRequired':
            fields=review_filter_fields(t)
            for label in ('评价类型','评价来源','评价状态'):
                if fields[label].get('attributes',{}).get('value')!='全部':raise ValueError('nondefault-review-filter:'+label)
            if context_plan is not None:
                value=fields['评价时间'].get('attributes',{}).get('value')
                if value==desired['start']+' ~ '+desired['end']:self.go('verifyFilter');return self.s
                if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2} ~ \d{4}-\d{2}-\d{2}',value):raise ValueError('review-context-filter-date-malformed')
            self.s.pop('waiting_for',None);self.go('openPageCalendar')
        elif p=='openPageCalendar':
            self.mutate('click',review_filter_fields(t)['评价时间'],'filter');self.go('calendarProfileRequired')
        elif p=='calendarProfileRequired':
            calendar_day(t,desired['start']);calendar_day(t,desired['end'])
            self.s.pop('waiting_for',None);self.go('pageStart')
        elif p=='pageStart':
            self.mutate('click',calendar_day(t,desired['start']),'filter');self.go('pageEnd')
        elif p=='pageEnd':
            self.mutate('click',calendar_day(t,desired['end']),'filter');self.go('verifyFilter')
        elif p=='clearReviewNegativeShortcut':
            from review_filter_loading import validate_filter_values
            validate_filter_values(t,desired);all_store_scope(t)
            prior=self.current_call()
            if prior:
                if prior.get('state')!='confirmed':raise ValueError('ui-outcome-unknown-do-not-replay')
                cmd=prior.get('command',{});clicked=prior.get('result',{}).get('clicked',{})
                if cmd.get('op')!='click' or cmd.get('kind')!='filter' or cmd.get('tabId')!=self.s['tab_id'] or cmd.get('locator')!={'by':'selector','value':clicked.get('selector')} or clicked.get('name')!='中差评（1-3心）':raise ValueError('review-shortcut-original-intent-conflict')
            else:
                target=review_shortcut_reset_target(t)
                if target is not None:self.mutate('click',target,'filter')
            self.go('verifyClearedReviewShortcut')
        elif p=='verifyClearedReviewShortcut':
            from review_filter_loading import validate_filter_values
            validate_filter_values(t,desired);all_store_scope(t)
            if review_shortcut_reset_target(t) is not None:raise ValueError('review-shortcut-clear-not-observed-readonly')
            self.go('verifyFilter')
        elif p=='verifyFilter':
            require_no_review_system_error(t)
            if self.advance_date_restore(snapshot,current):return self.s
            t=self.settle_review_filter(t,current)
            if review_shortcut_reset_target(t) is not None:
                from review_filter_loading import validate_filter_values
                validate_filter_values(t,desired);all_store_scope(t);self.go('clearReviewNegativeShortcut');return self.s
            result=self.verified_review_filter_settled(t,tabs,current,desired);all_store_scope(t)
            for label in ('好评（4-5心）','中差评（1-3心）','未回复','已回复','抖音消费','非抖音消费'):
                if set(exact(t,label).get('attributes',{}).get('class','').split())!={'option-YmRyn3'}:raise ValueError('nondefault-review-shortcut:'+label)
            if context_plan is not None:self.s['review_context_recovery']['filter_verified']=True
            self.s['page_filtered']=result['page_filtered'];self.checkpoint('filter',groupid=str(self.job['groupid']),**result);self.go('openExportMenu')
        elif p=='openExportMenu':
            self.mutate('hover',exact(t,'导出'),'export');self.go('exportProfileRequired')
        elif p=='exportProfileRequired':
            verdict,probe=self.settle_export_menu(t)
            if verdict=='ready':
                self.s.pop('waiting_for',None);self.s.pop('export_menu_wait_started',None);self.go('baselineRecordTabs')
            elif verdict=='absent':return self.retry_export_menu_hover(t)
            else:
                if verdict=='incomplete':
                    # Data lag only: park on a pure read and let the next tick
                    # re-read. The deadline exists so a panel that never
                    # finishes rendering still ends in the original error code
                    # (the reviewed reconciliation gate reads exactly that).
                    started=self.s.setdefault('export_menu_wait_started',now())
                    if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()<=86400:
                        self.s['waiting_for']='export-menu-items-not-rendered';self.s['export_menu_probe']=probe;self.save();return self.s
                    self.s['export_menu_wait_expired']={'started':started,'at':now(),'probe':probe};self.save()
                for label in EXPORT_MENU_ITEMS:exact(t,label)
                raise ValueError('export-menu-not-ready')
        elif p=='baselineRecordTabs':
            candidates=record_tabs(tabs,self.job['groupid'])
            self.s['baseline_record_tab_ids']=[x['tabId'] for x in candidates]
            chosen=existing_record_tab(tabs,self.job['groupid'],current['windowId'],self.job.get('record_tab_id'))
            if chosen is not None:
                self.s['record_tab_id']=chosen['tabId'];self.go('recordsProfileRequired')
            else:self.go('openRecordMenu')
        elif p=='openRecordMenu':
            # W131c2: same late dropdown, but only the record entry matters
            # here (the profile phase already proved both items were rendered).
            # No new action is introduced: an unready panel parks on a pure
            # read and the deadline still ends in the original error code.
            verdict,probe=self.settle_export_menu(t,('评价导出记录',))
            if verdict=='ready':
                self.s.pop('waiting_for',None);self.s.pop('export_record_menu_wait_started',None)
            else:
                started=self.s.setdefault('export_record_menu_wait_started',now())
                if (datetime.now(timezone.utc)-datetime.fromisoformat(started)).total_seconds()<=86400:
                    self.s['waiting_for']='export-record-menu-not-rendered';self.s['export_menu_probe']=probe;self.save();return self.s
                self.s['export_record_menu_wait_expired']={'started':started,'at':now(),'verdict':verdict,'probe':probe};self.save()
            self.mutate('click',exact(t,'评价导出记录'),'export');self.go('recordTabAfterOpen')
        elif p=='recordTabAfterOpen':
            candidates=[x for x in record_tabs(tabs,self.job['groupid']) if x['tabId'] not in self.s.get('baseline_record_tab_ids',[])]
            if not candidates:
                recovery=self.recover_record_popup()
                candidates=[recovery['record_tab']] if recovery.get('state')=='complete' and recovery.get('record_tab') else []
            self.s['record_tab_id']=unique(candidates,'new-record-tab-not-unique')['tabId'];self.go('recordsProfileRequired')
        elif p=='recordsProfileRequired':
            verified_review_filter(t,desired);all_store_scope(t)
            if export_baseline_pages.advance(self):
                self.s.pop('waiting_for',None);self.go('openExportMenuAgain')
        elif p=='openExportMenuAgain':
            verified_review_filter(t,desired);all_store_scope(t)
            self.mutate('hover',exact(t,'导出'),'export');self.go('openExportDialog')
        elif p=='openExportDialog':
            self.mutate('click',exact(t,'导出评价'),'export');self.go('exportDialogProfileRequired')
        elif p=='exportDialogProfileRequired':
            t=self.settle_export_dialog(t,current)
            _,field=verified_export_dialog(t,desired,require_dates=False)
            self.s.pop('waiting_for',None)
            self.go('checkExportRange' if field.get('attributes',{}).get('value')==desired['start']+' ~ '+desired['end'] else 'openExportCalendar')
        elif p=='openExportCalendar':
            _,field=verified_export_dialog(t,desired,require_dates=False)
            self.mutate('click',field,'filter');self.go('exportStart')
        elif p=='exportStart':
            self.mutate('click',export_calendar_day(t,desired,desired['start']),'filter');self.go('exportEnd')
        elif p=='exportEnd':
            self.mutate('click',export_calendar_day(t,desired,desired['end']),'filter');self.go('checkExportRange')
        elif p=='checkExportRange':
            verified_export_dialog(t,desired);result=verified_review_filter(t,desired);all_store_scope(t)
            if result['page_filtered']!=self.s['page_filtered']:raise ValueError('filtered-count-changed-before-export')
            self.go('readyToExport')
        elif p=='readyToExport':
            modal,_=verified_export_dialog(t,desired);result=verified_review_filter(t,desired);all_store_scope(t)
            if result['page_filtered']!=self.s['page_filtered']:raise ValueError('filtered-count-changed-before-export')
            if not isinstance(self.s.get('baseline_records'),list) or not self.s.get('record_tab_id'):raise ValueError('export-baseline-unverified')
            context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            if self.s.get('exportPending') or self.s.get('attempts',0):raise ValueError('export-intent-already-exists')
            target=exact({'truncated':False,'root':modal},'导出')
            self.s.update(exportPending=True,attempts=1,submitted_at=now(),export_command={'op':'click','tabId':self.s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'export'})
            self.checkpoint('export-intent',company=self.job['company'],groupid=str(self.job['groupid']),date_range=desired,page_filtered=self.s['page_filtered'])
            self.s.pop('waiting_for',None);self.go('submitExport')
        elif p=='submitExport':
            previous=self.current_call()
            if previous is None:
                modal,_=verified_export_dialog(t,desired)
                target=exact({'truncated':False,'root':modal},'导出')
                if self.s['export_command'].get('locator')!={'by':'selector','value':target['selector']}:raise ValueError('export-target-changed')
                if verified_review_filter(t,desired)['page_filtered']!=self.s['page_filtered']:raise ValueError('filtered-count-changed-before-export')
                all_store_scope(t)
            if previous is None or previous.get('state')=='confirmed':
                self.once(self.s['export_command'])
            # Unknown submission is reconciled only from records, never replayed.
            self.go('reloadRecords')
        elif p=='reloadRecords':
            context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            previous=self.current_call()
            if previous is None or previous.get('state')=='confirmed':
                self.once({'op':'reload-records','tabId':self.s['record_tab_id'],'groupid':str(self.job['groupid']),'reloadKey':self.job['work_order_id']+'-records-'+str(self.s['revision'])})
            else:self.s['reload_outcome_unknown']=True
            self.go('pollRecords')
        elif p=='pollRecords':
            record_tab=context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            record_tree=self.tree(self.s['record_tab_id'])
            record_tree=self.settle_record_page(record_tree,record_tab)
            if record_tree is None:
                # W131b: the mask is gone but the virtual table body is still
                # filling (B57) or its object columns are still async
                # (B36/W101). An unsettled page is unconfirmed, never a
                # baseline - wait for the next readonly tick.
                self.s['waiting_for']='record-page-not-settled';self.save();return self.s
            if record_tree.get('url')!=urlsplit(record_tab['url'])._replace(query='',fragment='').geturl():raise ValueError('record-tree-path-mismatch')
            proof,row=self._resolve_record_row(record_tree,desired);self.s['postsubmit_record_page']=proof['page']
            bound=self.s.get('generated_record') if isinstance(self.s.get('generated_record'),dict) and self.s['generated_record'].get('bound_by') else None
            if row is None or row['state']=='pending':
                if self.s.get('reload_outcome_unknown'):raise ValueError('record-refresh-outcome-unknown-readonly-only')
                if self.s.get('submitted_at') and (datetime.now(timezone.utc)-datetime.fromisoformat(self.s['submitted_at'])).total_seconds()>600:raise ValueError('export-outcome-unknown-no-resubmit')
                self.s['waiting_for']='generated-export-record-not-visible-or-ready-on-first-page';self.save();return self.s
            elif row['state']=='failed':
                self.s.update(exportPending=False,state='failed',error_code='platform-export-failed',failed_record=row);self.save()
            else:
                started=datetime.fromisoformat(self.s['submitted_at']).astimezone(ZoneInfo('Asia/Shanghai')).replace(microsecond=0)
                generated=datetime.strptime(row['generated_at'],'%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Shanghai'))
                # B92: a bound artifact was proven pre-existing by the identity
                # reconcile (submission created nothing); the submission window
                # check only governs rows this run's submission created.
                if not bound and generated<started:raise ValueError('generated-record-predates-export-intent')
                self.s.update(generated_record={**bound,**row} if bound else row,record_url=record_tab['url']);self.s.pop('waiting_for',None)
                self.checkpoint('export-generated',generated_at=row['generated_at'],text=row['text'],record_url=record_tab['url']);self.go('armDownload')
        elif p=='armDownload':
            record_tab=context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            record_tree=self.tree(self.s['record_tab_id'])
            if record_tree.get('url')!=urlsplit(record_tab['url'])._replace(query='',fragment='').geturl():raise ValueError('record-tree-path-mismatch')
            proof,row=self._resolve_record_row(record_tree,desired)
            if not row or row['state']!='success' or row['generated_at']!=self.s['generated_record']['generated_at']:raise ValueError('download-record-changed')
            self.s['postsubmit_record_page']=proof['page']
            self.expect_download_collision()
            result=self.once({'op':'download-begin','tabId':self.s['record_tab_id']})
            if not isinstance(result.get('ticket'),str) or not result['ticket'] or not result.get('since') or not isinstance(result.get('expires'),(int,float)) or result['expires']<=datetime.now(timezone.utc).timestamp()*1000:raise ValueError('download-ticket-unverified')
            self.s['download_ticket']=result;self.go('prepareDownload')
        elif p=='prepareDownload':
            record_tab=context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            record_tree=self.tree(self.s['record_tab_id'])
            if record_tree.get('url')!=urlsplit(record_tab['url'])._replace(query='',fragment='').geturl():raise ValueError('record-tree-path-mismatch')
            proof,row=self._resolve_record_row(record_tree,desired);self.s['postsubmit_record_page']=proof['page']
            if not row or row['state']!='success' or row['generated_at']!=self.s['generated_record']['generated_at']:raise ValueError('download-record-changed')
            source=unique([n for n in nodes(record_tree) if n.get('selector')==row['selector']],'download-row-not-unique')
            target=exact({'truncated':False,'root':source},'下载')
            self.s.update(downloadPending=True,download_command={'op':'click','tabId':self.s['record_tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'download'})
            self.checkpoint('download-intent',generated_at=row['generated_at'],ticket=self.s['download_ticket']['ticket']);self.go('clickDownload')
        elif p=='clickDownload':
            record_tab=context(tabs,self.s['record_tab_id'],self.job['groupid'],record=True)
            previous=self.current_call()
            if previous is None:
                if self.s['download_ticket']['expires']<=datetime.now(timezone.utc).timestamp()*1000:raise ValueError('download-ticket-expired-before-click')
                # The preceding phase derived this exact row selector from live DOM.
                record_tree=self.tree(self.s['record_tab_id'])
                if record_tree.get('url')!=urlsplit(record_tab['url'])._replace(query='',fragment='').geturl():raise ValueError('record-tree-path-mismatch')
                proof,row=self._resolve_record_row(record_tree,desired);self.s['postsubmit_record_page']=proof['page']
                if not row or row['state']!='success' or row['generated_at']!=self.s['generated_record']['generated_at']:raise ValueError('download-record-changed')
                source=unique([n for n in nodes(record_tree) if n.get('selector')==row['selector']],'download-row-not-unique')
                target=exact({'truncated':False,'root':source},'下载')
                if target['selector']!=self.s['download_command']['locator']['value']:raise ValueError('download-target-changed')
            if previous is None or previous.get('state')=='confirmed':self.once(self.s['download_command'])
            self.go('downloadResult')
        else:raise ValueError('workflow-phase-invalid')
        return self.s
    def finish_download(self):
        # This phase consumes the original ticket/file, not a merchant DOM tree.
        # A timed-out original click may only reconcile its existing download.
        command=self.s.get('download_command')
        clicks=[c for c in self.s.get('calls',[]) if c.get('command',{}).get('kind')=='download']
        begins=[c for c in self.s.get('calls',[]) if c.get('command',{}).get('op')=='download-begin']
        if not isinstance(command,dict) or command.get('op')!='click' or command.get('kind')!='download' or command.get('tabId')!=self.s.get('record_tab_id') or len(clicks)!=1 or clicks[0].get('command')!=command or clicks[0].get('state') not in ('confirmed','unknown'):
            raise ValueError('original-download-click-required')
        if len(begins)!=1 or begins[0].get('state')!='confirmed' or begins[0].get('command')!={'op':'download-begin','tabId':self.s['record_tab_id']} or begins[0].get('result')!=self.s.get('download_ticket'):
            raise ValueError('original-download-ticket-required')
        result=self.download_status()
        if result.get('state')=='pending':
            recovery=self.recover_download_popup()
            if recovery.get('download_status',{}).get('state')=='complete':result=recovery['download_status']
        if result.get('state')!='complete':
            scanned=self.filesystem_download_reconcile(result)
            if scanned is not None:result=scanned
        if result.get('state')!='complete':
            self.s['waiting_for']='download-complete';self.save();return self.s
        file=self.verify_download(result)
        self.s['download_receipt']=result;self.s.pop('waiting_for',None)
        self.checkpoint('download-complete',path=str(file),sha256=digest(file),ticket=self.s['download_ticket']['ticket'])
        self.s['result']={'source':str(file),'src_sha256':digest(file),'download_verified':True,'download_ticket':self.s['download_ticket'],
            'download_receipt':result,'backend':'local-dom-bridge','transport_proof':self.s['transport_proof'],'work_order_id':self.job['work_order_id'],
            'company':self.job['company'],'groupid':str(self.job['groupid']),'date_range':self.s['date_range'],'page_filtered':self.s['page_filtered'],
            'identity':self.s['identity'],'identity_before':self.s['identity'],'account_verified':True,'record_url':self.s['record_url'],
            'record_generated_at':self.s['generated_record']['generated_at'],'source_is_authoritative_export':True}
        self.s.update(exportPending=False,downloadPending=False,state='complete');self.go('done')
        return self.s
    def download_status(self):
        ticket=self.s['download_ticket']
        try:return self.call({'op':'download-status','ticket':ticket['ticket']})
        except RuntimeError as exc:
            if str(exc)!='bridge-command-failed: download ticket missing or expired':raise
        # The original durable intent survives an extension update or timeout.
        # Read Chrome's public download list for this exact file/time/scope only;
        # do not arm a new ticket, invoke download(), or click the page again.
        command={'op':'download-reconcile','tabId':self.s['record_tab_id'],
                 'groupid':str(self.job['groupid']),'ticket':ticket['ticket'],'since':ticket['since'],
                 'filename':export_tag(self.s['date_range'])+'.xlsx'}
        self.s['download_reconciliation']={'command':command,'readonly':True,'at':now()};self.save()
        return self.call(command)
    def expect_download_collision(self):
        # W131d write-side foreknowledge (Easel _unique_upload_path idea, but
        # read-only): a bare "<tag>.xlsx" already in Downloads means Chrome
        # will save this export as "<tag> (2).xlsx". Knowing it BEFORE the
        # click turns a later surprise into a journaled fact. Nothing here may
        # delete, move or rename a user file; an occupied bare name stays a
        # fact, never an obstacle we clear ourselves.
        if 'download_collision_expected' in self.s:return self.s['download_collision_expected']
        bare=Path.home()/'Downloads'/(export_tag(self.s['date_range'])+'.xlsx')
        if bare.is_file() and not bare.is_symlink():
            st=bare.stat()
            self.s['download_collision_expected']={'bare_name_present':True,'name':bare.name,'size':st.st_size,'mtime':st.st_mtime,'at':now()}
            self.save();return self.s['download_collision_expected']
        return None

    def filesystem_download_reconcile(self,result):
        # The original click may have landed under a Chrome collision suffix:
        # an earlier same-day export already held the bare name, so Chrome
        # saved this one as "<tag> (2).xlsx". The extension reconcile refuses
        # suffixes by policy; this supervised readonly filesystem scan admits
        # exactly one matching file with full evidence, never arms a ticket,
        # invokes download(), or clicks the page again.
        armed=self.s.get('download_reconciliation')
        if not(type(armed)is dict and armed.get('readonly')is True):return None
        ticket=self.s['download_ticket']
        if not(type(ticket)is dict and type(ticket.get('since'))is str and type(ticket.get('ticket'))is str):return None
        tag=export_tag(self.s['date_range'])
        pattern=re.compile(re.escape(tag)+r'(?: \(\d+\))?\.xlsx$')
        try:since_epoch=datetime.fromisoformat(ticket['since'].replace('Z','+00:00')).timestamp()
        except ValueError:return None
        candidates=[]
        for p in (Path.home()/'Downloads').iterdir():
            if not p.is_file() or not pattern.fullmatch(p.name):continue
            if p.stat().st_mtime+1<since_epoch:continue
            candidates.append(p)
        if not candidates:return None
        if len(candidates)>1:raise ValueError('filesystem-download-reconcile-ambiguous-no-replay')
        file=candidates[0]
        # W131d read-side stability: Chrome creates the .xlsx and then writes
        # it, so a file that exists is not yet a file that is finished. Two
        # agreeing sizes past the mtime margin is what "complete" means; a
        # still-growing file returns None so the caller keeps its existing
        # download-complete wait (600s outer bound) instead of shipping a
        # half-written receipt.
        try:size=file_size_stable(file,2.0,.25,.3)
        except ValueError as error:
            if str(error)!='download-size-unconfirmed':raise
            return None
        if size<=0:raise ValueError('filesystem-download-reconcile-empty-file')
        receipt={'state':'complete','downloadId':None,'path':str(file),'exists':True,'bytesReceived':size,'totalBytes':size,
                 'ticket':ticket['ticket'],'reconciled':True,'readonly':True,'source':'filesystem-reconcile-v1','at':now()}
        self.s['download_filesystem_reconciliation']={'filename':file.name,'size':size,'mtime':file.stat().st_mtime,
                 'sha256':digest(file),'chrome_reconcile_result':result,'at':now()};self.save()
        return receipt
    def verify_download(self,receipt):
        if receipt.get('exists') is not True or receipt.get('state')!='complete':raise ValueError('download-file-not-reported-complete')
        raw=Path(receipt.get('path',''))
        if not raw.is_absolute() or raw.is_symlink() or not raw.is_file() or raw.suffix.lower()!='.xlsx':raise ValueError('download-file-unverified')
        file=raw.resolve()
        # W131d: wait for a quiet size before hashing. The old order hashed
        # first and detected a change afterwards, which proved the file moved
        # under us but only after the fact. No new error code: an unstable
        # file is the existing download-file-changed-during-verification.
        try:size=file_size_stable(file,1.0,.25,0)
        except ValueError as error:
            if str(error)!='download-size-unconfirmed':raise
            raise ValueError('download-file-changed-during-verification')
        if size<=0 or receipt.get('bytesReceived')!=size or (receipt.get('totalBytes',0)>0 and receipt['totalBytes']!=size):raise ValueError('download-size-mismatch')
        before=digest(file)
        try:
            with ZipFile(file) as z:
                if not {'[Content_Types].xml','xl/workbook.xml'}<=set(z.namelist()) or z.testzip():raise ValueError('download-xlsx-invalid')
        except BadZipFile:raise ValueError('download-xlsx-invalid')
        if digest(file)!=before or file.stat().st_size!=size:raise ValueError('download-file-changed-during-verification')
        return file

    def recover_download_popup(self):
        # No second page download click. A single wrapper owns focus + AX probe
        # + any admitted list/link chain; repeat recovery can only read the ticket.
        directory=self.file.parent/'native-download-navigation'
        receipt=directory/'recovery.json'
        calls=[c for c in self.s.get('calls',[]) if c.get('command',{}).get('kind')=='download']
        if len(calls)!=1 or calls[0].get('state')!='confirmed':
            return {'state':'await-download','phase':'download-click-outcome-unconfirmed'}
        module_spec=importlib.util.spec_from_file_location('durable_download_popup_recovery',Path(__file__).with_name('popup-recover-download.py'))
        module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
        allow_expired=True
        if receipt.exists():
            saved=json.loads(receipt.read_text());pid=saved['expected_pid']
            allow_expired=saved.get('allow_expired_readonly_reconcile',False)
        else:
            native=module.popup.PopupShellInspector()
            try:pid=native.pid
            finally:native.close()
        self.save()
        result=module.recover(self.job,self.s['record_tab_id'],pid,directory,invoke=self.invoke,
                              allow_expired_readonly_reconcile=allow_expired,probe_pending=True)
        evidence=receipt if receipt.exists() else directory/'probe.json'
        self.s['native_download_navigation']={'path':str(evidence),'sha256':digest(evidence),
            'state':result.get('state'),'phase':result.get('phase'),'replayed':False}
        self.save();return result

    def recover_record_popup(self):
        # The role owns this normal Chrome UI navigation; no model-selected
        # clicks, browser settings, debugging interfaces or guessed destinations.
        module_spec=importlib.util.spec_from_file_location('durable_record_popup_recovery',Path(__file__).with_name('popup-recover-record.py'))
        module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
        native=module.popup.PopupShellInspector()
        try:pid=native.pid
        finally:native.close()
        directory=self.file.parent/'native-record-navigation'
        self.save() # Recovery validates the exact current formal journal.
        result=module.recover(self.job,self.s['tab_id'],pid,directory,invoke=self.invoke)
        receipt=directory/'recovery.json'
        self.s['native_record_navigation']={'path':str(receipt),'sha256':digest(receipt),'state':result.get('state'),'replayed':False}
        self.save();return result
    def after_switch(self):
        if self.job['action']=='return-company':
            self.s.update(state='complete',result={'verified':True,'company':self.job['company'],'groupid':str(self.job['groupid']),'identity':self.s['identity'],'backend':'local-dom-bridge'})
            self.go('done')
        else:self.go('openReviews')
    def set_identity(self,value,groupid=None,scope='company'):
        if self.job.get('identity_contract')=='merchant-v2':
            expected=self.scoped_identity_baseline(groupid,scope)
            if set(value)!={'provider','account_id','manager'} or not all(isinstance(v,str) and v for v in value.values()):raise ValueError('full-merchant-identity-required')
            if scope=='company' and not self.s.get('identity') and self.s.get('phase')!='identityAfterSwitch':raise ValueError('target-identity-before-confirmed-switch')
            provider=self.s.get('provider_baseline')
            if provider is None:
                origin=self.s.get('identity_bootstrap_origin',{})
                if scope!='entry' or self.s.get('entry_identity') or str(groupid) not in origin.get('allowed_groupids',[]) or self.s.get('phase') not in ('account','readAccount') or has_side_effect_intent(self.s):raise ValueError('bootstrap-provider-repin-forbidden')
                if not re.fullmatch(r'服务商\d+',value['provider']):raise ValueError('provider-changed')
                self.s['provider_baseline']=provider=value['provider']
                self.checkpoint('provider-bootstrap',provider=provider,groupid=str(groupid))
            if value.get('provider')!=provider:raise ValueError('provider-changed')
            if expected and value!=expected:raise ValueError('account-changed')
            if scope=='entry':
                if self.s.get('entry_identity') and self.s['entry_identity']!=value:raise ValueError('account-changed')
                self.s.update(entry_identity=value,entry_groupid=str(groupid))
                self.checkpoint('identity',identity=value,identity_scope='entry',groupid=str(groupid))
                if str(groupid)!=str(self.job['groupid']):return
                # Already on the target: the known full entry identity is also
                # the target identity, never an unrelated source merchant.
            self.s.update(identity=value,identity_before=value)
            self.checkpoint('identity',identity=value,identity_scope='company',groupid=str(groupid))
        else:
            if self.job.get('identity_baseline') and value!=self.job['identity_baseline']:raise ValueError('account-changed')
            if self.s.get('identity') and self.s['identity']!=value:raise ValueError('account-changed')
            self.s['identity']=value
            self.checkpoint('identity',identity=value)
        self.s['transport_proof']={'safety_version':VERSION,'safety':'DOM-only','reviewed_extension_ready':True}

@contextlib.contextmanager
def _search_command_lifecycle(self):
    if not self.s.get('company_search_explicit_recovery'):
        yield;return
    module=getattr(self,'_company_configuration',None)
    if module is None:raise ValueError('search-progression-module-required')
    if hasattr(self,'_typed_canonical_bytes'):
        # Nested tick retains the enclosing run_steps token for error persistence.
        yield;return
    with module.search_progression_command():
        module.search_progression_admission(self.s,self.s['company_configuration_job'])
        self._typed_canonical_bytes=module.regular(self.file).read_bytes()
        try:yield
        finally:del self._typed_canonical_bytes
Workflow.search_command_lifecycle=_search_command_lifecycle

_original_untyped_tick=Workflow.tick
def _typed_tick(self):
    if not self.s.get('company_search_explicit_recovery'):return _original_untyped_tick(self)
    with self.search_command_lifecycle():return _original_untyped_tick(self)
Workflow.tick=_typed_tick

_original_untyped_save=Workflow.save
def _typed_save(self):
    if not self.s.get('company_search_explicit_recovery'):return _original_untyped_save(self)
    module=getattr(self,'_company_configuration',None)
    if module is None:raise ValueError('search-progression-module-required')
    expected=getattr(self,'_typed_canonical_bytes',None)
    if expected is None:raise ValueError('search-progression-save-outside-checked-command')
    if module.regular(self.file).read_bytes()!=expected:raise ValueError('search-progression-canonical-CAS-conflict')
    result=_original_untyped_save(self)
    self._typed_canonical_bytes=module.regular(self.file).read_bytes()
    return result
Workflow.save=_typed_save

def step_count(value):
    try:value=int(value)
    except (TypeError,ValueError):raise argparse.ArgumentTypeError('steps must be an integer from 1 to 25')
    if not 1<=value<=25:raise argparse.ArgumentTypeError('steps must be an integer from 1 to 25')
    return value

# ---------------------------------------------------------------------------
# B63: a render wait is a re-read, not a manual hold. Every waiting marker below
# is set by a branch that has just clicked something and whose next step is a
# pure DOM re-read (the page has not painted yet); most of them own an internal
# deadline that raises the reviewed timeout code, and that deadline can only be
# reached if the tick is entered again. _run_steps used to stop on any
# waiting_for, so each of these got exactly one look and then froze the run -
# the same shape that already forced the download-complete and
# company-search-results exceptions above. company-switch-readonly-scope is
# deliberately absent: it is an archived read contract (switch_read_recovery),
# not a render wait, and re-ticking it would bypass that contract.
# ---------------------------------------------------------------------------
RENDER_WAIT_STATES=frozenset({'configured-login-result','onboarding-close','company-switch-result',
                              'post-switch-home-account-trigger','review-management-load',
                              'export-menu-hover-retried','export-menu-items-not-rendered',
                              'export-record-menu-not-rendered','record-page-not-settled',
                              'generated-export-record-not-visible-or-ready-on-first-page'})

def _run_steps(w,file,steps=1,status=False):
    def output(step):
        print(json.dumps({'state':w.s['state'],'phase':w.s['phase'],'waiting_for':w.s.get('waiting_for'),
                          'journal':str(file),'step':step},ensure_ascii=False),flush=True)
    if status:
        output(0);return
    for index in range(steps):
        # Reviewed profiles are validated by tick itself, including all fields
        # and source scope. Only an actual waiting marker is a manual hold;
        # a historical phase name is not a request for another model decision.
        # A known owned download wait permits one fresh status tick per call.
        # Pending returns below immediately; never rearm/click or bypass an
        # unresolved intent/error. Other waiting markers keep their old hold.
        download_wait=(w.s.get('phase')=='downloadResult' and
                       w.s.get('waiting_for')=='download-complete' and
                       not w.s.get('last_error') and
                       (w.calls_progression_safe()if w.s.get('company_search_explicit_recovery')else all(c.get('state') in ('confirmed','rejected') for c in w.s.get('calls',[]))))
        # Only this confirmed search may perform one normal fresh-read tick.
        # chooseCompany owns the original 60s clock: ready may progress even
        # after a pause; still-missing results time out without another search.
        company_search_wait=(w.s.get('phase')=='chooseCompany' and
                             w.s.get('waiting_for')=='company-search-results' and
                             not w.s.get('last_error') and w.s.get('calls') and
                             (w.calls_progression_safe()if w.s.get('company_search_explicit_recovery')else all(c.get('state')=='confirmed'for c in w.s['calls'])) and
                             w.s['calls'][-1].get('phase')=='searchCompany' and
                             w.s['calls'][-1].get('command',{}).get('value')==w.job['company'])
        # B63: a render wait may take one fresh read per tick; it never inputs,
        # never rearms and never bypasses an unresolved intent/error.
        render_wait=(w.s.get('waiting_for')in RENDER_WAIT_STATES and
                     not w.s.get('last_error') and
                     all(c.get('state')=='confirmed' for c in w.s.get('calls',[])))
        stopped=w.s['state']!='running' or (steps>1 and w.s.get('waiting_for') and not download_wait and not company_search_wait and not render_wait)
        if stopped:
            if index==0:output(0)
            break
        try:w.tick()
        except Exception as exc:
            if not w.s.get('last_error'):w.s['last_error']={'at':now(),'code':str(exc).split(':')[0],'message':str(exc)}
            if isinstance(w,Workflow) and w.review_tab_zero_match()is not None:
                # The owned extension reply proves one() rejected before click.
                # One fresh semantic re-location may use the same original key.
                w.save();w.prepare_review_tab_preinput();time.sleep(.25)
                # This rejected lookup performed no input. Finish its sole
                # bounded recovery inside the same logical step, including
                # when the caller's chunk ends here. A second failure escapes.
                try:w.tick()
                except Exception:
                    w.save();raise
                output(index+1)
                if w.s['state']!='running' or w.s.get('waiting_for'):break
                continue
            if not w.s.get('company_search_explicit_recovery'):w.save();raise
            try:w.save()
            except Exception as persistence_error:raise exc from persistence_error
            raise
        output(index+1)
        if w.s['state']!='running' or w.s.get('waiting_for'):break

def run_steps(w,file,steps=1,status=False):
    # One invocation only. Plain scheduling fakes retain the old public API.
    if not isinstance(w,Workflow):return _run_steps(w,file,steps,status)
    w._export_cluster_token=None;w._export_cluster_active=not status;w._export_cluster_blocked=False
    try:return _run_steps(w,file,steps,status)
    finally:
        w._export_cluster_token=None;w._export_cluster_active=False
        w._export_cluster_origin=None;w._export_cluster_reused=False;w._export_cluster_blocked=False

_configured_original_run_steps=run_steps
def run_steps(w,file,steps=1,status=False):
    module=getattr(w,'_company_configuration',None)
    if module is None:return _configured_original_run_steps(w,file,steps,status)
    with module.configuration_command():
        if w.s.get('company_search_explicit_recovery'):
            with w.search_command_lifecycle():return _configured_original_run_steps(w,file,steps,status)
        return _configured_original_run_steps(w,file,steps,status)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work-order',type=Path,required=True);p.add_argument('--tab-id',type=int,required=True);p.add_argument('--status',action='store_true')
    p.add_argument('--steps',type=step_count,default=1,help='1..25 durable ticks; reviewed profiles validate in code; actual waits/errors stop the batch')
    p.add_argument('--reconcile-rejected-company-switch',action='store_true',help='After reviewed v7 upgrade: reconcile only the exact pre-action merchant switch policy denial; performs no click')
    p.add_argument('--reconcile-company-confirmation-loading',action='store_true');p.add_argument('--reconcile-export-menu-hover',action='store_true');p.add_argument('--failure');p.add_argument('--failure-sha256')
    a=p.parse_args(argv)
    job=json.loads(a.work_order.read_text());file=Path(job['workflow_path']);file.parent.mkdir(parents=True,exist_ok=True)
    try:
        with file.with_name('.bridge-execution.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            w=Workflow.read_company_confirmation_reconciliation(job,a.tab_id) if a.reconcile_company_confirmation_loading else (Workflow.read_export_menu_reconciliation(job,a.tab_id) if a.reconcile_export_menu_hover else Workflow(job,a.tab_id))
            if a.reconcile_company_confirmation_loading:
                if a.status or a.steps!=1 or a.reconcile_rejected_company_switch:raise ValueError('reconciliation-must-be-standalone')
                w.reconcile_company_confirmation_loading({'path':str(Path(a.failure).absolute()),'sha256':a.failure_sha256})
                print(json.dumps({'state':w.s['state'],'phase':w.s['phase'],'reconciled':True,'ui_action_performed':False,'journal':str(file)},ensure_ascii=False))
            elif a.reconcile_rejected_company_switch:
                if a.status or a.steps!=1:raise ValueError('reconciliation-must-be-standalone')
                w.reconcile_rejected_company_switch()
                print(json.dumps({'state':w.s['state'],'phase':w.s['phase'],'reconciled':True,'ui_action_performed':False,'journal':str(file)},ensure_ascii=False))
            elif a.reconcile_export_menu_hover:
                if a.status or a.steps!=1:raise ValueError('reconciliation-must-be-standalone')
                w.reconcile_export_menu_hover({'path':str(Path(a.failure).absolute()),'sha256':a.failure_sha256})
                print(json.dumps({'state':w.s['state'],'phase':w.s['phase'],'reconciled':True,'ui_action_performed':False,'journal':str(file)},ensure_ascii=False))
            else:run_steps(w,file,a.steps,a.status)
        return 0
    except Exception as exc:print(json.dumps({'ok':False,'error':str(exc)},ensure_ascii=False),flush=True);return 1

def _configured_timing():
 import importlib.util
 path=ROOT/'skills/workshop-director/scripts/execution_timing.py'
 if not path.is_absolute()or not path.is_file()or path.resolve()!=path or any(x.is_symlink()for x in(path,*path.parents)):raise ValueError('company-config-resolver-origin')
 before=path.read_bytes();expected={'path':str(path),'sha256':hashlib.sha256(before).hexdigest()};prior=sys.modules.get('execution_timing')
 if prior is not None:
  if getattr(prior,'__file__',None)!=str(path)or getattr(prior,'_CONFIGURATION_MODULE_SOURCE',None)!=expected:raise ValueError('company-config-loaded-resolver-drift')
  return prior
 spec=importlib.util.spec_from_file_location('execution_timing',path);module=importlib.util.module_from_spec(spec);exec(compile(before,str(path),'exec'),module.__dict__)
 if path.read_bytes()!=before or path.resolve()!=path or any(x.is_symlink()for x in(path,*path.parents))or module._CONFIGURATION_MODULE_SOURCE!=expected:raise ValueError('company-config-resolver-drift')
 sys.modules['execution_timing']=module;return module
_CONFIGURED_RUN_STEPS=run_steps
def run_steps(w,file,steps=1,status=False):
 if getattr(w,'_company_configuration',None)is None:return _CONFIGURED_RUN_STEPS(w,file,steps,status)
 with _configured_timing().company_policy_command():return _CONFIGURED_RUN_STEPS(w,file,steps,status)

if __name__=='__main__':raise SystemExit(main())
