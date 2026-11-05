#!/usr/bin/env python3
"""Resume only the original first-read connection refusal; never performs RPC/input."""
import argparse,fcntl,json
from pathlib import Path
import normal_paging_runner as c
def resume(manifest,original_state_sha256,grant):
    m=c.document(manifest);base=Path(manifest['path']).parent
    with (base/'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        r=c.Runner(manifest);r.guard();approval=c.document(grant)
        c.need(approval.get('kind')=='supervisor-original-normal-read-recovery-grant-v1' and approval.get('manifest')==manifest and approval.get('original_state_sha256')==original_state_sha256,'original-read-recovery-grant-required')
        c.need(all(approval.get(k) is True for k in ('service_running_verified','original_navigation_unchanged','allow_original_read_resume_only','no_browser_or_business_input')),'read-recovery-approval-required')
        c.document(approval['service_health'])
        if r.s.get('read_recovery'):
            c.need(r.s['read_recovery']['grant']==grant and r.s['read_recovery']['original_state_sha256']==original_state_sha256,'read-recovery-original-authorization-required')
            return {'state':r.s['state'],'operation':c.ref(r.path),'rearmed':False,'ui_used':False,'rpc_used':False}
        c.need(c.ref(r.path)['sha256']==original_state_sha256,'read-recovery-original-state-changed')
        c.need(r.s['state']=='hold' and r.s['phase']=='read-first' and r.s['expected_page']==1 and not r.s.get('pages') and not r.s.get('calls') and not r.s.get('upgraded_navigation') and not r.s.get('upgrade_intent'),'read-recovery-preinput-only')
        transport=r.s.get('transport',[]);c.need(len(transport)==1,'read-recovery-single-original-failure-required');failure=c.document(transport[0]);error=failure.get('exception',{})
        c.need(failure.get('command')=={'op':'tabs'} and 'reply' not in failure and error.get('type')=='URLError' and error.get('message')=='<urlopen error [Errno 61] Connection refused>' and r.s.get('error')==error['message'],'read-recovery-explicit-connection-refusal-only')
        nav=c.document({'path':m['original_navigation']['path'],'sha256':r.s['navigation_sha256']});c.need(r.s['navigation_sha256']==m['original_navigation']['sha256'] and all(x.get('state')=='confirmed' for x in nav['calls']),'read-recovery-original-navigation-required')
        directory=base/'read-recovery';old=c.immutable(directory/'original-hold.json',r.path.read_bytes());audit=c.publish(directory/'authorization.json',{'grant':grant,'manifest':manifest,'original_state':old,'failure':transport[0],'at':c.now(),'rpc_used':False,'input_used':False})
        r.s['read_recovery']={'grant':grant,'original_state_sha256':original_state_sha256,'audit':audit};r.s['state']='running';r.s.pop('error',None);r.persist()
        return {'state':'running','operation':c.ref(r.path),'rearmed':True,'ui_used':False,'rpc_used':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','grant'):p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
    p.add_argument('--original-state-sha256',required=True);a=p.parse_args();print(json.dumps(resume({'path':a.manifest,'sha256':a.manifest_sha256},a.original_state_sha256,{'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
    try:main()
    except (ValueError,KeyError,OSError,RuntimeError) as e:print(json.dumps({'state':'hold','error':str(e),'ui_used':False,'rpc_used':False},ensure_ascii=False));raise SystemExit(2)
