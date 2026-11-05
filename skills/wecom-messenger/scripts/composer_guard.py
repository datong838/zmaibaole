"""Read-only current-composer input guard; deliberately excludes chat history.
No focus, activation, keys, clipboard, scroll or sender state. Unknown menus and
windows fail closed. Experimental: the first live sampling was unavailable at
the menu gate; this scope is not integrated into the sending path.
AXShownMenuUIElement must positively return kAXErrorNoValue
(-25212); AttributeUnsupported (-25205) does NOT prove there is no menu.
"""
import ctypes as C
import time
SCOPE='current-composer-input-guard-v1'
FIELDS=('AXRole','AXTitle','AXDescription','AXValue','AXHelp','AXSubrole','AXIdentifier','AXEnabled','AXURL','AXFilename')
STRUCTURAL={'AXWindow','AXGroup','AXSplitGroup','AXScrollArea','AXTabGroup','AXToolbar'}
LEAVES={'AXButton','AXTextField','AXTextArea','AXStaticText','AXImage','AXTable','AXSplitter','AXScrollBar','AXValueIndicator','AXColumn'}
class GuardError(RuntimeError):pass
def public_attribute(native,element,key):
    """Preserve public AX return status: never confuse failure with nil value.
    Values/attribute strings are released without inspecting arbitrary content.
    Constants are the named values in the local SDK AXError.h.
    """
    name=native.string(key);out=C.c_void_p()
    try:code=native.ax.AXUIElementCopyAttributeValue(element,name,C.byref(out))
    finally:native.cf.CFRelease(name)
    present=bool(out.value)
    if out.value:native.cf.CFRelease(out.value)
    return int(code),present

def capture(native,*,timeout=15,max_nodes=600,max_depth=35,require_focused=False,clock=time.monotonic):
    start=clock();deadline=start+timeout;native.by_path={};native._attribute_batches={};count=0;discovered=0;graph={};childmap={};roles={};reason=None
    result={'ok':True,'pid':native.pid,'bundle_id':'com.tencent.WeWorkMac','read_scope':SCOPE,'history_read':False,'transcript_complete':False,'guard_complete':False,'truncated':True,'window_inventory_complete':False,'menu_state':'unknown','input_ready':False}
    def need(ok,why):
        if not ok:raise GuardError(why)
    def budget(depth=0):
        need(clock()<=deadline,'composer-guard-deadline');need(depth<=max_depth,'composer-guard-depth-limit');need(count+discovered<max_nodes,'composer-guard-node-limit')
    def role(e):
        if e not in roles:roles[e]=native.get(e,'AXRole')
        need(isinstance(roles[e],str) and roles[e],'composer-guard-role-unavailable');return roles[e]
    def children(e,required=False):return native.scoped_array(e,'AXChildren',required) or []
    def same(a,b):return native.same_element(a,b)
    def same_list(a,b):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    def menu_absent():
        code,present=public_attribute(native,native.root,'AXShownMenuUIElement')
        names={-25212:'kAXErrorNoValue',-25205:'kAXErrorAttributeUnsupported',-25204:'kAXErrorCannotComplete',0:'kAXErrorSuccess'}
        evidence={'attribute':'AXShownMenuUIElement','owner':'AXApplication','AX_error':code,'present':present,'result':names.get(code,'unclassified-public-AX-error')}
        result['menu_evidence']=evidence
        need(code==-25212 and present is False,'composer-guard-menu-present' if present else 'composer-guard-menu-state-unavailable')
        return evidence
    def attrs(e,path):
        nonlocal count
        budget(len(path));count+=1;native.by_path[tuple(path)]=e
        values=native.node_attributes(e,FIELDS)
        need(isinstance(values,dict) and all(k in values for k in FIELDS) and values['AXRole']==role(e),'composer-guard-attributes-incomplete')
        node={'path':list(path),'role':values['AXRole'],'children':[]}
        for k in FIELDS[1:]:
            if values[k] is not None and values[k]!='':node[k]=values[k]
        if values.get('__attribute_errors__'):node['optional_attribute_errors']=values['__attribute_errors__']
        return node
    def discover(e,path):
        nonlocal discovered
        budget(len(path));discovered+=1;r=role(e);graph[tuple(path)]=e
        need(r not in ('AXSheet','AXDialog','AXMenu','AXMenuItem','AXMenuBarItem'),'composer-guard-modal-or-menu-present')
        need(r in STRUCTURAL|LEAVES,'composer-guard-control-role-unreviewed:'+r)
        if r not in STRUCTURAL:return
        cs=children(e,True);childmap[tuple(path)]=cs
        for i,child in enumerate(cs):discover(child,path+[i])
    def composer_full(e,path):
        n=attrs(e,path)
        if n['role']=='AXTextArea':need(native.scoped_settable(e,'AXValue'),'composer-guard-editor-not-settable');n['settable']=['AXValue']
        cs=children(e,n['role']=='AXTextArea')
        for i,ch in enumerate(cs):
            child=composer_full(ch,path+[i]);need(child['role'] in ('AXUnknown','AXImage') and child.get('AXSubrole')=='AXTextAttachment' and not child['children'],'composer-guard-attachment-shape-unreviewed');n['children'].append(child)
        return n
    def indicator(e,path,main):
        n=attrs(e,path);need(not same(e,main) and n['role']=='AXWindow' and n.get('AXSubrole')=='AXDialog' and native.get(e,'AXMain') is not True and not any(n.get(k) for k in ('AXTitle','AXValue','AXDescription')),'composer-guard-extra-window-unreviewed');cs=children(e,True);need(len(cs)==1,'composer-guard-extra-window-unreviewed');button=attrs(cs[0],list(path)+[0]);need(button['role']=='AXButton' and button.get('AXIdentifier')=='InputSource' and button.get('AXDescription')=='com.apple.inputmethod.SCIM.ITABC' and button.get('AXEnabled') is True and not button.get('AXValue') and not button.get('AXTitle') and not children(cs[0]),'composer-guard-extra-window-unreviewed');return {'path':list(path),'kind':'observed-system-input-source-indicator'}
    try:
        need(type(require_focused) is bool,'composer-guard-focus-mode-invalid');menu=menu_absent();windows=native.scoped_array(native.root,'AXWindows',True);root_children=children(native.root,True);need(windows,'composer-guard-window-inventory-empty');main=native.value(native.root,'AXMainWindow');need(main is not None,'composer-guard-main-window-unavailable')
        candidates=[w for w in windows if role(w)=='AXWindow' and native.get(w,'AXTitle')=='企业微信' and native.get(w,'AXSubrole')=='AXStandardWindow'];need(len(candidates)==1 and same(candidates[0],main),'composer-guard-main-window-ambiguous');main=candidates[0];paths=[i for i,c in enumerate(root_children) if same(c,main)];need(len(paths)==1,'composer-guard-main-path-unverified');wp=[paths[0]];inventory=[]
        for i,w in enumerate(windows):
            if same(w,main):continue
            candidates=[j for j,c in enumerate(root_children) if same(c,w)];path=[candidates[0]] if len(candidates)==1 else ['AXWindows',i];inventory.append(indicator(w,path,main))
        for e in root_children:
            r=role(e)
            if r=='AXMenuBar':continue # Not proof of closure; explicit app menu status above is required.
            need(any(same(e,w) for w in windows),'composer-guard-root-control-unreviewed:'+r)
        discover(main,wp)
        headers=[(p,e) for p,e in graph.items() if role(e)=='AXButton' and native.get(e,'AXHelp')=='添加群成员'];need(len(headers)==1,'composer-guard-chat-header-ambiguous');info_path,info=headers[0];shell_path=info_path[:-1];direct=childmap.get(shell_path);need(direct is not None,'composer-guard-shell-unavailable');hi=info_path[-1]+1;need(hi<len(direct),'composer-guard-recipient-unavailable');header=direct[hi];need(role(header) in ('AXTextField','AXStaticText'),'composer-guard-recipient-role-unreviewed');header_node=attrs(header,list(shell_path)+( [hi] ));name=header_node.get('AXValue') or header_node.get('AXTitle') or header_node.get('AXDescription');need(isinstance(name,str) and name,'composer-guard-recipient-empty');kind='group' if role(header)=='AXTextField' else 'person';toolbar=[attrs(info,list(info_path))]
        group_info=[(i,e) for i,e in enumerate(direct) if role(e)=='AXButton' and native.get(e,'AXHelp')=='聊天信息']
        if kind=='group':need(len(group_info)==1,'composer-guard-group-info-unverified');toolbar.append(attrs(group_info[0][1],list(shell_path)+[group_info[0][0]]))
        editable=[(p,e) for p,e in graph.items() if p[:len(shell_path)]==shell_path and role(e)=='AXTextArea' and native.scoped_settable(e,'AXValue')];need(len(editable)==1,'composer-guard-editor-ambiguous');cp,editor=editable[0];composer=composer_full(editor,list(cp));window=attrs(main,wp)
        # The same public shape/path is reread; no previous/input-era snapshot is reused.
        need(attrs(header,list(shell_path)+[hi])==header_node,'composer-guard-recipient-changed');need(composer_full(editor,list(cp))==composer,'composer-guard-editor-changed');need(attrs(main,wp)==window,'composer-guard-window-changed');need(same(native.value(native.root,'AXMainWindow'),main) and same_list(windows,native.scoped_array(native.root,'AXWindows',True)) and same_list(root_children,children(native.root,True)),'composer-guard-window-set-changed');need(menu_absent()==menu,'composer-guard-menu-state-changed')
        for path,original_children in childmap.items():
            need(same_list(original_children,children(graph[path],True)),'composer-guard-structure-changed-during-read')
        focused=native.value(native.root,'AXFocusedUIElement');need(focused is not None,'composer-guard-focused-element-unavailable');front=native.get(native.root,'AXFrontmost');need(type(front) is bool,'composer-guard-frontmost-unavailable');focused_composer=same(focused,editor);need(not require_focused or front and focused_composer,'composer-guard-composer-not-focused');budget()
        result.update(guard_complete=True,truncated=False,window_inventory_complete=True,menu_state='positively-no-shown-menu',menu_evidence=menu,window=window,extra_windows=inventory,recipient={'name':name,'kind':kind,'header':header_node},toolbar=toolbar,composer=composer,focus={'frontmost':front,'focused_composer':focused_composer},input_ready=front and focused_composer)
    except (GuardError,RuntimeError) as error:reason=str(error)
    result.update(node_count=count,discovery_node_count=discovered,truncation_reason=reason,read_seconds=clock()-start)
    return result
