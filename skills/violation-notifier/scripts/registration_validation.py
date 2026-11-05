"""Pure registration-node verification transaction (isolated production proposal).
Only Python path-based readers are supported: audited read opens include Pillow.
A file-descriptor reader, write, subprocess or network event rejects this scope.
Only pinned governance documents may use the existing bounded immutable tree
index inside this pure scope; no derive memo, live request or cross-command cache.
"""
import copy,hashlib,json,os,sys,threading,pathlib
from pathlib import Path
from contextvars import ContextVar
from contextlib import contextmanager,nullcontext
_ACTIVE=ContextVar('region_node_memo',default=None)
_SCOPE_LOCK=threading.RLock()
_COMMAND_BINDING=ContextVar('registration_command_owner',default=None)
_EFFECT_CHECK=ContextVar('registration_effect_check',default=False)
_STANDARD_PATH_TYPES=tuple((getattr(pathlib,name),name) for name in ('PosixPath','WindowsPath','PurePosixPath','PureWindowsPath'))

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def _audit(event,args):
    scope=_ACTIVE.get()
    if scope is None:
        write_open=event=='open' and bool(args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if write_open or event in ('subprocess.Popen','os.system','socket.connect','socket.bind','os.fork','os.forkpty','os.posix_spawn','os.exec','os.remove','os.rename','os.mkdir','os.rmdir','os.link','os.symlink','os.truncate','os.chmod','os.chown','os.utime','sqlite3.connect'):
            effect_boundary()
        return
    if scope.suspended:return
    if event in ('subprocess.Popen','os.system','socket.connect','socket.bind','os.fork','os.forkpty','os.posix_spawn','os.exec','os.remove','os.rename','os.mkdir','os.rmdir','os.link','os.symlink','os.truncate','os.chmod','os.chown','os.utime','sqlite3.connect'):
        scope.invalidated='candidate-not-pure-validation';raise ValueError(scope.invalidated)
    if event!='open':return
    path,mode,flags=args
    if not isinstance(path,(str,bytes,os.PathLike)):
        scope.invalidated='candidate-untracked-file-descriptor';raise ValueError(scope.invalidated)
    if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        scope.invalidated='candidate-write-forbidden';raise ValueError(scope.invalidated)
    scope.record(path)
sys.addaudithook(_audit)

class Session:
    def __init__(self,code_token,*,max_bytes=32*1024*1024):
        self.code_token=code_token;self.token=code_token();self.max_bytes=max_bytes;self.retained=0
        self.invalidated=None;self.generation=0;self.entries={};self.stack=[];self.in_progress=set();self.all_deps={};self.all_guards={};self.suspended=False;self.normalization=[]
        self.stats={'hits':0,'misses':0,'bypasses':0,'hash_checks':0,'guard_checks':0,'semantic_computations':0,'unpublished_computations':0,'history_hits':0,'history_misses':0}
    @contextmanager
    def pause(self):
        previous=self.suspended;self.suspended=True
        try:yield
        finally:self.suspended=previous
    def record(self,path):
        with self.pause():
            p=str(Path(path).resolve())
            if not Path(p).is_file():return # the real reader retains its missing-file error
            checksum=digest(p);self.stats['hash_checks']+=1
        self._merge({p:checksum},{})
    def _merge(self,deps,guards):
        for p,h in deps.items():
            if p in self.all_deps and self.all_deps[p]!=h:raise ValueError('candidate-dependency-changed')
            if p not in self.all_deps and len(self.all_deps)>=10000:raise ValueError('candidate-dependency-budget-exhausted')
            self.all_deps[p]=h
            for frame in self.stack:
                if p in frame['deps'] and frame['deps'][p]!=h:raise ValueError('candidate-dependency-changed')
                frame['deps'][p]=h
        self.all_guards.update(guards)
        for frame in self.stack:frame['guards'].update(guards)
    def _check(self,deps,guards):
        if self.invalidated:raise ValueError('candidate-pure-scope-invalidated:'+self.invalidated)
        current=self.code_token()
        if current!=self.token:
            error=ValueError('candidate-code-graph-changed');error.code_graph_difference=code_token_difference(self.token,current);raise error
        with self.pause():
            for path,checksum in deps.items():
                self.stats['hash_checks']+=1
                if digest(path)!=checksum:raise ValueError('candidate-dependency-changed')
            for guard,args in guards.values():
                self.stats['guard_checks']+=1;guard(*copy.deepcopy(args))
    def guard(self,guard,args):
        key=canonical(args)
        with self.pause():result=guard(*args)
        self._merge({}, {key:(guard,copy.deepcopy(args))})
        return result
    def node(self,reference,image,source,allow_preview,metadata,compute):
        # caller must have obtained this ref from the original document reader;
        # matching bytes alone cannot authorize unpublished mutable dictionaries.
        path=str(Path(reference['path']).resolve());checksum=reference['sha256']
        with self.pause():
            data=Path(path).read_bytes()
            if hashlib.sha256(data).hexdigest()!=checksum:raise ValueError('candidate-registration-changed')
            if json.loads(data)!=metadata:raise ValueError('candidate-metadata-mutated')
        key=(path,checksum,str(Path(image).resolve()),canonical(source),type(allow_preview).__name__,allow_preview,self.token)
        self._merge({path:checksum},{})
        if key in self.in_progress:raise ValueError('candidate-registration-cycle')
        if key in self.entries:
            old=self.entries[key];self._check(old['deps'],old['guards']);self._merge(old['deps'],old['guards']);self.stats['hits']+=1
            return copy.deepcopy(old['result'])
        self.stats['misses']+=1;frame={'deps':{path:checksum},'guards':{}};self.stack.append(frame);self.in_progress.add(key)
        try:
            result=compute();self._check(frame['deps'],frame['guards'])
            stored=copy.deepcopy(result);weight=len(canonical(stored).encode())+sum(len(p)+len(h)+128 for p,h in frame['deps'].items())+len(repr(frame['guards']))+512
            if self.retained+weight<=self.max_bytes:
                self.entries[key]={'result':stored,'deps':dict(frame['deps']),'guards':dict(frame['guards'])};self.retained+=weight
            else:self.stats['bypasses']+=1
            return result
        finally:self.stack.pop();self.in_progress.remove(key)
    def reboot_history(self,reference,compute,frontier,frontier_guard):
        try:return self._reboot_history_checked(reference,compute,frontier,frontier_guard)
        except BaseException:
            self.invalidated='candidate-history-verification-failed';self.entries.clear();raise
    def _reboot_history_checked(self,reference,compute,frontier,frontier_guard):
        """Only R.verify's historical branch in this transaction, no global memo."""
        module=sys.modules.get('violation_reboot_continuation')
        if (_ACTIVE.get() is not self or self.suspended or not hasattr(self,'region_module') or module is None or compute is not module._verify_uncached or frontier is not module._verify_history_frontier or frontier_guard is not module._guard_history_frontier):raise ValueError('candidate-history-caller-binding')
        if type(reference)is not dict or set(reference)!={'path','sha256'}:return compute(reference,live_boot=None)
        bound=copy.deepcopy(reference);key=('R.verify-history-v1',canonical(bound),self.region_module,self.generation,compute,compute.__code__,self.token)
        self._check({},{})
        if key in self.in_progress:raise ValueError('candidate-history-cycle')
        if key in self.entries:
            old=self.entries[key];self._check(old['deps'],old['guards']);self._merge(old['deps'],old['guards']);self.stats['history_hits']+=1
            if reference!=bound:raise ValueError('candidate-history-reference-mutated')
            return copy.deepcopy(old['result'])
        self.stats['history_misses']+=1;frame={'deps':{},'guards':{}};self.stack.append(frame);self.in_progress.add(key)
        try:
            snapshot=frontier(bound);self.guard(frontier_guard,(bound,snapshot))
            result=compute(copy.deepcopy(bound),live_boot=None)
            if reference!=bound:raise ValueError('candidate-history-reference-mutated')
            self._check(frame['deps'],frame['guards']);stored=copy.deepcopy(result);weight=len(canonical(stored).encode())+sum(len(p)+len(h)+128 for p,h in frame['deps'].items())+len(repr(frame['guards']))+512
            if self.retained+weight<=self.max_bytes:self.entries[key]={'result':stored,'deps':dict(frame['deps']),'guards':dict(frame['guards'])};self.retained+=weight
            else:self.stats['bypasses']+=1
            return copy.deepcopy(stored)
        except BaseException:
            self.invalidated='candidate-history-compute-failed';self.entries.clear();raise
        finally:self.stack.pop();self.in_progress.remove(key)
    def finish(self):self._check(self.all_deps,self.all_guards)
    @contextmanager
    def transaction(self):
        if _ACTIVE.get() is not None:raise ValueError('candidate-nested-transaction-forbidden')
        entry=getattr(self,'command_entry',None)
        if entry is not None:
            _guard_command_entry(entry)
            if not self.generation:self.generation=1
        else:self.generation+=1
        token=_ACTIVE.set(self)
        try:
            yield self;self.finish()
        except BaseException as error:
            if entry is not None:_record_command_failure(entry,error);self.invalidated='candidate-command-validation-failed';self.entries.clear()
            raise
        finally:
            if entry is None:self.entries.clear();self.all_deps.clear();self.all_guards.clear();self.retained=0
            _ACTIVE.reset(token)

@contextmanager
def installed(region_module,session):
    """Patch only this isolated interpreter. Use one scope for pure inspect;
    capture's fresh/live stages must never be executed through this adapter.
    code_token must cover actual reviewed loaded functions/constants and files,
    normalizing only these exact three installed adapter functions.
    """
    sr=region_module.sr;original_document=sr.document;original_validate=region_module.validate_frame;original_prefix=region_module._selection_prefix
    documents={}
    def document(reference):
        if _ACTIVE.get() is not session:return original_document(reference)
        value=original_document(reference)
        # Keep the original object strongly referenced to prevent id reuse.
        if isinstance(value,dict) and 'capture_backend' in value and 'pinned_inputs' in value:
            weight=8*len(canonical(value).encode())+512
            if session.retained+weight<=session.max_bytes:
                documents[id(value)]=(value,dict(reference),weight);session.retained+=weight
            else:session.stats['bypasses']+=1
        return value
    def prefix(selection,source,profile_sha):
        if _ACTIVE.get() is not session:return original_prefix(selection,source,profile_sha)
        return session.guard(original_prefix,(selection,source,profile_sha))
    def validate(image,m,*,source,allow_preview=False):
        if _ACTIVE.get() is not session:return original_validate(image,m,source=source,allow_preview=allow_preview)
        seen=documents.get(id(m))
        def compute():
            session.stats['semantic_computations']+=1
            return original_validate(image,m,source=source,allow_preview=allow_preview)
        if seen is None or seen[0] is not m:
            session.stats['unpublished_computations']+=1
            return compute() # unpublished dict: no node result memo
        # Consume authentication immediately. The normal call stack owns m now;
        # the registry must not add a second long-lived metadata owner.
        held=documents.pop(id(m));session.retained-=held[2]
        return session.node(seen[1],image,source,allow_preview,m,compute)

    sr.document=document;region_module.validate_frame=validate;region_module._selection_prefix=prefix
    session.normalization=[(sr,'document',document,original_document),(region_module,'validate_frame',validate,original_validate),(region_module,'_selection_prefix',prefix,original_prefix)]
    try:yield
    finally:
        sr.document=original_document;region_module.validate_frame=original_validate;region_module._selection_prefix=original_prefix;session.normalization=[]


def fixed_subprocess_token(module):
    """Only the already-observed stdlib subprocess.run default's loaded graph.
    Nothing here executes it; subprocess execution remains forbidden by audit.
    Canonical builtin defaults are signed by identity, never converted to absent.
    """
    import types
    def value_token(value):
        if type(value) in (str,int,float,bool,type(None)):return (type(value).__name__,value)
        if isinstance(value,(tuple,list)):return (type(value).__name__,tuple(value_token(x) for x in value))
        if isinstance(value,dict) and all(type(k) is str for k in value):return ('dict',tuple(sorted((k,value_token(x)) for k,x in value.items())))
        if isinstance(value,types.BuiltinFunctionType):
            owner=sys.modules.get(value.__module__)
            if owner is None or getattr(owner,value.__name__,None) is not value:raise ValueError('candidate-stdlib-builtin-not-fixed')
            return ('canonical-builtin',value,value.__module__,value.__name__)
        if isinstance(value,type):return ('class-identity',value)
        raise ValueError('candidate-stdlib-default-unsupported')
    def function(fn):
        if fn.__closure__:raise ValueError('candidate-stdlib-closure-unsupported')
        return (fn,fn.__code__,value_token(fn.__defaults__),value_token(fn.__kwdefaults__))
    entries=[]
    for name,value in vars(module).items():
        if isinstance(value,types.FunctionType):entries.append((name,function(value)))
        elif isinstance(value,type) and value.__module__==module.__name__:
            entries.append((name,value,tuple((k,function(v)) for k,v in vars(value).items() if isinstance(v,types.FunctionType))))
        elif isinstance(value,types.ModuleType):entries.append((name,('module-identity',value)))
        elif not name.startswith('__') and type(value) in (str,int,float,bool,type(None),list,tuple,dict):entries.append((name,value_token(value)))
    return (module,tuple(entries))

def reviewed_graph_token(modules,signature_function,normalization):
    """Fixed reviewed Python graph only; caller supplies its complete module list.
    Unknown dynamic closures/constants rejected by the existing graph signer.
    Include every actual source byte hash; no file-stat trust.
    """
    from types import ModuleType
    views=[];files=[];decorators=[];function_defaults=[];path_defaults=[]
    module_map={m.__name__:m for m in modules}
    import contextlib,types
    contextmanager_code=contextlib.contextmanager(lambda: None).__code__
    def fixed_default(value,visiting):
        for cls,name in _STANDARD_PATH_TYPES:
            if type(value) is cls:
                if getattr(pathlib,name) is not cls or cls.__module__!='pathlib':raise ValueError('registration-path-class-binding-changed')
                # Lexical value only: never resolve/stat/read the named file.
                literal=(str(value),tuple(value.parts))
                path_defaults.append((value,id(value),cls,name,literal,pathlib,digest(pathlib.__file__)))
                return ('standard-path-default',cls.__module__,name,*literal),[]
        if isinstance(value,types.FunctionType):
            owner=module_map.get(value.__module__);external_token=None
            if owner is None and value.__module__=='subprocess' and value.__name__=='run':
                import subprocess
                owner=subprocess
                if value is not subprocess.run:raise ValueError('candidate-default-function-not-fixed:subprocess:run')
                external_token=(fixed_subprocess_token(subprocess),digest(subprocess.__file__))
            fixed=owner is not None and getattr(owner,value.__name__,None) is value
            if not fixed and owner is not None and owner.__name__=='chrome_process_identity' and value.__name__=='<lambda>':
                target=getattr(owner,'verify',None);slot=(getattr(target,'__kwdefaults__',None) or {}).get('resolve_fn')
                source=Path(owner.__file__).resolve()
                if slot is value and not value.__closure__ and value.__defaults__ is None and value.__kwdefaults__ is None and Path(value.__code__.co_filename).resolve()==source:
                    compiled=compile(source.read_bytes(),str(source),'exec',dont_inherit=True)
                    literals=[c for c in compiled.co_consts if isinstance(c,types.CodeType) and c.co_name=='<lambda>' and c.co_firstlineno==value.__code__.co_firstlineno]
                    fixed=len(literals)==1 and literals[0]==value.__code__
            if not fixed:raise ValueError('candidate-default-function-not-fixed:'+value.__module__+':'+value.__name__)
            if value.__closure__:raise ValueError('candidate-default-function-closure')
            if value in visiting:raise ValueError('candidate-default-function-cycle')
            clone,extras=normalized_function(value,visiting|{value})
            probe=ModuleType(value.__module__);setattr(probe,value.__name__,clone)
            function_defaults.append((value,value.__module__,value.__name__,signature_function([probe]),tuple(extras),external_token))
            return ('fixed-function-default',value.__module__,value.__name__),[]
        if isinstance(value,type) and value.__module__!='builtins':
            owner=module_map.get(value.__module__)
            if owner is None or getattr(owner,value.__name__,None) is not value:raise ValueError('candidate-default-class-not-fixed:'+value.__module__+':'+value.__name__)
        return value,[]
    def normalized_function(fn,visiting):
        defaults=[];extras=[];changed=False
        for value in fn.__defaults__ or ():
            item,extra=fixed_default(value,visiting);defaults.append(item);extras.extend(extra);changed=changed or item is not value
        kw={}
        for key,value in (fn.__kwdefaults__ or {}).items():
            item,extra=fixed_default(value,visiting);kw[key]=item;extras.extend(extra);changed=changed or item is not value
        if not changed:return fn,extras
        clone=types.FunctionType(fn.__code__,fn.__globals__,fn.__name__,tuple(defaults) if fn.__defaults__ is not None else None,fn.__closure__)
        clone.__kwdefaults__=kw if fn.__kwdefaults__ is not None else None
        return clone,extras
    for module in modules:
        view=ModuleType(module.__name__);view.__dict__.update(vars(module))
        for owner,name,adapter,original in normalization:
            if owner is module:
                if getattr(module,name) is not adapter:raise ValueError('candidate-adapter-code-changed')
                setattr(view,name,original)
        for name,value in list(vars(view).items()):
            if isinstance(value,types.FunctionType) and value.__code__ is contextmanager_code:
                wrapped=getattr(value,'__wrapped__',None);cells=value.__closure__ or ()
                if not isinstance(wrapped,types.FunctionType) or len(cells)!=1 or cells[0].cell_contents is not wrapped:raise ValueError('candidate-contextmanager-code-changed')
                decorators.append((module.__name__,name,value.__code__,wrapped.__code__));setattr(view,name,wrapped)
        for name,value in list(vars(view).items()):
            if isinstance(value,types.FunctionType):
                normalized,_=normalized_function(value,{value});setattr(view,name,normalized)
        for name,value in list(vars(view).items()):
            if isinstance(value,type) and value.__module__==module.__name__:
                methods={};changed=False
                for method_name,method in vars(value).items():
                    if not isinstance(method,types.FunctionType):continue
                    if method.__code__ is contextmanager_code:
                        wrapped=getattr(method,'__wrapped__',None);cells=method.__closure__ or ()
                        if not isinstance(wrapped,types.FunctionType) or len(cells)!=1 or cells[0].cell_contents is not wrapped:raise ValueError('registration-contextmanager-method-changed')
                        decorators.append((module.__name__,name,method_name,value,method.__code__,wrapped.__code__));method=wrapped;changed=True
                    normalized,_=normalized_function(method,{method});methods[method_name]=normalized;changed=changed or normalized is not method
                if changed:
                    # Signature-only class view, never instantiated. Preserve the
                    # actual class identity separately; no inheritance hooks run.
                    decorators.append((module.__name__,name,'class-identity',value))
                    methods['__module__']=value.__module__;setattr(view,name,type(value.__name__,(),methods))
        views.append(view)
        path=getattr(module,'__file__',None)
        if path:files.append((str(Path(path).resolve()),digest(path)))
    return signature_function(views),tuple(files),tuple(decorators),tuple(function_defaults),tuple(path_defaults)

# Production proposal: one explicit pure scope. No workflow entrypoint is cached.
def loaded_graph(region_module):
    """Include actual module aliases, even spec-loaded modules absent sys.modules."""
    import types
    here=sys.modules[__name__]
    roots={Path(here.__file__).resolve().parent,Path(region_module.__file__).resolve().parent,Path(region_module.fc.__file__).resolve().parent}
    for name in ('governance_detail','verification_session'):
        known=sys.modules.get(name)
        if known is not None:roots.add(Path(known.__file__).resolve().parent)
    scripts_root=Path(region_module.fc.__file__).resolve().parents[3]/'skills'
    seen=set();queue=[here,region_module]
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and Path(path).resolve().parent in roots:queue.append(module)
    result=[]
    while queue:
        module=queue.pop()
        if id(module) in seen:continue
        seen.add(id(module));result.append(module)
        for value in vars(module).values():
            path=getattr(value,'__file__',None) if isinstance(value,types.ModuleType) else None
            if path and Path(path).resolve().parent in roots:queue.append(value)
            if isinstance(value,types.FunctionType):
                owner=sys.modules.get(value.__module__);owner_path=getattr(owner,'__file__',None)
                if owner_path and scripts_root in Path(owner_path).resolve().parents:queue.append(owner)
    return sorted(result,key=lambda m:(m.__name__,str(Path(m.__file__).resolve()),id(m)))

def _execution_identity():
    module=sys.modules.get('asyncio');task=None
    if module is not None:
        try:task=module.current_task()
        except RuntimeError:pass
    return os.getpid(),threading.get_ident(),task

def _record_command_failure(entry,error):
    entry['failed']=True
    if entry.get('failure') is None:entry['failure']=error

def _raise_command_failure(entry):
    error=entry.get('failure')
    if isinstance(error,BaseException):raise error
    raise ValueError('registration-command-prior-validation-failed')

def _guard_command_entry(entry):
    if entry['closed'] or entry['execution']!=_execution_identity():raise ValueError('registration-command-owner-conflict')
    if entry['failed']:_raise_command_failure(entry)
    binding=_COMMAND_BINDING.get()
    if binding is not None and binding is not entry:raise ValueError('registration-command-context-conflict')
    if not entry['closing']:
        import execution_timing as timing
        if timing._POLICY_COMMAND.get() is not entry['state']:raise ValueError('registration-command-state-conflict')

def _clear_governance(session):
    for name in ('docs','indexes','memos','frames','guard_frames','touched','all_guards','graph_tokens'):getattr(session,name).clear()
    session.bytes=0;session.enabled=False

def effect_boundary():
    """Verify then retire an owned pure epoch BEFORE a possible external effect.
    This is not authorization for the effect. Its original caller guards remain.
    An in-pure operation is rejected by the audit hook, never retired/rebased.
    """
    if _EFFECT_CHECK.get():return
    if _ACTIVE.get() is not None:raise ValueError('registration-effect-inside-pure-scope')
    timing=sys.modules.get('execution_timing')
    state=timing._POLICY_COMMAND.get() if timing is not None else None
    entry=state.get('registration_pure_owner_v1') if state is not None else None
    if entry is None:return
    if entry.get('closed'):raise ValueError('registration-command-closed-context')
    _guard_command_entry(entry)
    parser=entry['parser'];scope=entry['registration']
    if scope is None:return
    token=_EFFECT_CHECK.set(True)
    try:
        import verification_session as verification
        if verification.current() is not None or verification.owner() is not None:raise ValueError('registration-effect-foreign-parser')
        with verification.owner_session(parser),verification.validation_scope(max_bytes=parser.max_bytes):
            active=_ACTIVE.set(scope)
            try:
                with installed(scope.region_module,scope):scope.finish()
            finally:_ACTIVE.reset(active)
    except BaseException as error:
        _record_command_failure(entry,error)
        raise
    finally:
        scope.entries.clear();scope.all_deps.clear();scope.all_guards.clear();scope.retained=0;scope.invalidated='candidate-effect-epoch-closed'
        _clear_governance(parser);entry['registration']=None
        # Never reuse old parsed docs, touched refs, guards, or a stale token.
        entry['parser']=verification.Session(max_bytes=32*1024*1024,revision='registration-command-pinned-v1')
        entry['effect_epochs']=entry.get('effect_epochs',0)+1
        _EFFECT_CHECK.reset(token)

def _finish_command_entry(entry):
    # The policy ContextVar has already reset. Use only this exact stored owner.
    parser=entry['parser'];scope=entry['registration'];entry['closing']=True
    previous_binding=_COMMAND_BINDING.get();token=_COMMAND_BINDING.set(entry)
    try:
        _guard_command_entry_for_exit(entry,previous_binding)
        if entry['failed'] or (scope is not None and scope.invalidated):
            if sys.exc_info()[0] is None:_raise_command_failure(entry)
            return
        import verification_session as verification
        owner_context=verification.owner_session(parser) if verification.current() is None and verification.owner() is None else nullcontext()
        with owner_context,verification.validation_scope(max_bytes=parser.max_bytes):
            if scope is not None:
                active=_ACTIVE.set(scope)
                try:
                    with installed(scope.region_module,scope):scope.finish()
                finally:_ACTIVE.reset(active)
    finally:
        if scope is not None:scope.entries.clear();scope.all_deps.clear();scope.all_guards.clear();scope.retained=0;scope.invalidated='candidate-command-closed'
        _clear_governance(parser);entry['closed']=True;entry['state']['registration_pure_owner_v1']={'closed':True};_COMMAND_BINDING.reset(token)

def _guard_command_entry_for_exit(entry,previous_binding):
    if entry['closed'] or entry['execution']!=_execution_identity():raise ValueError('registration-command-exit-owner-conflict')
    if previous_binding is not None and previous_binding is not entry:raise ValueError('registration-command-exit-binding-conflict')
    if _ACTIVE.get() is not None:raise ValueError('registration-command-exit-active-scope')
    import verification_session as verification
    if verification.current() is not None or verification.owner() not in (None,entry['parser']):raise ValueError('registration-command-exit-foreign-parser')

def _policy_command_entry(region_module,verification):
    if verification.current() is not None or verification.owner() is not None:return None
    import execution_timing as timing
    state=timing._POLICY_COMMAND.get()
    if state is None:return None
    entry=state.get('registration_pure_owner_v1')
    if entry is None:
        entry={'state':state,'execution':_execution_identity(),'region':region_module,'parser':verification.Session(max_bytes=32*1024*1024,revision='registration-command-pinned-v1'),'registration':None,'closed':False,'closing':False,'failed':False}
        state['registration_pure_owner_v1']=entry;state['stack'].callback(_finish_command_entry,entry)
    if entry.get('closed'):raise ValueError('registration-command-closed-context')
    _guard_command_entry(entry)
    if entry['region'] is not region_module:
        error=ValueError('registration-command-region-conflict');_record_command_failure(entry,error)
        raise error
    return entry

@contextmanager
def pure_scope(region_module):
    """Read current evidence directly; no source graph or transitive audit replay."""
    import verification_session
    with verification_session.validation_scope(max_bytes=32*1024*1024,revision='current-frame-inputs-v1'):
        yield None


def code_token_difference(before,after):
    """Code-only evidence; never serialize token globals/default values."""
    def files(token):
        if not isinstance(token,tuple)or len(token)<2 or not isinstance(token[1],(tuple,list)):return {}
        return {item[0]:item[1]for item in token[1]if isinstance(item,(tuple,list))and len(item)==2 and isinstance(item[0],str)and isinstance(item[1],str)and len(item[1])==64}
    left=files(before);right=files(after)
    def changed(index):
        return not(isinstance(before,tuple)and isinstance(after,tuple)and len(before)>index and len(after)>index)or before[index]!=after[index]
    return {'kind':'registration-validation-code-graph-difference-v1','files_added':[{'path':p,'sha256':right[p]}for p in sorted(set(right)-set(left))],'files_removed':[{'path':p,'sha256':left[p]}for p in sorted(set(left)-set(right))],'files_changed':[{'path':p,'before_sha256':left[p],'after_sha256':right[p]}for p in sorted(set(left)&set(right))if left[p]!=right[p]],'runtime_signature_changed':changed(0),'decorator_signature_changed':changed(2),'function_defaults_signature_changed':changed(3),'path_defaults_signature_changed':changed(4),'token_values_disclosed':False}

def active_history_session():
    scope=_ACTIVE.get()
    return scope if scope is not None and not scope.suspended and hasattr(scope,'region_module') else None
