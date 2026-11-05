#!/usr/bin/env python3
"""Pure, immutable native-selector descriptor from a real ticket and root grant."""
import argparse,hashlib,json,os,re
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def need(ok,message):
    if not ok:raise ValueError(message)
def ref(path):
    p=Path(path);need(p.is_absolute() and p.resolve()==p and not any(q.is_symlink() for q in (p,*p.parents)),'canonical-reference-required')
    need(p.name not in ('config.js','config.json'),'config-read-forbidden')
    return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(reference):
    need(set(reference)=={'path','sha256'} and ref(reference['path'])==reference,'pinned-reference-changed')
    return json.loads(Path(reference['path']).read_bytes())
def prepare(ticket_ref,grant_ref,*,root=ROOT):
    ticket=read(ticket_ref);grant=read(grant_ref)
    need(ticket.get('kind')=='independent-python-server-and-extension-maintenance-ticket-v1','maintenance-ticket-required')
    need(grant.get('kind')=='supervisor-existing-browser-maintenance-grant-v1' and grant.get('ticket')==ticket_ref,'original-root-grant-required')
    need(grant.get('authorized') is True and grant.get('maintenance_only') is True and grant.get('one_original_merchant_activation_only') is True,'maintenance-only-grant-required')
    need(all(grant.get(k) is False for k in ('execute_business','test_wecom_send','complaint_submit','chrome_restart','debugging')),'maintenance-redline-conflict')
    need(grant.get('actor')==ticket.get('target_actor') and grant.get('unknown_input_outcome_no_replay') is True,'maintenance-actor-or-replay-conflict')
    key=ticket.get('ticket_id');need(type(key) is str and re.fullmatch('[A-Za-z0-9_.:-]{8,128}',key),'maintenance-ticket-id-required')
    command=ticket.get('readonly_verification_command',{});need(set(command)=={'op','tabId','windowId'} and command['op']=='readonly-scope' and all(type(command[k]) is int and command[k]>0 for k in ('tabId','windowId')),'original-merchant-scope-required')
    release=read(grant['formal_release']);need(release.get('status')=='published-files-maintenance-required-not-installed' and release.get('published')==grant.get('published_files') and bool(release.get('published')),'formal-release-required')
    for relative,digest in release['published'].items():
        path=root/relative;need(relative.startswith('skills/') and path.resolve().is_relative_to(root.resolve()) and path.name not in ('config.js','config.json'),'release-path-forbidden')
        need(ref(path)['sha256']==digest,'published-source-changed')
    out=Path(ticket_ref['path']).parent/'native-control-order.json'
    value={'kind':'independent-extension-maintenance-ticket-v1','descriptor_kind':'root-approved-native-control-maintenance-compat-v1','ticket_id':key,'created_at':datetime.now(timezone.utc).isoformat(),'no_business_dispatch':True,'await_supervisor_review_after_report':True,'release':grant['formal_release'],'derived_from':{'maintenance_ticket':ticket_ref,'root_grant':grant_ref},'allowed':['select existing reviewed local control tab','update installed extension once under original maintenance intent','return originalmerchant'+str(command['tabId'])],'forbidden':['business actions','WeCom sends','complaint submission','new Chrome tabs','Chrome restart','debugging','credentials','pixel input','replay unknown input']}
    if out.exists():
        old=read(ref(out));need({k:v for k,v in old.items() if k!='created_at'}=={k:v for k,v in value.items() if k!='created_at'},'original-native-maintenance-order-conflict')
    else:
        with out.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())
    return {'order':ref(out),'ui_used':False,'maintenance_authorized_by':grant_ref,'new_authorization_invented':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('ticket','grant'):p.add_argument('--'+name,required=True);p.add_argument('--'+name+'-sha256',required=True)
    a=p.parse_args();print(json.dumps(prepare(*[{'path':getattr(a,k),'sha256':getattr(a,k+'_sha256')} for k in ('ticket','grant')]),ensure_ascii=False))
if __name__=='__main__':main()
