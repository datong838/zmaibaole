#!/usr/bin/env python3
"""One-shot AXPress of Chrome's blocked-popup toolbar button. No page AX reads.
Only the observed list button and bound record link are supported; never changes settings.
"""
import argparse
import ctypes as C
from datetime import datetime,timezone
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import tempfile
import time
from urllib.parse import urlsplit,parse_qs
spec=importlib.util.spec_from_file_location('chrome_shell_for_popup',Path(__file__).with_name('chrome-shell-diagnostic.py'))
shell=importlib.util.module_from_spec(spec);spec.loader.exec_module(shell)
AXError=shell.AXError
_spec_de=importlib.util.spec_from_file_location('dom_evidence_for_popup',Path(__file__).with_name('dom_evidence.py'))
dom_evidence=importlib.util.module_from_spec(_spec_de);_spec_de.loader.exec_module(dom_evidence)
LABEL='已拦截弹出式窗口'

def require(ok,code):
    if not ok:raise AXError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def atomic(path,value):
    fd,tmp=tempfile.mkstemp(prefix='.popup-intent-',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def focused_bridge_proof(path,pid,at=None):
    path=Path(path).resolve();require(path.is_file(),'bridge-focus-proof-missing');p=json.loads(path.read_text())
    require(p.get('source')=='local-dom-bridge' and p.get('expected_pid')==pid,'bridge-focus-source-pid-mismatch')
    try:age=((at or datetime.now(timezone.utc))-datetime.fromisoformat(str(p['observed_at']).replace('Z','+00:00'))).total_seconds()
    except Exception:raise AXError('bridge-focus-time-invalid')
    require(0<=age<=60,'bridge-focus-proof-stale-or-future')
    require(str(p.get('groupid','')).isdigit(),'bridge-focus-group-required')
    windows=[w for w in p.get('tabs',[]) if w.get('focused') is True]
    require(len(windows)==1,'bridge-focused-window-not-unique');window=windows[0]
    active=[t for t in window.get('tabs',[]) if t.get('active') is True];require(len(active)==1,'bridge-active-tab-not-unique');tab=active[0]
    require(window.get('windowId')==p.get('windowId')==tab.get('windowId') and tab.get('tabId')==p.get('tabId') and tab.get('allowed') is True,'bridge-focus-tab-window-mismatch')
    url=urlsplit(tab.get('url',''));require(url.scheme=='https' and url.netloc=='life.douyin.com' and parse_qs(url.query).get('groupid')==[str(p['groupid'])],'bridge-focus-group-origin-mismatch')
    require(tab.get('title'),'bridge-active-tab-title-missing')
    activation=p.get('activation',{})
    require(activation.get('tabId')==tab['tabId'] and activation.get('windowId')==window['windowId'] and activation.get('active') is True and activation.get('windowFocused') is True and activation.get('safety_version')==dom_evidence.VERSION and activation.get('url')==tab['url'],'bridge-activation-result-unverified')
    try:activation_age=((at or datetime.now(timezone.utc))-datetime.fromisoformat(str(activation['observedAt']).replace('Z','+00:00'))).total_seconds()
    except Exception:raise AXError('bridge-activation-time-invalid')
    require(0<=activation_age<=60,'bridge-activation-result-stale-or-future')
    return {'path':str(path),'sha256':sha(path),'tabId':tab['tabId'],'windowId':window['windowId'],'groupid':str(p['groupid']),'url':tab['url'],'title':tab['title'],'observed_at':p['observed_at']}

def public_business_query(q):
    # Only the two observed public merchant UI routing values are accepted.
    return not set(q)-{'groupid','life_biz_view_id','life_account_biz_ids'} and ('life_biz_view_id' not in q or q['life_biz_view_id']==['22']) and ('life_account_biz_ids' not in q or q['life_account_biz_ids']==[''])

def public_navigation_url(value):
    if not isinstance(value,str):return None
    try:
        u=urlsplit(value);q=parse_qs(u.query,keep_blank_values=True)
        if u.scheme!='https' or u.netloc!='life.douyin.com' or u.fragment or u.username or u.password or not public_business_query(q):return None
        if 'groupid' in q and (len(q['groupid'])!=1 or not q['groupid'][0].isdigit()):return None
        return value
    except Exception:return None

def public_shell_text(value):
    if not isinstance(value,str):return value
    return re.sub(r'https?://[^\s]+',lambda match:public_navigation_url(match.group(0)) or '[non-public navigation URL omitted]',value)

def flat(node):
    yield node
    if node.get('role')=='AXWebArea':return
    for child in node.get('children',[]):yield from flat(child)

def popup_target(snapshot,pid,title):
    require(snapshot.get('ok') is True and snapshot.get('pid')==pid and snapshot.get('bundle_id')=='com.google.Chrome' and snapshot.get('truncated') is False,'chrome-shell-snapshot-unverified')
    all_nodes=list(flat(snapshot['tree']))
    windows=[n for n in all_nodes if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXStandardWindow']
    main=[n for n in windows if n.get('AXMain') is True and n.get('AXMinimized') is not True]
    require(len(main)==1,'main-chrome-window-not-unique');window=main[0]
    titles=(title,title+' - Google Chrome')
    require(window.get('AXTitle') in titles,'main-window-active-tab-title-mismatch')
    buttons=[n for n in flat(window) if n.get('role')=='AXButton' and n.get('AXEnabled') is True and 'AXPress' in n.get('actions',[]) and (n.get('AXTitle') or n.get('AXDescription'))==LABEL and all(n.get(k) in (None,'',LABEL) for k in ('AXTitle','AXDescription'))]
    require(len(buttons)==1,'blocked-popup-button-not-unique')
    require(isinstance(buttons[0].get('path'),list) and isinstance(window.get('path'),list),'shell-path-missing')
    return window,buttons[0]

class PopupShellInspector(shell.ChromeShellInspector):
    def tree(self):
        # Deliberately does not reuse extension-maintenance traversal: every WebArea
        # is omitted without reading AXURL, text, actions or any descendants.
        self.by_path={};count=0;truncated=False;deadline=time.monotonic()+25
        def walk(element,path,depth):
            nonlocal count,truncated
            if depth>22 or count>=2500 or time.monotonic()>deadline:truncated=True;return None
            count+=1;self.by_path[tuple(path)]=element;row={'path':path,'role':self.get(element,'AXRole')}
            if row['role']=='AXWebArea':return {**row,'web_content_omitted':True,'children':[]}
            for key in ('AXMain','AXFocused','AXMinimized','AXTitle','AXDescription','AXIdentifier','AXSubrole','AXEnabled'):
                value=self.get(element,key)
                if value is not None:row[key]=public_shell_text(value)
            if row['role']=='AXLink':
                url=self.get(element,'AXURL');safe=public_navigation_url(url)
                if safe:row['AXURL']=safe
                elif url:row['AXURL_omitted']='non-public-navigation-url'
            if row['role']=='AXStaticText':
                key=self.string('AXValue');editable=C.c_bool()
                try:error=self.ax.AXUIElementIsAttributeSettable(element,key,C.byref(editable))
                finally:self.cf.CFRelease(key)
                if error==0 and not editable.value:
                    value=self.get(element,'AXValue')
                    if value is not None:row['AXValue']=public_shell_text(value)
            actions=C.c_void_p()
            if self.ax.AXUIElementCopyActionNames(element,C.byref(actions))==0 and actions.value:
                self.refs.append(actions.value);row['actions']=[self.decode(self.cf.CFArrayGetValueAtIndex(actions.value,i)) for i in range(self.cf.CFArrayGetCount(actions.value))]
            row['children']=[]
            for index,child in enumerate(self.array(element,'AXChildren')):
                result=walk(child,path+[index],depth+1)
                if result is not None:row['children'].append(result)
                if truncated:break
            return row
        root=walk(self.root,[],0)
        return {'ok':True,'bundle_id':'com.google.Chrome','pid':self.pid,'tree':root,'node_count':count,'truncated':truncated,'all_web_areas_omitted':True}
    def press(self,path,window_path):
        element=self.by_path[tuple(path)];window=self.by_path[tuple(window_path)]
        require(self.get(window,'AXMain') is True and self.get(element,'AXEnabled') is True,'main-window-or-button-changed')
        action=self.string('AXPress')
        try:error=self.ax.AXUIElementPerformAction(element,action)
        finally:self.cf.CFRelease(action)
        if error:raise AXError('blocked-popup-open-outcome-unknown:'+str(error))

def run_open_list(out,pid,focus_path,native_factory=PopupShellInspector,at=None):
    require(type(pid) is int and pid>0,'explicit-chrome-pid-required');out=Path(out).resolve();focus_path=Path(focus_path).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_name(out.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():
            previous=json.loads(out.read_text());require(previous.get('mode')=='open-list' and previous.get('expected_pid')==pid and previous.get('bridge_focus',{}).get('sha256')==sha(focus_path),'popup-intent-conflict')
            return {**previous,'replayed':False,'already_recorded':True}
        proof=focused_bridge_proof(focus_path,pid,at);native=native_factory(expected_pid=pid)
        try:
            require(native.pid==pid,'chrome-process-changed');before=native.tree();window,target=popup_target(before,pid,proof['title'])
            journal={'version':1,'mode':'open-list','state':'unknown','expected_pid':pid,'bridge_focus':proof,'target':{'window_path':window['path'],'path':target['path'],'label':LABEL},'intent_at':now(),'before':before,'settings_changed':False,'website_webarea_read':False,'replayed':False}
            atomic(out,journal) # Write-ahead intent precedes the sole AXPress.
            try:
                fresh=focused_bridge_proof(focus_path,pid,at)
                require(fresh['sha256']==proof['sha256'],'bridge-focus-proof-changed')
                native.press(target['path'],window['path']);journal['press_returned_success']=True
                journal['after']=native.tree();require(journal['after'].get('ok') is True and journal['after'].get('pid')==pid and journal['after'].get('truncated') is False,'after-shell-snapshot-unverified');journal['state']='complete';journal['completed_at']=now();atomic(out,journal)
            except Exception as error:
                journal['error']=str(error);journal['state']='unknown';atomic(out,journal);raise
            return journal
        finally:native.close()

POPUP_TITLE='已拦截弹出式窗口：'
RECORD_LABEL='•  life.douyin.com/p/fulfillsettle/…/20101?grou…'

def source_main(snapshot,pid,title):
    require(snapshot.get('ok') is True and snapshot.get('pid')==pid and snapshot.get('bundle_id')=='com.google.Chrome' and snapshot.get('truncated') is False,'chrome-shell-snapshot-unverified')
    main=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXStandardWindow' and n.get('AXMain') is True and n.get('AXMinimized') is not True]
    require(len(main)==1,'main-chrome-window-not-unique')
    require(main[0].get('AXTitle') in (title,title+' - Google Chrome'),'main-window-active-tab-title-mismatch');return main[0]

def record_link_target(snapshot,pid,title,groupid):
    main=source_main(snapshot,pid,title)
    popups=[n for n in flat(snapshot['tree']) if n.get('role')=='AXWindow' and n.get('AXSubrole')=='AXUnknown' and n.get('AXTitle')==POPUP_TITLE]
    require(len(popups)==1,'observed-popup-window-not-unique')
    links=[n for n in flat(popups[0]) if n.get('role')=='AXLink']
    require(len(links)==1,'observed-record-link-not-unique');link=links[0]
    require(link.get('AXTitle')==RECORD_LABEL and link.get('AXDescription')==RECORD_LABEL and link.get('AXEnabled') is True and 'AXPress' in link.get('actions',[]),'observed-record-link-changed')
    if link.get('AXURL'):
        require(record_url(link['AXURL'],groupid),'record-link-public-url-mismatch')
    require(not link.get('AXURL_omitted'),'record-link-url-not-public')
    return main,link

def record_url(value,groupid):
    try:
        u=urlsplit(value);q=parse_qs(u.query,keep_blank_values=True)
        return u.scheme=='https' and u.netloc=='life.douyin.com' and u.path.startswith('/p/fulfillsettle/') and '/export_records/' in u.path and u.path.rstrip('/').endswith('/20101') and public_business_query(q) and q.get('groupid')==[str(groupid)] and not u.fragment
    except Exception:return False

def bridge_tabs():
    spec=importlib.util.spec_from_file_location('popup_local_bridge',Path(__file__).resolve().parents[2]/'chrome-dom-export/scripts/bridge.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    reply=module.request({'op':'tabs'});require(reply.get('ok') is True,'post-navigation-tabs-unavailable');return reply['result']

def run_record_link(out,pid,focus_path,list_path,list_sha,native_factory=PopupShellInspector,tabs_reader=bridge_tabs,at=None):
    require(type(pid) is int and pid>0,'explicit-chrome-pid-required');out=Path(out).resolve();focus_path=Path(focus_path).resolve();list_path=Path(list_path).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    with out.with_name(out.name+'.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():
            previous=json.loads(out.read_text());require(previous.get('mode')=='open-record-link' and previous.get('expected_pid')==pid and previous.get('list_intent',{}).get('sha256')==list_sha and previous.get('bridge_focus',{}).get('sha256')==sha(focus_path),'popup-intent-conflict')
            return {**previous,'already_recorded':True,'replayed':False}
        require(list_path.is_file() and sha(list_path)==list_sha,'completed-list-intent-hash-mismatch')
        original=json.loads(list_path.read_text());require(original.get('mode')=='open-list' and original.get('state')=='complete' and original.get('expected_pid')==pid,'completed-list-intent-required')
        old=original.get('bridge_focus',{});proof=focused_bridge_proof(focus_path,pid,at)
        require(all(old.get(k)==proof[k] for k in ('tabId','windowId','groupid','url')),'record-link-source-scope-changed')
        _,observed=record_link_target(original['after'],pid,proof['title'],proof['groupid'])
        focus_data=json.loads(focus_path.read_text());before_ids={t.get('tabId') for w in focus_data['tabs'] for t in w.get('tabs',[])}
        native=native_factory(expected_pid=pid)
        try:
            require(native.pid==pid,'chrome-process-changed');before=native.tree();window,target=record_link_target(before,pid,proof['title'],proof['groupid'])
            require(target.get('AXTitle')==observed.get('AXTitle') and target.get('AXDescription')==observed.get('AXDescription'),'observed-record-link-changed')
            journal={'version':1,'mode':'open-record-link','state':'unknown','expected_pid':pid,'bridge_focus':proof,'list_intent':{'path':str(list_path),'sha256':list_sha},'target':{'window_path':window['path'],'path':target['path'],'label':RECORD_LABEL},'intent_at':now(),'before':before,'settings_changed':False,'website_webarea_read':False,'replayed':False}
            atomic(out,journal)
            try:
                fresh=focused_bridge_proof(focus_path,pid,at);require(fresh['sha256']==proof['sha256'] and sha(list_path)==list_sha,'navigation-proof-changed')
                native.press(target['path'],window['path']);journal['press_returned_success']=True;atomic(out,journal)
                tabs=tabs_reader();journal['post_tabs']=tabs
                candidates=[t for w in tabs for t in w.get('tabs',[]) if t.get('tabId') not in before_ids and t.get('allowed') is True and record_url(t.get('url',''),proof['groupid'])]
                require(len(candidates)==1,'new-record-tab-not-unique-or-unverified')
                journal['record_tab']=candidates[0];journal['state']='complete';journal['completed_at']=now();atomic(out,journal)
            except Exception as error:journal['error']=str(error);journal['state']='unknown';atomic(out,journal);raise
            return journal
        finally:native.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['open-list','open-record-link'],default='open-list');p.add_argument('--out',type=Path,required=True);p.add_argument('--expected-pid',type=int,required=True);p.add_argument('--bridge-focus',type=Path,required=True);p.add_argument('--list-intent',type=Path);p.add_argument('--list-intent-sha256');a=p.parse_args()
    try:
        if a.mode=='open-record-link':
            require(a.list_intent and a.list_intent_sha256,'completed-list-intent-and-hash-required')
            result=run_record_link(a.out,a.expected_pid,a.bridge_focus,a.list_intent,a.list_intent_sha256)
        else:result=run_open_list(a.out,a.expected_pid,a.bridge_focus)
        print(json.dumps({'ok':result['state']=='complete','state':result['state'],'out':str(a.out.resolve()),'replayed':False,'settings_changed':False},ensure_ascii=False));return 0 if result['state']=='complete' else 2
    except Exception as error:print(json.dumps({'ok':False,'error':str(error),'replayed':False,'settings_changed':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
