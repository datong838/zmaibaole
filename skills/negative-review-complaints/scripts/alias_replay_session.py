"""Bounded in-process pure replay memo. No live guard/result persists here.
Every read dependency and directory inventory is checked on hits and at exit.
Each independent public call gets a new transaction; exceptions never publish.
"""
import copy,functools,hashlib,json,os,sys
from pathlib import Path
from contextvars import ContextVar
from contextlib import contextmanager
ACTIVE=ContextVar('alias_pure_replay',default=None)
LAST=ContextVar('alias_pure_replay_last_stats',default=None)

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def inventory(path):
    return tuple(sorted((p.name,p.is_symlink(),p.is_dir()) for p in Path(path).iterdir()))
def audit(event,args):
    session=ACTIVE.get()
    if session is None or session.paused:return
    if event in ('subprocess.Popen','os.system','socket.connect','socket.bind','os.remove','os.rename','os.rmdir','os.mkdir','os.link','os.symlink','os.chdir','os.chmod','os.truncate'):raise ValueError('alias-replay-not-pure')
    if event=='open':
        path,mode,flags=args
        if not isinstance(path,(str,bytes,os.PathLike)):raise ValueError('alias-replay-untracked-fd')
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):raise ValueError('alias-replay-write-forbidden')
        session.record(path)
    elif event in ('os.scandir','os.listdir'):session.record_directory(args[0])
sys.addaudithook(audit)

class Session:
    def __init__(self,token,*,max_bytes=32*1024*1024):
        self.token_fn=token;self.token=token();self.max_bytes=max_bytes;self.retained=0;self.entries={};self.inflight=set();self.frames=[];self.files={};self.dirs={};self.paused=False;self.live_lease=None
        self.stats={'hits':0,'misses':0,'bypasses':0,'computations':{},'hash_checks':0,'directory_checks':0,'retained_bytes':0,'semantic_lease_reads':0}
    @contextmanager
    def pause(self):
        old=self.paused;self.paused=True
        try:yield
        finally:self.paused=old
    def _read_current_lease(self,readonly_reconcile):
        # One fixed policy, not a caller-supplied path or arbitrary projection.
        # Ordinary readers of this same file are NOT exempt from byte auditing.
        import case_alias_cli as policy
        path=policy.canonical(policy.LEASE)
        current=json.loads(path.read_bytes())
        if policy.canonical(policy.LEASE)!=path:raise ValueError('alias-replay-live-lease-changed')
        projection={'binding':policy.lease_binding(current,readonly_reconcile=readonly_reconcile),'phase':current['phase']}
        self.stats['semantic_lease_reads']+=1
        return current,(str(path),str(path.resolve()),path.is_symlink()),projection
    def read_current_lease(self,*,readonly_reconcile=False):
        if ACTIVE.get() is not self or type(readonly_reconcile) is not bool:raise ValueError('alias-replay-live-lease-scope-required')
        # Only this explicit read is semantic. No global path-based exclusion:
        # an explicit SHA ref/open elsewhere still records full bytes normally.
        with self.pause():current,path,projection=self._read_current_lease(readonly_reconcile)
        dependency=(path,readonly_reconcile,copy.deepcopy(projection))
        if self.live_lease is not None and self.live_lease!=dependency:raise ValueError('alias-replay-live-lease-changed')
        self.live_lease=dependency
        return current
    def check_current_lease(self):
        if self.live_lease is None:return
        path,readonly_reconcile,projection=self.live_lease
        with self.pause():_,fresh_path,fresh_projection=self._read_current_lease(readonly_reconcile)
        if fresh_path!=path or fresh_projection!=projection:raise ValueError('alias-replay-live-lease-changed')
    def merge(self,files,dirs):
        for values,target in ((files,self.files),(dirs,self.dirs)):
            for p,h in values.items():
                if p in target and target[p]!=h:raise ValueError('alias-replay-dependency-changed')
                if p not in target and len(self.files)+len(self.dirs)>=10000:raise ValueError('alias-replay-dependency-cap')
                target[p]=h
        for frame in self.frames:frame[0].update(files);frame[1].update(dirs)
    def record(self,path):
        with self.pause():
            p=os.path.abspath(os.fsdecode(path))
            if not Path(p).is_file():return # retain original missing-file semantics
            h=(digest(p),str(Path(p).resolve()),Path(p).is_symlink());self.stats['hash_checks']+=1
        self.merge({p:h},{})
    def record_directory(self,path):
        if not isinstance(path,(str,bytes,os.PathLike)):raise ValueError('alias-replay-untracked-directory')
        with self.pause():
            p=os.path.abspath(os.fsdecode(path));values=(inventory(p),str(Path(p).resolve()),Path(p).is_symlink());self.stats['directory_checks']+=1
        self.merge({}, {p:values})
    def check(self,files,dirs):
        with self.pause():
            if self.token_fn()!=self.token:raise ValueError('alias-replay-code-changed')
            for p,h in files.items():
                self.stats['hash_checks']+=1
                if (digest(p),str(Path(p).resolve()),Path(p).is_symlink())!=h:raise ValueError('alias-replay-dependency-changed')
            for p,h in dirs.items():
                self.stats['directory_checks']+=1
                if (inventory(p),str(Path(p).resolve()),Path(p).is_symlink())!=h:raise ValueError('alias-replay-directory-changed')
            # Last check in hit/compute/terminal validation: current permissions
            # are freshly sampled after potentially lengthy immutable byte reads.
            self.check_current_lease()
    def node(self,name,key,compute,*,cacheable=True,target=None,ancestors=()):
        key=(name,key)
        if target is not None and target in ancestors:raise ValueError('alias-replay-ancestor-cycle')
        for frame in self.frames:
            if target is not None:frame[2].add(target)
        if key in self.inflight:raise ValueError('alias-replay-cycle')
        if cacheable and key in self.entries:
            result,files,dirs,lineage=self.entries[key]
            if set(ancestors).intersection(lineage):raise ValueError('alias-replay-cached-ancestor-cycle')
            self.check(files,dirs);self.merge(files,dirs)
            for frame in self.frames:frame[2].update(lineage)
            self.stats['hits']+=1;return copy.deepcopy(result)
        self.stats['misses']+=1;self.stats['computations'][name]=self.stats['computations'].get(name,0)+1;frame=({},{},set() if target is None else {target});self.frames.append(frame);self.inflight.add(key)
        try:
            result=compute();self.check(frame[0],frame[1]);stored=copy.deepcopy(result);weight=8*len(canonical(stored).encode())+len(repr(key).encode())+sum(len(repr(x))+64 for x in frame[2])+sum(len(p)+128 for p in frame[0])+sum(len(p)+len(repr(v))+128 for p,v in frame[1].items())+512
            if cacheable and self.retained+weight<=self.max_bytes:
                self.entries[key]=(stored,dict(frame[0]),dict(frame[1]),frozenset(frame[2]));self.retained+=weight;self.stats['retained_bytes']=self.retained
            else:self.stats['bypasses']+=1
            return result
        finally:self.frames.pop();self.inflight.remove(key)
    def finish(self):self.check(self.files,self.dirs)

@contextmanager
def transaction(token):
    if ACTIVE.get() is not None:
        yield ACTIVE.get();return
    session=Session(token);mark=ACTIVE.set(session)
    try:yield session;session.finish()
    finally:LAST.set(copy.deepcopy(session.stats));ACTIVE.reset(mark)

def memo(name,token,authorize):
    """authorize(args,kwargs) runs BEFORE hits (cycle/source canonical checks).
    Return immutable key and cacheable flag. Stack is validated, never key noise.
    """
    def decorate(fn):
        @functools.wraps(fn)
        def wrapped(*args,**kwargs):
            with transaction(token) as session:
                key,cacheable,target,ancestors=authorize(args,kwargs)
                original=canonical((args,{k:v for k,v in kwargs.items() if k!='stack'}))
                def compute():
                    result=fn(*args,**kwargs)
                    if canonical((args,{k:v for k,v in kwargs.items() if k!='stack'}))!=original:raise ValueError('alias-replay-input-mutated')
                    return result
                return session.node(name,key,compute,cacheable=cacheable,target=target,ancestors=ancestors)
        return wrapped
    return decorate
