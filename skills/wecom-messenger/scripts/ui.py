"""Deterministic semantic selectors for the observed WeCom macOS AX layout."""
from main_window import snapshot_main_window,dialog_parts

class UIError(RuntimeError):pass

def nodes(root):
    yield root
    for child in root.get('children',[]):yield from nodes(child)

def only(items,code):
    if len(items)!=1:raise UIError(code+':'+str(len(items)))
    return items[0]

def value(n):return str(n.get('AXValue') or n.get('AXTitle') or n.get('AXDescription') or '')

def below(n,parent):return n['path'][:len(parent['path'])]==parent['path']

def context(snapshot):
    if not snapshot.get('ok') or snapshot.get('truncated') or snapshot.get('read_scope')=='current-chat-readonly' and snapshot.get('transcript_complete') is not True:raise UIError('ui-tree-incomplete')
    all_nodes=list(nodes(snapshot['tree']))
    windows=[n for n in all_nodes if snapshot_main_window(n)]
    window=only(windows,'main-window-ambiguous')
    if window.get('AXSubrole')=='AXDialog' and len([n for n in all_nodes if n['role']=='AXWindow'])!=1:raise UIError('main-dialog-extra-window')
    pool=[n for n in all_nodes if below(n,window)]
    info=only([n for n in pool if n['role']=='AXButton' and n.get('AXHelp')=='添加群成员'],'chat-header-unavailable')
    shell=only([n for n in pool if n['path']==info['path'][:-1]],'chat-shell-unavailable')
    direct=shell.get('children',[])
    # Semantic sibling of the known header action; never confuse search text with a name.
    header=only([n for n in direct if n['path'][-1]==info['path'][-1]+1 and n['role'] in ('AXTextField','AXStaticText') and value(n)],'recipient-header-ambiguous')
    group=header['role']=='AXTextField'
    if group:
        only([n for n in direct if n.get('AXHelp')=='聊天信息'],'group-info-unverified')
        kind='group'
    else:
        # Person layout must have a real direct header, not absence of a group marker alone.
        kind='person'
    editable=[n for n in pool if below(n,shell) and n['role']=='AXTextArea' and 'AXValue' in n.get('settable',[])]
    composer=only(editable,'composer-ambiguous')
    # The transcript is the table in the smallest composer ancestor containing a table.
    ancestors=sorted([n for n in pool if n['role']=='AXSplitGroup' and below(composer,n)],key=lambda n:len(n['path']),reverse=True)
    transcript=None
    for ancestor in ancestors:
        tables=[n for n in pool if n['role']=='AXTable' and below(n,ancestor)]
        if tables:transcript=only(tables,'transcript-ambiguous');break
    if transcript is None:raise UIError('transcript-unavailable')
    return {'name':value(header),'kind':kind,'header':header,'shell':shell,'composer':composer,'transcript':transcript,'pool':pool,'window':window}

def startup_context(snapshot):
    """A complete empty main shell is navigation-only, never a chat context."""
    if snapshot.get('ok') is not True or snapshot.get('truncated') is not False or snapshot.get('read_scope')!='application-windows-complete':raise UIError('startup-complete-window-snapshot-required')
    all_nodes=list(nodes(snapshot['tree']));windows=[n for n in all_nodes if n.get('role') in ('AXWindow','AXDialog','AXSheet')]
    window=only(windows,'startup-single-main-window-required');parts=dialog_parts(window)
    if parts is None:raise UIError('startup-main-shell-unverified')
    pool=[n for n in all_nodes if below(n,window)]
    preview_tables=[parts['conversation_list']]+[c for c in parts['sidebar'].get('children',[]) if c.get('role')=='AXTable']
    def preview(n):return any(below(n,table) for table in preview_tables) and 'AXValue' not in n.get('settable',[])
    if any((n.get('role')=='AXTextArea' or n.get('AXHelp') in ('添加群成员','聊天信息')) and not preview(n) for n in pool):raise UIError('startup-not-empty-chat-shell')
    shell=parts['shell'];search=only([n for n in shell.get('children',[]) if n.get('role')=='AXTextField' and 'AXValue' in n.get('settable',[])],'startup-search-field-ambiguous')
    return {'navigation_only':True,'name':None,'kind':None,'window':window,'shell':shell,'header':None,'composer':None,'transcript':None,'pool':pool,'search':search}

def startup_rejection_summary(snapshot):
    """Metadata from the already-read snapshot; never values, titles or messages."""
    all_nodes=list(nodes(snapshot['tree']));windows=[n for n in all_nodes if snapshot_main_window(n)]
    parts=dialog_parts(windows[0]) if len(windows)==1 else None
    tables=[] if parts is None else [('conversation-preview',parts['conversation_list'])]+[('sidebar-preview',c) for c in parts['sidebar'].get('children',[]) if c.get('role')=='AXTable']
    controls=[]
    for n in all_nodes:
        help=n.get('AXHelp');known_help=help if help in ('添加群成员','聊天信息') else None
        if n.get('role')!='AXTextArea' and known_help is None:continue
        controls.append({'path':n.get('path'),'role':n.get('role'),'known_help':known_help,'region':next((label for label,table in tables if below(n,table)),'non-preview'),'value_settable':'AXValue' in n.get('settable',[])})
    return {'kind':'startup-controls-structure-v1','pid':snapshot.get('pid'),'read_scope':snapshot.get('read_scope'),'truncated':snapshot.get('truncated'),'node_count':len(all_nodes),'controls':controls,'AXValue_recorded':False,'arbitrary_help_recorded':False}

def locate_context(snapshot):
    try:return context(snapshot)
    except UIError as error:
        if str(error)!='chat-header-unavailable:0':raise
        return startup_context(snapshot)

def verify(ctx,job):
    if ctx['name']!=job['target'] or ctx['kind']!=job['kind']:raise UIError('recipient-mismatch')

def recent_row(ctx,target):
    direct_scrolls=[n for n in ctx['shell'].get('children',[]) if n['role']=='AXScrollArea']
    tables=[n for n in ctx['pool'] if n['role']=='AXTable' and any(below(n,s) for s in direct_scrolls)]
    table=only(tables,'conversation-list-ambiguous')
    found=[]
    for row in table.get('children',[]):
        if row['role']!='AXRow':continue
        for cell in row.get('children',[]):
            labels=[n for n in cell.get('children',[]) if n['role']=='AXStaticText' and value(n)]
            if labels and value(labels[0])==target:found.append(row)
    return only(found,'recipient-not-unique')

def search_field(ctx):
    if ctx.get('navigation_only') is True:return ctx['search']
    return only([n for n in ctx['shell'].get('children',[]) if n['role']=='AXTextField' and n['path']!=ctx['header']['path'] and 'AXValue' in n.get('settable',[])],'search-field-ambiguous')

def message_count(ctx,text):
    all_nodes=list(nodes(ctx['transcript']))
    # WeCom trims the final line break on send; preserve the full interior text.
    canonical=lambda s:str(s).replace('\r\n','\n').rstrip('\n')
    matches=[n for n in all_nodes if n['role'] in ('AXTextArea','AXStaticText') and canonical(value(n))==canonical(text)]
    for match in matches:
        rows=[n for n in all_nodes if n['role']=='AXRow' and below(match,n)]
        if not rows:raise UIError('message-row-unverified')
        row=max(rows,key=lambda n:len(n['path']))
        for item in nodes(row):
            if any(item.get(key) in ('发送失败','重新发送','重发','消息发送失败') for key in ('AXTitle','AXValue','AXDescription','AXHelp')):
                raise UIError('client-send-failed')
    return len(matches)
