"""Quiescent stop/reload of the one installed Host and its original daemon.
No bundle/plist/config/queue changes; unknown commands are inspect-only.
"""
import argparse,os,plistlib,re,signal,sqlite3,subprocess,time
from pathlib import Path
from .common import *
from . import service
ROOT=service.PROJECT/'runtime/standalone-workshop-director'
TARGET='gui/501/'+service.LABEL
DEST=Path('/Users/feibing/Library/LaunchAgents')/(service.LABEL+'.plist')
# NSTask's reviewed CLT framework binary re-execs this exact bundled Python.
# Only this finite pair is admitted; never basename/contains/same-version matching.
CONFIGURED_FRAMEWORK_PYTHON=Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9')
FRAMEWORK_PYTHON_EXECUTABLE=CONFIGURED_FRAMEWORK_PYTHON.parent.parent/'Resources/Python.app/Contents/MacOS/Python'
def python_command_binding(configured,root,actual_args,actual_executable):
    if configured!=str(CONFIGURED_FRAMEWORK_PYTHON):return None
    allowed=(CONFIGURED_FRAMEWORK_PYTHON,FRAMEWORK_PYTHON_EXECUTABLE)
    if not all(p.is_file() and p.resolve()==p and not p.is_symlink() for p in allowed):return None
    suffix=['-m','workshop_director','--root',str(root),'serve']
    prefixes={str(p) for p in allowed};matches=[p for p in prefixes if actual_args==' '.join([p,*suffix])]
    if len(matches)!=1 or actual_executable not in prefixes:return None
    return {'kind':'reviewed-framework-python-process-binding-v1','configured_python':configured,'actual_executable':actual_executable,'actual_args':actual_args,'route':'configured-framework' if matches[0]==configured else 'same-framework-bundled-reexec','suffix':suffix}

def queue(root):return queue_file(Path(root)/'queue.sqlite3')
def queue_file(path):
    path=Path(path);need(path.is_file() and not path.is_symlink(),'lifecycle-original-queue-required')
    c=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    try:
        meta={r['key']:json.loads(r['value']) for r in c.execute('SELECT * FROM meta')}
        return {'plans':[dict(r) for r in c.execute('SELECT * FROM plans ORDER BY id')],'tasks':[dict(r) for r in c.execute('SELECT * FROM tasks ORDER BY id')],'owner':meta.get('resource_owner'),'daemon':meta.get('daemon')}
    finally:c.close()
def business(q):return {k:q[k] for k in ('plans','tasks','owner')}
def quiet(q):
    need(all(p['state'] in ('paused','cancelled') for p in q['plans']),'lifecycle-all-plans-must-be-paused');refs=[]
    for t in q['tasks']:
        need(t['state'] not in ('running','dispatching','unknown'),'lifecycle-child-running-or-unknown')
        if not t.get('active_attempt'):continue
        f=Path(t['active_attempt']);need(f.parent==ROOT/'attempts' and f.resolve()==f,'lifecycle-attempt-scope')
        request=ref(f/'request.json');x=read(f/'exit.json')
        need(x.get('kind')=='workshop-worker-exit-v1' and x.get('attempt_id')==f.name and x.get('request')==request,'lifecycle-original-natural-exit-required');refs.extend([request,ref(f/'exit.json')])
        for name in ('spawn.json','started.json'):
            p=f/name
            if p.exists():need(not same_process(read(p).get('process')),'lifecycle-original-worker-still-alive');refs.append(ref(p))
    return refs
def archive_bytes(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    syncdir(path.parent);return ref(path)

def backup(root,out):
    need(not out.exists(),'lifecycle-backup-exists');a=sqlite3.connect((root/'queue.sqlite3').as_uri()+'?mode=ro',uri=True);b=sqlite3.connect(out)
    try:a.backup(b);b.commit();need(b.execute('PRAGMA integrity_check').fetchone()[0]=='ok','lifecycle-backup-integrity')
    finally:a.close();b.close()
    with out.open('rb') as f:os.fsync(f.fileno())
    return ref(out)
def descendants(rows,pid):
    found=set();pending=[pid]
    while pending:
        children=[r['pid'] for r in rows if r['ppid'] in pending and r['pid'] not in found];found.update(children);pending=children
    return found
def terminal_zombies(rows,pid,q,*,root,boot_id):
    """Only kernel-terminal, exact naturally-exited original workers qualify."""
    children=descendants(rows,pid);proofs=[]
    for row in rows:
        if row['pid'] not in children or not re.fullmatch(r'Z[+<N>LsEX]*',row.get('stat','')):continue
        matches=[]
        for task in q['tasks']:
            if not task.get('active_attempt'):continue
            f=Path(task['active_attempt']);need(f.parent==root/'attempts' and f.resolve()==f,'lifecycle-attempt-scope')
            records=[read(f/n) for n in ('started.json','spawn.json') if (f/n).is_file()]
            if not any(v.get('process',{}).get('pid')==row['pid'] for v in records):continue
            process={'pid':row['pid'],'started':row.get('started'),'boot':boot_id};request=ref(f/'request.json');exit=read(f/'exit.json')
            need(task['state'] not in ('running','dispatching','unknown') and records and all(v.get('process')==process and v.get('attempt_id')==f.name for v in records),'lifecycle-zombie-worker-identity-unverified')
            need(exit.get('kind')=='workshop-worker-exit-v1' and exit.get('attempt_id')==f.name and exit.get('request')==request and isinstance(exit.get('returncode'),int) and not isinstance(exit.get('returncode'),bool) and timestamp(exit['exited_at']).utcoffset() is not None,'lifecycle-zombie-natural-exit-unverified')
            matches.append({'row':row,'process':process,'request':request,'exit':ref(f/'exit.json'),'records':[ref(f/n)for n in ('started.json','spawn.json')if(f/n).is_file()]})
        need(len(matches)==1,'lifecycle-zombie-original-worker-unverified');proofs.extend(matches)
    return proofs
class System:
    def run(self,argv):
        p=subprocess.run(argv,capture_output=True,text=True,timeout=30);return {'argv':argv,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    def print_service(self):return self.run(['/bin/launchctl','print',TARGET])
    def absent(self,s):return s['returncode']!=0 and 'Could not find service' in s['stdout']+s['stderr']
    def alive(self,p):return same_process(p)
    def rows(self):
        raw=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,pgid=,stat=,lstart='],text=True,timeout=5)
        rows=[]
        for line in raw.splitlines():
            if not line.strip():continue
            parts=line.split(None,4);need(len(parts)==5,'lifecycle-process-row-incomplete');rows.append({**dict(zip(('pid','ppid','pgid'),map(int,parts[:3]))),'stat':parts[3],'started':parts[4].strip()})
        need(len({r['pid']for r in rows})==len(rows),'lifecycle-process-row-duplicate');return rows
    def args(self,pid):return subprocess.check_output(['/bin/ps','-p',str(pid),'-o','command='],text=True,timeout=5).strip()
    def executable(self,pid):return subprocess.check_output(['/bin/ps','-p',str(pid),'-o','comm='],text=True,timeout=5).strip()
    def qualified_descendants(self,rows,pid,q=None):
        if not any(r['pid'] in descendants(rows,pid) and r.get('stat','').startswith('Z')for r in rows):return descendants(rows,pid),[]
        q=queue(ROOT)if q is None else q;quiet(q);proof=terminal_zombies(rows,pid,q,root=ROOT,boot_id=boot());return descendants(rows,pid)-{x['row']['pid']for x in proof},proof
    def no_descendants(self,p):
        remaining,proof=self.qualified_descendants(self.rows(),p['pid']);need(not remaining,'lifecycle-new-child-appeared')
    def term(self,p):
        need(self.alive(p),'lifecycle-original-daemon-identity-changed');self.no_descendants(p);os.kill(p['pid'],signal.SIGTERM);return {'pid':p['pid'],'signal':'SIGTERM','posted':True,'process':p}
    def wait_gone(self,p,seconds):
        deadline=time.monotonic()+seconds
        while self.alive(p) and time.monotonic()<deadline:time.sleep(.1)
        return not self.alive(p)
    def capture(self,root):
        need(os.getuid()==501 and root==ROOT and root.resolve()==root,'lifecycle-fixed-runtime-user-required')
        expected=service.host_plist(root);need(not DEST.is_symlink() and plistlib.loads(DEST.read_bytes())==expected,'lifecycle-installed-host-route-changed')
        q=queue(root);receipts=quiet(q);s=self.print_service();m=re.search(r'^\s*pid = (\d+)\s*$',s['stdout'],re.M);need(s['returncode']==0 and m,'lifecycle-host-not-running')
        host=identity(int(m[1]));daemon=(q['daemon'] or {}).get('process');need(host and self.alive(daemon),'lifecycle-live-original-daemon-required')
        status=read(root/'authorization-host.json');need(status.get('state')=='scheduler-child-started' and status.get('host_pid')==host['pid'] and status.get('child_pid')==daemon['pid'],'lifecycle-host-daemon-binding')
        hc=read(service.HOST_APP/'Contents/Resources/host-config.json');ha=self.args(host['pid']);da=self.args(daemon['pid']);python_binding=python_command_binding(hc['python'],root,da,self.executable(daemon['pid']));need(ha==' '.join(expected['ProgramArguments']) and python_binding is not None,'lifecycle-process-command-changed')
        rows=self.rows();host_children,terminal=self.qualified_descendants(rows,host['pid'],q);daemon_children=descendants(rows,daemon['pid'])-{x['row']['pid']for x in terminal};dr=next((r for r in rows if r['pid']==daemon['pid']),None);need(dr and dr['ppid']==host['pid'] and host_children=={daemon['pid']} and not daemon_children,'lifecycle-unexpected-process-descendants')
        need(identity(host['pid'])==host and identity(daemon['pid'])==daemon,'lifecycle-process-changed-during-capture')
        from .engine import load_active_config
        cfg,active,base=load_active_config(root);configs=[base,active]+([ref(root/'active_config.json')] if (root/'active_config.json').exists() else [])
        return {'host':host,'daemon':daemon,'host_args':ha,'daemon_args':da,'daemon_python_binding':python_binding,'process_scope':[r for r in rows if r['pid'] in (host['pid'],daemon['pid'])],'terminal_zombies':terminal,'business':business(q),'exit_refs':receipts,'configs':configs,'installed_plist':ref(DEST),'launchctl':s}
    def unchanged(self,root,v):
        need(business(queue(root))==v['business'],'lifecycle-original-queue-changed');quiet(queue(root))
        for r in v['configs']:need(ref(Path(r['path']))==r,'lifecycle-original-config-changed')
        need(ref(DEST)==v['installed_plist'],'lifecycle-installed-plist-changed')
def one_shot(folder,name,action,description):
    p=folder/(name+'-intent.json');need(not p.exists(),'lifecycle-existing-intent-inspect-only');immutable(p,{'kind':'service-lifecycle-one-shot-v1','target':TARGET,'action':description,'at':now()})
    try:out=action()
    except BaseException as e:
        immutable(folder/(name+'-unknown.json'),{'error':type(e).__name__,'at':now()});raise
    immutable(folder/(name+'-result.json'),out);return out
def prepare(root,out,action,ops=None):
    root=Path(root);out=Path(out);ops=ops or System();need(action in ('stop','reload'),'lifecycle-action');need(root==ROOT and out.is_absolute() and out.resolve()==out and out.parent==root/'service-lifecycle' and not out.exists(),'lifecycle-new-evidence-directory-required')
    with lock(root/'service-lifecycle.lock',False),lock(root/'scheduler.lock',False):
        out.parent.mkdir(parents=True,exist_ok=True)
        for prior in out.parent.iterdir():
            if not prior.is_dir():continue
            need((prior/'completion.json').is_file(),'lifecycle-prior-operation-unresolved-no-new-ID');done=read(prior/'completion.json');old=ticket(done['ticket']);need(done.get('kind')=='host-daemon-lifecycle-completed-v1' and Path(done['ticket']['path'])==prior/'ticket.json' and terminal(old,done['status']) and not ops.alive(old['before']['host']) and not ops.alive(old['before']['daemon']),'lifecycle-prior-terminal-proof-invalid')
        out.mkdir()
        v=ops.capture(root);saved=backup(root,out/'queue.before.sqlite3');need(business(queue_file(Path(saved['path'])))==v['business'],'lifecycle-backup-queue-changed')
        # Backup API yields a transaction-consistent archive; it never changes the live DB.
        old=DEST.read_bytes();plist_archive=archive_bytes(out/'installed.plist',old);configs=[]
        for r in v['configs']:
            need(ref(Path(r['path']))==r,'lifecycle-config-changed-during-archive');path=out/'configs'/(r['sha256']+'.json')
            if not path.exists():archive_bytes(path,Path(r['path']).read_bytes())
            need(ref(path)['sha256']==r['sha256'],'lifecycle-config-archive-mismatch');configs.append(ref(path))
        return immutable(out/'ticket.json',{'kind':'installed-host-daemon-lifecycle-v1','root':str(root),'target':TARGET,'action':action,'before':v,'queue_backup':saved,'config_archives':configs,'plist_archive':plist_archive,'at':now()})
def ticket(reference):
    v=pinned(reference);need(v.get('kind')=='installed-host-daemon-lifecycle-v1' and v.get('target')==TARGET and v.get('root')==str(ROOT) and v.get('action') in ('stop','reload'),'lifecycle-ticket-scope');need(Path(reference['path']).name=='ticket.json' and Path(reference['path']).parent.parent==ROOT/'service-lifecycle' and Path(reference['path']).resolve()==Path(reference['path']),'lifecycle-ticket-path');return v
def inspect(reference,ops=None):
    v=ticket(reference);ops=ops or System();s=ops.print_service();result={'kind':'host-daemon-lifecycle-readonly-status-v1','service':s,'host_alive':ops.alive(v['before']['host']),'daemon_alive':ops.alive(v['before']['daemon']),'queue_business_preserved':business(queue(ROOT))==v['before']['business'],'receipts':[ref(p) for p in sorted(Path(reference['path']).parent.glob('*-result.json'))],'new_host_daemon_healthy':False}
    if not ops.absent(s):
        try:
            current=ops.capture(ROOT);need(current['business']==v['before']['business'] and current['host']!=v['before']['host'] and current['daemon']!=v['before']['daemon'],'lifecycle-new-original-process-required');result.update(new_host_daemon_healthy=True,new_host=current['host'],new_daemon=current['daemon'])
        except Exception as error:result['new_health_pending']=str(error)
    return result

def _apply(reference,execute=False,ops=None):
    need(execute,'lifecycle-explicit-execute-required');v=ticket(reference);ops=ops or System();root=Path(v['root']);folder=Path(reference['path']).parent;before=v['before'];need(not (folder/'bootout-intent.json').exists(),'lifecycle-existing-intent-inspect-only')
    with lock(root/'scheduler.lock',False):
        current=ops.capture(root);need(all(current[k]==before[k] for k in ('host','daemon','host_args','daemon_args','business','configs','installed_plist')),'lifecycle-original-identity-or-queue-changed');ops.unchanged(root,before)
        argv=['/bin/launchctl','bootout',TARGET];r=one_shot(folder,'bootout',lambda:ops.run(argv),argv);need(r['returncode']==0,'lifecycle-bootout-failed-inspect-only')
    # Do not hold scheduler.lock while awaiting daemon exit: a daemon already
    # waiting for this lock must be able to finish its no-dispatch paused tick.
    host_gone=ops.wait_gone(before['host'],5);service_after=ops.print_service();need(host_gone and ops.absent(service_after),'lifecycle-host-exit-not-proven')
    if not ops.wait_gone(before['daemon'],2):
        ops.unchanged(root,before);ops.no_descendants(before['daemon']);r=one_shot(folder,'daemon-term',lambda:ops.term(before['daemon']),{'signal':'SIGTERM','original_process':before['daemon']});need(r.get('posted') is True,'lifecycle-daemon-term-unknown')
    need(ops.wait_gone(before['daemon'],20),'lifecycle-daemon-exit-not-proven');ops.unchanged(root,before)
    immutable(folder/'original-processes-exited.json',{'host':before['host'],'daemon':before['daemon'],'host_alive':False,'daemon_alive':False,'service':service_after,'at':now()})
    if v['action']=='reload':
        argv=['/bin/launchctl','bootstrap','gui/501',str(DEST)];r=one_shot(folder,'bootstrap',lambda:ops.run(argv),argv);need(r['returncode']==0,'lifecycle-bootstrap-failed-inspect-only')
    # A successful bootstrap is not a permission probe/health result. Inspect
    # reports pending until the new signed Host and its actual daemon are bound.
    status=inspect(reference,ops)
    if terminal(v,status):complete(reference,status)
    return status
def terminal(v,status):
    return status['queue_business_preserved'] and not status['host_alive'] and not status['daemon_alive'] and (status['new_host_daemon_healthy'] if v['action']=='reload' else System().absent(status['service']))
def complete(reference,status):
    return immutable(Path(reference['path']).parent/'completion.json',{'kind':'host-daemon-lifecycle-completed-v1','ticket':reference,'status':status,'at':now()})
def apply(reference,execute=False,ops=None):
    with lock(ROOT/'service-lifecycle.lock',False):return _apply(reference,execute,ops)
def finalize(reference,ops=None):
    with lock(ROOT/'service-lifecycle.lock',False):
        v=ticket(reference);status=inspect(reference,ops);need(terminal(v,status),'lifecycle-terminal-proof-pending');return complete(reference,status)
def main():
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='verb',required=True);a=s.add_parser('prepare');a.add_argument('--root',required=True,type=Path);a.add_argument('--out',required=True,type=Path);a.add_argument('--action',choices=('stop','reload'),required=True)
    for verb in ('apply','inspect','finalize'):
        a=s.add_parser(verb);a.add_argument('--ticket',required=True);a.add_argument('--ticket-sha256',required=True)
        if verb=='apply':a.add_argument('--execute',action='store_true')
    a=p.parse_args();out=prepare(a.root,a.out,a.action) if a.verb=='prepare' else globals()[a.verb]({'path':a.ticket,'sha256':a.ticket_sha256},**({'execute':a.execute} if a.verb=='apply' else {}));print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
