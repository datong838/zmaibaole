#!/usr/bin/env python3
"""Standard-library-only, loopback-only HTTP/CLI bridge. Never starts Chrome."""
import argparse
import collections
import hmac
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import threading
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.local'
CONFIG = STATE / 'config.json'
SAFETY_VERSION = 'dom-only-20261103-12'
OPS = {'readonly-scope', 'tabs', 'ping', 'tree', 'find', 'click', 'hover', 'filter', 'download-begin', 'download-status', 'activate', 'scroll', 'reload-records','capture-visible','capture-grant-status','download-reconcile','viewport-proof','review-viewport-proof','dom-region-proof'}

def read_config():
    if not CONFIG.exists():
        raise ValueError('Run init first')
    config = json.loads(CONFIG.read_text())
    if config.get('base') != 'http://127.0.0.1:17341':
        raise ValueError('bridge base must be the fixed loopback address')
    return config

def private_write(path, text):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(text)
    os.chmod(path, 0o600)

def initialize():
    STATE.mkdir(mode=0o700, exist_ok=True)
    if CONFIG.exists():
        raise ValueError('Already initialized; preserve keys. Copy package to a new folder to create a separate instance.')
    c = {'base': 'http://127.0.0.1:17341', 'cliToken': secrets.token_urlsafe(32), 'bridgeToken': secrets.token_urlsafe(32), 'extensionId': None}
    private_write(CONFIG, json.dumps(c, indent=2))
    private_write(ROOT / 'extension' / 'config.js', 'globalThis.LOCAL_BRIDGE_CONFIG = Object.freeze(' + json.dumps({'base': c['base'], 'bridgeToken': c['bridgeToken']}) + ');\n')
    return {'initialized': True, 'extensionDirectory': str(ROOT / 'extension'), 'config': str(CONFIG), 'note': 'Keys created, not displayed. Load unpacked extension, then bind its ID.'}

def validate_command(c):
    if not isinstance(c, dict) or c.get('op') not in OPS:
        raise ValueError('unsupported operation')
    allowed = {'op', 'tabId', 'locator', 'value', 'kind', 'ticket', 'filename','groupid','reloadKey','windowId','captureKey','since','source_sha256','dom_sha256','elements','scope','reviews','base','selectors','purpose','companyRequest','retentionRequest'}
    if set(c) - allowed:
        raise ValueError('unsupported fields (no coordinates, scripts, URLs, debugger options or raw browser commands)')
    if 'retentionRequest' in c:
        r=c['retentionRequest']
        if (type(r) is not dict or set(r)!={'path','sha256'} or c.get('op')!='click'
            or c.get('kind') not in ('backed-up-export-delete','backed-up-export-confirm') or set(c)!={'op','tabId','locator','kind','retentionRequest'}):
            raise ValueError('retention operation reference required')
    elif c.get('kind') in ('backed-up-export-delete','backed-up-export-confirm'):
        raise ValueError('retention operation reference required')
    if 'companyRequest'in c:
        r=c['companyRequest']
        if type(r)is not dict or set(r)!={'path','sha256'} or c['op']not in ('click','filter'):
            raise ValueError('company operation reference required')
    if c['op']=='readonly-scope':
        if set(c)!={'op','tabId','windowId'} or any(type(c.get(k)) is not int or not 0<=c[k]<=9007199254740991 for k in ('tabId','windowId')):
            raise ValueError('readonly-scope requires only explicit safe integer tabId/windowId')
        return c
    if c['op'] in {'ping', 'tree', 'find', 'click', 'hover', 'filter', 'download-begin', 'activate', 'scroll', 'reload-records','capture-visible','capture-grant-status','viewport-proof'}:
        if type(c.get('tabId')) is not int or c['tabId'] < 0:
            raise ValueError('integer tabId required')
    if c['op'] in {'find', 'click', 'hover', 'filter', 'scroll'} or 'locator' in c:
        q = c.get('locator')
        if not isinstance(q, dict) or set(q) - {'by', 'value', 'name'} or q.get('by') not in {'text', 'role', 'selector'} or not isinstance(q.get('value'), str) or not q['value'].strip():
            raise ValueError('locator: {by: text|role|selector, value: string, name?: string}')
    if c['op'] == 'download-status' and not isinstance(c.get('ticket'), str):
        raise ValueError('download ticket required')
    if c['op']=='reload-records':
        import re
        if set(c)!={'op','tabId','groupid','reloadKey'} or not isinstance(c.get('groupid'),str) or not re.fullmatch(r'[0-9]{1,32}',c['groupid']):
            raise ValueError('reload-records requires only explicit tabId, numeric groupid, reloadKey')
        if not isinstance(c.get('reloadKey'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',c['reloadKey']):
            raise ValueError('stable reloadKey required; unknown outcomes must reuse key, never reload again')
    elif c['op']=='download-reconcile':
        import re
        from datetime import datetime
        if set(c)!={'op','tabId','groupid','ticket','since','filename'} or type(c.get('tabId')) is not int or c['tabId']<0 or not isinstance(c.get('groupid'),str) or not re.fullmatch(r'[0-9]{1,32}',c['groupid']):
            raise ValueError('download reconcile requires original explicit scope')
        if not isinstance(c.get('ticket'),str) or not re.fullmatch(r'[-A-Za-z0-9]{16,128}',c['ticket']) or not isinstance(c.get('filename'),str) or not re.fullmatch(r'门店评价_全部门店_[0-9]{4}_[0-9]{2}_[0-9]{2}-[0-9]{4}_[0-9]{2}_[0-9]{2}\.xlsx',c['filename']):
            raise ValueError('original download ticket and exact export filename required')
        if not isinstance(c.get('since'),str):raise ValueError('original download timestamp required')
        datetime.fromisoformat(c['since'].replace('Z','+00:00'))
    elif c['op']=='dom-region-proof':
        if set(c)!={'op','tabId','windowId','groupid','base','selectors','purpose'} or c.get('purpose')!='evidence-crop-only' or not isinstance(c.get('base'),dict) or c['base'].get('op') not in ('review-viewport-proof','viewport-proof'):raise ValueError('explicit evidence crop command required')
        validate_command(c['base'])
        if not all(c.get(k)==c['base'].get(k) for k in ('tabId','windowId','groupid')) or not isinstance(c.get('selectors'),list) or not 0<len(c['selectors'])<=100 or not all(isinstance(s,str) and 0<len(s)<=2000 for s in c['selectors']) or len(set(c['selectors']))!=len(c['selectors']):raise ValueError('evidence crop scope/selectors invalid')
    elif c['op']=='review-viewport-proof':
        import re
        if set(c)!={'op','tabId','windowId','groupid','source_sha256','dom_sha256','scope','reviews'} or type(c.get('tabId')) is not int or c['tabId']<0 or type(c.get('windowId')) is not int or c['windowId']<0 or not re.fullmatch(r'[0-9]{1,32}',str(c.get('groupid',''))) or not all(re.fullmatch(r'[a-f0-9]{64}',str(c.get(k,''))) for k in ('source_sha256','dom_sha256')):raise ValueError('review proof explicit scope required')
        q=c.get('scope');exclusive=isinstance(q,dict) and q.get('scope_mode')=='verified-complete-normal-list';fields={'list','date','negative','count','other_filters','date_text','active_class','normal_count'}|({'scope_mode','complete_list'} if exclusive else {'boundary'})
        if not isinstance(q,dict) or set(q)!=fields or type(q.get('normal_count')) is not int or q['normal_count']<=0 or not re.fullmatch(r'\d{4}-\d\d-\d\d ~ \d{4}-\d\d-\d\d',str(q.get('date_text',''))) or not q.get('active_class'):raise ValueError('review proof query invalid')
        if not isinstance(q['other_filters'],dict) or set(q['other_filters'])!={'评价类型','评价来源','评价状态'}:raise ValueError('review proof other filters invalid')
        if exclusive:
            if not isinstance(q.get('complete_list'),dict) or set(q['complete_list'])!={'pager','total','current','previous','next'} or q['normal_count']>10:raise ValueError('review complete-list scope invalid')
            section=list(q['complete_list'].values())
        else:section=[q['boundary']]
        selectors=[q[k] for k in ('list','date','negative','count')]+section+list(q['other_filters'].values());seen=set()
        if not isinstance(c['reviews'],list) or not 0<len(c['reviews'])<=30:raise ValueError('review proof reviews invalid')
        for r in c['reviews']:
            if not isinstance(r,dict) or set(r)-({'body_text_schema'} if r.get('body_text_schema')=='public-visible-text-v2' else set())!={'review_key','card','store','customer','body','heart','store_text','customer_text','body_text'} or not re.fullmatch(re.escape(str(c['groupid']))+r':verified-tuple-sha256:[a-f0-9]{64}',str(r.get('review_key',''))) or r['review_key'] in seen:raise ValueError('review proof external key invalid')
            seen.add(r['review_key']);selectors.extend(r[k] for k in ('card','store','customer','body','heart'))
            if not all(isinstance(r[k],str) and len(r[k])<(16001 if k=='body_text' and r.get('body_text_schema')=='public-visible-text-v2' else 800) and (k=='body_text' or bool(r[k])) for k in ('store_text','customer_text','body_text')):raise ValueError('review proof text invalid')
        if not all(isinstance(s,str) and 0<len(s)<=2000 for s in selectors):raise ValueError('review proof selectors invalid')
    elif c['op']=='viewport-proof':
        import re
        if set(c)!={'op','tabId','windowId','groupid','source_sha256','dom_sha256','elements'} or type(c.get('windowId')) is not int or c['windowId']<0 or not isinstance(c.get('groupid'),str) or not re.fullmatch(r'[0-9]{1,32}',c['groupid']) or not re.fullmatch(r'[a-f0-9]{64}',str(c.get('source_sha256',''))) or not re.fullmatch(r'[a-f0-9]{64}',str(c.get('dom_sha256',''))):raise ValueError('viewport proof scope invalid')
        es=c['elements']
        if not isinstance(es,list) or not 0<len(es)<=100:raise ValueError('viewport proof elements required')
        seen=set()
        for e in es:
            if not isinstance(e,dict) or set(e)!={'key','kind','locator','expected_text','notice_id'} or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}',str(e.get('key',''))) or e['key'] in seen:raise ValueError('viewport proof key invalid')
            seen.add(e['key']);q=e['locator']
            if e['kind'] not in ('date-filter','header','row') or not isinstance(e['expected_text'],str) or not 0<len(e['expected_text'])<800:raise ValueError('viewport proof text invalid')
            if (e['kind']=='row' and (not isinstance(e['notice_id'],str) or not e['notice_id'] or e['notice_id'] not in e['expected_text'])) or (e['kind']!='row' and e['notice_id'] is not None):raise ValueError('viewport proof ID invalid')
            if not isinstance(q,dict) or set(q)-{'by','value','name'} or q.get('by') not in ('selector','text','role') or not isinstance(q.get('value'),str) or not q['value'].strip():raise ValueError('viewport proof locator invalid')
        if {e['kind'] for e in es}!={'date-filter','header','row'}:raise ValueError('viewport proof required kinds missing')
    elif c['op'] in ('capture-visible','capture-grant-status'):
        import re
        fields={'op','tabId','windowId','groupid'}|({'captureKey'} if c['op']=='capture-visible' else set())
        if set(c)!=fields or type(c.get('windowId')) is not int or c['windowId']<0 or not isinstance(c.get('groupid'),str) or not re.fullmatch(r'[0-9]{1,32}',c['groupid']):
            raise ValueError('capture requires explicit existing tabId/windowId/numeric groupid only')
        if c['op']=='capture-visible' and (not isinstance(c.get('captureKey'),str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}',c['captureKey'])):
            raise ValueError('capture stable captureKey required')
    elif c['op']=='hover' and c.get('kind')=='account-hover-exit':
        import re
        if set(c)!={'op','tabId','kind','groupid','locator','value'} or not isinstance(c.get('groupid'),str) or not re.fullmatch(r'[0-9]{1,32}',c['groupid']) or set(c['locator'])!={'by','value'} or c['locator']['by']!='selector':
            raise ValueError('account hover exit requires exact observed selector and group scope')
        identity=c['value']
        if not isinstance(identity,dict) or set(identity)!={'provider','account_id','manager'} or not re.fullmatch(r'服务商[0-9]+',str(identity.get('provider',''))) or not re.fullmatch(r'[0-9]{8,}',str(identity.get('account_id',''))) or not isinstance(identity.get('manager'),str) or not 0<len(identity['manager'])<100:
            raise ValueError('account hover exit identity required')
    elif set(c)&{'base','selectors','purpose','groupid','reloadKey','windowId','captureKey','since','source_sha256','dom_sha256','elements','scope','reviews'}:
        raise ValueError('record reload scope fields only allowed for reload-records')
    return c

_DIAGNOSTIC_PREFIX = 'X-Local-Bridge-'
_DIAGNOSTIC_DURATIONS = {
    'queue_ns': 'Queue-Ns',
    'delivery_result_ns': 'Delivery-Result-Ns',
    'result_encode_ns': 'Result-Encode-Ns',
    'enqueue_encode_ns': 'Enqueue-Encode-Ns',
}

_DIAGNOSTIC_PREQUEUE_DURATIONS = {
    'module_load_ns': 'Module-Load-Ns',
    'combined_admission_including_claim_ns': 'Admission-Including-Claim-Ns',
    'preenqueue_ns': 'Preenqueue-Ns',
    'jobs_add_ns': 'Jobs-Add-Ns',
}
def _duration(diagnostic,key,started):
    # Passive diagnostics cannot replace admission success/error or a claim.
    try:
        if type(diagnostic)is dict:diagnostic[key]=time.perf_counter_ns()-started
    except Exception:pass

def verified_backup(history_ref, backup_path, groupid, record_text):
    history = Path(history_ref['path'])
    backup = Path(backup_path)
    for p in (history, backup):
        if not p.is_absolute() or p.resolve() != p or not p.is_file() or any(x.is_symlink() for x in (p,*p.parents)):
            raise ValueError('retention-file-path-invalid')
    raw = history.read_bytes()
    if hashlib.sha256(raw).hexdigest() != history_ref['sha256']:
        raise ValueError('retention-history-changed')
    original = json.loads(raw); result = original.get('result',{}); record = original.get('generated_record',{})
    if (str(original.get('groupid')) != str(groupid) or str(result.get('groupid')) != str(groupid)
        or result.get('company') != original.get('company') or result.get('download_verified') is not True
        or result.get('source_is_authoritative_export') is not True or result.get('download_receipt',{}).get('state') != 'complete'
        or record.get('state') != 'success' or record.get('text') != record_text
        or record.get('generated_at') != result.get('record_generated_at')):
        raise ValueError('retention-original-download-mismatch')
    data = backup.read_bytes(); digest = hashlib.sha256(data).hexdigest()
    if digest != result.get('src_sha256') or len(data) != result['download_receipt'].get('bytesReceived'):
        raise ValueError('retention-backup-mismatch')
    return {'groupid':str(groupid),'recordText':record_text,'generated_at':record['generated_at'],
            'export_name':record_text.split(' ',1)[0], 'backup_sha256':digest,'backup_bytes':len(data)}

def claim_once(directory, groupid, export_name, generated_at, request_ref):
    if (not isinstance(groupid, str) or not groupid.isascii() or not groupid.isdigit()
            or not isinstance(export_name, str) or not export_name.startswith('门店评价_全部门店_')
            or not isinstance(generated_at, str) or len(generated_at) != 19
            or not isinstance(request_ref, dict) or set(request_ref) != {'path', 'sha256'}
            or not isinstance(request_ref['path'], str) or not Path(request_ref['path']).is_absolute()
            or not isinstance(request_ref['sha256'], str) or len(request_ref['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in request_ref['sha256'])):
        raise ValueError('retention-claim-invalid')
    directory = Path(directory)
    if not directory.is_absolute() or directory.resolve() != directory or not directory.is_dir() or any(p.is_symlink() for p in (directory, *directory.parents)):
        raise ValueError('retention-claim-directory-invalid')
    identity = json.dumps([groupid, export_name, generated_at], ensure_ascii=False, separators=(',', ':')).encode()
    target = directory / (hashlib.sha256(identity).hexdigest() + '.json')
    payload = json.dumps({'kind': 'backed-up-export-dispatch-claim-v1', 'groupid': groupid,
                          'export_name': export_name, 'generated_at': generated_at, 'request': request_ref}, ensure_ascii=False,
                         sort_keys=True, separators=(',', ':')).encode() + b'\n'
    try:
        fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    except FileExistsError:
        raise ValueError('retention-dispatch-already-claimed') from None
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        dirfd = os.open(str(directory), os.O_RDONLY)
        try:
            os.fsync(dirfd)
        finally:
            os.close(dirfd)
    except BaseException:
        # An incomplete claim also closes the opportunity: never unlink it.
        raise
    return target

def retention_backup_binding(command, verifier):
    """Validate the immutable request and backup; caller still needs lease and intent checks."""
    import hashlib
    reference=command.get('retentionRequest')
    if type(reference) is not dict or set(reference)!={'path','sha256'}:
        raise ValueError('retention-request-reference')
    path=Path(reference['path'])
    if not path.is_absolute() or path.resolve()!=path or not path.is_file() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('retention-request-origin')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=reference['sha256']:
        raise ValueError('retention-request-changed')
    request=json.loads(raw)
    if set(request)!={'kind','tab_id','groupid','record_text','history','backup'} or request.get('kind')!='backed-up-export-retention-request-v1' or request.get('tab_id')!=command.get('tabId'):
        raise ValueError('retention-request-scope')
    scope=verifier(request['history'],request['backup'],request['groupid'],request['record_text'])
    return scope

def retention_confirmation_binding(command, scope):
    """Require the same original confirmed delete-entry before one confirmation."""
    reference=command['retentionRequest'];folder=Path(reference['path']).parent
    identity=json.dumps([scope['groupid'],scope['export_name'],scope['generated_at']],ensure_ascii=False,separators=(',',':')).encode()
    claim=STATE/'retention-claims'/(hashlib.sha256(identity).hexdigest()+'.json')
    if claim.is_symlink() or not claim.is_file():raise ValueError('retention-original-dispatch-claim-missing')
    prior=json.loads(claim.read_bytes())
    if prior.get('request')!=reference or prior.get('groupid')!=scope['groupid'] or prior.get('export_name')!=scope['export_name'] or prior.get('generated_at')!=scope['generated_at']:
        raise ValueError('retention-original-dispatch-claim-mismatch')
    intent=json.loads((folder/'delete-intent.json').read_bytes())
    result=json.loads((folder/'delete-result.json').read_bytes())
    if (intent.get('retentionRequest')!=reference or intent.get('kind')!='backed-up-export-delete'
        or intent.get('op')!='click' or intent.get('tabId')!=command.get('tabId')
        or result.get('ok') is not True or result.get('result',{}).get('kind')!='backed-up-export-delete'
        or result.get('result',{}).get('clicked',{}).get('name')!='删除'):
        raise ValueError('retention-original-delete-entry-not-confirmed')
    return scope

def prepare_retention_command(command, verifier, claim_once, claim_directory):
    """Bind a backed-up record and consume its sole click opportunity.

    Candidate only: the handler remains closed until complete reconciliation
    and confirmation handling are reviewed.
    """
    scope=retention_backup_binding(command,verifier)
    claim_once(claim_directory,scope['groupid'],scope['export_name'],scope['generated_at'],command['retentionRequest'])
    return {**{k:v for k,v in command.items() if k!='retentionRequest'},
            'value':{'groupid':scope['groupid'],'recordText':scope['recordText']}}

def configured_company_command(command, *, _diagnostic=None):
    if 'companyRequest'not in command:return command
    started=time.perf_counter_ns()
    # Fixed local approved configuration; never accept a caller capability.
    # Pure import/read only. CompanyConfig never creates/extends an authority.
    path=ROOT.parents[1]/'skills/workshop-director/scripts/company_configuration.py'
    if path!=path.resolve() or not path.is_file() or any(p.is_symlink()for p in(path,*path.parents)):
        raise ValueError('configured company module canonical required')
    # Execute the current fixed local validator; archived source generations
    # and successor-release files are not runtime inputs.
    source=path.read_bytes()
    # Server processes have no worker bootstrap. Admit only these fixed local
    # read-only validation dependencies; never copy caller sys.path/env values.
    project=ROOT.parents[1]
    dependencies=[project/'skills'/name/'scripts'for name in ('workshop-director','douyin-laike-operator','chrome-dom-export')]
    for directory in dependencies:
        if not directory.is_dir()or directory.resolve()!=directory or any(p.is_symlink()for p in(directory,*directory.parents)):raise ValueError('configured company dependency canonical required')
    prefix=[str(p)for p in dependencies];sys.path[:]=prefix+[p for p in sys.path if p not in prefix]
    import types
    module=types.ModuleType('bridge_fixed_company_configuration');module.__file__=str(path)
    exec(compile(source,str(path),'exec'),module.__dict__)
    _duration(_diagnostic,'module_load_ns',started)
    started=time.perf_counter_ns()
    try:
        # One request owns one immutable-history fact scope, including claim
        # preflight. The next request loads/checks its own module and facts.
        with module.configuration_command(),module.search_progression_command():
            return module.admit_command(command,_claim_search_only=True)
    finally:_duration(_diagnostic,'combined_admission_including_claim_ns',started)

def diagnostic_headers(job, ready, encoded_ns):
    """Transport metadata only; never infer business success from delivery."""
    try:
        ident=job['id'];start=job['enqueued_ns'];delivered=job.get('delivered_ns')
        finished=job.get('finished_ns') if ready else None
        if str(uuid.UUID(ident))!=ident or type(ready) is not bool: return {}
        if type(start) is not int or type(encoded_ns) is not int or encoded_ns<start: return {}
        if delivered is not None and (type(delivered) is not int or not start<=delivered<=encoded_ns): return {}
        if ready and (delivered is None or type(finished) is not int or not delivered<=finished<=encoded_ns): return {}
        if bool(job['delivered']) != (delivered is not None): return {}
    except (KeyError,TypeError,ValueError,AttributeError):
        return {}
    state = 'returned' if ready else 'unknown' if job['delivered'] else 'not-delivered'
    values = {'enqueue_encode_ns': encoded_ns - start}
    if delivered is not None:
        values['queue_ns'] = delivered - start
    if finished is not None:
        values['delivery_result_ns'] = finished - delivered
        values['result_encode_ns'] = encoded_ns - finished
    headers = {_DIAGNOSTIC_PREFIX+'Version': '1', _DIAGNOSTIC_PREFIX+'Job': job['id'],
               _DIAGNOSTIC_PREFIX+'State': state}
    headers.update({_DIAGNOSTIC_PREFIX+_DIAGNOSTIC_DURATIONS[k]: str(v) for k,v in values.items()})
    prequeue=job.get('prequeue')
    if (type(prequeue)is dict and set(prequeue)==set(_DIAGNOSTIC_PREQUEUE_DURATIONS)
        and all(type(v)is int and 0<=v<=86400000000000 for v in prequeue.values())
        and prequeue['module_load_ns']+prequeue['combined_admission_including_claim_ns']<=prequeue['preenqueue_ns']):
        headers.update({_DIAGNOSTIC_PREFIX+name:str(prequeue[key])for key,name in _DIAGNOSTIC_PREQUEUE_DURATIONS.items()})
    return headers

def read_diagnostic_headers(headers):
    """Invalid diagnostics are omitted and cannot replace the original reply."""
    try:
        if hasattr(headers,'get_all') and any(len(headers.get_all(_DIAGNOSTIC_PREFIX+n,[]))>1 for n in ('Version','Job','State',*_DIAGNOSTIC_DURATIONS.values(),*_DIAGNOSTIC_PREQUEUE_DURATIONS.values())): return None
        if headers.get(_DIAGNOSTIC_PREFIX+'Version') != '1': return None
        ident = headers.get(_DIAGNOSTIC_PREFIX+'Job')
        if str(uuid.UUID(ident)) != ident: return None
        state = headers.get(_DIAGNOSTIC_PREFIX+'State')
        if state not in ('returned','unknown','not-delivered'): return None
        out = {'version':1,'job_id':ident,'state':state}
        for key,name in _DIAGNOSTIC_DURATIONS.items():
            value = headers.get(_DIAGNOSTIC_PREFIX+name)
            if value is None: continue
            if not isinstance(value,str) or not 1 <= len(value) <= 20 or any(c<'0' or c>'9' for c in value): return None
            number = int(value)
            if number > 86400000000000: return None
            out[key] = number
        if 'enqueue_encode_ns' not in out: return None
        total = out['enqueue_encode_ns']
        if any(out[k]>total for k in _DIAGNOSTIC_DURATIONS if k in out): return None
        if state == 'returned':
            if any(k not in out for k in ('queue_ns','delivery_result_ns','result_encode_ns')): return None
            if sum(out[k] for k in ('queue_ns','delivery_result_ns','result_encode_ns')) != total: return None
        elif any(k in out for k in ('delivery_result_ns','result_encode_ns')): return None
        if state == 'unknown' and 'queue_ns' not in out: return None
        if state == 'not-delivered' and 'queue_ns' in out: return None
        prequeue={key:headers.get(_DIAGNOSTIC_PREFIX+name)for key,name in _DIAGNOSTIC_PREQUEUE_DURATIONS.items()}
        if any(value is not None for value in prequeue.values()):
            if not all(type(value)is str and 1<=len(value)<=20 and value.isascii()and value.isdecimal() for value in prequeue.values()):return None
            prequeue={key:int(value)for key,value in prequeue.items()}
            if any(value>86400000000000 for value in prequeue.values())or prequeue['module_load_ns']+prequeue['combined_admission_including_claim_ns']>prequeue['preenqueue_ns']:return None
            out.update(prequeue)
        return out
    except (TypeError,ValueError,AttributeError):
        return None

def readonly_worker_timing(result):
    """Finite four-op metrics only, with no DOM/command/identity fields."""
    if type(result) is not dict or result.get('ok') is not True or type(result.get('result')) is not dict: return None
    value = result['result'].get('timing')
    if type(value) is not dict or set(value)!={'clock','steps','elapsed_ms'} or value['clock']!='worker-performance-now': return None
    steps=value['steps']
    if type(steps) is not list or len(steps)!=4: return None
    finite=lambda n:type(n) in (int,float) and 0<=n<=86400000 and math.isfinite(n)
    if not finite(value['elapsed_ms']): return None
    out=[]
    for step,op in zip(steps,('tabs','ping','tree','tabs')):
        if type(step) is not dict or set(step)!={'op','elapsed_ms'} or step['op']!=op or not finite(step['elapsed_ms']): return None
        out.append({'op':op,'elapsed_ms':step['elapsed_ms']})
    if sum(step['elapsed_ms'] for step in out)>value['elapsed_ms']: return None
    return {'clock':'worker-performance-now','steps':out,'elapsed_ms':value['elapsed_ms']}

class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.available = threading.Condition(self.lock)
        self.jobs = {}
        self.queue = collections.deque()
        self.last_seen = None
        self.safety_version = None

    def add(self, command, timeout, before_add=None):
        job = {'id': str(uuid.uuid4()), 'command': command, 'deadline': time.monotonic() + timeout, 'event': threading.Event(), 'delivered': False}
        with self.lock:
            if self.jobs:
                raise ValueError('another command is pending; use a single serial caller')
            if before_add is not None: before_add()
            job['enqueued_ns'] = time.perf_counter_ns()
            self.jobs[job['id']] = job
            self.queue.append(job['id'])
            self.available.notify_all()
        return job

    def poll(self, wait_seconds=0):
        deadline = time.monotonic() + min(3, max(0, wait_seconds))
        with self.available:
            self.last_seen = time.time()
            while True:
                while self.queue:
                    job = self.jobs.get(self.queue.popleft())
                    if job and job['deadline'] > time.monotonic():
                        job['delivered'] = True
                        job['delivered_ns'] = time.perf_counter_ns()
                        return {'id': job['id'], 'command': job['command']}
                # Never delay an empty duplicate poll while a delivered command
                # is awaiting its result; that could consume its remaining TTL.
                if any(j['delivered'] and not j['event'].is_set() for j in self.jobs.values()):
                    return None
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                self.available.wait(remaining)

    def finish(self, ident, result):
        with self.lock:
            job = self.jobs.get(ident)
            if not job or not job['delivered'] or job['event'].is_set():
                return False
            job['response'] = result
            job['finished_ns'] = time.perf_counter_ns()
            job['event'].set()
            return True

    def expire(self, job):
        with self.lock:
            self.jobs.pop(job['id'], None)

def make_server(config, port=17341):
    jobs = Jobs()
    class Handler(BaseHTTPRequestHandler):
        # No request-body, auth-token or page-content logging.
        def log_message(self, *_):
            pass

        def reply(self, status, obj, diagnostic=None):
            data = json.dumps(obj, ensure_ascii=True).encode()
            metadata = diagnostic_headers(diagnostic[0],diagnostic[1],time.perf_counter_ns()) if diagnostic else {}
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            for name,value in metadata.items():
                self.send_header(name,value)
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            self.reply(405, {'error': 'POST only; authentication required'})

        def do_OPTIONS(self):
            self.reply(403, {'error': 'web-origin CORS not enabled'})

        def do_POST(self):
            expected_host = '127.0.0.1:' + str(self.server.server_port)
            if self.headers.get('Host') != expected_host:
                return self.reply(403, {'error': 'invalid Host'})
            bridge = self.path.startswith('/bridge/')
            key = config['bridgeToken'] if bridge else config['cliToken']
            if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + key):
                return self.reply(401, {'error': 'unauthorized'})
            origin = self.headers.get('Origin')
            expected_origin = 'chrome-extension://' + str(config.get('extensionId'))
            if bridge and (not config.get('extensionId') or origin != expected_origin):
                return self.reply(403, {'error': 'extension not bound or wrong Origin'})
            if not bridge and origin:
                return self.reply(403, {'error': 'CLI endpoint rejects browser origins'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if length < 1 or length > 8_000_000:
                    raise ValueError('invalid body length')
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError('JSON object required')
                if self.path == '/v1/status':
                    return self.reply(200, {'ok': True, 'extensionBound': bool(config.get('extensionId')), 'lastExtensionContact': jobs.last_seen,'reviewedExtensionReady': jobs.safety_version==SAFETY_VERSION})
                if self.path == '/bridge/poll':
                    if data.get('extensionId') != config['extensionId']:
                        raise ValueError('extension ID mismatch')
                    jobs.safety_version=data.get('safety_version')
                    return self.reply(200, {'job': jobs.poll(wait_seconds=3)})
                if self.path == '/bridge/result':
                    ok = jobs.finish(data['id'], {'ok': data.get('ok') is True, 'result': data.get('result'), 'error': data.get('error')})
                    return self.reply(200 if ok else 409, {'accepted': ok})
                if self.path == '/v1/request':
                    command = validate_command(data['command'])
                    prequeue={key:0 for key in _DIAGNOSTIC_PREQUEUE_DURATIONS}
                    preenqueue_started=time.perf_counter_ns()
                    try:
                        command = configured_company_command(command,_diagnostic=prequeue)
                    except Exception as error:
                        # This boundary precedes Jobs.add, delivery and any DOM
                        # input. Do not expose paths, body, identity or secrets.
                        if type(error).__name__=='SearchOpportunityConsumed':return self.reply(409,{'ok':False,'error':'company-search-opportunity-consumed','stage':'pre-enqueue','outcome':'unknown','job_created':False,'execution_started':False,'retry':'Observe original operation; never enqueue again.'})
                        known=isinstance(error,(ValueError,KeyError,TypeError))
                        error_type=type(error).__name__ if type(error).__name__ in {'ValueError','KeyError','TypeError','ModuleNotFoundError','ImportError','AttributeError','OSError','FileNotFoundError','PermissionError','TimingError'} else 'AdmissionError'
                        return self.reply(400 if known else 503,{'ok':False,'error':'configured-company-admission-rejected'if known else'configured-company-admission-unavailable','error_type':error_type,'stage':'pre-enqueue','outcome':'not-delivered','job_created':False,'execution_started':False,'retry':'Never replay an existing UNKNOWN intent; reconcile its original evidence.'})
                    if command['op'] in {'click','hover','filter','download-begin','activate','scroll','reload-records','capture-visible','capture-grant-status','viewport-proof'} and jobs.safety_version!=SAFETY_VERSION:
                        raise ValueError('reviewed-extension-version-required: explicitly load audited extension update first')
                    retention_claim = None
                    if command.get('retentionRequest'):
                        scope = retention_backup_binding(command, verified_backup)
                        reference = command['retentionRequest']
                        if command['kind']=='backed-up-export-confirm':
                            retention_confirmation_binding(command,scope)
                        claim_directory = STATE / ('retention-confirm-claims' if command['kind']=='backed-up-export-confirm' else 'retention-claims')
                        retention_claim = lambda: claim_once(claim_directory, scope['groupid'], scope['export_name'], scope['generated_at'], reference)
                        command = {**{k:v for k,v in command.items() if k!='retentionRequest'},
                                   'value':{'groupid':scope['groupid'],'recordText':scope['recordText']}}
                    timeout = min(95, max(1, float(data.get('timeout', 90))))
                    _duration(prequeue,'preenqueue_ns',preenqueue_started)
                    jobs_add_started=time.perf_counter_ns()
                    job = jobs.add(command, timeout, before_add=retention_claim)
                    _duration(prequeue,'jobs_add_ns',jobs_add_started)
                    job['prequeue']=prequeue
                    ready = job['event'].wait(timeout)
                    # No retry after timeout: the click may already have happened.
                    with jobs.lock:
                        result = job.get('response') if ready else {'ok': False, 'error': 'bridge-timeout', 'outcome': 'unknown' if job['delivered'] else 'not-delivered', 'retry': 'Read current tree first; never automatically replay clicks.'}
                        diagnostic_job={k:job[k]for k in ('id','enqueued_ns','delivered','delivered_ns','finished_ns','prequeue')if k in job}
                    jobs.expire(job)
                    return self.reply(200 if ready else 504, result, (diagnostic_job,ready))
                return self.reply(404, {'error': 'unknown endpoint'})
            except (ValueError, KeyError, TypeError) as e:
                return self.reply(400, {'error': str(e)})
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.jobs = jobs
    return server

def call(path, payload, *, _timing_collector=None):
    c = read_config()
    request = Request(c['base'] + path, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json', 'Authorization':'Bearer ' + c['cliToken']}, method='POST')
    try:
        # Never send loopback authorization through an environment HTTP proxy.
        with build_opener(ProxyHandler({})).open(request, timeout=100) as response:
            metadata=read_diagnostic_headers(response.headers) if _timing_collector is not None else None
            if metadata is not None and type(_timing_collector) is dict: _timing_collector.update(metadata)
            return json.load(response)
    except HTTPError as e:
        metadata=read_diagnostic_headers(e.headers) if _timing_collector is not None else None
        if metadata is not None and type(_timing_collector) is dict: _timing_collector.update(metadata)
        return json.load(e)

def _request_timing_start():
    # Optional diagnostics only. No config/token reads, API calls or retry.
    try:
        directory=os.environ.get('BRIDGE_REQUEST_PERFORMANCE_DIR')
        if directory and Path(directory).is_absolute():return Path(directory),time.perf_counter_ns()
    except Exception:pass
    return None

def _request_timing_finish(trace,command,result,exception,diagnostic=None):
    if trace is None:return
    try:
        directory,started=trace
        elapsed=time.perf_counter_ns()-started
        op=command.get('op') if isinstance(command,dict) else None
        op=op if type(op) is str and op in OPS else 'unknown'
        ok=result.get('ok') if type(result) is dict else None
        ok=ok if type(ok) is bool else None
        outcome='exception' if exception else 'success' if ok is True else 'failed' if ok is False else 'returned'
        if not exception and type(result) is dict and type(result.get('outcome')) is str and result['outcome'] in ('unknown','not-delivered'):outcome=result['outcome']
        row={'schema':'bridge-request-timing-v1','op':op,'elapsed_monotonic_ns':elapsed,'ok':ok,'outcome':outcome,'exception':exception}
        if diagnostic:
            row['service']=diagnostic
            if op=='readonly-scope' and diagnostic.get('state')=='returned':
                worker=readonly_worker_timing(result)
                if worker is not None: row['worker']=worker
        directory.mkdir(parents=True,exist_ok=True)
        with (directory/('bridge-request-'+uuid.uuid4().hex+'.json')).open('x',encoding='utf-8') as stream:
            json.dump(row,stream,separators=(',',':'));stream.write('\n')
    except Exception:pass  # Diagnostics must never replace a result/exception.

def request(command, timeout=90):
    trace=_request_timing_start();result=None;exception=True;diagnostic={} if trace is not None else None
    try:
        validate_command(command)
        payload={'command':command,'timeout':timeout}
        result=call('/v1/request',payload) if diagnostic is None else call('/v1/request',payload,_timing_collector=diagnostic)
        exception=False
        return result
    finally:_request_timing_finish(trace,command,result,exception,diagnostic)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest='verb', required=True)
    s.add_parser('init'); s.add_parser('serve'); s.add_parser('status'); s.add_parser('tabs')
    b=s.add_parser('bind'); b.add_argument('extension_id')
    r=s.add_parser('request'); r.add_argument('json'); r.add_argument('--timeout', type=float, default=90)
    c=s.add_parser('capture-visible');c.add_argument('--tab-id',type=int,required=True);c.add_argument('--window-id',type=int,required=True);c.add_argument('--groupid',required=True);c.add_argument('--key',required=True);c.add_argument('--out',type=Path,required=True)
    w=s.add_parser('wait-download'); w.add_argument('ticket'); w.add_argument('--filename'); w.add_argument('--timeout', type=float, default=180)
    a=p.parse_args()
    if a.verb=='init': out=initialize()
    elif a.verb=='bind':
        if len(a.extension_id)!=32 or any(x not in 'abcdefghijklmnop' for x in a.extension_id): raise ValueError('invalid Chrome extension ID')
        c=read_config(); c['extensionId']=a.extension_id; private_write(CONFIG,json.dumps(c,indent=2));out={'bound':a.extension_id,'next':'Restart this bridge server, not Chrome.'}
    elif a.verb=='serve':
        server=make_server(read_config()); print('Listening only on http://127.0.0.1:17341; never starts or debugs Chrome.',flush=True)
        try: server.serve_forever()
        except KeyboardInterrupt: pass
        finally: server.server_close()
        return
    elif a.verb=='status': out=call('/v1/status',{})
    elif a.verb=='tabs': out=request({'op':'tabs'})
    elif a.verb=='request':
        command=json.loads(a.json)
        if command.get('op')=='capture-visible':raise ValueError('use capture-visible subcommand with --out; never print image base64')
        out=request(command,a.timeout)
    elif a.verb=='capture-visible':
        from visible_capture import write_capture
        command={'op':'capture-visible','tabId':a.tab_id,'windowId':a.window_id,'groupid':a.groupid,'captureKey':a.key}
        validate_command(command);out=write_capture(command,a.out,request)
    else:
        deadline=time.monotonic()+a.timeout
        while True:
            command={'op':'download-status','ticket':a.ticket}
            if a.filename: command['filename']=a.filename
            out=request(command, min(90,max(1,deadline-time.monotonic())))
            if not out.get('ok'): break
            result=out['result']
            if result.get('state')=='complete':
                f=Path(result['path'])
                if not f.is_absolute() or not f.is_file() or f.name.endswith('.crdownload'):
                    out={'ok':False,'error':'Chrome complete but local file missing; do not report successful delivery','result':result}
                else: result['localFileVerified']=True;result['localSize']=f.stat().st_size
                break
            if time.monotonic()>=deadline:
                out={'ok':False,'error':'download-wait-timeout','result':result};break
            time.sleep(1)
    print(json.dumps(out,ensure_ascii=True,indent=2))
    if out.get('ok') is False or out.get('outcome') in ('unknown','not-delivered') or ('error' in out and not (out.get('ok') is True and out['error'] is None)): raise SystemExit(1)

if __name__=='__main__':
    try: main()
    except (ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=True));raise SystemExit(1)
