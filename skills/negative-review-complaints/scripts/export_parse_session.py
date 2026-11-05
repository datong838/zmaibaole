"""One explicit run owner for decoded immutable XLSX only; no DOM or live guard.
Every hit and successful owner exit rehashes bytes and actual parser code.
"""
import copy,hashlib,json,sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType,ModuleType,MappingProxyType
_OWNER=ContextVar('immutable_xlsx_run_owner',default=None)
DEFAULT_MAX_BYTES=64*1024*1024

def _size(value,seen=None):
    seen=set() if seen is None else seen
    if id(value) in seen:return 0
    seen.add(id(value));n=sys.getsizeof(value)
    if isinstance(value,dict):n+=sum(_size(k,seen)+_size(v,seen) for k,v in value.items())
    elif isinstance(value,(list,tuple,set,frozenset)):n+=sum(_size(v,seen) for v in value)
    return n

def _function(fn):
    closed=tuple((type(c.cell_contents),repr(c.cell_contents),getattr(c.cell_contents,'__code__',None)) for c in fn.__closure__ or ())
    return (fn,fn.__code__,repr(fn.__defaults__),repr(fn.__kwdefaults__),closed,id(fn.__globals__))

def _token(compute):
    module=sys.modules[compute.__module__];modules={module.__name__:module,__name__:sys.modules[__name__]}
    modules.update({k:v for k,v in tuple(sys.modules.items()) if k=='zipfile' or k in ('xml.etree.ElementTree','defusedxml.ElementTree') or k=='openpyxl' or k.startswith('openpyxl.')})
    # These tables live only for this one graph traversal. Alias edges remain
    # in the result; identical objects share only their immutable snapshots.
    functions={};classes={}
    def function(fn):
        key=id(fn)
        if key not in functions:functions[key]=_function(fn)
        return functions[key]
    def methods(cls):
        key=id(cls)
        if key not in classes:
            entries=[]
            for name,method in sorted(vars(cls).items()):
                if isinstance(method,(staticmethod,classmethod)):method=method.__func__
                if isinstance(method,FunctionType):entries.append((name,function(method)))
                elif isinstance(method,property):entries.append((name,tuple(function(f) if f else None for f in (method.fget,method.fset,method.fdel))))
            classes[key]=tuple(entries)
        return classes[key]
    result={}
    for name,m in sorted(modules.items()):
        p=Path(m.__file__);guard=(str(p),str(p.resolve()),tuple(str(v) for v in (p,*p.parents) if v.is_symlink()),hashlib.sha256(p.read_bytes()).hexdigest());entries=[]
        for k,v in sorted(vars(m).items()):
            if isinstance(v,FunctionType):entries.append((k,function(v)))
            elif isinstance(v,type):entries.append((k,v,methods(v)))
            elif isinstance(v,ModuleType):entries.append((k,('module-alias',v)))
            elif k.isupper():entries.append((k,type(v),repr(v)))
            elif callable(v):entries.append((k,('callable-alias',v,getattr(v,'__wrapped__',None))))
        result[name]=(m,guard,tuple(entries))
    return result

def _source(path,expected):
    p=Path(path)
    if not p.is_absolute() or p!=p.resolve() or any(q.is_symlink() for q in (p,*p.parents)) or not p.is_file():raise ValueError('export-parse-source-path-changed')
    if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('export-parse-source-changed')

def _json_native(value):
    if type(value) in (str,int,bool,type(None)):return True
    if type(value) is list:return all(_json_native(v) for v in value)
    if type(value) is dict:return all(type(k) is str and _json_native(v) for k,v in value.items())
    return False

def _key(source,job,receipt):
    # Unknown argument shapes retain the uncached function's original semantics.
    if type(job) is not dict or type(receipt) is not dict or not isinstance(source,(str,Path)):return None
    if not _json_native(job) or not _json_native(receipt):return None
    path=str(source);expected=receipt.get('src_sha256')
    if receipt.get('source')!=path or type(expected) is not str or len(expected)!=64 or any(c not in '0123456789abcdef' for c in expected):return None
    try:return (path,expected,json.dumps(job,sort_keys=True,ensure_ascii=False,allow_nan=False),json.dumps(receipt,sort_keys=True,ensure_ascii=False,allow_nan=False))
    except (TypeError,ValueError):return None

class _Session:
    def __init__(self,max_bytes):
        if type(max_bytes) is not int or max_bytes<0:raise ValueError('export-parse-memory-cap-invalid')
        self.max_bytes=max_bytes;self.entries={};self.stats={'hits':0,'misses':0,'bypasses':0,'hash_checks':0,'retained_bytes':0,'peak_retained_bytes':0,'entries':0}
    def check(self,key,compute,token):
        _source(key[0],key[1]);self.stats['hash_checks']+=1
        if _token(compute)!=token:raise ValueError('export-parse-code-changed')
    def load(self,key,compute,source,job,receipt):
        _source(key[0],key[1]);self.stats['hash_checks']+=1
        if key in self.entries:
            value,token,stored_compute=self.entries[key];self.check(key,compute,token);result=copy.deepcopy(value);self.check(key,compute,token);self.stats['hits']+=1;return result
        self.stats['misses']+=1;before=_token(compute);value=compute(source,job,receipt);after=_token(compute)
        # Initial openpyxl lazy import is allowed; existing code may not mutate.
        if any(name not in after or after[name]!=old for name,old in before.items()):raise ValueError('export-parse-code-changed')
        _source(key[0],key[1]);self.stats['hash_checks']+=1
        if _key(source,job,receipt)!=key:raise ValueError('export-parse-input-mutated')
        stored=copy.deepcopy(value);entries={**self.entries,key:(stored,after,compute)};weight=_size(entries)
        if weight<=self.max_bytes:
            self.entries=entries;self.stats['retained_bytes']=weight;self.stats['peak_retained_bytes']=max(self.stats['peak_retained_bytes'],self.stats['retained_bytes']);self.stats['entries']=len(self.entries)
        else:self.stats['bypasses']+=1
        return value
    def finish(self):
        for key,(value,token,compute) in self.entries.items():self.check(key,compute,token)
    def clear(self):self.entries.clear();self.stats['retained_bytes']=0;self.stats['entries']=0

@contextmanager
def owner_session(*,max_bytes=DEFAULT_MAX_BYTES):
    owner=_Session(max_bytes);mark=_OWNER.set(owner)
    try:
        yield MappingProxyType(owner.stats)
    except BaseException:raise
    else:owner.finish()
    finally:owner.clear();_OWNER.reset(mark)

def load(source,job,receipt,compute):
    owner=_OWNER.get();key=_key(source,job,receipt) if owner is not None else None
    return compute(source,job,receipt) if key is None else owner.load(key,compute,source,job,receipt)
