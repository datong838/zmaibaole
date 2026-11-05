"""Offline v6 screenshot evidence validation. Integrity/scope checks, not a signature.
No browser/network calls, credentials, geometry output or business progress writes.
validate_capture_chain is reusable by other workflow-specific semantic builders.
"""
import hashlib,json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import verified_capture as vc
from visible_capture import validate_png
SAFETY='dom-only-20261021-6'  # Historical receipt compatibility.
SUPPORTED=(SAFETY,'dom-only-20261103-12','dom-only-20261021-7','dom-only-20261021-8','dom-only-20261021-9','dom-only-20261021-10','dom-only-20261021-11')
PROOF_KEYS={'source','method','source_sha256','dom_sha256','epoch','url','viewport_only','pixel_coordinates_returned','pixel_actions_used','elements','all_fully_visible','scope','safety_version'}
def need(ok,code):
    if not ok:raise ValueError(code)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def document(ref):
    need(isinstance(ref,dict) and isinstance(ref.get('path'),str) and Path(ref['path']).is_absolute(),'screenshot-chain-absolute-reference-required')
    p=Path(ref['path']);raw=p.read_bytes();need(hashlib.sha256(raw).hexdigest()==ref.get('sha256'),'screenshot-chain-reference-changed');return json.loads(raw)
def when(value):
    parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'));need(parsed.utcoffset() is not None,'screenshot-chain-timezone-required');return parsed

def validate_overlay_diagnostic(value):
    need(isinstance(value,dict) and set(value)=={'purpose','candidates','candidate_count','truncated'} and value['purpose']=='readonly-overlay-diagnostic-only','screenshot-overlay-diagnostic-fields-invalid')
    items=value['candidates'];count=value['candidate_count'];need(isinstance(items,list) and len(items)<=12 and type(count) is int and count>=len(items) and value['truncated']==(count>len(items)) and type(value['truncated']) is bool,'screenshot-overlay-diagnostic-bound-invalid')
    fields={'selector','tag','class','class_truncated','position','pointer_events','opacity','background_color','background_image_present','has_text'}
    for item in items:
        need(isinstance(item,dict) and set(item)==fields and (item['selector'] is None or isinstance(item['selector'],str) and len(item['selector'])<=1500) and isinstance(item['class'],str) and len(item['class'])<=500 and all(type(item[k]) is bool for k in ('class_truncated','background_image_present','has_text')),'screenshot-overlay-diagnostic-candidate-invalid')
        need(all(isinstance(item[k],str) and len(item[k])<=200 for k in ('tag','position','pointer_events','opacity','background_color')),'screenshot-overlay-diagnostic-style-invalid')

def validate_containment_diagnostic(value):
    need(isinstance(value,dict) and set(value)=={'purpose','scope','reasons','reason_count','truncated'} and value['purpose']=='readonly-containment-diagnostic-only' and value['scope']=='target-and-descendants','screenshot-containment-diagnostic-fields-invalid')
    rows=value['reasons'];count=value['reason_count'];need(isinstance(rows,list) and len(rows)<=12 and type(count) is int and count>=len(rows) and type(value['truncated']) is bool and value['truncated']==(count>len(rows)),'screenshot-containment-diagnostic-bound-invalid')
    for row in rows:
        need(isinstance(row,dict) and set(row)=={'target_selector','ancestor_selector','axis','reason'} and all(row[k] is None or isinstance(row[k],str) and len(row[k])<=1500 for k in ('target_selector','ancestor_selector')) and row['axis'] in ('x','y') and row['reason'] in ('outside-viewport','ancestor-overflow'),'screenshot-containment-diagnostic-reason-invalid')
        need(row['reason']!='outside-viewport' or row['ancestor_selector'] is None,'screenshot-containment-diagnostic-viewport-ancestor-invalid')

def validate_public_proof(before,expected_command,expected_url):
    source_sha256=expected_command['source_sha256'];groupid=expected_command['groupid']
    projected=any(e.get('key','').startswith('gov-records-') for e in expected_command['elements'])
    extra={'hash_contract','hash_scope'} if projected else set()
    need(set(before) in (PROOF_KEYS|extra,PROOF_KEYS|extra|{'diagnostic_build'}) and before.get('source')=='local-dom-bridge' and before.get('method')=='public-DOM-semantic-viewport-proof','screenshot-chain-public-proof-required')
    need(before.get('url')==expected_url and expected_command.get('source_sha256')==source_sha256 and str(expected_command.get('groupid'))==str(groupid),'screenshot-chain-proof-scope-mismatch')
    need(before.get('safety_version') in SUPPORTED and before.get('scope')=={k:expected_command[k] for k in ('tabId','windowId','groupid')} and before.get('source_sha256')==expected_command['source_sha256'] and before.get('dom_sha256')==expected_command['dom_sha256'],'screenshot-chain-proof-binding-mismatch')
    need(type(before.get('epoch')) is int and before['epoch']>=0 and before.get('viewport_only') is True and before.get('pixel_coordinates_returned') is False and before.get('pixel_actions_used') is False,'screenshot-chain-proof-safety-mismatch')
    actuals=before.get('elements',[]);want=expected_command['elements'];need(len(actuals)==len(want),'screenshot-chain-proof-elements-incomplete')
    flags=('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent')
    for actual,expected in zip(actuals,want):
        need(all(actual.get(k)==expected[k] for k in ('key','kind','notice_id','locator')) and actual.get('text')==expected['expected_text'],'screenshot-chain-semantic-binding-mismatch')
        need(all(type(actual.get(k)) is bool for k in (*flags,'fully_visible')) and actual['fully_visible']==all(actual[k] for k in flags),'screenshot-chain-visibility-inconsistent')
    need(type(before.get('all_fully_visible')) is bool and before['all_fully_visible']==all(e['fully_visible'] for e in actuals),'screenshot-chain-all-visible-inconsistent')
    element_keys={'key','kind','notice_id','locator','text','rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent','fully_visible'}
    need(before['epoch']>=0 and all(element_keys<=set(e) and not set(e)-element_keys-{'possible_overlay_diagnostic','containment_diagnostic'} for e in before['elements']),'screenshot-chain-unreviewed-proof-fields')
    for element in before['elements']:
        if 'containment_diagnostic' in element:
            validate_containment_diagnostic(element['containment_diagnostic']);need(element['viewport_contained']==(element['containment_diagnostic']['reason_count']==0),'screenshot-containment-diagnostic-visibility-conflict')
        if 'possible_overlay_diagnostic' in element:
            validate_overlay_diagnostic(element['possible_overlay_diagnostic']);need(element['possible_overlay_absent']==(element['possible_overlay_diagnostic']['candidate_count']==0),'screenshot-overlay-diagnostic-visibility-conflict')
    if projected:
        import governance_projection as projection
        need(all(e['key'].startswith(projection.SCHEMA+':') for e in expected_command['elements']) and before.get('hash_contract')==projection.SCHEMA and before.get('hash_scope')=='versioned-public-DOM-projection','screenshot-chain-projection-contract-mismatch')
    if 'diagnostic_build' in before:need(before['diagnostic_build'] in ('viewport-overlay-diagnostic-v1','viewport-governance-stable5-v1','viewport-governance-stable5-v2','viewport-governance-stable5-v3','viewport-governance-stable5-v4','viewport-governance-stable5-v5','viewport-notice-business-cells-v1','viewport-notice-business-cells-v2','viewport-notice-business-cells-v3','viewport-notice-business-cells-v4','viewport-notice-business-cells-v5','viewport-notice-business-cells-v12-rectification-projection-v3','viewport-notice-business-cells-v13-fractional-auto-padding-v1'),'screenshot-chain-diagnostic-build-unreviewed')
    return before

def _validate_capture_integrity(image,metadata,*,source_sha256,groupid,expected_command,expected_url):
    """Validate an already-derived semantic command and v6 PNG/proof chain.
    Caller must derive expected_command from its own pinned source/DOM schema.
    Returns file references for immutable local evidence snapshots, never coordinates.
    """
    m=metadata;image=Path(image).resolve();raw=image.read_bytes();digest=hashlib.sha256(raw).hexdigest();width,height=validate_png(raw)
    need(m.get('source')=='local-dom-bridge' and m.get('source_sha256')==source_sha256 and m.get('sha256')==digest,'screenshot-chain-image-source-mismatch')
    need(m.get('viewport_only') is True,'screenshot-chain-viewport-required')
    pair=m.get('public_dom_proof',{});before=pair.get('before');after=pair.get('after')
    need(isinstance(before,dict) and before==after and set(pair)=={'before','after'},'screenshot-chain-before-after-mismatch')
    validate_public_proof(before,expected_command,expected_url)
    scope={k:expected_command[k] for k in ('tabId','windowId','groupid')}
    u=urlsplit(expected_url);need(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[str(groupid)],'screenshot-chain-company-url-invalid')
    ref=m.get('capture_metadata');capture=document(ref)
    command={'op':'capture-visible',**scope,'captureKey':m['pinned_inputs']['captureKey']}
    vc.bridge.validate_command(command)
    need(capture.get('state')=='complete' and capture.get('source')=='local-dom-bridge' and capture.get('capture_method')=='chrome.tabs.captureVisibleTab' and capture.get('viewport_only') is True and capture.get('command')==command,'screenshot-chain-capture-journal-incomplete')
    png=capture.get('png',{});need(png.get('sha256')==digest and png.get('width')==width and png.get('height')==height and Path(png.get('path','')).is_absolute(),'screenshot-chain-png-journal-mismatch')
    # Same immutable bytes can be registered from an evidence copy. Original PNG
    # remains hash-bound; its exact original path is not an identity substitute.
    need(Path(png['path']).is_file() and sha(png['path'])==digest,'screenshot-chain-original-png-changed')
    result=capture.get('capture',{});cs=result.get('before',{})
    need(set(cs)=={'tabId','windowId','groupid','url','title'} and cs==result.get('after') and all(cs.get(k)==v for k,v in scope.items()) and cs.get('url')==expected_url,'screenshot-chain-capture-scope-mismatch')
    need(result.get('safety_version') in SUPPORTED and result.get('safety_version')==before['safety_version'] and result.get('capture_method')=='chrome.tabs.captureVisibleTab' and result.get('captureKey')==command['captureKey'] and result.get('viewport_only') is True and result.get('pixel_actions_used') is False and 'imageDataUrl' not in result,'screenshot-chain-capture-version-or-method-mismatch')
    grant=result.get('grant',{});need(grant.get('scope')==cs and grant.get('safety_version')==before['safety_version'] and grant.get('via')=='chrome.action.onClicked' and isinstance(grant.get('nonce'),str) and bool(grant['nonce']),'screenshot-chain-action-grant-unbound')
    need(when(grant.get('invokedAt'))<=when(result.get('observedAt')) and when(capture.get('intent_at'))<=when(result.get('observedAt'))<=when(capture.get('completed_at')),'screenshot-chain-capture-time-conflict')
    return {'capture_metadata':ref,'capture_png':{'path':str(Path(png['path']).resolve()),'sha256':digest},'version':before['safety_version'],'viewport_only':True,'observed_at':result['observedAt'],'grant_nonce':grant['nonce'],'capture_scope':cs}

def visible_facts(proof):
    elements=proof['elements'];dates=[e for e in elements if e['kind']=='date-filter'];headers=[e for e in elements if e['kind']=='header']
    required={'违规原因','处置主体','违规对象','处置生效状态','处置方式'}
    date_visible=bool(dates) and all(e['fully_visible'] for e in dates)
    headers_visible=required<={e['text'] for e in headers if e['fully_visible']}
    return {'date_filter_visible':date_visible,'filters_visible':date_visible,'list_headers_visible':headers_visible,'notice_ids':[e['notice_id'] for e in elements if e['kind']=='row' and e['fully_visible']]}

def validate_capture_chain(image,metadata,*,source_sha256,groupid,expected_command,expected_url):
    """Original strict path: all requested filters, headers and rows are visible."""
    result=_validate_capture_integrity(image,metadata,source_sha256=source_sha256,groupid=groupid,expected_command=expected_command,expected_url=expected_url)
    before=metadata['public_dom_proof']['before'];vc.checked(expected_command,lambda _: {'ok':True,'result':before})
    need(metadata.get('filters_visible') is True and metadata.get('date_filter_visible') is True and metadata.get('visible_filter_kinds')==['date-filter'] and metadata.get('required_scope_filters')==['date-filter'] and metadata.get('list_headers_visible') is True,'screenshot-chain-derived-filter-flags-mismatch')
    ids=[e['notice_id'] for e in before['elements'] if e['kind']=='row'];need(ids and len(ids)==len(set(ids)) and metadata.get('notice_ids')==ids,'screenshot-chain-row-coverage-mismatch')
    return {**result,'notice_ids':ids}

def validate_frame_capture_chain(image,metadata,*,source_sha256,groupid,expected_command,expected_url):
    """Explicit anchored-frame path, never reached by the strict API."""
    need(metadata.get('visibility_policy')=='anchored-frames-v1' and metadata.get('frame_mode') in ('anchor','rows'),'screenshot-frame-policy-required')
    result=_validate_capture_integrity(image,metadata,source_sha256=source_sha256,groupid=groupid,expected_command=expected_command,expected_url=expected_url)
    need(result['version'] in SUPPORTED,'screenshot-frame-reviewed-version-required')
    facts=visible_facts(metadata['public_dom_proof']['before'])
    need(all(metadata.get(k)==value for k,value in facts.items()),'screenshot-frame-derived-visibility-mismatch')
    if metadata['frame_mode']=='anchor':need(facts['date_filter_visible'] and facts['list_headers_visible'],'screenshot-frame-anchor-not-visible')
    else:need(bool(facts['notice_ids']),'screenshot-frame-no-complete-rows')
    result['notice_ids']=facts['notice_ids'];return result


def validate_violation_registration(image,metadata,*,source,company,groupid,start,end_exclusive,notice_ids):
    """Violation adapter: exact batch source + original DOM date/5 headers/rows."""
    m=metadata;batch_source=document(source);binding=m.get('pinned_inputs')
    need(isinstance(binding,dict) and binding.get('source_sha256')==source['sha256'],'screenshot-chain-pinned-source-required')
    original_ref={'path':binding.get('source_path'),'sha256':binding.get('source_sha256')};original=document(original_ref)
    need(original==batch_source and original.get('company')==company and str(original.get('groupid'))==str(groupid) and original.get('start')==start and original.get('end_exclusive')==end_exclusive,'screenshot-chain-batch-scope-conflict')
    need({r['notice_id'] for r in original['records']['rows']}==set(notice_ids),'screenshot-chain-batch-notices-conflict')
    observation_ref={'path':binding.get('observation_path'),'sha256':binding.get('observation_sha256')};observation=document(observation_ref)
    cmd=binding.get('command');need(isinstance(cmd,dict),'screenshot-chain-command-required')
    spec=[]
    for e in cmd.get('elements',[]):
        need(e.get('locator',{}).get('by')=='selector','screenshot-chain-exact-observed-selector-required')
        spec.append({'key':e['key'],'kind':e['kind'],'selector':e['locator']['value'],'notice_id':e['notice_id']})
    expected=vc.command_from_inputs(original_ref['path'],original_ref['sha256'],observation_ref['path'],observation_ref['sha256'],spec)
    need(expected==cmd,'screenshot-chain-command-not-derived-from-dom')
    result=validate_capture_chain(image,m,source_sha256=source['sha256'],groupid=str(groupid),expected_command=expected,expected_url=observation['tab']['url'])
    source_url=urlsplit(original['url']);observed_url=urlsplit(observation['tab']['url']);need(source_url.path==observed_url.path,'screenshot-chain-record-route-conflict')
    result['references']=[original_ref,observation_ref,result['capture_metadata'],result['capture_png']]
    # Recheck references before caller persists its own immutable snapshots.
    for ref in result['references']:need(sha(ref['path'])==ref['sha256'],'screenshot-chain-reference-changed')
    return result
