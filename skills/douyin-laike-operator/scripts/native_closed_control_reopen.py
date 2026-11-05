#!/usr/bin/env python3
"""One typed second toolbar press after own reload closed435 and restored434."""
import argparse,fcntl,importlib.util,json,time
from pathlib import Path
ROOT=Path('/Users/feibing/work/projects/zmaibaole');BASE=ROOT/'work/2026-10-23/sw17-v4-extension-maintenance'
FORMAL=ROOT/'skills/douyin-laike-operator/scripts/native_menu_control_maintenance.py';ALIAS=ROOT/'skills/douyin-laike-operator/scripts/native_blank_alias_continuation.py'
KIND='supervisor-closed-control-original-blank-reopen-v1'
def need(v,c):
 if not v:raise ValueError(c)
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def prove_return(m,before,after):
 bw,bt=m.tabs_map(before);aw,at=m.tabs_map(after);m.merchant(after,False)
 need(set(bw)==set(aw) and set(at)==set(bt)-{995698435} and 995698434 in at,'closed-control-exact-tab-removal')
 for k,w in bw.items():need({a:v for a,v in w.items() if a!='tabs'}=={a:v for a,v in aw[k].items() if a!='tabs'},'closed-control-window-changed')
 for k,t in at.items():
  expected=dict(bt[k])
  if k==995698434:expected['active']=True
  need(t==expected,'closed-control-other-tab-changed')
 need(bt[995698435]['url']==m.CONTROL and bt[995698435]['active'] is True and at[995698434]['url']=='chrome://newtab/' and at[995698434]['windowId']==995698278 and at[995698434]['active'] is True,'closed-control-original-blank')
 return at[995698434]
def validate(m,grant):
 g=m.read(grant);need(g.get('kind')==KIND and g.get('authorized') is True and g.get('actor')=='/root/violation_operator' and g.get('maintenance_only') is True,'root-closed-control-grant')
 need(g.get('helper')==m.ref(__file__) and g.get('formal_helper')==m.ref(FORMAL) and g['formal_helper']['sha256']=='824032448d9de5a3471f7dbbc022fcb83a405661988a365dd73d2ee8bd1733ff' and g.get('alias_helper')==m.ref(ALIAS) and g['alias_helper']['sha256']=='44dc20eb5db3bf2de65ff67d3e75b51fa0ed9cae134fb9229f459a3509e026eb','closed-control-helper-pins')
 need(g.get('toolbar_presses_max')==1 and type(g['toolbar_presses_max']) is int and g.get('total_toolbar_max')==2 and g.get('new_menu_or_update_allowed') is False and g.get('replay_unknown') is False,'closed-control-finite-cap')
 d=m.read(g['descriptor']);need(g['descriptor']==m.ref(BASE/'native-control-order.json') and m.prepare(d['ticket'],d['grant'])==d,'closed-control-original-descriptor')
 menu=m.read(g['menu_complete']);need(Path(g['menu_complete']['path'])==BASE/'new-blank-intent.json','closed-control-menu-ref');m.stage_intent(menu,g['descriptor'],d,BASE,'new-blank');need(menu['state']=='complete' and menu['result']['tabId']==995698434,'closed-control-original-menu')
 first=m.read(g['initial_complete']);need(Path(g['initial_complete']['path'])==BASE/'initial-toolbar-intent.json','closed-control-first-ref');m.stage_intent(first,g['descriptor'],d,BASE,'initial-toolbar');need(first['state']=='complete' and first['result']['tabId']==995698435,'closed-control-first-control')
 u=m.read(g['update_returned']);need(Path(g['update_returned']['path'])==BASE/'focus-space-update-intent.json' and u.get('kind')=='one-shot-public-AX-control-update-v1' and u.get('expected_pid')==d['pid']==86614 and u.get('control_url')==m.CONTROL and u.get('state')=='action-returned' and u.get('space_posted') is True,'closed-control-original-update')
 need(Path(g['returned_tabs_cli']['path'])==BASE/'15-reload-blank-tabs-cli.json','closed-control-original-tabs-ref');returned=m.cli_result(g['returned_tabs_cli'],{'op':'tabs'});prove_return(m,first['after_tabs'],returned)
 need(not (BASE/'reload-toolbar-intent.json').exists(),'closed-control-other-second-toolbar-intent')
 return d,returned
def execute(grant,request=None,native_factory=None):
 m=load(FORMAL,'original_closed_control_formal');d,returned=validate(m,grant);path=BASE/'closed-control-return-toolbar-intent.json'
 if request is None:
  import sys
  sys.path.insert(0,str(ROOT/'skills/chrome-dom-export/scripts'));import bridge;request=bridge.request
 def tabs(label):
  r=request({'op':'tabs'});p=BASE/('closed-control-return-'+label+'-'+str(time.time_ns())+'.json');m.durable(p,{'command':{'op':'tabs'},'reply':r,'at':m.now()});need(r.get('ok') is True and r.get('error') is None,'closed-control-tabs-failed');return r['result'],m.ref(p)
 def raw_ref(q,expected):
  need(Path(q['path']).parent==BASE.resolve(),'closed-control-raw-canonical-path');r=m.read(q);need(r.get('command')=={'op':'tabs'} and r.get('reply',{}).get('ok') is True and r['reply'].get('error') is None and r['reply']['result']==expected,'closed-control-raw-ref')
 def saved_guard(s):
  need(s.get('kind')=='closed-own-control-return-toolbar-once-v1' and s.get('grant')==grant and s.get('state') in ('unknown','complete') and type(s.get('input_count')) is int and s['input_count']==1 and s.get('before_tabs')==returned and s.get('old_active')==995698434,'closed-control-intent-schema')
  raw_ref(s['before_ref'],returned)
  if s['state']=='complete':raw_ref(s['after_ref'],s['after_tabs']);need(m.verify_delta(returned,s['after_tabs'],(m.CONTROL,),995698434)==s['result'],'closed-control-complete-delta')
 with (BASE/'.native-stages.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if path.exists():
   s=json.loads(path.read_text());saved_guard(s)
   if s['state']=='complete':return s
   after,rr=tabs('reconcile');s.update(after_tabs=after,after_ref=rr);m.durable(path,s);result=m.verify_delta(returned,after,(m.CONTROL,),995698434);s.update(state='complete',result=result,reconciled_readonly=True);m.durable(path,s);return s
  before,br=tabs('before');need(before==returned,'closed-control-fresh-tabs-changed')
  a=load(ALIAS,'original_closed_control_alias');factory=native_factory or a.alias_native(m.native_class(),'chrome://newtab/');n=None;s={'kind':'closed-own-control-return-toolbar-once-v1','grant':grant,'state':'preflight','before_tabs':before,'before_ref':br,'old_active':995698434,'input_count':0}
  try:
   n=factory(expected_pid=d['pid']);proof=n.scope();need(proof['pid']==86614 and proof['frontmost'] is True and proof['same_window'] is True and proof['active_url']=='chrome://newtab/' and proof['toolbar_targets']==1,'closed-control-native-blank-source')
   s.update(state='unknown',input_count=1,native_before=proof,intent_at=m.now());m.durable(path,s);n.open_control();s['action_returned_at']=m.now();m.durable(path,s)
   after,rr=tabs('after');s.update(after_tabs=after,after_ref=rr);m.durable(path,s);result=m.verify_delta(before,after,(m.CONTROL,),995698434);s.update(state='complete',result=result);m.durable(path,s);return s
  except Exception as e:s['error']=str(e);m.durable(path,s);raise
  finally:
   if n:n.close()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--grant',required=True);p.add_argument('--grant-sha256',required=True);a=p.parse_args();print(json.dumps(execute({'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'error':str(e),'replay_input':False}));raise SystemExit(2)
