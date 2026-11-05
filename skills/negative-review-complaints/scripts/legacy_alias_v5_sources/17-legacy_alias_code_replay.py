"""One reviewed completed v2 origin, pure replay only. No live capability.
The v2 CLI remains unchanged. This catalogue does not authorize new operations.
"""
import copy
from pathlib import Path
import case_alias_cli as v2
c=v2.c;need=c.need
CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue_v5.json')
CATALOGUE_SHA='b1b602bfbd3aa8da430864bc280d2448ed77f52de667509dbd8d05a762ab11a1'
PRIOR_CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue.json')
PRIOR_SHA='c0e7d1a0f836b8adca5bc54bc332154e75075006f6f5c3357bc4dfa1f99f1e2b'
CURRENT_PRIOR=Path(__file__).with_name('legacy_alias_catalogue_v2.json')
CURRENT_PRIOR_SHA='b57edb115f04d48a0f6b5998b9a37296aff42d4aef0946471b61b8d4da20bd09'
PREVIOUS_REPLAY=Path(__file__).with_name('legacy_alias_catalogue_v4.json')
PREVIOUS_REPLAY_SHA='0b27ea9317cedf2b1992a5f50d32860b08cbd1eb64d00acfb9c936f27321f56b'
PREVIOUS_BASE=Path(__file__).with_name('legacy_alias_catalogue_v3.json')
PREVIOUS_BASE_SHA='be5d22f91c8e363bae337d91380c169ce86d6f6b273ad61c316b96491a8af317'
DEPENDENCY_NAMES=('normal_review_body.py','export_parse_session.py','normal_paging.py','normal_source_proof_session.py')

def dependency_paths():
    return tuple(Path(v2.__file__).with_name(name).resolve() for name in DEPENDENCY_NAMES)

def catalogue():
    path=v2.canonical(CATALOGUE)
    need(c.ref(path)['sha256']==CATALOGUE_SHA,'legacy-alias-catalogue-changed')
    cat=v2.order_document({'path':str(path),'sha256':CATALOGUE_SHA})
    need(cat['schema']=='completed-v2-alias-reviewed-code-closure-v5','legacy-alias-catalogue-schema')
    need(c.ref(v2.canonical(PREVIOUS_REPLAY))['sha256']==PREVIOUS_REPLAY_SHA,'legacy-alias-previous-replay-changed')
    replay=v2.order_document({'path':str(v2.canonical(PREVIOUS_REPLAY)),'sha256':PREVIOUS_REPLAY_SHA})
    need(cat.get('previous_replay_catalogue')=={'file':PREVIOUS_REPLAY.name,'sha256':PREVIOUS_REPLAY_SHA} and replay.get('schema')=='completed-v2-alias-reviewed-code-closure-v4','legacy-alias-previous-replay-binding')
    need(all(cat[k]==replay[k] for k in ('old_code','archives','completed','source_refs','prior_catalogue','previous_current_catalogue','replay_dependency_names')),'legacy-alias-replay-origin-changed')
    need(c.ref(v2.canonical(PREVIOUS_BASE))['sha256']==PREVIOUS_BASE_SHA,'legacy-alias-base-replay-changed')
    inherited=v2.order_document({'path':str(v2.canonical(PREVIOUS_BASE)),'sha256':PREVIOUS_BASE_SHA})
    need(replay.get('previous_replay_catalogue')=={'file':PREVIOUS_BASE.name,'sha256':PREVIOUS_BASE_SHA} and inherited.get('schema')=='completed-v2-alias-reviewed-code-closure-v3','legacy-alias-base-replay-binding')
    prior_parser=str(Path(v2.__file__).with_name('result_observation.py').resolve())
    parser_delta={prior_parser:{'before':'eea92e5e65c69af6e22105f30e2a077c7cd849720e257c816cbebb3219e28303','after':'8db833a645c7e338086000287d3e6dd7d4360555c5c0e87a18d81c0325fd75e8'}}
    need(replay.get('reviewed_delta')==parser_delta and replay['current_code']=={**inherited['current_code'],prior_parser:parser_delta[prior_parser]['after']} and inherited['current_code'][prior_parser]==parser_delta[prior_parser]['before'],'legacy-alias-inherited-parser-delta')
    delta_path=str(Path(v2.__file__).with_name('normal_paging.py').resolve())
    expected_delta={delta_path:{'before':'98afbf69d6561270474a606bfdaca9591329c3007a175bbe25e50ca289294920','after':'fe3601e6b7949ff3c3771a3db139be0b90faa9a86a1052a8374b3e148f193744'}}
    need(cat.get('reviewed_delta')==expected_delta and set(cat['current_code'])==set(replay['current_code']),'legacy-alias-finite-parser-delta')
    need(all(cat['current_code'][k]==(expected_delta[k]['after'] if k in expected_delta else v) for k,v in replay['current_code'].items()) and replay['current_code'][delta_path]==expected_delta[delta_path]['before'],'legacy-alias-parser-delta-changed')
    need(cat.get('prior_catalogue')=={'file':PRIOR_CATALOGUE.name,'sha256':PRIOR_SHA} and c.ref(v2.canonical(PRIOR_CATALOGUE))['sha256']==PRIOR_SHA,'legacy-alias-prior-catalogue-changed')
    prior=v2.order_document({'path':str(v2.canonical(PRIOR_CATALOGUE)),'sha256':PRIOR_SHA})
    need(prior.get('schema')=='completed-v2-alias-reviewed-code-migration-v1' and all(cat[k]==prior[k] for k in ('old_code','archives','completed','source_refs')),'legacy-alias-origin-evidence-changed')
    previous=v2.order_document({'path':str(v2.canonical(CURRENT_PRIOR)),'sha256':CURRENT_PRIOR_SHA})
    need(cat.get('previous_current_catalogue')=={'file':CURRENT_PRIOR.name,'sha256':CURRENT_PRIOR_SHA} and previous.get('schema')=='completed-v2-alias-reviewed-code-closure-v2' and all(cat[k]==previous[k] for k in ('old_code','archives','completed','source_refs','prior_catalogue')) and len(previous['current_code'])==15 and all(inherited['current_code'].get(k)==v for k,v in previous['current_code'].items()),'legacy-alias-previous-closure-changed')
    original={str(p.resolve()) for p in v2.CODE};dependencies={str(p) for p in dependency_paths()}
    need(len(original)==13 and not original&dependencies and set(cat['old_code'])==original and len(cat['old_code'])==13 and set(cat['current_code'])==original|dependencies and len(cat['current_code'])==17,'legacy-alias-code-graph')
    need(cat.get('replay_dependency_names')==list(DEPENDENCY_NAMES),'legacy-alias-explicit-dependencies-required')
    need({p:c.ref(v2.canonical(p))['sha256'] for p in cat['current_code']}==cat['current_code'],'legacy-alias-current-code-changed')
    need({a['logical_path']:a['sha256'] for a in cat['archives']}==cat['old_code'] and len(cat['archives'])==13,'legacy-alias-archive-graph')
    for a in cat['archives']:
        p=v2.canonical(path.parent/a['archive']);need(p.is_relative_to(path.parent) if hasattr(p,'is_relative_to') else path.parent in p.parents,'legacy-alias-archive-path')
        need(c.ref(p)['sha256']==a['sha256'],'legacy-alias-archive-changed')
    return cat

def code_files():
    cat=catalogue()
    return [Path(__file__),CATALOGUE,PRIOR_CATALOGUE,CURRENT_PRIOR,PREVIOUS_REPLAY,PREVIOUS_BASE,*[CATALOGUE.parent/a['archive'] for a in cat['archives']],*dependency_paths()]

def completed(cat,m,manifest_ref):
    fixed=cat['completed'];need(manifest_ref==fixed['manifest'] and v2.order_document(manifest_ref)==m,'legacy-alias-original-manifest-required')
    for r in fixed.values():need(c.ref(v2.canonical(r['path']))==r,'legacy-alias-completed-artifact-changed')
    need(m['inputs']==cat['source_refs'],'legacy-alias-original-inputs-required')
    for r in cat['source_refs'].values():v2.order_document(r)
    s=v2.order_document(fixed['operation']);a=v2.order_document(fixed['apply'])
    need(s.get('state')=='complete' and s.get('manifest')==m and a.get('kind')=='apply-public-case-alias-v1' and a.get('state')=='complete' and a.get('receipt')==fixed['receipt'] and a.get('recorded_state')==fixed['application_ledger'] and a.get('workbook')==fixed['workbook'],'legacy-alias-completed-only')
    return s

def identity(m,manifest_ref):
    cat=catalogue()
    if m.get('code')!=cat['old_code']:return v2.identity(m,manifest_ref)
    completed(cat,m,manifest_ref);v2.root_guard(m)
    need(c.ref(v2.folder(m)/'manifest.json')==manifest_ref,'alias-original-canonical-manifest-required')
    need(m['order']==c.ref(m['order']['path']),'alias-order-changed');order=v2.order_document(m['order'])
    expected=copy.deepcopy({k:v for k,v in m.items() if k not in ('order','lease','code','original_ledger')});expected['inputs']['ledger']=m['original_ledger'];need(order['manifest']==expected,'alias-order-manifest-mismatch')
    snap=v2.order_document(m['lease']['snapshot']);need(m['lease']['snapshot']['sha256']==m['lease']['observed']['sha256'] and m['lease']['observed']['path']==m['lease']['current_path']==str(v2.LEASE) and v2.lease_binding(snap)==m['lease']['binding'],'alias-pinned-lease-invalid')
    return m

def verify(manifest_ref):
    m=v2.order_document(manifest_ref);identity(m,manifest_ref)
    if m['code']!=catalogue()['old_code']:return v2.verify(manifest_ref)
    s=completed(catalogue(),m,manifest_ref)
    return {'operation':c.ref(v2.folder(m)/'operation.json'),'alias':v2.runner.verify_complete(s),'ui_used':False}
