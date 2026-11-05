"""Program-owned capture focus events; no business click, URL change or new tab.
Prior tab activation stays immutable. Each unknown input stage is readonly-only;
a confirmed browser stage may precede one independently durable native stage.
"""
import sys,json,copy,fcntl,uuid,time,re,ctypes as C
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT/'skills/workshop-director/scripts'),str(ROOT/'skills/negative-review-complaints/scripts'),str(ROOT/'skills/chrome-dom-export/scripts'),str(ROOT/'skills/wecom-messenger/scripts')]
import complaint_execution_order as o
import initial_ledger_recovery as h
import review_capture_tab as previous
import native_window_capture as nw
from public_app_activation import PublicRunningApplication
from ax_capture_grant import NativeAction
FIELD=previous.FIELD;KIND='verified-review-native-preflight-recovery-v1';ERROR='native-window-frontmost-pid-title-mismatch'
def stamp():return datetime.now(timezone.utc).isoformat()
FRONT_SOURCE='public-expected-PID-AXFrontmost-and-CG-first-ordinary-v1'
def front_identity(pid,*,app_port=None,cg_port=None,ax_port=None):
    # NSWorkspace may be a per-process cached snapshot without a GUI runloop.
    # Keep it as diagnostic; AX+CG must independently agree for authority.
    port=app_port or PublicRunningApplication();ax=None
    try:
        app=port.identity(pid);diagnostic={}
        try:
            ws=port.send(port.objc.objc_getClass(b'NSWorkspace'),'sharedWorkspace',C.c_void_p);current=port.send(ws,'frontmostApplication',C.c_void_p);ns=port.send(current,'processIdentifier',C.c_int) if current else None
        except Exception as error:ns=None;diagnostic['nsworkspace_error']={'type':type(error).__name__,'message':str(error)}
        native=cg_port or nw.PublicCGWindow();process=nw.process_identity(native,pid);ax=ax_port or NativeAction(pid)
        if hasattr(ax,'frontmost_metadata'):attribute=ax.frontmost_metadata()
        else:
            name=ax.string('AXFrontmost');out=C.c_void_p()
            try:error=ax.ax.AXUIElementCopyAttributeValue(ax.root,name,C.byref(out))
            finally:ax.cf.CFRelease(name)
            if out.value:ax.refs.append(out.value)
            value=ax.decode(out.value) if error==0 and out.value and ax.cf.CFGetTypeID(out.value)==ax.cf.CFBooleanGetTypeID() else None
            attribute={'AX_error':int(error),'present':bool(out.value),'value':value}
        items=native.windows();normal=[w for w in items if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True];first=normal[0] if normal else None
        keys=('kCGWindowNumber','kCGWindowOwnerPID','kCGWindowOwnerName','kCGWindowLayer','kCGWindowIsOnscreen');public={k:first.get(k) for k in keys} if first else None
        if first and first.get('kCGWindowOwnerPID')==pid:public['kCGWindowName']=first.get('kCGWindowName')
        result={'application':app,**diagnostic,'frontmost_source':FRONT_SOURCE,'nsworkspace_frontmost_pid':ns,'expected_AXFrontmost':attribute,'CG_first_ordinary':public,'process':process,'frontmost_pid':None}
        try:result['frontmost_pid']=public_frontmost(result,pid)
        except ValueError as error:result['frontmost_error']=str(error)
        return result
    finally:
        if ax:ax.close()
        port.close()
def public_frontmost(observation,pid):
    a=observation['expected_AXFrontmost'];g=observation['CG_first_ordinary'];o.need(type(a.get('AX_error')) is int and a.get('AX_error')==0 and a.get('present') is True and type(a.get('value')) is bool,'capture-focus-public-AX-frontmost-unavailable');o.need(isinstance(g,dict) and type(g.get('kCGWindowOwnerPID')) is int and g['kCGWindowOwnerPID']>0 and type(g.get('kCGWindowNumber')) is int and g['kCGWindowNumber']>0 and g.get('kCGWindowLayer')==0 and g.get('kCGWindowIsOnscreen') is True,'capture-focus-public-CG-frontmost-unavailable');owner=g['kCGWindowOwnerPID'];o.need(a['value']==(owner==pid),'capture-focus-public-frontmost-evidence-conflict')
    if owner==pid:o.need(g.get('kCGWindowOwnerName')=='Google Chrome','capture-focus-public-CG-owner-name-mismatch')
    return owner

def activation_path(manifest):
    key=previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});return Path(manifest['source']['path']).parent/'.review-tab-activation'/(key+'.json')
def derive(manifest_ref,activation_ref,pid,*,archived_activation=None):
    o.need(type(pid) is int and pid>0,'capture-focus-explicit-pid');manifest=o.doc(manifest_ref);base=previous.derive(manifest_ref);activation=o.doc(activation_ref) if archived_activation is None else archived_activation
    o.need(Path(activation_ref['path'])==activation_path(manifest) and activation['kind']=='review-capture-tab-activation-v1' and activation['binding']==base and activation['state']=='complete' and len(activation['calls'])<=1,'capture-focus-original-complete-activation')
    if activation['calls']:
        call=activation['calls'][0];o.need(call['key']=='original-management-tab-once' and call['state']=='confirmed' and call['phase']=='frames' and call['command']=={'op':'activate','tabId':base['scope']['tabId']},'capture-focus-original-confirmed-call')
    reads=[o.doc(r) for r in activation['reads']];tabs=[r for r in reads if r['command']=={'op':'tabs'} and r.get('response',{}).get('ok') is True];o.need(tabs and previous.classify(tabs[-1]['response']['result'],base)=='active','capture-focus-original-active-proof')
    return {'manifest':manifest_ref,'activation':activation_ref,'pid':pid,'scope':base['scope'],'url':base['url'],'identity':base['identity'],'source':manifest['source']}
def browser_binding(binding):return {'scope':binding['scope'],'url':binding['url'],'original_record_tab':{'tabId':-1,'windowId':binding['scope']['windowId'],'url':'not-eligible-for-focus-restore'}}
def qualify(observation,binding):
    if 'frontmost_source' in observation:
        o.need(observation['frontmost_source']==FRONT_SOURCE and public_frontmost(observation,binding['pid'])==observation['frontmost_pid'],'capture-focus-fresh-frontmost-authority-mismatch')
    o.need(observation['application']=={'pid':binding['pid'],'bundle':'com.google.Chrome','terminated':False} and type(observation['frontmost_pid']) is int and observation['frontmost_pid']>0,'capture-focus-app-identity-unverified')
    when=datetime.fromisoformat(observation['observed_at']);o.need(when.utcoffset() is not None,'capture-focus-aware-observation-required')
    raw=o.doc(observation['tabs_reply']);o.need(raw.get('command')=={'op':'tabs'} and raw.get('response',{}).get('ok') is True and raw['response'].get('result')==observation['tabs'] and datetime.fromisoformat(raw['observed_at'])<=when,'capture-focus-observation-raw-binding')
    status=previous.classify(observation['tabs'],browser_binding(binding));o.need(status in ('active','target-active-window-unfocused'),'capture-focus-original-tab-not-active')
    native=observation['frontmost_pid']==binding['pid']
    if status=='active' and native:
        if 'frontmost_source' in observation:
            window=next(w for w in observation['tabs'] if w.get('windowId')==binding['scope']['windowId']);target=next(t for t in window['tabs'] if t.get('tabId')==binding['scope']['tabId'])
            title=target.get('title');o.need(isinstance(title,str) and 0<len(title)<800,'capture-focus-target-title-unavailable')
            if not nw.chrome_window_title(observation['CG_first_ordinary'].get('kCGWindowName'),title):return 'page-window-focus-loss'
        return 'ready'
    o.need(not native,'capture-focus-not-proven-external-change');return 'external-focus-loss'
def native_admission(observation,binding):
    status=previous.classify(observation['tabs'],browser_binding(binding))
    return qualify(observation,binding)=='external-focus-loss' and (status=='active' or (status=='target-active-window-unfocused' and all(w.get('focused') is False for w in observation['tabs'])))

def activate_original_chrome(pid,port=None,process=None):
    # This is not WeCom's fixed-bundle activate_existing wrapper. No launch.
    o.need(type(pid) is int and pid>0,'capture-focus-native-explicit-pid')
    native=process or nw.PublicCGWindow();identity=nw.process_identity(native,pid);port=port or PublicRunningApplication()
    try:
        actual=port.identity(pid);o.need(actual=={'pid':pid,'bundle':'com.google.Chrome','terminated':False},'capture-focus-native-app-identity-mismatch');accepted=port.activate();o.need(accepted is True,'capture-focus-native-activation-rejected');return {'pid':pid,'bundle':'com.google.Chrome','process':identity,'request_accepted':True,'frontmost_verified':False,'launch_used':False}
    finally:port.close()
def validate_events(state,binding):
    for r in state.get('reads',[]):o.doc(r)
    for i,event in enumerate(state['events']):
        o.need(event['number']==i+1 and event['binding']==binding and event['state'] in ('preflight','unknown','complete') and len(event['calls'])<=1 and event['phase']=='capture-focus' and event['revision']==0,'capture-focus-event-chain')
        before=o.doc(event['before']);o.need(qualify(before,binding) in ('external-focus-loss','page-window-focus-loss'),'capture-focus-event-without-external-change');created=datetime.fromisoformat(event['created_at']);o.need(datetime.fromisoformat(before['observed_at'])<=created,'capture-focus-before-event-time');o.need(event['state']!='unknown' or bool(event['calls']),'capture-focus-unknown-without-original-intent')
        if i<len(state['events'])-1:o.need(event['state']=='complete','capture-focus-earlier-unknown')
        if event['calls']:
            call=event['calls'][0];o.need(call['key']=='capture-focus:'+str(i+1) and call['command']=={'op':'activate','tabId':binding['scope']['tabId']} and call['state'] in ('unknown','confirmed') and call['phase']=='capture-focus' and created<=datetime.fromisoformat(call['at']),'capture-focus-original-event-intent')
            if call['state']=='confirmed':
                result=call['result']
                if result.get('observed') is True:o.need(result.get('proof')==event.get('after'),'capture-focus-reconciled-call-proof')
                else:
                    reply=o.doc(event['reply']);o.need(event['reply'] in state['reads'] and reply['command']==call['command'] and reply['response'].get('ok') is True and reply['response']['result']==result and all(result.get(k)==v for k,v in {'tabId':binding['scope']['tabId'],'windowId':binding['scope']['windowId'],'url':binding['url'],'active':True,'windowFocused':True}.items()),'capture-focus-confirmed-call-raw-binding')
        validate_window_stage(event,binding)
        native=event.get('native_focus')
        if native:
            o.need(len(event['calls'])==1 and event['calls'][0]['state']=='confirmed' and native['state'] in ('unknown','complete') and native['binding']==binding and native.get('action')=='activate-existing-Chrome-PID-only','capture-focus-native-intent-binding');before=o.doc(native['before']);o.need(native_admission(before,binding) and datetime.fromisoformat(before['observed_at'])<=datetime.fromisoformat(native['intent_at']),'capture-focus-native-before-scope')
            if native.get('reply'):
                reply=o.doc(native['reply']);o.need(reply['binding']==binding and reply['intent_at']==native['intent_at'],'capture-focus-native-reply-binding')
                if 'result' in reply:o.need(reply['result'].get('request_accepted') is True and reply['result'].get('pid')==binding['pid'] and reply['result'].get('bundle')=='com.google.Chrome' and reply['result'].get('launch_used') is False,'capture-focus-native-result-binding')
                if 'result' in reply and native.get('window_fallback'):o.need(reply['result'].get('process')==o.doc(native['before'])['process'],'capture-window-native-result-process-changed')
            if native['state']=='complete':
                after=o.doc(native['after']);o.need(qualify(after,binding)=='ready' and datetime.fromisoformat(native['intent_at'])<=datetime.fromisoformat(after['observed_at'])<=datetime.fromisoformat(native['completed_at']),'capture-focus-native-effect-proof')
        if event['state']=='complete':
            after=o.doc(event['after']);o.need(qualify(after,binding)=='ready' and created<=datetime.fromisoformat(after['observed_at'])<=datetime.fromisoformat(event['completed_at']),'capture-focus-prior-completion-proof');o.need(not event['calls'] or event['calls'][0]['state']=='confirmed','capture-focus-complete-call-unconfirmed');o.need(not native or native['state']=='complete','capture-focus-native-outcome-unresolved')

WINDOW_ACTION='AXRaise-exact-existing-Chrome-window-v1'
def window_scope(binding,observation):
    windows=[w for w in observation['tabs'] if w.get('windowId')==binding['scope']['windowId']]
    o.need(len(windows)==1,'capture-window-browser-window-not-unique');tabs=[t for t in windows[0]['tabs'] if t.get('tabId')==binding['scope']['tabId']]
    o.need(len(tabs)==1 and tabs[0].get('url')==binding['url'] and tabs[0].get('active') is True,'capture-window-browser-tab-mismatch')
    return {**binding['scope'],'pid':binding['pid'],'url':binding['url'],'title':tabs[0]['title']}
class ExactWindowRaise:
    """Unique public AXMain URL/title; CG frame is verification only. No page contents."""
    def __init__(self,pid,*,ax=None,cg=None):
        from native_region_capture import Geometry
        self.ax=ax or Geometry(pid);self.cg=cg or nw.PublicCGWindow();self.pid=pid;self.window=None
    def close(self):self.ax.close()
    def locate(self,scope):
        a=self.ax;o.need(scope['pid']==self.pid and a.get(a.root,'AXFrontmost') is True,'capture-window-Chrome-not-frontmost')
        matches=[];count=0;mains=[w for w in a.children(a.root,'AXWindows') if a.get(w,'AXMain') is True];o.need(len(mains)==1,'capture-window-AXMain-not-unique')
        for w in mains:
            if a.get(w,'AXRole')!='AXWindow' or a.get(w,'AXSubrole')!='AXStandardWindow' or a.get(w,'AXMinimized') is not False or not nw.chrome_window_title(a.get(w,'AXTitle'),scope['title']):continue
            urls=[]
            def walk(e,depth):
                nonlocal count
                count+=1;o.need(count<=2500 and depth<=24,'capture-window-outer-tree-incomplete')
                if a.get(e,'AXRole')=='AXWebArea':
                    if a.url(e)==scope['url']:urls.append(e)
                    return
                for c in a.children(e):walk(c,depth+1)
            walk(w,0)
            if len(urls)==1:matches.append(w)
            else:o.need(not urls,'capture-window-WebArea-not-unique')
        o.need(len(matches)==1,'capture-window-exact-URL-title-not-unique');self.window=matches[0]
        main=a.raw(a.root,'AXMainWindow')
        o.need(main and a.cf.CFEqual(main,self.window),'capture-window-AXMainWindow-mismatch')
        document=a.raw(self.window,'AXDocument')
        if document:
            value=a.decode(a.cf.CFURLGetString(document)) if a.cf.CFGetTypeID(document)==a.cf.CFURLGetTypeID() else a.decode(document)
            o.need(value==scope['url'],'capture-window-AXDocument-mismatch')
        frame=a.frame(self.window)
        import math
        o.need(set(frame)=={'x','y','width','height'} and all(type(v) in (int,float) and math.isfinite(v) for v in frame.values()) and frame['width']>0 and frame['height']>0,'capture-window-invalid-frame')
        items=self.cg.windows();found=[]
        for w in items:
            b=w.get('kCGWindowBounds',{});keys={'x':'X','y':'Y','width':'Width','height':'Height'}
            if w.get('kCGWindowOwnerPID')==self.pid and w.get('kCGWindowOwnerName')=='Google Chrome' and w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True and nw.chrome_window_title(w.get('kCGWindowName'),scope['title']) and all(type(b.get(v)) in (int,float) and abs(frame[k]-b[v])<=.001 for k,v in keys.items()):found.append(w)
        o.need(found and all(type(w.get('kCGWindowNumber')) is int and w['kCGWindowNumber']>0 for w in found),'capture-window-AX-CG-frame-unverified')
        if hasattr(a,'actions'):actions=a.actions(self.window)
        else:
            out=C.c_void_p();error=a.ax.AXUIElementCopyActionNames(self.window,C.byref(out));o.need(error==0 and out.value and a.cf.CFGetTypeID(out.value)==a.cf.CFArrayGetTypeID(),'capture-window-actions-unavailable');a.refs.append(out.value);actions=[a.decode(a.cf.CFArrayGetValueAtIndex(out.value,i)) for i in range(a.cf.CFArrayGetCount(out.value))]
        o.need(isinstance(actions,list) and len(actions)<=32 and actions.count('AXRaise')==1,'capture-window-AXRaise-unavailable')
        return {'scope':scope,'CG_frame_verified':True,'AX_main_verified':True,'AX_frame':frame,'AX_role':'AXWindow','AX_subrole':'AXStandardWindow','AX_url':scope['url'],'action':WINDOW_ACTION,'webarea_contents_read':False}
    def raise_once(self,scope,target):
        o.need(self.locate(scope)==target,'capture-window-target-changed-before-raise');a=self.ax
        if hasattr(a,'raise_window'):error=a.raise_window(self.window)
        else:
            name=a.string('AXRaise')
            try:error=a.ax.AXUIElementPerformAction(self.window,name)
            finally:a.cf.CFRelease(name)
        o.need(type(error) is int and error==0,'capture-window-AXRaise-error')
        return {'target':target,'request_accepted':True,'effect_verified':False,'launch_used':False}
    def effect(self,scope,target,observation):
        o.need(self.locate(scope)==target,'capture-window-effect-target-changed');a=self.ax;main=a.raw(a.root,'AXMainWindow')
        o.need(main and a.cf.CFEqual(main,self.window) and a.get(self.window,'AXMain') is True,'capture-window-effect-AXMain-mismatch')
        focused=a.raw(a.root,'AXFocusedWindow');o.need(focused and a.cf.CFEqual(focused,self.window),'capture-window-effect-AXFocusedWindow-mismatch')
        first=observation['CG_first_ordinary'];normal=[w for w in self.cg.windows() if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True];o.need(normal,'capture-window-effect-no-CG-window');actual=normal[0];b=actual.get('kCGWindowBounds',{});keys={'x':'X','y':'Y','width':'Width','height':'Height'}
        o.need(first['kCGWindowNumber']==actual.get('kCGWindowNumber') and actual.get('kCGWindowOwnerPID')==first['kCGWindowOwnerPID']==self.pid and actual.get('kCGWindowOwnerName')=='Google Chrome' and nw.chrome_window_title(actual.get('kCGWindowName'),scope['title']) and nw.chrome_window_title(first.get('kCGWindowName'),scope['title']) and all(type(b.get(v)) in (int,float) and abs(target['AX_frame'][k]-b[v])<=.001 for k,v in keys.items()),'capture-window-effect-CG-mismatch')
        return {'target':target,'CG_first_id':first['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False}
def validate_window_stage(event,binding):
    stage=event.get('window_focus')
    if stage is None:return
    coexist=bool(event.get('native_focus',{}).get('window_fallback'))
    if coexist:validate_window_native_admission(event,binding)
    o.need((not event.get('native_focus') or coexist) and event['calls'] and event['calls'][0]['state']=='confirmed' and stage['binding']==binding and stage['state'] in ('unknown','complete') and stage['action']==WINDOW_ACTION,'capture-window-stage-binding')
    before=o.doc(stage['before']);scope=window_scope(binding,before);target=stage['target']
    o.need(set(target)=={'scope','CG_frame_verified','AX_main_verified','AX_frame','AX_role','AX_subrole','AX_url','action','webarea_contents_read'} and target['CG_frame_verified'] is True and target['AX_main_verified'] is True and target['AX_role']=='AXWindow' and target['AX_subrole']=='AXStandardWindow' and set(target['AX_frame'])=={'x','y','width','height'} and all(type(v) in (int,float) and __import__('math').isfinite(v) for v in target['AX_frame'].values()) and target['AX_frame']['width']>0 and target['AX_frame']['height']>0,'capture-window-target-contract')
    o.need(qualify(before,binding)=='page-window-focus-loss' and before['CG_first_ordinary'].get('kCGWindowName')=='近期的下载记录' and target['scope']==scope and target['AX_url']==binding['url'] and target['action']==WINDOW_ACTION and target['webarea_contents_read'] is False and datetime.fromisoformat(before['observed_at'])<=datetime.fromisoformat(stage['intent_at']),'capture-window-stage-before')
    if stage.get('reply'):
        reply=o.doc(stage['reply']);o.need(reply['binding']==binding and reply['intent_at']==stage['intent_at'],'capture-window-stage-reply')
        if 'result' in reply:o.need(reply['result']=={'target':target,'request_accepted':True,'effect_verified':False,'launch_used':False},'capture-window-stage-result')
    for check_ref in stage.get('effect_checks',[]):
        check=o.doc(check_ref);required={'kind','number','binding','intent_at','target','observation','classification','input_performed'}
        o.need(set(check)in (required|{'effect'},required|{'effect_error'},required|{'effect_error','panel_dismiss'})and check['kind']=='capture-window-readonly-effect-check-v1'and type(check['number'])is int and 1<=check['number']<=3 and check['binding']==binding and check['intent_at']==stage['intent_at']and check['target']==target and check['input_performed']is False,'capture-window-effect-check-binding')
        observation=o.doc(check['observation']);o.need(datetime.fromisoformat(stage['intent_at'])<=datetime.fromisoformat(observation['observed_at'])and check['classification']==qualify(observation,binding)and window_scope(binding,observation)==scope,'capture-window-effect-check-observation')
        if 'effect'in check:o.need(check['effect']=={'target':target,'CG_first_id':observation['CG_first_ordinary']['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False},'capture-window-effect-check-result')
        else:
            o.need(type(check['effect_error'])is str and 0<len(check['effect_error'])<256,'capture-window-effect-check-error')
            if 'panel_dismiss' in check:
                dismiss=check['panel_dismiss'];o.need(type(dismiss)is dict and set(dismiss)=={'kind','intent','outcome'} and dismiss['kind']=='chrome-download-panel-escape-dismiss-v1','capture-window-panel-dismiss-binding')
                intent=o.doc(dismiss['intent']);o.need(intent.get('kind')=='chrome-download-panel-escape-intent-v1' and intent.get('pid')==binding['pid'] and (intent.get('panel') or {}).get('kCGWindowName')=='近期的下载记录' and (intent.get('panel') or {}).get('kCGWindowOwnerPID')==binding['pid'],'capture-window-panel-dismiss-intent')
                outcome=o.doc(dismiss['outcome']);o.need(outcome.get('kind')=='chrome-download-panel-escape-outcome-v1' and outcome.get('intent')==dismiss['intent'] and type(outcome.get('panel_gone'))is bool,'capture-window-panel-dismiss-outcome')
    if stage['state']=='complete':
        after=o.doc(stage['after']);effect=o.doc(stage['effect']);o.need(qualify(after,binding)=='ready' and effect=={'target':target,'CG_first_id':after['CG_first_ordinary']['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False} and datetime.fromisoformat(stage['intent_at'])<=datetime.fromisoformat(after['observed_at'])<=datetime.fromisoformat(stage['completed_at']),'capture-window-stage-effect')
    o.need(event['state']!='complete' or stage['state']=='complete' or (coexist and event['native_focus']['state']=='complete'),'capture-window-outcome-unresolved')

PANEL_TITLE='近期的下载记录'
def _panel_first(pid,cg_factory):
    cg=(cg_factory or nw.PublicCGWindow)()
    try:
        normal=[w for w in cg.windows() if w.get('kCGWindowLayer')==0 and w.get('kCGWindowIsOnscreen') is True and w.get('kCGWindowOwnerPID')==pid]
        return dict(normal[0]) if normal else None
    finally:
        close=getattr(cg,'close',None)
        if close:close()
def _panel_shell(pid):
    import importlib.util
    spec=importlib.util.spec_from_file_location('chrome_shell_diagnostic',ROOT/'skills/douyin-laike-operator/scripts/chrome-shell-diagnostic.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.ChromeShellInspector(pid)
def dismiss_download_panel(pid,observation,rawdir,*,shell_factory=None,cg_factory=None,sleeper=None):
    """One durable Escape closing Chrome's own download panel blocking CG first.

    AXRaise on the page window cannot lift it above this child panel (B81), so
    the only bounded, semantic escape is the panel's own dismiss key. Guards:
    fresh CG evidence of this exact panel first, Chrome frontmost, one AX
    window by this title, no sheets. The Escape is posted to the Chrome pid
    only; no business page input, no coordinates, no capture, bounded wait.
    Evidence is immutable before and after; a surviving panel keeps the stage
    fail-closed.
    """
    o.need(type(pid) is int and pid>0,'panel-dismiss-pid');panel=observation.get('CG_first_ordinary') or {}
    o.need(panel.get('kCGWindowName')==PANEL_TITLE and panel.get('kCGWindowOwnerPID')==pid,'panel-dismiss-panel-not-first')
    rawdir=Path(rawdir);n=(shell_factory or _panel_shell)(pid)
    try:
        o.need(n.get(n.root,'AXFrontmost') is True,'panel-dismiss-chrome-not-frontmost')
        windows=[w for w in n.array(n.root,'AXWindows') if n.get(w,'AXTitle')==PANEL_TITLE]
        o.need(len(windows)==1,'panel-dismiss-panel-not-unique');w=windows[0]
        o.need(not n.array(w,'AXSheets'),'panel-dismiss-sheet-present')
        intent=o.immutable(rawdir/('download-panel-escape-intent-'+uuid.uuid4().hex+'.json'),{'kind':'chrome-download-panel-escape-intent-v1','pid':pid,'panel':{'kCGWindowNumber':panel.get('kCGWindowNumber'),'kCGWindowOwnerPID':pid,'kCGWindowName':PANEL_TITLE,'kCGWindowBounds':panel.get('kCGWindowBounds')},'observed_at':stamp()})
        for down in (True,False):
            event=n.cg.CGEventCreateKeyboardEvent(None,53,down);o.need(event is not None,'panel-dismiss-escape-event-unavailable')
            try:n.cg.CGEventPostToPid(pid,event)
            finally:n.cf.CFRelease(event)
        (sleeper or time.sleep)(.15);gone_at=None;deadline=time.monotonic()+1.2
        while True:
            after=_panel_first(pid,cg_factory)
            if after is None or after.get('kCGWindowName')!=PANEL_TITLE:gone_at=stamp();break
            if time.monotonic()>=deadline:break
            (sleeper or time.sleep)(.1)
        outcome=o.immutable(rawdir/('download-panel-escape-outcome-'+uuid.uuid4().hex+'.json'),{'kind':'chrome-download-panel-escape-outcome-v1','intent':intent,'panel_gone':gone_at is not None,'panel_gone_at':gone_at,'observed_at':stamp()})
        return {'kind':'chrome-download-panel-escape-dismiss-v1','intent':intent,'outcome':outcome}
    finally:n.close()

def settle_window_effect(port,stage,binding,current,current_ref,observe,record,*,clock=None,sleeper=None,max_observations=3,panel_dismiss=None):
    """Only readonly AX/CG+exact-tab evidence. Never dispatch/redo AXRaise.

    Up to three observations, with a two-second next-poll-start budget. An
    in-flight observation retains its existing timeout; this is not a hard
    end-to-end two-second limit. Accepted AXRaise is never effect authority.
    """
    o.need(type(max_observations)is int and 1<=max_observations<=3,'capture-window-bounded-effect-observations');clock=clock or time.monotonic;sleeper=sleeper or time.sleep;started=clock()
    transient={'capture-window-effect-AXFocusedWindow-mismatch','capture-window-effect-AXMain-mismatch','capture-window-effect-CG-mismatch','capture-window-Chrome-not-frontmost'}
    dismissed=False
    for index in range(max_observations):
        # The current pre-dispatch sample cannot prove a later action's effect.
        if index or datetime.fromisoformat(current['observed_at'])<datetime.fromisoformat(stage['intent_at']):
            if index and clock()-started>=2:break
            if index:sleeper(.05)
            current,current_ref=observe()
        status=qualify(current,binding);scope=window_scope(binding,current)
        o.need(scope==stage['target']['scope'],'capture-window-effect-scope-changed')
        attempt={'kind':'capture-window-readonly-effect-check-v1','number':index+1,'binding':binding,'intent_at':stage['intent_at'],'target':stage['target'],'observation':current_ref,'classification':status,'input_performed':False}
        try:effect=port.effect(scope,stage['target'],current)
        except ValueError as error:
            attempt['effect_error']=str(error)
            panel=current.get('CG_first_ordinary') or {}
            # B81: AXRaise never lifts the page window above Chrome's own child
            # download panel, so a CG-mismatch whose front window is exactly
            # this panel gets one bounded Escape dismiss per settlement.
            if panel_dismiss is not None and not dismissed and str(error)=='capture-window-effect-CG-mismatch' and panel.get('kCGWindowName')==PANEL_TITLE and panel.get('kCGWindowOwnerPID')==binding['pid']:
                dismissed=True;attempt['panel_dismiss']=panel_dismiss(current)
            record(attempt)
            if str(error)not in transient:raise
        else:
            expected={'target':stage['target'],'CG_first_id':current['CG_first_ordinary']['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False}
            o.need(effect==expected,'capture-window-effect-contract')
            # AXMain/AXFocused alone cannot authorize capture while a panel is
            # still first in CG or while the original browser scope is not ready.
            attempt['effect']=effect;record(attempt)
            if status=='ready':return current,current_ref,effect
        if clock()-started>=2:break
    raise ValueError('capture-window-unknown-readonly-no-replay')

WINDOW_NATIVE_FALLBACK='independent-native-after-unverified-AXRaise-v1'
def window_native_admission(event,binding,first_ref,second_ref):
    stage=event.get('window_focus');o.need(stage and stage['state']=='unknown' and stage['binding']==binding and stage['action']==WINDOW_ACTION and not event.get('native_focus') and len(event['calls'])==1 and event['calls'][0]['state']=='confirmed','capture-window-native-original-stage')
    reply=o.doc(stage['reply']);o.need(reply.get('binding')==binding and reply.get('intent_at')==stage['intent_at'] and reply.get('result')=={'target':stage['target'],'request_accepted':True,'effect_verified':False,'launch_used':False},'capture-window-native-accepted-only')
    first=o.doc(first_ref);second=o.doc(second_ref)
    for observation in (first,second):
        o.need(observation.get('frontmost_source')==FRONT_SOURCE and observation.get('expected_AXFrontmost',{}).get('value') is False and native_admission(observation,binding) and window_scope(binding,observation)==stage['target']['scope'],'capture-window-native-negative-effect-scope')
    o.need(first.get('process')==second.get('process')==o.doc(stage['before']).get('process') and first.get('process')is not None,'capture-window-native-process-changed')
    a=first['CG_first_ordinary'];b=second['CG_first_ordinary'];o.need(first['frontmost_pid']==second['frontmost_pid']!=binding['pid'] and a['kCGWindowNumber']==b['kCGWindowNumber'] and a['kCGWindowOwnerPID']==b['kCGWindowOwnerPID'] and a.get('kCGWindowOwnerName')==b.get('kCGWindowOwnerName'),'capture-window-native-external-front-changed')
    t0=datetime.fromisoformat(stage['intent_at']);t1=datetime.fromisoformat(first['observed_at']);t2=datetime.fromisoformat(second['observed_at']);o.need(t0<=t1<=t2 and 0<=(t2-t1).total_seconds()<=30,'capture-window-native-admission-time')
    return {'kind':WINDOW_NATIVE_FALLBACK,'binding':binding,'window_stage':copy.deepcopy(stage),'observations':[first_ref,second_ref],'previous_action_outcome':'unknown-preserved','history_certified':False}
def validate_native_readonly_hold(reference,binding,stage,observation_ref):
    proof=o.doc(reference);keys={'kind','binding','window_stage','observation','attempts','error','input_performed'}
    o.need(set(proof)==keys and proof['kind']=='independent-native-readonly-window-hold-v1'and proof['binding']==binding and proof['window_stage']==stage and proof['observation']==observation_ref and proof['error']=='capture-window-unknown-readonly-no-replay'and proof['input_performed']is False,'capture-native-readonly-hold-binding')
    observation=o.doc(observation_ref);o.need(qualify(observation,binding)=='external-focus-loss'and window_scope(binding,observation)==stage['target']['scope'],'capture-native-readonly-hold-negative-scope')
    o.need(len(proof['attempts'])==1 and Path(reference['path']).parent==Path(observation_ref['path']).parent,'capture-native-one-readonly-settlement')
    attempt=o.doc(proof['attempts'][0]);expected={'kind':'capture-window-readonly-effect-check-v1','number':1,'binding':binding,'intent_at':stage['intent_at'],'target':stage['target'],'observation':observation_ref,'classification':'external-focus-loss','input_performed':False}
    o.need({k:v for k,v in attempt.items()if k!='effect_error'}==expected and attempt.get('effect_error')in {'capture-window-effect-AXFocusedWindow-mismatch','capture-window-effect-AXMain-mismatch','capture-window-effect-CG-mismatch','capture-window-Chrome-not-frontmost'}and Path(proof['attempts'][0]['path']).parent==Path(reference['path']).parent,'capture-native-readonly-effect-not-observed')
    return proof

def validate_window_native_admission(event,binding):
    native=event.get('native_focus');proof=native.get('window_fallback') if native else None
    o.need(native.get('key')=='capture-native-after-window:'+str(event['number']),'capture-window-native-independent-intent-key')
    o.need(proof and set(proof)=={'kind','binding','window_stage','observations','previous_action_outcome','history_certified'} and proof['kind']==WINDOW_NATIVE_FALLBACK and len(proof['observations'])==2,'capture-window-native-fallback-proof')
    intent=o.doc(native['stage_intent']);expected_stage={k:native[k]for k in ('binding','before','intent_at','action','window_fallback','readonly_hold','key')};expected_stage['state']='unknown'
    o.need(intent=={'kind':'independent-native-stage-intent-v1','event_number':event['number'],'window_stage':event['window_focus'],'native_stage':expected_stage} and Path(native['stage_intent']['path']).parent==Path(native['before']['path']).parent,'capture-window-native-durable-stage-intent')
    validate_native_readonly_hold(native['readonly_hold'],binding,event['window_focus'],proof['observations'][0]);original=copy.deepcopy(event);original.pop('native_focus',None);expected=window_native_admission(original,binding,*proof['observations']);o.need(proof==expected and native['before']==proof['observations'][-1] and datetime.fromisoformat(o.doc(native['before'])['observed_at'])<=datetime.fromisoformat(native['intent_at']),'capture-window-native-proof-binding')
    if native['state']=='complete':
        observed=o.doc(native['after']);effect=o.doc(native['window_effect']);o.need(qualify(observed,binding)=='ready' and window_scope(binding,observed)==event['window_focus']['target']['scope'] and effect=={'target':event['window_focus']['target'],'CG_first_id':observed['CG_first_ordinary']['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False},'capture-window-native-exact-window-effect')

class Focus:
    def __init__(self,path,state,event,binding,request,raw):self.path=path;self.state=state;self.s=event;self.binding=binding;self.request=request;self.raw=raw
    def save(self):previous.overlay.rc.atomic(self.path,self.state)
    def call(self,command):
        o.need(command=={'op':'activate','tabId':self.binding['scope']['tabId']},'capture-focus-only-original-tab');reply=self.raw(command,'activate');self.s['reply']=self.state['reads'][-1];self.save();o.need(reply.get('ok') is True,'capture-focus-activate-failed');result=reply['result'];o.need(all(result.get(k)==v for k,v in {'tabId':self.binding['scope']['tabId'],'windowId':self.binding['scope']['windowId'],'url':self.binding['url'],'active':True,'windowFocused':True}.items()),'capture-focus-activate-result-mismatch');return result
    def once(self,command):return previous.operator_primitives().once(self,command,intent_key='capture-focus:'+str(self.s['number']))
def ensure(manifest_ref,*,activation_ref,pid,request=None,reader=None,readonly=False,native_activator=None,pre_native_authorization=None,window_factory=None):
    binding=derive(manifest_ref,activation_ref,pid);manifest=o.doc(manifest_ref);directory=Path(manifest['source']['path']).parent/'.review-capture-focus';directory.mkdir(exist_ok=True);o.canonical(directory);key=previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});path=directory/(key+'.json');request=request or previous.overlay.bridge.request;reader=reader or front_identity
    def no_unknown():
        if pre_native_authorization is None:return previous.overlay.no_capture_unknown(Path(manifest['source']['path']))
        admitted=verify_pre_native_authorization(pre_native_authorization,None);facts=admitted['facts'];o.need(facts['operation']['manifest']==manifest and facts['operation']['pid']==pid,'panel-focus-original-manifest')
        panel_capture_state(pre_native_authorization,facts['operation'],require_fresh=True)
        allowed=Path(facts['region_state_ref']['path'])
        for name in ('.review-capture-state','.review-region-state'):
            for p in (Path(manifest['source']['path']).parent/name).glob('*.json'):
                if p!=allowed:o.need(o.doc(o.ref(p)).get('state') in ('complete','awaiting-visual-review'),'overlay-capture-intent-unresolved')
    with (directory/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);no_unknown()
        for other in directory.glob('*.json'):
            if other!=path:o.need(all(e['state']=='complete' for e in o.doc(o.ref(other))['events']),'capture-focus-other-unknown')
        state=o.doc(o.ref(path)) if path.exists() else {'kind':'review-capture-focus-events-v1','binding':binding,'events':[],'created_at':stamp()};o.need(state['kind']=='review-capture-focus-events-v1' and state['binding']==binding,'capture-focus-original-binding')
        rawdir=directory/key;rawdir.mkdir(exist_ok=True)
        def raw(command,label):
            o.need(derive(manifest_ref,activation_ref,pid)==binding,'capture-focus-inputs-changed');p=rawdir/(label+'-'+uuid.uuid4().hex+'.json')
            no_unknown()
            try:reply=request(command)
            except Exception as error:
                ref=o.immutable(p,{'command':command,'exception':{'type':type(error).__name__,'message':str(error)},'observed_at':stamp()});state.setdefault('reads',[]).append(ref);previous.overlay.rc.atomic(path,state);raise
            ref=o.immutable(p,{'command':command,'response':reply,'observed_at':stamp()});state.setdefault('reads',[]).append(ref);previous.overlay.rc.atomic(path,state);return reply
        def observe():
            reply=raw({'op':'tabs'},'tabs');o.need(reply.get('ok') is True,'capture-focus-tabs-failed');observed={**reader(pid),'tabs':reply['result'],'tabs_reply':state['reads'][-1],'observed_at':stamp()};r=o.immutable(rawdir/('focus-observation-'+uuid.uuid4().hex+'.json'),observed);return observed,r
        validate_events(state,binding)
        for event in state['events']:
            native=event.get('native_focus') if event.get('native_focus',{}).get('window_fallback') else event.get('window_focus') or event.get('native_focus')
            if event['state']!='complete' and native and native['state']=='complete':
                # Seal the already-proven effect after a crash between durable
                # native completion and outer event completion. No new input.
                event.update(state='complete',after=native['after'],completed_at=native['completed_at'],outcome='sealed-persisted-native-completion');previous.overlay.rc.atomic(path,state)
        observed,ref=observe();status=qualify(observed,binding)
        pending=state['events'][-1] if state['events'] and state['events'][-1]['state']!='complete' else None
        native_dispatched=False
        def finish_window(event,current,current_ref):
            nonlocal native_dispatched
            stage=event.get('window_focus');port=(window_factory or ExactWindowRaise)(pid)
            try:
                if stage is None:
                    o.need(not readonly and not event.get('native_focus') and event['calls'][0]['state']=='confirmed' and qualify(current,binding)=='page-window-focus-loss' and current['CG_first_ordinary'].get('kCGWindowName')=='近期的下载记录','capture-window-stage-not-qualified')
                    scope=window_scope(binding,current);target=port.locate(scope)
                    current,current_ref=observe();o.need(qualify(current,binding)=='page-window-focus-loss' and window_scope(binding,current)==scope and current['CG_first_ordinary'].get('kCGWindowName')=='近期的下载记录','capture-window-changed-before-intent');no_unknown()
                    stage={'state':'unknown','binding':binding,'before':current_ref,'target':target,'intent_at':stamp(),'action':WINDOW_ACTION};event['window_focus']=stage;previous.overlay.rc.atomic(path,state)
                    receipt=rawdir/('window-focus-reply-'+uuid.uuid4().hex+'.json');native_dispatched=True
                    try:result=port.raise_once(scope,target)
                    except Exception as error:
                        stage['reply']=o.immutable(receipt,{'binding':binding,'intent_at':stage['intent_at'],'exception':{'type':type(error).__name__,'message':str(error)},'observed_at':stamp()});previous.overlay.rc.atomic(path,state);raise
                    stage['reply']=o.immutable(receipt,{'binding':binding,'intent_at':stage['intent_at'],'result':result,'observed_at':stamp()});previous.overlay.rc.atomic(path,state)
                    o.need(result=={'target':target,'request_accepted':True,'effect_verified':False,'launch_used':False},'capture-window-stage-result')
                def record_effect(attempt):
                    evidence=o.immutable(rawdir/('window-effect-check-'+uuid.uuid4().hex+'.json'),attempt);stage.setdefault('effect_checks',[]).append(evidence);previous.overlay.rc.atomic(path,state)
                def panel_dismiss(observation):
                    return dismiss_download_panel(pid,observation,rawdir)
                current,current_ref,effect=settle_window_effect(port,stage,binding,current,current_ref,observe,record_effect,panel_dismiss=None if readonly else panel_dismiss)
                stage.update(state='complete',after=current_ref,effect=o.immutable(rawdir/('window-focus-effect-'+uuid.uuid4().hex+'.json'),effect),completed_at=stamp());previous.overlay.rc.atomic(path,state);validate_window_stage(event,binding);return current,current_ref
            finally:port.close()
        def finish_native(event,current,current_ref):
            nonlocal native_dispatched
            native=event.get('native_focus');fallback=None;readonly_hold=None
            if event.get('window_focus') and not native:
                if not readonly and native_admission(current,binding):
                    # Observe the old AXRaise effect once, without mutating its
                    # stage. Only exact Chrome-not-frontmost may admit fallback.
                    attempts=[];port=(window_factory or ExactWindowRaise)(pid)
                    def record_hold(attempt):attempts.append(o.immutable(rawdir/('native-readonly-effect-check-'+uuid.uuid4().hex+'.json'),attempt))
                    try:
                        try:settle_window_effect(port,event['window_focus'],binding,current,current_ref,observe,record_hold,max_observations=1)
                        except ValueError as error:
                            o.need(str(error)=='capture-window-unknown-readonly-no-replay','capture-native-readonly-settlement-risk')
                            readonly_hold=o.immutable(rawdir/('native-readonly-window-hold-'+uuid.uuid4().hex+'.json'),{'kind':'independent-native-readonly-window-hold-v1','binding':binding,'window_stage':copy.deepcopy(event['window_focus']),'observation':current_ref,'attempts':attempts,'error':str(error),'input_performed':False})
                            validate_native_readonly_hold(readonly_hold,binding,event['window_focus'],current_ref)
                        else:raise ValueError('capture-native-old-window-already-effective-no-upgrade')
                    finally:port.close()
                    first_ref=current_ref;current,current_ref=observe()
                    if qualify(current,binding)=='ready':return finish_window(event,current,current_ref)
                    fallback=window_native_admission(event,binding,first_ref,current_ref)
                else:return finish_window(event,current,current_ref)
            elif not native and qualify(current,binding)=='page-window-focus-loss':return finish_window(event,current,current_ref)
            def verified_native(observation):
                if qualify(observation,binding)!='ready':return None
                if not (fallback or (native and native.get('window_fallback'))):return True
                port=(window_factory or ExactWindowRaise)(pid)
                try:
                    effect=port.effect(window_scope(binding,observation),event['window_focus']['target'],observation)
                    expected={'target':event['window_focus']['target'],'CG_first_id':observation['CG_first_ordinary']['kCGWindowNumber'],'AX_main_verified':True,'CG_first_verified':True,'webarea_contents_read':False}
                    o.need(effect==expected,'capture-window-native-window-effect-contract')
                    return o.immutable(rawdir/('native-window-effect-'+uuid.uuid4().hex+'.json'),effect)
                finally:port.close()
            if native:
                effect=verified_native(current);o.need(effect is not None,'capture-focus-native-unknown-readonly-no-replay')
                if native.get('window_fallback'):native['window_effect']=effect
                native.update(state='complete',after=current_ref,completed_at=stamp(),outcome='readonly-native-effect-confirmed');previous.overlay.rc.atomic(path,state);return current,current_ref
            o.need(not readonly and event['calls'][0]['state']=='confirmed' and native_admission(current,binding),'capture-focus-native-stage-not-qualified')
            o.need(derive(manifest_ref,activation_ref,pid)==binding,'capture-focus-inputs-changed');no_unknown()
            native_dispatched=True
            native={'state':'unknown','binding':binding,'before':current_ref,'intent_at':stamp(),'action':'activate-existing-Chrome-PID-only'}
            if fallback:native.update(window_fallback=fallback,readonly_hold=readonly_hold,key='capture-native-after-window:'+str(event['number']))
            if fallback:native['stage_intent']=o.immutable(rawdir/('native-after-window-intent-'+uuid.uuid4().hex+'.json'),{'kind':'independent-native-stage-intent-v1','event_number':event['number'],'window_stage':copy.deepcopy(event['window_focus']),'native_stage':copy.deepcopy(native)})
            event['native_focus']=native;previous.overlay.rc.atomic(path,state) # sole native write-before-input boundary
            receipt=rawdir/('native-focus-reply-'+uuid.uuid4().hex+'.json');start=time.monotonic()
            try:result=(native_activator or activate_original_chrome)(pid)
            except Exception as error:
                native['reply']=o.immutable(receipt,{'binding':binding,'intent_at':native['intent_at'],'exception':{'type':type(error).__name__,'message':str(error)},'observed_at':stamp()});previous.overlay.rc.atomic(path,state);raise
            native['reply']=o.immutable(receipt,{'binding':binding,'intent_at':native['intent_at'],'result':result,'observed_at':stamp()});previous.overlay.rc.atomic(path,state)
            o.need(result.get('pid')==pid and result.get('bundle')=='com.google.Chrome' and result.get('request_accepted') is True and result.get('launch_used') is False,'capture-focus-native-result-binding')
            if fallback:o.need(result.get('process')==current['process'],'capture-window-native-result-process-changed')
            for count in range(3):
                current,current_ref=observe()
                effect=verified_native(current)
                if effect is not None:
                    if fallback:native['window_effect']=effect
                    native.update(state='complete',after=current_ref,completed_at=stamp(),outcome='native-frontmost-confirmed',elapsed_seconds=time.monotonic()-start);previous.overlay.rc.atomic(path,state);return current,current_ref
                if time.monotonic()-start>=2:break
                if count<2:time.sleep(.05)
            raise ValueError('capture-focus-native-effect-unverified-no-replay')
        if pending and pending['calls']:
            call=pending['calls'][0]
            if status!='ready':
                o.need(call['state']=='confirmed','capture-focus-unknown-readonly-no-replay');observed,ref=finish_native(pending,observed,ref)
            elif pending.get('native_focus') or pending.get('window_focus'):observed,ref=finish_native(pending,observed,ref)
            if call['state']=='unknown':call.update(state='confirmed',result={'observed':True,'proof':ref,'tabId':binding['scope']['tabId'],'windowId':binding['scope']['windowId'],'url':binding['url'],'active':True,'windowFocused':True})
            pending.update(state='complete',after=ref,completed_at=stamp(),outcome='readonly-original-effect-confirmed');previous.overlay.rc.atomic(path,state);return {'ready':True,'focus_event':pending['number'],'input_dispatched':native_dispatched,'native_input_dispatched':native_dispatched,'journal':o.ref(path)}
        if status=='ready':
            if pending:pending.update(state='complete',after=ref,completed_at=stamp(),outcome='already-ready-no-input')
            previous.overlay.rc.atomic(path,state);return {'ready':True,'focus_event':pending['number'] if pending else None,'input_dispatched':False,'journal':o.ref(path)}
        o.need(not readonly,'capture-focus-readonly-effect-not-observed')
        event=pending
        if event is None:
            event={'number':len(state['events'])+1,'binding':binding,'before':ref,'state':'preflight','phase':'capture-focus','revision':0,'calls':[],'created_at':stamp()};state['events'].append(event);previous.overlay.rc.atomic(path,state)
        focus=Focus(path,state,event,binding,request,raw);focus.once({'op':'activate','tabId':binding['scope']['tabId']});event['state']='unknown';focus.save()
        fresh,after=observe()
        if qualify(fresh,binding)!='ready':fresh,after=finish_native(event,fresh,after)
        event.update(state='complete',after=after,completed_at=stamp(),outcome='focus-restore-confirmed');focus.save();return {'ready':True,'focus_event':event['number'],'input_dispatched':True,'journal':o.ref(path)}

def paths():
    return {n:str(ROOT/'skills'/s/'scripts'/n) for s,n in [('chrome-dom-export','native_window_capture.py'),('chrome-dom-export','native_region_capture.py'),('chrome-dom-export','review_region_capture.py'),('negative-review-complaints','capture_review_region.py'),('negative-review-complaints','review_capture_tab.py'),('negative-review-complaints','initial_ledger_recovery.py'),('negative-review-complaints','review_capture_focus.py')]}
def source_tip(parent,release_ref,old_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);ps=paths();targets=rel['targets'];old={Path(r['path']).name:r for r in old_refs}
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(targets)==7 and {t['target'] for t in targets}==set(ps.values()) and all(t['mode']=='0644' for t in targets),'capture-focus-exact-seven-target-release')
    o.need(any(r['path']==str(ROOT/'skills/wecom-messenger/scripts/public_app_activation.py') for r in parent.get('code_refs',[])),'capture-focus-public-AppKit-source-unpinned')
    o.need(len(old_refs)==6 and set(old)=={n+'.before' for n in ps if n!='review_capture_focus.py'},'capture-focus-exact-six-archives');archives=[]
    for name,path in ps.items():
        if name=='review_capture_focus.py':continue
        t=next(t for t in targets if t['target']==path);r=old[name+'.before'];o.need(r['sha256']==t['old_sha256'],'capture-focus-old-source-binding');o.raw(r);archives.append({'target':path,'archive':r})
    native=[x for x in archives if Path(x['target']).name in ('native_window_capture.py','native_region_capture.py','review_region_capture.py')]
    prior=previous.verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[*native,*extra_source_archives]);codes=copy.deepcopy(prior['code_refs']);by={r['path']:r for r in codes}
    for t in targets:
        o.raw(t['after']);new={'path':t['target'],'sha256':t['after']['sha256']}
        if t['target']==ps['review_capture_focus.py']:o.need(t['old_sha256'] is None and t['target'] not in by,'capture-focus-new-helper-only');codes.append(new)
        else:before=by[t['target']];o.need(before['sha256']==t['old_sha256'],'capture-focus-admission-base');codes[codes.index(before)]=new
    if installed:
        for r in codes:o.raw(r)
        for p in ps.values():o.need(Path(p).stat().st_mode & 0o777==0o644,'capture-focus-installed-mode')
    return prior,codes,archives

def complete_overlay(manifest_ref,original_ref=None,archived=None):
    overlay=previous.overlay;manifest=o.doc(manifest_ref);base,source,scope,url=overlay.derive(manifest);binding={'source':manifest['source'],'job':manifest['job'],'profile':manifest['profile'],'envelope':manifest['envelope'],'identity':source['identity'],'scope':scope,'url':url,'content':overlay.content_identity()};key=overlay.rc.digest({'source_sha256':manifest['source']['sha256'],**scope,'identity':source['identity']});path=overlay.RUNTIME/(key+'.json');ref=original_ref or o.ref(path);state=o.doc(ref) if archived is None else archived
    o.need(Path(ref['path'])==path and state['kind']=='review-account-overlay-preflight-v1' and state['binding']==binding and state['state']=='complete' and state['closure_verified'] is True and state['last_ready_manifest']==manifest_ref,'capture-focus-original-overlay-not-closed')
    attempt=state['attempts'][-1];raw=[o.doc(r) for r in attempt['raw']];o.need(attempt['manifest']==manifest_ref and not attempt.get('error') and len(raw)==12,'capture-focus-original-overlay-complete-attempt')
    o.need([r['command']['op'] for r in raw]==['tabs','ping','tree','tabs','dom-region-proof','find','hover','tabs','ping','tree','tabs','dom-region-proof'],'capture-focus-original-overlay-sequence')
    for ids in ((0,1,2,3),(7,8,9,10)):
        a,ping,tree,b=[raw[i] for i in ids];o.need(a['response'].get('ok') is True and a['response']==b['response'] and previous.classify(a['response']['result'],previous.derive(manifest_ref))=='active','capture-focus-original-overlay-tabs')
        o.need(ping['response'].get('ok') is True and ping['response']['result'].get('content_build')==binding['content']['build'] and ping['response']['result'].get('version')==binding['content']['version'] and tree['response'].get('ok') is True,'capture-focus-original-overlay-read-failed')
        overlay.rc.normal.navigation_probe(tree['response']['result'],o.doc(manifest['job']),text_schema=o.doc(manifest['profile']).get('text_schema'))
    _,trigger=overlay.card(raw[2]['response']['result'],source['identity'],required=True);o.need(overlay.command(scope,source['identity'],trigger)==state['command']==raw[6]['command'],'capture-focus-original-hover-command');overlay.validate_reply(raw[6]['response']);o.need(overlay.card(raw[9]['response']['result'],source['identity'])[0] is None,'capture-focus-original-card-not-absent');intent=o.doc(state['input_intent']);o.need(intent['binding']==binding and intent['command']==state['command'] and intent['before']==attempt['raw'][:6] and state['reply']==attempt['raw'][6],'capture-focus-original-hover-intent');overlay.region.checked(raw[-1]['response'],overlay.region.region_command(base));return ref

def original_contract(parent,engine,activation_ref,prior,*,archived_activation=None,original_overlay=None,archived_overlay=None):
    old=o.doc(parent[FIELD]);oldp=o.doc(old['parent_archive']);olde=o.doc(old['engine_archive']);ready_p,ready_e=previous.recovered(oldp,olde,parent[FIELD]);folder=o.location(parent['order'])
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==6 and parent['calls'][:5]==prior['failed_calls'] and not parent.get('child') and not parent.get('completion'),'capture-focus-exact-parent-hold')
    o.need(engine['status']=='hold' and engine.get('error')==ERROR and len(engine['calls'])==46 and engine['calls'][:45]==olde['calls'],'capture-focus-exact-engine-hold')
    last=engine['calls'][-1];a=engine['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(last['state']=='failed' and last['error']==ERROR and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'capture-focus-exact-failed-frame-call')
    expected_p=copy.deepcopy(ready_p);expected_p['calls'].append(parent['calls'][-1]);expected_p.update(status='hold',error='execution-child-stopped');expected_e=copy.deepcopy(ready_e);expected_e['calls'].append(last);expected_e.update(status='hold',error=ERROR)
    o.need(parent==expected_p and engine==expected_e,'capture-focus-no-other-progress-delta');manifest_ref=old['facts']['manifest'];binding=derive_archived(manifest_ref,activation_ref,parent['pid'],archived_activation);overlay_ref=complete_overlay(manifest_ref,original_overlay,archived_overlay)
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==parent['calls'][4]['argv'] and launch['index']==5 and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':ERROR} and Path(call['launch']['path'])==folder/'children/0005-launch.json' and Path(call['result']['path'])==folder/'children/0005-exit.json','capture-focus-original-natural-rc2')
    return {'manifest':manifest_ref,'activation':activation_ref,'overlay':overlay_ref,'binding':binding,'ledger_current':a['ledger_current'],'failed_engine_indices':[0,4,43,44,45],'failed_calls':parent['calls'],'failure_geometry_recorded':False,'failure_cause_inferred':False}
def derive_archived(manifest_ref,activation_ref,pid,archived=None):
    if archived is None:return derive(manifest_ref,activation_ref,pid)
    return derive(manifest_ref,activation_ref,pid,archived_activation=archived)

def no_capture(manifest_ref):
    manifest=o.doc(manifest_ref);unit=Path(manifest['source']['path']).parent
    for directory in (unit/'.review-region-state',unit/'.review-capture-state'):o.need(not list(directory.glob('*.json')),'capture-focus-existing-capture-intent')
    out=Path(manifest_ref['path']).parent/'capture';o.need(not out.exists() or not any(out.iterdir()),'capture-focus-existing-pixels-or-native-intent')

def plan(parent_ref,engine_ref,activation_ref,worker_ref,release_ref,old_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','capture-focus-canonical-originals');prior,codes,archives=source_tip(parent,release_ref,old_refs,installed=installed);facts=original_contract(parent,engine,activation_ref,prior);no_capture(facts['manifest']);evidence=previous.previous.worker_evidence(parent,engine_ref,worker_ref)
    return {'kind':KIND,'original_parent':parent_ref,'original_engine':engine_ref,'original_activation':activation_ref,'original_overlay':facts['overlay'],'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'old_sources':archives,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}
def recovered(parent,engine,proof):return previous.recovered(parent,engine,proof)
def verify_recovered(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref)
    if current.get(FIELD) and o.doc(current[FIELD]).get('recovery_stage')==ANCHOR_STAGE:
        admitted=verify_anchor_stage(current,current[FIELD],installed=installed,extra_source_archives=extra_source_archives)
        if current[FIELD]!=proof_ref:
            latest=o.doc(current[FIELD]);verify_recovered(o.doc(latest['parent_archive']),proof_ref,installed=False,extra_source_archives=[{'target':str(ROOT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py'),'archive':latest['before_sources'][2]},*extra_source_archives])
        return admitted
    if current.get(FIELD) and o.doc(current[FIELD]).get('recovery_stage')==NORMAL_STAGE:
        admitted=verify_normal_stage(current,current[FIELD],installed=installed,extra_source_archives=extra_source_archives)
        if current[FIELD]!=proof_ref:
            latest=o.doc(current[FIELD]);verify_recovered(o.doc(latest['parent_archive']),proof_ref,installed=False,extra_source_archives=[{'target':str(ROOT/'skills/negative-review-complaints/scripts/complaint_execution_normal.py'),'archive':latest['before_sources'][2]},*extra_source_archives])
        return admitted
    if current.get(FIELD) and o.doc(current[FIELD]).get('recovery_stage')==RECHECK_STAGE:
        admitted=verify_recheck_stage(current,current[FIELD],installed=installed,extra_source_archives=extra_source_archives)
        if current[FIELD]!=proof_ref:
            latest=o.doc(current[FIELD]);verify_recovered(o.doc(latest['parent_archive']),proof_ref,installed=False,extra_source_archives=[{'target':str(ROOT/'skills/negative-review-complaints/scripts/complaint_execution_ports.py'),'archive':latest['before_sources'][2]},*extra_source_archives])
        return admitted
    if current.get(FIELD) and o.doc(current[FIELD]).get('recovery_stage')==SHORTCUT_STAGE:
        admitted=verify_shortcut_stage(current,current[FIELD],installed=installed,extra_source_archives=extra_source_archives)
        if current[FIELD]!=proof_ref:
            latest=o.doc(current[FIELD]);verify_recovered(o.doc(latest['parent_archive']),proof_ref,installed=False,extra_source_archives=[{'target':str(ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py'),'archive':latest['before_sources'][2]},*extra_source_archives])
        return admitted
    # Only this explicit waiting-QA source overlay can carry its direct prior
    # observation authorization; never a generic mismatch/old-code exemption.
    if current.get(FIELD)!=proof_ref and current.get(FIELD) and o.doc(current[FIELD]).get('recovery_stage')=='waiting-quality-source-admission':
        admitted=verify_quality_stage(current,current[FIELD],installed=installed,extra_source_archives=extra_source_archives);o.need(o.doc(current[FIELD])['prior_recovery']==proof_ref,'quality-admission-direct-prior-only');return admitted
    if p.get('recovery_stage')=='waiting-quality-source-admission':return verify_quality_stage(current,proof_ref,installed=installed,extra_source_archives=extra_source_archives)
    if p.get('recovery_stage')=='fresh-observation-revision':return verify_observation_stage(current,proof_ref,installed=installed,extra_source_archives=extra_source_archives)
    if p.get('recovery_stage')=='region-readonly-postguard':return verify_postguard_stage(current,proof_ref,installed=installed,extra_source_archives=extra_source_archives)
    if p.get('recovery_stage') in ('native-app-focus','native-app-focus-unfocused','native-app-focus-fresh-reader'):return verify_native_stage(current,proof_ref,installed=installed,extra_source_archives=extra_source_archives)
    folder=o.location(current['order']);base=folder/'.review-native-preflight-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and Path(proof_ref['path'])==base/'proof.json' and current.get(FIELD)==proof_ref and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'capture-focus-canonical-proof')
    for n in ('parent','engine','activation','overlay'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'capture-focus-archive-binding')
    o.need(all(Path(x['archive']['path'])==base/'sources'/Path(x['archive']['path']).name for x in p['old_sources']),'capture-focus-canonical-source-archives')
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'capture-focus-original-prior-proof');prior,codes,_=source_tip(parent,p['release'],[x['archive'] for x in p['old_sources']],installed=installed,extra_source_archives=extra_source_archives);facts=original_contract(parent,engine,p['original_activation'],prior,archived_activation=o.doc(p['activation_archive']),original_overlay=p['original_overlay'],archived_overlay=o.doc(p['overlay_archive']));evidence=previous.previous.worker_evidence(parent,p['original_engine'],p['worker']);expected=recovered(parent,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['worker_evidence']==evidence and p['code_refs']==codes and current['calls'][:6]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'capture-focus-preserved-original-history')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['activation_archive'],p['overlay_archive'],p['release'],*[x['archive'] for x in p['old_sources']],*evidence]}
def verified_engine_calls(engine):
    if o.doc(engine[FIELD]).get('recovery_stage')==ANCHOR_STAGE:
        parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];p=o.doc(proof);verify_anchor_stage(parent,proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['order']==parent['order'] and engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'switch-anchor-engine-history');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
    if o.doc(engine[FIELD]).get('recovery_stage')==NORMAL_STAGE:
        parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];p=o.doc(proof);verify_normal_stage(parent,proof);old=o.doc(p['engine_archive']);expected=recovered_normal(o.doc(p['parent_archive']),old,proof,p['facts']['outputs'])[1];o.need(engine['order']==parent['order'] and engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'normal-profile-engine-history');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
    if o.doc(engine[FIELD]).get('recovery_stage')==RECHECK_STAGE:
        parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];p=o.doc(proof);verify_recheck_stage(parent,proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['order']==parent['order'] and engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'recheck-focus-engine-history');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
    if o.doc(engine[FIELD]).get('recovery_stage')==SHORTCUT_STAGE:
        parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];p=o.doc(proof);verify_shortcut_stage(parent,proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['order']==parent['order'] and engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'],'review-shortcut-engine-history');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
    if o.doc(engine[FIELD]).get('recovery_stage')=='waiting-quality-source-admission':
        parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'quality-admission-parent-engine-proof');verify_quality_stage(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);o.need(engine['calls'][:len(old['calls'])]==old['calls'] and engine.get('resolved_errors')==old.get('resolved_errors') and engine['order']==parent['order'],'quality-admission-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
    if o.doc(engine[FIELD]).get('recovery_stage')=='fresh-observation-revision':return observation_stage_calls(engine)
    if o.doc(engine[FIELD]).get('recovery_stage')=='region-readonly-postguard':return postguard_stage_calls(engine)
    if o.doc(engine[FIELD]).get('recovery_stage') in ('native-app-focus','native-app-focus-unfocused','native-app-focus-fresh-reader'):return native_stage_calls(engine)
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'capture-focus-parent-engine-proof');verify_recovered(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['calls'][:46]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'capture-focus-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
def recover(parent_ref,engine_ref,activation_ref,worker_ref,release_ref,old_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-native-preflight-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_activation':activation_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted((Path(r['path']).name,r['sha256']) for r in old_refs)==sorted((Path(x['archive']['path']).name,x['archive']['sha256']) for x in p['old_sources']),'capture-focus-same-recovery-inputs')
        else:
            p=plan(parent_ref,engine_ref,activation_ref,worker_ref,release_ref,old_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'sources').mkdir(exist_ok=True)
            for n,r in (('parent',parent_ref),('engine',engine_ref),('activation',activation_ref),('overlay',p['original_overlay'])):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            for x in p['old_sources']:x['archive']=h.immutable_bytes(base/'sources'/Path(x['archive']['path']).name,o.raw(x['archive']))
            p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'capture-focus-current-lease');previous.previous.current_ledgers(parent,engine);o.raw(activation_ref);o.raw(p['original_overlay']);no_capture(p['facts']['manifest']);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe)];verify_recovered(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        previous.previous.current_ledgers(parent,engine);o.raw(activation_ref);o.raw(p['original_overlay'])
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

NATIVE_ERROR='capture-focus-effect-unverified-no-replay'
def native_tip(parent,release_ref,before_ref,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);path=str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py');test_paths={str(ROOT/'skills/negative-review-complaints/tests'/n) for n in ('test_review_native_app_focus_stage.py','test_review_native_focus_freshness.py')};targets=rel['targets'];sources=[t for t in targets if t['target']==path];o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(sources)==1 and len(targets) in (1,2) and len({t['target'] for t in targets})==len(targets) and all(t['target'] in ({path}|test_paths) and t['mode']=='0644' for t in targets) and sources[0]['old_sha256']==before_ref['sha256'],'capture-native-exact-one-source-release');o.raw(before_ref);t=sources[0]
    for item in targets:o.raw(item['after'])
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=extra_source_archives);codes=copy.deepcopy(prior['code_refs']);previous_ref=next(r for r in codes if r['path']==path);o.need(previous_ref['sha256']==before_ref['sha256'],'capture-native-source-admission-base');codes[codes.index(previous_ref)]={'path':path,'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
        o.need(Path(path).stat().st_mode & 0o777==0o644,'capture-native-installed-mode')
    return prior,codes

def native_original(parent,engine,focus_ref,observation_ref,prior,*,archived_focus=None):
    proof=o.doc(parent[FIELD]);stage=proof.get('recovery_stage');o.need(stage in (None,'native-app-focus','native-app-focus-unfocused'),'capture-native-one-stage-only');offset={None:0,'native-app-focus':1,'native-app-focus-unfocused':2}[stage];error={None:NATIVE_ERROR,'native-app-focus':'capture-focus-native-stage-not-qualified','native-app-focus-unfocused':'capture-focus-native-effect-unverified-no-replay'}[stage];oldp=o.doc(proof['parent_archive']);olde=o.doc(proof['engine_archive']);ready_p,ready_e=recovered(oldp,olde,parent[FIELD]);folder=o.location(parent['order'])
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==7+offset and parent['calls'][:6+offset]==prior['failed_calls'] and not parent.get('child') and not parent.get('completion'),'capture-native-exact-parent-hold')
    o.need(engine['status']=='hold' and engine.get('error')==error and len(engine['calls'])==47+offset and engine['calls'][:46+offset]==ready_e['calls'],'capture-native-exact-engine-hold');last=engine['calls'][-1];a=engine['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(last['state']=='failed' and last['error']==error and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'capture-native-exact-last-failure')
    expected_p=copy.deepcopy(ready_p);expected_p['calls'].append(parent['calls'][-1]);expected_p.update(status='hold',error='execution-child-stopped');expected_e=copy.deepcopy(ready_e);expected_e['calls'].append(last);expected_e.update(status='hold',error=error);o.need(parent==expected_p and engine==expected_e,'capture-native-no-other-delta')
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==parent['calls'][5+offset]['argv'] and launch['index']==6+offset and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':error} and Path(call['launch']['path'])==folder/'children'/(str(6+offset).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(6+offset).zfill(4)+'-exit.json'),'capture-native-original-natural-rc2')
    binding=proof['facts']['binding'];manifest=o.doc(binding['manifest']);key=previous.overlay.rc.digest({'source':manifest['source']['sha256'],'review_keys':sorted(manifest['review_keys'])});directory=Path(manifest['source']['path']).parent/'.review-capture-focus';state=o.doc(focus_ref) if archived_focus is None else archived_focus;o.need(Path(focus_ref['path'])==directory/(key+'.json') and state['kind']=='review-capture-focus-events-v1' and state['binding']==binding and len(state['events'])==1,'capture-native-canonical-original-focus');validate_events(state,binding);event=state['events'][0];o.need(event['state']=='unknown' and len(event['calls'])==1 and event['calls'][0]['state']=='confirmed','capture-native-original-extension-confirmed')
    if offset<2:o.need(not event.get('native_focus'),'capture-native-no-existing-native-intent')
    else:
        native=event.get('native_focus');o.need(native and native['state']=='unknown' and native['action']=='activate-existing-Chrome-PID-only' and native.get('reply'),'capture-native-sole-unknown-native-stage');reply=o.doc(native['reply']);o.need(reply.get('result',{}).get('request_accepted') is True and reply['result'].get('pid')==binding['pid'] and reply['result'].get('bundle')=='com.google.Chrome','capture-native-original-native-accepted-only')
    observed=o.doc(observation_ref);o.need(Path(observation_ref['path']).parent==directory/key and Path(observation_ref['path']).name.startswith('focus-observation-') and observed['tabs_reply']==state['reads'][-1] and qualify(observed,binding)=='external-focus-loss' and (native_admission(observed,binding) if stage else previous.classify(observed['tabs'],browser_binding(binding))=='active'),'capture-native-original-browser-focused-NS-external');o.need(datetime.fromisoformat(event['calls'][0]['at'])<=datetime.fromisoformat(observed['observed_at'])<=datetime.fromisoformat(result['at']),'capture-native-observation-time')
    return {'manifest':binding['manifest'],'binding':binding,'focus':focus_ref,'observation':observation_ref,'failed_engine_indices':[0,4,43,44,45,46]+list(range(47,47+offset)),'failed_calls':parent['calls'],'native_input_previously_issued':offset==2}
def plan_native(parent_ref,engine_ref,focus_ref,observation_ref,worker_ref,release_ref,before_ref,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','capture-native-canonical-originals');prior,codes=native_tip(parent,release_ref,before_ref,installed=installed);facts=native_original(parent,engine,focus_ref,observation_ref,prior);no_capture(facts['manifest']);return {'kind':KIND,'recovery_stage':{None:'native-app-focus','native-app-focus':'native-app-focus-unfocused','native-app-focus-unfocused':'native-app-focus-fresh-reader'}[o.doc(parent[FIELD]).get('recovery_stage')],'original_parent':parent_ref,'original_engine':engine_ref,'original_focus':focus_ref,'observation':observation_ref,'worker':worker_ref,'release':release_ref,'before_source':before_ref,'facts':facts,'code_refs':codes,'worker_evidence':previous.previous.worker_evidence(parent,engine_ref,worker_ref),'ui_used':False}
def verify_native_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-native-app-focus-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage'] in ('native-app-focus','native-app-focus-unfocused','native-app-focus-fresh-reader') and current.get(FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'capture-native-canonical-stage-proof')
    for n in ('parent','engine','focus'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'capture-native-immutable-original-archive')
    o.need(Path(p['before_source']['path'])==base/'review_capture_focus.py.before','capture-native-old-source-archive');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);prior,codes=native_tip(parent,p['release'],p['before_source'],installed=installed,extra_source_archives=extra_source_archives);facts=native_original(parent,engine,p['original_focus'],p['observation'],prior,archived_focus=o.doc(p['focus_archive']));evidence=previous.previous.worker_evidence(parent,p['original_engine'],p['worker']);expected=recovered(parent,engine,proof_ref)[0];o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==evidence and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'capture-native-original-history-preserved');return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['focus_archive'],p['observation'],p['before_source'],p['release'],*evidence]}
def native_stage_calls(engine):
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'capture-native-parent-engine-proof');verify_native_stage(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'capture-native-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]
def recover_native(parent_ref,engine_ref,focus_ref,observation_ref,worker_ref,release_ref,before_ref):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-native-app-focus-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_focus':focus_ref,'observation':observation_ref,'worker':worker_ref,'release':release_ref}.items()) and p['before_source']['sha256']==before_ref['sha256'],'capture-native-same-recovery-inputs')
        else:
            p=plan_native(parent_ref,engine_ref,focus_ref,observation_ref,worker_ref,release_ref,before_ref,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base)
            for n,r in (('parent',parent_ref),('engine',engine_ref),('focus',focus_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_source']=h.immutable_bytes(base/'review_capture_focus.py.before',o.raw(before_ref));p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'capture-native-current-lease');previous.previous.current_ledgers(parent,engine);o.raw(focus_ref);no_capture(p['facts']['manifest']);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe)];verify_native_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        previous.previous.current_ledgers(parent,engine);o.raw(focus_ref)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':p['recovery_stage'],'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

POSTGUARD_ERROR='review-region-proof-failed:capture-target-not-active-focused-stable-site'
def postguard_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    paths={str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/chrome-dom-export/scripts/review_region_capture.py')};tests={str(ROOT/'skills/negative-review-complaints/tests/test_review_region_postguard_continuation.py')};rel=o.doc(release_ref);targets=rel['targets'];sources=[t for t in targets if t['target'] in paths]
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(sources)==2 and len(targets) in (2,3) and len({t['target'] for t in targets})==len(targets) and all(t['target'] in paths|tests and t['mode']=='0644' for t in targets),'review-postguard-exact-two-source-release')
    old={Path(r['path']).name.removesuffix('.before'):r for r in before_refs};o.need(set(old)=={'review_capture_focus.py','review_region_capture.py'} and len(before_refs)==2,'review-postguard-exact-old-source-set')
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=extra_source_archives);codes=copy.deepcopy(prior['code_refs'])
    for t in sources:
        r=old[Path(t['target']).name];o.raw(r);o.raw(t['after']);previous_ref=next(x for x in codes if x['path']==t['target']);o.need(previous_ref['sha256']==t['old_sha256']==r['sha256'],'review-postguard-source-admission-base');codes[codes.index(previous_ref)]={'path':t['target'],'sha256':t['after']['sha256']}
    for t in targets:o.raw(t['after'])
    if installed:
        for r in codes:o.raw(r)
        o.need(all(Path(t['target']).stat().st_mode & 0o777==0o644 for t in sources),'review-postguard-installed-mode')
    return prior,codes

def postguard_original(parent,engine,region_ref,prior,*,archived_region=None,initial=False):
    import review_region_capture as rr
    proof=o.doc(parent[FIELD]);o.need(proof.get('recovery_stage')=='native-app-focus-fresh-reader','review-postguard-original-stage-required');oldp=o.doc(proof['parent_archive']);olde=o.doc(proof['engine_archive']);ready_p,ready_e=recovered(oldp,olde,parent[FIELD]);folder=o.location(parent['order'])
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==10 and parent['calls'][:9]==prior['failed_calls'] and not parent.get('child') and not parent.get('completion'),'review-postguard-exact-parent-hold')
    o.need(engine['status']=='hold' and engine.get('error')==POSTGUARD_ERROR and len(engine['calls'])==50 and engine['calls'][:49]==ready_e['calls'],'review-postguard-exact-engine-hold');last=engine['calls'][-1];a=engine['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(last['state']=='failed' and last['error']==POSTGUARD_ERROR and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'review-postguard-exact-last-failure')
    expected_p=copy.deepcopy(ready_p);expected_p['calls'].append(parent['calls'][-1]);expected_p.update(status='hold',error='execution-child-stopped');expected_e=copy.deepcopy(ready_e);expected_e['calls'].append(last);expected_e.update(status='hold',error=POSTGUARD_ERROR);o.need(parent==expected_p and engine==expected_e,'review-postguard-no-other-delta')
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==parent['calls'][8]['argv'] and launch['index']==9 and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':POSTGUARD_ERROR} and Path(call['launch']['path'])==folder/'children/0009-launch.json' and Path(call['result']['path'])==folder/'children/0009-exit.json','review-postguard-original-natural-rc2')
    original=o.doc(region_ref) if archived_region is None else archived_region;facts=rr.original_complete_region(original,region_ref['path']);o.need(original['operation']['manifest']==o.doc(proof['facts']['manifest']) and original['operation']['pid']==parent['pid'],'review-postguard-original-manifest-pid');out=Path(original['operation']['outdir'])
    if initial:o.need(all(not (out/n).exists() for n in ('preview-registration.json','registration.json','review-region.png')),'review-postguard-no-registration-or-derived-output')
    # No guessed old postguard facts: this exact original unknown has only its
    # immutable before proof/geometry and completed native raw metadata.
    if initial:o.need(not (out/'postguard-continuations').exists(),'review-postguard-no-prior-postguard-attempt')
    return {'manifest':proof['facts']['manifest'],'region':facts,'failed_engine_indices':[0,4,43,44,45,46,47,48,49],'failed_calls':parent['calls'],'native_capture_previously_complete':True,'readonly_postguard_only':True}

def plan_postguard(parent_ref,engine_ref,region_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','review-postguard-canonical-originals');prior,codes=postguard_tip(parent,release_ref,before_refs,installed=installed);facts=postguard_original(parent,engine,region_ref,prior,initial=True)
    return {'kind':KIND,'recovery_stage':'region-readonly-postguard','order':parent['order'],'original_parent':parent_ref,'original_engine':engine_ref,'original_region':region_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':previous.previous.worker_evidence(parent,engine_ref,worker_ref),'ui_used':False}

def verify_postguard_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-postguard-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']=='region-readonly-postguard' and current.get(FIELD)==proof_ref and p['order']==current['order'] and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-postguard-canonical-stage-proof')
    for n in ('parent','engine','region'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'review-postguard-immutable-original-archive')
    o.need(len(p['before_sources'])==2 and all(Path(r['path'])==base/Path(r['path']).name and Path(r['path']).name in ('review_capture_focus.py.before','review_region_capture.py.before') for r in p['before_sources']),'review-postguard-old-source-archive')
    parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);prior,codes=postguard_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=postguard_original(parent,engine,p['original_region'],prior,archived_region=o.doc(p['region_archive']));evidence=previous.previous.worker_evidence(parent,p['original_engine'],p['worker']);expected=recovered(parent,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==evidence and current['calls'][:10]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'review-postguard-original-history-preserved')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['region_archive'],*p['before_sources'],p['release'],*evidence]}

def postguard_stage_calls(engine):
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'review-postguard-parent-engine-proof');verify_postguard_stage(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['calls'][:50]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'review-postguard-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]

def recover_postguard(parent_ref,engine_ref,region_ref,worker_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-postguard-recovery'/parent_ref['sha256'];state=Path(region_ref['path'])
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b,state.with_suffix('.lock').open('a') as c:
        for lock in (a,b,c):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_region':region_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted(r['sha256'] for r in before_refs)==sorted(r['sha256'] for r in p['before_sources']),'review-postguard-same-recovery-inputs')
        else:
            p=plan_postguard(parent_ref,engine_ref,region_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base)
            for n,r in (('parent',parent_ref),('engine',engine_ref),('region',region_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);original=o.doc(p['region_archive']);newregion={**original,'postguard_continuation':proof};lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-postguard-current-lease');previous.previous.current_ledgers(parent,engine);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe),h.exact_metadata_state(state,p['region_archive'],newregion)];verify_postguard_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        previous.previous.current_ledgers(parent,engine)
        for path,value in ((state,newregion),(folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':p['recovery_stage'],'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'region':o.ref(state),'proof':proof,'ui_used':False}

OBSERVATION_ERROR='review-postguard-DOM-changed-original-unknown-preserved'
def observation_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    paths={str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/chrome-dom-export/scripts/review_region_capture.py')};tests={str(ROOT/'skills/chrome-dom-export/tests/test_region_durable_normal_capture.py'),*[str(ROOT/'skills/negative-review-complaints/tests'/n) for n in ('test_review_region_postguard_continuation.py','test_review_region_observation_revision.py')]};rel=o.doc(release_ref);targets=rel['targets'];sources=[t for t in targets if t['target'] in paths]
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(sources)==2 and 2<=len(targets)<=5 and len({t['target'] for t in targets})==len(targets) and all(t['target'] in paths|tests and t['mode']=='0644' for t in targets),'review-observation-exact-reviewed-release')
    old={Path(r['path']).name.removesuffix('.before'):r for r in before_refs};o.need(set(old)=={'review_capture_focus.py','review_region_capture.py'} and len(before_refs)==2,'review-observation-exact-old-source-set');prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=extra_source_archives);codes=copy.deepcopy(prior['code_refs'])
    for t in sources:
        r=old[Path(t['target']).name];o.raw(r);o.raw(t['after']);previous_ref=next(x for x in codes if x['path']==t['target']);o.need(previous_ref['sha256']==t['old_sha256']==r['sha256'],'review-observation-source-admission-base');codes[codes.index(previous_ref)]={'path':t['target'],'sha256':t['after']['sha256']}
    for t in targets:o.raw(t['after'])
    if installed:
        for r in codes:o.raw(r)
        o.need(all(Path(t['target']).stat().st_mode & 0o777==0o644 for t in sources),'review-observation-installed-mode')
    return prior,codes

def observation_original(parent,engine,region_ref,post_ref,prior,*,archived_region=None):
    import review_region_capture as rr
    proof=o.doc(parent[FIELD]);o.need(proof.get('recovery_stage')=='region-readonly-postguard','review-observation-original-postguard-stage');oldp=o.doc(proof['parent_archive']);olde=o.doc(proof['engine_archive']);ready_p,ready_e=recovered(oldp,olde,parent[FIELD]);folder=o.location(parent['order']);count=len(prior['failed_calls'])
    o.need(parent['status']=='hold' and parent.get('error')=='execution-child-stopped' and len(parent['calls'])==count+1 and parent['calls'][:count]==prior['failed_calls'] and not parent.get('child') and not parent.get('completion'),'review-observation-exact-parent-hold')
    o.need(engine['status']=='hold' and engine.get('error')==OBSERVATION_ERROR and len(engine['calls'])==len(ready_e['calls'])+1 and engine['calls'][:-1]==ready_e['calls'],'review-observation-exact-engine-hold');last=engine['calls'][-1];a=engine['companies'][0]['artifacts'];order=o.validate(parent['order']);o.need(last['state']=='failed' and last['error']==OBSERVATION_ERROR and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'},'review-observation-exact-last-failure')
    expected_p=copy.deepcopy(ready_p);expected_p['calls'].append(parent['calls'][-1]);expected_p.update(status='hold',error='execution-child-stopped');expected_e=copy.deepcopy(ready_e);expected_e['calls'].append(last);expected_e.update(status='hold',error=OBSERVATION_ERROR);o.need(parent==expected_p and engine==expected_e,'review-observation-no-other-delta')
    call=parent['calls'][-1];launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv']==parent['calls'][-2]['argv'] and launch['index']==count and launch['order']==parent['order'] and result['launch']==call['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':OBSERVATION_ERROR} and Path(call['launch']['path'])==folder/'children'/(str(count).zfill(4)+'-launch.json') and Path(call['result']['path'])==folder/'children'/(str(count).zfill(4)+'-exit.json'),'review-observation-original-natural-rc2')
    original=o.doc(region_ref) if archived_region is None else archived_region;before=o.doc(proof['region_archive']);o.need(Path(region_ref['path'])==Path(proof['original_region']['path']) and original=={**before,'postguard_continuation':parent[FIELD]},'review-observation-original-unknown-exact');facts=rr.original_complete_region(before,region_ref['path']);post=o.doc(post_ref);base=Path(before['operation']['outdir'])/'postguard-continuations'/proof['original_region']['sha256'];o.need(Path(post_ref['path']).parent.parent==base and re.fullmatch(r'[0-9a-f]{32}',Path(post_ref['path']).parent.name) is not None and Path(post_ref['path']).name=='post-reply.json' and post['command']==facts['command'] and post['original_region']==proof['original_region'],'review-observation-original-post-binding')
    after=rr.checked(post['response'],facts['command']);b=copy.deepcopy(before['proof_before']);c=copy.deepcopy(after);x=b['base_proof'].pop('epoch');y=c['base_proof'].pop('epoch');o.need(type(x) is int and type(y) is int and 0<=x<y and b==c,'review-observation-only-positive-epoch-change');o.need(datetime.fromisoformat(o.doc(facts['native_metadata'])['completed_at'])<=datetime.fromisoformat(post['request_started_at'])<=datetime.fromisoformat(post['observed_at'])<=datetime.fromisoformat(result['at']),'review-observation-original-post-time');new=rr.observation_operation(original['operation']);o.need(new['revision']!=original['operation']['revision'] and new['outdir']!=original['operation']['outdir'],'review-observation-new-revision-required')
    return {'manifest':proof['facts']['manifest'],'new_operation':new,'old_native':facts,'old_epochs':{'before':x,'post':y},'failed_engine_indices':[*proof['facts']['failed_engine_indices'],len(engine['calls'])-1],'failed_calls':parent['calls'],'old_PNG_approved':False,'fresh_observation_required':True}

def plan_observation(parent_ref,engine_ref,region_ref,post_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','review-observation-canonical-originals');prior,codes=observation_tip(parent,release_ref,before_refs,installed=installed);facts=observation_original(parent,engine,region_ref,post_ref,prior);out=Path(facts['new_operation']['outdir']);top=Path(o.doc(region_ref)['operation']['outdir']);o.need(not out.exists() and all(not (top/n).exists() for n in ('review-region.png','registration.json','preview-registration.json')),'review-observation-no-new-capture-or-registration')
    return {'kind':KIND,'recovery_stage':'fresh-observation-revision','order':parent['order'],'original_parent':parent_ref,'original_engine':engine_ref,'original_region':region_ref,'original_post':post_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':previous.previous.worker_evidence(parent,engine_ref,worker_ref),'ui_used':False}

def verify_observation_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-observation-revision'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']=='fresh-observation-revision' and current.get(FIELD)==proof_ref and p['order']==current['order'] and Path(proof_ref['path'])==base/'proof.json' and p['ui_used'] is False and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-observation-canonical-stage-proof')
    for n in ('parent','engine','region'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'review-observation-immutable-original-archive')
    o.need(len(p['before_sources'])==2 and all(Path(r['path'])==base/Path(r['path']).name and Path(r['path']).name in ('review_capture_focus.py.before','review_region_capture.py.before') for r in p['before_sources']),'review-observation-old-source-archive')
    o.need(datetime.fromisoformat(o.doc(p['original_post'])['observed_at'])<=datetime.fromisoformat(p['at']),'review-observation-authorization-after-failed-post');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);prior,codes=observation_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=observation_original(parent,engine,p['original_region'],p['original_post'],prior,archived_region=o.doc(p['region_archive']));expected_files={facts['old_native']['native_metadata']['path']:facts['old_native']['native_metadata'],facts['old_native']['raw_image']['path']:facts['old_native']['raw_image'],p['original_post']['path']:p['original_post']};o.need(len(p['attempt_archives'])==3 and {x['original']['path'] for x in p['attempt_archives']}==set(expected_files),'review-observation-complete-original-attempt-archives')
    for x in p['attempt_archives']:o.need(x['original']['sha256']==expected_files[x['original']['path']]['sha256']==x['archive']['sha256'] and Path(x['archive']['path'])==base/'attempt'/Path(x['original']['path']).name,'review-observation-original-attempt-archive-binding');o.raw(x['archive']);o.raw(x['original'])
    evidence=previous.previous.worker_evidence(parent,p['original_engine'],p['worker']);expected=recovered(parent,engine,proof_ref)[0];o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==evidence and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'review-observation-original-history-preserved')
    return {**prior,'kind':KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['region_archive'],p['original_post'],*p['before_sources'],p['release'],*[x['archive'] for x in p['attempt_archives']],*evidence]}

def observation_stage_calls(engine):
    parent=o.doc(o.ref(o.location(engine['order'])/'launcher.json'));proof=engine[FIELD];o.need(parent.get(FIELD)==proof,'review-observation-parent-engine-proof');verify_observation_stage(parent,proof);p=o.doc(proof);old=o.doc(p['engine_archive']);expected=recovered(o.doc(p['parent_archive']),old,proof)[1];o.need(engine['calls'][:len(old['calls'])]==old['calls'] and engine['resolved_errors']==expected['resolved_errors'] and engine['order']==parent['order'] and engine['scope_sha256']==parent['scope_sha256'],'review-observation-engine-prefix');return [c for i,c in enumerate(engine['calls']) if i not in p['facts']['failed_engine_indices']]

def recover_observation(parent_ref,engine_ref,region_ref,post_ref,worker_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-observation-revision'/parent_ref['sha256'];state=Path(region_ref['path'])
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b,state.with_suffix('.lock').open('a') as c:
        for lock in (a,b,c):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_region':region_ref,'original_post':post_ref,'worker':worker_ref,'release':release_ref}.items()) and sorted(r['sha256'] for r in before_refs)==sorted(r['sha256'] for r in p['before_sources']),'review-observation-same-recovery-inputs')
        else:
            p=plan_observation(parent_ref,engine_ref,region_ref,post_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base);(base/'attempt').mkdir(exist_ok=True)
            for n,r in (('parent',parent_ref),('engine',engine_ref),('region',region_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['attempt_archives']=[]
            for r in (p['facts']['old_native']['native_metadata'],p['facts']['old_native']['raw_image'],post_ref):
                original={k:r[k] for k in ('path','sha256')};p['attempt_archives'].append({'original':original,'archive':h.immutable_bytes(base/'attempt'/Path(r['path']).name,o.raw(original))})
            p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);original=o.doc(p['region_archive']);newregion={**original,'observation_revision':proof};lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-observation-current-lease');previous.previous.current_ledgers(parent,engine);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe),h.exact_metadata_state(state,p['region_archive'],newregion)];verify_observation_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        previous.previous.current_ledgers(parent,engine)
        for path,value in ((state,newregion),(folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':p['recovery_stage'],'state':'reconciled','launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'region':o.ref(state),'proof':proof,'ui_used':False}

QUALITY_STAGE='waiting-quality-source-admission'
def quality_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);root=ROOT/'skills/negative-review-complaints';paths={str(root/'scripts'/n) for n in ('review_capture_focus.py','program_review_quality.py')};test=str(root/'tests/test_review_quality_header_locator.py');sources=[t for t in rel['targets'] if t['target'] in paths];old={Path(r['path']).name.removesuffix('.before'):r for r in before_refs}
    base_ref=rel.get('quality_admission_base_release');base=o.doc(base_ref) if base_ref else rel
    if base_ref:
        hp=str(root/'scripts/initial_ledger_recovery.py');newtargets=rel['targets'];o.need(rel['kind']==base['kind']=='supervisor-reviewed-source-release-v1' and len(newtargets)==2 and {t['target'] for t in newtargets}=={str(root/'scripts/review_capture_focus.py'),hp} and all(t['mode']=='0644' for t in newtargets),'quality-history-exact-two-source-release')
        o.need(len(before_refs)==3 and set(old)=={'review_capture_focus.py','program_review_quality.py','initial_ledger_recovery.py'},'quality-history-exact-three-before-sources')
    else:o.need(len(before_refs)==2 and set(old)=={'review_capture_focus.py','program_review_quality.py'},'quality-admission-exact-two-before-sources')
    targets=base['targets'];sources=[t for t in targets if t['target'] in paths]
    o.need(base['kind']=='supervisor-reviewed-source-release-v1' and len(sources)==2 and len(targets) in (2,3) and len({t['target'] for t in targets})==len(targets) and all(t['target'] in paths|{test} and t['mode']=='0644' for t in targets),'quality-admission-exact-reviewed-sources')
    # Only the old Q bytes named by this reviewed base may satisfy historical
    # source pins. Current installed CODE still receives its own final SHA check.
    qpath=str(root/'scripts/program_review_quality.py');qr=old['program_review_quality.py'];qt=next(t for t in sources if t['target']==qpath);o.need(qr['sha256']==qt['old_sha256'],'quality-history-old-Q-reviewed-binding');o.raw(qr)
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[{'target':qpath,'archive':qr},*extra_source_archives]);codes=copy.deepcopy(prior['code_refs'])
    for t in sources:
        r=old[Path(t['target']).name];o.raw(r);o.raw(t['after']);previous_ref=next(x for x in codes if x['path']==t['target']);o.need(previous_ref['sha256']==t['old_sha256']==r['sha256'],'quality-admission-original-source-pin');codes[codes.index(previous_ref)]={'path':t['target'],'sha256':t['after']['sha256']}
    if base_ref:
        for t in newtargets:
            r=next(x for x in codes if x['path']==t['target']);o.need(t['old_sha256']==r['sha256'],'quality-history-publication-before-pin');o.raw(t['after'])
            if t['target']==hp:o.need(old['initial_ledger_recovery.py']['sha256']==r['sha256'],'quality-history-helper-before-pin');o.raw(old['initial_ledger_recovery.py'])
            codes[codes.index(r)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return prior,codes

def quality_facts(parent,engine,handoff_ref,prior,*,engine_ref=None):
    import review_region_capture as rr
    p=o.doc(parent[FIELD]);folder=o.location(parent['order']);child=parent.get('child') or {};request=o.doc(handoff_ref)
    o.need(parent['status']==engine['status']=='waiting' and not parent.get('error') and not engine.get('error') and not engine.get('acceptance') and child.get('status')=='waiting' and child.get('handoff')==engine.get('handoff')==handoff_ref and child.get('engine')==(engine_ref or o.ref(folder/'engine.json')) and child.get('order')==parent['order'],'quality-admission-original-waiting-boundary')
    o.need(p['recovery_stage']=='fresh-observation-revision' and request['kind']=='complaint-execution-handoff-v1' and request['response_kind']==engine['waiting_for']==child['waiting_for']=='complaint-region-qa-response-v1' and request['order']==parent['order'] and request['phase']==engine['phase']=='collect' and request['company']==o.validate(parent['order'])['companies'][engine['index']] and Path(handoff_ref['path'])==folder/'handoffs'/(str(len(engine['calls']))+'.json'),'quality-admission-original-QA-handoff')
    failed=p['facts']['failed_engine_indices'];o.need(all(c['state']=='returned' and c.get('applied') is True for i,c in enumerate(engine['calls']) if i not in failed),'quality-admission-no-unknown-or-new-failure')
    for call in parent['calls'][len(prior['failed_calls']):]:
        launch=o.doc(call['launch']);result=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==result['argv'] and result['launch']==call['launch'] and result['returncode']==0,'quality-admission-natural-returned-calls')
    last=o.doc(parent['calls'][-1]['result']);o.need(len(parent['calls'])>len(prior['failed_calls']) and json.loads(last['stdout'])==child and child.get('kind')=='complaint-execution-child-result-v1','quality-admission-last-exit-exact-child')
    preview=o.doc(request['preview']);manifest=o.doc(request['manifest']);o.need(request['manifest']==p['facts']['manifest'] and preview['state']=='awaiting-visual-review' and preview.get('observation_revision')==parent[FIELD] and preview['review_keys']==manifest['review_keys']==[request['review_key']],'quality-admission-original-preview')
    # Pure local full v2 pixel/source validation, without recursively consulting
    # the mutable parent's new admission while replaying this admission itself.
    command=rr.region_command(rr.rc.command_from_inputs(*(preview[k] for k in ('job','source','envelope','profile','page')),preview['review_keys']));rr.verify_normal_v2(preview,command);rr.region.validate(preview['derivation'],preview['proof_before'],preview['geometry_before']);original=rr.rc.document(preview['revision_registration']);o.need(not any(k in original for k in ('observation_revision','revision_registration','observation_revision_contract')),'quality-admission-plain-child-required');rr.verify(preview['revision_registration']['path'],allow_preview=True);expected=dict(preview)
    for k in ('observation_revision','observation_revision_contract','revision_registration'):expected.pop(k)
    o.need(expected==original and preview['observation_revision_contract']==rr.OBSERVATION_REVISION and preview['revision']==p['facts']['new_operation']['revision'] and Path(request['preview']['path'])==Path(p['facts']['new_operation']['outdir']).parent.parent/'preview-registration.json','quality-admission-exact-top-child-preview')
    directory=Path(request['preview']['path']).parent/'program-quality';evidence=[o.ref(directory/n) for n in ('intent.json','plan.json','first-ocr.json','exception.json')];intent,plan,first,exception=[o.doc(r) for r in evidence];o.need(intent['preview']==exception['preview']==request['preview'] and exception['reason']==request.get('program_quality_exception')=='review-quality-nickname-range-unavailable' and plan['image']==preview['image'] and first['kind']=='local-vision-cell-ocr-v1','quality-admission-original-program-attempt')
    return {'handoff':handoff_ref,'preview':request['preview'],'manifest':request['manifest'],'quality_attempt':evidence,'failed_engine_indices':failed,'failed_calls':prior['failed_calls']}

def plan_quality(parent_ref,engine_ref,handoff_ref,release_ref,before_refs,*,installed=False,archived_engine_ref=None):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','quality-admission-canonical-originals');prior,codes=quality_tip(parent,release_ref,before_refs,installed=installed);facts=quality_facts(parent,engine,handoff_ref,prior,engine_ref=engine_ref)
    return {'kind':KIND,'recovery_stage':QUALITY_STAGE,'order':parent['order'],'original_parent':parent_ref,'original_engine':engine_ref,'prior_recovery':parent[FIELD],'handoff':handoff_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'ui_used':False}

def verify_quality_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-quality-source-admission'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']==QUALITY_STAGE and p['ui_used'] is False and p['order']==current['order'] and current.get(FIELD)==proof_ref and Path(proof_ref['path'])==base/'proof.json' and datetime.fromisoformat(p['at']).utcoffset() is not None,'quality-admission-canonical-proof')
    for n in ('parent','engine'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'quality-admission-original-archives')
    o.need(len(p['before_sources']) in (2,3) and all(Path(r['path'])==base/Path(r['path']).name for r in p['before_sources']),'quality-admission-old-source-archives');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'quality-admission-direct-prior-proof');prior,codes=quality_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives)
    # The child's original engine ref is an immutable snapshot of the waiting
    # engine. Do not reread its mutable canonical path after the FIELD append.
    facts=quality_facts(parent,engine,p['handoff'],prior,engine_ref=p['original_engine'])
    o.need(p['facts']==facts and p['code_refs']==codes and current['calls'][:len(parent['calls'])]==parent['calls'] and current.get('resolved_errors')==parent.get('resolved_errors') and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'quality-admission-original-history-preserved');return {**prior,'proof':proof_ref,'code_refs':codes,'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['handoff'],*p['before_sources'],p['release'],*p['facts']['quality_attempt']]}

def admit_quality(parent_ref,engine_ref,handoff_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-quality-source-admission'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'handoff':handoff_ref,'release':release_ref}.items()) and sorted(r['sha256'] for r in before_refs)==sorted(r['sha256'] for r in p['before_sources']),'quality-admission-same-inputs')
        else:
            p=plan_quality(parent_ref,engine_ref,handoff_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True);o.canonical(base)
            for n,r in (('parent',parent_ref),('engine',engine_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp={**parent,FIELD:proof};newe={**engine,FIELD:proof};lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'quality-admission-current-lease');previous.previous.current_ledgers(parent,engine);refs=[h.exact_metadata_state(folder/'launcher.json',p['parent_archive'],newp),h.exact_metadata_state(folder/'engine.json',p['engine_archive'],newe)];verify_quality_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':QUALITY_STAGE,'launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

def quality_response(parent_ref,workshop_ref):
    import program_review_quality as quality
    parent=o.doc(parent_ref);proof=parent[FIELD];verify_quality_stage(parent,proof);p=o.doc(proof);o.need(parent['status']=='waiting' and parent['child']['handoff']==p['handoff'],'quality-response-original-waiting-parent');workshop=o.doc(workshop_ref);folder=Path(workshop_ref['path']).parent;original_request=o.doc(o.ref(folder/'request.json'));order=o.doc(parent['order']);o.need(folder.parent==ROOT/'runtime/standalone-workshop-director/attempts' and Path(workshop_ref['path']).name=='handoff.json' and folder.name==original_request['attempt_id'] and folder.name.startswith(workshop['task_id']+'-') and original_request['task']['id']==workshop['task_id'] and original_request['task']['day']==order['day'] and original_request['context']['order']==parent['order'] and workshop['original_outer']==original_request['task']['outer'],'quality-response-original-task-order-clock');o.need(workshop['kind']=='workshop-handoff-v1' and workshop['details']['parent_handoff']==p['handoff'],'quality-response-original-workshop-handoff');request=o.doc(p['handoff']);out=Path(request['preview']['path']).parent/'program-quality-repairs'/proof['sha256'];a=quality.create(request['preview'],out);base=o.location(parent['order'])/'quality-responses'/p['handoff']['sha256']/proof['sha256'];base.mkdir(parents=True,exist_ok=True);response=o.immutable(base/'parent-response.json',{'kind':request['response_kind'],'request':p['handoff'],'attestation':a});wrapped=o.immutable(base/'workshop-response.json',{'kind':'workshop-handoff-response-v1','request':workshop_ref,'task_id':workshop['task_id'],'parent_response':response});return {'parent_response':response,'workshop_response':wrapped,'quality_attestation':a,'ui_used':False,'business_acceptance':False}

SHORTCUT_STAGE='review-shortcut-reset'
SHORTCUT_ERROR='nondefault-review-shortcut:中差评（1-3心）'
def shortcut_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);names=('review_capture_focus.py','initial_ledger_recovery.py','bridge-workflow.py');paths=[str(ROOT/'skills'/('douyin-laike-operator' if n=='bridge-workflow.py' else 'negative-review-complaints')/'scripts'/n) for n in names]
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(rel['targets'])==len(before_refs)==3 and {t['target'] for t in rel['targets']}==set(paths) and all(t['mode']=='0644' for t in rel['targets']) and [Path(r['path']).name for r in before_refs]==[n+'.before' for n in names],'review-shortcut-exact-three-reviewed-sources')
    for r in before_refs:o.raw(r)
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[{'target':paths[2],'archive':before_refs[2]},*extra_source_archives]);codes=copy.deepcopy(prior['code_refs'])
    for path,archive in zip(paths,before_refs):
        t=next(t for t in rel['targets'] if t['target']==path);r=next(r for r in codes if r['path']==path);o.need(r['sha256']==archive['sha256']==t['old_sha256'],'review-shortcut-admission-base');o.raw(t['after']);codes[codes.index(r)]={'path':path,'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return prior,codes

def shortcut_facts(parent,engine,operator_ref,scope_ref,prior,*,archived_operator=None):
    import importlib.util
    spec=importlib.util.spec_from_file_location('review_shortcut_original_operator',ROOT/'skills/douyin-laike-operator/scripts/bridge-workflow.py');bw=importlib.util.module_from_spec(spec);spec.loader.exec_module(bw)
    from readonly_tick_snapshot import decode
    from dom_evidence import context,identity,nodes,all_store_scope,VERSION
    from review_filter_loading import validate_filter_values
    folder=o.location(parent['order']);order=o.validate(parent['order']);o.need(parent['status']==engine['status']=='hold' and parent.get('error')=='execution-child-stopped' and engine.get('error')==SHORTCUT_ERROR and not parent.get('completion') and not engine.get('acceptance'),'review-shortcut-known-parent-hold')
    if parent.get('child'):
        good=o.doc(parent['calls'][-2]['result']);o.need(good['returncode']==0 and json.loads(good['stdout'])==parent['child'] and parent['child']['kind']=='complaint-execution-child-result-v1','review-shortcut-last-known-child-receipt')
    ci=engine['index'];company=order['companies'][ci];a=engine['companies'][ci]['artifacts'];job_ref=a['unit_artifacts']['work_order'];job=o.doc(job_ref);unit=folder/'companies'/str(ci)/'units'/str(a['unit_index']);s=archived_operator if archived_operator is not None else o.doc(operator_ref);scope=o.doc(scope_ref)
    o.need(a['unit_phase']=='acquire' and Path(job_ref['path']).parent.parent==unit/'operator' and Path(job['work_order_path'])==Path(job_ref['path']) and Path(job['workflow_path'])==Path(operator_ref['path'])==Path(job_ref['path']).with_name('workflow.json') and job['action']=='acquire' and job.get('source_purpose')=='complaint-draft-only-current-dispatch' and job.get('submit_enabled') is False and job.get('send_enabled') is False and job.get('progress_updates_enabled') is False and job['company']==company['company'] and str(job['groupid'])==company['groupid'],'review-shortcut-original-job-scope')
    o.need(s['state']=='running' and s['phase']=='verifyFilter' and s['last_error']['code']=='nondefault-review-shortcut' and s['last_error']['message']==SHORTCUT_ERROR and s['tab_id']==parent['tab_id'] and s['work_order_id']==job['work_order_id'] and s['fingerprint']==bw.fingerprint(job) and s['date_range']=={k:job['date_range'][k] for k in ('start','end')} and s['identity_contract']==job['identity_contract']=='merchant-v2' and s['identity']==job['identity_baseline']==job['known_company_identities'][str(job['groupid'])] and not bw.has_side_effect_intent(s),'review-shortcut-exact-original-operator')
    o.need(s['calls'] and all(c['state']=='confirmed' for c in s['calls']) and s['calls'][-1]['phase']=='pageEnd' and not any(c['command'].get('kind') in ('export','export-submit','download') or c['phase'] in ('clearReviewNegativeShortcut','verifyClearedReviewShortcut') for c in s['calls']),'review-shortcut-no-export-unknown-or-prior-toggle')
    last=s['calls'][-1];o.need(last['command']['op']=='click' and last['command']['kind']=='filter' and last['result']['clicked']['name']==str(int(s['date_range']['end'][-2:])) and last['command']['locator']=={'by':'selector','value':last['result']['clicked']['selector']},'review-shortcut-original-end-confirmed')
    o.need(Path(scope_ref['path']).parent==Path(operator_ref['path']).parent/'bridge-evidence','review-shortcut-original-scope-path');decode(scope,s['tab_id'],scope['scope']['windowId']);before=context(scope['before'],s['tab_id'],job['groupid']);after=context(scope['after'],s['tab_id'],job['groupid']);o.need(before==after and scope['ping'].get('version')==VERSION and scope['ping'].get('safety')=='DOM-only' and scope['tree']==o.doc(s['last_tree']),'review-shortcut-original-scope-binding');validate_filter_values(scope['tree'],job['date_range']);all_store_scope(scope['tree']);bw.verified_review_filter(scope['tree'],job['date_range']);target=bw.review_shortcut_reset_target(scope['tree']);o.need(target is not None,'review-shortcut-original-not-selected')
    if any('UserCard-index-module__outer--' in n.get('attributes',{}).get('class','') for n in nodes(scope['tree'])):identity(scope['tree'],s['identity'])
    failed=[*o.doc(parent[FIELD])['facts']['failed_engine_indices'],len(engine['calls'])-1];o.need(len(set(failed))==len(failed) and all(c['state']=='returned' and c.get('applied') is True for i,c in enumerate(engine['calls']) if i not in failed),'review-shortcut-no-other-unknown');call=engine['calls'][-1];o.need(call['state']=='failed' and call['error']==SHORTCUT_ERROR and call['step']=='collect' and call['company_index']==ci and call['context']=={'order':order,'company':company,'artifacts':a,'folder':str(folder/'companies'/str(ci)),'phase':'collect'},'review-shortcut-original-engine-failure')
    for c in parent['calls'][len(prior['failed_calls']):-1]:o.need(c['state']=='returned' and o.doc(c['result'])['returncode']==0,'review-shortcut-unreviewed-outer-failure')
    c=parent['calls'][-1];launch=o.doc(c['launch']);result=o.doc(c['result']);o.need(c['state']=='returned' and c['argv']==launch['argv']==result['argv'] and result['launch']==c['launch'] and result['returncode']==2 and result['stderr']=='' and json.loads(result['stdout'])=={'ok':False,'error':SHORTCUT_ERROR},'review-shortcut-original-natural-rc2')
    return {'operator':operator_ref,'job':job_ref,'scope':scope_ref,'tree':s['last_tree'],'target':target,'ledger_current':a['ledger_current'],'failed_engine_indices':failed,'failed_calls':parent['calls'],'completed_units':a['completed_units']}

def plan_shortcut(parent_ref,engine_ref,operator_ref,scope_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','review-shortcut-canonical-originals');prior,codes=shortcut_tip(parent,release_ref,before_refs,installed=installed);facts=shortcut_facts(parent,engine,operator_ref,scope_ref,prior);evidence=previous.previous.worker_evidence(parent,engine_ref,worker_ref);previous.previous.current_ledgers(parent,engine)
    return {'kind':KIND,'recovery_stage':SHORTCUT_STAGE,'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}

def shortcut_operator(old,proof,at):
    new=copy.deepcopy(old);new.setdefault('resolved_errors',[]).append({**new.pop('last_error'),'resolved_at':at,'next_phase':'verifyFilter','recovery_proof':proof});new.update(review_shortcut_reset_recovery=proof,updated_at=at);return new

def verify_shortcut_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.review-shortcut-reset-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']==SHORTCUT_STAGE and p['ui_used'] is False and current[FIELD]==proof_ref and Path(proof_ref['path'])==base/'proof.json' and datetime.fromisoformat(p['at']).utcoffset() is not None,'review-shortcut-canonical-proof')
    for name in ('parent','engine','operator'):o.need(Path(p[name+'_archive']['path'])==base/('original-'+name+'.json') and p[name+'_archive']['sha256']==p['original_'+name]['sha256'],'review-shortcut-original-archive')
    o.need(len(p['before_sources'])==3 and all(Path(r['path'])==base/Path(r['path']).name for r in p['before_sources']),'review-shortcut-source-archives');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'review-shortcut-original-prior');prior,codes=shortcut_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=shortcut_facts(parent,engine,p['original_operator'],p['facts']['scope'],prior,archived_operator=o.doc(p['operator_archive']));expected=recovered(parent,engine,proof_ref)[0];o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==previous.previous.worker_evidence(parent,p['original_engine'],p['worker']) and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'review-shortcut-preserved-history')
    if o.doc(o.ref(folder/'launcher.json')).get(FIELD)==proof_ref:
        actual=o.doc(o.ref(p['original_operator']['path']));old=o.doc(p['operator_archive']);delta=shortcut_operator(old,proof_ref,p['at'])
        o.need(actual.get('review_shortcut_reset_recovery')==proof_ref and actual['calls'][:len(old['calls'])]==old['calls'] and actual.get('resolved_errors',[])[:len(delta['resolved_errors'])]==delta['resolved_errors'] and actual['checkpoints'][:len(old['checkpoints'])]==old['checkpoints'] and all(actual.get(k)==old.get(k) for k in ('work_order_id','fingerprint','company','groupid','date_range','tab_id','identity','entry_identity','identity_contract')),'review-shortcut-operator-continuation')
    return {**prior,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['operator_archive'],*p['before_sources'],p['release'],facts['scope'],facts['tree'],*p['worker_evidence']]}

def recover_shortcut(parent_ref,engine_ref,operator_ref,scope_ref,worker_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.review-shortcut-reset-recovery'/parent_ref['sha256'];operator_path=Path(operator_ref['path'])
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b,operator_path.with_name('.bridge-execution.lock').open('a') as c:
        for lock in (a,b,c):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker':worker_ref,'release':release_ref}.items()) and p['facts']['scope']==scope_ref,'review-shortcut-same-recovery')
        else:
            p=plan_shortcut(parent_ref,engine_ref,operator_ref,scope_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True)
            for name,r in (('parent',parent_ref),('engine',engine_ref),('operator',operator_ref)):p[name+'_archive']=h.immutable_bytes(base/('original-'+name+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);news=shortcut_operator(o.doc(p['operator_archive']),proof,p['at']);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'review-shortcut-current-lease');previous.previous.current_ledgers(parent,engine)
        refs=[h.exact_metadata_state(path,old,new) for path,old,new in ((folder/'launcher.json',p['parent_archive'],newp),(folder/'engine.json',p['engine_archive'],newe),(operator_path,p['operator_archive'],news))];verify_shortcut_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        for path,value in ((operator_path,news),(folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':SHORTCUT_STAGE,'launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'operator':o.ref(operator_path),'proof':proof,'ui_used':False}

RECHECK_STAGE='recheck-source-tab-activation'
RECHECK_ERROR='alias-v3-active-tab-changed'
def recheck_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);names=('review_capture_focus.py','initial_ledger_recovery.py','complaint_execution_ports.py','review_capture_tab.py');paths=[str(ROOT/'skills/negative-review-complaints/scripts'/n) for n in names]
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(rel['targets'])==len(before_refs)==4 and {t['target'] for t in rel['targets']}==set(paths) and all(t['mode']=='0644' for t in rel['targets']) and [Path(r['path']).name for r in before_refs]==[n+'.before' for n in names],'recheck-focus-exact-four-sources')
    for r in before_refs:o.raw(r)
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[{'target':paths[2],'archive':before_refs[2]},*extra_source_archives]);codes=copy.deepcopy(prior['code_refs'])
    for path,archive in zip(paths,before_refs):
        t=next(t for t in rel['targets'] if t['target']==path);r=next(r for r in codes if r['path']==path);o.need(r['sha256']==archive['sha256']==t['old_sha256'],'recheck-focus-admission-base');o.raw(t['after']);codes[codes.index(r)]={'path':path,'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return prior,codes

def recheck_facts(parent,engine,transport_ref,prior,*,require_preinput=False):
    import review_capture_tab as tab
    import case_alias_v3 as alias
    folder=o.location(parent['order']);order=o.validate(parent['order']);o.need(parent['status']==engine['status']=='hold' and parent.get('error')=='execution-child-stopped' and engine.get('error')==RECHECK_ERROR and not parent.get('completion') and not engine.get('acceptance'),'recheck-focus-original-hold')
    ci=engine['index'];a=engine['companies'][ci]['artifacts'];x=a['unit_artifacts'];company=order['companies'][ci];unit=folder/'companies'/str(ci)/'units'/str(a['unit_index']);inputs={k:x[k] for k in ('job','source','profile','envelope')};binding=tab.derive_recheck(inputs)
    o.need(a['unit_phase']=='recheck' and all(Path(r['path']).parent==unit for r in inputs.values()) and binding['scope']['groupid']==company['groupid'] and o.doc(x['job'])['company']==company['company'] and not x.get('source_activation'),'recheck-focus-original-source-unit')
    mr=x['alias_manifest'];m=o.doc(mr);alias.v.canonical_manifest(m,mr);alias.v.context(m);o.need(m['fresh']=={'fresh_job':x['job'],'fresh_profile':x['profile'],'normal_before':x['envelope']} and m['root']==company['root'] and m['review_key']==x['recheck_keys'][x['review_index']] and not x['operations'],'recheck-focus-original-alias')
    base=alias.v.base(m);raw=o.doc(transport_ref);o.need(Path(transport_ref['path']).parent.parent==base/'transport' and Path(transport_ref['path']).name=='001.json' and raw['command']=={'op':'tabs'} and raw['response'].get('ok') is True and tab.classify(raw['response']['result'],binding)=='original-record-active','recheck-focus-original-tabs-only')
    if require_preinput:
        o.need(list((base/'transport').glob('*/*.json'))==[Path(transport_ref['path'])] and not any((base/n).exists() for n in ('operation.json','unbound-case.json','receipt.json','alias-receipt.json')) and not list((unit/'.review-recheck-tab-activation').glob('*.json')),'recheck-focus-no-original-input')
    failed=[*o.doc(parent[FIELD])['facts']['failed_engine_indices'],len(engine['calls'])-1];o.need(len(failed)==len(set(failed)) and all(c['state']=='returned' and c.get('applied') is True for i,c in enumerate(engine['calls']) if i not in failed),'recheck-focus-no-other-unknown');last=engine['calls'][-1];o.need(last['state']=='failed' and last['error']==RECHECK_ERROR and last['step']=='collect' and last['company_index']==ci and last['context']=={'order':order,'company':company,'artifacts':a,'folder':str(folder/'companies'/str(ci)),'phase':'collect'},'recheck-focus-original-failed-call')
    for c in parent['calls'][len(prior['failed_calls']):-1]:o.need(c['state']=='returned' and o.doc(c['result'])['returncode']==0,'recheck-focus-other-outer-error')
    call=parent['calls'][-1];launch=o.doc(call['launch']);exit=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==exit['argv'] and exit['launch']==call['launch'] and exit['returncode']==2 and exit['stderr']=='' and json.loads(exit['stdout'])=={'ok':False,'error':RECHECK_ERROR},'recheck-focus-natural-preinput-exit')
    if parent.get('child'):
        prior_exit=next((o.doc(c['result']) for c in reversed(parent['calls'][:-1]) if o.doc(c['result'])['returncode']==0),None);o.need(prior_exit is not None and json.loads(prior_exit['stdout'])==parent['child'] and parent['child']['kind']=='complaint-execution-child-result-v1','recheck-focus-last-known-child')
    return {'manifest':mr,'transport':transport_ref,'binding':binding,'ledger_current':a['ledger_current'],'completed_units':a['completed_units'],'failed_engine_indices':failed,'failed_calls':parent['calls']}

def plan_recheck(parent_ref,engine_ref,transport_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','recheck-focus-canonical-originals');prior,codes=recheck_tip(parent,release_ref,before_refs,installed=installed);facts=recheck_facts(parent,engine,transport_ref,prior,require_preinput=True);evidence=previous.previous.worker_evidence(parent,engine_ref,worker_ref);previous.previous.current_ledgers(parent,engine)
    return {'kind':KIND,'recovery_stage':RECHECK_STAGE,'original_parent':parent_ref,'original_engine':engine_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}

def verify_recheck_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.recheck-source-tab-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']==RECHECK_STAGE and p['ui_used'] is False and current[FIELD]==proof_ref and Path(proof_ref['path'])==base/'proof.json' and datetime.fromisoformat(p['at']).utcoffset() is not None,'recheck-focus-canonical-proof')
    for n in ('parent','engine'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'recheck-focus-original-archives')
    o.need(len(p['before_sources'])==4 and all(Path(r['path'])==base/Path(r['path']).name for r in p['before_sources']),'recheck-focus-source-archives');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'recheck-focus-original-prior');prior,codes=recheck_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=recheck_facts(parent,engine,p['facts']['transport'],prior);expected=recovered(parent,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==previous.previous.worker_evidence(parent,p['original_engine'],p['worker']) and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'recheck-focus-preserved-history')
    return {**prior,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],*p['before_sources'],p['release'],p['facts']['manifest'],p['facts']['transport'],*p['worker_evidence']]}

def recover_recheck(parent_ref,engine_ref,transport_ref,worker_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.recheck-source-tab-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref}.items()) and p['facts']['transport']==transport_ref and [(Path(r['path']).name,r['sha256']) for r in before_refs]==[(Path(r['path']).name,r['sha256']) for r in p['before_sources']],'recheck-focus-same-recovery')
        else:
            p=plan_recheck(parent_ref,engine_ref,transport_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True)
            for n,r in (('parent',parent_ref),('engine',engine_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);newp,newe=recovered(parent,engine,proof);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'recheck-focus-current-lease');previous.previous.current_ledgers(parent,engine)
        refs=[h.exact_metadata_state(path,old,new) for path,old,new in ((folder/'launcher.json',p['parent_archive'],newp),(folder/'engine.json',p['engine_archive'],newe))];verify_recheck_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':RECHECK_STAGE,'launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'proof':proof,'ui_used':False}

NORMAL_STAGE='normal-mixed-action-profile'
NORMAL_ERROR='parent-normal-mixed-action-labels-unreviewed'
def normal_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    rel=o.doc(release_ref);names=('review_capture_focus.py','initial_ledger_recovery.py','complaint_execution_normal.py');paths=[str(ROOT/'skills/negative-review-complaints/scripts'/n) for n in names]
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(rel['targets'])==len(before_refs)==3 and {t['target'] for t in rel['targets']}==set(paths) and all(t['mode']=='0644' for t in rel['targets']) and [Path(r['path']).name for r in before_refs]==[n+'.before' for n in names],'normal-profile-exact-three-sources')
    for r in before_refs:o.raw(r)
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[{'target':paths[2],'archive':before_refs[2]},*extra_source_archives]);codes=copy.deepcopy(prior['code_refs'])
    for path,archive in zip(paths,before_refs):
        t=next(t for t in rel['targets'] if t['target']==path);r=next(r for r in codes if r['path']==path);o.need(r['sha256']==archive['sha256']==t['old_sha256'],'normal-profile-admission-base');o.raw(t['after']);codes[codes.index(r)]={'path':path,'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return prior,codes

def normal_documents(job_ref,page_ref,schema):
    import complaint_execution_normal as normal_api
    job=o.doc(job_ref);page=o.doc(page_ref);profile,envelope,source=normal_api.build(job,page,page,image_only_text_schema=schema)
    return {'page':page,'profile':profile,'envelope':envelope,'source':source}

def normal_facts(parent,engine,page_ref,prior,*,require_no_outputs=False):
    import re,hashlib
    folder=o.location(parent['order']);order=o.validate(parent['order']);ci=engine['index'];a=engine['companies'][ci]['artifacts'];x=a['unit_artifacts'];unit=folder/'companies'/str(ci)/'units'/str(a['unit_index']);job=o.doc(x['job']);navigation=o.doc(x['navigation']);page=o.doc(page_ref)
    o.need(parent['status']==engine['status']=='hold' and parent.get('error')=='execution-child-stopped' and engine.get('error')==NORMAL_ERROR and not parent.get('completion') and not engine.get('acceptance') and a['unit_phase']=='normal' and not any(k in x for k in ('page','source','profile','envelope','alias_manifest','exact_manifest')),'normal-profile-exact-local-preinput-failure')
    o.need(Path(page_ref['path']).parent==unit and re.fullmatch(r'normal-[a-f0-9]{32}\.json',Path(page_ref['path']).name) and page.get('source')=='local-dom-bridge' and page['ping'].get('version')=='dom-only-20261021-11' and page['ping'].get('safety')=='DOM-only' and page['tab']['tabId']==parent['tab_id'] and job['company']==order['companies'][ci]['company'] and str(job['groupid'])==order['companies'][ci]['groupid'] and job['start']==a['units'][a['unit_index']]['start'] and job['end_exclusive']==a['units'][a['unit_index']]['end_exclusive'],'normal-profile-original-page-scope')
    o.need(navigation['phase']=='profileRequired' and navigation['stable_normal_verified'] is True and all(c['state']=='confirmed' for c in navigation['calls']),'normal-profile-complete-navigation');schema=navigation['parser_contract']['image_only_text_schema'];docs=normal_documents(x['job'],page_ref,schema);labels={r['action'] for r in docs['source']['rows']}
    o.need(len(labels)>1 and labels <= {'投诉','查看投诉结果','投诉审核中'} and set(docs['profile']['action'])=={'attributes'} and docs['profile']['image_only_text_schema']==schema,'normal-profile-original-mixed-labels')
    receipt=o.doc(x['acquisition']);wf={'path':str(Path(x['acquisition']['path']).parent/'workflow.json'),'sha256':receipt['workflow_sha256']};state=o.doc(wf);o.need(state['state']=='complete' and state['phase']=='done' and not state.get('last_error') and all(c['state']=='confirmed' for c in state['calls']) and receipt['work_order_id']==job['source_work_order_id'] and job['source_receipt']==x['acquisition']['path'] and job['source_receipt_sha256']==x['acquisition']['sha256'],'normal-profile-original-acquisition-complete')
    failed=[*o.doc(parent[FIELD])['facts']['failed_engine_indices'],len(engine['calls'])-1];o.need(len(failed)==len(set(failed)) and all(c['state']=='returned' and c.get('applied') is True for i,c in enumerate(engine['calls']) if i not in failed),'normal-profile-no-other-unknown');last=engine['calls'][-1];o.need(last['state']=='failed' and last['error']==NORMAL_ERROR and last['step']=='collect' and last['company_index']==ci and last['context']=={'order':order,'company':order['companies'][ci],'artifacts':a,'folder':str(folder/'companies'/str(ci)),'phase':'collect'},'normal-profile-original-failed-call');o.need(datetime.fromisoformat(last['intent_at'])<=datetime.fromisoformat(page['observed_at']),'normal-profile-page-before-call')
    for c in parent['calls'][len(prior['failed_calls']):-1]:o.need(c['state']=='returned' and o.doc(c['result'])['returncode']==0,'normal-profile-other-outer-failure')
    call=parent['calls'][-1];launch=o.doc(call['launch']);exit=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==exit['argv'] and exit['launch']==call['launch'] and exit['returncode']==2 and exit['stderr']=='' and json.loads(exit['stdout'])=={'ok':False,'error':NORMAL_ERROR},'normal-profile-natural-local-rc2')
    if parent.get('child'):
        good=next((o.doc(c['result']) for c in reversed(parent['calls'][:-1]) if o.doc(c['result'])['returncode']==0),None);o.need(good is not None and json.loads(good['stdout'])==parent['child'] and parent['child']['kind']=='complaint-execution-child-result-v1','normal-profile-last-known-child')
    outputs={'page':page_ref,**{k:{'path':str(unit/('normal-'+k+'.json')),'sha256':hashlib.sha256(o.encode(docs[k])).hexdigest()} for k in ('profile','envelope','source')}}
    if require_no_outputs:o.need(all(not Path(outputs[k]['path']).exists() for k in ('profile','envelope','source')),'normal-profile-output-already-exists')
    return {'page':page_ref,'job':x['job'],'navigation':x['navigation'],'acquisition':x['acquisition'],'workflow':wf,'schema':schema,'outputs':outputs,'company_index':ci,'unit_index':a['unit_index'],'ledger_current':a['ledger_current'],'completed_units':a['completed_units'],'failed_engine_indices':failed,'failed_calls':parent['calls']}

def plan_normal(parent_ref,engine_ref,page_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','normal-profile-canonical-originals');prior,codes=normal_tip(parent,release_ref,before_refs,installed=installed);facts=normal_facts(parent,engine,page_ref,prior,require_no_outputs=True);evidence=previous.previous.worker_evidence(parent,engine_ref,worker_ref);previous.previous.current_ledgers(parent,engine);o.need(datetime.fromisoformat(o.doc(worker_ref)['exited_at'])>=datetime.fromisoformat(o.doc(page_ref)['observed_at']),'normal-profile-page-after-worker-exit')
    return {'kind':KIND,'recovery_stage':NORMAL_STAGE,'original_parent':parent_ref,'original_engine':engine_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}

def recovered_normal(parent,engine,proof,outputs):
    parent,engine=recovered(parent,engine,proof);a=engine['companies'][engine['index']]['artifacts'];a['unit_artifacts'].update(copy.deepcopy(outputs));a['unit_phase']='ingest';return parent,engine

def verify_normal_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.normal-mixed-action-profile-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']==NORMAL_STAGE and p['ui_used'] is False and current[FIELD]==proof_ref and Path(proof_ref['path'])==base/'proof.json' and datetime.fromisoformat(p['at']).utcoffset() is not None,'normal-profile-canonical-proof')
    for n in ('parent','engine'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'normal-profile-original-archive')
    o.need(len(p['before_sources'])==3 and all(Path(r['path'])==base/Path(r['path']).name for r in p['before_sources']),'normal-profile-source-archives');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'normal-profile-prior-recovery');prior,codes=normal_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=normal_facts(parent,engine,p['facts']['page'],prior);expected=recovered_normal(parent,engine,proof_ref,facts['outputs'])[0]
    o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==previous.previous.worker_evidence(parent,p['original_engine'],p['worker']) and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'normal-profile-preserved-history')
    for r in facts['outputs'].values():o.raw(r)
    return {**prior,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],*p['before_sources'],p['release'],*facts['outputs'].values(),*p['worker_evidence']]}

def recover_normal(parent_ref,engine_ref,page_ref,worker_ref,release_ref,before_refs):
    folder=Path(parent_ref['path']).parent;base=folder/'.normal-mixed-action-profile-recovery'/parent_ref['sha256']
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        for lock in (a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (base/'proof.json').exists():
            proof=o.ref(base/'proof.json');p=o.doc(proof);o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'worker':worker_ref,'release':release_ref}.items()) and p['facts']['page']==page_ref and [(Path(r['path']).name,r['sha256']) for r in before_refs]==[(Path(r['path']).name,r['sha256']) for r in p['before_sources']],'normal-profile-same-recovery')
        else:
            p=plan_normal(parent_ref,engine_ref,page_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True)
            for n,r in (('parent',parent_ref),('engine',engine_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);docs=normal_documents(p['facts']['job'],page_ref,p['facts']['schema']);newp,newe=recovered_normal(parent,engine,proof,p['facts']['outputs']);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'normal-profile-current-lease');previous.previous.current_ledgers(parent,engine)
        refs=[h.exact_metadata_state(path,old,new) for path,old,new in ((folder/'launcher.json',p['parent_archive'],newp),(folder/'engine.json',p['engine_archive'],newe))]
        for k in ('profile','envelope','source'):o.need(o.immutable(Path(p['facts']['outputs'][k]['path']),docs[k])==p['facts']['outputs'][k],'normal-profile-derived-output-exact')
        verify_normal_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':NORMAL_STAGE,'launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'outputs':p['facts']['outputs'],'proof':proof,'ui_used':False}

ANCHOR_STAGE='switch-active-window-anchor'
ANCHOR_ERROR='read-recovery-window-anchor-required'
def anchor_tip(parent,release_ref,before_refs,*,installed,extra_source_archives=()):
    names=('review_capture_focus.py','initial_ledger_recovery.py','switch_read_recovery.py');paths=[str(ROOT/'skills'/('douyin-laike-operator' if n=='switch_read_recovery.py' else 'negative-review-complaints')/'scripts'/n) for n in names];rel=o.doc(release_ref)
    o.need(rel['kind']=='supervisor-reviewed-source-release-v1' and len(rel['targets'])==len(before_refs)==3 and {t['target'] for t in rel['targets']}==set(paths) and all(t['mode']=='0644' for t in rel['targets']) and [Path(r['path']).name for r in before_refs]==[n+'.before' for n in names],'switch-anchor-exact-three-sources')
    for r in before_refs:o.raw(r)
    prior=verify_recovered(parent,parent[FIELD],installed=False,extra_source_archives=[{'target':paths[2],'archive':before_refs[2]},*extra_source_archives]);codes=copy.deepcopy(prior['code_refs'])
    for path,archive in zip(paths,before_refs):
        t=next(t for t in rel['targets'] if t['target']==path);r=next(r for r in codes if r['path']==path);o.need(r['sha256']==archive['sha256']==t['old_sha256'],'switch-anchor-admission-base');o.raw(t['after']);codes[codes.index(r)]={'path':path,'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
    return prior,codes

def anchor_facts(parent,engine,operator_ref,prior,*,archived_operator=None):
    import switch_read_recovery as switch
    folder=o.location(parent['order']);order=o.validate(parent['order']);ci=engine['index'];a=engine['companies'][ci]['artifacts'];x=a['unit_artifacts'];job_ref=x['work_order'];job=o.doc(job_ref);s=o.doc(operator_ref) if archived_operator is None else archived_operator;unit=folder/'companies'/str(ci)/'units'/str(a['unit_index'])
    o.need(parent['status']==engine['status']=='hold' and parent.get('error')=='execution-child-stopped' and engine.get('error')==ANCHOR_ERROR and not parent.get('completion') and not engine.get('acceptance') and a['unit_phase']=='acquire' and not any(k in x for k in ('acquisition','job','source','profile','envelope')),'switch-anchor-exact-pre-export-hold')
    o.need(Path(job_ref['path']).parent.parent==unit/'operator' and job['work_order_path']==job_ref['path'] and Path(job['workflow_path'])==Path(operator_ref['path'])==Path(job_ref['path']).with_name('workflow.json') and job['action']=='acquire' and job['company']==order['companies'][ci]['company'] and str(job['groupid'])==order['companies'][ci]['groupid'] and job.get('source_purpose')=='complaint-draft-only-current-dispatch' and all(job.get(k) is False for k in ('submit_enabled','send_enabled','progress_updates_enabled')) and job['date_range']['start']==a['units'][a['unit_index']]['start'] and job['date_range']['end_exclusive']==a['units'][a['unit_index']]['end_exclusive'],'switch-anchor-original-job')
    error=s.get('last_error',{});o.need(error.get('code')==error.get('message')==ANCHOR_ERROR and not any(s.get(k) for k in ('waiting_for','switch_read_hold','switch_read_recovery')) and len(s['calls'])==4 and [c['phase'] for c in s['calls']]==['context','searchCompany','chooseCompany','confirmSwitch'] and not any(c['command']['op']=='activate' for c in s['calls']),'switch-anchor-original-four-confirmed')
    scope=switch.contract(job,s);o.need('window_anchor_ref' in scope,'switch-anchor-original-active-companion');started=datetime.fromisoformat(s['company_switch_wait_started']);failed=datetime.fromisoformat(error['at']);o.need(started.utcoffset() is not None and failed.utcoffset() is not None and started<=failed,'switch-anchor-original-wait')
    failed_indices=[*o.doc(parent[FIELD])['facts']['failed_engine_indices'],len(engine['calls'])-1];o.need(len(failed_indices)==len(set(failed_indices)) and all(c['state']=='returned' and c.get('applied') is True for i,c in enumerate(engine['calls']) if i not in failed_indices),'switch-anchor-no-other-unknown');call=engine['calls'][-1];o.need(call['state']=='failed' and call['error']==ANCHOR_ERROR and call['step']=='collect' and call['company_index']==ci and call['context']=={'order':order,'company':order['companies'][ci],'artifacts':a,'folder':str(folder/'companies'/str(ci)),'phase':'collect'},'switch-anchor-original-engine-failure')
    for c in parent['calls'][len(prior['failed_calls']):-1]:o.need(c['state']=='returned' and o.doc(c['result'])['returncode']==0,'switch-anchor-other-outer-error')
    c=parent['calls'][-1];launch=o.doc(c['launch']);exit=o.doc(c['result']);o.need(c['state']=='returned' and c['argv']==launch['argv']==exit['argv'] and exit['launch']==c['launch'] and exit['returncode']==2 and exit['stderr']=='' and json.loads(exit['stdout'])=={'ok':False,'error':ANCHOR_ERROR},'switch-anchor-natural-local-rc2')
    if parent.get('child'):
        good=next((o.doc(c['result']) for c in reversed(parent['calls'][:-1]) if o.doc(c['result'])['returncode']==0),None);o.need(good is not None and json.loads(good['stdout'])==parent['child'] and parent['child']['kind']=='complaint-execution-child-result-v1','switch-anchor-last-known-child')
    return {'operator':operator_ref,'job':job_ref,'scope':scope,'window_anchor_ref':scope['window_anchor_ref'],'original_wait_started_at':s['company_switch_wait_started'],'original_error':error,'failed_engine_indices':failed_indices,'failed_calls':parent['calls'],'all_company_artifacts':engine['companies']}

def plan_anchor(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,before_refs,*,installed=False):
    parent=o.doc(parent_ref);engine=o.doc(engine_ref);folder=o.location(parent['order']);o.need(Path(parent_ref['path'])==folder/'launcher.json' and Path(engine_ref['path'])==folder/'engine.json','switch-anchor-canonical-originals');prior,codes=anchor_tip(parent,release_ref,before_refs,installed=installed);facts=anchor_facts(parent,engine,operator_ref,prior);evidence=previous.previous.worker_evidence(parent,engine_ref,worker_ref);previous.previous.current_ledgers(parent,engine)
    return {'kind':KIND,'recovery_stage':ANCHOR_STAGE,'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'prior_recovery':parent[FIELD],'worker':worker_ref,'release':release_ref,'before_sources':before_refs,'facts':facts,'code_refs':codes,'worker_evidence':evidence,'ui_used':False}

def verify_anchor_stage(current,proof_ref,*,installed=True,extra_source_archives=()):
    import switch_read_recovery as switch
    p=o.doc(proof_ref);folder=o.location(current['order']);base=folder/'.switch-active-window-anchor-recovery'/p['original_parent']['sha256'];o.need(p['kind']==KIND and p['recovery_stage']==ANCHOR_STAGE and p['ui_used'] is False and current[FIELD]==proof_ref and Path(proof_ref['path'])==base/'proof.json' and datetime.fromisoformat(p['at']).utcoffset() is not None,'switch-anchor-canonical-proof')
    for n in ('parent','engine','operator'):o.need(Path(p[n+'_archive']['path'])==base/('original-'+n+'.json') and p[n+'_archive']['sha256']==p['original_'+n]['sha256'],'switch-anchor-original-archive')
    o.need(len(p['before_sources'])==3 and all(Path(r['path'])==base/Path(r['path']).name for r in p['before_sources']),'switch-anchor-source-archives');parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);o.need(parent[FIELD]==p['prior_recovery'],'switch-anchor-original-prior');prior,codes=anchor_tip(parent,p['release'],p['before_sources'],installed=installed,extra_source_archives=extra_source_archives);facts=anchor_facts(parent,engine,p['original_operator'],prior,archived_operator=o.doc(p['operator_archive']));after=o.doc(p['reconciled_operator']);typed=switch.verify_recovered(after,p['switch_read_proof']);original=switch.document(typed['original_journal']);expected=recovered(parent,engine,proof_ref)[0]
    o.need(p['facts']==facts and p['code_refs']==codes and p['worker_evidence']==previous.previous.worker_evidence(parent,p['original_engine'],p['worker']) and original==o.doc(p['operator_archive']) and typed['facts']['window_anchor_ref']==facts['window_anchor_ref'] and after['calls']==original['calls'] and Path(p['reconciled_operator']['path'])==base/'reconciled-operator.json' and current['calls'][:len(parent['calls'])]==parent['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(parent['origin_ref']).items()) and all(current.get(k)==parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,previous.previous.entry.FIELD,previous.previous.FIELD)),'switch-anchor-preserved-history')
    intent=o.doc(p['readonly_intent']);result=o.doc(p['readonly_result']);o.need(Path(p['readonly_intent']['path'])==base/'readonly-intent.json' and Path(p['readonly_result']['path'])==base/'readonly-result.json' and {k:v for k,v in intent.items() if k!='at'}=={'kind':'switch-anchor-bounded-read-intent-v1','original_operator':p['original_operator'],'job':facts['job'],'release':p['release'],'max_samples':3,'ui_used':False} and result['state']=='reconciled' and result['proof']==p['switch_read_proof'] and result['journal']['sha256']==p['reconciled_operator']['sha256'] and result['journal']['path']==p['original_operator']['path'],'switch-anchor-bounded-read-receipts');o.need(set(intent)=={'kind','original_operator','job','release','max_samples','ui_used','at'} and datetime.fromisoformat(intent['at']).utcoffset() is not None and datetime.fromisoformat(intent['at'])<=datetime.fromisoformat(switch.document(switch.document(p['switch_read_proof'])['sample'])['at'])<=datetime.fromisoformat(p['at']),'switch-anchor-real-read-timing')
    if o.doc(o.ref(folder/'launcher.json')).get(FIELD)==proof_ref:
        actual=o.doc(o.ref(p['original_operator']['path']));o.need(actual.get('switch_read_recovery')==p['switch_read_proof'] and actual['calls'][:len(original['calls'])]==original['calls'] and all(actual.get(k)==original.get(k) for k in ('work_order_id','fingerprint','company','groupid','date_range','tab_id','initial_groupid','entry_groupid','entry_identity','identity_contract')),'switch-anchor-operator-continuation')
    return {**prior,'proof':proof_ref,'code_refs':codes,'failed_calls':parent['calls'],'evidence':[*prior['evidence'],proof_ref,p['parent_archive'],p['engine_archive'],p['operator_archive'],p['reconciled_operator'],p['switch_read_proof'],p['readonly_intent'],p['readonly_result'],*p['before_sources'],p['release'],facts['window_anchor_ref'],*p['worker_evidence']]}

def recover_anchor(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,before_refs,*,invoke=None):
    import switch_read_recovery as switch
    folder=Path(parent_ref['path']).parent;base=folder/'.switch-active-window-anchor-recovery'/parent_ref['sha256'];operator_path=Path(operator_ref['path'])
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b,operator_path.with_name('.bridge-execution.lock').open('a') as c:
        for lock in (a,b,c):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        plan_ref=base/'plan.json'
        if plan_ref.exists():
            p=o.doc(o.ref(plan_ref));o.need(all(p[k]==v for k,v in {'original_parent':parent_ref,'original_engine':engine_ref,'original_operator':operator_ref,'worker':worker_ref,'release':release_ref}.items()) and [(Path(r['path']).name,r['sha256']) for r in before_refs]==[(Path(r['path']).name,r['sha256']) for r in p['before_sources']],'switch-anchor-same-recovery')
        else:
            p=plan_anchor(parent_ref,engine_ref,operator_ref,worker_ref,release_ref,before_refs,installed=True);base.mkdir(parents=True,exist_ok=True)
            for n,r in (('parent',parent_ref),('engine',engine_ref),('operator',operator_ref)):p[n+'_archive']=h.immutable_bytes(base/('original-'+n+'.json'),o.raw(r))
            p['before_sources']=[h.immutable_bytes(base/Path(r['path']).name,o.raw(r)) for r in before_refs];o.immutable(plan_ref,p)
        parent=o.doc(p['parent_archive']);engine=o.doc(p['engine_archive']);lease=o.doc(o.ref(Path(parent['order']['path']).parent.parent/'state.json'));import director
        o.need(lease['dispatch_id']==o.doc(parent['order'])['dispatch_id'] and lease['day']==o.doc(parent['order'])['day'] and lease['phase'] in ('running','attention') and director.current(lease)['role']==o.ROLE,'switch-anchor-current-lease');previous.previous.current_ledgers(parent,engine)
        if not (base/'proof.json').exists():
            intent={'kind':'switch-anchor-bounded-read-intent-v1','original_operator':operator_ref,'job':p['facts']['job'],'release':release_ref,'max_samples':3,'ui_used':False};ip=base/'readonly-intent.json';rp=base/'readonly-result.json'
            if not ip.exists():
                o.need(o.ref(operator_path)==operator_ref and o.ref(folder/'launcher.json')==parent_ref and o.ref(folder/'engine.json')==engine_ref,'switch-anchor-originals-changed');o.immutable(ip,{**intent,'at':stamp()})
                if invoke is None:
                    import bridge
                    invoke=lambda command:bridge.request(command,timeout=50)
                def readonly(command):
                    o.need(command=={'op':'tabs'} or command in ({'op':'ping','tabId':o.doc(p['operator_archive'])['tab_id']},{'op':'tree','tabId':o.doc(p['operator_archive'])['tab_id']}),'switch-anchor-readonly-capability');return invoke(command)
                result=switch.reconcile(p['facts']['job']['path'],operator_ref['sha256'],readonly,max_samples=3);o.immutable(rp,result)
            elif not rp.exists():
                actual=o.doc(o.ref(operator_path));proof=actual.get('switch_read_recovery');o.need(proof is not None,'switch-anchor-read-outcome-unknown-no-repeat');checked=switch.verify_recovered(actual,proof);o.need(checked['original_journal']['sha256']==operator_ref['sha256'] and switch.document(checked['original_journal'])==o.doc(p['operator_archive']),'switch-anchor-crash-original-binding');o.immutable(rp,{'state':'reconciled','journal':o.ref(operator_path),'proof':proof,'phase':'accountAfterSwitch','ui_used':False})
            result=o.doc(o.ref(rp));o.need(result.get('state')=='reconciled','switch-anchor-fresh-read-held:'+str(result.get('error')));p['readonly_intent']=o.ref(ip);p['readonly_result']=o.ref(rp);p['switch_read_proof']=result['proof'];p['reconciled_operator']=h.immutable_bytes(base/'reconciled-operator.json',o.raw(result['journal']));p['at']=stamp();proof=o.immutable(base/'proof.json',p)
        else:proof=o.ref(base/'proof.json');p=o.doc(proof)
        newp,newe=recovered(parent,engine,proof);refs=[h.exact_metadata_state(path,old,new) for path,old,new in ((folder/'launcher.json',p['parent_archive'],newp),(folder/'engine.json',p['engine_archive'],newe))];verify_anchor_stage(newp,proof)
        import complaint_execution_launcher as launcher
        for r in refs:o.raw(r)
        for path,value in ((folder/'engine.json',newe),(folder/'launcher.json',newp)):
            if o.doc(o.ref(path))!=value:launcher.save(path,value)
        return {'kind':KIND,'recovery_stage':ANCHOR_STAGE,'launcher':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'operator':o.ref(operator_path),'proof':proof,'switch_read_proof':p['switch_read_proof'],'ui_used':False}

# Fixed, proved pre-native failure only. Original journal/operation/keys survive.
PANEL_STAGE='known-pre-native-page-window-focus-v1'
PANEL_KIND='verified-pre-native-page-window-focus-recovery-v1'
PANEL_REFS={
 'failure':('work/2026-10-24/full-three-flow-run-20261024/complaint2-native-download-panel-preflight-failure.json','a3fb5019fa95e3cac808cf6d0c42b0a1b7d2785e501c3f768aa50d35dffe1f27'),
 'boundary':('work/2026-10-24/full-three-flow-run-20261024/complaint2-pre-capture-boundary-inventory.json','028aa5dd250160ecd1e0824e3181eb80c57ad6730794269e7119096d508b7903'),
 'diagnostic':('work/2026-10-24/full-three-flow-run-20261024/complaint3-panel-readonly-diagnostic-summary.json','b5682d0d16b6c551c25f6615f793772251a1bce5eea074692af0ec807ead6532'),
 'correction':('work/2026-10-25/round001-issue07/region-state-inventory-correction.json','1195ab9be00262c9be2fb984c33dbe78ac08321845e5f287dd457f98abeef4dd')}
def panel_source_paths():
    return {n:str(ROOT/p) for n,p in {'review_capture_focus.py':'skills/negative-review-complaints/scripts/review_capture_focus.py','initial_ledger_recovery.py':'skills/negative-review-complaints/scripts/initial_ledger_recovery.py','capture_review_region.py':'skills/negative-review-complaints/scripts/capture_review_region.py','review_region_capture.py':'skills/chrome-dom-export/scripts/review_region_capture.py'}.items()}
def panel_material(reference,archives):
    matches=[x for x in archives if x['original']==reference];o.need(len(matches)<=1,'panel-recovery-duplicate-material')
    if matches:
        archive=matches[0]['archive'];o.need(archive['sha256']==reference['sha256'],'panel-recovery-archive-bytes');return o.raw(archive)
    return o.raw(reference)
def panel_facts(archives=(),*,initial=False):
    refs={k:{'path':str(ROOT/p),'sha256':sha} for k,(p,sha) in PANEL_REFS.items()};docs={k:o.doc(r) for k,r in refs.items()};f=docs['failure'];b=docs['boundary'];d=docs['diagnostic'];cor=docs['correction']
    parent=json.loads(panel_material(f['parent'],archives));engine=json.loads(panel_material(f['engine'],archives));state=json.loads(panel_material(cor['region_state'],archives));folder=Path(f['parent']['path']).parent
    o.need(f['task']=='task-e851f61b8d7642391ec23524' and f['attempt']==2 and f['capture_attempted'] is False and not f['native_outputs'] and b['failure_summary']==refs['failure'] and cor['original_frame_inventory']==refs['boundary'],'panel-recovery-fixed-failure')
    o.need(parent['status']==engine['status']=='hold' and parent.get('error')=='execution-child-stopped' and engine.get('error')==ERROR and engine['phase']=='collect' and engine['index']==0 and len(engine['calls'])==44 and len(parent['calls'])==1,'panel-recovery-fixed-hold')
    origin=o.doc(parent['origin_ref']);o.need(all(parent.get(k)==v for k,v in origin.items()) and not any(parent.get(k) for k in (h.FIELD,h.PLAN_FIELD,'completion')),'panel-recovery-original-origin')
    order=o.doc(parent['order']);a=engine['companies'][0]['artifacts'];last=engine['calls'][-1]
    o.need(last['state']=='failed' and last['error']==ERROR and last['step']=='collect' and last['company_index']==0 and last['context']=={'order':order,'company':order['companies'][0],'artifacts':a,'folder':str(folder/'companies/0'),'phase':'collect'} and a['unit_phase']=='frames' and all(c['state']=='returned' and c.get('applied') is True for c in engine['calls'][:-1]),'panel-recovery-only-failed43')
    call=parent['calls'][0];child=o.doc(call['result']);launch=o.doc(call['launch']);o.need(call['state']=='returned' and child['returncode']==2 and child['argv']==launch['argv']==call['argv'] and child['launch']==call['launch'] and child['stderr']=='' and json.loads(child['stdout'])=={'ok':False,'error':ERROR},'panel-recovery-original-child')
    o.need(set(state)=={'journal_contract','state','operation','created_at','before-reply.json','before-geometry.json'} and state['journal_contract']=='durable-normal-region-capture-v2' and state['state']=='unknown','panel-recovery-exact-pre-native-state')
    manifest=o.doc(f['frame_manifest']);op=state['operation'];out=Path(op['outdir']);o.need(op['manifest']==manifest and op['pid']==parent['pid'] and manifest['source']==f['normal_refs']['normal-source.json'] and b['geometry_record_error']=={'type':'ValueError','message':ERROR},'panel-recovery-original-operation')
    geometry=o.doc(state['before-geometry.json']);o.need(geometry['error']==b['geometry_record_error'] and geometry['operation']==op and state['before-geometry.json']==b['before_geometry_record'],'panel-recovery-error-before-native')
    for r in [*f['normal_refs'].values(),f['operator'],f['navigation'],f['frame_manifest'],*b['frame_files'],*f['natural_refs'].values()]:panel_material(r,archives)
    prior_focus=json.loads(panel_material(f['capture_focus'],archives));o.need(prior_focus['events']==[] and prior_focus['binding']['manifest']==f['frame_manifest'],'panel-recovery-original-focus-no-input')
    wf=o.doc(f['operator']);o.need(wf['state']=='complete' and wf['phase']=='done' and all(c['state']=='confirmed' for c in wf['calls']),'panel-recovery-acquire-confirmed')
    o.need(d['diagnostic_rc']==0 and d['UI_input_used'] is False and d['parent_resumed'] is False and d['parent_engine_unchanged']==[f['parent'],f['engine']],'panel-recovery-diagnostic-no-input');observation=o.doc(d['natural_refs']['capture-panel-readonly-observation.json']);o.need(observation['UI_input_used'] is False and observation['capture_used'] is False and observation['CG_before']==observation['CG_after']==d['CG_panel'],'panel-recovery-actual-panel-observation')
    if initial:
        o.need(o.ref(folder/'launcher.json')==f['parent'] and o.ref(folder/'engine.json')==f['engine'] and o.ref(cor['region_state']['path'])==cor['region_state'],'panel-recovery-original-CAS')
        expected={Path(r['path']) for r in b['frame_files']};frame=Path(f['frame_manifest']['path']).parent;actual={x for x in frame.rglob('*') if x.is_file()};o.need(actual==expected,'panel-recovery-output-inventory-changed')
        o.need(not any((out/n).exists() for n in ('raw-window.png','raw-window.json','review-region.png','registration.json','preview-registration.json')) and not (out/'capture-v2/derivation-intent.json').exists(),'panel-recovery-native-or-derivation-present')
    return {'refs':refs,'parent_ref':f['parent'],'engine_ref':f['engine'],'parent':parent,'engine':engine,'region_state':state,'region_state_ref':cor['region_state'],'focus_ref':f['capture_focus'],'operation':op,'folder':str(folder),'failure_ref':refs['failure'],'failed_engine_index':43,'fixed_evidence':[*refs.values(),f['parent'],f['engine'],f['capture_focus'],cor['region_state'],*f['normal_refs'].values(),*b['frame_files'],*f['natural_refs'].values(),d['natural_refs']['capture-panel-readonly-observation.json'],parent['origin_ref'],parent['order'],call['launch'],call['result']]}
def panel_tip(parent,release_ref,archives,*,installed):
    release=o.doc(release_ref);paths=panel_source_paths();extras={str(ROOT/'packages/workshop-director/workshop_director/adapters.py'),str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py')};targets=release['targets'];o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published') is True and release.get('test_projection_only') is False and release.get('reviewed_by')=='workshop-director' and len(targets)==6 and {t['target'] for t in targets}==set(paths.values())|extras,'panel-recovery-exact-reviewed-six-source-release')
    codes=copy.deepcopy(parent['code_refs']);o.need(len(codes)==len({r['path'] for r in codes}),'panel-recovery-original-code-graph')
    for name,path in paths.items():
        old=next(r for r in codes if r['path']==path);t=next(t for t in targets if t['target']==path);o.need(t['old_sha256']==old['sha256'],'panel-recovery-reviewed-before-source');panel_material(old,archives);o.raw(t['after']);new={'path':path,'sha256':t['after']['sha256']};codes[codes.index(old)]=new
    for t in targets:
        o.raw(t['after'])
        if installed:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    for r in codes:
        if r['path'] not in paths.values():quality_original_code(r)
    return codes

def panel_before_source(release_ref,reference):
    # Four exact old CODE materials come from this reviewed release's data
    # archives after publication, never the replaced canonical source path.
    release=o.doc(release_ref);paths=set(panel_source_paths().values());o.need(reference['path'] in paths,'panel-recovery-before-source-not-eligible')
    targets=release['targets'];expected=paths|{str(ROOT/'packages/workshop-director/workshop_director/adapters.py'),str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py')}
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published') is True and release.get('test_projection_only') is False and release.get('reviewed_by')=='workshop-director' and len(targets)==6 and {t['target'] for t in targets}==expected,'panel-recovery-before-source-release')
    policy=o.doc(release['source_repair_dependency_delta']);p_targets=policy['targets'];o.need(policy['kind']=='finite-reviewed-page-focus-dependency-delta-v1' and policy['previous_release']==release['previous_release'] and policy['authorization_release']==release['source_repair_authorization_release'] and len(p_targets)==5 and {t['target'] for t in p_targets}==expected-{str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py')},'panel-recovery-before-source-policy')
    current=next(t for t in targets if t['target']==reference['path']);entry=next(t for t in p_targets if t['target']==reference['path']);archive=entry['archive']
    o.need(current['old_sha256']==reference['sha256'] and entry['before']==reference and entry['after']==current['after'] and archive['sha256']==reference['sha256'] and archive['path']!=reference['path'],'panel-recovery-before-source-exact-pair');o.raw(current['after']);return o.raw(archive)

def recovered_panel_pair(parent,engine,proof_ref):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in (parent,engine):
        error=value.pop('error');value.update(status='running',**{h.FIELD:proof_ref,h.PLAN_FIELD:proof_ref});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof_ref})
    return parent,engine

def verify_panel_recovered(current,proof_ref,*,installed=True):
    p=o.doc(proof_ref);o.need(p['kind']==PANEL_KIND and p['recovery_stage']==PANEL_STAGE and p['ui_used'] is False and current[h.FIELD]==current[h.PLAN_FIELD]==proof_ref,'panel-recovery-proof-binding')
    facts=panel_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.page-window-focus-recovery'/p['original_parent']['sha256']
    o.need(Path(proof_ref['path'])==base/'proof.json' and p['original_parent']==facts['parent_ref'] and p['original_engine']==facts['engine_ref'] and all(Path(x['archive']['path']).parent==base/'archives' for x in p['archives']),'panel-recovery-canonical-archives');o.need(p['original_parent']['sha256']==__import__('hashlib').sha256(o.raw(p['parent_archive'])).hexdigest() and p['original_engine']['sha256']==__import__('hashlib').sha256(o.raw(p['engine_archive'])).hexdigest(),'panel-recovery-original-archive-hash')
    codes=panel_tip(facts['parent'],p['release'],p['archives'],installed=installed);expected,_=recovered_panel_pair(facts['parent'],facts['engine'],proof_ref)
    o.need(p['code_refs']==codes and current['calls'][:len(facts['parent']['calls'])]==facts['parent']['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(facts['parent']['origin_ref']).items()),'panel-recovery-preserved-parent')
    return {'kind':PANEL_KIND,'proof':proof_ref,'code_refs':codes,'failed_calls':facts['parent']['calls'],'initial_failed_call':facts['parent']['calls'][0],'failed_engine_call':facts['engine']['calls'][43],'facts':facts,'evidence':[proof_ref,p['release'],*[x['archive'] for x in p['archives']],*[next((x['archive'] for x in p['archives'] if x['original']==r),r) for r in facts['fixed_evidence']]]}

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'));proof=engine[h.PLAN_FIELD];o.need(engine[h.FIELD]==proof==current[h.FIELD]==current[h.PLAN_FIELD],'panel-recovery-engine-parent');admitted=verify_panel_recovered(current,proof);original=admitted['facts']['engine'];o.need(engine['calls'][:44]==original['calls'] and engine['resolved_errors']==original.get('resolved_errors',[])+[{'error':ERROR,'recovery':proof}],'panel-recovery-preserved-engine');return [c for i,c in enumerate(engine['calls']) if i!=43]

def verify_pre_native_authorization(proof_ref,operation):
    p=o.doc(proof_ref);facts=panel_facts(p['archives']);current=o.doc(o.ref(Path(facts['folder'])/'launcher.json'));admitted=verify_panel_recovered(current,proof_ref);o.need(operation is None or operation==facts['operation'],'panel-recovery-operation-changed');return admitted

def panel_capture_state(proof_ref,operation,*,require_fresh=False):
    admitted=verify_pre_native_authorization(proof_ref,operation);facts=admitted['facts'];current=o.doc(o.ref(facts['region_state_ref']['path']));old=facts['region_state']
    o.need(current.get('pre_native_authorization')==proof_ref and all(current.get(k)==v for k,v in old.items() if k!='state') and set(current)<=set(old)|{'pre_native_authorization','registration'},'panel-recovery-original-region-state')
    if require_fresh:
        out=Path(operation['outdir']);o.need(current['state']=='unknown' and not (out/'capture-v2/pre-native-continuation-v1/state.json').exists() and not any((out/n).exists() for n in ('raw-window.png','raw-window.json','review-region.png','registration.json','preview-registration.json')),'panel-recovery-native-stage-already-started')
    return admitted

def recover_panel(release_ref):
    original=o.doc({'path':str(ROOT/PANEL_REFS['failure'][0]),'sha256':PANEL_REFS['failure'][1]})['parent'];folder=Path(original['path']).parent;base=folder/'.page-window-focus-recovery'/original['sha256'];base.mkdir(parents=True,exist_ok=True)
    with (folder/'launcher.lock').open('a') as a,(folder/'engine.lock').open('a') as b:
        fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
        proof_path=base/'proof.json'
        if proof_path.exists():
            proof=o.ref(proof_path);p=o.doc(proof);o.need(p['release']==release_ref,'panel-recovery-same-release')
        else:
            facts=panel_facts(initial=True);refs=[o.ref(folder/'launcher.json'),o.ref(folder/'engine.json'),facts['region_state_ref'],facts['focus_ref']]+[r for r in facts['parent']['code_refs'] if r['path'] in panel_source_paths().values()];archives=[]
            for i,r in enumerate(refs):
                raw=panel_before_source(release_ref,r) if r['path'] in panel_source_paths().values() else o.raw(r)
                archives.append({'original':r,'archive':h.immutable_bytes(base/'archives'/(str(i)+'-'+Path(r['path']).name),raw)})
            codes=panel_tip(facts['parent'],release_ref,archives,installed=True);p={'kind':PANEL_KIND,'recovery_stage':PANEL_STAGE,'original_parent':refs[0],'original_engine':refs[1],'parent_archive':archives[0]['archive'],'engine_archive':archives[1]['archive'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(proof_path,p)
        facts=panel_facts(p['archives']);parent,engine=recovered_panel_pair(facts['parent'],facts['engine'],proof);state=copy.deepcopy(facts['region_state']);state['pre_native_authorization']=proof
        for path,old,new in ((Path(facts['region_state_ref']['path']),facts['region_state'],state),(folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            existing=o.doc(o.ref(path));o.need(existing in (old,new),'panel-recovery-partial-CAS-conflict')
            if existing==old:previous.overlay.rc.atomic(path,new)
        verify_panel_recovered(parent,proof);return {'kind':PANEL_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'region_state':o.ref(facts['region_state_ref']['path']),'ui_used':False}

# Single reviewed current-source append. Original anchor and all input history stay.
WINDOW_SOURCE_FIELD='window_focus_source_append'
WINDOW_SOURCE_KIND='verified-page-window-source-append-v1'
WINDOW_FAILURE=('work/2026-10-24/full-three-flow-run-20261024/complaint4-page-window-focus-native-admission-failure.json','fbdf5fb1c2b37bd1216c471f265b9f8172265d58dd0aff55097b2cece4c231bc')
WINDOW_DIAGNOSTIC_RELEASE=('work/performance-audit/complaint-exact-window-raise-candidate/readonly-window-diagnostic/supervisor-release.json','5508bb7c2b93e45297d7c192571dc68a552f506166d8853d7ef8e3fe09a80974')
_panel_verify_before_window_append=verify_panel_recovered
_panel_engine_calls_before_window_append=panel_engine_calls

def window_ref(pair):return {'path':str(ROOT/pair[0]),'sha256':pair[1]}
def window_material(reference,archives):
    hits=[x for x in archives if x['original']==reference];o.need(len(hits)<=1,'window-source-duplicate-archive')
    if hits:o.need(hits[0]['archive']['sha256']==reference['sha256'],'window-source-archive-hash');return o.raw(hits[0]['archive'])
    return o.raw(reference)
def window_source_facts(archives=(),*,initial=False):
    failure_ref=window_ref(WINDOW_FAILURE);f=o.doc(failure_ref)
    parent=json.loads(window_material(f['parent'],archives));engine=json.loads(window_material(f['engine'],archives));focus=json.loads(window_material(f['focus_journal'],archives));region=json.loads(window_material(f['region_state'],archives));folder=Path(f['parent']['path']).parent;anchor=parent[h.FIELD]
    o.need(f['task_id']=='task-e851f61b8d7642391ec23524' and f['attempt']==4 and f['leaf']=='capture-focus-native-stage-not-qualified' and parent[h.PLAN_FIELD]==engine[h.FIELD]==engine[h.PLAN_FIELD]==anchor,'window-source-fixed-original-anchor')
    base=_panel_verify_before_window_append(parent,anchor,installed=False);old=base['facts'];o.need(parent['status']==engine['status']=='hold' and parent['error']=='execution-child-stopped' and engine['error']==f['leaf'] and len(parent['calls'])==2 and len(engine['calls'])==45,'window-source-fixed-hold')
    o.need(parent['calls'][:1]==old['parent']['calls'] and engine['calls'][:44]==old['engine']['calls'],'window-source-unchanged-prefix')
    last=engine['calls'][44];o.need(last['state']=='failed' and last['step']=='collect' and last['company_index']==0 and last['error']==f['leaf'] and last['context']==old['engine']['calls'][43]['context'],'window-source-exact-failed44')
    call=parent['calls'][1];child=o.doc(f['child_exit']);launch=o.doc(call['launch']);o.need(call['state']=='returned' and call['result']==f['child_exit'] and child['returncode']==2 and child['argv']==launch['argv']==call['argv'] and child['launch']==call['launch'] and child['stderr']=='' and json.loads(child['stdout'])=={'ok':False,'error':f['leaf']},'window-source-exact-natural-child1')
    o.need(len(focus['events'])==1 and not f['native_focus_present'] and f['png_count']==0 and f['original_pre_native_authorization_only'] is True,'window-source-no-native-boundary')
    event=focus['events'][0];o.need(event['state']=='unknown' and event['phase']=='capture-focus' and event['number']==1 and len(event['calls'])==1 and not any(k in event for k in ('native_focus','window_focus')),'window-source-browser-only-event')
    c=event['calls'][0];o.need(c['key']=='capture-focus:1' and c['state']=='confirmed' and c['command']=={'op':'activate','tabId':event['binding']['scope']['tabId']} and event['reply']==f['extension_reply'] and c['result']['windowId']==event['binding']['scope']['windowId'] and c['result']['active'] is True and c['result']['windowFocused'] is True,'window-source-confirmed-activation-no-replay')
    after=o.doc(f['after_observation']);wins=[w for w in after['tabs']if w['windowId']==event['binding']['scope']['windowId']];tabs=[t for w in wins for t in w['tabs']if t['tabId']==event['binding']['scope']['tabId']];o.need(len(wins)==len(tabs)==1 and wins[0]['focused'] is True and tabs[0]==f['after']['target'],'window-source-exact-after-tab');o.need(after['CG_first_ordinary']['kCGWindowOwnerPID']==event['binding']['pid'] and after['CG_first_ordinary']['kCGWindowName']=='近期的下载记录' and after['expected_AXFrontmost']['value'] is True,'window-source-real-readonly-effect')
    o.need(region=={**old['region_state'],'pre_native_authorization':anchor} and region['operation']==old['operation'],'window-source-region-anchor-unchanged')
    fixed=[failure_ref,f['parent'],f['engine'],f['focus_journal'],f['region_state'],f['after_observation'],f['extension_reply'],f['parent_run_exit'],f['child_exit'],f['started'],f['request'],f['source'],f['manifest'],call['launch'],*f['capture_inventory']]
    for r in fixed:window_material(r,archives)
    if initial:
        for r in (f['parent'],f['engine'],f['focus_journal'],f['region_state']):o.need(o.ref(r['path'])==r,'window-source-original-CAS')
        out=Path(region['operation']['outdir']);o.need(not(out/'capture-v2/pre-native-continuation-v1/state.json').exists() and not any((out/n).exists() for n in ('raw-window.png','raw-window.json','review-region.png','registration.json','preview-registration.json')),'window-source-native-stage-exists')
    return {'failure_ref':failure_ref,'failure':f,'parent':parent,'engine':engine,'focus':focus,'region':region,'folder':str(folder),'anchor':anchor,'base':base,'fixed':fixed}
def window_source_tip(base,release_ref,*,installed):
    release=o.doc(release_ref);focus=str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py');adapter=str(ROOT/'packages/workshop-director/workshop_director/adapters.py');helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');targets=release['targets'];paths={focus,adapter,helper};diag_ref=window_ref(WINDOW_DIAGNOSTIC_RELEASE);diag=o.doc(diag_ref)
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published') is True and release.get('test_projection_only') is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==diag_ref and len(targets)==3 and {t['target']for t in targets}==paths,'window-source-exact-reviewed-release')
    o.need(diag['purpose']=='exact-original-complaint-business-window-readonly-diagnostic-only' and diag['published'] is True and diag['previous_release']==o.doc(base['proof'])['release'],'window-source-diagnostic-continuous-release')
    policy=o.doc(release['source_repair_dependency_delta']);o.need(policy['kind']=='finite-reviewed-exact-window-raise-dependency-delta-v1' and policy['previous_release']==diag_ref and policy['authorization_release']==release['source_repair_authorization_release'] and len(policy['targets'])==2 and {t['target']for t in policy['targets']}=={focus,adapter},'window-source-fixed-policy')
    codes=copy.deepcopy(base['code_refs']);old=next(r for r in codes if r['path']==focus)
    for t in targets:
        o.raw(t['after'])
        if installed:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
        if t['target']!=helper:
            pt=next(x for x in policy['targets']if x['target']==t['target']);o.need(pt['before']=={'path':t['target'],'sha256':t['old_sha256']} and pt['after']==t['after'] and pt['archive']['sha256']==t['old_sha256'],'window-source-exact-CAS-policy');o.raw(pt['archive'])
    t=next(t for t in targets if t['target']==focus);o.need(t['old_sha256']==old['sha256'],'window-source-original-focus-pin');codes[codes.index(old)]={'path':focus,'sha256':t['after']['sha256']}
    at=next(t for t in targets if t['target']==adapter);dt=next(t for t in diag['targets']if t['target']==adapter);original_release=o.doc(o.doc(base['proof'])['release']);normal=next(t for t in original_release['targets']if t['target']==adapter)
    o.need(at['old_sha256']==dt['after']['sha256'] and at['after']['sha256']==normal['after']['sha256'],'window-source-exact-diagnostic-hook-removal')
    for r in codes:
        if r['path']!=focus:quality_original_code(r)
    return codes

def window_recovered_pair(parent,engine,append_ref):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in (parent,engine):
        error=value.pop('error');value.update(status='running',**{WINDOW_SOURCE_FIELD:append_ref});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':append_ref})
    return parent,engine

def verify_window_source_append(current,oldproof,*,installed=True):
    append_ref=current[WINDOW_SOURCE_FIELD];p=o.doc(append_ref);facts=window_source_facts(p['archives']);folder=Path(facts['folder']);basepath=folder/'.page-window-focus-recovery'/o.doc(oldproof)['original_parent']['sha256']/'window-source-appends'
    o.need(Path(append_ref['path'])==basepath/'0001.json' and p['kind']==WINDOW_SOURCE_KIND and p['ui_used'] is False and p['oldproof']==oldproof==facts['anchor'] and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'],'window-source-canonical-same-anchor')
    o.need(all(Path(x['archive']['path']).parent==basepath/'archives' for x in p['archives']),'window-source-canonical-archives')
    expected,_=window_recovered_pair(facts['parent'],facts['engine'],append_ref);o.need(current[h.FIELD]==current[h.PLAN_FIELD]==oldproof and current['calls'][:2]==facts['parent']['calls'] and current['resolved_errors']==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(facts['parent']['origin_ref']).items()),'window-source-preserved-current-parent')
    view=copy.deepcopy(current);view['resolved_errors']=facts['parent']['resolved_errors'];base=_panel_verify_before_window_append(view,oldproof,installed=False);codes=window_source_tip(base,p['release'],installed=installed);o.need(p['code_refs']==codes,'window-source-effective-graph')
    return {**base,'code_refs':codes,'failed_calls':facts['parent']['calls'],'window_source_append':append_ref,'window_source_facts':facts,'evidence':[*base['evidence'],append_ref,p['release'],*[x['archive']for x in p['archives']],*[next((x['archive']for x in p['archives']if x['original']==r),r)for r in facts['fixed']]]}

def verify_panel_recovered(current,proof_ref,*,installed=True):
    if current.get(WINDOW_SOURCE_FIELD):return verify_window_source_append(current,proof_ref,installed=installed)
    return _panel_verify_before_window_append(current,proof_ref,installed=installed)

def panel_engine_calls(engine):
    if not engine.get(WINDOW_SOURCE_FIELD):return _panel_engine_calls_before_window_append(engine)
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'));o.need(engine[h.FIELD]==engine[h.PLAN_FIELD]==current[h.FIELD]==current[h.PLAN_FIELD],'window-source-engine-parent-anchor');admitted=verify_window_source_append(current,engine[h.FIELD]);facts=admitted['window_source_facts'];expected=window_recovered_pair(facts['parent'],facts['engine'],engine[WINDOW_SOURCE_FIELD])[1]
    o.need(current[WINDOW_SOURCE_FIELD]==engine[WINDOW_SOURCE_FIELD] and engine['calls'][:45]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'],'window-source-preserved-engine')
    return [c for i,c in enumerate(engine['calls'])if i not in (43,44)]

def recover_window_source(release_ref):
    failure=o.doc(window_ref(WINDOW_FAILURE));folder=Path(failure['parent']['path']).parent;anchor=o.doc(failure['region_state'])['pre_native_authorization'];base=folder/'.page-window-focus-recovery'/o.doc(anchor)['original_parent']['sha256']/'window-source-appends';base.mkdir(parents=True,exist_ok=True)
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB);path=base/'0001.json'
        if path.exists():
            append_ref=o.ref(path);p=o.doc(append_ref);o.need(p['release']==release_ref,'window-source-same-release')
        else:
            facts=window_source_facts(initial=True);archives=[]
            for n,r in enumerate([failure['parent'],failure['engine'],failure['focus_journal'],failure['region_state']]):archives.append({'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))})
            codes=window_source_tip(facts['base'],release_ref,installed=True);p={'kind':WINDOW_SOURCE_KIND,'oldproof':anchor,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'at':stamp(),'ui_used':False};append_ref=o.immutable(path,p)
        facts=window_source_facts(p['archives']);parent,engine=window_recovered_pair(facts['parent'],facts['engine'],append_ref)
        for dest,old,new in ((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in (old,new),'window-source-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_window_source_append(parent,anchor);return {'kind':WINDOW_SOURCE_KIND,'append':append_ref,'oldproof':anchor,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'ui_used':False}



def quality_original_code(reference):
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/packages/workshop-director/workshop_director/adapters.py', 'sha256': 'c62529f28fd7e406f6a3aca9f7c1066e25331ac46f74d387cf4589c2ddd279a2'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-completed-report-membership-candidate/dependency-source-archives/c62529f28fd7e406f6a3aca9f7c1066e25331ac46f74d387cf4589c2ddd279a2.py', 'sha256': 'c62529f28fd7e406f6a3aca9f7c1066e25331ac46f74d387cf4589c2ddd279a2'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/workshop-director/scripts/complaint_execution_orchestration.py', 'sha256': '5c9e170e62d698a056cf3e5b58d927fc811183c1e68bb520c808c09edbc7bacd'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-completed-report-membership-candidate/dependency-source-archives/5c9e170e62d698a056cf3e5b58d927fc811183c1e68bb520c808c09edbc7bacd.py', 'sha256': '5c9e170e62d698a056cf3e5b58d927fc811183c1e68bb520c808c09edbc7bacd'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/scripts/bridge-service.py', 'sha256': 'b880010a1b77978c9325da11ee4fbf46d5a98384e5e45fdb088a97b30e497882'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/bridge-unicode-json-candidate/dependency-source-archives/b880010a1b77978c9325da11ee4fbf46d5a98384e5e45fdb088a97b30e497882.py', 'sha256': 'b880010a1b77978c9325da11ee4fbf46d5a98384e5e45fdb088a97b30e497882'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/role_cli.py', 'sha256': '67d26a64c44b030a0ea49de75c326112b70b850f51fb3adc73c25bea0e5b3f07'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/bridge-unicode-json-candidate/dependency-source-archives/67d26a64c44b030a0ea49de75c326112b70b850f51fb3adc73c25bea0e5b3f07.py', 'sha256': '67d26a64c44b030a0ea49de75c326112b70b850f51fb3adc73c25bea0e5b3f07'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/chrome-dom-export/scripts/bridge.py', 'sha256': 'b8f084aae25212a478da8ebd4de292545509ea87d441d486c35cbe5408630611'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/bridge-unicode-json-candidate/dependency-source-archives/b8f084aae25212a478da8ebd4de292545509ea87d441d486c35cbe5408630611.py', 'sha256': 'b8f084aae25212a478da8ebd4de292545509ea87d441d486c35cbe5408630611'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/douyin-laike-operator/scripts/switch_read_recovery.py', 'sha256': '67993fc900f1be5a0805ed24f047611699b28d40016bcd0d7f76af2a38f95d7b'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-confirm-anchor-path-candidate/dependency-source-archives/67993fc900f1be5a0805ed24f047611699b28d40016bcd0d7f76af2a38f95d7b.py', 'sha256': '67993fc900f1be5a0805ed24f047611699b28d40016bcd0d7f76af2a38f95d7b'})
    if reference=={'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/complaint_exact_recheck.py', 'sha256': '7e9bb5783bdac844802e83ef7a179f5613237e67526b9d8120d26d9b92770549'}:return o.raw({'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-exact-historical-code-candidate/dependency-source-archives/7e9bb5783bdac844802e83ef7a179f5613237e67526b9d8120d26d9b92770549.py', 'sha256': '7e9bb5783bdac844802e83ef7a179f5613237e67526b9d8120d26d9b92770549'})
    extra={('/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/existing_result_runner.py', 'e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f'): {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/dependency-source-archives/e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f.py', 'sha256': 'e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f'}, ('/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/unbound_case_runner.py', 'e2eb33e8c8083b1a55cf276db3f1ee878d6afef53959b1aa70a515bf5d89f81f'): {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/dependency-source-archives/e2eb33e8c8083b1a55cf276db3f1ee878d6afef53959b1aa70a515bf5d89f81f.py', 'sha256': 'e2eb33e8c8083b1a55cf276db3f1ee878d6afef53959b1aa70a515bf5d89f81f'}, ('/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/case_alias_v3.py', 'e0aa1a6e5a3e20c9197bea4b963c00c9f5208d80db2c331b94b1b4b64bbeb928'): {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/dependency-source-archives/e0aa1a6e5a3e20c9197bea4b963c00c9f5208d80db2c331b94b1b4b64bbeb928.py', 'sha256': 'e0aa1a6e5a3e20c9197bea4b963c00c9f5208d80db2c331b94b1b4b64bbeb928'}, ('/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/legacy_alias_code_replay.py', 'f2dbccf8c0e0b160941a1fbb4e1f16bf5c2f37b55bcbb93229233921dad3aecb'): {'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/dependency-source-archives/f2dbccf8c0e0b160941a1fbb4e1f16bf5c2f37b55bcbb93229233921dad3aecb.py', 'sha256': 'f2dbccf8c0e0b160941a1fbb4e1f16bf5c2f37b55bcbb93229233921dad3aecb'}}
    if (reference['path'],reference['sha256'])in extra:return o.raw(extra[(reference['path'],reference['sha256'])])
    # Fixed old Q bytes, data-only. Final effective graph still checks new
    # canonical Q; these bytes never authorize a current source or execute.
    original={'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/program_review_quality.py', 'sha256': '8d0f5168f47374c11c78e6a7353d650af9147a88d3554ac308f7ecae11c332d1'}
    archive={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-quality-score-bullet-candidate/dependency-source-archives/8d0f5168f47374c11c78e6a7353d650af9147a88d3554ac308f7ecae11c332d1.py', 'sha256': '8d0f5168f47374c11c78e6a7353d650af9147a88d3554ac308f7ecae11c332d1'}
    if reference==original:
        o.need(archive['sha256']==original['sha256'],'current-quality-old-code-exact-archive');return o.raw(archive)
    if o.ref(reference['path'])==reference:return o.raw(reference)
    # Only registered, hash-pinned reviewed source policies provide old CODE
    # material. This is data-only; installed effective graph remains current.
    if Path(reference['path']).suffix=='.py':
        import importlib
        sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'));reboot=importlib.import_module('violation_reboot_continuation');choices=reboot.dependency_policies();o.need(len(choices)<=32,'quality-old-source-policy-budget');matches=[]
        for policyref,_,_ in choices:
            _,policy=reboot.dependency_policy(policyref)
            for target in policy['targets']:
                if target['before']==reference:
                    archive=target['archive'];o.need(archive['sha256']==reference['sha256'],'quality-old-source-archive-binding');matches.append(o.raw(archive))
        if matches:
            o.need(all(data==matches[0]for data in matches),'quality-old-source-archive-ambiguity');return matches[0]
    return o.raw(reference)

QUALITY_CURRENT_FIELD='current_program_quality_source'
QUALITY_CURRENT_KIND='same-preview-program-quality-source-v1'
QUALITY_CURRENT_SUMMARY={'path':str(ROOT/'work/2026-10-24/full-three-flow-run-20261024/complaint6-program-quality-waiting-summary.json'),'sha256':'2460f60606277fced2962fd67af69126c697d52b86c8da8d66a1d0e65685a97c'}
QUALITY_CURRENT_PREVIOUS={'path':str(ROOT/'work/performance-audit/complaint-exact-window-raise-candidate/supervisor-release.json'),'sha256':'81bb06f1401f543fb0f1fea1ccbdda108ebf599cb2bf21f94ae9df574864e875'}
_window_verify_before_quality=verify_window_source_append

def current_quality_facts(archives=(),*,initial=False):
    summary=o.doc(QUALITY_CURRENT_SUMMARY);parent=json.loads(window_material(summary['parent'],archives));engine=json.loads(window_material(summary['engine'],archives));request=o.doc(summary['parent_handoff']);workshop=o.doc(summary['typed_handoff']);folder=Path(summary['parent']['path']).parent
    prior=_window_verify_before_quality(parent,parent[h.FIELD],installed=False)
    o.need(summary['task_id']=='task-e851f61b8d7642391ec23524' and summary['attempt']==6 and parent['status']==engine['status']=='waiting' and not parent.get('error') and not engine.get('error') and len(parent['calls'])==3 and len(engine['calls'])==46,'current-quality-exact-waiting')
    o.need(parent[h.FIELD]==parent[h.PLAN_FIELD]==engine[h.FIELD]==engine[h.PLAN_FIELD] and parent[WINDOW_SOURCE_FIELD]==engine[WINDOW_SOURCE_FIELD] and parent['calls'][:2]==prior['failed_calls'],'current-quality-original-anchor')
    o.need(all(c['state']=='returned' and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in (43,44)),'current-quality-no-unknown')
    child=parent['child'];o.need(child['status']=='waiting' and child['engine']==summary['engine'] and child['handoff']==engine['handoff']==summary['parent_handoff'] and child['waiting_for']==engine['waiting_for']==request['response_kind']=='complaint-region-qa-response-v1','current-quality-typed-handoff')
    call=parent['calls'][2];launch=o.doc(call['launch']);exit=o.doc(call['result']);o.need(call['state']=='returned' and call['argv']==launch['argv']==exit['argv'] and exit['launch']==call['launch'] and exit['returncode']==0 and exit['stderr']=='' and json.loads(exit['stdout'])==child,'current-quality-natural-child2')
    o.need(request['order']==parent['order'] and request['phase']=='collect' and request['company']==o.validate(parent['order'])['companies'][engine['index']] and request['program_quality_exception']=='review-quality-locator:非常差' and request['preview'] in summary['capture_evidence'],'current-quality-current-source-request')
    preview=o.doc(request['preview']);o.need(preview['state']=='awaiting-visual-review' and preview['source']==prior['facts']['operation']['manifest']['source'] and preview['review_keys']==[request['review_key']] and request['manifest']==o.doc(prior['facts']['failure_ref'])['frame_manifest'],'current-quality-same-original-preview')
    refs=[QUALITY_CURRENT_SUMMARY,summary['parent'],summary['engine'],summary['parent_handoff'],summary['typed_handoff'],summary['parent_run_exit'],summary['worker_exit'],summary['started'],summary['request'],*summary['capture_evidence'],*summary['quality_evidence'],call['launch'],call['result']]
    for r in refs:window_material(r,archives)
    intent,plan,first,exception=[o.doc(r)for r in summary['quality_evidence']];o.need(intent['preview']==exception['preview']==request['preview'] and exception['reason']==request['program_quality_exception'] and plan['image']==preview['image'] and first['kind']=='local-vision-cell-ocr-v1','current-quality-original-cache')
    wrequest=o.doc(o.doc(summary['worker_exit'])['request']);o.need(workshop['task_id']==summary['task_id'] and workshop['details']['parent_handoff']==summary['parent_handoff'] and workshop['original_outer']==wrequest['task']['outer'] and wrequest['context']['order']==parent['order'],'current-quality-original-task-outer')
    if initial:
        for r in (summary['parent'],summary['engine']):o.need(o.ref(r['path'])==r,'current-quality-original-CAS')
    return {'summary':summary,'parent':parent,'engine':engine,'request':request,'workshop':workshop,'folder':str(folder),'prior':prior,'fixed':refs}

def current_quality_tip(base,release_ref,*,installed):
    release=o.doc(release_ref);paths={str(ROOT/p)for p in ('skills/negative-review-complaints/scripts/review_capture_focus.py','skills/negative-review-complaints/scripts/program_review_quality.py','skills/violation-notifier/scripts/violation_reboot_continuation.py')};helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');targets=release['targets']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==QUALITY_CURRENT_PREVIOUS and len(targets)==3 and {t['target']for t in targets}==paths,'current-quality-reviewed-release')
    policy=o.doc(release['source_repair_dependency_delta']);o.need(policy['kind']=='finite-reviewed-quality-score-dependency-delta-v1' and policy['previous_release']==QUALITY_CURRENT_PREVIOUS and policy['authorization_release']==release['source_repair_authorization_release'] and len(policy['targets'])==2 and {t['target']for t in policy['targets']}==paths-{helper},'current-quality-finite-two-source-policy')
    codes=copy.deepcopy(base['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        old=next(r for r in codes if r['path']==t['target']);pt=next(x for x in policy['targets']if x['target']==t['target']);o.need(t['old_sha256']==old['sha256'] and pt['before']==old and pt['after']==t['after'] and pt['archive']['sha256']==old['sha256'],'current-quality-reviewed-CAS');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def verify_current_quality_source(current,oldproof,*,installed=True):
    proof=current[QUALITY_CURRENT_FIELD];p=o.doc(proof);facts=current_quality_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.program-quality-source-admission'/facts['summary']['parent']['sha256']
    o.need(Path(proof['path'])==base/'proof.json' and p['kind']==QUALITY_CURRENT_KIND and p['ui_used']is False and p['original_parent']==facts['summary']['parent'] and p['original_engine']==facts['summary']['engine'] and p['oldproof']==oldproof==facts['parent'][h.FIELD] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'current-quality-canonical-source-proof')
    o.need(current['calls'][:3]==facts['parent']['calls'] and current.get('resolved_errors')==facts['parent'].get('resolved_errors') and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in (h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD)),'current-quality-preserved-origin')
    codes=current_quality_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'current-quality-effective-graph')
    return {**facts['prior'],'code_refs':codes,'quality_current_proof':proof,'quality_current_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[a['archive']for a in p['archives']]]}

def verify_window_source_append(current,oldproof,*,installed=True):
    if current.get(QUALITY_CURRENT_FIELD):return verify_current_quality_source(current,oldproof,installed=installed)
    return _window_verify_before_quality(current,oldproof,installed=installed)

_panel_engine_before_current_quality=panel_engine_calls
def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if engine.get(QUALITY_CURRENT_FIELD) or current.get(QUALITY_CURRENT_FIELD):o.need(current.get(QUALITY_CURRENT_FIELD)==engine.get(QUALITY_CURRENT_FIELD) and engine.get(QUALITY_CURRENT_FIELD)is not None,'current-quality-parent-engine-proof')
    return _panel_engine_before_current_quality(engine)

def admit_current_quality_source(release_ref):
    summary=o.doc(QUALITY_CURRENT_SUMMARY);folder=Path(summary['parent']['path']).parent;base=folder/'.program-quality-source-admission'/summary['parent']['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():
            proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'current-quality-same-release')
        else:
            facts=current_quality_facts(initial=True);codes=current_quality_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((summary['parent'],summary['engine']))];p={'kind':QUALITY_CURRENT_KIND,'oldproof':facts['parent'][h.FIELD],'original_parent':summary['parent'],'original_engine':summary['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=current_quality_facts(p['archives'])
        for name in('engine','parent'):
            dest=folder/('engine.json'if name=='engine'else'launcher.json');old=facts[name];new={**old,QUALITY_CURRENT_FIELD:proof};value=o.doc(o.ref(dest));o.need(value in(old,new),'current-quality-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        parent=o.doc(o.ref(folder/'launcher.json'));verify_current_quality_source(parent,p['oldproof']);return {'kind':QUALITY_CURRENT_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'ui_used':False}

def current_quality_response(parent_ref,workshop_ref):
    import program_review_quality as quality
    parent=o.doc(parent_ref);admitted=verify_current_quality_source(parent,parent[h.FIELD]);facts=admitted['quality_current_facts'];summary=facts['summary'];o.need(workshop_ref==summary['typed_handoff'] and parent['status']=='waiting' and parent['child']['handoff']==summary['parent_handoff'],'current-quality-response-original-waiting')
    request=facts['request'];proof=parent[QUALITY_CURRENT_FIELD];out=Path(request['preview']['path']).parent/'program-quality-repairs'/proof['sha256'];attestation=quality.create(request['preview'],out);preview=o.doc(request['preview']);quality.verify(attestation,{**preview,'state':'complete','quality_approved_at':stamp()})
    base=Path(facts['folder'])/'quality-responses'/summary['parent_handoff']['sha256']/proof['sha256'];base.mkdir(parents=True,exist_ok=True);response=o.immutable(base/'parent-response.json',{'kind':request['response_kind'],'request':summary['parent_handoff'],'attestation':attestation});wrapped=o.immutable(base/'workshop-response.json',{'kind':'workshop-handoff-response-v1','request':workshop_ref,'task_id':summary['task_id'],'parent_response':response});return {'parent_response':response,'workshop_response':wrapped,'quality_attestation':attestation,'ui_used':False,'business_acceptance':False}


QUALITY_GENERATION_KIND='same-preview-program-quality-source-generation-v1'
_quality_verify_before_generation=verify_current_quality_source
_quality_admit_before_generation=admit_current_quality_source

def quality_generation_verify(current,oldproof,*,installed=True,depth=0):
    o.need(depth<8,'quality-source-generation-limit');proof=current[QUALITY_CURRENT_FIELD];p=o.doc(proof)
    if p['kind']!=QUALITY_GENERATION_KIND:return _quality_verify_before_generation(current,oldproof,installed=installed)
    facts=quality_generation_facts(p['summary'],p['archives'],p['previous_proof'],depth=depth+1);folder=Path(facts['folder']);base=folder/'.program-quality-source-admission'/facts['summary']['parent']['sha256']
    o.need(Path(proof['path'])==base/'proof.json' and p['ui_used']is False and p['oldproof']==oldproof==facts['parent'][h.FIELD] and p['original_parent']==facts['summary']['parent'] and p['original_engine']==facts['summary']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'quality-generation-canonical-proof')
    o.need(current['calls'][:len(facts['parent']['calls'])]==facts['parent']['calls'] and current.get('resolved_errors')==facts['parent'].get('resolved_errors') and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD)),'quality-generation-preserved-origin')
    codes=quality_generation_tip(facts['prior'],p['release'],p['summary'],p['previous_proof'],installed=installed);o.need(p['code_refs']==codes,'quality-generation-effective-graph')
    return {**facts['prior'],'code_refs':codes,'quality_current_proof':proof,'quality_current_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],p['summary'],*[a['archive']for a in p['archives']]]}

def quality_generation_facts(summary_ref,archives,previous_proof,*,initial=False,depth=0):
    o.need(depth<8,'quality-source-generation-limit');summary=o.doc(summary_ref);parent=json.loads(window_material(summary['parent'],archives));engine=json.loads(window_material(summary['engine'],archives));folder=Path(summary['parent']['path']).parent
    o.need(Path(summary['parent']['path'])==folder/'launcher.json' and Path(summary['engine']['path'])==folder/'engine.json' and parent[QUALITY_CURRENT_FIELD]==engine[QUALITY_CURRENT_FIELD]==previous_proof,'quality-generation-original-previous-proof')
    prior=quality_generation_verify(parent,parent[h.FIELD],installed=False,depth=depth+1);old=prior['quality_current_facts'];request=o.doc(summary['parent_handoff']);workshop=o.doc(summary['typed_handoff'])
    o.need(parent['status']==engine['status']=='waiting' and not parent.get('error') and not engine.get('error') and parent['order']==old['parent']['order']==engine['order']==request['order'] and parent[h.FIELD]==parent[h.PLAN_FIELD]==engine[h.FIELD]==engine[h.PLAN_FIELD] and parent[WINDOW_SOURCE_FIELD]==engine[WINDOW_SOURCE_FIELD],'quality-generation-exact-waiting-order')
    o.need(len(parent['calls'])>len(old['parent']['calls']) and len(engine['calls'])>len(old['engine']['calls']) and parent['calls'][:len(old['parent']['calls'])]==old['parent']['calls'] and engine['calls'][:len(old['engine']['calls'])]==old['engine']['calls'],'quality-generation-preserved-prefix')
    o.need(all(c['state']=='returned'and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44)),'quality-generation-no-unknown')
    for c in parent['calls'][len(old['parent']['calls']):]:
        launch=o.doc(c['launch']);ex=o.doc(c['result']);o.need(c['state']=='returned' and c['argv']==launch['argv']==ex['argv'] and ex['launch']==c['launch'] and ex['returncode']==0 and ex['stderr']=='','quality-generation-natural-child')
    child=parent['child'];o.need(child['status']=='waiting' and child['engine']==summary['engine'] and child['handoff']==engine['handoff']==summary['parent_handoff'] and child['waiting_for']==engine['waiting_for']==request['response_kind']=='complaint-region-qa-response-v1' and json.loads(o.doc(parent['calls'][-1]['result'])['stdout'])==child,'quality-generation-natural-waiting-child')
    o.need(Path(summary['parent_handoff']['path'])==folder/'handoffs'/(str(len(engine['calls']))+'.json') and request['phase']==engine['phase']=='collect' and request['company']==o.validate(parent['order'])['companies'][engine['index']] and request['program_quality_exception']=='review-quality-locator:非常差','quality-generation-scope-handoff')
    preview=o.doc(request['preview']);o.need(preview['state']=='awaiting-visual-review' and preview['review_keys']==[request['review_key']] and preview['source']['path'].startswith(str(folder/'companies')+'/') and preview['image']!=o.doc(old['request']['preview'])['image'],'quality-generation-new-source-bound-preview')
    manifest=o.doc(request['manifest']);o.need(manifest['source']==preview['source'] and manifest['review_keys']==preview['review_keys'],'quality-generation-manifest-source')
    captures=summary.get('capture_evidence',summary.get('second_card_capture',[]));o.need(request['preview']in captures and any(r['path']==preview['image']['path']and r['sha256']==preview['image']['sha256']for r in captures),'quality-generation-exact-capture')
    evidence=summary['quality_evidence'];docs={Path(r['path']).name:o.doc(r)for r in evidence};o.need(docs['exception.json']['preview']==request['preview'] and docs['exception.json']['reason']==request['program_quality_exception'] and docs['plan.json']['image']==preview['image'] and docs['first-ocr.json']['kind']=='local-vision-cell-ocr-v1','quality-generation-original-failed-cache')
    wexit=o.doc(summary['worker_exit']);wrequest=o.doc(wexit['request']);o.need(wexit['returncode']==0 and wrequest['task']['id']==summary['task_id']==workshop['task_id']==old['workshop']['task_id'] and wrequest['context']['order']==parent['order'] and workshop['original_outer']==wrequest['task']['outer']==old['workshop']['original_outer'] and workshop['details']['parent_handoff']==summary['parent_handoff'],'quality-generation-original-worker-clock')
    fixed=[summary_ref,summary['parent'],summary['engine'],summary['parent_handoff'],summary['typed_handoff'],summary['worker_exit'],summary['started'],summary['parent_run_exit'],wexit['request'],request['preview'],request['manifest'],preview['source'],*captures,*evidence]
    if summary.get('first_card_registration'):fixed.append(summary['first_card_registration'])
    for r in fixed:window_material(r,archives)
    if initial:
        for r in(summary['parent'],summary['engine']):o.need(o.ref(r['path'])==r,'quality-generation-original-CAS')
    return {'summary':{**summary,'capture_evidence':captures},'parent':parent,'engine':engine,'request':request,'workshop':workshop,'folder':str(folder),'prior':prior,'fixed':fixed}

def quality_generation_tip(prior,release_ref,summary_ref,previous_proof,*,installed):
    release=o.doc(release_ref);previous=o.doc(previous_proof)['release'];helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');paths={helper,str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/negative-review-complaints/scripts/program_review_quality.py')};targets=release['targets'];policy=o.doc(release['source_repair_dependency_delta'])
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous==policy['previous_release'] and release['quality_recovery_input']==summary_ref==policy['quality_recovery_input'] and policy['authorization_release']==release['source_repair_authorization_release'] and policy['kind']=='finite-reviewed-quality-score-range-dependency-delta-v1','quality-generation-reviewed-input-release')
    o.need(len(targets)==3 and {t['target']for t in targets}==paths and len(policy['targets'])==2 and {t['target']for t in policy['targets']}==paths-{helper},'quality-generation-finite-targets');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        old=next(r for r in codes if r['path']==t['target']);pt=next(x for x in policy['targets']if x['target']==t['target']);o.need(t['old_sha256']==old['sha256'] and pt['before']==old and pt['after']==t['after'] and pt['archive']['sha256']==old['sha256'],'quality-generation-exact-source-CAS');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def verify_current_quality_source(current,oldproof,*,installed=True):return quality_generation_verify(current,oldproof,installed=installed)

def admit_current_quality_source(release_ref):
    release=o.doc(release_ref)
    if 'quality_recovery_input'not in release:return _quality_admit_before_generation(release_ref)
    sr=release['quality_recovery_input'];summary=o.doc(sr);folder=Path(summary['parent']['path']).parent;base=folder/'.program-quality-source-admission'/summary['parent']['sha256']
    with (folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref and p['summary']==sr,'quality-generation-same-input')
        else:
            previous_proof=o.doc(summary['parent'])[QUALITY_CURRENT_FIELD];facts=quality_generation_facts(sr,(),previous_proof,initial=True);codes=quality_generation_tip(facts['prior'],release_ref,sr,previous_proof,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((summary['parent'],summary['engine']))];p={'kind':QUALITY_GENERATION_KIND,'oldproof':facts['parent'][h.FIELD],'original_parent':summary['parent'],'original_engine':summary['engine'],'previous_proof':previous_proof,'summary':sr,'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=quality_generation_facts(sr,p['archives'],p['previous_proof'])
        for name in('engine','parent'):
            dest=folder/('engine.json'if name=='engine'else'launcher.json');old=facts[name];new={**old,QUALITY_CURRENT_FIELD:proof};value=o.doc(o.ref(dest));o.need(value in(old,new),'quality-generation-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        parent=o.doc(o.ref(folder/'launcher.json'));verify_current_quality_source(parent,parent[h.FIELD]);return {'kind':QUALITY_GENERATION_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'ui_used':False}


EMPTY_RESULT_FIELD='empty_result_drawer_source'
EMPTY_RESULT_KIND='verified-confirmed-open-empty-drawer-source-v1'
EMPTY_RESULT_FAILURE={'path':str(ROOT/'work/2026-10-24/full-three-flow-run-20261024/complaint10-empty-result-drawer-failure-summary.json'),'sha256':'5e62853fbe71e6b90ad39cca9dbe42d1e6773e033a847322057f39f1fddb6a7c'}
_quality_verify_before_empty_result=verify_current_quality_source
_panel_engine_before_empty_result=panel_engine_calls

def empty_result_facts(archives=(),*,initial=False):
    import existing_result_runner as runner
    failure=o.doc(EMPTY_RESULT_FAILURE);parent=json.loads(window_material(failure['parent'],archives));engine=json.loads(window_material(failure['engine'],archives));operation=json.loads(window_material(failure['operation'],archives));folder=Path(failure['parent']['path']).parent
    prior=_quality_verify_before_empty_result(parent,parent[h.FIELD],installed=False);old=prior['quality_current_facts'];o.need(failure['task_id']==old['workshop']['task_id'] and failure['attempt']==10 and failure['leaf']=='result-review-mismatch:store' and parent['status']==engine['status']=='hold' and parent['error']=='execution-child-stopped' and engine['error']==failure['leaf'] and len(parent['calls'])==7 and len(engine['calls'])==59,'empty-result-fixed-hold')
    o.need(parent['calls'][:len(old['parent']['calls'])]==old['parent']['calls'] and engine['calls'][:len(old['engine']['calls'])]==old['engine']['calls'] and engine['calls'][58]==failure['engine_last_failed_call'] and all(c['state']=='returned'and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58)),'empty-result-no-unknown-prefix')
    last=parent['calls'][-1];ex=o.doc(last['result']);launch=o.doc(last['launch']);o.need(last['state']=='returned' and last['result']==failure['child_exit'] and ex['argv']==last['argv']==launch['argv'] and ex['launch']==last['launch'] and ex['returncode']==2 and ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':failure['leaf']},'empty-result-exact-child6')
    for call in parent['calls'][len(old['parent']['calls']):-1]:
        reply=o.doc(call['result']);o.need(call['state']=='returned' and reply['returncode']==0 and reply['argv']==call['argv'] and reply['launch']==call['launch'],'empty-result-prior-natural-child')
    o.need(operation['state']=='opened' and operation['open_command']==failure['operation_open_command'] and operation['open_reply']==failure['operation_open_reply'] and failure['open_input_confirmed']is True and failure['unknown_open_input']is False and operation['error']==failure['leaf'] and operation['submission_enabled']is operation['send_enabled']is False,'empty-result-confirmed-original-open')
    runner.clicked(operation['open_reply'],operation['open_command']);v,order,row=runner.manifest_inputs(operation['manifest'],historical_complete=True);o.need(operation['manifest']['inputs']['source']==failure['source'] and operation['manifest']['inputs']['profile']==failure['profile'] and all(row[k]==failure['expected_source_fields'][k]for k in('review_id','store','customer','text','date')),'empty-result-source-facts')
    runner.normal_page(o.doc(failure['normal_before']),v,order,row);drawer=o.doc(failure['drawer']);o.need(runner.empty_loading_drawer(drawer,v) and failure['drawer_fields_actual']=={'store':[],'customer':[],'text':[]} and failure['drawer_body_count']==1 and failure['drawer_body_children']==[0],'empty-result-known-empty-skeleton')
    fixed=[EMPTY_RESULT_FAILURE,failure['parent'],failure['engine'],failure['operation'],failure['normal_before'],failure['drawer'],failure['source'],failure['profile'],failure['started'],failure['request'],failure['worker_exit'],failure['parent_run_exit'],failure['child_exit'],last['launch'],*failure['operation_files'],*failure['two_registered_frames'],failure['quality48_recovery']]
    for r in fixed:window_material(r,archives)
    if initial:
        for r in(failure['parent'],failure['engine'],failure['operation'],*failure['five_ledgers']):o.need(o.ref(r['path'])==r,'empty-result-original-CAS')
    return {'failure':failure,'parent':parent,'engine':engine,'operation':operation,'folder':str(folder),'prior':prior,'fixed':fixed}

def empty_result_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');rels=('existing_result_runner.py','unbound_case_runner.py','case_alias_v3.py','legacy_alias_code_replay.py','review_capture_focus.py','legacy_alias_catalogue_result_wait_v1.json');paths={str(ROOT/'skills/negative-review-complaints/scripts'/n)for n in rels};targets=release['targets'];previous_release=o.doc(prior['quality_current_proof'])['release']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous_release==policy['previous_release'] and release['result_recovery_input']==EMPTY_RESULT_FAILURE==policy['result_recovery_input'] and policy['kind']=='finite-reviewed-empty-result-drawer-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'empty-result-reviewed-release-input')
    o.need(len(targets)==7 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==6 and {t['target']for t in policy['targets']}==paths,'empty-result-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']==old and t['old_sha256']==(old['sha256']if old else None),'empty-result-exact-source-CAS')
        if old:o.need(pt['archive']['sha256']==old['sha256'],'empty-result-before-data-hash');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(Path(t['target']).name=='legacy_alias_catalogue_result_wait_v1.json' and pt['archive']is None,'empty-result-only-new-catalogue');codes.append({'path':t['target'],'sha256':t['after']['sha256']})
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def empty_result_pair(parent,engine,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in(parent,engine):error=value.pop('error');value.update(status='running',**{EMPTY_RESULT_FIELD:proof});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof})
    return parent,engine

def verify_empty_result_source(current,oldproof,*,installed=True):
    proof=current[EMPTY_RESULT_FIELD];p=o.doc(proof);facts=empty_result_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.empty-result-drawer-source'/facts['failure']['parent']['sha256'];o.need(p['kind']==EMPTY_RESULT_KIND and p['ui_used']is False and Path(proof['path'])==base/'proof.json' and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'empty-result-canonical-proof')
    expected,_=empty_result_pair(facts['parent'],facts['engine'],proof);o.need(current['calls'][:7]==facts['parent']['calls'] and current.get('resolved_errors')==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD)),'empty-result-preserved-original')
    codes=empty_result_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'empty-result-effective-graph');return {**facts['prior'],'code_refs':codes,'failed_calls':[*facts['prior']['failed_calls'],facts['parent']['calls'][-1]],'empty_result_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[x['archive']for x in p['archives']]]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    if current.get(EMPTY_RESULT_FIELD):return verify_empty_result_source(current,oldproof,installed=installed)
    return _quality_verify_before_empty_result(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if not(engine.get(EMPTY_RESULT_FIELD)or current.get(EMPTY_RESULT_FIELD)):return _panel_engine_before_empty_result(engine)
    o.need(engine.get(EMPTY_RESULT_FIELD)==current.get(EMPTY_RESULT_FIELD) and engine.get(EMPTY_RESULT_FIELD)is not None,'empty-result-parent-engine-proof');admitted=verify_empty_result_source(current,engine[h.FIELD]);facts=admitted['empty_result_facts'];expected=empty_result_pair(facts['parent'],facts['engine'],engine[EMPTY_RESULT_FIELD])[1];o.need(engine['calls'][:59]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'] and all(engine[k]==current[k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD)),'empty-result-preserved-engine');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58)]

def recover_empty_result_source(release_ref):
    failure=o.doc(EMPTY_RESULT_FAILURE);folder=Path(failure['parent']['path']).parent;base=folder/'.empty-result-drawer-source'/failure['parent']['sha256']
    with(folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'empty-result-same-release')
        else:
            facts=empty_result_facts(initial=True);codes=empty_result_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((failure['parent'],failure['engine'],failure['operation']))];p={'kind':EMPTY_RESULT_KIND,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=empty_result_facts(p['archives']);parent,engine=empty_result_pair(facts['parent'],facts['engine'],proof)
        for dest,old,new in((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in(old,new),'empty-result-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_empty_result_source(parent,parent[h.FIELD]);return {'kind':EMPTY_RESULT_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'operation_unchanged':o.ref(failure['operation']['path'])==failure['operation'],'ui_used':False}

EXACT_RECHECK_FIELD='exact_recheck_code_source'
EXACT_RECHECK_KIND='verified-exact-recheck-pre-input-source-v1'
EXACT_RECHECK_INPUT={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-exact-historical-code-candidate/exact-recovery-input.json', 'sha256': '51475098039753f67b67150e5c23dcdff6f4aef3df6421fd737d110777d2d4b2'}
_quality_verify_before_exact_recheck=verify_current_quality_source
_panel_engine_before_exact_recheck=panel_engine_calls

def exact_recheck_facts(archives=(),*,initial=False):
    import ast,complaint_exact_recheck as exact
    fixed=o.doc(EXACT_RECHECK_INPUT);failure=o.doc(fixed['failure']);parent=json.loads(window_material(failure['parent'],archives));engine=json.loads(window_material(failure['engine'],archives));folder=Path(failure['parent']['path']).parent;prior=_quality_verify_before_exact_recheck(parent,parent[h.FIELD],installed=False);old=prior['empty_result_facts'];prior={**prior,'exact_parent_empty_proof':parent[EMPTY_RESULT_FIELD]}
    o.need(failure['task_id']==old['failure']['task_id'] and failure['attempt']==11 and failure['leaf']=='exact-recheck-code-changed' and parent['status']==engine['status']=='hold' and parent['error']=='execution-child-stopped' and engine['error']==failure['leaf'] and len(parent['calls'])==8 and len(engine['calls'])==109,'exact-recheck-fixed-hold')
    o.need(parent['calls'][:7]==old['parent']['calls'] and engine['calls'][:59]==old['engine']['calls'] and engine['calls'][108]==fixed['failed_engine_call'] and all(c['state']=='returned' and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58,108)),'exact-recheck-no-unknown-prefix')
    call=parent['calls'][-1];exit=o.doc(call['result']);launch=o.doc(call['launch']);o.need(call['state']=='returned' and call['result']==failure['child_exit'] and exit['argv']==call['argv']==launch['argv'] and exit['launch']==call['launch'] and exit['returncode']==2 and exit['stderr']=='' and json.loads(exit['stdout'])=={'ok':False,'error':failure['leaf']},'exact-recheck-exact-child7')
    manifest=o.doc(failure['historical_manifest']);index=json.loads(window_material(failure['historical_active_index'],archives));navigation=navigation_prerequisite(failure);ledger=json.loads(window_material(fixed['current_ledger'],archives));order=o.doc(parent['order']);o.need(index['manifest']==failure['historical_manifest'] and index['review_key']==failure['review_key'] and manifest['day']==failure['historical_day']<order['day'] and manifest['review_key']==failure['review_key'],'exact-recheck-historical-version')
    o.need(navigation['state']=='complete' and navigation['calls']==failure['recheck_navigation_calls'] and len(navigation['calls'])==1 and navigation['calls'][0]['state']=='confirmed' and navigation['calls'][0]['command']['op']=='activate','exact-recheck-original-target-activation')
    o.need(failure['current_day_manifest_present']is False and failure['code_differences']==[{'path':str(ROOT/'skills/negative-review-complaints/scripts/existing_result_runner.py'),'expected':'e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f','actual':'a1f14ccab53961bbca35a9907c1f4dc6af50aceb419e68848dc1636709488665'}],'exact-recheck-only-reviewed-runner-drift')
    raw=quality_original_code(failure['exact_failure_source']);tree=ast.parse(raw);prepare=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='prepare');inputs=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='inputs');o.need('canonical_manifest(oldm' in ast.unparse(prepare) and "m['code'] == codes()" in ast.unparse(inputs) and not any(isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=='request'for x in ast.walk(prepare)),'exact-recheck-known-source-guard-before-input')
    version=o.digest({'dispatch_id':order['dispatch_id'],'day':order['day'],'key':failure['review_key'],'previous_result':ledger['tasks'][failure['review_key']]['result']['evidence']});new=exact.base(manifest['root'],manifest['review_key'])/version/'manifest.json'
    refs=[fixed['failure'],failure['parent'],failure['engine'],failure['started'],failure['worker_exit'],failure['parent_run_exit'],failure['child_exit'],call['launch'],failure['source'],failure['profile'],failure['acquisition'],failure['operator'],failure['historical_active_index'],failure['historical_manifest'],failure['recheck_navigation'],failure['prior_empty_result_recovery_complete'],fixed['current_ledger']]
    for r in refs:
        if r!=failure['recheck_navigation']:window_material(r,archives)
    if initial:
        for r in(failure['parent'],failure['engine'],fixed['current_ledger'],*fixed['protected_ledgers']):o.need(o.ref(r['path'])==r,'exact-recheck-original-CAS')
        o.need(not new.exists(),'exact-recheck-no-new-version-input')
    return {'failure':failure,'parent':parent,'engine':engine,'folder':str(folder),'prior':prior,'fixed':refs,'input':fixed,'new_manifest':str(new)}

def exact_recheck_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');rels=('complaint_exact_recheck.py','review_capture_focus.py');paths={str(ROOT/'skills/negative-review-complaints/scripts'/n)for n in rels};targets=release['targets'];previous_release=o.doc(prior['exact_parent_empty_proof'])['release']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous_release==policy['previous_release'] and release['exact_recovery_input']==EXACT_RECHECK_INPUT==policy['exact_recovery_input'] and policy['kind']=='finite-reviewed-exact-recheck-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'exact-recheck-reviewed-release-input')
    o.need(len(targets)==3 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==2 and {t['target']for t in policy['targets']}==paths,'exact-recheck-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']==old and t['old_sha256']==(old['sha256']if old else None),'exact-recheck-exact-source-CAS')
        if old:o.need(pt['archive']['sha256']==old['sha256'],'exact-recheck-before-data-hash');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(Path(t['target']).name=='legacy_alias_catalogue_result_wait_v1.json' and pt['archive']is None,'exact-recheck-only-new-catalogue');codes.append({'path':t['target'],'sha256':t['after']['sha256']})
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def exact_recheck_pair(parent,engine,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in(parent,engine):error=value.pop('error');value.update(status='running',**{EXACT_RECHECK_FIELD:proof});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof})
    return parent,engine

def verify_exact_recheck_source(current,oldproof,*,installed=True):
    proof=current[EXACT_RECHECK_FIELD];p=o.doc(proof);facts=exact_recheck_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.exact-recheck-source'/facts['failure']['parent']['sha256'];o.need(p['kind']==EXACT_RECHECK_KIND and p['ui_used']is False and Path(proof['path'])==base/'proof.json' and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'exact-recheck-canonical-proof')
    expected,_=exact_recheck_pair(facts['parent'],facts['engine'],proof);o.need(current['calls'][:8]==facts['parent']['calls'] and current.get('resolved_errors')==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD)),'exact-recheck-preserved-original')
    codes=exact_recheck_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'exact-recheck-effective-graph');return {**facts['prior'],'code_refs':codes,'failed_calls':[*facts['prior']['failed_calls'],facts['parent']['calls'][-1]],'exact_recheck_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[x['archive']for x in p['archives']]]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    if current.get(EXACT_RECHECK_FIELD):return verify_exact_recheck_source(current,oldproof,installed=installed)
    return _quality_verify_before_exact_recheck(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if not(engine.get(EXACT_RECHECK_FIELD)or current.get(EXACT_RECHECK_FIELD)):return _panel_engine_before_exact_recheck(engine)
    o.need(engine.get(EXACT_RECHECK_FIELD)==current.get(EXACT_RECHECK_FIELD) and engine.get(EXACT_RECHECK_FIELD)is not None,'exact-recheck-parent-engine-proof');admitted=verify_exact_recheck_source(current,engine[h.FIELD]);facts=admitted['exact_recheck_facts'];expected=exact_recheck_pair(facts['parent'],facts['engine'],engine[EXACT_RECHECK_FIELD])[1];o.need(engine['calls'][:109]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'] and all(engine[k]==current[k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD)),'exact-recheck-preserved-engine');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58,108)]

def recover_exact_recheck_source(release_ref):
    failure=o.doc(o.doc(EXACT_RECHECK_INPUT)['failure']);folder=Path(failure['parent']['path']).parent;base=folder/'.exact-recheck-source'/failure['parent']['sha256']
    with(folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'exact-recheck-same-release')
        else:
            facts=exact_recheck_facts(initial=True);codes=exact_recheck_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((failure['parent'],failure['engine'],failure['historical_active_index'],o.doc(EXACT_RECHECK_INPUT)['current_ledger']))];p={'kind':EXACT_RECHECK_KIND,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=exact_recheck_facts(p['archives']);parent,engine=exact_recheck_pair(facts['parent'],facts['engine'],proof)
        for dest,old,new in((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in(old,new),'exact-recheck-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_exact_recheck_source(parent,parent[h.FIELD]);return {'kind':EXACT_RECHECK_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'historical_index_unchanged':o.ref(failure['historical_active_index']['path'])==failure['historical_active_index'],'ui_used':False}

def validate_navigation_append(original,current,raw_loader):
    """Validate one frozen complete journal plus successful read-only growth.
    raw_loader(ref) returns hash-bound bytes, never a transport result/call.
    Caller must pin original to the reviewed full snapshot (not a lost hash).
    """
    import hashlib,json,re
    from pathlib import Path
    from datetime import datetime
    from review_capture_tab import classify
    def require(condition,why):
        if not condition:raise ValueError('recheck-navigation-'+why)
    def stamp(value):
        require(type(value) is str,'time-shape');t=datetime.fromisoformat(value.replace('Z','+00:00'));require(t.utcoffset() is not None,'time-zone');return t
    fields={'kind','binding','phase','revision','state','calls','reads','created_at','completed_at'}
    require(type(original) is dict and type(current) is dict and set(original)==set(current)==fields,'fields')
    require(all(current[k]==original[k] for k in fields-{'reads','completed_at'}),'immutable-field-changed')
    require(original['kind']=='review-recheck-source-tab-activation-v1' and original['phase']=='recheck-source' and type(original['revision']) is int and original['revision']==0 and original['state']=='complete','complete-original')
    b=original['binding'];scope=b['scope'];calls=original['calls']
    require(type(calls) is list and len(calls)==1,'one-original-call');call=calls[0]
    require(set(call)=={'key','at','phase','command','state','result'} and call['key']=='original-management-tab-once' and call['phase']=='recheck-source' and call['command']=={'op':'activate','tabId':scope['tabId']} and call['state']=='confirmed','confirmed-original-activate')
    require(type(original['reads']) is list and len(original['reads'])==4 and type(current['reads']) is list and current['reads'][:4]==original['reads'] and len(current['reads'])>=4,'original-prefix')
    source=Path(b['inputs']['source']['path']);root=source.parent/'.review-recheck-tab-activation'
    key=hashlib.sha256((json.dumps(b['inputs'],ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()).hexdigest()
    created=stamp(original['created_at']);old_end=stamp(original['completed_at']);end=stamp(current['completed_at']);require(created<=old_end<=end,'completed-time-regressed')
    previous=created;paths=set();raws=[]
    for i,ref in enumerate(current['reads']):
        require(type(ref) is dict and set(ref)=={'path','sha256'} and type(ref['path']) is str and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None,'ref-shape')
        p=Path(ref['path']);require(p.is_absolute() and p==p.resolve() and p.parent.parent==root/key and re.fullmatch('[0-9a-f]{32}',p.parent.name) is not None and str(p) not in paths,'raw-canonical-journal-path');paths.add(str(p))
        label='activate' if i==1 else 'after' if i==2 else 'before'
        require(p.name==str(i).zfill(3)+'-'+label+'.json','raw-contiguous-index')
        raw=raw_loader(ref);require(type(raw) is bytes and hashlib.sha256(raw).hexdigest()==ref['sha256'],'raw-bytes-changed');record=json.loads(raw)
        require(type(record) is dict and set(record)=={'command','response','observed_at'},'raw-success-shape');at=stamp(record['observed_at']);require(previous<=at<=end,'raw-time-order');previous=at
        if i>=4:require(at>=old_end,'append-before-frozen-complete')
        reply=record['response'];require(type(reply) is dict and set(reply)=={'ok','result','error'} and reply['ok'] is True and reply['error'] is None,'raw-response-shape')
        if i==1:
            require(record['command']==call['command'] and reply['result']==call['result'],'original-activate-result')
            require(set(reply['result'])=={'tabId','windowId','url','title','active','windowFocused','observedAt','safety_version'} and all(reply['result'].get(k)==v for k,v in {'tabId':scope['tabId'],'windowId':scope['windowId'],'url':b['url'],'active':True,'windowFocused':True}.items()),'activate-scope')
            require(stamp(call['at'])<=at,'activate-time')
        else:
            require(record['command']=={'op':'tabs'} and type(reply['result']) is list and bool(reply['result']),'tabs-only')
            windows=reply['result'];windowids=set();tabids=set()
            for w in windows:
                require(type(w) is dict and set(w)=={'windowId','focused','type','tabs'} and type(w['windowId']) is int and w['windowId'] not in windowids and type(w['focused']) is bool and type(w['type']) is str and type(w['tabs']) is list,'window-shape');windowids.add(w['windowId'])
                for t in w['tabs']:
                    require(type(t) is dict and set(t)=={'tabId','windowId','title','url','active','allowed'} and type(t['tabId']) is int and t['tabId'] not in tabids and t['windowId']==w['windowId'] and type(t['active']) is bool and type(t['allowed']) is bool and type(t['title']) is str and type(t['url']) is str,'tab-shape');tabids.add(t['tabId'])
            status=classify(windows,b)
            require(status=='active' if i>=2 else status in ('original-record-active','original-record-active-window-unfocused','target-active-window-unfocused','active'),'active-scope')
        raws.append(record)
    require(stamp(raws[0]['observed_at'])<=stamp(call['at'])<=stamp(raws[1]['observed_at']) and stamp(raws[3]['observed_at'])<=old_end,'original-call-time-order')

NAVIGATION_FIELD='recheck_navigation_source_append'
NAVIGATION_KIND='verified-recheck-navigation-readonly-lifecycle-v1'
NAVIGATION_INPUT={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-recheck-navigation-lifecycle-candidate/navigation-recovery-input.json', 'sha256': '397c232f26dfdb8a8d179915e88546b9d17a66c8dbc5973d59010cd35ee14427'}
_quality_verify_before_navigation_source=verify_current_quality_source
_panel_engine_before_navigation_source=panel_engine_calls

def navigation_prerequisite(failure):
    import ast
    authority=o.doc(NAVIGATION_INPUT);summary=o.doc(authority['failure']);original=o.doc(authority['original_navigation_snapshot']);cli=o.doc(authority['old_metadata_cli']);result=json.loads(cli['stdout']);proof=o.doc(authority['old_proof']);release=o.doc(authority['old_release']);old_source=o.raw(authority['old_source']);source=ast.parse(old_source)
    o.need(authority['kind']=='known-verified-navigation-prerequisite-snapshot-gap-v1' and authority['old_expected_navigation']==failure['recheck_navigation']==summary['actual_failure_ref'] and authority['original_navigation_snapshot']['sha256']==summary['actual_reference_now']['sha256'] and original==summary['navigation_current'],'navigation-original-snapshot-authority')
    o.need(cli['returncode']==0 and cli['stderr']=='' and result['kind']=='verified-exact-recheck-pre-input-source-v1' and result['proof']==authority['old_proof'] and result['ui_used']is False and result['historical_index_unchanged']is True and cli['argv'][1:4]==[str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),'recover-exact-recheck-source','--release'] and json.loads(cli['argv'][4])==authority['old_release'] and proof['release']==authority['old_release'] and proof['original_parent']==failure['parent'] and proof['original_engine']==failure['engine'],'navigation-old-successful-admission-receipt')
    target=next(t for t in release['targets']if t['target']==str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'));o.need(target['after']['sha256']==authority['old_source']['sha256']=='bca8ddbd64cd5acb02ac08cc367124b2cf715d6d29f8126176055c098d5d5018','navigation-old-verified-contract-source')
    facts=next(x for x in source.body if isinstance(x,ast.FunctionDef)and x.name=='exact_recheck_facts');recover=next(x for x in source.body if isinstance(x,ast.FunctionDef)and x.name=='recover_exact_recheck_source');o.need("navigation = o.doc(failure['recheck_navigation'])"in ast.unparse(facts) and ast.unparse(recover).index('exact_recheck_facts(initial=True)')<ast.unparse(recover).index('proof = o.immutable'),'navigation-old-precondition-before-proof')
    current=o.doc(o.ref(failure['recheck_navigation']['path']));validate_navigation_append(original,current,o.raw);return original

def navigation_source_facts(archives=(),*,initial=False):
    authority=o.doc(NAVIGATION_INPUT);failure=o.doc(authority['failure']);parent=json.loads(window_material(failure['parent'],archives));engine=json.loads(window_material(failure['engine'],archives));prior=_quality_verify_before_navigation_source(parent,parent[h.FIELD],installed=False);old=prior['exact_recheck_facts'];folder=Path(failure['parent']['path']).parent
    o.need(failure['attempt']==12 and failure['leaf']=='execution-reference-changed' and parent['status']==engine['status']=='hold' and parent['error']==engine['error']==failure['leaf'] and len(parent['calls'])==9 and len(engine['calls'])==110 and parent['calls'][:8]==old['parent']['calls'] and engine['calls'][:109]==old['engine']['calls'],'navigation-fixed-current-hold')
    last=parent['calls'][-1];exit=o.doc(last['result']);launch=o.doc(last['launch']);o.need(last['state']=='returned' and last['result']==failure['child_exit'] and exit['returncode']==0 and exit['stderr']=='' and exit['argv']==last['argv']==launch['argv'] and exit['launch']==last['launch'],'navigation-natural-child8-not-failed-input')
    call=engine['calls'][109];o.need(call['state']=='returned' and call['applied']is True and call['result']==failure['last_engine_call']['result'] and all(c['state']=='returned' and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58,108)),'navigation-no-unknown-actions')
    active=json.loads(window_material(failure['new_index'],archives));manifest=o.doc(failure['new_manifest_from_active']);unit=engine['companies'][0]['artifacts']['unit_artifacts'];o.need(active==failure['new_index_data'] and unit['exact_manifest']==active['manifest']==failure['new_manifest_from_active'] and unit['source']==old['failure']['source'] and unit['acquisition']==old['failure']['acquisition'] and manifest['day']=='2026-10-24' and failure['no_new_exact_operation_present']is True,'navigation-preserve-prepared-current-version')
    refs=[authority['failure'],failure['parent'],failure['engine'],failure['started'],failure['worker_exit'],failure['parent_run_exit'],failure['child_exit'],last['launch'],failure['new_index'],failure['new_manifest_from_active'],call['result']]
    for r in refs:window_material(r,archives)
    if initial:
        for r in(failure['parent'],failure['engine'],failure['new_index'],authority['current_ledger']):o.need(o.ref(r['path'])==r,'navigation-original-CAS')
        o.need(not Path(failure['new_manifest_from_active']['path']).with_name('operation.json').exists(),'navigation-no-input-before-repair')
    return {'failure':failure,'parent':parent,'engine':engine,'folder':str(folder),'prior':prior,'fixed':refs,'input':authority}

def navigation_source_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');rels=('review_capture_focus.py',);paths={str(ROOT/'skills/negative-review-complaints/scripts'/n)for n in rels};targets=release['targets'];previous_release=o.doc(o.doc(NAVIGATION_INPUT)['old_proof'])['release']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous_release==policy['previous_release'] and release['navigation_recovery_input']==NAVIGATION_INPUT==policy['navigation_recovery_input'] and policy['kind']=='finite-reviewed-navigation-lifecycle-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'navigation-source-reviewed-release-input')
    o.need(len(targets)==2 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==1 and {t['target']for t in policy['targets']}==paths,'navigation-source-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']==old and t['old_sha256']==(old['sha256']if old else None),'navigation-source-exact-source-CAS')
        if old:o.need(pt['archive']['sha256']==old['sha256'],'navigation-source-before-data-hash');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(Path(t['target']).name=='legacy_alias_catalogue_result_wait_v1.json' and pt['archive']is None,'navigation-source-only-new-catalogue');codes.append({'path':t['target'],'sha256':t['after']['sha256']})
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def navigation_source_pair(parent,engine,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in(parent,engine):error=value.pop('error');value.update(status='running',**{NAVIGATION_FIELD:proof});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof})
    return parent,engine

def verify_navigation_source(current,oldproof,*,installed=True):
    proof=current[NAVIGATION_FIELD];p=o.doc(proof);facts=navigation_source_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.recheck-navigation-source'/facts['failure']['parent']['sha256'];o.need(p['kind']==NAVIGATION_KIND and p['ui_used']is False and Path(proof['path'])==base/'proof.json' and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'navigation-source-canonical-proof')
    expected,_=navigation_source_pair(facts['parent'],facts['engine'],proof);o.need(current['calls'][:9]==facts['parent']['calls'] and current.get('resolved_errors')==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD)),'navigation-source-preserved-original')
    codes=navigation_source_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'navigation-source-effective-graph');return {**facts['prior'],'code_refs':codes,'failed_calls':facts['prior']['failed_calls'],'navigation_source_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[x['archive']for x in p['archives']]]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    if current.get(NAVIGATION_FIELD):return verify_navigation_source(current,oldproof,installed=installed)
    return _quality_verify_before_navigation_source(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if not(engine.get(NAVIGATION_FIELD)or current.get(NAVIGATION_FIELD)):return _panel_engine_before_navigation_source(engine)
    o.need(engine.get(NAVIGATION_FIELD)==current.get(NAVIGATION_FIELD) and engine.get(NAVIGATION_FIELD)is not None,'navigation-source-parent-engine-proof');admitted=verify_navigation_source(current,engine[h.FIELD]);facts=admitted['navigation_source_facts'];expected=navigation_source_pair(facts['parent'],facts['engine'],engine[NAVIGATION_FIELD])[1];o.need(engine['calls'][:110]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'] and all(engine[k]==current[k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD)),'navigation-source-preserved-engine');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58,108)]

def recover_navigation_source(release_ref):
    failure=o.doc(o.doc(NAVIGATION_INPUT)['failure']);folder=Path(failure['parent']['path']).parent;base=folder/'.recheck-navigation-source'/failure['parent']['sha256']
    with(folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'navigation-source-same-release')
        else:
            facts=navigation_source_facts(initial=True);codes=navigation_source_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((failure['parent'],failure['engine'],failure['new_index'],o.doc(NAVIGATION_INPUT)['current_ledger']))];p={'kind':NAVIGATION_KIND,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=navigation_source_facts(p['archives']);parent,engine=navigation_source_pair(facts['parent'],facts['engine'],proof)
        for dest,old,new in((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in(old,new),'navigation-source-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_navigation_source(parent,parent[h.FIELD]);return {'kind':NAVIGATION_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'prepared_current_index_unchanged':o.ref(failure['new_index']['path'])==failure['new_index'],'ui_used':False}

CONFIRM_ANCHOR_FIELD='company_confirm_anchor_source'
CONFIRM_ANCHOR_KIND='verified-company-confirm-anchor-source-v1'
CONFIRM_ANCHOR_INPUT={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-confirm-anchor-path-candidate/confirm-anchor-recovery-input.json', 'sha256': '4ed4dc9d028c10cfd715cb8917774f98da729ebd4ecd798efc232219d8c80bdb'}
_quality_verify_before_confirm_anchor_source=verify_current_quality_source
_panel_engine_before_confirm_anchor_source=panel_engine_calls

def confirm_anchor_source_facts(archives=(),*,initial=False):
    import ast
    authority=o.doc(CONFIRM_ANCHOR_INPUT);failure=o.doc(authority['failure']);parent=json.loads(window_material(failure['parent'],archives));engine=json.loads(window_material(failure['engine'],archives));workflow=json.loads(window_material(failure['workflow'],archives));prior=_quality_verify_before_confirm_anchor_source(parent,parent[h.FIELD],installed=False);old=prior['navigation_source_facts'];folder=Path(failure['parent']['path']).parent
    o.need(failure['attempt']==13 and failure['leaf']=='read-recovery-anchor-canonical-tree' and parent['status']==engine['status']=='hold' and parent['error']=='execution-child-stopped' and engine['error']==failure['leaf'] and len(parent['calls'])==10 and len(engine['calls'])==135 and parent['calls'][:9]==old['parent']['calls'] and engine['calls'][:110]==old['engine']['calls'],'confirm-anchor-fixed-hold')
    call=parent['calls'][-1];exit=o.doc(call['result']);launch=o.doc(call['launch']);o.need(call['state']=='returned' and call['result']==failure['last_child_exit'] and exit['returncode']==2 and exit['stderr']=='' and exit['argv']==call['argv']==launch['argv'] and exit['launch']==call['launch'] and json.loads(exit['stdout'])=={'ok':False,'error':failure['leaf']},'confirm-anchor-exact-child9')
    o.need(engine['calls'][134]==authority['failed_engine_call'] and all(c['state']=='returned'and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134)),'confirm-anchor-no-unknown-parent-prefix')
    o.need(workflow['phase']==failure['workflow_phase']=='verifySwitch' and workflow['revision']==failure['workflow_revision']==5 and workflow['calls']==failure['workflow_calls'] and len(workflow['calls'])==4 and all(x['state']=='confirmed'for x in workflow['calls']) and workflow['last_tree']==failure['last_tree'] and workflow['last_error']==failure['last_error'] and workflow['company_switch_wait_started']==failure['original_wait_started'],'confirm-anchor-confirmed-workflow-prefix')
    tree=o.doc(failure['last_tree']);scope=o.doc(failure['scope']);o.need(scope['tree']==tree and scope['before']==scope['after'] and scope['commands']==failure['scope_commands'] and scope['commands']==[{'op':'tabs'},{'op':'ping','tabId':workflow['tab_id']},{'op':'tree','tabId':workflow['tab_id']},{'op':'tabs'}] and failure['scope_tree_equals_last_tree_data']is True and failure['scope_before_equals_after']is True and failure['expected_tree_exists']is False,'confirm-anchor-exact-immutable-scope')
    before=[r for r in failure['source_code']if r['path'].endswith('/switch_read_recovery.py')];o.need(len(before)==1 and before[0]['sha256']=='67993fc900f1be5a0805ed24f047611699b28d40016bcd0d7f76af2a38f95d7b','confirm-anchor-fixed-helper-before');code=ast.parse(quality_original_code(before[0]));fn=next(x for x in code.body if isinstance(x,ast.FunctionDef)and x.name=='saved_active_window_anchor');o.need('read-recovery-anchor-canonical-tree'in ast.unparse(fn),'confirm-anchor-known-before-dispatch-guard')
    refs=[authority['failure'],failure['parent'],failure['engine'],failure['workflow'],failure['job'],failure['last_tree'],failure['scope'],failure['started'],failure['worker_exit'],failure['parent_run_exit'],failure['last_child_exit'],call['launch'],failure['yantai_three_rechecks_progress']]
    for r in refs:window_material(r,archives)
    if initial:
        for r in(failure['parent'],failure['engine'],failure['workflow'],*authority['protected_ledgers']):o.need(o.ref(r['path'])==r,'confirm-anchor-original-CAS')
    return {'failure':failure,'parent':parent,'engine':engine,'workflow':workflow,'folder':str(folder),'prior':prior,'fixed':refs,'input':authority}

def confirm_anchor_source_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');paths={str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/douyin-laike-operator/scripts/switch_read_recovery.py')};targets=release['targets'];previous_release=o.doc(o.doc(CONFIRM_ANCHOR_INPUT)['previous_source_proof'])['release']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous_release==policy['previous_release'] and release['confirm_anchor_recovery_input']==CONFIRM_ANCHOR_INPUT==policy['confirm_anchor_recovery_input'] and policy['kind']=='finite-reviewed-confirm-anchor-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'navigation-source-reviewed-release-input')
    o.need(len(targets)==3 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==2 and {t['target']for t in policy['targets']}==paths,'navigation-source-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']==old and t['old_sha256']==(old['sha256']if old else None),'navigation-source-exact-source-CAS')
        if old:o.need(pt['archive']['sha256']==old['sha256'],'navigation-source-before-data-hash');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(Path(t['target']).name=='legacy_alias_catalogue_result_wait_v1.json' and pt['archive']is None,'navigation-source-only-new-catalogue');codes.append({'path':t['target'],'sha256':t['after']['sha256']})
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def confirm_anchor_source_pair(parent,engine,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in(parent,engine):error=value.pop('error');value.update(status='running',**{CONFIRM_ANCHOR_FIELD:proof});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof})
    return parent,engine

def verify_confirm_anchor_source(current,oldproof,*,installed=True):
    proof=current[CONFIRM_ANCHOR_FIELD];p=o.doc(proof);facts=confirm_anchor_source_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.confirm-anchor-source'/facts['failure']['parent']['sha256'];o.need(p['kind']==CONFIRM_ANCHOR_KIND and p['ui_used']is False and Path(proof['path'])==base/'proof.json' and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'navigation-source-canonical-proof')
    expected,_=confirm_anchor_source_pair(facts['parent'],facts['engine'],proof);o.need(current['calls'][:10]==facts['parent']['calls'] and current.get('resolved_errors')==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD,NAVIGATION_FIELD)),'navigation-source-preserved-original')
    codes=confirm_anchor_source_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'navigation-source-effective-graph');return {**facts['prior'],'code_refs':codes,'failed_calls':[*facts['prior']['failed_calls'],facts['parent']['calls'][-1]],'confirm_anchor_source_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[x['archive']for x in p['archives']]]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    if current.get(CONFIRM_ANCHOR_FIELD):return verify_confirm_anchor_source(current,oldproof,installed=installed)
    return _quality_verify_before_confirm_anchor_source(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if not(engine.get(CONFIRM_ANCHOR_FIELD)or current.get(CONFIRM_ANCHOR_FIELD)):return _panel_engine_before_confirm_anchor_source(engine)
    o.need(engine.get(CONFIRM_ANCHOR_FIELD)==current.get(CONFIRM_ANCHOR_FIELD) and engine.get(CONFIRM_ANCHOR_FIELD)is not None,'navigation-source-parent-engine-proof');admitted=verify_confirm_anchor_source(current,engine[h.FIELD]);facts=admitted['confirm_anchor_source_facts'];expected=confirm_anchor_source_pair(facts['parent'],facts['engine'],engine[CONFIRM_ANCHOR_FIELD])[1];o.need(engine['calls'][:135]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'] and all(engine[k]==current[k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD,NAVIGATION_FIELD)),'navigation-source-preserved-engine');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134)]

def recover_confirm_anchor_source(release_ref):
    failure=o.doc(o.doc(CONFIRM_ANCHOR_INPUT)['failure']);folder=Path(failure['parent']['path']).parent;base=folder/'.confirm-anchor-source'/failure['parent']['sha256']
    with(folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'navigation-source-same-release')
        else:
            facts=confirm_anchor_source_facts(initial=True);codes=confirm_anchor_source_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((failure['parent'],failure['engine'],failure['workflow']))];p={'kind':CONFIRM_ANCHOR_KIND,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=confirm_anchor_source_facts(p['archives']);parent,engine=confirm_anchor_source_pair(facts['parent'],facts['engine'],proof)
        for dest,old,new in((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in(old,new),'navigation-source-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_confirm_anchor_source(parent,parent[h.FIELD]);return {'kind':CONFIRM_ANCHOR_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'workflow_unchanged':o.ref(failure['workflow']['path'])==failure['workflow'],'ui_used':False}

UNICODE_READ_FIELD='readonly_unicode_source'
UNICODE_READ_KIND='verified-readonly-unicode-source-v1'
UNICODE_READ_INPUT={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/bridge-unicode-json-candidate/unicode-recovery-input.json', 'sha256': 'b0a2483ca6954505cf9f6bc84eef53eec7d4e0effa8dc16617b34fb86a05de23'}
_quality_verify_before_unicode_read_source=verify_current_quality_source
_panel_engine_before_unicode_read_source=panel_engine_calls

def unicode_read_source_facts(archives=(),*,initial=False):
    import ast
    authority=o.doc(UNICODE_READ_INPUT);failure=o.doc(authority['failure']);parent=json.loads(window_material(failure['parent'],archives));engine=json.loads(window_material(failure['engine'],archives));workflow=json.loads(window_material(failure['workflow'],archives));prior=_quality_verify_before_unicode_read_source(parent,parent[h.FIELD],installed=False);old=prior['confirm_anchor_source_facts'];folder=Path(failure['parent']['path']).parent
    error="bridge-command-failed: 'utf-8' codec can't encode character '\\ud83c' in position 262142: surrogates not allowed"
    o.need(failure['attempt']==14 and failure['leaf']==error and parent['status']==engine['status']=='hold' and parent['error']=='execution-child-stopped' and engine['error']==error and len(parent['calls'])==11 and len(engine['calls'])==141 and parent['calls'][:10]==old['parent']['calls'] and engine['calls'][:135]==old['engine']['calls'],'unicode-read-fixed-hold')
    call=parent['calls'][-1];exit=o.doc(call['result']);launch=o.doc(call['launch']);o.need(call['state']=='returned' and call['result']==failure['last_child_exit'] and exit['returncode']==2 and exit['stderr']=='' and exit['argv']==call['argv']==launch['argv'] and exit['launch']==call['launch'] and json.loads(exit['stdout'])=={'ok':False,'error':failure['leaf']},'unicode-read-exact-child10')
    o.need(engine['calls'][140]==authority['failed_engine_call'] and all(c['state']=='returned'and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134,140)),'unicode-read-no-unknown-prefix')
    o.need(workflow['phase']==failure['phase']=='readReviewFilters' and workflow['revision']==failure['revision']==11 and workflow['calls']==failure['workflow_calls'] and len(workflow['calls'])==7 and all(x['state']=='confirmed'for x in workflow['calls']) and workflow['calls'][:4]==old['workflow']['calls'] and workflow['last_tree']==failure['last_tree'] and workflow['last_error']==failure['last_error'] and failure['no_new_phase11_tree_or_scope']is True,'unicode-read-confirmed-workflow-prefix')
    job=o.doc(failure['job']);o.need(job['workflow_path']==failure['workflow']['path'] and job['work_order_path']==failure['job']['path'] and workflow['phase'] not in('verifySwitch','searchCompany'),'unicode-read-original-job-readonly-phase')
    bridge=next(r for r in failure['source_code']if r['path'].endswith('/bridge.py'));tree=ast.parse(quality_original_code(bridge));reply=next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='reply');o.need('ensure_ascii=False' in ast.unparse(reply) and '.encode()' in ast.unparse(reply),'unicode-read-known-json-encoding-before-response')
    refs=[authority['failure'],failure['parent'],failure['engine'],failure['workflow'],failure['job'],failure['last_tree'],failure['started'],failure['worker_exit'],failure['parent_run_exit'],failure['last_child_exit'],call['launch'],failure['switch_read_recovery'],failure['confirmed_switch_recovery'],*failure['bridge_timing_refs']]
    for r in refs:window_material(r,archives)
    if initial:
        for r in(failure['parent'],failure['engine'],failure['workflow'],*authority['protected_ledgers']):o.need(o.ref(r['path'])==r,'unicode-read-original-CAS')
    return {'failure':failure,'parent':parent,'engine':engine,'workflow':workflow,'folder':str(folder),'prior':prior,'fixed':refs,'input':authority}

def unicode_read_source_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');paths={str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/chrome-dom-export/scripts/bridge.py'),str(ROOT/'skills/douyin-laike-operator/scripts/role_cli.py'),str(ROOT/'skills/chrome-dom-export/scripts/bridge-service.py')};targets=release['targets'];previous_release=o.doc(o.doc(UNICODE_READ_INPUT)['previous_source_proof'])['release']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==previous_release==policy['previous_release'] and release['unicode_recovery_input']==UNICODE_READ_INPUT==policy['unicode_recovery_input'] and policy['kind']=='finite-reviewed-readonly-unicode-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'navigation-source-reviewed-release-input')
    o.need(len(targets)==5 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==4 and {t['target']for t in policy['targets']}==paths,'navigation-source-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target'] not in paths:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']==old and t['old_sha256']==(old['sha256']if old else None),'navigation-source-exact-source-CAS')
        if old:o.need(pt['archive']['sha256']==old['sha256'],'navigation-source-before-data-hash');o.raw(pt['archive']);codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(Path(t['target']).name=='legacy_alias_catalogue_result_wait_v1.json' and pt['archive']is None,'navigation-source-only-new-catalogue');codes.append({'path':t['target'],'sha256':t['after']['sha256']})
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def unicode_read_source_pair(parent,engine,proof):
    parent=copy.deepcopy(parent);engine=copy.deepcopy(engine)
    for value in(parent,engine):error=value.pop('error');value.update(status='running',**{UNICODE_READ_FIELD:proof});value.setdefault('resolved_errors',[]).append({'error':error,'recovery':proof})
    return parent,engine

def verify_unicode_read_source(current,oldproof,*,installed=True):
    proof=current[UNICODE_READ_FIELD];p=o.doc(proof);facts=unicode_read_source_facts(p['archives']);folder=Path(facts['folder']);base=folder/'.readonly-unicode-source'/facts['failure']['parent']['sha256'];o.need(p['kind']==UNICODE_READ_KIND and p['ui_used']is False and Path(proof['path'])==base/'proof.json' and p['original_parent']==facts['failure']['parent'] and p['original_engine']==facts['failure']['engine'] and all(Path(a['archive']['path']).parent==base/'archives'for a in p['archives']),'navigation-source-canonical-proof')
    expected,_=unicode_read_source_pair(facts['parent'],facts['engine'],proof);o.need(current['calls'][:11]==facts['parent']['calls'] and current.get('resolved_errors')==expected['resolved_errors'] and all(current.get(k)==v for k,v in o.doc(current['origin_ref']).items()) and all(current[k]==facts['parent'][k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD,NAVIGATION_FIELD,CONFIRM_ANCHOR_FIELD)),'navigation-source-preserved-original')
    codes=unicode_read_source_tip(facts['prior'],p['release'],installed=installed);o.need(p['code_refs']==codes,'navigation-source-effective-graph');return {**facts['prior'],'code_refs':codes,'failed_calls':[*facts['prior']['failed_calls'],facts['parent']['calls'][-1]],'unicode_read_source_facts':facts,'evidence':[*facts['prior']['evidence'],proof,p['release'],*[x['archive']for x in p['archives']]]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    if current.get(UNICODE_READ_FIELD):return verify_unicode_read_source(current,oldproof,installed=installed)
    return _quality_verify_before_unicode_read_source(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'))
    if not(engine.get(UNICODE_READ_FIELD)or current.get(UNICODE_READ_FIELD)):return _panel_engine_before_unicode_read_source(engine)
    o.need(engine.get(UNICODE_READ_FIELD)==current.get(UNICODE_READ_FIELD) and engine.get(UNICODE_READ_FIELD)is not None,'navigation-source-parent-engine-proof');admitted=verify_unicode_read_source(current,engine[h.FIELD]);facts=admitted['unicode_read_source_facts'];expected=unicode_read_source_pair(facts['parent'],facts['engine'],engine[UNICODE_READ_FIELD])[1];o.need(engine['calls'][:141]==facts['engine']['calls'] and engine['resolved_errors']==expected['resolved_errors'] and all(engine[k]==current[k]for k in(h.FIELD,h.PLAN_FIELD,WINDOW_SOURCE_FIELD,QUALITY_CURRENT_FIELD,EMPTY_RESULT_FIELD,EXACT_RECHECK_FIELD,NAVIGATION_FIELD,CONFIRM_ANCHOR_FIELD)),'navigation-source-preserved-engine');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134,140)]

def recover_unicode_read_source(release_ref):
    failure=o.doc(o.doc(UNICODE_READ_INPUT)['failure']);folder=Path(failure['parent']['path']).parent;base=folder/'.readonly-unicode-source'/failure['parent']['sha256']
    with(folder/'launcher.lock').open('a')as a,(folder/'engine.lock').open('a')as b:
        for lock in(a,b):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        path=base/'proof.json'
        if path.exists():proof=o.ref(path);p=o.doc(proof);o.need(p['release']==release_ref,'navigation-source-same-release')
        else:
            facts=unicode_read_source_facts(initial=True);codes=unicode_read_source_tip(facts['prior'],release_ref,installed=True);base.mkdir(parents=True,exist_ok=True);archives=[{'original':r,'archive':h.immutable_bytes(base/'archives'/(str(n)+'-'+Path(r['path']).name),o.raw(r))}for n,r in enumerate((failure['parent'],failure['engine'],failure['workflow']))];p={'kind':UNICODE_READ_KIND,'original_parent':failure['parent'],'original_engine':failure['engine'],'archives':archives,'release':release_ref,'code_refs':codes,'ui_used':False,'at':stamp()};proof=o.immutable(path,p)
        facts=unicode_read_source_facts(p['archives']);parent,engine=unicode_read_source_pair(facts['parent'],facts['engine'],proof)
        for dest,old,new in((folder/'engine.json',facts['engine'],engine),(folder/'launcher.json',facts['parent'],parent)):
            value=o.doc(o.ref(dest));o.need(value in(old,new),'navigation-source-partial-CAS-conflict')
            if value==old:previous.overlay.rc.atomic(dest,new)
        verify_unicode_read_source(parent,parent[h.FIELD]);return {'kind':UNICODE_READ_KIND,'proof':proof,'parent':o.ref(folder/'launcher.json'),'engine':o.ref(folder/'engine.json'),'workflow_unchanged':o.ref(failure['workflow']['path'])==failure['workflow'],'ui_used':False}


COMPLETED_REPORT_INPUT={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/complaint-completed-report-membership-candidate/completed-report-input.json', 'sha256': '0bdf0e3738092255da8eb4e7c8c99b3a8d2cfcc5992ef37197c80b405f9293c2'}
_completed_verify_before_report=verify_current_quality_source
_completed_engine_before_report=panel_engine_calls

def completed_report_facts():
    authority=o.doc(COMPLETED_REPORT_INPUT);failure=o.doc(authority['failure']);parent=o.doc(authority['parent']);engine=o.doc(authority['engine']);final=o.doc(authority['completion']);request=o.doc(authority['request']);exit=o.doc(failure['worker_exit']);natural=o.doc(failure['parent_run_exit']);prior=_completed_verify_before_report(parent,parent[h.FIELD],installed=False)
    o.need(failure['attempt']==15 and failure['leaf']=='execution-final-child-returncode' and failure['parent']==authority['parent'] and failure['engine']==authority['engine'] and failure['completion']==authority['completion'] and parent['status']==engine['status']=='complete' and engine['phase']=='finish' and len(parent['calls'])==12 and len(engine['calls'])==192,'completed-report-fixed-complete')
    o.need(final['engine']==authority['engine'] and final['proof']==engine['completion'] and final['order']==parent['order']==request['context']['order'] and final['start_monotonic']==parent['start_monotonic'] and final['end_monotonic']==parent['end_monotonic'] and final['completed_at']==parent['wall_ended_at'],'completed-report-original-completion')
    o.need(request['task']['id']==failure['task_id']=='task-e851f61b8d7642391ec23524' and request['task']['day']=='2026-10-24' and request['attempt_id'].endswith('-15') and exit['request']==authority['request'] and exit['returncode']==1 and exit['response']is None and 'execution-final-child-returncode' in o.raw(exit['stderr']).decode() and natural['returncode']==0 and not o.raw(natural['stderr']),'completed-report-natural-only-report-failure')
    output=json.loads(o.raw(natural['stdout']));o.need(output['status']=='complete' and output['completion']==authority['completion'] and output['order']==parent['order'] and output['last_child_receipt']==parent['calls'][-1]['result'],'completed-report-natural-completed-parent-output')
    expected=[parent['calls'][i]for i in(0,1,6,7,9,10)];o.need(prior['failed_calls']==expected and all(c['state']=='returned' for c in parent['calls']) and all(c['state']=='returned'and c.get('applied')is True for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134,140)),'completed-report-exact-admitted-history')
    return {'authority':authority,'failure':failure,'parent':parent,'engine':engine,'prior':prior,'request':request}

def completed_report_source_tip(prior,release_ref,*,installed):
    release=o.doc(release_ref);policy=o.doc(release['source_repair_dependency_delta']);paths={str(ROOT/'skills/negative-review-complaints/scripts/review_capture_focus.py'),str(ROOT/'skills/workshop-director/scripts/complaint_execution_orchestration.py'),str(ROOT/'packages/workshop-director/workshop_director/adapters.py')};helper=str(ROOT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');previous=o.doc(o.doc(COMPLETED_REPORT_INPUT)['previous_source_proof'])['release'];targets=release['targets']
    o.need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release['previous_release']==policy['previous_release']==previous and release['completed_report_input']==COMPLETED_REPORT_INPUT==policy['completed_report_input'] and policy['kind']=='finite-reviewed-completed-report-dependency-delta-v1' and policy['authorization_release']==release['source_repair_authorization_release'],'completed-report-exact-reviewed-release')
    o.need(len(targets)==4 and {t['target']for t in targets}==paths|{helper} and len(policy['targets'])==3 and {t['target']for t in policy['targets']}==paths,'completed-report-finite-source-set');codes=copy.deepcopy(prior['code_refs'])
    for t in targets:
        o.raw(t['after'])
        if t['target']==helper:continue
        pt=next(x for x in policy['targets']if x['target']==t['target']);old=next((r for r in codes if r['path']==t['target']),None);o.need(pt['after']==t['after'] and pt['before']['path']==t['target'] and t['old_sha256']==pt['before']['sha256']==pt['archive']['sha256'],'completed-report-exact-source-CAS');o.raw(pt['archive'])
        if old:o.need(pt['before']==old,'completed-report-parent-logical-before');codes[codes.index(old)]={'path':t['target'],'sha256':t['after']['sha256']}
        else:o.need(t['target']==str(ROOT/'packages/workshop-director/workshop_director/adapters.py'),'completed-report-only-adapter-outside-parent-graph')
    if installed:
        for r in codes:o.raw(r)
        for t in targets:o.raw({'path':t['target'],'sha256':t['after']['sha256']})
    return codes

def completed_report_effective_graph(codes,original_release):
    # Historical completed data is verified at its own immutable release first.
    # Only the existing reviewed Root chain may select current implementations;
    # Root-only dependencies are not added to the complaint execution graph.
    import importlib
    sys.path.insert(0,str(ROOT/'skills/violation-notifier/scripts'));r=importlib.import_module('violation_reboot_continuation');authorization=o.doc(original_release)['source_repair_authorization_release'];current=r.dependency_release(authorization);_,_,mapping=r.source_release(current);result=[mapping.get(v['path'],v)for v in codes]
    for ref in result:o.raw(ref)
    return result,current

def completed_report_source_admission(current,oldproof,*,installed=True):
    facts=completed_report_facts();o.need(current==facts['parent'] and current[h.FIELD]==current[h.PLAN_FIELD]==oldproof,'completed-report-original-parent-immutable');release=o.ref(ROOT/'work/performance-audit/complaint-completed-report-membership-candidate/supervisor-release.json');codes=completed_report_source_tip(facts['prior'],release,installed=False)
    selected=release
    if installed:codes,selected=completed_report_effective_graph(codes,release)
    return {**facts['prior'],'code_refs':codes,'completed_report_facts':facts,'evidence':[*facts['prior']['evidence'],COMPLETED_REPORT_INPUT,release,selected,facts['authority']['failure'],facts['authority']['parent'],facts['authority']['engine'],facts['authority']['completion'],facts['authority']['request']]}

def verify_current_quality_source(current,oldproof,*,installed=True):
    authority=o.doc(COMPLETED_REPORT_INPUT)
    if current.get('status')=='complete' and current.get('order')==o.doc(authority['parent'])['order']:return completed_report_source_admission(current,oldproof,installed=installed)
    return _completed_verify_before_report(current,oldproof,installed=installed)

def panel_engine_calls(engine):
    current=o.doc(o.ref(h.phase_directory(engine)/'launcher.json'));authority=o.doc(COMPLETED_REPORT_INPUT)
    if current.get('status')!='complete' or current.get('order')!=o.doc(authority['parent'])['order']:return _completed_engine_before_report(engine)
    admitted=completed_report_source_admission(current,engine[h.FIELD]);facts=admitted['completed_report_facts'];o.need(engine==facts['engine'] and engine[h.FIELD]==engine[h.PLAN_FIELD]==current[h.FIELD]==current[h.PLAN_FIELD],'completed-report-original-engine-immutable');return [c for i,c in enumerate(engine['calls'])if i not in(43,44,58,108,134,140)]

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['recover','recover-native-stage','recover-postguard','recover-observation','admit-quality','quality-response','recover-shortcut','recover-recheck-tab','recover-normal-profile','recover-switch-anchor','recover-page-window-focus','recover-window-source','admit-current-quality-source','current-quality-response','recover-empty-result-source','recover-exact-recheck-source','recover-navigation-source','recover-confirm-anchor-source','recover-unicode-read-source']);
    for n in ('parent','engine','activation','focus','observation','worker','release','before-source','region','post','handoff','workshop','operator','scope','transport','page'):parser.add_argument('--'+n)
    parser.add_argument('--old-source',action='append');a=parser.parse_args()
    try:
        if a.action=='recover-unicode-read-source':result=recover_unicode_read_source(json.loads(a.release))
        elif a.action=='recover-confirm-anchor-source':result=recover_confirm_anchor_source(json.loads(a.release))
        elif a.action=='recover-navigation-source':result=recover_navigation_source(json.loads(a.release))
        elif a.action=='recover-exact-recheck-source':result=recover_exact_recheck_source(json.loads(a.release))
        elif a.action=='recover-empty-result-source':result=recover_empty_result_source(json.loads(a.release))
        elif a.action=='admit-current-quality-source':result=admit_current_quality_source(json.loads(a.release))
        elif a.action=='current-quality-response':result=current_quality_response(json.loads(a.parent),json.loads(a.workshop))
        elif a.action=='recover-window-source':result=recover_window_source(json.loads(a.release))
        elif a.action=='recover-page-window-focus':result=recover_panel(json.loads(a.release))
        elif a.action=='recover-switch-anchor':result=recover_anchor(*[json.loads(getattr(a,n)) for n in ('parent','engine','operator','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='recover-normal-profile':result=recover_normal(*[json.loads(getattr(a,n)) for n in ('parent','engine','page','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='recover-recheck-tab':result=recover_recheck(*[json.loads(getattr(a,n)) for n in ('parent','engine','transport','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='recover-shortcut':result=recover_shortcut(*[json.loads(getattr(a,n)) for n in ('parent','engine','operator','scope','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='recover':result=recover(*[json.loads(getattr(a,n)) for n in ('parent','engine','activation','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='admit-quality':result=admit_quality(*[json.loads(getattr(a,n)) for n in ('parent','engine','handoff','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='quality-response':result=quality_response(*[json.loads(getattr(a,n)) for n in ('parent','workshop')])
        elif a.action=='recover-observation':result=recover_observation(*[json.loads(getattr(a,n)) for n in ('parent','engine','region','post','worker','release')],[json.loads(x) for x in a.old_source])
        elif a.action=='recover-postguard':result=recover_postguard(*[json.loads(getattr(a,n)) for n in ('parent','engine','region','worker','release')],[json.loads(x) for x in a.old_source])
        else:result=recover_native(*[json.loads(getattr(a,n)) for n in ('parent','engine','focus','observation','worker','release','before_source')])
        print(json.dumps(result,ensure_ascii=False));return 0
    except Exception as e:print(json.dumps({'ok':False,'error':str(e)}));return 2
if __name__=='__main__':raise SystemExit(main())
