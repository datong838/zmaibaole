"""One reviewed completed v2 origin, pure replay only. No live capability.
The v2 CLI remains unchanged. This catalogue does not authorize new operations.
"""
import copy
from pathlib import Path
import case_alias_cli as v2
c=v2.c;need=c.need
CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue_result_wait_v1.json')
CATALOGUE_SHA='b77c9523837fbf19c790168e4221c03c15a5f88a010ccad53e98ab6d4591c045'
V6_CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue_v6.json')
V6_SHA='d7b620255f0b908e1bc3b07a17824792e1fca28ad5b3b19111d9781c387d96bd'
V5_CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue_v5.json')
V5_SHA='b1b602bfbd3aa8da430864bc280d2448ed77f52de667509dbd8d05a762ab11a1'
PRIOR_CATALOGUE=Path(__file__).with_name('legacy_alias_catalogue.json')
PRIOR_SHA='c0e7d1a0f836b8adca5bc54bc332154e75075006f6f5c3357bc4dfa1f99f1e2b'
CURRENT_PRIOR=Path(__file__).with_name('legacy_alias_catalogue_v2.json')
CURRENT_PRIOR_SHA='b57edb115f04d48a0f6b5998b9a37296aff42d4aef0946471b61b8d4da20bd09'
PREVIOUS_REPLAY=Path(__file__).with_name('legacy_alias_catalogue_v4.json')
PREVIOUS_REPLAY_SHA='0b27ea9317cedf2b1992a5f50d32860b08cbd1eb64d00acfb9c936f27321f56b'
PREVIOUS_BASE=Path(__file__).with_name('legacy_alias_catalogue_v3.json')
PREVIOUS_BASE_SHA='be5d22f91c8e363bae337d91380c169ce86d6f6b273ad61c316b96491a8af317'
CONTENT_SUCCESSOR=Path(__file__).with_name('legacy_alias_catalogue_chongqing_select_v2.json')
CONTENT_SUCCESSOR_SHA='c78b2817f6304be9410fa174b2ba9c6d16738f28406e91dc03aa85cc83a55157'
DEPENDENCY_NAMES=('normal_review_body.py','export_parse_session.py','normal_paging.py','normal_source_proof_session.py')

def dependency_paths():
    return tuple(Path(v2.__file__).with_name(name).resolve() for name in DEPENDENCY_NAMES)

def catalogue():
    path=v2.canonical(CATALOGUE)
    need(c.ref(path)['sha256']==CATALOGUE_SHA,'legacy-alias-catalogue-changed')
    upgrade=v2.order_document({'path':str(path),'sha256':CATALOGUE_SHA})
    need(upgrade.get('schema')=='completed-v2-alias-reviewed-result-wait-v1','legacy-alias-v7-schema')
    need(c.ref(v2.canonical(V6_CATALOGUE))['sha256']==V6_SHA and upgrade.get('previous_replay_catalogue')=={'file':V6_CATALOGUE.name,'sha256':V6_SHA},'legacy-alias-v6-catalogue-binding')
    current=v2.order_document({'path':str(V6_CATALOGUE),'sha256':V6_SHA})
    changed={'schema','previous_replay_catalogue','reviewed_delta','current_code'}
    need(set(upgrade)==set(current)|{'v6_current_archives','v6_replay_helper_archive'} and all(upgrade[k]==v for k,v in current.items() if k not in changed),'legacy-alias-v6-origin-changed')
    runner_path=str(Path(v2.__file__).with_name('existing_result_runner.py').resolve())
    runner_delta={'/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/existing_result_runner.py':{'before': 'e96f33c9284662ac650a215e5b6784076302d3f310285323413081f3a204372f', 'after': 'a1f14ccab53961bbca35a9907c1f4dc6af50aceb419e68848dc1636709488665'}, '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/unbound_case_runner.py':{'before': 'e2eb33e8c8083b1a55cf276db3f1ee878d6afef53959b1aa70a515bf5d89f81f', 'after': '88aada4a02971053ba301eb7d22aadc52007d3fcd2e3b149fce053ac1f45f7ae'}}
    need(upgrade.get('reviewed_delta')==runner_delta and len(current['current_code'])==17 and current['current_code'].get(runner_path)==runner_delta[runner_path]['before'] and upgrade['current_code']=={**current['current_code'],**{p:x['after']for p,x in runner_delta.items()}},'legacy-result-wait-exact-runner-delta')
    v6_archives=upgrade.get('v6_current_archives',[])
    need(len(v6_archives)==17 and {x['logical_path']:x['sha256']for x in v6_archives}==current['current_code'],'legacy-result-wait-v6-full-before-data')
    need(upgrade['v6_replay_helper_archive']=={'logical_path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/legacy_alias_code_replay.py', 'archive_path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/legacy-v6-before/18-legacy_alias_code_replay.py', 'sha256': 'f2dbccf8c0e0b160941a1fbb4e1f16bf5c2f37b55bcbb93229233921dad3aecb'},'legacy-result-wait-v6-helper-data')
    for item in v6_archives+[upgrade['v6_replay_helper_archive']]:
        archived=v2.canonical(item['archive_path'])
        need(archived.parent==Path('/Users/feibing/work/projects/zmaibaole/work/performance-audit/existing-result-empty-drawer-settle-candidate/legacy-v6-before') and c.ref(archived)['sha256']==item['sha256'],'legacy-result-wait-before-data-changed')
    need(current.get('schema')=='completed-v2-alias-reviewed-code-closure-v6','legacy-alias-v6-schema')
    need(c.ref(v2.canonical(V5_CATALOGUE))['sha256']==V5_SHA and current.get('previous_replay_catalogue')=={'file':V5_CATALOGUE.name,'sha256':V5_SHA},'legacy-alias-v5-catalogue-binding')
    cat=v2.order_document({'path':str(V5_CATALOGUE),'sha256':V5_SHA})
    need(all(current[k]==cat[k] for k in ('old_code','archives','completed','source_refs','prior_catalogue','previous_current_catalogue','replay_dependency_names')),'legacy-alias-v5-origin-changed')
    workflow_path=str(Path(v2.__file__).with_name('workflow.py').resolve())
    workflow_delta={workflow_path:{'before':'ce3e2e927b2831fb758912049345385363866e1b714db64f6bbf35e29f739d41','after':'96ddcea071901d2b7b3e9ff82fcb3bcc6aa8d49824755c3e0ded7002f96f2e75'}}
    need(current.get('reviewed_delta')==workflow_delta and cat['current_code'].get(workflow_path)==workflow_delta[workflow_path]['before'] and current['current_code']=={**cat['current_code'],workflow_path:workflow_delta[workflow_path]['after']},'legacy-alias-v6-finite-workflow-delta')
    archives=current.get('v5_current_archives',[])
    need(len(archives)==17 and {x['logical_path']:x['sha256'] for x in archives}==cat['current_code'],'legacy-alias-v5-full-current-archive-required')
    frozen=archives+[current['v5_replay_helper_archive']]
    need(current['v5_replay_helper_archive']['sha256']=='e3ef220cf0e3475eb85e294534815a597a8b37a43659981970406f4fe11f1e6e','legacy-alias-v5-helper-origin')
    for item in frozen:
        archived=v2.canonical(path.parent/item['archive'])
        need(archived.is_relative_to(path.parent) and archived.parent.name=='legacy_alias_v5_sources' and c.ref(archived)['sha256']==item['sha256'],'legacy-alias-v5-current-archive-changed')
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
    r={'path':str(CONTENT_SUCCESSOR),'sha256':CONTENT_SUCCESSOR_SHA}
    need(c.ref(v2.canonical(CONTENT_SUCCESSOR))==r,'legacy-content-successor-ref')
    node=v2.order_document(r)
    content=str(Path(v2.__file__).resolve().parents[2]/'chrome-dom-export/extension/content.js')
    bridge=str(Path(v2.__file__).resolve().parents[2]/'chrome-dom-export/scripts/bridge.py')
    delta={content:{'before':'090a35790f9483694fd4c3868f7f8d975eebeea0592086a305c6ec422b2b4080','after':'adb99caa1f05e402f558cc99318b2d89cb1eb5af1d8c11f490eec9d47dd3c97f'},bridge:{'before':'b8f084aae25212a478da8ebd4de292545509ea87d441d486c35cbe5408630611','after':'6b7fb8d42031fe4e99040d325244863fab5bac4afccfe5fc8f9d4042bca98331'}}
    need(set(node)=={'schema','previous_catalogue','reviewed_delta','bridge_published_generation','content_candidate','current_code','capability','previous_content_successor','previous_content_published_generation','previous_content_code'} and node['schema']=='completed-v2-alias-exact-content-successor-v1' and node['previous_catalogue']=={'path':str(CATALOGUE),'sha256':CATALOGUE_SHA} and node['capability']=='completed-origin-pure-validation-only-no-live-old-operation','legacy-content-successor-schema')
    previous={'path': '/Users/feibing/work/projects/zmaibaole/skills/negative-review-complaints/scripts/legacy_alias_catalogue_chongqing_content_v1.json', 'sha256': '5cb087abc8eecb041530d6396a8aa2a0d236e5ea778e673dd5ca3942e33a5507'};need(node['previous_content_successor']==previous and c.ref(v2.canonical(previous['path']))==previous,'legacy-select-previous-ref');before=v2.order_document(previous);need(node['previous_content_code']==before['current_code']and node['current_code']=={**before['current_code'],content:'adb99caa1f05e402f558cc99318b2d89cb1eb5af1d8c11f490eec9d47dd3c97f'},'legacy-select-only-content-delta')
    origin={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-27/chongqing-content-source-publication/supervisor-release.json', 'sha256': '96eab405eeb1939af90c44de1eda27364c370cb21db21d4fad397f684cab1c23'};need(node['previous_content_published_generation']==origin,'legacy-select-origin-ref');published_before=v2.order_document(origin);matches=[t for t in published_before['targets']if t['target']==content];need(published_before['published']is True and published_before['test_projection_only']is False and len(matches)==1 and matches[0]['after']['sha256']==before['current_code'][content],'legacy-select-actual-old-generation');v2.order_document(previous)
    need(node['reviewed_delta']==delta and len(upgrade['current_code'])==17 and all(upgrade['current_code'][p]==d['before']for p,d in delta.items()) and node['current_code']=={**upgrade['current_code'],**{p:d['after']for p,d in delta.items()}},'legacy-content-successor-exact-delta')
    published=node['bridge_published_generation'];need(set(published)=={'release','target','after'} and published['release']=={'path':'/Users/feibing/work/projects/zmaibaole/work/2026-10-27/bridge-history-source-publication/supervisor-release.json','sha256':'e008c007041d0d7b158367b07bc542244fcf33fb0225c44a026bd9324467f5fb'} and published['target']==bridge,'legacy-content-bridge-origin')
    root=v2.order_document(published['release']);targets=[t for t in root['targets']if t['target']==bridge]
    need(root['published']is True and root['test_projection_only']is False and len(targets)==1 and targets[0]['after']==published['after'] and published['after']['sha256']==delta[bridge]['after'],'legacy-content-bridge-generation')
    capsule={x['logical_path']:x for x in upgrade['v6_current_archives']}
    for p,d in delta.items():need(capsule[p]['sha256']==d['before'] and c.ref(v2.canonical(capsule[p]['archive_path']))['sha256']==d['before'],'legacy-content-before-capsule')
    need(all(c.ref(v2.canonical(p))['sha256']==sha for p,sha in node['current_code'].items()),'legacy-content-current-closure')
    upgrade={**upgrade,'current_code':node['current_code']}
    need({a['logical_path']:a['sha256'] for a in cat['archives']}==cat['old_code'] and len(cat['archives'])==13,'legacy-alias-archive-graph')
    for a in cat['archives']:
        p=v2.canonical(path.parent/a['archive']);need(p.is_relative_to(path.parent) if hasattr(p,'is_relative_to') else path.parent in p.parents,'legacy-alias-archive-path')
        need(c.ref(p)['sha256']==a['sha256'],'legacy-alias-archive-changed')
    return upgrade

def code_files():
    cat=catalogue()
    # v6-before capsule is data, hash-bound by the new fixed catalogue and read
    # on every verification; archived Python is never loaded/executed.
    return [Path(__file__),CONTENT_SUCCESSOR,CATALOGUE,V6_CATALOGUE,V5_CATALOGUE,PRIOR_CATALOGUE,CURRENT_PRIOR,PREVIOUS_REPLAY,PREVIOUS_BASE,*[CATALOGUE.parent/a['archive']for a in cat['archives']],*dependency_paths(),*[CATALOGUE.parent/x['archive']for x in cat['v5_current_archives']],CATALOGUE.parent/cat['v5_replay_helper_archive']['archive']]

def completed(cat,m,manifest_ref):
    fixed=cat['completed'];need(manifest_ref==fixed['manifest'] and v2.order_document(manifest_ref)==m,'legacy-alias-original-manifest-required')
    for r in fixed.values():need(c.ref(v2.canonical(r['path']))==r,'legacy-alias-completed-artifact-changed')
    need(m['inputs']==cat['source_refs'],'legacy-alias-original-inputs-required')
    for r in cat['source_refs'].values():v2.order_document(r)
    s=v2.order_document(fixed['operation']);a=v2.order_document(fixed['apply'])
    need(s.get('state')=='complete' and s.get('manifest')==m and a.get('kind')=='apply-public-case-alias-v1' and a.get('state')=='complete' and a.get('receipt')==fixed['receipt'] and a.get('recorded_state')==fixed['application_ledger'] and a.get('workbook')==fixed['workbook'],'legacy-alias-completed-only')
    return s

def identity(m,manifest_ref):
    cat=catalogue();before={x['logical_path']:x['sha256']for x in cat['v6_current_archives']};historical={str(p.resolve()):before[str(p.resolve())]for p in v2.CODE}
    if m.get('code')==cat['old_code']:completed(cat,m,manifest_ref)
    elif m.get('code')==historical:
        # Completed/applied v2 only. Same immutable origin may support future
        # fresh v3 identity, never run/reconcile an unfinished old operation.
        v2.root_guard(m);need(c.ref(v2.folder(m)/'manifest.json')==manifest_ref and v2.order_document(manifest_ref)==m,'legacy-result-wait-canonical-completed-manifest')
        state=v2.order_document(c.ref(v2.folder(m)/'operation.json'));audit=v2.order_document(c.ref(v2.folder(m)/'apply'/'operation.json'));receipt=c.ref(v2.folder(m)/'alias-receipt.json')
        need(state.get('state')=='complete' and state.get('manifest')==m and audit.get('kind')=='apply-public-case-alias-v1' and audit.get('state')=='complete' and audit.get('receipt')==receipt and v2.order_document(receipt).get('operation')==c.ref(v2.folder(m)/'operation.json'),'legacy-result-wait-completed-applied-only')
        v2.runner.verify_complete(state)
    else:return v2.identity(m,manifest_ref)
    v2.root_guard(m);need(c.ref(v2.folder(m)/'manifest.json')==manifest_ref,'alias-original-canonical-manifest-required');need(m['order']==c.ref(m['order']['path']),'alias-order-changed');order=v2.order_document(m['order']);expected=copy.deepcopy({k:v for k,v in m.items()if k not in('order','lease','code','original_ledger')});expected['inputs']['ledger']=m['original_ledger'];need(order['manifest']==expected,'alias-order-manifest-mismatch');snap=v2.order_document(m['lease']['snapshot']);need(m['lease']['snapshot']['sha256']==m['lease']['observed']['sha256'] and m['lease']['observed']['path']==m['lease']['current_path']==str(v2.LEASE) and v2.lease_binding(snap)==m['lease']['binding'],'alias-pinned-lease-invalid');return m

def verify(manifest_ref):
    m=v2.order_document(manifest_ref);identity(m,manifest_ref);cat=catalogue();before={x['logical_path']:x['sha256']for x in cat['v6_current_archives']};historical={str(p.resolve()):before[str(p.resolve())]for p in v2.CODE}
    if m['code']==cat['old_code']:s=completed(cat,m,manifest_ref)
    elif m['code']==historical:s=v2.order_document(c.ref(v2.folder(m)/'operation.json'))
    else:return v2.verify(manifest_ref)
    return {'operation':c.ref(v2.folder(m)/'operation.json'),'alias':v2.runner.verify_complete(s),'ui_used':False}
