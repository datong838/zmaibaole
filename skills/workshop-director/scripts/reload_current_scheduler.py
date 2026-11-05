"""Reload only the actual idle scheduler; no historical lifecycle scan."""
import fcntl,json,os,signal,sqlite3,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'packages/workshop-director'))
from workshop_director.common import identity,same_process
RUNTIME=ROOT/'runtime/standalone-workshop-director'
CURRENT=RUNTIME/'current-service-operation.json'
def save(value):
 p=CURRENT.with_suffix('.tmp')
 with p.open('w')as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
 p.replace(CURRENT)
def reload():
 with (RUNTIME/'service-lifecycle.lock').open('a')as maintenance:
  fcntl.flock(maintenance,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if CURRENT.exists():raise ValueError('inspect-current-service-operation-before-repeating')
  with (RUNTIME/'scheduler.lock').open('a')as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   with sqlite3.connect('file:'+str(RUNTIME/'queue.sqlite3')+'?mode=ro',uri=True)as db:
    assert db.execute("select count(*)from tasks where state in ('running','dispatching','unknown')").fetchone()[0]==0,'scheduler-not-quiescent'
    daemon=json.loads(db.execute("select value from meta where key='daemon'").fetchone()[0])['process']
   assert same_process(daemon),'current-daemon-not-alive'
   pid=daemon['pid'];cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip();assert cmd.endswith('-m workshop_director --root '+str(RUNTIME)+' serve'),'daemon-command-conflict'
   ppid=int(subprocess.check_output(['ps','-p',str(pid),'-o','ppid='],text=True));host=identity(ppid);hostcmd=subprocess.check_output(['ps','-p',str(ppid),'-o','command='],text=True).strip();assert hostcmd==str(ROOT/'dist/WorkshopDirectorHost.app/Contents/MacOS/WorkshopHost')+' --serve','host-command-conflict'
   state={'status':'stopping','daemon':daemon,'host':host};save(state);os.kill(pid,signal.SIGTERM)
  for _ in range(200):
   if not same_process(daemon)and not same_process(host):break
   time.sleep(.1)
  else:raise ValueError('old-service-not-exited-no-new-start')
  state['status']='old-processes-exited';save(state)
  command=['/bin/launchctl','kickstart','gui/'+str(os.getuid())+'/local.workshop-director'];state.update(status='start-outcome-unknown',command=command);save(state)
  r=subprocess.run(command,capture_output=True,text=True);state.update(status='start-request-confirmed'if r.returncode==0 else'failed',returncode=r.returncode,error=r.stderr);save(state);assert r.returncode==0,r.stderr
  print(json.dumps({'old_daemon_exited':True,'old_host_exited':True,'start_request_confirmed':True}))
if __name__=='__main__':reload()
