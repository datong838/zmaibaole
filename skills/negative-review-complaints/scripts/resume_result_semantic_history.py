#!/usr/bin/env python3
"""One exact case13 parser HOLD handoff. No workflow invocation or bridge calls."""
if __name__=='__main__':
    from runtime_entry import ensure_runtime
    ensure_runtime()
import argparse,fcntl,hashlib,json
from pathlib import Path
import normal_case_source_proof_runner as W
need=W.j.need
KIND='supervisor-exact-result-semantic-history-resume-v1'
EXPECTED={'batch': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/normal-case-batches/009047b3483643ef9a7a1c48e6db0025417c1020240a1a97d700a4b819d20ea8/operation.json', 'sha256': 'c994ae5adaebc97dfbcb8ea1708809d06bc75dbac887bdb8794d36878aed7501'}, 'operation': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/existing-result-operations/abd0752999a9d51749905a2a50b21f3fcbfbb63c07f298360947aad1e7fd159a/009047b3483643ef9a7a1c48e6db0025417c1020240a1a97d700a4b819d20ea8/operation.json', 'sha256': 'd156b86d972023050fe3539bf5aa8d43b5795983757490cc69aa12483b6e87a1'}, 'drawer': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/existing-result-operations/abd0752999a9d51749905a2a50b21f3fcbfbb63c07f298360947aad1e7fd159a/009047b3483643ef9a7a1c48e6db0025417c1020240a1a97d700a4b819d20ea8/0003-drawer.json', 'sha256': 'bf51478f5f49df072aaf8183c7734e60863c73802c78f6bd9feeb729c541680a'}, 'before': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/existing-result-operations/abd0752999a9d51749905a2a50b21f3fcbfbb63c07f298360947aad1e7fd159a/009047b3483643ef9a7a1c48e6db0025417c1020240a1a97d700a4b819d20ea8/0002-normal-before.json', 'sha256': '662edd35869f331ba17d402907d726dc594bffe912913407d7f4c82eea8ee833'}, 'history': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/state.json', 'sha256': '09c5f3305389e2d746b53a3a5df980a6b223aced9f49715f9e73c3ddb525eea2'}, 'inspection': {'path': '/Users/feibing/work/projects/zmaibaole/work/live-acceptance/complaints/month-history-20260921-20261021/01-1767942028615694/read-orders/009047b3483643ef9a7a1c48e6db0025417c1020240a1a97d700a4b819d20ea8/abd0752999a9d51749905a2a50b21f3fcbfbb63c07f298360947aad1e7fd159a.json', 'sha256': '3f09fb4758e31a63a593538da0ad853f14d91961afc290cd92f0efd5d62afbdd'}, 'checkpoint': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-23/history-only-preflight/actor-yantai-existing-batch-v6/hold-checkpoint.json', 'sha256': '721eb219a3c3ae6ef8c400bb8e596b30c30a39f7e6cf879ab58bd653f7d021bc'}}
REPAIR={'/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/case_memory.py': 'd69a5ac3151cc35c566491ca4bb00230bc7beb156a111ab8eb967361d4d230c5', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/normal_case_source_proof_runner.py': '694474bdc9c19663fe9c929d6a11b2d2a8ab84af03308de9033422fa4764768c', '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/result_observation.py': '8db833a645c7e338086000287d3e6dd7d4360555c5c0e87a18d81c0325fd75e8'}

def read(ref):return json.loads(W.P._bytes(ref))
def resume(grant_ref):
    grant=read(grant_ref)
    need(grant.get('kind')==KIND and grant.get('approved') is True and grant.get('reviewer_role')=='supervisor' and grant.get('quiescent') is True,'result-repair-supervisor-grant')
    need(grant.get('original_refs')==EXPECTED and grant.get('repair_pins')==REPAIR,'result-repair-exact-scope')
    release=read(grant['release']);need(release.get('published') is True,'result-repair-unpublished')
    import openpyxl
    need(grant.get('code_refs')==W.code_refs(),'result-repair-current-graph')
    for path,sha in REPAIR.items():W.P._bytes({'path':path,'sha256':sha})
    event={'kind':KIND,'grant':grant_ref,'original_batch':EXPECTED['batch'],'opened_operation':EXPECTED['operation']}
    path=Path(EXPECTED['batch']['path']);W.P._bytes({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    lock_path=path.parent/'.lock'
    need(not lock_path.is_symlink() and lock_path.is_file(),'result-repair-original-lock')
    with lock_path.open('r+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads(path.read_bytes())
        if state.get('semantic_history_recovery')==event:return {'ok':True,'idempotent':True,'state':state['state'],'UI_RPC_used':False}
        values={k:read(v) for k,v in EXPECTED.items()};op=values['operation'];m=values['inspection'];batch_manifest=read(state['manifest'])
        need(state==values['batch'] and state.get('state')=='hold' and state.get('error')=='result-report-form-unverified' and len(state.get('completed',[]))==12,'result-repair-original-hold')
        need(op.get('state')=='opened' and op.get('error')=='result-report-form-unverified' and op.get('manifest')==m and not op.get('result_input') and op.get('open_reply') and not op.get('close_command'),'result-repair-original-opened')
        W.j.results.clicked(op['open_reply'],op['open_command'])
        need(state.get('current_key')==m['review_key'] and state['completed']==batch_manifest['keys'][:12] and batch_manifest['keys'][12]==m['review_key'],'result-repair-next-case')
        need(state.get('journey')=={'state':'complete','navigation_used':False,'resume_original_result_only':True},'result-repair-no-navigation')
        need(grant['code_refs']==W.code_refs(),'result-repair-exit-code-changed')
        state.update(state='running',semantic_history_recovery=event);state.pop('error')
        W.j.c.save(path,state)
        return {'ok':True,'idempotent':False,'state':'running','operation':W.j.c.ref(path),'UI_RPC_used':False}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--grant',required=True);ap.add_argument('--grant-sha256',required=True);a=ap.parse_args()
    print(json.dumps(resume({'path':a.grant,'sha256':a.grant_sha256}),ensure_ascii=False))
if __name__=='__main__':main()
