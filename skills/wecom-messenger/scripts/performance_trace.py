"""Optional aggregate timing only: no UI reads, input, payload or receipt edits.

WECOM_PERFORMANCE_DIR enables independent per-advance JSON. Durations use
perf_counter_ns (monotonic elapsed wall time); UTC wall time is correlation only.
Nested operation totals are inclusive and must not be added to phase totals.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
import hashlib,json,os,re,time,uuid
from datetime import datetime,timezone

ACTIVE=ContextVar('wecom_performance_trace',default=None)
PHASES={'locate','verify','stage','ready','file-confirm','file-dialog','verify-sent','image-verify-sent','done'}
STATUSES={'running','unknown','complete','failed','abandoned'}
ATTRIBUTES={'AXRole','AXTitle','AXDescription','AXValue','AXIdentifier','AXRoleDescription','AXSubrole','AXPlaceholderValue','AXHelp','AXEnabled','AXSelected','AXURL','AXFilename','AXChildren','AXWindows','AXFrontmost','AXFocusedUIElement'}
def safe_phase(value):return value if isinstance(value,str) and value in PHASES else 'other'
class Recorder:
    def __init__(self,state,directory):
        self.state=state;self.directory=Path(directory);self.started=time.perf_counter_ns();self.wall=datetime.now(timezone.utc).isoformat();self.stats={};self.dropped=0
        key=state.get('job',{}).get('key','');self.key_sha256=hashlib.sha256(str(key).encode()).hexdigest();value=state.get('fingerprint');self.fingerprint=value if isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) else None
        self.initial_phase=safe_phase(state.get('phase'));self.type=state.get('job',{}).get('type');self.type=self.type if self.type in ('text','file') else 'other'
    def record(self,phase,name,start,failed,result_code=None):
        try:
            elapsed=time.perf_counter_ns()-start
            if elapsed<0:raise ValueError('monotonic clock regressed')
            phase=safe_phase(phase);key=(phase,name);v=self.stats.setdefault(key,{'calls':0,'exceptions':0,'elapsed_monotonic_ns':0,'max_monotonic_ns':0})
            v['calls']+=1;v['exceptions']+=int(failed);
            if result_code is not None:
                codes=v.setdefault('return_code_counts',{});codes[str(result_code)]=codes.get(str(result_code),0)+1
            v['elapsed_monotonic_ns']+=elapsed;v['max_monotonic_ns']=max(v['max_monotonic_ns'],elapsed)
        except Exception:self.dropped+=1
    def flush(self):
        elapsed=time.perf_counter_ns()-self.started
        data={'kind':'wecom-public-call-timing-v1','clock':'perf_counter_ns: monotonic elapsed wall time; durations inclusive','scope':'advance body after existing state/policy loading; diagnostic write excluded','instrumentation_overhead_included':True,'wall_started_at_utc':self.wall,'wall_finished_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_monotonic_ns':elapsed,'job_key_sha256':self.key_sha256,'job_fingerprint':self.fingerprint,'payload_type':self.type,'initial_phase':self.initial_phase,'final_phase':safe_phase(self.state.get('phase')),'final_status':self.state.get('status') if self.state.get('status') in STATUSES else 'other','business_error_present':bool(self.state.get('error')),'instrumentation_samples_dropped':self.dropped,'operations':[{'phase':phase,'operation':name,**v} for (phase,name),v in sorted(self.stats.items())],'contains_UI_values_or_payload':False,'business_receipt_modified':False}
        self.directory.mkdir(parents=True,exist_ok=True);p=self.directory/('wecom-'+self.key_sha256[:16]+'-'+uuid.uuid4().hex+'.json')
        with p.open('x',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True);f.write('\n')

@contextmanager
def sender_scope(state):
    recorder=None;token=None
    try:
        directory=os.environ.get('WECOM_PERFORMANCE_DIR')
        if directory and Path(directory).is_absolute():recorder=Recorder(state,directory);token=ACTIVE.set(recorder)
    except Exception:recorder=None
    try:yield
    finally:
        # Diagnostic failures never replace a business return or exception.
        if token is not None:
            try:ACTIVE.reset(token)
            except Exception:pass
        if recorder is not None:
            try:recorder.flush()
            except Exception:pass

def call(name,function,*args,**kwargs):
    try:recorder=ACTIVE.get()
    except Exception:return function(*args,**kwargs)
    if recorder is None:return function(*args,**kwargs)
    try:start=time.perf_counter_ns();phase=recorder.state.get('phase')
    except Exception:return function(*args,**kwargs)
    failed=False;result_code=None
    try:
        result=function(*args,**kwargs)
        if name.startswith('ax.rpc.') and type(result) is int:result_code=result
        return result
    except BaseException:
        failed=True;raise
    finally:
        try:recorder.record(phase,name,start,failed,result_code)
        except Exception:pass

def stage(name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args,**kwargs):return call(name,function,*args,**kwargs)
        return wrapped
    return decorate

def attribute_call(key,function,*args):
    return call('ax.rpc.attribute.'+(key if isinstance(key,str) and key in ATTRIBUTES else 'other'),function,*args)


def summarize(directory):
    """Offline diagnostic aggregation; never a business receipt or full timer."""
    jobs={}
    for p in sorted(Path(directory).glob('wecom-*.json')):
        d=json.loads(p.read_bytes())
        if d.get('kind')!='wecom-public-call-timing-v1':raise ValueError('unexpected timing schema')
        key=(d['job_key_sha256'],d['job_fingerprint']);out=jobs.setdefault(key,{'job_key_sha256':key[0],'job_fingerprint':key[1],'advance_calls':0,'elapsed_monotonic_ns':0,'operations':{}})
        out['advance_calls']+=1;out['elapsed_monotonic_ns']+=d['elapsed_monotonic_ns']
        for row in d['operations']:
            k=(row['phase'],row['operation']);v=out['operations'].setdefault(k,{'phase':k[0],'operation':k[1],'calls':0,'exceptions':0,'elapsed_monotonic_ns':0,'max_monotonic_ns':0})
            for field in ('calls','exceptions','elapsed_monotonic_ns'):v[field]+=row[field]
            v['max_monotonic_ns']=max(v['max_monotonic_ns'],row['max_monotonic_ns'])
            for code,count in row.get('return_code_counts',{}).items():
                v.setdefault('return_code_counts',{})[code]=v['return_code_counts'].get(code,0)+count
    result=[]
    for job in jobs.values():job['operations']=list(job['operations'].values());result.append(job)
    return {'kind':'wecom-timing-summary-v1','scope':'sender advance calls only; excludes prepare, external gaps and full-workflow time','operation_durations_inclusive':True,'jobs':result}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--summarize',type=Path,required=True);args=parser.parse_args();print(json.dumps(summarize(args.summarize),ensure_ascii=False,indent=2))
