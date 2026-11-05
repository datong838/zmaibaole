import contextlib,fcntl,hashlib,json,os,subprocess,tempfile,time,uuid,re
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
ZONE=ZoneInfo('Asia/Shanghai')
FLOWS=('daily-comment-stats','negative-review-complaints','violation-notifier')
def need(ok,why):
    if not ok:raise ValueError(why)
def now():return datetime.now(timezone.utc).isoformat()
def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def digest(v):return hashlib.sha256(encode(v)).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def ref(p):p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def pinned(r):
    p=Path(r['path']);need(p.is_absolute() and p.is_file() and not p.is_symlink(),'pinned-file-required');raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==r['sha256'],'pinned-file-changed');return json.loads(raw)
def atomic(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(encode(v));f.flush();os.fsync(f.fileno())
        os.replace(tmp,p);syncdir(p.parent)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
def syncdir(p):
    fd=os.open(p,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def immutable(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);raw=encode(v)
    if p.exists():need(p.read_bytes()==raw,'immutable-conflict');return ref(p)
    fd,tmp=tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.link(tmp,p)
        except FileExistsError:need(p.read_bytes()==raw,'immutable-conflict')
        syncdir(p.parent)
    finally:os.unlink(tmp)
    return ref(p)
@contextlib.contextmanager
def lock(path,blocking=True):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('a') as f:
        fcntl.flock(f,fcntl.LOCK_EX|(0 if blocking else fcntl.LOCK_NB));yield f

def boot():
    p=Path('/proc/sys/kernel/random/boot_id')
    if p.exists():return p.read_text().strip()
    raw=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],text=True,timeout=5).strip()
    need(re.fullmatch(r'[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}',raw) is not None,'boot-session-uuid-unavailable')
    value=uuid.UUID(raw);need(value.int!=0,'boot-session-uuid-unavailable')
    return 'darwin-kern-bootsessionuuid:'+str(value)
def identity(pid):
    # Public local process metadata only; never inspect an environment/token.
    try:
        value=subprocess.check_output(['/bin/ps','-p',str(pid),'-o','lstart=','-o','stat='],text=True,stderr=subprocess.DEVNULL).strip()
        if value:
            started,status=value.rsplit(None,1)
            if status.startswith('Z'):return None # exited, awaiting parent reap
            return {'pid':pid,'started':started.strip(),'boot':boot()}
    except (OSError,subprocess.CalledProcessError):pass
    return None
def same_process(value):return bool(value and identity(value['pid'])==value)
def timestamp(v):
    d=datetime.fromisoformat(v.replace('Z','+00:00'));need(d.utcoffset() is not None,'timezone-required');return d
