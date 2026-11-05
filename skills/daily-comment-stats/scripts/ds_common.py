"""Validation, atomic receipts, locks and fail-closed company matching."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

SKILL = Path(__file__).resolve().parents[1]
PROJECT = SKILL.parents[1]
MAPPING = SKILL / 'config/company_wecom_map.csv'
VERSION = '1.2.0'

class FlowError(Exception):
    def __init__(self, code, message=None, fatal=False):
        self.code, self.fatal = code, fatal
        super().__init__(message or code)

def now(): return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.'+path.name, dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

@contextmanager
def lock(directory):
    import fcntl
    p = Path(directory); p.mkdir(parents=True, exist_ok=True)
    with open(p / '.workflow.lock', 'a') as stream:
        try: fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: raise FlowError('run-locked', 'Another process is using this output directory')
        try: yield
        finally: fcntl.flock(stream, fcntl.LOCK_UN)

def normalize(value):
    value = unicodedata.normalize('NFKC', str(value or '')).lower()
    return ''.join(c for c in value if c.isalnum())

def variants(name):
    value = normalize(name); result = {value}
    for suffix in ('集团有限公司', '股份有限公司', '有限责任公司', '有限公司'):
        if value.endswith(suffix): result.add(value[:-len(suffix)])
    return result - {''}

def match_name(target, names):
    target_set = variants(target)
    exact = [n for n in names if normalize(n) == normalize(target)]
    if not exact: exact = [n for n in names if variants(n) & target_set]
    if exact:
        if len(exact) == 1: return exact[0]
        raise FlowError('company-ambiguous', 'Company name matches multiple candidates')
    contained = [n for n in names if any(a in b or b in a for a in target_set for b in variants(n))]
    if len(contained) == 1: return contained[0]
    raise FlowError('company-ambiguous' if contained else 'company-not-found', 'No unique company match')

def load_map(path=MAPPING):
    rows = []
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['公司名称', '企业微信群']: raise FlowError('mapping-schema', 'CSV headers must be 公司名称,企业微信群')
        seen = set()
        for row in reader:
            name, group = (row.get('公司名称') or '').strip(), (row.get('企业微信群') or '').strip()
            if not name and not group: continue
            if not name or not group or None in row: raise FlowError('mapping-invalid', 'Empty or extra mapping fields')
            if normalize(name) in seen: raise FlowError('mapping-duplicate', 'Duplicate normalized company')
            seen.add(normalize(name)); rows.append({'seq':len(rows)+1, 'company':name, 'wecom_group':group})
    if not rows: raise FlowError('mapping-empty')
    return rows

def select_company(mapping, name=None):
    if name:
        selected = match_name(name, [r['company'] for r in mapping])
        return next(row for row in mapping if row['company'] == selected)
    if len(mapping) != 1: raise FlowError('company-required', 'Multi-company mapping requires --company')
    return mapping[0]

def company_dir(root, company):
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', company['company']).strip('. ')
    return Path(root) / ('%02d_%s' % (company['seq'], safe))

def output_root(today, start, end, base=None):
    return Path(base) if base else PROJECT / 'work' / today / ('%s至%s' % (start, end))

def receipt_valid(receipt, src, identity, date_range, mapping_hash):
    if not isinstance(receipt,dict): return False
    if receipt.get('source_kind')=='daily-visible-dom-source-v1':
        try:validated_dom_receipt(receipt,src,identity,date_range,mapping_hash);return True
        except (FlowError,ValueError,KeyError,TypeError,OSError):return False
    if receipt.get('status') not in ('complete', 'needs_review', 'zero_rows'): return False
    if receipt.get('version') != VERSION or receipt.get('company') != identity['company']: return False
    if receipt.get('wecom_group') != identity['wecom_group'] or receipt.get('mapping_sha256') != mapping_hash: return False
    if receipt.get('date_range') != {'start':date_range['start'], 'end':date_range['end']}: return False
    if receipt.get('range_warnings',[]) != date_range.get('warnings',[]): return False
    if receipt.get('src_sha256') != sha256(src): return False
    try:
        shape=(receipt.get('status')=='zero_rows' and receipt.get('zero_rows') is True and receipt.get('row_count')==0 and not receipt.get('artifacts')) or (receipt.get('zero_rows') is False and len(receipt.get('artifacts', []))==3)
        return shape and all(Path(item['path']).is_file() and sha256(item['path']) == item['sha256'] for item in receipt.get('artifacts', []))
    except (OSError,KeyError,TypeError): return False


def acquisition_backend_valid(evidence):
    if evidence.get('operator_skill')!='douyin-laike-operator': return False
    backend=evidence.get('backend')
    if backend=='codex-existing-extension': return True
    if backend!='local-dom-bridge': return False
    proof=evidence.get('transport_proof',{})
    return (proof.get('safety_version') in ('dom-only-20261021-3','dom-only-20261021-4','dom-only-20261021-5','dom-only-20261021-6','dom-only-20261021-7','dom-only-20261021-8','dom-only-20261021-9','dom-only-20261021-10','dom-only-20261021-11','dom-only-20261103-12') and
            proof.get('safety')=='DOM-only' and proof.get('reviewed_extension_ready') is True)

# Literal is sealed after the independent producer freeze. Never import a
# caller-provided module, or infer trust from a module's self-reported hash.
DOM_PRODUCER_SHA256 = '0b5479e2271aa3d4118a84e9374daa1f899c4fbd8784ca080568785367a8d22d'
DOM_CAPTURE_SHA256 = '0b4ce7147ed84581bf3d01180a94c6c0a5faae5074853bd3cea6fa6b8bcc9489'

def dom_capture_module():
    import importlib.util
    import sys
    path=Path(__file__).absolute().with_name('dom_fresh_capture.py')
    if not path.is_file()or any(p.is_symlink()for p in (path,*path.parents))or path.resolve()!=path or sha256(path)!=DOM_CAPTURE_SHA256:
        raise FlowError('dom-capture-code-unavailable-or-changed')
    name='_daily_fresh_dom_capture_'+DOM_CAPTURE_SHA256
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__);sys.modules[name]=module
    module=sys.modules[name]
    if Path(module.__file__)!=path:raise FlowError('dom-capture-module-origin')
    return module

def dom_capture_data(capture_ref,payload,state=None,row=None):
    if not capture_ref:raise FlowError('dom-fresh-capture-required')
    module=dom_capture_module();command=_DOM_COMMAND.get()
    key=json.dumps([capture_ref,payload,DOM_CAPTURE_SHA256,DOM_PRODUCER_SHA256],ensure_ascii=False,sort_keys=True)
    try:
        import copy
        cache=command.setdefault('captures',{})if command is not None else{}
        if key in cache:
            facts=copy.deepcopy(cache[key]);_dom_dependencies_fresh(facts['verification_refs'])
            command['capture_hits']=command.get('capture_hits',0)+1
        else:
            facts=module.verify_capture(capture_ref,payload)
            if command is not None:
                cache[key]=copy.deepcopy(facts);command['capture_computes']=command.get('capture_computes',0)+1
        # Historical lease is archived; current operator source is ALWAYS fresh.
        _dom_dependencies_fresh([facts['workflow']])
        job=facts['job']
        if state is not None:
            original=dom_producer().pinned(job['original_job'])
            if state['dispatch_scope']['work_order']!=job['original_order']or Path(state['run_dir'])!=Path(original['workflow_path']).parents[3]:raise FlowError('dom-capture-batch-context')
        if row is not None and (row['company']!=job['company']or str(row['groupid'])!=str(job['groupid'])or {k:row['date_range'][k]for k in ('start','end')}!=job['date_range']):raise FlowError('dom-capture-row-context')
        if command is not None and 'producer_data'in facts:
            source_key=_dom_source_key(payload,{'company':job['company'],'groupid':job['groupid']},job['date_range'],payload['source'])
            if source_key not in command['sources']:
                command['sources'][source_key]={'data':copy.deepcopy(facts['producer_data']),'dependencies':copy.deepcopy(facts['verification_refs'])};command['computes']+=1
        return facts
    except (ValueError,KeyError,TypeError,OSError)as error:raise FlowError('dom-fresh-capture-unverified',str(error))from error

from contextvars import ContextVar
_DOM_COMMAND=ContextVar('daily_dom_command',default=None)

@contextmanager
def dom_command():
    """Bounded command-local computation facts, never a persistent boolean cache."""
    prior=_DOM_COMMAND.get()
    if prior is not None:yield prior;return
    facts={'sources':{},'computes':0,'hits':0};token=_DOM_COMMAND.set(facts)
    try:yield facts
    finally:facts['sources'].clear();facts.get('captures',{}).clear();_DOM_COMMAND.reset(token)

def dom_command_function(function):
    from functools import wraps
    @wraps(function)
    def command(*args,**kwargs):
        with dom_command():return function(*args,**kwargs)
    return command

def _dom_dependencies(producer,data,receipt_ref):
    receipt=producer.pinned(receipt_ref)
    refs=[receipt_ref,receipt['producer'],receipt['manifest'],receipt['xlsx'],*receipt['reader_code_refs'],producer.RATING_EVIDENCE,
          *data['pages'],*[data['job'][k]for k in ('original_job','original_order','original_request')]]
    return list({(r['path'],r['sha256']):dict(r)for r in refs}.values())

def _dom_dependencies_fresh(refs):
    for r in refs:
        path=Path(r['path'])
        if not path.is_absolute()or any(x.is_symlink()for x in (path,*path.parents))or not path.is_file()or path.resolve()!=path or sha256(path)!=r['sha256']:
            raise FlowError('dom-command-dependency-changed')

def dom_producer():
    import importlib.util
    import sys
    path=Path(__file__).absolute().with_name('dom_daily_acquisition.py')
    for part in (path,*path.parents):
        if part.is_symlink():raise FlowError('dom-producer-source-symlink')
    if not path.is_file() or path.resolve()!=path or sha256(path)!=DOM_PRODUCER_SHA256:
        raise FlowError('dom-producer-source-changed')
    name='_daily_verified_dom_producer_'+DOM_PRODUCER_SHA256
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__);sys.modules[name]=module
    module=sys.modules[name]
    if Path(module.__file__)!=path:raise FlowError('dom-producer-module-origin')
    return module

def _dom_source_key(payload,company,dates,source):
    return json.dumps([payload,{k:company[k]for k in ('company','groupid')},{k:dates[k]for k in ('start','end')},str(Path(source).absolute()),DOM_PRODUCER_SHA256],ensure_ascii=False,sort_keys=True)

def dom_source_data(payload,company,dates,source):
    if not isinstance(payload,dict) or payload.get('kind')!='daily-visible-dom-source-v1':
        raise FlowError('dom-source-kind')
    producer=dom_producer();facts=_DOM_COMMAND.get()
    key=_dom_source_key(payload,company,dates,source)
    try:
        if facts is not None and key in facts['sources']:
            import copy
            cached=facts['sources'][key];_dom_dependencies_fresh(cached['dependencies']);facts['hits']+=1;return copy.deepcopy(cached['data'])
        data=producer.checked_source(payload,company,dates,source)
        if facts is not None:
            import copy
            dependencies=_dom_dependencies(producer,data,payload['receipt']);_dom_dependencies_fresh(dependencies)
            facts['sources'][key]={'dependencies':dependencies,'data':copy.deepcopy(data)};facts['computes']+=1
        return data
    except (ValueError,KeyError,TypeError,OSError) as error:raise FlowError('dom-source-unverified',str(error)) from error

def _dom_hold_search_history(job,journal):
    """Reuse only an existing policy command's ExitStack, never a new owner."""
    if not journal.get('company_search_explicit_recovery'):return
    import sys
    timing=sys.modules.get('execution_timing')
    policy=getattr(timing,'_POLICY_COMMAND',None)
    active=policy.get()if policy is not None else None
    if active is None:return
    from switch_read_recovery import configured_source_module
    module=configured_source_module(job)
    # The public loader independently checks actual _WORKFLOW_SOURCE_REF.
    # Also require that the CC scope uses this exact existing policy owner.
    if module._configuration_timing()is not timing:raise FlowError('dom-search-policy-owner-drift')
    admitted=module._WORKFLOW_SOURCE_REF
    key=(id(module),admitted['path'],admitted['sha256'])
    commands=active.setdefault('dom_search_commands',{})
    if commands and key not in commands:raise FlowError('dom-search-command-generation-drift')
    if key not in commands:
        commands[key]=active['stack'].enter_context(module.search_progression_command())

def dom_original_download(data):
    """Use the existing public pure qualifier; never complete or query the ticket."""
    import importlib.util
    producer=dom_producer();job=producer.pinned(data['job']['original_job'])
    path=PROJECT/'skills/douyin-laike-operator/scripts/popup-recover-download.py'
    if path.is_symlink()or path.resolve()!=path:raise FlowError('dom-download-qualifier-source')
    spec=importlib.util.spec_from_file_location('_daily_dom_download_qualifier',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    journal_path=Path(job['workflow_path']);before=sha256(journal_path)
    journal=json.loads(journal_path.read_bytes());_dom_hold_search_history(job,journal)
    state,_=module.verified_order(job,journal['record_tab_id'])
    if before!=sha256(journal_path):raise FlowError('dom-original-workflow-raced')
    if state['identity']!=data['job']['identity']:raise FlowError('dom-original-identity-mismatch')
    return {'path':str(journal_path),'sha256':before}

def source_count_matches(receipt):
    if receipt.get('source_kind')!='daily-visible-dom-source-v1':
        if type(receipt.get('page_filtered'))is not int:return False
        if receipt.get('row_count')==receipt['page_filtered']:return True
        # A page/export count difference is a structural stop unless a
        # supervised adjudication is recorded on the receipt itself; the
        # adjudication must restate the exact receipt numbers, so a stale or
        # forged block can never match different bytes.
        a=receipt.get('count_adjudication')
        return (isinstance(a,dict)and a.get('kind')=='supervised-count-adjudication-v1'
                and a.get('page_filtered')==receipt['page_filtered']and a.get('row_count')==receipt.get('row_count'))
    counts=receipt.get('dom_counts',{})
    return (receipt.get('download_verified')is False and receipt.get('source_is_authoritative_export')is False
            and all(type(counts.get(k))is int and counts[k]>=0 for k in ('normal','folded','visible_rating_records','platform_filtered_normal_count','platform_pager_total'))
            and counts['normal']==counts['platform_filtered_normal_count']==receipt.get('page_filtered')
            and counts['normal']+counts['folded']==counts['visible_rating_records']==counts['platform_pager_total']==receipt.get('row_count'))

def validated_dom_receipt(receipt,src,company,dates,mapping_hash):
    if (receipt.get('source_kind')!='daily-visible-dom-source-v1' or not source_count_matches(receipt)
        or receipt.get('version')!=VERSION or receipt.get('flow')!='daily-comment-stats'
        or receipt.get('status') not in ('complete','zero_rows') or receipt.get('company')!=company['company']
        or receipt.get('wecom_group')!=company['wecom_group'] or receipt.get('mapping_sha256')!=mapping_hash
        or receipt.get('date_range')!={k:dates[k] for k in ('start','end')}
        or receipt.get('range_warnings',[])!=dates.get('warnings',[]) or receipt.get('src_sha256')!=sha256(src)
        or receipt.get('warnings') or receipt.get('mismatch')is not False or receipt.get('attribution_verified')is not True):
        raise FlowError('dom-processing-receipt-unverified')
    dom_capture_data(receipt.get('dom_capture'),receipt['dom_source'])
    data=dom_source_data(receipt.get('dom_source'),company,dates,src)
    if data['summary']!=receipt['dom_counts']:raise FlowError('dom-receipt-counts-changed')
    zero=receipt['status']=='zero_rows'
    if receipt.get('zero_rows')is not zero or receipt.get('quality_blocked')is not zero or (zero and receipt['row_count']!=0):
        raise FlowError('dom-receipt-status')
    artifacts=receipt.get('artifacts',[])
    if (len(artifacts)!= (0 if zero else 3) or any(not Path(a['path']).is_file() or sha256(a['path'])!=a['sha256'] for a in artifacts)):
        raise FlowError('dom-receipt-artifact-changed')
    return data
