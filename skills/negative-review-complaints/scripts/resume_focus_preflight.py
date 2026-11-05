#!/usr/bin/env python3
"""Rearm one proven zero-business-input focus failure; never call browser APIs."""
import argparse,fcntl,hashlib,json,os
from datetime import datetime,timezone
from urllib.parse import urlparse,parse_qs
from pathlib import Path
ERROR='result-runner-bridge-failed:existing-tab-focus-not-confirmed'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def ref(path):return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def load(r):
 p=Path(r['path']);need(p.is_absolute() and not p.is_symlink() and ref(p)==r,'reference-changed');return json.loads(p.read_bytes())
def immutable(p,data):
 raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode()
 if p.exists():need(p.read_bytes()==raw,'immutable-conflict');return
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def resume(batch_ref,operation_ref,focus_ref):
 bpath=Path(batch_ref['path']);event={'kind':'verified-zero-business-input-focus-recovery-v1','batch':batch_ref,'operation':operation_ref,'focus':focus_ref}
 with (bpath.parent/'.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  current=json.loads(bpath.read_bytes())
  if event in current.get('focus_preflight_recoveries',[]):return {'state':current['state'],'idempotent':True,'business_actions':False}
  b=load(batch_ref);o=load(operation_ref);focus=load(focus_ref)
  need(b.get('state')=='hold' and b.get('error')==ERROR,'batch-not-focus-hold')
  need(o.get('state')=='preflight' and o.get('error')==ERROR and o.get('reads')==0,'operation-not-zero-read-preflight')
  need(not any(k in o for k in ('open_command','open_reply','result_input','close_command','close_reply')),'business-action-already-prepared')
  m=o['manifest'];need(b.get('current_key')==m['review_key'] and b['current_key'] not in b.get('completed',[]),'current-case-conflict')
  bm=load(b['manifest']);need(bm['root']==m['root'] and bm['source']['sha256']==m['inputs']['source']['sha256'],'source-root-conflict')
  need(b.get('journey',{}).get('state')=='complete','journey-not-complete')
  need(focus.get('kind')=='existing-tab-focus-observation-v1' and focus.get('tab_id')==load(m['inputs']['page'])['tab']['tabId'] and focus.get('active') is True and focus.get('window_focused') is True and focus.get('chrome_frontmost') is True,'focus-not-confirmed')
  need(focus.get('business_actions') is False and focus.get('browser_restarted') is False,'focus-business-action-denied')
  observed=datetime.fromisoformat(focus['observed_at'].replace('Z','+00:00'));age=(datetime.now(timezone.utc)-observed).total_seconds()
  need(0<=age<=300,'focus-observation-stale')
  raw_tabs=load(focus.get('tabs_raw',focus.get('tabs')));need(raw_tabs.get('ok') is True,'focus-tabs-failed')
  matches=[(w,t) for w in raw_tabs['result'] for t in w.get('tabs',[]) if t.get('tabId')==focus['tab_id']]
  need(len(matches)==1,'focus-tab-not-unique');w,t=matches[0]
  need(w.get('focused') is True and t.get('active') is True and t.get('windowId')==w.get('windowId'),'focus-window-not-actual')
  url=urlparse(t['url']);job=load(m['inputs']['job'])
  need(url.scheme=='https' and url.netloc=='life.douyin.com' and parse_qs(url.query).get('groupid')==[str(job['groupid'])],'focus-company-changed')
  native=load(focus.get('native_ax_raw',focus.get('native')));need(native.get('AXFrontmost',native.get('frontmost')) is True,'native-focus-not-confirmed')

  immutable(bpath.parent/('focus-hold-'+batch_ref['sha256']+'.json'),b)
  immutable(bpath.parent/('focus-operation-'+operation_ref['sha256']+'.json'),o)
  immutable(bpath.parent/('focus-recovery-'+batch_ref['sha256']+'.json'),event)
  b['state']='running';b.pop('error');b.setdefault('focus_preflight_recoveries',[]).append(event)
  temp=bpath.with_suffix('.focus.tmp')
  with temp.open('w') as f:json.dump(b,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
  os.replace(temp,bpath)
  fd=os.open(bpath.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
  return {'state':'running','operation':ref(bpath),'idempotent':False,'business_actions':False}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('batch','operation','focus'):
  p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
 a=p.parse_args();out=resume(*({'path':getattr(a,n),'sha256':getattr(a,n+'_sha256')} for n in ('batch','operation','focus')));print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
