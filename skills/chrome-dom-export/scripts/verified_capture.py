#!/usr/bin/env python3
"""Proposal: derive screenshot registration metadata from public DOM proof only.
Fixed source and observation hashes; no handwritten visibility or coverage flags.
No business ingestion/progress/send, no activation, input or screenshot retry.
"""
import argparse,hashlib,json,re
from datetime import date,timedelta
from pathlib import Path
import bridge
from visible_capture import write_capture,atomic,sha

def need(ok,code):
    if not ok:raise ValueError(code)
def pinned(path,digest):
    path=Path(path).resolve();need(path.is_file() and sha(path)==digest,'capture-pinned-file-changed');return json.loads(path.read_text())
def canon_hash(tree):return hashlib.sha256(json.dumps(tree,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def allnodes(tree):
    need(tree.get('truncated') is False and tree.get('kind')=='DOM-derived semantic tree (not native AX)','capture-tree-incomplete')
    out=[]
    def walk(n):
        need(len(out)<10000,'capture-tree-too-large');out.append(n)
        for child in n.get('children',[]):walk(child)
    walk(tree['root']);return out
def explicit_header_text(node):
    """Original semantic TH, allowing only the observed Byted title wrappers."""
    need(node.get('role')=='columnheader','capture-header-not-explicit-columnheader')
    value=' '.join(str(node.get('name','')).split())
    need(0<len(value)<800,'capture-header-text-truncated-or-empty')
    if node.get('children'):
        cls=set(node.get('attributes',{}).get('class','').split())
        need(node.get('tag')=='th' and 'governance_merchant-Table-Cell' in cls,'capture-header-wrapper-not-reviewed')
        descendants=[]
        def visit(n):
            descendants.append(n)
            for c in n.get('children',[]):visit(c)
        for child in node['children']:visit(child)
        titles=[n for n in descendants if 'governance_merchant-Table-HeadCellContentTitle' in n.get('attributes',{}).get('class','').split()]
        need(len(titles)==1 and not titles[0].get('children') and ' '.join(str(titles[0].get('name','')).split())==value,'capture-header-title-not-unique')
        need(all(not n.get('name') or ' '.join(str(n['name']).split())==value for n in descendants),'capture-header-extra-visible-content')
    return value

def command_from_inputs(source_path,source_sha,observation_path,observation_sha,spec):
    source=pinned(source_path,source_sha);observation=pinned(observation_path,observation_sha)
    need(source.get('source')=='local-dom-bridge' and source.get('account_verified') is True,'capture-source-not-current-verified-bridge')
    need(observation.get('source')=='local-dom-bridge','capture-observation-source-invalid')
    tab=observation['tab'];tab_id=observation['tab_id'];window_id=tab['windowId'];url=tab['url'];group=str(source['groupid'])
    need(str(tab.get('id',tab.get('tabId')))==str(tab_id),'capture-observation-tab-unbound')
    from urllib.parse import urlsplit,parse_qs
    u=urlsplit(url);need(u.scheme=='https' and u.netloc=='life.douyin.com' and parse_qs(u.query).get('groupid')==[group],'capture-observation-company-conflict')
    tree=observation['tree'];need(tree.get('url')==u.scheme+'://'+u.netloc+u.path,'capture-observation-path-conflict');ns=allnodes(tree)
    need(isinstance(spec,list) and spec,'capture-semantic-elements-required');elements=[];seen=set();row_ids=set();headers=set();ids={r['notice_id'] for r in source['records']['rows']}
    expected_date=source['start']+' ~ '+(date.fromisoformat(source['end_exclusive'])-timedelta(days=1)).isoformat()
    for e in spec:
        need(set(e)=={'key','kind','selector','notice_id'},'capture-spec-unknown-fields');need(e['selector'] not in seen,'capture-duplicate-selector');seen.add(e['selector'])
        matches=[n for n in ns if n.get('selector')==e['selector']];need(len(matches)==1,'capture-selector-not-unique');n=matches[0]
        text=' '.join(str(n.get('attributes',{}).get('value',n.get('name',''))).split());need(0<len(text)<800,'capture-field-truncated-or-empty')
        if e['kind']=='date-filter':
            actual_date=text.replace('/','-')
            if source.get('capture_schema')=='governance-public-dom-capture-v1' and u.path=='/p/governance/violation_list' and n.get('tag')=='input' and n.get('role')=='textbox' and 'governance_merchant-input' in n.get('attributes',{}).get('class','').split():actual_date=re.sub(r'\s*[~～]\s*',' ~ ',actual_date)
            need(actual_date==expected_date,'capture-date-filter-mismatch')
        elif e['kind']=='header':
            need(explicit_header_text(n)==text,'capture-header-text-conflict');headers.add(text)
        elif e['kind']=='row':
            need(n.get('role')=='row','capture-row-not-explicit-semantic-row')
            need(e['notice_id'] in ids and e['notice_id'] not in row_ids and re.search(r'(?<![A-Za-z0-9_-])'+re.escape(e['notice_id'])+r'(?![A-Za-z0-9_-])',text) is not None,'capture-row-not-bound-to-source');row_ids.add(e['notice_id'])
        else:raise ValueError('capture-kind-invalid')
        elements.append({'key':e['key'],'kind':e['kind'],'locator':{'by':'selector','value':e['selector']},'expected_text':text,'notice_id':e['notice_id']})
    need({'违规原因','处置主体','违规对象','处置生效状态','处置方式'}<=headers,'capture-required-record-headers-missing')
    command={'op':'viewport-proof','tabId':tab_id,'windowId':window_id,'groupid':group,'source_sha256':source_sha,'dom_sha256':canon_hash(tree),'elements':elements};bridge.validate_command(command)
    return command

def checked(command,request,*,versions=('dom-only-20261021-6','dom-only-20261021-7','dom-only-20261021-8','dom-only-20261021-9','dom-only-20261021-10','dom-only-20261021-11')):
    response=request(command);need(response.get('ok') is True,'capture-viewport-proof-failed:'+str(response.get('error')));result=response['result']
    need(result.get('safety_version') in versions and result.get('source_sha256')==command['source_sha256'] and result.get('dom_sha256')==command['dom_sha256'],'capture-proof-binding-mismatch')
    need(result.get('scope')=={k:command[k] for k in ('tabId','windowId','groupid')},'capture-proof-scope-mismatch')
    need(result.get('viewport_only') is True and result.get('pixel_coordinates_returned') is False and result.get('pixel_actions_used') is False and result.get('all_fully_visible') is True,'capture-viewport-not-fully-visible')
    es=result.get('elements',[]);need(len(es)==len(command['elements']),'capture-proof-elements-incomplete')
    for actual,expected in zip(es,command['elements']):
        need(all(actual.get(k)==expected[k] for k in ('key','kind','notice_id','locator')) and actual.get('text')==expected['expected_text'],'capture-proof-element-binding-mismatch')
        need(all(actual.get(k) is True for k in ('rendered','viewport_contained','text_unclipped','unsupported_css_absent','possible_overlay_absent','fully_visible')),'capture-proof-incomplete-row')
    need(type(result.get('epoch')) is int,'capture-proof-epoch-required');return result

def capture(source_path,source_sha,observation_path,observation_sha,spec,key,out,request=None):
    command=command_from_inputs(source_path,source_sha,observation_path,observation_sha,spec);out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True);intent=out.with_suffix('.coverage-intent.json');registration=out.with_suffix('.registration.json')
    need(not intent.exists() and not registration.exists(),'capture-coverage-intent-exists-no-replay');request=request or bridge.request
    binding={'source_path':str(Path(source_path).resolve()),'source_sha256':source_sha,'observation_path':str(Path(observation_path).resolve()),'observation_sha256':observation_sha,'command':command,'captureKey':key}
    with intent.open('x') as f:json.dump({'state':'intent',**binding},f,ensure_ascii=False,indent=2);f.flush();__import__('os').fsync(f.fileno())
    try:
        before=checked(command,request,versions=('dom-only-20261103-12',))
        # Persist public proof before the single screenshot request.
        atomic(intent,{'state':'intent',**binding,'before':before})
        captured=write_capture({'op':'capture-visible',**{k:command[k] for k in ('tabId','windowId','groupid')},'captureKey':key},out,request)
        after=checked(command,request,versions=('dom-only-20261103-12',));need(before==after,'capture-dom-or-geometry-changed-during-screenshot')
        pinned(source_path,source_sha);pinned(observation_path,observation_sha)
        capture_meta=json.loads(out.with_suffix('.json').read_text());need(capture_meta['capture']['before']['url']==before['url'],'capture-png-proof-url-conflict')
        required_filters=['date-filter']
        visible_filters=sorted({e['kind'] for e in before['elements'] if e['kind']=='date-filter' and e['fully_visible'] is True})
        required_headers={'违规原因','处置主体','违规对象','处置生效状态','处置方式'}
        visible_headers={e['text'] for e in before['elements'] if e['kind']=='header' and e['fully_visible'] is True}
        metadata={'source':'local-dom-bridge','source_sha256':source_sha,'sha256':sha(out),'date_filter_visible':'date-filter' in visible_filters,'visible_filter_kinds':visible_filters,'required_scope_filters':required_filters,'filters_visible':set(required_filters)<=set(visible_filters),'list_headers_visible':required_headers<=visible_headers,'notice_ids':[e['notice_id'] for e in before['elements'] if e['kind']=='row'],'viewport_only':True,'coverage_scope':'only explicitly verified fully visible rows','public_dom_proof':{'before':before,'after':after},'capture_metadata':{'path':str(out.with_suffix('.json')),'sha256':sha(out.with_suffix('.json'))},'pinned_inputs':binding}
        atomic(registration,metadata);atomic(intent,{'state':'complete',**binding,'registration':str(registration),'sha256':sha(out)});return {'png':str(out),'metadata':str(registration),'viewport_only':True,'business_progress_changed':False}
    except Exception as error:atomic(intent,{'state':'unknown',**binding,'error':str(error),'retry_permitted':False});raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-sha256','observation','observation-sha256','spec','key','out'):p.add_argument('--'+name,required=True)
    a=p.parse_args();result=capture(a.source,a.source_sha256,a.observation,a.observation_sha256,json.loads(Path(a.spec).read_text()),a.key,a.out);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
