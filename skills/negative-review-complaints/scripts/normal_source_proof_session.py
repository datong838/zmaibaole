"""Explicit run owner for completed immutable normal-source reconstruction only.
No hook is installed here. Future joined_envelope hook must keep live page/ledger
validation outside. A reviewed loaded_guard supplies the full actual pure graph.
"""
import copy,hashlib,json,sys
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType,MappingProxyType,ModuleType
_OWNER=ContextVar('normal_immutable_source_proof_owner',default=None)
REFS={'job','envelope','profile','receipt','xlsx','source'}
MAX_BYTES=64*1024*1024

def _need(ok,message):
    if not ok:raise ValueError(message)
def _bytes(reference):
    _need(type(reference) is dict and set(reference)=={'path','sha256'},'source-proof-reference-shape')
    p=Path(reference['path']);_need(p.is_absolute() and p.resolve()==p and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),'source-proof-canonical-path')
    raw=p.read_bytes();_need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'source-proof-bytes-changed');return raw
def _json(value):
    if type(value) in (str,int,bool,type(None)):return True
    if type(value) is list:return all(_json(x) for x in value)
    return type(value) is dict and all(type(k) is str and _json(v) for k,v in value.items())
def _key(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).digest()
def _weight(value,seen=None):
    seen=set() if seen is None else seen
    if id(value) in seen:return 0
    seen.add(id(value));size=sys.getsizeof(value)
    if isinstance(value,dict):size+=sum(_weight(k,seen)+_weight(v,seen) for k,v in value.items())
    elif isinstance(value,(tuple,list,set,frozenset)):size+=sum(_weight(v,seen) for v in value)
    return size

def _function(fn):
    cells=tuple((type(c.cell_contents),id(c.cell_contents),getattr(c.cell_contents,'__code__',None)) for c in fn.__closure__ or ())
    return (fn,fn.__code__,repr(fn.__defaults__),repr(fn.__kwdefaults__),cells,id(fn.__globals__),fn.__globals__.get(fn.__name__))

def _provider_fingerprint(providers):
    # Independent direct reads: never ask C._token/_function to attest itself.
    result=[]
    for module,name in providers:
        _need(type(module) is ModuleType and type(name) is str,'source-proof-provider-shape')
        fn=module.__dict__.get(name)
        _need(isinstance(fn,FunctionType),'source-proof-provider-binding-changed')
        cells=tuple((id(c.cell_contents),getattr(c.cell_contents,'__code__',None)) for c in fn.__closure__ or ())
        result.append((module,name,fn,fn.__code__,repr(fn.__defaults__),repr(fn.__kwdefaults__),cells,id(fn.__globals__)))
    return tuple(result)

def _api_token():
    functions=[]
    for key,value in sorted(globals().items()):
        if isinstance(value,FunctionType):functions.append((key,_function(value)))
    methods=tuple((k,_function(v)) for k,v in sorted(vars(_Session).items()) if isinstance(v,FunctionType))
    return (tuple(functions),_Session,methods,tuple(sorted(REFS)),MAX_BYTES,_OWNER)

class _Session:
    def __init__(self,refs,scope,code_refs,loaded_guard,max_bytes,providers):
        _need(type(refs) is dict and set(refs)==REFS and _json(scope),'source-proof-admission-shape')
        _need(type(max_bytes) is int and max_bytes>=0,'source-proof-cap')
        _need(type(code_refs) is list and bool(code_refs) and len({r['path'] for r in code_refs})==len(code_refs) and str(Path(__file__).resolve()) in {r['path'] for r in code_refs},'source-proof-exact-code-refs')
        _need(isinstance(loaded_guard,FunctionType),'source-proof-loaded-guard-required')
        self.refs=copy.deepcopy(refs);self.scope=copy.deepcopy(scope);self.code_refs=copy.deepcopy(code_refs);self.guard=loaded_guard;self.max_bytes=max_bytes;self.entries={};self.extra=[]
        self.stats={'hits':0,'misses':0,'bypasses':0,'hash_checks':0,'retained_bytes':0,'peak_retained_bytes':0}
        self.providers=tuple(providers);self.provider_token=_provider_fingerprint(self.providers)
        self.api=_api_token();self.guard_entry=_function(loaded_guard);self.loaded=loaded_guard();self.check()
        bound={name:json.loads(_bytes(self.refs[name])) for name in ('job','envelope','profile')}
        receipt=json.loads(_bytes(self.refs['receipt']))
        _need(bound['job'].get('source_receipt')==self.refs['receipt']['path'] and bound['job'].get('source_receipt_sha256')==self.refs['receipt']['sha256'] and receipt.get('source')==self.refs['xlsx']['path'] and receipt.get('src_sha256')==self.refs['xlsx']['sha256'],'source-proof-receipt-xlsx-binding')
        terminal=bound['profile'].get('terminal_layout',{}).get('approved_page')
        self.extra=[copy.deepcopy(terminal)] if terminal else []
        for reference in self.extra:_bytes(reference)
        self.arguments=_key({**bound,'receipt_ref':self.refs['receipt']})
        self.base_weight=_weight((self.refs,self.scope,self.code_refs,self.loaded,self.api,self.arguments,self.extra,self.provider_token))
        _need(self.base_weight<=max_bytes,'source-proof-admission-over-cap')
        self.stats['retained_bytes']=self.stats['peak_retained_bytes']=self.base_weight
    def check(self):
        _need(_provider_fingerprint(self.providers)==self.provider_token,'source-proof-provider-binding-changed')
        for reference in (*self.refs.values(),*self.code_refs,*self.extra):_bytes(reference);self.stats['hash_checks']+=1
        _need(_api_token()==self.api and _function(self.guard)==self.guard_entry and self.guard()==self.loaded,'source-proof-loaded-code-changed')
    def get(self,arguments,compute):
        self.check()
        # Unknown shapes preserve original compute/exception semantics, no memo.
        if not _json(arguments):
            self.stats['bypasses']+=1;value=compute();self.check();return value
        key=_key(arguments);_need(key==self.arguments,'source-proof-bound-arguments-changed')
        if key in self.entries:
            result=copy.deepcopy(self.entries[key]);self.check();self.stats['hits']+=1;return result
        self.stats['misses']+=1;value=compute();self.check()
        _need(_key(arguments)==key,'source-proof-arguments-mutated')
        _need(not isinstance(value,dict) or '_ledger' not in value,'source-proof-ledger-forbidden')
        stored=copy.deepcopy(value);entries={**self.entries,key:stored};weight=self.base_weight+_weight(entries)
        if weight<=self.max_bytes:
            self.entries=entries;self.stats['retained_bytes']=weight;self.stats['peak_retained_bytes']=max(self.stats['peak_retained_bytes'],weight)
        else:self.stats['bypasses']+=1
        return value
    def clear(self):self.entries.clear();self.stats['retained_bytes']=0

@contextmanager
def owner_session(refs,scope,code_refs,loaded_guard,*,max_bytes=MAX_BYTES,providers=()):
    owner=_Session(refs,scope,code_refs,loaded_guard,max_bytes,providers);mark=_OWNER.set(owner)
    try:
        yield MappingProxyType(owner.stats)
        owner.check()
    finally:owner.clear();_OWNER.reset(mark)

def reconstruct(arguments,compute):
    owner=_OWNER.get()
    return compute() if owner is None else owner.get(arguments,compute)
