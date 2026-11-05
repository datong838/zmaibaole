"""Consumer for composer guards only. No transcript/message-count contract."""
import ui
from composer_guard import SCOPE

def context(snapshot,*,require_focused=False):
    if snapshot.get('read_scope')!=SCOPE or snapshot.get('guard_complete') is not True or snapshot.get('truncated') is not False or snapshot.get('history_read') is not False or snapshot.get('transcript_complete') is not False or snapshot.get('window_inventory_complete') is not True or snapshot.get('menu_state')!='positively-no-shown-menu':raise ui.UIError('composer-guard-incomplete')
    recipient=snapshot['recipient'];composer=snapshot['composer'];focus=snapshot['focus']
    if composer.get('role')!='AXTextArea' or 'AXValue' not in composer.get('settable',[]):raise ui.UIError('composer-guard-editor-unverified')
    if require_focused and not (focus.get('frontmost') is True and focus.get('focused_composer') is True):raise ui.UIError('composer-guard-composer-not-focused')
    return {'read_scope':SCOPE,'history_read':False,'name':recipient['name'],'kind':recipient['kind'],'header':recipient['header'],'composer':composer,'window':snapshot['window'],'focus':focus}

def verify(ctx,job):
    if ctx.get('read_scope')!=SCOPE or ctx.get('history_read') is not False:raise ui.UIError('composer-guard-context-required')
    ui.verify(ctx,job)
