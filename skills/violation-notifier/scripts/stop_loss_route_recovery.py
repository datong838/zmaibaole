"""Typed recovery of an already opened, newly reviewed public stop-loss route.
Four bounded public reads only. No open/click/return/activation operation here.
"""
import argparse,copy,fcntl,hashlib,json,os,re,uuid
from pathlib import Path
from datetime import datetime,timezone
import governance_detail as d
import governance_stop_loss as stop
nav=d.nav;need=d.need
FIELD='stop_loss_route_recovery'
KIND='verified-stop-loss-business-route-read-recovery-v1'
ERROR='stop-auto-known-template-not-unique'
def encoded(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
import verification_session as verification
def _canonical_uncached(p):
 p=Path(p);need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]),'stop-route-canonical-path-required');return p

def ref(p):p=canonical(p);return {'path':str(p),'sha256':sha(p.read_bytes())}
def read(r):canonical(r['path']);need(set(r)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(r['sha256'])),'stop-route-ref-invalid');return nav.read_pinned(r['path'],r['sha256'])
def publish(p,b):
 p=canonical(p);p.parent.mkdir(parents=True,exist_ok=True)
 try:
  with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 except FileExistsError:need(p.read_bytes()==b,'stop-route-immutable-conflict')
 return ref(p)
def inputs(original,path,last_sha):
 m=original['manifest'];v=d.inputs(m);job=v['job'];expected=Path(m['inputs']['query']['path']).parent/'governance-detail-operations'/nav.tag(job)/'state.json';need(canonical(path)==canonical(expected),'stop-route-state-location-invalid')
 need(original.get('phase')=='read-detail' and original.get('last_error')==ERROR and not any(original.get(k) for k in ('hold','waiting_for','unknown_intent','automatic_stop_loss_owner',FIELD)),'stop-route-original-error-or-phase-invalid')
 need(original.get('cursor')==0 and original.get('details')==[] and len(v['query']['rows'])==1 and len(original.get('calls',[]))==1 and all(c.get('state')=='confirmed' for c in original['calls']),'stop-route-current-single-open-required')
 need(original['last_observation']['sha256']==last_sha and original['observations'][-1]==original['last_observation'] and len(original['observations'])==2,'stop-route-original-observation-chain-invalid');d.verify_completed(original,m,v,require_complete=False)
 opening=original['calls'][-1];row=v['query']['rows'][0];need(original['current']=={'notice_id':row['notice_id'],'normal_before':opening['before']} and original['observations'][0]==opening['before'],'stop-route-original-open-prefix-changed')
 facts,command=stop.parse(read(original['last_observation']),row,opening,job);need(facts['source_binding'].get('observed_business_context')=={'life_account_biz_ids':'','life_biz_view_id':'22'} and facts.get('marketing_features_excluded_from_recommendation') is True,'stop-route-observed-new-context-required')
 # No new flow may have started behind the failed original journal.
 return m,v,facts,command

def verify_reads(records,original,m,v,facts,command):
 need(len(records)==4,'stop-route-four-reads-required');tab=m['tab_id'];commands=[{'op':'tabs'},{'op':'ping','tabId':tab},{'op':'tree','tabId':tab},{'op':'tabs'}]
 need([r.get('command') for r in records]==commands and all(r.get('reply',{}).get('ok') is True for r in records),'stop-route-read-commands-invalid')
 times=[datetime.fromisoformat(r['at']) for r in records];need(all(t.utcoffset() is not None for t in times) and times==sorted(times) and times[0]>=datetime.fromisoformat(read(original['last_observation'])['observed_at']),'stop-route-read-time-invalid')
 before=nav.context(records[0]['reply']['result'],tab,v['job']['groupid']);after=nav.context(records[3]['reply']['result'],tab,v['job']['groupid']);old=read(original['last_observation'])['tab'];need(before['url']==after['url']==old['url'] and before.get('windowId')==after.get('windowId')==old['windowId'],'stop-route-fresh-tab-window-changed')
 ping=records[1]['reply']['result'];need(ping.get('version')==nav.VERSION and ping.get('safety')=='DOM-only' and ping.get('governance_stop_loss_policy')=='public-notice-return-v1','stop-route-loaded-policy-unreviewed')
 tree=records[2]['reply']['result'];need(not any(n.get('role') in ('progressbar','alertdialog') or n.get('attributes',{}).get('aria-busy')=='true' or any(t in n.get('name','') for t in ('风险验证','扫码登录','安全验证','账号异常','请完成验证')) for n in d.g.nodes(tree)),'stop-route-fresh-busy-or-risk')
 fresh={'source':'local-dom-bridge','observed_at':records[-1]['at'],'tab_id':tab,'tab':after,'tree':tree,'not_business_capture':True};parsed,ret=stop.parse(fresh,v['query']['rows'][0],original['calls'][-1],v['job']);need(d.same_facts(parsed,facts) and ret==command,'stop-route-fresh-facts-changed');return fresh

def _proof_base_uncached(proof_ref):
 proof=read(proof_ref);need(proof.get('kind')==KIND and proof.get('ui_used') is False and proof.get('next_phase')=='read-detail' and proof.get('original_error')==ERROR,'stop-route-proof-contract-invalid');original=read(proof['original_journal']);path=canonical(proof['canonical_journal']);folder=path.parent/'.stop-loss-route-recovery'/proof['original_journal']['sha256'];need(canonical(proof_ref['path'])==folder/'proof.json' and canonical(proof['original_journal']['path'])==folder/'original-journal.json','stop-route-proof-location-invalid');m,v,facts,command=inputs(original,path,proof['original_observation']['sha256']);need(proof['original_observation']==original['last_observation'],'stop-route-original-raw-ref-changed')
 intent=read(proof['readonly_intent']);need(canonical(proof['readonly_intent']['path'])==folder/'readonly-intent.json' and intent.get('original_journal')==proof['original_journal'] and intent.get('canonical_journal')==str(path),'stop-route-read-intent-binding-invalid')
 refs=proof['read_replies'];need([canonical(r['path']) for r in refs]==[folder/(str(i)+'-read.json') for i in range(4)],'stop-route-read-receipt-location-invalid');records=[read(r) for r in refs];need(intent.get('commands')==[r['command'] for r in records],'stop-route-intent-command-changed');fresh=verify_reads(records,original,m,v,facts,command);need(canonical(proof['fresh_observation']['path'])==folder/'fresh-observation.json' and read(proof['fresh_observation'])==fresh and proof.get('at')==fresh['observed_at'],'stop-route-fresh-ref-invalid')
 expected=copy.deepcopy(original);expected.pop('last_error');expected['observations'].append(proof['fresh_observation']);expected['last_observation']=proof['fresh_observation'];expected[FIELD]=proof_ref;expected.setdefault('resolved_errors',[]).append({'error':ERROR,'proof':proof_ref,'original_journal':proof['original_journal'],'at':proof['at']});return original,expected

def verify_recovered(current,proof_ref):
 original,expected=proof_base(proof_ref);need(current==expected,'stop-route-recovered-delta-invalid');return {'kind':KIND,'original_journal':read(proof_ref)['original_journal'],'proof':proof_ref,'original_error':{'code':ERROR,'message':ERROR}}
def verify_continuation(current):
 original,expected=proof_base(current[FIELD]);need(all(current.get(k)==expected.get(k) for k in ('manifest','fingerprint',FIELD)) and current['calls'][:len(original['calls'])]==original['calls'] and current['observations'][:len(expected['observations'])]==expected['observations'] and current.get('resolved_errors',[])[:len(expected['resolved_errors'])]==expected['resolved_errors'] and current['details'][:len(original['details'])]==original['details'],'stop-route-continuation-prefix-changed');need(current.get('last_error')!=ERROR,'stop-route-original-error-not-resolved');return {'kind':KIND,'proof':current[FIELD]}

def _reconcile_uncached(path,original_sha,last_sha,invoke,checkpoint=None):
 path=canonical(path)
 with (path.parent/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);data=path.read_bytes();original=json.loads(data)
  if FIELD in original:verify_continuation(original);raise ValueError('stop-route-already-recovered-no-read')
  need(sha(data)==original_sha,'stop-route-original-sha-mismatch');m,v,facts,command=inputs(original,path,last_sha);flow=path.parent/'automatic-stop-loss'/hashlib.sha256(v['query']['rows'][0]['notice_id'].encode()).hexdigest()/'state.json';need(not flow.exists(),'stop-route-original-flow-already-exists');folder=path.parent/'.stop-loss-route-recovery'/original_sha;oldref=publish(folder/'original-journal.json',data);proofpath=folder/'proof.json';intentpath=folder/'readonly-intent.json';commands=[{'op':'tabs'},{'op':'ping','tabId':m['tab_id']},{'op':'tree','tabId':m['tab_id']},{'op':'tabs'}]
  if proofpath.exists():pr=ref(proofpath);_,expected=proof_base(pr)
  else:
   resumed=intentpath.exists()
   if resumed:need(all((folder/(str(i)+'-read.json')).is_file() for i in range(4)),'stop-route-incomplete-read-intent-hold-no-replay')
   intent={'original_journal':oldref,'canonical_journal':str(path),'commands':commands};ir=publish(intentpath,encoded(intent));records=[];refs=[]
   for i,c in enumerate(commands):
    p=folder/(str(i)+'-read.json')
    if resumed:r=read(ref(p));rr=ref(p)
    else:
     need(path.read_bytes()==data,'stop-route-current-changed');reply=invoke(c);r={'command':c,'at':now(),'reply':reply};rr=publish(p,encoded(r))
    records.append(r);refs.append(rr);need(r.get('command')==c and r.get('reply',{}).get('ok') is True,'stop-route-read-failed-no-replay')
   fresh=verify_reads(records,original,m,v,facts,command);fr=publish(folder/'fresh-observation.json',encoded(fresh));proof={'kind':KIND,'at':fresh['observed_at'],'canonical_journal':str(path),'original_journal':oldref,'original_observation':original['last_observation'],'readonly_intent':ir,'read_replies':refs,'fresh_observation':fr,'original_error':ERROR,'next_phase':'read-detail','ui_used':False};pr=publish(proofpath,encoded(proof));_,expected=proof_base(pr)
  if checkpoint:checkpoint('proof-published')
  verify_recovered(expected,pr);need(path.read_bytes()==data,'stop-route-current-changed');tmp=path.parent/('.route-recovery-'+uuid.uuid4().hex+'.json');publish(tmp,encoded(expected));os.replace(tmp,path);return {'journal':ref(path),'proof':pr,'phase':'read-detail','ui_used':False}


def canonical(path):
    session=verification.current()
    return session.guard(_canonical_uncached,path) if session is not None else _canonical_uncached(path)

def proof_base(proof_ref):
 existing=verification.current()
 with verification.validation_scope():
  value=verification.memo_proof(_proof_base_uncached,proof_ref)
  return value if existing is not None else copy.deepcopy(value)

def reconcile(path,original_sha,last_sha,invoke,checkpoint=None):
 # Keep only immutable evidence allocated between pure checks. No _ACTIVE
 # validation scope covers journal reads/writes, checkpoints, or fresh invokes.
 session=verification.Session(max_bytes=64*1024*1024)
 session.recovery_binding=(str(path),original_sha,last_sha)
 with verification.owner_session(session):return _reconcile_uncached(path,original_sha,last_sha,invoke,checkpoint)



def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state',type=Path,required=True);p.add_argument('--original-sha256',required=True);p.add_argument('--last-observation-sha256',required=True);a=p.parse_args();print(json.dumps(reconcile(a.state,a.original_sha256,a.last_observation_sha256,nav.bridge.request),ensure_ascii=False))
if __name__=='__main__':main()
