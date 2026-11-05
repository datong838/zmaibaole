"""Exact pre-native reboot continuation and source-bound environment restoration.
The restoration entry delegates only reviewed public navigation/filter programs;
no export, ingestion, screenshot, submission or notification entry is exposed.
Archives are data, never imported/executed. Admission is not a retry or lease.
"""
import copy,hashlib,json,os,sys
from pathlib import Path
from urllib.parse import urlsplit
PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'skills/workshop-director/scripts'))
sys.path.insert(0,str(PROJECT/'skills/violation-notifier/scripts'))
import role_execution_order as o
TASK='task-a443734e6e62e6a0c146755f'
ATTEMPT=TASK+'-11'
KIND='verified-violation-pre-native-reboot-continuation-v1'
CHECKPOINT_SHA='d3910460d381fdea05ae9ac34b7651578b0aa60f7203a4f72ef974de17e6f7e2'
OLD_BOOT='darwin-kern-bootsessionuuid:ce9cc1b4-7142-4035-9d74-2b7e51e4f803'
ERROR='execution-anchor-contract-proof-failed'
CATALOGUE_SHA='7b730baa6d53fb5061cd867c809b6e3b2bcb36066acaadb1aa3e151589d3dfd5'
V2_RELEASE_SHA='e833cc7e9e4b2efa0829ed5179d394d8865e97bbeac6897dade2f8392c6c19f8'
PRE_DISPATCH_AUTHORITY={'failure': {'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-23/standalone-oneoff-execution-brief/violation-reboot-date-focus-preinput-failure.json', 'sha256': 'dbbde718c631d8692667e5a42fd0495c750963ea4f13f6fa06df9a3364958512'}, 'query_sha256': 'c7c3b627c1f1d9c1242358fcba0d511dba17fd79e645513585958f4f1e52e1b5', 'probe_sha256': '557a75e19c7f8f796227e07f9554dd94da2b31d57d056b5bd661862764db5f3d', 'cli_sha256': '48a3e1825ec99c436d37b17e566b4118ec875c7ef6a53e8097a74ab73d83b44b', 'source_sha256': '0ffe34f0135041a7a423802533033e252d4267c46f591e48dc99c78a1017a695', 'transport': {'000-intent.json': '86740ea6f4b2e29a0dc80626b865ceace9b378d9ae26a9ce2c96b9194694758a', '000-reply.json': 'd0ea080559cb8c8c8054fb0687da14b83d4728abb2ef4fd83ff1081063f50056', '000-returned.json': '0c703a00f7ab4d07fe5e6752eabc517912a3c98a159fc3812d76115cbfa98d41', '001-intent.json': 'cb898ff75f4c25a0c85169152c770a9d15f156edbece3c158c81a2ebd2029c88', '001-reply.json': '037906ebb0d048bb6fe13457e23adbddbe24e0e48effa7b6d3a62426eef7a92c', '001-returned.json': '81ed830663ec5c44b4273e775c21807185c29bc9e01e4c4c96a3fe7481473ea2', '002-intent.json': 'f91624b9481222cdec248b4bf475f6c460ef8b8816791b0811560dad33a4b200', '002-reply.json': '2c891cdb2d0425a06e42531fe3f1d50ebffa63f1bb00c45b096af680612ef678', '002-returned.json': 'a63e801b8fc9ad84d6a4705d93c83e2e6873605c54b35b0c756506879a9910fd', '003-intent.json': '86740ea6f4b2e29a0dc80626b865ceace9b378d9ae26a9ce2c96b9194694758a', '003-reply.json': '634d00482dd2c878c3157936b8f1c03026cdde0b21ddb70c5c7b13a01a60312b', '003-returned.json': '049d5457f73b976b6ef1ef1dfb3a54f67abd1366dca08db24c976498893989dc', '004-intent.json': '6d5299d77ec4c9f5615867d01064f3942c4cdf6cf82187b0b8bf97c0332cad84'}, 'error': 'reboot-date-correction-input-current-window-focus'}
V1_RELEASE_SHA='543c1f194d92c67682abf6147e10e7beaa76e8addecb3fce3c5e5115692ad16b'
DATE_FAILURE_SHA='945f47c53f07b8f89882bb3bae8b94f76b2f5b56b11b3f13f2889829a310da71'
DATE_JOURNAL_SHA='ac9c296ef50a94e3ab8777367cade22391f97d3e67f70619d8515c79ab3f3c61'
DATE_ORIGINAL_READS={'000-intent.json': '80de81fae5881575c5cc340573fc954aee5aa157941726f670a9ba7d21d6376e', '000-reply.json': '3223ed5ebcb63f7e92bfbbcb0a071a857e396e0ed90befc908b24a8cba73c4e2', '000-returned.json': '6799d4bdf7f867f20803d50676643346a3d1280f6743cacb452d1b12468e89c4', '001-intent.json': 'acc02b644e80c0ebd670bfa0250c7fa47d2cf8c33336e75480b04f8c4df19069', '001-reply.json': '037906ebb0d048bb6fe13457e23adbddbe24e0e48effa7b6d3a62426eef7a92c', '001-returned.json': '616f54e468d6efe10df589ef6a1f6babd0a6ee066ee6d369d9ac8b952e63cd40', '002-intent.json': 'b97a04aeca45a7aa501d40befc00b67040769844675a453fc9293b6dc0d9429c', '002-reply.json': '37bfc1254d7ca2ef668e42d20bd7d36e1c13dcbf9f1b7d568affe532ee511a8d', '002-returned.json': 'b82076b26e036f084a605e970299d18e0334fc8c2a37550fe31adb196f4ddcd0', '003-intent.json': '80de81fae5881575c5cc340573fc954aee5aa157941726f670a9ba7d21d6376e', '003-reply.json': '3223ed5ebcb63f7e92bfbbcb0a071a857e396e0ed90befc908b24a8cba73c4e2', '003-returned.json': '310faf9411ad4bfcbb975b5bd99e682605f3e4e9cd42759ea57ced4ab3ac1bf2'}
NATIVE_DIRS=('.native-region-frame-state','.native-frame-capture-state','.frame-capture-state')

def need(ok,error):o.need(ok,'reboot-'+error)
def digest(value):return hashlib.sha256(o.encode(value)).hexdigest()
def raw(reference):return o.raw(reference)
def doc(reference):return o.doc(reference)
def canonical(p):return o.canonical(Path(p))
def catalogue():
 p=PROJECT/'skills/violation-notifier/references/reboot-failed11-catalogue.json';r=o.ref(p);need(r['sha256']==CATALOGUE_SHA,'fixed-catalogue-changed');c=doc(r)
 for entry in [*c['fixed'].values(),*c['before_sources'],*c['failed_readonly_archives']]:
  archive=PROJECT/entry['archive_relative'];need(o.ref(archive)['sha256']==entry['original']['sha256']==entry['sha256'],'fixed-catalogue-archive-changed')
 return c

def archived(entry):return o.ref(PROJECT/entry['archive_relative'])

def original_bindings(a):
 c=catalogue();v=a['original'];need(a['checkpoint']==c['fixed']['checkpoint']['original'] and a['checkpoint']['sha256']==CHECKPOINT_SHA,'checkpoint-not-decorative');doc(a['checkpoint'])
 for key in ('parent','engine'):
  need(v[key]==archived(c['fixed'][key]),'exact-original-'+key)
 for key in ('request','response','exit','order','source','job','query','profile','observation'):
  need(v[key]==c['fixed'][key]['original'],'exact-original-'+key)
 need(doc(v['task'])==c['task'],'exact-original-task-bytes')
 need(doc(v['engine'])['calls'][68]==c['failed_call'],'exact-failed68')
 need(a['failed_readonly_archives']==[{'original':e['original'],'archive':archived(e)} for e in c['failed_readonly_archives']],'exact-failed-reply-binding')
 return c

def release_graph(release_ref,*,source_archives=None):
 c=catalogue();release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1','reviewed-source-release-required');expected={str(PROJECT/p)for p in c['target_paths']};before={v['original']['path']:v for v in c['before_sources']};graph={v['path']:v for v in c['baseline_code_refs']};transitions=[];previous=release.get('previous_release');logical_by={};latest={};patch_by={}
 if previous is not None:
  v1={'path':str(PROJECT/'work/performance-audit/violation-reboot-continuation-candidate/supervisor-release.json'),'sha256':V1_RELEASE_SHA};v2={'path':str(PROJECT/'work/performance-audit/violation-reboot-date-correction-candidate/supervisor-release.json'),'sha256':V2_RELEASE_SHA};need(previous in(v1,v2),'previous-release-not-exact-root-chain');origin=doc(v1);old=[t for t in origin['targets']if t['target']in expected];need(origin.get('kind')=='supervisor-reviewed-source-release-v1'and len(old)==len(expected)and{t['target']for t in old}==expected,'previous-release-exact-thirteen');logical_by={t['target']:t for t in old};latest=dict(logical_by);helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');ports=str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')
  if previous==v2:
   prior=doc(v2);need(prior.get('kind')=='supervisor-reviewed-source-release-v1'and prior.get('previous_release')==v1 and len(prior['targets'])==1 and prior['targets'][0]['target']==helper and prior['targets'][0]['old_sha256']==latest[helper]['after']['sha256']and prior['targets'][0]['after']['sha256']==PRE_DISPATCH_AUTHORITY['source_sha256'],'previous-v2-exact-helper-chain');latest[helper]=prior['targets'][0]
  allowed={helper,ports}if previous==v2 else{helper};patch=release['targets'];need(len(patch)==len(allowed)and{t['target']for t in patch}==allowed,'patch-only-reviewed-finite-targets');patch_by={t['target']:t for t in patch}
  for t in patch:need(t['old_sha256']==latest[t['target']]['after']['sha256'],'patch-real-deployment-CAS');raw(latest[t['target']]['after'])
  selected=[patch_by.get(t['target'],t)for t in old]
 else:
  selected=[t for t in release['targets']if t['target']in expected];need(len(selected)==len(expected)and{t['target']for t in selected}==expected,'exact-thirteen-source-release')
 for t in selected:
  original=before.get(t['target']);logical=logical_by.get(t['target'],t);need(logical.get('old_sha256')==(original['sha256']if original else None),'release-before-not-catalogue');current={'path':t['target'],'sha256':t['after']['sha256']};need(source_reference(current,source_archives)==current and doc(release_ref)==release,'release-after-source-changed');graph[t['target']]=current;entry={'before':original['original']if original else None,'archive':archived(original)if original else None,'current':current}
  if previous is not None:entry.update(previous_release=previous,previous_current={'path':t['target'],'sha256':latest[t['target']]['after']['sha256']},deployment_before_sha256=patch_by[t['target']]['old_sha256']if t['target']in patch_by else None)
  transitions.append(entry)
 for v in graph.values():source_reference(v,source_archives)
 return sorted(transitions,key=lambda v:v['current']['path']),[graph[k]for k in sorted(graph)]

SOURCE_REPAIR_AUTHORITY_SHA='84b80e33f1ee86e72ed2614d5b0bf1e19b01d39a3ca9d9bef4f609ca9aac4eea'
SOURCE_REPAIR_DIRECTORY='work/performance-audit/violation-capture-focus-candidate'
SOURCE_REPAIR_KIND='reviewed-existing-order-source-repair-v1'
def source_reference(reference,archives=None):
 """Finite source-only physical view; never patch shared raw/ref or execute archives."""
 if archives and reference['path'] in archives:
  entry=archives[reference['path']];need(entry['original']==reference and entry['archive']['sha256']==reference['sha256'],'source-archive-exact-binding');raw(entry['archive']);return reference
 raw(reference);return reference

def source_repair_authority():
 r={'path':str(PROJECT/SOURCE_REPAIR_DIRECTORY/'source-repair-authority.json'),'sha256':SOURCE_REPAIR_AUTHORITY_SHA};a=doc(r)
 need(a['kind']=='reviewed-pre-native-source-repair-authority-v1' and a['task_id']==TASK and a['attempt_id']==TASK+'-12','source-repair-authority-scope')
 for entry in a['evidence']+a['before_sources']:
  need(entry['original']['sha256']==entry['archive']['sha256'],'source-repair-archive-binding');raw(entry['archive'])
 return r,a

def repair_evidence(authority,reference):
 matches=[e for e in authority['evidence']if e['original']==reference];need(len(matches)==1,'source-repair-evidence-not-fixed');return doc(matches[0]['archive'])

SOURCE_REPAIR_PATCH_DIRECTORY='work/performance-audit/violation-readonly-display-inventory-candidate'
SOURCE_REPAIR_ROOT_RELEASE_SHA='de2f8159e2c5773cb7f4aafd32a29a8ed130e7c4efd52e2939aa6af09570cd95'
ENVIRONMENT_DIRECTORY='work/performance-audit/quiescent-round-environment-integration-candidate'
EXECUTION_POLICY_SHA='a648f3861b12be7a9605e77bab06cfd42ad617aaffad06958a079f462d40eb2b'
def execution_policy():
 reference={'path':str(PROJECT/ENVIRONMENT_DIRECTORY/'execution-source-delta-v2.json'),'sha256':EXECUTION_POLICY_SHA};value=doc(reference);paths={str(PROJECT/p)for p in ('packages/workshop-director/workshop_director/engine.py','packages/workshop-director/workshop_director/__main__.py','packages/workshop-director/workshop_director/quiescent_lease_handoff.py','skills/workshop-director/scripts/coordinator.py')};need(value['kind']=='finite-quiescent-round-execution-source-delta-v1' and len(value['targets'])==4 and {t['target']for t in value['targets']}==paths,'execution-policy-four-targets')
 for t in value['targets']:
  raw(t['after'])
  if t['before'] is not None:need(t['before']['path']==t['target'] and t['archive']['sha256']==t['before']['sha256'],'execution-policy-before-archive');raw(t['archive'])
 return reference,value

DEPENDENCY_POLICY_SHA='2978a9d3b830bf1a8d58750227f3e4be50322f5771ed1402fcd6515bd833b551'
OPERATOR_DEPENDENCY_POLICY_SHA='821ed6774bf802afcbe44159bc239135fbddd546601846095107e7bb19305e1b'
RETURN_DEPENDENCY_POLICY_SHA='327867b68cedf71e69228c10a015d7a34a8d45c2c329500034937bf2d3012e64'
WECOM_DEPENDENCY_POLICY_SHA='f4624c2196ac44799febf1df507a3aad73ee1dd1be1f34034cdf797ebbbfed34'
DIAGNOSTIC_RELEASE_SHA='c04d0256d88fa3bc148955543461fe677f4c8ad70a96b1692d491b64e3ca6aca'
def diagnostic_deployment():
 r={'path':str(PROJECT/'work/performance-audit/wecom-initial-locate-readonly-diagnostic-candidate/supervisor-release.json'),'sha256':DIAGNOSTIC_RELEASE_SHA};v=doc(r);need(v.get('kind')=='supervisor-reviewed-source-release-v1' and v.get('purpose')=='exact-original-sender-readonly-diagnostic-only' and v.get('published')is True and {t['target']for t in v['targets']}=={str(PROJECT/'skills/wecom-messenger/scripts'/n)for n in ('messenger.py','diagnose_locate.py')} and len(v['targets'])==2,'diagnostic-deployment-exact-reviewed-step')
 archive=o.ref(PROJECT/'work/performance-audit/wecom-initial-locate-readonly-diagnostic-candidate/messenger.py.before');t=next(t for t in v['targets']if Path(t['target']).name=='messenger.py');need(archive['sha256']==t['old_sha256'],'diagnostic-origin-archive');return r,v,{'original':{'path':t['target'],'sha256':t['old_sha256']},'archive':archive}
PREVIEW_DEPENDENCY_POLICY_SHA='70a8dfc2c4642e114b6651e0487c951fb5ec5cffd17f93490e92a658811ecad8'
PAGE_FOCUS_POLICY_SHA='34f289b6063d0a4cb4c53be44ff4bb56e9c977a20991f7191637388a27519169'
PANEL_DIAGNOSTIC_RELEASE_SHA='e1942d1714377430d908b7a8498e23c369221ee13361264b502c6300cc907222'
def panel_diagnostic_deployment():
 r={'path':str(PROJECT/'work/performance-audit/complaint-download-panel-readonly-diagnostic-candidate/supervisor-release.json'),'sha256':PANEL_DIAGNOSTIC_RELEASE_SHA};v=doc(r);need(v.get('kind')=='supervisor-reviewed-source-release-v1' and v.get('purpose')=='exact-original-complaint-capture-panel-readonly-diagnostic-only' and v.get('published') is True and len(v['targets'])==2 and {t['target']for t in v['targets']}=={str(PROJECT/'packages/workshop-director/workshop_director/adapters.py'),str(PROJECT/'skills/negative-review-complaints/scripts/diagnose_capture_download_panel.py')},'panel-diagnostic-exact-reviewed-deployment');return r,v
WINDOW_RAISE_POLICY_SHA='d7e1d7ba83936b170883112062e01164a12ece44fae23af52226e2b4da037814'
WINDOW_DIAGNOSTIC_RELEASE_SHA='5508bb7c2b93e45297d7c192571dc68a552f506166d8853d7ef8e3fe09a80974'
def window_diagnostic_deployment():
 r={'path':str(PROJECT/'work/performance-audit/complaint-exact-window-raise-candidate/readonly-window-diagnostic/supervisor-release.json'),'sha256':WINDOW_DIAGNOSTIC_RELEASE_SHA};v=doc(r);need(v.get('kind')=='supervisor-reviewed-source-release-v1' and v.get('purpose')=='exact-original-complaint-business-window-readonly-diagnostic-only' and v.get('published') is True and len(v['targets'])==2 and {t['target']for t in v['targets']}=={str(PROJECT/'packages/workshop-director/workshop_director/adapters.py'),str(PROJECT/'skills/negative-review-complaints/scripts/diagnose_exact_window.py')},'window-diagnostic-exact-reviewed-deployment');return r,v
QUALITY_SCORE_POLICY_SHA='8c2b9034d97336ed607b67ce83f12a1210f5933e2bd833ed22191e2045002252'
QUALITY_SCORE_RANGE_POLICY_SHA='44fe76079313d04735cf5b67d7da60d2c5cab000fda03b7ddc75ae265fe77aad'
RESULT_WAIT_POLICY_SHA='05f0b23a33901f83eccce8fea0281774d0b231e1d4106819972bbe9a73aef6ee'
EXACT_RECHECK_POLICY_SHA='0ff2226c92a9dffb0880ab9f91cdf1419666dad814698fb28650c893d30c998f'
NAVIGATION_POLICY_SHA='3eec48a65dd2d04c743817c1e40839ac53ea0874af7d0cd5cec50c9fa0a27c67'
CONFIRM_ANCHOR_POLICY_SHA='658c82dfc35c56afa5f9263503f5d0c80fb48ed9e41fe9d9a908f989f4f41a6c'
UNICODE_READ_POLICY_SHA='6877e47b5b40bf49e74a0aaf779a64ad70455aa525ec98cd157b3741181ee3fe'
COMPLETED_REPORT_POLICY_SHA='4bf7e28f4418a242dbaa8032c9aa0a4b1b86fe6070f2d4deb9dbbfb32438dd94'
ENVIRONMENT_RUNTIME_POLICY_SHA='b56deeece84b04afbbfcd26799d2e18224d0840dbfc097bc754a9b678014e4cd'
DURABLE_ENVIRONMENT_POLICY_SHA='360021ea734a56c295356cf183801c9e879bf91ef525529b22a99378d86d63bc'
FOCUS_URL_POLICY_SHA='720fa41305031cc9ebd136cba8256b76c51f48e6542b35396c9dfcb9e4327be9'
REBOOT_NAV_POLICY_SHA='c98df735ba4d86c8ac783d98e55d2de791576e54a10ec1637615b696ba648d95'
ACCEPTANCE_POLICY_SHA='44edc97ccf61b22afed85ee6935030be8a3a2e664a6ee15c387f4679f073e9f2'
EPOCH_PIXEL_POLICY_SHA='ec8e7880a3585a0c044d738629bc4c26d730767e46f46e8745d9d34f03fa6f56'
COMPLETED_FRAME_POLICY_SHA='ea6226f4467f3ddec1f7d41490c5777e4f0a6a16b0544c7667652b0356c54927'
IDENTITY_REUSE_POLICY_SHA='c3e4efb533728cb93c51707781fd881e75a66fc1f043490a7df1c1fe32c7fa53'
ROWS_PIXEL_POLICY_SHA='2443714dffe8a4e0ba7a31b00dc1062e8fb5afbac7c86c6e5a4bf313ca5cf5ef'
ROWS_CHARACTER_DIRECTORY='work/performance-audit/violation-rows-character-range-integration-candidate'
ROWS_CHARACTER_POLICY_SHA='3a086653062e0edf52510f9a88d6d3e7b4f0963797c5761c1b4196a22c4fd39d'
FIRST_CHAIN_DIRECTORY='work/performance-audit/violation-first-screenshot-chain-candidate'
FIRST_CHAIN_POLICY_SHA='c6816f5e3c795a8b6d756cfc327c31be50b176e4a47cca040ea644c78cb4a510'
HISTORY_FACTS_DIRECTORY='work/performance-audit/registration-reboot-pure-scope-rebased-candidate'
HISTORY_FACTS_POLICY_SHA='0ac547403dbd100b1cd6a6900a8a017c4ba768fe0d7fee907bfb3413d34e572f'
CONFIRMED_SENDER_DIRECTORY='work/performance-audit/violation-confirmed-sender-continuation-candidate'
CONFIRMED_SENDER_POLICY_SHA='965769000ebf89e94eb8583bf63b34099e008e89f6d3892a6c5d7cf20d2c9c5f'
PARTIAL_SEND_DIRECTORY='work/performance-audit/violation-partial-send-checkpoint-candidate'
PARTIAL_SEND_POLICY_SHA='b30e0f66dc82bc9d290252599e6e55e512263a5f3d37681dba1c7e4f62758d2a'
NORMAL_PATH_DIRECTORY='work/performance-audit/violation-normal-send-readonly-integration-candidate'
NORMAL_PATH_POLICY_SHA='3ac1d540737169ccb8031a691e1e9d8c441258ba10a95a0b7be65d05e02de511'
NORMAL_PATH_POLICY_KIND='finite-reviewed-normal-dispatch-readonly-settle-dependency-delta-v1'
def dependency_policies():
 return [({'path':str(PROJECT/'work/performance-audit/daily-explicit-rehearsal-nonworkday-candidate/daily-dependency-delta.json'),'sha256':DEPENDENCY_POLICY_SHA},'finite-reviewed-daily-initialization-dependency-delta-v1',('skills/daily-comment-stats/scripts/daily_timed_run.py','skills/workshop-director/scripts/daily_execution_launcher.py','skills/workshop-director/scripts/daily_completed_archive.py')),({'path':str(PROJECT/'work/performance-audit/company-confirmation-loading-settle-candidate/operator-dependency-delta.json'),'sha256':OPERATOR_DEPENDENCY_POLICY_SHA},'finite-reviewed-operator-confirmation-dependency-delta-v1',('skills/douyin-laike-operator/scripts/bridge-workflow.py',)),({'path':str(PROJECT/'work/performance-audit/return-management-merchant-scope-candidate/return-dependency-delta.json'),'sha256':RETURN_DEPENDENCY_POLICY_SHA},'finite-reviewed-return-management-dependency-delta-v1',('skills/douyin-laike-operator/scripts/switch_read_recovery.py',)),({'path':str(PROJECT/'work/performance-audit/wecom-empty-shell-startup-candidate/wecom-dependency-delta.json'),'sha256':WECOM_DEPENDENCY_POLICY_SHA},'finite-reviewed-wecom-startup-dependency-delta-v1',('skills/wecom-messenger/scripts/main_window.py','skills/wecom-messenger/scripts/ui.py','skills/wecom-messenger/scripts/messenger.py','packages/workshop-director/workshop_director/adapters.py')),({'path':str(PROJECT/'work/performance-audit/wecom-startup-preview-partition-candidate/preview-dependency-delta.json'),'sha256':PREVIEW_DEPENDENCY_POLICY_SHA},'finite-reviewed-startup-preview-dependency-delta-v1',('skills/wecom-messenger/scripts/ui.py','skills/wecom-messenger/scripts/messenger.py','packages/workshop-director/workshop_director/adapters.py')),({'path':str(PROJECT/'work/performance-audit/complaint-page-window-focus-candidate/page-focus-dependency-delta.json'),'sha256':PAGE_FOCUS_POLICY_SHA},'finite-reviewed-page-focus-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py','skills/negative-review-complaints/scripts/initial_ledger_recovery.py','skills/negative-review-complaints/scripts/capture_review_region.py','skills/chrome-dom-export/scripts/review_region_capture.py','packages/workshop-director/workshop_director/adapters.py')),({'path':str(PROJECT/'work/performance-audit/complaint-exact-window-raise-candidate/window-raise-dependency-delta.json'),'sha256':WINDOW_RAISE_POLICY_SHA},'finite-reviewed-exact-window-raise-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py','packages/workshop-director/workshop_director/adapters.py')),({'path':str(PROJECT/'work/performance-audit/complaint-quality-score-bullet-candidate/quality-score-dependency-delta.json'),'sha256':QUALITY_SCORE_POLICY_SHA},'finite-reviewed-quality-score-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py','skills/negative-review-complaints/scripts/program_review_quality.py')),({'path':str(PROJECT/'work/performance-audit/complaint-quality-score-range-candidate/quality-score-range-dependency-delta.json'),'sha256':QUALITY_SCORE_RANGE_POLICY_SHA},'finite-reviewed-quality-score-range-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py','skills/negative-review-complaints/scripts/program_review_quality.py')),({'path':str(PROJECT/'work/performance-audit/existing-result-empty-drawer-settle-candidate/result-wait-dependency-delta.json'),'sha256':RESULT_WAIT_POLICY_SHA},'finite-reviewed-empty-result-drawer-dependency-delta-v1',('skills/negative-review-complaints/scripts/existing_result_runner.py', 'skills/negative-review-complaints/scripts/unbound_case_runner.py', 'skills/negative-review-complaints/scripts/case_alias_v3.py', 'skills/negative-review-complaints/scripts/legacy_alias_code_replay.py', 'skills/negative-review-complaints/scripts/review_capture_focus.py', 'skills/negative-review-complaints/scripts/legacy_alias_catalogue_result_wait_v1.json')),({'path':str(PROJECT/'work/performance-audit/complaint-exact-historical-code-candidate/exact-recheck-dependency-delta.json'),'sha256':EXACT_RECHECK_POLICY_SHA},'finite-reviewed-exact-recheck-dependency-delta-v1',('skills/negative-review-complaints/scripts/complaint_exact_recheck.py', 'skills/negative-review-complaints/scripts/review_capture_focus.py')),({'path':str(PROJECT/'work/performance-audit/complaint-recheck-navigation-lifecycle-candidate/navigation-lifecycle-dependency-delta.json'),'sha256':NAVIGATION_POLICY_SHA},'finite-reviewed-navigation-lifecycle-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py',)),({'path':str(PROJECT/'work/performance-audit/complaint-confirm-anchor-path-candidate/confirm-anchor-dependency-delta.json'),'sha256':CONFIRM_ANCHOR_POLICY_SHA},'finite-reviewed-confirm-anchor-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py','skills/douyin-laike-operator/scripts/switch_read_recovery.py')),({'path':str(PROJECT/'work/performance-audit/bridge-unicode-json-candidate/unicode-dependency-delta.json'),'sha256':UNICODE_READ_POLICY_SHA},'finite-reviewed-readonly-unicode-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py', 'skills/chrome-dom-export/scripts/bridge.py', 'skills/douyin-laike-operator/scripts/role_cli.py', 'skills/chrome-dom-export/scripts/bridge-service.py')),({'path':str(PROJECT/'work/performance-audit/complaint-completed-report-membership-candidate/completed-report-dependency-delta.json'),'sha256':COMPLETED_REPORT_POLICY_SHA},'finite-reviewed-completed-report-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py', 'skills/workshop-director/scripts/complaint_execution_orchestration.py', 'packages/workshop-director/workshop_director/adapters.py')),({'path':str(PROJECT/'work/performance-audit/environment-controlled-python-candidate/environment-python-dependency-delta.json'),'sha256':ENVIRONMENT_RUNTIME_POLICY_SHA},'finite-reviewed-controlled-environment-python-dependency-delta-v1',('skills/negative-review-complaints/scripts/review_capture_focus.py',)),({'path':str(PROJECT/'work/performance-audit/environment-durable-child-candidate/environment-child-dependency-delta.json'),'sha256':DURABLE_ENVIRONMENT_POLICY_SHA},'finite-reviewed-durable-environment-child-dependency-delta-v1',()),({'path':str(PROJECT/'work/performance-audit/violation-focus-url-lifecycle-candidate/focus-url-dependency-delta.json'),'sha256':FOCUS_URL_POLICY_SHA},'finite-reviewed-source-bound-focus-url-dependency-delta-v1',('skills/violation-notifier/scripts/violation_execution_ports.py',)),({'path':str(PROJECT/'work/performance-audit/violation-reboot-navigation-root-candidate/reboot-navigation-dependency-delta.json'),'sha256':REBOOT_NAV_POLICY_SHA},'finite-reviewed-reboot-navigation-root-dependency-delta-v1',('skills/chrome-dom-export/scripts/business_cells_capture.py','skills/negative-review-complaints/scripts/review_capture_focus.py')),({'path':str(PROJECT/'work/performance-audit/violation-anchor-epoch-pixel-quality-candidate/epoch-pixel-dependency-delta.json'),'sha256':EPOCH_PIXEL_POLICY_SHA},'finite-reviewed-anchor-epoch-pixel-quality-dependency-delta-v1',('skills/violation-notifier/scripts/program_region_quality.py','skills/violation-notifier/scripts/region_frame_capture.py')),({'path':str(PROJECT/ACCEPTANCE_DIRECTORY/'quality-accept-dependency-delta.json'),'sha256':ACCEPTANCE_POLICY_SHA},'finite-reviewed-quality-acceptance-lifecycle-dependency-delta-v1',('skills/violation-notifier/scripts/registration_validation.py','skills/violation-notifier/scripts/region_frame_capture.py')),({'path':str(PROJECT/COMPLETED_FRAME_DIRECTORY/'completed-frame-dependency-delta.json'),'sha256':COMPLETED_FRAME_POLICY_SHA},'finite-reviewed-completed-frame-consumption-dependency-delta-v1',('skills/violation-notifier/scripts/violation_execution_ports.py',)),({'path':str(PROJECT/IDENTITY_REUSE_DIRECTORY/'identity-reuse-dependency-delta.json'),'sha256':IDENTITY_REUSE_POLICY_SHA},'finite-reviewed-identity-reuse-evidence-lifecycle-dependency-delta-v1',('skills/violation-notifier/scripts/violation_execution_ports.py',)),({'path':str(PROJECT/ROWS_PIXEL_DIRECTORY/'rows-pixel-dependency-delta.json'),'sha256':ROWS_PIXEL_POLICY_SHA},'finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1',('skills/violation-notifier/scripts/program_epoch_rows_quality.py', 'skills/violation-notifier/scripts/region_frame_capture.py', 'skills/violation-notifier/scripts/violation_execution_ports.py', 'skills/violation-notifier/scripts/registration_validation.py')),({'path':str(PROJECT/ROWS_CHARACTER_DIRECTORY/'character-range-dependency-delta.json'),'sha256':ROWS_CHARACTER_POLICY_SHA},'finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1',('skills/violation-notifier/scripts/program_epoch_rows_quality.py', 'skills/violation-notifier/scripts/rows_character_range_quality.py', 'skills/violation-notifier/scripts/region_frame_capture.py', 'skills/violation-notifier/scripts/registration_validation.py')),({'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'first-chain-dependency-delta.json'),'sha256':FIRST_CHAIN_POLICY_SHA},'finite-reviewed-first-screenshot-chain-default-dependency-delta-v1',('skills/violation-notifier/scripts/violation_execution_ports.py',)),({'path':str(PROJECT/HISTORY_FACTS_DIRECTORY/'history-facts-dependency-delta.json'),'sha256':HISTORY_FACTS_POLICY_SHA},'finite-reviewed-registration-history-facts-dependency-delta-v1',('skills/violation-notifier/scripts/registration_validation.py','skills/violation-notifier/scripts/violation_execution_ports.py')),({'path':str(PROJECT/CONFIRMED_SENDER_DIRECTORY/'confirmed-sender-dependency-delta.json'),'sha256':CONFIRMED_SENDER_POLICY_SHA},'finite-reviewed-registration-history-facts-dependency-delta-v1',()),({'path':str(PROJECT/PARTIAL_SEND_DIRECTORY/'partial-send-dependency-delta.json'),'sha256':PARTIAL_SEND_POLICY_SHA},'finite-reviewed-registration-history-facts-dependency-delta-v1',()),({'path':str(PROJECT/NORMAL_PATH_DIRECTORY/'normal-path-dependency-delta.json'),'sha256':NORMAL_PATH_POLICY_SHA},NORMAL_PATH_POLICY_KIND,('skills/violation-notifier/scripts/workflow.py','skills/violation-notifier/scripts/violation_execution_ports.py','skills/wecom-messenger/scripts/native.py'))]

def dependency_policy(reference=None):
 choices=dependency_policies();reference=reference or choices[-1][0];hits=[v for v in choices if v[0]==reference];need(len(hits)==1,'dependency-policy-exact-reviewed-ref');_,kind,rels=hits[0];value=doc(reference);paths={str(PROJECT/p)for p in rels};need(value['kind']==kind and len(value['targets'])==len(paths) and {t['target']for t in value['targets']}==paths,'dependency-exact-reviewed-targets')
 need(value['authorization_release']=={'path':str(PROJECT/ENVIRONMENT_DIRECTORY/'supervisor-release.json'),'sha256':'182fcd5bc6e38f3fb6f13e1dd1fe79d90d6d5aba67626bb6bcfd3b9c64e7101c'},'daily-dependency-exact-authorization')
 for t in value['targets']:
  if t['before']is None:
   need(((kind=='finite-reviewed-empty-result-drawer-dependency-delta-v1' and t['target']==str(PROJECT/'skills/negative-review-complaints/scripts/legacy_alias_catalogue_result_wait_v1.json')) or (kind=='finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1' and t['target']==str(PROJECT/'skills/violation-notifier/scripts/program_epoch_rows_quality.py')) or (kind=='finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1' and t['target']==str(PROJECT/'skills/violation-notifier/scripts/rows_character_range_quality.py'))) and t['archive']is None,'dependency-only-reviewed-new-module-or-catalogue');raw(t['after']);continue
  original=t.get('origin_before',t['before']);need(t['before']['path']==original['path']==t['target'] and t['archive']['sha256']==original['sha256'],'daily-dependency-exact-archive');raw(t['archive']);raw(t['after'])
  if 'origin_before'in t:
   _,dv,da=diagnostic_deployment();dt=next(x for x in dv['targets']if x['target']==t['target']);need(da['original']==original and dt['after']==t['deployment_archive'] and t['before']=={'path':t['target'],'sha256':dt['after']['sha256']},'diagnostic-real-deployment-before');raw(t['deployment_archive'])
 return reference,value

def dependency_release(authorization):
 pr,p=dependency_policy()
 if authorization!=p['authorization_release']:return authorization
 r=o.ref(PROJECT/NORMAL_PATH_DIRECTORY/'supervisor-release.json');verify_dependency_release(r,authorization)
 return r

def verify_dependency_release(reference,authorization):
 v=doc(reference);pr,p=dependency_policy(v.get('source_repair_dependency_delta'));need(v.get('source_repair_dependency_delta')==pr and v.get('previous_release')==p.get('previous_release',authorization) and v.get('source_repair_authorization_release')==authorization==p['authorization_release'],'dependency-reviewed-authorization');return reference

def effective_codes(original,mapping):
 # Existing releases retain byte-equivalent ordering. Only the finite reviewed
 # new execution dependencies are appended and the full resulting set sorted.
 result=[mapping.get(v['path'],v)for v in original];known={v['path']for v in original};extra=[mapping[k]for k in mapping if k not in known]
 return sorted(result+extra,key=lambda v:v['path']) if extra else result

def metadata_release_parent(release_ref,expected):
 release=doc(release_ref)
 if release_ref==expected:return True
 if release_ref==window_diagnostic_deployment()[0]:return metadata_release_parent(release['previous_release'],expected)
 if release_ref==panel_diagnostic_deployment()[0]:return metadata_release_parent(release['previous_release'],expected)
 if release_ref==diagnostic_deployment()[0]:return metadata_release_parent(release['previous_release'],expected)
 if release.get('source_repair_dependency_delta') is not None:
  pr,p=dependency_policy(release['source_repair_dependency_delta']);need(release['source_repair_dependency_delta']==pr and release['previous_release']==p.get('previous_release',p['authorization_release']) and release.get('source_repair_authorization_release')==p['authorization_release'],'daily-dependency-metadata-parent');return metadata_release_parent(release['previous_release'],expected)
 if release.get('previous_release')==expected:return True
 pr,policy=execution_policy();need(release.get('source_repair_execution_delta')==pr and release.get('source_repair_parent_release')==expected==policy['metadata_parent_release'],'metadata-parent-explicit-existing-record')
 point=release['previous_release'];seen=set()
 while point!=expected:
  need(point['sha256']not in seen and len(seen)<32,'metadata-parent-bounded-review-chain');seen.add(point['sha256']);v=doc(point);need(v.get('kind')=='supervisor-reviewed-source-release-v1' and v.get('source_repair_authority')==release['source_repair_authority'],'metadata-parent-review-authority');point=v['previous_release']
 return True

def source_release(reference,*,_historical=False):
 """Exact de2 origin plus bounded helper-only reviewed deployment CAS chain.
 Historical records select their own immutable graph; only the final selected
 graph may authorize current execution and is checked against physical sources.
 """
 ar,a=source_repair_authority();rootref={'path':str(PROJECT/SOURCE_REPAIR_DIRECTORY/'supervisor-release.json'),'sha256':SOURCE_REPAIR_ROOT_RELEASE_SHA};chain=[];seen=set();selected_ref=reference
 while selected_ref!=rootref:
  path=canonical(selected_ref['path']);need(path.name=='supervisor-release.json' and path.is_relative_to(PROJECT/'work/performance-audit') and selected_ref['sha256']not in seen and len(chain)<64,'source-repair-finite-reviewed-chain');seen.add(selected_ref['sha256']);release=doc(selected_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1' and release.get('source_repair_authority')==ar and type(release.get('previous_release'))is dict,'source-repair-followup-release-binding');chain.append(release);selected_ref=release['previous_release']
 origin=doc(rootref);need(origin.get('kind')=='supervisor-reviewed-source-release-v1' and origin.get('source_repair_authority')==ar and origin.get('previous_release')==a['previous_release'],'source-repair-reviewed-release-binding')
 before={e['original']['path']:e for e in a['before_sources']};targets=origin.get('targets',[]);need(len(targets)==len(before) and {t['target']for t in targets}==set(before),'source-repair-finite-target-set');selected={t['target']:t for t in targets}
 for t in targets:need(t['old_sha256']==before[t['target']]['original']['sha256'],'source-repair-deployment-CAS');raw(t['after'])
 helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py')
 for release in reversed(chain):
  patch=release.get('targets',[]);allowed={helper}
  if release in (panel_diagnostic_deployment()[1],window_diagnostic_deployment()[1]):
   allowed=set()
   for t in patch:
    target=t['target'];allowed.add(target)
    if target not in selected:selected[target]={'after':{'path':target,'sha256':t['old_sha256']}if t['old_sha256']else None}
  if release==diagnostic_deployment()[1]:
   allowed=set();_,_,archive=diagnostic_deployment()
   for t in patch:
    target=t['target'];need(target not in selected,'diagnostic-previous-logical-target');selected[target]={'after':{'path':target,'sha256':t['old_sha256']}if t['old_sha256']else None};allowed.add(target)
    if target==archive['original']['path']:before[target]=archive
  if release.get('source_repair_ports_delta')is not None:
   pr={'path':str(PROJECT/NATIVE_FOCUS_DIRECTORY/'ports-delta.json'),'sha256':PORTS_DELTA_SHA};need(release['source_repair_ports_delta']==pr,'source-repair-finite-ports-policy');policy=doc(pr);ports=str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py');need(policy['kind']=='finite-reviewed-ports-focus-delta-v1' and policy['target']==ports and policy['before']=={'path':ports,'sha256':selected[ports]['after']['sha256']},'source-repair-ports-before-policy');pt=[t for t in patch if t['target']==ports];need(len(pt)==1 and pt[0]['after']==policy['after'],'source-repair-ports-after-policy');allowed.add(ports)
  if release.get('source_repair_dependency_delta') is not None:
   pr,dp=dependency_policy(release['source_repair_dependency_delta']);need(release['source_repair_dependency_delta']==pr and release['previous_release']==dp.get('previous_release',dp['authorization_release']) and release.get('source_repair_authorization_release')==dp['authorization_release'],'daily-dependency-exact-release-step');need(selected[helper]['after']['sha256']==dp['helper_before']['sha256'],'daily-dependency-helper-before')
   if dp['kind']=='finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1':
    runtime=dp['runtime_data'];need(len(runtime)==3 and {t['target']for t in runtime}=={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('rows-range-ocr.swift','rows-range-ocr','rows-range-runtime.json')} and release.get('data_targets')==[{'target':t['target'],'old_sha256':t['before']['sha256']if t['before']else None,'after':t['after'],'kind':'fixed-runtime-data','mode':493 if t['target'].endswith('/rows-range-ocr')else 420}for t in runtime],'rows-character-runtime-exact-publication')
    for t in runtime:
     need(t['before']is None and t['archive']is None,'rows-character-only-new-runtime-data');raw(t['after'])
     if not _historical:need(o.ref(Path(t['target']))=={'path':t['target'],'sha256':t['after']['sha256']},'rows-character-runtime-physical-data')
   for pt in dp['targets']:
    target=pt['target'];hits=[t for t in patch if t['target']==target];need(len(hits)==1 and hits[0]['after']==pt['after'] and hits[0]['old_sha256']==(pt['before']['sha256']if pt['before']else None),'daily-dependency-exact-CAS')
    if target not in selected:selected[target]={'after':pt['before']}
    need(selected[target]['after']==pt['before'] or (selected[target]['after']is not None and pt['before']is not None and selected[target]['after']['sha256']==pt['before']['sha256']),'daily-dependency-logical-before')
    if pt['before']is not None:
     if dp['kind']==NORMAL_PATH_POLICY_KIND and target==str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py'):need(before[target]['original']==next(x['admission_material']['original']for x in doc(dp['preserved_original_admission_materials'])['targets']if x['target']==target),'normal-path-preserve-original-ports-material')
     elif dp['kind']in('finite-reviewed-source-bound-focus-url-dependency-delta-v1','finite-reviewed-completed-frame-consumption-dependency-delta-v1','finite-reviewed-identity-reuse-evidence-lifecycle-dependency-delta-v1','finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1','finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1','finite-reviewed-first-screenshot-chain-default-dependency-delta-v1','finite-reviewed-registration-history-facts-dependency-delta-v1'):need((dp['kind']=='finite-reviewed-registration-history-facts-dependency-delta-v1' and target==str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py')) or (dp['kind']=='finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1' and target in {str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('program_epoch_rows_quality.py','region_frame_capture.py','registration_validation.py')}) or (dp['kind']=='finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1' and target in {str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('violation_execution_ports.py','region_frame_capture.py','registration_validation.py')}) or (target==str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py') and target in before and before[target]['original']==next(e['original']for e in a['before_sources']if e['original']['path']==target)),'finite-original-admission-archive-preserved')
     else:before[target]={'original':pt.get('origin_before',pt['before']),'archive':pt['archive']}
    allowed.add(target)
  if release.get('source_repair_execution_delta') is not None:
   er,ep=execution_policy();need(release['source_repair_execution_delta']==er and release['previous_release']==ep['previous_release'],'execution-policy-fixed-reference')
   for pt in ep['targets']:
    target=pt['target'];hits=[t for t in patch if t['target']==target];need(len(hits)==1 and hits[0]['after']==pt['after'] and hits[0]['old_sha256']==(pt['before']['sha256']if pt['before']else None),'execution-policy-exact-CAS');need(target not in selected,'execution-policy-new-logical-target');selected[target]={'after':pt['before']};allowed.add(target)
  need(len(patch)==len(allowed) and{t['target']for t in patch}==allowed,'source-repair-followup-only-reviewed-targets')
  for t in patch:need(t['old_sha256']==(selected[t['target']]['after']['sha256']if selected[t['target']]['after']else None),'source-repair-followup-real-CAS');raw(t['after']);selected[t['target']]=t
 after={}
 for target,t in selected.items():
  current={'path':target,'sha256':t['after']['sha256']}
  if not _historical:need(o.ref(Path(target))==current,'source-repair-after-physical')
  after[target]=current
 # Exact historical Engine bytes remain data-only when the new scheduler source
 # is loaded. The policy cannot change the original admission/source graph.
 if EXECUTION_POLICY_SHA!='PENDING_REVIEWED_FOUR_SOURCE_POLICY':
  _,ep=execution_policy()
  for pt in ep['targets']:
   if pt['before']is not None:before[pt['target']]={'original':pt['before'],'archive':pt['archive']}
 for policyref,_,_ in reversed(dependency_policies()):
  _,dp=dependency_policy(policyref)
  for pt in dp['targets']:
   if pt['before']is not None and dp['kind']not in('finite-reviewed-source-bound-focus-url-dependency-delta-v1','finite-reviewed-completed-frame-consumption-dependency-delta-v1','finite-reviewed-identity-reuse-evidence-lifecycle-dependency-delta-v1','finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1','finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1','finite-reviewed-first-screenshot-chain-default-dependency-delta-v1','finite-reviewed-registration-history-facts-dependency-delta-v1')and not(dp['kind']==NORMAL_PATH_POLICY_KIND and pt['target']==str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')):before[pt['target']]={'original':pt.get('origin_before',pt['before']),'archive':pt['archive']}
 _,_,da=diagnostic_deployment();before[da['original']['path']]=da
 for pr,pk,_ in dependency_policies():
  if pk!='finite-reviewed-six-field-rows-pixel-quality-dependency-delta-v1':continue
  _,dp=dependency_policy(pr);bound=doc(dp['admission_material_authority']);need(dp['admission_material_authority']=={'path':str(PROJECT/ROWS_PIXEL_DIRECTORY/'admission-material-boundaries.json'),'sha256':'91ebf455a13ee59d99a067e9cec73e99ce4fc9cddd51fa83fdd01924ba6d03e4'} and bound['previous_release']==dp['previous_release'],'rows-pixel-fixed-admission-materials')
  for t in dp['targets']:
   if t['before']is None:continue
   hits=[x for x in bound['targets']if x['target']==t['target']];need(len(hits)==1 and hits[0]['deployment_before']==t['before'] and hits[0]['admission_material']==t['admission_material']==before[t['target']],'rows-pixel-original-admission-not-deployment-before');raw(t['admission_material']['archive'])
 for pr,pk,_ in dependency_policies():
  if pk not in ('finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1','finite-reviewed-first-screenshot-chain-default-dependency-delta-v1','finite-reviewed-registration-history-facts-dependency-delta-v1',NORMAL_PATH_POLICY_KIND):continue
  _,dp=dependency_policy(pr);need(dp['preserved_original_admission_materials']=={'path':str(PROJECT/ROWS_PIXEL_DIRECTORY/'admission-material-boundaries.json'),'sha256':'91ebf455a13ee59d99a067e9cec73e99ce4fc9cddd51fa83fdd01924ba6d03e4'},'rows-character-original-admission-authority')
  for t in doc(dp['preserved_original_admission_materials'])['targets']:need(before[t['target']]==t['admission_material'],'rows-character-original-admission-byte-material');raw(t['admission_material']['archive'])
 for pr,pk,_ in dependency_policies():
  if pk!=NORMAL_PATH_POLICY_KIND:continue
  _,dp=dependency_policy(pr);bound=doc(dp['additional_original_materials']);need(bound['kind']=='fixed-workflow-native-original-admission-materials-v1'and {x['target']for x in bound['targets']}=={str(PROJECT/'skills/violation-notifier/scripts/workflow.py'),str(PROJECT/'skills/wecom-messenger/scripts/native.py')}and len(bound['targets'])==2,'normal-path-original-workflow-native-only');admission=doc(bound['admission'])
  for t in bound['targets']:need(t['admission_material']['original']in admission['current_code_refs']and before[t['target']]==t['admission_material'],'normal-path-original-workflow-native-material');raw(t['admission_material']['archive'])
 return a,before,after

def source_failure(authority,base):
 b=repair_evidence(authority,authority['failure']);p=repair_evidence(authority,b['parent']);e=repair_evidence(authority,b['engine']);reply=repair_evidence(authority,b['exact_contract_reply'])
 need(b['kind']=='original-violation-attempt12-provider-proof-focus-failure-v1' and b['exact_error']=='viewport-proof-page-not-focused' and b['reply']=={'ok':False,'error':'viewport-proof-page-not-focused','result':None},'source-repair-only-readonly-focus-failure')
 need(p['reboot_continuation']==e['reboot_continuation']==authority['activation'] and e['order']==p['order']==doc(base['original']['parent'])['order'],'source-repair-original-order')
 need(e['phase']=='frames' and e['index']==1 and len(e['calls'])==71 and e['calls'][70]==b['last_engine_call'] and e['calls'][70]['state']=='failed' and e['calls'][70]['step']=='frames' and e['calls'][70]['error']=='execution-anchor-contract-proof-failed','source-repair-exact-failed70')
 need(e['calls'][:69]==doc(base['original']['engine'])['calls'] and all(c['state']=='returned' for c in e['calls'][69:70]),'source-repair-original-calls-prefix')
 need(reply['reply']==b['reply'] and reply['command']['op']=='viewport-proof' and reply['source']==b['source']==base['original']['source'] and reply['chain_id']==base['capture']['chain'],'source-repair-contract-reply-binding')
 need(b['native_intent_files']==[] and b['new_png_paths']==[] and not e.get('delivery') and e['companies'][1]['artifacts'].get('frames')==[],'source-repair-pre-native-shape')
 child=p['calls'][10];need(len(p['calls'])==11 and child['state']=='returned','source-repair-natural-child')
 launch=repair_evidence(authority,child['launch']);exit=repair_evidence(authority,child['result']);need(exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and exit['returncode']==2 and launch['index']==10 and launch['order']==p['order'],'source-repair-exact-child-exit')
 worker=repair_evidence(authority,b['worker_exit']);request=repair_evidence(authority,worker['request']);response=repair_evidence(authority,worker['response'])
 need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==authority['attempt_id'] and worker['returncode']==0 and response['outcome']=='failed' and request['task']['id']==response['task_id']==TASK,'source-repair-natural-worker-failed')
 return b,p,e

def source_repair_path(activation):return Path(activation['path']).parent/'source-repairs/0001/returned.json'

def verify(reference,*,live_boot=None):
 import registration_validation as validation
 scope=validation.active_history_session()
 if live_boot is None and scope is not None:return scope.reboot_history(reference,_verify_uncached,_verify_history_frontier,_guard_history_frontier)
 return _verify_uncached(reference,live_boot=live_boot)


def _verify_history_frontier(reference):
 """Negative existence and complete repair-directory membership, not a stat cache.
 Read payloads/returned bytes normally; all other files opened by original verify
 remain tracked by Session. No live owner/DOM/process facts are cached here.
 """
 value=doc(reference);path=Path(reference['path']);activation=path if value.get('kind')=='violation-reboot-activation-v1' else path.parent/'activation.json'
 def entry(p):
  if p.is_symlink():return {'path':str(p),'kind':'symlink'}
  if not p.exists():return {'path':str(p),'kind':'absent'}
  if p.is_file():return {'path':str(p),'kind':'file'}
  if p.is_dir():return {'path':str(p),'kind':'directory'}
  return {'path':str(p),'kind':'other'}
 head=entry(activation)
 if head['kind']=='file':head['reference']=o.ref(activation)
 folder=activation.parent/'source-repairs';directory=entry(folder);children=[]
 if directory['kind']=='directory':
  for child in sorted(folder.iterdir()):
   item=entry(child)
   if item['kind']=='directory':
    item['members']=[entry(member)for member in sorted(child.iterdir())];returned=child/'returned.json';item['returned']=entry(returned)
    if item['returned']['kind']=='file':item['returned']['reference']=o.ref(returned)
   children.append(item)
 return {'kind':'same-pure-scope-R-history-frontier-v1','input':reference,'activation':head,'repair_directory':directory,'children':children}


def _guard_history_frontier(reference,expected):
 need(_verify_history_frontier(reference)==expected,'pure-history-frontier-changed')


def _verify_uncached(reference,*,live_boot=None):
 """Both immutable admission and activation resolve one canonical effective graph.
 No recursive public call: only the private original-admission replay descends.
 """
 value=doc(reference)
 if value.get('kind')==KIND:
  activation_path=Path(reference['path']).parent/'activation.json'
  if activation_path.exists():
   activation=o.ref(activation_path);need(doc(activation).get('kind')=='violation-reboot-activation-v1' and doc(activation).get('admission')==reference,'admission-canonical-activation-mismatch');return _verify_effective_activation(activation,live_boot=live_boot)
  return _verify_admission(reference,live_boot=live_boot)
 return _verify_effective_activation(reference,live_boot=live_boot)

def source_repair_records(activation):
 folder=Path(activation['path']).parent/'source-repairs'
 if not folder.exists():return []
 need(not folder.is_symlink(),'source-repair-directory-symlink');records=[]
 for index,path in enumerate(sorted(folder.iterdir()),1):
  need(index<=16 and path.is_dir() and not path.is_symlink() and path.name==str(index).zfill(4),'source-repair-contiguous-finite-chain');final=path/'returned.json';need(final.is_file(),'source-repair-partial-commit-unknown');records.append(o.ref(final))
 return records

def _verify_effective_activation(reference,*,live_boot=None,release_override=None):
 value=doc(reference)
 if value.get('kind')!='violation-reboot-activation-v1':return _verify_admission(reference,live_boot=live_boot)
 records=source_repair_records(reference)
 if not records:return _verify_admission(reference,live_boot=live_boot)
 returned=doc(records[0]);transition=doc(returned['transition']);need(transition['kind']==SOURCE_REPAIR_KIND and transition['activation']==reference,'source-repair-original-activation')
 authority,before,after=source_release(transition['release'],_historical=True);base=_verify_admission(reference,live_boot=live_boot,source_archives=before);b,parent,engine=source_failure(authority,base)
 need(transition['failure']==authority['failure'] and transition['task_id']==TASK and transition['attempt_id']==authority['attempt_id'] and transition['original_parent']==b['parent'] and transition['original_engine']==b['engine'],'source-repair-exact-checkpoint')
 need(transition['before_code_refs']==base['current_code_refs'],'source-repair-previous-graph');codes=effective_codes(base['current_code_refs'],after);need(transition['after_code_refs']==codes,'source-repair-derived-effective-graph')
 expected_parent=copy.deepcopy(parent);expected_parent.update(status='running',error=None);expected_engine=copy.deepcopy(engine);expected_engine.update(status='running',error=None)
 need(doc(returned['parent_after'])==expected_parent and doc(returned['engine_after'])==expected_engine,'source-repair-only-status-delta');need(transition['inventory']==doc(transition['inventory_ref']) and transition['inventory_checked_under_original_locks']is True,'source-repair-pre-native-inventory-proof')
 failed={'70':engine['calls'][70]};children={'10':parent['calls'][10]}
 for index,rr in enumerate(records[1:],2):
  record=doc(rr);t=doc(record['transition']);need(t['kind']=='appended-existing-order-source-repair-v1' and t['activation']==reference and t['previous_returned']==records[index-2],'source-repair-appended-chain-binding');proof,pp,ee=append_failure(t['append_proof'],{**base,'current_code_refs':codes})
  need(proof['previous_returned']==records[index-2] and t['failure']==proof['failure'] and t['task_id']==TASK and t['attempt_id']==proof['attempt_id'] and t['original_parent']==append_failure_snapshot(proof)['parent'] and t['original_engine']==append_failure_snapshot(proof)['engine'],'source-repair-appended-checkpoint')
  need(doc(t.get('dependency_release',t['release'])).get('source_repair_append_proof')==t['append_proof'] and metadata_release_parent(t['release'],doc(doc(records[index-2])['transition'])['release']),'source-repair-appended-release-step')
  if t.get('dependency_release') is not None:need(verify_dependency_release(t['dependency_release'],t['release'])==t['dependency_release'],'daily-dependency-transition-binding')
  _,_,after=source_release(t.get('dependency_release',t['release']),_historical=True);need(t['before_code_refs']==codes,'source-repair-appended-before-graph');codes=effective_codes(base['current_code_refs'],after);need(t['after_code_refs']==codes,'source-repair-appended-after-graph')
  pp.update(status='running',error=None);ee.update(status='running',error=None);_apply_partial_send_metadata(ee,proof);need(doc(record['parent_after'])==pp and doc(record['engine_after'])==ee,'source-repair-appended-only-status-delta');need(t['inventory']==doc(t['inventory_ref']) and t['inventory_checked_under_original_locks']is True,'source-repair-appended-inventory-proof');failed[str(proof['engine_index'])]=ee['calls'][proof['engine_index']];children[str(proof['child_index'])]=pp['calls'][proof['child_index']]
 latest=doc(doc(records[-1])['transition']);_,_,effective=source_release(release_override or (dependency_release(latest['release']) if latest.get('dependency_release') is not None else latest['release']));codes=effective_codes(base['current_code_refs'],effective)
 extra_child=_quality_acceptance_child(release_override or (dependency_release(latest['release']) if latest.get('dependency_release') is not None else latest['release']),base)
 if extra_child is not None:children['16']=extra_child
 return {**base,'current_code_refs':codes,'source_repair':records[-1],'source_transition':doc(records[-1])['transition'],'source_repairs':records,'historical_failed_calls':failed,'historical_child_calls':children}

APPEND_PROOF_SHA='5622e18a9387991074d1c0a10002cb3c3acf444afc9725298bf86d073ec1bbd1'
APPEND_DIRECTORY='work/performance-audit/violation-admission-effective-graph-candidate'
def proof_document(proof,reference):
 found=[e for e in proof['evidence']if e['original']==reference];need(len(found)==1,'append-evidence-exact-membership');return doc(found[0]['archive'])

def append_failure_snapshot(proof):
 value=proof_document(proof,proof['failure'])
 if proof['kind']=='exact-completed-frame-focus-before-consumption-failure-proof-v1':return {**value,'parent':value['parent_snapshot']['ref'],'engine':value['engine_snapshot']['ref']}
 if proof['kind']=='exact-source-bound-environment-focus-url-preinput-failure-proof-v1':return {**value,'parent':value['old_task']['parent'],'engine':value['old_task']['engine']}
 return value

def _append_profile_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/APPEND_DIRECTORY/'append-proof.json'),'sha256':APPEND_PROOF_SHA},'append-proof-fixed-reference');proof=doc(reference)
 need(proof['kind']=='exact-readonly-profile-initialization-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-13' and proof['engine_index']==71 and proof['child_index']==11,'append-proof-exact-scope')
 for entry in proof['evidence']+proof['guard_sources']:
  need(entry['original']['sha256']==entry['archive']['sha256'],'append-archive-exact-bytes');raw(entry['archive'])
 b=proof_document(proof,proof['failure']);parent=proof_document(proof,b['parent']);engine=proof_document(proof,b['engine']);previous=proof_document(proof,proof['previous_returned']);pp=proof_document(proof,previous['parent_after']);ee=proof_document(proof,previous['engine_after'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-previous-returned-immutable')
 need(b['kind']=='violation13-reboot-profile-prior-admission-source-read-failure-v1' and b['error']=='execution-reference-changed' and b['pure_diagnostic']['RPC']==0 and b['pure_diagnostic']['UI']==0 and b['new_native_or_png']is False,'append-only-profile-preinput-failure')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'],'append-original-order-activation')
 need(len(engine['calls'])==72 and len(parent['calls'])==12 and engine['calls'][:-1]==ee['calls'] and parent['calls'][:-1]==pp['calls'],'append-original-calls-prefix')
 last=engine['calls'][71];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['context']==engine['calls'][70]['context'] and last['error']=='execution-reference-changed' and 'result'not in last,'append-exact-failed71')
 expected=copy.deepcopy(ee);expected.update(calls=engine['calls'],status='hold',error='execution-reference-changed');need(engine==expected,'append-no-other-engine-delta');expected=copy.deepcopy(pp);expected.update(calls=parent['calls'],status='hold',error='execution-child-stopped');need(parent==expected,'append-no-other-parent-delta')
 child=parent['calls'][11];launch=proof_document(proof,child['launch']);exit=proof_document(proof,child['result']);need(child['state']=='returned' and child['result']==b['child_exit'] and exit['returncode']==2 and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==11 and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'] and json.loads(exit['stdout'])=={'ok':False,'error':'execution-reference-changed'},'append-natural-child-exact')
 worker=proof_document(proof,proof['worker_exit']);request=proof_document(proof,worker['request']);response=proof_document(proof,worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-natural-worker-exact')
 # Side-effect-free guard ordering is proven from exact old executable bytes,
 # not absence alone; the typed no-native inventory is separately made in locks.
 guards={Path(e['original']['path']).name:e for e in proof['guard_sources']}
 for entry in guards.values():need(entry['original']in base['current_code_refs'],'append-guard-source-was-current')
 ports=ast.parse(raw(guards['violation_execution_ports.py']['archive']));klass=next(n for n in ports.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');frames=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='_frames');calls=[n for n in ast.walk(frames)if isinstance(n,ast.Call)];constructor=next(n for n in calls if ast.unparse(n.func)=='screenshot_nav.Runner');focus=next(n for n in calls if ast.unparse(n.func)=='self.ensure_capture_focus');need(constructor.lineno<focus.lineno,'append-runner-before-focus')
 nav=ast.parse(raw(guards['records_region_navigation.py']['archive']));klass=next(n for n in nav.body if isinstance(n,ast.ClassDef)and n.name=='Runner');init=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='__init__');calls=[n for n in ast.walk(init)if isinstance(n,ast.Call)];validate=next(n for n in calls if ast.unparse(n.func)=='profile_api.validate');mkdir=next(n for n in calls if ast.unparse(n.func)=='self.folder.mkdir');need(validate.lineno<mkdir.lineno and not any(ast.unparse(n.func)in('self.invoke','self.request')for n in calls),'append-profile-before-io-no-rpc')
 return proof,parent,engine

FOCUS_URL_DIRECTORY='work/performance-audit/violation-focus-url-lifecycle-candidate'
FOCUS_URL_PROOF_SHA='b282f218114d6cdfd5d25b651e7cdec0e7e7b0379df42efcc6cf53219ab955a3'
def _append_focus_url_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/FOCUS_URL_DIRECTORY/'append-proof.json'),'sha256':FOCUS_URL_PROOF_SHA},'append-focus-url-fixed-proof');proof=doc(reference)
 need(proof['kind']=='exact-source-bound-environment-focus-url-preinput-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-15' and proof['engine_index']==73 and proof['child_index']==13,'append-focus-url-scope')
 for entry in proof['evidence']:need(entry['original']['sha256']==entry['archive']['sha256'],'append-focus-url-archive');raw(entry['archive'])
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(b['old_task']['parent']);engine=get(b['old_task']['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after']);need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-focus-url-previous-immutable')
 need(b['kind']=='old-violation15-environment-complete-focus-binding-failure-v1' and b['old_task']['leaf']=='execution-capture-focus-binding-changed' and b['old_task']['attempt']==15 and parent['reboot_continuation']==engine['reboot_continuation']==proof['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'],'append-focus-url-original-scope')
 completion=get(proof['environment_completion']);grant=get(completion['grant']);plan=get(proof['checkpoint_intent']);receipt=get(proof['checkpoint_returned']);before=get(plan['before_archive']);after=get(plan['after'])
 need(completion['kind']=='source-bound-records-environment-restored-v1' and completion['binding']==grant['environment_restore'] and grant['activation']==proof['activation'] and grant['task_id']==TASK and completion['binding']['source']==base['original']['source'] and completion['binding']['job']==base['original']['job'] and completion['original_refs']=={k:base['original'][k]for k in('source','job','query','profile','observation')} and completion['scope']==base['effective_scope'] and completion['boot']==base['effective_process']['boot'] and completion['business_ledgers_written']is False and completion['notifications_sent']is False,'append-focus-url-environment-binding')
 need(plan['kind']=='source-bound-environment-checkpoint-intent-v1' and plan['completion']==receipt['completion']==proof['environment_completion'] and receipt['intent']==proof['checkpoint_intent'] and receipt['after']=={'path':b['old_task']['engine']['path'],'sha256':plan['after']['sha256']} and plan['before']['sha256']==plan['before_archive']['sha256'] and before==ee,'append-focus-url-checkpoint-prefix')
 expected=copy.deepcopy(before);a=expected['companies'][1]['artifacts'];nested=copy.deepcopy(a.get('reboot_capture',{}));frame=copy.deepcopy(nested.get('frame_state',{'phase':'capture','observation':base['fresh_observation']}));need(frame['phase']=='capture','append-focus-url-capture-only');frame.update(observation=completion['observation'],navigation_checkpoint=completion['navigation'],reboot_current_observation=True);nested.update(frame_state=frame,environment_restoration=proof['environment_completion']);a['reboot_capture']=nested;need(after==expected and after['calls']==ee['calls'],'append-focus-url-only-environment-delta')
 observation=get(completion['observation']);need(completion['observation']==b['current_observation'] and environment_page(observation,base)==completion['page'],'append-focus-url-original-DOM-facts')
 state=get(completion['state']);navigation=get(completion['navigation_snapshot']);query=get(completion['corrective_query']);need(state['phase']=='complete' and state['grant']==completion['grant'] and state['steps']==14 and completion['navigation_snapshot']['sha256']==completion['navigation']['sha256'] and navigation['last_observation']==completion['observation'] and navigation['binding']['source']==base['original']['source'] and query['phase']=='capture-complete' and all(c['state']=='confirmed'for c in query['calls']) and not any(query.get(k)for k in('hold','error','last_error')),'append-focus-url-completed-checkpoint')
 need(len(engine['calls'])==74 and len(parent['calls'])==14 and engine['calls'][:-1]==ee['calls'] and parent['calls'][:-1]==pp['calls'],'append-focus-url-call-prefix');last=engine['calls'][73];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['context']['order']==doc(parent['order']) and last['error']=='execution-capture-focus-binding-changed' and 'result'not in last,'append-focus-url-failed73')
 expected=copy.deepcopy(after);expected.update(calls=engine['calls'],status='hold',error='execution-capture-focus-binding-changed');need(engine==expected,'append-focus-url-only-engine-delta');expected=copy.deepcopy(pp);expected.update(calls=parent['calls'],status='hold',error='execution-child-stopped');need(parent==expected,'append-focus-url-only-parent-delta')
 focus=get(b['capture_focus']);binding=focus['binding'];need(focus['kind']=='violation-frame-focus-v1' and focus['events']==[] and len(focus['reads'])==1 and binding['source']==base['original']['source'] and binding['profile']==base['derived_profile'] and binding['chain']==base['capture']['chain'] and binding['pid']==base['effective_scope']['pid'] and binding['tab_id']==observation['tab']['tabId']==base['effective_scope']['tab_id'] and binding['window_id']==observation['tab']['windowId']==base['effective_scope']['window_id'],'append-focus-url-no-input-binding')
 need(binding['url']==b['binding_difference']['url']['saved'] and observation['tab']['url']==b['binding_difference']['url']['current'] and binding['url']!=observation['tab']['url'],'append-focus-url-exact-difference');read=get(focus['reads'][0]);need(read['command']=={'op':'tabs'} and read['reply'].get('ok')is True,'append-focus-url-old-readonly')
 child=parent['calls'][13];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned' and exit['returncode']==2 and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==13 and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'] and json.loads(exit['stdout'])=={'ok':False,'error':'execution-capture-focus-binding-changed'},'append-focus-url-natural-child')
 worker=get(proof['worker_exit']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-focus-url-natural-worker')
 guard=next(e for e in proof['evidence']if e['original']==proof['guard_source']);need(proof['guard_source']in doc(previous['transition'])['after_code_refs'],'append-focus-url-guard-code');tree=ast.parse(raw(guard['archive']));klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='ensure_capture_focus');guardnode=next(n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='execution-capture-focus-binding-changed');sample=next(n for n in fn.body if isinstance(n,ast.With));later=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and ast.unparse(n.func)in('self.request','activate_original_chrome','wf.tick')];need(later and all(n.lineno>guardnode.lineno for n in later),'append-focus-url-guard-before-input')
 return proof,parent,engine

REBOOT_NAV_DIRECTORY='work/performance-audit/violation-reboot-navigation-root-candidate'
REBOOT_NAV_PROOF_SHA='49ce90f3a675b34cd73dd54e380f93d59998953a5efed43d7a721a4bcf609c6a'
def _append_navigation_profile_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/REBOOT_NAV_DIRECTORY/'append-proof.json'),'sha256':REBOOT_NAV_PROOF_SHA},'append-reboot-nav-fixed-proof');proof=doc(reference);need(proof['kind']=='exact-reboot-navigation-profile-preinput-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-16' and proof['engine_index']==74 and proof['child_index']==14,'append-reboot-nav-scope')
 for e in proof['evidence']:need(e['original']['sha256']==e['archive']['sha256'],'append-reboot-nav-archive');raw(e['archive'])
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(b['parent']);engine=get(b['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after']);need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-reboot-nav-previous-immutable')
 need(b['kind']=='old-violation16-canonical-navigation-capture-profile-mismatch-v1' and b['task']==TASK and b['attempt']==16 and b['leaf']=='business-navigation-capture-profile-scope-changed' and b['PNG_count']==0 and parent['reboot_continuation']==engine['reboot_continuation']==proof['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'],'append-reboot-nav-original-scope')
 need(len(engine['calls'])==75 and len(parent['calls'])==15 and engine['calls'][:-1]==ee['calls'] and parent['calls'][:-1]==pp['calls'],'append-reboot-nav-call-prefix');last=engine['calls'][74];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['error']=='business-navigation-capture-profile-scope-changed' and 'result'not in last and last['context']['order']==doc(parent['order']),'append-reboot-nav-failed74')
 expected=copy.deepcopy(ee);expected.update(calls=engine['calls'],status='hold',error=b['leaf']);need(engine==expected,'append-reboot-nav-only-engine-delta');expected=copy.deepcopy(pp);expected.update(calls=parent['calls'],status='hold',error='execution-child-stopped');need(parent==expected,'append-reboot-nav-only-parent-delta')
 capture=get(b['capture_profile']);navigation=get(b['canonical_navigation']);old_profile=get(b['navigation_profile']);need(b['source']==base['original']['source'] and b['capture_profile']==base['derived_profile'] and capture['derivation']['kind']=='governance-records-reboot-derived-profile-v1' and capture['derivation']['reboot_continuation']==doc(proof['activation'])['admission'] and navigation['binding']['source']==b['source'] and navigation['binding']['profile']==b['navigation_profile'] and old_profile['derivation']['kind']=='governance-records-derived-profile-v1' and {k:v for k,v in capture.items()if k!='evidence_contract'}!={k:v for k,v in old_profile.items()if k!='evidence_contract'} and all(op['state']=='complete'for op in navigation['operations']),'append-reboot-nav-exact-old-root-mismatch')
 need(len(b['focus_revisions'])==1,'append-reboot-nav-one-focus-epoch');revision=b['focus_revisions'][0];focus=get(revision['journal']);need(focus['kind']=='violation-frame-focus-v1' and focus['events']==revision['events']==[] and focus['reads']==revision['reads'] and len(focus['reads'])==2 and focus['binding']['source']==b['source'] and focus['binding']['profile']==b['capture_profile'] and focus['binding']['chain']==base['capture']['chain'] and focus['revision_authority']['environment']==proof['environment_completion'],'append-reboot-nav-readonly-focus');read=get(focus['reads'][0]);front=get(focus['reads'][1]);need(read['command']=={'op':'tabs'} and read['reply'].get('ok')is True and front['tabs_reply']==focus['reads'][0] and front['frontmost_source']=='public-expected-PID-AXFrontmost-and-CG-first-ordinary-v1','append-reboot-nav-two-readonly-observations')
 child=parent['calls'][14];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned' and exit['returncode']==2 and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==14 and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'] and json.loads(exit['stdout'])=={'ok':False,'error':b['leaf']},'append-reboot-nav-natural-child')
 worker=get(proof['worker_exit']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-reboot-nav-natural-worker')
 guards={Path(r['path']).name:r for r in proof['guard_sources']};need(all(r in doc(previous['transition'])['after_code_refs']for r in guards.values()),'append-reboot-nav-old-code-graph')
 def syntax(r):return ast.parse(raw(next(e['archive']for e in proof['evidence']if e['original']==r)))
 tree=syntax(guards['business_cells_capture.py']);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='no_unresolved_navigation');need(not any(isinstance(n,ast.Call)and ast.unparse(n.func)in('self.request','request','invoke','capture','subprocess.run','subprocess.Popen')for n in ast.walk(fn)) and any(isinstance(n,ast.Constant)and n.value=='business-navigation-capture-profile-scope-changed'for n in ast.walk(fn)),'append-reboot-nav-pure-guard')
 tree=syntax(guards['violation_execution_ports.py']);klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='capture_identity_anchor');calls=[n for n in ast.walk(fn)if isinstance(n,ast.Call)];inputs=next(n for n in calls if ast.unparse(n.func)=='region.fc.page_inputs');request=next(n for n in calls if ast.unparse(n.func)=='self.request');need((inputs.lineno,inputs.col_offset)<(request.lineno,request.col_offset),'append-reboot-nav-before-new-proof-request')
 return proof,parent,engine

NATIVE_FOCUS_DIRECTORY='work/performance-audit/violation-native-capture-focus-candidate'
NATIVE_FOCUS_PROOF_SHA='76d401bc4c9312ff96688a3204482593c3e6ed8d8ac3e2085ebf98fce8ed4ce5'
PORTS_DELTA_SHA='9196ccce101a43ca7c54382ec245ca4457af6f5cc98edbcb24e346255468a133'
def append_failure(reference,base):
 if reference=={'path':str(PROJECT/PARTIAL_SEND_DIRECTORY/'append-proof.json'),'sha256':PARTIAL_SEND_PROOF_SHA}:return _append_partial_send_failure(reference,base)
 if reference=={'path':str(PROJECT/CONFIRMED_SENDER_DIRECTORY/'append-proof.json'),'sha256':CONFIRMED_SENDER_PROOF_SHA}:return _append_confirmed_sender_failure(reference,base)
 if reference=={'path':str(PROJECT/ZERO_SEND_DIRECTORY/'append-proof.json'),'sha256':ZERO_SEND_PROOF_SHA}:return _append_zero_send_failure(reference,base)
 if reference=={'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'append-proof.json'),'sha256':FIRST_CHAIN_PROOF_SHA}:return _append_first_chain_failure(reference,base)
 if reference=={'path':str(PROJECT/IDENTITY_REUSE_DIRECTORY/'append-proof.json'),'sha256':IDENTITY_REUSE_PROOF_SHA}:return _append_identity_reuse_failure(reference,base)
 if reference=={'path':str(PROJECT/COMPLETED_FRAME_DIRECTORY/'append-proof.json'),'sha256':COMPLETED_FRAME_PROOF_SHA}:return _append_completed_frame_failure(reference,base)
 if reference=={'path':str(PROJECT/REBOOT_NAV_DIRECTORY/'append-proof.json'),'sha256':REBOOT_NAV_PROOF_SHA}:return _append_navigation_profile_failure(reference,base)
 if reference=={'path':str(PROJECT/FOCUS_URL_DIRECTORY/'append-proof.json'),'sha256':FOCUS_URL_PROOF_SHA}:return _append_focus_url_failure(reference,base)
 if reference=={'path':str(PROJECT/APPEND_DIRECTORY/'append-proof.json'),'sha256':APPEND_PROOF_SHA}:return _append_profile_failure(reference,base)
 need(reference=={'path':str(PROJECT/NATIVE_FOCUS_DIRECTORY/'append-proof.json'),'sha256':NATIVE_FOCUS_PROOF_SHA},'append-proof-fixed-reference');proof=doc(reference)
 need(proof['kind']=='exact-readonly-viewport-focus-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-14' and proof['engine_index']==72 and proof['child_index']==12,'append-native-focus-scope')
 for entry in proof['evidence']:need(entry['original']['sha256']==entry['archive']['sha256'],'append-native-focus-archive');raw(entry['archive'])
 b=proof_document(proof,proof['failure']);parent=proof_document(proof,b['parent']);engine=proof_document(proof,b['engine']);previous=proof_document(proof,proof['previous_returned']);pp=proof_document(proof,previous['parent_after']);ee=proof_document(proof,previous['engine_after'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-native-previous-immutable')
 need(b['kind']=='violation14-browser-focus-ready-page-focus-rejected-v1' and b['reply']=={'ok':False,'error':'viewport-proof-page-not-focused','result':None} and b['new_activation_dispatched']is False and b['new_native_PNG']is False,'append-native-only-readonly-failure')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'],'append-native-original-order')
 need(len(engine['calls'])==73 and len(parent['calls'])==13 and engine['calls'][:-1]==ee['calls'] and parent['calls'][:-1]==pp['calls'],'append-native-calls-prefix');last=engine['calls'][72];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['context']==engine['calls'][71]['context'] and last['error']=='execution-anchor-contract-proof-failed' and 'result'not in last,'append-native-failed72')
 expected=copy.deepcopy(ee);expected.update(calls=engine['calls'],status='hold',error='execution-anchor-contract-proof-failed');need(engine==expected,'append-native-only-engine-delta');expected=copy.deepcopy(pp);expected.update(calls=parent['calls'],status='hold',error='execution-child-stopped');need(parent==expected,'append-native-only-parent-delta')
 contract=proof_document(proof,b['contract_selection']);focus=proof_document(proof,b['capture_focus']);read=proof_document(proof,b['focus_read']);need(contract['reply']==b['reply'] and contract['command']['op']=='viewport-proof' and contract['source']==base['original']['source'] and contract['chain_id']==base['capture']['chain'],'append-native-read-contract')
 need(focus['kind']=='violation-frame-focus-v1' and focus['events']==[] and focus['reads']==[b['focus_read']] and focus['binding']['source']==base['original']['source'] and focus['binding']['chain']==base['capture']['chain'] and focus['binding']['profile']==contract['profile'] and focus['binding']['pid']==contract['pid'] and read['command']=={'op':'tabs'} and read['reply'].get('ok')is True,'append-native-no-focus-input')
 child=parent['calls'][12];launch=proof_document(proof,child['launch']);exit=proof_document(proof,child['result']);need(child['state']=='returned' and exit['returncode']==2 and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==12 and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'] and json.loads(exit['stdout'])=={'ok':False,'error':'execution-anchor-contract-proof-failed'},'append-native-natural-child')
 worker=proof_document(proof,proof['worker_exit']);request=proof_document(proof,worker['request']);response=proof_document(proof,worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-native-natural-worker')
 return proof,parent,engine

def repair_source(release_ref,*,clock,process_reader):
 authorized_release=release_ref;release_ref=dependency_release(release_ref);authority,archives,after=source_release(release_ref);activation=authority['activation'];records=source_repair_records(activation)
 if not records:return _repair_first_source(release_ref,clock=clock,process_reader=process_reader)
 latest=doc(doc(records[-1])['transition'])
 if latest['release']==authorized_release and latest.get('dependency_release',latest['release'])==release_ref:return verify(activation,live_boot=clock.boot())['source_repair']
 if latest['release']==authorized_release:need(doc(release_ref).get('source_repair_append_proof') is not None and doc(release_ref)['source_repair_append_proof']!=latest.get('append_proof'),'daily-dependency-existing-record-conflict')
 base=_verify_effective_activation(activation,live_boot=clock.boot(),release_override=release_ref);proofref=doc(release_ref).get('source_repair_append_proof');proof,parent,engine=append_failure(proofref,base);need(proof['previous_returned']==records[-1] and metadata_release_parent(release_ref,latest['release']),'append-next-reviewed-step');failure=append_failure_snapshot(proof);folder=Path(failure['parent']['path']).parent;path=Path(activation['path']).parent/'source-repairs'/str(len(records)+1).zfill(4)/'returned.json'
 import fcntl,sqlite3
 handles=[]
 try:
  for lp in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   f=lp.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  need(source_repair_records(activation)==records and o.ref(Path(failure['parent']['path']))==failure['parent'] and o.ref(Path(failure['engine']['path']))==failure['engine'],'append-state-raced')
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   db.row_factory=sqlite3.Row;t=db.execute('SELECT * FROM tasks WHERE id=?',(TASK,)).fetchone();need(t and t['state']=='failed' and Path(t['active_attempt']).name==proof['attempt_id'] and json.loads(t['outer'])==base['original']['outer'],'append-current-failed-task');need(not db.execute("SELECT id FROM tasks WHERE state IN ('running','dispatching','unknown')").fetchall(),'append-no-live-unknown');m=db.execute("SELECT state FROM plans WHERE id='morning'").fetchone();owner=db.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();need(m and m[0]=='paused' and owner and json.loads(owner[0])==TASK,'append-owner-morning')
  started=proof_document(proof,proof['worker_started'])['process'];seen=process_reader(started['pid']);need(not seen or seen!=started,'append-old-worker-live')
  inv=partial_send_repair_inventory(base,proof) if proof['kind']=='exact-partial-send-ledger-checkpoint-failure-proof-v1' else confirmed_sender_repair_inventory(base,proof) if proof['kind']=='confirmed-original-sender-postsend-failure-continuation-proof-v1' else zero_send_repair_inventory(base,proof) if proof['kind']=='exact-zero-verified-positive-send-guard-failure-proof-v1' else first_chain_repair_inventory(base,proof) if proof['kind']=='exact-first-screenshot-chain-missing-key-preadd-failure-proof-v1' else identity_reuse_repair_inventory(base,proof) if proof['kind']=='exact-identity-reuse-evidence-immutable-conflict-failure-proof-v1' else completed_frame_repair_inventory(base,proof) if proof['kind']=='exact-completed-frame-focus-before-consumption-failure-proof-v1' else inventory(Path(base['original']['company_folder']),base['original']['source'],base['capture']['key'],Path(base['capture']['out']));ir=o.immutable(path.parent/'inventory.json',inv)
  _,_,oldafter=source_release(latest['release'],_historical=True);beforecodes=latest['after_code_refs'];tr={'kind':'appended-existing-order-source-repair-v1','activation':activation,'previous_returned':records[-1],'append_proof':proofref,'failure':proof['failure'],'release':authorized_release,'dependency_release':release_ref,'task_id':TASK,'attempt_id':proof['attempt_id'],'original_parent':failure['parent'],'original_engine':failure['engine'],'before_code_refs':beforecodes,'after_code_refs':base['current_code_refs'],'inventory':inv,'inventory_ref':ir,'inventory_checked_under_original_locks':True};trr=o.immutable(path.parent/'transition.json',tr);intent=path.parent/'intent.json';need(not intent.exists(),'append-partial-commit-unknown');o.immutable(intent,{'transition':trr,'original_parent':failure['parent'],'original_engine':failure['engine']});parent.update(status='running',error=None);engine.update(status='running',error=None);_apply_partial_send_metadata(engine,proof);pr=o.immutable(path.parent/'parent-after.json',parent);er=o.immutable(path.parent/'engine-after.json',engine);atomic(Path(failure['parent']['path']),parent);atomic(Path(failure['engine']['path']),engine);rr=o.immutable(path,{'transition':trr,'parent_after':pr,'engine_after':er});verify(activation,live_boot=clock.boot());return rr
 finally:
  for f in reversed(handles):f.close()

def historical_failed_call(admission,index,call):
 if index==68:return call==doc(admission['original']['engine'])['calls'][68]
 return str(index) in admission.get('historical_failed_calls',{}) and call==admission['historical_failed_calls'][str(index)]

def historical_child_call(admission,index,call):
 return str(index) in admission.get('historical_child_calls',{}) and call==admission['historical_child_calls'][str(index)]

def _repair_first_source(release_ref,*,clock,process_reader):
 """Metadata-only fixed source transition, under original locks; no retry/input."""
 import fcntl
 authority,before,after=source_release(release_ref);activation=authority['activation'];path=source_repair_path(activation)
 if path.exists():
  result=verify(activation,live_boot=clock.boot());need(doc(result['source_transition'])['release']==release_ref,'source-repair-existing-release-conflict');return result['source_repair']
 base=_verify_admission(activation,live_boot=clock.boot(),source_archives=before);b,parent,engine=source_failure(authority,base);folder=Path(b['parent']['path']).parent;handles=[]
 try:
  for lockpath in (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   f=lockpath.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  need(o.ref(Path(b['parent']['path']))==b['parent'] and o.ref(Path(b['engine']['path']))==b['engine'],'source-repair-original-state-raced')
  import sqlite3
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   db.row_factory=sqlite3.Row;t=db.execute('SELECT * FROM tasks WHERE id=?',(TASK,)).fetchone();need(t is not None and t['state']=='failed' and Path(t['active_attempt']).name==authority['attempt_id'] and json.loads(t['outer'])==base['original']['outer'],'source-repair-original-failed-task');need(not db.execute("SELECT id FROM tasks WHERE state IN ('running','dispatching','unknown')").fetchall(),'source-repair-no-live-or-unknown');m=db.execute("SELECT state FROM plans WHERE id='morning'").fetchone();owner=db.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();need(m and m[0]=='paused' and owner and json.loads(owner[0])==TASK,'source-repair-owner-morning')
  started=repair_evidence(authority,b['worker_started']);seen=process_reader(started['process']['pid']);need(not seen or seen!=started['process'],'source-repair-original-worker-alive')
  inv=inventory(Path(base['original']['company_folder']),base['original']['source'],base['capture']['key'],Path(base['capture']['out']));inventory_ref=o.immutable(path.parent/'inventory.json',inv)
  transition={'kind':SOURCE_REPAIR_KIND,'activation':activation,'release':release_ref,'failure':authority['failure'],'task_id':TASK,'attempt_id':authority['attempt_id'],'original_parent':b['parent'],'original_engine':b['engine'],'before_code_refs':base['current_code_refs'],'after_code_refs':effective_codes(base['current_code_refs'],after),'inventory':inv,'inventory_ref':inventory_ref,'inventory_checked_under_original_locks':True}
  tr=o.immutable(path.parent/'transition.json',transition);intent=path.parent/'intent.json';need(not intent.exists(),'source-repair-partial-commit-unknown');o.immutable(intent,{'transition':tr,'original_parent':b['parent'],'original_engine':b['engine']})
  np=copy.deepcopy(parent);np.update(status='running',error=None);ne=copy.deepcopy(engine);ne.update(status='running',error=None);pr=o.immutable(path.parent/'parent-after.json',np);er=o.immutable(path.parent/'engine-after.json',ne);atomic(Path(b['parent']['path']),np);atomic(Path(b['engine']['path']),ne);result=o.immutable(path,{'transition':tr,'parent_after':pr,'engine_after':er});verify(activation,live_boot=clock.boot());return result
 finally:
  for f in reversed(handles):f.close()

def clock_view(parent,current_boot,current_monotonic,wall_now):
 """Never subtract clocks across boot; even same-new-boot segments cannot pass."""
 a=parent.get('reboot_continuation')
 if not a:return None
 value=verify(a,live_boot=current_boot)
 return {'clock_comparable':False,'elapsed_seconds':None,'acceptance_pass':False,'deadline_exceeded':None,'original_outer':value['original']['outer'],'original_parent_clock':value['original']['parent_clock'],'reboot_continuation':a,'current_segment':{'boot':current_boot,'start_monotonic':value['segment']['start_monotonic'],'active_elapsed_seconds':max(0,current_monotonic-value['segment']['start_monotonic']),'wall_observed_at':wall_now},'cross_boot_total_is_not_30s_evidence':True}

def scope(parent,*,live_boot=None):
 r=parent.get('reboot_continuation')
 if not r:return {'tab_id':parent['tab_id'],'pid':parent['pid']}
 return verify(r,live_boot=live_boot)['effective_scope']

def original_values(task,request,response,exit,parent,engine,order):
 """Exact metadata predicate before any fresh observation is admitted."""
 need(task['id']==TASK and task['flow']==o.FLOW and task['attempt']==11 and task['state']=='failed' and task['error']=='parent-hold-inspect-original','exact-failed11-task')
 need(request['attempt_id']==response['attempt_id']==exit['attempt_id']==ATTEMPT and request['task']['id']==response['task_id']==TASK and exit['returncode']==0 and response['outcome']=='failed' and response['error']==task['error'],'original-natural-receipt')
 need(task['context']['order']==request['context']['order']==response['context']['order']==parent['order']==engine['order'],'original-order-binding')
 need(order['workflow']==o.FLOW and order['day']==task['day'] and order['dispatch_id'].startswith(task['day']+':violation-notifier:'),'original-dispatch')
 need(parent['kind']=='role-execution-launcher-v1' and parent['status']=='hold' and parent['error']=='execution-child-stopped' and parent['boot_identity']==OLD_BOOT and parent['origin']=='fresh' and parent['mode']=='acceptance' and not parent.get('completion'),'exact-original-parent')
 need(task['outer']==request['task']['outer'] and task['outer']['boot']==OLD_BOOT and parent['start_monotonic']>=task['outer']['start_monotonic'],'original-clock')
 need(engine['status']=='hold' and engine['phase']=='frames' and engine['index']==1 and engine.get('error') is not None and engine['companies'][1]['phase']=='frames','exact-engine-frame-hold')
 need(len(engine['calls'])==69 and engine['calls'][68]['step']=='frames' and engine['calls'][68]['company_index']==1 and engine['calls'][68]['state']=='failed' and engine['calls'][68]['error']==ERROR,'exact-readonly-failed68')
 need(all(c['state']=='returned' and c.get('applied') is True for c in engine['calls'][:68]),'other-parent-call-unresolved')
 need(all(c['state']=='returned' for c in parent['calls']),'launcher-child-unknown')
 for c in parent['calls']:
  launched=doc(c['launch']);returned=doc(c['result']);need(returned['launch']==c['launch'] and c['argv']==returned['argv']==launched['argv'],'old-child-natural-binding')
 a=engine['companies'][1]['artifacts'];need(a['frame_index']==0 and a['frames']==[] and a['frame_state']['phase']=='capture' and a['frame_schedule'][0]=={'mode':'anchor','notice':None,'page':1} and not engine.get('delivery'),'exact-pre-native-stage')
 need(order['companies'][1]['company']=='上海老芗汇餐饮管理有限公司' and order['companies'][1]['groupid']=='1764303851132943','exact-company')
 return a

def identity_display_inventory(directory,source,key):
 """Finite completed display journal + its complete read/reference closure.
 No profile regeneration, native operation or UI; normal live proof owns identity.
 """
 directory=canonical(directory);files=[p for p in directory.iterdir()if p.is_file()];need(all(not p.is_symlink() for p in directory.iterdir()) and not any(p.is_dir()for p in directory.iterdir()),'identity-display-flat-canonical');accepted=set();result=[]
 mains=[]
 for path in files:
  if path.suffix=='.json':
   value=doc(o.ref(path))
   if value.get('kind')=='source-bound-screenshot-full-identity-display-v1':mains.append((path,value))
 need(mains,'identity-display-typed-journal-required')
 for path,state in mains:
  b=state['binding'];profile=doc(b['profile']);meta=profile['derivation'];anchor=doc(b['identity']);src=doc(source)
  need(state.get('phase')=='display-identity' and state.get('state')=='complete' and type(state.get('read_attempts'))is int and 1<=state['read_attempts']<=3 and b['source']==source and b['key']in(key+':reboot-current-identity',key+':full-date-identity') and path.name==hashlib.sha256(b['key'].encode()).hexdigest()+'.json','identity-display-completed-bound-key')
  need(b['chain_id']==anchor['chain_id'] and b['pid']==anchor['native_pid'] and type(b['pid'])is int and b['pid']>0 and b['tab_id']==anchor['tab_id']==meta['tab_id'] and b['window_id']==anchor['window_id']==meta['window_id'] and anchor['source']==source and anchor['profile']==b['profile'] and anchor['identity']==src['identity'] and str(anchor['groupid'])==str(src['groupid']) and anchor['job']==meta['job'] and anchor['query']==meta['query'],'identity-display-source-scope-binding')
  need(type(state['calls'])is list and len(state['calls'])<=1 and type(state['observations'])is list and len(state['observations'])==state['read_attempts'] and state['after']==state['observations'][-1] and 'reused_navigation'not in state,'identity-display-complete-read-closure')
  records=[]
  for index,obsref in enumerate(state['observations']):
   expected=directory/(path.stem+'-observation-'+str(index)+'.json');need(obsref==o.ref(expected),'identity-display-observation-path');record=doc(obsref);commands=record['commands'];need(len(commands)==4 and type(record.get('input_scope_ready'))is bool,'identity-display-four-reads')
   wanted=[{'op':'tabs'},{'op':'ping','tabId':b['tab_id']},{'op':'tree','tabId':b['tab_id']},{'op':'tabs'}]
   for count,item in enumerate(commands,1):
    need(item['command']==wanted[count-1] and item['reply'].get('ok')is True and item['reply'].get('error')is None,'identity-display-readonly-success');part=directory/(path.stem+'-read-'+str(index)+'-'+str(count)+'.json');prefix=doc(o.ref(part));need(prefix=={'at':record['at'],'commands':commands[:count]},'identity-display-read-prefix');accepted.add(part)
   rawview=record['raw'];need(rawview['source']=='local-dom-bridge' and rawview['tab_id']==b['tab_id'] and rawview['tree']==commands[2]['reply']['result'] and rawview['tree'].get('truncated')is False,'identity-display-full-tree')
   for item in (commands[0],commands[3]):
    windows=item['reply']['result'];hits=[(w,t)for w in windows for t in w.get('tabs',[])if t.get('tabId')==b['tab_id']];need(len(hits)==1 and hits[0][0]['windowId']==hits[0][1]['windowId']==b['window_id'] and hits[0][1]['url']==rawview['tab']['url'],'identity-display-read-scope')
   u=urlsplit(rawview['tab']['url']);need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and __import__('urllib.parse',fromlist=['parse_qs']).parse_qs(u.query).get('groupid')==[str(src['groupid'])],'identity-display-route');records.append(record);accepted.add(expected)
  if state['calls']:
   call=state['calls'][0];command=call['command'];need(call.get('state')=='confirmed' and call.get('key')==b['key'] and call.get('phase')=='display-identity' and command.get('op')=='hover' and command.get('kind')=='navigation' and command.get('tabId')==b['tab_id'] and command.get('locator',{}).get('by')=='selector','identity-display-known-hover-only')
   import governance_detail as d
   target=d.nav.exact(records[0]['raw']['tree'],anchor['identity']['provider']);need(command['locator']=={'by':'selector','value':target['selector']} and call['result']==state['hover_reply']['result'] and state['hover_reply'].get('ok')is True and state['hover_reply'].get('error')is None and call['result'].get('kind')=='navigation' and all(call['result'].get('hovered',{}).get(k)==target.get(k)for k in('selector','tag','name')),'identity-display-hover-result')
  accepted.add(path);lock=path.with_suffix('.lock')
  if lock.exists():need(lock.stat().st_size==0,'identity-display-nonempty-lock');accepted.add(lock)
 need(set(files)==accepted,'identity-display-unrecognized-or-extra-output')
 return [{'readonly_identity_display':o.ref(p)}for p in sorted(accepted)]

def _capture_focus_journal_inventory(out,source,key,*,journal_out=None):
 """Typed completed/read-only focus closure, never an OS-front assertion."""
 root=journal_out or out;path=root/'capture-focus.json';read_dir=root/'capture-focus-reads';lock=root/'capture-focus.lock'
 if not path.exists():need(not read_dir.exists() and not lock.exists(),'capture-focus-orphan-output');return []
 state=doc(o.ref(path));b=state['binding'];profile=doc(b['profile']);meta=profile['derivation'];src=doc(source);need(state['kind']=='violation-frame-focus-v1' and b['source']==source and b['chain']+':'+out.name==key and b['tab_id']==meta['tab_id'] and b['window_id']==meta['window_id'] and type(b['pid'])is int and b['pid']>0,'capture-focus-inventory-binding');u=urlsplit(b['url']);need(u.scheme=='https' and u.netloc=='life.douyin.com' and u.path=='/p/governance/violation_list' and __import__('urllib.parse',fromlist=['parse_qs']).parse_qs(u.query).get('groupid')==[str(src['groupid'])],'capture-focus-inventory-route')
 need(type(state['events'])is list and type(state['reads'])is list and state['reads'],'capture-focus-inventory-shape');accepted={path};values={}
 for index,r in enumerate(state['reads']):
  p=Path(r['path']);need(p.parent==read_dir and p.name.startswith(str(index).zfill(4)+'-') and p.suffix=='.json' and not p.is_symlink(),'capture-focus-read-path');v=doc(r);accepted.add(p);values[r['path']]=v
  if v.get('command')=={'op':'tabs'}:
   reply=v['reply'];need(reply.get('ok')is True and reply.get('error')is None,'capture-focus-read-success');need('response'not in v or v['response']==reply,'capture-focus-response-binding');hits=[(w,t)for w in reply['result']for t in w.get('tabs',[])if t.get('tabId')==b['tab_id']];need(len(hits)==1 and hits[0][0]['windowId']==hits[0][1]['windowId']==b['window_id'] and hits[0][1]['url']==b['url'] and hits[0][1].get('allowed')is True,'capture-focus-read-scope')
  else:
   need(v.get('frontmost_source')=='public-expected-PID-AXFrontmost-and-CG-first-ordinary-v1' and v['application']=={'pid':b['pid'],'bundle':'com.google.Chrome','terminated':False} and v['tabs_reply']in state['reads'],'capture-focus-public-read-kind');tabs=doc(v['tabs_reply']);need(tabs['reply']['result']==v['tabs'],'capture-focus-public-tabs-binding');ax=v['expected_AXFrontmost'];cg=v['CG_first_ordinary'];need(ax.get('AX_error')==0 and ax.get('present')is True and type(ax.get('value'))is bool and cg.get('kCGWindowLayer')==0 and cg.get('kCGWindowIsOnscreen')is True and v['frontmost_pid']==cg['kCGWindowOwnerPID'] and ax['value']==(v['frontmost_pid']==b['pid']),'capture-focus-public-read-authority')
 for index,event in enumerate(state['events']):
  need(event['state']=='complete' and event['phase']=='capture-focus' and event['revision']==index and len(event['calls'])<=1 and event['reads'] and all(r in state['reads']for r in event['reads']),'capture-focus-unresolved-event')
  for call in event['calls']:
   need(call['state']=='confirmed' and call['key']=='original-frame-focus-'+str(index) and call['phase']=='capture-focus' and call['command']=={'op':'activate','tabId':b['tab_id']} and event['reply'].get('ok')is True and call['result']==event['reply']['result'] and all(call['result'].get(k)==v for k,v in {'tabId':b['tab_id'],'windowId':b['window_id'],'url':b['url'],'active':True,'windowFocused':True}.items()),'capture-focus-unknown-browser-input')
  native=event.get('native_focus')
  if native:
   need(native['state']=='complete' and native['action']=='activate-existing-Chrome-PID-only' and native['binding']==b and native['before']in state['reads'] and native['after']in state['reads'],'capture-focus-unknown-native-input');after=values[native['after']['path']];need(after.get('frontmost_pid')==b['pid'],'capture-focus-native-effect-not-ready')
   if 'result'in native:need(native['result'].get('pid')==b['pid'] and native['result'].get('bundle')=='com.google.Chrome' and native['result'].get('request_accepted')is True and native['result'].get('launch_used')is False,'capture-focus-native-original-result')
 if lock.exists():need(lock.stat().st_size==0 and not lock.is_symlink(),'capture-focus-lock-not-empty');accepted.add(lock)
 need(read_dir.is_dir() and not read_dir.is_symlink() and set(read_dir.iterdir())=={Path(r['path'])for r in state['reads']},'capture-focus-extra-or-missing-read')
 return [{'readonly_capture_focus':o.ref(p)}for p in sorted(accepted)]

def capture_focus_inventory(out,source,key):
 result=_capture_focus_journal_inventory(out,source,key);revisions=out/'capture-focus-revisions'
 if not revisions.exists():return result
 need(revisions.is_dir() and not revisions.is_symlink(),'capture-focus-revisions-type')
 root=o.ref(out/'capture-focus.json');prior=doc(root)
 for folder in sorted(revisions.iterdir()):
  need(folder.is_dir() and not folder.is_symlink(),'capture-focus-revision-directory');path=folder/'capture-focus.json';value=doc(o.ref(path));binding=value['binding'];a=value.get('revision_authority',{})
  need(folder.name==o.digest(binding) and a.get('kind')=='source-bound-environment-focus-url-revision-v1' and a['previous']==root and a['original_binding']==prior['binding'] and {k:v for k,v in binding.items()if k!='url'}=={k:v for k,v in prior['binding'].items()if k!='url'},'capture-focus-revision-exact-parent')
  environment=doc(a['environment']);observation=doc(a['observation']);profile=doc(binding['profile']);meta=profile['derivation'];need(environment['kind']=='source-bound-records-environment-restored-v1' and environment['binding']['source']==source==binding['source'] and environment['binding']['job']==meta['job'] and environment['original_refs']['profile']==meta['original_profile'] and environment['observation']==a['observation'] and environment['scope']=={'pid':binding['pid'],'tab_id':binding['tab_id'],'window_id':binding['window_id']} and observation['tab']['url']==binding['url'] and observation['tab']['tabId']==binding['tab_id'] and observation['tab']['windowId']==binding['window_id'],'capture-focus-revision-environment-binding')
  from urllib.parse import parse_qsl
  left=urlsplit(prior['binding']['url']);right=urlsplit(binding['url']);lq=parse_qsl(left.query,keep_blank_values=True);rq=parse_qsl(right.query,keep_blank_values=True);ld=dict(lq);rd=dict(rq)
  need(left.scheme==right.scheme=='https' and left.netloc==right.netloc=='life.douyin.com' and left.path==right.path=='/p/governance/violation_list' and not left.fragment and not right.fragment and len(ld)==len(lq) and len(rd)==len(rq) and all(rd.get(k)==v for k,v in ld.items()) and set(rd)-set(ld)=={'StartTime','EndTime','enter_from'} and rd['enter_from']=='home_violation_center' and rd['StartTime'].isdigit() and rd['EndTime'].isdigit() and int(rd['StartTime'])<int(rd['EndTime']),'capture-focus-revision-query-transition')
  closure=_capture_focus_journal_inventory(out,source,key,journal_out=folder);need(set(folder.iterdir())=={folder/'capture-focus.json',folder/'capture-focus-reads',*( [folder/'capture-focus.lock']if(folder/'capture-focus.lock').exists()else[])},'capture-focus-revision-extra-output');result.extend(closure)
 return result


def inventory(folder,source,key,out):
 """Enumerate every fixed native store, not merely a missing PNG pathname."""
 folder=canonical(folder);out=canonical(out);result=[]
 names=set(NATIVE_DIRS)|{v.name for v in folder.iterdir() if v.name.startswith('.') and ('native' in v.name or 'frame' in v.name) and 'state' in v.name}
 for name in sorted(names):
  base=folder/name
  if not base.exists():result.append({'directory':str(base),'exists':False});continue
  need(base.is_dir() and not base.is_symlink(),'native-directory-type')
  files=[]
  for p in sorted(base.rglob('*')):
   need(not p.is_symlink(),'native-symlink')
   if p.is_dir():continue
   r=o.ref(p);files.append(r)
   if p.suffix=='.lock':need(p.stat().st_size==0,'nonempty-lock-unreviewed');continue
   # This exact company/source has never issued native capture. Any native
   # state, even a completed one, needs its own reconciliation, not this gate.
   need(False,'native-state-or-intent-present:'+p.name)
  result.append({'directory':str(base),'exists':True,'files':files})
 frames=folder/'frames'
 if frames.exists():
  for candidate in frames.rglob('*'):
   need(not candidate.is_symlink(),'frame-tree-symlink')
   if candidate.is_file():need(candidate.is_relative_to(out),'same-source-other-frame-output-present')
 if out.exists():
  display=out/'identity-display';display_files=set();focus_evidence=capture_focus_inventory(out,source,key);result.extend(focus_evidence);focus_files={Path(e['readonly_capture_focus']['path'])for e in focus_evidence}
  if display.exists():
   result.extend(identity_display_inventory(display,source,key));display_files=set(display.iterdir())
  for p in sorted(out.rglob('*')):
   need(not p.is_symlink(),'capture-output-symlink')
   if p.is_dir():continue
   if p in display_files or p in focus_files:continue
   need(p.suffix=='.json' and p.parent.name in ('proof-replies','contract-selection'),'native-png-or-other-output-present')
   value=json.loads(p.read_bytes());need(not any(k in value for k in ('native_command','captureKey','png','image','capture_metadata')),'native-output-intent-present');result.append({'readonly_output':o.ref(p)})
 return result

def no_live_process(record,current_boot,process_reader):
 need(record.get('boot')!=current_boot,'old-process-boot-not-old')
 observed=process_reader(record['pid'])
 need(not observed or observed!=record,'original-process-still-live')

def _transport_facts(proof,job_ref,query_ref,source_ref,*,new_boot,process_reader=None,require_identity=True,require_active=True,require_original_facts=True):
 """Replay four immutable replies. No new field is supplied from old facts."""
 import governance_detail as d
 import governance_dom as g
 job=doc(job_ref);query=doc(query_ref);source=doc(source_ref);need(proof['boot']==new_boot and new_boot!=OLD_BOOT,'fresh-new-boot-required')
 p=proof['process'];need(p['boot']==new_boot and p['comm']=='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' and type(p['pid']) is int and p['pid']>0 and p.get('started'),'fresh-public-process-identity')
 if process_reader:need(process_reader(p['pid'])=={k:p[k] for k in ('pid','started','boot')},'fresh-process-changed')
 replies=[doc(r) for r in proof['replies']];need(len(replies)==4,'four-original-replies-required')
 for r in replies:need(r.get('ok') is True and r.get('error') is None and 'result' in r,'fresh-transport-failed')
 commands=proof['commands'];tab=proof['tab_id'];need(commands==[{'op':'tabs'},{'op':'ping','tabId':tab},{'op':'tree','tabId':tab},{'op':'tabs'}],'only-four-readonly-commands')
 def candidates(value):
  return [t for packet in value for t in packet.get('tabs',[]) if urlsplit(t.get('url','')).scheme=='https' and urlsplit(t.get('url','')).netloc=='life.douyin.com' and urlsplit(t.get('url','')).path==g.RECORDS and __import__('urllib.parse',fromlist=['parse_qs']).parse_qs(urlsplit(t['url']).query).get('groupid')==[str(job['groupid'])]]
 first=candidates(replies[0]['result']);last=candidates(replies[3]['result']);need(len(first)==len(last)==1 and first[0]==last[0] and first[0]['tabId']==tab and (not require_active or first[0].get('active') is True),'unique-current-existing-records-tab')
 before=d.nav.context(replies[0]['result'],tab,job['groupid']);after=d.nav.context(replies[3]['result'],tab,job['groupid']);need(before==after and before['windowId']==proof['window_id'],'fresh-window-url-changed')
 ping=replies[1]['result'];need(ping.get('version')==d.nav.VERSION and ping.get('safety')=='DOM-only','unreviewed-wire')
 tree=replies[2]['result'];need(tree.get('url')=='https://life.douyin.com'+g.RECORDS,'fresh-tree-route')
 for node in g.nodes(tree):need(not any(v in node.get('name','') for v in ('扫码登录','风险验证','安全验证','账号异常')),'fresh-risk')
 # These existing parsers require all current fields; no update()/defaults from
 # source are used. Dynamic rectification display keeps its published label rule.
 if require_identity:d.nav.identity(tree,job['identity'])
 else:
  provider=d.nav.exact(tree,job['identity']['provider']);need(provider.get('name')==job['identity']['provider'],'current-provider-not-exact')
 page=None
 if require_original_facts:
  page=d.normal_page(tree,job,query)
  original=next(v for v in query['pages'] if v['page']==page['page']);need(page=={k:v for k,v in original.items() if k!='observation'},'fresh-current-record-facts-changed')
 need(job['identity']==source['identity'] and (job['start'],job['end_exclusive'])==(source['start'],source['end_exclusive']),'source-job-facts')
 raw={'source':'local-dom-bridge','not_business_capture':True,'observed_at':proof['observed_at'],'tab_id':tab,'tab':after,'tree':tree}
 return {'observation':raw,'page':page,'scope':{'pid':p['pid'],'tab_id':tab,'window_id':proof['window_id']},'process':p,'boot':new_boot,'current_identity_verified':require_identity,'all_fields_current_not_filled':require_original_facts}

def fresh_facts(proof,job_ref,query_ref,source_ref,*,new_boot,process_reader=None):
 if proof.get('date_correction'):
  checked=verify_date_correction(proof['date_correction']);need({k:v for k,v in proof.items()if k!='date_correction'}==checked['final_four_read'],'date-correction-final-proof-not-bound')
 return _transport_facts(proof,job_ref,query_ref,source_ref,new_boot=new_boot,process_reader=process_reader,require_identity=True)

def _exception_checked(parent,engine,a):
 # Private same-call facts only; no persistent or caller-supplied trust cache.
 need(a.get('kind')==KIND,'typed-admission-required');original=doc(a['original']['engine']);need(engine['order']==original['order'] and engine['calls'][:69]==original['calls'] and parent['calls'][:len(doc(a['original']['parent'])['calls'])]==doc(a['original']['parent'])['calls'],'original-prefix-changed')
 return 68

def exception(parent,engine,admission):
 return _exception_checked(parent,engine,verify(admission))

def allowed_calls(engine,admission):
 a=verify(admission);index=_exception_checked(doc(a['original']['parent']),engine,a)
 return all(c['state']=='returned' or historical_failed_call(a,i,c) for i,c in enumerate(engine['calls']))

def _verify_admission(reference,*,live_boot=None,source_archives=None):
 """Data verification; current boot checked only when authorizing new execution."""
 a=doc(reference)
 if a.get('kind')=='violation-reboot-activation-v1':
  base=_verify_admission(a['admission'],live_boot=live_boot,source_archives=source_archives)
  need(Path(reference['path'])==Path(a['admission']['path']).parent/'activation.json','activation-canonical-path')
  returned_path=Path(reference['path']).parent/'metadata-apply-returned.json';need(returned_path.is_file(),'metadata-apply-outcome-unknown');returned=doc(o.ref(returned_path));need(returned.get('activation')==reference,'metadata-apply-return-binding')
  expected_parent=copy.deepcopy(doc(base['original']['parent']));expected_parent.update(reboot_continuation=reference,status='running',error=None,clock_comparable=False,elapsed_seconds=None,acceptance_pass=False,end_monotonic=None)
  expected_engine=copy.deepcopy(doc(base['original']['engine']));expected_engine.update(reboot_continuation=reference,status='running',error=None)
  need(doc(returned['parent_after'])==expected_parent and doc(returned['engine_after'])==expected_engine,'metadata-after-not-exact-delta')
  need(a['derived_profile']['path']==str(Path(a['admission']['path']).parent/'capture-profile.json') and doc(a['derived_profile'])['derivation']['reboot_continuation']==a['admission'],'activation-profile-binding');need(a['initial_navigation']['path']==str(Path(a['admission']['path']).parent/'initial-navigation.json'),'activation-nav-path');doc(a['initial_navigation']);return {**base,'admission':a['admission'],'activation':reference,'derived_profile':a['derived_profile'],'initial_navigation':a['initial_navigation']}
 need(a.get('kind')==KIND and a.get('task_id')==TASK and a.get('attempt_id')==ATTEMPT and a.get('clock_comparable') is False and a.get('acceptance_pass') is False,'typed-admission-shape')
 original_bindings(a)
 need(Path(reference['path'])==segment_folder(a['segment']['boot'])/'admission.json','admission-canonical-path')
 original=a['original'];task=doc(original['task']);parent=doc(original['parent']);engine=doc(original['engine']);request=doc(original['request']);response=doc(original['response']);ex=doc(original['exit']);order=doc(parent['order']);original_values(task,request,response,ex,parent,engine,order)
 need(original['outer']==task['outer'] and original['parent_clock']=={k:parent[k] for k in ('boot_identity','start_monotonic','wall_started_at','pid','tab_id')} and a['segment']['boot']!=OLD_BOOT,'original-clock-or-new-segment')
 if live_boot is not None:
  need(a['segment']['boot']==live_boot,'continuation-not-current-boot')
  sys.path.insert(0,str(PROJECT/'packages/workshop-director'))
  from workshop_director.common import identity
  need(identity(a['effective_process']['pid'])=={k:a['effective_process'][k] for k in ('pid','started','boot')},'effective-browser-process-changed')
 transitions,codes=release_graph(a['release'],source_archives=source_archives);need(a['source_graph']==transitions and a['current_code_refs']==codes,'source-graph-not-release-derived')
 facts=fresh_facts(doc(a['fresh_proof']),original['job'],original['query'],original['source'],new_boot=a['segment']['boot'])
 need(facts['scope']==a['effective_scope'] and facts['process']==a['effective_process'] and a['effective_scope']['pid']!=parent['pid'],'effective-scope-not-derived')
 need(doc(a['fresh_observation'])==facts['observation'] and doc(a['fresh_page'])==facts['page'],'fresh-derived-artifact-changed')
 need(a.get('native_inventory_verified_under_original_locks') is True and doc(a['native_inventory_ref'])==a['native_inventory'],'original-native-inventory-record')
 for entry in a['failed_readonly_archives']:
  need(entry['original']['sha256']==entry['archive']['sha256'],'failed-readonly-archive-bytes');raw(entry['archive'])
 # Original absence is an admission PRECONDITION, never a permanent demand.
 # Current/new outputs go through normal region/native/source/client validators.
 # This metadata-only replay does not itself authorize capture or prove it done.
 return a


def verify_pre_capture_inventory(admission):
 """Call only under resource/scheduler/launcher/engine locks before commit."""
 a=admission;need(a['native_inventory']==inventory(Path(a['original']['company_folder']),a['original']['source'],a['capture']['key'],Path(a['capture']['out'])),'pre-capture-native-inventory-changed');return True

def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
 with tmp.open('wb') as f:f.write(o.encode(value));f.flush();os.fsync(f.fileno())
 os.replace(tmp,path)

class IdentityOnlyProbe:
 """Reuses Navigator account/readAccount, never a completed business Navigator.
 invoke is the existing installed bridge request. This class is not run by
 admission replay and never creates a tab/window or a new business order.
 """
 def __init__(self,*,checkpoint,job,query,source,process,tab_id,window_id,new_boot,out,invoke,process_reader):
  need(checkpoint['sha256']==CHECKPOINT_SHA,'probe-original-checkpoint');doc(checkpoint);self.job=job;self.query=query;self.source=source;self.process=process;self.tab=tab_id;self.window=window_id;self.boot=new_boot;self.out=canonical(out);self.invoke=invoke;self.process_reader=process_reader;self.replies=[];self.commands=[];self._navigator=None
  self.binding={'checkpoint':checkpoint,'job':job,'query':query,'source':source,'process':process,'tab_id':tab_id,'window_id':window_id,'boot':new_boot};self.file=self.out/'identity-only-probe.json'
  if self.file.exists():self.s=json.loads(self.file.read_bytes());need(self.s['binding']==self.binding,'probe-binding-changed')
  else:self.s={'binding':self.binding,'state':'prepared','tree_reads':0,'read_count':0,'activation':None};atomic(self.file,self.s)
 def save(self):atomic(self.file,self.s)
 def proof(self,refs=None,commands=None):
  import governance_detail as d
  return {'kind':'existing-records-reboot-four-read-proof-v1','boot':self.boot,'process':self.process,'tab_id':self.tab,'window_id':self.window,'commands':commands or self.commands[-4:],'replies':refs or self.replies[-4:],'observed_at':d.nav.stamp()}
 def read(self,command):
  need(command['op'] in ('tabs','ping','tree'),'probe-readonly-command')
  if command['op']=='tree':need(self.s['tree_reads']-self.s.get('date_correction',{}).get('identity_budget_origin',0)<3,'identity-probe-original-read-budget');self.s['tree_reads']+=1
  index=self.s['read_count'];self.s['read_count']+=1;self.save();intent=o.immutable(self.out/'reads'/(str(index).zfill(3)+'-intent.json'),{'command':command,'binding':self.binding});reply=self.invoke(command);rr=o.immutable(self.out/'reads'/(str(index).zfill(3)+'-reply.json'),reply);o.immutable(self.out/'reads'/(str(index).zfill(3)+'-returned.json'),{'intent':intent,'reply':rr});self.commands.append(command);self.replies.append(rr);return reply
 def activate(self,facts):
  import governance_detail as d
  before=doc(self.replies[-4])['result'];windows=[v for v in before if v.get('windowId')==self.window];focused=len(windows)==1 and windows[0].get('focused') is True;active=facts['observation']['tab'].get('active') is True
  if self.s['activation']:
   record=self.s['activation'];need(record['state']=='confirmed','activation-outcome-unknown-readonly-reconcile-required');return
  if active:self.s['activation']={'state':'confirmed','input_issued':False,'evidence':self.replies[-4:]};self.save();return
  command={'op':'activate','tabId':self.tab};intent=o.immutable(self.out/'existing-tab-activate-intent.json',{'kind':'existing-tab-activation-intent-v1','binding':self.binding,'command':command,'unknown':True});self.s['activation']={'state':'unknown','intent':intent};self.save();reply=self.invoke(command);rr=o.immutable(self.out/'existing-tab-activate-reply.json',reply);need(reply.get('ok') is True and reply.get('error') is None,'activation-rejected-or-unknown');v=reply['result'];need(v.get('tabId')==self.tab and v.get('windowId')==self.window and v.get('url')==facts['observation']['tab']['url'] and v.get('active') is True,'activation-effect-not-confirmed');self.s['activation']={'state':'confirmed','input_issued':True,'intent':intent,'reply':rr};self.save()
 def request(self,command):
  if command['op'] in ('tabs','ping','tree'):return self.read(command)
  need(command.get('op')=='hover' and self._navigator is not None and self._navigator.s['phase']=='account' and self.s['activation']['state']=='confirmed','identity-only-no-other-action')
  import governance_detail as d
  facts=_transport_facts(self.proof(),self.job,self.query,self.source,new_boot=self.boot,process_reader=self.process_reader,require_identity=False,require_original_facts=not bool(self.s.get('date_correction')));tree=facts['observation']['tree']
  provider=doc(self.job)['identity']['provider'];target=d.nav.exact(tree,provider);need(command=={'op':'hover','tabId':self.tab,'locator':{'by':'selector','value':target['selector']},'kind':'navigation'},'identity-only-exact-provider-hover')
  reply=self.invoke(command);o.immutable(self.out/'provider-hover-reply.json',reply);return reply
 def tick_identity(self):
  need(self._navigator.s['phase'] in ('account','readAccount'),'identity-only-menu-hard-stop');need(not any(c.get('state')=='unknown' for c in self._navigator.s.get('calls',[])),'identity-hover-unknown-no-replay');return self._navigator.tick()
 def run(self,*,corrective_identity=False):
  need(not corrective_identity or self.s.get('date_correction',{}).get('kind')=='exact-zero-input-reset-range-correction-v1','correction-not-authorized')
  need(self.s['state'] not in ('unknown','failed'),'probe-prior-error-needs-original-review')
  if self.s['state']=='complete':return self.s['proof'] # recorded facts only
  import governance_detail as d
  try:
   if not self.s['activation']:
    for c in ({'op':'tabs'},{'op':'ping','tabId':self.tab},{'op':'tree','tabId':self.tab},{'op':'tabs'}):self.read(c)
    facts=_transport_facts(self.proof(),self.job,self.query,self.source,new_boot=self.boot,process_reader=self.process_reader,require_identity=False,require_active=False,require_original_facts=not corrective_identity);self.activate(facts)
   need(self.s['activation']['state']=='confirmed','activation-unconfirmed-no-hover');self._navigator=d.nav.Navigator(doc(self.job),self.tab,self.out/'identity-only-navigation.json',invoke=self.request)
   for _ in range(2):
    if self._navigator.s['phase']=='menu':break
    self.tick_identity()
   need(self._navigator.s['phase']=='menu','identity-only-not-complete');proof=self.proof()
   if corrective_identity:
    _transport_facts(proof,self.job,self.query,self.source,new_boot=self.boot,process_reader=self.process_reader,require_original_facts=False);r=o.immutable(self.out/'full-identity-before-date-correction.json',proof);self.s.update(state='date-correction-identity-verified',identity_before_date=r)
   else:
    fresh_facts(proof,self.job,self.query,self.source,new_boot=self.boot,process_reader=self.process_reader);r=o.immutable(self.out/'full-identity-four-read-proof.json',proof);self.s.update(state='complete',proof=r)
   self.save();return r
  except BaseException:
   self.s['state']='unknown' if (self.s.get('activation') or {}).get('state')=='unknown' or self._navigator and any(c.get('state')=='unknown' for c in self._navigator.s.get('calls',[])) else 'failed';self.save();raise

def _state_inputs():
 c=catalogue();f=c['fixed'];task=copy.deepcopy(c['task']);parent=doc(archived(f['parent']));engine=doc(archived(f['engine']));a=original_values(task,doc(f['request']['original']),doc(f['response']['original']),doc(f['exit']['original']),parent,engine,doc(f['order']['original']));return c,parent,engine,a

def segment_folder(new_boot):
 import uuid
 prefix='darwin-kern-bootsessionuuid:';need(new_boot.startswith(prefix) and str(uuid.UUID(new_boot[len(prefix):]))==new_boot[len(prefix):] and new_boot!=OLD_BOOT,'exact-new-public-boot');c,parent,engine,a=_state_inputs();key=digest({'checkpoint':c['fixed']['checkpoint']['original'],'task':TASK,'order':parent['order'],'new_boot':new_boot});return o.location(parent['order'])/'reboot-continuations'/key

def _queue_guard():
 import sqlite3
 db=PROJECT/'runtime/standalone-workshop-director/queue.sqlite3'
 with __import__('sqlite3').connect(db.as_uri()+'?mode=ro',uri=True) as c:
  c.row_factory=sqlite3.Row;row=c.execute('SELECT * FROM tasks WHERE id=?',(TASK,)).fetchone();need(row is not None,'original-task-missing');task=dict(row)
  for k in ('payload','context','outer'):task[k]=json.loads(task[k]) if task.get(k) else None
  need(task==catalogue()['task'],'original-task-changed');owner=c.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK,'original-owner-required');morning=c.execute("SELECT state FROM plans WHERE id='morning'").fetchone();need(morning and morning[0]=='paused','morning-must-stay-paused');need(not c.execute("SELECT id FROM tasks WHERE state IN ('running','dispatching','unknown')").fetchall(),'live-or-unknown-child')
 return task

def apply(release_ref,fresh_proof_ref,*,clock,process_reader):
 """Metadata-only exact CAS. Does not retry a task or invoke the bridge."""
 import fcntl
 current_boot=clock.boot();folder=segment_folder(current_boot);folder.mkdir(parents=True,exist_ok=True);final=folder/'activation.json'
 if final.exists():
  need((folder/'metadata-apply-returned.json').is_file(),'metadata-apply-outcome-unknown');activation=o.ref(final);value=verify(activation,live_boot=current_boot);need(value['release']==release_ref and value['fresh_proof']==fresh_proof_ref,'existing-admission-input-conflict');return activation
 c,parent,engine,a=_state_inputs();source_graph,codes=release_graph(release_ref);proof=doc(fresh_proof_ref);facts=fresh_facts(proof,a['job'],a['query_final'],a['source'],new_boot=current_boot,process_reader=process_reader);original_folder=o.location(parent['order']);company_folder=original_folder/'companies/1';chain='violation-'+company_folder.parent.parent.name[:24]+'-1';out=company_folder/'frames/0000-anchor';key=chain+':0000-anchor';taskref=o.immutable(folder/'original-task.json',c['task']);inv=inventory(company_folder,a['source'],key,out);invref=o.immutable(folder/'pre-native-inventory.json',inv);observed=o.immutable(folder/'full-identity-observation.json',facts['observation']);page=o.immutable(folder/'full-current-page.json',facts['page'])
 original={'task':taskref,'parent':archived(c['fixed']['parent']),'engine':archived(c['fixed']['engine']),**{k:c['fixed'][k]['original'] for k in ('order','request','response','exit','source','job','query','profile','observation')},'company_folder':str(company_folder),'outer':c['task']['outer'],'parent_clock':{k:parent[k] for k in ('boot_identity','start_monotonic','wall_started_at','pid','tab_id')}}
 value={'kind':KIND,'task_id':TASK,'attempt_id':ATTEMPT,'checkpoint':c['fixed']['checkpoint']['original'],'original':original,'release':release_ref,'source_graph':source_graph,'current_code_refs':codes,'fresh_proof':fresh_proof_ref,'fresh_observation':observed,'fresh_page':page,'effective_scope':facts['scope'],'effective_process':facts['process'],'segment':{'boot':current_boot,'start_monotonic':clock.monotonic(),'wall_started_at':clock.wall().isoformat()},'clock_comparable':False,'acceptance_pass':False,'native_inventory':inv,'native_inventory_ref':invref,'native_inventory_verified_under_original_locks':True,'failed_readonly_archives':[{'original':e['original'],'archive':archived(e)} for e in c['failed_readonly_archives']],'capture':{'chain':chain,'key':key,'out':str(out)},'input_replayed':False,'scope_rebinding_is_not_old_proof_replacement':True}
 paths=[PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',original_folder/'launcher.lock',original_folder/'engine.lock'];handles=[]
 try:
  for path in paths:
   f=path.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  _queue_guard();need(o.ref(original_folder/'launcher.json')==c['fixed']['parent']['original'] and o.ref(original_folder/'engine.json')==c['fixed']['engine']['original'],'original-parent-or-engine-raced')
  verify_pre_capture_inventory(value)
  for n in ('started.json','child-process.json'):
   p=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/ATTEMPT/n))['process'];no_live_process(p,current_boot,process_reader)
  admission=o.immutable(folder/'admission.json',value);verify(admission,live_boot=current_boot)
  import violation_reboot_profile as profile_api
  profile=o.immutable(folder/'capture-profile.json',profile_api.derive(a['source'],a['profile'],admission));meta=doc(profile)['derivation'];nav={'binding':{'schema':'records-region-navigation-v1','source':a['source'],'profile':profile,'job':a['job'],'query':a['query_final'],'tab_id':facts['scope']['tab_id'],'window_id':facts['scope']['window_id']},'observations':[observed],'operations':[],'business_progress_changed':False,'last_observation':observed};nav_snapshot=o.immutable(folder/'initial-navigation.json',nav)
  nav_path=Path(meta['navigation_root'])/'state.json';need(not nav_path.exists(),'new-segment-navigation-conflict');atomic(nav_path,nav)
  activation_value={'kind':'violation-reboot-activation-v1','admission':admission,'derived_profile':profile,'initial_navigation':nav_snapshot};intent=folder/'metadata-apply-intent.json';need(not intent.exists(),'metadata-apply-unknown-no-replay');o.immutable(intent,{'kind':'exact-reboot-parent-metadata-apply-v1','original_parent':c['fixed']['parent']['original'],'original_engine':c['fixed']['engine']['original'],'activation':activation_value})
  # Reference is computable before publication, avoiding a cyclic profile ref.
  activation={'path':str(final),'sha256':hashlib.sha256(o.encode(activation_value)).hexdigest()};new_parent=copy.deepcopy(parent);new_parent.update(reboot_continuation=activation,status='running',error=None,clock_comparable=False,elapsed_seconds=None,acceptance_pass=False,end_monotonic=None);new_engine=copy.deepcopy(engine);new_engine.update(reboot_continuation=activation,status='running',error=None)
  parent_after=o.immutable(folder/'parent-after.json',new_parent);engine_after=o.immutable(folder/'engine-after.json',new_engine);atomic(original_folder/'launcher.json',new_parent);atomic(original_folder/'engine.json',new_engine);o.immutable(final,activation_value);o.immutable(folder/'metadata-apply-returned.json',{'intent':o.ref(intent),'parent_after':parent_after,'engine_after':engine_after,'activation':activation});return activation
 finally:
  for f in reversed(handles):f.close()

def run_identity(release_ref,*,tab_id,window_id,pid,clock,invoke,process_reader,comm_reader):
 """One durable identity-only preflight under the original owner/resource locks.
 No new business order, completed Navigator, new tab or arbitrary route.
 """
 import fcntl
 release_graph(release_ref);c,parent,engine,a=_state_inputs();new_boot=clock.boot();base=segment_folder(new_boot);original=o.location(parent['order']);folder=original/'companies/1';handles=[]
 public=process_reader(pid);need(public and public['boot']==new_boot,'probe-current-process-required');comm=comm_reader(pid);need(comm=='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','probe-exact-chrome-required');process={**public,'comm':comm}
 try:
  for path in (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',original/'launcher.lock',original/'engine.lock'):
   f=path.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  _queue_guard();need(o.ref(original/'launcher.json')==c['fixed']['parent']['original'] and o.ref(original/'engine.json')==c['fixed']['engine']['original'],'probe-original-parent-raced')
  inventory(folder,a['source'],'',folder/'frames/0000-anchor')
  probe=IdentityOnlyProbe(checkpoint=c['fixed']['checkpoint']['original'],job=a['job'],query=a['query_final'],source=a['source'],process=process,tab_id=tab_id,window_id=window_id,new_boot=new_boot,out=base/'identity-preflight',invoke=invoke,process_reader=process_reader)
  return probe.run()
 finally:
  for f in reversed(handles):f.close()

def date_failure(reference):
 """Exact observed zero-input failure, not an arbitrary retry capability."""
 need(reference=={'path':str(PROJECT/'work/2026-10-23/standalone-oneoff-execution-brief/violation-reboot-probe-date-reset-failure.json'),'sha256':DATE_FAILURE_SHA},'date-correction-fixed-failure-required');failure=doc(reference);need(failure['exact_error']=='governance-row-before-range' and failure['first_four_read_only']is True and failure['probe_state']=='failed' and failure['activation']is None and failure['provider_hover_intent_exists']is False and failure['apply_executed']is False and failure['task_retried']is False,'date-correction-not-zero-input-failure');need(failure['journal']['sha256']==DATE_JOURNAL_SHA,'date-correction-original-journal-sha');return failure

def verify_date_correction(reference):
 import governance_detail as d
 value=doc(reference)
 if value.get('pre_dispatch_recovery'):verify_pre_dispatch_recovery(value['pre_dispatch_recovery'],completed_query=doc(value['query_snapshot']))
 need(value.get('kind')=='verified-reboot-date-correction-v1','date-correction-proof-kind');failure=date_failure(value['failure']);old=doc(value['original_probe']);need(value['original_probe']['sha256']==DATE_JOURNAL_SHA and old['state']=='failed' and old['activation']is None and old['read_count']==4 and old['tree_reads']==1,'date-correction-original-prefix');need(value['binding']==old['binding'] and value['original_read_prefix_unchanged']is True,'date-correction-binding');base=Path(failure['journal']['path']).parent;need(Path(reference['path'])==base/'date-correction/verified-correction.json','date-correction-proof-path')
 need({Path(e['original']['path']).name:e['original']['sha256']for e in value['original_read_prefix']}==DATE_ORIGINAL_READS and len(value['original_read_prefix'])==12,'date-correction-exact-original-read-hashes')
 for entry in value['original_read_prefix']:
  need(Path(entry['original']['path']).parent==base/'reads'and Path(entry['archive']['path']).parent==base/'date-correction/original-raw'and Path(entry['archive']['path']).name==Path(entry['original']['path']).name,'date-correction-read-archive-path');raw(entry['original']);raw(entry['archive']);need(entry['original']['sha256']==entry['archive']['sha256'],'date-correction-original-read-bytes')
 binding=old['binding'];identity=doc(value['identity_before_date']);need(Path(value['identity_before_date']['path'])==base/'full-identity-before-date-correction.json','date-correction-identity-proof-path');identity_facts=_transport_facts(identity,binding['job'],binding['query'],binding['source'],new_boot=binding['boot'],require_original_facts=False);need(identity_facts['process']==binding['process'],'date-correction-full-identity-process');query=doc(value['query_snapshot']);job=doc(binding['job']);need(query['phase']=='capture-complete' and query['tab_id']==binding['tab_id'] and query['fingerprint']==d.nav.tag(job) and query['query_job_binding']['job']==binding['job'] and query['query_job_binding']['query_state_path']==str(base/'date-correction/records-query.json') and query['query_job_binding']['window_id']==binding['window_id'],'date-correction-query-binding');need(query['calls'] and all(c['state']=='confirmed'for c in query['calls']) and not query.get('settling_exhausted'),'date-correction-query-unresolved');last=query['calls'][-1];before=doc(last['before'])['tree'];expected={**d.g.QueryPlan(job['start'],job['end_exclusive']).next(before,{'phase':'verify-date'})['command'],'tabId':binding['tab_id']};need(last['command']==expected and sum(v['command']==expected for v in query['calls'])==1,'date-correction-exact-single-query')
 final=_transport_facts(value['final_four_read'],binding['job'],binding['query'],binding['source'],new_boot=binding['boot']);need(d.normal_page(doc(query['last_observation'])['tree'],job,doc(binding['query']))==final['page'],'date-correction-query-facts-not-original');need(value['final_four_read']['process']==binding['process'],'date-correction-process-binding');return value

def pre_dispatch_failure(reference):
 import ast
 need(reference==PRE_DISPATCH_AUTHORITY['failure'],'pre-dispatch-fixed-failure-required');failure=doc(reference);need(failure['error']==PRE_DISPATCH_AUTHORITY['error']and failure['returncode']==1 and failure['probe_state']=='unknown'and failure['query_phase']=='open-date'and len(failure['query_calls'])==1 and failure['query_calls'][0]['state']=='unknown'and 'result'not in failure['query_calls'][0],'pre-dispatch-exact-failure-shape');need(failure['query_state']['sha256']==PRE_DISPATCH_AUTHORITY['query_sha256']and failure['probe_journal']['sha256']==PRE_DISPATCH_AUTHORITY['probe_sha256']and failure['cli']['sha256']==PRE_DISPATCH_AUTHORITY['cli_sha256'],'pre-dispatch-exact-original-hashes');cli=doc(failure['cli']);need(cli['returncode']==1 and cli['stdout']==''and cli['stderr'].rstrip().endswith('ValueError: '+PRE_DISPATCH_AUTHORITY['error'])and 'runner.step()'in cli['stderr']and 'reply=invoke(command)'not in cli['stderr'],'pre-dispatch-natural-guard-trace')
 previous={'path':str(PROJECT/'work/performance-audit/violation-reboot-date-correction-candidate/supervisor-release.json'),'sha256':V2_RELEASE_SHA};release=doc(previous);source=release['targets'][0]['after'];need(source['sha256']==PRE_DISPATCH_AUTHORITY['source_sha256'],'pre-dispatch-exact-before-source');tree=__import__('ast').parse(raw(source));functions=[n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='request'and any(isinstance(k,ast.Constant)and k.value=='date-correction-input-current-window-focus'for k in ast.walk(n))];need(len(functions)==1,'pre-dispatch-before-source-guard');fn=functions[0];guard=[n.lineno for n in ast.walk(fn)if isinstance(n,ast.Constant)and n.value=='date-correction-input-current-window-focus'];dispatch=[n.lineno for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='invoke'];need(len(guard)==len(dispatch)==1 and guard[0]<dispatch[0],'pre-dispatch-before-invoke-proof');return failure,source

def raw_archive(reference,path):
 data=raw(reference);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists():need(path.read_bytes()==data,'pre-dispatch-archive-conflict')
 else:
  with path.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 return o.ref(path)

def verify_pre_dispatch_recovery(reference,*,completed_query=None):
 m=doc(reference);failure,_=pre_dispatch_failure(m['failure']);base=Path(failure['query_state']['path']).parent;need(Path(reference['path'])==base/'focus-preinput-recovery/admission.json'and m.get('kind')=='known-DOM-not-dispatched-open-date-v1','pre-dispatch-admission-path');old=doc(m['query_archive']);probe=doc(m['probe_archive']);need(m['query_archive']['sha256']==PRE_DISPATCH_AUTHORITY['query_sha256']and m['probe_archive']['sha256']==PRE_DISPATCH_AUTHORITY['probe_sha256'],'pre-dispatch-archive-original');need(old['phase']=='open-date'and old['calls']==failure['query_calls']and not old['pages']and probe['state']=='unknown'and probe['date_correction']['error']==PRE_DISPATCH_AUTHORITY['error']and probe['date_correction']['rpc_count']==5 and probe['date_correction']['steps']==1,'pre-dispatch-zero-effect-original');need({Path(v['original']['path']).name:v['original']['sha256']for v in m['transport_archives']}==PRE_DISPATCH_AUTHORITY['transport']and len(m['transport_archives'])==13,'pre-dispatch-exact-original-transport')
 for v in m['transport_archives']:raw(v['archive']);need(v['original']['sha256']==v['archive']['sha256']and Path(v['original']['path']).parent==base/'transport','pre-dispatch-transport-archive')
 if completed_query is not None:
  call=completed_query['calls'][0];need(call['command']==old['calls'][0]['command']and call['before']==old['calls'][0]['before']and call['intent_at']==old['calls'][0]['intent_at']and call.get('known_not_dispatched_recovery')==reference and call['state']=='confirmed','pre-dispatch-original-call-not-preserved');marker=doc(o.ref(base/'transport/004-dispatch-start.json'));reply=doc(o.ref(base/'transport/004-reply.json'));returned=doc(o.ref(base/'transport/004-returned.json'));intent=o.ref(base/'transport/004-intent.json');need(marker['intent']==returned['intent']==intent and marker['recovery']==reference and marker['command']==call['command']and reply.get('ok')is True and reply.get('error')is None and reply['result']==call['result']and returned['reply']==o.ref(base/'transport/004-reply.json'),'pre-dispatch-real-original-reply-required')
 return m

def prepare_pre_dispatch_recovery(probe,release_ref,failure_ref,folder):
 failure,source=pre_dispatch_failure(failure_ref);path=folder/'focus-preinput-recovery/admission.json';record=probe.s.get('date_correction');need(record is not None,'pre-dispatch-original-correction-required');need(doc(release_ref).get('previous_release')=={'path':str(PROJECT/'work/performance-audit/violation-reboot-date-correction-candidate/supervisor-release.json'),'sha256':V2_RELEASE_SHA},'pre-dispatch-reviewed-source-transition')
 if path.exists():
  reference=o.ref(path);verify_pre_dispatch_recovery(reference);need(record.get('known_not_dispatched_recovery')==reference and record['release']==release_ref,'pre-dispatch-existing-record-binding');return reference
 need(o.ref(probe.file)==failure['probe_journal']and o.ref(folder/'records-query.json')==failure['query_state'],'pre-dispatch-original-journals-raced');need(probe.s['state']=='unknown'and record['state']=='unknown'and record['error']==PRE_DISPATCH_AUTHORITY['error']and record['rpc_count']==5 and record['steps']==1,'pre-dispatch-original-counters');need(record['release']=={'path':str(PROJECT/'work/performance-audit/violation-reboot-date-correction-candidate/supervisor-release.json'),'sha256':V2_RELEASE_SHA},'pre-dispatch-original-release');files=[p for p in sorted((folder/'transport').iterdir())if p.is_file()];need({p.name:o.ref(p)['sha256']for p in files}==PRE_DISPATCH_AUTHORITY['transport'],'pre-dispatch-no-reply-or-later-dispatch')
 archives=[{'original':o.ref(p),'archive':raw_archive(o.ref(p),path.parent/'transport'/p.name)}for p in files];value={'kind':'known-DOM-not-dispatched-open-date-v1','failure':failure_ref,'source_before':source,'release':release_ref,'query_archive':raw_archive(failure['query_state'],path.parent/'original-query.json'),'probe_archive':raw_archive(failure['probe_journal'],path.parent/'original-probe.json'),'transport_archives':archives,'original_unknown_preserved':True,'authorization':'same open-date call0 and same transport004 only; original rejection occurred before invoke, not inferred from missing reply alone'};reference=o.immutable(path,value);verify_pre_dispatch_recovery(reference);record['release_history']=[record['release']];record.update(release=release_ref,known_not_dispatched_recovery=reference,state='corrective-query');probe.s.update(state='date-correction-identity-verified',date_correction=record);probe.save();return reference

def recovery_runner(base,recovery,resume):
 class KnownNotDispatchedRunner(base):
  def step(self):
   import governance_detail as d
   if not any(c.get('state')=='unknown'for c in self.s['calls']):return super().step()
   old=doc(verify_pre_dispatch_recovery(recovery)['query_archive']);need(self.s['phase']=='open-date'and len(self.s['calls'])==1 and self.s['calls']==old['calls']and not self.s['pages'],'pre-dispatch-original-call-only');need(not (self.file.parent/'transport/004-dispatch-start.json').exists()and not (self.file.parent/'transport/004-reply.json').exists(),'pre-dispatch-existing-dispatch-unknown');tree=self.observe();need(d.g.date_value(tree)=='2025-10-24 ~ 2026-10-24','pre-dispatch-current-reset-range-changed');step=self.plan.next(tree,{'phase':'open-date'});call=self.s['calls'][0];need({**step['command'],'tabId':self.tab}==call['command']and step['next_phase']=='select-start','pre-dispatch-current-selector-command-changed');call['known_not_dispatched_recovery']=recovery;call['recovery_fresh_before']=self.s['last_observation'];self.save();resume['pending']=True;result=self.request(call['command']);call.update(state='confirmed',result=result);self.s['phase']=step['next_phase'];self.s['needs_changed_tree']=self.s['last_observation'];self.save();return self.s
 return KnownNotDispatchedRunner

def correct_date(release_ref,failure_ref,*,tab_id,window_id,pid,clock,invoke,process_reader,comm_reader,pre_dispatch_failure=None):
 """Explicit one-off current filter correction, using the existing Runner.
 Original job/query/source and failed four reads are never edited. New UI
 intents live only in the same probe's corrective Runner; unknown is HOLD.
 """
 import fcntl,time
 import governance_detail as d
 release_graph(release_ref);failure=date_failure(failure_ref);base=Path(failure['journal']['path']).parent;c,parent,engine,a=_state_inputs();new_boot=clock.boot();need(base==segment_folder(new_boot)/'identity-preflight','date-correction-canonical-probe-path');handles=[]
 try:
  original=o.location(parent['order']);company=original/'companies/1'
  for path in (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',original/'launcher.lock',original/'engine.lock'):
   f=path.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  _queue_guard();need(o.ref(original/'launcher.json')==c['fixed']['parent']['original']and o.ref(original/'engine.json')==c['fixed']['engine']['original'],'date-correction-original-parent-raced');inventory(company,a['source'],'',company/'frames/0000-anchor')
  public=process_reader(pid);need(public and public['boot']==new_boot and comm_reader(pid)=='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','date-correction-current-process');process={**public,'comm':comm_reader(pid)};probe=IdentityOnlyProbe(checkpoint=c['fixed']['checkpoint']['original'],job=a['job'],query=a['query_final'],source=a['source'],process=process,tab_id=tab_id,window_id=window_id,new_boot=new_boot,out=base,invoke=invoke,process_reader=process_reader)
  folder=base/'date-correction';record=probe.s.get('date_correction');resume={'pending':False};recovery=None
  if pre_dispatch_failure is not None:
   recovery=prepare_pre_dispatch_recovery(probe,release_ref,pre_dispatch_failure,folder);record=probe.s['date_correction']
  if record:
   need(record['failure']==failure_ref and record['release']==release_ref,'date-correction-existing-binding-conflict');need(record.get('kind')=='exact-zero-input-reset-range-correction-v1'and record.get('identity_budget_origin')==1 and record['original_probe']=={'path':str(folder/'original-probe.json'),'sha256':DATE_JOURNAL_SHA}and doc(record['original_probe'])['binding']==probe.binding,'date-correction-original-record-binding');need(type(record['steps'])is int and 0<=record['steps']<=32 and type(record['rpc_count'])is int and 0<=record['rpc_count']<=160,'date-correction-record-budget-changed');need({Path(e['original']['path']).name:e['original']['sha256']for e in record['original_read_prefix']}==DATE_ORIGINAL_READS and len(record['original_read_prefix'])==12,'date-correction-original-prefix-changed')
   for e in record['original_read_prefix']:raw(e['original']);raw(e['archive']);need(e['original']['sha256']==e['archive']['sha256'],'date-correction-raw-archive-changed')
   if probe.s['state']=='complete':verify_date_correction(record['verified']);return probe.s['proof']
   need(probe.s['state']not in('failed','unknown') and record.get('state')not in('failed','unknown'),'date-correction-prior-error-inspect-only')
  else:
   need(o.ref(probe.file)==failure['journal'] and probe.s['state']=='failed' and probe.s['activation']is None and probe.s['read_count']==4 and probe.s['tree_reads']==1 and not (base/'identity-only-navigation.json').exists() and not (base/'existing-tab-activate-intent.json').exists(),'date-correction-exact-zero-input-original')
   old_probe=o.immutable(folder/'original-probe.json',probe.s)
   prefix=[]
   for path in sorted((base/'reads').glob('*.json')):
    dst=folder/'original-raw'/path.name;dst.parent.mkdir(parents=True,exist_ok=True);data=path.read_bytes()
    if dst.exists():need(dst.read_bytes()==data,'date-correction-archive-conflict')
    else:
     with dst.open('xb')as f:f.write(data);f.flush();os.fsync(f.fileno())
    prefix.append({'original':o.ref(path),'archive':o.ref(dst)})
   need(len(prefix)==12 and {Path(e['original']['path']).name:e['original']['sha256']for e in prefix}==DATE_ORIGINAL_READS,'date-correction-exact-four-read-records');old=doc(old_probe);need(old_probe['sha256']==DATE_JOURNAL_SHA,'date-correction-probe-original-byte-archive')
   proof={'boot':new_boot,'process':process,'tab_id':tab_id,'window_id':window_id,'commands':[{'op':'tabs'},{'op':'ping','tabId':tab_id},{'op':'tree','tabId':tab_id},{'op':'tabs'}],'replies':[o.ref(base/'reads'/(str(i).zfill(3)+'-reply.json'))for i in range(4)],'observed_at':failure['at']};_transport_facts(proof,a['job'],a['query_final'],a['source'],new_boot=new_boot,require_identity=False,require_original_facts=False);need(d.g.date_value(doc(proof['replies'][2])['result'])=='2025-10-24 ~ 2026-10-24','date-correction-reset-range-not-original')
   record={'kind':'exact-zero-input-reset-range-correction-v1','failure':failure_ref,'release':release_ref,'original_probe':old_probe,'original_read_prefix':prefix,'identity_budget_origin':probe.s['tree_reads'],'state':'identity-preflight','created_at':d.nav.stamp(),'steps':0,'rpc_count':0};probe.s.update(state='prepared',date_correction=record);probe.save()
  try:
   if record['state']=='identity-preflight':probe.run(corrective_identity=True);record=probe.s['date_correction'];record['state']='corrective-query';probe.save()
   refs=[];commands=[]
   def request(command):
    resumed=resume['pending']and command.get('op')=='click'
    if resumed:
     resume['pending']=False;index=4;intent=o.ref(folder/'transport/004-intent.json');need(doc(intent)=={'command':command,'binding':probe.binding,'unknown':True},'pre-dispatch-original-transport-command')
    else:
     index=record['rpc_count'];record['rpc_count']+=1;need(record['rpc_count']<=160,'date-correction-rpc-budget');probe.save();intent=o.immutable(folder/'transport'/(str(index).zfill(3)+'-intent.json'),{'command':command,'binding':probe.binding,'unknown':True})
    start=time.clock_gettime(time.CLOCK_MONOTONIC)
    if command['op']not in('tabs','ping','tree'):
     need(command.get('op')=='click' and command.get('kind')=='filter','date-correction-only-normal-filter');need(len(refs)>=4,'date-correction-fresh-before-input');current={'boot':new_boot,'process':process,'tab_id':tab_id,'window_id':window_id,'commands':commands[-4:],'replies':refs[-4:],'observed_at':d.nav.stamp()};_transport_facts(current,a['job'],a['query_final'],a['source'],new_boot=new_boot,process_reader=process_reader,require_original_facts=False)
     marker=folder/'transport'/(str(index).zfill(3)+'-dispatch-start.json');need(not marker.exists(),'date-correction-existing-dispatch-start-unknown');o.immutable(marker,{'kind':'DOM-semantic-dispatch-start-v1','intent':intent,'command':command,'recovery':recovery if resumed else None,'fresh_before':refs[-4:],'at':d.nav.stamp()})
    reply=invoke(command);r=o.immutable(folder/'transport'/(str(index).zfill(3)+'-reply.json'),reply);o.immutable(folder/'transport'/(str(index).zfill(3)+'-returned.json'),{'intent':intent,'reply':r,'elapsed_seconds':time.clock_gettime(time.CLOCK_MONOTONIC)-start});commands.append(command);refs.append(r);return reply
   query_file=folder/'records-query.json';query_lock=query_file.with_name(query_file.name+'.lock').open('a');handles.append(query_lock);fcntl.flock(query_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   if not query_file.exists():
    identity_proof=doc(probe.s['identity_before_date']);need(d.g.date_value(doc(identity_proof['replies'][2])['result'])=='2025-10-24 ~ 2026-10-24','date-correction-current-reset-range-changed')
   runner_type=recovery_runner(d.query_api.Runner,recovery,resume)if recovery else d.query_api.Runner
   runner=runner_type(doc(a['job']),tab_id,query_file,d.nav.VERSION,invoke=request,job_ref=a['job'])
   while runner.s['phase']!='capture-complete':
    need(record['steps']<32,'date-correction-original-step-budget');record['steps']+=1;probe.save();runner.step();need(not any(v['state']=='unknown'for v in runner.s['calls']),'date-correction-unknown-no-repeat');need(not runner.s.get('settling_exhausted')and runner.s['phase']!='profile-required','date-correction-hold-inspect-original')
   # One final original-shape four-read proof. No input is needed or authorized.
   final_commands=[{'op':'tabs'},{'op':'ping','tabId':tab_id},{'op':'tree','tabId':tab_id},{'op':'tabs'}]
   for command in final_commands:request(command)
   final={'kind':'existing-records-reboot-four-read-proof-v1','boot':new_boot,'process':process,'tab_id':tab_id,'window_id':window_id,'commands':commands[-4:],'replies':refs[-4:],'observed_at':d.nav.stamp()};fresh_facts(final,a['job'],a['query_final'],a['source'],new_boot=new_boot,process_reader=process_reader);snapshot=o.immutable(folder/'query-completed-snapshot.json',runner.s);verified=o.immutable(folder/'verified-correction.json',{'kind':'verified-reboot-date-correction-v1','failure':failure_ref,'binding':probe.binding,'original_probe':record['original_probe'],'original_read_prefix':record['original_read_prefix'],'original_read_prefix_unchanged':True,'query_snapshot':snapshot,'final_four_read':final,'identity_before_date':probe.s['identity_before_date'],**({'pre_dispatch_recovery':recovery}if recovery else{})});verify_date_correction(verified);final['date_correction']=verified;result=o.immutable(base/'full-identity-four-read-proof.json',final);record.update(state='complete',verified=verified);probe.s.update(state='complete',proof=result,date_correction=record);probe.save();return result
  except BaseException as error:
   record['error']=str(error);qp=folder/'records-query.json';unknown=probe.s.get('state')=='unknown' or qp.exists()and any(v.get('state')=='unknown'for v in json.loads(qp.read_bytes()).get('calls',[]));record['state']='unknown'if unknown else'failed';probe.s.update(state=record['state'],date_correction=record);probe.save();raise
 finally:
  for f in reversed(handles):f.close()

# Source-bound restoration for the single parked failed14 order. No new source,
# notification order, business ledger or old confirmed journal is created here.
def environment_binding(grant_ref,*,clock=None,process_reader=None,live=False):
 g=doc(grant_ref);e=g['environment_restore'];need(g.get('kind')=='reviewed-quiescent-round-handoff-grant-v1' and g['task_id']==TASK and e.get('kind')=='source-bound-pending-frames-environment-restore-v1' and e['company_index']==1,'environment-grant-scope')
 base=verify(e['activation'],live_boot=clock.boot() if clock else None);original=base['original'];need(e['activation']==g['activation'] and e['source']==original['source'] and e['job']==original['job'] and e['order']==original['order'],'environment-original-source-order')
 parent=engine=None
 if live:
  parent=doc(o.ref(o.location(e['order'])/'launcher.json'));engine=doc(o.ref(o.location(e['order'])/'engine.json'));need(parent['reboot_continuation']==engine['reboot_continuation']==e['activation'] and engine['index']==1 and engine['phase']=='frames' and allowed_calls(engine,e['activation']),'environment-pending-original-frames')
 scope=base['effective_scope'];process=base['effective_process'];need(clock is None or clock.boot()==process['boot'],'environment-boot-changed')
 if process_reader:need(process_reader(scope['pid'])=={k:process[k]for k in ('pid','started','boot')},'environment-process-changed')
 folder=Path(original['company_folder'])/'environment-restores'/grant_ref['sha256'];return g,e,base,parent,engine,scope,folder

def environment_page(raw,base):
 import governance_detail as d
 job=doc(base['original']['job']);query=doc(base['original']['query']);source=doc(base['original']['source']);need(len(query['pages'])==1 and len(query['rows'])==1,'environment-fixed-one-page-source');d.nav.identity(raw['tree'],job['identity']);page=d.normal_page(raw['tree'],job,query);expected=next(v for v in query['pages']if v['page']==page['page']);need(page=={k:v for k,v in expected.items()if k!='observation'},'environment-original-record-facts-changed');need(source['identity']==job['identity'] and (source['start'],source['end_exclusive'])==(job['start'],job['end_exclusive']),'environment-original-date-source');return page

def _verify_environment_data(reference,grant_ref,*,live=False,clock=None,process_reader=None):
 
 if live and clock is None:
  import execution_timing
  clock=execution_timing.Clock()
 if live and process_reader is None:
  from workshop_director.common import identity
  process_reader=identity
 g,e,base,parent,engine,scope,folder=environment_binding(grant_ref,clock=clock if live else None,process_reader=process_reader if live else None,live=live);v=doc(reference);need(Path(reference['path'])==folder/'complete.json' and v['kind']=='source-bound-records-environment-restored-v1' and v['grant']==grant_ref and v['binding']==e and v['scope']==scope and v['boot']==base['effective_process']['boot'],'environment-completion-binding')
 need(v['original_refs']=={k:base['original'][k]for k in ('source','job','query','profile','observation')} and v['business_ledgers_written'] is False and v['notifications_sent'] is False and v['clock_comparable'] is False,'environment-no-business-replacement')
 for r in v['journals']:need(r['original']['sha256']==r['archive']['sha256'],'environment-component-journal-archive');raw(r['archive'])
 state=doc(v['state']);need(state['phase']=='complete' and state['grant']==grant_ref and state['steps']<=256,'environment-complete-state');observation=doc(v['observation']);need(environment_page(observation,base)==v['page'],'environment-complete-facts');need(v['navigation']['sha256']==v['navigation_snapshot']['sha256'],'environment-navigation-archive');navigation=doc(v['navigation_snapshot']);need(navigation['last_observation']==v['observation'] and navigation['binding']['source']==e['source'] and navigation['binding']['profile']==base['derived_profile'] and all(x['state']=='complete'for x in navigation['operations']),'environment-navigation-checkpoint')
 import governance_detail as d
 query=doc(v['corrective_query']);job=doc(e['job']);original_query=doc(base['original']['query']);b=query.get('query_job_binding',{});need(b=={'kind':'governance-query-job-binding-v1','job':e['job'],'fingerprint':d.nav.tag(job),'tab_id':scope['tab_id'],'window_id':scope['window_id'],'query_state_path':str(folder/'components/normal-navigation/records-query.json')} and query['fingerprint']==d.nav.tag(job) and query['tab_id']==scope['tab_id'],'environment-query-original-job-binding');need([{k:x for k,x in page.items()if k!='observation'}for page in query['pages']]==[{k:x for k,x in page.items()if k!='observation'}for page in original_query['pages']],'environment-all-query-pages-original-facts');need(query['phase']=='capture-complete' and not any(query.get(k)for k in ('hold','error','last_error','settling_exhausted')) and all(c['state']=='confirmed'for c in query['calls']),'environment-corrective-query-not-complete')
 return v

def environment_runtime(grant_ref):
 """Resolve the same pinned scheduler config; never PATH/pip/sys.path fallback."""
 grant=doc(grant_ref);root=Path(grant['root']);need(root==PROJECT/'runtime/standalone-workshop-director' and root.resolve()==root,'environment-runtime-root')
 sys.path.insert(0,str(PROJECT/'packages/workshop-director'))
 from workshop_director.engine import load_active_config
 config,config_ref,base_ref=load_active_config(root);python=PROJECT/'skills/daily-comment-stats/.venv/bin/python'
 need(config.get('project')==str(PROJECT) and config.get('python')==str(python) and python.is_file(),'environment-runtime-fixed-python')
 return python,config_ref,base_ref

def environment_delegate(action,grant_ref,reference=None,*,live=False):
 import subprocess
 python,config_ref,base_ref=environment_runtime(grant_ref)
 # venv Python is a symlink to CLT on this Host; resolved executable equality
 # would incorrectly identify the daemon as the dependency-complete runtime.
 if Path(sys.prefix).resolve()==python.parent.parent.resolve():return None
 need(action in ('env-step','env-verify') and (action=='env-verify')==(reference is not None),'environment-runtime-action')
 if action=='env-step':
  import sqlite3
  grant=doc(grant_ref);original_task=doc(grant['task']);plans=(original_task['plan_id'],grant['new_plan_id']);queue=Path(grant['root'])/'queue.sqlite3'
  need(original_task.get('id')==grant.get('task_id') and all(type(p) is str and p and p!='morning' for p in plans) and plans[0]!=plans[1] and queue.is_file() and queue.resolve()==queue,'environment-runtime-plan-binding')
  with sqlite3.connect(queue.as_uri()+'?mode=ro',uri=True) as db:states=dict(db.execute('SELECT id,state FROM plans WHERE id IN (?,?)',plans).fetchall())
  need(set(states)==set(plans) and all(states[p]=='active' for p in plans),'environment-runtime-maintenance-paused')
 helper=PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py';helper_ref=o.ref(helper)
 argv=[str(python),'-I','-B',str(helper),action,'--grant',grant_ref['path'],'--grant-sha256',grant_ref['sha256']]
 if reference is not None:argv+=['--reference',reference['path'],'--sha256',reference['sha256']]
 if live:argv+=['--live']
 return environment_child(argv,grant_ref,action,reference,live,helper_ref,config_ref,base_ref)

def environment_progress(grant_ref):
 grant=doc(grant_ref);source=Path(grant['environment_restore']['source']['path']);folder=source.parent/'environment-restores'/grant_ref['sha256']
 need(source.is_absolute() and source.resolve()==source and PROJECT/'runtime/workshop-director/role-executions' in source.parents,'environment-runtime-progress-path')
 return {k:o.ref(folder/name) if (folder/name).is_file() else None for k,name in (('state','state.json'),('completion','complete.json'))}

def environment_child(argv,grant_ref,action,reference,live,helper_ref,config_ref,base_ref):
 """At most one spawn per durable step. Missing exit is never redispatched."""
 import fcntl,subprocess
 from workshop_director.common import identity
 grant=doc(grant_ref);root=Path(grant['root'])/'lease-handoffs'/grant_ref['sha256']/'environment-runtime';root.mkdir(parents=True,exist_ok=True)
 with (root/'runtime.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def outcome(folder):
   request_ref=o.ref(folder/'request.json');request=doc(request_ref);need(request['kind']=='controlled-environment-child-request-v1' and request['grant']==grant_ref and request['action']==action and request['reference']==reference and request['live'] is live,'environment-runtime-original-request')
   need(request['helper']==helper_ref and request['config']==config_ref and request['base_config']==base_ref,'environment-runtime-step-source-supersession-required');raw(request['helper_archive']);need(request['helper']['sha256']==request['helper_archive']['sha256'],'environment-runtime-helper-archive')
   dispatch=doc(o.ref(folder/'dispatch-start.json'));need(dispatch=={'request':request_ref,'argv':request['argv']},'environment-runtime-dispatch-binding')
   need((folder/'natural-exit.json').is_file(),'environment-runtime-child-unknown-no-replay');exit_ref=o.ref(folder/'natural-exit.json');receipt=doc(exit_ref)
   need(receipt['kind']=='controlled-environment-child-natural-exit-v1' and receipt['request']==request_ref and receipt['dispatch']==o.ref(folder/'dispatch-start.json') and receipt['process']==o.ref(folder/'process.json') and doc(receipt['process'])['request']==request_ref and type(receipt['returncode']) is int,'environment-runtime-exit-binding')
   need(receipt['stdout']==o.ref(folder/'stdout.log') and receipt['stderr']==o.ref(folder/'stderr.log'),'environment-runtime-output-paths');output=raw(receipt['stdout']);raw(receipt['stderr']);need(receipt['returncode']==0,'environment-runtime-child-failed-no-replay')
   value=json.loads(output);need(type(value) is dict and set(value)=={'kind','action','grant','reference','live','config','base_config','helper','result'} and value['kind']=='controlled-environment-runtime-result-v1' and value['action']==action and value['grant']==grant_ref and value['reference']==reference and value['live'] is live and value['config']==request['config'] and value['base_config']==request['base_config'] and value['helper']==request['helper'],'environment-runtime-child-binding')
   if action=='env-step':
    result=value['result'];need(type(result) is dict and result.get('status') in ('continue','complete'),'environment-runtime-step-result')
    if result['status']=='continue':need(receipt['after_progress']!=request['before_progress'] and receipt['after_progress']['state'] is not None and result['journal']==receipt['after_progress']['state'],'environment-runtime-no-progress')
    else:need(result['completion']==receipt['after_progress']['completion'] and result['completion'] is not None,'environment-runtime-completion-binding')
   return value['result'],receipt
  if action=='env-step':
   directory=root/'steps';directory.mkdir(exist_ok=True);entries=sorted(directory.glob('*'));need(all(p.is_dir() and p.name==str(i).zfill(4) for i,p in enumerate(entries)) and len(entries)<=256,'environment-runtime-step-sequence')
   if entries:
    result,last=outcome(entries[-1])
    if result['status']=='complete':return result
    need(environment_progress(grant_ref)==last['after_progress'],'environment-runtime-progress-changed')
   need(len(entries)<256,'environment-runtime-step-budget');folder=directory/str(len(entries)).zfill(4)
  else:
   directory=root/'verifications'/o.digest({'reference':reference,'live':live,'helper':helper_ref,'config':config_ref});directory.mkdir(parents=True,exist_ok=True);entries=sorted(directory.glob('*'));need(all(p.is_dir() and p.name==str(i).zfill(4) for i,p in enumerate(entries)),'environment-runtime-verify-sequence')
   if entries:outcome(entries[-1]) # Only resolves the preceding child; never trusts it as fresh live proof.
   folder=directory/str(len(entries)).zfill(4)
  folder.mkdir();helper_archive=raw_archive(helper_ref,root/'helper-refs'/helper_ref['sha256']/'source.py')
  before=environment_progress(grant_ref) if action=='env-step' else None
  request={'kind':'controlled-environment-child-request-v1','grant':grant_ref,'action':action,'reference':reference,'live':live,'helper':helper_ref,'helper_archive':helper_archive,'config':config_ref,'base_config':base_ref,'argv':argv,'before_progress':before,'created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()};request_ref=o.immutable(folder/'request.json',request);dispatch=o.immutable(folder/'dispatch-start.json',{'request':request_ref,'argv':argv})
  with (folder/'stdout.log').open('xb') as stdout,(folder/'stderr.log').open('xb') as stderr:
   child=subprocess.Popen(argv,stdout=stdout,stderr=stderr);process=o.immutable(folder/'process.json',{'request':request_ref,'pid':child.pid,'identity':identity(child.pid)});returncode=child.wait();stdout.flush();stderr.flush();os.fsync(stdout.fileno());os.fsync(stderr.fileno())
  receipt={'kind':'controlled-environment-child-natural-exit-v1','request':request_ref,'dispatch':dispatch,'process':process,'returncode':returncode,'stdout':o.ref(folder/'stdout.log'),'stderr':o.ref(folder/'stderr.log'),'after_progress':environment_progress(grant_ref) if action=='env-step' else None};o.immutable(folder/'natural-exit.json',receipt)
  need(o.ref(helper_ref['path'])==helper_ref and o.ref(config_ref['path'])==config_ref and o.ref(base_ref['path'])==base_ref,'environment-runtime-source-config-changed')
  return outcome(folder)[0]

def restore_environment(grant_ref,*,clock,process_reader,invoke=None):
 delegated=environment_delegate('env-step',grant_ref)
 if delegated is not None:
  need(invoke is None,'environment-runtime-no-injected-transport');return delegated
 return _restore_environment_local(grant_ref,clock=clock,process_reader=process_reader,invoke=invoke)

def _restore_environment_local(grant_ref,*,clock,process_reader,invoke=None):
 import fcntl,sqlite3,time
 import violation_execution_ports as ports
 g,e,base,parent,engine,scope,folder=environment_binding(grant_ref,clock=clock,process_reader=process_reader,live=True);folder.mkdir(parents=True,exist_ok=True)
 handles=[]
 try:
  for path in (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',folder/'environment.lock',o.location(e['order'])/'launcher.lock',o.location(e['order'])/'engine.lock'):
   f=path.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   db.row_factory=sqlite3.Row;t=db.execute('SELECT * FROM tasks WHERE id=?',(TASK,)).fetchone();owner=db.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();need(t and t['state']=='failed' and Path(t['active_attempt']).name==TASK+'-14' and owner and json.loads(owner[0])==TASK and not db.execute("SELECT id FROM tasks WHERE state IN ('running','dispatching','unknown')").fetchall(),'environment-original-quiescent-owner')
  need(not ports.screenshot_nav.pending_frames(e['source']),'environment-native-pending');inventory(Path(base['original']['company_folder']),e['source'],base['capture']['key'],Path(base['capture']['out']))
  final=folder/'complete.json'
  if final.exists():
   _verify_environment_data(o.ref(final),grant_ref,live=True,clock=clock,process_reader=process_reader);commit_environment_checkpoint(o.ref(final),grant_ref);verify_environment(o.ref(final),grant_ref,live=True,clock=clock,process_reader=process_reader);return {'status':'complete','completion':o.ref(final)}
  path=folder/'state.json';binding={'grant':grant_ref,'source':e['source'],'activation':e['activation'],'scope':scope,'boot':clock.boot()}
  s=json.loads(path.read_bytes())if path.exists()else{'kind':'source-bound-environment-restore-journal-v1',**binding,'phase':'company','steps':0,'rpc_count':0,'journals':[]}
  need(all(s[k]==v for k,v in binding.items()) and s['phase']in ('company','center','records-open','records-query','fresh-observation') and s['steps']<256,'environment-journal-binding-or-budget')
  def save():atomic(path,s)
  save();transport=folder/'transport';transport.mkdir(exist_ok=True)
  need(all((transport/(p.stem.replace('-intent','')+'-returned.json')).exists()for p in transport.glob('*-intent.json')),'environment-transport-unknown-no-replay')
  def request(command):
   need(command.get('op')in ('tabs','ping','tree','readonly-scope','click','hover','activate') and (command.get('op')!='click' or command.get('kind')in ('navigation','filter')),'environment-only-public-navigation-filter')
   if command.get('op')=='readonly-scope':need(command=={'op':'readonly-scope','tabId':scope['tab_id'],'windowId':scope['window_id']},'environment-readonly-scope-exact-target')
   need(process_reader(scope['pid'])=={k:base['effective_process'][k]for k in ('pid','started','boot')} and clock.boot()==s['boot'],'environment-live-process-changed');index=s['rpc_count'];s['rpc_count']+=1;save();stem=str(index).zfill(5);intent=o.immutable(transport/(stem+'-intent.json'),{'command':command,'at':clock.wall().isoformat(),'grant':grant_ref});start=clock.monotonic();reply=(invoke or ports.nav.bridge.request)(command);rr=o.immutable(transport/(stem+'-reply.json'),reply);o.immutable(transport/(stem+'-returned.json'),{'intent':intent,'reply':rr,'elapsed_seconds':clock.monotonic()-start});return reply
  p=ports.ProductionPorts(scope['tab_id'],scope['pid'],request=request);p.reboot_continuation=e['activation'];order=doc(e['order']);artifacts=engine['companies'][1]['artifacts'];ctx={'order':order,'company':order['companies'][1],'artifacts':artifacts,'folder':str(folder/'components/normal-navigation')};s['steps']+=1;save()
  if s['phase']!='fresh-observation':
   phase=s['phase'];result=p.step(phase,ctx)
   if result.get('journal'):s['journals'].append({'original':result['journal'],'archive':raw_archive(result['journal'],folder/'journals'/(str(s['steps']).zfill(4)+'.json'))})
   need(not result.get('hold'),'environment-component-held:'+str(result.get('hold')))
   if result.get('done'):s['phase']={'company':'center','center':'records-open','records-open':'records-query','records-query':'fresh-observation'}[phase]
   save();return {'status':'continue','journal':o.ref(path),'phase':s['phase']}
  r=ports.screenshot_nav.Runner(e['source'],base['derived_profile'],invoke=request);current=r.run('observe');observation=current['observation'];page=environment_page(doc(observation),base);s['phase']='complete';save();value={'kind':'source-bound-records-environment-restored-v1','grant':grant_ref,'binding':e,'scope':scope,'boot':s['boot'],'original_refs':{k:base['original'][k]for k in ('source','job','query','profile','observation')},'journals':s['journals'],'corrective_query':o.ref(folder/'components/normal-navigation/records-query.json'),'state':o.ref(path),'observation':observation,'navigation':current['journal'],'navigation_snapshot':raw_archive(current['journal'],folder/'navigation-complete.json'),'page':page,'business_ledgers_written':False,'notifications_sent':False,'clock_comparable':False};reference=o.immutable(final,value);_verify_environment_data(reference,grant_ref,live=True,clock=clock,process_reader=process_reader);commit_environment_checkpoint(reference,grant_ref);verify_environment(reference,grant_ref,live=True,clock=clock,process_reader=process_reader);return {'status':'complete','completion':reference}
 finally:
  for f in reversed(handles):f.close()


def commit_environment_checkpoint(reference,grant_ref):
 # Caller holds the original global resource and this event lock. Each write is
 # reconciled against an exact intent; a changed original engine is never merged.
 v=_verify_environment_data(reference,grant_ref);g,e,base,_,_,scope,folder=environment_binding(grant_ref);path=o.location(e['order'])/'engine.json';intent=folder/'checkpoint-intent.json';returned=folder/'checkpoint-returned.json'
 if not intent.exists():
  before=o.ref(path);old=doc(before);need(old['phase']=='frames' and old['index']==1 and old['reboot_continuation']==e['activation'] and allowed_calls(old,e['activation']),'environment-checkpoint-original-engine');after=copy.deepcopy(old);a=after['companies'][1]['artifacts'];need(a['source']==e['source'] and a['job']==e['job'] and a['profile']==base['original']['profile'] and a['query_final']==base['original']['query'],'environment-checkpoint-source-bound');nested=copy.deepcopy(a.get('reboot_capture',{}));frame=copy.deepcopy(nested.get('frame_state',{'phase':'capture','observation':base['fresh_observation']}));need(frame['phase']=='capture','environment-checkpoint-capture-only');frame.update(observation=v['observation'],navigation_checkpoint=v['navigation'],reboot_current_observation=True);nested.update(frame_state=frame,environment_restoration=reference);a['reboot_capture']=nested;oldarchive=raw_archive(before,folder/'engine-before-checkpoint.json');new=o.immutable(folder/'engine-after-checkpoint.json',after);o.immutable(intent,{'kind':'source-bound-environment-checkpoint-intent-v1','completion':reference,'before':before,'before_archive':oldarchive,'after':new})
 plan=doc(o.ref(intent));need(plan['completion']==reference and plan['before']['sha256']==plan['before_archive']['sha256'],'environment-checkpoint-intent');raw(plan['before_archive']);new=doc(plan['after']);old=doc(plan['before_archive']);expected=copy.deepcopy(old);a=expected['companies'][1]['artifacts'];nested=copy.deepcopy(a.get('reboot_capture',{}));frame=copy.deepcopy(nested.get('frame_state',{'phase':'capture','observation':base['fresh_observation']}));need(frame['phase']=='capture','environment-checkpoint-original-phase');frame.update(observation=v['observation'],navigation_checkpoint=v['navigation'],reboot_current_observation=True);nested.update(frame_state=frame,environment_restoration=reference);a['reboot_capture']=nested;need(new==expected and new['calls']==old['calls'],'environment-checkpoint-only-nested-delta');need(o.ref(path)in(plan['before'],{'path':str(path),'sha256':plan['after']['sha256']}),'environment-checkpoint-raced')
 if o.ref(path)==plan['before']:atomic(path,new)
 return o.immutable(returned,{'intent':o.ref(intent),'after':o.ref(path),'completion':reference})

def verify_environment(reference,grant_ref,*,live=False,clock=None,process_reader=None):
 delegated=environment_delegate('env-verify',grant_ref,reference,live=live)
 if delegated is not None:return delegated
 return _verify_environment_local(reference,grant_ref,live=live,clock=clock,process_reader=process_reader)

def _verify_environment_local(reference,grant_ref,*,live=False,clock=None,process_reader=None):
 v=_verify_environment_data(reference,grant_ref,live=live,clock=clock,process_reader=process_reader);g,e,base,_,_,scope,folder=environment_binding(grant_ref);receipt=doc(o.ref(folder/'checkpoint-returned.json'));plan=doc(receipt['intent']);need(plan['kind']=='source-bound-environment-checkpoint-intent-v1' and receipt['completion']==plan['completion']==reference and plan['before']['sha256']==plan['before_archive']['sha256'],'environment-checkpoint-receipt');old=doc(plan['before_archive']);new=doc(plan['after']);expected=copy.deepcopy(old);a=expected['companies'][1]['artifacts'];need(a['source']==e['source'] and a['profile']==base['original']['profile'] and a['job']==e['job'] and a['query_final']==base['original']['query'],'environment-checkpoint-receipt-source');nested=copy.deepcopy(a.get('reboot_capture',{}));frame=copy.deepcopy(nested.get('frame_state',{'phase':'capture','observation':base['fresh_observation']}));need(frame['phase']=='capture','environment-checkpoint-receipt-phase');frame.update(observation=v['observation'],navigation_checkpoint=v['navigation'],reboot_current_observation=True);nested.update(frame_state=frame,environment_restoration=reference);a['reboot_capture']=nested;need(new==expected and receipt['after']=={'path':str(o.location(e['order'])/'engine.json'),'sha256':plan['after']['sha256']},'environment-checkpoint-receipt-only-delta')
 if live:need(o.ref(o.location(e['order'])/'engine.json')==receipt['after'],'environment-checkpoint-live-engine-changed')
 return v



ACCEPTANCE_DIRECTORY='work/performance-audit/violation-quality-accept-cold-closure-candidate'
ACCEPTANCE_AUTHORITY_SHA='4afe55b3f5926ad6f8cd5aa8a7123291324d0d9189560d952454d76756a204ec'
def quality_acceptance_authority():
 reference={'path':str(PROJECT/ACCEPTANCE_DIRECTORY/'acceptance-authority.json'),'sha256':ACCEPTANCE_AUTHORITY_SHA};a=doc(reference)
 need(a.get('kind')=='fixed-original-unknown-quality-acceptance-continuation-authority-v1' and a['task_id']==TASK and a['attempt_id']==TASK+'-18' and a['child_index']==16,'quality-acceptance-fixed-authority')
 for entry in a['evidence']:
  need(entry['original']['sha256']==entry['archive']['sha256'],'quality-acceptance-archive-bytes');raw(entry['archive'])
 get=lambda r:proof_document(a,r)
 failure=get(a['failure']);audit=get(a['audit']);parent=get(a['parent']);engine=get(a['engine']);owner=get(a['owner']);child=parent['calls'][16];launch=get(child['launch']);exit=get(child['result']);worker=get(a['worker_exit']);request=get(worker['request']);response=get(worker['response']);handoff=get(a['request']);answer=get(a['response']);att=get(a['attestation'])
 need(failure['kind']=='old-violation18-quality-accept-pure-validation-code-token-failure-v1' and failure['task']==TASK and failure['attempt']==18 and failure['parent_calls']==17 and failure['engine_calls']==76 and failure['natural_child_exit']==child['result'],'quality-acceptance-fixed-failure')
 need(parent['status']=='hold' and parent['error']=='execution-child-stopped' and len(parent['calls'])==17 and len(engine['calls'])==76 and engine['status']=='waiting' and engine['error']is None and engine['phase']=='frames' and engine['index']==1,'quality-acceptance-exact-checkpoint')
 need(parent['order']==engine['order'] and parent['reboot_continuation']==engine['reboot_continuation']==a['activation'] and engine['acceptance']==a['acceptance'] and a['acceptance']['state']=='unknown' and engine['handoff']==a['request'] and a['acceptance']['request']==a['request'] and a['acceptance']['response']==a['response'],'quality-acceptance-original-intent')
 need(child==a['child'] and child['state']=='returned' and exit['returncode']==2 and exit['stderr']=='' and json.loads(exit['stdout'])=={'ok':False,'error':'candidate-code-graph-changed'} and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==16 and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==a['activation'],'quality-acceptance-exact-natural-child')
 argv=child['argv'];need(argv==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'accept','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id','995698666','--pid','632','--response',a['response']['path'],'--response-sha256',a['response']['sha256']],'quality-acceptance-exact-argv')
 need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==a['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','quality-acceptance-natural-worker')
 need(handoff['response_kind']=='violation-frame-qa-response-v1' and handoff['preview']==a['preview'] and handoff['source']==a['source'] and answer=={'request':a['request'],'kind':handoff['response_kind'],'attestation':a['attestation']} and att['registration_preview']==a['preview'] and att['source']==a['source'],'quality-acceptance-source-response')
 need(audit['parent']==a['parent'] and audit['engine']==a['engine'] and audit['owner_before_and_current_exact']==a['owner'] and audit['owner_state_unchanged_since_before_cached_producer_and_accept']is True and audit['final_registration']=={'path':a['final'],'exists':False} and audit['original_acceptance_result']=={'path':a['result'],'exists':False} and audit['original_unknown_intent_preserved']is True,'quality-acceptance-no-effects-audit')
 entries=[e for e in owner['frames']if e.get('registration')==a['preview']];need(len(entries)==1 and entries[0]['state']=='awaiting-visual-review' and entries[0]==audit['owner_registration_entry'] and Path(a['final'])==Path(a['preview']['path']).with_name('registration.json') and Path(a['result'])==Path(a['engine']['path']).parent/'acceptances'/(a['request']['sha256']+'-result.json'),'quality-acceptance-original-owner-paths')
 return reference,a,parent,engine

def _quality_acceptance_child(release_ref,base):
 release=doc(release_ref)
 if release.get('quality_acceptance_continuation')is None:return None
 reference,a,parent,engine=quality_acceptance_authority();need(release['quality_acceptance_continuation']==reference and a['activation']==base['activation'] and a['source']==base['original']['source'] and parent['order']==doc(base['original']['parent'])['order'],'quality-acceptance-release-scope');return a['child']

def _quality_acceptance_transaction(a,release_ref,*,approve,validate,classify,checkpoint=None):
 """One local writer dispatch. Unknown never creates a second approval.
 A present exact final permits only the owner's CAS completion. The original
 Engine result is published only after full read-only validation of both.
 """
 checkpoint=checkpoint or (lambda stage:None)
 root=Path(a['engine']['path']).parent;folder=root/'acceptance-continuations'/a['request']['sha256'];folder.mkdir(parents=True,exist_ok=True)
 expected={'kind':'same-intent-local-quality-registration-continuation-v1','authority':{'path':str(PROJECT/ACCEPTANCE_DIRECTORY/'acceptance-authority.json'),'sha256':ACCEPTANCE_AUTHORITY_SHA},'release':release_ref,'request':a['request'],'response':a['response'],'preview':a['preview'],'attestation':a['attestation'],'source':a['source'],'original_owner':a['owner'],'original_acceptance':a['acceptance']}
 intent=folder/'intent.json'
 if intent.exists():need(doc(o.ref(intent))==expected,'quality-acceptance-continuation-intent-conflict')
 else:o.immutable(intent,expected)
 resultpath=Path(a['result']);final=Path(a['final']);dispatch=folder/'registration-dispatch.json';returned=folder/'registration-returned.json'
 result={'request':a['request'],'response':a['response'],'updates':{}}
 if resultpath.exists():
  need(doc(o.ref(resultpath))==result,'quality-acceptance-original-result-conflict');validate();return o.ref(resultpath)
 if not returned.exists():
  reconcile_only=False
  if dispatch.exists():
   need(doc(o.ref(dispatch))=={'intent':o.ref(intent),'operation':'approve-original-preview-metadata-only'},'quality-acceptance-dispatch-conflict')
   need(final.exists(),'quality-acceptance-dispatch-unknown-no-reapprove');state=classify();need(state in('complete','awaiting'),'quality-acceptance-owner-stage');reconcile_only=(state=='complete')
  else:
   need(not final.exists() and o.ref(Path(a['owner']['path']))==a['owner'],'quality-acceptance-initial-owner-CAS')
   o.immutable(dispatch,{'intent':o.ref(intent),'operation':'approve-original-preview-metadata-only'});checkpoint('dispatched')
  # Existing final uses approve_preview's exact idempotent owner-CAS branch;
  # missing final is reachable only in this call's first durable dispatch.
  if not reconcile_only:approve();checkpoint('registered')
  validated=validate();o.immutable(returned,{'dispatch':o.ref(dispatch),'registration':o.ref(final),'owner':validated});checkpoint('registration-returned')
 else:
  entry=doc(o.ref(returned));need(entry['dispatch']==o.ref(dispatch) and entry['registration']==o.ref(final),'quality-acceptance-returned-conflict');need(validate()==entry['owner'],'quality-acceptance-returned-owner-conflict')
 o.immutable(resultpath,result);checkpoint('original-result-published');return o.ref(resultpath)

def continue_quality_acceptance(release_ref,*,clock,process_reader):
 """Fixed unknown QA intent: local registration only, no Engine/transport call."""
 import fcntl,sqlite3
 release=doc(release_ref);ar,a,parent,engine=quality_acceptance_authority()
 need(release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director' and release.get('quality_acceptance_continuation')==ar,'quality-acceptance-reviewed-release')
 need(dependency_release(dependency_policy()[1]['authorization_release'])==release_ref,'quality-acceptance-current-reviewed-tip');base=verify(a['activation'],live_boot=clock.boot());need(base['historical_child_calls'].get('16')==a['child'],'quality-acceptance-source-graph-verified')
 folder=Path(a['engine']['path']).parent;handles=[]
 try:
  for lp in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   f=lp.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  import region_frame_capture as region
  def classify():
   finalref=o.ref(Path(a['final']));m=doc(finalref);need(m.get('quality_attestation')==a['attestation'],'quality-acceptance-final-attestation');region.validate_frame(m['image']['path'],m,source=a['source']);owner=doc(o.ref(Path(a['owner']['path'])));original=proof_document(a,a['owner'])
   if owner==original:return 'awaiting'
   expected=copy.deepcopy(original);entries=[e for e in expected['frames']if e.get('registration')==a['preview']];need(len(entries)==1 and not entries[0].get('retake_attempt'),'quality-acceptance-fixed-owner-entry');entries[0].update(state='complete',registration=finalref,preview=a['preview']);need(owner==expected,'quality-acceptance-owner-CAS-complete-conflict');return 'complete'
  def validate():
   need(classify()=='complete','quality-acceptance-owner-not-complete');return o.ref(Path(a['owner']['path']))
  complete=folder/'acceptance-continuations'/a['request']['sha256']/'complete.json'
  if complete.exists():
   done=doc(o.ref(complete));need(done['authority']==ar and done['release']==release_ref and done['result']==o.ref(Path(a['result'])) and done['registration']==o.ref(Path(a['final'])),'quality-acceptance-complete-conflict');need(doc(done['result'])=={'request':a['request'],'response':a['response'],'updates':{}},'quality-acceptance-complete-result');validate();return o.ref(complete)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   db.row_factory=sqlite3.Row;t=db.execute('SELECT * FROM tasks WHERE id=?',(TASK,)).fetchone();need(t and t['state']=='failed' and Path(t['active_attempt']).name==a['attempt_id'] and json.loads(t['outer'])==base['original']['outer'],'quality-acceptance-original-failed-task');need(not db.execute("SELECT id FROM tasks WHERE state IN ('running','dispatching','unknown')").fetchall(),'quality-acceptance-no-active-worker');m=db.execute("SELECT state FROM plans WHERE id='morning'").fetchone();owner=db.execute("SELECT value FROM meta WHERE key='resource_owner'").fetchone();need(m and m[0]=='paused' and owner and json.loads(owner[0])==TASK,'quality-acceptance-owner-morning')
  old=proof_document(a,a['worker_started'])['process'];need(process_reader(old['pid'])!=old,'quality-acceptance-worker-still-live');need(o.ref(Path(a['engine']['path']))==a['engine'],'quality-acceptance-original-unknown-engine-CAS')
  expected=copy.deepcopy(parent);expected.update(status='running',error=None);current=doc(o.ref(Path(a['parent']['path'])));need(current in(parent,expected),'quality-acceptance-parent-CAS')
  result=_quality_acceptance_transaction(a,release_ref,approve=lambda:region.approve_preview(a['preview']['path'],a['attestation'],expected_owner=a['owner']),validate=validate,classify=classify)
  need(o.ref(Path(a['engine']['path']))==a['engine'],'quality-acceptance-original-engine-preserved');need(doc(o.ref(Path(a['parent']['path'])))in(parent,expected),'quality-acceptance-parent-raced')
  if doc(o.ref(Path(a['parent']['path'])))!=expected:atomic(Path(a['parent']['path']),expected)
  return o.immutable(complete,{'kind':'same-intent-quality-registration-continuation-complete-v1','authority':ar,'release':release_ref,'result':result,'registration':o.ref(Path(a['final'])),'owner':validate(),'parent':o.ref(Path(a['parent']['path'])),'engine':a['engine'],'original_unknown_preserved':True,'new_UI_or_OCR':False})
 finally:
  for f in reversed(handles):f.close()


COMPLETED_FRAME_DIRECTORY='work/performance-audit/violation-completed-frame-consumption-candidate'
COMPLETED_FRAME_PROOF_SHA='c9223ba4411115e9af0f045dbb9537bedb84aaa1b8c1a952a7d210a2ea204f88'
def _append_completed_frame_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/COMPLETED_FRAME_DIRECTORY/'append-proof.json'),'sha256':COMPLETED_FRAME_PROOF_SHA},'append-completed-frame-fixed-proof');proof=doc(reference);need(proof['kind']=='exact-completed-frame-focus-before-consumption-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-21' and proof['engine_index']==76 and proof['child_index']==19,'append-completed-frame-scope')
 for entry in proof['evidence']:need(entry['original']['sha256']==entry['archive']['sha256'],'append-completed-frame-archive');raw(entry['archive'])
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after'])
 need(b['kind']=='old-violation21-natural-focus-hold-terminal-supplement-v1' and b['parent_snapshot']=={'ref':proof['parent'],'value':parent} and b['engine_snapshot']=={'ref':proof['engine'],'value':engine} and b['relationship']['leaf']=='execution-capture-focus-native-or-QA-pending-no-input' and b['safety']['new_UI_input']==0,'append-completed-frame-exact-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'] and len(parent['calls'])==20 and len(engine['calls'])==77 and parent['calls'][:15]==pp['calls'] and engine['calls'][:75]==ee['calls'],'append-completed-frame-original-prefix')
 ar,aa,ap,ae=quality_acceptance_authority();need(parent['calls'][:17]==ap['calls'] and engine['calls'][:76]==ae['calls'] and 'acceptance'not in engine and engine['accepted'][-1]=={**aa['acceptance'],'state':'complete'},'append-completed-frame-original-accept-complete')
 accepted=get(proof['acceptance_continuation']);need(accepted['authority']==ar and accepted['result']['path']==aa['result'] and get(accepted['result'])=={'request':aa['request'],'response':aa['response'],'updates':{}} and accepted['registration']==proof['completed_registration'],'append-completed-frame-known-registration-result')
 need(parent['status']=='hold' and parent['error']=='execution-child-stopped' and engine['status']=='hold' and engine['error']==b['relationship']['leaf'] and engine['index']==1 and engine['phase']=='frames','append-completed-frame-held-phase')
 last=engine['calls'][76];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['error']==engine['error'] and 'result'not in last and last['context']['order']==doc(parent['order']),'append-completed-frame-failed76')
 for i in(17,18,19):
  child=parent['calls'][i];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned' and exit['returncode']==(2 if i==19 else 0) and exit['launch']==child['launch'] and exit['argv']==launch['argv']==child['argv'] and launch['index']==i and launch['order']==parent['order'] and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'],'append-completed-frame-natural-child')
 child=parent['calls'][19];need(json.loads(get(child['result'])['stdout'])=={'ok':False,'error':engine['error']} and child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-completed-frame-exact-run-argv')
 worker=get(proof['worker_exit']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-completed-frame-natural-worker')
 final=get(proof['completed_registration']);owner=get(proof['owner']);entries=[e for e in owner['frames']if e.get('registration')==proof['completed_registration']];need(len(entries)==1 and entries[0]['state']=='complete' and entries[0]['preview']==aa['preview'] and final['state']=='complete' and final['quality_attestation']==aa['attestation'] and final['source_sha256']==base['original']['source']['sha256'] and proof['completed_registration']['path']==aa['final'] and proof['owner']['path']==aa['owner']['path'],'append-completed-frame-final-owner')
 need(b['focus_journals'] and all(get(f['ref'])['events']==f['events']==[] and get(f['ref'])['reads']==f['reads'] for f in b['focus_journals']),'append-completed-frame-zero-focus-events')
 oldauth,oldbefore,oldafter=source_release(proof['previous_release'],_historical=True);need(proof['guard_source']==oldafter[str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')],'append-completed-frame-reviewed-old-guard')
 tree=ast.parse(raw(next(e['archive']for e in proof['evidence']if e['original']==proof['guard_source'])));klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');frames=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='_frames');calls=[n for n in ast.walk(frames)if isinstance(n,ast.Call)];focus=next(n for n in calls if ast.unparse(n.func)=='self.ensure_capture_focus');capture=next(n for n in calls if ast.unparse(n.func)=='region.capture');need(focus.lineno<capture.lineno,'append-completed-frame-focus-before-existing-consumer')
 guardfn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='ensure_capture_focus');guard=next(n for n in ast.walk(guardfn)if isinstance(n,ast.Call)and ast.unparse(n.func)=='need' and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value==engine['error']);events=[n for n in ast.walk(guardfn)if isinstance(n,ast.Call)and ast.unparse(n.func)=="state['events'].append"];need(events and all(n.lineno>guard.lineno for n in events),'append-completed-frame-guard-before-input-intent')
 return proof,parent,engine

def completed_frame_repair_inventory(base,proof):
 """This fixed completed operation only. Original pre-native inventory is intact."""
 expected=proof_document(proof,proof['completed_native_inventory']);folder=canonical(Path(base['original']['company_folder']));out=canonical(Path(base['capture']['out']));need(expected['kind']=='fixed-protected-completed-frame-native-inventory-v1' and expected['source']==base['original']['source'] and expected['owner']==proof['owner'] and expected['registration']==proof['completed_registration'] and expected['out']==str(out),'completed-frame-inventory-fixed-scope')
 names=set(NATIVE_DIRS)|{p.name for p in folder.iterdir()if p.name.startswith('.')and('native'in p.name or'frame'in p.name)and'state'in p.name};directories=[]
 for name in sorted(names):
  d=folder/name;entry={'directory':str(d),'exists':d.exists()}
  if d.exists():
   need(d.is_dir()and not d.is_symlink(),'completed-frame-inventory-directory');files=[]
   for p in sorted(d.rglob('*')):
    need(not p.is_symlink(),'completed-frame-inventory-symlink')
    if p.is_dir():continue
    r=o.ref(p);files.append(r)
    if p.suffix=='.lock':need(p.stat().st_size==0,'completed-frame-inventory-lock')
    else:need(r==proof['owner'],'completed-frame-unreviewed-native-state')
   entry['files']=files
  directories.append(entry)
 need(directories==expected['native_directories'],'completed-frame-native-inventory-changed');current=[]
 for p in sorted((folder/'frames').rglob('*')):
  need(not p.is_symlink(),'completed-frame-output-symlink')
  if p.is_file():need(p.is_relative_to(out),'completed-frame-other-output');current.append(o.ref(p))
 need(current==expected['frame_files'],'completed-frame-protected-output-changed');need(o.ref(Path(proof['owner']['path']))==proof['owner'] and o.ref(Path(proof['completed_registration']['path']))==proof['completed_registration'],'completed-frame-owner-registration-CAS')
 focus=capture_focus_inventory(out,base['original']['source'],base['capture']['key']);return {'kind':'protected-completed-frame-source-repair-inventory-v1','catalogue':proof['completed_native_inventory'],'native_directories':directories,'frame_files':current,'focus':focus,'owner_complete':True,'no_new_native_input_authorized':True}


IDENTITY_REUSE_DIRECTORY='work/performance-audit/violation-identity-reuse-evidence-lifecycle-candidate'
IDENTITY_REUSE_PROOF_SHA='64c140bc59ac26bed4998ae38520095f67d59ce9261755e6a90f6bb5d40226d0'
def _append_identity_reuse_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/IDENTITY_REUSE_DIRECTORY/'append-proof.json'),'sha256':IDENTITY_REUSE_PROOF_SHA},'append-identity-reuse-fixed-proof');proof=doc(reference)
 need(proof['kind']=='exact-identity-reuse-evidence-immutable-conflict-failure-proof-v1' and proof['task_id']==TASK and proof['attempt_id']==TASK+'-22' and proof['engine_index']==81 and proof['child_index']==20,'append-identity-reuse-fixed-scope')
 for e in proof['evidence']:need(e['original']['sha256']==e['archive']['sha256'],'append-identity-reuse-archive');raw(e['archive'])
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);prev=get(proof['previous_returned']);pp=get(prev['parent_after']);ee=get(prev['engine_after'])
 need(b['kind']=='old-violation22-identity-display-reused-navigation-immutable-conflict-v1' and b['task']==TASK and b['attempt']==22 and b['parent']==proof['parent'] and b['engine']==proof['engine'] and b['engine_calls']==82 and b['parent_calls']==21 and b['rowsPNG_count']==0,'append-identity-reuse-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation'] and parent['order']==engine['order']==doc(base['original']['parent'])['order'] and len(parent['calls'])==21 and len(engine['calls'])==82 and parent['calls'][:20]==pp['calls'] and engine['calls'][:77]==ee['calls'],'append-identity-reuse-original-prefix')
 need(parent['status']=='hold' and parent['error']=='execution-child-stopped' and engine['status']=='hold' and engine['error']=='execution-immutable-conflict' and engine['phase']=='frames' and engine['index']==1 and 'acceptance'not in engine and engine['accepted']==ee['accepted'],'append-identity-reuse-held-accepted-history')
 last=engine['calls'][81];need(last['state']=='failed' and last['step']=='frames' and last['company_index']==1 and last['error']==engine['error'] and 'result'not in last,'append-identity-reuse-failed81')
 for c in engine['calls'][77:81]:need(c['state']=='returned' and c.get('applied')is True and c['step']=='frames' and c['company_index']==1 and c.get('result')is not None,'append-identity-reuse-known-progress')
 capture=engine['companies'][1]['artifacts']['reboot_capture'];need(capture['frame_index']==1 and capture['frames']==[proof['completed_registration']] and capture['frame_state']['phase']=='capture' and capture['frame_state']['observation']==proof['current_observation'] and capture['frame_state']['navigation_checkpoint']==proof['current_navigation'] and capture['frame_state']['capture_focus']==proof['focus'],'append-identity-reuse-capture-checkpoint')
 child=parent['calls'][20];launch=get(child['launch']);x=get(child['result']);need(child['state']=='returned' and x==b['child_exit'] and x['returncode']==2 and x['launch']==child['launch'] and x['argv']==launch['argv']==child['argv'] and launch['index']==20 and launch['order']==parent['order'] and x['reboot_continuation']==launch['reboot_continuation']==proof['activation'] and json.loads(x['stdout'])=={'ok':False,'error':engine['error']} and not x['stderr'],'append-identity-reuse-natural-child')
 need(child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-identity-reuse-exact-argv')
 worker=get(proof['worker_exit']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id'] and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed','append-identity-reuse-natural-worker')
 focus=get(proof['focus']);need(focus['events']==b['focus_events'] and len(focus['events'])==1 and focus['events'][0]['state']=='complete' and focus['events'][0]['calls']==[] and focus['events'][0]['native_focus']['state']=='complete' and focus['events'][0]['native_focus']['binding']==focus['binding'] and focus['events'][0]['native_focus']['action']=='activate-existing-Chrome-PID-only','append-identity-reuse-confirmed-focus-preserved')
 receipt=get(proof['existing_identity_receipt']);nav=get(proof['current_navigation']);ob=get(proof['current_observation']);conflict=b['specific_candidate_conflict'];need(receipt['kind']=='saved-navigation-identity-display-precheck-only-v1' and receipt['navigation']==conflict['old_navigation'] and receipt['observation']==conflict['old_observation'] and proof['current_navigation']==conflict['latest_navigation'] and proof['current_observation']==conflict['latest_observation'] and nav['last_observation']==proof['current_observation'] and nav['observations'][-1]==proof['current_observation'] and all(e['state']=='complete'for e in nav['operations']),'append-identity-reuse-exact-old-new-evidence')
 need(receipt['raw']['tab']==ob['tab'] and ob['source']=='local-dom-bridge' and ob['tab_id']==base['effective_scope']['tab_id'] and ob['tree'].get('truncated')is False and set(conflict['old_vs_current_candidate_different_keys'])=={'navigation','observation','raw'},'append-identity-reuse-same-scope')
 _,_,oldafter=source_release(proof['previous_release'],_historical=True);need(proof['guard_source']==oldafter[str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')],'append-identity-reuse-reviewed-guard')
 tree=ast.parse(raw(next(e['archive']for e in proof['evidence']if e['original']==proof['guard_source'])));klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='ensure_screenshot_full_identity');writes=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and ast.unparse(n.func)=='o.immutable' and n.args and 'reused-navigation.json'in ast.unparse(n.args[0])];need(len(writes)==1 and 'state.update'in ast.unparse(fn),'append-identity-reuse-old-fixed-path-guard')
 return proof,parent,engine

def identity_reuse_repair_inventory(base,proof):
 expected=proof_document(proof,proof['fixed_native_inventory']);folder=canonical(Path(base['original']['company_folder']));anchor=canonical(Path(base['capture']['out']));rows=canonical(Path(proof['rows_out']));need(expected['kind']=='fixed-protected-anchor-and-pre-native-rows-inventory-v1' and expected['source']==base['original']['source'] and expected['owner']==proof['owner'] and expected['registration']==proof['completed_registration'] and expected['anchor_out']==str(anchor) and expected['rows_out']==str(rows) and rows==anchor.parent/'0001-rows' and expected['rows_png_count']==0,'identity-reuse-fixed-inventory-scope')
 names=set(NATIVE_DIRS)|{p.name for p in folder.iterdir()if p.name.startswith('.')and('native'in p.name or'frame'in p.name)and'state'in p.name};directories=[]
 for name in sorted(names):
  d=folder/name;entry={'directory':str(d),'exists':d.exists()}
  if d.exists():
   need(d.is_dir()and not d.is_symlink(),'identity-reuse-native-directory');files=[]
   for p in sorted(d.rglob('*')):
    need(not p.is_symlink(),'identity-reuse-native-symlink')
    if p.is_dir():continue
    r=o.ref(p);files.append(r)
    if p.suffix=='.lock':need(p.stat().st_size==0,'identity-reuse-native-lock')
    else:need(r==proof['owner'],'identity-reuse-other-native-state')
   entry['files']=files
  directories.append(entry)
 need(directories==expected['native_directories_observed'],'identity-reuse-native-inventory-changed');current=[]
 for p in sorted((folder/'frames').rglob('*')):
  need(not p.is_symlink(),'identity-reuse-output-symlink')
  if p.is_file():need(p.is_relative_to(anchor)or p.is_relative_to(rows),'identity-reuse-other-frame-output');current.append(o.ref(p))
 need(current==expected['frame_files'] and not list(rows.rglob('*.png')) and o.ref(Path(proof['owner']['path']))==proof['owner'] and o.ref(Path(proof['completed_registration']['path']))==proof['completed_registration'],'identity-reuse-exact-completed-and-pre-native-catalogue')
 focus=capture_focus_inventory(anchor,base['original']['source'],base['capture']['key']);focus+=capture_focus_inventory(rows,base['original']['source'],doc(proof['focus'])['binding']['chain']+':'+rows.name)
 return {'kind':'protected-complete-anchor-and-pre-native-rows-inventory-v1','catalogue':proof['fixed_native_inventory'],'native_directories':directories,'frame_files':current,'focus':focus,'owner_complete':True,'rows_no_native_capture':True,'original_completed_focus_not_replayed':True}


ROWS_PIXEL_DIRECTORY='work/performance-audit/violation-rows-epoch-pixel-quality-candidate'
ROWS_PIXEL_AUTHORITY_SHA='9478f9b94a6c87df248491fe0dcad71bc3c053e0b123fc647d06d4acb7915318'
def row_pixel_quality_authority(release_ref):
 reference={'path':str(PROJECT/ROWS_PIXEL_DIRECTORY/'row-quality-authority.json'),'sha256':ROWS_PIXEL_AUTHORITY_SHA};a=doc(reference);r=doc(release_ref)
 need(release_ref==dependency_release(dependency_policy()[1]['authorization_release']) and r.get('published')is True and r.get('test_projection_only')is False and r.get('reviewed_by')=='workshop-director' and r.get('rows_pixel_quality_original_waiting')==reference,'rows-pixel-exact-reviewed-release')
 need(a['kind']=='fixed-original-waiting85-epoch-row-pixel-program-quality-authority-v1' and a['task_id']==TASK and a['attempt_id']==TASK+'-23' and a['engine_count']==85 and a['parent_count']==22,'rows-pixel-fixed-authority')
 for e in a['evidence']:need(e['original']['sha256']==e['archive']['sha256'],'rows-pixel-archive-binding');raw(e['archive'])
 base=verify(a['activation']);parent=doc(a['parent']);engine=doc(a['engine']);need(base['original']['source']==a['source'] and source_repair_records(a['activation'])==a['source_records'] and len(a['source_records'])==7,'rows-pixel-original-source-records')
 previous=doc(a['source_records'][-1]);pp=doc(previous['parent_after']);ee=doc(previous['engine_after']);need(parent['status']==engine['status']=='waiting' and len(parent['calls'])==22 and len(engine['calls'])==85 and parent['calls'][:21]==pp['calls'] and engine['calls'][:82]==ee['calls'] and engine['accepted']==ee['accepted'] and 'acceptance'not in engine and engine['phase']=='frames' and engine['index']==1 and engine['handoff']==a['parent_handoff'],'rows-pixel-original-waiting-prefix')
 order=doc(engine['order']);handoff_payload=doc(engine['calls'][84]['result'])['handoff'];expected_handoff={'kind':'violation-execution-handoff-v1','order':engine['order'],'company':order['companies'][engine['index']],'phase':engine['phase'],**handoff_payload}
 need(allowed_calls(engine,a['activation']) and doc(a['parent_handoff'])==expected_handoff and all(c['state']=='returned' and c.get('applied')is True for c in engine['calls'][82:]),'rows-pixel-only-known-returned-progress')
 hand=doc(a['parent_handoff']);need(hand['response_kind']=='violation-frame-qa-response-v1' and hand['preview']==a['preview'] and hand['source']==a['source'] and hand['program_quality_exception']=='quality-DOM-race','rows-pixel-original-request')
 preview=doc(a['preview']);owner=doc(a['owner']);entries=[x for x in owner['frames']if x.get('registration')==a['preview']];need(len(entries)==1 and entries[0]['state']=='awaiting-visual-review' and preview['state']=='awaiting-visual-review' and preview['frame_mode']=='rows' and preview['notice_ids'] and preview['source_sha256']==a['source']['sha256'] and {k:preview['image'][k]for k in ('path','sha256')}==a['cropPNG'] and {k:preview['derivation']['source'][k]for k in ('path','sha256')}==a['rawPNG'],'rows-pixel-original-awaiting-preview')
 anchor=doc(a['anchor_registration']);need(anchor['state']=='complete' and anchor['quality_attestation']==a['anchor_quality'] and any(x.get('registration')==a['anchor_registration'] and x.get('state')=='complete'for x in owner['frames']),'rows-pixel-completed-anchor-preserved')
 for k in ('source','preview','rawPNG','cropPNG','native_metadata','failed_quality','typed_handoff','parent_handoff','owner','anchor_registration','anchor_quality'):raw(a[k])
 return reference,a,base


ROWS_CHARACTER_CACHE_SHA='fa8976340f21560f626fd62fa677db598f76785d6abf157ac0e655acf3da357c'
ROWS_CHARACTER_CACHE_ORIGIN_SHA='f703dab807e2aae1cd0bb01cf94e2f5f2dae9be1bf11534dc762432051a62fd5'
FIRST_CHAIN_CACHE_ROOT_SHA='5786423545f63e56564c141882b24188ba010c39427faf65b8f0e2b80578bfda'
HISTORY_FACTS_POLICY_KIND='finite-reviewed-registration-history-facts-dependency-delta-v1'
def _rows_character_cache_tip(authorization):return dependency_release(authorization)

def _rows_character_cache_first_chain_targets(origin_ref,origin,origin_policy):
 expected={t['target']:t['after']['sha256']for t in origin['targets']+origin['data_targets']};helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');ports=str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py');tip={'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'supervisor-release.json'),'sha256':FIRST_CHAIN_CACHE_ROOT_SHA}
 if tip!=origin_ref:
  need(tip==o.ref(PROJECT/FIRST_CHAIN_DIRECTORY/'supervisor-release.json'),'rows-character-first-chain-fixed-current-root');release=doc(tip);pr,dp=dependency_policy({'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'first-chain-dependency-delta.json'),'sha256':FIRST_CHAIN_POLICY_SHA})
  need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and release.get('previous_release')==dp['previous_release']==origin_ref and release.get('source_repair_dependency_delta')==pr and release.get('source_repair_authorization_release')==dp['authorization_release']==origin_policy['authorization_release'],'rows-character-first-chain-reviewed-successor')
  need(release.get('historical_rows_character_cache_origin')==origin_ref and release.get('rows_character_range_cached_evaluation')==origin['rows_character_range_cached_evaluation'] and not release.get('data_targets')and dp['kind']=='finite-reviewed-first-screenshot-chain-default-dependency-delta-v1'and len(dp['targets'])==1,'rows-character-first-chain-only-two-source-delta')
  pt=dp['targets'][0];need(pt['target']==ports and pt['before']=={'path':ports,'sha256':'3d3e543a8a160444fbabd9ebc91a5ffcf8fc57b6ebabf62c97e25d1b84861946'}and pt['archive']['sha256']==pt['before']['sha256'],'rows-character-first-chain-reviewed-ports-before');raw(pt['archive']);raw(pt['after'])
  predecessor=doc(origin['previous_release']);need(next(x for x in predecessor['targets']if x['target']==ports)['after']['sha256']==pt['before']['sha256']and ports not in expected,'rows-character-first-chain-ports-inherited-origin')
  need(dp['helper_before']=={'path':helper,'sha256':expected[helper]}and dp['helper_archive']['sha256']==expected[helper],'rows-character-first-chain-helper-before');raw(dp['helper_archive'])
  ht=next(t for t in release['targets']if t['target']==helper);need(release['targets']==[ht,{'target':ports,'old_sha256':pt['before']['sha256'],'after':pt['after']}]and ht['old_sha256']==expected[helper],'rows-character-first-chain-exact-CAS');raw(ht['after']);expected[helper]=ht['after']['sha256'];expected[ports]=pt['after']['sha256']
 return expected

def _rows_character_cache_effective_targets(origin_ref,origin,origin_policy):
 helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');validation=str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py');ports=str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py');expected=_rows_character_cache_first_chain_targets(origin_ref,origin,origin_policy);first={'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'supervisor-release.json'),'sha256':FIRST_CHAIN_CACHE_ROOT_SHA};tip=_rows_character_cache_tip(origin_policy['authorization_release']);cursor=tip;seen=set();chain=[]
 while cursor!=first:
  need(cursor['sha256']not in seen and len(chain)<32,'rows-character-cache-finite-reviewed-chain');seen.add(cursor['sha256']);path=canonical(cursor['path']);need(path.name=='supervisor-release.json'and path.is_relative_to(PROJECT/'work/performance-audit'),'rows-character-cache-reviewed-chain-path');release=doc(cursor);pr,dp=dependency_policy(release.get('source_repair_dependency_delta'))
  need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and dp['kind']in(HISTORY_FACTS_POLICY_KIND,NORMAL_PATH_POLICY_KIND)and release.get('source_repair_dependency_delta')==pr and release.get('source_repair_authority')==origin.get('source_repair_authority'),'rows-character-cache-reviewed-history-step')
  need(release.get('historical_rows_character_cache_origin')==origin_ref and release.get('rows_character_range_cached_evaluation')==origin['rows_character_range_cached_evaluation']and release.get('source_repair_authorization_release')==origin_policy['authorization_release']==dp['authorization_release']and release.get('previous_release')==dp['previous_release'],'rows-character-cache-explicit-ancestor-authorization')
  if dp['kind']==NORMAL_PATH_POLICY_KIND:_normal_path_transition(pr,dp,release)
  else:
   need({t['target']for t in dp['targets']}<={validation,ports}and not dp.get('runtime_data')and not release.get('data_targets'),'rows-character-cache-only-reviewed-R-validation-seal-delta');targets=release['targets'];need(len(targets)==len(dp['targets'])+1 and len({t['target']for t in targets})==len(targets)and {t['target']for t in targets}=={helper,*[t['target']for t in dp['targets']]},'rows-character-cache-exact-reviewed-targets')
  chain.append((release,dp));cursor=release['previous_release']
 for release,dp in reversed(chain):
  ht=next(t for t in release['targets']if t['target']==helper);need(dp['helper_before']=={'path':helper,'sha256':expected[helper]}and ht['old_sha256']==expected[helper]and dp['helper_archive']['sha256']==expected[helper],'rows-character-cache-helper-CAS');raw(dp['helper_archive']);raw(ht['after']);expected[helper]=ht['after']['sha256']
  for t in dp['targets']:
   if dp['kind']==NORMAL_PATH_POLICY_KIND and t['target']!=ports:
    need(t['target']not in expected,'rows-character-normal-unique-added-pin');expected[t['target']]=t['before']['sha256']
   elif t['target']==ports and dp['kind']!=NORMAL_PATH_POLICY_KIND:need(t['before']['sha256']=='029441ffb76168484ca5b716bda9f4c2d5bad4598f9ab0bfe71643c8e7bafe3e'and t['after']['sha256']=='1d2f14650340ea0588afd4c3c2a8e4ec57a3d7fcedde4b2161d5b8414742c8d2','rows-character-only-fixed-single-seal-optimization')
   need(t['before']=={'path':t['target'],'sha256':expected[t['target']]}and t['archive']['sha256']==expected[t['target']]and next(x for x in release['targets']if x['target']==t['target'])=={'target':t['target'],'old_sha256':expected[t['target']],'after':t['after']},'rows-character-cache-validation-CAS');raw(t['archive']);raw(t['after']);expected[t['target']]=t['after']['sha256']
 for path,sha in expected.items():need(o.ref(Path(path))['sha256']==sha,'rows-character-cache-all-reviewed-physical-targets')
 need(o.ref(Path(__file__))['sha256']==expected[helper],'rows-character-cache-executing-current-helper');return expected


def rows_character_range_cache_authority(release_ref):
 origin={'path':str(PROJECT/ROWS_CHARACTER_DIRECTORY/'supervisor-release.json'),'sha256':ROWS_CHARACTER_CACHE_ORIGIN_SHA};need(release_ref==origin,'rows-character-only-fixed-original-cache-root');r=doc(release_ref);reference={'path':str(PROJECT/ROWS_CHARACTER_DIRECTORY/'cached-evaluation-authority.json'),'sha256':ROWS_CHARACTER_CACHE_SHA};cache=doc(reference);policyref={'path':str(PROJECT/ROWS_CHARACTER_DIRECTORY/'character-range-dependency-delta.json'),'sha256':ROWS_CHARACTER_POLICY_SHA};pr,dp=dependency_policy(policyref)
 need(r.get('kind')=='supervisor-reviewed-source-release-v1'and r.get('published')is True and r.get('test_projection_only')is False and r.get('reviewed_by')=='workshop-director'and dp['kind']=='finite-reviewed-rows-character-range-pixel-quality-dependency-delta-v1'and r.get('source_repair_dependency_delta')==pr and r.get('previous_release')==dp['previous_release']and r.get('source_repair_authorization_release')==dp['authorization_release'],'rows-character-original-reviewed-root')
 need(r.get('rows_character_range_cached_evaluation')==cache and cache['kind']=='root-pinned-original-rows-character-ROI-cache-v1','rows-character-fixed-original-cache-authority')
 helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');targets=r['targets'];need(len(targets)==5 and len({t['target']for t in targets})==5 and {t['target']for t in targets}=={helper,*[t['target']for t in dp['targets']]},'rows-character-cache-exact-code-targets')
 for t in dp['targets']:need(next(x for x in targets if x['target']==t['target'])=={'target':t['target'],'old_sha256':t['before']['sha256']if t['before']else None,'after':t['after']},'rows-character-cache-code-CAS')
 oldhelper=next(x for x in targets if x['target']==helper);need(oldhelper['old_sha256']==dp['helper_before']['sha256']and oldhelper['after']['path']==str(PROJECT/ROWS_CHARACTER_DIRECTORY/'violation_reboot_continuation.final.py'),'rows-character-cache-original-helper-data')
 for t in targets:raw(t['after']) # immutable payloads, not imported/executed
 need(r.get('data_targets')==[{'target':t['target'],'old_sha256':t['before']['sha256']if t['before']else None,'after':t['after'],'kind':'fixed-runtime-data','mode':493 if t['target'].endswith('/rows-range-ocr')else 420}for t in dp['runtime_data']],'rows-character-cache-exact-runtime-targets')
 _rows_character_cache_effective_targets(origin,r,dp)
 for key in('preview','source','first_plan','first','first_exit','evaluation_result','evaluation_summary','evaluation_freeze','evaluation_script','evaluation_module','original_freeze','original_module'):raw(cache[key])
 for value in cache['locator_runtime'].values():raw(value)
 return cache


# Standalone insertion block; director supplies exact frozen proof SHA.
FIRST_CHAIN_PROOF_SHA='211baba776b7e2e6beea453af9126919c505fbef4536e13b1b73e0066ab4a180'
def _append_first_chain_failure(reference,base):
 import ast
 need(reference=={'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'append-proof.json'),'sha256':FIRST_CHAIN_PROOF_SHA},'append-first-chain-fixed-proof');proof=doc(reference)
 need(proof['kind']=='exact-first-screenshot-chain-missing-key-preadd-failure-proof-v1'and proof['task_id']==TASK and proof['attempt_id']==TASK+'-25'and proof['engine_index']==87 and proof['child_index']==23,'append-first-chain-fixed-scope')
 for e in proof['evidence']+proof['guard_sources']:need(e['original']['sha256']==e['archive']['sha256'],'append-first-chain-archive-bytes');raw(e['archive'])
 originals=[json.dumps(e['original'],sort_keys=True)for e in proof['evidence']];need(len(originals)==len(set(originals)),'append-first-chain-unique-evidence')
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-first-chain-immutable-previous-returned')
 need(b['kind']=='old-violation25-chain-first-add-missing-optional-key-v1'and b['task']==TASK and b['attempt']==25 and b['parent']==proof['parent']and b['engine']==proof['engine']and b['engine_calls']==88 and b['parent_calls']==24 and b['source']==proof['source']and b['assembled_manifest']==proof['assembled_manifest']and b['canonical_ledger']==proof['canonical_ledger'],'append-first-chain-exact-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation']and parent['order']==engine['order']==doc(base['original']['parent'])['order']and len(engine['calls'])==88 and len(parent['calls'])==24 and len(ee['calls'])==82 and len(pp['calls'])==21 and engine['calls'][:82]==ee['calls']and parent['calls'][:21]==pp['calls'],'append-first-chain-preserved-0007-prefix')
 need(parent['status']=='hold'and parent['error']=='execution-child-stopped'and engine['status']=='hold'and engine['error']=="'screenshot_chains'"and engine['index']==1 and engine['phase']=='chain'and 'acceptance'not in engine,'append-first-chain-held-state')
 accepted=b['prior_rows_accepted'];need(accepted['state']=='complete'and engine['accepted']==ee['accepted']+[accepted],'append-first-chain-exact-accepted85')
 request=get(accepted['request']);response=get(accepted['response']);need(response['kind']==request['response_kind']=='violation-frame-qa-response-v1'and response['request']==accepted['request']and response['attestation']==proof['rows_quality'],'append-first-chain-original-qa-response')
 for c in engine['calls'][82:87]:need(c['state']=='returned'and c.get('applied')is True and c['step']=='frames'and c['company_index']==1 and c.get('result')is not None,'append-first-chain-only-returned-frame-progress');get(c['result'])
 need(get(engine['calls'][86]['result'])=={'done':True},'append-first-chain-frame-stage-complete')
 last=engine['calls'][87];need(last==b['last_engine_call']and last['state']=='failed'and last['step']=='chain'and last['company_index']==1 and last['error']==engine['error']and 'result'not in last and 'applied'not in last,'append-first-chain-exact-failed87')
 for i in(21,22,23):
  child=parent['calls'][i];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned'and exit['returncode']==(2 if i==23 else 0)and exit['launch']==child['launch']and exit['argv']==launch['argv']==child['argv']and launch['index']==i and launch['order']==parent['order']and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation'],'append-first-chain-natural-child')
 child=parent['calls'][23];exit=get(child['result']);need(exit==b['child_exit']and not exit['stderr']and json.loads(exit['stdout'])=={'ok':False,'error':"'screenshot_chains'"}and child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-first-chain-exact-failed-child-argv')
 worker=get(proof['worker_exit']);started=get(proof['worker_started']);wr=get(worker['request']);ws=get(worker['response']);need(worker['attempt_id']==started['attempt_id']==wr['attempt_id']==ws['attempt_id']==proof['attempt_id']and wr['task']['id']==ws['task_id']==TASK and worker['returncode']==0 and ws['outcome']=='failed'and proof['worker_exit']==b['exit']and proof['worker_started']==b['started'],'append-first-chain-natural-worker')
 capture=engine['companies'][1]['artifacts']['reboot_capture'];need(capture==b['reboot_capture']and capture['frame_index']==2 and capture['frame_state']=={}and capture['frames']==[proof['anchor_registration'],proof['rows_registration']]and get(engine['calls'][85]['result'])['artifacts']['reboot_capture']==capture,'append-first-chain-both-frames-consumed')
 rows=get(proof['rows_registration']);anchor=get(proof['anchor_registration']);owner=get(proof['owner']);qa=get(proof['rows_quality']);entries=[e for e in owner['frames']if e.get('registration')==proof['rows_registration']];need(rows['state']==anchor['state']=='complete'and rows['frame_mode']=='rows'and anchor['frame_mode']=='anchor'and rows['source_sha256']==anchor['source_sha256']==proof['source']['sha256']==base['original']['source']['sha256']and rows['quality_attestation']==proof['rows_quality']and rows['chain_id']==anchor['chain_id']and len(entries)==1 and entries[0]['state']=='complete'and entries[0]['preview']==qa['registration_preview'],'append-first-chain-existing-frames-owner')
 chain=get(proof['assembled_manifest']);need(chain=={'capture_backend':'screen-capture-kit-dom-region','visibility_policy':rows['visibility_policy'],'source_sha256':proof['source']['sha256'],'chain_id':rows['chain_id'],'frames':[{'image':anchor['image']['path'],'metadata':proof['anchor_registration']},{'image':rows['image']['path'],'metadata':proof['rows_registration']}]},'append-first-chain-existing-assembled-manifest')
 ledger=get(proof['canonical_ledger']);batch=ledger['batches'][proof['batch']];company=last['context']['company'];need(proof['batch']==company['start']+'_'+company['end_exclusive']and ledger['company']==company['company']and ledger['groupid']==company['groupid']and batch['start']==company['start']and batch['end_exclusive']==company['end_exclusive']and batch['source']==proof['ledger_source']=={'path':str(Path(company['root'])/'evidence'/(proof['source']['sha256']+'.json')),'sha256':proof['source']['sha256']}and get(proof['ledger_source'])==get(proof['source'])and raw(next(e['archive']for e in proof['evidence']if e['original']==proof['ledger_source']))==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['source']))and batch['status']=='built'and batch['send_jobs']=={}and 'screenshot_chains'not in batch and b['canonical_batch_status']=='built'and set(b['canonical_batch_keys'])==set(batch),'append-first-chain-only-absent-optional-field')
 get(proof['source']);progress=get(proof['completed_rows_progress']);need(progress['kind']=='actual-original-rows-registration-consumed-chain-phase-v1'and progress['engine_calls']==88 and progress['phase']=='chain'and progress['call85']==engine['calls'][85]and progress['call86']==engine['calls'][86]and progress['reboot_capture']==capture,'append-first-chain-fixed-completed-progress')
 guards={Path(e['original']['path']).name:e for e in proof['guard_sources']};need(set(guards)=={'violation_execution_ports.py','workflow.py'}and guards['violation_execution_ports.py']['original']==proof['guard_source'] ,'append-first-chain-old-guard-shape');_,_,oldafter=source_release(proof['previous_release'],_historical=True);need(oldafter[str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')]==proof['guard_source'],'append-first-chain-reviewed-previous-guard')
 tree=ast.parse(raw(guards['violation_execution_ports.py']['archive']));klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='business');branches=[n for n in ast.walk(fn)if isinstance(n,ast.If)and ast.unparse(n.test)=="phase == 'chain'"and any(isinstance(x,ast.Call)and ast.unparse(x.func)=='w.add_screenshot_chain'for x in ast.walk(n))];need(len(branches)==1,'append-first-chain-old-chain-branch');branch=branches[0];reads=[n for n in ast.walk(branch)if isinstance(n,ast.Subscript)and ast.unparse(n)=="s['batches'][batch]['screenshot_chains']"];adds=[n for n in ast.walk(branch)if isinstance(n,ast.Call)and ast.unparse(n.func)=='w.add_screenshot_chain'];need(len(reads)==len(adds)==1 and reads[0].lineno<=adds[0].lineno and isinstance(branch.body[-1],ast.If)and reads[0]in list(ast.walk(branch.body[-1].test))and adds[0]in list(ast.walk(branch.body[-1].body[0])),'append-first-chain-failed-read-before-add')
 wf=ast.parse(raw(guards['workflow.py']['archive']));add=next(n for n in wf.body if isinstance(n,ast.FunctionDef)and n.name=='add_screenshot_chain');need("b.get('screenshot_chains', [])"in ast.unparse(add)and "b.setdefault('screenshot_chains', []).append(entry)"in ast.unparse(add)and 'not b[\'send_jobs\']'in ast.unparse(add),'append-first-chain-original-writer-contract')
 return proof,parent,engine

def first_chain_repair_inventory(base,proof):
 expected=proof_document(proof,proof['fixed_native_inventory']);folder=canonical(Path(base['original']['company_folder']));frames=folder/'frames';owner=proof_document(proof,proof['owner'])
 need(expected['kind']=='fixed-complete-anchor-rows-pre-chain-inventory-v1'and expected['company_folder']==str(folder)and expected['source']==proof['source']==base['original']['source']and expected['owner']==proof['owner']and expected['frames']==[proof['anchor_registration'],proof['rows_registration']]and expected['chain']==proof['assembled_manifest']and expected['ledger']==proof['canonical_ledger']and expected['unknown_native_allowed']is False,'first-chain-fixed-protected-inventory')
 need({p.name for p in frames.iterdir()}==set(expected['only_frame_dirs'])=={'0000-anchor','0001-rows'},'first-chain-only-original-two-frame-dirs')
 directories=[];names=set(NATIVE_DIRS)|{p.name for p in folder.iterdir()if p.name.startswith('.')and('native'in p.name or'frame'in p.name)and'state'in p.name}
 for name in sorted(names):
  dr=folder/name;entry={'directory':str(dr),'exists':dr.exists()}
  if dr.exists():
   need(dr.is_dir()and not dr.is_symlink(),'first-chain-native-directory');files=[]
   for path in sorted(dr.rglob('*')):
    need(not path.is_symlink(),'first-chain-native-symlink')
    if path.is_dir():continue
    value=o.ref(path);files.append(value)
    if path.suffix=='.lock':need(path.stat().st_size==0,'first-chain-native-lock')
    else:need(value==proof['owner'],'first-chain-only-exact-owner')
   entry['files']=files
  directories.append(entry)
 need(directories==sorted(expected['native_directories'],key=lambda e:e['directory']),'first-chain-native-catalogue-changed');outputs=[]
 for path in sorted(frames.rglob('*')):
  need(not path.is_symlink(),'first-chain-frame-output-symlink')
  if path.is_file():outputs.append(o.ref(path))
 need(outputs==expected['frame_files'],'first-chain-output-catalogue-changed')
 for r in expected['frames']+[expected['owner'],expected['source'],expected['chain'],expected['ledger']]:need(o.ref(Path(r['path']))==r,'first-chain-protected-reference-changed')
 need(len(owner['frames'])==2 and all(e['state']=='complete'for e in owner['frames'])and {json.dumps(e['registration'],sort_keys=True)for e in owner['frames']}=={json.dumps(r,sort_keys=True)for r in expected['frames']},'first-chain-exact-complete-owner-entries')
 focus=capture_focus_inventory(frames/'0000-anchor',base['original']['source'],base['capture']['key']);rows=frames/'0001-rows';binding=doc(o.ref(rows/'capture-focus.json'))['binding'];focus+=capture_focus_inventory(rows,base['original']['source'],binding['chain']+':'+rows.name)
 return {'kind':'protected-original-complete-anchor-rows-chain-inventory-v1','catalogue':proof['fixed_native_inventory'],'native_directories':directories,'frame_files':outputs,'focus':focus,'owner_complete':True,'row_registration_reused':True,'original_native_focus_not_replayed':True,'chain_not_yet_added':True}


# Fixed actual26 proof only; source archives are read as data, never executed.
ZERO_SEND_DIRECTORY='work/performance-audit/violation-zero-send-candidate'
ZERO_SEND_PROOF_SHA='3e450b742b9025799e9e637cfba035d01cf5a9da7e0095374b3c1ad0485095f5'
def _append_zero_send_failure(reference,base):
 import ast,hashlib,execution_timing as timing
 need(reference=={'path':str(PROJECT/ZERO_SEND_DIRECTORY/'append-proof.json'),'sha256':ZERO_SEND_PROOF_SHA},'append-zero-send-fixed-proof');proof=doc(reference)
 need(proof['kind']=='exact-zero-verified-positive-send-guard-failure-proof-v1'and proof['task_id']==TASK and proof['attempt_id']==TASK+'-26'and proof['engine_index']==91 and proof['child_index']==24,'append-zero-send-fixed-scope')
 for e in proof['evidence']+proof['guard_sources']:need(e['original']['sha256']==e['archive']['sha256'],'append-zero-send-archive-bytes');raw(e['archive'])
 originals=[json.dumps(e['original'],sort_keys=True)for e in proof['evidence']];need(len(originals)==len(set(originals)),'append-zero-send-unique-evidence')
 get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-zero-send-immutable-0008')
 need(b['kind']=='old-violation26-sealed-zero-company-positive-send-guard-failure-v1'and b['task']==TASK and b['attempt']==26 and b['parent']==proof['parent']and b['engine']==proof['engine']and b['engine_calls']==92 and b['parent_calls']==25 and b['delivery_manifest']==proof['delivery_manifest']and b['failing_company_ledger']==proof['zero_ledger'],'append-zero-send-exact-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation']and parent['order']==engine['order']==doc(base['original']['parent'])['order']and len(engine['calls'])==92 and len(parent['calls'])==25 and len(ee['calls'])==88 and len(pp['calls'])==24 and engine['calls'][:88]==ee['calls']and parent['calls'][:24]==pp['calls']and engine['accepted']==ee['accepted']and len(engine['accepted'])==3 and all(x['state']=='complete'for x in engine['accepted'])and 'acceptance'not in engine,'append-zero-send-original-prefix-accepted')
 need(parent['status']=='hold'and parent['error']=='execution-child-stopped'and engine['status']=='hold'and engine['error']=='artifacts-and-copy-required'and engine['phase']=='send'and engine['index']==0,'append-zero-send-held-state')
 for i,step,company in((88,'chain',1),(89,'ready',1),(90,'seal',0)):
  c=engine['calls'][i];need(c['state']=='returned'and c.get('applied')is True and c['step']==step and c['company_index']==company and c.get('result')is not None,'append-zero-send-known-progress');get(c['result'])
 last=engine['calls'][91];need(last==b['last_failed_call']and last['state']=='failed'and last['step']=='send'and last['company_index']==0 and last['error']==engine['error']and 'result'not in last and 'applied'not in last and last['context']['artifacts']['source']==proof['source']and last['context']['artifacts']['delivery_manifest']==proof['delivery_manifest'],'append-zero-send-exact-failed91')
 child=parent['calls'][24];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned'and exit==b['child_exit']and exit['returncode']==2 and exit['launch']==child['launch']and exit['argv']==launch['argv']==child['argv']and launch['index']==24 and launch['order']==parent['order']and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation']and not exit['stderr']and json.loads(exit['stdout'])=={'ok':False,'error':'artifacts-and-copy-required'}and child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-zero-send-natural-child-exact')
 worker=get(proof['worker_exit']);started=get(proof['worker_started']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==started['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id']and started['request']==worker['request']and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed'and proof['worker_exit']==b['exit']and proof['worker_started']==b['started'],'append-zero-send-natural-worker')
 ledger=get(proof['zero_ledger']);batch=ledger['batches'][proof['batch']];source=get(proof['source']);company=last['context']['company'];need(batch==b['failing_batch']and type(batch['total'])is int and batch['total']==0 and batch['status']=='zero_verified'and batch['send_jobs']=={}and batch['analysis']==batch['records']==[]and batch['copy']is None and batch['copy_evidence']is None and batch['artifacts']is None and batch['copy_parts']==batch['screenshots']==[]and batch.get('screenshot_chains',[])==[]and batch['completed_at']is None,'append-zero-send-exact-zero-ledger')
 need(proof['batch']==company['start']+'_'+company['end_exclusive']and ledger['company']==source['company']==company['company']and ledger['groupid']==source['groupid']==company['groupid']and batch['start']==source['start']==company['start']and batch['end_exclusive']==source['end_exclusive']==company['end_exclusive']and batch['source']==proof['zero_ledger_source']=={'path':str(Path(company['root'])/'evidence'/(proof['source']['sha256']+'.json')),'sha256':proof['source']['sha256']}and get(proof['zero_ledger_source'])==source and raw(next(e['archive']for e in proof['evidence']if e['original']==proof['zero_ledger_source']))==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['source']))and source['analysis']['total']==source['records']['total']==0 and source['analysis']['rows']==source['records']['rows']==[]and batch['input_fingerprint']==hashlib.sha256(json.dumps(source,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'append-zero-send-bound-source')
 delivery=get(proof['delivery_manifest']);need(delivery==b['delivery']and delivery['kind']=='violation-complete-delivery-manifest-v1'and delivery['fresh_canonical_absence_checked']is True and delivery['scope_sha256']==doc(parent['order'])['scope_sha256']and len(delivery['companies'])==2,'append-zero-send-original-seal')
 zero,positive=delivery['companies'];need(zero['company']==company['company']and zero['batch']==proof['batch']and zero['source']==proof['source']and zero['orders']==[]and positive['company']==doc(parent['order'])['companies'][1]['company']and positive['source']==base['original']['source']and len(positive['orders'])==6 and delivery['orders']==positive['orders'],'append-zero-send-original-zero-and-six')
 orders=delivery['orders'];keys=[x['key']for x in orders];need(len(set(keys))==6 and get(engine['calls'][90]['result'])=={'manifest':proof['delivery_manifest'],'keys':keys}and engine['calls'][90]==b['seal_call90'],'append-zero-send-seal-result-keys')
 gid=doc(parent['order'])['companies'][1]['groupid']
 for order in orders:
  need(order['kind']=='group'and order['scope']=='test'and order['target']=='测试群请忽略'and order['type']in('file','text'),'append-zero-send-test-targets')
  bare={k:v for k,v in order.items()if k not in('key','kind','target','scope')};need(set(bare)==({'part','type','file','file_sha256'}if order['type']=='file'else{'part','type','text_file','text_sha256'})and order['key']=='violation-'+hashlib.sha256(json.dumps([gid,positive['batch'],bare],ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:28],'append-zero-send-canonical-original-keys')
 absence=get(proof['sender_absence_inventory']);need(absence=={'kind':'fixed-zero-send-no-sender-inventory-v1','delivery_manifest':proof['delivery_manifest'],'senders':[{'key':key,'path':str(timing.sender_path(key)),'exists':False}for key in keys]},'append-zero-send-fixed-sender-absence')
 capture=engine['companies'][1]['artifacts']['reboot_capture'];need(capture['frame_index']==2 and capture['frame_state']=={}and capture['frames']==[proof['anchor_registration'],proof['rows_registration']]and engine['companies'][1]['artifacts']['chain']==proof['assembled_manifest'],'append-zero-send-existing-frame-coverage')
 anchor=get(proof['anchor_registration']);rows=get(proof['rows_registration']);qa=get(proof['rows_quality']);owner=get(proof['owner']);entries=[x for x in owner['frames']if x.get('registration')==proof['rows_registration']];need(anchor['state']==rows['state']=='complete'and anchor['frame_mode']=='anchor'and rows['frame_mode']=='rows'and anchor['source_sha256']==rows['source_sha256']==base['original']['source']['sha256']and rows['quality_attestation']==proof['rows_quality']and len(entries)==1 and entries[0]['state']=='complete'and entries[0]['preview']==qa['registration_preview'],'append-zero-send-rows-final-preserved')
 chain=get(proof['assembled_manifest']);need(chain['frames']==[{'image':anchor['image']['path'],'metadata':proof['anchor_registration']},{'image':rows['image']['path'],'metadata':proof['rows_registration']}]and chain['source_sha256']==base['original']['source']['sha256']and chain['chain_id']==anchor['chain_id']==rows['chain_id'],'append-zero-send-chain-preserved')
 guards={Path(e['original']['path']).name:e for e in proof['guard_sources']};need(set(guards)=={'violation_execution_ports.py','workflow.py'}and guards['violation_execution_ports.py']['original']==proof['guard_source'],'append-zero-send-old-guard-shape');_,_,oldafter=source_release(proof['previous_release'],_historical=True);need(oldafter[str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')]==proof['guard_source'],'append-zero-send-reviewed-old-guard')
 tree=ast.parse(raw(guards['violation_execution_ports.py']['archive']));klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ProductionPorts');fn=next(n for n in klass.body if isinstance(n,ast.FunctionDef)and n.name=='business');branch=next(n for n in ast.walk(fn)if isinstance(n,ast.If)and ast.unparse(n.test)=="phase == 'send'");calls=[n for n in ast.walk(branch)if isinstance(n,ast.Call)];send=next(n for n in calls if ast.unparse(n.func)=='w.send_orders');dispatch=next(n for n in calls if ast.unparse(n.func)=='w.dispatch');sendguard=next(n for n in branch.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and ast.unparse(n.value.func)=='need'and len(n.value.args)>1 and isinstance(n.value.args[1],ast.Constant)and n.value.args[1].value=='execution-delivery-orders-changed-after-seal');need(send.lineno<dispatch.lineno and send in list(ast.walk(sendguard)),'append-zero-send-positive-guard-before-dispatch')
 wf=ast.parse(raw(guards['workflow.py']['archive']));sendfn=next(n for n in wf.body if isinstance(n,ast.FunctionDef)and n.name=='send_orders');guard=next(n for n in ast.walk(sendfn)if isinstance(n,ast.Call)and ast.unparse(n.func)=='require'and len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='artifacts-and-copy-required');need(ast.unparse(guard.args[0])=="b['total'] > 0 and b['artifacts'] and b['copy']"and isinstance(sendfn.body[1],ast.Expr)and sendfn.body[1].value is guard,'append-zero-send-old-positive-only-guard')
 return proof,parent,engine

def zero_send_repair_inventory(base,proof):
 expected=proof_document(proof,proof['fixed_native_inventory']);folder=canonical(Path(base['original']['company_folder']));frames=folder/'frames';owner=proof_document(proof,proof['owner'])
 need(expected['kind']=='fixed-complete-anchor-rows-sealed-zero-send-inventory-v1'and expected['company_folder']==str(folder)and expected['source']==proof['positive_source']==base['original']['source']and expected['owner']==proof['owner']and expected['frames']==[proof['anchor_registration'],proof['rows_registration']]and expected['chain']==proof['assembled_manifest']and expected['ledger']==proof['positive_ledger']and expected['unknown_native_allowed']is False,'zero-send-fixed-protected-inventory')
 need({p.name for p in frames.iterdir()}==set(expected['only_frame_dirs'])=={'0000-anchor','0001-rows'},'zero-send-only-original-two-frame-dirs')
 directories=[];names=set(NATIVE_DIRS)|{p.name for p in folder.iterdir()if p.name.startswith('.')and('native'in p.name or'frame'in p.name)and'state'in p.name}
 for name in sorted(names):
  dr=folder/name;entry={'directory':str(dr),'exists':dr.exists()}
  if dr.exists():
   need(dr.is_dir()and not dr.is_symlink(),'zero-send-native-directory');files=[]
   for path in sorted(dr.rglob('*')):
    need(not path.is_symlink(),'zero-send-native-symlink')
    if path.is_dir():continue
    value=o.ref(path);files.append(value)
    if path.suffix=='.lock':need(path.stat().st_size==0,'zero-send-native-lock')
    else:need(value==proof['owner'],'zero-send-only-exact-owner')
   entry['files']=files
  directories.append(entry)
 need(directories==sorted(expected['native_directories'],key=lambda e:e['directory']),'zero-send-native-catalogue-changed');outputs=[]
 for path in sorted(frames.rglob('*')):
  need(not path.is_symlink(),'zero-send-frame-output-symlink')
  if path.is_file():outputs.append(o.ref(path))
 need(outputs==expected['frame_files'],'zero-send-output-catalogue-changed')
 for r in expected['frames']+[expected['owner'],expected['source'],expected['chain'],expected['ledger'],expected['zero_ledger'],expected['delivery_manifest']]:need(o.ref(Path(r['path']))==r,'zero-send-protected-reference-changed')
 need(len(owner['frames'])==2 and all(e['state']=='complete'for e in owner['frames'])and {json.dumps(e['registration'],sort_keys=True)for e in owner['frames']}=={json.dumps(r,sort_keys=True)for r in expected['frames']},'zero-send-exact-complete-owner-entries')
 absence=proof_document(proof,proof['sender_absence_inventory']);need(expected['zero_ledger']==proof['zero_ledger']and expected['delivery_manifest']==proof['delivery_manifest']and expected['sender_absence_inventory']==proof['sender_absence_inventory'],'zero-send-sealed-inventory-binding')
 for sender in absence['senders']:need(not Path(sender['path']).exists(),'zero-send-sender-already-present')
 focus=capture_focus_inventory(frames/'0000-anchor',base['original']['source'],base['capture']['key']);rows=frames/'0001-rows';binding=doc(o.ref(rows/'capture-focus.json'))['binding'];focus+=capture_focus_inventory(rows,base['original']['source'],binding['chain']+':'+rows.name)
 return {'kind':'protected-original-complete-anchor-rows-chain-inventory-v1','catalogue':proof['fixed_native_inventory'],'native_directories':directories,'frame_files':outputs,'focus':focus,'owner_complete':True,'row_registration_reused':True,'original_native_focus_not_replayed':True,'sealed_delivery_preserved':True,'senders_not_started':True}

# Only the original pre-send sealed manifest may retain these three old code refs.
def _sealed_delivery_root_context():
 origin={'path':str(PROJECT/HISTORY_FACTS_DIRECTORY/'supervisor-release.json'),'sha256':'a03ac5dde6c03fd9c3463f8cf44fc76f43bcac5c04090b2e965519eeca22e7e3'}
 tip=dependency_release(dependency_policy()[1]['authorization_release']);cursor=tip;seen=set();helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');latest=None
 while cursor!=origin:
  need(cursor['sha256']not in seen and len(seen)<32,'sealed-code-finite-R-only-chain');seen.add(cursor['sha256']);v=doc(cursor);pr,dp=dependency_policy(v.get('source_repair_dependency_delta'))
  need(dp['kind']==HISTORY_FACTS_POLICY_KIND and dp['targets']==[] and v['previous_release']==dp['previous_release'] and v['source_repair_authorization_release']==dp['authorization_release'] and v['published']is True and v['test_projection_only']is False and v['reviewed_by']=='workshop-director' and not v.get('data_targets') and len(v['targets'])==1,'sealed-code-only-reviewed-R-successor')
  t=v['targets'][0];need(t['target']==helper and t['old_sha256']==dp['helper_before']['sha256'] and dp['helper_before']['path']==helper and dp['helper_archive']['sha256']==t['old_sha256'],'sealed-code-R-before-archive');raw(dp['helper_archive']);raw(t['after']);previous=doc(dp['previous_release']);previous_helper=next(x for x in previous['targets']if x['target']==helper);need(previous_helper['after']['sha256']==t['old_sha256'],'sealed-code-R-contiguous-CAS')
  if latest is None:latest=t['after']
  cursor=v['previous_release']
 release=doc(origin);pr,policy=dependency_policy(release['source_repair_dependency_delta']);return pr,policy,release,latest

def _published_successor(reference):
 """True only when the frozen ref's file has legally moved forward along a
 recorded configuration-source-successors chain (written by every formal
 publication). Successions compose: each hop's link pins one release, and
 the walk continues until a hop lands exactly on the live bytes. Unchanged
 refs return False; unreleased drift or a broken/cyclic chain raises."""
 p=Path(reference['path'])
 live=hashlib.sha256(p.read_bytes()).hexdigest()
 if live==reference['sha256']:return False
 seen=set();current=reference['sha256']
 while True:
  need(current not in seen,'successor-cycle')
  seen.add(current)
  link=PROJECT/'skills/workshop-director/references/configuration-source-successors'/(current+'.json')
  value=doc(o.ref(link));need(value.get('kind')=='reviewed-configuration-code-successor-link-v1','successor-link-shape')
  release=doc(value['release']);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True,'successor-release-shape')
  target=next((t for t in release['targets'] if t['target']==reference['path']),None)
  need(target is not None,'successor-target-missing')
  if target['after']['sha256']==live:return True
  current=target['after']['sha256']
def _sealed_delivery_dependency(reference,delivery_ref):
 if _published_successor(reference):return
 old={str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py'):'5e8a8d23d973bdf636fd85088803cb1e08cf59dd436b944ac43281a22977462a',str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py'):'fc59964f6d7c168a9d161463700a7bf2ce51f31a11e919666893b9ef8822ace9',str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py'):'029441ffb76168484ca5b716bda9f4c2d5bad4598f9ab0bfe71643c8e7bafe3e',str(PROJECT/'skills/violation-notifier/scripts/workflow.py'):'84d06086a1902c7d2e91a1c6e92c8472477dd45e6548014ca1a8f3fd09066942',str(PROJECT/'skills/wecom-messenger/scripts/native.py'):'598726bf1b0c5114b9693661c754f419976df9705650348201783011f4f77e41'}
 if reference not in [{'path':p,'sha256':h}for p,h in old.items()]:return raw(reference)
 sealed={'path':str(PROJECT/'runtime/workshop-director/role-executions/7f9abaac7113a2719465c171e735266463a1a7337711acf8dc8e6d9e5bb83f05/delivery.json'),'sha256':'61e1c689f3ffe1386e7c2628c71e02bd53ec5727d76ccd56b6c15adde7bf32fe'};need(delivery_ref==sealed,'sealed-code-exact-original-delivery');delivery=doc(delivery_ref);need(reference in [r for c in delivery['companies']for r in c['dependencies']],'sealed-code-original-dependency-membership')
 archives,expected=_normal_sealed_delivery_context();need(reference['path']in archives and archives[reference['path']]['sha256']==reference['sha256'],'sealed-code-only-fixed-original-archive');return raw(archives[reference['path']])



# One fixed actual27, already-confirmed same sender. Data only; no UI/replay.
CONFIRMED_SENDER_DIRECTORY='work/performance-audit/violation-confirmed-sender-continuation-candidate'
CONFIRMED_SENDER_PROOF_SHA='b1ca2c284df3550b0a536f152908eb0635dfff7a4fc3edc70901f74342d65a85'
def _append_confirmed_sender_failure(reference,base):
 import hashlib,execution_timing as timing
 need(reference=={'path':str(PROJECT/CONFIRMED_SENDER_DIRECTORY/'append-proof.json'),'sha256':CONFIRMED_SENDER_PROOF_SHA},'append-confirmed-sender-fixed-proof');proof=doc(reference)
 need(proof['kind']=='confirmed-original-sender-postsend-failure-continuation-proof-v1'and proof['task_id']==TASK and proof['attempt_id']==TASK+'-27'and proof['engine_index']==93 and proof['child_index']==25,'append-confirmed-sender-exact-scope')
 for e in proof['evidence']:need(e['original']['sha256']==e['archive']['sha256'],'append-confirmed-sender-archive-bytes');raw(e['archive'])
 originals=[json.dumps(e['original'],sort_keys=True)for e in proof['evidence']];need(len(originals)==len(set(originals)),'append-confirmed-sender-unique-evidence')
 get=lambda r:proof_document(proof,r)
 def at(path):
  hits=[e['original']for e in proof['evidence']if e['original']['path']==str(path)];need(len(hits)==1,'append-confirmed-sender-exact-path-evidence');return hits[0]
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-confirmed-sender-immutable-0009')
 need(b['kind']=='old-violation27-testgroup-three-confirmed-text-unknown-no-resend-v1'and b['task']==TASK and b['attempt']==27 and b['parent']==proof['parent']and b['engine']==proof['engine']and b['engine_calls']==94 and b['parent_calls']==26,'append-confirmed-sender-original-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation']and parent['order']==engine['order']==doc(base['original']['parent'])['order']and len(engine['calls'])==94 and len(parent['calls'])==26 and len(ee['calls'])==92 and len(pp['calls'])==25 and engine['calls'][:92]==ee['calls']and parent['calls'][:25]==pp['calls']and engine['accepted']==ee['accepted']and len(engine['accepted'])==3 and all(e['state']=='complete'for e in engine['accepted'])and 'acceptance'not in engine,'append-confirmed-sender-original-prefix')
 need(parent['status']=='hold'and parent['error']=='execution-child-stopped'and engine['status']=='hold'and engine['error']=='send-unknown-stop-no-resend'and engine['phase']=='send'and engine['index']==1,'append-confirmed-sender-held-original')
 zero=engine['calls'][92];need(zero['step']=='send'and zero['company_index']==0 and zero['state']=='returned'and zero.get('applied')is True and get(zero['result'])['done']is True,'append-confirmed-sender-zero-skip-returned')
 last=engine['calls'][93];need(last==b['last_failed_call']and last['step']=='send'and last['company_index']==1 and last['state']=='failed'and last['error']=='send-unknown-stop-no-resend'and 'result'not in last and 'applied'not in last,'append-confirmed-sender-exact-failed93')
 child=parent['calls'][25];launch=get(child['launch']);exit=get(child['result']);need(child['state']=='returned'and exit==b['child_exit']and exit['returncode']==2 and exit['launch']==child['launch']and exit['argv']==launch['argv']==child['argv']and launch['index']==25 and launch['order']==parent['order']and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation']and not exit['stderr']and json.loads(exit['stdout'])=={'ok':False,'error':'send-unknown-stop-no-resend'}and child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-confirmed-sender-natural-child')
 worker=get(proof['worker_exit']);started=get(proof['worker_started']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==started['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id']and started['request']==worker['request']and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed'and proof['worker_exit']==b['exit']and proof['worker_started']==b['started'],'append-confirmed-sender-natural-worker')
 delivery=get(proof['delivery_manifest']);orders=proof['sealed_orders'];need(delivery['kind']=='violation-complete-delivery-manifest-v1'and delivery['scope_sha256']==doc(parent['order'])['scope_sha256']and delivery['orders']==orders and len(orders)==6 and len({o['key']for o in orders})==6 and delivery['companies'][0]['orders']==[]and delivery['companies'][1]['orders']==orders and delivery['companies'][1]['source']==proof['source']==base['original']['source']and engine['delivery']==ee['delivery']=={'manifest':proof['delivery_manifest'],'keys':[o['key']for o in orders]},'append-confirmed-sender-same-original-seal')
 before=get(proof['sender_before']);after=get(proof['sender_after']);job=before['job'];fingerprint=hashlib.sha256(json.dumps(job,ensure_ascii=False,sort_keys=True).encode()).hexdigest();textorder=orders[3]
 need(job['key']==textorder['key']=='violation-23c573135e7f40b7cbd062e738a4'and job['kind']==textorder['kind']=='group'and job['scope']==textorder['scope']=='test'and job['target']==textorder['target']=='测试群请忽略'and job['type']==textorder['type']=='text'and hashlib.sha256(job['text'].encode()).hexdigest()==textorder['text_sha256']and proof['sender_after']['path']==str(timing.sender_path(job['key']))and Path(proof['sender_after']['path']).name=='78f911cb917c7d900367131b.json','append-confirmed-sender-exact-job-key-text')
 need(before['status']=='unknown'and before['phase']=='verify-sent'and before['pid']==636 and before['baseline']==0 and before['send_intent_at']==proof['original_send_intent_at']=='2026-10-25T16:23:43+08:00'and before['fingerprint']==fingerprint and not before['sent']and not before['ui_confirmed']and before['error']=='ui-tree-incomplete'and before['last_read']=={'read_scope':'current-chat-readonly','node_count':45,'truncated':True,'truncation_reason':'node-role-changed-during-read','transcript_complete':False,'discovery_node_count':55}and len([e for e in before['events']if e['stage']=='send-intent'])==1,'append-confirmed-sender-unknown-original-preserved')
 result=get(proof['readonly_result']);need(result['kind']=='fixed-original-text-sender-readonly-reconciliation-result-v1'and result['original']==proof['sender_before']and result['sender_before']=={'path':proof['sender_after']['path'],'sha256':proof['sender_before']['sha256']}and result['sender_after']==proof['sender_after']and result['summary']==proof['failure']and result['reads']==1 and result['input_used']is False and result['send_intent_preserved']is True and result['status']=='complete'and result['phase']=='done'and result['ui_confirmed']is True and result['error']is None,'append-confirmed-sender-root-readonly-result')
 out=Path(proof['readonly_result']['path']).parent;intent=get(at(out/'intent.json'));snapshot=get(at(out/'snapshot.json'));need(intent['kind']=='fixed-original-text-sender-readonly-reconciliation-intent-v1'and intent['sender']==result['sender_before']and intent['original']==proof['sender_before']and intent['summary']==proof['failure']and intent['fingerprint']==fingerprint and intent['key']==job['key']and intent['pid']==636 and intent['phase']=='verify-sent'and intent['send_intent_at']==before['send_intent_at']and intent['read_budget']==1 and intent['input_allowed']is False,'append-confirmed-sender-one-read-intent')
 need(snapshot['pid']==636 and snapshot['ok']is True and snapshot['read_scope']=='current-chat-readonly'and snapshot['truncated']is False and snapshot['transcript_complete']is True and result['last_read']=={k:snapshot.get(k)for k in('read_scope','node_count','truncated','truncation_reason','transcript_complete','discovery_node_count')},'append-confirmed-sender-complete-read-metadata')
 need(after['events'][:len(before['events'])]==before['events']and len(after['events'])==len(before['events'])+1 and after['events'][-1]=={'stage':'ui-confirmed','at':after['completed_at'],'recipient':job['target'],'recipient_kind':job['kind']},'append-confirmed-sender-events-no-input')
 expected=copy.deepcopy(before);expected.update(status='complete',phase='done',sent=True,ui_confirmed=True,completed_at=after['completed_at'],updated_at=after['updated_at'],last_read=result['last_read'],events=after['events']);expected.pop('error',None);need(after==expected,'append-confirmed-sender-only-readonly-completion-delta')
 ledger=get(proof['ledger']);batch=ledger['batches'][proof['batch']];need(proof['ledger']==b['ledger']and batch['status']=='built'and len(proof['confirmed_senders'])==len(proof['confirmed_receipts'])==3 and set(batch['send_jobs'])=={o['part']for o in orders[:4]},'append-confirmed-sender-original-ledger')
 for i in range(3):
  sender=get(proof['confirmed_senders'][i]);receipt=get(proof['confirmed_receipts'][i]);order=orders[i];entry=batch['send_jobs'][order['part']];need(sender==receipt and proof['confirmed_senders'][i]['sha256']==proof['confirmed_receipts'][i]['sha256']and proof['confirmed_senders'][i]['path']==str(timing.sender_path(order['key']))and sender['status']=='complete'and sender['phase']=='done'and sender['ui_confirmed']is True and sender['job']['key']==order['key']and sender['job']['kind']==order['kind']=='group'and sender['job']['scope']==order['scope']=='test'and sender['job']['target']==order['target']=='测试群请忽略'and sender['job']['type']==order['type']=='file'and sender['job']['file_sha256']==order['file_sha256']and entry['order']==order and entry['confirmed']is True and entry['job_path']==proof['confirmed_senders'][i]['path']and entry['receipt']==proof['confirmed_receipts'][i],'append-confirmed-sender-three-permanent-confirmed')
 need(batch['send_jobs'][textorder['part']]=={'order':textorder,'job_path':proof['sender_after']['path'],'confirmed':False}and proof['missing_senders']==[{'key':o['key'],'path':str(timing.sender_path(o['key'])),'exists':False}for o in orders[4:]],'append-confirmed-sender-pending-same-job-two-missing')
 for o in orders:need(o['kind']=='group'and o['scope']=='test'and o['target']=='测试群请忽略','append-confirmed-sender-no-recipient-upgrade')
 capture=engine['companies'][1]['artifacts']['reboot_capture'];anchor=get(proof['anchor_registration']);rows=get(proof['rows_registration']);owner=get(proof['owner']);chain=get(proof['assembled_manifest']);need(capture['frame_index']==2 and capture['frame_state']=={}and capture['frames']==[proof['anchor_registration'],proof['rows_registration']]and engine['companies'][1]['artifacts']['chain']==proof['assembled_manifest']and anchor['state']==rows['state']=='complete'and rows['quality_attestation']==proof['rows_quality']and anchor['source_sha256']==rows['source_sha256']==proof['source']['sha256']and chain['frames']==[{'image':anchor['image']['path'],'metadata':proof['anchor_registration']},{'image':rows['image']['path'],'metadata':proof['rows_registration']}]and len([e for e in owner['frames']if e.get('registration')==proof['rows_registration']and e['state']=='complete'])==1,'append-confirmed-sender-original-frames-preserved')
 return proof,parent,engine

def confirmed_sender_repair_inventory(base,proof):
 previous=proof_document(proof,proof['previous_returned']);transition=doc(previous['transition']);reference=transition['inventory_ref'];prior=doc(reference);folder=Path(base['original']['company_folder']);frames=folder/'frames'
 need(prior['owner_complete']is True and prior['row_registration_reused']is True and prior['sealed_delivery_preserved']is True,'confirmed-sender-prior-complete-inventory')
 current=[]
 for p in sorted(frames.rglob('*')):
  need(not p.is_symlink(),'confirmed-sender-frame-symlink')
  if p.is_file():current.append(o.ref(p))
 need(current==prior['frame_files'],'confirmed-sender-completed-frame-files-changed')
 for entry in prior['native_directories']:
  directory=Path(entry['directory']);need(directory.parent==folder and directory.exists()==entry['exists']and not directory.is_symlink(),'confirmed-sender-native-directory-changed')
  if entry['exists']:
   files=[]
   for p in sorted(directory.rglob('*')):
    need(not p.is_symlink(),'confirmed-sender-native-symlink')
    if p.is_file():files.append(o.ref(p))
   need(files==entry['files'],'confirmed-sender-native-files-changed')
 refs=[proof[k]for k in ('source','owner','rows_registration','anchor_registration','rows_quality','assembled_manifest','delivery_manifest','ledger','sender_after')]+proof['confirmed_senders']+proof['confirmed_receipts']
 for r in refs:need(o.ref(Path(r['path']))==r,'confirmed-sender-protected-current-reference-changed')
 for item in proof['missing_senders']:need(item['exists']is False and not Path(item['path']).exists(),'confirmed-sender-unstarted-sender-present')
 return {'kind':'confirmed-sender-complete-native-and-original-receipts-inventory-v1','previous_inventory':reference,'protected':refs,'frame_files':current,'native_directories':prior['native_directories'],'missing_senders':proof['missing_senders'],'original_sender_reconciled_readonly':proof['readonly_result'],'business_inputs_used':False}


# Exact actual28 checkpoint only. No source/frame/UI replay or ledger write.
PARTIAL_SEND_DIRECTORY='work/performance-audit/violation-partial-send-checkpoint-candidate'
PARTIAL_SEND_PROOF_SHA='943aec4262a91bb0eb17f646639352ee5a969d4212623999681fd5cd6189c67a'
def _append_partial_send_failure(reference,base):
 need(reference=={'path':str(PROJECT/PARTIAL_SEND_DIRECTORY/'append-proof.json'),'sha256':PARTIAL_SEND_PROOF_SHA},'append-partial-send-fixed-proof');proof=doc(reference)
 need(proof['kind']=='exact-partial-send-ledger-checkpoint-failure-proof-v1'and proof['task_id']==TASK and proof['attempt_id']==TASK+'-28'and proof['engine_index']==93 and proof['child_index']==26,'append-partial-send-exact-scope')
 for e in proof['evidence']:need(e['original']['sha256']==e['archive']['sha256'],'append-partial-send-archive-bytes');raw(e['archive'])
 originals=[json.dumps(e['original'],sort_keys=True)for e in proof['evidence']];need(len(originals)==len(set(originals)),'append-partial-send-unique-evidence');get=lambda r:proof_document(proof,r)
 b=get(proof['failure']);parent=get(proof['parent']);engine=get(proof['engine']);previous=get(proof['previous_returned']);pp=get(previous['parent_after']);ee=get(previous['engine_after']);transition=get(previous['transition'])
 need(raw(proof['previous_returned'])==raw(next(e['archive']for e in proof['evidence']if e['original']==proof['previous_returned'])),'append-partial-send-immutable-0010')
 need(proof['confirmed_sender_proof']=={'path':str(PROJECT/'work/performance-audit/violation-confirmed-sender-continuation-candidate/append-proof.json'),'sha256':'b1ca2c284df3550b0a536f152908eb0635dfff7a4fc3edc70901f74342d65a85'}and transition['append_proof']==proof['confirmed_sender_proof']and transition['activation']==proof['activation']and transition['original_parent']['path']==proof['parent']['path'],'append-partial-send-existing-confirmed-authority')
 prior=get(proof['confirmed_sender_proof'])
 for key in('activation','source','batch','delivery_manifest','sealed_orders','owner','anchor_registration','rows_registration','rows_quality','assembled_manifest','confirmed_senders','confirmed_receipts','missing_senders','sender_before','sender_after','readonly_result','original_send_intent_at'):need(proof[key]==prior[key],'append-partial-send-existing-authority-fields')
 need(proof['current_ledger']==proof['ledger']==prior['ledger']and proof['old_ledger']['path']==proof['current_ledger']['path']and proof['old_ledger']['sha256']=='55dd89cfd6f7accf23d0442cc6efdab2c0bcca137c392e2ef38f59322159fddb'and proof['current_ledger']['sha256']=='224f21cf5f4ac338375801afbb16100d3301280b785058a0f7ea4bbba46ff7bc','append-partial-send-only-original-checkpoint')
 need(b['kind']=='old-violation28-partial-send-ledger-checkpoint-lifecycle-hold-v1'and b['task']==TASK and b['attempt']==28 and b['parent']==proof['parent']and b['engine']==proof['engine']and b['engine_calls']==94 and b['parent_calls']==27 and b['error']=='execution-external-ledger-change','append-partial-send-exact-terminal')
 need(parent['reboot_continuation']==engine['reboot_continuation']==proof['activation']==base['activation']and parent['order']==engine['order']==doc(base['original']['parent'])['order']and len(parent['calls'])==27 and len(pp['calls'])==26 and parent['calls'][:26]==pp['calls']and len(engine['calls'])==94 and engine['calls']==ee['calls']and engine['accepted']==ee['accepted']and len(engine['accepted'])==3 and 'acceptance'not in engine,'append-partial-send-all-original-calls')
 expected=copy.deepcopy(ee);expected.update(status='hold',error='execution-external-ledger-change');need(engine==expected and engine['phase']=='send'and engine['index']==1 and engine['companies'][1]['artifacts']['ledger_current']==proof['old_ledger'],'append-partial-send-no-other-engine-change')
 need(parent['status']=='hold'and parent['error']=='execution-external-ledger-change','append-partial-send-parent-hold')
 child=parent['calls'][26];launch=get(child['launch']);exit=get(child['result']);out=json.loads(exit['stdout']);need(child['state']=='returned'and exit==b['child_exit']and exit['returncode']==0 and exit['launch']==child['launch']and exit['argv']==launch['argv']==child['argv']and launch['index']==26 and launch['order']==parent['order']and exit['reboot_continuation']==launch['reboot_continuation']==proof['activation']and not exit['stderr']and child['argv']==[str(PROJECT/'skills/daily-comment-stats/.venv/bin/python'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution.py'),'run','--order',parent['order']['path'],'--order-sha256',parent['order']['sha256'],'--tab-id',str(base['effective_scope']['tab_id']),'--pid',str(base['effective_scope']['pid']),'--steps','1000'],'append-partial-send-natural-child-zero-exit')
 need(out['kind']=='violation-execution-child-result-v1'and out['order']==parent['order']and out['engine']==proof['engine']and out['status']=='hold'and out['error']=='execution-external-ledger-change'and out['phase']=='send'and out['company_index']==1 and out['waiting_for']is None and out['handoff']is None and out['parent_is_not_business_progress']is True and out['last_action']=={k:engine['calls'][93][k]for k in('step','state','intent_at','error')}and parent['child']==out,'append-partial-send-structured-hold-not-complete')
 expected=copy.deepcopy(pp);expected.update(calls=parent['calls'],child=out,status='hold',error='execution-external-ledger-change');need(parent==expected,'append-partial-send-no-other-parent-change')
 worker=get(proof['worker_exit']);started=get(proof['worker_started']);request=get(worker['request']);response=get(worker['response']);need(worker['attempt_id']==started['attempt_id']==request['attempt_id']==response['attempt_id']==proof['attempt_id']and started['request']==worker['request']and request['task']['id']==response['task_id']==TASK and worker['returncode']==0 and response['outcome']=='failed'and proof['worker_exit']==b['exit']and proof['worker_started']==b['started'],'append-partial-send-natural-worker')
 checks=b['ledger_scope_checks'];need(len(checks)==2 and checks[0]['index']==0 and checks[0]['expected']==checks[0]['actual']==engine['companies'][0]['artifacts']['ledger_current']and checks[0]['exact_equal']is True and checks[1]['index']==1 and checks[1]['expected']==proof['old_ledger']and checks[1]['actual']==proof['current_ledger']and checks[1]['exact_equal']is False,'append-partial-send-exact-ledger-mismatch')
 old=get(proof['old_ledger']);current=get(proof['current_ledger']);batch=proof['batch'];oldbatch=old['batches'][batch];newbatch=current['batches'][batch];need(oldbatch['send_jobs']=={}and oldbatch['status']==newbatch['status']=='built'and newbatch['send_jobs']==b['current_send_jobs']and old['company']==current['company']==doc(parent['order'])['companies'][1]['company']and old['groupid']==current['groupid']==doc(parent['order'])['companies'][1]['groupid'],'append-partial-send-ledger-scope')
 expected=copy.deepcopy(old);expected['batches'][batch]['send_jobs']=newbatch['send_jobs'];expected['updated_at']=current['updated_at'];expected['events']=current['events'];need(current==expected,'append-partial-send-only-send-jobs-ledger-delta')
 orders=proof['sealed_orders'];delivery=get(proof['delivery_manifest']);need(len(orders)==6 and len({x['key']for x in orders})==6 and delivery['orders']==delivery['companies'][1]['orders']==orders and delivery['companies'][0]['orders']==[]and engine['delivery']=={'manifest':proof['delivery_manifest'],'keys':[x['key']for x in orders]}and len(proof['confirmed_senders'])==len(proof['confirmed_receipts'])==3,'append-partial-send-original-six-orders')
 need(current['events'][:len(old['events'])]==old['events'],'append-partial-send-ledger-event-prefix');events=current['events'][len(old['events']):];need(len(events)==7,'append-partial-send-only-seven-events');expected_events=[]
 for i in range(3):
  order=orders[i];sender=get(proof['confirmed_senders'][i]);receipt=get(proof['confirmed_receipts'][i]);entry=newbatch['send_jobs'][order['part']];need(sender==receipt and proof['confirmed_senders'][i]['sha256']==proof['confirmed_receipts'][i]['sha256']and sender['status']=='complete'and sender['phase']=='done'and sender['ui_confirmed']is True and sender['job']['key']==order['key']and entry['order']==order and entry['job_path']==proof['confirmed_senders'][i]['path']and entry['confirmed']is True and entry['receipt']==proof['confirmed_receipts'][i],'append-partial-send-three-confirmed-preserved')
  expected_events.extend([{'at':events[i*2]['at'],'type':'send-job-prepared','batch':batch,'part':order['part'],'job_path':proof['confirmed_senders'][i]['path']},{'at':events[i*2+1]['at'],'type':'test-group-ui-confirmed','batch':batch,'part':order['part']}])
 text=orders[3];expected_events.append({'at':events[6]['at'],'type':'send-job-prepared','batch':batch,'part':text['part'],'job_path':proof['sender_after']['path']});need(events==expected_events and current['updated_at']==events[-1]['at']and all(type(e['at'])is str for e in events),'append-partial-send-exact-owned-events')
 before=get(proof['sender_before']);after=get(proof['sender_after']);result=get(proof['readonly_result']);need(before['job']==after['job']and before['fingerprint']==after['fingerprint']and before['send_intent_at']==after['send_intent_at']==proof['original_send_intent_at']and before['status']=='unknown'and before['phase']=='verify-sent'and after['status']=='complete'and after['phase']=='done'and after['ui_confirmed']is True and result['original']==proof['sender_before']and result['sender_after']==proof['sender_after']and result['input_used']is False and result['reads']==1 and result['status']=='complete'and result['ui_confirmed']is True and newbatch['send_jobs'][text['part']]=={'order':text,'job_path':proof['sender_after']['path'],'confirmed':False}and set(newbatch['send_jobs'])=={x['part']for x in orders[:4]},'append-partial-send-same-text-complete-no-new-notices')
 need(len(proof['missing_senders'])==2 and all(x['exists']is False for x in proof['missing_senders'])and [x['key']for x in proof['missing_senders']]==[x['key']for x in orders[4:]],'append-partial-send-two-original-missing')
 return proof,parent,engine

def _apply_partial_send_metadata(engine,proof):
 if proof['kind']!='exact-partial-send-ledger-checkpoint-failure-proof-v1':return
 need(engine['companies'][1]['artifacts']['ledger_current']==proof['old_ledger'],'partial-send-exact-old-engine-checkpoint')
 engine['companies'][1]['artifacts']['ledger_current']=copy.deepcopy(proof['current_ledger'])

def partial_send_repair_inventory(base,proof):
 previous=proof_document(proof,proof['previous_returned']);transition=doc(previous['transition']);reference=transition['inventory_ref'];prior=doc(reference);folder=Path(base['original']['company_folder']);frames=folder/'frames'
 need(prior['kind']=='confirmed-sender-complete-native-and-original-receipts-inventory-v1','partial-send-prior-confirmed-inventory');current=[]
 for p in sorted(frames.rglob('*')):
  need(not p.is_symlink(),'partial-send-frame-symlink')
  if p.is_file():current.append(o.ref(p))
 need(current==prior['frame_files'],'partial-send-frame-files-changed')
 for entry in prior['native_directories']:
  directory=Path(entry['directory']);need(directory.parent==folder and directory.exists()==entry['exists']and not directory.is_symlink(),'partial-send-native-directory-changed')
  if entry['exists']:
   files=[]
   for p in sorted(directory.rglob('*')):
    need(not p.is_symlink(),'partial-send-native-symlink')
    if p.is_file():files.append(o.ref(p))
   need(files==entry['files'],'partial-send-native-files-changed')
 refs=[proof[k]for k in ('source','owner','rows_registration','anchor_registration','rows_quality','assembled_manifest','delivery_manifest','current_ledger','sender_after')]+proof['confirmed_senders']+proof['confirmed_receipts']
 for r in refs:need(o.ref(Path(r['path']))==r,'partial-send-protected-current-reference-changed')
 for item in proof['missing_senders']:need(item['exists']is False and not Path(item['path']).exists(),'partial-send-unstarted-sender-present')
 return {'kind':'known-partial-send-checkpoint-native-and-receipts-inventory-v1','previous_inventory':reference,'protected':refs,'frame_files':current,'native_directories':prior['native_directories'],'missing_senders':proof['missing_senders'],'engine_single_metadata_delta':{'company_index':1,'field':'ledger_current','before':proof['old_ledger'],'after':proof['current_ledger']},'business_inputs_used':False}


def _normal_path_transition(pr,dp,release):
 fixed={'path':str(PROJECT/'work/performance-audit/violation-normal-send-readonly-integration-candidate/normal-path-dependency-delta.json'),'sha256':'3ac1d540737169ccb8031a691e1e9d8c441258ba10a95a0b7be65d05e02de511'}
 previous={'path':str(PROJECT/'work/performance-audit/violation-partial-send-checkpoint-candidate/supervisor-release.json'),'sha256':'52c4d7ac1dc515ee430ada7cc49553e4b50e5ba5918f08cef911267e5eebb10f'}
 helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');pairs={str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py'):('1d2f14650340ea0588afd4c3c2a8e4ec57a3d7fcedde4b2161d5b8414742c8d2','f6c175129b69326b7a4846e386683377175e9b7dfa9b4971a2f82c661a21ba35'),str(PROJECT/'skills/violation-notifier/scripts/workflow.py'):('84d06086a1902c7d2e91a1c6e92c8472477dd45e6548014ca1a8f3fd09066942','0630ce9e3dd0cf82b5c35d067a4a246c50dfab05caaa417e015cc84cccd6bc0a'),str(PROJECT/'skills/wecom-messenger/scripts/native.py'):('598726bf1b0c5114b9693661c754f419976df9705650348201783011f4f77e41','8b14ddafa8814e4b464636fa8a3e7275e7b08e312bdb98a15842896a64ca3e38')}
 need(pr==fixed and dp['kind']==NORMAL_PATH_POLICY_KIND and dp['previous_release']==release['previous_release']==previous and dp['helper_before']=={'path':helper,'sha256':'5b6f4a31ae447b8135cf236cd42fb9e1b3562d844ce3b35b2a631de5321c402b'}and dp['helper_archive']['sha256']==dp['helper_before']['sha256'],'normal-path-exact-reviewed-policy-before')
 need(len(dp['targets'])==3 and {t['target']for t in dp['targets']}==set(pairs)and not dp.get('runtime_data')and not release.get('data_targets')and release['source_repair_dependency_delta']==pr,'normal-path-only-three-reviewed-targets')
 need(len(release['targets'])==4 and {t['target']for t in release['targets']}=={helper,*pairs},'normal-path-exact-four-release-targets')
 for t in dp['targets']:
  before,after=pairs[t['target']];need(t['before']=={'path':t['target'],'sha256':before}and t['archive']['sha256']==before and t['after']['sha256']==after and next(x for x in release['targets']if x['target']==t['target'])=={'target':t['target'],'old_sha256':before,'after':t['after']},'normal-path-exact-before-after-CAS');raw(t['archive']);raw(t['after'])
 raw(dp['helper_archive']);return {t['target']:t for t in dp['targets']}


def _normal_sealed_delivery_context():
 origin={'path':str(PROJECT/HISTORY_FACTS_DIRECTORY/'supervisor-release.json'),'sha256':'a03ac5dde6c03fd9c3463f8cf44fc76f43bcac5c04090b2e965519eeca22e7e3'};release=doc(origin);pr,policy=dependency_policy(release['source_repair_dependency_delta']);helper=str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py');ports=str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py');validation=str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py')
 old={helper:'5e8a8d23d973bdf636fd85088803cb1e08cf59dd436b944ac43281a22977462a',validation:'fc59964f6d7c168a9d161463700a7bf2ce51f31a11e919666893b9ef8822ace9',ports:'029441ffb76168484ca5b716bda9f4c2d5bad4598f9ab0bfe71643c8e7bafe3e'}
 need(release['kind']=='supervisor-reviewed-source-release-v1'and release['published']is True and release['test_projection_only']is False and release['reviewed_by']=='workshop-director'and policy['kind']==HISTORY_FACTS_POLICY_KIND and release['source_repair_dependency_delta']==pr and release['previous_release']==policy['previous_release']=={'path':str(PROJECT/FIRST_CHAIN_DIRECTORY/'supervisor-release.json'),'sha256':'5786423545f63e56564c141882b24188ba010c39427faf65b8f0e2b80578bfda'},'sealed-code-fixed-original-history-release')
 transitions={t['target']:t for t in policy['targets']};need(len(policy['targets'])==2 and set(transitions)=={ports,validation}and len(release['targets'])==3 and {t['target']for t in release['targets']}==set(old)and not release.get('data_targets')and policy['helper_before']=={'path':helper,'sha256':old[helper]}and policy['helper_archive']['sha256']==old[helper],'sealed-code-original-three-CAS')
 archives={helper:policy['helper_archive']};expected={}
 for t in release['targets']:
  path=t['target'];need(t['old_sha256']==old[path],'sealed-code-original-before');raw(t['after']);expected[path]=t['after']['sha256']
  if path!=helper:
   pt=transitions[path];need(pt['before']=={'path':path,'sha256':old[path]}and pt['archive']['sha256']==old[path]and pt['after']==t['after'],'sealed-code-original-policy-CAS');archives[path]=pt['archive']
 for path,a in archives.items():need(a['sha256']==old[path],'sealed-code-original-archive');raw(a)
 cursor=_rows_character_cache_tip(policy['authorization_release']);seen=set();chain=[]
 while cursor!=origin:
  need(cursor['sha256']not in seen and len(seen)<32,'sealed-code-finite-reviewed-successors');seen.add(cursor['sha256']);p=canonical(cursor['path']);need(p.name=='supervisor-release.json'and p.is_relative_to(PROJECT/'work/performance-audit'),'sealed-code-reviewed-release-path');v=doc(cursor);dr,dp=dependency_policy(v.get('source_repair_dependency_delta'))
  need(v['kind']=='supervisor-reviewed-source-release-v1'and v['published']is True and v['test_projection_only']is False and v['reviewed_by']=='workshop-director'and v.get('source_repair_dependency_delta')==dr and v['previous_release']==dp['previous_release']and v['source_repair_authorization_release']==dp['authorization_release']==policy['authorization_release']and v.get('source_repair_authority')==release.get('source_repair_authority')and not v.get('data_targets'),'sealed-code-reviewed-successor-metadata')
  if dp['kind']==NORMAL_PATH_POLICY_KIND:_normal_path_transition(dr,dp,v)
  else:need(dp['kind']==HISTORY_FACTS_POLICY_KIND and dp['targets']==[]and len(v['targets'])==1,'sealed-code-only-R-or-fixed-normal-successor')
  chain.append((v,dp));cursor=v['previous_release']
 for v,dp in reversed(chain):
  ht=next(t for t in v['targets']if t['target']==helper);need(dp['helper_before']=={'path':helper,'sha256':expected[helper]}and ht['old_sha256']==expected[helper]and dp['helper_archive']['sha256']==expected[helper],'sealed-code-helper-contiguous-CAS');raw(dp['helper_archive']);raw(ht['after']);expected[helper]=ht['after']['sha256']
  if dp['kind']==NORMAL_PATH_POLICY_KIND:
   for t in dp['targets']:
    path=t['target']
    if path!=ports:need(path not in expected and path not in archives,'sealed-code-only-once-normal-added-source');expected[path]=t['before']['sha256'];archives[path]=t['archive']
    need(t['before']=={'path':path,'sha256':expected[path]},'sealed-code-normal-contiguous-CAS');expected[path]=t['after']['sha256']
 for path,sha in expected.items():need(o.ref(Path(path))['sha256']==sha,'sealed-code-reviewed-current-physical-pins')
 need(o.ref(Path(__file__))['sha256']==expected[helper],'sealed-code-executing-current-helper');return archives,expected


def main(argv=None):
 import argparse,subprocess
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 for verb in ('probe','correct-date','resume-date-pre-dispatch','apply','repair-source','continue-quality-acceptance','verify','env-step','env-verify'):
  q=sub.add_parser(verb)
  if verb in ('env-step','env-verify'):
   q.add_argument('--grant',required=True);q.add_argument('--grant-sha256',required=True);q.add_argument('--live',action='store_true')
   if verb=='env-verify':q.add_argument('--reference',required=True);q.add_argument('--sha256',required=True)
  elif verb=='verify':q.add_argument('--reference',required=True);q.add_argument('--sha256',required=True)
  else:
   q.add_argument('--release',required=True);q.add_argument('--release-sha256',required=True)
   if verb in ('probe','correct-date','resume-date-pre-dispatch'):
    for name in ('tab-id','window-id','pid'):q.add_argument('--'+name,type=int,required=True)
    if verb in('correct-date','resume-date-pre-dispatch'):q.add_argument('--failure',required=True);q.add_argument('--failure-sha256',required=True)
   elif verb=='apply':q.add_argument('--fresh-proof',required=True);q.add_argument('--fresh-proof-sha256',required=True)
 args=p.parse_args(argv);sys.path.insert(0,str(PROJECT/'packages/workshop-director'));from workshop_director.common import identity
 import execution_timing as timing
 if args.command in ('env-step','env-verify'):
  grant={'path':args.grant,'sha256':args.grant_sha256};reference={'path':args.reference,'sha256':args.sha256} if args.command=='env-verify' else None;python,config_ref,base_ref=environment_runtime(grant);need(Path(sys.prefix).resolve()==python.parent.parent.resolve(),'environment-child-wrong-interpreter');value=_restore_environment_local(grant,clock=timing.Clock(),process_reader=identity) if args.command=='env-step' else _verify_environment_local(reference,grant,live=args.live,clock=timing.Clock(),process_reader=identity);result={'kind':'controlled-environment-runtime-result-v1','action':args.command,'grant':grant,'reference':reference,'live':args.live,'config':config_ref,'base_config':base_ref,'helper':o.ref(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py'),'result':value}
 elif args.command=='verify':value=verify({'path':args.reference,'sha256':args.sha256});result={'verified':True,'task_id':value['task_id'],'clock_comparable':False,'acceptance_pass':False}
 else:
  release={'path':args.release,'sha256':args.release_sha256};clock=timing.Clock()
  if args.command=='continue-quality-acceptance':result={'continuation':continue_quality_acceptance(release,clock=clock,process_reader=identity),'business_retried':False}
  elif args.command=='repair-source':result={'source_repair':repair_source(release,clock=clock,process_reader=identity),'business_retried':False}
  elif args.command=='apply':result={'activation':apply(release,{'path':args.fresh_proof,'sha256':args.fresh_proof_sha256},clock=clock,process_reader=identity),'business_retried':False}
  else:
   import governance_detail as d
   def comm(pid):return subprocess.check_output(['/bin/ps','-p',str(pid),'-o','comm='],text=True,timeout=5).strip()
   result={'fresh_proof':(correct_date(release,{'path':str(PROJECT/'work/2026-10-23/standalone-oneoff-execution-brief/violation-reboot-probe-date-reset-failure.json'),'sha256':DATE_FAILURE_SHA}if args.command=='resume-date-pre-dispatch'else{'path':args.failure,'sha256':args.failure_sha256},tab_id=args.tab_id,window_id=args.window_id,pid=args.pid,clock=clock,invoke=d.nav.bridge.request,process_reader=identity,comm_reader=comm,pre_dispatch_failure={'path':args.failure,'sha256':args.failure_sha256}if args.command=='resume-date-pre-dispatch'else None) if args.command in('correct-date','resume-date-pre-dispatch') else run_identity(release,tab_id=args.tab_id,window_id=args.window_id,pid=args.pid,clock=clock,invoke=d.nav.bridge.request,process_reader=identity,comm_reader=comm)),'business_started':False}
 print(json.dumps(result,ensure_ascii=False));return 0

# Appended before existing main guard in violation_reboot_continuation.py.
TASK8='task-86161e9560b2bf7aa850c6c2'
TASK8_KIND='verified-violation-company-entry-reboot-continuation-v1'
TASK8_OLD_BOOT='darwin-kern-bootsessionuuid:c8788af9-730f-4310-a59b-af9d830f1d79'
TASK8_ORDER={'path':str(PROJECT/'runtime/workshop-director/role-execution-orders/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f.json'),'sha256':'7174e056432628c0f8c4ac87d324471184f027dce880bfb08f581c7fad04a9dc'}

def task8_scope_facts(snapshot,job,*,tab_id,window_id):
 """Read-only classification. Missing/malformed picker is never assumed closed."""
 import dom_evidence as dom
 import company_configuration as cc
 before=cc.entry_context(snapshot['before'],tab_id,window_id);after=cc.entry_context(snapshot['after'],tab_id,window_id)
 need(before==after and before['groupid']=='1764303851132943','task8-current-entry-context')
 tree=snapshot['tree'];need(tree.get('truncated')is False and snapshot['ping'].get('version')==dom.VERSION and snapshot['ping'].get('safety')=='DOM-only','task8-reviewed-complete-tree')
 cc.require_no_visible_system_error(tree);need(tree.get('url')=='https://life.douyin.com'+urlsplit(before['url']).path,'task8-tree-route')
 identity=dom.identity(tree);expected=cc.configured_source_identity(job,before['groupid']);need(identity==expected,'task8-current-entry-identity')
 prefix='src-components-HeaderV3-components-UserCard-components-SwitchAccountCardModal-index-module__'
 modals=[n for n in dom.nodes(tree)if prefix in n.get('attributes',{}).get('class','') and (n.get('role')=='dialog'or 'life-core-modal-content-container'in n.get('attributes',{}).get('class','').split())]
 if modals:
  _,_,field=cc.picker_parts(tree);need(field.get('attributes',{}).get('value','')=='','task8-no-prior-search-value');phase='searchCompany'
 else:
  # The standard context tick derives its switch selector afresh. Prove the
  # exact visible switch exists; do not copy the old selector as authority.
  dom.unique([n for n in dom.nodes(tree)if n.get('role')=='button'and n.get('name')=='切换'and n.get('selector')and not n.get('disabled')],'task8-fresh-switch-unique')
  phase='context'
 return {'scope':{'tab_id':tab_id,'window_id':window_id},'identity':identity,'entry_groupid':before['groupid'],'url':before['url'],'resume_phase':phase,'new_context_epoch_required':phase=='context'}

def task8_workflow_after(original,admission_ref,admission):
 """One exact metadata epoch; old confirmed input remains an immutable prefix."""
 need(original==doc(admission['original']['workflow']),'task8-original-workflow-bytes')
 need(admission['original']['workflow']['sha256']=='995872b9e6451f9f1487efaf372909ed8082693f79d096dcebd1439c4f019618','task8-fixed-original-workflow')
 calls=original.get('calls',[])
 need(original['phase']=='searchCompany'and original['revision']==2 and len(calls)==1 and calls[0]['key']=='1:context'and calls[0]['state']=='confirmed'and calls[0]['command']['tabId']==original['tab_id'],'task8-original-confirmed-context')
 need(original.get('last_error',{}).get('code')=='company-entry-reviewed-route'and not original.get('reboot_company_epoch'),'task8-only-original-entry-failure')
 new=copy.deepcopy(original);error=new.pop('last_error');new.setdefault('resolved_errors',[]).append({**error,'reboot_continuation':admission_ref,'disposition':'original-confirmed-context-preserved-new-boot-context-epoch'})
 new.update(tab_id=admission['effective_scope']['tab_id'],phase=admission['fresh_facts']['resume_phase'],revision=original['revision']+1)
 new['reboot_company_epoch']={'admission':admission_ref,'original_workflow':admission['original']['workflow'],'old_tab_id':original['tab_id'],'original_calls':copy.deepcopy(calls),'original_revision':2,'maximum_epochs':1,'context_reopened':admission['fresh_facts']['new_context_epoch_required']}
 return new

def task8_validate_prefix(parent,engine,a):
 original=doc(a['original']['parent']);base=doc(a['original']['engine'])
 need(parent['order']==engine['order']==TASK8_ORDER and parent['calls'][:len(original['calls'])]==original['calls'],'task8-parent-call-prefix')
 need(engine['calls'][:len(base['calls'])]==base['calls']and engine['companies'][0]==base['companies'][0],'task8-first-company-or-call-prefix-changed')
 need(all(c['state']=='returned'for c in engine['calls']),'task8-unresolved-new-call')
 return True

def task8_verify(reference,*,live_boot=None,_source_archives=None):
 a=doc(reference)
 need(Path(reference['path'])==o.location(TASK8_ORDER)/'reboot-company-entry'/digest({'entry_recovery':a['entry_recovery'],'fresh_proof':a['fresh_proof']})/'admission.json','task8-canonical-admission')
 need(a.get('kind')==TASK8_KIND and a.get('task_id')==TASK8 and a.get('attempt_id')==TASK8+'-8'and a.get('clock_comparable')is False and a.get('acceptance_pass')is False,'task8-typed-shape')
 need(a['original']['order']==TASK8_ORDER,'task8-fixed-original-order');doc(TASK8_ORDER)
 parent=doc(a['original']['parent']);engine=doc(a['original']['engine']);response=doc(a['original']['response']);worker=doc(a['original']['exit'])
 need(parent['order']==engine['order']==TASK8_ORDER and parent['boot_identity']==TASK8_OLD_BOOT and len(parent['calls'])==7 and engine['phase']=='company'and engine['index']==1,'task8-original-parent-engine')
 need(parent['status']==engine['status']=='running'and parent.get('error')is None and engine.get('error')is None and len(engine['calls'])==32,'task8-after-reviewed-w51-only')
 need(parent.get('violation_initial_ledger_recovery')==a['entry_recovery']and engine.get('resolved_readonly_failures',[])[-1]['proof']==a['entry_recovery']and engine['resolved_readonly_failures'][-1]['index']==32,'task8-entry-recovery-binding')
 import violation_initial_ledger_recovery as entry
 checked=entry.verify_recovered(parent,a['entry_recovery'],installed=_source_archives is None,source_archives=_source_archives);need(checked['kind']=='verified-violation-governance-entry-result-recovery-v1'and checked['code_refs']==a['current_code_refs'],'task8-reviewed-recovery-code-vector')
 need(worker['attempt_id']==response['attempt_id']==TASK8+'-8'and worker['returncode']==0 and response['task_id']==TASK8 and response['outcome']=='failed','task8-natural-original-worker')
 need(a['original']['outer']==doc(a['original']['request'])['task']['outer'],'task8-original-outer')
 need(a['original']['outer']['boot']==TASK8_OLD_BOOT and a['original']['parent_clock']=={k:parent[k]for k in('boot_identity','start_monotonic','wall_started_at','pid','tab_id')},'task8-preserved-clock')
 need(a['segment']['boot']!=TASK8_OLD_BOOT and type(a['segment']['start_monotonic'])in(int,float)and a['segment']['start_monotonic']>=0,'task8-new-segment')
 for r in a['current_code_refs']:source_reference(r,_source_archives)
 need(a['effective_scope']=={**a['fresh_facts']['scope'],'pid':a['effective_process']['pid']},'task8-derived-scope')
 from readonly_tick_snapshot import decode
 fresh=doc(a['fresh_proof']);need(fresh['command']=={'op':'readonly-scope','tabId':a['effective_scope']['tab_id'],'windowId':a['effective_scope']['window_id']}and fresh['raw_reply'].get('ok')is True,'task8-fresh-raw-proof')
 job=doc(a['original']['company_job']);facts=task8_scope_facts(decode(fresh['raw_reply']['result'],a['effective_scope']['tab_id'],a['effective_scope']['window_id']),job,tab_id=a['effective_scope']['tab_id'],window_id=a['effective_scope']['window_id']);need(facts==a['fresh_facts'],'task8-facts-not-derived')
 need(fresh['boot']==a['segment']['boot']and fresh['process']==a['effective_process'],'task8-fresh-process-binding')
 if live_boot is not None:
  from workshop_director.common import identity
  need(live_boot==a['segment']['boot']and identity(a['effective_process']['pid'])==a['effective_process'],'task8-live-process-boot')
 return a

_TASK8_LEGACY_VERIFY=verify
_TASK8_LEGACY_ALLOWED_CALLS=allowed_calls

def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==TASK8_KIND:return task8_verify(reference,live_boot=live_boot)
 return _TASK8_LEGACY_VERIFY(reference,live_boot=live_boot)

def allowed_calls(engine,admission):
 if doc(admission).get('kind')==TASK8_KIND:
  a=task8_verify(admission);return task8_validate_prefix(doc(a['original']['parent']),engine,a)
 return _TASK8_LEGACY_ALLOWED_CALLS(engine,admission)

def task8_probe(output,*,tab_id,window_id,pid,clock,process_reader,invoke):
 """Exactly one readonly-scope request, durable before/after; never input."""
 import fcntl
 folder=o.location(TASK8_ORDER);output=Path(output);need(not output.exists()and not output.with_name(output.name+'.intent.json').exists(),'task8-probe-existing-no-replay')
 process=process_reader(pid);need(process and process['boot']==clock.boot()and process['boot']!=TASK8_OLD_BOOT,'task8-probe-current-process')
 handles=[]
 try:
  for p in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',folder/'companies/1/company-navigation/.bridge-execution.lock'):
   f=p.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  task8_quiescent()
  command={'op':'readonly-scope','tabId':tab_id,'windowId':window_id};o.immutable(output.with_name(output.name+'.intent.json'),{'command':command,'boot':clock.boot(),'process':process,'at':clock.wall().isoformat()})
  raw_reply=invoke(command)
  proof={'kind':'task8-current-company-entry-readonly-proof-v1','command':command,'raw_reply':raw_reply,'boot':clock.boot(),'process':process,'observed_at':clock.wall().isoformat(),'business_inputs':0}
  return o.immutable(output,proof)
 finally:
  for f in reversed(handles):f.close()

def task8_quiescent():
 import sqlite3
 with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
  db.row_factory=sqlite3.Row;row=db.execute('select * from tasks where id=?',(TASK8,)).fetchone();need(row is not None and row['state']=='failed'and row['attempt']==8,'task8-only-original-failed8')
  need(not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'task8-no-inflight')
  owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'task8-original-owner')
  return dict(row)

def task8_apply(entry_recovery,fresh_proof,*,clock,process_reader):
 """Metadata-only CAS under scheduler/resource/parent/engine/WF locks."""
 import fcntl
 from readonly_tick_snapshot import decode
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for p in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',folder/'companies/1/company-navigation/.bridge-execution.lock'):
   f=p.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  task=task8_quiescent();parent_ref=o.ref(folder/'launcher.json');engine_ref=o.ref(folder/'engine.json');wf_ref=o.ref(folder/'companies/1/company-navigation/workflow.json');parent=doc(parent_ref);engine=doc(engine_ref)
  import violation_initial_ledger_recovery as entry
  checked=entry.verify_recovered(parent,entry_recovery);need(checked['kind']=='verified-violation-governance-entry-result-recovery-v1','task8-reviewed-entry-only')
  fresh=doc(fresh_proof);scope={k:fresh['command'][v]for k,v in(('tab_id','tabId'),('window_id','windowId'))};process=fresh['process'];need(process_reader(process['pid'])==process and clock.boot()==fresh['boot']==process['boot'],'task8-fresh-current-process')
  age=(clock.wall()-__import__('datetime').datetime.fromisoformat(fresh['observed_at'])).total_seconds();need(0<=age<=120,'task8-fresh-proof-expired')
  job_ref=o.ref(folder/'companies/1/company-navigation/work-order.json');facts=task8_scope_facts(decode(fresh['raw_reply']['result'],scope['tab_id'],scope['window_id']),doc(job_ref),**scope)
  attempt=PROJECT/'runtime/standalone-workshop-director/attempts'/ (TASK8+'-8');key=digest({'entry_recovery':entry_recovery,'fresh_proof':fresh_proof});out=folder/'reboot-company-entry'/key
  need(not(out/'intent.json').exists(),'task8-metadata-apply-unknown-no-replay');out.mkdir(parents=True,exist_ok=True)
  def archive(r,name):return raw_archive(r,out/name)
  original={'order':TASK8_ORDER,'parent':archive(parent_ref,'parent-before.json'),'engine':archive(engine_ref,'engine-before.json'),'workflow':archive(wf_ref,'workflow-before.json'),'company_job':job_ref,'outer':task['outer']if type(task['outer'])is dict else json.loads(task['outer']),'parent_clock':{k:parent[k]for k in('boot_identity','start_monotonic','wall_started_at','pid','tab_id')}}
  for k in('request','response','exit'):original[k]=o.ref(attempt/(k+'.json'))
  value={'kind':TASK8_KIND,'task_id':TASK8,'attempt_id':TASK8+'-8','original':original,'entry_recovery':entry_recovery,'current_code_refs':checked['code_refs'],'fresh_proof':fresh_proof,'fresh_facts':facts,'effective_scope':{**scope,'pid':process['pid']},'effective_process':process,'segment':{'boot':clock.boot(),'start_monotonic':clock.monotonic(),'wall_started_at':clock.wall().isoformat()},'clock_comparable':False,'acceptance_pass':False}
  ar=o.immutable(out/'admission.json',value)
  # Validate before publishing any state. The public verifier additionally
  # requires the completed metadata receipt, so partial CAS cannot run.
  _task8_verify_payload(ar,live_boot=clock.boot())
  np=copy.deepcopy(parent);np.update(reboot_continuation=ar,clock_comparable=False,elapsed_seconds=None,acceptance_pass=False,end_monotonic=None)
  ne=copy.deepcopy(engine);ne['reboot_continuation']=ar
  nw=task8_workflow_after(doc(original['workflow']),ar,value)
  o.immutable(out/'intent.json',{'kind':'task8-three-journal-metadata-cas-v1','before':{'parent':parent_ref,'engine':engine_ref,'workflow':wf_ref},'admission':ar})
  after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne),('workflow',nw))}
  need(o.ref(Path(parent_ref['path']))==parent_ref and o.ref(Path(engine_ref['path']))==engine_ref and o.ref(Path(wf_ref['path']))==wf_ref,'task8-cas-raced')
  from violation_execution import atomic
  atomic(Path(wf_ref['path']),nw);atomic(Path(engine_ref['path']),ne);atomic(Path(parent_ref['path']),np)
  o.immutable(out/'returned.json',{'kind':'task8-three-journal-metadata-cas-returned-v1','admission':ar,'after':after,'queue_modified':False,'business_inputs':0})
  task8_verify(ar,live_boot=clock.boot());return ar
 finally:
  for f in reversed(handles):f.close()

_task8_verify_payload=task8_verify

def task8_verify(reference,*,live_boot=None,_source_archives=None):
 a=_task8_verify_payload(reference,live_boot=live_boot,_source_archives=_source_archives);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'))
 need(receipt.get('kind')=='task8-three-journal-metadata-cas-returned-v1'and receipt['admission']==reference and receipt['queue_modified']is False and receipt['business_inputs']==0,'task8-metadata-outcome-required')
 p=copy.deepcopy(doc(a['original']['parent']));p.update(reboot_continuation=reference,clock_comparable=False,elapsed_seconds=None,acceptance_pass=False,end_monotonic=None)
 e=copy.deepcopy(doc(a['original']['engine']));e['reboot_continuation']=reference
 need(doc(receipt['after']['parent'])==p and doc(receipt['after']['engine'])==e and doc(receipt['after']['workflow'])==task8_workflow_after(doc(a['original']['workflow']),reference,a),'task8-exact-three-journal-delta')
 return a

_TASK8_LEGACY_MAIN=main

def main(argv=None):
 argv=list(sys.argv[1:]if argv is None else argv)
 if not argv or argv[0]not in('task8-discover','task8-probe','task8-apply','task8-verify'):return _TASK8_LEGACY_MAIN(argv)
 import argparse
 sys.path.insert(0,str(PROJECT/'packages/workshop-director'));sys.path.insert(0,str(PROJECT/'skills/douyin-laike-operator/scripts'))
 from workshop_director.common import identity
 import execution_timing as timing
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
 q=sub.add_parser('task8-discover');q.add_argument('--output',required=True)
 q=sub.add_parser('task8-probe');q.add_argument('--output',required=True)
 for name in('tab-id','window-id','pid'):q.add_argument('--'+name,type=int,required=True)
 q=sub.add_parser('task8-apply')
 for name in('entry-recovery','fresh-proof'):q.add_argument('--'+name,required=True);q.add_argument('--'+name+'-sha256',required=True)
 q=sub.add_parser('task8-verify');q.add_argument('--reference',required=True);q.add_argument('--sha256',required=True)
 args=p.parse_args(argv);clock=timing.Clock()
 if args.command=='task8-verify':result=task8_verify({'path':args.reference,'sha256':args.sha256},live_boot=clock.boot())
 elif args.command=='task8-apply':result=task8_apply({'path':args.entry_recovery,'sha256':args.entry_recovery_sha256},{'path':args.fresh_proof,'sha256':args.fresh_proof_sha256},clock=clock,process_reader=identity)
 else:
  import governance_detail as d
  if args.command=='task8-probe':result=task8_probe(args.output,tab_id=args.tab_id,window_id=args.window_id,pid=args.pid,clock=clock,process_reader=identity,invoke=d.nav.bridge.request)
  else:
   import fcntl
   from workshop_director.adapters import browser_processes,business_tab_candidates
   output=Path(args.output);need(not output.exists()and not output.with_name(output.name+'.intent.json').exists(),'task8-discovery-no-replay')
   with (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock').open('a')as lease:
    fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB);task8_quiescent();processes=browser_processes();need(len(processes['candidates'])==1,'task8-one-chrome-process');command={'op':'tabs'}
    o.immutable(output.with_name(output.name+'.intent.json'),{'kind':'task8-readonly-tab-discovery-intent-v1','command':command,'boot':clock.boot(),'processes':processes})
    reply=d.nav.bridge.request(command);need(reply.get('ok')is True,'task8-tab-discovery-error');inventory={'kind':'dom-only-browser-tab-inventory-v1','command':command,'windows':reply['result']};candidates=business_tab_candidates(inventory,['1764303851132943']);need(len(candidates)==1,'task8-unique-original-entry-tab')
    result=o.immutable(output,{'kind':'task8-readonly-tab-discovery-v1','command':command,'reply':reply,'processes':processes,'selected':candidates[0],'boot':clock.boot(),'business_inputs':0})
 print(json.dumps({'kind':'task8-reboot-maintenance-result-v1','command':args.command,'result':result,'business_retried':False},ensure_ascii=False));return 0

W53_KIND='verified-violation-company-preenqueue-source-successor-v1'
W53_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/reboot-company-entry/5cfce6be7ab5383245215a67da0a1964224661a79f512ca81b9b6acf4d99f93d/admission.json'),'sha256':'dd2caa35ce2fd6acb7176f99180c8b848964a6c54cfaf1dcca493a7c69c012f7'}
W53_SUMMARY={'path':str(PROJECT/'work/2026-10-29/round009-issue51-original-recovery/VI10-summary.json'),'sha256':'f245e5fb50e0da728e87b0ee4df12569b8a05e9167bc5309a01364a552d546d9'}
W53_PATHS={str(PROJECT/p)for p in('skills/chrome-dom-export/scripts/bridge.py','skills/violation-notifier/scripts/violation_reboot_continuation.py','skills/violation-notifier/scripts/violation_initial_ledger_recovery.py','skills/workshop-director/scripts/collection_ready.py','skills/violation-notifier/scripts/violation_execution_ports.py')}

def w53_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W53_PATHS,'W53-exact-reviewed-five-source-release')
 base=doc(W53_BASE);by={r['path']:r for r in base['current_code_refs']};archives={};codes=copy.deepcopy(base['current_code_refs'])
 for t in release['targets']:
  old=by[t['target']];need(t['old_sha256']==t['before']['sha256']==old['sha256']and t['mode']==420 and t['after']['sha256']!=old['sha256'],'W53-source-exact-before-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':old,'archive':t['before']};codes[codes.index(old)]=current
 need(len(codes)==159 and len(archives)==5,'W53-no-added-source-slot');return archives,codes

def w53_failure(parent,engine,wf):
 summary=doc(W53_SUMMARY);need(parent['reboot_continuation']==engine['reboot_continuation']==W53_BASE and parent['order']==engine['order']==TASK8_ORDER,'W53-original-task-admission');need(len(parent['calls'])==8 and parent['status']=='hold'and parent['error']=='execution-child-stopped','W53-parent-natural-held8');need(len(engine['calls'])==34 and engine['status']=='hold'and engine['phase']=='company'and engine['index']==1 and engine['error']=='bridge-command-failed: configured-company-admission-rejected'and all(c['state']=='returned'for c in engine['calls'][:33]),'W53-engine-exact-failed34')
 failed=engine['calls'][33];need(failed['state']=='failed'and failed['step']=='company'and failed['company_index']==1 and failed['error']==engine['error']and 'result'not in failed,'W53-only-failed-company-local-return');need(wf['phase']=='searchCompany'and wf['revision']==4 and len(wf['calls'])==3 and wf['calls'][0]['state']==wf['calls'][1]['state']=='confirmed'and wf['calls'][0]['key']=='1:context'and wf['calls'][1]['key']=='3:context','W53-two-context-inputs-preserved');search=wf['calls'][2];need(search['state']=='unknown'and search['key']=='4:searchCompany'and search['pre_enqueue_rejection']['kind']=='owned-preenqueue-no-delivery-v1','W53-original-owned-unknown')
 failure=wf['bridge_failures'][-1];reply=failure['reply'];need(failure['command']==search['command']and reply=={'ok':False,'error':'configured-company-admission-rejected','error_type':'ValueError','stage':'pre-enqueue','outcome':'not-delivered','job_created':False,'execution_started':False,'retry':'Never replay an existing UNKNOWN intent; reconcile its original evidence.'},'W53-exact-preenqueue-nondelivery')
 call=parent['calls'][7];launch=doc(call['launch']);ex=doc(call['result']);out=json.loads(ex['stdout']);need(call['state']=='returned'and ex['returncode']==2 and not ex['stderr']and launch['index']==7 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W53_BASE,'W53-natural-new-segment-child-two')
 need(out=={'ok':False,'error':engine['error']}and parent.get('child')is None,'W53-exact-inner-rc2-error-output');worker=summary['worker'];need(worker['returncode']==0 and worker['attempt_id']==TASK8+'-10'and summary['response']['outcome']=='failed','W53-natural-worker10')
 return call

def w53_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':33,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w53_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'original-preenqueue-failure-not-success'});return after

def w53_verify(reference,*,live_boot=None,_source_archives=None):
 p=doc(reference);need(p.get('kind')==W53_KIND and p['task_id']==TASK8 and p['attempt_id']==TASK8+'-10'and p['previous_admission']==W53_BASE and p['failure_summary']==W53_SUMMARY,'W53-fixed-task10-shape');archives,codes=w53_sources(p['release'],_source_archives=_source_archives);need(p['source_archives']==archives and p['current_code_refs']==codes,'W53-derived-five-source-view');base=task8_verify(W53_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});before=doc(p['parent_before']);engine=doc(p['engine_before']);wf=doc(p['workflow_before']);summary=doc(W53_SUMMARY);need(p['parent_before']['sha256']==summary['parent_frontier']['reference']['sha256']and p['engine_before']['sha256']==summary['engine_frontier']['reference']['sha256']and p['workflow_before']['sha256']==summary['workflow']['sha256'],'W53-fixed-before-archives');call=w53_failure(before,engine,wf);returned=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(returned['admission']==reference and doc(returned['parent_after'])==w53_parent_after(before,reference)and doc(returned['engine_after'])==w53_engine_after(engine,reference),'W53-completed-two-CAS-only');return {**base,'kind':W53_KIND,'task_id':TASK8,'attempt_id':TASK8+'-10','previous_admission':W53_BASE,'current_code_refs':codes,'approved_parent_calls':before['calls'],'historical_child_count':7,'preenqueue_failed_child':{'index':7,'call':call,'returncode':2},'successor':reference,'engine_prefix':w53_engine_after(engine,reference)['calls'],'source_archives':archives}

_W53_PREVIOUS_VERIFY=verify
_W53_PREVIOUS_ALLOWED=allowed_calls

def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W53_KIND:return w53_verify(reference,live_boot=live_boot)
 return _W53_PREVIOUS_VERIFY(reference,live_boot=live_boot)

def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W53_KIND:return _W53_PREVIOUS_ALLOWED(engine,admission)
 a=w53_verify(admission);need(engine['calls'][:33]==a['engine_prefix']and engine['companies'][0]==doc(a['original']['engine'])['companies'][0],'W53-original33-and-Shanghai-preserved');return all(c['state']=='returned'for c in engine['calls'])

def w53_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',folder/'companies/1/company-navigation/.bridge-execution.lock'):
   f=path.open('a');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   db.row_factory=sqlite3.Row;task=db.execute('select * from tasks where id=?',(TASK8,)).fetchone();need(task is not None and task['state']=='failed'and task['attempt']==10 and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W53-only-failed10-no-inflight');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W53-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-10')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W53-original-worker-not-live')
  summary=doc(W53_SUMMARY);pr=summary['parent_frontier']['reference'];er=summary['engine_frontier']['reference'];wr=summary['workflow'];parent=doc(pr);engine=doc(er);wf=doc(wr);w53_failure(parent,engine,wf);archives,codes=w53_sources(release_ref);task8_verify(W53_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'company-preenqueue-source-successors'/digest({'release':release_ref,'failure':W53_SUMMARY});need(not(out/'intent.json').exists(),'W53-partial-CAS-no-replay');out.mkdir(parents=True,exist_ok=True)
  p={'kind':W53_KIND,'task_id':TASK8,'attempt_id':TASK8+'-10','previous_admission':W53_BASE,'failure_summary':W53_SUMMARY,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'workflow_before':raw_archive(wr,out/'workflow-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',p);np=w53_parent_after(parent,reference);ne=w53_engine_after(engine,reference);pa=o.immutable(out/'parent-after.json',np);ea=o.immutable(out/'engine-after.json',ne);o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er,'workflow':wr},'after':{'parent':pa,'engine':ea},'WF_changed':False})
  need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er and o.ref(Path(wr['path']))==wr,'W53-CAS-frontier-raced');from violation_execution import atomic;atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':pa,'engine_after':ea,'WF_changed':False,'business_inputs':0});w53_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

W55_KIND='verified-violation-extension-guard-review-route-successor-v1'
W55_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/company-preenqueue-source-successors/1995f9ae51eeb3ccdbb60946ba3db7c37dc404e48eef8dd086ad1090ff95189f/admission.json'),'sha256':'f9b972d39a5b8caa64284e1be273daa0629c2df4429dcf937b941d61be8abeba'}
W55_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue54-original-recovery/VI12-summary.json'),'sha256':'12fb70832f009bdb77cf1267b3eb5d92cb527c0556c5f9520a1a5fd33b99f103'}
W55_GUARD_MODULE={'path':str(PROJECT/'work/performance-audit/extension-guard-preinput-proof-candidate/guard_proof.py'),'sha256':'3a1a29eb021563e4013d7daf848e53dc5ba069c3f39966de8dfffdefb3ae67db'}
W55_GUARD_PROOF={'path':str(PROJECT/'work/performance-audit/extension-guard-preinput-proof-candidate/saved-proof.json'),'sha256':'beb0b1cd195dcfe167330e4237d5c61335b51b2507b4ddc57d1c6a18fa4c174c'}
W55_ROUTE={'path':str(PROJECT/'work/2026-10-29/round009-issue55-original-recovery/review-route-once/complete.json'),'sha256':'1403e5a356d09868dde34e022747dc86a80e89b1fcb5c8701dd2866ca638edcc'}
W55_ACTOR={'path':str(PROJECT/'work/performance-audit/task8-review-route-restoration-candidate/restore_review_route_once.py'),'sha256':'a04f304a9297475b4736824559f76cf6070ce06a79ffef285ea6fb58353363c8'}
W55_PATHS={str(PROJECT/p)for p in('skills/douyin-laike-operator/scripts/bridge-workflow.py','skills/violation-notifier/scripts/violation_reboot_continuation.py','skills/violation-notifier/scripts/violation_execution_ports.py','skills/workshop-director/scripts/collection_ready.py')}

def w55_module(reference,name):
 import importlib.util
 raw(reference);spec=importlib.util.spec_from_file_location(name,reference['path']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def w55_route_facts():
 proof=w55_module(W55_GUARD_MODULE,'W55_exact_preinput_verifier').verify(W55_GUARD_PROOF);route=doc(W55_ROUTE);intent=doc(route['intent']);need(route['kind']=='verified-original-failed12-review-route-restoration-v1'and route['proof']==intent['proof']==W55_GUARD_PROOF and route['WF_unchanged']is True and route['search_granted']is False and intent['program']==W55_ACTOR and intent['original_workflow']==proof['workflow'],'W55-exact-route-lineage');actor=w55_module(W55_ACTOR,'W55_exact_navigation_reader');job=doc(o.ref(o.location(TASK8_ORDER)/'companies/1/company-navigation/work-order.json'));reply=doc(route['after']);need(reply.get('ok')is True,'W55-route-after-observed');facts=actor.target_facts(reply['result'],job,route['result']['scope']['tab_id'],route['result']['scope']['window_id'],proof['current_identity']);need(facts==route['result']and facts['groupid']==proof['source_groupid']and facts['search_performed']is False,'W55-current-review-identity-not-decorative');return proof,route

def w55_sources(release_ref,*,_source_archives=None):
 value=doc(release_ref);need(value.get('kind')=='supervisor-reviewed-source-release-v1'and value.get('published')is True and value.get('test_projection_only')is False and value.get('reviewed_by')=='workshop-director'and len(value['targets'])==4 and {t['target']for t in value['targets']}==W55_PATHS,'W55-exact-reviewed-four-source-release');base=doc(W55_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in value['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W55-exact-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==4,'W55-no-added-slot');return archives,codes

def w55_failure(parent,engine,wf):
 summary=doc(W55_FAILURE);proof,route=w55_route_facts();need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W55_BASE and len(parent['calls'])==9 and parent['status']=='hold'and parent['error']=='execution-child-stopped','W55-exact-held-parent9');need(engine['status']=='hold'and engine['phase']=='company'and engine['index']==1 and len(engine['calls'])==34 and all(c['state']=='returned'for c in engine['calls'][:33])and engine['calls'][33]['state']=='failed'and engine['calls'][33]['step']=='company'and engine['calls'][33]['error']==engine['error']=='bridge-command-failed: company capability source scope changed','W55-exact-engine-preinput34');need(wf==doc(proof['workflow_archive'])and len(wf['calls'])==3 and wf['calls'][-1]['key']=='4:searchCompany'and wf['calls'][-1]['state']=='unknown'and wf['calls'][-1]['pre_enqueue_recovery_attempted']is True,'W55-original-UNKNOWN-attempt-preserved');call=parent['calls'][8];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':engine['error']}and parent.get('child')is None and launch['index']==8 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W55_BASE,'W55-natural-child8-input-guard-error');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-12','W55-natural-worker12');return proof,route,call

def w55_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-extension-preinput-failure-not-success'});return after

def w55_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':33,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w55_workflow_after(before):
 after=copy.deepcopy(before);error=after.pop('last_error');after.setdefault('resolved_errors',[]).append({**error,'proof':W55_GUARD_PROOF,'route_complete':W55_ROUTE,'disposition':'known-extension-preinput-route-restored-not-search-success'});after['extension_guard_route_recovery']={'kind':'verified-workflow-extension-guard-route-recovery-v1','proof':W55_GUARD_PROOF,'route_complete':W55_ROUTE};return after

def w55_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W55_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-12'and value['previous_admission']==W55_BASE and value['failure']==W55_FAILURE and value['guard_proof']==W55_GUARD_PROOF and value['route_complete']==W55_ROUTE,'W55-fixed-task12-successor');archives,codes=w55_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W55-derived-source-view');base=w53_verify(W55_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});parent=doc(value['parent_before']);engine=doc(value['engine_before']);wf=doc(value['workflow_before']);summary=doc(W55_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256']and value['workflow_before']['sha256']==summary['WF']['reference']['sha256'],'W55-fixed-before-archives');_,_,call=w55_failure(parent,engine,wf);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w55_parent_after(parent,reference)and doc(receipt['engine_after'])==w55_engine_after(engine,reference)and doc(receipt['workflow_after'])==w55_workflow_after(wf),'W55-completed-three-CAS-required');return {**base,'kind':W55_KIND,'attempt_id':TASK8+'-12','previous_admission':W55_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'guard_failed_child':{'index':8,'call':call,'returncode':2},'successor':reference,'engine_prefix':w55_engine_after(engine,reference)['calls']}

_W55_PREVIOUS_VERIFY=verify
_W55_PREVIOUS_ALLOWED=allowed_calls

def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W55_KIND:return w55_verify(reference,live_boot=live_boot)
 return _W55_PREVIOUS_VERIFY(reference,live_boot=live_boot)

def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W55_KIND:return _W55_PREVIOUS_ALLOWED(engine,admission)
 value=w55_verify(admission);need(engine['calls'][:33]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W55-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w55_apply(release_ref,*,clock,process_reader):
 import sqlite3,fcntl
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',folder/'companies/1/company-navigation/.bridge-execution.lock'):
   need(o.canonical(path)==path and path.is_file(),'W55-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone();need(row==('failed',12)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W55-original-failed12');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W55-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-12')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W55-original-worker-dead');summary=doc(W55_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];wr=summary['WF']['reference'];parent=doc(pr);engine=doc(er);wf=doc(wr);w55_failure(parent,engine,wf);archives,codes=w55_sources(release_ref);w53_verify(W55_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'extension-guard-route-successors'/digest({'release':release_ref,'failure':W55_FAILURE,'route':W55_ROUTE});need(not(out/'intent.json').exists(),'W55-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W55_KIND,'task_id':TASK8,'attempt_id':TASK8+'-12','previous_admission':W55_BASE,'failure':W55_FAILURE,'guard_proof':W55_GUARD_PROOF,'route_complete':W55_ROUTE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'workflow_before':raw_archive(wr,out/'workflow-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w55_parent_after(parent,reference);ne=w55_engine_after(engine,reference);nw=w55_workflow_after(wf);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne),('workflow',nw))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er,'workflow':wr},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er and o.ref(Path(wr['path']))==wr,'W55-three-CAS-before-raced');from violation_execution import atomic;atomic(Path(wr['path']),nw);atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'workflow_after':after['workflow'],'business_inputs':0});w55_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

if __name__=='__main__':raise SystemExit(main())

# Exact original task13 read-detail parser failure; no UI input or child rewind.
W56_KIND='verified-violation-detail-subject-object-source-successor-v1'
W56_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/extension-guard-route-successors/a50a208f7dd2b2976435bfc35f312523168621e89e7ef2fc0caf69e8492fc8f6/admission.json'),'sha256':'67df7dd1923b83ebb1ea5ce2f98a5276e720ef937de46643c653dc9331128cd9'}
W56_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue55-original-recovery/VI13-summary.json'),'sha256':'00df60a1612fbab6aba4e5167d6144e53024c00fd015a69d43cb5d3e812a12df'}
W56_PATHS={str(PROJECT/p)for p in('skills/violation-notifier/scripts/governance_detail.py','skills/violation-notifier/scripts/violation_reboot_continuation.py','skills/violation-notifier/scripts/violation_execution_ports.py','skills/workshop-director/scripts/collection_ready.py')}
W56_ERROR='governance-detail-source-subject-mismatch'

def w56_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==4 and {t['target']for t in release['targets']}==W56_PATHS,'W56-exact-reviewed-four-sources');base=doc(W56_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W56-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==4,'W56-no-added-slot');return archives,codes

def w56_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W56_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W56_BASE and len(parent['calls'])==10 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W56-original-parent10');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W56_ERROR and len(engine['calls'])==57 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:56]),'W56-original-engine57');failed=engine['calls'][56];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W56_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W56-only-failed-read-detail');call=parent['calls'][9];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W56_ERROR}and launch['index']==9 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W56_BASE,'W56-natural-child9-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-13'and summary['worker_live']is False,'W56-natural-worker13')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W56-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W56-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==0 and len(state['calls'])==1 and state['calls'][0]['state']=='confirmed'and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='202610274830958481'and state['details']==[]and not state.get('hold')and not state.get('last_error'),'W56-original-open-confirmed-readonly-frontier');raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][0]==summary['row'],'W56-original-query-row');return call

def w56_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w56_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':56,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w56_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W56_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-13'and value['previous_admission']==W56_BASE and value['failure']==W56_FAILURE,'W56-fixed-original-task13');archives,codes=w56_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W56-derived-exact-source-view');base=w55_verify(W56_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W56_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W56-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w56_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w56_parent_after(parent,reference)and doc(receipt['engine_after'])==w56_engine_after(engine,reference),'W56-completed-two-CAS-required');return {**base,'kind':W56_KIND,'attempt_id':TASK8+'-13','previous_admission':W56_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':9,'call':call,'returncode':2},'child_admissions':{'7':base['previous_previous_admission'],'8':base['previous_admission'],'9':W56_BASE},'successor':reference,'engine_prefix':w56_engine_after(engine,reference)['calls']}

_W56_PREVIOUS_VERIFY=verify
_W56_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W56_KIND:return w56_verify(reference,live_boot=live_boot)
 return _W56_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W56_KIND:return _W56_PREVIOUS_ALLOWED(engine,admission)
 value=w56_verify(admission);need(engine['calls'][:56]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W56-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w56_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W56-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',13)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W56-original-failed13-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W56-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-13')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W56-worker-dead');summary=doc(W56_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w56_failure(parent,engine);archives,codes=w56_sources(release_ref);w55_verify(W56_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'detail-subject-object-successors'/digest({'release':release_ref,'failure':W56_FAILURE});need(not(out/'intent.json').exists(),'W56-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W56_KIND,'task_id':TASK8,'attempt_id':TASK8+'-13','previous_admission':W56_BASE,'failure':W56_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w56_parent_after(parent,reference);ne=w56_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W56-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w56_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task14 read-detail parser failure; no UI input or child rewind.
W57_KIND='verified-violation-stop-auto-template-source-successor-v1'
W57_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/detail-subject-object-successors/7bc51061d20c1c8a2aec452cd9e0cfc27d5b5d2bc275eacf26412b56bf60ded4/admission.json'),'sha256':'573fb6b94b9185e0ab58e82d395d00dc41afba6b57abc3b6abe381ca993b6a4a'}
W57_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue56-original-recovery/VI14-summary.json'),'sha256':'b4cc44b6499dd565dbc22637ce59e8207a6494c92852478e9e775823477d9835'}
W57_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_rates_stop_loss.py','governance_stop_loss_integration.py','governance_stop_loss_production.py','governance_detail.py','governance_capture.py','governance_rates_direct_recovery.py','governance_rates_direct_replay.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py')}
W57_ERROR='stop-auto-known-template-not-unique'

def w57_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==10 and {t['target']for t in release['targets']}==W57_PATHS,'W57-exact-reviewed-ten-sources');base=doc(W57_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W57-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==10,'W57-no-added-slot');return archives,codes

def w57_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W57_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W57_BASE and len(parent['calls'])==11 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W57-original-parent11');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W57_ERROR and len(engine['calls'])==61 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:60]),'W57-original-engine61');failed=engine['calls'][60];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W57_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W57-only-failed-read-detail');call=parent['calls'][10];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W57_ERROR}and launch['index']==10 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W57_BASE,'W57-natural-child10-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-14'and summary['worker_live']is False,'W57-natural-worker14')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W57-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W57-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==1 and len(state['calls'])==3 and all(c['state']=='confirmed'for c in state['calls'])and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='ZS202610274829552431'and len(state['details'])==1 and state['details'][0]['state']=='complete'and not state.get('hold')and not state.get('last_error'),'W57-original-open-confirmed-readonly-frontier');raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][1]==summary['row'],'W57-original-query-row');return call

def w57_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w57_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':60,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w57_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W57_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-14'and value['previous_admission']==W57_BASE and value['failure']==W57_FAILURE,'W57-fixed-original-task14');archives,codes=w57_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W57-derived-exact-source-view');base=w56_verify(W57_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W57_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W57-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w57_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w57_parent_after(parent,reference)and doc(receipt['engine_after'])==w57_engine_after(engine,reference),'W57-completed-two-CAS-required');return {**base,'kind':W57_KIND,'attempt_id':TASK8+'-14','previous_admission':W57_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':10,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'10':W57_BASE},'successor':reference,'engine_prefix':w57_engine_after(engine,reference)['calls']}

_W57_PREVIOUS_VERIFY=verify
_W57_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W57_KIND:return w57_verify(reference,live_boot=live_boot)
 return _W57_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W57_KIND:return _W57_PREVIOUS_ALLOWED(engine,admission)
 value=w57_verify(admission);need(engine['calls'][:60]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W57-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w57_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W57-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',14)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W57-original-failed14-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W57-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-14')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W57-worker-dead');summary=doc(W57_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w57_failure(parent,engine);archives,codes=w57_sources(release_ref);w56_verify(W57_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'stop-auto-template-successors'/digest({'release':release_ref,'failure':W57_FAILURE});need(not(out/'intent.json').exists(),'W57-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W57_KIND,'task_id':TASK8,'attempt_id':TASK8+'-14','previous_admission':W57_BASE,'failure':W57_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w57_parent_after(parent,reference);ne=w57_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W57-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w57_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task15 read-detail parser failure; no UI input or child rewind.
W58_KIND='verified-violation-anchor-advice-frame-source-successor-v1'
W58_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/stop-auto-template-successors/7f065ee48cd0341db7d8c26d8b171f75c75fdedf237c622c781f47e66aae34d4/admission.json'),'sha256':'f59a5cb5d13a84d5d54009a301d841b25dbca7e2108e49d9cbc766fb37e96714'}
W58_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue57-original-recovery/VI15-summary.json'),'sha256':'aa9c26ed9ee32ca972ba3c97655ed39a7aa99469a44b5b821d2baa9ae9f86033'}
W58_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_detail.py','governance_capture.py','center_reconciliation.py','workflow.py','public_copy_template.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py')}
W58_ERROR='governance-frame-title-changed'

def w58_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==8 and {t['target']for t in release['targets']}==W58_PATHS,'W58-exact-reviewed-eight-sources');base=doc(W58_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W58-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==8,'W58-no-added-slot');return archives,codes

def w58_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W58_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W58_BASE and len(parent['calls'])==12 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W58-original-parent12');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W58_ERROR and len(engine['calls'])==67 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:66]),'W58-original-engine67');failed=engine['calls'][66];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W58_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W58-only-failed-read-detail');call=parent['calls'][11];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W58_ERROR}and launch['index']==11 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W58_BASE,'W58-natural-child11-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-15'and summary['worker_live']is False,'W58-natural-worker15')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W58-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W58-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==2 and len(state['calls'])==5 and all(c['state']=='confirmed'for c in state['calls'])and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='202610264826012780'and len(state['details'])==2 and all(x['state']=='complete'for x in state['details'])and not state.get('hold')and not state.get('last_error'),'W58-original-open-confirmed-readonly-frontier');raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][2]==summary['row'],'W58-original-query-row');return call

def w58_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w58_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':66,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w58_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W58_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-15'and value['previous_admission']==W58_BASE and value['failure']==W58_FAILURE,'W58-fixed-original-task15');archives,codes=w58_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W58-derived-exact-source-view');base=w57_verify(W58_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W58_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W58-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w58_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w58_parent_after(parent,reference)and doc(receipt['engine_after'])==w58_engine_after(engine,reference),'W58-completed-two-CAS-required');return {**base,'kind':W58_KIND,'attempt_id':TASK8+'-15','previous_admission':W58_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':11,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'11':W58_BASE},'successor':reference,'engine_prefix':w58_engine_after(engine,reference)['calls']}

_W58_PREVIOUS_VERIFY=verify
_W58_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W58_KIND:return w58_verify(reference,live_boot=live_boot)
 return _W58_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W58_KIND:return _W58_PREVIOUS_ALLOWED(engine,admission)
 value=w58_verify(admission);need(engine['calls'][:66]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W58-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w58_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W58-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',15)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W58-original-failed15-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W58-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-15')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W58-worker-dead');summary=doc(W58_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w58_failure(parent,engine);archives,codes=w58_sources(release_ref);w57_verify(W58_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'anchor-advice-frame-successors'/digest({'release':release_ref,'failure':W58_FAILURE});need(not(out/'intent.json').exists(),'W58-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W58_KIND,'task_id':TASK8,'attempt_id':TASK8+'-15','previous_admission':W58_BASE,'failure':W58_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w58_parent_after(parent,reference);ne=w58_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W58-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w58_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task16 read-detail parser failure; no UI input or child rewind.
W59_KIND='verified-violation-anchor-frame-guard-route-source-successor-v1'
W59_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/anchor-advice-frame-successors/85134aae6ea0d809fd9b386a4a77367da470d166eb9efdced4c89c8a393c510b/admission.json'),'sha256':'121ff7c29d3f55db5205cfe5aa09ba4bae1f7957e896eed2475ad8963cd41298'}
W59_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue58-original-recovery/VI16-summary.json'),'sha256':'f3070caa6b31770c66491917f39179738786bf600867124485cd19783b6a81aa'}
W59_GUARD={'path':str(PROJECT/'work/performance-audit/governance-anchor-close-guard-candidate/saved-guard-proof.json'),'sha256':'b20a3ccccda8327aedda0ff6e6a1f1e8586a134a3934eb0fd5678ca4bb3414a3'}
W59_ROUTE={'path':str(PROJECT/'work/2026-10-29/round009-issue59-original-recovery/route-once/complete.json'),'sha256':'847b0277b9b3fc070b6cb5c30f5cac4793f91d8b0c782f02e2819f39729a8442'}
W59_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_detail.py','governance_capture.py','governance_stop_loss_integration.py','governance_rates_direct_recovery.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py')}
W59_ERROR='governance-bridge-request-failed:governance frame drawer structure unreviewed'

def w59_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==7 and {t['target']for t in release['targets']}==W59_PATHS,'W59-exact-reviewed-seven-sources');base=doc(W59_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W59-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==7,'W59-no-added-slot');return archives,codes

def w59_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W59_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W59_BASE and len(parent['calls'])==13 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W59-original-parent13');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W59_ERROR and len(engine['calls'])==68 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:67]),'W59-original-engine68');failed=engine['calls'][67];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W59_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W59-only-failed-read-detail');call=parent['calls'][12];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W59_ERROR}and launch['index']==12 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W59_BASE,'W59-natural-child12-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-16'and summary['worker_live']is False,'W59-natural-worker16')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W59-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W59-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='verify-closed-unknown'and state['cursor']==2 and len(state['calls'])==6 and all(c['state']=='confirmed'for c in state['calls'][:5])and state['calls'][5]['state']=='unknown'and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='202610264826012780'and len(state['details'])==2 and all(x['state']=='complete'for x in state['details'])and not state.get('hold')and not state.get('last_error'),'W59-original-open-confirmed-readonly-frontier');import governance_detail as detail
 proof=detail.verify_anchor_guard_proof(W59_GUARD);route=detail.verify_anchor_route_completion(W59_ROUTE,W59_GUARD);need(state==proof['original']and route['normal_after']==doc(W59_ROUTE)['normal_after'],'W59-actual-guard-and-route-completed');raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][2]==summary['row'],'W59-original-query-row');return call

def w59_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-delivered-anchor-close-guard-route-restored-not-close-success'});return after

def w59_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':67,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w59_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W59_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-16'and value['previous_admission']==W59_BASE and value['failure']==W59_FAILURE,'W59-fixed-original-task16');archives,codes=w59_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W59-derived-exact-source-view');base=w58_verify(W59_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W59_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W59-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w59_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w59_parent_after(parent,reference)and doc(receipt['engine_after'])==w59_engine_after(engine,reference)and doc(receipt['detail_after'])==w59_detail_after(doc(value['detail_archive'])),'W59-completed-two-CAS-required');return {**base,'kind':W59_KIND,'attempt_id':TASK8+'-16','previous_admission':W59_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':12,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'12':W59_BASE},'successor':reference,'engine_prefix':w59_engine_after(engine,reference)['calls']}

def w59_detail_after(before):
 after=copy.deepcopy(before);after['anchor_guard_route_recovery']={'kind':'verified-anchor-frame-guard-route-completion-v1','guard_proof':W59_GUARD,'route_complete':W59_ROUTE};return after

_W59_PREVIOUS_VERIFY=verify
_W59_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W59_KIND:return w59_verify(reference,live_boot=live_boot)
 return _W59_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W59_KIND:return _W59_PREVIOUS_ALLOWED(engine,admission)
 value=w59_verify(admission);need(engine['calls'][:67]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W59-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w59_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',Path(doc(W59_FAILURE)['detail_state']['path']).parent/'.lock'):
   need(o.canonical(path)==path and path.is_file(),'W59-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',16)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W59-original-failed16-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W59-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-16')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W59-worker-dead');summary=doc(W59_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w59_failure(parent,engine);archives,codes=w59_sources(release_ref);w58_verify(W59_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'anchor-guard-route-successors'/digest({'release':release_ref,'failure':W59_FAILURE});need(not(out/'intent.json').exists(),'W59-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W59_KIND,'task_id':TASK8,'attempt_id':TASK8+'-16','previous_admission':W59_BASE,'failure':W59_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w59_parent_after(parent,reference);ne=w59_engine_after(engine,reference);nd=w59_detail_after(doc(summary['detail_state']));after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne),('detail',nd))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er,'detail':summary['detail_state']},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er and o.ref(Path(summary['detail_state']['path']))==summary['detail_state'],'W59-before-CAS-raced');atomic(Path(summary['detail_state']['path']),nd);atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'detail_after':after['detail'],'business_inputs':0});w59_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task17 read-detail parser failure; no UI input or child rewind.
W60_KIND='verified-violation-noaccept-rate-template-source-successor-v1'
W60_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/anchor-guard-route-successors/2b8979b1855ac8b895a54de209169c7af87cd54f36654c251dafc493672784ac/admission.json'),'sha256':'8b74c3f7a2c6e76f9b2726d06a8bddbf0100a4360a925514a5cbf80e44b43b7e'}
W60_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue59-original-recovery/VI17-summary.json'),'sha256':'121a589d187dadf66eae0ca90b50bad2f9025ec3b254e22c2da9fc3fa0a4d4a5'}
W60_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_rates_stop_loss.py','governance_stop_loss_production.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py')}
W60_ERROR='stop-auto-known-template-not-unique'

def w60_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W60_PATHS,'W60-exact-reviewed-five-sources');base=doc(W60_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  original=by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W60-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==5,'W60-no-added-slot');return archives,codes

def w60_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W60_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W60_BASE and len(parent['calls'])==14 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W60-original-parent14');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W60_ERROR and len(engine['calls'])==70 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:69]),'W60-original-engine70');failed=engine['calls'][69];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W60_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W60-only-failed-read-detail');call=parent['calls'][13];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W60_ERROR}and launch['index']==13 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W60_BASE,'W60-natural-child13-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-17'and summary['worker_live']is False,'W60-natural-worker17')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W60-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W60-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==3 and len(state['calls'])==7 and all(c['state']=='confirmed'for i,c in enumerate(state['calls'])if i!=5)and state['calls'][5]['state']=='unknown'and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='ZS202610264820919650'and len(state['details'])==3 and all(x['state']=='complete'for x in state['details'])and not state.get('hold')and not state.get('last_error'),'W60-original-open-confirmed-readonly-frontier');import governance_detail as detail
 inputs=detail.inputs(state['manifest']);need(state['anchor_guard_route_recovery']==doc(W60_FAILURE)['detail_state_value']['anchor_guard_route_recovery']and detail.unresolved_detail_calls(state)==[],'W60-only-known-retired-UNKNOWN');detail.verify_anchor_route_entry(state['details'][2],state,state['manifest'],inputs,inputs['query']['rows'][2]);raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][3]==summary['row'],'W60-original-query-row');return call

def w60_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w60_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':69,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w60_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W60_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-17'and value['previous_admission']==W60_BASE and value['failure']==W60_FAILURE,'W60-fixed-original-task17');archives,codes=w60_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W60-derived-exact-source-view');base=w59_verify(W60_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W60_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W60-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w60_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w60_parent_after(parent,reference)and doc(receipt['engine_after'])==w60_engine_after(engine,reference),'W60-completed-two-CAS-required');return {**base,'kind':W60_KIND,'attempt_id':TASK8+'-17','previous_admission':W60_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':13,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'13':W60_BASE},'successor':reference,'engine_prefix':w60_engine_after(engine,reference)['calls']}

_W60_PREVIOUS_VERIFY=verify
_W60_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W60_KIND:return w60_verify(reference,live_boot=live_boot)
 return _W60_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W60_KIND:return _W60_PREVIOUS_ALLOWED(engine,admission)
 value=w60_verify(admission);need(engine['calls'][:69]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W60-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w60_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W60-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',17)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W60-original-failed17-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W60-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-17')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W60-worker-dead');summary=doc(W60_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w60_failure(parent,engine);archives,codes=w60_sources(release_ref);w59_verify(W60_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'noaccept-rate-template-successors'/digest({'release':release_ref,'failure':W60_FAILURE});need(not(out/'intent.json').exists(),'W60-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W60_KIND,'task_id':TASK8,'attempt_id':TASK8+'-17','previous_admission':W60_BASE,'failure':W60_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w60_parent_after(parent,reference);ne=w60_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W60-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w60_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task18 read-detail parser failure; no UI input or child rewind.
W61_KIND='verified-violation-noaccept-warning-template-source-successor-v1'
W61_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/noaccept-rate-template-successors/fb7513409b08c774c3eea6c462c093de88720f20b61d5bee9113a8308682d7e2/admission.json'),'sha256':'01604018ad172c227cf845da6fbe6a5c3066cbb2df76bca2a103bc5441779a07'}
W61_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue60-original-recovery/VI18-summary.json'),'sha256':'7ba5172493b0787d72e551e3b3b8df13ff760b7add01def092a0d51c5255b321'}
W61_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'1958287e14dcbe1927c56e79e458be034679b275e9ac320df9f8bb6fc2e1b3e7'}
W61_CF_AFTER='44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c'
W61_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_rates_stop_loss.py','governance_stop_loss_production.py','governance_detail.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts'/n)for n in('collection_ready.py','delivery_commit.py','unified_review_format.py')}|{W61_CF['path']}
W61_ERROR='stop-auto-known-template-not-unique'

def w61_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==9 and {t['target']for t in release['targets']}==W61_PATHS,'W61-exact-reviewed-nine-sources');base=doc(W61_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W61_CF['path'];original=W61_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W61_CF_AFTER,'W61-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W61-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==9,'W61-no-added-slot');return archives,codes

def w61_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W61_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W61_BASE and len(parent['calls'])==15 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W61-original-parent15');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W61_ERROR and len(engine['calls'])==76 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:75]),'W61-original-engine76');failed=engine['calls'][75];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W61_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W61-only-failed-read-detail');call=parent['calls'][14];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W61_ERROR}and launch['index']==14 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W61_BASE,'W61-natural-child14-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-18'and summary['worker_live']is False,'W61-natural-worker18')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W61-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W61-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==4 and len(state['calls'])==9 and all(c['state']=='confirmed'for i,c in enumerate(state['calls'])if i!=5)and state['calls'][5]['state']=='unknown'and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='ZS202610264820919207'and len(state['details'])==4 and all(x['state']=='complete'for x in state['details'])and not state.get('hold')and not state.get('last_error'),'W61-original-open-confirmed-readonly-frontier');import governance_detail as detail
 inputs=detail.inputs(state['manifest']);need(state['anchor_guard_route_recovery']==doc(W61_FAILURE)['detail_state_value']['anchor_guard_route_recovery']and detail.unresolved_detail_calls(state)==[],'W61-only-known-retired-UNKNOWN');detail.verify_anchor_route_entry(state['details'][2],state,state['manifest'],inputs,inputs['query']['rows'][2]);raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][4]==summary['row'],'W61-original-query-row');return call

def w61_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w61_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':75,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w61_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W61_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-18'and value['previous_admission']==W61_BASE and value['failure']==W61_FAILURE,'W61-fixed-original-task18');archives,codes=w61_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W61-derived-exact-source-view');base=w60_verify(W61_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W61_FAILURE);need(value['parent_before']['sha256']==summary['parent']['reference']['sha256']and value['engine_before']['sha256']==summary['engine']['reference']['sha256'],'W61-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w61_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w61_parent_after(parent,reference)and doc(receipt['engine_after'])==w61_engine_after(engine,reference),'W61-completed-two-CAS-required');return {**base,'kind':W61_KIND,'attempt_id':TASK8+'-18','previous_admission':W61_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':14,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'14':W61_BASE},'successor':reference,'engine_prefix':w61_engine_after(engine,reference)['calls']}

_W61_PREVIOUS_VERIFY=verify
_W61_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W61_KIND:return w61_verify(reference,live_boot=live_boot)
 return _W61_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W61_KIND:return _W61_PREVIOUS_ALLOWED(engine,admission)
 value=w61_verify(admission);need(engine['calls'][:75]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W61-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w61_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W61-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',18)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W61-original-failed18-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W61-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-18')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W61-worker-dead');summary=doc(W61_FAILURE);pr=summary['parent']['reference'];er=summary['engine']['reference'];parent=doc(pr);engine=doc(er);w61_failure(parent,engine);archives,codes=w61_sources(release_ref);w60_verify(W61_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'noaccept-warning-template-successors'/digest({'release':release_ref,'failure':W61_FAILURE});need(not(out/'intent.json').exists(),'W61-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W61_KIND,'task_id':TASK8,'attempt_id':TASK8+'-18','previous_admission':W61_BASE,'failure':W61_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w61_parent_after(parent,reference);ne=w61_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W61-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w61_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact original task19 read-detail parser failure; no UI input or child rewind.
W62_KIND='verified-violation-sixth-rate-template-source-successor-v1'
W62_BASE={'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/noaccept-warning-template-successors/0be985e7f30730385bca26054a1a545a70bec18a898834af07162263451ce9a3/admission.json', 'sha256': '2b6856a9afeaef7f26bbdb0477f1d727fc4f9f56c69d03c78ba73ba57d352354'}
W62_FAILURE={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-29/round009-issue61-original-recovery/VI19-summary.json', 'sha256': '28a20887c19cdeb66f8b49b1644672316a1629515346a5312a10cefc3a396d9a'}
W62_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'44f9c8b8be8fa79af31d62dfb8d285253269675c52ce8a74aceeeba7ded5585c'}
W62_CF_AFTER='21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10'
W62_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('governance_rates_stop_loss.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py')}|{W62_CF['path']}
W62_ERROR='stop-auto-known-template-not-unique'

def w62_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W62_PATHS,'W62-exact-reviewed-five-sources');base=doc(W62_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W62_CF['path'];original=W62_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W62_CF_AFTER,'W62-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W62-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==5,'W62-no-added-slot');return archives,codes

def w62_failure(parent,engine,*,detail_archive=None,query_archive=None):
 summary=doc(W62_FAILURE);need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W62_BASE and len(parent['calls'])==16 and parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent.get('child')is None,'W62-original-parent16');need(engine['status']=='hold'and engine['phase']=='details'and engine['index']==1 and engine['error']==W62_ERROR and len(engine['calls'])==82 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:81]),'W62-original-engine82');failed=engine['calls'][81];need(failed['state']=='failed'and failed['step']=='details'and failed['company_index']==1 and failed['error']==W62_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W62-only-failed-read-detail');call=parent['calls'][15];launch=doc(call['launch']);ex=doc(call['result']);need(call['state']=='returned'and ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W62_ERROR}and launch['index']==15 and launch['order']==parent['order']and ex['launch']==call['launch']and ex['argv']==launch['argv']==call['argv']and ex['reboot_continuation']==launch['reboot_continuation']==W62_BASE,'W62-natural-child15-rc2');need(summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-19'and summary['worker_live']is False,'W62-natural-worker19')
 need(detail_archive is None or detail_archive['sha256']==summary['detail_state']['sha256'],'W62-detail-archive-hash');need(query_archive is None or query_archive['sha256']==summary['records_query']['sha256'],'W62-query-archive-hash');state=doc(detail_archive or summary['detail_state']);need(state==summary['detail_state_value']and state['phase']=='read-detail'and state['cursor']==5 and len(state['calls'])==11 and all(c['state']=='confirmed'for i,c in enumerate(state['calls'])if i!=5)and state['calls'][5]['state']=='unknown'and state['calls'][0]['command']['op']=='click'and state['current']['notice_id']=='ZS202610264820918624'and len(state['details'])==5 and all(x['state']=='complete'for x in state['details'])and not state.get('hold')and not state.get('last_error'),'W62-original-open-confirmed-readonly-frontier');import governance_detail as detail
 inputs=detail.inputs(state['manifest']);need(state['anchor_guard_route_recovery']==doc(W62_FAILURE)['detail_state_value']['anchor_guard_route_recovery']and detail.unresolved_detail_calls(state)==[],'W62-only-known-retired-UNKNOWN');detail.verify_anchor_route_entry(state['details'][2],state,state['manifest'],inputs,inputs['query']['rows'][2]);raw(state['last_observation']);need(doc(query_archive or summary['records_query'])['rows'][5]['notice_id']==state['current']['notice_id'],'W62-original-query-row');return call

def w62_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-detail-parser-failure-not-success'});return after

def w62_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':81,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w62_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W62_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-19'and value['previous_admission']==W62_BASE and value['failure']==W62_FAILURE,'W62-fixed-original-task19');archives,codes=w62_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W62-derived-exact-source-view');base=w61_verify(W62_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W62_FAILURE);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W62-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);call=w62_failure(parent,engine,detail_archive=value['detail_archive'],query_archive=value['query_archive']);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w62_parent_after(parent,reference)and doc(receipt['engine_after'])==w62_engine_after(engine,reference),'W62-completed-two-CAS-required');return {**base,'kind':W62_KIND,'attempt_id':TASK8+'-19','previous_admission':W62_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':parent['calls'],'readonly_failed_child':{'index':15,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'15':W62_BASE},'successor':reference,'engine_prefix':w62_engine_after(engine,reference)['calls']}

_W62_PREVIOUS_VERIFY=verify
_W62_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W62_KIND:return w62_verify(reference,live_boot=live_boot)
 return _W62_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W62_KIND:return _W62_PREVIOUS_ALLOWED(engine,admission)
 value=w62_verify(admission);need(engine['calls'][:81]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W62-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w62_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file(),'W62-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',19)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W62-original-failed19-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W62-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-19')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W62-worker-dead');summary=doc(W62_FAILURE);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w62_failure(parent,engine);archives,codes=w62_sources(release_ref);w61_verify(W62_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'sixth-rate-template-successors'/digest({'release':release_ref,'failure':W62_FAILURE});need(not(out/'intent.json').exists(),'W62-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W62_KIND,'task_id':TASK8,'attempt_id':TASK8+'-19','previous_admission':W62_BASE,'failure':W62_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'detail_archive':raw_archive(summary['detail_state'],out/'detail-before.json'),'query_archive':raw_archive(summary['records_query'],out/'query-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w62_parent_after(parent,reference);ne=w62_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W62-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w62_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()
# Work-only exact failure/delta draft. No sources/apply/dispatch authority.
W63_FAILURE={'path':str(PROJECT/'work/2026-10-29/round009-issue62-original-recovery/VI22-summary.json'),'sha256':'a366dd6158dfdb5bcccdda03cc93f05c203a3c2d520ed7caeec36c6bb3dd034a'}
W63_ORIGINALS={'path':str(PROJECT/'work/performance-audit/task8-native-region-readonly-recovery-candidate/ORIGINALS.json'),'sha256':'7e3d98f7cd6f3551b04b6eb826d1a9ff43341d0bb869997316162d5bc0a90014'}
W63_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/sixth-rate-template-successors/4ff31413a458500f69ebd2b7fdd2c01f82f70d4de0af78faba3fbbbc481d63e0/admission.json'),'sha256':'53caaf8e1abf9ec5f82ee92203402ef7594de0394414905100d3139ac0a2ebe0'}
W63_ERROR='region-WebArea-URL-not-unique'
W63_BOUNDARY={'path':str(PROJECT/'work/performance-audit/task8-native-region-readonly-recovery-candidate/CAPTURE-BOUNDARY.json'),'sha256':'b22ce3201bb1ad5680fc4d48f479d2ba8d35a201642885e7df31388d3c3b55af'}
def w63_failure(parent,engine,*,live_frontier=False):
 original=doc(W63_ORIGINALS);summary=doc(W63_FAILURE);need(original['failure']==W63_FAILURE and parent==doc(original['parent_archive']) and engine==doc(original['engine_archive']),'W63-exact-original-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W63_BASE and len(parent['calls'])==19 and parent['status']=='hold' and parent['error']=='execution-child-stopped' and parent.get('child')==doc(original['parent_archive']).get('child'),'W63-exact-parent19')
 need(engine['status']=='hold' and engine['phase']=='frames' and engine['index']==1 and engine['error']==W63_ERROR and len(engine['calls'])==97 and all(c['state']=='returned' and c.get('applied')is True for c in engine['calls'][:96]),'W63-exact-engine97')
 failed=engine['calls'][96];need(failed['state']=='failed' and failed['step']=='frames' and failed['company_index']==1 and failed['error']==W63_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W63-only-failed-capture-read')
 codes=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);codes.append(ex['returncode']);need(c['state']=='returned' and ex['launch']==c['launch'] and ex['argv']==launch['argv']==c['argv'] and launch['index']==i and launch['order']==parent['order'],'W63-original-natural-receipt')
 need(codes==[2]*16+[0,0,2] and parent['calls'][16]['argv'][2]=='run' and parent['calls'][17]['argv'][2]=='accept' and parent['calls'][18]['argv'][2]=='run','W63-failed-subset17-normal16-17-preserved')
 for i in (16,17,18):
  ex=doc(parent['calls'][i]['result']);launch=doc(parent['calls'][i]['launch']);need(ex['reboot_continuation']==launch['reboot_continuation']==W63_BASE,'W63-three-natural-W62-child-lineages')
 ex=doc(parent['calls'][18]['result']);need(ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':W63_ERROR},'W63-natural-child18-error')
 need(summary['worker']['attempt_id']==TASK8+'-22' and summary['worker']['returncode']==0 and summary['worker_live']is False,'W63-natural-worker22')
 state=doc(summary['detail_archive']);need(state==summary['detail_state_value'] and state['phase']=='complete' and state['cursor']==6 and len(state['details'])==6 and len(state['calls'])==12 and state['calls'][5]['state']=='unknown' and all(c['state']=='confirmed' for i,c in enumerate(state['calls'])if i!=5),'W63-six-complete-preserved')
 import governance_detail as detail
 need(detail.unresolved_detail_calls(state)==[],'W63-only-verified-retired-unknown')
 need(engine['companies'][1]['artifacts']['frame_state']==summary['frame_state'] and summary['frame_state']['phase']=='capture' and engine['companies'][1]['artifacts']['frame_index']==0 and not engine['companies'][1]['artifacts'].get('frames'),'W63-original-first-frame-frontier')
 boundary=doc(W63_BOUNDARY);need(boundary['capture_focus_already_executed']is True and boundary['native_state_present']is False and boundary['native_state_folder_json_files']==[],'W63-original-preintent-capture-boundary');raw(boundary['region_producer_archive']);accepted=engine['accepted'][-1];need(accepted==boundary['accepted_record'] and accepted['state']=='complete','W63-exact-original-copy-acceptance');response=doc(accepted['response']);request=doc(accepted['request']);need(response==boundary['response'] and response['request']==accepted['request'] and response['kind']=='violation-copy-response-v1' and response['copy']==boundary['copy'] and request['source']==boundary['source']==engine['companies'][1]['artifacts']['source'] and doc(response['copy'])['source_sha256']==boundary['source']['sha256'],'W63-exact-copy-response-source');raw(boundary['source']);raw(boundary['profile'])
 native=Path(boundary['native_state_path']);source_path=Path(boundary['source']['path']);chain='violation-cdac95ef65466760d4bc91e9-1';name=hashlib.sha256(json.dumps([boundary['source']['sha256'],chain],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()+'.json';need(native==source_path.parent/'.native-region-frame-state'/name and Path(boundary['capture_output'])==source_path.parent/'frames/0000-anchor','W63-exact-native-state-path')
 if live_frontier:need(not native.exists() and not list(native.parent.glob('*.json')) and all(not Path(p).exists() for p in boundary['must_absent_outputs']),'W63-native-intent-or-output-now-present-HOLD')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for i,c in enumerate(parent['calls'])if codes[i]==2],'failed_child':parent['calls'][18]}
def w63_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-region-geometry-failure-not-success'});return after
def w63_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':96,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

W63_KIND='verified-violation-native-region-application-role-source-successor-v1'
W63_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'21a9e4287f6226f88210be08293f89b4fe6766c2f33bbe45c2556b1fd1f01b10'}
W63_CF_AFTER='f26701406ed6d8fa07276de4b77a00c9610a77cf6549a266e781bdf2e635133d'
W63_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/chrome-dom-export/scripts/native_region_capture.py'),str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W63_CF['path']}
def w63_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W63_PATHS,'W63-exact-reviewed-five-sources');base=doc(W63_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W63_CF['path'];original=W63_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W63_CF_AFTER,'W63-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W63-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==5,'W63-no-added-slot');return archives,codes

def w63_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W63_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-22'and value['previous_admission']==W63_BASE and value['failure']==W63_FAILURE,'W63-fixed-original-task19');archives,codes=w63_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W63-derived-exact-source-view');base=w62_verify(W63_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W63_FAILURE);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W63-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w63_failure(parent,engine);call=facts['failed_child'];receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w63_parent_after(parent,reference)and doc(receipt['engine_after'])==w63_engine_after(engine,reference),'W63-completed-two-CAS-required');return {**base,'kind':W63_KIND,'attempt_id':TASK8+'-22','previous_admission':W63_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':18,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'16':W63_BASE,'17':W63_BASE,'18':W63_BASE},'successor':reference,'engine_prefix':w63_engine_after(engine,reference)['calls']}

_W63_PREVIOUS_VERIFY=verify
_W63_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W63_KIND:return w63_verify(reference,live_boot=live_boot)
 return _W63_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W63_KIND:return _W63_PREVIOUS_ALLOWED(engine,admission)
 value=w63_verify(admission);need(engine['calls'][:96]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W63-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w63_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',Path(doc(W63_BOUNDARY)['native_state_path']).with_suffix('.lock')):
   need(o.canonical(path)==path and path.is_file(),'W63-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',22)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W63-original-failed22-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W63-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-22')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W63-worker-dead');summary=doc(W63_FAILURE);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w63_failure(parent,engine,live_frontier=True);archives,codes=w63_sources(release_ref);w62_verify(W63_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'native-region-application-role-successors'/digest({'release':release_ref,'failure':W63_FAILURE});need(not(out/'intent.json').exists(),'W63-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W63_KIND,'task_id':TASK8,'attempt_id':TASK8+'-22','previous_admission':W63_BASE,'failure':W63_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w63_parent_after(parent,reference);ne=w63_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W63-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w63_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()
# Work-only exact failure/delta draft. No sources/apply/dispatch authority.
W64_FAILURE={'path':str(PROJECT/'work/2026-10-30/round009-issue63-original-recovery/VI23-summary.json'),'sha256':'1c8a2ddcb8410ecb5fb18d9fd0e6cd04a457f04809ae81d81f56673eb8ae1825'}
W64_ORIGINALS={'path':str(PROJECT/'work/performance-audit/task8-preintent-frame-observation-recovery-candidate/ORIGINALS.json'),'sha256':'86cd0c903b2d34c9a559e95220e54701a8bb7390087b7e2e0f97920baf53cac7'}
W64_BASE={'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/native-region-application-role-successors/aa96e15484cc566e70bdff25e051a6bed5044b82cec8d1214eda52d9a55cf590/admission.json', 'sha256': '0f3a47f6cf6aca5c902eadc2c812cd6f7348d80cc063611a261b3c648888c963'}
W64_ERROR='execution-anchor-contract-proof-failed'
W64_BOUNDARY={'path':str(PROJECT/'work/performance-audit/task8-preintent-frame-observation-recovery-candidate/CAPTURE-BOUNDARY.json'),'sha256':'4bf05a8988350e2a752fb81e97ffcde63e70dab3a7b651898b4c44f3a58c059c'}
def w64_failure(parent,engine,*,live_frontier=False):
 original=doc(W64_ORIGINALS);summary=doc(W64_FAILURE);need(original['failure']==W64_FAILURE and parent==doc(original['parent_archive']) and engine==doc(original['engine_archive']),'W64-exact-original-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W64_BASE and len(parent['calls'])==20 and parent['status']=='hold' and parent['error']=='execution-child-stopped' and parent.get('child')==doc(original['parent_archive']).get('child'),'W64-exact-parent20')
 need(engine['status']=='hold' and engine['phase']=='frames' and engine['index']==1 and engine['error']==W64_ERROR and len(engine['calls'])==97 and all(c['state']=='returned' and c.get('applied')is True for c in engine['calls'][:96]),'W64-exact-engine97')
 failed=engine['calls'][96];need(failed['state']=='failed' and failed['step']=='frames' and failed['company_index']==1 and failed['error']==W64_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W64-only-failed-capture-read')
 codes=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);codes.append(ex['returncode']);need(c['state']=='returned' and ex['launch']==c['launch'] and ex['argv']==launch['argv']==c['argv'] and launch['index']==i and launch['order']==parent['order'],'W64-original-natural-receipt')
 need(codes==[2]*16+[0,0,2,2] and parent['calls'][16]['argv'][2]=='run' and parent['calls'][17]['argv'][2]=='accept' and parent['calls'][18]['argv'][2]=='run','W64-failed-subset18-normal16-17-preserved')
 for i in (19,):
  ex=doc(parent['calls'][i]['result']);launch=doc(parent['calls'][i]['launch']);need(ex['reboot_continuation']==launch['reboot_continuation']==W64_BASE,'W64-new-natural-W63-child-lineage')
 ex=doc(parent['calls'][19]['result']);need(ex['stderr']=='' and json.loads(ex['stdout'])=={'ok':False,'error':W64_ERROR},'W64-natural-child19-error')
 need(summary['worker']['attempt_id']==TASK8+'-23' and summary['worker']['returncode']==0 and summary['worker_live']is False,'W64-natural-worker23')
 state=doc(summary['detail_archive']);need(state==summary['detail_state_value'] and state['phase']=='complete' and state['cursor']==6 and len(state['details'])==6 and len(state['calls'])==12 and state['calls'][5]['state']=='unknown' and all(c['state']=='confirmed' for i,c in enumerate(state['calls'])if i!=5),'W64-six-complete-preserved')
 import governance_detail as detail
 need(detail.unresolved_detail_calls(state)==[],'W64-only-verified-retired-unknown')
 need(engine['companies'][1]['artifacts']['frame_state']==summary['frame_state'] and summary['frame_state']['phase']=='capture' and engine['companies'][1]['artifacts']['frame_index']==0 and not engine['companies'][1]['artifacts'].get('frames'),'W64-original-first-frame-frontier')
 boundary=doc(W64_BOUNDARY);need(boundary['capture_focus_already_executed']is True and boundary['native_state_present']is False and boundary['native_state_folder_json_files']==[],'W64-original-preintent-capture-boundary');raw(boundary['region_producer_archive']);accepted=engine['accepted'][-1];need(accepted==boundary['accepted_record'] and accepted['state']=='complete','W64-exact-original-copy-acceptance');response=doc(accepted['response']);request=doc(accepted['request']);need(response==boundary['response'] and response['request']==accepted['request'] and response['kind']=='violation-copy-response-v1' and response['copy']==boundary['copy'] and request['source']==boundary['source']==engine['companies'][1]['artifacts']['source'] and doc(response['copy'])['source_sha256']==boundary['source']['sha256'],'W64-exact-copy-response-source');raw(boundary['source']);raw(boundary['profile']);raw(boundary['ports_producer_archive']);selection=doc(boundary['failed_selection']);need(selection['reply']==boundary['expected_reply'] and selection['source']==boundary['source']and selection['profile']==boundary['profile']and selection['observation']==summary['frame_state']['observation']and selection['command']['op']=='viewport-proof'and selection['command']['dom_sha256']=='4b642f81e35b4359817c7e0dde46e77fd7b4f161954ff1f4da659f4f1e57480c','W64-original-readonly-projection-failure')
 native=Path(boundary['native_state_path']);source_path=Path(boundary['source']['path']);chain='violation-cdac95ef65466760d4bc91e9-1';name=hashlib.sha256(json.dumps([boundary['source']['sha256'],chain],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()+'.json';need(native==source_path.parent/'.native-region-frame-state'/name and Path(boundary['capture_output'])==source_path.parent/'frames/0000-anchor','W64-exact-native-state-path')
 if live_frontier:need(not native.exists() and not list(native.parent.glob('*.json')) and all(not Path(p).exists() for p in boundary['must_absent_outputs']),'W64-native-intent-or-output-now-present-HOLD')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for i,c in enumerate(parent['calls'])if codes[i]==2],'failed_child':parent['calls'][19]}
def w64_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'known-readonly-preintent-projection-failure-not-success'});return after
def w64_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':96,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

W64_KIND='verified-violation-preintent-projection-refresh-source-successor-v1'
W64_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'f26701406ed6d8fa07276de4b77a00c9610a77cf6549a266e781bdf2e635133d'}
W64_CF_AFTER='89e35dd10a68fcbf1b1ec9544324e7aac55618638ca384ac641588330753d504'
W64_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W64_CF['path']}
def w64_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==4 and {t['target']for t in release['targets']}==W64_PATHS,'W64-exact-reviewed-four-sources');base=doc(W64_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W64_CF['path'];original=W64_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W64_CF_AFTER,'W64-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W64-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']};
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==4,'W64-no-added-slot');return archives,codes

def w64_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W64_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-23'and value['previous_admission']==W64_BASE and value['failure']==W64_FAILURE,'W64-fixed-original-task19');archives,codes=w64_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W64-derived-exact-source-view');base=w63_verify(W64_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W64_FAILURE);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W64-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w64_failure(parent,engine);call=facts['failed_child'];receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w64_parent_after(parent,reference)and doc(receipt['engine_after'])==w64_engine_after(engine,reference),'W64-completed-two-CAS-required');return {**base,'kind':W64_KIND,'attempt_id':TASK8+'-23','previous_admission':W64_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':19,'call':call,'returncode':2},'child_admissions':{**base['child_admissions'],'19':W64_BASE},'successor':reference,'engine_prefix':w64_engine_after(engine,reference)['calls']}

_W64_PREVIOUS_VERIFY=verify
_W64_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W64_KIND:return w64_verify(reference,live_boot=live_boot)
 return _W64_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W64_KIND:return _W64_PREVIOUS_ALLOWED(engine,admission)
 value=w64_verify(admission);need(engine['calls'][:96]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W64-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w64_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock',Path(doc(W64_BOUNDARY)['native_state_path']).with_suffix('.lock')):
   need(o.canonical(path)==path and path.is_file(),'W64-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',23)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W64-original-failed23-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W64-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-23')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W64-worker-dead');summary=doc(W64_FAILURE);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w64_failure(parent,engine,live_frontier=True);archives,codes=w64_sources(release_ref);w63_verify(W64_BASE,live_boot=clock.boot(),_source_archives=archives)
  out=folder/'preintent-frame-observation-successors'/digest({'release':release_ref,'failure':W64_FAILURE});need(not(out/'intent.json').exists(),'W64-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W64_KIND,'task_id':TASK8,'attempt_id':TASK8+'-23','previous_admission':W64_BASE,'failure':W64_FAILURE,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w64_parent_after(parent,reference);ne=w64_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W64-before-CAS-raced');atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0});w64_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Exact failed24 original postcapture frontier; no metadata or image writes.
W65_FAILURE={'path':str(PROJECT/'work/2026-10-30/round009-issue64-original-recovery/VI24-summary.json'),'sha256':'6b83545c182a80c63be635397f43d0055e76c7e5f23e3a2cf7e1a05a9565e83d'}
W65_ORIGINALS={'path':str(PROJECT/'work/performance-audit/task8-existing-region-registration-recovery-candidate/ORIGINALS.json'),'sha256':'6d379542f6a96b88701cdcf63a22c517d1d2bffff1d87c2a1a464f5302d7d0ce'}
W65_FRONTIER={'path':str(PROJECT/'work/2026-10-30/round009-issue64-original-recovery/VI24-capture-frontier.json'),'sha256':'29251056e3095ad01db0587df5944a15e49954aff2b4bc517de04f048051f064'}
W65_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/preintent-frame-observation-successors/6f68d6d506afe36c639883e8d18017deafbec866d4bd880e0792befeb42df453/admission.json'),'sha256':'9a08bb120a7a5e23e9019ecdb1885281fdbf0914d18f9d8af65665bbde0d75a0'}
W65_ERROR='candidate-default-function-not-fixed:violation_initial_ledger_recovery:<lambda>'
def w65_failure(parent,engine):
 original=doc(W65_ORIGINALS);summary=doc(W65_FAILURE);need(original['failure']==W65_FAILURE and parent==doc(original['parent_archive'])and engine==doc(original['engine_archive']),'W65-exact-original-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W65_BASE and parent['status']=='hold'and parent['error']=='execution-child-stopped'and len(parent['calls'])==21,'W65-original-parent21')
 need(engine['status']=='hold'and engine['phase']=='frames'and engine['index']==1 and engine['error']==W65_ERROR and len(engine['calls'])==98 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:97]),'W65-original-engine98')
 failed=engine['calls'][97];need(failed['step']=='frames'and failed['state']=='failed'and failed['company_index']==1 and failed['error']==W65_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W65-postcapture-only-failed-registration')
 codes=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);codes.append(ex['returncode']);need(c['state']=='returned'and ex['launch']==c['launch']and ex['argv']==launch['argv']==c['argv']and launch['index']==i and launch['order']==parent['order'],'W65-natural-receipt')
 need(codes==[2]*16+[0,0,2,2,2]and parent['calls'][16]['argv'][2]=='run'and parent['calls'][17]['argv'][2]=='accept','W65-mixed21-failed19')
 last=parent['calls'][20];ex=doc(last['result']);launch=doc(last['launch']);need(ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W65_ERROR}and ex['reboot_continuation']==launch['reboot_continuation']==W65_BASE,'W65-natural-child20')
 need(summary['worker_live']is False and summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-24','W65-original-worker24-dead')
 state=doc(summary['detail_archive']);need(state==summary['detail_state_value']and state['phase']=='complete'and state['cursor']==6 and len(state['details'])==6 and len(state['calls'])==12 and state['calls'][5]['state']=='unknown'and all(c['state']=='confirmed'for i,c in enumerate(state['calls'])if i!=5),'W65-preserved-six-details')
 import governance_detail as detail
 need(detail.unresolved_detail_calls(state)==[],'W65-only-known-retired-UNKNOWN')
 frontier=doc(W65_FRONTIER);owner=doc(original['native_owner_archive']);need(owner==doc(frontier['native_owner_archive'])and len(owner['frames'])==1,'W65-original-native-owner');entry=owner['frames'][0];need(entry['state']=='unknown'and entry.get('registration')is None and entry['operation']==frontier['operation']and entry['raw_capture_metadata']==frontier['raw_capture_metadata']and entry['postguard_audit']==frontier['postguard_audit'],'W65-original-captured-UNKNOWN-preserved')
 a=engine['companies'][1]['artifacts'];marker=a['frame_state']['preintent_observation_refresh'];op=entry['operation'];need(a['frame_index']==0 and not a['frames']and a['frame_state']==summary['frame_state']and a['source']==op['source']and a['profile']==op['profile']and a['frame_state']['observation']==marker['fresh']==op['observation']and marker['binding']=={k:op[k]for k in('source','profile','key','outdir')},'W65-exact-original-capture-operation')
 audit=doc(entry['postguard_audit']);meta=doc(entry['raw_capture_metadata']);need(audit['operation']==op and audit['before']==entry['before']and audit['geometry_before']==entry['geometry_before']and audit['capture_metadata']==entry['raw_capture_metadata']and meta['state']=='complete'and meta['command']==audit['native_command'],'W65-captured-not-recaptureable')
 for image in frontier['images'].values():raw({'path':image['path'],'sha256':image['sha256']})
 need(engine['accepted'][-1]==doc(original['engine_archive'])['accepted'][-1]and engine['accepted'][-1]['state']=='complete','W65-preserved-accepted-copy')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for i,c in enumerate(parent['calls'])if codes[i]==2],'failed_child':last,'original_native_owner':owner}
def w65_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'original-captured-preview-registered-and-QA-verified-not-recapture'});return after
def w65_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':97,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after


W65_KIND='verified-violation-existing-region-registration-source-successor-v1'
W65_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'89e35dd10a68fcbf1b1ec9544324e7aac55618638ca384ac641588330753d504'}
W65_CF_AFTER='a1554688132549e644a9df59c1262e099edb6ea83d81acf7b3faad51f5b12008'
W65_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('violation_initial_ledger_recovery.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W65_CF['path']}
def w65_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W65_PATHS,'W65-exact-reviewed-five-sources');base=doc(W65_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W65_CF['path'];original=W65_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W65_CF_AFTER,'W65-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W65-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']}
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==5,'W65-no-added-slot');return archives,codes

# Work-only source/recovery assembly; actor exact reference is filled only after its independent freeze.
W65_REGISTRATION_ACTOR={'path':str(PROJECT/'work/performance-audit/existing-region-registration-actor-candidate/registration_actor.py'),'sha256':'9c4a03c33bb080c84176dd175f9e08f139c880329f2253c384e0222bf7898bc6'}

def w65_registration(receipt_ref,release_ref):
 import types
 need(isinstance(W65_REGISTRATION_ACTOR,dict),'W65-registration-actor-not-reviewed')
 module=types.ModuleType('_w65_existing_region_registration_actor');module.__file__=W65_REGISTRATION_ACTOR['path'];exec(compile(raw(W65_REGISTRATION_ACTOR),module.__file__,'exec'),module.__dict__)
 value=module.verify_data(receipt_ref,expected_release=release_ref);need(value['QA_complete']is True,'W65-registration-requires-independent-completed-QA');return value

def w65_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W65_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-24'and value['previous_admission']==W65_BASE and value['failure']==W65_FAILURE,'W65-fixed-original-failed24')
 archives,codes=w65_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W65-derived-exact-source-view');registration=w65_registration(value['registration_receipt'],value['release']);base=w64_verify(W65_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives})
 summary=doc(W65_FAILURE);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W65-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w65_failure(parent,engine)
 receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w65_parent_after(parent,reference)and doc(receipt['engine_after'])==w65_engine_after(engine,reference),'W65-completed-two-CAS-required')
 return {**base,'kind':W65_KIND,'attempt_id':TASK8+'-24','previous_admission':W65_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':20,'call':facts['failed_child'],'returncode':2},'child_admissions':{**base['child_admissions'],'20':W65_BASE},'successor':reference,'engine_prefix':w65_engine_after(engine,reference)['calls'],'registration':registration}

_W65_PREVIOUS_VERIFY=verify
_W65_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W65_KIND:return w65_verify(reference,live_boot=live_boot)
 return _W65_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W65_KIND:return _W65_PREVIOUS_ALLOWED(engine,admission)
 value=w65_verify(admission);need(engine['calls'][:97]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W65-preserved-original-prefix-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w65_apply(release_ref,registration_receipt,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file()and not path.is_symlink(),'W65-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat();need(stat.S_ISREG(held.st_mode)and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W65-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   need(db.execute('select state,attempt from tasks where id=?',(TASK8,)).fetchone()==('failed',24)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W65-original-failed24-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W65-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-24')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W65-worker-dead');summary=doc(W65_FAILURE);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w65_failure(parent,engine);archives,codes=w65_sources(release_ref);w64_verify(W65_BASE,live_boot=clock.boot(),_source_archives=archives);w65_registration(registration_receipt,release_ref)
  out=folder/'existing-region-registration-successors'/digest({'release':release_ref,'failure':W65_FAILURE,'registration_receipt':registration_receipt});need(not(out/'intent.json').exists(),'W65-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True)
  value={'kind':W65_KIND,'task_id':TASK8,'attempt_id':TASK8+'-24','previous_admission':W65_BASE,'failure':W65_FAILURE,'release':release_ref,'registration_receipt':registration_receipt,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w65_parent_after(parent,reference);ne=w65_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0,'capture_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W65-before-CAS-raced');
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink()and o.canonical(path)==path and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W65-lock-replaced-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0,'capture_inputs':0});w65_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Work-only waiting25 source qualification. Never failure-pop or capture repair.
W66_KIND='verified-violation-original-rows-quality-waiting-source-successor-v1'
W66_STOP={'path':str(PROJECT/'work/2026-10-30/round009-issue65-original-recovery/VI25-summary.json'),'sha256':'9880a14c5c2074088bd34d88e6f96ca0848f0bfd5d629dd9afe84577b447b219'}
W66_CONTEXT={'path':str(PROJECT/'work/2026-10-30/round009-issue66-original-quality/task25-raw-context-bytes-v2.json'),'sha256':'afcda29ecddb778707413933cf79900bbfa0ee72e6436f106f3910f43f0ebc86'}
W66_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/existing-region-registration-successors/0fdd5b50c9cdb514d0de8bee7267fce99fcfb83db5dcbe8090815160b8c7483c/admission.json'),'sha256':'3e8f57d7b01d3e06cd06716a2b122765fb6396bc7137e35e89cc4ab0822540a7'}
W66_PATHS=None
W66_QUALITY_MODULE=None

def w66_waiting(parent,engine):
 summary=doc(W66_STOP);original_context=doc(W66_CONTEXT);need(summary['kind']=='VI25-natural-rows-visual-QA-waiting-summary-v1'and parent==doc(summary['parent_archive'])and engine==doc(summary['engine_archive']),'W66-exact-original-waiting-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==original_context['reboot_continuation']==W66_BASE and parent['status']=='waiting'and len(parent['calls'])==22,'W66-original-parent22-waiting')
 need(engine['status']=='waiting'and engine['phase']=='frames'and engine.get('error')is None and len(engine['calls'])==103 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls']),'W66-no-failed-call-to-pop')
 codes=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);codes.append(ex['returncode']);need(c['state']=='returned'and ex['launch']==c['launch']and ex['argv']==launch['argv']==c['argv']and launch['index']==i,'W66-natural-original-receipts')
 need(codes==[2]*16+[0,0,2,2,2,0],'W66-22prefix-19failed-3normal')
 need(summary['worker_live']is False and summary['worker']['returncode']==0 and doc(summary['response'])['outcome']=='waiting','W66-natural-worker25-waiting-not-failed')
 handoff=doc(engine['handoff']);need(engine['handoff']==summary['handoff']and handoff['response_kind']=='violation-frame-qa-response-v1'and handoff['program_quality_exception']=='quality-full-cell-text-required'and handoff['preview']==summary['preview']and handoff['source']==summary['source'],'W66-original-handoff103')
 a=engine['companies'][1]['artifacts'];need(a['frame_index']==1 and len(a['frames'])==1 and a['frames'][0]['sha256']=='cb01068f2d3aacbc47ea80899c3c79575d936c546acbf5935fdde58663cb33a4','W66-existing-anchor-complete')
 for k in('preview','raw','crop','raw_metadata','postguard'):raw(summary[k])
 owner=doc(summary['native_owner_archive']);hits=[x for x in owner['frames']if x.get('registration')==summary['preview']];need(len(hits)==1 and hits[0]['state']=='awaiting-visual-review','W66-original-rows-already-registered')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for c,rc in zip(parent['calls'],codes)if rc==2],'normal_calls':[c for c,rc in zip(parent['calls'],codes)if rc==0],'handoff':engine['handoff'],'preview':summary['preview'],'original_context':original_context}

def w66_sources(release_ref):
 need(isinstance(W66_PATHS,set)and W66_PATHS and W66_QUALITY_MODULE is not None,'W66-source-set-and-quality-not-reviewed')
 raise ValueError('W66-source-verifier-not-finalized')

def w66_verify(reference,*,live_boot=None):
 need(W66_QUALITY_MODULE is not None,'W66-quality-ref-not-reviewed')
 raise ValueError('W66-waiting-admission-not-finalized')

def w66_effective_context(request,context,response,parent):
 import execution_timing as timing
 reference=response.get('waiting_source_successor');need(reference is not None,'W66-response-successor-required');value=w66_verify(reference,live_boot=timing.Clock().boot())
 original=doc(W66_CONTEXT);stop=doc(W66_STOP);need(doc(request['context']['response'])==response and request['task']['context']==request['context'],'W66-actual-response-reference-content');need(request['task']['id']==TASK8 and request['task']['flow']=='violation-notifier'and request['attempt_id']==TASK8+'-26'and request['task']['attempt']==25,'W66-only-first-legal-new-worker26')
 need(request['task']['outer']==value['original']['outer']and request['task']['active_attempt']==str(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-25')),'W66-original-worker25-and-outer')
 need(context==original and context['reboot_continuation']==W66_BASE and request['context']=={**original,'response':request['context']['response']},'W66-original-W65-context-unmodified')
 need(value['kind']==W66_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-25'and value['previous_admission']==W66_BASE,'W66-typed-waiting-successor')
 need(response['kind']=='workshop-handoff-response-v1'and response['task_id']==TASK8 and response['request']==original['handoff']and response['parent_response']==value['quality_response'],'W66-original-supervisor-response-binding')
 inner=doc(response['parent_response']);need(set(inner)=={'request','kind','attestation'}and inner['kind']=='violation-frame-qa-response-v1'and inner['request']==stop['handoff']and inner['attestation']==value['quality_attestation'],'W66-exact-original-QA-response')
 need(parent['reboot_continuation']==reference and parent['order']==TASK8_ORDER and parent['calls']==value['original_parent_prefix']and parent['status']=='waiting','W66-original-parent-awaits-exact-QA-accept')
 return {**context,'reboot_continuation':reference,'waiting_source_context_origin':W66_CONTEXT}

W66_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'a1554688132549e644a9df59c1262e099edb6ea83d81acf7b3faad51f5b12008'}
W66_CF_AFTER='785f0bd19277806c3ae4bb8046ec0f132b96e4de48f562ab23a43a5be20fdf01'
W66_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('program_object_ellipsis_quality.py','region_frame_capture.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'packages/workshop-director/workshop_director/adapters.py'),str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W66_CF['path']}
W66_QUALITY_MODULE={'path':str(PROJECT/'skills/violation-notifier/scripts/program_object_ellipsis_quality.py'),'sha256':'6e5f8974506a2099d95120a99fc172fb76900da6773d8a6aa43ddc0914e71745'}

def w66_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==7 and {t['target']for t in release['targets']}==W66_PATHS,'W66-exact-reviewed-seven-sources');base=doc(W66_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W66_CF['path'];original=W66_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W66_CF_AFTER,'W66-independent-CF-tested-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W66-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']}
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==7,'W66-no-added-slot');return archives,codes

def w66_quality(response_ref):
 import program_object_ellipsis_quality as quality
 need(o.ref(Path(quality.__file__))==W66_QUALITY_MODULE,'W66-fixed-five-field-quality-module');raw(W66_QUALITY_MODULE);summary=doc(W66_STOP);response=doc(response_ref);need(set(response)=={'request','kind','attestation'}and response['kind']=='violation-frame-qa-response-v1'and response['request']==summary['handoff'],'W66-exact-original-frame-QA-response');preview=doc(summary['preview']);a=doc(response['attestation']);virtual_final={**preview,'state':'complete','quality_attestation':response['attestation'],'quality_approved_at':a['checked_at']};quality.pixel_review_verify(response['attestation'],virtual_final,summary['source']);facts=quality.reviewed_pixel_facts(preview,summary['source']);need(len(facts['cells'])==20 and all(c['full_text_visible']is(not c['key'].endswith(':object'))and c['visible_fragment']is True for c in facts['cells'])and facts['all_five_fields_preserved']is True,'W66-five-fields-four-incomplete-objects');return {'response':response_ref,'attestation':response['attestation'],'preview':summary['preview'],'source':summary['source'],'pixel_review':facts['review'],'quality_approval_performed':False}

def w66_parent_after(before,reference):
 after=copy.deepcopy(before);after['reboot_continuation']=reference;return after

def w66_engine_after(before,reference):
 after=copy.deepcopy(before);after['reboot_continuation']=reference;return after

def w66_verify(reference,*,live_boot=None,_source_archives=None):
 value=doc(reference);need(value.get('kind')==W66_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-25'and value['previous_admission']==W66_BASE and value['stop']==W66_STOP and value['original_context']==W66_CONTEXT,'W66-fixed-original-waiting25');archives,codes=w66_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W66-derived-source-view');base=w65_verify(W66_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives});summary=doc(W66_STOP);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W66-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w66_waiting(parent,engine);quality=w66_quality(value['quality_response']);need(value['quality_contract']==quality,'W66-derived-quality-response');receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w66_parent_after(parent,reference)and doc(receipt['engine_after'])==w66_engine_after(engine,reference),'W66-complete-source-only-two-CAS-required');return {**base,'kind':W66_KIND,'attempt_id':TASK8+'-25','previous_admission':W66_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'waiting_source_child':{'index':21,'call':parent['calls'][21],'returncode':0},'child_admissions':{**base['child_admissions'],'21':W66_BASE},'successor':reference,'engine_prefix':engine['calls'],'quality_response':quality['response'],'quality_attestation':quality['attestation'],'original_waiting_handoff':facts['handoff'],'quality_approval_performed_by_source_qualification':False}

_W66_PREVIOUS_VERIFY=verify
_W66_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W66_KIND:return w66_verify(reference,live_boot=live_boot)
 return _W66_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W66_KIND:return _W66_PREVIOUS_ALLOWED(engine,admission)
 value=w66_verify(admission);need(engine['calls'][:103]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W66-original103-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w66_apply(release_ref,quality_response,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file()and not path.is_symlink(),'W66-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat();need(stat.S_ISREG(held.st_mode)and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W66-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt,context from tasks where id=?',(TASK8,)).fetchone();need(row[:2]==('waiting',25)and json.loads(row[2])==doc(W66_CONTEXT)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W66-original-waiting25-context-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W66-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-25')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W66-worker25-dead');summary=doc(W66_STOP);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w66_waiting(parent,engine);archives,codes=w66_sources(release_ref);w65_verify(W66_BASE,live_boot=clock.boot(),_source_archives=archives);quality=w66_quality(quality_response)
  out=folder/'rows-object-pixel-quality-waiting-successors'/digest({'release':release_ref,'stop':W66_STOP,'quality_response':quality_response});need(not(out/'intent.json').exists(),'W66-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W66_KIND,'task_id':TASK8,'attempt_id':TASK8+'-25','previous_admission':W66_BASE,'stop':W66_STOP,'original_context':W66_CONTEXT,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'quality_response':quality_response,'quality_contract':quality,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False,'QA_approval_performed':False};reference=o.immutable(out/'admission.json',value);np=w66_parent_after(parent,reference);ne=w66_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'source_qualification_only':True,'task_context_database_written':False,'QA_approval_performed':False,'business_inputs':0,'capture_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W66-before-CAS-raced')
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink()and o.canonical(path)==path and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W66-lock-replaced-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'source_qualification_only':True,'QA_approval_performed':False});w66_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()


# Work-only exact original failed27 boundary. No capture, image or metadata writes.
W67_FAILURE={'path':str(PROJECT/'work/2026-10-30/round009-issue67-original-capture/director-VI27-summary.json'),'sha256':'3c108b7e7af3f503dfa423543912345979cf46a6f563e6390ec84bb9ee9acefa'}
W67_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/rows-object-pixel-quality-waiting-successors/6e44c60ea50a5d6536a3672baaac9538448a3510a54dd435b8d79a697131c80f/admission.json'),'sha256':'2299a9ff487da851bd69802b6cc41d1790138d34f4c7ca06eef0570a8477c009'}
W67_ERROR='violation-region-dom-or-native-frame-changed'
W67_CONTEXT={'path':str(PROJECT/'work/2026-10-30/round009-issue67-original-capture/director-original27-context-raw.json'),'sha256':'8af08ef08fa2ab9ad49923dde6f3e6c0377d766b29fe15f5d4bda56842bf0033'}
def w67_failure(parent,engine):
 summary=doc(W67_FAILURE);need(summary['kind']=='VI27-natural-postraw-frame-proof-failure-summary-v1'and parent==doc(summary['parent_archive'])and engine==doc(summary['engine_archive']),'W67-exact-original-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W67_BASE and parent['status']=='hold'and parent['error']=='execution-child-stopped'and len(parent['calls'])==24,'W67-original-parent24')
 need(engine['status']=='hold'and engine['phase']=='frames'and engine['index']==1 and engine['error']==W67_ERROR and len(engine['calls'])==112 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:111]),'W67-original-engine112')
 failed=engine['calls'][111];need(failed==summary['failed_call']and failed['step']=='frames'and failed['state']=='failed'and failed['company_index']==1 and failed['error']==W67_ERROR and 'result'not in failed and failed['context']['artifacts']==engine['companies'][1]['artifacts'],'W67-exact-postraw-only-failure')
 codes=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);codes.append(ex['returncode']);need(c['state']=='returned'and ex['launch']==c['launch']and ex['argv']==launch['argv']==c['argv']and launch['index']==i and launch['order']==parent['order'],'W67-original-natural-receipts')
 need(codes==[2]*16+[0,0,2,2,2,0,0,2]and [parent['calls'][i]['argv'][2]for i in(16,17,21,22,23)]==['run','accept','run','accept','run'],'W67-mixed24-failed20-normal4')
 last=parent['calls'][23];ex=doc(last['result']);launch=doc(last['launch']);need(ex['returncode']==2 and ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W67_ERROR}and ex['reboot_continuation']==launch['reboot_continuation']==W67_BASE,'W67-natural-child23')
 need(summary['worker_live']is False and summary['worker']['returncode']==0 and summary['worker']['attempt_id']==TASK8+'-27'and summary['task_state']=='failed'and summary['task_attempt']==27 and summary['current_task_context']['reboot_continuation']==W67_BASE,'W67-natural-failed27-not-wrapper-success')
 detail=doc(summary['detail_archive']);need(detail['phase']=='complete'and detail['cursor']==6 and len(detail['details'])==6 and len(detail['calls'])==12 and detail['calls'][5]['state']=='unknown'and all(c['state']=='confirmed'for i,c in enumerate(detail['calls'])if i!=5),'W67-preserved-six-details-and-retired-UNKNOWN')
 # The prior admission verifies this unchanged historical detail/retirement proof.
 need(summary['detail_archive']['sha256']==doc(W65_FAILURE)['detail_archive']['sha256'],'W67-same-exact-previously-verified-detail-state')
 owner=doc(summary['native_owner_archive']);entry=owner['frames'][summary['native_entry_index']];need(entry==summary['native_entry']and entry is owner['frames'][-1]and entry['state']=='unknown'and entry.get('registration')is None,'W67-original-postraw-UNKNOWN')
 a=engine['companies'][1]['artifacts'];op=entry['operation'];need(a['frame_index']==summary['frame_index']==5 and a['frames']==summary['frames']and len(a['frames'])==2 and a['source']==op['source']and a['profile']==op['profile']and op['mode']=='rows'and op.get('uncovered_only')is True and Path(op['outdir']).name=='0005-rows','W67-original-frame5-operation')
 audit=doc(entry['postguard_audit']);need(audit['operation']==op and audit['before']==entry['before']and audit['geometry_before']==entry['geometry_before']and audit['capture_metadata']==entry['raw_capture_metadata']and audit['geometry_before']==audit['geometry_after'],'W67-original-complete-native-audit')
 need(audit['before']['derived_business_coverage']['notice_ids']==audit['after']['derived_business_coverage']['notice_ids']==['ZS202610264820919207']and summary['crop_present']is False and summary['preview_present']is False,'W67-row5-only-original-prederivation-failure')
 need(summary['raw_image']['sha256']=='d94910311c80fd7ef468d50e9ac537a079b567baecadfc09f0de17a679d3ed97','W67-exact-original-raw');raw(summary['raw_image'])
 for ref in summary['frame_files']:raw(ref)
 need(engine['accepted']==doc(summary['engine_archive'])['accepted']and engine['companies'][0]==doc(summary['engine_archive'])['companies'][0],'W67-accepted-and-Shanghai-preserved')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for c,rc in zip(parent['calls'],codes)if rc==2],'failed_child':last,'original_native_owner':owner}
def w67_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'original-row5-raw-derived-registered-and-independent-five-field-QA-not-recapture'});return after
def w67_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':111,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after


W67_KIND='verified-violation-original-raw-diagnostic-preview-source-successor-v1'
W67_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'785f0bd19277806c3ae4bb8046ec0f132b96e4de48f562ab23a43a5be20fdf01'}
W67_CF_AFTER='498145b11e9bc1b9b3bdd303e336ace5701909e87e2682fadc13eabfb69ea5ee'
W67_PATHS={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('region_postguard_retake.py','violation_reboot_continuation.py','violation_execution_ports.py')}|{str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W67_CF['path']}
def w67_sources(release_ref,*,_source_archives=None):
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==5 and {t['target']for t in release['targets']}==W67_PATHS,'W67-exact-reviewed-five-sources');base=doc(W67_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};archives={}
 for t in release['targets']:
  independent=t['target']==W67_CF['path'];original=W67_CF if independent else by[t['target']];need(not independent or t['after']['sha256']==W67_CF_AFTER,'W67-independent-CF-tested-generation');need(t['target']!=str(PROJECT/'skills/violation-notifier/scripts/region_postguard_retake.py')or t['after']['sha256']=='0d8328b6abb2e477aaea1dff267e6baa89c783b511a780fecdf32dc25c12227c','W67-exact-tested-postguard-generation');need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W67-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};source_reference(current,_source_archives);archives[t['target']]={'original':original,'archive':t['before']}
  if not independent:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==5,'W67-four-existing-slots-and-independent-CF');return archives,codes


# Runtime actor ref is deliberately unset until Root freezes its independent code.
W67_REGISTRATION_ACTOR={'path':str(PROJECT/'work/performance-audit/W67-original-raw-registration-actor/registration_actor_v2.py'),'sha256':'faa131775519e322c8f05da2d4c28575122e6ef440cd0e79ef2d8dd166a3f2a9'}

def w67_registration(receipt_ref,release_ref):
 import types
 need(isinstance(W67_REGISTRATION_ACTOR,dict),'W67-registration-actor-not-reviewed');module=types.ModuleType('_w67_existing_row5_registration_actor');module.__file__=W67_REGISTRATION_ACTOR['path'];exec(compile(raw(W67_REGISTRATION_ACTOR),module.__file__,'exec'),module.__dict__)
 result=module.verify_data(receipt_ref,expected_release=release_ref);need(result['QA_complete']is True,'W67-independent-five-field-completed-QA-required');return result

def w67_verify(reference,*,live_boot=None,_source_archives=None,_successor_release=None):
 value=doc(reference);need(value.get('kind')==W67_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-27'and value['previous_admission']==W67_BASE and value['failure']==W67_FAILURE,'W67-fixed-original-failed27')
 need(_source_archives is None or _successor_release is not None and _source_archives==w68_sources(_successor_release)[0],'W68-private-W67-source-view-only');archives,codes=w67_sources(value['release'],_source_archives=_source_archives);need(value['source_archives']==archives and value['current_code_refs']==codes,'W67-derived-source-view');registration=w68_historical_registration(value['registration_receipt'],value['release'],_successor_release) if _source_archives is not None else w67_registration(value['registration_receipt'],value['release']);base=w66_verify(W67_BASE,live_boot=live_boot,_source_archives={**(_source_archives or {}),**archives})
 summary=doc(W67_FAILURE);need(value['parent_before']['sha256']==summary['parent']['sha256']and value['engine_before']['sha256']==summary['engine']['sha256'],'W67-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w67_failure(parent,engine);receipt=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(receipt['admission']==reference and doc(receipt['parent_after'])==w67_parent_after(parent,reference)and doc(receipt['engine_after'])==w67_engine_after(engine,reference),'W67-completed-two-CAS-required')
 return {**base,'kind':W67_KIND,'attempt_id':TASK8+'-27','previous_admission':W67_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':23,'call':facts['failed_child'],'returncode':2},'child_admissions':{**base['child_admissions'],'22':W67_BASE,'23':W67_BASE},'successor':reference,'engine_prefix':w67_engine_after(engine,reference)['calls'],'registration':registration}
_W67_PREVIOUS_VERIFY=verify
_W67_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W67_KIND:return w67_verify(reference,live_boot=live_boot)
 return _W67_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W67_KIND:return _W67_PREVIOUS_ALLOWED(engine,admission)
 value=w67_verify(admission);need(engine['calls'][:111]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W67-preserved111-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w67_apply(release_ref,registration_receipt,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file()and not path.is_symlink(),'W67-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat();need(stat.S_ISREG(held.st_mode)and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W67-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt,context from tasks where id=?',(TASK8,)).fetchone();need(row[:2]==('failed',27)and row[2].encode()==raw(W67_CONTEXT)and json.loads(row[2])==doc(W67_FAILURE)['current_task_context']and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W67-original-failed27-context-only');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W67-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-27')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W67-worker27-dead');summary=doc(W67_FAILURE);pr=summary['parent'];er=summary['engine'];parent=doc(pr);engine=doc(er);w67_failure(parent,engine);archives,codes=w67_sources(release_ref);w66_verify(W67_BASE,live_boot=clock.boot(),_source_archives=archives);w67_registration(registration_receipt,release_ref)
  out=folder/'postraw-diagnostic-registration-successors'/digest({'release':release_ref,'failure':W67_FAILURE,'registration_receipt':registration_receipt});need(not(out/'intent.json').exists(),'W67-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True)
  value={'kind':W67_KIND,'task_id':TASK8,'attempt_id':TASK8+'-27','previous_admission':W67_BASE,'failure':W67_FAILURE,'release':release_ref,'registration_receipt':registration_receipt,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w67_parent_after(parent,reference);ne=w67_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'capture_inputs':0,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W67-before-CAS-raced')
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink()and o.canonical(path)==path and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W67-lock-replaced-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0,'capture_inputs':0});w67_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

# Work-only unified three-fix candidate. All runtime gates default strict.
W68_KIND='verified-violation-unified-fractional-leaf-validation-source-successor-v1'
W68_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/postraw-diagnostic-registration-successors/2ac972c354b44beca17091186270a9d357e7311d02bd4c8970eb40e744f1a060/admission.json'),'sha256':'8806a3925e1f6739a8dcd201c0a22d30cd149cc4d8753248b8e3e7182e20a2b2'}
W68_FAILURE={'path':str(PROJECT/'work/2026-10-30/round009-issue68-original-selection/director-VI28-summary.json'),'sha256':'a5b2c242b69f97025f2f2366def60d830327df62b8689c64dda466445ac987a0'}
W68_CONTEXT={'path':str(PROJECT/'work/2026-10-30/round009-issue68-original-selection/director-original28-context-raw.json'),'sha256':'0b2ee30d7ace79181b0c468feaf69fa9bc632917fa3dc8c52dc8c54033ff44a3'}
W68_BUSINESS={'path':str(PROJECT/'work/performance-audit/sixth-row-fractional-auto-clip-candidate/CONTRACT-v4.json'),'sha256':'18db7bb722c8a6454c7b5f6ddd111149139048308ef3c0cf4d715ba9651ae1e9'}
W68_BODY_SUCCESSOR={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/W68-body-root-selector-candidate/CONTRACT.json', 'sha256': 'ffe0b59c8ff536cf1f9652294ae0b9b9c77bac01e7ff75867878a145804b9408'}
W68_PUBLISHED_FULL10={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue68-maintenance/source/full10/supervisor-release.json', 'sha256': 'ba08d60b07edf89f832baf61c81725d89c7a74bb130aa272c034f5bba019d324'}
W68_PUBLISHED_PRODUCER={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-30/round009-issue68-original-recovery/producer-load-once/returned.json', 'sha256': 'ce461551f40b5301e3ce2c0953c65c846e7d3dee84425ba3a737f370afe4d67f'}
W70_POSTGUARD={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/v13-unselected-header-postguard-candidate/CONTRACT.json', 'sha256': '6b5b92e174a7a3be20d1e23a78fd46510af7c41a26b7a3f784712a8611f8c381'}
W70_PERFORMANCE={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/registration-command-effect-boundary-candidate/CONTRACT.json', 'sha256': '4dd7fdcf6c98036af6ab247491404b73d1be7b94718cec4cce5c55972f0acbd8'}
W68_HISTORY_READER={'path':str(PROJECT/'work/performance-audit/W67-reviewed-history-reader/history_reader_v4.py'),'sha256':'d28c2d70456dd3e26589d461fc7b8944fa20495dff6a54343c525ba81cd4817e'}
W68_CF={'path':str(PROJECT/'skills/negative-review-complaints/scripts/initial_ledger_recovery.py'),'sha256':'498145b11e9bc1b9b3bdd303e336ace5701909e87e2682fadc13eabfb69ea5ee'}
W68_CF_AFTER='0a6f809a8e447a228cd9dac3c864a05f2eac37c08ce15ae555d3143abf9ce371'
W68_PERFORMANCE={'path':str(PROJECT/'work/performance-audit/registration-governance-command-scope-v5-candidate/CONTRACT.json'),'sha256':'d9701e94b9d0e14fba486ace60956c556b4c03f4ee2a26e11ead5778c07716d5'}
W68_DELIVERY={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/unified-completion-admitted-role-sources-candidate/CONTRACT.json', 'sha256': 'e6aaf5bb5b6e201ac101f6f87fd940528d09a90c8dfa33fcd725b6ae9ec3a1a7'}
W68_FRAME_FRONTIER={'path':str(PROJECT/'work/2026-10-30/round009-issue68-original-selection/director-VI28-FRAME-FRONTIER.json'),'sha256':'99b62a397f55b1af66f9d3540b54069f9c127171984ac6c6747f179278152e84'}
W68_ERROR='violation-uncovered-no-eligible-five-cell-group-see-base-proof-replies'
W68_PATHS={str(PROJECT/'skills/chrome-dom-export/extension/viewport-proof.js'),*(str(PROJECT/'skills/chrome-dom-export/scripts'/n)for n in('business_cells_capture.py','screenshot_registration.py')),*(str(PROJECT/'skills/violation-notifier/scripts'/n)for n in('region_frame_capture.py','registration_validation.py','violation_reboot_continuation.py','violation_execution_ports.py')),str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W68_CF['path'],str(PROJECT/'skills/workshop-director/scripts/unified_delivery.py'),str(PROJECT/'skills/violation-notifier/scripts/region_postguard_retake.py')}
def w68_sources(release_ref):
 need(isinstance(W68_PERFORMANCE,dict)and isinstance(W68_CF_AFTER,str),'W68-all-three-fixes-not-final')
 release=doc(release_ref);need(release.get('kind')=='supervisor-reviewed-source-release-v1'and release.get('published')is True and release.get('test_projection_only')is False and release.get('reviewed_by')=='workshop-director'and len(release['targets'])==11 and {t['target']for t in release['targets']}==W68_PATHS,'W70-exact-eleven-physical-qualification-sources')
 base=doc(W68_BASE);codes=copy.deepcopy(base['current_code_refs']);by={r['path']:r for r in codes};need(len(codes)==len(by)==159,'W68-original159-no-added-slot');business=doc(W68_BUSINESS);need(business['kind']=='W68-fractional-auto-padding-and-public-text-four-source-business-package-v2'and business['no_original_slot_added']is True and len(business['targets'])==4,'W68-fixed-reviewed-business4');reviewed={r['target']:r for r in business['targets']};body=doc(W68_BODY_SUCCESSOR);need(body['kind']=='W68-reviewed-source-root-body-selector-successor-v1'and len(body['targets'])==1 and body['prior_business_contract']==W68_BUSINESS and body['prior_published_full10']==W68_PUBLISHED_FULL10 and body['original_producer_receipt']==W68_PUBLISHED_PRODUCER,'W68-exact-root-body-successor');bodyrow=body['targets'][0];bodypath=str(PROJECT/'skills/chrome-dom-export/scripts/business_cells_capture.py');prior=reviewed[bodypath];need(bodyrow['target']==bodypath and bodyrow['mode']==420 and body['original_before']==prior['before']and body['previous_payload']==prior['payload']and bodyrow['before']['sha256']==prior['payload']['sha256']and raw(bodyrow['before'])==raw(prior['payload']),'W68-root-body-prior-archive');reviewed[bodypath]={**prior,'payload':bodyrow['payload']};performance=doc(W68_PERFORMANCE);need(performance.get('kind')=='W68-command-scope-history-validation-performance-subpackage-v1'and len(performance['targets'])==1 and performance['targets'][0]['target']==str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py'),'W68-single-performance-subpackage');reviewed.update({r['target']:r for r in performance['targets']});perf_new=doc(W70_PERFORMANCE);need(perf_new['kind']=='W70-command-effect-boundary-single-source-package-v1'and len(perf_new['targets'])==1,'W70-effect-single-source');pn=perf_new['targets'][0];po=performance['targets'][0];need(pn['target']==po['target']and pn['mode']==420 and pn['before']['sha256']==po['payload']['sha256']and raw(pn['before'])==raw(po['payload']),'W70-effect-previous-source');reviewed[pn['target']]={**po,'payload':pn['payload']};pg=doc(W70_POSTGUARD);need(pg['kind']=='W70-v13-unselected-header-postguard-single-source-package-v1'and len(pg['targets'])==1 and pg['targets'][0]['target']==str(PROJECT/'skills/violation-notifier/scripts/region_postguard_retake.py'),'W70-postguard-existing-source');reviewed[pg['targets'][0]['target']]=pg['targets'][0];delivery=doc(W68_DELIVERY);need(delivery['kind']=='unified-completion-admitted-role-single-source-package-v1'and len(delivery['targets'])==1 and delivery['targets'][0]['target']==str(PROJECT/'skills/workshop-director/scripts/unified_delivery.py'),'W68-fixed-completion-source');reviewed.update({r['target']:r for r in delivery['targets']});archives={}
 for t in release['targets']:
  independent=t['target']==W68_CF['path'];original=W68_CF if independent else by[t['target']];need(t['old_sha256']==t['before']['sha256']==original['sha256']and t['mode']==420 and t['after']['sha256']!=original['sha256'],'W68-exact-before-existing-slot');raw(t['before']);raw(t['after']);current={'path':t['target'],'sha256':t['after']['sha256']};raw(current);need(Path(t['target']).stat().st_mode&0o777==420,'W68-actual-current-mode');archives[t['target']]={'original':original,'archive':t['before']}
  if t['target']in reviewed:
   r=reviewed[t['target']];need(r['mode']==420 and r['before']['sha256']==original['sha256']and raw(r['before'])==raw(t['before'])and r['payload']['sha256']==t['after']['sha256']and raw(r['payload'])==raw(t['after']),'W68-exact-tested-business-performance-payload')
  if independent:need(current['sha256']==W68_CF_AFTER,'W68-fixed-independent-CF-after')
  else:codes[codes.index(original)]=current
 need(len(codes)==159 and len(archives)==11,'W70-ten-existing-slots-one-independent-CF')
 for current in codes:raw(current)
 return archives,codes

def w68_historical_registration(receipt_ref,old_release,successor_release):
 import types
 need(successor_release is not None,'W68-history-successor-required');module=types.ModuleType('_w68_fixed_W67_history_reader');module.__file__=W68_HISTORY_READER['path'];exec(compile(raw(W68_HISTORY_READER),module.__file__,'exec'),module.__dict__);return module.verify_data(receipt_ref,expected_release=old_release,successor_release=successor_release)

def w68_failure(parent,engine,*,live_frontier=False):
 s=doc(W68_FAILURE);need(parent==doc(s['parent_archive'])and engine==doc(s['engine_archive'])and parent['order']==engine['order']==TASK8_ORDER,'W68-original-immutable-objects');need(parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent['reboot_continuation']==engine['reboot_continuation']==W68_BASE and len(parent['calls'])==25,'W68-original-parent25');need(engine['status']=='hold'and engine['phase']=='frames'and engine['index']==1 and engine['error']==W68_ERROR and len(engine['calls'])==117 and all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:116]),'W68-original-engine117');failed=engine['calls'][116];need(failed['state']=='failed'and failed['step']=='frames'and failed['company_index']==1 and failed['error']==W68_ERROR,'W68-exact-preselection-failure');rc=[]
 for i,c in enumerate(parent['calls']):
  ex=doc(c['result']);launch=doc(c['launch']);need(c['state']=='returned'and ex['launch']==c['launch']and ex['argv']==launch['argv']==c['argv']and launch['index']==i and launch['order']==TASK8_ORDER,'W68-original-natural-child');rc.append(ex['returncode'])
 need(rc==[2]*16+[0,0,2,2,2,0,0,2,2]and s['worker_exit_value']['returncode']==0 and s['response_value']['outcome']=='failed','W68-mixed25-failed21-normal4');ex=doc(parent['calls'][24]['result']);need(ex['stderr']==''and json.loads(ex['stdout'])=={'ok':False,'error':W68_ERROR},'W68-natural-child24')
 a=engine['companies'][1]['artifacts'];detail=doc(s['detail_archive']);need(detail['phase']=='complete'and detail['cursor']==6 and len(detail['details'])==6 and len(detail['calls'])==12 and detail['calls'][5]['state']=='unknown'and all(c['state']=='confirmed'for i,c in enumerate(detail['calls'])if i!=5),'W68-six-details-retired-UNKNOWN');need(a['frame_index']==6 and len(a['frames'])==3 and a['frames']==s['frames'],'W68-three-previous-completed-frames');owner=doc(s['native_owner_archive']);need(len(owner['frames'])==3 and all(f['state']=='complete'for f in owner['frames'])and not any(f['operation']['outdir']==str(Path(s['base_reply']['path']).parent.parent)for f in owner['frames']),'W68-no-sixth-native-operation')
 proof=doc(s['base_reply']);need(proof['stage']=='base'and proof['reply']['ok']is True and proof['command']['op']=='viewport-proof'and all(c['geometry']['box_viewport_contained']is False and c['geometry']['evidence_eligible']is False for c in s['sixth_row']['cells'])and s['sixth_row']['notice_id']=='ZS202610264820918624'and s['raw_present']is False and s['preview_present']is False,'W68-original-base-only-no-capture')
 frontier=doc(W68_FRAME_FRONTIER);need([r['original']for r in frontier['files']]==s['frame_files'],'W68-exact-original-frame-file-list')
 for item in frontier['files']:need(item['original']['sha256']==item['archive']['sha256'],'W68-original-file-archive-sha');raw(item['archive'])
 if live_frontier:
  for item in frontier['files']:raw(item['original'])
  need(doc(s['native_owner'])==owner and doc(s['detail'])==detail,'W68-current-preserved-native-detail');out=Path(s['base_reply']['path']).parent.parent;need(not any((out/n).exists()for n in('raw-window.png','raw-window.png.json','preview-registration.json','registration.json')),'W68-no-native-intent-or-image')
 return {'original_parent_prefix':parent['calls'],'failed_calls':[c for c,n in zip(parent['calls'],rc)if n==2],'failed_child':parent['calls'][24],'original_native_owner':owner}
def w68_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'unified-producer-leaf-validation-source-successor-no-recapture'});return after
def w68_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':116,'call':failed,'proof':reference});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

W68_PRODUCER_ACTOR={'path':str(PROJECT/'work/performance-audit/W68-producer-load-once-candidate/load_once.py'),'sha256':'80e52fc3bcdad24d3d41e7cf4b096ce35fc666a72542358621d9a5fb8da4cf34'}
def w68_loaded_producer(receipt_ref,release_ref):
 import types
 module=types.ModuleType('_W68_fixed_loader');module.__file__=W68_PRODUCER_ACTOR['path'];exec(compile(raw(W68_PRODUCER_ACTOR),module.__file__,'exec'),module.__dict__);need(receipt_ref==W68_PUBLISHED_PRODUCER,'W68-only-original-loaded-producer');original_imports=module.imports
 def prior_sources(reference):
  need(reference==W68_PUBLISHED_FULL10,'W68-loader-only-original-source-release');current_archives,current_codes=w68_sources(release_ref);old=doc(W68_PUBLISHED_FULL10);current=doc(release_ref);oldrows={t['target']:t for t in old['targets']};newrows={t['target']:t for t in current['targets']};need(set(oldrows)==W68_PATHS-{str(PROJECT/'skills/violation-notifier/scripts/region_postguard_retake.py')}and set(newrows)==W68_PATHS,'W70-loader-exact-old10-new11-targets');codes=copy.deepcopy(current_codes);by={c['path']:c for c in codes};archives={};originals={c['path']:c for c in doc(W68_BASE)['current_code_refs']};changed=set()
  for path,t in oldrows.items():
   nt=newrows[path];need(t['before']['sha256']==nt['before']['sha256']and t['old_sha256']==nt['old_sha256']and t['mode']==nt['mode']==420 and raw(t['before'])==raw(nt['before']),'W68-loader-exact-original-before');raw(t['after']);original=W68_CF if path==W68_CF['path']else originals[path];archives[path]={'original':original,'archive':t['before']}
   if t['after']['sha256']!=nt['after']['sha256']:changed.add(path)
   if path in by:codes[codes.index(by[path])]={'path':path,'sha256':t['after']['sha256']}
  need(changed=={str(PROJECT/'skills/chrome-dom-export/scripts/business_cells_capture.py'),str(PROJECT/'skills/violation-notifier/scripts/violation_reboot_continuation.py'),str(PROJECT/'skills/workshop-director/scripts/collection_ready.py'),W68_CF['path'],str(PROJECT/'skills/violation-notifier/scripts/registration_validation.py'),str(PROJECT/'skills/violation-notifier/scripts/violation_execution_ports.py')},'W70-loader-only-reviewed-six-changes')
  extra=str(PROJECT/'skills/violation-notifier/scripts/region_postguard_retake.py');need(set(newrows)-set(oldrows)=={extra}and current_archives[extra]['original']==originals[extra],'W70-loader-exact-extra-existing-slot');codes[codes.index(next(c for c in codes if c['path']==extra))]=originals[extra]
  for code in codes:
   if code['path']not in oldrows:source_reference(code,current_archives)
  return archives,codes
 def prior_imports():
  actual,order,ports=original_imports();return types.SimpleNamespace(w68_sources=prior_sources),order,ports
 module.imports=prior_imports;module.verify_receipt(receipt_ref,expected_release=W68_PUBLISHED_FULL10);w68_sources(release_ref)
 import region_frame_capture as region
 value=doc(receipt_ref);s=doc(W68_FAILURE);original=doc(s['base_reply']);need(value.get('kind')=='W68-reviewed-v13-existing-tab-load-receipt-v1'and value['release']==W68_PUBLISHED_FULL10 and value['original_base']==s['base_reply']and value['command']==original['command']and value['viewport_calls']==1 and value['new_capture']is False and value['business_inputs']==0 and value['capture_inputs']==0 and set(value['focus_inputs'])=={'native','tab'}and all(type(n)is int and 0<=n<=1 for n in value['focus_inputs'].values()) and value['bridge_Host_Chrome_restart']is False,'W68-exact-once-readonly-producer-load')
 reply=doc(value['reply']);need(reply['ok']is True and reply['result']['diagnostic_build']=='viewport-notice-business-cells-v13-fractional-auto-padding-v1','W68-actual-v13-not-disk-only');op=original['operation'];inputs=region.fc.page_inputs(op['source'],op['observation'],op['profile']);need(inputs['command']==original['command'],'W68-original-current-frame-command');base=region.business.validate_base(reply['result'],inputs);rows=[r for r in base['business_cells']if r['notice_id']=='ZS202610264820918624'];need(len(rows)==1 and len(rows[0]['cells'])==5 and all(c['geometry']['evidence_eligible']is True and c['geometry']['text_leaf_evidence']['excerpt_eligible']is True for c in rows[0]['cells']),'W68-five-field-new-producer-qualification');need(base['scope']==original['reply']['result']['scope']and base['url']==original['reply']['result']['url'],'W68-original-same-tab-company-scope');return {'receipt':receipt_ref,'base_reply':value['reply'],'diagnostic_build':base['diagnostic_build'],'text_full':[c['geometry']['text_leaf_evidence']['full']for c in rows[0]['cells']],'new_image_independent_QA_required':True,'global_overlay_absence_certified':False}

def w68_verify(reference,*,live_boot=None):
 value=doc(reference);need(value.get('kind')==W68_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-28'and value['previous_admission']==W68_BASE and value['failure']==W68_FAILURE,'W68-exact-original-failed28');archives,codes=w68_sources(value['release']);need(value['source_archives']==archives and value['current_code_refs']==codes,'W68-derived-nine-source-view');loaded=w68_loaded_producer(value['producer_receipt'],value['release']);base=w67_verify(W68_BASE,live_boot=live_boot,_source_archives=archives,_successor_release=value['release']);s=doc(W68_FAILURE);need(value['parent_before']['sha256']==s['parent']['sha256']and value['engine_before']['sha256']==s['engine']['sha256'],'W68-exact-before-archives');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w68_failure(parent,engine);returned=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(returned['admission']==reference and doc(returned['parent_after'])==w68_parent_after(parent,reference)and doc(returned['engine_after'])==w68_engine_after(engine,reference),'W68-natural-two-CAS-complete-required');return {**base,'kind':W68_KIND,'attempt_id':TASK8+'-28','previous_admission':W68_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':24,'call':facts['failed_child'],'returncode':2},'child_admissions':{**base['child_admissions'],'24':W68_BASE},'successor':reference,'engine_prefix':w68_engine_after(engine,reference)['calls'],'producer':loaded}
_W68_PREVIOUS_VERIFY=verify
_W68_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W68_KIND:return w68_verify(reference,live_boot=live_boot)
 return _W68_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W68_KIND:return _W68_PREVIOUS_ALLOWED(engine,admission)
 value=w68_verify(admission);need(engine['calls'][:116]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W68-preserved116-and-Shanghai');return all(c['state']=='returned'for c in engine['calls'])

def w68_apply(release_ref,producer_receipt,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file()and not path.is_symlink(),'W68-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat();need(stat.S_ISREG(held.st_mode)and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W68-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt,context from tasks where id=?',(TASK8,)).fetchone();need(row[:2]==('failed',28)and row[2].encode()==raw(W68_CONTEXT)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W68-original-failed28-context-static');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W68-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-28')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W68-worker28-dead');s=doc(W68_FAILURE);pr=s['parent'];er=s['engine'];parent=doc(pr);engine=doc(er);w68_failure(parent,engine,live_frontier=True);archives,codes=w68_sources(release_ref);w68_loaded_producer(producer_receipt,release_ref);w67_verify(W68_BASE,live_boot=clock.boot(),_source_archives=archives,_successor_release=release_ref)
  out=folder/'unified-fractional-leaf-validation-successors'/digest({'release':release_ref,'failure':W68_FAILURE,'producer_receipt':producer_receipt});need(not(out/'intent.json').exists(),'W68-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W68_KIND,'task_id':TASK8,'attempt_id':TASK8+'-28','previous_admission':W68_BASE,'failure':W68_FAILURE,'release':release_ref,'producer_receipt':producer_receipt,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w68_parent_after(parent,reference);ne=w68_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0,'capture_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W68-before-CAS-raced')
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink()and o.canonical(path)==path and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W68-lock-replaced-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0,'capture_inputs':0});w68_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()

W70_KIND='verified-violation-v13-original-raw-registration-source-successor-v1'

# Work-only exact failed29 postcapture continuation; never recapture the original raw.
W70_KIND='verified-violation-v13-original-raw-registration-source-successor-v1'
W70_BASE={'path':str(PROJECT/'runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/unified-fractional-leaf-validation-successors/94b9a0a1c72b01f0b5101ff9e4ba7bf093bde3710e0ba4c451b535af8ee4a0b3/admission.json'),'sha256':'a49d136482ca384a0dc73ff6f2b56b95cc094d6b870580d80719d8b299619b18'}
W70_FAILURE={'path':str(PROJECT/'work/2026-10-30/round009-issue70-original-capture/director-VI29-summary.json'),'sha256':'a45e6dfcdce8b8cd356efd3c11c16ff068c75e61503fbdf488782911a17a6f9f'}
W70_CONTEXT={'path':str(PROJECT/'work/2026-10-30/round009-issue70-original-capture/original29-context-raw.json'),'sha256':'661cbf8aaf46659b33dbf7f69191fa2935b73184849f7b9277220c4667b81742'}
W70_HISTORY={'path':str(PROJECT/'work/performance-audit/W68-reviewed-history-reader/history_reader.py'),'sha256':'0b7d285d11ec82e497ec909e5727cf0bf40136e5b80794ecbd5ba01cd45e7387'}
W70_REGISTRATION_ACTOR={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/W70-original-raw-registration-candidate/registration_actor_v2.py', 'sha256': '507243eda8a9442414c4e16bbcb746e5e3ab8f4cb0dc00cfaed4794683b3c180'}

def w70_historical_base(release_ref,*,live_boot=None):
 import types
 module=types.ModuleType('_W70_fixed_W68_history');module.__file__=W70_HISTORY['path'];exec(compile(raw(W70_HISTORY),module.__file__,'exec'),module.__dict__);return module.verify(W70_BASE,successor_release=release_ref,live_boot=live_boot)

def w70_failure(parent,engine):
 s=doc(W70_FAILURE);need(parent==doc(s['parent_archive'])and engine==doc(s['engine_archive'])and parent['order']==engine['order']==TASK8_ORDER,'W70-original-natural-objects')
 need(parent['status']=='hold'and parent['error']=='execution-child-stopped'and parent['reboot_continuation']==engine['reboot_continuation']==W70_BASE and len(parent['calls'])==26,'W70-parent26-and-prior-admission')
 need(engine['status']=='hold'and engine['phase']=='frames'and engine['index']==1 and engine['error']=='violation-region-dom-or-native-frame-changed'and len(engine['calls'])==117 and engine['calls'][-1]['state']=='failed'and engine['calls'][-1]['step']=='frames'and engine['calls'][-1]['company_index']==1,'W70-engine117-postcapture-failure')
 previous=doc(W68_FAILURE);need(parent['calls'][:25]==doc(previous['parent_archive'])['calls']and engine['calls'][:116]==doc(previous['engine_archive'])['calls'][:116],'W70-preserved25-and116-prefix')
 need(all(c['state']=='returned'and c.get('applied')is True for c in engine['calls'][:116]),'W70-returned-engine-prefix');rc=[]
 for index,call in enumerate(parent['calls']):
  launch=doc(call['launch']);result=doc(call['result']);need(call['state']=='returned'and launch['order']==TASK8_ORDER and launch['index']==index and launch['argv']==call['argv']==result['argv']and result['launch']==call['launch'],'W70-original-natural-child');rc.append(result['returncode'])
 need(rc==[2]*16+[0,0,2,2,2,0,0,2,2,2],'W70-mixed26-natural-exits');last=doc(parent['calls'][25]['result']);need(json.loads(last['stdout'])=={'ok':False,'error':'candidate-dependency-changed'}and last.get('stderr','')=='','W70-inner-effect-dependency-refusal')
 a=engine['companies'][1]['artifacts'];need(a['frame_index']==6 and a['frames']==s['frames']and len(a['frames'])==3 and a['source']==s['source']and a['profile']==s['profile'],'W70-original-three-completed-images')
 old_owner=doc(s['native_owner_archive']);need(len(old_owner['frames'])==4 and old_owner['frames'][:3]==doc(previous['native_owner_archive'])['frames'],'W70-three-complete-owner-prefix');entry=old_owner['frames'][3];need(entry['state']=='unknown'and not entry.get('registration')and entry==s['new_native_entry'],'W70-original-last-UNKNOWN-preserved')
 audit=doc(entry['postguard_audit']);meta=doc(entry['raw_capture_metadata']);need(audit['kind']=='actual-region-postguard-comparison-v1'and audit['operation']==entry['operation']and audit['before']==entry['before']and audit['geometry_before']==entry['geometry_before']and audit['capture_metadata']==entry['raw_capture_metadata'],'W70-original-actual-audit')
 need(meta['png']['sha256']=='90ead5c4027f3c0184fedcf08dd3317448ee9382d01a43f56287ab42f86baf0b'and o.ref(Path(meta['png']['path']))['sha256']==meta['png']['sha256'],'W70-original-raw-exact');need(audit['before']['derived_business_coverage']['notice_ids']==audit['after']['derived_business_coverage']['notice_ids']==['ZS202610264820918624'],'W70-original-row6-only')
 import region_postguard_retake as pg
 consistency=pg.compare(audit['before'],audit['after'],audit['geometry_before'],audit['geometry_after'],business=True);need(consistency.get('diagnostic_projection')=='unselected-header0-readonly-diagnostic-history-unresolved-v1'and consistency['automatic_certification']is False,'W70-postguard-still-requires-QA')
 need(doc(s['detail'])==doc(s['detail_archive']),'W70-detail6-unchanged')
 return {'original_parent_prefix':copy.deepcopy(parent['calls']),'failed_calls':copy.deepcopy(parent['calls'][:16]+parent['calls'][18:21]+parent['calls'][23:26]),'failed_child':copy.deepcopy(parent['calls'][25]),'native_before':s['native_owner_archive'],'entry':entry,'consistency':consistency}

def w70_registration(reference,release_ref):
 import types
 need(isinstance(W70_REGISTRATION_ACTOR,dict),'W70-registration-actor-not-final');module=types.ModuleType('_W70_fixed_original_raw_registration');module.__file__=W70_REGISTRATION_ACTOR['path'];exec(compile(raw(W70_REGISTRATION_ACTOR),module.__file__,'exec'),module.__dict__);value=module.verify_data(reference,expected_release=release_ref);need(value['QA_complete']is True,'W70-real-final-QA-required');return value

def w70_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error');after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'original-row6-raw-registration-completed-no-recapture'});return after

def w70_engine_after(before,reference):
 after=copy.deepcopy(before);failed=after['calls'].pop();after.setdefault('resolved_readonly_failures',[]).append({'index':116,'call':failed,'proof':reference,'raw_preserved':True});after.update(status='running',reboot_continuation=reference);after.pop('error');return after

def w70_verify(reference,*,live_boot=None):
 value=doc(reference);need(value.get('kind')==W70_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-29'and value['previous_admission']==W70_BASE and value['failure']==W70_FAILURE,'W70-exact-original-failed29');archives,codes=w68_sources(value['release']);need(value['source_archives']==archives and value['current_code_refs']==codes,'W70-current-source11-view');base=w70_historical_base(value['release'],live_boot=live_boot);registration=w70_registration(value['registration_receipt'],value['release']);s=doc(W70_FAILURE);need(value['parent_before']['sha256']==s['parent']['sha256']and value['engine_before']['sha256']==s['engine']['sha256'],'W70-original-before-bytes');parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w70_failure(parent,engine);returned=doc(o.ref(Path(reference['path']).parent/'returned.json'));need(returned['admission']==reference and doc(returned['parent_after'])==w70_parent_after(parent,reference)and doc(returned['engine_after'])==w70_engine_after(engine,reference),'W70-natural-two-CAS-required');return {**base,'kind':W70_KIND,'attempt_id':TASK8+'-29','previous_admission':W70_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':25,'call':facts['failed_child'],'returncode':2},'child_admissions':{**base['child_admissions'],'25':W70_BASE},'successor':reference,'engine_prefix':w70_engine_after(engine,reference)['calls'],'registration':registration}
_W70_PREVIOUS_VERIFY=verify
_W70_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W70_KIND:return w70_verify(reference,live_boot=live_boot)
 return _W70_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W70_KIND:return _W70_PREVIOUS_ALLOWED(engine,admission)
 value=w70_verify(admission);need(engine['calls'][:116]==value['engine_prefix']and engine['companies'][0]==doc(value['original']['engine'])['companies'][0],'W70-original116-and-Shanghai-preserved');return all(c['state']=='returned'for c in engine['calls'])

def w70_apply(release_ref,registration_receipt,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in(PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file()and not path.is_symlink(),'W70-existing-canonical-lock');f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat();need(stat.S_ISREG(held.st_mode)and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W70-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt,context from tasks where id=?',(TASK8,)).fetchone();need(row[:2]==('failed',29)and row[2].encode()==raw(W70_CONTEXT)and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W70-original-failed29-context-static');owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W70-original-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-29')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W70-worker29-dead');s=doc(W70_FAILURE);pr=s['parent'];er=s['engine'];parent=doc(pr);engine=doc(er);w70_failure(parent,engine);archives,codes=w68_sources(release_ref);w70_historical_base(release_ref,live_boot=clock.boot());w70_registration(registration_receipt,release_ref)
  out=folder/'v13-original-raw-registration-successors'/digest({'release':release_ref,'failure':W70_FAILURE,'registration_receipt':registration_receipt});need(not(out/'intent.json').exists(),'W70-partial-CAS-inspect-only');out.mkdir(parents=True,exist_ok=True);value={'kind':W70_KIND,'task_id':TASK8,'attempt_id':TASK8+'-29','previous_admission':W70_BASE,'failure':W70_FAILURE,'release':release_ref,'registration_receipt':registration_receipt,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False};reference=o.immutable(out/'admission.json',value);np=w70_parent_after(parent,reference);ne=w70_engine_after(engine,reference);after={k:o.immutable(out/(k+'-after.json'),v)for k,v in(('parent',np),('engine',ne))};o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'native_capture_inputs':0,'business_inputs':0});need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W70-before-CAS-raced')
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink()and o.canonical(path)==path and(held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W70-lock-replaced-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np);o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'native_capture_inputs':0,'business_inputs':0});w70_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()


"""Work-only W71 fragment; imported into exact reboot namespace only after review.
Source gate / authenticated history / no-effect certificate unbound: fail closed.
No top-level runtime action. Original unknown call is retained unchanged.
"""
W71_KIND="verified-violation-original-seal-prewrite-unknown-successor-v1"
W71_FAILURE={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-31/round009-issue71-original-seal/director-VI30-summary.json', 'sha256': 'd88d440f506c604691c4e2e7ed760cec056a0a34e6dab280fcab39d1e12b36c6'}
W71_CONTEXT={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-31/round009-issue71-original-seal/original30-context-raw.json', 'sha256': '3bc3eb8d8b764e9487ae41d497c3618e227935425e363db43df51cae424d30f7'}
W71_BASE={'path': '/Users/feibing/work/projects/zmaibaole/runtime/workshop-director/role-executions/cdac95ef65466760d4bc91e9595f5d8b391bf931f34df1a742d9cdd7b8617d6f/v13-original-raw-registration-successors/4b77dff38a1658a1aebb647c2465479c42dfb60571c15fd934db9975c67f5060/admission.json', 'sha256': 'f5b1492929373d1ea684e6124b121146cf10b4bc567cbb8e47dee4ef49813bec'}
W71_NO_EFFECT={'path': '/Users/feibing/work/projects/zmaibaole/work/2026-10-31/round009-issue71-original-seal/ROOT-PREWRITE-NO-BUSINESS-EFFECT-CERTIFICATE.json', 'sha256': '65ae5a175f5bbb3c47b76b4f73e437d66d1abfd81c0e257cc65a94db41801441'}
W71_SOURCES={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/W71-seal-unknown-retirement-candidate-v5/W71-BUSINESS-SOURCES.json', 'sha256': 'fb6ce63b70d89ebf8f7472213c819f6ddafbe0a38b9386274990dcaebff3d37a'}
W71_LAUNCHER=str(PROJECT/'skills/workshop-director/scripts/role_execution_launcher.py')
W71_PATHS=W68_PATHS|{W71_LAUNCHER}
W71_CF_AFTER='6f790f1a8ac3818ec489feafedfe9d80bd03745dc931eafc28422a4688ce1321'
W71_PRIOR_QUALIFICATION={'path':str(PROJECT/'work/2026-10-30/round009-issue70-maintenance/source/full11/supervisor-release.json'),'sha256':'7b301423cb51ba61fd5d79de9ca48a41c38a208af2ec382266056df743b2ad11'}
W71_HISTORY={'path': '/Users/feibing/work/projects/zmaibaole/work/performance-audit/W71-performance-fast-reader-candidate-v4/history_reader.py', 'sha256': 'bcb490d4564773a0cd6b360c7ac93830390fab0f6fe6466f9ebe57784c77741b'}

def w71_failure(parent,engine):
 s=doc(W71_FAILURE)
 need(parent==doc(s['parent_archive']) and engine==doc(s['engine_archive']),'W71-exact-original-objects')
 need(parent['order']==engine['order']==TASK8_ORDER and parent['reboot_continuation']==engine['reboot_continuation']==W71_BASE,'W71-original-order-and-prior')
 need(parent['status']=='hold' and parent['error']=='execution-child-stopped' and len(parent['calls'])==27,'W71-parent27-hold')
 need(engine['status']=='running' and engine['phase']=='collection-seal' and engine['index']==0 and len(engine['calls'])==121,'W71-exact-seal-frontier')
 need(all(c['state']=='returned' and c.get('applied') is True for c in engine['calls'][:120]),'W71-returned120-prefix')
 unknown=engine['calls'][120]
 need(unknown['state']=='unknown' and unknown['step']=='collection-seal' and unknown['company_index']==0 and 'result' not in unknown and 'error' not in unknown,'W71-original-unknown-not-failed')
 rc=[]
 for index,call in enumerate(parent['calls']):
  launch=doc(call['launch']);result=doc(call['result'])
  need(call['state']=='returned' and launch['order']==TASK8_ORDER and launch['index']==index and launch['argv']==call['argv']==result['argv'] and result['launch']==call['launch'],'W71-exact-natural-child')
  rc.append(result['returncode'])
 need(rc==[2]*16+[0,0,2,2,2,0,0,2,2,2,2],'W71-original-normal4-and-failed23')
 last=doc(parent['calls'][26]['result'])
 need(json.loads(last['stdout'])=={'ok':False,'error':'registration-command-prior-validation-failed'} and last['stderr']=='','W71-original-inner-refusal')
 a=engine['companies'][1]['artifacts']
 need(a['frame_index']==7 and len(a['frames'])==4 and doc(s['detail'])==doc(s['detail_archive']),'W71-completed-images-and-detail-preserved')
 need(isinstance(W71_NO_EFFECT,dict),'W71-prewrite-proof-not-reviewed')
 proof=doc(W71_NO_EFFECT)
 need(proof['failure']==W71_FAILURE and proof['original_unknown']==unknown and proof['actual_visible_error']=='registration-command-prior-validation-failed' and proof['diagnostic_primary_error']=='candidate-code-graph-changed' and proof['mechanism_reproduced'] is True and proof['original_primary_stack_captured'] is False and proof['prewrite_only'] is True and proof['root_review'],'W71-exact-prewrite-proof')
 need(proof['kind']=='Root-fixed-original-seal-prewrite-unknown-qualification-v1' and proof['original_unknown_index']==120 and proof['original_context']==W71_CONTEXT and proof['engine_archive']==s['engine_archive'] and proof['parent_archive']==s['parent_archive'],'W71-certificate-original-binding')
 need(len(proof['source_refs'])==len(proof['logical_source_archives'])==15 and proof['source_refs']==[row['archive']for row in proof['logical_source_archives']] and len(proof['fixed_outputs'])==len(set(proof['fixed_outputs']))==9,'W71-certificate-fixed-source-and-output-set')
 for row in proof['logical_source_archives']:need(row['original_sha256']==row['archive']['sha256'],'W71-original-source-archive-sha')
 for reference in proof['source_refs']:raw(reference)
 return {'original_parent_prefix':copy.deepcopy(parent['calls']),'failed_calls':[copy.deepcopy(c) for i,c in enumerate(parent['calls']) if i not in (16,17,21,22)],'unknown_index':120,'unknown_call':copy.deepcopy(unknown),'engine_prefix':copy.deepcopy(engine['calls']),'no_effect':W71_NO_EFFECT}

def w71_parent_after(before,reference):
 after=copy.deepcopy(before);after.update(status='running',reboot_continuation=reference);after.pop('error')
 after.setdefault('resolved_errors',[]).append({'error':'execution-child-stopped','recovery':reference,'result_kind':'seal-prewrite-unknown-retained-new-call-required'})
 return after

def w71_engine_after(before,reference):
 after=copy.deepcopy(before);after.update(reboot_continuation=reference)
 need(len(after['calls'])==121 and after['calls'][120]['state']=='unknown','W71-original-unknown-required')
 after.setdefault('retired_prewrite_unknowns',[]).append({'index':120,'call':copy.deepcopy(after['calls'][120]),'proof':reference,'may_replay_original':False})
 return after

def w71_allowed_calls(engine,reference,view):
 need(view['kind']==W71_KIND and view['successor']==reference,'W71-exact-verified-view')
 original=doc(doc(W71_FAILURE)['engine_archive'])
 expected=w71_engine_after(original,reference)
 need(view['engine_prefix']==expected['calls'],'W71-exact-original-engine-view')
 need(engine['calls'][:121]==expected['calls'] and engine.get('retired_prewrite_unknowns')==expected['retired_prewrite_unknowns'],'W71-retained121-and-retirement')
 need(engine['calls'][120]['state']=='unknown' and all(c['state']=='returned' for c in engine['calls'][121:]),'W71-only-fixed-old-unknown-allowed')
 return True

def w71_fixed_module(reference,name):
 import types
 need(isinstance(reference,dict),'W71-unbound-reviewed-interface')
 module=types.ModuleType(name);module.__file__=reference['path'];exec(compile(raw(reference),module.__file__,'exec'),module.__dict__)
 return module

def w71_sources(release_ref):
    need(isinstance(W68_PERFORMANCE, dict) and isinstance(W71_CF_AFTER, str), 'W68-all-three-fixes-not-final')
    release = doc(release_ref)
    need(release.get('kind') == 'supervisor-reviewed-source-release-v1' and release.get('published') is True and (release.get('test_projection_only') is False) and (release.get('reviewed_by') == 'workshop-director') and (len(release['targets']) == 12) and ({t['target'] for t in release['targets']} == W71_PATHS), 'W71-exact-twelve-physical-qualification-sources')
    base = doc(W68_BASE)
    codes = copy.deepcopy(base['current_code_refs'])
    by = {r['path']: r for r in codes}
    need(len(codes) == len(by) == 159, 'W68-original159-no-added-slot')
    business = doc(W68_BUSINESS)
    need(business['kind'] == 'W68-fractional-auto-padding-and-public-text-four-source-business-package-v2' and business['no_original_slot_added'] is True and (len(business['targets']) == 4), 'W68-fixed-reviewed-business4')
    reviewed = {r['target']: r for r in business['targets']}
    body = doc(W68_BODY_SUCCESSOR)
    need(body['kind'] == 'W68-reviewed-source-root-body-selector-successor-v1' and len(body['targets']) == 1 and (body['prior_business_contract'] == W68_BUSINESS) and (body['prior_published_full10'] == W68_PUBLISHED_FULL10) and (body['original_producer_receipt'] == W68_PUBLISHED_PRODUCER), 'W68-exact-root-body-successor')
    bodyrow = body['targets'][0]
    bodypath = str(PROJECT / 'skills/chrome-dom-export/scripts/business_cells_capture.py')
    prior = reviewed[bodypath]
    need(bodyrow['target'] == bodypath and bodyrow['mode'] == 420 and (body['original_before'] == prior['before']) and (body['previous_payload'] == prior['payload']) and (bodyrow['before']['sha256'] == prior['payload']['sha256']) and (raw(bodyrow['before']) == raw(prior['payload'])), 'W68-root-body-prior-archive')
    reviewed[bodypath] = {**prior, 'payload': bodyrow['payload']}
    performance = doc(W68_PERFORMANCE)
    need(performance.get('kind') == 'W68-command-scope-history-validation-performance-subpackage-v1' and len(performance['targets']) == 1 and (performance['targets'][0]['target'] == str(PROJECT / 'skills/violation-notifier/scripts/registration_validation.py')), 'W68-single-performance-subpackage')
    reviewed.update({r['target']: r for r in performance['targets']})
    perf_new = doc(W70_PERFORMANCE)
    need(perf_new['kind'] == 'W70-command-effect-boundary-single-source-package-v1' and len(perf_new['targets']) == 1, 'W70-effect-single-source')
    pn = perf_new['targets'][0]
    po = performance['targets'][0]
    need(pn['target'] == po['target'] and pn['mode'] == 420 and (pn['before']['sha256'] == po['payload']['sha256']) and (raw(pn['before']) == raw(po['payload'])), 'W70-effect-previous-source')
    reviewed[pn['target']] = {**po, 'payload': pn['payload']}
    pg = doc(W70_POSTGUARD)
    need(pg['kind'] == 'W70-v13-unselected-header-postguard-single-source-package-v1' and len(pg['targets']) == 1 and (pg['targets'][0]['target'] == str(PROJECT / 'skills/violation-notifier/scripts/region_postguard_retake.py')), 'W70-postguard-existing-source')
    reviewed[pg['targets'][0]['target']] = pg['targets'][0]
    delivery = doc(W68_DELIVERY)
    need(delivery['kind'] == 'unified-completion-admitted-role-single-source-package-v1' and len(delivery['targets']) == 1 and (delivery['targets'][0]['target'] == str(PROJECT / 'skills/workshop-director/scripts/unified_delivery.py')), 'W68-fixed-completion-source')
    reviewed.update({r['target']: r for r in delivery['targets']})
    need(isinstance(W71_SOURCES,dict),'W71-business-source-material-not-final')
    material=doc(W71_SOURCES)
    need(material['kind']=='W71-reviewed-seal-epoch-business-source-material-v1' and len(material['targets'])==3,'W71-exact-RV-ports-launcher-material')
    expected={str(PROJECT/'skills/violation-notifier/scripts'/n)for n in ('registration_validation.py','violation_execution_ports.py')}|{W71_LAUNCHER}
    need({row['target']for row in material['targets']}==expected,'W71-exact-business-targets')
    prior=doc(W71_PRIOR_QUALIFICATION)
    prior_rows={row['target']:row for row in prior['targets']}
    for row in material['targets']:
        old=prior_rows.get(row['target'])
        if row['target']==W71_LAUNCHER:
            need(row['before']['sha256']==by[W71_LAUNCHER]['sha256']=='908d14a375b2d040639240133dfa25bc9c453dd5a37c590a97dac02ca4de31ce','W71-only-original-launcher-slot')
            old={'before':row['before'],'after':row['before']}
        need(old is not None,'W71-no-unreviewed-new-slot')
        need(row['mode']==420 and row['before']['sha256']==old['after']['sha256'] and raw(row['before'])==raw(old['after']),'W71-reviewed-previous-payload')
        reviewed[row['target']]={'target':row['target'],'before':old['before'],'payload':row['payload'],'mode':420}
    archives = {}
    for t in release['targets']:
        independent = t['target'] == W68_CF['path']
        original = W68_CF if independent else by[t['target']]
        need(t['old_sha256'] == t['before']['sha256'] == original['sha256'] and t['mode'] == 420 and (t['after']['sha256'] != original['sha256']), 'W68-exact-before-existing-slot')
        raw(t['before'])
        raw(t['after'])
        current = {'path': t['target'], 'sha256': t['after']['sha256']}
        raw(current)
        need(Path(t['target']).stat().st_mode & 511 == 420, 'W68-actual-current-mode')
        archives[t['target']] = {'original': original, 'archive': t['before']}
        if t['target'] in reviewed:
            r = reviewed[t['target']]
            need(r['mode'] == 420 and r['before']['sha256'] == original['sha256'] and (raw(r['before']) == raw(t['before'])) and (r['payload']['sha256'] == t['after']['sha256']) and (raw(r['payload']) == raw(t['after'])), 'W68-exact-tested-business-performance-payload')
        if independent:
            need(current['sha256'] == W71_CF_AFTER, 'W68-fixed-independent-CF-after')
        else:
            codes[codes.index(original)] = current
    need(len(codes) == 159 and len(archives) == 12, 'W71-eleven-existing-slots-one-independent-CF')
    for current in codes:
        raw(current)
    return (archives, codes)

def w71_historical_base(release_ref,*,live_boot=None):
 return w71_fixed_module(W71_HISTORY,'_W71_fixed_original_history').verify(W71_BASE,successor_release=release_ref,live_boot=live_boot)

def w71_verify(reference,*,live_boot=None):
 value=doc(reference)
 need(value['kind']==W71_KIND and value['task_id']==TASK8 and value['attempt_id']==TASK8+'-30' and value['failure']==W71_FAILURE and value['previous_admission']==W71_BASE and value['no_effect']==W71_NO_EFFECT,'W71-exact-natural-failed30')
 archives,codes=w71_sources(value['release'])
 need(value['source_archives']==archives and value['current_code_refs']==codes,'W71-current-reviewed-sources')
 base=w71_historical_base(value['release'],live_boot=live_boot);s=doc(W71_FAILURE)
 need(value['parent_before']['sha256']==s['parent']['sha256'] and value['engine_before']['sha256']==s['engine']['sha256'],'W71-original-before-bytes')
 parent=doc(value['parent_before']);engine=doc(value['engine_before']);facts=w71_failure(parent,engine)
 returned=doc(o.ref(Path(reference['path']).parent/'returned.json'))
 need(returned['admission']==reference and doc(returned['parent_after'])==w71_parent_after(parent,reference) and doc(returned['engine_after'])==w71_engine_after(engine,reference),'W71-natural-complete-two-CAS')
 return {**base,'kind':W71_KIND,'attempt_id':TASK8+'-30','previous_admission':W71_BASE,'previous_previous_admission':base['previous_admission'],'current_code_refs':codes,'approved_parent_calls':facts['failed_calls'],'original_parent_prefix':facts['original_parent_prefix'],'readonly_failed_child':{'index':26,'call':facts['original_parent_prefix'][26],'returncode':2},'child_admissions':{**base['child_admissions'],'26':W71_BASE},'successor':reference,'engine_prefix':facts['engine_prefix'],'retired_engine_calls':[{'index':120,'call':facts['unknown_call'],'proof':reference}],'no_effect':W71_NO_EFFECT}

_W71_PREVIOUS_VERIFY=verify
_W71_PREVIOUS_ALLOWED=allowed_calls
def verify(reference,*,live_boot=None):
 if doc(reference).get('kind')==W71_KIND:return w71_verify(reference,live_boot=live_boot)
 return _W71_PREVIOUS_VERIFY(reference,live_boot=live_boot)
def allowed_calls(engine,admission):
 if doc(admission).get('kind')!=W71_KIND:return _W71_PREVIOUS_ALLOWED(engine,admission)
 return w71_allowed_calls(engine,admission,w71_verify(admission))

def w71_apply(release_ref,*,clock,process_reader):
 import fcntl,sqlite3,os,stat
 from violation_execution import atomic
 folder=o.location(TASK8_ORDER);handles=[];lock_ids=[]
 try:
  for path in (PROJECT/'runtime/workshop-director/browser-wecom.resource.lock',PROJECT/'runtime/standalone-workshop-director/scheduler.lock',folder/'launcher.lock',folder/'engine.lock'):
   need(o.canonical(path)==path and path.is_file() and not path.is_symlink(),'W71-existing-canonical-lock')
   f=path.open('r+');handles.append(f);fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);held=os.fstat(f.fileno());current=path.stat()
   need(stat.S_ISREG(held.st_mode) and (held.st_dev,held.st_ino)==(current.st_dev,current.st_ino),'W71-lock-replaced');lock_ids.append((path,f,held.st_dev,held.st_ino))
  with sqlite3.connect((PROJECT/'runtime/standalone-workshop-director/queue.sqlite3').as_uri()+'?mode=ro',uri=True)as db:
   row=db.execute('select state,attempt,context from tasks where id=?',(TASK8,)).fetchone()
   need(row[:2]==('failed',30) and row[2].encode()==raw(W71_CONTEXT) and not db.execute("select id from tasks where state in ('running','dispatching','unknown')").fetchall(),'W71-original-failed30-context-static')
   owner=db.execute("select value from meta where key='resource_owner'").fetchone();need(owner and json.loads(owner[0])==TASK8,'W71-original-resource-owner')
  started=doc(o.ref(PROJECT/'runtime/standalone-workshop-director/attempts'/(TASK8+'-30')/'started.json'));need(process_reader(started['process']['pid'])!=started['process'],'W71-worker30-dead')
  s=doc(W71_FAILURE);pr=s['parent'];er=s['engine'];parent=doc(pr);engine=doc(er);w71_failure(parent,engine)
  archives,codes=w71_sources(release_ref);w71_historical_base(release_ref,live_boot=clock.boot())
  proof=doc(W71_NO_EFFECT)
  for literal in proof['fixed_outputs']:
   path=Path(literal);need(path.is_absolute() and o.canonical(path)==path and not path.exists() and not path.is_symlink(),'W71-prewrite-output-no-longer-absent')
  out=folder/'seal-prewrite-unknown-successors'/digest({'release':release_ref,'failure':W71_FAILURE,'no_effect':W71_NO_EFFECT})
  need(not(out/'intent.json').exists(),'W71-partial-intent-inspect-only');out.mkdir(parents=True,exist_ok=True)
  value={'kind':W71_KIND,'task_id':TASK8,'attempt_id':TASK8+'-30','previous_admission':W71_BASE,'failure':W71_FAILURE,'no_effect':W71_NO_EFFECT,'release':release_ref,'source_archives':archives,'current_code_refs':codes,'parent_before':raw_archive(pr,out/'parent-before.json'),'engine_before':raw_archive(er,out/'engine-before.json'),'clock_comparable':False,'acceptance_pass':False}
  reference=o.immutable(out/'admission.json',value);np=w71_parent_after(parent,reference);ne=w71_engine_after(engine,reference)
  after={k:o.immutable(out/(k+'-after.json'),v) for k,v in (('parent',np),('engine',ne))}
  o.immutable(out/'intent.json',{'admission':reference,'before':{'parent':pr,'engine':er},'after':after,'business_inputs':0,'original_unknown_replayed':False})
  need(o.ref(Path(pr['path']))==pr and o.ref(Path(er['path']))==er,'W71-before-CAS-raced')
  for path,f,dev,ino in lock_ids:
   held=os.fstat(f.fileno());current=path.stat();need(not path.is_symlink() and o.canonical(path)==path and (held.st_dev,held.st_ino)==(current.st_dev,current.st_ino)==(dev,ino),'W71-lock-replaced-before-CAS')
  for literal in proof['fixed_outputs']:need(not Path(literal).exists() and not Path(literal).is_symlink(),'W71-output-created-before-CAS')
  atomic(Path(er['path']),ne);atomic(Path(pr['path']),np)
  o.immutable(out/'returned.json',{'admission':reference,'parent_after':after['parent'],'engine_after':after['engine'],'business_inputs':0,'original_unknown_replayed':False})
  w71_verify(reference,live_boot=clock.boot());return reference
 finally:
  for f in reversed(handles):f.close()
