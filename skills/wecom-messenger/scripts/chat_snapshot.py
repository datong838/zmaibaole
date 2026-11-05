from main_window import native_main_window
"""Read-only current-chat AX capture. No keyboard, scroll, focus or mutation.
Completeness means all AX-exposed transcript children, never all server history.
"""
import time
FIELDS=('AXTitle','AXDescription','AXValue','AXHelp','AXSubrole','AXURL','AXFilename','AXEnabled')
STRUCTURAL={'AXWindow','AXGroup','AXSplitGroup','AXScrollArea','AXTabGroup','AXToolbar'}
class CaptureError(RuntimeError):pass

def capture(native,timeout=55,max_nodes=16000,max_depth=40,clock=time.monotonic):
    deadline=clock()+timeout;count=0;discovered=0;reason=None;native.by_path={};native._attribute_batches={};graph={};children={};role_cache={};metadata={'read_scope':'current-chat-readonly','transcript_complete':False,'unrelated_regions_omitted':True,'history_scope':'complete AX-exposed transcript; no scrolling/history expansion'}
    def need(ok,why):
        if not ok:raise CaptureError(why)
    def budget(depth=0,discovery=False):
        need(clock()<=deadline,'deadline');need(depth<=max_depth,'depth-limit')
        need(count+discovered<max_nodes,'node-limit')
        if discovery:need(discovered<1500,'discovery-node-limit')
    def role(e):
        if e not in role_cache:role_cache[e]=native.get(e,'AXRole')
        return role_cache[e]
    def array(e,key,required=False):return native.scoped_array(e,key,required)
    def same_list(a,b):return len(a)==len(b) and all(native.same_element(x,y) for x,y in zip(a,b))
    def attrs(e,path,editable=False):
        nonlocal count
        budget(len(path));count+=1;native.by_path[tuple(path)]=e
        keys=('AXRole',)+FIELDS;reader=getattr(native,'node_attributes',None)
        values=reader(e,keys) if callable(reader) else {key:native.get(e,key) for key in keys}
        need(isinstance(values,dict) and all(key in values for key in keys),'node-attributes-incomplete')
        need(isinstance(values['AXRole'],str) and values['AXRole']==role(e),'node-role-changed-during-read')
        row={'path':list(path),'role':values['AXRole'],'children':[]}
        if values.get('__attribute_errors__'):row['optional_attribute_errors']=values['__attribute_errors__']
        for key in FIELDS:
            value=values[key]
            if value is not None and value!='':row[key]=value
        if editable:row['settable']=['AXValue']
        return row
    def discover(e,path):
        nonlocal discovered
        budget(len(path),True);discovered+=1;r=role(e);graph[tuple(path)]=e
        if r not in STRUCTURAL:return
        cs=array(e,'AXChildren',True);children[tuple(path)]=cs
        for i,child in enumerate(cs):discover(child,path+[i])
    def full(e,path):
        r=role(e);row=attrs(e,path)
        cs=array(e,'AXChildren',r in STRUCTURAL|{'AXTable','AXRow','AXCell'}) or []
        row['children']=[full(child,path+[i]) for i,child in enumerate(cs)]
        return row
    root={'path':[],'role':'AXApplication','children':[]}
    try:
        inventory=array(native.root,'AXWindows',True)
        windows=[w for w in inventory if native_main_window(native,w) and (native.get(w,'AXSubrole')=='AXStandardWindow' or len(inventory)==1)]
        need(len(windows)==1,'main-window-ambiguous');window=windows[0]
        main=native.value(native.root,'AXMainWindow');need(native.same_element(main,window),'main-window-unverified')
        root_children=array(native.root,'AXChildren',True);indexes=[i for i,c in enumerate(root_children) if native.same_element(c,window)]
        need(len(indexes)==1,'main-window-path-unverified');wp=[indexes[0]];discover(window,wp)
        headers=[(p,e) for p,e in graph.items() if role(e)=='AXButton' and native.get(e,'AXHelp')=='添加群成员']
        need(len(headers)==1,'chat-header-unavailable');info_path,info=headers[0];shell_path=info_path[:-1];shell=graph[shell_path]
        direct=children.get(shell_path);need(direct is not None,'chat-shell-unavailable')
        hi=info_path[-1]+1;need(hi<len(direct),'recipient-header-unavailable');header=direct[hi]
        need(role(header) in ('AXTextField','AXStaticText'),'recipient-header-unavailable')
        editable=[(p,e) for p,e in graph.items() if p[:len(shell_path)]==shell_path and role(e)=='AXTextArea' and native.scoped_settable(e,'AXValue')]
        need(len(editable)==1,'composer-ambiguous');composer_path,composer=editable[0]
        ancestors=sorted([p for p,e in graph.items() if role(e)=='AXSplitGroup' and composer_path[:len(p)]==p],key=len,reverse=True)
        table_path=None;table=None
        for parent in ancestors:
            tables=[(p,e) for p,e in graph.items() if role(e)=='AXTable' and p[:len(parent)]==parent]
            if tables:
                need(len(tables)==1,'transcript-ambiguous');table_path,table=tables[0];break
        need(table is not None,'transcript-unavailable')
        original_rows=array(table,'AXChildren',True)
        declared=native.get(table,'AXRowCount');rows=array(table,'AXRows')
        actual_rows=[e for e in original_rows if role(e)=='AXRow']
        if declared is not None:need(type(declared) is int and declared==len(actual_rows),'transcript-row-count-mismatch')
        if rows is not None:need(same_list(rows,actual_rows),'transcript-row-set-mismatch')
        kept={tuple(wp):attrs(window,wp),shell_path:attrs(shell,shell_path),info_path:attrs(info,info_path),tuple(shell_path+(hi,)):attrs(header,shell_path+(hi,)),composer_path:full(composer,list(composer_path)),table_path:full(table,list(table_path))}
        kept[composer_path]['settable']=['AXValue']
        # Keep the group-info sibling, but never the recent-conversation list.
        for i,e in enumerate(direct):
            if role(e)=='AXButton' and native.get(e,'AXHelp')=='聊天信息':kept[shell_path+(i,)]=attrs(e,shell_path+(i,))
        for path in list(kept):
            for size in range(1,len(path)):
                parent=path[:size]
                if parent not in kept:kept[parent]=attrs(graph[parent],parent)
        # Ancestor discovery may skip no required content: only transcript/composer
        # are expanded completely; other branches are explicitly outside this scope.
        for path,row in sorted(kept.items(),key=lambda item:len(item[0]),reverse=True):
            if path[:-1] in kept:kept[path[:-1]]['children'].append(row)
        for row in kept.values():row['children'].sort(key=lambda n:n['path'])
        root['children']=[kept[tuple(wp)]]
        need(native.same_element(native.value(native.root,'AXMainWindow'),window),'main-window-changed')
        need(same_list(original_rows,array(table,'AXChildren',True)),'transcript-changed-during-read')
        if rows is not None:need(same_list(rows,array(table,'AXRows',True)),'transcript-rows-changed-during-read')
        need(native.get(table,'AXRowCount')==declared,'transcript-count-changed-during-read')
        for element,path in [(header,shell_path+(hi,)),(composer,composer_path)]:
            saved=kept[path]
            for key in ('AXValue','AXTitle','AXDescription'):
                need((native.get(element,key) or '')==(saved.get(key) or ''),'chat-header-or-composer-changed')
        need(native.scoped_settable(composer,'AXValue'),'composer-changed')
        budget();metadata.update(transcript_complete=True,transcript_rows=len(actual_rows),declared_row_count=declared)
    except (CaptureError,RuntimeError) as error:reason=str(error)
    return {'ok':True,'bundle_id':'com.tencent.WeWorkMac','pid':native.pid,'tree':root,'node_count':count,'discovery_node_count':discovered,'truncated':reason is not None,'truncation_reason':reason,**metadata}
