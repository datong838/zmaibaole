#!/usr/bin/env python3
"""Stage-pinned own-control maintenance: menu blank, initial/reload toolbar once."""
import argparse,ctypes as C,fcntl,hashlib,importlib.util,json,os,sys,tempfile,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path('/Users/feibing/work/projects/zmaibaole');SCRIPTS=ROOT/'skills/douyin-laike-operator/scripts'
CONTROL='chrome-extension://egeefdmlpipoboehjpheioppnmkpaehb/control.html'
MERCHANT='https://life.douyin.com/p/life_comment/management?groupid=1767942028615694'
BLANK=('chrome://newtab/','chrome://new-tab-page/')
CAP={'native_file_menu_new_blank_max':1,'file_menu':'文件','new_tab_item':'新标签页','initial_blank_toolbar_max':1,'reload_blank_toolbar_max':1,'toolbar_total_max':2,'extension_update_max':1,'control_url':CONTROL,'merchant_tab':995698279,'merchant_window':995698278,'Cmd_T':False,'URL_input':False,'new_business_tab':False,'new_window':False,'Chrome_restart_or_update':False,'new_extension':False,'debug':False,'server_lifecycle':False,'replay_unknown':False}
def need(v,msg):
 if not v:raise ValueError(msg)
def ref(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(r):
 need(set(r)=={'path','sha256'} and Path(r['path']).is_absolute() and not Path(r['path']).is_symlink() and ref(r['path'])==r,'pinned-document-changed');return json.loads(Path(r['path']).read_bytes())
def now():return datetime.now(timezone.utc).isoformat()
def durable(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix='.stage-',dir=p.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p);fd=os.open(p.parent,os.O_RDONLY)
  try:os.fsync(fd)
  finally:os.close(fd)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def cli_result(q,command):
 x=read(q);argv=x.get('argv',[])
 need(len(argv)==4 and Path(argv[1]).resolve()==ROOT/'skills/chrome-dom-export/scripts/bridge.py' and argv[2]=='request' and json.loads(argv[3])==command and x.get('returncode') in (0,1) and x.get('stderr')=='','exact-public-CLI-required')
 r=json.loads(x['stdout']);need(r.get('ok') is True and r.get('error') is None,'successful-public-CLI-required');return r['result']
def tabs_map(tabs):
 windows={w['windowId']:w for w in tabs};rows={t['tabId']:t for w in tabs for t in w['tabs']};need(len(rows)==sum(len(w['tabs']) for w in tabs),'duplicate-tab-ID');return windows,rows
def merchant(tabs,active=None):
 w,t=tabs_map(tabs);need(995698278 in w and 995698279 in t and t[995698279]['windowId']==995698278 and t[995698279]['url']==MERCHANT,'original-merchant-scope')
 need([k for k,v in w.items() if v.get('focused') is True]==[995698278],'original-merchant-window-focused')
 if active is not None:need(t[995698279]['active'] is active and w[995698278]['focused'] is True,'original-merchant-active-scope')
 return t[995698279]
def verify_delta(before,after,urls,old_active):
 bw,bt=tabs_map(before);aw,at=tabs_map(after);merchant(after,False)
 need(set(bw)==set(aw) and set(bt)<=set(at) and len(at)==len(bt)+1,'one-new-tab-same-windows-only')
 added=[t for k,t in at.items() if k not in bt];need(len(added)==1 and added[0]['windowId']==995698278 and added[0]['url'] in urls and added[0]['active'] is True and aw[995698278]['focused'] is True,'new-tab-not-exact-active-target')
 for k,v in bt.items():
  expected=dict(v)
  if k==old_active:expected['active']=False
  need(at[k]==expected,'preexisting-tab-changed')
 return added[0]
def verify_merchant_scope(scope_ref,normal_operation):
 v=cli_result(scope_ref,{'op':'readonly-scope','tabId':995698279,'windowId':995698278});tab=merchant(v['before'],True);need(merchant(v['after'],True)==tab,'merchant-changed-during-scope')
 need(v['ping'].get('version')=='dom-only-20261103-12' and v['ping'].get('content_build')=='normal-review-export-terminal-prev-v2','reviewed-content-build')
 sys.path[:0]=[str(ROOT/'skills/negative-review-complaints/scripts'),str(SCRIPTS)];import normal_paging as p
 op=read(normal_operation);need(op.get('state')=='complete' and op.get('phase')=='source-ready','original-normal-complete-required');m=read(op['manifest']);job=read(m['job']);profile=read(op['outputs']['profile']);source=read(op['outputs']['source'])
 page={'tab':tab,'tree':v['tree'],'observed_at':now()}
 with p.A.export_parse_session.owner_session():proof=p.inspect_page(job,page,profile,m['receipt'])
 need(proof['pager']['page']==5 and proof['pager']['platform_pager_total']==54 and proof['normal_header_count']==44 and len(proof['rows'])==4 and [r['review_id'] for r in proof['rows']]==[r['review_id'] for r in source['rows'] if r['page_index']==5],'original-terminal-business-scope')
 return {'tabId':995698279,'windowId':995698278,'url':MERCHANT,'identity':p.n.public_identity(v['tree'],job['identity']),'page':5,'header':44,'total':54,'date':job['start']+'..'+job['end_exclusive'],'normal_operation':normal_operation}
def prepare(ticket_ref,grant_ref):
 t=read(ticket_ref);g=read(grant_ref)
 need(t.get('kind')=='installed-own-control-menu-maintenance-ticket-v3' and g.get('kind')=='supervisor-own-control-menu-maintenance-grant-v3' and g.get('ticket')==ticket_ref and g.get('authorized') is True and g.get('actor')=='/root/violation_operator' and g.get('maintenance_only') is True,'explicit-root-stage-grant')
 need(t.get('capability')==g.get('capability')==CAP and all(type(obj['capability'][k]) is type(v) for obj in (t,g) for k,v in CAP.items()) and g.get('helper')==ref(__file__),'exact-stage-capability')
 release=read(t['release']);need(release.get('published') is True and release.get('manifest_version')=='1.0.23' and release.get('service_worker')=='sw17.js' and release.get('build')=='normal-review-export-terminal-prev-v2','exact-sw17-release')
 for x in release['published_files']:need(ref(x['path'])==x,'released-source-changed')
 need(g.get('release')==t['release'] and type(t.get('expected_pid')) is int and t['expected_pid']>0,'exact-release-pid')
 menu=read(t['menu_proof']);need(menu.get('pid')==t['expected_pid'] and menu.get('input_actions_used') is False and menu.get('file_menu',{}).get('title')=='文件','observed-menu-proof')
 matches=[n for branch in menu['file_menu'].get('children',[]) for n in branch.get('children',[]) if n.get('role')=='AXMenuItem' and n.get('title')=='新标签页' and n.get('enabled') is True and 'AXPress' in n.get('actions',[])]
 need(len(matches)==1,'observed-new-tab-menu-item')
 return {'kind':'root-approved-own-control-stage-descriptor-v3','ticket':ticket_ref,'grant':grant_ref,'capability':CAP,'pid':t['expected_pid'],'release':t['release'],'normal_operation':t['normal_operation'],'scope':verify_merchant_scope(t['merchant_scope'],t['normal_operation']),'scope_cli':t['merchant_scope'],'menu_proof':t['menu_proof']}
def native_class():
 s=importlib.util.spec_from_file_location('reviewed_menu_maintenance',SCRIPTS/'chrome-maintenance-control.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 class Native(m.MaintenanceInspector):
  def scope(self):
   proof=self.observe();need(proof['main_window_verified'] and proof['same_window'] and proof['web_areas_count']==1,'native-main-scope')
   need(not self.array(self.bound_window,'AXSheets'),'native-sheet-present')
   areas=[]
   def walk(e,depth=0):
    need(depth<=25,'native-outer-depth')
    if self.get(e,'AXRole')=='AXWebArea':areas.append(self.get(e,'AXURL'));return
    for x in self.array(e,'AXChildren'):walk(x,depth+1)
   walk(self.bound_window);need(len(areas)==1,'native-WebArea-not-unique');proof['active_url']=areas[0];return proof
  def menu_item(self):
   bar=self.value(self.root,'AXMenuBar');need(bar and self.get(bar,'AXRole')=='AXMenuBar','native-menu-bar')
   files=[x for x in self.array(bar,'AXChildren') if self.get(x,'AXRole')=='AXMenuBarItem' and self.get(x,'AXTitle')=='文件' and self.get(x,'AXEnabled') is True];need(len(files)==1,'native-file-menu')
   menus=[x for x in self.array(files[0],'AXChildren') if self.get(x,'AXRole')=='AXMenu'];need(len(menus)==1,'native-file-submenu')
   items=[x for x in self.array(menus[0],'AXChildren') if self.get(x,'AXRole')=='AXMenuItem' and self.get(x,'AXTitle')=='新标签页' and self.get(x,'AXEnabled') is True];need(len(items)==1,'native-new-tab-item')
   e=items[0];v=C.c_void_p();need(self.ax.AXUIElementCopyActionNames(e,C.byref(v))==0 and v.value,'native-menu-actions');self.refs.append(v.value);actions=[self.decode(self.cf.CFArrayGetValueAtIndex(v.value,i)) for i in range(self.cf.CFArrayGetCount(v.value))];need('AXPress' in actions,'native-menu-press-not-supported')
   if hasattr(self,'bound_new_tab'):need(self.cf.CFEqual(e,self.bound_new_tab),'native-menu-handle-changed')
   else:self.bound_new_tab=e
   return {'role':'AXMenuItem','title':'新标签页','parent':'文件','enabled':True,'action':'AXPress'}
  def new_blank_once(self):
   need(self.scope()['active_url']==MERCHANT,'native-original-merchant-required');self.menu_item();a=self.string('AXPress')
   try:need(self.ax.AXUIElementPerformAction(self.bound_new_tab,a)==0,'native-menu-action-unknown')
   finally:self.cf.CFRelease(a)
 return Native
def stage_intent(saved,descriptor_ref,d,base,stage):
 """Local consistency of durable action intent; never a signature/authenticity claim."""
 required={'kind','descriptor','stage','state','before_tabs','before_ref','tabs_cli','stage_origin','update_ref','old_active','input_count','created_at','intent_at','native_before'}
 optional={'menu','action_returned_at','after_tabs','after_ref','result','native_after','reconciled_readonly','error'}
 need(type(saved) is dict and required<=set(saved)<=required|optional,'stage-intent-schema')
 need(saved['kind']=='one-shot-own-control-native-stage-v3' and saved['descriptor']==descriptor_ref and saved['stage']==stage and saved['state'] in ('unknown','complete') and type(saved['input_count']) is int and saved['input_count']==1,'stage-intent-binding-state')
 before=saved['before_tabs'];need(cli_result(saved['tabs_cli'],{'op':'tabs'})==before,'stage-original-tabs-CLI-changed')
 def raw_tabs(q,label):
  p=Path(q['path']);need(p.parent==base and p.name.startswith(stage+'-'+label+'-') and p.suffix=='.json','stage-raw-source-path')
  raw=read(q);need(raw.get('command')=={'op':'tabs'} and raw.get('reply',{}).get('ok') is True and raw['reply'].get('error') is None,'stage-raw-tabs-reply');return raw['reply']['result']
 need(raw_tabs(saved['before_ref'],'before')==before,'stage-original-before-digest');merchant(before)
 _,rows=tabs_map(before)
 if stage=='new-blank':
  merchant(before,True);need(saved['stage_origin'] is None and saved['update_ref'] is None and saved['old_active']==995698279 and not any(t['url']==CONTROL or t['url'] in BLANK for t in rows.values()),'stage-menu-origin')
  need(saved.get('menu')=={'role':'AXMenuItem','title':'新标签页','parent':'文件','enabled':True,'action':'AXPress'},'stage-menu-proof');required_url=MERCHANT
 else:
  prior='new-blank' if stage=='initial-toolbar' else 'initial-toolbar';q=saved['stage_origin'];need(Path(q['path'])==base/(prior+'-intent.json'),'stage-origin-canonical-ref');origin=read(q);stage_intent(origin,descriptor_ref,d,base,prior);need(origin['state']=='complete' and saved['old_active']==origin['result']['tabId'],'stage-origin-complete')
  need(saved['old_active'] in rows and rows[saved['old_active']]['windowId']==995698278 and rows[saved['old_active']]['active'] is True and rows[saved['old_active']]['url'] in BLANK and not any(t['url']==CONTROL for t in rows.values()),'stage-origin-blank-binding');required_url=rows[saved['old_active']]['url']
  if stage=='initial-toolbar':need(saved['update_ref'] is None and before==origin['after_tabs'],'stage-initial-blank-source')
  else:
   uref=saved['update_ref'];need(type(uref) is dict and Path(uref['path'])==base/'focus-space-update-intent.json','stage-reload-update-source');u=read(uref);need(u.get('kind')=='one-shot-public-AX-control-update-v1' and u.get('expected_pid')==d['pid'] and u.get('control_url')==CONTROL and u.get('state')=='action-returned' and u.get('space_posted') is True,'stage-reload-update-binding')
   bw,bt=tabs_map(origin['after_tabs']);aw,at=tabs_map(before);need(set(bw)==set(aw) and set(bt)==set(at),'stage-reload-tab-set-changed')
   for k,t in bt.items():
    expected=dict(t)
    if k==saved['old_active']:expected.update(url=at[k]['url'],title=at[k]['title'])
    need(at[k]==expected,'stage-reload-other-tab-changed')
 n=saved['native_before'];need(n.get('pid')==d['pid'] and n.get('frontmost') is True and n.get('same_window') is True and n.get('active_url')==required_url and n.get('toolbar_targets')==1,'stage-original-native-binding')
 if saved['state']=='complete':
  need({'after_tabs','after_ref','result'}<=set(saved),'stage-complete-fields')
  label='reconcile' if saved.get('reconciled_readonly') is True else 'after';need(raw_tabs(saved['after_ref'],label)==saved['after_tabs'],'stage-complete-after-digest')
  need(verify_delta(before,saved['after_tabs'],BLANK if stage=='new-blank' else (CONTROL,),saved['old_active'])==saved['result'],'stage-complete-result-delta')
 return saved
def run_stage(descriptor_ref,stage,tabs_proof,out,request=None,native_factory=None,update_ref=None):
 d=read(descriptor_ref);need(d['kind']=='root-approved-own-control-stage-descriptor-v3' and d['capability']==CAP,'stage-descriptor-kind');need(prepare(d['ticket'],d['grant'])==d,'stage-descriptor-changed')
 ticket=read(d['ticket']);base=Path(d['ticket']['path']).parent;out=Path(out).resolve();need(stage in ('new-blank','initial-toolbar','reload-toolbar') and out==base/(stage+'-intent.json'),'canonical-stage-output')
 base.mkdir(parents=True,exist_ok=True)
 if request is None:
  sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'));import bridge;request=bridge.request
 def tabs(label):
  r=request({'op':'tabs'});p=base/(stage+'-'+label+'-'+str(time.time_ns())+'.json');durable(p,{'command':{'op':'tabs'},'reply':r,'at':now()});need(r.get('ok') is True and r.get('error') is None,'stage-tabs-failed');return r['result'],ref(p)
 with (base/'.native-stages.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if out.exists():
   saved=stage_intent(json.loads(out.read_text()),descriptor_ref,d,base,stage)
   if saved['state']=='complete':return saved
   after,rr=tabs('reconcile');added=verify_delta(saved['before_tabs'],after,(BLANK if stage=='new-blank' else (CONTROL,)),saved['old_active']);saved.update(state='complete',result=added,after_tabs=after,after_ref=rr,reconciled_readonly=True);durable(out,saved);return saved
  before=cli_result(tabs_proof,{'op':'tabs'});current,br=tabs('before');need(current==before,'stage-fresh-tabs-changed');merchant(before)
  _,rows=tabs_map(before)
  origin_ref=None
  if stage=='new-blank':
   merchant(before,True);need(not any(t['url']==CONTROL or t['url'] in BLANK for t in rows.values()),'initial-control-or-blank-already-present');old_active=995698279;required=MERCHANT
  else:
   initial=read(ref(base/'new-blank-intent.json'));need(initial['state']=='complete' and initial['descriptor']==descriptor_ref,'original-menu-blank-stage-required')
   if stage=='initial-toolbar':origin=initial;origin_ref=ref(base/'new-blank-intent.json');stage_intent(initial,descriptor_ref,d,base,'new-blank');old_active=origin['result']['tabId']
   else:
    origin_ref=ref(base/'initial-toolbar-intent.json');origin=read(origin_ref);stage_intent(origin,descriptor_ref,d,base,'initial-toolbar');need(origin['state']=='complete' and origin['descriptor']==descriptor_ref,'initial-control-stage-required');need(update_ref is not None,'exact-update-intent-required');u=read(update_ref);need(Path(update_ref['path'])==base/'focus-space-update-intent.json' and u.get('kind')=='one-shot-public-AX-control-update-v1' and u.get('expected_pid')==d['pid'] and u.get('control_url')==CONTROL and u.get('state')=='action-returned' and u.get('space_posted') is True,'exact-update-returned-required');old_active=origin['result']['tabId']
   need(old_active in rows and rows[old_active]['windowId']==995698278 and rows[old_active]['active'] is True and rows[old_active]['url'] in BLANK and not any(t['url']==CONTROL for t in rows.values()),'stage-explicit-origin-blank-required');required=rows[old_active]['url']
  n=None;saved={'kind':'one-shot-own-control-native-stage-v3','descriptor':descriptor_ref,'stage':stage,'state':'preflight','before_tabs':before,'before_ref':br,'tabs_cli':tabs_proof,'stage_origin':origin_ref,'update_ref':update_ref,'old_active':old_active,'input_count':0,'created_at':now()}
  try:
   n=(native_factory or native_class())(expected_pid=d['pid']);proof=n.scope();need(proof['pid']==d['pid'] and proof['frontmost'] is True and proof['same_window'] and proof['active_url']==required and proof['toolbar_targets']==1,'native-stage-source-scope')
   if stage=='new-blank':saved['menu']=n.menu_item()
   saved.update(state='unknown',input_count=1,intent_at=now(),native_before=proof);stage_intent(saved,descriptor_ref,d,base,stage);durable(out,saved)
   if stage=='new-blank':n.new_blank_once()
   else:n.open_control() # Original proven blank guard and unique toolbar recheck.
   saved['action_returned_at']=now();durable(out,saved)
   after,rr=tabs('after');added=verify_delta(before,after,(BLANK if stage=='new-blank' else (CONTROL,)),old_active)
   final=n.scope();need(final['active_url']==added['url'],'native-post-action-URL')
   saved.update(state='complete',result=added,after_tabs=after,after_ref=rr,native_after=final);durable(out,saved);return saved
  except Exception as e:
   saved['error']=str(e);durable(out,saved);raise
  finally:
   if n:n.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True);a=sub.add_parser('prepare')
 for k in ('ticket','grant'):a.add_argument('--'+k,required=True);a.add_argument('--'+k+'-sha256',required=True)
 a.add_argument('--out',required=True);a=sub.add_parser('run')
 for k in ('descriptor','tabs-proof'):a.add_argument('--'+k,required=True);a.add_argument('--'+k+'-sha256',required=True)
 a.add_argument('--stage',choices=('new-blank','initial-toolbar','reload-toolbar'),required=True);a.add_argument('--out',required=True);a.add_argument('--update-intent');a.add_argument('--update-intent-sha256');x=p.parse_args();q=lambda k:{'path':getattr(x,k.replace('-','_')),'sha256':getattr(x,k.replace('-','_')+'_sha256')}
 if x.mode=='prepare':d=prepare(q('ticket'),q('grant'));out=Path(x.out);need(out.resolve()==Path(x.ticket).parent/'native-control-order.json' and not out.exists(),'new-canonical-descriptor-required');durable(out,d);print(json.dumps(ref(out)))
 else:print(json.dumps(run_stage(q('descriptor'),x.stage,q('tabs-proof'),x.out,update_ref=q('update-intent') if x.update_intent else None),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'error':str(e),'replay_input':False}));raise SystemExit(2)
