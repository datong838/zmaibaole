"""Pure verification of Navigator's center-entry review boundary; zero progress."""
import hashlib,importlib.util,json,re,sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

def need(ok,code):
    if not ok:raise ValueError(code)
def read_file(path):
    p=Path(path);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),'semantic-navigation-profile-path-invalid');raw=p.read_bytes();return raw,json.loads(raw)
def pinned(reference):
    need(isinstance(reference,dict) and set(reference)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(reference['sha256'])),'semantic-navigation-profile-ref-invalid');raw,v=read_file(reference['path']);need(hashlib.sha256(raw).hexdigest()==reference['sha256'],'semantic-navigation-profile-evidence-changed');return v
def aware(value):
    t=datetime.fromisoformat(str(value).replace('Z','+00:00'));need(t.utcoffset() is not None,'semantic-navigation-profile-time-invalid');return t

def verify(s,journal_path,*,role,navigation_directory):
    need(role=='violation_operator','semantic-navigation-profile-role-conflict');path=Path(journal_path);raw,current=read_file(path);need(path.name=='center-navigation.json' and current==s,'semantic-navigation-profile-canonical-journal-required')
    folder=path.parent;job_path=folder/'navigation-job.json';jobraw,job=read_file(job_path);jobref={'path':str(job_path),'sha256':hashlib.sha256(jobraw).hexdigest()}
    # The formal role plan owns this work directory; copies elsewhere are not
    # new canonical journals for the same immutable plan.
    need(Path(job['plan_path']).parent==folder,'semantic-navigation-profile-plan-directory-conflict')
    directory=Path(navigation_directory).resolve();spec=importlib.util.spec_from_file_location('workshop_navigation_profile_parser',directory/'bridge-navigation.py');nav=importlib.util.module_from_spec(spec);previous=list(sys.path)
    try:
        sys.path.insert(0,str(directory));spec.loader.exec_module(nav)
        need(Path(nav.__file__).resolve()==directory/'bridge-navigation.py','semantic-navigation-profile-module-origin-conflict');nav.scope(job)
        need(s.get('version')==1 and s.get('phase')=='profileRequired' and s.get('waiting_for')=='live-violation-analysis-date-and-pagination-profile','semantic-navigation-profile-phase-required')
        need(all(s.get(k) is False for k in ('profile_accepted','business_progress_changed','production_enabled','platform_writes','zero_verified')),'semantic-navigation-profile-flags-invalid')
        need(not any(s.get(k) for k in ('last_error','error','hold','switch_read_hold','waiting_input','settling_exhausted','readonly_route_exhausted','unknown_intent','details','pages','manifest','automatic_stop_loss_owner')),'semantic-navigation-profile-unresolved')
        need(s.get('fingerprint')==nav.tag(job) and all(s.get(k)==job.get(k) for k in ('company','start','end_exclusive')) and s.get('groupid')==str(job['groupid']) and type(s.get('tab_id')) is int and s['tab_id']>0,'semantic-navigation-profile-job-binding-conflict')
        refs=s.get('observations');need(isinstance(refs,list) and refs and s.get('last_tree')==refs[-1] and len({json.dumps(r,sort_keys=True) for r in refs})==len(refs),'semantic-navigation-profile-final-observation-required')
        observations=[];times=[]
        for r in refs:
            p=Path(r['path']);need(p.parent==folder/'navigation-evidence' and re.fullmatch(r'[0-9]{3,}-(?:account|readAccount|menu|openCenter|observeCenter)-[0-9a-f]{12}\.json',p.name),'semantic-navigation-profile-observation-path-invalid');o=pinned(r)
            need(o.get('source')=='local-dom-bridge' and o.get('company')==job['company'] and o.get('groupid')==str(job['groupid']) and o.get('tab_id')==s['tab_id'] and o.get('navigation_fingerprint')==s['fingerprint'] and o.get('plan_sha256')==job['plan_sha256'] and o.get('not_business_capture') is True and o.get('full_field_text_verified') is False and o.get('name_text_limit')==800,'semantic-navigation-profile-observation-binding-conflict')
            tab=nav.context([{'tabs':[o['tab']]}],s['tab_id'],job['groupid']);u=urlsplit(tab['url']);ns=list(nav.nodes(o['tree']));need(not u.fragment and u.path.startswith('/p/') and o['tree'].get('url')=='https://life.douyin.com'+u.path,'semantic-navigation-profile-route-conflict');need(not any(any(t in n.get('name','') for t in ('扫码登录','风险验证','安全验证','账号异常','请完成验证')) for n in ns),'semantic-navigation-profile-risk-stop');times.append(aware(o['observed_at']));observations.append(o)
        need(times==sorted(times),'semantic-navigation-profile-observation-time-invalid');final=observations[-1];window=final['tab'].get('windowId');need(type(window) is int and window>0 and urlsplit(final['tab']['url']).path==nav.CENTER and final['tree'].get('url')=='https://life.douyin.com'+nav.CENTER and '-observeCenter-' in Path(refs[-1]['path']).name,'semantic-navigation-profile-final-center-required');nav.identity(final['tree'],job['identity']);need(aware(s.get('identity_verified_at'))<=times[-1],'semantic-navigation-profile-identity-time-invalid');need(all(o['tab'].get('windowId')==window for o in observations),'semantic-navigation-profile-observation-window-conflict')
        calls=s.get('calls');need(isinstance(calls,list) and calls and all(c.get('state')=='confirmed' for c in calls),'semantic-navigation-profile-confirmed-calls-required');keys=set();index=-1;center_calls=0
        for call in calls:
            key=call.get('key','');match=re.fullmatch(r'[0-9]+:(account|menu|openCenter)',key);need(match and key not in keys,'semantic-navigation-profile-original-call-required');keys.add(key);phase=match.group(1)
            r=call.get('before')
            if r is None:
                need(phase=='openCenter','semantic-navigation-profile-original-before-required');r=s.get('readonly_center_before')
            need(r in refs,'semantic-navigation-profile-original-before-required');i=refs.index(r);need(i>index and i<len(refs)-1,'semantic-navigation-profile-call-order-invalid');index=i;before=observations[i];need(before['tab'].get('windowId')==window and times[i]<=aware(call['intent_at'])<=times[-1],'semantic-navigation-profile-call-time-or-window-conflict')
            label=job['identity']['provider'] if phase=='account' else '经营保障' if phase=='menu' else '违规中心';target=nav.exact(before['tree'],label);command={'op':'hover' if phase=='account' else 'click','tabId':s['tab_id'],'locator':{'by':'selector','value':target['selector']},'kind':'navigation'};need(call.get('command')==command,'semantic-navigation-profile-command-not-derived');reply=call.get('result',{});need(isinstance(reply,dict),'semantic-navigation-profile-reply-conflict');node=reply.get('hovered' if phase=='account' else 'clicked');need(isinstance(node,dict) and node.get('selector')==target['selector'] and node.get('name')==label and node.get('disabled',False) is False,'semantic-navigation-profile-reply-conflict')
            need(reply.get('kind')=='navigation','semantic-navigation-profile-reply-conflict')
            if command['op']=='click':need(reply.get('version')==nav.VERSION,'semantic-navigation-profile-reply-conflict')
            if phase=='openCenter':center_calls+=1;need(call is calls[-1],'semantic-navigation-profile-final-center-call-required');nav.identity(before['tree'],job['identity'])
        need(center_calls==1,'semantic-navigation-profile-unique-center-call-required')
        need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'semantic-navigation-profile-current-changed')
        # Re-hash every pinned observation and original plan/receipt at the end.
        for r in refs:pinned(r)
        nav.scope(job)
        need(path.read_bytes()==raw and job_path.read_bytes()==jobraw,'semantic-navigation-profile-current-changed')
        return {'kind':'verified-navigation-center-entry-pending-v1','job':jobref,'final_observation':refs[-1],'original_confirmed_calls':len(calls),'full_identity_verified':True,'target_path':nav.CENTER,'window_id':window,'profile_accepted':False,'dates_queried':False,'business_progress_changed':False,'completion_claimed':False,'observations_are_progress':False}
    finally:sys.path[:]=previous
