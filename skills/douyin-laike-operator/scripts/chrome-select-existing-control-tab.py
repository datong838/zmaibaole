#!/usr/bin/env python3
"""One durable public AX selection of an existing reviewed local control tab.
No bridge activate, new tab, toolbar, key event, URL input, WebArea content or config.
"""
import argparse,ctypes as C,fcntl,hashlib,importlib.util,json,math,os,re,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit,parse_qs
SCRIPTS=Path(__file__).resolve().parent;ROOT=SCRIPTS.parents[2]
spec=importlib.util.spec_from_file_location('select_control_shell',SCRIPTS/'chrome-shell-diagnostic.py');shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
STATE_DIR=ROOT/'runtime/chrome-control-tab-selection'
URL='chrome-extension://egeefdmlpipoboehjpheioppnmkpaehb/control.html';LABEL='本地 DOM 桥接'
def need(ok,code):
 if not ok:raise ValueError(code)
def now():return datetime.now(timezone.utc).isoformat()
def canonical(value):
 p=Path(value);need(p.is_absolute() and p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents)),'select-control-canonical-path-required');return p
def read(ref):
 need(isinstance(ref,dict) and set(ref)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',str(ref['sha256'])),'select-control-reference-required');path=canonical(ref['path']);need(path.name not in ('config.json','config.js'),'select-control-config-read-forbidden');raw=path.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'],'select-control-original-reference-changed');return json.loads(raw),raw
def atomic(path,value):
 temp=path.with_name(path.name+'.tmp')
 with temp.open('w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 temp.replace(path)
def title_ok(title):return type(title) is str and (title==LABEL or re.fullmatch(r'本地 DOM 桥接 - 内存用量 - [0-9]+(?:\.[0-9]+)? (?:MB|GB)',title) is not None)
def rejected_proof(original,tab_id,window_id):
 value,raw=read(original);need(set(value)=={'key','state','tabId','windowId','command','start_clock_monotonic','end_clock_monotonic','returncode','stdout','stderr'} and value['state']=='unknown' and value['returncode']==1 and value['stderr']=='' and type(value['tabId']) is int and type(value['windowId']) is int and value['tabId']==tab_id and value['windowId']==window_id,'select-control-known-rejected-activation-required');need(json.loads(value['stdout'])=={'ok':False,'result':None,'error':'tab is not allowed site'},'select-control-original-not-explicitly-rejected');argv=value['command'];need(isinstance(argv,list) and len(argv)==4 and canonical(argv[1])==ROOT/'skills/chrome-dom-export/scripts/bridge.py' and argv[2]=='request' and json.loads(argv[3])=={'op':'activate','tabId':tab_id},'select-control-original-command-mismatch');need(all(type(value[k]) in (int,float) and math.isfinite(value[k]) for k in ('start_clock_monotonic','end_clock_monotonic')) and 0<=value['start_clock_monotonic']<value['end_clock_monotonic'],'select-control-original-time-invalid');return raw

def binding(expected_pid,order,tabs,key,original=None):
 need(type(expected_pid) is int and expected_pid>0 and type(key) is str and re.fullmatch('[A-Za-z0-9_.:-]{8,128}',key),'select-control-explicit-pid-key-required');o,order_raw=read(order);need(o.get('kind')=='independent-extension-maintenance-ticket-v1' and type(o.get('ticket_id')) is str and re.fullmatch('[A-Za-z0-9_.:-]{8,128}',o['ticket_id']) and o.get('no_business_dispatch') is True and o.get('await_supervisor_review_after_report') is True and isinstance(o.get('allowed'),list) and isinstance(o.get('forbidden'),list),'select-control-maintenance-order-required');need(datetime.fromisoformat(o['created_at']).utcoffset() is not None,'select-control-order-time-required');read(o['release'])
 cli,tabs_raw=read(tabs);argv=cli.get('argv');need(isinstance(argv,list) and len(argv)==4 and canonical(argv[1])==ROOT/'skills/chrome-dom-export/scripts/bridge.py' and argv[2]=='request' and json.loads(argv[3])=={'op':'tabs'} and cli.get('stderr')=='' and type(cli.get('returncode')) is int and cli['returncode'] in (0,1),'select-control-public-tabs-CLI-required');need(all(type(cli.get(k)) in (int,float) and math.isfinite(cli[k]) for k in ('start_clock_monotonic','end_clock_monotonic')) and 0<=cli['start_clock_monotonic']<cli['end_clock_monotonic'],'select-control-tabs-time-invalid');reply=json.loads(cli['stdout']);need(reply.get('ok') is True and reply.get('error') is None and reply.get('outcome') not in ('unknown','not-delivered') and isinstance(reply.get('result'),list) and (cli['returncode']==0 or 'error' in reply),'select-control-successful-public-tabs-required');controls=[]
 for window in reply['result']:
  need(type(window.get('windowId')) is int and isinstance(window.get('tabs'),list),'select-control-tabs-window-invalid')
  for t in window['tabs']:
   if t.get('url')==URL:controls.append((window,t))
 need(len(controls)==1,'select-control-public-control-tab-not-unique');window,tab=controls[0];need(window.get('type')=='normal' and type(tab.get('tabId')) is int and tab['tabId']>0 and tab.get('windowId')==window['windowId'] and type(tab.get('active')) is bool and tab.get('allowed') is False and title_ok(tab.get('title')),'select-control-public-control-tab-invalid');merchants=[];return_ids=[int(match.group(1)) for text in o['allowed'] if type(text) is str for match in [re.fullmatch(r'return originalmerchant([0-9]+)',text)] if match]
 for t in window['tabs']:
  u=urlsplit(t.get('url',''));q=parse_qs(u.query,keep_blank_values=True)
  if (t.get('active') is True and tab['active'] is False or tab['active'] is True and len(return_ids)==1 and t.get('tabId')==return_ids[0]) and t.get('allowed') is True and u.scheme=='https' and u.netloc=='life.douyin.com' and len(q.get('groupid',[]))==1 and re.fullmatch('[0-9]+',q['groupid'][0]):merchants.append({**t,'groupid':q['groupid'][0]})
 need(len(merchants)==1,'select-control-original-active-merchant-scope-required');merchant=merchants[0];need(merchant.get('windowId')==window['windowId'] and type(merchant.get('tabId')) is int,'select-control-merchant-window-mismatch');archives={'maintenance-order':order_raw,'public-tabs':tabs_raw}
 if original is not None:archives['original-rejected-intent']=rejected_proof(original,tab['tabId'],window['windowId'])
 b={'kind':'one-shot-existing-control-tab-selection-v1','expected_pid':expected_pid,'key':key,'maintenance_order':order,'maintenance_ticket_id':o['ticket_id'],'public_tabs_proof':tabs,'original_rejected_intent':original,'control_tab_id':tab['tabId'],'control_window_id':window['windowId'],'original_merchant':merchant,'control_url':URL,'title_label':LABEL};out=canonical(STATE_DIR)/(hashlib.sha256(o['ticket_id'].encode()).hexdigest()+'.json');return b,out,archives
class ControlTab(shell.ChromeShellInspector):
 def inspect(self,require_frontmost=False):
  front=self.get(self.root,'AXFrontmost') is True
  if require_frontmost:need(front,'select-control-Chrome-not-frontmost')
  windows=[w for w in self.array(self.root,'AXWindows') if self.get(w,'AXRole')=='AXWindow' and self.get(w,'AXSubrole')=='AXStandardWindow' and self.get(w,'AXMain') is True and self.get(w,'AXMinimized') is not True];need(len(windows)==1,'select-control-main-window-not-unique');window=windows[0];actual=self.value(self.root,'AXMainWindow');need(actual and self.cf.CFEqual(window,actual),'select-control-main-window-conflict')
  if hasattr(self,'bound_window'):need(self.cf.CFEqual(window,self.bound_window),'select-control-main-window-changed')
  else:self.bound_window=window
  targets=[];areas=[];count=0;deadline=time.monotonic()+10
  def walk(e,path,depth):
   nonlocal count
   count+=1;need(count<=2000 and depth<=25 and time.monotonic()<deadline,'select-control-outer-tree-incomplete');role=self.get(e,'AXRole')
   if role=='AXWebArea':areas.append(self.get(e,'AXURL'));return # No children/other WebArea attributes.
   if role=='AXRadioButton' and self.get(e,'AXSubrole')=='AXTabButton' and title_ok(self.get(e,'AXTitle')):targets.append((e,path,self.get(e,'AXTitle')))
   for i,child in enumerate(self.array(e,'AXChildren')):walk(child,path+[i],depth+1)
  walk(window,[],0);need(len(targets)==1 and len(areas)==1 and type(areas[0]) is str,'select-control-tab-or-WebArea-not-unique');target,path,title=targets[0];need(self.get(target,'AXEnabled') is True and type(self.get(target,'AXSelected')) is bool,'select-control-tab-not-enabled-or-selected-state-unknown')
  actions=C.c_void_p();error=self.ax.AXUIElementCopyActionNames(target,C.byref(actions));need(error==0 and actions.value,'select-control-actions-unavailable');self.refs.append(actions.value);size=self.cf.CFArrayGetCount(actions.value);need(0<=size<=32,'select-control-actions-bound-exceeded');names=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(size)];need('AXPress' in names,'select-control-tab-AXPress-unavailable')
  if hasattr(self,'bound_tab'):need(self.cf.CFEqual(target,self.bound_tab),'select-control-tab-handle-changed')
  else:self.bound_tab=target
  if hasattr(self,'expected_source_url'):need(areas[0] in (self.expected_source_url,URL),'select-control-active-source-URL-changed')
  return {'pid':self.pid,'frontmost':front,'main_window_verified':True,'target':{'path':path,'role':'AXRadioButton','subrole':'AXTabButton','title':title,'enabled':True,'selected':self.get(target,'AXSelected'),'AXPress_public':True},'active_url':areas[0],'webarea_contents_read':False,'webarea_children_read':False,'node_count':count,'truncated':False}
 def front_once(self):
  self.inspect();name=self.string('AXFrontmost');yes=C.c_void_p.in_dll(self.cf,'kCFBooleanTrue').value
  try:error=self.ax.AXUIElementSetAttributeValue(self.root,name,yes)
  finally:self.cf.CFRelease(name)
  need(error==0,'select-control-activation-outcome-unknown');deadline=time.monotonic()+2
  while self.get(self.root,'AXFrontmost') is not True:
   need(time.monotonic()<deadline,'select-control-frontmost-not-confirmed');time.sleep(.05)
  return {'AXFrontmost_set_return_code':error}
 def press_once(self):
  proof=self.inspect(require_frontmost=True);need(proof['target']['selected'] is False,'select-control-target-already-selected-no-press');parent=self.value(self.bound_tab,'AXParent');inside=False
  for _ in range(25):
   if not parent or self.get(parent,'AXRole')=='AXWebArea':break
   if self.cf.CFEqual(parent,self.bound_window):inside=True;break
   parent=self.value(parent,'AXParent')
  need(inside,'select-control-tab-ancestry-changed');action=self.string('AXPress')
  try:error=self.ax.AXUIElementPerformAction(self.bound_tab,action)
  finally:self.cf.CFRelease(action)
  need(error==0,'select-control-AXPress-outcome-unknown');return {'AXPress_return_code':error}
def valid_scope(proof,pid):
 need(proof.get('pid')==pid and proof.get('main_window_verified') is True and proof.get('webarea_contents_read') is False and proof.get('webarea_children_read') is False and proof.get('truncated') is False and type(proof.get('frontmost')) is bool,'select-control-public-scope-invalid');target=proof.get('target',{});need(target.get('role')=='AXRadioButton' and target.get('subrole')=='AXTabButton' and title_ok(target.get('title')) and target.get('enabled') is True and target.get('AXPress_public') is True and type(target.get('selected')) is bool,'select-control-public-tab-invalid');return proof

def run(expected_pid,out,key,order,tabs,original=None,native_factory=ControlTab):
 b,expected,archives=binding(expected_pid,order,tabs,key,original);out=canonical(out);need(out==expected,'select-control-original-canonical-ticket-required');out.parent.mkdir(parents=True,exist_ok=True)
 with (canonical(STATE_DIR)/'.selection.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if out.exists():
   old=json.loads(out.read_text());need(old.get('binding')==b,'select-control-original-ticket-binding-required');return {**old,'replayed':False,'new_input':False,'verified_current':False}
  for other in out.parent.glob('*.json'):
   if not re.fullmatch('[0-9a-f]{64}\.json',other.name):continue
   prior=json.loads(other.read_text());need(prior.get('state')!='unknown' or prior.get('binding',{}).get('expected_pid')!=expected_pid,'select-control-other-maintenance-unknown')
  archive_refs={}
  for name,raw in archives.items():
   archive=out.parent/(out.stem+'-'+name+'.json')
   if archive.exists():need(archive.read_bytes()==raw,'select-control-archive-conflict')
   else:
    with archive.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
   archive_refs[name]={'path':str(archive),'sha256':hashlib.sha256(raw).hexdigest()}
  saved={'binding':b,'archives':archive_refs,'state':'preflight','phase':'inspect-existing-tab','created_at':now(),'samples':[],'press_count':0,'activation_count':0,'press_attempts':0,'activation_attempts':0,'business_data_changed':False};native=None
  try:
   native=native_factory(expected_pid=expected_pid);need(native.pid==expected_pid,'select-control-process-changed');native.expected_source_url=b['original_merchant']['url'];proof=valid_scope(native.inspect(),expected_pid);need(proof['active_url'] in (b['original_merchant']['url'],URL),'select-control-main-window-source-URL-changed');saved['before']=proof;need(proof['target']['selected'] or proof['active_url']!=URL,'select-control-selected-URL-conflict')
   if not proof['target']['selected']:
    if not proof['frontmost']:
     saved.update(state='unknown',phase='activation-intent',activation_intent_at=now(),activation_attempts=1);atomic(out,saved);saved['activation']=native.front_once();saved['activation_count']=1;proof=valid_scope(native.inspect(require_frontmost=True),expected_pid);need(proof['active_url'] in (b['original_merchant']['url'],URL),'select-control-active-source-URL-changed');saved['after_activation']=proof
    if not proof['target']['selected']:
     saved.update(state='unknown',phase='tab-press-intent',press_intent_at=now(),press_attempts=1);atomic(out,saved);saved['press_result']=native.press_once();saved.update(press_count=1,phase='verify-control',press_returned_at=now());atomic(out,saved)
     for _ in range(3):
      proof=valid_scope(native.inspect(require_frontmost=True),expected_pid);need(proof['active_url'] in (b['original_merchant']['url'],URL),'select-control-active-source-URL-changed');saved['samples'].append(proof);atomic(out,saved)
      if proof['target']['selected'] and proof['active_url']==URL:break
   need(proof['target']['selected'] is True and proof.get('active_url')==URL,'select-control-effect-not-confirmed-no-replay');need(binding(expected_pid,order,tabs,key,original)[0]==b,'select-control-original-scope-changed');saved.update(state='complete',phase='exact-control-URL-verified',after=proof,completed_at=now(),control_url_verified=True);atomic(out,saved);return {**saved,'new_input':bool(saved['press_count'] or saved['activation_count']),'replayed':False,'verified_current':True}
  except Exception as e:
   saved.update(error=str(e),state='unknown' if saved['state']=='unknown' else 'stopped-before-input');atomic(out,saved);raise
  finally:
   if native:native.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--out');p.add_argument('--key',required=True);p.add_argument('--plan',action='store_true')
 for name in ('maintenance-order','tabs-proof'):p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
 p.add_argument('--original-rejected-intent');p.add_argument('--original-rejected-intent-sha256');a=p.parse_args();need(bool(a.original_rejected_intent)==bool(a.original_rejected_intent_sha256),'select-control-original-reference-pair-required');ref=lambda n:{'path':str(Path(getattr(a,n)).resolve()),'sha256':getattr(a,n+'_sha256')};original=ref('original_rejected_intent') if a.original_rejected_intent else None;order=ref('maintenance_order');tabs=ref('tabs_proof')
 try:
  if a.plan:
   b,out,_=binding(a.expected_pid,order,tabs,a.key,original);print(json.dumps({'binding':b,'required_out':str(out),'native_used':False},ensure_ascii=False));return 0
  need(a.out is not None,'select-control-explicit-out-required');result=run(a.expected_pid,str(Path(a.out).resolve()),a.key,order,tabs,original);print(json.dumps(result,ensure_ascii=False));return 0 if result['state']=='complete' else 2
 except Exception as e:print(json.dumps({'ok':False,'error':str(e),'replayed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
