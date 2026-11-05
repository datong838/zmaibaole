#!/usr/bin/env python3
"""Fixed-project macOS LaunchAgent for the existing loopback DOM bridge only."""
import argparse,fcntl,hashlib,json,os,plistlib,re,subprocess,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/Users/feibing/work/projects/zmaibaole')
HOME=Path.home()
PYTHON=Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python')
SCRIPT=ROOT/'skills/chrome-dom-export/scripts/bridge.py'
SCRIPT_SHA='dd89f7603b918613b33aaaa68d179460d5f2d2ef49a52c66fc91349e4d622bb3'
LABEL='local.zmaibaole.chrome-dom-bridge'
def need(ok,code):
 if not ok:raise ValueError(code)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def runtime():return ROOT/'runtime/chrome-dom-bridge-service'
def state_path():return runtime()/'install-state.json'
def destination():return HOME/'Library/LaunchAgents'/(LABEL+'.plist')
def domain():return 'gui/'+str(os.getuid())
def target():return domain()+'/'+LABEL
def clean_path(p):
 p=Path(p);need(p.is_absolute() and p.resolve()==p and not any(v.is_symlink() for v in (p,*p.parents)),'canonical-nonsymlink-path-required');return p
def expected():
 return {'Label':LABEL,'ProgramArguments':[str(PYTHON),str(SCRIPT),'serve'],'WorkingDirectory':str(ROOT),'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':10,'ProcessType':'Background','StandardOutPath':str(runtime()/'stdout.log'),'StandardErrorPath':'/dev/null','Umask':0o077}
def plist_bytes():return plistlib.dumps(expected(),sort_keys=True)
def validate(p,digest=None):
 p=clean_path(p);raw=p.read_bytes();need(digest is None or hashlib.sha256(raw).hexdigest()==digest,'reviewed-plist-sha-required');need(plistlib.loads(raw)==expected() and raw==plist_bytes(),'fixed-reviewed-plist-required');return raw
def fsync_parent(path):
 fd=os.open(str(Path(path).parent),os.O_RDONLY)
 try:os.fsync(fd)
 finally:os.close(fd)
def publish(path,raw):
 path=clean_path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix='.publish-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o600);os.link(name,path);fsync_parent(path)
 finally:
  if os.path.exists(name):os.unlink(name)
def atomic(path,value):
 path=clean_path(path);path.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(prefix='.state-',dir=str(path.parent))
 try:
  with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
  os.chmod(name,0o600);os.replace(name,path);fsync_parent(path)
 finally:
  if os.path.exists(name):os.unlink(name)
def source_guard():
 need(SCRIPT.is_file() and PYTHON.is_file(),'fixed-source-or-python-missing');need(sha(SCRIPT)==SCRIPT_SHA,'reviewed-bridge-source-changed')
def run(argv):
 # All callers below construct fixed commands; no shell, caller-supplied argv or secrets.
 v=subprocess.run(argv,capture_output=True,text=True,timeout=15);return {'returncode':v.returncode,'stdout':v.stdout,'stderr':v.stderr}
def generate(out):
 out=clean_path(out);need(not out.exists(),'plist-already-exists');need(ROOT in out.parents and ('work' in out.relative_to(ROOT).parts or 'runtime' in out.relative_to(ROOT).parts),'project-output-required');publish(out,plist_bytes());return {'path':str(out),'sha256':sha(out),'installed':False}
def parse_print(text):
 program=re.findall(r'^\s*program = (.+)$',text,re.M);args=re.search(r'^\s*arguments = \{\s*\n(.*?)^\s*\}',text,re.M|re.S);pid=re.findall(r'^\s*pid = ([1-9][0-9]*)\s*$',text,re.M);path=re.findall(r'^\s*path = (.+)$',text,re.M)
 need(program==[str(PYTHON)] and args is not None and path==[str(destination())],'launchd-service-identity-mismatch');arguments=[v.strip() for v in args[1].splitlines() if v.strip()];need(arguments==expected()['ProgramArguments'],'launchd-service-arguments-mismatch');need(len(pid)<=1,'launchd-pid-ambiguous');return {'program':program[0],'arguments':arguments,'plist_path':path[0],'pid':int(pid[0]) if pid else None,'print_sha256':hashlib.sha256(text.encode()).hexdigest()}
def observe():
 source_guard()
 need(sys.platform=='darwin','macos-only');loaded=run(['/bin/launchctl','print',target()]);port=run(['/usr/sbin/lsof','-nP','-iTCP:17341','-sTCP:LISTEN','-Fpn']);need(port['returncode'] in (0,1),'listener-observation-failed');lines=port['stdout'].splitlines();pids=sorted(set(int(x[1:]) for x in lines if re.fullmatch('p[1-9][0-9]*',x)));addresses=[x[1:] for x in lines if x.startswith('n')];need(all(v=='127.0.0.1:17341' for v in addresses),'nonloopback-listener-stop')
 if loaded['returncode']:
  need('Could not find service' in loaded['stderr'] and LABEL in loaded['stderr'],'launchctl-status-unknown');return {'state':'absent','listener_pids':pids,'label':LABEL,'launchctl_returncode':loaded['returncode']}
 clean_path(destination());validate(destination());info=parse_print(loaded['stdout']);pid=info['pid'];state='loaded-not-running'
 if pid:
  ps=run(['/bin/ps','-p',str(pid),'-o','command=']);need(ps['returncode']==0 and ps['stdout'].strip()==' '.join(expected()['ProgramArguments']),'launchd-process-command-mismatch');started=run(['/bin/ps','-p',str(pid),'-o','lstart=']);need(started['returncode']==0 and 0<len(started['stdout'].strip())<100,'process-start-identity-unavailable');info['process_started_at']=started['stdout'].strip();cwd=run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn']);need(cwd['returncode']==0 and 'n'+str(ROOT)+'\n' in cwd['stdout'],'launchd-process-cwd-mismatch');need(pids in ([],[pid]),'foreign-listener-stop');state='healthy' if pids==[pid] else 'starting-no-listener'
 if not pid:need(not pids,'foreign-listener-stop')
 return {'state':state,'label':LABEL,'target':target(),'listener_pids':pids,'launchctl':info,'loopback':'127.0.0.1:17341','plist_sha256':sha(destination())}
def health():
 source_guard();return observe()
def install(plist,digest,confirm=False):
 need(confirm,'explicit-install-confirmation-required');raw=validate(plist,digest);source_guard();clean_path(runtime());need(not (runtime()/'stdout.log').is_symlink(),'service-log-symlink-refused');runtime().mkdir(parents=True,exist_ok=True);fsync_parent(runtime())
 with (runtime()/'lifecycle.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if state_path().exists():
   previous=json.loads(state_path().read_bytes());need(previous.get('state')=='bootstrap-returned-awaiting-health' and previous.get('plist_sha256')==digest,'existing-install-intent-no-replay');return {'reused':True,'health':health()}
  before=observe();need(before['state']=='absent' and before['listener_pids']==[],'service-or-foreign-listener-present');need(not destination().exists(),'launchagent-plist-already-present');destination().parent.mkdir(parents=True,exist_ok=True);fsync_parent(destination().parent);publish(destination(),raw)
  state={'kind':'fixed-bridge-launchagent-install-v1','label':LABEL,'state':'unknown','intent_at':now(),'plist_sha256':digest,'destination':str(destination()),'argv':['/bin/launchctl','bootstrap',domain(),str(destination())],'before':before};atomic(state_path(),state)
  result=run(state['argv']);state['launchctl_returncode']=result['returncode'];state['reply_sha256']=hashlib.sha256((result['stdout']+result['stderr']).encode()).hexdigest();need(result['returncode']==0,'bootstrap-unknown-no-replay');state.update(state='bootstrap-returned-awaiting-health',returned_at=now());atomic(state_path(),state);return state
def uninstall(confirm=False):
 need(confirm,'explicit-uninstall-confirmation-required');validate(destination());runtime().mkdir(parents=True,exist_ok=True);fsync_parent(runtime());p=runtime()/'uninstall-state.json'
 with (runtime()/'lifecycle.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);need(not p.exists(),'existing-uninstall-intent-no-replay');before=observe();need(before['state'] in ('healthy','starting-no-listener','loaded-not-running'),'service-not-managed-loaded');state={'kind':'fixed-bridge-launchagent-uninstall-v1','state':'unknown','intent_at':now(),'before':before,'argv':['/bin/launchctl','bootout',target()]};atomic(p,state);reply=run(state['argv']);need(reply['returncode']==0,'bootout-unknown-no-replay');validate(destination());destination().unlink();fsync_parent(destination());state.update(state='bootout-returned',returned_at=now());atomic(p,state);return state
def reload_service(ticket,confirm=False):
 """Quiescent caller must hold the global business resource lease.
 One durable kickstart at most. Unknown/returned tickets only observe effect;
 never replay an HTTP/DOM request or touch Chrome/config/plist/Host.
 """
 need(confirm,'explicit-reload-confirmation-required');need(type(ticket) is str and re.fullmatch('[0-9a-f]{64}',ticket) is not None,'fixed-reload-ticket-required');source_guard();clean_path(runtime());runtime().mkdir(parents=True,exist_ok=True);path=runtime()/('reload-'+ticket+'.json');argv=['/bin/launchctl','kickstart','-k',target()]
 with (runtime()/'lifecycle.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if path.exists():
   state=json.loads(path.read_bytes());need(state.get('kind')=='fixed-bridge-ticket-reload-v1' and state.get('ticket')==ticket and state.get('label')==LABEL and state.get('bridge_sha256')==SCRIPT_SHA and state.get('argv')==argv and state.get('state') in ('unknown','kickstart-returned-awaiting-health','complete'),'original-reload-ticket-required')
   before=state['before'];need(before.get('state')=='healthy' and before.get('label')==LABEL and before.get('target')==target() and before.get('plist_sha256')==hashlib.sha256(plist_bytes()).hexdigest() and type(before.get('launchctl',{}).get('pid')) is int and bool(before['launchctl'].get('process_started_at')),'original-reload-before-required')
  else:
   for other in runtime().glob('reload-*.json'):
    need(json.loads(other.read_bytes()).get('state')=='complete','other-reload-unknown-no-new-ticket')
   before=observe();need(before.get('state')=='healthy','reload-managed-healthy-required');state={'kind':'fixed-bridge-ticket-reload-v1','ticket':ticket,'label':LABEL,'bridge_sha256':SCRIPT_SHA,'state':'unknown','intent_at':now(),'argv':argv,'before':before};atomic(path,state)
   reply=run(argv);state.update(launchctl_returncode=reply['returncode'],reply_sha256=hashlib.sha256((reply['stdout']+reply['stderr']).encode()).hexdigest(),returned_at=now());atomic(path,state);need(reply['returncode']==0,'kickstart-unknown-no-replay');state['state']='kickstart-returned-awaiting-health';atomic(path,state)
  after=observe();old=state['before']['launchctl'];new=after.get('launchctl',{});changed=(new.get('pid'),new.get('process_started_at'))!=(old['pid'],old['process_started_at'])
  if state['state']=='complete':need(after.get('state')=='healthy' and changed and new.get('pid')==state['after']['launchctl']['pid'] and new.get('process_started_at')==state['after']['launchctl']['process_started_at'],'completed-reload-effect-changed');return {'state':'complete','ticket':ticket,'receipt':{'path':str(path),'sha256':sha(path)},'health':after,'input_replayed':False}
  if after.get('state')=='healthy' and changed:
   state.update(state='complete',after=after,completed_at=now());atomic(path,state);return {'state':'complete','ticket':ticket,'receipt':{'path':str(path),'sha256':sha(path)},'health':after,'input_replayed':False}
  return {'state':'pending-no-replay','ticket':ticket,'intent':{'path':str(path),'sha256':sha(path)},'health':after,'input_replayed':False}
def main():
 a=argparse.ArgumentParser(description=__doc__);s=a.add_subparsers(dest='command',required=True);p=s.add_parser('generate');p.add_argument('--out',type=Path,required=True);p=s.add_parser('install');p.add_argument('--plist',type=Path,required=True);p.add_argument('--expected-plist-sha256',required=True);p.add_argument('--confirm-install',action='store_true');s.add_parser('health');p=s.add_parser('uninstall');p.add_argument('--confirm-uninstall',action='store_true');p=s.add_parser('reload');p.add_argument('--ticket',required=True);p.add_argument('--confirm-reload',action='store_true');v=a.parse_args()
 try:
  result=reload_service(v.ticket,v.confirm_reload) if v.command=='reload' else generate(v.out) if v.command=='generate' else install(v.plist,v.expected_plist_sha256,v.confirm_install) if v.command=='install' else uninstall(v.confirm_uninstall) if v.command=='uninstall' else health();print(json.dumps({'ok':True,'result':result},ensure_ascii=False))
 except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__,'error':str(e) if isinstance(e,ValueError) else 'service-operation-stopped-no-replay'},ensure_ascii=False));raise SystemExit(1)
if __name__=='__main__':main()
