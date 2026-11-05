"""Bounded, process-local reuse for one pure pinned-evidence validation.
No disk trust receipts, UI, network, mutation, or negative-result cache. Every
pinned-file lookup and successful memo reuse checks current bytes, not mtime.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from collections import defaultdict
from bisect import bisect_left
from pathlib import Path
from types import FunctionType,ModuleType
import copy,hashlib,json,sys

_ACTIVE=ContextVar('governance_pure_verification_session',default=None)
_OWNER=ContextVar('governance_pure_verification_owner',default=None)
DEFAULT_MAX_BYTES=512*1024*1024
class FrozenDict(dict):
    __slots__=('_owner','_origin','_ordinal','_tree_root','_document_root')
    def _deny(self,*a,**k):raise TypeError('pinned-validation-input-is-immutable')
    __setitem__=__delitem__=clear=pop=popitem=setdefault=update=__ior__=_deny
    def __deepcopy__(self,memo):return {copy.deepcopy(k,memo):copy.deepcopy(v,memo) for k,v in self.items()}
class FrozenList(list):
    __slots__=('_owner','_origin','_document_root')
    def _deny(self,*a,**k):raise TypeError('pinned-validation-input-is-immutable')
    __setitem__=__delitem__=append=clear=extend=insert=pop=remove=reverse=sort=__iadd__=__imul__=_deny
    def __deepcopy__(self,memo):return [copy.deepcopy(v,memo) for v in self]
class NodeView:
    __slots__=('index','start','stop')
    def __init__(self,index,start,stop):self.index=index;self.start=start;self.stop=stop
    def __iter__(self):
        for i in range(self.start,self.stop):yield self.index['nodes'][i]
    def __len__(self):return self.stop-self.start

class Session:
    def __init__(self,*,enabled=True,max_bytes=DEFAULT_MAX_BYTES,revision='governance-pure-verification-v1'):
        if type(max_bytes) is not int or max_bytes<0:raise ValueError('verification-cache-memory-cap-invalid')
        self.enabled=enabled;self.max_bytes=max_bytes;self.revision=revision;self.owner=object();self.bytes=0;self.docs={};self.indexes={};self.memos={};self.frames=[];self.guard_frames=[];self.touched=set();self.all_guards=set();self.graph_tokens={}
        self.stats=defaultdict(int)
    def _reserve(self,weight):
        if weight>self.max_bytes-self.bytes:self.stats['cap_bypasses']+=1;return False
        self.bytes+=weight;self.stats['peak_retained_bytes']=max(self.stats['peak_retained_bytes'],self.bytes);return True
    def _check(self,ref):
        path,expected=ref;path=Path(path)
        if not path.is_absolute() or path.resolve()!=path or any(p.is_symlink() for p in (path,*path.parents)):raise ValueError('navigation-pinned-evidence-changed')
        if not path.is_file():raise ValueError('navigation-pinned-evidence-changed')
        data=path.read_bytes();self.stats['hash_checks']+=1;self.stats['hashed_bytes']+=len(data)
        if hashlib.sha256(data).hexdigest()!=expected:self.stats['changed_reference_rejections']+=1;raise ValueError('navigation-pinned-evidence-changed')
        if ref not in self.touched and self._reserve(256+len(str(path))):self.touched.add(ref)
        for dependencies in self.frames:dependencies.add((str(path),expected))
        return data
    def _freeze(self,value,origin=None,document_root=False):
        count=[0];roots={};seen=set();weight=[0]
        def account(obj):
            if id(obj) not in seen:seen.add(id(obj));weight[0]+=sys.getsizeof(obj)
        def freeze(v,tree_root=None,top=False):
            if isinstance(v,(FrozenDict,FrozenList)) and v._owner is self.owner:return v
            if isinstance(v,dict):
                count[0]+=1;ordinal=count[0];semantic=tree_root if tree_root is not None else ordinal if 'tag' in v and 'children' in v else None
                out=FrozenDict();out._owner=self.owner;out._origin=origin;out._ordinal=ordinal;out._tree_root=semantic;out._document_root=top;account(ordinal)
                for key,item in v.items():account(key);dict.__setitem__(out,key,freeze(item,semantic if key=='children' else None))
                if semantic==ordinal:roots[ordinal]=out
                account(out);return out
            if isinstance(v,tuple):
                out=tuple(freeze(item,tree_root) for item in v);account(out);return out
            if isinstance(v,list):
                out=FrozenList();out._owner=self.owner;out._origin=origin;out._document_root=top
                for item in v:list.append(out,freeze(item,tree_root))
                account(out);return out
            account(v);return v
        result=freeze(value,top=document_root)
        if origin is not None:
            account(origin)
            for part in origin:account(part)
        return result,weight[0]+sys.getsizeof(roots)+len(roots)*32+128,roots
    def read_pinned(self,path,checksum):
        ref=(str(Path(path)),checksum);data=self._check(ref)
        if self.enabled and ref in self.docs:self.stats['document_hits']+=1;return self.docs[ref]['value']
        self.stats['JSON_decodes']+=1;value=json.loads(data.decode('utf-8'))
        if not self.enabled or len(data)>self.max_bytes-self.bytes:self.stats['document_bypasses']+=1;return value
        frozen,weight,roots=self._freeze(value,ref,True)
        if not self._reserve(weight):return value
        self.docs[ref]={'value':frozen,'roots':roots};self.stats['document_misses']+=1;return frozen
    def document_ref(self,value):
        if isinstance(value,(FrozenDict,FrozenList)) and value._owner is self.owner and value._document_root and value._origin in self.docs:return value._origin
        return None
    def fingerprint(self,value,refs):
        ref=self.document_ref(value)
        if ref is not None:refs.add(ref);return ('pinned-document',ref)
        if isinstance(value,dict):
            if not all(type(k) is str for k in value):raise TypeError('verification-memo-nonstring-key')
            return ('dict',tuple(sorted((k,self.fingerprint(v,refs)) for k,v in value.items())))
        if isinstance(value,(list,tuple)):return (type(value).__name__,tuple(self.fingerprint(v,refs) for v in value))
        if type(value) in (str,int,float,bool,type(None)):return (type(value).__name__,value)
        raise TypeError('verification-memo-unreviewed-argument-type')
    def guard(self,function,path):
        result=function(path);item=(function,str(path))
        if item not in self.all_guards and self._reserve(256+len(str(path))):self.all_guards.add(item)
        for guards in self.guard_frames:guards.add((function,str(path)))
        return result
    def check_graphs(self):
        for module,signature in tuple(self.graph_tokens.items()):
            try:changed=loaded_graph(module)!=signature
            except (TypeError,ValueError):changed=True
            if changed:raise ValueError('verification-loaded-code-graph-changed')
    def memo(self,namespace,function,args,kwargs,*,code_token=(),isolated=False):
        if not self.enabled:return function(*args,**kwargs)
        roots=set();key=(namespace,self.revision,function.__code__,code_token,self.fingerprint(args,roots),self.fingerprint(kwargs,roots))
        old=self.memos.get(key)
        if old is not None:
            self.check_graphs()
            for guard,path in old.get('guards',()):self.guard(guard,path)
            for ref in old['dependencies']:self._check(ref)
            self.stats['memo_hits']+=1;return copy.deepcopy(old['value']) if isolated else old['value']
        dependencies=set(roots);guards=set();self.frames.append(dependencies);self.guard_frames.append(guards)
        try:
            for ref in roots:self._check(ref)
            value=function(*args,**kwargs)  # Failed calls never enter memos.
        except Exception:
            self.stats['memo_failures']+=1;raise
        finally:self.frames.pop();self.guard_frames.pop()
        frozen,weight,_=self._freeze(value)
        if self._reserve(weight+retained_weight(key)+retained_weight(dependencies)+retained_weight(guards)):self.memos[key]={'value':frozen,'dependencies':frozenset(dependencies),'guards':frozenset(guards)};self.stats['memo_misses']+=1
        return copy.deepcopy(frozen) if isolated else frozen
    def _index(self,node):
        if not self.enabled or not isinstance(node,FrozenDict) or node._owner is not self.owner or node._origin not in self.docs or node._tree_root is None:return None
        key=(node._origin,node._tree_root)
        if key in self.indexes:self.stats['tree_index_hits']+=1;return self.indexes[key]
        if self.max_bytes-self.bytes<4096:return None
        root=self.docs[node._origin]['roots'][node._tree_root];order=[];starts={};intervals={};stack=[(root,False)]
        while stack:
            n,leaving=stack.pop()
            if leaving:intervals[n._ordinal]=(starts[n._ordinal],len(order));continue
            starts[n._ordinal]=len(order);order.append(n);stack.append((n,True))
            for child in reversed(n.get('children',[])):stack.append((child,False))
        classes=defaultdict(list);ids=defaultdict(list)
        for i,n in enumerate(order):
            for c in set(n.get('attributes',{}).get('class','').split()):classes[c].append(i)
            ident=n.get('attributes',{}).get('id')
            if ident is not None:ids[ident].append(i)
        values=FrozenList(order);values._owner=self.owner;values._origin=None;values._document_root=False
        # One preorder + intervals per complete semantic tree; no per-subtree
        # list cache. Conservative retained-budget charge includes lookup maps.
        weight=sys.getsizeof(values)+len(order)*384+sum(sys.getsizeof(v)+len(v)*32+sys.getsizeof(k)+256 for k,v in classes.items())+sum(sys.getsizeof(v)+len(v)*32+sys.getsizeof(k)+256 for k,v in ids.items())
        if not self._reserve(weight):return None
        index={'nodes':values,'intervals':intervals,'classes':classes,'ids':ids};self.indexes[key]=index;self.stats['tree_index_misses']+=1;return index
    def walk_view(self,node):
        index=self._index(node)
        if index is None:return None
        start,stop=index['intervals'][node._ordinal];return NodeView(index,start,stop)
    def all_nodes(self,node):
        index=self._index(node)
        if index is None:return None
        start,stop=index['intervals'][node._ordinal]
        if start==0 and stop==len(index['nodes']):return index['nodes']
        return list(NodeView(index,start,stop))
    def matching(self,node,kind,value):
        index=self._index(node)
        if index is None:return None
        start,stop=index['intervals'][node._ordinal];positions=index[kind].get(value,[]);a=bisect_left(positions,start);b=bisect_left(positions,stop)
        return [index['nodes'][positions[i]] for i in range(a,b)]
    def summary(self):return {**self.stats,'retained_bytes':self.bytes,'max_bytes':self.max_bytes,'documents':len(self.docs),'trees':len(self.indexes),'successful_memos':len(self.memos)}

def current():return _ACTIVE.get()
@contextmanager
def validation_scope(*,enabled=True,max_bytes=DEFAULT_MAX_BYTES,revision='governance-pure-verification-v1'):
    existing=current()
    if existing is not None:yield existing;return
    session=_OWNER.get() or Session(enabled=enabled,max_bytes=max_bytes,revision=revision);token=_ACTIVE.set(session)
    try:
        yield session
        session.check_graphs()
        for function,path in tuple(session.all_guards):session.guard(function,path)
        for ref in tuple(session.touched):session._check(ref)
    finally:_ACTIVE.reset(token)

def _constant(value,depth=0):
    if depth>5:return None
    if type(value) in (str,int,float,bool,type(None)):return (type(value).__name__,value)
    if isinstance(value,type):return ('class-identity',value)
    if isinstance(value,(list,tuple)) and len(value)<=128:
        parts=[_constant(v,depth+1) for v in value]
        if all(v is not None for v in parts):return (type(value).__name__,tuple(parts))
    if isinstance(value,dict) and len(value)<=128 and all(type(k) is str for k in value):
        parts=[(k,_constant(v,depth+1)) for k,v in sorted(value.items())]
        if all(v is not None for _,v in parts):return ('dict',tuple(parts))
    return None

def _function_token(function):
    # The fixed reviewed validator graph has no dynamic closures. Do not invent
    # a cache key for arbitrary captured mutable state: caller falls back.
    closure=[]
    for name,cell in zip(function.__code__.co_freevars,function.__closure__ or ()):
        if function in (validation_scope,owner_session) and function.__wrapped__ is cell.cell_contents and function.__code__.co_freevars==('func',):
            closure.append((name,_function_token(cell.cell_contents)))
        elif name=='__class__' and isinstance(cell.cell_contents,type):closure.append((name,cell.cell_contents))
        else:raise TypeError('verification-memo-dynamic-closure')
    defaults=_constant(function.__defaults__);kwdefaults=_constant(function.__kwdefaults__)
    if defaults is None or kwdefaults is None:raise TypeError('verification-memo-dynamic-default')
    return (function.__code__,defaults,kwdefaults,tuple(closure))

def code_signature(modules):
    """Actual loaded code + simple semantic constants; no disk trust token."""
    result=[]
    for module in modules:
        entries=[]
        for name,value in vars(module).items():
            if isinstance(value,FunctionType):entries.append((name,_function_token(value)))
            elif isinstance(value,type) and value.__module__==module.__name__:
                entries.append((name,tuple((k,_function_token(v)) for k,v in vars(value).items() if isinstance(v,FunctionType))))
            elif isinstance(value,ModuleType):entries.append((name,('module-alias',value)))
            elif name.isupper():
                constant=_constant(value)
                if constant is not None:entries.append((name,constant))
        result.append((module.__name__,tuple(sorted(entries,key=lambda x:x[0]))))
    return tuple(result)


def retained_weight(value):
    seen=set()
    def size(v):
        if id(v) in seen:return 0
        seen.add(id(v));n=sys.getsizeof(v)
        if isinstance(v,dict):n+=sum(size(k)+size(w) for k,w in v.items())
        elif isinstance(v,(list,tuple,set,frozenset)):n+=sum(size(w) for w in v)
        return n
    return size(value)

def loaded_graph(module):
    # Follow the actual script module aliases, including separately loaded nav.
    directory=Path(module.__file__).resolve().parent;pending=[module];seen=set();modules=[]
    while pending:
        item=pending.pop()
        if id(item) in seen:continue
        seen.add(id(item));modules.append(item)
        for value in vars(item).values():
            if isinstance(value,ModuleType) and getattr(value,'__file__',None) and Path(value.__file__).resolve().parent==directory:pending.append(value)
    ordered=sorted(modules,key=lambda m:(m.__name__,id(m)));aliases=[]
    for item in ordered:
        entries=[]
        for name,value in vars(item).items():
            if isinstance(value,FunctionType):entries.append((name,value,id(value.__globals__)))
            elif isinstance(value,type) and value.__module__==item.__name__:
                entries.append((name,value,tuple((k,v,id(v.__globals__)) for k,v in vars(value).items() if isinstance(v,FunctionType))))
        aliases.append((item,tuple(sorted(entries,key=lambda e:e[0]))))
    return (code_signature(ordered),tuple(aliases))

def memo_proof(function,proof_ref):
    session=current()
    if session is None or not session.enabled:return function(proof_ref)
    if not isinstance(proof_ref,dict) or set(proof_ref)!={'path','sha256'} or any(type(proof_ref[k]) is not str for k in ('path','sha256')):return function(proof_ref)
    module=sys.modules[function.__module__]
    try:token=loaded_graph(module)
    except (TypeError,ValueError):return function(proof_ref)
    if module in session.graph_tokens and session.graph_tokens[module]!=token:raise ValueError('verification-loaded-code-graph-changed')
    if module not in session.graph_tokens:
        if not session._reserve(retained_weight(token)+128):return function(proof_ref)
        session.graph_tokens[module]=token
    return session.memo(function.__module__+'.'+function.__name__,function,(proof_ref,),{},code_token=token,isolated=True)


@contextmanager
def owner_session(session):
    if current() is not None:raise ValueError('verification-live-owner-inside-pure-scope')
    token=_OWNER.set(session)
    try:yield
    finally:_OWNER.reset(token)


def owner():return _OWNER.get()

# Explicit private pure graphs: no change to memo_proof/_function_token policy.
def _pure_semantic(value):
    if isinstance(value,Path):return ('path',str(value))
    if isinstance(value,(set,frozenset)):
        result=_constant(tuple(sorted(value)))
    elif isinstance(value,ContextVar):return ('contextvar-identity',value)
    else:result=_constant(value)
    if result is None:raise ValueError('verification-pure-semantics-invalid')
    return result

def _registered_token(groups):
    result=[]
    for module,names,constants in groups:
        functions=[]
        for name in names:
            value=vars(module).get(name)
            if not isinstance(value,FunctionType):raise ValueError('verification-pure-function-alias-changed')
            functions.append((name,value,id(value.__globals__),_function_token(value)))
        aliases=tuple(sorted((name,value)for name,value in vars(module).items()if isinstance(value,ModuleType)))
        semantics=tuple((name,_pure_semantic(vars(module)[name]))for name in constants)
        result.append((module,tuple(functions),aliases,semantics))
    return tuple(result)

def _pure_source_path(path):
    # Preserve the original lexical origin: never resolve a symlink to an
    # archive and then mistake that archive for a loadable canonical module.
    import stat
    path=Path(path)
    if not path.is_absolute()or any(p.is_symlink()for p in (path,*path.parents))or path.resolve()!=path or not stat.S_ISREG(path.lstat().st_mode):raise ValueError('verification-pure-source-origin')
    return str(path)

def _pure_module_source(self,module,path):
    if str(Path(module.__file__))!=str(path):raise ValueError('verification-pure-module-origin')
    self.guard(_pure_source_path,str(path))

def _bound_module(self,key,path,loader):
    token=(loader,id(loader.__globals__),_function_token(loader));path=Path(path)
    self.guard(_pure_source_path,str(path))
    modules=getattr(self,'_pure_modules',None)
    if modules is None:self._pure_modules={};modules=self._pure_modules
    if key in modules:
        old=modules[key]
        if old['path']!=str(path)or old['loader']!=token:raise ValueError('verification-pure-loader-changed')
        _pure_module_source(self,old['module'],old['path']);self._check(old['ref']);return old['module']
    if len(modules)>=4:raise ValueError('verification-pure-module-limit')
    raw=path.read_bytes();reference=(str(path),hashlib.sha256(raw).hexdigest());self._check(reference)
    module=loader()
    _pure_module_source(self,module,path)
    self._check(reference)
    if not self._reserve(len(raw)+4096):raise ValueError('verification-pure-module-memory-limit')
    modules[key]={'path':str(path),'loader':token,'ref':reference,'module':module};return module

def _registered_memo(self,name,function,proof_ref,groups,context):
    if not isinstance(proof_ref,dict)or set(proof_ref)!={'path','sha256'}or any(type(proof_ref[k])is not str for k in proof_ref):raise ValueError('verification-pure-proof-ref')
    if not any(vars(module).get(alias)is function for module,names,constants in groups for alias in names):raise ValueError('verification-pure-entry-not-registered')
    token=_registered_token(groups);partition=self.fingerprint(context,set())
    graphs=getattr(self,'_pure_graphs',None)
    if graphs is None:self._pure_graphs={};graphs=self._pure_graphs
    if name in graphs and graphs[name]['token']!=token:raise ValueError('verification-pure-code-graph-changed')
    if name not in graphs:
        if len(graphs)>=4:raise ValueError('verification-pure-graph-limit')
        sources=[];origins=[]
        for module in [*(m for m,_,_ in groups),sys.modules[__name__]]:
            path=Path(module.__file__);_pure_module_source(self,module,path)
            data=path.read_bytes();reference=(str(path),hashlib.sha256(data).hexdigest());origins.append((module,str(path)))
            if reference not in sources:sources.append(reference)
        if not self._reserve(retained_weight(token)+retained_weight(sources)+128):return function(proof_ref)
        graphs[name]={'token':token,'groups':groups,'sources':tuple(sources),'origins':tuple(origins)}
    for module,path in graphs[name]['origins']:_pure_module_source(self,module,path)
    for reference in graphs[name]['sources']:self._check(reference)
    return self.memo(name,function,(dict(proof_ref),),{},code_token=(token,partition),isolated=True)

_REGISTERED_ORIGINAL_CHECK_GRAPHS=Session.check_graphs
def _registered_check_graphs(self):
    _REGISTERED_ORIGINAL_CHECK_GRAPHS(self)
    for entry in getattr(self,'_pure_modules',{}).values():
        _pure_module_source(self,entry['module'],entry['path']);self._check(entry['ref'])
    for entry in getattr(self,'_pure_graphs',{}).values():
        for module,path in entry['origins']:_pure_module_source(self,module,path)
        if _registered_token(entry['groups'])!=entry['token']:raise ValueError('verification-pure-code-graph-changed')
        for reference in entry['sources']:self._check(reference)
Session.bound_pure_module=_bound_module
Session.memo_registered_pure=_registered_memo
Session.check_graphs=_registered_check_graphs
