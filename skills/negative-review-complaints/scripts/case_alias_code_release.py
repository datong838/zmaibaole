"""Completed v3 proof release bytes. Never imports or executes archived source."""
import functools,hashlib,json,os,tempfile
from pathlib import Path
from contextvars import ContextVar
RELEASES=Path(__file__).resolve().parents[3]/'runtime/negative-review-complaints/.alias-code-releases'
_HISTORY=ContextVar('alias_completed_release_only',default=None)
KIND='reviewed-alias-v3-code-bytes-v1'
def need(value,reason):
    if not value:raise ValueError(reason)
def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def strict(path):
    p=Path(path);need(p.is_absolute() and p==p.resolve() and not any(q.is_symlink() for q in (p,*p.parents)),'alias-release-canonical-path');return p
def reference(path):
    p=strict(path);return {'path':str(p),'sha256':digest(p.read_bytes())}
def publish(path,raw):
    path=strict(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():need(path.read_bytes()==raw,'alias-release-immutable-conflict')
    else:
        fd,tmp=tempfile.mkstemp(prefix='.seal-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            try:os.link(tmp,path)
            except FileExistsError:need(path.read_bytes()==raw,'alias-release-immutable-conflict')
        finally:os.unlink(tmp)
        fd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
    return reference(path)
def graph_id(graph):
    need(type(graph) is dict and 1<=len(graph)<=128,'alias-release-graph-shape')
    need(all(type(k) is str and type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v) for k,v in graph.items()),'alias-release-graph-shape')
    return digest(encoded(graph))
def seal(graph):
    """Only prepare calls this after obtaining the installed reviewed current graph."""
    folder=strict(RELEASES)/graph_id(graph);objects={}
    for logical,sha in sorted(graph.items()):
        source=strict(logical);raw=source.read_bytes();need(digest(raw)==sha,'alias-release-current-source-changed')
        objects[logical]=publish(folder/'objects'/(sha+'.source'),raw)
    # Re-read every source before sealing the immutable graph descriptor.
    need(all(reference(p)['sha256']==sha for p,sha in graph.items()),'alias-release-source-raced')
    return publish(folder/'release.json',encoded({'kind':KIND,'code':graph,'objects':objects}))
def check(m):
    graph=m['code'];folder=strict(RELEASES)/graph_id(graph);ref=m['code_release']
    need(type(ref) is dict and set(ref)=={'path','sha256'} and ref==reference(folder/'release.json'),'alias-release-ref-changed')
    value=json.loads((folder/'release.json').read_bytes());need(set(value)=={'kind','code','objects'} and value['kind']==KIND and value['code']==graph and set(value['objects'])==set(graph),'alias-release-graph-changed')
    for logical,sha in graph.items():
        need(value['objects'][logical]==reference(folder/'objects'/(sha+'.source')) and value['objects'][logical]['sha256']==sha,'alias-release-object-changed')
def history_active():return _HISTORY.get() is not None
def completed(m,base,document):
    bound=_HISTORY.get()
    if bound is None or 'code_release' not in m:return False
    if reference(base/'manifest.json')!=bound[0]:return False
    need(document(bound[0])==m,'alias-release-manifest-changed')
    # Canonical manifest and operation identity are also checked by original v3.
    path=base/'operation.json'
    if not path.is_file():return False
    operation=reference(path)
    need(operation==bound[1],'alias-release-original-operation-changed')
    state=document(operation)
    if state.get('state')!='complete':return False
    need(state.get('kind')=='known-public-complaint-case-operation-v3' and state.get('submission_enabled') is False and state.get('send_enabled') is False and state.get('manifest')==reference(base/'manifest.json'),'alias-release-completed-operation-required')
    check(m);return True

def pure_entry(name,function,resolve):
    @functools.wraps(function)
    def wrapped(*args,**kwargs):
        # Resolve one exact complete operation before entering the pure scope.
        # Nested unrelated manifests do not inherit a historical capability.
        mark=_HISTORY.set(resolve(name,args[0]))
        try:return function(*args,**kwargs)
        finally:_HISTORY.reset(mark)
    return wrapped
