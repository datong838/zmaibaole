"""Explicit observed custom main-chat AXDialog; no content or action access."""
STOP={'AXTable','AXOutline','AXTextArea','AXTextField','AXComboBox'}
STRUCTURAL={'AXWindow','AXSplitGroup','AXScrollArea','AXScrollBar','AXGroup'}
# Only the public containers whose child membership is required by the shape.
REQUIRED_CHILD_PATHS={(),(0,),(0,5),(0,8),(0,8,2),(0,8,9),(0,8,9,0),(0,8,9,0,0),(0,8,9,0,2),(0,8,9,2)}
def field(n,key):return n.get(key,n.get({'AXTitle':'title','AXSubrole':'subrole'}.get(key,key)))
def dialog_parts(root):
    """Main-app navigation topology, not variable toolbar/child totals.
    This only identifies a main window. It gives no recipient/composer authority.
    """
    if root.get('role')!='AXWindow' or field(root,'AXTitle')!='企业微信' or field(root,'AXSubrole')!='AXDialog':return None
    found=[]
    def walk(n,depth=0):
        if len(found)>=250 or depth>12:raise ValueError('main-dialog-shape-budget')
        found.append(n)
        if depth and (n.get('role') in ('AXWindow','AXDialog','AXSheet') or field(n,'AXSubrole')=='AXDialog'):raise ValueError('main-dialog-nested-modal')
        if n.get('role') not in STOP:
            for child in n.get('children',[]):walk(child,depth+1)
    try:walk(root)
    except ValueError:return None
    direct=root.get('children',[]);bodies=[n for n in direct if n.get('role')=='AXSplitGroup']
    if len(bodies)!=1:return None
    for subrole in ('AXCloseButton','AXFullScreenButton','AXMinimizeButton'):
        if len([n for n in direct if n.get('role')=='AXButton' and field(n,'AXSubrole')==subrole])!=1:return None
    if any(n is not bodies[0] and not(n.get('role')=='AXButton' and field(n,'AXSubrole') in ('AXCloseButton','AXFullScreenButton','AXMinimizeButton')) for n in direct):return None
    body=bodies[0]
    def table_scrolls(parent):return [n for n in parent.get('children',[]) if n.get('role')=='AXScrollArea' and len([c for c in n.get('children',[]) if c.get('role')=='AXTable'])==1]
    sidebar=table_scrolls(body)
    shells=[n for n in body.get('children',[]) if n.get('role')=='AXSplitGroup' and table_scrolls(n) and any(c.get('role')=='AXTextField' for c in n.get('children',[]))]
    if len(sidebar)!=1 or len(shells)!=1:return None
    shell=shells[0];lists=table_scrolls(shell)
    if len(lists)!=1:return None
    if len([n for n in found if n.get('role')=='AXTextArea'])>1:return None
    return {'body':body,'shell':shell,'sidebar':sidebar[0],'conversation_list':next(c for c in lists[0]['children'] if c.get('role')=='AXTable')}

def dialog_shape(root):return dialog_parts(root) is not None

def native_main_window(native,window):
    # Generic legacy window qualification is deliberately unchanged.
    title=native.get(window,'AXTitle');sub=native.get(window,'AXSubrole')
    if title!='企业微信':return False
    if sub=='AXStandardWindow':return True
    if sub!='AXDialog':return False
    count=0
    def read(e,path=()):
        nonlocal count
        count+=1
        if count>250 or len(path)>12:raise ValueError('main-dialog-shape-budget')
        role=native.get(e,'AXRole');row={'role':role,'AXSubrole':native.get(e,'AXSubrole')}
        if not path:row['AXTitle']=title
        if role not in STOP:
            required=not path # Semantic descendant membership is checked by dialog_parts.
            children=native.scoped_array(e,'AXChildren',required)
            if children is None:
                if required:raise ValueError('main-dialog-required-children-missing')
                children=[]
            row['children']=[read(c,path+(i,)) for i,c in enumerate(children)]
        return row
    return dialog_shape(read(window))

def snapshot_main_window(window):
    return window.get('role')=='AXWindow' and field(window,'AXTitle')=='企业微信' and (field(window,'AXSubrole')=='AXStandardWindow' or dialog_shape(window))
