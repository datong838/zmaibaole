#!/usr/bin/env python3
"""Only initial/reload toolbar on the original menu-created blank/control lineage."""
import argparse,importlib.util,json
from pathlib import Path
ROOT=Path('/Users/feibing/work/projects/zmaibaole');FORMAL=ROOT/'skills/douyin-laike-operator/scripts/native_menu_control_maintenance.py'
FORMAL_SHA='824032448d9de5a3471f7dbbc022fcb83a405661988a365dd73d2ee8bd1733ff'
BASE=ROOT/'work/2026-10-23/sw17-v4-extension-maintenance'
DESCRIPTOR={'path':str(BASE/'native-control-order.json'),'sha256':'6fa22429897b6a1878ff77b91a26f29d18e94aba50cbe686ed0480b10f8c1b95'}
DIAGNOSTIC={'path':str(BASE/'08-blank434-native-readonly-diagnostic.json'),'sha256':'85a206e86afd75d0e684bad4458950060c07d859dabe7e8110852508874c1cfd'}
BLANKS=('chrome://newtab/','chrome://new-tab-page/')
KIND='supervisor-native-blank-alias-continuation-v1'
def need(v,code):
 if not v:raise ValueError(code)
def load_formal():
 import hashlib
 need(hashlib.sha256(FORMAL.read_bytes()).hexdigest()==FORMAL_SHA,'original-formal-helper-changed')
 spec=importlib.util.spec_from_file_location('original_native_menu_maintenance',FORMAL);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def alias_native(original,browser_url):
 need(browser_url in BLANKS,'browser-blank-alias-required')
 class Native(original):
  def scope(self):
   proof=super().scope();raw=proof.get('active_url')
   if raw in BLANKS:
    proof=dict(proof,active_url_raw=raw,active_url_browser_canonical='chrome://newtab/',active_url=browser_url,normalization_rule='observed-chrome-newtab-AX-url-alias-v1')
   return proof
 return Native
def validate(m,grant):
 g=m.read(grant)
 need(g.get('kind')==KIND and g.get('authorized') is True and g.get('actor')=='/root/violation_operator' and g.get('maintenance_only') is True,'root-continuation-grant-required')
 need(g.get('adapter')==m.ref(__file__) and g.get('formal_helper')=={'path':str(FORMAL),'sha256':FORMAL_SHA} and g.get('descriptor')==DESCRIPTOR and g.get('diagnostic')==DIAGNOSTIC,'exact-continuation-pins')
 need(g.get('allowed_stages')==['initial-toolbar','reload-toolbar'] and g.get('menu_actions_allowed')==0 and g.get('original_blank_tab')==995698434 and g.get('replay_unknown') is False,'continuation-stage-boundary')
 d=m.read(DESCRIPTOR);need(m.prepare(d['ticket'],d['grant'])==d,'original-descriptor-validation');blank_ref=g['completed_menu_stage'];need(Path(blank_ref['path'])==BASE/'new-blank-intent.json','original-complete-menu-path');saved=m.read(blank_ref);m.stage_intent(saved,DESCRIPTOR,d,BASE,'new-blank')
 need(saved['state']=='complete' and saved['result']['tabId']==995698434 and saved['result']['windowId']==995698278 and saved['result']['url']=='chrome://newtab/','original-menu-created-blank-required')
 diagnostic=m.read(DIAGNOSTIC);p=diagnostic['maintenance_observe'];need(diagnostic['pid']==d['pid']==86614 and p['blank_verified'] is True and p['blank_url']=='chrome://new-tab-page/' and p['web_areas_count']==1 and diagnostic['input_count']==0,'actual-AX-blank-alias-evidence')
 return d
def execute(grant,stage,tabs_proof,update_ref=None):
 need(stage in ('initial-toolbar','reload-toolbar'),'continuation-no-menu-stage');m=load_formal();d=validate(m,grant)
 out=BASE/(stage+'-intent.json')
 if out.exists():
  # Old formal complete/unknown branches are read-only and need no blank still
  # active after a successfully delivered toolbar action. Never rebuild input.
  def no_native(**kwargs):raise ValueError('existing-stage-no-new-native-input')
  return m.run_stage(DESCRIPTOR,stage,tabs_proof,out,native_factory=no_native,update_ref=update_ref)
 before=m.cli_result(tabs_proof,{'op':'tabs'});_,rows=m.tabs_map(before);m.merchant(before)
 if stage=='initial-toolbar':target=995698434
 else:
  origin=m.read(m.ref(BASE/'initial-toolbar-intent.json'));m.stage_intent(origin,DESCRIPTOR,d,BASE,'initial-toolbar');need(origin['state']=='complete','original-initial-control-complete');target=origin['result']['tabId']
 need(target in rows and rows[target]['windowId']==995698278 and rows[target]['active'] is True and rows[target]['url'] in BLANKS,'continuation-original-active-blank')
 # Only the public native scope projection changes; all old stage/source/intent
 # guards, original toolbar implementation and real readbacks remain unchanged.
 return m.run_stage(DESCRIPTOR,stage,tabs_proof,out,native_factory=alias_native(m.native_class(),rows[target]['url']),update_ref=update_ref)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('grant','tabs-proof'):p.add_argument('--'+k,required=True);p.add_argument('--'+k+'-sha256',required=True)
 p.add_argument('--stage',choices=('initial-toolbar','reload-toolbar'),required=True);p.add_argument('--update-intent');p.add_argument('--update-intent-sha256');a=p.parse_args();q=lambda k:{'path':getattr(a,k.replace('-','_')),'sha256':getattr(a,k.replace('-','_')+'_sha256')}
 need(bool(a.update_intent)==bool(a.update_intent_sha256),'update-ref-pair')
 print(json.dumps(execute(q('grant'),a.stage,q('tabs-proof'),q('update-intent') if a.update_intent else None),ensure_ascii=False))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'error':str(e),'replay_input':False}));raise SystemExit(2)
