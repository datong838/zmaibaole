#!/usr/bin/env python3
"""Standard-library-only, loopback-only HTTP/CLI bridge. Never starts Chrome."""
import argparse
import collections
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / '.local'
CONFIG = STATE / 'config.json'
SAFETY_VERSION = 'dom-only-20261021-11'
OPS = {'tabs', 'ping', 'tree', 'find', 'click', 'hover', 'filter', 'download-begin', 'download-status', 'activate', 'scroll', 'reload-records','capture-visible','capture-grant-status','download-reconcile','viewport-proof','review-viewport-proof','dom-region-proof'}

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
    allowed = {'op', 'tabId', 'locator', 'value', 'kind', 'ticket', 'filename','groupid','reloadKey','windowId','captureKey','since','source_sha256','dom_sha256','elements','scope','reviews','base','selectors','purpose'}
    if set(c) - allowed:
        raise ValueError('unsupported fields (no coordinates, scripts, URLs, debugger options or raw browser commands)')
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

class Jobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.available = threading.Condition(self.lock)
        self.jobs = {}
        self.queue = collections.deque()
        self.last_seen = None
        self.safety_version = None

    def add(self, command, timeout):
        job = {'id': str(uuid.uuid4()), 'command': command, 'deadline': time.monotonic() + timeout, 'event': threading.Event(), 'delivered': False}
        with self.lock:
            if self.jobs:
                raise ValueError('another command is pending; use a single serial caller')
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

        def reply(self, status, obj):
            data = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
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
                    if command['op'] in {'click','hover','filter','download-begin','activate','scroll','reload-records','capture-visible','capture-grant-status','viewport-proof'} and jobs.safety_version!=SAFETY_VERSION:
                        raise ValueError('reviewed-extension-version-required: explicitly load audited extension update first')
                    timeout = min(95, max(1, float(data.get('timeout', 90))))
                    job = jobs.add(command, timeout)
                    ready = job['event'].wait(timeout)
                    # No retry after timeout: the click may already have happened.
                    result = job.get('response') if ready else {'ok': False, 'error': 'bridge-timeout', 'outcome': 'unknown' if job['delivered'] else 'not-delivered', 'retry': 'Read current tree first; never automatically replay clicks.'}
                    jobs.expire(job)
                    return self.reply(200 if ready else 504, result)
                return self.reply(404, {'error': 'unknown endpoint'})
            except (ValueError, KeyError, TypeError) as e:
                return self.reply(400, {'error': str(e)})
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.jobs = jobs
    return server

def call(path, payload):
    c = read_config()
    request = Request(c['base'] + path, data=json.dumps(payload).encode(), headers={'Content-Type':'application/json', 'Authorization':'Bearer ' + c['cliToken']}, method='POST')
    try:
        # Never send loopback authorization through an environment HTTP proxy.
        with build_opener(ProxyHandler({})).open(request, timeout=100) as response:
            return json.load(response)
    except HTTPError as e:
        return json.load(e)

def _request_timing_start():
    # Optional diagnostics only. No config/token reads, API calls or retry.
    try:
        directory=os.environ.get('BRIDGE_REQUEST_PERFORMANCE_DIR')
        if directory and Path(directory).is_absolute():return Path(directory),time.perf_counter_ns()
    except Exception:pass
    return None

def _request_timing_finish(trace,command,result,exception):
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
        directory.mkdir(parents=True,exist_ok=True)
        with (directory/('bridge-request-'+uuid.uuid4().hex+'.json')).open('x',encoding='utf-8') as stream:
            json.dump(row,stream,separators=(',',':'));stream.write('\n')
    except Exception:pass  # Diagnostics must never replace a result/exception.

def request(command, timeout=90):
    trace=_request_timing_start();result=None;exception=True
    try:
        validate_command(command)
        result=call('/v1/request', {'command':command, 'timeout':timeout})
        exception=False
        return result
    finally:_request_timing_finish(trace,command,result,exception)

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
    print(json.dumps(out,ensure_ascii=False,indent=2))
    if out.get('ok') is False or 'error' in out: raise SystemExit(1)

if __name__=='__main__':
    try: main()
    except (ValueError,OSError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));raise SystemExit(1)
