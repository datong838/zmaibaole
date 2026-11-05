"""Exact same-job text transport after an explicit client length rejection."""
import hashlib
from datetime import datetime,timezone
import ui

TIP='提示\n字数超出限制无法发出，是否需将消息转为智能文档发送？'
CONTRACT='same-job-exact-text-parts-v1'
def stamp():return datetime.now(timezone.utc).isoformat()
def digest(text):return hashlib.sha256(text.encode()).hexdigest()
def need(ok,reason):
    if not ok:raise ui.UIError(reason)
def split(text,limit=1800):
    result=[];current=''
    for line in text.splitlines(keepends=True):
        if len((current+line).encode())<=limit or not line.strip():current+=line;continue
        if current:result.append(current);current=''
        for char in line:
            if len((current+char).encode())>limit:result.append(current);current=''
            current+=char
    if current:result.append(current)
    need(''.join(result)==text and len(result)>1 and all(p.strip()and len(p.encode())<=1900 for p in result),'text-parts-exact-source-required')
    return result
def validate(s):
    p=s['text_parts'];parts=p['parts'];i=p['index']
    need(p['contract']==CONTRACT and p['original_fingerprint']==s['fingerprint'] and ''.join(parts)==s['job']['text'],'text-parts-source-changed')
    need(type(i)is int and 0<=i<len(parts) and len(p['confirmed'])==i and all(r['index']==n and r['text_sha256']==digest(parts[n]) and r.get('send_intent_at') and r.get('ui_confirmed_at')for n,r in enumerate(p['confirmed'])),'text-parts-current-frontier-changed')
    return parts[i]
def _parts(s,event):
    s['text_parts']={'contract':CONTRACT,'original_fingerprint':s['fingerprint'],'parts':split(s['job']['text']),'index':0,'confirmed':[]}
    s.update(phase='stage',status='running',checks=0);s.pop('error',None)
    event(s,'client-length-rejected-split',parts=len(s['text_parts']['parts']),original_text_sha256=digest(s['job']['text']))
def recover_rejection(native,s,path,atomic,event):
    need(not s.get('text_parts')and s['job']['type']=='text','text-rejection-original-text-required')
    snapshot=native.tree();ctx=ui.context(snapshot);ui.verify(ctx,s['job'])
    tips=[n for n in ui.nodes(snapshot['tree'])if n.get('role')=='AXStaticText'and ui.value(n)==TIP]
    if not tips:return False
    tip=ui.only(tips,'text-limit-tip-not-unique');modal=ui.only([n for n in ui.nodes(snapshot['tree'])if any(c.get('path')==tip['path']for c in n.get('children',[]))],'text-limit-modal-not-unique')
    buttons=[n for n in modal.get('children',[])if n.get('role')=='AXButton']
    need(modal.get('role')=='AXSheet'and len(modal['children'])==4 and {ui.value(n)for n in buttons}=={'取消','发送'}and len([n for n in modal['children']if n.get('role')=='AXImage'and ui.value(n)=='alert window logo'and not n.get('children')])==1,'text-limit-modal-shape-changed')
    need(ui.value(ctx['composer'])==s['job']['text']and ui.message_count(ctx,s['job']['text'])==s['baseline'],'text-rejection-owned-unsent-draft-required')
    s['length_rejection']={'reason':TIP,'original_send_intent_at':s['send_intent_at'],'original_text_sha256':digest(s['job']['text']),'observed_at':stamp(),'cancel_intent_at':stamp()}
    s.update(phase='text-limit-cancel-pending',status='unknown');event(s,'client-rejected-before-delivery',reason=TIP);atomic(path,s)
    native.press(ui.only([n for n in buttons if ui.value(n)=='取消'],'text-limit-cancel-required'))
    return finish_cancel(native,s,event)
def finish_cancel(native,s,event):
    snapshot=native.tree();ctx=ui.context(snapshot);ui.verify(ctx,s['job'])
    need(not any(ui.value(n)==TIP for n in ui.nodes(snapshot['tree']))and ui.value(ctx['composer'])==s['job']['text'],'text-limit-cancel-outcome-unresolved')
    need(s.get('length_rejection',{}).get('original_text_sha256')==digest(s['job']['text'])and ui.message_count(ctx,s['job']['text'])==s['baseline'],'text-limit-rejection-binding')
    s['length_rejection']['cancel_confirmed_at']=stamp();_parts(s,event);return True
def confirm(s,event,finish,count):
    p=s['text_parts'];label=validate(s);i=p['index']
    p['confirmed'].append({'index':i,'text_sha256':digest(label),'send_intent_at':s['send_intent_at'],'ui_confirmed_at':stamp(),'baseline':s['baseline'],'message_count':count})
    event(s,'text-part-ui-confirmed',index=i,text_sha256=digest(label))
    if i+1==len(p['parts']):finish(s)
    else:p['index']+=1;s.update(phase='stage',status='running',checks=0);s.pop('error',None)

def validate_completed(s):
    p=s['text_parts'];parts=p['parts'];receipts=p['confirmed']
    need(p['contract']==CONTRACT and p['original_fingerprint']==s['fingerprint'] and ''.join(parts)==s['job']['text'],'text-parts-source-changed')
    need(s.get('length_rejection',{}).get('cancel_confirmed_at')and len(receipts)==len(parts) and p['index']==len(parts)-1,'text-parts-not-complete')
    need(all(r['index']==i and r['text_sha256']==digest(parts[i]) and r.get('send_intent_at') and r.get('ui_confirmed_at')and r['message_count']>r['baseline']for i,r in enumerate(receipts)),'text-parts-client-confirmation-missing')
