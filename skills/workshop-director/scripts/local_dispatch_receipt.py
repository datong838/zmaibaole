"""Versioned actual local worker acknowledgement, never a Codex tool label."""
import hashlib,json,os,subprocess,uuid,re
from pathlib import Path
def need(x,e):
    if not x:raise ValueError(e)
def checked(r):
    p=Path(r['path']);need(p.is_absolute() and p.is_file() and not p.is_symlink(),'local-receipt-file-required');b=p.read_bytes();need(hashlib.sha256(b).hexdigest()==r['sha256'],'local-receipt-hash');return json.loads(b)
def identity(pid):
    try:
        start=subprocess.check_output(['/bin/ps','-p',str(pid),'-o','lstart=','-o','stat='],text=True,stderr=subprocess.DEVNULL).strip()
        if not start:return None
        start,status=start.rsplit(None,1)
        if status.startswith('Z'):return None
        p=Path('/proc/sys/kernel/random/boot_id')
        if p.exists():boot=p.read_text().strip()
        else:
            raw=subprocess.check_output(['/usr/sbin/sysctl','-n','kern.bootsessionuuid'],text=True,timeout=5).strip();need(re.fullmatch(r'[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}',raw) is not None,'local-ack-boot-session-uuid-unavailable')
            value=uuid.UUID(raw);need(value.int!=0,'local-ack-boot-session-uuid-unavailable')
            boot='darwin-kern-bootsessionuuid:'+str(value)
        return {'pid':pid,'started':start,'boot':boot} if start else None
    except (OSError,subprocess.CalledProcessError):return None
def verify(encoded,state):
    receipt=checked(json.loads(encoded));need(receipt.get('kind')=='local-subprocess-spawn-ack-v1' and receipt.get('dispatcher_protocol')=='local-subprocess-v1','local-ack-protocol')
    need(receipt.get('dispatch_id')==state['dispatch_id'] and receipt.get('day')==state['day'],'local-ack-dispatch-scope')
    need(identity(receipt.get('pid'))==receipt.get('process') and bool(receipt.get('process')),'local-ack-original-process-not-alive')
    request=checked(receipt['request']);need(request['task']['day']==state['day'] and request['task']['workflow' if 'workflow' in request['task'] else 'flow']==state['dispatch_id'].split(':')[1],'local-ack-task-scope')
    need(request['attempt_id']==receipt['attempt_id'] and receipt['pid']==os.getpid(),'local-ack-actual-caller-required')
    intent=checked(receipt['dispatch_intent']);need(intent.get('kind')=='local-coordinator-dispatch-intent-v1' and intent['request']==receipt['request'] and intent['dispatch_id']==state['dispatch_id'] and intent['offer']==receipt['offer'],'local-ack-durable-intent-required')
    offer=checked(receipt['offer']);need(offer.get('dispatcher_protocol')=='local-subprocess-v1' and offer.get('tool')=='local-subprocess-v1' and offer['dispatch_id']==state['dispatch_id'],'local-ack-offer-protocol')
    return receipt
